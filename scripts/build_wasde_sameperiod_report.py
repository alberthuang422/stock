# -*- coding: utf-8 -*-
"""
88 WASDE「往年同期口径」vs「事后终稿口径」——补齐 2015-2020 后的结论校验
数据: results/wasde_sameperiod_analysis.json
输出: reports/88_WASDE往年同期口径_20260912/index.html
"""
import json, os, statistics as st

ROOT = '/Users/alberthuang/Desktop/股票分析'
OUT = f'{ROOT}/reports/88_WASDE往年同期口径_20260912/index.html'
J = json.load(open(f'{ROOT}/results/wasde_sameperiod_analysis.json'))
YEARS = J['years']
CN = {'wheat': '小麦', 'corn': '玉米', 'soybean': '大豆'}

# ---- 计算补充统计 ----
extra = {}
for crop, rec in J['crops'].items():
    sp, fn = rec['sp'], rec['fn']
    m = {}
    m['sp_1519'] = round(st.mean([sp[str(y)]['five'] for y in range(2015, 2020)]), 1)
    m['sp_2026'] = sp['2026']['five']
    for a, b, tag in [(2015, 2020, 'early'), (2021, 2026, 'late')]:
        pass
    m['sp_mean_1520'] = round(st.mean([sp[str(y)]['five'] for y in range(2015, 2021)]), 1)
    m['sp_mean_2125'] = round(st.mean([sp[str(y)]['five'] for y in range(2021, 2026)]), 1)
    m['drift_mean_1520'] = round(st.mean([rec['drift'][str(y)] for y in range(2015, 2021)]), 1)
    m['drift_mean_2125'] = round(st.mean([rec['drift'][str(y)] for y in range(2021, 2026)]), 1)
    m['drift_mean_all'] = round(st.mean([rec['drift'][str(y)] for y in range(2015, 2026)]), 1)
    m['trough'] = min(sp[str(y)]['five'] for y in range(2021, 2024))
    m['trough_year'] = min(range(2021, 2024), key=lambda y: sp[str(y)]['five'])
    extra[crop] = m

w = J['stats']['wheat']['five']
s_w = extra['wheat']


def f(v, n=1):
    return f'{v:,.{n}f}'


# ---- 卡片 ----
cards = (
    '<div class="kcard"><div class="lab">小麦 · 2026 五国库存（同期口径）</div>'
    f'<div class="val">{f(s_w["sp_2026"])} Mt</div>'
    f'<div class="note">11 年同期区间 {f(w["sp_range"][0])}–{f(w["sp_range"][1])} → <b class="red">{w["pct_sp_11y"]} 分位</b></div></div>'
    '<div class="kcard"><div class="lab">同一读数 · 终稿口径下</div>'
    f'<div class="val">{w["pct_fn_11y"]} <span style="font-size:13px;">分位</span></div>'
    f'<div class="note">历史被系统性上修（均值 <b class="red">+{f(s_w["drift_mean_all"])} Mt</b>）→ 2026 显得异常低</div></div>'
    '<div class="kcard"><div class="lab">小麦 · 代际落差</div>'
    f'<div class="val">{f(s_w["sp_mean_1520"])} → {f(s_w["sp_mean_2125"])}</div>'
    '<div class="note">2015–20 均值 → 2021–25 均值（Mt），<b>−21%</b></div></div>'
    '<div class="kcard"><div class="lab">玉米 / 大豆 2026（同期 11 年分位）</div>'
    f'<div class="val">{J["stats"]["corn"]["five"]["pct_sp_11y"]}% / {J["stats"]["soybean"]["five"]["pct_sp_11y"]}%</div>'
    '<div class="note">玉米偏紧、大豆偏松，方向延续</div></div>'
)

