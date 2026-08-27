# -*- coding: utf-8 -*-
"""
构建研报 47：MCD 单股 RSI 超卖（下穿30）买入 · 超卖程度分档
口径与 39 号完全一致（Wilder RSI14 下穿30首日，当日收盘买入，T+N 交易日）
读取 results/mcd_rsi_oversold_buckets.json
输出 reports/47_MCD_RSI超卖分档买入/index.html
静默写盘。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "47_MCD_RSI超卖分档买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "mcd_rsi_oversold_buckets.json"), encoding="utf-8") as f:
    D = json.load(f)

ea = D["events_all"]["block"]
ec = D["events_cd10"]["block"]
base = D["baseline_all_days"]
b30 = D["baseline_rsi_lt30"]
cur = D["current"]

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}%"

def pct2(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- KPI ----------
n_all = D["n_events"]["cross30_all"]
n_cd = D["n_events"]["cross30_cd10"]
KPI = [
    (str(n_all), "RSI 下穿30买入事件（31.7年）", "num"),
    (str(n_cd), "cd10 去重后独立信号", "num"),
    (pct2(ea["T20"]["mean"]), "全部事件 T+20（胜率 %d%%）" % ea["T20"]["win"], "up"),
    (pct2(ea["T20_ex_spy"]["mean"]), "全部事件 T+20 超额 vs SPY", "warn" if ea["T20_ex_spy"]["mean"] < 0 else "up"),
    (pct2(D["buckets_all"]["20-25"]["T20"]["mean"]), "20–25 档 T+20（n=%d）" % D["buckets_all"]["20-25"]["T5"]["n"], "up"),
    (pct2(D["buckets_all"]["25-30"]["T20"]["mean"]), "25–30 档 T+20（n=%d）" % D["buckets_all"]["25-30"]["T5"]["n"], "num"),
    ("%.1f" % cur["rsi"], "当前 RSI（%s）" % cur["as_of"], "num"),
    ("0 次", "RSI<20 深度超卖（1995起）", "warn"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

# ---------- 分档表 ----------
bk_order = ["<20", "20-25", "25-30"]
bk_rows = []
bk_chart = []
for bk in bk_order:
    b = D["buckets_all"][bk]
    nn = b.get("T5", {}).get("n", 0)
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    def x(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])}{tstr}</td>"
    bk_rows.append(f"<tr><td class='nowrap'><b>RSI {bk}</b></td><td>{nn}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}{x(b['T20_ex_spy'])}</tr>")
    bk_chart.append({"bk": bk, "n": nn,
                     "t5": b["T5"]["mean"] if nn else None,
                     "t10": b["T10"]["mean"] if nn else None,
                     "t20": b["T20"]["mean"] if nn else None})
bk_rows_html = "".join(bk_rows)

# ---------- 基率/对照行 ----------
def row(name, b, tag=""):
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    def x(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])}{tstr}</td>"
    cls = " class='baserow'" if tag == "base" else ""
    return (f"<tr{cls}><td class='nowrap'><b>{name}</b></td><td>{b['T5']['n']}</td>"
            f"{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}{x(b['T20_ex_spy'])}</tr>")

ref_rows_html = "".join([
    row("MCD 全历史基率（所有交易日）", base, "base"),
    row("MCD 所有 RSI<30 日（含持续低位）", b30),
    row("MCD RSI 下穿30 全部事件", ea),
    row("MCD RSI 下穿30 cd10 去重", ec),
])

# ---------- 分阶段 ----------
STAGE_CN = {"A_pre": "疫情前(1995~2020-02)", "B_post": "疫情及股灾后(2020-02~2022-12)", "C_bull": "本轮牛市(2023~)"}
st_rows = []
for st in ["A_pre", "B_post", "C_bull"]:
    b = D["events_all"]["by_stage"][st]
    def c2(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    st_rows.append(f"<tr><td class='nowrap'><b>{STAGE_CN[st]}</b></td><td>{b['T5']['n']}</td>{c2(b['T5'])}{c2(b['T10'])}{c2(b['T20'])}</tr>")
st_rows_html = "".join(st_rows)

# ---------- 事件明细（cd10 去重版为主） ----------
def f(v):
    if v is None: return "<td class='na'>—</td>"
    return f"<td class='{'up' if v>0 else 'dn'} nowrap'>{v:+.2f}%</td>"

ev_rows = []
for e in D["events_cd10_list"]:
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td>{e['rsi']}</td><td class='nowrap'>{e['px']}</td>"
        f"{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>")
ev_rows_html = "".join(ev_rows)

ev_all_rows = []
for e in D["events"]:
    ev_all_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td>{e['rsi']}</td><td class='nowrap'>{e['px']}</td>"
        f"{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>")
ev_all_rows_html = "".join(ev_all_rows)

# 最近 5 次事件（含明细中的超卖事件）
recent5 = D["events"][:5]
recent5_html = "".join(
    f"<tr><td class='nowrap'>{e['date']}</td><td>{e['rsi']}</td><td class='nowrap'>{e['px']}</td>"
    f"{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>" for e in recent5)

# ---------- 图表数据 ----------
CH = D["chart"]
dates600 = CH["dates"]
# 超卖事件散点：仅保留落在最近600日窗口内的事件，x=日期在窗口内的索引
ev_pts = []
for d, v in zip(CH["ev_dates"], CH["ev_rsi"]):
    if d in dates600:
        ev_pts.append({"i": dates600.index(d), "v": v})
CHART = {
    "bucket": bk_chart,
    "baseline_t20": base["T20"]["mean"],
    "b30_t20": b30["T20"]["mean"],
    "ev_t20": ea["T20"]["mean"],
    "rsi": CH["rsi"], "px": CH["px"], "dates": dates600,
    "ev_pts": ev_pts,
    "cur_rsi": CH["cur_rsi"],
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
<title>MCD · RSI 超卖(下穿30)买入 · 超卖程度分档</title>
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
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
  .tabs{display:flex;gap:6px;border-bottom:2px solid var(--line);margin-bottom:0;}
  .tab{padding:8px 16px;cursor:pointer;font-size:13px;color:var(--sub);border-bottom:2px solid transparent;margin-bottom:-2px;user-select:none;}
  .tab.active{color:var(--blue);border-bottom-color:var(--blue);font-weight:600;}
  .tabpanel{display:none;} .tabpanel.active{display:block;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>MCD · RSI 超卖（下穿30）买入 · 超卖程度分档</h1>
  <div class="meta">事件研究 · MCD 日线 1995-01-03 ~ 2026-08-26（7965 根K线）· 口径与 39 号报告完全一致 · 生成于 2026-08-28</div>
  <div class="callout blue">
    <b>口径（同 39 号）：</b>Wilder RSI14(adj_close) 自上下穿 30 首日（前一日 ≥30、当日 &lt;30），当日收盘买入。
    分档：RSI &lt;20（深度超卖）/ 20–25 / 25–30（轻超卖）。T+N = N 个交易日。
  </div>
  <div class="kpis">__KPI__</div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict amber"><b>① MCD 的超卖买入 edge 明显弱于蓝筹平均 —— 绝对收益有、超额为负。</b>
    82 次下穿30事件 T+5 +0.84% / T+10 +1.78% / T+20 <b>+1.83%</b>（胜率 61.0%，t=2.06），高于自身基率 +1.08%；
    但相对 SPY 超额 T+20 <b>−0.51%</b>（t=−0.81，不显著）。对比 39 号全池（72 蓝筹，T+20 +2.85%、超额 +1.16pp 显著），
    <b>MCD 的"超卖反弹"跑不赢大盘，是 β 而非 alpha</b>——与 46 号支撑买入结论完全一致。</div>
  <div class="verdict"><b>② 分档：20–25 档绝对收益强（n=4，不过 t 不显著），25–30 档几乎无 edge。</b>
    20–25 档 4 次 T+5 +5.70% / T+10 +4.37% / T+20 <b>+4.89%</b>（胜率 75%），看似最强；
    但超额 T+20 <b>−2.90%</b>（同期 SPY 涨更多），且 n=4 无统计意义。25–30 档 78 次 T+20 +1.68%（胜率 60.3%）≈ 基率。
    <b>&lt;20 档 0 次 —— MCD 31.7 年从未跌到 RSI&lt;20</b>，深度超卖这种"真 edge"位置在 MCD 身上根本不存在。</div>
  <div class="verdict gr"><b>③ 本轮牛市超卖信号完全失效：2023 以来 10 次 T+20 −0.08%。</b>
    除 2022-12 疫情后 1 次（T+20 +6.32%，样本 1）外，2023 年起的 10 次下穿30买入 T+20 平均 <b>−0.08%</b>（胜率仅 60%），
    最近一次 2026-05-08（RSI 25.2）T+20 也仅 +1.42%。圣杯（&lt;30 买即赚）在 MCD 上近四年不成立。</div>
  <div class="verdict gr"><b>④ 当前状态：RSI 44.4，非超卖，不触发。</b>
    2026-08-26 收盘 266.93。38.1 RSI 距 30 尚有 14.4 点，按 39 号口径无任何买入信号；若未来 RSI 下穿 30，历史最有参考价值的档位是 20–25（2005 年两次 +8%+、1998 一次），但样本太少不足以构成可交易依据。</div>
</div>

<div class="card">
  <h2>一、超卖程度分档（核心）</h2>
  <div class="chart" id="ch_bk"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>档位</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th><th>超额T+20</th></tr></thead>
    <tbody>__BK_ROWS__</tbody>
  </table>
  </div>
  <div class="src">&lt;20 档 MCD 从未触及（0/82）；20–25 档 n=4 绝对收益最高但超额为负、无统计意义；25–30 档（占 95%）T+20 +1.68% ≈ 基率，edge 可忽略。虚线为 MCD 全历史基率 T+20 +1.08%。</div>
</div>

<div class="card">
  <h2>二、基率 / 对照 / 分阶段</h2>
  <div class="scroll">
  <table>
    <thead><tr><th>口径</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th><th>超额T+20</th></tr></thead>
    <tbody>__REF_ROWS__</tbody>
  </table>
  </div>
  <div class="grid2" style="margin-top:14px">
    <div>
      <h3>分阶段（T+20）</h3>
      <div class="scroll"><table>
        <thead><tr><th>阶段</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__ST_ROWS__</tbody>
      </table></div>
    </div>
    <div>
      <h3>最近 5 次超卖信号</h3>
      <div class="scroll"><table>
        <thead><tr><th>日期</th><th>RSI</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__RECENT5__</tbody>
      </table></div>
    </div>
  </div>
  <div class="src">"所有 RSI&lt;30 日"（226 日，含持续低位）T+20 +2.53% 显著，说明 MCD 躺在低位本身有价值；但"下穿当天才买"（82 次事件）T+20 +1.83% 且超额为负——入场时点没有挑出更好的位置。本轮牛市（2023~）10 次事件 T+20 −0.08%，超卖策略在 MCD 近四年失效。</div>
</div>

<div class="card">
  <h2>三、近 600 交易日 RSI 与超卖事件</h2>
  <div class="chart" id="ch_rsi"></div>
  <div class="src">橙点为 RSI 下穿30买入事件（共 82 次中落在近600日的部分）；蓝线 RSI、灰线收盘价、虚线 RSI=30 超卖线。当前 RSI 44.4 明显高于超卖线。</div>
</div>

<div class="card">
  <div class="tabs">
    <div class="tab active" data-tab="tab1" onclick="switchTab(this)">结论与图表</div>
    <div class="tab" data-tab="tab2" onclick="switchTab(this)">cd10 去重事件明细（__EVN__ 条）</div>
    <div class="tab" data-tab="tab3" onclick="switchTab(this)">全部事件明细（__EVNALL__ 条）</div>
  </div>
  <div class="tabpanel active" id="tab1">
    <p style="font-size:13px;color:var(--sub);padding:8px 0">cd10 = 同票 10 个交易日内只保留首个下穿信号，消除连续低位重复计数；主口径为全部 82 次。</p>
  </div>
  <div class="tabpanel" id="tab2">
    <div class="evbox">
      <table>
        <thead><tr><th>日期</th><th>RSI</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__EV_ROWS__</tbody>
      </table>
    </div>
  </div>
  <div class="tabpanel" id="tab3">
    <div class="evbox">
      <table>
        <thead><tr><th>日期</th><th>RSI</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__EVALL_ROWS__</tbody>
      </table>
    </div>
  </div>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close）· 方法：与 39 号完全同口径（RSI14 下穿30首日）· 脚本：scripts/mcd_rsi_oversold_buckets.py + build_mcd_rsi_oversold_buckets_report.py · 数据文件：results/mcd_rsi_oversold_buckets.json。
  <b>本报告仅为统计回测，不构成投资建议。</b></div>
</div>

</div>
<script>
var CHART = __DATA_JSON__;
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
function switchTab(el){
  document.querySelectorAll(".tab").forEach(function(t){t.classList.remove("active");});
  document.querySelectorAll(".tabpanel").forEach(function(p){p.classList.remove("active");});
  el.classList.add("active");
  document.getElementById(el.dataset.tab).classList.add("active");
}
(function(){
  var ch = echarts.init(document.getElementById("ch_bk"));
  var bk = CHART.bucket;
  var names = bk.map(function(x){return x.bk;});
  var t5 = bk.map(function(x){return x.t5==null?0:+x.t5.toFixed(2);});
  var t10 = bk.map(function(x){return x.t10==null?0:+x.t10.toFixed(2);});
  var t20 = bk.map(function(x){return x.t20==null?0:+x.t20.toFixed(2);});
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:13,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.dataIndex===0?"n=0":p.value.toFixed(2);}}},
      {name:"T+10",type:"bar",barWidth:13,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.dataIndex===0?"n=0":p.value.toFixed(2);}}},
      {name:"T+20",type:"bar",barWidth:13,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.dataIndex===0?"n=0":p.value.toFixed(2);}}},
      {name:"基率T+20",type:"line",data:[CHART.baseline_t20,CHART.baseline_t20,CHART.baseline_t20],lineStyle:{type:"dashed",color:C.sub,width:1.2},symbol:"none",label:{show:true,position:"bottom",formatter:"基率 "+CHART.baseline_t20.toFixed(2)+"%",fontSize:9,color:C.sub}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_rsi"));
  var n = CHART.dates.length;
  ch.setOption({
    animation:false,
    legend:{data:["RSI(14)","超卖事件","收盘价"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"cross"},formatter:function(ps){
      var i = ps[0].dataIndex;
      var h = "<b>"+CHART.dates[i]+"</b>";
      ps.forEach(function(p){h += "<br>"+p.marker+p.seriesName+": "+p.value;});
      return h;}},
    grid:{left:55,right:60,top:45,bottom:30},
    xAxis:{type:"category",data:CHART.dates,axisLabel:{show:false}},
    yAxis:[
      {type:"value",name:"RSI",min:0,max:100,axisLabel:{color:"#4b5563",fontSize:11},splitLine:{lineStyle:{color:"#eef0f3"}}},
      {type:"value",name:"价格($)",scale:true,axisLabel:{color:"#9aa1ab",fontSize:11},splitLine:{show:false},splitNumber:4}
    ],
    series:[
      {name:"RSI(14)",type:"line",data:CHART.rsi,showSymbol:false,lineStyle:{color:C.blue,width:1.8},itemStyle:{color:C.blue},
       markLine:{silent:true,symbol:"none",data:[{yAxis:30,lineStyle:{color:C.verm,type:"dashed"},label:{formatter:"RSI=30",color:C.verm,fontSize:10,position:"insideEndTop"}},{yAxis:CHART.cur_rsi,lineStyle:{color:C.sub,type:"dotted"},label:{formatter:"当前 "+CHART.cur_rsi.toFixed(1),color:C.sub,fontSize:10,position:"insideEndBottom"}}]}},
      {name:"超卖事件",type:"scatter",data:CHART.ev_pts.map(function(p){return [p.i, p.v];}),symbol:"diamond",symbolSize:7,itemStyle:{color:C.orange}},
      {name:"收盘价",type:"line",yAxisIndex:1,data:CHART.px,showSymbol:false,lineStyle:{color:"#9aa1ab",width:1,type:"dotted"},itemStyle:{color:"#9aa1ab"}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__KPI__", kpi_html)
HTML = HTML.replace("__BK_ROWS__", bk_rows_html)
HTML = HTML.replace("__REF_ROWS__", ref_rows_html)
HTML = HTML.replace("__ST_ROWS__", st_rows_html)
HTML = HTML.replace("__RECENT5__", recent5_html)
HTML = HTML.replace("__EV_ROWS__", ev_rows_html)
HTML = HTML.replace("__EVALL_ROWS__", ev_all_rows_html)
HTML = HTML.replace("__EVN__", str(len(D["events_cd10_list"])))
HTML = HTML.replace("__EVNALL__", str(len(D["events"])))
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")