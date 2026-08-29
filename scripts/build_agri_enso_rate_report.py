# -*- coding: utf-8 -*-
"""
Build 57 号研报：农业股 × 厄尔尼诺(ENSO) + 利率敏感性
读 results/agri_enso.json, agri_rate_sens.json, agri_verify.json → 生成 HTML
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
OUT_DIR = os.path.join(BASE, "reports", "57_农业股ENSO与利率敏感性")
os.makedirs(OUT_DIR, exist_ok=True)

enso = json.load(open(os.path.join(RES, "agri_enso.json"), encoding="utf-8"))
rate = json.load(open(os.path.join(RES, "agri_rate_sens.json"), encoding="utf-8"))
verify = json.load(open(os.path.join(RES, "agri_verify.json"), encoding="utf-8"))
strong = json.load(open(os.path.join(RES, "agri_strong_el.json"), encoding="utf-8"))
runup = json.load(open(os.path.join(RES, "agri_runup.json"), encoding="utf-8"))

SUB = enso["subsector"]
TICKERS = ["DE", "AGCO", "MOS", "CF", "NTR", "CTVA", "FMC", "ADM", "BG",
           "DAR", "FPI", "TSN", "HRL", "MOO", "DBA"]

# ---------- 通用表格渲染：cols = [(表头, 字段), ...] ----------
def mk_table(cols, rows, note=None, cls_field=None):
    head = "".join(f"<th>{c}</th>" for c, _ in cols)
    body = []
    for r in rows:
        tds = []
        for _, key in cols:
            v = r.get(key, "-")
            cls = ""
            if cls_field and key in cls_field:
                cls = r.get(cls_field[key], "")
            elif isinstance(v, str) and v.startswith(("+", "-", "−")) and key not in ("sig",):
                try:
                    cls = "up" if float(v) >= 0 else "down"
                except ValueError:
                    pass
            elif cls_field and key == "sig":
                cls = r.get("sigc", "no")
            tds.append(f"<td class='{cls}'>{v}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    note_html = f"<div class='note'>{note}</div>" if note else ""
    return f"<table><tr>{head}</tr>{''.join(body)}</table>{note_html}"

# ---------- 数据整理 ----------
g = enso["group"]
rows1 = []
for t in TICKERS:
    el, la, neu = g[t]["el"], g[t]["la"], g[t]["neu"]
    def fmt(x):
        if not x or "mean" not in x:
            return "-"
        ptag = {"sig": "<span class='tag sig'>sig</span>", "edge": "<span class='tag edge'>edge</span>", "no": ""}.get(x.get("sig", ""), "")
        return f"{x['mean']:+.2f}%<span class='note-in'>(n={x['n']})</span>{ptag}"
    diff = ""
    if el.get("mean") is not None and la.get("mean") is not None:
        diff = f"{la['mean'] - el['mean']:+.2f}"
    rows1.append({"t": t, "sub": SUB[t], "el": fmt(el), "la": fmt(la), "neu": fmt(neu), "diff": diff})

def ev_rows(key):
    d = enso[key]
    rows = []
    for t in TICKERS:
        v = d.get(t)
        if not v or v["n"] == 0:
            rows.append({"t": t, "n": 0, "mean": "-", "med": "-", "win": "-"})
            continue
        rows.append({"t": t, "n": v["n"], "mean": f"{v['mean']:+.1f}",
                     "med": f"{v['med']:+.1f}", "win": f"{v['win']:.0f}%"})
    return rows

la12 = enso["la_avg12"]
rows3 = []
for t in TICKERS:
    v = la12.get(t)
    if not v or v["n"] == 0:
        rows3.append({"t": t, "sub": SUB[t], "n": 0, "mean": "-", "med": "-", "win": "-"})
        continue
    rows3.append({"t": t, "sub": SUB[t], "n": v["n"], "mean": f"{v['mean']:+.1f}",
                  "med": f"{v['med']:+.1f}", "win": f"{v['win']:.0f}%"})
rows3.sort(key=lambda x: -x["n"])

reg = rate["reg"]
rows4 = []
for t in TICKERS:
    r = reg[t]
    if "error" in r:
        rows4.append({"t": t, "sub": SUB[t], "n": r.get("n", 0), "b10": "-", "p10": "-",
                      "sig": "-", "sigc": "no", "bs": "-", "r2": "-"})
        continue
    sigc = r.get("sens_sig", "no")
    label = {"sig": "显著", "edge": "边缘", "no": "不显著"}[sigc]
    rows4.append({"t": t, "sub": SUB[t], "n": r["n"], "b10": f"{r['beta10']:+.4f}",
                  "p10": f"{r['beta10_p']:.3f}", "sig": label, "sigc": sigc,
                  "bs": f"{r['beta_spy']:.2f}", "r2": f"{r['r2']:.2f}"})

grp = rate["groups"]
rows5 = []
for t in TICKERS:
    def gv(k):
        v = grp[t][k]
        if not v:
            return "-", "-"
        return str(v["n"]), f"{v['excess']:+.1f}"
    un, ux = gv("up")
    dn, dx = gv("dn")
    fn, fx = gv("flat")
    rows5.append({"t": t, "un": un, "ux": ux, "dn": dn, "dx": dx, "fn": fn, "fx": fx})

inf = verify["infl_ctrl"]
rows6 = []
for t in ["MOS", "CF", "DAR", "AGCO", "NTR", "DE", "ADM", "BG", "FMC"]:
    v = inf.get(t)
    if not v:
        continue
    rows6.append({"t": t, "n": v["n"], "rb": f"{v['beta10_raw']:+.3f}", "rp": f"{v['beta10_raw_p']:.3f}",
                  "cb": f"{v['beta10_ctrl']:+.3f}", "cp": f"{v['beta10_ctrl_p']:.3f}",
                  "cab": f"{v['beta_cpi']:+.3f}", "cap": f"{v['beta_cpi_p']:.3f}",
                  "r2ab": f"{v['r2_raw']:.3f} → {v['r2_ctrl']:.3f}"})

rec = verify["recent10"]
rows7 = []
for t in ["MOS", "CF", "DAR", "AGCO", "NTR", "CTVA"]:
    v = rec.get(t)
    if not v:
        continue
    sigc = "sig" if v["p"] < 0.01 else ("edge" if v["p"] < 0.05 else "no")
    label = {"sig": "显著", "edge": "边缘", "no": "不显著"}[sigc]
    rows7.append({"t": t, "n": v["n"], "b10": f"{v['beta10']:+.3f}", "p": f"{v['p']:.3f}",
                  "sig": label, "sigc": sigc, "bs": f"{v['beta_spy']:.2f}"})

d2 = rate["reg_d2"]
rows8 = []
for t in ["DAR", "AGCO", "MOS", "CF", "DE", "ADM", "BG", "FMC", "FPI", "CTVA"]:
    v = d2.get(t)
    if not v:
        continue
    s10 = "sig" if v["beta10_p"] < 0.01 else ("edge" if v["beta10_p"] < 0.05 else "no")
    s2 = "sig" if v["beta2_p"] < 0.01 else ("edge" if v["beta2_p"] < 0.05 else "no")
    l10 = {"sig": "显著", "edge": "边缘", "no": "不显著"}[s10]
    l2 = {"sig": "显著", "edge": "边缘", "no": "不显著"}[s2]
    rows8.append({"t": t, "n": v["n"], "b10": f"{v['beta10']:+.3f}", "l10": l10, "c10": s10,
                  "b2": f"{v['beta2']:+.3f}", "l2": l2, "c2": s2,
                  "bs": f"{v['beta_spy']:.2f}", "r2": f"{v['r2']:.2f}"})

ev_html_rows = "".join(
    f"<tr><td>{e['onset']}</td><td>{e['end']}</td><td>{e['peak_oni']}</td><td>{e['len_m']}</td></tr>"
    for e in enso["el_events"])

# ---------- 强厄尔尼诺数据 ----------
strong_ev = strong["strong_events"]
vstrong_ev = strong["vstrong_events"]
str_ev_html = "".join(
    f"<tr><td>{e['onset']}</td><td>{e['end']}</td><td>{e['peak']}</td><td>{e['len']}</td><td>{e['peak_ym']}</td></tr>"
    for e in strong_ev)

# 强 vs 弱 vs 全部 T+6/12/24 统计（合并计算，仅用 mean/med/win）
def agg_from_rows(rows, key):
    out = {}
    for r in rows:
        t = r["t"]
        if r["n"] == 0:
            continue
        out[t] = {"n": r["n"], "mean": r["mean"], "med": r["med"], "win": r["win"]}
    return out

def combine_block(key):
    str_rows = agg_from_rows(strong["strong_el_rows"][key], key)
    weak_rows_m = agg_from_rows(strong["weak_el_rows"][key], key)
    all_rows = {}
    for t in TICKERS:
        s, w = str_rows.get(t), weak_rows_m.get(t)
        if not s and not w:
            continue
        n = (s["n"] if s else 0) + (w["n"] if w else 0)
        if n == 0:
            continue
        mean = ((s["mean"] * s["n"] if s else 0) + (w["mean"] * w["n"] if w else 0)) / n
        # 中位与胜率无法精确合并，用加权近似(n 小时偏差大）
        meds = [ss["med"] if ss else None for ss in (s, w)]
        wins = [ss["win"] if ss else None for ss in (s, w)]
        all_rows[t] = {"n": n, "mean": round(mean, 1),
                       "med_s": s["med"] if s else None, "med_w": w["med"] if w else None,
                       "win_s": s["win"] if s else None, "win_w": w["win"] if w else None}
    return str_rows, weak_rows_m, all_rows

str6, weak6, _ = combine_block("e6")
str12, weak12, all12 = combine_block("e12")
str24, weak24, _ = combine_block("e24")

# 强 T+12 表格行
str12_rows = []
for t in TICKERS:
    v = str12.get(t)
    if not v:
        str12_rows.append({"t": t, "sub": SUB[t], "n": 0, "mean": "-", "med": "-", "win": "-"})
        continue
    str12_rows.append({"t": t, "sub": SUB[t], "n": v["n"], "mean": f"{v['mean']:+.1f}",
                       "med": f"{v['med']:+.1f}", "win": f"{v['win']:.0f}%"})

# 强度-超额相关
corr_rows = []
for r in sorted(strong["corr_peak"], key=lambda x: abs(x.get("corr_peak_e12", 0)), reverse=True):
    sigc = "sig" if r["p"] < 0.01 else ("edge" if r["p"] < 0.05 else "no")
    corr_rows.append({"t": r["t"], "sub": r["sub"], "n": r["n"],
                      "corr": f"{r['corr_peak_e12']:+.3f}",
                      "slope": f"{r['slope']:+.1f}",
                      "p": f"{r['p']:.3f}", "sigc": sigc})

# 强/弱月度对比
g = strong["group"]
strong_grp_rows = []
for t in TICKERS:
    s, w, n = g[t]["strong_el"], g[t]["weak_el"], g[t]["neutral"]
    def gfmt(x):
        if x.get("mean") is None:
            return "-"
        tag = {"sig": "<span class='tag sig'>sig</span>", "edge": "<span class='tag edge'>edge</span>", "no": ""}.get(x.get("sig", ""), "")
        return f"{x['mean']:+.2f}%<span class='note-in'>(n={x['n']})</span>{tag}"
    strong_grp_rows.append({"t": t, "sub": SUB[t], "s": gfmt(s), "w": gfmt(w), "neu": gfmt(n)})

# 强事件窗口 e6/e24 简短版（仅列 n>0）
def ev_mini(rows, key):
    return [{"t": r["t"], "n": r["n"], "mean": r["mean"], "med": r["med"], "win": r["win"]}
            for r in sorted(rows, key=lambda x: -x.get("mean", -999)) if r["n"] > 0]

# 图表数据：强 vs 弱 T+12 mean（按全事件排序）
bar_strweak = []
for t in TICKERS:
    s = str12.get(t)
    w = weak12.get(t)
    bar_strweak.append({"t": t, "s": s["mean"] if s else None, "w": w["mean"] if w else None,
                        "sn": s["n"] if s else 0, "wn": w["n"] if w else 0})
# 相关性散点数据
scat = []
for r in strong["corr_peak"]:
    scat.append({"t": r["t"], "corr": r["corr_peak_e12"], "p": r["p"]})

# ---------- 1.5 runup：分档 + 四指标数据 ----------
TIER_CN = {"weak": "弱(<+1.5°)", "strong": "强(1.5~2.0°)", "vstrong": "超强(≥2.0°)"}
def fnum(v, d="-", sgn=True):
    if v is None:
        return d
    return f"{v:+.1f}" if sgn else f"{v:.1f}"

# 分档汇总（三档 × 中位最大/期末 + 见顶/回撤时机）
tier_rows = []
for ts in runup["tier_summary"]:
    tier_rows.append({
        "tier": ts["tier_cn"], "ev": f"{ts['n_ev']} 次（{ts['n_ev_data']} 有数据）",
        "n": ts["n_samples"],
        "mx": fnum(ts["med_max"]), "end": fnum(ts["med_end"]),
        "mxavg": fnum(ts["avg_max"]), "endavg": fnum(ts["avg_end"]),
        "dd": fnum(ts["avg_dd"]),
        "pt": f"T+{ts['avg_peak_t']}" if ts["avg_peak_t"] else "-",
        "ds": f"T+{ts['avg_dd_start']}" if ts["avg_dd_start"] else "未跌破",
        "ud": f"{ts['n_updown_pct']:.0f}%", "al": f"{ts['n_alldown_pct']:.0f}%",
    })

# 事件 × 标的四指标明细（全部有数据事件，按档排序）
det_rows = []
for ev in runup["events_detail"]:
    if not ev["tickers"]:
        continue
    tr = TIER_CN[ev["tier"]]
    for t, v in ev["tickers"].items():
        e12 = v.get("end_excess12")
        det_rows.append({
            "ev": ev["onset"], "tr": tr, "oni": ev["oni_peak"], "t": t, "sub": SUB[t],
            "mx": fnum(v["max_excess"]), "pt": f"T+{v['peak_t']}",
            "ds": f"T+{v['dd_start_t']}" if v.get("dd_start_t") else "未跌破",
            "end": fnum(v["end_excess"]),
            "end12": fnum(e12) if e12 is not None else "-",
        })
# 按档分组顺序排序（超强→强→弱）
_torder = {"超强(≥2.0°)": 0, "强(1.5~2.0°)": 1, "弱(<+1.5°)": 2}
det_rows.sort(key=lambda x: (_torder[x["tr"]], x["ev"], x["t"]))

# 标的 × 档位（强/超强两档 avg_max / avg_end / 见顶时机对比）
byt_rows = []
for t in TICKERS:
    st = runup["by_ticker_tier"][t].get("strong")
    vs = runup["by_ticker_tier"][t].get("vstrong")
    byt_rows.append({
        "t": t, "sub": SUB[t],
        "s_n": st["n"] if st else 0,
        "s_mx": fnum(st["avg_max"]) if st else "-", "s_end": fnum(st["avg_end"]) if st else "-",
        "s_pt": f"T+{st['avg_peak_t']:.0f}" if st and st.get("avg_peak_t") else "-",
        "v_n": vs["n"] if vs else 0,
        "v_mx": fnum(vs["avg_max"]) if vs else "-", "v_end": fnum(vs["avg_end"]) if vs else "-",
        "v_pt": f"T+{vs['avg_peak_t']:.0f}" if vs and vs.get("avg_peak_t") else "-",
    })

# 图 c7 数据：三档 × 中位最大/中位期末（pp）+ 见顶/回撤时机
c7_tier = []
for ts in runup["tier_summary"]:
    c7_tier.append({
        "tier": ts["tier_cn"], "mx": ts["med_max"], "end": ts["med_end"],
        "dd": ts["avg_dd"], "pt": ts["avg_peak_t"], "ds": ts["avg_dd_start"],
    })

# ---------- 图表数据 ----------
oni_hist = []
with open(os.path.join(BASE, "data", "agri", "raw", "oni.txt"), encoding="utf-8") as f:
    sm = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
          "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
    for line in f:
        line = line.strip()
        if not line or line[:4] in ("SEAS", " SEA"):
            continue
        p = line.split()
        if len(p) < 4:
            continue
        try:
            seas, yr, anom = p[0], int(p[1]), float(p[3])
        except Exception:
            continue
        if sm.get(seas) is not None:
            oni_hist.append([f"{yr}-{sm[seas]:02d}", round(anom, 2)])
oni_hist = [x for x in oni_hist if int(x[0][:4]) >= 1980]

bar_beta = [{"t": t, "b": reg[t].get("beta10", 0) if "beta10" in reg[t] else 0,
             "sig": reg[t].get("sens_sig", "no") if "sens_sig" in reg[t] else "no",
             "lab": f"{reg[t]['beta10']:+.3f}" if "beta10" in reg[t] else "-"}
            for t in TICKERS]

bar_grp = []
for t in TICKERS:
    def ex(k):
        v = grp[t][k]
        return v["excess"] if v else 0
    bar_grp.append({"t": t, "u": ex("up"), "d": ex("dn")})

# ---------- 表格 ----------
COLS_1 = [("标的", "t"), ("子行业", "sub"), ("El Niño 月均收益", "el"),
          ("La Niña 月均收益", "la"), ("中性月均收益", "neu"), ("月均差(LA−EL)", "diff")]
t1 = mk_table(COLS_1, rows1,
              note="月度收益=当月 adj_close 月末复权收益的算术均值（%）；n=该 ENSO 状态覆盖的月份数。sig=双侧 p<0.01、edge=p<0.05（t 检验 vs 0）。La Niña 期化肥股（CF/MOS/NTR/CTVA）月均收益系统性高于中性与 El Niño 期；El Niño 期无一致规律，全部 p>0.5。")

COLS_EV = [("标的", "t"), ("n(事件数)", "n"), ("均值超额 pp", "mean"),
           ("中位超额 pp", "med"), ("胜率", "win")]
t2 = mk_table(COLS_EV, ev_rows("ev_avg6"))
t2b = mk_table(COLS_EV, ev_rows("ev_avg12"))
t2c = mk_table(COLS_EV, ev_rows("ev_avg24"))

COLS_3 = [("标的", "t"), ("子行业", "sub"), ("n(事件数)", "n"), ("均值超额 pp", "mean"),
          ("中位超额 pp", "med"), ("胜率", "win")]
t3 = mk_table(COLS_3, rows3,
              note="超额=个股 12 个月复利累计收益 − SPY 同期（pp）。La Niña 期化肥链（CF/MOS/NTR）与粮商（BG/ADM）、农机（DE）普遍跑赢；肉类（TSN）跑输。CF 8 次事件 8/8 全胜。样本=1995-2022 年 11 次 La Niña 中数据可得者。")

COLS_4 = [("标的", "t"), ("子行业", "sub"), ("n(月)", "n"), ("β₁₀ (%/bp)", "b10"),
          ("p", "p10"), ("显著性", "sig"), ("βSPY", "bs"), ("R²", "r2")]
t4 = mk_table(COLS_4, rows4, cls_field={"sig": "sigc"},
              note="月频双因子回归：个股月收益 = α + β₁×ΔUS10Y(bp) + β₂×SPY + ε（1962-2026，SPY 自 1993）。β₁>0 = 利率上行月跑赢；★不再另注，显著列按 sig/edge/no。MOS/CF 显著为正、DAR/AGCO 边缘为正——农业股对利率上行并非负敏感。")

COLS_5 = [("标的", "t"), ("上行月 n", "un"), ("上行月超额 pp", "ux"),
          ("下行月 n", "dn"), ("下行月超额 pp", "dx"), ("平坦月 n", "fn"), ("平坦月超额 pp", "fx")]
t5 = mk_table(COLS_5, rows5,
              note="上行月=US10Y 月末值月环比 > +5bp（321 个，均值 +26.9bp）；下行月=<-5bp（307 个，均值 −28.0bp）；平坦=±5bp 内。超额=当月收益−SPY（pp）。CF 上行月 +3.4pp、DAR +2.4pp、AGCO +1.7pp；下行月普遍转负——与 β₁ 正号一致。")

COLS_6 = [("标的", "t"), ("n", "n"), ("原始β₁₀", "rb"), ("原始p", "rp"),
          ("控制β₁₀", "cb"), ("控制p", "cp"), ("CPIβ", "cab"), ("CPIp", "cap"), ("R² 原→控", "r2ab")]
t6 = mk_table(COLS_6, rows6,
              note="控制变量加入 CPI 同比后 β₁₀ 系数与显著性几乎不变（MOS +0.075→+0.075；CF +0.072→+0.070），CPI 自身系数不显著 → 利率敏感性不是通胀交易的伪装。US10Y 月变动与 CPI 同比月相关系数仅 0.086（773 个月）。")

COLS_7 = [("标的", "t"), ("n(月)", "n"), ("β₁₀ 2016+", "b10"), ("p", "p"), ("显著性", "sig"), ("βSPY", "bs")]
t7 = mk_table(COLS_7, rows7, cls_field={"sig": "sigc"},
              note="2016-01 起子样本。MOS 近 10 年 β10=+0.169（p<0.001）、CF +0.142（p<0.001），较全期(+0.075/+0.073)显著增强——近年化肥股对利率上行的正联动更强。")

COLS_8 = [("标的", "t"), ("n", "n"), ("β₁₀ (US10Y)", "b10"), ("p₁₀", "l10"),
          ("β₂ (US2Y)", "b2"), ("p₂", "l2"), ("βSPY", "bs"), ("R²", "r2")]
t8 = mk_table(COLS_8, rows8, cls_field={"l10": "c10", "l2": "c2"},
              note="四因子回归（含 US2Y 月变动）。DAR 长短端方向相反：US10Y +0.164（p=0.002）显著正、US2Y −0.131（p=0.015）显著负 → 曲线平坦化受益者。AGCO 仅长端正（+0.089，p=0.008）。其余标的 10Y/2Y 双系数均不显著。")

# ---------- HTML ----------
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>57 · 农业股 × 厄尔尼诺(ENSO) 回测 + 利率敏感性</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
:root{{--bg:#ffffff;--fg:#1a1a1a;--muted:#666;--line:#e5e5e5;--accent:#185FA5;--red:#D55E00;--green:#009E73;--card:#f7f8fa;--okb:#0072B2;--okc:#E69F00;--okr:#D55E00;--okg:#009E73;--okp:#CC79A7;--okbl:#56B4E9}}
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
.badge{{display:inline-block;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:600;margin-right:8px}}
.b-hi{{background:#fde8e8;color:#A32D2D}}.b-mid{{background:#fdf3e0;color:#854F0B}}.b-lo{{background:#e8f5ee;color:#0F6E56}}
.chart{{width:100%;height:380px;margin:14px 0}}
.note{{font-size:12px;color:var(--muted);margin:6px 0 2px}}
.note-in{{font-size:11px;color:var(--muted)}}
.exec{{background:#fffbea;border:1px solid #f0dca0;border-radius:10px;padding:16px 20px;margin:16px 0}}
.exec li{{margin:6px 0}}
.legend{{font-size:12px;color:var(--muted);margin-top:8px}}
.warn{{background:#fdf2f2;border:1px solid #f0c8c8;border-radius:8px;padding:12px 16px;font-size:13px;margin-top:10px}}
.foot{{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}}
.collapse{{max-height:420px;overflow-y:auto;border:1px solid var(--line);border-radius:8px}}
.filterbar{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:10px 0;font-size:13px;display:flex;flex-wrap:wrap;gap:16px;align-items:center}}
.filterbar label{{display:inline-flex;align-items:center;gap:6px;color:#444}}
.filterbar select{{padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;font-size:13px;cursor:pointer}}
.filterbar .fcount{{color:var(--muted);font-size:12px}}
#det_tbl{{font-size:12.5px}}
#det_tbl thead th{{position:sticky;top:0;background:#f0f1f3;z-index:1}}
.fmore{{text-align:left;color:var(--muted);font-style:italic}}
</style>
</head>
<body><div class="wrap">

<h1>农业股 × 厄尔尼诺(ENSO) 历史回测 + 利率敏感性量化拆解</h1>
<div class="sub">报告编号 57 ｜ 2026-08-29 ｜ 覆盖：DE / AGCO / MOS / CF / NTR / CTVA / FMC / ADM / BG / DAR / FPI / TSN / HRL / MOO / DBA ｜ 数据源：NOAA ONI 1950-2026、FRED DGS10/DGS2/CPIAUCSL、Yahoo 日线(CDP)至 08-27、富途快照 08-28</div>

<div class="exec">
<b>一页结论</b>
<ul>
<li><b>厄尔尼诺（El Niño）本身不是有效的农业股交易信号</b>：22 次事件（1951-2023）下，农业股月度收益与中性期无统计显著差异（全部 p&gt;0.5）；事件窗口仅农机 DE 在 onset 后 T+6 温和正超额（+7.7pp，胜率 70%），且 T+24 稳健（中位数 +29.4pp，胜率 80%）；DAR 油脂加工 T+6 +12.7pp（60%）但中位数不稳。</li>
<li><b>真正的 ENSO 信号在反面——La Niña 期化肥链显著走强</b>：La Niña 月均收益 CF +5.8%/月 vs 中性 +1.6%、MOS +3.1%、NTR +3.0%；事件 onset 后 T+12 累计超额 CF +67.5pp（8 次事件 8/8 全胜）、MOS +35.1pp（73%）、BG +19.7pp（75%）、DE +13.0pp（73%）。机制＝La Niña 常伴南美大豆/玉米干旱减产→农产品价格与种植利润支撑→化肥量价齐升；肉类 TSN（−7.3pp）反向（饲料成本）。</li>
<li><b>农业股对利率上行并不悲观，方向与直觉相反</b>：全期月频回归中 MOS（β₁₀=+0.075，p=0.001）、CF（+0.073，p=0.009）显著为正，DAR（+0.064，p=0.049）、AGCO（+0.048，p=0.019）边缘为正——US10Y 上行月化肥/农机反而跑赢；控制 CPI 后系数几乎不变（非通胀代理）；近 10 年 MOS β₁₀=+0.169、CF +0.142（均 p&lt;0.001），敏感度增强。</li>
<li><b>但这是"增长型"利率上行的属性，非"紧缩型"</b>：DAR 长短端方向相反（US10Y +0.164 显著 / US2Y −0.131 显著）＝曲线平坦化交易的受益者；粮商（ADM/BG）、肉类（TSN/HRL）、农业 REIT（FPI）对利率真正中性；DE 亦不显著（业绩由全球农机周期主导）。</li>
<li><b>操作含义</b>：担心利率上行不必系统性回避农业股（化肥/农机甚至是顺风）；若做天气交易，盯 La Niña 而非 El Niño，化肥（CF/MOS/NTR）首选、农机（DE）次之，持仓周期宜 12 个月+。样本警示：CF/NTR/CTVA 事件数少（n=2~8）、CF 的 T+24 均值被 2006 化肥超级牛市单事件拉高，置信度打折。</li>
<li><b>强厄尔尼诺专项（≥+1.5°C，9 次）</b>：强度分级后出现"<b>越强越弱</b>"——弱 El Niño 事件后农业股多数正超额（CF +75.8pp、DAR +65.6pp、DE +13.8pp），<b>强 El Niño（含 1982/1997/2014 三次超强 ≥+2.0°C）后几乎所有标的 T+12 转负</b>（MOS −30.7pp、DAR −33.7pp、ADM −21.0pp；仅 DE/HRL/TSN 相对抗跌）；12 只中 10 只"峰值 ONI × 超额"斜率为负。强 El Niño 的全球天气紊乱+农产品价格过山车对农业链整体逆风，<b>与 La Niña 化肥强正构成不对称镜像</b>——交易上应反向对待（强 El Niño 期减持化肥/粮商/油脂，弱 El Niño 可做多 DE/DAR）。</li>
</ul>
</div>

<h2>一、厄尔尼诺量化回测</h2>

<h3>1.1 数据与方法</h3>
<div class="card">
<p><b>ENSO 定义（NOAA ONI）</b>：3 个月滑动 SST 异常指数，按季中点落月。El Niño = ONI ≥ +0.5°C 连续 ≥5 个月；La Niña = ≤ −0.5°C 连续 ≥5 个月；其余为中性。1950-2026 识别 El Niño 22 次 / La Niña 11 次（1990 年后）。</p>
<p><b>样本</b>：15 只农业标的 + SPY 基准，1990-2026 日线（后上市缩短：NTR 2018、CTVA 2019、FPI 2014、DBA 2007、MOO 2007）。<b>方法</b>：①单月收益按 ENSO 状态分组对比（t 检验，sig=双侧 p&lt;0.01 / edge=p&lt;0.05 / no=p≥0.05）；②事件研究＝sonset 月份起 T+6/T+12/T+24 复利累计收益 − SPY 同期＝超额（pp）。</p>
<p>月度状态分布：El Niño 23.4%（215 个月）、La Niña 24.1%（221 个月）、中性 48.8%（448 个月）。</p>
</div>

<div class="chart" id="c1"></div>
<div class="legend">ONI 指数（°C）月度序列（1980 起）｜ 橙色底纹 = El Niño 段（ONI≥+0.5）｜ 数据：NOAA ｜ 2023-24 为最近一次强事件（峰值 +1.99°C）</div>

<h3>1.2 月度收益按 ENSO 状态分组：月频无显著差异</h3>
{t1}

<div class="card">
<p><b>解读</b>：ENSO 作为"月度状态标签"对农业股收益没有统计可辨识的区分力——El Niño 组 vs 中性组差异全不显著（p 普遍 >0.8）。唯一结构性模式：<b>La Niña 月化肥股（CF/MOS/NTR/CTVA）与粮商（BG）月均收益系统性高于中性</b>，且与 El Niño 月之差明显（CF +5.8 vs +0.3、MOS +3.1 vs −0.2）。市场并未把官方 ENSO 状态定价进农业股（信息已被预期），弱信号需靠 La Niña 的供应冲击窗口捕捉。</p>
</div>

<h3>1.3 El Niño 事件窗口：onset 后累计超额（vs SPY）</h3>
<h4>T+6（onset 后 6 个月）</h4>
{t2}
<h4>T+12</h4>
{t2b}
<h4>T+24</h4>
{t2c}
<div class="warn">
<b>⚠ 阅读警示</b>：CF 的 T+24 均值 +126.9pp 由 2006-09 单次事件驱动（onset 后 24 个月 +863pp，恰逢 2006-08 起化肥超级牛市），中位数仅 −9.5pp——均值≠代表性。DAR T+6/T+12 均值为正但中位数偏负、胜率 40-60%，不稳健。<b>El Niño 下最可靠的窗口信号是 DE（农机）：T+6 胜率 70%、T+24 胜率 80% 且中位数 +29.4pp</b>，逻辑＝北美种植面积扩张→设备需求，但幅度温和。
</div>

<h3>1.4 La Niña 事件窗口：化肥链的系统性正向信号（重点）</h3>
{t3}
<div class="card">
<p><b>机理（基本面）</b>：La Niña 典型天气＝南美（阿根廷/巴西南部）干旱、美国南部冬麦区干燥、东南亚偏湿。传导：南美大豆/玉米减产预期 → 全球谷物价格获支撑 → 美国农户种植利润与出口优势改善 → <b>化肥投入意愿不减反增（量价齐升）</b>。历史窗口验证此链条：CF（北美最大氮肥）8/8 事件 T+12 全胜、MOS（磷钾肥）73% 胜率、BG/ADM（粮商，受益价差与贸易流）75%/64%。反例：TSN（27%）——饲料成本抬升挤压肉类加工毛利。</p>
<p><b>子行业排序（La Niña T+12 超额）</b>：<span class="badge b-hi">化肥 CF / MOS / NTR</span><span class="badge b-mid">粮商 BG / ADM</span><span class="badge b-mid">农机 DE</span><span class="badge b-mid">油脂 DAR</span><span class="badge b-lo">肉类 TSN</span></p>
</div>

<h3>1.5 强厄尔尼诺专项：三档强度 × 窗口内最大超额 / 最终超额 / 见顶时机 / 回撤起始</h3>
<div class="card">
<p><b>分级</b>：22 次 El Niño 按事件峰值 ONI 分三档——<b>弱（&lt;+1.5°C）13 次</b>、<b>强（+1.5~&lt;+2.0°C）6 次</b>、<b>超强（≥+2.0°C）3 次（1982/1997/2014）</b>。路径口径：onset 后逐月复利累计收益 − SPY 同期＝超额（pp），遍历 24 个月。</p>
<p><b>核心发现（补充 run-up 路径验证）</b>：强度越高，<b>窗口内最大超额越低、见顶越早、回撤越深</b>——弱档中位最大超额 +26.5pp、期末 +4.7pp；强档 +14.6pp / −23.4pp；超强档 +10.9pp / −40.7pp。见顶时机从弱档平均 T+13.6 提前到超强档 T+6.7。即<b>"越强越弱"并非全程阴跌：强/超强事件窗口内仍有冲高（中位 +11~15pp），但多在 onset 后 7-14 个月崩落转负</b>——交易含义＝快钱窗口在 onset 后约 6 个月内，之后转防守。</p>
<p><b>四指标定义</b>：<b>最大超额</b>=T+24 窗口内最大累计超额（run-up 峰值，pp）；<b>最终超额</b>=T+24 期末累计超额（pp，附 T+12 期末）；<b>见顶 T+</b>=最大超额发生在 onset 后第几个月（1=onset 月）；<b>回撤起始 T+</b>=见顶后首个跌破「峰值−5pp」的月份（≤24；未跌破记"未跌破"）。</p>
</div>

<h4>分档汇总（中位数为主口径，避免 2006 化肥牛市极端值污染）</h4>
{mk_table([("分档", "tier"), ("事件数", "ev"), ("样本", "n"), ("中位最大超额pp", "mx"), ("中位最终超额pp", "end"),
           ("平均最大超额pp", "mxavg"), ("平均最终超额pp", "endavg"), ("平均回撤pp", "dd"),
           ("平均见顶T+", "pt"), ("平均回撤起始T+", "ds"), ("冲高后转负", "ud"), ("全程阴跌", "al")], tier_rows,
          note="中位最大超额=窗口内峰值的中位数（pp）；中位最终超额=T+24 期末中位数；平均回撤=peak−期末；'冲高后转负'=窗口内最大超额>0 且期末<0 的样本占比；'全程阴跌'=窗口内从未转正的样本占比。三档单调：强度↑→最大超额↓、期末↓、见顶提前、回撤加深。")}

<div class="chart" id="c7"></div>
<div class="legend">三档 El Niño 事件：T+24 窗口内中位最大超额（蓝）vs 中位最终超额（橙，pp）＋ 平均见顶 T+N（紫点，右轴）｜ 强度越高→峰值越低、期末越负、见顶越早。</div>

<h4>事件 × 标的 四指标明细（可筛选）</h4>
<div class="filterbar">
  <label>强度档：<select id="f_tier"><option value="all">全部档位</option></select></label>
  <label>股票：<select id="f_tkr"><option value="all">全部标的</option></select></label>
  <label>显示 <select id="f_rows"><option value="20">20</option><option value="50">50</option><option value="100">100</option><option value="all" selected>全部</option></select> 行</label>
  <span class="fcount" id="f_count"></span>
</div>
<div class="collapse" style="max-height:none;max-height:560px">
<table id="det_tbl">
<thead><tr><th>事件</th><th>档</th><th>峰值ONI</th><th>标的</th><th>子行业</th><th>最大超额pp</th><th>见顶T+</th><th>回撤起始T+</th><th>T+12期末pp</th><th>T+24期末pp</th></tr></thead>
<tbody></tbody>
</table>
</div>
<div class="note">td<sub>12/24</sub>期末=对应窗口复利累计超额；'未跌破'=窗口内未跌破峰值−5pp（回撤未实质发生）。支持按强度档与股票双筛选，实时过滤，再按显示行数截断。强度档与股票下拉选项由数据自动生成。</div>

<h4>标的 × 强度档（强 vs 超强，平均口径）</h4>
{mk_table([("标的", "t"), ("子行业", "sub"),
           ("强n", "s_n"), ("强平均最大pp", "s_mx"), ("强平均期末pp", "s_end"), ("强平均见顶T+", "s_pt"),
           ("超强n", "v_n"), ("超强平均最大pp", "v_mx"), ("超强平均期末pp", "v_end"), ("超强平均见顶T+", "v_pt")], byt_rows,
          note="强=峰值 ONI 1.5~&lt;2.0°C（n 小，仅 2009/2023 两次有数据）；超强=≥2.0°C（1997/2014）。多数标的超强档平均期末超额低于强档（超强更惨），且见顶更早；仅 DE/HRL/TSN 等防御/资本品相对抗跌。n=1-2 时仅作方向参考。")}

<h4>事件强度（峰值 ONI）→ T+12 超额 相关性 / 斜率</h4>
<table><tr><th>标的</th><th>子行业</th><th>n(事件)</th><th>corr(峰值ONI,e12)</th><th>斜率pp/°C</th><th>p</th></tr>
{''.join(f"<tr><td>{r['t']}</td><td>{r['sub']}</td><td>{r['n']}</td><td class='{r['sigc']}'>{r['corr']}</td><td>{r['slope']}</td><td>{r['p']}</td></tr>" for r in corr_rows)}
</table>
<div class="note">corr 均为 12 次事件（含强弱）线性相关；斜率=ONI 每 +1°C 的 T+12 超额变化（pp）。FMC −34.6pp/°C、DAR −60.9pp/°C、CF −56.3pp/°C 等为强负，但 p 全部 &gt;0.28（n 小，方向性结论）。</div>

<div class="chart" id="c6"></div>
<div class="legend">强（≥+1.5°C，橙）vs 弱（&lt;+1.5°C，蓝）El Niño 事件 onset 后 T+12 平均超额（pp）｜ 弱事件多为正、强事件几乎全负 → 强度与超额反向。</div>

<h2>二、利率敏感性量化</h2>

<h3>2.1 方法</h3>
<div class="card">
<p>月频双因子回归：<b>个股月收益 = α + β₁×ΔUS10Y(bp) + β₂×SPY月收益 + ε</b>（1962-2026，SPY 自 1993）。β₁ 符号＝对利率月度变动的敏感方向（%/bp）。另做三组稳健性：①控制 CPI 同比（通胀代理检验）；②近 10 年子样本；③四因子含 US2Y（长短端分离）。</p>
<p>利率环境结构：全期 775 月（1962 起）中上行(>+5bp) 321 个月（均值 +26.9bp）、下行(<-5bp) 307 个月（均值 −28.0bp）、平坦 147 个月。</p>
</div>

<h3>2.2 全期回归：化肥/农机对利率上行正敏感，粮商/肉类中性</h3>
{t4}
<div class="card">
<p><b>解读</b>：①<b>方向反直觉</b>——教科书式"利率上行压制长久期/高估值"并不适用于农业股：利率上行月往往伴随经济增长与商品需求改善，化肥（MOS/CF）与农机（AGCO）作为工业+农业双周期资产反而受益；②粮商（ADM/BG）、肉类（TSN/HRL）、REIT（FPI）β₁≈0 且不显著——低贝塔防御型，利率方向与收益无关；③DE 不显著，业绩由全球农机替换周期主导。</p>
</div>

<div class="chart" id="c4"></div>
<div class="legend">β₁₀ = 月收益对 US10Y 月度变动(bp) 的回归系数（控制 SPY）。红=显著正、橙=边缘正、灰=不显著。★=显著(p&lt;0.01)  ☆=边缘(p&lt;0.05)。</div>

<h3>2.3 利率上行/下行月实际表现：与 β₁ 方向一致</h3>
{t5}
<div class="chart" id="c5"></div>
<div class="legend">US10Y 上行月（红，月内 >+5bp）与下行月（绿，<-5bp）的月度超额收益 vs SPY（pp）。上行月化肥/农机/DAR 正超额、下行月转负——与 β₁ 正号一致。</div>
<div class="card">
<p><b>一致性验证</b>：CF 上行月平均超额 +3.4pp（107 个月）、DAR +2.4pp（157 个月）、AGCO +1.7pp（168 个月）；而下行月普遍转负（MOS −1.3pp、NTR −1.3pp、AGCO −1.0pp）。农业股与利率月度变动的同向联动在全样本稳定存在，幅度 1-3pp/月。</p>
</div>

<h3>2.4 稳健性 1：控制通胀后依然成立 → 非通胀代理</h3>
{t6}
<div class="card">
<p><b>结论</b>：加入 CPI 同比后 β₁₀ 系数与显著性几乎不动（MOS +0.075→+0.075；CF +0.072→+0.070；DAR 持平），且 CPI 系数均不显著 → 利率敏感性不是"通胀交易"的伪装，而是独立于通胀的利率-增长周期暴露。US10Y 月变动与 CPI 同比仅相关 0.086（773 个月），信息含量不同。</p>
</div>

<h3>2.5 稳健性 2：近 10 年敏感性增强，非样本特有</h3>
{t7}

<h3>2.6 长短端分离：DAR 的"平坦化"暴露，其余无方向敏感</h3>
{t8}
<div class="card">
<p><b>DAR 是唯一长短端方向相反的标的</b>：US10Y 每 +1bp 月收益 +0.164pp（p=0.002）、US2Y 每 +1bp −0.131pp（p=0.015）＝<b>曲线平坦化交易的受益者</b>（长端上行=经济与需求预期、短端=流动性收紧），与其废弃油脂→再生柴油（RIN）业务对能源-利率环境的高敏感一致。AGCO 仅长端正（+0.089，p=0.008）。其余标的 10Y/2Y 双系数均不显著 → 对利率中枢方向无稳定暴露。</p>
</div>

<h2>三、基本面分析（子行业定性）</h2>
<table>
<tr><th>子行业</th><th>标的</th><th>利润驱动</th><th>厄尔尼诺暴露</th><th>利率暴露</th></tr>
<tr><td>农机制造（资本品）</td><td>DE / AGCO</td><td>全球农机替换周期、美国种植面积、经销商库存融资利率</td><td>El Niño 温和正（DE T+6/T+24 胜率高）；La Niña 正（DE T+12 +13pp）</td><td>低-温和正（AGCO +0.089；DE 不显著但融资成本敏感）</td></tr>
<tr><td>化肥（商品）</td><td>MOS / CF / NTR</td><td>钾磷氮价格周期、天然气成本（CF 氮肥）、供需缺口</td><td>El Niño 中性；<b>La Niña 强正（CF T+12 8/8 全胜、MOS 73%）</b></td><td><b>显著正</b>（MOS +0.075、CF +0.073）→利率上行顺风</td></tr>
<tr><td>种子/植保</td><td>CTVA / FMC</td><td>种植面积、抗性种子渗透率、植保价格</td><td>样本短（2019 起），信号弱</td><td>不显著</td></tr>
<tr><td>粮商（贸易）</td><td>ADM / BG</td><td>谷物-压榨价差、贸易流、乙醇（ADM）</td><td>La Niña 正（BG T+12 75%）；El Niño 偏弱</td><td>中性（β₁₀≈0）</td></tr>
<tr><td>油脂/副产品加工</td><td>DAR</td><td>油脂价差、再生柴油 RIN、副产品</td><td>El Niño T+6 正但中位数不稳</td><td>长短端相反（平坦化受益者）</td></tr>
<tr><td>农业 REIT</td><td>FPI</td><td>农田租金、土地增值、债务成本</td><td>样本短，信号弱</td><td>理论负（久期属性），样本系数不显著</td></tr>
<tr><td>肉类加工（防御）</td><td>TSN / HRL</td><td>饲料成本、肉类消费、利润率</td><td>La Niña 负（TSN −7.3pp，饲料成本压制）</td><td>中性（防御属性）</td></tr>
</table>
<div class="note">基本面判断基于各子行业商业模式与历史业绩结构，不含个股盈利预测。</div>

<h2>四、风险与局限</h2>
<div class="warn">
<ul>
<li><b>事件样本小</b>：La Niña 窗口 CF n=8、NTR/CTVA n=2；El Niño T+24 部分标的仅 2-6 个事件。事件研究统计功效有限，显著性一律视为上限（同既往事件研究口径）。</li>
<li><b>重叠/串扰</b>：1991-92、2014-16 等 El Niño 期间叠加海湾战争、中国去库存、商品超级周期等宏观冲击，超额非纯 ENSO 效应。</li>
<li><b>利率回归共线性</b>：β₁₀ 控制 CPI 后稳健，但无法完全剥离"增长预期"（PMI/信用利差）代理的共线；结论定性为"利率上行顺风"而非因果。</li>
<li><b>数据边界</b>：Yahoo 复权收盘价（CDP 抓取）、FRED/NOAA 官方原值；历史结论不保证未来。</li>
<li><b>个股异质</b>：CF 2006 化肥超级牛市为极端值来源；NTR/CTVA 上市晚，样本最短。</li>
<li>本报告为历史统计推演，不构成投资建议。投资有风险，决策需谨慎。</li>
</ul>
</div>

<h2>附录 A：El Niño 事件清单（22 次）</h2>
<div class="collapse">
<table><tr><th>起始日</th><th>结束日</th><th>峰值ONI</th><th>持续月数</th></tr>
{ev_html_rows}
</table>
</div>

<div class="foot">
报告 57 · 生成于 2026-08-29 · 数据：NOAA ONI（1950-2026）/ FRED DGS10,DGS2,CPIAUCSL（1962-2026）/ Yahoo 日线至 08-27 / 富途快照 08-28<br>
参数图例：β₁₀=个股月收益对 US10Y 月变动的敏感度（%/bp）；超额=累计收益−SPY 同期（pp）；胜率=正超额事件占比；El Niño/La Niña 按 ONI≥+0.5/≤−0.5 连续≥5 月；强 El Niño=事件峰值 ONI ≥+1.5°C（超强 ≥+2.0°C）；sig=双侧 p&lt;0.01、edge=p&lt;0.05、no=p≥0.05。
</div>

</div>
<script>
const ONI = {json.dumps(oni_hist)};
const BETA = {json.dumps(bar_beta)};
const GRP = {json.dumps(bar_grp)};
const STRWEAK = {json.dumps(bar_strweak)};
const TIER7 = {json.dumps(c7_tier)};
const DET = {json.dumps(det_rows)};
const OKB='#0072B2', OKR='#D55E00', OKG='#009E73', OKC='#E69F00', OKP='#CC79A7', MUT='#888';

// 图1 ONI
(function(){{
const el=document.getElementById('c1');
const dates=ONI.map(x=>x[0]), vals=ONI.map(x=>x[1]);
const areas=[]; let seg=null;
for(let i=0;i<vals.length;i++){{
  if(vals[i]>=0.5){{ if(!seg) seg={{s:i}}; }}
  else if(seg){{ seg.e=i; if(seg.e-seg.s>=2) areas.push({{s:dates[seg.s],e:dates[seg.e]}}); seg=null; }}
}}
if(seg) areas.push({{s:dates[seg.s],e:dates[seg.e]}});
echarts.init(el).setOption({{
  grid:{{left:44,right:16,top:30,bottom:40}},
  tooltip:{{trigger:'axis',formatter:p=>`${{p[0].axisValue}}: ${{p[0].data.toFixed(2)}}°C`}},
  xAxis:{{type:'category',data:dates,axisLabel:{{show:false}}}},
  yAxis:{{type:'value',name:'ONI °C',nameTextStyle:{{color:MUT}},splitLine:{{lineStyle:{{color:'#eee'}}}},axisLabel:{{formatter:v=>v.toFixed(1)}}}},
  series:[{{type:'line',data:vals,symbol:'none',lineStyle:{{color:OKB,width:1.6}},
    areaStyle:{{color:{{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{{offset:0,color:'rgba(0,114,178,0.15)'}},{{offset:1,color:'rgba(0,114,178,0.02)'}}]}}}},
    markArea:{{silent:true,itemStyle:{{color:'rgba(213,94,0,0.12)'}},data:areas.map(a=>[{{xAxis:a.s}},{{xAxis:a.e}}])}},
    markLine:{{silent:true,symbol:'none',label:{{show:false}},lineStyle:{{color:MUT,type:'dashed'}},data:[{{yAxis:0.5}},{{yAxis:-0.5}}]}}
  }}]
}});
}})();

// 图2 β10
(function(){{
const el=document.getElementById('c4');
const col=(s)=> s==='sig'?OKR:(s==='edge'?'#E8A84C':'#ccc');
echarts.init(el).setOption({{
  grid:{{left:52,right:26,top:22,bottom:64}},
  tooltip:{{formatter:p=>{{const d=BETA[p[0].dataIndex];return `${{d.t}}<br>β₁₀=${{d.lab}} (%/bp)<br>显著性：${{d.sig==='sig'?'显著(p<0.01)':(d.sig==='edge'?'边缘(p<0.05)':'不显著')}}`;}}}},
  xAxis:{{type:'category',data:BETA.map(x=>x.t),axisLabel:{{rotate:35,fontSize:11}},axisTick:{{show:false}}}},
  yAxis:{{type:'value',name:'β₁₀ (%/bp)',splitLine:{{lineStyle:{{color:'#eee'}}}}}},
  series:[{{type:'bar',data:BETA.map(x=>({{value:+(x.b.toFixed(3)),itemStyle:{{color:col(x.sig),borderRadius:[3,3,0,0]}},
    label:{{show:true,position:'top',fontSize:10,color:MUT,formatter:x.lab}}}}
  )),barWidth:'52%'}}]
}});
}})();

// 图3 上行/下行月超额
(function(){{
const el=document.getElementById('c5');
echarts.init(el).setOption({{
  grid:{{left:52,right:16,top:34,bottom:64}},
  tooltip:{{trigger:'axis'}},
  legend:{{data:['US10Y 上行月','US10Y 下行月'],textStyle:{{color:MUT,fontSize:11}}}},
  xAxis:{{type:'category',data:GRP.map(x=>x.t),axisLabel:{{rotate:35,fontSize:11}},axisTick:{{show:false}}}},
  yAxis:{{type:'value',name:'超额 pp/月',splitLine:{{lineStyle:{{color:'#eee'}}}}}},
  series:[
    {{name:'US10Y 上行月',type:'bar',data:GRP.map(x=>+(x.u.toFixed(2))),itemStyle:{{color:OKR}},barWidth:'32%'}},
    {{name:'US10Y 下行月',type:'bar',data:GRP.map(x=>+(x.d.toFixed(2))),itemStyle:{{color:OKG}},barWidth:'32%'}}
  ]
}});
}})();

// 图4 强 vs 弱 El Niño T+12 超额
(function(){{
const el=document.getElementById('c6');
const data = STRWEAK.filter(x=>x.s!=null||x.w!=null);
echarts.init(el).setOption({{
  grid:{{left:52,right:16,top:34,bottom:64}},
  tooltip:{{trigger:'axis'}},
  legend:{{data:['强 El Niño (≥+1.5°C)','弱 El Niño (<+1.5°C)'],textStyle:{{color:MUT,fontSize:11}}}},
  xAxis:{{type:'category',data:data.map(x=>x.t),axisLabel:{{rotate:35,fontSize:11}},axisTick:{{show:false}}}},
  yAxis:{{type:'value',name:'T+12 平均超额 pp',splitLine:{{lineStyle:{{color:'#eee'}}}}}},
  series:[
    {{name:'强 El Niño (≥+1.5°C)',type:'bar',data:data.map(x=>x.s!=null?+(x.s.toFixed(1)):null),itemStyle:{{color:OKC}},barWidth:'30%'}},
    {{name:'弱 El Niño (<+1.5°C)',type:'bar',data:data.map(x=>x.w!=null?+(x.w.toFixed(1)):null),itemStyle:{{color:OKB}},barWidth:'30%'}}
  ]
}});
}})();

// 图5 三档 El Niño：中位最大超额 vs 中位最终超额 + 平均见顶 T+N
(function(){{
const el=document.getElementById('c7');
const d = TIER7;
echarts.init(el).setOption({{
  grid:{{left:56,right:56,top:40,bottom:30}},
  tooltip:{{trigger:'item'}},
  legend:{{data:['中位最大超额 (pp)','中位最终超额 (pp)','平均见顶 T+N (右)'],textStyle:{{color:MUT,fontSize:11}}}},
  xAxis:{{type:'category',data:d.map(x=>x.tier),axisLabel:{{fontSize:12}},axisTick:{{show:false}}}},
  yAxis:[
    {{type:'value',name:'超额 pp',splitLine:{{lineStyle:{{color:'#eee'}}}}}},
    {{type:'value',name:'见顶 T+月',min:0,max:16,splitLine:{{show:false}}}}
  ],
  series:[
    {{name:'中位最大超额 (pp)',type:'bar',data:d.map(x=>x.mx),itemStyle:{{color:OKB}},barWidth:'26%'}},
    {{name:'中位最终超额 (pp)',type:'bar',data:d.map(x=>x.end),itemStyle:{{color:OKC}},barWidth:'26%'}},
    {{name:'平均见顶 T+N (右)',type:'line',yAxisIndex:1,data:d.map(x=>x.pt),itemStyle:{{color:OKP}},lineStyle:{{width:2,color:OKP}},symbolSize:8}}
  ]
}});
}})();

// 四指标明细表：强度 × 股票 双筛选
(function(){{
const ALL='all';
const trSel=document.getElementById('f_tier'), tkSel=document.getElementById('f_tkr'),
      rwSel=document.getElementById('f_rows'), cnt=document.getElementById('f_count'),
      tbody=document.querySelector('#det_tbl tbody');
const tiers=[...new Set(DET.map(x=>x.tr))].sort((a,b)=>a.indexOf('超')>=0?(b.indexOf('超')>=0?a.localeCompare(b):-1):(b.indexOf('超')>=0?1:a.localeCompare(b)));
const tkrs=[...new Set(DET.map(x=>x.t))];
tiers.forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=v;trSel.appendChild(o);}});
tkrs.forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=v;tkSel.appendChild(o);}});
const num=v=>v==='-'||v==='未跌破'?null:parseFloat(v.replace('+','').replace('T+',''));
const clsOf=v=>{{if(v==='-'||v==='未跌破'||v==null)return'';const n=typeof v==='number'?v:parseFloat(v);return n>=0?'up':'down';}};
function render(){{
  const tr=trSel.value, tk=tkSel.value, rw=rwSel.value;
  let rows=DET;
  if(tr!==ALL)rows=rows.filter(r=>r.tr===tr);
  if(tk!==ALL)rows=rows.filter(r=>r.t===tk);
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

out_path = os.path.join(OUT_DIR, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out_path, os.path.getsize(out_path), "bytes")