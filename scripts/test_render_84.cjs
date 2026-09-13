// 84 号报告渲染校验（逐事件小图·上下分窗版）
const { chromium } = require("playwright-core");
const path = require("path");

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FILE = path.resolve(__dirname, "../reports/84_CL月差背离事件回测/index.html");

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--no-sandbox", "--disable-gpu"] });
  const page = await browser.newPage({ viewport: { width: 1360, height: 2000 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  await page.goto("file://" + FILE, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(5000);

  const info = await page.evaluate(() => {
    const grid = document.getElementById("c_events");
    const nBox = grid ? grid.children.length : 0;
    // canvas 抽验：前 3 个 + 总数统计
    const canvasOk = [];
    for (let i = 0; i < Math.min(nBox, 5); i++) {
      const el = document.getElementById("c_e_" + i);
      canvasOk.push(el && el.querySelector("canvas") ? "ok" : "NO-CANVAS");
    }
    const totalCanvas = grid ? grid.querySelectorAll("canvas").length : 0;
    // 抽第一个图的 series 与 grid 数
    let sample = null;
    if (nBox > 0) {
      try {
        const o = window.echarts.getInstanceByDom(document.getElementById("c_e_0")).getOption();
        sample = { title: o.title[0].text, gridCount: o.grid.length, seriesCount: o.series.length,
                   votePts: o.series[1].data.length, marklineOnSeries: [o.series[0].markLine ? 'Y' : 'N', o.series[2].markLine ? 'Y' : 'N'] };
      } catch (e) { sample = "ERR:" + e.message; }
    }
    const pair = document.getElementById("c_pair") ? "ok" : "MISSING";
    return { nBox, canvasOk, totalCanvas, sample, pair };
  });

  console.log("事件图数量:", info.nBox);
  console.log("前5图canvas:", JSON.stringify(info.canvasOk));
  console.log("总canvas数:", info.totalCanvas);
  console.log("样例(第1图):", JSON.stringify(info.sample));
  console.log("pair:", info.pair);
  console.log("errors:", errors.length ? errors.join(" | ") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });