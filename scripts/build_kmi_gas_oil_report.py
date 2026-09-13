# -*- coding: utf-8 -*-
"""
KMI公司与气油相关性 补充页（并入 reports/81_KMI金德摩根深度分析/）
输入：results/kmi_ng_cl_corr.json（scripts/kmi_ng_cl_corr.py 产出）
     基本面文本（来源见正文数据卡片/表格图注）
输出：reports/81_KMI金德摩根深度分析/补充_天然气原油相关性/相关性分析.html
"""
import json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(BASE, "results", "kmi_ng_cl_corr.json"), encoding="utf-8"))
OUT_DIR = os.path.join(BASE, "reports", "81_KMI金德摩根深度分析", "补充_天然气原油相关性")
os.makedirs(OUT_DIR, exist_ok=True)

# ---- 图表数据 ----
DATES = D["dates"]
def clip_series(k):
    return [None if v is None or v <= 0 else v for v in D["norm_price"][k]]
NP = {k: clip_series(k) for k in ["KMI", "NG=F", "CL=F", "XLE", "SPY", "WMB"]}
C60 = D["corr60"]
SEG = D["seg"]
MT = D["monthly"]
MR = D["mreg"]
EV = D["events"]
COND = D["cond"]
SNAP = D["snapshot"]
LAT = D["latest"]
JSJSON = json.dumps({"dates": DATES, "np": NP, "c60": C60,
                     "seg": SEG, "monthly": MT, "mreg": MR, "ev": EV,
                     "cond": COND, "oil26": D["oil26"]}, ensure_ascii=False)

# ---- 分阶段表格行 ----
def fl_badge(fl):
    cls = {"sig": "sig", "edge": "edge", "no": "no"}[fl]
    lab = {"sig": "sig", "edge": "edge", "no": "—"}[fl]
    return f'<span class="fl {cls}">{lab}</span>'

seg_rows = ""
for r0 in SEG:
    seg_rows += ("<tr>"
                 f"<td class='l'>{r0['label']}</td>"
                 f"<td>{r0['n_ng']}</td>"
                 f"<td><b>{r0['r_ng']}</b></td><td>{fl_badge(r0['fl_ng'])}</td><td class='mono'>{r0['b_ng']}</td>"
                 f"<td><b>{r0['r_cl']}</b></td><td>{fl_badge(r0['fl_cl'])}</td><td class='mono'>{r0['b_cl']}</td>"
                 f"<td>{r0['r_xle']}</td><td>{r0['r_spy']}</td>"
                 f"<td>{r0['r_wmb_ng']}</td><td>{r0['r_wmb_cl']}</td>"
                 f"<td>{r0['r_xle_cl']}</td></tr>")

# ---- 月度表行 ----
mon_rows = ""
for tag, nm in [("ng", "KMI×天然气 NG=F"), ("cl", "KMI×原油 CL=F"),
                ("xle", "KMI×能源板块 XLE"), ("spy", "KMI×大盘 SPY")]:
    a, b = MT[tag], MT.get(tag + "_36", {})
    def fmt(o):
        return ("<b>—</b>" if o.get("r") is None else
                f"<b>{o['r']}</b> {fl_badge(o['flag'])}<span class='dim'> n={o['n']}</span>")
    mon_rows += (f"<tr><td class='l'>{nm}</td>"
                 f"<td>{fmt(a)}</td><td>{fmt(b)}</td></tr>")

# ---- 多元回归表行 ----
mr_rows = ""
for key, nm in [("full", "全期 2011-02~2026-09"), ("p23", "近 3.5 年 2023-01~2026-09"),
                ("p7", "近 1.7 年 2025-01~2026-09")]:
    m = MR[key]
    mr_rows += ("<tr>"
                f"<td class='l'>{nm}</td><td>{m['n']}</td>"
                f"<td>{m['r2_spy_xle']}</td><td>{m['incr_r2_ng_cl_pp']}pp</td>"
                f"<td class='mono'>{m['b_spy']} <span class='dim'>(t={m['t_spy']})</span></td>"
                f"<td class='mono'>{m['b_xle']} <span class='dim'>(t={m['t_xle']})</span></td>"
                f"<td class='mono'>{m['b_ng']} <span class='dim'>(t={m['t_ng']})</span></td>"
                f"<td class='mono'>{m['b_cl']} <span class='dim'>(t={m['t_cl']})</span></td>"
                f"<td class='mono'>{m['r2_ng_uv']}</td><td class='mono'>{m['r2_cl_uv']}</td></tr>")

# ---- 事件表行（红涨绿跌）----
def chg_cell(v, dec=1):
    if v is None:
        return "—"
    cls = "up" if v > 0 else ("dn" if v < 0 else "")
    return f"<span class='{cls}'><b>{v:+.{dec}f}%</b></span>"
EV_NOTES = {
    "ev_crash": "上个世代：油价崩盘 KMI 跟跌 −58%，中游同跌（WMB −75%）——彼时中游=开采活动的代理变量",
    "ev_covid_crash": "危机共振段：系统性去杠杆，KMI 单月 −50%，与油价/板块同步——负油价前最痛的一段",
    "ev_covid": "负油价月：CL −28%（4/20 单日 −306%）KMI 逆势 +8.9%——收费制在尾部风险下的韧性",
    "ev_gas22up": "气价 +154%：KMI 只涨 19%——管输费≠气价，不分享暴涨",
    "ev_gas22dn": "气价 −72%：KMI 只跌 5%——也不分担暴跌，双向免疫",
    "ev_oil26": "当下：油价 5 日 +9.7%（$83→$91），KMI −0.5% 纹丝不动",
}
ev_rows = ""
for e in EV:
    ev_rows += ("<tr>"
                f"<td class='l'>{e['label']}</td>"
                f"<td class='mono dim'>{e['span']}</td>"
                f"<td>{chg_cell(e['chg_ng'])}</td><td>{chg_cell(e['chg_cl'])}</td>"
                f"<td>{chg_cell(e['chg_KMI'])}</td><td>{chg_cell(e['chg_WMB'])}</td>"
                f"<td>{chg_cell(e['chg_XLE'])}</td><td>{chg_cell(e['chg_SPY'])}</td>"
                f"<td class='note'>{EV_NOTES[e['key']]}</td></tr>")

