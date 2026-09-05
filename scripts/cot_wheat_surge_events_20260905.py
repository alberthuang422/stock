# -*- coding: utf-8 -*-
"""
小麦非商业头寸"暴增"事件研究 — 完整分析
数据：CFTC COT futures-only legacy 1995-2026（results/cot/agri_cot_history_1995_2026.json）
价格：TradingView CBOT 小麦主力连续周线 1977-2026（data/wheat_zw_weekly_tradingview.csv）

主口径：小麦三合约合计（SRW+HRW+HRS），2016+ 真实价格段
定义：Δ净多 / Δ多头 / Δ空头 周变动超 2016+ p90（空头为 p10）为触发周，间隔>4 周聚类为独立事件
三因子：来源(多头主导≥50% vs 空头主导<50%) × 位置(事件前4周收益) × 持续性(cluster 长度 & 4周保留率)
输出：results/cot/wheat_surge_events_20260905.json / .csv  +  wheat_surge_stats_20260905.json
"""
import json, csv, bisect, statistics, math, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "results", "cot")
os.makedirs(OUT, exist_ok=True)

WINDOWS = [1, 2, 4, 8, 12]
P90_FROM = "2016-01-01"   # 阈值样本起点（真实价格段）
CLUSTER_GAP = 4           # 周
SIGN = 50000              # bootstrap 抽样次数

def pct(a, q):
    b = sorted(a)
    return b[max(0, min(len(b)-1, int(len(b)*q)))]

def mean(x):
    x = [v for v in x if v is not None]
    return statistics.mean(x) if x else float('nan')

def sem(x):
    x = [v for v in x if v is not None]
    if len(x) < 2: return float('nan')
    return statistics.stdev(x) / math.sqrt(len(x))

def ttest1(x):
    """单样本 t vs 0"""
    x = [v for v in x if v is not None]
    if len(x) < 2: return float('nan'), len(x)
    m = statistics.mean(x); s = statistics.stdev(x)
    se = s / math.sqrt(len(x))
    if se == 0: return (0.0 if m == 0 else float('nan')), len(x)
    t = m / se
    # 双侧 p，学生 t 近似
    df = len(x) - 1
    import math as _m
    # 用正态近似做 bootstrap 级别的检验即可，这里给双侧正态 p
    from scipy import stats as _s
    try:
        p = 2 * _s.t.sf(_m.fabs(t), df)
    except Exception:
        p = 2 * (1 - 0.5 * (1 + math.erf(_m.fabs(t) / _m.sqrt(2))))
    return p, len(x)

def sign_test(x):
    """符号检验：正收益比例 vs 50%"""
    x = [v for v in x if v is not None and v != 0]
    if len(x) < 3: return float('nan'), float('nan'), len(x)
    pos = sum(1 for v in x if v > 0)
    n = len(x)
    p = 2 * min((sum(math.comb(n, k) * 0.5**n for k in range(pos, n+1))),
                (sum(math.comb(n, k) * 0.5**n for k in range(0, pos+1))))
    return pos / n, p, n

# ---------- 载入持仓 ----------
d = json.load(open(os.path.join(BASE, "results", "cot", "agri_cot_history_1995_2026.json"), encoding="utf-8-sig"))
series = d["series"]

MARKETS = ["小麦 三合约合计", "小麦 SRW (CBOT)", "小麦 HRW (KCBT→CBOT)", "小麦 HRS (MGE→MIAX)"]

def load_tv():
    tv = []
    with open(os.path.join(BASE, "data", "wheat_zw_weekly_tradingview.csv"), encoding="utf-8") as f:
        r = csv.reader(f); next(r)
        for row in r:
            if row[0] and row[4]:
                tv.append((row[0], float(row[4])))
    tv.sort()
    return [x[0] for x in tv], tv

TV_DATES, TV = load_tv()

def tv_i(day):
    i = bisect.bisect_left(TV_DATES, day)
    return i if i < len(TV) else None

