import csv, json, sys, statistics as st

sys.stdout.reconfigure(encoding='utf-8')
codes = ['CL2610', 'CL2611', 'CL2612', 'CL2701', 'CL2702', 'CL2703']
D = {c: list(csv.DictReader(open(f'data/cl_contracts/daily/US.{c}.csv', encoding='utf-8'))) for c in codes}
dates = [r['date'] for r in D['CL2610']]
cl = {c: [float(r['close']) for r in D[c]] for c in codes}
N = len(dates)
S = [cl['CL2611'][i] - cl['CL2701'][i] for i in range(N)]
cur = S[-1]
mu = st.mean(S)
sd = st.stdev([S[i] - S[i - 1] for i in range(1, N)])
print(f'NOV-JAN 现价 {cur:.2f}  均值 {mu:.2f}  日σ {sd:.3f}  1σ={cur+sd:.2f}  2σ={cur+2*sd:.2f}')

# ---- 4h normalized momentum ----
h = json.load(open('results/futu_spread_4h_6legs_raw.json', encoding='utf-8'))['legs']
import datetime as dt
tk = [x['time_key'] for x in h['US.CL2610']]
def T(i): return dt.datetime.fromtimestamp(tk[i] / 1000 + 8 * 3600, dt.UTC).strftime('%m-%d %H:%M')
i903 = next(i for i in range(len(tk)) if T(i).startswith('09-03'))
hc = {k: [x['close'] for x in h[k]] for k in h}
CB = [('US.CL2611', 'US.CL2701', 'NOV-JAN', 2), ('US.CL2610', 'US.CL2611', 'OCT-NOV', 1), ('US.CL2610', 'US.CL2612', 'OCT-DEC', 2),
      ('US.CL2611', 'US.CL2612', 'NOV-DEC', 1), ('US.CL2610', 'US.CL2701', 'OCT-JAN', 3), ('US.CL2611', 'US.CL2702', 'NOV-FEB', 3),
      ('US.CL2702', 'US.CL2703', 'FEB-MAR', 1), ('US.CL2701', 'US.CL2703', 'JAN-MAR', 2), ('US.CL2612', 'US.CL2703', 'DEC-MAR', 3)]
mom = []
for a, b, nm, mo in CB:
    s = [hc[a][i] - hc[b][i] for i in range(len(tk))]
    mom.append((nm, (s[-1] - s[i903]) / mo, mo))
mom.sort(key=lambda x: -x[1])
print('4h归一化动量排序:', [(m[0], round(m[1], 2)) for m in mom])

# ---- SVG ----
W, H = 680, 600
X0, X1 = 70, 508
YT, YB = 72, 322
VLO, VHI = 0.0, 8.6
def px(i): return X0 + i / (N - 1) * (X1 - X0)
def py(v): return YB - (v - VLO) / (VHI - VLO) * (YB - YT)

TXT = '#e8eaed'; MUT = '#9aa0a6'; DIM = '#6b7076'; GRID = '#2a2d33'
RED = '#D55E00'; BLU = '#0072B2'; SKY = '#56B4E9'; GRY = '#8a9099'

A = []
A.append('<svg viewBox="0 0 680 600" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,\'Segoe UI\',\'Microsoft YaHei\',sans-serif" role="img">')
A.append('<title>NOV-JAN 价差轨迹与空头盈亏区间</title>')
A.append('<desc>上：NOV-JAN 128 日走势、现价、均值与波动边界。下：自 09-03 起 4 小时归一化动量排序。</desc>')
A.append('<rect width="680" height="600" fill="#17191d" rx="10"/>')
A.append(f'<text x="26" y="30" fill="{TXT}" font-size="14.5" font-weight="500">2611-2701（NOV-JAN）空头仓位：你在曲线的什么位置</text>')
A.append(f'<text x="26" y="47" fill="{MUT}" font-size="11.5">上：128 日日线收盘 ｜ 下：自 09-03 起 4 小时动量（已按跨月数归一，$/月）</text>')

# loss / profit bands
ycur, y2s, ymu = py(cur), py(cur + 2 * sd), py(mu)
A.append(f'<rect x="{X0}" y="{y2s:.1f}" width="{X1-X0}" height="{ycur-y2s:.1f}" fill="{RED}" opacity="0.13"/>')
A.append(f'<rect x="{X0}" y="{ycur:.1f}" width="{X1-X0}" height="{ymu-ycur:.1f}" fill="{BLU}" opacity="0.13"/>')

for v in [0, 2, 4, 6, 8]:
    y = py(v)
    A.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.7"/>')
    A.append(f'<text x="{X0-8}" y="{y+3.5:.1f}" fill="{DIM}" font-size="10.5" text-anchor="end">{v}</text>')

for v, col, dash, lab in [(cur + 2 * sd, RED, '4 3', f'+2σ {cur+2*sd:.2f}'), (cur + sd, RED, '3 3', ''),
                          (mu, GRY, '5 4', f'均值 {mu:.2f}'), (6.65, SKY, '6 3', '突破位 6.65')]:
    y = py(v)
    A.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{col}" stroke-width="1" stroke-dasharray="{dash}"/>')
    if lab:
        A.append(f'<text x="{X1+6:.1f}" y="{y+3.5:.1f}" fill="{col}" font-size="10.5">{lab}</text>')

pts = ' '.join(f'{px(i):.1f},{py(S[i]):.1f}' for i in range(N))
A.append(f'<polyline points="{pts}" fill="none" stroke="{TXT}" stroke-width="1.9" stroke-linejoin="round" stroke-linecap="round"/>')
A.append(f'<circle cx="{px(N-1):.1f}" cy="{ycur:.1f}" r="4" fill="{TXT}"/>')
A.append(f'<text x="{px(N-1)-6:.1f}" y="{ycur+18:.1f}" fill="{TXT}" font-size="12" font-weight="500" text-anchor="end">现价 {cur:.2f} · 128日新高</text>')

A.append(f'<text x="{X0+8}" y="{(ycur+y2s)/2+4:.1f}" fill="{RED}" font-size="11.5" font-weight="500">若继续扩大 → 你亏（1σ 处 −${sd*1000:.0f}/手）</text>')
A.append(f'<text x="{X0+8}" y="{(ycur+ymu)/2+4:.1f}" fill="{SKY}" font-size="11.5" font-weight="500">若回归均值 → 你赚 +${(cur-mu)*1000:.0f}/手</text>')

for i in range(0, N, 20):
    A.append(f'<text x="{px(i):.1f}" y="{YB+16:.1f}" fill="{DIM}" font-size="10" text-anchor="middle">{dates[i][5:]}</text>')

# ---- bottom: 4h momentum bars ----
A.append(f'<text x="26" y="372" fill="{MUT}" font-size="12" font-weight="500">自 09-03 起的 4 小时动量（归一化 $/月）— NOV-JAN 强于所有后端组合，但弱于前端</text>')
bx0, bx1 = 190, 470
mx = 0.70
for k, (nm, v, mo) in enumerate(mom):
    y = 392 + k * 19
    w = max(1, v / mx * (bx1 - bx0))
    ismine = (nm == 'NOV-JAN')
    col = SKY if ismine else '#5a6068'
    A.append(f'<text x="{bx0-8}" y="{y+9:.1f}" fill="{SKY if ismine else MUT}" font-size="11" font-weight="500" text-anchor="end">{nm}{"  ← 你的" if ismine else ""}</text>')
    A.append(f'<rect x="{bx0}" y="{y:.1f}" width="{w:.1f}" height="11" fill="{col}" rx="1.5"/>')
    A.append(f'<text x="{bx0+w+6:.1f}" y="{y+9:.1f}" fill="{SKY if ismine else DIM}" font-size="10.5">{v:.2f}</text>')

A.append(f'<text x="26" y="584" fill="{DIM}" font-size="10.5">数据：CME WTI 六腿日线+4小时，富途行情 ｜ 日线至 09-10 收盘，4h 至 09-10 10:00 ｜ 1 手 = 1000 桶，价差变动 1.00 ≈ $1000/手</text>')
A.append('</svg>')

open('Temp/position.svg', 'w', encoding='utf-8').write('\n'.join(A))
print('svg bytes', len('\n'.join(A)))
