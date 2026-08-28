#!/usr/bin/env python3
"""CSCO/VST/APO 相关性加固验证——回应"三者相关性很低吗"质疑。

维度:
  1. 周频收益相关性（日频噪声低敏）2026-02 起
  2. 剥离 SPY(市场) 后残差相关性（纯个股联动）
  3. 极端日联动: 单日 |ret|>=2% 的同步率 & 平均对侧收益
  4. 分段: 2026-02~04 vs 2026-05~08
  5. 全期 n=144 的 95% 显著带核对
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


def clean(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    return a[m], b[m]


def r_p_beta(a, b):
    """Pearson r, p, beta(b 对 a 的 pct 解释... 用 a=x 作为解释), n"""
    a, b = clean(a, b)
    n = len(a)
    if n < 3 or np.var(a) == 0:
        return None, None, None, n
    r = float(np.corrcoef(a, b)[0, 1])
    pv = None
    if r ** 2 < 1:
        tv = r * np.sqrt((n - 2) / (1 - r ** 2))
        pv = float(2 * (1 - tdist.cdf(abs(tv), df=n - 2)))
    beta = float(np.cov(b, a)[0, 1] / np.var(a))
    return r, pv, beta, n


def weekly_corr(dfx, dfy):
    def to_week(df):
        d = df.copy()
        d["wk"] = d["date"].dt.to_period("W")
        g = d.groupby("wk").agg(px_last=("adj_close", "last"), px_first=("adj_close", "first"))
        g["wret"] = (g["px_last"] / g["px_first"] - 1) * 100
        return g["wret"].reset_index().rename(columns={"wret": "ret"})
    wx, wy = to_week(dfx), to_week(dfy)
    m = pd.merge(wx, wy, on="wk", suffixes=("_x", "_y")).dropna()
    m = m[m["wk"].astype(str).str[:7] >= "2026-02"]
    return m, r_p_beta(m["ret_x"].values, m["ret_y"].values)


def residual_corr(dfx, dfy, mkt):
    def reg(df, mm):
        mm = pd.merge(df, mm, on="date", suffixes=("", "_m")).dropna()
        mm = mm[mm["date"] >= START]
        x = mm["mkt_ret"].values
        y = mm["ret"].values
        m = ~(np.isnan(x) | np.isnan(y))
        if m.sum() < 30 or np.var(x[m]) == 0:
            return None
        x, y = x[m], y[m]
        slope, intercept = np.polyfit(x, y, 1)
        resid = y - (slope * x + intercept)
        return pd.DataFrame({"date": mm["date"].values[m], "resid": resid})
    rx, ry = reg(dfx, mkt), reg(dfy, mkt)
    if rx is None or ry is None:
        return None, None, None, None, 0
    m = pd.merge(rx, ry, on="date", suffixes=("_x", "_y")).dropna()
    r, pv, beta, n = r_p_beta(m["resid_x"].values, m["resid_y"].values)
    return m, r, pv, beta, n


def extreme_sync(dfx, dfy):
    m = pd.merge(dfx, dfy, on="date", suffixes=("_x", "_y")).dropna()
    m = m[m["date"] >= START].reset_index(drop=True)
    ex = m[np.abs(m["ret_x"]) >= 2.0]
    ey = m[np.abs(m["ret_y"]) >= 2.0]
    both = m[(np.abs(m["ret_x"]) >= 2.0) & (np.abs(m["ret_y"]) >= 2.0)]
    return {
        "n_days": int(len(m)),
        "x_extreme_days": int(len(ex)), "y_extreme_days": int(len(ey)),
        "both_extreme_same_day": int(len(both)),
        "x_extreme_y_avg": round(float(ey["ret_y"].mean()), 2) if len(ey) else None,
        "same_sign_rate": round(float(len(both) / max(len(ex) + len(ey), 1) * 100), 1),
    }


def main():
    data = {tk: load_equity(tk) for tk in TICKS}
    spy = load_equity("SPY").rename(columns={"ret": "mkt_ret", "adj_close": "mkt_px"})
    out = {"pairs": [], "meta": {"note": "2026-02-01 起; 数据 Yahoo adj_close"}}

    import itertools
    for a, b in [("CSCO", "VST"), ("CSCO", "APO"), ("VST", "APO")]:
        dfx, dfy = data[a], data[b]
        # 1. 日频全期（对照）
        m = pd.merge(dfx, dfy, on="date", suffixes=("_x", "_y")).dropna()
        m = m[m["date"] >= START]
        r_d, p_d, beta_d, n_d = r_p_beta(m["ret_x"].values, m["ret_y"].values)

        # 2. 周频
        wm, (r_w, p_w, beta_w, n_w) = weekly_corr(dfx, dfy)

        # 3. SPY 剥离残差
        rm, r_r, p_r, beta_r, n_r = residual_corr(dfx, dfy, spy)

        # 4. 极端日
        es = extreme_sync(dfx, dfy)

        # 5. 分段（按月份做两个半段）
        m1 = m[m["date"] < "2026-05-01"]
        m2 = m[m["date"] >= "2026-05-01"]
        r1, p1, b1, n1 = r_p_beta(m1["ret_x"].values, m1["ret_y"].values)
        r2, p2, b2, n2 = r_p_beta(m2["ret_x"].values, m2["ret_y"].values)

        seg = {
            "pair": f"{a}×{b}",
            "daily_full": {"r": round(r_d, 4) if r_d is not None else None, "p": round(p_d, 4) if p_d is not None else None,
                           "beta": round(beta_d, 4) if beta_d is not None else None, "n": int(n_d)},
            "weekly": {"r": round(r_w, 4) if r_w is not None else None, "p": round(p_w, 4) if p_w is not None else None,
                       "beta": round(beta_w, 4) if beta_w is not None else None, "n": int(n_w),
                       "weeks": [str(x) for x in wm["wk"].astype(str)] if wm is not None else []},
            "resid_vs_spy": {"r": round(r_r, 4) if r_r is not None else None, "p": round(p_r, 4) if p_r is not None else None,
                             "beta": round(beta_r, 4) if beta_r is not None else None, "n": int(n_r)},
            "extreme": es,
            "h1_feb_apr": {"r": round(r1, 4) if r1 is not None else None, "p": round(p1, 4) if p1 is not None else None, "n": int(n1)},
            "h2_may_aug": {"r": round(r2, 4) if r2 is not None else None, "p": round(p2, 4) if p2 is not None else None, "n": int(n2)},
        }
        out["pairs"].append(seg)
        print(f"\n== {a}×{b} ==")
        print(f"日频: r={seg['daily_full']['r']} p={seg['daily_full']['p']} n={seg['daily_full']['n']}")
        print(f"周频: r={seg['weekly']['r']} p={seg['weekly']['p']} n={seg['weekly']['n']}")
        print(f"SPY残差: r={seg['resid_vs_spy']['r']} p={seg['resid_vs_spy']['p']} n={seg['resid_vs_spy']['n']}")
        print(f"极端日: {es}")
        print(f"分段 feb-apr r={seg['h1_feb_apr']['r']} (n={n1}) | may-aug r={seg['h2_may_aug']['r']} (n={n2})")

    p = os.path.join(OUT, "csco_vst_apo_corr_verify.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nsaved:", p)


if __name__ == "__main__":
    main()