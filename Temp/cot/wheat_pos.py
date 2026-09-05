# -*- coding: utf-8 -*-
import zipfile,csv,io,os,collections,json

FILES={}
for y in range(1995,2004): FILES[y]=f'old_{y}.zip'
for y in range(2004,2026): FILES[y]=f'hist_{y}.zip'
FILES[2026]='fo2026.zip'
TMP=os.path.dirname(os.path.abspath(__file__))

def cls(nm):
    u=nm.upper().strip()
    if not u.startswith('WHEAT') or 'WHITE' in u: return None
    if 'WHEAT-SRW' in u or u in ('WHEAT - CHICAGO BOARD OF TRADE','WHEAT - CBT WHEAT'): return 'SRW'
    if 'WHEAT-HRW' in u or u in ('WHEAT - KANSAS CITY BOARD OF TRADE','WHEAT - KCBT WHEAT'): return 'HRW'
    if 'WHEAT-HRSPRING' in u or u in ('WHEAT - MINNEAPOLIS GRAIN EXCHANGE','WHEAT - MGE WHEAT'): return 'HRS'
    return None

agg={}
for y,zf in FILES.items():
    p=os.path.join(TMP,zf)
    if not os.path.exists(p): print('MISSING',y); continue
    z=zipfile.ZipFile(p)
    inner=[x for x in z.namelist() if x.lower().endswith('.txt')][0]
    for r in csv.DictReader(io.StringIO(z.read(inner).decode('utf-8','replace'))):
        c=cls(r['Market and Exchange Names'])
        if not c: continue
        def n(k):
            v=r.get(k,'').replace(',','').strip(); return int(v) if v not in ('','.') else None
        rec=(n('Noncommercial Positions-Long (All)'),n('Noncommercial Positions-Short (All)'),n('Open Interest (All)'))
        if None in rec: continue
        agg[(r['As of Date in Form YYYY-MM-DD'],c)]=rec
W={}
for (d,c),(L,S,OI) in agg.items():
    W.setdefault(d,[0,0,0]); W[d][0]+=L; W[d][1]+=S; W[d][2]+=OI
ds=sorted(W)
print('总周',len(ds),ds[0],'->',ds[-1])
json.dump({'n':len(ds),'series':{d:W[d] for d in ds}},open(os.path.join(TMP,'wheat_3c_1995.json'),'w'))

def pct(s,v): return round(100*sum(1 for x in s if x<=v)/len(s),1)
chg=[]
for i in range(1,len(ds)):
    p,w=W[ds[i-1]],W[ds[i]]
    chg.append(dict(d=ds[i],dL=w[0]-p[0],dS=w[1]-p[1],dNet=(w[0]-w[1])-(p[0]-p[1]),
                    L=w[0],S=w[1],Net=w[0]-w[1],OI=w[2],dLpct=(w[0]-p[0])/p[2]*100))
cur=chg[-1]; N=len(chg)
dl=[c['dL'] for c in chg]; dn=[c['dNet'] for c in chg]; dlp=[c['dLpct'] for c in chg]
print('样本 %d 周，%s -> %s'%(N,ds[1],ds[-1]))
print()
print('== 本周 (2026-09-01) 定位 ==')
rank=sorted(dl,reverse=True).index(cur['dL'])+1
print('多头单周 +%s   全样本分位 %.1f%%   排名 #%d/%d'%(f"{cur['dL']:,}",pct(dl,cur['dL']),rank,N))
print('净头寸单周 +%s   分位 %.1f%%'%(f"{cur['dNet']:,}",pct(dn,cur['dNet'])))
mu=sum(dlp)/N; md=sorted(dlp)[N//2]
print('多头增量/OI(前周) %.2f%%   分位 %.1f%%   (样本均值 %.2f%% 中位 %.2f%%)'%(cur['dLpct'],pct(dlp,cur['dLpct']),mu,md))
print('当前净头寸 %s   净/OI %.1f%%'%(f"{cur['Net']:,}",cur['Net']/cur['OI']*100))
print()
print('== 多头单周增仓 top12（1995-2026 全样本）==')
for c in sorted(chg,key=lambda x:-x['dL'])[:12]:
    print('  %s  +%s  (%+.2f%%OI)  净%+s'%(c['d'],f"{c['dL']:,}",c['dLpct'],f"{c['dNet']:,}"))
print()
print('== 净头寸单周增幅 top12 ==')
for c in sorted(chg,key=lambda x:-x['dNet'])[:12]:
    print('  %s  净%+s  (多%+s 空%+s)'%(c['d'],f"{c['dNet']:,}",f"{c['dL']:,}",f"{c['dS']:,}"))
print()
net=[c['Net'] for c in chg]; netoi=[c['Net']/c['OI']*100 for c in chg]
print('当前净头寸绝对分位 %.1f%%  |  净/OI 分位 %.1f%%'%(pct(net,cur['Net']),pct(netoi,cur['Net']/cur['OI']*100)))
topoi=sorted(chg,key=lambda x:-x['Net']/x['OI'])[:10]
print('净/OI 历史 top10:')
for c in topoi: print('  %s  %.1f%%  (净%+s)'%(c['d'],c['Net']/c['OI']*100,f"{c['Net']:,}"))
print()
def inwin(d):
    m,d2=map(int,d.split('-')[1:])
    return (m==8 and d2>=20) or (m==9 and d2<=12)
seas=[c for c in chg if inwin(c['d'])]
sd=[c['dL'] for c in seas]
print('同季窗口(8/20-9/12, n=%d) 多头单周增仓 本周 +%s -> 分位 %.1f%% ; 窗口内历史最大 +%s'%(
    len(seas),f"{cur['dL']:,}",pct(sd,cur['dL']),f"{max(sd):,}"))
# 窗口内 top6
for c in sorted(seas,key=lambda x:-x['dL'])[:6]:
    print('    %s  +%s'%(c['d'],f"{c['dL']:,}"))
