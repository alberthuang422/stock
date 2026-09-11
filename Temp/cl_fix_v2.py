# -*- coding: utf-8 -*-
"""修正窗口边界后的最终版 (上一版上界写成 '2026-04' 把整月排除了)"""
import csv, json, numpy as np, os, datetime as dt
DL=r"C:/Users/Administrator/Downloads"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
EXP={"K":"2026-04-21","M":"2026-05-19","N":"2026-06-22","U":"2026-08-20"}
WIN={"KM":("2026-02-01","2026-04-21"),"MN":("2025-09-01","2026-05-19"),"NU":("2025-09-01","2026-06-22")}
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
def build(lbl):
    a,b,lm={"KM":("K","M","K"),"MN":("M","N","M"),"NU":("N","U","N")}[lbl]
    ts=sorted(set(D[a])&set(D[b])); ts=[t for t in ts if WIN[lbl][0]<=t[:10]<=WIN[lbl][1]]
    keep=[0]+[i for i in range(1,len(ts)) if abs(D[a][ts[i]]-D[a][ts[i-1]])>0.005 and abs(D[b][ts[i]]-D[b][ts[i-1]])>0.005]
    ts=[ts[i] for i in keep]
    return ts,np.array([D[a][t] for t in ts]),np.array([D[a][t]-D[b][t] for t in ts])
print("="*116)
print("【1】事件簇明细 (窗口已修正; 距前月到期天数)")
print("="*116)
print(f"{'pair':6s}{'事件':18s}{'RSI':>6s}{'D-到期':>7s}{'前月价':>8s}{'月差':>7s}{'Δ+6':>7s}{'Δ+12':>7s}{'Δ+24':>7s}{'Δ+48':>7s}")
ALL=[]
for lbl in ("KM","MN","NU"):
    ts,x,sp=build(lbl); r=rsi(x)
    for i in evx(np.nan_to_num(r,nan=-1)>=70,12):
        g=lambda h:(sp[i+h]-sp[i]) if i+h<len(sp) else np.nan
        dte=(dt.date.fromisoformat(EXP[lbl[0]])-dt.date.fromisoformat(ts[i][:10])).days
        ALL.append(dict(pair=lbl,t=ts[i],rsi=float(r[i]),dte=dte,sp=float(sp[i]),d6=g(6),d12=g(12),d24=g(24),d48=g(48)))
        print(f"{lbl:6s}{ts[i][5:16]:18s}{r[i]:>6.1f}{dte:>7d}{x[i]:>8.2f}{sp[i]:>7.2f}{g(6):>+7.2f}{g(12):>+7.2f}{g(24):>+7.2f}{g(48):>+7.2f}")
V=lambda k:np.array([e[k] for e in ALL if e[k] is not None and not (isinstance(e[k],float) and np.isnan(e[k]))])
print()
print(f"  ── 全部事件 n={len(ALL)} (KM {sum(1 for e in ALL if e['pair']=='KM')} / MN {sum(1 for e in ALL if e['pair']=='MN')} / NU {sum(1 for e in ALL if e['pair']=='NU')})")
for h,k in ((6,'d6'),(12,'d12'),(24,'d24'),(48,'d48')):
    v=V(k); print(f"     h={h:2d}({h//6}日)  均值{v.mean():+7.3f}  中位{np.median(v):+7.3f}  为负(收敛)占比{100*np.mean(v<0):5.1f}%  n={len(v)}")
print()
print("  ── 按距到期分段:")
for lab,lo,hi in ((">45日 (远期)",46,10**9),("20-45日",20,45),("<20日 (近月挤压)",-10**9,19)):
    sub=[e for e in ALL if lo<=e["dte"]<=hi]
    if len(sub)<3: print(f"     {lab}: n={len(sub)} 样本不足"); continue
    s="  ".join(f"h={h}:Δ={np.mean([e[k] for e in sub if e[k] is not None]):+.2f}({100*np.mean([e[k]<0 for e in sub if e[k] is not None]):.0f}%)" for h,k in ((6,'d6'),(12,'d12'),(24,'d24')))
    print(f"     {lab} n={len(sub)}: {s}")
print()
print("="*116)
print("【2】阈值敏感性 (事件簇层面, 前月腿 RSI)")
print("="*116)
for th in (65,70,75,80):
    for lbl in ("KM","MN","NU"):
        ts,x,sp=build(lbl); r=rsi(x); ev=evx(np.nan_to_num(r,nan=-1)>=th,12)
        if len(ev)<3: continue
        out=[]
        for h in (6,12,24):
            v=np.array([sp[i+h]-sp[i] for i in ev if i+h<len(sp)])
            out.append(f"h={h}:{v.mean():+.2f}/{100*np.mean(v<0):.0f}%")
        print(f"  RSI>={th}  {lbl}  事件{len(ev):2d}  "+"  ".join(out))
print()
print("="*116)
print("【3】对照: RSI 打在【月差自身】上")
print("="*116)
for th in (70,75,80):
    for lbl in ("KM","MN","NU"):
        ts,x,sp=build(lbl); r=rsi(sp); ev=evx(np.nan_to_num(r,nan=-1)>=th,12)
        if len(ev)<3: continue
        out=[]
        for h in (6,12,24):
            v=np.array([sp[i+h]-sp[i] for i in ev if i+h<len(sp)])
            out.append(f"h={h}:{v.mean():+.2f}/{100*np.mean(v<0):.0f}%")
        print(f"  RSI(spread)>={th}  {lbl}  事件{len(ev):2d}  "+"  ".join(out))
json.dump(ALL,open(r"C:/Users/Administrator/Desktop/stock/results/cl_fix_events.json","w"),ensure_ascii=False,indent=1,default=float)
print("\n[done]")
