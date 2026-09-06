# -*- coding: utf-8 -*-
"""小麦非商净多暴增事件：来源(多头/空头主导) × 持续性(保留率/cluster) × 后续价格 — 干净版"""
import json, csv, bisect, statistics

BASE = "C:/Users/Administrator/Desktop/stock"
d = json.load(open(BASE + "/results/cot/agri_cot_history_1995_2026.json", encoding="utf-8-sig"))
v = d["series"]["小麦 三合约合计"]
dates = v["dates"]; n = len(dates)
net = v["nc_net"]; dL = v["nc_l_chg"]; dS = v["nc_s_chg"]; dnL_o = []
dnet = [(dL[i] or 0) - (dS[i] or 0) for i in range(n)]  # 注意 dnet[i] 对应 dates[i]（第 i 周变动）

# TradingView 周线
tv = []
with open(BASE + "/data/wheat_zw_weekly_tradingview.csv", encoding="utf-8") as f:
    r = csv.reader(f); next(r)
    for row in r:
        if row[0] and row[4]: tv.append((row[0], float(row[4])))
tv.sort(); tv_dates = [x[0] for x in tv]

def tv_i(day):
    i = bisect.bisect_left(tv_dates, day)
    return i if i < len(tv) else None

def fwd(day, k):
    i = tv_i(day)
    if i is None or i + k >= len(tv): return None
    return tv[i+k][1] / tv[i][1] - 1

def pre4(day):
    i = tv_i(day)
    if i is None or i - 4 < 0: return None
    return tv[i][1] / tv[i-4][1] - 1

def pct(a, q):
    b = sorted(a); return b[int(len(b)*q)]

sel = [i for i in range(1, n) if dates[i] >= "2016-01-01"]
T = pct([dnet[i] for i in sel], .90)

# 聚类事件
evs = []; cur = None
for i in range(1, n):
    if dates[i] >= "2016-01-01" and dnet[i] >= T:
        if cur is None or i - cur[1] > 4: cur = [i, i]; evs.append(cur)
        else: cur[1] = i

print(f"净多暴增事件 p90(≥{T:,.0f}) 2016+: {len(evs)} 个\n")
recs = []
for ev in evs:
    I = list(range(ev[0], ev[1]+1))  # 触发周
    dt = dates[ev[0]]
    dl = sum(dL[i] or 0 for i in I); ds = sum(dS[i] or 0 for i in I)
    dn = dl - ds
    shareL = dl/dn if dn > 0 else float('nan')
    # 持续性1: cluster 长度（触发周数）
    clen = len(I)
    # 持续性2: 事件净多增量在 +4 周后的保留率
    i0 = ev[0]
    if i0 + 4 < n:
        inc = net[i0] - net[i0-1]
        ret4 = (net[i0+4] - net[i0-1]) / inc if inc != 0 else float('nan')
    else: ret4 = float('nan')
    recs.append(dict(dt=dt, dn=dn, dl=dl, ds=ds, shareL=shareL, clen=clen, ret4=ret4,
                     pre4=pre4(dt), f4=fwd(dt,4), f8=fwd(dt,8), f12=fwd(dt,12)))

# 输出全表
print(f"{'事件日':<11}{'Δnet':>9}{'Δ多头':>9}{'Δ空头':>9}{'多头占比':>8}{'cluster':>8}{'保留率4w':>9}{'前4周价':>8}{'+4周价':>8}{'+8周价':>8}{'+12周价':>8}")
for r in recs:
    f = lambda x: f"{x*100:7.1f}%" if x is not None else "     --"
    print(f"{r['dt']:<11}{r['dn']:>9,.0f}{r['dl']:>9,.0f}{r['ds']:>9,.0f}{r['shareL']*100:>7.0f}%{r['clen']:>8}{f'{(r['ret4']*100 if r['ret4']==r['ret4'] else float('nan')):>7.0f}%' if r['ret4']==r['ret4'] else '     --':>9}{f(r['pre4']):>8}{f(r['f4']):>8}{f(r['f8']):>8}{f(r['f12']):>8}")

# 分组统计：来源
def grp_mean(rs, key):
    vals = [r[key] for r in rs if r[key] is not None]
    return (statistics.mean(vals), len(vals)) if vals else (float('nan'), 0)

print("\n===== 按来源分组（多头主导 shareL≥50% vs 空头主导 <50%）=====")
multi = [r for r in recs if r['shareL'] >= 0.5]
short = [r for r in recs if r['shareL'] < 0.5]
for nm, g in [("多头主导(主动做多≥50%)", multi), ("空头主导(砍仓贡献>50%)", short)]:
    m4, n4 = grp_mean(g, 'f4'); m8, n8 = grp_mean(g, 'f8'); m12, n12 = grp_mean(g, 'f12')
    mp, np_ = grp_mean(g, 'pre4')
    print(f"{nm}: n={len(g)}  前4周价 {mp*100:+.1f}%  |  +4周 {m4*100:+.1f}%  +8周 {m8*100:+.1f}%  +12周 {m12*100:+.1f}%")

print("\n===== 按持续性分组（保留率4周 ≥50% = 维持住 vs <50% = 回吐）=====")
keep = [r for r in recs if r['ret4'] == r['ret4'] and r['ret4'] >= 0.5]
revert = [r for r in recs if r['ret4'] == r['ret4'] and r['ret4'] < 0.5]
for nm, g in [("维持住(保留≥50%)", keep), ("回吐(保留<50%)", revert)]:
    m4, n4 = grp_mean(g, 'f4'); m8, n8 = grp_mean(g, 'f8'); m12, n12 = grp_mean(g, 'f12')
    mp, np_ = grp_mean(g, 'pre4')
    print(f"{nm}: n={len(g)}  前4周价 {mp*100:+.1f}%  |  +4周 {m4*100:+.1f}%  +8周 {m8*100:+.1f}%  +12周 {m12*100:+.1f}%")

print("\n===== 2×2：来源 × 持续性 → +12周均值 =====")
for nm, g in [("多头主导", multi), ("空头主导", short)]:
    gk = [r for r in g if r['ret4']==r['ret4'] and r['ret4']>=0.5]
    gr = [r for r in g if r['ret4']==r['ret4'] and r['ret4']<0.5]
    m12k,_ = grp_mean(gk,'f12'); m12r,_ = grp_mean(gr,'f12')
    print(f"  {nm}: 维持住 n={len(gk)} → +12周 {m12k*100:+.1f}%  |  回吐 n={len(gr)} → +12周 {m12r*100:+.1f}%")

print("\n===== 按事件前价格（启动型 ≤0 / 追涨型 >5%）=====")
start = [r for r in recs if r['pre4'] is not None and r['pre4'] <= 0]
chase = [r for r in recs if r['pre4'] is not None and r['pre4'] >= 0.05]
mid = [r for r in recs if r['pre4'] is not None and 0 < r['pre4'] < 0.05]
for nm, g in [("启动型(前4周≤0%)", start), ("中性(0~5%)", mid), ("追涨型(前4周≥5%)", chase)]:
    m4,_ = grp_mean(g,'f4'); m8,_ = grp_mean(g,'f8'); m12,_ = grp_mean(g,'f12')
    print(f"  {nm}: n={len(g)}  |  +4周 {m4*100:+.1f}%  +8周 {m8*100:+.1f}%  +12周 {m12*100:+.1f}%")
