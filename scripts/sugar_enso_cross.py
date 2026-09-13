# -*- coding: utf-8 -*-
"""
交叉分析：厄尔尼诺事件 × 当时全球糖库消比 —— 2026-09-12

核心问题：糖价对 ENSO 的响应为什么不像橡胶那样稳定？
假设：天气冲击的价格弹性取决于「库存缓冲」——低库消比放大冲击，高库消比吸收冲击。
输出 results/sugar_enso_cross.json
"""
import json
import os
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1) 库消比序列
g = pd.read_csv(os.path.join(BASE, "data", "sugar", "sugar_global_sd.csv"))
g = g.rename(columns={g.columns[0]: "MY"}).set_index("MY")

# 2) 事件表
ev = pd.read_csv(os.path.join(BASE, "results", "sugar_enso_events.csv"))

# 3) 价格（用于抢跑）
wb = load_workbook(os.path.join(BASE, "data", "sugar", "raw", "pink_sheet_2026.xlsx"),
                   read_only=True, data_only=True)
rows = list(wb["Monthly Prices"].iter_rows(values_only=True))
hdr = {str(x).strip(): i for i, x in enumerate(rows[4]) if x}
i_s = hdr["Sugar, world"]
px = []
for r in rows[6:]:
    if r[0] and re.match(r"^\d{4}M\d{2}$", str(r[0])):
        v = pd.to_numeric(r[i_s], errors="coerce")
        if pd.notna(v):
            px.append((str(r[0]), float(v)))
P = dict(px)
KM = sorted(P)


def at(ym):
    """ym=(y,m) -> 最近可得月价格"""
    y, m = ym
    key = f"{y}M{m:02d}"
    if key in P:
        return P[key], key
    cand = [k for k in KM if k <= key]
    return (P[cand[-1]], cand[-1]) if cand else (None, None)


def sh(ym, n):
    y, m = ym
    m += n
    y += (m - 1) // 12
    return (y, (m - 1) % 12 + 1)


recs = []
for r in ev.itertuples():
    on = tuple(map(int, r.onset.split("-")))
    # [口径修正] 糖榨季 = Oct-Sep。onset 在 10-12 月 -> 属当年榨季 MY=Y；
    #            1-9 月 -> 仍在本榨季内，MY=Y-1（v1 误用阈值 7，把 7/8/9 月错配了一年）
    my = on[0] if on[1] >= 10 else on[0] - 1
    sur = float(g.loc[my, "StockToUse"]) if my in g.index else np.nan
    # 事件所影响/收获的榨季（天气作用于当年生长季 -> 收成落在 MY=Y 或 Y+1）
    my_imp = on[0] if on[1] >= 10 else on[0]
    sur_imp = float(g.loc[my_imp, "StockToUse"]) if my_imp in g.index else np.nan
    p6a, _ = at(sh(on, -6))
    p6b, _ = at(sh(on, -1))
    p_now, _ = at(on)
    run_up = round(np.log(p6b / p6a) * 100, 1) if (p6a and p6b) else None
    recs.append({
        "onset": r.onset, "peak_ym": r.peak_ym, "peak": r.peak,
        "season_MY": f"{my}/{str(my+1)[2:]}", "stock_to_use": round(sur, 1),
        "impact_MY": f"{my_imp}/{str(my_imp+1)[2:]}", "sur_impact": round(sur_imp, 1),
        "pre6_run_up": run_up, "T6": r.T6_abs, "T12": r.T12_abs, "T24": r.T24_abs,
        "T12_exc": r.T12_exc,
    })
c = pd.DataFrame(recs)
c.to_csv(os.path.join(BASE, "results", "sugar_enso_cross.csv"), index=False)
print("=== 事件 × 库消比 × 收益 ===")
print(c.to_string(index=False))

# 分组：低库存（< 中位）vs 高库存
med = c.stock_to_use.median()
print(f"\n库消比中位 {med:.1f}%")
for lab, sub in [("低库存 (<中位)", c[c.stock_to_use < med]), ("高库存 (>=中位)", c[c.stock_to_use >= med])]:
    s = sub.dropna(subset=["T12"])
    print(f"{lab}: n={len(s)}  T12 均值 {s.T12.mean():+.1f}%  中位 {s.T12.median():+.1f}%  胜率 {(s.T12>0).mean()*100:.0f}%  |  T6 均值 {s.T6.mean():+.1f}%")

print("\n=== 双层筛选：强天气(峰值>=1.5) × 低库存 ===")
hot = c[(c.peak >= 1.5) & (c.stock_to_use < med)].dropna(subset=["T12"])
print(hot[["onset", "peak", "season_MY", "stock_to_use", "pre6_run_up", "T6", "T12", "T24"]].to_string(index=False))
print(f"n={len(hot)}  T12 均值 {hot.T12.mean():+.1f}%  中位 {hot.T12.median():+.1f}%")

print("\n=== 抢跑检验：onset 前 6 月糖价涨幅 ===")
print(f"全样本 pre6 均值 {c.pre6_run_up.mean():+.1f}%  中位 {c.pre6_run_up.median():+.1f}%")
sub = c.dropna(subset=["pre6_run_up", "T12"])
rr, pp = np.corrcoef(sub.pre6_run_up, sub.T12)[0, 1], None
from scipy import stats  # noqa: E402
rr, pp = stats.pearsonr(sub.pre6_run_up, sub.T12)
print(f"corr(pre6 涨幅, T12) = {rr:+.2f}  p={pp:.3f}  n={len(sub)}")

# 排名：当前 2026 事件的相似度打分
print("\n=== 2026 事件（onset 2026-05, 爬坡 +2.19, 库消比 24.6%）的邻居 ===")
c2 = c.copy()
c2["d_ramp"] = (c2.index * 0)  # placeholder
ev2 = pd.read_csv(os.path.join(BASE, "results", "sugar_enso_events.csv"))
c2["ramp"] = ev2.ramp_jan_jul.values
c2["onset_m"] = ev2.onset_month.values
c2["peak_m"] = [int(x.split("-")[1]) for x in c2.peak_ym]
TARGET = {"ramp": 2.19, "onset_m": 5, "peak_m": 12, "peak": 2.4, "sur": 24.6}
c2["score"] = (
    (c2.ramp - TARGET["ramp"]).abs() / 1.0 * 1.0
    + (c2.onset_m - TARGET["onset_m"]).abs() / 3.0 * 1.0
    + (c2.peak - TARGET["peak"]).abs() / 0.8 * 1.0
    + (c2.stock_to_use - TARGET["sur"]).abs() / 5.0 * 1.0
)
cols = ["onset", "peak", "peak_ym", "ramp", "onset_m", "stock_to_use", "T6", "T12", "T24", "score"]
print(c2.sort_values("score")[cols].head(8).to_string(index=False))

out = {
    "table": c.fillna("").to_dict("records"),
    "median_sur": round(float(med), 1),
    "low_stock": {"n": int(len(c[c.stock_to_use < med].dropna(subset=["T12"]))),
                  "T12_mean": round(float(c[c.stock_to_use < med].dropna(subset=["T12"]).T12.mean()), 1)},
    "hot_combo": hot.fillna("").to_dict("records"),
    "runup_corr": {"r": round(float(rr), 2), "p": round(float(pp), 3), "n": int(len(sub))},
    "neighbors": c2.sort_values("score")[cols].head(8).fillna("").to_dict("records"),
    "target_2026": TARGET,
}
with open(os.path.join(BASE, "results", "sugar_enso_cross.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nwrote results/sugar_enso_cross.json")
