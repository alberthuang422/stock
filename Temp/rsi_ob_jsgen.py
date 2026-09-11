import json,csv,numpy as np
B=r"C:/Users/Administrator/Desktop/stock"
rows=list(csv.DictReader(open(B+r"\data\cl_contracts\spread\cl_spread_4h.csv",encoding="utf-8-sig")))
price=np.array([float(r["CL2610"]) for r in rows]);N=len(rows)
def rsi(c,n=14):
    d=np.diff(c);up=np.where(d>0,d,0.);dn=np.where(d<0,-d,0.);o=np.full(len(c),np.nan)
    au=up[:n].mean();ad=dn[:n].mean();o[n]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(n+1,len(c)):
        au=(au*(n-1)+up[i-1])/n;ad=(ad*(n-1)+dn[i-1])/n;o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
r=rsi(price,14)
ev=[];last=-999;prev=False
for i in range(N):
    if r[i]>=70 and not prev and i-last>=12: ev.append(i);last=i
    prev=r[i]>=70
d=json.load(open(B+r"\results\rsi_ob_chartdata.json"));step=d["step"];ts=d["ts"]
def arr(a): return "["+",".join(("null" if v is None else f"{v}") for v in a)+"]"
print("LABELS="+arr([t[5:13] for t in ts]))
print("PRICE="+arr(d["price"]))
print("SP2="+arr(d["sp2"]))
print("EVPOS="+str([round(i/step) for i in ev]))
print("EVTS="+str([[i]+[t.split()[0][5:],t.split()[1]] for i,t in zip([round(x/step) for x in ev],[rows[x]["ts"] for x in ev])]))
print("EVPRICE="+str(d["ev_price"]))
print("EVSP="+str(d["ev_sp2"]))
print("EVDP="+str(d["ev_dp"]))
print("EVDS="+str(d["ev_ds"]))
p=d["paths"]
print("PATH1="+arr(p["abs1_OCT26_NOV26"]))
print("PATH2="+arr(p["abs2_NOV26_JAN27"]))
print("PATH3="+arr(p["abs3_OCT26_JAN27"]))
print("BASE="+json.dumps(d["base"]))
