// SSR 渲染测试：options-strategy.html — 验证日历价差曲线修复（最近到期日基准估值）
const { chromium } = require("playwright-core");
const path = require("path");

(async () => {
  const exe = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe";
  const browser = await chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1700 } });
  const errors = [];
  page.on("pageerror", e => errors.push("PAGEERROR: " + e.message));
  page.on("console", m => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });
  page.on("dialog", d => d.accept()); // 接受"清空后载入模板"确认框

  const file = "file:///" + path.resolve(__dirname, "../options-strategy.html").replace(/\\/g, "/");
  await page.goto(file, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);

  // 1) 点击「日历价差」预设
  await page.click('.chip[data-id="calendar"]');
  await page.waitForTimeout(800);

  // 2) 采集页面状态：图例/指标卡口径、明细表、曲线数值
  const info = await page.evaluate(() => {
    const chart = window.chart;
    const opt = chart ? chart.getOption() : null;
    let legendNames = [], seriesData = {};
    if (opt) {
      legendNames = (opt.legend && opt.legend[0] && opt.legend[0].data) || [];
      (opt.series || []).forEach(s => {
        const d = s.data.filter(p => Array.isArray(p));
        seriesData[s.name] = seriesData[s.name] || [];
        seriesData[s.name].push({ n: d.length, first: d[0], last: d[d.length - 1] });
      });
    }
    const canvases = [...document.querySelectorAll("#chart canvas")];
    return {
      legendNames,
      seriesData,
      canvasCount: canvases.length,
      zeroSizeCanvas: canvases.filter(c => c.width === 0 || c.height === 0).length,
      maxExpLabel: document.getElementById("mMaxExpLabel").textContent,
      minExpLabel: document.getElementById("mMinExpLabel").textContent,
      maxExpNote: document.getElementById("mMaxExpNote").textContent,
      maxExpVal: document.getElementById("mMaxExp").textContent,
      minExpVal: document.getElementById("mMinExp").textContent,
      chartTag: document.getElementById("chartTag").textContent,
      legCount: document.getElementById("legCount").textContent,
      sliderMax: document.getElementById("dateSlider").max,
      sliderDate: document.getElementById("sliderDate").textContent
    };
  });
  console.log("图例:", JSON.stringify(info.legendNames));
  console.log("series:", JSON.stringify(info.seriesData));
  console.log("canvas:", info.canvasCount, "| zeroSize:", info.zeroSizeCanvas);
  console.log("指标卡:", info.maxExpLabel, info.maxExpVal, "|", info.minExpLabel, info.minExpVal, "|", info.maxExpNote);
  console.log("chartTag:", info.chartTag);
  console.log("持仓:", info.legCount, "| 滑块max:", info.sliderMax, "| 滑块日期:", info.sliderDate);

  // 3) 拖动滑块到最近到期日（30天），验证曲线联动无报错
  await page.evaluate(() => {
    const sl = document.getElementById("dateSlider");
    sl.value = 30;
    sl.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await page.waitForTimeout(800);
  const afterSlide = await page.evaluate(() => ({
    sliderDate: document.getElementById("sliderDate").textContent,
    maxCurVal: document.getElementById("mMaxCur").textContent,
    minCurVal: document.getElementById("mMinCur").textContent
  }));
  console.log("滑块30天后:", JSON.stringify(afterSlide));

  console.log("JS errors:", errors.length ? errors.slice(0, 8) : "NONE");
  await page.screenshot({ path: path.resolve(__dirname, "../results/options_calendar_today.png") });

  // 4) 单到期日回归：载入「牛市看涨价差」，确认口径回落为「到期日盈亏」
  await page.click('.chip[data-id="bull-call"]');
  await page.waitForTimeout(800);
  const single = await page.evaluate(() => ({
    legend: (window.chart.getOption().legend[0].data),
    maxExpLabel: document.getElementById("mMaxExpLabel").textContent,
    maxExpNote: document.getElementById("mMaxExpNote").textContent
  }));
  console.log("单到期日回归:", JSON.stringify(single));
  console.log("JS errors:", errors.length ? errors.slice(0, 8) : "NONE");
  await page.screenshot({ path: path.resolve(__dirname, "../results/options_bullcall_single.png") });

  await browser.close();
})();
