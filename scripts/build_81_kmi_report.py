# -*- coding: utf-8 -*-
"""81 号报告：KMI 金德摩根全面深度分析（基本面 × 估值 × 技术面 × 行业 × 宏观 × 投资观点）
数据源：SEC XBRL（CIK0001506307, 10-K/10-Q）、KMI Q2'26 财报新闻稿（IR）、
新浪美股日线（未复权）、Yahoo Finance 快照、同花顺/东财机构共识、EIA/FERC 政策快讯。
"""
import os
import json

ROOT = "C:/Users/Administrator/Desktop/stock"
OUT_DIR = os.path.join(ROOT, "reports", "81_KMI金德摩根深度分析")
os.makedirs(OUT_DIR, exist_ok=True)

# ============ 数据 ============
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
REV  = [14.14, 13.21, 11.70, 16.61, 19.20, 15.33, 15.10, 16.94]
OP   = [3.79, 4.87, 1.56, 2.92, 4.07, 4.26, 4.38, 4.72]
NI   = [1.61, 2.19, 0.12, 1.78, 2.55, 2.39, 2.61, 3.06]
OCF  = [5.04, 4.75, 4.55, 5.71, 4.97, 6.49, 5.64, 5.92]
CAPX = [2.90, 2.27, 1.71, 1.28, 1.62, 2.32, 2.63, 3.03]
DPS  = [0.80, 1.00, 1.05, 1.08, 1.11, 1.13, 1.15, 1.17]
DEBT = [33.94, 31.92, 32.13, 30.67, 28.40, 28.07, 29.88, 30.78]
EQ   = [33.68, 33.74, 31.44, 30.82, 30.74, 30.31, 30.53, 31.16]
ASSET= [78.87, 74.16, 71.97, 70.42, 70.08, 71.02, 71.41, 72.75]
DA   = [2.30, 2.41, 2.16, 2.14, 2.19, 2.25, 2.35, 2.45]
SHARES = [2.266, 2.267, 2.264, 2.259, 2.248, 2.220, 2.222, 2.225]

FCF = [round(c - x, 2) for c, x in zip(OCF, CAPX)]
NPM = [round(n / r * 100, 1) for n, r in zip(NI, REV)]
EPS = [round(n / s, 2) for n, s in zip(NI, SHARES)]
PAYOUT = [round(d / e * 100, 1) for d, e in zip(DPS, EPS)]

Q = [
    {"q": "24Q1", "rev": 3.842, "ni": 0.746}, {"q": "24Q2", "rev": 3.572, "ni": 0.575},
    {"q": "24Q3", "rev": 3.699, "ni": 0.625}, {"q": "24Q4", "rev": 3.987, "ni": 0.702},
    {"q": "25Q1", "rev": 4.241, "ni": 0.717}, {"q": "25Q2", "rev": 4.042, "ni": 0.715},
    {"q": "25Q3", "rev": 4.146, "ni": 0.628}, {"q": "25Q4", "rev": 4.511, "ni": 0.996},
    {"q": "26Q1", "rev": 4.828, "ni": 0.976}, {"q": "26Q2", "rev": 4.477, "ni": 0.867},
]
Q_YOY_REV = [None, None, None, None, round((4.241 / 3.842 - 1) * 100, 1),
             round((4.042 / 3.572 - 1) * 100, 1), round((4.146 / 3.699 - 1) * 100, 1),
             None, round((4.828 / 4.241 - 1) * 100, 1), round((4.477 / 4.042 - 1) * 100, 1)]

MONTHLY = [
    ("2024-04", 19.35), ("2024-05", 19.62), ("2024-06", 19.91), ("2024-07", 20.83),
    ("2024-08", 21.08), ("2024-09", 21.70), ("2024-10", 22.16), ("2024-11", 23.10),
    ("2024-12", 23.74), ("2025-01", 25.10), ("2025-02", 25.98), ("2025-03", 25.15),
    ("2025-04", 25.94), ("2025-05", 27.19), ("2025-06", 28.65), ("2025-07", 29.63),
    ("2025-08", 28.59), ("2025-09", 28.31), ("2025-10", 26.19), ("2025-11", 27.32),
    ("2025-12", 27.49), ("2026-01", 30.49), ("2026-02", 33.27), ("2026-03", 33.53),
    ("2026-04", 32.87), ("2026-05", 31.08), ("2026-06", 31.97), ("2026-07", 32.18),
    ("2026-08", 32.24), ("2026-09", 31.40),
]

PEERS_PERF = [
    {"sym": "KMI", "name": "Kinder Morgan", "ytd": 13.3, "y1": 18.1, "y3": 82.3, "gap": -8.5},
    {"sym": "WMB", "name": "Williams", "ytd": 21.9, "y1": 29.6, "y3": 114.7, "gap": -6.6},
    {"sym": "ET", "name": "Energy Transfer", "ytd": 29.6, "y1": 23.6, "y3": 59.6, "gap": -0.2},
    {"sym": "OKE", "name": "ONEOK", "ytd": 28.4, "y1": 31.4, "y3": 46.4, "gap": -1.7},
    {"sym": "ENB", "name": "Enbridge", "ytd": 4.1, "y1": 3.8, "y3": 42.8, "gap": -13.7},
    {"sym": "EPD", "name": "Enterprise Products", "ytd": 21.1, "y1": 23.0, "y3": 46.3, "gap": -2.2},
]
PEERS_VAL = [
    {"sym": "KMI", "name": "Kinder Morgan", "pe": 20.3, "pb": 2.21, "dy": 3.76, "mcap": 699, "roe": 11.0, "beta": 0.54},
    {"sym": "WMB", "name": "Williams", "pe": 29.5, "pb": 6.89, "dy": 2.80, "mcap": 907, "roe": 18.8, "beta": 0.87},
    {"sym": "OKE", "name": "ONEOK", "pe": 16.5, "pb": 2.62, "dy": 4.44, "mcap": 602, "roe": 16.4, "beta": 0.73},
    {"sym": "ET", "name": "Energy Transfer", "pe": 11.2, "pb": 1.38, "dy": 7.40, "mcap": 737, "roe": 8.9, "beta": 0.83},
    {"sym": "EPD", "name": "Enterprise Products", "pe": 11.3, "pb": 2.08, "dy": 6.40, "mcap": 842, "roe": 16.7, "beta": 0.76},
    {"sym": "ENB", "name": "Enbridge", "pe": 18.6, "pb": 2.32, "dy": 5.90, "mcap": 1096, "roe": 9.8, "beta": 0.55},
]

