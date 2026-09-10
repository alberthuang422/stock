# -*- coding: utf-8 -*-
"""OCT-NOV vs NOV-DEC：7/23 高点对比 + NOV 相对强度"""
import csv, sys

codes = ['CL2610', 'CL2611', 'CL2612', 'CL2701']
D = {c: list(csv.DictReader(open(f'data/cl_contracts/daily/US.{c}.csv', encoding='utf-8'))) for c in codes}
dates = [r['date'] for r in D['CL2610']]
cl = {c: [float(r['close']) for r in D[c]] for c in codes}
n = len(dates)
s1 = [cl['CL2610'][i] - cl['CL2611'][i] for i in range(n)]   # OCT-NOV
s2 = [cl['CL2611'][i] - cl['CL2612'][i] for i in range(n)]   # NOV-DEC

# 样本：7/20 起
i0 = dates.index('2026-07-20')
idx = list(range(i0, n))
N = len(idx)
lab = [dates[i][5:] for i in idx]

W, H = 680, 596
A = []
A.append('<svg viewBox="0 0 680 596" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,\'Segoe UI\',\'Microsoft YaHei\',sans-serif">')
A.append('<rect width="680" height="596" fill="#17191d" rx="10"/>')

BLUE   = '#56B4E9'
ORANGE = '#E69F00'
VERM   = '#D55E00'
SKY    = '#8FD6F5'
GREEN  = '#009E73'
PURPLE = '#CC79A7'
TXT    = '#e6e9ec'
DIM    = '#9aa0a6'
GRID   = '#2a2e35'
PANEL  = '#1c1f24'

A.append(f'<text x="24" y="30" fill="{TXT}" font-size="15" font-weight="700">OCT-NOV  vs  NOV-DEC  ·  7/20 – 9/10</text>')
A.append(f'<text x="24" y="49" fill="{DIM}" font-size="11.5">真实日线收盘价差（$ / 桶，近月 − 远月）｜项目内 CL2610/2611/2612 具体合约</text>')

# ---- Panel 1: 两条价差叠加 ----
PL, PR, PT, PB = 58, 588, 66, 300
lo, hi = 0.8, 4.3
def px(i): return PL + i * (PR - PL) / (N - 1)
def py(v): return PB - (v - lo) / (hi - lo) * (PB - PT)

for v in [1, 2, 3, 4]:
    y = py(v)
    A.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.8"/>')
    A.append(f'<text x="{PL-8}" y="{y+3.5:.1f}" fill="{DIM}" font-size="10" text-anchor="end">{v}</text>')

# x 刻度
for d in ['2026-07-23', '2026-08-05', '2026-09-03', '2026-09-10']:
    i = dates.index(d); j = i - i0
    A.append(f'<line x1="{px(j):.1f}" y1="{PT}" x2="{px(j):.1f}" y2="{PB}" stroke="{GRID}" stroke-width="0.7" stroke-dasharray="2 4"/>')
    A.append(f'<text x="{px(j):.1f}" y="{PB+16}" fill="{DIM}" font-size="10" text-anchor="middle">{d[5:7]}/{d[8:10]}</text>')

p1 = ' '.join(f'{px(j):.1f},{py(s1[i]):.1f}' for j, i in enumerate(idx))
p2 = ' '.join(f'{px(j):.1f},{py(s2[i]):.1f}' for j, i in enumerate(idx))
A.append(f'<polyline points="{p1}" fill="none" stroke="{BLUE}" stroke-width="2.2" stroke-linejoin="round"/>')
A.append(f'<polyline points="{p2}" fill="none" stroke="{ORANGE}" stroke-width="2.2" stroke-dasharray="7 3" stroke-linejoin="round"/>')

# 7/23 高点水平线
y723_1 = py(4.08); y723_2 = py(2.80)
A.append(f'<line x1="{PL}" y1="{y723_1:.1f}" x2="{PR}" y2="{y723_1:.1f}" stroke="{BLUE}" stroke-width="0.9" stroke-dasharray="6 4" opacity="0.55"/>')
A.append(f'<line x1="{PL}" y1="{y723_2:.1f}" x2="{PR}" y2="{y723_2:.1f}" stroke="{ORANGE}" stroke-width="0.9" stroke-dasharray="6 4" opacity="0.55"/>')

# 关键点
i723j = dates.index('2026-07-23') - i0
i_end = N - 1
for j, v, col in [(i723j, 4.08, BLUE), (i723j, 2.80, ORANGE), (i_end, 3.61, BLUE), (i_end, 3.90, ORANGE)]:
    A.append(f'<circle cx="{px(j):.1f}" cy="{py(v):.1f}" r="3.8" fill="{col}" stroke="#17191d" stroke-width="1.3"/>')

# 标注
def tx(x, y, t, col, anc='middle', fs=10.5, w='600'):
    A.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{col}" font-size="{fs}" font-weight="{w}" text-anchor="{anc}" '
             f'paint-order="stroke" stroke="#17191d" stroke-width="3" stroke-linejoin="round">{t}</text>')

tx(px(i723j) - 6, py(4.08) - 12, '7/23 高点 4.08', BLUE, 'end')
tx(px(i723j) + 8, py(2.80) + 17, '7/23 高点 2.80', ORANGE, 'start')
tx(px(i_end) - 4, py(3.90) - 13, 'NOV-DEC 3.90', ORANGE, 'end')
tx(px(i_end) - 4, py(3.61) + 19, 'OCT-NOV 3.61', BLUE, 'end')

# 突破/未突破 结论标
tx(px(i_end) - 108, py(3.90) + 4, '✓ 突破 +39%', VERM, 'end', 11, '700')
tx(px(i_end) - 108, py(3.61) + 22, '✗ 未过 −11.5%', GREEN, 'end', 11, '700')

# 图例
A.append(f'<rect x="{PL+196}" y="{PT+8}" width="176" height="46" rx="6" fill="{PANEL}" opacity="0.92"/>')
A.append(f'<line x1="{PL+208}" y1="{PT+24}" x2="{PL+230}" y2="{PT+24}" stroke="{BLUE}" stroke-width="2.4"/>')
A.append(f'<text x="{PL+238}" y="{PT+27.5}" fill="{TXT}" font-size="10.5">OCT-NOV（前端 M1-M2）</text>')
A.append(f'<line x1="{PL+208}" y1="{PT+42}" x2="{PL+230}" y2="{PT+42}" stroke="{ORANGE}" stroke-width="2.4" stroke-dasharray="7 3"/>')
A.append(f'<text x="{PL+238}" y="{PT+45.5}" fill="{TXT}" font-size="10.5">NOV-DEC（次段 M2-M3）</text>')

# ---- Panel 2: NOV 相对强度 ----
P2T, P2B = 344, 500
def py2(v): return P2B - (v - 95) / (108 - 95) * (P2B - P2T)
A.append(f'<text x="24" y="{P2T-12}" fill="{TXT}" font-size="12.5" font-weight="700">NOV 相对强度（指数，7/23 = 100）：相对后端强、相对前端平</text>')

for v in [96, 100, 104, 108]:
    y = py2(v)
    A.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.8"/>')
    A.append(f'<text x="{PL-8}" y="{y+3.5:.1f}" fill="{DIM}" font-size="10" text-anchor="end">{v}</text>')
A.append(f'<line x1="{PL}" y1="{py2(100):.1f}" x2="{PR}" y2="{py2(100):.1f}" stroke="#5a5f66" stroke-width="1.1" stroke-dasharray="4 3"/>')

def idxab(a, b, i): return cl[a][i] / cl[b][i] / (cl[a][dates.index('2026-07-23')] / cl[b][dates.index('2026-07-23')]) * 100
r_no = [idxab('CL2611', 'CL2610', i) for i in idx]
r_nd = [idxab('CL2611', 'CL2612', i) for i in idx]
r_nj = [idxab('CL2611', 'CL2701', i) for i in idx]
for ser, col, dash in [(r_no, BLUE, ''), (r_nd, ORANGE, '7 3'), (r_nj, PURPLE, '2 3')]:
    pts = ' '.join(f'{px(j):.1f},{py2(v):.1f}' for j, v in enumerate(ser))
    A.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-dasharray="{dash}" stroke-linejoin="round"/>')

# 末端标签（错开）
for j in [i_end]:
    A.append(f'<circle cx="{px(j):.1f}" cy="{py2(r_no[j]):.1f}" r="3.2" fill="{BLUE}"/>')
    A.append(f'<circle cx="{px(j):.1f}" cy="{py2(r_nd[j]):.1f}" r="3.2" fill="{ORANGE}"/>')
    A.append(f'<circle cx="{px(j):.1f}" cy="{py2(r_nj[j]):.1f}" r="3.2" fill="{PURPLE}"/>')

tx(px(i_end) - 6, py2(r_nj[i_end]) - 10, 'vs JAN 102.1', PURPLE, 'end')
tx(px(i_end) - 6, py2(r_nd[i_end]) + 4, 'vs DEC 100.8', ORANGE, 'end')
tx(px(i_end) - 6, py2(r_no[i_end]) + 17, 'vs OCT 101.0', BLUE, 'end')

# Panel3 结论条
P3T = 512
A.append(f'<rect x="24" y="{P3T}" width="632" height="72" rx="8" fill="{PANEL}"/>')
A.append(f'<text x="40" y="{P3T+22}" fill="{TXT}" font-size="12" font-weight="700">结论：11 月「变强」是错觉对了一半 —— 强的是 NOV-DEC 这一段，不是 NOV 这个合约</text>')
A.append(f'<text x="40" y="{P3T+41}" fill="{DIM}" font-size="10.5">① OCT-NOV 的 4.08 是 7/23 事件尖峰（单日冲高），非阶段高点，现已回落 −11.5%</text>')
A.append(f'<text x="40" y="{P3T+57}" fill="{DIM}" font-size="10.5">② NOV-DEC 的 2.80 是普通水平，现 3.90 是 128 日真新高 → 突破真实；NOV 相对 OCT 仅 +0.5%</text>')

A.append('<text x="24" y="596" fill="#6b7076" font-size="9.5">数据：项目内 data/cl_contracts/daily/US.CL26xx.csv（2026-03-10 起 128 日，非僵尸填充）</text>')
A.append('</svg>')

open('Temp/nov_strength.svg', 'w', encoding='utf-8').write('\n'.join(A))
print('OK')
