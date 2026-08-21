// SSR 渲染测试：weekline_ob_report.html — 验证画廊 K 线 canvas 是否真的有尺寸
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1200 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });
  const file = "file:///" + path.resolve(__dirname, "../reports/12_weekline_ob/weekline_ob_report.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4000);
  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("#gallery canvas")];
    const zero = canvases.filter(c => c.width === 0 || c.height === 0).length;
    const sizes = canvases.slice(0, 5).map(c => c.width + "x" + c.height);
    return {
      galleryCanvas: canvases.length,
      zeroSize: zero,
      firstSizes: sizes,
      figCount: document.querySelectorAll("#gallery .fig").length,
      mainCanvas: document.querySelectorAll("#ch_dd canvas, #ch_dist canvas, #ch_gap canvas").length,
    };
  });
  console.log("galleryCanvas:", info.galleryCanvas, "| zeroSize:", info.zeroSize, "| figCount:", info.figCount, "| mainCanvas:", info.mainCanvas);
  console.log("first 5 sizes:", info.firstSizes.join(", "));
  console.log("JS errors:", errors.length ? errors.slice(0, 8) : "NONE");
  await page.screenshot({ path: path.resolve(__dirname, "../results/weekline_ob_shot2.png") });
  await browser.close();
})();