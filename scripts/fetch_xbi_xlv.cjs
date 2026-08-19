// 通过本机 Chrome CDP 抓取 Yahoo chart API 数据
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
const TICKERS = ["XBI", "XLV"];
const PERIOD1 = Math.floor(new Date("2015-01-01").getTime() / 1000);

async function fetchChart(browser, ticker) {
  const page = await browser.newPage();
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?period1=${PERIOD1}&period2=${Math.floor(Date.now() / 1000)}&interval=1d&events=history&includeAdjustedClose=true`;
  let jsonText = null;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    // 等 body 出现 JSON
    await page.waitForTimeout(4000);
    jsonText = await page.evaluate(() => document.body.innerText.trim());
  } catch (e) {
    console.error(ticker, "goto err:", e.message);
  }
  await page.close();
  if (!jsonText || !jsonText.startsWith("{")) {
    // 尝试页面内 fetch（同源）
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
  for (const tk of TICKERS) {
    const txt = await fetchChart(browser, tk);
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
    console.log(`${tk}: ${rows.length} 行, ${rows[0][0]} ~ ${rows[rows.length-1][0]} 已保存`);
  }
  await browser.close();
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
