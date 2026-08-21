// 渲染测试: SBUX 财报研究报告
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 4000 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/07_sbux星巴克/sbux_report.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3500);

  const chartInfo = await page.evaluate(() => {
    const ids = ["chart1", "chart2", "chart3", "chart4"];
    const out = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS") : "MISSING";
    }
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  const dataLoaded = await page.evaluate(() => window.SBUX_DATA && window.SBUX_DATA.monthly.length);
  console.log("echarts loaded:", hasEcharts);
  console.log("sbux_data loaded, monthly len:", dataLoaded);
  console.log("charts:", JSON.stringify(chartInfo));
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await page.screenshot({ path: "/tmp/sbux_report_top.png", fullPage: false });
  await page.screenshot({ path: "/tmp/sbux_report_full.png", fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });
