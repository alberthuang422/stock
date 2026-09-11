# -*- coding: utf-8 -*-
import csv,json,numpy as np
B=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts"
def ld(p):
    r=list(csv.DictReader(open(p,encoding='utf-8-sig')))
    return {x['datetime']:float(x['close']) for x in r}
cur=ld(B+r"\4h\US.CLcurrent.csv"); nxt=ld(B+r"\4h\US.CLnext.csv")
c10=ld(B+r"\4h\US.CL2610.csv"); c11=ld(B+r"\4h\US.CL2611.csv")
ts=sorted(set(cur)&set(nxt)); n=len(ts)
C=np.array([cur[t] for t in ts]); N_=np.array([nxt[t] for t in ts])
P10=np.array([c10[t] for t in ts]); P11=np.array([c11[t] for t in ts])
RF=C-N_; FIX=P10-P11
def rsi(c,k=14):
    d=np.diff(c);up=np.where(d>0,d,0.);dn=np.where(d<0,-d,0.);o=np.full(len(c),np.nan)
    au=up[:k].mean();ad=dn[:k].mean();o[k]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(k+1,len(c)):
        au=(au*(k-1)+up[i-1])/k;ad=(ad*(k-1)+dn[i-1])/k;o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
def fwd(x,h):
    o=np.full(len(x),np.nan);o[:-h]=x[h:]-x[:-h];return o
def bbd(cond,vals,block=12,nboot=6000,seed=9):
    rng=np.random.default_rng(seed);v=~np.isnan(vals);vals=vals[v];cond=cond[v]
    if cond.sum()<3: return np.nan,1.0
    obs=np.nanmean(vals[cond])-np.nanmean(vals);m=len(vals);nb=int(np.ceil(m/block));dif=[]
    for _ in range(nboot):
        s=rng.integers(0,m,size=nb);sel=np.concatenate([np.arange(x,min(x+block,m)) for x in s])[:m]
        vv=vals[sel];cc=cond[sel]
        if cc.sum()==0: continue
        dif.append(vv[cc].mean()-vv.mean())
    dif=np.array(dif);return obs,float(2*min((dif<=0).mean(),(dif>=0).mean()))
def evx(m,gap):
    o=[];last=-10**9;prev=False
    for i in range(len(m)):
        if m[i] and not prev and i-last>=gap: o.append(i);last=i
        prev=m[i]
    return o
rC=rsi(C); r10=rsi(P10)
print("=== 事件侦测 ===")
print("RSI(14)≥70 bars:  当期合约 CLcurrent =",int(np.nansum(rC>=70)),"  |  2610 =",int(np.nansum(r10>=70)))
evC=evx(rC>=70,12); ev10=evx(r10>=70,12)
print(f"\n【新】RSI on CLcurrent 事件 {len(evC)} 个:")
for i in evC: print(f"   {ts[i]}  cur={C[i]:7.2f}  RF={RF[i]:+6.2f}  (cur-2610={C[i]-P10[i]:5.2f})")
print(f"\n【旧】RSI on 2610 事件 {len(ev10)} 个:")
for i in ev10: print(f"   {ts[i]}  cur={C[i]:7.2f}  RF={RF[i]:+6.2f}")

print("\n"+"="*100)
print("A'. 真实滚动月差 RF 的前向变化 (事件 = RSI on CLcurrent, 即真前月)")
print("="*100)
print(f"{'h':>4s}{'n_OB':>6s}{'条件均值':>10s}{'基准':>9s}{'差':>9s}{'p':>7s}{'收敛率|OB':>10s}{'基准收敛':>9s}")
for h in (1,2,3,6,12,18,24):
    d=fwd(RF,h);m=rC>=70;v=~np.isnan(d);o,p=bbd(m,d)
    print(f"{h:>4d}{int((m&v).sum()):>6d}{np.nanmean(d[m]):>10.3f}{np.nanmean(d):>9.3f}{o:>+9.3f}{p:>7.3f}{100*np.mean(d[m&v]<0):>9.1f}%{100*np.mean(d[v]<0):>8.1f}%")

print("\n"+"="*100)
print("B'. 对照: 同一批【旧】2610事件, 分别打在 RF(真) 与 FIX(旧) 上 (h=12)")
print("="*100)
dR=fwd(RF,12); dF=fwd(FIX,12)
print(f"{'日期':18s}{'cur':>8s}{'RF':>7s}{'FIX':>7s}{'ΔRF':>8s}{'ΔFIX':>8s}{'一致':>6s}")
for i in ev10:
    print(f"{ts[i]:18s}{C[i]:8.2f}{RF[i]:7.2f}{FIX[i]:7.2f}{dR[i]:+8.2f}{dF[i]:+8.2f}{'是' if (dR[i]<0)==(dF[i]<0) else '否':>6s}")
print(f"  RF : 收敛{int((dR[ev10]<0).sum())}/9  均值{np.nanmean(dR[ev10]):+.3f}")
print(f"  FIX: 收敛{int((dF[ev10]<0).sum())}/9  均值{np.nanmean(dF[ev10]):+.3f}")

print("\n"+"="*100)
print("C'. 事件平均路径 (两组事件 × 真实RF)")
print("="*100)
for lbl,ev in [("RSI on CLcurrent 事件",evC),("RSI on 2610 事件",ev10)]:
    print(f"\n  --- {lbl} (n={len(ev)}) ---")
    row="   h:      "; row2="   ΔRF:   "; row3="   收敛%: "
    for h in (1,3,6,9,12,18,24):
        v=np.array([RF[i+h]-RF[i] for i in ev if i+h<n])
        row+=f"{h:>8d}"; row2+=f"{v.mean():>+8.3f}"; row3+=f"{100*np.mean(v<0):>7.1f}%"
    print(row); print(row2); print(row3)

print("\n"+"="*100)
print("D'. 换月污染检验: 剔除距换月(每月~20日)±3bar内的事件")
print("="*100)
def near_roll(i,win=18):
    d=ts[i]; return any(d[5:7]!=ts[j][5:7] for j in range(max(0,i-win),min(n,i+win)))
evC2=[i for i in evC if not near_roll(i)]; ev102=[i for i in ev10 if not near_roll(i)]
print(f"  CLcurrent事件 剔除后 {len(evC2)}/{len(evC)};  2610事件 剔除后 {len(ev102)}/{len(ev10)}")
for lbl,ev in [("RSI@CLcurrent 净",evC2),("RSI@2610 净",ev102)]:
    if len(ev)<4: print(f"   {lbl}: 样本不足 {len(ev)}"); continue
    print(f"   {lbl}: ", end="")
    for h in (6,12,24):
        v=np.array([RF[i+h]-RF[i] for i in ev if i+h<n])
        print(f"h={h} ΔRF={v.mean():+.3f}(收敛{100*np.mean(v<0):.0f}%)  ",end="")
    print()

print("\n"+"="*100)
print("E'. 控价回归  ΔRF(h=12) ~ Δcur(h=12) + RSI_t")
print("="*100)
y=fwd(RF,12)
for lbl,rr,x1 in [("x1=Δcur, RSI@CLcurrent",rC,fwd(C,12)),("x1=Δcur, RSI@2610",r10,fwd(C,12)),
                  ("x1=Δ2610, RSI@2610",r10,fwd(P10,12))]:
    m=~np.isnan(y)&~np.isnan(x1)&~np.isnan(rr)
    X=np.column_stack([np.ones(m.sum()),x1[m],rr[m]]);yy=y[m]
    b,*_=np.linalg.lstsq(X,yy,rcond=None);res=yy-X@b
    s2=res@res/(len(yy)-3);se=np.sqrt(np.diag(s2*np.linalg.inv(X.T@X)));t=b/se
    print(f"  {lbl:26s} b={b[1]:+.4f}(t={t[1]:+.1f})  c(RSI)={b[2]:+.5f}(t={t[2]:+.2f})  R2={1-res@res/((yy-yy.mean())@(yy-yy.mean())):.3f}")
json.dump(dict(ts=ts,RF=[round(float(v),3) for v in RF],C=[round(float(v),2) for v in C],
  rC=[None if np.isnan(v) else round(float(v),1) for v in rC],
  evC=[ts[i] for i in evC],ev10=[ts[i] for i in ev10],evC2=[ts[i] for i in evC2],ev102=[ts[i] for i in ev102]),
  open(r"C:/Users/Administrator/Desktop/stock/results/rsi_ob_rolling.json","w"),ensure_ascii=False)
print("\n[saved]")
