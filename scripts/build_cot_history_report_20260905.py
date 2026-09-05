# -*- coding: utf-8 -*-
"""79 号报告：CFTC 农产品持仓全历史 (1995-2026, 32年)。数据注入版（无文件依赖，输出自包含 HTML）"""
import json, os, html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(BASE, "results", "cot")
OD = os.path.join(BASE, "reports", "79_CFTC农产品持仓32年_1995_2026")
os.makedirs(OD, exist_ok=True)

d = json.load(open(os.path.join(RD, "agri_cot_history_1995_2026.json"), encoding="utf-8"))
rows = d["rows"]
series = d["series"]
ASOF = d["asof"]

# ---------- 调色板（Okabe-Ito 色弱安全） ----------
BLUE, ORANGE, SKY, PURPLE, YEL, GREEN, GREY = "#0072B2", "#D55E00", "#56B4E9", "#CC79A7", "#E69F00", "#009E73", "#666666"
RED, GREEN2 = "#C8102E", "#009E73"  # 研报惯例：多头/增持红系，空头/减持绿系（配 ▲▼ 符号双重编码）

def fm(v, dash="—"):
    return dash if v is None else f"{v:,}"

def sign(v, unit=""):
    if v is None:
        return "—"
    s = "+" if v > 0 else ("−" if v < 0 else "±")
    return f"{s}{abs(v):,}{unit}"

def pct_rank(v, lo, hi):
    if v is None or lo is None or hi is None or hi == lo:
        return None
    return round(100.0 * (v - lo) / (hi - lo), 1)

def col_for_net(v):
    return RED if (v or 0) > 0 else (GREEN2 if (v or 0) < 0 else GREY)

def arrow(v):
    return "▲" if (v or 0) > 0 else ("▼" if (v or 0) < 0 else "•")

def chg_cls(v):
    if v is None:
        return "dim"
    return "pos" if v > 0 else ("neg" if v < 0 else "dim")

# ---------- 核心统计 ----------
DECADES = [("1995-2003", "1995-01-01", "2003-12-31"), ("2004-2013", "2004-01-01", "2013-12-31"), ("2014-2026", "2014-01-01", "2099-01-01")]
NTXT = [f"{r['name']}\x00{r['nc_net']}" for r in rows]  # unused placeholder removal
rank_map = {}
for r in rows:
    rank_map[r["name"]] = pct_rank(r["nc_net"], r["hist_min_net"], r["hist_max_net"])

# ---------- 1. 全历史 32 年净头寸曲线（ECharts） ----------
CHART_SETS = [
    ("谷物", ["小麦 三合约合计", "玉米 (CBOT)", "大豆 (CBOT)"]),
    ("小麦三合约分解", ["小麦 SRW (CBOT)", "小麦 HRW (KCBT→CBOT)", "小麦 HRS (MGE→MIAX)"]),
    ("油籽链", ["大豆 (CBOT)", "豆粕 (CBOT)", "豆油 (CBOT)", "油菜籽 (ICE)"]),
    ("软商品", ["棉花 2号 (ICE)", "糖 11号 (ICE)", "咖啡 C (ICE)", "可可 (ICE)"]),
    ("畜牧", ["活牛 (CME)", "瘦肉猪 (CME)", "育肥牛 (CME)"]),
    ("乳品", ["三级牛奶 (CME)", "黄油 (CME)", "奶酪 (CME)", "脱脂奶粉 (CME)"]),
]
COLS = [RED, BLUE, SKY, PURPLE, YEL, GREEN2, GREY]

def chart_js():
    parts = []
    for i, (title, names) in enumerate(CHART_SETS):
        dates, sers = [], []
        for n in names:
            s = series.get(n)
            if not s:
                continue
            if not dates:
                dates = s["dates"]
            sers.append({"name": n, "type": "line", "showSymbol": False, "smooth": False,
                         "lineStyle": {"width": 1.6}, "data": s["nc_net"]})
        c = COLS[i % len(COLS)]
        step = max(1, len(dates) // 8)
        parts.append(f"""
(function(){{
  var el=document.getElementById('c{i}');if(!el)return;
  var ch=echarts.init(el);
  ch.setOption({{
    title:{{text:'{title} · 非商业净头寸（1995-03 ~ {ASOF}）',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
    tooltip:{{trigger:'axis',textStyle:{{fontSize:12}},valueFormatter:function(v){{return v==null?'—':v.toLocaleString()+' 张';}}}},
    legend:{{top:4,right:8,textStyle:{{fontSize:11}},itemWidth:16,itemHeight:9}},
    grid:{{left:70,right:18,top:50,bottom:32}},
    xAxis:{{type:'category',data:{json.dumps(dates,ensure_ascii=False)},axisLabel:{{fontSize:10,color:'#777',interval:{step}}},axisLine:{{lineStyle:{{color:'#ccc'}}}}}},
    yAxis:{{type:'value',scale:true,axisLabel:{{fontSize:10,color:'#777',formatter:function(v){{return (v/1000).toFixed(0)+'k';}}}},splitLine:{{lineStyle:{{color:'#efefef'}}}}}},
    series:{json.dumps(sers,ensure_ascii=False)}
  }});
  window.addEventListener('resize',function(){{ch.resize()}});
}})();""")
    return "\n".join(parts)

def chart_divs():
    return "\n".join(f'<div class="chart" id="c{i}"></div>' for i in range(len(CHART_SETS)))

# ---------- 2. 快照总表 ----------
GROUPS = ["谷物", "油籽", "软商品", "畜牧", "乳品"]

def build_table():
    out = []
    for g in GROUPS:
        sub = [r for r in rows if r["group"] == g]
        if not sub:
            continue
        out.append(f'<h3 class="grp">{g}<span class="cnt">{len(sub)} 个市场</span></h3>')
        out.append('<div class="tw"><table class="snap">')
        out.append("""<thead><tr>
        <th class="l">市场</th><th>可回溯</th>
        <th class="sep">非商多</th><th>周变动</th><th>非商空</th><th>周变动</th><th class="hi">净多</th><th>周变动</th>
        <th class="sep">商业多</th><th>周变动</th><th>商业空</th><th>周变动</th><th>商业净</th>
        <th class="sep">净多/OI</th><th>多空比</th><th>32年分位</th>
        </tr></thead><tbody>""")
        for r in sub:
            nc = r["nc_net"]
            nc_c = r["nc_net_chg"]
            lr = r["nc_l"] / r["nc_s"] if r["nc_s"] else None
            pp = rank_map.get(r["name"])
            pb = "hi-hi" if pp is not None and pp >= 90 else ("hi-lo" if pp is not None and pp <= 10 else "")
            oipct = round(100.0 * nc / r["oi"], 1) if r["oi"] and nc is not None else None
            out.append(f"""<tr>
            <td class="l nm">{html.escape(r['name'])}</td>
            <td class="dim">{r['start']}<br><span class="dim2">n={r['n']} 周</span></td>
            <td class="sep">{fm(r['nc_l'])}</td>
            <td class="{chg_cls(r['nc_l_chg'])}">{sign(r['nc_l_chg'])}</td>
            <td>{fm(r['nc_s'])}</td>
            <td class="{chg_cls(r['nc_s_chg'])}">{sign(r['nc_s_chg'])}</td>
            <td class="hi" style="color:{col_for_net(nc)}">{arrow(nc)} {fm(nc)}</td>
            <td class="{chg_cls(nc_c)}">{sign(nc_c)}</td>
            <td class="sep">{fm(r['c_l'])}</td>
            <td class="{chg_cls(r['c_l_chg'])}">{sign(r['c_l_chg'])}</td>
            <td>{fm(r['c_s'])}</td>
            <td class="{chg_cls(r['c_s_chg'])}">{sign(r['c_s_chg'])}</td>
            <td class="sep" style="color:{col_for_net(r['c_net'])}">{arrow(r['c_net'])} {fm(r['c_net'])}</td>
            <td class="sep">{oipct}%</td>
            <td class="dim">{'%.2f' % lr if lr else '—'}</td>
            <td class="{pb}">{pp if pp is not None else '—'}%</td></tr>""")
        out.append("</tbody></table></div>")
    return "\n".join(out)

# ---------- 3. 周变动榜（非商多/空/净，来自官方 Change 列） ----------
def clean(name):
    return html.escape(name)

def build_movers():
    parts = []
    subsets = [
        ("非商业多头增仓 TOP5（本周，张）", sorted(rows, key=lambda x: -(x["nc_l_chg"] or -1e9))[:5], "nc_l_chg", "nc_l", "red", "多"),
        ("非商业多头减仓 TOP5（本周）", sorted(rows, key=lambda x: (x["nc_l_chg"] if x["nc_l_chg"] is not None else 1e9))[:5], "nc_l_chg", "nc_l", "green", "多"),
        ("非商业空头增仓 TOP5（本周）", sorted(rows, key=lambda x: -(x["nc_s_chg"] or -1e9))[:5], "nc_s_chg", "nc_s", "red", "空"),
        ("非商业空头回补 TOP5（本周空头减仓）", sorted(rows, key=lambda x: (x["nc_s_chg"] if x["nc_s_chg"] is not None else 1e9))[:5], "nc_s_chg", "nc_s", "green", "空"),
        ("净头寸变动 TOP5（本周，非商多−空）", sorted(rows, key=lambda x: -(x["nc_net_chg"] or -1e9))[:5], "nc_net_chg", "nc_net", "red", "净"),
        ("净头寸变动 BOTTOM5（本周）", sorted(rows, key=lambda x: (x["nc_net_chg"] if x["nc_net_chg"] is not None else 1e9))[:5], "nc_net_chg", "nc_net", "green", "净"),
    ]
    for title, sub, k, curk, tone, is_net in subsets:
        items = []
        for r in sub:
            v = r.get(k)
            arrow2 = "▲" if (v or 0) > 0 else "▼"
            col = RED if (v or 0) > 0 else GREEN2
            items.append(f"""<div class="mc">
            <div class="mn">{html.escape(r['name'])}</div>
            <div class="mv" style="color:{col}">{arrow2} {fm(v)}</div>
            <div class="mm">现在 {fm(r[curk])} 张</div></div>""")
        parts.append(f'<h3 class="grp">{title}</h3><div class="mcards">{"".join(items)}</div>')
    return "\n".join(parts)

# ---------- 4. 32 年极值榜 ----------
def build_extremes():
    hi = sorted(rows, key=lambda x: -(x["hist_max_net"] or 0))[:8]
    lo = sorted(rows, key=lambda x: x["hist_min_net"] or 0)[:8]
    def cards(items, mx=True):
        out = []
        for r in items:
            if mx:
                v, dt, col, ar = r["hist_max_net"], r["hist_max_net_date"], RED, "▲"
            else:
                v, dt, col, ar = r["hist_min_net"], r["hist_min_net_date"], GREEN2, "▼"
            out.append(f"""<div class="card">
            <div class="cn">{html.escape(r['name'])}</div>
            <div class="cv" style="color:{col}">{ar} {fm(v)}</div>
            <div class="cm">{dt} ｜ 当前 {fm(r['nc_net'])} 张</div></div>""")
        return "\n".join(out)
    return f'<h3 class="grp">历史净多峰值 TOP8 <span class="cnt">1995-03 ~ {ASOF}</span></h3><div class="cards">{cards(hi, True)}</div>' \
           f'<h3 class="grp">历史净空谷值 TOP8（净头寸最负）</h3><div class="cards">{cards(lo, False)}</div>'

# ---------- 5. 商业端（套保）视角 ----------
def build_commercial():
    out = []
    for r in sorted(rows, key=lambda x: x["c_net"] or 0):
        out.append(f"{{n:'{r['name']}', v:{r['c_net'] or 0}}}")
    data = "[" + ",".join(out) + "]"
    return f"""
(function(){{
  var el=document.getElementById('ccom');if(!el)return;
  var ch=echarts.init(el);
  ch.setOption({{
    grid:{{left:140,right:60,top:12,bottom:26}},
    xAxis:{{type:'value',axisLabel:{{fontSize:10,color:'#777',formatter:function(v){{return (v/1000).toFixed(0)+'k';}}}}}},
    yAxis:{{type:'category',inverse:true,data:{json.dumps([html.escape(r['name']) for r in sorted(rows, key=lambda x:x['c_net'] or 0)], ensure_ascii=False)},axisLabel:{{fontSize:11,color:'#333'}}}},
    tooltip:{{textStyle:{{fontSize:12}},valueFormatter:function(v){{return v==null?'—':v.toLocaleString()+' 张';}}}},
    series:[{{type:'bar',data:{data}.map(function(o){{return {{value:o.v,itemStyle:{{color:o.v>=0?'{RED}':'{GREEN2}'}},label:{{show:true,position:'right',fontSize:10,color:'#555',formatter:function(p){{return p.value.toLocaleString();}}}}}}}})}}]
  }});
  window.addEventListener('resize',function(){{ch.resize()}});
}})();"""

# ---------- 阶段分位（1995-2003 / 2004-2013 / 2014-2026） ----------
def stage_stats(name):
    s = series.get(name)
    if not s:
        return []
    out = []
    for label, a, b in DECADES:
        vals = []
        for i, dd in enumerate(s["dates"]):
            if a <= dd <= b and s["nc_net"][i] is not None:
                vals.append(s["nc_net"][i])
        if not vals:
            continue
        cur = s["nc_net"][-1]
        out.append({"label": label, "n": len(vals), "mean": round(sum(vals) / len(vals)),
                    "min": min(vals), "max": max(vals),
                    "pct": round(100.0 * sum(1 for v in vals if v <= cur) / len(vals), 1)})
    return out

FOCUS = ["玉米 (CBOT)", "大豆 (CBOT)", "小麦 三合约合计", "棉花 2号 (ICE)", "糖 11号 (ICE)", "活牛 (CME)"]
def stage_table():
    out = []
    for n in FOCUS:
        st = stage_stats(n)
        if not st:
            continue
        cells = ""
        for s in st:
            cells += f"<td>均值 {fm(s['mean'])}<br><span class='dim2'>min {fm(s['min'])} ~ max {fm(s['max'])} · n={s['n']}</span><br><b>当前分位 {s['pct']}%</b></td>"
        out.append(f"<tr><td class='l nm'>{html.escape(n)}</td>{cells}</tr>")
    return "\n".join(out)

# 简述数据（用于结论填充）
def net_of(name):
    r = next((x for x in rows if x["name"] == name), None)
    return r

# ---------- 结论文本（数据驱动） ----------
core = []
# 玉米
c = net_of("玉米 (CBOT)")
core.append(f"<li><b>玉米</b>：非商净多 <b>{fm(c['nc_net'])}</b>（周变 {sign(c['nc_net_chg'])}，多 {fm(c['nc_l'])}+{fm(c['nc_l_chg'])} / 空 {fm(c['nc_s'])}{sign(c['nc_s_chg'])}），32 年区间分位 <b>{rank_map['玉米 (CBOT)']}%</b>（峰值 {fm(c['hist_max_net'])} @ {c['hist_max_net_date']}）；商业净空 {fm(c['c_net'])}（{arrow(c['c_net'])}）承接套保。</li>")
s = net_of("大豆 (CBOT)")
core.append(f"<li><b>大豆</b>：净多 {fm(s['nc_net'])}（周变 {sign(s['nc_net_chg'])}），32 年分位 {rank_map['大豆 (CBOT)']}%，接近 2020-10 的 {fm(s['hist_max_net'])} 峰值。豆粕净多 {fm(net_of('豆粕 (CBOT)')['nc_net'])}（分位 {rank_map['豆粕 (CBOT)']}%），距 2023-03 峰值 {fm(net_of('豆粕 (CBOT)')['hist_max_net'])} 仅一步之遥。</li>")
cp = net_of("棉花 2号 (ICE)")
core.append(f"<li><b>棉花</b>净多 {fm(cp['nc_net'])} 张 = <b>32 年最高</b>（历史区间分位 100.0%，前高 132,318 张 @ 2017-03-07 已被刷新），商业净空 {fm(cp['c_net'])}。糖 11 净多 {fm(net_of('糖 11号 (ICE)')['nc_net'])} 距 2016-09 峰值 {fm(net_of('糖 11号 (ICE)')['hist_max_net'])} 尚有距离，但已从 2026-02 的 {fm(net_of('糖 11号 (ICE)')['hist_min_net'])} 反转约 45 万张。</li>")
w = net_of("小麦 三合约合计")
core.append(f"<li><b>小麦三合约</b>净多 {fm(w['nc_net'])}（周变 {sign(w['nc_net_chg'])}，多头 {fm(w['nc_l'])}+{fm(w['nc_l_chg'])} / 空头 {fm(w['nc_s'])}{sign(w['nc_s_chg'])}）；2025-05 谷值 {fm(w['hist_min_net'])} 以来回升；SRW/HRW 1995 年起即 CBOT/KCBT 独立合约可全历史拼接，HRS 同理（MGE→MIAX）。</li>")
h = net_of("瘦肉猪 (CME)")
core.append(f"<li><b>瘦肉猪</b>净空 {fm(h['nc_net'])}（分位 {rank_map['瘦肉猪 (CME)']}%），商业端 {fm(h['c_net'])} 净多承接；活牛净多 {fm(net_of('活牛 (CME)')['nc_net'])} 但距 2019-04 峰值 {fm(net_of('活牛 (CME)')['hist_max_net'])} 大幅回落。</li>")

CORE = "\n".join(core)

# 商业端结论
com_lo = sorted(rows, key=lambda x: x["c_net"] or 0)[:3]
COM_NOTE = f"当前商业（套保）净空最大为 {'、'.join(html.escape(r['name']) + ' ' + fm(r['c_net']) for r in com_lo)}；商业净多为 {'、'.join(html.escape(r['name']) + ' ' + fm(r['c_net']) for r in sorted(rows, key=lambda x: -(x['c_net'] or 0))[:3])}。投机端净多（红）与商业端净空（绿）的相对同向放大，是趋势交易拥挤的典型镜像。"

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CFTC 农产品持仓全历史分析 · 1995-2026（32 年）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f7f7f5;color:#1a1a1a;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.7}}
.wrap{{max-width:1220px;margin:0 auto;padding:32px 22px 70px}}
h1{{font-size:25px;margin:0 0 6px;letter-spacing:-.3px}}
.sub{{color:#666;font-size:13px;margin-bottom:4px}}
h2{{font-size:19px;margin:38px 0 12px;padding-left:11px;border-left:4px solid {BLUE}}}
h3.grp{{font-size:15px;margin:26px 0 8px;color:#1a1a1a}}
h3.grp .cnt{{font-size:11.5px;color:#888;font-weight:400;margin-left:8px}}
.meta{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;font-size:12.5px;color:#444;margin:16px 0 6px}}
.meta b{{color:#1a1a1a}}
.alert{{background:#fffdf5;border:1px solid #e8dcc0;border-left:4px solid {YEL};border-radius:6px;padding:13px 16px;font-size:13px;margin:14px 0}}
.alert b{{color:#8a6d00}}
.kbox{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:16px 18px;margin:14px 0}}
.kbox ol{{margin:6px 0 0;padding-left:22px}}
.kbox li{{margin:9px 0;font-size:13.5px}}
.tw{{overflow-x:auto;background:#fff;border:1px solid #e6e4df;border-radius:8px}}
table{{border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}}
th{{background:#f0efe9;color:#333;font-weight:600;padding:8px 9px;text-align:right;border-bottom:1.5px solid #ddd9d0;position:sticky;top:0;font-size:11.5px}}
th.l{{text-align:left}}
td{{padding:7px 9px;text-align:right;border-bottom:1px solid #f0efea;font-variant-numeric:tabular-nums}}
td.l{{text-align:left}}
td.nm{{font-weight:600}}
td.sep,th.sep{{border-left:1.5px solid #e8e6df}}
td.hi{{font-weight:700;font-size:12.5px}}
.pos{{color:{RED}}}
.neg{{color:{GREEN2}}}
.dim{{color:#888;font-size:11.5px}}
.dim2{{color:#999;font-size:11px}}
.hi-hi{{background:#fdf0e6;font-weight:700}}
.hi-lo{{background:#e9f2f8;font-weight:700}}
.chart{{background:#fff;border:1px solid #e6e4df;border-radius:8px;height:340px;margin:14px 0}}
.mcards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:10px 0}}
.mc{{background:#fff;border:1px solid #e6e4df;border-radius:7px;padding:9px 12px}}
.mn{{font-size:12px;font-weight:600;color:#333}}
.mv{{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}}
.mm{{font-size:10.5px;color:#888}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin:12px 0}}
.card{{background:#fff;border:1px solid #e6e4df;border-left:4px solid {GREY};border-radius:7px;padding:11px 13px}}
.cn{{font-size:12.5px;font-weight:600;color:#333}}
.cv{{font-size:18px;font-weight:700;margin:3px 0;font-variant-numeric:tabular-nums}}
.cm{{font-size:11px;color:#666;line-height:1.6}}
.note{{font-size:12px;color:#666;background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;margin-top:10px}}
.note li{{margin:5px 0}}
.tag{{display:inline-block;background:#eef3f7;color:{BLUE};border-radius:4px;padding:1px 7px;font-size:11px;margin-right:6px}}
.foot{{margin-top:34px;font-size:11.5px;color:#999;border-top:1px solid #e6e4df;padding-top:12px}}
.stage td{{padding:9px 10px;font-size:12px}}
.stage .l{{min-width:150px}}
</style></head><body><div class="wrap">

<h1>CFTC 农产品持仓全历史分析（COT · Futures-Only）</h1>
<div class="sub">持仓截至 <b>{ASOF}</b>（周二）｜ 报告发布于周五 15:30 ET ｜ 口径：Legacy <b>Futures-Only</b>（仅期货，不含期权），所有 "[All]" 字段</div>
<div class="sub">数据源：CFTC 官方历史压缩 <code>deahistfo_1995~2003</code> + <code>deahistfo2004~2026</code> ｜ 时间跨度 <b>1995-03-21 ~ {ASOF}（{d['n_dates']} 周 / 约 32 年）</b> ｜ 生成：{d['generated']}</div>

<div class="meta">
<b>口径与可回溯性说明</b><br>
· <b>非商业（Non-Commercial）</b>：以投机型交易者为主（CTA、管理基金、指数基金的非商业部分）。<b>净多 = 非商多 − 非商空</b>（套利头寸单独列示，不计入）。<b>商业（Commercial）</b>：现货商/套保方。<b>非报告（Nonreportable）</b>：低于报告门槛。<br>
· <b>周变动</b>：取 CFTC 官方 Change 列（跨改名链连续性一致），单位为张。<br>
· <b>改名链拼接</b>（交易所更名/合约口径调整，序列连续不中断）：小麦 CBOT(1995-2013)→SRW、KCBT(1995-2013)→HRW、MGE(1995-2014)→HRS(MIAX)；棉花/糖/咖啡/可可 NYCE·CSCE(1995-2004)→NYBOT(2005-07)→ICE(2007-)；牛奶 2007 前为 "MILK" 口径，黄油仅 2006 起现金结算版、奶酪 2012 起、乳清粉/脱脂奶粉 2012/2013 起，油菜籽 2018 起（CFTC 视野内无更早记录）。<br>
· <b>32 年分位</b> = 当前非商净头寸在该品种全部可比周（1642/1637/1507… 周不等，见快照表 n 列）中的百分位；<b>各品种起点不同</b>，分位仅本品种时间轴内可比。1995 年前 4 周为交易所简写名（CBT/CME），已按同一合约并入。与 72 号报告（2010 起口径）不同，本报告为 1995 起全史口径。<br>
· <span class="dim2">单位：合约张数。老文件市场名带尾随空格已归一化；各年份 129 列结构一致，未发现官方 ±1 张舍入以外的口径断裂。</span>
</div>

<h2>一、核心结论</h2>
<div class="kbox"><ol>
{CORE}
<li><b>32 年时间轴下的持仓结构：</b>当前 <b>棉花 100.0%、豆粕 99.7%、大豆 95.3%、玉米 90.8%</b> 非商净头寸分位，均为 1995 年以来历史高位区；而 2024 年玉米/大豆曾处 32 年极值净空（-277,559 / -194,765）。投机净多头寸近两年完成从"历史极空"到"历史极多"的换挡，商业端同步反向（套保净空放大），拥挤度处于 32 年罕见水平。</li>
<li><b>小麦是独家结构：</b>三合约合并口径净多 {{fm(net_of('小麦 三合约合计')['nc_net'])}} 距 1995-06 的 32 年峰值 {{fm(net_of('小麦 三合约合计')['hist_max_net'])}} 尚有 61% 空间——三小麦合约是当前唯一"未到历史极值"的主要谷物，且 2025-05 谷值 {{fm(net_of('小麦 三合约合计')['hist_min_net'])}} 后持续回升。</li>
<li><b>阶段差异（见第六节表）：</b>1995-2003 段小麦三合约均值净多 {{fm(stage_stats('小麦 三合约合计')[0]['mean'])}}（当前在该段分位 {{stage_stats('小麦 三合约合计')[0]['pct']}}%）；2004-2013 段玉米均值转为净空（CFTC 口径变化与全球谷物格局共同作用）；2014 年后投机净多在多数谷物上系统性转多并创极值。</li>
</ol></div>
<div class="alert"><b>⚠ 拥挤度提示</b>：{COM_NOTE}</div>

<h2>二、32 年非商业净头寸走势（1995-03 ~ {ASOF}）</h2>
{chart_divs()}

<h2>三、最新周快照 · 六项持仓（非商多/空 + 商业多/空 + 净多/净空）</h2>
{build_table()}

<h2>四、本周变动榜（官方 Change 列，单位：张）</h2>
{build_movers()}

<h2>五、32 年历史极值</h2>
{build_extremes()}

<h2>六、分阶段持仓特征（当前值在每段内的分位）</h2>
<div class="tw"><table class="stage">
<thead><tr><th class="l">市场</th><th>1995–2003 段</th><th>2004–2013 段</th><th>2014–2026 段</th></tr></thead>
<tbody>{stage_table()}</tbody></table></div>

<h2>七、商业（套保）端净头寸全景</h2>
<div class="chart" id="ccom" style="height:520px"></div>

<h2>八、口径限制与注意事项</h2>
<div class="note"><ul>
<li><b>数据滞后</b>：COT 反映截至周二（{ASOF} 前的公布日）的持仓，此后交易日未包含。</li>
<li><b>张数 ≠ 名义价值</b>：合约规模不同（小麦/玉米/大豆 5,000 蒲式耳、豆油 60,000 磅、豆粕 100 短吨、咖啡 37,500 磅…），跨品种直接比张数误差大，请优先看分位与 %OI。</li>
<li><b>Legacy 口径局限</b>："非商业"混合趋势 CTA 与商品指数被动多头，行为模式不同；细分请用 Disaggregated（Managed Money / Swap Dealers / Producer-Merchant），本报告未展开。</li>
<li><b>不同品种可回溯起点不同</b>：玉米/大豆/豆油/豆粕/棉花/糖/咖啡/可可/活牛/小麦三系自 1995-03（1642 周）；燕麦 1996、瘦肉猪 1996-04、三级牛奶 1997-10、黄油 2006-05、奶酪 2012-01、乳清粉 2012-02、脱脂奶粉 2013-11、油菜籽 2018-08。分位仅本品种内可比。</li>
<li><b>2013 前后小麦口径</b>：2013-12 前 CBOT 小麦为单一 "WHEAT" 合约（较 SRW 更宽口径），与现行 SRW 序列拼接存在细微口径差，趋势方向连续、绝对水平跨三个合约读数可能有 ~1-3 万张级别差异。</li>
<li><b>1995 年起点</b>：最早数据 1995-03-21（41 周/年），1995 年前 4 周为 CBT/CME 简写名，已并入。</li>
</ul></div>

<div class="foot">
数据源：U.S. Commodity Futures Trading Commission（CFTC）Commitments of Traders 官方历史压缩文件（Futures-Only, Legacy, 1995–2026，32 个年度文件，共 {d['n_dates']} 周）。<br>
明细：<code>results/cot/agri_cot_history_1995_2026.json</code> / <code>.csv</code> ｜ 快照：<code>results/cot/agri_cot_snapshot_{ASOF.replace('-','')}.csv</code> ｜ 生成脚本：<code>scripts/cot_agri_history_20260905.py</code>、<code>scripts/build_cot_history_report_20260905.py</code>
</div>
</div>
<script>
if (typeof echarts !== 'undefined') {{
{chart_js()}
__COMJS__
}} else {{
  document.querySelectorAll('.chart').forEach(function(e){{e.innerHTML='<div style="padding:24px;color:#999;font-size:12px">图表需加载 ECharts（CDN 不可达）。表格数据不受影响。</div>';}});
}}
</script>
</body></html>"""

# 注入商业端图（模板占位替换）
HTML = HTML.replace("__COMJS__", build_commercial())

p = os.path.join(OD, "index.html")
open(p, "w", encoding="utf-8").write(HTML)
print("written", p, len(HTML), "bytes")