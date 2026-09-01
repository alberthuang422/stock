# -*- coding: utf-8 -*-
"""构建「随机10只美股阻力位」HTML 报告（基于项目 skill `support-resistance-levels`）
每只股票：ECharts K线（2023至今）+ 阻力位 markLine（颜色区分是否破位）+ 阻力位表格
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
RES_DIR = os.path.join(BASE, "results", "resistance_skill")
PICKS = os.path.join(BASE, "Temp", "resistance_picks.json")
OUT = os.path.join(BASE, "reports", "resistance_10stocks_20260902.html")

NAMES = {
    "kkr": "KKR & Co.", "nrg": "NRG Energy", "acn": "Accenture", "bg": "Bunge Global",
    "xom": "Exxon Mobil", "nee": "NextEra Energy", "abt": "Abbott Labs",
    "spgi": "S&P Global", "trow": "T. Rowe Price", "tdg": "TransDigm Group",
}

with open(PICKS, encoding="utf-8") as f:
    picks = json.load(f)["tickers"]
data_js = {}
for tk in picks:
    fn = os.path.join(RES_DIR, f"{tk.lower()}.json")
    if not os.path.exists(fn):
        continue
    with open(fn, encoding="utf-8") as f:
        r = json.load(f)
    csv = os.path.join(DATA, tk.lower(), f"{tk.upper()}, 1D.csv")
    if not os.path.exists(csv):
        csv = os.path.join(DATA, tk.lower())
        for x in os.listdir(csv):
            if x.endswith(".csv") and x.startswith(tk.upper()) and "1D" in x:
                csv = os.path.join(csv, x); break
    klines = []
    with open(csv, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.strip().split(",")
            if len(p) < 6 or p[0] < "2023-01-01":
                continue
            o, c, l, h = float(p[1]), float(p[4]), float(p[2]), float(p[3])
            klines.append([p[0], o, c, l, h])
    res_above = r.get("resists_above", [])
    data_js[tk] = {
        "name": NAMES.get(tk, tk.upper()),
        "dates": [k[0] for k in klines],
        "ohlc": [[k[1], k[2], k[3], k[4]] for k in klines],
        "last_close": r["window"]["last_close"],
        "last_date": r["window"]["end"],
        "resistance": res_above,
    }
    print(f"{tk}: kline {len(klines)} bars | res_above {len(res_above)}")

tpl = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>随机 10 只美股 · 阻力位识别报告（skill 算法 · 2 个月级）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f6f7f9;color:#1a1a1a;padding:24px 20px 60px}
  .wrap{max-width:1180px;margin:0 auto}
  h1{font-size:24px;font-weight:700;letter-spacing:.5px}
  .sub{color:#666;font-size:13px;margin:8px 0 18px}
  .method{background:#fff;border:1px solid #e4e7ec;border-left:4px solid #0072B2;border-radius:6px;padding:14px 18px;font-size:13px;line-height:1.9;color:#333;margin-bottom:20px}
  .method b{color:#0072B2}
  .method code{background:#eef0f3;padding:1px 5px;border-radius:3px;font-size:12px}
  .overview{background:#fff;border:1px solid #e4e7ec;border-radius:8px;padding:16px 18px;margin-bottom:26px}
  .overview h2{font-size:16px;margin-bottom:10px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  .overview th{background:#f0f2f5;text-align:left;padding:8px 10px;border-bottom:2px solid #d9dee6}
  .overview td{padding:8px 10px;border-bottom:1px solid #eef0f3}
  .ticker{font-weight:700;color:#0072B2}
  .up{color:#c0392b;font-weight:600}
  .down{color:#1e8449;font-weight:600}
  .card{background:#fff;border:1px solid #e4e7ec;border-radius:8px;margin-bottom:28px;overflow:hidden}
  .card-head{display:flex;align-items:baseline;gap:12px;padding:14px 18px 0}
  .card-head .tk{font-size:20px;font-weight:700;color:#111}
  .card-head .nm{font-size:14px;color:#555}
  .card-head .px{margin-left:auto;font-size:14px;color:#333}
  .card-head .px b{font-size:18px}
  .chart{width:100%;height:430px}
  .rtab{padding:0 18px 16px}
  .rtab h3{font-size:14px;color:#333;margin:4px 0 8px}
  .rtab table th{background:#f0f2f5;text-align:left;padding:7px 10px;border-bottom:2px solid #d9dee6;font-weight:600}
  .rtab table td{padding:7px 10px;border-bottom:1px solid #eef0f3}
  .broken-warn{color:#cc3300;font-size:11px;margin-left:4px}
  .foot{color:#888;font-size:12px;margin-top:8px;line-height:1.8}
</style>
</head>
<body>
<div class="wrap">
  <h1>随机 10 只美股 · 阻力位识别报告</h1>
  <div class="sub">基于项目 skill <code>support-resistance-levels</code> &nbsp;|&nbsp; 数据区间 2023-01-01 至今（日线）&nbsp;|&nbsp; 抽样：seed=20260902，从项目股票池 145 只纯股票中随机抽 10 只 &nbsp;|&nbsp; 生成时间 2026-09-02</div>

  <div class="method">
    <b>方法说明（来自项目 skill <code>support-resistance-levels</code>，swing 窗口扩到 40 根 K 线 ≈ 2 个月）：</b><br>
    ① <b>Swing 分形</b>：左右各 40 个交易日的局部极值点（≈2 个月级别高点） → ② <b>水平聚类</b>：容差 = 0.75 × ATR14 中位（近 60 日，ATR 归一化）→ ③ <b>评分</b>：score = 触击次数^1.2 × |触击后 5 日反应中位| × min(1, 存活天数/200) × 100 → ④ <b>破位检测</b>：近 10 日收盘穿透带边界即标"已突破"。<br>
    本报告仅列出现价上方 ≥2% 的阻力位，按价位由近及远排序；触击次数 = 该价格 ±tol 范围内被识别为 swing high 的次数；反应中位 = 触击后 5 日内最低回落幅度（绝对值越大说明压制越强）。数据源：项目本地 Yahoo 日线缓存。
  </div>

  <div class="overview">
    <h2>一览：现价与最近上方阻力位</h2>
    <table>
      <tr><th>代码</th><th>公司</th><th>现价</th><th>最近阻力位</th><th>距现价</th><th>阻力位数量</th></tr>
      __OVERVIEW_ROWS__
    </table>
  </div>

  __CARDS__

  <div class="foot">
    说明：阻力位为技术性参考位，不代表价格必然在此受阻。橙色虚线 = 当前有效阻力位；灰色虚线 = 近 10 日已突破的阻力位（标记"已突破"）。本报告仅作数据展示，不构成投资建议。
  </div>
</div>

<script>
const DATA = __DATA_JS__;

Object.keys(DATA).forEach(function (tk) {
  const d = DATA[tk];
  const el = document.getElementById('chart-' + tk);
  if (!el) return;
  const lastClose = d.last_close;
  const markLines = d.resistance.map(function (r) {
    const broken = r.broken;
    const color = broken ? '#999' : '#E69F00';
    const dash = broken ? 'dotted' : 'dashed';
    const width = broken ? 1 : 1.5;
    return {
      yAxis: r.price,
      lineStyle: { color: color, width: width, type: dash },
      label: {
        show: true, position: 'insideEndTop',
        formatter: '$' + r.price.toLocaleString() + '  (' + r.touches + 'x)' + (broken ? ' 已突破' : ''),
        color: broken ? '#777' : '#8a5a00', fontSize: 11,
        backgroundColor: broken ? '#f5f5f5' : '#fdf3e0', padding: [2, 4], borderRadius: 3
      },
      tooltip: { formatter: '阻力位 $' + r.price.toLocaleString() + ' | 触击 ' + r.touches + ' 次 | 反应 ' + r.react_med_pct + '% | 存活 ' + r.days_live + ' 天 | 评分 ' + r.score + (broken ? ' | ⚠已突破' : '') }
    };
  });
  markLines.push({
    yAxis: lastClose,
    lineStyle: { color: '#555', width: 1, type: 'solid' },
    label: { show: true, position: 'insideEndTop', formatter: '$' + lastClose.toLocaleString(), color: '#333', fontSize: 11, backgroundColor: '#eee', padding: [2, 4], borderRadius: 3 }
  });
  const chart = echarts.init(el);
  chart.setOption({
    animation: false,
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, backgroundColor: '#fff', borderColor: '#ddd', textStyle: { color: '#333', fontSize: 12 } },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    legend: { data: ['日K'], top: 6, textStyle: { color: '#555' } },
    grid: { left: 70, right: 30, top: 36, height: 360 },
    xAxis: { type: 'category', data: d.dates, boundaryGap: true, axisLine: { lineStyle: { color: '#999' } }, axisLabel: { color: '#666' } },
    yAxis: { scale: true, position: 'left', axisLabel: { color: '#666', formatter: function (v) { return '$' + v; } }, splitLine: { lineStyle: { color: '#eee' } } },
    dataZoom: [
      { type: 'inside', start: 55, end: 100 },
      { type: 'slider', start: 55, end: 100, bottom: 8, height: 18, borderColor: '#ccc', textStyle: { color: '#888' } }
    ],
    series: [{
      name: '日K', type: 'candlestick', data: d.ohlc,
      itemStyle: { color: '#c0392b', color0: '#1e8449', borderColor: '#c0392b', borderColor0: '#1e8449' },
      markLine: { silent: true, symbol: 'none', data: markLines }
    }]
  });
  window.addEventListener('resize', function () { chart.resize(); });
});
</script>
</body>
</html>
"""

