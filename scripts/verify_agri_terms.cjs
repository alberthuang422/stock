// 功能验证：术语悬停浮窗（.term span + #termtip 交互）
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

  // 1. 基础状态：canvas=5（图表渲染 OK）+ 正文标注数
  const base = await probe(`({
    canvas: document.querySelectorAll('canvas').length,
    termN: document.querySelectorAll('.term').length,
    glossaryTermN: (() => { const g = document.querySelector('.glossary'); return g ? g.querySelectorAll('.term').length : -1; })(),
    tipInitial: (() => { const t = document.getElementById('termtip'); return t ? getComputedStyle(t).display : 'NO_DIV'; })()
  })`);

  // 2. 悬停第一个 .term：浮窗应出现且有内容
  const hover = await probe(`(() => {
    const t = document.querySelector('.term');
    const word = t.textContent.trim();
    t.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    const tip = document.getElementById('termtip');
    return { word, display: getComputedStyle(tip).display, content: tip.textContent.trim().slice(0, 60) };
  })()`);

  // 3. mouseout：浮窗消失
  const out = await probe(`(() => {
    const t = document.querySelector('.term');
    t.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
    const tip = document.getElementById('termtip');
    return { display: getComputedStyle(tip).display };
  })()`);

  // 4. 悬停第二个（确保非首个也 OK）且内容不同
  const hover2 = await probe(`(() => {
    const ts = document.querySelectorAll('.term');
    const t = ts[1];
    const word = t.textContent.trim();
    t.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    const tip = document.getElementById('termtip');
    return { word, content: tip.textContent.trim().slice(0, 60) };
  })()`);

  console.log("BASE:", JSON.stringify(base));
  console.log("HOVER:", JSON.stringify(hover));
  console.log("MOUSEOUT:", JSON.stringify(out));
  console.log("HOVER2:", JSON.stringify(hover2));
  console.log("ERRORS:", errors.length ? errors.join("\n") : "none");

  if (sess) sess.close();
  if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }

  const ok = base.canvas === 5 && base.termN > 30 && base.glossaryTermN === 0 &&
             base.tipInitial === "none" && hover.display === "block" && hover.content.length > 0 &&
             out.display === "none" && hover2.content.length > 0 && hover2.word !== hover.word &&
             errors.length === 0;
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });