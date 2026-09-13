const { chromium } = require("playwright-core");
const path = require("path");
(async () => {
  const exe = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1600 } });
  const logs = [];
  page.on("pageerror", e => logs.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") logs.push("CONSOLE: " + m.text()); });
  const file = "file://" + path.resolve(__dirname, "../reports/93_棉花库消比与厄尔尼诺_20260912/index.html");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(6500);
  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("canvas")];
    const zero = canvases.filter(c => c.width === 0 || c.height === 0).length;
    return {
      totalCanvas: canvases.length, zeroSize: zero,
      tables: document.querySelectorAll("table").length,
      rows: document.querySelectorAll("table tr").length,
      h2n: document.querySelectorAll("h2").length,
      ddOk: typeof DD !== "undefined",
      d1n: (typeof DD !== "undefined" && DD.d1) ? DD.d1.length : 0,
      d2n: (typeof DD !== "undefined" && DD.d2) ? DD.d2.length : 0,
      d3n: (typeof DD !== "undefined" && DD.d3) ? DD.d3.length : 0,
      d4n: (typeof DD !== "undefined" && DD.d4) ? DD.d4.length : 0,
      d5n: (typeof DD !== "undefined" && DD.d5) ? DD.d5.length : 0,
      d6n: (typeof DD !== "undefined" && DD.d6) ? DD.d6.length : 0,
      d7n: (typeof DD !== "undefined" && DD.d7_cn) ? DD.d7_cn.length : 0,
      d8n: (typeof DD !== "undefined" && DD.d8_m) ? DD.d8_m.length : 0,
      bodyLen: document.body.innerText.length,
    };
  });
  console.log(JSON.stringify(info, null, 1));
  console.log("JS errors:", logs.length ? logs.slice(0, 8) : "NONE");
  await browser.close();
})();
