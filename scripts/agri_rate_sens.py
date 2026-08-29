# -*- coding: utf-8 -*-
"""
农业股 × 利率敏感性量化分析
- 月频回归：ret_agri = α + β1 × ΔUS10Y(bp) + β2 × ret_SPY + ε
- 利率上行/下行月分组表现（US10Y 月度变动>0/<0）
- 敏感性子行业拆解（农机资本品 / 化肥商品 / 粮商贸易 / 农业REIT）
- β 统计显著性 + R² + t/p
"""
import json
import os
import math
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "agri_rate_sens.json")

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
    m = df["adj_close"].resample("ME").last().dropna()
    ret = m.pct_change().dropna() * 100
    r = pd.DataFrame({"ret": ret})
    r["y"] = r.index.year
    r["m"] = r.index.month
    r["ym"] = r.index.year * 100 + r.index.month
    return r

# 利率月度变动
def rate_monthly():
    d10 = pd.read_csv(os.path.join(DATA, "agri", "raw", "dgs10.csv"))
    d10["observation_date"] = pd.to_datetime(d10["observation_date"])
    d10 = d10.set_index("observation_date")["DGS10"].dropna()
    d10 = d10.astype(float)
    m10 = d10.resample("ME").last().dropna()
    # 月度变动（月末值 diff）
    chg = m10.diff().dropna() * 100  # 单位 bp
    out = pd.DataFrame({"d10_bp": chg})
    out["y"] = chg.index.year
    out["m"] = chg.index.month
    out["ym"] = chg.index.year * 100 + chg.index.month
    return out, m10

rates, m10 = rate_monthly()

def build_panel():
    """合并所有标的面板数据"""
    rows = []
    for t in TICKERS:
        mdf = monthly_df(t)
        mdf = mdf.merge(rates[["ym", "d10_bp"]], on="ym", how="inner")
        mdf = mdf.dropna(subset=["d10_bp"])
        mdf["ticker"] = t
        rows.append(mdf)
    panel = pd.concat(rows, ignore_index=True)
    return panel

panel = build_panel()

# SPY 月收益
spy = monthly_df("SPY").set_index("ym")["ret"].to_dict()

def ols(y, x):
    """y: (n,), x: (n,k) 带常数项"""
    n = len(y)
    X = np.column_stack([np.ones(n)] + [np.asarray(xi, dtype=float) for xi in x])
    Y = np.asarray(y, dtype=float)
    try:
        beta, res, rank, sv = np.linalg.lstsq(X, Y, rcond=None)
    except np.linalg.LinAlgError:
        return None
    yhat = X @ beta
    resid = Y - yhat
    dof = n - X.shape[1]
    if dof <= 0:
        return None
    s2 = resid @ resid / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    tvals = beta / se
    r2 = 1 - (resid @ resid) / ((Y - Y.mean()) @ (Y - Y.mean())) if np.var(Y) > 0 else 0
    return {"beta": [float(b) for b in beta], "se": [float(s) for s in se],
            "t": [float(t2) for t2 in tvals], "r2": float(r2), "n": int(n)}

def t_pval(t, df):
    """双侧 p 值：df>=30 用正态近似，df<30 用数值积分"""
    if df >= 30:
        x = abs(float(t))
        # Abramowitz-Stegun 正态 CDF 近似
        b1, b2, b3, b4, b5 = 0.319381530, -0.356563782, 1.781477937, -1.821255978, 1.330274429
        p = 0.2316419
        if x > 38:
            return 0.0
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

# 每个 ticker 回归
reg_res = {}
for t in TICKERS:
    sub = panel[panel["ticker"] == t].dropna(subset=["ret"])
    if len(sub) < 24:
        reg_res[t] = {"n": int(len(sub)), "error": "insufficient"}
        continue
    y = sub["ret"].values
    x_d10 = sub["d10_bp"].values
    x_spy = np.array([spy.get(ym, np.nan) for ym in sub["ym"].values])
    ok = ~np.isnan(y) & ~np.isnan(x_d10) & ~np.isnan(x_spy)
    y2, xd, xs = y[ok], x_d10[ok], x_spy[ok]
    if len(y2) < 24:
        reg_res[t] = {"n": int(len(y2)), "error": "insufficient"}
        continue
    res = ols(y2, [xd, xs])
    if res is None:
        reg_res[t] = {"n": int(len(y2)), "error": "lstsq fail"}
        continue
    dfree = res["n"] - 3
    p10 = t_pval(res["t"][1], dfree)
    pspy = t_pval(res["t"][2], dfree)
    reg_res[t] = {
        "n": res["n"], "r2": round(res["r2"], 4),
        "alpha": round(res["beta"][0], 3),
        "beta10": round(res["beta"][1], 4),
        "beta10_t": round(res["t"][1], 2), "beta10_p": round(p10, 4),
        "beta_spy": round(res["beta"][2], 3), "beta_spy_p": round(pspy, 4),
        "ann_alpha": round(res["beta"][0] * 12, 2),
    }
    if p10 < 0.01:
        reg_res[t]["sens_sig"] = "sig"
    elif p10 < 0.05:
        reg_res[t]["sens_sig"] = "edge"
    else:
        reg_res[t]["sens_sig"] = "no"

# 利率上行 / 下行月分组
rate_up_months = set(rates.loc[rates["d10_bp"] > 5, "ym"])   # >5bp
rate_dn_months = set(rates.loc[rates["d10_bp"] < -5, "ym"])  # <-5bp
rate_flat_months = set(rates.loc[(rates["d10_bp"] >= -5) & (rates["d10_bp"] <= 5), "ym"])

def group_mean(t, months):
    sub = panel[panel["ticker"] == t]
    if len(sub) == 0:
        return None
    m_list = [mm for mm in months if mm in set(sub["ym"])]
    if len(m_list) < 6:
        return None
    rets = sub[sub["ym"].isin(m_list)]["ret"].dropna()
    spy_rets = np.array([spy.get(mm, np.nan) for mm in m_list])
    ex = rets.mean() - np.nanmean(spy_rets)
    return {"n": int(len(rets)), "mean": round(float(rets.mean()), 3),
            "med": round(float(rets.median()), 3),
            "excess": round(float(ex), 3),
            "win": round(float((rets > 0).mean()) * 100, 0)}

rate_groups = {t: {"up": group_mean(t, rate_up_months),
                   "dn": group_mean(t, rate_dn_months),
                   "flat": group_mean(t, rate_flat_months)}
               for t in TICKERS}

# 子行业汇总
sub_agg = {}
for s in set(SUB.values()):
    mem = [t for t, ss in SUB.items() if ss == s and t != "SPY"]
    agg_up, agg_dn = [], []
    for t in mem:
        gu = rate_groups[t]["up"]
        gd = rate_groups[t]["dn"]
        if gu and gu["excess"] is not None:
            agg_up.append(gu["excess"])
        if gd and gd["excess"] is not None:
            agg_dn.append(gd["excess"])
    sub_agg[s] = {
        "mems": mem,
        "up_excess": round(float(np.mean(agg_up)), 3) if agg_up else None,
        "dn_excess": round(float(np.mean(agg_dn)), 3) if agg_dn else None,
    }

# 利率上行/下行月概览
rate_months_meta = {"up": len(rate_up_months), "dn": len(rate_dn_months),
                    "flat": len(rate_flat_months)}
# 速率统计
rate_stats = {"up_mean_bp": round(float(rates[rates["d10_bp"] > 5]["d10_bp"].mean()), 1),
              "dn_mean_bp": round(float(rates[rates["d10_bp"] < -5]["d10_bp"].mean()), 1),
              "range": [str(rates["ym"].min()), str(rates["ym"].max())]}

# 长端 vs 短端（敏感性检查：d2 利率）
d2 = pd.read_csv(os.path.join(DATA, "agri", "raw", "dgs2.csv"))
d2["observation_date"] = pd.to_datetime(d2["observation_date"])
d2 = d2.set_index("observation_date")["DGS2"].dropna().astype(float)
m2 = d2.resample("ME").last().dropna()
chg2 = m2.diff().dropna() * 100
rates2 = pd.DataFrame({"ym": chg2.index.year * 100 + chg2.index.month, "d2_bp": chg2.values})

# 双因子回归含 d2
reg2_res = {}
for t in ["DE", "AGCO", "MOS", "CF", "ADM", "BG", "FPI", "DAR", "CTVA", "FMC"]:
    sub = panel[panel["ticker"] == t].merge(rates2, on="ym", how="inner").dropna(subset=["d2_bp"])
    if len(sub) < 24:
        continue
    y = sub["ret"].values
    x_spy = np.array([spy.get(ym, np.nan) for ym in sub["ym"].values])
    x_d10 = sub["d10_bp"].values
    x_d2 = sub["d2_bp"].values
    ok = ~np.isnan(y) & ~np.isnan(x_spy) & ~np.isnan(x_d10) & ~np.isnan(x_d2)
    y2, xs, x1, x2 = y[ok], x_spy[ok], x_d10[ok], x_d2[ok]
    if len(y2) < 24:
        continue
    try:
        res = ols(y2, [x1, x2, xs])
    except Exception:
        continue
    dfree = res["n"] - 4
    reg2_res[t] = {
        "n": res["n"], "r2": round(res["r2"], 4),
        "beta10": round(res["beta"][1], 4), "beta10_p": round(t_pval(res["t"][1], dfree), 4),
        "beta2": round(res["beta"][2], 4), "beta2_p": round(t_pval(res["t"][2], dfree), 4),
        "beta_spy": round(res["beta"][3], 3),
    }

out = {
    "reg": reg_res,
    "reg_d2": reg2_res,
    "groups": rate_groups,
    "sub_agg": sub_agg,
    "rate_months_meta": rate_months_meta,
    "rate_stats": rate_stats,
    "subsector": SUB,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT, os.path.getsize(OUT), "bytes")
print("up months:", rate_months_meta["up"], " dn:", rate_months_meta["dn"], " flat:", rate_months_meta["flat"])