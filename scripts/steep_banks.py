#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
银行板块（JPM/MS/BAC）在 10Y-2Y 利差（slope = DGS10 - DGS2）走阔时期的表现
主口径：月频 Δslope > 0（宽松）；Δslope ≥ +10bp（显著）；Δslope ≥ +20bp（强）
对照：Δslope < 0（收窄）；Δslope ≤ -10bp（显著收窄）
类型分解（走阔月）：熊陡(2Y↓10Y↑) / 牛陡(2Y↓10Y↓) / 加息陡(2Y↑10Y↑)
标的：jpm/bac/ms（点名）+ gs/kre/xlf/gspc（对照/基准）；bank3 = 三只银行股等权
窗口：收益率 1976-07 起；股票受上市时间限制（BAC 1990、MS 1993、GS 1999、KRE 2006、XLF 1998）
"""
import pandas as pd
import numpy as np
import json, os, glob

DATA = r"C:\Users\Administrator\Desktop\stock\data"
OUT = r"C:\Users\Administrator\Desktop\stock\results"
os.makedirs(OUT, exist_ok=True)

SYMS = ["jpm", "bac", "ms", "gs", "kre", "xlf", "gspc"]
SYM_NAMES = {"jpm": "JPM", "bac": "BAC", "ms": "MS", "gs": "GS",
             "kre": "KRE", "xlf": "XLF", "gspc": "S&P500"}

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
monthly = monthly.dropna().drop(columns=["slope"])  # 保留 slope 用于图
# 恢复 slope 列（diff 后 dropna 会删首行，slope 列保留）
monthly["slope"] = monthly["y10"] - monthly["y2"]
monthly = monthly[monthly.index <= "2026-07-31"]

# ---------- 2. 月收益 ----------
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
    if sym == "bank3":
        vals = [ret_over_period(s, months) for s in ["jpm", "bac", "ms"]]
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

def steep_type(r):
    """走阔月分类：熊陡 / 牛陡 / 加息陡"""
    d2v, d10v = r["d2"], r["d10"]
    if d2v < 0 and d10v > 0: return "熊陡(2Y降10Y升)"
    if d2v < 0 and d10v <= 0: return "牛陡(2Y降10Y降)"
    return "加息陡(2Y升10Y升)"

def classify(y2c, y10c):
    if y2c < 0 and y10c > 0: return "熊陡(2Y降10Y升)"
    if y2c < 0 and y10c <= 0: return "牛陡(2Y降10Y降)"
    return "加息陡(2Y升10Y升)"

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
    for sym in SYMS:
        r = ret_over_period(sym, months)
        row[f"ret_{sym}"] = round(r * 100, 2) if r is not None else None
    # bank3 等权（可用者平均）
    vals = [row[f"ret_{s}"] for s in ["jpm", "bac", "ms"] if row.get(f"ret_{s}") is not None]
    row["ret_bank3"] = round(np.mean(vals), 2) if vals else None
    g = row.get("ret_gspc")
    if row.get("ret_bank3") is not None and g is not None:
        row["xs_bank3"] = round(row["ret_bank3"] - g, 2)
    else:
        row["xs_bank3"] = None
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
        for sym in SYMS + ["bank3"]:
            out[sym] = None
        return out
    for sym in SYMS + ["bank3"]:
        vals = [r[f"ret_{sym}"] for r in rows if r.get(f"ret_{sym}") is not None]
        xsv = [r[f"xs_{sym}"] for r in rows if r.get(f"xs_{sym}") is not None] if f"xs_{sym}" in rows[0] else []
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

base = {s: all_month_ret(s) for s in SYMS + ["bank3"]}

def base_stat(sym):
    v = base[sym]
    return {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1),
            "median": round(np.median(v) * 100, 2), "mean": round(np.mean(v) * 100, 2)}

base_sum = {s: base_stat(s) for s in SYMS + ["bank3"]}

# ---------- 4b. 单月口径统计（与全月基准可比） ----------
def single_month_stats(mask, syms=("jpm", "bac", "ms", "bank3", "gspc")):
    """mask: bool Series（按 monthly.index 对齐）；统计每个单月收益"""
    out = {}
    idxs = monthly.index[mask]
    for sym in syms:
        vals, xs = [], []
        for idx in idxs:
            r = ret_over_period(sym, [idx])
            if r is None: continue
            vals.append(r)
            g = ret_over_period("gspc", [idx])
            if sym != "gspc" and g is not None:
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
# 走阔月类型分解（单月口径）
sm["type"] = {}
for tname in ["熊陡(2Y降10Y升)", "牛陡(2Y降10Y降)", "加息陡(2Y升10Y升)"]:
    mask = pd.Series([classify(monthly.loc[i, "d2"], monthly.loc[i, "d10"]) == tname
                      for i in monthly.index], index=monthly.index) & (monthly["dslope"] > 0)
    sm["type"][tname] = single_month_stats(mask)

# 分位数对照：走阔显著期收益 vs 全部同月收益分布
def pctile_vs_base(sym, rows):
    v = base[sym]
    return [round(np.mean(v < r[f"ret_{sym}"] / 100) * 100, 1)
            if r.get(f"ret_{sym}") is not None else None for r in rows]

pct_up_sig = {s: pctile_vs_base(s, t_up_sig) for s in ["jpm", "bac", "ms", "bank3", "gspc"]}

# ---------- 5. 分档（敏感度曲线，按 Δslope 月度幅度） ----------
BUCKETS = [
    ("S5_走阔>+30bp", lambda r: r["dslope"] > 0.30),
    ("S4_走阔+10~30bp", lambda r: 0.10 < r["dslope"] <= 0.30),
    ("S3_走阔0~+10bp", lambda r: 0 < r["dslope"] <= 0.10),
    ("S2_收窄-10~0bp", lambda r: -0.10 <= r["dslope"] < 0),
    ("S1_收窄<-10bp", lambda r: r["dslope"] < -0.10),
]
bucket_stats = {s: {} for s in ["jpm", "bac", "ms", "bank3", "gspc"]}
for bname, f in BUCKETS:
    mask = np.array([f(monthly.loc[i]) for i in monthly.index])
    idxs = monthly.index[mask]
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        vals = []
        for idx in idxs:
            r = ret_over_period(sym, [idx])
            if r is not None: vals.append(r)
        v = np.array(vals)
        bucket_stats[sym][bname] = {
            "n": int(len(v)),
            "win_rate": round(np.mean(v > 0) * 100, 1) if len(v) else None,
            "median": round(np.median(v), 2) if len(v) else None,
            "mean": round(np.mean(v), 2) if len(v) else None,
        }

# ---------- 6. 月频回归：Δslope(bp) → 银行股月收益 ----------
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
    # p 值（t 分布近似，n>30 用正态）
    from math import erf, sqrt
    p = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2)))) if n > 30 else None
    r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return {"n": int(n), "beta_per_bp": round(beta * 100, 4),
            "beta_per_10bp": round(beta * 1000, 3), "alpha": round(alpha, 3),
            "r2": round(r2, 4), "t": round(t, 2), "p": round(p, 4) if p is not None else None}

reg = {}
for sym in ["jpm", "bac", "ms", "bank3", "gspc", "kre", "xlf"]:
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
for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
    up = [ret_over_period(sym, [i]) for i in monthly.index[monthly["dslope"] > 0]]
    dn = [ret_over_period(sym, [i]) for i in monthly.index[monthly["dslope"] < 0]]
    welch_res[sym] = welch(up, dn)

# ---------- 7. 走阔期类型分解 ----------
type_stats = {}
for tname in ["熊陡(2Y降10Y升)", "牛陡(2Y降10Y降)", "加息陡(2Y升10Y升)"]:
    rows = [r for r in t_up if r["type"] == tname]
    type_stats[tname] = summarize(rows)

# ---------- 8. 周频 ----------
def weekly_last(df):
    return df.set_index("date")["y"].resample("W-FRI").last().dropna()

w2 = weekly_last(d2)
w10 = weekly_last(d10)
weekly = pd.DataFrame({"y2": w2, "y10": w10}).dropna()
weekly["slope"] = weekly["y10"] - weekly["y2"]
weekly["dslope"] = weekly["slope"].diff()
weekly = weekly.dropna()
weekly = weekly[weekly.index <= "2026-08-08"]

def find_w_episodes(cond):
    eps, cur = [], []
    for i, idx in enumerate(weekly.index):
        if cond.iloc[i]: cur.append(idx)
        else:
            if cur: eps.append(cur); cur = []
    if cur: eps.append(cur)
    return eps

def ret_over_weeks(sym, weeks):
    if not weeks: return None
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

def describe_w_episode(weeks):
    sub = weekly.loc[weeks]
    start, end = weeks[0], weeks[-1]
    y2c = weekly.loc[end, "y2"] - weekly.loc[start, "y2"]
    y10c = weekly.loc[end, "y10"] - weekly.loc[start, "y10"]
    row = {"start": str(start), "end": str(end), "weeks": len(weeks),
           "y2_chg": round(y2c * 100, 2), "y10_chg": round(y10c * 100, 2),
           "slope_chg": round((y10c - y2c) * 100, 2)}
    for sym in SYMS:
        r = ret_over_weeks(sym, weeks)
        row[f"ret_{sym}"] = round(r * 100, 2) if r is not None else None
    vals = [row[f"ret_{s}"] for s in ["jpm", "bac", "ms"] if row.get(f"ret_{s}") is not None]
    row["ret_bank3"] = round(np.mean(vals), 2) if vals else None
    return row

def build_w_table(cond):
    return [describe_w_episode(w) for w in find_w_episodes(cond)]

w_up = build_w_table(weekly["dslope"] > 0)
w_up_sig = build_w_table(weekly["dslope"] >= 0.10)
w_up_strong = build_w_table(weekly["dslope"] >= 0.20)
w_down = build_w_table(weekly["dslope"] < 0)

def summarize_w(rows):
    out = {"n_episodes": len(rows)}
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        vals = [r[f"ret_{sym}"] for r in rows if r.get(f"ret_{sym}") is not None]
        if not vals: out[sym] = None; continue
        out[sym] = {"n": len(vals), "win_rate": round(np.mean([v > 0 for v in vals]) * 100, 1),
                    "median": round(np.median(vals), 2), "mean": round(np.mean(vals), 2)}
    return out

sum_w_up = summarize_w(w_up)
sum_w_up_sig = summarize_w(w_up_sig)
sum_w_up_strong = summarize_w(w_up_strong)
sum_w_down = summarize_w(w_down)

# ---------- 9. 显著走阔期结束后的持有表现 ----------
def forward_ret(sym, anchor_date):
    """anchor 后 3/6/12 个月收益（anchor 为时期末月最后交易日）"""
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

fwd_rows = []
for r in t_up_sig:
    last, _ = edges["jpm"]
    anchor = last.get(pd.Period(r["end"], "M"))
    if anchor is None: continue
    row = {"label": f"{r['start'][:7]}~{r['end'][:7]}", "slope_chg": r["slope_chg"]}
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        if sym == "bank3":
            fv = {}
            parts = [forward_ret(s, anchor) for s in ["jpm", "bac", "ms"]]
            parts = [p for p in parts if p]
            if parts:
                for tag in ["m3", "m6", "m12"]:
                    vals = [p[tag] for p in parts if p.get(tag) is not None]
                    fv[tag] = round(np.mean(vals), 2) if vals else None
            row[sym] = fv
        else:
            row[sym] = forward_ret(sym, anchor)
    fwd_rows.append(row)

def fwd_summary(rows, tag):
    out = {}
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        vals = [r[sym][tag] for r in rows if r.get(sym) and r[sym].get(tag) is not None]
        if not vals: out[sym] = None; continue
        out[sym] = {"n": len(vals), "win_rate": round(np.mean([v > 0 for v in vals]) * 100, 1),
                    "median": round(np.median(vals), 2), "mean": round(np.mean(vals), 2)}
    return out

fwd_m3 = fwd_summary(fwd_rows, "m3")
fwd_m6 = fwd_summary(fwd_rows, "m6")
fwd_m12 = fwd_summary(fwd_rows, "m12")

# ---------- 10. 著名时期案例（日频，供报告绘图） ----------
CASES = [
    ("c1994", "1994-02-01", "1994-05-31", "对照·1994-02~05 · 加息平坦化(2Y↑更快)"),
    ("c2003", "2003-06-02", "2004-05-31", "2003-06~2004-05 · 复苏双升"),
    ("c2013", "2013-05-01", "2013-09-30", "2013-05~09 · Taper Tantrum 熊陡"),
    ("c2016", "2016-11-01", "2017-03-31", "2016-11~2017-03 · Trump 再通胀"),
    ("c2020", "2020-02-01", "2020-05-31", "2020-02~05 · 危机牛陡"),
    ("c2021", "2021-01-01", "2021-03-31", "2021-01~03 · Reflation 熊陡"),
    ("c2024", "2024-09-01", "2024-12-31", "2024-09~12 · 降息+长端反弹"),
]

def case_daily(cid, start, end, label, syms):
    d2w = d2[(d2["date"] >= start) & (d2["date"] <= end)]
    d10w = d10[(d10["date"] >= start) & (d10["date"] <= end)]
    merged = pd.merge(d2w[["date", "y"]], d10w[["date", "y"]], on="date", suffixes=("2", "10")).dropna()
    dates = [str(d)[:10] for d in merged["date"]]
    y2v = [round(v, 3) for v in merged["y2"]]
    y10v = [round(v, 3) for v in merged["y10"]]
    slope_v = [round(a - b, 3) for a, b in zip(y10v, y2v)]
    rets, ret_dates = {}, dates
    for sym in syms:
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

case_syms = ["jpm", "bac", "ms", "kre", "gspc"]
case_data = [case_daily(cid, s, e, lbl, case_syms) for cid, s, e, lbl in CASES]

# 案例区间收益汇总（直接算，跨月）
def case_ret_summary():
    out = []
    for c in case_data:
        s, e = c["start"], c["end"]
        row = {"label": c["label"], "slope_chg": c["slope_chg_bp"]}
        for sym in ["jpm", "bac", "ms", "kre", "gspc"]:
            df = stocks[sym]
            w = df[(df["date"] >= s) & (df["date"] <= e)]
            if w.empty: row[sym] = None; continue
            row[sym] = round((w.iloc[-1]["px"] / w.iloc[0]["px"] - 1) * 100, 2)
        vals = [row[s] for s in ["jpm", "bac", "ms"] if row.get(s) is not None]
        row["bank3"] = round(np.mean(vals), 2) if vals else None
        out.append(row)
    return out

case_summary = case_ret_summary()

# ---------- 11. 输出 ----------
result = {
    "window": f"{monthly.index[0]} ~ {monthly.index[-1]}",
    "n_months": int(len(monthly)),
    "slope_monthly_series": {
        "dates": [str(p)[:7] for p in monthly.index],
        "slope": [round(v, 3) for v in monthly["slope"]],
        "dslope": [round(v * 100, 1) for v in monthly["dslope"]],
        "bank3_ret": [round(r * 100, 2) if (r := ret_over_period("bank3", [i])) is not None else None
                      for i in monthly.index],
    },
    "cond_counts": {
        "up_loose": int((monthly["dslope"] > 0).sum()),
        "up_sig": int((monthly["dslope"] >= 0.10).sum()),
        "up_strong": int((monthly["dslope"] >= 0.20).sum()),
        "down_loose": int((monthly["dslope"] < 0).sum()),
        "down_sig": int((monthly["dslope"] <= -0.10).sum()),
    },
    "episodes": {"up": t_up, "up_sig": t_up_sig, "up_strong": t_up_strong,
                 "down": t_down, "down_sig": t_down_sig},
    "summary": {"up": sum_up, "up_sig": sum_up_sig, "up_strong": sum_up_strong,
                "down": sum_down, "down_sig": sum_down_sig},
    "single_month": sm,
    "base_all_month": base_sum,
    "pctile_up_sig": pct_up_sig,
    "buckets": bucket_stats,
    "regression": reg,
    "welch": welch_res,
    "type_stats": type_stats,
    "weekly": {
        "n_weeks": int(len(weekly)),
        "cond_counts": {"up_loose": int((weekly["dslope"] > 0).sum()),
                        "up_sig": int((weekly["dslope"] >= 0.10).sum()),
                        "up_strong": int((weekly["dslope"] >= 0.20).sum())},
        "episodes": {"up": w_up, "up_sig": w_up_sig, "up_strong": w_up_strong, "down": w_down},
        "summary": {"up": sum_w_up, "up_sig": sum_w_up_sig, "up_strong": sum_w_up_strong, "down": sum_w_down},
    },
    "forward": {"rows": fwd_rows, "m3": fwd_m3, "m6": fwd_m6, "m12": fwd_m12},
    "cases": case_data,
    "case_summary": case_summary,
    "sym_names": SYM_NAMES,
}

with open(os.path.join(OUT, "steep_banks.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)

# ---------- 控制台摘要 ----------
print(f"分析窗口: {result['window']} ({result['n_months']} 个月)")
cc = result["cond_counts"]
print(f"走阔月: 宽松 {cc['up_loose']} / 显著≥10bp {cc['up_sig']} / 强≥20bp {cc['up_strong']} | 收窄月 {cc['down_loose']} / 显著 {cc['down_sig']}")
print(f"全月基准中位: " + "  ".join(f"{'BK3' if s=='bank3' else s.upper()} {base_sum[s]['median']}%" for s in ["jpm", "bac", "ms", "bank3", "gspc"]))
print()
print("=== 单月口径（与全月基准可比；超额 vs SPY 当月） ===")
for k, name in [("up", "走阔(全)"), ("up_sig", "走阔≥10bp"), ("up_strong", "走阔≥20bp"), ("down", "收窄(全)"), ("down_sig", "收窄≤-10bp")]:
    s = sm[k]
    line = f"[{name}] "
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        if not s.get(sym): continue
        line += f"{'BK3' if sym=='bank3' else sym.upper()} {s[sym]['median']}%/{s[sym]['win_rate']}%"
        if "xs_median" in s[sym]: line += f"(超额{s[sym]['xs_median']})"
        line += " "
    print(line)
print()
print("=== 走阔月类型分解（单月口径） ===")
for tname, st in sm["type"].items():
    if st.get("bank3"):
        print(f"  {tname}: n={st['bank3']['n']}月 bank3 中位{st['bank3']['median']}% 胜率{st['bank3']['win_rate']}% | JPM {st['jpm']['median']}% BAC {st['bac']['median']}% MS {st['ms']['median']}% SPY {st['gspc']['median']}%")
print()
print("=== 月频汇总（中位收益 / 胜率 / 超额中位 vs SPY） ===")
for k, name in [("up", "走阔(全)"), ("up_sig", "走阔≥10bp"), ("up_strong", "走阔≥20bp"), ("down", "收窄(全)"), ("down_sig", "收窄≤-10bp")]:
    s = result["summary"][k]
    line = f"[{name}] n={s['n_episodes']}期 "
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        if not s.get(sym): continue
        line += f"{'BK3' if sym=='bank3' else sym.upper()} {s[sym]['median']}%/{s[sym]['win_rate']}%"
        if "xs_median" in s[sym]: line += f"(超额{s[sym]['xs_median']})"
        line += " "
    print(line)
print()
print("=== 回归（月频 Δslope bp → 月收益%） ===")
for sym in ["jpm", "bac", "ms", "bank3", "gspc", "kre", "xlf"]:
    r = reg[sym]
    if r: print(f"  {sym.upper():5s} β={r['beta_per_10bp']:+.3f}%/10bp  R²={r['r2']:.3f}  p={r['p']}  n={r['n']}")
print()
print("=== 走阔 vs 收窄 月收益均值差 (Welch) ===")
for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
    w = welch_res[sym]
    if w: print(f"  {sym.upper():5s} 走阔均值{w['mean_up']:+.2f}% vs 收窄{w['mean_dn']:+.2f}%  diff={w['mean_up']-w['mean_dn']:+.2f}pp  t={w['t']} p={w['p']}")
print()
print("=== 类型分解（走阔月内） ===")
for tname, st in type_stats.items():
    if st["n_episodes"]:
        b = st.get("bank3")
        print(f"  {tname}: {st['n_episodes']}期 bank3 中位{b['median']}% 胜率{b['win_rate']}% | JPM {st['jpm']['median']}% BAC {st['bac']['median']}% MS {st['ms']['median']}%")
print()
print("=== 周频 ===")
for k, name in [("up", "走阔"), ("up_sig", "≥10bp/周"), ("up_strong", "≥20bp/周"), ("down", "收窄")]:
    s = result["weekly"]["summary"][k]
    b = s.get("bank3")
    if b: print(f"  [{name}] n={s['n_episodes']}期 bank3 中位{b['median']}% 胜率{b['win_rate']}% | SPY {s['gspc']['median']}%")
print()
print("=== 显著走阔后持有（bank3 中位） ===")
for tag, nm in [("m3", "后3月"), ("m6", "后6月"), ("m12", "后12月")]:
    s = result["forward"][tag]
    if s and s.get("bank3"): print(f"  {nm}: bank3 中位 {s['bank3']['median']}% 胜率 {s['bank3']['win_rate']}% | SPY {s['gspc']['median']}%")
print()
print("=== 著名时期案例 ===")
for c in case_summary:
    print(f"  {c['label']}: slope {c['slope_chg']:+.0f}bp | BK3 {c['bank3']}% JPM {c['jpm']}% BAC {c['bac']}% MS {c['ms']}% KRE {c['kre']}% SPY {c['gspc']}%")
print()
print("JSON saved:", os.path.join(OUT, "steep_banks.json"))
