#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIX 中期选举前抬升 —— 渲染 HTML Dashboard（reports/42_VIX中期选举抬升/index.html）"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

SKILL = "C:/Users/Administrator/.workbuddy/plugins/marketplaces/experts/plugins/strategy-backtest-expert/skills/quant-backtest-lab"
sys.path.insert(0, os.path.join(SKILL, "reference"))
from render_dashboard import build_dashboard_data, render_dashboard  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADES = os.path.join(ROOT, "results", "vix_midterm_vol_trades.csv")
STATS = os.path.join(ROOT, "results", "vix_midterm_vol_group_stats.json")
OUT_HTML = os.path.join(ROOT, "reports", "42_VIX中期选举抬升", "index.html")
TEMPLATE = os.path.join(SKILL, "reference", "dashboard_template.html")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]
GROUPS = {"midterm": "中期选举", "offyear": "奇数年(无选举)", "pres": "总统大选年"}
COLORS = {"midterm": "#c0392b", "offyear": "#8e8e8e", "pres": "#2c6fbb"}


def load_trades() -> list[dict]:
    return pd.read_csv(TRADES).to_dict("records")


def load_stats() -> dict:
    return json.load(open(STATS, encoding="utf-8"))


def build_curve_chart(stats: dict) -> dict:
    """选举前 -90~-1 交易日平均 VIX 抬升曲线。"""
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
    <div id="bt-custom-vixcurve-1" style="height:360px;"></div>
    """
    mount = r"""
        function init() {
            const el = host.querySelector('#bt-custom-vixcurve-1');
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
                    type: 'value', name: 'VIX(10日均) ÷ 基准',
                    scale: true, min: 0.4, max: 2.0,
                    axisLabel: { formatter: v => '×' + v.toFixed(1) },
                },
                series: series.concat([
                    { name: '×1.0（基准）', type: 'line', data: [[90,1],[1,1]],
                      lineStyle: { type: 'dashed', color: '#555', width: 1 }, symbol: 'none',
                      tooltip: { show: false }, silent: true },
                    { name: '×1.2', type: 'line', data: [[90,1.2],[1,1.2]],
                      lineStyle: { type: 'dotted', color: '#c0392b', width: 1 }, symbol: 'none',
                      tooltip: { show: false }, silent: true },
                ]),
            });
        }
        init();
    """.replace("__SERIES__", json.dumps(series, ensure_ascii=False))
    return {
        "type": "custom_html", "tab": "overview", "width": "full",
        "title": "选举前 VIX 抬升曲线（事件平均 · 基准=前121~180交易日）",
        "subtitle": "VIX 10日滚动均值/基准；中期选举(6) vs 奇数年无选举(13) vs 总统大选年(7)",
        "html": html, "mount_script": mount,
    }


def build_window_table(stats: dict) -> dict:
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
        "title": "各前置窗口平均 VIX 抬升（vs 基准 121~180 交易日）",
        "subtitle": "中期选举 vs 奇数年对照（Welch t 检验，n=6 小样本仅作参考）",
        "columns": ["窗口", "中期选举", "奇数年对照", "大选年", "中期vs奇数年"],
        "rows": rows,
    }


def build_window_bar(stats: dict) -> dict:
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
    <div id="bt-custom-vixbar-1" style="height:320px;"></div>
    """
    mount = r"""
        function init() {
            const el = host.querySelector('#bt-custom-vixbar-1');
            if (typeof echarts === 'undefined') { setTimeout(init, 150); return; }
            const chart = echarts.init(el);
            chart.setOption({
                tooltip: { trigger: 'axis', valueFormatter: v => v + '%' },
                legend: { top: 0 },
                grid: { left: 55, right: 20, top: 40, bottom: 30 },
                xAxis: { type: 'category', data: __CATS__, axisLabel: { rotate: 0 } },
                yAxis: { type: 'value', name: '平均 VIX 抬升（%）',
                         axisLabel: { formatter: v => v + '%' } },
                series: __SERIES__,
            });
        }
        init();
    """.replace("__CATS__", json.dumps(cats, ensure_ascii=False)).replace(
        "__SERIES__", json.dumps(series, ensure_ascii=False))
    return {
        "type": "custom_html", "tab": "overview", "width": "full",
        "title": "各窗口 VIX 抬升幅度（三组对比）",
        "html": html, "mount_script": mount,
    }


