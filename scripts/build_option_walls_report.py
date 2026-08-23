# -*- coding: utf-8 -*-
"""期权墙报告 build：8 标的 2026-09-18 到期 OI 分布 -> reports/20_期权墙八标的/index.html"""
import json, os

BASE = r"C:\Users\Administrator\Desktop\stock"
OUT_DIR = os.path.join(BASE, "reports", "20_期权墙八标的")
os.makedirs(OUT_DIR, exist_ok=True)

w = json.load(open(os.path.join(BASE, "results", "option_walls_20260918.json")))
near = json.load(open(os.path.join(BASE, "results", "option_walls_near_20260918.json")))
spots = json.load(open(os.path.join(BASE, "results", "spot_20260821.json")))

NAMES = {"ABBV":"艾伯维","GILD":"吉利德科学","LLY":"礼来","JNJ":"强生","KO":"可口可乐","SBUX":"星巴克","CSCO":"思科","AMZN":"亚马逊"}
ORDER = ["AMZN","LLY","ABBV","JNJ","GILD","KO","SBUX","CSCO"]

DATA = {"spot": spots, "names": NAMES, "tickers": {}}
for tk in ORDER:
    d = w[tk]
    DATA["tickers"][tk] = {
        "spot": spots[tk],
        "strikes": [r["strike"] for r in d["strikes"]],
        "call_oi": [r["call_oi"] for r in d["strikes"]],
        "put_oi": [r["put_oi"] for r in d["strikes"]],
        "wall_call": d["wall_call_strike"], "wall_call_oi": d["wall_call_oi"],
        "wall_put": d["wall_put_strike"], "wall_put_oi": d["wall_put_oi"],
        "max_pain": d["max_pain"], "pcr": d["pcr_oi"],
        "total_call": d["total_call_oi"], "total_put": d["total_put_oi"],
        "near_call": near[tk]["near_call_wall"], "near_put": near[tk]["near_put_wall"],
        "top5_call": near[tk]["top5_call"], "top5_put": near[tk]["top5_put"],
    }

# 总览表行
rows = []
for tk in ORDER:
    t = DATA["tickers"][tk]
    sp, mp = t["spot"], t["max_pain"]
    pos = "上方" if mp > sp else ("下方" if mp < sp else "持平")
    gap = (mp/sp - 1) * 100
    rows.append(f"""<tr><td><b>{tk}</b> {NAMES[tk]}</td>
<td>{sp:.2f}</td>
<td class="num pos">{t['wall_call']:.0f}</td><td class="num">{t['wall_call_oi']:,}</td>
<td class="num neg">{t['near_put'][0]:.0f}</td><td class="num">{t['near_put'][1]:,}</td>
<td class="num"><b>{mp:.0f}</b> <span class="muted">({pos} {gap:+.1f}%)</span></td>
<td class="num">{t['pcr']:.2f}</td>
<td class="num">{(t['total_call']+t['total_put']):,}</td></tr>""")
ROWS_HTML = "\n".join(rows)

