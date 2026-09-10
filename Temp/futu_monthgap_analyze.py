# -*- coding: utf-8 -*-
"""近6个月 WTI 合约：月间隔 +1/+2/+3 价差强弱分析"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\Administrator\Desktop\stock"
d = json.load(open(BASE + r"\results\futu_all_contracts_raw.json", encoding="utf-8"))

codes = ["US.CL2610", "US.CL2611", "US.CL2612", "US.CL2701", "US.CL2702", "US.CL2703"]
lab = {"US.CL2610": "OCT26", "US.CL2611": "NOV26", "US.CL2612": "DEC26",
       "US.CL2701": "JAN27", "US.CL2702": "FEB27", "US.CL2703": "MAR27"}
K = {c: d["kline"][c] for c in codes}
n = min(len(v) for v in K.values())
dates = [str(x["date"]) for x in K["US.CL2610"][-n:]]
# 校验日期对齐
for c in codes:
    dd = [str(x["date"]) for x in K[c][-n:]]
    assert dd == dates, f"date mismatch {c}"
px = {c: [K[c][-n + i]["close"] for i in range(n)] for c in codes}
oi = {c: K[c][-1].get("open_interest") for c in codes}
vol = {c: K[c][-1].get("volume") for c in codes}

print("=== 最新价与流动性 ===")
print(f"{'合约':<10}{'最新':>9}{'持仓量':>12}{'成交量':>10}")
for c in codes:
    print(f"{lab[c]:<10}{px[c][-1]:>9.2f}{(oi[c] or 0):>12,.0f}{(vol[c] or 0):>10,.0f}")

def stats(series):
    v = series[-1]
    d5 = v - series[-6]
    d20 = v - series[-21]
    d60 = v - series[-61]
    pct = sum(1 for x in series if x <= v) / len(series) * 100
    mu = sum(series) / len(series)
    sd = (sum((x - mu) ** 2 for x in series) / len(series)) ** 0.5
    z = (v - mu) / sd if sd else 0
    return v, d5, d20, d60, pct, z, min(series), max(series)

rows = []
for k in (1, 2, 3):
    for i in range(len(codes) - k):
        a, b = codes[i], codes[i + k]
        s = [px[a][j] - px[b][j] for j in range(n)]
        v, d5, d20, d60, pct, z, lo, hi = stats(s)
        rows.append({"k": k, "i": i, "pair": f"{lab[a][:3]}-{lab[b][:3]}",
                     "near": lab[a], "far": lab[b], "level": round(v, 2),
                     "per_m": round(v / k, 2), "d5": round(d5, 2), "d20": round(d20, 2),
                     "d60": round(d60, 2), "pct": round(pct), "z": round(z, 2),
                     "lo": round(lo, 2), "hi": round(hi, 2)})

for k in (1, 2, 3):
    grp = [r for r in rows if r["k"] == k]
    print(f"\n=== 月间隔 +{k}（{len(grp)} 条）===")
    print(f"{'组合':<10}{'水平$':>8}{'$/月':>8}{'5日Δ':>7}{'20日Δ':>8}{'60日Δ':>8}{'分位':>7}{'z':>7}")
    for r in grp:
        print(f"{r['pair']:<10}{r['level']:>8.2f}{r['per_m']:>8.2f}{r['d5']:>+7.2f}{r['d20']:>+8.2f}{r['d60']:>+8.2f}{r['pct']:>6.0f}%{r['z']:>7.2f}")

print("\n=== 三条带横向对比（单位化 $/月）===")
print(f"{'间隔':<8}{'平均$/月':>10}{'最大$/月':>10}{'最强组合':>12}{'平均20日Δ/月':>14}")
for k in (1, 2, 3):
    grp = [r for r in rows if r["k"] == k]
    avg = sum(r["per_m"] for r in grp) / len(grp)
    mx = max(grp, key=lambda r: r["per_m"])
    a20 = sum(r["d20"] / k for r in grp) / len(grp)
    print(f"+{k:<7}{avg:>10.2f}{mx['per_m']:>10.2f}{mx['pair']:>12}{a20:>14.2f}")

print("\n=== 全表排序：按 20 日扩张（$/月归一）===")
for r in sorted(rows, key=lambda r: -r["d20"] / r["k"]):
    print(f"  +{r['k']} {r['pair']:<10} 水平 {r['level']:>6.2f} (${r['per_m']:>5.2f}/月)  20日Δ {r['d20']:>+6.2f}  分位 {r['pct']}%  z {r['z']:>5.2f}")

print("\n=== 全表排序：按 20 日绝对扩张 ===")
for r in sorted(rows, key=lambda r: -r["d20"]):
    print(f"  +{r['k']} {r['pair']:<10} 20日Δ {r['d20']:>+6.2f}  水平 {r['level']:>6.2f}  分位 {r['pct']}%")

json.dump({"dates": dates[-60:],
           "px": {lab[c]: [round(px[c][-60 + i], 2) for i in range(60)] for c in codes},
           "rows": rows}, open(BASE + r"\Temp\monthgap.json", "w", encoding="utf-8"), ensure_ascii=False)
print("\nsaved Temp/monthgap.json")
