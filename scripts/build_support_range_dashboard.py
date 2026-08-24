# -*- coding: utf-8 -*-
"""生成图表 + HTML看板：蓝筹区间下沿支撑 三组对照

输入：support_range_events.csv / support_range_stats.json（由 support_range_backtest.py 产出）
输出：matplotlib PNG（破位率曲线、均值收益曲线、4张代表性事件K线图）
      index.html（render_dashboard 渲染）
"""
import json
import os
import sys

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
# 看板模板三件套：优先用报告目录内的副本，否则用 scripts/ 共享副本
if os.path.exists(os.path.join(OUT, "render_dashboard.py")):
    sys.path.insert(0, OUT)
elif os.path.exists(os.path.join(SCRIPTS_DIR, "render_dashboard.py")):
    sys.path.insert(0, SCRIPTS_DIR)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from render_dashboard import build_dashboard_data, render_dashboard

DATA_DIR = os.path.normpath(os.path.join(OUT, "..", "..", "data"))

plt.rcParams["font.sans-serif"] = ["Heiti SC", "Arial Unicode MS", "PingFang SC"]
plt.rcParams["axes.unicode_minus"] = False

# Okabe-Ito 色（色弱安全）+ 线型区分
COLOR = {"A": "#0072B2", "B": "#009E73", "C": "#D55E00"}
STYLE = {"A": "-", "B": "--", "C": "-."}
GROUP_CN = {"A": "A组 压制·未死叉", "B": "B组 无压制", "C": "C组 压制·已死叉"}
UP, DOWN = "#D62728", "#2CA02C"  # 红涨绿跌


def load_data():
    ev = pd.read_csv(os.path.join(OUT, "support_range_events.csv"))
    stats = json.load(open(os.path.join(OUT, "support_range_stats.json"), encoding="utf-8"))
    return ev, stats


def chart_breakdown(ev, stats):
    T = [int(t) for t in stats["horizons"]]
    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=150)
    for g in ("A", "B", "C"):
        y = [stats["horizon"][str(t)][g]["broken_rate"] for t in T]
        ax.plot(T, y, STYLE[g], color=COLOR[g], marker="o", lw=2, ms=5,
                label=f"{GROUP_CN[g]} (破位率)")
    ax.set_xlabel("事件后天数 T（交易日）")
    ax.set_ylabel("破位率 %（收盘跌破下沿×2%）")
    ax.set_title("三组破位率曲线：周线EMA20压制 × 死叉状态")
    ax.set_xticks(T)
    ax.grid(alpha=0.3, ls=":")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "support_range_breakdown_curve.png"))
    plt.show()
    plt.close(fig)


def chart_fwd_mean(ev, stats):
    T = [int(t) for t in stats["horizons"]]
    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=150)
    for g in ("A", "B", "C"):
        y = [stats["horizon"][str(t)][g]["mean"] for t in T]
        ax.plot(T, y, STYLE[g], color=COLOR[g], marker="s", lw=2, ms=5,
                label=f"{GROUP_CN[g]} (均值收益%)")
    ax.axhline(0, color="grey", lw=0.8)
    ax.set_xlabel("事件后天数 T（交易日）")
    ax.set_ylabel("事件后平均收益 %")
    ax.set_title("三组事件后平均收益：下沿触达的反弹力度")
    ax.set_xticks(T)
    ax.grid(alpha=0.3, ls=":")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "support_range_fwd_mean.png"))
    plt.show()
    plt.close(fig)


def load_symbol_daily(symbol):
    path = os.path.join(DATA_DIR, symbol, f"{symbol}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    ratio = df["adj_close"] / df["close"]
    for col in ("open", "high", "low"):
        df[col] = df[col] * ratio
    df["close"] = df["adj_close"]
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    return df[["date", "open", "high", "low", "close", "ema20"]].reset_index(drop=True)


def pick_representative(ev, group, stat_key, broken=None):
    sub = ev[(ev["group"] == group) & ev["fwd20"].notna()]
    if broken is not None:
        sub = sub[sub["broken20"] == broken]
    target = stat_key(sub["fwd20"])
    return sub.loc[(sub["fwd20"] - target).abs().idxmin()]


def draw_kline(ev_row, out_name, title_extra=""):
    df = load_symbol_daily(ev_row["symbol"])
    ev_date = pd.Timestamp(ev_row["event_date"])
    idx = df.index[df["date"] == ev_date][0]
    s, e = max(0, idx - 40), min(len(df), idx + 45)
    w = df.iloc[s:e].reset_index(drop=True)
    ev_i = idx - s
    lower, upper, mid = ev_row["lower"], ev_row["upper"], ev_row["mid"]

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=150)
    for i, row in w.iterrows():
        c = UP if row["close"] >= row["open"] else DOWN
        ax.plot([i, i], [row["low"], row["high"]], color=c, lw=0.8, zorder=2)
        body = max(row["close"], row["open"]) - min(row["close"], row["open"])
        if body < 1e-9:
            ax.plot([i], [row["close"]], marker="_", color=c, ms=4, zorder=3)
        else:
            ax.add_patch(plt.Rectangle((i - 0.32, min(row["open"], row["close"])),
                                       0.64, body, facecolor=c, edgecolor=c, zorder=3))
    ax.plot(range(len(w)), w["ema20"], color="#666666", lw=1.2, label="日线EMA20")
    for val, lab, ls in ((lower, "区间下沿", "--"), (mid, "区间中轨", ":"), (upper, "区间上沿", "--")):
        ax.axhline(val, color="#333333", ls=ls, lw=0.9, alpha=0.75)
        ax.text(len(w) - 0.5, val, f" {lab}", va="bottom", ha="right", fontsize=8, color="#333333")
    ax.axvline(ev_i, color="#D55E00", lw=1.4, ls="--", alpha=0.9)
    # 事件日标注
    ymin, ymax = w["low"].min(), w["high"].max()
    ax.text(ev_i, ymax * 1.005, "事件日", ha="center", fontsize=9, color="#D55E00", fontweight="bold")
    ax.set_xlim(-1.5, len(w) + 0.5)
    ax.set_ylim(ymin * 0.985, ymax * 1.03)

    xt = list(range(0, len(w), 10))
    ax.set_xticks(xt)
    ax.set_xticklabels([w["date"].iloc[i].strftime("%Y-%m-%d") for i in xt], rotation=30, fontsize=8)
    fwd = ev_row["fwd20"]
    fwd_s = f"{fwd:+.1f}%" if pd.notna(fwd) else "N/A"
    gname = GROUP_CN[ev_row["group"]]
    ax.set_title(f"{ev_row['symbol'].upper()} · {ev_row['event_date']} · {gname} · T+20收益 {fwd_s} · 振幅{ev_row['amp_pct']:.1f}%")
    ax.grid(alpha=0.2, ls=":")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, out_name))
    plt.show()
    plt.close(fig)


def make_kline_charts(ev):
    stats = json.load(open(os.path.join(OUT, "support_range_stats.json"), encoding="utf-8"))
    cases = [
        ("A", "典型反弹（中位数）", lambda s: s.median(), None, "kline_case_A_median.png"),
        ("A", "强反弹（约P90）", lambda s: s.quantile(0.90), None, "kline_case_A_strong.png"),
        ("A", "破位案例（约P10）", lambda s: s.quantile(0.10), 1, "kline_case_A_break.png"),
        ("C", "死叉后破位（约P10）", lambda s: s.quantile(0.10), 1, "kline_case_C_break.png"),
    ]
    for group, desc, stat, broken, fname in cases:
        row = pick_representative(ev, group, stat, broken)
        draw_kline(row, fname)
        print(f"  K线案例 {desc}: {row['symbol'].upper()} {row['event_date']} fwd20={row['fwd20']:.2f}% broken20={row['broken20']}")


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
def build_dashboard(ev, stats):
    trade_history = []
    for _, r in ev.iterrows():
        trade_history.append({
            "symbol": r["symbol"],
            "label": f"{r['symbol'].upper()} · {r['event_date']} · {r['group']}组",
            "group": r["group"],
            "entry_date": r["event_date"],
            "exit_date": (r["fwd20_date"] if pd.notna(r["fwd20_date"]) else r["event_date"]),
            "pnl_pct": (float(r["fwd20"]) if pd.notna(r["fwd20"]) else None),
            "broken20": int(r["broken20"]) if pd.notna(r["broken20"]) else None,
            "amp_pct": float(r["amp_pct"]),
            "days_to_mid": int(r["days_to_mid"]) if pd.notna(r["days_to_mid"]) else None,
        })

    summary = {
        "total_trades": int(stats["n_total"]),
        "avg_return_pct": float(ev["fwd20"].mean()),
        "median_return_pct": float(ev["fwd20"].median()),
        "win_rate_pct": float((ev["fwd20"] > 0).mean() * 100),
        "best_trade_pct": float(ev["fwd20"].max()),
        "worst_trade_pct": float(ev["fwd20"].min()),
    }

    meta = {
        "strategy_name": "蓝筹区间下沿支撑 × 周线EMA20压制（三组对照）",
        "symbol": "47只低波动蓝筹（年化波动率≤32%）",
        "start": str(ev["event_date"].min()),
        "end": str(ev["event_date"].max()),
        "market": "us",
        "report_kind": "event_study",
        "event_overview_mode": "stats",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    }

    modules = [
        {"type": "custom_html", "tab": "overview", "title": "核心结论",
         "width": "full", "html": kpi_html(stats)},
        {"type": "metric_table", "tab": "overview", "title": "T=20 三组核心对比",
         "subtitle": "事件后20个交易日 · 破位率=收盘跌破下沿×2%",
         "columns": ["指标", "A组 压制·未死叉", "B组 无压制", "C组 压制·已死叉"],
         "rows": metric_rows(stats)},
        {"type": "custom_html", "tab": "overview", "title": "破位率曲线（T=5/10/20/60）",
         "width": "full", "html": ECHARTS_HTML, "mount_script": echarts_breakdown_script(stats)},
        {"type": "custom_html", "tab": "overview", "title": "事件后平均收益与胜率",
         "width": "full", "html": ECHARTS_HTML2, "mount_script": echarts_fwd_script(stats)},
        {"type": "custom_html", "tab": "overview", "title": "全 horizon 对比表（n/均值/中位数/胜率/破位率/t值）",
         "width": "full", "html": horizon_table(stats)},
        {"type": "custom_html", "tab": "overview", "title": "按区间振幅分桶（T=20）",
         "width": "full", "html": amp_table(stats)},
        {"type": "custom_html", "tab": "overview", "title": "触中轨与最大回撤（事件后20日）",
         "width": "full", "html": mdd_mid_table(stats)},
        {"type": "text", "tab": "notes", "title": "事件定义与口径（严格无前视）",
         "text": METHOD_TEXT},
        {"type": "text", "tab": "notes", "title": "局限与偏差",
         "text": LIMIT_TEXT},
        {"type": "trades_table", "tab": "events", "title": "事件明细（共%d条，含A/B/C三组）" % stats["n_total"],
         "subtitle": "pnl_pct = T+20收益；broken20=1 表示20日内跌破下沿×2%",
         "rows": trade_history,
         "columns": [
             {"key": "label", "label": "事件", "format": "text"},
             {"key": "display_symbol", "label": "标的", "format": "text"},
             {"key": "group", "label": "组别", "format": "pill"},
             {"key": "entry_date", "label": "事件日", "format": "text"},
             {"key": "exit_date", "label": "T+20日", "format": "text"},
             {"key": "pnl_pct", "label": "T20收益", "format": "pct"},
             {"key": "broken20", "label": "20日破位", "format": "text"},
             {"key": "amp_pct", "label": "振幅%", "format": "number"},
             {"key": "days_to_mid", "label": "触中轨天数", "format": "text"},
         ]},
    ]

    report_data = build_dashboard_data(
        trade_history=trade_history, summary=summary, meta=meta,
        language="zh", market="us", event_overview_mode="stats",
        ui_overrides={
            "tabs": [
                {"id": "overview", "label": "总览"},
                {"id": "notes", "label": "口径与局限"},
                {"id": "events", "label": "事件明细"},
            ],
            "active_tab": "overview",
            "subtitle": "47只低波动蓝筹 · 1570个下沿触达事件 · 周线EMA20压制×死叉状态三组对照",
            "color_scheme": "eastern",
        },
    )
    report_data["modules"] = modules
    out = os.path.join(OUT, "index.html")
    render_dashboard(report_data, out)
    print(f"written: {out}")


def fmt(v, digits=2, suffix="%"):
    if v is None:
        return "--"
    return f"{v:,.{digits}f}{suffix}"


def metric_rows(stats):
    h = stats["horizon"]["20"]
    mid = stats["days_to_mid"]
    mdd = stats["mdd20"]
    rows = [
        ("事件数 n", [str(h[g]["n"]) for g in "ABC"]),
        ("平均收益 %", [fmt(h[g]["mean"]) for g in "ABC"]),
        ("中位数收益 %", [fmt(h[g]["median"]) for g in "ABC"]),
        ("胜率 %", [fmt(h[g]["win_rate"]) for g in "ABC"]),
        ("破位率 %（跌破下沿×2%）", [fmt(h[g]["broken_rate"]) for g in "ABC"]),
        ("单样本t值", [fmt(h[g]["t_one"], 2, "") for g in "ABC"]),
        ("20日最大回撤均值 %", [fmt(mdd[g]["mean"]) for g in "ABC"]),
        ("触中轨比例(60日内) %", [fmt(mid[g]["pct_reached_60d"]) for g in "ABC"]),
        ("触中轨中位天数", [fmt(mid[g]["median_days"], 0, "") for g in "ABC"]),
    ]
    return [{"metric": m, "values": [{"main": v} for v in vals]} for m, vals in rows]


ECHARTS_HTML = """
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<div id="bt-custom-brk-1" style="height:300px;"></div>
"""

ECHARTS_HTML2 = """
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<div id="bt-custom-fwd-1" style="height:300px;"></div>
"""


def echarts_breakdown_script(stats):
    T = [int(t) for t in stats["horizons"]]
    data = {g: [round(stats["horizon"][str(t)][g]["broken_rate"], 1) for t in T] for g in "ABC"}
    js = """
const el = host.querySelector('#bt-custom-brk-1');
function initBrk(){
  const chart = echarts.init(el);
  chart.setOption({
  tooltip: {trigger:'axis'},
  legend: {data:['A组 压制·未死叉','B组 无压制','C组 压制·已死叉']},
  grid: {left:45, right:20, top:40, bottom:30},
  xAxis: {type:'category', data:['T=5','T=10','T=20','T=60'], name:'事件后天数'},
  yAxis: {type:'value', name:'破位率 %', min:0},
  series: [
    {name:'A组 压制·未死叉', type:'line', data:__DA__, smooth:true, symbolSize:7,
     lineStyle:{width:2.5, color:'#0072B2'}, itemStyle:{color:'#0072B2'}},
    {name:'B组 无压制', type:'line', data:__DB__, smooth:true, symbolSize:7,
     lineStyle:{width:2.5, type:'dashed', color:'#009E73'}, itemStyle:{color:'#009E73'}},
    {name:'C组 压制·已死叉', type:'line', data:__DC__, smooth:true, symbolSize:7,
     lineStyle:{width:2.5, type:'dotted', color:'#D55E00'}, itemStyle:{color:'#D55E00'}},
  ]
  });
}
if (window.echarts) initBrk();
else { let n=0; const iv=setInterval(function(){ if(window.echarts){clearInterval(iv);initBrk();} else if(++n>120){clearInterval(iv);} }, 50); }
""".replace("__DA__", json.dumps(data["A"])).replace("__DB__", json.dumps(data["B"])).replace("__DC__", json.dumps(data["C"]))
    return js


def echarts_fwd_script(stats):
    T = [int(t) for t in stats["horizons"]]
    m = {g: [round(stats["horizon"][str(t)][g]["mean"], 2) for t in T] for g in "ABC"}
    w = {g: [round(stats["horizon"][str(t)][g]["win_rate"], 1) for t in T] for g in "ABC"}
    js = """
const el = host.querySelector('#bt-custom-fwd-1');
function initFwd(){
  const chart = echarts.init(el);
  chart.setOption({
  tooltip:{trigger:'axis'},
  legend:{data:['A组 均值%','B组 均值%','C组 均值%','A组 胜率%','B组 胜率%','C组 胜率%']},
  grid:{left:50, right:50, top:45, bottom:30},
  xAxis:{type:'category', data:['T=5','T=10','T=20','T=60']},
  yAxis:[{type:'value', name:'均值收益 %', axisLabel:{formatter:'{value}%'}},
         {type:'value', name:'胜率 %', min:0, max:100, splitLine:{show:false}}],
  series:[
    {name:'A组 均值%', type:'line', data:__MA__, smooth:true, lineStyle:{width:2.5,color:'#0072B2'}, itemStyle:{color:'#0072B2'}},
    {name:'B组 均值%', type:'line', data:__MB__, smooth:true, lineStyle:{width:2.5,type:'dashed',color:'#009E73'}, itemStyle:{color:'#009E73'}},
    {name:'C组 均值%', type:'line', data:__MC__, smooth:true, lineStyle:{width:2.5,type:'dotted',color:'#D55E00'}, itemStyle:{color:'#D55E00'}},
    {name:'A组 胜率%', type:'line', yAxisIndex:1, data:__WA__, smooth:true, lineStyle:{width:1.5,color:'#0072B2'}, itemStyle:{color:'#0072B2'}, symbolSize:4},
    {name:'B组 胜率%', type:'line', yAxisIndex:1, data:__WB__, smooth:true, lineStyle:{width:1.5,type:'dashed',color:'#009E73'}, itemStyle:{color:'#009E73'}, symbolSize:4},
    {name:'C组 胜率%', type:'line', yAxisIndex:1, data:__WC__, smooth:true, lineStyle:{width:1.5,type:'dotted',color:'#D55E00'}, itemStyle:{color:'#D55E00'}, symbolSize:4},
  ]
  });
}
if (window.echarts) initFwd();
else { let n=0; const iv=setInterval(function(){ if(window.echarts){clearInterval(iv);initFwd();} else if(++n>120){clearInterval(iv);} }, 50); }
""".replace("__MA__", json.dumps(m["A"])).replace("__MB__", json.dumps(m["B"])).replace("__MC__", json.dumps(m["C"])) \
     .replace("__WA__", json.dumps(w["A"])).replace("__WB__", json.dumps(w["B"])).replace("__WC__", json.dumps(w["C"]))
    return js


def horizon_table(stats):
    head = "<thead><tr><th>T</th><th>组</th><th>n</th><th>均值%</th><th>中位数%</th><th>胜率%</th><th>破位率%</th><th>单样本t</th></tr></thead>"
    body = []
    for T in stats["horizons"]:
        h = stats["horizon"][str(T)]
        for g in "ABC":
            r = h[g]
            t1 = fmt(r["t_one"], 2, "") if r["t_one"] is not None else "--"
            body.append(
                f"<tr><td>T={T}</td><td>{g}组</td><td>{r['n']}</td>"
                f"<td>{fmt(r['mean'])}</td><td>{fmt(r['median'])}</td>"
                f"<td>{fmt(r['win_rate'])}</td><td>{fmt(r['broken_rate'])}</td><td>{t1}</td></tr>")
        ta, tc = h["ttest"]["A_vs_B"], h["ttest"]["A_vs_C"]
        ta = fmt(ta, 2, "") if ta is not None else "--"
        tc = fmt(tc, 2, "") if tc is not None else "--"
        body.append(
            f"<tr class='bt-custom-t'><td>T={T}</td><td colspan='4'>两样本Welch t：A vs B = {ta}</td>"
            f"<td colspan='3'>A vs C = {tc}</td></tr>")
    return f"""<div class="bt-custom-table-wrap"><table class="bt-custom-tbl">{head}<tbody>{''.join(body)}</tbody></table></div>"""


def amp_table(stats):
    head = "<thead><tr><th>组</th><th>振幅</th><th>n</th><th>均值T20%</th><th>胜率%</th><th>破位率%</th></tr></thead>"
    body = []
    for g in "ABC":
        for b in stats["amp_bucket"][g]:
            body.append(
                f"<tr><td>{g}组</td><td>{b['bucket']}</td><td>{b['n']}</td>"
                f"<td>{fmt(b['mean_fwd20'])}</td><td>{fmt(b['win_rate'])}</td><td>{fmt(b['broken_rate'])}</td></tr>")
    return f"""<div class="bt-custom-table-wrap"><table class="bt-custom-tbl">{head}<tbody>{''.join(body)}</tbody></table></div>"""


def mdd_mid_table(stats):
    mid, mdd = stats["days_to_mid"], stats["mdd20"]
    head = "<thead><tr><th>组</th><th>20日回撤均值%</th><th>20日回撤中位%</th><th>触中轨(60日)%</th><th>触中轨中位天数</th></tr></thead>"
    body = []
    for g in "ABC":
        body.append(
            f"<tr><td>{g}组</td><td>{fmt(mdd[g]['mean'])}</td><td>{fmt(mdd[g]['median'])}</td>"
            f"<td>{fmt(mid[g]['pct_reached_60d'])}</td><td>{fmt(mid[g]['median_days'],0,'')}</td></tr>")
    return f"""<div class="bt-custom-table-wrap"><table class="bt-custom-tbl">{head}<tbody>{''.join(body)}</tbody></table></div>"""


def kpi_html(stats):
    h = stats["horizon"]["20"]
    n = stats["n_group"]
    a, b, c = h["A"], h["B"], h["C"]
    style = """
<style>
.bt-custom-table-wrap{overflow-x:auto;}
.bt-custom-tbl{border-collapse:collapse;width:100%;font-size:13px;}
.bt-custom-tbl th,.bt-custom-tbl td{border:1px solid #d0d7de;padding:5px 10px;text-align:center;white-space:nowrap;}
.bt-custom-tbl thead th{background:rgba(127,127,127,0.12);font-weight:600;}
.bt-custom-tbl tr.bt-custom-t td{text-align:left;color:#6e7781;background:rgba(127,127,127,0.06);}
</style>"""
    return style + f"""
<div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:4px;">
  <div class="bt-custom-kpi" style="flex:1;min-width:150px;border:1px solid #d0d7de;border-radius:8px;padding:10px 14px;background:var(--bt-card-bg,#ffffff);">
    <div style="font-size:12px;color:#6e7781;">总事件数</div>
    <div style="font-size:22px;font-weight:700;">{stats['n_total']:,}</div>
    <div style="font-size:12px;color:#6e7781;">A {n['A']:,} / B {n['B']:,} / C {n['C']:,}</div>
  </div>
  <div class="bt-custom-kpi" style="flex:1;min-width:150px;border:1px solid #d0d7de;border-radius:8px;padding:10px 14px;background:var(--bt-card-bg,#ffffff);">
    <div style="font-size:12px;color:#6e7781;">T+20 平均收益</div>
    <div style="font-size:22px;font-weight:700;color:#d62728;">A {a['mean']:+.2f}%</div>
    <div style="font-size:12px;color:#6e7781;">B {b['mean']:+.2f}% · C {c['mean']:+.2f}%</div>
  </div>
  <div class="bt-custom-kpi" style="flex:1;min-width:150px;border:1px solid #d0d7de;border-radius:8px;padding:10px 14px;background:var(--bt-card-bg,#ffffff);">
    <div style="font-size:12px;color:#6e7781;">T+20 破位率（跌破下沿2%）</div>
    <div style="font-size:22px;font-weight:700;color:#d62728;">A {a['broken_rate']:.1f}%</div>
    <div style="font-size:12px;color:#6e7781;">B {b['broken_rate']:.1f}% · C {c['broken_rate']:.1f}%</div>
  </div>
  <div class="bt-custom-kpi" style="flex:1;min-width:150px;border:1px solid #d0d7de;border-radius:8px;padding:10px 14px;background:var(--bt-card-bg,#ffffff);">
    <div style="font-size:12px;color:#6e7781;">核心结论</div>
    <div style="font-size:13px;line-height:1.5;">死叉显著放大尾部风险：C组P10={stats['fwd20_dist']['C']['p10']:.1f}% vs A组{stats['fwd20_dist']['A']['p10']:.1f}%；压制本身影响有限（T+20均值 A vs B 差异不显著）</div>
  </div>
</div>
"""

