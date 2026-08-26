#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中期选举波动率研究 —— 渲染 HTML Dashboard（reports/37_中期选举波动率/index.html）"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

SKILL = "/Users/alberthuang/.workbuddy/plugins/marketplaces/experts/plugins/strategy-backtest-expert/skills/quant-backtest-lab"
sys.path.insert(0, os.path.join(SKILL, "reference"))
from render_dashboard import build_dashboard_data, render_dashboard  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADES = os.path.join(ROOT, "results", "midterm_vol_trades.csv")
STATS = os.path.join(ROOT, "results", "midterm_vol_group_stats.json")
OUT_HTML = os.path.join(ROOT, "reports", "37_中期选举波动率", "index.html")
TEMPLATE = os.path.join(SKILL, "reference", "dashboard_template.html")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]
GROUPS = {"midterm": "中期选举", "offyear": "奇数年(无选举)", "pres": "总统大选年"}
COLORS = {"midterm": "#c0392b", "offyear": "#8e8e8e", "pres": "#2c6fbb"}


def load_trades() -> list[dict]:
    df = pd.read_csv(TRADES)
    return df.to_dict("records")


def load_stats() -> dict:
    return json.load(open(STATS, encoding="utf-8"))


def build_curve_chart(stats: dict) -> dict:
    """选举前 -90~-1 交易日平均放大曲线（echarts，x=前 N 交易日）。"""
    series = []
    for g in ["midterm", "offyear", "pres"]:
        c = stats["groups"][g]["avg_curve"]
        data = [[abs(int(t)), round(float(c[str(t)]), 3)] for t in range(-90, 0)]
        series.append({
            "name": GROUPS[g], "type": "line", "smooth": True, "symbol": "none",
            "lineStyle": {"width": 2.5, "color": COLORS[g]},
            "itemStyle": {"color": COLORS[g]},
            "data": data,
        })
    html = """
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <div id="bt-custom-volcurve-1" style="height:360px;"></div>
    """
    mount = r"""
        function init() {
            const el = host.querySelector('#bt-custom-volcurve-1');
            if (typeof echarts === 'undefined') { setTimeout(init, 150); return; }
            const chart = echarts.init(el);
            const series = __SERIES__;
            chart.setOption({
                tooltip: { trigger: 'axis', valueFormatter: v => (v*100).toFixed(1) + '%' },
                legend: { top: 0 },
                grid: { left: 55, right: 20, top: 40, bottom: 40 },
                xAxis: {
                    type: 'value', inverse: true, min: 1, max: 90,
                    name: '距选举日（交易日，0=选举日）',
                    axisLabel: { formatter: v => '前' + v + '日', interval: 14 },
                    splitLine: { show: true, lineStyle: { color: '#eee' } },
                },
                yAxis: {
                    type: 'value', name: '波动率 ÷ 基准',
                    scale: true, min: 0.4, max: 1.9,
                    axisLabel: { formatter: v => '×' + v.toFixed(1) },
                },
                series: series.concat([
                    { name: '×1.0（基准）', type: 'line', data: [[90,1],[1,1]],
                      lineStyle: { type: 'dashed', color: '#555', width: 1 }, symbol: 'none',
                      tooltip: { show: false }, silent: true },
                    { name: '×1.2', type: 'line', data: [[90,1.2],[1,1.2]],
                      lineStyle: { type: 'dotted', color: '#c0392b', width: 1 }, symbol: 'none',
                      tooltip: { show: false }, silent: true },
                    { name: '×1.3', type: 'line', data: [[90,1.3],[1,1.3]],
                      lineStyle: { type: 'dotted', color: '#e67e22', width: 1 }, symbol: 'none',
                      tooltip: { show: false }, silent: true },
                ]),
            });
        }
        init();
    """.replace("__SERIES__", json.dumps(series, ensure_ascii=False))
    return {
        "type": "custom_html", "tab": "overview", "width": "full",
        "title": "选举前波动率放大曲线（事件平均 · 基准=前121~180交易日）",
        "subtitle": "中期选举(6) vs 奇数年无选举(13) vs 总统大选年(7)；y=当日10日滚动波动率/基准",
        "html": html, "mount_script": mount,
    }


