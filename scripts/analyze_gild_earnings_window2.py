#!/usr/bin/env python3
"""补充: GILD 6/10(低点)->7/7(高点) 及财报前后细分窗口的板块对照"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(t):
    df = pd.read_csv(os.path.join(ROOT, "data", t, f"{t}, 1D.csv"), parse_dates=["date"])
    return df[["date", "close", "adj_close", "high", "low"]].sort_values("date").reset_index(drop=True)

def pct(a, b):
    return (b / a - 1) * 100

tickers = ["GILD", "IBB", "XBI", "XLV"]
data = {t: load(t) for t in tickers}

windows = [
    ("GILD涨很凶段 6/10->7/7", "2026-06-10", "2026-07-07"),
    ("板块同步段 6/2->7/7 (板块低点->高点)", "2026-06-02", "2026-07-07"),
    ("GILD回落段 7/7->8/3", "2026-07-07", "2026-08-03"),
    ("财报日当周 7/31->8/7", "2026-07-31", "2026-08-07"),
    ("财报后两日 8/4->8/6", "2026-08-04", "2026-08-06"),
    ("财报后修复 8/6->8/14", "2026-08-06", "2026-08-14"),
    ("近一周 8/7->8/14", "2026-08-07", "2026-08-14"),
]
for name, s, e in windows:
    print(f"\n--- {name} ({s} ~ {e}) ---")
    for t in tickers:
        d = data[t]
        sub = d[(d["date"] >= s) & (d["date"] <= e)]
        if len(sub) < 2:
            print(f"{t}: 数据不足"); continue
        ret = pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"])
        print(f"{t}: {ret:+.2f}%")

# 7/7 之后 GILD 是否创新高? 8/14 收盘 vs 7/7 高点
g = data["GILD"]
print("\nGILD: 7/7 高点 close =", round(g[g['date']=='2026-07-07'].iloc[0]['close'],2),
      "| 8/14 close =", round(g[g['date']=='2026-08-14'].iloc[0]['close'],2),
      "| 8/14 vs 7/7 高点:", f"{pct(g[g['date']=='2026-07-07'].iloc[0]['close'], g[g['date']=='2026-08-14'].iloc[0]['close']):+.2f}%")
g2 = g[(g['date']>='2026-08-04')]
print("8/4 以来 GILD 最高 close:", round(g2['close'].max(),2), "日期:", g2.loc[g2['close'].idxmax(),'date'].date())
