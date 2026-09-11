# -*- coding: utf-8 -*-
"""稳健性: 多RSI周期/阈值 + 基准率 + 事件清单 + W2子样本检验 + price-orthogonal"""
import csv, json
import numpy as np

BASE = r"C:\Users\Administrator\Desktop\stock"
SPREAD = BASE + r"\data\cl_contracts\spread\cl_spread_4h.csv"
rows = list(csv.DictReader(open(SPREAD, encoding="utf-8-sig")))
ts = [r["ts"] for r in rows]
price = np.array([float(r["CL2610"]) for r in rows])
SP = {k: np.array([float(r[k]) for r in rows]) for k in rows[0] if k.startswith("abs")}
N = len(ts)

def rsi(close, n=14):
    d = np.diff(close); up = np.where(d>0,d,0.0); dn = np.where(d<0,-d,0.0)
    out = np.full(len(close), np.nan)
    au = up[:n].mean(); ad = dn[:n].mean()
    out[n] = 100.0 if ad==0 else 100-100/(1+au/ad)
    for i in range(n+1,len(close)):
        au = (au*(n-1)+up[i-1])/n; ad = (ad*(n-1)+dn[i-1])/n
        out[i] = 100.0 if ad==0 else 100-100/(1+au/ad)
    return out

def fwd(x,h):
    o = np.full(len(x), np.nan); o[:-h] = x[h:]-x[:-h]; return o

print("="*90)
print("F. 基准率: 无条件 P(Δ<0) 与 条件(RSI>=70) P(Δ<0)   [abs3_OCT26_JAN27 = 用户2611-2701同类]")
print("="*90)
KV = {"abs1_OCT26_NOV26":"+1 近端 M1-M2","abs2_NOV26_JAN27":"+2 (2611-2701)","abs3_OCT26_JAN27":"+3 M1-M4"}
r14 = rsi(price,14)
print(f"{'spread':22s}{'h':>4s}{'P(收敛)基准':>12s}{'P(收敛)|OB':>12s}{'n_base':>8s}{'n_OB':>7s}")
for k in KV:
    for h in (3,6,12,24):
        d = fwd(SP[k],h); v=~np.isnan(d); m=(r14>=70)
        pb = np.mean(d[v]<0)*100
        mv = v&m
        pc = np.mean(d[mv]<0)*100 if mv.sum() else np.nan
        print(f"{k:22s}{h:>4d}{pb:11.1f}%{pc:11.1f}%{int(v.sum()):>8d}{int(mv.sum()):>7d}")

print("\n"+"="*90)
print("G. 多参数稳健性: 条件均值-基准均值 (单位 $, h=12 即 2 个交易日)")
print("="*90)
print(f"{'RSI周期':>8s}{'阈值':>6s}{'OB bar数':>9s}" + "".join([f"{k.split('_')[0][-2:]:>12s}" for k in KV]))
GRID=[]
for n in (9,14,21):
    rr = rsi(price,n)
    for th in (60,65,70,75):
        line=f"{n:>8d}{th:>6d}{int(np.nansum(rr>=th)):>9d}"
        rec={"n":n,"th":th,"bars":int(np.nansum(rr>=th))}
        for k in KV:
            d=fwd(SP[k],12); m=rr>=th
            diff = np.nanmean(d[m])-np.nanmean(d)
            rec[k]=float(diff)
            line += f"{diff:+12.3f}"
        GRID.append(rec)
        print(line)
print("  (负 = 超买后月差相对收敛; 正 = 相对扩张)")

print("\n"+"="*90)
print("H. 事件清单 RSI(14)>=70 (非重叠, 间隔>=12bar=2日)")
print("="*90)
ev=[];last=-999;prev=False
for i in range(N):
    if r14[i]>=70 and not prev and i-last>=12:
        ev.append(i); last=i
    prev = r14[i]>=70
print(f"{'#':>3s} {'bar时刻':18s} {'价格':>8s} {'RSI':>6s} {'+1价Δ':>8s} {'+3价Δ':>8s} {'+12价Δ':>8s} | {'+12 2611-2701Δ':>15s}")
d3=fwd(SP['abs2_NOV26_JAN27'],3); d1p=fwd(price,1); d3p=fwd(price,3); d12p=fwd(price,12)
d12=fwd(SP['abs2_NOV26_JAN27'],12)
for j,i in enumerate(ev):
    print(f"{j+1:>3d} {ts[i]:18s} {price[i]:8.2f} {r14[i]:6.1f} {d1p[i]:+8.3f} {d3p[i]:+8.3f} {d12p[i]:+8.3f} | {d12[i]:+15.3f}")

print("\n"+"="*90)
print("I. W2(7/10后) 子样本: RSI>=70 -> Δspread(h=12), 含 block bootstrap p")
print("="*90)
CUT=next(i for i,t in enumerate(ts) if t>="2026-07-10")
def bbd(cond, vals, block=12, nboot=5000, seed=11):
    rng=np.random.default_rng(seed)
    v=~np.isnan(vals); vals=vals[v]; cond=cond[v]
    obs=np.nanmean(vals[cond])-np.nanmean(vals); n=len(vals); nb=int(np.ceil(n/block))
    diffs=[]
    for _ in range(nboot):
        s=rng.integers(0,n,size=nb)
        sel=np.concatenate([np.arange(x,min(x+block,n)) for x in s])[:n]
        vv=vals[sel]; cc=cond[sel]
        if cc.sum()==0: continue
        diffs.append(vv[cc].mean()-vv.mean())
    diffs=np.array(diffs)
    p=2*min((diffs<=0).mean(),(diffs>=0).mean())
    return obs,float(p)
for name,sl in [("W1 3/10-7/10",slice(0,CUT)),("W2 7/10-9/09",slice(CUT,None))]:
    pr=price[sl]; rr=rsi(pr,14)
    print(f"\n {name}  n={len(pr)}  RSI>=70: {int(np.nansum(rr>=70))}bar")
    for k in KV:
        sp=SP[k][sl]; d=fwd(sp,12); m=rr>=70
        if np.nansum(m)<3: print(f"   {k:22s} 样本不足"); continue
        o,p=bbd(m,d)
        print(f"   {k:22s} 条件={np.nanmean(d[m]):+7.3f} 基准={np.nanmean(d):+7.3f} 差={o:+7.3f} p={p:.3f}")

print("\n"+"="*90)
print("J. 月差自身RSI超买 -> 前向变化 的 p 值 (含W2)")
print("="*90)
for k in KV:
    for name,sl in [("全样本",slice(0,None)),("W2",slice(CUT,None))]:
        sp=SP[k][sl]; sr=rsi(sp,14); d=fwd(sp,12); m=sr>=70
        if np.nansum(m)<5: print(f"  {k:22s} {name} 样本不足({int(np.nansum(m))})"); continue
        o,p=bbd(m,d)
        print(f"  {k:22s} {name:6s} 条件={np.nanmean(d[m]):+7.3f} 基准={np.nanmean(d):+7.3f} 差={o:+7.3f} p={p:.3f} ({int(np.nansum(m))}bar)")

json.dump(dict(grid=GRID,events=[ts[i] for i in ev]),open(BASE+r"\results\rsi_ob_robust.json","w"),ensure_ascii=False,indent=1)
print("\n[saved] results/rsi_ob_robust.json")
