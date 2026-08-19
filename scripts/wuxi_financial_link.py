#!/usr/bin/env python3
"""药明康德 vs 美国大药企 财务增长关联 + 时间窗口错配分析。

数据来源(agentic_search 检索汇总, 需以年报为准):
  药明康德: A股(CAS)口径, 2015-2017 招股书, 2018-2025 年报, 2026H1 中报
  5 大药企: GAAP 口径(10-K), 营收 + R&D(含并购/减值, 尖峰年份已标注)
输出 JSON 到 results/wuxi_financial_link.json
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results")

YEARS = list(range(2015, 2026))  # 2015..2025

# 药明康德(亿元, CAS)
wuxi_rev = {2015: 48.83, 2016: 61.16, 2017: 77.65, 2018: 96.14, 2019: 128.72,
            2020: 165.35, 2021: 229.02, 2022: 393.55, 2023: 403.41, 2024: 392.41, 2025: 454.56}
# 5 大药企合计(十亿美元, GAAP)
bp_rev = {2015: 185.06, 2016: 188.95, 2017: 193.77, 2018: 203.47, 2019: 206.69,
          2020: 225.61, 2021: 254.49, 2022: 267.36, 2023: 260.59, 2024: 282.91, 2025: 314.89}
bp_rd = {2015: 27.85, 2016: 34.06, 2017: 34.64, 2018: 39.83, 2019: 37.30,
         2020: 43.01, 2021: 44.98, 2022: 46.37, 2023: 68.33, 2024: 64.86, 2025: 58.70}

# 单只 R&D(十亿美元, 供报告拆解)
bp_rd_each = {
    "ABBV": {2015: 4.29, 2016: 4.39, 2017: 5.01, 2018: 10.33, 2019: 6.41, 2020: 6.38, 2021: 6.92, 2022: 6.51, 2023: 7.68, 2024: 12.79, 2025: 9.10},
    "MRK":  {2015: 6.70, 2016: 10.12, 2017: 10.21, 2018: 9.75, 2019: 9.87, 2020: 13.56, 2021: 12.25, 2022: 13.55, 2023: 30.53, 2024: 17.94, 2025: 15.79},
    "JNJ":  {2015: 9.05, 2016: 9.14, 2017: 10.59, 2018: 10.78, 2019: 11.36, 2020: 12.16, 2021: 14.28, 2022: 14.14, 2023: 15.09, 2024: 17.23, 2025: 14.67},
    "LLY":  {2015: 4.80, 2016: 5.31, 2017: 5.10, 2018: 5.05, 2019: 5.60, 2020: 5.98, 2021: 6.93, 2022: 7.19, 2023: 9.31, 2024: 10.99, 2025: 13.34},
    "GILD": {2015: 3.01, 2016: 5.10, 2017: 3.73, 2018: 3.92, 2019: 4.06, 2020: 4.93, 2021: 4.60, 2022: 4.98, 2023: 5.72, 2024: 5.91, 2025: 5.80},
}
bp_rd_name = {"ABBV": "艾伯维", "MRK": "默沙东", "JNJ": "强生", "LLY": "礼来", "GILD": "吉利德"}

# 药明在手订单(亿元, 持续经营口径)与增速
wuxi_backlog = {"2024末": (493.1, 47.0), "2025末": (580.0, 28.8), "2026H1末": (664.3, 25.2)}
# 合同负债(亿元)
wuxi_contract_liab = {2021: 29.86, 2022: 24.97, 2023: 19.55, 2024: 22.51, 2025: 27.09}
# 美国客户收入(亿元)与增速
wuxi_us = {"2021": (121.46, None, 53.04), "2024": (250.2, 7.7, 64.0),
           "2025": (312.5, 34.3, 72.0), "2026H1": (222.8, 61.5, 77.1)}

def growth(series, years):
    return {y: (series[y] / series[y - 1] - 1) * 100 for y in years if y - 1 in series}

def corr(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 4:
        return None
    return round(float(np.corrcoef(a, b)[0, 1]), 3)

wuxi_g = growth(wuxi_rev, YEARS)      # 2016..2025
bp_rev_g = growth(bp_rev, YEARS)
bp_rd_g = growth(bp_rd, YEARS)

# 错位相关: corr(药明增速(t), X增速(t+k)), k=-1,0,1
def lag_corr_arr(wg, xg, k):
    # 对齐: 药明 t, X t+k
    ts = sorted(set(wg) & set(xg))
    pairs = []
    for t in ts:
        tk = t + k
        if tk in xg:
            pairs.append((wg[t], xg[tk]))
    if len(pairs) < 4:
        return None, len(pairs)
    a = np.array([p[0] for p in pairs])
    b = np.array([p[1] for p in pairs])
    return round(float(np.corrcoef(a, b)[0, 1]), 3), len(pairs)

lag_out = {}
for label, xg in [("大药企营收增速", bp_rev_g), ("大药企R&D增速", bp_rd_g)]:
    for k, kn in [(0, "同步(0)"), (-1, "大药企领先1年"), (1, "药明领先1年")]:
        r, n = lag_corr_arr(wuxi_g, xg, k)
        lag_out[f"{label}|{kn}"] = {"corr": r, "n": n}

# 剔除 2022(新冠大订单)后的敏感性
wuxi_g_ex = {y: v for y, v in wuxi_g.items() if y != 2022}
lag_out_ex = {}
for label, xg in [("大药企营收增速", bp_rev_g), ("大药企R&D增速", bp_rd_g)]:
    for k, kn in [(0, "同步(0)"), (-1, "大药企领先1年"), (1, "药明领先1年")]:
        r, n = lag_corr_arr(wuxi_g_ex, xg, k)
        lag_out_ex[f"{label}|{kn}"] = {"corr": r, "n": n}

# 收入/增速序列(供图表)
series_out = {
    "years": YEARS,
    "wuxi_rev": [round(wuxi_rev[y], 1) for y in YEARS],
    "wuxi_g": [round(wuxi_g.get(y), 1) if y in wuxi_g else None for y in YEARS],
    "bp_rev": [round(bp_rev[y], 1) for y in YEARS],
    "bp_rev_g": [round(bp_rev_g.get(y), 1) if y in bp_rev_g else None for y in YEARS],
    "bp_rd": [round(bp_rd[y], 1) for y in YEARS],
    "bp_rd_g": [round(bp_rd_g.get(y), 1) if y in bp_rd_g else None for y in YEARS],
    "bp_rd_each": {k: [round(v[y], 2) for y in YEARS] for k, v in bp_rd_each.items()},
    "bp_rd_name": bp_rd_name,
    "bp_rev_each": {
        "ABBV": [22.86, 25.64, 28.22, 32.75, 33.27, 45.80, 56.20, 58.05, 54.32, 56.33, 61.16],
        "MRK": [39.50, 39.81, 40.12, 42.45, 46.59, 48.01, 48.91, 58.47, 59.87, 63.97, 64.93],
        "JNJ": [70.07, 71.89, 76.45, 81.58, 82.06, 82.57, 93.76, 95.02, 85.16, 88.82, 94.18],
        "LLY": [19.99, 21.22, 22.87, 24.56, 22.32, 24.54, 28.32, 28.54, 34.12, 45.04, 65.18],
        "GILD": [32.64, 30.39, 26.11, 22.13, 22.45, 24.69, 27.30, 27.28, 27.12, 28.75, 29.44],
    },
    "wuxi_us": wuxi_us,
    "wuxi_backlog": wuxi_backlog,
    "wuxi_contract_liab": {str(k): v for k, v in wuxi_contract_liab.items()},
}

out = {
    "meta": {
        "source": "药明康德 A股年报/招股书(CAS口径, 亿元) + 5大药企 10-K(GAAP, 十亿美元); agentic_search 检索汇总",
        "note": "大药企 R&D 为 GAAP 全口径, 含并购/减值: MRK2023(30.5B, 含Prometheus收购等~17B交易支出)、ABBV2018(10.3B, 含Stemcentrx减值5.1B)、ABBV2024(12.8B, 含emraclidine减值4.5B); JNJ2023起口径不含Kenvue",
        "fetched": "2026-08-16",
    },
    "lag": lag_out,
    "lag_ex2022": lag_out_ex,
    "series": series_out,
}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "wuxi_financial_link.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("saved: results/wuxi_financial_link.json")
print("\n=== 药明收入增速 vs 大药企营收/R&D增速 (错位相关) ===")
for k, v in lag_out.items():
    print(f"{k:24s} corr={v['corr']} (n={v['n']})")
print("\n=== 剔除2022(新冠订单)后 ===")
for k, v in lag_out_ex.items():
    print(f"{k:24s} corr={v['corr']} (n={v['n']})")
print("\n=== 增速序列 ===")
print("年 | 药明增速 | 大药企营收增速 | 大药企R&D增速")
for i, y in enumerate(YEARS):
    print(f"{y} | {series_out['wuxi_g'][i]} | {series_out['bp_rev_g'][i]} | {series_out['bp_rd_g'][i]}")
