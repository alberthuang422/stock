// 渲染测试: 加载 VST × UTES 分阶段报告, 收集 JS 错误并截图
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 3000 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/05_vst_utes/vst_utes_phase_report.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);

  const chartInfo = await page.evaluate(() => {
    const ids = ["chart_norm", "chart_roll", "chart_year", "chart_ratio"];
    const out = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS") : "MISSING";
    }
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  console.log("echarts loaded:", hasEcharts);
  console.log("charts:", JSON.stringify(chartInfo));
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await page.screenshot({ path: "/tmp/vst_utes_report_top.png", fullPage: false });
  await page.screenshot({ path: "/tmp/vst_utes_report_full.png", fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });
