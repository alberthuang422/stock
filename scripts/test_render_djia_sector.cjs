// SSR 渲染测试：djia_sector_support_report.html — 验证主图表与画廊 K 线渲染
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1600 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });
  const file = "file:///" + path.resolve(__dirname, "../reports/13_道指板块支撑/djia_sector_support_report.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4500);
  // 滚动触发懒渲染
  await page.evaluate(async () => {
    for (let y = 0; y <= document.body.scrollHeight; y += 600) {
      await new Promise(r => setTimeout(r, 120));
    }
  });
  await page.waitForTimeout(2000);
  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("canvas")];
    const zero = canvases.filter(c => c.width === 0 || c.height === 0).length;
    const main = [...document.querySelectorAll("[id^=ch_] canvas")].length;
    const gal = [...document.querySelectorAll("[id^=gk_] canvas")].length;
    const evRows = document.querySelectorAll("table tbody tr").length;
    return { totalCanvas: canvases.length, zeroSize: zero, mainCharts: main, galleryCharts: gal, evRows };
  });
  console.log("totalCanvas:", info.totalCanvas, "| zeroSize:", info.zeroSize, "| mainCharts:", info.mainCharts, "| gallery:", info.galleryCharts, "| tableRows:", info.evRows);
  console.log("JS errors:", errors.length ? errors.slice(0, 8) : "NONE");
  await page.evaluate(() => { const el = document.getElementById("gallery"); el && el.scrollIntoView(); });
  await page.waitForTimeout(1200);
  await browser.close();
})();
