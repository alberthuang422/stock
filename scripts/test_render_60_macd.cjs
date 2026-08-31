// 60 号报告无头渲染验证（echarts 散点图）
const { chromium } = require('playwright-core');

const target = process.argv[2] || 'reports/60_MACD死叉_4hRSI超卖_胜率回测/index.html';

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe',
    args: ['--no-sandbox', '--headless=new'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 1600 } });
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));

  const abs = 'file:///' + process.cwd().replace(/\\/g, '/') + '/' + target;
  await page.goto(abs, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(6000);

  const result = await page.evaluate(() => {
    const out = { canvases: {}, termCount: 0, tables: 0 };
    document.querySelectorAll('canvas').forEach((canvas, idx) => {
      let nonblank = null;
      try {
        const ctx = canvas.getContext('2d');
        let blank = true;
        for (let y = 0; y < canvas.height && blank; y += 6) {
          const data = ctx.getImageData(0, y, canvas.width, 6).data;
          for (let i = 3; i < data.length; i += 4) { if (data[i] > 0) { blank = false; break; } }
        }
        nonblank = !blank;
      } catch (e) { nonblank = 'ERR:' + e.message; }
      out.canvases[idx] = { w: canvas.width, h: canvas.height, nonblank, cls: canvas.parentElement?.id || '' };
    });
    out.termCount = document.querySelectorAll('.term').length;
    out.tables = document.querySelectorAll('table').length;
    out.title = document.title;
    out.tipPresent = !!document.getElementById('termtip');
    return out;
  });
  console.log('file=', target);
  console.log(JSON.stringify(result, null, 2));
  console.log('errors=', JSON.stringify(errors, null, 2));
  await browser.close();
})();