# -*- coding: utf-8 -*-
"""资管公司（APO/BX/KKR/BLK/TROW）× 10Y-2Y 利差走阔 研报生成器
复刻 08_银行陡峭化 报告的样式与结构，标的换成资管，与银行结果并列对照。"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "30_资管陡峭化")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "steep_am.json"), encoding="utf-8") as f:
    R = json.load(f)

def js(o):
    return json.dumps(o, ensure_ascii=False)

# ---------- 数据准备 ----------
slope_dates = R["slope_monthly_series"]["dates"]
slope_vals = R["slope_monthly_series"]["slope"]
am3_series = R["slope_monthly_series"]["am3_ret"]
trad2_series = R["slope_monthly_series"]["trad2_ret"]

CASES_ORDER = ["c2013", "c2016", "c2020", "c2021", "c2024"]
case_label = {c["id"]: c["label"] for c in R["cases"]}
case_start = {c["id"]: c["start"] for c in R["cases"]}
case_end = {c["id"]: c["end"] for c in R["cases"]}
mark_areas = [[{
    "name": case_label[cid][:22],
    "xAxis": case_start[cid][:7],
    "itemStyle": {"color": "rgba(30,102,214,0.10)"},
}, {
    "xAxis": case_end[cid][:7],
}] for cid in CASES_ORDER]

cur_slope = slope_vals[-1]
cur_date = slope_dates[-1]

BUCKET_KEYS = ["S5_走阔>+30bp", "S4_走阔+10~30bp", "S3_走阔0~+10bp", "S2_收窄-10~0bp", "S1_收窄<-10bp"]
bucket_data = {k: {} for k in BUCKET_KEYS}
for sym in ["apo", "bx", "kkr", "blk", "trow", "am3", "trad2", "bank3", "spy"]:
    for k in BUCKET_KEYS:
        bucket_data[k][sym] = R["buckets"][sym][k]

TYPE_KEYS = ["加息陡(2Y升10Y升)", "熊陡(2Y降10Y升)", "牛陡(2Y降10Y降)"]
sm_types = R["single_month"]["type"]
type_stats = {t: sm_types[t] for t in TYPE_KEYS}

reg = R["regression"]
welch = R["welch"]
base = R["base_all_month"]

cc = R["cond_counts"]
n_months = R["n_months"]
sm = R["single_month"]

fwd = R["forward"]
fwd_rows = fwd["rows"]

common = R["common"]
bear_lead = R["bear_lead"]
ep_common_sig = R["ep_common_sig"]

case_summary = R["case_summary"]
cases = R["cases"]

# ---------- HTML 表格工具 ----------
def cell(v, fmt="{:+.2f}%", na="<td class=na>-</td>"):
    if v is None:
        return na
    cls = "up" if v > 0 else "dn" if v < 0 else ""
    return f"<td class='{cls}'>{fmt.format(v)}</td>"

def cellpct(v, na="<td class=na>-</td>"):
    if v is None:
        return na
    return f"<td>{v}%</td>"

# T1 单月五档（含三类组合 + APO/BX/KKR）
t1_rows = []
for k in BUCKET_KEYS:
    b = bucket_data[k]
    am = b["am3"]
    row = [f"<tr><td><b>{k}</b></td><td>{am['n'] if am else '-'} 个月</td>"]
    for sym in ["apo", "bx", "kkr", "am3", "blk", "trow", "trad2", "bank3", "spy"]:
        d = b.get(sym)
        if d and d.get("median") is not None:
            row.append(cell(d["median"]))
        else:
            row.append("<td class=na>-</td>")
    row.append(cellpct(am["win_rate"]) if am else "<td class=na>-</td>")
    t1_rows.append("".join(row) + "</tr>")

# T2 形态分解（走阔月内）
t2_rows = []
for t in TYPE_KEYS:
    st = type_stats[t]
    am = st.get("am3")
    if not am or not am.get("n"):
        t2_rows.append(f"<tr><td>{t}</td><td class=na>-</td></tr>")
        continue
    row = [f"<tr><td>{t}</td><td>{am['n']} 个月</td>"]
    for sym in ["apo", "bx", "kkr", "am3", "blk", "trow", "trad2", "bank3", "spy"]:
        d = st.get(sym)
        row.append(cell(d["median"]) if d and d.get("median") is not None else "<td class=na>-</td>")
    row.append(cellpct(am["win_rate"]))
    row.append(cell(am.get("xs_median"), "{:+.2f}pp"))
    t2_rows.append("".join(row) + "</tr>")

# T3 回归
t3_rows = ""
for sym, nm in [("apo", "APO"), ("bx", "BX"), ("kkr", "KKR"), ("am3", "另类资管3(APO/BX/KKR)"),
                ("blk", "BLK"), ("trow", "TROW"), ("trad2", "传统资管2(BLK/TROW)"),
                ("bank3", "银行3等权"), ("spy", "S&P500")]:
    r = reg.get(sym)
    if not r:
        continue
    sig = "**" if r["p"] is not None and r["p"] < 0.05 else ("*" if r["p"] is not None and r["p"] < 0.10 else "")
    t3_rows += (f"<tr><td>{nm}</td><td>{r['n']}</td>"
                f"<td class='{'up' if r['beta_per_10bp'] > 0 else 'dn'}'>{r['beta_per_10bp']:+.3f}%{sig}</td>"
                f"<td>{r['r2']:.3f}</td><td>{r['t']:+.2f}</td>"
                f"<td>{r['p']:.3f}</td></tr>")

# T4 显著走阔期明细（2011-11 后，全部）
t4_rows = []
for i, e in enumerate(ep_common_sig):
    y2_cls = "dn" if e["y2_chg"] < 0 else "up"
    y10_cls = "up" if e["y10_chg"] > 0 else "dn"
    t4_rows.append(
        f"<tr><td>{e['start'][:7]} ~ {e['end'][:7]}</td><td>{e['months']}M</td>"
        f"<td class='{y2_cls}'>{e['y2_chg']:+.0f}bp</td><td class='{y10_cls}'>{e['y10_chg']:+.0f}bp</td>"
        f"<td class='up'>{e['slope_chg']:+.0f}bp</td><td style='color:var(--sub)'>{e['type']}</td>"
        + cell(e.get("ret_am3")) + cell(e.get("ret_apo")) + cell(e.get("ret_bx")) + cell(e.get("ret_kkr"))
        + cell(e.get("ret_trad2")) + cell(e.get("ret_bank3")) + cell(e.get("ret_spy"))
        + cell(e.get("xs_am3"), "{:+.1f}pp") + "</tr>")

# T5 案例
t5_rows = []
for c in case_summary:
    t5_rows.append(
        f"<tr><td>{c['label']}</td><td class='{'up' if c['slope_chg'] > 0 else 'dn'}'>{c['slope_chg']:+.0f}bp</td>"
        + cell(c.get("am3")) + cell(c.get("apo")) + cell(c.get("bx")) + cell(c.get("kkr"))
        + cell(c.get("trad2")) + cell(c.get("blk")) + cell(c.get("trow"))
        + cell(c.get("jpm")) + cell(c.get("spy")) + "</tr>")

# T6 持有
t6_rows = ""
for tag, nm in [("m3", "后 3 个月"), ("m6", "后 6 个月"), ("m12", "后 12 个月")]:
    s = fwd[tag]
    am = s.get("am3") if s else None
    if not am or not am.get("n"):
        t6_rows += f"<tr><td>{nm}</td><td class=na colspan=9>-</td></tr>"
        continue
    t6_rows += (f"<tr><td>{nm}</td><td>{am['n']} 段</td>"
                + cell(am["median"]) + cellpct(am["win_rate"])
                + cell(s["apo"]["median"]) + cell(s["bx"]["median"]) + cell(s["kkr"]["median"])
                + cell(s["trad2"]["median"]) + cell(s["bank3"]["median"])
                + cell(s["spy"]["median"]) + "</tr>")

# T7 严格熊陡月份明细（2011.11 后资管可得）
t7_rows = []
for r in bear_lead["bear_month_rows"]:
    if r["am3"] is None:
        continue
    t7_rows.append(
        f"<tr><td>{r['month']}</td><td class='dn'>{r['y2_chg']:+.0f}bp</td><td class='up'>{r['y10_chg']:+.0f}bp</td>"
        f"<td class='up'>{r['slope_chg']:+.0f}bp</td>"
        + cell(r["am3"]) + cell(r["trad2"]) + cell(r["spy"])
        + cell(round(r["am3"] - r["spy"], 1), "{:+.2f}pp") + "</tr>")

# T8 同窗口对照表（2011-11 起）
t8_rows = ""
for k, name in [("up", "走阔（全）"), ("up_sig", "走阔 ≥10bp"), ("up_strong", "走阔 ≥20bp"),
                ("down", "收窄（全）"), ("down_sig", "收窄 ≤-10bp"),
                ("bear", "严格熊陡（2Y↓10Y↑）"), ("lead", "长端领涨（10Y≥2Y 且 ↑）")]:
    s = common[k]
    am = s.get("am3")
    if not am or not am.get("n"):
        t8_rows += f"<tr><td>{name}</td><td class=na colspan=9>-</td></tr>"
        continue
    xs = am.get("xs_median")
    b = common["base"]["am3"]
    t8_rows += (
        f"<tr><td>{name}</td><td>{am['n']} 个月</td>"
        + cell(am["median"]) + cellpct(am["win_rate"]) + cell(xs, "{:+.2f}pp")
        + cell(s["trad2"]["median"]) + cell(s["bank3"]["median"])
        + cell(s["spy"]["median"]) + f"<td style='color:var(--sub)'>{b['median']}%</td></tr>")

# ---------- KPI ----------
up_sig_common = common["up_sig"]["am3"]
bear_common = common["bear"]["am3"]
bear_xs = bear_common.get("xs_median")
n_bear = bear_common["n"]
up_strong_common = common["up_strong"]["am3"]
up_strong_xs = up_strong_common.get("xs_median")
down_sig_common = common["down_sig"]["am3"]
down_sig_xs = down_sig_common.get("xs_median")
fwd_m3_am = fwd["m3"]["am3"] if fwd["m3"] else None
fwd_m3_xs = fwd_m3_am.get("xs_median") if fwd_m3_am else None
reg_am = reg["am3"]
reg_trad = reg["trad2"]
welch_am = welch["am3"]

# ---------- 当前形态（2026-08 从 JSON 直接读 slope） ----------
cur_slope_bp = round(cur_slope * 100)

# 模式占位符格式化函数
def fmt(v, plus=True, nd=2):
    if v is None:
        return "-"
    return f"{v:+.2f}" if plus else f"{v:.2f}"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>资管公司 × 曲线陡峭化：US10Y-US2Y 利差扩大时，APO/BX/KKR 怎么走？</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;--teal:#0b7285;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1280px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:20px;font-weight:700;}
  .kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .verdict{background:linear-gradient(135deg,#eef4ff,#f6f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:14.5px;font-weight:600;line-height:1.75;}
  .verdict .b .hl{color:var(--blue);} .verdict .b .hl2{color:var(--red);} .verdict .b .hl3{color:var(--purple);}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .chart.sm{height:330px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;margin-top:10px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
  <h1>资管公司 × 曲线陡峭化：US10Y-US2Y 利差扩大时，APO / BX / KKR 怎么走？</h1>
  <div class="meta">数据窗口：1976-07 ~ 2026-07（月频 @@N_MONTHS@@ 个月；股票受上市限制：APO 2011-03、BX 2007-06、KKR 2010-07、BLK 1999-10、TROW 1986-03）｜主口径：10Y-2Y 利差（slope）月度变化｜标的：APO/BX/KKR（另类资管，点名）+ BLK/TROW（传统资管）+ JPM/BAC/MS（银行对照）；am3=APO/BX/KKR 等权、trad2=BLK/TROW 等权、bank3=JPM/BAC/MS 等权｜数据源：FRED（DGS2/DGS10）+ Yahoo Finance 日线（adj_close）｜为规避上市窗口差异，关键结论一律附 2011-11 起同窗口对照</div>
  <div class="kpis">
    <div class="kpi"><div class="num up">@@BEAR_MED@@%</div><div class="lab">严格熊陡月（2Y↓10Y↑，2011 后 n=@@BEAR_N@@）am3 单月中位 · 超额 @@BEAR_XS@@pp · 胜率 @@BEAR_WR@@%</div></div>
    <div class="kpi"><div class="num dn">@@UPSTRONG_MED@@%</div><div class="lab">强走阔月（Δslope≥20bp，2011 后 n=@@UPSTRONG_N@@）am3 中位 · 超额 @@UPSTRONG_XS@@pp —— 转负</div></div>
    <div class="kpi"><div class="num up">@@DOWNSIG_MED@@%</div><div class="lab">显著收窄月（Δslope≤-10bp，2011 后 n=@@DOWNSIG_N@@）am3 中位 · 超额 @@DOWNSIG_XS@@pp —— 反而更强</div></div>
    <div class="kpi"><div class="num up">@@FWD_M3@@%</div><div class="lab">显著走阔期结束后 3 个月 am3 中位（胜率 @@FWD_M3_WR@@%）</div></div>
    <div class="kpi"><div class="num">@@SLOPE_BP@@bp</div><div class="lab">当前 10Y-2Y（@@CUR_DATE@@）｜近 1 月 2Y 持平 / 10Y +11bp = 长端领涨</div></div>
  </div>
  <div class="verdict">
    <div class="t">核心结论</div>
    <div class="b">「US10Y-US2Y 利差扩大」对资管公司<span class="hl3">不是普适看涨信号，且与银行股的结论方向相反</span>——关键同样在「怎么扩大」：<br>
    <span class="hl3">温和/长端领涨型走阔（加息陡、Taper/Trump/Reflation 类）</span>：另类资管 APO/BX/KKR 中位跑赢 SPY（2011 后走阔月超额约 +0.8~+1.1pp，长端领涨 56 个月超额 +1.09pp），但强度和胜率都低于银行（bank3 同口径超额 +0.8~+2.7pp、强走阔月 +3.5% vs am3 +1.2%）。<br>
    <span class="hl2">大幅走阔（月 &gt;30bp，n=13）</span>：am3 单月中位 <b>-6.8%</b>、胜率仅 31%——<b>与银行相反</b>。因为大幅走阔高度集中于 2008-09 信用危机与 2023-03 SVB 类时刻，曲线陡峭化本身就是「风险溢价 + 信用恐慌」的产物，而资管公司是<u>信用周期敏感型资产</u>（私募信贷按市值波动 + 融资成本 + 风险偏好），被直接冲击；银行反而因「息差预期 + 危机中受益于存款成本下降」抗跌。<br>
    <span class="hl2">严格熊陡（2Y↓10Y↑，2011 后 n=@@BEAR_N@@）</span>：am3 单月中位 <b>+@@BEAR_MED@@%</b>、胜率 @@BEAR_WR@@%、超额 +@@BEAR_XS@@pp（二项 p≈0.03）——历史上 2013 Taper、2016 Trump、2019-10/12 均大涨。注意熊陡的斜率扩大并不意味着「利差扩大必涨」：它只在该形态由「宽松预期 + 增长交易」驱动时成立，危机型熊陡（2008）同样崩盘。<br>
    当前（2026-08）：slope @@SLOPE_BP@@bp，近 1 月 2Y 持平、10Y +11bp = <b>长端领涨型</b>——历史上偏向温和利好资管相对表现，但强度弱于银行；若后续走阔加速至月 &gt;+30bp（往往伴随信用事件），资管反而先承压。</div>
  </div>
</div>

<div class="card">
  <h2>一、50 年利差全景：走阔常见，资管 vs 银行在弱走阔段几乎同涨</h2>
  <div class="chart" id="c1"></div>
  <div class="note">蓝线 = 10Y-2Y 利差（%），柱状 = am3 月度收益（%）。浅蓝阴影 = 5 个代表性走阔时期。走阔月占全部月份 @@UP_PCT@@%（<b>走阔并不稀有</b>），大幅走阔（&gt;30bp/月）仅 35 个月——其中 2008 年占了 6 个，是资管最差的历史窗口。</div>
</div>

<div class="card">
  <h2>二、单月口径：Δslope 分五档 — 只有大幅走阔把资管打趴</h2>
  <div class="scroll"><table>
    <tr><th>月度档位（互斥）</th><th>样本</th><th>APO</th><th>BX</th><th>KKR</th><th>am3 中位</th><th>BLK</th><th>TROW</th><th>trad2</th><th>bank3</th><th>S&amp;P500</th><th>am3 胜率</th></tr>
    @@T1_ROWS@@
  </table></div>
  <div class="note">五档按 Δslope 月度幅度（单月，全期；am3 样本自 2011 起）。红涨绿跌。规律：<b>S3-S4（0~+30bp 走阔）与 S2（小幅收窄）对资管无显著区分</b>——中位 1.7%~2.8%、胜率 58%-61%，全部高于全月基准；<b>S5 大幅走阔（&gt;+30bp）am3 中位 -6.8%、胜率 31%</b>，是唯一「利差扩大反而重挫」的档位。对照 bank3：S4 走阔 +2.0%、S5 也从 -3.9% 缓和——<b>银行在大幅走阔时比资管抗跌得多</b>。</div>
  <div class="chart sm" id="c2"></div>
  <div class="note">柱 = 各档 am3（深蓝）与 S&amp;P500（浅蓝）单月收益中位 %。可见大幅走阔档（S5）资管与大盘同跌、且跌得更深。</div>
</div>

<div class="card">
  <h2>三、怎么走阔（形态分解）：熊陡最强、加息陡次之、牛陡平庸</h2>
  <div class="scroll"><table>
    <tr><th>走阔形态</th><th>样本</th><th>APO</th><th>BX</th><th>KKR</th><th>am3 中位</th><th>BLK</th><th>TROW</th><th>trad2</th><th>bank3</th><th>S&amp;P500</th><th>am3 胜率</th><th>am3 超额</th></tr>
    @@T2_ROWS@@
  </table></div>
  <div class="chart sm" id="c3"></div>
  <div class="note">三形态只统计「slope 走阔」月份。全期样本（走阔月内）：<b>熊陡 n=19（am3 中位 +4.87%、超额 +3.58pp）&gt; 加息陡 n=56（+1.33%、超额 +0.43pp）&gt; 牛陡 n=29（+2.39%、超额 -1.27pp）</b>。与银行对比：bank3 在加息陡最强（+2.37%、超额 +2.11pp）、牛陡跑输——<b>银行最怕牛陡、资管最怕大幅走阔</b>，两者对「走阔成因」的敏感方向错位。</div>
</div>

<div class="card">
  <h2>四、敏感度回归：Δslope 几乎不解释资管月收益</h2>
  <div class="grid2">
    <div class="chart sm" id="c4"></div>
    <div class="scroll" style="align-self:center;"><table>
      <tr><th>标的</th><th>n</th><th>β（%/10bp）</th><th>R²</th><th>t</th><th>p</th></tr>
      @@T3_ROWS@@
    </table>
    <div class="note" style="margin-top:8px;">β = 月频 Δslope（bp）对月收益 % 的回归斜率。* p&lt;0.10，** p&lt;0.05。<b>所有标的 R² 均 &lt;1%、几乎全部 p&gt;0.1</b>（仅 TROW p=0.05 边缘）且 β 方向不统一——利差变化在月度尺度上对资管股无稳定解释力。结合 S5 档可知：<b>利差对资管的作用是「阈值式 + 危机式」的（大幅走阔时重挫），不是线性连续的</b>。</div>
    </div>
  </div>
</div>

<div class="card">
  <h2>五、2011-11 起同窗口对照：排除上市窗口差异后的稳健结论</h2>
  <div class="scroll"><table>
    <tr><th>条件（2011-11 起）</th><th>样本</th><th>am3 中位</th><th>am3 胜率</th><th>am3 超额</th><th>trad2 中位</th><th>bank3 中位</th><th>S&amp;P500 中位</th><th>全月基准 am3</th></tr>
    @@T8_ROWS@@
  </table></div>
  <div class="note">同窗口内所有标的均有数据（APO 2011-03 上市，取 2011-11 起共 @@N_MONTHS_COMMON@@ 个月）。关键：<b>① 严格熊陡 am3 +5.71%/81.8%（超额 +3.78pp，二项 p≈0.03）是最强且唯一接近显著的条件</b>；② 走阔≥10bp 超额 +0.82pp、≥20bp 转负（-0.97pp）；③ <b>显著收窄（≤-10bp）am3 超额 +2.53pp 反而高于显著走阔</b>——资管与「利差走阔」没有单调正相关；④ bank3 在长端领涨型走阔下超额明显高于 am3（+2.7pp vs +1.09pp）。</div>
</div>

<div class="card">
  <h2>六、显著走阔期（Δslope≥10bp/月）明细：2011-11 后 24 段</h2>
  <div class="scroll" style="max-height:520px;overflow-y:auto;"><table>
    <tr><th>时期</th><th>长度</th><th>2Y</th><th>10Y</th><th>slope</th><th>形态</th><th>am3</th><th>APO</th><th>BX</th><th>KKR</th><th>trad2</th><th>bank3</th><th>S&amp;P500</th><th>am3 超额</th></tr>
    @@T4_ROWS@@
  </table></div>
  <div class="note">2011-11 后全部 24 段显著走阔期。可见：<b>2020-03（危机牛陡）am3 -21.1% 是最深单段</b>；2012-12~2013-01、2020-12~2021-03、2024-07~09、2026-07 四段 am3 +18.6%~+29.7% 大幅跑赢；而 2022-04~05、2022-12、2023-07~10（熊市走阔）am3 为负——<b>走阔期资管表现由「风险偏好」主导，与走阔形态/幅度的对应关系很弱</b>。</div>
</div>

<div class="card">
  <h2>七、严格熊陡月份明细（2011-11 后，am3 可得 20 个月）</h2>
  <div class="scroll" style="max-height:440px;overflow-y:auto;"><table>
    <tr><th>月份</th><th>2Y 变化</th><th>10Y 变化</th><th>slope</th><th>am3</th><th>trad2</th><th>S&amp;P500</th><th>am3 超额</th></tr>
    @@T7_ROWS@@
  </table></div>
  <div class="note">严格熊陡 = 2Y 降 + 10Y 升。2012 后 am3 可得 20 个月（2011 起统计 11 个月，此处展示 am3 可得全样本）。<b>2013-07（Taper）、2016-03、2019-10/12、2020-05/12 六个月内 am3 全部 +5% 以上</b>；唯二重挫是 2008-10（-39.2%）与 2007-06（-16.5%）——危机型熊陡。规律：<b>熊陡本身中性，真正决定资管命运的是「走阔发生在牛市还是危机」</b>。</div>
</div>

<div class="card">
  <h2>八、七个标志性时期：与银行、大盘并列</h2>
  <div class="scroll"><table>
    <tr><th>时期</th><th>slope</th><th>am3</th><th>APO</th><th>BX</th><th>KKR</th><th>trad2</th><th>BLK</th><th>TROW</th><th>JPM</th><th>S&amp;P500</th></tr>
    @@T5_ROWS@@
  </table></div>
  <div class="note">区间收益（复权）。<b>2024-09~12（降息+长端反弹）am3 +33.2%（APO +48.8%）&gt; 2016-11~2017-03 Trump 再通胀 am3 +31.9%（APO +40.5%）&gt; 2021-01~03 Reflation am3 +14.4%（BX +19.9%、KKR +23.6%）&gt; 2013 Taper am3 +14.5%（BX +23.5%）</b>——四段长端领涨走阔资管全线大涨，弹性从高到低 APO &gt; KKR ~ BX &gt; BLK/TROW。对照：危机牛陡（2020-02~05）am3 -3.2%（优于 JPM -26%）；2003 复苏双升期无资管样本（仅 trad2 +35.6%）。</div>
  <div class="grid2">
    <div class="chart sm" id="c5a"></div>
    <div class="chart sm" id="c5b"></div>
    <div class="chart sm" id="c5c"></div>
    <div class="chart sm" id="c5d"></div>
  </div>
  <div class="note">日频图：绿/红线 = 2Y/10Y 收益率（左轴），其余线 = 自段首归一化收益 %（右轴）。左上 2016 Trump 再通胀：10Y 上行、slope 走阔，APO 领涨 +40%；右上 2021 Reflation：10Y 从 0.9% 冲到 1.7%，BX/KKR 涨 20%+；左下 2020 危机牛陡：2Y 崩至 0.25%，am3 相对抗跌（-3% vs JPM -26%）；右下 2024 降息+长端反弹：APO +48.8% 弹性最大。</div>
</div>

<div class="card">
  <h2>九、显著走阔之后：买资管能拿多久？</h2>
  <div class="scroll"><table>
    <tr><th>持有期</th><th>样本</th><th>am3 中位</th><th>am3 胜率</th><th>APO</th><th>BX</th><th>KKR</th><th>trad2</th><th>bank3</th><th>S&amp;P500</th></tr>
    @@T6_ROWS@@
  </table></div>
  <div class="note">以每个「显著走阔期（≥10bp/月）」结束日为锚，其后 3/6/12 个月收益（am3 为三股均值）。样本为全部显著走阔期（@@FWD_N@@ 段，多数在 2011 后）。<b>后 3 个月 am3 中位 +8.6%（胜率 63%）&gt;&gt; SPY +4.4%、bank3 +3.9%</b>——资管在走阔结束后的短期弹性强于大盘与银行；但 12 个月维度 SPY +15.0% &gt; am3 +6.8%，<b>资管的超额偏短周期，长期仍是 beta 属性</b>。</div>
</div>

<div class="card">
  <h2>结论与机制</h2>
  <h3>回答：US10Y-US2Y 利差扩大的情况下，APO/BX/KKR 表现如何？</h3>
  <p><b>1. 方向本身：弱信号，且非线性。</b>全部 601 个月中，走阔 268 个月。2011-11 起同窗口：走阔月 am3 中位 +2.46%（胜率 59.5%、超额 +1.09pp），仅略高于全月基准 +2.06%；回归 R²&lt;1%、p&gt;0.1。<b>「利差扩大资管看涨」不成立</b>——它是利率水平、风险偏好、信用周期的复合结果，单看 slope 方向没有稳定交易含义。</p>
  <p><b>2. 阈值效应：大幅走阔（月 &gt;+30bp）资管重挫、银行抗跌。</b>S5 档 am3 中位 -6.8%、胜率 31%，bank3 仅 -3.9%。原因：月 &gt;30bp 的走阔几乎都发生在信用/流动性恐慌（1979-82 沃尔克、2008-09 次贷、2023-03 SVB、2023-09 长端抛售），此时利差走阔 = <b>风险溢价陡升</b>；另类资管（私募信贷市值、杠杆融资、风险偏好）直接受损，而银行靠负债端成本下降与息差预期相对受益。机制上「走阔幅度」代理了「危机烈度」。</p>
  <p><b>3. 形态效应：熊陡（2Y↓10Y↑）时资管最强，但分两种熊陡。</b>2011 后严格熊陡 11 个月：am3 +5.71%/81.8%（二项 p≈0.03），2013 Taper、2016 Trump、2019-10/12、2020-05/12 齐涨；但 2008-10 同形态 am3 -39%——<b>「宽松 + 增长」型熊陡（牛市加速）与「危机」型熊陡（恐慌）天壤之别</b>。对照：bank3 在加息陡（2Y↑10Y↑）超额最大（+2.11pp），资管则熊陡更强——<b>两者对走阔成因的敏感度错位：银行吃息差，资管吃风险偏好与融资环境</b>。</p>
  <p><b>4. 当前读数（2026-08）。</b>slope @@SLOPE_BP@@bp（50 年中位附近），近 1 月 2Y 持平、10Y +11bp = <b>长端领涨型</b>，历史对应温和利好的资管相对表现（超额 +1pp 量级、非强信号）；若后续走阔陡峭化（&gt;+30bp/月）尤其伴随信用事件，资管而非银行更可能先承压。2026 年与 2024-09~12 的映射（降息+长端反弹）偏正面（当时 am3 +33%）。</p>
  <div class="warn">局限性：① 资管股上市晚（APO 2011、BX 2007、KKR 2010），全期表格早期为 None，核心结论已用 2011-11 同窗口重算；② 大幅走阔档 n=13、熊陡 n=11，样本小、二项检验仅 p≈0.03（单尾、未多重比较校正，视作上限）；③ 形态划分依赖月末值、边界有噪音；④ 牛市 vs 危机的「双重熊陡」说明同一形态内部方差大——形态标签不足以完全区分，须结合宏观环境；⑤ 未计交易成本与股息。</div>
</div>

</div>
<script>
const slopeDates = @@SLOPE_DATES@@;
const slopeVals = @@SLOPE_VALS@@;
const am3Series = @@AM3_SERIES@@;
const markAreas = @@MARK_AREAS@@;
const curDate = "@@CUR_DATE@@";
const curSlope = @@CUR_SLOPE@@;
const bucketKeys = @@BUCKET_KEYS@@;
const bucketAM = @@BUCKET_AM@@;
const bucketSPY = @@BUCKET_SPY@@;
const typeKeys = @@TYPE_KEYS@@;
const typeAM = @@TYPE_AM@@;
const typeSPY = @@TYPE_SPY@@;
const typeN = @@TYPE_N@@;
const scatter = @@SCATTER@@;
const regLine = @@REG_LINE@@;
const cases = @@CASES@@;

function mk(id){ return echarts.init(document.getElementById(id)); }
const RED="#e03131", GREEN="#0aa06e", BLUE="#1e66d6", AMBER="#b45309", PURPLE="#7048e8", GRAY="#9aa4b2", ORANGE="#d97706", TEAL="#0b7285";

// 图1 利差全景 + am3 月度收益
const c1 = mk('c1');
c1.setOption({
  tooltip:{trigger:'axis'},
  legend:{top:0,data:['10Y-2Y 利差','am3 月度收益']},
  grid:{left:55,right:55,top:35,bottom:45},
  xAxis:{type:'category',data:slopeDates,axisLabel:{show:false},axisTick:{show:false}},
  yAxis:[{type:'value',name:'10Y-2Y (%)'},{type:'value',name:'am3 月%',splitLine:{show:false}}],
  dataZoom:[{type:'slider',height:18,bottom:6}],
  series:[
    {name:'10Y-2Y 利差',type:'line',data:slopeVals,symbol:'none',
      lineStyle:{color:BLUE,width:1.2},
      markArea:{silent:true,data:markAreas},
      markPoint:{data:[{xAxis:curDate,yAxis:curSlope,name:'当前',itemStyle:{color:RED},symbol:'diamond',symbolSize:12,
        label:{show:true,fontSize:9,formatter:'当前 '+curSlope.toFixed(2)}}]}},
    {name:'am3 月度收益',type:'bar',yAxisIndex:1,data:am3Series,
      itemStyle:{color:(p)=>{const v=p.value;return v>=0?'rgba(224,49,49,.45)':'rgba(10,160,110,.45)';}}}
  ]
});

// 图2 五档
const c2 = mk('c2');
c2.setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{top:0,data:['am3 中位','S&P500 中位']},
  grid:{left:50,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:bucketKeys,axisLabel:{fontSize:10}},
  yAxis:{type:'value',name:'单月收益中位 %'},
  series:[
    {name:'am3 中位',type:'bar',data:bucketAM,itemStyle:{color:BLUE,borderRadius:[3,3,0,0]},barGap:'15%'},
    {name:'S&P500 中位',type:'bar',data:bucketSPY,itemStyle:{color:'#bcd3f5',borderRadius:[3,3,0,0]}}
  ]
});

// 图3 形态分解
const c3 = mk('c3');
c3.setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
    formatter:p=>{const i=p[0].dataIndex;return typeKeys[i]+'（'+typeN[i]+' 个月）<br>'+p.map(x=>x.marker+x.seriesName+': '+x.value+'%').join('<br>');}},
  legend:{top:0,data:['am3 中位','S&P500 中位']},
  grid:{left:50,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:typeKeys,axisLabel:{fontSize:10}},
  yAxis:{type:'value',name:'单月收益中位 %'},
  series:[
    {name:'am3 中位',type:'bar',data:typeAM,itemStyle:{color:PURPLE,borderRadius:[3,3,0,0]},barGap:'15%'},
    {name:'S&P500 中位',type:'bar',data:typeSPY,itemStyle:{color:'#e3d5f0',borderRadius:[3,3,0,0]}}
  ]
});

// 图4 散点回归
const c4 = mk('c4');
c4.setOption({
  title:{text:'Δslope(bp) → am3 月收益（散点+回归线）',fontSize:13,left:0},
  tooltip:{trigger:'item',formatter:p=>'Δslope '+p.value[0]+'bp<br>am3 '+p.value[1]+'%'},
  grid:{left:50,right:20,top:45,bottom:40},
  xAxis:{type:'value',name:'Δslope (bp/月)'},
  yAxis:{type:'value',name:'am3 月收益 %'},
  series:[
    {name:'散点',type:'scatter',data:scatter,symbolSize:4,itemStyle:{color:'rgba(30,102,214,.35)'}},
    {name:'回归线',type:'line',data:regLine,symbol:'none',lineStyle:{color:ORANGE,width:2},markLine:{silent:true,symbol:'none',
      lineStyle:{color:GRAY,type:'dashed'},data:[{yAxis:0}]}}
  ]
});

// 案例日频
function caseChart(id, cid){
  const c = cases.find(x=>x.id===cid);
  const ch = mk(id);
  ch.setOption({
    title:{text:c.label,fontSize:12,left:0},
    tooltip:{trigger:'axis'},
    legend:{top:20},
    grid:{left:45,right:50,top:52,bottom:25},
    xAxis:{type:'category',data:c.dates,axisLabel:{show:false}},
    yAxis:[{type:'value',name:'收益率 %',scale:true},{type:'value',name:'收益 %',scale:true,splitLine:{show:false}}],
    series:[
      {name:'2Y',type:'line',data:c.y2,symbol:'none',lineStyle:{color:GREEN,width:1.1},yAxisIndex:0},
      {name:'10Y',type:'line',data:c.y10,symbol:'none',lineStyle:{color:RED,width:1.1},yAxisIndex:0},
      {name:'APO',type:'line',data:c.rets.apo,symbol:'none',lineStyle:{color:BLUE,width:1.4},yAxisIndex:1},
      {name:'BX',type:'line',data:c.rets.bx,symbol:'none',lineStyle:{color:AMBER,width:1.4},yAxisIndex:1},
      {name:'KKR',type:'line',data:c.rets.kkr,symbol:'none',lineStyle:{color:PURPLE,width:1.4},yAxisIndex:1},
      {name:'trad2',type:'line',data:c.rets.blk!=null&&c.rets.blk.length?c.rets.trow??c.rets.blk:null,symbol:'none',lineStyle:{color:TEAL,width:1.1},yAxisIndex:1},
      {name:'S&P500',type:'line',data:c.rets.spy,symbol:'none',lineStyle:{color:GRAY,width:1.1,type:'dashed'},yAxisIndex:1}
    ]
  });
  return ch;
}
const charts = [c1,c2,c3,c4,
  caseChart('c5a','c2016'),caseChart('c5b','c2021'),caseChart('c5c','c2020'),caseChart('c5d','c2024')];
window.addEventListener('resize',()=>charts.forEach(ch=>ch.resize()));
</script>
</body>
</html>"""

