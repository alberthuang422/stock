# -*- coding: utf-8 -*-
"""
86 三品种可贸易库存三口径 —— 2015-2026 分阶段(疫情前后)
数据: 读 results/tribu_stocks_stage.json
输出: reports/86_三品种可贸易库存三口径_20260912/index.html
"""
import json, os

OUT_HTML = '/Users/alberthuang/Desktop/股票分析/reports/86_三品种可贸易库存三口径_20260912/index.html'
J = json.load(open('/Users/alberthuang/Desktop/股票分析/results/tribu_stocks_stage.json'))
series = J['series']
stats = J['stats']
Y_PRE = J['y_pre']
Y_POST = J['y_post']
YEARS = series['wheat']['years']

CN = {'wheat': '小麦', 'corn': '玉米', 'soybean': '大豆'}


def f(v):
    return f'{v:,.1f}'


def sign(v):
    return ('+' if v > 0 else '') + f'{v:,.1f}'


def trend_cls_one(v):
    # 单口径当前相对疫情后均值的方向
    return 'red' if v < 0 else 'green'


def build_section(com, idx):
    cn = CN[com]
    s = stats[com]
    d = series[com]
    rows = ''
    for gk, gl in [('hard', '三硬（美/加/澳）'), ('soft', '两软（巴/欧盟）'), ('five', '可贸易五国')]:
        g = s[gk]
        rows += ('<tr><td><b>' + gl + '</b></td>'
                 '<td class="num">' + f(g['pre_mean']) + '</td>'
                 '<td class="num">' + f(g['post_mean']) + '</td>'
                 '<td class="num"><b>' + f(g['cur']) + '</b></td>'
                 '<td class="num">' + sign(g['pre_vs_post']) + '</td>'
                 '<td class="num">' + sign(g['cur_vs_post']) + '</td></tr>')
    five = s['five']
    hard = s['hard']
    # 方向判断
    if five['cur_vs_post'] < -1:
        fiv_dir = '疫情后再去库'
    elif five['cur_vs_post'] > 1:
        fiv_dir = '疫情后回补'
    else:
        fiv_dir = '疫情后企稳'
    return ('<h2 id="' + com + '">' + str(idx) + '. ' + cn + '：疫情前后三口径库存</h2>\n'
            '<div class="panel">\n'
            '<div class="cards" style="grid-template-columns:repeat(4,1fr);margin-bottom:0;">\n'
            '<div class="kcard"><div class="lab">五国库存 2026</div><div class="val">' + f(five['cur']) + ' Mt</div><div class="note">疫情前均值 ' + f(five['pre_mean']) + ' · ' + fiv_dir + '</div></div>\n'
            '<div class="kcard"><div class="lab">三硬 2026</div><div class="val">' + f(hard['cur']) + ' Mt</div><div class="note">疫情前 ' + f(hard['pre_mean']) + ' → 后 ' + f(hard['post_mean']) + '</div></div>\n'
            '<div class="kcard"><div class="lab">两软 2026</div><div class="val">' + f(s['soft']['cur']) + ' Mt</div><div class="note">疫情前 ' + f(s['soft']['pre_mean']) + ' → 后 ' + f(s['soft']['post_mean']) + '</div></div>\n'
            '<div class="kcard"><div class="lab">全年份走势</div><div class="val" style="font-size:17px;">' + fiv_dir + '</div><div class="note">详见下方折线</div></div>\n'
            '</div>\n'
            '<div id="ch_' + com + '" style="height:320px;margin-top:14px;"></div>\n'
            '<div class="src">' + cn + '三口径期末库存（Mt，2015–2026 市场年度；左侧淡红阴影=疫情前 2015-19，右侧=疫情后 2020-26）。蓝=三硬、橙=两软、红=五国。</div>\n'
            '<table style="margin-top:14px;"><thead><tr><th>口径</th><th>疫情前均值</th><th>疫情后均值</th><th>2026 当前</th><th>前→后变化</th><th>后→今变化</th></tr></thead><tbody>' + rows + '</tbody></table>\n'
            '</div>')


sections_html = '\n'.join(build_section(com, i) for i, com in enumerate(['wheat', 'corn', 'soybean'], 1))

