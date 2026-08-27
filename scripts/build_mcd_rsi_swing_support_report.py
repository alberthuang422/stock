# -*- coding: utf-8 -*-
"""
构建研报 46：MCD 单股 RSI 摆动低点(swing low)聚集支撑买入
口径与 41 号完全一致（K=5/M=3/TOL=3/BUF=2/COOL=20）
读取 results/mcd_rsi_swing_support.json
输出 reports/46_MCD_RSI摆动低点支撑买入/index.html
静默写盘。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "46_MCD_RSI摆动低点支撑买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "mcd_rsi_swing_support.json"), encoding="utf-8") as f:
    D = json.load(f)

ea = D["events_all"]
base = D["baseline_all_days"]
cur = D["current"]
ev = D["events"]

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}%"

def pct2(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- KPI ----------
n_ev = D["n_events"]
KPI = [
    (str(n_ev), "MCD 支撑买入事件总数（1995 起）", "num"),
    (pct2(ea["T20"]["mean"]), "全部事件 T+20 均值（胜率 %d%%）" % ea["T20"]["win"], "up"),
    (pct2(ea["T20_ex_spy"]["mean"]), "全部事件 T+20 超额 vs SPY", "warn" if ea["T20_ex_spy"]["mean"] < 0 else "up"),
    (pct2(base["T20"]["mean"]), "MCD 全历史基率 T+20", "up"),
    ("%.1f" % cur["rsi"], "当前 RSI（%s）" % cur["as_of"], "num"),
    ("无", "当前生效 swing low 聚集支撑", "warn"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

# ---------- 事件明细 ----------
def f(v):
    if v is None: return "<td class='na'>—</td>"
    return f"<td class='{'up' if v>0 else 'dn'} nowrap'>{v:+.2f}%</td>"

ev_rows = []
for e in ev:
    sw = "、".join(str(x) for x in e["swing_lows"])
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td>"
        f"<td>{e['rsi']}</td><td>{e['support']}</td><td class='note2' nowrap>{sw}</td>"
        f"<td class='nowrap'>{e['px']}</td>{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>")
ev_rows_html = "".join(ev_rows)

# ---------- 分档表 ----------
bk_order = ["<35", "35-40", "40-45", "45-50", ">=50"]
bk_rows = []
bk_chart = []
for bk in bk_order:
    b = D["support_buckets"][bk]
    nn = b.get("T5", {}).get("n", 0)
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])}{tstr}</td>"
    bk_rows.append(f"<tr><td class='nowrap'><b>支撑位 {bk}</b></td><td>{nn}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}</tr>")
    bk_chart.append({"bk": bk, "n": nn,
                     "t5": b["T5"]["mean"] if nn else None,
                     "t10": b["T10"]["mean"] if nn else None,
                     "t20": b["T20"]["mean"] if nn else None})
bk_rows_html = "".join(bk_rows)

# ---------- 分阶段 ----------
STAGE_CN = {"A_pre": "疫情前(1995~2020-02)", "B_post": "疫情及股灾后(2020-02~2022-12)", "C_bull": "本轮牛市(2023~)"}
st_rows = []
for st in ["A_pre", "B_post", "C_bull"]:
    b = D["by_stage"][st]
    def c2(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    st_rows.append(f"<tr><td class='nowrap'><b>{STAGE_CN[st]}</b></td><td>{b['T5']['n']}</td>{c2(b['T5'])}{c2(b['T10'])}{c2(b['T20'])}</tr>")
st_rows_html = "".join(st_rows)

# 对照：41 号全池 / 消费板块（硬编码自 41 号 JSON，避免耦合）
REF = [
    ("MCD 全历史基率", base["T20"]["n"], base["T5"]["mean"], base["T10"]["mean"], base["T20"]["mean"], base["T5"]["win"], base["T10"]["win"], base["T20"]["win"], None, None, None),
    ("MCD 支撑买入（本报告）", ea["T5"]["n"], ea["T5"]["mean"], ea["T10"]["mean"], ea["T20"]["mean"], ea["T5"]["win"], ea["T10"]["win"], ea["T20"]["win"], ea["T5_ex_spy"]["mean"], ea["T10_ex_spy"]["mean"], ea["T20_ex_spy"]["mean"]),
    ("41号全池 72 蓝筹支撑买入", 594, 0.548, 0.822, 1.39, 52.8, 55.6, 58.6, 0.15, 0.33, 0.53),
    ("41号全池 消费板块支撑买入", 78, 0.225, 0.795, 1.402, 51.3, 55.1, 59.0, None, None, -0.107),
]
def ref_cell(v, with_win=None):
    if v is None: return "<td class='na'>—</td>"
    return f"<td class='{'up' if v>0 else 'dn'} nowrap'>{pct(v)}</td>"
ref_rows = []
for name, n, t5, t10, t20, w5, w10, w20, x5, x10, x20 in REF:
    ref_rows.append(
        f"<tr><td class='nowrap'><b>{name}</b></td><td>{n}</td>"
        f"{ref_cell(t5)}{ref_cell(t10)}{ref_cell(t20)}"
        f"{ref_cell(x5)}{ref_cell(x10)}{ref_cell(x20)}</tr>")
ref_rows_html = "".join(ref_rows)

# ---------- 图表数据 ----------
CH = D["chart"]
rsi = CH["rsi"]
px = CH["px"]
dates = CH["dates"]
sup = CH["support_line"]
n_days = len(dates)
base_last_120_idx = n_days - 120

# 近120日 swing low 标注（诊断数据，用于展示"为什么无聚集"）
dg = cur["diag"]
sl_marks = []
for dt_s, v in zip(dg["swing_low_dates_120d"], dg["swing_lows_120d"]):
    try:
        i = dates.index(dt_s)
        sl_marks.append({"i": i, "v": v, "d": dt_s})
    except ValueError:
        pass

CHART = {
    "rsi": rsi, "px": px, "dates": dates, "support": sup,
    "last120": base_last_120_idx, "cur_rsi": cur["rsi"],
    "last_date": cur["as_of"], "cur_px": cur["px"],
    "sl_marks": sl_marks,
    "bucket": bk_chart,
    "stage": [{"name": STAGE_CN[st], **{k: (D["by_stage"][st][k]["mean"] if D["by_stage"][st][k].get("n") else None) for k in ["T5", "T10", "T20"]}} for st in ["A_pre", "B_post", "C_bull"]],
    "baseline_t20": base["T20"]["mean"],
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
<title>MCD · RSI 摆动低点(swing low)聚集支撑买入 · 单股复刻</title>
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
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:19px;font-weight:700;}
  .kpi .num.up{color:var(--verm);} .kpi .num.dn{color:var(--teal);} .kpi .num.warn{color:var(--amber);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;}
  td.nowrap{white-space:nowrap;}
  .note2{color:var(--sub);font-size:11px;font-weight:400;}
  td.up{color:var(--verm);font-weight:600;white-space:nowrap;}
  td.dn{color:var(--teal);font-weight:600;white-space:nowrap;}
  td.na{color:#c3c8cf;white-space:nowrap;}
  tr.baserow td{background:#fbf7ee;}
  .scroll{overflow-x:auto;}
  .evbox{max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:8px;}
  .evbox table th{position:sticky;top:0;z-index:2;}
  .chart{width:100%;height:420px;}
  .callout{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}
  .callout.blue{border-color:#cfe0f5;background:#f0f6fd;}
  .callout.b{color:var(--amber);} .callout.blue b{color:var(--blue);}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>MCD · RSI 摆动低点（swing low）聚集支撑买入 · 单股复刻</h1>
  <div class="meta">事件研究 · MCD 日线 1995-01-03 ~ 2026-08-26（7965 根K线）· 口径与 41 号报告完全一致 · 生成于 2026-08-28</div>
  <div class="callout blue">
    <b>口径（同 41 号）：</b>swing low = 某日 RSI 严格低于前后各 K=5 日的 RSI。支撑位 S = 过去 120 日内<b>最近 3 个摆动低点聚集</b>（RSI 极差 ≤3）中的<b>最低谷</b>。
    买入触发 = RSI 从上方首日进入 [S−2, S+2]，当日收盘买入，同票 20 日去重。T+N 为交易日。
  </div>
  <div class="kpis">__KPI__</div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict amber"><b>① MCD 的"支撑买入"信号极稀缺 —— 31.7 年仅触发 6 次，且本轮牛市（2023~）一次都没有。</b>
    蓝筹属性强（长期单边上涨）导致 RSI 摆动低点通常<b>不聚集</b>：要么 V 型反转只留下单一低点，要么逐级抬升（higher lows）分布过散，都无法凑齐"3 个谷底在 ±3 内反复测试"。最近一次支撑买入信号是 <b>2022-12-15</b>，距今逾 3 年半。</div>
  <div class="verdict"><b>② 仅有的 6 次信号：绝对收益可观，但超额为负 —— 是 β，不是择时 edge。</b>
    6 次买入 T+20 <b>+4.96%</b>（胜率 83.3%，t=2.74），显著高于 MCD 全历史基率 +1.08%；但相对 SPY 的超额 <b>−0.56%</b>（t=−0.31，不显著）。
    即买入后赚钱主要来自 MCD 自身长期上涨（beta），而非"支撑买入时点"跑赢了市场。</div>
  <div class="verdict gr"><b>③ 与 41 号全池结论一致：MCD 的支撑买入同样落在"无 edge"区间。</b>
    41 号全池 72 蓝筹 594 事件 T+20 +1.39% ≈ 基率（无 edge）；MCD 单股 6 事件 +4.96% 看似更高，但 n=6 无统计意义、且超额为负。
    唯一干净 edge 是 41 号确认的"支撑位 &lt;35~40"（均值回归），而 MCD 6 次信号中支撑位 &lt;40 的仅 2 次（2005 年两次）。</div>
  <div class="verdict gr"><b>④ 当前状态：无有效支撑、不在触发区 —— 观望区间。</b>
    2026-08-26 收盘 266.93、RSI=44.4。近 120 日 RSI 摆动低点为 29.9→35.8→24.5→36.5→33.4→37.8→38.7→43.2→41.9，<b>极差 18.7（≫3），不构成聚集支撑</b>；
    RSI 44.4 恰落在 39/41 号共同确认的"无 edge 震荡区"（40–50）。若按 39 号"真 edge 在 RSI&lt;30"的逻辑，MCD 最近一次该买的位置是 <b>2026-05-08（RSI 25.2，T+20 +1.42%）</b>，已过。</div>
</div>

<div class="card">
  <h2>一、当前状态：近 400 交易日 RSI 与支撑轨迹</h2>
  <div class="chart" id="ch_rsi"></div>
  <div class="src">蓝色为 RSI(14)；橙色散点为近 120 日出现的摆动低点（9 个，过度分散、未聚集）；浅色区为最近 120 个交易日窗口；右轴灰线为收盘价。
  当前 RSI 44.4，高于全部摆动低点，位于"无 edge 震荡区"。</div>
</div>

<div class="card">
  <h2>二、历史全部 6 次支撑买入事件</h2>
  <div class="scroll">
  <table>
    <thead><tr><th>日期</th><th>RSI</th><th>支撑S</th><th>聚集的摆动低点</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
    <tbody>__EV_ROWS__</tbody>
  </table>
  </div>
  <div class="src">6 次事件中 5 次在疫情前（1998/2005×2/2013/2019），1 次在 2022-12；本轮牛市 0 次。
  亮点：1998-11 和 2005 年两次（含支撑位&lt;35 的 2005-06）T+20 均 &gt;+8%；唯一亏损是 2013-04（T+20 −0.78%）。
  样本仅 6，任何统计推断均无置信度——本表价值在"信号何时出现"，而非"出现后赚多少"。</div>
</div>

<div class="card">
  <h2>三、分档 / 分阶段 / 全池对照</h2>
  <div class="chart" id="ch_bk"></div>
  <div class="grid2">
    <div>
      <h3>支撑位高度分档</h3>
      <div class="scroll"><table>
        <thead><tr><th>支撑位</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__BK_ROWS__</tbody>
      </table></div>
    </div>
    <div>
      <h3>分阶段</h3>
      <div class="scroll"><table>
        <thead><tr><th>阶段</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__ST_ROWS__</tbody>
      </table></div>
    </div>
  </div>
  <h3>对照：MCD vs 41 号全池口径</h3>
  <div class="scroll">
  <table>
    <thead><tr><th>口径</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th><th>超额T+5</th><th>超额T+10</th><th>超额T+20</th></tr></thead>
    <tbody>__REF_ROWS__</tbody>
  </table>
  </div>
  <div class="src">MCD 支撑买入 T+20 +4.96% 高于 41 号全池（+1.39%）与消费板块（+1.40%），但超额 vs SPY 为 −0.56%（全池 +0.53%、消费 −0.11%）。
  41 号全池对照数值取自 results/blue_chip_rsi_swing_support.json（2026-08-27）。</div>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close）· 方法：与 41 号完全同口径（swing low K=5/M=3/TOL=3/BUF=2/COOL=20）· 脚本：scripts/mcd_rsi_swing_support.py + build_mcd_rsi_swing_support_report.py · 数据文件：results/mcd_rsi_swing_support.json。
  <b>本报告仅为统计回测，不构成投资建议。</b></div>
</div>

</div>
<script>
var CHART = __DATA_JSON__;
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
(function(){
  var ch = echarts.init(document.getElementById("ch_rsi"));
  var n = CHART.dates.length;
  var x = CHART.dates.map(function(_,i){return i;});
  var last120 = CHART.last120;
  var supData = CHART.support.map(function(v,i){return v===null?null:[i,v];});
  var sl = CHART.sl_marks.map(function(m){return [m.i, m.v];});
  ch.setOption({
    animation:false,
    legend:{data:["RSI(14)","支撑位(聚集谷值)","近120日摆动低点","收盘价"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"cross"},formatter:function(ps){
      var i = ps[0].dataIndex;
      var h = "<b>"+CHART.dates[i]+"</b>";
      ps.forEach(function(p){
        var v = p.value; if(v instanceof Array) v = v[1]+"（RSI）"; else v = v==null?"—":v;
        h += "<br>"+p.marker+p.seriesName+": "+v;
      });
      return h;}},
    grid:{left:55,right:60,top:45,bottom:30},
    xAxis:{type:"value",min:0,max:n-1,show:false},
    yAxis:[
      {type:"value",name:"RSI",min:0,max:100,axisLabel:{color:"#4b5563",fontSize:11},splitLine:{lineStyle:{color:"#eef0f3"}}},
      {type:"value",name:"价格($)",scale:true,axisLabel:{color:"#9aa1ab",fontSize:11},splitLine:{show:false},splitNumber:4}
    ],
    series:[
      {name:"近120日摆动低点",type:"scatter",data:sl,symbol:"diamond",symbolSize:8,itemStyle:{color:C.orange},
       markArea:{silent:true,data:[[{xAxis:last120},{xAxis:n-1}]],itemStyle:{color:"rgba(230,159,0,0.08)"}}},
      {name:"支撑位(聚集谷值)",type:"line",data:supData,connectNulls:false,lineStyle:{color:C.verm,width:1.6},symbol:"none",itemStyle:{color:C.verm}},
      {name:"RSI(14)",type:"line",data:CHART.rsi,showSymbol:false,lineStyle:{color:C.blue,width:1.8},itemStyle:{color:C.blue},
       markLine:{silent:true,symbol:"none",data:[{yAxis:CHART.cur_rsi,lineStyle:{color:C.sub,type:"dashed"},label:{formatter:"当前RSI "+CHART.cur_rsi.toFixed(1),color:C.sub,fontSize:10,position:"insideEndTop"}}]}},
      {name:"收盘价",type:"line",yAxisIndex:1,data:CHART.px,showSymbol:false,lineStyle:{color:"#9aa1ab",width:1,type:"dotted"},itemStyle:{color:"#9aa1ab"}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_bk"));
  var bk = CHART.bucket;
  var names = bk.map(function(x){return x.bk;});
  var t20 = bk.map(function(x){return x.t20==null?0:+x.t20.toFixed(2);});
  ch.setOption({animation:false,tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},grid:{left:50,right:20,top:30,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"T+20 收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[{name:"T+20",type:"bar",data:t20,itemStyle:{color:C.verm,opacity:0.85},label:{show:true,position:"top",fontSize:10,formatter:function(p){return bk[p.dataIndex].n+"次 "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";}},markLine:{silent:true,symbol:"none",data:[{yAxis:CHART.baseline_t20,lineStyle:{color:C.sub,type:"dashed"},label:{formatter:"基率 "+CHART.baseline_t20.toFixed(2)+"%",color:C.sub,fontSize:9}}]}}]});
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__KPI__", kpi_html)
HTML = HTML.replace("__EV_ROWS__", ev_rows_html)
HTML = HTML.replace("__BK_ROWS__", bk_rows_html)
HTML = HTML.replace("__ST_ROWS__", st_rows_html)
HTML = HTML.replace("__REF_ROWS__", ref_rows_html)
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")