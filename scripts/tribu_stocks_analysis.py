# -*- coding: utf-8 -*-
"""
三品种(小麦/玉米/大豆) 三口径库存分析:
  三硬  = US + CA + AS (美国/加拿大/澳洲, 有官方库存盘点)
  两软  = BR + E4      (巴西/欧盟, 库存仍以残差为主)
  五国  = 三硬 + 两软  (= US+CA+AS+BR+E4, 即 82 号"可贸易缓冲"口径)
输出 each commodity 期末库存(end_stocks=176)时间序列 + 往年同期对比
"""
import json, os, csv

PSD_DIR = '/Users/alberthuang/Desktop/股票分析/Temp/psd'
OUT_DIR = '/Users/alberthuang/Desktop/股票分析/results'

ATTR_END = 176
ATTR_PROD = 28
ATTR_CONS = 125
ATTR_EXP = 88

HARD = ['US', 'CA', 'AS']      # 美/加/澳
SOFT = ['BR', 'E4']            # 巴/欧盟
FIVE = HARD + SOFT             # 可贸易五国

COMMODITIES = ['wheat', 'corn', 'soybean']
YEARS = list(range(2000, 2027))


def load(commodity, year):
    with open(os.path.join(PSD_DIR, f'{commodity}_{year}.json')) as f:
        raw = json.load(f)
    best = {}
    for r in raw:
        key = (r['countryCode'], r['attributeId'])
        m = int(r['month'])
        if key not in best or m > best[key][0]:
            best[key] = (m, r['value'])
    out = {}
    for (cc, attr), (m, v) in best.items():
        out.setdefault(cc, {})[attr] = v
    return out


def agg(data, countries, attr):
    return sum(data.get(cc, {}).get(attr, 0.0) for cc in countries)


def pct_rank(vals, v):
    """百分位(0-100, 越大越靠历史高位)"""
    n = len(vals)
    if n == 0:
        return None
    cnt_less = sum(1 for x in vals if x < v)
    cnt_eq = sum(1 for x in vals if x == v)
    return round((cnt_less + 0.5 * cnt_eq) / n * 100, 1)


all_rows = []
summary = {}  # commodity -> {口径 -> {year: end_stocks}}

for com in COMMODITIES:
    year_data = {}
    for y in YEARS:
        data = load(com, y)
        year_data[y] = {
            'hard_end': agg(data, HARD, ATTR_END),
            'soft_end': agg(data, SOFT, ATTR_END),
            'five_end': agg(data, FIVE, ATTR_END),
            'hard_prod': agg(data, HARD, ATTR_PROD),
            'soft_prod': agg(data, SOFT, ATTR_PROD),
            'five_prod': agg(data, FIVE, ATTR_PROD),
            'five_exp': agg(data, FIVE, ATTR_EXP),
            'five_cons': agg(data, FIVE, ATTR_CONS),
        }

    # 对比往年同期(2000-2025) vs 2026最新
    hist = {k: [year_data[y][k] for y in range(2000, 2026)]
            for k in ['hard_end', 'soft_end', 'five_end']}

    for grp in ['hard_end', 'soft_end', 'five_end']:
        h = hist[grp]
        v26 = year_data[2026][grp]
        v25 = year_data[2025][grp]
        mean = sum(h) / len(h)
        mn, mx = min(h), max(h)
        med = sorted(h)[len(h) // 2]
        summary.setdefault(com, {})[grp] = {
            'series': {y: round(year_data[y][grp], 2) for y in YEARS},
            'hist_mean': round(mean, 1),
            'hist_min': round(mn, 1),
            'hist_max': round(mx, 1),
            'hist_med': round(med, 1),
            'y2026': round(v26, 1),
            'y2025': round(v25, 1),
            'yoy': round(v26 - v25, 1),
            'pct_rank': pct_rank(h, v26),
        }

    # 输出 CSV
    with open(os.path.join(OUT_DIR, f'{com}_tribu_stocks.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['year', 'hard_end', 'soft_end', 'five_end',
                    'hard_prod', 'soft_prod', 'five_prod', 'five_exp', 'five_cons'])
        for y in YEARS:
            d = year_data[y]
            w.writerow([y,
                        round(d['hard_end'], 2), round(d['soft_end'], 2), round(d['five_end'], 2),
                        round(d['hard_prod'], 2), round(d['soft_prod'], 2), round(d['five_prod'], 2),
                        round(d['five_exp'], 2), round(d['five_cons'], 2)])

# 打印摘要
print('=' * 80)
for com in COMMODITIES:
    s = summary[com]
    print(f'\n### {com.upper()}')
    for grp, label in [('hard_end', '三硬(美加澳)'), ('soft_end', '两软(巴西欧盟)'), ('five_end', '可贸易五国')]:
        g = s[grp]
        print(f'  [{label}] 2026={g["y2026"]:>8.1f}  2025={g["y2025"]:>8.1f}  同比={g["yoy"]:>+7.1f}  '
              f'历史均值={g["hist_mean"]:>8.1f} 中位={g["hist_med"]:>7.1f} '
              f'区间[{g["hist_min"]:.1f},{g["hist_max"]:.1f}]  百分位={g["pct_rank"]:>5.1f}%')

print('\n' + '=' * 80)
print('JSON 已可导出, 供 build 使用')