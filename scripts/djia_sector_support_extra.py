# -*- coding: utf-8 -*-
"""补充维度：年度稳定性 / 板块拆分 / 支撑类型 / 分布分位
基于 results/djia_sector_support_events.csv + djia_sector_support.json
输出 results/djia_sector_support_extra.json
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

ev = pd.read_csv(os.path.join(RES, "djia_sector_support_events.csv"))
ev["year"] = ev["date"].str[:4]

def stats_block(g):
    out = {}
    for k in (1, 5, 10, 20):
        col = f"fwd{k}"
        v = g[col].dropna().values
        if len(v) == 0:
            out[str(k)] = None
            continue
        out[str(k)] = {
            "n": int(len(v)),
            "mean": round(float(v.mean()), 2),
            "median": round(float(np.median(v)), 2),
            "win": round(float(np.mean(v > 0)) * 100, 1),
            "p10": round(float(np.percentile(v, 10)), 2),
            "p90": round(float(np.percentile(v, 90)), 2),
        }
    out["n"] = int(len(g))
    return out

result = {}

# 1) 年度稳定性（T+5 / T+10 胜率与均值）
year_stats = {y: stats_block(g) for y, g in ev.groupby("year")}
result["by_year"] = year_stats

# 2) 板块拆分
sector_stats = {s: stats_block(g) for s, g in ev.groupby("sector")}
result["by_sector"] = sector_stats

# 3) 支撑质量分桶（新口径：分形+ATR聚类；按触碰次数 / 支撑年龄）
import re
def n_touches(row):
    m = re.search(r"(\d+)\s*触", str(row.get("support_kinds", "")))
    return int(m.group(1)) if m else None
ev["n_touch"] = ev.apply(n_touches, axis=1)
ev["touch_bucket"] = pd.cut(ev["n_touch"], bins=[0, 2, 4, 99], labels=["2触", "3-4触", ">=5触"]).astype(str)
result["by_touches"] = {b: stats_block(g) for b, g in ev.groupby("touch_bucket")}
ev["age_bucket_s"] = pd.cut(ev["support_age"], bins=[0, 90, 9999], labels=["42-90日", ">90日"]).astype(str)
result["by_support_age"] = {b: stats_block(g) for b, g in ev.groupby("age_bucket_s")}

# 4) 结局分类按板块（击穿率）
result["break_rate_by_sector"] = {
    s: round(float((g["support_broken_day"].notna()).mean()) * 100, 1)
    for s, g in ev.groupby("sector")
}

# 5) 线龄分桶（趋势线年龄 42-60 / 60-90 / >90）
def line_age_bucket(a):
    if a is None or pd.isna(a):
        return "unknown"
    if a <= 60:
        return "42-60日"
    if a <= 90:
        return "60-90日"
    return ">90日"
ev["age_bucket"] = ev["line_age"].apply(line_age_bucket)
result["by_line_age"] = {b: stats_block(g) for b, g in ev.groupby("age_bucket")}

# 6) R2 质量分桶
def r2_bucket(r):
    if r is None or pd.isna(r):
        return "2点/未知"
    return "3点R2>=0.7" if r >= 0.7 else "弱"
ev["r2_bucket"] = ev["line_r2"].apply(r2_bucket)
result["by_line_r2"] = {b: stats_block(g) for b, g in ev.groupby("r2_bucket")}

# 7) 个股当日缩量 vs 放量
ev["stk_vol_bucket"] = pd.cut(ev["stk_vol_ratio"], bins=[0, 0.8, 1.5, 99], labels=["缩量<0.8", "平量0.8-1.5", "放量>=1.5"]).astype(str)
result["by_stk_vol"] = {b: stats_block(g) for b, g in ev.groupby("stk_vol_bucket")}

def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(x) for x in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return round(float(o), 3)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)):
        return None
    return o

result = clean(result)
with open(os.path.join(RES, "djia_sector_support_extra.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, allow_nan=False)

# 控制台只打关键
print("=== by_year (T+10 胜率/均值) ===")
for y in sorted(year_stats):
    b = year_stats[y].get("10") or {}
    print(f"  {y}: n={year_stats[y]['n']} T10 均{b.get('mean')}% 胜率{b.get('win')}")
print("=== by_sector ===")
for s in sorted(sector_stats):
    b10 = sector_stats[s].get("10") or {}
    b5 = sector_stats[s].get("5") or {}
    print(f"  {s}: n={sector_stats[s]['n']} T5 胜率{b5.get('win')} T10 均{b10.get('mean')}% 胜率{b10.get('win')} 击穿率{result['break_rate_by_sector'].get(s)}%")
print("=== by_touches / by_support_age ===")
for k in ("2触", "3-4触", ">=5触"):
    b = result["by_touches"].get(k, {}).get("10") or {}
    n = result["by_touches"].get(k, {}).get("n", 0)
    print(f"  {k}: n={n} T10 均{b.get('mean')}% 胜率{b.get('win')}")
for k in ("42-90日", ">90日"):
    b = result["by_support_age"].get(k, {}).get("10") or {}
    n = result["by_support_age"].get(k, {}).get("n", 0)
    print(f"  支撑龄{k}: n={n} T10 均{b.get('mean')}% 胜率{b.get('win')}")
print("written: results/djia_sector_support_extra.json")
