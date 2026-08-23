// 渲染测试（仅验证，不交付截图）: V/MA 相关性报告, 收集 JS 错误 + 图表渲染状态
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

  const file = path.resolve(__dirname, "../reports/27_银行卡网络_银行科技相关性/visa_master_corr_report.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(5000);

  const ids = ["ch_roll_kbwb", "ch_2026_kbwb", "ch_roll_tech", "ch_2026_tech",
               "ch_scatter_kbwb", "ch_scatter_tech", "ch_year_kbwb", "ch_year_tech",
               "ch_ratio_all", "ch_monthly_kbwb"];
  const chartInfo = await page.evaluate((ids) => {
    const out = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS") : "MISSING";
    }
    return out;
  }, ids);
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  const hasData = await page.evaluate(() => typeof DATA !== "undefined" && !!DATA.pairs && !!DATA.pairs.V);
  console.log("echarts loaded:", hasEcharts);
  console.log("DATA injected:", hasData);
  console.log("charts:", JSON.stringify(chartInfo));
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });