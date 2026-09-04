// PSD 主要出口国期末库存——分段历史比较（2001-2014 / 2015-2020 / 2021-2025 vs 2026/27）
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
const RUUA = { RS: 1, UP: 1 };

function load(com, y) {
  return JSON.parse(fs.readFileSync(path.join(DIR, `${com}_${y}.json`), 'utf8'));
}

// val[com][year][cc] = kMT
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

// 分段定义（市场年度，marketYear；含端点）
const SEG = [
  { key: 'S1', label: '2001-2014', ys: 2001, ye: 2014 },
  { key: 'S2', label: '2015-2020', ys: 2015, ye: 2020 },
  { key: 'S3', label: '2021-2025', ys: 2021, ye: 2025 },
];

function stats(arr) {
  const n = arr.length;
  const mean = arr.reduce((a, b) => a + b, 0) / n;
  const mn = Math.min(...arr), mx = Math.max(...arr);
  return { n, mean, mn, mx };
}
// 段内分位：段内严格低于当前值的年份占比
function pctWithin(arr, cur) {
  const below = arr.filter(v => v < cur).length;
  return below / arr.length * 100;
}

const outRows = [];
const lines = [];

for (const [com, comCn] of COM) {
  lines.push('==== ' + comCn + '（' + com + '） ====');
  const specs = [];
  for (const [cc, ccCn] of CC) specs.push({ key: cc, label: ccCn, get: y => val[com][y][cc] });
  specs.push({ key: 'SUM5', label: '主出口5国(美加欧澳巴)', get: y => { let s = 0; for (const c in SUM5) s += val[com][y][c] || 0; return s; } });
  specs.push({ key: 'SUM6', label: '主出口6国(+阿根廷)', get: y => { let s = 0; for (const c in SUM6) s += val[com][y][c] || 0; return s; } });
  specs.push({ key: 'RUUA', label: '俄+乌合计', get: y => { let s = 0; for (const c in RUUA) s += val[com][y][c] || 0; return s; } });

  for (const sp of specs) {
    const cur = sp.get(2026);
    if (cur == null || cur <= 0) { continue; }
    const segs = {};
    let ok = true;
    for (const sg of SEG) {
      const arr = [];
      for (let y = sg.ys; y <= sg.ye; y++) {
        const v = sp.get(y);
        if (v != null && v > 0) arr.push(v);
      }
      if (arr.length < 4) { ok = false; break; } // 段内数据不足（如澳大利亚大豆）
      segs[sg.key] = { arr, ...stats(arr) };
    }
    if (!ok) { lines.push(`  ${sp.label}: 段内数据不足，跳过`); continue; }

    const dev = k => (cur - segs[k].mean) / segs[k].mean * 100;
    const d2 = dev('S2'), d3 = dev('S3'), d1 = dev('S1');
    const p1 = pctWithin(segs.S1.arr, cur), p2 = pctWithin(segs.S2.arr, cur), p3 = pctWithin(segs.S3.arr, cur);

    const f = (x, d = 1) => (x / 1000).toFixed(d);
    const segStr = k => `${f(segs[k].mean)}(区间${f(segs[k].mn, 0)}~${f(segs[k].mx, 0)})`;
    lines.push(`  ${sp.label} | 2026/27=${f(cur)}Mt`);
    lines.push(`    S1(2001-14): 均值${segStr('S1')} | vs=${d1 >= 0 ? '+' : ''}${d1.toFixed(0)}% | 段内分位${p1.toFixed(0)}%`);
    lines.push(`    S2(2015-20): 均值${segStr('S2')} | vs=${d2 >= 0 ? '+' : ''}${d2.toFixed(0)}% | 段内分位${p2.toFixed(0)}%`);
    lines.push(`    S3(2021-25): 均值${segStr('S3')} | vs=${d3 >= 0 ? '+' : ''}${d3.toFixed(0)}% | 段内分位${p3.toFixed(0)}%`);

    outRows.push({
      crop: comCn, series: sp.label, curMt: +f(cur),
      s1_mean: +f(segs.S1.mean), s1_min: +f(segs.S1.mn, 1), s1_max: +f(segs.S1.mx, 1), s1_pct: +p1.toFixed(0),
      s2_mean: +f(segs.S2.mean), s2_min: +f(segs.S2.mn, 1), s2_max: +f(segs.S2.mx, 1), s2_pct: +p2.toFixed(0),
      s3_mean: +f(segs.S3.mean), s3_min: +f(segs.S3.mn, 1), s3_max: +f(segs.S3.mx, 1), s3_pct: +p3.toFixed(0),
      dev_s1: +d1.toFixed(1), dev_s2: +d2.toFixed(1), dev_s3: +d3.toFixed(1),
    });
  }
  // 打印 SUM5 年度序列（供图表）
  const yr = [];
  for (let y = 2001; y <= 2026; y++) {
    let s = 0; for (const c in SUM5) s += val[com][y][c] || 0;
    yr.push(+(s / 1000).toFixed(1));
  }
  lines.push('  SUM5年度序列 2001-2026 (Mt): ' + yr.join(','));
  lines.push('');
}

// CSV
const header = 'crop,series,cur2026Mt,s1_meanMt,s1_minMt,s1_maxMt,s1_pctile,s2_meanMt,s2_minMt,s2_maxMt,s2_pctile,s3_meanMt,s3_minMt,s3_maxMt,s3_pctile,dev_vs_s1_pct,dev_vs_s2_pct,dev_vs_s3_pct';
const csv = [header];
for (const r of outRows) csv.push([r.crop, r.series, r.curMt, r.s1_mean, r.s1_min, r.s1_max, r.s1_pct, r.s2_mean, r.s2_min, r.s2_max, r.s2_pct, r.s3_mean, r.s3_min, r.s3_max, r.s3_pct, r.dev_s1, r.dev_s2, r.dev_s3].join(','));
const out = path.join(__dirname, '..', 'results', '68_psd_exporter_stocks_segments_20260903.csv');
fs.writeFileSync(out, '\ufeff' + csv.join('\n'), 'utf8');
console.log(lines.join('\n'));
console.log('\nCSV ->', out);
