// 83 号报告渲染校验（Windows / playwright-core + 本机 Chrome）
const { chromium } = require("playwright-core");
const path = require("path");

const CHROME = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
const FILE = path.resolve(__dirname, "../reports/83_HO月差与EIA库存解构/index.html");

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--no-sandbox", "--disable-gpu"] });
  const page = await browser.newPage({ viewport: { width: 1360, height: 1200 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  await page.goto("file:///" + FILE.replace(/\\/g, "/"), { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(3500);

  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  const info = await page.evaluate(() => {
    const ids = ["c_scatter", "c_tl", "c_r2", "c_bucket", "c_hist"];
    const out = {};
    for (const id of ids) {
      const el = document.getElementById(id);
      out[id] = el ? (el.querySelector("canvas") ? "ok" : "NO-CANVAS") : "MISSING";
    }
    return out;
  });
  const apiOk = await page.evaluate(() => {
    const ids = ["c_scatter", "c_tl", "c_r2", "c_bucket", "c_hist"];
    const out = {};
    for (const id of ids) {
      try { out[id] = window.echarts.getInstanceByDom(document.getElementById(id)).getOption().series.length; }
      catch (e) { out[id] = "ERR:" + e.message; }
    }
    return out;
  });
  console.log("echarts:", hasEcharts);
  console.log("canvas:", JSON.stringify(info));
  console.log("series:", JSON.stringify(apiOk));
  console.log("errors:", errors.length ? errors.join(" | ") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });
