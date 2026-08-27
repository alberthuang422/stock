#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""板块中期选举波动率 —— 渲染 HTML Dashboard（reports/38_板块中期选举波动率/index.html）"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

SKILL = "/Users/alberthuang/.workbuddy/plugins/marketplaces/experts/plugins/strategy-backtest-expert/skills/quant-backtest-lab"
sys.path.insert(0, os.path.join(SKILL, "reference"))
from render_dashboard import build_dashboard_data, render_dashboard  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADES = os.path.join(ROOT, "results", "sector_midterm_vol_trades.csv")
STATS = os.path.join(ROOT, "results", "sector_midterm_vol_stats.json")
OUT_HTML = os.path.join(ROOT, "reports", "38_板块中期选举波动率", "index.html")
TEMPLATE = os.path.join(SKILL, "reference", "dashboard_template.html")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]


def load_stats() -> dict:
    return json.load(open(STATS, encoding="utf-8"))


def build_ranking_bar(stats: dict) -> dict:
    """板块 v20 排序柱状图。"""
    rank = stats["ranking"]
    syms = [r["symbol"] for r in rank]
    full = set(stats["meta"]["full_history_sectors"])
    names = [f"{s} {stats['meta']['sectors'][s]}" for s in syms]
    vals = [r["v20_mean"] for r in rank]
    spy = stats["spy"]["v20_midterm_mean"]
    colors = ["#c0392b" if s in full else "#e67e22" for s in syms]
    html = """
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <div id="bt-custom-sec-rank-1" style="height:380px;"></div>
    """
    mount = r"""
        function init() {
            const el = host.querySelector('#bt-custom-sec-rank-1');
            if (typeof echarts === 'undefined') { setTimeout(init, 150); return; }
            const chart = echarts.init(el);
            chart.setOption({
                tooltip: { trigger: 'item', valueFormatter: v => v + '%' },
                grid: { left: 70, right: 30, top: 30, bottom: 60 },
                xAxis: { type: 'value', name: '选举前20交易日平均波动放大%', axisLabel: { formatter: '{value}%' } },
                yAxis: { type: 'category', data: __NAMES__, inverse: true },
                series: [{
                    type: 'bar', data: __DATA__, barWidth: 16,
                    label: { show: true, position: 'right', formatter: '{c}%' },
                    itemStyle: { color: p => p.dataIndex === 0 ? '#c0392b' : '#d98880' },
                    markLine: { symbol: 'none', label: { formatter: 'SPY +' + __SPY__ + '%' },
                                data: [{ xAxis: __SPY__ }], lineStyle: { color: '#333', type: 'dashed' } },
                }],
            });
        }
        init();
    """.replace("__NAMES__", json.dumps(names, ensure_ascii=False)).replace(
        "__DATA__", json.dumps(vals)).replace("__SPY__", str(spy))
    return {
        "type": "custom_html", "tab": "overview", "width": "full",
        "title": "板块受中期选举波动冲击排序（v20 前20个交易日）",
        "subtitle": "红色=全史6次中期样本；橙=成立晚（XLRE 2次 / XLC 1次，仅参考）；虚线=SPY 全市场 +30.8%",
        "html": html, "mount_script": mount,
    }


def build_heatmap(stats: dict) -> dict:
    """板块 × 窗口 热力图。"""
    rank = stats["ranking"]
    syms = [r["symbol"] for r in rank]
    cats = [f"前{k}日" for k in WINDOWS]
    data = []
    for i, s in enumerate(syms):
        for j, k in enumerate(WINDOWS):
            data.append([j, i, round(stats["sectors"][s][f"v{k}"]["mean"], 1)])
    html = """
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <div id="bt-custom-sec-heat-1" style="height:440px;"></div>
    """
    mount = r"""
        function init() {
            const el = host.querySelector('#bt-custom-sec-heat-1');
            if (typeof echarts === 'undefined') { setTimeout(init, 150); return; }
            const chart = echarts.init(el);
            chart.setOption({
                tooltip: { position: 'top', formatter: p => p.value[0] === -1 ? '' :
                    (p.name + '<br/>' + p.value[2] + '%') },
                grid: { left: 90, right: 30, top: 30, bottom: 50 },
                xAxis: { type: 'category', data: __CATS__, splitArea: { show: true } },
                yAxis: { type: 'category', data: __SYMS__, splitArea: { show: true } },
                visualMap: { min: -15, max: 50, calculable: true, orient: 'horizontal',
                             left: 'center', bottom: 0, text: ['放大%', '高'], textStyle: { fontSize: 11 } },
                series: [{
                    type: 'heatmap', data: __DATA__,
                    label: { show: true, formatter: p => (p.value[2] > 0 ? '+' : '') + p.value[2] },
                    itemStyle: { borderColor: '#fff', borderWidth: 2 },
                    emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,.4)' } },
                }],
            });
        }
        init();
    """.replace("__CATS__", json.dumps(cats, ensure_ascii=False)).replace(
        "__SYMS__", json.dumps(syms, ensure_ascii=False)).replace(
        "__DATA__", json.dumps(data))
    return {
        "type": "custom_html", "tab": "overview", "width": "full",
        "title": "板块 × 前置窗口 波动放大矩阵（中期选举事件平均，%）",
        "html": html, "mount_script": mount,
    }


def build_window_table(stats: dict) -> dict:
    """板块 × 8 窗口数值表 + 对照 + p。"""
    rank = stats["ranking"]
    rows = []
    for r in rank:
        s, full = r["symbol"], r["symbol"] in set(stats["meta"]["full_history_sectors"])
        sec = stats["sectors"][s]
        n = sec["n"]
        ctrl = stats["control_offyear"][s]["v20"]
        sig = stats["significance"][s]
        p = sig["p"]
        ptxt = "—" if p is None else f"p={p:.2f}" + ("·显著" if p < 0.05 else ("·边际" if p < 0.1 else ""))
        rows.append({
            "metric": f"{s} {stats['meta']['sectors'][s]}",
            "values": [{"main": f"{sec['v5']['mean']:+.1f}%"}, {"main": f"{sec['v10']['mean']:+.1f}%"},
                       {"main": f"{sec['v15']['mean']:+.1f}%"}, {"main": f"{sec['v20']['mean']:+.1f}%"},
                       {"main": f"{sec['v30']['mean']:+.1f}%"}, {"main": f"{sec['v45']['mean']:+.1f}%"},
                       {"main": f"{sec['v60']['mean']:+.1f}%"}, {"main": f"{sec['v90']['mean']:+.1f}%"},
                       {"main": f"{int(sec['v20']['hit_p20'])}%"}, {"main": f"{ctrl:+.1f}%" if ctrl is not None else "—"},
                       {"main": f"{n}"}, {"main": ptxt}],
        })
    return {
        "type": "metric_table", "tab": "overview", "width": "full",
        "title": "板块 × 窗口 平均波动放大（%）· 对照与显著性",
        "subtitle": "hit%=6次中前20日放大≥+20%的占比；对照=同板块奇数年v20均值；p=板块中期组vs奇数年组 Welch t（n=6 仅参考）",
        "columns": ["板块", "前5日", "前10日", "前15日", "前20日", "前30日", "前45日", "前60日", "前90日",
                    "hit%", "对照v20", "样本", "p(v20)"],
        "rows": rows,
    }


def build_curves(stats: dict) -> dict:
    """代表板块放大曲线：XLB(最大) vs SPY vs XLV(最小)。"""
    secs = ["XLB", "XLU", "XLV"]
    lines = []
    for s in secs:
        c = stats["sectors"][s]["avg_curve"]
        lines.append({
            "name": f"{s} {stats['meta']['sectors'][s]}",
            "type": "line", "smooth": True, "symbol": "none", "lineStyle": {"width": 2.2},
            "data": [[abs(int(t)), round(float(c[str(t)]), 3)] for t in range(-90, 0)],
        })
    # SPY
    spy_stats = json.load(open(os.path.join(ROOT, "results", "midterm_vol_group_stats.json"), encoding="utf-8"))
    c = spy_stats["groups"]["midterm"]["avg_curve"]
    lines.append({
        "name": "SPY 全市场", "type": "line", "smooth": True, "symbol": "none",
        "lineStyle": {"width": 2.6, "color": "#333", "type": "dashed"},
        "data": [[abs(int(t)), round(float(c[str(t)]), 3)] for t in range(-90, 0)],
    })
    html = """
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <div id="bt-custom-sec-curve-1" style="height:340px;"></div>
    """
    mount = r"""
        function init() {
            const el = host.querySelector('#bt-custom-sec-curve-1');
            if (typeof echarts === 'undefined') { setTimeout(init, 150); return; }
            const chart = echarts.init(el);
            chart.setOption({
                tooltip: { trigger: 'axis', valueFormatter: v => '×' + v.toFixed(2) },
                legend: { top: 0 },
                grid: { left: 55, right: 20, top: 40, bottom: 40 },
                xAxis: { type: 'value', inverse: true, min: 1, max: 90, name: '距选举日（交易日）',
                         axisLabel: { formatter: v => '前' + v + '日', interval: 14 } },
                yAxis: { type: 'value', name: '波动率 ÷ 基准', scale: true, min: 0.3, max: 2.0,
                         axisLabel: { formatter: v => '×' + v.toFixed(1) } },
                series: __SERIES__,
            });
        }
        init();
    """.replace("__SERIES__", json.dumps(lines, ensure_ascii=False))
    return {
        "type": "custom_html", "tab": "overview", "width": "full",
        "title": "放大曲线对比：材料 / 公用事业（平均冲击最大） vs 全市场 vs 医疗（平均最小）",
        "html": html, "mount_script": mount,
    }


