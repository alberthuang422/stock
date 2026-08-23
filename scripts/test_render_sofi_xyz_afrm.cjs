// SSR 渲染测试：验证 reports/sofi_xyz_afrm_report.html 图表渲染无 JS 错误
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true, args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1300, height: 900 } });
  const errors = [];
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));

  const file = path.resolve(__dirname, "../reports/sofi_xyz_afrm_report.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3500);

  // 检查 canvas 数量（ECharts 渲染后生成 canvas）
  const canvases = await page.evaluate(() => document.querySelectorAll("canvas").length);
  const charts = await page.evaluate(() => {
    return [...document.querySelectorAll(".chart")].map(c => ({
      id: c.id, w: c.clientWidth, h: c.clientHeight,
      canvas: c.querySelectorAll("canvas").length,
    }));
  });

  console.log("canvas total:", canvases);
  console.log("charts:", JSON.stringify(charts, null, 1));
  console.log("JS errors:", errors.length ? errors : "NONE");

  await browser.close();
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
