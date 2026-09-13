// KMI × 天然气/原油 相关性分析拉数（Yahoo chart API，经本机 Chrome CDP）
// 显式 ticker -> 输出目录/文件名 映射，避免 "NG=F" 这类符号污染目录名
// 用法：先确保 9222 端口有 Chrome 实例，再 node kmi_ng_cl_fetch.cjs
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
const PERIOD1 = 0; // 全历史

// symbol  -> { dir, file }
const MAP = {
  "KMI":   { dir: "kmi", file: "KMI, 1D.csv" },
  "NG=F":  { dir: "ng",  file: "NG=F, 1D.csv" },
  "CL=F":  { dir: "cl",  file: "CL, 1D.csv" },
  "UNG":   { dir: "ung", file: "UNG, 1D.csv" },
  "WMB":   { dir: "wmb", file: "WMB, 1D.csv" },
  "XLE":   { dir: "xle", file: "xle, 1D.csv" },
  "SPY":   { dir: "spy", file: "SPY, 1D.csv" }
};

async function grabJSON(browser, url) {
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

  for (const [tk, m] of Object.entries(MAP)) {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(tk)}?period1=${PERIOD1}&period2=${period2}&interval=1d&events=div%2Csplit&includeAdjustedClose=true`;
    console.log("fetching", tk);
    const txt = await grabJSON(browser, url);
    if (!txt) { console.error(tk, "空响应"); continue; }
    let j;
    try { j = JSON.parse(txt); } catch (e) {
      console.error(tk, "非 JSON，头部:", txt.slice(0, 160));
      continue;
    }
    const res = j.chart && j.chart.result && j.chart.result[0];
    if (!res) { console.error(tk, "无 result:", JSON.stringify(j).slice(0, 300)); continue; }
    if (!res.timestamp) { console.error(tk, "meta:", JSON.stringify(res.meta || {}).slice(0, 300)); continue; }

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

    const dir = path.join(OUT_ROOT, m.dir);
    fs.mkdirSync(dir, { recursive: true });
    const csv = ["date,open,high,low,close,volume,adj_close",
      ...rows.map(r => r.join(","))].join("\n");
    fs.writeFileSync(path.join(dir, m.file), csv);
    console.log(`  ${tk} -> data/${m.dir}/${m.file}: ${rows.length} 行, ${rows[0][0]} ~ ${rows[rows.length - 1][0]}`);
  }
  await browser.close();
  console.log("done");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
