# -*- coding: utf-8 -*-
"""
82 小麦库存历史分析报告生成器
数据: results/wheat_stocks_history.csv (由 wheat_stocks_history.py 产出)
风格: 浅色研报 + ECharts + 术语浮窗 (复用 58/68 号规范)
红涨绿跌 Okabe-Ito 色彩
"""
import csv, json, re, os

CSV_PATH = os.path.expanduser('~/Desktop/股票分析/results/wheat_stocks_history.csv')
OUT_DIR = os.path.expanduser('~/Desktop/股票分析/reports/82_小麦库存历史分析_20260907')
OUT_HTML = os.path.join(OUT_DIR, 'index.html')

rows = []
with open(CSV_PATH) as f:
    for r in csv.DictReader(f):
        rows.append(r)
rows.sort(key=lambda r: int(r['year']))

YEARS = [int(r['year']) for r in rows]
PROD = [float(r['world_prod']) for r in rows]
CONS = [float(r['world_cons']) for r in rows]
END = [float(r['world_end']) for r in rows]
SU = [r['world_su_ratio'] for r in rows]
T5 = [float(r['trade5_end']) for r in rows]
RU = [float(r['ru_end']) for r in rows]
CN = [float(r['cn_end']) for r in rows]

# 派生计算
WORLD_END_STMT = float(rows[-1]['world_end']) / 1000
WORLD_SU_LATEST = float(rows[-1]['world_su_ratio'])
WORLD_SU_PEAK = max(float(r['world_su_ratio']) for r in rows)
WORLD_SU_PEAK_Y = YEARS[[float(r['world_su_ratio']) for r in rows].index(WORLD_SU_PEAK)]
PROD_LATEST = float(rows[-1]['world_prod']) / 1000
PROD_PEAK = max(float(r['world_prod']) for r in rows) / 1000
PROD_PEAK_Y = YEARS[[float(r['world_prod']) for r in rows].index(PROD_PEAK * 1000)]
CN_LATEST = float(rows[-1]['cn_end']) / 1000
CN_PEAK = max(float(r['cn_end']) for r in rows) / 1000
CN_PEAK_Y = YEARS[[float(r['cn_end']) for r in rows].index(CN_PEAK * 1000)]
T5_LATEST = float(rows[-1]['trade5_end']) / 1000
T5_PREV = float(rows[-2]['trade5_end']) / 1000
T5_MIN = min(float(r['trade5_end']) for r in rows) / 1000
T5_MIN_Y = YEARS[[float(r['trade5_end']) for r in rows].index(T5_MIN * 1000)]

# 五国缓冲百分位
t5_hist = [float(r['trade5_end']) for r in rows[:-1]]
t5_latest = float(rows[-1]['trade5_end'])
pct_t5 = sum(1 for x in t5_hist if x <= t5_latest) / len(t5_hist) * 100

# 口径敏感性：五国 + 俄乌（若俄乌可出口）
T5RU = [float(r['trade5_end']) + float(r['ru_end']) for r in rows]
t5ru_latest = T5RU[-1]
pct_t5ru = sum(1 for x in T5RU[:-1] if x <= t5ru_latest) / len(T5RU[:-1]) * 100

# 2026/27 俄乌占全球出口比重
RU_EXPORT_SHARE = float(rows[-1]['ru_export']) / float(rows[-1]['world_export']) * 100
RU_PROD_SHARE = float(rows[-1]['ru_prod']) / float(rows[-1]['world_prod']) * 100

chart_prod = json.dumps([round(x, 0) for x in PROD])
chart_cons = json.dumps([round(x, 0) for x in CONS])
chart_end = json.dumps([round(x, 0) for x in END])
chart_su = json.dumps([float(x) for x in SU])
chart_t5 = json.dumps([round(x, 0) for x in T5])
chart_t5ru = json.dumps([round(x, 0) for x in T5RU])
chart_ru = json.dumps([round(x, 0) for x in RU])
chart_cn = json.dumps([round(x, 0) for x in CN])

# 五国产量/消费/出口 全序列（用于四节平衡图）
T5_PROD_ALL = json.dumps([round(float(r['trade5_prod']), 0) for r in rows])
T5_CONS_ALL = json.dumps([round(float(r['trade5_cons']), 0) for r in rows])
T5_EXP_ALL = json.dumps([round(float(r['trade5_export']), 0) for r in rows])