# ---------- 替换 ----------
scatter = [[d, r] for d, r in zip(R["slope_monthly_series"]["dslope"], am3_series)
           if r is not None and abs(d) <= 150]
rab = reg["am3"]
regLine = [[-80, round(rab["alpha"] + rab["beta_per_bp"] * -80, 2)],
           [80, round(rab["alpha"] + rab["beta_per_bp"] * 80, 2)]]

t1_rows_html = "\n    ".join(t1_rows)
t2_rows_html = "\n    ".join(t2_rows)
t4_rows_html = "\n    ".join(t4_rows)
t5_rows_html = "\n    ".join(t5_rows)
t7_rows_html = "\n    ".join(t7_rows)

bucketAM = [bucket_data[k]["am3"]["median"] if bucket_data[k]["am3"] and bucket_data[k]["am3"].get("median") is not None else None for k in BUCKET_KEYS]
bucketSPY = [bucket_data[k]["spy"]["median"] if bucket_data[k]["spy"] and bucket_data[k]["spy"].get("median") is not None else None for k in BUCKET_KEYS]
typeAM = [type_stats[t]["am3"]["median"] if type_stats[t].get("am3") and type_stats[t]["am3"].get("median") is not None else None for t in TYPE_KEYS]
typeSPY = [type_stats[t]["spy"]["median"] if type_stats[t].get("spy") and type_stats[t]["spy"].get("median") is not None else None for t in TYPE_KEYS]
typeN = [type_stats[t]["am3"]["n"] if type_stats[t].get("am3") else 0 for t in TYPE_KEYS]

