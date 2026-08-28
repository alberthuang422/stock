// 快速渲染验证：打开 53 号报告，检查 console 错误与 ECharts canvas
const { chromium } = require("playwright-core");
(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const page = await browser.newPage();
  const errs = [];
  page.on("console", m => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  page.on("pageerror", e => errs.push("pageerror: " + String(e).slice(0, 200)));
  const url = "file:///C:/Users/Administrator/Desktop/stock/reports/53_%E9%87%91%E8%9E%8D%E7%A7%91%E6%8A%80%E8%B4%A2%E6%8A%A5%E6%97%A5%E7%9B%B8%E5%85%B3%E6%80%A7/index.html";
  await page.goto(url, { waitUntil: "load", timeout: 45000 });
  await page.waitForTimeout(5000);
  const canvases = await page.evaluate(() => document.querySelectorAll("canvas").length);
  const h1 = await page.evaluate(() => document.querySelector("h1") ? document.querySelector("h1").textContent : null);
  const tables = await page.evaluate(() => document.querySelectorAll("table").length);
  console.log("H1:", h1);
  console.log("canvas 数量:", canvases, "| table 数量:", tables);
  console.log("console 错误:", errs.length ? errs : "无");
  await page.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });