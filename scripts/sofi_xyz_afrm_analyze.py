# -*- coding: utf-8 -*-
"""SOFI / XYZ(Block) / AFRM 三家公司财报对比 + US10Y 敏感性分析
数据截至 2026-08-14。
"""
import json
import numpy as np
import pandas as pd

DATA = "/Users/alberthuang/Desktop/股票分析/data"
OUT = "/Users/alberthuang/Desktop/股票分析/results/sofi_xyz_afrm_analysis.json"

TICKERS = {"SOFI": "SoFi", "XYZ": "Block(XYZ)", "AFRM": "Affirm"}

def load_stock(tk):
    df = pd.read_csv(f"{DATA}/{tk.lower()}/{tk}, 1D.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df["ret"] = df["close"].pct_change() * 100  # 日收益 %
    return df[["close", "ret"]]

def load_dgs10():
    df = pd.read_csv(f"{DATA}/dgs10.csv")
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    df["DGS10"] = pd.to_numeric(df["DGS10"], errors="coerce")
    df = df.dropna().set_index("observation_date").sort_index()
    df["dy"] = df["DGS10"].diff() * 100  # 日变化 bp
    return df[["DGS10", "dy"]]

stocks = {tk: load_stock(tk) for tk in TICKERS}
r10 = load_dgs10()

# 合并：个股日收益 + 当日/前日 10Y 变化（用当日：10Y 收盘变化影响隔夜与当日定价，日频对齐用同一天收盘收益 vs 同一天收盘 10Y）
aligned = {}
for tk in TICKERS:
    m = pd.concat([stocks[tk]["ret"], r10["dy"], r10["DGS10"]], axis=1, join="inner").dropna()
    m.columns = ["ret", "dy", "level"]
    aligned[tk] = m

common_start = pd.Timestamp("2021-01-13")  # AFRM IPO 后共同起点
full = {tk: m[m.index >= common_start] for tk, m in aligned.items()}
last1y = {tk: m[m.index >= "2025-08-15"] for tk, m in full.items()}
last3m = {tk: m[m.index >= "2026-05-15"] for tk, m in full.items()}

def corr_ret_dy(m):
    if len(m) < 30:
        return None
    return float(np.corrcoef(m["ret"], m["dy"])[0, 1])

def ols_beta(m):
    if len(m) < 30:
        return None
    x = m["dy"].values
    y = m["ret"].values
    X = np.column_stack([np.ones(len(x)), x])
    try:
        beta = np.linalg.lstsq(X, y, rcond=None)[0][1]
    except Exception:
        return None
    return float(beta)

def rolling_corr(tk, window=60):
    m = aligned[tk]
    rc = m["ret"].rolling(window).corr(m["dy"])
    return rc.dropna()

res = {"meta": {"asof": "2026-08-14", "common_start": str(common_start.date())},
       "windows": {}, "rolling": {}, "monthly": {}, "level_buckets": {},
       "big_moves": {}, "annualized": {}, "beta": {}}

# 1. 各窗口相关 + beta
for wname, m in [("full", full), ("1y", last1y), ("3m", last3m)]:
    res["windows"][wname] = {
        tk: {"corr": corr_ret_dy(m[tk]), "beta_pct_per_10bp": (ols_beta(m[tk]) * 10 if ols_beta(m[tk]) is not None else None),
             "n": int(len(m[tk])), "mean_ret": float(m[tk]["ret"].mean()), "std_ret": float(m[tk]["ret"].std())}
        for tk in TICKERS
    }

# 2. 滚动 60 日相关（月末采样）
for tk in TICKERS:
    rc = rolling_corr(tk)
    if len(rc) == 0:
        continue
    rc = rc[~rc.index.duplicated(keep="last")]
    monthly = rc.resample("ME").last().dropna()
    res["rolling"][tk] = {
        "dates": [d.strftime("%Y-%m-%d") for d in monthly.index],
        "corr": [round(float(v), 4) for v in monthly.values],
        "avg": float(rc.mean()), "last": float(rc.iloc[-1]),
        "latest_date": rc.index[-1].strftime("%Y-%m-%d"),
    }

# 3. 月度：10Y 上行月 vs 下行月个股月收益
m10 = r10["DGS10"].resample("ME").last()
m10_diff = m10.diff().dropna()
mst = {}
for tk in TICKERS:
    mst[tk] = stocks[tk]["close"].resample("ME").last().pct_change() * 100
mst = pd.DataFrame(mst).dropna()
mdf = pd.DataFrame({"m10": m10_diff, "up": m10_diff > 0})
mdf["month"] = mdf.index
common_m = mdf.index.intersection(mst.index)
mdf = mdf.loc[common_m]
mst = mst.loc[common_m]
res["monthly"] = {
    "n_up": int((mdf["up"]).sum()), "n_down": int((~mdf["up"]).sum()),
    "n_total": int(len(mdf)),
    "up_months": {tk: float(mst.loc[mdf["up"], tk].mean()) for tk in TICKERS},
    "down_months": {tk: float(mst.loc[~mdf["up"], tk].mean()) for tk in TICKERS},
    "all_months": {tk: float(mst[tk].mean()) for tk in TICKERS},
    "corr_month_ret_dy": {tk: float(np.corrcoef(mst[tk], mdf["m10"])[0, 1]) for tk in TICKERS},
}
# 分年（2022-2026 每年 10Y 变化与个股收益）
mst_y = mst.copy(); mst_y["year"] = mst_y.index.year
by_year = {}
for yr, g in mst_y.groupby("year"):
    by_year[str(yr)] = {"m10_chg": float(m10_diff.loc[g.index].sum()),
                        **{tk: float(g[tk].mean()) for tk in TICKERS}}
res["monthly"]["by_year"] = by_year

# 4. 利率水平分档（按日）
buckets = [(0, 4.0, "<4.0%"), (4.0, 4.5, "4.0-4.5%"), (4.5, 5.0, "4.5-5.0%"), (5.0, 99, ">=5.0%")]
for tk in TICKERS:
    m = full[tk]
    out = {}
    for lo, hi, label in buckets:
        sub = m[(m["level"] >= lo) & (m["level"] < hi)]
        if len(sub) > 30:
            out[label] = {"days": int(len(sub)), "avg_ret": float(sub["ret"].mean()),
                          "ann": float(sub["ret"].mean() * 252)}
    res["level_buckets"][tk] = out

# 5. 10Y 大波动日（|Δ10Y|>=12bp）个股平均收益
th = 12
for tk in TICKERS:
    m = full[tk]
    up = m[m["dy"] >= th]
    down = m[m["dy"] <= -th]
    res["big_moves"][tk] = {
        "n_up": int(len(up)), "avg_ret_up": float(up["ret"].mean()) if len(up) else None,
        "n_down": int(len(down)), "avg_ret_down": float(down["ret"].mean()) if len(down) else None,
    }

# 6. 归一化净值（报告图用，月末）
for tk in TICKERS:
    c = stocks[tk]["close"]
    c = c[c.index >= common_start]
    c = c[~c.index.duplicated(keep="last")]
    monthly = c.resample("ME").last()
    res["annualized"][tk] = {
        "dates": [d.strftime("%Y-%m-%d") for d in monthly.index],
        "nav": [round(float(v / monthly.iloc[0]), 4) for v in monthly.values],
    }
# 10Y 月末水平（图用）
m10_all = r10["DGS10"][r10["DGS10"].index >= common_start]
m10_all = m10_all[~m10_all.index.duplicated(keep="last")].resample("ME").last()
res["annualized"]["10Y"] = {
    "dates": [d.strftime("%Y-%m-%d") for d in m10_all.index],
    "level": [round(float(v), 2) for v in m10_all.values],
}

# 7. 回撤（健康度参考）
def max_drawdown(close):
    return float((close / close.cummax() - 1).min() * 100)

res["drawdown"] = {tk: max_drawdown(stocks[tk]["close"][stocks[tk]["close"].index >= common_start]) for tk in TICKERS}
res["drawdown_1y"] = {tk: max_drawdown(stocks[tk]["close"][stocks[tk]["close"].index >= "2025-08-15"]) for tk in TICKERS}

# 8. 各股上市以来累计收益
for tk in TICKERS:
    c = stocks[tk]["close"]
    res["annualized"][tk]["cum_return"] = float((c.iloc[-1] / c.iloc[0] - 1) * 100)
    res["annualized"][tk]["cum_return_since_common"] = float((c[c.index >= common_start].iloc[-1] / c[c.index >= common_start].iloc[0] - 1) * 100)

def np_round(o):
    if isinstance(o, dict):
        return {k: np_round(v) for k, v in o.items()}
    if isinstance(o, list):
        return [np_round(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(np_round(res), f, ensure_ascii=False, indent=1)

print("=== 全期(2021-01起) 日收益 vs Δ10Y ===")
for tk in TICKERS:
    w = res["windows"]["full"][tk]
    print(f"{tk}: corr={w['corr']:.3f}  beta(每10bp)={w['beta_pct_per_10bp']:.4f}%  n={w['n']}")
print("\n=== 近1年 ===")
for tk in TICKERS:
    w = res["windows"]["1y"][tk]
    print(f"{tk}: corr={w['corr']:.3f}  beta(每10bp)={w['beta_pct_per_10bp']:.4f}%  n={w['n']}")
print("\n=== 滚动60日相关 均值/最新 ===")
for tk in TICKERS:
    r = res["rolling"][tk]
    print(f"{tk}: avg={r['avg']:.3f}  last={r['last']:.3f} ({r['latest_date']})")
print("\n=== 月度: 10Y上行月 vs 下行月 平均月收益 ===")
for tk in TICKERS:
    print(f"{tk}: up={res['monthly']['up_months'][tk]:.2f}%  down={res['monthly']['down_months'][tk]:.2f}%  all={res['monthly']['all_months'][tk]:.2f}%  corr={res['monthly']['corr_month_ret_dy'][tk]:.3f}")
print("\n=== 利率分档 平均日收益(bp) ===")
for tk in TICKERS:
    s = "  ".join(f"{k}:{v['avg_ret']*100:.1f}bp" for k, v in res["level_buckets"][tk].items())
    print(f"{tk}: {s}")
print("\n=== 大波动日 |Δ10Y|>=12bp ===")
for tk in TICKERS:
    b = res["big_moves"][tk]
    print(f"{tk}: 上行日{b['n_up']}个 avg {b['avg_ret_up']:.2f}% / 下行日{b['n_down']}个 avg {b['avg_ret_down']:.2f}%")
print("\n=== 回撤 ===")
print({k: round(v, 1) for k, v in res["drawdown"].items()})
print("by_year:", json.dumps(res["monthly"]["by_year"], ensure_ascii=False))
