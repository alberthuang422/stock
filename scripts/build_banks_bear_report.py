# -*- coding: utf-8 -*-
"""熊陡专题研报生成器：当前形态判定 + 严格熊陡/长端领涨下 JPM/MS/BAC 表现"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "09_banks_bear_steep")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "steep_banks_bear.json"), encoding="utf-8") as f:
    R = json.load(f)

def js(o):
    return json.dumps(o, ensure_ascii=False)

# ---------- 数据 ----------
now_state = R["now_state"]
cc = R["cond_counts"]
stats = R["stats"]
bear_months = R["bear_month_rows"]
leadB_months = R["leadB_month_rows"]
ep_lead = R["episodes"]["lead"]
ep_bear = R["episodes"]["bear"]
weekly = R["weekly"]
fwd = R["forward"]
cases = R["cases"]
case_summary = R["case_summary"]

# ---------- HTML 工具 ----------
def cell(v, fmt="{:+.2f}%", na="<td class=na>-</td>"):
    if v is None: return na
    cls = "up" if v > 0 else "dn" if v < 0 else ""
    return f"<td class='{cls}'>{fmt.format(v)}</td>"

def cellpct(v, na="<td class=na>-</td>"):
    if v is None: return na
    return f"<td>{v}%</td>"

# 形态判定表
now_rows = ""
for s in now_state:
    if "type" in s:
        now_rows += (f"<tr><td>{s['window']}</td><td>{s['start']} ~ {s['end']}</td>"
                     f"<td>{s['d2_bp']:+.0f}bp</td><td>{s['d10_bp']:+.0f}bp</td>"
                     f"<td>{s['slope_bp']:+.0f}bp</td><td><b>{s['type']}</b></td></tr>")
    else:
        now_rows += (f"<tr><td>{s['window']}</td><td>{s['end']}</td>"
                     f"<td>{s['y2']}%</td><td>{s['y10']}%</td>"
                     f"<td>{s['slope_bp']:.0f}bp</td><td class=na>—</td></tr>")

# 统计表（月频）
def stat_row(name, k, note=""):
    st = stats[k]
    b = st.get("bank3")
    if not b or not b.get("n"):
        return f"<tr><td><b>{name}</b></td><td class=na colspan=8>-</td></tr>"
    return (f"<tr><td><b>{name}</b></td><td>{b['n']} 个月</td>"
            + cell(st["jpm"]["median"]) + cell(st["bac"]["median"]) + cell(st["ms"]["median"])
            + cell(b["median"]) + cellpct(b["win_rate"])
            + cell(st["gspc"]["median"]) + cell(b.get("xs_median"), "{:+.2f}pp") + "</tr>")

t_rows = ""
t_rows += stat_row("长端领涨（合计）", "lead_total")
t_rows += stat_row("　├ A：严格熊陡（2Y 降）", "lead_A")
t_rows += stat_row("　├ B：2Y 平 + 10Y 升", "lead_B")
t_rows += stat_row("　└ C：加息陡·长端领涨", "lead_C")
t_rows += stat_row("严格熊陡（独立口径）", "bear_strict")

# B 子类明细
b_rows = ""
for r in sorted(leadB_months, key=lambda x: x["month"]):
    b_rows += (f"<tr><td>{r['month']}</td><td>{r['y2_chg']:+.0f}bp</td><td>{r['y10_chg']:+.0f}bp</td>"
               f"<td class='up'>{r['slope_chg']:+.0f}bp</td>"
               + cell(r["bank3"]) + cell(r["gspc"]) + "</tr>")

# 严格熊陡明细
bear_rows = ""
for r in sorted(bear_months, key=lambda x: x["month"]):
    bear_rows += (f"<tr><td>{r['month']}</td><td class='dn'>{r['y2_chg']:+.0f}bp</td>"
                  f"<td class='up'>{r['y10_chg']:+.0f}bp</td><td class='up'>{r['slope_chg']:+.0f}bp</td>"
                  + cell(r["bank3"]) + cell(r["gspc"]) + "</tr>")

# 周频
w_rows = ""
for k, name in [("bear", "严格熊陡"), ("lead", "长端领涨"), ("lead_sig10", "长端领涨·10Y≥10bp/周")]:
    st = weekly["stats"][k]
    b = st.get("bank3")
    if not b or not b.get("n"):
        w_rows += f"<tr><td>{name}</td><td class=na colspan=4>-</td></tr>"; continue
    w_rows += (f"<tr><td>{name}</td><td>{b['n']} 周</td>"
               + cell(b["median"]) + cellpct(b["win_rate"]) + cell(st["gspc"]["median"]) + "</tr>")

# 持有
f_rows = ""
for tag, nm in [("m3", "后 3 个月"), ("m6", "后 6 个月"), ("m12", "后 12 个月")]:
    s = fwd[tag]
    b = s.get("bank3") if s else None
    if not b or not b.get("n"):
        f_rows += f"<tr><td>{nm}</td><td class=na colspan=5>-</td></tr>"; continue
    f_rows += (f"<tr><td>{nm}</td><td>{b['n']} 段</td>"
               + cell(b["median"]) + cellpct(b["win_rate"])
               + cell(s["jpm"]["median"]) + cell(s["ms"]["median"]) + cell(s["gspc"]["median"]) + "</tr>")

# 案例
c_rows = ""
for c in case_summary:
    k = "对照" in c["label"]
    c_rows += (f"<tr><td>{c['label']}</td><td class='{'up' if c['slope_chg']>0 else 'dn'}'>{c['slope_chg']:+.0f}bp</td>"
               + cell(c.get("bank3")) + cell(c.get("jpm")) + cell(c.get("bac")) + cell(c.get("ms"))
               + cell(c.get("kre")) + cell(c.get("gspc")) + "</tr>")

# KPI
stb = stats["bear_strict"]["bank3"]
stl = stats["lead_total"]["bank3"]
bB = stats["lead_B"]["bank3"]
bC = stats["lead_C"]["bank3"]
w12 = fwd["m12"]["bank3"]

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>熊陡专题：当前形态判定 + 10Y 领涨时 JPM/MS/BAC 表现</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1240px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:20px;font-weight:700;}
  .kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .verdict{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:15px;font-weight:600;line-height:1.75;}
  .verdict .b .hl{color:var(--blue);}
  .verdict .b .hl2{color:var(--red);}
  .verdict .b .hl3{color:var(--purple);}
  .warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;margin-top:10px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .chart.sm{height:330px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
  <h1>熊陡专题：现在是熊陡吗？10Y 领涨时 JPM / MS / BAC 怎么走？</h1>
  <div class="meta">数据窗口：1976-07 ~ 2026-07（月频 601 个月）+ 2026-08 日频｜口径：严格熊陡 = 2Y 降 &amp; 10Y 升；长端领涨 = 10Y 升 &amp; 升幅≥2Y｜bank3 = JPM/BAC/MS 等权｜数据源：FRED + Yahoo Finance</div>
  <div class="kpis">
    <div class="kpi"><div class="num">@@NOW_TYPE@@</div><div class="lab">当前形态（近 1~12 月全部窗口判定）</div></div>
    <div class="kpi"><div class="num up">@@B_MED@@%</div><div class="lab">B 型（2Y 平+10Y 升）bank3 单月中位 · 胜率 @@B_WR@@%</div></div>
    <div class="kpi"><div class="num up">@@BEAR_MED@@%</div><div class="lab">严格熊陡 bank3 单月中位（超额 @@BEAR_XS@@pp）</div></div>
    <div class="kpi"><div class="num up">@@W12_MED@@%</div><div class="lab">长端领涨期后 12 个月 bank3 中位（胜率 @@W12_WR@@%）</div></div>
    <div class="kpi"><div class="num">@@SLOPE@@bp</div><div class="lab">当前 10Y-2Y（2026-08-14）</div></div>
  </div>
  <div class="verdict">
    <div class="t">结论</div>
    <div class="b"><span class="hl2">严格口径下，当前不是熊陡</span>：近 1 / 3 / 6 / 12 个月 2Y 全部上行（+1 / +17 / +77 / +45bp），10Y 同步上行（+11 / +21 / +64 / +39bp）——教科书定义这是「加息陡」，且 slope 近半年还收窄了 -13bp。<br>
    但你的直觉有数据支撑的一半：<span class="hl">近 1~3 个月 10Y 升幅明显大于 2Y（+11 vs +1、+21 vs +17bp），即「长端领涨」</span>。历史长端领涨（尤其 <span class="hl3">B 型：2Y 持平 + 10Y 升</span>，与当前最接近）是银行股最强窗口：单月 bank3 中位 @@B_MED@@%、胜率 @@B_WR@@%（2025-12 就是同形态实例：bank3 +4.5% vs SPY +0.5%）。<br>
    <b>关键区分</b>：熊陡若由「联储降息 + 长端担忧」驱动（1998-10 / 2001-01），银行股大涨；若由「信用危机」驱动（2008-10 / 2023-08），银行股大跌。当前 2Y 仍 4.17%、联储尚未降息——离真正熊陡还有「一次降息」的距离，现阶段更适用长端领涨（B 型）历史参考。</div>
  </div>
</div>

<div class="card">
  <h2>一、当前形态判定：数据说话</h2>
  <div class="scroll"><table>
    <tr><th>窗口</th><th>区间</th><th>2Y 变化</th><th>10Y 变化</th><th>slope 变化</th><th>判定</th></tr>
    @@NOW_ROWS@@
  </table></div>
  <div class="chart" id="c1"></div>
  <div class="note">近 24 个月 2Y（绿）/ 10Y（红）收益率与 10Y-2Y 利差（下方面积）。可见 2026-06 利差一度压到 30bp，7 月以来随 10Y 上冲 4.68% 重新走阔至 51bp——斜率扩张主要来自长端，符合「长端领涨」。</div>
</div>

<div class="card">
  <h2>二、长端领涨 vs 严格熊陡：历史收益</h2>
  <div class="scroll"><table>
    <tr><th>口径（月频）</th><th>样本</th><th>JPM 中位</th><th>BAC 中位</th><th>MS 中位</th><th>bank3 中位</th><th>bank3 胜率</th><th>S&amp;P500 中位</th><th>超额</th></tr>
    @@T_ROWS@@
  </table></div>
  <div class="chart sm" id="c2"></div>
  <div class="note">三子类互斥（A 严格熊陡 / B 2Y 平 / C 加息陡长端领涨）。<b>B 型最强</b>（bank3 +@@B_MED@@%、胜率 @@B_WR@@%，超额 +@@B_XS@@pp）；A 型（严格熊陡）次之；C 型（2Y 也在涨）最弱——2Y 上行的加息成本在吞噬长端利好。</div>
</div>

<div class="card">
  <h2>三、B 型（2Y 平 + 10Y 升）31 个月明细：为什么是最强窗口</h2>
  <div class="scroll" style="max-height:400px;overflow-y:auto;"><table>
    <tr><th>月份</th><th>2Y</th><th>10Y</th><th>slope</th><th>bank3</th><th>S&amp;P500</th></tr>
    @@B_ROWS@@
  </table></div>
  <div class="note">31 个月中 bank3 正收益 23 个（74%）。赢家集中在「增长/再通胀预期升温、但央行按兵不动」的窗口：2011-10（欧债危机缓解 +29.3%）、2009-05（复苏 +20.2%）、2021-02（Reflation +14.3%）、2012-12（财政悬崖解决 +14.1%）、2019-04（+10.2%）、2023-07（+8.3%）。输家 2022-12 / 2023-10 / 2024-01 为「加息周期中的长端反扑」——2Y 仍受加息压制、10Y 因通胀/供给冲高，此时银行股被估值与信用担忧压制。<b>机制：B 型 = 增长预期（息差利好）无加息成本（2Y 平），是银行股最舒服的定价环境。</b></div>
</div>

<div class="card">
  <h2>四、严格熊陡（2Y 降 + 10Y 升）37 个月明细：分化极大</h2>
  <div class="scroll" style="max-height:400px;overflow-y:auto;"><table>
    <tr><th>月份</th><th>2Y</th><th>10Y</th><th>slope</th><th>bank3</th><th>S&amp;P500</th></tr>
    @@BEAR_ROWS@@
  </table></div>
  <div class="note">严格熊陡整体 bank3 中位 +@@BEAR_MED@@%（超额 +@@BEAR_XS@@pp），但内部冰火两重天：<b>危机缓和型</b>（联储降息 + 恐慌消退）1998-10 bank3 +37.0%、2001-01 +19.6%、2019-10 +10.4%；<b>危机加深型</b>（信贷违约担忧）2008-10 -26.8%、2023-08 -7.3%、2010-09/10 跑输。2Y 下降 = 联储宽松信号，但若宽松是因为金融危机，银行股首当其冲。</div>
</div>

<div class="card">
  <h2>五、标志性案例：长端领涨 vs 危机对照</h2>
  <div class="scroll"><table>
    <tr><th>时期</th><th>slope</th><th>bank3</th><th>JPM</th><th>BAC</th><th>MS</th><th>KRE</th><th>S&amp;P500</th></tr>
    @@C_ROWS@@
  </table></div>
  <div class="grid2">
    <div class="chart sm" id="c4a"></div>
    <div class="chart sm" id="c4b"></div>
    <div class="chart sm" id="c4c"></div>
    <div class="chart sm" id="c4d"></div>
  </div>
  <div class="note">左上 1998-10（严格熊陡，LTCM 后联储 3 连降息 + 长端通胀担忧）：银行股一个月翻倍级反弹；右上 2016-11~12（Trump 交易，长端领涨）：bank3 +28.4%；左下 2021-01~03（Reflation）：bank3 +21.8%；右下对照·2020-02~05（危机牛陡）：bank3 -22.6%。绿/红 = 2Y/10Y（左轴），其余 = 收益%（右轴）。</div>
</div>

<div class="card">
  <h2>六、周频与持有</h2>
  <div class="scroll"><table>
    <tr><th>周频口径</th><th>样本</th><th>bank3 中位</th><th>bank3 胜率</th><th>S&amp;P500 中位</th></tr>
    @@W_ROWS@@
  </table></div>
  <div class="note">周频样本充足：长端领涨（10Y 升 ≥10bp/周）334 周中 bank3 中位 +0.43% vs SPY <b>-0.08%</b>——大幅走阔的周里银行股显著跑赢大盘。</div>
  <h3>长端领涨期结束后的持有表现</h3>
  <div class="scroll"><table>
    <tr><th>持有期</th><th>样本</th><th>bank3 中位</th><th>bank3 胜率</th><th>JPM 中位</th><th>MS 中位</th><th>S&amp;P500 中位</th></tr>
    @@F_ROWS@@
  </table></div>
  <div class="note">以每个长端领涨期（月频，合计 @@EP_N@@ 段）结束日为锚。后 12 个月 bank3 中位 @@W12_MED@@%、胜率 @@W12_WR@@%，跑赢 SPY（@@W12_SPY@@%）——长端领涨作为中期信号偏正面。</div>
</div>

<div class="card">
  <h2>结论</h2>
  <h3>1. 「现在是熊陡」需要修正</h3>
  <p>教科书熊陡 = 2Y 降 + 10Y 升。当前 2Y 在升（近 1/3/6/12 月 +1/+17/+77/+45bp），所以严格判定是<b>加息陡</b>；但近 1-3 月 <b>10Y 升幅明显大于 2Y</b>，斜率的扩张完全由长端贡献——这是「长端领涨」形态，方向上有熊陡的色彩。</p>
  <h3>2. 如果继续「长端领涨」：历史银行股明确占优</h3>
  <p>最接近当前的是 <b>B 型（2Y 平 + 10Y 升）</b>：单月 bank3 中位 @@B_MED@@%、胜率 @@B_WR@@%、超额 +@@B_XS@@pp，31 个月中 23 个月正收益；最近实例 2025-12（2Y 持平、10Y +16bp）bank3 +4.5% vs SPY +0.5%。周频口径同样占优（334 周，SPY 为负时 bank3 仍 +0.43%）。</p>
  <h3>3. 如果 2Y 开始降（联储转向）→ 进入真正熊陡：分化取决于成因</h3>
  <p>严格熊陡 37 个月中位 +@@BEAR_MED@@%（超额 +@@BEAR_XS@@pp），但 1998-10 / 2001-01 大涨 vs 2008-10 / 2023-08 大跌的分水岭是「降息是为了救什么」：宽松 + 长端因增长/通胀预期升 = 银行大涨；宽松 + 长端因信用/主权担忧升 = 银行大跌。当前若联储开始降息而 10Y 因财政/供给担忧继续上行，需重点观察信用利差与存款成本，不能只看曲线形态。</p>
  <div class="warn">局限：B 型样本仅 31 个月，中位受 2011-10（+29.3%）等极端值影响；严格熊陡 37 个月同样样本小；月频判定依赖月末值；未计股息与成本。统计显著性：长端领涨月频 bank3 超额 +1.43pp，但单月回归 R² 仍 &lt;1%（见主报告 08），本专题聚焦条件均值，不构成交易建议。</div>
</div>

</div>
<script>
const nowType = "@@NOW_TYPE@@";
const dates24 = @@DATES24@@;
const y2_24 = @@Y2_24@@;
const y10_24 = @@Y10_24@@;
const slope24 = @@SLOPE24@@;
const subKeys = @@SUB_KEYS@@;
const subBK = @@SUB_BK@@;
const subSPY = @@SUB_SPY@@;
const subN = @@SUB_N@@;
const cases = @@CASES@@;

function mk(id){ return echarts.init(document.getElementById(id)); }
const RED="#e03131", GREEN="#0aa06e", BLUE="#1e66d6", AMBER="#b45309", PURPLE="#7048e8", GRAY="#9aa4b2";

// 图1 近24月
const c1 = mk('c1');
c1.setOption({
  tooltip:{trigger:'axis'},
  legend:{top:0,data:['2Y','10Y','10Y-2Y (bp,右)']},
  grid:{left:55,right:55,top:35,bottom:45},
  xAxis:{type:'category',data:dates24,axisLabel:{interval:2,fontSize:10}},
  yAxis:[{type:'value',name:'收益率 %',scale:true},{type:'value',name:'bp',scale:true,splitLine:{show:false}}],
  dataZoom:[{type:'slider',height:16,bottom:4}],
  series:[
    {name:'2Y',type:'line',data:y2_24,symbol:'none',lineStyle:{color:GREEN,width:1.3}},
    {name:'10Y',type:'line',data:y10_24,symbol:'none',lineStyle:{color:RED,width:1.3}},
    {name:'10Y-2Y (bp,右)',type:'line',data:slope24,symbol:'none',yAxisIndex:1,
     lineStyle:{color:BLUE,width:1.1,type:'dashed'},areaStyle:{color:'rgba(30,102,214,.08)'}}
  ]
});

// 图2 子类
const c2 = mk('c2');
c2.setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
    formatter:p=>{const i=p[0].dataIndex;return subKeys[i]+'（'+subN[i]+' 个月）<br>'+p.map(x=>x.marker+x.seriesName+': '+x.value+'%').join('<br>');}},
  legend:{top:0,data:['bank3 中位','S&P500 中位']},
  grid:{left:50,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:subKeys,axisLabel:{fontSize:10}},
  yAxis:{type:'value',name:'单月收益中位 %'},
  series:[
    {name:'bank3 中位',type:'bar',data:subBK,itemStyle:{color:PURPLE,borderRadius:[3,3,0,0]},barGap:'15%'},
    {name:'S&P500 中位',type:'bar',data:subSPY,itemStyle:{color:'#e3d5f0',borderRadius:[3,3,0,0]}}
  ]
});

// 案例日频
function caseChart(id, cid){
  const c = cases.find(x=>x.id===cid);
  const ch = mk(id);
  ch.setOption({
    title:{text:c.label,fontSize:12,left:0},
    tooltip:{trigger:'axis'},
    legend:{top:20},
    grid:{left:45,right:50,top:52,bottom:25},
    xAxis:{type:'category',data:c.dates,axisLabel:{show:false}},
    yAxis:[{type:'value',name:'收益率 %',scale:true},{type:'value',name:'收益 %',scale:true,splitLine:{show:false}}],
    series:[
      {name:'2Y',type:'line',data:c.y2,symbol:'none',lineStyle:{color:GREEN,width:1.1},yAxisIndex:0},
      {name:'10Y',type:'line',data:c.y10,symbol:'none',lineStyle:{color:RED,width:1.1},yAxisIndex:0},
      {name:'JPM',type:'line',data:c.rets.jpm,symbol:'none',lineStyle:{color:BLUE,width:1.4},yAxisIndex:1},
      {name:'BAC',type:'line',data:c.rets.bac,symbol:'none',lineStyle:{color:AMBER,width:1.4},yAxisIndex:1},
      {name:'MS',type:'line',data:c.rets.ms,symbol:'none',lineStyle:{color:PURPLE,width:1.4},yAxisIndex:1},
      {name:'KRE',type:'line',data:c.rets.kre,symbol:'none',lineStyle:{color:'#2ca02c',width:1.2},yAxisIndex:1},
      {name:'S&P500',type:'line',data:c.rets.gspc,symbol:'none',lineStyle:{color:GRAY,width:1.1,type:'dashed'},yAxisIndex:1}
    ]
  });
  return ch;
}
const charts = [c1,c2,
  caseChart('c4a','c1998'),caseChart('c4b','c2016'),caseChart('c4c','c2021'),caseChart('c4d','c2020')];
window.addEventListener('resize',()=>charts.forEach(ch=>ch.resize()));
</script>
</body>
</html>"""

