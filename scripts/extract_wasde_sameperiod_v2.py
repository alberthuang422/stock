# -*- coding: utf-8 -*-
"""
WASDE "往年同期"口径提取（v2，2015-2026 全样本）
- 数据源（均为 USDA 官方"当时公布快照"，非事后修订值）:
    * 2015-09 ~ 2020-09: Temp/wasde_snapshot/z1015|z1620/oce-wasde-report-data-*.csv （官方 ZIP 打包）
    * 2021-09 ~ 2026-09: Temp/wasde_snapshot/oce-wasde-report-data-YYYY-09.csv （官方单月 CSV）
- 口径: 每年9月报告中, 对"最新市场年度"（ProjEstFlag 含 Proj）的期末库存预测
- 三硬 = US+CA+AS（有官方库存盘点）; 两软 = BR+E4（残差）; 五国 = 并集
输出: results/wasde_sameperiod_2015_2026.json
"""
import pandas as pd, json, os

ROOT = '/Users/alberthuang/Desktop/股票分析'
SNAP = os.path.join(ROOT, 'Temp/wasde_snapshot')
OUT = os.path.join(ROOT, 'results/wasde_sameperiod_2015_2026.json')

REGION = {'US': 'United States', 'CA': 'Canada', 'AS': 'Australia',
          'BR': 'Brazil', 'E4': 'European Union'}
HARD, SOFT = ['US', 'CA', 'AS'], ['BR', 'E4']
FIVE = HARD + SOFT
COM = {'wheat': 'Wheat', 'corn': 'Corn', 'soybean': 'Oilseed, Soybean'}

# ---------- 1) 载入全部快照 CSV ----------
srcs = [
    f'{SNAP}/z1015/oce-wasde-report-data-2010-04-to-2015-12.csv',
    f'{SNAP}/z1620/oce-wasde-report-data-2016-01-to-2020-12.csv',
]
for y in range(2021, 2027):
    srcs.append(f'{SNAP}/oce-wasde-report-data-{y}-09.csv')

frames = []
for p in srcs:
    if not os.path.exists(p):
        print('MISS', p); continue
    frames.append(pd.read_csv(p, dtype=str, low_memory=False))
df = pd.concat(frames, ignore_index=True)
print('total rows:', len(df))

# ---------- 2) 筛选 ----------
base = df[(df['Attribute'] == 'Ending Stocks')
          & (df['Unit'] == 'Million Metric Tons')
          & (df['Region'].isin(REGION.values()))
          & (df['Commodity'].isin(COM.values()))].copy()
base['is_proj'] = base['ProjEstFlag'].fillna('').str.contains('Proj')

print('\n=== 校验：每年9月 Proj 年度行（确认每品种每年唯一） ===')
series = {c: {'years': [], 'hard': [], 'soft': [], 'five': [], 'my': []} for c in COM}
detail = {}
for y in range(2015, 2027):
    rd = f'September {y}'
    d = base[(base['ReportDate'] == rd) & base['is_proj']]
    detail[y] = {}
    for com, cname in COM.items():
        dd = d[d['Commodity'] == cname]
        mys = sorted(set(dd['MarketYear'].dropna()))
        vals = {}
        for cc, reg in REGION.items():
            r = dd[dd['Region'] == reg]
            if len(r):
                vals[cc] = float(r.iloc[-1]['Value'].replace(',', ''))
                my = r.iloc[-1]['MarketYear']
        hard = sum(vals.get(c_, 0) for c_ in HARD)
        soft = sum(vals.get(c_, 0) for c_ in SOFT)
        detail[y][com] = {'my': mys, 'vals': vals, 'hard': round(hard, 2),
                          'soft': round(soft, 2), 'five': round(hard + soft, 2)}
        s = series[com]
        s['years'].append(str(y))
        s['my'].append(mys[0] if len(mys) == 1 else mys)
        s['hard'].append(round(hard, 2))
        s['soft'].append(round(soft, 2))
        s['five'].append(round(hard + soft, 2))
    if y <= 2027:
        print(f'{y}: ' + ' | '.join(
            f'{com}:MY={detail[y][com]["my"]}(n={len(detail[y][com]["vals"])})' for com in COM))

print('\n=== 往年同期口径（2015-2026）三口径序列 ===')
for com in COM:
    s = series[com]
    print(f'\n{com}')
    print('  years:', s['years'])
    print('  MY   :', s['my'])
    print('  三硬 :', s['hard'])
    print('  两软 :', s['soft'])
    print('  五国 :', s['five'])

json.dump({'series': series, 'detail': {str(k): v for k, v in detail.items()}},
          open(OUT, 'w'), ensure_ascii=False, indent=2)
print('\nOK ->', OUT)
