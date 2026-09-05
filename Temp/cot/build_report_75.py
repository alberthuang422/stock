# -*- coding: utf-8 -*-
"""生成 75 号报告：小麦极端增仓驱动归因——故事类型 × 终结方式（2026-09-05）"""
import json, os, csv, statistics as st

TMP = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(TMP))
OD = os.path.join(BASE, "reports", "75_小麦增仓驱动归因_20260905")
os.makedirs(OD, exist_ok=True)

bt = json.load(open(os.path.join(TMP, "wheat_bt_results.json"), encoding="utf-8"))
ev = {r["date"]: r for r in csv.DictReader(open(os.path.join(TMP, "wheat_events.csv"), encoding="utf-8"))}

# 逐事件驱动归因（story=上涨驱动；typ=故事类型；term=见顶终结方式）
# 2015/2016/2017/2024 催化剂经 Reuters/Bloomberg/USDA 系信源核实；2012/2018/2020-21/2022 为公开史实级行情
EVT = {
 '2012-07-17': ("美国世纪干旱（玉米主导，小麦替代跟涨）", "①供给脉冲", "②替代供给（俄丰收+8月降雨，玉米先顶）", "全球库存高位，脉冲被吸收；高位净多再暴增=情绪顶"),
 '2015-06-30': ("玉米带6月洪水，软红麦质量担忧", "①供给脉冲", "①官方数据证伪（7月WASDE上调美麦产量+3300万bu，另中国库存追溯+1200万吨）", "深度净空−6.8万一周翻多=空头回补主导，反弹到前高即耗尽；欧/加单产担忧缓解"),
 '2016-06-07': ("全球产区旱情担忧（美平原/加/澳/俄）", "①供给脉冲", "①数据证伪+宏观（USDA 5-7月产量上修+2.63亿bu/+10%；6/23脱欧美元暴涨）", "USDA连续上修+全球创纪录库存→7月破$4；非商净空−11万仅回补"),
 '2017-07-11': ("ND/MT春麦历史干旱（面积1919年来最小）", "①供给脉冲", "①数据证伪+③价格挤出需求（7/12 USDA好于恐慌预期；埃及招标弃美买俄）", "MGEX盘中$8.685创2013来新高；9月产量4.16亿bu≫恐慌预估3亿——“world awash in wheat”"),
 '2018-07-31': ("欧盟热浪减产（真实减1400万吨）", "①供给脉冲", "②替代供给（俄创纪录丰产+美丰收+库存高企）", "8/1 USDA确认减产但被俄对冲；净多4万天气炒作中段"),
 '2018-08-07': ("欧洲热浪余波", "①供给脉冲", "②替代供给（同上）", "高位净多9.2万再增=情绪顶"),
 '2019-12-17': ("全球库存去化周期+中国采购启动", "②需求/库存周期", "—无单一终结（牛市台阶）", "牛市第一阶段起点；前期深净空"),
 '2020-01-21': ("中国采购+库存收紧", "②需求/库存周期", "—无单一终结", "牛市早期"),
 '2020-03-31': ("疫情恐慌后需求恢复+采购回流", "②需求/库存周期", "—无单一终结", "低点反弹段，多头新建84%"),
 '2020-07-14': ("中国大规模采购潮+俄出口限制传闻", "②需求/库存周期", "—无单一终结", "净空区翻多，回补64%"),
 '2020-09-01': ("俄出口限制落地+黑海供给收缩", "②需求/库存周期", "—无单一终结（与2026最像：黑海）", "中国采购+俄限制双驱动"),
 '2020-10-06': ("全球库存新低预期+采购持续", "②需求/库存周期", "—无单一终结", "USDA月月下调库存，利多不断档"),
 '2020-10-20': ("俄关税+中国采购+去库多线并进", "②需求/库存周期", "—无单一终结", "净/OI 10.9%高拥挤仍续涨"),
 '2021-01-05': ("USDA库存报告利多", "②需求/库存周期", "—无单一终结", "净多9.6万仍续涨45周+33%"),
 '2021-04-27': ("美春麦播种担忧（牛市内供给叠加）", "①+②叠加", "—无单一终结（接力至2022-03顶）", "r4−10.4%仍续涨+76.5%"),
 '2021-08-03': ("北美旱（牛市后段）", "①+②叠加", "—无单一终结", "牛市冲刺段"),
 '2021-08-17': ("北美旱余波", "①+②叠加", "—无单一终结", "牛市冲刺段"),
 '2022-02-22': ("俄乌开战：约30%全球出口悬空", "①供给脉冲（地缘）", "④利多出尽计价完毕（恐慌溢价打满+实际断供<预估）", "连涨2日+52.5%至$12.94天价；r26才转负、r52−17.9%"),
 '2024-01-30': ("俄南部干旱+霜冻（SovEcon砍1300万吨）", "①供给脉冲", "①数据证伪+③需求（土耳其6/6进口禁令+美欧丰产+收获季）", "5/28 CBOT顶$7.20后6月崩25%；净空−10.5万低位起跳的中短途反弹"),
 '2024-06-25': ("法国小麦评级暴跌（60% vs 上年81%）", "①供给脉冲", "②替代供给（罗/保创纪录+全球宽松）", "反弹14周乏力，r52回负"),
}

