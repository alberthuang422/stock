# -*- coding: utf-8 -*-
"""生成白糖 CFTC 40 年持仓可视化看板（单页 HTML，ECharts，浅底研报风）。"""
import csv, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE, "data", "sugar", "sugar_cftc_futonly_1986_2026.csv")
OUT_HTML = os.path.join(BASE, "reports", "白糖CFTC持仓_1986-2026_看板.html")
os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)

rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))

def num(r, k):
    v = r.get(k)
    if v in ("", "None", None):
        return None
    return int(v)

dates = [r["date"] for r in rows]
oi = [num(r, "oi") for r in rows]
nc_net = [num(r, "nc_net") for r in rows]
c_net = [num(r, "c_net") for r in rows]

last = rows[-1]
hist_net = [x for x in nc_net if x is not None]

def pctile(s, v):
    if v is None or not s:
        return None
    return round(100.0 * sum(1 for x in s if x <= v) / len(s), 1)

latest_net = hist_net[-1]
p_all = pctile(hist_net, latest_net)
hist_5y = [x for x, d in zip(nc_net, dates) if d >= "2021-09-01"]
p_5y = pctile(hist_5y, latest_net)
mx = max(hist_net); mn = min(hist_net)
mxd = dates[nc_net.index(mx)]; mnd = dates[nc_net.index(mn)]
detail = {k: num(last, k) for k in
          ["oi", "nc_l", "nc_s", "nc_sp", "c_l", "c_s", "nr_l", "nr_s", "nc_net", "c_net", "nr_net",
           "nc_l_chg", "nc_s_chg", "c_l_chg", "c_s_chg"]}

