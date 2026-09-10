# -*- coding: utf-8 -*-
"""OCT-NOV 是否天然更强：128日全样本 + 比值制度切换"""
import csv, sys, statistics as st
sys.stdout.reconfigure(encoding='utf-8')

codes = ['CL2610', 'CL2611', 'CL2612']
D = {c: list(csv.DictReader(open(f'data/cl_contracts/daily/US.{c}.csv', encoding='utf-8'))) for c in codes}
dates = [r['date'] for r in D['CL2610']]
cl = {c: [float(r['close']) for r in D[c]] for c in codes}
n = len(dates)
s1 = [cl['CL2610'][i] - cl['CL2611'][i] for i in range(n)]
s2 = [cl['CL2611'][i] - cl['CL2612'][i] for i in range(n)]

W, H = 680, 620
A = []
A.append('<svg viewBox="0 0 680 620" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,\'Segoe UI\',\'Microsoft YaHei\',sans-serif">')
A.append('<rect width="680" height="620" fill="#17191d" rx="10"/>')

BLUE, ORANGE, VERM, GREEN, PURPLE = '#56B4E9', '#E69F00', '#D55E00', '#009E73', '#CC79A7'
TXT, DIM, GRID, PANEL = '#e6e9ec', '#9aa0a6', '#2a2e35', '#1c1f24'

A.append(f'<text x="24" y="30" fill="{TXT}" font-size="15" font-weight="700">「OCT-NOV 天然更强」成立吗？· 128 日全样本检验</text>')
A.append(f'<text x="24" y="49" fill="{DIM}" font-size="11.5">比值 NOV-DEC ÷ OCT-NOV（&gt;1 = 次段更陡，即挤压点后移）</text>')

# ---- Panel 1: 比值时间序列 ----
PL, PR, PT, PB = 58, 588, 68, 268
lo, hi = 0.4, 1.7
def px(i): return PL + i * (PR - PL) / (n - 1)
def py(v): return PB - (v - lo) / (hi - lo) * (PB - PT)

for v in [0.5, 0.75, 1.0, 1.25]:
    y = py(v)
    A.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.8"/>')
    A.append(f'<text x="{PL-8}" y="{y+3.5:.1f}" fill="{DIM}" font-size="10" text-anchor="end">{v}</text>')
# y=1 基准强调
A.append(f'<line x1="{PL}" y1="{py(1.0):.1f}" x2="{PR}" y2="{py(1.0):.1f}" stroke="#7a7f86" stroke-width="1.3" stroke-dasharray="5 3"/>')
A.append(f'<text x="{PR-4}" y="{py(1.0)-6:.1f}" fill="#9aa0a6" font-size="10" text-anchor="end">比值 = 1（分界）</text>')

# 阴影：切换后
i_sw = dates.index('2026-08-05')
A.append(f'<rect x="{px(i_sw):.1f}" y="{PT}" width="{PR-px(i_sw):.1f}" height="{PB-PT}" fill="{VERM}" opacity="0.12"/>')
A.append(f'<text x="{px(i_sw)+10:.1f}" y="{PT+19}" fill="{VERM}" font-size="11" font-weight="700">8/5 起：制度切换（比值 &gt;1）</text>')

# 曲线
pts = ' '.join(f'{px(i):.1f},{py(max(lo,min(hi,s2[i]/s1[i]))):.1f}' for i in range(n) if s1[i] > 0.001)
A.append(f'<polyline points="{pts}" fill="none" stroke="{PURPLE}" stroke-width="1.9" stroke-linejoin="round"/>')

# x 轴
for d in ['2026-03-10', '2026-05-01', '2026-07-01', '2026-09-10']:
    i = dates.index(d)
    A.append(f'<line x1="{px(i):.1f}" y1="{PT}" x2="{px(i):.1f}" y2="{PB}" stroke="{GRID}" stroke-width="0.7" stroke-dasharray="2 4"/>')
    A.append(f'<text x="{px(i):.1f}" y="{PB+15}" fill="{DIM}" font-size="10" text-anchor="middle">{d[5:7]}/{d[8:10]}</text>')

# 标注首次站稳
A.append(f'<circle cx="{px(i_sw):.1f}" cy="{py(s2[i_sw]/s1[i_sw]):.1f}" r="4" fill="{VERM}" stroke="#17191d" stroke-width="1.3"/>')
A.append(f'<text x="{px(i_sw)+8:.1f}" y="{py(s2[i_sw]/s1[i_sw])-10:.1f}" fill="{VERM}" font-size="10.5" font-weight="600" '
         f'paint-order="stroke" stroke="#17191d" stroke-width="3">8/5 首次站稳</text>')

