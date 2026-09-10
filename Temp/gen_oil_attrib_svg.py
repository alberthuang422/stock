# -*- coding: utf-8 -*-
"""生成 2026年7-9月 WTI 近月连续合约走势 + 事件归因图"""
import csv, sys

R = list(csv.DictReader(open('data/cl_contracts/daily/US.CLcurrent.csv', encoding='utf-8')))
D = {r['date']: r for r in R}
ds = [d for d in sorted(D) if '2026-06-25' <= d <= '2026-09-10']
n = len(ds)

# ---- 画布 ----
W, H = 680, 612
A = []
A.append('<svg viewBox="0 0 680 612" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,\'Segoe UI\',\'Microsoft YaHei\',sans-serif">')
A.append('<rect width="680" height="612" fill="#17191d" rx="10"/>')

# 配色（Okabe-Ito，深色底）
BLUE   = '#56B4E9'
ORANGE = '#E69F00'
VERM   = '#D55E00'
SKY    = '#8FD6F5'
GREEN  = '#009E73'
TXT    = '#e6e9ec'
DIM    = '#9aa0a6'
GRID   = '#2a2e35'
PANEL  = '#1c1f24'

# ---- Panel 1: 价格 ----
PL, PR, PT, PB = 54, 596, 66, 356
lo, hi = 67.0, 100.0

def px(i): return PL + i * (PR - PL) / (n - 1)
def py(v): return PB - (v - lo) / (hi - lo) * (PB - PT)

# 标题
A.append(f'<text x="24" y="30" fill="{TXT}" font-size="15" font-weight="700">WTI 近月连续合约 · 2026/06/25 – 09/10</text>')
A.append(f'<text x="24" y="49" fill="{DIM}" font-size="11.5">真实日线收盘价（$ / 桶）｜数据：项目内 CLcurrent 连续合约，128 日</text>')

# 网格 + y 轴
for v in range(70, 101, 5):
    y = py(v)
    A.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.8"/>')
    A.append(f'<text x="{PL-8}" y="{y+3.5:.1f}" fill="{DIM}" font-size="10" text-anchor="end">{v}</text>')

# x 轴刻度（每月 1 日 + 关键日）
def xi_of(d):
    return ds.index(d) if d in ds else None
for d in ['2026-07-01', '2026-08-03', '2026-09-01']:
    i = xi_of(d)
    if i is None: continue
    A.append(f'<line x1="{px(i):.1f}" y1="{PT}" x2="{px(i):.1f}" y2="{PB}" stroke="{GRID}" stroke-width="0.7" stroke-dasharray="2 4"/>')
    A.append(f'<text x="{px(i):.1f}" y="{PB+16}" fill="{DIM}" font-size="10" text-anchor="middle">{d[5:7]}/{d[8:10]}</text>')

# 价格折线 + 面积
pts = [(px(i), py(float(D[d]['close']))) for i, d in enumerate(ds)]
poly = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
A.append(f'<polygon points="{PL},{py(lo):.1f} {poly} {PR},{py(lo):.1f}" fill="{BLUE}" opacity="0.10"/>')
A.append(f'<polyline points="{poly}" fill="none" stroke="{BLUE}" stroke-width="2.1" stroke-linejoin="round"/>')

# ---- 关键节点标注 ----
# (日期, 值, 标签, 标签dy, 符号, 颜色)
EV = [
    ('2026-07-20', 82.96, '7/20 胡塞封锁红海', -18, '▲', ORANGE),
    ('2026-07-23', 92.36, '7/23 峰值 93.5', 0, '★', VERM),
    ('2026-07-27', 81.91, '7/27 缓和信号 −9.5%', 0, '▼', VERM),
    ('2026-08-03', 80.06, '8/3 取消打击+宣布谈判 −7.8%', 0, '▼', VERM),
    ('2026-08-05', 75.08, '8/5 谷底 75.1', 0, '●', GREEN),
    ('2026-09-10', 97.20, '9/10  97.2', 0, '●', SKY),
]
for d, v, lab, dy, sym, col in EV:
    i = xi_of(d)
    if i is None: continue
    x, y = px(i), py(float(D[d]['close']))
    A.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{col}" stroke="#17191d" stroke-width="1.2"/>')
    # 竖线连到顶部
    A.append(f'<line x1="{x:.1f}" y1="{PT-4}" x2="{x:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="0.8" stroke-dasharray="2 3" opacity="0.55"/>')

# 手工放置文字标签，避免重叠
LBL = [
    (px(xi_of('2026-07-20')), py(82.96)-19, '7/20 胡塞封锁红海', 'middle', ORANGE, 3),
    (px(xi_of('2026-07-23')), py(92.36)-12, '7/23 峰值 93.5', 'middle', VERM, 0),
    (px(xi_of('2026-07-27'))-4, py(81.91)+18, '7/27 缓和信号 −9.5%', 'end', VERM, 0),
    (px(xi_of('2026-08-03'))+6, py(80.06)-26, '8/3 取消打击+宣布谈判', 'start', VERM, 0),
    (px(xi_of('2026-08-03'))+6, py(80.06)-13, '单日 −7.8%', 'start', VERM, 0),
    (px(xi_of('2026-08-05')), py(75.08)+17, '8/5 谷底 75.1', 'middle', GREEN, 0),
    (px(xi_of('2026-09-10'))-2, py(97.20)-12, '9/10  97.2', 'end', SKY, 0),
]
for x, y, lab, anc, col, _ in LBL:
    if anc == 'start' and x > 470: anc = 'end'
    A.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{col}" font-size="10.5" font-weight="600" text-anchor="{anc}" '
             f'paint-order="stroke" stroke="#17191d" stroke-width="2.8" stroke-linejoin="round">{lab}</text>')

# 峰值/谷底水平参考线
for v, lab, col in [(93.50, '峰值 93.5', VERM), (75.08, '谷底 75.1', GREEN)]:
    y = py(v)
    A.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{PR}" y2="{y:.1f}" stroke="{col}" stroke-width="0.7" stroke-dasharray="5 4" opacity="0.5"/>')

# 跌幅箭头（7/23 -> 8/5）
x1, y1 = px(xi_of('2026-07-23')), py(92.36)
x2, y2 = px(xi_of('2026-08-05')), py(75.08)
A.append(f'<path d="M {x1+8:.1f} {y1-6:.1f} Q {(x1+x2)/2:.1f} {(y1+y2)/2+26:.1f} {x2-4:.1f} {y2-8:.1f}" fill="none" stroke="{VERM}" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.75"/>')
A.append(f'<text x="{(x1+x2)/2+16:.1f}" y="271" fill="{VERM}" font-size="11" font-weight="700" text-anchor="middle" paint-order="stroke" stroke="#17191d" stroke-width="3">8 个交易日 −19.5%</text>')

# ---- Panel 2: 归因分层 ----
PY0 = 392
A.append(f'<rect x="24" y="{PY0}" width="632" height="196" rx="8" fill="{PANEL}"/>')
A.append(f'<text x="40" y="{PY0+24}" fill="{TXT}" font-size="13" font-weight="700">这波跌的是什么：三层归因</text>')

rows = [
    ('触发', VERM, '地缘溢价「政治性出清」',
     '7/27 缓和信号 → 8/3 特朗普取消打击、宣布谈判（条件：重开霍尔木兹）',
     '市场瞬时计价「海峡重开、Gulf 桶回归」→ 7 月堆积的战争溢价一次性吐出'),
    ('放大', ORANGE, '基本面数据偏空（助攻，非触发器）',
     'EIA 8/7 当周原油 +1740 万桶（史上第二大）｜OPEC/IEA 下调 2026 需求',
     '出口骤降 + 进口激增的「物流性堆积」；OPEC+ 增产、俄黑海出口回暖'),
    ('反证', GREEN, '为什么是溢价出清，不是趋势反转',
     '柴油裂解价差 8 月破 $100 创历史极值，原油跌、成品油不跌',
     'SPR 2.99 亿桶（40 年最低）｜IEA：开战以来库存 −4.1 亿桶，7 月再 −6900 万'),
]
yy = PY0 + 44
for tag, col, title, sub1, sub2 in rows:
    A.append(f'<rect x="40" y="{yy-11}" width="42" height="17" rx="4" fill="{col}" opacity="0.20" stroke="{col}" stroke-width="0.9"/>')
    A.append(f'<text x="61" y="{yy+1.5}" fill="{col}" font-size="10" font-weight="700" text-anchor="middle">{tag}</text>')
    A.append(f'<text x="92" y="{yy+2}" fill="{TXT}" font-size="11.5" font-weight="600">{title}</text>')
    A.append(f'<text x="92" y="{yy+19}" fill="{DIM}" font-size="10.3">{sub1}</text>')
    A.append(f'<text x="92" y="{yy+34}" fill="{DIM}" font-size="10.3">{sub2}</text>')
    yy += 52

A.append('<text x="24" y="604" fill="#6b7076" font-size="9.5">数据：项目内 CLcurrent 近月连续合约（2026-03-10 起 128 日）；事件经 Reuters / CGTN / 每日经济新闻 / EIA / Saxo 交叉核实</text>')
A.append('</svg>')

open('Temp/oil_attrib.svg', 'w', encoding='utf-8').write('\n'.join(A))
print('OK n_bars =', n, ' range', ds[0], '->', ds[-1])
