# -*- coding: utf-8 -*-
"""小麦非商净多暴增事件：持续性(retention) × 来源(多头/空头主导) × 后续价格"""
import json, csv, statistics

BASE = "C:/Users/Administrator/Desktop/stock"
d = json.load(open(BASE + "/results/cot/agri_cot_history_1995_2026.json", encoding="utf-8-sig"))
v = d["series"]["小麦 三合约合计"]
dates = v["dates"]; n = len(dates)

# 周线价格（TradingView, 周一标注）
tv = []
with open(BASE + "/data/wheat_zw_weekly_tradingview.csv", encoding="utf-8") as f:
    r = csv.reader(f); next(r)
    for row in r:
        if row[0] and row[4]:
            tv.append((row[0], float(row[4])))  # date, close
tv.sort(); tv_dates = [x[0] for x in tv]

def tv_idx(day, offset=0):
    """≥day 的第一根 TV bar 索引（预处理 offset 用）"""
    import bisect
    return bisect.bisect_left(tv_dates, day)

def fwd_ret(day, k):
    """从>=day 的 bar 收盘为基准，往后第 k 根 bar 收盘的收益率"""
    i = tv_idx(day)
    if i + k >= len(tv): return None
    return tv[i+k][1] / tv[i][1] - 1

def pre_ret(day, k=4):
    """day 之前 k 根 bar 的收益率（基准 = 更早一根）"""
    i = tv_idx(day)
    if i - k < 0: return None
    return tv[i][1] / tv[i-k][1] - 1

# 周变动序列
dnet = [(v["nc_l_chg"][i] or 0) - (v["nc_s_chg"][i] or 0) for i in range(1, n)]
dL = [v["nc_l_chg"][i] or 0 for i in range(1, n)]
dS = [v["nc_s_chg"][i] or 0 for i in range(1, n)]
net = [v["nc_net"][i] for i in range(1, n)]  # 对应 dates[1:]

def pct(a, q):
    b = sorted(a); return b[max(0, min(len(b)-1, int(len(b)*q)))]

# 2016+ 阈值
sel = [i for i in range(1, n) if dates[i] >= "2016-01-01"]
T_NET = pct([dnet[i-1] for i in sel], .90)

# 事件聚类（净多暴增）
evs = []; cur = None
for i in range(1, n):
    if dates[i] >= "2016-01-01" and dnet[i-1] >= T_NET:
        if cur is None or i - cur[1] > 4: cur = [i, i]; evs.append(cur)
        else: cur[1] = i

print(f"净多暴增事件(2016+,p90≥{T_NET:.0f}): {len(evs)} 个\n")
print(f"{'事件日':<12}{'Δnet':>9}{'Δ多头':>9}{'Δ空头':>9}{'多头贡献%':>9}{'前4周价':>9}{'+4周价':>8}{'+8周价':>8}{'+12周价':>8}{'4周后净多':>10}{'维持率':>7}")
rows = []
for ev in evs:
    i0 = ev[0]
    dt = dates[i0]
    dn = dnet[i0-1]; dl = dL[i0-1]; ds = dS[i0-1]
    shareL = dl / dn if dn > 0 else float("nan")
    pre = pre_ret(dt); f4 = fwd_ret(dt, 4); f8 = fwd_ret(dt, 8); f12 = fwd_ret(dt, 12)
    # 维持率：事件后第4周净多相对事件前净多的回吐
    net_before = net[i0-1] if i0 >= 1 else None
    if i0 + 4 < len(net):
        net_f4 = net[i0 + 3]  # 事件周+4周后（索引对齐：net[0]=dates[1]，net[i]对应dates[i+1]）
        # 修正索引
        net_f4 = net[i0] if i0 < len(net) else None
        net_t0 = net[i0-1]
        denom = net_t0 - net_before
        retention = (net_f4 - net_before) / denom if denom != 0 else float("nan")
    else:
        retention = float("nan")
    rows.append(dict(dt=dt, dn=dn, dl=dl, ds=ds, shareL=shareL, pre=pre, f4=f4, f8=f8, f12=f12, retention=retention, net_before=net_before, net_t0=net_t0))
    print(f"{dt:<12}{dn:>9,.0f}{dl:>9,.0f}{ds:>9,.0f}{shareL*100:>8.0f}%{pre*100:>8.1f}%{f4*100 if f4 is not None else float('nan'):>8.1f}%{f8*100 if f8 is not None else float('nan'):>8.1f}%{f12*100 if f12 is not None else float('nan'):>8.1f}%{net_before:>10,.0f}{retention*100 if retention==retention else float('nan'):>6.0f}%")
