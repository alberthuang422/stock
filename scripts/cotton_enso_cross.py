# -*- coding: utf-8 -*-
"""
交叉分析：厄尔尼诺事件 × 当时全球棉花库消比 + 类比年两口径 —— 2026-09-12

与白糖（sugar_enso_cross.py）同框架，另加基本面类比年（sugar_analog_fundamental.py 方法）。
棉花市场年度 = Aug-Jul，榨季归属：onset 在 8-12 月 -> MY=Y；1-7 月 -> MY=Y-1（阈值 8）。
输出 results/cotton_enso_cross.json / results/cotton_enso_cross.csv
"""
import json
import os
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1) 库消比序列
g = pd.read_csv(os.path.join(BASE, "data", "cotton", "cotton_global_sd.csv"))
g = g.rename(columns={g.columns[0]: "MY"}).set_index("MY")

# 2) 事件表
ev = pd.read_csv(os.path.join(BASE, "results", "cotton_enso_events.csv"))

# 3) 价格（用于抢跑）
wb = load_workbook(os.path.join(BASE, "data", "sugar", "raw", "pink_sheet_2026.xlsx"),
                   read_only=True, data_only=True)
rows = list(wb["Monthly Prices"].iter_rows(values_only=True))
hdr = {str(x).strip(): i for i, x in enumerate(rows[4]) if x}
i_c = hdr["Cotton, A Index"]
px = []
for r in rows[6:]:
    if r[0] and re.match(r"^\d{4}M\d{2}$", str(r[0])):
        v = pd.to_numeric(r[i_c], errors="coerce")
        if pd.notna(v):
            px.append((str(r[0]), float(v)))
P = dict(px)
KM = sorted(P)


def at(ym):
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
    # 棉花榨季 Aug-Jul：onset 在 8-12 月 -> MY=Y；1-7 月 -> MY=Y-1
    my = on[0] if on[1] >= 8 else on[0] - 1
    sur = float(g.loc[my, "StockToUse"]) if my in g.index else np.nan
    p6a, _ = at(sh(on, -6))
    p6b, _ = at(sh(on, -1))
    run_up = round(np.log(p6b / p6a) * 100, 1) if (p6a and p6b) else None
    recs.append({
        "onset": r.onset, "peak_ym": r.peak_ym, "peak": r.peak,
        "season_MY": f"{my}/{str(my+1)[2:]}", "stock_to_use": round(sur, 1),
        "pre6_run_up": run_up, "T6": r.T6_abs, "T12": r.T12_abs, "T24": r.T24_abs,
        "T12_exc": r.T12_exc,
    })
c = pd.DataFrame(recs)
c.to_csv(os.path.join(BASE, "results", "cotton_enso_cross.csv"), index=False)
print("=== 事件 × 库消比 × 收益 ===")
print(c[["onset", "peak", "season_MY", "stock_to_use", "pre6_run_up", "T6", "T12", "T24"]].to_string(index=False))

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

print("\n=== 抢跑检验：onset 前 6 月棉价涨幅 ===")
sub = c.dropna(subset=["pre6_run_up", "T12"])
rr, pp = stats.pearsonr(sub.pre6_run_up, sub.T12)
print(f"corr(pre6 涨幅, T12) = {rr:+.2f}  p={pp:.3f}  n={len(sub)}")

# ============ 类比年 ============
# 天气形态口径（爬坡/起始月/峰值月/峰值ONI/库消比）
ev2 = ev.copy()
ev2["onset_m"] = ev2.onset_month
ev2["peak_m"] = ev2.peak_month
c2 = c.copy()
c2["ramp"] = ev2.ramp_jan_jul.values
c2["onset_m"] = ev2.onset_m.values
c2["peak_m"] = ev2.peak_m.values
# 2026 事件 target（onset 2026-05, 爬坡 +2.19, 峰值预期 12 月, 库消比 MY2025=62.2）
TARGET = {"ramp": 2.19, "onset_m": 5, "peak_m": 12, "peak": 2.4, "sur": 62.2}
c2["score_w"] = (
    (c2.ramp - TARGET["ramp"]).abs() / 1.0 * 1.0
    + (c2.onset_m - TARGET["onset_m"]).abs() / 3.0 * 1.0
    + (c2.peak_m - TARGET["peak_m"]).abs() / 3.0 * 1.0
    + (c2.peak - TARGET["peak"]).abs() / 0.8 * 1.0
    + (c2.stock_to_use - TARGET["sur"]).abs() / 8.0 * 1.0
)
cols_w = ["onset", "peak", "peak_ym", "ramp", "onset_m", "stock_to_use", "T12", "T24", "score_w"]
print("\n=== 天气形态类比年（2026 target: onset 5月/爬坡+2.19/峰值12月/库消比62.2）===")
print(c2.sort_values("score_w")[cols_w].head(8).to_string(index=False))

# 基本面口径类比年（库消比水位/变动/产需差率/产量同比/消费同比/前3年累计变动/库存同比）
gf = g.copy()
gf["sur_chg"] = gf["StockToUse"].diff()
gf["prod_g"] = gf["Production"].pct_change() * 100
gf["use_g"] = gf["Domestic Use"].pct_change() * 100
gf["stk_g"] = gf["Ending Stocks"].pct_change() * 100
gf["sur_cum3"] = gf["StockToUse"].diff(3)
gf["pdratio"] = gf["ProdMinusUse"] / gf["Production"] * 100

FEAT = ["StockToUse", "sur_chg", "pdratio", "prod_g", "use_g", "sur_cum3", "stk_g"]
sd = gf[FEAT].std()
# target = MY2025（2026 onset 5月归属 MY2025）
ty = 2025
tgt = gf.loc[ty, FEAT].values
print("\n=== 基本面口径类比年（target MY2025）===")
print("target:", {f: round(float(tgt[i]), 1) for i, f in enumerate(FEAT)})
sc = []
for y in gf.index:
    if y == ty or y < 1962:
        continue
    row = gf.loc[y, FEAT].values
    if np.isnan(row).any() or np.isnan(tgt).any():
        continue
    d = np.sqrt((((row - tgt) / sd.values) ** 2).sum())
    sc.append((int(y), float(d), {f: round(float(row[i]), 1) for i, f in enumerate(FEAT)}))
sc.sort(key=lambda x: x[1])
print("最相似 8 年（基本面孔径）:")
for y, d, feat in sc[:8]:
    print(f"  MY{y}  dist={d:.2f}  sur={feat['StockToUse']:.1f}% cum3={feat['sur_cum3']:+.1f} prod_g={feat['prod_g']:+.1f}%")

# 关联这些类比年的 T+12/T+24（用同 onset 月份最接近的事件近似——取该年 onset 在 5-7 月的事件）
analog_t = {}
for y, d, feat in sc[:8]:
    match = c[(c.onset.str.startswith(str(y))) | (c.onset.str.startswith(str(y+1)))]
    t12 = match["T12"].dropna().mean() if len(match.dropna(subset=["T12"])) else np.nan
    t24 = match["T24"].dropna().mean() if len(match.dropna(subset=["T24"])) else np.nan
    analog_t[y] = {"dist": round(d, 2), "T12": round(float(t12), 1) if not np.isnan(t12) else None,
                   "T24": round(float(t24), 1) if not np.isnan(t24) else None}
print("\n类比年结局（该年附近事件的 T12/T24）:", analog_t)

out = {
    "table": c.fillna("").to_dict("records"),
    "median_sur": round(float(med), 1),
    "low_stock": {"n": int(len(c[c.stock_to_use < med].dropna(subset=["T12"]))),
                  "T12_mean": round(float(c[c.stock_to_use < med].dropna(subset=["T12"]).T12.mean()), 1)},
    "high_stock": {"n": int(len(c[c.stock_to_use >= med].dropna(subset=["T12"]))),
                   "T12_mean": round(float(c[c.stock_to_use >= med].dropna(subset=["T12"]).T12.mean()), 1)},
    "hot_combo": hot.fillna("").to_dict("records"),
    "runup_corr": {"r": round(float(rr), 2), "p": round(float(pp), 3), "n": int(len(sub))},
    "weather_neighbors": c2.sort_values("score_w")[cols_w].head(8).fillna("").to_dict("records"),
    "fundamental_neighbors": [{"MY": y, "dist": d, **feat} for y, d, feat in sc[:8]],
    "fundamental_outcome": analog_t,
    "target_2026": TARGET,
}
with open(os.path.join(BASE, "results", "cotton_enso_cross.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nwrote results/cotton_enso_cross.json")
