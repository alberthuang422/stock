# -*- coding: utf-8 -*-
"""放宽命题: 4h RSI 超买后, 月差是否"大概率很快有一波回落"?
三套样本 × 条件概率 vs 无条件基准率"""
import csv, json, numpy as np, os
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
OUT=r"C:/Users/Administrator/Desktop/stock/results"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
def fu(n): return {r["datetime"]:float(r["close"]) for r in csv.DictReader(open(os.path.join(FU,f"US.{n}.csv"),encoding="utf-8-sig"))}
FC,FN=fu("CLcurrent"),fu("CLnext")
SPEC={k:fu(f"CL{k}") for k in ("2610","2611","2612","2701","2702","2703")}
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

# ---------- 样本A: 富途滚动近月月差 (剔除换月) ----------
tsA=sorted(set(FC)&set(FN))
spA=np.array([FC[t]-FN[t] for t in tsA])
# 追踪映射: CLcurrent 最接近哪个具体合约
track=[]
for t in tsA:
    best=min(SPEC,key=lambda k:abs(FC[t]-SPEC[k][t]) if t in SPEC[k] else 1e9)
    track.append(best)
roll=[i for i in range(1,len(track)) if track[i]!=track[i-1]]
bad=set()
for i in roll:
    for j in range(max(0,i-4),min(len(tsA),i+5)): bad.add(j)
# 还剔除极端跳变
jumps=[i for i in range(1,len(spA)) if abs(spA[i]-spA[i-1])>2.0]
for i in jumps:
    for j in range(max(0,i-1),min(len(tsA),i+2)): bad.add(j)
keepA=[i for i in range(6,len(tsA)) if i not in bad]
tsA=[tsA[i] for i in keepA]; spA=spA[keepA]
pxA=np.array([FC[t] for t in tsA]) if False else None
curA=np.array([FC[tsA[i]] for i in range(len(tsA))])
rA=rsi(curA)
print("="*118)
print("【样本A】富途滚动近月月差 RF=CLcurrent−CLnext  (换月±4bar 与 >$2 跳变已剔除)")
print("="*118)
print(f"  n={len(tsA)} bar  {tsA[0]} ~ {tsA[-1]}   spread: mean={spA.mean():.2f} sd={spA.std():.2f} min={spA.min():.2f} max={spA.max():.2f}")
print(f"  换月点 {len(roll)} 个 @ "+", ".join(tsA[i][5:10] for i in roll if i<len(tsA))[:120])
print(f"  RSI(14)≥70: {int(np.nansum(rA>=70))} bar ({100*np.nanmean(rA>=70):.1f}%)")

# ---------- 样本B: NYMEX 真前月月差 K−M + M−N ----------
def seg(a,b,t0,t1,lm):
    ts=sorted(set(D[a])&set(D[b])); ts=[t for t in ts if t0<=t[:10]<=t1]
    keep=[0]+[i for i in range(1,len(ts)) if abs(D[a][ts[i]]-D[a][ts[i-1]])>0.005 and abs(D[b][ts[i]]-D[b][ts[i-1]])>0.005]
    ts=[ts[i] for i in keep]
    return ts,np.array([D[a][t] for t in ts]),np.array([D[a][t]-D[b][t] for t in ts])
b1=seg("K","M","2026-03-20","2026-04-21","K"); b2=seg("M","N","2026-04-22","2026-05-19","M")
tsB=b1[0]+b2[0]; spB=np.concatenate([b1[2],b2[2]]); curB=np.concatenate([b1[1],b2[1]])
rB=rsi(curB)
print()
print("="*118)
print("【样本B】NYMEX 真前月月差 (K−M 3/20-4/21 ⊕ M−N 4/22-5/19)")
print("="*118)
print(f"  n={len(tsB)} bar  {tsB[0]} ~ {tsB[-1]}  spread: mean={spB.mean():.2f} sd={spB.std():.2f} max={spB.max():.2f}")
print(f"  RSI(14)≥70: {int(np.nansum(rB>=70))} bar ({100*np.nanmean(rB>=70):.1f}%)")

# ---------- 样本C: NYMEX N−U 长历史 (跨2月, 与 2611-2701 同结构) ----------
tsC=sorted(set(D["N"])&set(D["U"])); tsC=[t for t in tsC if "2025-09-01"<=t[:10]<="2026-06-22"]
keepC=[0]+[i for i in range(1,len(tsC)) if abs(D["N"][tsC[i]]-D["N"][tsC[i-1]])>0.005 and abs(D["U"][tsC[i]]-D["U"][tsC[i-1]])>0.005]
tsC=[tsC[i] for i in keepC]
Np=np.array([D["N"][t] for t in tsC]); spC=Np-np.array([D["U"][t] for t in tsC])
rC=rsi(Np)
print()
print("="*118)
print("【样本C】NYMEX N−U (2607−2609, 跨2月 = 与你的 2611−2701 同结构) 长历史")
print("="*118)
print(f"  n={len(tsC)} bar  {tsC[0]} ~ {tsC[-1]}  spread: mean={spC.mean():.2f} sd={spC.std():.2f} min={spC.min():.2f} max={spC.max():.2f}")
print(f"  RSI(14)≥70: {int(np.nansum(rC>=70))} bar ({100*np.nanmean(rC>=70):.1f}%)")

# ---------- 通用: 回落概率 条件 vs 基准 ----------
def analyze(name,ts,sp,r,THR=(0.5,1.0,2.0),HZ=(12,24,48)):
    n=len(sp)
    dd=lambda i,H:(lambda s: (float((s[0]-s[1:]).max()) if len(s)>2 else np.nan))(sp[i:min(i+H+1,n)])
    ev=evx(np.nan_to_num(r,nan=-1)>=70,12)
    ev=[i for i in ev if i+HZ[-1]<n]
    print(f"\n{'─'*118}\n{name}: 事件 n={len(ev)}  基准bar={n}")
    res={}
    print(f"  {'H':>5s}{'tau':>6s}{'条件P':>9s}{'基准P':>9s}{'lift':>8s}{'条件均值':>10s}{'基准均值':>10s}")
    for H in HZ:
        bmv=np.array([dd(i,H) for i in range(n-H) if not np.isnan(dd(i,H))])
        cmv=np.array([dd(i,H) for i in ev])
        for tau in THR:
            pc=100*np.mean(cmv>=tau); pb=100*np.mean(bmv>=tau)
            res[f"{H}_{tau}"]=dict(pc=round(float(pc),1),pb=round(float(pb),1),lift=round(float(pc-pb),1),
                                   mc=round(float(cmv.mean()),3),mb=round(float(bmv.mean()),3),n=len(cmv))
            print(f"  {H:>5d}{tau:>6.1f}{pc:>8.1f}%{pb:>8.1f}%{pc-pb:>+7.1f}pp{cmv.mean():>10.3f}{bmv.mean():>10.3f}")
    # 先扩后收
    hp=[];de=[];ap=[]
    for i in ev:
        s=sp[i:i+49] if i+48<n else sp[i:]
        if len(s)<10: continue
        pk=int(np.argmax(s)); de.append(float((s[0]-s[1:]).max())); ap.append(float(s.max()-s[0]))
        hp.append(float(s[pk]-s[pk:].min()) if pk<len(s)-1 else 0.0)
    print(f"  先扩后收: 事件后48bar内仍创更高点 {100*np.mean(np.array(ap)>0):.0f}% (中位+{np.median(np.array(ap)[np.array(ap)>0]) if (np.array(ap)>0).any() else 0:.2f})")
    print(f"            相对事件点回撤 中位{np.median(de):.2f} | 相对事件后高点回撤 中位{np.median(hp):.2f}")
    res["xiankuo"]=dict(newhi=round(float(100*np.mean(np.array(ap)>0)),1),de=round(float(np.median(de)),3),hp=round(float(np.median(hp)),3))
    return res,ev

RA,evA=analyze("样本A 富途滚动近月月差 (128日)",tsA,spA,rA)
RB,evB=analyze("样本B NYMEX 真前月月差 (K−M ⊕ M−N)",tsB,spB,rB)
RC,evC=analyze("样本C NYMEX N−U 跨2月 长历史 (~10个月)",tsC,spC,rC)
json.dump(dict(A=RA,B=RB,C=RC,
    evA=[tsA[i] for i in evA],evB=[tsB[i] for i in evB],evC=[tsC[i] for i in evC],
    nA=len(tsA),nB=len(tsB),nC=len(tsC),
    spA=[round(float(v),2) for v in spA],rA=[None if np.isnan(v) else round(float(v),1) for v in rA],tsA=tsA,posA=[int(i) for i in evA],
    spC=[round(float(v),2) for v in spC],rC=[None if np.isnan(v) else round(float(v),1) for v in rC],tsC=tsC,posC=[int(i) for i in evC],
    spB=[round(float(v),2) for v in spB],tsB=tsB,posB=[int(i) for i in evB]),
    open(OUT+r"/cl_pullback2.json","w"),ensure_ascii=False,default=float)
print("\n[saved]")
