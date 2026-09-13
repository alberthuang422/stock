// 85 号报告渲染校验（三品种 tab + 逐事件上下双窗图）
const { chromium } = require("playwright-core");
const path = require("path");

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FILE = path.resolve(__dirname, "../reports/85_月差背离三品种对比/index.html");

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--no-sandbox", "--disable-gpu"] });
  const page = await browser.newPage({ viewport: { width: 1400, height: 2400 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });

  await page.goto("file://" + FILE, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(4500);

  const info = await page.evaluate(() => {
    const out = {};
    // 对比图
    const cmp = document.getElementById('c_cmp');
    out.cmpCanvas = cmp && cmp.querySelector('canvas') ? 'ok' : 'NO-CANVAS';
    if (cmp) {
      try {
        const o = window.echarts.getInstanceByDom(cmp).getOption();
        out.cmpSeries = o.series.length;
      } catch(e){ out.cmpSeries = 'ERR:'+e.message; }
    }
    // 逐事件图（当前 CL tab）
    const grid = document.getElementById('c_events');
    out.nBox = grid ? grid.children.length : 0;
    const canvasOk = [];
    for (let i=0;i<Math.min(out.nBox,4);i++){
      const el = document.getElementById('ev_CL_'+i);
      canvasOk.push(el && el.querySelector('canvas') ? 'ok':'NO');
    }
    out.canvasOk = canvasOk;
    out.totalCanvas = grid ? grid.querySelectorAll('canvas').length : 0;
    // 抽验第1图
    let sample=null;
    if (out.nBox>0){
      try{
        const o = window.echarts.getInstanceByDom(document.getElementById('ev_CL_0')).getOption();
        sample = { gridCount:o.grid.length, seriesCount:o.series.length, votePts:o.series[1].data.length, markline:[o.series[0].markLine?'Y':'N', o.series[2].markLine?'Y':'N'] };
      }catch(e){ sample='ERR:'+e.message; }
    }
    out.sample = sample;
    // 切到 HO tab
    const hoTab = document.querySelector('.tab[data-p="HO"]');
    if (hoTab) hoTab.click();
    return out;
  });

  await page.waitForTimeout(3500);
  const hoInfo = await page.evaluate(() => {
    const grid = document.getElementById('c_events');
    const n = grid ? grid.children.length : 0;
    let c=0, first=null;
    if(n>0){
      const el = document.getElementById('ev_HO_0');
      c = el && el.querySelector('canvas') ? 1 : 0;
      try{ const o=window.echarts.getInstanceByDom(el).getOption(); first={grid:o.grid.length,series:o.series.length}; }catch(e){ first='ERR:'+e.message; }
    }
    return { nHO:n, canvas0:c, first };
  });

  console.log("=== CL tab ===");
  console.log("对比图canvas:", info.cmpCanvas, "| series:", info.cmpSeries);
  console.log("事件图数量:", info.nBox, "| 前4图:", JSON.stringify(info.canvasOk), "| 总canvas:", info.totalCanvas);
  console.log("样例(CL第1图):", JSON.stringify(info.sample));
  console.log("=== HO tab ===");
  console.log("HO事件图数量:", hoInfo.nHO, "| canvas0:", hoInfo.canvas0, "| 首图:", JSON.stringify(hoInfo.first));
  console.log("errors:", errors.length ? errors.join(" | ") : "none");
  await browser.close();
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });
