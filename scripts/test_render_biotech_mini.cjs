// 小型 biotech 景气度报告 SSR 渲染测试
// 用法: NODE_PATH=<workspace node_modules> node scripts/test_render_biotech_mini.cjs
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const CHROME = 'C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe';
const htmlPath = path.join(__dirname, '..', 'reports', '22_小型生物科技景气度', 'index.html');

async function main() {
  const html = fs.readFileSync(htmlPath, 'utf-8');
  let errors = [];
  const checks = {};

  // 静态校验
  checks['链接数'] = (html.match(/class="lnk"/g) || []).length;
  if (checks['链接数'] < 100) errors.push('来源链接数不足 100: ' + checks['链接数']);
  for (const y of [2022, 2023, 2024, 2025]) {
    if (!html.includes(String(y) + ' 年核查明细')) errors.push('缺少年份明细卡片 ' + y);
  }
  if (!html.includes('◎ 融资与资本面')) errors.push('缺少 2026 当前核查板块卡片');
  const needTxt = ['融资与资本面', '并购与退出通道', '临床与研发', '宏观利率与政策', '强景气', '低迷期', '0.494', '双口径对照', '加权敏感性', '平权总分', '加权总分', '敏感性扫描'];
  for (const t of needTxt) {
    if (!html.includes(t)) errors.push('缺少关键文本: ' + t);
  }

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
  if (Object.keys(chartInfo).length < 4) errors.push('图表数量不足 4');
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