# -*- coding: utf-8 -*-
"""最终口径: 流动性窗口限定 + 事件簇(每簇1个观测) + 距到期分段 + 块自助"""
import csv, json, numpy as np, os
DL=r"C:/Users/Administrator/Downloads"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
EXP={"K":"2026-04-21","M":"2026-05-19","N":"2026-06-22","U":"2026-08-20"}
import datetime as dt
def days_to(t,e): return (dt.date.fromisoformat(e)-dt.date.fromisoformat(t[:10])).days
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
def bbd(cond,vals,block=24,nboot=8000,seed=7):
    rng=np.random.default_rng(seed); v=~np.isnan(vals); vals=vals[v]; cond=np.asarray(cond)[v]
    if cond.sum()<3: return np.nan,1.0,int(cond.sum())
    obs=np.nanmean(vals[cond])-np.nanmean(vals); m=len(vals); nb=int(np.ceil(m/block)); dif=[]
    for _ in range(nboot):
        s=rng.integers(0,m,size=nb); sel=np.concatenate([np.arange(x,min(x+block,m)) for x in s])[:m]
        vv=vals[sel]; cc=cond[sel]
        if cc.sum()==0: continue
        dif.append(vv[cc].mean()-vv.mean())
    dif=np.array(dif); return obs,float(2*min((dif<=0).mean(),(dif>=0).mean())),int(cond.sum())

# 1) 各腿月度活跃度 -> 定义"双腿流动性窗口"
print("="*112); print("【1】各合约 4h 月度活跃bar数 (定义有效样本窗口)"); print("="*112)
mon={}
for m in "KMNU":
    ts=sorted(D[m]); cnt={}
    for i in range(1,len(ts)):
        if abs(D[m][ts[i]]-D[m][ts[i-1]])>0.005: cnt[ts[i][:7]]=cnt.get(ts[i][:7],0)+1
    mon[m]=cnt
allm=sorted(set().union(*[set(c) for c in mon.values()]))
print(f"{'月份':9s}"+"".join(f"{'CL'+m:>8s}" for m in "KMNU"))
for k in allm:
    if k<"2024-06": continue
    print(f"{k:9s}"+"".join(f"{mon[m].get(k,0):>8d}" for m in "KMNU"))
LIQ={"KM":("2026-02","2026-04"),"MN":("2025-08","2026-05"),"NU":("2025-06","2026-06")}

# 2) 事件簇层面
print()
print("="*112); print("【2】事件簇层面 (每簇1观测=簇首) × 距前月到期天数分段"); print("="*112)
print(f"{'pair':6s}{'事件':18s}{'RSI':>6s}{'D-到期':>8s}{'月差':>8s}{'Δ+6':>8s}{'Δ+12':>8s}{'Δ+24':>8s}{'Δ+48':>8s}")
ALL=[]
for lbl,(a,b,lm) in {"KM":("K","M","K"),"MN":("M","N","M"),"NU":("N","U","N")}.items():
    ts=sorted(set(D[a])&set(D[b])); ts=[t for t in ts if LIQ[lbl][0]<=t[:10]<=LIQ[lbl][1]]
    keep=[0]+[i for i in range(1,len(ts)) if abs(D[a][ts[i]]-D[a][ts[i-1]])>0.005 and abs(D[b][ts[i]]-D[b][ts[i-1]])>0.005]
    ts=[ts[i] for i in keep]
    x=np.array([D[a][t] for t in ts]); sp=np.array([D[a][t]-D[b][t] for t in ts]); r=rsi(x)
    ev=evx(np.nan_to_num(r,nan=-1)>=70,12)
    for i in ev:
        g=lambda h:(sp[i+h]-sp[i]) if i+h<len(sp) else np.nan
        dte=days_to(ts[i],EXP[a])
        ALL.append(dict(pair=lbl,t=ts[i],rsi=r[i],dte=dte,sp=sp[i],d6=g(6),d12=g(12),d24=g(24),d48=g(48)))
        print(f"{lbl:6s}{ts[i][5:16]:18s}{r[i]:>6.1f}{dte:>8d}{sp[i]:>8.2f}{g(6):>+8.2f}{g(12):>+8.2f}{g(24):>+8.2f}{g(48):>+8.2f}")
arr=lambda k: np.array([e[k] for e in ALL if e[k] is not None and not (isinstance(e[k],float) and np.isnan(e[k]))])
print()
print(f"  全部事件 n={len(ALL)}:")
for h,k in ((6,'d6'),(12,'d12'),(24,'d24'),(48,'d48')):
    v=arr(k); print(f"    h={h:2d}  均值{v.mean():+7.3f}  中位{np.median(v):+7.3f}  收敛占比{100*np.mean(v<0):5.1f}%")
print()
for lbl,lo,hi in (("距到期 >45日",46,10**9),("距到期 20-45日",20,45),("距到期 <20日",-10**9,19)):
    sub=[e for e in ALL if lo<=e["dte"]<=hi]
    if len(sub)<3: print(f"  {lbl}: n={len(sub)} 样本不足"); continue
    print(f"  {lbl} (n={len(sub)}): "+"  ".join(
        f"h={h}: Δ={np.mean([s[k] for s in sub if s[k] is not None]):+.2f} 收敛{100*np.mean([s[k]<0 for s in sub if s[k] is not None]):.0f}%" 
        for h,k in ((6,'d6'),(12,'d12'),(24,'d24'))))

# 3) 用"月差自身"的RSI
print()
print("="*112); print("【3】对照: RSI 打在【月差序列本身】上 (均值回归视角)"); print("="*112)
for lbl,(a,b,lm) in {"KM":("K","M","K"),"MN":("M","N","M"),"NU":("N","U","N")}.items():
    ts=sorted(set(D[a])&set(D[b])); ts=[t for t in ts if LIQ[lbl][0]<=t[:10]<=LIQ[lbl][1]]
    keep=[0]+[i for i in range(1,len(ts)) if abs(D[a][ts[i]]-D[a][ts[i-1]])>0.005 and abs(D[b][ts[i]]-D[b][ts[i-1]])>0.005]
    ts=[ts[i] for i in keep]; sp=np.array([D[a][t]-D[b][t] for t in ts]); r=rsi(sp)
    for th in (70,75,80):
        ev=evx(np.nan_to_num(r,nan=-1)>=th,12)
        if len(ev)<3: print(f"  {lbl} RSI(spread)>={th}: 事件仅{len(ev)}个"); continue
        row=[]
        for h in (6,12,24):
            v=np.array([sp[i+h]-sp[i] for i in ev if i+h<len(sp)])
            row.append(f"h={h}: Δ={v.mean():+.3f} 收敛{100*np.mean(v<0):.0f}%(n={len(v)})")
        print(f"  {lbl} RSI(spread)>={th}  事件{len(ev)}: "+"  ".join(row))
print()
print("[done]")
