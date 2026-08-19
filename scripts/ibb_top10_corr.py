#!/usr/bin/env python3
"""IBB 前十大成分股 vs IBB 批量对照分析。

读 data/<ticker>/ 下 CSV, 计算每只相对 IBB 的:
  - 分阶段 Pearson / Spearman / beta / 残差波动 / Fisher z
  - 分界后区间收益与相对 IBB 超额
  - 跑赢天数占比 (全期 / 分界后 / 7-15以来)
  - 跷跷板占比
输出 results/ibb_top10_corr.json。
"""
import os, json
import numpy as np
import pandas as pd
from math import atanh, sqrt, erf
from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
SPLIT = pd.Timestamp("2026-02-01")
D715 = pd.Timestamp("2026-07-15")

# 名称与权重 (2026-08 口径, 综合 Morningstar/iShares/investingfacts)
HOLDINGS = [
    ("AMGN", "安进 Amgen", 8.55), ("VRTX", "福泰制药 Vertex", 8.12),
    ("GILD", "吉利德 Gilead", 6.99), ("REGN", "再生元 Regeneron", 5.96),
    ("ARGX", "argenx", 3.37), ("NTRA", "Natera", 3.20),
    ("RVMD", "Revolution Medicines", 2.89), ("ALNY", "Alnylam", 2.21),
    ("BIIB", "渤健 Biogen", 2.26), ("ILMN", "因美纳 Illumina", 2.16),
]

def load(tk):
    df = pd.read_csv(os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 100
    return df

def pair(ibb, stk, tk, name, w):
    m = pd.merge(ibb[["date", "ret", "close"]], stk[["date", "ret", "close"]],
                 on="date", suffixes=("_x", "_y")).dropna()
    out = {"ticker": tk, "name": name, "weight": w, "n_total": len(m),
           "start": str(m["date"].iloc[0].date()), "end": str(m["date"].iloc[-1].date())}
    for blk, df in [("all", m), ("pre", m[m["date"] < SPLIT]), ("post", m[m["date"] >= SPLIT])]:
        if len(df) < 10:
            out[blk] = None
            continue
        x = df["ret_x"].values; y = df["ret_y"].values
        p = float(np.corrcoef(x, y)[0, 1])
        s = float(spearmanr(x, y).statistic)
        beta = float(np.cov(y, x)[0, 1] / np.var(x))
        resid = y - beta * x
        x_ret = (df["close_x"].iloc[-1] / df["close_x"].iloc[0] - 1) * 100
        y_ret = (df["close_y"].iloc[-1] / df["close_y"].iloc[0] - 1) * 100
        out[blk] = {
            "n": len(df),
            "pearson": round(p, 4), "spearman": round(s, 4),
            "beta": round(beta, 3), "resid_vol": round(float(resid.std()), 3),
            "r2": round(p * p, 4),
            "x_ret": round(float(x_ret), 2), "y_ret": round(float(y_ret), 2),
            "excess": round(float(y_ret - x_ret), 2),
        }
    if out.get("pre") and out.get("post"):
        r1, n1 = out["pre"]["pearson"], out["pre"]["n"]
        r2, n2 = out["post"]["pearson"], out["post"]["n"]
        z = (atanh(r1) - atanh(r2)) / sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
        pv = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
        out["fisher"] = {"z": round(z, 3), "p": round(pv, 4)}
    # 跑赢占比
    for key, df in [("all_strong", m), ("after_strong", m[m["date"] >= SPLIT]),
                    ("d715_strong", m[m["date"] >= D715])]:
        if len(df) < 10:
            out[key] = None
            continue
        strong = int((df["ret_y"] > df["ret_x"]).sum())
        out[key] = {"strong": strong, "n": len(df),
                    "pct": round(strong / len(df) * 100, 1),
                    "x_cum": round((df["close_x"].iloc[-1] / df["close_x"].iloc[0] - 1) * 100, 2),
                    "y_cum": round((df["close_y"].iloc[-1] / df["close_y"].iloc[0] - 1) * 100, 2)}
    # 2026 年内各阶段超额（x_ret/y_ret）
    YTD = pd.Timestamp("2026-01-01")
    for key, df, label in [("ytd_pre", m[(m["date"] >= YTD) & (m["date"] < SPLIT)], "2026分界前"),
                           ("ytd", m[m["date"] >= YTD], "2026以来")]:
        if len(df) < 10:
            out[key] = None
            continue
        x_ret = (df["close_x"].iloc[-1] / df["close_x"].iloc[0] - 1) * 100
        y_ret = (df["close_y"].iloc[-1] / df["close_y"].iloc[0] - 1) * 100
        out[key] = {"n": len(df), "x_ret": round(float(x_ret), 2),
                    "y_ret": round(float(y_ret), 2),
                    "excess": round(float(y_ret - x_ret), 2),
                    "label": label}
    # 分界后跷跷板
    af = m[m["date"] >= SPLIT]
    if len(af) >= 10:
        seesaw = int(((af["ret_x"] > 0) & (af["ret_y"] < 0)).sum() +
                     ((af["ret_x"] < 0) & (af["ret_y"] > 0)).sum())
        out["seesaw_after"] = {"seesaw": seesaw, "n": len(af),
                               "pct": round(seesaw / len(af) * 100, 1)}
    return out

def main():
    ibb = load("IBB")
    results = []
    for tk, name, w in HOLDINGS:
        stk = load(tk)
        results.append(pair(ibb, stk, tk, name, w))
        r = results[-1]
        post = r.get("post") or {}
        print(f"{tk:<5} {name:<22} w={w:>4.1f}% 全期r={r['all']['pearson'] if r.get('all') else '-':<7} "
              f"分界r={post.get('pearson','-'):<7} 分界超额={post.get('y_ret',0)-post.get('x_ret',0):+6.1f}pp "
              f"跑赢(分界)={r['after_strong']['pct'] if r.get('after_strong') else '-':<5}% "
              f"7/15跑赢={r['d715_strong']['pct'] if r.get('d715_strong') else '-':<5}% 跷跷板={r['seesaw_after']['pct'] if r.get('seesaw_after') else '-':<4}%")
    with open(os.path.join(OUT, "ibb_top10_corr.json"), "w", encoding="utf-8") as f:
        json.dump({"split": str(SPLIT.date()), "d715": str(D715.date()),
                   "holdings": results}, f, ensure_ascii=False, indent=1)
    print("\nsaved:", os.path.join(OUT, "ibb_top10_corr.json"))

if __name__ == "__main__":
    main()
