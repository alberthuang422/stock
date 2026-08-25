# -*- coding: utf-8 -*-
"""报告33 · 蓝筹「周线MACD能量柱收敛 × 支撑位」事件研究 Dashboard 构建

读取 reports/33_周线MACD收敛支撑位回测/ 下 macd_support_stats.json + macd_support_events.csv，
按事件研究口径（平均/中位/胜率/超额/破位率）渲染 index.html（事件研究：无Sharpe/年化/回撤）。
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from render_dashboard import build_dashboard_data, render_dashboard

OUT_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "reports", "33_周线MACD收敛支撑位回测")
STATS_PATH = os.path.join(OUT_DIR, "macd_support_stats.json")
EVENTS_PATH = os.path.join(OUT_DIR, "macd_support_events.csv")
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template.html")

GROUPS = ["CVG", "POS", "NEG"]
GROUP_DESC = {
    "CVG": "周线MACD柱收敛(≥3根递减,起点水上)",
    "POS": "当周柱水上(非收敛)",
    "NEG": "当周柱水下(非收敛)",
}
GROUP_COLOR = {"CVG": "#0072B2", "POS": "#E69F00", "NEG": "#D55E00"}


def fmt(x, digits=2, suffix=""):
    if x is None:
        return "--"
    return f"{x:.{digits}f}{suffix}"


def main():
    stats = json.load(open(STATS_PATH, encoding="utf-8"))
    ev = pd.read_csv(EVENTS_PATH)

    # ---- 事件清单（用于 trades_table + markers：每事件一行，label = 收敛组+形态） ----
    trades = []
    for _, r in ev.iterrows():
        cvg_tag = "收敛" if r["group"] == "CVG" else ("水上" if r["group"] == "POS" else "水下")
        in_water = "仍水上" if r["hist_cur"] > 0 else "已回水下"
        labels = f"{r['symbol']} {r['event_date']} · {cvg_tag}"
        if r["group"] == "CVG":
            labels += f"·{in_water}"
        if pd.notna(r["conv_len"]) and r["group"] == "CVG":
            labels += f"·{int(r['conv_len'])}根"
        trades.append({
            "label": labels,
            "symbol": r["symbol"],
            "event_date": r["event_date"],
            "entry_date": r["event_date"],
            "pnl_pct": float(r["fwd20"]) if pd.notna(r["fwd20"]) else None,
            "exc20": float(r["exc20"]) if pd.notna(r["exc20"]) else None,
            "hist_cur": float(r["hist_cur"]) if pd.notna(r["hist_cur"]) else None,
            "hist_prev2": float(r["hist_prev2"]) if pd.notna(r["hist_prev2"]) else None,
            "group": r["group"],
            "broken20": int(r["broken20"]) if pd.notna(r["broken20"]) else None,
        })

    # ---- event summary（全样本 + CVG 关键） ----
    f20 = ev["fwd20"].dropna()
    summary = {
        "total_trades": int(len(ev)),
        "win_rate_pct": float((f20 > 0).mean() * 100),
        "avg_return_pct": float(f20.mean()),
        "median_return_pct": float(f20.median()),
        "total_return_pct": float(f20.mean()),
        "best_trade_pct": float(f20.max()),
        "worst_trade_pct": float(f20.min()),
    }

    meta = {
        "strategy_name": "周线MACD能量柱收敛 × 支撑位触达 · 蓝筹事件研究",
        "report_kind": "event_study",
        "event_overview_mode": "stats",
        "start": ev["event_date"].min(),
        "end": ev["event_date"].max(),
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "market": "us",
    }

    # ---- 分组 horizon 对比表（metric_table 多列） ----
    h = stats["horizon"]
    metric_rows = []
    for T in (5, 10, 20, 60):
        metric_rows.append({
            "metric": f"T+{T} 平均收益 (%)",
            "values": [{"main": fmt(h[str(T)][g]["mean"]), "raw": h[str(T)][g]["mean"]} for g in GROUPS],
        })
        metric_rows.append({
            "metric": f"T+{T} 中位数 (%)",
            "values": [{"main": fmt(h[str(T)][g]["median"]), "raw": h[str(T)][g]["median"]} for g in GROUPS],
        })
        metric_rows.append({
            "metric": f"T+{T} 胜率 (%)",
            "values": [{"main": fmt(h[str(T)][g]["win_rate"], 1), "raw": h[str(T)][g]["win_rate"]} for g in GROUPS],
        })
        metric_rows.append({
            "metric": f"T+{T} 超额均值 vs SPY (%)",
            "values": [{"main": fmt(h[str(T)][g]["exc_mean"]), "raw": h[str(T)][g]["exc_mean"]} for g in GROUPS],
        })
        metric_rows.append({
            "metric": f"T+{T} 破位率 (%)",
            "values": [{"main": fmt(h[str(T)][g]["broken_rate"], 1), "raw": h[str(T)][g]["broken_rate"]} for g in GROUPS],
        })
    metric_table = {
        "type": "metric_table",
        "tab": "overview",
        "title": "分组 × 持有期对照（事件后交易日收益）",
        "subtitle": "CVG=周线MACD柱收敛(起点水上≥3根递减) | POS=当周柱水上非收敛 | NEG=当周柱水下非收敛",
        "columns": ["指标", "CVG 收敛", "POS 水上非收敛", "NEG 水下非收敛"],
        "rows": metric_rows,
    }

    # ---- 短线到长线均值阶梯（line_chart） ----
    line_series = []
    for g in GROUPS:
        pts = []
        for T in (5, 10, 20, 60):
            pts.append({"date": f"T+{T}", "value": round(h[str(T)][g]["mean"], 2)})
        line_series.append({"name": GROUP_DESC[g], "color": GROUP_COLOR[g], "points": pts})
    line_chart = {
        "type": "line_chart",
        "tab": "overview",
        "title": "事件后平均收益阶梯（T+5 → T+60）",
        "subtitle": "统一纵轴：T+5/10/20/60 交易日平均收益 %",
        "series": line_series,
    }

    # ---- 收敛强度分层（custom_html + ECharts） ----
    cvg = ev[ev["group"] == "CVG"]
    cvg_by_len = cvg.groupby("conv_len").agg(
        n=("fwd20", "size"), mean=("fwd20", "mean"), med=("fwd20", "median"),
        win=("fwd20", lambda x: (x > 0).mean() * 100),
        exc=("exc20", "mean")).reset_index()
    # 只保留样本充分的桶（n>=10），3~10根
    cvg_by_len = cvg_by_len[cvg_by_len["n"] >= 10].sort_values("conv_len")
    conv_len_json = cvg_by_len.to_dict(orient="records")
    # 累计：>=4 / >=5 / >=6
    cum_rows = []
    for L in (3, 4, 5, 6):
        sub = cvg[cvg["conv_len"] >= L]
        if len(sub):
            cum_rows.append({"len": L, "n": int(len(sub)),
                             "mean": round(float(sub["fwd20"].mean()), 2),
                             "win": round(float((sub["fwd20"] > 0).mean() * 100), 1),
                             "exc": round(float(sub["exc20"].mean()), 2)})
    conv_html = _conv_hist_html(conv_len_json, cum_rows)
    conv_module = {
        "type": "custom_html",
        "tab": "overview",
        "title": "收敛强度分层（连续递减周柱数）· T+20",
        "html": conv_html,
    }

    # ---- 环境分层（文本表） ----
    env_rows = []
    for g in GROUPS:
        for b in stats["env20"][g]:
            env_rows.append((GROUP_DESC[g], b["bucket"], b["n"], b["mean_fwd20"], b["exc_mean"], b["win_rate"], b["broken_rate"]))
    env_table = _env_table(env_rows)
    env_module = {
        "type": "custom_html",
        "tab": "overview",
        "title": "市场环境分层（事件前 SPY 20日收益）· T+20",
        "html": env_table,
    }

    # ---- 聚集统计（text） ----
    clust = stats["clustering"]
    clust_text = (f"- 事件共 {stats['n_total']} 条，分布在 {stats['clustering']['event_days']} 个交易日；"
                  f"同日 ≥3 只股票同时触发的拥挤日占 {fmt(clust['pct_days_ge3'], 0)}% 的交易日，"
                  f"但涉及 {fmt(clust['pct_events_in_ge3_days'], 0)}% 的事件。\n"
                  f"- 系统性大跌日（2020-03、2022-09 等）事件高度聚集，t 值与显著性一律视为上限。")

    # ---- 随机日基线 ----
    base_mean, base_win = 1.29, 59.5

    # ---- text 模块 ----
    texts = [
        {"type": "text", "tab": "overview", "title": "一句话结论",
         "text": (
             "**周线MACD能量柱「水上收敛 ≥3 根后触支撑位」在本回测中不产生增量 alpha。**\n"
             f"- 收敛组（CVG，n={stats['n_group']['CVG']}）T+20 平均 **+{h['20']['CVG']['mean']:.2f}%**、胜率 **{h['20']['CVG']['win_rate']:.1f}%**，"
             f"与水下非收敛组（NEG，n={stats['n_group']['NEG']}，+{h['20']['NEG']['mean']:.2f}%/{h['20']['NEG']['win_rate']:.1f}%）几乎打平（Welch t ≈ {h['20']['ttest']['CVG_vs_NEG']:.1f}，不显著）。\n"
             f"- 水上非收敛组（POS，n={stats['n_group']['POS']}）最差：T+20 **{h['20']['POS']['mean']:.2f}%**、胜率 {h['20']['POS']['win_rate']:.1f}% —— 逆直觉，但该组是「强势但未收敛」状态，且样本仅 {stats['n_group']['POS']}。\n"
             "- 对照组随机买入基线为 T+20 +1.29%/胜率 59.5%，说明**支撑位触达本身**在这些低波动蓝筹上即有约 +0.5pp 的微弱正偏（与报告31一致），收敛条件没有在此基础上再叠加。"
         )},
        {"type": "text", "tab": "overview", "title": "事件与分组口径（无前视）",
         "text": (
             "- **支撑位**：事件日前 20 个交易日的震荡区间下沿（区间振幅 ≤35%、日线 EMA20 交替穿叉、最近穿叉 ≤10 日、区间维持 ≥20 日），事件日收盘 ≤ 下沿×1.005。与报告31完全一致。\n"
             "- **周线MACD**：MACD(12,26,9)，能量柱 = DIF − DEA。用「已完成周序列 + 当周 to-date 值」递推，**严格无前视**——信号只使用事件日（含）之前的数据。\n"
             "- **收敛（CVG）**：当周柱 < 上周柱 < 上上周柱（连续 ≥3 根递减），且起点（上上周柱）> 0 在水上；是否已回水下不设限。\n"
             "- **POS**：当周柱 > 0 但非收敛；**NEG**：当周柱 ≤ 0 非收敛。三组互斥、同日同股只记一次。\n"
             "- 股票池：47 只低波动蓝筹（年化波动率 ≤32%，数据 1962–2026），**周线数据已落盘** data/<sym>/<sym>, W.csv。"
         )},
        {"type": "text", "tab": "overview", "title": "关键口径与统计",
         "text": (
             f"- 度量：T+5/10/20/60 交易日 fwd 收益（个股）与超额（减去 SPY 同窗收益）；破位率 = T 日内收盘最低 < 下沿×0.98。\n"
             f"- CVG 内部：仍在水上（n={stats['cvg_sub']['水上']['n']}）vs 已回水下（n={stats['cvg_sub']['已回水下']['n']}）T+20 平均 {stats['cvg_sub']['水上']['T20']['mean']:.2f}% vs {stats['cvg_sub']['已回水下']['T20']['mean']:.2f}%，差异很小，**「是否回水下」不是决定性变量**。\n"
             f"- 收敛长度分层（conv_len，从事件日往回连续递减的周柱数）无单调性：恰好 4 根时 T+20 平均 +3.34%、≥6 根衰减、≥5 根超额转负——**参数在 3 根附近并不敏感，找不到「越多越好」的证据**。\n"
             f"- 事件聚集：{clust_text}\n"
             f"- 超额四档环境分层见下（CVG 只在深跌档有明显超额 +1.27pp）。"
         )},
        {"type": "text", "tab": "overview", "title": "已知局限",
         "text": (
             "- **幸存者偏差**：47 只仍存续的蓝筹，不适用会退市的衰败股；结果系统性偏向「大盘蓝筹 + 支撑位」这一类行为。\n"
             "- **事件聚集**：16% 事件集中在系统性风险日，t 值一律视为上限解释。\n"
             "- **2020 COVID 崩盘**贡献了主要尾部亏损（2020 年 CVG 平均 T+20 −0.13%、P10 −14.13%），剔除后 CVG T+20 +1.86%。\n"
             "- **近三年（2024/2025）CVG ≈ NEG**（+2.19 vs +2.20、+3.09 vs +3.06）——收敛优势在近期也未见恢复。\n"
             "- 支撑位、MACD 参数均为事先给定，未做参数寻优；周线的「当周值」用 to-date 递推，与收盘后计算的实际 MACD 可能有微小差异（事件日即交易日收盘时行情）。"
         )},
        {"type": "text", "tab": "overview", "title": "下一步建议",
         "text": (
             "- 若坚持用「收敛+支撑」做择时，建议改为**收敛+深跌环境双重过滤**（CVG 在 SPY 前 20 日 <−5% 时 T+20 +2.38%、超额 +1.27pp）；\n"
             "- 水上非收敛（POS）组在 T+20 反而垫底，建议进一步单列「水上扩张」vs「水上金叉初期」子状态再验证；\n"
             "- 深死叉组（NEG 内 EMA20<EMA50 且深度 <−5%）在报告31中显示为深熊超跌反弹（T+60 +7.08%），与 B 缺口结合可做独立题；\n"
             "- 收敛长度分层出现「4根最优、6根衰减」的非单调，可能与事件周数混合有关，可控制事件周（事件日所在周在收敛段中的位置）再验证。"
         )},
    ]

    # ---- extra modules ----
    extra = [metric_table, line_chart, conv_module, env_module] + texts

    report_data = build_dashboard_data(
        equity_curve=None,
        trade_history=trades,
        summary=summary,
        meta=meta,
        language="zh",
        market="us",
        event_overview_mode="stats",
        extra_modules=extra,
        ui_overrides={
            "tabs": [{"id": "overview", "label": "汇总"}],
            "active_tab": "overview",
            "subtitle": "蓝筹周线MACD收敛 × 支撑位 · 事件研究",
        },
    )
    out_html = os.path.join(OUT_DIR, "index.html")
    render_dashboard(report_data, output_path=out_html, template_path=TEMPLATE)
    print(f"written: {out_html}")


def _conv_hist_html(conv_len_json, cum_rows):
    """收敛长度分层柱状图 + 累计表（ECharts CDN；浅底深字）"""
    lens = [r["conv_len"] for r in conv_len_json]
    means = [r["mean"] for r in conv_len_json]
    wins = [r["win"] for r in conv_len_json]
    ns = [r["n"] for r in conv_len_json]
    cum_ops = "".join(
        f"<tr><td>&gt;={r['len']} 根</td><td>{r['n']}</td><td>{r['mean']:+.2f}%</td>"
        f"<td>{r['win']:.1f}%</td><td>{r['exc']:+.2f}%</td></tr>" for r in cum_rows
    )
    return f"""
