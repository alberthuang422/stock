# -*- coding: utf-8 -*-
"""
构建研报：优质蓝筹股池 RSI 超卖(<30)买入事件研究 —— T+5/T+10/T+20
读取 results/blue_chip_rsi_oversold.json
输出 reports/39_蓝筹RSI超卖买入/index.html
静默写盘：只打印 written 路径与体积。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "39_蓝筹RSI超卖买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "blue_chip_rsi_oversold.json"), encoding="utf-8") as f:
    D = json.load(f)

SECTOR_CN = {
    "Technology": "科技",
    "Financials": "金融",
    "Industrials": "工业",
    "Healthcare": "医疗",
    "Consumer": "消费",
    "Materials_Utilities_Other": "材料/公用/其他",
}
SECTOR_ORDER = ["科技", "金融", "工业", "医疗", "消费", "材料/公用/其他"]
# Okabe-Ito 板块配色（色弱安全），避免红绿单色区分
SECTOR_COLOR = {
    "科技": "#0072B2", "金融": "#E69F00", "工业": "#009E73",
    "医疗": "#56B4E9", "消费": "#CC79A7", "材料/公用/其他": "#D55E00",
}

ea = D["events_all"]["block"]
ea_day = D["events_all"]["day_clustered"]
ec = D["events_cd10"]["block"]
base = D["baseline_all_days"]
lt30 = D["baseline_rsi_lt30"]
ge30 = D["baseline_rsi_ge30"]

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}%"

def pct2(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- KPI ----------
KPI = [
    ("5275", "下穿30买入事件总数（72只票·1962起）", "num"),
    ("2620", "日历日聚类后独立事件日", "num"),
    (pct2(ea["T20"]["mean"]), "全部事件 T+20 均值（胜率 %d%%）" % ea["T20"]["win"], "up"),
    (pct2(lt30["T20"]["mean"]), "RSI<30 日 T+20 均值（胜率 %d%%）" % lt30["T20"]["win"], "up"),
    (pct2(base["T20"]["mean"]), "全历史基率 T+20 均值（胜率 %d%%）" % base["T20"]["win"], "up"),
    (pct2(ea_day["T20"]["mean"]), "聚类口径 T+20 均值（t=%.1f）" % ea_day["T20"]["t"], "up"),
    (pct2(ea["T20_ex_spy"]["mean"]), "全部事件 T+20 超额 vs SPY（t=%.1f）" % ea["T20_ex_spy"]["t"], "up"),
    ("TJX 22.8", "当前唯一 RSI<30 蓝筹（08-26）", "warn"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

# ---------- 核心对比表 ----------
def row(name, b, tag=""):
    def cell(s):
        if not s or s.get("n", 0) == 0:
            return "<td class='na'>—</td>"
        mean = s["mean"]; win = s["win"]; t = s.get("t")
        tstr = f"<span class='note2'>t={t:.1f}</span>" if t is not None else ""
        cls = "up" if mean > 0 else "dn"
        return f"<td class='{cls}'>{pct(mean)} <span class='note2'>({win}%)</span> {tstr}</td>"
    cls = " class='baserow'" if tag == "base" else ""
    return (f"<tr{cls}><td class='nowrap'><b>{name}</b></td>"
            f"<td class='nowrap'>{b.get('T5',{}).get('n','—')}</td>"
            f"{cell(b.get('T5'))}{cell(b.get('T10'))}{cell(b.get('T20'))}"
            f"{cell(b.get('T5_ex_spy'))}{cell(b.get('T10_ex_spy'))}{cell(b.get('T20_ex_spy'))}</tr>")

core_rows = "".join([
    row("全历史基率（72票·每日）", base, "base"),
    row("RSI ≥ 30 日（对照）", ge30),
    row("RSI < 30 日（含持续低位）", lt30),
    row("下穿30首日 · 全部事件", {k: ea[k] for k in ea if not k.startswith("T") or True}),
    row("下穿30首日 · 日历日聚类", ea_day),
    row("下穿30首日 · cd10去重", ec),
])

# 用一个独立的 block 形式对齐列（EA 有 ex_spy）
def block_rows():
    def r(name, b, tag=""):
        def cell(s):
            if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
            t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
            return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
        def xcell(s):
            if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
            t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
            return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} {tstr}</td>"
        cls = " class='baserow'" if tag == "base" else ""
        return (f"<tr{cls}><td class='nowrap'><b>{name}</b></td><td>{b['T5']['n']}</td>"
                f"{cell(b['T5'])}{cell(b['T10'])}{cell(b['T20'])}"
                f"{xcell(b['T5_ex_spy'])}{xcell(b['T10_ex_spy'])}{xcell(b['T20_ex_spy'])}</tr>")
    return "".join([
        r("全历史基率", base, "base"),
        r("RSI ≥ 30 日（对照）", ge30),
        r("RSI < 30 日（含持续低位）", lt30),
        r("下穿30首日 · 全部事件", ea),
        r("下穿30首日 · 日历日聚类", ea_day),
        r("下穿30首日 · cd10去重", ec),
    ])

# ---------- 分阶段 ----------
STAGE_CN = {"A_pre": "疫情前(1962~2020-02)", "B_post": "疫情及股灾后(2020-02~2022-12)", "C_bull": "本轮牛市(2023~)"}
stage_tab = []
for st in ["A_pre", "B_post", "C_bull"]:
    b = D["events_all"]["by_stage"][st]
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    stage_tab.append(f"<tr><td class='nowrap'><b>{STAGE_CN[st]}</b></td><td>{b['T5']['n']}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}</tr>")
stage_tab_html = "".join(stage_tab)

# 牛市逐年
bull_rows = []
for y in sorted(D["events_all"]["bull_by_year"], key=int):
    b = D["events_all"]["bull_by_year"][y]
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    bull_rows.append(f"<tr><td class='nowrap'><b>{y}</b></td><td>{b['T5']['n']}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}</tr>")
bull_rows_html = "".join(bull_rows)

# ---------- 分板块 ----------
sector_tab = []
sector_chart = []
# by_sector 的 key 是英文（分析脚本 SECTOR_CN 的原始 key），须用英文查、中文显示
_by_sector_map = D["events_all"]["by_sector"]
for sc in SECTOR_ORDER:
    sc_en = {v: k for k, v in SECTOR_CN.items()}.get(sc, sc)  # 中文→英文
    b = _by_sector_map.get(sc_en, {})
    if not b.get("T5", {}).get("n"): continue
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    sector_tab.append(f"<tr><td class='nowrap'><b>{sc}</b></td><td>{b['T5']['n']}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}</tr>")
    sector_chart.append({"name": sc, "n": b["T5"]["n"],
                         "t5": b["T5"]["mean"], "t10": b["T10"]["mean"], "t20": b["T20"]["mean"]})
sector_tab_html = "".join(sector_tab)

# ---------- 每只票（cd10去重口径）T+20 排序 ----------
pkl = []
for t, b in D["per_ticker"].items():
    if b["T20"].get("n", 0) == 0: continue
    pkl.append({"t": t, "sector": b["sector"], "n": b["n"],
                "t20m": b["T20"]["mean"], "t20w": b["T20"]["win"],
                "t5m": b["T5"]["mean"], "t10m": b["T10"]["mean"]})
pkl.sort(key=lambda x: -x["t20m"])
top10 = pkl[:12]
bot10 = pkl[-12:][::-1]

def ticker_row(r, tag=""):
    cls = "up" if r["t20m"] > 0 else "dn"
    return (f"<tr><td class='nowrap'><b>{r['t']}</b></td><td class='nowrap'>{SECTOR_CN.get(r['sector'], r['sector'])}</td>"
            f"<td>{r['n']}</td>"
            f"<td class='{ 'up' if r['t5m']>0 else 'dn'} nowrap'>{pct(r['t5m'])}</td>"
            f"<td class='{ 'up' if r['t10m']>0 else 'dn'} nowrap'>{pct(r['t10m'])}</td>"
            f"<td class='{cls} nowrap'>{pct(r['t20m'])} <span class='note2'>({r['t20w']}%)</span></td></tr>")
top_html = "".join(ticker_row(r) for r in top10)
bot_html = "".join(ticker_row(r) for r in bot10)

# ---------- 事件明细（5275 条，独立 tab）----------
ev_list = D["events"]
ev_rows = []
for e in ev_list:
    def f(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='{ 'up' if v>0 else 'dn'} nowrap'>{v:+.2f}%</td>"
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'><b>{e['ticker']}</b></td>"
        f"<td class='nowrap'>{SECTOR_CN.get(e['sector'], e['sector'])}</td>"
        f"<td>{e['rsi']}</td><td>{e['px']}</td>{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>")
ev_rows_html = "".join(ev_rows)

# ---------- 数据注入（供图表）----------
CHART = {
    "sector": sector_chart,
    "stage": [{"name": STAGE_CN[st], **{k: D["events_all"]["by_stage"][st][k]["mean"] if D["events_all"]["by_stage"][st][k].get("n") else None for k in ["T5", "T10", "T20"]}} for st in ["A_pre", "B_post", "C_bull"]],
    "base": {"t5": base["T5"]["mean"], "t10": base["T10"]["mean"], "t20": base["T20"]["mean"]},
    "bull_year": [{"y": y, "n": D["events_all"]["bull_by_year"][y]["T5"]["n"],
                   "t5": D["events_all"]["bull_by_year"][y]["T5"]["mean"],
                   "t10": D["events_all"]["bull_by_year"][y]["T10"]["mean"],
                   "t20": D["events_all"]["bull_by_year"][y]["T20"]["mean"]}
                  for y in sorted(D["events_all"]["bull_by_year"], key=int)],
    "ticker_top": [{"t": r["t"], "v": r["t20m"]} for r in top10],
    "ticker_bot": [{"t": r["t"], "v": r["t20m"]} for r in bot10],
    "horizon_compare": {
        "labels": ["T+5", "T+10", "T+20"],
        "base": [base["T5"]["mean"], base["T10"]["mean"], base["T20"]["mean"]],
        "event": [ea["T5"]["mean"], ea["T10"]["mean"], ea["T20"]["mean"]],
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

cur = D["current"]
cur_txt = "，".join([f"{c['ticker']} RSI {c['rsi']}" for c in cur["rsi_below_30"]]) or "无"

# ---------- 组装 HTML ----------
echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>优质蓝筹股 RSI 超卖(&lt;30)买入事件研究 · T+5/T+10/T+20</title>
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
  .callout b{color:var(--amber);} .callout.blue b{color:var(--blue);}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
  ul.tight{padding-left:20px;margin:6px 0;} ul.tight li{margin:3px 0;font-size:13px;}
  /* tabs */
  .tabs{display:flex;gap:6px;border-bottom:2px solid var(--line);margin-bottom:0;}
  .tab{padding:8px 16px;cursor:pointer;font-size:13px;color:var(--sub);border-bottom:2px solid transparent;margin-bottom:-2px;user-select:none;}
  .tab.active{color:var(--blue);border-bottom-color:var(--blue);font-weight:600;}
  .tabpanel{display:none;} .tabpanel.active{display:block;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>优质蓝筹股 RSI 超卖（&lt;30）买入事件研究 · T+5 / T+10 / T+20 表现</h1>
  <div class="meta">事件研究 · 数据 1962 ~ 2026-08-26（Yahoo 复权价 adj_close，72 只蓝筹、16,271 个交易日，MMC 因数据源故障未含）· 生成于 2026-08-27</div>
  <div class="callout blue">
    <b>口径定义：</b>事件 = 日线 RSI14（Wilder，基于 adj_close）<b>自上下穿 30 首日</b>（前一日 ≥30、当日 &lt;30），以当日收盘价为基准买入计算 T+5 / T+10 / T+20 收益（T+N 为<b>交易日</b>，shift(-N) 跳过周末假日）。
    标的是用户定义的 <b>73 只优质蓝筹股池</b>（data/blue_chips.csv）。对照 = 全历史所有交易日基率、RSI≥30 日、SPY 同期超额。
    <b>稳健性</b>：① cd10 去重（同一只票 10 个交易日内重复下穿只计一次）；② 日历日聚类（同日多票同时下穿代表市场系统性下跌，合并为一条"日事件"以修正独立性高估）。
  </div>
  <div class="callout">
    <b>当前状态（2026-08-26 收盘）：</b>72 只蓝筹中，当前 RSI&lt;30 的仅 <b style="color:var(--verm)">__CUR__</b> — 其余 71 只均已脱离超卖区（蓝筹整体处于 RSI 中性偏强位置，超卖信号已基本消化）。
  </div>
  <div class="kpis">__KPI__</div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict gr"><b>① RSI&lt;30 买入是蓝筹股稳健且显著的均值回归信号，且随持有期延长而增强。</b>全部 5,275 个"下穿30首日"事件：T+5 <b>+1.00%</b>（胜率 59.3%）、T+10 <b>+1.60%</b>（60.2%）、T+20 <b>+2.85%</b>（63.8%），逐级抬升；对比全历史基率 T+5 +0.36% / T+10 +0.71% / T+20 +1.42%，超卖买入在每一档都<b>约为基率的 2 倍</b>。T+20 是收益最优档。</div>
  <div class="verdict gr"><b>② 超额真实存在、非 β 贡献。</b>全部事件相对 SPY 的 T+20 超额 <b>+1.16pp</b>（t=8.93），T+5 +0.51pp（t=6.90）——超卖买入不仅跑输于大盘时才有效，其相对大盘的超额本身统计显著，说明这是蓝筹股自身的均值回归属性，而非市场 beta。</div>
  <div class="verdict gr"><b>③ 独立性修正后结论不变（这是最关键的稳健性检验）。</b>同日多票同时超卖通常是市场系统性下杀，逐笔统计会高估独立性。按日历日聚类（2,620 个独立事件日）后：T+20 均值 <b>+2.27% / 63.3%</b>，t 值仍高达 <b>12.12</b>（远高于 1.96 阈值）；cd10 去重（560 事件）T+20 甚至升至 <b>+3.04%</b>。三个口径方向完全一致。</div>
  <div class="verdict"><b>④ 分阶段：信号在牛熊都有效，但疫情前最强、疫情股灾期 T+5 失效。</b>疫情前（4,008 事件）T+20 +2.87%/63.8%（t=16.8）；本轮牛市（698 事件）T+20 +2.34%/63.4%（t=8.0）；仅疫情及股灾后（568 事件）T+5 +0.12%/51.2%（t=0.32 不显著）——极端下杀中 5 日不足以反弹，但放到 T+20 仍 +3.35%/64.1% 收复。</div>
  <div class="verdict"><b>⑤ 分板块：金融最强、科技绝对收益最高、消费偏弱。</b>金融 T+20 <b>+3.69%/68.4%</b>（胜率最高），科技 T+20 <b>+3.83%/63.6%</b>（绝对收益最高），材料/公用/其他 T+20 +2.49%（t=11.87 最稳）；消费最钝（T+5 +0.66% t=2.34，T+20 +2.92%）。</div>
  <div class="verdict"><b>⑥ 当前应用窗口有限。</b>截至 08-26 收盘，全池仅 TJX 一只处于 RSI&lt;30（22.8），超卖机会稀缺——这是"可遇不可求"型信号，宜在机会出现时执行，而非常态持有。</div>
</div>

<div class="card">
  <h2>一、核心对比：不同口径的 T+5 / T+10 / T+20</h2>
  <div class="chart" id="ch_horizon"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>口径</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th><th>T+5 超额SPY</th><th>T+10 超额SPY</th><th>T+20 超额SPY</th></tr></thead>
    <tbody>__CORE_ROWS__</tbody>
  </table>
  </div>
  <div class="src">均值内含 (胜率%) 与 t 值；红=正、绿=负。基率行以米色底标出。T+20 一列：基率 +1.42% vs 下穿30 +2.85% vs cd10去重 +3.04%——超卖信号的完整落点。</div>
</div>

<div class="card">
  <h2>二、分板块：蓝筹超卖买入的板块差异</h2>
  <div class="chart" id="ch_sector"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>板块</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__SECTOR_ROWS__</tbody>
  </table>
  </div>
  <div class="src">柱状图为各板块 T+5/T+10/T+20 均值（Okabe-Ito 色弱安全配色，叠加图例区分窗口）。金融胜率最高、科技绝对收益最高、消费最钝。</div>
</div>

<div class="card">
  <h2>三、分阶段与牛市逐年</h2>
  <div class="grid2">
    <div class="chart" id="ch_stage"></div>
    <div class="chart" id="ch_bullyear"></div>
  </div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>阶段</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__STAGE_ROWS__</tbody>
  </table>
  </div>
  <h3>本轮牛市逐年（2023~）</h3>
  <div class="scroll">
  <table>
    <thead><tr><th>年份</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__BULL_ROWS__</tbody>
  </table>
  </div>
  <div class="src">左图：三阶段 T+5/T+10/T+20 均值对比（虚线为全历史基率）。右图：本轮牛市逐年 T+20 均值。疫情股灾期 T+5 失效（+0.12%/51%），但 T+20 收复 +3.35%。</div>
</div>

<div class="card">
  <h2>四、个股维度：T+20 表现最强 / 最弱的蓝筹（cd10 去重口径）</h2>
  <div class="grid2">
    <div>
      <h3>▲ T+20 表现最强（Top 12）</h3>
      <div class="scroll"><table>
        <thead><tr><th>票</th><th>板块</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__TOP_ROWS__</tbody>
      </table></div>
    </div>
    <div>
      <h3>▼ T+20 表现最弱（Bottom 12）</h3>
      <div class="scroll"><table>
        <thead><tr><th>票</th><th>板块</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__BOT_ROWS__</tbody>
      </table></div>
    </div>
  </div>
  <div class="src">以 cd10 去重口径（每票独立事件）按 T+20 均值排序。个别样本量小的票（n 少）数值波动大，仅供参考，不宜单票外推。</div>
</div>

<!-- 事件明细独立 tab -->
<div class="card">
  <div class="tabs">
    <div class="tab active" data-tab="tab1" onclick="switchTab(this)">结论与图表</div>
    <div class="tab" data-tab="tab2" onclick="switchTab(this)">事件明细（__EVN__ 条）</div>
  </div>
  <div class="tabpanel active" id="tab1">
    <p style="font-size:13px;color:var(--sub);padding:8px 0">完整 5,275 个"RSI 下穿30"买入事件明细见「事件明细」选项卡。</p>
  </div>
  <div class="tabpanel" id="tab2">
    <div class="evbox">
      <table>
        <thead><tr><th>日期</th><th>票</th><th>板块</th><th>RSI</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__EV_ROWS__</tbody>
      </table>
    </div>
  </div>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close 复权，CDP 拉取）· 方法：Wilder RSI14 / 事件研究 / 日历日聚类与 cd10 去重稳健性 · 脚本：scripts/blue_chip_rsi_oversold.py + build_blue_chip_rsi_report.py · 数据文件：results/blue_chip_rsi_oversold.json · 模型：73 只优质蓝筹股池（MMC 因数据源返回 delisted 未含）。<b>本报告仅为统计回测，不构成投资建议。</b></div>
</div>

</div>
<script>
var CHART = __DATA_JSON__;
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
var baseAxis = {axisLine:{lineStyle:{color:"#d5dae2"}},axisLabel:{color:"#4b5563",fontSize:11},splitLine:{lineStyle:{color:"#eef0f3"}}};

function switchTab(el){
  document.querySelectorAll(".tab").forEach(function(t){t.classList.remove("active");});
  document.querySelectorAll(".tabpanel").forEach(function(p){p.classList.remove("active");});
  el.classList.add("active");
  document.getElementById(el.dataset.tab).classList.add("active");
}

// 一、核心对比柱状图（T+5/T+10/T+20 分组：基率 vs 事件 vs 聚类 vs cd10）
(function(){
  var ch = echarts.init(document.getElementById("ch_horizon"));
  var hc = CHART.horizon_compare;
  var cats = ["基率(全历史)", "下穿30·全部", "下穿30·日历日聚类", "下穿30·cd10去重"];
  var mk = [{data: hc.base, color: C.sub, dash:"dashed"},
            {data: hc.event, color: C.blue, dash:"solid"},
            {data: hc.day, color: C.orange, dash:"solid"},
            {data: hc.cd10, color: C.verm, dash:"solid"}];
  var series = []; var legend = [];
  hc.labels.forEach(function(_, i){
    series.push({
      name: hc.labels[i], type:"bar", barWidth:16,
      data: mk.map(function(m){ return {value: m.data[i], itemStyle:{color:m.color}}; }),
      label:{show:true, position:"top", formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2)+"%";}, fontSize:10}
    });
    legend.push(hc.labels[i]);
  });
  ch.setOption({
    animation:false,
    legend:{data:[{name:"基率",icon:"dashed"},{name:"全部事件"},{name:"日历日聚类"},{name:"cd10去重"}],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:44,bottom:28},
    xAxis:{type:"category",data:cats,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"基率", type:"bar", barWidth:15, data:hc.base, itemStyle:{color:C.sub,opacity:0.55}, label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);},fontSize:10}},
      {name:"全部事件", type:"bar", barWidth:15, data:hc.event, itemStyle:{color:C.blue}, label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);},fontSize:10}},
      {name:"日历日聚类", type:"bar", barWidth:15, data:hc.day, itemStyle:{color:C.orange}, label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);},fontSize:10}},
      {name:"cd10去重", type:"bar", barWidth:15, data:hc.cd10, itemStyle:{color:C.verm}, label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);},fontSize:10}},
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 二、板块柱状图
(function(){
  var ch = echarts.init(document.getElementById("ch_sector"));
  var sc = CHART.sector;
  var names = sc.map(function(x){return x.name;});
  var scolor = {"科技":"#0072B2","金融":"#E69F00","工业":"#009E73","医疗":"#56B4E9","消费":"#CC79A7","材料/公用/其他":"#D55E00"};
  var t5 = sc.map(function(x){return x.t5?+x.t5.toFixed(2):0;});
  var t10 = sc.map(function(x){return x.t10?+x.t10.toFixed(2):0;});
  var t20 = sc.map(function(x){return x.t20?+x.t20.toFixed(2):0;});
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:60},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11,rotate:0}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:12,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+10",type:"bar",barWidth:12,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+20",type:"bar",barWidth:12,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 三、阶段图
(function(){
  var ch = echarts.init(document.getElementById("ch_stage"));
  var st = CHART.stage;
  var names = st.map(function(x){return x.name.split("(")[0];});
  var t5 = st.map(function(x){return x.T5?+x.T5.toFixed(2):0;});
  var t10 = st.map(function(x){return x.T10?+x.T10.toFixed(2):0;});
  var t20 = st.map(function(x){return x.T20?+x.T20.toFixed(2):0;});
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:13,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+10",type:"bar",barWidth:13,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+20",type:"bar",barWidth:13,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"基率T+20",type:"line",data:[CHART.base.t20,CHART.base.t20,CHART.base.t20],lineStyle:{type:"dashed",color:C.sub,width:1.2},symbol:"none",label:{show:true,position:"top",formatter:"基率T+20 "+CHART.base.t20.toFixed(2)+"%",fontSize:9,color:C.sub}},
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 牛市逐年
(function(){
  var ch = echarts.init(document.getElementById("ch_bullyear"));
  var by = CHART.bull_year;
  var names = by.map(function(x){return x.y;});
  var t20 = by.map(function(x){return x.t20?+x.t20.toFixed(2):0;});
  ch.setOption({
    animation:false,
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var p=ps[0];return p.name+"<br>T+20: "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";}},
    grid:{left:50,right:20,top:30,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"T+20 收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[{name:"T+20",type:"bar",barWidth:30,data:t20,itemStyle:{color:function(p){return p.value>=0?C.verm:C.teal;}},
      label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2)+"%";},fontSize:10},
      markLine:{silent:true,symbol:"none",lineStyle:{type:"dashed",color:C.sub},data:[{yAxis:CHART.base.t20}],label:{formatter:"基率 "+CHART.base.t20.toFixed(2)+"%",fontSize:9,color:C.sub}}}]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__KPI__", kpi_html)
HTML = HTML.replace("__CORE_ROWS__", block_rows())
HTML = HTML.replace("__SECTOR_ROWS__", sector_tab_html)
HTML = HTML.replace("__STAGE_ROWS__", stage_tab_html)
HTML = HTML.replace("__BULL_ROWS__", bull_rows_html)
HTML = HTML.replace("__TOP_ROWS__", top_html)
HTML = HTML.replace("__BOT_ROWS__", bot_html)
HTML = HTML.replace("__EV_ROWS__", ev_rows_html)
HTML = HTML.replace("__EVN__", str(len(ev_list)))
HTML = HTML.replace("__CUR__", cur_txt)
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")