METHOD_TEXT = """
- **事件（严格无前视，只用事件日及之前数据）**：
  - **震荡区间**：以事件日前20个交易日为观察窗（不含事件日），窗内收盘相对日线EMA20 至少各1次上穿/下穿、穿叉方向交替、最近一次穿叉距事件日≤10日、窗内振幅 max(high)/min(low)−1 ≤ 35%；该震荡状态连续维持≥20个交易日（区间维持≥20日）。区间下沿=窗内最低价，上沿=窗内最高价，中轨=(下沿+上沿)/2。
  - **日线条件**：事件日收盘 ≤ 下沿 ×(1+0.5%)（触达下沿）。
  - **周线条件**：当周周线收盘（=事件日收盘，周内滚动值）< 周线EMA20，且 周线EMA20 > 周线EMA50（未死叉）。周线EMA用「已完成周序列EMA + 当周值递推」，不引用未来周数据。
  - **去重**：同一触达连续段内只保留首次；事件间至少间隔10个交易日（缓解前向窗口重叠）。
- **三组**：A=触下沿+周线压制+未死叉；B=触下沿+周线在EMA20上方（无压制）；C=触下沿+周线压制+已死叉。
- **度量（复权收盘价）**：破位率=T日内收盘最低 < 下沿×0.98 的占比；反弹=T日后收益的均值/中位数/胜率；触中轨天数=60日内首次收盘≥中轨；最大回撤=事件后20日窗口内收盘的峰谷回撤；振幅分桶=(上沿/下沿−1)。
- **样本**：47只低波动蓝筹（年化波动率≤32%，数据自1962~2018年起），事件区间 1963-10 ~ 2026-08，共1570个事件。
"""

LIMIT_TEXT = """
- **前视已控制**：事件判定、区间边界、周线EMA全部只用≤事件日的数据；T日后的收益为结果度量而非信号。
- **破位率口径偏敏感**：下沿×2%的破位阈值在20日窗口内被正常波动触达的概率本就偏高（A组62.8%），其绝对值不等于「支撑必然失效」，需结合反弹胜率/均值一起看；破位后价格仍可能收复（均值收益仍为正）。
- **独立性**：事件间隔≥10日，但同一标的相邻事件的前向窗口仍有部分重叠，t值应视为上限；同类（同板块/同宏观日）事件存在聚集性。
- **幸存者偏差**：样本为当前仍存续的蓝筹股，未含退市/衰败个股；蓝筹池由「低波动+大盘成熟」筛选，波动率≤32%为人为阈值。
- **口径假设**：全部使用复权价；周线为「当周滚动收盘」口径；振幅上限35%排除了更大震荡箱体；事件在2002/2008/2009/2023等熊市年偏多（C组死叉事件天然集中在下跌市），跨组比较未做宏观环境对齐。
- 结果不构成投资建议。
"""


def main():
    ev, stats = load_data()
    print("== 图表 ==")
    chart_breakdown(ev, stats)
    chart_fwd_mean(ev, stats)
    make_kline_charts(ev)
    print("== 看板 ==")
    build_dashboard(ev, stats)


if __name__ == "__main__":
    main()
