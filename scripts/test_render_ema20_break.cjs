const { chromium } = require("playwright-core");
const path = require("path");
(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1700 } });
  const logs = [];
  page.on("pageerror", e => logs.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") logs.push("CONSOLE: " + m.text()); });
  const file = "file:///" + path.resolve(__dirname, "../reports/44_贴EMA20缩量跌破平台/index.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(6000);
  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("canvas")];
    const zero = canvases.filter(c => c.width === 0 || c.height === 0).length;
    const rows = document.querySelectorAll("#tab2 tbody tr").length;
    // K线浏览器检查
    const klineOk = (typeof KLINE !== "undefined") && KLINE.length > 0;
    const selOptions = document.querySelectorAll("#klineSel option").length;
    const kcard = document.querySelector("#klineCard") && document.querySelector("#klineCard").textContent.length > 20;
    return { totalCanvas: canvases.length, zeroSize: zero, evRows: rows,
             klineOk, klineN: klineOk ? KLINE.length : 0, selOptions, kcard,
             hasChart: typeof CHART !== "undefined",
             klinkCount: document.querySelectorAll("a.klink").length };
  });
  console.log("totalCanvas:", info.totalCanvas, "| zeroSize:", info.zeroSize, "| evRows:", info.evRows);
  console.log("klineOk:", info.klineOk, "| KLINE_N:", info.klineN, "| selOptions:", info.selOptions, "| kcard:", info.kcard);
  console.log("klinkCount:", info.klinkCount, "| chartData:", info.hasChart);
  // 测试 K 线切换
  const stepErr = await page.evaluate(() => {
    try { gotoKline(5); return "OK"; } catch (e) { return "ERR: " + e.message; }
  });
  console.log("gotoKline(5):", stepErr);
  // 截一张 K 线图
  await page.waitForTimeout(1500);
  const el = await page.$("#ch_kline");
  if (el) await el.screenshot({ path: path.resolve(__dirname, "../reports/44_贴EMA20缩量跌破平台/_kline_check.png") });
  console.log("JS errors:", logs.length ? logs.slice(0, 10) : "NONE");
  await browser.close();
})();
