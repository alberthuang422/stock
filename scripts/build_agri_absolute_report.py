# -*- coding: utf-8 -*-
"""
Build 57 附 · 绝对收益版：农业股 × ENSO + 利率敏感性（绝对口径，不减 SPY）
读 results/agri_absolute.json → 生成 reports/57_农业股ENSO与利率敏感性/绝对收益版.html
风格与主报告（index.html）一致：浅底研报 + ECharts + 术语悬停 + 红涨绿跌。
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
OUT_DIR = os.path.join(BASE, "reports", "57_农业股ENSO与利率敏感性")
os.makedirs(OUT_DIR, exist_ok=True)

d = json.load(open(os.path.join(RES, "agri_absolute.json"), encoding="utf-8"))

SUB = d["subsector"]
TICKERS = ["DE", "AGCO", "MOS", "CF", "NTR", "CTVA", "FMC", "ADM", "BG",
           "DAR", "FPI", "TSN", "HRL", "MOO", "DBA"]

def mk_table(cols, rows, note=None):
    head = "".join(f"<th>{c}</th>" for c, _ in cols)
    body = []
    for r in rows:
        tds = []
        for _, key in cols:
            v = r.get(key, "-")
            cls = ""
            if isinstance(v, str) and v.startswith(("+", "-", "−")):
                try:
                    cls = "up" if float(v) >= 0 else "down"
                except ValueError:
                    pass
            tds.append(f"<td class='{cls}'>{v}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    note_html = f"<div class='note'>{note}</div>" if note else ""
    return f"<table><tr>{head}</tr>{''.join(body)}</table>{note_html}"

SIGTAG = {"sig": "<span class='tag sig'>sig</span>",
          "edge": "<span class='tag edge'>edge</span>", "no": ""}

# ---------- 表1：ENSO 分组绝对月均（含 SPY） ----------
g = d["group_abs"]
rows1 = []
for t in TICKERS + ["SPY"]:
    def fmt(x):
        if x.get("mean") is None:
            return "-"
        tag = SIGTAG.get(x.get("sig", ""), "")
        return (f"{x['mean']:+.2f}%"
                f"<span class='note-in'>(n={x['n']}, p={x['p']:.3f})</span>{tag}")
    rows1.append({"t": t, "sub": SUB.get(t, "基准"), "el": fmt(g[t]["el"]),
                  "la": fmt(g[t]["la"]), "neu": fmt(g[t]["neu"])})

# ---------- 表2：拉尼娜 T+12 绝对 ----------
la = d["la_abs12"]
rows2 = []
for t in TICKERS + ["SPY"]:
    v = la[t]
    if not v or v.get("n", 0) == 0:
        rows2.append({"t": t, "sub": SUB.get(t, "基准"), "n": 0, "mean": "-", "med": "-", "win": "-"})
        continue
    rows2.append({"t": t, "sub": SUB.get(t, "基准"), "n": v["n"],
                  "mean": f"{v['mean']:+.1f}%", "med": f"{v['med']:+.1f}%", "win": f"{v['win']:.0f}%"})
rows2.sort(key=lambda x: -(x["n"] if isinstance(x["n"], int) else 0))

# ---------- 表3：厄尔尼诺 T+6/12/24 绝对 ----------
el = d["el_abs"]
def el_rows(w):
    rows = []
    for t in TICKERS + ["SPY"]:
        v = el[f"r{w}"][t]
        if not v or v.get("n", 0) == 0:
            rows.append({"t": t, "n": 0, "mean": "-", "med": "-", "win": "-"})
            continue
        rows.append({"t": t, "n": v["n"], "mean": f"{v['mean']:+.1f}%",
                     "med": f"{v['med']:+.1f}%", "win": f"{v['win']:.0f}%"})
    return rows

# ---------- 表4：三档绝对路径（pooled 排除 SPY + SPY 单列行） ----------
DD_TOL = d["meta"]["dd_tol_pp"]
def pooled_stats(tier, tickers):
    rows = []
    for ev in d["events_detail_abs"]:
        if ev["tier"] != tier:
            continue
        for t, v in ev["tickers"].items():
            if t in tickers:
                rows.append(v)
    if not rows:
        return None
    import numpy as np
    return {"n": len(rows),
            "med_max": round(float(np.median([x["max"] for x in rows])), 1),
            "avg_max": round(float(np.mean([x["max"] for x in rows])), 1),
            "med_end": round(float(np.median([x["end"] for x in rows])), 1),
            "avg_end": round(float(np.mean([x["end"] for x in rows])), 1),
            "avg_dd": round(float(np.mean([x["dd"] for x in rows])), 1),
            "avg_peak_t": round(float(np.mean([x["peak_t"] for x in rows])), 1),
            "avg_dd_start": round(float(np.mean([x["dd_start_t"] for x in rows if x["dd_start_t"]])), 1)
            if any(x["dd_start_t"] for x in rows) else None,
            "n_updown_pct": round(float(np.mean([x["max"] > 0 and x["end"] < 0 for x in rows])) * 100, 0),
            "n_alldown_pct": round(float(np.mean([x["max"] <= 0 for x in rows])) * 100, 0)}

TIER_ORDER = [("weak", "弱(<+1.5°)"), ("strong", "强(1.5~2.0°)"), ("vstrong", "超强(≥2.0°)")]
tier_meta = {tr: d["tier_path_abs"][tr] for tr, _ in TIER_ORDER}
tier_rows = []
for tr, cn in TIER_ORDER:
    st = pooled_stats(tier_meta[tr]["tier_cn"], set(TICKERS))
    spy = d["by_ticker_tier_abs"]["SPY"][tr]
    tier_rows.append({
        "tier": cn, "ev": f"{tier_meta[tr]['n_ev']} 次",
        "n": st["n"], "mx": f"{st['med_max']:+.1f}", "end": f"{st['med_end']:+.1f}",
        "mxavg": f"{st['avg_max']:+.1f}", "endavg": f"{st['avg_end']:+.1f}",
        "dd": f"{st['avg_dd']:.1f}",
        "pt": f"T+{st['avg_peak_t']:.0f}",
        "ds": f"T+{st['avg_dd_start']:.0f}" if st["avg_dd_start"] else "未跌破",
        "ud": f"{st['n_updown_pct']:.0f}%", "al": f"{st['n_alldown_pct']:.0f}%",
        "spy_end": f"{spy['med_end']:+.1f}" if spy.get("n") and "med_end" in spy else "-",
    })

# 事件 × 标的明细（绝对）
TIER_CN = {v["tier_cn"]: k for k, v in tier_meta.items()}
CN2SHORT = {"weak": "弱", "strong": "强", "vstrong": "超强"}
det_rows = []
for ev in d["events_detail_abs"]:
    key = TIER_CN[ev["tier"]]
    for t, v in ev["tickers"].items():
        if t == "SPY":
            continue
        det_rows.append({
            "ev": ev["onset"], "tr": CN2SHORT[key], "oni": ev["oni_peak"], "t": t, "sub": SUB[t],
            "mx": f"{v['max']:+.1f}", "pt": f"T+{v['peak_t']}",
            "ds": f"T+{v['dd_start_t']}" if v["dd_start_t"] else "未跌破",
            "end12": f"{v['end12']:+.1f}" if v["end12"] is not None else "-",
            "end": f"{v['end']:+.1f}",
        })
_torder = {"超强": 0, "强": 1, "弱": 2}
det_rows.sort(key=lambda x: (_torder[x["tr"]], x["ev"], x["t"]))

# ---------- 表5：利率分组绝对 ----------
r = d["rate_abs"]
rows5 = []
for t in TICKERS + ["SPY"]:
    def gv(k, field):
        v = r[t][k]
        return v[field] if v else "-"
    rows5.append({"t": t, "sub": SUB.get(t, "基准"),
                  "un": gv("up", "n"), "um": f"{gv('up','mean'):+.2f}%" if gv("up", "mean") != "-" else "-",
                  "uw": f"{gv('up','win'):.0f}%" if gv("up", "win") != "-" else "-",
                  "dn": gv("dn", "n"), "dm": f"{gv('dn','mean'):+.2f}%" if gv("dn", "mean") != "-" else "-",
                  "dw": f"{gv('dn','win'):.0f}%" if gv("dn", "win") != "-" else "-",
                  "fm": gv("flat", "n")})

# ---------- 图表数据 ----------
c1_data = [{"t": t, "v": la[t]["mean"], "n": la[t]["n"]} for t in TICKERS]
spy_la = la["SPY"]
c2_data = []
for tr, cn in TIER_ORDER:
    st = pooled_stats(tier_meta[tr]["tier_cn"], set(TICKERS))
    c2_data.append({"tier": cn, "mx": st["med_max"], "end": st["med_end"], "pt": st["avg_peak_t"]})
c3_data = [{"t": t, "u": r[t]["up"]["mean"] if r[t]["up"] else None,
            "dn": r[t]["dn"]["mean"] if r[t]["dn"] else None} for t in TICKERS]

ev_count = f"{d['meta']['n_el']}"
la_count = d["meta"]["n_la_1990"]

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>57 附 · 农业股 ENSO + 利率敏感性（绝对收益版）</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
:root{{--bg:#ffffff;--fg:#1a1a1a;--muted:#666;--line:#e5e5e5;--accent:#185FA5;--red:#D55E00;--green:#009E73;--card:#f7f8fa;--okb:#0072B2;--okc:#E69F00;--okr:#D55E00;--okg:#009E73;--okp:#CC79A7}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--fg);line-height:1.7;padding:32px 20px 60px}}
.wrap{{max-width:1100px;margin:0 auto}}
h1{{font-size:26px;font-weight:700;letter-spacing:.5px;margin-bottom:6px}}
.sub{{color:var(--muted);font-size:13px;margin-bottom:22px}}
h2{{font-size:20px;font-weight:600;margin:38px 0 14px;padding-left:12px;border-left:4px solid var(--accent)}}
h3{{font-size:16px;font-weight:600;margin:22px 0 10px}}
h4{{font-size:14px;font-weight:600;margin:16px 0 6px;color:#333}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right}}
th:first-child,td:first-child{{text-align:left}}
th{{background:#f0f1f3;font-weight:600;white-space:nowrap}}
.up{{color:var(--red);font-weight:600}}.down{{color:var(--green);font-weight:600}}
.tag{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;margin-left:4px}}
.sig{{background:#fde8e8;color:#A32D2D}}.edge{{background:#fdf3e0;color:#854F0B}}.no{{background:#eef0f2;color:#666}}
.chart{{width:100%;height:380px;margin:14px 0}}
.note{{font-size:12px;color:var(--muted);margin:6px 0 2px}}
.note-in{{font-size:11px;color:var(--muted)}}
.exec{{background:#fffbea;border:1px solid #f0dca0;border-radius:10px;padding:16px 20px;margin:16px 0}}
.exec li{{margin:6px 0}}
.legend{{font-size:12px;color:var(--muted);margin-top:8px}}
.warn{{background:#fdf2f2;border:1px solid #f0c8c8;border-radius:8px;padding:12px 16px;font-size:13px;margin-top:10px}}
.foot{{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}}
.collapse{{max-height:560px;overflow-y:auto;border:1px solid var(--line);border-radius:8px}}
.filterbar{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:10px 0;font-size:13px;display:flex;flex-wrap:wrap;gap:16px;align-items:center}}
.filterbar label{{display:inline-flex;align-items:center;gap:6px;color:#444}}
.filterbar select{{padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;font-size:13px;cursor:pointer}}
.filterbar .fcount{{color:var(--muted);font-size:12px}}
.fmore{{text-align:left;color:var(--muted);font-style:italic}}
.term{{border-bottom:1px dashed #7aa5d9;cursor:help;transition:background .15s}}
.term:hover{{background:#e8f1fc;color:#185FA5}}
.termtip{{display:none;position:fixed;z-index:9999;max-width:280px;background:#123248;color:#eef6ff;border-radius:8px;padding:8px 12px;font-size:12.5px;line-height:1.6;box-shadow:0 4px 14px rgba(0,0,0,.25);pointer-events:none}}
</style>
</head>
<body><div class="wrap">

<h1>农业股 × 厄尔尼诺 + 利率敏感性 · 绝对收益版</h1>
<div class="sub">报告 57 附 ｜ 2026-08-30 ｜ 口径：<b>绝对收益</b>（不减 SPY）｜ 主报告（超额口径）见同目录 index.html ｜ 数据源同主报告</div>

<div class="exec">
<b>一页结论（绝对口径）</b>
<ul>
<li><b>拉尼娜信号在绝对口径下更强、且通过严格显著性检验</b>：拉尼娜 onset 后 T+12 绝对收益 CF 平均 <b>+77.1%</b>（中位 +43.7%，{la_count} 次中 8 次可算、8/8 全胜）、NTR +62.8%、MOS +43.3%、CTVA +48.5%，同期 SPY 仅 +8.1%——化肥链的拉尼娜行情不是"靠大盘抬轿"，自身就有独立alpha。</li>
<li><b>重要更正（p 值 bug）</b>：主报告 t 检验用手写数值积分算 p 值，45 个组合中 42 个明显算错。scipy 重算后：<b>拉尼娜期 CF 月均 +5.79%（p=0.0006，sig）、BG +3.51%（p=0.004，sig）显著异于零</b>——原"拉尼娜化肥信号"结论不仅成立，统计置信度更高；厄尔尼诺期仍全部不显著（CF p=0.83），"厄尔尼诺不是月频信号"坐实。</li>
<li><b>厄尔尼诺窗口绝对收益：多数标的仍为正，但只是"跟大盘"</b>：T+12 绝对 DE +19.9%（胜率 73%）vs SPY +15.9%，温和正超额结论不变；CF/MOS 均值为正（+43.5%/+9.6%）但中位数转负（−9.3%/−1.5%）且胜率仅 33%/36%——少数极端事件拉高均值。</li>
<li><b>"越强越弱"在绝对口径下依然单调，但惨烈程度大幅缩水</b>：T+24 中位期末收益 弱档 +35.5% → 强档 +21.6% → 超强档 −3.4%（15 只农业标的 pooled，不含 SPY）；超强档是唯一转负档，冲高后转负占比 57%。对照超额口径（+4.7 / −23.4 / −40.7pp）可知：<b>超额口径把"大盘同期大涨"计入为损失，绝对口径显示强厄尔尼诺的真实伤害是"少赚"而非"绝对亏损"，只有超强档真正亏钱</b>。</li>
<li><b>利率上行月绝对收益差距更直观</b>：CF 上行月均 +4.33%/月（胜率 63%）vs SPY +1.04%、DAR +3.56%、AGCO +2.77%、MOS +1.87%；下行月普遍归零或转负（MOS −0.63%、AGCO −0.31%）——化肥/农机/油脂的利率顺风在绝对口径下看得更清楚。</li>
<li><b>操作含义（与主报告一致、加一条）</b>：拉尼娜化肥链多头交易的绝对空间（历史 T+12 +40~77%）远大于主报告超额口径给出的 +35~68pp 印象；强厄尔尼诺期做防守的紧迫性按档位递增——超强档减仓、强档降杠杆、弱档不必恐慌。</li>
</ul>
</div>

<h2>一、ENSO 状态分组：绝对月均收益</h2>
{mk_table([("标的", "t"), ("子行业", "sub"), ("厄尔尼诺月均", "el"), ("拉尼娜月均", "la"), ("中性月均", "neu")], rows1,
          note="月度绝对收益（adj_close 月末复权，%），t 检验 vs 0（scipy，双侧）。sig=p&lt;0.01、edge=p&lt;0.05。本表已修正主报告的手写 t 分布 p 值 bug。拉尼娜列 CF/BG 显著为正、MOS/ADM/DE 边缘以上；厄尔尼诺列全部不显著（HRL/SPY 边缘）。SPY 拉尼娜期月均仅 +0.62%——农业股拉尼娜行情与大盘无关。")}
<div class="card">
<p><b>解读</b>：绝对口径下分组结构更清晰——<b>拉尼娜月化肥（CF +5.79%、MOS +3.12%、NTR +3.04%）与粮商（BG +3.51%）自身就有显著正收益</b>，而同期 SPY 只 +0.62%（不显著）；厄尔尼诺月所有农业标的都接近零，唯一例外 HRL（+1.28%，edge）是防御属性而非 ENSO 信号。</p>
</div>

<h2>二、拉尼娜事件窗口：绝对收益（重点）</h2>
{mk_table([("标的", "t"), ("子行业", "sub"), ("n(事件)", "n"), ("T+12 绝对均值", "mean"), ("中位数", "med"), ("正收益占比", "win")], rows2,
          note=f"onset 起 12 个月复利累计绝对收益（%），样本=1990 年后 {la_count} 次拉尼娜中数据可得者。'正收益占比'=绝对收益&gt;0 的事件占比。CF 8/8 全胜且均值 +77.1%；TSN 均值仅 +0.8%、中位数转负——饲料成本逻辑在绝对口径下同样成立。SPY 行为大盘参照。")}
<div class="chart" id="c1"></div>
<div class="legend">拉尼娜 onset 后 T+12 平均绝对收益（%，{la_count} 次事件）｜ 虚线 = SPY 同期均值 +8.1% ｜ 红=高于 SPY、绿=低于。化肥链（CF/MOS/NTR/CTVA）断层领先。</div>

<h2>三、厄尔尼诺事件窗口：绝对收益</h2>
<h4>T+6（onset 后 6 个月）</h4>
{mk_table([("标的", "t"), ("n", "n"), ("绝对均值", "mean"), ("中位数", "med"), ("正收益占比", "win")], el_rows(6))}
<h4>T+12</h4>
{mk_table([("标的", "t"), ("n", "n"), ("绝对均值", "mean"), ("中位数", "med"), ("正收益占比", "win")], el_rows(12))}
<h4>T+24</h4>
{mk_table([("标的", "t"), ("n", "n"), ("绝对均值", "mean"), ("中位数", "med"), ("正收益占比", "win")], el_rows(24))}
<div class="warn">
<b>与超额口径的差异</b>：厄尔尼诺窗口内大盘多为牛市（SPY T+12 绝对均值 +15.9%、胜率 90%），所以超额口径下"转负"的标的（如 MOS 中位 −1.5%）在绝对口径下多数只是"持平或少赚"。DE 是唯一绝对/超额双口径都稳健的（T+12 +19.9%、T+24 中位数 +30.9%、胜率 73%/77%）。
</div>

<h2>四、强厄尔尼诺三档：绝对路径四指标</h2>
<div class="card">
<p><b>口径</b>：onset 起 T+24 逐月复利<b>绝对</b>累计收益路径（不减 SPY），分档同主报告（峰值 ONI 弱 &lt;+1.5 / 强 1.5~2.0 / 超强 ≥2.0）。四指标定义同主报告：最大值=窗口内峰值；期末=T+24；见顶 T+；回撤起始=见顶后跌破峰值−{DD_TOL:.0f}pp 的月份。表中 SPY 期末列 = SPY 同档事件 T+24 绝对期末均值，用于对照"少赚了多少"。</p>
</div>
{mk_table([("分档", "tier"), ("事件数", "ev"), ("样本", "n"), ("中位最大", "mx"), ("中位期末", "end"),
           ("平均最大", "mxavg"), ("平均期末", "endavg"), ("平均回撤", "dd"),
           ("平均见顶T+", "pt"), ("回撤起始T+", "ds"), ("冲高转负", "ud"), ("全程阴跌", "al"), ("SPY期末", "spy_end")], tier_rows,
          note="农业 15 只 pooled（不含 SPY）。中位口径抗极端值。三档单调成立：强度↑ → 峰值↓、期末↓、见顶提前。弱档中位期末 +35.5% 大幅高于其超额口径 +4.7pp——弱厄尔尼诺多落在牛市，主报告的'弱档也没怎么跑赢'实为'绝对大赚但与大盘同步'。超强档期末 −3.4% 是唯一绝对亏损档。")}

<div class="chart" id="c2"></div>
<div class="legend">三档厄尔尼诺 T+24 窗口：中位最大绝对收益（蓝）vs 中位期末绝对收益（橙，%）＋ 平均见顶 T+N（紫点，右轴）｜ 超强档期末转负、见顶最早。</div>

<h4>事件 × 标的 明细（可筛选）</h4>
<div class="filterbar">
  <label>强度档：<select id="f_tier"><option value="all">全部</option></select></label>
  <label>股票：<select id="f_tkr"><option value="all">全部</option></select></label>
  <label>显示 <select id="f_rows"><option value="20">20</option><option value="50">50</option><option value="all" selected>全部</option></select> 行</label>
  <span class="fcount" id="f_count"></span>
</div>
<div class="collapse">
<table id="det_tbl">
<thead><tr><th>事件</th><th>档</th><th>峰值ONI</th><th>标的</th><th>子行业</th><th>最大</th><th>见顶T+</th><th>回撤起始</th><th>T+12期末</th><th>T+24期末</th></tr></thead>
<tbody></tbody>
</table>
</div>
<div class="note">数值均为绝对累计收益（%）。'未跌破'=窗口内未跌破峰值−{DD_TOL:.0f}pp。</div>

<h2>五、利率上行/下行月：绝对收益</h2>
{mk_table([("标的", "t"), ("子行业", "sub"), ("上行月n", "un"), ("上行月均", "um"), ("胜率", "uw"),
           ("下行月n", "dn"), ("下行月均", "dm"), ("胜率", "dw"), ("平坦月n", "fm")], rows5,
          note="US10Y 月变动 &gt;+5bp 为上行月、&lt;−5bp 为下行月（口径同主报告）。绝对月收益（%）。CF 上行月 +4.33% vs SPY +1.04%，利率顺风在绝对口径下更直观；但注意上行月本身是风险偏好较高的月份，绝对收益高部分来自市场环境。")}

<div class="chart" id="c3"></div>
<div class="legend">US10Y 上行月（红）vs 下行月（绿）平均绝对月收益（%）。化肥/农机/油脂上行月明显占优、下行月归零——方向与主报告 β₁₀ 一致。</div>

<h2>六、口径对比速览：绝对 vs 超额</h2>
{mk_table([("关键指标", "k"), ("超额口径(主报告)", "ex"), ("绝对口径(本报告)", "ab"), ("差异解读", "why")], [
    {"k": "拉尼娜 CF T+12", "ex": "+67.5pp（8/8 胜）", "ab": "+77.1%（8/8 胜）",
     "why": "同向且更强：拉尼娜窗口 SPY 仅 +8.1%，化肥行情是自身独立行情"},
    {"k": "拉尼娜期 CF 月均", "ex": "+5.2pp/月（p 值 bug 未检出）", "ab": "+5.79%/月（p=0.0006 sig）",
     "why": "修正检验后显著性成立，月频信号比主报告更可信"},
    {"k": "弱厄尔尼诺 中位期末", "ex": "+4.7pp", "ab": "+35.5%",
     "why": "弱档事件多落牛市：绝对大赚、与大盘同步——超额口径低估了绝对回报"},
    {"k": "强厄尔尼诺 中位期末", "ex": "−23.4pp", "ab": "+21.6%",
     "why": "强档真实伤害是'少赚'（SPY 同期 +37% 量级），非绝对亏损"},
    {"k": "超强厄尔尼诺 中位期末", "ex": "−40.7pp", "ab": "−3.4%",
     "why": "唯一绝对亏损档：减仓信号只在超强档成立，且幅度远小于超额口径观感"},
    {"k": "CF 利率上行月", "ex": "+3.4pp", "ab": "+4.33%/月",
     "why": "方向一致；绝对口径需注意上行月本身多为风险偏好扩张期"},
], note="两口径结合使用：超额口径回答'该不该持有农业股而非大盘'，绝对口径回答'这个交易本身能赚多少、最大回撤多深'。")}

<h2>七、风险与局限</h2>
<div class="warn">
<ul>
<li><b>事件样本小</b>：拉尼娜 CF n=8、NTR/CTVA n=2；超强档仅 3 次事件（1982/1997/2014）。均值易被单事件拉高（CF T+12 均值 +77.1% 受 2020-22 化肥超级周期影响大，中位数 +43.7% 更具代表性）。</li>
<li><b>大盘环境混入</b>：绝对口径不剔除大盘 beta——弱/强档的"正期末"主要来自 1990s-2000s 牛市环境，不能线性外推到熊市中的厄尔尼诺事件。</li>
<li><b>p 值修正影响主报告</b>：主报告 index.html 的分组 p 值列仍为旧 bug 版本（42/45 组合有误），本表为正确版本；主报告结论方向均不变，仅"拉尼娜月频信号"的显著性从"未检出"变为"显著"。</li>
<li>本报告为历史统计推演，不构成投资建议。投资有风险，决策需谨慎。</li>
</ul>
</div>

<div class="foot">
报告 57 附（绝对收益版）· 生成于 2026-08-30 · 参数图例：绝对收益=不复权扣减 SPY 的复利累计（%）；正收益占比=绝对收益&gt;0 事件占比；sig=双侧 p&lt;0.01、edge=p&lt;0.05（scipy t 检验 vs 0）；其余定义同主报告。
</div>

</div>
<script>
const C1 = {json.dumps(c1_data)};
const C2 = {json.dumps(c2_data)};
const C3 = {json.dumps(c3_data)};
const DET = {json.dumps(det_rows)};
const OKB='#0072B2', OKR='#D55E00', OKG='#009E73', OKC='#E69F00', OKP='#CC79A7', MUT='#888';

// 图1 拉尼娜 T+12 绝对
(function(){{
const el=document.getElementById('c1');
const spyThresh=8.1;
echarts.init(el).setOption({{
  grid:{{left:56,right:20,top:34,bottom:64}},
  tooltip:{{formatter:p=>{{const x=C1[p[0].dataIndex];return `${{x.t}}<br>T+12 平均绝对收益：${{x.v>0?'+':''}}${{x.v}}%（${{x.n}} 次事件）`;}}}},
  xAxis:{{type:'category',data:C1.map(x=>x.t),axisLabel:{{rotate:35,fontSize:11}},axisTick:{{show:false}}}},
  yAxis:{{type:'value',name:'T+12 绝对收益 %',splitLine:{{lineStyle:{{color:'#eee'}}}}}},
  series:[{{type:'bar',data:C1.map(x=>({{value:x.v,itemStyle:{{color:x.v>=spyThresh?OKR:OKG,borderRadius:[3,3,0,0]}},
    label:{{show:true,position:'top',fontSize:10,color:MUT,formatter:p=>(p.value>0?'+':'')+p.value.toFixed(0)}}}})),barWidth:'55%',
    markLine:{{silent:true,symbol:'none',lineStyle:{{color:MUT,type:'dashed'}},
      label:{{formatter:'SPY +8.1%',color:MUT,fontSize:11}},data:[{{yAxis:8.1}}]}}}}]
}});
}})();

// 图2 三档绝对路径
(function(){{
const el=document.getElementById('c2');
const d=C2;
echarts.init(el).setOption({{
  grid:{{left:56,right:56,top:40,bottom:30}},
  tooltip:{{trigger:'item'}},
  legend:{{data:['中位最大 (%)','中位期末 (%)','平均见顶 T+N (右)'],textStyle:{{color:MUT,fontSize:11}}}},
  xAxis:{{type:'category',data:d.map(x=>x.tier),axisLabel:{{fontSize:12}},axisTick:{{show:false}}}},
  yAxis:[
    {{type:'value',name:'绝对收益 %',splitLine:{{lineStyle:{{color:'#eee'}}}}}},
    {{type:'value',name:'见顶 T+月',min:0,max:24,splitLine:{{show:false}}}}
  ],
  series:[
    {{name:'中位最大 (%)',type:'bar',data:d.map(x=>x.mx),itemStyle:{{color:OKB}},barWidth:'26%'}},
    {{name:'中位期末 (%)',type:'bar',data:d.map(x=>x.end),itemStyle:{{color:x=>x>=0?OKC:'#999'}},barWidth:'26%'}},
    {{name:'平均见顶 T+N (右)',type:'line',yAxisIndex:1,data:d.map(x=>x.pt),itemStyle:{{color:OKP}},lineStyle:{{width:2,color:OKP}},symbolSize:8}}
  ]
}});
}})();

// 图3 利率上行/下行月绝对
(function(){{
const el=document.getElementById('c3');
echarts.init(el).setOption({{
  grid:{{left:52,right:16,top:34,bottom:64}},
  tooltip:{{trigger:'axis',valueFormatter:v=>v==null?'-':v.toFixed(2)+'%'}},
  legend:{{data:['US10Y 上行月','US10Y 下行月'],textStyle:{{color:MUT,fontSize:11}}}},
  xAxis:{{type:'category',data:C3.map(x=>x.t),axisLabel:{{rotate:35,fontSize:11}},axisTick:{{show:false}}}},
  yAxis:{{type:'value',name:'绝对月均 %',splitLine:{{lineStyle:{{color:'#eee'}}}}}},
  series:[
    {{name:'US10Y 上行月',type:'bar',data:C3.map(x=>x.u),itemStyle:{{color:OKR}},barWidth:'32%'}},
    {{name:'US10Y 下行月',type:'bar',data:C3.map(x=>x.dn),itemStyle:{{color:OKG}},barWidth:'32%'}}
  ]
}});
}})();

// 明细表筛选
(function(){{
const ALL='all';
const trSel=document.getElementById('f_tier'), tkSel=document.getElementById('f_tkr'),
      rwSel=document.getElementById('f_rows'), cnt=document.getElementById('f_count'),
      tbody=document.querySelector('#det_tbl tbody');
const trOrder=['超强','强','弱'];
const tkrs=[...new Set(DET.map(x=>x.t))];
trOrder.forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=v;trSel.appendChild(o);}});
tkrs.forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=v;tkSel.appendChild(o);}});
const clsOf=v=>{{if(v==='-'||v==='未跌破')return'';const n=parseFloat(v);return isNaN(n)?'':(n>=0?'up':'down');}};
function render(){{
  const tr=trSel.value, tk=tkSel.value, rw=rwSel.value;
  let rows=DET;
  if(tr!==ALL)rows=rows.filter(x=>x.tr===tr);
  if(tk!==ALL)rows=rows.filter(x=>x.t===tk);
  cnt.textContent='共 '+rows.length+' 行';
  const shown=(rw===ALL||rows.length<=parseInt(rw))?rows:rows.slice(0,parseInt(rw));
  tbody.innerHTML=shown.map(r=>`<tr>
    <td>${{r.ev}}</td><td>${{r.tr}}</td><td>${{r.oni}}</td><td>${{r.t}}</td><td>${{r.sub}}</td>
    <td class='${{clsOf(r.mx)}}'>${{r.mx}}</td><td>${{r.pt}}</td><td>${{r.ds}}</td>
    <td class='${{clsOf(r.end12)}}'>${{r.end12}}</td><td class='${{clsOf(r.end)}}'>${{r.end}}</td></tr>`).join('')
    + (rows.length>shown.length?`<tr><td colspan='10' class='fmore'>仅显示前 ${{shown.length}} 行，调整"显示行数"查看全部</td></tr>`:'');
}}
[trSel,tkSel,rwSel].forEach(el=>el.addEventListener('change',render));
render();
}})();
</script>
</body>
</html>"""

