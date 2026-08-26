#!/usr/bin/env python3
"""VIX 低位 × SPY 事件研究 — HTML 仪表盘渲染。
数据: results/vix_low_spy.json + results/vix_low_spy_events.csv
渲染: scripts/render_dashboard.py + scripts/dashboard_template.html (模块化看板)
输出: reports/vix_low_spy_dashboard/index.html
"""
import os, sys, json
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
from render_dashboard import build_dashboard_data, render_dashboard  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "results", "vix_low_spy.json"), encoding="utf-8"))
EV = os.path.join(ROOT, "results", "vix_low_spy_events.csv")
OUT_DIR = os.path.join(ROOT, "reports", "vix_low_spy_dashboard")
os.makedirs(OUT_DIR, exist_ok=True)

meta = D["meta"]
base = D["base_fwd"]
by_day = D["by_day"]
by_start = D["by_start"]
sig = D["sig"]
rs15 = D["run_stats"]["15"]
rs13 = D["run_stats"]["13"]
rs12 = D["run_stats"]["12"]
life15 = D["life_tab_15"]
bk15 = D["break_to20"]["15"]


def fnum(x, nd=2):
    if x is None:
        return "--"
    return f"{x:,.{nd}f}"


# ---------- 图表数据准备 ----------
# 月度 VIX / SPY 序列 (主图)
v = pd.read_csv(os.path.join(ROOT, "data", "vix", "VIX, 1D.csv"), parse_dates=["date"])
s = pd.read_csv(os.path.join(ROOT, "data", "spy", "SPY, 1D.csv"), parse_dates=["date"])
m = v.merge(s, on="date", suffixes=("_vix", "_spy"))[["date", "close_vix", "close_spy"]]
m["ym"] = m["date"].dt.strftime("%Y-%m")
mm = m.groupby("ym").agg(vix=("close_vix", "mean"), spy=("close_spy", "last")).reset_index()
monthly = {
    "labels": mm["ym"].tolist(),
    "vix": [round(x, 2) for x in mm["vix"].tolist()],
    "spy": [round(x, 1) for x in mm["spy"].tolist()],
    "low15": [1 if x < 15 else 0 for x in mm["vix"].tolist()],  # 低位月标记
}
# 近12个月日度
recent = m.tail(252).copy()
recent_daily = {
    "labels": recent["date"].dt.strftime("%m-%d").tolist(),
    "vix": [round(x, 2) for x in recent["close_vix"].tolist()],
    "spy": [round(x, 1) for x in recent["close_spy"].tolist()],
}

# 前瞻收益对比表 (持有期 × 低位日/非低位日/基线)
rows_fwd = []
for k in [5, 10, 20, 60, 120]:
    kk = f"T{k}"
    ev = by_day["15"][kk]
    ctrl_t = sig["15"][kk]
    rows_fwd.append({
        "k": kk,
        "low_mean": ev["mean"], "low_win": ev["win"], "low_n": ev["n"],
        "notlow_mean": ctrl_t["ctrl_mean"], "notlow_win": None,
        "diff": ctrl_t["diff_mean"], "t": ctrl_t["t"],
        "base_mean": base[kk]["mean"], "base_win": base[kk]["win"],
    })
# 非低位胜率 = (base_win*N - low_win*n_low)/(N - n_low) 精确计算
N = meta["n_days"]
for r in rows_fwd:
    k = int(r["k"][1:])
    base_w = base[r["k"]]["win"] / 100
    n_all = N - k
    n_low = r["low_n"]
    wins_all = base_w * n_all
    wins_low = r["low_win"] / 100 * n_low
    r["notlow_win"] = round((wins_all - wins_low) / max(n_all - n_low, 1) * 100, 1) if n_all > n_low else None

# 区间长度分布
lens = [r["days"] for r in D["run_detail"]["15"]]
len_buckets = [(1, 3, "1-3天"), (4, 10, "4-10天"), (11, 20, "11-20天"), (21, 40, "21-40天"), (41, 80, "41-80天"), (81, 9999, ">80天")]
len_dist = []
for lo, hi, lab in len_buckets:
    vals = [x for x in lens if lo <= x <= hi]
    len_dist.append({"lab": lab, "n": len(vals), "pct": round(len(vals) / len(lens) * 100, 1)})

# 条件剩余寿命矩阵 (供表格与热力)
life_rows = []
for dd in [1, 3, 5, 10, 20, 40]:
    life_rows.append({"d": dd, **{f"k{k}": life15[str(dd)][str(k)] for k in [3, 5, 10, 20, 40, 60]}})

# 回归速度桶
bk_lens = D["run_detail"]["15"]  # 非直接; 用 break_to20 概览即可

# 近12个月 VIX 低位情况 (最近一次 <15 区间)
cur_low_days = meta["cur_run_days_under15"]

JS = {
    "monthly": monthly,
    "recent_daily": recent_daily,
    "rows_fwd": rows_fwd,
    "len_dist": len_dist,
    "life_rows": life_rows,
    "meta": meta,
    "bk15": bk15,
    "by_day15_T120": by_day["15"]["T120"],
    "sig15": sig["15"],
}

# ---------- custom_html 模块 ----------
def echarts_html(div_id, option_js, height=340):
    return f"""
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<div id="bt-custom-{div_id}" style="width:100%;height:{height}px;"></div>
<script>
(function(){{
  const el = document.getElementById('bt-custom-{div_id}');
  if (!el) return;
  const start = function() {{
    if (!el.offsetWidth || !el.offsetHeight) return;   // 容器不可见时跳过
    const chart = echarts.init(el);
    const opt = {option_js};
    chart.setOption(opt);
    window.addEventListener('resize', function(){{ chart.resize(); }});
  }};
  if (typeof echarts !== 'undefined') {{ start(); }}
  else {{
    const t0 = Date.now();
    const iv = setInterval(function() {{
      if (typeof echarts !== 'undefined') {{ clearInterval(iv); start(); }}
      else if (Date.now() - t0 > 20000) {{ clearInterval(iv); }}
    }}, 100);
  }}
}})();
</script>"""

# 主图: VIX 月均 + SPY 月收 (双轴, 低位月底色)
mark_area_data = [
    [{"xAxis": lab, "itemStyle": {"color": "rgba(30,102,214,0.07)"}}, {"xAxis": lab}]
    for lab, low in zip(monthly["labels"], monthly["low15"]) if low
]
main_chart = echarts_html("main", f"""
{{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['VIX 月均', 'SPY 月收'], top: 0 }},
  grid: {{ left: 52, right: 60, top: 34, bottom: 42 }},
  xAxis: {{ type: 'category', data: {json.dumps(monthly['labels'])}, axisLabel: {{ fontSize: 9.5, interval: 23 }} }},
  yAxis: [
    {{ type: 'value', name: 'VIX', min: 0, axisLabel: {{ fontSize: 10 }} }},
    {{ type: 'value', name: 'SPY', axisLabel: {{ fontSize: 10, formatter: v => v/100 + 'k' }} }}
  ],
  dataZoom: [{{ type: 'inside', start: 65 }}, {{ type: 'slider', start: 65, height: 16, bottom: 2 }}],
  series: [
    {{ name: 'VIX 月均', type: 'line', data: {json.dumps(monthly['vix'])}, smooth: true, showSymbol: false,
       lineStyle: {{ width: 1.6, color: '#1e66d6' }}, itemStyle: {{ color: '#1e66d6' }},
       markArea: {{ silent: true, itemStyle: {{ color: 'rgba(30,102,214,0.07)' }}, data: {json.dumps(mark_area_data)} }},
       markLine: {{ silent: true, symbol: 'none', data: [ {{ yAxis: 15, label: {{ formatter: '15 低位线', color: '#b45309', fontSize: 10 }}, lineStyle: {{ color: '#b45309', type: 'dashed' }} }} ] }} }},
    {{ name: 'SPY 月收', type: 'line', yAxisIndex: 1, data: {json.dumps(monthly['spy'])}, smooth: true, showSymbol: false,
       lineStyle: {{ width: 1.6, color: '#e03131' }}, itemStyle: {{ color: '#e03131' }} }}
  ]
}}
""", height=400)

# 前瞻收益对比: 平均收益(红涨绿跌) + 胜率
fwd_chart = echarts_html("fwd", f"""
{{
  tooltip: {{ trigger: 'axis', valueFormatter: v => (v===null||v===undefined) ? '--' : v + '%' }},
  legend: {{ data: ['低位日 均值', '非低位日 均值', '基线 均值', '低位日 胜率(右轴)'], top: 0 }},
  grid: {{ left: 52, right: 60, top: 34, bottom: 36 }},
  xAxis: {{ type: 'category', data: ['T+5','T+10','T+20','T+60','T+120'], axisLabel: {{ fontSize: 11 }} }},
  yAxis: [
    {{ type: 'value', name: '平均收益 %', axisLabel: {{ fontSize: 10 }} }},
    {{ type: 'value', name: '胜率 %', min: 50, max: 90, axisLabel: {{ fontSize: 10, formatter: "{{v}}%" }} }}
  ],
  series: [
    {{ name: '低位日 均值', type: 'bar', data: {json.dumps([r['low_mean'] for r in rows_fwd])},
       itemStyle: {{ color: p => p.value >= 0 ? '#e03131' : '#0aa06e' }}, barGap: '20%' }},
    {{ name: '非低位日 均值', type: 'bar', data: {json.dumps([r['notlow_mean'] for r in rows_fwd])},
       itemStyle: {{ color: p => p.value >= 0 ? '#dd8b8b' : '#8fc7b0' }} }},
    {{ name: '基线 均值', type: 'line', data: {json.dumps([r['base_mean'] for r in rows_fwd])},
       lineStyle: {{ width: 1.4, color: '#9aa2ab', type: 'dashed' }}, symbol: 'circle', symbolSize: 6, itemStyle: {{ color: '#9aa2ab' }} }},
    {{ name: '低位日 胜率(右轴)', type: 'bar', yAxisIndex: 1, data: {json.dumps([r['low_win'] for r in rows_fwd])},
       itemStyle: {{ color: 'rgba(30,102,214,0.45)' }} }}
  ]
}}
""", height=340)

# 区间长度分布 + 条件剩余寿命
len_chart_data = [{"value": d["n"], "pct": d["pct"]} for d in len_dist]
len_chart = echarts_html("len", f"""
{{
  tooltip: {{ trigger: 'axis', formatter: ps => ps[0].axisValue + '：' + ps[0].value + ' 段 (' + ps[0].data.pct + '%)' }},
  grid: {{ left: 48, right: 20, top: 30, bottom: 36 }},
  xAxis: {{ type: 'category', data: {json.dumps([d['lab'] for d in len_dist])}, axisLabel: {{ fontSize: 10 }} }},
  yAxis: {{ type: 'value', name: '区间段数', axisLabel: {{ fontSize: 10 }} }},
  series: [{{ type: 'bar', data: {json.dumps(len_chart_data)},
    barWidth: '58%',
    itemStyle: {{ color: p => p.dataIndex === 0 ? '#e03131' : (p.dataIndex <= 2 ? '#b45309' : '#1e66d6') }},
    label: {{ show: true, position: 'top', fontSize: 10, formatter: p => p.value + '段' }} }}]
}}
""", height=300)

# 近12个月 VIX/SPY
recent_chart = echarts_html("recent", f"""
{{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['VIX', 'SPY'], top: 0 }},
  grid: {{ left: 52, right: 60, top: 34, bottom: 36 }},
  xAxis: {{ type: 'category', data: {json.dumps(recent_daily['labels'])}, axisLabel: {{ fontSize: 9, interval: 19 }} }},
  yAxis: [
    {{ type: 'value', name: 'VIX', axisLabel: {{ fontSize: 10 }} }},
    {{ type: 'value', name: 'SPY', axisLabel: {{ fontSize: 10 }} }}
  ],
  series: [
    {{ name: 'VIX', type: 'line', data: {json.dumps(recent_daily['vix'])}, smooth: true, showSymbol: false,
       lineStyle: {{ width: 1.8, color: '#1e66d6' }},
       markLine: {{ silent: true, symbol: 'none', data: [ {{ yAxis: 15, label: {{ formatter: '15', color: '#b45309', fontSize: 9 }}, lineStyle: {{ color: '#b45309', type: 'dashed' }} }} ] }}
    }},
    {{ name: 'SPY', type: 'line', yAxisIndex: 1, data: {json.dumps(recent_daily['spy'])}, smooth: true, showSymbol: false,
       lineStyle: {{ width: 1.6, color: '#e03131' }} }}
  ]
}}
""", height=300)

# 条件剩余寿命表 (HTML 表格)
def life_table_html():
    rows_html = ""
    for r in life_rows:
        cells = "".join(
            f'<td class="{"bt-custom-hl" if r[f"k{k}"] and r[f"k{k}"] >= 50 else ""}">{fnum(r[f"k{k}"], 1)}%</td>'
            for k in [3, 5, 10, 20, 40, 60]
        )
        rows_html += f"<tr><td><b>已持续 {r['d']} 天</b></td>{cells}</tr>"
    return f"""
<style>
  .bt-custom-life {{ font-size: 12px; }}
  .bt-custom-life table {{ width: 100%; border-collapse: collapse; }}
  .bt-custom-life th {{ background: #f3f5f8; padding: 6px 8px; border-bottom: 2px solid #e5e7eb; font-weight: 600; text-align: left; white-space: nowrap; }}
  .bt-custom-life td {{ padding: 5px 8px; border-bottom: 1px solid #f0f1f3; white-space: nowrap; }}
  .bt-custom-life .bt-custom-hl {{ color: #e03131; font-weight: 700; }}
</style>
<div class="bt-custom-life">
<table>
  <thead><tr><th>已持续天数 ↓ / 还能再维持 →</th><th>≥3 天</th><th>≥5 天</th><th>≥10 天</th><th>≥20 天</th><th>≥40 天</th><th>≥60 天</th></tr></thead>
  <tbody>{rows_html}</tbody>
</table>
</div>"""

# 文本模块
conclusion_text = f"""
**核心结论**

**Q1 · VIX 低位时 SPY 表现如何（1995-01 ~ 2026-08，SPY 收盘口径，持有 N 个交易日）**

- **胜率优势在长持有期，均值优势不明显**：VIX<15 低位日 T+20 胜率 {by_day['15']['T20']['win']}%（基线 {base['T20']['win']}%）、T+120 胜率 {by_day['15']['T120']['win']}%（基线 {base['T120']['win']}%）；但均值 T+20 为 {by_day['15']['T20']['mean']:+.2f}%（对照非低位日 {rows_fwd[2]['notlow_mean']:+.2f}%），**短期（T+5/10）低位日反而略弱**（diff {rows_fwd[0]['diff']:+.2f}~{rows_fwd[1]['diff']:+.2f}pp），T+120 低位日显著更强（diff {rows_fwd[4]['diff']:+.2f}pp，Welch t={rows_fwd[4]['t']}）。
- **阈值越低长持效果越好**：VIX<12 低位日 T+120 胜率 {by_day['12']['T120']['win']}%、均值 {by_day['12']['T120']['mean']:+.2f}%（diff +{sig['12']['T120']['diff_mean']:.2f}pp，t={sig['12']['T120']['t']}）。

**Q2 · VIX 低位能持续多久**

- **中位数仅 3 天，均值 13.5 天，P90=32 天，最长 192 天**（1994-12 起）。41% 的区间只维持 1-3 天即告结束；30.1% 的交易日处于 VIX<15。
- **自我强化**：已持续 3 天时，再维持 ≥5 天概率 {life15['3']['5']}%、≥10 天 {life15['3']['10']}%、≥20 天 {life15['3']['20']}%；已持续 10 天 → ≥10 天概率升至 {life15['10']['10']}%。
- **均值回归慢**：从 VIX<15 区间起点到 VIX 首次站上 20，中位 {bk15['median']} 个交易日（约 3 个月）、均值 {bk15['mean']} 天、P25={bk15['p25']} 天。低波动可以按季度规划，而非按周。

**风险提示**：低波动结束往往伴随波动率跳升——VIX 从 15 向 20+ 回升的途中，历史上是回撤高发窗口。当前 VIX 16.0（36.7% 分位），已脱离 <15 低位；SPY 距历史高点 -2.0%。
"""

