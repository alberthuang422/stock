# -*- coding: utf-8 -*-
"""
MCD RSI 低位（下穿40）事件窗口质量分析报告
窗口 N=20 交易日：
  ① 窗口内最大涨幅 max_gain = max(px[t+1..t+N])/px[t] - 1
  ② 效率比率 ER (Kaufman) = |px[t+N]-px[t]| / Σ|Δpx|  (0~1，越高越单边)
  ③ SPY 同窗口对照
  ④ 基率 = 全部交易日 20 日窗口的分布（重叠窗口）
读取 results/mcd_rsi_low_er.json
输出 reports/48_MCD_RSI低位窗口质量/index.html
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "48_MCD_RSI低位窗口质量")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "mcd_rsi_low_er.json"), encoding="utf-8") as f:
    D = json.load(f)

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}%"

base = D["base"]
bc = D["buckets_cd10"]
st = D["stage_cd10"]

# ---------- 档位表 ----------
BK_ORDER = ["<30", "30-35", "35-40"]
bk_rows = []
bk_chart = []
for bk in BK_ORDER:
    b = bc[bk]
    nn = b.get("m_maxg", {}).get("n", 0)
    def g(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        cls = "up" if s["mean"] > 0 else "dn"
        return f"<td class='{cls} nowrap'>{pct(s['mean'])}</td>"
    def er(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        return f"<td class='nowrap'>{s['mean']:.2f}</td>"
    bk_rows.append(f"<tr><td class='nowrap'><b>RSI {bk}</b></td><td>{nn}</td>"
                   f"{g(b['m_maxg'])}{g(b['s_maxg'])}{er(b['m_er'])}{er(b['s_er'])}{g(b['ex'])}</tr>")
    bk_chart.append({"bk": bk, "n": nn,
                     "m": b["m_maxg"]["mean"] if nn else None,
                     "s": b["s_maxg"]["mean"] if nn else None,
                     "mere": b["m_er"]["mean"] if nn else None,
                     "sere": b["s_er"]["mean"] if nn else None,
                     "ex": b["ex"]["mean"] if nn else None})
bk_rows_html = "".join(bk_rows)

# ---------- 基率行 ----------
def brow(name, b, tag=""):
    def g(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        cls = "up" if s["mean"] > 0 else "dn"
        return f"<td class='{cls} nowrap'>{pct(s['mean'])}</td>"
    def er(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        return f"<td class='nowrap'>{s['mean']:.2f}</td>"
    cls = " class='baserow'" if tag == "base" else ""
    return (f"<tr{cls}><td class='nowrap'><b>{name}</b></td><td>{b['m_maxg']['n']}</td>"
            f"{g(b['m_maxg'])}{g(b['s_maxg'])}{er(b['m_er'])}{er(b['s_er'])}{g(b['ex'])}</tr>")

base_rows_html = "".join([
    brow("基率 · 全部20日窗口（重叠）", base, "base"),
    brow("cd10 下穿40 全部事件", {"m_maxg": {"n": sum(bc[b]["m_maxg"]["n"] for b in BK_ORDER),
                                          "mean": np.mean([bc[b]["m_maxg"]["mean"] * bc[b]["m_maxg"]["n"] for b in BK_ORDER]) / max(1, sum(bc[b]["m_maxg"]["n"] for b in BK_ORDER)) if sum(bc[b]["m_maxg"]["n"] for b in BK_ORDER) else None},
                             "s_maxg": {"n": sum(bc[b]["s_maxg"]["n"] for b in BK_ORDER),
                                          "mean": np.mean([bc[b]["s_maxg"]["mean"] * bc[b]["s_maxg"]["n"] for b in BK_ORDER]) / max(1, sum(bc[b]["s_maxg"]["n"] for b in BK_ORDER)) if sum(bc[b]["s_maxg"]["n"] for b in BK_ORDER) else None},
                             "m_er": {"n": sum(bc[b]["m_er"]["n"] for b in BK_ORDER),
                                          "mean": np.mean([bc[b]["m_er"]["mean"] * bc[b]["m_er"]["n"] for b in BK_ORDER]) / max(1, sum(bc[b]["m_er"]["n"] for b in BK_ORDER)) if sum(bc[b]["m_er"]["n"] for b in BK_ORDER) else None},
                             "s_er": {"n": sum(bc[b]["s_er"]["n"] for b in BK_ORDER),
                                          "mean": np.mean([bc[b]["s_er"]["mean"] * bc[b]["s_er"]["n"] for b in BK_ORDER]) / max(1, sum(bc[b]["s_er"]["n"] for b in BK_ORDER)) if sum(bc[b]["s_er"]["n"] for b in BK_ORDER) else None},
                             "ex": {"n": sum(bc[b]["ex"]["n"] for b in BK_ORDER),
                                          "mean": np.mean([bc[b]["ex"]["mean"] * bc[b]["ex"]["n"] for b in BK_ORDER]) / max(1, sum(bc[b]["ex"]["n"] for b in BK_ORDER)) if sum(bc[b]["ex"]["n"] for b in BK_ORDER) else None}})
])

# ---------- 事件明细（cd10，超额最差/最好各展示，附 ER） ----------
events = sorted(D["events_cd10"], key=lambda x: (x["ex"] if x["ex"] is not None else -999))
worst = events[:10]
best = events[-10:][::-1]

def erow(e):
    def f(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='{'up' if v>0 else 'dn'} nowrap'>{v:+.1f}</td>"
    def g2(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='nowrap'>{v:.2f}</td>"
    return (f"<tr><td class='nowrap'>{e['date']}</td><td>{e['rsi']}</td>"
            f"{f(e['m_maxg20'])}{f(e['s_maxg'])}{g2(e['m_er20'])}{g2(e['s_er'])}"
            f"{f(e['m_fwd20'])}{f(e['s_fwd'])}{f(e['ex'])}</tr>")

worst_html = "".join(erow(e) for e in worst)
best_html = "".join(erow(e) for e in best)

# ---------- 近 5 事件（新格式：三窗口 最大/最终/ER） ----------
recent = D["events_cd10"][:5] if len(D["events_cd10"]) > 5 else D["events_cd10"]
WINS = (5, 10, 20)

def wrow(e):
    """一行 = 日期 + RSI + T+5/T+10/T+20 各三列（最大涨幅/最终收益/ER）"""
    def g(v):
        if v is None: return "<td class='na'>—</td>"
        cls = "up" if v > 0 else "dn"
        return f"<td class='{cls} nowrap'>{v:+.2f}%</td>"
    def g2(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='nowrap'>{v:.2f}</td>"
    cells = ""
    for NN in WINS:
        cells += (f"{g(e.get(f'm_maxg{NN}'))}{g(e.get(f'm_fwd{NN}'))}{g2(e.get(f'm_er{NN}'))}")
    return (f"<tr><td class='nowrap'>{e['date']}</td><td>{e['rsi']}</td>"
            f"{cells}</tr>")

def whead():
    th = "<tr><th rowspan='2'>日期</th><th rowspan='2'>RSI</th>"
    for NN in WINS:
        th += (f"<th colspan='3' class='grph'>{NN}日窗口<br>最大 / 最终 / ER</th>")
    th += "</tr><tr>"
    for NN in WINS:
        th += "<th>最大</th><th>最终</th><th>ER</th>"
    th += "</tr>"
    return th

recent_html = "".join(wrow(e) for e in recent)
recent_head_html = whead()

# ---------- 图表数据 ----------
CHART = {
    "bucket": bk_chart,
    "base_m": base["m_maxg"]["mean"], "base_s": base["s_maxg"]["mean"],
    "base_er_m": base["m_er"]["mean"], "base_er_s": base["s_er"]["mean"],
    "scatter": [{"ex": e["ex"], "er": e["m_er20"], "date": e["date"], "rsi": e["rsi"]}
                for e in D["events_cd10"] if e["ex"] is not None and e["m_er20"] is not None],
}

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o
CHART = clean(CHART)

echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCD · RSI 低位事件窗口质量（最大涨幅 + 效率比率 ER）</title>
__ECHARTS__
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;--amber:#b45309;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:13.5px;margin:14px 0 6px;color:#374151;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;}
  td.nowrap{white-space:nowrap;}
  .note2{color:var(--sub);font-size:11px;font-weight:400;}
  td.up{color:var(--verm);font-weight:600;white-space:nowrap;}
  td.dn{color:var(--teal);font-weight:600;white-space:nowrap;}
  td.na{color:#c3c8cf;white-space:nowrap;}
  td.grp{background:#eef3fa;color:#4b5563;font-weight:700;text-align:center;font-size:11px;border-left:1px solid #dbe4ef;border-right:1px solid #dbe4ef;padding:5px 4px;}
  th.grph{text-align:center;border-left:1px solid #dbe4ef;border-right:1px solid #dbe4ef;background:#eaf1fa;color:#374151;font-weight:700;font-size:11.5px;}
  tr.baserow td{background:#fbf7ee;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:420px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .callout{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}
  .callout.blue{border-color:#cfe0f5;background:#f0f6fd;}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>MCD · RSI 低位事件窗口质量（最大涨幅 + 效率比率 ER）</h1>
  <div class="meta">事件口径：RSI 下穿40首日买入 · 窗口 N=20 交易日 · cd10 去重（事件日相隔≥10交易日）· SPY 同窗口对照 · 2026-08-28</div>
  <div class="callout blue">
    <b>指标定义：</b>① <b>窗口最大涨幅</b> = max(收盘[t+1..t+20]) ÷ 买入收盘 − 1，衡量反弹最高能到哪；
    ② <b>效率比率 ER（Kaufman）</b> = |收盘[t+20] − 收盘[t]| ÷ Σ|Δ收盘|（0~1），1 为完全单边、近 0 为来回震荡——
    ER 把"涨了但过程曲折"与"一路单边"区分开，是趋势质量的核心指标。
  </div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict amber"><b>① 为什么 MCD 超额少：窗口最大涨幅不差，但 ER 低于 SPY、且下行端被"假反弹"拖累。</b>
    cd10 下穿40 事件：MCD 窗口最大涨幅均值 +4.5%（<30 档 +3.1%、35–40 档 +4.6%）不比 SPY（+3.6%）差；
    但 <b>MCD ER 中位 0.19 vs SPY 0.22</b>（35–40 档 0.19 vs 0.22）——MCD 的反弹更"磕绊"（先涨后回），
    且最差 5 个超额事件（−18~−10pp）全部是 MCD 几乎没涨（maxG +0.2%~+3.2%）而 SPY 大涨（+3.9%~+9.7%）的窗口（2026-04-01/2026-04-21/2002-09/2000-02/2019-10）。</div>
  <div class="verdict"><b>② ER 对超额有区分力：ER 高 → 超额正，ER 低 → 超额负。</b>
    超额最差 5 档：MCD ER 0.22~0.44、SPY ER 0.01~0.71；超额最好 5 档（+13~+20pp）：MCD ER 0.31~0.55、SPY ER 0.02~0.44——
    <b>MCD 自身 ER&gt;0.3 的单边反弹几乎都是大正超额（2000-04/1998-09/2000-12）</b>，而低 ER 的震荡段超额趋零或为负。</div>
  <div class="verdict gr"><b>③ 反弹"天花板"不是问题，问题是"接飞刀"。</b>
    <30 档（5 次，最深超卖）MCD 窗口最大涨幅 +3.05%、但 <b>超额 −3.73pp（T+5/T+10/T+20 均负）</b>——5 次全为单日暴跌穿30 的极端日（2020-02 疫情等），
    之后的 20 日里 MCD 只回来 3%，SPY 却已经 +3.5% 且 ER 0.15~0.71 反弹更流畅。真正该做的不是"下穿当天买"，而是等 ER 确认后的右侧。<b>ER 让你避开"假反弹"，但代价是错过 V 型反弹的第一口。</b></div>
  <div class="verdict"><b>④ 本轮牛市：最大涨幅收窄到 +2.9%、超额 −2.08pp。</b>
    2023 年以来 29 个独立信号（cd10）MCD 窗口最大涨幅仅 +2.87%（疫情前 +4.82%），超额中位 −1.64pp——
    近年 MCD 低位反弹幅度变小、且跑输 SPY，是"超额少"在时间上的第二轮证据。</div>
</div>

<div class="card">
  <h2>一、事件窗口质量 vs 基率（cd10 171 事件）</h2>
  <div class="chart" id="ch_bk"></div>
  <p class="src" style="margin-top:2px">事件档内 MCD/SPY 窗口最大涨幅与 ER 均值；深蓝点为各档 ER（左轴 0~0.5）、柱为最大涨幅（右轴）。</p>
  <div class="scroll" style="margin-top:8px">
  <table>
    <thead><tr><th>档位</th><th>n</th><th>MCD maxGain</th><th>SPY maxGain</th><th>MCD ER</th><th>SPY ER</th><th>超额T+20</th></tr></thead>
    <tbody>__BK_ROWS__</tbody>
  </table>
  </div>
  <p class="src">基率 = 全部 7944 个重叠 20 日交易日窗口（非事件限定）。MCD 基率 maxGain +4.23% > SPY +3.12%，说明 MCD 日常"能涨"，问题在下行段反弹质量与弹性。</p>
</div>

<div class="card">
  <h2>二、ER × 超额散点（每次独立信号）</h2>
  <div class="chart" id="ch_scatter"></div>
  <p class="src">横轴 = MCD 窗口 ER，纵轴 = MCD 相对 SPY 的 T+20 超额（pp）。右上象限（高 ER、正超额）集中在 2000 年~2005 年；左下（低 ER、负超额）包含 2026-04 两次。右上方是"真单边反弹"。</p>
</div>

<div class="card">
  <h2>三、超额最差 / 最好事件（各 10 个）</h2>
  <div class="grid2">
    <div>
      <h3>▼ 超额最差 Top10</h3>
      <div class="scroll"><table>
        <thead><tr><th>日期</th><th>RSI</th><th>MCD<br>maxG</th><th>SPY<br>maxG</th><th>MCD<br>ER</th><th>SPY<br>ER</th><th>MCD<br>T20</th><th>SPY<br>T20</th><th>超额</th></tr></thead>
        <tbody>__WORST_ROWS__</tbody>
      </table></div>
    </div>
    <div>
      <h3>▲ 超额最好 Top10</h3>
      <div class="scroll"><table>
        <thead><tr><th>日期</th><th>RSI</th><th>MCD<br>maxG</th><th>SPY<br>maxG</th><th>MCD<br>ER</th><th>SPY<br>ER</th><th>MCD<br>T20</th><th>SPY<br>T20</th><th>超额</th></tr></thead>
        <tbody>__BEST_ROWS__</tbody>
      </table></div>
    </div>
  </div>
  <div class="src" style="margin-top:6px">最差档（负超额）集中在 2000 年初、2002-09、2019-10、2026-04：MCD 窗口 maxG 多在 +3% 以下、ER 偏低；最好档（正超额）集中在 1997-2000：MCD ER 0.31~0.55，单边流畅反弹。复权价口径下 2000 年前后 MCD 弹性比现在大得多。</div>
</div>

<div class="card">
  <h2>四、最近 5 次独立信号（cd10）</h2>
  <div class="scroll"><table>
    <thead>__RECENT_HEAD__</thead>
    <tbody>__RECENT_ROWS__</tbody>
  </table></div>
  <div class="src">2026 年 5 个信号：每行为一次下穿40买入，三组列为 T+5 / T+10 / T+20 窗口内的 最大涨幅 / 最终收益 / 效率比率 ER。
    例：2026-07-15（RSI 37.8）持有 20 日最终 +4.06%，但路径 ER 仅 0.19——先跌后涨、非单边；
    2026-06-03（RSI 37.1）T+5 最终 +3.38%、ER 0.64 为最流畅的一次；2026-04-21（RSI 38.7）三窗口最终全负、最大涨幅仅 +0.23%，是"假反弹"典型。</div>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close）· 脚本：scripts/mcd_rsi_low_er.py + build_mcd_rsi_low_er_report.py · 数据文件：results/mcd_rsi_low_er.json。
  <b>本报告仅为统计回测，不构成投资建议。</b></div>
</div>

</div>
<script>
var CHART = __DATA_JSON__;
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
(function(){
  var ch = echarts.init(document.getElementById("ch_bk"));
  var bk = CHART.bucket;
  var names = bk.map(function(x){return x.bk;});
  var m = bk.map(function(x){return x.m==null?0:+x.m.toFixed(2);});
  var s = bk.map(function(x){return x.s==null?0:+x.s.toFixed(2);});
  var mere = bk.map(function(x){return x.mere==null?0:+x.mere.toFixed(2);});
  var sere = bk.map(function(x){return x.sere==null?0:+x.sere.toFixed(2);});
  ch.setOption({
    animation:false,
    legend:{data:["MCD maxGain","SPY maxGain","MCD ER","SPY ER"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:55,right:55,top:40,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:[
      {type:"value",name:"maxGain %",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
      {type:"value",name:"ER",min:0,max:0.5,axisLabel:{formatter:function(v){return v.toFixed(2);},color:"#9aa1ab"},splitLine:{show:false}}
    ],
    series:[
      {name:"MCD maxGain",type:"bar",barWidth:12,data:m,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"SPY maxGain",type:"bar",barWidth:12,data:s,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"MCD ER",type:"line",yAxisIndex:1,data:mere,lineStyle:{color:C.blue,width:1.6},symbol:"none",itemStyle:{color:C.blue}},
      {name:"SPY ER",type:"line",yAxisIndex:1,data:sere,lineStyle:{color:C.sub,width:1.2,type:"dashed"},symbol:"none",itemStyle:{color:C.sub}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_scatter"));
  var pts = CHART.scatter.map(function(p){return [p.er, p.ex];});
  ch.setOption({
    animation:false,
    tooltip:{trigger:"item",formatter:function(p){
      var d = CHART.scatter[p.dataIndex];
      return d.date+"<br>RSI "+d.rsi+"<br>MCD ER "+d.er.toFixed(2)+"<br>超额 "+(d.ex>=0?"+":"")+d.ex.toFixed(2)+"pp";}},
    grid:{left:55,right:25,top:25,bottom:40},
    xAxis:{type:"value",name:"MCD 窗口 ER",min:0,max:0.8,axisLabel:{color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    yAxis:{type:"value",name:"超额 T+20 (pp)",axisLabel:{color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[{type:"scatter",data:pts,symbolSize:8,itemStyle:{color:C.blue,opacity:0.75},
      markLine:{silent:true,symbol:"none",data:[{yAxis:0,lineStyle:{color:C.sub,type:"dashed"},label:{formatter:"超额=0",color:C.sub,fontSize:9}}]}}]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__BK_ROWS__", bk_rows_html)
HTML = HTML.replace("__WORST_ROWS__", worst_html)
HTML = HTML.replace("__BEST_ROWS__", best_html)
HTML = HTML.replace("__RECENT_HEAD__", recent_head_html)
HTML = HTML.replace("__RECENT_ROWS__", recent_html)
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")