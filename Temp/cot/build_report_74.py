# -*- coding: utf-8 -*-
"""生成 74 号报告：玉米投机净多极端脉冲——历史定位与见顶回测（2026-09-05）"""
import json, os, csv, datetime as dt, statistics as st

TMP = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(TMP))
OD = os.path.join(BASE, "reports", "74_玉米投机净多极端脉冲_20260905")
os.makedirs(OD, exist_ok=True)

# ---------- 数据 ----------
hold = json.load(open(os.path.join(TMP, "corn_1c_1995.json")))   # {n, series{date:[L,S,OI]}}
S, DATES = hold["series"], sorted(hold["series"])
ev = list(csv.DictReader(open(os.path.join(TMP, "corn_events.csv"), encoding="utf-8")))
bt = json.load(open(os.path.join(TMP, "corn_bt_results.json"), encoding="utf-8"))
px = json.load(open(os.path.join(TMP, "zc_main_hist.json"), encoding="utf-8"))
pxd = {}
for k in px:
    ts = dt.datetime.fromtimestamp(k["time_key"] / 1000)
    pxd.setdefault(ts.date().isoformat(), {"c": k["close"]})
pxd = {d: v for d, v in sorted(pxd.items())}
days = list(pxd)
CUR = "2026-09-01"
iC = DATES.index(CUR)
net_now = S[CUR][0] - S[CUR][1]

def net(i): return S[DATES[i]][0] - S[DATES[i]][1]
def cum_net(i, k): return net(i) - net(i - k)

# 全体对照 r4/r13/r26/r52
def all_wk(weeks):
    vals = []
    for i in range(0, len(days) - weeks * 5):
        vals.append((pxd[days[i + weeks * 5]]["c"] / pxd[days[i]]["c"] - 1) * 100)
    return st.median(vals), round(100 * sum(1 for x in vals if x < 0) / len(vals))

# ---------- 图1：4/8/12 周累计净增 vs 历史极值 ----------
rk = {}
for kk in (4, 8, 12):
    hist = [cum_net(j, kk) for j in range(kk, len(DATES))]
    mx = max(hist); mxd = DATES[hist.index(mx) + kk]
    c = cum_net(iC, kk)
    r = sorted(hist, reverse=True).index(c) + 1
    pct = round(100 * sum(1 for x in hist if x <= c) / len(hist), 1)
    rk[kk] = dict(cur=c, mx=mx, mxd=mxd, rank=r, pct=pct, n=len(hist))
g1 = {"k": [f"近{kk}周" for kk in (4, 8, 12)],
      "cur": [rk[k]["cur"] for k in (4, 8, 12)],
      "mx": [rk[k]["mx"] for k in (4, 8, 12)]}

# ---------- 事件汇总 ----------
evs = [x for x in bt]
imm = [x for x in evs if x["weeks"] <= 2]
late = [x for x in evs if x["weeks"] > 2]
bull = [x for x in evs if "2020-01-01" <= x["evdate"] <= "2021-12-31"]
nb = [x for x in evs if not ("2020-01-01" <= x["evdate"] <= "2021-12-31")]
evv = bt  # 窗口收益统计基于回测结果表
def med(key): return st.median([x[key] for x in evv if x[key] is not None])
def posr(key): return round(100 * sum(1 for x in evv if x[key] is not None and x[key] > 0) / len([x for x in evv if x[key] is not None]))
r4m, r13m, r26m, r52m = med("r4"), med("r13"), med("r26"), med("r52")
r4p, r13p, r26p, r52p = posr("r4"), posr("r13"), posr("r26"), posr("r52")
a4, a13, a26, a52 = all_wk(4), all_wk(13), all_wk(26), all_wk(52)
late_weeks, late_ret = st.median([x["weeks"] for x in late]), st.median([x["ret"] for x in late])

# ---------- 归一化路径 ----------
def weekly_path(d0, weeks=52):
    i = days.index(d0)
    seg = days[i:min(len(days), i + weeks * 5 + 1)]
    base = pxd[d0]["c"]
    out = []
    for j, s in enumerate(seg):
        if j % 5 == 0:
            out.append(round(pxd[s]["c"] / base * 100, 2))
    return out

paths = []
for x in bt:
    p0 = x["pxdate"]
    if p0 not in pxd: continue
    paths.append({"d": x["evdate"], "weeks": x["weeks"], "ret": x["ret"], "path": weekly_path(p0)})
L = max(len(p["path"]) for p in paths)
def med_path(grp):
    mat = [p["path"] + [p["path"][-1]] * (L - len(p["path"])) for p in grp]
    return [round(st.median(col), 2) for col in zip(*mat)]
med_all = med_path(paths)

def path_series(grp, color, alpha=0.25):
    return [{"name": p["d"], "type": "line", "data": p["path"], "showSymbol": False,
             "lineStyle": {"width": 1.1, "color": color, "opacity": alpha},
             "itemStyle": {"color": color},
             "emphasis": {"lineStyle": {"opacity": 0.95, "width": 2}}} for p in grp]

BLUE, ORANGE, SKY, GREY = "#0072B2", "#D55E00", "#56B4E9", "#666666"
YEL = "#E69F00"
path_all = path_series([p for p in paths if p["weeks"] > 2], BLUE) + \
           path_series([p for p in paths if p["weeks"] <= 2], ORANGE) + \
           [{"name": "中位", "type": "line", "data": med_all, "showSymbol": False,
             "lineStyle": {"width": 3.2, "color": "#1a1a1a"}}]
XW = list(range(0, L))

# ---------- 图2 散点 ----------
scat = [[x["evdate"], round(x["weeks"], 1), 1, round(x["ret"], 1), x["dNet"]] for x in sorted(bt, key=lambda z: z["evdate"])]
scat_dates = sorted(x["evdate"] for x in bt)

# ---------- 图4 窗口收益 ----------
bar4 = json.dumps([round(r4m, 1), round(r13m, 1), round(r26m, 1), round(r52m, 1)])
all4 = json.dumps([round(a4[0], 1), round(a13[0], 1), round(a26[0], 1), round(a52[0], 1)])

# ---------- 事件明细表 ----------
def fm(v): return f"{v:,}"
def sgn(v, suf=""):
    if v is None: return "—"
    return f"{'+' if v > 0 else ('−' if v < 0 else '±')}{abs(v):,.0f}{suf}"
def pctcls(x): return 'pos' if x > 0 else ('neg' if x < 0 else 'dim')
def typ(x):
    bullmark = ' <span style="color:#a06a00">★牛市窗</span>' if "2020-01-01" <= x["evdate"] <= "2021-12-31" else ''
    return ('<span class="tg tgA">即时顶 ≤2周</span>' if x["weeks"] <= 2 else '<span class="tg tgB">续涨型</span>') + bullmark

rows_html = []
for x in sorted(bt, key=lambda z: z["evdate"]):
    rows_html.append(f"""<tr>
<td>{x['evdate']}</td><td class="r">{sgn(float(x['net_prev']))}</td>
<td class="r b">{pctcls(float(x['dNet']))}">{'+' if x['dNet']>0 else ''}{fm(x['dNet'])}</td>
<td class="r">+{fm(x['dL'])}</td><td class="r">{'−' if x['dS']<0 else '+'}{fm(abs(x['dS']))}</td>
<td class="r">{x['p0']:.1f}</td><td>{x['peak_d']}</td>
<td class="r b">{x['weeks']:.1f}</td>
<td class="r {pctcls(x['ret'])} b">{x['ret']:+.1f}%</td>
<td class="r {pctcls(x['r4'])}">{x['r4']:+.1f}%</td>
<td class="r {pctcls(x['r13'])}">{x['r13']:+.1f}%</td>
<td class="r {pctcls(x['r26'])}">{x['r26']:+.1f}%</td>
<td class="r {pctcls(x['r52'])}">{x['r52']:+.1f}%</td>
<td>{typ(x)}</td></tr>""")

# 图1 数据（预计算）
g1_cur_data = json.dumps([{"value": v, "itemStyle": {"color": BLUE}} for v in g1["cur"]])
g1_mx_data = json.dumps([{"value": v, "itemStyle": {"color": "#c9c9c9"}} for v in g1["mx"]])

def fnum(v): return f"{v/1000:.0f}k"
def fmt_k(v):
    return f"{v:,.0f}"

# 表头行（无 pctcls 位置 bug：重构后 pctcls 应用于 td class 用表达式）
rows_html2 = []
for x in sorted(bt, key=lambda z: z["evdate"]):
    rows_html2.append(f"""<tr>
<td>{x['evdate']}</td><td class="r">{sgn(float(x['net_prev']))}</td>
<td class="r b">{'+' if x['dNet']>0 else '−'}{fm(abs(x['dNet']))}</td>
<td class="r">+{fm(x['dL'])}</td><td class="r">−{fm(abs(x['dS']))}</td>
<td class="r">{x['p0']:.1f}</td><td>{x['peak_d']}</td>
<td class="r b">{x['weeks']:.1f}</td>
<td class="r {pctcls(x['ret'])} b">{x['ret']:+.1f}%</td>
<td class="r {pctcls(x['r4'])}">{x['r4']:+.1f}%</td>
<td class="r {pctcls(x['r13'])}">{x['r13']:+.1f}%</td>
<td class="r {pctcls(x['r26'])}">{x['r26']:+.1f}%</td>
<td class="r {pctcls(x['r52'])}">{x['r52']:+.1f}%</td>
<td>{typ(x)}</td></tr>""")

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>玉米投机净多极端脉冲 · 历史定位与见顶回测（2026-09-05）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f7f7f5;color:#1a1a1a;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.7}}
.wrap{{max-width:1180px;margin:0 auto;padding:32px 22px 80px}}
h1{{font-size:26px;margin:0 0 6px;letter-spacing:-.3px}}
.sub{{color:#666;font-size:13px;margin-bottom:4px}}
h2{{font-size:19px;margin:40px 0 12px;padding-left:11px;border-left:4px solid {BLUE}}}
h3{{font-size:15px;margin:24px 0 8px}}
.meta{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;font-size:12.5px;color:#444;margin:16px 0 6px}}
.meta b{{color:#1a1a1a}}
.alert{{background:#fffdf5;border:1px solid #e8dcc0;border-left:4px solid {YEL};border-radius:6px;padding:13px 16px;font-size:13px;margin:14px 0}}
.kbox{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:16px 18px;margin:16px 0}}
.chart{{width:100%;height:430px;background:#fff;border:1px solid #e6e4df;border-radius:8px;margin:10px 0}}
.chart.tall{{height:500px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:12.3px;margin:10px 0}}
th{{background:#f2f1ec;font-weight:600;padding:7px 8px;border:1px solid #e2e0d9;text-align:center;white-space:nowrap}}
td{{padding:6px 8px;border:1px solid #eceadf;text-align:center}}
td.r{{text-align:right;font-variant-numeric:tabular-nums}}
td.b{{font-weight:700}}
.pos{{color:{BLUE}}} .neg{{color:{ORANGE}}} .dim{{color:#999}}
.tg{{font-size:11px;padding:1px 7px;border-radius:10px;white-space:nowrap}}
.tgA{{background:#fde8e0;color:#a03d00}} .tgB{{background:#e0edf8;color:#00507a}}
ul{{padding-left:20px;margin:8px 0}} li{{margin:5px 0}}
.note{{font-size:12px;color:#777}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}}
.card{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:13px 15px}}
.card .t{{font-size:12px;color:#777;margin-bottom:4px}}
.card .v{{font-size:20px;font-weight:700;letter-spacing:-.3px}}
.card .s{{font-size:11.5px;color:#888;margin-top:3px}}
.foot{{margin-top:44px;padding-top:14px;border-top:1px solid #e6e4df;font-size:12px;color:#888}}
</style></head><body><div class="wrap">

<h1>玉米投机净多极端脉冲：增仓速度史上第 2，之后会发生什么</h1>
<div class="sub">CBOT 玉米（CORN，非商业头寸 Legacy Futures-Only）· 分析日 2026-09-05 · 对应 COT 报告截至 2026-09-01</div>
<div class="meta"><b>数据与口径</b>：CFTC Legacy Futures-Only（Noncommercial 分类），官方历史压缩文件 <b>1995-03-21 起 1,642 周</b>；价格 = 富途 US.ZCmain（CBOT 玉米主力连续日线），覆盖 <b>2011-09-02 起 3,764 根</b>；事件日按 COT 周二对齐日线收盘；"顶"= 事件后 52 交易周内最高收盘。历史事件样本 n=22（2011-10 后<b>单周净头寸增 ≥7.8 万张</b>，剔除 2026 年未完结事件）。玉米 OI 约 260 万张（小麦三合约合计约 60 万），阈值不可与 73 号小麦报告直接类比。</div>

<div class="cards">
<div class="card"><div class="t">拥挤度（9/1 周）</div><div class="v">98.3 分位</div><div class="s">净多 {fm(net_now)} 张 = 31 年全样本 98.3 分位；净/OI 18.5%（94.3 分位）；<b>未破 2021-01 峰值 {fm(557581)}</b></div></div>
<div class="card"><div class="t">增仓速度（8 周累计）</div><div class="v" style="color:{BLUE}">99.5 分位</div><div class="s">净增 +{fmt_k(rk[8]['cur'])} = 1,634 周样本第 {rk[8]['rank']} 大；<b>史上仅 2019 春（贸易战+洪涝）更快</b></div></div>
<div class="card"><div class="t">事件后 13 周（22 次历史）</div><div class="v" style="color:{ORANGE}">中位 −{abs(r13m):.1f}%</div><div class="s">正收益仅 {r13p}% → 极端净增周追入，<b>3 个月后约 73% 收阴</b></div></div>
<div class="card"><div class="t">当前价格位置</div><div class="v">52 周新高</div><div class="s">9/1 创 546（52 周低 403，+35%）→ 9/4 收 536.75（−1.6%）；核心分叉点 <b>9/11 USDA 单产</b></div></div>
</div>

<h2>一、数据能力边界</h2>
<div class="kbox">CFTC Legacy futures-only 官方历史最早 <b>1995-03-21</b>（1,642 周），持仓全史可用；但玉米<b>连续期货价格</b>免费全史源在本环境不可得，富途主力连续（US.ZCmain）仅覆盖 <b>2011-09-02 起</b>。因此：<b>增仓定位用 1995-2026 全样本（1,641 个周变化），见顶回测限于 2011-09 后（22 个事件）</b>。1995-97 玉米大牛市（单周多头增仓 top 榜近半出自该段，如 1995-05-23 +16.3 万、1997-02-25 +12.5 万）与 1995-06 净多 55.2 万张（全史第 2 存量）有持仓无价格，未纳入回测。</div>

<h2>二、定位：拥挤但未破峰值，极端在"速度"</h2>
<div class="kbox"><b>存量端（98 分位但未极端）</b>：9/1 非商净多 {fm(net_now)} 张。绝对分位 98.3%（31 年峰值 2021-01-12 {fm(557581)}，1995-06 亦达 {fm(551980)}）；净/OI 18.5% = 94.3 分位，离历史峰值 24.3%（2021-12-28）还有约 6 个百分点。属于"高仓位、未到历史极限"。<br><br>
<b>速度端（这才是真极端）</b>：近 4 周净增 +{fmt_k(rk[4]['cur'])}（第 {rk[4]['rank']} 大 / {rk[4]['pct']} 分位）、近 8 周 +{fmt_k(rk[8]['cur'])}（第 {rk[8]['rank']} / {rk[8]['pct']}）、近 12 周 +{fmt_k(rk[12]['cur'])}（第 {rk[12]['rank']} / {rk[12]['pct']}）。<b>31 年中只有 2019 年 4-5 月（中美贸易战 + 春洪涝，8 周最高 +{fmt_k(rk[8]['mx'])} 张）比当前更快</b>。2026 年内已三次出现单周多头增仓进入全史 top-11：3/10 +109,509（第 6）、5/5 +76,931（第 11）、8/25 +111,211（第 5，2011 年以来最大）；8/25 当周净头寸已 +153,495（全史单周第 6），9/1 再续 +74,571，逼空式加速延续。对 9/1 增仓的拆解看：多头 +40,518 与空头 −34,053 近乎各半，<b>属于典型的高位逼空式加速</b>。</div>
<div class="chart" id="c1"></div>
<div class="note">图：当前 4/8/12 周累计净增（蓝）vs 各自 1995-2026 全样本最大值（灰）。三条速度指标全部落在 99.4-99.5 分位，历史极值均出自 2019 年 4-5 月窗口。</div>

<h2>三、核心回测：极端净增周之后，价格走什么路径？</h2>
<h3>3.1 与小麦不同的答案：玉米很少"立即见顶"，但 3-6 个月普遍转阴</h3>
<div class="cards" style="grid-template-columns:repeat(3,1fr)">
<div class="card"><div class="t">立即见顶（22 次中）</div><div class="v">仅 2/22</div><div class="s">2016-06-07（1 周）、2023-06-20（0.2 周）——与小麦 35% 的即时顶率形成对比</div></div>
<div class="card"><div class="t">续涨型（20/22）</div><div class="v">中位 {late_weeks:.1f} 周 / +{late_ret:.1f}%</div><div class="s">事件后还能涨，但多数是"先冲高再回落套人"：13 周中位仍 {r13m:+.1f}%</div></div>
<div class="card"><div class="t">3-6 个月统计</div><div class="v" style="color:{ORANGE}">73% 收阴</div><div class="s">13 周中位 {r13m:+.1f}%、26 周 {r26m:+.1f}%（对照 +0.1/+0.2%）；仅 2020-21 牛市窗两事件大幅为正</div></div>
</div>
<div class="chart tall" id="c2"></div>
<div class="note">图：22 个事件散点。x=事件日期，y=事件后见顶用时（周）；点大小=事件日→顶涨幅。橙=即时顶（≤2 周，仅 2016-06-07 与 2023-06-20），蓝=续涨型；★=2020-21 牛市窗两事件（2020-06-30、2020-12-29）。</div>
<div class="chart tall" id="c3"></div>
<div class="note">图：22 个事件的事件日=100 归一化价格路径（52 交易周）。蓝=续涨型（20 条），橙=即时顶型（2 条），粗黑=中位。多数曲线在 1-3 个月内冲高至 105-125 后回落，52 周末中位落回 100 下方——"脉冲后套人"是玉米的主导形态，与小麦"要么急顶、要么大牛"的双峰不同。</div>
<div class="chart" id="c4"></div>
<div class="note">图：事件后固定窗口收益中位数 vs 全体交易日"任意买入"对照。4 周基本中性（{r4m:+.1f}% vs 对照 {a4[0]:+.1f}%），13/26 周显著跑输（中位 {r13m:+.1f}%/{r26m:+.1f}% vs {a13[0]:+.1f}%/{a26[0]:+.1f}%）。</div>

<h3>3.2 拥挤度不是见顶信号，接力才是（玉米与小麦一致）</h3>
<div class="kbox">高拥挤（事件日净/OI&gt;12%）的 4 次事件：2016-06-07（16.3% → 1 周即顶）、2018-03-06/03-13（13.3%/16.0% → 11/10 周慢顶后阴跌）、2020-12-29（<b>22.3%，31 年最拥挤之一 → 续涨 17.8 周再 +56.8%</b>）。同样贴着 52 周高（pos52≥97%）的 6 次事件中，只有 2016-06-07 立即见顶，其余续涨 5.6-43.8 周。低拥挤（净/OI&lt;8%）的事件同样有续涨 47 周也有 0.2 周即顶（2023-06-20）。<b>net_prev / 净OI / 价格位置与见顶用时的 Spearman 相关均不显著（p&gt;0.1）——历史没有给出"涨到这个仓位就该跑"的阈值；真正的分型变量是事件后有无新利多接力（对应小麦 73 号结论）</b>。唯一系统性例外是 2020-01~2021-12 库存牛市窗：窗内两事件（2020-06-30 从净空 −23 万起步、2020-12-29 高位冲刺）r26 分别 +41.6%/+14.1%，全部大幅为正——<b>牛市环境里极端增仓是趋势确认，非牛市环境里它是脉冲顶部区</b>。</div>

<h3>3.3 事件明细（22 次，按时间排序）</h3>
<table>
<tr><th>事件日</th><th>前周净头寸</th><th>单周净增</th><th>多头增</th><th>空头减</th><th>事件日价</th><th>52周内顶日</th><th>见顶(周)</th><th>到顶涨幅</th><th>后4周</th><th>后13周</th><th>后26周</th><th>后52周</th><th>类型</th></tr>
{''.join(rows_html2)}
</table>
<div class="note">价格单位：美分/蒲式耳（CBOT 主力连续）。"空头减"列取绝对值。★牛市窗 = 2020-01-01~2021-12-31（2020-21 库存周期大牛市）。r52 已全部覆盖（事件 ≤2024-12）。</div>

<h2>四、事件簇解读（按持仓结构 + 价格形态归类）</h2>
<ul>
<li><b>净空回补型（空头踩踏推涨）· 2015-06-30/07-07</b>：一周内空头砍仓 10.5-12.4 万张（2015 年后最大回补周之一），价格仅小幅续涨（慢顶 47 周至 2016-06-14 +4~5%），<b>但事件后 4 周即 −10%</b>——回补驱动的脉冲，短期照常回吐。</li>
<li><b>情绪顶 · 2016-06-07</b>：2016 年 4-5 月阿根廷暴雨天气市的收尾段（4/19、4/26 已两次净增），第三次脉冲时净/OI 16.3%、价格 52 周高 97% —— 1 周即顶（+3.2%），随后 13 周 −21%。高位连续逼空后的最后一冲 = 教科书情绪顶。</li>
<li><b>史上最大单周 · 2019-05-21（+19.7 万）</b>：贸易战 + 春洪涝的空头踩踏，5.6-7.4 周后见顶（+9~17%），<b>随后 52 周 −18~−22%</b>，洪水溢价完全回吐。当年 4-5 月正是玉米 31 年增仓速度纪录的创造者——速度纪录段本身以深跌收场。</li>
<li><b>牛市接力（唯一正收益子样本）· 2020-06-30 / 2020-12-29</b>：前者从净空 −23 万起步（牛市启动段，r26 +41.6%），后者在净/OI 22.3% 的史上最拥挤区继续冲刺（17.8 周到 2021-05-07 顶 +56.8%，r52 +28.5%）。<b>这是当前最需要盯的"如果走牛"参照</b>。</li>
<li><b>反弹末段衰竭 · 2023-06-20</b>：熊市反弹在 596 美分处次日冲高 629 即顶（0.2 周），13 周 −20.4%——即使位置只在中位（52 周高 75%），没有基本面的接力，反弹的拥挤末端同样致命。</li>
<li><b>中段慢顶 · 2024 三事件（5/7、11/12、12/10）</b>：顶全部落在 2025-02-21（9.8-39.8 周，+8~+18%），随后回落震荡，r52 约 −1.6~+4.0%——低速温吞型。</li>
</ul>

<h2>五、对 2026-09-01 的推演（历史参照，非预测）</h2>
<div class="alert"><b>当前坐标</b>：净多 {fm(net_now)}（98.3 分位）+ 净/OI 18.5%（94.3 分位）+ 价格 52 周新高 546 + 8 周增仓速度 99.5 分位。在 22 个历史事件里，同时满足"贴 52 周高 + 净/OI&gt;15%"的只有 3 个：<b>2020-12-29</b>（→牛市接力 +56.8%）、<b>2018-03-13</b>（→10 周慢顶后阴跌）、<b>2016-06-07</b>（→1 周即顶崩）。三种剧本都曾发生，差异不在仓位本身，而在事件后的信息接力。<br><br>
<b>场景 A · 接力不足（历史先验概率更高）</b>：9/11 USDA 作物产量报告未兑现单产下修、或黑海/出口端出现利空 → 参考 2016-06-07 / 2019-07 后段 / 2023-06-20：数周内见顶（事件日 545.5 上方空间有限），随后 3-6 个月回吐 10-20%。22 事件 3-6 个月正收益仅 27% 的统计先验站在这一侧。<br>
<b>场景 B · 新利多接力（对应 2020-21 牛市窗）</b>：单产题材被 USDA 确认 + 需求端（中国采购、乙醇/出口）跟上 → 顶在数月之后，事件日到顶或还有 +10~30% 甚至更多（2020-12-29 曾 +56.8%）。<br>
<b>分型信号（事件后 4-8 周观察，对齐小麦 73 号框架）</b>：续涨型事件在 4-8 周内收复事件日高点并创新高（此处即站回并突破 ~546-550）；衰竭型在 4 周内跌破事件日平台（9/4 收 536.75 下方、即 535 一线）。两个方向的直接催化剂：<b>9/11 USDA 作物产量（与 68 号谷物研究同一节点）</b>与 <b>10 月起俄乌玉米出口季</b>（俄+乌玉米库存 6.3Mt 历史高位，黑海供给是潜在利空源）。<br><br>
<b>操作层面的历史教训</b>：事件后 4 周收益中位 {r4m:+.1f}%（正收益 {r4p}%），13/26 周中位显著为负——<b>在 9/11 报告与 4-8 周价格确认前抢跑追多，不符合历史分布；即使看多，等待"站回 546"或"USDA 落地后首日方向"再行动，胜率结构完全不同</b>。</div>

<h2>六、口径与限制</h2>
<ul>
<li>持仓口径：Legacy 期货-only 非商业头寸（CBOT 玉米单一合约，1995 年别名 'CORN - CBT CORN' 与 2013 年 CSO 组合单已排除/合并，周数连续无同日冲突）。</li>
<li>事件阈值：单周净头寸增 ≥7.8 万张（2011-09 后可得 22 个；2011 前玉米另有 1995-97 段大量同量级事件因无价格未回测）。玉米 OI 为小麦 4 倍量级，张数阈值不可跨品种比较（须用分位或 %OI）。</li>
<li>"顶"为事后定义（52 周内最高收盘），存在前视偏差，不能作为实时择时规则；2026-09-01 事件未走完，不在 22 事件样本内。</li>
<li>价格：富途 US.ZCmain 主力连续（换月拼接，可能有小幅跳空）；2011-09-02 起共 3,764 根，无周内缺口。</li>
<li>子样本小（即时顶 2、牛市窗 2），双峰/分类结论为描述性而非推断统计；weeks 与拥挤度/位置变量相关均不显著（n=22）。</li>
</ul>

<div class="foot">脚本：Temp/cot/corn_pos.py（1995 全史序列/分位）、Temp/cot/corn_bt.py（事件回测）、Temp/cot/corn_depth.py（分层统计）、Temp/cot/build_report_74.py（本报告）｜明细：Temp/cot/corn_1c_1995.json、corn_events.csv、corn_bt_results.json、zc_main_hist.json｜关联：reports/72_CFTC农产品持仓_20260901（全品种当期持仓）、reports/73_小麦投机增仓见顶回测_20260905（同框架小麦版）、reports/68（谷物供需背景）</div>
</div>
<script>
function el(id){{return document.getElementById(id)}}
if (typeof echarts !== 'undefined') {{
var c1=el('c1');
if(c1){{
var ch=echarts.init(c1);
ch.setOption({{
 title:{{text:'增仓速度：4/8/12 周累计净增 · 当前 vs 1995-2026 全样本最大（张）',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
 tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}}}},
 legend:{{top:4,right:8,textStyle:{{fontSize:11}}}},
 grid:{{left:70,right:24,top:52,bottom:30}},
 xAxis:{{type:'category',data:{json.dumps(g1['k'])},axisLabel:{{fontSize:11,color:'#333'}}}},
 yAxis:{{type:'value',axisLabel:{{fontSize:10,color:'#666',formatter:function(v){{return (v/1000).toFixed(0)+'k'}}}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
 series:[
 {{name:'当前(2026-09-01)',type:'bar',data:{g1_cur_data},barWidth:36,label:{{show:true,position:'top',fontSize:10.5,color:'#1a1a1a',formatter:function(p){{return (p.value/1000).toFixed(0)+'k'}}}}}},
 {{name:'历史最大',type:'bar',data:{g1_mx_data},barWidth:36,label:{{show:true,position:'top',fontSize:10.5,color:'#888',formatter:function(p){{return (p.value/1000).toFixed(0)+'k'}}}}}}
 ]
}});
window.addEventListener('resize',function(){{ch.resize()}});
}}
var c2=el('c2');
if(c2){{
var ch2=echarts.init(c2);
ch2.setOption({{
 title:{{text:'22 次极端净增事件：见顶用时（周）· 蓝=续涨 橙=即时顶',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
 tooltip:{{trigger:'item',formatter:function(p){{var d=p.data;return d[0]+'<br>见顶用时 <b>'+d[1]+' 周</b><br>到顶涨幅 <b>'+d[3]+'%</b><br>单周净增 +'+(d[4]/1000).toFixed(0)+'k';}}}},
 grid:{{left:52,right:26,top:52,bottom:44}},
 xAxis:{{type:'category',data:{json.dumps(scat_dates)},axisLabel:{{fontSize:9.5,color:'#666',rotate:40}},axisLine:{{lineStyle:{{color:'#ccc'}}}}}},
 yAxis:{{type:'value',name:'见顶周数',nameTextStyle:{{fontSize:10}},axisLabel:{{fontSize:10}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
 series:[{{type:'scatter',symbolSize:function(v){{return 10+Math.min(30,Math.abs(v[3])*0.35)}},data:{json.dumps(scat)},itemStyle:{{color:function(p){{return p.data[1]<=2?'{ORANGE}':'{BLUE}'}},opacity:0.88}}}}]
}});
window.addEventListener('resize',function(){{ch2.resize()}});
}}
var c3=el('c3');
if(c3){{
var ch3=echarts.init(c3);
ch3.setOption({{
 title:{{text:'22 次事件后价格路径（事件日=100，52 周）',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
 tooltip:{{trigger:'axis'}},
 legend:{{show:false}},
 grid:{{left:54,right:22,top:52,bottom:36}},
 xAxis:{{type:'category',data:{json.dumps(XW)},name:'交易周',nameTextStyle:{{fontSize:10}},axisLabel:{{fontSize:9.5,color:'#666'}},axisLine:{{lineStyle:{{color:'#ccc'}}}}}},
 yAxis:{{type:'value',axisLabel:{{fontSize:10,color:'#666'}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
 series:{json.dumps(path_all,ensure_ascii=False)}
}});
window.addEventListener('resize',function(){{ch3.resize()}});
}}
var c4=el('c4');
if(c4){{
var ch4=echarts.init(c4);
var cats=['后4周','后13周','后26周','后52周'];
ch4.setOption({{
 title:{{text:'事件后固定窗口收益中位数 vs 全体交易日对照',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
 tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}}}},
 legend:{{top:4,right:8,textStyle:{{fontSize:11}}}},
 grid:{{left:52,right:20,top:56,bottom:34}},
 xAxis:{{type:'category',data:cats}},
 yAxis:{{type:'value',axisLabel:{{fontSize:10,color:'#666',formatter:function(v){{return v+'%'}}}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
 series:[
 {{name:'极端净增事件后',type:'bar',data:{bar4},itemStyle:{{color:'{BLUE}'}},barWidth:34,label:{{show:true,position:'top',formatter:function(p){{return p.value+'%'}},fontSize:10,color:'#1a1a1a'}}}},
 {{name:'全体交易日(对照)',type:'bar',data:{all4},itemStyle:{{color:'#c9c9c9'}},barWidth:34,label:{{show:true,position:'top',formatter:function(p){{return p.value+'%'}},fontSize:10,color:'#888'}}}}
 ]
}});
window.addEventListener('resize',function(){{ch4.resize()}});
}}
}}
</script>
</body></html>"""

with open(os.path.join(OD, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print("written", os.path.join(OD, "index.html"), len(HTML))
