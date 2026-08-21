// 道指行业板块 + 龙头股 Yahoo chart 抓取（CDP 原生 WebSocket 模板）
// 22 标的：5 板块 ETF + SPY + ^VIX + 15 成分股
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
// dir: 输出目录名（小写）; q: Yahoo 请求用代码
const TARGETS = [
  { dir: "xlf", q: "XLF" }, { dir: "xlk", q: "XLK" }, { dir: "xli", q: "XLI" },
  { dir: "xlv", q: "XLV" }, { dir: "xlp", q: "XLP" },
  { dir: "spy", q: "SPY" }, { dir: "vix", q: "^VIX" },
  { dir: "jpm", q: "JPM" }, { dir: "gs", q: "GS" }, { dir: "axp", q: "AXP" },
  { dir: "msft", q: "MSFT" }, { dir: "v", q: "V" }, { dir: "ma", q: "MA" },
  { dir: "cat", q: "CAT" }, { dir: "hon", q: "HON" }, { dir: "ba", q: "BA" },
  { dir: "unh", q: "UNH" }, { dir: "jnj", q: "JNJ" }, { dir: "amgn", q: "AMGN" },
  { dir: "wmt", q: "WMT" }, { dir: "pg", q: "PG" }, { dir: "ko", q: "KO" },
];
const PERIOD1 = Math.floor(new Date("1995-01-01").getTime() / 1000);
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

async function fetchChart(sym) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?period1=${PERIOD1}&period2=${Math.floor(Date.now() / 1000)}&interval=1d&events=history&includeAdjustedClose=true`;
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
    await sleep(6500);
    const r = await sess.send("Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
    return r && r.result && r.result.value != null ? String(r.result.value).trim() : null;
  } catch (e) {
    console.error(sym, "err:", e.message);
    return null;
  } finally {
    if (sess) sess.close();
    if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }
  }
}

(async () => {
  const failed = [];
  for (const t of TARGETS) {
    const txt = await fetchChart(t.q);
    if (!txt) { console.error(t.q, "no data"); failed.push(t.dir); continue; }
    let j;
    try { j = JSON.parse(txt); } catch (e) { console.error(t.q, "not json"); failed.push(t.dir); continue; }
    const res = j.chart && j.chart.result && j.chart.result[0];
    if (!res) { console.error(t.q, "no result:", JSON.stringify(j).slice(0, 150)); failed.push(t.dir); continue; }
    const ts = res.timestamp;
    const q = res.indicators.quote[0];
    const adj = res.indicators.adjclose && res.indicators.adjclose[0] ? res.indicators.adjclose[0].adjclose : [];
    const rows = [];
    for (let i = 0; i < ts.length; i++) {
      if (q.close[i] == null) continue;
      const d = new Date(ts[i] * 1000);
      const dateStr = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`;
      rows.push([dateStr, q.open[i], q.high[i], q.low[i], q.close[i], q.volume[i] ?? 0, adj[i] ?? q.close[i]]);
    }
    const dir = path.join(OUT_ROOT, t.dir);
    fs.mkdirSync(dir, { recursive: true });
    const csv = ["date,open,high,low,close,volume,adj_close",
      ...rows.map(r => r.join(","))].join("\n");
    fs.writeFileSync(path.join(dir, `${t.dir}, 1D.csv`), csv);
    console.log(`${t.q}: ${rows.length} rows ${rows[0][0]}~${rows[rows.length - 1][0]} saved`);
  }
  console.log(failed.length ? "FAILED: " + failed.join(",") : "ALL DONE");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
