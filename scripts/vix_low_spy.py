#!/usr/bin/env python3
"""VIX 低位 → SPY 后续行情 + VIX 低位持续时长事件研究。

核心问题(对标旧 vix_low_spx.py 口径, 标的从 ^GSPC 换成 SPY ETF):
Q1: VIX 处于低位时, SPY 后续行情如何 (vs 全期基线)?
Q2: VIX 低位能维持多久? (区间长度分布 + 条件剩余寿命 + 回归速度)

口径:
- 数据: data/vix/VIX, 1D.csv + data/spy/SPY, 1D.csv (1995-01-03 ~ 2026-08-20, 内对齐)
- VIX 低位阈值: 15(低) / 13(极低) / 12(罕见极低)
- 事件 = 任意满足 VIX 收盘 < 阈值的交易日 (重叠样本, 与旧报告 by_day 口径一致);
  另按"连续低位区间起点"独立样本复核
- 前瞻收益: 事件日(VIX 低位日)收盘买入, 持有 N 个交易日(交易日对齐)后收盘卖出; 不计成本
- 基线: 全期所有可交易日前瞻收益
- 显著性: 事件收益 vs 基线收益 双样本 Welch t (Python 手工实现, 无 scipy)

输出: results/vix_low_spy.json + results/vix_low_spy_events.csv(全部 VIX<15 低位日事件)
"""
import os, json, math
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def pct(a, b):
    return (b / a - 1) * 100

