// 渲染验证 32/37 号报告：检查 ECharts 图表 canvas 渲染与 y 轴数据范围
const { chromium } = require("playwright-core");
const path = require("path");

const TARGETS = [
  {
    file: "../reports/32_ko_科技医药相关性/index.html",
    charts: ["chart_roll_comp", "chart_year", "chart_monthly"],
  },
  {
    file: "../reports/37_ko_xlv_dji相关性/index.html",
    charts: ["chart_roll_comp", "chart_year", "chart_monthly"],
  },
];

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 2400 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  for (const t of TARGETS) {
    const file = path.resolve(__dirname, t.file);
    await page.goto("file://" + file, { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(3500);
    const info = await page.evaluate((chartIds) => {
      const out = {};
      for (const id of chartIds) {
        const el = document.getElementById(id);
        const inst = window.echarts ? echarts.getInstanceByDom(el) : null;
        if (!el) { out[id] = { status: "MISSING" }; continue; }
        const canvas = el.querySelector("canvas");
        if (!inst) { out[id] = { status: "NO-INSTANCE", canvas: !!canvas }; continue; }
        const opt = inst.getOption();
        // y 轴范围
        const yMin = opt.yAxis[0] && opt.yAxis[0].min;
        const yMax = opt.yAxis[0] && opt.yAxis[0].max;
        // 各系列数据点值域
        const seriesInfo = opt.series.map(s => {
          const data = (s.data || []).filter(v => v !== null && v !== undefined && !isNaN(v));
          return {
            name: s.name,
            n: data.length,
            min: data.length ? Math.min(...data) : null,
            max: data.length ? Math.max(...data) : null,
          };
        });
        // 检查是否有数据点超出 y 轴范围
        const overflow = seriesInfo.filter(s => s.n > 0 && (
          (typeof yMin === "number" && s.min < yMin) || (typeof yMax === "number" && s.max > yMax)
        )).map(s => `${s.name}: ${s.min}~${s.max} vs y[${yMin},${yMax}]`);
        out[id] = {
          status: "OK",
          canvas: !!canvas,
          yAxis: [yMin, yMax],
          series: seriesInfo.slice(0, 3),
          overflow,
        };
      }
      return out;
    }, t.charts);
    console.log("=== " + path.basename(path.dirname(file)) + " ===");
    console.log(JSON.stringify(info, null, 1));
  }
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });