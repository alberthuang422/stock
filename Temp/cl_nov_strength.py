# -*- coding: utf-8 -*-
"""CL 各月合约近期强弱与月差结构（基于 data/cl_contracts/daily）"""
import os, csv, statistics as st

BASE = r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/daily"
CODES = ["US.CL2610", "US.CL2611", "US.CL2612", "US.CL2701", "US.CL2702", "US.CL2703"]

data = {}
for c in CODES:
    rows = list(csv.DictReader(open(os.path.join(BASE, c + ".csv"), encoding="utf-8")))
    data[c] = rows
    print(c, "cols:", list(rows[0].keys()), "n=", len(rows))

dates = [r["date"] for r in data[CODES[0]]]
print("\nfirst/last date:", dates[0], dates[-1])

close = {c: [float(r["close"]) for r in data[c]] for c in CODES}
vol = {c: [float(r.get("volume", 0) or 0) for r in data[c]] for c in CODES}
oi = {c: [float(r.get("open_interest", 0) or 0) for r in data[c]] for c in CODES}

def ret(c, n):
    return (close[c][-1] / close[c][-1-n] - 1) * 100

print("\n=== 区间涨幅 % ===")
print(f"{'合约':<12}" + "".join(f"{f'{n}日':>9}" for n in [1,2,3,5,10,20]))
for c in CODES:
    print(f"{c:<12}" + "".join(f"{ret(c,n):>9.2f}" for n in [1,2,3,5,10,20]))

print("\n=== 最新收盘 / 成交量 / 持仓量 ===")
for c in CODES:
    print(f"{c:<12} close={close[c][-1]:>8.2f} vol={vol[c][-1]:>9.0f} oi={oi[c][-1]:>9.0f}  "
          f"oi_20d前={oi[c][-21]:>9.0f}  oi变化={oi[c][-1]-oi[c][-21]:>+9.0f}")

print("\n=== 相邻月差 (abs1) 与占近月比 pm1(%) ===")
names = [("US.CL2610","US.CL2611"),("US.CL2611","US.CL2612"),
         ("US.CL2612","US.CL2701"),("US.CL2701","US.CL2702"),("US.CL2702","US.CL2703")]
print(f"{'价差':<24}" + "".join(f"{f'T-{n}':>10}" for n in [0,1,2,3,5,10,20]))
for a,b in names:
    tag=f"{a[-4:]}-{b[-4:]}"
    line=f"{tag:<24}"
    for n in [0,1,2,3,5,10,20]:
        i=-1-n
        sp=close[a][i]-close[b][i]
        line+=f"{sp:>10.2f}"
    print(line)
print()
for a,b in names:
    tag=f"{a[-4:]}/{b[-4:]} pm1%"
    line=f"{tag:<24}"
    for n in [0,1,2,3,5,10,20]:
        i=-1-n
        sp=close[a][i]-close[b][i]
        line+=f"{sp/close[a][i]*100:>10.2f}"
    print(line)

print("\n=== 曲线整体陡度：近月-远月 pm1 与 各段斜率 ===")
for n in [0,5,10,20]:
    i=-1-n
    p=[close[c][i] for c in CODES]
    segs=[(p[k]-p[k+1]) for k in range(5)]
    print(f"T-{n:<3} " + " ".join(f"{s:>6.2f}" for s in segs) + f"   seg均值={st.mean(segs):.2f}")
