// 内容级验证：抽取报告关键文本与画廊标题，确认数据渲染
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1600 } });
  const file = "file:///" + path.resolve(__dirname, "../reports/13_djia_sector_support/djia_sector_support_report.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);
  const info = await page.evaluate(() => {
    const kpis = [...document.querySelectorAll(".kpi .num")].map(e => e.textContent.trim());
    const figs = [...document.querySelectorAll(".fig .ft")].map(e => e.textContent.trim());
    const h2s = [...document.querySelectorAll("h2")].map(e => e.textContent.trim());
    const sectorRow1 = document.querySelector("table tbody tr");
    const evRowCount = document.querySelectorAll("table tbody tr").length;
    // 检查图表是否有实际图形元素（canvas 非空 + ECharts 实例存在）
    const charts = [...document.querySelectorAll("[id^=ch_],[id^=gk_]")].filter(el => echarts.getInstanceByDom(el));
    return { kpis, figs, h2s: h2s.length, sectorRow1: sectorRow1 ? sectorRow1.textContent.slice(0, 160) : null, evRowCount, chartInstances: charts.length };
  });
  console.log("KPI:", JSON.stringify(info.kpis));
  console.log("gallery figs:", info.figs.length, "->", info.figs.slice(0, 4).join(" | "));
  console.log("h2 数量:", info.h2s, "| ECharts 实例:", info.chartInstances, "| 表格行:", info.evRowCount);
  console.log("板块表首行:", info.sectorRow1);
  await browser.close();
})();
