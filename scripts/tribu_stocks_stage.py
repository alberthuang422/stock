# -*- coding: utf-8 -*-
"""
三品种(小麦/玉米/大豆) 三口径库存分析 —— 2015-2026 分阶段(疫情前后)
  三硬  = US + CA + AS (美/加/澳, 有官方库存盘点)
  两软  = BR + E4      (巴/欧盟, 库存靠残差)
  五国  = 三硬 + 两软
阶段: 疫情前 2015-2019 / 疫情后 2020-2026, 当前=2026 单独标出
"""
import json, os, csv

PSD_DIR = '/Users/alberthuang/Desktop/股票分析/Temp/psd'
OUT_DIR = '/Users/alberthuang/Desktop/股票分析/results'

HARD = ['US', 'CA', 'AS']
SOFT = ['BR', 'E4']
FIVE = HARD + SOFT
CMDS = ['wheat', 'corn', 'soybean']
YEARS = list(range(2015, 2027))   # 2015-2026
Y_PRE = list(range(2015, 2020))    # 疫情前
Y_POST = list(range(2020, 2027))   # 疫情后(含2020疫情年)


def load(com, y):
    with open(os.path.join(PSD_DIR, f'{com}_{y}.json')) as f:
        raw = json.load(f)
    best = {}
    for r in raw:
        k = (r['countryCode'], r['attributeId'])
        m = int(r['month'])
        if k not in best or m > best[k][0]:
            best[k] = (m, r['value'])
    out = {}
    for (cc, a), (m, v) in best.items():
        out.setdefault(cc, {})[a] = v
    return out


def agg(data, ccs):
    return sum(data.get(c, {}).get(176, 0.0) for c in ccs)


def mean(vals):
    return sum(vals) / len(vals)


res = {}
for com in CMDS:
    hard, soft, five = [], [], []
    for y in YEARS:
        d = load(com, y)
        hard.append(round(agg(d, HARD) / 1000, 1))
        soft.append(round(agg(d, SOFT) / 1000, 1))
        five.append(round(agg(d, FIVE) / 1000, 1))
    res[com] = {'years': [str(y) for y in YEARS], 'hard': hard, 'soft': soft, 'five': five}


def stage_stat(series, pre_idx, post_idx):
    pre = [series[i] for i in pre_idx]
    post = [series[i] for i in post_idx]
    cur = series[-1]  # 2026
    pre_m = mean(pre)
    post_m = mean(post)
    return {
        'pre_mean': round(pre_m, 1),
        'post_mean': round(post_m, 1),
        'cur': round(cur, 1),
        'pre_vs_post': round(post_m - pre_m, 1),
        'cur_vs_post': round(cur - post_m, 1),
        'cur_vs_pre': round(cur - pre_m, 1),
    }


pre_idx = [YEARS.index(y) for y in Y_PRE]
post_idx = [YEARS.index(y) for y in Y_POST]

stats = {}
for com in CMDS:
    d = res[com]
    stats[com] = {
        'hard': stage_stat(d['hard'], pre_idx, post_idx),
        'soft': stage_stat(d['soft'], pre_idx, post_idx),
        'five': stage_stat(d['five'], pre_idx, post_idx),
    }

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, 'tribu_stocks_stage.json'), 'w') as f:
    json.dump({'series': res, 'stats': stats,
               'y_pre': Y_PRE, 'y_post': Y_POST}, f, ensure_ascii=False, indent=2)

for com in CMDS:
    with open(os.path.join(OUT_DIR, f'{com}_tribu_stage.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['year', 'hard_end', 'soft_end', 'five_end'])
        d = res[com]
        for i, y in enumerate(YEARS):
            w.writerow([y, d['hard'][i], d['soft'][i], d['five'][i]])

print('=' * 78)
for com in CMDS:
    s = stats[com]
    print(f'\n### {com}')
    for gk, gl in [('hard', '三硬'), ('soft', '两软'), ('five', '五国')]:
        g = s[gk]
        print(f'  [{gl}] 疫情前均值={g["pre_mean"]:>7.1f}  疫情后均值={g["post_mean"]:>7.1f}  '
              f'2026={g["cur"]:>7.1f}  前→后={g["pre_vs_post"]:>+7.1f}  后→今={g["cur_vs_post"]:>+7.1f}')
print('OK ->', os.path.join(OUT_DIR, 'tribu_stocks_stage.json'))