# -*- coding: utf-8 -*-
"""IPP 板块 2026-08-18 大跌归因分析 v2（单位统一为百分数）"""
import json, os, glob
import pandas as pd
import numpy as np

BASE = "/Users/alberthuang/Desktop/股票分析"
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "ipp_drop_0818.json")

TICKERS = {
    "TLN": "Talen Energy",
    "NRG": "NRG Energy",
    "CEG": "Constellation Energy",
    "VST": "Vistra",
    "XLU": "公用事业ETF XLU",
    "UTES": "电力ETF UTES",
    "SPY": "标普500 ETF",
}

def load(tk):
    f = [x for x in glob.glob(os.path.join(DATA, tk.lower(), "*.csv")) if "BATS_" not in x][0]
    df = pd.read_csv(f, parse_dates=["date"])
    df = df.drop_duplicates("date").set_index("date").sort_index()
    df["ret_pct"] = df["close"].pct_change() * 100  # 百分数
    return df

def pct(a, b):
    return (a / b - 1) * 100

dfs = {k: load(k) for k in TICKERS}
d1, d2, d3 = pd.Timestamp("2026-08-14"), pd.Timestamp("2026-08-17"), pd.Timestamp("2026-08-18")
assert d3 in dfs["TLN"].index

stats = {}
for k, name in TICKERS.items():
    df = dfs[k]
    c14, c17, c18 = df.loc[d1, "close"], df.loc[d2, "close"], df.loc[d3, "close"]
    hi52 = df["close"].tail(252).max(); lo52 = df["close"].tail(252).min()
    hi52_d = df["close"].tail(252).idxmax(); lo52_d = df["close"].tail(252).idxmin()
    vol18 = df.loc[d3, "volume"]; vol_avg = df["volume"].iloc[-31:-1].mean()
    stats[k] = {
        "name": name,
        "close_0814": round(float(c14), 2),
        "close_0817": round(float(c17), 2),
        "close_0818": round(float(c18), 2),
        "ret_0817": round(pct(c17, c14), 2),
        "ret_0818": round(pct(c18, c17), 2),
        "ret_5d": round(pct(c18, df["close"].iloc[-6]), 2),
        "ret_20d": round(pct(c18, df["close"].iloc[-21]), 2),
        "hi52": round(float(hi52), 2), "hi52_date": str(hi52_d.date()),
        "off_hi52": round(pct(c18, hi52), 2),
        "lo52": round(float(lo52), 2), "lo52_date": str(lo52_d.date()),
        "off_lo52": round(pct(c18, lo52), 2),
        "vol_ratio": round(float(vol18 / vol_avg), 2),
        "ret_hist_min": round(float(df["ret_pct"].min()), 2),
        "ret_hist_p1": round(float(df["ret_pct"].quantile(0.01)), 2),
    }

# ---- 板块等权 & beta 分解（全用百分数）----
members = ["TLN", "NRG", "CEG", "VST"]
px = pd.DataFrame({k: dfs[k]["close"] for k in members}).dropna()
mkt_ret = dfs["SPY"]["ret_pct"]
idx_ret = px.pct_change().mean(axis=1) * 100
joint = pd.concat([idx_ret.rename("idx"), mkt_ret.rename("spy")], axis=1).dropna()
joint["cov60"] = joint["idx"].rolling(60).cov(joint["spy"])
joint["var60"] = joint["spy"].rolling(60).var()
joint["beta"] = joint["cov60"] / joint["var60"]
beta_latest = float(joint["beta"].iloc[-1])
spy_d18 = float(mkt_ret.loc[d3])
idx_d18 = float(idx_ret.loc[d3])
excess = idx_d18 - spy_d18
expected = beta_latest * spy_d18
resid = idx_d18 - expected
print(f"板块等权 8/18: {idx_d18:.2f}% | SPY: {spy_d18:.2f}% | 超额 {excess:+.2f}pp")
print(f"60日 beta(vs SPY): {beta_latest:.2f} | beta期望跌幅 {expected:.2f}% | 残差 {resid:+.2f}pp")

stock_resid = {}
for k in members:
    s = dfs[k]["ret_pct"]
    j2 = pd.concat([s.rename("s"), mkt_ret.rename("spy")], axis=1).dropna()
    j2["beta"] = j2["s"].rolling(60).cov(j2["spy"]) / j2["spy"].rolling(60).var()
    b = float(j2["beta"].iloc[-1])
    actual = float(j2["s"].loc[d3])
    exp = b * spy_d18
    r = actual - exp
    stock_resid[k] = {"beta": round(b, 2), "expected": round(exp, 2),
                      "actual": round(actual, 2), "resid": round(r, 2)}
    print(f"{k}: beta {b:.2f} | 实际 {actual:.2f}% | beta期望 {exp:.2f}% | 残差 {r:+.2f}pp")

# ---- 8/18 跌幅历史分位（2025 年以来 vs 全历史）----
hist_pct = {}
for k in members:
    r = dfs[k]["ret_pct"]
    r25 = r[r.index >= "2025-01-01"]
    hist_pct[k] = {
        "pct_2025": round(float((r25 <= stats[k]["ret_0818"]).mean() * 100), 1),
        "pct_all": round(float((r <= stats[k]["ret_0818"]).mean() * 100), 1),
    }
    print(f"{k}: 8/18 跌幅历史分位(2025以来) = 小于该跌幅的日子占比 {hist_pct[k]['pct_2025']}%")

# ---- 2026 年内最大回撤 ----
drawdowns = {}
for k in members:
    s = dfs[k]["close"]; ytd = s[s.index >= "2026-01-01"]
    dd = (ytd / ytd.cummax() - 1).min() * 100
    drawdowns[k] = round(float(dd), 2)

# ---- 近 6 个月走势（图表用）----
norm = {}
base_d = "2026-02-18"
for k in TICKERS:
    s = dfs[k]["close"].tail(130)
    base = s.loc[:base_d].iloc[-1]
    norm[k] = {"date": [str(d.date()) for d in s.index],
               "idx": [round(float(x) / base * 100, 2) for x in s.values]}

dgs30_df = None
if os.path.exists(os.path.join(DATA, "dgs30.csv")):
    dgs30_df = pd.read_csv(os.path.join(DATA, "dgs30.csv"), parse_dates=["date"]).set_index("date")["dgs30"]
d30 = None
if dgs30_df is not None:
    s = dgs30_df.tail(130)
    d30 = {"date": [str(d.date()) for d in s.index], "yield": [round(float(x), 3) for x in s.values]}
    last = dgs30_df.tail(8)
    print("\nDGS30 最近 8 个观测:", [(str(d.date()), round(float(v), 3)) for d, v in last.items()])

out = {
    "generated": "2026-08-19",
    "stats": stats,
    "sector": {
        "ret_0818_idx": round(idx_d18, 2), "ret_0818_spy": round(spy_d18, 2),
        "excess_0818": round(excess, 2), "beta_60d": beta_latest,
        "expected_beta_drop": round(expected, 2), "resid": round(resid, 2),
        "members_avg_dd_2026": drawdowns,
    },
    "stock_resid": stock_resid,
    "hist_pct": hist_pct,
    "series": {"norm": norm, "dgs30": d30},
}
with open(OUT, "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n已保存:", OUT)
