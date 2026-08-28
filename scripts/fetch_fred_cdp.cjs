// 通过 CDP 页内 fetch 抓取 FRED CSV（页面导航后执行 fetch，处理跨域）
const fs = require("fs");
const path = require("path");
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));
const OUT = path.resolve(__dirname, "../data/us_treasury");

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

async function fetchFred(seriesId) {
  const url = `https://fred.stlouisfed.org/graph/fredgraph.csv?id=${seriesId}`;
  let target = null;
  let sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP;
    await sess.send("Page.enable");
    // 先导航到 fred 官网（同源），再页内 fetch CSV
    await sess.send("Page.navigate", { url: "https://fred.stlouisfed.org/" });
    await sleep(4000);
    const expr = `(async () => {
      try {
        const r = await fetch("${url}");
        if (!r.ok) return "HTTP_ERR:" + r.status;
        return await r.text();
      } catch (e) { return "FETCH_ERR:" + e.message; }
    })()`;
    const r = await sess.send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
    return r && r.result && r.result.value != null ? String(r.result.value) : null;
  } catch (e) {
    console.error(seriesId, "err:", e.message);
    return null;
  } finally {
    if (sess) sess.close();
    if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }
  }
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const sid of ["DGS2", "DGS10"]) {
    const txt = await fetchFred(sid);
    if (!txt || txt.startsWith("HTTP_ERR") || txt.startsWith("FETCH_ERR")) {
      console.error(sid, "no data:", txt?.slice(0, 120));
      continue;
    }
    const lines = txt.split("\n").filter(l => /^\d{4}-\d{2}-\d{2},/.test(l.trim()));
    const csv = ["observation_date,value", ...lines].join("\n");
    fs.writeFileSync(path.join(OUT, `${sid}.csv`), csv);
    console.log(`${sid}: ${lines.length} 行, 末 ${lines[lines.length-1]?.slice(0,10)}`);
  }
  console.log("DONE");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });