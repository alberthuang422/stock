# -*- coding: utf-8 -*-
"""原油月差曲线完整结构画像：6 合约逐段 + 累计 + 相对斜率"""
import csv, os, statistics

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cl_contracts', 'daily')
CS = ['2610','2611','2612','2701','2702','2703']
LABEL = {'2610':'OCT26(2610)','2611':'NOV26(2611)','2612':'DEC26(2612)',
         '2701':'JAN27(2701)','2702':'FEB27(2702)','2703':'MAR27(2703)'}

def load(c):
    out = {}
    with open(os.path.join(BASE, f'US.CL{c}.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try: out[r['date']] = (float(r['close']), float(r['open_interest']) if r['open_interest'] else 0)
            except: pass
    return out

D = {c: load(c) for c in CS}
dates = sorted(set.intersection(*[set(D[c]) for c in CS]))
TODAY = dates[-1]

print(f'基准日: {TODAY}   样本: {len(dates)} 日\n')

print('=== 1) 曲线点位（M1..M6 收盘价）===')
px = {c: D[c][TODAY][0] for c in CS}
for i, c in enumerate(CS):
    print(f'M{i+1}  {LABEL[c]:<14} {px[c]:>8.2f}   OI {D[c][TODAY][1]:>9,.0f}')

print('\n=== 2) 逐段月差（相邻，$）===')
segs = []
for i in range(len(CS)-1):
    a, b = CS[i], CS[i+1]
    v = px[a] - px[b]
    segs.append((f'M{i+1}-M{i+2}', LABEL[a].split("(")[1][:4], LABEL[b].split("(")[1][:4], v))
    print(f'{LABEL[a]:<14} - {LABEL[b]:<14} = {v:>6.2f}')

print('\n=== 3) 累计月差（相对近月 M1）===')
for i, c in enumerate(CS):
    print(f'M1 - M{i+1}  ({LABEL[c]:<14}) = {px[CS[0]] - px[c]:>7.2f}')

print('\n=== 4) 曲线斜率结构（每段占 M1-M6 总幅度的比重）===')
total = px[CS[0]] - px[CS[-1]]
print(f'M1-M6 总幅度 = {total:.2f}')
for n, a, b, v in segs:
    print(f'{n}: {v:>5.2f}  占 {v/total*100:>5.1f}%   段内均价/桶 {v:>5.2f}')

print('\n=== 5) 历史分位（各段 128 日中所处位置）===')
for idx, (n, a, b, v) in enumerate(segs):
    cA, cB = CS[idx], CS[idx+1]
    s = [D[cA][d][0] - D[cB][d][0] for d in dates]
    rank = sum(1 for x in s if x < v) / len(s) * 100
    print(f'{n}: 现 {v:>5.2f} | 分位 {rank:>5.1f}% | 均值 {statistics.mean(s):>5.2f} | 峰值 {max(s):>5.2f} | 谷 {min(s):>5.2f}')

print('\n=== 6) 昨日(9/9) vs 今日(9/10) 变化 ===')
if len(dates) >= 2:
    p = dates[-2]
    for i in range(len(CS)-1):
        cA, cB = CS[i], CS[i+1]
        v0 = D[cA][p][0] - D[cB][p][0]
        v1 = D[cA][TODAY][0] - D[cB][TODAY][0]
        print(f'M{i+1}-M{i+2}: {v0:>5.2f} -> {v1:>5.2f}   Δ{v1-v0:>+6.3f}')

print('\n=== 7) 曲线形态判定：单调性检验 ===')
mono = all(px[CS[i]] > px[CS[i+1]] for i in range(len(CS)-1))
print(f'严格单调递减（全程 backwardation）: {mono}')
print('形状: ' + ' > '.join(f'{px[c]:.2f}' for c in CS))

print('\n=== 8) 斜率衰减率（每段/首段）===')
base = segs[0][3]
for n, a, b, v in segs:
    print(f'{n}: {v/base*100:>6.1f}% of M1-M2')
