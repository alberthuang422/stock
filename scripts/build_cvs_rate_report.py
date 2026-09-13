# -*- coding: utf-8 -*-
"""构建 CVS×利率敏感性补充页（并入 reports/66_CVS与VIX高波动期表现/）
读取 results/cvs_rate_sens.json，生成 reports/66_CVS与VIX高波动期表现/补充_公司研究与利率敏感性/利率敏感性.html
注意：corr 存的是小数（如 0.1146），注入 ECharts 必须 ×100 转百分数（项目单位陷阱铁律）
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results", "cvs_rate_sens.json")
OUT_DIR = os.path.join(BASE, "reports", "66_CVS与VIX高波动期表现", "补充_公司研究与利率敏感性")
OUT = os.path.join(OUT_DIR, "利率敏感性.html")

with open(RES, encoding="utf-8") as f:
    D = json.load(f)

# 预提取图表数据（corr ×100 转百分数）
roll = D["roll_series"]
c10 = [{"d": r["d"], "v": None if r["c10"] is None else round(r["c10"] * 100, 1)} for r in roll]
c2s = [{"d": r["d"], "v": None if r["c2"] is None else round(r["c2"] * 100, 1)} for r in roll]
b10 = [{"d": r["d"], "v": None if r["b10"] is None else round(r["b10"], 3)} for r in roll]

cum = D["cum_series"]

peers = D["peers"]
peer_rows = []
for tk in ["CVS", "UNH", "CI", "XLV"]:
    p = peers.get(tk)
    if not p:
        continue
    peer_rows.append({
        "t": tk, "beta": p["beta_d10"], "p": p["p_d10"], "sig": p["sig_d10"],
        "corr": p["corr_d10"], "vol": p["ann_vol"], "n": p["n"],
        "beta2": p["beta_d2"], "p2": p["p_d2"], "sig2": p["sig_d2"],
    })

buckets = D["buckets"]["post_d10"]
bk_rows = [b for b in buckets if not b.get("skip")]

shapes = [s for s in D["shape"] if not s.get("skip")]
steep = [s for s in D["steep"] if not s.get("skip")]

lv = D["models_by_level"]
lv_rows = []
for k in ["<2%", "2–3%", "3–4%", "≥4%"]:
    m = lv.get(k, {})
    ma = m.get("modelA") or {}
    mb = m.get("modelB") or {}
    lv_rows.append({
        "k": k, "n": m.get("n"), "span": m.get("span", ""), "y10": m.get("y10_mean"),
        "beta": ma.get("beta_d10"), "p": ma.get("p_d10"), "sig": ma.get("sig_d10"),
        "betaL": mb.get("beta_level"), "pL": mb.get("p_level"), "sigL": mb.get("sig_level"),
        "corr": m.get("corr", {}).get("cvs_d10"),
    })

q = D["quarters"]
q_rows = [{"q": x["q"], "corr": x["corr_d10"], "beta": x["beta_d10"], "p": x["p_d10"],
           "sig": x["sig"], "ret": x["ret_cvs"], "spy": x["ret_spy"], "ex": x["excess"],
           "d_bp": x["d_q_bp"], "y0": x["y10_start"], "y1": x["y10_end"]} for x in q]

expl = D["explained"]
# JS 侧统一用 full/pre/post 三键（JSON 里是 pre_aetna/post_aetna）
expl_js = {"full": expl["full"], "pre": expl["pre_aetna"], "post": expl["post_aetna"]}
cur = D["current"]
rolls = D["roll_stats"]
mods = D["models"]

# 模型表格行
def mrow(m):
    return {"n": m["n"], "r2": m["r2"], "alpha": m.get("alpha"), "p_alpha": m.get("p_alpha"),
            "b10": m.get("beta_d10"), "t10": m.get("t_d10"), "p10": m.get("p_d10"), "s10": m.get("sig_d10"),
            "b2": m.get("beta_d2"), "t2": m.get("t_d2"), "p2": m.get("p_d2"), "s2": m.get("sig_d2"),
            "bspy": m.get("beta_spy"), "pspy": m.get("p_spy"),
            "blv": m.get("beta_level"), "tlv": m.get("t_level"), "plv": m.get("p_level"), "slv": m.get("sig_level"),
            "bsl": m.get("beta_slope"), "psl": m.get("p_slope"), "ssl": m.get("sig_slope")}

model_rows = {
    "full": mrow(mods["full"]["modelA"]), "fullB": mrow(mods["full"]["modelB"]),
    "pre": mrow(mods["pre_aetna"]["modelA"]), "preB": mrow(mods["pre_aetna"]["modelB"]),
    "post": mrow(mods["post_aetna"]["modelA"]), "postB": mrow(mods["post_aetna"]["modelB"]),
}

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CVS × 美债利率敏感性分析 · 2026-09</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#1a1d24;--ink2:#4a5260;--ink3:#7a8290;--line:#e3e7ed;
--accent:#1f5fbf;--accent-soft:#eaf1fc;--up:#c0392b;--down:#1e8449;--warn:#b9770e;--warn-soft:#fdf5e3;
--danger:#a93226;--danger-soft:#fdecea;--ok-soft:#eaf5ee;--ok:#1e7a45;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue","Microsoft YaHei",sans-serif;font-size:15px;line-height:1.75;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px 72px;}
header{background:linear-gradient(135deg,#1f5fbf 0%,#2d7a5f 100%);color:#fff;padding:36px 0 28px;margin-bottom:26px;}
header .wrap{padding-bottom:0;}
h1{margin:0 0 8px;font-size:28px;font-weight:700;}
.sub{opacity:.92;font-size:13.5px;}
h2{font-size:21px;margin:44px 0 14px;padding-left:12px;border-left:4px solid var(--accent);line-height:1.3;}
h3{font-size:16.5px;margin:24px 0 10px;}
p{margin:10px 0;color:var(--ink2);}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0;}
.tldr{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:10px;padding:22px 24px;margin-bottom:8px;}
.tldr h2{margin:0 0 12px;border:none;padding:0;font-size:19px;color:var(--accent);}
.tldr ul{margin:8px 0 0;padding-left:20px;}
.tldr li{margin:9px 0;color:var(--ink2);}
.grid{display:grid;gap:12px;}
.g4{grid-template-columns:repeat(4,1fr);}
.g2{grid-template-columns:repeat(2,1fr);}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 15px;}
.kpi .k{font-size:12.5px;color:var(--ink3);margin-bottom:5px;}
.kpi .v{font-size:21px;font-weight:700;line-height:1.25;}
.kpi .n{font-size:11.5px;color:var(--ink3);margin-top:3px;}
.up{color:var(--up);}.down{color:var(--down);}
table{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0;}
th,td{padding:8px 10px;text-align:right;border-bottom:1px solid var(--line);}
th{background:#f0f3f7;color:var(--ink2);font-weight:600;white-space:nowrap;}
td:first-child,th:first-child{text-align:left;}
tbody tr:hover{background:#fafbfd;}
.chart{width:100%;height:350px;}
.src{font-size:12px;color:var(--ink3);margin-top:6px;}
.note{font-size:13px;color:var(--ink3);background:#f4f6f9;border-radius:6px;padding:9px 12px;margin:10px 0;}
.tag{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:20px;margin-right:6px;font-weight:600;}
.t-good{background:var(--ok-soft);color:var(--ok);}
.t-bad{background:var(--danger-soft);color:var(--danger);}
.t-mid{background:var(--warn-soft);color:var(--warn);}
.t-info{background:var(--accent-soft);color:var(--accent);}
.sig-s{background:#eaf5ee;color:#1e7a45;border-radius:4px;padding:1px 7px;font-size:11.5px;font-weight:700;}
.sig-e{background:#fdf5e3;color:#b9770e;border-radius:4px;padding:1px 7px;font-size:11.5px;font-weight:700;}
.sig-n{background:#eef0f3;color:#7a8290;border-radius:4px;padding:1px 7px;font-size:11.5px;font-weight:700;}
.term{border-bottom:1px dotted var(--accent);color:var(--accent);cursor:help;position:relative;font-weight:500;}
.term:hover .tip{visibility:visible;opacity:1;transform:translateY(0);}
.tip{visibility:hidden;opacity:0;position:absolute;bottom:130%;left:50%;transform:translateX(-50%) translateY(4px);width:280px;background:#232833;color:#eef1f5;font-size:12.5px;line-height:1.65;padding:11px 13px;border-radius:7px;z-index:99;transition:opacity .16s,transform .16s;box-shadow:0 6px 22px rgba(0,0,0,.22);font-weight:400;}
.tip::after{content:"";position:absolute;top:100%;left:50%;margin-left:-6px;border:6px solid transparent;border-top-color:#232833;}
details{border:1px solid var(--line);border-radius:8px;background:#fff;padding:10px 16px;margin:10px 0;}
summary{cursor:pointer;font-weight:600;color:var(--ink);font-size:14px;padding:4px 0;}
.disc{background:#f4f6f9;border:1px solid var(--line);border-radius:8px;padding:14px 18px;margin-top:34px;font-size:13px;color:var(--ink2);}
.legend{font-size:12.5px;color:var(--ink3);margin:6px 0 12px;padding:8px 12px;background:#f4f6f9;border-radius:6px;}
@media(max-width:860px){.g4,.g2{grid-template-columns:1fr 1fr;}}
</style>
</head>
<body>
<header><div class="wrap">
<h1>CVS × 美债利率（US10Y / US2Y）敏感性分析</h1>
<div class="sub">日频回归 + 60 日滚动相关 + 期限结构形态 + 分档超额 ｜ 行情截至 2026-09-01 ｜ 利率截至 2026-08-27（FRED）</div>
</div></header>

<div class="wrap">

<div class="tldr">
<h2>一页结论</h2>
<ul>
<li><b>选 US10Y，不选 US2Y。</b>Δ2Y 对 CVS 在所有回归规格下都不显著（p&gt;0.3），增量解释力为 0；Δ10Y 是唯一有效因子。回答你的问题：<b>敏感性分析做 US10Y 即可，US2Y 可以直接放弃</b>。</li>
<li><b>方向：正敏感——长端利率上行，CVS 反而跑赢。</b>post-Aetna（2018-11 起）控制大盘后，ΔUS10Y 每 +100bp，CVS 当日超额 +2.7%（β_level=+0.027，p=0.0003）。机制是价值/防御属性：利率上行往往伴随成长股杀估值，资金轮动进低估值（前瞻 PE 12×）的管理式医疗。UNH/CI 同样正敏感，XLV（板块 ETF）不敏感——<b>这是管理式医疗行业共性，不是 CVS 个性，也不是板块属性</b>。</li>
<li><b>但幅度很小：利率不是 CVS 的主要定价因子。</b>把 Δ10Y 加进模型，增量 R² 只有 0.64pp（大盘 SPY 解释 16%）。β 统计显著 ≠ 经济意义重大。</li>
<li><b>最关键的不是方向，是条件：敏感性随利率环境剧烈变化。</b>① 期限结构：倒挂期 CVS 年化 −15.6% 且利率敏感失效；曲线越陡表现越强（陡峭 ≥50bp 期年化 +41%、β 最强 +0.047）；② 利率水平：低利率时代（US10Y&lt;2%）β 显著为正（+0.059），<b>当前高利率档（≥4%）β 已转负且不显著</b>。</li>
<li><b>当前状态：历史正 β 已失效。</b>现 US10Y 4.67%、2s10s +47bp（接近 50bp 陡峭门槛）、最新 60 日滚动相关 −0.024（已归零转负）。<b>当前环境下的正确表述：CVS 对利率基本免疫，若美债继续上行，它的"利率尾风"（2025 年那波行情的一部分）已经消失。</b></li>
</ul>
</div>

<div class="grid g4">
<div class="kpi"><div class="k">US10Y（最新）</div><div class="v">4.67%</div><div class="n">1 年前 4.26% · 60日波动 4.4bp/日</div></div>
<div class="kpi"><div class="k">US2Y（最新）</div><div class="v">4.20%</div><div class="n">2s10s 斜率 +47bp（临界）</div></div>
<div class="kpi"><div class="k">60 日滚动相关（CVS×Δ10Y）</div><div class="v" style="color:var(--down);">−2.4%</div><div class="n">历史均值 +12.6% · 已归零转负</div></div>
<div class="kpi"><div class="k">60 日滚动 β</div><div class="v" style="color:var(--down);">−0.012</div><div class="n">post-Aetna 均值 +0.024</div></div>
</div>
<div class="src">数据来源：行情 Yahoo（CDP，2026-09-01 收盘）；利率 FRED DGS10/DGS2（2026-08-27，美债市场 08-28 后无交易日数据源更新）；分析见 results/cvs_rate_sens.json。</div>

<h2>一、回答你的问题：US10Y 还是 US2Y？</h2>
<p>两者同时放进回归（控制 SPY）后，<b>只有 ΔUS10Y 显著，ΔUS2Y 的系数在所有样本段都接近 0 且 p&gt;0.3</b>。原因很直接：Δ10Y 与 Δ2Y 高度共线（corr=0.79），而 CVS 的定价更贴近长端——它的估值锚、险资再投资收益、以及"利率上行=衰退担忧缓解"的信号都来自长端。短端的货币政策路径（加息/降息）对它反而是噪声。</p>
<table>
<thead><tr><th>规格（post-Aetna，控制 SPY）</th><th>β_Δ10Y</th><th>t / p</th><th>显著性</th><th>β_Δ2Y</th><th>t / p</th><th>显著性</th><th>R²</th></tr></thead>
<tbody>
<tr>
<td><b>模型 A</b>：Δ10Y + Δ2Y</td>
<td class="up">+0.0282</td><td>2.57 / 0.010</td><td><span class="sig-e">edge</span></td>
<td>−0.0016</td><td>−0.15 / 0.878</td><td><span class="sig-n">no</span></td><td>0.166</td>
</tr>
<tr>
<td><b>模型 B</b>：Δ水平(10Y) + Δ斜率</td>
<td class="up">+0.0266</td><td>3.63 / 0.0003</td><td><span class="sig-s">sig</span></td>
<td>+0.0016（斜率）</td><td>0.15 / 0.878</td><td><span class="sig-n">no</span></td><td>0.166</td>
</tr>
<tr>
<td>Δ2Y 的<b>增量 R²</b>（在 Δ10Y 之后加入）</td><td colspan="6">0.0000 —— 加入短端后解释力完全没有提升</td><td>—</td>
</tr>
</tbody>
</table>
<p class="note"><b>模型解释：</b>模型 A 把利率拆成长端+短端，但两者高度共线，系数互相拉扯；模型 B 把利率拆成「长端水平 + 期限斜率」（两者相关性仅 0.29，更正交），β_level 是最干净的估计。后文统一用模型 B 的 β_level 或模型 A 的 β_Δ10Y（两者含义近似）。</p>

<h2>二、方向：正敏感，但很小</h2>

<div class="grid g2">
<div>
<h3>分段回归（控制 SPY）</h3>
<div id="c1" class="chart" style="height:300px;"></div>
<div class="src">β = 控制 SPY 后 CVS 日收益对 ΔUS10Y 的敏感度（%/bp）。全样本 corr(Δ10Y,Δ2Y)=0.79，故展示模型 B 的 β_level。</div>
</div>
<div>
<h3>解释力拆解：利率占 CVS 收益方差的多少？</h3>
<div id="c2" class="chart" style="height:300px;"></div>
<div class="src">R² 分解：灰色为 SPY 单独解释的部分，蓝色为加入 Δ10Y 后的增量（post-Aetna 仅 +0.64pp）。红涨绿跌口径不适用于 R²。</div>
</div>
</div>

<table>
<thead><tr><th>样本段</th><th>β_level（%/bp）</th><th>t</th><th>p</th><th>显著性</th><th>corr(CVS, Δ10Y)</th><th>corr(CVS, Δ2Y)</th><th>n</th></tr></thead>
<tbody>
<tr><td>全样本（1993–2026）</td><td class="up">+0.0132</td><td>3.67</td><td>0.0002</td><td><span class="sig-s">sig</span></td><td>+0.114</td><td>+0.107</td><td>8,386</td></tr>
<tr><td>Pre-Aetna（1993–2018-11）</td><td class="up">+0.0087</td><td>2.09</td><td>0.037</td><td><span class="sig-e">edge</span></td><td>+0.114</td><td>+0.112</td><td>6,453</td></tr>
<tr><td><b>Post-Aetna（2018-11–2026）</b></td><td class="up"><b>+0.0266</b></td><td>3.63</td><td>0.0003</td><td><span class="sig-s">sig</span></td><td>+0.115</td><td>+0.090</td><td>1,933</td></tr>
</tbody>
</table>
<div class="note"><b>读法：</b>post-Aetna 的 β=+0.027，意思是"其他条件不变，长端利率单日 +10bp，CVS 相对大盘多涨约 0.27%"——这在利率单日大波动的日子（>±10bp 每年约 80 天）是可感知的，但平时基本无感。Aetna 收购后 β 翻了三倍（0.0087→0.0266），说明<b>保险业务的加入放大了利率敏感性</b>（险资固收再投资 + 政府医疗定价与利率挂钩），但即便放大后，解释力仍不足 1%。</div>

<h2>三、同业对照：这是管理式医疗的行业共性</h2>
<div id="c3" class="chart" style="height:320px;"></div>
<table>
<thead><tr><th>标的（post-Aetna 同期）</th><th>β_Δ10Y（%/bp）</th><th>p</th><th>显著性</th><th>corr(Δ10Y)</th><th>β_Δ2Y</th><th>p</th><th>显著性</th><th>年化波动</th></tr></thead>
<tbody>
<tr><td><b>CVS 西维斯健康</b></td><td class="up">+0.0282</td><td>0.010</td><td><span class="sig-e">edge</span></td><td>+0.115</td><td>−0.0016</td><td>0.878</td><td><span class="sig-n">no</span></td><td>30.5%</td></tr>
<tr><td>UNH 联合健康</td><td class="up">+0.0233</td><td>0.047</td><td><span class="sig-e">edge</span></td><td>+0.077</td><td>−0.0110</td><td>0.328</td><td><span class="sig-n">no</span></td><td>33.1%</td></tr>
<tr><td>CI 信诺</td><td class="up">+0.0344</td><td>0.003</td><td><span class="sig-s">sig</span></td><td>+0.105</td><td>−0.0133</td><td>0.230</td><td><span class="sig-n">no</span></td><td>33.0%</td></tr>
<tr><td>XLV 医疗板块 ETF</td><td>+0.0020</td><td>0.657</td><td><span class="sig-n">no</span></td><td>+0.030</td><td>−0.0112</td><td>0.011</td><td><span class="sig-e">edge</span></td><td>17.8%</td></tr>
</tbody>
</table>
<p><b>结论：</b>三家管理式医疗（CVS/UNH/CI）对 ΔUS10Y 全部正敏感且至少边缘显著，而代表整个医疗板块的 XLV 完全不敏感（β≈0）。说明这个敏感性来自<b>管理式医疗商业模式本身</b>（保险浮存金固收再投资、政府项目定价与利率挂钩、价值股属性），而不是"医疗板块"或"防御板块"的普遍特征。CVS 的敏感度（0.028）恰好介于 UNH（0.023）和 CI（0.034）之间——<b>它没有独特性，是标准的管理式医疗贝塔</b>。有趣的是 XLV 对 Δ2Y 反而是边缘显著的负敏感——进一步说明短端利率确实不属于"长端资产"的定价框架。</p>

<h2>四、60 日滚动相关：当前已归零转负</h2>
<div class="grid g2">
<div><h3>60 日滚动相关（% 口径）</h3><div id="c4" class="chart"></div>
<div class="src">黑线=CVS×Δ10Y，灰线=CVS×Δ2Y。灰色带=post-Aetna 均值 ±1σ。corr 为小数，图中 ×100 显示。</div></div>
<div><h3>60 日滚动 β（对 Δ10Y）</h3><div id="c5" class="chart"></div>
<div class="src">滚动窗口 60 交易日，控制 SPY。当前最新值 −0.012，显著低于历史均值 +0.024。</div></div>
</div>
<p><b>读图：</b>2024 年之前 CVS×Δ10Y 的 60 日相关长期在 0~+40% 区间波动（正敏感占主导）；2024Q4 一度冲到 +40% 上方（利率大幅上行+CVS 大跌那段的同步）；<b>2025Q4 起相关性掉头向下，2026 年以来持续在 0 附近徘徊，最新已转负（−2.4%）</b>。这意味着 CVS 与长端利率的联动关系在最近 12 个月已经实质性断裂——这也与 2025-2026 年 CVS 走出独立基本面行情（Aetna 修复）互相印证：<b>当基本面故事接管后，利率因子退场</b>。</p>

<h2>五、分档：利率大涨日显著跑赢，大跌日不额外受损</h2>
<div id="c6" class="chart" style="height:330px;"></div>
<table>
<thead><tr><th>ΔUS10Y 当日（post-Aetna）</th><th>n</th><th>CVS 日均收益</th><th>超额 vs SPY</th><th>胜率</th><th>t</th><th>p</th><th>显著性</th></tr></thead>
<tbody>
<tr><td class="up">大幅上行 &gt;+10bp</td><td>81</td><td class="up">+0.276%</td><td class="up">+0.443%</td><td>53.1%</td><td>2.02</td><td>0.047</td><td><span class="sig-e">edge</span></td></tr>
<tr><td class="up">上行 +3~+10bp</td><td>509</td><td class="up">+0.253%</td><td class="up">+0.096%</td><td>57.4%</td><td>1.14</td><td>0.256</td><td><span class="sig-n">no</span></td></tr>
<tr><td>震荡 −3~+3bp</td><td>785</td><td>+0.089%</td><td class="down">−0.086%</td><td>53.5%</td><td>−1.38</td><td>0.168</td><td><span class="sig-n">no</span></td></tr>
<tr><td class="down">下行 −10~−3bp</td><td>481</td><td class="down">−0.212%</td><td class="down">−0.142%</td><td>44.3%</td><td>−1.76</td><td>0.079</td><td><span class="sig-n">no</span></td></tr>
<tr><td class="down">大幅下行 &lt;−10bp</td><td>77</td><td class="down">−0.554%</td><td class="down">−0.053%</td><td>35.1%</td><td>−0.23</td><td>0.820</td><td><span class="sig-n">no</span></td></tr>
</tbody>
</table>
<p><b>不对称性：</b>利率大幅上行日（&gt;+10bp，多为"成长杀估值+避险资金流入价值"的日子）CVS 显著跑赢大盘 +0.44pp；而利率大幅下行日 CVS 只是跟随大盘下跌（超额 −0.05pp 不显著）。<b>上行有超额、下行不额外受损——这是典型低久期价值股的利率画像</b>。对照：pre-Aetna 时期所有档位超额都不显著，进一步坐实"利率敏感性是 Aetna 收购之后才长出来的"。</p>

<h2>六、真正的调节变量：期限结构形态（倒挂 / 平缓 / 陡峭）</h2>
<div id="c7" class="chart" style="height:330px;"></div>
<table>
<thead><tr><th>2s10s 形态（post-Aetna）</th><th>n</th><th>年化收益</th><th>年化波动</th><th>β_Δ10Y</th><th>p</th><th>显著性</th><th>corr</th></tr></thead>
<tbody>
<tr><td class="down">倒挂 slope&lt;0（2022-07~2024-08）</td><td>543</td><td class="down">−15.6%</td><td>28.0%</td><td>+0.013</td><td>0.204</td><td><span class="sig-n">no</span></td><td>−0.002</td></tr>
<tr><td class="up">平缓 0~50bp</td><td>734</td><td class="up">+0.8%</td><td>33.9%</td><td>+0.028</td><td>0.030</td><td><span class="sig-e">edge</span></td><td>+0.200</td></tr>
<tr><td class="up">陡峭 ≥50bp</td><td>656</td><td class="up">+41.4%</td><td>28.4%</td><td>+0.047</td><td>0.0015</td><td><span class="sig-s">sig</span></td><td>+0.136</td></tr>
</tbody>
</table>
<p><b>这是全篇最重要的结构性发现：</b>管理式医疗的利率敏感性<b>不是常数，而是"曲线形态的函数"</b>——倒挂期（衰退预警）CVS 年化 −15.6%，且利率敏感失效；曲线越陡（政策正常化、衰退担忧解除），CVS 表现越强、对长端利率的正敏感越强（β 从 0.013 → 0.047，三倍）。这与项目内银行股研究的结论同构：<b>「形态决定一切」。</b></p>
<p class="note"><b>当前的含义：</b>截至 2026-08-27，2s10s = +47bp，正悬在 50bp 的「陡峭」门槛下方。若美联储降息驱动短端更快下行、曲线陡过 50bp，CVS 将进入 post-Aetna 样本中表现最强（年化 +41%）的形态区间；反之若经济走弱、曲线重新走平甚至倒挂，则是最差环境。<b>CVS 的利率敏感性交易，本质是 2s10s 的形态交易。</b></p>

<div class="grid g2">
<div>
<h3>走阔 / 收窄日表现</h3>
<table>
<thead><tr><th>Δ斜率（post）</th><th>n</th><th>超额</th><th>胜率</th><th>p</th><th>显著性</th></tr></thead>
<tbody>
<tr><td class="up">走阔 &gt;+5bp</td><td>158</td><td class="up">+0.204%</td><td>48.7%</td><td>0.248</td><td><span class="sig-n">no</span></td></tr>
<tr><td>平稳 ±5bp</td><td>1,624</td><td>−0.025%</td><td>52.8%</td><td>0.573</td><td><span class="sig-n">no</span></td></tr>
<tr><td class="down">收窄 &lt;−5bp</td><td>151</td><td class="down">−0.313%</td><td>40.4%</td><td>0.034</td><td><span class="sig-e">edge</span></td></tr>
</tbody>
</table>
<div class="src">Δ斜率=Δ10Y−Δ2Y，单位 bp。</div>
</div>
<div>
<h3>利率水平分档（post-Aetna 内）</h3>
<table>
<thead><tr><th>US10Y 水平</th><th>n</th><th>β_Δ10Y</th><th>p</th><th>显著性</th><th>corr</th></tr></thead>
<tbody>
<tr><td>&lt;2%（2019-07~2022-03）</td><td>651</td><td class="up">+0.0588</td><td>0.0007</td><td><span class="sig-s">sig</span></td><td>+0.323</td></tr>
<tr><td>2–3%（2018-12~2022-08）</td><td>255</td><td class="up">+0.0108</td><td>0.721</td><td><span class="sig-n">no</span></td><td>+0.137</td></tr>
<tr><td>3–4%（2018-11~2026-02）</td><td>305</td><td class="up">+0.0131</td><td>0.490</td><td><span class="sig-n">no</span></td><td>+0.006</td></tr>
<tr><td class="down">≥4%（2022-10~至今）</td><td>722</td><td class="down">−0.0231</td><td>0.325</td><td><span class="sig-n">no</span></td><td>+0.009</td></tr>
</tbody>
</table>
<div class="src">分档限定在 post-Aetna 内，避免把 1993-2000 高利率时代（纯零售药房）与现在混谈。</div>
</div>
</div>
<p><b>两条曲线的交点就是当前：</b>低利率时代（US10Y&lt;2%）β 显著为正（+0.059，corr +0.32）；进入高利率时代（≥4%，当前 4.67%）后 β 转负且不显著，corr 归零。<b>所谓"CVS 利率上行跑赢"的历史规律，只在低利率+曲线趋陡的环境成立；在 4%+ 的利率水平上，这个规律已经失效</b>——这就是为什么最新 60 日相关是负的。组合起来看：当前 4.67% + 斜率 47bp，处于「高利率档（β 失效）× 临界陡峭档（β 最强）」的交叉点，两种力量方向相反，净效应是<b>利率对 CVS 的影响在当下基本中性</b>。</p>

<h2>七、季度分阶段（post-Aetna，31 个自然季度）</h2>
<details open>
<summary>季度明细：corr / β / 季度收益 / 超额（点击收起）</summary>
<div id="c8" class="chart" style="height:420px;"></div>
<table>
<thead><tr><th>季度</th><th>US10Y 变动(bp)</th><th>corr</th><th>β_Δ10Y</th><th>p</th><th>显著性</th><th>CVS 季度收益</th><th>SPY</th><th>超额</th></tr></thead>
<tbody>
__QROWS__
</tbody>
</table>
<div class="src">β 为季度内日频回归（控制 SPY）。季度内样本约 60 天，β 估计噪声大，仅作参考；显著季度极少，从反面印证日频利率敏感性是弱信号。</div>
</details>

<h2>八、结论与操作含义</h2>
<div class="card" style="border-left:5px solid var(--accent);">
<p style="font-size:15.5px;color:var(--ink);"><b>一句话：</b>CVS 对 US10Y 是「显著但很小」的正敏感（post-Aetna β≈+0.027，Δ2Y 无效），而且这个敏感性只在「低利率 + 曲线趋陡」的环境成立——<b>当前 4.67% 的高利率环境里，正 β 已经失效，最新 60 日相关 −2.4%</b>。</p>
<p style="font-size:15.5px;color:var(--ink);"><b>三个可执行的判断：</b></p>
<ul>
<li><b>利率不是 CVS 的定价主变量。</b>增量 R² 0.64pp 意味着做 CVS 不该把利率当核心因子；它的行情 95% 以上由基本面（Aetna 赔付率、Caremark 会员、340B）决定。此前 60 号报告的核心逻辑不受影响。</li>
<li><b>如果一定要交易利率，盯 2s10s 形态而不是利率方向。</b>倒挂期年化 −15.6%、陡峭期 +41.4%。当前 +47bp 距 50bp 门槛一步之遥：美联储降息 → 曲线陡化 → 对 CVS 是顺风；经济走弱 → 曲线平化/倒挂 → 是逆风。</li>
<li><b>警惕"历史 β 外推"陷阱。</b>2025 年 CVS 大涨 +83% 常被归因为基本面反转，但其中一部分是"曲线从倒挂转陡峭"的形态顺风。若 Q4 美债收益率重新上行（而非回落），这股东风已经没了——只剩基本面本身。</li>
</ul>
</div>

<div class="disc">
<b>方法口径：</b>日频回归（控制 SPY），β 单位 %/bp（ΔUS10Y 每 1bp 对应的 CVS 日收益变动）；p 值用 scipy t 分布（df=n−k）；显著性三档 sig(p&lt;0.01)/edge(p&lt;0.05)/no。60 日滚动相关为项目主口径。样本=股债同时有报价的交易日（债券市场假日如哥伦布日/退伍军人节剔除）；CVS 在 Yahoo 源缺失 2026-08-28 一根 bar（已核实为数据源缺口，SPY 等无此问题），该日及其前后两日收益不进入样本，对 8,386 日样本无实质影响。分档与形态分组均限定 post-Aetna（2018-11-28 Aetna 收购完成后），避免与纯零售时代混杂。
</div>

<div class="disc" style="background:#fdecea;border-color:#f5c6c0;">
<b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
</div>

</div>

<script>
const C10 = __C10__;
const C2S = __C2S__;
const B10 = __B10__;
const CUM = __CUM__;
const PEERS = __PEERS__;
const BK = __BK__;
const SHAPES = __SHAPES__;
const LV = __LV__;
const Q = __Q__;
const EXPL = __EXPL__;
const CUR = __CUR__;
const ROLLS = __ROLLS__;

var AX = { color: '#4a5260', fontSize: 12 };
var SPLIT = { lineStyle: { color: '#e3e7ed' } };

// c1: 分段 β
echarts.init(document.getElementById('c1')).setOption({
  tooltip: { trigger: 'axis', valueFormatter: function (v) { return v + ' %/bp'; } },
  grid: { left: 70, right: 30, top: 30, bottom: 50 },
  xAxis: { type: 'category', data: ['全样本\\n1993–2026', 'Pre-Aetna\\n1993–2018.11', 'Post-Aetna\\n2018.11–2026'], axisLabel: AX, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: { type: 'value', name: 'β (%/bp)', nameTextStyle: AX, axisLabel: AX, splitLine: SPLIT },
  series: [{
    type: 'bar', barWidth: '40%',
    data: [
      { value: 0.0132, itemStyle: { color: '#c0392b' } },
      { value: 0.0087, itemStyle: { color: '#c0392b' } },
      { value: 0.0266, itemStyle: { color: '#c0392b' } }
    ],
    label: { show: true, position: 'top', formatter: '{c}', color: '#c0392b', fontSize: 13, fontWeight: 'bold' }
  }]
});

// c2: 解释力拆解
echarts.init(document.getElementById('c2')).setOption({
  tooltip: { trigger: 'axis', valueFormatter: function (v) { return (v * 100).toFixed(1) + '%'; } },
  legend: { data: ['仅 SPY 解释', 'Δ10Y 增量', '未解释'], bottom: 0, textStyle: AX, itemWidth: 12, itemHeight: 12 },
  grid: { left: 70, right: 30, top: 30, bottom: 52 },
  xAxis: { type: 'category', data: ['全样本', 'Pre-Aetna', 'Post-Aetna'], axisLabel: AX, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: { type: 'value', name: 'R²（×100 显示%）', nameTextStyle: AX, axisLabel: { formatter: function (v) { return (v * 100).toFixed(0) + '%'; }, color: '#4a5260', fontSize: 12 }, splitLine: SPLIT },
  series: [
    { name: '仅 SPY 解释', type: 'bar', stack: 'r', barWidth: '42%', data: [{ value: EXPL.full.r2_spy_only, itemStyle: { color: '#a8b2c0' } }, { value: EXPL.pre.r2_spy_only, itemStyle: { color: '#a8b2c0' } }, { value: EXPL.post.r2_spy_only, itemStyle: { color: '#a8b2c0' } }] },
    { name: 'Δ10Y 增量', type: 'bar', stack: 'r', barWidth: '42%', data: [{ value: EXPL.full.incr_d10, itemStyle: { color: '#1f5fbf' } }, { value: EXPL.pre.incr_d10, itemStyle: { color: '#1f5fbf' } }, { value: EXPL.post.incr_d10, itemStyle: { color: '#1f5fbf' } }], label: { show: true, position: 'top', formatter: function (p) { return (p.value * 100).toFixed(2) + '%'; }, color: '#1f5fbf', fontSize: 11 } },
    { name: '未解释', type: 'bar', stack: 'r', barWidth: '42%', data: [{ value: 1 - EXPL.full.r2_plus_d10, itemStyle: { color: '#eef0f3' } }, { value: 1 - EXPL.pre.r2_plus_d10, itemStyle: { color: '#eef0f3' } }, { value: 1 - EXPL.post.r2_plus_d10, itemStyle: { color: '#eef0f3' } }] }
  ]
});

// c3: 同业 β
echarts.init(document.getElementById('c3')).setOption({
  tooltip: { trigger: 'axis', valueFormatter: function (v) { return v + ' %/bp'; } },
  grid: { left: 70, right: 30, top: 30, bottom: 40 },
  xAxis: { type: 'category', data: PEERS.map(function (p) { return p.t; }), axisLabel: AX, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: { type: 'value', name: 'β_Δ10Y (%/bp)', nameTextStyle: AX, axisLabel: AX, splitLine: SPLIT },
  series: [{
    type: 'bar', barWidth: '45%',
    data: PEERS.map(function (p) {
      return { value: p.beta, itemStyle: { color: p.beta > 0 ? '#c0392b' : '#1e8449' } };
    }),
    label: { show: true, position: 'top', formatter: function (p) { return p.value + ' (' + PEERS[p.dataIndex].sig + ')'; }, color: '#4a5260', fontSize: 11.5 }
  }]
});

// c4: 60日滚动相关（×100）
echarts.init(document.getElementById('c4')).setOption({
  tooltip: { trigger: 'axis', valueFormatter: function (v) { return v + '%'; } },
  legend: { data: ['CVS × Δ10Y', 'CVS × Δ2Y'], bottom: 0, textStyle: AX, itemWidth: 12, itemHeight: 12 },
  grid: { left: 65, right: 30, top: 30, bottom: 52 },
  xAxis: { type: 'time', axisLabel: AX, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: { type: 'value', name: '相关 (%)', nameTextStyle: AX, min: -50, max: 60, axisLabel: { formatter: '{value}%', color: '#4a5260', fontSize: 12 }, splitLine: SPLIT },
  series: [
    { name: 'CVS × Δ10Y', type: 'line', showSymbol: false, lineStyle: { width: 1.6, color: '#1a1d24' }, data: C10.map(function (r) { return [r.d, r.v]; }) },
    { name: 'CVS × Δ2Y', type: 'line', showSymbol: false, lineStyle: { width: 1, color: '#a8b2c0' }, data: C2S.map(function (r) { return [r.d, r.v]; }) }
  ]
});

// c5: 滚动 β
echarts.init(document.getElementById('c5')).setOption({
  tooltip: { trigger: 'axis', valueFormatter: function (v) { return v + ' %/bp'; } },
  grid: { left: 65, right: 30, top: 30, bottom: 40 },
  xAxis: { type: 'time', axisLabel: AX, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: { type: 'value', name: 'β (%/bp)', nameTextStyle: AX, axisLabel: AX, splitLine: SPLIT },
  series: [{
    type: 'line', showSymbol: false, lineStyle: { width: 1.6, color: '#1f5fbf' },
    data: B10.map(function (r) { return [r.d, r.v]; }),
    markLine: {
      symbol: 'none', label: { formatter: '均值 {c}', color: '#7a8290', fontSize: 11 },
      data: [{ yAxis: ROLLS.post_beta_d10_mean, lineStyle: { color: '#7a8290', type: 'dashed' } }]
    }
  }]
});

// c6: 分档超额
echarts.init(document.getElementById('c6')).setOption({
  tooltip: { trigger: 'axis', valueFormatter: function (v) { return v + '%'; } },
  grid: { left: 75, right: 40, top: 40, bottom: 45 },
  xAxis: { type: 'category', data: BK.map(function (b) { return b.bucket; }), axisLabel: AX, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: { type: 'value', name: '日均超额 (%)', nameTextStyle: AX, axisLabel: { formatter: '{value}%', color: '#4a5260', fontSize: 12 }, splitLine: SPLIT },
  series: [{
    type: 'bar', barWidth: '46%',
    data: BK.map(function (b) { return { value: b.excess, itemStyle: { color: b.excess >= 0 ? '#c0392b' : '#1e8449' } }; }),
    label: { show: true, position: 'top', formatter: function (p) { return p.value > 0 ? '+' + p.value.toFixed(3) : p.value.toFixed(3); }, color: '#4a5260', fontSize: 11.5 },
    markLine: { symbol: 'none', silent: true, label: { formatter: '', }, data: [{ yAxis: 0, lineStyle: { color: '#9aa3af' } }] }
  }]
});

// c7: 形态分组（年化收益柱 + β 线）
echarts.init(document.getElementById('c7')).setOption({
  tooltip: { trigger: 'axis' },
  legend: { data: ['年化收益', 'β_Δ10Y'], bottom: 0, textStyle: AX, itemWidth: 12, itemHeight: 12 },
  grid: { left: 70, right: 70, top: 30, bottom: 52 },
  xAxis: { type: 'category', data: SHAPES.map(function (s) { return s.shape; }), axisLabel: AX, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: [
    { type: 'value', name: '年化收益 (%)', nameTextStyle: AX, axisLabel: { formatter: '{value}%', color: '#4a5260', fontSize: 12 }, splitLine: SPLIT },
    { type: 'value', name: 'β (%/bp)', nameTextStyle: AX, min: 0, max: 0.06, axisLabel: AX, splitLine: { show: false } }
  ],
  series: [
    { name: '年化收益', type: 'bar', barWidth: '38%', data: SHAPES.map(function (s) { return { value: s.ann_ret, itemStyle: { color: s.ann_ret >= 0 ? '#c0392b' : '#1e8449' } }; }), label: { show: true, position: 'top', formatter: '{c}%', color: '#4a5260', fontSize: 12 } },
    { name: 'β_Δ10Y', type: 'line', yAxisIndex: 1, symbolSize: 9, lineStyle: { width: 3, color: '#1f5fbf' }, itemStyle: { color: '#1f5fbf' }, data: SHAPES.map(function (s) { return s.beta_d10; }), label: { show: true, formatter: '{c}', color: '#1f5fbf', fontSize: 12 } }
  ]
});

// c8: 季度
echarts.init(document.getElementById('c8')).setOption({
  tooltip: { trigger: 'axis' },
  legend: { data: ['季度超额收益', '季度内 corr(×100)'], bottom: 0, textStyle: AX, itemWidth: 12, itemHeight: 12 },
  grid: { left: 75, right: 70, top: 30, bottom: 62 },
  xAxis: { type: 'category', data: Q.map(function (x) { return x.q; }), axisLabel: { interval: 2, rotate: 45, color: '#4a5260', fontSize: 11 }, axisLine: { lineStyle: { color: '#d5dae1' } } },
  yAxis: [
    { type: 'value', name: '超额收益 (%)', nameTextStyle: AX, axisLabel: { formatter: '{value}%', color: '#4a5260', fontSize: 12 }, splitLine: SPLIT },
    { type: 'value', name: 'corr (%)', nameTextStyle: AX, min: -50, max: 50, axisLabel: { formatter: '{value}%', color: '#4a5260', fontSize: 12 }, splitLine: { show: false } }
  ],
  series: [
    { name: '季度超额收益', type: 'bar', barWidth: '45%', data: Q.map(function (x) { return { value: x.ex, itemStyle: { color: x.ex >= 0 ? '#c0392b' : '#1e8449' } }; }) },
    { name: '季度内 corr(×100)', type: 'line', yAxisIndex: 1, showSymbol: false, lineStyle: { width: 1.6, color: '#1f5fbf' }, data: Q.map(function (x) { return x.corr * 100; }) }
  ]
});

window.addEventListener('resize', function () {
  ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el && echarts.getInstanceByDom(el)) echarts.getInstanceByDom(el).resize();
  });
});
</script>
</body>
</html>
"""

