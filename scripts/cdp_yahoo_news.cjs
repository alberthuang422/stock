// 抓取 Yahoo Finance 个股新闻区标题（真实浏览器核实提价事实）
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function cdpSession(wsUrl) {
  const ws = new WebSocket(wsUrl); let idc = 0; const pending = new Map();
  const openP = new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws error")); });
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } };
  const send = (method, params = {}) => new Promise((res, rej) => { const id = ++idc; pending.set(id, {res,rej}); ws.send(JSON.stringify({id, method, params})); });
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}
(async () => {
  const tk = (process.argv[2] || "HSY").toUpperCase();
  const url = `https://finance.yahoo.com/quote/${tk}/`;
  let target = null, sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP; await sess.send("Page.enable");
    await sess.send("Page.navigate", { url });
    await sleep(7000);
    const expr = `(() => {
      const heads = [...document.querySelectorAll('h3, [class*="news"] a, li[class*="news"] a')].map(a => a.innerText.trim()).filter(t => t && t.length > 20);
      return [...new Set(heads)].slice(0, 12).join('\\n');
    })()`;
    const r = await sess.send("Runtime.evaluate", { expression: expr, returnByValue: true });
    const out = r.result.value || "NO_NEWS";
    console.log(`== ${tk} NEWS ==`);
    console.log(out);
  } catch (e) { console.error("err:", e.message); }
  finally { if (sess) sess.close(); if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} } }
  console.log("DONE");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
