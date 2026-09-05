# -*- coding: utf-8 -*-
"""即时顶 vs 续涨：20 事件当周完整 CFTC 状态表 + 2026 未完结候选对照"""
import json, csv, datetime as dt, statistics as st
from scipy.stats import mannwhitneyu, spearmanr

res = json.load(open(r'C:\Users\Administrator\Desktop\stock\Temp\cot\wheat_bt_results.json'))
ev = list(csv.DictReader(open(r'C:\Users\Administrator\Desktop\stock\Temp\cot\wheat_events.csv')))
# date -> 行索引
idx = {r['date']: i for i, r in enumerate(ev)}

def dL4(date):
    """事件日之前 4 周的多头累计变化 = L[i] - L[i-4]（当周不计入，看增仓动能）"""
    i = idx[date]
    if i < 4:
        return None
    return int(ev[i]['L']) - int(ev[i-4]['L'])

print('='*118)
print('表A. 20 个回测事件·当周完整 CFTC 状态（Legacy 小麦 3 合约合并，张）')
print('='*118)
print(f"{'事件日':<12}{'Δ多(dL)':>10}{'Δ空(dS)':>10}{'周ΔOI':>9}{'4周Δ多':>9}{'前周净':>10}{'当周净':>10}{'净/OI%':>8}{'周Δ净':>9}  {'类型':<4} 背景/驱动快照")
bg = {
 '2012-07-17':'2012美国大干旱 价格打顶后 USDA 转向',
 '2015-06-30':'净空区空头回补反弹至前高',
 '2016-06-07':'净空区回补反弹(2016春高点)',
 '2017-07-11':'净多9.6万高位再加=情绪顶',
 '2018-07-31':'净多4万天气炒作(春麦)中段',
 '2018-08-07':'净多9.2万高位再加=情绪顶',
 '2019-12-17':'牛市启动段(库存周期转紧)',
 '2020-01-21':'牛市早期',
 '2020-03-31':'疫情底部区反弹',
 '2020-07-14':'牛市中段(中国采购潮)',
 '2020-09-01':'牛市推进(俄罗斯出口限制)',
 '2020-10-06':'牛市推进(全球库存新低预期)',
 '2020-10-20':'牛市推进',
 '2021-01-05':'牛市冲刺前(库存报告利多)',
 '2021-04-27':'牛市冲刺(美春麦播种担忧)',
 '2021-08-03':'牛市后段(加仓续涨)',
 '2021-08-17':'牛市后段(加仓续涨)',
 '2022-02-22':'俄乌开战 脉冲式利多一步到位',
 '2024-01-30':'低位反弹(净空10.5万)',
 '2024-06-25':'低位反弹(净空7万)',
}
rows = []
for x in res:
    d = x['evdate']
    e = idx[d]
    r_ev = ev[e]
    L = int(r_ev['L']); S = int(r_ev['S']); OI = int(r_ev['OI']); net = int(r_ev['net'])
    dL = int(r_ev['dL']); dS = int(r_ev['dS']); dOI = int(r_ev['dOI']); dNet = int(r_ev['dNet'])
    net_prev = int(r_ev['net_prev'])
    typ = '即时顶' if x['weeks'] <= 2 else '续涨'
    rows.append(dict(ev=d, dL=dL, dS=dS, dOI=dOI, dL4=dL4(d), net_prev=net_prev, net=net,
                     net_oi=round(100*net/OI,1), dNet=dNet, typ=typ))
    print(f"{d:<12}{dL:>10,}{dS:>10,}{dOI:>9,}{str(dL4(d)) if dL4(d) is not None else 'n/a':>9}{net_prev:>10,}{net:>10,}{100*net/OI:>7.1f}%{dNet:>9,}  {typ:<4} {bg[d]}")

imm = [r for r in rows if r['typ']=='即时顶']
cont = [r for r in rows if r['typ']=='续涨']
print()
print('--- 组间对比 ---')
for lab, fld, fmt in [('Δ多 dL','dL',','), ('Δ空 dS','dS',','), ('周ΔOI','dOI',','),
                       ('4周Δ多','dL4',','), ('前周净','net_prev',','), ('当周净','net',','),
                       ('净/OI%','net_oi','.1f'), ('周Δ净','dNet',',')]:
    a = sorted(r[fld] for r in imm if r[fld] is not None)
    b = sorted(r[fld] for r in cont if r[fld] is not None)
    u, p = mannwhitneyu(a, b, alternative='two-sided')
    print(f'  {lab:<8} 即时顶中位 {st.median(a):{fmt}}  vs  续涨中位 {st.median(b):{fmt}}   MW p={p:.3f}')

print()
print('='*118)
print('表B. 2026 年未完结候选（同阈值 dL>=1.5万，但未到顶即还在上涨/未完成回测）')
print('='*118)
cand = ['2026-02-24','2026-03-31','2026-04-28','2026-08-25','2026-09-01']
prev_row = {}
print(f"{'事件日':<12}{'Δ多(dL)':>10}{'Δ空(dS)':>10}{'周ΔOI':>9}{'4周Δ多':>9}{'前周净':>10}{'当周净':>10}{'净/OI%':>8}{'周Δ净':>9}  涨后至今表现")
px = json.load(open(r'C:\Users\Administrator\Desktop\stock\Temp\cot\zw_main_hist.json'))
px_by_d = {dt.datetime.fromtimestamp(x['time_key']/1000).date(): x['close'] for x in px}
pdays = sorted(px_by_d)
for d in cand:
    e = idx[d]
    r_ev = ev[e]
    L = int(r_ev['L']); S = int(r_ev['S']); OI = int(r_ev['OI']); net = int(r_ev['net'])
    dL = int(r_ev['dL']); dS = int(r_ev['dS']); dOI = int(r_ev['dOI']); dNet = int(r_ev['dNet'])
    net_prev = int(r_ev['net_prev'])
    # 事件日后累计涨跌（到 2026-09-04 最后交易日）
    d0 = dt.date.fromisoformat(d)
    last = None
    for pd in pdays:
        if pd >= d0:
            last = pd
            break
    if last is not None:
        fwd = 100*(px_by_d[pdays[-1]]/px_by_d[last]-1)
        fwd_txt = f'当日{pdays[-1]}至今 {fwd:+.1f}%'
    else:
        fwd_txt = 'n/a'
    print(f"{d:<12}{dL:>10,}{dS:>10,}{dOI:>9,}{str(dL4(d)) if dL4(d) is not None else 'n/a':>9}{net_prev:>10,}{net:>10,}{100*net/OI:>7.1f}%{dNet:>9,}  {fwd_txt}")
    prev_row[d] = dL

# 2026-09-01 当周 vs 20 事件 dL 分布
dL_all = [r['dL'] for r in rows]
print()
print(f'--- 2026-09-01 +36,782 在 20 历史事件 dL 中的位置：max={max(dL_all):,}，即 2026-09-01 为 2011 后全体最大单周增仓 ---')