def main():
    trades = pd.read_csv(TRADES).to_dict("records")
    stats = load_stats()

    ui_overrides = {
        "tabs": [{"id": "overview", "label": "总览"}, {"id": "detail", "label": "事件明细"}],
        "active_tab": "overview",
    }

    report_data = build_dashboard_data(
        trade_history=trades,
        meta={
            "strategy_name": "中期选举前标普板块波动率放大（板块对比）",
            "symbol": "11 个板块 ETF",
            "market": "us",
            "report_kind": "event_study",
            "event_overview_mode": "stats",
            "start": "2002-11-05", "end": "2022-11-08",
            "generated_at": pd.Timestamp.now().isoformat(),
        },
        language="zh",
        event_overview_mode="stats",
        ui_overrides=ui_overrides,
        extra_modules=[
            build_ranking_bar(stats),
            build_window_table(stats),
            build_heatmap(stats),
            build_curves(stats),
            {
                "type": "text", "tab": "overview", "title": "核心结论",
                "text": (
                    "**政策敏感型板块（材料/工业/能源/公用事业）在中期选举前存在系统性波动溢价：6 次事件中 5 次为正，v20 平均放大 +33%~+44%，超过全市场 SPY(+30.8%)。但板块差异在统计上并不显著，单年排序不稳定——科技/医疗并非「每次都没反应」。**\n\n"
                    "- **平均排序（前 20 个交易日平均波动放大）**：XLB 材料 +43.8% ＞ XLRE 房地产 +41.0%(样本2次) ＞ XLU 公用事业 +37.9% ＞ XLI 工业 +33.9% ＞ XLE 能源 +33.0% ＞ XLY 可选消费 +32.7% ＞ XLF 金融 +32.3% ＞ XLP 必需消费 +23.2% ＞ XLK 科技 +22.8% ＞ XLV 医疗保健 +20.6% ＞ XLC 通信服务 +7.5%(样本1次)。\n"
                    "- **⚠️ 板块差异不显著**：同一 6 次事件内配对检验，XLB vs XLK 平均差 +21pp 但 p=0.36、XLB vs XLV p=0.23（符号秩 0.44/0.16）——排序主要由 2002 年单次极端事件（材料 +144%、公用 +185%）主导，**不能据此断言「科技医疗钝化」**。\n"
                    "- **分年真相**：2002 年科技/医疗其实也放大约 +40%（泡沫余波+战争预期，全市场高波动）；**2014 年医疗 +56.9%、2018 年科技 +61.1%（全板块第一）**——当科技/医疗有自身事件（10 月科技抛售）时，其放大甚至超过周期板块；真正「没反应」的只有 2022 年（科技 +4.3%/医疗 +3.2%）。\n"
                    "- **2022 年没反应=基数效应**：2022 年科技基准期（前 121~180 交易日≈2~5 月加息暴跌期）波动率高达 2.19%/日 vs 公用事业仅 1.06%——基数高则相对放大被稀释，并非选举效应缺席；公用事业（XLU）2022 年反而放大 +80%（防御资金+政策博弈）。\n"
                    "- **机制**：材料/工业/能源/公用事业的盈利定价含大量「政策期权」（关税、基建、气候补贴、商品监管），国会构成的不确定性直接冲击其预期；科技/医疗的波动主驱动是自身盈利/产品/创新事件（财报、AI 叙事、临床数据），全年均匀分布，对选举日期的敏感度低——但当自身事件发生时（2018），板块叙事会压过选举效应。\n"
                    "- **对照验证**：各板块奇数年（无选举）同期 v20 放大基本为 0 或负（-15.7% ~ +11.8%）→ 板块级放大同样是选举不确定性驱动，非秋季季节性。\n"
                    "- **稳健性**：XLRE（2016 年成立，2 次样本）与 XLC（2018 年成立，1 次样本）排序仅参考；所有板块 Welch 检验 p=0.15~0.59 不显著。结论定位为**描述性倾向**，非严格统计规律。"
                ),
            },
            {
                "type": "text", "tab": "overview", "title": "方法与口径",
                "text": (
                    "- **数据**：11 个标普板块 ETF 日线（Yahoo，adj_close）；9 个全史（1998~，6 次中期选举全含），XLRE（2015~）含 2 次、XLC（2018~）含 1 次。\n"
                    "- **波动率**：10 日滚动收益率标准差（日化 %）；基准=选举日前 121~180 个交易日均值（与 ≤90 日前置窗口无重叠）。\n"
                    "- **处理组**：6 次中期选举（2002/2006/2010/2014/2018/2022，选举日=当年 11 月第一个周一后的周二）；对照组=13 个奇数年 + 7 个大选年（伪事件日同规则）。\n"
                    "- **指标**：各窗口（前 5/10/15/20/30/45/60/90 交易日）累积放大%；v20 为主排序指标；命中率=放大 ≥+20% 的事件占比。事件研究，无资金/仓位假设。\n"
                    "- 2026-11-03 选举未举行，不纳入。"
                ),
            },
            {
                "type": "text", "tab": "overview", "title": "局限与偏差",
                "text": (
                    "- **样本极小**：每板块仅 6 次事件，Welch 检验全部不显著（p≥0.15）；**板块间排序差异亦不显著**（同事件配对 t 检验 p=0.23~0.75），排序主要由 2002 年单次极端事件贡献，只能作为历史倾向参考，不能据此做板块择时。\n"
                    "- **基数效应**：波动放大%是相对基准（前 121~180 交易日）的比值，当年基准本身波动高（如 2022 年科技 2.19%/日）时放大被稀释——「没反应」不等于「真没动」，要看绝对波动水平。\n"
                    "- **板块成分随时间漂移**：XLK 在 2018 年移入 FAANG、XLC 2018 年从 XLF/XLK 分拆成立、XLRE 2016 年从 XLF 分拆——历史波动率反映的是当时成分，与今日构成不完全可比。\n"
                    "- **混入宏观噪声**：2002（安然+战争预期）、2011（美债降级）、2014（埃博拉+油价）等极端期未被剔除，个别年份会拉高个别板块（保守口径）。\n"
                    "- **波动放大≠下跌**：本研究发现的是波动幅度抬升，不包含方向信息；周期板块波动放大也可能对应政策利好驱动的上涨。\n"
                    "- **用于 2026 年参考**：若规律重演，政策敏感板块（材料/工业/能源/公用）的波动放大窗口约在 2026-09-22（前31日）至 10 月中（峰值）；科技/医疗是否放大取决于届时是否有自身事件（财报、产品、政策议案），不应预设其「无反应」。"
                ),
            },
            {
                "type": "trades_table", "tab": "detail", "title": "板块 × 中期选举 事件明细（57 行）",
                "rows": trades,
                "columns": [
                    {"key": "label", "label": "事件", "format": "text"},
                    {"key": "sector_name", "label": "板块", "format": "pill"},
                    {"key": "event_date", "label": "选举日", "format": "text"},
                    {"key": "entry_date", "label": "窗口起点(-10日)", "format": "text"},
                    {"key": "exit_date", "label": "窗口终点(选举日)", "format": "text"},
                    {"key": "pnl_pct", "label": "前10日放大%", "format": "pct"},
                    {"key": "v15", "label": "前15日%", "format": "sign"},
                    {"key": "v20", "label": "前20日%", "format": "sign"},
                    {"key": "v30", "label": "前30日%", "format": "sign"},
                ],
            },
        ],
    )

    render_dashboard(report_data, output_path=OUT_HTML, template_path=TEMPLATE)
    print(f"written: {OUT_HTML} size={os.path.getsize(OUT_HTML)}")


if __name__ == "__main__":
    main()
