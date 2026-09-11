# -*- coding: utf-8 -*-
import csv,json,numpy as np,os,math
DL=r"C:/Users/Administrator/Downloads"; FU=r"C:/Users/Administrator/Desktop/stock/data/cl_contracts/4h"
def norm(t):
    d,tm=t.split("T"); hh=int(tm[:2])
    if hh in (3,7,11,15,19,23): hh-=1
    return f"{d} {hh:02d}:00"
D={m:{norm(r["time"]):float(r["close"]) for r in csv.DictReader(open(os.path.join(DL,f"NYMEX_DL_CL{m}2026, 240.csv"),encoding="utf-8-sig"))} for m in "KMNU"}
F=lambda n:{r["datetime"]:float(r["close"]) for r in csv.DictReader(open(os.path.join(FU,f"US.{n}.csv"),encoding="utf-8-sig"))}
F10,F11=F("CL2610"),F("CL2611")
KM_ts=sorted(set(D["K"])&set(D["M"])); MN_ts=sorted(set(D["M"])&set(D["N"]))
def daily(ts,val):
    d={}
    for t,v in zip(ts,val): d[t[:10]]=v
    return d
KMd=daily(KM_ts,[D["K"][t]-D["M"][t] for t in KM_ts]); MNd=daily(MN_ts,[D["M"][t]-D["N"][t] for t in MN_ts])
P_ts=sorted(set(F10)&set(F11)); Pd=daily(P_ts,[F10[t]-F11[t] for t in P_ts])
days=sorted(d for d in set(list(KMd)+list(MNd)) if "2026-02-09"<=d<="2026-05-19")
KM=[KMd[d] if (d in KMd and d<="2026-04-21") else None for d in days]
MN=[MNd[d] if (d in MNd and d>="2026-04-21") else None for d in days]
PR=[Pd[d] if d in Pd else None for d in days]
N=len(days)
X0,X1=62,656; W=X1-X0
def x(i): return X0+W*i/(N-1)
P1T,P1B=44,214; YMAX=17.0
def y1(v): return P1B-(v/YMAX)*(P1B-P1T)
def path(vals):
    seg=[];cur=[]
    for i,v in enumerate(vals):
        if v is None:
            if len(cur)>1: seg.append(cur)
            cur=[]
        else: cur.append((x(i),y1(v)))
    if len(cur)>1: seg.append(cur)
    return " ".join("M"+" L".join(f"{a:.0f},{b:.0f}" for a,b in s) for s in seg)
def dots(vals,color,r=2.2,shape="c"):
    out=[]
    for i,v in enumerate(vals):
        if v is None: continue
        out.append(f'<circle cx="{x(i):.0f}" cy="{y1(v):.0f}" r="{r}" fill="{color}"/>')
    return "".join(out)
ev=json.load(open(r"C:/Users/Administrator/Desktop/stock/results/cl_fix_events.json"))
mark=[]
for e in ev:
    if e["pair"] not in ("KM","MN"): continue
    d=e["t"][:10]
    if d not in days: continue
    i=days.index(d)
    v=KM[i] if e["pair"]=="KM" else MN[i]
    if v is None: continue
    mark.append((i,v,e["sp"],e["pair"]))
mk="".join(f'<path d="M{x(i):.1f},{y1(v)-5.5:.1f} l4.6,7.4 h-9.2 z" fill="#F0E442"/>' for i,v,_,_ in mark)
# 案例
i0=[k for k,t in enumerate(KM_ts) if t[:10]=="2026-04-02"][-1]
C=[D["K"][t]-D["M"][t] for t in KM_ts[i0-6:i0+49]]; CT=[t for t in KM_ts[i0-6:i0+49]]
P3T,P3B=404,556; CMIN,CMAX=2.0,17.0
def y3(v): return P3B-(v-CMIN)/(CMAX-CMIN)*(P3B-P3T)
def x3(i): return X0+W*i/(len(C)-1)
cpath="M"+" L".join(f"{x3(i):.0f},{y3(v):.0f}" for i,v in enumerate(C))
pk=int(np.argmax(C))
# 收敛率
AGG={"6(1日)":37.0,"12(2日)":30.8,"24(4日)":53.8,"48(8日)":46.2}
BN=[27,26,26,26]
P2T,P2B=272,352
BW=44; gap=(W-4*BW)/4
bars=""
for k,(lb,v) in enumerate(AGG.items()):
    bx=X0+gap*0.5+k*(BW+gap); bh=(v/100)*(P2B-P2T); by=P2B-bh
    col="#E69F00" if v>=50 else "#56B4E9"
    bars+=(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{BW}" height="{bh:.1f}" fill="{col}" rx="2"/>'
           f'<text x="{bx+BW/2:.1f}" y="{by-6:.1f}" text-anchor="middle" font-size="12" font-weight="500" fill="var(--color-text-primary)">{v:.1f}%</text>'
           f'<text x="{bx+BW/2:.1f}" y="{P2B+15:.1f}" text-anchor="middle" font-size="11" fill="var(--color-text-secondary)">{lb}</text>'
           f'<text x="{bx+BW/2:.1f}" y="{P2B+28:.1f}" text-anchor="middle" font-size="11" fill="var(--color-text-secondary)">n={BN[k]}</text>')
