# -*- coding: utf-8 -*-
"""CSCO vs PANW vs CRWD 相关性研报生成器（35_网安vs网络设备脱钩）"""
import json, os, csv

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "35_网安vs网络设备")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "csco_panw_crwd_corr.json"), encoding="utf-8") as f:
    C = json.load(f)
with open(os.path.join(BASE, "..", "results", "csco_panw_crwd_extra.json"), encoding="utf-8") as f:
    E = json.load(f)

# 滚动相关 CSV → 图表数据（聚焦区 2026-02 起）
roll_dates, cp60, cc60, pc60, cp30, cc30, pc30 = [], [], [], [], [], [], []
with open(os.path.join(BASE, "..", "results", "csco_panw_crwd_rollcorr.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        d = row["date"]
        roll_dates.append(d)
        cp60.append(None if row.get("CSCO×PANW_60") == "" else round(float(row["CSCO×PANW_60"]), 4))
        cc60.append(None if row.get("CSCO×CRWD_60") == "" else round(float(row["CSCO×CRWD_60"]), 4))
        pc60.append(None if row.get("PANW×CRWD_60") == "" else round(float(row["PANW×CRWD_60"]), 4))
        cp30.append(None if row.get("CSCO×PANW_30") == "" else round(float(row["CSCO×PANW_30"]), 4))
        cc30.append(None if row.get("CSCO×CRWD_30") == "" else round(float(row["CSCO×CRWD_30"]), 4))
        pc30.append(None if row.get("PANW×CRWD_30") == "" else round(float(row["PANW×CRWD_30"]), 4))

def js(o):
    return json.dumps(o, ensure_ascii=False)

ev = E["极端日明细"]
ev_dates = [r["date"] for r in ev]
ev_csco = [r["CSCO%"] for r in ev]
ev_panw = [r["PANW%"] for r in ev]
ev_crwd = [r["CRWD%"] for r in ev]
n_ext = len(ev)
n_same = E["极端日统计"]["CSCO与其他两家同向天数"]
n_pw = E["极端日统计"]["PANW与CRWD同向天数"]

roll_m = E["PANW×CRWD r60 逐月均值"]
rm_dates = list(roll_m.keys())
rm_vals = list(roll_m.values())

seg_data = [["2026-02~04", 0.083, 0.112, 0.793], ["2026-05~07", 0.329, 0.230, 0.867],
            ["2026-08至今", 0.240, 0.216, 0.927], ["2025-01~26-01", 0.445, 0.449, 0.716]]

# ---- JS 数据注入（占位符法）----
JS_DATA = {
    "roll_dates": roll_dates, "cp60": cp60, "cc60": cc60, "pc60": pc60, "cp30": cp30, "cc30": cc30, "pc30": pc30,
    "ev_dates": ev_dates, "ev_csco": ev_csco, "ev_panw": ev_panw, "ev_crwd": ev_crwd,
    "seg": seg_data, "rm_d": rm_dates, "rm_v": rm_vals,
}

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSCO × PANW × CRWD 相关性拆解 · 网络设备 vs 网络安全</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072b2;--orange:#e69f00;--sky:#56b4e9;--green:#009e73;--red:#d55e00;--purple:#cc79a7;--slate:#5a6a7a;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;color:var(--ink);}
  table{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0;}
  th,td{border:1px solid var(--line);padding:6px 8px;text-align:right;}
  th{background:#f0f2f5;font-weight:600;white-space:nowrap;}
  td:first-child,th:first-child{text-align:left;}
  .kpi{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0;}
  .kpi .box{flex:1;min-width:170px;border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:8px;padding:12px 14px;background:#fff;}
  .kpi .box .v{font-size:22px;font-weight:700;}
  .kpi .box .l{font-size:12px;color:var(--sub);}
  .tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;margin-left:4px;}
  .t-high{background:#e7f4ee;color:#0a7a4e;}
  .t-low{background:#fdeeea;color:#b23b1a;}
  .note{font-size:12px;color:var(--sub);margin-top:4px;}
  .chart{width:100%;height:380px;}
  .chart.sm{height:300px;}
  .legend{font-size:12px;color:var(--sub);margin-bottom:6px;}
  .callout{background:#fffbe6;border-left:4px solid #f5a623;border-radius:6px;padding:10px 14px;margin:10px 0;font-size:13px;}
  .good{background:#eef9f4;border-left:4px solid var(--green);}
  .footer{color:var(--sub);font-size:11.5px;text-align:center;margin-top:24px;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>CSCO × PANW × CRWD 相关性拆解</h1>
  <div class="meta">网络设备龙头 vs 网络安全双雄 · 窗口：2026-02至今（141 交易日）· 口径：日线对数收益 + 静态Pearson / 60日滚动(主) / 30日(辅) · 数据：Yahoo Finance adj_close · 生成 2026-08-25</div>
  <div class="kpi">
    <div class="box"><div class="v">0.84</div><div class="l">PANW×CRWD 静态r<span class="tag t-high">高度抱团</span></div></div>
    <div class="box"><div class="v">0.18–0.23</div><div class="l">CSCO×网安 静态r<span class="tag t-low">显著脱钩</span></div></div>
    <div class="box"><div class="v">↓50%</div><div class="l">CSCO×网安 相关性较2025年</div></div>
    <div class="box"><div class="v">+98%/+73%</div><div class="l">PANW/CRWD 2026-02至今累计</div></div>
  </div>
  <div class="callout good"><b>核心结论：</b>2026 年 2 月以来，<b>CSCO 与网安双雄呈结构性脱钩</b>——CSCO×PANW/CRWD 静态相关仅 0.23/0.18（2025 全年 0.45/0.45），而 <b>PANW×CRWD 高度抱团且逐月增强</b>（静态 0.84，8 月滚动 r60 达 0.89）。CSCO 的最大单日波动全部来自自身财报事件（02-12 −13.2% / 05-14 +12.6% / 08-13 −8.8%），网安板块零跟随。三者分属两条独立驱动链：<b>CSCO=企业硬件/网络周期</b>，<b>PANW/CRWD=AI 安全软件叙事</b>。</div>
</div>

<div class="card">
  <h2>一、静态相关矩阵（2026-02 至今）</h2>
  <table>
    <tr><th>配对</th><th>静态 r</th><th>样本</th><th>p 值</th><th>2025-01~2026-01 r</th><th>变化</th></tr>
    <tr><td>PANW × CRWD</td><td><b>0.8398</b></td><td>141</td><td>&lt;0.0001</td><td>0.7155</td><td>+17pp ↑</td></tr>
    <tr><td>CSCO × PANW</td><td>0.2258</td><td>141</td><td>0.0069</td><td>0.4452</td><td>−22pp ↓</td></tr>
    <tr><td>CSCO × CRWD</td><td>0.1816</td><td>141</td><td>0.0310</td><td>0.4494</td><td>−27pp ↓</td></tr>
  </table>
  <p class="note">注：CSCO×网安两对虽 p&lt;0.05，但 r 仅 0.18–0.23，解释方差 &lt;5%，经济意义≈无。对比 2025 年同期（0.45/0.45，p&lt;0.0001）显著走低。</p>
  <div class="chart" id="chart_static"></div>
</div>

<div class="card">
  <h2>二、60 日滚动相关（主口径）</h2>
  <div class="legend">2026-02 以前为滚动窗口 warmup（PANW×CRWD 半透明）；2026-02 起为分析窗口</div>
  <div class="chart" id="chart_roll"></div>
  <table>
    <tr><th>配对</th><th>窗口内均值</th><th>首值(2026-02初)</th><th>末值(08-24)</th><th>区间</th></tr>
    <tr><td>PANW × CRWD</td><td>0.8139</td><td>0.7245</td><td><b>0.8889</b></td><td>0.69–0.90</td></tr>
    <tr><td>CSCO × PANW</td><td>0.2059</td><td>0.2216</td><td>0.2311</td><td>0.01–0.33</td></tr>
    <tr><td>CSCO × CRWD</td><td>0.2017</td><td>0.3636</td><td>0.1992</td><td>0.11–0.36</td></tr>
  </table>
  <p class="note">PANW×CRWD 滚动相关自 2 月 0.72 一路抬升至 0.89，8 月未见衰减；CSCO 与网安相关在 0.1–0.3 低位震荡，无收敛迹象。</p>
</div>

<div class="card">
  <h2>三、分月段静态相关</h2>
  <div class="chart sm" id="chart_seg"></div>
  <table>
    <tr><th>分段</th><th>CSCO×PANW</th><th>CSCO×CRWD</th><th>PANW×CRWD</th></tr>
    <tr><td>2026-02~04</td><td>0.083</td><td>0.112</td><td>0.793</td></tr>
    <tr><td>2026-05~07</td><td>0.329</td><td>0.230</td><td>0.867</td></tr>
    <tr><td>2026-08至今(n=16)</td><td>0.240</td><td>0.216</td><td><b>0.927</b></td></tr>
    <tr><td>2025-01~2026-01(对照)</td><td>0.445</td><td>0.449</td><td>0.716</td></tr>
  </table>
  <p class="note">PANW×CRWD 各段均 &gt;0.79 且逐月走强（2-4月 0.79 → 5-7月 0.87 → 8月 0.93）；CSCO×网安全段 &lt;0.33。8 月段 n=16 样本过小，p 不显著，仅做趋势参考。</p>
</div>

<div class="card">
  <h2>四、PANW×CRWD 滚动相关逐月均值</h2>
  <div class="chart sm" id="chart_month"></div>
  <div class="callout"><b>读法：</b>网安双雄相关性呈<b>趋势性增强</b>（1 月 0.70 → 6 月 0.88 峰值 → 8 月 0.88），并非波动性脉冲，说明二者同属 AI 安全交易（platformization / AI 安全代理）同一叙事仓位，市场将其作为同一板块交易。</div>
</div>

<div class="card">
  <h2>五、极端日联动（|收益|≥2σ，2026-02 至今）</h2>
  <div class="legend">共 @N_EXT@ 个极端日 · CSCO 与两网安同向 @N_SAME@ 天 · PANW×CRWD 同向 @N_PW@ 天</div>
  <div class="chart" id="chart_ev"></div>
  <table>
    <tr><th>日期</th><th>CSCO</th><th>PANW</th><th>CRWD</th><th>事件归属</th></tr>
    <tr><td>2026-02-05</td><td>+1.5%</td><td>−7.4%</td><td>−9.7%</td><td>网安板块独立大跌</td></tr>
    <tr><td>2026-02-12</td><td><b>−13.2%</b></td><td>−1.5%</td><td>−1.0%</td><td><b>CSCO 财报</b>(02-11 盘后 Q2 FY26)</td></tr>
    <tr><td>2026-02-18</td><td>+1.7%</td><td>−7.1%</td><td>+0.4%</td><td>PANW 个股事件</td></tr>
    <tr><td>2026-02-20</td><td>+0.8%</td><td>−1.5%</td><td>−8.3%</td><td>CRWD 个股事件</td></tr>
    <tr><td>2026-02-23</td><td>−1.9%</td><td>−3.1%</td><td>−10.4%</td><td>网安重挫</td></tr>
    <tr><td>2026-04-09/10</td><td>−0.6%/−1.2%</td><td>−4.0%/−7.0%</td><td>−7.8%/−4.1%</td><td>网安双挫（宏观）</td></tr>
    <tr><td>2026-05-07</td><td>+0.6%</td><td>+6.8%</td><td>+7.7%</td><td>网安共振</td></tr>
    <tr><td>2026-05-14</td><td><b>+12.6%</b></td><td>+4.5%</td><td>+3.0%</td><td><b>CSCO 财报</b>(05-13 盘后 Q3 FY26)</td></tr>
    <tr><td>2026-05-29</td><td>+1.5%</td><td>+8.9%</td><td>+8.6%</td><td>网安共振</td></tr>
    <tr><td>2026-06-01/02</td><td>+0.8%/+5.4%</td><td>+6.5%/−1.1%</td><td>+6.8%/−1.7%</td><td>混合</td></tr>
    <tr><td>2026-06-05</td><td>−6.7%</td><td>−2.6%</td><td>−6.9%</td><td>普跌</td></tr>
    <tr><td>2026-06-29</td><td>+3.4%</td><td>+8.7%</td><td>+5.8%</td><td>网安强势</td></tr>
    <tr><td>2026-07-14</td><td>−1.8%</td><td>+6.6%</td><td>+11.5%</td><td>网安大涨/CSCO 走弱</td></tr>
    <tr><td>2026-08-13</td><td><b>−8.8%</b></td><td>+2.3%</td><td>+1.7%</td><td><b>CSCO 财报</b>(08-12 盘后 Q4 FY26)</td></tr>
  </table>
  <p class="note">财报归属已用富途 earnings_price_history 核实：02-12 / 05-14 / 08-13 三个 CSCO 最大单日波动均为财报反应日，当日网安两标的方向相反或零跟随。</p>
</div>

<div class="card">
  <h2>六、收益与波动概览（2026-02 至今）</h2>
  <table>
    <tr><th>标的</th><th>累计收益</th><th>年化波动</th><th>驱动定性</th></tr>
    <tr><td>PANW</td><td>+98.3%</td><td>50.2%</td><td>AI 安全叙事主导</td></tr>
    <tr><td>CRWD</td><td>+72.8%</td><td>56.0%</td><td>AI 安全叙事主导</td></tr>
    <tr><td>CSCO</td><td>+42.0%</td><td>41.6%</td><td>硬件周期 + 财报事件</td></tr>
  </table>
  <div class="callout"><b>投资含义：</b>① <b>分散效果真实存在</b>：CSCO 与网安 r≈0.2，组合中加 CSCO 可实现跨链条分散；② <b>网安同买=加杠杆</b>：PANW×CRWD r≈0.84 且持续走高，同时持有两只网安 ≈ 单一叙事的高相关性仓位，非分散；③ 财报日历错开：CSCO（8月中旬）与网安（5月底/8月底财报季）事件日不同源，个股 alpha 可独立捕捉。</div>
</div>

<div class="footer">数据来源：Yahoo Finance（adj_close 日线）· 财报事件核实：富途 earnings_price_history · 报告编号 35 · 生成 2026-08-25</div>
</div>

<script>
const D = @JS_DATA@;
const OKABE = {CSCO: "#0072b2", PANW: "#e69f00", CRWD: "#56b4e9", pair: "#cc79a7"};
const SEGS = D.seg.map(r => r[0]);

function base(extra) {
  return Object.assign({tooltip: {trigger: "axis", axisPointer: {type: "cross"}}, grid: {left: 56, right: 24, top: 40, bottom: 64}}, extra || {});
}
function xAxis(dates) {
  return {type: "category", data: dates, axisLabel: {rotate: 45, fontSize: 11}};
}

// 1 静态分组条形
const staticChart = echarts.init(document.getElementById("chart_static"));
staticChart.setOption(base({legend: {top: 6}, xAxis: {type: "category", data: ["PANW×CRWD", "CSCO×PANW", "CSCO×CRWD"]},
  yAxis: {type: "value", min: 0, max: 1, name: "相关系数 r"},
  series: [
    {name: "2026-02至今", type: "bar", data: [0.8398, 0.2258, 0.1816], itemStyle: {color: "#cc79a7"},
     label: {show: true, position: "top", formatter: p => p.value.toFixed(3)}},
    {name: "2025-01~2026-01", type: "bar", data: [0.7155, 0.4452, 0.4494], itemStyle: {color: "#8cb8e8"},
     label: {show: true, position: "top", formatter: p => p.value.toFixed(3)}},
  ]}));

// 2 滚动相关
const rollChart = echarts.init(document.getElementById("chart_roll"));
rollChart.setOption(base({
  legend: {top: 6, data: ["PANW×CRWD 60d", "CSCO×PANW 60d", "CSCO×CRWD 60d", "PANW×CRWD 30d"]},
  xAxis: xAxis(D.roll_dates),
  yAxis: {type: "value", min: -0.2, max: 1, name: "相关系数"},
  dataZoom: [{type: "inside", start: 0, end: 100}, {type: "slider", bottom: 4, height: 18}],
  series: [
    {name: "PANW×CRWD 60d", type: "line", data: D.pc60, showSymbol: false, lineStyle: {width: 2.5, color: "#cc79a7", opacity: 0.35}, itemStyle: {color: "#cc79a7"}},
    {name: "CSCO×PANW 60d", type: "line", data: D.cp60, showSymbol: false, lineStyle: {width: 2, color: "#0072b2"}, itemStyle: {color: "#0072b2"}},
    {name: "CSCO×CRWD 60d", type: "line", data: D.cc60, showSymbol: false, lineStyle: {width: 2, color: "#56b4e9"}, itemStyle: {color: "#56b4e9"}},
    {name: "PANW×CRWD 30d", type: "line", data: D.pc30, showSymbol: false, lineStyle: {width: 1.2, color: "#009e73", type: "dashed"}, itemStyle: {color: "#009e73"}},
  ]
}));

// 3 分段条形（成组）
const segChart = echarts.init(document.getElementById("chart_seg"));
segChart.setOption(base({legend: {top: 6, data: ["CSCO×PANW", "CSCO×CRWD", "PANW×CRWD"]},
  xAxis: {type: "category", data: SEGS},
  yAxis: {type: "value", min: 0, max: 1, name: "相关系数 r"},
  series: [
    {name: "CSCO×PANW", type: "bar", data: D.seg.map(r => r[1]), itemStyle: {color: "#0072b2"}},
    {name: "CSCO×CRWD", type: "bar", data: D.seg.map(r => r[2]), itemStyle: {color: "#56b4e9"}},
    {name: "PANW×CRWD", type: "bar", data: D.seg.map(r => r[3]), itemStyle: {color: "#e69f00"},
     label: {show: true, position: "top", formatter: p => p.value.toFixed(2)}},
  ]}));

// 4 逐月
const mChart = echarts.init(document.getElementById("chart_month"));
mChart.setOption(base({xAxis: xAxis(D.rm_d), yAxis: {type: "value", min: 0.5, max: 1, name: "r60 均值"},
  series: [{name: "PANW×CRWD", type: "line", data: D.rm_v, showSymbol: true, lineStyle: {width: 2.5, color: "#e69f00"}, itemStyle: {color: "#e69f00"},
    label: {show: true, position: "top", formatter: p => p.value.toFixed(2)}, areaStyle: {color: "rgba(230,159,0,.12)"}}]}));

// 5 极端日
const evChart = echarts.init(document.getElementById("chart_ev"));
evChart.setOption(base({legend: {top: 6, data: ["CSCO", "PANW", "CRWD"]},
  xAxis: {type: "category", data: D.ev_dates, axisLabel: {rotate: 45, fontSize: 11}},
  yAxis: {type: "value", name: "当日收益 %"},
  series: [
    {name: "CSCO", type: "bar", data: D.ev_csco, itemStyle: {color: "#0072b2"}},
    {name: "PANW", type: "bar", data: D.ev_panw, itemStyle: {color: "#e69f00"}},
    {name: "CRWD", type: "bar", data: D.ev_crwd, itemStyle: {color: "#56b4e9"}},
  ]}));
</script>
</body>
</html>
"""

html = TEMPLATE
html = html.replace("@JS_DATA@", js(JS_DATA))
html = html.replace("@N_EXT@", str(n_ext)).replace("@N_SAME@", str(n_same)).replace("@N_PW@", str(n_pw))

with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("written:", os.path.join(OUT, "index.html"), len(html.encode("utf-8")), "bytes")