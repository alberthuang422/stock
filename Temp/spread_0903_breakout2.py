# -*- coding: utf-8 -*-
"""09-03 高点为基准的突破分析 v2：增加基线分位、突破时点、08-26 起点对照"""
import json, sys, csv, datetime as dt
from statistics import pstdev
sys.stdout.reconfigure(encoding='utf-8')

SLOTS = ['CL2610','CL2611','CL2612','CL2701','CL2702','CL2703']
LAB = {'CL2610':'OCT26','CL2611':'NOV26','CL2612':'DEC26','CL2701':'JAN27','CL2702':'FEB27','CL2703':'MAR27'}
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
jd = {d: i for i, d in enumerate(ddate)}

out = []
for tier, a, b in COMBOS:
    span = int(tier[1])
    c4 = [round(raw['US.'+a][i]['close']-raw['US.'+b][i]['close'], 4) for i in range(n)]
    cd = [round(float(D[a][i]['close'])-float(D[b][i]['close']), 4) for i in range(len(ddate))]
    i903 = [i for i in range(n) if T(tk[i]).strftime('%m-%d') == '09-03']
    iend = i903[-1]
    base = max(c4[i] for i in i903)
    now = c4[-1]
    # 基线在近 130 日 4h 序列中的分位（说明它是否"尖顶"）
    hist = c4[-520:]
    bpct = sum(1 for x in hist if x <= base)/len(hist)*100
    # 突破时点
    fb = next((i for i in range(iend+1, n) if c4[i] > base), None)
    fb_t = T(tk[fb]).strftime('%m-%d %H:%M') if fb is not None else '—'
    # 09-08 收盘是否已破
    i908 = [i for i in range(n) if T(tk[i]).strftime('%m-%d') == '09-08']
    c908 = c4[i908[-1]] if i908 else None
    # 08-26 起点
    i826 = [i for i in range(n) if T(tk[i]).strftime('%m-%d') == '08-26']
    c826 = c4[i826[0]] if i826 else None
    # σ
    dif = [c4[i]-c4[i-1] for i in range(1, n)]
    sig = pstdev(dif[-240:])
    out.append(dict(
        tier=tier, span=span, name=f'{LAB[a]}-{LAB[b]}',
        base=base, now=now, bpct=bpct,
        brk=now-base, brk_pct=(now-base)/base*100,
        brk_pm=(now-base)/span, brk_sig=(now-base)/sig, sigma=sig,
        fb=fb_t, c908=c908, broke_908=(c908 is not None and c908 > base),
        c826=c826, since826=now-c826, since826_pct=(now-c826)/c826*100 if c826 else float('nan'),
        since826_pm=(now-c826)/span, pm_now=now/span, pm_base=base/span,
    ))

print('【基线性质】09-03 高点在近 130 个交易日 4h 序列中的分位（越接近100%=当天是尖顶）')
for r in sorted(out, key=lambda x: -x['bpct']):
    print(f"  {r['name']:<12}{r['tier']:<3} 09-03高点={r['base']:>6.2f}  历史分位={r['bpct']:>5.1f}%  最新={r['now']:>6.2f}")

print()
print('【突破时点与新鲜度】')
print(f"{'组合':<12}{'档':<3}{'基线':>7}{'最新':>7}{'首次突破时刻':>14}{'09-08是否已破':>13}")
for r in sorted(out, key=lambda x: -x['brk']):
    print(f"{r['name']:<12}{r['tier']:<3}{r['base']:>7.2f}{r['now']:>7.2f}{r['fb']:>14}{('已破' if r['broke_908'] else '未破(新启动)'):>13}")

print()
print('【排序E】按 08-26 起累计扩张（归一陡度 $/月，剔除基线效应）')
for i, r in enumerate(sorted(out, key=lambda x: -x['since826_pm']), 1):
    print(f"  {i:>2}. {r['name']:<12} {r['since826_pm']:>+6.2f} $/月   绝对 {r['since826']:>+6.2f} ({r['since826_pct']:>+6.1f}%)")

print()
print('【汇总矩阵】行=组合，列=四种排序的名次')
rankA = {r['name']: i for i, r in enumerate(sorted(out, key=lambda x: -x['brk']), 1)}
rankB = {r['name']: i for i, r in enumerate(sorted(out, key=lambda x: -x['brk_pct']), 1)}
rankC = {r['name']: i for i, r in enumerate(sorted(out, key=lambda x: -x['brk_pm']), 1)}
rankD = {r['name']: i for i, r in enumerate(sorted(out, key=lambda x: -x['brk_sig']), 1)}
rankE = {r['name']: i for i, r in enumerate(sorted(out, key=lambda x: -x['since826_pm']), 1)}
print(f"{'组合':<12}{'档':<3}{'A绝对$':>8}{'B相对%':>8}{'C陡度':>7}{'D波动σ':>8}{'E自0826':>9}{'均名次':>8}")
rows = []
for r in out:
    nm = r['name']
    rs = [rankA[nm], rankB[nm], rankC[nm], rankD[nm], rankE[nm]]
    rows.append((nm, r, rs, sum(rs)/5))
for nm, r, rs, avg in sorted(rows, key=lambda x: x[3]):
    print(f"{nm:<12}{r['tier']:<3}{rs[0]:>8}{rs[1]:>8}{rs[2]:>7}{rs[3]:>8}{rs[4]:>9}{avg:>8.1f}")

json.dump(dict(meta=dict(n=n, tlast=T(tk[-1]).strftime('%Y-%m-%d %H:%M'), dlast=ddate[-1]), rows=out),
          open('Temp/breakout_0903.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nsaved Temp/breakout_0903.json')