<div class="bt-custom-conv-wrap" style="display:flex;flex-wrap:wrap;gap:16px;">
  <div style="flex:1 1 46%;min-width:320px;">
    <div id="bt-custom-conv-chart" style="height:300px;"></div>
  </div>
  <div style="flex:1 1 46%;min-width:280px;">
    <table class="bt-custom-conv-tbl" style="width:100%;border-collapse:collapse;font-size:12.5px;">
      <thead><tr style="border-bottom:1px solid #d5d5d5;">
        <th style="text-align:left;padding:6px 4px;">收敛长度</th><th>n</th>
        <th>T+20均值</th><th>胜率</th><th>超额</th></tr></thead>
      <tbody>{cum_ops}</tbody>
    </table>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>
(function(){{
  var chart = echarts.init(document.getElementById('bt-custom-conv-chart'));
  chart.setOption({{
    tooltip: {{trigger:'axis'}},
    legend: {{data:['T+20均值%','胜率%'], top:0, textStyle:{{color:'#333'}}}},
    grid: {{left:50,right:120,top:32,bottom:28}},
    xAxis: {{type:'category', data:{json.dumps(lens, ensure_ascii=False)}, axisLabel:{{color:'#333'}}}},
    yAxis: [
      {{type:'value', name:'均值%', nameTextStyle:{{color:'#555'}}, axisLabel:{{color:'#555'}}}},
      {{type:'value', name:'胜率%', min:0, max:100, nameTextStyle:{{color:'#555'}}, axisLabel:{{color:'#555'}}}}
    ],
    series: [
      {{name:'T+20均值%', type:'bar', data:{json.dumps([round(m,2) for m in means], ensure_ascii=False)}, barWidth:'46%', itemStyle:{{color:'#0072B2'}},
        label:{{show:true, position:'top', formatter:'{{c}}%', color:'#333'}}}},
      {{name:'胜率%', type:'line', yAxisIndex:1, data:{json.dumps([round(w,1) for w in wins], ensure_ascii=False)}, itemStyle:{{color:'#E69F00'}},
        label:{{show:true, position:'top', formatter:'{{c}}%', color:'#333'}}}}
    ]
  }});
  window.addEventListener('resize', function(){{chart.resize();}});
}})();
</script>
"""


def _env_table(rows):
    tr = ""
    for desc, bucket, n, m, e, w, b in rows:
        tr += (f"<tr><td>{desc}</td><td>{bucket}</td><td>{n}</td>"
               f"<td>{m:+.2f}%</td><td>{e:+.2f}%</td><td>{w:.1f}%</td><td>{b:.1f}%</td></tr>")
    return f"""
<table style="width:100%;border-collapse:collapse;font-size:12.5px;">
  <thead><tr style="border-bottom:1px solid #d5d5d5;">
    <th style="text-align:left;padding:6px 4px;">分组</th><th>环境</th><th>n</th>
    <th>T+20均值</th><th>超额</th><th>胜率</th><th>破位率</th></tr></thead>
  <tbody>{tr}</tbody>
</table>
"""


if __name__ == "__main__":
    main()