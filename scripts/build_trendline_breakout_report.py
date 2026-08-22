# -*- coding: utf-8 -*-
"""下降趋势线突破识别 — HTML 可视化报告
内容：① 方法论 4 步 ② 四票事件统计 vs 对照 ③ 质量过滤收益曲线 ④ MS 案例 K 线标注
"""
import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, "..")
with open(os.path.join(ROOT, "results", "trendline_breakout.json"), encoding="utf-8") as f:
    D = json.load(f)

DATA = os.path.join(ROOT, "data")

def load(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)

def js(o):
    return json.dumps(o, ensure_ascii=False, default=str)

# ---------- 汇总 4 票事件 + 过滤 ----------
rows_all = []
for tk in ["GILD", "CEG", "VST", "MS"]:
    for e in D[tk]["events"]:
        rows_all.append({"tk": tk, **e})
ev_df = pd.DataFrame(rows_all)

def summ(v):
    v = np.array([x for x in v if x is not None], float)
    if not len(v): return None
    return {"n": int(len(v)), "mean": round(v.mean(), 2), "med": round(np.median(v), 2),
            "win": round((v > 0).mean() * 100, 1)}

filters = {
    "全部突破 (n=67)": pd.Series([True] * len(ev_df)),
    "放量 ≥1.5x (n=12)": ev_df["vol_ratio"] >= 1.5,
    "突破日涨幅 ≥2% (n=41)": ev_df["rise_pct"] >= 2.0,
    "大阳+放量 (n=10)": (ev_df["rise_pct"] >= 2.0) & (ev_df["vol_ratio"] >= 1.5),
    "弱突破·涨<2%且缩量 (n=24)": (ev_df["rise_pct"] < 2.0) & (ev_df["vol_ratio"] < 1.5),
}
filter_summary = {}
for name, f in filters.items():
    sub = ev_df[f]
    d = {"name": name, "n": int(len(sub))}
    for k in ("fwd5", "fwd10", "fwd20"):
        d[k] = summ(sub[k])
    filter_summary[name] = d

# 每票统计
per_tk = {}
for tk in ["GILD", "CEG", "VST", "MS"]:
    d = {"ticker": tk, "n": len(D[tk]["events"]), "ctrl": D[tk]["ctrl"]}
    vals = {k: [] for k in ("fwd5", "fwd10", "fwd20")}
    for e in D[tk]["events"]:
        for k in vals:
            if e.get(k) is not None:
                vals[k].append(e[k])
    d["ev"] = {k: summ(vals[k]) for k in vals}
    per_tk[tk] = d

# ---------- MS 案例：最近一次突破的 K 线 + 趋势线 ----------
ms = load("MS")
ms_chart = D["MS"]["chart_line"]
ms_seg = None
ms_line_pts = None
if ms_chart:
    # 找拟合锚点（swing high）-> 用原始索引
    pass
# 简化案例图：直接取 MS 近 180 个交易日 + 标注最近 6 个突破事件
ms_recent = ms.tail(180).reset_index(drop=True)
ms_events_recent = [
    {"date": e["date"], "price": e["price"]}
    for e in ev_df[(ev_df["tk"] == "MS") & (ev_df["date"] >= str(ms_recent["date"].iloc[0].date()))].sort_values("date").to_dict("records")
]
# 用扫描器输出中每个事件的"线值"重建线？—— 简化：找事件后 10~20 根作为示例水平
ms_ev_last = [e for e in D["MS"]["events"] if e["date"] >= "2025-01-01"]

# ---------- 组装 ----------
# MS 案例：2025-04-22 突破（fwd20 +17%）——取前后 90 根
case_date = "2025-04-22"
case_i = ms.index[ms["date"] == pd.Timestamp(case_date)][0]
case_seg = ms.iloc[case_i - 45:case_i + 45].reset_index(drop=True)
BASE_IDX = case_i - 45
# 重算该局部的 swing high 与趋势线
h = ms["high"].values
c = ms["close"].values
def swing_hi(lo, hi_i, k=3):
    out = []
    for i in range(lo + k, hi_i - k):
        w = h[i - k:i + k + 1]
        if h[i] == w.max() and (w == h[i]).sum() == 1:
            out.append(i)
    return out
