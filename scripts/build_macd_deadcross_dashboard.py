# -*- coding: utf-8 -*-
"""报告36 · 蓝筹周线「0轴上方高位刚死叉 + 回踩EMA20(1~3%缓冲)」事件研究 Dashboard

事件研究口径（平均/中位/胜率/超额/破位率）；超长事件清单放独立「事件明细」选项卡。
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from render_dashboard import build_dashboard_data, render_dashboard

OUT_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "reports", "36_高位死叉回踩EMA20支撑")
STATS_PATH = os.path.join(OUT_DIR, "macd_deadcross_stats.json")
EVENTS_PATH = os.path.join(OUT_DIR, "macd_deadcross_events.csv")
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template.html")

GROUPS = ["A", "B", "C"]
GROUP_DESC = {
    "A": "死叉+10~16周窗口",
    "B": "未死叉+10~16周窗口",
    "C": "死叉+窗口外",
}
GROUP_FULL = {
    "A": "高位刚死叉回踩EMA20 · 距0轴上穿10~16周",
    "B": "未死叉回踩EMA20 · 距0轴上穿10~16周",
    "C": "高位刚死叉回踩EMA20 · 距0轴上穿窗口外",
}
GROUP_COLOR = {"A": "#0072B2", "B": "#E69F00", "C": "#D55E00"}


def fmt(x, digits=2, suffix=""):
    if x is None:
        return "--"
    return f"{x:.{digits}f}{suffix}"


def main():
    stats = json.load(open(STATS_PATH, encoding="utf-8"))
    ev = pd.read_csv(EVENTS_PATH)

    trades = []
    for _, r in ev.iterrows():
        dc = "死叉" if r["group"] in ("A", "C") else "未死叉"
        wsc = int(r["weeks_since_cross"]) if pd.notna(r["weeks_since_cross"]) else None
        labels = f"{r['symbol']} {r['event_date']} · {dc}·距0轴上穿{wsc}周"
        if pd.notna(r["diff_drawdown"]):
            labels += f"·DIF回落{r['diff_drawdown']:.0%}"
        trades.append({
            "label": labels,
            "symbol": r["symbol"],
            "event_date": r["event_date"],
            "entry_date": r["event_date"],
            "pnl_pct": float(r["fwd20"]) if pd.notna(r["fwd20"]) else None,
            "exc20": float(r["exc20"]) if pd.notna(r["exc20"]) else None,
            "group": r["group"],
            "broken20": int(r["broken20"]) if pd.notna(r["broken20"]) else None,
        })

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
        "strategy_name": "蓝筹周线：0轴上方高位刚死叉 × 回踩EMA20支撑 · 事件研究",
        "report_kind": "event_study",
        "event_overview_mode": "stats",
        "start": ev["event_date"].min(),
        "end": ev["event_date"].max(),
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "market": "us",
    }

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
            "metric": f"T+{T} 破位率(%)",
            "values": [{"main": fmt(h[str(T)][g]["broken_rate"], 1), "raw": h[str(T)][g]["broken_rate"]} for g in GROUPS],
        })
    metric_table = {
        "type": "metric_table",
        "tab": "overview",
        "title": "三组对照：收益 / 胜率 / 超额 / 破位率（周线级别）",
        "subtitle": "公共条件：0轴上方 + EMA多头 + 跌破EMA10收于EMA20上方1~3% + DIF较峰值回落≥25%",
        "columns": ["指标", "A 死叉·10~16周", "B 未死叉·10~16周", "C 死叉·窗口外"],
        "rows": metric_rows,
    }

    line_series = []
    for g in GROUPS:
        pts = [{"date": f"T+{T}", "value": round(h[str(T)][g]["mean"], 2)} for T in (5, 10, 20, 60)]
        line_series.append({"name": GROUP_DESC[g], "color": GROUP_COLOR[g], "points": pts})
    line_chart = {
        "type": "line_chart",
        "tab": "overview",
        "title": "事件后平均收益阶梯（T+5 → T+60 周）",
        "subtitle": "纵轴：平均收益 %",
        "series": line_series,
    }

    # ---- 敏感性图表（custom_html） ----
    sens = stats.get("sensitivity", {})
    sens_module = {
        "type": "custom_html",
        "tab": "overview",
        "title": "参数敏感性：DIF回落阈值扫描 × 距0轴上穿窗口分档（T+20）",
        "html": _sens_html(sens),
    }

    # ---- 环境分层表 ----
    env_rows = []
    for g in GROUPS:
        for b in stats["env8"][g]:
            env_rows.append((GROUP_DESC[g], b["bucket"], b["n"], b["mean_fwd20"], b["exc_mean"], b["win_rate"], b["broken_rate"]))
    env_module = {
        "type": "custom_html",
        "tab": "overview",
        "title": "市场环境分层（事件周前 8 周 SPY 收益）· T+20",
        "html": _env_table(env_rows),
    }

    # ---- text 模块 ----
    a_n = stats["n_group"]["A"]
    a = h["20"]["A"]
    clust = stats["clustering"]
    texts = [
        {"type": "text", "tab": "overview", "title": "一句话结论",
         "text": (
             "**在你的信号定义下（0轴上方高位刚死叉 + 多头排列未破坏 + 跌破EMA10但收于EMA20上方1~3% + 距0轴上穿10~16周），支撑位的有效性没有被削弱，破位率也没有被抬升。**\n"
             f"- A组（n={a_n}，严格信号）T+20 平均 **+{a['mean']:.2f}%** / 中位 {a['median']:.2f}% / 胜率 {a['win_rate']:.1f}%；对 SPY 超额 **{a['exc_mean']:+.2f}pp**——与随机周买入基线（+5.79%/64.1%）基本打平，支撑没有失效。\n"
             f"- **破位率 {a['broken_rate']:.1f}% 反而是三组最低**（B 未死叉 {h['20']['B']['broken_rate']:.1f}%、C 窗口外 {h['20']['C']['broken_rate']:.1f}%）——「刚死叉」没有让 EMA20 更容易被打穿。\n"
             "- 但两个重要反转：①**10~16周「首次回调」窗口是表现最差的一档**（放宽后仅 +2.63%，而 16~24 周 +7.07%、24~40 周 +6.65%）；②窗口外死叉（C）胜率最高（74.3%）。逐层检验见敏感性模块。"
         )},
        {"type": "text", "tab": "overview", "title": "信号与分组口径（严格无前视）",
         "text": (
             "- 频率：**周线级别**（周bar=每周最后交易日，复权OHLC，来自 data/<sym>/<sym>, W.csv）。\n"
             "- **MACD(12,26,9)**，DIF/DEA/Hist 均用「已完成周序列 + 当周 to-date close 递推」，不含未来信息。\n"
             "- 公共条件：DIF>0 且 DEA>0（0轴上方）；EMA10>EMA20（多头排列未破坏）；close<EMA10（已跌破10）；close/EMA20−1 ∈ [1%,3%]（勉强收于20上方）；DIF 较近26周峰值回落 ≥25%。\n"
             "- **死叉当周** = 本周 Hist<0 且上周 Hist≥0（刚触发死叉）。\n"
             "- **窗口** = 距最近一次 DIF 上穿 0 轴 10~16 周（A/B 组）或窗口外（C 组，含更早/更晚）。\n"
             "- 破位率 = 事件后 T 周内周收盘最低 < 事件周 EMA20×0.98；超额 = 个股 − SPY 同窗。"
         )},
        {"type": "text", "tab": "overview", "title": "关键敏感性结果（参数扫描）",
         "text": (
             "- **DIF回落阈值**：≥0 或 ≥0.15 时「死叉+10~16周」样本从 37→37 例、fwd20 +2.63%/胜率62%；提到 ≥0.25 样本骤减到 14 例、fwd20 降至 +0.12%（≥0.35 仅 1 例）——**DIF回落≥25% 是主要样本杀手，且未带来收益提升**（敏感性模块柱图）。\n"
             f"- **窗口分档**（死叉，无回落约束）：5-10w n=2；**10-16w n=37 fwd20 +2.63%**；16-24w n=75 **+7.07%/胜率77%**；24-40w n=103 **+6.65%/75%**——10~16 周是全部分档里最弱的一段。\n"
             f"- **窗口内死叉 vs 未死叉**：死叉 n=37 +2.63% vs 未死叉 n=205 +4.11%——死叉在收益上略弱（约 −1.5pp），但**破位率反而更低**（A 57% vs B 73%）。"
         )},
        {"type": "text", "tab": "overview", "title": "破位后行为（A组内部）",
         "text": (
             "- A 组 20 周内破位（n=7）fwd20 平均 **−9.95%**，未破位（n=6）**+19.59%**——分化极大，破位与否决定短期盈亏；\n"
             "- 但破位组 fwd60（约 60 周）平均仍能收回至 **+8.1%**、未破位 +32.7%——周线级别破位后「收回」概率仍不低（与报告31的深死叉逻辑一致）；\n"
             "- 提示：EMA20 上方 1~3% 缓冲意味着「破位」需要跌穿 2%~4% 才算，一旦触发往往是真的破位，止损纪律比胜率更重要。"
         )},
        {"type": "text", "tab": "overview", "title": "已知局限",
         "text": (
             f"- **样本量极小**：A 组仅 {a_n} 例、B 组 {stats['n_group']['B']} 例，统计功效低，所有均值/t 值仅作方向参考；加严 DIF回落≥25% 后 A 组实际 T+20 有效样本 13 例。\n"
             f"- **三组并非等概率抽样**：C（窗口外，n={stats['n_group']['C']}）天然包含更长的牛市段，样本构成不同。\n"
             "- 幸存者偏差：47 只仍存续蓝筹，不适用于退市/衰败股；事件历史最早至 1980 年，早年 SPY 超额有缺口（exc 部分为 NaN）。\n"
             f"- 事件聚集：同周≥3股占 {clust['pct_events_in_ge3_days']:.0f}% 事件，t 值视为上限。\n"
             "- 参数未寻优；周线「当周」值为 to-date 递推，与收盘后实际 MACD 略有差异。"
         )},
        {"type": "text", "tab": "overview", "title": "下一步建议",
         "text": (
             "- 若把「首次回调」当入场理由，数据更支持 **16~40 周** 而非 10~16 周；10~16 周是动能最不稳定段。\n"
             "- 建议弱化 DIF 回落阈值（≥0.15 即可），以换取样本量；或改用「跌幅/回撤深度」等连续变量替代硬阈值。\n"
             "- 破位后 fwd60 收回率高，可专门验证「破位 EMA20 后周收盘收回」作为二次买点的收益/回撤（承接报告31 深死叉超跌反弹线索）。\n"
             "- 扩展标的池（SP500 全成分、含已退市）提升样本并控制幸存者偏差。"
         )},
    ]

    extra = [metric_table, line_chart, sens_module, env_module] + texts

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
            "subtitle": "蓝筹周线高位死叉回踩EMA20 · 事件研究",
        },
    )
    # 事件明细独立选项卡
    mods = report_data["modules"]
    evt = None
    for m in mods:
        if m.get("type") == "trades_table":
            evt = m
            break
    if evt is not None:
        evt["tab"] = "events"
        evt["title"] = f"事件明细（共 {len(trades)} 条：分组 / 距0轴上穿 / DIF回落 / T+20 / 超额 / 破位）"
        evt["subtitle"] = "event = 回踩EMA20周；T+20 为事件周后第 20 周个股收益，超额为相对 SPY 同窗"
        mods = [m for m in mods if m.get("type") != "trades_table"]
        mods.append(evt)
    report_data["modules"] = mods
    report_data["ui"]["tabs"] = [
        {"id": "overview", "label": "汇总"},
        {"id": "events", "label": "事件明细"},
    ]

    out_html = os.path.join(OUT_DIR, "index.html")
    render_dashboard(report_data, output_path=out_html, template_path=TEMPLATE)
    print(f"written: {out_html}")


def _sens_html(sens):
    """敏感性：DIF回落扫描柱图 + 窗口分档柱图（ECharts CDN）"""
    dif = sens.get("dif_thresh", {})
    dif_keys = list(dif.keys())
    dif_n = [dif[k]["n"] or 0 for k in dif_keys]
    dif_f = [round(dif[k]["fwd20"] or 0, 2) for k in dif_keys]

    wb = sens.get("window_buckets", {})
    wb_keys = list(wb.keys())
    wb_n = [wb[k]["n"] or 0 for k in wb_keys]
    wb_f = [round(wb[k]["fwd20"] or 0, 2) for k in wb_keys]
    wb_w = [round(wb[k]["win"] or 0, 1) for k in wb_keys]

    return f"""
