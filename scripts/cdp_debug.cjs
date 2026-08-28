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
  const url = "https://html.duckduckgo.com/html/?q=Hershey+cocoa+price+increase+2026";
  let target = null, sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP; await sess.send("Page.enable");
    await sess.send("Page.navigate", { url });
    await sleep(7000);
    const r = await sess.send("Runtime.evaluate", { expression: `JSON.stringify({title: document.title, len: document.body.innerText.length, text: document.body.innerText.slice(0, 600)})`, returnByValue: true });
    console.log(r.result.value);
  } catch (e) { console.error("err:", e.message); }
  finally { if (sess) sess.close(); if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} } }
  console.log("DONE");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
