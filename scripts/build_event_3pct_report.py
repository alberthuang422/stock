#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成生物医药股涨3%事件研究报告 (reports/10_3pct_event/3pct_event_report.html)
读 results/event_3pct_biopharma.json
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "event_3pct_biopharma.json"), encoding="utf-8") as f:
    D = json.load(f)

P, B = D["pooled"]["PHARMA"], D["pooled"]["BIOTECH"]
CP, CB = D["ctrl"]["PHARMA"], D["ctrl"]["BIOTECH"]
TP, TB = D["tickers"]["PHARMA"], D["tickers"]["BIOTECH"]
EX = D["excess"]

NS = ("T1", "T5", "T10")
NSL = {"T1": "T+1", "T5": "T+5", "T10": "T+10"}
POOL_LABEL = {"PHARMA": "制药大票(9)", "BIOTECH": "生物科技(5)"}


def fmt_pct(v, nd=2):
    return f"{v:+.{nd}f}%" if v is not None else "—"


def cls(v):
    if v is None:
        return "na"
    return "up" if v > 0 else ("dn" if v < 0 else "")


# ============ 1. 图表数据 ============
data_js = {
    # 图1: 事件 vs 小涨对照, 6组
    "fig1_cats": [f"{POOL_LABEL[p]} {NSL[n]}" for p in ["PHARMA", "BIOTECH"] for n in NS],
    "fig1_evt": [P[n]["mean"] for n in NS] + [B[n]["mean"] for n in NS],
    "fig1_ctrl": [CP["small_up"][n]["mean"] for n in NS] + [CB["small_up"][n]["mean"] for n in NS],
    # 图2: 分档折线 (中位数)
    "fig2_x": ["T+1", "T+5", "T+10"],
    "fig2_p35": [P["band_35"][n]["med"] for n in NS],
    "fig2_p5p": [P["band_5p"][n]["med"] for n in NS],
    "fig2_b35": [B["band_35"][n]["med"] for n in NS],
    "fig2_b5p": [B["band_5p"][n]["med"] for n in NS],
    # 图3: 个股 T+10 中位
    "fig3_p_tkrs": list(TP.keys()),
    "fig3_p_t10": [TP[t]["T10"]["med"] for t in TP],
    "fig3_p_win": [TP[t]["T10"]["win"] for t in TP],
    "fig3_p_n": [TP[t]["n"] for t in TP],
    "fig3_b_tkrs": list(TB.keys()),
    "fig3_b_t10": [TB[t]["T10"]["med"] for t in TB],
    "fig3_b_win": [TB[t]["T10"]["win"] for t in TB],
    "fig3_b_n": [TB[t]["n"] for t in TB],
    # 图4: 年份
    "fig4_p_years": [y["year"] for y in P["years"]],
    "fig4_p_t5": [y["T5"]["med"] for y in P["years"]],
    "fig4_p_win5": [y["T5"]["win"] for y in P["years"]],
    "fig4_b_years": [y["year"] for y in B["years"]],
    "fig4_b_t5": [y["T5"]["med"] for y in B["years"]],
    "fig4_b_win5": [y["T5"]["win"] for y in B["years"]],
}
DATA_JSON = json.dumps(data_js, ensure_ascii=False)

# ============ 2. KPI 卡 ============
def kpi(v, lab, upgood=True):
    c = cls(v)
    return f'<div class="kpi"><div class="num {c}">{fmt_pct(v)}</div><div class="lab">{lab}</div></div>'

