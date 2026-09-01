# -*- coding: utf-8 -*-
"""
DAL RSI 区间跌落买入（阶梯式越跌越买）报告 —— 复刻 56 号 CCL 格式 + <30 下钻章节
读取 results/dal_rsi_band_dip.json + results/dal_rsi_sub30_deep.json
输出 reports/64_DAL_RSI档位买入/index.html
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "64_DAL_RSI档位买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "dal_rsi_band_dip.json"), encoding="utf-8") as f:
    D = json.load(f)
with open(os.path.join(RES, "dal_rsi_sub30_deep.json"), encoding="utf-8") as f:
    S = json.load(f)

BK_ORDER = ["35-40", "30-35", "<30"]
WINS = (5, 10, 20)


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

# ---------- 表4 下钻（<30 内） ----------
DEEP_KEYS = [
    ("RSI 精值", "by_rsi", ["rsi<24", "rsi24-26", "rsi26-28", "rsi28-30"]),
    ("回撤深度 dd60", "by_dd60", ["dd60>-10", "dd60 -20~-10", "dd60 -30~-20", "dd60<=-30"]),
    ("回撤深度 dd250", "by_dd250", ["dd250>-20", "dd250 -35~-20", "dd250<=-35"]),
]


def deep_row(label):
    blk = S["by_rsi"].get(label) or S["by_dd60"].get(label) or S["by_dd250"].get(label)
    if not blk or not blk["fwd20"] or blk["fwd20"]["n"] == 0:
        return f"<tr><td class='nowrap'>{label}</td><td class='na'>—</td></tr>", None
    d = blk["fwd20"]
    row = (f"<tr><td class='nowrap'>{label}</td><td>{d['n']}</td>"
           f"{fcell(blk['fwd5']['median'])}{fcell(d['median'])}"
           f"<td class='nowrap'>{blk['win20']}%</td>"
           f"{fcell(blk['ex20']['median'])}"
           f"{fcell(blk['maxg20']['median'])}"
           f"<td class='nowrap'>{blk['d2m']['median']:.1f}</td></tr>")
    return row, {"label": label, "n": d["n"], "fwd": d["median"], "ex": blk["ex20"]["median"],
                 "win": blk["win20"], "maxg": blk["maxg20"]["median"]}

rows4a, chart_deep = [], []
for k in DEEP_KEYS[0][2]:
    r, c = deep_row(k)
    rows4a.append(r)
    if c:
        chart_deep.append(c)
rows4b, chart_deep2 = [], []
for k in DEEP_KEYS[1][2] + DEEP_KEYS[2][2]:
    r, c = deep_row(k)
    rows4b.append(r)
    if c:
        chart_deep2.append(c)

# d2m / pl5 两行
rows4c = []
for label, key in [("反弹快 d2m≤3", "d2m<=3"), ("反弹慢 d2m>3", "d2m>3"),
                   ("前5日跌<5%", "pl5>=-5"), ("前5日跌≥5%", "pl5<-5")]:
    blk = S["by_d2m"].get(key) or S["by_pl5"].get(key)
    if not blk or not blk["fwd20"] or blk["fwd20"]["n"] == 0:
        rows4c.append(f"<tr><td class='nowrap'>{label}</td><td class='na'>—</td></tr>")
        continue
    d = blk["fwd20"]
    rows4c.append(f"<tr><td class='nowrap'>{label}</td><td>{d['n']}</td>"
                  f"{fcell(blk['fwd5']['median'])}{fcell(d['median'])}"
                  f"<td class='nowrap'>{blk['win20']}%</td>"
                  f"{fcell(blk['ex20']['median'])}"
                  f"{fcell(blk['maxg20']['median'])}"
                  f"<td class='nowrap'>{blk['d2m']['median']:.1f}</td></tr>")

# 二维 grid
rows4d = []
for k, v in sorted(S["grid_rsi_dd60"].items(), key=lambda x: -(x[1]["fwd20"]["median"] or -99)):
    if not v["fwd20"] or not v["fwd20"]["n"]:
        continue
    d = v["fwd20"]
    rows4d.append(f"<tr><td class='nowrap'>{k}</td><td>{d['n']}</td>"
                  f"{fcell(d['median'])}<td class='nowrap'>{v['win20']}%</td>"
                  f"{fcell(v['ex20']['median'])}{fcell(v['maxg20']['median'])}</tr>")

# ---------- 表5 最近 5 次 ----------
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


def whead():
    th = "<tr><th rowspan='2'>日期</th><th rowspan='2'>档位</th><th rowspan='2'>RSI</th>"
    for NN in WINS:
        th += f"<th colspan='3' class='grph'>{NN}日窗口<br>最大 / 最终 / ER</th>"
    th += "</tr><tr>"
    for _ in WINS:
        th += "<th>最大</th><th>最终</th><th>ER</th>"
    th += "</tr>"
    return th


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


recent_html = "".join(wrow(e) for e in D["recent"])
all_events_html = "".join(all_wrow(e) for e in sorted(D["events"], key=lambda x: x["date"], reverse=True))

# ---------- 年份分布 ----------
chart_year = D["year_dist"]

CHART = {"band": chart_band, "cd10": chart_cd10, "year": chart_year,
         "deep": chart_deep, "deep2": chart_deep2,
         "n_total": D["n_total"], "n_cd10": D["n_cd10"],
         "base_fwd": D["base"]["fwd"]["median"], "base_maxg": D["base"]["maxg"]["median"],
         "sub_base_fwd": S["base"]["fwd20"]["median"], "sub_base_ex": S["base"]["ex20"]["median"]}

echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DAL · RSI 区间跌落买入（越跌越买阶梯式）</title>
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
  <h1>DAL · RSI 区间跌落买入（越跌越买阶梯式）</h1>
  <div class="meta">事件口径：当日收盘 RSI 档位比前日更低位 → 当日收盘买入 · 三档：35-40 / 30-35 / &lt;30（40 以上不买）· 每次跨区间独立统计 · 主口径无去重（332 事件）+ cd10 对照（138）· SPY 同窗口对照 · 2026-09-02（数据至 09-01）</div>
  <div class="callout blue">
    <b>与 56 号 CCL 同口径：</b>只要收盘 RSI 从高区间跌入更低区间就买一次（例：36 跌入 35-40 买第 1 次、次日 25 跌入 &lt;30 买第 2 次），每次买入独立统计 T+5/T+10/T+20 窗口。
    <b>当前状态：DAL 收 76.41，RSI 14 = 29.5 已跌破 30（09-01），dd60/dd250 = −18.2%，正处 &lt;30 档触发窗口边缘。</b>回答：把每次跌入更低档当成买入机会，DAL 的收益结构如何？
  </div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="callout amber">
    <b>与 CCL 结论相反：DAL 的 RSI 分档买入全程无超额，是"纯 β 反弹"标的。</b>
    三档超额中位 <b>−0.05 / −0.93 / −0.82pp</b>（CCL 为 −0.13 / −0.33 / <b>+1.50pp</b>）——即使跌透 &lt;30 买入，DAL 也只是随大盘一起反弹，跑不赢 SPY；
    全期 DAL fwd20 基率 +1.29% 本就跑输 SPY +1.59%。绝对收益虽随档位加深上升（35-40 +1.70% → 30-35 +0.89% → &lt;30 +2.42%），但 30-35 档反常转弱、&lt;30 档胜率仅 59.4%，远弱于 CCL 同档 64.6%。
  </div>
  <div class="verdict"><b>① cd10 去重后 &lt;30 档彻底崩坏（与 CCL 相反）：10 次 fwd20 −5.34%、胜率 40%、超额 −4.47pp。</b>
    CCL 同一波暴跌"首档触发"质量最高（去重后胜率 84.6%、超额 +2.73pp）；DAL 去重后 n 仅 10 且集中在 2008 金融危机 / 2020 疫情两次系统性熊市——
    <b>首次触发就买 DAL = 接飞刀</b>，连续加仓反而摊平成本。</div>
  <div class="verdict"><b>② 全部历史 alpha 来自疫情前，本轮牛市（2023+）三档全负、30-35 档最惨。</b>
    疫情前 &lt;30 档 +5.70% / 超额 +3.24pp / 胜率 70.7%（2008-09 金融危机 V 型反弹贡献）；
    <b>本轮牛市 35-40 −1.11% / 30-35 −7.54%（胜率 26.3%）/ &lt;30 −4.29%，超额 −1.8~−7.0pp 全线失效</b>——航空股 2023 以来结构性阴跌，超卖不反弹（与 CCL 本轮 &lt;30 档 +11.49% 恰好相反）。</div>
  <div class="verdict gr"><b>③ 下钻：只有"年线级深跌 + RSI 跌破 26"才有 edge。</b>
    dd250 ≤ −35%（距 250 日高点回撤 35%+）n=23 超额 <b>+4.9pp</b>、maxG +11.1%；RSI 精值 &lt;24 超额 +12.9pp（n=2）/ 24-26 +2.2pp（n=6），
    <b>26-30 区间超额转负（−2.1 / −0.5pp）——DAL 的 RSI 30 不是超卖线，26 才是</b>；当前 RSI 29.5、dd250 仅 −18.2%，均未达高质量买点门槛。</div>
  <div class="verdict"><b>④ "反弹快"= 下跌中继，与 CCL 完全一致：d2m≤3（20 日内 3 天见顶）n=22 fwd20 −10.4%、胜率 0%、超额 −11.4pp。</b>
    慢反弹（d2m&gt;3）n=47 +6.8% / 胜率 87.2% / 超额 +2.9pp——快反弹是空头陷阱，等 20 日窗口走出方向再确认。</div>
  <div class="verdict amber"><b>⑤ 操作含义：当前 RSI 29.5 虽触发 &lt;30 档，但历史统计不支持 DAL 的超卖买入。</b>
    本轮牛市该档超额 −4.77pp、cd10 后 −4.47pp；唯一正 edge 的"RSI&lt;26 × dd250≤−35"组合当前不满足（RSI 29.5、dd250 −18.2%）。
    <b>若已持有，不因 RSI 超卖加仓；若空仓，等 RSI 跌破 26 且年线级回撤再评估</b>。</div>
</div>

<div class="card">
  <h2>一、三档收益 vs 基率（332 次，T+20 中位）</h2>
  <div class="chart" id="ch_band"></div>
  <p class="src" style="margin-top:2px">柱 = maxG / fwd（中位，左轴）；点 = ER（右轴）。基率（全部重叠 20 日窗口）：DAL fwd 中位 +1.29%、maxG +6.50%、SPY fwd +1.59%。</p>
  <div class="scroll" style="margin-top:8px">
  <table>
    <thead><tr><th>档位</th><th>n</th><th>maxG20 中位</th><th>fwd20 中位</th><th>ER20 中位</th><th>胜率 T+20</th><th>曾解套率</th><th>超额20 中位</th></tr></thead>
    <tbody>__ROWS1__</tbody>
  </table>
  </div>
  <p class="src">三档绝对收益随档位加深整体上升但<b>超额全部 ≤0</b>：35-40 +1.70%（超额 −0.05pp）≈ 基率，30-35 反常转弱 +0.89%（−0.93pp），
  &lt;30 绝对收益最高 +2.42% 但超额仍 −0.82pp——DAL 的 RSI 超卖反弹是 β 反弹（大盘带动），无自身 α；对比 CCL 同档超额 +1.50pp。</p>
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
  <p class="src" style="margin-top:8px">去重逻辑：事件日相隔 ≥10 交易日（同一波下跌只保留第一次触发）。<b>&lt;30 档去重后 fwd20 +2.42% → −5.34%、胜率 59.4%→40%、超额 −0.82→−4.47pp</b>——
  与 CCL 相反（CCL 去重后 +4.46%/84.6%/+2.73pp 质量提升）：DAL 的 &lt;30 事件集中在系统性熊市，首档触发即接飞刀；</p>
</div>

<div class="card">
  <h2>三、分阶段 × 档位（fwd20 中位）</h2>
  <div class="scroll"><table>
    <thead><tr><th>阶段</th><th>RSI 35-40</th><th>RSI 30-35</th><th>RSI &lt;30</th></tr></thead>
    <tbody>__ROWS3__</tbody>
  </table></div>
  <p class="src">疫情前（2007-2020.2）：三档全正、&lt;30 档 +5.70% 超额 +3.24pp 胜率 70.7%——金融危机 V 型反弹期的低位买入普适有效；
  疫情~2022：35-40 +4.06%（2020 V 反弹）但 30-35 / &lt;30 档超额 −3.7~−6.7pp（2021-22 航空股反复承压、超卖不弹）；
  <b>本轮牛市（2023+）：三档 fwd20 全负（−1.11 / −7.54 / −4.29%），超额 −1.8~−7.0pp 全线失效，30-35 档胜率仅 26.3%</b>——与 CCL 本轮"&lt;30 档一枝独秀"完全相反，DAL 是"越跌越不能买"。</p>
</div>

<div class="card">
  <h2>四、&lt;30 下钻：什么位置买 DAL 才有 edge（69 次）</h2>
  <div class="grid2">
    <div class="chart" id="ch_deep" style="height:360px"></div>
    <div class="chart" id="ch_deep2" style="height:360px"></div>
  </div>
  <h3>4a. RSI 精值四档 × 回撤深度（fwd20 中位）</h3>
  <div class="scroll"><table>
    <thead><tr><th>分档</th><th>n</th><th>fwd5 中位</th><th>fwd20 中位</th><th>胜率 T+20</th><th>超额20 中位</th><th>maxG20 中位</th><th>d2m 中位</th></tr></thead>
    <tbody>__ROWS4A____ROWS4B__</tbody>
  </table></div>
  <p class="src">RSI 精值：<b>&lt;24 / 24-26 档超额为正（+12.9 / +2.2pp），26-30 转负</b>——DAL 的 RSI 超卖线在 26 而非 30；
  回撤深度：<b>dd250 ≤ −35% 是唯一显著正超额维度（+4.9pp）</b>，dd60 ≤ −30% 弱正（+1.6pp）——必须年线级深跌，月线级回调（dd60 −10~−30%）无 edge（超额 −0.8~−1.5pp）。</p>
  <h3>4b. 反弹速度 × 前 5 日动能</h3>
  <div class="scroll"><table>
    <thead><tr><th>分档</th><th>n</th><th>fwd5 中位</th><th>fwd20 中位</th><th>胜率 T+20</th><th>超额20 中位</th><th>maxG20 中位</th><th>d2m 中位</th></tr></thead>
    <tbody>__ROWS4C__</tbody>
  </table></div>
  <p class="src"><b>d2m≤3（20 日内 3 天即见顶）n=22、fwd20 −10.4%、胜率 0%、超额 −11.4pp——"反弹快"是下跌中继（与 CCL 结论一致）</b>；
  前 5 日跌 ≥5%（下跌动能强）的超卖（n=59，fwd20 +3.5%）好于跌 &lt;5% 的阴跌（n=10，+0.8%）——急跌后的超卖才有反弹，阴跌没有。</p>
  <h3>4c. RSI 精值 × dd60 二维组合（n≥3）</h3>
  <div class="scroll"><table>
    <thead><tr><th>组合</th><th>n</th><th>fwd20 中位</th><th>胜率 T+20</th><th>超额20 中位</th><th>maxG20 中位</th></tr></thead>
    <tbody>__ROWS4D__</tbody>
  </table></div>
  <p class="src">唯一亮眼组合 rsi24-26 × dd60≤-30（n=3，+14.2%/超额 +8.6pp）样本太少不可靠；次优 rsi26-28 × dd60 -20~-10（n=11，+5.0%/胜率 72.7%）但超额 −1.2pp——<b>二维组合无稳健正超额，印证结论①：DAL 分档买入无 α</b>。</p>
</div>

<div class="card">
  <h2>五、事件年份分布 + 最近 5 次买入</h2>
  <div class="chart" id="ch_year" style="height:240px"></div>
  <p class="src">事件分布均匀（每年 10-33 次），波动大年（2011 年 33 次、2008 年 24 次、2021 年 24 次）略高；2026 年至今 6 次。</p>
  <h3 style="margin-top:14px">最近 5 次买入（三窗口 最大涨幅 / 最终收益 / ER）</h3>
  <div class="scroll"><table>
    <thead>__RECENT_HEAD__</thead>
    <tbody>__RECENT_ROWS__</tbody>
  </table></div>
  <p class="src">2026-07-23（35-40 档）T+20 −1.11%、超额 −4.42pp——浅跌档失效的最近样本；
  2026-03 波段：30-35 档两次 +14.9%/+13.2%、超额 +14.8/+14.9pp（3 月趋势启动期强反弹），35-40 档 +5.9%/−1.6%——2026 年 DAL 的买点出现在 3 月启动段而非 7-9 月的回落段。</p>
</div>

<div class="card">
  <div class="src">数据：Futu MCP 日线（前复权，2007-04-26 ~ 2026-09-01，SPY 增补 08-28~09-01）· 脚本：scripts/fetch_dal_futu.py + dal_rsi_band_dip.py + dal_rsi_sub30_deep.py + build_64_dal_rsi_report.py · 结果：results/dal_rsi_band_dip.json + dal_rsi_sub30_deep.json。
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
function barChart(id, dd, labels){
  var ch = echarts.init(document.getElementById(id));
  ch.setOption({
    animation:false,
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:120,right:55,top:16,bottom:24},
    xAxis:{type:"value",name:"fwd20 中位 %",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    yAxis:{type:"category",data:labels,axisLabel:{color:"#4b5563",fontSize:10.5}},
    series:[{type:"bar",barWidth:13,data:dd.map(function(x){
        return {value:x.fwd,itemStyle:{color:x.fwd>=0?C.verm:C.teal}};
      }),label:{show:true,position:"right",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}}]
  });
  window.addEventListener("resize",function(){ch.resize();});
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
barChart("ch_deep", CHART.deep, CHART.deep.map(function(x){return x.label;}));
barChart("ch_deep2", CHART.deep2, CHART.deep2.map(function(x){return x.label;}));
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__ROWS1__", "".join(rows1))
HTML = HTML.replace("__ROWS2__", "".join(rows2))
HTML = HTML.replace("__ROWS3__", "".join(rows3))
HTML = HTML.replace("__ROWS4A__", "".join(rows4a))
HTML = HTML.replace("__ROWS4B__", "".join(rows4b))
HTML = HTML.replace("__ROWS4C__", "".join(rows4c))
HTML = HTML.replace("__ROWS4D__", "".join(rows4d))
HTML = HTML.replace("__RECENT_HEAD__", whead())
HTML = HTML.replace("__RECENT_ROWS__", recent_html)
HTML = HTML.replace("__N_TOTAL__", str(D["n_total"]))
HTML = HTML.replace("__N_BAND1__", str(D["by_band"]["35-40"]["fwd20"]["n"]))
HTML = HTML.replace("__N_BAND2__", str(D["by_band"]["30-35"]["fwd20"]["n"]))
HTML = HTML.replace("__N_BAND3__", str(D["by_band"]["<30"]["fwd20"]["n"]))
HTML = HTML.replace("__ALL_HEAD__", all_whead())
HTML = HTML.replace("__ALL_ROWS__", all_events_html)
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")
