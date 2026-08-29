# -*- coding: utf-8 -*-
"""核对 8/28 JH 前后：10Y-2Y 与 10Y-30Y 的实际变化"""
import urllib.request, csv, io

def fred(series):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    with urllib.request.urlopen(url, timeout=30) as r:
        rows = list(csv.reader(io.StringIO(r.read().decode())))
    out = {}
    for d, v in rows[1:]:
        if not v or not d: continue
        try: out[d] = float(v)
        except ValueError: pass
    return out

d2  = fred("DGS2")
d10 = fred("DGS10")
d30 = fred("DGS30")

common = sorted(set(d2) & set(d10) & set(d30))
print("日期 | 2Y | 10Y | 30Y | 10Y-2Y(bp) | 10Y-30Y(bp)")
for d in common[-12:]:
    s102 = (d10[d]-d2[d])*100
    s1030 = (d10[d]-d30[d])*100
    print(f"{d} | {d2[d]:.2f}% | {d10[d]:.2f}% | {d30[d]:.2f}% | {s102:+5.0f} | {s1030:+5.0f}")

# 最近一次变动
if len(common) >= 2:
    d_prev, d_last = common[-2], common[-1]
    print(f"\n{common[-6][0]} -> {d_last} 累计变动:")
    for name, s in [("2Y", d2), ("10Y", d10), ("30Y", d30)]:
        print(f"  {name}: {(s[d_last]-s[common[-6]])*100:+.0f}bp")
    print(f"  10Y-2Y : {(d10[d_last]-d2[d_last]-(d10[common[-6]]-d2[common[-6]]))*100:+.0f}bp")
    print(f"  10Y-30Y: {(d10[d_last]-d30[d_last]-(d10[common[-6]]-d30[common[-6]]))*100:+.0f}bp")