# -*- coding: utf-8 -*-
"""
利率灵敏度增强验证
1. 控制 CPI YoY 后，ΔUS10Y 系数是否仍显著（通胀驱动检验）
2. 近 10 年样本检验 MOS/CF 等敏感性是否稳定
3. La Niña 事件明细（每只股票每个事件窗口超额）
"""
import json
import os
import math
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "agri_verify.json")

TICKERS = ["ADM", "BG", "MOS", "CF", "NTR", "CTVA", "AGCO", "FMC", "DAR",
           "FPI", "TSN", "HRL", "MOO", "DBA", "DE", "SPY"]

def monthly_df(ticker):
    path = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    m = df["adj_close"].resample("ME").last().dropna()
    ret = m.pct_change().dropna() * 100
    r = pd.DataFrame({"ret": ret})
    r["ym"] = r.index.year * 100 + r.index.month
    return r

def rate_chg():
    d10 = pd.read_csv(os.path.join(DATA, "agri", "raw", "dgs10.csv"))
    d10["observation_date"] = pd.to_datetime(d10["observation_date"])
    d10 = d10.set_index("observation_date")["DGS10"].dropna().astype(float)
    m10 = d10.resample("ME").last().dropna()
    chg = m10.diff().dropna() * 100
    return pd.DataFrame({"ym": chg.index.year * 100 + chg.index.month, "d10_bp": chg.values})

def cpi_yoy():
    cpi = pd.read_csv(os.path.join(DATA, "agri", "raw", "cpi.csv"))
    cpi["observation_date"] = pd.to_datetime(cpi["observation_date"])
    cpi = cpi.set_index("observation_date")["CPIAUCSL"].dropna().astype(float)
    yoy = (cpi / cpi.shift(12) - 1) * 100
    m = yoy.resample("ME").last().dropna()
    return pd.DataFrame({"ym": m.index.year * 100 + m.index.month, "cpi_yoy": m.values})

rates = rate_chg()
cpi = cpi_yoy()
spy = monthly_df("SPY").set_index("ym")["ret"].to_dict()

def ols(y, xs):
    n = len(y)
    X = np.column_stack([np.ones(n)] + [np.asarray(x, dtype=float) for x in xs])
    Y = np.asarray(y, dtype=float)
    beta, res, rank, sv = np.linalg.lstsq(X, Y, rcond=None)
    yhat = X @ beta
    resid = Y - yhat
    dof = n - X.shape[1]
    s2 = resid @ resid / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    tvals = beta / se
    r2 = 1 - (resid @ resid) / ((Y - Y.mean()) @ (Y - Y.mean())) if np.var(Y) > 0 else 0
    return {"beta": [float(b) for b in beta], "t": [float(t2) for t2 in tvals],
            "se": [float(s) for s in se], "r2": float(r2), "n": int(n)}

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

# ---------- 1. 控制通胀后的回归 ----------
infl_ctrl = {}
for t in ["MOS", "CF", "DAR", "AGCO", "NTR", "DE", "ADM", "BG", "FMC"]:
    mdf = monthly_df(t).merge(rates, on="ym", how="inner").merge(cpi, on="ym", how="inner")
    mdf = mdf.dropna()
    y = mdf["ret"].values
    x_spy = np.array([spy.get(ym, np.nan) for ym in mdf["ym"].values])
    x_rate = mdf["d10_bp"].values
    x_cpi = mdf["cpi_yoy"].values
    ok = ~np.isnan(y) & ~np.isnan(x_spy) & ~np.isnan(x_rate) & ~np.isnan(x_cpi)
    if ok.sum() < 24:
        continue
    r1 = ols(y[ok], [x_rate[ok], x_spy[ok]])   # 不含 CPI
    r2 = ols(y[ok], [x_rate[ok], x_cpi[ok], x_spy[ok]])  # 含 CPI
    df1 = r1["n"] - 3
    df2 = r2["n"] - 4
    infl_ctrl[t] = {
        "n": int(ok.sum()),
        "beta10_raw": round(r1["beta"][1], 4),
        "beta10_raw_p": round(t_pval(r1["t"][1], df1), 4),
        "beta10_ctrl": round(r2["beta"][1], 4),
        "beta10_ctrl_p": round(t_pval(r2["t"][1], df2), 4),
        "beta_cpi": round(r2["beta"][2], 4),
        "beta_cpi_p": round(t_pval(r2["t"][2], df2), 4),
        "r2_raw": round(r1["r2"], 4),
        "r2_ctrl": round(r2["r2"], 4),
    }

# ---------- 2. 近10年样本 ----------
recent = {}
for t in ["MOS", "CF", "DAR", "AGCO", "NTR", "CTVA"]:
    mdf = monthly_df(t).merge(rates, on="ym", how="inner")
    mdf = mdf[mdf["ym"] >= 201601].dropna()
    if len(mdf) < 24:
        continue
    y = mdf["ret"].values
    x_spy = np.array([spy.get(ym, np.nan) for ym in mdf["ym"].values])
    x_rate = mdf["d10_bp"].values
    ok = ~np.isnan(y) & ~np.isnan(x_spy) & ~np.isnan(x_rate)
    r = ols(y[ok], [x_rate[ok], x_spy[ok]])
    dfr = r["n"] - 3
    recent[t] = {"n": int(ok.sum()),
                 "beta10": round(r["beta"][1], 4),
                 "p": round(t_pval(r["t"][1], dfr), 4),
                 "beta_spy": round(r["beta"][2], 3)}

# ---------- 3. 通胀相关性（US10Y 与 CPI 的月度联动）----------
rate_cpi_corr = rates.merge(cpi, on="ym", how="inner").dropna()
rc = np.corrcoef(rate_cpi_corr["d10_bp"], rate_cpi_corr["cpi_yoy"])[0, 1]
rate_cpi_month = {"n": len(rate_cpi_corr), "corr": round(float(rc), 4)}
# 高 CPI 月份（>4%）的利率变化均值
hi = rate_cpi_corr[rate_cpi_corr["cpi_yoy"] > 4]
lo = rate_cpi_corr[rate_cpi_corr["cpi_yoy"] <= 4]
rate_cpi_month["hi_cpi_d10_mean_bp"] = round(float(hi["d10_bp"].mean()), 1) if len(hi) else None
rate_cpi_month["lo_cpi_d10_mean_bp"] = round(float(lo["d10_bp"].mean()), 1) if len(lo) else None

out = {
    "infl_ctrl": infl_ctrl,
    "recent10": recent,
    "rate_cpi_month": rate_cpi_month,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT)
print("=== 控制 CPI 后 ===")
for t, v in infl_ctrl.items():
    print(f"{t:5s} raw_beta={v['beta10_raw']:+.3f}(p={v['beta10_raw_p']:.3f}) -> ctrl_beta={v['beta10_ctrl']:+.3f}(p={v['beta10_ctrl_p']:.3f}) | cpi_beta={v['beta_cpi']:+.3f}(p={v['beta_cpi_p']:.3f}) r2 {v['r2_raw']:.3f}->{v['r2_ctrl']:.3f}")
print("=== 近10年(2016+) ===")
for t, v in recent.items():
    print(f"{t:5s} n={v['n']} beta10={v['beta10']:+.3f} p={v['p']:.3f} spy={v['beta_spy']:.3f}")
print("=== 利率-通胀联动 ===")
print(rate_cpi_month)