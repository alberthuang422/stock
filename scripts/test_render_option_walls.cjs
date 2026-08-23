// 渲染测试: 期权墙八标的报告, 收集 JS 错误并截图
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

  const file = path.resolve(__dirname, "../reports/20_期权墙八标的/index.html");
  await page.goto("file://" + file.replace(/\\/g, "/"), { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);

  const chartInfo = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll("[id^='chart_']"));
    const out = {};
    for (const el of els) out[el.id] = el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS";
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  console.log("echarts loaded:", hasEcharts);
  console.log("charts:", JSON.stringify(chartInfo, null, 1));
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });
