# -*- coding: utf-8 -*-
"""
构建研报：纳指区间(2025-10~2026-02) 优质蓝筹 RSI 低买高卖 T5/T10 专项
读取 results/blue_chip_rsi_reversion_window.json
输出 reports/50_纳指区间RSI低买高卖/index.html
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "50_纳指区间RSI低买高卖")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "blue_chip_rsi_reversion_window.json"), encoding="utf-8") as f:
    D = json.load(f)
with open(os.path.join(RES, "pair_complete_open.json"), encoding="utf-8") as f:
    PC = json.load(f)

SECTOR_CN = {
    "Technology": "科技", "Financials": "金融", "Industrials": "工业",
    "Healthcare": "医疗", "Consumer": "消费", "Materials_Utilities_Other": "材料/公用/其他",
}
SECTOR_COLOR = {
    "科技": "#0072B2", "金融": "#E69F00", "工业": "#009E73",
    "医疗": "#56B4E9", "消费": "#CC79A7", "材料/公用/其他": "#D55E00",
}
SECTOR_ORDER = ["科技", "金融", "工业", "医疗", "消费", "材料/公用/其他"]

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"
def pct2(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- 便捷访问 ----------
LB = D["low_buy"]       # {'L30': {block, day_clustered}, 'L35': ...}
HS = D["high_sell"]     # {'H70': ..., 'H65': ...}
PA = D["paired_low30_sell70"]
B = D["benchmark"]

L30, L35 = LB["L30"]["block"], LB["L35"]["block"]
L30d, L35d = LB["L30"]["day_clustered"], LB["L35"]["day_clustered"]
H70, H65 = HS["H70"]["block"], HS["H70"]["block"] if False else HS["H70"]["block"]
H65b = HS["H65"]["block"]
P_RET = PA["round_ret_stats"]

# ---------- 回合数据 ----------
complete = PC["complete"]
openp = PC["open"]
c_ret = np.array([r["ret"] for r in complete]) if complete else np.array([])
o_ret = np.array([r["ret"] for r in openp]) if openp else np.array([])

def arr_stats(a):
    if len(a) == 0:
        return {"n": 0}
    return {
        "n": len(a), "mean": round(float(a.mean()), 3),
        "median": round(float(np.median(a)), 3),
        "win": round(float((a > 0).mean()) * 100, 1),
        "min": round(float(a.min()), 3), "max": round(float(a.max()), 3),
    }

CR = arr_stats(c_ret)
OR = arr_stats(o_ret)

# ---------- KPI ----------
def kcell(block, k):
    s = block.get(k)
    if not s or s.get("n", 0) == 0:
        return "—"
    cls = "up" if s["mean"] > 0 else "dn"
    t = s.get("t")
    tstr = f" <span class='note2'>(t={t:.1f})</span>" if t is not None else ""
    return f"<span class='{cls}'>{s['mean']:+.2f}%</span>{tstr} <span class='note2'>n={s['n']}</span>"

KPI = [
    (f"{L30['T5']['n']}", "RSI<30 低买信号（cd10）", "num"),
    (f"{L30['T5'].get('mean') or 0:+.2f}%", "L30 低买 T+5 均值", "up" if (L30["T5"].get("mean") or 0) > 0 else "dn"),
    (f"{L30['T10'].get('mean') or 0:+.2f}%", "L30 低买 T+10 均值", "up" if (L30["T10"].get("mean") or 0) > 0 else "dn"),
    (f"{H65['T5'].get('mean') or 0:+.2f}%", "H65 高卖 T+5 均值", "up" if (H65["T5"].get("mean") or 0) > 0 else "dn"),
    (f"{H65['T10'].get('mean') or 0:+.2f}%", "H65 高卖 T+10 均值", "up" if (H65["T10"].get("mean") or 0) > 0 else "dn"),
    (f"{CR['n']}", "完整 低买→高卖 回合数", "num"),
    (f"{CR['mean']}%", "完整回合均值(胜率%d%%)" % CR["win"], "up" if CR["mean"] > 0 else "dn"),
    (f"{OR['n']}", "未平仓至区间末(2/27)", "num"),
    (f"{OR['mean']}%", "未平仓均值(胜率%d%%)" % OR["win"], "up" if OR["mean"] > 0 else "dn"),
    (f"{B['QQQ_window']}%", "QQQ 区间涨跌", "up" if B["QQQ_window"] > 0 else "dn"),
]
if len(KPI) > 8:
    KPI = KPI[:10]
kpi_html = "".join(
    f"<div class='kpi'><div class='num {cls}'>{n}</div><div class='lab'>{lab}</div></div>"
    for n, lab, cls in KPI
)

# ---------- 核心信号表 ----------
def cell(s):
    if not s or s.get("n", 0) == 0:
        return "<td class='na'>—</td>"
    t = s.get("t"); tstr = f"<span class='note2'>t={t:.1f}</span>" if t is not None else ""
    cls = "up" if s["mean"] > 0 else "dn"
    return (f"<td class='{cls} nowrap'>{pct(s['mean'])} "
            f"<span class='note2'>胜率{s['win']}%</span> {tstr}</td>")
def row(name, b, tag=""):
    cls = " class='baserow'" if tag == "base" else ""
    return (f"<tr{cls}><td class='nowrap'><b>{name}</b></td>"
            f"<td>{b.get('T5',{}).get('n','—')}</td>{cell(b.get('T5'))}{cell(b.get('T10'))}"
            f"<td>{b.get('T5_exspy',{}).get('n','—')}</td>{cell(b.get('T5_exspy'))}{cell(b.get('T10_exspy'))}"
            f"<td>{b.get('T5_exqqq',{}).get('n','—')}</td>{cell(b.get('T5_exqqq'))}{cell(b.get('T10_exqqq'))}</tr>")

vwin = np.mean(np.array([x["ret"] for x in complete]) > 0) * 100 if complete else 0

def core_row_L(name, b, tag=""):
    return row(name, b, tag)

core_rows = "".join([
    core_row_L("RSI<30 低买信号（下穿30）", L30),
    core_row_L("RSI<35 低买信号（下穿35）", L35),
    core_row_L("RSI>70 高卖信号（上穿70）", H70),
    core_row_L("RSI>65 高卖信号（上穿65）", H65b),
    # 基准
    row("区间全部交易日（等权基线）", {"T5": B["all_days_ew"]["T5"], "T5_exspy": B["all_days_ew"]["T5_exspy"], "T10": B["all_days_ew"]["T10"], "T10_exspy": B["all_days_ew"]["T10_exspy"], "T5_exqqq": B["all_days_ew"]["T5_exqqq"], "T10_exqqq": B["all_days_ew"]["T10_exqqq"]}, "base"),
])

# ---------- 配对循环表 ----------
def pr_run(r):
    cls = "up" if r["ret"] > 0 else "dn"
    return (f"<tr><td class='nowrap'>{r['ticker']}</td><td class='nowrap'>{r['buy']}</td>"
            f"<td class='nowrap'>{r['sell'][:10]}</td><td>{r['hold']}</td>"
            f"<td class='{cls} nowrap'>{r['ret']:+.2f}%</td></tr>")
pair_tab = "".join(
    [f"<tr><th>代码</th><th>买入日</th><th>卖出日</th><th>持有(交易日)</th><th>收益</th></tr>"] +
    [pr_run(r) for r in sorted(complete, key=lambda x: -x["ret"])] +
    [f"<tr><td colspan='5' style='background:#fbfcfe;color:var(--sub)'>—— 未平仓至区间末的买入（{len(openp)} 笔，不含高卖）——</td></tr>"] +
    [pr_run(r) for r in sorted(openp, key=lambda x: -x["ret"])]
)

# ---------- 低买事件明细 ----------
ev_buy = D["detail"]["low_buy_L35"]
def dcell(v):
    if v is None: return "<td class='na'>—</td>"
    return f"<td class='{'up' if v>0 else 'dn'} nowrap'>{v:+.2f}%</td>"
ev_buy_rows = "".join(
    f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'><b>{e['ticker']}</b></td>"
    f"<td class='nowrap'>{SECTOR_CN.get(e['sector'], e['sector'])}</td>"
    f"<td>{e['rsi']}</td><td>{e['px']}</td>{dcell(e['fwd5'])}{dcell(e['fwd10'])}</tr>"
    for e in sorted(ev_buy, key=lambda x: x["date"])
)
ev_sell = D["detail"]["high_sell_H65"]
ev_sell_rows = "".join(
    f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'><b>{e['ticker']}</b></td>"
    f"<td class='nowrap'>{SECTOR_CN.get(e['sector'], e['sector'])}</td>"
    f"<td>{e['rsi']}</td><td>{e['px']}</td>{dcell(e['fwd5'])}{dcell(e['fwd10'])}</tr>"
    for e in sorted(ev_sell, key=lambda x: x["date"])
)

# ---------- 图表数据 ----------
CHART = {
    "signal": [
        {"name": "L30 低买", "t5": L30["T5"]["mean"], "t10": L30["T10"]["mean"]},
        {"name": "L35 低买", "t5": L35["T5"]["mean"], "t10": L35["T10"]["mean"]},
        {"name": "H70 高卖", "t5": H70["T5"]["mean"], "t10": H70["T10"]["mean"]},
        {"name": "H65 高卖", "t5": H65b["T5"]["mean"], "t10": H65b["T10"]["mean"]},
    ],
    "base_t5": B["all_days_ew"]["T5"]["mean"],
    "base_t10": B["all_days_ew"]["T10"]["mean"],
    "pairs": [{"t": r["ticker"], "ret": r["ret"]} for r in sorted(complete, key=lambda x: -x["ret"])],
    "qqq": {"label": "QQQ", "val": B["QQQ_window"]},
    "spy": {"label": "SPY", "val": B["SPY_window"]},
    "buyhold": {"label": "个股等权Buy&Hold", "val": B["buy_hold_ew_window"]["mean"]},
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

window = D["meta"]["window"]
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>纳指区间RSI低买高卖专项 · {window[0]}~{window[1]}</title>
__ECHARTS__
<style>
  :root{{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;--amber:#b45309;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}}
  .wrap{{max-width:1220px;margin:0 auto;}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}}
  h1{{font-size:21px;margin-bottom:4px;}}
  .meta{{color:var(--sub);font-size:12.5px;margin-bottom:14px;}}
  h2{{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}}
  h3{{font-size:13.5px;margin:14px 0 6px;color:#374151;}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-top:14px;}}
  .kpi{{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
  .kpi .num{{font-size:18px;font-weight:700;}}
  .kpi .num.up{{color:var(--verm);}} .kpi .num.dn{{color:var(--teal);}} .kpi .num.warn{{color:var(--amber);}}
  .kpi .lab{{color:var(--sub);font-size:12px;margin-top:2px;}}
  table{{width:100%;border-collapse:collapse;font-size:12px;}}
  th{{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}}
  td{{padding:5px 7px;border-bottom:1px solid #f0f1f3;}}
  td.nowrap{{white-space:nowrap;}}
  .note2{{color:var(--sub);font-size:11px;font-weight:400;}}
  td.up{{color:var(--verm);font-weight:600;white-space:nowrap;}}
  td.dn{{color:var(--teal);font-weight:600;white-space:nowrap;}}
  td.na{{color:#c3c8cf;white-space:nowrap;}}
  tr.baserow td{{background:#fbf7ee;}}
  .scroll{{overflow-x:auto;}}
  .evbox{{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:8px;}}
  .evbox table th{{position:sticky;top:0;z-index:2;}}
  .chart{{width:100%;height:420px;}}
  .callout{{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}}
  .callout.blue{{border-color:#cfe0f5;background:#f0f6fd;}}
  .chartgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
  @media(max-width:860px){{.chartgrid{{grid-template-columns:1fr;}}}}
  .badge{{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:600;}}
  .badge.verm{{background:#fdeaea;color:var(--verm);}} .badge.teal{{background:#e6f6ef;color:var(--teal);}}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>纳指区间 · 蓝筹股 RSI 低买高卖 专项</h1>
  <div class="meta">区间 {window[0]} ~ {window[1]}（5 个月）｜标的：blue_chips 池 {D["meta"]["n_tickers_loaded"]} 只优质蓝筹｜
  RSI14 (Wilder, adj_close) 全历史前推｜对照：QQQ / SPY / 个股等权 Buy&Hold</div>
  <div class="kpis">{kpi_html}</div>
  <div class="callout blue"><b>背景</b>：区间内 QQQ 几乎横盘（+0.8%），SPY +2.9%，蓝筹等权 Buy&amp;Hold +7.5%。
    市场整体缺乏单边趋势，是验证"摆动策略"（低买高卖）是否优于躺平的天然试验场。</div>
</div>

<div class="card">
  <h2>一、信号收益总览（事件后 T5 / T10）</h2>
  <div class="scroll">
  <table>
    <tr><th>口径</th>
        <th>n</th><th>T+5 均值</th><th>T+10 均值</th>
        <th>n*</th><th>T+5 超额SPY</th><th>T+10 超额SPY</th>
        <th>n*</th><th>T+5 超额QQQ</th><th>T+10 超额QQQ</th></tr>
    {core_rows}
  </table>
  </div>
  <p class="note2" style="margin-top:6px">n* 为超额对照样本数。低买=下穿阈值当日收盘买入持有 N 日；高卖=上穿阈值当日收盘卖出后仍持有观察 N 日。
  超额 = 个股 N 日收益 − 对应指数 N 日收益。信号按 ticker 分组、相邻同类信号间隔≥10交易日去重。</p>
  <div class="callout"><b>解读</b>：
    <ul style="margin:6px 0 0 16px">
      <li><b>RSI&lt;30 低买</b>：T+5 均值 −0.38%（胜率50%）、T+10 −0.12%，<b>无显著正收益</b>，t≈0。说明该区间蓝筹深跌抄底并不占优。</li>
      <li><b>RSI&lt;35 低买</b>：T+5 +0.18%、T+10 +0.96%（胜率53.4%，t=1.44），略微为正但不显著。</li>
      <li><b>RSI&gt;70 高卖</b>：卖出后 T+5 −0.37%、T+10 +0.07%，<b>卖出并非避开下跌</b>——强势股卖出后仍可能继续涨。</li>
      <li><b>结论雏形</b>：以固定 T+N 持有看，低买信号在此区间没有稳定超额；真正有效的部分是<b>内生的"低买→高卖"长持仓循环</b>（见下节），而非 5/10 日短持。</li>
    </ul>
  </div>
</div>

<div class="card">
  <h2>二、连续"低买→高卖"配对循环</h2>
  <p>规则：同票 RSI 首次下穿 30 当日收盘买入，持有直至 RSI 上穿 70 当日收盘卖出（循环）。区间内未出现高卖的持仓记入"未平仓"。</p>
  <div class="chartgrid">
    <div><div id="c1" class="chart"></div></div>
    <div><div id="c2" class="chart"></div></div>
  </div>
  <h3>统计</h3>
  <div class="scroll">
  <table>
    <tr><th>类别</th><th>笔数</th><th>均值</th><th>中位数</th><th>胜率</th><th>最差</th><th>最好</th><th>平均持有(交易日)</th></tr>
    <tr><td class='nowrap'><b>完整回合（含真实高卖）</b></td><td>{CR["n"]}</td>
        <td class="{'up' if CR['mean']>0 else 'dn'} nowrap">{CR["mean"]:+.2f}%</td>
        <td>{CR["median"]:+.2f}%</td><td>{CR["win"]:.0f}%</td>
        <td>{CR["min"]:+.2f}%</td><td>{CR["max"]:+.2f}%</td>
        <td>{np.mean([x["hold"] for x in complete]):.0f}</td></tr>
    <tr><td class='nowrap'><b>未平仓至区间末（仅低买）</b></td><td>{OR["n"]}</td>
        <td class="{'up' if OR['mean']>0 else 'dn'} nowrap">{OR["mean"]:+.2f}%</td>
        <td>{OR["median"]:+.2f}%</td><td>{OR["win"]:.0f}%</td>
        <td>{OR["min"]:+.2f}%</td><td>{OR["max"]:+.2f}%</td>
        <td>—</td></tr>
    <tr class='baserow'><td class='nowrap'><b>对照：个股等权 Buy&amp;Hold</b></td><td>{B["buy_hold_ew_window"]["n"]}</td>
        <td class="{'up' if B['buy_hold_ew_window']['mean']>0 else 'dn'} nowrap">{B["buy_hold_ew_window"]["mean"]:+.2f}%</td>
        <td>{B["buy_hold_ew_window"]["median"]:+.2f}%</td><td>{B["buy_hold_ew_window"]["win"]:.0f}%</td>
        <td>—</td><td>—</td><td>103</td></tr>
  </table>
  </div>
  <div class="callout"><b>解读</b>：21 笔完整回合平均 +{CR["mean"]:.1f}%、胜率 {CR["win"]:.0f}%（全部盈利）
    ——但这与<b>区间本身是 V 型震荡、带买入时点偏逢低</b>密切相关，且持仓 40~50 交易日、比 T5/T10 长得多。
    未平仓的 24 笔（区间未出现 >70 高卖）平均 −{abs(OR["mean"]):.1f}%，说明<b>并非每次低买都对</b>，风险集中在没等到高卖的持仓上。</div>

  <h3>完整回合明细（21 笔）＋ 未平仓明细（{len(openp)} 笔）</h3>
  <div class="evbox"><table>{pair_tab}</table></div>
</div>

<div class="card">
  <h2>三、单次信号事件明细</h2>
  <h3>RSI&lt;35 低买信号（{len(ev_buy)} 笔）</h3>
  <div class="evbox"><table>
    <tr><th>日期</th><th>代码</th><th>板块</th><th>RSI</th><th>收盘</th><th>T+5</th><th>T+10</th></tr>
    {ev_buy_rows}
  </table></div>
  <h3 style="margin-top:16px">RSI&gt;65 高卖信号（{len(ev_sell)} 笔）</h3>
  <div class="evbox"><table>
    <tr><th>日期</th><th>代码</th><th>板块</th><th>RSI</th><th>收盘</th><th>T+5</th><th>T+10</th></tr>
    {ev_sell_rows}
  </table></div>
</div>

</div>
<script>
const CHART = {json.dumps(CHART, ensure_ascii=False)};
// 图1：信号 T5/T10 分组柱状
echarts.init(document.getElementById('c1')).setOption({{
  title:{{text:'信号 T+5/T+10 均值对比',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{}},
  legend:{{data:['T+5','T+10'],top:24}},
  grid:{{left:44,right:14,top:64,bottom:28}},
  xAxis:{{type:'category',data:CHART.signal.map(s=>s.name)}},
  yAxis:{{type:'value',name:'收益%'}},
  series:[
    {{name:'T+5',type:'bar',data:CHART.signal.map(s=>s.t5),itemStyle:{{color:'#0072B2'}}}},
    {{name:'T+10',type:'bar',data:CHART.signal.map(s=>s.t10),itemStyle:{{color:'#D55E00'}}}},
  ]
}});
// 图2：完整回合收益横向条形
const pr = CHART.pairs.slice().reverse();
echarts.init(document.getElementById('c2')).setOption({{
  title:{{text:'完整低买→高卖回合收益',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{}},
  grid:{{left:56,right:40,top:40,bottom:20}},
  xAxis:{{type:'value',name:'%'}},
  yAxis:{{type:'category',data:pr.map(p=>p.t),axisLabel:{{fontSize:10}}}},
  series:[{{type:'bar',data:pr.map(p=>p.ret),
    itemStyle:{{color:function(p){{return p.value>=0?'#D55E00':'#009E73';}}}},
    label:{{show:true,position:'right',formatter:function(p){{return p.value.toFixed(1)+'%';}},fontSize:10}}}}]
}});
</script>
</body>
</html>
"""
html = html.replace("__ECHARTS__", echarts)

# 修正回合统计持有天数——未平仓不改
out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out} ({os.path.getsize(out)} bytes)")