# 总览柱状数据: [品种][口径] = 当前 vs 疫情后均值 的差
ov = {}
for com in ['wheat', 'corn', 'soybean']:
    ov[com] = {
        'hard_diff': stats[com]['hard']['cur_vs_post'],
        'soft_diff': stats[com]['soft']['cur_vs_post'],
        'five_diff': stats[com]['five']['cur_vs_post'],
    }

chart_json = json.dumps({'series': series, 'ov': ov}, ensure_ascii=False)

TPL = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>86 · 三品种可贸易库存三口径（疫情前后） · 2026-09-12</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec; --card:#fff; --bg:#f5f7fa; --ref-bg:#eef2f7;}
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
  .kcard .val{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;}
  .kcard .note{font-size:12px;color:var(--sub);margin-top:3px;}
  .red{color:#b2182b;} .green{color:#1a7a3a;}
  h2{font-size:19px;margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--oi-blue);}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:16px;}
  table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;}
  th{background:#eef2f7;color:#12365e;padding:7px 9px;text-align:left;border-bottom:2px solid var(--line);font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:middle;}
  tr:last-child td{border-bottom:none;}
  .num{font-variant-numeric:tabular-nums;}
  .src{font-size:11px;color:var(--sub);margin-top:7px;line-height:1.5;}
  .callout{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:14px 18px;margin:14px 0;font-size:13.5px;}
  .warn{background:#fdf2f2;border:1px solid #eccaca;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}
  .footer{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}
  @media(max-width:820px){.cards{grid-template-columns:repeat(2,1fr);}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>三品种可贸易库存：疫情前后，三个剧本</h1>
    <div class="meta">报告编号 86 ｜ 数据源：USDA FAS PSD（期末库存 attribute 176）｜ 2015–2026 分阶段 ｜ 2026-09-12</div>
    <div class="sub">结论一句话：<b>拆成「三硬（美/加/澳）」「两软（巴/欧盟）」「五国」三口径对比疫情前后，小麦是唯一「疫情前→后→今」三段全下行的品种（可贸易缓冲已跌破疫情后均值）；玉米疫情后大幅去库、2026 才刚回稳；大豆则走出最极端的分化——三硬（美国为主）疫情中崩掉，全靠巴西两软一路狂增顶着不跌。</b></div>
  </div>

  <div class="callout"><b>口径与阶段：</b>「三硬」= 美+加+澳（有官方库存盘点，最接近实测）；「两软」= 巴+欧盟（库存靠平衡表残差，可信度次之）；「五国」= 三硬+两软（82 号可贸易缓冲口径）。阶段：疫情前=2015–2019，疫情后=2020–2026（含疫情当年），「今」= 2026 市场年度最新值。</div>

  <div class="panel">
    <h3 style="font-size:16px;color:#12365e;">总览：当前库存相对「疫情后均值」的偏离（Mt）</h3>
    <div id="ch_ov" style="height:320px;margin-top:10px;"></div>
    <div class="src">正值=当前库存高于疫情后均值（供给回补），负值=低于（仍在去库）。红=五国、蓝=三硬、橙=两软。</div>
  </div>

__SECTIONS__

  <div class="panel">
    <h3 style="font-size:16px;color:#12365e;">横向解读：三个品种，三个剧本</h3>
    <div class="warn"><b>小麦 —— 唯一三段全下行：</b>五国 57.6（疫前）→ 45.7（疫后）→ 42.9 Mt（今）；三硬更狠，39.5→29.3→26.8，两软基本走平。这意味着小麦的紧张不是周期波动，而是疫后持续至今的<b>结构性去库</b>——可贸易缓冲已系统性下移一个台阶，与 82 号「逼近 2007 危机水平」的判断完全同向。</div>
    <div class="callout"><b>玉米 —— 疫情后去库、2026 刚企稳：</b>五国 72.1→57.9 Mt 是大跌，但 2026 回到 59.1（+1.2），三硬亦 +2.5，两软小幅续降。玉米是「疫情冲击去库 → 当前供给正在修复」的<b>周期中段</b>，方向已从去库转向回补，但尚未回到疫前水位。</div>
    <div class="callout"><b>大豆 —— 三硬崩、两软冲：</b>三硬 13.6→8.6→9.1 Mt（疫后均值腰斩，美豆份额让给巴西），两软 30.0→35.1→<b>38.3 Mt 一路新高</b>。五国合计 43.6→43.7 看似原地踏步，实则是「美国去库」被「巴西暴增」完全对冲。大豆的宽松全部押在巴西身上——而巴西恰好是两软口径里<b>库存数据质量最差</b>的一环（饲料/乙醇消费靠估），所以「大豆很宽裕」这个结论要打折读。</div>
  </div>

  <div class="footer">
    <b>数据与方法：</b>USDA FAS PSD 官方缓存（Temp/psd），期末库存 attributeId=176，单位已转 Mt（千吨→Mt）。三硬=US/CA/AS，两软=BR/E4，五国=两者并集。疫情前=2015-2019 均值，疫情后=2020-2026 均值。<b>提醒：</b>两软（尤其欧盟、巴西）库存为平衡表残差，绝对值精确度低于三硬，本报告用于相对趋势与阶段对比。<br>
    脚本：scripts/tribu_stocks_stage.py（拉数）→ scripts/build_tribu_report.py（构建）。原始数据：results/tribu_stocks_stage.json。
  </div>
</div>
<script>
  var D = __CHART_JSON__;
  var colors = { hard:'#0072B2', soft:'#E69F00', five:'#D55E00' };
  function mkLine(el, com){
    var d = D.series[com];
    var ch = echarts.init(document.getElementById(el));
    ch.setOption({
      tooltip:{trigger:'axis', valueFormatter:function(v){return v+' Mt';}},
      legend:{data:['三硬(美/加/澳)','两软(巴/欧盟)','五国'], top:0, textStyle:{fontSize:12}},
      grid:{left:48,right:20,top:36,bottom:28},
      xAxis:{type:'category', data:d.years, axisLabel:{fontSize:11}},
      yAxis:{type:'value', name:'Mt', axisLabel:{fontSize:11}},
      series:[
        {name:'三硬(美/加/澳)', type:'line', data:d.hard, smooth:true, symbol:'circle', symbolSize:5, lineStyle:{width:2,color:colors.hard}, itemStyle:{color:colors.hard}},
        {name:'两软(巴/欧盟)', type:'line', data:d.soft, smooth:true, symbol:'circle', symbolSize:5, lineStyle:{width:2,color:colors.soft}, itemStyle:{color:colors.soft}},
        {name:'五国', type:'line', data:d.five, smooth:true, symbol:'circle', symbolSize:5, lineStyle:{width:2.5,color:colors.five}, itemStyle:{color:colors.five}},
        {name:'疫情分界', type:'line', markLine:{silent:true, symbol:'none', lineStyle:{type:'dashed',color:'#999'}, data:[{xAxis:'2019'}]}, data:[], tooltip:{show:false}, legendHoverLink:false}
      ]
    });
  }
  mkLine('ch_wheat','wheat');
  mkLine('ch_corn','corn');
  mkLine('ch_soybean','soybean');
  (function(){
    var ov = D.ov;
    var ch = echarts.init(document.getElementById('ch_ov'));
    var cats = ['小麦','玉米','大豆'];
    ch.setOption({
      tooltip:{trigger:'item', valueFormatter:function(v){return (v>=0?'+':'')+v+' Mt';}},
      legend:{data:['三硬','两软','五国'], top:0, textStyle:{fontSize:12}},
      grid:{left:48,right:20,top:36,bottom:28},
      xAxis:{type:'category', data:cats, axisLabel:{fontSize:12}},
      yAxis:{type:'value', name:'偏离(Mt)', axisLabel:{fontSize:11}},
      series:[
        {name:'三硬', type:'bar', data:[ov.wheat.hard_diff, ov.corn.hard_diff, ov.soybean.hard_diff], barWidth:18, itemStyle:{color:'#0072B2'}},
        {name:'两软', type:'bar', data:[ov.wheat.soft_diff, ov.corn.soft_diff, ov.soybean.soft_diff], barWidth:18, itemStyle:{color:'#E69F00'}},
        {name:'五国', type:'bar', data:[ov.wheat.five_diff, ov.corn.five_diff, ov.soybean.five_diff], barWidth:18, itemStyle:{color:'#D55E00'}}
      ]
    });
  })();
</script>
</body>
</html>'''

html = TPL.replace('__SECTIONS__', sections_html)
html = html.replace('__CHART_JSON__', chart_json)

os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
print('OK ->', OUT_HTML)