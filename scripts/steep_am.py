#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资管公司（APO/BX/KKR/BLK/TROW）在 10Y-2Y 利差（slope = DGS10 - DGS2）走阔时期的表现
主口径：月频 Δslope > 0（宽松）；Δslope ≥ +10bp（显著）；Δslope ≥ +20bp（强）
对照：Δslope < 0（收窄）；Δslope ≤ -10bp（显著收窄）
类型分解（走阔月）：熊陡(2Y↓10Y↑) / 牛陡(2Y↓10Y↓) / 加息陡(2Y↑10Y↑)
标的：apo/bx/kkr（另类资管，点名）+ blk/trow（传统资管对照）+ jpm/bac/ms（银行对照）+ spy（基准）
组合：am3 = apo/bx/kkr 等权；trad2 = blk/trow 等权；bank3 = jpm/bac/ms 等权
窗口：收益率 1976-07 起；股票受上市时间限制（APO 2011-03、BX 2007-06、KKR 2010-07、BLK 1999-10、TROW 1986-03、JPM/BAC/MS 1980/1990/1993）
为排除上市窗口差异，额外输出 2011-11 起的同窗口对照段（所有标的全可用）。
"""
import pandas as pd
import numpy as np
import json, os, glob

DATA = r"C:\Users\Administrator\Desktop\stock\data"
OUT = r"C:\Users\Administrator\Desktop\stock\results"
os.makedirs(OUT, exist_ok=True)

SYMS = ["apo", "bx", "kkr", "blk", "trow", "jpm", "bac", "ms", "spy"]
AM = ["apo", "bx", "kkr"]
TRAD = ["blk", "trow"]
BANK = ["jpm", "bac", "ms"]
SYM_NAMES = {"apo": "APO", "bx": "BX", "kkr": "KKR", "blk": "BLK", "trow": "TROW",
             "jpm": "JPM", "bac": "BAC", "ms": "MS", "spy": "SPY/S&P500",
             "am3": "另类资管3(APO/BX/KKR)", "trad2": "传统资管2(BLK/TROW)", "bank3": "银行3(JPM/BAC/MS)"}
COMBO = ["am3", "trad2", "bank3"]


def load_yield(name):
    df = pd.read_csv(os.path.join(DATA, f"{name}.csv"), parse_dates=["observation_date"])
    df.columns = ["date", "y"]
    df = df.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    return df.dropna().reset_index(drop=True)


def load_stock(name):
    cands = [p for p in glob.glob(os.path.join(DATA, name, "*.csv"))
             if not os.path.basename(p).startswith("BATS_")]
    f = sorted(cands)[0]
    df = pd.read_csv(f, parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    return df.dropna().sort_values("date").reset_index(drop=True)


# ---------- 1. 数据 ----------
d2 = load_yield("dgs2")    # 1976-06 起
d10 = load_yield("dgs10")  # 1962 起
stocks = {s: load_stock(s) for s in SYMS}


def monthly_last(df):
    return df.set_index("date")["y"].resample("ME").last().dropna()


m2 = monthly_last(d2)
m10 = monthly_last(d10)
monthly = pd.DataFrame({"y2": m2, "y10": m10}).dropna()
monthly["slope"] = monthly["y10"] - monthly["y2"]
monthly["dslope"] = monthly["slope"].diff()
monthly["d2"] = monthly["y2"].diff()
monthly["d10"] = monthly["y10"].diff()
monthly = monthly.dropna()
monthly["slope"] = monthly["y10"] - monthly["y2"]
monthly = monthly[monthly.index <= "2026-07-31"]


def month_edges(df):
    df = df.copy()
    df["ym"] = df["date"].dt.to_period("M")
    return df.groupby("ym")["date"].min(), df.groupby("ym")["date"].max()


edges = {s: month_edges(stocks[s]) for s in SYMS}


def ret_in_window(sym, start, end):
    df = stocks[sym]
    s = df[df["date"] >= start]
    if s.empty: return None
    e = df[df["date"] <= end]
    if e.empty: return None
    a, b = s.iloc[0]["px"], e.iloc[-1]["px"]
    if a <= 0 or b <= 0: return None
    return b / a - 1.0


def ret_over_period(sym, months):
    if not months: return None
    if sym == "am3":
        vals = [ret_over_period(s, months) for s in AM]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None
    if sym == "trad2":
        vals = [ret_over_period(s, months) for s in TRAD]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None
    if sym == "bank3":
        vals = [ret_over_period(s, months) for s in BANK]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None
    first, last = edges[sym]
    start, end = first.get(months[0]), last.get(months[-1])
    if start is None or end is None: return None
    return ret_in_window(sym, start, end)


# ---------- 3. 时期识别 ----------
def find_episodes(cond):
    eps, cur = [], []
    for i, idx in enumerate(monthly.index):
        if cond.iloc[i]:
            cur.append(idx)
        else:
            if cur: eps.append(cur); cur = []
    if cur: eps.append(cur)
    return eps


def classify(y2c, y10c):
    if y2c < 0 and y10c > 0: return "熊陡(2Y降10Y升)"
    if y2c < 0 and y10c <= 0: return "牛陡(2Y降10Y降)"
    return "加息陡(2Y升10Y升)"


ALL_SYMS = SYMS + COMBO


def describe_episode(months):
    sub = monthly.loc[months]
    start, end = months[0], months[-1]
    if len(months) == 1:
        y2c, y10c = sub.iloc[0]["d2"], sub.iloc[0]["d10"]
    else:
        y2c = monthly.loc[end, "y2"] - monthly.loc[start, "y2"]
        y10c = monthly.loc[end, "y10"] - monthly.loc[start, "y10"]
    sc = y10c - y2c
    typ = classify(y2c, y10c)
    row = {
        "start": str(start), "end": str(end), "months": len(months),
        "y2_chg": round(y2c * 100, 2), "y10_chg": round(y10c * 100, 2),
        "slope_chg": round(sc * 100, 2), "type": typ,
    }
    for sym in ALL_SYMS:
        r = ret_over_period(sym, months)
        row[f"ret_{sym}"] = round(r * 100, 2) if r is not None else None
    g = row.get("ret_spy")
    for sym in ALL_SYMS:
        if sym == "spy": continue
        if row.get(f"ret_{sym}") is not None and g is not None:
            row[f"xs_{sym}"] = round(row[f"ret_{sym}"] - g, 2)
        else:
            row[f"xs_{sym}"] = None
    return row


def build_table(cond):
    return [describe_episode(m) for m in find_episodes(cond)]


t_up = build_table(monthly["dslope"] > 0)
t_up_sig = build_table(monthly["dslope"] >= 0.10)
t_up_strong = build_table(monthly["dslope"] >= 0.20)
t_down = build_table(monthly["dslope"] < 0)
t_down_sig = build_table(monthly["dslope"] <= -0.10)


# ---------- 4. 汇总统计 ----------
def summarize(rows):
    n = len(rows)
    out = {"n_episodes": n}
    if not rows:
        for sym in ALL_SYMS:
            out[sym] = None
        return out
    for sym in ALL_SYMS:
        vals = [r[f"ret_{sym}"] for r in rows if r.get(f"ret_{sym}") is not None]
        xsv = [r[f"xs_{sym}"] for r in rows if r.get(f"xs_{sym}") is not None]
        if not vals:
            out[sym] = None; continue
        out[sym] = {
            "n": len(vals),
            "win_rate": round(np.mean([v > 0 for v in vals]) * 100, 1),
            "median": round(np.median(vals), 2),
            "mean": round(np.mean(vals), 2),
            "min": round(min(vals), 2), "max": round(max(vals), 2),
        }
        if xsv:
            out[sym]["xs_median"] = round(np.median(xsv), 2)
            out[sym]["xs_win_rate"] = round(np.mean([v > 0 for v in xsv]) * 100, 1)
    return out


sum_up = summarize(t_up)
sum_up_sig = summarize(t_up_sig)
sum_up_strong = summarize(t_up_strong)
sum_down = summarize(t_down)
sum_down_sig = summarize(t_down_sig)


# 全月基准（任意月份收益分布）
def all_month_ret(sym):
    out = []
    for idx in monthly.index:
        r = ret_over_period(sym, [idx])
        if r is not None: out.append(r)
    return np.array(out)


base = {s: all_month_ret(s) for s in ALL_SYMS}


def base_stat(sym):
    v = base[sym]
    return {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1),
            "median": round(np.median(v) * 100, 2), "mean": round(np.mean(v) * 100, 2)}


base_sum = {s: base_stat(s) for s in ALL_SYMS}


# ---------- 4b. 单月口径统计（与全月基准可比） ----------
def single_month_stats(mask, syms=None):
    syms = syms or ALL_SYMS
    out = {}
    idxs = monthly.index[mask]
    for sym in syms:
        vals, xs = [], []
        for idx in idxs:
            r = ret_over_period(sym, [idx])
            if r is None: continue
            vals.append(r)
            g = ret_over_period("spy", [idx])
            if sym != "spy" and g is not None:
                xs.append(r - g)
        v = np.array(vals)
        if not len(v):
            out[sym] = None; continue
        d = {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1),
             "median": round(np.median(v) * 100, 2), "mean": round(np.mean(v) * 100, 2)}
        if xs:
            d["xs_median"] = round(np.median(xs) * 100, 2)
            d["xs_win_rate"] = round(np.mean(np.array(xs) > 0) * 100, 1)
        out[sym] = d
    return out


sm = {}
sm["up"] = single_month_stats(monthly["dslope"] > 0)
sm["up_sig"] = single_month_stats(monthly["dslope"] >= 0.10)
sm["up_strong"] = single_month_stats(monthly["dslope"] >= 0.20)
sm["down"] = single_month_stats(monthly["dslope"] < 0)
sm["down_sig"] = single_month_stats(monthly["dslope"] <= -0.10)
sm["type"] = {}
for tname in ["熊陡(2Y降10Y升)", "牛陡(2Y降10Y降)", "加息陡(2Y升10Y升)"]:
    mask = pd.Series([classify(monthly.loc[i, "d2"], monthly.loc[i, "d10"]) == tname
                      for i in monthly.index], index=monthly.index) & (monthly["dslope"] > 0)
    sm["type"][tname] = single_month_stats(mask)


# ---------- 5. 分档（敏感度曲线，按 Δslope 月度幅度） ----------
BUCKETS = [
    ("S5_走阔>+30bp", lambda r: r["dslope"] > 0.30),
    ("S4_走阔+10~30bp", lambda r: 0.10 < r["dslope"] <= 0.30),
    ("S3_走阔0~+10bp", lambda r: 0 < r["dslope"] <= 0.10),
    ("S2_收窄-10~0bp", lambda r: -0.10 <= r["dslope"] < 0),
    ("S1_收窄<-10bp", lambda r: r["dslope"] < -0.10),
]
bucket_stats = {s: {} for s in ALL_SYMS}
for bname, f in BUCKETS:
    mask = np.array([f(monthly.loc[i]) for i in monthly.index])
    idxs = monthly.index[mask]
    for sym in ALL_SYMS:
        vals = []
        for idx in idxs:
            r = ret_over_period(sym, [idx])
            if r is not None: vals.append(r)
        v = np.array(vals)
        bucket_stats[sym][bname] = {
            "n": int(len(v)),
            "win_rate": round(np.mean(v > 0) * 100, 1) if len(v) else None,
            "median": round(np.median(v) * 100, 2) if len(v) else None,
            "mean": round(np.mean(v) * 100, 2) if len(v) else None,
        }


# ---------- 6. 月频回归：Δslope(bp) → 资管股月收益 ----------
def ols(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 10: return None
    xc, yc = x - x.mean(), y - y.mean()
    beta = (xc * yc).sum() / (xc * xc).sum()
    alpha = y.mean() - beta * x.mean()
    resid = y - (alpha + beta * x)
    n, k = len(x), 1
    se = np.sqrt((resid ** 2).sum() / (n - k - 1) / (xc * xc).sum())
    t = beta / se if se > 0 else float("nan")
    from math import erf, sqrt
    p = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2)))) if n > 30 else None
    r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return {"n": int(n), "beta_per_bp": round(beta * 100, 4),
            "beta_per_10bp": round(beta * 1000, 3), "alpha": round(alpha, 3),
            "r2": round(r2, 4), "t": round(t, 2), "p": round(p, 4) if p is not None else None}


reg = {}
for sym in ALL_SYMS + ["jpm", "bac", "ms"]:
    xs, ys = [], []
    for idx in monthly.index:
        xs.append(monthly.loc[idx, "dslope"] * 100)
        ys.append(ret_over_period(sym, [idx]))
    reg[sym] = ols(xs, ys)


# 走阔月 vs 收窄月 均值差异（Welch t 检验）
def welch(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[~np.isnan(x)]; y = y[~np.isnan(y)]
    if len(x) < 5 or len(y) < 5: return None
    vx, vy = x.var(ddof=1), y.var(ddof=1)
    t = (x.mean() - y.mean()) / np.sqrt(vx / len(x) + vy / len(y))
    df = (vx / len(x) + vy / len(y)) ** 2 / ((vx / len(x)) ** 2 / (len(x) - 1) + (vy / len(y)) ** 2 / (len(y) - 1))
    from math import erf, sqrt
    p = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))
    return {"t": round(t, 2), "p": round(p, 4), "n1": int(len(x)), "n2": int(len(y)),
            "mean_up": round(x.mean() * 100, 2), "mean_dn": round(y.mean() * 100, 2)}


welch_res = {}
for sym in ALL_SYMS:
    up = [ret_over_period(sym, [i]) for i in monthly.index[monthly["dslope"] > 0]]
    dn = [ret_over_period(sym, [i]) for i in monthly.index[monthly["dslope"] < 0]]
    welch_res[sym] = welch(up, dn)


# ---------- 7. 走阔期类型分解 ----------
type_stats = {}
for tname in ["熊陡(2Y降10Y升)", "牛陡(2Y降10Y降)", "加息陡(2Y升10Y升)"]:
    rows = [r for r in t_up if r["type"] == tname]
    type_stats[tname] = summarize(rows)


# ---------- 8. 熊陡专题：长端领涨（复用 steep_banks_bear 逻辑） ----------
m_bear = (monthly["d2"] < 0) & (monthly["d10"] > 0)
m_lead = (monthly["dslope"] > 0) & (monthly["d10"] > 0) & (monthly["d10"] >= monthly["d2"])
m_leadA = m_lead & (monthly["d2"] < 0)
m_leadB = m_lead & (monthly["d2"].abs() <= 0.05) & (monthly["d2"] >= 0)
m_leadC = m_lead & (monthly["d2"] > 0.05)

stat_bear = single_month_stats(m_bear)
stat_lead = single_month_stats(m_lead)
stat_A = single_month_stats(m_leadA)
stat_B = single_month_stats(m_leadB)
stat_C = single_month_stats(m_leadC)

ep_bear = [describe_episode(m) for m in find_episodes(m_bear)]
ep_lead = [describe_episode(m) for m in find_episodes(m_lead)]

bear_month_rows = []
leadB_month_rows = []
for i, idx in enumerate(monthly.index):
    if m_bear.iloc[i]:
        bear_month_rows.append({
            "month": str(idx)[:7], "y2_chg": round(monthly.loc[idx, "d2"] * 100, 1),
            "y10_chg": round(monthly.loc[idx, "d10"] * 100, 1),
            "slope_chg": round(monthly.loc[idx, "dslope"] * 100, 1),
            "am3": round(ret_over_period("am3", [idx]) * 100, 2) if ret_over_period("am3", [idx]) is not None else None,
            "trad2": round(ret_over_period("trad2", [idx]) * 100, 2) if ret_over_period("trad2", [idx]) is not None else None,
            "spy": round(ret_over_period("spy", [idx]) * 100, 2) if ret_over_period("spy", [idx]) is not None else None,
        })
    if m_leadB.iloc[i]:
        leadB_month_rows.append({
            "month": str(idx)[:7], "y2_chg": round(monthly.loc[idx, "d2"] * 100, 1),
            "y10_chg": round(monthly.loc[idx, "d10"] * 100, 1),
            "slope_chg": round(monthly.loc[idx, "dslope"] * 100, 1),
            "am3": round(ret_over_period("am3", [idx]) * 100, 2) if ret_over_period("am3", [idx]) is not None else None,
            "trad2": round(ret_over_period("trad2", [idx]) * 100, 2) if ret_over_period("trad2", [idx]) is not None else None,
            "spy": round(ret_over_period("spy", [idx]) * 100, 2) if ret_over_period("spy", [idx]) is not None else None,
        })


# ---------- 9. 周频 ----------
def weekly_last(df):
    return df.set_index("date")["y"].resample("W-FRI").last().dropna()


w2 = weekly_last(d2)
w10 = weekly_last(d10)
weekly = pd.DataFrame({"y2": w2, "y10": w10}).dropna()
weekly["slope"] = weekly["y10"] - weekly["y2"]
weekly["dslope"] = weekly["slope"].diff()
weekly = weekly.dropna()
weekly = weekly[weekly.index <= "2026-08-08"]


def ret_over_weeks(sym, weeks):
    if not weeks: return None
    if sym in ("am3", "trad2", "bank3"):
        parts = [AM, TRAD, BANK][["am3", "trad2", "bank3"].index(sym)]
        vals = [ret_over_weeks(s, weeks) for s in parts]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None
    start = weeks[0] - pd.Timedelta(days=6)
    end = weeks[-1]
    df = stocks[sym]
    s = df[df["date"] >= start]
    if s.empty: return None
    e = df[df["date"] <= end]
    if e.empty: return None
    a, b = s.iloc[0]["px"], e.iloc[-1]["px"]
    if a <= 0 or b <= 0: return None
    return b / a - 1.0


def find_w_episodes(cond):
    eps, cur = [], []
    for i, idx in enumerate(weekly.index):
        if cond.iloc[i]: cur.append(idx)
        else:
            if cur: eps.append(cur); cur = []
    if cur: eps.append(cur)
    return eps


def weekly_cond_stats(mask, syms=None):
    syms = syms or ALL_SYMS
    out = {}
    idxs = weekly.index[mask]
    for sym in syms:
        vals, xs = [], []
        for idx in idxs:
            r = ret_over_weeks(sym, [idx])
            if r is None: continue
            vals.append(r)
            g = ret_over_weeks("spy", [idx])
            if sym != "spy" and g is not None: xs.append(r - g)
        v = np.array(vals)
        if not len(v): out[sym] = None; continue
        d = {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1),
             "median": round(np.median(v) * 100, 2), "mean": round(np.mean(v) * 100, 2)}
        if xs:
            d["xs_median"] = round(np.median(xs) * 100, 2)
        out[sym] = d
    return out


w_up = weekly_cond_stats(weekly["dslope"] > 0)
w_up_sig = weekly_cond_stats(weekly["dslope"] >= 0.10)
w_up_strong = weekly_cond_stats(weekly["dslope"] >= 0.20)
w_down = weekly_cond_stats(weekly["dslope"] < 0)
w_bear = weekly_cond_stats(weekly["dslope"] > 0)  # 占位保持键结构


# ---------- 10. 显著走阔期结束后的持有表现 ----------
def forward_ret(sym, anchor_date):
    df = stocks[sym]
    s = df[df["date"] <= anchor_date]
    if s.empty: return None
    a = s.iloc[-1]["px"]
    out = {}
    for k, tag in [(3, "m3"), (6, "m6"), (12, "m12")]:
        end = anchor_date + pd.DateOffset(months=k)
        e = df[(df["date"] > anchor_date) & (df["date"] <= end)]
        if e.empty: out[tag] = None; continue
        out[tag] = round((e.iloc[-1]["px"] / a - 1) * 100, 2)
    return out


def combo_forward(sym, anchor):
    parts = {"am3": AM, "trad2": TRAD, "bank3": BANK}[sym]
    fv = {}
    got = [forward_ret(s, anchor) for s in parts]
    got = [p for p in got if p]
    if got:
        for tag in ["m3", "m6", "m12"]:
            vals = [p[tag] for p in got if p.get(tag) is not None]
            fv[tag] = round(np.mean(vals), 2) if vals else None
    return fv


fwd_rows = []
for r in t_up_sig:
    last = edges["jpm"][1]
    anchor = last.get(pd.Period(r["end"], "M"))
    if anchor is None: continue
    row = {"label": f"{r['start'][:7]}~{r['end'][:7]}", "slope_chg": r["slope_chg"]}
    for sym in ALL_SYMS:
        if sym in COMBO:
            row[sym] = combo_forward(sym, anchor)
        else:
            row[sym] = forward_ret(sym, anchor)
    fwd_rows.append(row)


def fwd_summary(rows, tag):
    out = {}
    for sym in ALL_SYMS:
        vals = [r[sym][tag] for r in rows if r.get(sym) and r[sym].get(tag) is not None]
        if not vals: out[sym] = None; continue
        out[sym] = {"n": len(vals), "win_rate": round(np.mean([v > 0 for v in vals]) * 100, 1),
                    "median": round(np.median(vals), 2), "mean": round(np.mean(vals), 2)}
    return out


fwd_m3 = fwd_summary(fwd_rows, "m3")
fwd_m6 = fwd_summary(fwd_rows, "m6")
fwd_m12 = fwd_summary(fwd_rows, "m12")


# ---------- 11. 著名时期案例（日频，供报告绘图；含资管可得的时期） ----------
CASES = [
    ("c1994", "1994-02-01", "1994-05-31", "对照·1994-02~05 · 加息平坦化(2Y↑更快)"),
    ("c2003", "2003-06-02", "2004-05-31", "2003-06~2004-05 · 复苏双升"),
    ("c2013", "2013-05-01", "2013-09-30", "2013-05~09 · Taper Tantrum 熊陡"),
    ("c2016", "2016-11-01", "2017-03-31", "2016-11~2017-03 · Trump 再通胀"),
    ("c2020", "2020-02-01", "2020-05-31", "2020-02~05 · 危机牛陡"),
    ("c2021", "2021-01-01", "2021-03-31", "2021-01~03 · Reflation 熊陡"),
    ("c2024", "2024-09-01", "2024-12-31", "2024-09~12 · 降息+长端反弹"),
]


def case_daily(cid, start, end, label):
    d2w = d2[(d2["date"] >= start) & (d2["date"] <= end)]
    d10w = d10[(d10["date"] >= start) & (d10["date"] <= end)]
    merged = pd.merge(d2w[["date", "y"]], d10w[["date", "y"]], on="date", suffixes=("2", "10")).dropna()
    dates = [str(d)[:10] for d in merged["date"]]
    y2v = [round(v, 3) for v in merged["y2"]]
    y10v = [round(v, 3) for v in merged["y10"]]
    slope_v = [round(a - b, 3) for a, b in zip(y10v, y2v)]
    rets, ret_dates = {}, dates
    for sym in ["apo", "bx", "kkr", "blk", "trow", "jpm", "spy"]:
        df = stocks[sym]
        w = df[(df["date"] >= start) & (df["date"] <= end)].copy()
        if w.empty: rets[sym] = None; continue
        base0 = w.iloc[0]["px"]
        rets[sym] = [round((p / base0 - 1) * 100, 2) for p in w["px"]]
        ret_dates = [str(d)[:10] for d in w["date"]]
    sl_chg = round((y10v[-1] - y2v[-1] - (y10v[0] - y2v[0])) * 100, 1)
    return {"id": cid, "label": label, "start": start, "end": end,
            "dates": dates, "y2": y2v, "y10": y10v, "slope": slope_v,
            "slope_chg_bp": sl_chg, "ret_dates": ret_dates, "rets": rets}


case_data = [case_daily(cid, s, e, lbl) for cid, s, e, lbl in CASES]


def case_ret_summary():
    out = []
    for c in case_data:
        s, e = c["start"], c["end"]
        row = {"label": c["label"], "slope_chg": c["slope_chg_bp"]}
        for sym in ["apo", "bx", "kkr", "blk", "trow", "jpm", "spy"]:
            df = stocks[sym]
            w = df[(df["date"] >= s) & (df["date"] <= e)]
            if w.empty: row[sym] = None; continue
            row[sym] = round((w.iloc[-1]["px"] / w.iloc[0]["px"] - 1) * 100, 2)
        vals = [row[s] for s in ["apo", "bx", "kkr"] if row.get(s) is not None]
        row["am3"] = round(np.mean(vals), 2) if vals else None
        vals2 = [row[s] for s in ["blk", "trow"] if row.get(s) is not None]
        row["trad2"] = round(np.mean(vals2), 2) if vals2 else None
        out.append(row)
    return out


case_summary = case_ret_summary()


# ---------- 12. 2011-11 起同窗口对照（所有标的全可用；规避早期窗口成分差异） ----------
common_start = "2011-11-30"
monthly2 = monthly[monthly.index >= pd.Timestamp(common_start)]
idx2 = monthly2.index

# 全月基准（common 窗口）
base2 = {}
for sym in ALL_SYMS:
    vals = []
    for idx in idx2:
        r = ret_over_period(sym, [idx])
        if r is not None: vals.append(r)
    v = np.array(vals)
    base2[sym] = {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1) if len(v) else None,
                  "median": round(np.median(v) * 100, 2) if len(v) else None,
                  "mean": round(np.mean(v) * 100, 2) if len(v) else None}


def single_month_stats_window(mask_cond, syms=None):
    """mask_cond: callable(monthly-row) -> bool；只统计 common 窗口内月份"""
    syms = syms or ALL_SYMS
    out = {}
    valid = [i for i in idx2 if mask_cond(monthly.loc[i])]
    for sym in syms:
        vals, xs = [], []
        for idx in valid:
            r = ret_over_period(sym, [idx])
            if r is None: continue
            vals.append(r)
            g = ret_over_period("spy", [idx])
            if sym != "spy" and g is not None: xs.append(r - g)
        v = np.array(vals)
        if not len(v): out[sym] = None; continue
        d = {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1),
             "median": round(np.median(v) * 100, 2), "mean": round(np.mean(v) * 100, 2)}
        if xs:
            d["xs_median"] = round(np.median(xs) * 100, 2)
        out[sym] = d
    return out


common = {}
common["base"] = base2
common["up"] = single_month_stats_window(lambda r: r["dslope"] > 0)
common["up_sig"] = single_month_stats_window(lambda r: r["dslope"] >= 0.10)
common["up_strong"] = single_month_stats_window(lambda r: r["dslope"] >= 0.20)
common["down"] = single_month_stats_window(lambda r: r["dslope"] < 0)
common["down_sig"] = single_month_stats_window(lambda r: r["dslope"] <= -0.10)
common["type"] = {}
for tname in ["熊陡(2Y降10Y升)", "牛陡(2Y降10Y降)", "加息陡(2Y升10Y升)"]:
    common["type"][tname] = single_month_stats_window(
        lambda r, t=tname: r["dslope"] > 0 and classify(r["d2"], r["d10"]) == t)
common["bear"] = single_month_stats_window(lambda r: r["d2"] < 0 and r["d10"] > 0)
common["lead"] = single_month_stats_window(lambda r: r["dslope"] > 0 and r["d10"] > 0 and r["d10"] >= r["d2"])

# 2011 后走阔≥10bp 期明细（供表格）
ep_common_sig = []
for m in find_episodes(monthly["dslope"] >= 0.10):
    if m[0] >= pd.Timestamp(common_start):
        ep_common_sig.append(describe_episode(m))


# ---------- 13. 输出 ----------
result = {
    "window": f"{monthly.index[0]} ~ {monthly.index[-1]}",
    "common_window_start": common_start,
    "n_months": int(len(monthly)),
    "n_months_common": int(len(idx2)),
    "slope_monthly_series": {
        "dates": [str(p)[:7] for p in monthly.index],
        "slope": [round(v, 3) for v in monthly["slope"]],
        "dslope": [round(v * 100, 1) for v in monthly["dslope"]],
        "am3_ret": [round(r * 100, 2) if (r := ret_over_period("am3", [i])) is not None else None
                    for i in monthly.index],
        "trad2_ret": [round(r * 100, 2) if (r := ret_over_period("trad2", [i])) is not None else None
                      for i in monthly.index],
    },
    "cond_counts": {
        "up_loose": int((monthly["dslope"] > 0).sum()),
        "up_sig": int((monthly["dslope"] >= 0.10).sum()),
        "up_strong": int((monthly["dslope"] >= 0.20).sum()),
        "down_loose": int((monthly["dslope"] < 0).sum()),
        "down_sig": int((monthly["dslope"] <= -0.10).sum()),
        "bear_strict": int(m_bear.sum()),
        "lead_total": int(m_lead.sum()),
        "lead_A": int(m_leadA.sum()), "lead_B": int(m_leadB.sum()), "lead_C": int(m_leadC.sum()),
    },
    "episodes": {"up": t_up, "up_sig": t_up_sig, "up_strong": t_up_strong,
                 "down": t_down, "down_sig": t_down_sig,
                 "bear": ep_bear, "lead": ep_lead},
    "summary": {"up": sum_up, "up_sig": sum_up_sig, "up_strong": sum_up_strong,
                "down": sum_down, "down_sig": sum_down_sig},
    "single_month": sm,
    "base_all_month": base_sum,
    "buckets": bucket_stats,
    "regression": reg,
    "welch": welch_res,
    "type_stats": type_stats,
    "bear_lead": {
        "stats": {"bear_strict": stat_bear, "lead_total": stat_lead, "lead_A": stat_A,
                  "lead_B": stat_B, "lead_C": stat_C},
        "bear_month_rows": bear_month_rows,
        "leadB_month_rows": leadB_month_rows,
    },
    "weekly": {
        "cond_counts": {"up": int((weekly["dslope"] > 0).sum()), "up_sig": int((weekly["dslope"] >= 0.10).sum()),
                        "up_strong": int((weekly["dslope"] >= 0.20).sum()), "down": int((weekly["dslope"] < 0).sum())},
        "stats": {"up": w_up, "up_sig": w_up_sig, "up_strong": w_up_strong, "down": w_down},
    },
    "forward": {"rows": fwd_rows, "m3": fwd_m3, "m6": fwd_m6, "m12": fwd_m12},
    "common": common,
    "ep_common_sig": ep_common_sig,
    "cases": case_data,
    "case_summary": case_summary,
    "sym_names": SYM_NAMES,
}

with open(os.path.join(OUT, "steep_am.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)

# ---------- 控制台摘要 ----------
print(f"分析窗口: {result['window']} ({result['n_months']} 个月) | 同窗口对照 {common_start} 起 {result['n_months_common']} 个月")
cc = result["cond_counts"]
print(f"走阔月: {cc['up_loose']} / 显著≥10bp {cc['up_sig']} / 强≥20bp {cc['up_strong']} | 收窄 {cc['down_loose']} / 显著 {cc['down_sig']} | 熊陡 {cc['bear_strict']} / 长端领涨 {cc['lead_total']} (A {cc['lead_A']}/B {cc['lead_B']}/C {cc['lead_C']})")
print(f"全月基准中位: " + "  ".join(f"{SYM_NAMES[s].split('(')[0]} {base_sum[s]['median']}%" for s in ALL_SYMS))
print()
print("=== 单月口径 ===")
for k, name in [("up", "走阔(全)"), ("up_sig", "走阔≥10bp"), ("up_strong", "走阔≥20bp"), ("down", "收窄(全)"), ("down_sig", "收窄≤-10bp")]:
    s = sm[k]
    line = f"[{name}] "
    for sym in ["am3", "trad2", "bank3", "spy"]:
        if not s.get(sym): continue
        line += f"{SYM_NAMES[sym].split('(')[0]} {s[sym]['median']}%/{s[sym]['win_rate']}%"
        if "xs_median" in s[sym]: line += f"(超额{s[sym]['xs_median']})"
        line += " "
    print(line)
print()
print("=== 走阔月类型分解（单月口径） ===")
for tname, st in sm["type"].items():
    if st.get("am3"):
        print(f"  {tname}: n={st['am3']['n']}月 am3 中位{st['am3']['median']}% 胜率{st['am3']['win_rate']}% | trad2 {st['trad2']['median']}% bank3 {st['bank3']['median']}% SPY {st['spy']['median']}%")
print()
print("=== 回归（月频 Δslope bp → 月收益%） ===")
for sym in ALL_SYMS:
    r = reg[sym]
    if r: print(f"  {SYM_NAMES[sym].split('(')[0]:6s} β={r['beta_per_10bp']:+.3f}%/10bp  R²={r['r2']:.3f}  p={r['p']}  n={r['n']}")
print()
print("=== 2011-11 起同窗口（规避上市窗口差异） ===")
for k, name in [("up", "走阔"), ("up_sig", "走阔≥10bp"), ("up_strong", "走阔≥20bp"), ("down_sig", "收窄≤-10bp"), ("bear", "严格熊陡"), ("lead", "长端领涨")]:
    s = common[k]
    if s.get("am3"):
        a = s["am3"]
        print(f"  [{name}] n={a['n']}月 am3 {a['median']}%/{a['win_rate']}%(超额{a.get('xs_median')}) | trad2 {s['trad2']['median']}% bank3 {s['bank3']['median']}% SPY {s['spy']['median']}% | 全月基准 am3 {base2['am3']['median']}%")
print()
print("=== 周频 ===")
for k, name in [("up", "走阔"), ("up_sig", "≥10bp/周"), ("up_strong", "≥20bp/周"), ("down", "收窄")]:
    s = result["weekly"]["stats"][k]
    if s.get("am3"):
        print(f"  [{name}] n={s['am3']['n']}周 am3 中位{s['am3']['median']}% 胜率{s['am3']['win_rate']}% | SPY {s['spy']['median']}%")
print()
print("=== 显著走阔后持有（am3 中位） ===")
for tag, nm in [("m3", "后3月"), ("m6", "后6月"), ("m12", "后12月")]:
    s = result["forward"][tag]
    if s and s.get("am3"): print(f"  {nm}: am3 中位 {s['am3']['median']}% 胜率 {s['am3']['win_rate']}% | SPY {s['spy']['median']}%")
print()
print("=== 著名时期案例 ===")
for c in case_summary:
    print(f"  {c['label']}: slope {c['slope_chg']:+.0f}bp | AM3 {c['am3']}% APO {c['apo']}% BX {c['bx']}% KKR {c['kkr']}% | trad2 {c['trad2']}% BLK {c['blk']}% TROW {c['trow']}% | JPM {c['jpm']}% SPY {c['spy']}%")
print()
print("JSON saved:", os.path.join(OUT, "steep_am.json"))