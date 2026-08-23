// SSR 渲染测试: 用本机 Chrome 无头渲染 vix_low_spx_report.html, 检查 ECharts canvas 是否成功绘制
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1600 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });

  const file = "file://" + path.resolve(__dirname, "../reports/vix_low_spx_report.html");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4000);

  // 检查所有 chart 容器是否生成了 canvas
  const charts = await page.evaluate(() => {
    return Array.from(document.querySelectorAll(".chart")).map((el) => ({
      id: el.id, canvas: !!el.querySelector("canvas"), h: el.offsetHeight,
    }));
  });
  const canvases = charts.filter((c) => c.canvas).length;
  console.log("charts:", JSON.stringify(charts));

  const shot = path.resolve(__dirname, "../results/vix_low_report_ssr.png");
  console.log("canvas count:", canvases, "/", charts.length);
  console.log("js errors:", errors.length ? errors.join("\n") : "none");

  await browser.close();
  if (canvases !== charts.length || errors.length > 0) {
    console.log("RESULT: FAIL");
    process.exit(1);
  }
  console.log("RESULT: PASS");
})().catch((e) => { console.error("FATAL:", e); process.exit(1); });
