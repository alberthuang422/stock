# -*- coding: utf-8 -*-
import csv,json,numpy as np,os
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
F=lambda n:{r["datetime"]:float(r["close"]) for r in csv.DictReader(open(os.path.join(FU,f"US.{n}.csv"),encoding="utf-8-sig"))}
F10,F11=F("CL2610"),F("CL2611")
# 日度取样: 每天最后一个 bar
def daily(ts,val):
    d={}
    for t,v in zip(ts,val): d[t[:10]]=v
    return d
KM_ts=sorted(set(D["K"])&set(D["M"])); KMd=daily(KM_ts,[D["K"][t]-D["M"][t] for t in KM_ts])
MN_ts=sorted(set(D["M"])&set(D["N"])); MNd=daily(MN_ts,[D["M"][t]-D["N"][t] for t in MN_ts])
P_ts=sorted(set(F10)&set(F11)); Pd=daily(P_ts,[F10[t]-F11[t] for t in P_ts])
days=sorted(d for d in set(list(KMd)+list(MNd)) if "2026-02-09"<=d<="2026-05-19")
print("L="+json.dumps([d[5:] for d in days]))
print("KM="+json.dumps([round(KMd[d],2) if (d in KMd and d<="2026-04-21") else None for d in days]))
print("MN="+json.dumps([round(MNd[d],2) if (d in MNd and d>="2026-04-21") else None for d in days]))
print("PR="+json.dumps([round(Pd[d],2) if d in Pd else None for d in days]))
# 事件
EV=json.load(open(r"C:/Users/Administrator/Desktop/stock/results/cl_fix_events.json"))
print("EV="+json.dumps([[e["t"][5:10],e["pair"],e["dte"],round(e["sp"],2),
    None if e["d6"] is None or (isinstance(e["d6"],float) and np.isnan(e["d6"])) else round(e["d6"],2),
    None if e["d12"] is None or (isinstance(e["d12"],float) and np.isnan(e["d12"])) else round(e["d12"],2),
    None if e["d24"] is None or (isinstance(e["d24"],float) and np.isnan(e["d24"])) else round(e["d24"],2)] for e in EV]))
import math
def agg(k): 
    v=np.array([e[k] for e in EV if e[k] is not None and not (isinstance(e[k],float) and math.isnan(e[k]))]); return v
print("AGG="+json.dumps({h:[round(float(agg(k).mean()),3),round(float(100*np.mean(agg(k)<0)),1),len(agg(k))] for h,k in ((6,'d6'),(12,'d12'),(24,'d24'),(48,'d48'))}))
# 4/2 案例: K-M 路径 i..i+48 (bar)
i=KM_ts.index([t for t in KM_ts if t[:13]=="2026-04-02 18:00"][0])
seg=[round(D["K"][t]-D["M"][t],2) for t in KM_ts[i-6:i+49]]
print("CASE_TS="+json.dumps([t[5:16] for t in KM_ts[i-6:i+49]]))
print("CASE="+json.dumps(seg))
# 同事件旧代理 h=12
o_ts=sorted(F10); SPO=np.array([F10[t]-F11[t] for t in o_ts])
old=[]
for e in EV:
    if e["pair"]!="KM": continue
    j=next((k for k,t in enumerate(o_ts) if t[:13]==e["t"][:13]),None)
    old.append(round(float(SPO[j+12]-SPO[j]),2) if (j is not None and j+12<len(SPO)) else None)
print("OLD_KM12="+json.dumps(old))
# 相关: 真 vs 旧 (变动)
for lab,ts_,sp_ in (("KM",KM_ts,[D["K"][t]-D["M"][t] for t in KM_ts]),("MN",MN_ts,[D["M"][t]-D["N"][t] for t in MN_ts])):
    c=[t for t in ts_ if t in F10 and t in F11]
    a=np.array([sp_[ts_.index(t)] for t in c]); b=np.array([F10[t]-F11[t] for t in c])
    print(f"CORR_{lab}="+json.dumps(dict(n=len(c),lv=round(float(np.corrcoef(a,b)[0,1]),3),chg=round(float(np.corrcoef(np.diff(a),np.diff(b))[0,1]),3),
        tm=round(float(a.mean()),2),om=round(float(b.mean()),2),tsd=round(float(a.std()),2),osd=round(float(b.std()),2))))
