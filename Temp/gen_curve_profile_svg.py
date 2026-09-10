# -*- coding: utf-8 -*-
"""原油月差曲线结构画像 SVG"""
import csv, os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cl_contracts', 'daily')
BLUE, ORANGE, VERM, GREEN, SKY, PURPLE = '#56B4E9', '#E69F00', '#D55E00', '#009E73', '#8FD6F5', '#CC79A7'
BG, CARD, GRID, TXT, MUTE = '#17191d', '#1c1f24', '#2c3037', '#e8eaed', '#8b929c'

CS = ['2610','2611','2612','2701','2702','2703']
def load(c):
    out = {}
    with open(os.path.join(BASE, f'US.CL{c}.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try: out[r['date']] = float(r['close'])
            except: pass
    return out
D = {c: load(c) for c in CS}
TODAY = '2026-09-10'
px = [D[c][TODAY] for c in CS]
segs = [px[i]-px[i+1] for i in range(5)]
total = px[0]-px[-1]

W, H = 680, 720
o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">']
o.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
o.append(f'<text x="20" y="28" fill="{TXT}" font-size="15" font-weight="600">WTI 原油月差曲线结构画像 · 2026-09-10</text>')
o.append(f'<text x="20" y="47" fill="{MUTE}" font-size="10.5">6 个合约逐段拆解 · 收盘价 · 近月 − 远月（正值 = backwardation）</text>')

# ===== 面板 1: 曲线本身（价格 vs 合约月份）=====
px_, py_, pw_, ph_ = 20, 66, 640, 200
o.append(f'<rect x="{px_}" y="{py_}" width="{pw_}" height="{ph_}" fill="{CARD}" rx="5" stroke="{GRID}"/>')
o.append(f'<text x="{px_+12}" y="{py_+19}" fill="{TXT}" font-size="11.5" font-weight="600">① 曲线点位：严格单调递减，全程 backwardation</text>')

lo, hi = 78, 100
def XP(i): return px_ + 72 + i * (pw_ - 105) / (len(CS)-1)
def YP(v): return py_ + ph_ - 42 - (v-lo)/(hi-lo)*(ph_-72)

for v in [80,85,90,95,100]:
    y = YP(v)
    o.append(f'<line x1="{px_+62}" y1="{y:.1f}" x2="{px_+pw_-22}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.6"/>')
    o.append(f'<text x="{px_+56}" y="{y+3.5:.1f}" fill="{MUTE}" font-size="9" text-anchor="end">{v}</text>')

pts = ' '.join(f'{XP(i):.1f},{YP(v):.1f}' for i, v in enumerate(px))
o.append(f'<polygon points="{XP(0):.1f},{YP(px[0]):.1f} {pts} {XP(5):.1f},{py_+ph_-42} {XP(0):.1f},{py_+ph_-42}" fill="{BLUE}" opacity="0.10"/>')
o.append(f'<polyline points="{pts}" fill="none" stroke="{SKY}" stroke-width="2.4" stroke-linejoin="round"/>')

lbls = ['OCT26','NOV26','DEC26','JAN27','FEB27','MAR27']
for i, (v, l) in enumerate(zip(px, lbls)):
    x, y = XP(i), YP(v)
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{SKY}" stroke="{BG}" stroke-width="1.4"/>')
    o.append(f'<text x="{x:.1f}" y="{y-9:.1f}" fill="{TXT}" font-size="9.8" font-weight="600" text-anchor="middle">{v:.2f}</text>')
    o.append(f'<text x="{x:.1f}" y="{py_+ph_-24:.1f}" fill="{MUTE}" font-size="9" text-anchor="middle">{l}</text>')
    o.append(f'<text x="{x:.1f}" y="{py_+ph_-12:.1f}" fill="{MUTE}" font-size="8" text-anchor="middle">M{i+1}</text>')

# 标注总幅度
o.append(f'<text x="{px_+pw_-24}" y="{py_+30}" fill="{GREEN}" font-size="10.5" text-anchor="end" font-weight="600">M1−M6 = ${total:.2f}</text>')

# ===== 面板 2: 逐段柱状 + 占比 =====
py2 = py_ + ph_ + 14
o.append(f'<rect x="{px_}" y="{py2}" width="{pw_}" height="175" fill="{CARD}" rx="5" stroke="{GRID}"/>')
o.append(f'<text x="{px_+12}" y="{py2+19}" fill="{TXT}" font-size="11.5" font-weight="600">② 逐段月差（$）· 峰值落在 M2-M3（NOV-DEC）</text>')

bx = px_ + 60
bw = (pw_ - 100) / 5
bmax = 4.2
base_y = py2 + 140
seg_names = ['10-11','11-12','12-01','01-02','02-03']

for i, (s, n) in enumerate(zip(segs, seg_names)):
    x = bx + i * bw
    h = s / bmax * 96
    y = base_y - h
    col = VERM if i == 1 else BLUE
    o.append(f'<rect x="{x+8:.1f}" y="{y:.1f}" width="{bw-24:.1f}" height="{h:.1f}" fill="{col}" rx="2"/>')
    o.append(f'<text x="{x+bw/2-4:.1f}" y="{y-6:.1f}" fill="{TXT}" font-size="10.5" font-weight="600" text-anchor="middle">{s:.2f}</text>')
    o.append(f'<text x="{x+bw/2-4:.1f}" y="{base_y+15:.1f}" fill="{TXT}" font-size="9.2" text-anchor="middle">{n}</text>')
    o.append(f'<text x="{x+bw/2-4:.1f}" y="{base_y+29:.1f}" fill="{MUTE}" font-size="8.4" text-anchor="middle">{s/total*100:.1f}%</text>')

o.append(f'<line x1="{bx}" y1="{base_y}" x2="{bx+5*bw-16}" y2="{base_y}" stroke="{MUTE}" stroke-width="0.8"/>')
o.append(f'<text x="{px_+12}" y="{py2+166}" fill="{MUTE}" font-size="8.8">柱高 = 月差绝对额；下方百分比 = 该段占 M1−M6 总幅度的比重</text>')

# ===== 面板 3: 形态演变对比 =====
py3 = py2 + 175 + 14
o.append(f'<rect x="{px_}" y="{py3}" width="{pw_}" height="180" fill="{CARD}" rx="5" stroke="{GRID}"/>')
o.append(f'<text x="{px_+12}" y="{py3+19}" fill="{TXT}" font-size="11.5" font-weight="600">③ 曲线形状演变：从「前端独陡」到「平行陡化」</text>')

hist = [('07-23', '2026-07-23', BLUE), ('08-05', '2026-08-05', GREEN), ('09-03', '2026-09-03', ORANGE), ('09-10', '2026-09-10', VERM)]
rows_ = []
for lbl, d, col in hist:
    if all(d in D[c] for c in CS):
        p = [D[c][d] for c in CS]
        s = [p[i]-p[i+1] for i in range(5)]
        t = p[0]-p[-1]
        rows_.append((lbl, [x/t*100 for x in s], t, col))

# 表头
hx = px_ + 60; hw = (pw_ - 95) / 5
o.append(f'<text x="{px_+12}" y="{py3+40}" fill="{MUTE}" font-size="8.6">段占比</text>')
for i, n in enumerate(seg_names):
    o.append(f'<text x="{hx+i*hw+hw/2:.1f}" y="{py3+40}" fill="{MUTE}" font-size="8.6" text-anchor="middle">{n}</text>')

for k, (lbl, ratios, t, col) in enumerate(rows_):
    y = py3 + 56 + k * 29
    o.append(f'<text x="{px_+12}" y="{y+12}" fill="{TXT}" font-size="9.4" font-weight="600">{lbl}</text>')
    o.append(f'<text x="{px_+12}" y="{y+23}" fill="{col}" font-size="7.8">总${t:.1f}</text>')
    for i, r in enumerate(ratios):
        w = r / 40 * (hw - 14)
        o.append(f'<rect x="{hx+i*hw+2:.1f}" y="{y+3:.1f}" width="{w:.1f}" height="15" fill="{col}" opacity="0.80" rx="1.5"/>')
        o.append(f'<text x="{hx+i*hw+6:.1f}" y="{y+14:.1f}" fill="#0d0f12" font-size="8" font-weight="600">{r:.0f}%</text>')

o.append(f'<line x1="{px_+12}" y1="{py3+172}" x2="{px_+pw_-12}" y2="{py3+172}" stroke="{GRID}" stroke-width="0.6"/>')
o.append(f'<text x="{px_+12}" y="{py3+172}" fill="{MUTE}" font-size="0.1"> </text>')

# 结论条
py4 = py3 + 180 + 10
o.append(f'<rect x="{px_}" y="{py4}" width="{pw_}" height="46" fill="{CARD}" rx="5" stroke="{GRID}"/>')
o.append(f'<text x="{px_+12}" y="{py4+17}" fill="{TXT}" font-size="10.5" font-weight="600">结论</text>')
o.append(f'<text x="{px_+50}" y="{py4+17}" fill="{TXT}" font-size="9.3">全程 backwardation，五段全部处于 128 日 97.7–99.2% 分位</text>')
o.append(f'<text x="{px_+50}" y="{py4+33}" fill="{TXT}" font-size="9.3">形态已由「前端独陡」（7/23：M1-M2 占 36%）转为「平行陡化」（9/10：M2-M3 占 24%，衰减趋缓）</text>')

o.append('</svg>')
svg = '\n'.join(o)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spread_curve_profile.svg'), 'w', encoding='utf-8') as f:
    f.write(svg)

import re
bad = [m for m in re.findall(r'<text[^>]*y="([\d.]+)"', svg) if float(m) > H+2 or float(m) < -2]
print('生成: Temp/spread_curve_profile.svg  溢出:', len(bad))