# ---- JS 数组文本 ----
def js_arr(a, fmt="{:.2f}"):
    return "[" + ",".join((fmt.format(x) if x is not None else "null") for x in a) + "]"

J = {
    "YEARS": js_arr(YEARS, "{:.0f}"),
    "REV": js_arr(REV), "OP": js_arr(OP), "NI": js_arr(NI),
    "OCF": js_arr(OCF), "CAPX": js_arr(CAPX), "FCF": js_arr(FCF),
    "Q_YOY": js_arr(Q_YOY_REV),
    "Q_NAMES": json.dumps([q["q"] for q in Q]),
    "Q_REV": "[" + ",".join(str(round(q["rev"], 2)) for q in Q) + "]",
    "Q_NI": "[" + ",".join(str(round(q["ni"], 2)) for q in Q) + "]",
    "MON_DATES": json.dumps([m[0] for m in MONTHLY]),
    "MON_VALS": "[" + ",".join(str(round(m[1], 2)) for m in MONTHLY) + "]",
    "PEER_NAMES": json.dumps([p["name"] for p in PEERS_PERF]),
    "PEER_YTD": js_arr([p["ytd"] for p in PEERS_PERF]),
    "PEER_Y1": js_arr([p["y1"] for p in PEERS_PERF]),
    "PEER_Y3": js_arr([p["y3"] for p in PEERS_PERF]),
    "VAL_NAMES": json.dumps([p["name"] for p in PEERS_VAL]),
    "VAL_PE": "[" + ",".join(str(p["pe"]) for p in PEERS_VAL) + "]",
    "VAL_DY": "[" + ",".join(str(p["dy"]) for p in PEERS_VAL) + "]",
    "VAL_SCATTER": "[" + ",".join("[" + str(p["pe"]) + "," + str(p["dy"]) + "]" for p in PEERS_VAL) + "]",
}

def fill(tpl):
    out = tpl
    for k, v in J.items():
        out = out.replace('@@' + k + '@@', v)
    return out

# ============ HTML ============
HTML_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>81 · KMI 金德摩根全面深度分析</title>
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
.kpis{display:grid; grid-template-columns:repeat(8,1fr); gap:10px; margin:18px 0;}
.kpi{background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 8px; text-align:center;}
.kpi b{display:block; font-size:17px; margin-top:2px;}
.kpi span{font-size:12px; color:var(--sub);}
h2{font-size:20px; margin:34px 0 12px; padding-left:10px; border-left:5px solid var(--blue);}
h3{font-size:16px; margin:20px 0 8px;}
.card{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:18px 20px; margin-bottom:14px;}
.chart{width:100%; height:380px;}
.chart-sm{height:330px;}
.grid2{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
table{width:100%; border-collapse:collapse; font-size:14px; background:var(--card);}
th{background:#eef1f4; color:var(--ink); font-weight:600; text-align:left;}
th,td{padding:8px 10px; border-bottom:1px solid var(--line);}
tr:hover td{background:#f6f9fc;}
.num{text-align:right; font-variant-numeric:tabular-nums;}
.up{color:var(--red); font-weight:600;}
.down{color:var(--down); font-weight:600;}
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
ul.tight li{margin:5px 0;}
.foot{margin-top:40px; color:var(--sub); font-size:12px; border-top:1px solid var(--line); padding-top:12px;}
.disclaimer{background:#f4f1ea; border:1px dashed var(--grey); border-radius:8px; padding:10px 14px; font-size:12.5px; color:var(--sub); margin-top:16px;}
.badge{display:inline-block; background:var(--blue); color:#fff; border-radius:4px; padding:2px 10px; font-size:13px; margin-right:6px;}
.vrating{font-size:18px; font-weight:700;}
@media (max-width:900px){ .kpis{grid-template-columns:repeat(4,1fr);} .grid2{grid-template-columns:1fr;} }
</style>
</head>
<body>
<div class="wrap">

<div class="head">
  <h1>81 · 金德摩根（Kinder Morgan, KMI）全面深度分析</h1>
  <div class="meta">北美最大能源基础设施公司 · NYSE: KMI ｜ 报告日 2026-09-06 ｜ 行情截至 2026-09-04 ｜ 财务口径：SEC XBRL 10-K/10-Q（GAAP）+ 公司 Q2'26 新闻稿（非 GAAP 另注）</div>
  <div class="toc">
    <a href="#s1">① 公司与商业模式</a><a href="#s2">② 行业格局与竞争地位</a><a href="#s3">③ 核心财务</a>
    <a href="#s4">④ 估值分析</a><a href="#s5">⑤ 股价走势与技术面</a><a href="#s6">⑥ 增长动力与风险</a>
    <a href="#s7">⑦ 宏观与能源政策</a><a href="#s8">⑧ 投资观点</a><a href="#s9">⑨ 数据来源与时效</a>
  </div>
</div>

<div class="kpis">
  <div class="kpi"><span>收盘（09-04）</span><b>$31.40</b></div>
  <div class="kpi"><span>总市值</span><b>$699亿</b></div>
  <div class="kpi"><span>PE (TTM)</span><b>≈20.3×</b></div>
  <div class="kpi"><span>Forward PE</span><b>≈21×</b></div>
  <div class="kpi"><span>股息率 (年化)</span><b>3.79%</b></div>
  <div class="kpi"><span>净债务/EBITDA</span><b>3.6×</b></div>
  <div class="kpi"><span>52周区间</span><b>25.84–34.49</b></div>
  <div class="kpi"><span>共识目标价</span><b>$35.9</b></div>
</div>

<div class="card concl">
<b>核心结论（一句话版）</b>：KMI 正处于 <b>「数据中心电力需求 + LNG 出口 + FERC 审批环境转顺」三重驱动的天然气基建资本开支上行周期</b>——Q2'26 调整 EBITDA $2.20B（+12%）创纪录、全年指引二度上调、净杠杆降至 3.6×（2014 合并以来最低）并获穆迪 Baa1 上调；但股价已在 2月/5月两轮上涨后进入 4 个月箱体整理（YTD +13.3%，距 52 周高 −8.5%）。<b>估值不贵不便宜</b>：20.3× TTM 高于 OKE/ET 等流量型同业，低于 WMB 成长溢价；3.79% 股息率 + 9 年连增提供类债底座。<b>评级：增持（Accumulate）/ 12 个月目标价 $33.5–35.5（中枢 ≈$34.5）</b>，核心逻辑：$9.6B 项目积压（92% 天然气）将在 2027–2029 转为合同化 EBITDA + 杠杆回落释放回购/提息空间；主要风险：天然气现货疲弱、2026H2 增速环比放缓、利率上行压制长久期资产估值。
</div>

<h2 id="s1">① 公司与商业模式</h2>
<div class="card">
<p><b>金德摩根（Kinder Morgan, Inc.）</b>是北美最大的能源基础设施公司（按企业价值计），总部休斯顿。核心资产：约 <b>78,000 英里</b>天然气/成品油/原油管道、<b>136 座</b>码头储罐终端、天然气集输加工设施、CO₂ 驱油（EOR）油田及美国最大独立储气网络（约 700 Bcf）<span class="note">（Yahoo Finance 公司简介 / 年报口径）</span>。</p>
<p style="margin-top:8px">收入结构（FY2025 分部口径，具 10-K 构成）：</p>
<table style="margin-top:6px">
<tr><th>业务分部</th><th>FY25 收入</th><th>占比</th><th>属性与近期趋势（Q2'26）</th></tr>
<tr><td><b>天然气管道</b></td><td class="num">$109.9亿</td><td class="num">64.9%</td><td>州际/州内干线段、集输加工、储气——管输量 <b>+7%</b>（LNG 原料气/墨西哥出口/亚利桑那电力需求），集输量 <b>+26%</b>（KinderHawk +54%、Haynesville +50%）</td></tr>
<tr><td><b>成品油管道</b></td><td class="num">$26.9亿</td><td class="num">15.9%</td><td>汽柴航煤/原油/凝析油——成品油量 <b>−5%</b>（西海岸扰动+高油价），原油/凝析油量 <b>−16%</b>（Double H 转 NGL 服务）</td></tr>
<tr><td><b>码头</b></td><td class="num">$20.9亿</td><td class="num">12.4%</td><td>液体/干散货码头、储罐、Jones Act 油轮——液体码头利用率 ~93%、储罐 ~99%；油轮 2026 全约、2027 高九成覆盖</td></tr>
<tr><td><b>CO₂</b></td><td class="num">$11.7亿</td><td class="num">6.9%</td><td>CO₂ 销售 + EOR（SACROC）+ Energy Transition Ventures（RNG/CCS）——SACROC 产量 +15%</td></tr>
</table>
<p style="margin-top:8px"><b>商业模式特征</b>：约 <b>65% 营收受"照付不议"（ship-or-pay）长期合同保障</b>、约 50% 与商品价格脱钩——现金流的可预测性在能源股中罕见；<b>调整后 EBITDA 利润率稳定在 ~53%</b>（26Q1 创 8 季度新高），量增直接转现金流、不带来同比例成本。管理理念"合同驱动、股东友好"：净杠杆从 2015 年峰值 5.4× 降至 3.6×，股息连续 9 年上调。</p>
</div>

<h2 id="s2">② 行业格局与竞争地位</h2>
<div class="card">
<h3>2.1 美国中游行业结构</h3>
<p>美国中游（Midstream）高度集中、以"存量资产寡头"为特征：跨州天然气管线受 FERC NGA §7 证书制监管，新进入者需逐项目审批，已建网络具自然垄断属性。<b>行业逻辑已从 2014–2016 的"气荒找买家"切换至 2025+ 的"需求过剩"</b>——数据中心电力、LNG 出口、电代煤三股力量拉动天然气消费（管理层指引 2031 年国内需求 150 Bcf/d，较当前 +27%）。瓶颈从"找买家"变成"建产能"，拥有走廊位置与完整网络的运营商获得定价权与合同溢价。</p>
<h3>2.2 同业全景对比</h3>
<table style="margin-top:6px">
<tr><th>公司</th><th>市值($B)</th><th>PE(TTM)</th><th>PB</th><th>股息率</th><th>ROE</th><th>β(5y)</th><th>定位</th></tr>
<tr><td><b>KMI</b> Kinder Morgan</td><td class="num">699</td><td class="num">20.3</td><td class="num">2.21</td><td class="num">3.8%</td><td class="num">11.0%</td><td class="num">0.54</td><td>天然气干线网络最广（78k 英里）</td></tr>
<tr><td>WMB Williams</td><td class="num">907</td><td class="num">29.5</td><td class="num">6.89</td><td class="num">2.8%</td><td class="num">18.8%</td><td class="num">0.87</td><td>高成长天然气旗舰（东向 LDC 权重高）</td></tr>
<tr><td>OKE ONEOK</td><td class="num">602</td><td class="num">16.5</td><td class="num">2.62</td><td class="num">4.4%</td><td class="num">16.4%</td><td class="num">0.73</td><td>NGL/集输一体化增长型</td></tr>
<tr><td>ET Energy Transfer</td><td class="num">737</td><td class="num">11.2</td><td class="num">1.38</td><td class="num">7.4%</td><td class="num">8.9%</td><td class="num">0.83</td><td>流量大、杠杆高、高分红（LP）</td></tr>
<tr><td>EPD Enterprise Products</td><td class="num">842</td><td class="num">11.3</td><td class="num">2.08</td><td class="num">6.4%</td><td class="num">16.7%</td><td class="num">0.76</td><td>NGL 综合平台、订单簿强（LP）</td></tr>
<tr><td>ENB Enbridge</td><td class="num">1096</td><td class="num">18.6</td><td class="num">2.32</td><td class="num">5.9%</td><td class="num">9.8%</td><td class="num">0.55</td><td>跨境输油+公用事业混合</td></tr>
</table>
<p class="note">来源：Yahoo Finance + 同花顺/东财快照（2026-09-04）；ET/EPD 为 MLP（LP）结构，KMI/WMB/OKE 为 C-Corp。</p>
<h3>2.3 竞争壁垒与相对优劣</h3>
<ul class="tight">
<li><b>网络广度 + 运力稀缺</b>：TGP 为美国最大州际天然气系统之一、直达东北部与路易斯安那 LNG 走廊；得州州内系统吃边际电价套利；El Paso 管道连接加州/亚利桑那数据中心与墨西哥出口——多走廊并行，单一需求源扰动不伤整体。</li>
<li><b>"纯天然气管网为主 + C-Corp 治理"的超级平台</b>：较 LP 无 K-1 税务复杂度，机构可投性更强；较 WMB 估值低近 1/3（20.3× vs 29.5×）。</li>
<li><b>增长位置</b>：$9.6B 已批准积压（92% 天然气、60%+ 服务电力/LDC），Trident（2027Q1）/MSX（2028）/SSE4（2029）三大项目按期在预算内。</li>
<li><b>弱势</b>：成长弹性不及 WMB/OKE（共识成长分 C）；成品油周期暴露（量 −5%）；碳转型敞口有限（RNG/CCS 相对整体规模偏小）。</li>
</ul>
</div>

<h2 id="s3">③ 核心财务：盈利质量与现金流结构</h2>
<div class="grid2">
  <div class="card"><h3>营收 / 营业利润 / 净利润（2018–2025，$B）</h3><div id="c1" class="chart"></div></div>
  <div class="card"><h3>经营现金流 / 资本开支 / 自由现金流（$B）</h3><div id="c2" class="chart"></div></div>
</div>
<div class="card">
<h3>年度关键指标（SEC XBRL, GAAP）</h3>
<table>
<tr><th>财年</th><th>营收($B)</th><th>净利率</th><th>OCF($B)</th><th>Capex($B)</th><th>FCF($B)</th><th>EPS($)</th><th>DPS($)</th><th>派息率</th><th>长期债务($B)</th></tr>
<tr><td>2018</td><td class="num">14.14</td><td class="num">11.4%</td><td class="num">5.04</td><td class="num">2.90</td><td class="num">2.14</td><td class="num">0.71</td><td class="num">0.80</td><td class="num">113%</td><td class="num">33.9</td></tr>
<tr><td>2019</td><td class="num">13.21</td><td class="num">16.6%</td><td class="num">4.75</td><td class="num">2.27</td><td class="num">2.48</td><td class="num">0.97</td><td class="num">1.00</td><td class="num">103%</td><td class="num">31.9</td></tr>
<tr><td>2020</td><td class="num">11.70</td><td class="num">1.0%</td><td class="num">4.55</td><td class="num">1.71</td><td class="num">2.84</td><td class="num">0.05</td><td class="num">1.05</td><td class="num">—</td><td class="num">32.1</td></tr>
<tr><td>2021</td><td class="num">16.61</td><td class="num">10.7%</td><td class="num">5.71</td><td class="num">1.28</td><td class="num">4.43</td><td class="num">0.79</td><td class="num">1.08</td><td class="num">137%</td><td class="num">30.7</td></tr>
<tr><td>2022</td><td class="num">19.20</td><td class="num">13.3%</td><td class="num">4.97</td><td class="num">1.62</td><td class="num">3.35</td><td class="num">1.13</td><td class="num">1.11</td><td class="num">98%</td><td class="num">28.4</td></tr>
<tr><td>2023</td><td class="num">15.33</td><td class="num">15.6%</td><td class="num">6.49</td><td class="num">2.32</td><td class="num">4.17</td><td class="num">1.08</td><td class="num">1.13</td><td class="num">105%</td><td class="num">28.1</td></tr>
<tr><td>2024</td><td class="num">15.10</td><td class="num">17.3%</td><td class="num">5.64</td><td class="num">2.63</td><td class="num">3.01</td><td class="num">1.18</td><td class="num">1.15</td><td class="num">97%</td><td class="num">29.9</td></tr>
<tr><td>2025</td><td class="num">16.94</td><td class="num">18.0%</td><td class="num">5.92</td><td class="num">3.03</td><td class="num">2.89</td><td class="num">1.37</td><td class="num">1.17</td><td class="num">85%</td><td class="num">30.8</td></tr>
</table>
<p class="note" style="margin-top:6px">注：2020 净利含疫情/低油价大额减值，派息率失真作"—"；EPS 按归属净利/期末摊薄股数近似；2024–25 股息对 OCF 覆盖约 2.0–2.3×。</p>
<h3>关键读数</h3>
<ul class="tight">
<li><b>2026H1 强劲</b>：H1 营收 $9.31B（+12.4% yoy）、归属净利 $1.84B（+28.7%）、OCF $3.45B（YTD，+22.8%）——增长来自管线量增与合同重定价而非商品价。</li>
<li><b>现金流自给</b>：Q2 单季 OCF $1.96B、FCF $978M、股息后 FCF 仍 +$313M；管理层明确"增长开支大部分由内部现金流融资"，净杠杆目标 3.6× 不动摇。</li>
<li><b>分红政策</b>：年化 $1.19（+2%），Q2 派 $0.2975（8/17 派付）；9 年连增、派息率降至 ~85% 可持续区间——管理层口径"内部融资增长 + 股息温和增长 + 杠杆回落"三位一体。</li>
</ul>
</div>
<div class="grid2">
  <div class="card"><h3>季度动量：单季营收/净利与营收同比（24Q1–26Q2）</h3><div id="c3" class="chart"></div></div>
  <div class="card"><h3>负债结构（截至 2026-06-30）</h3>
  <table style="margin-top:6px">
  <tr><th>指标</th><th>数值</th></tr>
  <tr><td>长期债务（非流动，XBRL）</td><td class="num">$307.8亿</td></tr>
  <tr><td>净债务（公司口径）</td><td class="num"><b>$320.3亿</b></td></tr>
  <tr><td>净债务 / 调整后 EBITDA</td><td class="num"><b>3.6×</b>（'25 末 3.8×）</td></tr>
  <tr><td>总负债 / 总资产</td><td class="num">55.6%</td></tr>
  <tr><td>在手现金</td><td class="num">$0.9亿</td></tr>
  <tr><td>信用评级</td><td class="num">穆迪 Baa1（'26-02 上调）/ 标普 BBB+</td></tr>
  <tr><td>利息覆盖（EBIT/利息，近似）</td><td class="num">≈3.5×</td></tr>
  </table>
  <p class="note">净杠杆为 2014 年合并以来最低；年底目标 3.6×（好于预算 3.8×）。评级上调 + 降息周期打开再融资成本下行与回购/提息空间。</p>
  </div>
</div>

<h2 id="s4">④ 估值分析</h2>
<div class="grid2">
  <div class="card"><h3>PE vs 股息率（中游同业散点）</h3><div id="c6" class="chart-sm"></div>
  <p class="note">Q2'26 财报后快照：KMI PE 20.3× / PB 2.21× / 股息率 3.76%；WMB 29.5× 为板块最贵（最高成长溢价）；ET/EPD LP 11–11.3× 为流量型折价。KMI 处于"成长溢价区与收息区之间"。</p></div>
  <div class="card"><h3>估值要点拆解</h3>
  <ul class="tight">
  <li><b>绝对估值</b>：PE(TTM) 20.3×，处自身 3 年区间（14–23×）中高位；Forward 2026E（指引上限，调整后 EPS ≈ $1.52–1.55）≈ 20.5–21.5×。</li>
  <li><b>与增速匹配</b>：2026E 调整后 EPS +12–15%、2027E 共识 +8–10% → PEG ≈ 1.4–1.7：不便宜但未泡沫化。</li>
  <li><b>股息视角</b>：3.79% 收益率 + 9 年连增 + 派息率 85%，"类债 + 成长"定价；低于 ET/EPD/OKE 收益率档、高于 WMB。</li>
  <li><b>EV/EBITDA</b>：EV ≈ $102B ÷ 2026E EBITDA ≈ $9.0B → <b>≈11.3×</b>，高于典型中游 8–10×，反映稀缺走廊溢价与评级上修。</li>
  <li><b>相对同业</b>：对 WMB 折价 31% 合理（增速/敞口差异）；对 OKE/ET/EPD 溢价主要来自 C-Corp + 纯天然气叙事，部分由 2.2× PB 支撑。</li>
  </ul></div>
</div>

<h2 id="s5">⑤ 股价走势与技术面</h2>
<div class="card"><h3>月度走势 2024-04 → 2026-09（未复权收盘）</h3><div id="c4" class="chart"></div></div>
<div class="grid2">
  <div class="card"><h3>核心技术指标（2026-09-04）</h3>
  <table>
  <tr><th>指标</th><th>数值</th><th>读解</th></tr>
  <tr><td>收盘价</td><td class="num">$31.40</td><td>箱体整理中</td></tr>
  <tr><td>SMA 20/50/100/200</td><td class="num">31.79/31.96/32.04/31.08</td><td>短期均线缠绕，仅 200 日下方 1.0%（中长期多头未破坏）</td></tr>
  <tr><td>RSI(14)</td><td class="num">46.0</td><td>中性偏弱，无超买超卖</td></tr>
  <tr><td>MACD(12,26,9)</td><td class="num">DIF −0.06/DEA −0.06/柱 +0.01</td><td>水下柱状翻红、弱势金叉初现（30 日前柱 −0.28 大幅收敛）</td></tr>
  <tr><td>布林(20,2)</td><td class="num">30.69–32.88</td><td>中轨下方，波动收窄</td></tr>
  <tr><td>52 周高/低</td><td class="num">34.49/25.84</td><td>距高 −8.5%、距低 +21.5%</td></tr>
  <tr><td>60 日趋势斜率</td><td class="num">年化 −7.1%</td><td>5 月见顶后下行整理</td></tr>
  <tr><td>YTD/1Y/3Y</td><td class="num">+13.3%/+18.1%/+82.3%</td><td>中期动量强、短期休整（含息口径 YTD +17.4%）</td></tr>
  </table>
  <p class="note">行情为新浪未复权；技术判读以价格行为为准。</p></div>
  <div class="card"><h3>支撑 / 阻力位</h3>
  <table>
  <tr><th>层级</th><th>价位</th><th>性质</th></tr>
  <tr><td>阻力 R1</td><td class="num">32.9–33.2</td><td>20/60 日高点 + 布林上轨</td></tr>
  <tr><td>阻力 R2</td><td class="num">34.3–34.5</td><td>52 周高（24/05/19）</td></tr>
  <tr><td>支撑 S1</td><td class="num">30.85–30.94</td><td>近 20/60 日低点密集区（6–9 月三度确认）</td></tr>
  <tr><td>支撑 S2</td><td class="num">29.3–29.7</td><td>2 月跳空缺口上沿</td></tr>
  <tr><td>支撑 S3</td><td class="num">27.5–28.0</td><td>250 日均线带（深度回调防御）</td></tr>
  </table>
  <p><b>形态判读</b>：30.85–32.9 箱体已持续约 4 个月（6 月至今），下沿三度测试未破、量能未见出逃；MACD 柱状转正在箱底附近出现"弱企稳"。<b>向上突破需 32.9 上方放量</b>（配合 Q4 财报/证书催化），<b>向下跌破 30.85 则看 29.3–29.7</b>（约 −5%）。</p></div>
</div>
<div class="card"><h3>同业表现对比（未复权，%）</h3><div id="c5" class="chart-sm"></div>
<p class="note">KMI 今年跑输绝大多数同业（除 ENB）：2025 年涨幅已大（3Y +82%）、资金偏好高成长天然气标的（WMB/OKE/ET）。绝对动量仍正、相对动量偏弱——"基本面不差、资金面不抢"阶段。</p></div>

<h2 id="s6">⑥ 增长动力与潜在风险</h2>
<div class="grid2">
<div class="card"><h3>增长动力（偏多）</h3>
<ul class="tight">
<li><b>项目积压兑现（核心）</b>：$9.6B 已批准积压（92% 天然气），首年 EBITDA 倍数约 5.6×；Trident 2027Q1 → MSX 2028 → SSE4 2029 依次投产，把合同化订单转 EBITDA；机会集 >$10B，H2 预期再批大额项目抵消在运 ~$1B。</li>
<li><b>电力需求第二曲线</b>：数据中心/电气化拉动燃气发电；积压 >60% 服务电力/LDC；Amarillo Expansion（$200M，服务德州数据中心、全额签约）已进入执行。</li>
<li><b>LNG 出口乘数</b>：服务约 3 Bcf/d 新增 LNG 需求 + >10 Bcf/d 开发中电力需求；EIA 上调 2026 出口至 17.0 Bcf/d，TGP 直达路易斯安那走廊。</li>
<li><b>财务弹性</b>：杠杆 3.6× 历史最低 + Baa1 + 65% 照付不议合同锁现金流 → 再融资成本下行、回购/提息空间打开。</li>
<li><b>政策顺风</b>：FERC 审批提速、EPA 电厂规则二审预期撤回 CCS 要求、LNG 非 FTA 授权持续放量。</li>
</ul></div>
<div class="card"><h3>潜在风险（需跟踪）</h3>
<ul class="tight">
<li><b>增长"时间差"（核心空头论点）</b>：EBITDA 增量集中在 2028+，2026H2–2027 为青黄不接期——共识预期 2026Q4 EBITDA 同比或小幅转负；若 Q3/Q4 弱于新预期，股价回撤风险。</li>
<li><b>天然气现货疲弱</b>：HH 低位压缩 E&P 投入 → 集输量斜率放缓；储气/授权费承压。</li>
<li><b>利率敏感</b>：长久期资产，10Y 上行 100bp 可压缩中游 EV/EBITDA 约 0.5–1×，"类债"替代溢价消失。</li>
<li><b>关税/通胀</b>：钢铝关税推材料成本 +4–40%（Deloitte），在建项目或超支。</li>
<li><b>监管残余</b>：MSX/SSE4 证书批复原定 7 月底、实际延迟至 9 月未最终落定——需逐项跟踪。</li>
<li><b>需求逆风</b>：成品油量 −5%、原油量 −16%；若油价持续走弱，商品挂钩收入侵蚀合同利润。</li>
<li><b>估值不便宜</b>：20.3× TTM 未完全反映青黄不接期增速放缓——市场对 2026 指引的乐观已部分定价。</li>
</ul></div>
</div>

<h2 id="s7">⑦ 宏观经济与能源政策影响</h2>
<div class="card">
<h3>7.1 天然气需求宏观</h3>
<p>管理层指引 2031 年需求 150 Bcf/d（+27%），驱动 = 电力（数据中心）/LNG 出口/工业电气化。EIA 2026-04 STEO：LNG 出口上调至 <b>17.0 Bcf/d</b>（1 月 16.4），终端利用率近满负荷；2025–26 新增出口产能约 5 Bcf/d（Plaquemines、Corpus Christi 3 期）。对 KMI：<b>出口与电厂需求是"量"的发动机，气价本身对收入影响有限</b>（65% 合同化 + 50% 脱钩价）。</p>
<h3>7.2 政策环境（2026 年实际演变，整体转顺）</h3>
<table>
<tr><th>政策/事件</th><th>状态</th><th>对 KMI 含义</th></tr>
<tr><td>FERC NGA §7 证书审批</td><td>2026 提速；MSX/SSE4 于 6/26 获最终 EIS，证书原预期 7 月底、截至 9 月初未最终落定（延迟）</td><td>项目排期是最大单一跟踪变量</td></tr>
<tr><td>EPA 电厂规则（2024 版 CCS 要求）</td><td>二审重审推进，预期 2026H2 终局，撤回 CCS 概率高</td><td>解除新燃气电厂成本压制 → 结构性利多管道需求</td></tr>
<tr><td>LNG 审批（DOE 非 FTA 授权）</td><td>持续放量（如 Plaquemines +0.5 Bcf/d）</td><td>利多 Gulf Coast 走廊管输/储气</td></tr>
<tr><td>关税（钢铝）</td><td>2026 落地，材料成本 +4–40%</td><td>在建项目成本风险（多为已签约 EP&C 模式，可控）</td></tr>
<tr><td>利率（10Y）</td><td>高位平台、降息路径未明</td><td>估值分母 —— 主要估值天花板</td></tr>
</table>
<h3>7.3 利率敏感性与融资</h3>
<p>中游资产久期长（合同 10–20 年），股价对 10Y 高度敏感（本报告引用历史观测：KMI×DGS10 区间相关约 −0.5，<b>未单独重跑、方向性参考</b>）。对冲项：3.6× 低杠杆 + Baa1 → 假设 10Y −50bp，$30B 债务重定价年省利息约 $1.5–2 亿，可部分转增 EPS——<b>降息周期是 KMI 估值倍数上修的最大宏观触发</b>。</p>
<p class="note">政策状态来自 2026 年上半年公开报道（EIA STEO 4 月、energycentral/Oilprice 政策简报、Consilium 综述），截至 2026-09-06 为最新可得。</p>
</div>

<h2 id="s8">⑧ 投资观点</h2>
<div class="card" style="border-left:5px solid var(--blue)">
<h3>8.1 综合评级与目标价</h3>
<table>
<tr><th>项目</th><th>结论</th><th>依据</th></tr>
<tr><td><b>投资评级</b></td><td><span class="badge">增持 / Accumulate（12 个月）</span></td><td>基本面（Q2 创纪录、指引二度上调、杠杆新低）强于短期青黄不接 + 估值不便宜的约束；较"买入"略保守</td></tr>
<tr><td><b>12 个月目标价</b></td><td><span class="vrating">$33.5 – $35.5</span>（中枢 ≈$34.5）</td><td>2027E EBITDA ~$9.4–9.6B × 11–11.5× EV/EBITDA 折算 + 股息；对应上行 +6.7%–13.1%，含息总回报 +10.4%–16.8%</td></tr>
<tr><td>乐观情景</td><td>$37–39</td><td>证书快速落定 + H2 新积压落地 + 10Y 回落 → 2027E 12×+</td></tr>
<tr><td>悲观情景</td><td>$29–30</td><td>Q3/4 EBITDA 转负坐实 + 证书再延迟 + 10Y 上行 → 回归 9.5–10×</td></tr>
</table>
<p class="note" style="margin-top:6px">共识参考（2026-09 聚合）：18–24 家机构均价目标 $35.9–36.3（隐含 +14–15%），最高 $43 / 最低 $31–32；54% 买入/增持、46% 持有、0 减持。本目标价中枢略低于街平均：技术面未确认突破 + 2026H2 增速放缓预期。</p>
</div>
<div class="card">
<h3>8.2 分风险偏好操作建议</h3>
<table>
<tr><th>投资者类型</th><th>操作建议</th><th>逻辑</th></tr>
<tr><td><b>稳健 / 收息型</b></td><td><b>分批建仓：现价可 1/3 底仓</b>，≤31 加至 1/2，30.8 失守暂停观望</td><td>3.8% 股息 + 9 年连增 + 杠杆新低，下行保护充分；类债替代价值在利率企稳期显著</td></tr>
<tr><td><b>均衡 / 核心配置型</b></td><td><b>区间策略：30.9 附近吸、33.0 减仓兑现、放量突破 33.2 回补</b></td><td>30.85–32.9 箱体 4 个月，高抛低吸兼顾股息，突破确认再追趋势</td></tr>
<tr><td><b>进取 / 交易型</b></td><td><b>事件驱动</b>：跟踪 FERC 证书与 Q3 财报（10 月中旬），催化前布局、落空离场；止损 30.8</td><td>催化剂集中在 H2：证书、新积压公告、潜在回购；波动窗口在 10 月财报前后</td></tr>
<tr><td><b>不建议</b></td><td>当前 31.4 追涨</td><td>距箱体上沿仅 +5%、H2 增速环比放缓、技术未突破——追涨性价比低</td></tr>
</table>
</div>
<div class="card">
<h3>8.3 关键跟踪清单（按重要性）</h3>
<ol>
<li><b>FERC MSX/SSE4 证书批复</b>（原定 7 月底已延迟——9 月落定概率大）→ 消除积压转化最大不确定性</li>
<li><b>Q3'26 财报（10 月中旬）</b>：EBITDA 环比是否如共识放缓、指引是否三度上调</li>
<li><b>新积压公告</b>：H2 预期新增 >$1B（净抵消在运）</li>
<li><b>净负债/EBITDA 季度读数</b>：3.6× 若再降 → 回购/提息预期升温</li>
<li><b>10Y 收益率 & EIA 月度 LNG 出口</b>（市场 β 与行业 β）</li>
</ol>
</div>

<h2 id="s9">⑨ 数据来源与时效性</h2>
<div class="card">
<table>
<tr><th>数据</th><th>来源</th><th>时效</th></tr>
<tr><td>年度/季度财务（GAAP）</td><td>SEC XBRL companyconcept（10-K/10-Q, CIK 0001506307）</td><td>截至 2026-06-30（Q2'26 10-Q）</td></tr>
<tr><td>非 GAAP（调整 EBITDA/EPS、净债务、积压、指引）</td><td>KMI Q1/Q2'26 财报新闻稿（IR 官网）</td><td>2026-07-22 发布</td></tr>
<tr><td>股价/技术面</td><td>新浪美股日线（未复权）</td><td>截至 2026-09-04 收盘</td></tr>
<tr><td>含息总回报/市值/PE/PB/股息率</td><td>Yahoo Finance 行情快照</td><td>2026-09-04</td></tr>
<tr><td>机构评级/目标价/估值矩阵</td><td>同花顺·东财聚合、MarketBeat、TIKR 博文引用</td><td>2026-08 ~ 09</td></tr>
<tr><td>行业/政策（EIA、FERC、EPA、关税）</td><td>EIA 4 月 STEO、Oilprice/energycentral 政策简报、Consilium 2026 综述</td><td>2026 年上半年发布</td></tr>
</table>
<p style="margin-top:10px" class="note"><b>数据纪律说明</b>：① 财务主口径为 SEC XBRL 原始值，未经第三方加工；② 分析师目标价/评级为公开聚合数据，非个人推荐；③ 行情为未复权价，含息口径引 Yahoo 并已注明；④ 2020 年净利受减值影响、2026Q4 无数据，结论已作相应收敛；⑤ "KMI×DGS10 负相关 ≈−0.5" 为本项目历史观测引用、未在本报告重跑，属<b>未核实引用</b>，仅作方向性参考。</p>
</div>

<div class="disclaimer">
<b>免责声明</b>：本报告仅为研究用途，不构成任何证券买卖建议。目标价为情景推演结果，实际走势受宏观、监管与公司执行影响可能显著偏离。作者不持有 KMI 头寸。过往表现不代表未来收益。
</div>

<div class="foot">
81 · 金德摩根（KMI）全面深度分析 ｜ 报告日 2026-09-06 ｜ 数据截至 2026-09-04 收盘 ｜ 由 WorkBuddy 生成
</div>
</div>
<script>
const OKABE = ['#0072B2','#E69F00','#56B4E9','#009E73','#CC79A7','#D55E00','#F0E442','#000000'];
const UP = '#C0392B', DOWN = '#1E8449';

var c1 = echarts.init(document.getElementById('c1'));
c1.setOption({
  tooltip:{trigger:'axis'}, legend:{data:['营收','营业利润','净利润']},
  grid:{left:55,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:@@YEARS@@},
  yAxis:{type:'value',name:'$B',nameTextStyle:{color:'#5b6672'}},
  series:[
    {name:'营收',type:'bar',data:@@REV@@,itemStyle:{color:OKABE[0]},barWidth:'36%'},
    {name:'营业利润',type:'line',data:@@OP@@,itemStyle:{color:OKABE[1]},lineStyle:{width:2.5}},
    {name:'净利润',type:'line',data:@@NI@@,itemStyle:{color:OKABE[2]},lineStyle:{width:2.5,dash:[4,3]}}
  ]
});

var c2 = echarts.init(document.getElementById('c2'));
c2.setOption({
  tooltip:{trigger:'axis'}, legend:{data:['经营现金流','资本开支','自由现金流']},
  grid:{left:55,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:@@YEARS@@},
  yAxis:{type:'value',name:'$B'},
  series:[
    {name:'经营现金流',type:'bar',data:@@OCF@@,itemStyle:{color:OKABE[0]},barWidth:'30%'},
    {name:'资本开支',type:'bar',data:@@CAPX@@,itemStyle:{color:OKABE[4]},barWidth:'30%'},
    {name:'自由现金流',type:'line',data:@@FCF@@,itemStyle:{color:OKABE[1]},lineStyle:{width:2.5}}
  ]
});

var c3 = echarts.init(document.getElementById('c3'));
c3.setOption({
  tooltip:{trigger:'axis'}, legend:{data:['单季营收','单季净利润','营收同比%']},
  grid:{left:55,right:45,top:40,bottom:30},
  xAxis:{type:'category',data:@@Q_NAMES@@},
  yAxis:[{type:'value',name:'$B',nameTextStyle:{color:'#5b6672'}},{type:'value',name:'%',min:-10,max:35,splitLine:{show:false}}],
  series:[
    {name:'单季营收',type:'bar',data:@@Q_REV@@,itemStyle:{color:OKABE[0]},barWidth:'38%'},
    {name:'单季净利润',type:'bar',data:@@Q_NI@@,itemStyle:{color:OKABE[5]},barWidth:'38%'},
    {name:'营收同比%',type:'line',yAxisIndex:1,data:@@Q_YOY@@,itemStyle:{color:OKABE[2]},lineStyle:{width:2}}
  ]
});

var c4 = echarts.init(document.getElementById('c4'));
var evMark = [
  {name:'穆迪上调Baa1', coord:['2026-02',31.0], value:31.0},
  {name:"Q1'26财报·上调指引", coord:['2026-04',33.0], value:32.87},
  {name:'52周高34.49', coord:['2026-05',34.0], value:34.49},
  {name:"Q2'26财报·创纪录", coord:['2026-07',33.2], value:32.18}
];
c4.setOption({
  tooltip:{trigger:'axis'},
  grid:{left:45,right:140,top:30,bottom:30},
  xAxis:{type:'category',data:@@MON_DATES@@,boundaryGap:false},
  yAxis:{type:'value',name:'$',min:17,max:36},
  series:[
    {type:'line',data:@@MON_VALS@@,smooth:true,symbol:'none',lineStyle:{color:OKABE[0],width:2.5},areaStyle:{color:'rgba(0,114,178,0.08)'}},
    {type:'scatter',data:evMark,symbolSize:9,itemStyle:{color:UP},label:{show:true,formatter:function(p){return p.name},position:'right',fontSize:11,color:'#26313d'}},
    {type:'line',silent:true,symbol:'none',lineStyle:{color:'#9a948a',type:'dashed'},data:[[0,34.49],[100,34.49]],markLine:{silent:true,symbol:'none',label:{fontSize:10}}}
  ]
});

var c5 = echarts.init(document.getElementById('c5'));
c5.setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{data:['YTD','1年','3年']},
  grid:{left:90,right:30,top:40,bottom:30},
  xAxis:{type:'value'},
  yAxis:{type:'category',data:@@PEER_NAMES@@},
  series:[
    {name:'YTD',type:'bar',data:@@PEER_YTD@@,itemStyle:{color:OKABE[0]},barWidth:9},
    {name:'1年',type:'bar',data:@@PEER_Y1@@,itemStyle:{color:OKABE[1]},barWidth:9},
    {name:'3年',type:'bar',data:@@PEER_Y3@@,itemStyle:{color:OKABE[2]},barWidth:9}
  ]
});

var c6 = echarts.init(document.getElementById('c6'));
c6.setOption({
  tooltip:{formatter:function(p){return p.name+'<br/>PE: '+p.value[0]+'×<br/>股息率: '+p.value[1]+'%'}},
  grid:{left:50,right:30,top:30,bottom:40},
  xAxis:{type:'value',name:'PE (TTM)',min:8,max:34},
  yAxis:{type:'value',name:'股息率 %',min:0,max:8},
  series:[
    {type:'scatter',data:@@VAL_SCATTER@@,symbolSize:16,itemStyle:{color:OKABE[0]},label:{show:true,formatter:function(p){return p.name},position:'top',fontSize:11,color:'#26313d'}}
  ]
});

window.addEventListener('resize', function(){ [c1,c2,c3,c4,c5,c6].forEach(function(ch){ch.resize();}); });
</script>
</body>
</html>
"""

html = fill(HTML_TPL)

# 校验残留占位符
import re
leftover = re.findall(r"%\([A-Z_]+\)s", html)
if leftover:
    print("WARN leftover placeholders:", set(leftover))

with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("written:", os.path.join(OUT_DIR, "index.html"), len(html), "bytes")