ov_rows = []
for tk in picks:
    r = data_js.get(tk)
    if not r: continue
    res = r["resistance"]
    if res:
        nearest = res[0]
        pct = nearest["price"] / r["last_close"] * 100 - 100
        pct_cell = f'<span class="up">+{pct:.1f}%</span>'
        px = f"${nearest['price']:,.2f}"
    else:
        pct_cell = '<span class="down">— 历史新高区</span>'
        px = "—"
    ov_rows.append(
        f'<tr><td class="ticker">{tk.upper()}</td><td>{NAMES.get(tk, tk.upper())}</td>'
        f'<td>${r["last_close"]:,.2f}</td><td>{px}</td><td>{pct_cell}</td>'
        f'<td>{len(res)} 个</td></tr>'
    )

cards = []
for tk in picks:
    r = data_js.get(tk)
    if not r: continue
    res = r["resistance"]
    if res:
        rows = ""
        for s in res:
            pct = s["price"] / r["last_close"] * 100 - 100
            flag = '<span class="broken-warn">⚠已突破</span>' if s.get("broken") else ""
            rows += (
                f'<tr><td>#{s["rank"]}</td><td><b>${s["price"]:,.2f}</b></td>'
                f'<td>${s["band_lo"]:,.2f} ~ ${s["band_hi"]:,.2f}</td>'
                f'<td class="up">+{pct:.1f}%</td><td>{s["touches"]}</td>'
                f'<td>{s["react_med_pct"]:+.2f}%</td><td>{s["first_touch"]}</td>'
                f'<td>{s["last_touch"]}</td><td>{s["days_live"]}</td>'
                f'<td>{s["score"]}{flag}</td></tr>'
            )
        table_html = (
            '<div class="rtab"><h3>阻力位明细（按价位由近及远）</h3><table>'
            '<tr><th>排名</th><th>价位</th><th>容差带</th><th>距现价</th><th>触击</th><th>反应中位</th><th>首次触达</th><th>最近触达</th><th>存活天数</th><th>评分</th></tr>'
            + rows + '</table></div>'
        )
    else:
        table_html = ('<div class="rtab"><h3>阻力位明细</h3><p style="color:#666;font-size:13px;">'
                      '现价上方 ≥2% 范围内无有效阻力位（处于历史新高区域）。</p></div>')
    px = f'<b>${r["last_close"]:,.2f}</b>'
    cards.append(
        f'<div class="card">'
        f'<div class="card-head"><span class="tk">{tk.upper()}</span><span class="nm">{r["name"]}</span>'
        f'<span class="px">现价 {px} <span style="color:#888;font-size:12px;">({r["last_date"]})</span></span></div>'
        f'<div class="chart" id="chart-{tk}"></div>'
        + table_html + '</div>'
    )

html = tpl.replace("__OVERVIEW_ROWS__", "\n      ".join(ov_rows)) \
          .replace("__CARDS__", "\n\n  ".join(cards)) \
          .replace("__DATA_JS__", json.dumps(data_js, ensure_ascii=False))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("saved ->", OUT, "size=", len(html))
