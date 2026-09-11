import csv,json,numpy as np
B=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts"
def ld(p):
    r=list(csv.DictReader(open(p,encoding='utf-8-sig')))
    return {x['datetime']:float(x['close']) for x in r}
cur=ld(B+r"\4h\US.CLcurrent.csv");nxt=ld(B+r"\4h\US.CLnext.csv")
c10=ld(B+r"\4h\US.CL2610.csv");c11=ld(B+r"\4h\US.CL2611.csv")
ts=sorted(set(cur)&set(nxt));n=len(ts)
C=np.array([cur[t] for t in ts]);N_=np.array([nxt[t] for t in ts])
P10=np.array([c10[t] for t in ts]);P11=np.array([c11[t] for t in ts])
RF=C-N_;FIX=P10-P11;GAP=C-P10
def fwd(x,h):
    o=np.full(len(x),np.nan);o[:-h]=x[h:]-x[:-h];return o
OLD=['2026-03-12 17:00','2026-04-29 06:00','2026-05-17 22:00','2026-07-07 17:00','2026-07-13 14:00','2026-07-19 22:00','2026-07-22 06:00','2026-08-11 06:00','2026-09-01 06:00']
old=[ts.index(t) for t in OLD]
NEW=['2026-03-29 22:00','2026-04-02 10:00','2026-04-29 06:00','2026-05-17 22:00','2026-07-07 17:00','2026-07-13 14:00','2026-07-19 22:00','2026-07-22 06:00','2026-08-20 06:00','2026-09-01 06:00']
new=[ts.index(t) for t in NEW]
dR=fwd(RF,12);dF=fwd(FIX,12);dC12=fwd(C,12)
print("old idx",old); print("new idx",new)
print("EVD="+json.dumps([[ts[i][5:10],round(float(dR[i]),2),round(float(dF[i]),2)] for i in old],separators=(",",":")))
print("EVTS="+json.dumps([ts[i][5:10] for i in old]))
print("EVP="+json.dumps([round(i/4) for i in old]))
print("EVPnew="+json.dumps([round(i/4) for i in new]))
print("meanRF_old=%.3f meanFIX_old=%.3f convRF=%d convFIX=%d"%(np.nanmean(dR[old]),np.nanmean(dF[old]),(dR[old]<0).sum(),(dF[old]<0).sum()))
# 事件平均路径 RF
for lbl,ev in [("OLD9",old),("NEW10",new)]:
    row=[]
    for h in (1,3,6,9,12,18,24):
        v=np.array([RF[i+h]-RF[i] for i in ev if i+h<n]);row.append(round(float(v.mean()),3))
    print(f"PATH_{lbl}="+json.dumps(row))
step=4
def J(a): return json.dumps([None if np.isnan(v) else round(float(v),2) for v in a[::step]],separators=(",",":"))
print("L="+json.dumps([ts[i][5:10] for i in range(0,n,step)],separators=(",",":")))
print("GAP="+J(GAP)); print("RF="+J(RF)); print("FIX="+J(FIX))
print("MEANS="+json.dumps(dict(gap_max=round(float(GAP.max()),1),gap_p80=round(float(np.percentile(GAP,80)),1),
  rf=round(float(RF.mean()),2),fix=round(float(FIX.mean()),2),rfsd=round(float(RF.std()),2),fixsd=round(float(FIX.std()),2),
  rfmax=round(float(RF.max()),2),fixmax=round(float(FIX.max()),2))))
# 每个旧事件: 当时的 cur/next/RF/FIX
print("TBL="+json.dumps([[ts[i][5:10],round(float(C[i]),2),round(float(N_[i]),2),round(float(RF[i]),2),round(float(FIX[i]),2),round(float(GAP[i]),2)] for i in old],separators=(",",":")))
