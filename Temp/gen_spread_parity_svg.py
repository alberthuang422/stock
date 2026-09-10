# -*- coding: utf-8 -*-
"""生成：三段月差拉升同步性 SVG"""
import csv, os, statistics

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cl_contracts', 'daily')
BLUE, ORANGE, VERM, GREEN, SKY, PURPLE = '#56B4E9', '#E69F00', '#D55E00', '#009E73', '#8FD6F5', '#CC79A7'
BG, GRID, TXT, MUTE = '#17191d', '#2c3037', '#e8eaed', '#8b929c'

def load(c):
    out = {}
    with open(os.path.join(BASE, f'US.CL{c}.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try: out[r['date']] = float(r['close'])
            except: pass
    return out

C = {c: load(c) for c in ['2610','2611','2612','2701']}
dates = sorted(set(C['2610']) & set(C['2611']) & set(C['2612']) & set(C['2701']))
segs = [('OCT-NOV', '2610','2611', BLUE), ('NOV-DEC','2611','2612', ORANGE), ('DEC-JAN','2612','2701', GREEN)]
series = {n: {d: C[a][d]-C[b][d] for d in dates} for n,a,b,_ in segs}

W, H = 680, 630
out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">']
out.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
out.append(f'<text x="20" y="28" fill="{TXT}" font-size="15" font-weight="600">三段月差同步性检验 · 平行陡化还是单段走强</text>')
out.append(f'<text x="20" y="47" fill="{MUTE}" font-size="10.5">CL 期货 2026-03-10 ~ 09-10  ·  日线收盘  ·  月差 = 近月 − 远月</text>')

# ---- 面板 1: 三条月差绝对值走势 ----
pw, ph = 640, 190
px, py = 20, 66
out.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#1c1f24" rx="5" stroke="{GRID}"/>')
out.append(f'<text x="{px+10}" y="{py+18}" fill="{TXT}" font-size="11.5" font-weight="600">① 三段月差绝对值（$）</text>')

lo, hi = 0, 4.3
def X(i): return px + 55 + i * (pw - 75) / (len(dates)-1)
def Y1(v): return py + ph - 22 - (v-lo)/(hi-lo)*(ph-45)

for v in [0,1,2,3,4]:
    y = Y1(v)
    out.append(f'<line x1="{px+55}" y1="{y:.1f}" x2="{px+pw-20}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.6"/>')
    out.append(f'<text x="{px+48}" y="{y+3.5:.1f}" fill="{MUTE}" font-size="9" text-anchor="end">{v}</text>')

for n, a, b, col in segs:
    pts = ' '.join(f'{X(i):.1f},{Y1(series[n][d]):.1f}' for i, d in enumerate(dates))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.9" stroke-linejoin="round"/>')

# 图例
lx = px + 300
for k,(n,a,b,col) in enumerate(segs):
    out.append(f'<line x1="{lx+k*105}" y1="{py+15}" x2="{lx+k*105+16}" y2="{py+15}" stroke="{col}" stroke-width="2.4"/>')
    out.append(f'<text x="{lx+k*105+20}" y="{py+18.5}" fill="{MUTE}" font-size="9.5">{n}</text>')

for d, lbl in [('2026-07-23','7/23'), ('2026-08-05','8/5'), ('2026-09-10','9/10')]:
    i = dates.index(d); x = X(i)
    out.append(f'<line x1="{x:.1f}" y1="{py+22}" x2="{x:.1f}" y2="{py+ph-20}" stroke="{MUTE}" stroke-width="0.6" stroke-dasharray="2,3" opacity="0.55"/>')
    out.append(f'<text x="{x:.1f}" y="{py+ph-8}" fill="{MUTE}" font-size="8.5" text-anchor="middle">{lbl}</text>')

# ---- 面板 2: 归一化累计（σ 标准化）----
py2 = py + ph + 14
out.append(f'<rect x="{px}" y="{py2}" width="{pw}" height="{ph}" fill="#1c1f24" rx="5" stroke="{GRID}"/>')
out.append(f'<text x="{px+10}" y="{py2+18}" fill="{TXT}" font-size="11.5" font-weight="600">② σ 标准化累计涨幅（8/12=0 起算，看同形度）</text>')

deltas = {n: [series[n][dates[i]]-series[n][dates[i-1]] for i in range(1,len(dates))] for n,a,b,c in segs}
sig = {n: statistics.stdev(deltas[n]) for n,a,b,c in segs}
cum = {n: [0.0] for n,a,b,c in segs}
for i in range(1, len(dates)):
    for n,a,b,c in segs:
        cum[n].append(cum[n][-1] + deltas[n][i-1]/sig[n])

i0 = dates.index('2026-08-12')
sdates = dates[i0:]
lo2, hi2 = 0, 11.5
def X2(i): return px + 55 + i * (pw - 75) / (len(sdates)-1)
def Y2(v): return py2 + ph - 22 - (v-lo2)/(hi2-lo2)*(ph-45)

for v in [0,3,6,9]:
    y = Y2(v)
    out.append(f'<line x1="{px+55}" y1="{y:.1f}" x2="{px+pw-20}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.6"/>')
    out.append(f'<text x="{px+48}" y="{y+3.5:.1f}" fill="{MUTE}" font-size="9" text-anchor="end">{v}</text>')

for n,a,b,col in segs:
    pts = ' '.join(f'{X2(k):.1f},{Y2(cum[n][i0+k]):.1f}' for k in range(len(sdates)))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.9" stroke-linejoin="round"/>')

# 关键数值标注
k_end = len(sdates)-1
for n,a,b,col in segs:
    v = cum[n][-1]
    out.append(f'<circle cx="{X2(k_end):.1f}" cy="{Y2(v):.1f}" r="3" fill="{col}"/>')
    out.append(f'<text x="{X2(k_end)-6:.1f}" y="{Y2(v)-7:.1f}" fill="{col}" font-size="9" text-anchor="end" font-weight="600">{v:.1f}σ</text>')

for d, lbl in [('2026-08-12','8/12'),('2026-09-03','9/3'),('2026-09-10','9/10')]:
    if d in sdates:
        k = sdates.index(d); x = X2(k)
        out.append(f'<line x1="{x:.1f}" y1="{py2+22}" x2="{x:.1f}" y2="{py2+ph-20}" stroke="{MUTE}" stroke-width="0.6" stroke-dasharray="2,3" opacity="0.55"/>')
        out.append(f'<text x="{x:.1f}" y="{py2+ph-8}" fill="{MUTE}" font-size="8.5" text-anchor="middle">{lbl}</text>')

# ---- 面板 3: 结论条 ----
py3 = py2 + ph + 14
out.append(f'<rect x="{px}" y="{py3}" width="{pw}" height="86" fill="#1c1f24" rx="5" stroke="{GRID}"/>')
out.append(f'<text x="{px+12}" y="{py3+20}" fill="{TXT}" font-size="11.5" font-weight="600">③ 结论</text>')
lines = [
    (f'8/5 谷底 → 9/10 累计涨幅：OCT-NOV +$2.47  |  NOV-DEC +$2.74  |  DEC-JAN +$2.45  →  三段几乎等量', GREEN),
    (f'日变化相关性：OCT-NOV×NOV-DEC = 0.840（高度同步）；三段同涨同跌，无独立行情', ORANGE),
    (f'唯一分化在最近 6 日：9/3→9/10 NOV-DEC +$0.62（+18.9%）> OCT-NOV +$0.20（+5.9%）', VERM),
    (f'判定：主趋势 = 全曲线平行陡化；NOV-DEC 的额外优势仅来自最近一周，且 DEC-JAN 同时也在补涨', SKY),
]
for k,(t,col) in enumerate(lines):
    out.append(f'<line x1="{px+12}" y1="{py3+32+k*15}" x2="{px+18}" y2="{py3+32+k*15}" stroke="{col}" stroke-width="2.4"/>')
    out.append(f'<text x="{px+24}" y="{py3+35.5+k*15}" fill="{TXT}" font-size="9.6">{t}</text>')

out.append('</svg>')
svg = '\n'.join(out)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spread_parity.svg'), 'w', encoding='utf-8') as f:
    f.write(svg)

import re
bad = [m for m in re.findall(r'<text[^>]*y="([\d.]+)"', svg) if float(m) > H or float(m) < 0]
print('生成完成: Temp/spread_parity.svg  溢出元素:', len(bad))