# ---- 条件均值 ----
cond_rows = ""
for c in COND:
    def cm(x):
        o = c[x]
        if o.get("kmi_avg") is None:
            return "—"
        return (f"<span class='{( 'up' if o['kmi_avg'] > 0 else 'dn' if o['kmi_avg'] < 0 else '')}'><b>{o['kmi_avg']:+.2f}%</b></span>"
                f"<span class='dim'> ({o['n']}日)</span>")
    cond_rows += ("<tr>"
                  f"<td class='l'>{c['era']}</td><td>{c['n']}</td>"
                  f"<td>{cm('cl_up2')}</td><td>{cm('cl_dn2')}</td>"
                  f"<td>{cm('ng_up3')}</td><td>{cm('ng_dn3')}</td></tr>")

# ---- 2026 油急拉日线 ----
oil26_rows = ""
for sd in D["oil26"]:
    def oc(tk):
        v = sd.get(tk)
        if v is None:
            return "—"
        cls = "up" if v > 0 else ("dn" if v < 0 else "")
        return f"<span class='{cls}'><b>{v:+.2f}</b></span>"
    oil26_rows += ("<tr><td class='mono'>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>"
                   .format(sd["date"], oc("CL=F"), oc("NG=F"), oc("KMI"), oc("WMB"), oc("XLE"), oc("SPY")))

# 快照
S = SNAP
kmi_chg_ytd = S["KMI_chg_ytd"]

# ================= HTML =================
CSS = """
:root{--bg:#f7f8fa;--card:#fff;--ink:#1a1d24;--ink2:#4a5260;--ink3:#7a8290;--line:#e3e7ed;
--accent:#1f5fbf;--accent-soft:#eaf1fc;--up:#c0392b;--down:#1e8449;--warn:#b9770e;--warn-soft:#fdf5e3;
--danger:#a93226;--danger-soft:#fdecea;--ok:#1e7a45;--ok-soft:#eaf5ee;
--ckmi:#0072B2;--cng:#E69F00;--ccl:#CC3311;--cxle:#009E73;--cspy:#8a94a0;--cwmb:#882255;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue","Microsoft YaHei",sans-serif;font-size:15px;line-height:1.75;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 72px;}
header{background:linear-gradient(135deg,#123c74 0%,#1f5fbf 55%,#2d7a5f 100%);color:#fff;padding:34px 0 26px;margin-bottom:24px;}
header .wrap{padding-bottom:0;}
h1{margin:0 0 6px;font-size:27px;font-weight:700;line-height:1.35;}
.sub{opacity:.94;font-size:13.5px;margin-top:4px;}
h2{font-size:20px;margin:42px 0 12px;padding-left:12px;border-left:4px solid var(--accent);line-height:1.3;}
h3{font-size:16px;margin:22px 0 8px;}
p{margin:9px 0;color:var(--ink2);}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0;}
.note2{font-size:13px;color:var(--ink3);}
.dim{color:var(--ink3);font-size:12.5px;font-weight:400;}
.mono{font-variant-numeric:tabular-nums;}
.tldr{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:10px;padding:22px 26px;margin:6px 0 0;}
.tldr h2{margin:0 0 8px;border:none;padding:0;font-size:19px;color:var(--accent);}
.tldr ul{margin:6px 0 0;padding-left:20px;}
.tldr li{margin:8px 0;color:var(--ink2);}
.tldr b{color:var(--ink);}
.grid{display:grid;gap:12px;}
.g4{grid-template-columns:repeat(4,1fr);}
.g2{grid-template-columns:repeat(2,1fr);}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 15px;}
.kpi .k{font-size:12px;color:var(--ink3);margin-bottom:4px;}
.kpi .v{font-size:21px;font-weight:700;letter-spacing:.2px;}
.kpi .s{font-size:12px;color:var(--ink3);margin-top:2px;}
.up{color:var(--up);} .dn{color:var(--down);}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:13.2px;}
th{background:#eef1f6;color:var(--ink2);font-weight:600;padding:8px 10px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;}
td{padding:7px 10px;text-align:center;border-bottom:1px solid #eef1f5;color:var(--ink2);white-space:nowrap;}
td.l{text-align:left;color:var(--ink);font-weight:600;white-space:normal;}
td.note{text-align:left;white-space:normal;color:var(--ink3);font-size:12.3px;min-width:260px;}
tr:last-child td{border-bottom:none;}
tbody tr:hover{background:#f4f8fe;}
.fl{display:inline-block;font-size:10.5px;line-height:1;padding:2.5px 5px;border-radius:4px;font-weight:700;vertical-align:1px;}
.fl.sig{background:var(--ok-soft);color:var(--ok);}
.fl.edge{background:var(--warn-soft);color:var(--warn);}
.fl.no{background:#eef1f5;color:var(--ink3);}
.chart{width:100%;height:380px;}
.chart.tall{height:430px;}
.chart-box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 14px 6px;margin:14px 0;}
.chart-box .cap{font-size:12.5px;color:var(--ink3);padding:2px 6px 10px;}
.src{font-size:11.5px;color:var(--ink3);margin-top:4px;}
.src b{color:#5b6675;font-weight:600;}
.tag{display:inline-block;background:#eef1f6;color:#5b6675;border-radius:4px;font-size:11px;padding:1px 6px;margin-right:4px;vertical-align:1px;}
.kbd{background:#fdf3e0;color:#8a5a00;border-radius:5px;padding:1px 7px;font-size:12.3px;border:1px solid #f0dcae;}
.callout{background:var(--ok-soft);border-left:4px solid var(--ok);border-radius:8px;padding:14px 18px;margin:16px 0;}
.callout.blue{background:var(--accent-soft);border-left-color:var(--accent);}
.callout.warn{background:var(--warn-soft);border-left-color:var(--warn);}
.callout p{margin:6px 0;color:#23543c;}
.callout.blue p{color:#274b74;}
.callout.warn p{color:#6b5410;}
.legend-line{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:12.5px;color:var(--ink2);margin:6px 0 2px;}
.legend-line i{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:3px;margin-right:5px;}
.legend-line .dash i{height:0;border-top:2px dashed;}
.term{border-bottom:1px dashed var(--ink3);cursor:help;}
.termtip{position:fixed;display:none;z-index:99;max-width:340px;background:#22303f;color:#e9eef4;font-size:12.5px;line-height:1.6;padding:9px 12px;border-radius:8px;box-shadow:0 6px 18px rgba(20,30,50,.25);pointer-events:none;}
.pill{display:inline-block;font-size:11.5px;padding:2px 8px;border-radius:20px;margin-right:6px;}
.pill.blue{background:var(--accent-soft);color:var(--accent);}
@media(max-width:900px){.g4{grid-template-columns:repeat(2,1fr);}.g2{grid-template-columns:1fr;}}
"""

