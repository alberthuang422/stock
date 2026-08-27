# -*- coding: utf-8 -*-
"""
构建研报 47（v2）：MCD 单股 RSI 低位（下穿40）买入 · RSI 分档 <30 / 30-35 / 35-40
口径：39 号下穿30 扩展为下穿40（覆盖整个低位区间），当日收盘买入，T+N 交易日
读取 results/mcd_rsi_oversold_buckets.json
输出 reports/47_MCD_RSI低位分档买入/index.html
静默写盘。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "47_MCD_RSI低位分档买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "mcd_rsi_oversold_buckets.json"), encoding="utf-8") as f:
    D = json.load(f)

ea = D["events_all"]["block"]
ec = D["events_cd10"]["block"]
base = D["baseline_all_days"]
b30 = D["baseline_lt30"]
b40 = D["baseline_lt40"]
cur = D["current"]

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}%"

def pct2(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- KPI ----------
n_all = D["n_events"]["cross40_all"]
n_cd = D["n_events"]["cross40_cd10"]
KPI = [
    (str(n_all), "RSI 下穿40 买入事件（31.7年）", "num"),
    (str(n_cd), "cd10 去重后独立信号", "num"),
    (pct2(ea["T20"]["mean"]), "全部事件 T+20（胜率 %d%%）" % ea["T20"]["win"], "num"),
    (pct2(ea["T20_ex_spy"]["mean"]), "全部事件 T+20 超额 vs SPY", "warn" if ea["T20_ex_spy"]["mean"] < 0 else "up"),
    (pct2(D["buckets_all"]["<30"]["T20"]["mean"]), "<30 档 T+20（n=%d，暴跌日为主）" % D["buckets_all"]["<30"]["T5"]["n"], "dn"),
    (pct2(D["buckets_all"]["30-35"]["T20"]["mean"]), "30–35 档 T+20（n=%d）" % D["buckets_all"]["30-35"]["T5"]["n"], "num"),
    (pct2(b30["T20"]["mean"]), "所有 RSI<30 日 T+20（n=%d）" % b30["T5"]["n"], "up"),
    ("%.1f" % cur["rsi"], "当前 RSI（%s）" % cur["as_of"], "num"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

# ---------- 分档表（下穿事件 + 同档所有日对照） ----------
bk_order = ["<30", "30-35", "35-40"]
bk_rows = []
bk_chart = []
for bk in bk_order:
    b = D["buckets_all"][bk]
    bl = D["baseline_buckets"][bk]
    nn = b.get("T5", {}).get("n", 0)
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    def x(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])}{tstr}</td>"
    def lcell(blk):
        n_ = blk.get("T5", {}).get("n", 0)
        if not n_: return "<td class='na'>—</td>"
        t = blk.get("T20", {}).get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        cls = "up" if blk["T20"]["mean"] > 0 else "dn"
        return f"<td class='{cls} nowrap'>{pct(blk['T20']['mean'])} <span class='note2'>(n={n_})</span>{tstr}</td>"
    bk_rows.append(f"<tr><td class='nowrap'><b>RSI {bk}</b></td><td>{nn}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}{x(b['T20_ex_spy'])}{lcell(bl)}</tr>")
    bk_chart.append({"bk": bk, "n": nn,
                     "t5": b["T5"]["mean"] if nn else None,
                     "t10": b["T10"]["mean"] if nn else None,
                     "t20": b["T20"]["mean"] if nn else None,
                     "lvl20": bl["T20"]["mean"]})
bk_rows_html = "".join(bk_rows)

# 分档注：同档所有日对照存到一个单独说明行
BKU_NOTE = ("「同档所有日 T+20」= 该 RSI 区间内任意一天（不限下穿日）的未来20日收益，衡量「身处该低位状态」的价值；"
            "对比「下穿当天买入」可判断入场时点是否提供额外信息。")

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
    row("MCD 所有 RSI<40 日（含持续低位）", b40),
    row("MCD RSI 下穿40 全部事件", ea),
    row("MCD RSI 下穿40 cd10 去重", ec),
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

# ---------- 事件明细 ----------
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

recent5_html = "".join(
    f"<tr><td class='nowrap'>{e['date']}</td><td>{e['rsi']}</td><td class='nowrap'>{e['px']}</td>"
    f"{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>" for e in D["events_cd10_list"][:5])

# ---------- 图表数据 ----------
CH = D["chart"]
dates600 = CH["dates"]
ev_pts = []
for d, v in zip(CH["ev_dates"], CH["ev_rsi"]):
    if d in dates600:
        ev_pts.append({"i": dates600.index(d), "v": v})

CHART = {
    "bucket": [{"bk": x["bk"], "n": x["n"], "t5": x["t5"], "t10": x["t10"], "t20": x["t20"], "lvl20": x["lvl20"]} for x in bk_chart],
    "baseline_t20": base["T20"]["mean"],
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
<title>MCD · RSI 低位（下穿40）买入 · RSI 分档</title>
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
  <h1>MCD · RSI 低位（下穿40）买入 · RSI 分档</h1>
  <div class="meta">事件研究 · MCD 日线 1995-01-03 ~ 2026-08-26（7965 根K线）· 39 号口径扩展至下穿40 · 生成于 2026-08-28</div>
  <div class="callout blue">
    <b>口径：</b>Wilder RSI14(adj_close) <b>自上下穿 40 首日</b>（前一日 ≥40、当日 &lt;40），当日收盘买入，覆盖整个 RSI 低位区间。
    分档：RSI &lt;30（超卖）/ 30–35 / 35–40（偏低回调）。T+N = N 个交易日。cd10 = 同票 10 交易日去重。
  </div>
  <div class="kpis">__KPI__</div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict amber"><b>① 把门槛从 30 放宽到 40，edge 反而更弱 —— 阈值越宽，信号越被稀释。</b>
    下穿40 事件 258 次，T+20 <b>+0.89%</b>（胜率 60.1%）<b>低于</b> MCD 全历史基率 +1.08%（t=2.24 但幅度无意义），超额 vs SPY <b>−0.32%</b>（t=−0.92）。
    对比收紧到 30 时（47 号 v1 / 39 号口径：82 次，T+20 +1.83%），放宽阈值后绝对收益从 +1.83% 掉到 +0.89%——大部分新纳入的"轻回调"信号没有 edge。</div>
  <div class="verdict"><b>② 分档看：35–40 档（占 87%）无 edge，30–35 档勉强为正，&lt;30 档样本全是"暴跌日"不可靠。</b>
    35–40 档 225 次 T+20 <b>+1.00%</b> ≈ 基率；30–35 档 28 次 +1.20%（t=1.01，不显著）。
    &lt;30 档仅 5 次 T+20 <b>−5.65%</b>（超额 −3.73%，t=−2.16）——但这 5 次是<b>单日从 40 上方直接砸穿 30 的极端暴跌日</b>（2020-02-27 疫情 −16.2%、2000-01-26 −12.2%、2002-09-17 −4.5%、2015-08-24 +5.6%），
    本质是"暴跌当天抄底"策略的惨案，n=5 不能外推。</div>
  <div class="verdict gr"><b>③ 关键对比："身处低位"有价值，"下穿当天买"没有 —— 时点选择没提供信息。</b>
    所有 RSI&lt;30 的日子（226 天，不限下穿）T+20 <b>+2.53%</b>（t=4.99）、30–35 区间（320 天）+2.10%（t=5.33）显著为正；
    但"下穿 40 当天才买"只有 +0.89%。<b>躺在低位本身就是正期望（均值回归），而下穿事件当天并不比随便哪天更好。</b>
    39 号全池 72 蓝筹下穿30 有真 edge（+2.85%、超额 +1.16pp 显著），MCD 连这条都没有——个股层面该策略不成立。</div>
  <div class="verdict"><b>④ 本轮牛市依旧失效：2023 以来 43 次 T+20 −0.48%；当前 RSI 44.4 未进任何低位档。</b>
    近四年 MCD 的 RSI 低位买入整体负收益，与 47 号 v1（下穿30 口径）结论一致。当前 08-26 收盘 266.93、RSI 44.4，距 40 尚有 4.4 点。</div>
</div>

<div class="card">
  <h2>一、RSI 低位分档（下穿40 事件）</h2>
  <div class="chart" id="ch_bk"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>档位</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th><th>超额T+20</th><th>同档所有日 T+20</th></tr></thead>
    <tbody>__BK_ROWS__</tbody>
  </table>
  </div>
  <div class="src">__BKU_NOTE__<br>下穿40当天买入 vs 同档所有日：<30 档 5 次全为单日暴跌穿40的极端日（拖累为负）；30–35、35–40 档下穿当天收益与"躺在那"并无显著差别——时点无信息。</div>
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
      <h3>分阶段（下穿40 事件）</h3>
      <div class="scroll"><table>
        <thead><tr><th>阶段</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__ST_ROWS__</tbody>
      </table></div>
    </div>
    <div>
      <h3>最近 5 次独立信号（cd10）</h3>
      <div class="scroll"><table>
        <thead><tr><th>日期</th><th>RSI</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__RECENT5__</tbody>
      </table></div>
    </div>
  </div>
  <div class="src">所有 RSI&lt;40 日（1100 天）T+20 +1.87%（t=9.04）显著——低位状态本身有均值回归价值；但把它变成"下穿当天买入"的择时信号后，超额归零甚至为负。本轮牛市 43 次事件 T+20 −0.48%。</div>
</div>

<div class="card">
  <h2>三、近 600 交易日 RSI 与低位信号</h2>
  <div class="chart" id="ch_rsi"></div>
  <div class="src">橙点为 RSI 下穿40 买入事件落在近600日的部分；蓝线 RSI、灰线收盘价、虚线 RSI=40 / 30 分档线。当前 RSI 44.4 高于 40。</div>
</div>

<div class="card">
  <div class="tabs">
    <div class="tab active" data-tab="tab1" onclick="switchTab(this)">结论与图表</div>
    <div class="tab" data-tab="tab2" onclick="switchTab(this)">cd10 去重事件明细（__EVN__ 条）</div>
    <div class="tab" data-tab="tab3" onclick="switchTab(this)">全部事件明细（__EVNALL__ 条）</div>
  </div>
  <div class="tabpanel active" id="tab1">
    <p style="font-size:13px;color:var(--sub);padding:8px 0">cd10 = 同票 10 个交易日内只保留首个下穿信号；主口径为全部 258 次。</p>
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
  <div class="src">数据：Yahoo Finance（adj_close）· 方法：39 号 RSI 下穿口径扩展至 40 · 脚本：scripts/mcd_rsi_oversold_buckets.py + build_mcd_rsi_oversold_buckets_report.py · 数据文件：results/mcd_rsi_oversold_buckets.json。
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
  var lvl = bk.map(function(x){return x.lvl20==null?null:+x.lvl20.toFixed(2);});
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20","同档所有日 T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){if(p.value==null)return;h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:11,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.dataIndex===0?"n=5":p.value.toFixed(2);}}},
      {name:"T+10",type:"bar",barWidth:11,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.dataIndex===0?"n=5":p.value.toFixed(2);}}},
      {name:"T+20",type:"bar",barWidth:11,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.dataIndex===0?"n=5":p.value.toFixed(2);}}},
      {name:"同档所有日 T+20",type:"scatter",data:lvl,symbol:"diamond",symbolSize:9,itemStyle:{color:C.orange},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value==null?"":p.value.toFixed(2)+"%";}}},
      {name:"基率T+20",type:"line",data:[CHART.baseline_t20,CHART.baseline_t20,CHART.baseline_t20],lineStyle:{type:"dashed",color:C.sub,width:1.2},symbol:"none",label:{show:true,position:"bottom",formatter:"基率 "+CHART.baseline_t20.toFixed(2)+"%",fontSize:9,color:C.sub}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_rsi"));
  ch.setOption({
    animation:false,
    legend:{data:["RSI(14)","低位信号(下穿40)","收盘价"],top:2,textStyle:{fontSize:11,color:"#374151"}},
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
       markLine:{silent:true,symbol:"none",data:[{yAxis:40,lineStyle:{color:C.sub,type:"dashed"},label:{formatter:"RSI=40",color:C.sub,fontSize:10,position:"insideEndTop"}},{yAxis:30,lineStyle:{color:C.verm,type:"dashed"},label:{formatter:"RSI=30",color:C.verm,fontSize:10,position:"insideEndTop"}},{yAxis:CHART.cur_rsi,lineStyle:{color:"#9aa1ab",type:"dotted"},label:{formatter:"当前 "+CHART.cur_rsi.toFixed(1),color:"#9aa1ab",fontSize:10,position:"insideEndBottom"}}]}},
      {name:"低位信号(下穿40)",type:"scatter",data:CHART.ev_pts.map(function(p){return [p.i, p.v];}),symbol:"diamond",symbolSize:7,itemStyle:{color:C.orange}},
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
HTML = HTML.replace("__BKU_NOTE__", BKU_NOTE)
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