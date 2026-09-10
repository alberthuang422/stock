# -*- coding: utf-8 -*-
"""
季节性实证：柴油需求季节 vs 农产品价格季节（2026-09-10）
- EIA WGFUPUS2 美国馏分油产品供应（周度, kb/d） -> 月度季节指数
- 农产品/柴油期货月度收益季节性
输出 results/agri_diesel_seasonality_20260910.json
"""
import json, os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP, RES = os.path.join(BASE, "Temp"), os.path.join(BASE, "results")

# ---------- 1. EIA 馏分油需求 ----------
xl = pd.read_excel(os.path.join(TEMP, "eia_distillate_w.xls"), sheet_name=None, header=None)
print("sheets:", list(xl.keys()))
df_eia = None
for name, sh in xl.items():
    # 找形如 1991-02-08 的日期列
    for c in range(min(4, sh.shape[1])):
        col = pd.to_datetime(sh[c], errors="coerce")
        if col.notna().sum() > 500:
            val = pd.to_numeric(sh[c + 1], errors="coerce")
            df_eia = pd.DataFrame({"date": col, "val": val}).dropna()
            print(f"  sheet '{name}' col{c} rows={len(df_eia)} "
                  f"{df_eia.date.min().date()}~{df_eia.date.max().date()}")
            break
    if df_eia is not None:
        break

df_eia = df_eia.set_index("date").sort_index()
df_eia["val"] = df_eia["val"].replace(0, np.nan)
# 月度均值 -> 季节指数
m = df_eia["val"].resample("ME").mean()
m = m[m.index.year >= 1995]              # 剔除早期结构差异
seas = m.groupby(m.index.month).mean()
seas_idx = (seas / seas.mean() * 100).round(1)
print("EIA 馏分油需求季节指数(1995+):")
print("  " + " ".join(f"{i}月={seas_idx[i]:.0f}" for i in seas_idx.index))
spread = float(seas_idx.max() - seas_idx.min())
print(f"  峰谷差={spread:.1f}  (峰{seas_idx.idxmax()}月, 谷{seas_idx.idxmin()}月)")

# 近5年
m5 = m[m.index.year >= 2021]
seas5 = m5.groupby(m5.index.month).mean()
seas5_idx = (seas5 / seas5.mean() * 100).round(1)

# ---------- 2. 期货价格季节性 ----------
FILES = {"HO": "ho_main_1D.csv", "ZC": "agri_zc_main_1D.csv", "ZS": "agri_zs_main_1D.csv",
         "ZW": "agri_zw_main_1D.csv", "ZL": "fut_zl_main_1D.csv", "CL": "fut_cl_main_1D.csv"}
LABEL = {"HO": "柴油(HO)", "ZC": "玉米", "ZS": "大豆", "ZW": "小麦", "ZL": "豆油", "CL": "原油(WTI)"}
seas_ret = {}
for k, fn in FILES.items():
    d = pd.read_csv(os.path.join(TEMP, fn))
    d["date"] = pd.to_datetime(d["date"].astype(str), format="%Y%m%d", errors="coerce")
    d = d.dropna(subset=["date"]).set_index("date").sort_index()
    r = np.log(pd.to_numeric(d["close"], errors="coerce")).diff() * 100
    # 月度累计收益（当月日收益求和 = 月度对数收益%）
    mo = r.resample("ME").sum()
    g = mo.groupby(mo.index.month).mean()
    seas_ret[k] = {int(i): round(float(g[i]), 2) for i in g.index}
    amp = float(g.max() - g.min())
    print(f"{k:3s} 月度平均收益年幅={amp:.2f}%  最强={g.idxmax()}月({g.max():+.2f}%) 最弱={g.idxmin()}月({g.min():+.2f}%)")

out = {
    "eia_distillate": {
        "desc": "EIA WGFUPUS2 美国馏分油产品供应 周度->月度季节指数(均值=100)",
        "index_all": {int(i): float(seas_idx[i]) for i in seas_idx.index},
        "index_5y": {int(i): float(seas5_idx[i]) for i in seas5_idx.index},
        "peak_trough": round(spread, 1),
        "window": [str(m.index.min().date()), str(m.index.max().date())],
    },
    "futures_monthly_avg_return_pct": seas_ret,
    "label": LABEL,
}
with open(os.path.join(RES, "agri_diesel_seasonality_20260910.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("DONE -> results/agri_diesel_seasonality_20260910.json")
