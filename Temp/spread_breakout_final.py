# -*- coding: utf-8 -*-
"""
最终口径：
  基准 = 09-03 当日 4h 收盘口径价差最大值（= 用户 4h 图上看到的 09-03 高点）
  最新 = 日线 2026-09-10 收盘价差（= 最新价，4h 在该时点滞后）
  严格基准 = 09-03 日线日内上沿（high_near − high_far），做稳健性对照
排序 A 绝对$/B 相对%/C 归一陡度$/月/D 波动σ/E 自08-26累计陡度
"""
import json, sys, csv, datetime as dt
from statistics import pstdev
sys.stdout.reconfigure(encoding='utf-8')

SLOTS = ['CL2610','CL2611','CL2612','CL2701','CL2702','CL2703']
LAB = {'CL2610':'OCT26','CL2611':'NOV26','CL2612':'DEC26','CL2701':'JAN27','CL2702':'FEB27','CL2703':'MAR27'}
POS = {'CL2610':0,'CL2611':1,'CL2612':2,'CL2701':3,'CL2702':4,'CL2703':5}
COMBOS = [
    ('+1','CL2610','CL2611'),('+1','CL2611','CL2612'),('+1','CL2612','CL2701'),
    ('+1','CL2701','CL2702'),('+1','CL2702','CL2703'),
    ('+2','CL2610','CL2612'),('+2','CL2611','CL2701'),('+2','CL2612','CL2702'),('+2','CL2701','CL2703'),
    ('+3','CL2610','CL2701'),('+3','CL2611','CL2702'),('+3','CL2612','CL2703'),
]
raw = json.load(open('results/futu_spread_4h_6legs_raw.json', encoding='utf-8'))['legs']
tk = [x['time_key'] for x in raw['US.CL2610']]
n = len(tk)
def T(ms): return dt.datetime.fromtimestamp(ms/1000+8*3600, dt.UTC)
D = {s: list(csv.DictReader(open(f'data/cl_contracts/daily/US.{s}.csv', encoding='utf-8'))) for s in SLOTS}
ddate = [r['date'] for r in D['CL2610']]
j903, j910 = ddate.index('2026-09-03'), ddate.index('2026-09-10')

out = []
for tier, a, b in COMBOS:
    span = int(tier[1])
    c4 = [round(raw['US.'+a][i]['close']-raw['US.'+b][i]['close'], 4) for i in range(n)]
    i903 = [i for i in range(n) if T(tk[i]).strftime('%m-%d') == '09-03']
    base = round(max(c4[i] for i in i903), 2)                       # 09-03 4h 高点
    base_strict = round(float(D[a][j903]['high'])-float(D[b][j903]['high']), 2)  # 09-03 日线上沿
    now = round(float(D[a][j910]['close'])-float(D[b][j910]['close']), 2)        # 最新
    dif = [c4[i]-c4[i-1] for i in range(1, n)]
    sig = pstdev(dif[-240:])
    # 08-26 起
    i826 = [i for i in range(n) if T(tk[i]).strftime('%m-%d') == '08-26']
    c826 = c4[i826[0]]
    # 首次突破
    iend = i903[-1]
    fb = next((i for i in range(iend+1, n) if c4[i] > base), None)
    out.append(dict(
        tier=tier, span=span, name=f'{LAB[a]}-{LAB[b]}',
        seg_from=LAB[a], seg_to=LAB[b],
        pos=POS[a]/5*100,   # 曲线位置 0=最前 100=最后
        base=base, base_strict=base_strict, now=now,
        brk=round(now-base, 2), brk_pct=round((now-base)/base*100, 1),
        brk_pm=round((now-base)/span, 2), brk_sig=round((now-base)/sig, 1),
        i18=now-base_strict,
        fb=r'T' if fb is not None else '-',
        since826=round(now-c826, 2), since826_pct=round((now-c826)/c826*100, 1),
        since826_pm=round((now-c826)/span, 2),
        broke=now > base, broke_strict=now > base_strict,
    ))

def rank(key, rev=True):
    return {r['name']: i for i, r in enumerate(sorted(out, key=lambda x: -x[key] if rev else x[key]), 1)}
rA, rB, rC, rD, rE = rank('brk'), rank('brk_pct'), rank('brk_pm'), rank('brk_sig'), rank('since826_pm')
for r in out:
    rs = [rA[r['name']], rB[r['name']], rC[r['name']], rD[r['name']], rE[r['name']]]
    r['ranks'] = rs
    r['avg_rank'] = round(sum(rs)/5, 1)

print('基准=09-03 4h高点 ｜ 最新=09-10 收盘（日线） ｜ 4h 最后 bar 2026-09-10 10:00')
print('='*116)
print(f"{'组合':<12}{'档':>3}{'09-03高':>9}{'严格上沿':>9}{'最新':>8}{'突破$':>8}{'突破%':>8}{'陡度$/月':>9}{'σ':>7}{'破?':>5}")
for r in sorted(out, key=lambda x: x['avg_rank']):
    print(f"{r['name']:<12}{r['tier']:>3}{r['base']:>9.2f}{r['base_strict']:>9.2f}{r['now']:>8.2f}{r['brk']:>+8.2f}{r['brk_pct']:>+7.1f}%{r['brk_pm']:>+9.2f}{r['brk_sig']:>+7.1f}{'✓' if r['broke'] else '✗':>5}")
print()
nb = sum(1 for r in out if r['broke'])
print(f'突破计数：{nb}/12（按 4h 高点基准）｜ {sum(1 for r in out if r["broke_strict"])}/12（按日线严格上沿）')
print()
print('多方法名次矩阵（1=最强）')
print(f"{'组合':<12}{'A绝对$':>8}{'B相对%':>8}{'C陡度':>7}{'D波动σ':>8}{'E自0826':>9}{'均名次':>8}")
for r in sorted(out, key=lambda x: x['avg_rank']):
    rs = r['ranks']
    print(f"{r['name']:<12}{rs[0]:>8}{rs[1]:>8}{rs[2]:>7}{rs[3]:>8}{rs[4]:>9}{r['avg_rank']:>8.1f}")

json.dump(dict(meta=dict(t4='2026-09-10 10:00', dlast=ddate[-1], n_broke=nb), rows=out),
          open('Temp/breakout_final.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nsaved Temp/breakout_final.json')
