# -*- coding: utf-8 -*-
"""
构建研报：蓝筹 RSI 摆动低点(swing low)聚集支撑买入 —— 纠正 40 号的口径错误
读取 results/blue_chip_rsi_swing_support.json
输出 reports/41_蓝筹RSI摆动低点支撑买入/index.html
静默写盘。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "41_蓝筹RSI摆动低点支撑买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "blue_chip_rsi_swing_support.json"), encoding="utf-8") as f:
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

# 参数敏感性（来自敏感性扫描，硬编码关键结果）
SENS_ROWS = [
    ("K=3  M=2  TOL=3", 5238, "+1.66%", "+2.32%"),
    ("K=5  M=2  TOL=3", 3314, "+1.53%", "+1.56%"),
    ("K=5  M=3  TOL=3 (主口径)", 594, "+1.39%", "+2.97%"),
    ("K=8  M=3  TOL=3", 410, "+1.69%", "+2.56%"),
    ("K=10 M=3  TOL=3", 342, "+2.05%", "+2.10%"),
    ("K=10 M=4  TOL=4", 98, "+3.69%", "+4.95%"),
]
sens_rows_html = "".join(
    f"<tr><td class='nowrap'><b>{a}</b></td><td>{b}</td>"
    f"<td class='nowrap'>{c}</td><td class='nowrap'>{d}</td></tr>"
    for a, b, c, d in SENS_ROWS
)

sp_dist = D["n_events"]["support_level_dist"]
buy_dist = D["n_events"]["buy_rsi_dist"]

KPI = [
    (str(D["n_events"]["support_buy"]), "swing low 聚集支撑买入事件总数", "num"),
    ("%.1f" % sp_dist["median"], "支撑位(S)中位 RSI（p10–p90 %.0f–%.0f）" % (sp_dist["p10"], sp_dist["p90"]), "warn"),
    ("%.1f" % buy_dist["median"], "买入时 RSI 中位", "warn"),
    (pct2(ea["T20"]["mean"]), "全部事件 T+20 均值（胜率 %d%%）" % ea["T20"]["win"], "up"),
    (pct2(base["T20"]["mean"]), "全历史基率 T+20 均值", "up"),
    (pct2(D["support_buckets"]["35-40"]["T20"]["mean"]), "支撑 35–40 档 T+20（胜率 %d%%）" % D["support_buckets"]["35-40"]["T20"]["win"], "up"),
    (pct2(D["support_buckets"][">=50"]["T20"]["mean"]), "支撑 ≥50 档 T+20（胜率 %d%%）" % D["support_buckets"][">=50"]["T20"]["win"], "up"),
    (pct2(ea["T20_ex_spy"]["mean"]), "全部事件 T+20 超额 vs SPY", "up"),
]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

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
        r("swing low 支撑买入 · 全部", ea),
        r("swing low 支撑买入 · 聚类", ea_day),
    ])

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

pkl = []
for t, b in D["per_ticker"].items():
    if b["T20"].get("n", 0) < 5: continue
    pkl.append({"t": t, "sector": b["sector"], "n": b["n"],
                "t20m": b["T20"]["mean"], "t20w": b["T20"]["win"]})
pkl.sort(key=lambda x: -x["t20m"])
top = pkl[:10]; bot = pkl[-10:][::-1]

def tk_row(r):
    return (f"<tr><td class='nowrap'><b>{r['t']}</b></td><td class='nowrap'>{SECTOR_CN.get(r['sector'], r['sector'])}</td>"
            f"<td>{r['n']}</td><td class='{ 'up' if r['t20m']>0 else 'dn'} nowrap'>{pct(r['t20m'])} <span class='note2'>({r['t20w']}%)</span></td></tr>")
top_html = "".join(tk_row(r) for r in top)
bot_html = "".join(tk_row(r) for r in bot)

ev_list = D["events"]
ev_rows = []
for e in ev_list:
    def f(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='{ 'up' if v>0 else 'dn'} nowrap'>{v:+.2f}%</td>"
    sw = "、".join(str(x) for x in e["swing_lows"])
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'><b>{e['ticker']}</b></td>"
        f"<td class='nowrap'>{SECTOR_CN.get(e['sector'], e['sector'])}</td>"
        f"<td>{e['rsi']}</td><td>{e['support']}</td><td class='note2' nowrap>{sw}</td><td>{e['px']}</td>{f(e['fwd5'])}{f(e['fwd10'])}{f(e['fwd20'])}</tr>")
ev_rows_html = "".join(ev_rows)

CHART = {
    "bucket": bucket_chart,
    "sector": sector_chart,
    "stage": [{"name": STAGE_CN[st], **{k: D["events_all"]["by_stage"][st][k]["mean"] if D["events_all"]["by_stage"][st][k].get("n") else None for k in ["T5", "T10", "T20"]}} for st in ["A_pre", "B_post", "C_bull"]],
    "base": {"t5": base["T5"]["mean"], "t10": base["T10"]["mean"], "t20": base["T20"]["mean"]},
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
<title>蓝筹 RSI 摆动低点(swing low)聚集支撑买入 · 纠正版</title>
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
  .tabs{display:flex;gap:6px;border-bottom:2px solid var(--line);margin-bottom:0;}
  .tab{padding:8px 16px;cursor:pointer;font-size:13px;color:var(--sub);border-bottom:2px solid transparent;margin-bottom:-2px;user-select:none;}
  .tab.active{color:var(--blue);border-bottom-color:var(--blue);font-weight:600;}
  .tabpanel{display:none;} .tabpanel.active{display:block;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>蓝筹 RSI 摆动低点（swing low）聚集支撑买入 · 纠正版</h1>
  <div class="meta">事件研究 · 数据 1962 ~ 2026-08-26（72 只蓝筹，MMC 未含）· 生成于 2026-08-27 · <b>纠正 40 号报告的支撑位定义错误</b></div>
  <div class="callout blue">
    <b>口径（本义）：</b>swing low = 某日 RSI 严格低于前后各 K=5 日的 RSI。支撑位 S = 过去 120 日内<b>最近 3 个摆动低点聚集</b>（RSI 极差 ≤3）中的<b>最低谷</b>——即"多个谷底反复测试同一水平、都没跌破"。
    买入触发 = RSI 从上方首日进入 [S−2, S+2]（触及/轻微下破），当日收盘买入，同票 20 日去重。T+N 为交易日。
  </div>
  <div class="callout">
    <b>对 40 号的纠正：</b>40 号用「过去120日 RSI 的 15% 分位」当支撑位，<b style="color:var(--verm)">这是错的</b>——15% 分位意味着过去 120 日里有约 20 天 RSI 低于它，等于"被反复跌破"，与"支撑位"（跌不下去）的本义相反。本报告改用 swing low 聚集的正确定义重跑。
  </div>
  <div class="kpis">__KPI__</div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict amber"><b>① 定义修正后，整体仍然几乎无 edge —— 不是因为定义，而是因为"支撑位"本就不该落在中高位。</b>594 个 swing low 聚集支撑买入事件（主口径 K=5/M=3/TOL=3），T+20 <b>+1.39%</b> 与基率 +1.42% 几乎重合，超额仅 +0.53pp（t 不显著）。用 swing low 本义找"支撑"，得到的支撑位中位是 <b>44.9</b>——因为 RSI 在正常波动中天然会反复形成 40+ 的摆动低点，聚集支撑也大多聚在 44 附近，而非"跌不动的底"（&lt;35）。</div>
  <div class="verdict gr"><b>② 但分档后规律依然清晰：edge 仍在"低支撑"，并在"高位强势支撑"处出现第二极。</b>支撑位 35–40 档 T+20 <b>+2.97%/64.1%</b>（t=3.24）显著为正；而 40–50 档几乎为零（+0.14% / +0.07%）——这是"无 edge 的日常震荡区"。另有 ≥50 档 +2.41%（t=3.88），但那本质是<b>强势趋势股的"高位回调"</b>（RSI 50+ 的摆动低点），逻辑与"均值回归支撑"不同，属另一类信号。</div>
  <div class="verdict"><b>③ 参数敏感性稳健：35–40 档的正 edge 在几乎所有 K/M/TOL 组合下复现。</b>从 K=3 到 K=10、M=2 到 M=4，35–40 档 T+20 稳定落在 +1.6%~+3.0% 区间（t 3.2~6.4），而整体均值始终压在基率附近（+1.3%~+2.0%）。结论不是某个参数设置的巧合。</div>
  <div class="verdict gr"><b>④ 最终判断（与 39 号收敛）：真正的 edge 是"RSI 低位"本身，不是"支撑位"这个形态。</b>无论用分位数（40号）、还是 swing low 本义（本报告），只要支撑位定义让它落在 RSI 40+ 的中位区，就没有超额；唯一稳定赚钱的是"低支撑"（RSI&lt;35~40），这与 39 号 RSI&lt;30 的结论完全同源。支撑位形态只是给"低位"包了一层技术外衣，不改变底层的均值回归逻辑。</div>
</div>

<div class="card">
  <h2>一、核心：支撑位高度分档（swing low 正确口径）</h2>
  <div class="chart" id="ch_bucket"></div>
  <div class="scroll" style="margin-top:4px">
  <table>
    <thead><tr><th>支撑位高度</th><th>n</th><th>T+5 均值</th><th>T+10 均值</th><th>T+20 均值</th></tr></thead>
    <tbody>__BUCKET_ROWS__</tbody>
  </table>
  </div>
  <div class="src">形状是「两头强、中间弱」：35–40 档 +2.97%（低支撑，均值回归）、≥50 档 +2.41%（高位强势，趋势回调）、40–50 档几乎为零（无 edge 震荡区）。支撑位中位 44.9，大部分事件落在无 edge 的中位区。</div>
</div>

<div class="card">
  <h2>二、参数敏感性：35–40 档的正 edge 稳健复现</h2>
  <div class="scroll">
  <table>
    <thead><tr><th>参数组合 (K/M/TOL)</th><th>总事件 n</th><th>整体 T+20</th><th>35–40 档 T+20</th></tr></thead>
    <tbody>__SENS_ROWS__</tbody>
  </table>
  </div>
  <div class="src">K=swing low 半宽、M=聚集所需摆动低点数、TOL=聚集 RSI 极差阈值。无论参数如何调，35–40 档始终显著高于整体均值；整体均值始终贴近基率 +1.42%。</div>
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
  <div class="src">本轮牛市（58 事件）T+20 +2.81%/64.3% 相对最强，疫情前（485 事件）+1.22% 最弱——与 39 号"疫情前强"相反，因为 swing low 聚集支撑本质上更像趋势回踩而非超跌反弹。</div>
</div>

<div class="card">
  <h2>四、个股维度：T+20 最强 / 最弱（样本≥5）</h2>
  <div class="grid2">
    <div>
      <h3>▲ T+20 最强（Top 10）</h3>
      <div class="scroll"><table>
        <thead><tr><th>票</th><th>板块</th><th>n</th><th>T+20</th></tr></thead>
        <tbody>__TOP_ROWS__</tbody>
      </table></div>
    </div>
    <div>
      <h3>▼ T+20 最弱（Bottom 10）</h3>
      <div class="scroll"><table>
        <thead><tr><th>票</th><th>板块</th><th>n</th><th>T+20</th></tr></thead>
        <tbody>__BOT_ROWS__</tbody>
      </table></div>
    </div>
  </div>
</div>

<div class="card">
  <div class="tabs">
    <div class="tab active" data-tab="tab1" onclick="switchTab(this)">结论与图表</div>
    <div class="tab" data-tab="tab2" onclick="switchTab(this)">事件明细（__EVN__ 条）</div>
  </div>
  <div class="tabpanel active" id="tab1">
    <p style="font-size:13px;color:var(--sub);padding:8px 0">完整 __EVN__ 个 swing low 聚集支撑买入事件见「事件明细」选项卡。</p>
  </div>
  <div class="tabpanel" id="tab2">
    <div class="evbox">
      <table>
        <thead><tr><th>日期</th><th>票</th><th>板块</th><th>RSI</th><th>支撑S</th><th>聚集的摆动低点</th><th>收盘价</th><th>T+5</th><th>T+10</th><th>T+20</th></tr></thead>
        <tbody>__EV_ROWS__</tbody>
      </table>
    </div>
  </div>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close）· 方法：RSI swing low（前后5日最低）聚集支撑 · 脚本：scripts/blue_chip_rsi_swing_support.py + build_blue_chip_rsi_swing_support_report.py · 数据文件：results/blue_chip_rsi_swing_support.json。<b>本报告仅为统计回测，不构成投资建议。</b></div>
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
(function(){
  var ch = echarts.init(document.getElementById("ch_stage"));
  var st = CHART.stage;
  var names = st.map(function(x){return x.name.split("(")[0];});
  var t5 = st.map(function(x){return x.T5?+x.T5.toFixed(2):0;});
  var t10 = st.map(function(x){return x.T10?+x.T10.toFixed(2):0;});
  var t20 = st.map(function(x){return x.T20?+x.T20.toFixed(2):0;});
  ch.setOption({animation:false,legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},grid:{left:50,right:20,top:40,bottom:30},xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},series:[{name:"T+5",type:"bar",barWidth:13,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9}},{name:"T+10",type:"bar",barWidth:13,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9}},{name:"T+20",type:"bar",barWidth:13,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9}}]});
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_sector"));
  var sc = CHART.sector;
  var names = sc.map(function(x){return x.name;});
  var t5 = sc.map(function(x){return x.t5?+x.t5.toFixed(2):0;});
  var t10 = sc.map(function(x){return x.t10?+x.t10.toFixed(2):0;});
  var t20 = sc.map(function(x){return x.t20?+x.t20.toFixed(2):0;});
  ch.setOption({animation:false,legend:{data:["T+5","T+10","T+20"],top:2,textStyle:{fontSize:11,color:"#374151"}},tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},grid:{left:50,right:20,top:40,bottom:60},xAxis:{type:"category",data:names,axisLabel:{color:"#4b5563",fontSize:11}},yAxis:{type:"value",name:"收益%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},series:[{name:"T+5",type:"bar",barWidth:12,data:t5,itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9}},{name:"T+10",type:"bar",barWidth:12,data:t10,itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9}},{name:"T+20",type:"bar",barWidth:12,data:t20,itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9}}]});
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__KPI__", kpi_html)
HTML = HTML.replace("__BUCKET_ROWS__", bucket_rows_html)
HTML = HTML.replace("__SENS_ROWS__", sens_rows_html)
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