// 渲染验证：无头 Edge 打开报告，统计 canvas / 表格行 / console 报错
const { chromium } = require("playwright-core");
const { pathToFileURL } = require("url");
const path = require("path");

const FILE = process.argv[2];
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";

(async () => {
  const browser = await chromium.launch({ executablePath: EDGE, headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  page.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
  page.on("pageerror", e => errs.push("PAGEERROR: " + e.message));
  page.on("requestfailed", r => errs.push("REQFAIL: " + r.url().slice(0, 120) + " " + (r.failure() || {}).errorText));

  await page.goto(pathToFileURL(FILE).href, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(3500);

  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll("canvas")];
    const drawn = canvases.filter(c => c.width > 50 && c.height > 50).length;
    const tbs = [...document.querySelectorAll("tbody")].map(t => ({ id: t.id, rows: t.querySelectorAll("tr").length }));
    const charts = [...document.querySelectorAll(".chart,.chart-sm")].map(e => ({
      id: e.id, h: e.clientHeight, w: e.clientWidth
    }));
    return {
      title: document.title,
      canvasTotal: canvases.length, canvasDrawn: drawn,
      plotPixels: canvases.map(c => c.width * c.height).reduce((a, b) => a + b, 0),
      tables: tbs, charts, bodyH: document.body.scrollHeight,
      placeholders: (document.body.innerHTML.match(/__[A-Z_0-9]+__/g) || []).length,
      nan: (document.body.innerText.match(/\bNaN\b/g) || []).length,
      undefinedTxt: (document.body.innerText.match(/undefined/g) || []).length,
    };
  });
  console.log(JSON.stringify({ file: path.basename(FILE), errors: errs.slice(0, 12), errCount: errs.length, ...info }, null, 1));
  await browser.close();
})();
