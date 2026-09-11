# -*- coding: utf-8 -*-
"""以 NYMEX 单合约重建「真·当期月差」: 事件级口径修正 + 大样本重跑"""
import csv, json, numpy as np, os
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
OUT=r"C:/Users/Administrator/Desktop/stock/results"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
def fu(n):
    return {r["datetime"]:float(r["close"]) for r in csv.DictReader(open(os.path.join(FU,f"US.{n}.csv"),encoding="utf-8-sig"))}
F10,F11,FC,FN=fu("CL2610"),fu("CL2611"),fu("CLcurrent"),fu("CLnext")

def rsi(c,k=14):
    c=np.asarray(c,float); d=np.diff(c); up=np.where(d>0,d,0.); dn=np.where(d<0,-d,0.)
    o=np.full(len(c),np.nan); au=up[:k].mean(); ad=dn[:k].mean()
    o[k]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(k+1,len(c)):
        au=(au*(k-1)+up[i-1])/k; ad=(ad*(k-1)+dn[i-1])/k
        o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
def pair_series(a,b):
    ts=sorted(set(D[a])&set(D[b]))
    return ts,np.array([D[a][t] for t in ts]),np.array([D[b][t] for t in ts])
def spread(a,b): 
    ts,x,y=pair_series(a,b); return ts,x-y
def fwd(x,h):
    o=np.full(len(x),np.nan); o[:-h]=x[h:]-x[:-h]; return o
def evx(m,gap=12):
    o=[];last=-10**9;prev=False
    for i in range(len(m)):
        if m[i] and not prev and i-last>=gap: o.append(i); last=i
        prev=m[i]
    return o
def bbd(cond,vals,block=12,nboot=6000,seed=11):
    rng=np.random.default_rng(seed); v=~np.isnan(vals); vals=vals[v]; cond=cond[v]
    if cond.sum()<3: return np.nan,1.0,0
    obs=np.nanmean(vals[cond])-np.nanmean(vals); mm=len(vals); nb=int(np.ceil(mm/block)); dif=[]
    for _ in range(nboot):
        s=rng.integers(0,mm,size=nb); sel=np.concatenate([np.arange(x,min(x+block,mm)) for x in s])[:mm]
        vv=vals[sel]; cc=cond[sel]
        if cc.sum()==0: continue
        dif.append(vv[cc].mean()-vv.mean())
    dif=np.array(dif); return obs,float(2*min((dif<=0).mean(),(dif>=0).mean())),int(cond.sum())

# ============ 1. 事件级口径修正 ============
KM_ts,KM=spread("K","M"); MN_ts,MN=spread("M","N"); NU_ts,NU=spread("N","U")
print("="*112)
print("【1】事件级口径修正：每个超买事件当时的『真·当期月差』到底是哪一对")
print("="*112)
ROT=[("2026-03-20","2026-04-21","K","M","CLK26(2605)-CLM26(2606)","5月-6月"),
     ("2026-04-21","2026-05-19","M","N","CLM26(2606)-CLN26(2607)","6月-7月"),
     ("2026-05-19","2026-06-22",None,"Q","CLN26(2607)-CLQ26(2608)【Q缺失】","7月-8月"),
     ("2026-07-21","2026-08-20",None,"V","CLU26(2609)-CLV26(2610)【V缺失】","9月-10月")]
print("  换月日历（按到期日切分）:")
for a,b,x,y,lbl,g in ROT: print(f"    {a} ~ {b}   真M1={lbl.split('-')[0]:18s} 次月={lbl.split('-')[1] if '-' in lbl else ''}")
EV=["2026-03-12 17:00","2026-03-29 22:00","2026-04-02 10:00","2026-04-29 06:00","2026-05-17 22:00",
    "2026-07-07 17:00","2026-07-13 14:00","2026-07-19 22:00","2026-07-22 06:00","2026-08-20 06:00","2026-09-01 06:00"]
print()
print(f"{'事件时刻':18s}{'当时真M1':>10s}{'正解月差':>28s}{'真值':>8s}{'+12bar':>9s} | {'旧2610-11':>10s}{'+12bar':>9s}{'误差比':>8s}")
rows=[]
for e in EV:
    # 定位真 M1
    if e<"2026-03-20": real,spr,lbl="CLJ26(2604)","【无数据】","4月-5月"
    elif e<"2026-04-21": real,spr,lbl="CLK26(2605)","K-M","5月-6月"
    elif e<"2026-05-19": real,spr,lbl="CLM26(2606)","M-N","6月-7月"
    elif e<"2026-06-22": real,spr,lbl="CLN26(2607)","【N-Q缺Q】","7月-8月"
    elif e<"2026-07-21": real,spr,lbl="CLQ26(2608)","【无数据】","8月-9月"
    else: real,spr,lbl="CLU26(2609)","【U-V缺V】","9月-10月"
    # 真值 (K-M 或 M-N)
    tv,dv=np.nan,np.nan
    if spr=="K-M":
        ts,arr=KM_ts,KM
    elif spr=="M-N":
        ts,arr=MN_ts,MN
    else: ts,arr=None,None
    if arr is not None:
        cand=[t for t in ts if t[:13]==e[:13]] or [t for t in ts if t[:10]==e[:10]]
        if cand:
            i=ts.index(cand[0]); tv=arr[i]; dv=arr[i+12]-arr[i] if i+12<len(arr) else np.nan
    old_ts=sorted(F10); i0=next((j for j,t in enumerate(old_ts) if t[:13]==e[:13]),None)
    ov=od=np.nan
    SPO=np.array([F10[t]-F11[t] for t in old_ts])
    if i0 is not None:
        ov=SPO[i0]
        od=SPO[i0+12]-SPO[i0] if i0+12<len(SPO) else np.nan
    ratio=(tv/ov) if (ov and not np.isnan(ov) and ov!=0 and not np.isnan(tv)) else np.nan
    rows.append(dict(e=e,real=real,spread=spr,tv=None if np.isnan(tv) else round(float(tv),2),
                     dv=None if np.isnan(dv) else round(float(dv),2),ov=round(float(ov),2) if not np.isnan(ov) else None,
                     od=None if np.isnan(od) else round(float(od),2),ratio=None if np.isnan(ratio) else round(float(ratio),2)))
    print(f"{e:18s}{real:>10s}{(spr if spr.startswith('【') else spr):>28s}"
          f"{('  n/a' if np.isnan(tv) else format(tv,'8.2f'))}{('   n/a' if np.isnan(dv) else format(dv,'+9.2f'))} | "
          f"{ov:10.2f}{od:+9.2f}{('   n/a' if np.isnan(ratio) else format(ratio,'8.2f'))}")
json.dump(rows,open(OUT+r"\cl_events_corrected.json","w"),ensure_ascii=False)

# ============ 2. 修正后的事件级收敛统计 ============
print()
print("="*112)
print("【2】修正口径下的超买事件统计 (K-M 与 M-N 合并为『真当期月差』, 仅取各自当期的窗口)")
print("="*112)
seg=[]
for ts,arr in ((KM_ts,KM),(MN_ts,MN)):
    seg.append((ts,arr))
# 拼接窗口: K-M 取 >=3/20 ; M-N 取 >=4/21
def window(ts,arr,a,b):
    idx=[i for i,t in enumerate(ts) if a<=t[:10]<=b]
    return [ts[i] for i in idx],arr[idx[0]:idx[-1]+1]
wKM=window(KM_ts,KM,"2026-03-20","2026-04-21"); wMN=window(MN_ts,MN,"2026-04-21","2026-05-19")
ts_all=wKM[0]+wMN[0]; sp_all=np.concatenate([wKM[1],wMN[1]])
print(f"  真当期月差窗口: {ts_all[0]} ~ {ts_all[-1]}  共 {len(ts_all)} bar  (K-M {len(wKM[0])} + M-N {len(wMN[0])})")
print(f"  统计: mean={sp_all.mean():.3f} sd={sp_all.std():.3f} min={sp_all.min():.3f} max={sp_all.max():.3f}")
# RSI 分别打在各自的前月腿
legs=[]
for ts,arr,a,b,lm in ((KM_ts,KM,"2026-03-20","2026-04-21","K"),(MN_ts,MN,"2026-04-21","2026-05-19","M")):
    idx=[i for i,t in enumerate(ts) if a<=t[:10]<=b]
    px=np.array([D[lm][ts[i]] for i in idx]); legs.append(rsi(px))
r_all=np.concatenate(legs)
print(f"  RSI(14) 打在真前月腿上: >=70 bar数={int(np.nansum(r_all>=70))} / {len(r_all)} ({100*np.nanmean(r_all>=70):.1f}%)")
ev=evx(np.nan_to_num(r_all,nan=-1)>=70,12)
print(f"  独立事件数(间隔>=12bar) = {len(ev)}: "+", ".join(ts_all[i][5:16] for i in ev))
print()
print(f"  {'h':>4s}{'n':>5s}{'条件Δ':>9s}{'基准Δ':>9s}{'超额':>9s}{'p':>7s}{'收敛率|OB':>10s}{'基准收敛':>9s}")
for h in (1,2,3,6,9,12,18,24):
    d=fwd(sp_all,h); m=np.nan_to_num(r_all,nan=-1)>=70; v=~np.isnan(d)
    o,p,n=bbd(m,d)
    print(f"  {h:>4d}{n:>5d}{np.nanmean(d[m]):>+9.3f}{np.nanmean(d):>+9.3f}{o:>+9.3f}{p:>7.3f}"
          f"{100*np.mean(d[m&v]<0):>9.1f}%{100*np.mean(d[v]<0):>8.1f}%")

# ============ 3. 与旧口径(2610-2611)在同一时段的重叠相关性 ============
print()
print("="*112)
print("【3】同一时段: 真当期月差 vs 旧 2610-2611 (Futu) — 变动相关性")
print("="*112)
for lbl,ts_,sp_ in (("K-M(3/20-4/21)",wKM[0],wKM[1]),("M-N(4/21-5/19)",wMN[0],wMN[1])):
    common=[t for t in ts_ if t in F10 and t in F11]
    if len(common)<30: print(f"  {lbl}: 重叠不足 ({len(common)})"); continue
    a=np.array([sp_[ts_.index(t)] for t in common]); b=np.array([F10[t]-F11[t] for t in common])
    da,db=np.diff(a),np.diff(b)
    print(f"  {lbl:16s} n={len(common):4d}  水平相关={np.corrcoef(a,b)[0,1]:+.3f}  变动相关={np.corrcoef(da,db)[0,1]:+.3f}"
          f"  真值mean={a.mean():.2f} 旧值mean={b.mean():.2f}")

# ============ 4. 大样本: 各日历月差 × 前月腿RSI ============
print()
print("="*112)
print("【4】大样本重跑: 三个日历月差 × (前月腿 4h RSI>=70) 的前向变化")
print("="*112)
RES={}
for lbl,(a,b,lm) in {"K-M(2605-2606)":("K","M","K"),"M-N(2606-2607)":("M","N","M"),"N-U(2607-2609)":("N","U","N")}.items():
    ts,x,y=pair_series(a,b); sp=x-y; r=rsi(x)
    # 活跃过滤
    keep=[i for i in range(1,len(ts)) if (abs(x[i]-x[i-1])>0.005 or (0)) and (abs(y[i]-y[i-1])>0.005)]
    ts=[ts[i] for i in keep]; sp=sp[keep]; r=r[keep]
    m=np.nan_to_num(r,nan=-1)>=70; ev=evx(m,12)
    print(f"\n  ── {lbl}: 活跃bar={len(ts)}  {ts[0]} ~ {ts[-1]}   spread mean={sp.mean():.3f} sd={sp.std():.3f}")
    print(f"     RSI>=70: {int(np.nansum(m))} bar | 独立事件 {len(ev)} 个")
    if len(ev)>=5:
        print(f"     {'h':>4s}{'事件Δ均值':>11s}{'收敛占比':>9s}{'基准Δ':>9s}{'基准收敛':>9s}")
        for h in (3,6,12,24):
            v=np.array([sp[i+h]-sp[i] for i in ev if i+h<len(sp)]); d=fwd(sp,h); vv=~np.isnan(d)
            print(f"     {h:>4d}{v.mean():>+11.3f}{100*np.mean(v<0):>8.1f}%{np.nanmean(d):>+9.3f}{100*np.mean(d[vv]<0):>8.1f}%")
    RES[lbl]=dict(n=len(ts),n_ob=int(np.nansum(m)),events=[ts[i] for i in ev],
                  ev=[round(float(sp[i]),3) for i in ev])
json.dump(RES,open(OUT+r"\cl_bign.json","w"),ensure_ascii=False,indent=1)
print("\n[done]")
