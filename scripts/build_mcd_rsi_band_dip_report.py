# -*- coding: utf-8 -*-
"""
MCD RSI 区间跌落买入（阶梯式越跌越买）报告
读取 results/mcd_rsi_band_dip.json
输出 reports/49_MCD_RSI区间跌落买入/index.html
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "49_MCD_RSI区间跌落买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "mcd_rsi_band_dip.json"), encoding="utf-8") as f:
    D = json.load(f)

BK_ORDER = ["35-40", "30-35", "<30"]
WINS = (5, 10, 20)


def pct(v, nd=2):
    return "—" if v is None else f"{v:+.2f}%"


def med(s, key, scale=100):
    return None if not s or s.get(key) is None else s[key]["median"] * (1 if key.startswith("er") else 1)


def fcell(v, pctf=True):
    if v is None:
        return "<td class='na'>—</td>"
    cls = "up" if v > 0 else "dn"
    s = f"{v:+.2f}%" if pctf else f"{v:.2f}"
    return f"<td class='{cls} nowrap'>{s}</td>"


# ---------- 表1 三档主表（中位） ----------
rows1 = []
chart_band = []
for bk in BK_ORDER:
    s = D["by_band"][bk]
    n = s["fwd20"]["n"]
    row = (f"<tr><td class='nowrap'><b>RSI {bk}</b></td><td>{n}</td>"
           f"{fcell(s['maxg20']['median'])}{fcell(s['fwd20']['median'])}"
           f"<td class='nowrap'>{s['er20']['median']:.2f}</td>"
           f"<td class='nowrap'>{s['win20']}%</td>"
           f"<td class='nowrap'>{s['ever_positive']}%</td>"
           f"{fcell(s['ex20']['median'])}</tr>")
    rows1.append(row)
    chart_band.append({"bk": bk, "n": n,
                       "maxg": round(s["maxg20"]["median"], 2),
                       "fwd": round(s["fwd20"]["median"], 2),
                       "er": round(s["er20"]["median"], 3),
                       "ex": round(s["ex20"]["median"], 2),
                       "win": s["win20"]})

# ---------- 表2 全量 vs cd10 ----------
rows2 = []
chart_cd10 = []
for bk in BK_ORDER:
    a = D["by_band"][bk]
    b = D["by_band_cd10"][bk]
    row = (f"<tr><td class='nowrap'><b>RSI {bk}</b></td>"
           f"<td>{a['fwd20']['n']}</td>{fcell(a['fwd20']['median'])}<td class='nowrap'>{a['win20']}%</td>{fcell(a['ex20']['median'])}"
           f"<td>{b['fwd20']['n']}</td>{fcell(b['fwd20']['median'])}<td class='nowrap'>{b['win20']}%</td>{fcell(b['ex20']['median'])}</tr>")
    rows2.append(row)
    chart_cd10.append({"bk": bk,
                       "all_fwd": a["fwd20"]["median"], "cd10_fwd": b["fwd20"]["median"],
                       "all_win": a["win20"], "cd10_win": b["win20"],
                       "all_ex": a["ex20"]["median"], "cd10_ex": b["ex20"]["median"]})

# ---------- 表3 阶段×档（fwd20 med） ----------
rows3 = []
chart_stage = []
for stg in ["疫情前", "疫情~2022", "本轮牛市"]:
    sb = D["stage_band"][stg]
    cells = ""
    for bk in BK_ORDER:
        s = sb[bk]
        n = s["fwd20"]["n"]
        if n == 0:
            cells += "<td class='na'>—</td>"
        else:
            v = s["fwd20"]["median"]
            cls = "up" if v > 0 else "dn"
            cells += f"<td class='{cls} nowrap'>{v:+.2f}%<span class='note2'> (n={n})</span></td>"
    rows3.append(f"<tr><td class='nowrap'><b>{stg}</b></td>{cells}</tr>")

# ---------- 表4 最近5次（三窗口 最大/最终/ER） ----------
def wrow(e):
    def g(v):
        if v is None:
            return "<td class='na'>—</td>"
        cls = "up" if v > 0 else "dn"
        return f"<td class='{cls} nowrap'>{v:+.2f}%</td>"

    def g2(v):
        if v is None:
            return "<td class='na'>—</td>"
        return f"<td class='nowrap'>{v:.2f}</td>"
    cells = ""
    for NN in WINS:
        cells += f"{g(e.get(f'maxg{NN}'))}{g(e.get(f'fwd{NN}'))}{g2(e.get(f'er{NN}'))}"
    return (f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'>{e['band']}</td><td>{e['rsi']}</td>"
            f"{cells}</tr>")


def whead():
    th = "<tr><th rowspan='2'>日期</th><th rowspan='2'>档位</th><th rowspan='2'>RSI</th>"
    for NN in WINS:
        th += f"<th colspan='3' class='grph'>{NN}日窗口<br>最大 / 最终 / ER</th>"
    th += "</tr><tr>"
    for _ in WINS:
        th += "<th>最大</th><th>最终</th><th>ER</th>"
    th += "</tr>"
    return th


recent_html = "".join(wrow(e) for e in D["recent"])

# ---------- 表5 年份分布 ----------
chart_year = D["year_dist"]

CHART = {"band": chart_band, "cd10": chart_cd10, "year": chart_year,
         "n_total": D["n_total"], "n_cd10": D["n_cd10"],
         "base_fwd": D["base"]["fwd"]["median"], "base_maxg": D["base"]["maxg"]["median"]}

echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCD · RSI 区间跌落买入（越跌越买阶梯式）</title>
__ECHARTS__
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;--amber:#b45309;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:13.5px;margin:14px 0 6px;color:#374151;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;}
  td.nowrap{white-space:nowrap;}
  .note2{color:var(--sub);font-size:11px;font-weight:400;}
  td.up{color:var(--verm);font-weight:600;white-space:nowrap;}
  td.dn{color:var(--teal);font-weight:600;white-space:nowrap;}
  td.na{color:#c3c8cf;white-space:nowrap;}
  th.grph{text-align:center;border-left:1px solid #dbe4ef;border-right:1px solid #dbe4ef;background:#eaf1fa;color:#374151;font-weight:700;font-size:11.5px;}
  tr.baserow td{background:#fbf7ee;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .callout{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}
  .callout.blue{border-color:#cfe0f5;background:#f0f6fd;}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>MCD · RSI 区间跌落买入（越跌越买阶梯式）</h1>
  <div class="meta">事件口径：当日收盘 RSI 档位比前日更低位 → 当日收盘买入 · 三档：35-40 / 30-35 / &lt;30（40 以上不买）· 每次跨区间独立统计 · 主口径无去重（449 事件）+ cd10 对照（195）· SPY 同窗口对照 · 2026-08-28</div>
  <div class="callout blue">
    <b>与 47/48 号的区别：</b>47/48 只在"RSI 下穿40首日"买入一次（后续 35/33/28 都不再买，&lt;30 档仅 5 次）；
    本报告改为<b>越跌越买</b>——只要收盘 RSI 从高区间跌入更低区间就再买一次（例：36 跌入 35-40 买第 1 次、次日 25 跌入 &lt;30 买第 2 次），
    每次买入独立统计 T+5/T+10/T+20 窗口。回答：<b>把每次跌入更低档都当成买入机会，收益结构如何？</b>
  </div>
</div>

<div class="card">
  <h2>结论速览</h2>
  <div class="verdict gr"><b>① "越跌越买"的绝对收益成立：档位越低，天花板越高。</b>
    449 次买入三档 fwd20 中位全为正（35-40 +1.28% / 30-35 +2.17% / &lt;30 +1.99%），
    且 maxG 随档位递增（+3.77% → +4.53% → +4.99%）——跌得越深弹得越猛，MCD 低位均值回归强度随深度递增。</div>
  <div class="verdict amber"><b>② &lt;30 档从"5 次接飞刀"变成"82 次可操作"：低位状态价值被捕捉。</b>
    原口径（下穿40首日）&lt;30 档仅 5 次且 fwd 中位 −4.5%（全是单日暴跌首日）；本口径把"渐进跌入超卖"的日子也算入（82 次），
    fwd 中位 <b>+1.99%</b>——同样买在 RSI&lt;30，渐进下跌时买比暴跌首日买好 6.5pp，直接验证 47 号"RSI&lt;30 状态有均值回归价值、暴跌时点无信息"。</div>
  <div class="verdict"><b>③ 但超额全 ≤ 0：抄底赚的是"自己弹回来"的钱，不是"跑赢大盘"的钱。</b>
    三档超额中位 −0.14 / −0.07 / <b>−1.32pp</b>——跌得越深超额越差（&lt;30 档对应市场恐慌期，SPY 反弹比 MCD 猛）。
    绝对收益正、相对跑输，是 MCD 防御属性（β 低、弹性弱）在超卖反弹中的固定模式。</div>
  <div class="verdict gr"><b>④ cd10 去重后 30-35 档凸显为唯一正超额子集：胜率 74.2%、超额 +0.71pp。</b>
    连续加仓（同一下跌段多次买入）拖累 30-35 档：全量 141 次超额 −0.07pp → 去重 31 次 +0.71pp、胜率从 64.5% 升到 74.2%。
    阶梯加仓中"第二次及以后的加仓"反而稀释了收益——首档触发（30-35）才是质量最高的买入。</div>
  <div class="verdict"><b>⑤ 本轮牛市信号仍在（2026 年 23 次）但超额全负（−1.4~−1.65pp）。</b>
    2023 以来三档 fwd20 中位 +1.30%~−0.62%，超额 −1.39~−1.65pp——MCD 低位反弹近年弹性收窄、相对 SPY 持续偏弱（与 48 号一致），
    绝对收益为正但作为"抄底策略"的相对价值有限。</div>
</div>

<div class="card">
  <h2>一、三档收益 vs 基率（449 次，T+20 中位）</h2>
  <div class="chart" id="ch_band"></div>
  <p class="src" style="margin-top:2px">柱 = maxG / fwd（中位，左轴）；点 = ER（右轴）。基率（全部重叠 20 日窗口）：MCD fwd 中位 +1.24%、maxG +3.40%。</p>
  <div class="scroll" style="margin-top:8px">
  <table>
    <thead><tr><th>档位</th><th>n</th><th>maxG20 中位</th><th>fwd20 中位</th><th>ER20 中位</th><th>胜率 T+20</th><th>曾解套率</th><th>超额20 中位</th></tr></thead>
    <tbody>__ROWS1__</tbody>
  </table>
  </div>
  <p class="src">三档绝对收益全为正、胜率 61%~64.5%；超额全 ≤0。&lt;30 档 maxG 最高（+4.99%）但超额最差（−1.32pp）——弹得高，但 SPY 弹得更猛。</p>
</div>

<div class="card">
  <h2>二、连续加仓是否有效：全量 vs cd10 去重对照</h2>
  <div class="grid2">
    <div class="chart" id="ch_cd10" style="height:340px"></div>
    <div class="scroll"><table>
      <thead><tr><th rowspan='2'>档位</th><th colspan='3' class='grph'>全量（连续加仓）</th><th colspan='3' class='grph'>cd10 去重（首档触发）</th></tr>
      <tr><th>n</th><th>fwd20 中位</th><th>胜率</th><th>n</th><th>fwd20 中位</th><th>胜率</th></tr></thead>
      <tbody>__ROWS2__</tbody>
    </table></div>
  </div>
  <p class="src" style="margin-top:8px">去重逻辑：事件日相隔 ≥10 交易日（同一波下跌只保留第一次触发）。30-35 档去重后胜率 64.5% → 74.2%、超额 −0.07 → +0.71pp——
    <b>同一波下跌中第二次及以后的加仓（跌入 30-35 后继续跌入 &lt;30 的那部分）拖累整体</b>；&lt;30 档去重后反而更差（+1.99% → +1.20%，超额 −2.63pp），因去重保留了更多暴跌首日。</p>
</div>

<div class="card">
  <h2>三、分阶段 × 档位（fwd20 中位）</h2>
  <div class="scroll"><table>
    <thead><tr><th>阶段</th><th>RSI 35-40</th><th>RSI 30-35</th><th>RSI &lt;30</th></tr></thead>
    <tbody>__ROWS3__</tbody>
  </table></div>
  <p class="src">疫情前：三档全正（+2.1~+2.7%，&lt;30 超额 −1.96pp）；本轮牛市：三档超额全负（−1.39~−1.65pp）、35-40 档 fwd 中位转负（−0.62%）——
    近年 MCD 低位买入只剩绝对收益、相对价值持续走弱。</p>
</div>

<div class="card">
  <h2>四、事件年份分布 + 最近 5 次买入</h2>
  <div class="chart" id="ch_year" style="height:240px"></div>
  <p class="src">事件集中在波动大年（2000 年 35 次峰值、2020-2026 每年 12~23 次）；2017 年仅 1 次（单边牛市 RSI 极少破 40）。</p>
  <h3 style="margin-top:14px">最近 5 次买入（三窗口 最大涨幅 / 最终收益 / ER）</h3>
  <div class="scroll"><table>
    <thead>__RECENT_HEAD__</thead>
    <tbody>__RECENT_ROWS__</tbody>
  </table></div>
  <p class="src">例：2026-07-21（35-40 档）T+20 最终 +1.17% 但 ER 仅 0.06（来回震荡）；2026-06-25（30-35 档）T+5 冲到 +6.08% 但 T+20 只剩 +0.08%、ER≈0——典型"冲高留不住"。</p>
</div>

<div class="card">
  <div class="src">数据：Yahoo Finance（adj_close）· 脚本：scripts/mcd_rsi_band_dip.py + build_mcd_rsi_band_dip_report.py · 数据文件：results/mcd_rsi_band_dip.json。
  主口径无 cd10 去重（连续加仓为设计意图，窗口重叠 → 独立性与显著性为上限，本报告数字为描述性统计）。
  <b>本报告仅为统计回测，不构成投资建议。</b></div>
</div>

</div>
<script>
var CHART = __DATA_JSON__;
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
(function(){
  var ch = echarts.init(document.getElementById("ch_band"));
  var b = CHART.band;
  ch.setOption({
    animation:false,
    legend:{data:["maxG 中位","fwd20 中位","ER 中位"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:55,right:55,top:38,bottom:30},
    xAxis:{type:"category",data:b.map(function(x){return "RSI "+x.bk;}),axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:[
      {type:"value",name:"%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
      {type:"value",name:"ER",min:0,max:0.35,axisLabel:{formatter:function(v){return v.toFixed(2);},color:"#9aa1ab"},splitLine:{show:false}}
    ],
    series:[
      {name:"maxG 中位",type:"bar",barWidth:16,data:b.map(function(x){return x.maxg;}),itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"fwd20 中位",type:"bar",barWidth:16,data:b.map(function(x){return x.fwd;}),itemStyle:{color:C.teal},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"ER 中位",type:"line",yAxisIndex:1,data:b.map(function(x){return x.er;}),lineStyle:{color:C.blue,width:1.6},symbol:"circle",symbolSize:6,itemStyle:{color:C.blue}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_cd10"));
  var d = CHART.cd10;
  ch.setOption({
    animation:false,
    legend:{data:["全量 fwd20","cd10 fwd20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:50,right:20,top:36,bottom:30},
    xAxis:{type:"category",data:d.map(function(x){return "RSI "+x.bk;}),axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"fwd20 中位 %",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"全量 fwd20",type:"bar",barWidth:14,data:d.map(function(x){return x.all_fwd;}),itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"cd10 fwd20",type:"bar",barWidth:14,data:d.map(function(x){return x.cd10_fwd;}),itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_year"));
  var y = CHART.year;
  ch.setOption({
    animation:false,
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:40,right:15,top:20,bottom:24},
    xAxis:{type:"category",data:y.map(function(x){return x.y;}),axisLabel:{color:"#4b5563",fontSize:10,interval:2}},
    yAxis:{type:"value",name:"事件数",minInterval:1,axisLabel:{color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[{type:"bar",data:y.map(function(x){return x.n;}),itemStyle:{color:C.orange,opacity:0.9},barWidth:"55%",
      label:{show:true,position:"top",fontSize:8,formatter:function(p){return p.value>0?p.value:"";}}}]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__ECHARTS__", echarts)
HTML = HTML.replace("__ROWS1__", "".join(rows1))
HTML = HTML.replace("__ROWS2__", "".join(rows2))
HTML = HTML.replace("__ROWS3__", "".join(rows3))
HTML = HTML.replace("__RECENT_HEAD__", whead())
HTML = HTML.replace("__RECENT_ROWS__", recent_html)
HTML = HTML.replace("__DATA_JSON__", json.dumps(CHART, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")
