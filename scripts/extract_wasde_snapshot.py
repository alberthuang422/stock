# -*- coding: utf-8 -*-
"""
WASDE "往年同期"口径提取：每年9月报告里，对"当前市场年度(Proj.)"的五国期末库存预测
- 数据源: Temp/wasde_snapshot/oce-wasde-report-data-{yyyy}-09.csv (2021-2026)
- 取数: Commodity ∈ {Wheat, Corn, Oilseed Soybean}, Attribute='Ending Stocks',
        Unit='Million Metric Tons', Region ∈ 五国, MarketYear 的 Proj. flag
- 口径: 三硬=US/CA/AS, 两软=BR/E4, 五国=并集
输出: results/wasde_snapshot_sameperiod.json + 打印验证
"""
import csv, os, json, glob

SNAP_DIR = '/Users/alberthuang/Desktop/股票分析/Temp/wasde_snapshot'
OUT = '/Users/alberthuang/Desktop/股票分析/results/wasde_snapshot_sameperiod.json'

# 品种名 -> CSV Commodity 名
COM_MAP = {'wheat': 'Wheat', 'corn': 'Corn', 'soybean': 'Oilseed, Soybean'}
# 国别 -> Region 名
REG = {'US': 'United States', 'CA': 'Canada', 'AS': 'Australia',
       'BR': 'Brazil', 'E4': 'European Union'}
HARD = ['US', 'CA', 'AS']
SOFT = ['BR', 'E4']
FIVE = HARD + SOFT


def parse(csv_path):
    """返回 {com_mod: {cc: {'flag':..., 'value':..., 'my':...} }} 取 Proj. 当前年度的 Ending Stocks(Mt)"""
    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    out = {}
    for com_mod, com_name in COM_MAP.items():
        out[com_mod] = {}
        # 先找 MarketYear 里 Proj. flag 对应的年度
        proj_years = set()
        for x in rows:
            if x['Commodity'] == com_name and x['Attribute'] == 'Ending Stocks' \
               and x['Unit'] == 'Million Metric Tons' and x['Region'] in REG.values():
                if x['ProjEstFlag'] and ('Proj' in x['ProjEstFlag']):
                    proj_years.add(x['MarketYear'])
        for cc, reg in REG.items():
            best = None
            for x in rows:
                if x['Commodity'] == com_name and x['Region'] == reg \
                   and x['Attribute'] == 'Ending Stocks' \
                   and x['Unit'] == 'Million Metric Tons':
                    is_proj = x['ProjEstFlag'] and 'Proj' in x['ProjEstFlag']
                    if is_proj:
                        try:
                            v = float(x['Value'].replace(',', ''))
                        except ValueError:
                            continue
                        best = {'value': v, 'my': x['MarketYear'], 'flag': x['ProjEstFlag']}
                        break
            if best:
                out[com_mod][cc] = best
    return out


# 收集所有 9 月快照按年组织
snaps = {}
for y in range(2021, 2027):
    csv_path = os.path.join(SNAP_DIR, f'oce-wasde-report-data-{y}-09.csv')
    if os.path.exists(csv_path):
        snaps[y] = parse(csv_path)

# 每个"快照年 y" 对应"市场年度" 起始年 = y (玉米/大豆) ；小麦市场年度6月开始，也是 y/yy+1
# 但 MarketYear 字段里直接是 'yyyy/yy+1'，我们按快照年分组即可
# 构造序列: my_year(y) -> 三口径
series = {com: {'years': [], 'hard': [], 'soft': [], 'five': []} for com in COM_MAP}
for y in sorted(snaps.keys()):
    for com in COM_MAP:
        d = snaps[y].get(com, {})
        hard = sum(d.get(cc, {}).get('value', 0) for cc in HARD)
        soft = sum(d.get(cc, {}).get('value', 0) for cc in SOFT)
        five = hard + soft
        series[com]['years'].append(str(y))
        series[com]['hard'].append(round(hard, 2))
        series[com]['soft'].append(round(soft, 2))
        series[com]['five'].append(round(five, 2))

# 打印验证
print('=== 每个9月快照解析出的五个国家期末库存(Mt) ===')
for y in sorted(snaps.keys()):
    print(f'\n--- {y}-09 快照 ---')
    for com in COM_MAP:
        d = snaps[y].get(com, {})
        line = ', '.join(f'{REG[cc]}={d[cc]["value"]:.1f}({d[cc]["my"]})' for cc in FIVE if cc in d)
        print(f'  {com:8s}: {line}')

print('\n=== 往年同期口径 三口径序列 ===')
for com in COM_MAP:
    s = series[com]
    print(f'\n{com}: years={s["years"]}')
    print(f'  三硬={s["hard"]}')
    print(f'  两软={s["soft"]}')
    print(f'  五国={s["five"]}')

# 补一个 US 单列（大豆三硬核心是美国）
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({'series': series}, open(OUT, 'w'), ensure_ascii=False, indent=2)
print('\nOK ->', OUT, f'({len(snaps)} 个快照)')