def fwd(day, k):
    i = tv_i(day)
    if i is None or i + k >= len(TV): return None
    return TV[i+k][1] / TV[i][1] - 1

def pre(day, k=4):
    i = tv_i(day)
    if i is None or i - k < 0: return None
    return TV[i][1] / TV[i-k][1] - 1

# ---------- 事件检测 ----------
def detect(mkt_name):
    v = series[mkt_name]
    dates = v["dates"]; n = len(dates)
    dnet = [(v["nc_l_chg"][i] or 0) - (v["nc_s_chg"][i] or 0) for i in range(1, n)]
    dL = [v["nc_l_chg"][i] or 0 for i in range(1, n)]
    dS = [v["nc_s_chg"][i] or 0 for i in range(1, n)]
    # 阈值样本
    sel = [i for i in range(1, n) if dates[i] >= P90_FROM]
    Tnet = pct([dnet[i-1] for i in sel], .90)
    Tlong = pct([dL[i-1] for i in sel], .90)
    Tshort = pct([dS[i-1] for i in sel], .10)
    # 三类事件
    all_ev = {}
    for key, cond in [
        ("net_surge", lambda i: dnet[i-1] >= Tnet),
        ("long_surge", lambda i: dL[i-1] >= Tlong),
        ("short_cover", lambda i: dS[i-1] <= Tshort),
    ]:
        evs = []; cur = None
        for i in range(1, n):
            if dates[i] >= P90_FROM and cond(i):
                if cur is None or i - cur[1] > CLUSTER_GAP:
                    cur = [i, i]; evs.append(cur)
                else:
                    cur[1] = i
        all_ev[key] = (evs, Tnet if key == "net_surge" else (Tlong if key == "long_surge" else Tshort))
    return dates, v, (dnet, dL, dS), all_ev

def compute_events(mkt_name):
    dates, v, (dnet, dL, dS), ev_map = detect(mkt_name)
    net = v["nc_net"]
    # dL/dS 对应 dates[1:]（dL[i] = dates[i+1] 的变动）；事件周 i 的变动 = dL[i-1]
    out = []
    for etype, (evs, thr) in ev_map.items():
        for ev in evs:
            I = list(range(ev[0], ev[1]+1))
            dt = dates[ev[0]]
            dl = sum(dL[i-1] or 0 for i in I); ds = sum(dS[i-1] or 0 for i in I)
            dn = dl - ds
            shareL = dl/dn if dn > 0 else float('nan')
            clen = len(I)
            i0 = ev[0]
            if i0 + 4 < len(net):
                inc = net[i0] - net[i0-1]
                ret4 = (net[i0+4] - net[i0-1]) / inc if inc != 0 else float('nan')
            else:
                ret4 = float('nan')
            rec = dict(market=mkt_name, type=etype, date=dt, dnet=dn, dlong=dl, dshort=ds,
                       share_long=shareL, cluster_len=clen, retention_4w=ret4,
                       pre4=pre(dt, 4), pre8=pre(dt, 8),
                       net_after=net[i0] if i0 < len(net) else None)
            for w in WINDOWS:
                rec[f"fwd{w}"] = fwd(dt, w)
            out.append(rec)
    return out

all_recs = []
for m in MARKETS:
    all_recs += compute_events(m)

# 2016+ 且价格样本内（有 pre4 用于分组）
price_recs = [r for r in all_recs if r["pre4"] is not None]
net_recs = [r for r in price_recs if r["type"] == "net_surge" and r["market"] == "小麦 三合约合计"]

# 基线：2016+ 全样本（非事件）同窗口收益
base_dates = [x[0] for x in TV if x[0] >= P90_FROM]
base_rec = {}
for w in WINDOWS:
    rets = []
    for i in range(len(TV) - w):
        if TV[i][0] >= P90_FROM:
            rets.append(TV[i+w][1] / TV[i][1] - 1)
    base_rec[f"fwd{w}"] = rets

