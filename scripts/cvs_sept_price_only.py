# -*- coding: utf-8 -*-
"""CVS 9 月季节性 · 口径对照重跑
用户提供 TradingView BATS 月线（data/cvs/BATS_CVS, 1M.csv，1968 起）
实证其收益与 Yahoo adj_close 一致率 93.8% → 同属"含股息前复权/总回报"口径。
本脚本同时用 Yahoo close（拆股调整、股息未调 = 纯价格口径）重跑，做三口径对照。
输出 results/cvs_sept_seasonality_price.json
"""
import json
import os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "cvs_sept_seasonality_price.json")


def tv_monthly():
    df = pd.read_csv(os.path.join(DATA, "cvs", "BATS_CVS, 1M.csv"))
    df["date"] = pd.to_datetime(df["time"])
    px = df.set_index("date")["close"].dropna().astype(float)
    ret = px.pct_change().dropna() * 100
    ret = ret[ret.index < pd.Timestamp("2026-09-01")]  # 2026-09 不完整（仅 9/1 一根）
    return ret  # index = 每月 1 号


def yahoo_close_monthly():
    df = pd.read_csv(os.path.join(DATA, "cvs", "CVS, 1D.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").dropna(subset=["close"]).set_index("date")
    px = df["close"]
    r = px.pct_change().dropna()
    m = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    m = m * 100
    last_key = m.index[-1]
    keep = [(y, mo) for (y, mo) in m.index
            if (y, mo) != last_key]  # 剔除最后数据月（2026-09 不完整）
    m = m.loc[keep]
    idx = pd.PeriodIndex([f"{y}-{mo:02d}" for y, mo in m.index], freq="M")
    m.index = idx
    return m


def stats_sep(series, name):
    """series: index 为 Period('M')，值=月收益%"""
    sep = series[series.index.month == 9]
    other = series[series.index.month != 9]
    v = sep.values
    t0, p0 = stats.ttest_1samp(v, 0.0)
    return {
        "name": name, "n": int(len(v)),
        "start": str(sep.index.min()), "end": str(sep.index.max()),
        "mean": round(float(v.mean()), 2),
        "med": round(float(np.median(v)), 2),
        "win": round(float((v > 0).mean()) * 100, 1),
        "best": round(float(v.max()), 2), "worst": round(float(v.min()), 2),
        "best_ym": str(sep.index[int(np.argmax(v))]),
        "worst_ym": str(sep.index[int(np.argmin(v))]),
        "t": round(float(t0), 2), "p": round(float(p0), 5),
        "other_mean": round(float(other.values.mean()), 2),
    }


tv = tv_monthly()                      # 1968 起（含息前复权，同 adj 口径）
tv.index = tv.index.to_period("M")
pxc = yahoo_close_monthly()            # 1993-02 起（纯价格：拆股调、股息不调）

tv_full = stats_sep(tv, "TradingView 月线（1968 起，含息口径）")
tv_93 = stats_sep(tv[tv.index.year >= 1993], "TradingView（1993 起）")
px_93 = stats_sep(pxc[pxc.index.year >= 1993], "Yahoo close 纯价格（1993 起）")

# 近 10 年三列对照（2017-2025 完整 9 月）
years = list(range(2017, 2026))
recent = []
for y in years:
    sep_tv = tv[(tv.index.year == y) & (tv.index.month == 9)]
    sep_px = pxc[(pxc.index.year == y) & (pxc.index.month == 9)]
    row = {"year": y,
           "tv": round(float(sep_tv.iloc[0]), 2) if len(sep_tv) else None,
           "price": round(float(sep_px.iloc[0]), 2) if len(sep_px) else None}
    recent.append(row)

# 9 月差 = 纯价格 vs 含息（理论上 9 月无除息 → 差应≈0）
both = pd.DataFrame({"tv": tv, "px": pxc}).dropna()
both = both[both.index.month == 9]
d = (both["tv"] - both["px"]).abs()
diff_sep = {"n": len(d), "mean_abs_diff_pp": round(float(d.mean()), 4),
            "max_abs_diff_pp": round(float(d.max()), 4)}

out = {
    "meta": {"note": "TV=用户提供月线(前复权含息)；price=Yahoo close(拆股调整,股息不调)"},
    "stats": {"tv_full": tv_full, "tv_93": tv_93, "px_93": px_93},
    "recent10": recent,
    "sept_diff_tv_vs_price": diff_sep,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT)

print("\n=== 9 月统计对照 ===")
for k, v in out["stats"].items():
    print(f"{v['name']:36s} n={v['n']:3d} 均值={v['mean']:+6.2f}% 中位={v['med']:+6.2f}% 胜率={v['win']:5.1f}% "
          f"最好={v['best']:+6.1f}%({v['best_ym']}) 最差={v['worst']:+7.1f}%({v['worst_ym']}) t={v['t']:+5.2f} p={v['p']:.4f} 非9月={v['other_mean']:+6.2f}%")
print("\n=== 近 10 年 9 月：含息(TV) vs 纯价格(price) ===")
for r in recent:
    print(f"  {r['year']}: 含息 {r['tv']:+6.2f}%  |  纯价格 {r['price']:+6.2f}%  |  差 {(r['tv'] or 0)-(r['price'] or 0):+.3f}pp")
print("\n9 月口径差异统计:", diff_sep)
