# -*- coding: utf-8 -*-
"""识别 Futu CLcurrent/CLnext 每月跟踪哪个 NYMEX 合约; 检验跨源价格一致性"""
import csv, numpy as np, os
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
def norm_4h(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
def load4h_nymex(m):
    out={}
    for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig")):
        out[norm_4h(r["time"])]=float(r["close"])
    return out
def load_fu(n):
    out={}
    for r in csv.DictReader(open(os.path.join(FU,n),encoding="utf-8-sig")):
        out[r["datetime"]]=float(r["close"])
    return out
N={m:load4h_nymex(m) for m in "KMNU"}
F={n:load_fu(f"US.{n}.csv") for n in ("CLcurrent","CLnext","CL2610","CL2611")}
print("【A】Futu 各代码 vs NYMEX 各合约: 4h 变动相关性 (按月份分段)")
print(f"{'源':12s}{'月份':9s}"+"".join(f"{'CL'+k+'26':>12s}" for k in "KMNU")+"  最佳")
for src in F:
    allts=sorted(F[src])
    months=sorted({t[:7] for t in allts})
    for mo in months:
        ts=[t for t in allts if t[:7]==mo]
        rs={}
        for k in "KMNU":
            pairs=[(t,F[src][t],N[k][t]) for t in ts if t in N[k]]
            if len(pairs)<30: rs[k]=np.nan; continue
            a=np.diff([p[1] for p in pairs]); b=np.diff([p[2] for p in pairs])
            rs[k]=np.corrcoef(a,b)[0,1]
        best=max(rs,key=lambda k:(rs[k] if not np.isnan(rs[k]) else -9))
        print(f"{src:12s}{mo:9s}"+"".join((f"{rs[k]:12.3f}" if not np.isnan(rs[k]) else f"{'-':>12s}") for k in "KMNU")+f"   CL{best}26")
print()
print("【B】水平对比: 选定日期的绝对价格 (判断跨源是否可直接相减)")
dates=["2026-03-16 02:00","2026-03-30 02:00","2026-04-13 02:00","2026-04-27 02:00","2026-05-11 02:00","2026-05-18 02:00"]
print(f"{'时间':18s}{'Fcur':>8s}{'Fnext':>8s}"+"".join(f"{'CL'+k:>9s}" for k in "KMNU"))
for d in dates:
    row=f"{d:18s}"
    row+=f"{F['CLcurrent'].get(d,float('nan')):>8.2f}{F['CLnext'].get(d,float('nan')):>8.2f}"
    for k in "KMNU": row+=f"{N[k].get(d,float('nan')):>9.2f}"
    print(row)
print()
print("【C】Futu CLcurrent 与 NYMEX 各合约的 水平差 (逐月均值)")
for mo in ["2026-03","2026-04","2026-05"]:
    row=f"  {mo}: "
    for k in "KMNU":
        d=[F['CLcurrent'][t]-N[k][t] for t in F['CLcurrent'] if t[:7]==mo and t in N[k]]
        row+=f"CL{k}: {np.mean(d):+7.2f} (n={len(d):4d})   " if d else f"CL{k}: n/a    "
    print(row)
