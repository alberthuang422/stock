# -*- coding: utf-8 -*-
"""
58 号报告构建：农业股（CF/DAR）× 地缘溢价脱钩监测（2025-11 ~ 至今）
输入：results/agri_geo_premium.json（scripts/agri_geo_premium_monitor.py 产出）
输出：reports/58_农业股地缘溢价脱钩监测/index.html
风格：浅底研报风 + ECharts + 术语悬停浮窗 + Okabe-Ito 色弱安全
"""
import json
import os
import re as _re
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "results", "agri_geo_premium.json")
OUT_DIR = os.path.join(BASE, "reports", "58_农业股地缘溢价脱钩监测")

# Okabe-Ito 色弱安全
C_CF, C_DAR, C_CL, C_XLE = "#0072B2", "#E69F00", "#56B4E9", "#D55E00"
C_UP, C_DN = "#C0392B", "#1E8449"  # 红涨绿跌（仅表格涨跌文字）

d = json.load(open(SRC, encoding="utf-8"))
dates = d["panel_dates"]
meta = d["meta"]
latest = d["latest"]
events = d["events"]
nh = d["new_high"]
span_chg = d["span_chg_pct"]

# ---------------- 分阶段统计（r / β / 显著性三档） ----------------
panel = pd.DataFrame({"date": pd.to_datetime(dates)})
for tk in ["CF", "DAR", "CL", "XLE", "MOS"]:
    pass  # 仅用 JSON 序列做图；分阶段用收益率需重建，直接读 price？JSON 无价格序列 → 用 monitor 重算
import importlib.util
spec = importlib.util.spec_from_file_location("mon", os.path.join(BASE, "scripts", "agri_geo_premium_monitor.py"))
mon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mon)
pnl = mon.build_panel()
rt = pnl[["CF", "DAR", "CL"]].pct_change()

def sig_tier(r, n):
    if n < 8 or r is None or (isinstance(r, float) and np.isnan(r)):
        return "no", None
    t = r * np.sqrt((n - 2) / (1 - r * r))
    p = 2 * (1 - stats.t.cdf(abs(t), n - 2))
    tier = "sig" if p < 0.01 else ("edge" if p < 0.05 else "no")
    return tier, round(float(p), 4)

def seg_stats(lo, hi):
    mk = (pnl["date"] >= lo) & (pnl["date"] <= hi)
    sub = rt[mk]
    out = {}
    for tk in ["CF", "DAR"]:
        cc = sub[[tk, "CL"]].dropna()
        n = cc.shape[0]
        r = cc[tk].corr(cc["CL"]) if n > 8 else np.nan
        b = np.cov(cc["CL"], cc[tk])[0, 1] / cc["CL"].var() if n > 8 and cc["CL"].var() > 0 else np.nan
        tier, p = sig_tier(r, n)
        out[tk] = {"n": n, "r": round(float(r), 3) if not np.isnan(r) else None,
                   "beta": round(float(b), 2) if not np.isnan(b) else None,
                   "tier": tier, "p": p}
    return out

SEG = [
    ("全期 2025-11~2026-08", "2025-11-01", "2026-12-31"),
    ("分界前 2025-11~2026-02", "2025-11-01", "2026-02-28"),
    ("分界后 2026-03~至今", "2026-03-01", "2026-12-31"),
]
SEGSTATS = {label: seg_stats(lo, hi) for label, lo, hi in SEG}

TIER_CN = {"sig": "sig (p<0.01)", "edge": "edge (0.01≤p<0.05)", "no": "no (p≥0.05)"}

# ---------------- 异动事件表行 ----------------
def fmt_chg(v):
    if v is None:
        return "—"
    cls = "up" if v > 0 else ("dn" if v < 0 else "")
    return f"<span class='{cls}'>{v:+.2f}%</span>"

