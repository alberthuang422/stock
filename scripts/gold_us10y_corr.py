#!/usr/bin/env python3
"""XAUUSD(黄金) × US10Y(DGS10 名义收益率) 滚动相关性分析 —— 重点: 最近两个月。

数据:
  - XAUUSD: data/xauusd/XAUUSD, 1D.csv (Yahoo, 收盘)
  - US10Y : data/us_treasury/DGS10.csv (FRED 名义 10Y 收益率)  + Temp/dgs10_latest.csv 补齐最新

口径:
  - 日收益率: XAU 为收盘价 pct_change×100; US10Y 为收益率日变动(基点变化 bp；同收益率单位, 用 diff×100)
  - 主口径 60 日滚动相关(项目惯例), 30 日滚动辅助
  - 输出: 全期 + 近 60/40/20 交易日静态相关
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")


def load_gold():
    p = os.path.join(DATA, "xauusd", "XAUUSD, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    df = df[["date", "close"]].rename(columns={"close": "gold"})
    df["gold_ret"] = df["gold"].pct_change() * 100
    return df


def load_us10y():
    # 本地 + FRED 最新 (若存在且更新则合并)
    p = os.path.join(DATA, "us_treasury", "DGS10.csv")
    df = pd.read_csv(p, parse_dates=["observation_date"])
    df = df[["observation_date", "DGS10"]].rename(columns={"observation_date": "date", "DGS10": "us10y"})
    # 补最新
    latest = os.path.join(ROOT, "Temp", "dgs10_latest.csv")
    if os.path.exists(latest):
        df2 = pd.read_csv(latest, parse_dates=["observation_date"])
        df2 = df2[["observation_date", "DGS10"]].rename(columns={"observation_date": "date", "DGS10": "us10y"})
        df2 = df2[~df2["date"].isin(df["date"])]
        df = pd.concat([df, df2], ignore_index=True)
    df = df.dropna().sort_values("date").reset_index(drop=True)
    df["us10y_bp"] = df["us10y"] * 100  # 收益率百分数 -> bp
    df["us10y_chg"] = df["us10y_bp"].diff()  # 日变动 bp
    return df


def pearson(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, len(a)
    return float(np.corrcoef(a, b)[0, 1]), len(a)


def main():
    gold = load_gold()
    us10y = load_us10y()
    print(f"gold {gold['date'].iloc[0].date()}~{gold['date'].iloc[-1].date()} n={len(gold)}")
    print(f"us10y {us10y['date'].iloc[0].date()}~{us10y['date'].iloc[-1].date()} n={len(us10y)}")

    m = pd.merge(gold, us10y, on="date", how="inner").dropna()
    m = m[m["date"] >= "2022-01-01"].reset_index(drop=True)
    print(f"合并交集 2022起: n={len(m)}  {m['date'].iloc[0].date()} ~ {m['date'].iloc[-1].date()}")

    # 全期相关
    r_all, n_all = pearson(m["gold_ret"].values, m["us10y_chg"].values)

    # 滚动 60/30
    def rolling(df, win):
        out = []
        for i in range(win - 1, len(df)):
            w = df.iloc[i - win + 1: i + 1]
            r, _ = pearson(w["gold_ret"].values, w["us10y_chg"].values)
            out.append({"date": str(df["date"].iloc[i].date()), "r": r})
        return out

    roll60 = rolling(m, 60)
    roll30 = rolling(m, 30)

    # 最近两个月窗口 (截至 2026-08-31 前推 60 交易日 ≈ 三个月; 取最近 60/40/20 交易日静态)
    recent = {}
    for win in (60, 40, 20):
        w = m.tail(win)
        r, _ = pearson(w["gold_ret"].values, w["us10y_chg"].values)
        recent[str(win)] = {
            "start": str(w["date"].iloc[0].date()), "end": str(w["date"].iloc[-1].date()),
            "n": len(w), "r": round(r, 4) if r is not None else None,
            "gold": round(float((w["gold"].iloc[-1] / w["gold"].iloc[0] - 1) * 100), 2),
            "us10y_bp_chg": round(float(w["us10y_bp"].iloc[-1] - w["us10y_bp"].iloc[0]), 2),
        }

    # 近两个月滚动序列的统计 (60日滚动最近 40 个点)
    tail60 = pd.DataFrame(roll60).tail(40)
    roll60_desc = {
        "start": str(tail60["date"].iloc[0]), "end": str(tail60["date"].iloc[-1]),
        "min": round(float(tail60["r"].min()), 4), "max": round(float(tail60["r"].max()), 4),
        "mean": round(float(tail60["r"].mean()), 4), "latest": round(float(tail60["r"].iloc[-1]), 4),
    }

    out = {
        "meta": {
            "x": "XAUUSD 黄金现货 (Yahoo 收盘)",
            "y": "US10Y 美债10年期名义收益率 DGS10 (FRED, 日变动 bp)",
            "x_ret": "gold_ret = close.pct_change×100(%)",
            "y_chg": "us10y_chg = 收益率×100 差分 (bp 变动)",
            "windows": {"full": "2022-01 至今", "main": "60日滚动(主口径)", "aux": "30日滚动", "static": "最近60/40/20交易日"},
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        },
        "full": {"start": str(m["date"].iloc[0].date()), "end": str(m["date"].iloc[-1].date()),
                 "n": n_all, "r": round(r_all, 4) if r_all is not None else None},
        "recent": recent,
        "roll60_latest40": roll60_desc,
        "roll60": roll60,
        "roll30": roll30,
    }
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "gold_us10y_corr.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", p)

    print(f"\n== 全期(2022起) r = {r_all:.4f}")
    for k, v in recent.items():
        print(f"近{k}交易日: {v['start']}~{v['end']} n={v['n']} r={v['r']} 金 {v['gold']:+.2f}% 10Y {v['us10y_bp_chg']:+.1f}bp")
    print(f"60日滚动 近40点: {roll60_desc}")
    print("\n最近 12 个滚动值 (60日):")
    for row in roll60[-12:]:
        print(f"  {row['date']}  r={row['r']}")


if __name__ == "__main__":
    main()