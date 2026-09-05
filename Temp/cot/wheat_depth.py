# -*- coding: utf-8 -*-
"""73号报告深挖：见顶用时 vs 时间聚类 / 净头寸存量 / 价格位置"""
import json, csv, datetime as dt, statistics as st
from scipy.stats import spearmanr, mannwhitneyu

res = json.load(open('wheat_bt_results.json'))
px = json.load(open('zw_main_hist.json'))          # list[dict], close=美分, date=YYYYMMDD int
ev = {r['date']: r for r in csv.DictReader(open('wheat_events.csv'))}

px_by_d = {}
for x in px:
    d = dt.datetime.fromtimestamp(x['time_key']/1000).date()
    px_by_d[d] = x['close']
pdays = sorted(px_by_d)                              # 升序日期
close = {d: px_by_d[d] for d in pdays}

def pos52(d0):
    """事件日收盘 相对过去52周(约260交易日)最高收盘 的位置(%) 与 距52周高回撤"""
    i = pdays.index(d0)
    win = [close[d] for d in pdays[max(0, i-260):i+1]]
    hi = max(win)
    c = close[d0]
    return 100*c/hi, 100*(c-hi)/hi, hi

rows = []
for x in res:
    d = dt.date.fromisoformat(x['evdate'])
    e = ev[x['evdate']]
    # 事件日净头寸与净/OI（当周）
    net_ev = int(e['net']); oi = int(e['OI'])
    p52, dd, hi = pos52(d)
    rows.append(dict(ev=x['evdate'], p0=x['p0'], pos52=round(p52,1), dd52=round(dd,1),
                     net_prev=int(x['net_prev']), net_ev=net_ev, net_oi=round(100*net_ev/oi,1),
                     dL=int(x['dL']), weeks=x['weeks'], ret=x['ret'],
                     r4=x['r4'], r13=x['r13'], r52=x['r52'],
                     typ='即时顶' if x['weeks']<=2 else '续涨',
                     bull = '2019-12-01' <= x['evdate'] <= '2021-12-31'))

print(f"{'事件日':<12}{'价(美分)':>8}{'52周高%':>8}{'净头寸prev':>11}{'净/OI%':>8}{'周数':>6}{'类型':>5}{'牛市窗':>5}{'r4%':>7}{'r13%':>7}  背景")
bg = {
 '2012-07-17':'2012美国大干旱 价格打顶后 USDA 转向',
 '2015-06-30':'净空区空头回补反弹至前高',
 '2016-06-07':'净空区回补反弹(2016春高点)',
 '2017-07-11':'净多9.6万高位再加=情绪顶',
 '2018-07-31':'净多4万天气炒作(春麦)中段',
 '2018-08-07':'净多9.2万高位再加=情绪顶',
 '2019-12-17':'牛市启动段(库存周期转紧)',
 '2020-01-21':'牛市早期',
 '2020-03-31':'疫情底部区反弹',
 '2020-07-14':'牛市中段(中国采购潮)',
 '2020-09-01':'牛市推进(俄罗斯出口限制)',
 '2020-10-06':'牛市推进(全球库存新低预期)',
 '2020-10-20':'牛市推进',
 '2021-01-05':'牛市冲刺前(库存报告利多)',
 '2021-04-27':'牛市冲刺(美春麦播种担忧)',
 '2021-08-03':'牛市后段(加仓续涨)',
 '2021-08-17':'牛市后段(加仓续涨)',
 '2022-02-22':'俄乌开战 脉冲式利多一步到位',
 '2024-01-30':'低位反弹(净空10.5万)',
 '2024-06-25':'低位反弹(净空7万)',
}
for r in rows:
    print(f"{r['ev']:<12}{r['p0']:>8.0f}{r['pos52']:>7.1f}%{r['net_prev']:>11,}{r['net_oi']:>7.1f}%{r['weeks']:>6.1f}{r['typ']:>4}{'Y' if r['bull'] else 'N':>5}{r['r4']:>7.1f}{r['r13']:>7.1f}  {bg[r['ev']]}")

print()
print('='*100)
print('检验1：续涨型是否集中在 2019-12~2021-08 牛市窗口')
imm=[r for r in rows if r['typ']=='即时顶']; cont=[r for r in rows if r['typ']=='续涨']
b=[r for r in rows if r['bull']]; nb=[r for r in rows if not r['bull']]
print(f'总事件 20 = 牛市窗 {len(b)} + 非牛市 {len(nb)}')
print(f'牛市窗 {len(b)} 个: 续涨 {sum(1 for r in b if r["typ"]=="续涨")} / 即时顶 {sum(1 for r in b if r["typ"]=="即时顶")}')
print(f'非牛市 {len(nb)} 个: 续涨 {sum(1 for r in nb if r["typ"]=="续涨")} / 即时顶 {sum(1 for r in nb if r["typ"]=="即时顶")}')
print(f'-> 续涨型 {len(cont)} 个中 {sum(1 for r in cont if r["bull"])} 个在牛市窗 = {100*sum(1 for r in cont if r["bull"])/len(cont):.0f}%')
print(f'-> 剔除牛市窗后快速见顶占比 = {100*sum(1 for r in nb if r["typ"]=="即时顶")/len(nb):.0f}% ({sum(1 for r in nb if r["typ"]=="即时顶")}/{len(nb)})')

print()
print('='*100)
print('检验2：见顶用时 vs 事件日/前周净头寸存量  (Spearman)')
for lab, fld in [('net_prev','net_prev'),('net_ev','net_ev'),('net/OI%','net_oi'),('52周价格位置%','pos52'),('r4','r4')]:
    for grp, gname in [(rows,'全20'), (nb,'剔牛市窗')]:
        xs=[r[fld] for r in grp]; ys=[r['weeks'] for r in grp]
        rho,p=spearmanr(xs,ys)
        print(f'  weeks vs {lab:<10} {gname}: rho={rho:+.3f} p={p:.3f}  (n={len(grp)})')

print()
print('分组中位数对比 (即时顶 n=%d vs 续涨 n=%d):'%(len(imm),len(cont)))
for lab,fld,fmt in [('net_prev','net_prev',','),('net/OI%','net_oi','.1f'),('52周位置%','pos52','.1f'),('p0 价格','p0','.0f'),('r4%','r4','.1f')]:
    a=st.median([r[fld] for r in imm]); b=st.median([r[fld] for r in cont])
    try:
        u,p=mannwhitneyu([r[fld] for r in imm],[r[fld] for r in cont],alternative='two-sided')
        ps=f'MW p={p:.3f}'
    except Exception as ex: ps='n/a'
    print(f'  {lab:<10} 即时顶中位 {a:{fmt}}  vs  续涨中位 {b:{fmt}}   {ps}')

print()
print('极值切分探针：')
print('  net/OI>10% 的事件(高拥挤):',[(r['ev'],r['net_oi'],r['weeks'],r['typ']) for r in rows if r['net_oi']>10])
print('  net/OI<0  的事件(净空):',[(r['ev'],r['net_oi'],r['weeks'],r['typ'],r['pos52']) for r in rows if r['net_oi']<0])
print('  pos52>=97 的事件(价格在52周高附近):',[(r['ev'],r['pos52'],r['weeks'],r['typ'],r['net_oi']) for r in rows if r['pos52']>=97])
print('  pos52<=85 的事件(价格远离52周高):',[(r['ev'],r['pos52'],r['weeks'],r['typ'],r['net_oi']) for r in rows if r['pos52']<=85])
