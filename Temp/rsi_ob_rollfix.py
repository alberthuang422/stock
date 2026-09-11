# -*- coding: utf-8 -*-
"""修正版: 用真实滚动月差 RF = CLcurrent - CLnext (恒定1个月期限), RSI 打在当期合约 CLcurrent 上"""
import csv,json,numpy as np
B=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts"
def ld(p):
    r=list(csv.DictReader(open(p,encoding='utf-8-sig')))
    return {x['datetime']:float(x['close']) for x in r}
cur=ld(B+r"\4h\US.CLcurrent.csv"); nxt=ld(B+r"\4h\US.CLnext.csv")
c10=ld(B+r"\4h\US.CL2610.csv"); c11=ld(B+r"\4h\US.CL2611.csv")
ts=sorted(set(cur)&set(nxt))
C=np.array([cur[t] for t in ts]); N_=np.array([nxt[t] for t in ts])
RF=C-N_                      # 真实滚动近月月差 (恒定1个月)
FIX=np.array([c10[t] for t in ts])-np.array([c11[t] for t in ts])   # 固定 2610-2611 (旧口径)
def rsi(c,n=14):
    d=np.diff(c);up=np.where(d>0,d,0.);dn=np.where(d<0,-d,0.);o=np.full(len(c),np.nan)
    au=up[:n].mean();ad=dn[:n].mean();o[n]=100 if ad==0 else 100-100/(1+au/ad)
    for i in range(n+1,len(c)):
        au=(au*(n-1)+up[i-1])/n;ad=(ad*(n-1)+dn[i-1])/n;o[i]=100 if ad==0 else 100-100/(1+au/ad)
    return o
def fwd(x,h):
    o=np.full(len(x),np.nan);o[:-h]=x[h:]-x[:-h];return o
def bbd(cond,vals,block=12,nboot=5000,seed=5):
    rng=np.random.default_rng(seed);v=~np.isnan(vals);vals=vals[v];cond=cond[v]
    if cond.sum()<3: return np.nan,1.0
    obs=np.nanmean(vals[cond])-np.nanmean(vals);n=len(vals);nb=int(np.ceil(n/block));dif=[]
    for _ in range(nboot):
        s=rng.integers(0,n,size=nb);sel=np.concatenate([np.arange(x,min(x+block,n)) for x in s])[:n]
        vv=vals[sel];cc=cond[sel]
        if cc.sum()==0: continue
        dif.append(vv[cc].mean()-vv.mean())
    dif=np.array(dif);p=2*min((dif<=0).mean(),(dif>=0).mean());return obs,float(p)
def evs_cross(m,gap):
    out=[];last=-10**9;prev=False
    for i in range(len(m)):
        if m[i] and not prev and i-last>=gap: out.append(i);last=i
        prev=m[i]
    return out

rC=rsi(C,14)     # RSI 打在当期合约(真正的前月)
rO=rsi(FIX,14)   # 旧口径之下的 2610
print("RSI(14) on CLcurrent(真前月): >=70 bars =",int(np.nansum(rC>=70)),"| mean=%.1f max=%.1f"%(np.nanmean(rC),np.nanmax(rC)))
print("RSI(14) on 2610 (旧):          >=70 bars =",int(np.nansum(rO>=70)))
ev_new=evs_cross(rC>=70,12)
print("\n新事件清单(RSI on CLcurrent, 间隔>=12bar):")
for i in ev_new: print(f"   {ts[i]}  cur={C[i]:7.2f}  RF={RF[i]:+.2f}  2610-11={FIX[i]:+.2f}")
old=[4,51,70,123,129,135,139,160,182]
print("\n旧事件清单(RSI on 2610):", [ts[i] for i in old])

print("\n"+"="*96)
print("A'. 前向变化: 真实滚动月差 RF (事件=RSI on CLcurrent)")
print("="*96)
print(f"{'h':>4s}{'条件均值':>10s}{'基准均值':>10s}{'差':>9s}{'p':>8s}{'收敛率|OB':>10s}{'收敛率基准':>11s}")
for h in (1,2,3,6,12,24):
    d=fwd(RF,h);m=rC>=70
    o,p=bbd(m,d);v=~np.isnan(d)
    print(f"{h:>4d}{np.nanmean(d[m]):>10.3f}{np.nanmean(d):>10.3f}{o:>+9.3f}{p:>8.3f}{100*np.mean(d[m&v]<0):>9.1f}%{100*np.mean(d[v]<0):>10.1f}%")

