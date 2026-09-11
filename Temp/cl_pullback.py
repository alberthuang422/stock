# -*- coding: utf-8 -*-
"""命题放宽: 4h RSI 超买后, 月差是否"大概率很快出现一波回落"?
关键 = 条件概率 vs 无条件基准率(挤压 regime 里月差本身波动就大)"""
import csv, json, numpy as np, os, datetime as dt
DL=r"C:/Users/Administrator/Downloads"
OUT=r"C:/Users/Administrator/Desktop/stock/results"
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

TASKS={}
for lbl in ("KM","MN","NU"):
    ts,x,sp=build(lbl); TASKS[lbl]=(ts,x,sp,rsi(x))
# 拼接: 真当期月差 = KM + MN ; 扩展 = +NU
tsC=TASKS["KM"][0]+TASKS["MN"][0]+TASKS["NU"][0]
spC=np.concatenate([TASKS["KM"][2],TASKS["MN"][2],TASKS["NU"][2]])
rC =np.concatenate([TASKS["KM"][3],TASKS["MN"][3],TASKS["NU"][3]])
n=len(spC)
print(f"合并样本: {n} bar  {tsC[0]} ~ {tsC[-1]}")
for lbl in TASKS:
    ts,x,sp,r=TASKS[lbl]
    print(f"  {lbl}: {len(ts):4d} bar  {ts[0][:10]}~{ts[-1][:10]}  spread mean={sp.mean():.2f} sd={sp.std():.2f}  RSI>=70 bar={int(np.nansum(r>=70)):3d}")

# ---- 回落指标 ----
def dd_series(sp,i,H):
    """事件后 H bar 内, 相对事件点的最大回撤(正值); 返回(幅度, 首次达到bar, 到达时bar)"""
    seg=sp[i:min(i+H+1,len(sp))]
    if len(seg)<3: return np.nan,np.nan,np.nan
    base=seg[0]; rel=base-seg[1:]
    return float(rel.max()), float(np.argmin(seg[1:])+1), float(seg.argmin())
def dd_from_peak(sp,i,H):
    """事件后 H bar 内, 相对事件后最高点的回撤"""
    seg=sp[i:min(i+H+1,len(sp))]
    if len(seg)<3: return np.nan
    pk=seg.argmax(); tail=seg[pk:]
    return float(tail[0]-tail.min()) if len(tail)>1 else 0.0

print()
print("="*112)
print("【1】条件概率 vs 无条件基准率: 事件后 H bar 内出现 >=tau 的月差回落")
print("="*112)
THR=[0.5,1.0,1.5,2.0]; HZ=[6,12,24,48]
ev=np.array(evx(np.nan_to_num(rC,nan=-1)>=70,12))
print(f"  事件数 n={len(ev)}   基准样本(全部bar)={n}")
tbl={}
for H in HZ:
    # 基准: 全部可评估起点
    bm=np.array([dd_series(spC,i,H)[0] for i in range(0,n-H) if not np.isnan(dd_series(spC,i,H)[0])])
    cm=np.array([dd_series(spC,i,H)[0] for i in ev if i+H<n])
    for tau in THR:
        pb=100*np.mean(bm>=tau); pc=100*np.mean(cm>=tau)
        tbl[f"{H}|{tau}"]=dict(pc=round(float(pc),1),pb=round(float(pb),1),lift=round(float(pc-pb),1),n=len(cm))
        print(f"  H={H:3d}({H//6}日) tau=${tau:.1f}   条件 {pc:5.1f}%   基准 {pb:5.1f}%   lift {pc-pb:+5.1f}pp   n={len(cm)}")
    print()

