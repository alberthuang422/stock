# -*- coding: utf-8 -*-
"""KBWB vs MS 相关性研报生成器（读 results/kbwb_ms_corr.json）
规范：普通三引号模板 + @@PLACEH@@ 占位符 replace（避免 f-string 与 JS 花括号冲突）
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "13_kbwb_ms")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "kbwb_ms_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

B = D["blocks"]
F = D["fisher"]
PB = D["price_blocks"]
R = D["ratio"]
meta = D["meta"]
monthly_mean = sum(x["corr"] for x in D["monthly"]) / len(D["monthly"])
m3y = [x for x in D["monthly"] if x["month"] >= "2023-08"]
monthly_3y_mean = sum(x["corr"] for x in m3y) / len(m3y)

def js(o):
    return json.dumps(o, ensure_ascii=False)

# ---------- 动态片段 ----------
kpis = f"""
    <div class="kpis">
      <div class="kpi"><div class="num">{B[0]['pearson']:.2f}</div><div class="lab">日收益 Pearson 相关（全期）</div></div>
      <div class="kpi"><div class="num">{B[0]['spearman']:.2f}</div><div class="lab">Spearman 秩相关（全期）</div></div>
      <div class="kpi"><div class="num">β {B[0]['beta']:+.2f}</div><div class="lab">MS 对 KBWB 的 beta（全期）</div></div>
      <div class="kpi"><div class="num">R² {B[0]['r2']:.2f}</div><div class="lab">KBWB 收益可解释 MS 的方差占比</div></div>
      <div class="kpi"><div class="num">{B[0]['p_same_dir']:.0f}%</div><div class="lab">同涨同跌占比（全期）</div></div>
    </div>"""

verdict = f"""
    <div class="verdict">
      <div class="t">核心结论</div>
      <div class="b">KBWB 与 MS 日收益相关系数全期 <span class="hlb">0.82</span>、近 1 年 <span class="hlb">0.80</span>，
        属<b>高度正相关</b>——MS 的日常波动约 <span class="hlb">68%</span> 可由银行板块（KBWB）解释，
        β≈1.0、同涨同跌约 <span class="hlb">81%</span>。但 <span class="hl">MS 长期显著跑赢板块</span>：
        全期累计 <span class="hl">+1735% vs +591%</span>，相对强弱（KBWB/MS）归一化从 1.00 跌至 <span class="hl">0.38</span>，
        超额收益主要来自 2013/2016/2021 等牛市年份。相关性与超额是<b>两个独立维度</b>——
        高相关不意味着收益对齐。
      </div>
    </div>"""

blocks_rows = ""
for b in B:
    blocks_rows += (f"""<tr><td>{b['name']}</td><td>{b['n']:,}</td><td class="hlb">{b['pearson']:.3f}</td>"""
                    f"""<td>{b['spearman']:.3f}</td><td>{b['beta']:+.2f}</td><td>{b['r2']:.2f}</td>"""
                    f"""<td>{b['p_same_dir']:.0f}%</td><td class="up">{b['ms_ret_on_kbwb_up']:+.2f}%</td>"""
                    f"""<td class="dn">{b['ms_ret_on_kbwb_dn']:+.2f}%</td></tr>""")

fisher_html = ("不显著" if not F["sig"] else "显著")

price_rows = ""
for key, label, kb, ms in [
    ("full", "全期（2011-11 起）", PB["full"]["kbwb"], PB["full"]["ms"]),
    ("after_split", f'分界后（{D["split"]} 起）', PB["after_split"]["kbwb"], PB["after_split"]["ms"]),
    ("last1y", "近 1 年（2025-08 起）", PB["last1y"]["kbwb"], PB["last1y"]["ms"]),
]:
    price_rows += f"""<tr><td>{label}</td>
        <td><span class="hl">+{kb['total_ret']:.0f}%</span> / <b class="hl">+{ms['total_ret']:.0f}%</b></td>
        <td>{kb['max_dd']:.0f}% / {ms['max_dd']:.0f}%</td>
        <td>{kb['ann_vol']:.0f}% / {ms['ann_vol']:.0f}%</td>
        <td>{kb['sharpe']:.2f} / <b>{ms['sharpe']:.2f}</b></td></tr>"""

# ---------- 模板 ----------
html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KBWB vs MS · 银行板块 ETF 与投行巨头 · 相关性分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#d23b2e;--green:#1a9e4b;--blue:#1f4e79;--orange:#e67e22;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:22px;font-weight:700;color:var(--ink);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .verdict{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:15.5px;font-weight:700;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:380px;}
  .chart.sm{height:320px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);}
  .tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .tag.kbwb{background:#e8eef6;color:var(--blue);} .tag.ms{background:#fdf1e7;color:#c05c0b;}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>KBWB vs MS · 银行板块 ETF 与投行巨头的联动拆解</h1>
    <div class="meta">@@META@@</div>
    @@KPIS@@
    @@VERDICT@@
  </div>

  <div class="card">
    <h2>① 分阶段相关性（Pearson / Spearman / β / 同向占比）</h2>
    <div class="scroll">
    <table>
      <tr><th>区间</th><th>样本 n</th><th>Pearson</th><th>Spearman</th><th>β (MS~KBWB)</th><th>R²</th><th>同向占比</th><th>KBWB 涨日 MS 日均</th><th>KBWB 跌日 MS 日均</th></tr>
      @@BLOCKS_ROWS@@
    </table>
    </div>
    <div class="note">分界点 @@SPLIT@@ 前后相关性差异 Fisher z 检验：z = @@Z@@，p = @@P@@，<b>@@FISHER_SIG@@</b> —— 2026-02 以来高相关结构并未改变，仅数值小幅回落（0.825 → 0.805）。近 1 年 Pearson 0.795，Spearman 0.773，β 升至 <b>+1.08</b>（MS 波动相对板块放大）。</div>
  </div>

  <div class="card">
    <h2>② 长期走势一览（2011-11 起，归一化 = 1）</h2>
    <div class="chart" id="ch_full"></div>
    <div class="note">线条区分：<span class="tag kbwb">KBWB 实线</span> <span class="tag ms">MS 虚线</span>。MS 长期显著跑赢，相对强弱（KBWB/MS）最新归一化 <b>@@RATIO_LATEST@@</b>（2011-11 = 1），高点 1.53（2012-07），低点 0.34（2026-06）。</div>
  </div>

  <div class="card">
    <h2>③ 2026 年以来走势（归一化 = 1，同期对照）</h2>
    <div class="chart sm" id="ch_2026"></div>
    <div class="note">2026 年以来 KBWB +@@Y26_KBWB@@% vs MS +@@Y26_MS@@%（差 @@Y26_DIFF@@pp），联动仍在但 MS 继续跑赢。</div>
  </div>

  <div class="card">
    <h2>④ 滚动 60 日相关性（2011-11 起）</h2>
    <div class="chart" id="ch_roll"></div>
    <div class="note">滚动 60 日相关长期在 0.65 ~ 0.93 区间运行，中位数约 0.83；2026 年 6 月触达历史区间下沿后回升，最新约 <b>0.75</b>。无长期脱钩迹象。</div>
  </div>

  <div class="card">
    <h2>⑤ 月频相关性（2011-11 起）</h2>
    <div class="chart" id="ch_monthly"></div>
    <div class="note">月频相关均值 @@MONTHLY_MEAN@@，近 36 个月均值约 @@MONTHLY_3Y@@，最新（2026-08）0.75。月度口径下相关性同样稳定在高位。</div>
  </div>

  <div class="card">
    <h2>⑥ 日收益散点（近 3 年，分界前 / 分界后分色）</h2>
    <div class="chart" id="ch_scatter"></div>
    <div class="note">散点沿 45° 线聚集：KBWB 涨 1% 时 MS 平均 +1.20%，跌 1% 时平均 −1.14%（全期口径），斜率≈β。分界后（◆ 深紫点）散点无明显偏移，说明相关性结构未变。</div>
  </div>

  <div class="card">
    <h2>⑦ 年度收益对比（%）</h2>
    <div class="chart" id="ch_year"></div>
    <div class="note">红 = 正收益，绿 = 负收益（正负均叠数值标签，色弱可辨）。<b>MS 跑赢年份</b>：2013（+61 vs +33）、2020（+36 vs −11，疫后牛市）、2021（+47 vs +39）、2023（+13 vs −2）、2025（+46 vs +32）；<b>KBWB 跑赢年份</b>：2015（+0.3 vs −16）、2012（+28 vs +20）。2022 双双大跌（MS −12% 韧性更强）。</div>
  </div>

  <div class="card">
    <h2>⑧ 价格表现与风险对比</h2>
    <div class="scroll">
    <table>
      <tr><th>区间</th><th>累计收益 KBWB / MS</th><th>最大回撤 KBWB / MS</th><th>年化波动 KBWB / MS</th><th>夏普 KBWB / MS</th></tr>
      @@PRICE_ROWS@@
    </table>
    </div>
    <div class="keypoint"><b>解读：</b>高相关 ≠ 等收益。MS 全期年化 21.8%（夏普 0.69）vs KBWB 年化 14.0%（夏普 0.53）。MS 的波动（32%）高于板块（27%），回撤却与板块相当——意味着 MS 的更高收益并非靠更高尾部风险换取，而是牛市中的更高弹性（图⑦中大年份跑赢）。KBWB（等权银行 ETF）更贴「传统借贷银行」加权，MS 属投行+财富管理，β 放大来自其杠杆与顺周期特性。</div>
  </div>

  <div class="card">
    <h2>⑨ 相对强弱走势（KBWB / MS 比值，归一化）</h2>
    <div class="chart sm" id="ch_ratio"></div>
    <div class="note">KBWB/MS 比值长期下行（MS 相对走强为主），2012-07 至 2026-06 单边下滑，2026-06 见底 @@RATIO_MIN@@ 后小幅回升至 @@RATIO_LATEST@@。比值度量的是一篮子银行（KBWB）相对投行个股（MS）的相对强弱。</div>
  </div>

  <div class="card">
    <h2>⑩ 方法口径与局限</h2>
    <ul>
      <li><b>数据</b>：Yahoo Finance 日线复权收盘价（adj_close）；KBWB 2011-11 上市，窗口 2011-11-02 ~ @@END@@，n = @@N@@。</li>
      <li><b>相关口径</b>：日收益率 Pearson / Spearman；滚动 60 日与月频（月末收益合并至少 2 个点）两种窗口均计算；β 为 MS 对 KBWB 的 OLS 斜率。</li>
      <li><b>分阶段</b>：以 @@SPLIT@@ 为结构分界点（沿项目既有口径），Fisher z 检验分界前后相关系数差异。</li>
      <li><b>局限</b>：KBWB 为等权银行 ETF（覆盖传统银行+大行），与 MS 个股并非同一资产，相关性度量的是「投行个股 vs 板块」的联动而非同质资产对比；未扣交易成本；年度统计含 2020 疫情极端年；β 估计未加入市场因子，与 CAPM β 不同。</li>
    </ul>
  </div>

  <div class="card dis">
    <div style="font-weight:600;margin-bottom:6px;">免责声明</div>
    本报告仅为数据分析参考，不构成任何投资建议。历史相关性不代表未来表现，文中所有统计基于历史数据，存在样本区间依赖。
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
RED = "#d23b2e"; GREEN = "#1a9e4b"; ORANGE = "#e67e22"; BLUE = "#1f4e79"; GRAY = "#999";
KB = "#1f4e79"; MS = "#e67e22";

// 图② 长期归一化走势
(function(){
  var ch = echarts.init(document.getElementById("ch_full"));
  var d = DATA.full_series;
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":v.toFixed(2)); } },
    legend:{ data:["KBWB (实线)","MS (虚线)"], top:0 },
    grid:{ left:60, right:30, top:40, bottom:50 },
    xAxis:{ type:"category", data:d.map(function(x){return x.date;}), axisLabel:{ fontSize:10, interval: Math.floor(d.length/8) } },
    yAxis:{ type:"value", name:"归一化(起点=1)", scale:true },
    dataZoom:[{ type:"inside", start:0, end:100 }],
    series:[
      { name:"KBWB (实线)", type:"line", data:d.map(function(x){return x.kbwb;}), showSymbol:false,
        lineStyle:{ color:KB, width:2 }, itemStyle:{ color:KB } },
      { name:"MS (虚线)", type:"line", data:d.map(function(x){return x.ms;}), showSymbol:false,
        lineStyle:{ color:MS, width:2, type:"dashed" }, itemStyle:{ color:MS } }
    ]
  });
})();

// 图③ 2026 走势
(function(){
  var ch = echarts.init(document.getElementById("ch_2026"));
  var d = DATA.series_2026;
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":v.toFixed(3)); } },
    legend:{ data:["KBWB","MS"], top:0 },
    grid:{ left:60, right:30, top:40, bottom:40 },
    xAxis:{ type:"category", data:d.map(function(x){return x.date;}), axisLabel:{ fontSize:10, interval: Math.floor(d.length/6) } },
    yAxis:{ type:"value", name:"归一化(2026-01=1)", scale:true },
    series:[
      { name:"KBWB", type:"line", data:d.map(function(x){return x.kbwb;}), symbol:"circle", symbolSize:3,
        lineStyle:{ color:KB, width:2 } },
      { name:"MS", type:"line", data:d.map(function(x){return x.ms;}), symbol:"diamond", symbolSize:3,
        lineStyle:{ color:MS, width:2, type:"dashed" } }
    ]
  });
})();

// 图④ 滚动60日相关
(function(){
  var ch = echarts.init(document.getElementById("ch_roll"));
  var d = DATA.rolling60;
  var dd = d.filter(function(x){return x.corr!=null;});
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":v.toFixed(3)); } },
    grid:{ left:60, right:30, top:30, bottom:45 },
    xAxis:{ type:"category", data:dd.map(function(x){return x.date;}), axisLabel:{ fontSize:10, interval: Math.floor(dd.length/8) } },
    yAxis:{ type:"value", min:0.5, max:1, axisLabel:{ formatter:function(v){return v.toFixed(2);} } },
    dataZoom:[{ type:"inside", start:0, end:100 }],
    series:[
      { name:"60日相关", type:"line", data:dd.map(function(x){return x.corr;}), showSymbol:false,
        lineStyle:{ color:BLUE, width:1.5 },
        areaStyle:{ color:"rgba(31,78,121,0.10)" },
        markLine:{ silent:true, symbol:"none",
          data:[ { yAxis:0.83, lineStyle:{color:GRAY,type:"dashed"}, label:{formatter:"均值~0.83",fontSize:9,color:GRAY} } ] } }
    ]
  });
})();

// 图⑤ 月频相关
(function(){
  var ch = echarts.init(document.getElementById("ch_monthly"));
  var d = DATA.monthly;
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":v.toFixed(3)); } },
    grid:{ left:60, right:30, top:30, bottom:45 },
    xAxis:{ type:"category", data:d.map(function(x){return x.month;}), axisLabel:{ fontSize:9, interval: Math.floor(d.length/10) } },
    yAxis:{ type:"value", min:0.4, max:1, axisLabel:{ formatter:function(v){return v.toFixed(2);} } },
    dataZoom:[{ type:"inside", start:0, end:100 }],
    series:[
      { name:"月频相关", type:"bar", data:d.map(function(x){return x.corr;}),
        itemStyle:{ color:function(p){
            var v = p.value;
            return v>=0.7 ? BLUE : (v>=0.5 ? "#7fa8d4" : "#c98d5e");
          } },
        markLine:{ silent:true, symbol:"none", data:[{yAxis:0.7, lineStyle:{color:GRAY,type:"dashed"}, label:{formatter:"0.70",fontSize:9,color:GRAY}}] } }
    ]
  });
})();

// 图⑥ 散点
(function(){
  var ch = echarts.init(document.getElementById("ch_scatter"));
  var d = DATA.scatter;
  ch.setOption({
    tooltip:{ trigger:"item", formatter:function(p){
        var x = p.data[0]; var y = p.data[1];
        return p.data[3] + "<br>KBWB " + x.toFixed(2) + "%　MS " + y.toFixed(2) + "%";
      } },
    legend:{ data:["分界前 (2011-2026-01)","分界后 (2026-02 起)"], top:0 },
    grid:{ left:60, right:40, top:40, bottom:45 },
    xAxis:{ type:"value", name:"KBWB 日收益 %", scale:true,
      axisLabel:{formatter:function(v){return v+"%";}} },
    yAxis:{ type:"value", name:"MS 日收益 %", scale:true,
      axisLabel:{formatter:function(v){return v+"%";}} },
    series:[
      { name:"分界前 (2011-2026-01)", type:"scatter",
        data:d.filter(function(x){return !x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:3.5, itemStyle:{ color:"rgba(31,78,121,0.35)" } },
      { name:"分界后 (2026-02 起)", type:"scatter",
        data:d.filter(function(x){return x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:7, symbol:"diamond", itemStyle:{ color:"rgba(214,51,132,0.8)" } }
    ]
  });
})();

// 图⑦ 年度收益
(function(){
  var ch = echarts.init(document.getElementById("ch_year"));
  var ys = DATA.years;
  var k = ys.map(function(y){return DATA.yearly[y].kbwb;});
  var m = ys.map(function(y){return DATA.yearly[y].ms;});
  ch.setOption({
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"}, valueFormatter:function(v){ return (v==null?"-":v.toFixed(1)+"%"); } },
    legend:{ data:["KBWB","MS"], top:0 },
    grid:{ left:60, right:20, top:40, bottom:30 },
    xAxis:{ type:"category", data:ys.map(function(y){return String(y);}) },
    yAxis:{ type:"value", name:"%", axisLabel:{ formatter:function(v){return v+"%";} } },
    series:[
      { name:"KBWB", type:"bar", data:k, barGap:"10%",
        itemStyle:{ color:function(p){ return p.value>=0 ? "#71a2cc" : "#7fbf9a"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } },
      { name:"MS", type:"bar", data:m,
        itemStyle:{ color:function(p){ return p.value>=0 ? ORANGE : "#c98d5e"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } }
    ]
  });
})();

// 图⑨ 相对强弱
(function(){
  var ch = echarts.init(document.getElementById("ch_ratio"));
  var d = DATA.full_series;
  var ratio = d.map(function(x){ return x.kbwb / x.ms; });
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":v.toFixed(3)); } },
    grid:{ left:60, right:30, top:30, bottom:45 },
    xAxis:{ type:"category", data:d.map(function(x){return x.date;}), axisLabel:{ fontSize:10, interval: Math.floor(d.length/8) } },
    yAxis:{ type:"value", name:"KBWB / MS (归一)", scale:true },
    dataZoom:[{ type:"inside", start:0, end:100 }],
    series:[
      { name:"KBWB/MS 相对强弱", type:"line", data:ratio, showSymbol:false,
        lineStyle:{ color:"#7048e8", width:1.8 }, itemStyle:{ color:"#7048e8" } }
    ]
  });
})();
</script>
</body>
</html>
"""

# ---------- 替换占位符 ----------
y26 = D["yearly"]["2026"]
repl = {
    "@@META@@": f'{meta["kbwb"]} vs {meta["ms"]} · 分析窗口 {D["period"]["start"]} ~ {D["period"]["end"]}（共 {D["period"]["n"]:,} 个交易日）· {meta["source"]}',
    "@@KPIS@@": kpis,
    "@@VERDICT@@": verdict,
    "@@BLOCKS_ROWS@@": blocks_rows,
    "@@PRICE_ROWS@@": price_rows,
    "@@SPLIT@@": D["split"],
    "@@Z@@": str(F["z"]),
    "@@P@@": str(F["p_value"]),
    "@@FISHER_SIG@@": fisher_html,
    "@@RATIO_LATEST@@": f'{R["norm_latest"]:.2f}',
    "@@RATIO_MIN@@": f'{R["min"]:.2f}',
    "@@Y26_KBWB@@": f'{y26["kbwb"]:+.1f}',
    "@@Y26_MS@@": f'{y26["ms"]:+.1f}',
    "@@Y26_DIFF@@": f'{y26["diff"]:+.1f}',
    "@@MONTHLY_MEAN@@": f'{monthly_mean:.2f}',
    "@@MONTHLY_3Y@@": f'{monthly_3y_mean:.2f}',
    "@@END@@": D["period"]["end"],
    "@@N@@": f'{D["period"]["n"]:,}',
}
for k, v in repl.items():
    html = html.replace(k, v)
html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + js(D) + ";")

out_path = os.path.join(OUT_DIR, "kbwb_ms_corr_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={os.path.getsize(out_path)}")