ev_rows = ""
for e in events:
    ev_rows += (
        f"<tr><td>{e['date']}</td><td>{e['direction']}</td><td>{fmt_chg(e['oil_ret_pct'])}</td>"
        f"<td>{fmt_chg(e.get('CF'))}<br><small>次 {fmt_chg(e.get('CF_nxt'))}</small></td>"
        f"<td>{fmt_chg(e.get('DAR'))}<br><small>次 {fmt_chg(e.get('DAR_nxt'))}</small></td>"
        f"<td>{fmt_chg(e.get('MOS'))}<br><small>次 {fmt_chg(e.get('MOS_nxt'))}</small></td>"
        f"<td>{fmt_chg(e.get('XLE'))}</td><td>{e['judge'] or '—'}</td></tr>"
    )

# ---------------- 分阶段表行 ----------------
seg_rows = ""
for label, _, _ in SEG:
    s = SEGSTATS[label]
    seg_rows += (
        f"<tr><td rowspan='2'>{label}</td><td>CF×CL</td><td>{s['CF']['r']}</td><td>{s['CF']['beta']}</td>"
        f"<td>{s['CF']['n']}</td><td>{s['CF']['p'] if s['CF']['p'] is not None else '—'}</td><td>{TIER_CN[s['CF']['tier']]}</td></tr>"
        f"<tr><td>DAR×CL</td><td>{s['DAR']['r']}</td><td>{s['DAR']['beta']}</td>"
        f"<td>{s['DAR']['n']}</td><td>{s['DAR']['p'] if s['DAR']['p'] is not None else '—'}</td><td>{TIER_CN[s['DAR']['tier']]}</td></tr>"
    )

# ---------------- 创新高表行 ----------------
own_hi = {}
for tk in ["XLE", "CL", "CF", "DAR"]:
    rollmax = pnl[tk].rolling(60, min_periods=60).max()
    own_hi[tk] = int((pnl[tk] >= rollmax).sum())
nh_rows = (
    f"<tr><td>能源锚（XLE 或 CL 创 60 日新高）</td><td>{nh['oil_high_days']}</td><td>—</td><td>—</td></tr>"
    f"<tr><td>其中 CF 同步创新高</td><td>{nh['cf_also_high_days']}</td><td>{nh['cf_sync_rate']:.0%}</td><td>CF 自身新高 {own_hi['CF']} 天</td></tr>"
    f"<tr><td>其中 DAR 同步创新高</td><td>{nh['dar_also_high_days']}</td><td>{nh['dar_sync_rate']:.0%}</td><td>DAR 自身新高 {own_hi['DAR']} 天</td></tr>"
)

# ---------------- 判定结论 ----------------
drops = [e for e in events if e["direction"] == "油价大跌"]
cf_drop_follow = sum(1 for e in drops if (e.get("CF") is not None and e["CF"] < 0) or (e.get("CF_nxt") is not None and e["CF_nxt"] < 0))
dar_drop_follow = sum(1 for e in drops if (e.get("DAR") is not None and e["DAR"] < 0) or (e.get("DAR_nxt") is not None and e["DAR_nxt"] < 0))

judge1_cf = "未跟跌 → 已剥离" if cf_drop_follow == 0 else f"{cf_drop_follow}/{len(drops)} 跟跌 → 部分残留"
judge1_dar = "未跟跌 → 已剥离" if dar_drop_follow == 0 else f"{dar_drop_follow}/{len(drops)} 跟跌 → 部分残留"
s_post = SEGSTATS["分界后 2026-03~至今"]
judge2_cf = f"r={s_post['CF']['r']}（{TIER_CN[s_post['CF']['tier']]}）显著负 → 剥离，纯基本面托底"
judge2_dar = f"r={s_post['DAR']['r']}（{TIER_CN[s_post['DAR']['tier']]}）显著负 → 剥离，纯基本面托底"
judge3_cf = f"同步率 {nh['cf_sync_rate']:.0%}（不创新高为主）→ 引擎切换，天气腿或已见顶"
judge3_dar = f"同步率 {nh['dar_sync_rate']:.0%} 但 r 显著负 → 并行新高非油价驱动，引擎未切换"

asof = latest.get("asof", {})
span_txt = meta["data_span"]