def build_window_table(stats: dict) -> dict:
    """各窗口三组平均放大% + 中期vs奇数年显著性。"""
    rows = []
    for k in WINDOWS:
        def fmt(g):
            s = stats["groups"][g][f"v{k}"]
            return {"main": f"{s['mean']:+.1f}%", "raw": s["mean"]}
        p = stats["comparisons"][f"v{k}"]["midterm_vs_offyear"]["p"]
        sig = "显著" if p < 0.05 else ("边际" if p < 0.10 else "不显著")
        rows.append({
            "metric": f"选举前{k}个交易日",
            "values": [fmt("midterm"), fmt("offyear"), fmt("pres"),
                       {"main": f"p={p:.2f}·{sig}"}],
        })
    return {
        "type": "metric_table", "tab": "overview", "width": "full",
        "title": "各前置窗口平均波动放大（vs 基准 121~180 交易日）",
        "subtitle": "中期选举 vs 奇数年对照（Welch t 检验，n=6 小样本仅作参考）",
        "columns": ["窗口", "中期选举", "奇数年对照", "大选年", "中期vs奇数年"],
        "rows": rows,
    }


def build_window_bar(stats: dict) -> dict:
    """各窗口三组放大% 柱状图。"""
    cats = [f"前{k}日" for k in WINDOWS]
    series = []
    for g in ["midterm", "offyear", "pres"]:
        series.append({
            "name": GROUPS[g], "type": "bar",
            "data": [round(stats["groups"][g][f"v{k}"]["mean"], 1) for k in WINDOWS],
            "itemStyle": {"color": COLORS[g]}, "barGap": "10%",
        })
    html = """
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <div id="bt-custom-volbar-1" style="height:320px;"></div>
    """
    mount = r"""
        function init() {
            const el = host.querySelector('#bt-custom-volbar-1');
            if (typeof echarts === 'undefined') { setTimeout(init, 150); return; }
            const chart = echarts.init(el);
            chart.setOption({
                tooltip: { trigger: 'axis', valueFormatter: v => v + '%' },
                legend: { top: 0 },
                grid: { left: 55, right: 20, top: 40, bottom: 30 },
                xAxis: { type: 'category', data: __CATS__ },
                yAxis: { type: 'value', name: '平均波动放大（%）',
                         axisLabel: { formatter: v => v + '%' } },
                series: __SERIES__,
            });
        }
        init();
    """.replace("__CATS__", json.dumps(cats, ensure_ascii=False)).replace(
        "__SERIES__", json.dumps(series, ensure_ascii=False))
    return {
        "type": "custom_html", "tab": "overview", "width": "full",
        "title": "各窗口波动放大幅度（三组对比）",
        "html": html, "mount_script": mount,
    }


def main():
    trades = load_trades()
    stats = load_stats()

    report_data = build_dashboard_data(
        trade_history=trades,
        meta={
            "strategy_name": "中期选举前标普500波动率放大",
            "symbol": "SPY",
            "market": "us",
            "report_kind": "event_study",
            "event_overview_mode": "stats",
            "start": "2000-11-07", "end": "2025-11-04",
            "generated_at": pd.Timestamp.now().isoformat(),
        },
        language="zh",
        event_overview_mode="stats",
        extra_modules=[
            build_curve_chart(stats),
            build_window_table(stats),
            build_window_bar(stats),
            {
                "type": "text", "tab": "overview", "title": "核心结论",
                "text": (
                    "**中期选举前波动放大集中在最后约 1 个月：前 31 个交易日窗口波动平均达基准 ×1.22，前 22 个交易日达 ×1.3，峰值在前 19 个交易日（×1.31）；前 15~20 个交易日（约 3~4 周）是最明显的放大窗口。**\n\n"
                    "- **平均幅度**：选举前 20 个交易日窗口波动放大 **+30.8%**、前 15 日 **+27.0%**、前 10 日 **+18.6%**；前 5 日回落至 +8.4%（部分事件在选前最后一周消息落地、波动收敛）。\n"
                    "- **时点定位**：跨事件平均曲线显示，含前 31 个交易日的窗口平均波动 ≥×1.2（明显放大），前 22 日 ≥×1.3，峰值在前 19 日。即放大不是提前 2~3 个月开始，而是选举临近（约 1~1.5 个月）才启动。\n"
                    "- **对照验证**：奇数年（无选举）同期各窗口放大 −2.3% ~ +8.4%，**不存在任何 ≥×1.2 的持续窗口**（峰值仅 ×1.09）→ 该效应是**选举不确定性**驱动，而非秋季季节性。\n"
                    "- **并非每年都放大**：6 次中 4 次放大（2002/2014/2018/2022），2 次反而缩小（2006、2010 低波动年）；幅度 ≥+20% 的 3/6 次。单次幅度高度依赖当年宏观环境（2002 安然余波+战争预期、2018 年 10 月科技抛售、2022 高波动基准下反而相对平静）。\n"
                    "- **与大选年比较**：总统大选年前 10 日放大 +34.7%、前 15 日 +38.3%、峰值前 14 日 ×1.39，均强于中期选举 → 职位重要性决定不确定性溢价，中期选举约为大选年的 6~8 成。\n"
                    "- **统计显著性**：n=6 小样本，中期 vs 奇数年各窗口 Welch t 检验 p=0.27~0.62，均不显著；二项检验（前 10 日放大≥+20% 出现 3/6 次 vs 奇数年率 23%）p=0.14。结论定位为**描述性规律**，非严格统计显著。"
                ),
            },
            {
                "type": "text", "tab": "overview", "title": "方法与口径",
                "text": (
                    "- **数据**：SPY 日线（Yahoo，1995~2026，adj_close 复权），SPY 作为标普500 代理；事件均为 2000 年以来。\n"
                    "- **波动率**：10 交易日滚动收益率标准差（日化 %）；基准 = 选举日前 121~180 个交易日（约 3 个月前平静期）的均值，与任何 ≤90 日窗口无时间重叠，避免「窗口吃掉基准」。\n"
                    "- **窗口**：选举日前 5/10/15/20/30/45/60/90 个交易日（累积，交易日对齐）；另做 1~30/31~60/61~90 日分段（段内独立标准差，完全无重叠）。\n"
                    "- **处理组**：6 次中期选举（2002-11-05、2006-11-07、2010-11-02、2014-11-04、2018-11-06、2022-11-08）。**对照组**：13 个奇数年（无联邦选举）+ 7 个总统大选年，伪事件日=当年 11 月第一个周二。\n"
                    "- 事件研究，无资金/仓位/佣金假设；波动放大% = (窗口波动率/基准 − 1) × 100。\n"
                    "- 2026 年中期选举（11-03）尚未举行，未纳入。"
                ),
            },
            {
                "type": "text", "tab": "overview", "title": "局限与偏差",
                "text": (
                    "- **样本量极小（n=6）**：任何统计检验功效都不足，结论只能作为「历史倾向」参考，不能作为确定性规律。\n"
                    "- **混入宏观噪声**：2002 年（安然+伊拉克战争预期）、2008 年（金融危机，仅影响大选年组）、2011 年（美债降级）等极端波动期会拉高个别年份；对照组未做剔除，属保守口径。\n"
                    "- **SPY vs 指数**：SPY 有分红、跟踪误差与流动性因素，与 ^GSPC 指数理论波动率有细微差别；ETF 分红除息日可能引入单日噪声（10 日滚动窗口下影响有限）。\n"
                    "- 波动率放大≠方向性下跌：本研究发现的是波动幅度抬升，不意味着选举前必然下跌（2006/2010 甚至收缩）。\n"
                    "- 用于 2026 年参考时注意：当前处于 2026-08 末，距 11-03 选举约 45 个交易日，若规律重演，波动抬升可能已启动或即将启动，但幅度仍取决于当年宏观环境。"
                ),
            },
        ],
    )

    render_dashboard(report_data, output_path=OUT_HTML, template_path=TEMPLATE)
    print(f"written: {OUT_HTML} size={os.path.getsize(OUT_HTML)}")


if __name__ == "__main__":
    main()
