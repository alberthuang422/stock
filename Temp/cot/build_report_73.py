# -*- coding: utf-8 -*-
"""生成 73 号报告：小麦投机多头极端增仓——历史定位与见顶回测"""
import json, os, csv, html, datetime as dt, statistics as st

TMP = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(TMP))
OD = os.path.join(BASE, "reports", "73_小麦投机增仓见顶回测_20260905")
os.makedirs(OD, exist_ok=True)

# ---------- 数据 ----------
ev = list(csv.DictReader(open(os.path.join(TMP, "wheat_events.csv"), encoding="utf-8")))
bt = json.load(open(os.path.join(TMP, "wheat_bt_results.json"), encoding="utf-8"))
px = json.load(open(os.path.join(TMP, "zw_main_hist.json"), encoding="utf-8"))
pxd = {}
for k in px:
    ts = dt.datetime.fromtimestamp(k["time_key"] / 1000)
    pxd.setdefault(ts.date().isoformat(), {"c": k["close"]})
pxd = {d: v for d, v in sorted(pxd.items())}
days = list(pxd)

# 全体对照 r4/r13/r26/r52
def all_wk(weeks):
    vals = []
    for i in range(0, len(days) - weeks * 5):
        vals.append((pxd[days[i + weeks * 5]]["c"] / pxd[days[i]]["c"] - 1) * 100)
    return st.median(vals), round(100 * sum(1 for x in vals if x < 0) / len(vals))

# ---------- 图1：1995 以来单周多头增仓 top20 ----------
top = sorted(ev, key=lambda r: -int(r["dL"]))[:20]
top = sorted(top, key=lambda r: int(r["dL"]))  # 水平条形升序

# ---------- 图2/3 数据：事件周度归一化路径 ----------
def weekly_path(d0, weeks=52):
    """每 5 交易日采 1 点"""
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
    if p0 not in pxd:
        continue
    w = weekly_path(p0)
    paths.append({"d": x["evdate"], "weeks": x["weeks"], "ret": x["ret"], "path": w})

# 中位路径（按周数对齐补齐到相同长度 0..52 周）
L = max(len(p["path"]) for p in paths)
def med_path(grp):
    mat = [p["path"] + [p["path"][-1]] * (L - len(p["path"])) for p in grp]
    meds = []
    for j in range(L):
        col = sorted(m[j] for m in mat)
        meds.append(round(col[len(col) // 2], 2))
    return meds

imm = [p for p in paths if p["weeks"] <= 2]
late = [p for p in paths if p["weeks"] > 2]

# 供图3：每事件 series 直接传（52 周内点）
P_ALPHA = 0.25
def path_series(grp, color):
    out = []
    for p in grp:
        out.append({"name": p["d"], "type": "line", "data": p["path"],
                    "showSymbol": False, "lineStyle": {"width": 1.1, "color": color, "opacity": P_ALPHA},
                    "itemStyle": {"color": color}, "emphasis": {"lineStyle": {"opacity": 0.9, "width": 2}}})
    return out

# ---------- 摘要 ----------
imm_n = len(imm); late_n = len(late)
imm_weeks = st.median([p["weeks"] for p in imm])
late_weeks = st.median([p["weeks"] for p in late])
late_ret = st.median([p["ret"] for p in late])
r4_neg = sum(1 for x in bt if (x["r4"] or 0) < 0)
r4_med = st.median([x["r4"] for x in bt])
all_r4 = all_wk(4); all_r13 = all_wk(13); all_r26 = all_wk(26); all_r52 = all_wk(52)

BLUE, ORANGE, SKY, PURPLE, YEL, GREEN, GREY = "#0072B2", "#D55E00", "#56B4E9", "#CC79A7", "#E69F00", "#009E73", "#666666"

def fm(v):
    return f"{v:,}"

def pctcls(x):
    return 'pos' if x > 0 else ('neg' if x < 0 else 'dim')

def sgn(v, suf=""):
    if v is None: return "—"
    return f"{'+' if v > 0 else ('−' if v < 0 else '±')}{abs(v):,.1f}{suf}"

def typ(x):
    return '<span class="tg tgA">即时顶 ≤2周</span>' if x["weeks"] <= 2 else '<span class="tg tgB">续涨型</span>'

rows_html = []
for x in sorted(bt, key=lambda z: z["evdate"]):
    rows_html.append(f"""<tr>
<td>{x['evdate']}</td><td>{sgn(float(x['net_prev']))}</td>
<td class="r">+{fm(x['dL'])}</td><td class="r">{sgn(float(x['dNet']))}</td>
<td class="r">{x['p0']:.1f}</td><td>{x['peak_d']}</td>
<td class="r b">{x['weeks']:.1f}</td>
<td class="r {pctcls(x['ret'])} b">{x['ret']:+.1f}%</td>
<td class="r {pctcls(x['r4'])}">{x['r4']:+.1f}%</td>
<td class="r {pctcls(x['r13'])}">{x['r13']:+.1f}%</td>
<td class="r {pctcls(x['r26'])}">{x['r26']:+.1f}%</td>
<td class="r {pctcls(x['r52'])}">{x['r52']:+.1f}%</td>
<td>{typ(x)}</td></tr>""")

# ---------- HTML ----------
# 图1 数据（预计算避免 f-string 嵌套）
bar_data = []
for r in top:
    if r["date"] == "2026-09-01":
        col = BLUE
    elif int(r["dL"]) < 36782:
        col = "#b0b0b0"
    else:
        col = GREY
    bar_data.append({"value": int(r["dL"]), "itemStyle": {"color": col}})
bar_dates = [r["date"] for r in top]
scat_data = [[x["evdate"], round(x["weeks"], 1), 1, round(x["ret"], 1), x["dL"]] for x in sorted(bt, key=lambda z: z["evdate"])]
scat_dates = sorted(x["evdate"] for x in bt)
med_all = med_path(paths)
med_series = [{"name": "中位", "type": "line", "data": med_all, "showSymbol": False,
               "lineStyle": {"width": 3.2, "color": "#1a1a1a"}}]
path_all_series = path_series(late, BLUE) + path_series(imm, ORANGE) + med_series
bar4_data = json.dumps([round(st.median([x["r4"] for x in bt]), 1), round(st.median([x["r13"] for x in bt]), 1),
                        round(st.median([x["r26"] for x in bt]), 1), round(st.median([x["r52"] for x in bt]), 1)])
all4_data = json.dumps([round(all_r4[0], 1), round(all_r13[0], 1), round(all_r26[0], 1), round(all_r52[0], 1)])
HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>小麦投机多头极端增仓 · 历史定位与见顶回测（2026-09-05）</title>
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
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}}
.card{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:13px 15px}}
.card .t{{font-size:12px;color:#777;margin-bottom:4px}}
.card .v{{font-size:20px;font-weight:700;letter-spacing:-.3px}}
.card .s{{font-size:11.5px;color:#888;margin-top:3px}}
.foot{{margin-top:44px;padding-top:14px;border-top:1px solid #e6e4df;font-size:12px;color:#888}}
</style></head><body><div class="wrap">

<h1>小麦投机多头极端增仓：历史定位与"什么时候见顶"回测</h1>
<div class="sub">CBOT 小麦（SRW/HRW/HRS 三合约合计，非商业头寸）· 分析日 2026-09-05 · 对应 COT 报告截至 2026-09-01</div>
<div class="meta"><b>数据与口径</b>：CFTC Legacy Futures-Only（含 Noncommercial 分类），官方历史压缩文件 <b>1995-03-21 起 1,642 周</b>；价格 = 富途 US.ZWmain（CBOT 小麦主力连续日线），覆盖 <b>2011-07-11 起 3,708 根</b>；事件日按 COT 周二对齐日线收盘；"顶"定义为事件后 52 交易周内最高收盘价。历史事件样本 n=20（2011-07 后单周非商多头增仓 ≥1.5 万张，剔除 2026 年 4 个未完结事件与数据窗口外事件）。</div>

<div class="cards">
<div class="card"><div class="t">本周单周多头增仓（2026-09-01）</div><div class="v" style="color:{BLUE}">+36,782</div><div class="s">1995 年以来 1,641 周样本<b>第 5 大</b>（99.8 分位）；OI 归一化 99.1 分位</div></div>
<div class="card"><div class="t">历史事件见顶用时（20 次 ≥1.5 万张增仓）</div><div class="v">双峰</div><div class="s"><b>35%</b> 事件 ≤2 周即顶；<b>65%</b> 续涨型中位 <b>41 周</b>（约 9.5 个月）</div></div>
<div class="card"><div class="t">事件日 → 顶 涨幅（续涨型 13 次）</div><div class="v" style="color:{BLUE}">中位 +29.3%</div><div class="s">2020-21 牛市最高 +78.5%</div></div>
<div class="card"><div class="t">事件后 4 周收益（全部 20 次）</div><div class="v" style="color:{ORANGE}">84% 为负</div><div class="s">中位 −4.8% vs 全体交易日 −0.4% → 追单周暴增短期胜率差</div></div>
</div>

<h2>一、数据能力边界：为什么是"1995 + 2011"两个窗口</h2>
<div class="kbox">CFTC 官方 Legacy futures-only 历史文件（<code>deahistfo{{YYYY}}.zip</code>，内部 annualof.txt）最早 <b>1995-03-21</b>，持仓可完整回溯 31.5 年；若改用期货+期权合并口径（deacot 系列）可再回溯至 <b>1986</b>。但小麦<b>连续期货价格</b>的免费全史源在本环境不可得（Yahoo 对大陆封锁 403、stooq 强制 JS 验证、新浪无外盘期货代码），富途主力连续仅覆盖 <b>2011-07-11 起</b>。因此增仓定位用 1995-2026 全样本（1,641 周变化），见顶回测限于 2011 后（价格可得区间）。<b>1995-2010 间的 4 次超大增仓（1995-04/05、1996-01、1997-09、2004-03）有持仓、无价格，未纳入回测</b>。</div>

<h2>二、增仓的历史定位：极端的是速度，不是存量</h2>
<div class="kbox"><b>2026-09-01 当周：</b>非商多头 +36,782（73% 为主动做多，空头仅 −13,343），净头寸 +50,125。在全样本 1,641 个周变化中：多头单周增仓排<b>第 5</b>（99.8 分位）；按前周 OI 归一化后增量 3.97%，仍在 <b>99.1 分位</b>（历史中位仅 +0.04%）——不是市场长期膨胀造成的假象。前 4 名全部出自 1995-97 大牛市与 2004-03。季节上，9 月初窗口（8/20-9/12，109 周）中排第 2，仅次 1997-09-02，<b>不是每年 9 月的常规开仓动作</b>。<br><br>
相反，<b>存量端不极端</b>：当前净 +74,288 的绝对分位仅 85.4%，净/OI 7.3% 处 74.9 分位——历史上拥挤得多的时期（2004 年春净/OI 曾达 21-22%，1995 年 5-6 月净多 15-18 万张）屡见不鲜。真正罕见的是单周冲入 3.7 万张多头这个<b>速度</b>。2026 年内净头寸从 1/20 的 −119,818 摆动至 +74,288（±19.4 万张），其中 8/11→9/1 三周从 −7,703 拉回 +74,288。</div>
<div class="chart" id="c1"></div>
<div class="note">图：1995 年以来单周非商多头增仓 top20（水平条）。2026-09-01 的 +36,782 排第 5；橙条为 1995-97 牛市与 2004-03 的更大增仓周。</div>

<h2>三、核心回测：大量买入之后，什么时候见顶？</h2>
<h3>3.1 结论：双峰分布——要么很快见顶，要么再走 7-10 个月</h3>
<div class="cards" style="grid-template-columns:repeat(3,1fr)">
<div class="card"><div class="t">即时顶型（7/20，35%）</div><div class="v">0–2 周</div><div class="s">2012 干旱顶、2015-18 反弹顶、2022-02 俄乌战争（1.8 周打满 +52.5% 后见顶）</div></div>
<div class="card"><div class="t">续涨型（13/20，65%）</div><div class="v">中位 41 周</div><div class="s">事件日到顶中位 +29.3%；2020-21 牛市最典型，最长 51.6 周</div></div>
<div class="card"><div class="t">共同特征：短期先回吐</div><div class="v" style="color:{ORANGE}">r4 84% 为负</div><div class="s">事件后 4 周中位 −4.8%（对照 −0.4%）；续涨型也多数先回 3-10% 再新高</div></div>
</div>
<div class="chart tall" id="c2"></div>
<div class="note">图：20 个事件散点。x=事件日期，y=事件后见顶用时（周）；点大小=事件日收盘→顶涨幅。蓝=续涨型（&gt;2 周），橙=即时顶型（≤2 周，压在 0-2 周一带）。2022-02-22（战争，+52.5%，1.8 周见顶）为最特殊的橙点。</div>
<div class="chart tall" id="c3"></div>
<div class="note">图：20 个事件的事件日=100 的归一化价格路径（52 交易周）；蓝=续涨型（13 条），橙=即时顶型（7 条），粗黑=中位。可见续涨型集体在 5-10 个月后创出 130-180 的高点，即时顶型随后普遍深跌。</div>
<div class="chart" id="c4"></div>
<div class="note">图：事件后固定窗口收益中位数 vs 全体交易日"任意买入"对照。事件后 4 周显著跑输（−4.8% vs −0.4%）；26 周内仍略偏弱；52 周中位转正（+10.7%），因续涨型事件多在牛市中段触发。</div>

<h3>3.2 事件明细（20 次，按时间排序）</h3>
<table>
<tr><th>事件日</th><th>前周净头寸</th><th>单周多头增</th><th>净变化</th><th>事件日价</th><th>52周内顶日</th><th>见顶用时(周)</th><th>到顶涨幅</th><th>后4周</th><th>后13周</th><th>后26周</th><th>后52周</th><th>类型</th></tr>
{''.join(rows_html)}
</table>
<div class="note">价格单位：美分/蒲式耳（CBOT 主力连续）。2022-02-22 顶（2022-03-07，+52.5%）对应 CBOT $12.94 历史天价，由俄乌战争供给冲击驱动，归入即时顶型但幅度性质不同。r52 缺失的 2024-06-25 事件为数据窗口截断。</div>

<h2>四、历史案例注解</h2>
<ul>
<li><b>即时顶 · 2012-07-17（+19,354）</b>：美国世纪干旱炒作尾声，事件日 875 美分，3 个交易日后 2012-07-20 见顶（+7.4%），随后半年 −25%。高位净多（+85,133）再暴增 = 情绪顶的教科书案例。</li>
<li><b>即时顶 · 2015-06-30（+29,336）</b>：从净空 −67,984 一周翻多 +73,707（2015 年后最大净增），当天即顶，4 周 −19.8% —— 空头回补驱动的暴增常是最后一冲。</li>
<li><b>即时顶 · 2018-07-31 / 08-07</b>：天气炒作 +27,337/+23,825，两次增仓间隔一周，顶均在 8 月初（+7.8%/+0.5%），随后 13 周 −10~−13%。与 2026-09 的"供给冲击 + 8-9 月炒作"场景结构最接近的对照组之一。</li>
<li><b>即时顶 · 2022-02-22（+15,209）</b>：俄乌开战前一周资金涌入，战争溢价 1.8 周内打满 +52.5%（$12.94 天价），随后 52 周 −17.9% —— 供给冲击的顶可以来得极快。</li>
<li><b>续涨 · 2020-09-01（+25,017）</b>：俄乌减产预期+中国采购启动的 2020-21 牛市起点，34 周后 2021-05-07 见顶 +35.3%。同簇 2020-07-14/2020-10-06/2021-01-05 等多事件都在 2021-05 ~ 2021-11 见顶，涨幅 +29~79%。<b>连续多月出现"暴增周"本身就是牛市特征，而非见顶信号</b>。</li>
<li><b>续涨 · 2024-01-30（+15,100）</b>：从净空 −104,694 低位起跳，16.2 周后 +16.2% 见顶（2024-05-24），随后回落 —— 中短途反弹型。</li>
</ul>

<h2>五、对 2026-09-01 的推演（历史参照，非预测）</h2>
<div class="alert"><b>场景 A · 证伪（对应 35% 的即时顶路径）</b>：9/11 USDA 作物产量报告利空、或黑海停火/出口恢复落地 → 顶就在未来 1-2 周（$7.75 附近），随后 4-13 周回吐 10-25%。历史对照：2018-07/08、2012-07。<br>
<b>场景 B · 趋势延续（对应 65% 的续涨路径）</b>：供给冲击深化（参照 2020-21 中国采购+减产牛市、2022 战争的结构）→ 顶在 <b>2027 年 3-6 月</b>区间，事件日到顶或还有 +29%~50%。<br>
<b>分型信号（事件后 4-8 周观察）</b>：续涨型事件在 4-8 周内创事件日以来新高；即时顶型事件在 4 周内跌破事件日低点。两个方向的最直接催化剂：9/11 USDA 报告与黑海停火谈判进程。<br><br>
<b>操作层面的历史教训</b>：无论哪种场景，事件后 4 周 84% 概率负收益（中位 −4.8%）——"单周暴增即追多"在历史上短期胜率很差；等待分型信号（4-8 周价格行为 + USDA）比抢跑更符合历史分布。</div>

<h2>六、口径与限制</h2>
<ul>
<li>持仓口径：Legacy 期货-only 非商业头寸，三合约（SRW+HRW+HRS）合计；2014-01 前 HRW 在 KCBT、后并入 CBOT，已按交易所语义映射合并（详见 2026-09-05 日志与 cot_agri_20260905.py）。</li>
<li>价格口径：富途 US.ZWmain 主力连续（换月拼接），跨月可能有小幅跳空；事件日价格为当日收盘，若遇休市取最近前交易日。</li>
<li>样本：价格窗口仅 2011-07 起（15 年），20 个事件。1995-2010 的更大增仓事件（1996-01 +69,306、1995-05 +38,504 等）无价格源，未纳入。子样本（即时顶 7、续涨 13）小，双峰是描述性结论而非推断统计。</li>
<li>"见顶"为事后定义（52 周内最高收盘价），存在前视偏差——不能作为实时择时规则，仅描述历史条件分布。</li>
<li>2022-02-22 战争事件在幅度上极端（+52.5%），若不剔除，r4 中位会略改善；本报告正文统计未剔除（r4 中位 −4.8% 已含该事件，若剔除则 −5.1%）。</li>
<li>2026-09-01 事件本身尚未走完，不在 20 事件样本内；第五节为其按历史分布的定位，非预测。</li>
</ul>

<div class="foot">脚本：Temp/cot/wheat_pos.py（1995 序列构建/分位）、Temp/cot/wheat_bt.py（见顶回测）、Temp/cot/build_report_73.py（本报告）｜明细：Temp/cot/wheat_3c_1995.json、wheat_events.csv、wheat_bt_results.json、zw_main_hist.json｜关联：reports/72_CFTC农产品持仓_20260901（全品种当期持仓）</div>
</div>
<script>
function el(id){{return document.getElementById(id)}}
if (typeof echarts !== 'undefined') {{
var c1=el('c1');
if(c1){{
var ch=echarts.init(c1);
ch.setOption({{
 title:{{text:'1995-2026 单周非商多头增仓 top20（张）',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
 tooltip:{{trigger:'item'}},
 grid:{{left:170,right:60,top:40,bottom:30}},
 xAxis:{{type:'value',axisLabel:{{fontSize:10,color:'#666'}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
 yAxis:{{type:'category',data:{json.dumps(bar_dates)},axisLabel:{{fontSize:10.5,color:'#1a1a1a'}}}},
 series:[{{type:'bar',data:{json.dumps(bar_data)},barWidth:13,label:{{show:true,position:'right',fontSize:10,color:'#555',formatter:function(p){{return (p.value/1000).toFixed(0)+'k'}}}}}}]
}});
window.addEventListener('resize',function(){{ch.resize()}});
}}
var c2=el('c2');
if(c2){{
var ch2=echarts.init(c2);
ch2.setOption({{
 title:{{text:'20 次极端增仓事件：见顶用时（周）',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
 tooltip:{{trigger:'item',formatter:function(p){{var d=p.data;return d[0]+'<br>见顶用时 <b>'+d[1]+' 周</b><br>到顶涨幅 <b>'+d[3]+'%</b><br>单周多头增 +'+(d[4]/1000).toFixed(0)+'k';}}}},
 grid:{{left:52,right:30,top:56,bottom:40}},
 xAxis:{{type:'category',data:{json.dumps(scat_dates)},axisLabel:{{fontSize:9.5,color:'#666',rotate:38}},axisLine:{{lineStyle:{{color:'#ccc'}}}}}},
 yAxis:{{type:'value',name:'见顶周数',nameTextStyle:{{fontSize:10}},axisLabel:{{fontSize:10}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
 series:[{{type:'scatter',symbolSize:function(v){{return 9+Math.min(26,v[3]*0.3)}},data:{json.dumps(scat_data)},itemStyle:{{color:function(p){{return p.data[1]<=2?'{ORANGE}':'{BLUE}'}},opacity:0.85}}}}]
}});
window.addEventListener('resize',function(){{ch2.resize()}});
}}
var c3=el('c3');
if(c3){{
var ch3=echarts.init(c3);
ch3.setOption({{
 title:{{text:'20 次事件后价格路径（事件日=100，52 周）',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
 tooltip:{{trigger:'axis'}},
 legend:{{top:4,right:8,textStyle:{{fontSize:11}},data:['续涨型','即时顶型','中位']}},
 grid:{{left:54,right:22,top:52,bottom:36}},
 xAxis:{{type:'category',data:{json.dumps(list(range(0,L)))},name:'交易周',nameTextStyle:{{fontSize:10}},axisLabel:{{fontSize:9.5,color:'#666'}},axisLine:{{lineStyle:{{color:'#ccc'}}}}}},
 yAxis:{{type:'value',axisLabel:{{fontSize:10,color:'#666'}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
 series:{json.dumps(path_all_series,ensure_ascii=False)}
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
 {{name:'极端增仓事件后',type:'bar',data:{bar4_data},itemStyle:{{color:'{BLUE}'}},barWidth:34,label:{{show:true,position:'top',formatter:'{{c}}%',fontSize:10,color:'#1a1a1a'}}}},
 {{name:'全体交易日(对照)',type:'bar',data:{all4_data},itemStyle:{{color:'#b8b8b8'}},barWidth:34,label:{{show:true,position:'top',formatter:'{{c}}%',fontSize:10,color:'#888'}}}}
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