# ---- Panel 2: 月度均值柱状 ----
P2T, P2B = 312, 448
import collections
mm = collections.OrderedDict()
for i, d in enumerate(dates):
    mm.setdefault(d[:7], []).append((s1[i], s2[i]))
months = list(mm.keys())
m1 = [st.mean(x[0] for x in mm[k]) for k in months]
m2 = [st.mean(x[1] for x in mm[k]) for k in months]
vmax = max(max(m1), max(m2)) * 1.18
def py2(v): return P2B - v / vmax * (P2B - P2T)
bw = (PR - PL) / len(months)
A.append(f'<text x="24" y="{P2T-12}" fill="{TXT}" font-size="12.5" font-weight="700">月度均值：3–7 月 OCT-NOV 全胜，8–9 月被 NOV-DEC 反超</text>')
A.append(f'<line x1="{PL}" y1="{P2B}" x2="{PR}" y2="{P2B}" stroke="{GRID}" stroke-width="1"/>')
for j, k in enumerate(months):
    x0 = PL + j * bw
    w = bw * 0.32
    A.append(f'<rect x="{x0+bw*0.11:.1f}" y="{py2(m1[j]):.1f}" width="{w:.1f}" height="{P2B-py2(m1[j]):.1f}" fill="{BLUE}" rx="1.5"/>')
    A.append(f'<rect x="{x0+bw*0.51:.1f}" y="{py2(m2[j]):.1f}" width="{w:.1f}" height="{P2B-py2(m2[j]):.1f}" fill="{ORANGE}" rx="1.5"/>')
    A.append(f'<text x="{x0+bw/2:.1f}" y="{P2B+14}" fill="{DIM}" font-size="10" text-anchor="middle">{k[5:7]}月</text>')
    # 谁赢
    win = 'O' if m1[j] > m2[j] else 'N'
    col = BLUE if m1[j] > m2[j] else VERM
    A.append(f'<text x="{x0+bw/2:.1f}" y="{min(py2(m1[j]),py2(m2[j]))-6:.1f}" fill="{col}" font-size="9.5" font-weight="700" text-anchor="middle">{win}</text>')

# 图例
A.append(f'<rect x="{PL+6}" y="{P2T+4}" width="150" height="34" rx="5" fill="{PANEL}" opacity="0.9"/>')
A.append(f'<rect x="{PL+16}" y="{P2T+12}" width="10" height="10" fill="{BLUE}" rx="1.5"/>')
A.append(f'<text x="{PL+31}" y="{P2T+21}" fill="{TXT}" font-size="10">OCT-NOV</text>')
A.append(f'<rect x="{PL+86}" y="{P2T+12}" width="10" height="10" fill="{ORANGE}" rx="1.5"/>')
A.append(f'<text x="{PL+101}" y="{P2T+21}" fill="{TXT}" font-size="10">NOV-DEC</text>')

# ---- Panel 3: 结论 ----
P3T = 486
A.append(f'<rect x="24" y="{P3T}" width="632" height="118" rx="8" fill="{PANEL}"/>')
A.append(f'<text x="40" y="{P3T+23}" fill="{TXT}" font-size="12.5" font-weight="700">你说得对：「前端更陡」是常态 —— 但它这次真的被打破了</text>')
rows = [
    ('常态', BLUE, '128 日中 92 日（71.9%）OCT-NOV 更陡；均值 1.731 vs 1.491（比值 0.86）。'),
    ('常态成因', DIM, '近月合约最贴近现货，交割/移仓与现货紧张集中在前端 → M1-M2 天然占优。'),
    ('这次例外', VERM, '8/5 起比值首次「连续 5 日站稳 1.0」；8/5–9/10 有 96.2% 的交易日 NOV-DEC 反而更陡。'),
    ('怎么判读', GREEN, '不是 NOV 单腿变强（9/3→9/10 三腿涨幅几乎相同：OCT/NOV +5.99%、DEC +5.50%），'),
    ('', DIM, '而是定价重心从 M1-M2 搬到 M2-M3 = 挤压点后移的结构信号。'),
]
yy = P3T + 42
for tag, col, txt in rows:
    if tag:
        A.append(f'<text x="40" y="{yy}" fill="{col}" font-size="10.5" font-weight="700">{tag}</text>')
    A.append(f'<text x="104" y="{yy}" fill="{DIM}" font-size="10.3">{txt}</text>')
    yy += 15

A.append('<text x="24" y="620" fill="#6b7076" font-size="9.5">数据：data/cl_contracts/daily/US.CL2610|2611|2612.csv（2026-03-10 起 128 交易日）</text>')
A.append('</svg>')

open('Temp/near_month_premium.svg', 'w', encoding='utf-8').write('\n'.join(A))
print('OK')
