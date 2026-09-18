# -*- coding: utf-8 -*-
"""
96 号报告数据层：白糖「各国产量」全景 2000-2026
数据源：data/sugar/psd_sugar_all.csv（USDA FAS PSD，2026-09-11 快照）
口径：千吨·原糖当量（raw value）；市场年（MY）按各国自身窗口（巴西 4-3 月 / 中国印度 10-9 月 / 泰国 12-11 月）
与 94 号报告同源同口径，本篇聚焦「产量（28）」以及「甘蔗糖（43）/ 甜菜糖（30）」的结构拆分。
"""
import csv, json, os, math
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'sugar', 'psd_sugar_all.csv')
OUT = os.path.join(ROOT, 'results', 'sugar_production.json')

YEARS = list(range(2000, 2027))
# ⚠️ PSD CSV 中的属性码为 3 位零填充字符串（'028' 而非 '28'）——键必须零填充，否则全部落空
ATTRS = {'020': 'beg_stocks', '028': 'production', '030': 'beet_prod', '043': 'cane_prod',
         '057': 'imports', '088': 'exports', '126': 'disappearance', '139': 'consumption',
         '176': 'end_stocks', '086': 'total_supply', '178': 'total_dist'}

# 历史聚合实体：这些是"世界/区域合计"行，会造成重复计数，必须排除。
# ⚠️ 欧盟标签在 PSD 中随时间轮转：EU-15（≤2004）→ EU-25（2005-2009）→ European Union（2010+）。
#    三者是同一报告主体的不同成员国范围，必须【合并为一个 'European Union' 实体】才能得到连贯的
#    时间序列（否则 2000 年世界产量会少算 18.5 Mt）。这与 94 号报告口径一致
#    （94 号 world[2000] 产量 = 130,764、world[2026] = 184,854，两处均含欧盟）。
EU_LABELS = {'EU-15', 'EU-25', 'European Union', 'EU-27', 'EU-28'}
EXCLUDE = {'World', 'Union of Soviet Socialist Repu',
           'Yugoslavia', 'Czechoslovakia', 'Former Czechoslovakia', 'Other'}

# 载入：{country: {attr_code: {year: value}}}
panel = defaultdict(lambda: defaultdict(dict))
isoc = {}
for r in csv.reader(open(SRC, encoding='utf-8', errors='replace')):
    if len(r) < 12:
        continue
    iso, name, my, ac, val = r[2].strip(), r[3].strip(), r[4].strip(), r[7].strip(), r[11].strip()
    if name in EU_LABELS:
        name = 'European Union'   # 合并欧盟三代口径
    if name in EXCLUDE or ac not in ATTRS:
        continue
    y = int(my)
    if y < 1995 or y > 2026:
        continue
    isoc[iso] = name
    v = float(val) if val not in ('', 'NA') else 0.0
    # ⚠️ 欧盟三代标签的年份区间重叠且 'European Union' 在 2001-2005 为 0——末次写入会把
    #    EU-15/EU-25 的真实值覆盖成 0。故同一 (实体, 属性, 年) 取【最大值】而非末次写入。
    prev = panel[name][ac].get(y)
    panel[name][ac][y] = v if prev is None else max(prev, v)

# 世界合计
world = {ATTRS[ac]: {} for ac in ATTRS}
for y in YEARS:
    for ac in ATTRS:
        world[ATTRS[ac]][y] = round(sum(panel[c][ac].get(y, 0.0) for c in panel), 1)

# 分国：产量、甘蔗/甜菜、消费、出口
countries = {}
for c, d in panel.items():
    prod = d.get('028', {})
    if not prod or max(prod.get(y, 0) for y in YEARS) <= 0:   # 剔零产实体；小产国保留以保世界合计口径一致
        continue
    countries[c] = {
        'iso': next((k for k, v in isoc.items() if v == c), ''),
        'prod': [round(prod.get(y, 0.0), 1) for y in YEARS],
        'cane': [round(d.get('043', {}).get(y, 0.0), 1) for y in YEARS],
        'beet': [round(d.get('030', {}).get(y, 0.0), 1) for y in YEARS],
        'cons': [round(d.get('126', {}).get(y, 0.0), 1) for y in YEARS],
        'exp':  [round(d.get('088', {}).get(y, 0.0), 1) for y in YEARS],
        'imp':  [round(d.get('057', {}).get(y, 0.0), 1) for y in YEARS],
        'end':  [round(d.get('176', {}).get(y, 0.0), 1) for y in YEARS],
    }

# 按 2026 产量排序
rank26 = sorted(countries.items(), key=lambda kv: -kv[1]['prod'][-1])
rank00 = sorted(countries.items(), key=lambda kv: -kv[1]['prod'][0])

def _tot(i):
    return sum(x['prod'][i] for x in countries.values())

def _conc(n, i):
    t = _tot(i)
    return round(100.0 * sum(v['prod'][i] for _, v in rank26[:n]) / t, 1) if t else 0.0

def hhi(idx):
    tot = _tot(idx)
    return round(sum((v['prod'][idx] / tot * 100) ** 2 for v in countries.values()), 1) if tot else 0.0

conc = {
    'years': YEARS,
    'top3': [_conc(3, i) for i in range(len(YEARS))],
    'top5': [_conc(5, i) for i in range(len(YEARS))],
    'top10': [_conc(10, i) for i in range(len(YEARS))],
    'hhi': [hhi(i) for i in range(len(YEARS))],
}

# 甘蔗 / 甜菜全球结构
cane_tot = [round(sum(v['cane'][i] for v in countries.values()), 1) for i in range(len(YEARS))]
beet_tot = [round(sum(v['beet'][i] for v in countries.values()), 1) for i in range(len(YEARS))]
struct = {
    'cane': cane_tot, 'beet': beet_tot,
    'cane_share': [round(100.0 * cane_tot[i] / (cane_tot[i] + beet_tot[i]), 1) if (cane_tot[i] + beet_tot[i]) else 0.0 for i in range(len(YEARS))],
}

# 分国增长率（2000 -> 2026）与纯增量
growth = []
for c, v in rank26:
    p00, p26 = v['prod'][0], v['prod'][-1]
    d = p26 - p00
    growth.append({
        'country': c, 'iso': v['iso'], 'p2000': p00, 'p2026': p26,
        'delta': round(d, 1), 'pct': round(100.0 * d / p00, 1) if p00 > 0 else None,
        'cane26': v['cane'][-1], 'beet26': v['beet'][-1],
        'cane_share26': round(100.0 * v['cane'][-1] / p26, 1) if p26 > 0 else 0.0,
        'cons26': v['cons'][-1],
        'exp26': v['exp'][-1],
        'imp26': v['imp'][-1],
        'end26': v['end'][-1],
        'self_suff': round(100.0 * p26 / v['cons'][-1], 1) if v['cons'][-1] > 0 else None,
        'export_ratio': round(100.0 * v['exp'][-1] / p26, 1) if p26 > 0 else None,
    })

# 主要生产国（2026 产量 Top 15）完整时间序列
top15 = [c for c, _ in rank26[:15]]
series = {'years': YEARS, 'ranking': top15,
          'data': {c: countries[c]['prod'] for c in top15},
          'cane': {c: countries[c]['cane'] for c in top15},
          'beet': {c: countries[c]['beet'] for c in top15},
          'cons': {c: countries[c]['cons'] for c in top15},
          'exp': {c: countries[c]['exp'] for c in top15},
          'imp': {c: countries[c]['imp'] for c in top15}}

# 产区集中度演变（前 5 国份额，逐年）
top5_series = {c: countries[c]['prod'] for c, _ in rank26[:5]}
def _sh(c, i):
    t = _tot(i)
    return round(100.0 * countries[c]['prod'][i] / t, 1) if t else 0.0
share_series = {c: [_sh(c, i) for i in range(len(YEARS))] for c in top5_series}

# 甜菜糖国 vs 甘蔗糖国
beet_ctry = sorted([(c, v['beet'][-1], v['prod'][-1]) for c, v in countries.items() if v['beet'][-1] > 100],
                   key=lambda t: -t[1])
cane_ctry = sorted([(c, v['cane'][-1], v['prod'][-1]) for c, v in countries.items() if v['cane'][-1] > 100],
                   key=lambda t: -t[1])

# 消费-产量缺口（自给率极值）
gap = []
for c, v in countries.items():
    if v['cons'][-1] > 300:
        gap.append({'country': c, 'prod': v['prod'][-1], 'cons': v['cons'][-1], 'imp': v['imp'][-1],
                    'self_suff': round(100.0 * v['prod'][-1] / v['cons'][-1], 1) if v['cons'][-1] else None,
                    'deficit': round(v['cons'][-1] - v['prod'][-1], 1)})
gap.sort(key=lambda x: x['self_suff'] if x['self_suff'] is not None else 999)

out = {
    'meta': {'as_of': '2026-09-11 PSD 快照（本地 psd_sugar_all.csv）',
             'unit': '千吨，原糖当量（raw value）',
             'n_countries': len(countries),
             'years': [YEARS[0], YEARS[-1]],
             'note': '分国市场年窗口不同（巴西4-3月/中国印度10-9月/泰国12-11月）；MY2026 为 USDA 预测值',
             'threshold': '入样门槛：2000-2026 任一年产量 ≥ 5 万吨'},
    'world': {k: [v[y] for y in YEARS] for k, v in world.items()},
    'concentration': conc,
    'structure': struct,
    'series': series,
    'share_series': share_series,
    'growth': growth,
    'rank2000': [c for c, _ in rank00[:15]],
    'beet_countries': [{'country': c, 'beet': b, 'prod': p} for c, b, p in beet_ctry[:12]],
    'cane_countries': [{'country': c, 'cane': b, 'prod': p} for c, b, p in cane_ctry[:12]],
    'self_sufficiency': gap[:20],
    'self_sufficiency_high': sorted([g for g in gap if g['self_suff']], key=lambda x: -x['self_suff'])[:12],
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---- 控制台复核输出 ----
print('=' * 72)
print('入样国家数:', len(countries), '| 年份:', YEARS[0], '-', YEARS[-1])
print('=' * 72)
W = out['world']
for i, y in enumerate(YEARS):
    if y in (2000, 2005, 2010, 2015, 2020, 2024, 2025, 2026):
        w = W['production'][i]; c = W['disappearance'][i]; e = W['end_stocks'][i]
        st = 100.0 * e / c if c else 0
        print(f'{y}  产量 {w:>9,.0f}  消费 {c:>9,.0f}  期末库存 {e:>9,.0f}  STU {st:5.1f}%')
print()
print('--- 全球产量集中度 ---')
for i in (0, len(YEARS) - 1):
    print(f"  {YEARS[i]}: Top3 {conc['top3'][i]}%  Top5 {conc['top5'][i]}%  Top10 {conc['top10'][i]}%  HHI {conc['hhi'][i]}")
print()
print('--- 甘蔗 / 甜菜结构 ---')
for i in (0, len(YEARS) - 1):
    print(f"  {YEARS[i]}: 甘蔗 {struct['cane'][i]:,.0f}  甜菜 {struct['beet'][i]:,.0f}  甘蔗占比 {struct['cane_share'][i]}%")
print()
print('--- 2026 产量 Top 15 ---')
for i, (c, v) in enumerate(rank26[:15]):
    g = next(x for x in growth if x['country'] == c)
    pct = f"{g['pct']:+.0f}%" if g['pct'] is not None else 'n/a'
    print(f"{i+1:>2}. {c:<22} {v['prod'][-1]:>8,.0f}  ({v['prod'][0]:>7,.0f} → {pct:>7})  甘蔗占比 {g['cane_share26']:>5.1f}%  出口/产量 {g['export_ratio'] if g['export_ratio'] else 0:>5.1f}%")
print()
print('--- 甜菜糖 Top 8 ---')
for x in out['beet_countries'][:8]:
    print(f"  {x['country']:<20} 甜菜 {x['beet']:>8,.0f}  / 总产 {x['prod']:>8,.0f}")
print()
print('--- 自给率最低（消费>30万吨）---')
for x in out['self_sufficiency'][:8]:
    print(f"  {x['country']:<20} 自给率 {x['self_suff']:>5.1f}%  缺口 {x['deficit']:>8,.0f}  产量 {x['prod']:>8,.0f}")
print()
print("saved ->", OUT)
