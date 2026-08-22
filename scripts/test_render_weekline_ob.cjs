// SSR 渲染测试：weekline_ob_report.html
// 用本机 Chrome 无头渲染，检查 JS 无异常、图表容器有 canvas
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1200 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });
  const file = "file:///" + path.resolve(__dirname, "../reports/12_周线超买/weekline_ob_report.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  // 等 ECharts 渲染
  await page.waitForTimeout(4000);
  const nCanvas = await page.evaluate(() => document.querySelectorAll("canvas").length);
  const nFig = await page.evaluate(() => document.querySelectorAll(".fig").length);
  const nCards = await page.evaluate(() => document.querySelectorAll(".card").length);
  const htmlLen = await page.evaluate(() => document.documentElement.outerHTML.length);
  console.log("canvas:", nCanvas, "| fig:", nFig, "| cards:", nCards, "| htmlLen:", htmlLen);
  if (errors.length) {
    console.log("ERRORS(" + errors.length + "):");
    errors.slice(0, 10).forEach(e => console.log("  ", e));
  } else {
    console.log("NO JS ERRORS");
  }
  await page.screenshot({ path: path.resolve(__dirname, "../results/weekline_ob_report_shot.png"), fullPage: false });
  await browser.close();
})();