// 增量拉取 ^VIX + SPY 最近 30 个交易日 (2026-08-01 起), 用于定位当前 VIX 状态
// 通过本机 Chrome CDP -> Yahoo chart API
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data/tmp_vix_spy_update");
const PERIOD1 = Math.floor(new Date("2026-08-01T00:00:00Z").getTime() / 1000);
const TICKERS = ["^VIX", "SPY"];

async function fetchChart(browser, ticker) {
  const page = await browser.newPage();
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(ticker)}?period1=${PERIOD1}&period2=${Math.floor(Date.now() / 1000)}&interval=1d&events=history&includeAdjustedClose=true`;
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
      await page2.waitForTimeout(2500);
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
  fs.mkdirSync(OUT_ROOT, { recursive: true });
  for (const tk of TICKERS) {
    const txt = await fetchChart(browser, tk);
    if (!txt) { console.error(tk, "no data"); continue; }
    let j;
    try { j = JSON.parse(txt); } catch (e) { console.error(tk, "not json, head:", txt.slice(0, 150)); continue; }
    const res = j.chart && j.chart.result && j.chart.result[0];
    if (!res) { console.error(tk, "no result:", JSON.stringify(j).slice(0, 150)); continue; }
    const ts = res.timestamp;
    const q = res.indicators.quote[0];
    const rows = [];
    for (let i = 0; i < ts.length; i++) {
      if (q.close[i] == null) continue;
      const d = new Date(ts[i] * 1000);
      const dateStr = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`;
      rows.push([dateStr, q.open[i], q.high[i], q.low[i], q.close[i], q.volume[i], q.close[i]]);
    }
    const safe = tk === "^VIX" ? "vix" : "spy";
    const fn = tk === "^VIX" ? "VIX_update.csv" : "SPY_update.csv";
    const csv = ["date,open,high,low,close,volume,adj_close",
      ...rows.map(r => r.join(","))].join("\n");
    fs.writeFileSync(path.join(OUT_ROOT, fn), csv);
    console.log(`${tk}: ${rows.length} 行, ${rows[0] && rows[0][0]} ~ ${rows[rows.length - 1] && rows[rows.length - 1][0]}`);
  }
  await browser.close();
})().catch(e => { console.error("FATAL:", e); process.exit(1); });