// 渲染测试: 21_生物医药行业景气度, 收集 JS 错误并截图
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe",
    headless: true,
    args: ["--no-sandbox", "--disable-gpu"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 3200 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  const file = path.resolve(__dirname, "../reports/21_生物医药行业景气度/index.html");
  await page.goto("file://" + file.replace(/\\/g, "/"), { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(2500);

  const chartInfo = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll("[id^='chart_']"));
    const out = {};
    for (const el of els) out[el.id] = el.querySelector("canvas") ? "canvas-ok" : "NO-CANVAS";
    return out;
  });
  const hasEcharts = await page.evaluate(() => typeof window.echarts !== "undefined");
  const h1 = await page.evaluate(() => document.querySelector("h1") ? document.querySelector("h1").innerText : "NO-H1");
  const totalTxt = await page.evaluate(() => {
    const el = document.querySelector(".verdict .b");
    return el ? el.innerText : "NO-VERDICT";
  });
  const items = await page.evaluate(() => document.querySelectorAll("table tbody tr").length);
  const yearRows = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll("table tbody tr"));
    const data = [];
    rows.forEach(r => {
      const tds = r.querySelectorAll("td");
      if (tds.length >= 3 && /^202[2-6]$/.test(tds[0].textContent.trim())) data.push(tds[0].textContent.trim() + ":" + tds[1].textContent.trim());
    });
    return data;
  });
  const xbiRow = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll("h2"));
    const h = els.find(e => e.textContent.indexOf("口径辨析") >= 0);
    if (!h) return "NO-XBI-SECTION";
    const card = h.closest(".card");
    const firstRow = card ? card.querySelector("tbody tr") : null;
    return firstRow ? firstRow.textContent.replace(/\s+/g, " ").trim().slice(0, 90) : "NO-ROW";
  });
  const corr = await page.evaluate(() => {
    const m = document.body.innerText.match(/相关系数 = ([0-9.]+)/);
    return m ? m[1] : "NO-CORR";
  });
  const links = await page.evaluate(() => document.querySelectorAll("a.lnk").length);
  console.log("h1:", h1);
  console.log("verdict:", totalTxt);
  console.log("echarts loaded:", hasEcharts);
  console.log("charts:", JSON.stringify(chartInfo, null, 1));
  console.log("table rows:", items);
  console.log("year rows:", JSON.stringify(yearRows));
  console.log("xbi first row:", xbiRow);
  console.log("corr:", corr);
  console.log("source links:", links);
  console.log("errors:", errors.length ? errors.join("\n") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });