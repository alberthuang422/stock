const { chromium } = require("playwright-core");
const path = require("path");
(async () => {
  const exe = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1600 } });
  const logs = [];
  page.on("pageerror", e => logs.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") logs.push("CONSOLE: " + m.text()); });
  const file = "file://" + path.resolve(__dirname, "../reports/91_白糖可贸易库存与价格解释力_20260912/index.html");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(6500);
  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("canvas")];
    const zero = canvases.filter(c => c.width === 0 || c.height === 0).length;
    return {
      totalCanvas: canvases.length, zeroSize: zero,
      tables: document.querySelectorAll("table").length,
      rows: document.querySelectorAll("table tr").length,
      ddOk: typeof DD !== "undefined" && DD.d1 && DD.d1.length > 0,
      d1n: (typeof DD !== "undefined" && DD.d1) ? DD.d1.length : 0,
      d3n: (typeof DD !== "undefined" && DD.d3) ? DD.d3.length : 0,
      d6a: (typeof DD !== "undefined" && DD.d6) ? DD.d6.a.filter(x => x != null).length : 0,
      d6b: (typeof DD !== "undefined" && DD.d6) ? DD.d6.b.filter(x => x != null).length : 0,
      h2n: document.querySelectorAll("h2").length,
    };
  });
  console.log(JSON.stringify(info, null, 1));
  console.log("JS errors:", logs.length ? logs.slice(0, 8) : "NONE");
  await browser.close();
})();
