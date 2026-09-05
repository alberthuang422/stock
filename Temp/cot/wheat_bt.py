# -*- coding: utf-8 -*-
"""极端多头增仓周 → 价格见顶回测（2011-07 后，富途 ZWmain 日线）"""
import json,csv,datetime as dt,statistics as st

px=json.load(open('zw_main_hist.json'))  # 富途 kline list
pxd={}
for k in px:
    ts=dt.datetime.fromtimestamp(k['time_key']/1000)
    d0=ts.date().isoformat()
    pxd.setdefault(d0,{'c':k['close'],'h':k['high']})
pxd={d:v for d,v in sorted(pxd.items())}
days=list(pxd)
print('价格区间',days[0],'->',days[-1],'n=',len(days))

def px_at(d,field='c',back=6):
    """找 d 当日或之前最近交易日价格"""
    cur=dt.date.fromisoformat(d)
    for _ in range(back):
        s=cur.isoformat()
        if s in pxd: return pxd[s][field]
        cur=cur-dt.timedelta(days=1)
    return None

def fwd_ret(d0,weeks):
    """从事件日(含)起持有 weeks 个交易周(每5交易日近似)的收益"""
    i=days.index(d0)
    if i+weeks*5>=len(days): return None
    return (pxd[days[i+weeks*5]]['c']/pxd[d0]['c']-1)*100

def peak_info(d0,max_weeks=52):
    """事件后 max_weeks 交易周内最高收盘价/用时(周)/触发点"""
    i=days.index(d0)
    j=min(len(days),i+max_weeks*5)
    seg=days[i:j]
    if not seg: return None
    pk=max(seg,key=lambda s:pxd[s]['c'])
    weeks=(len(seg[:seg.index(pk)+1])-1)/5
    return dict(peak_d=pk,weeks=round(weeks,1),ret=(pxd[pk]['c']/pxd[d0]['c']-1)*100)

ev=list(csv.DictReader(open('wheat_events.csv')))
# 事件：2011-07 后 dL>=15000，排除2026(未完结)与数据窗口外
evs=[r for r in ev if r['date']>='2011-07-25' and int(r['dL'])>=15000 and r['date']<='2024-12-31']
print('候选事件',len(evs))
res=[]
for r in evs:
    d0=r['date']
    if d0 not in pxd:
        # 回退查找
        cand=dt.date.fromisoformat(d0)
        found=None
        for _ in range(7):
            if cand.isoformat() in pxd: found=cand.isoformat(); break
            cand=cand-dt.timedelta(days=1)
        if not found: print('NO PRICE',d0); continue
        d0=found
    pi=peak_info(d0)
    if not pi: continue
    res.append(dict(evdate=r['date'],pxdate=d0,p0=pxd[d0]['c'],
        dL=int(r['dL']),dNet=int(r['dNet']),net_prev=int(r['net_prev']),
        r4=fwd_ret(d0,4),r8=fwd_ret(d0,8),r13=fwd_ret(d0,13),r26=fwd_ret(d0,26),r52=fwd_ret(d0,52),
        **pi))
print('有效事件',len(res))
print()
print(f"{'事件日':<12}{'P0':>8}{'顶日':<12}{'见顶周':>7}{'顶涨%':>8}{'r4':>7}{'r13':>7}{'r26':>7}{'r52':>7}{'dL':>9}")
for x in sorted(res,key=lambda z:z['evdate']):
    f=lambda v: f"{v:+.1f}" if v is not None else "  NA"
    print(f"{x['evdate']:<12}{x['p0']:>8.1f}{x['peak_d']:<12}{x['weeks']:>7.1f}{x['ret']:>+8.1f}{f(x['r4']):>7}{f(x['r13']):>7}{f(x['r26']):>7}{f(x['r52']):>7}{x['dL']:>9,}")
json.dump(res,open('wheat_bt_results.json','w'),ensure_ascii=False)
