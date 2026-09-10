# -*- coding: utf-8 -*-
"""
以 2026-09-03 高点为基准，测算 WTI 12 条月差价差的突破情况。
口径：价差 = 近月 - 远月（backwardation 为正）
baseline(高点) 用两种定义：
  base_close = 09-03 当日 4h bar 的 close 口径价差最大值
  base_high  = 09-03 当日 4h bar 的 (high_near - high_far) 最大值（日内上沿近似）
"""
import json, sys, csv, datetime as dt
from statistics import mean, pstdev

sys.stdout.reconfigure(encoding='utf-8')

SLOTS = ['CL2610','CL2611','CL2612','CL2701','CL2702','CL2703']
LAB = {'CL2610':'OCT26','CL2611':'NOV26','CL2612':'DEC26','CL2701':'JAN27','CL2702':'FEB27','CL2703':'MAR27'}
COMBOS = [
    ('+1','CL2610','CL2611'),('+1','CL2611','CL2612'),('+1','CL2612','CL2701'),
    ('+1','CL2701','CL2702'),('+1','CL2702','CL2703'),
    ('+2','CL2610','CL2612'),('+2','CL2611','CL2701'),('+2','CL2612','CL2702'),('+2','CL2701','CL2703'),
    ('+3','CL2610','CL2701'),('+3','CL2611','CL2702'),('+3','CL2612','CL2703'),
]

# ---------- 4h 数据（raw json，含 09-10 bar） ----------
raw = json.load(open('results/futu_spread_4h_6legs_raw.json', encoding='utf-8'))['legs']
def T4(ms):
    return dt.datetime.fromtimestamp(ms/1000+8*3600, dt.UTC)
# 时间对齐
tk = [x['time_key'] for x in raw['US.CL2610']]
for s in SLOTS:
    assert [x['time_key'] for x in raw['US.'+s]] == tk, s
n = len(tk)
bars = {s: raw['US.'+s] for s in SLOTS}

# ---------- 日线数据 ----------
daily = {}
for s in SLOTS:
    rows = list(csv.DictReader(open(f'data/cl_contracts/daily/US.{s}.csv', encoding='utf-8')))
    daily[s] = rows
dn = len(daily['CL2610'])
for s in SLOTS:
    assert len(daily[s]) == dn, s
ddate = [r['date'] for r in daily['CL2610']]

def dmax_oi():
    return max(daily[s][-1]['open_interest'] for s in SLOTS)

# ---------- 逐条价差 ----------
out = []
for tier, a, b in COMBOS:
    span = int(tier[1])
    # 4h 序列
    c4 = [round(bars[a][i]['close']-bars[b][i]['close'], 4) for i in range(n)]
    h4 = [round(bars[a][i]['high']-bars[b][i]['high'], 4) for i in range(n)]
    l4 = [round(bars[a][i]['low']-bars[b][i]['low'], 4) for i in range(n)]
    # 日线序列
    cd = [round(float(daily[a][i]['close'])-float(daily[b][i]['close']), 4) for i in range(dn)]
    hd = [round(float(daily[a][i]['high'])-float(daily[b][i]['high']), 4) for i in range(dn)]

    # 定位 09-03
    i903 = [i for i in range(n) if T4(tk[i]).strftime('%m-%d') == '09-03']
    j903 = ddate.index('2026-09-03')
    # 最新（4h）
    ilast = n-1
    tlast = T4(tk[ilast])
    # baseline
    base_c = max(c4[i] for i in i903)          # 09-03 4h close 口径最高
    base_h = max(h4[i] for i in i903)          # 09-03 4h 上沿口径
    base_dh = hd[j903]                         # 09-03 日线日内上沿（更严格）
    base_dc = cd[j903]                         # 09-03 日线收盘
    # 09-03 之后至今
    since = c4[i903[-1]+1:]
    peak_since = max(since)
    ipeak = i903[-1]+1+since.index(peak_since)
    now4 = c4[-1]
    nowd = cd[-1]
    # 波动归一：近 60 个 4h bar 的价差变动标准差
    dif = [c4[i]-c4[i-1] for i in range(1, n)]
    sig = pstdev(dif[-240:])   # 约 60 交易日（4h×4/日）
    out.append(dict(
        tier=tier, span=span, name=f'{LAB[a]}-{LAB[b]}',
        base_c=base_c, base_h=base_h, base_dc=base_dc, base_dh=base_dh,
        now4=now4, nowd=nowd, peak_since=peak_since,
        t_peak=T4(tk[ipeak]).strftime('%m-%d %H:%M'),
        sigma=sig,
        n_903=len(i903),
        brk_c=now4-base_c, brk_h=now4-base_h,
        brk_pct=(now4-base_c)/base_c*100 if base_c else float('nan'),
        brk_sig=(now4-base_c)/sig if sig else float('nan'),
        peak_brk=peak_since-base_c,
        broke=now4 > base_c, ever=peak_since > base_c,
        pm_now=now4/span, pm_base=base_c/span, pm_brk=(now4-base_c)/span,
    ))

tlast = T4(tk[-1]).strftime('%Y-%m-%d %H:%M')

print('='*118)
print(f'4h 数据：{n} 根，最新 bar = {tlast}（UTC+8）｜ 日线最新 = {ddate[-1]}')
print(f'09-03 4h bar 数 = {out[0]["n_903"]}')
print('='*118)
print()
print('【表1】以 09-03 高点（4h close 口径）为基准')
print(f'{"档":<3}{"组合":<12}{"09-03高点":>10}{"09-03上沿":>10}{"最新":>8}{"峰值":>8}{"峰值时刻":>12}{"突破$":>8}{"突破%":>8}{"σ倍数":>8}{"判定":>6}')
for r in sorted(out, key=lambda x: -x['brk_c']):
    flag = '已破' if r['broke'] else ('曾破' if r['ever'] else '未破')
    print(f"{r['tier']:<3}{r['name']:<12}{r['base_c']:>10.2f}{r['base_h']:>10.2f}{r['now4']:>8.2f}{r['peak_since']:>8.2f}{r['t_peak']:>12}{r['brk_c']:>+8.2f}{r['brk_pct']:>+7.1f}%{r['brk_sig']:>8.1f}{flag:>6}")

print()
print('【表2】日线口径核对（09-03 日线上沿 vs 09-10 收盘）')
print(f'{"组合":<12}{"09-03上沿":>10}{"09-03收":>9}{"09-09收":>9}{"09-10收":>9}{"超上沿$":>9}{"超上沿%":>8}')
for r in sorted(out, key=lambda x: -(x['nowd']-x['base_dh'])):
    db = r['nowd']-r['base_dh']
    print(f"{r['name']:<12}{r['base_dh']:>10.2f}{r['base_dc']:>9.2f}{r['nowd']:>9.2f}{r['now4']:>9.2f}{db:>+9.2f}{(db/r['base_dh']*100 if r['base_dh'] else 0):>+7.1f}%")

print()
print('【排序A】按绝对突破幅度（$/bbl，最新 − 09-03 高点）')
for i, r in enumerate(sorted(out, key=lambda x: -x['brk_c']), 1):
    print(f"  {i:>2}. {r['name']:<12} {r['brk_c']:>+6.2f}  (基线 {r['base_c']:.2f} → 最新 {r['now4']:.2f})")
print()
print('【排序B】按相对突破幅度（%）')
for i, r in enumerate(sorted(out, key=lambda x: -(x['brk_pct'] if x['brk_pct']==x['brk_pct'] else -99)), 1):
    print(f"  {i:>2}. {r['name']:<12} {r['brk_pct']:>+7.1f}%")
print()
print('【排序C】按归一陡度突破（$/月，剔除跨月数）')
for i, r in enumerate(sorted(out, key=lambda x: -x['pm_brk']), 1):
    print(f"  {i:>2}. {r['name']:<12} {r['pm_brk']:>+6.2f} $/月   (基线陡度 {r['pm_base']:.2f} → 最新 {r['pm_now']:.2f})")
print()
print('【排序D】按波动归一（突破 / 近60日4h变动σ）')
for i, r in enumerate(sorted(out, key=lambda x: -x['brk_sig']), 1):
    print(f"  {i:>2}. {r['name']:<12} {r['brk_sig']:>+6.1f}σ   (1σ={r['sigma']:.2f})")

json.dump(dict(meta=dict(n=n, tlast=tlast, dlast=ddate[-1]), rows=out),
          open('Temp/breakout_0903.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('saved Temp/breakout_0903.json')
