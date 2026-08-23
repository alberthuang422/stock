// 原生 CDP 抓取 Yahoo chart JSON：V / MA / KBWB / QQQ / XLK
// 用于：visa/master 银行卡 vs KBWB 银行ETF + vs 科技(QQQ/XLK) 相关性分析
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
const TICKERS = ["V", "MA", "KBWB", "QQQ", "XLK"];
const PERIOD1 = Math.floor(new Date("1998-01-01").getTime() / 1000);
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

async function fetchChart(ticker) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?period1=${PERIOD1}&period2=${Math.floor(Date.now() / 1000)}&interval=1d&events=history&includeAdjustedClose=true`;
  let target = null;
  let sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    if (!resp.ok) throw new Error("new tab: " + resp.status);
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP;
    await sess.send("Page.enable");
    await sess.send("Page.navigate", { url });
    await sleep(8000);
    const r = await sess.send("Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
    return r && r.result && r.result.value != null ? String(r.result.value).trim() : null;
  } catch (e) {
    console.error(ticker, "err:", e.message);
    return null;
  } finally {
    if (sess) sess.close();
    if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }
  }
}

(async () => {
  for (const tk of TICKERS) {
    const txt = await fetchChart(tk);
    if (!txt) { console.error(tk, "no data"); continue; }
    let j;
    try { j = JSON.parse(txt); } catch (e) { console.error(tk, "not json, head:", txt.slice(0, 200)); continue; }
    const res = j.chart && j.chart.result && j.chart.result[0];
    if (!res) { console.error(tk, "no result:", JSON.stringify(j).slice(0, 200)); continue; }
    const ts = res.timestamp;
    const q = res.indicators.quote[0];
    const adj = res.indicators.adjclose && res.indicators.adjclose[0] ? res.indicators.adjclose[0].adjclose : [];
    const rows = [];
    for (let i = 0; i < ts.length; i++) {
      if (q.close[i] == null) continue;
      const d = new Date(ts[i] * 1000);
      const dateStr = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`;
      rows.push([dateStr, q.open[i], q.high[i], q.low[i], q.close[i], q.volume[i], adj[i] ?? q.close[i]]);
    }
    const dir = path.join(OUT_ROOT, tk.toLowerCase());
    fs.mkdirSync(dir, { recursive: true });
    const csv = ["date,open,high,low,close,volume,adj_close",
      ...rows.map(r => r.join(","))].join("\n");
    fs.writeFileSync(path.join(dir, `${tk}, 1D.csv`), csv);
    console.log(`${tk}: ${rows.length} 行, ${rows[0][0]} ~ ${rows[rows.length - 1][0]} 已保存`);
  }
  console.log("DONE");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });