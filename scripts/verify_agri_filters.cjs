// 功能验证：57 号报告明细表筛选器（强度×股票双筛选）
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));
const FILE = "file:///C:/Users/Administrator/Desktop/stock/reports/57_%E5%86%9C%E4%B8%9A%E8%82%A1ENSO%E4%B8%8E%E5%88%A9%E7%8E%87%E6%95%8F%E6%84%9F%E6%80%A7/index.html";

async function cdpSession(wsUrl, onMsg) {
  const ws = new WebSocket(wsUrl);
  let idc = 0; const pending = new Map();
  const openP = new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws open error")); });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (onMsg) setTimeout(() => onMsg(m, ws), 0);
    if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); }
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const id = ++idc; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })); });
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}

(async () => {
  const errors = [];
  const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
  const target = await resp.json();
  const sess = await cdpSession(target.webSocketDebuggerUrl, (m) => {
    const method = m.method || "";
    if (method === "Runtime.exceptionThrown") errors.push("EXC: " + (m.params.exceptionDetails?.exception?.description || "").slice(0, 300));
    if (method === "Runtime.consoleAPICalled" && (m.params.type === "error" || m.params.type === "warning")) errors.push("CONSOLE: " + (m.params.args || []).map(a => a.value || a.description || "").join(" ").slice(0, 300));
  });
  await sess.openP;
  await sess.send("Page.enable"); await sess.send("Runtime.enable");
  await sess.send("Page.navigate", { url: FILE });
  await sleep(12000);

  const probe = async (expr) => {
    const r = await sess.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    return r.result.value;
  };

  // 1. 初始状态：筛选器选项 + 默认表格行数
  const init = await probe(`({
    canvas: document.querySelectorAll('canvas').length,
    tierOpts: [...document.querySelector('#f_tier').options].map(o=>o.value).join(','),
    tkrOpts: document.querySelector('#f_tkr').options.length,
    rowsOpts: document.querySelector('#f_rows').options.length,
    rowsShown: document.querySelectorAll('#det_tbl tbody tr').length,
    countTxt: document.querySelector('#f_count').textContent
  })`);

  // 2. 筛选强度=超强：表格应只含超强行
  const vstrong = await probe(`(() => {
    const s = document.querySelector('#f_tier');
    s.value = [...s.options].find(o=>o.value.includes('超强')).value;
    s.dispatchEvent(new Event('change'));
    const rows = [...document.querySelectorAll('#det_tbl tbody tr')];
    const evs = rows.map(r=>r.children[0].textContent);
    const tiers = rows.map(r=>r.children[1].textContent);
    const uniq = [...new Set(tiers)];
    return {n: rows.length, uniqTiers: uniq.join(','), evs: evs.slice(0,8).join(',')};
  })()`);

  // 3. 筛选股票=MOS：表格只含 MOS
  const mos = await probe(`(() => {
    const s = document.querySelector('#f_tkr');
    const tier = document.querySelector('#f_tier');
    tier.value='all'; tier.dispatchEvent(new Event('change'));
    s.value='MOS'; s.dispatchEvent(new Event('change'));
    const rows = [...document.querySelectorAll('#det_tbl tbody tr')];
    const tkrs = [...new Set(rows.map(r=>r.children[3].textContent))];
    return {n: rows.length, uniqTkrs: tkrs.join(','), countTxt: document.querySelector('#f_count').textContent};
  })()`);

  // 4. 显示行数限制=20（先重置筛选器）
  const rowlim = await probe(`(() => {
    const tier = document.querySelector('#f_tier'); tier.value='all';
    const tk = document.querySelector('#f_tkr'); tk.value='all';
    tk.dispatchEvent(new Event('change'));
    const s = document.querySelector('#f_rows'); s.value='20'; s.dispatchEvent(new Event('change'));
    return {n: document.querySelectorAll('#det_tbl tbody tr').length,
            hasMore: !!document.querySelector('.fmore'),
            countTxt: document.querySelector('#f_count').textContent};
  })()`);

  console.log("INIT:", JSON.stringify(init));
  console.log("VSTRONG:", JSON.stringify(vstrong));
  console.log("MOS:", JSON.stringify(mos));
  console.log("ROWLIM:", JSON.stringify(rowlim));
  console.log("ERRORS:", errors.length ? errors.join("\n") : "none");

  if (sess) sess.close();
  if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }

  const ok = init.canvas === 5 && init.tierOpts.split(',').length > 3 &&
             init.rowsShown > 0 && vstrong.n > 0 && vstrong.uniqTiers.split(',').every(x=>x.includes('超强')) &&
             mos.uniqTkrs === 'MOS' && mos.n > 0 && rowlim.n === 21 && rowlim.hasMore && errors.length === 0;
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });