# -*- coding: utf-8 -*-
"""逐事件明细 + 三种月差口径的同事件对照 + 日线扩展样本"""
import csv, json, numpy as np, os
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
D1={m:{r["time"]:float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 1D.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
def fu(tf,n):
    return {r["datetime"]:float(r["close"]) for r in csv.DictReader(open(os.path.join(FU,tf,f"US.{n}.csv"),encoding="utf-8-sig"))}
F10,F11,FC,FN=fu("4h","CL2610"),fu("4h","CL2611"),fu("4h","CLcurrent"),fu("4h","CLnext")
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

# ---- 真当期月差 (4h): K-M [3/20,4/21] + M-N [4/21,5/19] ----
def seg(a,b,lm,t0,t1):
    ts=sorted(set(D[a])&set(D[b])); ts=[t for t in ts if t0<=t[:10]<=t1]
    return ts,np.array([D[a][t]-D[b][t] for t in ts]),rsi(np.array([D[lm][t] for t in ts]))
S1=seg("K","M","K","2026-03-20","2026-04-21"); S2=seg("M","N","M","2026-04-21","2026-05-19")
tsT=S1[0]+S2[0]; spT=np.concatenate([S1[1],S2[1]]); rT=np.concatenate([S1[2],S2[2]])
ev=evx(np.nan_to_num(rT,nan=-1)>=70,12)
print("="*118)
print("【A】真当期月差：5 次超买事件逐笔 (窗口 2026-03-20 ~ 05-19, 258bar)")
print("="*118)
print(f"{'事件':18s}{'前月':>7s}{'RSI':>6s}{'真月差':>8s}{'前月价':>8s}{'Δ价+12':>9s}{'Δ月差+3':>9s}{'Δ月差+6':>9s}{'Δ月差+12':>10s}{'Δ月差+24':>10s}")
for i in ev:
    leg="K-M" if tsT[i]<"2026-04-21" else "M-N"
    px=D["K"][tsT[i]] if leg=="K-M" else D["M"][tsT[i]]
    g=lambda h: (spT[i+h]-spT[i]) if i+h<len(spT) else np.nan
    dp=(D["K" if leg=="K-M" else "M"][tsT[min(i+12,len(tsT)-1)]]-px)
    print(f"{tsT[i][5:16]:18s}{leg:>7s}{rT[i]:>6.1f}{spT[i]:>8.2f}{px:>8.2f}{dp:>+9.2f}{g(3):>+9.2f}{g(6):>+9.2f}{g(12):>+10.2f}{g(24):>+10.2f}")
print()
d12=np.array([spT[i+12]-spT[i] for i in ev if i+12<len(spT)])
print(f"  事件 Δ(spread,+12bar): 负(收敛){int((d12<0).sum())}/{len(d12)}  均值{d12.mean():+.3f}")
print(f"  逐笔: "+"  ".join(f"{v:+.2f}" for v in d12))

# ---- B. 同一批事件 × 三种口径 ----
print()
print("="*118)
print("【B】同一批事件 × 三种月差口径 (h=12bar = 2日)")
print("="*118)
o_ts=sorted(F10); SPO=np.array([F10[t]-F11[t] for t in o_ts])
o_ts2=sorted(FC); SPR=np.array([FC[t]-FN[t] for t in o_ts2])
print(f"{'事件':18s}{'真(拼接口径)':>13s}{'旧2610-2611':>13s}{'Futu滚动RF':>12s}{'真-旧':>9s}")
diffs=[]
for i in ev:
    e=tsT[i]
    j=next((k for k,t in enumerate(o_ts) if t[:13]==e[:13]),None)
    j2=next((k for k,t in enumerate(o_ts2) if t[:13]==e[:13]),None)
    a=(spT[i+12]-spT[i]) if i+12<len(spT) else np.nan
    b=(SPO[j+12]-SPO[j]) if (j is not None and j+12<len(SPO)) else np.nan
    c=(SPR[j2+12]-SPR[j2]) if (j2 is not None and j2+12<len(SPR)) else np.nan
    if not (np.isnan(a) or np.isnan(b)): diffs.append(a-b)
    print(f"{e[5:16]:18s}{a:>+13.2f}{(f'{b:+.2f}' if not np.isnan(b) else 'n/a'):>13s}{(f'{c:+.2f}' if not np.isnan(c) else 'n/a'):>12s}{a-b:>+9.2f}")
diffs=np.array(diffs)
print(f"  → 真口径均值 {np.nanmean([spT[i+12]-spT[i] for i in ev if i+12<len(spT)]):+.3f} vs 旧口径均值 "
      f"{np.nanmean([SPO[j+12]-SPO[j] for i in ev for j in [next((k for k,t in enumerate(o_ts) if t[:13]==tsT[i][:13]),None)] if j is not None and j+12<len(SPO)]):+.3f}"
      f"  | 平均绝对分歧 {np.abs(diffs).mean():.2f}  符号一致 {int((diffs*np.sign(diffs)).size and sum(1 for x in diffs if True)) }")

# ---- C. 日线扩展: 更长的『真当期月差』序列 ----
print()
print("="*118)
print("【C】日线扩展: 同一本质问题在 1D 上的更大样本 (RSI=14 日)")
print("="*118)
PAIRS=[("K","M","K","2026-01-01","2026-04-21","K-M"),
       ("M","N","M","2025-08-01","2026-05-19","M-N"),
       ("N","U","N","2025-06-01","2026-06-22","N-U")]
for a,b,lm,t0,t1,lbl in PAIRS:
    ts=sorted(set(D1[a])&set(D1[b])); ts=[t for t in ts if t0<=t<=t1]
    sp=np.array([D1[a][t]-D1[b][t] for t in ts]); r=rsi(np.array([D1[lm][t] for t in ts]))
    evd=evx(np.nan_to_num(r,nan=-1)>=70,5)
    d={}
    for h in (1,3,5,10):
        v=np.array([sp[i+h]-sp[i] for i in evd if i+h<len(sp)])
        base=np.nanmean(np.diff(sp,h)) if h<len(sp) else np.nan
        d[h]=(v.mean(),100*np.mean(v<0),base)
    print(f"  {lbl}: n={len(ts)}d  {ts[0]}~{ts[-1]}  RSI>=70事件 {len(evd)} 个  spread mean={sp.mean():.2f}")
    print(f"     "+"  ".join(f"h={h}: Δ={d[h][0]:+.2f} 收敛{d[h][1]:.0f}% (基准Δ{d[h][2]:+.3f})" for h in (1,3,5,10)))
json.dump(dict(tsT=tsT,spT=[round(float(v),3) for v in spT],rT=[None if np.isnan(v) else round(float(v),1) for v in rT],
               ev=[tsT[i] for i in ev],evpos=[i for i in ev]),
          open(r"C:/Users/Administrator/Desktop/stock/results/cl_fix_detail.json","w"),ensure_ascii=False)
print("\n[done]")
