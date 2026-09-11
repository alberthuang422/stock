import json,csv,numpy as np
B=r"C:/Users/Administrator/Desktop/stock"
rows=list(csv.DictReader(open(B+r"\data\cl_contracts\spread\cl_spread_4h.csv",encoding="utf-8-sig")))
ts=[r["ts"] for r in rows];price=np.array([float(r["CL2610"]) for r in rows])
SP2=np.array([float(r["abs2_NOV26_JAN27"]) for r in rows]);N=len(rows)
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
step=4
L=[ts[i][5:10]+" "+ts[i][11:13] for i in range(0,N,step)]
P=[round(float(price[i]),2) for i in range(0,N,step)]
S=[round(float(SP2[i]),3) for i in range(0,N,step)]
EVP=[round(i/step) for i in ev]
print("L="+json.dumps(L,separators=(",",":")))
print("P="+json.dumps(P,separators=(",",":")))
print("S="+json.dumps(S,separators=(",",":")))
print("EVP="+json.dumps(EVP))
print("EVD="+json.dumps([[ts[i][5:10],round(float(price[i]),2),round(float(SP2[i]),2),
   round(float(price[min(i+12,N-1)]-price[i]),2),round(float(SP2[min(i+12,N-1)]-SP2[i]),2)] for i in ev],separators=(",",":")))
p=json.load(open(B+r"\results\rsi_ob_chartdata.json"))["paths"]
print("PA="+json.dumps(p["abs1_OCT26_NOV26"],separators=(",",":")))
print("PB="+json.dumps(p["abs2_NOV26_JAN27"],separators=(",",":")))
print("PC="+json.dumps(p["abs3_OCT26_JAN27"],separators=(",",":")))
