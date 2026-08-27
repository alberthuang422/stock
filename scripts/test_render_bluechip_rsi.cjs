const { chromium } = require("playwright-core");
const path = require("path");
(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1600 } });
  const logs = [];
  page.on("pageerror", e => logs.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") logs.push("CONSOLE: " + m.text()); });
  const file = "file:///" + path.resolve(__dirname, "../reports/39_蓝筹RSI超卖买入/index.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(5000);
  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("canvas")];
    const zero = canvases.filter(c => c.width === 0 || c.height === 0).length;
    const rows = document.querySelectorAll("#tab2 tbody tr").length;
    return { totalCanvas: canvases.length, zeroSize: zero, evRows: rows,
             hasChart: typeof CHART !== "undefined" };
  });
  console.log("totalCanvas:", info.totalCanvas, "| zeroSize:", info.zeroSize, "| evRows:", info.evRows, "| chartData:", info.hasChart);
  console.log("JS errors:", logs.length ? logs.slice(0, 10) : "NONE");
  await browser.close();
})();