# -*- coding: utf-8 -*-
"""补充: 标准化回撤 / 回落时间分布 / 状态细分 / 二项检验"""
import csv, json, numpy as np, os
from math import comb
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
OUT=r"C:/Users/Administrator/Desktop/stock/results"
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
def binom_p(k,n,p):
    """单侧: 观察 k/n >= p 的概率 (P(X>=k))"""
    return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))

# 样本A
tsA=sorted(set(FC)&set(FN)); spA=np.array([FC[t]-FN[t] for t in tsA])
keepA=[i for i in range(6,len(tsA)) if abs(spA[i]-spA[i-1])<=2.0]
tsA=[tsA[i] for i in keepA]; spA=spA[keepA]
curA=np.array([FC[t] for t in tsA]); rA=rsi(curA)
evA=[i for i in evx(np.nan_to_num(rA,nan=-1)>=70,12) if i+48<len(tsA)]
# 样本C
tsC=sorted(set(D["N"])&set(D["U"])); tsC=[t for t in tsC if "2025-09-01"<=t[:10]<="2026-06-22"]
keepC=[0]+[i for i in range(1,len(tsC)) if abs(D["N"][tsC[i]]-D["N"][tsC[i-1]])>0.005 and abs(D["U"][tsC[i]]-D["U"][tsC[i-1]])>0.005]
tsC=[tsC[i] for i in keepC]
Np=np.array([D["N"][t] for t in tsC]); spC=Np-np.array([D["U"][t] for t in tsC]); rC=rsi(Np)
evC=[i for i in evx(np.nan_to_num(rC,nan=-1)>=70,12) if i+48<len(tsC)]

print("="*118)
print("【1】事件后『最高点』出现的 bar 位置 (回答: 超买后是立刻见顶, 还是先冲高?)")
print("="*118)
for name,ts,sp,ev in (("A 富铜滚动近月",tsA,spA,evA),("C N−U 跨2月长史",tsC,spC,evC)):
    pk=[];ap=[];de=[];hp=[];f05=[];std_de=[]
    for i in ev:
        s=sp[i:i+49]; p=int(np.argmax(s)); pk.append(p)
        ap.append(float(s.max()-s[0])); de.append(float((s[0]-s[1:]).max()))
        hp.append(float(s[p]-s[p:].min()) if p<len(s)-1 else 0.0)
        std_de.append(de[-1]/max(abs(s[0]),.3))
        f=next((h for h in range(1,49) if s[0]-s[h]>=0.5),None); f05.append(f if f else 49)
    pk=np.array(pk);ap=np.array(ap);de=np.array(de);hp=np.array(hp);f05=np.array(f05);std_de=np.array(std_de)
    print(f"\n  {name} n={len(ev)}")
    print(f"    最高点位置(bar): 中位{np.median(pk):.0f}  均值{pk.mean():.1f}  分布 {sorted(pk.tolist())}")
    print(f"    事件→最高点: 中位+{np.median(ap):.2f}  |  最高点→随后低点: 中位{np.median(hp):.2f}")
    print(f"    相对事件点回撤 中位{np.median(de):.2f}  |  标准化(回撤/事件时月差) 中位{np.median(std_de):.2f}")
    print(f"    首次回落$0.5 的bar: 中位 {np.median(f05):.0f}  在24bar内达成 {int((f05<=24).sum())}/{len(f05)}")

print()
print("="*118)
print("【2】净效果: 从事件点起算 h bar 后的月差变化 (含先冲高) —— 这才是'做空能否赚钱'")
print("="*118)
for name,ts,sp,ev in (("A 富途滚动近月",tsA,spA,evA),("C N−U 跨2月",tsC,spC,evC)):
    n=len(sp)
    print(f"\n  {name}")
    print(f"    {'h':>4s}{'事件均值Δ':>11s}{'基准均值Δ':>11s}{'差':>9s}{'事件为负占比':>13s}{'基准为负占比':>13s}")
    for h in (1,3,6,12,24,48):
        cv=np.array([sp[i+h]-sp[i] for i in ev if i+h<n]); v=~np.isnan(np.array([sp[i+h]-sp[i] for i in range(n-h)]))
        bv=np.array([sp[i+h]-sp[i] for i in range(n-h)])
        print(f"    {h:>4d}{cv.mean():>+11.3f}{bv.mean():>+11.3f}{cv.mean()-bv.mean():>+9.3f}{100*np.mean(cv<0):>12.1f}%{100*np.mean(bv<0):>12.1f}%")

print()
print("="*118)
print("【3】状态细分: 事件发生时月差自身分位 → 回落概率 (是不是'高处才回落')")
print("="*118)
for name,ts,sp,r,ev in (("A 富途滚动近月",tsA,spA,rA,evA),("C N−U 跨2月",tsC,spC,rC,evC)):
    n=len(sp); q=np.array([float(np.mean(sp[:i+1]<=sp[i])) for i in range(n)])
    print(f"\n  {name}")
    for lab,lo,hi in (("月差<50%分位",0,.5),("50-80%",.5,.8),(">80%分位(高位)",.8,1.01)):
        sub=[i for i in ev if lo<q[i]<=hi]
        if len(sub)<3: print(f"    {lab}: n={len(sub)} 样本不足"); continue
        v24=np.array([(sp[i:i+25][0]-sp[i:i+25][1:]).max() for i in sub])
        d24=np.array([sp[min(i+24,n-1)]-sp[i] for i in sub])
        pb24=np.mean([(sp[i:i+25][0]-sp[i:i+25][1:]).max()>=1.0 for i in range(n-24)])
        pc24=np.mean(v24>=1.0)
        print(f"    {lab} n={len(sub):2d}: 24bar内最大回撤中位{np.median(v24):5.2f}  达$1占比{100*pc24:5.1f}% (基准{100*pb24:.1f}%)"
              f"  净变化均值{d24.mean():+.2f}")

print()
print("="*118)
print("【4】二项检验: 条件概率是否显著高于基准 (n=事件数)")
print("="*118)
for name,ts,sp,r,ev in (("A 富途滚动近月",tsA,spA,rA,evA),("C N−U 跨2月",tsC,spC,rC,evC)):
    n=len(sp)
    print(f"\n  {name} (n_event={len(ev)})")
    for H,tau in ((24,0.5),(24,1.0),(48,1.0)):
        pb=np.mean([(sp[i:i+H+1][0]-sp[i:i+H+1][1:]).max()>=tau for i in range(n-H)])
        c=np.array([(sp[i:i+H+1][0]-sp[i:i+H+1][1:]).max()>=tau for i in ev])
        k=int(c.sum()); p=binom_p(k,len(c),pb)
        print(f"    H={H:2d} tau=${tau:.1f}: 条件 {k}/{len(c)}={100*k/len(c):5.1f}%  基准{100*pb:5.1f}%  P(X>={k}|基准)={p:.3f} {'显著' if p<0.05 else '不显著'}")
json.dump(dict(tsA=tsA,tsC=tsC),open(OUT+r"/_tmp_ts.json","w"),ensure_ascii=False)
print("\n[done]")
