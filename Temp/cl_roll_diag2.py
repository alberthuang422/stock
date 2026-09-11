# -*- coding: utf-8 -*-
import csv,numpy as np
B=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts"
def ld(p):
    r=list(csv.DictReader(open(p,encoding='utf-8-sig')))
    return {x['datetime']:(float(x['close']),float(x['volume'])) for x in r}
cur=ld(B+r"\4h\US.CLcurrent.csv"); nxt=ld(B+r"\4h\US.CLnext.csv")
c10=ld(B+r"\4h\US.CL2610.csv")
ts=sorted(set(cur)&set(nxt))
C=np.array([cur[t][0] for t in ts]); N_=np.array([nxt[t][0] for t in ts])
VC=np.array([cur[t][1] for t in ts])
print("检验: 换月时 新cur ≈ 旧next   (找 |cur[i+1]-next[i]|<0.05 的 bar)")
hits=[]
for i in range(len(ts)-1):
    if abs(C[i+1]-N_[i])<0.05:
        hits.append(i)
print("命中数:",len(hits))
for i in hits: print(f"  → {ts[i+1]}  cur[i+1]={C[i+1]:.2f}  next[i]={N_[i]:.2f}")
print()
print("检验2: CLcurrent 何时与 CL2610 重合 (首个持续重合日)")
c2610=np.array([c10[t][0] for t in ts])
d=np.abs(C-c2610)
first=None
for i in range(len(ts)-30):
    if max(d[i:i+30])<0.02: first=i;break
print("  ",ts[first] if first is not None else "未找到", " 之后 |cur-2610| 恒 <0.02")
print("  最后30根 |cur-2610| max =",round(float(max(d[-30:])),4))
print()
print("检验3: 全样本 |cur-2610| > 0.02 的bar数 =",int((d>0.02).sum()),"/",len(ts))
print("  分段 |cur-2610| 均值:")
seg=[0,80,160,240,320,400,480,560,640,700,770]
for a,b in zip(seg[:-1],seg[1:]):
    print(f"   {ts[a][:10]} ~ {ts[b-1][:10]}   mean={d[a:b].mean():7.2f}   max={d[a:b].max():7.2f}")
print()
print("=== 关键: 各超买事件日, 真实滚动月差 RF vs 2610-2611 ===")
RF=C-N_
c11=np.array([ld(B+r"\4h\US.CL2611.csv")[t][0] for t in ts])
FIX=c2610-c11
evs=['2026-03-12 17:00','2026-04-29 06:00','2026-05-17 22:00','2026-07-07 17:00','2026-07-13 14:00','2026-07-19 22:00','2026-07-22 06:00','2026-08-11 06:00','2026-09-01 06:00']
print(f"{'事件':18s}{'cur':>8s}{'next':>8s}{'RF真':>9s}{'2610-11':>9s}{'cur-2610':>10s}{'比值':>7s}")
for e in evs:
    if e not in ts: e2=[t for t in ts if t[:10]==e[:10]][0]; e=e2
    i=ts.index(e)
    print(f"{e:18s}{C[i]:8.2f}{N_[i]:8.2f}{RF[i]:9.2f}{FIX[i]:9.2f}{C[i]-c2610[i]:10.2f}{RF[i]/FIX[i] if FIX[i]!=0 else float('nan'):7.2f}")
np.save(B+r"\4h\_roll_arrays.npy",np.vstack([C,N_,c2610,c11]))
