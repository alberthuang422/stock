// SSR 渲染自检: 无头渲染 vix_low_spy_dashboard/index.html, 验证 ECharts canvas 与页面完整
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1800 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });

  const file = "file://" + path.resolve(__dirname, "../reports/vix_low_spy_dashboard/index.html");
  await page.goto(file, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForTimeout(5000);

  const info = await page.evaluate(() => {
    const charts = Array.from(document.querySelectorAll("[id^='bt-custom-']")).map((el) => ({
      id: el.id, hasCanvas: !!el.querySelector("canvas"), h: el.offsetHeight,
    }));
    const modCards = document.querySelectorAll(".bt-card, [class*='module']").length;
    const tabs = Array.from(document.querySelectorAll("[class*='tab']")).map((t) => t.textContent.trim()).slice(0, 10);
    return { charts, modCards, tabs };
  });

  console.log("charts:", JSON.stringify(info.charts));
  const canvases = info.charts.filter((c) => c.hasCanvas).length;
  console.log("canvas count:", canvases, "/", info.charts.length);
  console.log("js errors:", errors.length ? errors.join("\n") : "none");

  // 事件明细 tab 切过去验证表格行数
  await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll("*"));
    const tab = els.find((e) => e.textContent.trim() === "事件明细" && e.children.length === 0);
    if (tab) tab.click();
  });
  await page.waitForTimeout(1500);
  const tabInfo = await page.evaluate(() => {
    const rows = document.querySelectorAll("table tbody tr").length;
    const body = document.body.innerText.length;
    return { rows, body };
  });
  console.log("明细 tab rows:", tabInfo.rows, "body chars:", tabInfo.body);

  await browser.close();
  if (canvases === 0 || errors.length > 0) {
    console.log("RESULT: FAIL");
    process.exit(1);
  }
  console.log("RESULT: PASS");
})().catch((e) => { console.error("FATAL:", e); process.exit(1); });