kpis = f"""
<div class="kpis">
  <div class="kpi"><div class="num">{P['n_evt']}</div><div class="lab">制药大票 涨≥3% 事件数（2015-2026.8）</div></div>
  {kpi(P['T1']['mean'], '制药 T+1 平均收益（次日）')}
  {kpi(P['T1']['win'] / 100.0 - 1.0 if False else P['T1']['win'] - 100.0, '', False) if False else ''}
  <div class="kpi"><div class="num {cls(P['T1']['win'] - 50.0)}">{P['T1']['win']}%</div><div class="lab">制药 T+1 上涨概率（<50% 即次日偏回落）</div></div>
  <div class="kpi"><div class="num {cls(P['T10']['med'])}">{fmt_pct(P['T10']['med'])}</div><div class="lab">制药 T+10 中位收益</div></div>
  <div class="kpi"><div class="num {cls(P['band_5p']['T1']['win'] - 50.0)}">{P['band_5p']['T1']['win']}%</div><div class="lab">制药 涨≥5% 后 T+1 上涨概率</div></div>
</div>
<div class="kpis">
  <div class="kpi"><div class="num">{B['n_evt']}</div><div class="lab">生物科技 涨≥3% 事件数</div></div>
  {kpi(B['T1']['mean'], '生物科技 T+1 平均收益（次日）')}
  <div class="kpi"><div class="num {cls(B['T1']['win'] - 50.0)}">{B['T1']['win']}%</div><div class="lab">生物科技 T+1 上涨概率</div></div>
  <div class="kpi"><div class="num {cls(B['T10']['med'])}">{fmt_pct(B['T10']['med'])}</div><div class="lab">生物科技 T+10 中位收益</div></div>
  <div class="kpi"><div class="num {cls(B['band_5p']['T5']['win'] - 50.0)}">{B['band_5p']['T5']['win']}%</div><div class="lab">生物科技 涨≥5% 后 T+5 上涨概率</div></div>
</div>
"""

# ============ 3. 核心统计表 ============
def stats_row(label, d, is_evt=False):
    n = d.get("n", d["T1"]["n"])
    cells = f'<td class="{ "hl" if is_evt else "" }">{label}</td><td>{n}</td>'
    for n in NS:
        s = d[n]
        cells += (f'<td class="{cls(s["mean"])}">{fmt_pct(s["mean"])}</td>'
                  f'<td class="{cls(s["med"])}">{fmt_pct(s["med"])}</td>'
                  f'<td class="{cls(s["win"] - 50)}">{s["win"]}%</td>')
    return f"<tr>{cells}</tr>"

tbl_rows_p = "".join([
    stats_row("事件 · 当日涨≥3%", {k: P[k] for k in NS}, True),
    stats_row("事件 · 3% ~ 5%", {k: P["band_35"][k] for k in NS}),
    stats_row("事件 · ≥5%", {k: P["band_5p"][k] for k in NS}),
    stats_row("稳健性 · 10日冷却期事件", {k: P["cooldown10"][k] for k in NS}),
    stats_row("对照 · 小涨日(0~3%)", {k: CP["small_up"][k] for k in NS}),
    stats_row("对照 · 全部非事件日", {k: CP["all"][k] for k in NS}),
])
tbl_rows_b = "".join([
    stats_row("事件 · 当日涨≥3%", {k: B[k] for k in NS}, True),
    stats_row("事件 · 3% ~ 5%", {k: B["band_35"][k] for k in NS}),
    stats_row("事件 · ≥5%", {k: B["band_5p"][k] for k in NS}),
    stats_row("稳健性 · 10日冷却期事件", {k: B["cooldown10"][k] for k in NS}),
    stats_row("对照 · 小涨日(0~3%)", {k: CB["small_up"][k] for k in NS}),
    stats_row("对照 · 全部非事件日", {k: CB["all"][k] for k in NS}),
])

# 超额表
xs_rows = ""
for p, label in [("PHARMA", "制药大票"), ("BIOTECH", "生物科技")]:
    for n in NS:
        e = EX[f"{p}_{n}"]
        s_spy, s_sec = e["xs_spy"], e["xs_sec"]
        xs_rows += (f'<tr><td>{label}</td><td>{NSL[n]}</td>'
                    f'<td class="{cls(s_spy["mean"])}">{fmt_pct(s_spy["mean"])}</td>'
                    f'<td class="{cls(s_spy["med"])}">{fmt_pct(s_spy["med"])}</td>'
                    f'<td class="{cls(s_spy["win"] - 50)}">{s_spy["win"]}%</td>'
                    f'<td class="{cls(s_sec["mean"])}">{fmt_pct(s_sec["mean"])}</td>'
                    f'<td class="{cls(s_sec["med"])}">{fmt_pct(s_sec["med"])}</td>'
                    f'<td class="{cls(s_sec["win"] - 50)}">{s_sec["win"]}%</td></tr>')