grid1="".join(f'<line x1="{X0}" y1="{y1(v):.1f}" x2="{X1}" y2="{y1(v):.1f}" stroke="rgba(255,255,255,0.13)" stroke-width="1"/>'
   f'<text x="{X0-7}" y="{y1(v)+4:.1f}" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">${v}</text>' for v in (0,5,10,15))
grid3="".join(f'<line x1="{X0}" y1="{y3(v):.1f}" x2="{X1}" y2="{y3(v):.1f}" stroke="rgba(255,255,255,0.13)" stroke-width="1"/>'
   f'<text x="{X0-7}" y="{y3(v)+4:.1f}" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">${v}</text>' for v in (5,10,15))
axis3="".join(f'<text x="{x3(i):.1f}" y="{P3B+15:.1f}" text-anchor="middle" font-size="11" fill="var(--color-text-secondary)">{CT[i][5:10]}</text>' for i in (0,len(C)//3,2*len(C)//3,len(C)-1))
axis1="".join(f'<text x="{x(i):.1f}" y="{P1B+15:.1f}" text-anchor="middle" font-size="11" fill="var(--color-text-secondary)">{days[i][5:]}</text>' for i in (0,15,30,45,60,70,82))
rollx=x(60)
svg=f'''<svg viewBox="0 0 680 600" width="100%" role="img" xmlns="http://www.w3.org/2000/svg">
<title>NYMEX 单合约重建真当期月差与超买事件研究</title>
<desc>上：真当期月差（K26-M26拼接M26-N26）对比旧代理 CL2610-CL2611；中：超买后月差收敛率；下：4月2日超买案例路径</desc>
<text x="12" y="20" font-size="13" font-weight="500" fill="var(--color-text-primary)">真当期月差 vs 旧代理：形态完全不同（2026-02-09 ~ 05-19，4h 折算日值）</text>
{grid1}
<path d="{path(KM)}" fill="none" stroke="#56B4E9" stroke-width="2"/>
<path d="{path(MN)}" fill="none" stroke="#E69F00" stroke-width="2" stroke-dasharray="7,3"/>
<path d="{path(PR)}" fill="none" stroke="#9AA0A6" stroke-width="1.4" stroke-dasharray="1.5,3"/>
{mk}
<line x1="{rollx:.1f}" y1="{P1T}" x2="{rollx:.1f}" y2="{P1B}" stroke="#F0E442" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{rollx+4:.1f}" y="{P1T+11}" font-size="11" fill="#F0E442">4/21 换月</text>
{axis1}
<text x="{X0}" y="{P1T-8}" font-size="11" fill="#56B4E9">真 K26−M26</text>
<text x="{X0+96}" y="{P1T-8}" font-size="11" fill="#E69F00">真 M26−N26</text>
<text x="{X0+206}" y="{P1T-8}" font-size="11" fill="#9AA0A6">旧代理 CL2610−CL2611</text>
<text x="{X0+376}" y="{P1T-8}" font-size="11" fill="#F0E442">▲ 前月腿 RSI≥70 事件</text>
<text x="12" y="252" font-size="13" font-weight="500" fill="var(--color-text-primary)">超买后月差「为负（收敛）」的占比：1-2 日仅 31-37%，低于抛硬币</text>
<line x1="{X0}" y1="{P2B-(0.5*(P2B-P2T)):.1f}" x2="{X1}" y2="{P2B-(0.5*(P2B-P2T)):.1f}" stroke="rgba(255,255,255,0.4)" stroke-width="1" stroke-dasharray="4,4"/>
<text x="{X1-2}" y="{P2B-(0.5*(P2B-P2T))-5:.1f}" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">50% 基准</text>
{bars}
<text x="12" y="384" font-size="13" font-weight="500" fill="var(--color-text-primary)">案例：4/2 超买点后价格继续冲顶，真正收敛发生在顶部之后</text>
{grid3}
<path d="{cpath}" fill="none" stroke="#56B4E9" stroke-width="2"/>
<path d="M{x3(5):.1f},{y3(C[5])-6:.1f} l5,8 h-10 z" fill="#F0E442"/>
<text x="{x3(5)-2:.1f}" y="{y3(C[5])-10:.1f}" text-anchor="middle" font-size="11" fill="#F0E442">超买 RSI 72.2 → $14.92</text>
<path d="M{x3(pk):.1f},{y3(C[pk])-6:.1f} l5,8 h-10 z" fill="#56B4E9"/>
<text x="{x3(pk)+8:.1f}" y="{y3(C[pk])-2:.1f}" font-size="11" fill="#56B4E9">真顶 $16.04（+2 日后）</text>
<circle cx="{x3(len(C)-1):.0f}" cy="{y3(C[-1]):.0f}" r="3.5" fill="#E69F00"/>
<text x="{x3(len(C)-1)-6:.1f}" y="{y3(C[-1])-8:.1f}" text-anchor="end" font-size="11" fill="#E69F00">8 日后 $3.56</text>
{axis3}
</svg>'''
open(r"C:/Users/Administrator/Desktop/stock/Temp/widget.svg","w",encoding="utf-8").write(svg)
print("bytes",len(svg))