method_text = f"""
**口径与方法**

- **数据**：CBOE VIX 指数 + SPY ETF（Yahoo 日线，1995-01-03 ~ 2026-08-20，{meta['n_days']} 个交易日对齐）。
- **事件**：任意收盘 VIX < 阈值的交易日（<15 主口径 2395 个事件日，含区间内重叠；另有 <13 / <12 辅助口径）。
- **前瞻收益**：事件日收盘买入 → 持有 N 个交易日收盘卖出（交易日对齐，计入尾部截断），不扣任何成本/股息。
- **对照**：同持有期"非低位日"为互斥对照组，Welch 双样本 t；另以"连续低位区间起点"（独立样本）复核。
- **局限**：① 事件日样本高度重叠（同一区间内多日），独立信息量小于事件数；② 前瞻收益未计成本，且 SPY 含分红未复投；③ VIX 是"结果"而非"原因"，低波动期本身选自特定宏观环境；④ 2007 年之前 VIX 定价结构与低波动时代不同，长历史统计仅供参考。
"""

# ---------- 组装 report_data ----------
report_data = build_dashboard_data(
    trades_csv=EV,
    meta={
        "strategy_name": "VIX 低位 × SPY 事件研究",
        "symbol": "SPY",
        "start": meta["start"],
        "end": meta["end"],
        "report_kind": "event_study",
        "event_overview_mode": "both",
    },
    language="zh",
    event_overview_mode="both",
    ui_overrides={
        "tabs": [
            {"id": "overview", "label": "总览"},
            {"id": "list", "label": "事件明细"},
        ],
        "active_tab": "overview",
        "subtitle": "VIX 低位持续时间 · SPY 前瞻表现",
    },
    extra_modules=[
        {"type": "custom_html", "tab": "overview", "title": "全历史：VIX 月均与 SPY（低位月淡蓝底）", "width": "full", "html": main_chart},
        {"type": "text", "tab": "overview", "title": "核心结论", "text": conclusion_text},
        {"type": "custom_html", "tab": "overview", "title": "SPY 前瞻收益：低位日 vs 非低位日（红涨绿跌）", "width": "full", "html": fwd_chart},
        {"type": "custom_html", "tab": "overview", "title": "VIX<15 区间长度分布", "width": "half", "html": len_chart},
        {"type": "custom_html", "tab": "overview", "title": "条件剩余寿命：已持续 D 天还能再维持 ≥K 天（VIX<15）", "width": "half", "html": life_table_html()},
        {"type": "custom_html", "tab": "overview", "title": "近 12 个月：VIX 与 SPY 日线", "width": "full", "html": recent_chart},
        {"type": "text", "tab": "overview", "title": "口径、方法与局限", "text": method_text},
    ],
)

# 把事件明细表移到独立 tab "list"
for mod in report_data["modules"]:
    if mod.get("type") == "trades_table":
        mod["tab"] = "list"
        mod["title"] = "全部低位日事件明细（VIX<15，2395 条）"
        mod["subtitle"] = "每个 VIX<15 交易日为一行：事件日收盘买入，持有 20 个交易日收盘卖出（T+20 收益）"
        # 精简列
        mod["columns"] = [
            {"key": "label", "label": "事件", "format": "text"},
            {"key": "display_symbol", "label": "标的", "format": "text"},
            {"key": "entry_date", "label": "事件日", "format": "text"},
            {"key": "exit_date", "label": "卖出日(T+20)", "format": "text"},
            {"key": "pnl_pct", "label": "T+20 收益", "format": "pct"},
            {"key": "vix", "label": "当日 VIX", "format": "number"},
            {"key": "days_in_run", "label": "所在区间天数", "format": "number"},
        ]

# 移除默认 timeline 主图(性能 + 语义: 合成曲线为重叠样本累计, 不具净值含义)
report_data["modules"] = [m for m in report_data["modules"] if m.get("type") != "overview_chart"]

render_dashboard(report_data, output_path=os.path.join(OUT_DIR, "index.html"),
                 template_path=os.path.join(ROOT, "scripts", "dashboard_template.html"))
print("saved:", os.path.join(OUT_DIR, "index.html"))