# ---- 明细表 ----
rows = ''
for crop in ['wheat', 'corn', 'soybean']:
    rec = J['crops'][crop]
    cs = rec['cset']
    for tag, key, lab in [('sp', 'sp', '往年同期'), ('fn', 'fn', '事后终稿')]:
        cells = ''.join(f'<td class="num">{f(rec[key][str(y)]["five"])}</td>' for y in map(int, YEARS))
        rows += (f'<tr><td><b>{CN[crop]}</b></td><td>{lab}</td>'
                 f'<td class="src" style="font-size:11px;">{len(cs)}国</td>' + cells + '</tr>')
    dcell = ''.join(f'<td class="num {"red" if rec["drift"][str(y)]>0 else "green"}">{rec["drift"][str(y)]:+.1f}</td>'
                    for y in map(int, YEARS))
    rows += f'<tr class="dr"><td></td><td>漂移(终稿−同期)</td><td></td>{dcell}</tr>'

head = ''.join(f'<th class="num">{y}</th>' for y in YEARS)

# ---- 统计表 ----
stat_rows = ''
for crop in ['wheat', 'corn', 'soybean']:
    s = J['stats'][crop]
    for wkey, wlab in [('five', '可贸易篮子'), ('hard', '三硬(美加澳)')]:
        a = s[wkey]
        stat_rows += (f'<tr><td><b>{CN[crop]}</b></td><td>{wlab}</td>'
                      f'<td class="num">{f(a["cur_sp"])}</td>'
                      f'<td class="num">{f(a["sp_range"][0])}–{f(a["sp_range"][1])}</td>'
                      f'<td class="num">{f(a["sp_median"])}</td>'
                      f'<td class="num"><b class="{"red" if a["pct_sp_11y"]<50 else "green"}">{a["pct_sp_11y"]}%</b></td>'
                      f'<td class="num">{a["pct_sp_5y"]}%</td>'
                      f'<td class="num">{a["pct_fn_11y"]}%</td></tr>')

chart_json = json.dumps({'J': J, 'extra': extra}, ensure_ascii=False)

