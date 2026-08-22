# -*- coding: utf-8 -*-
"""银行板块（JPM/MS/BAC）× 10Y-2Y 利差走阔 复盘研报生成器"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "08_银行陡峭化")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "steep_banks.json"), encoding="utf-8") as f:
    R = json.load(f)

def js(o):
    return json.dumps(o, ensure_ascii=False)

# ---------- 数据准备 ----------
slope_dates = R["slope_monthly_series"]["dates"]
slope_vals = R["slope_monthly_series"]["slope"]

# 案例区间（markArea）
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

# 当前点位（2026-07）
cur_slope = slope_vals[-1]
cur_date = slope_dates[-1]

# 五档（互斥，单月口径来自 buckets）
BUCKET_KEYS = ["S5_走阔>+30bp", "S4_走阔+10~30bp", "S3_走阔0~+10bp", "S2_收窄-10~0bp", "S1_收窄<-10bp"]
bucket_data = {k: {} for k in BUCKET_KEYS}
for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
    for k in BUCKET_KEYS:
        d = R["buckets"][sym][k]
        bucket_data[k][sym] = d

# 形态分解（单月口径）
types = R["single_month"]["type"]
TYPE_KEYS = ["加息陡(2Y升10Y升)", "熊陡(2Y降10Y升)", "牛陡(2Y降10Y降)"]
type_stats = {t: types[t] for t in TYPE_KEYS}

# 回归
reg = R["regression"]
welch = R["welch"]
base = R["base_all_month"]

# 时期明细（显著走阔 top20）
up_sig = sorted(R["episodes"]["up_sig"], key=lambda x: abs(x["slope_chg"]), reverse=True)[:20]
up_sig = sorted(up_sig, key=lambda x: x["start"])
pct = R["pctile_up_sig"]

# 持有
fwd = R["forward"]
fwd_rows = fwd["rows"]

# 案例
case_summary = R["case_summary"]
cases = R["cases"]

# ---------- HTML 表格 ----------
def cell(v, fmt="{:+.2f}%", na="<td class=na>-</td>"):
    if v is None:
        return na
    cls = "up" if v > 0 else "dn" if v < 0 else ""
    return f"<td class='{cls}'>{fmt.format(v)}</td>"

def cellpct(v, na="<td class=na>-</td>"):
    if v is None:
        return na
    return f"<td>{v}%</td>"

# T1 单月五档
t1_rows = []
for k in BUCKET_KEYS:
    b = bucket_data[k]
    bk = b["bank3"]
    if bk is None or not bk.get("n"):
        t1_rows.append(f"<tr><td><b>{k}</b></td><td class=na>-</td>"
                       f"<td class=na>-</td><td class=na>-</td><td class=na>-</td><td class=na>-</td>"
                       f"<td class=na>-</td><td class=na>-</td><td class=na>-</td></tr>")
        continue
    xs = bk.get("xs_median")
    t1_rows.append(
        f"<tr><td><b>{k}</b></td><td>{bk['n']} 个月</td>"
        + cell(b["jpm"]["median"]) + cell(b["bac"]["median"]) + cell(b["ms"]["median"])
        + cell(bk["median"]) + cellpct(bk["win_rate"])
        + cell(b["gspc"]["median"]) + cell(xs, "{:+.2f}pp") + "</tr>")
bb = base["bank3"]
base_row = (f"<tr><td><b>全月基准</b></td><td>{bb['n']} 个月</td>"
            + cell(base["jpm"]["median"]) + cell(base["bac"]["median"]) + cell(base["ms"]["median"])
            + cell(bb["median"]) + cellpct(bb["win_rate"])
            + cell(base["gspc"]["median"]) + "<td class=na>-</td></tr>")

# T2 形态分解
t2_rows = []
for t in TYPE_KEYS:
    st = type_stats[t]
    bk = st.get("bank3")
    if bk is None or not bk.get("n"):
        t2_rows.append(f"<tr><td>{t}</td><td class=na>-</td></tr>")
        continue
    xs = bk.get("xs_median")
    t2_rows.append(
        f"<tr><td>{t}</td><td>{bk['n']} 个月</td>"
        + cell(st["jpm"]["median"]) + cell(st["bac"]["median"]) + cell(st["ms"]["median"])
        + cell(bk["median"]) + cellpct(bk["win_rate"])
        + cell(st["gspc"]["median"]) + cell(xs, "{:+.2f}pp") + "</tr>")

# T3 回归
t3_rows = ""
for sym, nm in [("jpm", "JPM"), ("bac", "BAC"), ("ms", "MS"), ("bank3", "银行三股等权"),
                ("kre", "KRE 区域银行"), ("xlf", "XLF 金融"), ("gspc", "S&P500")]:
    r = reg.get(sym)
    if not r:
        continue
    sig = "**" if r["p"] is not None and r["p"] < 0.05 else ("*" if r["p"] is not None and r["p"] < 0.10 else "")
    t3_rows += (f"<tr><td>{nm}</td><td>{r['n']}</td>"
                f"<td class='{'up' if r['beta_per_10bp'] > 0 else 'dn'}'>{r['beta_per_10bp']:+.3f}%{sig}</td>"
                f"<td>{r['r2']:.3f}</td><td>{r['t']:+.2f}</td>"
                f"<td>{r['p']:.3f}</td></tr>")

# T4 显著走阔时期明细
t4_rows = []
for i, e in enumerate(up_sig):
    bk3 = e.get("ret_bank3")
    pv = pct["bank3"][i] if i < len(pct["bank3"]) else None
    xs_td = cell(e.get("xs_bank3"), "{:+.1f}pp")
    pct_td = f"<td>{pv:.0f}%</td>" if pv is not None else "<td class=na>-</td>"
    y2_cls = "dn" if e["y2_chg"] < 0 else "up"
    y10_cls = "up" if e["y10_chg"] > 0 else "dn"
    t4_rows.append(
        f"<tr><td>{e['start'][:7]} ~ {e['end'][:7]}</td><td>{e['months']}M</td>"
        f"<td class='{y2_cls}'>{e['y2_chg']:+.0f}bp</td><td class='{y10_cls}'>{e['y10_chg']:+.0f}bp</td>"
        f"<td class='up'>{e['slope_chg']:+.0f}bp</td><td style='color:var(--sub)'>{e['type']}</td>"
        + cell(bk3) + cell(e.get("ret_jpm")) + cell(e.get("ret_bac")) + cell(e.get("ret_ms"))
        + cell(e.get("ret_gspc")) + xs_td + pct_td + "</tr>")

# T5 案例
t5_rows = []
for c in case_summary:
    k = c["label"].startswith("对照")
    lab = c["label"]
    t5_rows.append(
        f"<tr><td>{lab}</td><td class='{'up' if c['slope_chg'] > 0 else 'dn'}'>{c['slope_chg']:+.0f}bp</td>"
        + cell(c.get("bank3")) + cell(c.get("jpm")) + cell(c.get("bac")) + cell(c.get("ms"))
        + cell(c.get("kre")) + cell(c.get("gspc")) + "</tr>")

# T6 持有
t6_rows = ""
for tag, nm in [("m3", "后 3 个月"), ("m6", "后 6 个月"), ("m12", "后 12 个月")]:
    s = fwd[tag]
    bk = s.get("bank3") if s else None
    if not bk or not bk.get("n"):
        t6_rows += f"<tr><td>{nm}</td><td class=na colspan=7>-</td></tr>"
        continue
    t6_rows += (f"<tr><td>{nm}</td><td>{bk['n']} 段</td>"
                + cell(bk["median"]) + cellpct(bk["win_rate"])
                + cell(s["jpm"]["median"]) + cell(s["bac"]["median"]) + cell(s["ms"]["median"])
                + cell(s["gspc"]["median"]) + "</tr>")

# ---------- KPI ----------
cc = R["cond_counts"]
n_months = R["n_months"]
sm = R["single_month"]
up_med = sm["up_sig"]["bank3"]["median"]
up_wr = sm["up_sig"]["bank3"]["win_rate"]
up_xs = sm["up_sig"]["bank3"].get("xs_median")
bear_m = type_stats["加息陡(2Y升10Y升)"]["bank3"]["median"]
bull_m = type_stats["牛陡(2Y降10Y降)"]["bank3"]["median"]
spy_bear = type_stats["加息陡(2Y升10Y升)"]["gspc"]["median"]
fwd12 = fwd["m12"]["bank3"]["median"]
fwd12_wr = fwd["m12"]["bank3"]["win_rate"]
reg_bank3 = reg["bank3"]
case_2020 = next(c for c in case_summary if "2020" in c["label"])
case_2016 = next(c for c in case_summary if "2016" in c["label"])

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>银行板块 × 曲线陡峭化：10Y-2Y 利差扩大时 JPM/MS/BAC 怎么走？</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1240px;margin:0 auto;}
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
  .verdict{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:15px;font-weight:600;line-height:1.75;}
  .verdict .b .hl{color:var(--blue);}
  .verdict .b .hl2{color:var(--red);}
  .verdict .b .hl3{color:var(--purple);}
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
  <h1>银行板块 × 曲线陡峭化：10Y-2Y 利差扩大时，JPM / MS / BAC 怎么走？</h1>
  <div class="meta">数据窗口：1976-07 ~ 2026-07（月频 601 个月）｜主口径：10Y-2Y 利差（slope）月度变化｜标的：JPM/BAC/MS（点名），对照 GS/KRE/XLF/SPY；bank3 = 三股等权｜数据源：FRED（DGS2/DGS10）+ Yahoo Finance 日线（adj_close，1990 起）</div>
  <div class="kpis">
    <div class="kpi"><div class="num up">@@UP_MED@@%</div><div class="lab">显著走阔月（Δslope≥10bp）bank3 单月收益中位</div></div>
    <div class="kpi"><div class="num">@@UP_WR@@%</div><div class="lab">显著走阔月 bank3 胜率（超额 @@UP_XS@@pp）</div></div>
    <div class="kpi"><div class="num up">@@BEAR_M@@%</div><div class="lab">加息陡月（2Y↑10Y↑）bank3 中位（SPY @@SPY_BEAR@@%）</div></div>
    <div class="kpi"><div class="num dn">@@BULL_M@@%</div><div class="lab">牛陡月（2Y↓10Y↓）bank3 中位——跑输</div></div>
    <div class="kpi"><div class="num up">@@FWD12@@%</div><div class="lab">显著走阔期结束后 12 个月 bank3 中位（胜率 @@FWD12_WR@@%）</div></div>
    <div class="kpi"><div class="num">@@SLOPE@@bp</div><div class="lab">当前 10Y-2Y（@@CUR_DATE@@，@@SLOPE_BP@@bp 为 50 年中位附近）</div></div>
  </div>
  <div class="verdict">
    <div class="t">核心结论</div>
    <div class="b">「10Y-2Y 利差扩大」本身<span class="hl">不足以预测银行股月度表现</span>（月频回归 R²&lt;1%、走阔 vs 收窄月收益差统计不显著）——<b>关键是「怎么扩大」</b>：<br>
    <span class="hl3">加息陡（2Y 升 + 10Y 升得更快，增长/通胀/财政预期驱动）</span>：银行股 <span class="hl">显著跑赢</span>，单月 bank3 中位 @@BEAR_M@@% vs SPY @@SPY_BEAR@@%；历史上 2013 Taper、2016-11 Trump 交易、2021 Reflation、2024-09~12 四段长端领涨走阔，bank3 区间 +15%~+33%，全部大幅跑赢 SPY。<br>
    <span class="hl2">牛陡（2Y 领跌、宽松/衰退预期）</span>：银行股跑输甚至绝对下跌（2020-02~05 危机牛陡 bank3 -22.6% vs SPY -6.3%），息差改善预期被资产质量与信用担忧压制。<br>
    当前（2026-08）：slope 51bp，7 月以来 <b>2Y 持平、10Y +20bp = 长端领涨型</b>，历史形态偏向利好银行相对表现；但 8/18 板块单日 -6% 提示：斜率快速走阔初期常伴随 30Y 新高与估值/信用再定价的剧烈波动。</div>
  </div>
</div>

<div class="card">
  <h2>一、50 年利差全景：走阔常见，但形态不同含义完全不同</h2>
  <div class="chart" id="c1"></div>
  <div class="note">蓝线 = 10Y-2Y 利差（%）。浅蓝阴影 = 5 个代表性走阔时期（2013 Taper / 2016 Trump / 2020 危机 / 2021 Reflation / 2024-09~12）。过去 50 年 slope 月度变化 &gt;0 的月份占 @@UP_PCT@@%（走阔比收窄略少，但绝不少见）——单纯「走阔」不是稀有事件，真正的信息在走阔的成因。</div>
</div>

<div class="card">
  <h2>二、单月口径：利差变化幅度 vs 银行股收益</h2>
  <div class="scroll"><table>
    <tr><th>月度档位（互斥）</th><th>样本</th><th>JPM 中位</th><th>BAC 中位</th><th>MS 中位</th><th>bank3 中位</th><th>bank3 胜率</th><th>S&amp;P500 中位</th><th>bank3 超额中位</th></tr>
    @@T1_ROWS@@
  </table></div>
  <div class="note">五档按 Δslope 幅度划分（单月，1976-07~2026-07）。红涨绿跌。可见：<b>只有「走阔&gt;+30bp」档银行股出现明显超额（约 +@@X5_XS@@pp）</b>；+10~30bp 档超额微弱；0~+10bp 与收窄档几乎无差别——小幅度利差波动对银行股无信息量，<b>大幅走阔（月 &gt;30bp）才是有效信号</b>。</div>
  <div class="chart sm" id="c2"></div>
  <div class="note">柱 = 各档 bank3（深色）与 S&amp;P500（浅色）单月收益中位 %。</div>
</div>

<div class="card">
  <h2>三、关键：怎么走阔（形态分解）</h2>
  <div class="scroll"><table>
    <tr><th>走阔形态</th><th>样本</th><th>JPM 中位</th><th>BAC 中位</th><th>MS 中位</th><th>bank3 中位</th><th>bank3 胜率</th><th>S&amp;P500 中位</th><th>bank3 超额中位</th></tr>
    @@T2_ROWS@@
  </table></div>
  <div class="chart sm" id="c3"></div>
  <div class="note">三形态只统计「slope 走阔」月份。加息陡（2Y↑10Y↑）样本 104 个月、胜率 ~59%、超额约 +@@BEAR_XS@@pp —— 银行股最强；熊陡（2Y↓10Y↑）样本少（37 个月）且超额有限；<b>牛陡（2Y↓10Y↓）bank3 跑输 SPY</b>——短端崩塌=宽松/衰退预期，市场在定价银行资产质量而非息差。</div>
</div>

<div class="card">
  <h2>四、敏感度回归：Δslope 能解释多少银行股波动？</h2>
  <div class="grid2">
    <div class="chart sm" id="c4"></div>
    <div class="scroll" style="align-self:center;"><table>
      <tr><th>标的</th><th>n</th><th>β（%/10bp）</th><th>R²</th><th>t</th><th>p</th></tr>
      @@T3_ROWS@@
    </table>
    <div class="note" style="margin-top:8px;">β = 月频 Δslope（bp）对月收益 % 的回归斜率。* p&lt;0.10，** p&lt;0.05。<b>所有标的 R² 均 &lt;1%、p 均不显著</b>——利差变化在月度尺度上几乎不解释银行股收益。银行股收益主要受信用周期、盈利、风险偏好驱动；利差只是其中很小的一块。</div>
    </div>
  </div>
</div>

<div class="card">
  <h2>五、显著走阔期（Δslope≥10bp/月）明细：Top 20</h2>
  <div class="scroll" style="max-height:480px;overflow-y:auto;"><table>
    <tr><th>时期</th><th>长度</th><th>2Y 变化</th><th>10Y 变化</th><th>slope 变化</th><th>形态</th><th>bank3</th><th>JPM</th><th>BAC</th><th>MS</th><th>S&amp;P500</th><th>超额</th><th>bank3 分位</th></tr>
    @@T4_ROWS@@
  </table></div>
  <div class="note">按 |slope 变化| 取前 20（再按时间排序）。「bank3 分位」= 该段累计收益在全部同长度随机月窗口中的百分位（&gt;50 表示好于随机）。可见 2004-2005、2013、2016、2021、2024 的走阔期银行股表现位居历史高分位。</div>
</div>

<div class="card">
  <h2>六、七个标志性时期：走阔 vs 对照</h2>
  <div class="scroll"><table>
    <tr><th>时期</th><th>slope 变化</th><th>bank3</th><th>JPM</th><th>BAC</th><th>MS</th><th>KRE</th><th>S&amp;P500</th></tr>
    @@T5_ROWS@@
  </table></div>
  <div class="note">区间收益（复权）。对照·1994 = 加息初期短端涨更快（曲线反而走平），用于对比。<b>规律：长端领涨的走阔（2013/2016/2021/2024）bank3 大幅跑赢 SPY；危机牛陡（2020）bank3 腰斩级下跌、重创。</b></div>
  <div class="grid2">
    <div class="chart sm" id="c5a"></div>
    <div class="chart sm" id="c5b"></div>
    <div class="chart sm" id="c5c"></div>
    <div class="chart sm" id="c5d"></div>
  </div>
  <div class="note">日频图：绿/红线 = 2Y/10Y 收益率（左轴），其余线 = 自段首归一化收益 %（右轴）。左上 2016-11~2017-03（Trump 再通胀）：2Y、10Y 同步抬升、slope 走阔，银行股全线大涨；右上 2021-01~03（Reflation）：10Y 从 0.9% 冲到 1.7%，JPM/BAC/KRE 涨 20%+；左下 2020-02~05（危机牛陡）：2Y 崩至 0.25%、10Y 回落，银行股 -20%+；右下 2024-09~12（降息+长端反弹）：2Y 先降后稳、10Y 4.5%，MS 弹性最大 +27.7%。</div>
</div>

<div class="card">
  <h2>七、显著走阔之后：买银行股能拿多久？</h2>
  <div class="scroll"><table>
    <tr><th>持有期</th><th>样本</th><th>bank3 中位</th><th>bank3 胜率</th><th>JPM 中位</th><th>BAC 中位</th><th>MS 中位</th><th>S&amp;P500 中位</th></tr>
    @@T6_ROWS@@
  </table></div>
  <div class="note">以每个「显著走阔期（≥10bp/月）」结束日为锚，计算其后 3/6/12 个月收益（bank3 为三股均值）。样本为 1980 后全部显著走阔期（@@FWD_N@@ 段）。后 12 个月 bank3 中位 @@FWD12@@%、胜率 @@FWD12_WR@@%，小幅跑赢 SPY（@@FWD12_SPY@@%）——<b>走阔本身作为信号偏正面但强度有限，更可靠的解读是：不要因为「利差收窄」而恐慌卖出银行股，历史后验胜率在收窄期后的持有表现同样为正</b>。</div>
</div>

<div class="card">
  <h2>结论与机制</h2>
  <h3>回答：10Y-2Y 利差扩大的情况下，JPM/MS/BAC 表现如何？</h3>
  <p><b>1. 方向本身：弱信号。</b>全部 601 个月中，走阔 268 个月、收窄 316 个月（其余持平）。bank3 在走阔月单月收益中位 @@UP_ALL_MED@@%、胜率 @@UP_ALL_WR@@%；收窄月 @@DOWN_ALL_MED@@%、胜率 @@DOWN_ALL_WR@@%——差异远小于波动，回归与均值差检验均不显著（p&gt;0.1）。<b>「利差扩大会涨」不是可靠的交易规则</b>，只有大幅走阔（月 &gt;30bp，仅 @@UP_STRONG_N@@ 个月）才出现稳定超额。</p>
  <p><b>2. 成因比方向重要。</b>同为走阔：<b>加息陡（长端领涨）</b>= 增长/通胀/财政预期升温 → 银行净息差预期改善 + 风险偏好回升 + 交易/投行业务活跃（MS 弹性最大）→ 单月中位 @@BEAR_M@@% vs SPY @@SPY_BEAR@@%；<b>牛陡（短端领跌）</b>= 联储宽松 / 衰退担忧 → 息差改善被信用成本与坏账担忧对冲 → bank3 中位 @@BULL_M@@% 跑输 SPY @@SPY_BULL@@%。2020 危机牛陡 bank3 -22.6% vs SPY -6.3% 是最极端样本。</p>
  <p><b>3. 当前读数（2026-08）。</b>slope 51bp，7 月以来 2Y 持平 4.17%、10Y +20bp 至 4.68%——<b>长端领涨型</b>，形态上更接近 2013/2024 而非 2020。历史对应：长端领涨走阔期银行股相对跑赢；但 8/18 IPP/公用事业大跌显示「30Y 5.32% 创 2007 来新高」的斜率急升也伴随估值再定价，银行股若要复制 2013/2024 的相对强势，需要利率上行来自「增长/通胀」而非「财政供给+风险溢价」。两者对银行的影响方向相反：前者提息差，后者压估值。</p>
  <div class="warn">局限性：回归与均值差检验均不显著，大幅走阔档样本仅 @@UP_STRONG_N@@ 个月；形态划分依赖月末值、边界有噪音；未计交易成本与股息再投资细节；MS 1993 起、BAC 1990 起、KRE 2006 起才有数据，早期时期（1976-1989）无银行股样本；周频口径（≥20bp/周走阔，57 周）结论一致：bank3 中位 +1.4% vs SPY +0.07%，大幅走阔周银行显著占优。</div>
</div>

</div>
<script>
const slopeDates = @@SLOPE_DATES@@;
const slopeVals = @@SLOPE_VALS@@;
const markAreas = @@MARK_AREAS@@;
const curDate = "@@CUR_DATE@@";
const curSlope = @@CUR_SLOPE@@;
const bucketKeys = @@BUCKET_KEYS@@;
const bucketBK = @@BUCKET_BK@@;
const bucketSPY = @@BUCKET_SPY@@;
const typeKeys = @@TYPE_KEYS@@;
const typeBK = @@TYPE_BK@@;
const typeSPY = @@TYPE_SPY@@;
const typeN = @@TYPE_N@@;
const scatter = @@SCATTER@@;
const regLine = @@REG_LINE@@;
const cases = @@CASES@@;

function mk(id){ return echarts.init(document.getElementById(id)); }
const RED="#e03131", GREEN="#0aa06e", BLUE="#1e66d6", AMBER="#b45309", PURPLE="#7048e8", GRAY="#9aa4b2", ORANGE="#d97706";

// 图1 利差全景
const c1 = mk('c1');
c1.setOption({
  tooltip:{trigger:'axis'},
  grid:{left:55,right:30,top:35,bottom:45},
  xAxis:{type:'category',data:slopeDates,axisLabel:{show:false},axisTick:{show:false}},
  yAxis:{type:'value',name:'10Y-2Y (%)'},
  dataZoom:[{type:'slider',height:18,bottom:6}],
  series:[{
    name:'10Y-2Y 利差',type:'line',data:slopeVals,symbol:'none',
    lineStyle:{color:BLUE,width:1.2},
    markArea:{silent:true,data:markAreas},
    markPoint:{data:[{xAxis:curDate,yAxis:curSlope,name:'当前',itemStyle:{color:RED},symbol:'diamond',symbolSize:12,
      label:{show:true,fontSize:9,formatter:'当前 '+curSlope.toFixed(2)}}]}
  }]
});

// 图2 五档
const c2 = mk('c2');
c2.setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{top:0,data:['bank3 中位','S&P500 中位']},
  grid:{left:50,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:bucketKeys,axisLabel:{fontSize:10}},
  yAxis:{type:'value',name:'单月收益中位 %'},
  series:[
    {name:'bank3 中位',type:'bar',data:bucketBK,itemStyle:{color:BLUE,borderRadius:[3,3,0,0]},barGap:'15%'},
    {name:'S&P500 中位',type:'bar',data:bucketSPY,itemStyle:{color:'#bcd3f5',borderRadius:[3,3,0,0]}}
  ]
});

// 图3 形态分解
const c3 = mk('c3');
c3.setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
    formatter:p=>{const i=p[0].dataIndex;return typeKeys[i]+'（'+typeN[i]+' 个月）<br>'+p.map(x=>x.marker+x.seriesName+': '+x.value+'%').join('<br>');}},
  legend:{top:0,data:['bank3 中位','S&P500 中位']},
  grid:{left:50,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:typeKeys,axisLabel:{fontSize:10}},
  yAxis:{type:'value',name:'单月收益中位 %'},
  series:[
    {name:'bank3 中位',type:'bar',data:typeBK,itemStyle:{color:PURPLE,borderRadius:[3,3,0,0]},barGap:'15%'},
    {name:'S&P500 中位',type:'bar',data:typeSPY,itemStyle:{color:'#e3d5f0',borderRadius:[3,3,0,0]}}
  ]
});

// 图4 散点回归
const c4 = mk('c4');
c4.setOption({
  title:{text:'Δslope(bp) → bank3 月收益（散点+回归线）',fontSize:13,left:0},
  tooltip:{trigger:'item',formatter:p=>'Δslope '+p.value[0]+'bp<br>bank3 '+p.value[1]+'%'},
  grid:{left:50,right:20,top:45,bottom:40},
  xAxis:{type:'value',name:'Δslope (bp/月)'},
  yAxis:{type:'value',name:'bank3 月收益 %'},
  series:[
    {name:'散点',type:'scatter',data:scatter,symbolSize:4,itemStyle:{color:'rgba(30,102,214,.35)'}},
    {name:'回归线',type:'line',data:regLine,symbol:'none',lineStyle:{color:ORANGE,width:2},markLine:{silent:true,symbol:'none',
      lineStyle:{color:GRAY,type:'dashed'},data:[{yAxis:0}]}}
  ]
});

// 案例日频
function caseChart(id, cid, y2c, y10c){
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
      {name:'JPM',type:'line',data:c.rets.jpm,symbol:'none',lineStyle:{color:BLUE,width:1.4},yAxisIndex:1},
      {name:'BAC',type:'line',data:c.rets.bac,symbol:'none',lineStyle:{color:AMBER,width:1.4},yAxisIndex:1},
      {name:'MS',type:'line',data:c.rets.ms,symbol:'none',lineStyle:{color:PURPLE,width:1.4},yAxisIndex:1},
      {name:'KRE',type:'line',data:c.rets.kre,symbol:'none',lineStyle:{color:'#2ca02c',width:1.2},yAxisIndex:1},
      {name:'S&P500',type:'line',data:c.rets.gspc,symbol:'none',lineStyle:{color:GRAY,width:1.1,type:'dashed'},yAxisIndex:1}
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
def get(d, k):
    v = d.get(k)
    return v if v is not None else None

sm = R["single_month"]
b = sm["up_strong"]["bank3"]
x5 = b.get("xs_median") if b else None
bear_xs = type_stats["加息陡(2Y升10Y升)"]["bank3"].get("xs_median")
bull_spy = type_stats["牛陡(2Y降10Y降)"]["gspc"]["median"]
up_all = sm["up"]["bank3"]; down_all = sm["down"]["bank3"]
fwd12_spy = fwd["m12"]["gspc"]["median"]

# 散点 + 回归线
rb = reg["bank3"]
scatter = [[d, r] for d, r in zip(R["slope_monthly_series"]["dslope"],
                                   R["slope_monthly_series"]["bank3_ret"])
           if r is not None and abs(d) <= 150]
regLine = [[-80, round(rb["alpha"] + rb["beta_per_bp"] * -80, 2)],
           [80, round(rb["alpha"] + rb["beta_per_bp"] * 80, 2)]]

t1_rows_html = "\n    ".join(t1_rows)
t2_rows_html = "\n    ".join(t2_rows)
t4_rows_html = "\n    ".join(t4_rows)
t5_rows_html = "\n    ".join(t5_rows)

# 图2/图3 数据
bucketBK = [bucket_data[k]["bank3"]["median"] if bucket_data[k]["bank3"] else None for k in BUCKET_KEYS]
bucketSPY = [bucket_data[k]["gspc"]["median"] if bucket_data[k]["gspc"] else None for k in BUCKET_KEYS]
typeBK = [type_stats[t]["bank3"]["median"] if type_stats[t].get("bank3") else None for t in TYPE_KEYS]
typeSPY = [type_stats[t]["gspc"]["median"] if type_stats[t].get("gspc") else None for t in TYPE_KEYS]
typeN = [type_stats[t]["bank3"]["n"] if type_stats[t].get("bank3") else 0 for t in TYPE_KEYS]

html = (TEMPLATE
        .replace("@@UP_MED@@", f"{up_med:+.2f}")
        .replace("@@UP_WR@@", str(up_wr))
        .replace("@@UP_XS@@", f"{up_xs:+.2f}" if up_xs is not None else "-")
        .replace("@@BEAR_M@@", f"{bear_m:+.2f}")
        .replace("@@SPY_BEAR@@", f"{spy_bear:+.2f}")
        .replace("@@BULL_M@@", f"{bull_m:+.2f}")
        .replace("@@BULL_SPY@@", f"{bull_spy:+.2f}")
        .replace("@@FWD12@@", f"{fwd12:+.1f}")
        .replace("@@FWD12_WR@@", str(fwd12_wr))
        .replace("@@FWD12_SPY@@", f"{fwd12_spy:+.1f}")
        .replace("@@SLOPE@@", f"{cur_slope * 100:.0f}")
        .replace("@@CUR_DATE@@", cur_date)
        .replace("@@SLOPE_BP@@", f"{cur_slope * 100:.0f}")
        .replace("@@UP_PCT@@", f"{round(cc['up_loose'] / n_months * 100, 1)}")
        .replace("@@X5_XS@@", f"{x5:+.1f}" if x5 is not None else "-")
        .replace("@@BEAR_XS@@", f"{bear_xs:+.1f}" if bear_xs is not None else "-")
        .replace("@@UP_ALL_MED@@", f"{up_all['median']:+.2f}")
        .replace("@@UP_ALL_WR@@", str(up_all["win_rate"]))
        .replace("@@DOWN_ALL_MED@@", f"{down_all['median']:+.2f}")
        .replace("@@DOWN_ALL_WR@@", str(down_all["win_rate"]))
        .replace("@@UP_STRONG_N@@", str(cc["up_strong"]))
        .replace("@@FWD_N@@", str(len(fwd_rows)))
        .replace("@@T1_ROWS@@", t1_rows_html + "\n    " + base_row)
        .replace("@@T2_ROWS@@", t2_rows_html)
        .replace("@@T3_ROWS@@", t3_rows)
        .replace("@@T4_ROWS@@", t4_rows_html)
        .replace("@@T5_ROWS@@", t5_rows_html)
        .replace("@@T6_ROWS@@", t6_rows)
        .replace("@@SLOPE_DATES@@", js(slope_dates))
        .replace("@@SLOPE_VALS@@", js(slope_vals))
        .replace("@@MARK_AREAS@@", js(mark_areas))
        .replace("@@CUR_SLOPE@@", js(cur_slope))
        .replace("@@BUCKET_KEYS@@", js(BUCKET_KEYS))
        .replace("@@BUCKET_BK@@", js(bucketBK))
        .replace("@@BUCKET_SPY@@", js(bucketSPY))
        .replace("@@TYPE_KEYS@@", js(TYPE_KEYS))
        .replace("@@TYPE_BK@@", js(typeBK))
        .replace("@@TYPE_SPY@@", js(typeSPY))
        .replace("@@TYPE_N@@", js(typeN))
        .replace("@@SCATTER@@", js(scatter))
        .replace("@@REG_LINE@@", js(regLine))
        .replace("@@CASES@@", js(cases)))

with open(os.path.join(OUT, "banks_steep_report.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("报告已生成:", os.path.join(OUT, "banks_steep_report.html"))