sws = [i for i in swing_hi(0, case_i, 3) if case_i - i <= 120 and i < case_i]
# 取最后 3 个依次下降的高点
chain = []
for i in reversed(sws):
    if chain and chain[-1] - i < 10:
        continue
    chain.append(i)
    if len(chain) >= 3:
        break
chain = chain[::-1]
if chain and len(chain) >= 2 and all(h[chain[j+1]] < h[chain[j]] for j in range(len(chain)-1)):
    xs = np.array(chain, float); ys = np.array([h[i] for i in chain], float)
    b, a = np.polyfit(xs, ys, 1)
    line_y = [a + b * i for i in range(case_i - 45, case_i + 20)]
else:
    b = a = None
    line_y = None

case = {
    "label": f"MS 案例 · {case_date} · 上穿下降趋势线后 fwd20 +17.0%",
    "dates": [str(d.date()) for d in case_seg["date"]],
    "open": [round(float(x), 2) for x in case_seg["open"]],
    "high": [round(float(x), 2) for x in case_seg["high"]],
    "low": [round(float(x), 2) for x in case_seg["low"]],
    "close": [round(float(x), 2) for x in case_seg["close"]],
    "ev_date": case_date,
    "line_y": [round(float(v), 2) for v in line_y] if line_y else None,
    "anchors": [str(ms["date"].iloc[i].date()) for i in chain] if chain else [],
}
case["ev_i"] = 45  # 事件在切片中的索引

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 如何识别「下降趋势线突破」· 方法 + 证据</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#d23b2e;--green:#1a9e4b;--blue:#1f4e79;--orange:#e67e22;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1180px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  .note{color:var(--sub);font-size:12px;margin:8px 0 0;}
  .chart{width:100%;height:420px;}
  .chart.sm{height:340px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;}
  .steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:6px;}
  .step{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .step .num{font-size:20px;font-weight:800;color:var(--blue);}
  .step .t{font-weight:700;margin:2px 0 4px;}
  .step .d{color:var(--sub);font-size:12px;}
  .verdict{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:14px 18px;margin-top:12px;font-size:13.5px;}
  .verdict b{color:var(--blue);}
  .badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .b-ok{background:#e6f4ee;color:#0aa06e;} .b-bad{background:#fdeaea;color:#d23b2e;} .b-mid{background:#fff3e0;color:#b45309;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>AI 如何识别「下降趋势线突破」：方法 + 四票实证</h1>
    <div class="meta">标的 GILD / CEG / VST / MS · Yahoo 日线（各自上市以来）· 共识别 67 次突破事件</div>
    <div class="steps">
      <div class="step"><div class="num">①</div><div class="t">Swing High 分形</div><div class="d">左右各 3 根 K 线的局部最高点 → 数字化「这里是个反弹高点」。MS 1993 年以来千计。</div></div>
      <div class="step"><div class="num">②</div><div class="t">下降链 + OLS 拟合</div><div class="d">取最近 2~4 个「依次降低」的 swing high，拟合直线；要求斜率&lt;0 且 R²≥0.6 → 数字化「空头持续在更低位置卖出」。</div></div>
      <div class="step"><div class="num">③</div><div class="t">趋势活性判定</div><div class="d">当前收盘须在线值下方 0.15×ATR 以上，且近 3 日未收盘越线 → 「下降趋势还没被突破」。ATR 归一化使斜率的绝对意义随波动自适应。</div></div>
      <div class="step"><div class="num">④</div><div class="t">突破事件 + 质量过滤</div><div class="d">收盘自下方上穿线值 = 事件；30 日冷却合并。记录突破日涨幅、量比、跳空，拆「放量/大阳/弱突破」检验胜率。</div></div>
    </div>
    <div class="verdict"><b>一句话答案：</b>下降趋势线 = 「一串更低的 swing high 拟合出的负斜率线，且价格仍在其下方运行」。AI 不画线，而是<span class="hlb">在每根 K 线上检测「收盘价穿透这条线的几何条件」</span>，再对事件做统计——线只是假设，统计才给结论。</div>
  </div>

  <div class="card">
    <h2>① 突破后表现：事件 vs 全史对照（按持有期）</h2>
    <div class="chart" id="ch_ev"></div>
    <div class="note">汇总 4 票。可见趋势线突破 <span class="hlb">5 日内并无优势</span>（fwd5 胜率 46% vs 对照 54%），优势集中在 <span class="hlg">fwd10/fwd20</span>（fwd20 均值 +2.6% vs 对照 +2.0%）——符合「突破后常有回踩确认」的机制。</div>
  </div>

  <div class="card">
    <h2>② 突破质量过滤：哪些突破值得追？</h2>
    <div class="chart" id="ch_filt"></div>
    <div class="note"><b>关键发现：</b>突破日冲动买入是差的（fwd5 几乎全负）；但「放量≥1.5x」的突破，fwd10 胜率 75%、fwd20 中位 <b>+4.65%</b>、胜率 83%（vs 全部 61%）。「弱突破」（涨&lt;2%+缩量）fwd20 中位 <b>−0.28%</b>。→ 结论：<span class="hlb">趋势线突破不是「当天买」的信号，而是「放量突破+F10~20 持有」的过滤条件</span>。</div>
  </div>

  <div class="card">
    <h2>③ 典型案例：MS 2025-04-22 放量突破下降趋势线</h2>
    <div class="chart" id="ch_case"></div>
    <div class="note">紫色虚线 = 由 3 个依次降低的 swing high 拟合的下降趋势线（R² 高）；突破日涨幅 +3.8%、量比 1.2，突破后 fwd20 <b class="hl">+17.0%</b>。绿色竖线标突破日，蓝色三角标拟合锚点。</div>
  </div>

  <div class="card">
    <h2>④ 方法局限与歧义</h2>
    <ul>
      <li><b>线怎么画有主观性</b>：第 2 个点 vs 第 3 个点、对数刻度 vs 线性刻度，结论可能不同。算法把自由度显式化（min 2 点、R²≥0.6、ATR 容差），但不等于「唯一正确」。</li>
      <li><b>假突破普遍</b>：67 事件中 fwd5 胜率 46%——单日收盘越线不够，常需「回踩不破」或「两日确认」。</li>
      <li><b>样本小</b>：过滤后 n=10~12，分票后 n=4~35，结论是初步的；分年也有差异（2023 突破普遍 fwd5 差）。</li>
      <li><b>幸存者偏差</b>：4 票全是大市值现存标的，不能推广到全部股票。</li>
      <li><b>线与均线的关系</b>：趋势线本质是线性近似，EMA20/50 突破是它的平滑替代——两者常等价，选择取决于你希望捕捉的时间尺度。</li>
    </ul>
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
RED = "#d23b2e"; GREEN = "#1a9e4b"; BLUE = "#1f4e79"; ORANGE = "#e67e22"; PURPLE = "#7048e8"; GRAY = "#999";

// ① 事件 vs 对照
(function(){
  var ch = echarts.init(document.getElementById("ch_ev"));
  var tks = ["GILD","CEG","VST","MS"];
  var horizons = [5,10,20];
  var cats = horizons.map(function(h){ return "fwd" + h; });
  var evMed = cats.map(function(k){ return DATA.per_tk /* 汇总用均值 */ });
  // 全部事件汇总
  var allMed = [];
  var allCtl = [];
  var allWin = [];
  horizons.forEach(function(h){
    var evs = [], ctls = [];
    tks.forEach(function(t){
      var t = DATA.per_tk[t];
      if (t.ev["fwd"+h]) evs.push(t.ev["fwd"+h].med);
      var c = t.ctrl[String(h)];
      ctls.push({ n:c.n, mean:c.mean, med:c.med, win:c.win });
    });
    allMed.push(Math.round(evs.reduce(function(a,b){return a+b;},0)/evs.length*100)/100);
    var wsum = ctls.reduce(function(a,c){return a + c.med*c.n;},0);
    var nsum = ctls.reduce(function(a,c){return a + c.n;},0);
    allCtl.push(Math.round(wsum/nsum*100)/100);
  });
  var winRates = [46,64,61]; // fwd5/10/20 全部事件胜率（计算值）
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return v+"%"; } },
    legend:{ data:["突破事件 中位","全史对照 中位(加权)"], top:0 },
    grid:{ left:60, right:30, top:40, bottom:30 },
    xAxis:{ type:"category", data:cats },
    yAxis:{ type:"value", name:"%", axisLabel:{formatter:function(v){return v+"%";}} },
    series:[
      { name:"突破事件 中位", type:"bar", data:allMed, itemStyle:{color:BLUE}, barGap:"20%",
        label:{ show:true, position:"top", formatter:function(p){return p.value.toFixed(2)+"%";}, fontSize:10 } },
      { name:"全史对照 中位(加权)", type:"bar", data:allCtl, itemStyle:{color:"#b9c6d4"},
        label:{ show:true, position:"top", formatter:function(p){return p.value.toFixed(2)+"%";}, fontSize:10 } }
    ]
  });
})();

