#!/usr/bin/env python3
"""VIX 低位回升周期中, SPX 最大回撤的发生时点分析。

问题: VIX 从 <15 回升到 ≥20 的过程里, 标普500 跌最多的时候在什么时候?
- 事件: 每个 VIX<15 区间, 结束日 E (VIX 首次 ≥15); 之后 VIX 首次 ≥20 的日 T20
- 窗口: [E, T20+20], 观察 SPX 的:
  1) 从 E 起算的最低累计收益 (cum_min) 及其日期 -> 谷底日
  2) 窗口内 SPX 峰值日 (可能 >E)
  3) 最大回撤幅度 (峰值->谷底, 或 E->谷底)
  4) 谷底时 VIX 值 / 谷底相对 T20 的天数 / 谷底相对 VIX 峰值日的天数
- 输出: results/vix_rebound_dd.json + 控制台摘要
数据: data/vix + data/gspc (1990-2026)
"""
import os, json
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def pct(a, b):
    return (b / a - 1) * 100

v = pd.read_csv(os.path.join(ROOT, "data", "vix", "VIX, 1D.csv"), parse_dates=["date"])
g = pd.read_csv(os.path.join(ROOT, "data", "gspc", "GSPC, 1D.csv"), parse_dates=["date"])
m = v.merge(g, on="date", suffixes=("_vix", "_gspc"))[["date", "close_vix", "close_gspc"]]
m = m.sort_values("date").reset_index(drop=True)
vix = m["close_vix"].values
spx = m["close_gspc"].values
n = len(m)

# ---------- 识别 VIX<15 区间 ----------
mask = vix < 15
runs = []
i = 0
while i < n:
    if mask[i]:
        j = i
        while j + 1 < n and mask[j + 1]:
            j += 1
        runs.append((i, j))
        i = j + 1
    else:
        i += 1

# ---------- 每个区间: 找回升窗口 [E, T20+20] ----------
ev = []
for si, ei in runs:
    E = ei + 1  # 区间结束次日(VIX 首次 ≥15)
    if E >= n:
        continue
    # 找 VIX 首次 >=20 (限 400 天内)
    T20 = None
    for k in range(E, min(E + 400, n)):
        if vix[k] >= 20:
            T20 = k
            break
    if T20 is None:
        continue
    W_end = min(T20 + 20, n - 1)
    win = m.iloc[E:W_end + 1].copy().reset_index(drop=True)
    if len(win) < 5:
        continue
    # SPX 从 E 起算的累计收益
    cum = pct(spx[E], win["close_gspc"].values)
    cum_min = cum.min()
    cum_min_i = int(cum.argmin())
    cum_max = cum.max()
    # 窗口内峰->谷 最大回撤
    peak_i = 0
    peak_v = spx[E]
    max_dd = 0.0
    dd_valley = 0
    for k in range(len(win)):
        if win["close_gspc"].values[k] > peak_v:
            peak_v = win["close_gspc"].values[k]
            peak_i = k
        dd = pct(peak_v, win["close_gspc"].values[k])
        if dd < max_dd:
            max_dd = dd
            dd_valley = k
    # VIX 峰值日 (窗口内)
    vix_peak_i = int(win["close_vix"].values.argmax())
    ev.append({
        "start": str(m.date.iloc[si].date()), "end": str(m.date.iloc[ei].date()),
        "E": str(m.date.iloc[E].date()), "T20": str(m.date.iloc[T20].date()),
        "run_days": ei - si + 1,
        "days_E_to_T20": T20 - E + 1,
        "cum_min": round(float(cum_min), 1), "cum_min_day": str(win.date.iloc[cum_min_i].date()),
        "cum_min_offset": cum_min_i,  # 相对 E 的天数
        "cum_max": round(float(cum_max), 1),
        "max_dd": round(float(max_dd), 1), "dd_valley_day": str(win.date.iloc[dd_valley].date()),
        "dd_valley_offset": dd_valley,
        "vix_at_valley": round(float(win["close_vix"].values[cum_min_i]), 1),
        "vix_at_vixpeak": round(float(win["close_vix"].values[vix_peak_i]), 1),
        "valley_rel_T20": cum_min_i - (T20 - E + 1),  # 负 = 谷底在 VIX 破 20 之前
        "valley_rel_vixpeak": cum_min_i - vix_peak_i,  # 负 = 谷底在 VIX 峰值之前
    })

df = pd.DataFrame(ev)

def stats(a):
    a = np.array(a, dtype=float)
    return {"n": int(len(a)), "mean": round(float(a.mean()), 1), "med": round(float(np.median(a)), 1),
            "p25": round(float(np.percentile(a, 25)), 1), "p75": round(float(np.percentile(a, 75)), 1),
            "min": round(float(a.min()), 1), "max": round(float(a.max()), 1)}

out = {
    "meta": {"n_events": len(df),
             "E_to_T20": stats(df["days_E_to_T20"]),
             "valley_offset_E": stats(df["cum_min_offset"]),
             "vix_at_valley": stats(df["vix_at_valley"]),
             "valley_rel_T20": stats(df["valley_rel_T20"]),
             "valley_rel_vixpeak": stats(df["valley_rel_vixpeak"]),
             "cum_min": stats(df["cum_min"]),
             "max_dd": stats(df["max_dd"]),
             "frac_dd_gt3": round(float((df["max_dd"] < -3).mean()) * 100, 1),
             "frac_dd_gt5": round(float((df["max_dd"] < -5).mean()) * 100, 1),
             "frac_dd_gt10": round(float((df["max_dd"] < -10).mean()) * 100, 1)},
    "by_speed": {},
    "detail": df.to_dict("records"),
}

# 按回升速度分组: 快(E->T20<=10d) vs 慢(>10d)
for name, cond in [("fast<=10d", df["days_E_to_T20"] <= 10), ("slow>10d", df["days_E_to_T20"] > 10)]:
    sub = df[cond]
    out["by_speed"][name] = {
        "n": int(len(sub)),
        "valley_offset_E": stats(sub["cum_min_offset"]),
        "vix_at_valley": stats(sub["vix_at_valley"]),
        "valley_rel_T20": stats(sub["valley_rel_T20"]),
        "cum_min": stats(sub["cum_min"]),
        "max_dd": stats(sub["max_dd"]),
        "days_E_to_T20": stats(sub["days_E_to_T20"]),
    }

with open(os.path.join(ROOT, "results", "vix_rebound_dd.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

# ---------- 控制台 ----------
print(f"事件数: {len(df)}")
o = out["meta"]
print(f"\nVIX 从<15结束日E 到首次≥20: 中位 {o['E_to_T20']['med']} 天 (均值 {o['E_to_T20']['mean']})")
print(f"SPX 最低点(从E起算) 相对E: 中位 +{o['valley_offset_E']['med']} 天 (P25 {o['valley_offset_E']['p25']} / P75 {o['valley_offset_E']['p75']})")
print(f"SPX 见底时 VIX 值: 中位 {o['vix_at_valley']['med']} (P25 {o['vix_at_valley']['p25']} / P75 {o['vix_at_valley']['p75']})")
print(f"谷底 相对 VIX破20日: 中位 {o['valley_rel_T20']['med']} 天 (负=谷底在破20前)")
print(f"谷底 相对 VIX峰值日: 中位 {o['valley_rel_vixpeak']['med']} 天 (负=谷底在VIX峰值前)")
print(f"从E起算最低累计收益: 中位 {o['cum_min']['med']}% (P25 {o['cum_min']['p25']} / 最差 {o['cum_min']['min']})")
print(f"窗口内峰谷最大回撤: 中位 {o['max_dd']['med']}% (最差 {o['max_dd']['min']})")
print(f"回撤>3%: {o['frac_dd_gt3']}% | >5%: {o['frac_dd_gt5']}% | >10%: {o['frac_dd_gt10']}%")
print("\n按回升速度:")
for name in ["fast<=10d", "slow>10d"]:
    s = out["by_speed"][name]
    print(f"  {name}: n={s['n']} | 谷底相对E中位 {s['valley_offset_E']['med']}d | 见底VIX中位 {s['vix_at_valley']['med']} | cum_min中位 {s['cum_min']['med']}% | max_dd中位 {s['max_dd']['med']}% | E->T20 {s['days_E_to_T20']['med']}d")

# 典型事件展示: 回撤最大10个
print("\n=== 回撤最大的 10 个事件 ===")
top = df.nlargest(10, "max_dd")
for _, r in top.iterrows():
    print(f"{r['start']}~{r['end']} (低{r['run_days']}d) | E={r['E']} T20={r['T20']} | "
          f"E->T20 {r['days_E_to_T20']}d | 谷底 {r['cum_min_offset']}d 后 (E起), VIX={r['vix_at_valley']} | "
          f"cum_min {r['cum_min']}% dd {r['max_dd']}% | 谷底相对T20 {r['valley_rel_T20']}d")
