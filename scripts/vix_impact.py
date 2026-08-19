#!/usr/bin/env python3
"""VIX 拉涨对 XLV/IBB/GILD/XBI 的影响分析。
1) 自动识别 VIX 局部低点→高点的显著拉升事件(2020-2026)
2) 每个事件窗口内 四标的 表现 + 见顶后 5/10/20 日修复
3) 全期统计: ΔVIX vs 标的日收益相关 / VIX上升日vs下降日 / VIX分位分桶
数据: data/vix/VIX, 1D.csv + data/<t>/*.csv (Yahoo 日线 adj_close)
"""
import os
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS = ["XLV", "IBB", "GILD", "XBI"]
NAMES = {"XLV": "医疗保健XLV", "IBB": "生物科技IBB", "GILD": "吉利德", "XBI": "小盘生物XBI"}

def load(t):
    df = pd.read_csv(os.path.join(ROOT, "data", t, f"{t}, 1D.csv"), parse_dates=["date"])
    return df[["date", "close", "adj_close"]].sort_values("date").reset_index(drop=True)

v = pd.read_csv(os.path.join(ROOT, "data", "vix", "VIX, 1D.csv"), parse_dates=["date"])
v = v[["date", "close"]].sort_values("date").reset_index(drop=True)
D = {t: load(t) for t in TICKERS}

def pct(a, b):
    return (b / a - 1) * 100

# ============ 1) 识别 VIX 拉升事件 ============
# 局部峰值: close>=24 且为前后2日最高
peaks = []
for i in range(2, len(v) - 2):
    if v.loc[i, "close"] >= 24 and v.loc[i, "close"] >= v.loc[i-2:i+3, "close"].max():
        peaks.append(i)

# 对每个峰值, 向前找前 30 交易日内的最低点
events = []
for pi in peaks:
    lo_idx = v.loc[max(0, pi - 30):pi, "close"].idxmin()
    vlo, vhi = v.loc[lo_idx, "close"], v.loc[pi, "close"]
    if (vhi - vlo) / vlo < 0.35:  # 至少 +35% 才算显著拉升
        continue
    # 与已有事件合并(峰值 120 交易日外才新建事件)
    if events and (v.loc[pi, "date"] - v.loc[events[-1][1], "date"]).days < 120:
        prev_lo, prev_pk = events[-1]
        prev_gain = (v.loc[prev_pk, "close"] - v.loc[prev_lo, "close"]) / v.loc[prev_lo, "close"]
        cur_gain = (vhi - vlo) / vlo
        if cur_gain > prev_gain * 1.15:
            events[-1] = (lo_idx, pi)
        continue
    events.append((lo_idx, pi))

print(f"识别到 {len(events)} 个显著 VIX 拉升事件:\n")
for k, (lo, pk) in enumerate(events):
    d_lo, d_pk = v.loc[lo, "date"], v.loc[pk, "date"]
    print(f"E{k+1}: {d_lo.strftime('%Y-%m-%d')}({v.loc[lo,'close']:.1f}) -> {d_pk.strftime('%Y-%m-%d')}({v.loc[pk,'close']:.1f})  +{pct(v.loc[lo,'close'], v.loc[pk,'close']):.0f}%")

# ============ 2) 事件窗口内 标的 表现 ============
print("\n===== 事件窗口: VIX 低点->高点 期间 标的涨跌 =====")
rows = []
for k, (lo, pk) in enumerate(events):
    d_lo, d_pk = v.loc[lo, "date"], v.loc[pk, "date"]
    line = f"E{k+1} VIX {v.loc[lo,'close']:.1f}->{v.loc[pk,'close']:.1f} (+{pct(v.loc[lo,'close'], v.loc[pk,'close']):.0f}%): "
    ev = {"ev": f"E{k+1}", "win": f"{d_lo.strftime('%y-%m-%d')}~{d_pk.strftime('%y-%m-%d')}", "vix": pct(v.loc[lo,'close'], v.loc[pk,'close'])}
    for t in TICKERS:
        d = D[t]
        sub = d[(d["date"] >= d_lo) & (d["date"] <= d_pk)]
        if len(sub) >= 3:
            r = pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"])
            ev[t] = r
            line += f"{t} {r:+.1f}%  "
    rows.append(ev)
    print(line)

# ============ 3) 见顶后 5/10/20 日修复 ============
print("\n===== VIX 见顶后 标的 N 日表现 (平均) =====")
import collections
fwd = collections.defaultdict(list)  # (t, n) -> [ret]
fwd_detail = collections.defaultdict(list)
for k, (lo, pk) in enumerate(events):
    d_pk = v.loc[pk, "date"]
    for t in TICKERS:
        d = D[t].reset_index(drop=True)
        m = d[d["date"] == d_pk]
        if not len(m):
            continue
        i = m.index[0]
        for n in [5, 10, 20]:
            if i + n < len(d):
                r = pct(d.loc[i, "adj_close"], d.loc[i + n, "adj_close"])
                fwd[(t, n)].append(r)
                fwd_detail[(t, n)].append((f"E{k+1}", r))
print(f"{'标的':<8} {'5日':>8} {'10日':>8} {'20日':>8}  (均值%, 样本数)")
for t in TICKERS:
    line = f"{t:<8}"
    for n in [5, 10, 20]:
        a = np.array(fwd[(t, n)])
        line += f" {np.mean(a):+7.1f}% (n={len(a)})"
    print(line)

# ============ 4) 全期相关: ΔVIX vs 标的日收益 ============
print("\n===== 全期: ΔVIX(日涨幅) vs 标的日收益 Pearson =====")
v["dvix"] = v["close"].pct_change() * 100
merged = v[["date", "dvix"]].merge(
    pd.concat([D[t].set_index("date")["adj_close"].pct_change() * 100 for t in TICKERS], axis=1).rename(columns={0: "x"}) if False else D[TICKERS[0]][["date"]],
    on="date", how="left")
ret_df = pd.DataFrame({"date": v["date"]})
for t in TICKERS:
    m = D[t].set_index("date")["adj_close"].pct_change() * 100
    ret_df[t] = ret_df["date"].map(m)
full = ret_df.merge(v[["date", "dvix"]], on="date").dropna()
for t in TICKERS:
    c = full["dvix"].corr(full[t])
    print(f"ΔVIX vs {t}: {c:+.3f} (n={len(full)})")

# 分年
print("\n--- 分年相关 ---")
full["year"] = full["date"].dt.year
for y in sorted(full["year"].unique()):
    sub = full[full["year"] == y]
    if len(sub) < 50: continue
    cs = " ".join(f"{t} {sub['dvix'].corr(sub[t]):+.2f}" for t in TICKERS)
    print(f"{y}: {cs}")

# ============ 5) VIX 上升日 vs 下降日 ============
print("\n===== VIX 上涨日 vs 下跌日: 标的平均日收益 =====")
up = full[full["dvix"] > 0]
dn = full[full["dvix"] < 0]
for t in TICKERS:
    print(f"{t}: VIX涨日 {up[t].mean():+.3f}% (n={len(up)}) | VIX跌日 {dn[t].mean():+.3f}% (n={len(dn)}) | 差 {up[t].mean()-dn[t].mean():+.3f}%")

# ============ 6) VIX 分位分桶 ============
print("\n===== VIX 水平分桶: 标的当日收益均值 =====")
v2 = v.rename(columns={"close": "vix_c"})
buckets = [(0, 15, "VIX<15"), (15, 20, "15-20"), (20, 30, "20-30"), (30, 999, ">30")]
for lo, hi, name in buckets:
    sub_dates = v2[(v2["vix_c"] >= lo) & (v2["vix_c"] < hi)]["date"]
    line = f"{name:<8}: "
    for t in TICKERS:
        m = full[full["date"].isin(sub_dates)]
        line += f"{t} {m[t].mean():+.3f}%  "
    print(line)

# ============ 7) 事件汇总保存 ============
ev_out = []
for k, (lo, pk) in enumerate(events):
    d_lo, d_pk = v.loc[lo, "date"], v.loc[pk, "date"]
    e = {
        "event": f"E{k+1}",
        "start": d_lo.strftime("%Y-%m-%d"), "end": d_pk.strftime("%Y-%m-%d"),
        "vix_start": round(v.loc[lo, "close"], 1), "vix_peak": round(v.loc[pk, "close"], 1),
        "vix_chg": round(pct(v.loc[lo, "close"], v.loc[pk, "close"]), 1),
    }
    for t in TICKERS:
        sub = D[t][(D[t]["date"] >= d_lo) & (D[t]["date"] <= d_pk)]
        e[t] = round(pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"]), 1) if len(sub) >= 3 else None
        e[t + "_fwd10"] = None
    ev_out.append(e)
with open(os.path.join(ROOT, "results", "vix_impact.json"), "w", encoding="utf-8") as f:
    import json
    json.dump({"events": ev_out, "corr_all": {t: round(full["dvix"].corr(full[t]), 3) for t in TICKERS},
               "fwd_mean": {f"{t}_{n}": round(float(np.mean(fwd[(t, n)])), 2) for t in TICKERS for n in [5, 10, 20]}},
              f, ensure_ascii=False, indent=1)
print("\nsaved: results/vix_impact.json")
