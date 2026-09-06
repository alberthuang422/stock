# -*- coding: utf-8 -*-
"""KMI 技术面分析：均线/RSI/MACD/布林/支撑阻力/年度表现
输入：data/KMI/KMI, 1D.csv（新浪未复权）
输出：results/kmi_tech.json
"""
import pandas as pd
import numpy as np
import json
import os

ROOT = "C:/Users/Administrator/Desktop/stock"
df = pd.read_csv(os.path.join(ROOT, "data/KMI/KMI, 1D.csv"), parse_dates=["date"]).set_index("date").sort_index()
df = df[~df.index.duplicated(keep='last')]
c = df["close"]

def last_price(s):
    return float(s.iloc[-1])

def sma(s, n):
    return float(s.rolling(n).mean().iloc[-1])

def ema(s, n):
    return float(s.ewm(span=n, adjust=False).mean().iloc[-1])

# RSI(14) Wilder
delta = c.diff()
gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
rsi14 = float((100 - 100/(1 + gain/loss)).iloc[-1])

# MACD(12,26,9)
ema12 = c.ewm(span=12, adjust=False).mean()
ema26 = c.ewm(span=26, adjust=False).mean()
dif = ema12 - ema26
dea = dif.ewm(span=9, adjust=False).mean()
macd_hist = (dif - dea) * 2
macd = {"DIF": float(dif.iloc[-1]), "DEA": float(dea.iloc[-1]), "HIST": float(macd_hist.iloc[-1])}
# 20日前
macd20 = {"DIF": float(dif.iloc[-21]), "DEA": float(dea.iloc[-21]), "HIST": float(macd_hist.iloc[-21])}

# 布林(20,2)
m20 = c.rolling(20).mean()
sd20 = c.rolling(20).std()
boll = {"mid": float(m20.iloc[-1]), "upper": float((m20+2*sd20).iloc[-1]), "lower": float((m20-2*sd20).iloc[-1])}

# 52周高低
w52 = c.tail(252)
ret_52w = last_price(c)/float(w52.iloc[0]) - 1
# YTD
ytd_start = c[c.index >= "2026-01-01"].iloc[0]
ret_ytd = last_price(c)/float(ytd_start) - 1
# 自 2025 年底
ret_2025 = float(c[c.index <= "2025-12-31"].iloc[-1])
ret_2025_full = last_price(c)/ret_2025 - 1

# 支撑/阻力（近1年 5日极值聚类，tol 1.5%）
W = w52
levels = []
for w_ in [20, 60, 120]:
    seg = c.tail(w_)
    hi = float(seg.max()); lo = float(seg.min())
    levels.append({"window": w_, "high": round(hi, 2), "low": round(lo, 2)})

# 近60日 回归趋势
seg = c.tail(60)
x = np.arange(60)
slope = np.polyfit(x, seg.values, 1)[0]
trend60 = {"slope_per_day": round(float(slope), 4), "annualized_pct": round(float(slope)/float(seg.iloc[-1])*252*100, 1)}

# 成交量
vol = df["volume"]
vol20 = float(vol.tail(20).mean())
vol5 = float(vol.tail(5).mean())

# 关键价位附近的距离
px = last_price(c)
res = {
    "close": round(px, 2),
    "date": str(c.index[-1].date()),
    "sma20": round(sma(c, 20), 2),
    "sma50": round(sma(c, 50), 2),
    "sma100": round(sma(c, 100), 2),
    "sma200": round(sma(c, 200), 2),
    "ema20": round(ema(c, 20), 2),
    "rsi14": round(rsi14, 1),
    "macd": macd, "macd20": macd20,
    "boll": {k: round(v, 2) for k, v in boll.items()},
    "high52w": round(float(w52.max()), 2),
    "low52w": round(float(w52.min()), 2),
    "ret_ytd": round(ret_ytd*100, 1),
    "ret_1y": round(ret_52w*100, 1),
    "ret_2025_full": round(ret_2025_full*100, 1),
    "levels": levels,
    "trend60": trend60,
    "vol20": int(vol20), "vol5": int(vol5),
    "px_vs_sma20": round((px/sma(c,20)-1)*100, 1),
    "px_vs_sma200": round((px/sma(c,200)-1)*100, 1),
    "px_vs_52w_high": round((px/float(w52.max())-1)*100, 1),
    "px_vs_52w_low": round((px/float(w52.min())-1)*100, 1),
}

# 月度收盘序列（近24月，用于图表）
mon = c.resample("ME").last().tail(30)
monthly = [{"date": str(d.date()), "close": round(float(v), 2)} for d, v in mon.items()]

# 近一年每周
wk = c.resample("W-FRI").last().tail(60)
weekly = [{"date": str(d.date()), "close": round(float(v), 2)} for d, v in wk.items()]

out = {"res": res, "monthly": monthly, "weekly": weekly}
json.dump(out, open(os.path.join(ROOT, "results/kmi_tech.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))