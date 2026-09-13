const { chromium } = require("playwright-core");
(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const page = await browser.newPage();
  const errs = [];
  page.on("pageerror", e => errs.push(String(e).slice(0, 300)));
  page.on("console", m => { if (m.type() === "error") errs.push("console:" + m.text().slice(0, 200)); });
  await page.goto("file:///Users/alberthuang/Desktop/股票分析/reports/81_KMI金德摩根深度分析/补充_天然气原油相关性/相关性分析.html", { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  const res = await page.evaluate(() => ({
    canvases: document.querySelectorAll("canvas").length,
    divs: ["c1", "c2", "c4", "c_pie"].map(id => ({ id, has: !!document.getElementById(id) })),
    title: document.title,
    terms: document.querySelectorAll(".term").length,
  }));
  console.log(JSON.stringify(res, null, 1));
  console.log("pageerrors:", errs.length ? errs : "none");
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
