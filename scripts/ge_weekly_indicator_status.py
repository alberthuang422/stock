# -*- coding: utf-8 -*-
"""GE 周线 MACD(12,26,9) + EMA10/20 现状计算
口径: adj_close 复权; EMA=ewm(span, adjust=False); DIF=EMA12-EMA26; DEA=DIF的EMA9; 柱=2*(DIF-DEA)
双口径: ①最后完整周(bar 2026-08-17, 即 8/17-8/21)  ②含本周实时(bar 2026-08-24, 截至8/25收盘, 本周未收盘)
"""
import pandas as pd
import numpy as np

CSV = r"C:\Users\Administrator\Desktop\stock\data\ge\GE, 1W.csv"
df = pd.read_csv(CSV)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

c = df["adj_close"]
ema12 = c.ewm(span=12, adjust=False).mean()
ema26 = c.ewm(span=26, adjust=False).mean()
dif = ema12 - ema26
dea = dif.ewm(span=9, adjust=False).mean()
hist = (dif - dea) * 2
ema10 = c.ewm(span=10, adjust=False).mean()
ema20 = c.ewm(span=20, adjust=False).mean()

out = df.copy()
out["ema10"] = ema10
out["ema20"] = ema20
out["dif"] = dif
out["dea"] = dea
out["hist"] = hist
out["state"] = np.where(dif > dea, "金叉区(DIF>DEA)", "死叉区(DIF<DEA)")
out["zero"] = np.where(dif > 0, "0轴上", "0轴下")
out["ema"] = np.where(ema10 > ema20, "EMA10>EMA20", "EMA10<EMA20")

print("=" * 100)
print("GE 周线 MACD + EMA 最近 16 周明细 (adj_close 口径)")
print("=" * 100)
cols = ["date", "close", "ema10", "ema20", "dif", "dea", "hist", "state", "zero", "ema"]
print(out[cols].tail(16).to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

# 关键时点
last_full = out[out["date"] <= "2026-08-21"].iloc[-1]   # 最后完整周 bar(2026-08-17 标注)
live = out.iloc[-1]                                     # 含本周实时

def fmt(r):
    return (f"日期: {r['date'].date()} | 收盘: {r['close']:.2f} | "
            f"EMA10: {r['ema10']:.2f} | EMA20: {r['ema20']:.2f} | "
            f"DIF: {r['dif']:.3f} | DEA: {r['dea']:.3f} | 柱: {r['hist']:.3f} | "
            f"{r['state']} | {r['zero']} | {r['ema']}")

print("\n" + "=" * 100)
print("【口径1】最后完整周 (2026-08-17 周, 8/16-8/21 已收盘):")
print(fmt(last_full))
print("\n【口径2】含本周实时 (bar 2026-08-24 = 本周一/二, 截至 8/25 收盘, 本周未收盘):")
print(fmt(live))
print("=" * 100)

# 金叉/死叉历史事件(近步)
prev = out.iloc[:-5].copy()
cross_events = []
for i in range(1, len(out)):
    d0, d1 = out["dif"].iloc[i-1], out["dif"].iloc[i]
    e0, e1 = out["dea"].iloc[i-1], out["dea"].iloc[i]
    if d0 <= e0 and d1 > e1:
        cross_events.append((out["date"].iloc[i], "金叉", out["close"].iloc[i], out["dif"].iloc[i], out["dea"].iloc[i]))
    elif d0 >= e0 and d1 < e1:
        cross_events.append((out["date"].iloc[i], "死叉", out["close"].iloc[i], out["dif"].iloc[i], out["dea"].iloc[i]))
print("\n最近 8 次 DIF/DEA 交叉事件:")
for ev in cross_events[-8:]:
    print(f"  {ev[0].date()}  {ev[1]}  收盘 {ev[2]:.2f}  DIF {ev[3]:.3f}  DEA {ev[4]:.3f}")

# 0 轴穿越事件(近步)
zero_events = []
for i in range(1, len(out)):
    d0, d1 = out["dif"].iloc[i-1], out["dif"].iloc[i]
    if d0 <= 0 and d1 > 0:
        zero_events.append((out["date"].iloc[i], "上穿0轴", out["close"].iloc[i], out["dif"].iloc[i]))
    elif d0 >= 0 and d1 < 0:
        zero_events.append((out["date"].iloc[i], "下穿0轴", out["close"].iloc[i], out["dif"].iloc[i]))
print("\n最近 5 次 DIF 穿越 0 轴事件:")
for ev in zero_events[-5:]:
    print(f"  {ev[0].date()}  {ev[1]}  收盘 {ev[2]:.2f}  DIF {ev[3]:.3f}")

# EMA10/20 交叉事件
ema_events = []
for i in range(1, len(out)):
    a0, a1 = out["ema10"].iloc[i-1], out["ema10"].iloc[i]
    b0, b1 = out["ema20"].iloc[i-1], out["ema20"].iloc[i]
    if a0 <= b0 and a1 > b1:
        ema_events.append((out["date"].iloc[i], "EMA10金叉EMA20", out["close"].iloc[i]))
    elif a0 >= b0 and a1 < b1:
        ema_events.append((out["date"].iloc[i], "EMA10死叉EMA20", out["close"].iloc[i]))
print("\n最近 5 次 EMA10/20 交叉事件:")
for ev in ema_events[-5:]:
    print(f"  {ev[0].date()}  {ev[1]}  收盘 {ev[2]:.2f}")

# 近期涨跌幅参考
print("\n近期收盘路径: ")
for i in range(len(out) - 6, len(out)):
    row = out.iloc[i]
    chg = (row["close"] / out["close"].iloc[i-1] - 1) * 100 if i > 0 else np.nan
    print(f"  {row['date'].date()}  {row['close']:.2f}  周涨跌 {chg:+.2f}%")