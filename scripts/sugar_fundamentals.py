# -*- coding: utf-8 -*-
"""
白糖（Sugar, Centrifugal, PSD code 612000）全球供需 / 库消比 —— 2026-09-12  【口径修正版 v2】

口径审计结论（v1 → v2 修正点）
  [修正1] 欧盟拼接：PSD 的欧盟是三个互不重叠的聚合体，必须按年份拼接：
            EU-15   1960-2003      （15 个老成员国）
            EU-25   2004-2005      （2004 东扩）
            European Union 2006-2026
          且 2004 年入盟国（波兰/捷克/匈牙利…）在 <=2003 是独立行、2004 起并入 EU-25。
          v1 简单剔除欧盟成员国 → 2004 年前整个欧盟产量被漏掉（1960 低估约 35%）。
  [修正2] 历史实体（USSR 1960-1988 / Former Yugoslavia 1960-1991 / Former Czechoslovakia
          1960-1988 / GDR 1960-1973）与后继国（Russia 1989- 等）**不重叠**，必须计入。
  [修正3] 德国：Federal Republic 1960-1989 + GDR 1960-1973 = 全德；1990+ 已在 EU 聚合内。
  [声明]  PSD alldata 每个 (国别,年,属性) 只有 1 条记录（实测 max=1）→ **只有最新修订值，
          无法重建"当年公布值"的同期口径**。故本表库消比历史百分位 = 终稿口径，
          与"当时市场上的认知"存在系统性差异（当年预测普遍偏松）。

输出 results/sugar_fundamentals.json / data/sugar/sugar_global_sd.csv
"""
import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "sugar", "raw", "psd", "psd_alldata.csv")
OUT_JSON = os.path.join(BASE, "results", "sugar_fundamentals.json")
OUT_CSV = os.path.join(BASE, "data", "sugar", "sugar_global_sd.csv")

# --- 聚合体（必须整体剔除，再按年份条件加回）---
AGG = {"EU-15", "EU-25", "European Union",
       "Union of Soviet Socialist Repu", "Former Yugoslavia", "Former Czechoslovakia",
       "German Democratic Republic", "Yemen (Aden)", "Yemen (Sanaa)", "Yemen",
       "Gilbert and Ellice Islands", "Vanuatu/New Hebrides", "Fr.Ter.Africa-Issas",
       "Reunion", "French West Indies", "Guadeloupe", "Martinique",
       "French Polynesia", "New Caledonia"}
# --- 欧盟成员国（2004 起并入 EU 聚合，须剔除；<=2003 时按年份加回）---
MEMBERS = {"Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark",
           "Estonia", "Finland", "France", "Germany, Federal Republic of", "Greece", "Hungary",
           "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
           "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"}

df = pd.read_csv(SRC, low_memory=False)
s = df[df.Commodity_Code == 612000].copy()
s["Value"] = pd.to_numeric(s["Value"], errors="coerce")
piv = s.pivot_table(index=["Country_Name", "Market_Year"], columns="Attribute_Description",
                    values="Value", aggfunc="first").reset_index()
COLS = ["Production", "Human Dom. Consumption", "Total Disappearance", "Ending Stocks",
        "Total Supply", "Imports", "Exports"]

base = piv[~piv.Country_Name.isin(AGG | MEMBERS)]
g = base.groupby("Market_Year")[COLS].sum(min_count=1)

pi = piv.set_index(["Country_Name", "Market_Year"])


def get(name, y, col):
    """取某国别某年的某属性值，缺失返回 nan"""
    try:
        v = pi.loc[(name, y), col]
        if isinstance(v, pd.Series):
            v = v.iloc[0]
        return np.nan if pd.isna(v) else float(v)
    except KeyError:
        return np.nan


def sget(names, y, col):
    """多个国别求和（忽略缺失）"""
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
        # --- 欧盟三口径按年份拼接（互不重叠，见文件头说明）---
        if y <= 2003:
            part = sget(["EU-15"], y, col) + sget(list(MEMBERS), y, col)
        elif y <= 2005:
            part = sget(["EU-25"], y, col)
        else:
            part = sget(["European Union"], y, col)
        v += 0.0 if pd.isna(part) else part
        # --- 历史实体（与后继国不重叠）---
        if 1960 <= y <= 1988:
            v += sget(["Union of Soviet Socialist Repu"], y, col)
            v += sget(["Former Czechoslovakia"], y, col)
        if 1960 <= y <= 1991:
            v += sget(["Former Yugoslavia"], y, col)
        if 1960 <= y <= 1973:
            v += sget(["German Democratic Republic"], y, col)
        adj.append(v)
    g[col] = adj

g["StockToUse"] = g["Ending Stocks"] / g["Total Disappearance"] * 100
g["ProdMinusUse"] = g["Production"] - g["Total Disappearance"]
g = g.loc[1960:]

# ---------- 校验：与公认量级对照 ----------
BENCH = {1960: 53000, 1970: 70000, 1980: 88500, 1990: 114000, 2000: 130000,
         2010: 162000, 2020: 180000, 2026: 185000}
print("=== 校验：全球产量 vs 公认量级（千吨）===")
for y, ref in BENCH.items():
    if y in g.index:
        got = g.loc[y, "Production"]
        print(f"  MY{y}: 本表 {got:>8.0f}   参考 {ref:>8.0f}   偏差 {(got/ref-1)*100:+.1f}%")

print("\n=== 全球糖供需（千吨）===")
print(g.loc[2010:, ["Production", "Total Disappearance", "Ending Stocks", "StockToUse", "ProdMinusUse"]].round(1).to_string())

cur = int(g.index.max())
sur = g.loc[cur, "StockToUse"]
hist = g.loc[1960:cur, "StockToUse"]
print(f"\nMY{cur} 库消比 {sur:.1f}%  1960 年以来分位 {(hist<sur).mean()*100:.0f}%")
print(f"  区间 {hist.min():.1f}%({hist.idxmin()}) ~ {hist.max():.1f}%({hist.idxmax()})  中位 {hist.median():.1f}%")
print(f"  近10年均值 {g.loc[cur-10:cur-1,'StockToUse'].mean():.1f}% | 近5年均值 {g.loc[cur-5:cur-1,'StockToUse'].mean():.1f}%")
print("\n=== 近 20 年库消比 ===")
print(g.loc[2007:cur, "StockToUse"].round(1).to_string())

g.round(1).to_csv(OUT_CSV)

# ---------- 分国别 ----------
KEYS = ["Brazil", "India", "Thailand", "China", "European Union", "United States",
        "Mexico", "Australia", "Pakistan", "Russia", "Guatemala", "South Africa"]
tbl = {}
for c in KEYS:
    sub = piv[piv.Country_Name == c].set_index("Market_Year")
    tbl[c] = {k: {str(y): (None if pd.isna(sub.loc[y, k]) else round(float(sub.loc[y, k]), 1))
                  for y in sub.index if y >= 2015}
              for k in ["Production", "Total Disappearance", "Ending Stocks", "Exports", "Imports"]
              if k in sub.columns}

out = {
    "meta": {
        "source": "USDA FAS PSD psd_alldata.csv (snapshot 2026-09-11)",
        "market_year": "Market_Year Y == season Y/Y+1 (Oct-Sep)",
        "eu_splice": "EU-15 1960-2003 | EU-25 2004-2005 | European Union 2006-2026",
        "vintage_caveat": "PSD 只保留最新修订值 -> 本表为终稿口径，非当年公布值",
        "sugar_revision_cycle": "FAS 'Sugar: World Markets and Trade' 仅 5 月/11 月更新 -> MY2026 值 = 2026-05 版",
    },
    "global": {str(y): {k: (None if pd.isna(g.loc[y, k]) else round(float(g.loc[y, k]), 1))
                        for k in ["Production", "Human Dom. Consumption", "Total Disappearance",
                                  "Ending Stocks", "StockToUse", "ProdMinusUse", "Imports", "Exports"]}
               for y in g.index if y >= 1990},
    "validation": {str(y): round(float(g.loc[y, "Production"]), 0) for y in BENCH if y in g.index},
    "stock_to_use_stats": {
        "current": round(float(sur), 2),
        "percentile_since_1960": round(float((hist < sur).mean() * 100), 1),
        "min": round(float(hist.min()), 1), "min_year": int(hist.idxmin()),
        "max": round(float(hist.max()), 1), "max_year": int(hist.idxmax()),
        "median": round(float(hist.median()), 1),
        "avg_10y": round(float(g.loc[cur-10:cur-1, "StockToUse"].mean()), 1),
        "avg_5y": round(float(g.loc[cur-5:cur-1, "StockToUse"].mean()), 1),
    },
    "countries": tbl,
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nwrote", OUT_JSON, "/", OUT_CSV)