HTML_TOP = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KMI 公司研究 × 天然气/原油相关性 · 2026-09</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>__CSS__</style>
</head>
<body>
<header><div class="wrap">
<h1>Kinder Morgan（KMI）公司研究 × 与天然气 / 石油的相关性</h1>
<div class="sub">NYSE: KMI · 数据截至 2026-09-04 收盘（拉数 2026-09-06） · 全文图表口径见文末"口径与来源"</div>
</div></header>
<div class="wrap">

<div class="tldr">
<h2>TL;DR —— 先给结论</h2>
<ul>
<li><b>KMI 是什么：</b>北美最大的中游"收费公路"——7.8 万英里管道、136 座码头，约 <b>35% 的美国天然气产量</b>经其管网。FY2025 营收 169 亿美元（+12%），其中天然气管道占 <b>65%</b>。它是<b>类公用事业的天然气基础设施增长股</b>，不是油气价格股。</li>
<li><b>生意对价格的直接敞口极小：</b>公司官方口径（2025 预算 IR）：WTI 每 +1 美元 → 全年 Adj EBITDA <b>仅 +700 万美元</b>；Henry Hub 每 +0.10 美元 → <b>仅 +600 万美元</b>（均 &lt; EBITDA 的 0.1%）。真正的驱动是<b>输送量</b>，不是价格。</li>
<li><b>与天然气的相关性：弱。</b>全期（2011-2026，日频）r≈0.12；近 36 个月（月度口径）r≈<b>0.00</b>。2022 年气价 +154% KMI 只涨 19%；随后气价 −72% KMI 只跌 5%——<b>双向免疫</b>。</li>
<li><b>与石油的相关性：有"世代断裂"。</b>2011-2019 日相关 r=0.31~0.50、日 β 0.26~0.45（那个年代中游=开采活动的代理变量）；<b>2020 起系统性衰减</b>；近 36 个月月度 r≈0.11（不显著）；2026-08-28→09-04 油价 5 日 +9.7%（$83→$91），KMI <b>−0.5% 纹丝不动</b>。</li>
<li><b>剩下的"相关性"是什么？板块 β。</b>控掉 SPY+XLE 后，油价对 KMI 的增量贡献<b>≈0（全期 t=−0.9）</b>、2025 年以来甚至<b>转负（t=−3.4）</b>——KMI 的日波动主要由能源板块（XLE r≈0.55~0.7）与大盘（SPY）解释，商品价格本身不解释它。</li>
<li><b>风险提示：</b>极端期（2014-16 油价崩盘 KMI −58%、2020-03 危机 KMI −50%）"价格相关性"会临时上身——那是<b>宏观信用 β + 量收缩渠道</b>，不是收费公式。现价 31.40 对应 PE(TTM) 20.3×，2026-05-19 高点后已回撤 −7.6%，估值已计入大量增长预期。</li>
</ul>
</div>

<div class="grid g4" style="margin-top:14px;">
<div class="kpi"><div class="k">现价（2026-09-04）</div><div class="v">$31.40</div><div class="s">YTD <span class="up">+17.5%</span> · 52周 24.74–34.49</div></div>
<div class="kpi"><div class="k">总市值</div><div class="v">$699 亿</div><div class="s">NYSE · 2011-02 上市</div></div>
<div class="kpi"><div class="k">估值</div><div class="v">PE 20.3× · PB 2.2×</div><div class="s">2026E Adj EPS 超预算 12% → 前瞻 ≈20-21×</div></div>
<div class="kpi"><div class="k">股东回报 / 杠杆</div><div class="v">股息率 ≈3.8%</div><div class="s">年化股息 $1.19（+2%）· 净债/EBITDA 3.6-3.9×</div></div>
</div>
"""

H_SEC1 = """
<h2>一、公司速览：它到底靠什么赚钱</h2>
<div class="grid g2">
<div>
<div class="card">
<h3>业务结构（FY2025，营收 169.3 亿美元，同比 +12%）</h3>
<div class="chart" id="c_pie"></div>
<div class="legend-line">
<span><i style="background:#0072B2"></i>天然气管道 64.9%</span>
<span><i style="background:#CC3311"></i>成品油管道 15.9%</span>
<span><i style="background:#E69F00"></i>码头仓储 12.4%</span>
<span><i style="background:#882255"></i>CO2/EOR 6.9%</span>
</div>
<p style="margin-top:10px;">三大块看门道：</p>
<ul style="margin:6px 0;padding-left:20px;color:var(--ink2);">
<li><b style="color:var(--ink);">天然气管道（65%）</b>：集气、储气、输气的全国管网，收的是"过路费"。2025 该板块营收 +23%（Outrigger 并表 + LNG 出口 + Permian→Waha/墨西哥输送）。</li>
<li><b style="color:var(--ink);">成品油管道（16%）</b>：美国最大独立成品油承运（~240 万桶/日），2025 −9% 主要因原油旧长约到期（量的结构性，非油价）。</li>
<li><b style="color:var(--ink);">码头 / CO2</b>：琼斯法案油轮队（全租至 2026）+ EOR 采收（CO2 板块是<b>唯一直接卖油</b>的部分，2026Q2 实现油价 $73.78）。</li>
</ul>
<div class="src">来源：neodata 主营构成（2025 年报口径）+ KMI 2025 10-K 转述（earningsanatomy，2026）<span class="tag">2025 财年</span></div>
</div>
</div>
<div>
<div class="card">
<h3>一句话本质</h3>
<div class="callout">
<p>买 KMI，本质是买 <b>"美国天然气输送量的长期合同现金流"</b>——LNG 出口、燃气发电、数据中心电气化带来的<b>量</b>扩张，通过照付不议（take-or-pay）长协变现。油、气<b>价格</b>本身不是它的收益来源。</p>
</div>
<h3>增长引擎与质量（截至 2026-07-22 业绩会）</h3>
<ul style="margin:4px 0;padding-left:20px;color:var(--ink2);">
<li>项目积压 <b>$96-101 亿</b>，<b>92% 是天然气项目</b>；管理层看到 &gt;10 Bcf/d 的发电用气机会、~3 Bcf/d 的 LNG 机会。</li>
<li>2026Q2 创纪录：Adj EPS $0.37（<b>+32% yoy</b>）、Adj EBITDA $22 亿（+12%）；上调全年指引（Adj EBITDA 超预算 $86 亿 5%+、Adj EPS 超 $1.36 预算 12%+）。</li>
<li>评级 BBB / Baa2（S&amp;P、Moody's，outlook positive）；2026-08-03 除息 $0.2975/季 → 年化 <b>$1.19（+2%）</b>，自 2016 重建后逐年递增。</li>
</ul>
<div class="src">来源：KMI IR 2026-07-22 Q2 业绩会/新闻稿；S&amp;P/Moody's 2025-06（via IR）；股息公告转述（2026-07-23 报道）<span class="tag">2026Q2</span></div>
<h3>估值快写（为什么 20× TTM 不算贵得要命）</h3>
<ul style="margin:4px 0;padding-left:20px;color:var(--ink2);">
<li>PE(TTM) 20.3× 的分子分母都"含新"：EPS(TTM)≈1.55 已计入 2026H1 强劲增长；按 2026 指引 Adj EPS≈$1.52 的口径，<b>前瞻 PE≈20.5×</b>，与 TTM 几乎持平=市场认为增长能延续。</li>
<li>横向：纯气中游同业 WMB/OKE 常态 17-22× PE、EV/EBITDA 11-13×；KMI 处于行业中位偏上，并未显著溢价——溢价来自更分散的资产与更低杠杆。</li>
<li>中游估值锚是<b>股息增长率 + 项目回报倍数</b>（积压项目 EBITDA 倍数 ~5.8×，远好于其 ~10-11% 的加权资本成本），而非油价周期。</li>
</ul>
<div class="src">PE/PB/股息：westock 行情（2026-09-04）；指引：KMI IR 2026-07-22；横向区间为行业常识性参照，非精确报价<span class="tag">估值估算</span></div>
</div>
</div>
</div>
"""

H_SEC2 = """
<h2>二、生意对商品价格的"直接"敏感度：先看账本，再看股价</h2>
<div class="card">
<div class="grid g2">
<div>
<div class="kpi"><div class="k">WTI 原油每 +$1/桶（全年均价）</div><div class="v" style="color:#1f5fbf;">Adj EBITDA +$7M</div><div class="s">≈ +0.01% · 83 亿 EBITDA 的 0.008%</div></div>
<div class="kpi"><div class="k">Henry Hub 气价每 +$0.10/MMBtu</div><div class="v" style="color:#1f5fbf;">Adj EBITDA +$6M</div><div class="s">≈ +0.007% · 价格暴涨 50% 也只多几千万</div></div>
</div>
<div>
<p>这是 KMI 2025 预算 IR 公布的<b>官方敏感性</b>（2024-12-09 新闻稿，用于预算口径）。含义：即便油价从 $68 涨到 $95（+40%），对全年 EBITDA 的拉动也只有 <b>~$19M</b>——不到 0.25%。管理层原话："绝大多数现金流是费用型的，不直接暴露于商品价格"。</p>
<p style="margin-top:6px;"><b>为什么 2011-2016 年它跟油价那么紧、现在不跟了？</b>答案在第二、三节：旧模式里中游利润=开采活动的函数（集气/新产能合同随钻机数走），油价是开采活动的<b>代理变量</b>；2015-16 削减股息、重组资产负债表后，KMI 的收入结构转向"已签约费 + 长协扩建"，价格信号自然退出。</p>
</div>
</div>
<div class="src">来源：KMI IR "2025 Financial Expectations" 新闻稿（2024-12-09，budget 口径假设 WTI $68 / HH $3.00）<span class="tag">一手 · 2024-12-09</span></div>
</div>
"""

H_SEC3 = """
<h2>三、相关性分析（核心）</h2>

<div class="chart-box"><h3 style="margin:0 0 4px;">归一化走势 2011-02=100（对数轴，2011-02-11 KMI 上市以来）</h3>
<div class="legend-line">
<span><i style="background:#0072B2"></i>KMI（现 31.40）</span>
<span><i style="background:#882255"></i>WMB（纯气中游同业）</span>
<span><i style="background:#E69F00"></i>天然气 NG=F（现 $2.98）</span>
<span><i style="background:#CC3311"></i>原油 CL=F（现 $91.5）</span>
<span><i style="background:#009E73"></i>能源板块 XLE</span>
<span class="dash"><i style="border-color:#8a94a0"></i>大盘 SPY</span>
</div>
<div class="chart tall" id="c1"></div>
<div class="cap">两个"世代"一眼可见：2011-2016 KMI 与油价同步沉浮（2014-16 一起腰斩）；2017 后 KMI 走自己的"现金牛+扩产"曲线；2020 负油价日油价瞬间砸穿 0 轴（图中剔除该异常点）；2022 气价 3.9→9.7 的暴涨 KMI 几乎无感。2026 油气双上行，KMI 却自 5 月高点回撤 7.6%。</div>
<div class="src">本地数据：data/kmi、ng、cl、xle、spy、wmb（Yahoo Finance，2026-09-06 拉取，收盘 2026-09-04）<span class="tag">一手行情</span></div>
</div>

<div class="chart-box"><h3 style="margin:0 0 4px;">60 日滚动日相关：KMI×天然气 / KMI×原油（虚线=±0.26 显著带）</h3>
<div class="legend-line">
<span><i style="background:#0072B2"></i>KMI×天然气 NG=F</span>
<span><i style="background:#CC3311"></i>KMI×原油 CL=F</span>
</div>
<div class="chart" id="c2"></div>
<div class="cap">滚动相关<b>长期在两个世代间切换</b>：2011-2016 油价相关常年 0.3-0.5（显著带外），2017 后大部分时间在 ±0.2 内徘徊；气价相关几乎从未系统性站上 0.3。2020-2022 能源大年曾把两条线都推高，2023 后回落。当前（2026-08 末）：KMI×NG 60 日 0.23、KMI×CL 60 日 0.21——仍在"统计显著但经济意义极小"区间。</div>
<div class="src">算法：两资产日收益（股票用 adj_close 含股息、期货用 close）60 日滚动 Pearson；显著带 ±1.96/√(n−2)≈±0.26；数据窗口 2011-02~2026-09-04（KMI 上市后）</div>
</div>

