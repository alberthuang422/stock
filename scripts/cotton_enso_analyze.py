# -*- coding: utf-8 -*-
"""
厄尔尼诺 × 世界棉价（World Bank Pink Sheet "Cotton, A Index"）事件研究 —— 2026-09-12

与白糖（sugar_enso_analyze.py）同框架，逐品种实测（不外推）。
棉花主产区对 ENSO 的传导比糖更直接：
  厄尔尼诺 -> 印度季风偏弱 + 巴基斯坦/澳大利亚干旱 -> 减产（利多棉价）
  拉尼娜   -> 美国德州（最大产棉州）干旱 -> 美棉减产；但印/巴/澳降水改善 -> 增产
  => 多产区方向部分对冲，须实测净效应。
价格 = Pink Sheet "Cotton, A Index"（col 54，$/kg，1960M01-2026M08，800 月）
输出 results/cotton_enso.json / results/cotton_enso_events.csv
"""
import json
import os
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PINK = os.path.join(BASE, "data", "sugar", "raw", "pink_sheet_2026.xlsx")
ONI = os.path.join(BASE, "data", "cotton", "raw", "oni_latest.txt")
OUT = os.path.join(BASE, "results", "cotton_enso.json")

# ---------- 1. 价格 ----------
wb = load_workbook(PINK, read_only=True, data_only=True)
rows = list(wb["Monthly Prices"].iter_rows(values_only=True))
hdr = {str(x).strip(): i for i, x in enumerate(rows[4]) if x}
i_cot, i_ne = hdr["Cotton, A Index"], None
for k, v in hdr.items():
    if k.lower().startswith("non-energy"):
        i_ne = v

mon = []
for r in rows[6:]:
    if not r[0] or not re.match(r"^\d{4}M\d{2}$", str(r[0])):
        continue
    mon.append((str(r[0]), r[i_cot]))
cot = pd.DataFrame(mon, columns=["ym", "cotton"])
cot["cotton"] = pd.to_numeric(cot.cotton, errors="coerce")
cot = cot.dropna().reset_index(drop=True)
cot["y"] = cot.ym.str[:4].astype(int)
cot["m"] = cot.ym.str[5:].astype(int)
print(f"Pink Sheet cotton A Index: {cot.ym.iloc[0]} -> {cot.ym.iloc[-1]}  n={len(cot)}")
print(f"最新价 {cot.cotton.iloc[-1]:.3f} $/kg = {cot.cotton.iloc[-1]*45.359237:.1f} 美分/磅")

nb = list(wb["Monthly Indices"].iter_rows(values_only=True))
nhdr = {str(x).strip(): i for i, x in enumerate(nb[5]) if x}
ine = next(v for k, v in nhdr.items() if k.lower().startswith("non-energy"))
nmon = []
for r in nb[9:]:
    if not r[0] or not re.match(r"^\d{4}M\d{2}$", str(r[0])):
        continue
    nmon.append((str(r[0]), r[ine]))
ne = pd.DataFrame(nmon, columns=["ym", "nex"])
ne["nex"] = pd.to_numeric(ne["nex"], errors="coerce")
df = cot.merge(ne, on="ym", how="left")

# ---------- 2. ONI ----------
seas = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6, "JJA": 7,
        "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
orows = []
for line in open(ONI, encoding="utf-8"):
    p = line.split()
    if len(p) >= 4 and p[0] in seas:
        try:
            orows.append({"y": int(p[1]), "m": seas[p[0]], "oni": float(p[3])})
        except ValueError:
            pass
oni = pd.DataFrame(orows).sort_values(["y", "m"]).reset_index(drop=True)
vals = {(int(r.y), int(r.m)): float(r.oni) for r in oni.itertuples()}
keys = sorted(vals)

events = []
i = 0
while i < len(keys):
    if vals[keys[i]] >= 0.5:
        j = i
        while j < len(keys) and vals[keys[j]] >= 0.5:
            j += 1
        if j - i >= 5:
            seg = keys[i:j]
            pk = max(seg, key=lambda k: vals[k])
            events.append({"onset": keys[i], "end": keys[j - 1], "peak_ym": pk,
                           "peak": round(vals[pk], 2), "len": j - i})
        i = j
    else:
        i += 1
print(f"events (>=0.5, >=5 seasons): {len(events)}")

ramp = {}
for y in sorted({k[0] for k in keys}):
    if (y, 1) in vals and (y, 7) in vals:
        ramp[y] = round(vals[(y, 7)] - vals[(y, 1)], 2)
rk = pd.Series(ramp).sort_values(ascending=False)
print("爬坡最快 5 年（1月->7月 ONI）:", rk.head(5).to_dict())

# ---------- 3. 事件响应 ----------
yrs = df.y.values
mos = df.m.values
px = df.cotton.values
nev = df["nex"].values


def pos(y, m):
    for k in range(len(df)):
        if yrs[k] == y and mos[k] == m:
            return k
    return None


def shift(ym, n):
    y, m = ym
    m += n
    y += (m - 1) // 12
    return (y, (m - 1) % 12 + 1)


def ret(a_ym, b_ym, series):
    ka, kb = pos(*a_ym), pos(*b_ym)
    if ka is None or kb is None:
        return None
    if series[ka] <= 0 or series[kb] <= 0 or np.isnan(series[ka]) or np.isnan(series[kb]):
        return None
    return float(np.log(series[kb] / series[ka]) * 100)


rows = []
for ev in events:
    on, pk = ev["onset"], ev["peak_ym"]
    ramp_yr = ramp.get(on[0])
    rec = {"onset": f"{on[0]}-{on[1]:02d}", "peak_ym": f"{pk[0]}-{pk[1]:02d}", "peak": ev["peak"],
           "len": ev["len"], "onset_month": on[1], "peak_month": pk[1], "ramp_jan_jul": ramp_yr}
    for h in (3, 6, 12, 24):
        rec[f"T{h}_abs"] = ret(shift(on, 1), shift(on, 1 + h), px)
        rec[f"T{h}_exc"] = None
        a = ret(shift(on, 1), shift(on, 1 + h), px)
        b = ret(shift(on, 1), shift(on, 1 + h), nev)
        if a is not None and b is not None:
            rec[f"T{h}_exc"] = round(a - b, 1)
        rec[f"T{h}_abs"] = None if rec[f"T{h}_abs"] is None else round(rec[f"T{h}_abs"], 1)
    rec["A_pre6_to_peak6"] = ret(shift(on, -6), shift(pk, 6), px)
    rec["peak_px"] = None
    kp = pos(*pk)
    if kp is not None:
        rec["peak_px"] = round(float(px[kp]), 4)
    rows.append(rec)

res = pd.DataFrame(rows)
res.to_csv(os.path.join(BASE, "results", "cotton_enso_events.csv"), index=False)
print("\n=== 全部事件（棉价对数收益 %）===")
print(res[["onset", "peak_ym", "peak", "onset_month", "ramp_jan_jul", "T6_abs", "T12_abs", "T24_abs", "T12_exc"]].to_string(index=False))


def band(p):
    return "超强(>=2.0)" if p >= 2.0 else "强(1.5-2.0)" if p >= 1.5 else "中等(1.0-1.5)" if p >= 1.0 else "弱(0.5-1.0)"


res["band"] = res.peak.apply(band)
print("\n=== 按强度分档（T+12 绝对 / 超额）===")
g = res.groupby("band").agg(n=("T12_abs", "size"), T12_abs_mean=("T12_abs", "mean"),
                            T12_abs_med=("T12_abs", "median"), win=("T12_abs", lambda x: (x > 0).mean() * 100),
                            T12_exc_mean=("T12_exc", "mean"), T12_exc_med=("T12_exc", "median"),
                            T24_abs_mean=("T24_abs", "mean"))
print(g.round(1).to_string())

print("\n=== 按 onset 月份 ===")
gm = res.groupby("onset_month").agg(n=("T12_abs", "size"), T12=("T12_abs", "mean"), T12m=("T12_abs", "median"))
print(gm.round(1).to_string())

print("\n=== 快速爬坡 (>=1.5) ===")
fast = res[res.ramp_jan_jul >= 1.5]
print(f"n={len(fast)}  T12 均值 {fast.T12_abs.mean():.1f}%  中位 {fast.T12_abs.median():.1f}%  胜率 {(fast.T12_abs>0).mean()*100:.0f}%")
print(fast[["onset", "peak", "ramp_jan_jul", "T6_abs", "T12_abs", "T24_abs"]].to_string(index=False))

# ---------- 4. 期限扫描 ----------
print("\n=== 期限扫描：corr(ONI_t, 未来 H 月棉价对数收益) ===")
scan = {}
for H in range(0, 37, 3):
    xs, ys = [], []
    for k in range(len(df)):
        if k + H >= len(df) or np.isnan(px[k]) or np.isnan(px[k + H]):
            continue
        ym = (int(yrs[k]), int(mos[k]))
        if ym not in vals or px[k] <= 0 or px[k + H] <= 0:
            continue
        xs.append(vals[ym])
        ys.append(np.log(px[k + H] / px[k]))
    if len(xs) > 24:
        r, p = stats.pearsonr(xs, ys)
        scan[H] = (round(r, 3), len(xs))
print({k: v[0] for k, v in scan.items()})

# 回归 + Newey-West（H=12）
import statsmodels.api as sm  # noqa: E402
xs, ys, ne_s = [], [], []
H = 12
for k in range(len(df) - H):
    ym = (int(yrs[k]), int(mos[k]))
    if ym not in vals or np.isnan(px[k]) or np.isnan(px[k + H]) or px[k] <= 0 or px[k + H] <= 0:
        continue
    xs.append(vals[ym])
    ys.append(np.log(px[k + H] / px[k]) * 100)
    ne_s.append(nev[k + H] / nev[k] if not np.isnan(nev[k]) and nev[k] > 0 else np.nan)
X = sm.add_constant(pd.DataFrame({"oni": xs}))
m1 = sm.OLS(ys, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
d2 = pd.DataFrame({"oni": xs, "ne": ne_s}).dropna()
m2 = sm.OLS(pd.Series(ys).loc[d2.index], sm.add_constant(d2)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
print(f"\nH=12 回归 n={len(xs)}")
print(f"  单变量  ONI 系数 {m1.params['oni']:+.2f}%/℃  t={m1.tvalues['oni']:.2f}  R2={m1.rsquared:.3f}")
print(f"  +商品β  ONI 系数 {m2.params['oni']:+.2f}%/℃  t={m2.tvalues['oni']:.2f}  R2={m2.rsquared:.3f}")

# ---------- 5. 拉尼娜对称性 ----------
la = []
i = 0
while i < len(keys):
    if vals[keys[i]] <= -0.5:
        j = i
        while j < len(keys) and vals[keys[j]] <= -0.5:
            j += 1
        if j - i >= 5:
            la.append((keys[i], max(keys[i:j], key=lambda k: -vals[k])))
        i = j
    else:
        i += 1
ln = []
for on, pk in la:
    r12 = ret(shift(on, 1), shift(on, 13), px)
    if r12 is not None:
        ln.append(round(r12, 1))
print(f"\n=== 拉尼娜（<=-0.5，>=5 季）n={len(ln)}  T+12 均值 {np.mean(ln):.1f}%  中位 {np.median(ln):.1f}%  胜率 {np.mean([x>0 for x in ln])*100:.0f}% ===")

# ---------- 6. 2026 进行中 ----------
print("\n=== 2026 进行中 ===")
print(f"ONI 最新 JJA 2026 = +{vals.get((2026,7), float('nan')):.2f}")
t12_now = ret((2026, 1), (2026, 8), px)
print(f"棉价 2026-01 -> 2026-08：{t12_now:.1f}%  (价格 {px[pos(2026,1)]:.3f} -> {px[pos(2026,8)]:.3f} $/kg)")
for ref in (1982, 1997, 2009, 2015, 2023):
    ks = [k for k in range(len(df)) if yrs[k] == ref and 1 <= mos[k] <= 8]
    if len(ks) >= 2:
        print(f"  {ref} 年 1->8 月: {np.log(px[ks[-1]]/px[ks[0]])*100:+.1f}%   ({px[ks[0]]:.3f}->{px[ks[-1]]:.3f})")

out = {
    "meta": {"source": "World Bank Pink Sheet Cotton A Index ($/kg, 1960M01-2026M08) + NOAA CPC ONI",
             "method": "ONI>=0.5 连续>=5 季; 无前视锚 onset+1 月; 超额=减 Non-energy 商品指数"},
    "latest_price": {"ym": cot.ym.iloc[-1], "usd_kg": round(float(cot.cotton.iloc[-1]), 4),
                     "cents_lb": round(float(cot.cotton.iloc[-1]) * 45.359237, 1)},
    "current_2026": {"oni_jja": round(vals.get((2026, 7), float("nan")), 2),
                     "ramp_djf2025_to_jja2026": round(vals.get((2026, 7), float("nan")) - vals.get((2025, 12), float("nan")), 2),
                     "price_jan_to_aug_pct": round(float(t12_now), 1)},
    "events": res.fillna("").to_dict("records"),
    "by_band": g.round(1).reset_index().to_dict("records"),
    "ramp_fastest": rk.head(8).to_dict(),
    "term_scan": {str(k): v[0] for k, v in scan.items()},
    "reg_H12": {"univar_coef": round(float(m1.params['oni']), 2), "univar_t": round(float(m1.tvalues['oni']), 2),
                "ctrl_coef": round(float(m2.params['oni']), 2), "ctrl_t": round(float(m2.tvalues['oni']), 2),
                "n": len(xs)},
    "lanina": {"n": len(ln), "mean": round(float(np.mean(ln)), 1), "median": round(float(np.median(ln)), 1)},
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nwrote", OUT)
