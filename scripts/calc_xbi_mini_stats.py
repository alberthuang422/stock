# -*- coding: utf-8 -*-
"""本地量化：XBI/IBB/XPH 2022-2026 年度统计 + 10Y 利率环境
输出: results/xbi_mini_stats.json
口径: 年度收益 = 每年末 adj_close/上年末-1（收益率=百分数×100）；maxDD 用年内日线；波动率=年化日波动
"""
import json, os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(BASE, "..", "results", "xbi_mini_stats.json")

def load(tk):
    path = os.path.join(DATA, tk, "%s, 1D.csv" % tk.upper())
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "adj_close"]].dropna().sort_values("date").reset_index(drop=True)
    return df

def yearly_stats(df):
    """输入含 date/adj_close，输出 2022-2026 年度 {ret, maxdd, vol}"""
    df = df.copy()
    df["year"] = df["date"].dt.year
    out = {}
    for y in range(2022, 2027):
        sub = df[df["year"] == y]
        prev = df[df["date"] < sub["date"].min()]
        if sub.empty or prev.empty:
            continue
        ret = (sub["adj_close"].iloc[-1] / prev["adj_close"].iloc[-1] - 1) * 100
        roll_max = sub["adj_close"].cummax()
        dd = (sub["adj_close"] / roll_max - 1) * 100
        maxdd = dd.min()
        vol = sub["adj_close"].pct_change().std() * np.sqrt(252) * 100
        out[y] = dict(ret=round(ret, 1), maxdd=round(maxdd, 1), vol=round(vol, 1))
    return out

def load_dgs10():
    path = os.path.join(DATA, "dgs10.csv")
    df = pd.read_csv(path)
    df.columns = ["date", "dgs10"]
    df["date"] = pd.to_datetime(df["date"])
    df["dgs10"] = pd.to_numeric(df["dgs10"], errors="coerce")
    df = df.dropna().sort_values("date")
    return df

def main():
    res = {}
    for tk in ["xbi", "ibb", "xph"]:
        df = load(tk)
        res[tk] = yearly_stats(df)
    # 利率环境
    dgs = load_dgs10()
    dgs["year"] = dgs["date"].dt.year
    res["dgs10"] = {}
    for y in range(2022, 2027):
        sub = dgs[dgs["year"] == y]
        if sub.empty:
            continue
        res["dgs10"][y] = dict(
            mean=round(sub["dgs10"].mean(), 2),
            year_end=round(sub["dgs10"].iloc[-1], 2),
            min=round(sub["dgs10"].min(), 2),
            max=round(sub["dgs10"].max(), 2),
        )
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    # 汇总KPI
    for tk in ["xbi", "ibb", "xph"]:
        s = " ".join("%s:%.0f%%" % (y, res[tk][y]["ret"]) for y in res[tk])
        print("[%s ret] %s" % (tk.upper(), s))
    print("[dgs10] mean: " + " ".join("%s=%.1f" % (y, res["dgs10"][y]["mean"]) for y in res["dgs10"]))
    print("written: %s" % OUT)

if __name__ == "__main__":
    main()