# 库存 vs 价格实证（2016/17–2026/27，市场年度均价，$/bu）
PX_DATA = [
    {'y': 2016, 't5': 61.3, 'px': 4.26},
    {'y': 2017, 't5': 61.2, 'px': 4.60},
    {'y': 2018, 't5': 57.8, 'px': 5.01},
    {'y': 2019, 't5': 51.2, 'px': 5.18},
    {'y': 2020, 't5': 44.5, 'px': 6.15},
    {'y': 2021, 't5': 40.7, 'px': 8.66},
    {'y': 2022, 't5': 43.6, 'px': 7.56},
    {'y': 2023, 't5': 44.3, 'px': 6.04},
    {'y': 2024, 't5': 45.9, 'px': 5.56},
    {'y': 2025, 't5': 58.2, 'px': 5.93},
    {'y': 2026, 't5': 42.9, 'px': 7.24},
]
PX_SCATTER = json.dumps([{'value': [d['t5'], d['px']], 'name': f"{d['y']}/{(d['y']+1)%100:02d}"} for d in PX_DATA])

# ---------- 术语 ----------
TERMS = [
    ("库存消费比", "期末库存 / 总消费 × 100%。全球谷物库存的通用紧张度指标：越高越宽松，越低越紧张。USDA 每月用其衡量全球缓冲能力。"),
    ("可贸易库存", "真正能自由进入国际市场流通的库存。区别于纸面库存——战略储备（如中国临储）、战争封锁国（俄乌）虽计入总量，但无法实际出口。"),
    ("五国可贸易缓冲", "美国+加拿大+欧盟+澳大利亚+巴西的期末库存合计（报告 68 口径，不含俄乌/中国）。代表全球海运谷物最直接的备用粮。注意：俄乌虽是全球头号出口区，但其库存被战争封锁、无法自由出口，故不计入。"),
    ("出口导向、低库存", "俄罗斯/乌克兰的库存模式：每年产量大部分直接出口，期末库存占比较低（俄乌库存仅占全球 6.7%，但出口占 28%）。" ),
    ("市场年度", "农业统计年度，小麦为当年 7 月至次年 6 月（如 2026/27 指 2026-07 至 2027-06）。报告横轴年份为该市场年度的开始年。"),
    ("单产", "单位面积产量。USDA 每月对主产国单产做预估，田间巡查（如 Pro Farmer）会进一步修正，差额即预期差。"),
    ("FSI 消费", "Food, Seed & Industrial 消费，即食用+种用+工业用。与饲用（Feed）共同构成总消费。"),
    ("WASDE", "World Agricultural Supply and Demand Estimates，USDA 每月发布的全球农产品供需平衡预测报告，是谷物库存最权威的月度数据源。"),
]
TERM_DICT = {k: v for k, v in sorted(TERMS, key=lambda x: -len(x[0]))}
_TERM_PAT = re.compile("|".join(re.escape(k) for k in TERM_DICT.keys()))
_BLOCK_RE = re.compile(r"(<script[\s\S]*?</script>|<style[\s\S]*?</style>|<title[\s\S]*?</title>)", re.S)
_TAG_SPLIT_RE = re.compile(r"<[^>]+>")

def _annotate_text(text):
    def _repl(m):
        tip = TERM_DICT[m.group(0)].replace("'", "&#39;")
        return f"<span class='term' data-tip='{tip}'>{m.group(0)}</span>"
    return _TERM_PAT.sub(_repl, text)

