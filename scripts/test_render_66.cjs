// SSR 渲染验证：66 号报告（CVS×VIX>18）图表渲染无 JS 错误 + canvas 检查
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const page = await browser.newPage({ viewport: { width: 1360, height: 950 } });
  const errors = [];
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));

  const file = path.resolve(__dirname, "../reports/66_CVS与VIX高波动期表现/index.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(4000);

  const canvases = await page.evaluate(() => document.querySelectorAll("canvas").length);
  const charts = await page.evaluate(() => {
    return [...document.querySelectorAll(".chart")].map(c => ({
      id: c.id, w: c.clientWidth, h: c.clientHeight,
      canvas: c.querySelectorAll("canvas").length,
    }));
  });
  // 抽样检查关键图表的 series/点数
  const probe = await page.evaluate(() => {
    const out = {};
    const ids = ["ch_pan", "ch_bucket", "ch_shock", "ch_seg"];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (!el) { out[id] = "MISSING"; continue; }
      const inst = echarts.getInstanceByDom(el);
      if (!inst) { out[id] = "NO-INSTANCE"; continue; }
      const o = inst.getOption();
      const pts = o.series.map(s => (s.data || []).length);
      const x0 = (o.xAxis && o.xAxis[0] && o.xAxis[0].data) ? o.xAxis[0].data.length : -1;
      out[id] = { series: o.series.length, pts, xLen: x0 };
    }
    return out;
  });
  console.log("canvas total:", canvases);
  console.log("charts:", JSON.stringify(charts));
  console.log("probe:", JSON.stringify(probe, null, 1));
  console.log("JS errors:", errors.length ? errors : "NONE");

  await page.close();
  await browser.close();
  if (errors.length) process.exit(1);
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