# ---------- 输出 ----------
def stats_block(recs, label):
    blk = {"label": label, "n": len(recs)}
    for w in WINDOWS:
        vals = [r[f"fwd{w}"] for r in recs if r.get(f"fwd{w}") is not None]
        if vals:
            m = statistics.mean(vals)
            med = statistics.median(vals)
            se = statistics.stdev(vals)/math.sqrt(len(vals)) if len(vals) > 1 else float('nan')
            pos = sum(1 for v in vals if v > 0)/len(vals)
            blk[f"fwd{w}"] = {"n": len(vals), "mean": m, "median": med, "se": se, "pos": pos}
            # 相对基线
            base = base_rec[f"fwd{w}"]
            if base:
                # 均值差 + 池化 t
                m2 = statistics.mean(base); s2 = statistics.stdev(base); n2 = len(base)
                sp = math.sqrt(((len(vals)-1)*statistics.stdev(vals)**2 + (n2-1)*s2**2) / (len(vals)+n2-2)) if len(vals)+n2-2 > 0 else float('nan')
                blk[f"fwd{w}"]["excess"] = m - m2
                blk[f"fwd{w}"]["excess_t"] = (m - m2) / (sp*math.sqrt(1/len(vals)+1/n2)) if sp and sp == sp else float('nan')
                blk[f"fwd{w}"]["base_mean"] = m2
                # 符号检验 vs 基线正频
                blk[f"fwd{w}"]["base_pos"] = statistics.mean(1 for _ in base) if False else sum(1 for v in base if v > 0)/n2
        else:
            blk[f"fwd{w}"] = {"n": 0}
    return blk

# 分组统计
groups = {}
def add_group(key, recs, label):
    groups[key] = stats_block(recs, label)

add_group("all_net", net_recs, "全部净多暴增（合计）")
add_group("net_multi", [r for r in net_recs if r["share_long"] >= 0.5], "净多暴增·多头主导≥50%")
add_group("net_cover", [r for r in net_recs if r["share_long"] < 0.5], "净多暴增·空头主导<50%")
add_group("net_start", [r for r in net_recs if r["pre4"] <= 0], "净多暴增·启动型(前4周≤0%)")
add_group("net_chase", [r for r in net_recs if r["pre4"] >= 0.05], "净多暴增·追涨型(前4周≥5%)")
add_group("net_keep", [r for r in net_recs if r["retention_4w"] == r["retention_4w"] and r["retention_4w"] >= 0.5], "净多暴增·4周保留≥50%")
add_group("net_revert", [r for r in net_recs if r["retention_4w"] == r["retention_4w"] and r["retention_4w"] < 0.5], "净多暴增·4周保留<50%")
add_group("long_surge_all", [r for r in price_recs if r["type"] == "long_surge" and r["market"] == "小麦 三合约合计"], "多头加仓全部")
add_group("short_cover_all", [r for r in price_recs if r["type"] == "short_cover" and r["market"] == "小麦 三合约合计"], "空头砍仓全部")

# 基线段本身
base_stats = {f"fwd{w}": {"n": len(base_rec[f"fwd{w}"]), "mean": statistics.mean(base_rec[f"fwd{w}"]),
                          "median": statistics.median(base_rec[f"fwd{w}"]),
                          "pos": sum(1 for v in base_rec[f"fwd{w}"] if v > 0)/len(base_rec[f"fwd{w}"])} for w in WINDOWS}

# 事件明细 CSV / JSON
out_json = dict(
    asof="2026-09-05", generated="2026-09-05T23:53+08:00",
    p90_from=P90_FROM, cluster_gap=CLUSTER_GAP, windows=WINDOWS,
    thresholds={m: detect(m)[3] for m in MARKETS},   # (evs, thr) 太大，剥离
    events=all_recs,
    groups=groups,
    base=base_stats,
    notes=[
        "事件：Δ净多/Δ多头≥2016+p90、Δ空头≤2016+p10，间隔≤4周聚类",
        "价格：TradingView CBOT 小麦主力连续周线（美分/蒲式耳），2016+ 为真实价格段",
        "未来收益 fwdW = 事件日(报告日周二)之后第W根周线收盘相对事件日收盘的涨跌",
        "excess = 事件组均值 − 2016+ 同期全样本均值；excess_t = 池化 t 值",
    ],
)
# 阈值单独存
thr_out = {}
for m in MARKETS:
    dates, v, (dnet, dL, dS), ev_map = detect(m)
    sel = [i for i in range(1, len(dates)) if dates[i] >= P90_FROM]
    thr_out[m] = {
        "T_net_p90": pct([dnet[i-1] for i in sel], .90),
        "T_long_p90": pct([dL[i-1] for i in sel], .90),
        "T_short_p10": pct([dS[i-1] for i in sel], .10),
    }
out_json["thresholds_summary"] = thr_out
out_json.pop("thresholds", None)

with open(os.path.join(OUT, "wheat_surge_events_20260905.json"), "w", encoding="utf-8") as f:
    json.dump(out_json, f, ensure_ascii=False, indent=1, default=str)

# CSV（事件明细）
with open(os.path.join(OUT, "wheat_surge_events_20260905.csv"), "w", encoding="utf-8", newline="") as f:
    cols = ["market", "type", "date", "dnet", "dlong", "dshort", "share_long", "cluster_len",
            "retention_4w", "pre4", "pre8", "net_after"] + [f"fwd{w}" for w in WINDOWS]
    wtr = csv.DictWriter(f, fieldnames=cols)
    wtr.writeheader()
    for r in all_recs:
        wtr.writerow({k: ("" if r.get(k) is None else (round(r[k], 4) if isinstance(r[k], float) else r[k])) for k in cols})

# 分组统计 CSV
with open(os.path.join(OUT, "wheat_surge_stats_20260905.csv"), "w", encoding="utf-8", newline="") as f:
    hdr = ["group", "n"]
    for w in WINDOWS:
        hdr += [f"fwd{w}_mean", f"fwd{w}_med", f"fwd{w}_pos", f"fwd{w}_excess", f"fwd{w}_t"]
    wtr = csv.writer(f); wtr.writerow(hdr)
    for k, g in groups.items():
        row = [k, g["n"]]
        for w in WINDOWS:
            s = g[f"fwd{w}"]
            row += [s.get("mean"), s.get("median"), s.get("pos"), s.get("excess"), s.get("excess_t")]
        wtr.writerow(row)
    # 基线行
    brow = ["base_2016plus", base_stats["fwd1"]["n"]]
    for w in WINDOWS:
        s = base_stats[f"fwd{w}"]
        brow += [s["mean"], s["median"], s["pos"], 0, 0]
    wtr.writerow(brow)

# 控制台摘要
print("=== 事件数（2016+ 价格样本内） ===")
for etype, nm in [("net_surge", "净多暴增"), ("long_surge", "多头加仓"), ("short_cover", "空头砍仓")]:
    cnt = len([r for r in price_recs if r["type"] == etype and r["market"] == "小麦 三合约合计"])
    print(f"  {nm}: {cnt}")
print("\n=== 小麦三合约合计·净多暴增 分组统计 ===")
for k in ["all_net", "net_multi", "net_cover", "net_start", "net_chase", "net_keep", "net_revert"]:
    g = groups[k]
    f4 = g["fwd4"]; f12 = g["fwd12"]
    print(f"  {g['label']:28s} n={g['n']:3d}  +4周 {f4['mean']*100:6.1f}% (t={f4['excess_t']:+.2f})  +12周 {f12['mean']*100:6.1f}% (t={f12['excess_t']:+.2f})")
print("\n基线 2016+ 全样本周收益均值：", {w: f"{base_stats[f'fwd{w}']['mean']*100:.2f}%" for w in WINDOWS})
print("\n已输出 results/cot/wheat_surge_events_20260905.json/.csv, wheat_surge_stats_20260905.csv")