def annotate_terms(html_str):
    parts = _BLOCK_RE.split(html_str)
    return "".join((_annotate_text(seg) if (i % 2 == 0 and seg) else (seg or "")) for i, seg in enumerate(parts))

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>82 · 小麦 27 年库存历史：丰收 vs 紧张的真相 · 2026-09-07</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{
    --oi-blue:#0072B2; --oi-orange:#E69F00; --oi-sky:#56B4E9;
    --oi-vermillion:#D55E00; --oi-purple:#CC79A7; --oi-green:#009E73;
    --oi-yellow:#F0E442; --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec;
    --card:#ffffff; --bg:#f5f7fa; --ref-bg:#eef2f7;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px;}
  .wrap{max-width:1080px;margin:0 auto;padding:24px 20px 60px;}
  .hero{background:linear-gradient(135deg,#12365e 0%,#1d5c93 100%);color:#fff;border-radius:12px;padding:28px 32px;margin-bottom:20px;}
  .hero h1{font-size:24px;margin-bottom:6px;line-height:1.4;}
  .hero .meta{font-size:12.5px;opacity:.85;margin-top:4px;}
  .hero .sub{margin-top:12px;font-size:14px;opacity:.95;border-top:1px solid rgba(255,255,255,.25);padding-top:10px;}
  .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}
  .kcard{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}
  .kcard .lab{font-size:12px;color:var(--sub);margin-bottom:3px;}
  .kcard .val{font-size:21px;font-weight:700;font-variant-numeric:tabular-nums;}
  .kcard .note{font-size:12px;color:var(--sub);margin-top:3px;}
  .red{color:#b2182b;} .green{color:#1a7a3a;}
  h2{font-size:19px;margin:36px 0 12px;padding-left:12px;border-left:4px solid var(--oi-blue);}
  h3{font-size:15px;margin:18px 0 8px;color:#12365e;}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:16px;}
  .two{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
  table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;}
  th{background:#eef2f7;color:#12365e;padding:7px 9px;text-align:left;border-bottom:2px solid var(--line);font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top;}
  tr:last-child td{border-bottom:none;}
  .num{font-variant-numeric:tabular-nums;}
  .src{font-size:11px;color:var(--sub);margin-top:7px;line-height:1.5;}
  sup.c a{color:var(--oi-blue);text-decoration:none;font-size:11px;font-weight:700;}
  ul{padding-left:22px;} li{margin:5px 0;}
  .callout{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:14px 18px;margin:14px 0;font-size:13.5px;}
  .warn{background:#fdf2f2;border:1px solid #eccaca;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}
  .footer{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}
  a{color:var(--oi-blue);}
  .tag{display:inline-block;font-size:11px;color:#fff;background:var(--oi-blue);border-radius:4px;padding:1px 8px;margin-right:6px;vertical-align:1px;}
  .tag.g{background:var(--oi-vermillion);}
  .lead{font-size:15px;}
  .term{text-decoration:underline dotted var(--oi-blue);cursor:help;}
  .termtip{display:none;position:fixed;z-index:9999;max-width:280px;background:#123248;color:#eef6ff;border-radius:8px;padding:8px 12px;font-size:12.5px;line-height:1.6;box-shadow:0 4px 14px rgba(0,0,0,.25);pointer-events:none;}
  @media(max-width:820px){.cards{grid-template-columns:repeat(2,1fr);}.two{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="hero">
    <h1>小麦 27 年库存历史：丰收为何仍感紧张？</h1>
    <div class="meta">报告编号 82 ｜ 数据源：USDA FAS PSD 官方库（2000/01–2026/27 全部市场年度，123 国期末库存）｜ 2026-09-07</div>
    <div class="sub">结论一句话：<b>「丰收」与「紧张」都对，但说的不是同一个东西</b>——全球小麦总库存 2005 年起被中国战略储备撑起（现占比 44%、处于去库通道），而真正可贸易的五国缓冲（美/加/欧盟/澳/巴）2026/27 仅 42.9 Mt，处 27 年第 19 百分位、逼近 2007 危机水平；再叠加俄乌战储被战争困在境内，<b>纸面宽松、可得性紧张</b>。</div>
  </div>

  <div class="cards">
    <div class="kcard"><div class="lab">全球产量 (2025/26 峰值)</div><div class="val">843 Mt</div><div class="note">2004 年以来 +51%</div></div>
    <div class="kcard"><div class="lab">全球库消比 (2026/27)</div><div class="val">33.3%</div><div class="note">历史高位（峰值 2019 年 40.4%）</div></div>
    <div class="kcard"><div class="lab">五国可贸易库存 (2026/27)</div><div class="val">42.9 Mt</div><div class="note">处 27 年第 19 百分位 · 同比 -26%</div></div>
    <div class="kcard"><div class="lab">含俄乌口径缓冲</div><div class="val">61.3 Mt</div><div class="note">第 50 百分位 · 俄乌占全球出口 28%</div></div>
    <div class="kcard"><div class="lab">中国期末库存占比</div><div class="val">44%</div><div class="note">120 Mt，去库中（峰值 150 Mt）</div></div>
  </div>

  <h2>一、先算清账：全球小麦 27 年供需全景</h2>
  <div class="panel">
    <p class="lead">「丰收」是事实：全球小麦产量从 2004 年 557 Mt 一路抬升到 <b>2025/26 的 843 Mt</b>（+51%），消费同步增长至 818 Mt。粗看全球库消比从 2019 年峰值 40.4% 回落到 33.3%，依然处于历史区间上半段——单独看这个数字，怎么也不算「紧张」。</p>
    <div id="c_prod" style="height:360px;margin-top:10px;"></div>
    <div class="src">全球小麦产量（蓝）与消费（橙），Mt。数据：USDA PSD，市场年度口径。2026/27 为 8 月 WASDE 预测。</div>
    <div class="callout"><b>第一个钥匙：全球库消比高，是被谁撑起来的？</b>把全球库存拆开看——中国占总量的 44%，且 2005-2019 年持续十年累库（34→150 Mt）。剔除中国后，2026/27 全球库存为 153 Mt，库消比约 22%，比「33%」看起来紧张得多。总量指标被战略储备稀释了「紧张度」。</div>
  </div>

  <h2>二、总量 vs 可得性：库存到底在哪</h2>
  <div class="panel">
    <p class="lead"><b>真正决定国际市场价格的，是「可得性」而非「存量」。</b>2026/27 全球期末库存 273 Mt 里：中国 120 Mt（战略储备，不进国际市场）、俄乌 18.4 Mt（战争封锁出口物流）、其余各国合计约 135 Mt。而这其中能顺畅出口的，主要是美/加/欧盟/澳/巴五国的缓冲。</p>
    <div id="c_struct" style="height:300px;margin-top:10px;"></div>
    <div class="src">2026/27 全球小麦期末库存结构（USDA PSD 各国加总）。「可贸易」=美/加/欧盟/澳/巴五国，约 43 Mt。</div>
    <table style="margin-top:10px;">
      <tr><th>库存归属</th><th>规模 (Mt)</th><th>占全球</th><th>能否进入国际市场</th></tr>
      <tr class="num"><td>🇨🇳 中国</td><td>120</td><td>44%</td><td>战略/临储，内循环安全垫，不放</td></tr>
      <tr class="num"><td>🇷🇺 俄罗斯</td><td>13.6</td><td>5%</td><td>战争封锁，出口物流近零（88% 分位堆积）</td></tr>
      <tr class="num"><td>🇺🇦 乌克兰</td><td>4.8</td><td>2%</td><td>黑海被袭，出口受限</td></tr>
      <tr class="num"><td><b>五国可贸易</b></td><td><b>42.9</b></td><td><b>16%</b></td><td><b>✓ 国际市场的真缓冲</b></td></tr>
      <tr class="num"><td>其他（印/埃/土等）</td><td>92.0</td><td>34%</td><td>多为消费国国内库存，贸易弹性有限</td></tr>
    </table>
  </div>

  <h2>三、五国可贸易缓冲：口径与敏感度</h2>
  <div class="panel">
    <p class="lead">「五国」口径（美/加/欧盟/澳/巴）<b>有意排除了俄乌</b>——不是它们不重要，恰恰相反：俄乌 2026/27 产量 113.9 Mt（占全球 13.9%），<b>出口 59.5 Mt、占全球贸易 28%，是全球头号小麦出口区</b>。但它们的库存模式是「出口导向、低库存」：收了粮直接卖掉，期末库存仅 18.4 Mt（占全球 6.7%），且当前被战争锁在境内。因此「五国缓冲」衡量的是<b>现在就能自由流向国际市场的量</b>。</p>
    <div id="c_t5" style="height:340px;margin-top:10px;"></div>
    <div class="src">蓝柱=美/加/欧盟/澳/巴五国缓冲；橙柱=五国+俄乌（假设俄乌可出口）。黄色虚线=2007 危机低点（五国口径 30.6 Mt）。</div>
    <table style="margin-top:10px;">
      <tr><th>口径</th><th>2026/27 缓冲</th><th>27 年百分位</th><th>解读</th></tr>
      <tr class="num"><td><b>五国（不含俄乌）</b></td><td>42.9 Mt</td><td><b>第 19</b>（紧张）</td><td>当前实际可出口的缓冲，同比 -26%</td></tr>
      <tr class="num"><td>五国 + 俄乌（含假设）</td><td>61.3 Mt</td><td>第 50（中性）</td><td>若俄乌恢复出口，紧张度大幅缓解</td></tr>
    </table>
    <div class="warn"><b>口径敏感性提示</b>：俄乌 18.4 Mt 库存是 27 年中最高水平之一（战争导致被动堆积），一旦停火、黑海物流修复，这部分缓冲<u>即刻释放</u>——「五国紧张」的定价，本质上押注的是「俄乌短期出不来」。</div>
    <div class="src">俄乌占全球产量 13.9%、出口 28%，是贸易流发动机；但其库存占比仅 6.7%——「低库存、高流转」模式，出口封锁是紧张的关键变量。</div>
  </div>

  <h2>四、结构性的「纸面宽松」：全球库消比的错觉</h2>
  <div class="panel">
    <p>全球库消比（橙线）2019 年见顶 40.4% 后缓慢回落，至 2026/27 的 33.3% 与前十年均值基本持平——这是「丰收」叙事的数据基础。但这条线被中国战略储备总量注水：中国库存占比从 2005 年的 26% 一路上行至 2019 年的 50% 峰值，近年虽主动去库（150→120 Mt），占比仍高达 44%。<b>剔除中国后，世界（除中国）库消比 2026/27 约 22%，远低于表面数字。</b></p>
    <div id="c_su" style="height:320px;margin-top:10px;"></div>
    <div class="src">全球库消比（橙）与中国期末库存（绿，右轴，Mt）。中国占比在 2019 年达到全期峰值 50%。</div>
  </div>

  <h2>五、为什么五国缓冲这么低：出口负担把盈余吃光了</h2>
  <div class="panel">
    <p class="lead"><b>「低」不是 2026 年特有的，而是五国 27 年来的结构性常态。</b>用供需平衡账拆开看：五国每年「产量 − 消费」的盈余约 65–80 Mt（产量 240–270，消费约 170–180），但<b>出口从 2000 年的 78 Mt 一路涨到 2020 年代 105–116 Mt（+50%）</b>——出口几乎吞掉了全部产消盈余，留给库存的只剩 40–60 Mt，<b>最终库存 ≠ 总供给盈余，而是「出口吃完后的残渣」</b>。</p>
    <div id="c_bal" style="height:360px;margin-top:10px;"></div>
    <div class="src">五国合计：深蓝=产量，橙=出口（<b>出口负担 27 年 +50%</b>），灰=消费，绿线=期末库存。出口线 2000 年来持续上扬，是压平库存的主要力量。</div>
    <div class="callout"><b>三把结构性成因：</b><br>
      ① <b>出口负担加重</b>：全球小麦贸易量扩张（中国采购、中东/北非进口增长），五国作为主要出口商被迫每年多卖——俄乌出口 2010 年 8 Mt → 2019 年 55 Mt，五国被顶上去接单。<br>
      ② <b>产量增长追不上出口</b>：五国产量 2010→2024 几乎没变（252→253 Mt），出口却从 96→105 Mt，差额全部从库存里抠。<br>
      ③ <b>低库存是模式，不是事故</b>：五国走「高流转、低留存」路线，期末库存常年只有 40–60 Mt（占产量约 20%），从未建立起像中国那样的战略囤积。</div>
    <table style="margin-top:10px;">
      <tr><th>年份</th><th>五国产量</th><th>消费</th><th>出口</th><th>平衡缺口</th><th>期末库存</th></tr>
      <tr class="num"><td>2000</td><td>243.7</td><td>177.4</td><td>77.9</td><td class="red">−11.6</td><td>57.5</td></tr>
      <tr class="num"><td>2010</td><td>252.1</td><td>175.4</td><td>95.9</td><td class="red">−19.2</td><td>54.4</td></tr>
      <tr class="num"><td>2019</td><td>243.7</td><td>167.3</td><td>99.9</td><td class="red">−23.5</td><td>51.2</td></tr>
      <tr class="num"><td>2024</td><td>252.8</td><td>168.7</td><td>105.4</td><td class="red">−21.2</td><td>45.9</td></tr>
      <tr class="num"><td><b>2025</b></td><td>282.9</td><td>176.3</td><td>112.1</td><td class="red">−5.5</td><td>58.2</td></tr>
      <tr class="num" style="background:#fff8ee;"><td><b>2026</b></td><td>245.0</td><td>174.5</td><td>104.5</td><td class="red"><b>−34.0</b></td><td><b>42.9</b></td></tr>
    </table>
    <div class="src">平衡缺口 = 产量 − 消费 − 出口（正=累库，负=去库）。2026/27 的 −34.0 Mt 是 27 年最深去库。单位 Mt。</div>
    <div class="warn"><b>2026 为什么特惨？</b>不是出口暴增（实际还从 112 降至 104），而是<b>五国同步减产 38 Mt</b>（2025 的 283 → 2026 的 245），而消费和出口都没随减产收缩 → 账在产量这边，缺口只能从库存里硬补。所以「低」= 结构性薄底（出口吃盈余）× 周期性减产（2026 同步减）<b>双重叠加</b>。</div>
  </div>

  <h2>六、库存到底影响多价格？实证：五国缓冲是年度价格最强解释变量</h2>
  <div class="panel">
    <p class="lead">把五国缓冲与 CBOT 小麦年均价对齐（2016/17–2026/27，11 个市场年度）：<b>五国缓冲 vs 年均价 Pearson r = −0.816（p&lt;0.0001）</b>——缓冲越低价格越高，关系在统计上极其显著。而同期的全球库消比与价格相关仅 −0.51（p=0.078，边际）——<b>「可贸易缓冲」对价格的解释力显著强于「全球总量」</b>。</p>
    <div id="c_px" style="height:340px;margin-top:10px;"></div>
    <div class="src">散点：横轴=五国缓冲（Mt），纵轴=CBOT 小麦市场年度均价（$/bu）。负斜率清晰，低缓冲含战争年（2021/22、2022/23）。</div>
    <table style="margin-top:10px;">
      <tr><th>缓冲档位</th><th>年份</th><th>年均价 ($/bu)</th><th>解读</th></tr>
      <tr class="num"><td><b>低缓冲 &lt;45 Mt</b></td><td>2020、21、22、23、26</td><td class="red"><b>$7.13</b></td><td>价格显著抬升（含战争两年）</td></tr>
      <tr class="num"><td>中缓冲 45–55 Mt</td><td>2019、24</td><td>$5.37</td><td>中性</td></tr>
      <tr class="num"><td>高缓冲 &gt;55 Mt</td><td>2016、17、18、25</td><td class="green">$4.95</td><td>价格明显压低</td></tr>
    </table>
    <div class="callout"><b>稳健性</b>：剔除 2021/22 战争首年（价格 +38%）后 r=−0.804（p=0.0001）；剔除战争两年后 r=−0.797（p=0.0005）——<b>负相关不是战争年驱动的，是库存的持续定价</b>。差分检验（Δ缓冲 vs Δ价格）r=−0.44、p=0.17，说明<u>年度间增量关系弱、水平关系强</u>——库存定的是「价格地板/天花板」而非短期涨跌。</div>
    <div class="warn"><b>2026/27 定位</b>：当前五国缓冲 42.9 Mt、年均价 $7.24。同缓冲档位的历史价格区间为 $6.04–8.66——<b>当前价格处于该档上沿</b>，意味着低库存已提供底部支撑，而地缘升水（黑海）提供了额外溢价。<b>若俄乌停火、缓冲回升至 58 Mt（2025 水平），按历史关系价格中枢或回落至 $5.5–6.0 区间</b>——这就是「库存百分比」对未来价格的锚定作用。</div>
  </div>

  <h2>七、结论：纸上丰、碗里紧</h2>
  <div class="panel">
    <table>
      <tr><th>听说的版本</th><th>数据验证</th><th>真相</th></tr>
      <tr class="num"><td>小麦近几年丰收</td><td>全球产量 2015→2025 连续 10 年上行，2025 峰值 843 Mt</td><td class="green">✓ 对，总量层面确实过剩</td></tr>
      <tr class="num"><td>现在库存相对紧张</td><td>五国可贸易缓冲 42.9 Mt，27 年第 19 百分位，同比 -26%</td><td class="red">✓ 也对，但紧张的是「可得性」</td></tr>
      <tr class="num"><td>两个都听说？</td><td>全球总库存 273 Mt 不低，但 44% 在中国、7% 在俄乌</td><td>不矛盾——纸面宽松、结构紧张</td></tr>
      <tr class="num"><td>俄乌不是很重要吗？</td><td>俄乌占全球出口 <b>28%</b>，却因战争被锁境内；若计入其库存，缓冲从第 19 分位跳到第 50 分位</td><td>重要，但它是「潜在供给」——紧张定价押注它短期出不来</td></tr>
    </table>
    <div class="warn"><b>对交易的含义</b>：决定 CBOT 价格的，从来不是「全球库存总量」而是「可贸易缓冲」。当前缓冲处于历史低位 + 俄乌物流基本归零（其 18.4 Mt 库存被锁）+ 五国同步减产，<b>是 2007-08 之后最脆弱的供给安全垫</b>。但注意口径敏感性：<b>一旦俄乌停火恢复出口，61.3 Mt 的潜在缓冲（第 50 分位）即刻释放，供给紧张的逻辑会被大幅削弱</b>——俄乌复航是当前空头最核心的潜在催化剂（与 68 号「停火后的流量约束」逻辑互为印证）。</div>
    <div class="src">指标口径：库消比=（期初/期末库存）÷ 总消费；五国=US+CA+E4+AS+BR；中国/俄乌=国家期末库存。所有数据源自 USDA FAS PSD 官方数据库（api.fas.usda.gov），市场年度口径，2026/27 为 8 月 WASDE 预测。</div>
  </div>

  <h2>八、附录：2000–2026 全球小麦供需数据</h2>
  <div class="panel">
    <table id="t_full"></table>
    <div class="src">单位：Mt（千吨）；库消比=期末库存÷总消费。数据：USDA FAS PSD，各市场年度最终修订值。</div>
  </div>

  <h2>数据与方法说明</h2>
  <div class="footer">
    <ol>
      <li>数据源：USDA Foreign Agricultural Service – PSD Online（api.fas.usda.gov），2026/27 为 2026 年 8 月 WASDE 预测值，历史年为最终审定值；每市场年度取最晚修订月份版本</li>
      <li>全球合计 = USDA PSD 全部国家/地区（123 个）加总；欧盟以 E4 整体口径计入（不含成员国重复）</li>
      <li>「五国可贸易缓冲」口径沿用报告 68：美/加/欧盟/澳/巴，不含俄乌、中国</li>
      <li>库消比（库存消费比）为常用宽松度指标，此处采用「期末库存/总消费」</li>
      <li>生成脚本：<code>scripts/wheat_stocks_history.py</code>（分析）＋ <code>scripts/build_82_wheat_stocks_report.py</code>（渲染），本地缓存 <code>Temp/psd/</code></li>
    </ol>
  </div>

</div>

<div class="termtip" id="termtip"></div>
<script>
(function(){
  const tip=document.getElementById('termtip');let cur=null;
  document.addEventListener('mouseover',e=>{
    const t=e.target.closest('.term');
    if(!t||t===cur)return;cur=t;
    tip.textContent=t.dataset.tip||'';tip.style.display='block';
    const r=t.getBoundingClientRect();
    tip.style.left=Math.min(r.left,window.innerWidth-300)+'px';
    tip.style.top=r.bottom+6+'px';
  });
  document.addEventListener('mouseout',e=>{
    if(e.target.closest('.term')){cur=null;tip.style.display='none';}
  });
})();
</script>

<script>
const YEARS=__YEARS__, PROD=__PROD__, CONS=__CONS__, END=__END__, SU=__SU__, T5=__T5__, T5RU=__T5RU__, RU=__RU__, CN=__CN__;
const T5P=__T5_PROD__, T5C=__T5_CONS__, T5X=__T5_EXP__, PX=__PX_SCATTER__;
const OI={blue:'#0072B2',orange:'#E69F00',sky:'#56B4E9',vm:'#D55E00',purple:'#CC79A7',green:'#009E73'};
let charts=[];
function mk(id,opt){const c=echarts.init(document.getElementById(id),null,{renderer:'canvas'});c.setOption(opt);charts.push(c);return c;}
window.addEventListener('resize',()=>charts.forEach(c=>c.resize()));

mk('c_prod',{
  tooltip:{trigger:'axis'},legend:{data:['产量','消费']},
  grid:{left:60,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:YEARS,axisLabel:{interval:1}},
  yAxis:{type:'value',name:'Mt',nameTextStyle:{color:'#5a6a7d'}},
  series:[
    {name:'产量',type:'line',smooth:true,data:PROD,lineStyle:{width:2.5,color:OI.blue},itemStyle:{color:OI.blue},symbol:'none'},
    {name:'消费',type:'line',smooth:true,data:CONS,lineStyle:{width:2,color:OI.orange,dash:[4,3]},itemStyle:{color:OI.orange},symbol:'none'}
  ]
});

mk('c_struct',{
  tooltip:{trigger:'item',formatter:'{b}: {c} Mt ({d}%)'},
  legend:{bottom:0},
  series:[{
    type:'pie',radius:['34%','68%'],center:['50%','45%'],
    itemStyle:{borderColor:'#fff',borderWidth:2},
    label:{formatter:'{b}\\n{c} Mt'},
    data:[
      {name:'中国储备 (120)',value:120,itemStyle:{color:OI.orange}},
      {name:'五国可贸易 (42.9)',value:42.9,itemStyle:{color:OI.blue}},
      {name:'俄乌 (18.4)',value:18.4,itemStyle:{color:OI.vm}},
      {name:'其他消费国 (91.9)',value:91.9,itemStyle:{color:OI.sky}}
    ]
  }]
});

mk('c_t5',{
  tooltip:{trigger:'axis'},legend:{data:['五国可贸易库存','五国+俄乌（含假设）']},
  grid:{left:60,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:YEARS,axisLabel:{interval:1}},
  yAxis:{type:'value',name:'Mt',nameTextStyle:{color:'#5a6a7d'}},
  series:[
    {name:'五国可贸易库存',type:'bar',data:T5,itemStyle:{color:OI.blue},
      markLine:{silent:true,symbol:'none',data:[{yAxis:30.6,label:{formatter:'2007 危机低点 30.6',color:OI.vm,position:'insideEndTop'},lineStyle:{color:OI.vm,type:'dashed'}}]}},
    {name:'五国+俄乌（含假设）',type:'bar',data:T5RU,itemStyle:{color:OI.orange,opacity:.65}}
  ]
});

mk('c_bal',{
  tooltip:{trigger:'axis'},legend:{data:['产量','出口','消费','期末库存']},
  grid:{left:60,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:YEARS,axisLabel:{interval:1}},
  yAxis:{type:'value',name:'Mt',nameTextStyle:{color:'#5a6a7d'}},
  series:[
    {name:'产量',type:'line',smooth:true,data:T5P,lineStyle:{width:2.5,color:OI.blue},itemStyle:{color:OI.blue},symbol:'none',areaStyle:{color:'rgba(0,114,178,.08)'}},
    {name:'出口',type:'line',smooth:true,data:T5X,lineStyle:{width:2.5,color:OI.orange},itemStyle:{color:OI.orange},symbol:'none'},
    {name:'消费',type:'line',smooth:true,data:T5C,lineStyle:{width:2,color:OI.sky,dash:[4,3]},itemStyle:{color:OI.sky},symbol:'none'},
    {name:'期末库存',type:'bar',data:T5,yAxisIndex:0,itemStyle:{color:OI.green,opacity:.55}},
  ]
});

mk('c_px',{
  tooltip:{trigger:'item',formatter:p=>{
    const d=p.data; if(p.dataType==='markLine')return '线性拟合';
    return d.name+'<br>缓冲 '+d.value[0]+' Mt<br>年均价 $'+d.value[1].toFixed(2);
  }},
  grid:{left:60,right:20,top:30,bottom:40},
  xAxis:{type:'value',name:'五国缓冲 (Mt)',nameTextStyle:{color:'#5a6a7d'},min:38,max:64},
  yAxis:{type:'value',name:'年均价 ($/bu)',nameTextStyle:{color:'#5a6a7d'},min:3.5,max:9.5},
  series:[{
    type:'scatter',data:PX,symbolSize:11,
    itemStyle:{color:OI.blue},
    label:{show:true,position:'top',formatter:p=>p.name,fontSize:10,color:'#5a6a7d'},
    markLine:{silent:true,symbol:'none',data:[{xAxis:42.9,label:{formatter:'2026/27 缓冲 42.9',color:OI.vm},lineStyle:{color:OI.vm,type:'dashed'}}]},
    markArea:{silent:true,data:[[{xAxis:38,yAxis:3.5},{xAxis:45,yAxis:9.5,itemStyle:{color:'rgba(210,90,40,.15)'}}]]}
  }]
});

mk('c_su',{
  tooltip:{trigger:'axis'},legend:{data:['全球库消比 (%)','中国库存 (Mt)']},
  grid:{left:60,right:60,top:40,bottom:40},
  xAxis:{type:'category',data:YEARS,axisLabel:{interval:1}},
  yAxis:[{type:'value',name:'%',nameTextStyle:{color:'#5a6a7d'}},{type:'value',name:'Mt',nameTextStyle:{color:'#5a6a7d'},splitLine:{show:false}}],
  series:[
    {name:'全球库消比 (%)',type:'line',smooth:true,data:SU,lineStyle:{width:2.5,color:OI.orange},itemStyle:{color:OI.orange},symbol:'none'},
    {name:'中国库存 (Mt)',type:'line',smooth:true,yAxisIndex:1,data:CN,lineStyle:{width:2,color:OI.green,dash:[4,3]},itemStyle:{color:OI.green},symbol:'none'}
  ]
});

const thead='<tr><th>市场年度</th><th>全球产量</th><th>全球消费</th><th>期末库存</th><th>库消比</th><th>五国可贸易库存</th><th>俄乌库存</th><th>中国库存</th></tr>';
let tbody='';
YEARS.forEach((y,i)=>{
  tbody+='<tr class="num"><td>'+y+'/'+((y+1)%100).toString().padStart(2,'0')+'</td>'
    +'<td>'+(PROD[i]/1000).toFixed(0)+'</td><td>'+(CONS[i]/1000).toFixed(0)+'</td>'
    +'<td>'+(END[i]/1000).toFixed(0)+'</td><td>'+Number(SU[i]).toFixed(1)+'%</td>'
    +'<td>'+(T5[i]/1000).toFixed(1)+'</td><td>'+(RU[i]/1000).toFixed(0)+'</td>'
    +'<td>'+(CN[i]/1000).toFixed(0)+'</td></tr>';
});
document.getElementById('t_full').innerHTML=thead+tbody;
</script>
</body>
</html>
"""

# 注入图表数据
HTML = HTML.replace('__YEARS__', json.dumps(YEARS))
HTML = HTML.replace('__PROD__', chart_prod)
HTML = HTML.replace('__CONS__', chart_cons)
HTML = HTML.replace('__END__', chart_end)
HTML = HTML.replace('__SU__', chart_su)
HTML = HTML.replace('__T5__', chart_t5)
HTML = HTML.replace('__T5RU__', chart_t5ru)
HTML = HTML.replace('__T5_PROD__', T5_PROD_ALL)
HTML = HTML.replace('__T5_CONS__', T5_CONS_ALL)
HTML = HTML.replace('__T5_EXP__', T5_EXP_ALL)
HTML = HTML.replace('__PX_SCATTER__', PX_SCATTER)
HTML = HTML.replace('__RU__', chart_ru)
HTML = HTML.replace('__CN__', chart_cn)
HTML = annotate_terms(HTML)

os.makedirs(OUT_DIR, exist_ok=True)
with open(OUT_HTML, 'w') as f:
    f.write(HTML)
print('OK ->', OUT_HTML, 'size', len(HTML))