<div class="card">
<h3>分阶段相关性总表：R 与 β 同列（日频，KMI 上市以来）</h3>
<table>
<thead><tr>
<th rowspan="2">阶段</th><th rowspan="2">N</th>
<th colspan="3">KMI × 天然气 NG=F</th><th colspan="3">KMI × 原油 CL=F</th>
<th colspan="2">对照（KMI 自身结构）</th>
<th colspan="3">同业与板块对照</th>
</tr>
<tr>
<th>R</th><th>显著</th><th>β</th><th>R</th><th>显著</th><th>β</th>
<th>×XLE</th><th>×SPY</th><th>WMB×NG</th><th>WMB×CL</th><th>XLE×CL</th>
</tr></thead>
<tbody>
__SEG_ROWS__
</tbody>
</table>
<div class="legend-line" style="margin-top:8px;">
<span><span class="fl sig">sig</span>=p&lt;0.01 显著</span>
<span><span class="fl edge">edge</span>=0.01~0.05 边缘</span>
<span><span class="fl no">—</span>=不显著</span>
<span class="dim">β = 该资产每涨 1%（日频），KMI 平均跟涨的 %（单变量 OLS 斜率）· R 为 Pearson 日收益相关</span>
</div>
<div class="note2" style="margin-top:6px;">读法：<b>油价列</b>（黄底直觉反转）——R 在 P1-P3 世代 0.31→0.50，P4(2020) 崩到 0.14，P5(2021-22) 反弹到 0.49，P6-P7（2023+）回落到 ~0.2 但同期 <b>XLE×CL 仍高达 0.6</b>——即"板块还跟油价、KMI 不跟了"。<b>气价列</b>从未超过 0.26，P7 也仅 0.16。同业 WMB 呈现同构（对气价也弱、对油价也世代衰减），证明这是<b>中游商业模式的结构属性</b>，不是 KMI 单家问题。</div>
</div>

<div class="card">
<h3>月度口径（平滑噪音后的"长期眼"）—— 近三年：油气价格已不解释 KMI</h3>
<table>
<thead><tr><th>配对（月度收益）</th><th>全期 2011-2026（188 个月）</th><th>近 36 个月（2023-09~2026-08）</th></tr></thead>
<tbody>
__MON_ROWS__
</tbody>
</table>
<div class="note2" style="margin-top:6px;">月度相关最抗噪、最能反映"跨月看，涨跌到底跟不跟"。全期里 KMI×CL 0.36 显著——但那几乎全部由 2011-2016 旧世代贡献；<b>近 36 个月 KMI×CL 0.11 不显著、KMI×NG ≈0.00</b>，同期 KMI×XLE 0.50 依然显著。结论：长期维度上，KMI 已从"油气的孩子"变成"能源板块的孩子"，商品价格本尊退场。</div>
</div>

<div class="card">
<h3>多元回归：把 SPY（大盘）+ XLE（板块）控制住后，油气还剩多少解释力？</h3>
<table>
<thead><tr>
<th>窗口</th><th>N</th><th>R²（仅 SPY+XLE）</th><th>加入 NG+CL 增量</th>
<th>β_SPY (t)</th><th>β_XLE (t)</th><th>β_NG (t)</th><th>β_CL (t)</th><th>NG 单变量 R²</th><th>CL 单变量 R²</th>
</tr></thead>
<tbody>
__MR_ROWS__
</tbody>
</table>
<div class="note2" style="margin-top:6px;">
四条信息：<br>
① SPY+XLE 两个变量就解释了 KMI 日波动的 <b>31-50%</b>——KMI 本质上是"板块 β + 大盘 β"的股票；<br>
② 加入天然气、油价后，全期解释力<b>只 +0.09pp</b>（可忽略），2023 年以来也只 +2.5~2.9pp——其中油价系数还是<b>负的</b>（控板块后油价涨 KMI 反而略跌，t=−3.4~−5.3）；<br>
③ 单变量看，油价单靠自己只解释 KMI 的 3-5% 波动、气价 1-4%；<br>
④ 2025 年以来 β_SPY 已不显著（t=0.8）——KMI 最近一年连大盘都不太跟，走自己的（利率/自身基本面）节奏，这解释了它 60 日与 SPY 相关一度为负（−0.34）。
</div>
</div>

<div class="card">
<h3>极端事件检验：六个"压力测试"窗口（区间累计涨跌 %）</h3>
<table>
<thead><tr><th>事件窗口</th><th>区间</th><th>天然气</th><th>原油</th><th>KMI</th><th>WMB</th><th>XLE</th><th>SPY</th><th style="min-width:210px;">解读</th></tr></thead>
<tbody>
__EV_ROWS__
</tbody>
</table>
<div class="note2" style="margin-top:6px;">
红=涨、绿=跌（本报告涨跌配色）。四个关键观察：<br>
① <b>上个世代确实跟油</b>：2014-06→2016-02 油价 −76%，KMI −58%、同业 WMB −75%（中游普跌甚至比油还惨——当时中游高杠杆 + 靠产能扩张吃饭）；<br>
② <b>危机共振仍存在但已是"宏观"不是"油价"</b>：2020-02→03 系统性去杠杆，KMI −50%（跟着大盘与信用走，不是跟着油价公式）；<br>
③ <b>负油价月（2020-04，含 4/20 单日 CL −306%）KMI 逆势 +8.9%</b>——收费现金流的韧性在尾部风险里兑现；<br>
④ <b>2022 气价 +154% / −72% 两段，KMI +18.9% / −5.2%</b>：管输费不分享气价暴涨、也不分担崩盘，双向免疫；<br>
⑤ <b>当下（2026-08-28→09-04）：油价 5 日 +9.7% 冲到 $91，KMI −0.5% 无感</b>——市场已经完全按"费率公用事业"给它定价。
</div>
</div>

