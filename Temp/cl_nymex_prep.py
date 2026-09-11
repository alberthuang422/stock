# -*- coding: utf-8 -*-
"""NYMEX 单合约数据: 载入/对齐/构建真实日历月差, 并与 Futu 滚动月差交叉验证"""
import csv, json, numpy as np, os
DL=r"C:/Users/Administrator/Downloads"
OUT=r"C:/Users/Administrator/Desktop/stock/results"
MON={"K":"2605","M":"2606","N":"2607","U":"2609"}

def norm_4h(t):
    """把 +08:00 时间戳统一到 ET 网格: EST(03/07/11/15/19/23) -> -1h"""
    date, tm = t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{date} {hh:02d}:00"

def load4h(m):
    p=os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv")
    out={}
    for r in csv.DictReader(open(p,encoding="utf-8-sig")):
        out[norm_4h(r["time"])]=(float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]))
    return out

def load1d(m):
    p=os.path.join(DL,f"NYMEX_DL_CL{m}2026, 1D.csv")
    out={}
    for r in csv.DictReader(open(p,encoding="utf-8-sig")):
        out[r["time"]]=(float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]))
    return out

D4={m:load4h(m) for m in MON}
D1={m:load1d(m) for m in MON}

# ---- 1. 4h 两两交集覆盖 ----
print("="*104)
print("【1】4h 两两合约交集覆盖 (归一化到 ET 网格后)")
print("="*104)
keys=list(D4); print(f"{'pair':14s}{'bars':>7s}{'起':>18s}{'止':>18s}{'mean':>9s}{'sd':>8s}{'min':>8s}{'max':>8s}")
PAIRS=[("K","M"),("M","N"),("N","U"),("K","N"),("M","U"),("K","U")]
S4={}
for a,b in PAIRS:
    ts=sorted(set(D4[a])&set(D4[b]))
    s=np.array([D4[a][t][3]-D4[b][t][3] for t in ts])
    S4[f"{a}{b}"]=(ts,s)
    print(f"{a}-{b}({MON[a]}-{MON[b]}){len(ts):>7d}{ts[0]:>18s}{ts[-1]:>18s}{s.mean():>9.3f}{s.std():>8.3f}{s.min():>8.3f}{s.max():>8.3f}")

# ---- 2. 活跃度过滤: 两腿都“非陈旧” ----
print()
print("="*104)
print("【2】活跃度过滤后 (两腿收盘均较上一bar变动, 或当bar有真实振幅)")
print("="*104)
def active_series(a,b,bars):
    ts=sorted(set(D4[a])&set(D4[b]))
    keep=[]
    for i,t in enumerate(ts):
        if i==0: continue
        p=ts[i-1]
        ka=abs(D4[a][t][3]-D4[a][p][3])>0.005; kb=abs(D4[b][t][3]-D4[b][p][3])>0.005
        ra=D4[a][t][1]-D4[a][t][2]>0.02; rb=D4[b][t][1]-D4[b][t][2]>0.02
        if (ka or ra) and (kb or rb): keep.append(t)
    s=np.array([D4[a][t][3]-D4[b][t][3] for t in keep])
    return keep,s
print(f"{'pair':14s}{'活跃bars':>9s}{'覆盖起点':>18s}{'覆盖终点':>18s}{'mean':>9s}{'sd':>8s}{'max':>8s}")
ACT4={}
for a,b in PAIRS:
    ts,s=active_series(a,b,None); ACT4[f"{a}{b}"]=(ts,s)
    print(f"{a}-{b}{len(ts):>9d}{ts[0]:>18s}{ts[-1]:>18s}{s.mean():>9.3f}{s.std():>8.3f}{s.max():>8.3f}")

# ---- 3. 真前月窗口 (M1-M2 = 前月与次月) ----
print()
print("="*104)
print("【3】合约到期序列 → 前月归属 (CL 到期=交割月前月25日前3个交易日)")
print("="*104)
last={m:sorted(D1[m])[-1] for m in MON}
for m in MON: print(f"  CL{m}2026 ({MON[m]}) 数据末值 {last[m]}  1D行数={len(D1[m])}")

# ---- 4. 交叉验证: 与 Futu CLcurrent/CLnext 滚动月差对比 ----
print()
print("="*104)
print("【4】交叉验证: 本数据集 M-N 月差  vs  Futu CLcurrent-CLnext (4h)")
print("="*104)
FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
def load_fu(name):
    p=os.path.join(FU,name)
    out={}
    for r in csv.DictReader(open(p,encoding="utf-8-sig")):
        t=r["datetime"]; out[t[:13]+":00"]=float(r["close"])
    return out
try:
    fc=load_fu("US.CLcurrent.csv"); fn=load_fu("US.CLnext.csv")
    fk=load_fu("US.CL2610.csv"); fm=load_fu("US.CL2611.csv")
    ts=sorted(set(fc)&set(fn)&set(D4["M"])&set(D4["N"]))
    print(f"  共同bar={len(ts)}  区间 {ts[0]} ~ {ts[-1]}")
    print(f"  {'时间':18s}{'Futu cur':>10s}{'NYMEX M(2606)':>15s}{'差':>8s} | {'Futu next':>10s}{'NYMEX N(2607)':>15s}{'差':>8s} | {'RF_futu':>8s}{'M-N':>8s}")
    step=max(1,len(ts)//12)
    for i in list(range(0,len(ts),step))+[len(ts)-1]:
        t=ts[i]
        print(f"  {t:18s}{fc[t]:>10.2f}{D4['M'][t][3]:>15.2f}{fc[t]-D4['M'][t][3]:>8.2f} | {fn[t]:>10.2f}{D4['N'][t][3]:>15.2f}{fn[t]-D4['N'][t][3]:>8.2f} | {fc[t]-fn[t]:>8.2f}{D4['M'][t][3]-D4['N'][t][3]:>8.2f}")
    d1=np.array([fc[t]-D4['M'][t][3] for t in ts]); d2=np.array([fn[t]-D4['N'][t][3] for t in ts])
    print(f"\n  对齐误差: cur vs M26 平均{d1.mean():+.3f} 最大{abs(d1).max():.3f} | next vs N26 平均{d2.mean():+.3f} 最大{abs(d2).max():.3f}")
except Exception as e:
    print("  Futu 对齐失败:",e)

json.dump({"note":"prep only"},open(OUT+r"\cl_nymex_prep.json","w"))
print("\n[done]")
