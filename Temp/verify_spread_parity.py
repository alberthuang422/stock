# -*- coding: utf-8 -*-
"""检验：OCT-NOV / NOV-DEC / DEC-JAN 三段月差近期拉升幅度是否同步（平行陡化）"""
import csv, os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cl_contracts', 'daily')

def load(c):
    p = os.path.join(BASE, f'US.CL{c}.csv')
    out = {}
    with open(p, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                out[r['date']] = float(r['close'])
            except (ValueError, TypeError):
                pass
    return out

C = {c: load(c) for c in ['2610', '2611', '2612', '2701', '2702', '2703']}
dates = sorted(set(C['2610']) & set(C['2611']) & set(C['2612']) & set(C['2701']))
print('样本区间:', dates[0], '->', dates[-1], f'({len(dates)} 日)')

def sp(d, a, b):
    return C[a].get(d, {}).get if False else (C[a][d] - C[b][d] if d in C[a] and d in C[b] else None)

# 三段月差：M1-M2 / M2-M3 / M3-M4
segs = [('OCT-NOV', '2610', '2611'), ('NOV-DEC', '2611', '2612'), ('DEC-JAN', '2612', '2701')]
series = {n: {d: (C[a][d] - C[b][d]) for d in dates if d in C[a] and d in C[b]} for n, a, b in segs}

print('\n=== 1) 各段当前水平与 7/23 基准对比 ===')
for n, _, _ in segs:
    s = series[n]
    cur = s[dates[-1]]
    peak = max(s.values())
    peak_d = max(s, key=lambda d: s[d])
    base723 = s.get('2026-07-23')
    print(f'{n}: 现 {cur:.2f} | 全期峰值 {peak:.2f}({peak_d}) | 7/23 {base723:.2f} | '
          f'距峰值 {(cur/peak-1)*100:+.1f}%')

print('\n=== 2) 关键区间涨幅对比（用绝对变化 $）===')
windows = [('8/5 谷底 -> 9/10', '2026-08-05', '2026-09-10'),
           ('8/28 -> 9/10', '2026-08-28', '2026-09-10'),
           ('9/3 -> 9/10', '2026-09-03', '2026-09-10'),
           ('9/4 -> 9/10', '2026-09-04', '2026-09-10')]
for wn, d0, d1 in windows:
    print(f'\n[{wn}]')
    for n, _, _ in segs:
        s = series[n]
        if d0 in s and d1 in s:
            a, b = s[d0], s[d1]
            print(f'  {n}: {a:.2f} -> {b:.2f}   Δ=${b-a:+.2f}  ({(b/a-1)*100:+.1f}%)')

print('\n=== 3) 各段日变化（Δ spread）近 10 日 ===')
print('date        ' + ''.join(f'{n:>12}' for n, _, _ in segs))
for d in dates[-10:]:
    row = f'{d}  '
    for n, _, _ in segs:
        s = series[n]
        prev = None
        idx = dates.index(d)
        if idx > 0 and dates[idx-1] in s and d in s:
            prev = s[dates[idx-1]]
        if d in s and prev is not None:
            row += f'{s[d]-prev:>+12.3f}'
        else:
            row += f'{"--":>12}'
    print(row)

print('\n=== 4) Δ 月差的相关性矩阵（日变化）===')
import statistics
deltas = {}
for n, _, _ in segs:
    s = series[n]
    dl = []
    for i in range(1, len(dates)):
        d0, d1 = dates[i-1], dates[i]
        if d0 in s and d1 in s:
            dl.append(s[d1] - s[d0])
        else:
            dl.append(None)
    deltas[n] = dl

def corr(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 5:
        return None, 0
    xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a-mx)*(b-my) for a, b in pairs)
    den = (sum((a-mx)**2 for a in xs) * sum((b-my)**2 for b in ys)) ** 0.5
    return (num/den if den else None), len(pairs)

names = [n for n, _, _ in segs]
print('          ' + ''.join(f'{n:>12}' for n in names))
for i, n1 in enumerate(names):
    row = f'{n1:>9} '
    for j, n2 in enumerate(names):
        r, k = corr(deltas[n1], deltas[n2])
        row += f'{(f"{r:.3f}" if r is not None else "--"):>12}'
    print(row)

print('\n=== 5) 波动率对比（日变化标准差，全样本）===')
for n, _, _ in segs:
    v = [x for x in deltas[n] if x is not None]
    print(f'{n}: σ={statistics.stdev(v):.4f}  均值|Δ|={statistics.mean(abs(x) for x in v):.4f}')

print('\n=== 6) 归一化：三段各自按自身 σ 标准化后的累计（看是否同形）===')
import math
print('date        ' + ''.join(f'{n:>12}' for n, _, _ in segs))
z = {n: 0.0 for n, _, _ in segs}
sig = {n: statistics.stdev([x for x in deltas[n] if x is not None]) for n, _, _ in segs}
cum = {n: 0.0 for n, _, _ in segs}
start_idx = max(0, len(dates) - 21)
for i in range(1, len(dates)):
    for n, _, _ in segs:
        if deltas[n][i-1] is not None:
            cum[n] += deltas[n][i-1] / sig[n]
    if i >= start_idx:
        row = f'{dates[i]}  '
        for n, _, _ in segs:
            row += f'{cum[n]:>12.2f}'
        print(row)
