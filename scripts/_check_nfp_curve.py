# -*- coding: utf-8 -*-
"""核对：①非农连续负月份历史先例 ②10Y-30Y 当前水平与历史分位"""
import urllib.request, csv, io, json
from collections import defaultdict

def fred(series):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    with urllib.request.urlopen(url, timeout=30) as r:
        rows = list(csv.reader(io.StringIO(r.read().decode())))
    out = {}
    for d, v in rows[1:]:
        if not v or not d: continue
        try:
            out[d] = float(v)
        except ValueError:
            pass
    return out

pay = fred("PAYEMS")          # 非农就业总人数(千人)
d10 = fred("DGS10")           # 10Y
d30 = fred("DGS30")           # 30Y

# ---- 1) 非农环比 + 连续负月份 ----
keys = sorted(pay)
diffs = []
for i in range(1, len(keys)):
    prev, cur = keys[i-1], keys[i]
    diff = pay[cur] - pay[prev]
    diffs.append((cur, diff))

print("== 最近8个月非农环比(千人) ==")
for cur, d in diffs[-8:]:
    print(f"  {cur}: {int(d):+d}")

neg_streaks = []
cur_streak = []
for cur, d in diffs:
    if d < 0:
        cur_streak.append((cur, int(d)))
    else:
        if len(cur_streak) >= 2:
            neg_streaks.append(cur_streak)
        cur_streak = []
if len(cur_streak) >= 2:
    neg_streaks.append(cur_streak)

print("\n== 1970以来 连续>=2个月非农为负的时段 ==")
for s in neg_streaks:
    rng = f"{s[0][0]} 至 {s[-1][0]}"
    print(f"  {rng}: " + ", ".join(f"{m}({d:+d})" for m, d in s))

# ---- 2) 10y30y ----
common = sorted(set(d10) & set(d30))
spread = [(d, (d10[d] - d30[d]) * 100) for d in common if d >= "2020-01-01"]  # bp, 10Y-30Y
cur_d = spread[-1][0]
vals = [s for _, s in spread]
mean = sum(vals)/len(vals)
pct = sum(1 for s in vals if s <= spread[-1][1])/len(vals)*100
lo = min(spread, key=lambda x: x[1])
hi = max(spread, key=lambda x: x[1])
print(f"\n== 10Y-30Y 利差(bp, =10Y-30Y) 2020以来 ==")
print(f"  最新({cur_d}): {spread[-1][1]:+.0f}bp | 10Y={d10[cur_d]}% 30Y={d30[cur_d]}%")
print(f"  均值 {mean:+.0f}bp | 区间 [{lo[1]:+.0f}bp @{lo[0]}, {hi[1]:+.0f}bp @{hi[0]}] | 当前分位 {pct:.0f}%")
print(f"  近30个交易日 10y30y(bp):")
for d, s in spread[-30:]:
    print(f"    {d}: {s:+.0f}bp")