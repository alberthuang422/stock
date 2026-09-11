# -*- coding: utf-8 -*-
"""功效分析(MDE) + 事件窗口均值(供绘图) + 去价格效应检验"""
import csv, json
import numpy as np
BASE=r"C:\Users\Administrator\Desktop\stock"
rows=list(csv.DictReader(open(BASE+r"\data\cl_contracts\spread\cl_spread_4h.csv",encoding="utf-8-sig")))
ts=[r["ts"] for r in rows]; price=np.array([float(r["CL2610"]) for r in rows])
SP={k:np.array([float(r[k]) for r in rows]) for k in rows[0] if k.startswith("abs")}
N=len(ts)
def rsi(c,n=14):
    d=np.diff(c);up=np.where(d>0,d,0.);dn=np.where(d<0,-d,0.);o=np.full(len(c),np.nan)
    au=up[:n].mean();ad=dn[:n].mean();o[n]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(n+1,len(c)):
        au=(au*(n-1)+up[i-1])/n;ad=(ad*(n-1)+dn[i-1])/n
        o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
def fwd(x,h):
    o=np.full(len(x),np.nan);o[:-h]=x[h:]-x[:-h];return o
r=rsi(price,14)

print("[K] 功效分析: OB事件下 Δspread(h=12) 的离散度 -> 最小可检测效应 MDE")
ev=[];last=-999;prev=False
for i in range(N):
    if r[i]>=70 and not prev and i-last>=12: ev.append(i);last=i
    prev=r[i]>=70
for k in ("abs1_OCT26_NOV26","abs2_NOV26_JAN27","abs3_OCT26_JAN27"):
    d=fwd(SP[k],12); v=np.array([d[i] for i in ev if not np.isnan(d[i])])
    se=v.std(ddof=1)/np.sqrt(len(v))
    print(f"  {k:22s} n={len(v)} mean={v.mean():+.3f} sd={v.std(ddof=1):.3f} SE={se:.3f}  MDE(80%power,2side)={2.8*se:.3f}")

print("\n[L] 事件窗口平均路径 (event-time, 相对事件bar的累计Δ, 单位$)  RSI(14)>=70")
H=24
for k in ("abs1_OCT26_NOV26","abs2_NOV26_JAN27","abs3_OCT26_JAN27"):
    s=SP[k]; path=[]
    for h in range(1,H+1):
        v=[s[i+h]-s[i] for i in ev if i+h<N]
        path.append(float(np.mean(v)))
    print(f"  {k}")
    print("   ", " ".join([f"{p:+.2f}" for p in path[:12]]))
    print("   ", " ".join([f"{p:+.2f}" for p in path[12:]]))

print("\n[M] 去价格效应: Δspread(h=12) ~ a + b*Δprice(h=12) + c*RSI_t   (c 是否为0)")
for k in ("abs1_OCT26_NOV26","abs2_NOV26_JAN27","abs3_OCT26_JAN27"):
    dsp=fwd(SP[k],12); dp=fwd(price,12); rr=r
    m=~np.isnan(dsp)&~np.isnan(dp)&~np.isnan(rr)
    X=np.column_stack([np.ones(m.sum()),dp[m],rr[m]]); y=dsp[m]
    beta,res,rank,sv=np.linalg.lstsq(X,y,rcond=None)
    resid=y-X@beta; s2=resid@resid/(len(y)-3)
    cov=s2*np.linalg.inv(X.T@X); se=np.sqrt(np.diag(cov))
    t=beta/se
    print(f"  {k:22s} b(Δprice)={beta[1]:+.4f}(t={t[1]:+.2f})  c(RSI)={beta[2]:+.4f}(t={t[2]:+.2f})  R2={1-resid@resid/((y-y.mean())@(y-y.mean())):.3f}")

print("\n[N] 关键结构性事实: 月差 vs 价格水平 的稳定性")
for k in ("abs1_OCT26_NOV26","abs2_NOV26_JAN27","abs3_OCT26_JAN27"):
    s=SP[k]
    b,a=np.polyfit(price,s,1); pred=a+b*price
    r2=1-((s-pred)**2).sum()/((s-s.mean())**2).sum()
    print(f"  {k:22s} slope={b:+.4f} $/$(R2={r2:.3f})   同价区间70-80: corr={np.corrcoef(price[(price>=70)&(price<=80)],s[(price>=70)&(price<=80)])[0,1]:+.2f}")

json.dump(dict(events=[ts[i] for i in ev]),open(BASE+r"\results\rsi_ob_mde.json","w"),ensure_ascii=False,indent=1)
print("\n[saved]")