<div class="bt-custom-sens-wrap" style="display:flex;flex-wrap:wrap;gap:20px;">
  <div style="flex:1 1 46%;min-width:320px;">
    <div id="bt-custom-sens-dif" style="height:280px;"></div>
  </div>
  <div style="flex:1 1 46%;min-width:320px;">
    <div id="bt-custom-sens-win" style="height:280px;"></div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>
(function(){{
  var c1 = echarts.init(document.getElementById('bt-custom-sens-dif'));
  c1.setOption({{
    tooltip: {{trigger:'axis'}},
    legend: {{data:['n','T+20均值%'], top:0, textStyle:{{color:'#333'}}}},
    grid: {{left:44,right:56,top:30,bottom:30}},
    xAxis: {{type:'category', data:{json.dumps(dif_keys, ensure_ascii=False)}, axisLabel:{{color:'#333'}}}},
    yAxis: [
      {{type:'value', name:'n', nameTextStyle:{{color:'#555'}}, axisLabel:{{color:'#555'}}}},
      {{type:'value', name:'均值%', nameTextStyle:{{color:'#555'}}, axisLabel:{{color:'#555'}}}}
    ],
    series: [
      {{name:'n', type:'bar', data:{json.dumps(dif_n)}, barWidth:'40%', itemStyle:{{color:'#B0BEC5'}},
        label:{{show:true, position:'top', color:'#333'}}}},
      {{name:'T+20均值%', type:'line', yAxisIndex:1, data:{json.dumps(dif_f)}, itemStyle:{{color:'#0072B2'}},
        label:{{show:true, position:'top', formatter:'{{c}}%', color:'#333'}}}}
    ]
  }});
  var c2 = echarts.init(document.getElementById('bt-custom-sens-win'));
  c2.setOption({{
    tooltip: {{trigger:'axis'}},
    legend: {{data:['n','T+20均值%','胜率%'], top:0, textStyle:{{color:'#333'}}}},
    grid: {{left:44,right:56,top:30,bottom:30}},
    xAxis: {{type:'category', data:{json.dumps(wb_keys, ensure_ascii=False)}, axisLabel:{{color:'#333'}}}},
    yAxis: [
      {{type:'value', name:'n', nameTextStyle:{{color:'#555'}}, axisLabel:{{color:'#555'}}}},
      {{type:'value', name:'%', min:0, max:100, nameTextStyle:{{color:'#555'}}, axisLabel:{{color:'#555'}}}}
    ],
    series: [
      {{name:'n', type:'bar', data:{json.dumps(wb_n)}, barWidth:'36%', itemStyle:{{color:'#B0BEC5'}},
        label:{{show:true, position:'top', color:'#333'}}}},
      {{name:'T+20均值%', type:'line', yAxisIndex:1, data:{json.dumps(wb_f)}, itemStyle:{{color:'#0072B2'}},
        label:{{show:true, position:'top', formatter:'{{c}}%', color:'#333'}}}},
      {{name:'胜率%', type:'line', yAxisIndex:1, data:{json.dumps(wb_w)}, itemStyle:{{color:'#E69F00', type:'dashed'}},
        label:{{show:true, position:'bottom', formatter:'{{c}}%', color:'#333'}}}}
    ]
  }});
  window.addEventListener('resize', function(){{c1.resize(); c2.resize();}});
}})();
</script>
"""


def _env_table(rows):
    tr = ""
    for desc, bucket, n, m, e, w, b in rows:
        tr += (f"<tr><td>{desc}</td><td>{bucket}</td><td>{n if n else '--'}</td>"
               f"<td>{m:+.2f}%</td><td>{e:+.2f}%</td><td>{w:.1f}%</td><td>{b:.1f}%</td></tr>")
    return f"""
<table style="width:100%;border-collapse:collapse;font-size:12.5px;">
  <thead><tr style="border-bottom:1px solid #d5d5d5;">
    <th style="text-align:left;padding:6px 4px;">分组</th><th>环境(SPY前8周)</th><th>n</th>
    <th>T+20均值</th><th>超额</th><th>胜率</th><th>破位率</th></tr></thead>
  <tbody>{tr}</tbody>
</table>
"""


if __name__ == "__main__":
    main()