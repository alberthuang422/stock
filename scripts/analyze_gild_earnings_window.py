#!/usr/bin/env python3
"""GILD 财报(2026-08-04)前后窗口对比: GILD vs IBB/XBI/XLV
计算: 财报前涨幅起点定位、财报前/财报日/财报后各窗口表现、板块同期表现、GILD 回撤。
数据: data/<t>/*.csv (Yahoo 日线, 用 adj_close 复权价)
"""
import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(t):
    p = os.path.join(ROOT, "data", t, f"{t}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df[["date", "open", "high", "low", "close", "adj_close"]].copy()
    df = df.sort_values("date").reset_index(drop=True)
    return df

def pct(a, b):
    return (b / a - 1) * 100

tickers = ["GILD", "IBB", "XBI", "XLV"]
data = {t: load(t) for t in tickers}

# 1) 定位 GILD "涨很凶"起点: 打印 2026-05-01 以来每隔一周的收盘, 以及阶段涨跌
g = data["GILD"]
m = g[g["date"] >= "2026-05-01"].copy()
print("=== GILD 2026-05-01 以来关键节点 ===")
# 找出局部低点与后续高点
for d in ["2026-05-01","2026-05-15","2026-06-01","2026-06-15","2026-07-01","2026-07-10","2026-07-17","2026-07-24","2026-07-31","2026-08-03","2026-08-04","2026-08-05","2026-08-07","2026-08-10","2026-08-12","2026-08-14"]:
    row = g[g["date"] == d]
    if len(row):
        r = row.iloc[0]
        print(f"{d}: close={r['close']:.2f}  adj={r['adj_close']:.2f}  hi={r['high']:.2f}  lo={r['low']:.2f}")

# 2) 全窗口收益表
print("\n=== 窗口收益 (adj_close, %) ===")
# 找到 GILD 财报前的最低点(从6月起)以确定"涨很凶"起点
g6 = g[(g["date"] >= "2026-06-01") & (g["date"] <= "2026-08-03")]
lo_row = g6.loc[g6["adj_close"].idxmin()]
hi_row = g6.loc[g6["adj_close"].idxmax()]
print(f"GILD 6/1-8/3 区间: 最低 {lo_row['date'].date()} adj={lo_row['adj_close']:.2f}, 最高 {hi_row['date'].date()} adj={hi_row['adj_close']:.2f}")

windows = [
    ("财报前1个月", "2026-07-01", "2026-08-03"),
    ("财报前6周", "2026-06-22", "2026-08-03"),
    ("财报前(6/1起)", "2026-06-01", "2026-08-03"),
    ("财报前(5/15起)", "2026-05-15", "2026-08-03"),
]
for name, s, e in windows:
    print(f"\n--- {name} ({s} ~ {e}) ---")
    for t in tickers:
        d = data[t]
        sub = d[(d["date"] >= s) & (d["date"] <= e)]
        if len(sub) < 5:
            print(f"{t}: 数据不足"); continue
        ret = pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"])
        lo_ = sub.loc[sub["adj_close"].idxmin()]; hi_ = sub.loc[sub["adj_close"].idxmax()]
        print(f"{t}: 涨跌 {ret:+.2f}% | 区间最低 {lo_['date'].date()} 最高 {hi_['date'].date()}")

# 3) 财报日与财报后
print("\n--- 财报日(8/4)当日 ---")
for t in tickers:
    d = data[t]
    prev = d[d["date"] < "2026-08-04"].iloc[-1]
    day = d[d["date"] == "2026-08-04"]
    if len(day):
        r = day.iloc[0]
        print(f"{t}: 前收 {prev['close']:.2f} -> 8/4收 {r['close']:.2f} ({pct(prev['close'], r['close']):+.2f}%), 盘中高 {r['high']:.2f}")

print("\n--- 财报后 (8/4收 ~ 8/14) ---")
for t in tickers:
    d = data[t]
    sub = d[(d["date"] >= "2026-08-04") & (d["date"] <= "2026-08-14")]
    ret = pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"])
    print(f"{t}: {ret:+.2f}%")

print("\n--- 财报后回撤(自8/4以来盘中高点) ---")
for t in tickers:
    d = data[t]
    sub = d[(d["date"] >= "2026-08-04") & (d["date"] <= "2026-08-14")]
    h = sub["high"].max(); hd = sub.loc[sub["high"].idxmax(), "date"]
    last = sub.iloc[-1]["close"]
    print(f"{t}: 高点 {h:.2f} ({hd.date()}) -> 8/14收 {last:.2f}, 距高点 {pct(h,last):+.2f}%")

# 4) 财报前后 4 日窗口的日收益 (看回落节奏)
print("\n=== 8/4 之后逐日涨跌 (close) ===")
for t in tickers:
    d = data[t]
    sub = d[(d["date"] >= "2026-08-04") & (d["date"] <= "2026-08-14")]
    r = sub["close"].pct_change() * 100
    line = f"{t}: " + " | ".join(f"{sub['date'].iloc[i].strftime('%m-%d')} {r.iloc[i]:+.2f}%" for i in range(1, len(sub)))
    print(line)

# 5) 财报前的板块联动: GILD 与三只 ETF 在"涨很凶"窗口内的日收益相关
print("\n=== 财报前窗口(7/1-8/3)日收益相关 (GILD vs ETF) ===")
w0 = data["GILD"].set_index("date")["adj_close"].pct_change()
for t in ["IBB", "XBI", "XLV"]:
    w = data[t].set_index("date")["adj_close"].pct_change()
    j = pd.concat([w0.rename("GILD"), w.rename(t)], axis=1).dropna()
    j = j[(j.index >= "2026-07-01") & (j.index <= "2026-08-03")]
    c = j["GILD"].corr(j[t])
    print(f"GILD~{t}: pearson={c:.3f} (n={len(j)})")