print("="*112)
print("【2】事件后回落的时间结构 (中位数, 单位=4h bar)")
print("="*112)
print(f"{'tau':>6s}{'首次回落bar':>12s}{'最大回撤bar':>12s}{'事件后仍创新高占比':>20s}{'最大回撤幅度中位':>18s}")
for tau in THR:
    first=[];peakpos=[];newhi=[];mdd=[]
    for i in ev:
        if i+48>=n: continue
        seg=spC[i:i+49]
        f=next((h for h in range(1,49) if seg[0]-seg[h]>=tau),None)
        if f is not None: first.append(f)
        rel=seg[0]-seg[1:]; peakpos.append(int(np.argmin(seg[1:]))+1); mdd.append(rel.max())
        newhi.append(1 if seg[1:].max()>seg[0] else 0)
    print(f"  ${tau:.1f}  {(np.median(first) if first else float('nan')):>11.1f}   {np.median(peakpos):>11.1f}"
          f"   {100*np.mean(newhi):>18.1f}%   {np.median(mdd):>17.2f}  (达tau {len(first)}/{len(peakpos)})")

print()
print("="*112)
print("【3】'先扩后收': 事件后最高点之后的回落 vs 相对事件点")
print("="*112)
rows=[]
for i in ev:
    if i+48>=n: continue
    seg=spC[i:i+49]
    d_ev,_,_=dd_series(spC,i,48)
    pk=seg.argmax()
    hi=seg[pk]; d_pk=hi-seg[pk:].min() if pk<len(seg)-1 else 0.0
    rows.append(dict(t=tsC[i],rsi=float(rC[i]),sp=float(spC[i]),after_peak=float(seg.max()-seg[0]),d_ev=float(d_ev),d_pk=float(d_pk),pk_bar=int(pk)))
print(f"{'事件':18s}{'RSI':>6s}{'月差':>7s}{'+48内最高-事件':>14s}{'最高点位置':>10s}{'事件点回撤':>11s}{'高点回撤':>9s}")
for r in sorted(rows,key=lambda z:z["t"]):
    print(f"{r['t'][5:16]:18s}{r['rsi']:>6.1f}{r['sp']:>7.2f}{r['after_peak']:>+14.2f}{r['pk_bar']:>10d}{r['d_ev']:>11.2f}{r['d_pk']:>9.2f}")
a1=np.array([r["d_ev"] for r in rows]); a2=np.array([r["d_pk"] for r in rows]); a3=np.array([r["after_peak"] for r in rows])
print(f"\n  相对事件点回撤: 中位 {np.median(a1):.2f} 均值 {a1.mean():.2f} | 相对事件后高点回撤: 中位 {np.median(a2):.2f} 均值 {a2.mean():.2f}")
print(f"  事件后 48bar 内先创更高点的占比: {100*np.mean(a3>0):.1f}%  幅度中位 {np.median(a3[a3>0]) if (a3>0).any() else 0:.2f}")

# ---- 状态细分: 月差自身分位 ----
print()
print("="*112)
print("【4】状态细分: 事件发生时月差自身的分位 (是否高处才回落)")
print("="*112)
q=np.array([float(np.mean(spC[:i+1]<=spC[i])) for i in range(n)])
for lab,lo,hi in (("月差低位(<50%)",0,.5),("月差中位(50-80%)",.5,.8),("月差高位(>80%)",.8,1.01)):
    sub=[i for i in ev if lo<q[i]<=hi and i+24<n]
    if len(sub)<3: print(f"  {lab}: n={len(sub)} 样本不足"); continue
    out=[]
    for H in (12,24):
        v=np.array([dd_series(spC,i,H)[0] for i in sub])
        out.append(f"H={H}: 回撤中位{v.mean():.2f} 达$1占比{100*np.mean(v>=1.0):.0f}%")
    print(f"  {lab} n={len(sub)}: "+"  ".join(out))
json.dump(dict(tbl=tbl,ts=tsC,sp=[round(float(v),2) for v in spC],rsi=[None if np.isnan(v) else round(float(v),1) for v in rC],
   ev=[tsC[i] for i in ev],evpos=[int(i) for i in ev],q=[round(float(v),3) for v in q],
   rows=rows,n=n),open(OUT+r"/cl_pullback.json","w"),ensure_ascii=False,default=float)
print("\n[saved] results/cl_pullback.json")
