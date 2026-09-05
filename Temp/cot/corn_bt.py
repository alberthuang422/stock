# -*- coding: utf-8 -*-
"""玉米极端净多单周脉冲 → 价格见顶回测（2011-09 后，富途 ZCmain 日线）
事件主键：单周净头寸增幅 dNet>=78,000（全史 1641 周样本外/2011 后 top 量级），剔 2026 未完结
复刻 wheat_bt.py 范式
"""
import json, csv, datetime as dt

# ---------- 1. 事件表 ----------
d = json.load(open('corn_1c_1995.json'))
s = d['series']; ds = sorted(s)
rows = []
for i in range(1, len(ds)):
    p, w = s[ds[i-1]], s[ds[i]]
    rows.append(dict(date=ds[i], prev=ds[i-1], L=w[0], S=w[1], OI=w[2], net=w[0]-w[1],
                     dL=w[0]-p[0], dS=w[1]-p[1], dNet=(w[0]-w[1])-(p[0]-p[1]),
                     dOI=w[2]-p[2], dLpct=(w[0]-p[0])/p[2]*100, net_prev=p[0]-p[1]))
with open('corn_events.csv', 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
print('events', len(rows), rows[0]['date'], '->', rows[-1]['date'])

# ---------- 2. 价格 ----------
px = json.load(open('zc_main_hist.json'))
pxd = {}
for k in px:
    ts = dt.datetime.fromtimestamp(k['time_key']/1000)
    d0 = ts.date().isoformat()
    pxd.setdefault(d0, {'c': k['close'], 'h': k['high']})
pxd = {d0: v for d0, v in sorted(pxd.items())}
days = list(pxd)
print('价格区间', days[0], '->', days[-1], 'n=', len(days), '最新收', pxd[days[-1]]['c'])

def px_at(d, back=6):
    cur = dt.date.fromisoformat(d)
    for _ in range(back):
        if cur.isoformat() in pxd: return cur.isoformat()
        cur = cur - dt.timedelta(days=1)
    return None

def fwd_ret(d0, weeks):
    i = days.index(d0)
    if i + weeks*5 >= len(days): return None
    return (pxd[days[i+weeks*5]]['c']/pxd[d0]['c']-1)*100

def peak_info(d0, max_weeks=52):
    i = days.index(d0)
    j = min(len(days), i + max_weeks*5)
    seg = days[i:j]
    if not seg: return None
    pk = max(seg, key=lambda x: pxd[x]['c'])
    weeks = (len(seg[:seg.index(pk)+1])-1)/5
    return dict(peak_d=pk, weeks=round(weeks, 1), ret=(pxd[pk]['c']/pxd[d0]['c']-1)*100)

# ---------- 3. 筛选事件 ----------
evs = [r for r in rows if r['date'] >= '2011-10-01' and int(r['dNet']) >= 78000 and r['date'] <= '2024-12-31']
print('候选事件(2011-10后 dNet>=78k, <2026):', len(evs))
# 灵敏度
import collections
for thr in [60000, 78000, 90000]:
    n = sum(1 for r in rows if r['date'] >= '2011-10-01' and int(r['dNet']) >= thr and r['date'] <= '2024-12-31')
    print(f'  dNet>=+{thr:,}: n={n}')

res = []
for r in evs:
    d0 = px_at(r['date'])
    if not d0: print('NO PRICE', r['date']); continue
    pi = peak_info(d0)
    if not pi: continue
    res.append(dict(evdate=r['date'], pxdate=d0, p0=pxd[d0]['c'],
                    dL=int(r['dL']), dS=int(r['dS']), dNet=int(r['dNet']), net_prev=int(r['net_prev']),
                    r4=fwd_ret(d0, 4), r8=fwd_ret(d0, 8), r13=fwd_ret(d0, 13), r26=fwd_ret(d0, 26), r52=fwd_ret(d0, 52),
                    **pi))
print('有效事件', len(res))
print()
print(f"{'事件日':<12}{'P0':>8}{'顶日':<12}{'见顶周':>7}{'顶涨%':>8}{'r4':>7}{'r13':>7}{'r26':>7}{'r52':>7}{'dNet':>9}{'多':>8}{'空':>8}")
for x in sorted(res, key=lambda z: z['evdate']):
    f = lambda v: f"{v:+.1f}" if v is not None else "   NA"
    print(f"{x['evdate']:<12}{x['p0']:>8.1f}{x['peak_d']:<12}{x['weeks']:>7.1f}{x['ret']:>+8.1f}{f(x['r4']):>7}{f(x['r13']):>7}{f(x['r26']):>7}{f(x['r52']):>7}{x['dNet']:>9,}{x['dL']:>8,}{x['dS']:>8,}")
json.dump(res, open('corn_bt_results.json', 'w'), ensure_ascii=False)
