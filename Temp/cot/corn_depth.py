# -*- coding: utf-8 -*-
"""玉米深度：见顶类型分层 / 牛市窗 / 存量拥挤 / 位置 / 对照基准（复刻 wheat_depth.py）"""
import json, csv, datetime as dt, statistics as st
from scipy.stats import spearmanr, mannwhitneyu

res = json.load(open('corn_bt_results.json'))
ev = {r['date']: r for r in csv.DictReader(open('corn_events.csv'))}
px = json.load(open('zc_main_hist.json'))
px_by_d = {}
for x in px:
    d = dt.datetime.fromtimestamp(x['time_key']/1000).date().isoformat()
    px_by_d[d] = x['close']
pdays = sorted(px_by_d)
close = {d: px_by_d[d] for d in pdays}

def pos52(d0):
    i = pdays.index(d0)
    win = [close[d] for d in pdays[max(0, i-260):i+1]]
    hi = max(win); lo = min(win); c = close[d0]
    return 100*c/hi, 100*(c-hi)/hi, 100*(c-lo)/hi, hi, lo

rows = []
for x in res:
    d0 = x['pxdate']  # 实际交易日
    e = ev[x['evdate']]
    net_ev = int(e['net']); oi = int(e['OI'])
    p52, dd, rng, hi, lo = pos52(d0)
    rows.append(dict(ev=x['evdate'], px=x['pxdate'], p0=x['p0'], pos52=round(p52, 1), dd52=round(dd, 1),
                     rng52=round(rng, 1), hi52=hi, lo52=lo,
                     net_prev=int(x['net_prev']), net_ev=net_ev, net_oi=round(100*net_ev/oi, 1),
                     dL=int(x['dL']), dS=int(x['dS']), weeks=x['weeks'], ret=x['ret'],
                     r4=x['r4'], r8=x['r8'], r13=x['r13'], r26=x['r26'], r52=x['r52'],
                     typ='即时顶' if x['weeks'] <= 2 else '续涨',
                     bull='2020-01-01' <= x['evdate'] <= '2021-12-31'))
print(f"{'事件日':<12}{'P0':>7}{'52周高%':>8}{'区间%':>7}{'净prev':>10}{'净/OI':>7}{'周':>6}{'类型':>5}{'牛市':>4}{'r4':>7}{'r13':>7}{'r26':>7}{'r52':>8}  dNet")
for r in rows:
    print(f"{r['ev']:<12}{r['p0']:>7.0f}{r['pos52']:>7.1f}%{r['rng52']:>6.1f}%{r['net_prev']:>10,}{r['net_oi']:>6.1f}%{r['weeks']:>6.1f}{r['typ']:>4}{'Y' if r['bull'] else 'N':>4}{r['r4']:>7.1f}{r['r13']:>7.1f}{r['r26']:>7.1f}{r['r52']:>8.1f}  {r['dL']:+,}")

print('\n' + '='*100)
imm = [r for r in rows if r['typ'] == '即时顶']; cont = [r for r in rows if r['typ'] == '续涨']
b = [r for r in rows if r['bull']]; nb = [r for r in rows if not r['bull']]
print(f'总事件 {len(rows)} = 牛市窗 {len(b)} + 非牛市 {len(nb)}')
print(f'即时顶 {len(imm)} 个 (≤2周), 续涨 {len(cont)} 个 (见顶周数中位 {st.median([r["weeks"] for r in cont]):.1f}, 顶涨中位 {st.median([r["ret"] for r in cont]):+.1f}%)')
print(f'牛市窗事件: 续涨 {sum(1 for r in b if r["typ"]=="续涨")}/{len(b)} | 非牛市: 即时顶 {sum(1 for r in nb if r["typ"]=="即时顶")}/{len(nb)}')
print(f'-> 续涨 {len(cont)} 个中牛市窗占 {100*sum(1 for r in cont if r["bull"])/len(cont):.0f}%')
print(f'-> 非牛市快速见顶率 {100*sum(1 for r in nb if r["typ"]=="即时顶")/len(nb):.0f}% ({sum(1 for r in nb if r["typ"]=="即时顶")}/{len(nb)})')
print(f'即时顶事件明细: {[(r["ev"], r["p0"], r["weeks"], r["net_oi"]) for r in imm]}')

print('\n' + '='*100)
print('检验: weeks vs 各变量 Spearman')
for lab, fld in [('net_prev', 'net_prev'), ('net/OI', 'net_oi'), ('pos52', 'pos52'), ('r4', 'r4')]:
    for grp, gn in [(rows, '全22'), (nb, '剔牛市窗')]:
        rho, p = spearmanr([r[fld] for r in grp], [r['weeks'] for r in grp])
        print(f'  weeks vs {lab:<8} {gn}: rho={rho:+.3f} p={p:.3f} (n={len(grp)})')

print('\n分组中位数 (即时顶 n=%d vs 续涨 n=%d):' % (len(imm), len(cont)))
for lab, fld, fmt in [('net_prev', 'net_prev', ','), ('net/OI', 'net_oi', '.1f'), ('pos52', 'pos52', '.1f'), ('r4', 'r4', '.1f')]:
    a = st.median([r[fld] for r in imm]); bb = st.median([r[fld] for r in cont])
    try:
        u, p = mannwhitneyu([r[fld] for r in imm], [r[fld] for r in cont], alternative='two-sided')
        ps = f'MW p={p:.3f}'
    except Exception:
        ps = 'n/a'
    print(f'  {lab:<10} 即时顶中位 {a:{fmt}}  vs  续涨中位 {bb:{fmt}}   {ps}')

print('\n窗口收益 vs 全体交易日对照:')
def bench(w):
    n = 0; s = 0.0
    for i in range(0, len(pdays)-w*5, 21):
        s += (close[pdays[i+w*5]]/close[pdays[i]]-1)*100; n += 1
    return s/n
for w in (4, 13, 26):
    evv = [r[f'r{w}'] for r in rows if r[f'r{w}'] is not None]
    pos = sum(1 for x in evv if x > 0)
    print(f'  事件后{w}周: 中位 {st.median(evv):+.1f}%  正收益占比 {100*pos/len(evv):.0f}%  (全体交易日对照中位 {bench(w):+.1f}%)')
for grp, gn in [(cont, '续涨'), (imm, '即时顶')]:
    for w in (4, 13, 26):
        evv = [r[f'r{w}'] for r in grp if r[f'r{w}'] is not None]
        if evv: print(f'    {gn} 事件后{w}周: 中位 {st.median(evv):+.1f}%')

print('\n极值探针:')
print('  net/OI>12% (高拥挤):', [(r['ev'], r['net_oi'], r['weeks'], r['typ']) for r in rows if r['net_oi'] > 12])
print('  net/OI<8%  (低拥挤):', [(r['ev'], r['net_oi'], r['weeks'], r['typ']) for r in rows if r['net_oi'] < 8])
print('  pos52>=97  (价格贴52周高):', [(r['ev'], r['pos52'], r['weeks'], r['typ']) for r in rows if r['pos52'] >= 97])
print('  pos52<=85  (价格低):', [(r['ev'], r['pos52'], r['weeks'], r['typ']) for r in rows if r['pos52'] <= 85])

print('\n' + '='*100)
print('当前 2026-09-01 周定位（对齐上述口径）:')
cur = ev['2026-09-01']
# 9/1 COT 报告后价格路径
i9 = pdays.index('2026-09-01') if '2026-09-01' in pdays else pdays.index(px_at_impl())
def px_at_impl():
    cur_d = dt.date(2026, 9, 1)
    for _ in range(5):
        if cur_d.isoformat() in px_by_d: return cur_d.isoformat()
        cur_d = cur_d - dt.timedelta(days=1)
    return None
d0 = px_at_impl()
p52, dd, rng, hi, lo = pos52(d0)
print(f'  报告对齐交易日 {d0}  收 {close[d0]}   52周高% {p52:.1f}   (52周高 {hi:.0f} / 低 {lo:.0f})')
net_cur = int(cur['net']); print(f'  当周净 {net_cur:,}  净/OI {100*net_cur/int(cur["OI"]):.2f}%  单周dNet {int(cur["dNet"]):+,}')
if d0 != pdays[-1]:
    for dd0 in pdays[pdays.index(d0):pdays.index(d0)+8]:
        print(f'    {dd0} close {close[dd0]:.2f}  ({100*(close[dd0]/close[d0]-1):+.2f}%)')
