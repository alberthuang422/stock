# -*- coding: utf-8 -*-
"""
农业股 × 厄尔尼诺（ENSO）量化回测
- ONI 月度化（3 个月滑动 SST 异常，按季中点落月）
- ENSO 状态：El Niño(ONI>=0.5 连续>=5月) / La Niña(ONI<=-0.5 连续>=5月) / 中性
- 月度收益按状态分组（均值/中位数/t 检验/超额 vs SPY）
- El Niño 事件窗口：onset 后 T+6/12/24 累计收益与超额
"""
import json
import math
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "agri_enso.json")

# ---------- 1. ONI 解析 ----------
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
            seas, yr, total, anom = parts[0], int(parts[1]), float(parts[2]), float(parts[3])
        except (ValueError, IndexError):
            continue
        mon = seas_to_mon.get(seas)
        if mon is None:
            continue
        oni_rows.append({"year": yr, "month": mon, "oni": anom})
oni = pd.DataFrame(oni_rows).sort_values(["year", "month"]).reset_index(drop=True)

# 去掉首尾不完整的（NDJ 需要下一年 1 月等，前面已自然连续生成）
# ONI 连续季度流：最后一个 NDJ 无法映射到真实月份则跳过
oni = oni[(oni["year"] >= 1950) & (oni["oni"].notna())]
oni["ym"] = oni["year"] * 100 + oni["month"]

def ensos(oni_df):
    """返回每月的 ENSO 状态字符串"""
    states = {}
    vals = {}
    for _, r in oni_df.iterrows():
        states[r["ym"]] = "onset?"  # placeholder
        vals[r["ym"]] = r["oni"]
    yms = sorted(states.keys())
    # 连续段扫描
    result = {}
    i = 0
    n = len(yms)
    while i < n:
        if vals[yms[i]] >= 0.5:
            j = i
            while j < n and vals[yms[j]] >= 0.5:
                j += 1
            length = j - i
            tag = "el" if length >= 5 else "mix"
            for k in range(i, j):
                result[yms[k]] = tag
            i = j
        elif vals[yms[i]] <= -0.5:
            j = i
            while j < n and vals[yms[j]] <= -0.5:
                j += 1
            length = j - i
            tag = "la" if length >= 5 else "mix"
            for k in range(i, j):
                result[yms[k]] = tag
            i = j
        else:
            result[yms[i]] = "neu"
            i += 1
    return result, vals

enmap, oni_val = ensos(oni)

# 事件列表（严格 El Niño：连续>=5）
def events(oni_df, polarity):
    vals = {}
    for _, r in oni_df.iterrows():
        vals[r["ym"]] = r["oni"]
    yms = sorted(vals.keys())
    evs = []
    i = 0
    n = len(yms)
    while i < n:
        cond = vals[yms[i]] >= 0.5 if polarity == "el" else vals[yms[i]] <= -0.5
        if cond:
            j = i
            while j < n and (vals[yms[j]] >= 0.5 if polarity == "el" else vals[yms[j]] <= -0.5):
                j += 1
            if j - i >= 5:
                evs.append({"onset": yms[i], "end": yms[j - 1],
                            "peak": max(vals[yms[k]] for k in range(i, j)) if polarity == "el"
                                    else min(vals[yms[k]] for k in range(i, j)),
                            "len": j - i})
            i = j
        else:
            i += 1
    return evs

el_events = events(oni, "el")
la_events = events(oni, "la")

# ---------- 2. 月度收益 ----------
TICKERS = ["ADM", "BG", "MOS", "CF", "NTR", "CTVA", "AGCO", "FMC", "DAR",
           "FPI", "TSN", "HRL", "MOO", "DBA", "DE", "SPY"]
SUB = {"DE": "农机", "AGCO": "农机", "MOS": "化肥", "CF": "化肥", "NTR": "化肥",
       "ADM": "粮商", "BG": "粮商", "CTVA": "种子植保", "FMC": "种子植保",
       "DAR": "油脂加工", "FPI": "农业REIT", "TSN": "肉类", "HRL": "肉类",
       "MOO": "农业ETF", "DBA": "商品ETF"}

def monthly_df(ticker):
    path = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    m = df["adj_close"].resample("ME").last()  # 月末值
    m = m.dropna()
    ret = m.pct_change().dropna() * 100
    r = pd.DataFrame({"ret": ret})
    r["ym"] = r.index.year * 100 + r.index.month
    return r

mrets = {t: monthly_df(t) for t in TICKERS}

# ---------- 3. 分组统计 ----------
def tstat(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 3:
        return None, None, None
    mean = x.mean()
    sd = x.std(ddof=1)
    if sd == 0 or math.isnan(sd):
        return mean, 0.0, 1.0
    t = mean / (sd / math.sqrt(n))
    p = 2 * (1 - _t_cdf(abs(t), n - 1))
    return mean, t, p

def _t_cdf(t, df):
    # 近似 Student t CDF（数值积分不引入 scipy）
    from math import gamma, sqrt, pi
    x = t / sqrt(df)
    def f(u):
        return (1 + u * u / df) ** (-(df + 1) / 2.0)
    # Simpson 0~x
    steps = 200
    h = x / steps
    s = f(0) + f(x)
    for k in range(1, steps):
        s += (4 if k % 2 else 2) * f(k * h)
    area = s * h / 3
    cdf = 0.5 + area * gamma((df + 1) / 2.0) / (sqrt(pi * df) * gamma(df / 2.0))
    return min(max(cdf, 0.0), 1.0)

def group_stats(ticker, state):
    df = mrets[ticker]
    sub = df[df["ym"].map(lambda y: enmap.get(y, "neu")) == state]["ret"]
    if len(sub) == 0:
        return {"n": 0}
    mean, t, p = tstat(sub.values)
    sp = mrets["SPY"].copy()
    spsub = sp[sp["ym"].map(lambda y: enmap.get(y, "neu")) == state]["ret"]
    ex = mean - (spsub.mean() if len(spsub) else np.nan)
    out = {"n": int(len(sub)), "mean": round(float(sub.mean()), 3),
           "med": round(float(sub.median()), 3),
           "t": round(float(t), 2) if t is not None else None,
           "p": round(float(p), 4) if p is not None else None,
           "excess_spy": round(float(ex), 3)}
    if out["p"] is not None:
        out["sig"] = "sig" if p < 0.01 else ("edge" if p < 0.05 else "no")
    return out

group_res = {}
for t in TICKERS:
    group_res[t] = {"el": group_stats(t, "el"), "la": group_stats(t, "la"),
                    "neu": group_stats(t, "neu")}

# 状态占比
def state_share():
    tot = len(enmap)
    c = {s: sum(1 for v in enmap.values() if v == s) for s in ["el", "la", "neu"]}
    return {k: {"n": v, "pct": round(v / tot * 100, 1)} for k, v in c.items()}

# ---------- 4. 事件窗口 ----------
def window_cum(ticker, onset_ym, months):
    df = mrets[ticker]
    cy = onset_ym
    if cy not in set(df["ym"]):
        return None
    # 累计 = 复利叠乘月收益（onset 月起 months 个月）
    sub = df[(df["ym"] >= cy) & (df["ym"] < cy + months * 1.001 if months < 100 else df["ym"] >= cy)]
    # 修正：月份推进用日历年月步进
    yy, mm = divmod(int(onset_ym), 100)
    end_ym = None
    for _ in range(months):
        mm += 1
        if mm > 12:
            mm = 1
            yy += 1
    end_ym = yy * 100 + mm
    sub = df[(df["ym"] >= onset_ym) & (df["ym"] < end_ym)]["ret"]
    if len(sub) < max(2, months - 2):
        return None
    cum = float((1 + sub / 100.0).prod() - 1) * 100
    return cum

ev_res = []
for ev in el_events:
    onset = ev["onset"]
    yy, mm = divmod(int(onset), 100)
    label = f"{int(yy)}-{int(mm):02d}"
    entry = {"onset": label, "end": f"{int(divmod(int(ev['end']),100)[0])}-{int(divmod(int(ev['end']),100)[1]):02d}",
             "peak_oni": round(ev["peak"], 2), "len_m": ev["len"],
             "stocks": {}}
    for t in TICKERS:
        if t == "SPY":
            continue
        c6 = window_cum(t, onset, 6)
        c12 = window_cum(t, onset, 12)
        c24 = window_cum(t, onset, 24)
        s6 = window_cum("SPY", onset, 6)
        s12 = window_cum("SPY", onset, 12)
        s24 = window_cum("SPY", onset, 24)
        d = {}
        if c6 is not None and s6 is not None:
            d["r6"], d["e6"] = round(c6, 1), round(c6 - s6, 1)
        if c12 is not None and s12 is not None:
            d["r12"], d["e12"] = round(c12, 1), round(c12 - s12, 1)
        if c24 is not None and s24 is not None:
            d["r24"], d["e24"] = round(c24, 1), round(c24 - s24, 1)
        if d:
            entry["stocks"][t] = d
    ev_res.append(entry)

# 事件平均超额（用于汇总表）
def ev_avg(evs, key):
    agg = {}
    for ev in evs:
        for t, d in ev["stocks"].items():
            if key in d:
                agg.setdefault(t, []).append(d[key])
    out = {}
    for t, vals in agg.items():
        out[t] = {"n": len(vals), "mean": round(float(np.mean(vals)), 1),
                  "med": round(float(np.median(vals)), 1),
                  "win": round(float(np.mean([v > 0 for v in vals])) * 100, 0)}
    return out

ev_avg6 = ev_avg(ev_res, "e6")
ev_avg12 = ev_avg(ev_res, "e12")
ev_avg24 = ev_avg(ev_res, "e24")

# La Niña 对照（简：窗口超额）
la_res = []
for ev in la_events:
    onset = ev["onset"]
    if onset < 199001:  # 只统计有股票数据的时期
        continue
    yy, mm = divmod(int(onset), 100)
    la_res.append({"onset": f"{int(yy)}-{int(mm):02d}",
                   "peak_oni": round(ev["peak"], 2), "len_m": ev["len"]})
# La Niña 对照（窗口超额，显式循环）
la_stocks = {t: [] for t in TICKERS if t != "SPY"}
for e in la_events:
    onset = int(e["onset"])
    if onset < 199001:
        continue
    for t in TICKERS:
        if t == "SPY":
            continue
        c12 = window_cum(t, onset, 12)
        s12 = window_cum("SPY", onset, 12)
        if c12 is not None and s12 is not None:
            la_stocks[t].append(round(c12 - s12, 1))
la_avg12 = {t: {"n": len(v), "mean": round(float(np.mean(v)), 1),
                "med": round(float(np.median(v)), 1),
                "win": round(float(np.mean([x > 0 for x in v])) * 100, 0)}
            for t, v in la_stocks.items() if len(v) > 0}

out = {
    "group": group_res,
    "state_share": state_share(),
    "el_events": ev_res,
    "la_events": la_res,
    "ev_avg6": ev_avg6,
    "ev_avg12": ev_avg12,
    "ev_avg24": ev_avg24,
    "la_avg12": la_avg12,
    "subsector": SUB,
    "meta": {"oni_range": f"{oni['year'].min()}-{oni['year'].max()}",
             "n_el_events": len(ev_res), "n_la_events_1990": len(la_res)}
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT, os.path.getsize(OUT), "bytes")
print("El Niño events:", len(ev_res), " La Niña events(1990+):", len(la_res))