CHART_DIVS = "\n".join(f'<div class="card"><h3>{tk} {NAMES[tk]} — 2026-09-18 到期 OI 分布</h3><div id="chart_{tk}" class="chart"></div><div class="note" id="note_{tk}"></div></div>' for tk in ORDER)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>美股八标的期权墙分析 · 2026-09-18 到期</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{--bg:#f7f8fa;--card:#ffffff;--ink:#1f2430;--muted:#6b7280;--line:#e5e7eb;
--blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--red:#D55E00;--green:#009E73;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",sans-serif;font-size:14px;line-height:1.7;}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px;}
h1{font-size:24px;margin-bottom:6px;}
h2{font-size:18px;margin:34px 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
h3{font-size:15px;margin-bottom:8px;color:#374151;}
.sub{color:var(--muted);font-size:13px;margin-bottom:20px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin-bottom:16px;}
table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;}
th{background:#eef2f7;padding:8px 10px;text-align:left;border-bottom:2px solid #d7dee8;white-space:nowrap;}
td{padding:7px 10px;border-bottom:1px solid var(--line);}
tr:hover td{background:#f4f8fd;}
.num{text-align:right;font-variant-numeric:tabular-nums;}
.pos{color:var(--red);font-weight:600;}
.neg{color:var(--blue);font-weight:600;}
.muted{color:var(--muted);font-size:12px;font-weight:400;}
.chart{width:100%;height:360px;}
.note{font-size:12.5px;color:#4b5563;background:#f6f8fb;border-left:3px solid var(--sky);padding:8px 12px;margin-top:6px;border-radius:0 4px 4px 0;}
.method{font-size:13px;color:#374151;}
.method li{margin:6px 0 6px 18px;}
.warn{background:#fff8e6;border:1px solid #f2e2ad;border-radius:6px;padding:10px 14px;font-size:13px;color:#6b5416;margin-top:14px;}
</style>
</head>
<body><div class="wrap">
<h1>美股八标的期权墙分析（2026-09-18 到期）</h1>
<div class="sub">数据源：富途（交易所公布 OI）· 行情截至 2026-08-21 收盘 · 距到期 27 天 · 生成日期 2026-08-22</div>

<h2>一、总览</h2>
<div class="card">
<table>
<thead><tr><th>标的</th><th>现价</th><th>Call 墙</th><th>Call OI</th><th>Put 墙(近场)</th><th>Put OI</th><th>Max Pain</th><th>PCR(OI)</th><th>总 OI</th></tr></thead>
<tbody>
@@ROWS@@
</tbody>
</table>
<div class="warn">注：LLY 全场 Put 墙位于 520（4,542 张）、AMZN 位于 160（15,712 张），均为深度价外的历史遗留仓位，参考意义有限，故总览采用「近场 Put 墙」（现价 80% 以上行权价区间内最大 Put OI）。CSCO 的 Call 墙 80 为深度价内仓位（股票替代/备兑），同样单独标注。</div>
</div>

<h2>二、逐标的 OI 分布</h2>
@@CHARTS@@

<h2>三、方法论与口径</h2>
<div class="card method">
<ul>
<li><b>期权墙</b>：某行权价上 Call（或 Put）未平仓量 OI 最大，视为潜在支撑/阻力聚集位。OI 为交易所公布值，含历史仓位，不等于当前交易意图。</li>
<li><b>Max Pain（最大痛点）</b>：假设到期时所有期权归零价值最大的标的价格，即卖方（庄家）赔付最小的价位：对每个候选价 S 计算 Σ CallOI·max(0,S−K) + Σ PutOI·max(0,K−S)，取最小值。</li>
<li><b>PCR（Put/Call Ratio）</b>：Put 总 OI ÷ Call 总 OI。&gt;1 偏防守/对冲情绪重，&lt;0.5 偏看涨/备兑情绪重。</li>
<li><b>到期日统一取 2026-09-18 月度合约</b>（季度到期，OI 结构最完整），跨标的可比；周度合约 OI 明显偏弱，不采用。</li>
<li><b>局限</b>：① OI 是存量快照，不区分开仓方向（买 Call 与卖 Call 同记 1 张 OI）；② 期权墙是"磁吸/阻挡"的经验假说，实证支持并不稳定，不应作为唯一交易依据；③ 深度价外老仓位会污染全场极值，故补充近场口径。</li>
</ul>
</div>
</div>

<script>
var DATA = __DATA_JSON__;
var ORDER = __ORDER_JSON__;
var C = {blue:'#0072B2', orange:'#E69F00', sky:'#56B4E9', ink:'#1f2430', muted:'#6b7280'};

function fmtK(n){return n>=10000?(n/10000).toFixed(1)+'w':n>=1000?(n/1000).toFixed(1)+'k':n;}

ORDER.forEach(function(tk){
  var t = DATA.tickers[tk];
  var chart = echarts.init(document.getElementById('chart_'+tk));
  chart.setOption({
    grid:{left:60,right:70,top:36,bottom:40},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
      formatter:function(ps){var s='<b>'+tk+' '+ps[0].axisValue+'</b><br>';
        ps.forEach(function(p){s+=p.marker+' '+p.seriesName+'：'+fmtK(p.value)+' 张<br>';});return s;}},
    legend:{top:0,data:['Call OI','Put OI']},
    xAxis:{type:'category',data:t.strikes.map(String),name:'行权价',nameLocation:'middle',nameGap:26,
      axisLabel:{interval:Math.max(0,Math.ceil(t.strikes.length/16)-1),rotate:0,fontSize:11}},
    yAxis:{type:'value',name:'OI(张)',axisLabel:{formatter:fmtK},splitLine:{lineStyle:{color:'#eef0f3'}}},
    series:[
      {name:'Call OI',type:'bar',data:t.call_oi,itemStyle:{color:C.orange},barGap:'0%',
       markLine:{symbol:'none',lineStyle:{type:'dashed'},label:{position:'insideEndTop',fontSize:11},data:[
         {yAxis:t.spot,name:'现价',lineStyle:{color:C.ink},label:{formatter:'现价 '+t.spot}},
         {yAxis:t.max_pain,name:'MaxPain',lineStyle:{color:C.sky},label:{formatter:'MaxPain '+t.max_pain}}
       ]}},
      {name:'Put OI',type:'bar',data:t.put_oi,itemStyle:{color:C.blue}}
    ]
  });
  var nc=t.near_call, np=t.near_put;
  document.getElementById('note_'+tk).innerHTML =
    '<b>'+tk+'</b>：现价 '+t.spot+'。Call 墙 <b>'+t.wall_call+'</b>（'+fmtK(t.wall_call_oi)+' 张，现价上方 '+((t.wall_call/t.spot-1)*100).toFixed(1)+'%）'+
    '；近场 Put 墙 <b>'+np[0]+'</b>（'+fmtK(np[1])+' 张）；Max Pain <b>'+t.max_pain+'</b>；PCR '+t.pcr+'。'+
    ' Top Call OI：'+t.top5_call.map(function(x){return x[0]+'('+fmtK(x[1])+')';}).join('、')+
    ' ｜ Top Put OI：'+t.top5_put.map(function(x){return x[0]+'('+fmtK(x[1])+')';}).join('、')+'。';
  window.addEventListener('resize',function(){chart.resize();});
});
</script>
</body></html>"""

html = (HTML.replace("@@ROWS@@", ROWS_HTML)
            .replace("@@CHARTS@@", CHART_DIVS)
            .replace("__DATA_JSON__", json.dumps(DATA, ensure_ascii=False))
            .replace("__ORDER_JSON__", json.dumps(ORDER)))

out = os.path.join(OUT_DIR, "index.html")
open(out, "w", encoding="utf-8").write(html)
print(f"written: {out} size={len(html)}")
