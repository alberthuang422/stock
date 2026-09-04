// PSD 主要出口国期末库存百分位分析
const fs = require('fs');
const path = require('path');
const DIR = path.join(__dirname, 'psd');
const ATTR = { ending: 176 };

const COM = [
  ['wheat', '小麦'],
  ['corn', '玉米'],
  ['soybean', '大豆'],
];
const CC = [
  ['US', '美国'], ['CA', '加拿大'], ['E4', '欧盟'], ['AS', '澳大利亚'],
  ['BR', '巴西'], ['AR', '阿根廷'], ['RS', '俄罗斯'], ['UP', '乌克兰'], ['CH', '中国'],
];
const SUM6 = { US: 1, CA: 1, E4: 1, AS: 1, BR: 1, AR: 1 };
const SUM5 = { US: 1, CA: 1, E4: 1, AS: 1, BR: 1 };

function load(com, y) {
  return JSON.parse(fs.readFileSync(path.join(DIR, `${com}_${y}.json`), 'utf8'));
}

// 数据表: series[com][year][cc] = kMT
const val = {};
for (const [com] of COM) {
  val[com] = {};
  for (let y = 2000; y <= 2026; y++) {
    const rows = load(com, y);
    const m = {};
    for (const r of rows) if (r.attributeId === ATTR.ending) m[r.countryCode] = r.value;
    val[com][y] = m;
  }
}

const rows = [];
const lines = [];
function addLine(s) { lines.push(s); }
const C = { wheat: '小麦', corn: '玉米', soybean: '大豆' };

for (const [com, comCn] of COM) {
  addLine('==== ' + comCn + '（' + com + '） ====');
  const specs = [];
  for (const [cc, ccCn] of CC) specs.push({ key: cc, label: ccCn, get: y => val[com][y][cc] });
  specs.push({ key: 'SUM5', label: '主出口5国(美加欧澳巴)', get: y => { let s = 0; for (const c in SUM5) s += val[com][y][c] || 0; return s; } });
  specs.push({ key: 'SUM6', label: '主出口6国(+阿根廷)', get: y => { let s = 0; for (const c in SUM6) s += val[com][y][c] || 0; return s; } });

  for (const sp of specs) {
    const hist = []; // 2001..2025
    for (let y = 2001; y <= 2025; y++) {
      const v = sp.get(y);
      if (v != null && v > 0) hist.push({ y, v });
    }
    const cur = sp.get(2026);
    if (cur == null || hist.length < 10) { addLine(`  ${sp.label}: 2026/27 缺失或历史不足`); continue; }
    const hs = hist.map(h => h.v).sort((a, b) => a - b);
    const below = hs.filter(h => h < cur).length;
    const pct = (below / hist.length * 100);
    const mean10 = hs.slice(-10).reduce((a, b) => a + b, 0) / 10;
    const mean5 = hs.slice(-5).reduce((a, b) => a + b, 0) / 5;
    const diff10 = (cur - mean10) / mean10 * 100;
    const diff5 = (cur - mean5) / mean5 * 100;
    const mn = hist.reduce((a, h) => (h.v < a.v ? h : a));
    const mx = hist.reduce((a, h) => (h.v > a.v ? h : a));
    const yr = [];
    for (let y = 2021; y <= 2026; y++) yr.push(`${y}/${(y + 1) % 100}:${Math.round(sp.get(y) / 1000)}`);
    addLine(`  ${sp.label} | 2026/27=${(cur / 1000).toFixed(1)}Mt | 2001-25百分位=${pct.toFixed(0)}% | 10年均值偏离=${diff10 >= 0 ? '+' : ''}${diff10.toFixed(1)}% | 5年均值偏离=${diff5 >= 0 ? '+' : ''}${diff5.toFixed(1)}% | 区间 ${(mn.v / 1000).toFixed(0)}-${(mx.v / 1000).toFixed(0)}Mt(${mn.y}/${mx.y}) | 近6年: ${yr.join(' ')}`);
    rows.push({
      crop: comCn, series: sp.label, curMt: +(cur / 1000).toFixed(1), pct2001_25: +pct.toFixed(0),
      mean10Mt: +(mean10 / 1000).toFixed(1), diff10pct: +diff10.toFixed(1),
      mean5Mt: +(mean5 / 1000).toFixed(1), diff5pct: +diff5.toFixed(1),
      minMt: +(mn.v / 1000).toFixed(1), minY: mn.y, maxMt: +(mx.v / 1000).toFixed(1), maxY: mx.y,
    });
  }
}

// CSV 落盘
const csv = ['crop,series,cur2026Mt,pctile2001_25,mean10Mt,diff10pct,mean5Mt,diff5pct,minMt,minYear,maxMt,maxYear'];
for (const r of rows) csv.push([r.crop, r.series, r.curMt, r.pct2001_25, r.mean10Mt, r.diff10pct, r.mean5Mt, r.diff5pct, r.minMt, r.minY, r.maxMt, r.maxY].join(','));
const out = path.join(__dirname, '..', 'results', '68_psd_exporter_stocks_pct_20260903.csv');
fs.writeFileSync(out, '\ufeff' + csv.join('\n'), 'utf8');
console.log(lines.join('\n'));
console.log('\nCSV ->', out);