# ---------- 近 24 月序列（从每日数据重建：这里用 cases 外的日频，直接从 JSON now_state 没有，需从 dgs csv） ----------
import pandas as pd
DATA = os.path.join(BASE, "..", "data")

def load_yield(name):
    df = pd.read_csv(os.path.join(DATA, f"{name}.csv"), parse_dates=["observation_date"])
    df.columns = ["date", "y"]
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    return df.dropna().reset_index(drop=True)

d2 = load_yield("dgs2"); d10 = load_yield("dgs10")
dm = pd.merge(d2[["date", "y"]], d10[["date", "y"]], on="date", suffixes=("2", "10")).dropna()
dm["slope"] = (dm["y10"] - dm["y2"]) * 100
dm = dm[dm["date"] >= "2024-09-01"]
dates24 = [str(d)[:10] for d in dm["date"]]
y2_24 = [round(v, 2) for v in dm["y2"]]
y10_24 = [round(v, 2) for v in dm["y10"]]
slope24 = [round(v, 1) for v in dm["slope"]]

# KPI
bB = stats["lead_B"]["bank3"]; stb = stats["bear_strict"]["bank3"]; stl = stats["lead_total"]["bank3"]
w12 = fwd["m12"]["bank3"]
now_typ = now_state[0]["type"]

html = (TEMPLATE
        .replace("@@NOW_TYPE@@", now_typ)
        .replace("@@B_MED@@", f"{bB['median']:+.2f}")
        .replace("@@B_WR@@", str(bB["win_rate"]))
        .replace("@@B_XS@@", f"{bB['xs_median']:+.1f}")
        .replace("@@BEAR_MED@@", f"{stb['median']:+.2f}")
        .replace("@@BEAR_XS@@", f"{stb['xs_median']:+.1f}")
        .replace("@@BEAR_WR@@", str(stb["win_rate"]))
        .replace("@@W12_MED@@", f"{w12['median']:+.1f}")
        .replace("@@W12_WR@@", str(w12["win_rate"]))
        .replace("@@W12_SPY@@", f"{fwd['m12']['gspc']['median']:+.1f}")
        .replace("@@SLOPE@@", str(now_state[-1]["slope_bp"]))
        .replace("@@EP_N@@", str(len(ep_lead)))
        .replace("@@NOW_ROWS@@", now_rows)
        .replace("@@T_ROWS@@", t_rows)
        .replace("@@B_ROWS@@", b_rows)
        .replace("@@BEAR_ROWS@@", bear_rows)
        .replace("@@C_ROWS@@", c_rows)
        .replace("@@W_ROWS@@", w_rows)
        .replace("@@F_ROWS@@", f_rows)
        .replace("@@DATES24@@", js(dates24))
        .replace("@@Y2_24@@", js(y2_24))
        .replace("@@Y10_24@@", js(y10_24))
        .replace("@@SLOPE24@@", js(slope24))
        .replace("@@SUB_KEYS@@", js(["A 严格熊陡\n2Y降10Y升", "B 2Y平\n10Y升", "C 加息陡\n长端领涨"]))
        .replace("@@SUB_BK@@", js([stats["lead_A"]["bank3"]["median"], bB["median"], stats["lead_C"]["bank3"]["median"]]))
        .replace("@@SUB_SPY@@", js([stats["lead_A"]["gspc"]["median"], stats["lead_B"]["gspc"]["median"], stats["lead_C"]["gspc"]["median"]]))
        .replace("@@SUB_N@@", js([stats["lead_A"]["bank3"]["n"], bB["n"], stats["lead_C"]["bank3"]["n"]]))
        .replace("@@CASES@@", js(cases)))

with open(os.path.join(OUT, "banks_bear_steep_report.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("报告已生成:", os.path.join(OUT, "banks_bear_steep_report.html"))
