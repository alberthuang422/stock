// 诊断2: module-host 容器状态 + 手动执行 echarts.init 验证
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

  const diag = await page.evaluate(() => {
    const out = {};
    out.hosts = Array.from(document.querySelectorAll("[id^='module-host-']")).map((h) => ({
      id: h.id, len: h.innerHTML.length, cls: h.className,
    }));
    // 手动初始化
    const el = document.getElementById('bt-custom-main');
    try {
      const c = echarts.init(el);
      c.setOption({ xAxis: { type: 'category', data: ['a', 'b'] }, yAxis: {}, series: [{ type: 'bar', data: [1, 2] }] });
      out.manualInit = "OK childCount=" + el.childElementCount;
    } catch (e) {
      out.manualInit = "ERR " + e.message;
    }
    // 找带数据的 script 里 BT_PAYLOAD 或全局
    out.reportData = typeof window.__REPORT_DATA__ !== 'undefined' ? 'has global' : 'no global';
    return out;
  });
  console.log("diag2:", JSON.stringify(diag, null, 1));
  console.log("js errors:", errors.length ? errors.join("\n---\n") : "none");
  await browser.close();
})().catch((e) => { console.error("FATAL:", e); process.exit(1); });