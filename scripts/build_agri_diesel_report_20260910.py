# -*- coding: utf-8 -*-
"""生成 82 号报告 HTML（图表数据全部来自结果 JSON，脚本生成）2026-09-10"""
import json, os, csv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
OUTDIR = os.path.join(BASE, "reports", "82_农产品与柴油价格相关性")
os.makedirs(OUTDIR, exist_ok=True)

A = json.load(open(os.path.join(RES, "agri_diesel_corr_20260910.json"), encoding="utf-8"))
S = json.load(open(os.path.join(RES, "agri_diesel_seasonality_20260910.json"), encoding="utf-8"))

# 滚动相关序列
roll = {"dates": [], "ZC": [], "ZS": [], "ZW": [], "ZL": []}
with open(os.path.join(RES, "agri_diesel_roll60.csv"), encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for r in rd:
        roll["dates"].append(r["date"])
        for k in ["ZC", "ZS", "ZW", "ZL"]:
            v = r.get(k, "")
            roll[k].append(None if v in ("", "None") else round(float(v), 4))

JA = lambda o: json.dumps(o, ensure_ascii=False)
AG = ["ZC", "ZS", "ZW", "ZL"]
LBL = A["meta"]["label"]

# ---- 预计算若干展示用表 ----
A_level = A["A_level_vs_return"]
B = A["B_roll60"]
C = A["C_window_sensitivity"]
D = A["D_seasonality"]
E = A["E_phases"]
F = A["F_lead_lag"]
G = A["G_channels"]

LV = A_level["level"]
RT = A_level["return"]

# 季节指数
eia_all = S["eia_distillate"]["index_all"]
eia_5y = S["eia_distillate"]["index_5y"]
fmr = S["futures_monthly_avg_return_pct"]

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>82 · 农产品价格 × 柴油价格：相关性验证与方法论复盘</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{
  --bg:#f7f6f3; --card:#ffffff; --ink:#26313d; --sub:#5b6672; --line:#e3e0d8;
  --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --purple:#CC79A7;
  --vermil:#D55E00; --green:#009E73; --yellow:#F0E442; --grey:#9a948a;
  --red:#C0392B; --down:#1E8449;
}
*{box-sizing:border-box; margin:0; padding:0;}
body{background:var(--bg); color:var(--ink); font-family:"Microsoft YaHei","PingFang SC",sans-serif; font-size:15px; line-height:1.7;}
.wrap{max-width:1200px; margin:0 auto; padding:28px 20px 60px;}
h1{font-size:26px; letter-spacing:.5px;}
.meta{color:var(--sub); font-size:13px; margin-top:6px;}
.head{border-bottom:3px solid var(--blue); padding-bottom:14px; margin-bottom:20px;}
.kpis{display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:18px 0;}
.kpi{background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 12px;}
.kpi .t{font-size:12.5px; color:var(--sub);}
.kpi b{font-size:20px; display:block; margin-top:2px;}
.kpi .s{font-size:12px; color:var(--sub);}
h2{font-size:20px; margin:36px 0 12px; padding-left:10px; border-left:5px solid var(--blue);}
h3{font-size:16px; margin:22px 0 8px; color:#1d2833;}
.card{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:18px 20px; margin-bottom:14px;}
.chart{width:100%; height:390px;}
.chart-sm{height:340px;}
.grid2{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
table{width:100%; border-collapse:collapse; font-size:14px; background:var(--card);}
th{background:#eef1f4; color:var(--ink); font-weight:600; text-align:left;}
th,td{padding:8px 10px; border-bottom:1px solid var(--line);}
tr:hover td{background:#f6f9fc;}
.num{text-align:right; font-variant-numeric:tabular-nums;}
.tag{display:inline-block; padding:1px 8px; border-radius:10px; font-size:12px; margin-right:4px;}
.tag-b{background:#e3f0f9; color:var(--blue);}
.tag-o{background:#fdf3e0; color:#9a6400;}
.tag-g{background:#e4f4ef; color:#007a5e;}
.tag-r{background:#fbe9e4; color:var(--vermil);}
.note{font-size:12.5px; color:var(--sub);}
.concl{border-left:5px solid var(--orange);}
.toc{display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 4px;}
.toc a{text-decoration:none; color:var(--blue); background:var(--card); border:1px solid var(--line); border-radius:16px; padding:3px 14px; font-size:13px;}
.toc a:hover{background:#eaf3fa;}
ul.tight li{margin:6px 0;}
ol.tight li{margin:8px 0;}
.foot{margin-top:40px; color:var(--sub); font-size:12px; border-top:1px solid var(--line); padding-top:12px;}
.disclaimer{background:#f4f1ea; border:1px dashed var(--grey); border-radius:8px; padding:10px 14px; font-size:12.5px; color:var(--sub); margin-top:16px;}
.badge{display:inline-block; background:var(--blue); color:#fff; border-radius:4px; padding:2px 10px; font-size:13px; margin-right:6px;}
.warn{background:#fdf3e0; border-left:4px solid var(--orange); padding:10px 14px; border-radius:6px; font-size:13.5px;}
.ok{background:#e4f4ef; border-left:4px solid var(--green); padding:10px 14px; border-radius:6px; font-size:13.5px;}
.no{background:#fbe9e4; border-left:4px solid var(--vermil); padding:10px 14px; border-radius:6px; font-size:13.5px;}
.small{font-size:13px;}
@media (max-width:900px){ .kpis{grid-template-columns:repeat(2,1fr);} .grid2{grid-template-columns:1fr;} }
</style>
</head>
<body>
<div class="wrap">

<div class="head">
  <h1>82 · 农产品价格 × 柴油价格：相关性验证与方法论复盘</h1>
  <div class="meta">多口径相关性研究 ｜ 报告日 2026-09-10 ｜ 样本：NYMEX/CME 期货主连日线 2011-09 ~ 2026-09（n=3,400）｜ 柴油基准：NYMEX 取暖油/ULSD 期货（HO，美国柴油定价基准）</div>
  <div class="toc">
    <a href="#s0">摘要</a><a href="#s1">方法矩阵</a><a href="#s2">水平=假象</a><a href="#s3">真实通道</a>
    <a href="#s4">季节性检验</a><a href="#s5">窗口选择</a><a href="#s6">结构断裂</a><a href="#s7">领先滞后</a>
    <a href="#s8">结论与口径</a><a href="#s9">局限</a>
  </div>
</div>

<h2 id="s0">摘要 · 结论先行</h2>
<div class="card concl">
<ol class="tight">
<li><b>表面的"高相关"是趋势假象。</b>玉米/大豆/小麦/豆油与柴油的<b>水平价格</b>相关系数 0.60–0.76，看似很强；换成<b>日收益</b>口径后降至 0.125–0.318，衰减 58–80%。撑起表面相关的是共同趋势（通胀、美元、大宗商品超级周期），不是日度联动。</li>
<li><b>真实的联动集中在油脂，不在谷物。</b>豆油 0.318，是玉米（0.125）的 2.5 倍、小麦（0.136）的 2.3 倍。这符合<b>生物柴油通道</b>——豆油既是农产品又是柴油的竞争性原料；而小麦几乎没有能源需求端，仅剩成本端。</li>
<li><b>你担心的"季节性"在数据上不成立。</b>美国馏分油（柴油）总需求季节性极弱：月度季节指数峰谷差仅 <b>9.2%</b>，峰值在 8 月而非取暖季；农产品价格季节性明显（月均收益年幅 6.1–6.4%），但与柴油<b>相位错配</b>（6 月农产品集体最弱 −3.8%~−3.9%，柴油却最强 +2.66%）。把季节性剥离后，相关性几乎不变（Δ +0.001~+0.002）。</li>
<li><b>60 日窗口不是错的选择，但不能单用。</b>20 日滚动相关的标准差 0.23–0.25，是 60 日（0.13–0.15）的近两倍，噪声主导；60 日是噪声与分辨率的合理折中。真正需要改的是<b>"用单一数字下结论"</b>——应改为分阶段 + 分品种。</li>
<li><b>不是成本滞后传导，是同步的共同因子。</b>交叉相关峰值<b>全部落在 lag=0</b>；且柴油×原油 0.763 远高于任何农产品。农产品与柴油被同一个能源/通胀因子同步驱动，而非"柴油涨→农机作业成本升→粮价涨"的滞后链条。</li>
</ol>
</div>

<div class="kpis">
  <div class="kpi"><div class="t">玉米 × 柴油</div><b>0.64 → 0.13</b><div class="s">水平 r → 日收益 r（−80%）</div></div>
  <div class="kpi"><div class="t">大豆 × 柴油</div><b>0.68 → 0.17</b><div class="s">水平 r → 日收益 r（−75%）</div></div>
  <div class="kpi"><div class="t">小麦 × 柴油</div><b>0.60 → 0.14</b><div class="s">水平 r → 日收益 r（−77%）</div></div>
  <div class="kpi"><div class="t">豆油 × 柴油</div><b>0.76 → 0.32</b><div class="s">水平 r → 日收益 r（−58%，最强）</div></div>
</div>

<h2 id="s1">一、研究设计与方法矩阵</h2>
<div class="card">
<p class="small">你的原始提法："农产品价格可能跟柴油价格有较大相关性，但 60/30 日滚动相关可能不合适，因为农业有季节性和阶段差异。"<br>
我们把这句话拆成 <b>4 个可检验命题</b>，并配 8 组口径——每一组都在回答"用什么方法看才对"。</p>
<table>
<thead><tr><th style="width:14%">模块</th><th style="width:34%">口径</th><th>回答的问题</th></tr></thead>
<tbody>
<tr><td><span class="tag tag-b">A</span>水平 vs 收益</td><td>水平价格 Pearson ↔ 日对数收益 Pearson</td><td>"高相关"是真联动，还是共同趋势的假象？</td></tr>
<tr><td><span class="tag tag-b">B</span>60 日滚动</td><td>日收益 60 日滚动相关（你的原口径）</td><td>这条曲线长什么样？有多不稳定？</td></tr>
<tr><td><span class="tag tag-b">C</span>窗口敏感性</td><td>20 / 30 / 60 / 120 / 250 日滚动对比</td><td>60 天是不是合适？换窗口结论会变吗？</td></tr>
<tr><td><span class="tag tag-o">D</span>季节性</td><td>分日历月 / 分农事季节 / 季节性剥离 / 窗口季节归属</td><td><b>农业季节性是否让 60 日窗口失真？</b></td></tr>
<tr><td><span class="tag tag-g">E</span>分阶段</td><td>6 个宏观阶段分别计算</td><td>相关性是不是稳定结构？</td></tr>
<tr><td><span class="tag tag-g">F</span>领先滞后</td><td>lag −10 ~ +10 日交叉相关</td><td>是成本滞后传导，还是同步？</td></tr>
<tr><td><span class="tag tag-r">G</span>机制通道</td><td>柴油×原油 / 豆油×柴油 / 玉米×汽油 / 裂解价差</td><td>相关性走的是哪条经济通道？</td></tr>
<tr><td><span class="tag tag-o">H</span>实物需求季节</td><td>EIA 馏分油产品供应（周度→月度季节指数）</td><td>"有些月份更耗柴油"是否成立？</td></tr>
</tbody></table>
<p class="note" style="margin-top:10px">口径纪律：所有相关性均以<b>日对数收益 ×100</b> 为主口径（水平口径仅作对照）；显著性按 Pearson t 检验，* p&lt;0.05、** p&lt;0.01、*** p&lt;0.001，ns=不显著。样本 2011-09-02 ~ 2026-09-08，有效交易日 3,400 个（小麦自 2017-11 起，n=2,220）。</p>
</div>

<h2 id="s2">二、第一层：水平口径的"高相关"是假象</h2>
<div class="card">
<div id="c_lvl" class="chart"></div>
<p class="small" style="margin-top:8px">左：水平价格相关；右：日收益相关。<b>原油、汽油几乎不受影响</b>（0.91→0.76、0.93→0.71），因为它们与柴油共享同一现货基本面；而<b>农产品衰减 58–80%</b>——说明农产品与柴油的"相关"大部分来自两条独立上涨/下跌的长趋势叠在一起。</p>
<table style="margin-top:12px">
<thead><tr><th>品种</th><th class="num">水平 r</th><th class="num">日收益 r</th><th class="num">衰减幅度</th><th class="num">Spearman</th><th>显著性</th><th>解读</th></tr></thead>
<tbody id="tb_lvl"></tbody>
</table>
<div class="warn" style="margin-top:12px"><b>口径陷阱：</b>如果你用价格水平去算"农产品与柴油相关 0.6–0.7"并据此认为"能跟踪柴油做农产品"，这个结论不成立。水平相关是趋势伪相关——项目内既有的利率敏感度研究（水平×水平=伪相关）是同一个道理。</div>
</div>

<h2 id="s3">三、第二层：真实联动弱，且集中在油脂</h2>
<div class="card">
<div class="grid2">
  <div><div id="c_chan" class="chart chart-sm"></div></div>
  <div>
    <h3 style="margin-top:0">通道分解结果</h3>
    <table>
      <thead><tr><th>组合</th><th class="num">日收益 r</th><th>经济通道</th></tr></thead>
      <tbody id="tb_chan"></tbody>
    </table>
    <div class="ok" style="margin-top:12px"><b>关键读法：</b>柴油×原油 0.763 是"能源内部强相关"的标尺；以此为参照，<b>豆油×柴油 0.318 相当于该标尺的 42%</b>，而玉米/小麦只有 14–18%。农产品的能源属性<b>高度不均</b>——油脂类（生物柴油原料）显著强于谷物。</div>
  </div>
</div>
<div class="card" style="margin-top:14px; padding:14px 20px">
<h3 style="margin-top:0">为什么是豆油？两条相反的经济机制</h3>
<table>
<thead><tr><th style="width:20%">机制</th><th>逻辑</th><th>预测</th><th>实证</th></tr></thead>
<tbody>
<tr><td><b>成本端</b>（所有农产品共有）</td><td>柴油→农机作业、化肥（天然气制氮肥）、农药、物流 → 抬升<b>种植成本</b>与"成本底"</td><td>各农产品相关应大致相当</td><td><span class="tag tag-r">不成立</span>谷物仅 0.13–0.17</td></tr>
<tr><td><b>需求端</b>（仅油脂/玉米有）</td><td>豆油→生物柴油原料；玉米→乙醇。能源价格高 → 生物燃料掺混经济性改善 → 抬高原料需求</td><td>油脂/玉米相关应显著更高</td><td><span class="tag tag-g">部分成立</span>豆油 0.318 ✓；玉米 0.125 ✗</td></tr>
</tbody></table>
<p class="note" style="margin-top:10px">玉米×汽油（乙醇通道）仅 0.106，比豆油×柴油弱得多——说明<b>生物柴油通道（油脂）</b>比<b>乙醇通道（谷物）</b>在美国市场更活跃。这可能与美国生物柴油/RD 产能扩张、以及豆油同时受食用与能源双重需求有关；乙醇则因玉米长期供给宽松而钝化。</p>
</div>
<div class="card" style="padding:14px 20px">
<h3 style="margin-top:0">裂解价差检验（柴油相对原油的强弱）</h3>
<table>
<thead><tr><th>裂解价差 × </th><th class="num">玉米</th><th class="num">大豆</th><th class="num">小麦</th><th class="num">豆油</th></tr></thead>
<tbody id="tb_crack"></tbody>
</table>
<p class="note" style="margin-top:8px">裂解价差（HO − CL÷42）与农产品的相关性整体很弱（0.039–0.133），小麦甚至不显著。<b>含义：</b>农产品跟踪的是<b>原油/能源的绝对价格水平</b>（通过成本与通胀预期），而不是"炼油利润"这个更窄的变量。用裂解价差解释粮价是找错了变量。</p>
</div>
</div>

<h2 id="s4">四、第三层：回应"农业季节性"的疑问</h2>
<div class="card">
<p class="small">你的判断是：农业有季节性（有些月份耗柴油多），所以 60 日滚动相关可能不合适。我们把它拆成三条独立证据来检验。</p>

<h3>证据 1：柴油需求的季节性其实很弱</h3>
<div id="c_seas" class="chart"></div>
<p class="small" style="margin-top:8px">EIA 美国<b>馏分油产品供应</b>（WGFUPUS2，1995–2026 周度→月度）季节指数：峰 8 月 = 104，谷 1 月 = 94，<b>峰谷差仅 9.2%</b>。美国馏分油以公路货运/工业/农业为主，取暖油占比很小，因此<b>明显不同于取暖油的强冬季季节性</b>。"有些月份很耗柴油"在总需求层面并不显著。</p>

<h3>证据 2：农产品的价格季节性很明显，但与柴油相位错配</h3>
<table>
<thead><tr><th>月份</th><th class="num">1</th><th class="num">2</th><th class="num">3</th><th class="num">4</th><th class="num">5</th><th class="num">6</th><th class="num">7</th><th class="num">8</th><th class="num">9</th><th class="num">10</th><th class="num">11</th><th class="num">12</th><th class="num">年幅</th></tr></thead>
<tbody id="tb_mo"></tbody>
</table>
<p class="note" style="margin-top:8px">单位：月度对数收益的多年均值（%）。<b>6 月是农产品集体的最弱月</b>（玉米 −3.89%、大豆 −3.78%、小麦 −3.90%）——典型的"南美收割 + 北美天气市未启动"季节性；而同月柴油却是全年最强（+2.66%）。<b>两者相位相反</b>，季节性不仅不能增强相关性，反而在中和它。</p>

<h3>证据 3：把季节性剥离后，相关性几乎不变</h3>
<div class="grid2">
  <div><div id="c_deseason" class="chart chart-sm"></div></div>
  <div>
    <table>
      <thead><tr><th>品种</th><th class="num">原始 r</th><th class="num">去季节 r</th><th class="num">Δ</th></tr></thead>
      <tbody id="tb_ds"></tbody>
    </table>
    <table style="margin-top:12px">
      <thead><tr><th>分季节（原始日收益 r）</th><th class="num">春(播种)</th><th class="num">夏(生长)</th><th class="num">秋(收获)</th><th class="num">冬(淡季)</th></tr></thead>
      <tbody id="tb_seas"></tbody>
    </table>
    <div class="no" style="margin-top:12px"><b>结论（与你直觉相反）：</b>季节性剥离前后 Δ 仅 +0.001~+0.002，分季节相关也高度稳定（豆油常年 0.30–0.35，玉米 0.10–0.16）。<b>农业季节性是真实存在的，但它不是农产品×柴油相关性的主要扰动源。</b>用"季节性"作为放弃滚动相关的理由，实证上站不住。</div>
  </div>
</div>
</div>

<h2 id="s5">五、第四层：60 日窗口到底合不合适？</h2>
<div class="card">
<div id="c_roll" class="chart"></div>
<p class="small" style="margin-top:8px">4 条品种的 60 日滚动相关曲线。直观可见：<b>它是一条反复穿越 0 轴、在 −0.3 ~ +0.7 之间游走的曲线</b>。任一单一时点的读数都不可靠。</p>
<table style="margin-top:12px">
<thead><tr><th>品种</th><th class="num">均值</th><th class="num">区间</th><th class="num">正值占比</th><th class="num">|r|&gt;0.3 占比</th><th>读数</th></tr></thead>
<tbody id="tb_roll"></tbody>
</table>
<h3>窗口敏感性：短窗口的噪声有多大</h3>
<div id="c_win" class="chart chart-sm"></div>
<table style="margin-top:12px">
<thead><tr><th>窗口</th><th class="num">20 日</th><th class="num">30 日</th><th class="num">60 日</th><th class="num">120 日</th><th class="num">250 日</th></tr></thead>
<tbody id="tb_win"></tbody>
</table>
<p class="note" style="margin-top:8px">表中为各品种滚动相关的<b>标准差</b>（波动度）。20 日窗口的 σ = 0.23–0.25，意味着单点观测的 95% 置信区间宽达 ±0.5，几乎无法区分"正相关"与"无关系"——这正是项目内 2026-08-23 结论"13 日口径被实证否定"的同一机制。</p>
<div class="warn" style="margin-top:12px"><b>结论：</b>60 日窗口不是一个"错误的"选择，它是<b>噪声与分辨率的折中</b>：比 30 日噪声小约 30%，同时保留时变信息。真正的问题不在窗口长度，而在<b>用一条滚动曲线上的某个点去下结论</b>。正确做法是"分阶段 + 分品种"，而不是纠结 30 还是 60。</div>
</div>

<h2 id="s6">六、第五层：真正的驱动是结构断裂</h2>
<div class="card">
<div id="c_phase" class="chart"></div>
<table style="margin-top:12px">
<thead><tr><th>品种</th><th class="num">P1 高油价<br>2011-09~2014-06</th><th class="num">P2 油价崩塌<br>2014-07~2016-12</th><th class="num">P3 低波动<br>2017-01~2019-12</th><th class="num">P4 疫情<br>2020</th><th class="num">P5 通胀+俄乌<br>2021~2022</th><th class="num">P6 后危机<br>2023~2026</th></tr></thead>
<tbody id="tb_phase"></tbody>
</table>
<p class="note" style="margin-top:8px">日收益相关系数；<span class="tag tag-r">ns</span> 表示不显著。小麦自 2017-11 起，故 P1/P2 无样本。</p>
<div class="ok" style="margin-top:12px"><b>这是全篇最重要的发现：</b>农产品×柴油的相关性<b>不是稳定结构，而是随宏观环境跳变</b>。平静期趋近于 0（玉米 P1 −0.009<sup>ns</sup>、大豆 P3 +0.053<sup>ns</sup>），危机期飙升 2–4 倍（疫情期玉米 0.279、大豆 0.319、豆油 0.487）。<b>相关性本身是被"能源/通胀因子"激活的</b>——当宏观因子主导市场时，农产品被迫与能源同涨同跌；当基本面（天气、库存、出口）主导时，两者脱钩。</div>
<div class="card" style="margin-top:14px; padding:14px 20px">
<h3 style="margin-top:0">当前处于哪个状态（P6，2023-01 至 2026-09）</h3>
<table>
<thead><tr><th>品种</th><th class="num">P6 相关</th><th class="num">P5 相关</th><th>变化</th></tr></thead>
<tbody id="tb_p6"></tbody>
</table>
<p class="note" style="margin-top:8px">后危机期相关整体回落，但<b>豆油反而走高（0.339 vs P5 0.321）</b>且显著性强，反映 2023 年以来生物柴油/RD 政策与豆油能源属性的持续强化；玉米则明显衰减（0.073<sup>*</sup>），接近噪声区间。这与项目内 57/58 号"农业与化肥链脱钩监测"是同一叙事的两面。</p>
</div>
</div>

<h2 id="s7">七、第六层：同步，而不是成本滞后传导</h2>
<div class="card">
<div id="c_lag" class="chart"></div>
<p class="small" style="margin-top:8px">交叉相关（横轴 &gt;0 = 柴油领先农产品）。<b>四条曲线的峰值全部落在 lag = 0</b>。</p>
<div class="no" style="margin-top:12px"><b>这否定了"成本传导"叙事。</b>如果农产品跟柴油是"柴油涨→秋收/春耕成本上升→粮价上抬"，峰值应出现在柴油领先 1–6 个月的位置。实证是同步，意味着两者被同一个上游因子（原油价格 / 通胀预期 / 美元）同时驱动——<b>是"共同因子"而非"传导链"</b>。实务含义：不能把柴油当农产品的领先指标使用。</div>
</div>

<h2 id="s8">八、结论：这类问题应该怎么分析</h2>
<div class="card">
<table>
<thead><tr><th style="width:26%">维度</th><th>不推荐</th><th>推荐（本报告口径）</th></tr></thead>
<tbody>
<tr><td>价格口径</td><td>水平价格相关（0.6–0.76 的假象）</td><td><b>日对数收益 ×100</b>（0.13–0.32 的真值）</td></tr>
<tr><td>时间维度</td><td>单一滚动窗口的某一点读数</td><td><b>分阶段</b>（6 段宏观期）+ <b>全期</b>双报告</td></tr>
<tr><td>横截面</td><td>把"农产品"当同质整体</td><td><b>分品种</b>：油脂（豆油）与谷物（玉米/小麦）分开</td></tr>
<tr><td>季节性</td><td>担心季节性扭曲相关性</td><td>季节性影响可忽略（Δ≈0）；但需知道<b>价格季节性存在且相位错配</b></td></tr>
<tr><td>窗口长度</td><td>20/30 日（噪声主导，σ≥0.23）</td><td><b>60 日主口径</b>，120/250 日作结构参考</td></tr>
<tr><td>因果方向</td><td>把柴油当领先指标</td><td>视作<b>同步共同因子</b>，不用于择时</td></tr>
</tbody></table>

<h3>对"农产品 × 柴油"的最终判断</h3>
<ul class="tight">
<li><b>相关性确实存在，但强度被普遍高估。</b>真实日度相关：豆油 0.32、大豆 0.17、小麦 0.14、玉米 0.13（全期），均显著但属"弱到中等"。</li>
<li><b>结构上是"能源系"与"农业系"的重叠带。</b>越靠近能源需求端的品种（油脂）联动越强，越靠近纯供给驱动的品种（小麦）联动越弱。<b>豆油是唯一具备完整双通道（成本+需求）的品种</b>。</li>
<li><b>不构成可交易关系。</b>日收益 r≈0.13–0.32 意味着 R² 仅 1.6%–10%——柴油只能解释农产品日波动的极小部分，不构成可用的对冲或跟踪关系。</li>
<li><b>真正的使用场景是"因子识别"而非"价格预测"：</b>当宏观能源/通胀因子升温（如 2020、2022），农产品会被动跟随能源；识别到这一状态，可以作为<b>风险叠加</b>的提示（农产品多头在能源冲击期面临额外波动），而不是作为方向信号。</li>
</ul>
</div>

<h2 id="s9">九、数据来源、局限与后续</h2>
<div class="card">
<h3 style="margin-top:0">数据来源</h3>
<ul class="tight small">
<li>期货主连日线：富途行情接口（NYMEX/CME 主连），2011-09 ~ 2026-09-09。品种：HO（取暖油/ULSD，柴油基准）、CL（WTI 原油）、RB（RBOB 汽油）、ZC（玉米）、ZS（大豆）、ZW（CBOT 小麦）、ZL（豆油）。</li>
<li>实物需求：EIA WGFUPUS2（美国馏分油产品供应，周度，1991-02 ~ 2026-08）。</li>
<li>统计：Pearson / Spearman 双报，t 检验显著性；滚动相关为 60 日窗口日收益相关。</li>
</ul>
<h3>局限（须明确）</h3>
<ul class="tight small">
<li><b>主连拼接问题：</b>期货主连存在换月跳空，虽经平滑但仍可能引入微量噪声；日收益口径已大幅降低其影响。</li>
<li><b>小麦样本缺口：</b>富途小麦主连仅自 2017-11 起（n=2,220），P1/P2 阶段无法覆盖，其全期相关与谷物组的可比性弱于玉米/大豆。</li>
<li><b>柴油代理：</b>使用 NYMEX 取暖油（HO）期货作为美国柴油定价基准。HO 与 ULSD 高度同向但存在取暖季结构性差异；若需绝对精确，应改用 ULSD（HO 是公开可得的连续序列代理）。</li>
<li><b>未做的检验：</b>未纳入美元指数、CRB、通胀预期（T10YIE）做偏相关/控制变量回归，因此"共同因子"结论属于<b>排除法推断</b>（由 lag=0 + 原油强相关推出），而非因子模型的直接验证。<span class="tag tag-o">若需强化，下一步可做：控制 CL 后的偏相关</span>。</li>
</ul>
<div class="disclaimer">本文为量化统计研究，所有结论基于历史数据的相关性描述，不构成因果断言或投资建议。相关系数不代表可交易关系。</div>
</div>

<div class="foot">
  数据截至 2026-09-09 ｜ 生成脚本 scripts/agri_diesel_corr_20260910.py、scripts/agri_diesel_seasonality_20260910.py、scripts/build_agri_diesel_report_20260910.py ｜ 结果文件 results/agri_diesel_corr_20260910.json
</div>

</div>

<script>
const COL = {blue:'#0072B2', orange:'#E69F00', sky:'#56B4E9', purple:'#CC79A7', vermil:'#D55E00', green:'#009E73', grey:'#7a736a', black:'#26313d'};
const FONT = {fontFamily:'Microsoft YaHei, PingFang SC, sans-serif'};
const AX = {axisLine:{lineStyle:{color:'#c8c3b8'}}, axisLabel:{color:'#5b6672', fontSize:11},
            splitLine:{lineStyle:{color:'#eeebe4'}}};
const TIP = {trigger:'axis', backgroundColor:'#fff', borderColor:'#e3e0d8', textStyle:{color:'#26313d',fontSize:12},
             extraCssText:'box-shadow:0 4px 14px rgba(0,0,0,.08);border-radius:6px;'};
const SUM = {type:'summary', backgroundColor:'#fff', borderColor:'#e3e0d8', textStyle:{color:'#26313d',fontSize:12},
             extraCssText:'box-shadow:0 4px 14px rgba(0,0,0,.08);border-radius:6px;'};

/* ---------- 图1 水平 vs 收益 ---------- */
(function(){
  const items = __LVL_LABELS__;
  const lv = __LVL_VALUES__, rt = __RET_VALUES__;
  const ch = echarts.init(document.getElementById('c_lvl'));
  ch.setOption(Object.assign({}, FONT, {
    tooltip: Object.assign({}, SUM, {formatter: p => p.map(x=>`${x.seriesName}<br>${x.name}: <b>${x.value.toFixed(3)}</b>`).join('<br>')}),
    legend:{data:['水平价格 r','日收益 r'], top:0, textStyle:{fontSize:12}},
    grid:{left:46, right:20, top:44, bottom:56},
    xAxis:Object.assign({type:'category', data:items, axisLabel:{color:'#5b6672', fontSize:12, interval:0}}, {axisLine:AX.axisLine}),
    yAxis:Object.assign({type:'value', min:0, max:1, name:'Pearson r'}, AX),
    series:[
      {name:'水平价格 r', type:'bar', data:lv, itemStyle:{color:COL.sky}, barGap:'12%',
       label:{show:true, position:'top', fontSize:11, color:'#5b6672', formatter:p=>p.value.toFixed(3)}},
      {name:'日收益 r', type:'bar', data:rt, itemStyle:{color:COL.vermil},
       label:{show:true, position:'top', fontSize:11, color:'#a8410a', fontWeight:'bold', formatter:p=>p.value.toFixed(3)}}
    ]
  }));
})();

/* ---------- 图2 通道分解 ---------- */
(function(){
  const d = __CHAN__;
  const ch = echarts.init(document.getElementById('c_chan'));
  ch.setOption(Object.assign({}, FONT, {
    tooltip:Object.assign({}, TIP, {trigger:'item'}),
    grid:{left:96, right:56, top:10, bottom:24},
    xAxis:Object.assign({type:'value', min:0, max:0.85, name:'日收益 r'}, AX),
    yAxis:Object.assign({type:'category', data:d.names}, AX),
    series:[{type:'bar', data:d.values, itemStyle:{color:function(p){return d.colors[p.dataIndex];}},
      label:{show:true, position:'right', fontSize:11, formatter:p=>p.value.toFixed(3), color:'#26313d'}}]
  }));
})();

/* ---------- 图3 季节性 ---------- */
(function(){
  const eia=__EIA__, eia5=__EIA5__, fm=__FMR__;
  const mon=['1','2','3','4','5','6','7','8','9','10','11','12'];
  const ch=echarts.init(document.getElementById('c_seas'));
  ch.setOption(Object.assign({}, FONT, {
    tooltip:Object.assign({}, TIP, {formatter:function(ps){
      let s=`<b>${ps[0].name}月</b>`;
      ps.forEach(p=>{ s+=`<br>${p.marker}${p.seriesName}: <b>${p.value}</b>`;});
      return s;}}),
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:52, right:56, top:40, bottom:34},
    xAxis:Object.assign({type:'category', data:mon, name:'月份', axisLabel:{color:'#5b6672', fontSize:12}}, {axisLine:AX.axisLine}),
    yAxis:[
      Object.assign({type:'value', min:88, max:108, name:'需求季节指数', nameTextStyle:{fontSize:11}}, AX),
      Object.assign({type:'value', min:-6, max:6, name:'月均收益 %', position:'right', nameTextStyle:{fontSize:11}}, AX)
    ],
    series:[
      {name:'馏分油需求季节指数(1995+)', type:'bar', data:eia, itemStyle:{color:COL.sky}, barWidth:'46%',
       markLine:{silent:true, symbol:'none', lineStyle:{type:'dashed', color:COL.grey},
         data:[{yAxis:100, label:{formatter:'均值=100', fontSize:10, color:'#7a736a'}}]}},
      {name:'玉米 月均收益', type:'line', yAxisIndex:1, data:fm.ZC, itemStyle:{color:COL.orange}, lineStyle:{width:2}, symbol:'circle', symbolSize:5},
      {name:'小麦 月均收益', type:'line', yAxisIndex:1, data:fm.ZW, itemStyle:{color:COL.vermil}, lineStyle:{width:2, type:'dashed'}, symbol:'triangle', symbolSize:6},
      {name:'柴油(HO) 月均收益', type:'line', yAxisIndex:1, data:fm.HO, itemStyle:{color:COL.blue}, lineStyle:{width:2.6}, symbol:'rect', symbolSize:6,
       markLine:{silent:true, symbol:'none', lineStyle:{type:'dotted', color:COL.blue, opacity:.4}, data:[{yAxis:0}]}}
    ]
  }));
})();

/* ---------- 图4 去季节 ---------- */
(function(){
  const d=__DS__;
  const ch=echarts.init(document.getElementById('c_deseason'));
  ch.setOption(Object.assign({}, FONT, {
    tooltip:Object.assign({}, SUM, {formatter:p=>p.map(x=>`${x.seriesName}<br>${x.name}: <b>${x.value.toFixed(3)}</b>`).join('<br>')}),
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:46, right:16, top:40, bottom:34},
    xAxis:Object.assign({type:'category', data:d.labels, axisLabel:{color:'#5b6672', fontSize:12}}, {axisLine:AX.axisLine}),
    yAxis:Object.assign({type:'value', min:0, max:0.4, name:'r'}, AX),
    series:[
      {name:'原始', type:'bar', data:d.raw, itemStyle:{color:COL.sky}, barGap:'10%', label:{show:true, position:'top', fontSize:10.5, formatter:p=>p.value.toFixed(3)}},
      {name:'去季节性', type:'bar', data:d.ds, itemStyle:{color:COL.purple}, label:{show:true, position:'top', fontSize:10.5, formatter:p=>p.value.toFixed(3)}}
    ]
  }));
})();

/* ---------- 图5 60日滚动 ---------- */
(function(){
  const r=__ROLL__;
  const ch=echarts.init(document.getElementById('c_roll'));
  const series=[
    {name:'玉米', key:'ZC', color:COL.orange, sym:'circle', type:'solid'},
    {name:'大豆', key:'ZS', color:COL.purple, sym:'triangle', type:'dashed'},
    {name:'小麦', key:'ZW', color:COL.vermil, sym:'rect', type:'dotted'},
    {name:'豆油', key:'ZL', color:COL.blue, sym:'diamond', type:'solid'}
  ].map(s=>({name:s.name, type:'line', data:r[s.key], showSymbol:false, smooth:true,
             lineStyle:{width:2, color:s.color, type:s.type},
             itemStyle:{color:s.color}, emphasis:{focus:'series'}}));
  ch.setOption(Object.assign({}, FONT, {
    tooltip:Object.assign({}, TIP, {valueFormatter:v=>v==null?'—':(+v).toFixed(3)}),
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:50, right:20, top:40, bottom:34},
    xAxis:Object.assign({type:'category', data:r.dates, axisLabel:{color:'#5b6672', fontSize:11, hideOverlap:true}}, {axisLine:AX.axisLine}),
    yAxis:Object.assign({type:'value', min:-0.4, max:0.8, name:'60日滚动 r'}, AX),
    series:series,
    graphic:[{type:'line', left:50, right:20, top:'50%', shape:{x1:0,y1:0,x2:1,y2:0},
      style:{stroke:'#b8b2a7', lineWidth:1, lineDash:[4,4]}, silent:true}]
  }));
})();

/* ---------- 图6 窗口敏感性 ---------- */
(function(){
  const d=__WIN__;
  const ch=echarts.init(document.getElementById('c_win'));
  const series=[['玉米','ZC',COL.orange,'circle'],['大豆','ZS',COL.purple,'triangle'],['小麦','ZW',COL.vermil,'rect'],['豆油','ZL',COL.blue,'diamond']]
    .map(([n,k,c,s])=>({name:n, type:'line', data:d.windows.map(w=>d.data[k][w]),
      itemStyle:{color:c}, lineStyle:{width:2.2, color:c}, symbol:s, symbolSize:7,
      label:{show:true, fontSize:10, color:'#5b6672'}}));
  ch.setOption(Object.assign({}, FONT, {
    tooltip:Object.assign({}, TIP),
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:50, right:20, top:40, bottom:40},
    xAxis:Object.assign({type:'category', data:d.windows.map(w=>w+'日'), name:'滚动窗口'}, AX),
    yAxis:Object.assign({type:'value', name:'滚动相关 σ', min:0, max:0.28}, AX),
    series:series
  }));
})();

/* ---------- 图7 分阶段 ---------- */
(function(){
  const d=__PHASE__;
  const ch=echarts.init(document.getElementById('c_phase'));
  const series=d.series.map((s,i)=>({name:s.name, type:'bar', data:s.data,
    itemStyle:{color:s.color}, barGap:'8%',
    label:{show:true, position:'top', fontSize:9.5, color:'#5b6672',
      formatter:p=>(p.value==null?'':p.value.toFixed(2)+(s.ns[p.dataIndex]?'ⁿˢ':'')), overflow:'none'}}));
  ch.setOption(Object.assign({}, FONT, {
    tooltip:Object.assign({}, SUM),
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:50, right:20, top:44, bottom:62},
    xAxis:Object.assign({type:'category', data:d.phases, axisLabel:{color:'#5b6672', fontSize:11, interval:0, width:100, overflow:'break'}}, {axisLine:AX.axisLine}),
    yAxis:Object.assign({type:'value', name:'日收益 r', min:-0.05, max:0.55}, AX),
    series:series
  }));
})();

/* ---------- 图8 领先滞后 ---------- */
(function(){
  const d=__LAG__;
  const ch=echarts.init(document.getElementById('c_lag'));
  const series=[['玉米','ZC',COL.orange,'circle','solid'],['大豆','ZS',COL.purple,'triangle','dashed'],
                ['小麦','ZW',COL.vermil,'rect','dotted'],['豆油','ZL',COL.blue,'diamond','solid']]
    .map(([n,k,c,s,t])=>({name:n, type:'line', data:d.lags.map(l=>d.data[k][l]),
      itemStyle:{color:c}, lineStyle:{width:2.1, color:c, type:t}, symbol:s, symbolSize:6}));
  ch.setOption(Object.assign({}, FONT, {
    tooltip:Object.assign({}, TIP, {formatter:function(ps){
      let s=`lag = <b>${ps[0].name}</b> 日<br><span style="font-size:11.5px;color:#7a736a">${(+ps[0].name)>0?'柴油领先':'农产品领先'}</span>`;
      ps.forEach(p=>{s+=`<br>${p.marker}${p.seriesName}: <b>${(+p.value).toFixed(3)}</b>`;});return s;}}),
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:52, right:20, top:40, bottom:40},
    xAxis:Object.assign({type:'category', data:d.lags, name:'lag (日)'}, AX),
    yAxis:Object.assign({type:'value', name:'交叉相关 r', min:-0.05, max:0.35}, AX),
    series:series,
    graphic:[{type:'line', left:52, right:20, top:40, bottom:40, shape:{x1:0,y1:0,x2:0,y2:1},
      style:{stroke:'#b8b2a7', lineWidth:1.2, lineDash:[4,4]}, silent:true},
      {type:'text', left:'center', bottom:12, style:{text:'← 农产品领先   |   柴油领先 →', fill:'#7a736a', fontSize:11}}]
  }));
})();

window.addEventListener('resize',()=>{document.querySelectorAll('.chart,.chart-sm').forEach(e=>{
  const i=echarts.getInstanceByDom(e); if(i) i.resize();});});
</script>
</body>
</html>
"""

# ---------- 表格行生成 ----------
def tr_lvl():
    rows = ""
    for a in ["ZC", "ZS", "ZW", "ZL", "CL", "RB"]:
        lv = LV[a]; rt = RT[a]
        decay = (rt["r"] - lv["r"]) / abs(lv["r"]) * 100
        star = {True: "***"}.get(rt["p"] < 0.001, "") + ("" if rt["p"] < 0.001 else ("**" if rt["p"] < 0.01 else ("*" if rt["p"] < 0.05 else " ns")))
        note = {"ZC": "谷物 · 需求端通道弱", "ZS": "油籽 · 双通道", "ZW": "纯供给驱动 · 仅成本端", "ZL": "油脂 · 生物柴油通道最强", "CL": "能源内部基准", "RB": "能源内部基准"}[a]
        rows += (f'<tr><td><b>{LBL[a]}</b></td><td class="num">{lv["r"]:.3f}</td>'
                 f'<td class="num" style="color:#C0392B;font-weight:700">{rt["r"]:.3f}</td>'
                 f'<td class="num">{decay:.0f}%</td><td class="num">{rt["spearman"]:.3f}</td>'
                 f'<td>{star}</td><td class="note">{note}</td></tr>')
    return rows

def tr_chan():
    order = [("HO-CL", "柴油 × 原油 — 能源内部标尺"), ("ZL-HO", "豆油 × 柴油 — 生物柴油通道"),
             ("ZS-HO", "大豆 × 柴油"), ("ZW-HO", "小麦 × 柴油"), ("ZC-RB", "玉米 × 汽油 — 乙醇通道")]
    rows = ""
    for k, desc in order:
        g = G[k]
        s = "***" if g["p"] < 0.001 else ("**" if g["p"] < 0.01 else ("*" if g["p"] < 0.05 else "ns"))
        tag = 'tag-r' if k in ("HO-CL",) else ('tag-g' if k in ("ZL-HO",) else ('tag-o' if k in ("ZS-HO", "ZW-HO") else 'tag-b'))
        rows += (f'<tr><td><b>{k.replace("-"," × ")}</b></td><td class="num" style="font-weight:700">{g["ret_r"]:.3f}</td>'
                 f'<td class="note">{desc}</td></tr>')
    return rows

def tr_crack():
    c = G["crack"]
    return "".join(f'<td class="num">{c[a]["ret_r"]:.3f}{"ⁿˢ" if c[a]["p"]>=0.05 else ""}</td>' for a in AG)

def tr_mo():
    rows_html = ""
    order = [("HO", "柴油(HO)"), ("ZC", "玉米"), ("ZS", "大豆"), ("ZW", "小麦"), ("ZL", "豆油"), ("CL", "原油(WTI)")]
    for k, name in order:
        d = fmr[k]
        amp = max(d.values()) - min(d.values())
        tds = ""
        for m in range(1, 13):
            v = d[str(m)]
            cls = ' style="color:#C0392B;font-weight:600"' if v > 1.5 else (' style="color:#1E8449;font-weight:600"' if v < -1.5 else '')
            tds += f'<td class="num"{cls}>{v:+.2f}</td>'
        rows_html += f'<tr><td><b>{name}</b></td>{tds}<td class="num">{amp:.2f}%</td></tr>'
    return rows_html

def tr_ds():
    rows = ""
    for a in AG:
        x = D["deseasonalized"][a]
        rows += (f'<tr><td><b>{LBL[a]}</b></td><td class="num">{x["raw"]["r"]:.3f}</td>'
                 f'<td class="num">{x["deseason"]["r"]:.3f}</td>'
                 f'<td class="num" style="color:#9a6400;font-weight:700">+{x["delta"]:.3f}</td></tr>')
    return rows

def tr_seas():
    rows = ""
    for a in AG:
        d = D["by_season"][a]
        tds = ""
        for sz in ["春季(播种)", "夏季(生长)", "秋季(收获)", "冬季(淡季)"]:
            v = d.get(sz)
            if not v:
                tds += '<td class="num">—</td>'
                continue
            st = "***" if v["p"] < 0.001 else ("**" if v["p"] < 0.01 else ("*" if v["p"] < 0.05 else "ⁿˢ"))
            tds += f'<td class="num">{v["r"]:.3f}{"" if st=="ⁿˢ" else st}</td>'
        rows += f'<tr><td><b>{LBL[a]}</b></td>{tds}</tr>'
    return rows

def tr_roll():
    rows = ""
    for a in AG:
        b = B[a]
        rows += (f'<tr><td><b>{LBL[a]}</b></td><td class="num">{b["mean"]:+.3f}</td>'
                 f'<td class="num">[{b["min"]:+.2f}, {b["max"]:+.2f}]</td>'
                 f'<td class="num">{b["share_positive"]*100:.0f}%</td>'
                 f'<td class="num">{b["share_sig_like"]*100:.0f}%</td>'
                 f'<td class="note">{"稳定偏正、振幅最小" if a=="ZL" else "反复穿越 0 轴、单点读数不可靠"}</td></tr>')
    return rows

def tr_win():
    rows = ""
    for a in AG:
        tds = ""
        for w in ["20", "30", "60", "120", "250"]:
            v = C[a][w]["std"]
            hl = ' style="background:#fdf3e0;font-weight:700"' if w == "60" else ''
            tds += f'<td class="num"{hl}>{v:.3f}</td>'
        rows += f'<tr><td><b>{LBL[a]}</b></td>{tds}</tr>'
    return rows

def tr_phase():
    names = [p[0] for p in PHASES_LIST]
    rows = ""
    for a in AG:
        tds = ""
        for nm in names:
            k = [x for x in E[a] if x.startswith(nm.split()[0])]
            if not k:
                tds += '<td class="num">—</td>'
                continue
            v = E[a][k[0]]
            st = "***" if v["ret_p"] < 0.001 else ("**" if v["ret_p"] < 0.01 else ("*" if v["ret_p"] < 0.05 else "ⁿˢ"))
            tds += f'<td class="num">{v["ret_r"]:.3f}<span style="font-size:10px;color:#9a948a">{st}</span></td>'
        rows += f'<tr><td><b>{LBL[a]}</b></td>{tds}</tr>'
    return rows

def tr_p6():
    rows = ""
    for a in AG:
        p6k = [x for x in E[a] if x.startswith("P6")]
        p5k = [x for x in E[a] if x.startswith("P5")]
        if not p6k:
            continue
        r6 = E[a][p6k[0]]["ret_r"]; p6p = E[a][p6k[0]]["ret_p"]
        r5 = E[a][p5k[0]]["ret_r"] if p5k else None
        st = "***" if p6p < 0.001 else ("**" if p6p < 0.01 else ("*" if p6p < 0.05 else " ns"))
        chg = "" if r5 is None else (f'<span style="color:#C0392B">↑ {r6-r5:+.3f}</span>' if r6 > r5 else f'<span style="color:#1E8449">↓ {r6-r5:+.3f}</span>')
        rows += (f'<tr><td><b>{LBL[a]}</b></td><td class="num">{r6:.3f}<span style="font-size:10px;color:#9a948a">{st}</span></td>'
                 f'<td class="num">{"" if r5 is None else f"{r5:.3f}"}</td><td>{chg}</td></tr>')
    return rows

PHASES_LIST = [("P1", "2011-09-01", "2014-06-30"), ("P2", "2014-07-01", "2016-12-31"),
               ("P3", "2017-01-01", "2019-12-31"), ("P4", "2020-01-01", "2020-12-31"),
               ("P5", "2021-01-01", "2022-12-31"), ("P6", "2023-01-01", "2026-12-31")]

# ---------- 图表数据 ----------
chan_names = ["柴油 × 原油", "豆油 × 柴油", "大豆 × 柴油", "小麦 × 柴油", "玉米 × 汽油"]
chan_vals = [G["HO-CL"]["ret_r"], G["ZL-HO"]["ret_r"], G["ZS-HO"]["ret_r"], G["ZW-HO"]["ret_r"], G["ZC-RB"]["ret_r"]]
chan_colors = ["#0072B2", "#009E73", "#CC79A7", "#D55E00", "#E69F00"]

lvl_labels = [LBL[a] for a in ["ZC", "ZS", "ZW", "ZL", "CL", "RB"]]
lvl_values = [LV[a]["r"] for a in ["ZC", "ZS", "ZW", "ZL", "CL", "RB"]]
ret_values = [RT[a]["r"] for a in ["ZC", "ZS", "ZW", "ZL", "CL", "RB"]]

ds_data = {"labels": [LBL[a] for a in AG],
           "raw": [D["deseasonalized"][a]["raw"]["r"] for a in AG],
           "ds": [D["deseasonalized"][a]["deseason"]["r"] for a in AG]}

win_data = {"windows": [20, 30, 60, 120, 250],
            "data": {a: {str(w): C[a][str(w)]["std"] for w in [20, 30, 60, 120, 250]} for a in AG}}

phase_names = ["P1 高油价末期", "P2 油价崩塌", "P3 低波动期", "P4 疫情冲击", "P5 通胀+俄乌双危机", "P6 后危机期"]
phase_series = []
pc = {"ZC": "#E69F00", "ZS": "#CC79A7", "ZW": "#D55E00", "ZL": "#0072B2"}
for a in AG:
    data, ns = [], []
    for nm in phase_names:
        key = [x for x in E[a] if x.startswith(nm.split()[0])]
        if key:
            data.append(E[a][key[0]]["ret_r"])
            ns.append(E[a][key[0]]["ret_p"] >= 0.05)
        else:
            data.append(None); ns.append(True)
    phase_series.append({"name": LBL[a], "data": data, "ns": ns, "color": pc[a]})
phase_data = {"phases": phase_names, "series": phase_series}

lags = list(range(-10, 11))
lag_data = {"lags": lags, "data": {a: [F[a][str(l)] for l in lags] for a in AG}}

# ---------- 注入 ----------
html = html.replace("__LVL_LABELS__", JA(lvl_labels))
html = html.replace("__LVL_VALUES__", JA(lvl_values))
html = html.replace("__RET_VALUES__", JA(ret_values))
html = html.replace("__CHAN__", JA({"names": chan_names, "values": chan_vals, "colors": chan_colors}))
html = html.replace("__EIA__", JA([eia_all[str(m)] for m in range(1, 13)]))
html = html.replace("__EIA5__", JA([eia_5y[str(m)] for m in range(1, 13)]))
html = html.replace("__FMR__", JA({k: [fmr[k][str(m)] for m in range(1, 13)] for k in fmr}))
html = html.replace("__DS__", JA(ds_data))
html = html.replace("__ROLL__", JA(roll))
html = html.replace("__WIN__", JA(win_data))
html = html.replace("__PHASE__", JA(phase_data))
html = html.replace("__LAG__", JA(lag_data))

# 表格 body 注入
html = html.replace('<tbody id="tb_lvl"></tbody>', '<tbody id="tb_lvl">' + tr_lvl() + '</tbody>')
html = html.replace('<tbody id="tb_chan"></tbody>', '<tbody id="tb_chan">' + tr_chan() + '</tbody>')
html = html.replace('<tbody id="tb_crack"></tbody>', '<tbody id="tb_crack">' + tr_crack() + '</tbody>')
html = html.replace('<tbody id="tb_mo"></tbody>', '<tbody id="tb_mo">' + tr_mo() + '</tbody>')
html = html.replace('<tbody id="tb_ds"></tbody>', '<tbody id="tb_ds">' + tr_ds() + '</tbody>')
html = html.replace('<tbody id="tb_seas"></tbody>', '<tbody id="tb_seas">' + tr_seas() + '</tbody>')
html = html.replace('<tbody id="tb_roll"></tbody>', '<tbody id="tb_roll">' + tr_roll() + '</tbody>')
html = html.replace('<tbody id="tb_win"></tbody>', '<tbody id="tb_win">' + tr_win() + '</tbody>')
html = html.replace('<tbody id="tb_phase"></tbody>', '<tbody id="tb_phase">' + tr_phase() + '</tbody>')
html = html.replace('<tbody id="tb_p6"></tbody>', '<tbody id="tb_p6">' + tr_p6() + '</tbody>')

fn = os.path.join(OUTDIR, "index.html")
with open(fn, "w", encoding="utf-8") as f:
    f.write(html)
print("WROTE", fn, os.path.getsize(fn), "bytes")
