# -*- coding: utf-8 -*-
"""
CCL RSI 区间跌落买入（阶梯式越跌越买）报告 —— 复刻 49 号 MCD 格式
读取 results/ccl_rsi_band_dip.json
输出 reports/56_CCL_RSI档位买入/index.html（覆盖状态式版）
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "56_CCL_RSI档位买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "ccl_rsi_band_dip.json"), encoding="utf-8") as f:
    D = json.load(f)

BK_ORDER = ["35-40", "30-35", "<30"]
WINS = (5, 10, 20)


def pct(v, nd=2):
    return "—" if v is None else f"{v:+.2f}%"


def fcell(v, pctf=True):
    if v is None:
        return "<td class='na'>—</td>"
    cls = "up" if v > 0 else "dn"
    s = f"{v:+.2f}%" if pctf else f"{v:.2f}"
    return f"<td class='{cls} nowrap'>{s}</td>"


# ---------- 表1 三档主表（中位） ----------
rows1 = []
chart_band = []
for bk in BK_ORDER:
    s = D["by_band"][bk]
    n = s["fwd20"]["n"]
    row = (f"<tr><td class='nowrap'><b>RSI {bk}</b></td><td>{n}</td>"
           f"{fcell(s['maxg20']['median'])}{fcell(s['fwd20']['median'])}"
           f"<td class='nowrap'>{s['er20']['median']:.2f}</td>"
           f"<td class='nowrap'>{s['win20']}%</td>"
           f"<td class='nowrap'>{s['ever_positive']}%</td>"
           f"{fcell(s['ex20']['median'])}</tr>")
    rows1.append(row)
    chart_band.append({"bk": bk, "n": n,
                       "maxg": round(s["maxg20"]["median"], 2),
                       "fwd": round(s["fwd20"]["median"], 2),
                       "er": round(s["er20"]["median"], 3),
                       "ex": round(s["ex20"]["median"], 2),
                       "win": s["win20"]})

# ---------- 表2 全量 vs cd10 ----------
rows2 = []
chart_cd10 = []
for bk in BK_ORDER:
    a = D["by_band"][bk]
    b = D["by_band_cd10"][bk]
    row = (f"<tr><td class='nowrap'><b>RSI {bk}</b></td>"
           f"<td>{a['fwd20']['n']}</td>{fcell(a['fwd20']['median'])}<td class='nowrap'>{a['win20']}%</td>{fcell(a['ex20']['median'])}"
           f"<td>{b['fwd20']['n']}</td>{fcell(b['fwd20']['median'])}<td class='nowrap'>{b['win20']}%</td>{fcell(b['ex20']['median'])}</tr>")
    rows2.append(row)
    chart_cd10.append({"bk": bk,
                       "all_fwd": a["fwd20"]["median"], "cd10_fwd": b["fwd20"]["median"],
                       "all_win": a["win20"], "cd10_win": b["win20"],
                       "all_ex": a["ex20"]["median"], "cd10_ex": b["ex20"]["median"]})

# ---------- 表3 阶段×档（fwd20 med） ----------
rows3 = []
for stg in ["疫情前", "疫情~2022", "本轮牛市"]:
    sb = D["stage_band"][stg]
    cells = ""
    for bk in BK_ORDER:
        s = sb[bk]
        n = s["fwd20"]["n"]
        if n == 0:
            cells += "<td class='na'>—</td>"
        else:
            v = s["fwd20"]["median"]
            cls = "up" if v > 0 else "dn"
            cells += f"<td class='{cls} nowrap'>{v:+.2f}%<span class='note2'> (n={n})</span></td>"
    rows3.append(f"<tr><td class='nowrap'><b>{stg}</b></td>{cells}</tr>")

# ---------- 表4 最近5次（三窗口 最大/最终/ER） ----------
def _g(v):
    if v is None:
        return "<td class='na'>—</td>"
    cls = "up" if v > 0 else "dn"
    return f"<td class='{cls} nowrap'>{v:+.2f}%</td>"


def _g2(v):
    if v is None:
        return "<td class='na'>—</td>"
    return f"<td class='nowrap'>{v:.2f}</td>"


def wrow(e):
    cells = "".join(_g(e.get(f"maxg{NN}")) + _g(e.get(f"fwd{NN}")) + _g2(e.get(f"er{NN}")) for NN in WINS)
    return f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'>{e['band']}</td><td>{e['rsi']}</td>{cells}</tr>"


def all_whead():
    th = "<tr><th rowspan='2'>日期</th><th rowspan='2'>档位</th><th rowspan='2'>RSI</th>"
    for NN in WINS:
        th += f"<th colspan='3' class='grph'>{NN}日窗口<br>最大 / 最终 / ER</th>"
    th += "<th rowspan='2' class='grph'>超额<br>T+20</th></tr><tr>"
    for _ in WINS:
        th += "<th>最大</th><th>最终</th><th>ER</th>"
    th += "</tr>"
    return th


def all_wrow(e):
    cells = "".join(_g(e.get(f"maxg{NN}")) + _g(e.get(f"fwd{NN}")) + _g2(e.get(f"er{NN}")) for NN in WINS)
    return f"<tr data-band='{e['band']}'><td class='nowrap'>{e['date']}</td><td class='nowrap'>{e['band']}</td><td>{e['rsi']}</td>{cells}{_g(e.get('ex'))}</tr>"


def whead():
    th = "<tr><th rowspan='2'>日期</th><th rowspan='2'>档位</th><th rowspan='2'>RSI</th>"
    for NN in WINS:
        th += f"<th colspan='3' class='grph'>{NN}日窗口<br>最大 / 最终 / ER</th>"
    th += "</tr><tr>"
    for _ in WINS:
        th += "<th>最大</th><th>最终</th><th>ER</th>"
    th += "</tr>"
    return th


recent_html = "".join(wrow(e) for e in D["recent"])
all_events_html = "".join(all_wrow(e) for e in sorted(D["events"], key=lambda x: x["date"], reverse=True))
all_head_html = all_whead()

# ---------- 表5 年份分布 ----------
chart_year = D["year_dist"]

CHART = {"band": chart_band, "cd10": chart_cd10, "year": chart_year,
         "n_total": D["n_total"], "n_cd10": D["n_cd10"],
         "base_fwd": D["base"]["fwd"]["median"], "base_maxg": D["base"]["maxg"]["median"]}

echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CCL · RSI 区间跌落买入（越跌越买阶梯式）</title>
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
  th.grph{text-align:center;border-left:1px solid #dbe4ef;border-right:1px solid #dbe4ef;background:#eaf1fa;color:#374151;font-weight:700;font-size:11.5px;}
  tr.baserow td{background:#fbf7ee;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .callout{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}
  .callout.blue{border-color:#cfe0f5;background:#f0f6fd;}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
  .tabbar{display:flex;gap:4px;margin-bottom:16px;border-bottom:1px solid var(--line);}
  .tabbar button{background:transparent;border:none;border-bottom:3px solid transparent;padding:9px 18px;font-size:13.5px;color:var(--sub);cursor:pointer;}
  .tabbar button:hover{color:var(--ink);}
  .tabbar button.on{color:var(--ink);border-bottom-color:var(--verm);font-weight:600;}
  .pane{display:none;}
  .pane.on{display:block;}
  tr.grprow td{background:#eef3fa;color:#4b5563;font-weight:700;text-align:center;font-size:11px;padding:4px;}
  .filterbar{display:flex;align-items:center;gap:10px;margin:4px 0 10px;flex-wrap:wrap;}
  .filter-label{font-size:12.5px;color:#4b5563;font-weight:600;}
  .filterbar select{padding:5px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12.5px;background:#fff;color:var(--ink);cursor:pointer;}
  .filterbar select:focus{outline:none;border-color:var(--blue);}
  .filter-note{font-size:12px;color:var(--sub);}
</style>
</head>
<body>
<div class="wrap">
<div class="tabbar">
  <button class="on" onclick="showTab('pane_main',this)">报告正文</button>
  <button onclick="showTab('pane_events',this)">事件明细（__N_TOTAL__）</button>
</div>
<div class="pane on" id="pane_main">

<div class="card">
  <h1>CCL · RSI 区间跌落买入（越跌越买阶梯式）</h1>
  <div class="meta">事件口径：当日收盘 RSI 档位比前日更低位 → 当日收盘买入 · 三档：35-40 / 30-35 / &lt;30（40 以上不买）· 每次跨区间独立统计 · 主口径无去重（474 事件）+ cd10 对照（203）· SPY 同窗口对照 · 2026-08-29（数据至 08-27）</div>
  <div class="callout blue">
    <b>与 56 号状态式版 / 47-50 号的区别：</b>状态式版统计"RSI 处于某档的所有日子"；本报告改为<b>越跌越买</b>——只要收盘 RSI 从高区间跌入更低区间就买一次（例：36 跌入 35-40 买第 1 次、次日 25 跌入 &lt;30 买第 2 次），
    每次买入独立统计 T+5/T+10/T+20 窗口。回答：<b>把每次跌入更低档都当成买入机会，CCL 的收益结构如何？（当前 RSI 35.44 落在 35-40 档）</b>
  </div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="callout amber">
    <b>为什么 30-35 档最差？—— CCL 高波动下 RSI 30-35 是"下跌中段"而非"超卖"。</b>
    证据（本报告口径）：① 30-35 档触发后 20 日内有 <b>51% 概率继续跌破 RSI 30</b>（35-40 档仅 30%），
    这 74 次"接飞刀" fwd20 中位 <b>−5.51%</b>、胜率仅 26%，而止跌的 72 次 +4.27%/74%——档内一半接飞刀、一半反弹，抵消后归零；
    ② CCL 日波动 σ 2.9%（年化 46%）= SPY 的 2.4 倍、MCD 的 2 倍——同样 RSI 30-35，对低波动 MCD（σ1.5%）是历史级超卖（49 号 +2.17% 最好），
    对高波动 CCL 只是普通回调中继，下跌动能未尽；
    ③ 触发时距 60 日高点回撤 −16.8%（35-40 档 −15.0% / &lt;30 档 −21.5%），前 10 日累计跌 −7.3%——正好卡在"跌了一半"的位置，
    <b>跌透（&lt;30，回撤 −21.5%）才有均值回归，半山腰（30-35）买入是在接下跌动能</b>。
  </div>
  <div class="verdict gr"><b>① 与 MCD 不同，CCL 的"越跌越买"只在 &lt;30 档有效：三档收益不单调。</b>
    474 次买入三档 fwd20 中位 35-40 +1.41% / 30-35 <b class="dn">−0.18%</b> / &lt;30 <b>+3.70%</b>——
    30-35 档是中段（下跌未到底、接飞刀风险区），跌穿 30 才是 CCL 真正的低位买点（胜率 64.6%、曾解套率 96.2%）。</div>
  <div class="verdict"><b>② 超额只有 &lt;30 档为正：CCL 是"超卖才跑赢大盘"的标的。</b>
    三档超额中位 −0.13 / −0.33 / <b>+1.50pp</b>——35-40、30-35 两档绝对收益≈基率甚至跑输；
    <b>&lt;30 档超额 +1.50pp 与 MCD（−1.32pp）正好相反</b>：CCL 高 β 弹性股，超卖反弹时 SPY 追不上它。</div>
  <div class="verdict amber"><b>③ cd10 去重后 &lt;30 档质量进一步凸显：13 次、胜率 84.6%、超额 +2.73pp。</b>
    同一波下跌只买首档触发后，&lt;30 档 cd10 13 次 fwd 中位 +4.46%、胜率 64.6%→84.6%、超额 +1.50→+2.73pp；
    而 35-40 档去重后超额从 −0.13 微升 +0.20pp（n=150）——<b>浅跌档位无 edge，深跌（&lt;30）首档触发才是质量最高的买入</b>。</div>
  <div class="verdict"><b>④ 本轮牛市：35-40 / 30-35 档失效（超额 −3.7~−4.2pp），&lt;30 档一枝独秀（+11.49%、超额 +5.71pp）。</b>
    2023 以来 35-40 档 fwd 中位 −3.00%、30-35 档 −3.50%，"RSI 35-40 就买"在当下环境持续亏钱；
    &lt;30 档 13 次 +11.49%——2026 年的 CCL 只有跌透（&lt;30）才有行情，浅回调不构成买点。</div>
  <div class="verdict"><b>⑤ 当前 RSI 35.44（35-40 档）：历史该档 T+20 +1.41% 但超额 −0.13pp、本轮牛市 −3.70pp——不是 CCL 的买点。</b>
    2026 年最近 5 次 35-40/30-35 档触发，T+20 超额 −2.4~+24.2pp 高度分化（5/19 +24.2pp 是趋势启动、7/23 −2.39pp 是反弹失败）；
    当前价跌破全部均线、YTD −18%，与 47/50 号同源结论一致：<b>浅跌档位无信息，等 &lt;30 档 + 企稳确认</b>。</div>
</div>

<div class="card">
  <h2>一、三档收益 vs 基率（474 次，T+20 中位）</h2>
  <div class="chart" id="ch_band"></div>
  <p class="src" style="margin-top:2px">柱 = maxG / fwd（中位，左轴）；点 = ER（右轴）。基率（全部重叠 20 日窗口）：CCL fwd 中位 +0.72%、maxG +4.90%、SPY fwd +1.34%。</p>
  <div class="scroll" style="margin-top:8px">
  <table>
    <thead><tr><th>档位</th><th>n</th><th>maxG20 中位</th><th>fwd20 中位</th><th>ER20 中位</th><th>胜率 T+20</th><th>曾解套率</th><th>超额20 中位</th></tr></thead>
    <tbody>__ROWS1__</tbody>
  </table>
  </div>
  <p class="src">三档收益<b>不随档位单调</b>：30-35 档 fwd 中位转负（−0.18%）、maxG 也最低（+4.95%）——CCL 的 30-35 是"没跌透"的中段陷阱；
  &lt;30 档 maxG +6.46%、胜率 64.6%、超额 +1.50pp 全档最强。基率 ER 0.21，三档 ER 0.18~0.23 无显著差异（反弹流畅度不随深度变化）。</p>
</div>

<div class="card">
  <h2>二、连续加仓是否有效：全量 vs cd10 去重对照</h2>
  <div class="grid2">
    <div class="chart" id="ch_cd10" style="height:340px"></div>
    <div class="scroll"><table>
      <thead><tr><th rowspan='2'>档位</th><th colspan='3' class='grph'>全量（连续加仓）</th><th colspan='3' class='grph'>cd10 去重（首档触发）</th></tr>
      <tr><th>n</th><th>fwd20 中位</th><th>胜率</th><th>n</th><th>fwd20 中位</th><th>胜率</th></tr></thead>
      <tbody>__ROWS2__</tbody>
    </table></div>
  </div>
  <p class="src" style="margin-top:8px">去重逻辑：事件日相隔 ≥10 交易日（同一波下跌只保留第一次触发）。<b>&lt;30 档去重后胜率 64.6%→84.6%、超额 +1.50→+2.73pp</b>——同一波暴跌中只在首次跌穿 30 时买、后续加仓纯稀释；
  35-40 档去重后超额 −0.13→+0.20pp（浅跌档"首档触发"略好但仍≈0）；30-35 档去重后反而更差（−0.33→−1.91pp，n=40 且多为暴跌中继）。</p>
</div>

<div class="card">
  <h2>三、分阶段 × 档位（fwd20 中位）</h2>
  <div class="scroll"><table>
    <thead><tr><th>阶段</th><th>RSI 35-40</th><th>RSI 30-35</th><th>RSI &lt;30</th></tr></thead>
    <tbody>__ROWS3__</tbody>
  </table></div>
  <p class="src">疫情前：三档全正（+0.28~+2.34%），CCL 低位买入普适有效；疫情~2022：35-40 档 +7.78%（V 型反弹）、30-35 档 −7.65%（疫情二次探底接飞刀）；
  本轮牛市：<b>35-40 / 30-35 档超额 −3.7~−4.2pp 失效、&lt;30 档 +11.49%/超额 +5.71pp 是唯一有效买点</b>——2023 以来 CCL 的高波动结构决定了"必须跌透才有行情"。</p>
</div>

<div class="card">
  <h2>四、事件年份分布 + 最近 5 次买入</h2>
  <div class="chart" id="ch_year" style="height:240px"></div>
  <p class="src">事件集中在波动大年（2008 年 31 次峰值、2022 年 26 次）；2017 年仅 4 次（单边牛市 RSI 极少破 40）；2026 年至今 9 次。</p>
  <h3 style="margin-top:14px">最近 5 次买入（三窗口 最大涨幅 / 最终收益 / ER）</h3>
  <div class="scroll"><table>
    <thead>__RECENT_HEAD__</thead>
    <tbody>__RECENT_ROWS__</tbody>
  </table></div>
  <p class="src">例：2026-05-19（35-40 档）T+20 +25.20%、超额 +24.21pp（趋势启动期强反弹）；2026-07-23（35-40 档）T+5 冲到 +9.89% 但 T+20 只剩 +0.92%、ER 0.02（冲高回落典型）——浅跌档结果高度分化，取决于是否踩中趋势启动。</p>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close，2000-01-03 ~ 2026-08-27）· 脚本：scripts/ccl_rsi_band_dip.py + build_ccl_rsi_band_dip_report.py · 数据文件：results/ccl_rsi_band_dip.json。
  主口径无 cd10 去重（连续加仓为设计意图，窗口重叠 → 独立性与显著性为上限，本报告数字为描述性统计）。
  <b>本报告仅为统计回测，不构成投资建议。</b></div>
</div>

</div>

<div class="pane" id="pane_events">
<div class="card">
  <h2>事件明细（全部 __N_TOTAL__ 次买入，日期倒序）</h2>
  <div class="filterbar">
    <span class="filter-label">按档位筛选：</span>
    <select id="bandFilter" onchange="filterEvents(this.value)">
      <option value="all">全部（__N_TOTAL__）</option>
      <option value="35-40">RSI 35-40（__N_BAND1__）</option>
      <option value="30-35">RSI 30-35（__N_BAND2__）</option>
      <option value="&lt;30">RSI &lt;30（__N_BAND3__）</option>
    </select>
    <span class="filter-note" id="filterNote"></span>
  </div>
  <div class="scroll"><table>
    <thead>__ALL_HEAD__</thead>
    <tbody id="eventBody">__ALL_ROWS__</tbody>
  </table></div>
  <p class="src">三档区间跌落买入全部事件：每行一次买入（当日收盘），三组列为 T+5 / T+10 / T+20 窗口的 最大涨幅 / 最终收益 / 效率比率 ER，末列为相对 SPY 的 T+20 超额（pp）。</p>
</div>
</div>

</div>
<script>
var CHART = __DATA_JSON__;
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
function showTab(id, btn){
  document.querySelectorAll(".pane").forEach(function(p){p.classList.remove("on");});
  document.querySelectorAll(".tabbar button").forEach(function(b){b.classList.remove("on");});
  document.getElementById(id).classList.add("on");
  btn.classList.add("on");
  setTimeout(function(){window.dispatchEvent(new Event("resize"));},60);
}
function filterEvents(v){
  var rows = document.querySelectorAll("#eventBody tr");
  var show = 0;
  rows.forEach(function(r){
    var hit = (v === "all" || r.getAttribute("data-band") === v);
    r.style.display = hit ? "" : "none";
    if (hit) show++;
  });
  var note = document.getElementById("filterNote");
  if (note) note.textContent = "当前显示 " + show + " / " + rows.length + " 条";
}
(function(){
  var ch = echarts.init(document.getElementById("ch_band"));
  var b = CHART.band;
  ch.setOption({
    animation:false,
    legend:{data:["maxG 中位","fwd20 中位","ER 中位"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:55,right:55,top:38,bottom:30},
    xAxis:{type:"category",data:b.map(function(x){return "RSI "+x.bk;}),axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:[
      {type:"value",name:"%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
      {type:"value",name:"ER",min:0,max:0.35,axisLabel:{formatter:function(v){return v.toFixed(2);},color:"#9aa1ab"},splitLine:{show:false}}
    ],
    series:[
      {name:"maxG 中位",type:"bar",barWidth:16,data:b.map(function(x){return x.maxg;}),itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"fwd20 中位",type:"bar",barWidth:16,data:b.map(function(x){return x.fwd;}),itemStyle:{color:C.teal},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"ER 中位",type:"line",yAxisIndex:1,data:b.map(function(x){return x.er;}),lineStyle:{color:C.blue,width:1.6},symbol:"circle",symbolSize:6,itemStyle:{color:C.blue}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_cd10"));
  var d = CHART.cd10;
  ch.setOption({
    animation:false,
    legend:{data:["全量 fwd20","cd10 fwd20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:50,right:20,top:36,bottom:30},
    xAxis:{type:"category",data:d.map(function(x){return "RSI "+x.bk;}),axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"fwd20 中位 %",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"全量 fwd20",type:"bar",barWidth:14,data:d.map(function(x){return x.all_fwd;}),itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"cd10 fwd20",type:"bar",barWidth:14,data:d.map(function(x){return x.cd10_fwd;}),itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_year"));
  var y = CHART.year;
  ch.setOption({
    animation:false,
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:40,right:15,top:20,bottom:24},
    xAxis:{type:"category",data:y.map(function(x){return x.y;}),axisLabel:{color:"#4b5563",fontSize:10,interval:2}},
    yAxis:{type:"value",name:"事件数",minInterval:1,axisLabel:{color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[{type:"bar",data:y.map(function(x){return x.n;}),itemStyle:{color:C.orange,opacity:0.9},barWidth:"55%",
      label:{show:true,position:"top",fontSize:8,formatter:function(p){return p.value>0?p.value:"";}}}]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__ROWS1__", "".join(rows1))
HTML = HTML.replace("__ROWS2__", "".join(rows2))
HTML = HTML.replace("__ROWS3__", "".join(rows3))
HTML = HTML.replace("__RECENT_HEAD__", whead())
HTML = HTML.replace("__RECENT_ROWS__", recent_html)
HTML = HTML.replace("__N_TOTAL__", str(D["n_total"]))
HTML = HTML.replace("__N_BAND1__", str(D["by_band"]["35-40"]["fwd20"]["n"]))
HTML = HTML.replace("__N_BAND2__", str(D["by_band"]["30-35"]["fwd20"]["n"]))
HTML = HTML.replace("__N_BAND3__", str(D["by_band"]["<30"]["fwd20"]["n"]))
HTML = HTML.replace("__ALL_HEAD__", all_head_html)
HTML = HTML.replace("__ALL_ROWS__", all_events_html)
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")
