// CDP 核实提价事实：Bing 搜索英文关键词，取前几条摘要
// 用法: node cdp_news_search.cjs "Hershey cocoa price increase 2026"
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function cdpSession(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let idc = 0;
  const pending = new Map();
  const openP = new Promise((res, rej) => {
    ws.onopen = res;
    ws.onerror = () => rej(new Error("ws open error"));
  });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++idc;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}

(async () => {
  const query = process.argv[2] || "Hershey price increase 2026";
  const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
  let target = null, sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP;
    await sess.send("Page.enable");
    await sess.send("Page.navigate", { url });
    await sleep(5000);
    const expr = `(() => {
      const items = [...document.querySelectorAll('.result')].slice(0, 6).map(r => {
        const t = r.querySelector('.result__title') ? r.querySelector('.result__title').innerText : '';
        const sn = r.querySelector('.result__snippet') ? r.querySelector('.result__snippet').innerText : '';
        return t.replace(/\\s+/g,' ').trim() + ' ||| ' + sn.replace(/\\s+/g,' ').trim().slice(0, 350);
      });
      return items.join('\\n====\\n');
    })()`;
    const r = await sess.send("Runtime.evaluate", { expression: expr, returnByValue: true });
    console.log(r.result.value || "NO_RESULTS");
  } catch (e) {
    console.error("err:", e.message);
  } finally {
    if (sess) sess.close();
    if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }
  }
  console.log("DONE");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });