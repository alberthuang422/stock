# -*- coding: utf-8 -*-
"""生成 72 号报告：CFTC 农产品持仓（截至 2026-09-01）"""
import json, os, csv, zipfile, io, html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(BASE, "Temp", "cot")
RD = os.path.join(BASE, "results", "cot")
OD = os.path.join(BASE, "reports", "72_CFTC农产品持仓_20260901")
os.makedirs(OD, exist_ok=True)

ASOF = "20260901"
d = json.load(open(os.path.join(RD, f"agri_cot_{ASOF}.json"), encoding="utf-8"))
rows, series = d["rows"], d["series"]

# ---- 历史分位定位数据（min/max/cur 已在 rows）
def fm(v, dash="—"):
    if v is None:
        return dash
    return f"{v:,}"

def sign(v, unit=""):
    if v is None:
        return "—"
    s = "+" if v > 0 else ("−" if v < 0 else "±")
    return f"{s}{abs(v):,}{unit}"

BLUE, ORANGE, SKY, PURPLE, YEL, GREEN, GREY = "#0072B2", "#D55E00", "#56B4E9", "#CC79A7", "#E69F00", "#009E73", "#666666"

# ================= 图1：非商业净头寸历史定位（SVG） =================
def svg_position():
    items = [r for r in rows if r["hist_min"] is not None and r["hist_max"] is not None]
    items = [r for r in items if (r["hist_max"] - r["hist_min"]) > 2000]  # 剔除流动性过低
    rowh, top, left, W = 26, 46, 210, 720
    plotw = W - left - 130
    H = top + rowh * len(items) + 30
    p = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif">']
    p.append(f'<text x="10" y="20" font-size="14" font-weight="700" fill="#1a1a1a">非商业净头寸 · 历史区间定位（截至 {d["asof"]}；各品种可回溯起点不同）</text>')
    p.append(f'<text x="10" y="36" font-size="11" fill="{GREY}">横轴 = 该品种 2010 年以来非商业净头寸的最低值 → 最高值；◆ = 当前位置；灰点 = 一年前位置</text>')
    zero_xs = []
    for i, r in enumerate(items):
        lo, hi, cur = r["hist_min"], r["hist_max"], r["nc_net"]
        y = top + i * rowh + 12
        span = hi - lo
        def x(v):
            return left + (v - lo) / span * plotw
        # 轴
        p.append(f'<line x1="{left}" y1="{y}" x2="{left+plotw}" y2="{y}" stroke="#e0e0e0" stroke-width="6" stroke-linecap="round"/>')
        # 0 线
        if lo < 0 < hi:
            p.append(f'<line x1="{x(0):.1f}" y1="{y-8}" x2="{x(0):.1f}" y2="{y+8}" stroke="#999" stroke-width="1.2" stroke-dasharray="2,2"/>')
        # 一年前
        sv = series.get(r["name"], {}).get("net") or []
        if len(sv) >= 53 and sv[-53] is not None:
            p.append(f'<circle cx="{x(sv[-53]):.1f}" cy="{y}" r="3" fill="#b0b0b0"/>')
        col = BLUE if cur >= 0 else ORANGE
        p.append(f'<path d="M{x(cur):.1f},{y-7} L{x(cur)+6:.1f},{y} L{x(cur):.1f},{y+7} L{x(cur)-6:.1f},{y} Z" fill="{col}" stroke="#fff" stroke-width="1"/>')
        p.append(f'<text x="{left-8}" y="{y+4}" font-size="11.5" text-anchor="end" fill="#1a1a1a">{html.escape(r["name"])}</text>')
        ntxt = ("▲ " if cur >= 0 else "▼ ") + f"{cur:,}"
        p.append(f'<text x="{left+plotw+10}" y="{y+4}" font-size="11" fill="{col}" font-weight="600">{ntxt}</text>')
        p.append(f'<text x="{left+plotw+10}" y="{y+15}" font-size="9.5" fill="{GREY}">分位 {r["pct_all"]}%</text>')
    p.append(f'<text x="{left}" y="{H-8}" font-size="10.5" fill="{GREY}">◆ 当前（蓝=净多 ▲ / 橙=净空 ▼）　● 一年前位置　虚线=零轴</text>')
    p.append('</svg>')
    return "\n".join(p)


# ================= 表格 =================
GROUPS = ["谷物", "油籽", "软商品", "畜牧", "乳品"]

def build_table():
    out = []
    for g in GROUPS:
        sub = [r for r in rows if r["group"] == g]
        if not sub:
            continue
        out.append(f'<h3 class="grp">{g}<span class="cnt">{len(sub)} 个市场</span></h3>')
        out.append('<div class="tw"><table>')
        out.append("""<thead><tr>
        <th class="l">市场</th>
        <th>总持仓 OI</th><th>周增</th>
        <th class="sep">非商多</th><th>非商空</th><th>套利</th><th class="hi">非商净</th><th>周变</th><th>4周变</th>
        <th class="sep">商业净</th><th>周变</th>
        <th class="sep">非报告净</th>
        <th class="sep">净/OI</th><th>全史分位</th><th>3年分位</th><th>样本周</th><th class="sep">MM净*</th>
        </tr></thead><tbody>""")
        for r in sub:
            nc = r["nc_net"] or 0
            cls = "pos" if nc > 0 else ("neg" if nc < 0 else "")
            arrow = "▲" if nc > 0 else ("▼" if nc < 0 else "•")
            pct = r["pct_all"]
            if pct is not None:
                pb = "hi-hi" if pct >= 95 else ("hi-lo" if pct <= 5 else ("hi-mid" if pct >= 80 or pct <= 20 else ""))
            else:
                pb = ""
            out.append(f"""<tr>
            <td class="l nm">{html.escape(r['name'])}</td>
            <td>{fm(r['oi'])}</td><td class="dim">{sign(r['oi_chg'])}</td>
            <td class="sep">{fm(r['nc_l'])}</td><td>{fm(r['nc_s'])}</td><td class="dim">{fm(r['nc_sp'])}</td>
            <td class="hi {cls}">{arrow} {fm(nc)}</td>
            <td class="{'pos' if (r['nc_net_chg'] or 0)>0 else ('neg' if (r['nc_net_chg'] or 0)<0 else 'dim')}">{sign(r['nc_net_chg'])}</td>
            <td class="{'pos' if (r['nc_net_chg4'] or 0)>0 else ('neg' if (r['nc_net_chg4'] or 0)<0 else 'dim')}">{sign(r['nc_net_chg4'])}</td>
            <td class="sep {cls if False else ('pos' if (r['c_net'] or 0)>0 else 'neg')}">{fm(r['c_net'])}</td>
            <td class="dim">{sign(r['c_net_chg'])}</td>
            <td class="sep {'pos' if (r['nr_net'] or 0)>0 else 'neg'}">{fm(r['nr_net'])}</td>
            <td class="sep">{r['nc_net_pct']}%</td><td class="{pb}">{pct}%</td><td class="{pb}">{r['pct_3y']}%</td><td class="dim">{r['nall']}</td>
            <td class="sep dim">{fm(r['mm_net'])}</td></tr>""")
        out.append("</tbody></table></div>")
    return "\n".join(out)


# ================= ECharts 序列图 =================
CHART_SETS = [
    ("谷物", ["玉米 (CBOT)", "小麦 三合约合计", "大豆 (CBOT)"]),
    ("油籽复合", ["大豆 (CBOT)", "豆粕 (CBOT)", "豆油 (CBOT)", "油菜籽 (ICE)"]),
    ("软商品", ["棉花 2号 (ICE)", "糖 11号 (ICE)", "咖啡 C (ICE)", "可可 (ICE)"]),
    ("畜牧与乳品", ["活牛 (CME)", "瘦肉猪 (CME)", "育肥牛 (CME)", "三级牛奶 (CME)", "黄油 (CME)"]),
]

def chart_js():
    parts = []
    for i, (title, names) in enumerate(CHART_SETS):
        dates = []
        sers = []
        for n in names:
            s = series.get(n) or {}
            if not s.get("dates"):
                continue
            if not dates:
                dates = s["dates"]
            sers.append({"name": n, "type": "line", "showSymbol": False, "smooth": False,
                         "lineStyle": {"width": 1.8},
                         "data": [x if x is not None else None for x in s["net"][-156:]]})
        dates = dates[-156:]
        cols = [BLUE, ORANGE, SKY, PURPLE, YEL, GREEN]
        for j, s in enumerate(sers):
            s["itemStyle"] = {"color": cols[j % len(cols)]}
            s["lineStyle"]["color"] = cols[j % len(cols)]
        parts.append(f"""
  (function(){{
    var el=document.getElementById('c{i}');if(!el)return;
    var ch=echarts.init(el);
    ch.setOption({{
      title:{{text:'{title} · 非商业净头寸（近 3 年）',textStyle:{{fontSize:13,color:'#1a1a1a'}},left:8,top:4}},
      tooltip:{{trigger:'axis',textStyle:{{fontSize:12}}}},
      legend:{{top:4,right:8,textStyle:{{fontSize:11}},itemWidth:16,itemHeight:9}},
      grid:{{left:62,right:18,top:52,bottom:34}},
      xAxis:{{type:'category',data:{json.dumps(dates,ensure_ascii=False)},axisLabel:{{fontSize:10,color:'#666',interval:Math.floor({len(dates)}/6)}},axisLine:{{lineStyle:{{color:'#ccc'}}}}}},
      yAxis:{{type:'value',axisLabel:{{fontSize:10,color:'#666',formatter:function(v){{return (v/1000).toFixed(0)+'k';}}}},splitLine:{{lineStyle:{{color:'#f0f0f0'}}}}}},
      series:{json.dumps(sers,ensure_ascii=False)}
    }});
    window.addEventListener('resize',function(){{ch.resize()}});
  }})();""")
    return "\n".join(parts)

def chart_divs():
    return "\n".join(f'<div class="chart" id="c{i}"></div>' for i in range(len(CHART_SETS)))


# ================= 关键结论数据 =================
def key_rows():
    """极值榜：分位 ≥95（拥挤多头）与 ≤5（极端净空）"""
    hi = sorted([r for r in rows if r["pct_all"] is not None and r["pct_all"] >= 90],
                key=lambda x: -x["pct_all"])
    lo = sorted([r for r in rows if r["pct_all"] is not None and r["pct_all"] <= 10],
                key=lambda x: x["pct_all"])
    return hi, lo

hi, lo = key_rows()

def card_list(items, kind):
    out = []
    for r in items:
        col = BLUE if kind == "hi" else ORANGE
        arrow = "▲" if kind == "hi" else "▼"
        out.append(f"""<div class="card">
        <div class="cn">{html.escape(r['name'])}</div>
        <div class="cv" style="color:{col}">{arrow} {fm(r['nc_net'])}</div>
        <div class="cm">全史分位 <b>{r['pct_all']}%</b> ｜ 3年分位 {r['pct_3y']}%<br>
        周变 {sign(r['nc_net_chg'])} ｜ 4周变 {sign(r['nc_net_chg4'])}<br>
        <span class="dim2">区间 {fm(r['hist_min'])} ~ {fm(r['hist_max'])}</span></div></div>""")
    return "\n".join(out)


HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CFTC 农产品持仓报告 · 截至 2026-09-01</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f7f7f5;color:#1a1a1a;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.7}}
.wrap{{max-width:1180px;margin:0 auto;padding:32px 22px 70px}}
h1{{font-size:26px;margin:0 0 6px;letter-spacing:-.3px}}
.sub{{color:#666;font-size:13px;margin-bottom:4px}}
h2{{font-size:19px;margin:38px 0 12px;padding-left:11px;border-left:4px solid {BLUE}}}
h3.grp{{font-size:15px;margin:26px 0 8px;color:#1a1a1a}}
h3.grp .cnt{{font-size:11.5px;color:#888;font-weight:400;margin-left:8px}}
.meta{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;font-size:12.5px;color:#444;margin:16px 0 6px}}
.meta b{{color:#1a1a1a}}
.alert{{background:#fffdf5;border:1px solid #e8dcc0;border-left:4px solid {YEL};border-radius:6px;padding:13px 16px;font-size:13px;margin:14px 0}}
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
.pos{{color:{BLUE}}}
.neg{{color:{ORANGE}}}
.dim{{color:#888;font-size:11.5px}}
.dim2{{color:#999;font-size:11px}}
.hi-hi{{background:#fdf0e6;font-weight:700}}
.hi-lo{{background:#e9f2f8;font-weight:700}}
.hi-mid{{background:#faf8f2}}
.chart{{background:#fff;border:1px solid #e6e4df;border-radius:8px;height:330px;margin:14px 0}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:12px;margin:14px 0}}
.card{{background:#fff;border:1px solid #e6e4df;border-left:4px solid {GREY};border-radius:7px;padding:11px 13px}}
.cn{{font-size:12.5px;font-weight:600;color:#333}}
.cv{{font-size:19px;font-weight:700;margin:3px 0;font-variant-numeric:tabular-nums}}
.cm{{font-size:11px;color:#666;line-height:1.6}}
.note{{font-size:12px;color:#666;background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;margin-top:10px}}
.note li{{margin:5px 0}}
.tag{{display:inline-block;background:#eef3f7;color:{BLUE};border-radius:4px;padding:1px 7px;font-size:11px;margin-right:6px}}
.tag.o{{background:#fdf0e8;color:{ORANGE}}}
.foot{{margin-top:34px;font-size:11.5px;color:#999;border-top:1px solid #e6e4df;padding-top:12px}}
</style></head><body><div class="wrap">

<h1>CFTC 农产品持仓报告（COT）</h1>
<div class="sub">持仓截至 <b>2026-09-01（周二）</b> ｜ 报告发布 2026-09-04（周五 15:30 ET）｜ 口径：Legacy <b>Futures-Only</b>（仅期货，不含期权）</div>
<div class="sub">数据源：CFTC 官方历史数据 <code>deahistfoYYYY.zip</code>（2010–2026）+ 分类持仓 <code>fut_disagg_txt_2026</code> ｜ 生成：{d['generated']}</div>

<div class="meta">
<b>报告口径说明</b><br>
· <b>非商业（Non-Commercial）</b>：以投机型交易者为主（CTA、管理基金、指数基金的非商业部分），本报告重点。<b>净头寸 = 非商多 − 非商空</b>（套利头寸单独列示，不计入净头寸）。<br>
· <b>商业（Commercial）</b>：现货商/套保方，通常与非商业方向相反。<b>非报告（Nonreportable）</b>：低于报告门槛的小户。<br>
· <b>全史分位</b>：当前非商业净头寸在该品种<b>自 2010-01 以来的全部可比周</b>（见表格「样本周」列，272–870 周不等）中的百分位；<b>3 年分位</b>为近 156 周。各品种可回溯起点不同（小麦 SRW/HRW 自 2013-12 起独立统计、HRS 自 2014-03、油菜籽自 2018-08、部分乳品自 2010–2013），故分位数仅在本品种时间轴内可比。<br>
· <span class="dim2">* MM 净 = 分类持仓口径下 Managed Money 净头寸（仅作方向交叉验证，与非商业口径不完全可比）</span><br>
· <span class="dim2">单位：合约张数。数据校验：383 个市场中 34 个存在 ±1 张的官方四舍五入残差（含小麦 SRW/HRW、豆粕、活牛等），不影响结论。</span>
</div>

<h2>一、核心结论</h2>
<div class="kbox"><ol>
<li><b>谷物与油籽的多头拥挤度已达 2010 年以来极值区。</b>棉花非商业净多 <b>133,147</b> 张，全史分位 <b>100.0%</b>——<b>刷新 2017-03-07 的 132,318 张，为 2010 年以来最高</b>；豆粕 173,892 张（分位 99.9%，距 2023-03-07 历史峰值 174,900 仅差 1,008 张）；玉米 480,732 张（98.0%，历史峰值 2021-01-12 的 557,581）；大豆 249,131 张（97.9%）；豆油 125,526（96.1%）；油菜籽 84,719（96.9%）。</li>
<li><b>小麦多头确实在暴增，且是有可比数据以来单周最大增仓。</b>三合约合计本周非商业<b>多头增仓 +36,782</b>、<b>空头减仓 −13,343</b>，净头寸 +50,125——即 73% 来自主动做多而非空头回补。分合约方向一致：SRW 多 +23,136 / 空 −9,689；HRW 多 +8,829 / 空 −1,073；HRS 多 +4,817 / 空 −2,581。多头总量 219,087 → 255,869（<b>+16.8%</b>）。<b>+36,782 张的单周增仓在 649 周可比样本中排名第一</b>（分位 100.0%，超过 2015-06-30 的 +29,336）；净头寸周增幅 +50,125 排第 7（分位 98.6%，历史最大为 2015-06-30 的 +73,707）。<br><span class="dim2">路径：6/30 −80,988 → 7/21 首次翻多 +3,196 → 8 月零轴震荡（−7,703 ~ +24,163）→ 9/1 +74,288，为 2026 年内最高、近 3 年最高（3 年分位 100%），全史分位 89.2%（2010 年以来峰值 135,776）。年内低点 1/20 的 −119,818。</span></li>
<li><b>玉米是增仓最快的品种。</b>净多 480,732 张（+74,571/周），<b>3 周内从 19.6 万增至 48.1 万</b>（8/11 182,951 → 8/18 252,666 → 8/25 406,161 → 9/1 480,732），OI 单周增 +183,678 至 2,594,329——典型增仓上行，投机资金是新作合约的主要边际买盘；商业端净空 −428,629 同步承接。</li>
<li><b>食糖是本年度最大的持仓反转。</b>2026-02-17 净空 <b>−237,843</b>（历史级净空）→ 本周净多 <b>+211,195</b>，7 个月内翻转约 <b>45 万张</b>，3 年分位 97.5%；本周仍在增持 +30,252。</li>
<li><b>畜牧端处于历史级净空。</b>瘦肉猪净空 −35,121 张，全史分位 <b>0.2%</b>（上周 −40,458 为 2010 年以来最空，本周小幅回补 +5,337）；黄油 −5,503（1.3%，2022-03 历史峰值 −5,949）；脱脂奶粉 −4,086（1.8%）。活牛净多 41,915 但 3 年分位仅 <b>4.5%</b>（全史 17.0%），本周大幅减持 −11,870。</li>
<li><b>可可、咖啡是软商品中的逆势品种。</b>可可净空 −11,273（分位 13.6%，3 年 21.0%），但本周空头大幅回补 <b>+7,113</b>；咖啡净多 23,823，本周减持 −6,923，3 年分位降至 18.5%——多头正在离场。</li>
<li><b>持仓结构含义：</b>谷物/油籽/棉花/糖的多头已极度拥挤，而商业端对应大规模净空（玉米商业净 −428,629、棉花 −144,997、豆粕 −202,241、糖 −271,250），即现货商在高位大量套保。历史上此类"投机极端净多 + 商业极端净空"的组合对利多消息的边际敏感度下降，对利空（9/11 USDA 产量报告）的脆弱性上升。</li>
</ol></div>

<div class="alert"><b>⚠ 与既有研究的一致性</b>：本轮持仓数据与 68 号报告（2026-08-24~28 谷物暴涨：小麦 +12.1%、玉米 +5.5%、大豆 +3.9%）方向一致——价格与投机净多头同步冲高，且本周（9/1）仍在加仓。这意味着 9/11 USDA 作物产量报告是直接的证伪节点：若单产预期差收敛，拥挤多头的平仓压力将被放大。</div>

<h2>二、非商业净头寸 · 历史区间定位</h2>
<div class="tw" style="padding:12px 14px">{svg_position()}</div>

<h2>三、主要品种非商业净头寸走势（近 3 年）</h2>
{chart_divs()}

<h2>四、全品种头寸明细（Futures-Only）</h2>
{build_table()}

<h2>五、极端持仓榜</h2>
<h3 class="grp">分位 ≥ 90% <span class="cnt">投机多头拥挤</span></h3>
<div class="cards">{card_list(hi, 'hi')}</div>
<h3 class="grp">分位 ≤ 10% <span class="cnt">投机极度净空 / 多头清空</span></h3>
<div class="cards">{card_list(lo, 'lo')}</div>

<h2>六、分板块解读</h2>
<div class="note"><ul>
<li><span class="tag">谷物</span><b>玉米</b>：非商净多 480,732（+74,571/周，3 周 +29.8 万），OI 单周暴增 +183,678 至 2,594,329——增仓上行，投机资金是新作合约的主要买盘；商业净空 −428,629 同步扩大，套保盘承接。历史上玉米净多头超过 45 万张后（2021-01 峰值 557,581）价格多在随后 1–3 个月内回落。<b>小麦</b>：SRW 净多 21,085（+32,825）、HRW 31,445（+9,902）、HRS 21,758（+7,398）；三合约合计本周<b>多头 +36,782、空头 −13,343</b>，即净增 +50,125 中<b>七成来自主动做多</b>，多头总量 +16.8% 至 255,869。该增仓幅度为 649 周可比样本中单周最大。三合约 7 月下旬由空翻多、本周加速至 +74,288，创 2026 年新高。燕麦、糙米流动性极低（OI 3,163 / 13,539），参考意义有限。</li>
<li><span class="tag">油籽</span><b>大豆</b>：净多 249,131（+42,909），4 周 +102,996；<b>豆粕</b>净多 173,892（+61,783，本周增持幅度最大，逼近 2023-03 历史峰值）；<b>豆油</b> 125,526（+21,855）；<b>油菜籽</b> 84,719（+13,263，分位 96.9%）。整个油籽链条同步处于极值区，联动性强于单品种，一旦转向易形成共振。</li>
<li><span class="tag">软商品</span><b>棉花</b>净多 133,147 = 2010 年以来最高（+5,964/周，4 周 +30,655），商业净空 −144,997；<b>糖</b>净多 211,195（+30,252），7 个月反转 45 万张，3 年分位 97.5、全史分位 84.3（2016 年峰值 351,383）；<b>可可</b>净空 −11,273（全史 13.6%、3 年 21.0%），本周回补 +7,113；<b>咖啡</b>净多 23,823，本周减持 −6,923，3 年分位 18.5 为软商品中最低；<b>橙汁</b>净头寸 −28（几乎零），OI 仅 11,206，信号价值低。</li>
<li><span class="tag">畜牧</span><b>瘦肉猪</b>净空 −35,121（分位 0.2%，本周回补 +5,337），上周的 −40,458 是 2010 年以来最空；但对比 4 周变化 −23,214，空头是近一个月持续建立、本周刚开始松动。<b>活牛</b>净多 41,915 但本周大减 −11,870、4 周 −25,610，3 年分位 4.5%——多头在快速离场（此前 2019-04 峰值 183,134）。<b>育肥牛</b>净空 −1,744，OI 单周 −17,035（减仓离场）。</li>
<li><span class="tag">乳品</span>全线净空且多数处于历史极低分位：<b>黄油</b> −5,503（1.3%，非商多仅 129 张 vs 空 5,632）；<b>脱脂奶粉</b> −4,086（1.8%）；<b>三级牛奶</b> −8,283（3.7%）；<b>奶酪</b> −12,106（3 年分位 1.9%）。乳品整体是投机资金最看空的农产品板块，且空头集中在近月合约。</li>
</ul></div>

<h2>七、口径限制与注意事项</h2>
<div class="note"><ul>
<li><b>数据滞后</b>：COT 反映截至周二（9/1）的持仓，9/2–9/4 的三个交易日变化未包含；周五发布后市场已消化部分信息。</li>
<li><b>净头寸 ≠ 净头寸价值</b>：不同品种合约规模不同（小麦/玉米/大豆 5,000 蒲式耳、豆油 60,000 磅、豆粕 100 短吨、活牛 40,000 磅），跨品种不可直接比较张数，请以"净/OI"或分位数横向比较。</li>
<li><b>套利头寸不计入净头寸</b>：谷物类套利头寸规模很大（玉米 895,659、大豆 408,355、小麦 SRW 247,090），这部分是跨期价差交易，不代表方向性押注。</li>
<li><b>非商业分类的局限</b>：Legacy 口径的"非商业"混合了趋势跟踪型 CTA 与商品指数基金的被动多头，二者行为模式不同；如需细分请参照分类持仓（Managed Money / Swap Dealers / Producer-Merchant），本报告仅附 MM 净头寸作方向交叉验证。</li>
<li><b>各品种可回溯区间不同（重要）</b>：玉米/大豆/豆油/豆粕/棉花/糖/咖啡/可可/活牛/瘦肉猪/三级牛奶等自 2010-01 起（870 周）；小麦 SRW/HRW 自 2013-12 起（664 周，此前 CFTC 以 "WHEAT - CBOT" 单一合约统计，与现行 SRW 口径不同，<b>未合并</b>）；HRS 自 2014-03 起，Minneapolis Grain Exchange 于 2024-11 更名为 MIAX Futures Exchange（本报告已将两段按同一合约合并，650 周）；油菜籽 422 周、乳清粉 272 周、奶酪 764 周、脱脂奶粉 668 周。故"全史分位"是各品种自身时间轴内的分位，跨品种比较请统一看分位数值而非绝对张数。<span class="dim2">（技术注：2015 年之前 CFTC 历史文件的市场名字段带尾随空格，需归一化后匹配，否则会漏掉 2010–2014 全部数据。）</span></li>
<li><b>分位数的自指性</b>：全史分位包含当前观测值本身，故 100.0% 表示"当前值即为区间内的历史最高"。</li>
</ul></div>

<div class="foot">
数据源：U.S. Commodity Futures Trading Commission（CFTC）Commitments of Traders，官方历史压缩文件 <code>deahistfo2010–2026.zip</code>（Futures-Only, Legacy）与 <code>fut_disagg_txt_2026.zip</code>（Disaggregated）。<br>
明细数据：<code>results/cot/agri_cot_20260901.json</code> / <code>.csv</code> ｜ 生成脚本：<code>scripts/cot_agri_20260905.py</code>、<code>scripts/build_cot_report_20260905.py</code>
</div>
</div>
<script>
if (typeof echarts !== 'undefined') {{
{chart_js()}
}} else {{
  document.querySelectorAll('.chart').forEach(function(e){{e.innerHTML='<div style="padding:24px;color:#999;font-size:12px">图表需加载 ECharts（CDN 不可达）。表格数据不受影响。</div>';}});
}}
</script>
</body></html>"""

p = os.path.join(OD, "index.html")
open(p, "w", encoding="utf-8").write(HTML)
print("written", p, len(HTML), "bytes")
