# -*- coding: utf-8 -*-
"""82-附: 小麦库存 vs 价格 实证"""
import csv, math

PRICE = '/Users/alberthuang/Desktop/股票分析/data/wheat_zw_1D.csv'
STOCK = '/Users/alberthuang/Desktop/股票分析/results/wheat_stocks_history.csv'

# ---- 价格: 日线 -> 市场年度均价 (当年7月~次年6月) ----
prices = {}
with open(PRICE) as f:
    for r in csv.DictReader(f):
        try:
            c = float(r['close'])
        except:
            continue
        if c > 0:
            prices[r['date']] = c

def my_avg(my):
    v = []
    for d, c in prices.items():
        y, m = int(d[:4]), int(d[5:7])
        yy = y if m >= 7 else y - 1
        if yy == my:
            v.append(c)
    return sum(v) / len(v) if v else None

stocks = {}
with open(STOCK) as f:
    for r in csv.DictReader(f):
        stocks[int(r['year'])] = (float(r['world_su_ratio']), float(r['trade5_end']) / 1000)

data = []
for y in range(2015, 2027):
    p = my_avg(y)
    if p and y in stocks:
        data.append((y, stocks[y][0], stocks[y][1], p / 100))

print('市场年度 | 全球库消比% | 五国缓冲(Mt) | CBOT年均价($)')
for d in data:
    print(f'{d[0]}/{(d[0]+1)%100:02d} | {d[1]:5.1f} | {d[2]:5.1f} | {d[3]:6.2f}')

def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx = sum((a - mx) ** 2 for a in x)
    vy = sum((b - my) ** 2 for b in y)
    r = cov / math.sqrt(vx * vy)
    t = r * math.sqrt(n - 2) / math.sqrt(1 - r * r)
    from math import erf
    p = 1 - erf(abs(t) / math.sqrt(2))  # 双侧
    return r, t, p

print()
for label, idx in [('全球库消比', 1), ('五国缓冲Mt', 2)]:
    xs = [d[idx] for d in data]
    ys = [d[3] for d in data]
    r, t, p = pearson(xs, ys)
    print(f'{label} vs 年均价: n={len(xs)} r={r:.3f} t={t:.2f} p={p:.4f}')

# 差分: Δ五国缓冲 vs Δ价格
dy = [data[i][3] - data[i-1][3] for i in range(1, len(data))]
dx = [data[i][2] - data[i-1][2] for i in range(1, len(data))]
r, t, p = pearson(dx, dy)
print(f'Δ五国缓冲 vs Δ价格: n={len(dy)} r={r:.3f} t={t:.2f} p={p:.4f}')

# 分档对照
print()
lo = [d for d in data if d[2] < 45]
hi = [d for d in data if d[2] > 55]
mid = [d for d in data if 45 <= d[2] <= 55]
def avg(x): return sum(x) / len(x) if x else 0
print(f'低缓冲档(<45Mt): n={len(lo)} 均价=${avg([d[3] for d in lo]):.2f}  年份={[d[0] for d in lo]}')
print(f'中缓冲档(45-55): n={len(mid)} 均价=${avg([d[3] for d in mid]):.2f}  年份={[d[0] for d in mid]}')
print(f'高缓冲档(>55Mt): n={len(hi)} 均价=${avg([d[3] for d in hi]):.2f}  年份={[d[0] for d in hi]}')