TPL = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>88 · WASDE 往年同期口径 vs 事后终稿口径 · 2026-09-12</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --oi-green:#009E73;
        --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec; --card:#fff; --bg:#f5f7fa; --ref-bg:#eef2f7;}
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px;}
  .wrap{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}
  .hero{background:linear-gradient(135deg,#12365e 0%,#1d5c93 100%);color:#fff;border-radius:12px;padding:28px 32px;margin-bottom:20px;}
  .hero h1{font-size:24px;margin-bottom:6px;line-height:1.4;}
  .hero .meta{font-size:12.5px;opacity:.85;margin-top:4px;}
  .hero .sub{margin-top:12px;font-size:14px;opacity:.96;border-top:1px solid rgba(255,255,255,.25);padding-top:10px;}
  .cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}
  .kcard{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}
  .kcard .lab{font-size:12px;color:var(--sub);margin-bottom:3px;}
  .kcard .val{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;}
  .kcard .note{font-size:12px;color:var(--sub);margin-top:3px;}
  .red{color:#b2182b;} .green{color:#1a7a3a;}
  h2{font-size:19px;margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--oi-blue);}
  h3{font-size:16px;color:#12365e;}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:16px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;}
  th{background:#eef2f7;color:#12365e;padding:6px 7px;text-align:left;border-bottom:2px solid var(--line);font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid var(--line);vertical-align:middle;}
  tr:last-child td{border-bottom:none;}
  tr.dr td{background:#fafbfd;font-size:11.5px;}
  .num{font-variant-numeric:tabular-nums;text-align:right;}
  th.num{text-align:right;}
  .src{font-size:11px;color:var(--sub);margin-top:7px;line-height:1.5;}
  .callout{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:14px 18px;margin:14px 0;font-size:13.5px;}
  .warn{background:#fdf2f2;border:1px solid #eccaca;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}
  .ok{background:#f0f8f4;border:1px solid #c9e5d6;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}
  .footer{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}
  .term{border-bottom:1px dashed #8aa0b8;cursor:help;position:relative;}
  .term:hover::after{content:attr(data-t);position:absolute;left:0;top:130%;z-index:99;
    background:#12365e;color:#fff;font-size:12px;line-height:1.5;padding:8px 11px;border-radius:7px;
    width:290px;white-space:normal;box-shadow:0 6px 20px rgba(0,0,0,.22);font-weight:400;}
  code{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px;}
  @media(max-width:900px){.cards{grid-template-columns:repeat(2,1fr);}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>小麦到底紧不紧？——WASDE「往年同期口径」补齐 2015–2020 后的结论校验</h1>
    <div class="meta">报告编号 88 ｜ 数据源：USDA WASDE 官方"当时公布"历史数据（2010–2026）+ FAS PSD 最新修订 ｜ 2026-09-12</div>
    <div class="sub">结论一句话：<b>「2026 小麦处于历史极低位」这个读数，很大程度是口径造成的假象——拿"当期新鲜预测"去比"事后被上修过的历史"，历史被系统性抬高了约 5–6 Mt。换成往年同期口径后，2026 的小麦位置从 9 分位升到 36 分位。但补齐 2015–2020 也让原判断打了折：2026 在 11 年窗口里只是"略低于中位"，不再"偏中上"。</b></div>
  </div>

  <div class="cards">__CARDS__</div>

  <div class="callout"><b>一句话讲清口径之争：</b>WASDE 每月都会修正历史估计。PSD 数据库现在给出的 2015–2020 小麦库存，是<b>被反复上修之后</b>的终稿值；而 2026 是<b>刚出炉的预测</b>。拿"新鲜预测"比"修订过的历史"，历史上修越多，当前就显得越低。正确做法是——把 2026 与<b>前几年 9 月报告当时公布的同期预测</b>相比（<span class="term" data-t="每年9月WASDE报告在当时给出的"最新市场年度"期末库存预测值，取自USDA官方Historical WASDE Report Data（当时公布快照，不含事后修订）">往年同期口径</span>）。</div>

  <h2 id="method">1. 三种看法，一张图看懂差别</h2>
  <div class="panel">
    <div id="ch_wheat" style="height:360px;"></div>
    <div class="src">小麦「五国（美/加/澳+巴/欧盟）」期末库存，单位 Mt，横轴=报告年份（市场年度 Y/Y+1）。<b>蓝线</b>=往年同期口径（每年 9 月当时的预测）；<b>橙线</b>=事后终稿口径（PSD 最新修订）。灰底=2015–2020（本次新补齐的年份）。两线之差即"<span class="term" data-t="终稿值 − 同期值。正值=该年库存事后被上修，会让当前年份在历史排名中显得更低">修订漂移</span>"。</div>
  </div>

  <div class="panel">
    <h3>读图三件事</h3>
    <div class="warn"><b>① 历史被系统性上修。</b>2015–2025 年小麦五国的平均漂移为 <b class="red">+__DRIFT_ALL__ Mt</b>（终稿显著高于当年预测）。尤其 2017 年（+15.0）、2018 年（+12.1）、2025 年（+11.4）——这正是 82 号"27 年第 19 百分位"这类读数的来源：历史底被抬高，当前自然显得低。</div>
    <div class="ok"><b>② 换成同期口径，2026 立刻"变高"。</b>2026 同期值 __SP26__ Mt，在 2015–2025 十一年同期区间 __RANGE__ 中位列 <b>__P11__ 分位</b>；而同样的 2026 值放进终稿历史里只剩 <b class="red">__PFN__ 分位</b>。口径一换，位置差了一个身位。</div>
    <div class="callout"><b>③ 但补上 2015–2020 后，"偏中上"不成立了。</b>2015–2020 五国小麦缓冲常年 __M1520__ Mt 均值，2021–2025 崩到 __M2125__ Mt（−21%）。把这段高水位纳入基准后，2026 的 __P11__ 分位只算"略低于中位"——不再是"近 5 年对比里的 80 分位（偏中上）"。<b>结论修正：2026 不是历史极低位，但也不是宽裕，而是"从 2021–23 深坑里的部分修复"。</b></div>
  </div>

  <h2 id="crops">2. 三品种横向：同期口径下的走势</h2>
  <div class="panel">
    <div id="ch_crops" style="height:340px;"></div>
    <div class="src">往年同期口径、可贸易篮子（小麦=5 国，玉米=4 国，大豆=3 国，见下方口径说明），单位 Mt。</div>
  </div>

  <h2 id="rank">3. 2026 到底在什么位置？——三种基准下的百分位</h2>
  <div class="panel">
    <div id="ch_rank" style="height:340px;"></div>
    <div class="src">百分位=2026 值在历史样本中的分位（越高代表库存越宽裕）。<b>红=终稿口径（11 年）</b>，蓝=同期口径（11 年），绿=同期口径（近 5 年）。同一品种三根柱子的落差，就是口径与窗口选择带来的结论分歧。</div>
    <div class="warn" style="margin-top:12px;"><b>关键分歧点：</b>小麦 2026 的同期位置，近 5 年基准给 <b>__P5Y__</b>，11 年基准只给 <b>__P11__</b>。也就是说，"2026 小麦偏宽松"这个判断，成立与否取决于你把 2015–2020 那段高水位算不算进基准。本次补齐后，答案倾向"不算宽裕"。</div>
  </div>

  <h2 id="stat">4. 统计总表</h2>
  <div class="panel">
    <table>
      <thead><tr><th>品种</th><th>口径</th><th class="num">2026 同期值</th><th class="num">11 年同期区间</th><th class="num">中位</th><th class="num">同期11年分位</th><th class="num">同期5年分位</th><th class="num">终稿11年分位</th></tr></thead>
      <tbody>__STATS__</tbody>
    </table>
    <div class="src">单位 Mt。玉米/大豆篮子国别少于 5 国（WASDE 世界表未单列澳洲玉米、加拿大/澳洲大豆），缺口均 &lt;2%，不影响方向。</div>
  </div>

  <h2 id="detail">5. 明细：同期 vs 终稿（Mt）</h2>
  <div class="panel" style="overflow-x:auto;">
    <table>
      <thead><tr><th>品种</th><th>口径</th><th>国别</th>__HEAD__</tr></thead>
      <tbody>__ROWS__</tbody>
    </table>
    <div class="src">漂移行 = 终稿 − 同期。<b class="red">红色正值</b>=该年库存事后被上修（抬高历史基准）；绿色负值=事后被下修。</div>
  </div>

  <h2 id="conc">6. 结论：补齐 15–20 后，哪些成立、哪些不成立</h2>
  <div class="panel">
    <div class="ok"><b>✔ 成立（且更重要）：口径偏差是真的。</b>2015–2025 年小麦库存的终稿值平均比当年预测高 <b>+__DRIFT_ALL__ Mt</b>，玉米、大豆同样存在两位数级别的年际漂移。任何"当前处于历史 N 年最低"的判断，只要拿新鲜预测比修订后历史，就天然偏严。</div>
    <div class="ok"><b>✔ 成立：小麦是唯一"代际台阶下移"的品种。</b>2015–2020 五国均值 <b>__M1520__ Mt</b> → 2021–2025 <b>__M2125__ Mt</b>，−21%；同期玉米为 __MC1520__ → __MC2125__，大豆 __MS1520__ → __MS2125__，均为震荡而非台阶式下移。</div>
    <div class="warn"><b>✘ 不成立（本次新增的修正）：</b>"2026 小麦在同期口径下偏中上（80 分位）"是<b>只看 2021–2025 短窗口</b>的结论。补入 2015–2020 后，11 年窗口下 2026 落到 <b>__P11__ 分位</b>——低于中位。原判断的"偏中上"应修正为"略偏中下"。</div>
    <div class="callout"><b>综合口径结论：</b>2026 小麦 <b>既不是"27 年最低"（终稿口径假象，9 分位），也不是"偏宽裕"（短窗口假象，80 分位）</b>。真实位置：<b>长期区间的下半部（36 分位）</b>，且明显好于 2022–23 年 __TROUGH__ Mt 的深坑（当年 9 月预测值）。对价格的含义是——缓冲偏薄但未到危机，方向随供给端边际变化（详见 82 / 86 号）。</div>
  </div>

  <div class="footer">
    <b>数据与方法：</b>①<span class="term" data-t="USDA官方Historical WASDE Report Data，每月报告公布当时的数值快照，不含任何事后修订。2010-04至2020-12以ZIP打包发布，2021年起按月单文件发布">往年同期口径</span>取自 USDA 官方 Historical WASDE Report Data（2010-04~2026-09 全套），筛选 ReportDate=int("September YYYY")、Attribute=Ending Stocks、Unit=Million Metric Tons、ProjEstFlag 含 Proj；②终稿口径取自 FAS PSD 缓存（Temp/psd），attributeId=176，取各市场年度最晚修订月份，单位千吨→Mt。<br>
    <b>口径对齐：</b>两腿严格使用同一国别集合（小麦 US/CA/AS/BR/E4；玉米 US/CA/BR/E4；大豆 US/BR/E4），避免把"国别缺失"误读为"修订漂移"。<br>
    <b>已知局限：</b>①玉米缺澳洲、大豆缺加拿大/澳洲（官方世界表未单列，缺口 &lt;2%）；②"同期口径"是预测值、本身含预判误差（如 2020 年漂移为负），并非真值；③PSD 缓存最新修订截至 2026-08，2026 年终稿值略滞后于 9 月报告。<br>
    <b>脚本：</b>scripts/extract_wasde_sameperiod_v2.py（同期口径提取）→ scripts/wasde_sameperiod_analysis.py（对照）→ scripts/build_wasde_sameperiod_report.py（本页）。数据：results/wasde_sameperiod_2015_2026.json、results/wasde_sameperiod_analysis.json。
  </div>
</div>
<script>
  var D = __CHART_JSON__;
  var J = D.J, EX = D.extra;
  var YEARS = J.years;
  var C = {sp:'#0072B2', fn:'#E69F00', verm:'#D55E00', green:'#009E73'};

  // ---- 图1: 小麦 同期 vs 终稿 ----
  (function(){
    var sp = YEARS.map(function(y){return J.crops.wheat.sp[y].five;});
    var fn = YEARS.map(function(y){return J.crops.wheat.fn[y].five;});
    var ch = echarts.init(document.getElementById('ch_wheat'));
    ch.setOption({
      tooltip:{trigger:'axis', valueFormatter:function(v){return v+' Mt';}},
      legend:{data:['往年同期口径','事后终稿口径'], top:0, textStyle:{fontSize:12}},
      grid:{left:56,right:24,top:38,bottom:30},
      xAxis:{type:'category', data:YEARS, axisLabel:{fontSize:11}},
      yAxis:{type:'value', name:'Mt', min:30, axisLabel:{fontSize:11}},
      series:[
        {name:'往年同期口径', type:'line', data:sp, smooth:true, symbol:'circle', symbolSize:6,
         lineStyle:{width:3,color:C.sp}, itemStyle:{color:C.sp},
         markArea:{silent:true, itemStyle:{color:'rgba(0,114,178,.06)'}, data:[[{xAxis:'2015'},{xAxis:'2020'}]]},
         markPoint:{data:[{name:'2026', coord:['2026', sp[YEARS.length-1]], value:sp[YEARS.length-1]}],
                    symbolSize:46, itemStyle:{color:C.sp}, label:{fontSize:10,color:'#fff'}}},
        {name:'事后终稿口径', type:'line', data:fn, smooth:true, symbol:'circle', symbolSize:5,
         lineStyle:{width:2,color:C.fn,type:'dashed'}, itemStyle:{color:C.fn}}
      ]
    });
  })();

  // ---- 图2: 三品种同期 ----
  (function(){
    var ch = echarts.init(document.getElementById('ch_crops'));
    var mk = function(k,n){return {name:n, type:'line', smooth:true, symbol:'circle', symbolSize:5,
      lineStyle:{width:2.4}, data:YEARS.map(function(y){return J.crops[k].sp[y].five;})};};
    var a=mk('wheat','小麦'), b=mk('corn','玉米'), c=mk('soybean','大豆');
    a.lineStyle.color=C.verm; a.itemStyle={color:C.verm};
    b.lineStyle.color=C.sp;   b.itemStyle={color:C.sp};
    c.lineStyle.color=C.green;c.itemStyle={color:C.green};
    ch.setOption({
      tooltip:{trigger:'axis', valueFormatter:function(v){return v+' Mt';}},
      legend:{data:['小麦','玉米','大豆'], top:0, textStyle:{fontSize:12}},
      grid:{left:56,right:24,top:38,bottom:30},
      xAxis:{type:'category', data:YEARS, axisLabel:{fontSize:11}},
      yAxis:{type:'value', name:'Mt', axisLabel:{fontSize:11}},
      series:[a,b,c]
    });
  })();

  // ---- 图3: 2026 百分位 ----
  (function(){
    var ch = echarts.init(document.getElementById('ch_rank'));
    var cats = ['小麦','玉米','大豆'];
    var keys = ['wheat','corn','soybean'];
    var dFn = keys.map(function(k){return J.stats[k].five.pct_fn_11y;});
    var dSp11 = keys.map(function(k){return J.stats[k].five.pct_sp_11y;});
    var dSp5 = keys.map(function(k){return J.stats[k].five.pct_sp_5y;});
    ch.setOption({
      tooltip:{trigger:'axis', axisPointer:{type:'shadow'}, valueFormatter:function(v){return v+' 分位';}},
      legend:{data:['终稿口径·11年','同期口径·11年','同期口径·近5年'], top:0, textStyle:{fontSize:12}},
      grid:{left:56,right:24,top:38,bottom:30},
      xAxis:{type:'category', data:cats, axisLabel:{fontSize:12}},
      yAxis:{type:'value', name:'百分位(%)', max:100, axisLabel:{fontSize:11}},
      series:[
        {name:'终稿口径·11年', type:'bar', data:dFn, barWidth:20, itemStyle:{color:'#b2182b'}},
        {name:'同期口径·11年', type:'bar', data:dSp11, barWidth:20, itemStyle:{color:C.sp}},
        {name:'同期口径·近5年', type:'bar', data:dSp5, barWidth:20, itemStyle:{color:C.green}}
      ]
    });
  })();
</script>
</body>
</html>'''

html = (TPL.replace('__CARDS__', cards)
           .replace('__STATS__', stat_rows)
           .replace('__HEAD__', head)
           .replace('__ROWS__', rows)
           .replace('__DRIFT_ALL__', f(s_w['drift_mean_all']))
           .replace('__SP26__', f(s_w['sp_2026']))
           .replace('__RANGE__', f'{f(w["sp_range"][0])}–{f(w["sp_range"][1])}')
           .replace('__P11__', str(w['pct_sp_11y']))
           .replace('__P5Y__', str(w['pct_sp_5y']))
           .replace('__PFN__', str(w['pct_fn_11y']))
           .replace('__M1520__', f(s_w['sp_mean_1520']))
           .replace('__M2125__', f(s_w['sp_mean_2125']))
           .replace('__MC1520__', f(extra['corn']['sp_mean_1520']))
           .replace('__MC2125__', f(extra['corn']['sp_mean_2125']))
           .replace('__MS1520__', f(extra['soybean']['sp_mean_1520']))
           .replace('__MS2125__', f(extra['soybean']['sp_mean_2125']))
           .replace('__TROUGH__', f(s_w['trough']))
           .replace('__CHART_JSON__', chart_json))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(html)
print('OK ->', OUT, len(html), 'bytes')
print('extra:', json.dumps(extra, ensure_ascii=False, indent=2))
