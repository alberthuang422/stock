// 渲染测试: 21_生物医药行业景气度, 收集 JS 错误并截图
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 3200 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/21_生物医药行业景气度/index.html");
  await page.goto("file://" + file.replace(/\\/g, "/"), { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);

  const chartInfo = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll("[id^='chart_']"));
    const out = {};
    for (const el of els) out[el.id] = el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS";
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  const h1 = await page.evaluate(() => document.querySelector("h1") ? document.querySelector("h1").innerText : "NO-H1");
  const totalTxt = await page.evaluate(() => {
    const el = document.querySelector(".verdict .b");
    return el ? el.innerText : "NO-VERDICT";
  });
  const items = await page.evaluate(() => document.querySelectorAll("table tbody tr").length);
  console.log("h1:", h1);
  console.log("verdict:", totalTxt);
  console.log("echarts loaded:", hasEcharts);
  console.log("charts:", JSON.stringify(chartInfo, null, 1));
  console.log("table rows:", items);
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await page.screenshot({ path: path.resolve(__dirname, "../results/biopharma_prosperity_render_top.png"), fullPage: false });
  await page.screenshot({ path: path.resolve(__dirname, "../results/biopharma_prosperity_render_full.png"), fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });