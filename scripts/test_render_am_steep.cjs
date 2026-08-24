// 渲染测试: 加载资管×利差走阔报告, 收集 JS 错误并验证图表
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 4200 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/30_资管陡峭化/index.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4000);

  const chartInfo = await page.evaluate(() => {
    const ids = ["c1", "c2", "c3", "c4", "c5a", "c5b", "c5c", "c5d"];
    const out = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS") : "MISSING";
    }
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  const tableRows = await page.evaluate(() => document.querySelectorAll("table tr").length);
  const h1 = await page.evaluate(() => document.querySelector("h1").textContent);
  console.log("echarts loaded:", hasEcharts);
  console.log("h1:", h1);
  console.log("charts:", JSON.stringify(chartInfo));
  console.log("table rows:", tableRows);
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });