// 89 号报告渲染校验（4 张 ECharts 图 + 表格行数）
const { chromium } = require("playwright-core");
const path = require("path");

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FILE = path.resolve(__dirname, "../reports/89_厄尔尼诺与橡胶价格_20260912/index.html");

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true,
    args: ["--no-sandbox", "--disable-gpu"] });
  const page = await browser.newPage({ viewport: { width: 1400, height: 2600 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  await page.goto("file://" + FILE, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(5000);

  const info = await page.evaluate(() => {
    const out = { charts: {}, echarts: typeof window.echarts };
    for (const id of ["c1", "c2", "c3", "c4"]) {
      const el = document.getElementById(id);
      if (!el) { out.charts[id] = "NO-DIV"; continue; }
      const has = el.querySelector("canvas") ? "canvas" : "NO-CANVAS";
      try {
        const o = echarts.getInstanceByDom(el).getOption();
        out.charts[id] = has + " | series=" + o.series.length +
          " | pts=" + (o.series[0].data ? o.series[0].data.length : "?");
      } catch (e) { out.charts[id] = has + " | ERR:" + e.message; }
    }
    out.tables = document.querySelectorAll("table").length;
    out.rows = [...document.querySelectorAll("table")].map(t => t.querySelectorAll("tr").length);
    out.h2 = [...document.querySelectorAll("h2")].map(h => h.textContent.slice(0, 12));
    out.terms = document.querySelectorAll(".term").length;
    out.bodyLen = document.body.innerText.length;
    return out;
  });

  console.log("echarts:", info.echarts);
  for (const [k, v] of Object.entries(info.charts)) console.log(" ", k, "->", v);
  console.log("tables:", info.tables, "| rows:", JSON.stringify(info.rows));
  console.log("h2:", JSON.stringify(info.h2, null, 0));
  console.log("term spans:", info.terms, "| 正文字数:", info.bodyLen);
  console.log("errors:", errors.length ? errors.join(" | ") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });
