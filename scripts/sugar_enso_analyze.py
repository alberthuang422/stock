# -*- coding: utf-8 -*-
"""
厄尔尼诺 × 世界糖价（World Bank Pink Sheet "Sugar, world"）事件研究 —— 2026-09-12

为什么用 Pink Sheet 而不是 CANE ETN：
  CANE 只有 2011-09 起 → 仅覆盖 4 次厄尔尼诺事件；
  Pink Sheet 世界糖价自 1960M01 起 → 覆盖全部 22 次事件，样本量提升 5 倍。

方法（遵循 commodity-data-sources skill）
  - 事件定义：ONI 季值 >= +0.5 且连续 >= 5 个重叠季（中心月映射：DJF->1 ... NDJ->12）
  - 响应：绝对收益 + 剔除商品 β 的超额（vs Pink Sheet Non-energy 指数）
  - 窗口：A 预报→峰值+3m（ONI 滞后1月，用 onset 前3月作为"可预报点"）
          B onset→+12m（无前视：锚 onset+1 月）
  - 分档按峰值：>=2.0 / 1.5-2.0 / 1.0-1.5 / 0.5-1.0
  - 重叠窗口 -> 同时给 Mann-Whitney 秩检验
输出 results/sugar_enso.json
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
ONI = os.path.join(BASE, "data", "sugar", "raw", "oni_latest.txt")
OUT = os.path.join(BASE, "results", "sugar_enso.json")

# ---------- 1. 价格 ----------
wb = load_workbook(PINK, read_only=True, data_only=True)
rows = list(wb["Monthly Prices"].iter_rows(values_only=True))
hdr = {str(x).strip(): i for i, x in enumerate(rows[4]) if x}
i_sug, i_ne = hdr["Sugar, world"], None
for k, v in hdr.items():
    if k.startswith("Non-energy") or k == "Non-energy":
        i_ne = v

mon = []
for r in rows[6:]:
    if not r[0] or not re.match(r"^\d{4}M\d{2}$", str(r[0])):
        continue
    mon.append((str(r[0]), r[i_sug]))
sug = pd.DataFrame(mon, columns=["ym", "sugar"])
sug["sugar"] = pd.to_numeric(sug.sugar, errors="coerce")
sug = sug.dropna().reset_index(drop=True)
sug["y"] = sug.ym.str[:4].astype(int)
sug["m"] = sug.ym.str[5:].astype(int)
# 尾 bar 体检
print(f"Pink Sheet sugar: {sug.ym.iloc[0]} -> {sug.ym.iloc[-1]}  n={len(sug)}")
print(f"最新价 {sug.sugar.iloc[-1]:.3f} $/kg = {sug.sugar.iloc[-1]*45.359237:.1f} 美分/磅")

# Non-energy 指数在第二个表
nb = list(wb["Monthly Indices"].iter_rows(values_only=True))
nhdr = {str(x).strip(): i for i, x in enumerate(nb[5]) if x}
print("Indices cols:", {k: v for k, v in nhdr.items()})
ine = next(v for k, v in nhdr.items() if k.lower().startswith("non-energy"))
nmon = []
for r in nb[9:]:
    if not r[0] or not re.match(r"^\d{4}M\d{2}$", str(r[0])):
        continue
    nmon.append((str(r[0]), r[ine]))
ne = pd.DataFrame(nmon, columns=["ym", "nex"])
ne["nex"] = pd.to_numeric(ne["nex"], errors="coerce")
df = sug.merge(ne, on="ym", how="left")

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

# 爬坡速度：同年 1 月 -> 7 月 ONI 变化
ramp = {}
for y in sorted({k[0] for k in keys}):
    if (y, 1) in vals and (y, 7) in vals:
        ramp[y] = round(vals[(y, 7)] - vals[(y, 1)], 2)
rk = pd.Series(ramp).sort_values(ascending=False)
print("爬坡最快 5 年（1月->7月 ONI）:", rk.head(5).to_dict())

# ---------- 3. 事件响应 ----------
idx = {(int(r.y), int(r.m)): k for k, r in enumerate(df.itertuples())}
yrs = df.y.values
mos = df.m.values
px = df.sugar.values
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
    on, pk = ev["onset"], ev["peak_ym"]          # tuples
    ramp_yr = ramp.get(on[0])
    rec = {"onset": f"{on[0]}-{on[1]:02d}", "peak_ym": f"{pk[0]}-{pk[1]:02d}", "peak": ev["peak"],
           "len": ev["len"], "onset_month": on[1], "peak_month": pk[1], "ramp_jan_jul": ramp_yr}
    for h in (3, 6, 12, 24):
        rec[f"T{h}_abs"] = ret(shift(on, 1), shift(on, 1 + h), px)      # 无前视：onset+1 起算
        rec[f"T{h}_exc"] = None
        a = ret(shift(on, 1), shift(on, 1 + h), px)
        b = ret(shift(on, 1), shift(on, 1 + h), nev)
        if a is not None and b is not None:
            rec[f"T{h}_exc"] = round(a - b, 1)
        rec[f"T{h}_abs"] = None if rec[f"T{h}_abs"] is None else round(rec[f"T{h}_abs"], 1)
    # 预报窗口：onset 前 6 月 -> 峰值 +6 月
    rec["A_pre6_to_peak6"] = ret(shift(on, -6), shift(pk, 6), px)
    rec["peak_px"] = None
    kp = pos(*pk)
    if kp is not None:
        rec["peak_px"] = round(float(px[kp]), 4)
    rows.append(rec)

res = pd.DataFrame(rows)
res.to_csv(os.path.join(BASE, "results", "sugar_enso_events.csv"), index=False)
print("\n=== 全部事件（糖价对数收益 %）===")
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

print("\n=== 按爬坡速度（1月->7月 ONI 变化）===")
fast = res[res.ramp_jan_jul >= 1.5]
print(f"快速爬坡 (>=1.5): n={len(fast)}  T12 均值 {fast.T12_abs.mean():.1f}%  中位 {fast.T12_abs.median():.1f}%  胜率 {(fast.T12_abs>0).mean()*100:.0f}%")
print(fast[["onset", "peak", "ramp_jan_jul", "T6_abs", "T12_abs", "T24_abs"]].to_string(index=False))

# ---------- 4. 期限扫描 corr(ONI_t, fwd_H) ----------
print("\n=== 期限扫描：corr(ONI_t, 未来 H 月糖价对数收益) ===")
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
            la.append((keys[i], max(keys[i:j], key=lambda k: -vals[k]), vals[max(keys[i:j], key=lambda k: -vals[k])]))
        i = j
    else:
        i += 1
ln = []
for on, pk, pkv in la:
    r12 = ret(shift(on, 1), shift(on, 13), px)
    if r12 is not None:
        ln.append(round(r12, 1))
print(f"\n=== 拉尼娜（<=-0.5，>=5 季）n={len(ln)}  T+12 均值 {np.mean(ln):.1f}%  中位 {np.median(ln):.1f}%  胜率 {np.mean([x>0 for x in ln])*100:.0f}% ===")

# ---------- 6. 2026 进行中事件 ----------
print("\n=== 2026 进行中 ===")
print(f"ONI 最新 JJA 2026 = +1.80；爬坡 DJF2025->JJA2026 = {round(vals[(2026,7)]-vals[(2025,12)],2)}")
t12_now = ret((2026, 1), (2026, 8), px)
print(f"糖价 2026-01 -> 2026-08：{t12_now:.1f}%  (价格 {px[pos(2026,1)]:.3f} -> {px[pos(2026,8)]:.3f} $/kg)")
# 与 1997 / 2015 同期路径对比
for ref in (1982, 1997, 2009, 2015, 2023):
    ks = [k for k in range(len(df)) if yrs[k] == ref and 1 <= mos[k] <= 8]
    if len(ks) >= 2:
        print(f"  {ref} 年 1->8 月: {np.log(px[ks[-1]]/px[ks[0]])*100:+.1f}%   ({px[ks[0]]:.3f}->{px[ks[-1]]:.3f})")

out = {
    "meta": {"source": "World Bank Pink Sheet Sugar, world ($/kg, 1960M01-2026M08) + NOAA CPC ONI",
             "method": "ONI>=0.5 连续>=5 季; 无前视锚 onset+1 月; 超额=减 Non-energy 商品指数"},
    "latest_price": {"ym": sug.ym.iloc[-1], "usd_kg": round(float(sug.sugar.iloc[-1]), 4),
                     "cents_lb": round(float(sug.sugar.iloc[-1]) * 45.359237, 1)},
    "current_2026": {"oni_jja": 1.80,
                     "ramp_djf2025_to_jja2026": round(vals[(2026, 7)] - vals[(2025, 12)], 2),
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
