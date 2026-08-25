// KO×科技/制药/医疗保健 相关性报告 SSR 渲染测试（仅验证，不交付截图）
// 用法: NODE_PATH=<workspace node_modules> node scripts/test_render_ko_sector.cjs
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const CHROME = 'C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe';
const htmlPath = path.join(__dirname, '..', 'reports', '32_ko_科技医药相关性', 'index.html');

async function main() {
  const html = fs.readFileSync(htmlPath, 'utf-8');
  let errors = [];
  const checks = {};

  checks['HTML大小(KB)'] = Math.round(html.length / 1024);
  const needTxt = ['KO × 科技', '制药', '医疗保健', '60 日滚动相关性', 'Fisher z', '−0.397',
                   '0.026', '0.406', '8.63', '4.67', '2026-02-01', 'XPH 代理'];
  for (const t of needTxt) {
    if (!html.includes(t)) errors.push('缺少关键文本: ' + t);
  }
  if (html.includes('__DATA_JSON__')) errors.push('存在未替换的 DATA 占位符');
  if (html.includes('__BLOCK_ROWS_')) errors.push('存在未替换的表格占位符');

  // 无头浏览器渲染
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
  if (Object.keys(chartInfo).length < 6) errors.push('图表数量不足 6');
  for (const [id, v] of Object.entries(chartInfo)) if (v !== 'canvas-ok') errors.push('图表无 canvas: ' + id);

  const hasEcharts = await page.evaluate(() => typeof window.echarts !== 'undefined');
  checks['echarts'] = hasEcharts;
  if (!hasEcharts) errors.push('echarts 未加载');

  await browser.close();
  console.log('checks:', JSON.stringify(checks, null, 1));
  if (errors.length) {
    console.error('FAILED:\n- ' + errors.join('\n- '));
    process.exit(1);
  }
  console.log('PASS: 渲染测试通过（' + Object.keys(chartInfo).length + ' 图表均 canvas-ok，无 JS 错误）');
}

main().catch(e => { console.error(e); process.exit(1); });