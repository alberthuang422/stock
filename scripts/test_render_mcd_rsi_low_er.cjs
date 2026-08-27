const { chromium } = require("playwright-core");
const path = require("path");
(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1700 } });
  const logs = [];
  page.on("pageerror", e => logs.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") logs.push("CONSOLE: " + m.text()); });
  const file = "file:///" + path.resolve(__dirname, "../reports/48_MCD_RSI低位窗口质量/index.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(5000);
  const info = await page.evaluate(() => {
    // 找标题为"四、"的卡片
    const cards = [...document.querySelectorAll(".card")];
    const sec4 = cards.find(c => c.textContent.includes("四、最近 5 次独立信号"));
    const tbl = sec4 ? sec4.querySelector("table") : null;
    const rows = tbl ? [...tbl.querySelectorAll("tbody tr")] : [];
    const firstRowCells = rows.length ? [...rows[0].querySelectorAll("td")].map(td => td.textContent.trim()) : [];
    const headerCols = tbl ? [...tbl.querySelectorAll("thead tr:last-child th")].map(th => th.textContent.trim()) : [];
    return {
      found: !!tbl,
      rowCount: rows.length,
      firstRowCells,
      headerCols,
      firstRowTdCount: firstRowCells.length
    };
  });
  console.log("sec4 found:", info.found, "| rows:", info.rowCount, "| td count:", info.firstRowTdCount);
  console.log("header sub-cols:", JSON.stringify(info.headerCols));
  console.log("first row cells:", JSON.stringify(info.firstRowCells));
  console.log("JS errors:", logs.length ? logs.slice(0, 10) : "NONE");
  await browser.close();
})();