print("\n"+"="*96)
print("B'. 9 次旧事件在新口径下的表现 (RF 真实滚动月差, +12bar=2日)")
print("="*96)
d12=fwd(RF,12)
print(f"{'日期':18s}{'cur':>8s}{'RF_真':>8s}{'2610-11':>9s}{'RF+12':>9s}{'FIX+12':>9s}{'符号一致':>9s}")
for i in old:
    a,b=d12[i],fwd(FIX,12)[i]
    print(f"{ts[i]:18s}{C[i]:8.2f}{RF[i]:8.2f}{FIX[i]:9.2f}{a:+9.2f}{b:+9.2f}{'是' if (a<0)==(b<0) else '否':>9s}")
print(f"\n  RF 口径: 收敛 {int((d12[old]<0).sum())}/9  均值={np.nanmean(d12[old]):+.3f}")
print(f"  FIX口径: 收敛 {int((fwd(FIX,12)[old]<0).sum())}/9  均值={np.nanmean(fwd(FIX,12)[old]):+.3f}")

print("\n"+"="*96)
print("C'. 事件平均路径 RF (9 旧事件)")
print("="*96)
for h in (1,3,6,9,12,18,24):
    v=[RF[i+h]-RF[i] for i in old if i+h<len(RF)]
    print(f"  h={h:<3d} 均值 ΔRF = {np.mean(v):+.3f}  收敛占比 {100*np.mean(np.array(v)<0):5.1f}%")

print("\n"+"="*96)
print("D'. 控价回归  ΔRF(h=12) ~ Δcur(h=12) + RSI_t")
print("="*96)
for lbl,rr in [("RSI on CLcurrent",rC),("RSI on 2610(旧)",rO)]:
    y=fwd(RF,12);x1=fwd(C,12);m=~np.isnan(y)&~np.isnan(x1)&~np.isnan(rr)
    X=np.column_stack([np.ones(m.sum()),x1[m],rr[m]]);yy=y[m]
    b,*_=np.linalg.lstsq(X,yy,rcond=None);res=yy-X@b
    s2=res@res/(len(yy)-3);se=np.sqrt(np.diag(s2*np.linalg.inv(X.T@X)));t=b/se
    r2=1-res@res/((yy-yy.mean())@(yy-yy.mean()))
    print(f"  {lbl:18s} b(Δcur)={b[1]:+.4f}(t={t[1]:+.2f})  c(RSI)={b[2]:+.5f}(t={t[2]:+.2f})  R2={r2:.3f}")
print("\n  [对照·旧口径] Δ(2610-2611) ~ Δ2610 + RSI:  c 为 +0.0046(t=+4.42) / +0.0027 / +0.0073")

print("\n"+"="*96)
print("E'. 结构性: RF 与价格的关系")
print("="*96)
bb,aa=np.polyfit(C,RF,1);pred=aa+bb*C
print(f"  corr(cur, RF)={np.corrcoef(C,RF)[0,1]:+.3f}  slope={bb:+.4f} $/$  R2={1-((RF-pred)**2).sum()/((RF-RF.mean())**2).sum():.3f}")
print(f"  旧固定口径 corr(2610, 2610-2611) = {np.corrcoef(FIX_F:=np.array([c10[t] for t in ts]),FIX)[0,1]:+.3f}")
json.dump(dict(ts=ts,RF=[round(float(v),3) for v in RF],C=[round(float(v),2) for v in C],
   rC=[None if np.isnan(v) else round(float(v),1) for v in rC],
   ev_new=[ts[i] for i in ev_new],ev_old=[ts[i] for i in old]),
   open(r"C:/Users/Administrator/Desktop/stock/results/rsi_ob_rolling.json","w"),ensure_ascii=False)
print("\n[saved] results/rsi_ob_rolling.json")
