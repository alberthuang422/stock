// A/WAT/DHR/TMO × IBB/XBI 相关性报告 SSR 渲染测试
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const CHROME = 'C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe';
const htmlPath = path.join(__dirname, '..', 'reports', '24_工具龙头_ibb_xbi相关性', 'index.html');

async function main() {
  const html = fs.readFileSync(htmlPath, 'utf-8');
  let errors = [];
  const checks = {};

  checks['HTML大小(KB)'] = Math.round(html.length / 1024);
  const needTxt = ['核心结论', '相关性矩阵热力图', '分阶段相关性全览', '0.395', '0.284', '0.411', '0.320',
                   '0.415', '0.289', '0.450', '0.346', '不显著', 'Fisher', 'DHR', 'WAT 沃特世',
                   '安捷伦', '赛默飞'];
  for (const t of needTxt) {
    if (!html.includes(t)) errors.push('缺少关键文本: ' + t);
  }
  if (html.includes('__DATA_JSON__')) errors.push('存在未替换的 DATA 占位符');

  const browser = await chromium.launch({
    executablePath: CHROME, headless: true, args: ['--no-sandbox', '--disable-gpu'],
  });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });
  await page.goto('file://' + htmlPath.replace(/\\/g, '/'), { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(2500);

  const chartInfo = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[id^="chart_"]'));
    const out = {};
    for (const el of els) out[el.id] = el.querySelector('canvas') ? 'canvas-ok' : 'NO-CANVAS';
    return out;
  });
  checks['chart'] = chartInfo;
  if (Object.keys(chartInfo).length < 2) errors.push('图表数量不足 2');
  for (const [id, v] of Object.entries(chartInfo)) if (v !== 'canvas-ok') errors.push('图表无 canvas: ' + id);

  await browser.close();
  console.log('checks:', JSON.stringify(checks, null, 1));
  if (errors.length) {
    console.error('FAILED:\n- ' + errors.join('\n- '));
    process.exit(1);
  }
  console.log('PASS: 渲染测试通过（' + Object.keys(chartInfo).length + ' 图表 canvas-ok，无 JS 错误）');
}

main().catch(e => { console.error(e); process.exit(1); });