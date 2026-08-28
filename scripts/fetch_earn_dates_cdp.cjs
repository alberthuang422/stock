// 通过本机 Chrome CDP 抓取 Yahoo earningsHistory（带 crumb），交叉验证财报日
const { chromium } = require("playwright-core");
const fs = require("fs");
const TICKERS = ["SOFI", "AFRM", "UPST"];
async function main() {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  console.log("CDP connected");
  const page = await browser.newPage();
  await page.goto("https://fc.yahoo.com", { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(2500);
  const crumb = await page.evaluate(async () => {
    const r = await fetch("https://query1.finance.yahoo.com/v1/test/getcrumb", { credentials: "include" });
    if (!r.ok) throw new Error("crumb status " + r.status);
    return await r.text();
  }).catch(e => { console.error("crumb err:", e.message); return null; });
  console.log("crumb:", crumb);
  if (!crumb) return;
  for (const tk of TICKERS) {
    const url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/" + tk + "?modules=earningsHistory&crumb=" + encodeURIComponent(crumb);
    const txt = await page.evaluate(async (u) => {
      const r = await fetch(u, { credentials: "include" });
      return await r.text();
    }, url);
    let j;
    try { j = JSON.parse(txt); } catch (e) { console.error(tk, "not json:", txt.slice(0, 150)); continue; }
    const q = j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
    const eh = q && q.earningsHistory && q.earningsHistory.history;
    if (!eh || !eh.length) { console.error(tk, "no eh:", JSON.stringify(j).slice(0, 250)); continue; }
    const rows = [];
    for (const r of eh) {
      const date = r.date && r.date.fmt ? r.date.fmt : null;
      const actual = r.actual && r.actual.raw != null ? r.actual.raw : null;
      const est = r.estimate && r.estimate.raw != null ? r.estimate.raw : null;
      const surprise = r.surprisePercent && r.surprisePercent.raw != null ? Math.round(r.surprisePercent.raw * 1000) / 1000 : null;
      rows.push([date, actual, est, surprise]);
    }
    fs.writeFileSync("C:/Users/Administrator/Desktop/stock/results/earn_dates_" + tk.toLowerCase() + ".json", JSON.stringify(rows, null, 1));
    console.log(tk + ": " + rows.length + " 期");
    for (const r of rows) console.log("  ", r.join(" | "));
  }
  await page.close();
  // 浏览器实例由主流程统一管理，此处不关闭
}
main().catch(e => { console.error("FATAL:", e); process.exit(1); });