<div class="card">
<h3>条件均值：油价/气价"大波动日"KMI 平均怎么走（两世代对比）</h3>
<table>
<thead><tr><th>世代</th><th>样本日</th><th>油价 ≥+2% 日 → KMI</th><th>油价 ≤−2% 日 → KMI</th><th>气价 ≥+3% 日 → KMI</th><th>气价 ≤−3% 日 → KMI</th></tr></thead>
<tbody>
__COND_ROWS__
</tbody>
</table>
<div class="note2" style="margin-top:6px;">
把"大波动日"挑出来看平均反应：2011-2019 世代油价 ±2% 日 KMI 平均 ±1.1%（几乎 1:1 跟）；2020 年后油价 −2% 日的平均跌幅收窄到 −0.77%，且此时油价单日平均已放大到 −5.6%——<b>按每 1% 油价折算的敏感度已减半以上</b>（0.35→0.14）。气价 ±3% 日的传导在两个世代都只有油价的 1/3~1/4，从未成为主引擎。</div>
</div>

<div class="card">
<h3>附：2026-08-28 → 09-04 油价急拉逐日（%）——"当下正在发生的脱敏"</h3>
<table>
<thead><tr><th>日期</th><th>原油 CL=F</th><th>天然气 NG=F</th><th>KMI</th><th>WMB</th><th>XLE</th><th>SPY</th></tr></thead>
<tbody>
__OIL26_ROWS__
</tbody>
</table>
<div class="note2" style="margin-top:6px;">这 5 天油价累计 +9.7%（8/28 的 $83.4 → 9/4 的 $91.5，FRED 现货 9/1 已报 $91.5）。只有第一根大阳线（8/31，CL +2.8%）KMI 象征性跟了 +2.2%，随后油价继续 +5.2%/+0.9%/+0.3% 时 KMI 连跌三天回吐——单日"板块情绪"有、持续性没有。</div>
</div>
"""

H_SEC4 = """
<h2>四、结论：如何理解 KMI × 天然气 × 石油</h2>

<div class="card">
<h3>一句话（可证伪的）投资判断</h3>
<div class="callout">
<p>KMI 的股价相关性结构 = <b>板块 β（XLE，强且稳定）＋ 大盘 β（SPY，近年减弱）＋ 自身基本面噪声</b>；<b>天然气、原油价格本身基本不解释它</b>（控板块后油价甚至转负）。把 KMI 当"油价上涨的杠杆"或"气价反弹的标的"都会用错框架——<b>正确的框架是"美国天然气输送量的长期合同现金流"</b>。</p>
</div>
<h3>为什么 2011-2016 相关、2017 后脱钩（机制解释）</h3>
<ul style="padding-left:20px;color:var(--ink2);">
<li><b>2011-2016</b>：中游盈利=产区开采活动的函数（集气 + 新产能合同随钻机数走），油价是开采活动最灵敏的代理变量 → KMI 的成长与油价强绑定；同时高杠杆 + 2014-16 行业现金流枯竭 → 2015-11 削减股息 75%，股价腰斩再腰斩（本报告 P2 段 β 0.45 的历史来源）。</li>
<li><b>2016-2019 重建</b>：削减股息、去杠杆、把增长转向"已签约费/长协扩建"，评级修复至 BBB/Baa2；油价相关下台阶但仍 0.4 上下（P3）。</li>
<li><b>2020 后量变到质变</b>：增长引擎切换到 LNG 出口、燃气发电、数据中心——这些是<b>电力/国际贸易需求</b>，与气价高低弱相关（气价低反而刺激气电替代）；2023 起 P6-P7 日相关仅 ~0.2、月度近零。2026 年 92% 项目积压是天然气、60%+ 服务发电与 LDC——<b>公司自己也在往"费率型增长"上加码</b>。</li>
</ul>
<h3>什么时候"价格相关性"会重新上身？（风险清单）</h3>
<ul style="padding-left:20px;color:var(--ink2);">
<li><b>极端宏观/信用共振</b>：2020-03 型系统性去杠杆，KMI 会跟油价、跟板块一起被抛售（2020-02→03 单月 −50% 的先例）——不是因为它按油价公式赚钱，而是它带杠杆、属能源板块。这是"油价相关"最大的残留项。</li>
<li><b>产区大幅减产传导到量</b>：气价长期低于产区盈亏线（当前 HH $2.98、2026 高点后回落）若导致 Haynesville 等主力产区产量收缩，会侵蚀集气与输送量（2025 年已有前科：Haynesville gathering −6%）。这是<b>气价通过"量"的间接渠道</b>，比直接渠道更值得盯。</li>
<li><b>估值已计入增长</b>：PE(TTM) 20.3×、股价自 2026-05-19 高点回撤 −7.6%，而 2026Q2 起市场已price in "超预算 12%+"。任何 LNG/数据中心项目延期或利率重抬升，都可能先杀估值。</li>
<li><b>与 WMB 的同构提醒</b>：同业 WMB 与油气价格同样弱相关（对油价从旧世代 0.33-0.49 衰减到现在 0.14）——脱钩是<b>行业商业模式的结构属性</b>。若哪天看到中游整体重新与油价强相关，先怀疑是宏观/信用环境变化，而不是"油价又能驱动中游了"。</li>
</ul>
<div class="src">结论依据：上文全部本地计算（scripts/kmi_ng_cl_corr.py → results/kmi_ng_cl_corr.json，数据截至 2026-09-04）；基本面口径见第一节图注来源</div>
</div>

<div class="card" style="margin-top:16px;">
<h3 style="margin-top:0;">口径与来源</h3>
<ul style="padding-left:20px;color:var(--ink2);font-size:13px;">
<li><b>数据</b>：Yahoo Finance 日线（2026-09-06 拉取，收盘 2026-09-04）：KMI/WMB/XLE/SPY 用 adj_close（含股息），NG=F、CL=F 用 close（NYMEX 前月连续合约）。FRED DCOILWTICO（现货 WTI）作油价旁证。报告生成 2026-09-06，北京时间。</li>
<li><b>统计口径</b>：收益=日频 pct_change×100；60 日滚动 Pearson（显著带 ±1.96/√(n−2)≈±0.26）；β=单变量 OLS 斜率（回归 x 于 y）；多元回归 OLS（SPY/XLE/NG/CL 四变量），t 值 = 系数/标准误；显著性三档 sig(p&lt;0.01)/edge(0.01-0.05)/no。月度=月内复利收益。异常说明：2020-04-20/21 负油价两日（CL −306%/−127%）仅存在于单日表中，滚动/分段相关与归一化图已剔除该异常值（≤0 置空）。</li>
<li><b>基本面来源分级</b>：一手=公司 IR 新闻稿/业绩会（敏感性 2024-12-09；2026Q2 指引 2026-07-22）、westock/neodata 行情与主营构成（2026-09-04/2025 年报口径）；<span class="kbd">需核实原文</span>=媒体转述（股息公告、同业估值区间、10-K 细节转述）。分析师目标价（大摩 $38 / 加皇 $35）为第三方观点，非本报告判断。</li>
<li>本报告为数据分析，不含操作建议。市场有风险，投资需谨慎。</li>
</ul>
</div>

