// SSR 渲染验证：63 号报告图表渲染无 JS 错误 + canvas 检查
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const page = await browser.newPage({ viewport: { width: 1300, height: 900 } });
  const errors = [];
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));

  const file = path.resolve(__dirname, "../reports/63_SOFI_AFRM_SQ相关性分析/index.html");
  await page.goto("file://" + file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3500);

  const canvases = await page.evaluate(() => document.querySelectorAll("canvas").length);
  const charts = await page.evaluate(() => {
    return [...document.querySelectorAll(".chart")].map(c => ({
      id: c.id, w: c.clientWidth, h: c.clientHeight,
      canvas: c.querySelectorAll("canvas").length,
    }));
  });
  // ECharts 实例检查
  const echartsOk = await page.evaluate(() => {
    try {
      const insts = echarts.getInstanceByDom(document.getElementById('c_nav')) &&
                    echarts.getInstanceByDom(document.getElementById('c_roll'));
      const opt = echarts.getInstanceByDom(document.getElementById('c_nav')).getOption();
      return { hasInstances: !!insts, seriesCount: opt.series.length, xLen: opt.xAxis[0].data.length };
    } catch (e) { return { err: e.message }; }
  });
  // 术语悬停元素存在
  const terms = await page.evaluate(() => document.querySelectorAll(".term").length);

  console.log("canvas total:", canvases);
  console.log("charts:", JSON.stringify(charts));
  console.log("echarts:", JSON.stringify(echartsOk));
  console.log("terms:", terms);
  console.log("JS errors:", errors.length ? errors : "NONE");

  await page.close();
  await browser.close();
  if (errors.length) process.exit(1);
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
