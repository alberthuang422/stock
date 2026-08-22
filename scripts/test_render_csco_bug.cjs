// 渲染测试: 加载 CSCO×BUG 报告, 收集 JS 错误并截图（Windows 本机 Chrome）
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 3000 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/19_csco_bug网络安全/csco_bug_corr_report.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);

  const chartInfo = await page.evaluate(() => {
    const ids = ["chart_norm", "chart_roll", "chart_mon", "chart_ratio"];
    const out = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS") : "MISSING";
    }
    // 检查 ECharts 实例数量与任一实例是否有 series 数据
    const instances = window.echarts ? echarts.getInstanceCount ? "n/a" : "n/a" : "no-echarts";
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  console.log("echarts loaded:", hasEcharts);
  console.log("charts:", JSON.stringify(chartInfo));
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await page.screenshot({ path: "C:/Users/Administrator/Desktop/stock/results/csco_bug_report_top.png", fullPage: false });
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });