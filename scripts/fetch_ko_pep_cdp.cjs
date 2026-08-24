// 原生 CDP(proxy :3456) 抓取 Yahoo chart JSON：PEP（并刷新 KO 至最新）
// 用法：建 tab → navigate → sleep → Runtime.evaluate(document.body.innerText) → 解析落盘
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
const TICKERS = ["PEP", "KO"];
const PERIOD1 = Math.floor(new Date("1990-01-01").getTime() / 1000);
const PROXY = "http://localhost:3456";
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function fetchChart(ticker) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?period1=${PERIOD1}&period2=${Math.floor(Date.now() / 1000)}&interval=1d&events=history&includeAdjustedClose=true`;
  let target = null;
  try {
    // 建后台 tab（PUT /json/new 忽略 url，须 navigate）
    const resp = await fetch(`${PROXY}/new`, { method: "POST", body: url });
    const t = await resp.json();
    target = t.targetId || t.id || (t.target && t.target.targetId);
    if (!target) { console.error(ticker, "no target:", JSON.stringify(t).slice(0, 200)); return null; }
    // 等页面加载完成
    let txt = null;
    for (let i = 0; i < 8; i++) {
      await sleep(1500);
      const ev = await fetch(`${PROXY}/eval?target=${target}`, {
        method: "POST",
        body: "document.readyState + '|' + (document.body ? document.body.innerText.length : 0)"
      }).then(r => r.json()).catch(() => null);
      const v = ev && ev.result ? ev.result.value : ev && ev.value;
      if (v && typeof v === "string") {
        const [rs, len] = v.split("|");
        if (rs === "complete" && Number(len) > 100) {
          const full = await fetch(`${PROXY}/eval?target=${target}`, {
            method: "POST",
            body: "document.body.innerText"
          }).then(r => r.json()).catch(() => null);
          txt = full && full.result ? full.result.value : full && full.value;
          break;
        }
      }
    }
    return typeof txt === "string" && txt.trim() ? String(txt).trim() : null;
  } catch (e) {
    console.error(ticker, "err:", e.message);
    return null;
  } finally {
    if (target) { try { await fetch(`${PROXY}/close?target=${target}`); } catch {} }
  }
}

(async () => {
  for (const tk of TICKERS) {
    const txt = await fetchChart(tk);
    if (!txt) { console.error(tk, "no data"); continue; }
    let j;
    try { j = JSON.parse(txt); } catch (e) { console.error(tk, "not json, head:", txt.slice(0, 200)); continue; }
    const res = j.chart && j.chart.result && j.chart.result[0];
    if (!res) { console.error(tk, "no result:", JSON.stringify(j).slice(0, 300)); continue; }
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