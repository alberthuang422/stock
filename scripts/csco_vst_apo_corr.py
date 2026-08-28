#!/usr/bin/env python3
"""CSCO / VST / APO 两两相关性——2026-02 起（用户指定起点）。

口径（项目惯例，同 50 号 sofi_btc_corr）:
  - 日收益 pct_change×100
  - 全期 Pearson R / Spearman / β / R² / 显著带 ±1.96/√(n−2) / p 值三档(sig/edge/no)
  - 60 日滚动为主口径，30 日作辅助
  - 分月统计 + 近 20/60 交易日
  - R 与 β 同列

输出 results/csco_vst_apo_corr.json
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


def load_equity(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change() * 100
    return df[["date", "adj_close", "ret"]]


def clean(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    return a[m], b[m]


def seg_stats(df, label):
    """df: date, retx, rety, px"""
    n = len(df)
    a, b = clean(df["retx"].values, df["rety"].values)
    r = float(np.corrcoef(a, b)[0, 1]) if len(a) >= 3 else None
    s = float(spearmanr(a, b).statistic) if len(a) >= 3 else None
    if len(a) >= 3 and np.var(b) > 0:
        beta = float(np.cov(a, b)[0, 1] / np.var(b))
    else:
        beta = None
    r2 = r ** 2 if r is not None else None
    band = 1.96 / np.sqrt(n - 2) if n > 3 else None
    p_val = None
    if r is not None and n > 3 and r ** 2 < 1:
        tv = r * np.sqrt((n - 2) / (1 - r ** 2))
        p_val = float(2 * (1 - tdist.cdf(abs(tv), df=n - 2)))
    if p_val is None:
        level = "no"
    elif p_val < 0.01:
        level = "sig"
    elif p_val < 0.05:
        level = "edge"
    else:
        level = "no"
    retx = (df["px"].iloc[-1] / df["px"].iloc[0] - 1) * 100 if len(df) else None
    rety = (df["py"].iloc[-1] / df["py"].iloc[0] - 1) * 100 if len(df) else None
    return {
        "label": label, "n": int(n),
        "r": round(r, 4) if r is not None else None,
        "spearman": round(s, 4) if s is not None else None,
        "beta": round(beta, 4) if beta is not None else None,      # x 对 y 的 β（y 涨1% x 平均跟 %）
        "r2": round(r2, 4) if r2 is not None else None,
        "sig_band": round(band, 4) if band is not None else None,
        "p": round(p_val, 4) if p_val is not None else None,
        "sig_level": level,
        "ret_x": round(float(retx), 2) if retx is not None else None,
        "ret_y": round(float(rety), 2) if rety is not None else None,
        "start": str(df["date"].iloc[0].date()), "end": str(df["date"].iloc[-1].date()),
    }


def build_pair(dfx, dfy, name):
    m = pd.merge(dfx, dfy, on="date", suffixes=("_x", "_y")).dropna()
    m = m[m["date"] >= START].reset_index(drop=True)
    m.columns = ["date", "px", "retx", "py", "rety"] if len(dfx) < len(dfy) or name[0] != "C" else ["date", "px", "retx", "py", "rety"]
    # 统一列名: px/ retx 始终为第一个标的
    m = m[["date", "px", "retx", "py", "rety"]]
    print(f"[{name}] 窗口 {m['date'].iloc[0].date()} ~ {m['date'].iloc[-1].date()}  n={len(m)}")

    full = seg_stats(m, "full")

    monthly = [seg_stats(g, str(k)[:7]) for k, g in m.groupby(m["date"].dt.to_period("M")) if len(g) >= 8]

    def rolling(win):
        out = []
        for i in range(win - 1, len(m)):
            w = m.iloc[i - win + 1: i + 1]
            r, s, _ = pearson_spearman(w["retx"].values, w["rety"].values)
            b, r2 = beta_r2(w["rety"].values, w["retx"].values)
            out.append({"date": str(m["date"].iloc[i].date()),
                        "r": round(r, 4) if r is not None else None,
                        "spearman": round(s, 4) if s is not None else None,
                        "beta": round(b, 4) if b is not None else None})
        return out
    roll30 = rolling(30)
    roll60 = rolling(60)

    w20 = m.tail(20)
    last20 = seg_stats(w20, "last20")
    w60 = m.tail(60)
    last60 = seg_stats(w60, "last60")

    return {
        "name": name,
        "full": full, "monthly": monthly,
        "rolling30": roll30, "rolling60": roll60,
        "last20": last20, "last60": last60,
    }


def pearson_spearman(a, b):
    a, b = clean(a, b)
    if len(a) < 3:
        return None, None, len(a)
    r = float(np.corrcoef(a, b)[0, 1])
    s = float(spearmanr(a, b).statistic)
    return r, s, len(a)


def beta_r2(x, y):
    """y 对 x 的 β（解释变量 x=第二个标的，y=第一个标的）与 R²"""
    x, y = clean(x, y)
    if len(x) < 3 or np.var(x) == 0:
        return None, None
    beta = float(np.cov(y, x)[0, 1] / np.var(x))
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    return beta, r2


def main():
    data = {tk: load_equity(tk) for tk in TICKS}
    out = {"pairs": [], "meta": {
        "note": "2026-02-01 起; 日收益 pct_change×100; r(Pearson)=日收益线性相关; Spearman=秩相关; "
                "β = 第二标的涨1%第一标的平均跟涨%; R²=解释波动比例; 显著带 ±1.96/√(n−2); "
                "sig(p<0.01)/edge(0.01≤p<0.05)/no(p≥0.05); 涨跌幅=区间首尾累计",
        "sources": {tk: "Yahoo Finance 日线 adj_close 复权 (美东交易日)" for tk in TICKS},
        "seg_key": {"retx": "前一只(表中 x)", "px": "前一只价格", "py": "后一只价格"},
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
    }}
    pairs = [("CSCO", "VST", "CSCO×VST"), ("CSCO", "APO", "CSCO×APO"), ("VST", "APO", "VST×APO")]
    for a, b, name in pairs:
        d = build_pair(data[a], data[b], name)
        out["pairs"].append(d)
        print(f"\n== {name} ==")
        f = d["full"]
        print(f"全期 n={f['n']} r={f['r']} spearman={f['spearman']} beta={f['beta']} r2={f['r2']} "
              f"p={f['p']}({f['sig_level']}) | {a} {f['ret_x']:+.1f}% {b} {f['ret_y']:+.1f}%")
        print("月度:")
        for mo in d["monthly"]:
            print(f"  {mo['label']} n={mo['n']} r={mo['r']} sig={mo['sig_level']} beta={mo['beta']} r2={mo['r2']} "
                  f"| {a} {mo['ret_x']:+.1f}% {b} {mo['ret_y']:+.1f}%")
        print("近20:", {k: d['last20'][k] for k in ('r', 'p', 'sig_level', 'beta', 'r2')},
              f"{a} {d['last20']['ret_x']:+.1f}% {b} {d['last20']['ret_y']:+.1f}%")
        print("近60:", {k: d['last60'][k] for k in ('r', 'p', 'sig_level', 'beta', 'r2')},
              f"{a} {d['last60']['ret_x']:+.1f}% {b} {d['last60']['ret_y']:+.1f}%")

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "csco_vst_apo_corr.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nsaved:", p)


if __name__ == "__main__":
    main()