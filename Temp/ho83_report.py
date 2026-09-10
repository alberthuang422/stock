# -*- coding: utf-8 -*-
"""生成 83 号报告 HTML"""
import json, io, os

T = r'C:/Users/Administrator/Desktop/stock/Temp'
OUT = r'C:/Users/Administrator/Desktop/stock/reports/83_HO月差与EIA库存解构'
os.makedirs(OUT, exist_ok=True)
D = json.load(open(T + '/ho83_data.json', encoding='utf-8'))

J = lambda k: json.dumps(D[k], ensure_ascii=False)

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>83 · HO 月差 × EIA 库存：为什么价格新高、月差却远低于前高</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{
  --bg:#f7f6f3; --card:#ffffff; --ink:#26313d; --sub:#5b6672; --line:#e3e0d8;
  --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --purple:#CC79A7;
  --vermil:#D55E00; --green:#009E73; --grey:#9a948a;
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
.chart{width:100%; height:400px;}
.chart-sm{height:340px;}
.chart-lg{height:470px;}
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
.up{color:var(--red); font-weight:700;}
.dn{color:var(--down); font-weight:700;}
.term{border-bottom:1px dotted var(--blue); color:var(--blue); cursor:help; position:relative;}
.term:hover::after{content:attr(data-tip); position:absolute; left:0; top:130%; z-index:99;
  background:#26313d; color:#fff; font-size:12.5px; line-height:1.6; padding:8px 12px; border-radius:6px;
  width:400px; box-shadow:0 4px 14px rgba(0,0,0,.25); text-align:left; font-weight:400;}
@media (max-width:900px){ .kpis{grid-template-columns:repeat(2,1fr);} .grid2{grid-template-columns:1fr;} .term:hover::after{width:260px;} }
</style>
</head>
<body>
<div class="wrap">

<div class="head">
  <h1>83 · HO 月差 × EIA 库存：为什么价格新高、月差却远低于前高</h1>
  <div class="meta">库存-价差结构研究 ｜ 报告日 2026-09-10 ｜ 价格/月差：TradingView 主连(HO1!、HO1!−HO2!) 2013-03~2026-09-10 ｜ 库存：EIA WPSR 周度（用户 psw01/psw06 原始表 1982-08~2026-08-21 + EIA v2 API 补 2026-08-28）</div>
  <div class="toc">
    <a href="#s0">摘要</a><a href="#s1">口径与数据</a><a href="#s2">库存事实</a><a href="#s3">核心矛盾</a>
    <a href="#s4">敏感度差异</a><a href="#s5">时点分解</a><a href="#s6">机制</a><a href="#s7">外部验证</a>
    <a href="#s8">结论与证伪</a><a href="#s9">局限</a>
  </div>
</div>

<h2 id="s0">摘要 · 结论先行</h2>
<div class="card concl">
<ol class="tight">
<li><b>库存确实在史低——但"价格新高"的原因和"月差低"的原因是两回事。</b>美国馏分油库存 2026-08-28 为 1.042 亿桶，是 <b>1982 年有数据以来 8 月同期最低</b>（低于 5 年同期均值 14%）；东海岸 PADD1 仅 1,932 万桶，<b>破 1990 年以来纪录</b>。价格新高有扎实的物理基础。</li>
<li><b>但月差不是库存的函数。</b>同一自变量（库存 5 年同期偏离）对两者的解释力差距 <b>近 3 倍</b>：价格 R²=<b>0.55</b>（r=−0.74），月差 R²=<b>0.19</b>（r=−0.44）。库存紧张主要被定价在<b>绝对价格 / 整条远期曲线</b>上，不在近次月价差。</li>
<li><b>最刺眼的反证：2026-03-20 库存偏离只有 −1.0%（完全正常）月差却飙到 0.4823；2026-08-28 库存偏离 −13.6%（史低）月差只有 0.1444。</b>库存紧张度差 14 倍，月差反方向差 3.3 倍。3 月的月差是<b>事件型近端恐慌溢价</b>，与库存无关。</li>
<li><b>同样库存水平，月差可以差 10 倍。</b>库存落在 10.0–10.6 百万桶区间时：2025 年月差中位 <b>0.014</b>、2023 年 <b>0.016</b>、2022 年 <b>0.177</b>、2026 年 <b>0.139</b>。按"5 年偏离 −15%~−10%"分桶，历史中位仅 <b>0.017</b>，而 2026-08 实际 <b>0.144</b>（8.5 倍）。<b>低库存 ≠ 正价差；2026 的月差相对其库存其实偏高，而非偏低。</b></li>
<li><b>"月差低"是相对 2026-03 和 2022 两次事件峰值而言的，不是相对基本面。</b>月差度量的是<span class="term" data-tip="近次月价差 = 近月相对次月的溢价，本质是边际稀缺租金：市场愿意为'现在就有货'多付多少。它是流量/加速度变量，不是存量/水位变量。">边际稀缺租金</span>（流速），价格度量的是<span class="term" data-tip="绝对价格水平包含了整条远期曲线对结构性缺口的定价；供需缺口若被预期为长期存在，会被'整条曲线一起抬高'，只体现为价格而非近端斜率。">绝对稀缺水位</span>。2026-03 是"急性冲击"（近端能不能拿到货），2026-09 是"结构性短缺被整条曲线定价"。</li>
<li><b>机制上有一层被忽略的事实：美国正在用自己的库存补贴全球。</b>馏分油出口 174–188 万桶/日，约占国内产量 <b>34%</b>、同比 +24~29%；炼厂开工率 <b>98%</b>（2018 年 8 月以来最高）但馏分油收率从 31.1% 降到 <b>29.3%</b>——加工更多原油、产出更少柴油。<b>库存被抽走的是"全球竞价"，不是美国需求。</b></li>
</ol>
</div>

<div class="kpis">
  <div class="kpi"><div class="t">美国馏分油库存（8/28）</div><b>104.2 <span style="font-size:13px">百万桶</span></b><div class="s">1982 年以来 8 月同期最低 ｜ 5 年偏离 <span class="dn">−13.6%</span></div></div>
  <div class="kpi"><div class="t">PADD1 东海岸库存（8/28）</div><b>19.3 <span style="font-size:13px">百万桶</span></b><div class="s">1990 年以来最低 ｜ 5 年偏离 <span class="dn">−41.0%</span></div></div>
  <div class="kpi"><div class="t">价格 vs 库存解释力</div><b>R² 0.55</b><div class="s">价格 ~ 库存偏离（r=−0.74）</div></div>
  <div class="kpi"><div class="t">月差 vs 库存解释力</div><b>R² 0.19</b><div class="s">月差 ~ 库存偏离（r=−0.44）</div></div>
</div>

<h2 id="s1">一、口径、数据与一处必须修正的旧结论</h2>
<div class="card">
<h3>1.1 两套价格口径，先排除"到期周失真"</h3>
<p class="small">项目内既有的 HO 月差数据集（CME/Barchart 逐合约，2000-2026）给出"全史最高 = 2022-04-28 $1.1270"，<b>该数字不可用</b>。核验：该日近月合约 HOK22 处于到期周，成交量 15,330 → 次日仅 1,478 手（正常 2–5 万手），2022-10-28 同样（12,404 → 1,197）。NYMEX 近月在到期前 2–3 个交易日报价完全失真，该数据集 Top 极值中 8 个属此类。</p>
<table style="margin-top:10px">
<thead><tr><th>口径</th><th class="num">2022 峰值</th><th class="num">2026 峰值</th><th>说明</th></tr></thead>
<tbody>
<tr><td>CME/Barchart 逐合约（旧）</td><td class="num">1.1270 <span class="note">(04-28)</span></td><td class="num">—</td><td class="note">到期周流动性失真，<b>作废</b></td></tr>
<tr><td><b>TradingView 主连（本次采用）</b></td><td class="num"><b>0.4014</b> <span class="note">(05-02)</span></td><td class="num"><b>0.4823</b> <span class="note">(03-20)</span></td><td class="note">连续主力，天然避开到期周；非到期窗口两口径逐日差 &lt;0.02</td></tr>
</tbody></table>
<div class="warn" style="margin-top:12px"><b>"前高月差"是 0.40–0.48，不是 1.13。</b>这个修正直接影响本轮判断：用 1.13 当基准会得出"现在只有 1/6、严重背离"的夸大结论。</div>

<h3>1.2 库存数据来源</h3>
<ul class="tight small">
<li><b>用户提供</b>：EIA WPSR 完整分表 <code>psw01.xls</code>（Petroleum Balance Sheet，Data 1 库存 19 系列 + Data 2 供应 37 系列）、<code>psw06.xls</code>（馏分油按 PADD 分区库存，69 系列），均为 2026-08-26 发布版（数据截至 2026-08-21）。</li>
<li><b>本报告补齐</b>：结构表只到 8/21，与价格（9/10）差 2.5 周。通过 EIA v2 API 补取 <b>2026-08-28</b> 周数据（WDISTUS1=104,187；WDISTP11=19,318；WD0ST_NUS_1=94,181）。WPSR 9/4 期在 API 尚未更新，最新可得为 8/28。</li>
<li><b>季节性口径</b>：所有"5 年偏离"= （当期 − 前 1~5 年同一日历周均值）/ 均值，至少 3 个观测，排除本年。分位基准 2015–2025 同日历周。</li>
</ul>
</div>

<h2 id="s2">二、库存事实：不是"不够紧"，而是史无前例地紧</h2>
<div class="card">
<div id="c_hist" class="chart chart-sm"></div>
<table style="margin-top:12px">
<thead><tr><th>库存口径</th><th class="num">2026-08-28</th><th class="num">同日历周历史均值</th><th class="num">同周历史最低</th><th class="num">季节分位</th><th>状态</th></tr></thead>
<tbody>
<tr><td>美国馏分油总库存</td><td class="num"><b>104,187</b></td><td class="num">132,583</td><td class="num">102,797</td><td class="num"><b>0.2%</b></td><td><span class="tag tag-r">史低区</span></td></tr>
<tr><td>美国 ULSD（0–15ppm）</td><td class="num"><b>94,181</b></td><td class="num">118,677</td><td class="num">93,525</td><td class="num"><b>0.2%</b></td><td><span class="tag tag-r">史低区</span></td></tr>
<tr><td>美国低硫 15–500ppm（取暖油品级）</td><td class="num">3,893</td><td class="num">4,426</td><td class="num">1,811</td><td class="num">53.1%</td><td><span class="tag tag-o">中性</span></td></tr>
<tr><td>PADD1 东海岸</td><td class="num"><b>19,318</b></td><td class="num">41,870</td><td class="num">20,966</td><td class="num"><b>0.2%</b></td><td><span class="tag tag-r">破纪录</span></td></tr>
<tr><td>PADD1A 新英格兰</td><td class="num"><b>2,419</b></td><td class="num">6,878</td><td class="num">2,703</td><td class="num"><b>0.0%</b></td><td><span class="tag tag-r">破纪录</span></td></tr>
<tr><td>PADD1B 中区（含纽约港）</td><td class="num"><b>10,373</b></td><td class="num">22,822</td><td class="num">8,479</td><td class="num"><b>1.4%</b></td><td><span class="tag tag-r">史低区</span></td></tr>
<tr><td>PADD1C 下大西洋</td><td class="num"><b>8,211</b></td><td class="num">12,170</td><td class="num">8,467</td><td class="num"><b>0.0%</b></td><td><span class="tag tag-r">破纪录</span></td></tr>
<tr><td>PADD2 中西部</td><td class="num">28,563</td><td class="num">30,339</td><td class="num">22,883</td><td class="num">31.0%</td><td><span class="tag tag-o">偏紧</span></td></tr>
<tr><td>PADD3 墨西哥湾</td><td class="num">39,556</td><td class="num">43,830</td><td class="num">34,405</td><td class="num">19.3%</td><td><span class="tag tag-o">偏紧</span></td></tr>
<tr><td>汽油总库存</td><td class="num">206,842</td><td class="num">231,723</td><td class="num">205,064</td><td class="num">0.7%</td><td><span class="tag tag-r">史低区</span></td></tr>
<tr><td>商业原油（不含 SPR）</td><td class="num">424,460</td><td class="num">450,888</td><td class="num">348,806</td><td class="num">31.7%</td><td><span class="tag tag-g">正常</span></td></tr>
</tbody></table>
<p class="note" style="margin-top:10px">分位为 2015–2025 同日历周排名（当前值所在的百分位，越低越紧）。注：分表 psw01 截至 8/21，表中 8/28 各值由 EIA v2 API 补取；PADD1A/B/C 与低硫/ULSD 的 8/28 值沿用 8/21（仅 U.S. 总量、PADD1、ULSD 有 8/28 更新）。</p>

<div class="no" style="margin-top:12px"><b>结构性事实：</b>紧张是<b>区域性和品级性</b>的。美国总量史低，但<u>低硫 15–500ppm（取暖油品级）仍在 53 分位＝中性</u>，而 <b>ULSD（0–15ppm）与东海岸全部在 0.0–0.2 分位</b>。也就是说，缺口集中在<b>车用柴油/超低硫</b>与<b>东部交割区</b>，而不是"取暖油品级"。这解释了为什么 HO 期货（交割在纽约港）的紧张与"取暖油品级库存充裕"可以同时存在。</div>
</div>

<h2 id="s3">三、核心矛盾：库存史低，月差却只有事件峰值的 30%</h2>
<div class="card">
<div id="c_scatter" class="chart chart-lg"></div>
<p class="small" style="margin-top:8px">横轴＝美国馏分油库存相对前 5 年同一日历周的偏离（越靠左＝越紧）；纵轴＝HO 近−次月价差（$/gal）。<b>2026-03-20</b>（偏离 −1.0%）与 <b>2026-08-28</b>（偏离 −13.6%）在两个极端位置，月差却是 3.4 倍差距——夹在两者中间的拟合线斜率仅 0.002 $/gal 每 1% 偏离。</p>
<table style="margin-top:12px">
<thead><tr><th>日期</th><th class="num">库存(千桶)</th><th class="num">5年偏离</th><th class="num">PADD1</th><th class="num">PADD1 偏离</th><th class="num">HO1! 价格</th><th class="num">近−次月</th><th>性质</th></tr></thead>
<tbody>
<tr><td>2022-04-29</td><td class="num">104,942</td><td class="num">−22.0%</td><td class="num">22,395</td><td class="num">—</td><td class="num">3.9949</td><td class="num"><b>0.3179</b></td><td class="note">制裁型冲击 · 实货抢货</td></tr>
<tr><td>2022-05-27</td><td class="num">107,000</td><td class="num">−22.2%</td><td class="num"><b>20,966</b></td><td class="num">—</td><td class="num">3.6900</td><td class="num">0.0774</td><td class="note"><b>库存几乎相同，月差已跌 76%</b></td></tr>
<tr><td>2026-03-20</td><td class="num">119,936</td><td class="num"><b>−1.0%</b></td><td class="num">27,448</td><td class="num">−15.7%</td><td class="num">4.2965</td><td class="num"><b>0.4823</b></td><td class="note">霍尔木兹封锁 · 急性近端恐慌</td></tr>
<tr><td>2026-05-22</td><td class="num">100,799</td><td class="num">−11.4%</td><td class="num">23,659</td><td class="num">−13.0%</td><td class="num">3.8000</td><td class="num">0.1171</td><td class="note">年内库存最低点，月差不高</td></tr>
<tr><td>2026-08-21</td><td class="num">103,391</td><td class="num">−14.4%</td><td class="num">21,003</td><td class="num">−35.5%</td><td class="num">4.3480</td><td class="num">0.1417</td><td class="note">区域性恶化被全国口径掩盖</td></tr>
<tr><td><b>2026-08-28</b></td><td class="num"><b>104,187</b></td><td class="num"><b>−13.6%</b></td><td class="num"><b>19,318</b></td><td class="num"><b>−41.0%</b></td><td class="num">4.2421</td><td class="num">0.1444</td><td class="note">东海岸破 1990 年以来纪录</td></tr>
<tr><td>2026-09-10</td><td class="num note">(8/28)</td><td class="num note">(8/28)</td><td class="num note">(8/28)</td><td class="num note">(8/28)</td><td class="num"><b>5.0082</b></td><td class="num">0.2023</td><td class="note">全史价格最高（库存数据滞后）</td></tr>
</tbody></table>
<div class="ok" style="margin-top:12px"><b>这段对照最能说明问题：</b>2022 年 4 月末到 5 月末，美国库存<b>几乎没变</b>（−22.0% → −22.2%），东海岸甚至刚创下当时的纪录低点，但月差从 0.3179 崩到 0.0774。<b>库存水平解释了 0%，月差走的是完全独立的一条时间线。</b></div>
</div>

<h2 id="s4">四、敏感度差异：价格吃库存，月差不吃</h2>
<div class="card">
<div class="grid2">
  <div><div id="c_r2" class="chart chart-sm"></div></div>
  <div><div id="c_bucket" class="chart chart-sm"></div></div>
</div>
<p class="small" style="margin-top:8px">左：同一自变量对"价格"与"月差"的解释力（R²）。<b>三种库存口径下，价格的解释力都是月差的 2.4–2.8 倍</b>，这不是口径挑出来的，是稳健结果。右：按"5 年偏离"分桶的月差中位数（灰柱，柱顶为样本数）。<b>2026-08 实际值 0.1444（橙点）落在 −15%~−10% 桶，是该桶中位数 0.017 的 8.5 倍。</b></p>
<table style="margin-top:12px">
<thead><tr><th>库存 5 年偏离桶</th><th class="num">&lt;−25%</th><th class="num">−25~−20%</th><th class="num">−20~−15%</th><th class="num">−15~−10%</th><th class="num">−10~−5%</th><th class="num">−5~0%</th><th class="num">&gt;0%</th></tr></thead>
<tbody>
<tr><td>样本数</td><td class="num">29</td><td class="num">42</td><td class="num">90</td><td class="num">144</td><td class="num">93</td><td class="num">140</td><td class="num">—</td></tr>
<tr><td>月差中位</td><td class="num">0.078</td><td class="num">0.058</td><td class="num">0.017</td><td class="num">0.0067</td><td class="num">0.0022</td><td class="num">−0.010</td><td class="num">—</td></tr>
</tbody></table>
<p class="note" style="margin-top:8px">注：2016-01 起价格与库存的周度交集，n=538。桶标签按实际分桶显示（&lt;−25% 桶无样本）。<b>单位：$/gal。</b></p>
<div class="warn" style="margin-top:12px"><b>关键推论：把"低库存 → 应该有大月差"当作基准，搞错了方向。</b>历史数据里，即使库存偏离到 −20% 以下，月差中位数也只有 0.058–0.078；2023 年 5 月、2025 年 8 月库存同样在 10.4 百万桶量级，月差中位只有 0.014–0.016（zero 附近）。<b>真正反常的是 2023/2025（库存一样低却完全没有月差），而不是 2026。</b></div>
</div>

<h2 id="s5">五、2026 年逐周分解：两种完全不同的机制</h2>
<div class="card">
<div id="c_tl" class="chart chart-lg"></div>
<p class="small" style="margin-top:8px">上图：HO1! 价格与近−次月价差。下图：<b>库存缺口</b>（= −[相对前 5 年同周偏离 %]，柱子越高＝比 5 年同期越紧）；蓝＝美国总量、橙＝PADD1 东海岸。</p>
<ul class="tight">
<li><b>2 月末–3 月：缺口为零，月差爆表。</b>2/27 全国库存偏离仅 −2.8%（PADD1 −21.7%），月差 0.067；3/6 价格跳涨到 3.65、月差飙到 0.338；3/20 库存偏离还是 −1.0%（<b>全国完全不紧</b>），月差见顶 0.4823。<b>这一段月差与美国库存无关，是霍尔木兹封锁下的近端交割恐慌。</b></li>
<li><b>4–8 月：缺口持续扩大，月差一路回落。</b>全国库存从 3/20 的 119.9 百万桶一路降到 8/28 的 104.2（−13%），月差却从 0.4823 收敛到 0.14。<b>月差与库存周度变化的相关性仅 −0.10~−0.14</b>（R²≈0.02），几乎无关。</li>
<li><b>7–9 月：缺口在东部加速恶化。</b>PADD1 从 3 月的 −15.7% 扩大到 8/28 的 <b>−41.0%</b>（1990 年以来最低），但月差只从 0.067 回到 0.14–0.20。<b>区域恶化被全国口径掩盖，且没有转化为近端斜率。</b></li>
</ul>
</div>

<h2 id="s6">六、机制：为什么这次是"整条曲线抬升"而不是"近端凸起"</h2>
<div class="card">
<table>
<thead><tr><th style="width:16%">维度</th><th style="width:42%">2026-03（急性挤压）</th><th>2026-08/09（结构性短缺）</th></tr></thead>
<tbody>
<tr><td>触发</td><td>霍尔木兹封锁（2/28 美以对伊动武），全球约 90 万桶/日柴油 + 35 万桶/日航煤航道中断</td><td>俄柴油出口禁令（延至 9/30）+ 乌克兰无人机打击俄炼厂 + 中东持续中断</td></tr>
<tr><td>市场认知</td><td>"会不会马上断供" → 近端抢货、远端不动</td><td>"缺口是长期的、已知的" → 全曲线一起抬</td></tr>
<tr><td>美国库存</td><td>完全正常（偏离 −1.0%）</td><td>史低（偏离 −13.6%，东海岸 −41.0%）</td></tr>
<tr><td>曲线形态</td><td>陡倒挂：次月/近月 <b>92.6%</b>（2022-04-28 对照）</td><td>近平行：次月/近月 <b>96.0%</b>，且次月 4.8059 <b>已超 2022 年价格前高 4.5275</b></td></tr>
<tr><td>月差</td><td>0.4823（全史最高）</td><td>0.14–0.20</td></tr>
<tr><td>价格</td><td>4.2965</td><td>5.0082（全史最高）</td></tr>
<tr><td>本质</td><td><b>速度问题</b>：能不能在到期前拿到货 → 表现为近端溢价</td><td><b>水位问题</b>：整条曲线对结构性赤字定价 → 表现为绝对价格</td></tr>
</tbody></table>

<h3>6.1 三条支撑"结构性"的机制证据</h3>
<ol class="tight">
<li><b>出口抽血（最重要）。</b>美国馏分油出口创纪录：截至 7/31 当周 188.4 万桶/日，4 周均值约 170–174 万桶/日，<b>同比 +24~29%</b>，8 月单月出口 5,420 万桶创纪录。出口量约等于国内产量的 <b>34%</b>。<b>美国库存下降不是因为美国需求，而是全球在竞标美国桶。</b></li>
<li><b>无冗余产能。</b>炼厂开工率 <b>98%</b>（2018 年 8 月以来最高），中西部已超过铭牌能力；但馏分油产量 513 万桶/日、<b>同比 −2.4%</b>，收率从 31.1% 降到 <b>29.3%</b>——多加工原油并不等于多产柴油。恢复受损产能要几个季度，新建要几年。</li>
<li><b>套利边界回归。</b>月差本质上有实货上限（运费 + 保险 + 仓储 + 融资）。3 月封锁把这条上限打穿（保险与运力成本飙升），9 月替代路线恢复运转后，套利重新把月差压回物流成本之内——这部分是<b>纯技术性的压缩</b>，与库存无关。</li>
</ol>
<div class="note" style="margin-top:8px">另有一个结构性因素：HO1!−HO2! 在 9 月对应的是 <b>10 月合约 vs 11 月合约</b>（肩月），冬季风险（12–2 月）定价在更远的曲线段，近次月价差天然无法承载。这也削弱了"月差低＝市场不担心冬天"的解读。</div>
</div>

<h2 id="s7">七、外部交叉验证</h2>
<div class="card">
<table>
<thead><tr><th style="width:14%">来源</th><th>要点</th></tr></thead>
<tbody>
<tr><td>路透 <span class="note">(2026-09-03)</span></td><td>美国柴油零售价创纪录 $5.820/加仑（破 2022-06-17 的 $5.819）；美国柴油裂解盘中创纪录 <b>$108.02/桶</b>；"馏分油库存的 8 月均值为 1982 年以来同期最低"；东海岸库存"截至 8/28 当周跌至 1,930 万桶的纪录低点（数据回溯至 1990 年）"；俄柴油出口禁令延至 9/30。</td></tr>
<tr><td>EIA <span class="note">(9/2 发布)</span></td><td>全国馏分油库存 <b>+0.8 百万桶</b>（市场预期 −1.3），但增量<b>全部来自墨西哥湾（+3.1 至 4,270 万桶）</b>，东海岸反而 <b>−1.7 至 1,930 万桶</b>。"全国口径的累库掩盖了东部恶化"。</td></tr>
<tr><td>买方/卖方观点</td><td>Goldman：柴油是震中，非计划停产比季节常态高约 60%，2027 柴油毛利预测上调至美国 $63/桶、欧洲 $49/桶；ING：认为中东与俄罗斯成品油流量<b>短期不会恢复</b>；UBS：炼厂已提开工率但被其他地区炼厂中断抵消。</td></tr>
<tr><td>政策风险</td><td>欧盟 6 国（奥/德/意/葡/西/波）推动全欧暴利税，9/18–19 都柏林财长会议列议题；美国成品油出口限制在 2022 年被讨论过，当前出口量使该议题政治敏感度回升。<b>（政策端，非本报告核心论据）</b></td></tr>
</tbody></table>
<div class="note" style="margin-top:10px">一处<b>未核实</b>信息：有二手来源称加拿大 Irving Oil 圣约翰炼厂自 2026 年 8 月因火灾停产约 75 天、加剧东北部紧张。该消息未在路透/EIA/主流财经源找到对应，<b>本报告不作为论据</b>。</div>
</div>

<h2 id="s8">八、结论、置信度与证伪条件</h2>
<div class="card concl">
<ol class="tight">
<li><b>直接回答"为什么价格回到前高甚至创新高，月差却大幅低于前高"：</b>因为这两个量衡量的不是同一件事。价格＝绝对稀缺水位，会被"结构性赤字"整条曲线抬升；月差＝边际稀缺租金（近端相对远端的稀缺速度），只在"市场担心近期拿不到货"时爆发。2026-03 的 0.4823 与 2022 的 0.4014 都是<b>事件型近端恐慌</b>；2026-09 是<b>结构性短缺的慢变量定价</b>。同一份库存数据（甚至更紧）在两种机制下会给出完全相反的月差。</li>
<li><b>另一个常被忽略的点：现在的月差相对其库存水平是偏高的，不是偏低。</b>库存偏离 −13.6% 对应的历史月差中位仅 0.017，实际 0.144；2023/2025 在同样库存水平上月差约为 0。低库存本来就不保证正价差。</li>
<li><b>对交易的含义（不是建议）：</b>用"库存史低"去论证"月差应该更高"是方法错误——月差的驱动是<span class="term" data-tip="近端供需的时间导数：本周比上周更紧还是更松。库存的历史变化与月差的相关系数仅 −0.10~−0.14。">库存变化的边际</span>与事件风险，不是库存水位。反过来，若把"库存史低 + 区域破纪录 + 出口占产量 34%"作为<b>价格</b>的支撑论据，则证据链完整。</li>
</ol>
<p style="margin-top:10px"><b>置信度</b>：</p>
<table>
<thead><tr><th>结论</th><th style="width:14%">置信度</th><th>依据 / 保留</th></tr></thead>
<tbody>
<tr><td>库存处于史低（美国 + 东海岸）</td><td><span class="tag tag-g">高</span></td><td>EIA 原始表 + API + 路透交叉验证，三源一致</td></tr>
<tr><td>价格对库存的敏感度显著高于月差</td><td><span class="tag tag-g">高</span></td><td>三种库存口径下 R² 比值稳定在 2.4–2.8 倍，n=538</td></tr>
<tr><td>2026-03 与 2026-09 属两种机制</td><td><span class="tag tag-o">中高</span></td><td>库存与曲线形态证据自洽；"急性 vs 结构性"的归因缺少可独立观测的预期变量</td></tr>
<tr><td>月差近端上限由套利/物流决定</td><td><span class="tag tag-o">中</span></td><td>与 3 月封锁期月差突破物流上限的事实一致，但无运费/保险逐日数据可验证</td></tr>
</tbody></table>
<div class="warn" style="margin-top:14px"><b>证伪条件（三条同时满足才推翻"结构性"判断）：</b>
<ol class="tight small" style="margin-top:6px">
<li>连续 <b>3 周</b> 美国馏分油库存累库；</li>
<li><b>且 PADD1 东海岸同步累库</b>（仅全国累库不算——8/28 已经出现"全国 +0.8 而东部 −1.7"的假信号）；</li>
<li><b>且 ULSD 裂解价差回落至约 $60/桶以下</b>（当前约 $100–108）。</li>
</ol>
<p class="small" style="margin-top:6px">三条中任意两条而无第三条，视为噪声。另外，10 月起的两个硬节点会重新定价：<b>俄柴油出口禁令 9/30 到期是否续期</b>、<b>11 月起的冬季取暖需求与拉尼娜相关的寒潮风险</b>。</p></div>
</div>

<h2 id="s9">九、数据来源与局限</h2>
<div class="card">
<ul class="tight small">
<li><b>价格/月差</b>：TradingView 导出主连日线 HO1!（2013-03 起）与 HO1!−HO2!（2015-11 起），数据文件 <code>Temp/ho_price_spread_merged.csv</code>。主连为连续主力、未复权，仅用于水平与价差结构，不做收益统计。</li>
<li><b>库存</b>：用户提供 <code>psw01.xls</code>/<code>psw06.xls</code>（2026-08-26 发布版，截至 8/21）+ EIA v2 API 补 8/28；解析后落盘 <code>Temp/eia_wpsr_weekly.csv</code>（2,291 周，1982-08-20 ~ 2026-08-28）。</li>
<li><b>局限 1（时间错位）</b>：库存最新 8/28、价格最新 9/10，两者差约 1.5 周。9/10 的"价格 5.0082 + 月差 0.2023"配的是 8/28 的库存，不是同日。结论对此不敏感（8/21→8/28 全国库存仅 +0.8%），但严格同日口径不可得。</li>
<li><b>局限 2（口径）</b>：<code>dist_ls500</code> 等分品级系列的 8/28 值缺失，沿用 8/21；分位数基准为 2015–2025，窗口选择会影响绝对值但不变结论方向（用 2016-2025 或 10 年基准结论一致）。</li>
<li><b>局限 3（相关性 ≠ 因果）</b>：库存与价格/月差均为内生变量，共同受地缘事件驱动；本报告用"同库存水平横截面差异"（2022/2023/2025/2026 对照）来部分规避趋势共动，但无法排除遗漏变量。</li>
</ul>
<div class="disclaimer">本报告为数据研究记录，不构成任何投资建议。EIA 周度数据存在修订可能；月差为期货近次月价差，不代表实货贴水。</div>
</div>

<div class="foot">
83 · HO 月差 × EIA 库存解构 ｜ 生成 2026-09-10 ｜ 数据：TradingView（HO1!/HO1!−HO2!）· EIA WPSR psw01/psw06 · EIA v2 API（石油库存/供应）<br>
配套文件：<code>Temp/eia_wpsr_weekly.csv</code>（库存面板）· <code>Temp/ho_price_spread_merged.csv</code>（价格/月差）· <code>Temp/ho83_data.json</code>（图表数据）
</div>

</div>

<script>
const D_SCATTER = __SCATTER__;
const D_KEY = __KEY__;
const D_TL = __TL__;
const D_BUCKET = __BUCKET__;
const D_HIST = __HIST__;
const D_P1MIN = __P1MIN__;
const D_R2 = __R2__;

const C = {blue:'#0072B2', orange:'#E69F00', sky:'#56B4E9', purple:'#CC79A7', vermil:'#D55E00',
           green:'#009E73', grey:'#9a948a', ink:'#26313d', sub:'#5b6672', line:'#e3e0d8', red:'#C0392B'};
const AX = {axisLine:{lineStyle:{color:'#c9c4ba'}}, axisLabel:{color:C.sub, fontSize:11}, splitLine:{lineStyle:{color:'#efece6'}}};
const TT = {backgroundColor:'rgba(38,49,61,.94)', borderWidth:0, textStyle:{color:'#fff', fontSize:12.5}, padding:[8,12]};

/* ---------- 1. 散点 ---------- */
(function(){
  const mk = (arr) => arr.map(p => [p[0], p[1], p[2]]);
  const fit = D_SCATTER.fit;
  const xs = D_SCATTER.pts.other.concat(D_SCATTER.pts.y2022, D_SCATTER.pts.y2026).map(p=>p[0]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const ch = echarts.init(document.getElementById('c_scatter'));
  const markPts = Object.keys(D_KEY).map(k => ({
    name: k, coord: D_KEY[k], value: k.slice(5),
    label:{formatter: k.slice(5)+'\n'+D_KEY[k][1].toFixed(3), color:'#26313d', fontSize:11, position:'top'},
    itemStyle:{color: k.startsWith('2026-03')?C.red:(k.startsWith('2026')?C.blue:C.orange)}
  }));
  ch.setOption({
    animationDuration:700,
    grid:{left:64, right:26, top:34, bottom:52},
    tooltip:Object.assign({trigger:'item', formatter: p => {
      if (p.seriesName==='回归线') return '拟合线：月差 = '+fit.a.toFixed(4)+' '+(fit.b<0?'−':'+')+Math.abs(fit.b).toFixed(5)+' × 库存偏离';
      return '<b>'+(p.data[2]||p.name)+'</b><br>库存5年偏离：'+p.data[0]+'%<br>近−次月月差：'+p.data[1]+' $/gal';}}, TT),
    xAxis:Object.assign({name:'库存相对前5年同周偏离 (%)', nameLocation:'middle', nameGap:32, nameTextStyle:{color:C.sub,fontSize:12}, min:Math.floor(x0)-1, max:Math.ceil(x1)+1, type:'value'}, AX),
    yAxis:Object.assign({name:'月差 ($/gal)', nameTextStyle:{color:C.sub,fontSize:12}, scale:true}, AX),
    series:[
      {name:'其他年份', type:'scatter', data:mk(D_SCATTER.pts.other), symbolSize:5,
       itemStyle:{color:C.grey, opacity:.42},
       markPoint:{silent:true, symbolSize:0, data:markPts}},
      {name:'2022 年', type:'scatter', data:mk(D_SCATTER.pts.y2022), symbolSize:9,
       itemStyle:{color:C.orange, opacity:.95, borderColor:'#fff', borderWidth:.5}},
      {name:'2026 年', type:'scatter', data:mk(D_SCATTER.pts.y2026), symbolSize:10,
       itemStyle:{color:C.blue, opacity:.95, borderColor:'#fff', borderWidth:.5}},
      {name:'回归线', type:'line', data:[[x0, fit.a+fit.b*x0],[x1, fit.a+fit.b*x1]], symbol:'none',
       lineStyle:{color:C.ink, width:2, type:'dashed'}, tooltip:{show:true}}
    ],
    legend:{top:0, right:10, itemWidth:12, itemHeight:8, textStyle:{color:C.sub, fontSize:12}},
    graphic:[{type:'text', right:30, top:26, style:{
      text:'r = '+fit.r+'   R² = '+fit.r2+'   n = '+fit.n, fill:C.sub, fontSize:12}}]
  });
})();

/* ---------- 2. 2026 时序 ---------- */
(function(){
  const t = D_TL;
  const gap_us = t.dev_us.map(v => +(-v).toFixed(1));
  const gap_p1 = t.dev_p1.map(v => +(-v).toFixed(1));
  const ch = echarts.init(document.getElementById('c_tl'));
  ch.setOption({
    animationDuration:700,
    tooltip:Object.assign({trigger:'axis', axisPointer:{type:'cross'}, formatter: ps => {
      const i = ps[0].dataIndex;
      return '<b>'+t.lbl[i]+'</b>（EIA 周）<br>' +
        '库存缺口 美国：'+(gap_us[i]>0?'−':'+')+Math.abs(gap_us[i])+'%<br>' +
        '库存缺口 PADD1：'+(gap_p1[i]>0?'−':'+')+Math.abs(gap_p1[i])+'%<br>' +
        '美国库存：'+(t.dist[i]/1000).toFixed(1)+' 百万桶<br>' +
        'HO1! 价格：'+t.price[i]+'<br>近−次月：'+t.spread[i]+' $/gal';}}, TT),
    axisPointer:{link:[{xAxisIndex:'all'}]},
    grid:[{left:62, right:64, top:40, height:'38%'},{left:62, right:64, top:'62%', height:'26%'}],
    legend:{top:2, left:'center', itemWidth:12, itemHeight:8, textStyle:{color:C.sub, fontSize:12},
      data:['HO1! 价格','近−次月价差','库存缺口 · 美国','库存缺口 · PADD1']},
    xAxis:[
      {type:'category', data:t.lbl, boundaryGap:false, axisLabel:{color:C.sub, fontSize:11},
       axisLine:{lineStyle:{color:'#c9c4ba'}}, splitLine:{show:false}},
      {type:'category', data:t.lbl, gridIndex:1, boundaryGap:false, axisLabel:{color:C.sub, fontSize:11},
       axisLine:{lineStyle:{color:'#c9c4ba'}}, splitLine:{show:false}}
    ],
    yAxis:[
      {type:'value', name:'价格 ($/gal)', nameTextStyle:{color:C.sub,fontSize:11}, scale:true,
       axisLine:{lineStyle:{color:'#c9c4ba'}}, axisLabel:{color:C.sub,fontSize:11,formatter:v=>v.toFixed(1)}, splitLine:{lineStyle:{color:'#efece6'}}},
      {type:'value', name:'月差 ($/gal)', nameTextStyle:{color:C.sub,fontSize:11}, scale:true,
       axisLine:{lineStyle:{color:'#c9c4ba'}}, axisLabel:{color:C.sub,fontSize:11,formatter:v=>v.toFixed(2)}, splitLine:{show:false}},
      {type:'value', gridIndex:1, name:'库存缺口 (%)', nameTextStyle:{color:C.sub,fontSize:11},
       axisLine:{lineStyle:{color:'#c9c4ba'}}, axisLabel:{color:C.sub,fontSize:11,formatter:v=>v+'%'}, splitLine:{lineStyle:{color:'#efece6'}}}
    ],
    series:[
      {name:'HO1! 价格', type:'line', data:t.price, smooth:true, symbol:'none',
       lineStyle:{color:C.ink, width:2}, yAxisIndex:0},
      {name:'近−次月价差', type:'line', data:t.spread, smooth:true, symbol:'none',
       lineStyle:{color:C.vermil, width:2.2}, yAxisIndex:1, areaStyle:{color:'rgba(213,94,0,.08)'}},
      {name:'库存缺口 · 美国', type:'bar', data:gap_us, xAxisIndex:1, yAxisIndex:2,
       itemStyle:{color:C.blue, opacity:.85}, barWidth:'46%'},
      {name:'库存缺口 · PADD1', type:'bar', data:gap_p1, xAxisIndex:1, yAxisIndex:2,
       itemStyle:{color:C.orange, opacity:.9}, barWidth:'46%'},
      {name:'零轴', type:'line', data:t.lbl.map(()=>0), xAxisIndex:1, yAxisIndex:2, symbol:'none',
       lineStyle:{color:C.sub, width:1, type:'dotted'}, silent:true, legendHoverLink:false}
    ]
  });
})();

/* ---------- 3. R² 对比 ---------- */
(function(){
  const d = D_R2;
  const ch = echarts.init(document.getElementById('c_r2'));
  ch.setOption({
    animationDuration:700,
    tooltip:Object.assign({trigger:'axis', axisPointer:{type:'shadow'}, formatter: ps => {
      const i = ps[0].dataIndex, s = d[i];
      return '<b>'+s.lab+'</b><br>价格：R² = '+s.price+'（r = '+s.price_r+'）<br>月差：R² = '+s.spread+'（r = '+s.spread_r+'）';}}, TT),
    legend:{top:0, itemWidth:12, itemHeight:8, textStyle:{color:C.sub,fontSize:12}},
    grid:{left:56, right:22, top:40, bottom:56},
    xAxis:Object.assign({type:'category', data:d.map(s=>s.lab), axisLabel:{color:C.sub,fontSize:11.5,interval:0,width:84,overflow:'break'}}, AX),
    yAxis:Object.assign({type:'value', name:'R²', max:0.65, nameTextStyle:{color:C.sub,fontSize:11}}, AX),
    series:[
      {name:'对 价格 的解释力', type:'bar', data:d.map(s=>s.price), barGap:'12%',
       itemStyle:{color:C.ink}, label:{show:true, position:'top', color:C.ink, fontSize:11, formatter:p=>p.value.toFixed(3)}},
      {name:'对 月差 的解释力', type:'bar', data:d.map(s=>s.spread),
       itemStyle:{color:C.orange}, label:{show:true, position:'top', color:C.vermil, fontSize:11, formatter:p=>p.value.toFixed(3)}}
    ]
  });
})();

/* ---------- 4. 分桶 ---------- */
(function(){
  const d = D_BUCKET;
  const cur = d.cur;
  const idx = d.lbl.findIndex(l => d.cur_dev >= parseFloat(l.split('~')[0].replace('%','').replace('<','')) );
  const ch = echarts.init(document.getElementById('c_bucket'));
  ch.setOption({
    animationDuration:700,
    tooltip:Object.assign({trigger:'axis', axisPointer:{type:'shadow'}, formatter: ps => {
      const i = ps[0].dataIndex;
      let s = '<b>库存偏离 '+d.lbl[i]+'</b><br>样本数：'+d.n[i]+'<br>月差中位：'+d.med[i]+' $/gal';
      if (d.lbl[i]==='-15~-10%') s += '<br><b style="color:#E69F00">2026-08 实际：'+cur+'（'+(cur/d.med[i]).toFixed(1)+'× 中位）</b>';
      return s;}}, TT),
    grid:{left:62, right:24, top:34, bottom:58},
    xAxis:Object.assign({type:'category', data:d.lbl, axisLabel:{color:C.sub,fontSize:11.5,interval:0}}, AX),
    yAxis:Object.assign({type:'value', name:'月差中位 ($/gal)', nameTextStyle:{color:C.sub,fontSize:11}}, AX),
    series:[
      {name:'月差中位', type:'bar', data:d.med.map((v,i)=>({value:v, itemStyle:{color: d.lbl[i]==='-15~-10%'?C.blue:C.grey, opacity: d.lbl[i]==='-15~-10%'?1:.72}})),
       barWidth:'56%',
       label:{show:true, position:'top', color:C.sub, fontSize:10.5, formatter:p=>p.value.toFixed(3)},
       markLine:{silent:true, symbol:'none', label:{show:false}, data:[{yAxis:0}]}},
      {name:'2026-08 实际', type:'scatter', data:[[d.lbl.indexOf('-15~-10%'), cur]], symbolSize:13,
       itemStyle:{color:C.vermil, borderColor:'#fff', borderWidth:1.5},
       label:{show:true, position:'top', color:C.vermil, fontSize:11.5, fontWeight:'bold', formatter:'2026-08 实际 '+cur}}
    ]
  });
})();

/* ---------- 5. 库存史 ---------- */
(function(){
  const h = D_HIST, pm = D_P1MIN;
  const ch = echarts.init(document.getElementById('c_hist'));
  const n = h.lbl.length;
  const band = h.lbl.map(()=>null);
  ch.setOption({
    animationDuration:700,
    tooltip:Object.assign({trigger:'axis', axisPointer:{type:'cross'}, formatter: ps => {
      const i = ps[0].dataIndex;
      return '<b>'+h.lbl[i]+'</b><br>美国馏分油：'+(h.us[i]/1000).toFixed(1)+' 百万桶' +
             (h.p1[i]!=null ? '<br>PADD1 东海岸：'+(h.p1[i]/1000).toFixed(2)+' 百万桶' : '');}}, TT),
    legend:{top:0, itemWidth:12, itemHeight:8, textStyle:{color:C.sub,fontSize:12}},
    grid:{left:66, right:66, top:36, bottom:40},
    xAxis:Object.assign({type:'category', data:h.lbl, boundaryGap:false,
      axisLabel:{color:C.sub, fontSize:10.5, interval:23}}, AX),
    yAxis:[
      Object.assign({type:'value', name:'美国 (百万桶)', nameTextStyle:{color:C.sub,fontSize:11},
        axisLabel:{color:C.sub,fontSize:11,formatter:v=>(v/1000).toFixed(0)}}, AX),
      Object.assign({type:'value', name:'PADD1 (百万桶)', nameTextStyle:{color:C.sub,fontSize:11},
        axisLabel:{color:C.sub,fontSize:11,formatter:v=>(v/1000).toFixed(0)}, splitLine:{show:false}}, AX)
    ],
    series:[
      {name:'美国馏分油库存', type:'line', data:h.us, symbol:'none', smooth:false,
       lineStyle:{color:C.blue, width:1.8}, areaStyle:{color:'rgba(0,114,178,.07)'}},
      {name:'PADD1 东海岸', type:'line', data:h.p1, symbol:'none', smooth:false, yAxisIndex:1,
       lineStyle:{color:C.orange, width:1.8},
       markPoint:{symbolSize:9, data:[
         {name:'史低', coord:[h.lbl.indexOf('26/08'), pm.v26], value:'史低',
          itemStyle:{color:C.red}, label:{color:C.red, fontSize:11, position:'bottom', formatter:'1990 年以来最低 19.3'}}],
         label:{color:C.red}}}
    ]
  });
})();
</script>
</body>
</html>
'''

HTML = (HTML.replace('__SCATTER__', J('scatter'))
            .replace('__KEY__', J('key_pts'))
            .replace('__TL__', J('tl26'))
            .replace('__BUCKET__', J('buckets'))
            .replace('__HIST__', J('hist'))
            .replace('__P1MIN__', J('p1_min'))
            .replace('__R2__', J('r2cmp')))

open(OUT + '/index.html', 'w', encoding='utf-8').write(HTML)
print('written', OUT + '/index.html', len(HTML), 'bytes')
print('placeholders left:', [p for p in ['__SCATTER__','__KEY__','__TL__','__BUCKET__','__HIST__','__P1MIN__','__R2__'] if p in HTML])
