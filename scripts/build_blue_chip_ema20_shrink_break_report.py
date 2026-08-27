# -*- coding: utf-8 -*-
"""
构建研报：优质蓝筹「贴EMA20缩量跌破平台」事件研究 —— T+5/T+10/T+20
读取 results/blue_chip_ema20_shrink_break.json + ..._kline.json
输出 reports/44_贴EMA20缩量跌破平台/index.html
核心新增：事件 K 线浏览器（candlestick + EMA20 + 缩量破位标注 + 平台下沿 + T+N 标记点）
静默写盘：只打印 written 路径与体积。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "44_贴EMA20缩量跌破平台")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "blue_chip_ema20_shrink_break.json"), encoding="utf-8") as f:
    D = json.load(f)
with open(os.path.join(RES, "blue_chip_ema20_shrink_break_kline.json"), encoding="utf-8") as f:
    KL = json.load(f)

SECTOR_CN = {
    "Technology": "科技", "Financials": "金融", "Industrials": "工业",
    "Healthcare": "医疗", "Consumer": "消费",
    "Materials_Utilities_Other": "材料/公用/其他",
}
SECTOR_ORDER = ["科技", "金融", "工业", "医疗", "消费", "材料/公用/其他"]
SECTOR_COLOR = {
    "科技": "#0072B2", "金融": "#E69F00", "工业": "#009E73",
    "医疗": "#56B4E9", "消费": "#CC79A7", "材料/公用/其他": "#D55E00",
}
STAGE_CN = {"A_pre": "疫情前(1962~2020-02)", "B_post": "疫情及股灾后(2020-02~2022-12)", "C_bull": "本轮牛市(2023~)"}

ea = D["events_main"]["block"]
ea_day = D["events_main"]["day_clustered"]
ec = D["events_cd10"]["block"]
base = D["baseline_all_days"]
bg0 = D["baseline_bg_only"]
ctlA = D["control_kept_box"]
ctlB = D["control_no_shrink"]

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}%"

def pct2(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- KPI ----------
KPI = [
    ("8305", "缩量破平台事件总数（72只·1962起）", "num"),
    ("3935", "日历日聚类后独立事件日", "num"),
    (pct2(ea["T5"]["mean"]), "T+5 均值（胜率 %d%%）" % ea["T5"]["win"], "up"),
    (pct2(ea["T10"]["mean"]), "T+10 均值（胜率 %d%%）" % ea["T10"]["win"], "up"),
    (pct2(ea["T20"]["mean"]), "T+20 均值（胜率 %d%%）" % ea["T20"]["win"], "up"),
    (pct2(base["T10"]["mean"]), "全历史基率 T+10（胜率 %d%%）" % base["T10"]["win"], "dn"),
    (pct2(ea["T5_ex_spy"]["mean"]), "T+5 超额 vs SPY（t=%.1f）" % ea["T5_ex_spy"]["t"], "up"),
    (pct2(ctlA["T5"]["mean"]), "对照：缩量收跌但守住平台 T+5", "dn"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

# ---------- 表格行生成 ----------
def cell(s):
    if not s or s.get("n", 0) == 0:
        return "<td class='na'>—</td>"
    mean = s["mean"]; win = s["win"]; t = s.get("t")
    tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
    cls = "up" if mean > 0 else "dn"
    return f"<td class='{cls} nowrap'>{pct(mean)} <span class='note2'>({win}%)</span>{tstr}</td>"

def xcell(s):
    if not s or s.get("n", 0) == 0:
        return "<td class='na'>—</td>"
    t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
    cls = "up" if s["mean"] > 0 else "dn"
    return f"<td class='{cls} nowrap'>{pct(s['mean'])}{tstr}</td>"

def row(name, b, tag=""):
    cls = " class='baserow'" if tag == "base" else ""
    return (f"<tr{cls}><td class='nowrap'><b>{name}</b></td><td>{b['T5']['n']}</td>"
            f"{cell(b['T5'])}{cell(b['T10'])}{cell(b['T20'])}"
            f"{xcell(b['T5_ex_spy'])}{xcell(b['T10_ex_spy'])}{xcell(b['T20_ex_spy'])}</tr>")

core_rows = "".join([
    row("全历史基率（72票·每日）", base, "base"),
    row("纯背景（贴线横盘所有日）", bg0),
    row("对照A：缩量收跌但守住平台", ctlA),
    row("对照B：收跌破平台但放量", ctlB),
    row("主事件 · 全部（8305）", ea),
    row("主事件 · 日历日聚类", ea_day),
    row("主事件 · cd10去重", ec),
])

# ---------- 分阶段 ----------
stage_rows = ""
stage_chart = []
for st in ["A_pre", "B_post", "C_bull"]:
    b = D["events_main"]["by_stage"][st]
    stage_rows += f"<tr><td class='nowrap'><b>{STAGE_CN[st]}</b></td><td>{b['T5']['n']}</td>{cell(b['T5'])}{cell(b['T10'])}{cell(b['T20'])}</tr>"
    stage_chart.append({"name": STAGE_CN[st].split("(")[0],
                        "t5": b["T5"]["mean"], "t10": b["T10"]["mean"], "t20": b["T20"]["mean"]})

# ---------- 分板块 ----------
sector_rows = ""
sector_chart = []
_for_sector_map = D["events_main"]["by_sector"]
for sc in SECTOR_ORDER:
    sc_en = {v: k for k, v in SECTOR_CN.items()}.get(sc, sc)
    b = _for_sector_map.get(sc_en, {})
    if not b.get("T5", {}).get("n"):
        continue
    sector_rows += f"<tr><td class='nowrap'><b>{sc}</b></td><td>{b['T5']['n']}</td>{cell(b['T5'])}{cell(b['T10'])}{cell(b['T20'])}</tr>"
    sector_chart.append({"name": sc, "n": b["T5"]["n"],
                         "t5": b["T5"]["mean"], "t10": b["T10"]["mean"], "t20": b["T20"]["mean"]})

# ---------- 敏感性 ----------
sens_rows = ""
for s in D["sensitivity"]:
    t5, t10 = s["T5"], s["T10"]
    def sc(s):
        if not s.get("n"): return "<td class='na'>—</td>"
        cls = "up" if s["mean"] > 0 else "dn"
        return f"<td class='{cls} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span></td>"
    sens_rows += f"<tr><td class='nowrap'><b>{s['label']}</b></td><td>{s['n']}</td>{sc(s['T5'])}{sc(s['T10'])}{sc(s['T20'])}</tr>"

# ---------- 事件明细（全部）----------
# 建立 (date,ticker) -> kline 序号 映射，供"看K线"跳转
kline_index = {}
for i, e in enumerate(KL["events"]):
    kline_index[(e["date"], e["ticker"])] = i

ev_rows = []
for e in D["events"]:
    def f(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='{'up' if v>0 else 'dn'} nowrap'>{v:+.2f}%</td>"
    ki = kline_index.get((e["date"], e["ticker"]))
    klink = (f"<a class='klink' href='javascript:gotoKline({ki})'>K线</a>" if ki is not None else "")
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'><b>{e['ticker']}</b></td>"
        f"<td class='nowrap'>{SECTOR_CN.get(e['sector'], e['sector'])}</td>"
        f"<td>{e['px']}</td><td>{e['dev_pct']}%</td><td>{e['vol_rank']}</td>"
        f"{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}<td class='nowrap'>{klink}</td></tr>")
ev_rows_html = "".join(ev_rows)

# ---------- 当前状态 ----------
cur = D["current"]
cur_bg_txt = "、".join([f"{c['ticker']}(dev {c['dev']}%)" for c in cur["bg_today"]]) or "无"
recent_ev_txt = []
for r in cur["recent_events_45d"]:
    f5 = f"{r['fwd5']:+.2f}%" if r["fwd5"] is not None else "—"
    f10 = f"{r['fwd10']:+.2f}%" if r["fwd10"] is not None else "—"
    recent_ev_txt.append(f"{r['date']} {r['ticker']} (T+5 {f5} / T+10 {f10})")
recent_ev_txt = "；".join(recent_ev_txt) or "近45日无事件"

# ---------- 数据注入 ----------
CHART = {
    "stage": stage_chart,
    "sector": sector_chart,
    "base": {"t5": base["T5"]["mean"], "t10": base["T10"]["mean"], "t20": base["T20"]["mean"]},
    "compare": {
        "labels": ["T+5", "T+10", "T+20"],
        "base": [base["T5"]["mean"], base["T10"]["mean"], base["T20"]["mean"]],
        "bg": [bg0["T5"]["mean"], bg0["T10"]["mean"], bg0["T20"]["mean"]],
        "ctlA": [ctlA["T5"]["mean"], ctlA["T10"]["mean"], ctlA["T20"]["mean"]],
        "ctlB": [ctlB["T5"]["mean"], ctlB["T10"]["mean"], ctlB["T20"]["mean"]],
        "ev": [ea["T5"]["mean"], ea["T10"]["mean"], ea["T20"]["mean"]],
        "day": [ea_day["T5"]["mean"], ea_day["T10"]["mean"], ea_day["T20"]["mean"]],
        "cd10": [ec["T5"]["mean"], ec["T10"]["mean"], ec["T20"]["mean"]],
    },
}

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o

CHART = clean(CHART)
KLINE = clean(KL["events"])
params = D["meta"]["params"]

# ---------- 组装 HTML ----------
echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>优质蓝筹「贴EMA20缩量跌破平台」事件研究 · T+5/T+10/T+20</title>
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
  .evbox table th{position:sticky;top:0;z-index:2;background:#f3f5f8;}
  .chart{width:100%;height:420px;}
  .callout{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}
  .callout.blue{border-color:#cfe0f5;background:#f0f6fd;}
  .callout b{color:var(--amber);} .callout.blue b{color:var(--blue);}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
  ul.tight{padding-left:20px;margin:6px 0;} ul.tight li{margin:3px 0;font-size:13px;}
  a.klink{color:var(--blue);text-decoration:none;font-weight:600;}
  a.klink:hover{text-decoration:underline;}
  /* tabs */
  .tabs{display:flex;gap:6px;border-bottom:2px solid var(--line);margin-bottom:0;flex-wrap:wrap;}
  .tab{padding:8px 16px;cursor:pointer;font-size:13px;color:var(--sub);border-bottom:2px solid transparent;margin-bottom:-2px;user-select:none;}
  .tab.active{color:var(--blue);border-bottom-color:var(--blue);font-weight:600;}
  .tabpanel{display:none;} .tabpanel.active{display:block;}
  /* K线浏览器 */
  .kb{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:8px 0 12px;}
  .kb select{font-size:13px;padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);min-width:210px;}
  .kb button{padding:5px 14px;font-size:13px;border:1px solid var(--line);border-radius:8px;background:#fbfcfe;cursor:pointer;color:var(--ink);}
  .kb button:hover{background:#f0f4fb;border-color:var(--blue);}
  .kb .seq{color:var(--sub);font-size:12px;}
  .kcard{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:10px 0;}
  .kcell{background:#fbfcfe;border:1px solid var(--line);border-radius:8px;padding:8px 10px;}
  .kcell .k{font-size:15px;font-weight:700;}
  .kcell .l{color:var(--sub);font-size:11px;}
  .kcell .k.up{color:var(--verm);} .kcell .k.dn{color:var(--teal);}
  .kcell .k.flat{color:var(--ink);}
  .kchart{width:100%;height:480px;}
  .legend-bar{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--sub);margin-top:6px;}
  .legend-bar i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:4px;vertical-align:-1px;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>优质蓝筹「贴EMA20 · 缩量跌破平台」事件研究 · T+5 / T+10 / T+20 表现</h1>
  <div class="meta">事件研究 · 数据 1962 ~ 2026-08-26（Yahoo 复权价 adj_close，72 只蓝筹、16,271 个交易日，MMC 因数据源故障未含）· 生成于 2026-08-27</div>
  <div class="callout blue">
    <b>口径定义（通俗版）：</b>先找<b>贴着 20 日均线（EMA20）横盘的小平台</b>——过去 __BW__ 个交易日（默认 5 日，3~10 日均可）股价在 EMA20 上方小幅波动（每日常偏离 ≤ +6% 内、允许偶发跌破 ≤ 2.5% 并快速修复、平台振幅 ≤ 5%）。
    然后某一天出现<b>缩量阴线跌破平台</b>——当天收跌，成交量是近 10 个交易日（约两周）里<b>数一数二低的</b>（第 1 或第 2 低），且收盘价跌破平台下沿（过去 __BW__ 日最低收盘价）。
    以此为买入基准，统计其后 T+5 / T+10 / T+20（交易日）表现。
  </div>
  <div class="callout">
    <b>当前状态（2026-08-26 收盘）：</b>全池 72 只蓝筹中，最新一日仍处于"贴线横盘平台"形态的有 <b style="color:var(--blue)">__CURBG__</b>。<br>
    近 45 个交易日触发过本事件的有：__RECENTEV__。
  </div>
  <div class="kpis">__KPI__</div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict"><b>① 整体几乎没有可交易 edge（优势）。</b>8,305 次"贴EMA20缩量跌破平台"后：T+5 <b>+0.40%</b>（胜率 56.4%）、T+10 <b>+0.63%</b>（56.9%）、T+20 <b>+1.26%</b>（59.2%）。对比全历史基率（T+5 +0.36% / T+10 +0.71% / T+20 +1.42%）——<b>T+10、T+20 甚至略低于"随便哪天买"</b>；T+5 也只高 0.04pp，扣掉大盘本身上涨后（相对 SPY 超额仅 +0.11pp）基本是零。</div>
  <div class="verdict"><b>② "缩量"不是关键条件。</b>同样跌破平台，缩量（+0.40%）和放量（+0.37%）之后 T+5 几乎一模一样——低成交量这个"数一数二低"的设定本身不携带额外信息。</div>
  <div class="verdict"><b>③ "破位"只有一点点信息。</b>缩量下跌时，跌破平台（+0.40%）比没跌破、守住平台（+0.21%）T+5 高 0.19pp——破位后反而略快企稳，幅度太小、不足为据。</div>
  <div class="verdict"><b>④ 当前环境最差。</b>本轮牛市（2023 以来）该形态 T+5 仅 +0.15%、胜率刚过半（51%）——正是现在所处的环境。疫情前最强（T+5 +0.45%）。分板块科技 T+5 +0.67% 最强、消费 T+10 +0.87% 最强。</div>
  <div class="verdict"><b>⑤ 结论稳健。</b>平台天数 3/7/10、振幅阈值、量能窗口、破位用收盘还是最低价——全部参数扫描下 T+5 稳定在 +0.27%~+0.48%，没有任何一组参数能翻出显著正 edge。</div>
  <div class="verdict gr"><b>一句话：</b>这跟此前 RSI 系列（报告 39/40/41）同一结论——<b>技术形态（平台/缩量/支撑）本身不给 edge</b>，"缩量假跌破后反弹"只存在于个例，统计上不可依赖。真正的 edge 在超卖位置（RSI&lt;30），不在形态。</div>
</div>

<div class="card">
  <h2>一、核心对比：不同口径的 T+5 / T+10 / T+20</h2>
  <div class="chart" id="ch_compare"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>口径</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th><th>T+5 超额SPY</th><th>T+10 超额SPY</th><th>T+20 超额SPY</th></tr></thead>
    <tbody>__CORE_ROWS__</tbody>
  </table>
  </div>
  <div class="src">均值内含 (胜率%) 与 t 值；红=正、绿=负；基率行米色底。主事件与基率几乎重合（T+10/T+20 略低），仅相对"纯背景/守住平台"略好一点点。</div>
</div>

<div class="card">
  <h2>二、分板块</h2>
  <div class="chart" id="ch_sector"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>板块</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__SECTOR_ROWS__</tbody>
  </table>
  </div>
  <div class="src">Okabe-Ito 色弱安全配色。科技 T+5 绝对收益最高（+0.67%/60.2%），消费 T+10/T+20 强，材料/公用/其他最钝。板块差异不足以构成可交易信号。</div>
</div>

<div class="card">
  <h2>三、分阶段</h2>
  <div class="chart" id="ch_stage"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>阶段</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__STAGE_ROWS__</tbody>
  </table>
  </div>
  <div class="src">虚线=全历史基率。本轮牛市（当前环境）该形态最弱，T+5 +0.15%/51.0%，基本是抛硬币。</div>
</div>

<div class="card">
  <h2>四、参数敏感性</h2>
  <div class="scroll">
  <table>
    <thead><tr><th>参数变体</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__SENS_ROWS__</tbody>
  </table>
  </div>
  <div class="src">全部变体 T+5 落在 +0.27%~+0.48%、T+10 落在 +0.57%~+0.76%，与主口径一致 → 结论不依赖参数选择。破位用收盘（主口径）还是最低价：结果一致。</div>
</div>

<div class="card">
  <h2>五、事件 K 线浏览器</h2>
  <div class="callout blue" style="margin-top:0">
    <b>怎么看：</b>右侧下拉选择事件（按日期倒序，共 __KLINE_N__ 个内嵌事件，含最近 400 个以内的全部有完整 K 线者），或用「上一个/下一个」翻页。
    K 线图中：<b style="color:var(--verm)">红K涨 / <b style="color:var(--blue)">蓝K跌</b>；<b style="color:var(--orange)">橙线 = EMA20</b>；<b style="color:var(--verm)">红色竖线 = 缩量破位日</b>；<b>灰色虚线 = 平台下沿</b>；K 线上方 pin 标记 = 事件后 T+5 / T+10 / T+20 的位置与收益。下方为成交量柱（红/蓝随涨跌，破位日橙框高亮）。事件明细表中的「K线」链接可直接跳到对应事件。
  </div>
  <div class="kb">
    <button onclick="stepKline(-1)">◀ 上一个</button>
    <button onclick="stepKline(1)">下一个 ▶</button>
    <select id="klineSel" onchange="gotoKline(+this.value)"></select>
    <span class="seq" id="klineSeq"></span>
  </div>
  <div class="kcard" id="klineCard"></div>
  <div class="kchart" id="ch_kline"></div>
  <div class="legend-bar">
    <span><i style="background:var(--verm)"></i>上涨 K 线</span>
    <span><i style="background:var(--blue)"></i>下跌 K 线</span>
    <span><i style="background:var(--orange)"></i>EMA20 均线</span>
    <span><i style="background:var(--verm)"></i>缩量破位日（红色竖线）</span>
    <span><i style="background:var(--sub)"></i>平台下沿（灰色虚线）</span>
  </div>
</div>

<!-- 事件明细独立 tab -->
<div class="card">
  <div class="tabs">
    <div class="tab active" data-tab="tab1" onclick="switchTab(this)">结论与图表</div>
    <div class="tab" data-tab="tab2" onclick="switchTab(this)">事件明细（__EVN__ 条）</div>
  </div>
  <div class="tabpanel active" id="tab1">
    <p style="font-size:13px;color:var(--sub);padding:8px 0">完整 __EVN__ 个"贴EMA20缩量跌破平台"事件明细见「事件明细」选项卡；带「K线」链接的（最近 400 个以内）可点击跳转到 K 线浏览器查看。</p>
  </div>
  <div class="tabpanel" id="tab2">
    <div class="evbox">
      <table>
        <thead><tr><th>日期</th><th>票</th><th>板块</th><th>收盘</th><th>偏离EMA</th><th>量能排名</th><th>T+5</th><th>T+10</th><th>T+20</th><th>K线</th></tr></thead>
        <tbody>__EV_ROWS__</tbody>
      </table>
    </div>
  </div>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（复权价，CDP 拉取）· 方法：EMA20 / 事件研究 / 日历日聚类与 cd10 去重稳健性 · 脚本：scripts/blue_chip_ema20_shrink_break.py + build_blue_chip_ema20_shrink_break_report.py · 数据文件：results/blue_chip_ema20_shrink_break.json（K 线：..._kline.json）· 模型：72 只优质蓝筹股池（data/blue_chips.csv，MMC 未含）。<b>本报告仅为统计回测，不构成投资建议。</b></div>
</div>

</div>
<script>
var CHART = __DATA_JSON__;
var KLINE = __KLINE_JSON__;
var KWIN = 20;
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
var kchart = null;
var curIdx = 0;

function switchTab(el){
  document.querySelectorAll(".tab").forEach(function(t){t.classList.remove("active");});
  document.querySelectorAll(".tabpanel").forEach(function(p){p.classList.remove("active");});
  el.classList.add("active");
  document.getElementById(el.dataset.tab).classList.add("active");
}

function fmt(v){ return (v>=0?"+":"")+v.toFixed(2)+"%"; }

function buildSel(){
  var sel = document.getElementById("klineSel");
  sel.innerHTML = "";
  KLINE.forEach(function(e,i){
    var o = document.createElement("option");
    o.value = i;
    o.text = e.date + "  " + e.ticker + "  " + e.sector;
    sel.appendChild(o);
  });
}

function stepKline(d){ gotoKline(curIdx + d); }

function gotoKline(i){
  if(i<0 || i>=KLINE.length) return;
  curIdx = i;
  var e = KLINE[i];
  document.getElementById("klineSel").value = i;
  document.getElementById("klineSeq").textContent = (i+1) + " / " + KLINE.length;
  var k = e.k, ev = k.ev, dates = k.dates, ohlc = k.ohlc;
  // 平台下沿 = 事件日前 KWIN 根最低 low（或收盘，取更低者直观）
  var boxLo = null;
  for(var j=0;j<ev;j++){ if(ohlc[j][2]< (boxLo===null?1e18:boxLo)) boxLo=ohlc[j][2]; }
  var evDate = dates[ev];
  // 信息卡
  var f5 = e.fwd5===null?"—":fmt(e.fwd5), f10=e.fwd10===null?"—":fmt(e.fwd10), f20=e.fwd20===null?"—":fmt(e.fwd20);
  var cls5 = e.fwd5===null?"flat":(e.fwd5>=0?"up":"dn");
  var cls10 = e.fwd10===null?"flat":(e.fwd10>=0?"up":"dn");
  var cls20 = e.fwd20===null?"flat":(e.fwd20>=0?"up":"dn");
  document.getElementById("klineCard").innerHTML =
    "<div class='kcell'><div class='k'>"+e.date+"</div><div class='l'>事件日期</div></div>"+
    "<div class='kcell'><div class='k'>"+e.ticker+"</div><div class='l'>"+e.sector+"</div></div>"+
    "<div class='kcell'><div class='k'>"+e.px+"</div><div class='l'>事件日收盘价</div></div>"+
    "<div class='kcell'><div class='k "+(e.dev_pct>=0?"up":"dn")+"'>"+e.dev_pct+"%</div><div class='l'>当日偏离EMA20</div></div>"+
    "<div class='kcell'><div class='k'>第"+e.vol_rank+"低</div><div class='l'>近10日量能排名</div></div>"+
    "<div class='kcell'><div class='k "+cls5+"'>"+f5+"</div><div class='l'>T+5</div></div>"+
    "<div class='kcell'><div class='k "+cls10+"'>"+f10+"</div><div class='l'>T+10</div></div>"+
    "<div class='kcell'><div class='k "+cls20+"'>"+f20+"</div><div class='l'>T+20</div></div>";
  // 量柱颜色
  var volData = k.vols.map(function(v,j){
    var up = ohlc[j][3]>=ohlc[j][0];
    var col = up ? C.verm : C.blue;
    if(j===ev) return {value:v, itemStyle:{color:"#ffffff", borderColor:C.orange, borderWidth:2}};
    return {value:v, itemStyle:{color:col, opacity:0.75}};
  });
  // T+N markPoint（事件后 5/10/20 根）
  var marks = [];
  [[5,"T+5",e.fwd5],[10,"T+10",e.fwd10],[20,"T+20",e.fwd20]].forEach(function(m){
    if(m[2]===null) return;
    var j = ev + m[0];
    if(j>=dates.length) return;
    marks.push({name:m[1], coord:[dates[j], ohlc[j][3]],
                value:m[1]+" "+fmt(m[2]),
                symbol:"pin", symbolSize:44,
                itemStyle:{color: m[2]>=0?C.verm:C.teal},
                label:{show:true, formatter:m[1]+"\\n"+fmt(m[2]), fontSize:9}});
  });
  kchart.setOption({
    animation:false,
    tooltip:{trigger:"axis", axisPointer:{type:"cross"}, borderWidth:1},
    legend:{data:["K线","EMA20"], top:0, textStyle:{fontSize:11,color:"#374151"}},
    axisPointer:{link:[{xAxisIndex:"all"}]},
    grid:[
      {left:64, right:24, top:34, height:"52%"},
      {left:64, right:24, top:"68%", height:"20%"}
    ],
    xAxis:[
      {type:"category", data:dates, boundaryGap:true, axisLine:{lineStyle:{color:"#d5dae2"}}, axisLabel:{color:"#4b5563",fontSize:10}, axisPointer:{label:{show:false}}},
      {type:"category", gridIndex:1, data:dates, axisLine:{lineStyle:{color:"#d5dae2"}}, axisLabel:{show:false}, axisTick:{show:false}}
    ],
    yAxis:[
      {scale:true, splitLine:{lineStyle:{color:"#eef0f3"}}, axisLabel:{color:"#4b5563",fontSize:10}},
      {gridIndex:1, splitLine:{show:false}, axisLabel:{show:false}, axisLine:{show:false}, axisTick:{show:false}}
    ],
    dataZoom:[
      {type:"inside", xAxisIndex:[0,1], start:0, end:100},
      {type:"slider", xAxisIndex:[0,1], start:0, end:100, height:14, bottom:2, borderColor:"#e5e7eb", fillerColor:"rgba(0,114,178,0.12)"}
    ],
    series:[
      {name:"K线", type:"candlestick", data:ohlc,
       itemStyle:{color:C.verm, color0:C.blue, borderColor:C.verm, borderColor0:C.blue},
       markLine:{silent:true, symbol:"none", label:{fontSize:10},
         data:[
           {xAxis:evDate, lineStyle:{color:C.verm, width:2, type:"dashed"},
            label:{formatter:"缩量破位日", position:"insideEnd", color:C.verm, fontSize:11, fontWeight:600, padding:[3,5,3,5], backgroundColor:"rgba(255,255,255,0.92)"}},
           {yAxis:boxLo, lineStyle:{color:C.sub, width:1.5, type:"dashed"},
            label:{formatter:"平台下沿 "+boxLo.toFixed(2), position:"insideEnd", color:C.sub, fontSize:10, padding:[2,4,2,4], backgroundColor:"rgba(255,255,255,0.85)"}}
         ]},
       markPoint:{data:marks, animation:false}},
      {name:"EMA20", type:"line", data:k.ema, symbol:"none",
       lineStyle:{color:C.orange, width:1.4}, itemStyle:{color:C.orange},
       markArea:{silent:true, itemStyle:{color:"rgba(0,114,178,0.05)"}, data:[[{xAxis:dates[Math.max(0,ev-20)]},{xAxis:evDate}]]}},
      {name:"成交量", type:"bar", xAxisIndex:1, yAxisIndex:1, data:volData, barWidth:"62%"}
    ]
  });
}

document.addEventListener("DOMContentLoaded", function(){
  kchart = echarts.init(document.getElementById("ch_kline"));
  buildSel();
  gotoKline(0);
  window.addEventListener("resize", function(){ kchart.resize(); });
});

// 核心对比图
(function(){
  var ch = echarts.init(document.getElementById("ch_compare"));
  var c = CHART.compare;
  var cats = ["基率","纯背景","缩量守平台","放量破平台","主事件·全部","日历日聚类","cd10去重"];
  var series = c.labels.map(function(_, i){
    return {name:c.labels[i], type:"bar", barWidth:15,
      data: cats.map(function(cn, j){
        var v = [c.base,c.bg,c.ctlA,c.ctlB,c.ev,c.day,c.cd10][j][i];
        var col = [C.sub,C.sky,C.sky,C.sky,C.blue,C.orange,C.verm][j];
        return {value:v, itemStyle:{color:col, opacity:(j<4?0.45:1)}};
      }),
      label:{show:true, position:"top", formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);}, fontSize:9, color:"#6b7280"}};
  });
  ch.setOption({
    animation:false,
    legend:{data:c.labels, top:2, textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis", axisPointer:{type:"shadow"}, formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:52,right:20,top:40,bottom:70},
    xAxis:{type:"category", data:cats, axisLabel:{color:"#4b5563",fontSize:10.5,rotate:18}},
    yAxis:{type:"value", name:"收益%", axisLabel:{formatter:"{value}%",color:"#4b5563"}, splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:series
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 板块图
(function(){
  var ch = echarts.init(document.getElementById("ch_sector"));
  var sc = CHART.sector;
  var names = sc.map(function(x){return x.name;});
  var scolor = {"科技":"#0072B2","金融":"#E69F00","工业":"#009E73","医疗":"#56B4E9","消费":"#CC79A7","材料/公用/其他":"#D55E00"};
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:12,data:sc.map(function(x){return +x.t5.toFixed(2);}),itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+10",type:"bar",barWidth:12,data:sc.map(function(x){return +x.t10.toFixed(2);}),itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+20",type:"bar",barWidth:12,data:sc.map(function(x){return +x.t20.toFixed(2);}),itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 阶段图
(function(){
  var ch = echarts.init(document.getElementById("ch_stage"));
  var st = CHART.stage;
  var names = st.map(function(x){return x.name;});
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:13,data:st.map(function(x){return +x.t5.toFixed(2);}),itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+10",type:"bar",barWidth:13,data:st.map(function(x){return +x.t10.toFixed(2);}),itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+20",type:"bar",barWidth:13,data:st.map(function(x){return +x.t20.toFixed(2);}),itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"基率T+20",type:"line",data:[CHART.base.t20,CHART.base.t20,CHART.base.t20],lineStyle:{type:"dashed",color:C.sub,width:1.2},symbol:"none",label:{show:true,position:"top",formatter:"基率T+20 "+CHART.base.t20.toFixed(2)+"%",fontSize:9,color:C.sub}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__BW__", str(params["bg_win"]))
HTML = HTML.replace("__KPI__", kpi_html)
HTML = HTML.replace("__CORE_ROWS__", core_rows)
HTML = HTML.replace("__SECTOR_ROWS__", sector_rows)
HTML = HTML.replace("__STAGE_ROWS__", stage_rows)
HTML = HTML.replace("__SENS_ROWS__", sens_rows)
HTML = HTML.replace("__EV_ROWS__", ev_rows_html)
HTML = HTML.replace("__EVN__", str(len(D["events"])))
HTML = HTML.replace("__KLINE_N__", str(len(KLINE)))
HTML = HTML.replace("__CURBG__", cur_bg_txt)
HTML = HTML.replace("__RECENTEV__", recent_ev_txt)
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))
HTML = HTML.replace("__KLINE_JSON__", json.dumps(KLINE, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")