# ============ 4. 个股明细表 ============
def tkr_row(t, x):
    s1, s5, s10, x10 = x["T1"], x["T5"], x["T10"], x["xs_spy10"]
    return (f'<tr><td class="hl">{t}</td><td>{x["n"]}</td><td>{x["n_year"]:.1f}</td>'
            f'<td>{x["ret_mean"]:.2f}%</td>'
            f'<td class="{cls(s1["mean"])}">{fmt_pct(s1["mean"])}</td><td class="{cls(s1["win"] - 50)}">{s1["win"]}%</td>'
            f'<td class="{cls(s5["med"])}">{fmt_pct(s5["med"])}</td><td class="{cls(s5["win"] - 50)}">{s5["win"]}%</td>'
            f'<td class="{cls(s10["med"])}">{fmt_pct(s10["med"])}</td><td class="{cls(s10["win"] - 50)}">{s10["win"]}%</td>'
            f'<td class="{cls(x10["med"])}">{fmt_pct(x10["med"])}</td></tr>')

tkr_rows_p = "".join(tkr_row(t, TP[t]) for t in TP)
tkr_rows_b = "".join(tkr_row(t, TB[t]) for t in TB)

# ============ 5. 年份表 ============
def year_rows(pool):
    out = ""
    for y in pool["years"]:
        s5, s10 = y["T5"], y["T10"]
        out += (f'<tr><td>{y["year"]}</td><td>{y["n"]}</td>'
                f'<td class="{cls(s5["mean"])}">{fmt_pct(s5["mean"])}</td><td class="{cls(s5["med"])}">{fmt_pct(s5["med"])}</td><td class="{cls(s5["win"] - 50)}">{s5["win"]}%</td>'
                f'<td class="{cls(s10["mean"])}">{fmt_pct(s10["mean"])}</td><td class="{cls(s10["med"])}">{fmt_pct(s10["med"])}</td><td class="{cls(s10["win"] - 50)}">{s10["win"]}%</td></tr>')
    return out

yr_p = year_rows(P)
yr_b = year_rows(B)