# ================= 术语悬停浮窗标注 =================
TERMS = [
    ("厄尔尼诺", "太平洋海温异常偏暖的气候现象，常导致南美/东南亚天气反常，农产品产量承压"),
    ("拉尼娜", "与厄尔尼诺相反——太平洋海温偏冷，常导致南美大豆/玉米干旱减产，化肥需求与粮价获支撑"),
    ("ENSO", "El Niño-Southern Oscillation（厄尔尼诺-南方涛动）的英文缩写，是厄尔尼诺+拉尼娜现象的合称"),
    ("ONI", "Oceanic Niño Index（海洋尼诺指数）——NOAA 衡量厄尔尼诺/拉尼娜强弱的温度计（°C）：≥+0.5 算出现、≥+1.5 强、≥+2.0 超强"),
    ("onset", "一次厄尔尼诺/拉尼娜事件的\"开始月\"——事件窗口就从它算起"),
    ("绝对收益", "不复盘大盘、直接看这只股票自己赚了多少——对比'超额收益'（减去大盘后的部分）"),
    ("超额", "该股相比大盘（SPY）多赚/少赚的百分点——剔除大盘普涨普跌后的真实表现"),
    ("累计收益", "从事件开始月一路持有到窗口结束，逐月复利叠加后的总收益"),
    ("复利", "利滚利——每个月的收益都是在上个月已经涨/跌过的基础上再算"),
    ("T+6", "事件发生后第 6 个月的累计表现（T+12/T+24 同理）"),
    ("T+12", "事件发生后第 12 个月的累计表现"),
    ("T+24", "事件发生后第 24 个月的累计表现"),
    ("见顶", "收益在窗口内涨到的最高点，之后就开始回落"),
    ("见顶 T+", "最高点出现在事件开始月后的第几个月（1=开始当月就见顶）"),
    ("回撤", "从最高点往下掉的幅度——本报告用\"峰值与期末之差\"衡量"),
    ("回撤起始", "从最高点回落、且首次跌破\"峰值−5个百分点\"的那个月份"),
    ("正收益占比", "历史上多少比例的事件里该股绝对赚钱（不与大盘比较）"),
    ("胜率", "历史上多少比例的事件里该股赚钱/跑赢——本报告绝对版指绝对收益>0"),
    ("中位数", "一组数字按大小排中间那个——比均值更抗极端值干扰"),
    ("显著性", "结论可信度的统计表述——越显著越不可能是碰巧"),
    ("sig", "统计上很可信（p<0.01 的缩写）"),
    ("edge", "统计上一般可信（p<0.05 的缩写，还没到很可信）"),
    ("US10Y", "美国 10 年期国债利率——长端，反映经济与通胀预期"),
    ("SPY", "追踪标普 500 指数的 ETF，代表美股大盘，本报告作参照线"),
    ("t 检验", "判断一组收益的平均值是不是真的不等于零（而不是碰巧）的统计方法"),
    ("p 值", "\"纯属巧合\"的概率——越小越可信；p<0.01 记 sig、p<0.05 记 edge"),
    ("beta", "衡量一只股票跟随大盘涨跌的敏感度——大盘涨 1% 它跟多少"),
    ("峰值 ONI", "一次气候事件期间 ONI 达到的最高值，用于给事件分强度档"),
]
TERM_DICT = {k: v for k, v in sorted(TERMS, key=lambda x: -len(x[0]))}
import re as _re
_TERM_PAT = _re.compile("|".join(_re.escape(k) for k in TERM_DICT.keys()))
_BLOCK_RE = _re.compile(r"(<script[\s\S]*?</script>)|(<style[\s\S]*?</style>)", _re.S)
_TAG_SPLIT_RE = _re.compile(r"<[^>]+>")

def _annotate_text(text):
    def _repl(m):
        term = m.group(0)
        tip = TERM_DICT[term].replace("'", "&#39;")
        return f"<span class='term' data-tip='{tip}'>{term}</span>"
    return _TERM_PAT.sub(_repl, text)

def _annotate_block(text):
    if not text:
        return ""
    parts = _TAG_SPLIT_RE.split(text)
    tags = _TAG_SPLIT_RE.findall(text)
    out = []
    for i, p in enumerate(parts):
        out.append(_annotate_text(p))
        if i < len(tags):
            out.append(tags[i])
    return "".join(out)

def annotate_terms(html_str):
    parts = _BLOCK_RE.split(html_str)
    return "".join(_annotate_block(p) if (i % 2 == 0 and p) else (p or "") for i, p in enumerate(parts))

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
html = html.replace("</body>", tip_engine + "</body>")

out_path = os.path.join(OUT_DIR, "绝对收益版.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out_path, os.path.getsize(out_path), "bytes")