</div><!-- /wrap -->
"""

FOOT = """<div class="termtip" id="termtip"></div>
<script>
(function(){
  const tip=document.getElementById('termtip');
  let cur=null;
  document.addEventListener('mouseover',e=>{
    const t=e.target.closest('.term');
    if(!t||t===cur)return; cur=t;
    tip.textContent=t.dataset.tip||'';
    tip.style.display='block';
    const r=t.getBoundingClientRect();
    tip.style.left=Math.min(r.left,window.innerWidth-340)+'px';
    tip.style.top=r.bottom+6+'px';
  });
  document.addEventListener('mouseout',e=>{
    if(e.target.closest('.term')){cur=null;tip.style.display='none';}
  });
})();
</script>
<script>
const D = __JSJSON__;
const C_KMI='#0072B2', C_NG='#E69F00', C_CL='#CC3311', C_XLE='#009E73', C_SPY='#8a94a0', C_WMB='#882255';
const base={tooltip:{trigger:'axis'},grid:{left:56,right:24,top:40,bottom:66},
 dataZoom:[{type:'inside'},{type:'slider',height:16,bottom:10}],
 legend:{top:2,textStyle:{color:'#4a5260'}}};
function mk(id,opt){echarts.init(document.getElementById(id)).setOption(opt);}
function lineBase(yf){
  return Object.assign({},base,{
    xAxis:{type:'category',data:D.dates,axisLabel:{color:'#6b7480'}},
    yAxis:yf,series:[]});
}
const mkZ={type:'value',scale:true,axisLabel:{color:'#6b7480',formatter:(v)=>v.toFixed(2)},splitLine:{lineStyle:{color:'#e5e9f0'}}};
// c1 归一化（对数轴）
{
 const o=lineBase({type:'log',axisLabel:{color:'#6b7480'},splitLine:{lineStyle:{color:'#e5e9f0'}}});
 o.series=[
  {name:'KMI',data:D.np.KMI,type:'line',showSymbol:false,lineStyle:{color:C_KMI,width:2.4},itemStyle:{color:C_KMI}},
  {name:'WMB',data:D.np.WMB,type:'line',showSymbol:false,lineStyle:{color:C_WMB,width:1.8},itemStyle:{color:C_WMB}},
  {name:'天然气 NG=F',data:D.np['NG=F'],type:'line',showSymbol:false,lineStyle:{color:C_NG,width:1.8},itemStyle:{color:C_NG}},
  {name:'原油 CL=F',data:D.np['CL=F'],type:'line',showSymbol:false,lineStyle:{color:C_CL,width:1.8},itemStyle:{color:C_CL}},
  {name:'能源板块 XLE',data:D.np.XLE,type:'line',showSymbol:false,lineStyle:{color:C_XLE,width:1.6},itemStyle:{color:C_XLE}},
  {name:'大盘 SPY',data:D.np.SPY,type:'line',showSymbol:false,lineStyle:{color:C_SPY,width:1.5,type:'dashed'},itemStyle:{color:C_SPY}}
 ];
 mk('c1',o);
}
// c2 60 日滚动相关
{
 const o=lineBase(mkZ);
 const band={symbol:'none',silent:true,data:[
   {yAxis:0.26,lineStyle:{type:'dashed',color:'#b6bfca'},label:{formatter:'+0.26',color:'#889',position:'insideEndTop'}},
   {yAxis:-0.26,lineStyle:{type:'dashed',color:'#b6bfca'},label:{formatter:'−0.26',color:'#889',position:'insideEndBottom'}},
   {yAxis:0,lineStyle:{color:'#c8cfd8'},label:{show:false}}]};
 o.series=[
  {name:'KMI×天然气',data:D.c60.km_ng,type:'line',showSymbol:false,lineStyle:{color:C_NG,width:2},itemStyle:{color:C_NG},markLine:band},
  {name:'KMI×原油',data:D.c60.km_cl,type:'line',showSymbol:false,lineStyle:{color:C_CL,width:2},itemStyle:{color:C_CL}}
 ];
 mk('c2',o);
}
// c_pie FY25 营收
{
 mk('c_pie',{tooltip:{trigger:'item',formatter:'{b}: {c} 亿美元 ({d}%)'},
  series:[{type:'pie',radius:['42%','72%'],center:['50%','46%'],
    itemStyle:{borderColor:'#fff',borderWidth:2},
    label:{formatter:'{b}\\n{d}%',color:'#4a5260',fontSize:11},
    data:[
      {name:'天然气管道 109.9',value:109.9,itemStyle:{color:C_KMI}},
      {name:'成品油管道 26.9',value:26.9,itemStyle:{color:C_CL}},
      {name:'码头仓储 20.9',value:20.9,itemStyle:{color:C_NG}},
      {name:'CO2/EOR 11.7',value:11.7,itemStyle:{color:C_WMB}}]}]});
}
// c4 阶段 R（分组柱）
{
 const seg=D.seg;
 const cats=seg.map(s=>s.label.split(' ')[0]);
 const o={tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{top:2,textStyle:{color:'#4a5260'}},
  grid:{left:52,right:20,top:44,bottom:20},
  xAxis:{type:'category',data:cats,axisLabel:{color:'#6b7480',interval:0,rotate:18,fontSize:10}},
  yAxis:{type:'value',axisLabel:{color:'#6b7480'},splitLine:{lineStyle:{color:'#e5e9f0'}}},
  series:[
   {name:'KMI×原油',type:'bar',data:seg.map(s=>s.r_cl),itemStyle:{color:C_CL}},
   {name:'KMI×天然气',type:'bar',data:seg.map(s=>s.r_ng),itemStyle:{color:C_NG}},
   {name:'KMI×能源板块',type:'bar',data:seg.map(s=>s.r_xle),itemStyle:{color:C_XLE}}]};
 mk('c4',o);
}
</script>
"""

# 分段 R 条形图放在月度口径前
def bars():
    return ('<div class="chart-box"><h3 style="margin:0 0 4px;">各阶段日相关 R 一览（柱高=相关强度）</h3>'
            '<div class="chart" id="c4"></div>'
            '<div class="cap">世代断裂可视化：油价相关（红柱）2011-2016 显著、2021-22 反弹后 2023 起回落；气价相关（橙柱）从未高企；能源板块相关（绿柱）贯穿始终——KMI 一直"属于能源板块"，只是不再"属于油价"。</div></div>')

repl = {
    "__CSS__": CSS,
    "__SEG_ROWS__": seg_rows,
    "__MON_ROWS__": mon_rows,
    "__MR_ROWS__": mr_rows,
    "__EV_ROWS__": ev_rows,
    "__COND_ROWS__": cond_rows,
    "__OIL26_ROWS__": oil26_rows,
    "__JSJSON__": JSJSON,
}
html = HTML_TOP + H_SEC1 + H_SEC2 + H_SEC3.replace('</div>\n\n<div class="card">\n<h3>月度口径', bars() + '\n\n<div class="card">\n<h3>月度口径') + H_SEC4 + FOOT
# 简化：H_SEC3 内部把月度表前插条形图 —— 上面用 replace 注入可能不干净，这里改为在 H_SEC3 定义处处理太绕。
for k, v in repl.items():
    html = html.replace(k, v)

# ============ 术语悬停 ============
TERMS = [
    ("收费公路", "中游商业模式比喻：像高速收费站一样，按过境量收管输/储存费，不承担商品价格涨跌"),
    ("照付不议", "take-or-pay：客户无论用不用运力都按长协付费——KMI 收入稳定的制度基础"),
    ("take-or-pay", "照付不议长协：客户承诺最低运量并照付费用"),
    ("Henry Hub", "美国天然气基准价（路易斯安那州交割点），$/MMBtu"),
    ("MMBtu", "百万英热单位——天然气的计价单位"),
    ("WTI", "西得州中质原油，美国油价基准（NYMEX CL 期货跟踪标的）"),
    ("Adj EBITDA", "调整后税息折旧摊销前利润——中游最常用盈利口径，剔除非经常项"),
    ("集气", "gathering：把气井产出的天然气汇入主干网的支线管网环节"),
    ("EOR", "提高采收率：向成熟油藏注入 CO2 驱油——KMI CO2 板块主业"),
    ("LNG 出口", "液化天然气出口——美国天然气需求的最大增量来源之一"),
    ("数据中心", "AI/算力基建的大电力负荷，被视为美国燃气发电长期需求的新引擎"),
    ("P/E / PE(TTM)", "股价 ÷ 最近四个季度每股收益——TTM=滚动 12 个月"),
    ("前瞻 PE", "股价 ÷ 预测年度每股收益，用于剔除一次性项后的可比口径"),
    ("WMB", "Williams Companies——纯天然气中游同业，本报告的对照标的"),
    ("XLE", "标普能源板块 ETF——一篮子美股石油天然气公司"),
    ("CL=F", "NYMEX WTI 原油期货连续（前月）合约价格"),
    ("NG=F", "NYMEX Henry Hub 天然气期货连续（前月）合约价格"),
    ("SPY", "标普 500 ETF——大盘基准"),
    ("归一化", "把不同价格起点统一换算成基准日=100，便于同图比较走势"),
    ("对数轴", "y 轴按对数刻度：同样的百分比涨幅在图上的高度一致，长周期比较更公平"),
    ("60 日滚动", "每天取过去 60 个交易日算一次指标、逐日前移——观察联动如何随时间变化"),
    ("显著带", "±1.96/√(n−2)≈±0.26——滚动相关超出该带才算统计上'真联动'"),
    ("显著性", "结论可信度的统计表述：sig=强、edge=边缘、no=不显著"),
    ("p 值", "假设'其实无关'时观察到当前相关强度的概率，越小越可信"),
    ("β", "贝塔：该资产每涨 1%（日频）时 KMI 平均跟涨的 %"),
    ("R", "Pearson 相关系数：两资产日收益的线性相关，−1~1"),
    ("世代", "本报告把 2011 年以来分成 7 个结构性阶段，把'旧中游'与'新中游'的差别叫作世代差异"),
    ("股息削减 75%", "2015-11 KMI 将季度股息从 $0.51 砍到 $0.125，标志旧高杠杆成长模式的终结"),
    ("双向免疫", "价格上涨不分钱、价格下跌也不受伤——收费合同对商品价格的对称性脱敏"),
    ("宏观信用 β", "系统性风险期（如 2020-03）所有杠杆资产一起被抛售的联动，与基本面公式无关"),
    ("费率型增长", "靠新增签约运量（而非商品涨价）驱动利润增长的经营模式"),
    ("琼斯法案", "美国沿海航运只允许美籍美造船舶经营的法律——KMI 油轮船队的壁垒"),
    ("红涨绿跌", "本报告涨跌配色：红=涨、绿=跌"),
    ("pp", "百分点：两个百分数之差（如 5%−3%=2pp）"),
]
TERM_DICT = {k: v for k, v in sorted(TERMS, key=lambda x: -len(x[0]))}
_TERM_PAT = re.compile("|".join(re.escape(k) for k in TERM_DICT.keys()))
_BLOCK_RE = re.compile(r"(<script[\s\S]*?</script>|<style[\s\S]*?</style>|<title[\s\S]*?</title>)", re.S)
_TAG_SPLIT_RE = re.compile(r"<[^>]+>")

def _annotate_text(text):
    def _repl(m):
        tip = TERM_DICT[m.group(0)].replace("'", "&#39;")
        return f"<span class='term' data-tip='{tip}'>{m.group(0)}</span>"
    return _TERM_PAT.sub(_repl, text)

def annotate_terms(html_str):
    parts = _BLOCK_RE.split(html_str)
    return "".join((_annotate_text(seg) if (i % 2 == 0 and seg) else (seg or "")) for i, seg in enumerate(parts))

html = annotate_terms(html)
with open(os.path.join(OUT_DIR, "相关性分析.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("written", os.path.join(OUT_DIR, "相关性分析.html"), len(html), "chars")