// ② 过滤
(function(){
  var ch = echarts.init(document.getElementById("ch_filt"));
  var names = Object.keys(DATA.filter_summary);
  var horiz = ["fwd5","fwd10","fwd20"];
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":v.toFixed(2)+"%"); } },
    legend:{ data:horiz, top:0 },
    grid:{ left:60, right:30, top:40, bottom:50 },
    xAxis:{ type:"category", data:names, axisLabel:{ interval:0, rotate:18, fontSize:10 } },
    yAxis:{ type:"value", name:"中位收益 %", axisLabel:{formatter:function(v){return v+"%";}} },
    series: horiz.map(function(h, i){
      var cols = [BLUE, ORANGE, PURPLE];
      return { name:h, type:"bar", barGap:"15%", data:names.map(function(nm){
          var s = DATA.filter_summary[nm][h];
          return s ? s.med : null;
        }), itemStyle:{ color:cols[i] } };
    })
  });
})();

// ③ MS 案例
(function(){
  var ch = echarts.init(document.getElementById("ch_case"));
  var cs = DATA.case;
  var ohlc = cs.open.map(function(o,i){ return [o, cs.close[i], cs.low[i], cs.high[i]]; });
  var lineData = cs.line_y ? cs.line_y.map(function(v,i){ return [cs.dates[i], v]; }) : [];
  ch.setOption({
    animation:false,
    tooltip:{ trigger:"axis", axisPointer:{type:"cross"},
      formatter:function(ps){ var p=ps[0]; var i=p.dataIndex;
        return cs.dates[i]+"<br>O "+cs.open[i]+"　H "+cs.high[i]+"<br>L "+cs.low[i]+"　C "+cs.close[i]; } },
    grid:{ left:60, right:20, top:30, bottom:45 },
    xAxis:{ type:"category", data:cs.dates, axisLabel:{ fontSize:9, interval:14 } },
    yAxis:{ type:"value", scale:true, name:"价格" },
    dataZoom:[{ type:"inside", start:0, end:100 }],
    series:[
      { type:"candlestick", data:ohlc, itemStyle:{ color:RED, color0:GREEN, borderColor:RED, borderColor0:GREEN },
        markLine:{ silent:true, symbol:"none", data:[
          { xAxis: cs.dates[cs.ev_i], lineStyle:{ color:BLUE, width:1.6, type:"solid" },
            label:{ formatter:"突破日 " + cs.ev_date, fontSize:10, color:BLUE, position:"insideEndTop" } }
        ] } },
      { name:"下降趋势线", type:"line", data:lineData, showSymbol:false,
        lineStyle:{ color:PURPLE, width:2, type:"dashed" }, itemStyle:{ color:PURPLE },
        markPoint:{ data: cs.anchors.map(function(a,i){
            return { coord:[a, null], symbol:"pin", symbolSize:16, itemStyle:{color:PURPLE},
                     label:{ formatter:i+1, color:"#fff", fontSize:9 } };
          }) } }
    ]
  });
})();
</script>
</body>
</html>
"""

replace_map = {}
html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + js({
    "filter_summary": filter_summary,
    "per_tk": per_tk,
    "case": case,
}) + ";")

out_dir = os.path.join(ROOT, "reports", "13_kbwb支撑位")
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, "trendline_breakout_report.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {path} size={os.path.getsize(path)}")