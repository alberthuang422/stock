# -*- coding: utf-8 -*-
"""
WASDE 小麦/玉米/大豆 "往年同期口径" vs "事后终稿口径" 对照分析
- 同期口径: scripts/extract_wasde_sameperiod_v2.py 产出（每年9月报告当时的预测）
- 终稿口径: Temp/psd/*.json（PSD 数据库最新修订值, attribute 176=Ending Stocks, 单位千吨）
- 国别集合严格对齐：wheat=US/CA/AS/BR/E4, corn=US/CA/BR/E4, soybean=US/BR/E4
输出: results/wasde_sameperiod_analysis.json
"""
import json, os, statistics as st

ROOT = '/Users/alberthuang/Desktop/股票分析'
YEARS = list(range(2015, 2027))
COUNTRY_SET = {'wheat': ['US', 'CA', 'AS', 'BR', 'E4'],
               'corn': ['US', 'CA', 'BR', 'E4'],
               'soybean': ['US', 'BR', 'E4']}
HARD = ['US', 'CA', 'AS']
SOFT = ['BR', 'E4']
CN = {'US': '美国', 'CA': '加拿大', 'AS': '澳大利亚', 'BR': '巴西', 'E4': '欧盟'}

# ---------- 1) 同期口径 ----------
sp = json.load(open(f'{ROOT}/results/wasde_sameperiod_2015_2026.json'))


def sp_basket(crop, year, which):
    d = sp['detail'][str(year)][crop]['vals']
    if which == 'five':
        return round(sum(d.get(c, 0) for c in COUNTRY_SET[crop]), 2)
    if which == 'hard':
        return round(sum(d.get(c, 0) for c in HARD if c in COUNTRY_SET[crop]), 2)
    if which == 'soft':
        return round(sum(d.get(c, 0) for c in SOFT), 2)


# ---------- 2) 终稿口径（PSD 最新修订） ----------
def final_val(crop, my, cc):
    p = f'{ROOT}/Temp/psd/{crop}_{my}.json'
    if not os.path.exists(p):
        return None
    rows = [x for x in json.load(open(p))
            if x['attributeId'] == 176 and x['countryCode'] == cc]
    if not rows:
        return None
    r = max(rows, key=lambda x: (x['calendarYear'], x['month']))
    return r['value'] / 1000.0  # 千吨 -> Mt


def fn_basket(crop, my, which):
    cs = COUNTRY_SET[crop]
    if which == 'hard':
        cs = [c for c in HARD if c in cs]
    elif which == 'soft':
        cs = [c for c in SOFT if c in cs]
    tot, miss = 0.0, []
    for c in cs:
        v = final_val(crop, my, c)
        if v is None:
            miss.append(c)
        else:
            tot += v
    return round(tot, 2), miss


# ---------- 3) 组装 ----------
out = {'years': [str(y) for y in YEARS], 'crops': {}}
for crop in ['wheat', 'corn', 'soybean']:
    rec = {'sp': {}, 'fn': {}, 'drift': {}, 'cset': COUNTRY_SET[crop]}
    for y in YEARS:
        my = str(y)
        rec['sp'][str(y)] = {w: sp_basket(crop, y, w) for w in ['five', 'hard', 'soft']}
        fnv = {}
        miss = []
        for w in ['five', 'hard', 'soft']:
            v, m = fn_basket(crop, my, w)
            fnv[w] = v
            miss += m
        rec['fn'][str(y)] = fnv
        rec['drift'][str(y)] = round(fnv['five'] - rec['sp'][str(y)]['five'], 2)
    out['crops'][crop] = rec


# ---------- 4) 统计 ----------
def pct_rank(value, arr):
    arr = sorted(arr)
    below = sum(1 for a in arr if a < value)
    return round(100.0 * below / len(arr), 1)


stats = {}
for crop, rec in out['crops'].items():
    sz = {}
    for w in ['five', 'hard', 'soft']:
        cur_sp = rec['sp']['2026'][w]
        cur_fn = rec['fn']['2026'][w]
        hist_sp = [rec['sp'][str(y)][w] for y in YEARS if y < 2026]
        hist_sp5 = [rec['sp'][str(y)][w] for y in range(2021, 2026)]
        hist_fn = [rec['fn'][str(y)][w] for y in YEARS if y < 2026]
        sz[w] = {
            'cur_sp': cur_sp, 'cur_fn': cur_fn,
            'sp_range': [min(hist_sp), max(hist_sp)],
            'sp_median': round(st.median(hist_sp), 2),
            'pct_sp_11y': pct_rank(cur_sp, hist_sp),
            'pct_sp_5y': pct_rank(cur_sp, hist_sp5),
            'fn_range': [min(hist_fn), max(hist_fn)],
            'fn_median': round(st.median(hist_fn), 2),
            'pct_fn_11y': pct_rank(cur_fn, hist_fn),
            'mean_drift': round(sum(rec['drift'][str(y)] for y in YEARS if y < 2026) / 11, 2),
        }
    stats[crop] = sz
out['stats'] = stats

json.dump(out, open(f'{ROOT}/results/wasde_sameperiod_analysis.json', 'w'),
          ensure_ascii=False, indent=2)

# ---------- 5) 打印 ----------
print('=== 五国同期口径 vs 终稿口径（Mt） ===')
for crop, rec in out['crops'].items():
    print(f'\n--- {crop} (国别集: {"+".join(rec["cset"])}) ---')
    print('  年   :', '  '.join(f'{y:>6d}' for y in YEARS))
    print('  同期 :', '  '.join(f'{rec["sp"][str(y)]["five"]:6.1f}' for y in YEARS))
    print('  终稿 :', '  '.join(f'{rec["fn"][str(y)]["five"]:6.1f}' for y in YEARS))
    print('  漂移 :', '  '.join(f'{rec["drift"][str(y)]:6.1f}' for y in YEARS))

print('\n\n=== 2026 位置（百分位） ===')
for crop, sz in stats.items():
    for w in ['five', 'hard']:
        s = sz[w]
        print(f'{crop:8s} [{w}] 2026 同期={s["cur_sp"]:6.2f} | 同期口径: 11年区[{s["sp_range"][0]:.1f},{s["sp_range"][1]:.1f}] '
              f'中位{s["sp_median"]:.1f} → 百分位 11y={s["pct_sp_11y"]}% 5y={s["pct_sp_5y"]}% '
              f'|| 终稿口径 11y 百分位={s["pct_fn_11y"]}%')
print('\nOK -> results/wasde_sameperiod_analysis.json')
