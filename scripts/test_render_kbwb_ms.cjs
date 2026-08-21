// 渲染测试: KBWB vs MS 相关性报告, 收集 JS 错误并截图
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 4800 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/13_kbwb支撑位/kbwb_ms_corr_report.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4000);

  const chartInfo = await page.evaluate(() => {
    const ids = ["ch_full", "ch_2026", "ch_roll", "ch_monthly", "ch_scatter", "ch_year", "ch_ratio"];
    const out = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS") : "MISSING";
    }
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  const hasData = await page.evaluate(() => typeof DATA !== "undefined" && DATA.blocks.length === 5);
  console.log("echarts loaded:", hasEcharts);
  console.log("DATA injected:", hasData);
  console.log("charts:", JSON.stringify(chartInfo));
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await page.screenshot({ path: "C:\\Users\\Administrator\\Desktop\\stock\\results\\kbwb_ms_corr_report_full.png", fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });