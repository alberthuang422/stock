# -*- coding: utf-8 -*-
"""EIA 库存 vs HO 价格/月差 定量检验"""
import pandas as pd, numpy as np, json

T = r'C:/Users/Administrator/Desktop/stock/Temp'
w = pd.read_csv(T + '/eia_wpsr_weekly.csv', parse_dates=['date']).set_index('date')
ho = pd.read_csv(T + '/ho_price_spread_merged.csv', parse_dates=['time']).rename(columns={'time': 'date'})

print('=' * 78)
print('A. 库存季节性分位（对同一日历周历史值排序，1983 起）')
print('=' * 78)
w['woy'] = w.index.isocalendar().week.astype(int)
BASE0, BASE1 = 2015, 2025   # 历史基线窗口
def pctile(series):
    s = series.copy()
    s = s[(s.index.year >= BASE0) & (s.index.year <= BASE1)]
    cur = series.dropna().iloc[-1]
    return (s <= cur).mean() * 100, s.mean(), s.min(), s.quantile(.05), s.quantile(.10)

for col, label in [('dist_total', '美国馏分油总库存'), ('dist_ulsd', '美国 ULSD(0-15ppm)'),
                   ('dist_ls500', '美国低硫(15-500ppm=取暖油)'), ('dist_p1', 'PADD1 东海岸馏分油'),
                   ('dist_p1a', 'PADD1A 新英格兰'), ('dist_p1b', 'PADD1B 中区(含NY港)'),
                   ('dist_p1c', 'PADD1C 下大西洋'), ('dist_p2', 'PADD2 中西部'),
                   ('dist_p3', 'PADD3 墨西哥湾'), ('dist_p5', 'PADD5 西海岸'),
                   ('gasoline', '汽油总库存'), ('crude_exspr', '商业原油(不含SPR)')]:
    s = w[col].dropna()
    pk, mn, mnv, q5, q10 = pctile(s)
    print('%-24s 当前 %9.0f | 分位 %5.1f%% | 同周均值 %9.0f | 同周最低 %9.0f | 5%%分位 %9.0f'
          % (label, s.iloc[-1], pk, mn, mnv, q5))
print('  分位基准：同日历周 %d-%d；当前值取 %s' % (BASE0, BASE1, w.dropna(subset=['dist_total']).index[-1].date()))
print()

print('=' * 78)
print('B. 关键节点对照（库存 vs 价格/月差）')
print('=' * 78)
key = ['2022-03-04', '2022-04-22', '2022-04-29', '2022-05-06', '2022-06-03', '2022-09-02',
       '2026-02-27', '2026-03-06', '2026-03-13', '2026-03-20', '2026-03-27', '2026-04-03',
       '2026-04-24', '2026-05-22', '2026-06-26', '2026-07-24', '2026-08-14', '2026-08-21']
sub = w.loc[[d for d in key if d in w.index.astype(str)], ['dist_total', 'dist_p1', 'dist_p1b', 'dist_ulsd', 'dist_supplied', 'crude_exspr', 'gasoline']].copy()
# 贴最近的价格/月差
def nearest(dt):
    i = ho.date.searchsorted(pd.Timestamp(dt), side='right') - 1
    return ho.iloc[i] if i >= 0 else None
rows = []
for d in sub.index:
    r = nearest(d)
    rows.append([str(d.date()), sub.loc[d, 'dist_total'], sub.loc[d, 'dist_p1'], sub.loc[d, 'dist_p1b'],
                 sub.loc[d, 'dist_supplied'],
                 round(sub.loc[d, 'dist_total'] / sub.loc[d, 'dist_supplied'], 1) if sub.loc[d, 'dist_supplied'] else np.nan,
                 round(r.ho1, 4), round(r.spread, 4), str(r.date.date())])
t = pd.DataFrame(rows, columns=['EIA周', '馏分油库存', 'PADD1', 'PADD1B', '需求kb/d', '天数库存', 'HO近月', '月差', '价差对应日'])
print(t.to_string(index=False))
print()

print('=' * 78)
print('C. 全样本回归：月差 ~ 库存变量（2016-2026 周度交集）')
print('=' * 78)
m = ho.merge(w.reset_index(), on='date', how='inner')
m = m[m.date >= '2016-01-01']
m['dos'] = m.dist_total / m.dist_supplied                       # 天数库存
m['dos_p1'] = m.dist_p1 / m.dist_supplied
# 季节性偏离：对每个日历周的历史均值取偏离
for c, n in [('dist_total', 'dist_dev'), ('dist_p1', 'p1_dev'), ('dos', 'dos_dev')]:
    base = m.groupby(m.date.dt.isocalendar().week)[c].transform('mean')
    m[n] = (m[c] - base) / base * 100
m['d_dist'] = m.dist_total.diff()
m['d_p1'] = m.dist_p1.diff()

def reg(x, y):
    s = m[[x, y]].dropna()
    b, a = np.polyfit(s[x], s[y], 1)
    r = s[x].corr(s[y])
    return len(s), r, b, a
print('%-34s %6s %8s %11s' % ('关系', 'n', 'corr', '斜率'))
for x, y, lab in [('dist_total', 'spread', '月差 ~ 美国馏分油库存'),
                  ('dist_p1', 'spread', '月差 ~ PADD1 库存'),
                  ('dos', 'spread', '月差 ~ 天数库存'),
                  ('dist_dev', 'spread', '月差 ~ 库存季节偏离(%)'),
                  ('p1_dev', 'spread', '月差 ~ PADD1季节偏离(%)'),
                  ('d_dist', 'spread', '月差 ~ 库存周变化'),
                  ('d_p1', 'spread', '月差 ~ PADD1周变化'),
                  ('dist_total', 'ho1', '价格 ~ 美国馏分油库存'),
                  ('p1_dev', 'ho1', '价格 ~ PADD1季节偏离(%)')]:
    n, r, b, a = reg(x, y)
    print('%-34s %6d %8.3f %11.5f' % (lab, n, r, b))
print()

print('=' * 78)
print('D. 2022 与 2026 逐周库存对照（同日历周对齐）')
print('=' * 78)
for col in ['dist_total', 'dist_p1', 'dist_ulsd']:
    a = w[(w.index.year == 2022)][col].groupby(w[(w.index.year == 2022)].index.month).mean()
    b = w[(w.index.year == 2026)][col].groupby(w[(w.index.year == 2026)].index.month).mean()
    print('%s:' % col)
    print('  2022 月均 [' + ', '.join('%7.0f' % v for v in a) + ']')
    print('  2026 月均 [' + ', '.join('%7.0f' % v for v in b) + ']')
print()

print('=' * 78)
print('E. 2026 蒸馏油库存在 2015-2025 同周的排位（百分位越低越紧）')
print('=' * 78)
w['pct_us'] = np.nan
for wk in sorted(w.woy.dropna().unique()):
    idx = w.index[(w.woy == wk) & (w.index.year >= 2015)]
    if len(idx) < 5:
        continue
    v = w.loc[idx, 'dist_total']
    w.loc[idx, 'pct_us'] = v.rank(pct=True) * 100
y26 = w.loc['2026-01-01':, ['dist_total', 'pct_us', 'dist_p1']]
print(y26.round(1).to_string())
