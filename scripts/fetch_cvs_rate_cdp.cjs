// 通过本机 Chrome CDP 抓取 Yahoo chart API 日线数据（CVS 利率敏感性分析用）
// 用法：先确保 9222 端口有 Chrome 实例，再 node 本脚本
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
// CVS 主标的 + 管理式医疗同业（UNH/CI）+ 板块/大盘对照（XLV/SPY）
// 可用命令行覆盖：node fetch_cvs_rate_cdp.cjs CVS SPY
const TICKERS = process.argv.slice(2).length ? process.argv.slice(2)
                                             : ["CVS", "UNH", "CI", "XLV", "SPY"];
const PERIOD1 = 0; // 全历史，用于拆 pre-Aetna(2018前) / post-Aetna 两段

async function grabJSON(browser, url) {
  // 路线1：直接访问 Yahoo chart API
  let page = await browser.newPage();
  let txt = null;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(3500);
    txt = await page.evaluate(() => document.body.innerText.trim());
  } catch (e) {
    console.error("  route1 err:", e.message);
  }
  await page.close();
  if (txt && txt.startsWith("{")) return txt;

  // 路线2：先落地 finance.yahoo.com 拿 cookie/crumb，再页内同源 fetch
  const p2 = await browser.newPage();
  try {
    await p2.goto("https://finance.yahoo.com", { waitUntil: "domcontentloaded", timeout: 45000 });
    await p2.waitForTimeout(3000);
    txt = await p2.evaluate(async (u) => {
      const r = await fetch(u);
      return await r.text();
    }, url);
  } catch (e) {
    console.error("  route2 err:", e.message);
  }
  await p2.close();
  return txt;
}

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  console.log("CDP connected");
  const period2 = Math.floor(Date.now() / 1000);

  for (const tk of TICKERS) {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${tk}?period1=${PERIOD1}&period2=${period2}&interval=1d&events=div%2Csplit&includeAdjustedClose=true`;
    console.log("fetching", tk);
    const txt = await grabJSON(browser, url);
    if (!txt) { console.error(tk, "空响应"); continue; }
    let j;
    try { j = JSON.parse(txt); } catch (e) {
      console.error(tk, "非 JSON，头部:", txt.slice(0, 160));
      continue;
    }
    const res = j.chart && j.chart.result && j.chart.result[0];
    if (!res) { console.error(tk, "无 result:", JSON.stringify(j).slice(0, 200)); continue; }

    const ts = res.timestamp;
    const q = res.indicators.quote[0];
    const adjArr = res.indicators.adjclose && res.indicators.adjclose[0]
      ? res.indicators.adjclose[0].adjclose : [];
    const rows = [];
    for (let i = 0; i < ts.length; i++) {
      if (q.close[i] == null) continue;
      const d = new Date(ts[i] * 1000);
      const dateStr = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`;
      rows.push([dateStr, q.open[i], q.high[i], q.low[i], q.close[i], q.volume[i], adjArr[i] ?? q.close[i]]);
    }
    if (!rows.length) { console.error(tk, "0 行"); continue; }

    const dir = path.join(OUT_ROOT, tk.toLowerCase());
    fs.mkdirSync(dir, { recursive: true });
    const csv = ["date,open,high,low,close,volume,adj_close",
      ...rows.map(r => r.join(","))].join("\n");
    fs.writeFileSync(path.join(dir, `${tk}, 1D.csv`), csv);
    console.log(`  ${tk}: ${rows.length} 行, ${rows[0][0]} ~ ${rows[rows.length - 1][0]}`);
  }
  await browser.close();
  console.log("done");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
