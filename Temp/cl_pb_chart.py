# -*- coding: utf-8 -*-
import csv,json,numpy as np,os
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
def fu(n): return {r["datetime"]:float(r["close"]) for r in csv.DictReader(open(os.path.join(FU,f"US.{n}.csv"),encoding="utf-8-sig"))}
FC,FN=fu("CLcurrent"),fu("CLnext")
def rsi(c,k=14):
    c=np.asarray(c,float); d=np.diff(c); up=np.where(d>0,d,0.); dn=np.where(d<0,-d,0.)
    o=np.full(len(c),np.nan); au=up[:k].mean(); ad=dn[:k].mean(); o[k]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(k+1,len(c)):
        au=(au*(k-1)+up[i-1])/k; ad=(ad*(k-1)+dn[i-1])/k; o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
def evx(m,gap=12):
    o=[];last=-10**9;prev=False
    for i in range(len(m)):
        if m[i] and not prev and i-last>=gap: o.append(i); last=i
        prev=m[i]
    return o
# A
tsA=sorted(set(FC)&set(FN)); spA=np.array([FC[t]-FN[t] for t in tsA])
keepA=[i for i in range(6,len(tsA)) if abs(spA[i]-spA[i-1])<=2.0]
tsA=[tsA[i] for i in keepA]; spA=spA[keepA]
evA=[i for i in evx(np.nan_to_num(rsi(np.array([FC[t] for t in tsA])),nan=-1)>=70,12) if i+48<len(tsA)]
# C
tsC=sorted(set(D["N"])&set(D["U"])); tsC=[t for t in tsC if "2025-09-01"<=t[:10]<="2026-06-22"]
keepC=[0]+[i for i in range(1,len(tsC)) if abs(D["N"][tsC[i]]-D["N"][tsC[i-1]])>0.005 and abs(D["U"][tsC[i]]-D["U"][tsC[i-1]])>0.005]
tsC=[tsC[i] for i in keepC]
Np=np.array([D["N"][t] for t in tsC]); spC=Np-np.array([D["U"][t] for t in tsC])
evC=[i for i in evx(np.nan_to_num(rsi(Np),nan=-1)>=70,12) if i+48<len(tsC)]
def path(sp,ev,H=48):
    M=[];S=[]
    for h in range(H+1):
        v=np.array([sp[i+h]-sp[i] for i in ev if i+h<len(sp)])
        M.append(float(v.mean())); S.append(float(v.std()/np.sqrt(len(v))) if len(v)>1 else 0.)
    return M,S
MA,SA=path(spA,evA); MC,SC=path(spC,evC)
print("PA="+json.dumps([round(v,3) for v in MA]))
print("SA="+json.dumps([round(v,3) for v in SA]))
print("PC="+json.dumps([round(v,3) for v in MC]))
print("SC="+json.dumps([round(v,3) for v in SC]))
print("nA=%d nC=%d"%(len(evA),len(evC)))
# 概率对比 (tau=1.0)
PROB={}
for nm,sp,ev in (("A",spA,evA),("C",spC,evC)):
    n=len(sp); d={}
    for H in (12,24,48):
        pb=100*np.mean([(sp[i:i+H+1][0]-sp[i:i+H+1][1:]).max()>=1.0 for i in range(n-H)])
        pc=100*np.mean([(sp[i:i+H+1][0]-sp[i:i+H+1][1:]).max()>=1.0 for i in ev])
        d[str(H)]=dict(pc=round(float(pc),1),pb=round(float(pb),1))
    PROB[nm]=d
print("PROB="+json.dumps(PROB))
# 事件明细: 事件后最高点位置 / 幅度 / 到回落bar
det=[]
for nm,ts,sp,ev in (("A",tsA,spA,evA),("C",tsC,spC,evC)):
    for i in ev:
        s=sp[i:i+49]; p=int(np.argmax(s)); f=next((h for h in range(1,49) if s[0]-s[h]>=0.5),None)
        det.append([nm,ts[i][5:10],round(float(s[0]),2),int(p),round(float(s.max()-s[0]),2),round(float(s[0]-s[1:].max()),2),f if f else 49])
print("DET="+json.dumps(det))
# 净变化路径 (有符号)
print("NETA="+json.dumps([round(float(np.mean([spA[i+h]-spA[i] for i in evA if i+h<len(spA)])),3) for h in (1,3,6,12,24,36,48)]))
print("NETC="+json.dumps([round(float(np.mean([spC[i+h]-spC[i] for i in evC if i+h<len(spC)])),3) for h in (1,3,6,12,24,36,48)]))
