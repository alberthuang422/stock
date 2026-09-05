# -*- coding: utf-8 -*-
# 玉米 legacy futures-only 全史（1995-2026）解析 + 2026-09-01 周单周变化定位
# 复刻 wheat_pos.py 范式；市场名变体：'CORN - CHICAGO BOARD OF TRADE' / 'CORN - CBT CORN'(1995)
import zipfile, csv, io, os, json

TMP = os.path.dirname(os.path.abspath(__file__))
FILES = {}
for y in range(1995, 2004): FILES[y] = f'old_{y}.zip'
for y in range(2004, 2026): FILES[y] = f'hist_{y}.zip'
FILES[2026] = 'fo2026.zip'

CORN_NAMES = {'CORN - CHICAGO BOARD OF TRADE', 'CORN - CBT CORN'}

def is_corn(nm):
    u = nm.upper().strip()
    if u not in CORN_NAMES: return False
    # 排除 IOWA CORN YIELD INSURANCE / CSO 等（它们不含上列全名，双保险）
    return True

agg = {}
skip_dup = 0
for y, zf in FILES.items():
    p = os.path.join(TMP, zf)
    if not os.path.exists(p):
        print('MISSING', y); continue
    z = zipfile.ZipFile(p)
    inner = [x for x in z.namelist() if x.lower().endswith('.txt')][0]
    for r in csv.DictReader(io.StringIO(z.read(inner).decode('utf-8', 'replace'))):
        if not is_corn(r['Market and Exchange Names']): continue
        def n(k):
            v = r.get(k, '').replace(',', '').strip()
            return int(v) if v not in ('', '.') else None
        rec = (n('Noncommercial Positions-Long (All)'),
               n('Noncommercial Positions-Short (All)'),
               n('Open Interest (All)'))
        if None in rec: continue
        key = r['As of Date in Form YYYY-MM-DD']
        if key in agg:
            skip_dup += 1  # 同日重复（1995 别名迁移），覆盖为同值校验
            if agg[key] != rec:
                print('  同日冲突', key, agg[key], 'vs', rec)
        agg[key] = rec

ds = sorted(agg)
print('原始周数', len(ds), ds[0], '->', ds[-1], '同日重复', skip_dup)
series = {d: agg[d] for d in ds}  # (L, S, OI)
json.dump({'n': len(ds), 'series': series}, open(os.path.join(TMP, 'corn_1c_1995.json'), 'w'))

def pct(s, v): return round(100 * sum(1 for x in s if x <= v) / len(s), 1)

chg = []
for i in range(1, len(ds)):
    p, w = agg[ds[i-1]], agg[ds[i]]
    chg.append(dict(d=ds[i], dL=w[0]-p[0], dS=w[1]-p[1],
                    dNet=(w[0]-w[1])-(p[0]-p[1]),
                    L=w[0], S=w[1], Net=w[0]-w[1], OI=w[2],
                    dLpct=(w[0]-p[0])/p[2]*100))
cur = chg[-1]; N = len(chg)
dl = [c['dL'] for c in chg]; dn = [c['dNet'] for c in chg]; dlp = [c['dLpct'] for c in chg]
print('\n样本 %d 周, %s -> %s' % (N, ds[1], ds[-1]))
print('\n== 本周 2026-09-01 定位 ==')
rank = sorted(dl, reverse=True).index(cur['dL']) + 1
print('多头单周 +%s   全样本分位 %.1f%%   #%d/%d' % (f"{cur['dL']:,}", pct(dl, cur['dL']), rank, N))
print('净头寸单周 %+s   分位 %.1f%%   #%d' % (f"{cur['dNet']:,}", pct(dn, cur['dNet']), sorted(dn, reverse=True).index(cur['dNet'])+1))
print('多头增量/OI(前周) %.2f%%   分位 %.1f%%   (均值 %.2f%% 中位 %.2f%%)' % (cur['dLpct'], pct(dlp, cur['dLpct']), sum(dlp)/N, sorted(dlp)[N//2]))
net = [c['Net'] for c in chg]; netoi = [c['Net']/c['OI']*100 for c in chg]
print('当前净头寸 %s   绝对分位 %.1f%% | 净/OI %.2f%% 分位 %.1f%%' % (f"{cur['Net']:,}", pct(net, cur['Net']), cur['Net']/cur['OI']*100, pct(netoi, cur['Net']/cur['OI']*100)))
print('\n== 多头单周增仓 top15 ==')
for c in sorted(chg, key=lambda x: -x['dL'])[:15]:
    print('  %s  +%s  (%+.2f%%OI)  净%+s' % (c['d'], f"{c['dL']:,}", c['dLpct'], f"{c['dNet']:,}"))
print('\n== 净头寸单周增幅 top15 ==')
for c in sorted(chg, key=lambda x: -x['dNet'])[:15]:
    print('  %s  净%+s  (多%+s 空%+s)' % (c['d'], f"{c['dNet']:,}", f"{c['dL']:,}", f"{c['dS']:,}"))
print('\n== 当前周 4 周/8 周累计 ==')
def cum(cs):
    r = agg[ds[cs[0]-1]]
    return agg[ds[cs[-1]]][0] - r[0], (agg[ds[cs[-1]]][0]-agg[ds[cs[-1]]][1]) - (r[0]-r[1])
for k in (4, 8, 12):
    if N >= k:
        dL, dNet = cum(list(range(N-k+1, N+1)))
        print('  近%d周: 多头%+s  净%+s' % (k, f"{dL:,}", f"{dNet:,}"))
def inwin(d):
    m, d2 = map(int, d.split('-')[1:])
    return (m == 8 and d2 >= 20) or (m == 9 and d2 <= 12)
seas = [c for c in chg if inwin(c['d'])]
print('\n同季窗口(8/20-9/12, n=%d) 多头单周增仓 本周 +%s -> 分位 %.1f%% ; 窗口内历史最大 +%s' % (len(seas), f"{cur['dL']:,}", pct([x['dL'] for x in seas], cur['dL']), f"{max(x['dL'] for x in seas):,}"))
for c in sorted(seas, key=lambda x: -x['dL'])[:6]:
    print('    %s  +%s' % (c['d'], f"{c['dL']:,}"))