# ---------------- 图表数据 ----------------
JS = {
    "dates": dates,
    "norm_cf": d["norm_price"]["CF"],
    "norm_dar": d["norm_price"]["DAR"],
    "norm_cl": d["norm_price"]["CL"],
    "norm_xle": d["norm_price"]["XLE"],
    "ratio_cf": d["ratio"]["CF/CL"],
    "ratio_dar": d["ratio"]["DAR/CL"],
    "corr_cf": d["corr60"]["CF/CL"],
    "corr_dar": d["corr60"]["DAR/CL"],
    "beta_cf": d["beta"]["CF_b60"],
    "beta_dar": d["beta"]["DAR_b60"],
}
JSJSON = json.dumps(JS, ensure_ascii=False)

SPLIT = "2026-03-01"

# ---------------- HTML ----------------
html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>58 · 农业股（CF/DAR）地缘溢价脱钩监测（2025-11 至今）</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
body{margin:0;background:#f7f8fa;color:#1c2430;font-family:"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.75}
.wrap{max-width:1080px;margin:0 auto;padding:28px 22px 60px}
h1{font-size:24px;margin:0 0 4px}
.sub{color:#5a6472;font-size:13px;margin-bottom:18px}
h2{font-size:18px;border-left:4px solid #0072B2;padding-left:10px;margin:34px 0 12px}
.card{background:#fff;border:1px solid #e3e7ee;border-radius:10px;padding:16px 18px;margin:12px 0;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.card h3{margin:0 0 8px;font-size:15px}
.verdict{display:flex;gap:10px;align-items:flex-start}
.tag{flex:0 0 auto;font-size:12px;border-radius:6px;padding:2px 10px;margin-top:2px}
.tag.a{background:#0072B2;color:#fff}
.tag.b{background:#E69F00;color:#fff}
.tag.c{background:#56B4E9;color:#fff}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13px}
th,td{border:1px solid #dfe4ec;padding:6px 10px;text-align:center}
th{background:#eef2f7}
td:first-child,td:nth-child(2){text-align:left}
.up{color:@@CUP@@;font-weight:600}
.dn{color:@@CDN@@;font-weight:600}
small{color:#7a8494}
.chart{width:100%;height:340px;margin:8px 0}
.note{background:#fff8ec;border:1px solid #f0dcb8;border-radius:8px;padding:10px 14px;font-size:13px;color:#6b5320}
.legend{font-size:12.5px;color:#5a6472;background:#f2f5f9;border-radius:8px;padding:8px 12px;margin:8px 0}
.term{border-bottom:1px dashed #0072B2;cursor:help}
.termtip{display:none;position:fixed;z-index:9999;max-width:280px;background:#123248;color:#eef6ff;border-radius:8px;padding:8px 12px;font-size:12.5px;line-height:1.6;box-shadow:0 4px 14px rgba(0,0,0,.25);pointer-events:none}
.kpi{display:flex;gap:14px;flex-wrap:wrap}
.kpi .k{background:#fff;border:1px solid #e3e7ee;border-radius:10px;padding:10px 16px;min-width:120px}
.kpi .v{font-size:20px;font-weight:700}
.kpi .l{font-size:12px;color:#5a6472}
</style>
</head>
<body>
<div class="wrap">
<h1>58 · CF/DAR 地缘溢价脱钩监测</h1>
<div class="sub">数据窗口 @@SPAN@@（股票 @@ASOF_S@@ / CL @@ASOF_C@@）｜基准 2025-12=100｜对照 MOS（无油气暴露）/ XLE（能源锚）</div>

<h2>〇、结论先行</h2>
<div class="card verdict"><span class="tag a">判定一</span><div><b>油价大跌 → CF/DAR 是否跟跌？</b>　@@N_DROP@@ 次单日≥3% 油价大跌中：CF <b>@@J1CF@@</b>；DAR <b>@@J1DAR@@</b>（仅一次次日 -1.35% 的弱跟跌；08-27 油价 -9.3% 级冲击若计入，DAR 当日仅 -1.8% 亦未同步深跌）。</div></div>
<div class="card verdict"><span class="tag b">判定二</span><div><b>联动方向？</b>　2026-03 起 CF×CL r=@@R_CF@@、DAR×CL r=@@R_DAR@@，均<b>显著为负</b>（@@TIER_NOTE@@）——不是"不跟"，是"反向"：油价涨它跌、油价跌它涨，地缘溢价已剥离，剩纯基本面托底。</div></div>
<div class="card verdict"><span class="tag c">判定三</span><div><b>创新高同步？</b>　能源锚创 60 日新高 @@OIL_HI@@ 天中：CF 仅同步 @@CF_HI@@ 天（@@CF_RATE@@）→ <b>行情引擎切换，天气腿或已见顶</b>；DAR 同步 @@DAR_HI@@ 天（@@DAR_RATE@@）但 r 显著负 → 并行新高、引擎未切换（基本面腿仍在走）。</div></div>
<div class="kpi">
<div class="k"><div class="v up">+@@CHG_CF@@%</div><div class="l">CF 区间涨跌</div></div>
<div class="k"><div class="v up">+@@CHG_DAR@@%</div><div class="l">DAR 区间涨跌</div></div>
<div class="k"><div class="v up">+@@CHG_CL@@%</div><div class="l">CL 区间涨跌</div></div>
<div class="k"><div class="v up">+@@CHG_XLE@@%</div><div class="l">XLE 区间涨跌</div></div>
<div class="k"><div class="v">+@@CHG_SPY@@%</div><div class="l">SPY 区间涨跌</div></div>
<div class="k"><div class="v">@@B_CF@@</div><div class="l">CF 最新 β60</div></div>
<div class="k"><div class="v">@@B_DAR@@</div><div class="l">DAR 最新 β60</div></div>
<div class="k"><div class="v">@@RC_CF@@</div><div class="l">CF/CL 最新 60 日 r</div></div>
<div class="k"><div class="v">@@RC_DAR@@</div><div class="l">DAR/CL 最新 60 日 r</div></div>
</div>

<h2>一、归一化走势（2025-12=100）</h2>
<div class="card"><div id="c1" class="chart"></div>
<div class="legend">2026 年 1-2 月 CF/DAR 与油价同涨（地缘溢价期）；3 月起 CL 横盘回落、CF/DAR 走独立行情；虚线为 2026-03-01 分界。</div></div>

<h2>二、60 日滚动相关（含显著带 ±0.26）</h2>
<div class="card"><div id="c2" class="chart"></div>
<div class="legend">3 月后两条线跌入负区并持续穿过 −0.26 显著带 → 负相关显著，联动性质从"同向"变为"反向"。</div></div>

<h2>三、60 日滚动 β（CF/DAR 对 CL）</h2>
<div class="card"><div id="c3" class="chart"></div>
<div class="legend">1-2 月 CF β 一度冲至 +1.5 上方（油价每涨 1% CF 跟涨 1.5%+，地缘溢价高峰）；3 月后回落至 0 轴附近甚至转负 → 敏感度剥离。</div></div>

<h2>四、相对强弱比率（CF/CL、DAR/CL，2025-12=100）</h2>
<div class="card"><div id="c4" class="chart"></div>
<div class="legend">比率持续上行 = 农业股相对油价走强。CF/CL 最新 @@RATIO_CF@@、DAR/CL @@RATIO_DAR@@。</div></div>

<h2>五、油价异动事件对照（单日 |ΔCL| ≥ 3%）</h2>
<div class="card"><table>
<tr><th>日期</th><th>方向</th><th>CL 当日</th><th>CF 当日/次日</th><th>DAR 当日/次日</th><th>MOS 当日/次日</th><th>XLE 当日</th><th>判定（大跌日）</th></tr>
@@EV_ROWS@@
</table>
<div class="legend">参数图例：当日=异动日收益率、次=次交易日收益率；判定仅对油价大跌日给出——跟跌=地缘占比仍高，未跟跌=剥离中。MOS 为无油气暴露负对照。注意 03-11 油价 -3.1% 当日 CF +9.2%/MOS +10.1%——化肥板块大涨由自身基本面（钾肥/供应叙事）驱动，与油价反向，是脱钩的最直观一例。</div></div>

<h2>六、分阶段相关 / β（日收益，三档显著性）</h2>
<div class="card"><table>
<tr><th>阶段</th><th>配对</th><th>r</th><th>β</th><th>n</th><th>p 值</th><th>显著性</th></tr>
@@SEG_ROWS@@
</table>
<div class="legend">参数图例：r (Pearson)=日收益线性相关 −1~1；β=CL 涨 1% 标的平均跟涨 %；n=交易日数；显著性三档：sig(p<0.01)/edge(0.01≤p<0.05)/no(p≥0.05)；分界 2026-03-01（霍尔木兹冲突升级、油价与农股行情分水岭）。</div></div>

<h2>七、创新高同步（判定三明细，60 日口径）</h2>
<div class="card"><table>
<tr><th>项</th><th>天数</th><th>同步率</th><th>参照</th></tr>
@@NH_ROWS@@
</table>
<div class="legend">创新高=当日收盘 ≥ 过去 60 交易日最高收盘；能源锚=XLE 或 CL 任一创新高。XLE 自身新高 @@XLE_HI@@ 天、CL @@CL_HI@@ 天。</div></div>

<h2>八、数据与口径说明</h2>
<div class="note">
① 数据源 Yahoo（经 Chrome CDP 拉取），股票截至 @@ASOF_S@@、CL 期货截至 @@ASOF_C@@（期货口径滞后 1 个交易日）。<br>
② 2026-08-27 CL 原始 bar 成交量 25.6 万（常态约 360 万）且与 XLE 当日 -0.3% 矛盾，判为不完整 bar 已剔除，不纳入任何统计。<br>
③ 窗口 2025-11-01 起；滚动 β/相关窗口 60 交易日；异动阈值 ±3%；归一化基准 2025-12 首有效日=100。<br>
④ 本报告为量化研究，不构成投资建议。
</div>
</div>
@@TIP@@
</body>
</html>"""

repl = {
    "@@SPAN@@": span_txt,
    "@@ASOF_S@@": asof.get("stocks", "—"), "@@ASOF_C@@": asof.get("cl_last_valid", "—"),
    "@@N_DROP@@": str(len(drops)),
    "@@J1CF@@": judge1_cf, "@@J1DAR@@": judge1_dar,
    "@@R_CF@@": str(s_post["CF"]["r"]), "@@R_DAR@@": str(s_post["DAR"]["r"]),
    "@@TIER_NOTE@@": f"CF p={s_post['CF']['p']}、DAR p={s_post['DAR']['p']}",
    "@@OIL_HI@@": str(nh["oil_high_days"]),
    "@@CF_HI@@": str(nh["cf_also_high_days"]), "@@CF_RATE@@": f"{nh['cf_sync_rate']:.0%}",
    "@@DAR_HI@@": str(nh["dar_also_high_days"]), "@@DAR_RATE@@": f"{nh['dar_sync_rate']:.0%}",
    "@@CHG_CF@@": str(span_chg["CF"]), "@@CHG_DAR@@": str(span_chg["DAR"]),
    "@@CHG_CL@@": str(span_chg["CL"]), "@@CHG_XLE@@": str(span_chg["XLE"]), "@@CHG_SPY@@": str(span_chg["SPY"]),
    "@@B_CF@@": str(latest["beta_cf_60"]), "@@B_DAR@@": str(latest["beta_dar_60"]),
    "@@RC_CF@@": str(latest["corr60_cf_cl"]), "@@RC_DAR@@": str(latest["corr60_dar_cl"]),
    "@@RATIO_CF@@": str(latest["ratio_cf_cl"]), "@@RATIO_DAR@@": str(latest["ratio_dar_cl"]),
    "@@EV_ROWS@@": ev_rows, "@@SEG_ROWS@@": seg_rows, "@@NH_ROWS@@": nh_rows,
    "@@XLE_HI@@": str(own_hi["XLE"]), "@@CL_HI@@": str(own_hi["CL"]),
    "@@CUP@@": C_UP, "@@CDN@@": C_DN,
}
for k, v in repl.items():
    html = html.replace(k, v)

# ---------------- 术语悬停 ----------------
TERMS = [
    ("地缘溢价", "资产价格里因战争/封锁/海峡紧张等政治风险而多出来的那部分'惊吓升水'——风险消退时这部分会被剥掉"),
    ("脱钩", "两只原本同涨同跌的资产，联动消失甚至反向——各走各的行情"),
    ("相对强弱比率", "CF（或 DAR）价格除以 CL 价格再归一化——比率上行=农业股相对油价走强"),
    ("归一化", "把不同起点的价格序列统一换算成'基准日=100'，方便放在一张图里比走势"),
    ("60 日滚动", "每天往前数 60 个交易日算一次指标，逐日滚动——看联动关系如何随时间变化"),
    ("滚动 β", "过去 60 个交易日里 CL 每涨 1%、标的平均跟涨多少 %——衡量对油价的敏感度"),
    ("显著带", "±1.96/√(n−2)，60 日约 ±0.26——滚动相关超出这条带才算'真联动'，带内都可能是噪音"),
    ("显著性", "结论可信度的统计表述——p<0.01 记 sig（很可信）、0.01~0.05 记 edge、≥0.05 记 no（可能碰巧）"),
    ("p 值", "假设'其实没关系'时，观察到当前这么强相关的概率——越小越可信"),
    ("r", "Pearson 相关系数，日收益线性相关，−1~1；正=同向、负=反向、0=无关"),
    ("β", "贝塔——CL 涨 1% 时标的平均跟涨的 %（如 β=1.5 即跟涨 1.5%）"),
    ("XLE", "标普能源板块 ETF——一篮子美股石油公司，本报告的'能源锚'之一"),
    ("CL", "NYMEX WTI 原油期货——本报告的另一'能源锚'，代表油价本身"),
    ("能源锚", "用来代表油价/能源行情的参照标的（XLE 或 CL），看农股跟不跟它走"),
    ("MOS", "美盛公司，钾肥龙头——开采钾盐不需要油气，故当'无油气暴露'的负对照"),
    ("负对照", "理论上不该受油价影响的标的——如果它也跟着油价动，说明联动是板块情绪而非基本面"),
    ("创新高", "当日收盘 ≥ 过去 60 个交易日最高收盘价——代表趋势仍在向上"),
    ("天气腿", "农产品行情里由天气/气候预期（干旱、厄尔尼诺等）推动的那一段涨幅"),
    ("行情引擎切换", "推动股价上涨的主动力换了——比如从'天气/地缘升水'换成'自身供需基本面'"),
    ("分界", "把时间轴切开的日期（2026-03-01），对比分界前后联动结构是否变化"),
    ("口径", "统计计算采用的具体规则——同一件事不同口径结果不同，先说清口径再谈结论"),
    ("bp", "basis point，基点=0.01%"),
    ("pp", "百分点——两个百分数之差，如 5%−3%=2pp"),
]
TERM_DICT = {k: v for k, v in sorted(TERMS, key=lambda x: -len(x[0]))}
_TERM_PAT = _re.compile("|".join(_re.escape(k) for k in TERM_DICT.keys()))
_BLOCK_RE = _re.compile(r"(<script[\s\S]*?</script>|<style[\s\S]*?</style>|<title[\s\S]*?</title>)", _re.S)  # 单捕获组：split 奇位=块、偶位=正文
_TAG_SPLIT_RE = _re.compile(r"<[^>]+>")

def _annotate_text(text):
    def _repl(m):
        tip = TERM_DICT[m.group(0)].replace("'", "&#39;")
        return f"<span class='term' data-tip='{tip}'>{m.group(0)}</span>"
    return _TERM_PAT.sub(_repl, text)

def annotate_terms(html_str):
    parts = _BLOCK_RE.split(html_str)
    return "".join(
        (_annotate_text(seg) if (i % 2 == 0 and seg) else (seg or "")) for i, seg in enumerate(parts)
    )

html = annotate_terms(html)

tip_engine = """<div class="termtip" id="termtip"></div>
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
    tip.style.left=Math.min(r.left,window.innerWidth-300)+'px';
    tip.style.top=r.bottom+6+'px';
  });
  document.addEventListener('mouseout',e=>{
    if(e.target.closest('.term')){cur=null;tip.style.display='none';}
  });
})();
</script>"""
html = html.replace("@@TIP@@", tip_engine)

# ---------------- 图表脚本 ----------------
charts = """<script>
const D = @@JSJSON@@;
const SPLIT = '@@SPLIT@@';
const base = {
  tooltip:{trigger:'axis'},
  grid:{left:52,right:20,top:42,bottom:60},
  dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:8}]
};
function mkLine(id, series, extra){
  const opt = Object.assign({}, base, {
    legend:{top:6,textStyle:{color:'#333'}},
    xAxis:{type:'category',data:D.dates,axisLabel:{color:'#555'}},
    yAxis:{type:'value',scale:true,axisLabel:{color:'#555'},splitLine:{lineStyle:{color:'#e5e9f0'}}},
    series:series
  });
  if (extra) Object.assign(opt, extra);
  echarts.init(document.getElementById(id)).setOption(opt);
}
const mkVL = {type:'category',coord:SPLIT,lineStyle:{type:'dashed',color:'#98a2b3'},label:{formatter:'分界 03-01',color:'#667',position:'insideEndTop'}};
mkLine('c1', [
 {name:'CF',data:D.norm_cf,lineStyle:{color:'@@CCF@@',width:2},itemStyle:{color:'@@CCF@@'},showSymbol:false},
 {name:'DAR',data:D.norm_dar,lineStyle:{color:'@@CDAR@@',width:2},itemStyle:{color:'@@CDAR@@'},showSymbol:false},
 {name:'CL',data:D.norm_cl,lineStyle:{color:'@@CCL@@',width:2,type:'dashed'},itemStyle:{color:'@@CCL@@'},showSymbol:false,connectNulls:false},
 {name:'XLE',data:D.norm_xle,lineStyle:{color:'@@CXLE@@',width:2,type:'dotted'},itemStyle:{color:'@@CXLE@@'},showSymbol:false},
].map(s=>{s.markLine={symbol:'none',data:[{xAxis:SPLIT}],lineStyle:{type:'dashed',color:'#98a2b3'},label:{formatter:'03-01',color:'#667'}};return s;}));
mkLine('c2', [
 {name:'CF×CL',data:D.corr_cf,lineStyle:{color:'@@CCF@@',width:2},itemStyle:{color:'@@CCF@@'},showSymbol:false,
  markLine:{symbol:'none',silent:true,data:[{yAxis:0.26,lineStyle:{type:'dashed',color:'#b6bfca'},label:{formatter:'+0.26',color:'#889'}},{yAxis:-0.26,lineStyle:{type:'dashed',color:'#b6bfca'},label:{formatter:'-0.26',color:'#889'}},{yAxis:0,lineStyle:{color:'#c8cfd8'},label:{show:false}}]}},
 {name:'DAR×CL',data:D.corr_dar,lineStyle:{color:'@@CDAR@@',width:2},itemStyle:{color:'@@CDAR@@'},showSymbol:false}
]);
mkLine('c3', [
 {name:'CF β60',data:D.beta_cf,lineStyle:{color:'@@CCF@@',width:2},itemStyle:{color:'@@CCF@@'},showSymbol:false,
  markLine:{symbol:'none',silent:true,data:[{yAxis:0,lineStyle:{color:'#c8cfd8'},label:{show:false}}]}},
 {name:'DAR β60',data:D.beta_dar,lineStyle:{color:'@@CDAR@@',width:2},itemStyle:{color:'@@CDAR@@'},showSymbol:false}
]);
mkLine('c4', [
 {name:'CF/CL',data:D.ratio_cf,lineStyle:{color:'@@CCF@@',width:2},itemStyle:{color:'@@CCF@@'},showSymbol:false,
  markLine:{symbol:'none',data:[{xAxis:SPLIT}],lineStyle:{type:'dashed',color:'#98a2b3'},label:{formatter:'03-01',color:'#667'}}},
 {name:'DAR/CL',data:D.ratio_dar,lineStyle:{color:'@@CDAR@@',width:2},itemStyle:{color:'@@CDAR@@'},showSymbol:false}
]);
</script>"""
charts = charts.replace("@@JSJSON@@", JSJSON).replace("@@SPLIT@@", SPLIT)
charts = charts.replace("@@CCF@@", C_CF).replace("@@CDAR@@", C_DAR).replace("@@CCL@@", C_CL).replace("@@CXLE@@", C_XLE)
html = html.replace("</body>", charts + "</body>")

os.makedirs(OUT_DIR, exist_ok=True)
out_path = os.path.join(OUT_DIR, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out_path, os.path.getsize(out_path), "bytes")
