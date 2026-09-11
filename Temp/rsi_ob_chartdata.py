# -*- coding: utf-8 -*-
import csv,json,numpy as np
BASE=r"C:/Users/Administrator/Desktop/stock"
rows=list(csv.DictReader(open(BASE+r"\data\cl_contracts\spread\cl_spread_4h.csv",encoding="utf-8-sig")))
ts=[r["ts"] for r in rows];price=np.array([float(r["CL2610"]) for r in rows])
SP={k:np.array([float(r[k]) for r in rows]) for k in rows[0] if k.startswith("abs")}
N=len(ts)
def rsi(c,n=14):
    d=np.diff(c);up=np.where(d>0,d,0.);dn=np.where(d<0,-d,0.);o=np.full(len(c),np.nan)
    au=up[:n].mean();ad=dn[:n].mean();o[n]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(n+1,len(c)):
        au=(au*(n-1)+up[i-1])/n;ad=(ad*(n-1)+dn[i-1])/n
        o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
r=rsi(price,14)
ev=[];last=-999;prev=False
for i in range(N):
    if r[i]>=70 and not prev and i-last>=12: ev.append(i);last=i
    prev=r[i]>=70
H=24
paths={}
for k in ("abs1_OCT26_NOV26","abs2_NOV26_JAN27","abs3_OCT26_JAN27"):
    s=SP[k];paths[k]=[round(float(np.mean([s[i+h]-s[i] for i in ev if i+h<N])),3) for h in range(1,H+1)]
def fwd(x,h):
    o=np.full(len(x),np.nan);o[:-h]=x[h:]-x[:-h];return o
base={}
for h in (3,6,12,24):
    d=fwd(SP["abs2_NOV26_JAN27"],h);v=~np.isnan(d);m=r>=70
    base[str(h)]=dict(pb=round(float(np.mean(d[v]<0)*100),1),pc=round(float(np.mean(d[m&v]<0)*100),1))
# 下采样折线
step=2
out=dict(ts=[ts[i] for i in range(0,N,step)],
         price=[round(float(price[i]),2) for i in range(0,N,step)],
         sp2=[round(float(SP["abs2_NOV26_JAN27"][i]),3) for i in range(0,N,step)],
         rsi=[None if np.isnan(r[i]) else round(float(r[i]),1) for i in range(0,N,step)],
         ev_idx=[int(i) for i in ev],
         ev_ts=[ts[i] for i in ev],
         ev_price=[round(float(price[i]),2) for i in ev],
         ev_sp2=[round(float(SP["abs2_NOV26_JAN27"][i]),3) for i in ev],
         ev_dp=[round(float(fwd(price,12)[i]),2) for i in ev],
         ev_ds=[round(float(fwd(SP["abs2_NOV26_JAN27"],12)[i]),3) for i in ev],
         paths=paths, base=base, N=N, step=step)
json.dump(out,open(BASE+r"\results\rsi_ob_chartdata.json","w"),ensure_ascii=False)
print("events:",len(ev),"bars:",N)
print("ev_ts:",out["ev_ts"])
print("ev_ds(2611-2701 +12bar):",out["ev_ds"])
print("base:",base)
print("path M2M4:",paths["abs2_NOV26_JAN27"])