BLUE, ORANGE, PURPLE, SKY, GREEN, YEL, GREY = "#0072B2", "#D55E00", "#CC79A7", "#56B4E9", "#009E73", "#E69F00", "#666666"
def typcolor(t):
    if t.startswith("①") and "叠加" not in t:
        return ORANGE
    if "叠加" in t:
        return PURPLE
    if t.startswith("②"):
        return BLUE
    return GREY

# ---------- 统计 ----------
recs = []
for x in bt:
    d = x["evdate"]
    story, typ, term, note = EVT[d]
    e = ev[d]
    recs.append(dict(ev=d, story=story, typ=typ, term=term, note=note,
                     weeks=x["weeks"], ret=x["ret"], p0=x["p0"], peak=x["peak_d"],
                     r4=x["r4"], r13=x["r13"], r26=x["r26"], r52=x["r52"],
                     net_prev=int(x["net_prev"]), dL=int(x["dL"]),
                     immed="即时顶" if x["weeks"] <= 2 else "续涨"))
def med(grp, k):
    v = [g[k] for g in grp if g[k] is not None]
    return st.median(v) if v else None
supply = [r for r in recs if r["typ"].startswith("①") and "叠加" not in r["typ"] and r["typ"] != "①供给脉冲（地缘）"]
cyc = [r for r in recs if r["typ"] == "②需求/库存周期"]
mix = [r for r in recs if r["typ"] == "①+②叠加"]
war = [r for r in recs if r["typ"] == "①供给脉冲（地缘）"]
print("供给脉冲(剔战争) n=%d 即时顶 %d/%d 中位周数 %.1f" % (len(supply), sum(1 for r in supply if r["immed"]=="即时顶"), len(supply), med(supply,'weeks')))
print("周期 n=%d 即时顶 %d 中位周数 %.1f 到顶中位 %+.1f%%" % (len(cyc), sum(1 for r in cyc if r["immed"]=="即时顶"), med(cyc,'weeks'), med(cyc,'ret')))
print("混合 n=%d 中位周数 %.1f 到顶中位 %+.1f%%" % (len(mix), med(mix,'weeks'), med(mix,'ret')))

# 终结方式主因
term_main = {
 '2012-07-17':"②替代供给", '2015-06-30':"①官方数据证伪", '2016-06-07':"①官方数据证伪",
 '2017-07-11':"①官方数据证伪", '2018-07-31':"②替代供给", '2018-08-07':"②替代供给",
 '2022-02-22':"④利多出尽计价", '2024-01-30':"①官方数据证伪", '2024-06-25':"②替代供给"}
term_main_stat = {}
for r in recs:
    if r["ev"] in term_main:
        term_main_stat.setdefault(term_main[r["ev"]], []).append(r)
for k in ["①官方数据证伪", "②替代供给", "③价格挤出需求", "④利多出尽计价"]:
    g = term_main_stat.get(k, [])
    print(k, "n=%d 中位wk=%s r13中位=%s r52中位=%s" % (len(g), med(g,'weeks'), med(g,'r13'), med(g,'r52')))

bull = [r for r in recs if "2019-12-01" <= r["ev"] <= "2021-12-31"]
print("牛市台阶", sorted(set(r["peak"] for r in bull)))

# ---------- 图1 数据 ----------
scat = [[r["ev"], round(r["weeks"], 1), round(r["ret"], 1), typcolor(r["typ"]), r["dL"], r["net_prev"], r["typ"]] for r in recs]
scat_dates = sorted(r["ev"] for r in recs)
scat_json = json.dumps(scat, ensure_ascii=False)

# ---------- 图2 数据 ----------
tm_rows = []
for t in ["①官方数据证伪", "②替代供给", "③价格挤出需求", "④利多出尽计价"]:
    g = term_main_stat.get(t, [])
    tm_rows.append({"t": t, "n": len(g), "wk": med(g, "weeks") if g else None,
                    "r13": med(g, "r13") if g else None, "r52": med(g, "r52") if g else None,
                    "cases": ", ".join(r["ev"] for r in g)})
tm_json = json.dumps(tm_rows, ensure_ascii=False)

# ---------- 图3 甘特 ----------
timeline = []
for i, r in enumerate(reversed(recs)):
    timeline.append({"y": i, "ev": r["ev"], "weeks": r["weeks"], "ret": r["ret"],
                     "color": typcolor(r["typ"]), "immed": r["immed"]})
tl_json = json.dumps(timeline, ensure_ascii=False)

def sgn(v, suf="", dec=1):
    if v is None: return "—"
    return f"{'+' if v > 0 else ('−' if v < 0 else '±')}{abs(v):,.{dec}f}{suf}"
def cls(v):
    return "pos" if v and v > 0 else ("neg" if v and v < 0 else "dim")
def fnum(v):
    return f"{v:,}"

rows_html = []
for r in sorted(recs, key=lambda z: z["ev"]):
    rows_html.append(f"""<tr>
<td>{r['ev']}</td>
<td class="l">{r['story']}</td>
<td><span class="tg" style="background:{typcolor(r['typ'])}22;color:{typcolor(r['typ'])}">{r['typ']}</span></td>
<td class="l">{r['term']}</td>
<td class="r b">{r['weeks']:.1f}</td>
<td class="r {cls(r['ret'])}">{r['ret']:+.1f}%</td>
<td class="r {cls(r['r4'])}">{r['r4']:+.1f}%</td>
<td class="r {cls(r['r13'])}">{r['r13']:+.1f}%</td>
<td class="r {cls(r['r52'])}">{sgn(r['r52'])}</td>
<td class="r">{fnum(r['net_prev'])}</td>
<td class="r">{fnum(r['dL'])}</td>
<td class="l note">{r['note']}</td></tr>""")

# ---------- JS 段（普通字符串，零转义；占位符 @@XX@@ 注入） ----------
DATES_J = json.dumps(scat_dates, ensure_ascii=False)
SCRIPT = """
<script>
const charts = {}
function mk(id){ charts[id] = echarts.init(document.getElementById(id)); return charts[id]; }

// 图1 散点
const c1 = mk('c1')
c1.setOption({
  tooltip: {
    trigger: 'item',
    formatter: function(p){
      const d = p.data
      return '<b>' + d[0] + '</b><br/>类型: ' + d[6] + '<br/>见顶用时: ' + d[1] + ' 周<br/>到顶涨幅: ' + d[2] + '%<br/>Δ多头: +' + d[4].toLocaleString() + '<br/>事件前净: ' + d[5].toLocaleString()
    }
  },
  legend: { data: ['① 供给脉冲（含2022战争）', '② 需求/库存周期', '①+② 叠加'], top: 4 },
  grid: { left: 46, right: 18, top: 40, bottom: 34 },
  xAxis: { type: 'category', data: @@DATES@@, axisLabel: { fontSize: 9.5, color: '#666', rotate: 38 }, axisLine: { lineStyle: { color: '#ccc' } } },
  yAxis: { type: 'value', name: '见顶用时（周）', nameTextStyle: { fontSize: 10 }, axisLabel: { fontSize: 10, color: '#666' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  series: [{
    type: 'scatter', data: @@SCAT@@,
    symbolSize: function(v){ return 9 + Math.min(26, v[2] * 0.28) },
    itemStyle: { color: function(p){ return p.data[3] }, opacity: 0.88 },
    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#999', type: 'dashed' }, label: { formatter: '即时顶阈值', fontSize: 10 }, data: [{ yAxis: 2 }] }
  }]
})

// 图2 终结方式
const c2 = mk('c2')
const tm = @@TM@@
c2.setOption({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
    formatter: function(ps){ const i = ps[0].dataIndex; const r = tm[i]; return '<b>' + r.t + '</b>（n=' + r.n + '）<br/>中位见顶: ' + (r.wk == null ? '—' : r.wk + ' 周') + '<br/>r13中位: ' + (r.r13==null?'—':r.r13+'%') + '<br/>事件: <b>' + r.cases + '</b>' } },
  grid: { left: 150, right: 60, top: 16, bottom: 30 },
  xAxis: { type: 'value', name: '中位见顶周数', nameTextStyle: { fontSize: 10 }, axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  yAxis: { type: 'category', data: tm.map(function(r){ return r.t + '（n=' + r.n + '）' }), axisLabel: { fontSize: 11.5, color: '#1a1a1a' } },
  series: [{
    type: 'bar', data: tm.map(function(r){ return r.wk == null ? null : r.wk }),
    barWidth: 22,
    itemStyle: { color: function(p){ return ['#D55E00', '#0072B2', '#56B4E9', '#CC79A7'][p.dataIndex] || '#999' } },
    label: { show: true, position: 'right', formatter: function(p){ return p.value == null ? '—' : p.value + ' 周' }, fontSize: 10.5, color: '#1a1a1a' }
  }]
})

// 图3 甘特
const c3 = mk('c3')
const tl = @@TL@@
const lab = tl.map(function(r){ return r.ev })
c3.setOption({
  tooltip: { formatter: function(p){ const r = tl[p.dataIndex]; return '<b>' + r.ev + '</b><br/>' + r.immed + '：' + r.weeks + ' 周见顶' + (r.ret>0 ? '（+' + r.ret + '%）' : '') } },
  grid: { left: 96, right: 80, top: 10, bottom: 30 },
  xAxis: { type: 'value', name: '事件日后周数', nameTextStyle: { fontSize: 10 }, min: 0, max: 56, axisLabel: { fontSize: 10, color: '#666' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
  yAxis: { type: 'category', data: lab, axisLabel: { fontSize: 9.5, color: '#555' } },
  series: tl.map(function(r, i){
    return {
      name: r.ev, type: 'line',
      data: [[0, i], [Math.min(56, r.weeks), i]],
      showSymbol: false, lineStyle: { width: 7, color: r.color, opacity: 0.85 },
      markPoint: {
        data: [{ coord: [Math.min(56, r.weeks), i], symbol: 'circle', symbolSize: 9, itemStyle: { color: '#1a1a1a' },
                  label: { position: 'right', fontSize: 9.5, color: '#333', formatter: r.ret > 0 ? ('+' + r.ret + '%') : '' } }]
      }
    }
  })
})
window.addEventListener('resize', function(){ Object.values(charts).forEach(c => c.resize()) })
</script>
</body></html>"""
SCRIPT = SCRIPT.replace("@@DATES@@", DATES_J).replace("@@SCAT@@", scat_json).replace("@@TM@@", tm_json).replace("@@TL@@", tl_json)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>小麦极端增仓驱动归因：故事类型 × 终结方式（2026-09-05）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f7f7f5;color:#1a1a1a;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.7}}
.wrap{{max-width:1220px;margin:0 auto;padding:32px 22px 80px}}
h1{{font-size:26px;margin:0 0 6px;letter-spacing:-.3px}}
.sub{{color:#666;font-size:13px;margin-bottom:4px}}
h2{{font-size:19px;margin:40px 0 12px;padding-left:11px;border-left:4px solid {BLUE}}}
h3{{font-size:15px;margin:24px 0 8px}}
.meta{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;font-size:12.5px;color:#444;margin:16px 0 6px}}
.meta b{{color:#1a1a1a}}
.alert{{background:#fffdf5;border:1px solid #e8dcc0;border-left:4px solid {YEL};border-radius:6px;padding:13px 16px;font-size:13px;margin:14px 0}}
.alert b{{color:#7a5c00}}
.kbox{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:16px 18px;margin:16px 0}}
.chart{{width:100%;height:460px;background:#fff;border:1px solid #e6e4df;border-radius:8px;margin:10px 0}}
.chart.tall{{height:560px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:12.1px;margin:10px 0}}
th{{background:#f2f1ec;font-weight:600;padding:7px 8px;border:1px solid #e2e0d9;text-align:center;white-space:nowrap}}
td{{padding:6px 7px;border:1px solid #eceadf;text-align:center}}
td.l{{text-align:left}}
td.r{{text-align:right;font-variant-numeric:tabular-nums}}
td.b{{font-weight:700}}
.pos{{color:{BLUE}}} .neg{{color:{ORANGE}}} .dim{{color:#999}}
.tg{{font-size:10.5px;padding:1px 7px;border-radius:10px;white-space:nowrap;font-weight:600}}
ul{{padding-left:20px;margin:8px 0}} li{{margin:5px 0}}
.note{{font-size:12px;color:#777}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}}
.card{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:13px 15px}}
.card .t{{font-size:12px;color:#777;margin-bottom:4px}}
.card .v{{font-size:19px;font-weight:700;letter-spacing:-.3px}}
.card .s{{font-size:11.5px;color:#888;margin-top:3px}}
.foot{{margin-top:44px;padding-top:14px;border-top:1px solid #e6e4df;font-size:12px;color:#888}}
</style></head><body><div class="wrap">

<h1>小麦极端增仓驱动归因：故事类型 × 终结方式</h1>
<div class="sub">CBOT 小麦（SRW/HRW/HRS 三合约合计，非商业头寸）· 分析日 2026-09-05 · COT 截至 2026-09-01 · 20 个历史事件（2011-07 后单周多头增仓 ≥1.5 万张）</div>
<div class="meta"><b>本报告回答的问题</b>：每一轮投机暴增是<b>被什么驱动力推上去、又被什么力量打下来的</b>？核心结论：<b>涨靠"故事"，见顶=故事被终结；故事的保质期决定行情长度</b>。归因基础：73 号回测的 20 事件数值 + 逐事件催化剂核实（2015/2016/2017/2024 经 Reuters / Bloomberg / USDA 系信源，2012/2018/2020-21/2022 为公开史实级行情）。</div>

<div class="cards">
<div class="card"><div class="t">① 供给脉冲型（8 次，剔战争）</div><div class="v" style="color:{ORANGE}">75% ≤2周即顶</div><div class="s">中位见顶 0.4 周；2012/15/16/17/18 天气市 6 次全部快速终结，仅 2024 两次 14-16 周（净空低位起跳）</div></div>
<div class="card"><div class="t">② 需求/库存周期型（8 次）</div><div class="v" style="color:{BLUE}">8/8 全部续涨</div><div class="s">中位 44 周、到顶中位 +26%；2020-21 牛市清一色</div></div>
<div class="card"><div class="t">①+② 叠加型（3 次）</div><div class="v" style="color:{PURPLE}">全续涨</div><div class="s">牛市中叠加的供给冲击被周期接力（2021-08-03 后 +78.5%）</div></div>
<div class="card"><div class="t">终结 = 四种武器</div><div class="v">数据/替代/挤出/出尽</div><div class="s">①官方数据证伪 ②替代供给 ③价格挤出需求 ④利多出尽计价——见顶时刻=边际故事断供时刻</div></div>
</div>

<h2>一、驱动分类：三类故事，保质期不同</h2>
<div class="kbox">
<b>① 供给侧脉冲</b>（2012 美旱、2015 洪水、2016 全球旱情、2017 春麦旱、2018 欧洲热浪、2022 战争、2024 俄旱+法大雨）——冲击真实，但<b>作物年度内自我终结</b>：收获季的官方产量报告就是审判日；且小麦是俄/欧/美/加/澳/乌多源供给，单产区减产总被其他产区对冲。<b>保质期：数周到 1 个作物季。</b><br><br>
<b>② 需求/政策/库存周期</b>（中国采购、俄出口税/限制、全球去库）——<b>自我强化</b>：中国采购持续 6-12 个月、USDA 月月下调库存、俄关税反复加码——利多消息不断生成。<b>保质期：18-24 个月</b>（2020-21 牛市）。<br><br>
<b>①+② 叠加</b>（2021-04/08 北美旱发生在已去库的牛市里）——供给冲击被周期"接力"，是 ① 中的异类。<br><br>
一图定位（颜色=故事类型，点大小=事件日→顶涨幅）：</div>
<div class="chart" id="c1"></div>
<div class="note">图：20 事件散点。x=事件日期，y=事件后见顶用时（周），0-2 周一带即"即时顶"。橙色=纯供给脉冲（几乎全压在 0-2 周），蓝色=需求/库存周期（全部 29-52 周），紫色=叠加型。点越大=到顶涨幅越高（2021-08 的 +78%、2022-02 的 +52.5% 最大）。虚线=即时顶阈值（2 周）。</div>

<h3>归类结论</h3>
<table>
<tr><th>故事类型</th><th>n</th><th>快速见顶 ≤2周</th><th>中位见顶用时</th><th>中位到顶涨幅</th><th>代表事件</th></tr>
<tr><td style="color:{ORANGE};font-weight:700">① 供给侧脉冲（剔战争）</td><td>8</td><td class="b">6/8（75%）</td><td class="b">0.4 周</td><td>+2.0%（多为当天/3天即顶）</td><td>2012/2015/2016/2017/2018×2</td></tr>
<tr><td style="color:{GREY}">① 供给侧脉冲（地缘·2022 战争）</td><td>1</td><td>是（1.8 周）</td><td>1.8 周</td><td>+52.5%（极端）</td><td>2022-02-22</td></tr>
<tr><td style="color:{BLUE};font-weight:700">② 需求/库存周期</td><td>8</td><td class="b neg">0/8</td><td class="b">44 周</td><td class="pos b">+26%</td><td>2019-12 ~ 2021-01 牛市</td></tr>
<tr><td style="color:{PURPLE};font-weight:700">①+② 叠加</td><td>3</td><td>0/3</td><td>30 周</td><td class="pos b">+76%</td><td>2021-04-27 / 08-03 / 08-17</td></tr>
</table>
<div class="note">① 型中唯二的例外是 2024 两次（14-16 周）：净空低位起跳的俄旱/法担忧反弹，但 r52 均回负——中短途、非真牛市。故事类型对见顶用时的预测力远大于净头寸存量（73 号深挖：weeks×net rho≈0）。</div>

<h2>二、见顶的四种终结方式</h2>
<div class="kbox">终结发生的时刻 = <b>边际故事供给断供的时刻</b>。四种方式（主因归类，9 个有明确终结的非牛市事件；③ 需求挤出在 2017-07-11 作为与①并存的次因出现，无独立持仓属性，主因归 ①，故图表 n=0）：</div>
<div class="chart" id="c2"></div>
<div class="note">图：四种终结方式的中位见顶周数（横向条形，n=事件数）。① 官方数据证伪与 ② 替代供给各处置 4 起——合起来解释了 8/9 的快速见顶；③ 需求挤出、④ 计价出尽各 1 起。</div>

<table>
<tr><th>终结方式</th><th>n</th><th>中位见顶用时</th><th>机制</th><th>代表事件</th><th>事后路径（r13/r52 中位）</th></tr>
<tr><td class="b" style="color:{ORANGE}">① 官方数据证伪</td><td>4</td><td>0.1 周</td><td>USDA 产量/库存报告证伪炒作叙事，单次报告即"审判日"</td><td>2015-06-30、2016-06-07、2017-07-11、2024-01-30</td><td>r13 −18.2% / r52 −5.8%</td></tr>
<tr><td class="b" style="color:{BLUE}">② 替代供给</td><td>4</td><td>0.7 周</td><td>其他产区（几乎总是俄罗斯）丰产对冲，减产故事"被分担"</td><td>2012-07、2018-07/08、2024-06-25</td><td>r13 −5.2% / r52 −15.0%</td></tr>
<tr><td class="b" style="color:{SKY}">③ 价格挤出需求</td><td>—</td><td>—</td><td>价格涨到美麦无竞争力，买家转向替代产地（埃及弃美买俄）——2017-07-11 与①并存、无独立事件</td><td>2017-07-11（次因）</td><td>—</td></tr>
<tr><td class="b" style="color:{PURPLE}">④ 利多出尽计价</td><td>1</td><td>1.8 周</td><td>冲击一次性计价打满，再涨只剩情绪惯性</td><td>2022-02-22（战争）</td><td>r26 转负、r52 −17.9%</td></tr>
</table>
<div class="note">r13/r52 中位统计基于各终结方式分组（①组 r13 −18.2%、②组 r13 −5.2%/r52 −15.0%、④ r52 −17.9%）：被终结的供给脉冲事后普遍再跌 13-18%（一年维度）。2017-07-11 的数据证伪与需求挤出并存，主因归 ①。</div>

<h2>三、2020-21 牛市的共享剧本：没有"哪一次见顶"，只有台阶</h2>
<div class="kbox">11 个牛市事件（2019-12 ~ 2021-08）的见顶日不是各自独立的——它们沿 <b>2020-10-23 → 2021-05-07 → 2021-11-23 → 2022-03-07（战争顶）</b> 阶梯排列，每个事件后 6-10 个月爬到下一台阶、随后 10-20% 回调再涨。真实终局统一在 <b>2022-03-07 的 $12.94 战争泡沫顶</b>。<b>四股驱动叠加且不断档</b>：中国采购（需求）+ 俄出口关税/限制（政策）+ 全球库存连续两年去化（库存）+ 2021 北美春麦旱（供给）——任何单股被证伪（如 2021-01-05 后 r13 −2.2%）都有其他驱动接力。<b>这就是"持续推动因素"的具象：不是某个利多特别强，而是利多链条不断档。</b></div>
<div class="chart tall" id="c3"></div>
<div class="note">图：20 事件的"事件日 → 52 周内顶日"时间线（横条=事件日后见顶周数，最新在上）。橙=供给脉冲（条极短，压在 0-2 周），蓝=周期型与叠加型（条长 27-52 周）；横条末端黑点旁标注=事件日→顶涨幅。可见"短条集中在下、长条集中在上"的时期聚集。</div>

<h2>四、2026-09-01 落点：这次的黑海故事属于哪一类？</h2>
<div class="alert">
当前驱动（72 号报告）：<b>黑海断供</b>——俄罗斯 8 月出口创 2010 年来最低、乌克兰出口能力损失 >97%。这属于<b>① 供给脉冲</b>，但两个关键区别决定它可能偏离历史①的"快速见顶"剧本：<br><br>
<b>· 像 2022 战争，但又不是 2022</b>：2022 是一次性恐慌（3 天计价完毕，顶 1.8 周）；2026 是<b>真实出口能力损失</b>，若黑海约束跨季持续，故事寿命以季计——更接近 2020-21 的"俄出口限制"这一②类成分（正是那轮牛市最重要的驱动之一，2020-09-01 事件即"俄出口限制+中国采购"）。<br>
<b>· 两种剧本由证伪点决定</b>：<br>
— <b>替代供给剧本</b>（类 2018/2022/2024）：澳/加/美/乌产量证明能填补（<b>9/11 USDA 是第一个裁判</b>）或黑海停火恢复出口 → 顶在 9-10 月，参照 2024-05 俄旱证伪后 3 周崩 25%。<br>
— <b>跨季约束剧本</b>（类 2020-21 俄关税）：出口约束无法在数季内解除（<b>乌仓储 11 月初近满、缺口约 1,100 万吨</b> + 俄政策惯性）→ 利多链条延伸，顶不在今年。<br><br>
<b>观察点就三个</b>：① 9/11 USDA 其他产区对冲程度；② 9 月俄出口船期是否实质恢复；③ 停火谈判进展（8/31 单日 −2.5% 的样板）。事件后 3 日 −6.2% 目前是中性信号——牛市事件 2021-04-27 也曾 r4 −10.4% 仍续涨 +76%。</div>

<h2>五、事件驱动归因总表（20 事件）</h2>
<table>
<tr><th>事件日</th><th class="l">上涨驱动（故事）</th><th>类型</th><th class="l">见顶终结方式</th><th>见顶周</th><th>到顶</th><th>后4周</th><th>后13周</th><th>后52周</th><th>事件前净</th><th>Δ多头</th><th class="l">注解</th></tr>
{''.join(rows_html)}
</table>

<h2>六、口径、来源与限制</h2>
<ul>
<li>事件样本：2011-07 后单周非商多头增仓 ≥1.5 万张的 20 个事件（价格窗口=富途 US.ZWmain 2011-07 起；1995-2010 有持仓无价格，未纳入）。</li>
<li>驱动故事与终结方式为<b>事后归因</b>：数值部分来自 73 号回测（wheat_bt_results.json，口径详见 73 号第六节）；催化剂叙述 2015/2016/2017/2024 已本轮核实（USDA WASDE/面积报告、Reuters、Bloomberg、SovEcon、USW、GFO 等），2012/2018/2020-21/2022 为公开史实级行情。</li>
<li>多因子事件按主因单标签归类（如 2017-07-11 数据证伪+需求挤出并存，主因记①）；2024-06-25 的 r52 为数据窗口截断值。</li>
<li>终结统计（第二节）仅覆盖 9 个有明确终结的非牛市事件，n 小，结论为描述性；"无单一终结"的 11 个牛市事件见第三节。</li>
<li>本节推演为<b>历史模式参照，非预测</b>；最终分叉由 9/11 USDA 与黑海动态决定。</li>
</ul>

<div class="foot">脚本：Temp/cot/build_report_75.py（本报告）、Temp/cot/wheat_depth.py（存量/位置深挖）｜数据：Temp/cot/wheat_events.csv、wheat_bt_results.json、zw_main_hist.json｜关联：73 号报告（回测方法）、74 号报告（玉米对照）、72 号报告（当期全品种持仓）</div>
</div>
""" + SCRIPT

open(os.path.join(OD, "index.html"), "w", encoding="utf-8").write(HTML)
print("written", len(HTML))