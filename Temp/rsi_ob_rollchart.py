import csv,json,numpy as np
B=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts"
def ld(p):
    r=list(csv.DictReader(open(p,encoding='utf-8-sig')))
    return {x['datetime']:float(x['close']) for x in r}
cur=ld(B+r"\4h\US.CLcurrent.csv"); nxt=ld(B+r"\4h\US.CLnext.csv")
c10=ld(B+r"\4h\US.CL2610.csv"); c11=ld(B+r"\4h\US.CL2611.csv")
ts=sorted(set(cur)&set(nxt)); n=len(ts)
C=np.array([cur[t] for t in ts]);N_=np.array([nxt[t] for t in ts])
P10=np.array([c10[t] for t in ts]);P11=np.array([c11[t] for t in ts])
RF=C-N_;FIX=P10-P11;GAP=C-P10
def fwd(x,h):
    o=np.full(len(x),np.nan);o[:-h]=x[h:]-x[:-h];return o
old=[4,51,70,123,129,135,139,160,182]
dR=fwd(RF,12);dF=fwd(FIX,12)
step=4
def J(a): return json.dumps([None if (isinstance(v,float) and np.isnan(v)) else round(float(v),3) for v in a[::step]],separators=(",",":"))
print("L="+json.dumps([ts[i][5:10] for i in range(0,n,step)],separators=(",",":")))
print("GAP="+J(GAP))
print("RF="+J(RF))
print("FIX="+J(FIX))
print("EVD="+json.dumps([[ts[i][5:10],round(float(dR[i]),2),round(float(dF[i]),2)] for i in old],separators=(",",":")))
print("EVTS="+json.dumps([ts[i][5:10] for i in old]))
print("EVP="+json.dumps([round(i/step) for i in old]))
print("STAT="+json.dumps(dict(rf_mean=round(float(RF.mean()),2),rf_min=round(float(RF.min()),2),rf_max=round(float(RF.max()),2),
  rf_sd=round(float(RF.std()),2),fix_mean=round(float(FIX.mean()),2),fix_max=round(float(FIX.max()),2),fix_sd=round(float(FIX.std()),2),
  gap_max=round(float(GAP.max()),2),gap_mean_apr=round(float(GAP[190:300].mean()),2))))
