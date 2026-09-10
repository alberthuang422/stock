# -*- coding: utf-8 -*-
"""83 号报告：HO 月差 × EIA 库存 图表数据生成"""
import pandas as pd, numpy as np, json

T = r'C:/Users/Administrator/Desktop/stock/Temp'
w = pd.read_csv(T + '/eia_wpsr_weekly.csv', parse_dates=['date']).set_index('date')
ho = pd.read_csv(T + '/ho_price_spread_merged.csv', parse_dates=['time']).rename(columns={'time': 'date'})

# 由 EIA API 补最新一周 (2026-08-28)
w.loc[pd.Timestamp('2026-08-28'), 'dist_total'] = 104187
w.loc[pd.Timestamp('2026-08-28'), 'dist_p1'] = 19318
w.loc[pd.Timestamp('2026-08-28'), 'dist_ulsd'] = 94181
w = w.sort_index()

def prior5(s):
    out = pd.Series(index=s.index, dtype=float)
    for d, v in s.items():
        m = (s.index.year >= d.year - 5) & (s.index.year <= d.year - 1) & (s.index.isocalendar().week == d.isocalendar().week)
        if m.sum() >= 3:
            out[d] = (v - s[m].mean()) / s[m].mean() * 100
    return out
for c, n in [('dist_total', 'dev5_us'), ('dist_p1', 'dev5_p1'), ('dist_ulsd', 'dev5_ulsd')]:
    w[n] = prior5(w[c])
w['woy'] = w.index.isocalendar().week.astype(int)

m = ho.merge(w.reset_index(), on='date', how='inner')
m = m[m.date >= '2016-01-01'].copy()
m['dos'] = m.dist_total / m.dist_supplied
base = m.groupby(m.date.dt.isocalendar().week)['dos'].transform('mean')
m['dev_dos'] = (m.dos - base) / base * 100

def reg(x, y):
    s = m[[x, y]].dropna()
    b, a = np.polyfit(s[x], s[y], 1)
    r = s[x].corr(s[y])
    return a, b, r, r * r, len(s)

out = {}
# --- C1 散点：库存季节偏离 vs 月差 ---
s = m[['date', 'dev5_us', 'spread', 'ho1']].dropna()
def grp(d):
    return 'y2022' if d.year == 2022 else ('y2026' if d.year == 2026 else 'other')
pts = {'other': [], 'y2022': [], 'y2026': []}
for r in s.itertuples():
    pts[grp(r.date)].append([round(r.dev5_us, 2), round(r.spread, 4), r.date.strftime('%Y-%m-%d')])
a, b, r_, r2, n = reg('dev5_us', 'spread')
out['scatter'] = {'pts': pts, 'fit': {'a': round(a, 4), 'b': round(b, 5), 'r': round(r_, 3), 'r2': round(r2, 3), 'n': n}}
# 关键点
key = {}
for d in ['2022-04-29', '2022-05-27', '2026-03-20', '2026-08-28', '2026-09-10']:
    z = s[s.date == d]
    if len(z):
        key[d] = [round(z.dev5_us.iloc[0], 2), round(z.spread.iloc[0], 4)]
out['key_pts'] = key

# --- C2 2026 周度时序 ---
y = w.loc['2026-01-01':, ['dist_total', 'dev5_us', 'dev5_p1', 'dist_p1']].copy()
y = y.join(ho.set_index('date')[['ho1', 'spread']], how='left')
y['ho1'] = y['ho1'].interpolate()
y['spread'] = y['spread'].interpolate()
out['tl26'] = {
    'lbl': [d.strftime('%m/%d') for d in y.index],
    'dev_us': [round(v, 1) for v in y.dev5_us],
    'dev_p1': [round(v, 1) for v in y.dev5_p1],
    'spread': [round(v, 4) for v in y.spread],
    'price': [round(v, 3) for v in y.ho1],
    'dist': [int(v) for v in y.dist_total],
    'p1': [int(v) for v in y.dist_p1],
}

# --- C3 分桶 ---
m['bucket'] = pd.cut(m.dev5_us, [-99, -25, -20, -15, -10, -5, 0, 99],
                     labels=['<-25%', '-25~-20%', '-20~-15%', '-15~-10%', '-10~-5%', '-5~0%', '>0%'])
bt = m.groupby('bucket', observed=True).agg(n=('spread', 'size'), med=('spread', 'median'))
out['buckets'] = {'lbl': list(bt.index.astype(str)), 'n': [int(v) for v in bt.n], 'med': [round(v, 4) for v in bt.med]}
cur = m[m.date == '2026-08-28']
out['buckets']['cur'] = round(float(cur.spread.iloc[0]), 4) if len(cur) else None
out['buckets']['cur_dev'] = round(float(cur.dev5_us.iloc[0]), 1) if len(cur) else None

# --- C4 库存序列 2015+ ---
h = w.loc['2015-01-01':, ['dist_total', 'dist_p1', 'dist_ulsd']].dropna(subset=['dist_total'])
out['hist'] = {
    'lbl': [d.strftime('%y/%m') for d in h.index],
    'us': [int(v) for v in h.dist_total],
    'p1': [int(v) if not np.isnan(v) else None for v in h.dist_p1],
}
out['p1_min'] = {'v': int(w.dist_p1.min()), 'd': str(w.dist_p1.idxmin().date()),
                 'v26': int(w.loc['2026-08-28', 'dist_p1'])}

# --- C5 解释力 R2 对比 ---
cmp = []
for x, lab in [('dev5_us', '库存5年偏离'), ('dev5_p1', 'PADD1 5年偏离'), ('dev_dos', '天数库存偏离')]:
    _, _, rp, r2p, _ = reg(x, 'ho1')
    _, _, rs, r2s, _ = reg(x, 'spread')
    cmp.append({'lab': lab, 'price': round(r2p, 3), 'price_r': round(rp, 3), 'spread': round(r2s, 3), 'spread_r': round(rs, 3)})
out['r2cmp'] = cmp

json.dump(out, open(T + '/ho83_data.json', 'w'), ensure_ascii=False)
print('saved. keys:', list(out.keys()))
print('散点 n:', {k: len(v) for k, v in pts.items()})
print('拟合:', out['scatter']['fit'])
print('关键点:', key)
print('桶:', out['buckets'])
print('PADD1 最低:', out['p1_min'])
print('R2:', cmp)
print('2026周数:', len(out['tl26']['lbl']))
print('hist n:', len(out['hist']['lbl']))
