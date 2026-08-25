# -*- coding: utf-8 -*-
"""生成蓝筹股周线数据：data/<sym>/<sym>, W.csv

口径（与报告31完全一致）：
- 从日线 adj_close 统一折算 OHLC（ratio = adj_close/close 乘到 open/high/low，close=adj_close）
- 周线聚合：每周最后一个交易日（含当周 in-progress bar）为周bar；
  对应 weekly_last = groupby(period).last() 的递推口径
- 列：date(周最后交易日), open, high, low, close, volume(周求和)
- 原始周线不加任何EMA（EMA 只在回测脚本里按无前视方式算，避免落盘带EMA误导）
"""
import os

import numpy as np
import pandas as pd

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"))

UNIVERSE = [
    "ko", "brk.b", "jnj", "mcd", "pg", "pep", "cnp", "lnt", "xel", "mo",
    "trv", "wmt", "vz", "etr", "hon", "sre", "v", "pm", "abbv", "ma",
    "amgn", "jpm", "hd", "gild", "mrk", "cvx", "csco", "xom", "nee", "shw",
    "blk", "tmo", "aapl", "msft", "gs", "mmm", "ms", "vrtx", "dhr", "axp",
    "dis", "ibm", "trow", "ge", "regn", "sbux", "cat",
]


def load_daily(symbol):
    path = os.path.join(DATA_DIR, symbol, f"{symbol}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    if "adj_close" not in df.columns or df["adj_close"].isna().all():
        df["adj_close"] = df["close"]
    ratio = df["adj_close"] / df["close"]
    for col in ("open", "high", "low"):
        df[col] = df[col] * ratio
    df["close"] = df["adj_close"]
    return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def to_weekly(df):
    period = df["date"].dt.to_period("W-FRI")
    wk = df.groupby(period, sort=True).agg(
        date=("date", "last"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).reset_index(drop=True)
    return wk


def main():
    n_ok = 0
    for sym in UNIVERSE:
        try:
            daily = load_daily(sym)
            wk = to_weekly(daily)
        except Exception as e:
            print(f"  {sym:>9s}: FAIL {e}")
            continue
        out_dir = os.path.join(DATA_DIR, sym)
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, f"{sym}, W.csv")
        wk.to_csv(out, index=False, encoding="utf-8")
        n_ok += 1
        print(f"  {sym:>9s}: {len(wk):5d} weeks  {str(wk['date'].iloc[0])[:10]} ~ {str(wk['date'].iloc[-1])[:10]}")
    print(f"\nwritten: {n_ok}/{len(UNIVERSE)} weekly files to {DATA_DIR}")


if __name__ == "__main__":
    main()