# 季度行
qhtml = "\n".join(
    "<tr><td>{q}</td><td>{d:+.0f}</td><td>{corr:+.3f}</td><td>{beta:+.4f}</td><td>{p:.3f}</td>"
    "<td><span class='sig-{sig}'>{sig}</span></td>"
    "<td class='{cls_r}'>{ret:+.2f}%</td><td>{spy:+.2f}%</td><td class='{cls_e}'>{ex:+.2f}%</td></tr>".format(
        q=x["q"], d=x["d_bp"], corr=x["corr"] if x["corr"] is not None else 0,
        beta=x["beta"] if x["beta"] is not None else 0,
        p=x["p"] if x["p"] is not None else 0,
        sig=x["sig"], ret=x["ret"], spy=x["spy"],
        cls_r="up" if (x["ret"] or 0) >= 0 else "down",
        cls_e="up" if (x["ex"] or 0) >= 0 else "down",
        ex=x["ex"] or 0)
    for x in q_rows
)

HTML = (HTML
        .replace("__C10__", json.dumps(c10, ensure_ascii=False))
        .replace("__C2S__", json.dumps(c2s, ensure_ascii=False))
        .replace("__B10__", json.dumps(b10, ensure_ascii=False))
        .replace("__CUM__", json.dumps(cum, ensure_ascii=False))
        .replace("__PEERS__", json.dumps(peer_rows, ensure_ascii=False))
        .replace("__BK__", json.dumps(bk_rows, ensure_ascii=False))
        .replace("__SHAPES__", json.dumps(shapes, ensure_ascii=False))
        .replace("__LV__", json.dumps(lv_rows, ensure_ascii=False))
        .replace("__Q__", json.dumps(q_rows, ensure_ascii=False))
        .replace("__EXPL__", json.dumps(expl_js, ensure_ascii=False))
        .replace("__CUR__", json.dumps(cur, ensure_ascii=False))
        .replace("__ROLLS__", json.dumps(rolls, ensure_ascii=False))
        .replace("__QROWS__", qhtml))

os.makedirs(OUT_DIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print("written:", OUT, os.path.getsize(OUT), "bytes")
