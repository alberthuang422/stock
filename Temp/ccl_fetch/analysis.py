# -*- coding: utf-8 -*-
"""CCL 技术面 + 结构分析：读本地日线，产出报告用 JSON"""
import csv, json, math

def load(fp):
    rows = []
    with open(fp, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d = r['date'].split(' ')[0]
            try:
                rows.append({'d': d, 'o': float(r['open']), 'h': float(r['high']),
                             'l': float(r['low']), 'c': float(r['close']), 'v': float(r['volume']),
                             'a': float(r['adj_close'] or r['close'])})
            except (ValueError, TypeError):
                continue
    rows.sort(key=lambda x: x['d'])
    return rows

ccl = load('data/ccl/CCL, 1D.csv')
spy = load('data/spy/SPY, 1D.csv')
print('CCL:', ccl[0]['d'], '~', ccl[-1]['d'], len(ccl))
print('SPY:', spy[0]['d'], '~', spy[-1]['d'], len(spy))

# RSI14 (Wilder)
def rsi_series(prices, n=14):
    rsi = [None]*len(prices)
    g = l = 0.0
    for i in range(1, len(prices)):
        ch = prices[i] - prices[i-1]
        if ch > 0: g = ch
        else: l = -ch
        if i < n: continue
        # rolling over last n
        gg = ll = 0.0
        for k in range(i-n+1, i+1):
            chk = prices[k]-prices[k-1]
            if chk > 0: gg += chk
            else: ll -= chk
        gg /= n; ll /= n
        rsi[i] = 100 - 100/(1 + (gg/ll if ll else 999))
    return rsi

# Wilder EMA 平滑版
def rsi_wilder(prices, n=14):
    if len(prices) <= n: return [None]*len(prices)
    gains, losses = [], []
    for i in range(1, len(prices)):
        ch = prices[i]-prices[i-1]
        gains.append(max(ch, 0)); losses.append(max(-ch, 0))
    ag = sum(gains[:n])/n; al = sum(losses[:n])/n
    rsi = [None]*n
    for i in range(n, len(prices)):
        ag = (ag*(n-1)+gains[i-1])/n
        al = (al*(n-1)+losses[i-1])/n
        rsi.append(100-100/(1+(ag/al if al else 999)))
    return rsi

px = [x['a'] for x in ccl]
rsi = rsi_wilder(px)

def ema(vals, n):
    k = 2/(n+1)
    out = []
    em = None
    for v in vals:
        em = v if em is None else v*k + em*(1-k)
        out.append(em)
    return out

e20 = ema(px, 20); e50 = ema(px, 50)
# SMA200
def sma(vals, n):
    out = []
    for i in range(len(vals)):
        if i < n-1: out.append(None)
        else: out.append(sum(vals[i-n+1:i+1])/n)
    return out
s200 = sma(px, 200)

N = len(ccl)
last = ccl[-1]
i_last = N-1
print('\n=== 最新日 (08-27) ===')
print('close:', last['c'], 'adj:', last['a'], 'vol:', last['v'])
print('RSI14:', round(rsi[-1],2))
for name, arr, n in [('EMA20', e20, 20), ('EMA50', e50, 50), ('SMA200', s200, 200)]:
    v = arr[-1]
    if v:
        diff = (last['a']/v - 1)*100
        print(f'{name}: {v:.2f}  diff {diff:+.2f}%')

# 52周高低
w52 = ccl[-252:]
hi52 = max(x['h'] for x in w52); lo52 = min(x['l'] for x in w52)
print(f'52周高:{hi52:.2f} ({[x["d"] for x in w52 if x["h"]==hi52][0]})  52周低:{lo52:.2f} ({[x["d"] for x in w52 if x["l"]==lo52][0]})')
print(f'距52周高回撤: {(last["a"]/hi52-1)*100:.1f}%  距52周低: {(last["a"]/lo52-1)*100:+.1f}%')

# YTD
ytd0 = px[0]
# 找2025-12-31
idx_ytd = next((i for i,x in enumerate(ccl) if x['d'] >= '2025-12-31'), 0)
ytd_base = ccl[idx_ytd-1]['a'] if idx_ytd > 0 else ccl[0]['a']
# 找2026-01-02第一个交易
idx_2026 = next(i for i,x in enumerate(ccl) if x['d'] >= '2026-01-01')
base2026 = ccl[idx_2026-1]['a']
print(f'2026 YTD(基准{base2026:.2f}): {(last["a"]/base2026-1)*100:+.1f}%')
print(f'1Y收益: {(last["a"]/ccl[-253]["a"]-1)*100:+.1f}%')
print(f'3Y收益: {(last["a"]/ccl[-757]["a"]-1)*100:+.1f}%')

# 60日/250日回撤
def drawdown(vals, lookback):
    dd = []
    for i in range(len(vals)):
        lo = min(vals[max(0,i-lookback+1):i+1])
        hi = max(vals[max(0,i-lookback+1):i+1])
        dd.append((vals[i]/hi-1)*100)
    return dd
dd60 = drawdown(px, 60); dd250 = drawdown(px, 250)
print(f'dd60: {dd60[-1]:.1f}%  dd250: {dd250[-1]:.1f}%')

# 月度序列（近 5 年 + 全史月度）
def monthly(rows):
    bym = {}
    for x in rows:
        key = x['d'][:7]
        bym.setdefault(key, []).append(x['a'])
    return [(k, v[-1]) for k, v in sorted(bym.items())]
months_full = monthly(ccl)
print('月度数:', len(months_full), months_full[0], months_full[-1])

# 阶段收益
stages = {'疫情前(2000-2019)': ('2000-01-01','2019-12-31'),
          '疫情期(2020-2022)': ('2020-01-01','2022-12-31'),
          '复苏牛市(2023起)': ('2023-01-01','2026-12-31')}
ret = {}
for name,(s,e) in stages.items():
    idxs = [i for i,x in enumerate(ccl) if s <= x['d'] <= e]
    if idxs:
        i0, i1 = idxs[0], idxs[-1]
        ret[name] = (ccl[i1]['a']/ccl[i0]['a']-1)*100
print('阶段收益:', ret)

# 年度收益表（近10年+关键年）
years = ['2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026YTD']
yret = {}
for y in years[:-1]:
    idxs = [i for i,x in enumerate(ccl) if x['d'].startswith(y)]
    if idxs:
        i0, i1 = idxs[0], idxs[-1]
        yret[y] = (ccl[i1]['a']/ccl[i0-1]['a']-1)*100 if i0>0 else 0
idx26 = [i for i,x in enumerate(ccl) if x['d'].startswith('2026')]
yret['2026YTD'] = (ccl[idx26[-1]]['a']/ccl[idx26[0]-1]['a']-1)*100
print('年度收益:', yret)

# 图表数据：近 500 日价格+RSI+均线
N2 = 500
chart = []
for i in range(N-N2, N):
    chart.append({'d': ccl[i]['d'], 'px': round(ccl[i]['a'],2),
                  'rsi': (None if rsi[i] is None else round(rsi[i],1)),
                  'e20': (None if e20[i] is None else round(e20[i],2)),
                  'e50': (None if e50[i] is None else round(e50[i],2)),
                  's200': (None if s200[i] is None else round(s200[i],2))})

out = {
  'asof_local': ccl[-1]['d'],
  'last_close_raw': last['c'],
  'last_close_adj': last['a'],
  'rsi14': round(rsi[-1],1),
  'ema20': round(e20[-1],2), 'e20diff': round((last['a']/e20[-1]-1)*100,1),
  'ema50': round(e50[-1],2), 'e50diff': round((last['a']/e50[-1]-1)*100,1),
  'sma200': round(s200[-1],2), 's200diff': round((last['a']/s200[-1]-1)*100,1),
  'hi52': round(hi52,2), 'lo52': round(lo52,2), 'dd52': round((last['a']/hi52-1)*100,1),
  'ytd': round((last['a']/base2026-1)*100,1),
  'y1': round((last['a']/ccl[-253]['a']-1)*100,1),
  'y3': round((last['a']/ccl[-757]['a']-1)*100,1),
  'dd60': round(dd60[-1],1), 'dd250': round(dd250[-1],1),
  'stage_ret': ret, 'year_ret': yret,
  'months_full': months_full, 'chart500': chart,
  'vol_last': last['v'],
}
with open('Temp/ccl_fetch/tech.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
print('\nsaved Temp/ccl_fetch/tech.json')
