# -*- coding: utf-8 -*-
"""检验：OCT-NOV 是否一贯强于 NOV-DEC（月差近端溢价持续性）"""
import csv, sys, statistics as st, collections
sys.stdout.reconfigure(encoding='utf-8')

codes = ['CL2610', 'CL2611', 'CL2612', 'CL2701']
D = {c: list(csv.DictReader(open(f'data/cl_contracts/daily/US.{c}.csv', encoding='utf-8'))) for c in codes}
dates = [r['date'] for r in D['CL2610']]
cl = {c: [float(r['close']) for r in D[c]] for c in codes}
n = len(dates)

s1 = [cl['CL2610'][i] - cl['CL2611'][i] for i in range(n)]   # OCT-NOV
s2 = [cl['CL2611'][i] - cl['CL2612'][i] for i in range(n)]   # NOV-DEC

print('=== 检验前提：OCT-NOV 是否「一贯」强于 NOV-DEC ===')
gt = sum(1 for i in range(n) if s1[i] > s2[i] + 0.005)
eq = sum(1 for i in range(n) if abs(s1[i] - s2[i]) <= 0.005)
lt = sum(1 for i in range(n) if s2[i] > s1[i] + 0.005)
print(f'样本 {n} 日：')
print(f'  OCT-NOV 更陡 : {gt:>3} 日 ({gt/n*100:>5.1f}%)')
print(f'  NOV-DEC 更陡 : {lt:>3} 日 ({lt/n*100:>5.1f}%)')
print(f'  基本相等     : {eq:>3} 日 ({eq/n*100:>5.1f}%)')
print(f'均值：OCT-NOV {st.mean(s1):.3f}  |  NOV-DEC {st.mean(s2):.3f}  |  比值 {st.mean(s2)/st.mean(s1):.3f}')
print(f'中位：OCT-NOV {st.median(s1):.3f}  |  NOV-DEC {st.median(s2):.3f}  |  比值 {st.median(s2)/st.median(s1):.3f}')
print()

print('=== 分阶段（比值 = NOV-DEC / OCT-NOV）===')
def segstats(a, b, lab):
    ix = [i for i, d in enumerate(dates) if a <= d <= b]
    r = [s2[i] / s1[i] for i in ix if s1[i] > 0.001]
    above = sum(1 for x in r if x > 1)
    print(f'{lab:<14} {len(ix):>3}日  中位比值 {st.median(r):>6.3f}  区间[{min(r):.2f},{max(r):.2f}]  比值>1 占 {above/len(r)*100:>5.1f}%')
segstats('2026-03-10', '2026-05-31', '3-5月')
segstats('2026-06-01', '2026-07-19', '6月-7/19')
segstats('2026-07-20', '2026-08-04', '7/20-8/4')
segstats('2026-08-05', '2026-09-10', '8/5-9/10')
print()

print('=== 月度均值 ===')
mm = collections.OrderedDict()
for i, d in enumerate(dates):
    mm.setdefault(d[:7], []).append((s1[i], s2[i]))
print('月份      OCT-NOV    NOV-DEC    比值   谁更陡')
for k, v in mm.items():
    a = st.mean(x[0] for x in v)
    b = st.mean(x[1] for x in v)
    who = 'OCT-NOV' if a > b else 'NOV-DEC'
    print(f'{k:<10}{a:>8.3f}{b:>10.3f}{b/a:>9.3f}   {who}')
print()

print('=== 关键转折点：比值首次站上 1.0 并持续 ===')
run = 0
for i in range(n):
    if s1[i] > 0.001 and s2[i] / s1[i] > 1.0:
        run += 1
        if run == 1:
            print(f'  首次突破(单日): {dates[i]}')
        if run == 5:
            print(f'  连续5日站稳  : {dates[i-4]} ~ {dates[i]}  <= 确认切换')
    else:
        run = 0
last_below = None
for i in range(n - 1, -1, -1):
    if s1[i] > 0.001 and s2[i] / s1[i] < 1.0:
        last_below = dates[i]
        break
print(f'  最近一次比值<1 : {last_below}')
print()

print('=== 单腿涨幅（近端三腿，9/3 -> 9/10）===')
i0 = dates.index('2026-09-03')
for c, nm in [('CL2610', 'OCT'), ('CL2611', 'NOV'), ('CL2612', 'DEC'), ('CL2701', 'JAN')]:
    v0, v1 = cl[c][i0], cl[c][-1]
    print(f'  {nm}: {v0:.2f} -> {v1:.2f}  {(v1/v0-1)*100:+.2f}%')
