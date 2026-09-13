# -*- coding: utf-8 -*-
"""
棉花 ENSO 事件 × 「剥离中国库消比」交叉分析 —— 2026-09-12（v2：剥离中国主口径）

对比 v1（全球库消比口径）：
  全球口径把 2014 中国收储的 92.1% 峰值算进去，导致事件分组的"库消比中位"高达 52.6%，
  且低/高库存分组结论可能与"可贸易真实松紧"脱节。
本脚本改用 R1_sur = (全球库存 − 中国国储) / 全球消费 作事件分组口径，重跑：
  1. 事件 × 剥离中国库消比 × 收益
  2. 低库存 vs 高库存分组（剥离中国口径中位）
  3. 抢跑检验（价格序列不变）
  4. 天气形态类比年（库消比维度改剥离中国）+ 基本面类比年（剥离中国特征）
输出 results/cotton_enso_cross_exCN.json / .csv
"""
import json
import os
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1) 剥离中国库消比序列（cotton_tradeable.csv 的 R1_sur）
M = pd.read_csv(os.path.join(BASE, "data", "cotton", "cotton_tradeable.csv"))
M = M.rename(columns={M.columns[0]: "MY"}).set_index("MY")
# R1_sur / R2_sur 只从 tradeable 脚本 1990+ 起有？重新读原始 global csv 更稳
g = pd.read_csv(os.path.join(BASE, "data", "cotton", "cotton_global_sd.csv"))
g = g.rename(columns={g.columns[0]: "MY"}).set_index("MY")

# 用 PSD 直接重算 中国库存，构造剥离中国库消比（全 1960-2026）
piv = pd.read_csv(os.path.join(BASE, "data", "sugar", "raw", "psd", "psd_alldata.csv"), low_memory=False)
piv = piv[piv.Commodity_Code == 2631000].copy()
piv["Value"] = pd.to_numeric(piv.Value, errors="coerce")
cn_stk = piv[(piv.Country_Name == "China") & (piv.Attribute_Description == "Ending Stocks")].set_index("Market_Year")["Value"]
in_stk = piv[(piv.Country_Name == "India") & (piv.Attribute_Description == "Ending Stocks")].set_index("Market_Year")["Value"]

SUR = {}
for y in g.index:
    w = g.loc[y, "Ending Stocks"]
    du = g.loc[y, "Domestic Use"]
    cn = cn_stk.get(y, 0.0)
    ind = in_stk.get(y, 0.0)
    SUR[y] = {
        "w": float(g.loc[y, "StockToUse"]),
        "exCN": float((w - cn) / du * 100),
        "exCNIN": float((w - cn - ind) / du * 100),
    }

# 2) 事件表
ev = pd.read_csv(os.path.join(BASE, "results", "cotton_enso_events.csv"))

# 3) 价格（抢跑用）
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
    my = on[0] if on[1] >= 8 else on[0] - 1
    p6a, _ = at(sh(on, -6))
    p6b, _ = at(sh(on, -1))
    run_up = round(np.log(p6b / p6a) * 100, 1) if (p6a and p6b) else None
    recs.append({
        "onset": r.onset, "peak_ym": r.peak_ym, "peak": r.peak,
        "season_MY": f"{my}/{str(my+1)[2:]}",
        "sur_w": round(SUR[my]["w"], 1) if my in SUR else None,
        "sur_exCN": round(SUR[my]["exCN"], 1) if my in SUR else None,
        "sur_exCNIN": round(SUR[my]["exCNIN"], 1) if my in SUR else None,
        "pre6_run_up": run_up, "T6": r.T6_abs, "T12": r.T12_abs, "T24": r.T24_abs,
        "T12_exc": r.T12_exc,
    })
c = pd.DataFrame(recs)
c.to_csv(os.path.join(BASE, "results", "cotton_enso_cross_exCN.csv"), index=False)
print("=== 事件 × 剥离中国库消比 × 收益 ===")
print(c[["onset", "peak", "season_MY", "sur_w", "sur_exCN", "T6", "T12", "T24"]].to_string(index=False))

# 分组：剥离中国口径中位
med_cn = c.sur_exCN.median()
print(f"\n=== 剥离中国库消比中位 {med_cn:.1f}% ===")
for lab, sub in [("低库存(剥离中)<中位", c[c.sur_exCN < med_cn]), ("高库存(剥离中)>=中位", c[c.sur_exCN >= med_cn])]:
    s = sub.dropna(subset=["T12"])
    print(f"{lab}: n={len(s)}  T12 均值 {s.T12.mean():+.1f}%  中位 {s.T12.median():+.1f}%  胜率 {(s.T12>0).mean()*100:.0f}%  |  T6 {s.T6.mean():+.1f}%  |  T24 {s.T24.mean():+.1f}%")

# 对照：全球口径中位分组（复现 v1）
med_w = c.sur_w.median()
print(f"\n=== [对照] 全球库消比中位 {med_w:.1f}% ===")
for lab, sub in [("低库存(全球)<中位", c[c.sur_w < med_w]), ("高库存(全球)>=中位", c[c.sur_w >= med_w])]:
    s = sub.dropna(subset=["T12"])
    print(f"{lab}: n={len(s)}  T12 均值 {s.T12.mean():+.1f}%  中位 {s.T12.median():+.1f}%  胜率 {(s.T12>0).mean()*100:.0f}%")

# 双层筛选：强天气(>=1.5) × 剥离中国低库存
hot = c[(c.peak >= 1.5) & (c.sur_exCN < med_cn)].dropna(subset=["T12"])
print("\n=== 强天气(>=1.5) × 剥离中国低库存 ===")
print(hot[["onset", "peak", "season_MY", "sur_exCN", "T6", "T12", "T24"]].to_string(index=False))
print(f"n={len(hot)}  T12 均值 {hot.T12.mean():+.1f}%  中位 {hot.T12.median():+.1f}%")

# 抢跑
sub = c.dropna(subset=["pre6_run_up", "T12"])
rr, pp = stats.pearsonr(sub.pre6_run_up, sub.T12)
print(f"\n抢跑 corr(pre6, T12) = {rr:+.2f} p={pp:.3f} n={len(sub)}")

# 2026 target：剥离中国库消比 MY2025
ty = 2025
print(f"\n=== 2026 事件 target（onset 2026-05, MY2025）===")
print(f"  全球库消比 {SUR[ty]['w']:.1f}%  剥离中国 {SUR[ty]['exCN']:.1f}%  剥离中印 {SUR[ty]['exCNIN']:.1f}%")

# 基本面类比年：用剥离中国库消比特征
gf = pd.DataFrame(index=g.index)
gf["sur"] = [SUR[y]["exCN"] for y in g.index]
gf["sur_chg"] = gf["sur"].diff()
gf["prod_g"] = g["Production"].pct_change() * 100
gf["use_g"] = g["Domestic Use"].pct_change() * 100
gf["stk_g"] = g["Ending Stocks"].pct_change() * 100
gf["sur_cum3"] = gf["sur"].diff(3)
FEAT = ["sur", "sur_chg", "prod_g", "use_g", "sur_cum3", "stk_g"]
sd = gf[FEAT].std()
tgt = gf.loc[ty, FEAT].values
print("\n=== 基本面类比年（剥离中国口径，target MY2025）===")
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
for y, d, feat in sc[:8]:
    print(f"  MY{y} dist={d:.2f} sur={feat['sur']:.1f}% cum3={feat['sur_cum3']:+.1f} prod_g={feat['prod_g']:+.1f}%")

out = {
    "table": c.fillna("").to_dict("records"),
    "median_exCN": round(float(med_cn), 1),
    "median_w": round(float(med_w), 1),
    "low_exCN": {"n": int(len(c[c.sur_exCN < med_cn].dropna(subset=["T12"]))),
                 "T12_mean": round(float(c[c.sur_exCN < med_cn].dropna(subset=["T12"]).T12.mean()), 1),
                 "T12_med": round(float(c[c.sur_exCN < med_cn].dropna(subset=["T12"]).T12.median()), 1),
                 "win": round(float((c[c.sur_exCN < med_cn].dropna(subset=["T12"]).T12 > 0).mean() * 100), 0)},
    "high_exCN": {"n": int(len(c[c.sur_exCN >= med_cn].dropna(subset=["T12"]))),
                  "T12_mean": round(float(c[c.sur_exCN >= med_cn].dropna(subset=["T12"]).T12.mean()), 1),
                  "win": round(float((c[c.sur_exCN >= med_cn].dropna(subset=["T12"]).T12 > 0).mean() * 100), 0)},
    "hot_combo": hot.fillna("").to_dict("records"),
    "runup_corr": {"r": round(float(rr), 2), "p": round(float(pp), 3), "n": int(len(sub))},
    "fundamental_neighbors": [{"MY": y, "dist": d, **feat} for y, d, feat in sc[:8]],
    "target_2026_exCN": {"MY": ty, "sur_exCN": round(SUR[ty]["exCN"], 1),
                         "sur_w": round(SUR[ty]["w"], 1), "sur_exCNIN": round(SUR[ty]["exCNIN"], 1)},
}
with open(os.path.join(BASE, "results", "cotton_enso_cross_exCN.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nwrote results/cotton_enso_cross_exCN.json")
