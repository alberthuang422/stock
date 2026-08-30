# -*- coding: utf-8 -*-
"""
57 号报告绝对收益口径重算（超额 → 绝对）
板块：
  A. ENSO 状态分组绝对月均收益（scipy t 检验 vs 0，修正旧脚本手写 t CDF 的 p 值 bug）
  B. 拉尼娜事件 onset 后 T+12 绝对累计收益（原 la_avg12 为超额口径，须重算）
  C. 厄尔尼诺事件 T+6/12/24 绝对累计（从 agri_enso.json el_events 的 r6/r12/r24 聚合，本身即绝对）
  D. 强厄尔尼诺三档路径四指标绝对版（max/期末/见顶 T+/回撤，不减 SPY；含 SPY 参照）
  E. 利率上行/下行/平坦月绝对收益（rate_sens groups 的 mean 本就是绝对，取出来附 SPY）
输出 results/agri_absolute.json
"""
import json
import os
import pandas as pd
import numpy as np
from scipy import stats as sps

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
RES = os.path.join(BASE, "results")
OUT = os.path.join(RES, "agri_absolute.json")

TICKERS = ["DE", "AGCO", "MOS", "CF", "NTR", "CTVA", "FMC", "ADM", "BG",
           "DAR", "FPI", "TSN", "HRL", "MOO", "DBA"]
SUB = {"DE": "农机", "AGCO": "农机", "MOS": "化肥", "CF": "化肥", "NTR": "化肥",
       "ADM": "粮商", "BG": "粮商", "CTVA": "种子植保", "FMC": "种子植保",
       "DAR": "油脂加工", "FPI": "农业REIT", "TSN": "肉类", "HRL": "肉类",
       "MOO": "农业ETF", "DBA": "商品ETF"}

def sig_of(p):
    return "sig" if p < 0.01 else ("edge" if p < 0.05 else "no")

def monthly_df(ticker):
    path = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    m = df["adj_close"].resample("ME").last().dropna()
    ret = m.pct_change().dropna() * 100
    r = pd.DataFrame({"ret": ret})
    r["ym"] = r.index.year.astype(int) * 100 + r.index.month.astype(int)
    return r

mrets = {t: monthly_df(t) for t in TICKERS}
mrets["SPY"] = monthly_df("SPY")

# ---------- ONI + 事件（与 agri_runup_analyze.py 同口径） ----------
seas_to_mon = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
               "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
