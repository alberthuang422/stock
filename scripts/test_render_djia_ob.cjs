// SSR 渲染测试：djia_ob_cross_report.html — 验证图表 canvas 与表格行数
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1600 } });
  const logs = [];
  page.on("pageerror", e => logs.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") logs.push("CONSOLE: " + m.text()); });
  const file = "file:///" + path.resolve(__dirname, "../reports/32_道指板块超买横向/djia_ob_cross_report.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(5000);
  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("canvas")];
    const zero = canvases.filter(c => c.width === 0 || c.height === 0).length;
    const tbodies = [...document.querySelectorAll("tbody")].map(t => t.querySelectorAll("tr").length);
    return { totalCanvas: canvases.length, zeroSize: zero, tbodies,
             dataTicks: typeof DATA !== "undefined" ? DATA.ticks.length : "DATA undefined" };
  });
  console.log("totalCanvas:", info.totalCanvas, "| zeroSize:", info.zeroSize);
  console.log("tbodies rows:", JSON.stringify(info.tbodies));
  console.log("DATA.ticks:", info.dataTicks);
  console.log("JS errors:", logs.length ? logs.slice(0, 10) : "NONE");
  await browser.close();
})();