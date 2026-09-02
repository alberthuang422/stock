# -*- coding: utf-8 -*-
"""
分析：VIX 较高（>18）时 CVS 的表现如何
口径（2026-09-02 更换数据源）：CVS 用 BATS 前复权 close（TradingView 导出，含分红回溯，
锚点 2022-02-08 high=95.30 与富途 autype=1 前复权一致）；VIX 用 CBOE 官方收盘；
      SPY 作大盘对照（未复权 close，价格收益近似）。窗口 2015-01-01 ~ 最新。
日期对齐采用三表 inner join。收益均为价格收益百分比。
"""
import json
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
RESULTS = os.path.join(BASE, "results")

def load(tk):
    return pd.read_csv(os.path.join(DATA, f"{tk.lower()}/{tk.upper()}, 1D.csv"),
                       parse_dates=["date"]).sort_values("date").reset_index(drop=True)

cvs = load("CVS")[["date", "close"]].rename(columns={"close": "cvs"})
vix = load("VIX")[["date", "close"]].rename(columns={"close": "vix"})
spy = load("SPY")[["date", "close"]].rename(columns={"close": "spy"})

df = cvs.merge(vix, on="date").merge(spy, on="date")
df = df[df.date >= "2015-01-01"].reset_index(drop=True)

for col in ["cvs", "spy"]:
    df[f"{col}_ret"] = df[col].pct_change() * 100          # 当日收益 %
for n in (1, 5, 20, 60):
    df[f"cvs_fwd{n}"] = df["cvs"].shift(-n) / df["cvs"] * 100 - 100
    df[f"spy_fwd{n}"] = df["spy"].shift(-n) / df["spy"] * 100 - 100
df["cvs_exc"] = df["cvs_ret"] - df["spy_ret"]              # 当日超额
for n in (1, 5, 20, 60):
    df[f"cvs_fwd{n}_exc"] = df[f"cvs_fwd{n}"] - df[f"spy_fwd{n}"]

hi = df.vix > 18
out = {"window": f"{df.date.iloc[0].date()} ~ {df.date.iloc[-1].date()}", "n_days": int(len(df)),
       "hi_days": int(hi.sum()), "lo_days": int((~hi).sum())}

def stats(s):
    return dict(n=int(s.notna().sum()), med=round(float(np.nanmedian(s)), 2),
                mean=round(float(np.nanmean(s)), 2), win=round(float((s > 0).mean() * 100), 1))

# 表1 高/低 VIX 当日表现（恐慌日 CVS 是否抗跌）
t1 = {}
for name, m in (("VIX>18", hi), ("VIX<=18", ~hi)):
    sub = df[m]
    t1[name] = {
        "cvs_d0_med": round(float(np.nanmedian(sub.cvs_ret)), 2),
        "spy_d0_med": round(float(np.nanmedian(sub.spy_ret)), 2),
        "cvs_exc_d0_med": round(float(np.nanmedian(sub.cvs_exc)), 2),
        "cvs_d0_win": round(float((sub.cvs_ret > 0).mean() * 100), 1),
        "cvs_exc_win": round(float((sub.cvs_exc > 0).mean() * 100), 1),
    }
out["tab_d0"] = t1

# 表2 高VIX 状态下买入 CVS 未来收益 vs 低VIX 对照
t2 = {}
for mname, m in (("VIX>18", hi), ("VIX<=18", ~hi)):
    sub = df[m]
    t2[mname] = {f"fwd{n}": stats(sub[f"cvs_fwd{n}"]) for n in (1, 5, 20, 60)}
    t2[mname + "_exc"] = {f"fwd{n}": stats(sub[f"cvs_fwd{n}_exc"]) for n in (1, 5, 20, 60)}
out["tab_fwd_abs_exc"] = t2

# 表3 VIX 分层桶 → fwd20
bins = [0, 15, 18, 25, 35, 100]
labs = ["<=15", "15-18", "18-25", "25-35", ">35"]
df["vb"] = pd.cut(df.vix, bins=bins, labels=labs)
t3 = []
for lb, g in df.groupby("vb", observed=True):
    t3.append({"bucket": lb, "n": int(len(g)), "fwd20": stats(g.cvs_fwd20),
               "fwd20_exc": stats(g.cvs_fwd20_exc)})
out["tab_buckets"] = t3

# 表4 VIX 单日飙升事件（日涨>=15% 且收>18）：恐慌冲击日 CVS 表现
vix_prev = df.vix.shift(1)
shock = (df.vix / vix_prev - 1 >= 0.15) & (df.vix > 18)
ev = df[shock].copy()
t4 = []
for _, r in ev.iterrows():
    t4.append({"date": r.date.strftime("%Y-%m-%d"), "vix": round(float(r.vix), 1),
               "vix_chg_pct": round(float((r.vix / vix_prev.loc[r.name] - 1) * 100), 0),
               "cvs_d0": round(float(r.cvs_ret), 2), "spy_d0": round(float(r.spy_ret), 2),
               "cvs_exc_d0": round(float(r.cvs_exc), 2),
               "cvs_fwd5_exc": round(float(r.cvs_fwd5_exc), 2)})
t4s = {"n": len(t4),
       "cvs_d0_med": round(float(np.nanmedian([e["cvs_d0"] for e in t4])), 2),
       "exc_d0_med": round(float(np.nanmedian([e["cvs_exc_d0"] for e in t4])), 2),
       "exc_d0_win": round(float(np.mean([e["cvs_exc_d0"] > 0 for e in t4]) * 100), 1),
       "fwd5_exc_med": round(float(np.nanmedian([e["cvs_fwd5_exc"] for e in t4])), 2),
       "fwd5_exc_win": round(float(np.mean([e["cvs_fwd5_exc"] > 0 for e in t4]) * 100), 1)}
out["tab_shocks"] = {"events": t4, "summary": t4s}

# 表5 主要高VIX持续段（>=10 连续交易日 VIX>18）：CVS vs SPY
hi_arr = hi.values
segs = []
i = 0
while i < len(df):
    if hi_arr[i]:
        j = i
        while j + 1 < len(df) and hi_arr[j + 1]:
            j += 1
        if j - i + 1 >= 10:
            segs.append((i, j))
        i = j + 1
    else:
        i += 1
t5 = []
for i, j in segs:
    s, e = df.iloc[i], df.iloc[j]
    cvs_ret = (e.cvs / s.cvs - 1) * 100
    spy_ret = (e.spy / s.spy - 1) * 100
    t5.append({"start": s.date.strftime("%Y-%m-%d"), "end": e.date.strftime("%Y-%m-%d"),
               "days": int(j - i + 1), "vix_hi": round(float(s.vix), 1),
               "vix_end": round(float(e.vix), 1),
               "cvs": round(float(cvs_ret), 1), "spy": round(float(spy_ret), 1),
               "cvs_exc_pp": round(float(cvs_ret - spy_ret), 1)})
out["tab_segments"] = t5

os.makedirs(RESULTS, exist_ok=True)
p = os.path.join(RESULTS, "cvs_vix_analysis.json")
with open(p, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
