#!/usr/bin/env python3
"""CSCO / VST / APO × SPY 相关性——2026-02 起（用户口径），附全期/2026以来/月度。

口径（项目惯例）:
  - 日收益 pct_change×100，Pearson R / Spearman / β / R²
  - β = SPY 涨 1% 该股平均跟涨%（SPY 为解释变量）
  - 显著带 ±1.96/√(n−2)，p 值三档 sig/edge/no
  - 60 日滚动相关性（主口径）
输出 results/csco_vst_apo_vs_spy.json
"""
import os, json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, t as tdist

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
START = pd.Timestamp("2026-02-01")
TICKS = ["CSCO", "VST", "APO"]


def load_equity(tk, dirname=None):
    d = dirname or tk.lower()
    p = os.path.join(DATA, d, f"{tk.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change() * 100
    return df[["date", "adj_close", "ret"]]


def calc(a, b, n_needed=3):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    n = len(a)
    if n < n_needed or np.var(b) == 0:
        return {"n": int(n), "r": None, "spearman": None, "beta": None, "r2": None, "sig_band": None, "p": None, "sig_level": "no"}
    r = float(np.corrcoef(a, b)[0, 1])
    s = float(spearmanr(a, b).statistic)
    beta = float(np.cov(a, b)[0, 1] / np.var(b))   # a=标的收益, b=SPY收益 → 标的对 SPY 的 β
    r2 = r ** 2
    band = 1.96 / np.sqrt(n - 2) if n > 3 else None
    pv = None
    if r ** 2 < 1 and n > 3:
        tv = r * np.sqrt((n - 2) / (1 - r ** 2))
        pv = float(2 * (1 - tdist.cdf(abs(tv), df=n - 2)))
    if pv is None:
        level = "no"
    elif pv < 0.01:
        level = "sig"
    elif pv < 0.05:
        level = "edge"
    else:
        level = "no"
    return {"n": int(n), "r": round(r, 4), "spearman": round(s, 4), "beta": round(beta, 4),
            "r2": round(r2, 4), "sig_band": round(band, 4) if band else None,
            "p": round(pv, 4) if pv is not None else None, "sig_level": level}


def seg(df, label):
    d = {"label": label}
    d.update(calc(df["ret"].values, df["spy_ret"].values))
    d["ret_stock"] = round(float((df["adj_close"].iloc[-1] / df["adj_close"].iloc[0] - 1) * 100), 2) if len(df) else None
    d["ret_spy"] = round(float((df["spy_px"].iloc[-1] / df["spy_px"].iloc[0] - 1) * 100), 2) if len(df) else None
    d["start"] = str(df["date"].iloc[0].date()) if len(df) else None
    d["end"] = str(df["date"].iloc[-1].date()) if len(df) else None
    return d


def main():
    spy = load_equity("SPY").rename(columns={"ret": "spy_ret", "adj_close": "spy_px"})
    out = {"stocks": [], "meta": {
        "note": "口径: 日收益 pct_change×100; r(Pearson)=与 SPY 日收益线性相关; Spearman=秩相关; "
                "β=SPY 涨1%该股平均跟涨%; R²=SPY 解释该股波动比例; 显著带±1.96/√(n−2); "
                "sig(p<0.01)/edge(0.01≤p<0.05)/no(p≥0.05); 涨跌幅=区间首尾累计",
        "sources": {"SPY": "Yahoo Finance 日线 adj_close 复权 (SPDR S&P500 ETF)", **{tk: "Yahoo Finance 日线 adj_close 复权" for tk in TICKS}},
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
    }}
    for tk in TICKS:
        stk = load_equity(tk)
        m = pd.merge(stk, spy, on="date", suffixes=("", "_s")).dropna().sort_values("date").reset_index(drop=True)
        full = seg(m, "全期(1993交集)")
        since26 = seg(m[m["date"] >= "2026-01-01"], "2026 以来")
        since_feb = seg(m[m["date"] >= START], "2026-02 起(用户口径)")
        monthly = [seg(g, str(k)[:7]) for k, g in m[m["date"] >= START].groupby(m["date"].dt.to_period("M")) if len(g) >= 8]
        # 60 日滚动
        mf = m[m["date"] >= START].reset_index(drop=True)
        roll = []
        for i in range(59, len(mf)):
            w = mf.iloc[i - 59: i + 1]
            c = calc(w["ret"].values, w["spy_ret"].values)
            roll.append({"date": str(mf["date"].iloc[i].date()), "r": c["r"], "beta": c["beta"]})
        # 近 20/60 交易日
        last20 = seg(m.tail(20), "近20交易日")
        last60 = seg(m.tail(60), "近60交易日")
        d = {"ticker": tk, "full": full, "since26": since26, "since_feb": since_feb,
             "monthly": monthly, "rolling60": roll, "last20": last20, "last60": last60}
        out["stocks"].append(d)
        print(f"\n== {tk} × SPY ==")
        print(f"全期: {full['r']} (n={full['n']}) | 2026以来: {since26['r']} ({since26['sig_level']}) | "
              f"2026-02起: {since_feb['r']} p={since_feb['p']} beta={since_feb['beta']} r2={since_feb['r2']} | "
              f"{tk} {since_feb['ret_stock']:+.1f}% SPY {since_feb['ret_spy']:+.1f}%")
        print("月度:")
        for mo in monthly:
            print(f"  {mo['label']} n={mo['n']} r={mo['r']} sig={mo['sig_level']} beta={mo['beta']} | "
                  f"{tk} {mo['ret_stock']:+.1f}% SPY {mo['ret_spy']:+.1f}%")
        print(f"近20: r={last20['r']} p={last20['p']} | 近60: r={last60['r']} p={last60['p']}")

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "csco_vst_apo_vs_spy.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nsaved:", p)


if __name__ == "__main__":
    main()