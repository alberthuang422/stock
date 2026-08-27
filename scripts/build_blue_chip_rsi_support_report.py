# -*- coding: utf-8 -*-
"""
构建研报：优质蓝筹股 RSI 动态支撑位买入事件研究 —— T+5/T+10/T+20
读取 results/blue_chip_rsi_support.json
输出 reports/40_蓝筹RSI支撑位买入/index.html
静默写盘：只打印 written 路径与体积。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "40_蓝筹RSI支撑位买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "blue_chip_rsi_support.json"), encoding="utf-8") as f:
    D = json.load(f)

SECTOR_CN = {
    "Technology": "科技", "Financials": "金融", "Industrials": "工业",
    "Healthcare": "医疗", "Consumer": "消费", "Materials_Utilities_Other": "材料/公用/其他",
}
SECTOR_ORDER = ["科技", "金融", "工业", "医疗", "消费", "材料/公用/其他"]
SECTOR_EN = {v: k for k, v in SECTOR_CN.items()}

ea = D["events_all"]["block"]
ea_day = D["events_all"]["day_clustered"]
base = D["baseline_all_days"]

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}%"

def pct2(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- KPI ----------
sp_dist = D["n_events"]["support_level_dist"]
buy_dist = D["n_events"]["buy_rsi_dist"]
KPI = [
    (str(D["n_events"]["support_buy"]), "支撑位买入事件总数（72只票）", "num"),
    (str(D["n_events"]["day_clustered"]), "日历日聚类后独立事件日", "num"),
    (pct2(ea["T20"]["mean"]), "支撑买入 T+20 均值（胜率 %d%%）" % ea["T20"]["win"], "up"),
    (pct2(base["T20"]["mean"]), "全历史基率 T+20 均值（胜率 %d%%）" % base["T20"]["win"], "up"),
    (pct2(ea["T20_ex_spy"]["mean"]), "支撑买入 T+20 超额 vs SPY（t=%.1f）" % ea["T20_ex_spy"]["t"], "up"),
    ("%.1f" % sp_dist["median"], "支撑位中位 RSI 水平（p10–p90 %.0f–%.0f）" % (sp_dist["p10"], sp_dist["p90"]), "warn"),
    (pct2(D["support_buckets"]["<35"]["T20"]["mean"]), "支撑<35 档 T+20 均值（胜率 %d%%）" % D["support_buckets"]["<35"]["T20"]["win"], "up"),
    ("%.1f" % buy_dist["median"], "买入时 RSI 中位（≈支撑位）", "warn"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

# ---------- 核心对比表 ----------
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
        r("支撑位买入 · 全部事件", ea),
        r("支撑位买入 · 日历日聚类", ea_day),
    ])

# ---------- 支撑位高度分档（核心）----------
bucket_order = ["<35", "35-40", "40-45", "45-50", ">=50"]
bucket_rows = []
bucket_chart = []
for bk in bucket_order:
    b = D["support_buckets"][bk]
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    bucket_rows.append(f"<tr><td class='nowrap'><b>支撑位 {bk}</b></td><td>{b['T5']['n']}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}</tr>")
    bucket_chart.append({"bk": bk, "n": b["T5"]["n"],
                         "t5": b["T5"]["mean"], "t10": b["T10"]["mean"], "t20": b["T20"]["mean"]})
bucket_rows_html = "".join(bucket_rows)

# ---------- 分阶段 ----------
STAGE_CN = {"A_pre": "疫情前(1962~2020-02)", "B_post": "疫情及股灾后(2020-02~2022-12)", "C_bull": "本轮牛市(2023~)"}
stage_rows = []
for st in ["A_pre", "B_post", "C_bull"]:
    b = D["events_all"]["by_stage"][st]
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    stage_rows.append(f"<tr><td class='nowrap'><b>{STAGE_CN[st]}</b></td><td>{b['T5']['n']}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}</tr>")
stage_rows_html = "".join(stage_rows)

# ---------- 分板块 ----------
sector_rows = []
sector_chart = []
_by_sector = D["events_all"]["by_sector"]
for sc in SECTOR_ORDER:
    b = _by_sector.get(SECTOR_EN[sc], {})
    if not b.get("T5", {}).get("n"): continue
    def c(s):
        if not s or s.get("n", 0) == 0: return "<td class='na'>—</td>"
        t = s.get("t"); tstr = f" <span class='note2'>t={t:.1f}</span>" if t is not None else ""
        return f"<td class='{ 'up' if s['mean']>0 else 'dn'} nowrap'>{pct(s['mean'])} <span class='note2'>({s['win']}%)</span>{tstr}</td>"
    sector_rows.append(f"<tr><td class='nowrap'><b>{sc}</b></td><td>{b['T5']['n']}</td>{c(b['T5'])}{c(b['T10'])}{c(b['T20'])}</tr>")
    sector_chart.append({"name": sc, "n": b["T5"]["n"],
                         "t5": b["T5"]["mean"], "t10": b["T10"]["mean"], "t20": b["T20"]["mean"]})
sector_rows_html = "".join(sector_rows)

# ---------- 每只票 T+20 排序 ----------
pkl = []
for t, b in D["per_ticker"].items():
    if b["T20"].get("n", 0) < 5: continue  # 样本太少的票跳过
    pkl.append({"t": t, "sector": b["sector"], "n": b["n"],
                "t20m": b["T20"]["mean"], "t20w": b["T20"]["win"],
                "t5m": b["T5"]["mean"], "t10m": b["T10"]["mean"]})
pkl.sort(key=lambda x: -x["t20m"])
top12 = pkl[:10]
bot12 = pkl[-10:][::-1]

def ticker_row(r):
    return (f"<tr><td class='nowrap'><b>{r['t']}</b></td><td class='nowrap'>{SECTOR_CN.get(r['sector'], r['sector'])}</td>"
            f"<td>{r['n']}</td>"
            f"<td class='{ 'up' if r['t5m']>0 else 'dn'} nowrap'>{pct(r['t5m'])}</td>"
            f"<td class='{ 'up' if r['t10m']>0 else 'dn'} nowrap'>{pct(r['t10m'])}</td>"
            f"<td class='{ 'up' if r['t20m']>0 else 'dn'} nowrap'>{pct(r['t20m'])} <span class='note2'>({r['t20w']}%)</span></td></tr>")
top_html = "".join(ticker_row(r) for r in top12)
bot_html = "".join(ticker_row(r) for r in bot12)

# ---------- 事件明细 ----------
ev_list = D["events"]
ev_rows = []
for e in ev_list:
    def f(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='{ 'up' if v>0 else 'dn'} nowrap'>{v:+.2f}%</td>"
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'><b>{e['ticker']}</b></td>"
        f"<td class='nowrap'>{SECTOR_CN.get(e['sector'], e['sector'])}</td>"
        f"<td>{e['rsi']}</td><td>{e['support']}</td><td>{e['px']}</td>{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>")
ev_rows_html = "".join(ev_rows)

# ---------- 数据注入 ----------
CHART = {
    "bucket": bucket_chart,
    "sector": sector_chart,
    "stage": [{"name": STAGE_CN[st], **{k: D["events_all"]["by_stage"][st][k]["mean"] if D["events_all"]["by_stage"][st][k].get("n") else None for k in ["T5", "T10", "T20"]}} for st in ["A_pre", "B_post", "C_bull"]],
    "base": {"t5": base["T5"]["mean"], "t10": base["T10"]["mean"], "t20": base["T20"]["mean"]},
    "horizon": {
        "labels": ["T+5", "T+10", "T+20"],
        "base": [base["T5"]["mean"], base["T10"]["mean"], base["T20"]["mean"]],
        "event": [ea["T5"]["mean"], ea["T10"]["mean"], ea["T20"]["mean"]],
        "day": [ea_day["T5"]["mean"], ea_day["T10"]["mean"], ea_day["T20"]["mean"]],
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

echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>优质蓝筹股 RSI 动态支撑位买入事件研究 · T+5/T+10/T+20</title>
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
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
  ul.tight{padding-left:20px;margin:6px 0;} ul.tight li{margin:3px 0;font-size:13px;}
  .tabs{display:flex;gap:6px;border-bottom:2px solid var(--line);margin-bottom:0;}
  .tab{padding:8px 16px;cursor:pointer;font-size:13px;color:var(--sub);border-bottom:2px solid transparent;margin-bottom:-2px;user-select:none;}
  .tab.active{color:var(--blue);border-bottom-color:var(--blue);font-weight:600;}
  .tabpanel{display:none;} .tabpanel.active{display:block;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>优质蓝筹股 RSI 动态支撑位买入事件研究 · T+5 / T+10 / T+20</h1>
  <div class="meta">事件研究 · 数据 1962 ~ 2026-08-26（Yahoo 复权价 adj_close，72 只蓝筹 · 16,271 交易日，MMC 因数据源故障未含）· 生成于 2026-08-27</div>
  <div class="callout blue">
    <b>口径定义：</b>支撑位 L(t) = 过去 <b>120 交易日（约半年）RSI 的 15% 分位数</b>，<b>上限截断 55</b>（支撑位不能太高）；须满足 <b>多次触碰</b>（过去 120 日下探至 L+2 以内的段数 ≥ 2 次）且 <b>近 20 交易日（约1个月）未跌破</b>（最低 ≥ L−2）。
    <b>买入触发</b> = RSI 从上方首日进入 <b>[L−2, L+2]</b> 支撑带（触及/轻微下破，含 ±2 缓冲），当日收盘买入，同票 20 交易日去重。T+N 为交易日。
  </div>
  <div class="callout">
    <b>关键事实：</b>这个"放松条件"的框架<b style="color:var(--amber)">本身不产生超额</b>——9347 个支撑买入事件 T+20 <b>+1.45%</b> 与全历史基率 +1.42% <b>几乎完全重合</b>，超额仅 +0.52pp。真正的 edge <b>完全集中在支撑位 &lt;35 的低位档</b>（+3.36%，接近 RSI&lt;30 的效果）。
  </div>
  <div class="kpis">__KPI__</div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict amber"><b>① "支撑位附近买入"整体几乎无 edge —— 放松条件的代价是把 edge 稀释到接近零。</b>9,347 个支撑买入事件 T+5 +0.52%/T+10 +0.85%/T+20 <b>+1.45%</b>，与全历史基率（+0.36%/+0.71%/<b>+1.42%</b>）逐档几乎重合；相对 SPY 的 T+20 超额仅 <b>+0.52pp</b>（t=6.29）。日历日聚类后 T+20 +1.39%/59.3%。——对比报告 39 的 RSI&lt;30（T+20 +2.85%、超额 +1.16pp），支撑位框架把信号强度削去了大半。</div>
  <div class="verdict gr"><b>② edge 不在"支撑位"，而在"支撑位够低" —— 分档后一目了然。</b>支撑位 &lt;35 档（662 事件）T+20 <b>+3.36%/61.9%</b>（t=6.42）；而支撑位 40–45 档（3032 事件）仅 +1.31%、45–50 档 +1.19%——edge 随支撑位抬高而单调衰减。<b>支撑位框架里真正赚钱的部分，正是"RSI 低"这个底层事实，与 39 号结论完全同源。</b></div>
  <div class="verdict"><b>③ 支撑位分布决定了框架的"先天缺陷"：大多数支撑其实在中高位。</b>支撑位中位 RSI <b>43.1</b>（p10–p90 36.0–50.2），买入时 RSI 中位 43.4——半数的"支撑买入"其实发生在 RSI 40–50 的无 edge 区间。因为用 15% 分位数+上限55 定义，天然会把很多股票日常回调的 45–50 也当成"支撑"。</div>
  <div class="verdict"><b>④ 分阶段：本轮牛市支撑买入最弱。</b>疫情前 T+20 +1.65%（样本 7387）；本轮牛市仅 <b>+0.79%/52.8%</b>（t=3.54）——牛市里"回调到支撑"的均值回归幅度远弱于震荡/下行市。</div>
  <div class="verdict gr"><b>⑤ 结论：若要用支撑位框架，必须加"支撑位够低"（如 &lt;35）这个硬约束，否则就是给 RSI&lt;30 信号掺水。</b>换句话说——"放松到支撑位就买"在数据上不成立；有效的是"低的支撑位"（接近 RSI&lt;30），而不是"任意支撑位"。</div>
</div>

<div class="card">
  <h2>一、核心：支撑位高度分档 ——edge 的单调衰减</h2>
  <div class="chart" id="ch_bucket"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>支撑位高度</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__BUCKET_ROWS__</tbody>
  </table>
  </div>
  <div class="src"><b>这是本报告最核心的一张图。</b>T+20 均值从支撑位 &lt;35 的 +3.36% 一路衰减到 45–50 的 +1.19%，再略微回升至 ≥50 的 +1.50%（非单调的尾部，但均远低于 &lt;35 档）。支撑位越高的"逢低买"，越接近随机买入。</div>
</div>

<div class="card">
  <h2>二、口径对比：支撑买入 vs 全历史基率</h2>
  <div class="chart" id="ch_horizon"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>口径</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th><th>T+5 超额SPY</th><th>T+10 超额SPY</th><th>T+20 超额SPY</th></tr></thead>
    <tbody>__CORE_ROWS__</tbody>
  </table>
  </div>
  <div class="src">支撑买入整体 T+20 +1.45% 与基率 +1.42% 几乎重合；超额 +0.52pp（t=6.29）虽统计显著但经济意义微弱。</div>
</div>

<div class="card">
  <h2>三、分阶段与分板块</h2>
  <div class="grid2">
    <div class="chart" id="ch_stage"></div>
    <div class="chart" id="ch_sector"></div>
  </div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>阶段</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__STAGE_ROWS__</tbody>
  </table>
  </div>
  <h3>分板块</h3>
  <div class="scroll">
  <table>
    <thead><tr><th>板块</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__SECTOR_ROWS__</tbody>
  </table>
  </div>
  <div class="src">左图：三阶段 T+20 均值（虚线=基率）。本轮牛市 +0.79% 明显最弱。右图：分板块，科技/医疗相对较强，材料/公用最弱（+0.96%）。</div>
</div>

<div class="card">
  <h2>四、个股维度：T+20 表现最强 / 最弱（样本≥5）</h2>
  <div class="grid2">
    <div>
      <h3>▲ T+20 表现最强（Top 10）</h3>
      <div class="scroll"><table>
        <thead><tr><th>票</th><th>板块</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__TOP_ROWS__</tbody>
      </table></div>
    </div>
    <div>
      <h3>▼ T+20 表现最弱（Bottom 10）</h3>
      <div class="scroll"><table>
        <thead><tr><th>票</th><th>板块</th><th>n</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__BOT_ROWS__</tbody>
      </table></div>
    </div>
  </div>
  <div class="src">按 T+20 均值排序，仅收录每票支撑买入 ≥5 次的标的（过滤小样本噪声）。</div>
</div>

<!-- 事件明细独立 tab -->
<div class="card">
  <div class="tabs">
    <div class="tab active" data-tab="tab1" onclick="switchTab(this)">结论与图表</div>
    <div class="tab" data-tab="tab2" onclick="switchTab(this)">事件明细（__EVN__ 条）</div>
  </div>
  <div class="tabpanel active" id="tab1">
    <p style="font-size:13px;color:var(--sub);padding:8px 0">完整 __EVN__ 个"RSI 支撑位买入"事件明细见「事件明细」选项卡。</p>
  </div>
  <div class="tabpanel" id="tab2">
    <div class="evbox">
      <table>
        <thead><tr><th>日期</th><th>票</th><th>板块</th><th>RSI(买入)</th><th>支撑位</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__EV_ROWS__</tbody>
      </table>
    </div>
  </div>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close 复权，CDP 拉取）· 方法：RSI 动态支撑位（120日15%分位/上限55/缓冲±2/≥2次触碰/20日未跌破）· 脚本：scripts/blue_chip_rsi_support.py + build_blue_chip_rsi_support_report.py · 数据文件：results/blue_chip_rsi_support.json · 模型：72 只优质蓝筹股池（MMC 未含）。<b>本报告仅为统计回测，不构成投资建议。</b></div>
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

// 一、支撑位分档柱状图（核心）
(function(){
  var ch = echarts.init(document.getElementById("ch_bucket"));
  var bk = CHART.bucket;
  var names = bk.map(function(x){return x.bk;});
  var t5 = bk.map(function(x){return x.t5?+x.t5.toFixed(2):0;});
  var t10 = bk.map(function(x){return x.t10?+x.t10.toFixed(2):0;});
  var t20 = bk.map(function(x){return x.t20?+x.t20.toFixed(2):0;});
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:13,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2);}}},
      {name:"T+10",type:"bar",barWidth:13,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2);}}},
      {name:"T+20",type:"bar",barWidth:13,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2);}}},
      {name:"基率T+20",type:"line",data:[CHART.base.t20,CHART.base.t20,CHART.base.t20,CHART.base.t20,CHART.base.t20],lineStyle:{type:"dashed",color:C.sub,width:1.2},symbol:"none",label:{show:true,position:"bottom",formatter:"基率 "+CHART.base.t20.toFixed(2)+"%",fontSize:9,color:C.sub}},
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 二、口径对比
(function(){
  var ch = echarts.init(document.getElementById("ch_horizon"));
  var h = CHART.horizon;
  ch.setOption({
    animation:false,
    legend:{data:["基率","支撑买入·全部","支撑买入·聚类"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var hh="";ps.forEach(function(p){hh+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return hh;}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:h.labels,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"基率",type:"bar",barWidth:15,data:h.base,itemStyle:{color:C.sub,opacity:0.55},label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);},fontSize:10}},
      {name:"支撑买入·全部",type:"bar",barWidth:15,data:h.event,itemStyle:{color:C.blue},label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);},fontSize:10}},
      {name:"支撑买入·聚类",type:"bar",barWidth:15,data:h.day,itemStyle:{color:C.orange},label:{show:true,position:"top",formatter:function(p){return (p.value>=0?"+":"")+p.value.toFixed(2);},fontSize:10}},
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 三、阶段
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
      {name:"T+5",type:"bar",barWidth:13,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2);}}},
      {name:"T+10",type:"bar",barWidth:13,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2);}}},
      {name:"T+20",type:"bar",barWidth:13,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2);}}},
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();

// 板块
(function(){
  var ch = echarts.init(document.getElementById("ch_sector"));
  var sc = CHART.sector;
  var names = sc.map(function(x){return x.name;});
  var t5 = sc.map(function(x){return x.t5?+x.t5.toFixed(2):0;});
  var t10 = sc.map(function(x){return x.t10?+x.t10.toFixed(2):0;});
  var t20 = sc.map(function(x){return x.t20?+x.t20.toFixed(2):0;});
  ch.setOption({
    animation:false,
    legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"},formatter:function(ps){var h="<b>"+ps[0].name+"</b>";ps.forEach(function(p){h+="<br>"+p.marker+p.seriesName+": "+(p.value>=0?"+":"")+p.value.toFixed(2)+"%";});return h;}},
    grid:{left:50,right:20,top:40,bottom:60},
    xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"T+5",type:"bar",barWidth:12,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+10",type:"bar",barWidth:12,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
      {name:"T+20",type:"bar",barWidth:12,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(1);}}},
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
HTML = HTML.replace("__BUCKET_ROWS__", bucket_rows_html)
HTML = HTML.replace("__CORE_ROWS__", block_rows())
HTML = HTML.replace("__STAGE_ROWS__", stage_rows_html)
HTML = HTML.replace("__SECTOR_ROWS__", sector_rows_html)
HTML = HTML.replace("__TOP_ROWS__", top_html)
HTML = HTML.replace("__BOT_ROWS__", bot_html)
HTML = HTML.replace("__EV_ROWS__", ev_rows_html)
HTML = HTML.replace("__EVN__", str(len(ev_list)))
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")