def clean(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if math.isnan(v) else round(float(v), 4)
    return v

def clean_all(o):
    if isinstance(o, dict):
        return {k: clean_all(v) for k, v in o.items() if v is not None}
    if isinstance(o, list):
        return [clean_all(v) for v in o]
    return clean(o)

# ---------- 1. 加载 ----------
v = pd.read_csv(os.path.join(ROOT, "data", "vix", "VIX, 1D.csv"), parse_dates=["date"])
s = pd.read_csv(os.path.join(ROOT, "data", "spy", "SPY, 1D.csv"), parse_dates=["date"])
m = v.merge(s, on="date", suffixes=("_vix", "_spy"))[["date", "close_vix", "close_spy"]]
m = m.sort_values("date").reset_index(drop=True)
print(f"合并样本: {len(m)} 交易日, {m.date.iloc[0].date()} ~ {m.date.iloc[-1].date()}")

vix = m["close_vix"].astype(float).values
spy = m["close_spy"].astype(float).values
dates = m["date"].values
n = len(m)

# ---------- 2. 当前状态定位 ----------
cur_vix = float(vix[-1])
cur_spy = float(spy[-1])
cur_pctile = (vix < cur_vix).mean() * 100
spy_hist_high = float(spy.max())
spy_drawdown_from_high = pct(spy_hist_high, cur_spy)

run15 = 0
for i in range(n - 1, -1, -1):
    if vix[i] < 15:
        run15 += 1
    else:
        break

# ---------- 3. 前瞻收益 ----------
THRESHOLDS = [15, 13, 12]
FWDS = [5, 10, 20, 60, 120]

def stats(arr):
    a = np.asarray(arr, dtype=float)
    if len(a) == 0:
        return None
    se = float(a.std(ddof=1) / math.sqrt(len(a)))
    return {
        "n": int(len(a)),
        "mean": round(float(a.mean()), 2),
        "median": round(float(np.median(a)), 2),
        "win": round(float((a > 0).mean()) * 100, 1),
        "p25": round(float(np.percentile(a, 25)), 2),
        "worst": round(float(a.min()), 2),
        "best": round(float(a.max()), 2),
        "se": round(se, 2),
        "t": round(float(a.mean() / se), 2) if se > 0 else None,
    }

# 前瞻收益矩阵
fwd = {k: np.full(n, np.nan) for k in FWDS}
for k in FWDS:
    fwd[k][: n - k] = np.array([pct(spy[i], spy[i + k]) for i in range(n - k)])

# 基线
base = {f"T{k}": stats(fwd[k][: n - k]) for k in FWDS}

# 事件 = 任意低位日
events = {}
for th in THRESHOLDS:
    idxs = np.where(vix < th)[0]
    events[th] = {int(i): {f"T{k}": round(float(fwd[k][i]), 4) for k in FWDS if not math.isnan(fwd[k][i])} for i in idxs}

by_day = {}
for th in THRESHOLDS:
    by_day[th] = {}
    for k in FWDS:
        vals = [events[th][i][f"T{k}"] for i in events[th] if f"T{k}" in events[th][i]]
        by_day[th][f"T{k}"] = stats(vals)

# 独立样本: 连续低位区间起点入场
starts = {}
for th in THRESHOLDS:
    mask = vix < th
    starts[th] = [int(i) for i in np.where(mask & ~np.roll(mask, 1))[0]]

by_start = {}
for th in THRESHOLDS:
    by_start[th] = {}
    for k in FWDS:
        vals = [pct(spy[i], spy[i + k]) for i in starts[th] if i + k < n]
        by_start[th][f"T{k}"] = stats(vals)

# ---------- 4. 低位持续时长 ----------
def find_runs(th):
    mask = vix < th
    runs = []
    i = 0
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            runs.append((i, j, j - i + 1))
            i = j + 1
        else:
            i += 1
    return runs

run_stats = {}
run_detail = {}
for th in THRESHOLDS:
    runs = find_runs(th)
    lens = np.array([r[2] for r in runs])
    run_stats[th] = {
        "n_runs": int(len(runs)),
        "len_mean": round(float(lens.mean()), 1),
        "len_median": int(np.median(lens)),
        "len_p75": int(np.percentile(lens, 75)),
        "len_p90": int(np.percentile(lens, 90)),
        "len_max": int(lens.max()),
        "pct_time": round(float((vix < th).mean()) * 100, 1),
    }
    run_detail[th] = [{
        "start": str(pd.Timestamp(dates[i]).date()), "end": str(pd.Timestamp(dates[j]).date()),
        "days": int(r), "vix_start": round(float(vix[i]), 2), "vix_end": round(float(vix[j]), 2),
        "spy_chg": round(float(pct(spy[i], spy[j])), 1),
        "spy_fwd20": round(float(pct(spy[j], spy[j + 20])), 1) if j + 20 < n else None,
        "spy_fwd60": round(float(pct(spy[j], spy[j + 60])), 1) if j + 60 < n else None,
    } for i, j, r in runs]

# ---------- 5. 条件剩余寿命 ----------
def cond_lifetable(th, Ds, Ks):
    runs = find_runs(th)
    tab = {}
    for D in Ds:
        row = {}
        for K in Ks:
            surv = np.array([(r[2] - D + 1) >= K for r in runs if r[2] >= D], dtype=float)
            row[K] = round(float(surv.mean()) * 100, 1) if len(surv) else None
        tab[D] = row
    return tab

life_tab_15 = cond_lifetable(15, [1, 3, 5, 10, 20, 40], [3, 5, 10, 20, 40, 60])
life_tab_13 = cond_lifetable(13, [1, 3, 5, 10, 20, 40], [3, 5, 10, 20, 40, 60])

# ---------- 6. 低位结束后回归到 VIX>=20 ----------
def days_to_break_20(starts_):
    out = []
    for s in starts_:
        target = None
        for j in range(s, n):
            if vix[j] >= 20:
                target = j - s + 1
                break
        if target:
            out.append(target)
    return out

break_to20 = {}
for th in THRESHOLDS:
    b20 = days_to_break_20(starts[th])
    break_to20[th] = stats(b20) if b20 else None

# ---------- 7. 高波动→低波动场景: VIX 低位起点 + SPY 距 250 日高点 5% 以内 ----------
high_scen = {}
for th in THRESHOLDS:
    rows = []
    for s in starts[th]:
        if s < 250:
            continue
        hi250 = spy[max(0, s - 250):s].max()
        dd = pct(hi250, spy[s])
        if dd > -5:
            rec = {"start": str(pd.Timestamp(dates[s]).date()), "vix": round(float(vix[s]), 2),
                   "spy_drawdown_from_high": round(float(dd), 1)}
            for k in FWDS:
                if s + k < n:
                    rec[f"fwd{k}"] = round(float(pct(spy[s], spy[s + k])), 2)
            rows.append(rec)
    if rows:
        agg = {f"T{k}": stats([r[f"fwd{k}"] for r in rows if f"fwd{k}" in r]) for k in FWDS}
        high_scen[th] = {"n": len(rows), "agg": agg, "detail": rows}
    else:
        high_scen[th] = None

# ---------- 8. 显著性(低位日 vs 非低位日 互斥对照)与近 12 个月摘要 ----------
sig = {}
for th in THRESHOLDS:
    sig[th] = {}
    mask_ev = vix < th
    for k in FWDS:
        ev = np.array([fwd[k][i] for i in range(n - k) if mask_ev[i]])
        ctrl = np.array([fwd[k][i] for i in range(n - k) if not mask_ev[i]])
        if len(ev) > 1 and len(ctrl) > 1:
            var_ev = ev.var(ddof=1) / len(ev)
            var_ct = ctrl.var(ddof=1) / len(ctrl)
            se2 = var_ev + var_ct
            t = float((ev.mean() - ctrl.mean()) / math.sqrt(se2)) if se2 > 0 else None
            df = (se2 ** 2 / (var_ev ** 2 / (len(ev) - 1) + var_ct ** 2 / (len(ctrl) - 1))) if se2 > 0 else None
            sig[th][f"T{k}"] = {"ev_mean": round(float(ev.mean()), 2), "ctrl_mean": round(float(ctrl.mean()), 2),
                                "diff_mean": round(float(ev.mean() - ctrl.mean()), 2),
                                "t": round(t, 2) if t else None, "df": round(df, 1) if df else None,
                                "n_ev": int(len(ev)), "n_ctrl": int(len(ctrl))}
        else:
            sig[th][f"T{k}"] = None

recent = m.tail(252).copy()
recent["month"] = recent["date"].dt.strftime("%Y-%m")
recent_m = recent.groupby("month").agg(vix_mean=("close_vix", "mean"), vix_min=("close_vix", "min"),
                                       vix_max=("close_vix", "max"),
                                       spy_ret=("close_spy", lambda x: pct(x.iloc[0], x.iloc[-1]))).round(2)

# ---------- 9. 事件明细 CSV (事件研究标准输出: 一行一事件, VIX<15 主口径) ----------
runs15 = find_runs(15)
def run_of(day):
    for (ii, jj, ln) in runs15:
        if ii <= day <= jj:
            return ii, jj, ln
    return None

main_events = []
for i in sorted(events[15].keys()):
    d = events[15][i]
    if "T20" not in d:          # 尾部无完整前瞻窗口, 不构成完整事件
        continue
    rn = run_of(i)
    main_events.append({
        "label": f"VIX 低位日 <15 (区间D{rn[2]}天)",
        "symbol": "SPY",
        "entry_date": str(pd.Timestamp(dates[i]).date()),
        "exit_date": str(pd.Timestamp(dates[i + 20]).date()) if i + 20 < n else "",
        "pnl_pct": d["T20"],
        "vix": round(float(vix[i]), 2),
        "days_in_run": int(rn[2]),           # 所在低位区间总长度
        "day_no_in_run": int(i - rn[0] + 1), # 区间内第几天 (1=起点)
        "show_marker": False,   # 低位日稠密, 不在主图逐日打标(避免 >200 markers), 明细表保留
    })

os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
pd.DataFrame(main_events).to_csv(os.path.join(ROOT, "results", "vix_low_spy_events.csv"), index=False, encoding="utf-8")

out = {
    "meta": {"n_days": n, "start": str(pd.Timestamp(dates[0]).date()), "end": str(pd.Timestamp(dates[-1]).date()),
             "cur_vix": round(cur_vix, 2), "cur_spy": round(cur_spy, 2),
             "cur_pctile": round(cur_pctile, 1),
             "vix_mean_all": round(float(vix.mean()), 2), "vix_median_all": round(float(np.median(vix)), 2),
             "vix_q25": round(float(np.percentile(vix, 25)), 2), "vix_q10": round(float(np.percentile(vix, 10)), 2),
             "spy_hist_high": round(spy_hist_high, 2), "spy_drawdown_from_high": round(spy_drawdown_from_high, 2),
             "cur_run_days_under15": int(run15)},
    "base_fwd": {f"T{k}": base[f"T{k}"] for k in FWDS},
    "by_day": {str(th): {f"T{k}": by_day[th][f"T{k}"] for k in FWDS} for th in THRESHOLDS},
    "by_start": {str(th): {f"T{k}": by_start[th][f"T{k}"] for k in FWDS} for th in THRESHOLDS},
    "sig": {str(th): {f"T{k}": sig[th][f"T{k}"] for k in FWDS} for th in THRESHOLDS},
    "run_stats": {str(th): run_stats[th] for th in THRESHOLDS},
    "run_detail": {str(th): run_detail[th] for th in THRESHOLDS},
    "life_tab_15": {str(D): life_tab_15[D] for D in life_tab_15},
    "life_tab_13": {str(D): life_tab_13[D] for D in life_tab_13},
    "break_to20": {str(th): break_to20[th] for th in THRESHOLDS},
    "high_scenario": {str(th): high_scen[th] for th in THRESHOLDS},
    "recent_monthly": recent_m.reset_index().to_dict("records"),
}
with open(os.path.join(ROOT, "results", "vix_low_spy.json"), "w", encoding="utf-8") as f:
    json.dump(clean_all(out), f, ensure_ascii=False, indent=1)
print("saved: results/vix_low_spy.json")
print("saved: results/vix_low_spy_events.csv")

# ---------- 控制台摘要 ----------
print(f"\n当前: VIX={cur_vix:.2f} (分位 {cur_pctile:.1f}%), SPY={cur_spy:.2f} (距历史高点 {spy_drawdown_from_high:.1f}%), 连续<15 天数={run15}")
print(f"样本 {n} 交易日, {m.date.iloc[0].date()} ~ {m.date.iloc[-1].date()}")
print(f"\n基线 T+20: mean={base['T20']['mean']}% win={base['T20']['win']}% | T+60: mean={base['T60']['mean']}% win={base['T60']['win']}%")
for th in THRESHOLDS:
    s = by_start[th]["T20"]
    print(f"VIX<{th} 区间起点入场 T+20: mean={s['mean']}% med={s['median']}% win={s['win']}% (n={s['n']}) | 基线 mean={base['T20']['mean']}%")
    sd = by_day[th]["T20"]
    print(f"   [按日] T+20: mean={sd['mean']}% win={sd['win']}% (n={sd['n']}) | T+60: mean={by_day[th]['T60']['mean']}% win={by_day[th]['T60']['win']}%")
    rs = run_stats[th]
    print(f"   区间: {rs['n_runs']}段, 中位{rs['len_median']}d/均值{rs['len_mean']}d/P90={rs['len_p90']}d/最长{rs['len_max']}d, 占全期 {rs['pct_time']}%")

print("\nVIX<15 条件剩余寿命表 (% 能再维持 ≥K 天):")
print("   已持续\\再维持   K=3    K=5    K=10   K=20   K=40   K=60")
for D in [1, 3, 5, 10, 20, 40]:
    row = life_tab_15[D]
    print(f"   D={D:<3d}        " + "  ".join(f"{row[K]:>5.1f}" if row[K] is not None else "   -" for K in [3, 5, 10, 20, 40, 60]))

print("\n回归速度(区间起点 -> VIX 首破20, 交易日):")
for th in THRESHOLDS:
    b = break_to20[th]
    if b:
        print(f"   VIX<{th}: n={b['n']} 中位{b['median']}d 均值{b['mean']}d P25={b['p25']}d 最长{b['best']}d")

print("\n显著性(低位日 vs 非低位日, diff_mean / Welch t):")
for th in THRESHOLDS:
    for k in FWDS:
        s_ = sig[th][f"T{k}"]
        if s_:
            print(f"   VIX<{th} T+{k}: 低位={s_['ev_mean']:+.2f}% vs 非低位={s_['ctrl_mean']:+.2f}% diff={s_['diff_mean']:+.2f}pp t={s_['t']} df={s_['df']}")