payload = json.dumps(dict(dates=dates, oi=oi, nc_net=nc_net, c_net=c_net), ensure_ascii=False)
net_cls = "up" if latest_net >= 0 else "down"
pct_str = round(latest_net / detail["oi"] * 100, 1) if detail["oi"] else 0

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>白糖 SUGAR NO.11 CFTC 持仓 · 1986–2026</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{--bg:#f7f5f0;--card:#ffffff;--ink:#1f2430;--sub:#7a8090;--red:#c0392b;--green:#1e8a5a;--blue:#2f6fb0;--amber:#c8862e;--line:#e8e4dc;--accent:#b08d57}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:36px 40px 60px;line-height:1.6}
.wrap{max-width:1160px;margin:0 auto}
h1{font-size:24px;font-weight:700;letter-spacing:.5px}
.tag{display:inline-block;font-size:12px;color:var(--accent);border:1px solid var(--accent);border-radius:20px;padding:2px 12px;margin-left:10px;vertical-align:3px}
.sub{color:var(--sub);font-size:13px;margin-top:8px}
.rule{height:1px;background:var(--line);margin:20px 0}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.card .k{font-size:12px;color:var(--sub)}
.card .v{font-size:22px;font-weight:700;margin-top:6px}
.card .d{font-size:11px;color:var(--sub);margin-top:4px}
.up{color:var(--red)}.down{color:var(--green)}
.chart{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:16px}
.chart h2{font-size:15px;font-weight:600;margin-bottom:4px}
.chart .note{font-size:12px;color:var(--sub);margin-bottom:8px}
.chartbox{width:100%;height:380px}
.chartbox.tall{height:300px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.note2{font-size:12px;color:var(--sub);margin-top:18px;padding:14px 16px;background:#efece5;border-radius:10px}
.note2 b{color:var(--ink)}
</style>
</head>
<body>
<div class="wrap">
  <h1>白糖 SUGAR NO.11 · CFTC 持仓全历史 <span class="tag">Futures-Only · 1986–2026</span></h1>
  <div class="sub">数据源：CFTC 官方 Futures-Only (deacot) legacy 报告 · 单位：张（112,000 磅/张） · 频率：1986–1991 半月、1993 起周度 · 交易所链 CSCE → NYBOT → ICE US</div>
  <div class="rule"></div>

  <div class="cards">
    <div class="card"><div class="k">最新非商业净头寸 (nc_net)</div>
      <div class="v @@CLS@@">@@NET@@</div><div class="d">@@DATE@@ · 全历史 @@PA@@ 分位 / 近5年 @@P5@@ 分位</div></div>
    <div class="card"><div class="k">未平仓合约 OI</div>
      <div class="v">@@OI@@</div><div class="d">@@DATE@@ · 净多占比 @@PCT@@%</div></div>
    <div class="card"><div class="k">历史最高净多</div>
      <div class="v up">@@MX@@</div><div class="d">@@MXD@@</div></div>
    <div class="card"><div class="k">历史最深净空</div>
      <div class="v down">@@MN@@</div><div class="d">@@MND@@</div></div>
  </div>

  <div class="chart"><h2>非商业净头寸（40 年，周度）</h2>
    <div class="note">红=净多、绿=净空；净多头寸为正表示投机/基金看多</div>
    <div id="c1" class="chartbox tall"></div></div>

  <div class="grid2">
    <div class="chart"><h2>商业净头寸（套保盘，与投机盘镜像）</h2>
      <div class="note">商业=生产者/贸易商/加工商套保</div><div id="c2" class="chartbox"></div></div>
    <div class="chart"><h2>未平仓合约 OI</h2>
      <div class="note">市场规模指标</div><div id="c3" class="chartbox"></div></div>
  </div>

  <div class="note2">
    <b>口径说明：</b>本序列为 CFTC <b>纯期货（Futures-Only）</b>legacy 报告的 <b>(All) 总口径</b>，自 1986 年起全程统一、不含期权。
    1986-09–1992-09 过渡期存在 Old/Other 两套细分，(All)=Old+Other，本序列一律取 (All)。
    与项目此前 combined（含期权）口径相比，重叠期 1995–2026 净头寸相关系数 r=0.9827，本口径更纯且历史更长 9 年。
    <br><b>字段：</b>nc_l/nc_s 非商业多空 · c_l/c_s 商业多空 · nr_l/nr_s 非报告多空 · nc_sp 非商业套利 · nc_net=nc_l−nc_s（正=净多）。
  </div>
</div>
<script>
var D = @@PAYLOAD@@;
var dates = D.dates, oi = D.oi, nc_net = D.nc_net, c_net = D.c_net;
var RED='#c0392b', GREEN='#1e8a5a', BLUE='#2f6fb0', AMBER='#c8862e';
function mk(id, series){
  var c = echarts.init(document.getElementById(id));
  c.setOption({
    backgroundColor:'transparent',
    grid:{left:52,right:16,top:16,bottom:40},
    tooltip:{trigger:'axis',axisPointer:{type:'cross',label:{backgroundColor:'#555'}}},
    legend:{top:0,right:0,textStyle:{color:'#7a8090',fontSize:12}},
    xAxis:{type:'category',data:dates,boundaryGap:false,
      axisLine:{lineStyle:{color:'#c9c4ba'}},axisLabel:{color:'#9a9aa5',fontSize:11}},
    yAxis:{type:'value',axisLabel:{color:'#9a9aa5',fontSize:11,formatter:function(v){return v/1000+'k'}},
      splitLine:{lineStyle:{color:'#eeeae2'}}},
    dataZoom:[{type:'inside',start:0,end:100}],
    series:series
  });
  return c;
}
var c1 = mk('c1', [{name:'非商业净头寸',type:'line',data:nc_net,symbol:'none',smooth:true,
  lineStyle:{width:1.4,color:BLUE},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,
  colorStops:[{offset:0,color:'rgba(47,111,176,.25)'},{offset:1,color:'rgba(47,111,176,0)'}]}}}]);
var c2 = mk('c2', [{name:'商业净头寸',type:'line',data:c_net,symbol:'none',smooth:true,
  lineStyle:{width:1.2,color:AMBER}}]);
var c3 = mk('c3', [{name:'OI',type:'line',data:oi,symbol:'none',smooth:true,
  lineStyle:{width:1.2,color:'#8a5a2f'},areaStyle:{color:'rgba(138,90,47,.12)'}}]);
window.addEventListener('resize',function(){c1.resize();c2.resize();c3.resize();});
</script>
</body>
</html>"""

repl = {
    "@@PAYLOAD@@": payload,
    "@@NET@@": f"{latest_net:,}",
    "@@OI@@": f"{detail['oi']:,}",
    "@@PCT@@": str(pct_str),
    "@@DATE@@": last["date"],
    "@@PA@@": str(p_all),
    "@@P5@@": str(p_5y),
    "@@MX@@": f"{mx:,}",
    "@@MXD@@": mxd,
    "@@MN@@": f"{mn:,}",
    "@@MND@@": mnd,
    "@@CLS@@": net_cls,
}
for k, v in repl.items():
    html = html.replace(k, v)

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML ->", OUT_HTML)
print("最新一期:", detail)
