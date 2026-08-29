# -*- coding: utf-8 -*-
"""
强厄尔尼诺（Strong El Niño）增量分析
- 强度分档：峰值 ONI ≥+1.5 = 强（Strong），≥+2.0 = 超强（Very Strong）
- 强 El Niño 月 vs 普通 El Niño 月 vs La Niña 的月度收益对比
- 强事件 onset 后 T+6/12/24 窗口超额明细（沿用 57 号事件窗口口径）
- 强度-超额相关性：每标的 e12/e24 × 事件 peak ONI
输出 results/agri_strong_el.json
"""
import json
import math
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "agri_strong_el.json")

TICKERS = ["DE", "AGCO", "MOS", "CF", "NTR", "CTVA", "FMC", "ADM", "BG",
           "DAR", "FPI", "TSN", "HRL", "MOO", "DBA"]
SUB = {"DE": "农机", "AGCO": "农机", "MOS": "化肥", "CF": "化肥", "NTR": "化肥",
       "ADM": "粮商", "BG": "粮商", "CTVA": "种子植保", "FMC": "种子植保",
       "DAR": "油脂加工", "FPI": "农业REIT", "TSN": "肉类", "HRL": "肉类",
       "MOO": "农业ETF", "DBA": "商品ETF"}

# ---------- 1. ONI 解析（复用 57 号） ----------
seas_to_mon = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
               "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
oni_rows = []
with open(os.path.join(DATA, "agri", "raw", "oni.txt"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("SEAS") or line.startswith(" SEAS"):
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
            oni_rows.append({"year": int(yr), "month": int(mon), "oni": float(anom)})
oni = pd.DataFrame(oni_rows).sort_values(["year", "month"]).reset_index(drop=True)
oni = oni[(oni["year"] >= 1950) & oni["oni"].notna()].copy()
oni["ym"] = oni["year"].astype(int) * 100 + oni["month"].astype(int)
oni_val = dict(zip(oni["ym"], oni["oni"]))

# El Niño 事件（连续 >=0.5 且长度>=5）+ 事件峰值
def el_events():
    vals = {int(k): float(v) for k, v in oni_val.items()}
    yms = sorted(vals.keys())
    evs = []
    i = 0
    n = len(yms)
    while i < n:
        if vals[yms[i]] >= 0.5:
            j = i
            while j < n and vals[yms[j]] >= 0.5:
                j += 1
            if j - i >= 5:
                evs.append({
                    "onset": int(yms[i]), "end": int(yms[j - 1]),
                    "peak": max(vals[yms[k]] for k in range(i, j)),
                    "len": j - i,
                    "peak_ym": int(yms[i + int(np.argmax([vals[yms[k]] for k in range(i, j)]))]),
                })
            i = j
        else:
            i += 1
    return evs

events = el_events()
strong_evs = [e for e in events if e["peak"] >= 1.5]
vstrong_evs = [e for e in events if e["peak"] >= 2.0]
weak_evs = [e for e in events if e["peak"] < 1.5]

def ym_to_label(ym):
    return f"{int(ym) // 100}-{int(ym) % 100:02d}"

# 月度状态：普通/强/超强 El Niño 月（按日历月推进，仅标注真实存在的 ym）
month_state = {}
for ym in oni_val:
    month_state[ym] = "neutral"
for e in events:
    tag = "el_strong" if e["peak"] >= 1.5 else "el_weak"
    yy, mm = divmod(int(e["onset"]), 100)
    end_yy, end_mm = divmod(int(e["end"]), 100)
    while (yy, mm) <= (end_yy, end_mm):
        ym = yy * 100 + mm
        if ym in month_state:  # 只标真实月份，防幽灵键
            month_state[ym] = tag
        mm += 1
        if mm > 12:
            mm, yy = 1, yy + 1

# ---------- 2. 月度收益 ----------
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

def t_pval(t, df):
    if df >= 30:
        x = abs(float(t))
        if x > 38:
            return 0.0
        b1, b2, b3, b4, b5 = 0.319381530, -0.356563782, 1.781477937, -1.821255978, 1.330274429
        p = 0.2316419
        z = 1.0 / (1.0 + p * x)
        phi = math.exp(-x * x / 2) / math.sqrt(2 * math.pi)
        cdf = 1.0 - phi * (b1 * z + b2 * z ** 2 + b3 * z ** 3 + b4 * z ** 4 + b5 * z ** 5)
        return min(max(2 * (1 - cdf), 0.0), 1.0)
    from math import gamma, sqrt, pi
    x = abs(float(t)) / sqrt(df)
    def f(u):
        return (1 + u * u / df) ** (-(df + 1) / 2.0)
    steps = 300
    h = x / steps
    s = f(0) + f(x)
    for k in range(1, steps):
        s += (4 if k % 2 else 2) * f(k * h)
    area = s * h / 3
    cdf = 0.5 + area * gamma((df + 1) / 2.0) / (sqrt(pi * df) * gamma(df / 2.0))
    return min(max(2 * (1 - cdf), 0.0), 1.0)

def group_stats(ticker, state):
    sub = mrets[ticker][mrets[ticker]["ym"].map(lambda y: month_state.get(y, "neutral")) == state]["ret"]
    if len(sub) < 3:
        return {"n": int(len(sub)), "mean": None}
    mean = float(sub.mean())
    sd = float(sub.std(ddof=1))
    t = mean / (sd / math.sqrt(len(sub))) if sd > 0 else 0.0
    p = t_pval(t, len(sub) - 1)
    sig = "sig" if p < 0.01 else ("edge" if p < 0.05 else "no")
    return {"n": int(len(sub)), "mean": round(mean, 3), "med": round(float(sub.median()), 3),
            "t": round(t, 2), "p": round(p, 4), "sig": sig}

# 状态月数
state_months = {}
for y, s in month_state.items():
    state_months[s] = state_months.get(s, 0) + 1

# ---------- 3. 事件窗口超额 ----------
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

def ev_agg(ev_list, key):
    agg = {t: [] for t in TICKERS}
    for e in ev_list:
        for t in TICKERS:
            c = window_cum(t, e["onset"], {"e6": 6, "e12": 12, "e24": 24}[key])
            s = window_cum("SPY", e["onset"], {"e6": 6, "e12": 12, "e24": 24}[key])
            if c is not None and s is not None:
                agg[t].append({"dv": round(c - s, 1), "peak": e["peak"], "onset": ym_to_label(e["onset"])})
    rows = []
    for t in TICKERS:
        v = agg[t]
        if not v:
            rows.append({"t": t, "sub": SUB[t], "n": 0})
            continue
        vals = [x["dv"] for x in v]
        rows.append({"t": t, "sub": SUB[t], "n": len(vals),
                     "mean": round(float(np.mean(vals)), 1),
                     "med": round(float(np.median(vals)), 1),
                     "win": round(float(np.mean([x > 0 for x in vals])) * 100, 0),
                     "min": round(float(np.min(vals)), 1),
                     "max": round(float(np.max(vals)), 1),
                     "cases": v})
    return rows

strong_rows = {k: ev_agg([e for e in strong_evs], k) for k in ("e6", "e12", "e24")}
weak_rows = {k: ev_agg(weak_evs, k) for k in ("e6", "e12", "e24")}

# ---------- 4. 强度-超额相关性 ----------
corr_rows = []
for t in TICKERS:
    pairs = []
    for e in events:
        c = window_cum(t, e["onset"], 12)
        s = window_cum("SPY", e["onset"], 12)
        if c is not None and s is not None:
            pairs.append((e["peak"], c - s))
    if len(pairs) >= 5:
        xs = np.array([p[0] for p in pairs], dtype=float)
        ys = np.array([p[1] for p in pairs], dtype=float)
        r = float(np.corrcoef(xs, ys)[0, 1]) if np.std(ys) > 0 else 0.0
        # 线性回归斜率（excess vs peak）
        slope, intercept = np.polyfit(xs, ys, 1)
        n = len(pairs)
        corr_rows.append({"t": t, "sub": SUB[t], "n": n,
                          "corr_peak_e12": round(r, 3),
                          "slope": round(float(slope), 2),
                          "p": round(t_pval(r * math.sqrt((n - 2) / max(1 - r * r, 1e-9)), n - 2), 4)
                          if abs(r) < 1 else 0.0})

# 强 vs 弱事件 T+12 超额对比（汇总）
strong_t12_rows = [r for r in strong_rows["e12"] if r["n"] > 0]
weak_t12_rows = [r for r in weak_rows["e12"] if r["n"] > 0]
def to_dict_list(rows):
    return [{"t": r["t"], "sub": r["sub"], "n": r["n"], "mean": r["mean"],
             "med": r["med"], "win": r["win"], "min": r.get("min"), "max": r.get("max")}
            for r in rows]

out = {
    "strong_events": [{"onset": ym_to_label(e["onset"]), "end": ym_to_label(e["end"]),
                       "peak": round(e["peak"], 2), "len": e["len"],
                       "peak_ym": ym_to_label(e["peak_ym"])} for e in strong_evs],
    "vstrong_events": [{"onset": ym_to_label(e["onset"]), "end": ym_to_label(e["end"]),
                        "peak": round(e["peak"], 2), "len": e["len"],
                        "peak_ym": ym_to_label(e["peak_ym"])} for e in vstrong_evs],
    "all_events": [{"onset": ym_to_label(e["onset"]), "end": ym_to_label(e["end"]),
                    "peak": round(e["peak"], 2), "len": e["len"]} for e in events],
    "state_months": state_months,
    "group": {t: {"strong_el": group_stats(t, "el_strong"),
                  "weak_el": group_stats(t, "el_weak"),
                  "neutral": group_stats(t, "neutral")}
              for t in TICKERS},
    "strong_el_rows": {k: to_dict_list(strong_rows[k]) for k in ("e6", "e12", "e24")},
    "weak_el_rows": {k: to_dict_list(weak_rows[k]) for k in ("e6", "e12", "e24")},
    "strong_detail": {t: strong_rows["e12"].get(t) if isinstance(strong_rows["e12"], dict) else None for t in []},
    "corr_peak": corr_rows,
    "meta": {"n_all": len(events), "n_strong": len(strong_evs), "n_vstrong": len(vstrong_evs),
             "n_weak": len(weak_evs)},
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT, os.path.getsize(OUT), "bytes")
print("all:", len(events), "strong:", len(strong_evs), "vstrong:", len(vstrong_evs), "weak:", len(weak_evs))
for e in strong_evs:
    print(ym_to_label(e["onset"]), "~", ym_to_label(e["end"]), "peak", round(e["peak"], 2), "len", e["len"])