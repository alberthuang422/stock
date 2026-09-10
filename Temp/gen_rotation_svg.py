import csv, sys

sys.stdout.reconfigure(encoding='utf-8')
SL = ['CL2610', 'CL2611', 'CL2612', 'CL2701', 'CL2702', 'CL2703']
D = {s: list(csv.DictReader(open(f'data/cl_contracts/daily/US.{s}.csv', encoding='utf-8'))) for s in SL}
dd = [r['date'] for r in D['CL2610']]
cl = {s: [float(r['close']) for r in D[s]] for s in SL}
oi = {s: [float(r['open_interest'] or 0) for r in D[s]] for s in SL}

b = dd.index('2026-08-26')
idx = list(range(b - 2, len(dd)))
N = len(idx)
dates = [dd[i][5:] for i in idx]

def ridx(num, den):
    return [cl[num][i] / cl[den][i] / (cl[num][b] / cl[den][b]) * 100 for i in idx]

ro = ridx('CL2611', 'CL2610')   # vs OCT
rd = ridx('CL2611', 'CL2612')   # vs DEC
rj = ridx('CL2611', 'CL2701')   # vs JAN
oi_o = [oi['CL2610'][i] / 1000 for i in idx]
oi_n = [oi['CL2611'][i] / 1000 for i in idx]
oi_d = [oi['CL2612'][i] / 1000 for i in idx]

W, H = 680, 620
X0, X1 = 74, 520
def px(i): return X0 + i / (N - 1) * (X1 - X0)

P1T, P1B = 84, 278
V1LO, V1HI = 97.5, 104.8
def py1(v): return P1B - (v - V1LO) / (V1HI - V1LO) * (P1B - P1T)

P2T, P2B = 318, 548
V2LO, V2HI = 160, 275
def py2(v): return P2B - (v - V2LO) / (V2HI - V2LO) * (P2B - P2T)

TXT = '#e8eaed'; MUT = '#9aa0a6'; DIM = '#6b7076'; GRID = '#2a2d33'
C_NOV = '#56B4E9'; C_DEC = '#E69F00'; C_OCT = '#D55E00'

A = []
A.append('<svg viewBox="0 0 680 620" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,\'Segoe UI\',\'Microsoft YaHei\',sans-serif" role="img">')
A.append('<title>WTI 11月合约相对强度与持仓量轮动</title>')
A.append('<desc>上图：NOV 相对 OCT/DEC/JAN 的相对强度指数（08-26=100）；下图：OCT/NOV/DEC 三腿持仓量与主力切换。</desc>')
A.append('<rect width="680" height="620" fill="#17191d" rx="10"/>')

A.append(f'<text x="26" y="30" fill="{TXT}" font-size="14.5" font-weight="500">NOV（11月合约）是"变强"了吗 — 相对强度与持仓量轮动</text>')
A.append(f'<text x="26" y="49" fill="{MUT}" font-size="11.5">指数编制 08-26 = 100 ｜ 线上行 = NOV 相对该腿走强 ｜ 日线收盘口径</text>')

# ---- panel1 header + legend ----
A.append(f'<text x="26" y="72" fill="{MUT}" font-size="12" font-weight="500">① NOV 相对强度指数</text>')
lx = 292
for lb, col, mk in [('vs JAN', C_NOV, 'c'), ('vs DEC', C_DEC, 's'), ('vs OCT', C_OCT, 't')]:
    if mk == 'c':
        A.append(f'<circle cx="{lx}" cy="68" r="3.4" fill="{col}"/>')
    elif mk == 's':
        A.append(f'<rect x="{lx-3}" y="64.6" width="6.8" height="6.8" fill="{col}"/>')
    else:
        A.append(f'<polygon points="{lx},64.6 {lx-3.6},71 {lx+3.6},71" fill="{col}"/>')
    A.append(f'<text x="{lx+9}" y="72" fill="{col}" font-size="11">{lb}</text>')
    lx += 78

for v in [98, 99, 100, 101, 102, 103, 104]:
    y = py1(v)
    A.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.7"/>')
    A.append(f'<text x="{X0-8}" y="{y+3.5:.1f}" fill="{DIM}" font-size="10.5" text-anchor="end">{v}</text>')
y100 = py1(100)
A.append(f'<line x1="{X0}" y1="{y100:.1f}" x2="{X1}" y2="{y100:.1f}" stroke="#8a9099" stroke-width="1" stroke-dasharray="5 4"/>')

def poly(vals, fn, color, dash, marker, ms):
    pts = ' '.join(f'{px(i):.1f},{fn(vals[i]):.1f}' for i in range(N))
    d = f' stroke-dasharray="{dash}"' if dash else ''
    A.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"{d} stroke-linejoin="round" stroke-linecap="round"/>')
    for i in range(N):
        x = px(i); y = fn(vals[i])
        if marker == 'c':
            A.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{ms}" fill="{color}"/>')
        elif marker == 's':
            A.append(f'<rect x="{x-ms:.1f}" y="{y-ms:.1f}" width="{2*ms}" height="{2*ms}" fill="{color}"/>')
        else:
            A.append(f'<polygon points="{x:.1f},{y-ms-0.5:.1f} {x-ms-0.5:.1f},{y+ms:.1f} {x+ms+0.5:.1f},{y+ms:.1f}" fill="{color}"/>')

poly(rj, py1, C_NOV, None, 'c', 2.6)
poly(rd, py1, C_DEC, '7 4', 's', 2.4)
poly(ro, py1, C_OCT, '2 3', 't', 2.8)

A.append(f'<text x="{X1+8:.1f}" y="{py1(rj[-1])+3.5:.1f}" fill="{C_NOV}" font-size="11" font-weight="500">{rj[-1]:.1f} ↑</text>')
A.append(f'<text x="{X1+8:.1f}" y="{py1(rd[-1])+3.5:.1f}" fill="{C_DEC}" font-size="11" font-weight="500">{rd[-1]:.1f} ↑</text>')
A.append(f'<text x="{X1+8:.1f}" y="{py1(ro[-1])+3.5:.1f}" fill="{C_OCT}" font-size="11" font-weight="500">{ro[-1]:.1f} ↓</text>')

# ---- panel2 ----
A.append(f'<text x="26" y="305" fill="{MUT}" font-size="12" font-weight="500">② 持仓量（千手）— 主力合约切换</text>')
lx = 292
for lb, col, mk in [('OCT', C_OCT, 't'), ('NOV', C_NOV, 'c'), ('DEC', C_DEC, 's')]:
    if mk == 'c':
        A.append(f'<circle cx="{lx}" cy="301" r="3.4" fill="{col}"/>')
    elif mk == 's':
        A.append(f'<rect x="{lx-3}" y="297.6" width="6.8" height="6.8" fill="{col}"/>')
    else:
        A.append(f'<polygon points="{lx},297.6 {lx-3.6},304 {lx+3.6},304" fill="{col}"/>')
    A.append(f'<text x="{lx+9}" y="305" fill="{col}" font-size="11">{lb}</text>')
    lx += 62

for v in [175, 200, 225, 250, 275]:
    y = py2(v)
    A.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="0.7"/>')
    A.append(f'<text x="{X0-8}" y="{y+3.5:.1f}" fill="{DIM}" font-size="10.5" text-anchor="end">{v}</text>')

poly(oi_o, py2, C_OCT, '2 3', 't', 2.6)
poly(oi_d, py2, C_DEC, '7 4', 's', 2.2)
poly(oi_n, py2, C_NOV, None, 'c', 2.6)

xc = px(N - 1)
A.append(f'<circle cx="{xc:.1f}" cy="{py2(oi_n[-1]):.1f}" r="6.5" fill="none" stroke="{C_NOV}" stroke-width="1.6"/>')
A.append(f'<text x="{xc-4:.1f}" y="{py2(oi_n[-1])-13:.1f}" fill="{C_NOV}" font-size="11" font-weight="500" text-anchor="end">09-10 反超</text>')

A.append(f'<text x="{X1+8:.1f}" y="{py2(oi_n[-1])+3.5:.1f}" fill="{C_NOV}" font-size="11" font-weight="500">NOV {oi_n[-1]:.0f}k</text>')
A.append(f'<text x="{X1+8:.1f}" y="{py2(oi_o[-1])+4:.1f}" fill="{C_OCT}" font-size="11" font-weight="500">OCT {oi_o[-1]:.0f}k</text>')
A.append(f'<text x="{X1+8:.1f}" y="{py2(oi_d[-1])+13:.1f}" fill="{C_DEC}" font-size="11" font-weight="500">DEC {oi_d[-1]:.0f}k</text>')

# ---- shared vertical markers + x axis ----
for lab in ['09-03', '09-09']:
    if lab in dates:
        i = dates.index(lab); x = px(i)
        A.append(f'<line x1="{x:.1f}" y1="{P1T}" x2="{x:.1f}" y2="{P2B}" stroke="#3a3e45" stroke-width="0.8" stroke-dasharray="3 3"/>')

for i in range(N):
    if i % 2 == 0 or i == N - 1:
        A.append(f'<text x="{px(i):.1f}" y="{P2B+18:.1f}" fill="{DIM}" font-size="10" text-anchor="middle">{dates[i]}</text>')

A.append(f'<text x="26" y="598" fill="{DIM}" font-size="10.5">数据：CME WTI 六条腿日线收盘 + 持仓量，富途行情 ｜ 截至 2026-09-10 收盘</text>')
A.append('</svg>')

open('Temp/rotation.svg', 'w', encoding='utf-8').write('\n'.join(A))
print('ok bytes =', len('\n'.join(A)))
print('panel1 end ys:', round(py1(rj[-1]),1), round(py1(rd[-1]),1), round(py1(ro[-1]),1))
print('panel2 end ys:', round(py2(oi_n[-1]),1), round(py2(oi_o[-1]),1), round(py2(oi_d[-1]),1))