# ============ 6. 页面模板 ============
TPL = open(os.path.join(ROOT, "scripts", "_report_template.html"), encoding="utf-8").read()
# 取模板的 <style> 部分复用
style = TPL.split("<style>")[1].split("</style>")[0]
style = style.replace("--red:#e03131;", "--red:#e03131;--up:#e03131;--dn:#0aa06e;--blue:#1e66d6;--orange:#e8930c;")

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>生物医药股 当日涨≥3% 后走势 · 事件研究（T+1/T+5/T+10）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
__STYLE__
  .kpis{grid-template-columns:repeat(auto-fit,minmax(175px,1fr));}
  .tbl{font-size:12px;}
  .tbl th,.tbl td{padding:5px 6px;}
  .grp{background:#f3f5f8;font-weight:700;}
  .chip{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;margin-right:6px;}
  .chip.evt{background:#e7f0fb;color:#1e66d6;border:1px solid #c7d9f5;}
  .chip.ctrl{background:#fdf3e3;color:#b45309;border:1px solid #f3ddb8;}
  .two{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
  @media(max-width:900px){.two{grid-template-columns:1fr;}}
  .chart{width:100%;height:340px;}
  .chart.tall{height:400px;}
  .neg{color:var(--dn);} .pos{color:var(--up);}
  .conc{font-size:13.5px;line-height:2;}
  .conc b{color:#17442f;}
  .conc .head{font-weight:700;color:#0b4d8c;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>生物医药股「当日涨 ≥3%」后走势 · 事件研究</h1>
  <div class="meta">标的池：制药大票 9 只（GILD / ABBV / LLY / AMGN / VRTX / MRK / JNJ / REGN / BIIB）＋ 生物科技 5 只（ALNY / NTRA / ILMN / RVMD / ARGX）｜数据：Yahoo 日线 __RANGE__（复权 adj_close，与看盘软件对齐）｜事件：当日收盘涨幅 ≥ +3%（严格阈值，无容差），共 <b>__N_EVT_P__ 个制药事件 / __N_EVT_B__ 个生物科技事件</b>｜收益口径：事件日收盘买入持有至 T+1 / T+5 / T+10 收盘，不含成本｜对照组：同股「小涨日(0~3%)」与「全部非事件日」</div>

  <div class="keypoint" style="margin-top:14px;">
    <b style="font-size:14px;">一句话结论：</b>制药大票单日大涨是「事件脉冲」，次日大概率回落、越猛越危险（≥5% 次日胜率仅 39%），<b>不宜追涨</b>；生物科技大涨后 T+10 确有正收益（中位 +1.1%、胜率 53%），但与小涨日无差异 —— 吃的是<b>板块常态波动（beta）</b>而非事件动量（α），且 2026 年以来两池追涨信号均已转弱。
  </div>
</div>

<div class="card">
  <h2>核心指标一览</h2>
  __KPIS__
  <div class="note">KPI 为两池合并事件统计；上涨概率以 50% 为分界（低于 50% 表示次日/持有期更可能收跌）。</div>
</div>

<div class="card">
  <h2>1. 涨≥3% 后 vs 「小涨日(0~3%)」：追涨是动量还是反转？</h2>
  <div class="lgd"><span><span class="dot" style="background:#1e66d6;"></span>事件日（涨≥3%）后持有收益（均值）</span><span><span class="dot" style="background:#e8930c;"></span>对照·小涨日（0~3%）后持有收益（均值）</span></div>
  <div id="fig1" class="chart tall"></div>
  <div class="keypoint">
    <b>制药大票：大涨后反而跑输自己的小涨日。</b>涨≥3% 后 T+1 均值 −0.13%（胜率 46.3%），而小涨日 T+1 为 +0.05%（胜率 51.4%）—— 单日大涨的次日更倾向回吐；T+10 事件 +0.24% 也低于小涨日 +0.45%。<br>
    <b>生物科技：大涨后与平日无异。</b>T+1 中性（+0.05%，胜率 49.6%），T+10 事件 +1.25% vs 小涨日 +1.28%，几乎重合 —— 大涨后没有额外动量，收益主要来自板块本身的高波动常态。
  </div>
</div>

<div class="card">
  <h2>2. 涨幅分档：涨 3~5% 与涨 ≥5% 命运完全不同</h2>
  <div class="lgd">
    <span><span class="dot" style="background:#1e66d6;"></span>制药 3~5%</span>
    <span><span class="dot" style="background:#56b4e9;"></span>制药 ≥5%</span>
    <span><span class="dot" style="background:#e8930c;"></span>生物科技 3~5%</span>
    <span><span class="dot" style="background:#f4b942;"></span>生物科技 ≥5%</span>
  </div>
  <div id="fig2" class="chart"></div>
  <div class="keypoint">
    <b>制药：涨得越猛、次日越危险。</b>≥5% 的 262 次事件后，T+1 中位 −0.49%、胜率仅 <b>39.3%</b>（3~5% 档为 48.9%），T+5/T+10 中位数也始终为负 —— 大涨 5%+ 基本对应财报/并购/审批等一次性利好，次日即回吐。<br>
    <b>生物科技：恰恰相反，大涨有延续。</b>≥5% 档 T+5 中位 +0.90%、胜率 <b>56.0%</b>，T+10 +1.61%；而 3~5% 档 T+5 仅 +0.05%/47.6% —— 生物科技的大涨多为临床/管线催化，「涨不动的小涨」反而没有信号意义。
  </div>
</div>

<div class="card">
  <h2>3. 核心统计表（含超额收益）</h2>
  <div class="two">
    <div>
      <h2 style="font-size:14px;">制药大票（9 只）</h2>
      <div class="scroll"><table class="tbl">
        <thead><tr><th>口径</th><th>n</th><th>T+1均值</th><th>T+1中位</th><th>T+1胜率</th><th>T+5均值</th><th>T+5中位</th><th>T+5胜率</th><th>T+10均值</th><th>T+10中位</th><th>T+10胜率</th></tr></thead>
        <tbody>__TBL_P__</tbody>
      </table></div>
    </div>
    <div>
      <h2 style="font-size:14px;">生物科技（5 只）</h2>
      <div class="scroll"><table class="tbl">
        <thead><tr><th>口径</th><th>n</th><th>T+1均值</th><th>T+1中位</th><th>T+1胜率</th><th>T+5均值</th><th>T+5中位</th><th>T+5胜率</th><th>T+10均值</th><th>T+10中位</th><th>T+10胜率</th></tr></thead>
        <tbody>__TBL_B__</tbody>
      </table></div>
    </div>
  </div>
  <div class="note">胜率 = 持有至 T+N 收盘收益为正的比例（%）。「10日冷却期」为稳健性口径：同一股票 10 个交易日内多次触发只计首次，用于剔除连续大涨的重叠影响。</div>
  <h2 style="font-size:14px;margin-top:16px;">超额收益：事件后个股 vs 基准（均值/中位/胜率）</h2>
  <div class="scroll"><table class="tbl">
    <thead><tr><th>池</th><th>窗口</th><th>vs SPY 均值</th><th>vs SPY 中位</th><th>vs SPY 胜率</th><th>vs 板块均值</th><th>vs 板块中位</th><th>vs 板块胜率</th></tr></thead>
    <tbody>__TBL_XS__</tbody>
  </table></div>
  <div class="note">板块基准：制药 → XLV（医疗保健 ETF）、生物科技 → IBB（生物科技 ETF）。超额 = 个股 T+N 持有收益 − 基准同期持有收益。</div>
</div>

<div class="card">
  <h2>4. 个股分化：谁追得、谁追不得</h2>
  <div class="two">
    <div><div id="fig3p" class="chart"></div></div>
    <div><div id="fig3b" class="chart"></div></div>
  </div>
  <div class="scroll"><table class="tbl">
    <thead><tr><th>标的</th><th>事件数</th><th>年均</th><th>事件日均涨</th><th>T+1均值</th><th>T+1胜率</th><th>T+5中位</th><th>T+5胜率</th><th>T+10中位</th><th>T+10胜率</th><th>vs SPY T+10中位</th></tr></thead>
    <tbody>__TKR_P____TKR_B__</tbody>
  </table></div>
  <div class="keypoint">
    <b>制药池里相对能追：</b>LLY（n=132，T+10 胜率 58.3%）、AMGN（58.5%）、JNJ（65.6%，n=32 样本小）—— 趋势型标的，大涨后延续性强；<b>追不得：</b>MRK（T+10 −0.84%/43.8%）、REGN（−0.36%/48.2%）、GILD（−0.38%/47.4%）、VRTX（T+1 仅 43.5%）。<br>
    <b>生物科技池里相对能追：</b>NTRA（n=472，T+10 +2.14%/59.3%，超额 SPY +1.01%）、ILMN（+1.21%）、ARGX（+1.05%）；<b>追不得：</b>ALNY（T+10 −0.27%，超额 −1.10%）、RVMD（−0.54%）。
  </div>
</div>

<div class="card">
  <h2>5. 年份视角：追涨胜率随板块环境起伏</h2>
  <div class="two">
    <div><div id="fig4p" class="chart"></div></div>
    <div><div id="fig4b" class="chart"></div></div>
  </div>
  <div class="scroll"><table class="tbl">
    <thead><tr><th>年份</th><th>n</th><th>T+5均值</th><th>T+5中位</th><th>T+5胜率</th><th>T+10均值</th><th>T+10中位</th><th>T+10胜率</th></tr></thead>
    <tbody>
      <tr class="grp"><td colspan="8">制药大票</td></tr>__YR_P__
      <tr class="grp"><td colspan="8">生物科技</td></tr>__YR_B__
    </tbody>
  </table></div>
  <div class="keypoint">
    <b>大涨后追涨的有效性高度依赖当年板块环境。</b>制药池：2023（T+5 胜率 71.1%）、2021（60.9%）、2025（57.8%）是追涨好年份；2016（40.2%）、2018（47.6%）、<b>2026（39.3%）</b>追涨必挨打。生物科技：2019-2020 疫情牛（60%/57%）、2024-2025 好；2021-2023 连续三年胜率 <48%。<b>当前 2026 年，制药池大涨后 T+5 中位 −1.03%、胜率 39.3%，生物科技 T+10 也已转负（−0.54%）</b> —— 与 8/18 板块大跌、生物医药整体弱势的环境一致。
  </div>
</div>

<div class="card">
  <h2>6. 方法口径与局限</h2>
  <div class="conc">
    <span class="head">口径：</span>收益一律用<b>复权收盘价（adj_close）</b>；事件 = 当日复权收益 ≥ +3%；持有收益 = 事件日收盘 → 第 N 个交易日收盘；事件日须具备 T+10 数据（尾部不足 10 个交易日的事件剔除）；合并统计为 pooled（每个事件 = 1 个样本，未按股票加权）。<br>
    <span class="head">检验：</span>t 检验（均值 vs 0）与二项检验（胜率 vs 50%，正态近似）；显著性标注见「关键数据」表，制药 T+10 t=1.13（不显著）、生物科技 T+10 t=4.23（p&lt;0.001 显著）。<br>
    <span class="head">局限：</span>① 事件为「无差异事件」，混合了财报、并购、临床数据、评级调整等各类催化剂，未分类；② 未扣除交易成本；③ 10 日冷却期稳健性版本结论与主版本一致（制药 T+10 +0.25% vs +0.24%，生物科技 +1.27% vs +1.25%），重叠事件未扭曲结果；④ 生物科技池含 ILMN（测序工具）等非纯药标的；⑤ 2026 年数据截至 8 月中旬，样本 <90 次/池，统计稳定性有限；⑥ 历史规律不构成未来保证，尤其当前板块处于阴跌环境。
  </div>
  <div class="dis">数据：Yahoo Finance 日线（复权）· __RANGE__｜分析脚本：scripts/event_3pct_analyze.py｜报告生成：scripts/build_event_3pct_report.py｜统计单位：%｜事件研究无未来函数，持有收益为事后观察。</div>
</div>

</div>
<script>
const DATA = __DATA_JS__;
const INK = '#1f2329', SUB = '#6b7280', LINE = '#e5e7eb';
const C_EVT = '#1e66d6', C_CTRL = '#e8930c';
const base = {
  textStyle:{color:INK,fontSize:12},
  color:[C_EVT,C_CTRL,'#56b4e9','#cc79a7','#e8930c','#b45309'],
  grid:{left:52,right:52,top:44,bottom:30},
  tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:LINE,textStyle:{color:INK}},
  legend:{top:6,textStyle:{color:SUB},itemWidth:18,itemHeight:10}
};
const marker = {itemStyle:{borderWidth:0}};

// 图1: 事件 vs 小涨对照
echarts.init(document.getElementById('fig1')).setOption(Object.assign({}, base, {
  legend:Object.assign({}, base.legend, {data:['涨≥3%事件后','小涨日(0~3%)对照']}),
  xAxis:{type:'category',data:DATA.fig1_cats,axisLine:{lineStyle:{color:LINE}},axisLabel:{color:INK}},
  yAxis:{type:'value',name:'持有收益(%)',axisLine:{lineStyle:{color:LINE}},splitLine:{lineStyle:{color:'#f0f1f3'}}},
  series:[
    {name:'涨≥3%事件后',type:'bar',data:DATA.fig1_evt,barWidth:22,
     label:{show:true,position:'top',formatter:p=>p.value>0?'+'+p.value+'%':p.value+'%',color:SUB,fontSize:11},
     itemStyle:{color:C_EVT}},
    {name:'小涨日(0~3%)对照',type:'bar',data:DATA.fig1_ctrl,barWidth:22,
     label:{show:true,position:'top',formatter:p=>p.value>0?'+'+p.value+'%':p.value+'%',color:SUB,fontSize:11},
     itemStyle:{color:C_CTRL}}
  ]
}));

// 图2: 分档折线 (中位)
echarts.init(document.getElementById('fig2')).setOption(Object.assign({}, base, {
  legend:Object.assign({}, base.legend, {data:['制药 3~5%','制药 ≥5%','生科 3~5%','生科 ≥5%']}),
  xAxis:{type:'category',data:DATA.fig2_x,axisLine:{lineStyle:{color:LINE}},axisLabel:{color:INK}},
  yAxis:{type:'value',name:'中位持有收益(%)',axisLine:{lineStyle:{color:LINE}},splitLine:{lineStyle:{color:'#f0f1f3'}}},
  series:[
    {name:'制药 3~5%',type:'line',data:DATA.fig2_p35,smooth:true,symbolSize:8,itemStyle:{color:C_EVT},lineStyle:{color:C_EVT,width:3}},
    {name:'制药 ≥5%',type:'line',data:DATA.fig2_p5p,smooth:true,symbolSize:8,itemStyle:{color:'#56b4e9'},lineStyle:{color:'#56b4e9',width:3,type:'dashed'}},
    {name:'生科 3~5%',type:'line',data:DATA.fig2_b35,smooth:true,symbolSize:8,itemStyle:{color:'#e8930c'},lineStyle:{color:'#e8930c',width:3}},
    {name:'生科 ≥5%',type:'line',data:DATA.fig2_b5p,smooth:true,symbolSize:8,itemStyle:{color:'#f4b942'},lineStyle:{color:'#f4b942',width:3,type:'dashed'}}
  ]
}));

function tkrChart(el, tkrs, t10, win, n, title){
  const labels = tkrs.map((t,i)=> t + (n[i]>=300?'':''));
  const colors = t10.map(v=> v>=0 ? '#e03131' : '#0aa06e');
  echarts.init(document.getElementById(el)).setOption(Object.assign({}, base, {
    title:{text:title,left:6,top:0,textStyle:{fontSize:13,color:INK,fontWeight:700}},
    grid:{left:52,right:60,top:34,bottom:30},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:LINE,textStyle:{color:INK},
      formatter:ps=>{const i=ps[0].dataIndex;return tkrs[i]+'<br>事件数 '+n[i]+' · T+10中位 '+t10[i]+'%<br>胜率 '+win[i]+'%';}},
    xAxis:{type:'category',data:labels,axisLine:{lineStyle:{color:LINE}},axisLabel:{color:INK,fontSize:11}},
    yAxis:{type:'value',name:'T+10中位(%)',axisLine:{lineStyle:{color:LINE}},splitLine:{lineStyle:{color:'#f0f1f3'}}},
    series:[{type:'bar',data:t10.map((v,i)=>({value:v})),barWidth:'55%',
      itemStyle:{color:p=>colors[p.dataIndex]},
      label:{show:true,position:'top',formatter:p=>{const i=p.dataIndex;return win[i]+'%';},color:SUB,fontSize:10.5}}]
  }));
}
tkrChart('fig3p', DATA.fig3_p_tkrs, DATA.fig3_p_t10, DATA.fig3_p_win, DATA.fig3_p_n, '制药大票 · 涨≥3%后 T+10 中位收益(柱, %)+胜率(标)');
tkrChart('fig3b', DATA.fig3_b_tkrs, DATA.fig3_b_t10, DATA.fig3_b_win, DATA.fig3_b_n, '生物科技 · 涨≥3%后 T+10 中位收益(柱, %)+胜率(标)');

function yearChart(el, years, t5, win5, title){
  echarts.init(document.getElementById(el)).setOption(Object.assign({}, base, {
    title:{text:title,left:6,top:0,textStyle:{fontSize:13,color:INK,fontWeight:700}},
    legend:Object.assign({}, base.legend, {data:['T+5中位收益(%)','T+5胜率(%)'],top:24}),
    grid:{left:52,right:52,top:56,bottom:30},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:LINE,textStyle:{color:INK}},
    xAxis:{type:'category',data:years,axisLine:{lineStyle:{color:LINE}},axisLabel:{color:INK}},
    yAxis:[
      {type:'value',name:'中位(%)',axisLine:{lineStyle:{color:LINE}},splitLine:{lineStyle:{color:'#f0f1f3'}}},
      {type:'value',name:'胜率(%)',min:30,max:80,axisLine:{lineStyle:{color:LINE}},splitLine:{show:false}}
    ],
    series:[
      {name:'T+5中位收益(%)',type:'bar',data:t5,barWidth:'50%',
       itemStyle:{color:p=>p.value>=0?'#1e66d6':'#0aa06e'},
       label:{show:true,position:'top',formatter:p=>(p.value>0?'+':'')+p.value+'%',color:SUB,fontSize:10}},
      {name:'T+5胜率(%)',type:'line',data:win5,yAxisIndex:1,smooth:true,symbolSize:7,
       itemStyle:{color:'#b45309'},lineStyle:{color:'#b45309',width:2.5},
       label:{show:true,position:'bottom',formatter:'{c}%',color:'#b45309',fontSize:10}}
    ]
  }));
}
yearChart('fig4p', DATA.fig4_p_years, DATA.fig4_p_t5, DATA.fig4_p_win5, '制药大票 · 逐年 T+5 表现');
yearChart('fig4b', DATA.fig4_b_years, DATA.fig4_b_t5, DATA.fig4_b_win5, '生物科技 · 逐年 T+5 表现');
</script>
</body>
</html>
"""

for k, v in {
    "__STYLE__": style,
    "__RANGE__": D["meta"]["range"],
    "__N_EVT_P__": str(P["n_evt"]),
    "__N_EVT_B__": str(B["n_evt"]),
    "__KPIS__": kpis,
    "__TBL_P__": tbl_rows_p,
    "__TBL_B__": tbl_rows_b,
    "__TBL_XS__": xs_rows,
    "__TKR_P__": tkr_rows_p,
    "__TKR_B__": tkr_rows_b,
    "__YR_P__": yr_p,
    "__YR_B__": yr_b,
    "__DATA_JS__": DATA_JSON,
}.items():
    HTML = HTML.replace(k, v)

outdir = os.path.join(ROOT, "reports", "10_3pct_event")
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "3pct_event_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("saved:", out, len(HTML), "bytes")
