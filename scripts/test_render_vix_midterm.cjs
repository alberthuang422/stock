// 无头 Chrome 渲染验证脚本（SSR 验证 echarts canvas 渲染）
const { chromium } = require('playwright-core');

const target = process.argv[2] || 'reports/42_VIX中期选举抬升/index.html';

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe',
    args: ['--no-sandbox', '--headless=new'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));

  const abs = 'file:///' + process.cwd().replace(/\\/g, '/') + '/' + target;
  await page.goto(abs, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(5000);

  const result = await page.evaluate(() => {
    const out = {};
    document.querySelectorAll('[id^=bt-custom-]').forEach((el) => {
      const canvas = el.querySelector('canvas');
      if (!canvas) { out[el.id] = 'NO_CANVAS'; return; }
      let nonblank = null;
      try {
        const ctx = canvas.getContext('2d');
        let blank = true;
        for (let y = 0; y < canvas.height && blank; y += 8) {
          const data = ctx.getImageData(0, y, canvas.width, 8).data;
          for (let i = 3; i < data.length; i += 4) { if (data[i] > 0) { blank = false; break; } }
        }
        nonblank = !blank;
      } catch (e) { nonblank = 'ERR:' + e.message; }
      out[el.id] = { w: canvas.width, h: canvas.height, nonblank };
    });
    return out;
  });
  console.log('file=', target);
  console.log(JSON.stringify(result, null, 2));
  console.log('errors=', JSON.stringify(errors, null, 2));
  await browser.close();
})();