n_months_common = R["n_months_common"]
fwd_n = len(fwd_rows)

html = (TEMPLATE
        .replace("@@N_MONTHS@@", str(n_months))
        .replace("@@N_MONTHS_COMMON@@", str(n_months_common))
        .replace("@@BEAR_MED@@", fmt(bear_common["median"]))
        .replace("@@BEAR_N@@", str(n_bear))
        .replace("@@BEAR_XS@@", fmt(bear_xs))
        .replace("@@BEAR_WR@@", str(bear_common["win_rate"]))
        .replace("@@UPSTRONG_MED@@", fmt(up_strong_common["median"]))
        .replace("@@UPSTRONG_N@@", str(up_strong_common["n"]))
        .replace("@@UPSTRONG_XS@@", fmt(up_strong_xs))
        .replace("@@DOWNSIG_MED@@", fmt(down_sig_common["median"]))
        .replace("@@DOWNSIG_N@@", str(down_sig_common["n"]))
        .replace("@@DOWNSIG_XS@@", fmt(down_sig_xs))
        .replace("@@FWD_M3@@", fmt(fwd_m3_am["median"]))
        .replace("@@FWD_M3_WR@@", str(fwd_m3_am["win_rate"]))
        .replace("@@SLOPE_BP@@", str(cur_slope_bp))
        .replace("@@CUR_DATE@@", cur_date)
        .replace("@@UP_PCT@@", f"{round(cc['up_loose'] / n_months * 100, 1)}")
        .replace("@@FWD_N@@", str(fwd_n))
        .replace("@@T1_ROWS@@", t1_rows_html)
        .replace("@@T2_ROWS@@", t2_rows_html)
        .replace("@@T3_ROWS@@", t3_rows)
        .replace("@@T4_ROWS@@", t4_rows_html)
        .replace("@@T5_ROWS@@", t5_rows_html)
        .replace("@@T6_ROWS@@", t6_rows)
        .replace("@@T7_ROWS@@", t7_rows_html)
        .replace("@@T8_ROWS@@", t8_rows)
        .replace("@@SLOPE_DATES@@", js(slope_dates))
        .replace("@@SLOPE_VALS@@", js(slope_vals))
        .replace("@@AM3_SERIES@@", js(am3_series))
        .replace("@@MARK_AREAS@@", js(mark_areas))
        .replace("@@CUR_SLOPE@@", js(cur_slope))
        .replace("@@BUCKET_KEYS@@", js(BUCKET_KEYS))
        .replace("@@BUCKET_AM@@", js(bucketAM))
        .replace("@@BUCKET_SPY@@", js(bucketSPY))
        .replace("@@TYPE_KEYS@@", js(TYPE_KEYS))
        .replace("@@TYPE_AM@@", js(typeAM))
        .replace("@@TYPE_SPY@@", js(typeSPY))
        .replace("@@TYPE_N@@", js(typeN))
        .replace("@@SCATTER@@", js(scatter))
        .replace("@@REG_LINE@@", js(regLine))
        .replace("@@CASES@@", js(cases)))

with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("written:", os.path.join(OUT, "index.html"), len(html))