# -*- coding: utf-8 -*-
"""WTI 近6月曲线形状演化：是否前端集中 + 后方塌缩"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\Administrator\Desktop\stock"
d = json.load(open(BASE + r"\results\futu_all_contracts_raw.json", encoding="utf-8"))
codes = ["US.CL2610", "US.CL2611", "US.CL2612", "US.CL2701", "US.CL2702", "US.CL2703"]
lab = ["OCT-NOV", "NOV-DEC", "DEC-JAN", "JAN-FEB", "FEB-MAR"]
K = {c: d["kline"][c] for c in codes}
n = min(len(v) for v in K.values())
dates = [str(x["date"]) for x in K["US.CL2610"][-n:]]
px = {c: [K[c][-n + i]["close"] for i in range(n)] for c in codes}

# 每日 5 段斜率 + 结构指标
rows = []
for t in range(n):
    p = [px[c][t] for c in codes]
    segs = [p[i] - p[i + 1] for i in range(5)]
    total = p[0] - p[5]
    if total <= 0:
        rows.append({"t": t, "date": dates[t], "contango": True, "segs": segs, "total": total})
        continue
    peak = segs.index(max(segs))
    front_share = (segs[0] + segs[1]) / total * 100
    mid_share = (segs[1] + segs[2]) / total * 100
    back_share = segs[4] / total * 100
    ratio = max(segs) / (sum(segs) / 5)
    rows.append({"t": t, "date": dates[t], "segs": [round(x, 2) for x in segs],
                 "total": round(total, 2), "peak": peak, "front_share": round(front_share, 1),
                 "mid_share": round(mid_share, 1), "back_share": round(back_share, 1),
                 "ratio": round(ratio, 2)})

valid = [r for r in rows if not r.get("contango")]
print(f"总交易日 {n}，其中 contango/负总价差 {n - len(valid)} 天；backwardation {len(valid)} 天")
print(f"backwardation 起始日: {valid[0]['date'] if valid else '-'}\n")

print("=== 关键时点结构快照（5段斜率 / 占比）===")
print(f"{'日期':<10}{'总差':>7}   " + "".join(f"{l:>10}" for l in lab) + f"{'峰位':>6}{'前2段%':>8}{'峰/均':>7}")
for t in [len(valid) - 61, len(valid) - 21, len(valid) - 6, len(valid) - 1]:
    if t < 0:
        continue
    r = valid[t]
    tot = r["total"]
    cells = "".join(f"{s:>6.2f}({s/tot*100:>3.0f}%)" for s in r["segs"])
    print(f"{r['date']:<10}{tot:>7.2f}   {cells}{lab[r['peak']][:3]:>6}{r['front_share']:>8.1f}{r['ratio']:>7.2f}")

print("\n=== 峰值位置分布（backwardation 期间）===")
from collections import Counter
cnt = Counter(r["peak"] for r in valid)
for i, l in enumerate(lab):
    print(f"  峰值在 {l}: {cnt.get(i,0):>3} 天 ({cnt.get(i,0)/len(valid)*100:>4.0f}%)")

print("\n=== 前端集中度演化（前2段占总价差%）===")
for t in range(0, len(valid), max(1, len(valid) // 12)):
    r = valid[t]
    bar = "█" * int(r["front_share"] / 2)
    print(f"  {r['date']}  均值基准40%  实际 {r['front_share']:>5.1f}%  {bar}")
r = valid[-1]
print(f"  {r['date']}  均值基准40%  实际 {r['front_share']:>5.1f}%  " + "█" * int(r["front_share"] / 2))

# 剔 OCT 后的形状
print("\n=== 剔除 OCT 后（NOV-MAR 4段）===")
p = [px[c][-1] for c in codes]
sub = [p[i] - p[i + 1] for i in range(1, 5)]
tot = sum(sub)
print(f"{'段':<10}{'斜率':>8}{'占比':>8}{'基准25%':>10}{'偏离':>8}")
for l, s in zip(lab[1:], sub):
    print(f"{l:<10}{s:>8.2f}{s/tot*100:>7.1f}%{25.0:>10.1f}{s/tot*100-25:>+8.1f}pp")
print(f"合计 {tot:.2f}；最大/最小 = {max(sub)/min(sub):.2f}x")

out = {"dates": [r["date"] for r in valid],
       "front_share": [r["front_share"] for r in valid],
       "peak": [r["peak"] for r in valid],
       "segs_now": valid[-1]["segs"], "total_now": valid[-1]["total"],
       "label": lab}
json.dump(out, open(BASE + r"\Temp\shape.json", "w", encoding="utf-8"), ensure_ascii=False)
print("\nsaved Temp/shape.json")