oni_rows = []
with open(os.path.join(DATA, "agri", "raw", "oni.txt"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("SEAS"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            seas, yr, anom = parts[0], int(parts[1]), float(parts[3])
        except (ValueError, IndexError):
            continue
        mon = seas_to_mon.get(seas)
        if mon is not None:
            oni_rows.append({"year": yr, "month": mon, "oni": anom})
oni = pd.DataFrame(oni_rows).sort_values(["year", "month"]).reset_index(drop=True)
oni = oni[(oni["year"] >= 1950) & oni["oni"].notna()].copy()
oni["ym"] = oni["year"].astype(int) * 100 + oni["month"].astype(int)

def scan_events(polarity):
    vals = dict(zip(oni["ym"], oni["oni"]))
    yms = sorted(vals.keys())
    evs, i, n = [], 0, len(yms)
    while i < n:
        cond = vals[yms[i]] >= 0.5 if polarity == "el" else vals[yms[i]] <= -0.5
        if cond:
            j = i
            while j < n and (vals[yms[j]] >= 0.5 if polarity == "el" else vals[yms[j]] <= -0.5):
                j += 1
            if j - i >= 5:
                evs.append({"onset": int(yms[i]), "end": int(yms[j - 1]),
                            "peak": max(vals[yms[k]] for k in range(i, j)) if polarity == "el"
                                    else min(vals[yms[k]] for k in range(i, j)),
                            "len": j - i})
            i = j
        else:
            i += 1
    return evs

el_events = scan_events("el")
la_events = [e for e in scan_events("la") if e["onset"] >= 199001]

# ENSO 状态映射（分组用，与 agri_enso_analyze.py ensos() 同逻辑）
def build_states():
    vals = dict(zip(oni["ym"], oni["oni"]))
    yms = sorted(vals.keys())
    result, i, n = {}, 0, len(yms)
    while i < n:
        if vals[yms[i]] >= 0.5:
            j = i
            while j < n and vals[yms[j]] >= 0.5:
                j += 1
            tag = "el" if j - i >= 5 else "mix"
            for k in range(i, j):
                result[yms[k]] = tag
            i = j
        elif vals[yms[i]] <= -0.5:
            j = i
            while j < n and vals[yms[j]] <= -0.5:
                j += 1
            tag = "la" if j - i >= 5 else "mix"
            for k in range(i, j):
                result[yms[k]] = tag
            i = j
        else:
            result[yms[i]] = "neu"
            i += 1
    return result

enmap = build_states()

# ---------- A. ENSO 分组绝对月均收益（scipy t 检验 vs 0） ----------
group_abs = {}
for t in TICKERS + ["SPY"]:
    df = mrets[t]
    group_abs[t] = {}
    for st in ("el", "la", "neu"):
        sub = df[df["ym"].map(lambda y: enmap.get(y, "neu")) == st]["ret"].dropna()
        if len(sub) < 3:
            group_abs[t][st] = {"n": int(len(sub))}
            continue
        tt = sps.ttest_1samp(sub.values, 0.0)
        group_abs[t][st] = {"n": int(len(sub)), "mean": round(float(sub.mean()), 3),
                            "med": round(float(sub.median()), 3),
                            "t": round(float(tt.statistic), 2), "p": round(float(tt.pvalue), 4),
                            "sig": sig_of(float(tt.pvalue))}

# ---------- 窗口绝对累计（复利，与主口径 window_cum 相同） ----------
def window_cum(ticker, onset_ym, months):
    df = mrets[ticker]
    cy = int(onset_ym)
    if cy not in set(df["ym"]):
        return None
    yy, mm = divmod(cy, 100)
    for _ in range(months):
        mm += 1
        if mm > 12:
            mm, yy = 1, yy + 1
    end_ym = yy * 100 + mm
    sub = df[(df["ym"] >= cy) & (df["ym"] < end_ym)]["ret"]
    if len(sub) < max(2, months - 2):
        return None
    return float((1 + sub / 100.0).prod() - 1) * 100

def agg_wins(vals):
    if not vals:
        return None
    return {"n": len(vals), "mean": round(float(np.mean(vals)), 1),
            "med": round(float(np.median(vals)), 1),
            "win": round(float(np.mean([v > 0 for v in vals])) * 100, 0)}

# ---------- B. 拉尼娜 T+12 绝对累计 ----------
la_abs12 = {}
for t in TICKERS + ["SPY"]:
    vals = []
    for e in la_events:
        c = window_cum(t, e["onset"], 12)
        if c is not None:
            vals.append(round(c, 1))
    la_abs12[t] = agg_wins(vals) or {"n": 0}

# ---------- C. 厄尔尼诺 T+6/12/24 绝对累计（直接重算，保证口径一致） ----------
el_abs = {"r6": {}, "r12": {}, "r24": {}}
for t in TICKERS + ["SPY"]:
    for w in (6, 12, 24):
        vals = []
        for e in el_events:
            c = window_cum(t, e["onset"], w)
            if c is not None:
                vals.append(round(c, 1))
        el_abs[f"r{w}"][t] = agg_wins(vals) or {"n": 0}

# ---------- D. 强厄尔尼诺三档路径四指标（绝对版） ----------
DD_TOL, WINDOW = 5.0, 24

def tier_of(peak):
    if peak >= 2.0:
        return "vstrong"
    if peak >= 1.5:
        return "strong"
    return "weak"

def path_metrics_abs(ticker, onset_ym, months):
    df = mrets[ticker]
    cy = int(onset_ym)
    if cy not in set(df["ym"]):
        return None
    yy, mm = divmod(cy, 100)
    for _ in range(months):
        mm += 1
        if mm > 12:
            mm, yy = 1, yy + 1
    end_ym = yy * 100 + mm
    sub = df[(df["ym"] >= cy) & (df["ym"] < end_ym)]["ret"]
    if len(sub) < max(2, months - 2):
        return None
    acc, path = 1.0, []
    for r in sub:
        acc *= (1 + r / 100.0)
        path.append((acc - 1) * 100)
    peak, pidx = max(path), int(np.argmax(path))
    dd_start = None
    for k in range(pidx + 1, len(path)):
        if path[k] < peak - DD_TOL:
            dd_start = k + 1
            break
    return {"max": round(peak, 1), "peak_t": pidx + 1, "dd_start_t": dd_start,
            "end": round(path[-1], 1),
            "end12": round(path[11], 1) if len(path) >= 12 else None,
            "dd": round(peak - path[-1], 1)}

ev_recs = []
for e in el_events:
    rec = {"onset": e["onset"], "tier": tier_of(e["peak"]), "oni_peak": round(e["peak"], 2),
           "tickers": {}}
    for t in TICKERS + ["SPY"]:
        st = path_metrics_abs(t, e["onset"], WINDOW)
        if st:
            rec["tickers"][t] = st
    ev_recs.append(rec)

TIER_CN = {"weak": "弱厄尔尼诺(<+1.5°C)", "strong": "强厄尔尼诺(1.5~2.0°C)",
           "vstrong": "超强厄尔尼诺(≥2.0°C)"}

def block_stats(rows):
    if not rows:
        return None
    return {"n": len(rows),
            "avg_max": round(float(np.mean([x["max"] for x in rows])), 1),
            "med_max": round(float(np.median([x["max"] for x in rows])), 1),
            "avg_end": round(float(np.mean([x["end"] for x in rows])), 1),
            "med_end": round(float(np.median([x["end"] for x in rows])), 1),
            "avg_dd": round(float(np.mean([x["dd"] for x in rows])), 1),
            "avg_peak_t": round(float(np.mean([x["peak_t"] for x in rows])), 1),
            "avg_dd_start": round(float(np.mean([x["dd_start_t"] for x in rows if x["dd_start_t"]])), 1)
            if any(x["dd_start_t"] for x in rows) else None,
            "n_updown_pct": round(float(np.mean([x["max"] > 0 and x["end"] < 0 for x in rows])) * 100, 0),
            "n_alldown_pct": round(float(np.mean([x["max"] <= 0 for x in rows])) * 100, 0)}

tier_path_abs = {}
for tr in ("weak", "strong", "vstrong"):
    rows = []
    for r in ev_recs:
        if r["tier"] == tr:
            rows += list(r["tickers"].values())
    tier_path_abs[tr] = {"tier_cn": TIER_CN[tr],
                         "n_ev": sum(1 for r in ev_recs if r["tier"] == tr),
                         **(block_stats(rows) or {"n": 0})}

by_ticker_tier_abs = {}
for t in TICKERS + ["SPY"]:
    by_ticker_tier_abs[t] = {}
    for tr in ("weak", "strong", "vstrong", "all"):
        rows = []
        for r in ev_recs:
            if tr != "all" and r["tier"] != tr:
                continue
            if t in r["tickers"]:
                rows.append(r["tickers"][t])
        by_ticker_tier_abs[t][tr] = block_stats(rows) or {"n": 0}

# 事件明细（绝对，供报告明细表/复用）
events_detail_abs = []
for r in ev_recs:
    if not r["tickers"]:
        continue
    det = {"onset": f"{r['onset']//100}-{r['onset']%100:02d}", "tier": TIER_CN[r["tier"]],
           "oni_peak": r["oni_peak"], "tickers": {}}
    for t, v in r["tickers"].items():
        det["tickers"][t] = v
    events_detail_abs.append(det)

# ---------- E. 利率分组绝对收益（rate_sens groups 的 mean 本就是绝对口径） ----------
rate = json.load(open(os.path.join(RES, "agri_rate_sens.json"), encoding="utf-8"))
rate_abs = {}
for t in TICKERS + ["SPY"]:
    src = rate["groups"].get(t, {})
    rate_abs[t] = {}
    for k in ("up", "dn", "flat"):
        v = src.get(k)
        if not v:
            rate_abs[t][k] = None
        else:
            rate_abs[t][k] = {"n": v["n"], "mean": v["mean"], "med": v["med"], "win": v["win"]}

# ---------- 旧 p 值对照（暴露 bug） ----------
old = json.load(open(os.path.join(RES, "agri_enso.json"), encoding="utf-8"))
p_check = []
for t in TICKERS:
    for st in ("el", "la", "neu"):
        o, n = old["group"][t].get(st, {}), group_abs[t].get(st, {})
        if o.get("p") is not None and n.get("p") is not None:
            p_check.append({"t": t, "st": st, "t_old": o.get("t"), "t_new": n.get("t"),
                            "p_old": o.get("p"), "p_new": n.get("p")})

out = {
    "group_abs": group_abs,
    "la_abs12": la_abs12,
    "el_abs": el_abs,
    "tier_path_abs": tier_path_abs,
    "by_ticker_tier_abs": by_ticker_tier_abs,
    "events_detail_abs": events_detail_abs,
    "rate_abs": rate_abs,
    "p_check": p_check,
    "subsector": SUB,
    "meta": {"n_el": len(el_events), "n_la_1990": len(la_events),
             "window_months": WINDOW, "dd_tol_pp": DD_TOL,
             "note": "绝对口径：不减 SPY；窗口=onset 起复利累计；t 检验=scipy ttest_1samp vs 0（修正旧脚本手写 t CDF 的 p 值）"},
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT, os.path.getsize(OUT), "bytes")

# ---------- 摘要打印 ----------
print("\n== A 分组绝对月均（拉尼娜）==")
for t in ["CF", "MOS", "NTR", "BG", "ADM", "DE", "TSN", "SPY"]:
    v = group_abs[t]["la"]
    print(f"  {t:5s} mean={v.get('mean')} med={v.get('med')} t={v.get('t')} p={v.get('p')} (n={v.get('n')})")
print("\n== B 拉尼娜 T+12 绝对 ==")
for t in ["CF", "MOS", "NTR", "BG", "DE", "TSN", "SPY"]:
    print(f"  {t:5s} {la_abs12[t]}")
print("\n== C 厄尔尼诺 T+12 绝对 ==")
for t in ["DE", "DAR", "CF", "MOS", "SPY"]:
    print(f"  {t:5s} {el_abs['r12'][t]}")
print("\n== D 三档绝对路径 ==")
for tr, v in tier_path_abs.items():
    print(f"  {v['tier_cn']}: n={v['n']} med_max={v['med_max']} med_end={v['med_end']} "
          f"avg_peak_t=T+{v['avg_peak_t']} 冲高转负{v['n_updown_pct']}%")
print("\n== p 值对照（旧 vs 新，仅列差异大的）==")
ndiff = sum(1 for x in p_check if x["p_old"] is not None and x["p_new"] is not None and abs(x["p_old"] - x["p_new"]) > 0.1)
print(f"  差异>0.1 的组合数: {ndiff}/{len(p_check)}")
