# -*- coding: utf-8 -*-
"""
棉花（Cotton, PSD code 2631000）全球供需 / 库消比 —— 2026-09-12

与白糖（sugar_fundamentals.py）同框架，但棉花有三处口径差异：
  [差异1] 单位 = 1000 480-lb Bales（1 bale = 217.724 kg = 0.217724 MT），非 1000 MT。
  [差异2] 库消比分母 = Domestic Use + Exports（不含 Loss），已反推校准到 PSD 官方
          Stocks-to-Use 属性（美国 2020/21/22: 18450/16600/14500 精确命中）。
          糖用 Total Disappearance（含损耗），棉花官方口径不含 Loss。
  [差异3] 市场年度 = Aug-Jul（8月1日~次年7月31日），非糖的 Oct-Sep。MY Y == 榨季 Y/Y+1。
  [差异4] 棉花 PSD 逐月更新（Month 1-12，因 WASDE 每月发布棉花），糖只 5/11/12 月。

欧盟/历史实体处理与糖相同（USSR 对棉花尤其关键：中亚产棉国 1960-88 全球第二）。
输出 results/cotton_fundamentals.json / data/cotton/cotton_global_sd.csv
"""
import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "sugar", "raw", "psd", "psd_alldata.csv")
OUT_JSON = os.path.join(BASE, "results", "cotton_fundamentals.json")
OUT_CSV = os.path.join(BASE, "data", "cotton", "cotton_global_sd.csv")

BALE_T = 480 * 0.45359237 / 1000  # 0.217724 kg -> MT

AGG = {"EU-15", "EU-25", "European Union",
       "Union of Soviet Socialist Repu", "Former Yugoslavia", "Former Czechoslovakia",
       "German Democratic Republic", "Yemen (Aden)", "Yemen (Sanaa)", "Yemen",
       "Gilbert and Ellice Islands", "Vanuatu/New Hebrides", "Fr.Ter.Africa-Issas",
       "Reunion", "French West Indies", "Guadeloupe", "Martinique",
       "French Polynesia", "New Caledonia"}
MEMBERS = {"Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark",
           "Estonia", "Finland", "France", "Germany, Federal Republic of", "Greece", "Hungary",
           "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
           "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"}

df = pd.read_csv(SRC, low_memory=False)
s = df[df.Commodity_Code == 2631000].copy()
s["Value"] = pd.to_numeric(s["Value"], errors="coerce")
piv = s.pivot_table(index=["Country_Name", "Market_Year"], columns="Attribute_Description",
                    values="Value", aggfunc="first").reset_index()
COLS = ["Production", "Domestic Use", "Total Distribution", "Ending Stocks",
        "Total Supply", "Imports", "Exports", "Beginning Stocks"]

base = piv[~piv.Country_Name.isin(AGG | MEMBERS)]
g = base.groupby("Market_Year")[COLS].sum(min_count=1)

pi = piv.set_index(["Country_Name", "Market_Year"])


def get(name, y, col):
    try:
        v = pi.loc[(name, y), col]
        if isinstance(v, pd.Series):
            v = v.iloc[0]
        return np.nan if pd.isna(v) else float(v)
    except KeyError:
        return np.nan


def sget(names, y, col):
    vals = [get(n, y, col) for n in names]
    vals = [v for v in vals if not pd.isna(v)]
    return float(sum(vals)) if vals else np.nan


for col in COLS:
    adj = []
    for y in g.index:
        y = int(y)
        v = g.loc[y, col]
        if pd.isna(v):
            adj.append(np.nan)
            continue
        if y <= 2003:
            part = sget(["EU-15"], y, col) + sget(list(MEMBERS), y, col)
        elif y <= 2005:
            part = sget(["EU-25"], y, col)
        else:
            part = sget(["European Union"], y, col)
        v += 0.0 if pd.isna(part) else part
        if 1960 <= y <= 1988:
            v += sget(["Union of Soviet Socialist Repu"], y, col)
            v += sget(["Former Czechoslovakia"], y, col)
        if 1960 <= y <= 1991:
            v += sget(["Former Yugoslavia"], y, col)
        if 1960 <= y <= 1973:
            v += sget(["German Democratic Republic"], y, col)
        adj.append(v)
    g[col] = adj

# 库消比主口径 = Ending Stocks / Domestic Use（消费口径，不含出口，对齐糖的 Total Disappearance）
# 参考口径 = Ending Stocks / (Domestic Use + Exports)（单国"总使用"口径，USDA 单国 stocks-to-use）
g["StockToUse"] = g["Ending Stocks"] / g["Domestic Use"] * 100
g["StockToUse_total"] = g["Ending Stocks"] / (g["Domestic Use"] + g["Exports"]) * 100
g["ProdMinusUse"] = g["Production"] - g["Domestic Use"]
g = g.loc[1960:]

# ---------- 校验：全球产量 vs 公认量级（千 480-lb bales） ----------
BENCH = {1960: 46000, 1970: 52000, 1980: 64000, 1990: 86000, 2000: 88000,
         2010: 115000, 2020: 116000, 2026: 118000}
print("=== 校验：全球棉花产量 vs 公认量级（千 480-lb bales）===")
for y, ref in BENCH.items():
    if y in g.index:
        got = g.loc[y, "Production"]
        print(f"  MY{y}: 本表 {got:>9.0f}   参考 {ref:>9.0f}   偏差 {(got/ref-1)*100:+.1f}%")

print("\n=== 全球棉花供需（千 480-lb bales）===")
print(g.loc[2010:, ["Production", "Domestic Use", "Exports", "Ending Stocks", "StockToUse", "ProdMinusUse"]].round(1).to_string())

cur = int(g.index.max())
sur = g.loc[cur, "StockToUse"]
hist = g.loc[1960:cur, "StockToUse"]
print(f"\nMY{cur} 库消比(消费口径) {sur:.1f}%  1960 年以来分位 {(hist<sur).mean()*100:.0f}%")
print(f"  区间 {hist.min():.1f}%({hist.idxmin()}) ~ {hist.max():.1f}%({hist.idxmax()})  中位 {hist.median():.1f}%")
print(f"  近10年均值 {g.loc[cur-10:cur-1,'StockToUse'].mean():.1f}% | 近5年均值 {g.loc[cur-5:cur-1,'StockToUse'].mean():.1f}%")
print(f"  本世纪最低 {g.loc[2000:, 'StockToUse'].idxmin()} 年 {g.loc[2000:, 'StockToUse'].min():.1f}%")
print(f"  参考(总使用口径) {g.loc[cur, 'StockToUse_total']:.1f}%")
print("\n=== 近 20 年库消比 ===")
print(g.loc[2007:cur, "StockToUse"].round(1).to_string())

g.round(1).to_csv(OUT_CSV)

# ---------- 分国别 ----------
KEYS = ["China", "India", "United States", "Brazil", "Pakistan", "Australia",
        "Turkey", "Uzbekistan", "European Union", "Greece", "Mexico", "Mali",
        "Benin", "Burkina", "Turkmenistan", "Tajikistan", "Egypt", "Vietnam", "Bangladesh"]
tbl = {}
for c in KEYS:
    sub = piv[piv.Country_Name == c].set_index("Market_Year")
    tbl[c] = {k: {str(y): (None if pd.isna(sub.loc[y, k]) else round(float(sub.loc[y, k]), 1))
                  for y in sub.index if y >= 2015}
              for k in ["Production", "Domestic Use", "Ending Stocks", "Exports", "Imports"]
              if k in sub.columns}

# 全球库存/消费换算为千吨（供报告展示）
def kt(bales):
    return None if pd.isna(bales) else round(float(bales) * BALE_T, 0)

out = {
    "meta": {
        "source": "USDA FAS PSD psd_alldata.csv (snapshot 2026-09-11)",
        "market_year": "Market_Year Y == season Y/Y+1 (Aug-Jul)",
        "unit": "1000 480-lb Bales (1 bale = 217.724 kg)",
        "stocks_to_use_denom": "主口径 Ending Stocks / Domestic Use（消费，不含出口，对齐糖 Total Disappearance）；参考口径 Ending Stocks/(Domestic Use+Exports)",
        "eu_splice": "EU-15 1960-2003 | EU-25 2004-2005 | European Union 2006-2026",
        "vintage_caveat": "PSD 只保留最新修订值 -> 本表为终稿口径；棉花 WASDE 逐月更新",
    },
    "global": {str(y): {k: (None if pd.isna(g.loc[y, k]) else round(float(g.loc[y, k]), 1))
                        for k in ["Production", "Domestic Use", "Total Distribution",
                                  "Ending Stocks", "StockToUse", "StockToUse_total",
                                  "ProdMinusUse", "Imports", "Exports"]}
               for y in g.index if y >= 1990},
    "global_kt": {str(y): {"stocks_kt": kt(g.loc[y, "Ending Stocks"]),
                           "production_kt": kt(g.loc[y, "Production"]),
                           "use_kt": kt(g.loc[y, "Domestic Use"])}
                  for y in g.index if y >= 1990},
    "validation": {str(y): round(float(g.loc[y, "Production"]), 0) for y in BENCH if y in g.index},
    "stock_to_use_stats": {
        "current": round(float(sur), 2),
        "percentile_since_1960": round(float((hist < sur).mean() * 100), 1),
        "min": round(float(hist.min()), 1), "min_year": int(hist.idxmin()),
        "max": round(float(hist.max()), 1), "max_year": int(hist.idxmax()),
        "median": round(float(hist.median()), 1),
        "min_since_2000": round(float(g.loc[2000:, "StockToUse"].min()), 1),
        "min_year_since_2000": int(g.loc[2000:, "StockToUse"].idxmin()),
        "avg_10y": round(float(g.loc[cur-10:cur-1, "StockToUse"].mean()), 1),
        "avg_5y": round(float(g.loc[cur-5:cur-1, "StockToUse"].mean()), 1),
    },
    "countries": tbl,
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nwrote", OUT_JSON, "/", OUT_CSV)
