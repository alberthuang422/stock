// 通过本机 Chrome CDP 抓取 Yahoo chart API 数据：KO/MO/PM/^GSPC/XLP
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
const TICKERS = [
  { tk: "KO", p1: new Date("1960-01-01").getTime() / 1000, name: "ko" },
  { tk: "MO", p1: new Date("1970-01-01").getTime() / 1000, name: "mo" },
  { tk: "PM", p1: new Date("2008-01-01").getTime() / 1000, name: "pm" },
  { tk: "%5EGSPC", p1: new Date("1976-01-01").getTime() / 1000, name: "gspc" },
  { tk: "XLP", p1: new Date("1998-01-01").getTime() / 1000, name: "xlp" },
];

async function fetchChart(browser, ticker, period1) {
  const page = await browser.newPage();
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?period1=${Math.floor(period1)}&period2=${Math.floor(Date.now() / 1000)}&interval=1d&events=history&includeAdjustedClose=true`;
  let jsonText = null;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(3500);
    jsonText = await page.evaluate(() => document.body.innerText.trim());
  } catch (e) {
    console.error(ticker, "goto err:", e.message);
  }
  await page.close();
  if (!jsonText || !jsonText.startsWith("{")) {
    const page2 = await browser.newPage();
    try {
      await page2.goto("https://finance.yahoo.com", { waitUntil: "domcontentloaded", timeout: 45000 });
      await page2.waitForTimeout(3000);
      jsonText = await page2.evaluate(async (u) => {
        const r = await fetch(u);
        return await r.text();
      }, url);
    } catch (e) {
      console.error(ticker, "fetch err:", e.message);
    }
    await page2.close();
  }
  return jsonText;
}

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  console.log("CDP connected");
  for (const t of TICKERS) {
    const txt = await fetchChart(browser, t.tk, t.p1);
    if (!txt) { console.error(t.tk, "no data"); continue; }
    let j;
    try { j = JSON.parse(txt); } catch (e) { console.error(t.tk, "not json, head:", txt.slice(0, 200)); continue; }
    const res = j.chart && j.chart.result && j.chart.result[0];
    if (!res) { console.error(t.tk, "no result:", JSON.stringify(j).slice(0, 300)); continue; }
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
    const dir = path.join(OUT_ROOT, t.name);
    fs.mkdirSync(dir, { recursive: true });
    const csv = ["date,open,high,low,close,volume,adj_close",
      ...rows.map(r => r.join(","))].join("\n");
    fs.writeFileSync(path.join(dir, `${t.name}, 1D.csv`), csv);
    console.log(`${t.tk}(${t.name}): ${rows.length} 行, ${rows[0][0]} ~ ${rows[rows.length - 1][0]} 已保存`);
  }
  await browser.close();
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
