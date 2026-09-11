# -*- coding: utf-8 -*-
import csv,numpy as np
BASE=r"C:/Users/Administrator/Desktop/stock"
rows=list(csv.DictReader(open(BASE+r"\data\cl_contracts\spread\cl_spread_4h.csv",encoding="utf-8-sig")))
ts=[r["ts"] for r in rows];price=np.array([float(r["CL2610"]) for r in rows])
SP={k:np.array([float(r[k]) for r in rows]) for k in rows[0] if k.startswith("abs")}
def rsi(c,n=14):
    d=np.diff(c);up=np.where(d>0,d,0.);dn=np.where(d<0,-d,0.);o=np.full(len(c),np.nan)
    au=up[:n].mean();ad=dn[:n].mean();o[n]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(n+1,len(c)):
        au=(au*(n-1)+up[i-1])/n;ad=(ad*(n-1)+dn[i-1])/n
        o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
def fwd(x,h):
    o=np.full(len(x),np.nan);o[:-h]=x[h:]-x[:-h];return o
def bbd(cond,vals,block=12,nboot=4000,seed=3):
    rng=np.random.default_rng(seed);v=~np.isnan(vals);vals=vals[v];cond=cond[v]
    n=len(vals);nb=int(np.ceil(n/block));nb_=nb;dif=[]
    if cond.sum()<3: return np.nan,1.0
    obs=np.nanmean(vals[cond])-np.nanmean(vals)
    for _ in range(nboot):
        s=rng.integers(0,n,size=nb_);sel=np.concatenate([np.arange(x,min(x+block,n)) for x in s])[:n]
        vv=vals[sel];cc=cond[sel]
        if cc.sum()==0: continue
        dif.append(vv[cc].mean()-vv.mean())
    dif=np.array(dif);p=2*min((dif<=0).mean(),(dif>=0).mean());return obs,float(p)
r=rsi(price,14)
print("阈值 x 视界 扫描 (abs3_OCT26_JAN27 = M1-M4 中段): 差=条件-基准, *=p<0.05")
print(f"{'th':>4s}{'h':>4s}{'n':>5s}{'diff':>9s}{'p':>7s}")
for th in (60,65,68,70,72,75,78):
    for h in (1,2,3,6,12,24):
        d=fwd(SP["abs3_OCT26_JAN27"],h);m=r>=th
        o,p=bbd(m,d);n=int(np.nansum(m&~np.isnan(d)))
        st="*" if p<0.05 else ""
        print(f"{th:>4d}{h:>4d}{n:>5d}{o:+9.3f}{p:>6.3f}{st}")
print("\n【超卖侧对照】RSI<=30 -> Δspread (若为负=继续收敛, 正=反转向陡)")
for h in (1,2,3,6,12,24):
    for k in ("abs1_OCT26_NOV26","abs2_NOV26_JAN27","abs3_OCT26_JAN27"):
        d=fwd(SP[k],h);m=r<=30;o,p=bbd(m,d);n=int(np.nansum(m&~np.isnan(d)))
        print(f"  {k:22s} h={h:<3d} n={n:<4d} 差={o:+7.3f} p={p:.3f}{'*' if p<0.05 else ''}")
