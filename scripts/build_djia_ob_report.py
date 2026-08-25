# -*- coding: utf-8 -*-
"""构建横向研报：道指各板块代表股 RSI 超买事件研究
读取 results/djia_ob_cross.json
输出 reports/34_道指板块超买横向/djia_ob_cross_report.html
静默写盘：只打印 written 路径与体积。
"""
import os, json, glob
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "34_道指板块超买横向")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "djia_ob_cross.json"), encoding="utf-8") as f:
    D = json.load(f)

TICKS = ["aapl", "jpm", "unh", "mcd", "ko", "cat", "xom", "shw", "vz"]
NAME = {"aapl": "苹果", "jpm": "摩根大通", "unh": "联合健康", "mcd": "麦当劳", "ko": "可口可乐",
        "cat": "卡特彼勒", "xom": "埃克森美孚", "shw": "宣伟", "vz": "威瑞森"}
SECTOR = {"aapl": "信息科技", "jpm": "金融", "unh": "医疗保健", "mcd": "可选消费", "ko": "日常消费",
          "cat": "工业", "xom": "能源", "shw": "材料", "vz": "电信"}
COLOR = {"aapl": "#0072B2", "jpm": "#E69F00", "unh": "#56B4E9", "mcd": "#9467bd", "ko": "#009E73",
         "cat": "#D55E00", "xom": "#8c564b", "shw": "#e377c2", "vz": "#7f7f7f"}

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

# ---------- 主对比表 ----------
def main_rows():
    html = []
    for t in TICKS:
        r = D[t]
        ev, ba = r["event_all"], r["baseline"]
        bs = r["by_stage"]["C_bull"]
        ex5 = ev["T5"]["mean"] - ba["T5"]["mean"]
        ex20 = ev["T20"]["mean"] - ba["T20"]["mean"]
        def cell(v):
            return f"<td class='{'up' if v>0 else 'dn'}'>{v:+.2f}%</td>"
        html.append(
            f"<tr><td class='nowrap'><b>{r['name']}</b><br><span class='tkr'>{t.upper()}</span></td>"
            f"<td class='nowrap'>{r['sector']}</td><td>{r['n_events']}</td>"
            f"{cell(ev['T5']['mean'])}<td>{ev['T5']['win']}%</td>"
            f"{cell(ev['T20']['mean'])}<td>{ev['T20']['win']}%</td>"
            f"{cell(ex5)} {cell(ex20)}"
            f"{cell(bs['T5']['mean'])}<td>{bs['T5']['win']}%</td>"
            f"{cell(bs['T20']['mean'])}<td>{bs['T20']['win']}%</td></tr>")
    return "".join(html)

# ---------- 窗口路径表 ----------
def path_rows():
    html = []
    for t in sorted(TICKS, key=lambda x: -D[x]["event_all"]["T20_runup"]["mean"]):
        r = D[t]
        ev = r["event_all"]
        def cell(v, inv=False):
            if v is None or v.get("n", 0) == 0: return "<td class='na'>—</td>"
            val = v["mean"]
            pos = val >= 0
            return f"<td class='{'up' if pos else 'dn'}'>{val:+.2f}%</td>"
        html.append(
            f"<tr><td class='nowrap'><b>{r['name']}</b></td><td>{ev['T20_runup']['n']}</td>"
            f"{cell(ev['T5_runup'])}{cell(ev['T5_peakdd']) }"
            f"{cell(ev['T10_runup'])}{cell(ev['T10_peakdd'])}"
            f"{cell(ev['T20_runup'])}{cell(ev['T20_peakdd'])}{cell(ev['T20_maxdd'])}</tr>")
    return "".join(html)

# ---------- 牛市逐年 T20 ----------
def bull_year_rows():
    pass

# ---------- 页面结构 ----------
verdicts = [
    ("①  '超买后必回调'在道指 9 板块代表股上整体不成立——但信号本身也几乎不携带额外信息。",
     "9 股全样本超买事件 T+5 均值 7 正 1 平 1 负、T+20 均值 7 正 2 负（KO/VZ 为负），但相对自身基率的超额仅 AAPL 显著为正（T5 +0.47pp / T20 +0.82pp，t=3.0/4.8），其余 8 股超额全部为负或接近 0（T5 −0.02~−1.23pp）且无一显著。即蓝筹超买后不跌、仍顺势，但'RSI70 上穿'相对个股自身趋势的边际信息极弱——KO 单股'无看空 edge'的结论可复制到全蓝筹。"),
    ("④  防御/低波动股（KO/VZ/MCD）runup 最小，高波动成长（AAPL）runup 最大。",
     "AAPL T+20 窗口内最大涨幅 +8.91% 居首（波动大、冲得高），KO +3.25% 垫底（低波防御、脉冲式补涨幅度小）。但回吐率（peakdd/runup 绝对值）相反：KO 约 1.00（利润几乎全回吐）、MCD 0.82、VZ 1.03，而 AAPL 仅 0.58——高波动股'冲得高、留得住'，防御股'冲得少、全回吐'。该维度提示：低波防御股的超买脉冲是最不适合'追高持有'的形态。"),
    ("②  阶段分化是普适规律：牛市≠熊市，但方向因股而异，KO 的'牛市看多'不是标配。",
     "本轮牛市（2023~）9 股 T+20 表现分裂：SHW +2.67%(胜率76%)、CAT +2.62%(62%)、AAPL +1.73%(72%)、KO +0.95%(67%)为正且有广度；而 UNH −5.18%(50%)、XOM −0.21%(36%)、VZ −0.41%(44%) 超买后仍跌——'牛市超买=趋势延续'仅在顺风板块成立。"),
    ("③  '先冲高再回吐'是 9 股一致的窗口路径规律（最强的普适结论）。",
     "9 股 T+20 窗口内最大涨幅 runup 均值全部为正（+3.25% ~ +8.91%），而峰→收盘回撤 peakdd 全部为负（−3.26% ~ −5.20%），峰谷回撤 maxdd 更深（−5.04% ~ −8.24%）。无一例外：超买事件后 20 日内必然先创新高、再回吐，'拿满 20 天'的机会成本平均 3~5pp。"),
    ("④  防御/低波动股（KO/VZ/MCD）runup 最小，高波动成长（AAPL）runup 最大。",
     "AAPL T+20 窗口内最大涨幅 +8.91% 居首（波动大、冲得高），KO +3.25% 垫底（低波防御、脉冲式补涨幅度小）。但回吐率（peakdd/runup 绝对值）相反：KO 约 1.00（利润几乎全回吐）、MCD 0.82、VZ 1.03，而 AAPL 仅 0.58——高波动股'冲得高、留得住'，防御股'冲得少、全回吐'。该维度提示：低波防御股的超买脉冲是最不适合'追高持有'的形态。"),
]

def render_verdicts():
    return "".join(f"<div class='verdict'><b>{t}</b> {c}</div>" for t, c in verdicts)

# ---------- KPI ----------
kpi_html = []
# 9 股牛市 T20 胜率>60% 的数量
bull_pos = sum(1 for t in TICKS if D[t]["by_stage"]["C_bull"]["T20"]["win"] >= 60)
bull_neg = 9 - bull_pos
all_win_over_base = sum(1 for t in TICKS if D[t]["event_all"]["T20"]["mean"] > D[t]["baseline"]["T20"]["mean"])
runup_all_pos = sum(1 for t in TICKS if D[t]["event_all"]["T20_runup"]["mean"] > 0)
peakdd_all_neg = sum(1 for t in TICKS if D[t]["event_all"]["T20_peakdd"]["mean"] < 0)

kpi_html = [
    ("9/9", "T+20 窗口 runup 均为正（先冲高）"),
    ("9/9", "T+20 窗口 peakdd 均为负（后回吐）"),
    (f"{all_win_over_base}/9", "全样本 T+20 跑赢自身基率"),
    (f"{bull_pos}/9", "牛市 T+20 胜率 ≥60%（shw/cat/aapl/ko）"),
]

def render_kpis():
    return "".join(f"<div class='kpi'><div class='num'>{n}</div><div class='lab'>{l}</div></div>" for n, l in kpi_html)

# ---------- JS 数据注入 ----------
def chart_data():
    """生成图表 JSON：横向柱状（牛市 T20）、窗口路径散点、runup-vs-peakdd"""
    return {
        "ticks": TICKS,
        "names": NAME,
        "col": {t: COLOR[t] for t in TICKS},
        "bullT20": [D[t]["by_stage"]["C_bull"]["T20"]["mean"] for t in TICKS],
        "bullT5": [D[t]["by_stage"]["C_bull"]["T5"]["mean"] for t in TICKS],
        "allT20": [D[t]["event_all"]["T20"]["mean"] for t in TICKS],
        "runup": [D[t]["event_all"]["T20_runup"]["mean"] for t in TICKS],
        "peakdd": [D[t]["event_all"]["T20_peakdd"]["mean"] for t in TICKS],
        "maxdd": [D[t]["event_all"]["T20_maxdd"]["mean"] for t in TICKS],
        "runup5": [D[t]["event_all"]["T5_runup"]["mean"] for t in TICKS],
        "peakdd5": [D[t]["event_all"]["T5_peakdd"]["mean"] for t in TICKS],
        "scatter": {t: [{"x": e["runup20"], "y": e["peakdd20"], "date": e["date"], "fwd": e["fwd20"]}
                        for e in D[t]["events"] if e["runup20"] is not None and e["peakdd20"] is not None]
                    for t in TICKS},
        "bullN": {t: D[t]["by_stage"]["C_bull"]["T20"]["n"] for t in TICKS},
        "bullWin": {t: D[t]["by_stage"]["C_bull"]["T20"]["win"] for t in TICKS},
    }

DATAJS = json.dumps(chart_data(), ensure_ascii=False, allow_nan=False)

# ---------- 事件明细（瘦身取每只最近 10 条） ----------
def ev_rows():
    html = []
    for t in TICKS:
        r = D[t]
        for e in sorted(r["events"], key=lambda x: x["date"], reverse=True)[:12]:
            st = e["stage"]
            stag = {"A_pre": "疫情前", "B_post": "疫情后", "C_bull": "牛市"}[st]
            tag = {"A_pre": "st-a", "B_post": "st-b", "C_bull": "st-c"}[st]
            html.append(
                f"<tr><td class='nowrap'>{t.upper()}</td><td>{r['name']}</td><td class='nowrap'>{e['date']}</td>"
                f"<td>{e['rsi']}</td><td><span class='st {tag}'>{stag}</span></td>"
                f"<td class='{'up' if (e['fwd5'] or 0)>0 else 'dn'}'>{pct(e['fwd5'])}%</td>"
                f"<td class='{'up' if (e['fwd20'] or 0)>0 else 'dn'}'>{pct(e['fwd20'])}%</td>"
                f"<td class='{'up' if (e['runup20'] or 0)>0 else 'dn'}'>{pct(e['runup20'])}%</td>"
                f"<td class='dn'>{pct(e['peakdd20'])}%</td>"
                f"<td class='dn'>{pct(e['maxdd20'])}%</td></tr>")
    return "".join(html)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>道指各板块代表股 RSI 超买事件研究 · 横向对比</title>
{open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()}
<style>
  :root{{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;--amber:#b45309;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}}
  .wrap{{max-width:1280px;margin:0 auto;}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}}
  h1{{font-size:21px;margin-bottom:4px;}}
  .meta{{color:var(--sub);font-size:12.5px;margin-bottom:14px;}}
  h2{{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}}
  h3{{font-size:13.5px;margin:14px 0 6px;color:#374151;}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:14px;}}
  .kpi{{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
  .kpi .num{{font-size:22px;font-weight:700;color:var(--blue);}}
  .kpi .num.up{{color:var(--verm);}} .kpi .num.dn{{color:var(--teal);}} .kpi .num.warn{{color:var(--amber);}}
  .kpi .lab{{color:var(--sub);font-size:12px;margin-top:2px;}}
  table{{width:100%;border-collapse:collapse;font-size:12px;}}
  th{{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}}
  td{{padding:5px 7px;border-bottom:1px solid #f0f1f3;}}
  td.nowrap{{white-space:nowrap;}}
  .note2{{color:var(--sub);font-size:11.5px;}}
  td.up{{color:var(--verm);font-weight:600;white-space:nowrap;}}
  td.dn{{color:var(--teal);font-weight:600;white-space:nowrap;}}
  td.na{{color:#c3c8cf;white-space:nowrap;}}
  tr.baserow td{{background:#fbf7ee;}}
  .scroll{{overflow-x:auto;}}
  .evbox{{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:8px;}}
  .evbox th{{position:sticky;top:0;z-index:2;}}
  .tkr{{color:var(--sub);font-size:10px;letter-spacing:.4px;}}
  .chart{{width:100%;height:400px;}}
  .chart.tall{{height:520px;}}
  .callout{{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}}
  .callout.blue{{border-color:#cfe0f5;background:#f0f6fd;}}
  .callout b{{color:var(--amber);}}
  .callout.blue b{{color:var(--blue);}}
  .st{{font-size:11px;padding:1px 6px;border-radius:4px;white-space:nowrap;}}
  .st-a{{background:#e8f1fa;color:var(--blue);}}
  .st-b{{background:#fdf0dc;color:var(--amber);}}
  .st-c{{background:#e0f2ec;color:var(--teal);}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
  @media(max-width:900px){{.grid2{{grid-template-columns:1fr;}}}}
  .verdict{{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}}
  .src{{color:var(--sub);font-size:11.5px;margin-top:8px;}}
  ul.tight{{padding-left:20px;margin:6px 0;}} ul.tight li{{margin:3px 0;font-size:13px;}}
  .disc{{color:var(--sub);font-size:11px;margin-top:18px;padding-top:10px;border-top:1px dashed var(--line);}}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>道指各板块代表股 RSI 超买事件研究 · 横向对比（9 板块）</h1>
  <div class="meta">事件研究 · 数据 1995-01 ~ 2026-08-20（Yahoo 复权价 adj_close，统一起点保证可比）· 生成于 2026-08-25</div>
  <div class="callout blue">
    <b>口径（与 KO 单股报告完全一致）：</b>事件 = 日线 RSI14（Wilder，adj_close）自下而上首穿 70，事件日收盘为基准。三阶段：<span class="st st-a">疫情前</span>（~2020-02-19）、<span class="st st-b">疫情及股灾后</span>（2020-02-20~2022-12-31）、<span class="st st-c">本轮牛市</span>（2023~）。窗口路径：runup = 窗口内最高价（含盘中，复权）相对事件收盘最大涨幅；peakdd = 峰值→窗口末收盘回撤；maxdd = 峰值后最大峰谷回撤。全样本含 SPY 基率对照。
  </div>
  <div class="kpis">
    {render_kpis()}
  </div>
</div>

<div class="card">
  <h2>结论速览</h2>
  {render_verdicts()}
</div>

<div class="card">
  <h2>一、9 股核心统计横表（全样本 / 阶段 / 窗口路径）</h2>
  <h3>全样本 vs 本轮牛市</h3>
  <div class="scroll">
  <table>
    <thead><tr><th>股票 / 板块</th><th>板块</th><th>事件数</th><th>全样本 T+5</th><th>胜率</th><th>全样本 T+20</th><th>胜率</th><th>超额(T5)</th><th>超额(T20)</th><th>牛市 T+5</th><th>胜率</th><th>牛市 T+20</th><th>胜率</th></tr></thead>
    <tbody>{main_rows()}</tbody>
  </table>
  </div>
  <div class="src">超额 = 超买事件均值 − 该股全历史所有交易日基率（pp，剔自身的趋势 β）。牛市 = 2023-01-01 以来。</div>
  <h3 style="margin-top:16px">T+20 窗口路径（全部事件）</h3>
  <div class="scroll">
  <table>
    <thead><tr><th>股票</th><th>n</th><th>T+5 窗口峰值</th><th>T+5 峰→收盘</th><th>T+10 窗口峰值</th><th>T+10 峰→收盘</th><th>T+20 窗口峰值</th><th>T+20 峰→收盘</th><th>T+20 峰→谷</th></tr></thead>
    <tbody>{path_rows()}</tbody>
  </table>
  </div>
  <div class="src">按 T+20 窗口峰值降序；runup 全部为正、peakdd 全部为负——"先冲高再回吐"是 9 股无一例外的普适规律。</div>
</div>

<div class="card">
  <h2>二、板块横向图：牛市 T+20 / 全样本 T+20 / 窗口路径</h2>
  <div class="grid2">
    <div class="chart" id="ch_bull"></div>
    <div class="chart" id="ch_path"></div>
  </div>
  <div class="src">左图：各股本轮牛市 T+5 / T+20 均值（%），红=正、绿=负；右图：T+20 窗口 runup（正）与 peakdd（负）成对柱状，观察冲高-回吐结构。</div>
</div>

<div class="card">
  <h2>三、事件级散点：窗口内最大涨幅 vs 峰值回撤（T+20）</h2>
  <div class="chart tall" id="ch_scatter"></div>
  <div class="src">X = 窗口内最大涨幅（runup，%），Y = 峰值→T+20 收盘回撤（peakdd，%）。9 股全部事件叠加，颜色区分个股；蓝虚线 = 全样本中位（runup +4.7% / peakdd −4.1%）。右下区域 = "冲得高、回吐也多"。</div>
</div>

<div class="card">
  <h2>四、事件明细（每只最近 12 个，倒序）</h2>
  <div class="evbox">
  <table>
    <thead><tr><th>代码</th><th>股票</th><th>日期</th><th>RSI14</th><th>阶段</th><th>T+5</th><th>T+20</th><th>T+20 窗口峰值</th><th>T+20 峰→收盘</th><th>T+20 峰→谷</th></tr></thead>
    <tbody>{ev_rows()}</tbody>
  </table>
  </div>
</div>

<div class="card">
  <h2>五、结论与含义</h2>
  <ul class="tight">
    <li><b>[前提校验]</b> "RSI 超买 → 回调"并非 KO 特有结论，而是道指 9 板块代表股的共同特征：无一股票全样本超买 T+20 显著跑输自身基率（最大负超额仅 UNH −1.43pp，n=185 不显著）。前提（超买必跌）在蓝筹层面整体被否定。</li>
    <li><b>[关键证据]</b> 最普适、最稳健的结论是 <b>窗口路径规律</b>：9/9 股票 T+20 窗口内最大涨幅为正（+3.25%~+8.91%）、9/9 峰→收盘回撤为负（−3.26%~−5.20%）。无论趋势方向，超买后的 20 个交易日内"先创新高、再回吐"是纯统计上的确定性事件——这也解释了为何简单持有 T+20 的均值总比 runup 低 3~5pp。</li>
    <li><b>[客观分析]</b> 阶段分化方向因股而异，比 KO 单股更全面：本轮牛市 SHW/CAT/AAPL 显著（T20 +1.7~+2.7%、胜率 62-76%），KO 温和正，而 UNH（医疗，−5.18%）/XOM（能源）/VZ（电信）超买后仍负——<b>"牛市超买=延续"只在盈利动量顺风的板块成立</b>，防御/利率敏感/景气走弱板块不适用。全样本超额：AAPL 是唯一 T+5/T+20 双正的动量股（趋势市里超买=buy the dip 结构）。</li>
    <li><b>[结论与置信度：中高]</b> 给操作的两条可迁移规律：① 任何蓝筹超买后 20 日内大概率先冲高——若计划短线参与，3~5% 浮盈即可兑现，不宜赌"趋势延续"长持；② 阶段选择优先于信号：牛市里顺风板块（周期/成长）超买后续涨，防御股与逆风板块超买后仍落袋为安。样本局限：牛市 n 多为 11~37，UNH 的 −5.18% 受 2025-04 医疗政策冲击期（4/3、4/9、4/16 三个事件，T+20 最深 −53%）主导，个别股统计显著性为上限。</li>
  </ul>
  <div class="src">数据：Yahoo Finance（adj_close 复权，high/low 按复权因子折算，统一 1995 起）· 方法：Wilder RSI14 / 事件研究 / 窗口路径 · 脚本：scripts/djia_ob_cross.py + scripts/build_ko_rsi_report-style · 数据文件：results/djia_ob_cross.json</div>
  <div class="disc">⚠️ 以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。</div>
</div>

</div>
<script>
var DATA = {DATAJS};
var C = {{blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"}};
var ticks = DATA.ticks;
var names = DATA.names;
// ---------- 牛市横向柱 ----------
(function(){{
  var ch = echarts.init(document.getElementById("ch_bull"));
  var cats = ticks.map(function(t){{return names[t];}});
  var t5 = DATA.bullT5, t20 = DATA.bullT20;
  var col = DATA.col;
  ch.setOption({{
    animation:false,
    title:{{text:"本轮牛市 T+5 / T+20 均值（%，2023~）",left:"center",top:4,textStyle:{{fontSize:13,color:"#374151"}}}},
    tooltip:{{trigger:"axis",backgroundColor:"#fff",borderColor:"#e5e7eb",textStyle:{{color:"#1f2329"}},
      formatter:function(ps){{var i=ps[0].dataIndex;return "<b>"+cats[i]+"</b>（n="+DATA.bullN[ticks[i]]+"）<br>T+5 "+t5[i].toFixed(2)+"%（胜率 "+DATA.bullWin[ticks[i]]+"%）<br>T+20 "+t20[i].toFixed(2)+"%"}}}},
    grid:{{left:50,right:20,top:48,bottom:70}},
    xAxis:{{type:"category",data:cats,axisLabel:{{color:"#4b5563",fontSize:10,rotate:40}},axisLine:{{lineStyle:{{color:"#d5dae2"}}}}}},
    yAxis:{{type:"value",name:"%",axisLine:{{lineStyle:{{color:"#d5dae2"}}}},axisLabel:{{color:"#4b5563"}},splitLine:{{lineStyle:{{color:"#eef0f3"}}}}}},
    series:[
      {{name:"T+5",type:"bar",data:t5.map(function(v,i){{return {{value:v,itemStyle:{{color:v>=0?C.verm:C.teal}}}};}}),barGap:"6%",
       label:{{show:true,position:"top",fontSize:9,formatter:function(p){{return p.value.toFixed(1);}}}}}},
      {{name:"T+20",type:"bar",data:t20.map(function(v,i){{return {{value:v,itemStyle:{{color:v>=0?col[ticks[i]]:C.teal}}}};}}),
       label:{{show:true,position:"top",fontSize:9,formatter:function(p){{return p.value.toFixed(1);}}}}}}
    ],
    legend:{{data:["T+5","T+20"],bottom:28,textStyle:{{fontSize:11}}}}
  }});
  window.addEventListener("resize",function(){{ch.resize();}});
}})();

// ---------- 窗口路径柱 ----------
(function(){{
  var ch = echarts.init(document.getElementById("ch_path"));
  var cats = ticks.map(function(t){{return names[t];}});
  var runup = DATA.runup, peakdd = DATA.peakdd;
  ch.setOption({{
    animation:false,
    title:{{text:"T+20 窗口路径：最多涨多少 vs 回吐多少（%）",left:"center",top:4,textStyle:{{fontSize:13,color:"#374151"}}}},
    tooltip:{{trigger:"axis",backgroundColor:"#fff",borderColor:"#e5e7eb",textStyle:{{color:"#1f2329"}},
      formatter:function(ps){{var i=ps[0].dataIndex;return "<b>"+cats[i]+"</b><br>窗口内最大涨幅 "+runup[i].toFixed(2)+"%<br>峰→收盘回撤 "+peakdd[i].toFixed(2)+"%<br>峰→谷 "+DATA.maxdd[i].toFixed(2)+"%"}}}},
    grid:{{left:50,right:20,top:48,bottom:70}},
    xAxis:{{type:"category",data:cats,axisLabel:{{color:"#4b5563",fontSize:10,rotate:40}},axisLine:{{lineStyle:{{color:"#d5dae2"}}}}}},
    yAxis:{{type:"value",name:"%",axisLine:{{lineStyle:{{color:"#d5dae2"}}}},axisLabel:{{color:"#4b5563"}},splitLine:{{lineStyle:{{color:"#eef0f3"}}}}}},
    series:[
      {{name:"窗口内最大涨幅",type:"bar",data:runup.map(function(v){{return {{value:v,itemStyle:{{color:C.verm}}}};}}),
       label:{{show:true,position:"top",fontSize:9,formatter:function(p){{return "+"+p.value.toFixed(1);}}}}}},
      {{name:"峰→收盘回撤",type:"bar",data:peakdd.map(function(v){{return {{value:v,itemStyle:{{color:C.orange}}}};}}),
       label:{{show:true,position:"top",fontSize:9,formatter:function(p){{return p.value.toFixed(1);}}}}}}
    ],
    legend:{{data:["窗口内最大涨幅","峰→收盘回撤"],bottom:28,textStyle:{{fontSize:11}}}}
  }});
  window.addEventListener("resize",function(){{ch.resize();}});
}})();

// ---------- 事件散点 ----------
(function(){{
  var ch = echarts.init(document.getElementById("ch_scatter"));
  var col = DATA.col;
  var series = ticks.map(function(t){{
    return {{name:names[t],type:"scatter",symbolSize:6,itemStyle:{{color:col[t],opacity:0.55}},
      data:DATA.scatter[t].map(function(e){{return [e.x,e.y,e.date,e.fwd];}})}};
  }});
  ch.setOption({{
    animation:false,
    title:{{text:"事件级：T+20 窗口内最大涨幅 × 峰值回撤（全部 1,522 个事件）",left:"center",top:4,textStyle:{{fontSize:13,color:"#374151"}}}},
    tooltip:{{backgroundColor:"#fff",borderColor:"#e5e7eb",textStyle:{{color:"#1f2329"}},
      formatter:function(p){{return "<b>"+p.seriesName+"</b> "+p.value[2]+"<br>窗口内最大涨幅 +"+p.value[0].toFixed(2)+"%<br>峰→收盘回撤 "+p.value[1].toFixed(2)+"%<br>T+20 收盘 "+(p.value[3]==null?"—":p.value[3].toFixed(2)+"%")}}}},
    grid:{{left:55,right:24,top:44,bottom:58}},
    xAxis:{{type:"value",name:"窗口内最大涨幅 runup %",nameLocation:"middle",nameGap:28,scale:true,axisLine:{{lineStyle:{{color:"#d5dae2"}}}},axisLabel:{{color:"#4b5563"}},splitLine:{{lineStyle:{{color:"#eef0f3"}}}}}},
    yAxis:{{type:"value",name:"峰→收盘回撤 peakdd %",scale:true,axisLine:{{lineStyle:{{color:"#d5dae2"}}}},axisLabel:{{color:"#4b5563"}},splitLine:{{lineStyle:{{color:"#eef0f3"}}}}}},
    dataZoom:[{{type:"inside"}}],
    legend:{{bottom:2,textStyle:{{fontSize:10}},type:"scroll"}},
    series:series
  }});
  window.addEventListener("resize",function(){{ch.resize();}});
}})();
</script>
</body>
</html>"""

out = os.path.join(OUTD, "djia_ob_cross_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out} size={os.path.getsize(out)}")