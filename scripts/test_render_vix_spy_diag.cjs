// SSR 渲染自检诊断: 查 echarts 是否加载、custom_html body 内容、script 执行情况
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1800 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });
  page.on("requestfailed", (r) => errors.push("reqfail: " + r.url() + " -> " + (r.failure()?.errorText || "")));

  const file = "file://" + path.resolve(__dirname, "../reports/vix_low_spy_dashboard/index.html");
  await page.goto(file, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForTimeout(6000);

  const diag = await page.evaluate(() => {
    const out = {};
    out.echartsType = typeof window.echarts;
    out.moduleCount = document.querySelectorAll(".bt-card, [class*='card']").length;
    // 找 custom_html 容器
    const customs = Array.from(document.querySelectorAll("[id^='bt-custom-']")).map((el) => ({
      id: el.id, w: el.offsetWidth, h: el.offsetHeight, childCount: el.childElementCount,
      innerHTMLlen: el.innerHTML.length,
      hasEchartsDom: !!el.querySelector("canvas, div[_echarts_instance_]"),
    }));
    out.customs = customs;
    // 检查是否有 script 未被替换
    out.inlineScripts = Array.from(document.querySelectorAll("script:not([src])")).length;
    out.srcScripts = Array.from(document.querySelectorAll("script[src]")).map((s) => s.src);
    return out;
  });

  console.log("diag:", JSON.stringify(diag, null, 1));
  console.log("js errors:", errors.length ? errors.join("\n---\n") : "none");
  await browser.close();
})().catch((e) => { console.error("FATAL:", e); process.exit(1); });