def build_individual_table(trades: list[dict]) -> dict:
    """6 次中期事件明细（含 VIX 绝对水平与峰值）。"""
    rows = []
    for r in trades:
        rows.append({
            "metric": r["label"],
            "values": [
                {"main": r["event_date"]},
                {"main": f"{r['base_vix']:.1f}"},
                {"main": f"{r['v10']:+.1f}%", "raw": r["v10"]},
                {"main": f"{r['v20']:+.1f}%", "raw": r["v20"]},
                {"main": f"{r['win10_mean_vix']:.1f}"},
                {"main": f"{r['win10_max_vix']:.1f}"},
            ],
        })
    return {
        "type": "metric_table", "tab": "overview", "width": "full",
        "title": "6 次中期选举事件明细（VIX 口径）",
        "subtitle": "前10日为选举前10个交易日的 VIX 均值/当日高值；基准 VIX=前121~180交易日均值",
        "columns": ["事件", "选举日", "基准VIX", "前10日抬升", "前20日抬升", "前10日VIX均值", "前10日VIX峰值"],
        "rows": rows,
    }


def main():
    trades = load_trades()
    stats = load_stats()

    report_data = build_dashboard_data(
        trade_history=trades,
        meta={
            "strategy_name": "VIX 中期选举前抬升（事件研究）",
            "symbol": "VIX",
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
            build_individual_table(trades),
            {
                "type": "text", "tab": "overview", "title": "核心结论",
                "text": (
                    "**VIX 视角与报告 37 的 SPY 已实现波动率口径高度同源：中期选举前隐含波动率抬升同样集中在最后约 1 个月，峰值窗口在前 17 个交易日（平均 ×1.214）。**\n\n"
                    "- **抬升幅度**：选举前 20 个交易日 VIX 平均抬升 **+21.1%**、前 15 日 **+21.3%**、前 10 日 **+19.3%**、前 5 日 +16.2%；峰值窗口为前 17 个交易日（×1.214）。量级约为同期 SPY 已实现波动率放大（前20日 +30.8%）的 **7 成**——期权市场定价的预期波动抬升略小于实际波动抬升。\n"
                    "- **对照验证（同报告37）**：奇数年（无选举）同期各窗口仅 −0.4% ~ +7.5%，峰值仅 ×1.076 → 中期选举前的 VIX 抬升同样是**选举不确定性驱动**，而非秋季季节性。\n"
                    "- **个体差异大（6 次中 4 次抬升）**：2002（前20日 +76.8%，前20日 VIX 峰值高达 43.4，安然余波+战争预期）> 2014（+28.4%）> 2018（+5.7% 但前10日峰值 27.9，临近期 VIX 实际拉高）> 2022（+11.9%，但基准 VIX 已高达 27.0，前10日仍 26.1）> 2010/2006（低波动年几乎无抬升甚至收缩）。和报告 37 一样：幅度高度依赖当年宏观环境，不是每年都放大。\n"
                    "- **vs 大选年**：总统大选年前 10 日 VIX 抬升 +23.4%、前 5 日 +26.3%、峰值窗口仅前 1 日（×1.290，即选举临近才急剧冲高）；中期选举是更平滑的前 3~4 周逐步抬升。\n"
                    "- **当前（2026-08-26）**：VIX 收 15.69，处于历史偏低区间（8 月 19 日低见 14.89）。距 11月3日 中期选举约 **45 个交易日**——若历史规律重演，VIX 的抬升启动点（前 45 日附近）与当前时点接近，未来 1 个月波动溢价可能开始回升。\n"
                    "- **统计显著性**：n=6 小样本，中期 vs 奇数年各窗口 Welch t p=0.21~0.70，均不显著；二项检验（前10日抬升≥+20% 出现 2/6 次 vs 奇数年率 15.4%）p=0.23。定位为**描述性规律**，与报告 37 同为小样本结论。"
                ),
            },
            {
                "type": "text", "tab": "overview", "title": "方法与口径",
                "text": (
                    "- **数据**：VIX 日线（Yahoo，1995~2026，close）。事件均自 2000 年以来。\n"
                    "- **指标**：VIX 收盘价的 10 交易日滚动均值（平滑单日尖峰）。抬升% = (窗口 VIX(10日均)均值 / 基准 − 1) × 100。\n"
                    "- **基准** = 选举日前 121~180 个交易日（约 3 个月前平静期）的 VIX(10日均) 均值，与任何 ≤90 日窗口无时间重叠。\n"
                    "- **窗口**：选举日前 5/10/15/20/30/45/60/90 个交易日（累积）；另做 1~30/31~60/61~90 日分段。\n"
                    "- **处理组**：6 次中期选举（2022/2018/2014/2010/2006/2002）。**对照组**：13 个奇数年 + 7 个总统大选年，伪事件日=当年 11 月第一个周一后的周二。\n"
                    "- 事件研究，无资金/仓位假设；2002 起 VIX 与 SPY 不同年数差异很小（VIX 数据实际 1995 起可用）。\n"
                    "- 2026 年中期选举（11-03）尚未举行，未纳入事件集。"
                ),
            },
            {
                "type": "text", "tab": "overview", "title": "与报告 37（SPY 口径）的关系",
                "text": (
                    "- **同源信号**：报告 37 发现 SPY 已实现波动率在中期选举前 19 个交易日达峰（×1.31）；本次 VIX 峰值窗口在前 17 个交易日（×1.214），两个峰值时点基本重合 → 市场对选举不确定性的定价（VIX）与股票实际波动（SPY vol）同步启动。\n"
                    "- **幅度差异**：VIX 抬升（前20日 +21%）系统性小于 SPY 已实现波动放大（+31%）→ 隐含波动率的抬升更温和，期权卖方不需要为选举季提前大幅加价；这也与 2022 年基准 VIX 已高（27）时抬升有限的现象一致。\n"
                    "- **额外意义**：VIX 抬升=期权成本抬升，对做多波动率或保护性买权方是顺风；对做空波动率方风险。报告 37 侧重股票端波动，本报告侧重期权端定价，两者互为验证。"
                ),
            },
            {
                "type": "text", "tab": "overview", "title": "局限与偏差",
                "text": (
                    "- **样本量极小（n=6）**：统计功效不足，仅描述性规律。\n"
                    "- **混入宏观噪声**：2002（安然+伊拉克预期）、2018-10（科技抛售）、2022（加息+高基准）等非选举因素主导了个别年份的 VIX 绝对水平。\n"
                    "- **VIX 均值 ≠ 实际期权成本**：VIX 是 30 日恒定到期期权隐含波动率，10 日均值平滑后滞后于市场尖峰；实际 VIX 期货/期权结构还受期限结构影响。\n"
                    "- **对照年份（奇数年）VIX 历史平均略高于中期选举年基准**：奇数年 VIX 历史均值（约 19~20）系统性高于选举年均值（VX 1990s-2000s 时段），但本方法用各自事件前 121~180 日做基准，已消除水平差异。\n"
                    "- VIX 数据 1995 起，早于 SPY 的 1995/1993 实际一致；2000 年前事件（若有）不适用。\n"
                    "- 用于 2026 年参考时注意：本次事件前基准 VIX 处于低位（8 月均值约 15~16），若规律重演，相对抬升幅度大概率高于 2022 年（高基准抑制了相对抬升）。"
                ),
            },
        ],
    )

    render_dashboard(report_data, output_path=OUT_HTML, template_path=TEMPLATE)
    print(f"written: {OUT_HTML} size={os.path.getsize(OUT_HTML)}")


if __name__ == "__main__":
    main()