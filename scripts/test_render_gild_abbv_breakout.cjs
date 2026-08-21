// 渲染测试: 加载 GILD/ABBV 横盘突破报告, 收集 JS 错误并截图
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1360, height: 3200 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/11_gild_abbv_breakout/gild_abbv_breakout_report.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);

  const info = await page.evaluate(() => {
    const out = {};
    const ids = ["chart_overview"];
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS") : "MISSING";
    }
    out.galleryItems = document.querySelectorAll("#gallery .fig").length;
    out.galleryCanvases = document.querySelectorAll("#gallery canvas").length;
    out.firstFigText = (document.querySelector("#gallery .cap") || {}).textContent || "NONE";
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  console.log("echarts loaded:", hasEcharts);
  console.log("overview:", info.chart_overview, "| gallery figs:", info.galleryItems, "| gallery canvases:", info.galleryCanvases);
  console.log("first fig caption:", info.firstFigText);
  console.log("errors:", errors.length ? errors.join("\n") : "none");

  await page.screenshot({ path: path.resolve(__dirname, "../reports/11_gild_abbv_breakout/render_top.png"), fullPage: false });
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.resolve(__dirname, "../reports/11_gild_abbv_breakout/render_bottom.png"), fullPage: false });
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });