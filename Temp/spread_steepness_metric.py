# -*- coding: utf-8 -*-
"""月差陡峭度：多口径对比 + 历史分位（回答"全曲线最陡"如何定义）"""
import csv, math, json

DAILY = "data/cl_contracts/spread/cl_spread_daily.csv"
slots = ["CL2610", "CL2611", "CL2612", "CL2701", "CL2702", "CL2703"]
names = ["10月", "11月", "12月", "1月", "2月", "3月"]
# 最后交易日（富途 reference_listed）
last_trade = ["2026-09-22", "2026-10-20", "2026-11-20", "2026-12-21", "2027-01-20", "2027-02-22"]

from datetime import date
def d(s):
    y, m, dd = map(int, s.split("-")); return date(y, m, dd)
gaps = [(d(last_trade[i + 1]) - d(last_trade[i])).days for i in range(5)]

rows = list(csv.DictReader(open(DAILY, encoding="utf-8")))
cur = rows[-1]
px = [float(cur[s]) for s in slots]

print("== 数据日:", cur["ts"], " 收盘:", px)
print("== 相邻段间隔天数:", gaps, " 合计", sum(gaps))
print()

res = []
avg = sum(px) / 6
for i in range(5):
    pn, pf = px[i], px[i + 1]
    abs_ = pn - pf
    pct_near = abs_ / pn * 100          # 占近腿
    logd = math.log(pn / pf) / gaps[i] * 365 * 100   # 日归一化年化对数斜率
    res.append((f"{names[i]}->{names[i+1]}", abs_, pct_near, logd, gaps[i]))

print(f"{'段':<12}{'绝对$':>8}{'占近腿%':>10}{'年化对数斜率%':>14}{'间隔天':>7}")
for r in res:
    print(f"{r[0]:<12}{r[1]:>8.2f}{r[2]:>10.3f}{r[3]:>14.2f}{r[4]:>7}")

for k, lab in [(1, "绝对$"), (2, "占近腿%"), (3, "年化对数斜率%")]:
    best = max(res, key=lambda x: x[k])
    print(f"\n按[{lab}]排名第1: {best[0]} = {best[k]:.3f}")

# 历史分位（128 日）：对每段取当日值在过去128日的分位
print("\n== 各段历史分位（近128交易日）==")
cols = ["abs1_OCT26_NOV26", "abs1_NOV26_DEC26", "abs1_DEC26_JAN27",
        "abs1_JAN27_FEB27", "abs1_FEB27_MAR27"]
for i, c in enumerate(cols):
    series = [float(r[c]) for r in rows if r[c] not in ("", "nan")]
    v = float(cur[c])
    rank = sum(1 for x in series if x <= v) / len(series) * 100
    mx = max(series)
    print(f"{res[i][0]:<12} 现值{v:>6.2f}  历史max{mx:>6.2f}  {'★新高' if abs(v-mx)<1e-9 else '':<5} 分位{rank:>6.1f}%")

# 曲线整体形状：对数价格 vs 累计天数
print("\n== 对数价格 vs 累计天数（曲线凸性检验）==")
t = 0
print(f"{'合约':<6}{'累计天数':>9}{'ln(P)':>10}")
print(f"{names[0]:<6}{0:>9}{math.log(px[0]):>10.4f}")
for i in range(5):
    t += gaps[i]
    print(f"{names[i+1]:<6}{t:>9}{math.log(px[i+1]):>10.4f}")
