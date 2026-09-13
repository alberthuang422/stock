# -*- coding: utf-8 -*-
"""
82 小麦库存历史分析 (2000-2026)
数据源: USDA FAS PSD 本地缓存 Temp/psd/wheat_{year}.json (2000..2026)
口径:
  - 每个 (country, attribute, marketYear) 取 month 最大(=最晚修订)的版本
  - 全球 = 全部国家/区域代码求和(PSD 以 E4 代表欧盟整体, 无成员国重复)
  - 世界总消费 = attributeId 125 Domestic Consumption
  - 可贸易五国 = US + CA + E4 + AS(澳洲) + BR(巴西)  (与 68 报告口径一致, 不含俄乌/中国)
输出: results/wheat_stocks_history.csv
"""
import json, csv, os, sys

PSD_DIR = '/Users/alberthuang/Desktop/股票分析/Temp/psd'
OUT_CSV = '/Users/alberthuang/Desktop/股票分析/results/wheat_stocks_history.csv'

ATTR = {
    'beg_stocks': 20, 'production': 28, 'imports': 57, 'total_supply': 86,
    'exports': 88, 'dom_cons': 125, 'feed_cons': 130, 'fsi_cons': 192,
    'end_stocks': 176,
}
TRADE5 = ['US', 'CA', 'E4', 'AS', 'BR']  # 美/加/欧盟/澳/巴西
KEY = ['RS', 'UP']  # 俄乌
CN = ['CH']  # 中国

years = list(range(2000, 2027))

def load(year):
    with open(os.path.join(PSD_DIR, f'wheat_{year}.json')) as f:
        raw = json.load(f)
    # 每个 (cc, attr) 取 month 最大的版本
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

def agg(data, countries):
    wp = {a: 0.0 for a in ATTR.values()}
    for cc in countries:
        d = data.get(cc, {})
        for a in wp:
            wp[a] += d.get(a, 0.0)
    return wp

rows = []
for y in years:
    data = load(y)
    world = agg(data, list(data.keys()))
    t5 = agg(data, TRADE5)
    ru = agg(data, KEY)
    cn = agg(data, CN)
    end_w = world[ATTR['end_stocks']]
    cons_w = world[ATTR['dom_cons']]
    rows.append({
        'year': y,
        'world_prod': world[ATTR['production']],
        'world_cons': cons_w,
        'world_end': end_w,
        'world_su_ratio': round(end_w / cons_w * 100, 2) if cons_w else None,
        'world_beg': world[ATTR['beg_stocks']],
        'world_export': world[ATTR['exports']],
        'world_feed': world[ATTR['feed_cons']],
        'world_fsi': world[ATTR['fsi_cons']],
        'trade5_end': t5[ATTR['end_stocks']],
        'trade5_prod': t5[ATTR['production']],
        'trade5_cons': t5[ATTR['dom_cons']],
        'trade5_export': t5[ATTR['exports']],
        'ru_end': ru[ATTR['end_stocks']],
        'ru_prod': ru[ATTR['production']],
        'ru_export': ru[ATTR['exports']],
        'cn_end': cn[ATTR['end_stocks']],
        'cn_prod': cn[ATTR['production']],
    })

os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
with open(OUT_CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f'OK -> {OUT_CSV} ({len(rows)} rows)')
for r in rows:
    print(r['year'], 'prod=%8.1f' % r['world_prod'], 'cons=%8.1f' % r['world_cons'],
          'end=%8.1f' % r['world_end'], 'S/U=%6.2f%%' % (r['world_su_ratio'] or 0),
          'T5end=%7.1f' % r['trade5_end'], 'RUend=%7.1f' % r['ru_end'], 'CNend=%7.1f' % r['cn_end'])