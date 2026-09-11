# -*- coding: utf-8 -*-
"""诊断: CLcurrent/CLnext 是否为滚动连续合约; 找换月日; 量化固定合约对的期限漂移"""
import csv,numpy as np
B=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts"
def ld(p):
    r=list(csv.DictReader(open(p,encoding='utf-8-sig')))
    return [x['datetime'] for x in r],{x['datetime']:(float(x['close']),float(x['volume'])) for x in r}
tc,cur=ld(B+r"\4h\US.CLcurrent.csv"); tn,nxt=ld(B+r"\4h\US.CLnext.csv")
ts=[t for t in tc if t in nxt]
C=np.array([cur[t][0] for t in ts]); N_=np.array([nxt[t][0] for t in ts])
VC=np.array([cur[t][1] for t in ts]); VN=np.array([nxt[t][1] for t in ts])
RF=C-N_
dC=np.diff(C)
print("CLcurrent 单根最大跌幅 top10 (换月日候选):")
idx=np.argsort(dC)[:10]
for i in sorted(idx):
    print(f"  {ts[i+1]}  Δcur={dC[i]:+7.2f}   cur {C[i]:.2f}->{C[i+1]:.2f}   next {N_[i]:.2f}->{N_[i+1]:.2f}   RF {RF[i]:+.2f}->{RF[i+1]:+.2f}")
print("\nCLnext 单根最大跌幅 top10:")
dd=np.diff(N_)
for i in sorted(np.argsort(dd)[:10]):
    print(f"  {ts[i+1]}  Δnext={dd[i]:+7.2f}   next {N_[i]:.2f}->{N_[i+1]:.2f}   cur {C[i]:.2f}->{C[i+1]:.2f}")
print("\n滚动月差 RF=CLcurrent-CLnext 描述:")
print(f"  n={len(RF)}  mean={RF.mean():.3f} min={RF.min():.3f} max={RF.max():.3f}  末值={RF[-1]:.3f}")
print(f"  负值bar数={int((RF<0).sum())}")
print("\n|ΔRF| top12 (跳变=换月):")
dr=np.abs(np.diff(RF))
for i in sorted(np.argsort(dr)[-12:]):
    print(f"  {ts[i+1]}  ΔRF={np.diff(RF)[i]:+7.2f}   RF {RF[i]:+.2f}->{RF[i+1]:+.2f}   curΔ={C[i+1]-C[i]:+6.2f} nextΔ={N_[i+1]-N_[i]:+6.2f}")
np.save(B+r"\4h\_rf.npy",RF)
print("\n[末段核验] 2026-09-09 22:00  RF =",round(float(RF[-1]),3),"  spread_csv abs1_OCT26_NOV26 末值 = 3.40")
