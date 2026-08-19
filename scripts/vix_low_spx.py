#!/usr/bin/env python3
"""VIX 低位 → 标普500 后续行情 + VIX 低位持续时长分析。

核心问题:
Q1: VIX 处于低位时, SPX 后续行情如何 (vs 全期基线)?
Q2: VIX 低位能维持多久? (区间长度分布 + 条件剩余寿命 + 回归速度)

口径:
- 数据: data/vix/VIX, 1D.csv + data/gspc/GSPC, 1D.csv (1990-01-02 ~ 2026-08-14, 内对齐 9222 日)
- VIX 低位阈值: 15(低) / 13(极低) / 12(罕见极低) / 14.0(≈P25)
- 前瞻收益: 按"连续低位区间起点"入场(独立样本) + 按日入场(全样本, 样本重叠, 供参考)
- 低位区间: 连续 close_vix < 阈值 的交易日段

输出: results/vix_low_spx.json
"""
import os, json
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def pct(a, b):
    return (b / a - 1) * 100

# ---------- 1. 加载 ----------
v = pd.read_csv(os.path.join(ROOT, "data", "vix", "VIX, 1D.csv"), parse_dates=["date"])
g = pd.read_csv(os.path.join(ROOT, "data", "gspc", "GSPC, 1D.csv"), parse_dates=["date"])
m = v.merge(g, on="date", suffixes=("_vix", "_gspc"))[["date", "close_vix", "close_gspc"]]
m = m.sort_values("date").reset_index(drop=True)
print(f"合并样本: {len(m)} 交易日, {m.date.iloc[0].date()} ~ {m.date.iloc[-1].date()}")

vix = m["close_vix"].values
spx = m["close_gspc"].values
dates = m["date"].values
n = len(m)

# ---------- 2. 当前状态定位 ----------
cur_vix = float(vix[-1])
cur_spx = float(spx[-1])
cur_pctile = (vix < cur_vix).mean() * 100
spx_hist_high = float(spx.max())
spx_drawdown_from_high = pct(spx_hist_high, cur_spx)

# 当前连续 <15 天数
run15 = 0
for i in range(n - 1, -1, -1):
    if vix[i] < 15:
        run15 += 1
    else:
        break

# ---------- 3. 前瞻收益 ----------
THRESHOLDS = [15, 13, 12]
FWDS = [5, 10, 20, 60, 120]
fwd_ret = {}  # (th, start_idx) -> {n: ret}
for th in THRESHOLDS:
    fwd_ret[th] = {}
    mask = vix < th
    # 区间起点
    starts = np.where(mask & ~np.roll(mask, 1))[0]  # 前一天不低位, 今天低位 -> 起点
    for s in starts:
        d = {}
        for nn in FWDS:
            if s + nn < n:
                d[nn] = pct(spx[s], spx[s + nn])
        fwd_ret[th][int(s)] = d

def stats(arr):
    a = np.array([x for x in arr if x is not None], dtype=float)
    if len(a) == 0:
        return None
    return {
        "n": int(len(a)), "mean": round(float(a.mean()), 2), "median": round(float(np.median(a)), 2),
        "win": round(float((a > 0).mean()) * 100, 1), "p25": round(float(np.percentile(a, 25)), 2),
        "worst": round(float(a.min()), 2), "best": round(float(a.max()), 2),
    }

# 基线: 所有可计算日
base = {}
for n_ in FWDS:
    base[n_] = stats([pct(spx[i], spx[i + n_]) for i in range(n - n_)])

by_start = {th: {n_: stats([d.get(n_) for d in fwd_ret[th].values()]) for n_ in FWDS} for th in THRESHOLDS}

# 按日入场(全样本, 重叠) 供参考
by_day = {}
for th in THRESHOLDS:
    by_day[th] = {}
    idxs = np.where(vix < th)[0]
    for n_ in FWDS:
        vals = [pct(spx[i], spx[i + n_]) for i in idxs if i + n_ < n]
        by_day[th][n_] = stats(vals)

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
        "days": r, "vix_start": round(float(vix[i]), 2), "vix_end": round(float(vix[j]), 2),
        "spx_chg": round(float(pct(spx[i], spx[j])), 1),
        "spx_fwd20": round(float(pct(spx[j], spx[j + 20])), 1) if j + 20 < n else None,
        "spx_fwd60": round(float(pct(spx[j], spx[j + 60])), 1) if j + 60 < n else None,
    } for i, j, r in runs]

# ---------- 5. 条件剩余寿命: 已持续 D 天, 还能再维持 ≥K 天? ----------
# 对每个区间, 已持续 d 天时剩余寿命; 汇总条件概率
def cond_lifetable(th, Ds, Ks):
    runs = find_runs(th)
    tab = {}
    for D in Ds:
        row = {}
        for K in Ks:
            # 该区间长度 L >= D 时, 剩余 >= K 当且仅当 L - D + 1 >= K (已持续到第D天, 剩余含当天共 L-D+1)
            eligible = [r[2] for r in runs if r[2] >= D]
            if not eligible:
                row[K] = None
                continue
            surv = [r[2] - D + 1 >= K for r in runs if r[2] >= D]
            row[K] = round(float(np.mean(surv)) * 100, 1)
        tab[D] = row
    return tab

life_tab_15 = cond_lifetable(15, [1, 3, 5, 10, 20, 40], [3, 5, 10, 20, 40, 60])
life_tab_13 = cond_lifetable(13, [1, 3, 5, 10, 20, 40], [3, 5, 10, 20, 40, 60])

# ---------- 6. 低位结束后的回归: 从区间起点到 VIX 首次升破 20 的天数 ----------
def days_to_break_20(starts):
    out = []
    for s in starts:
        target = None
        for j in range(s, n):
            if vix[j] >= 20:
                target = j - s + 1
                break
        if target:
            out.append(target)
    return out

break15 = {}  # 从 VIX<15 区间起点, 到首次 >=20
for th in THRESHOLDS:
    starts = [s for s in fwd_ret[th].keys()]
    d20 = days_to_break_20(starts)
    break15[th] = stats(d20) if d20 else None

# ---------- 7. 特殊场景: VIX 低位起点 + SPX 处于高位(距250日高点<5%) ----------
# 当前 SPX 距历史高点仅 xx%, 需要看"低波动+高位"组合的后续
high_scen = {}
for th in THRESHOLDS:
    rows = []
    for s in fwd_ret[th].keys():
        if s < 250:
            continue
        hi250 = spx[max(0, s - 250):s].max()
        dd = pct(hi250, spx[s])
        if dd > -5:  # 距 250 日高点 5% 以内
            rec = {"start": str(pd.Timestamp(dates[s]).date()), "vix": round(float(vix[s]), 2),
                   "spx_drawdown_from_high": round(float(dd), 1)}
            for n_ in FWDS:
                rec[f"fwd{n_}"] = fwd_ret[th][s].get(n_)
            rows.append(rec)
    if rows:
        df = pd.DataFrame(rows)
        agg = {n_: stats([r[f"fwd{n_}"] for r in rows if r.get(f"fwd{n_}") is not None]) for n_ in FWDS}
        high_scen[th] = {"n": len(rows), "agg": agg, "detail": rows}
    else:
        high_scen[th] = None

# ---------- 8. 近12个月 VIX 走势摘要 ----------
recent = m.tail(252).copy()
recent["month"] = recent["date"].dt.strftime("%Y-%m")
recent_m = recent.groupby("month").agg(vix_mean=("close_vix", "mean"), vix_min=("close_vix", "min"),
                                       vix_max=("close_vix", "max"), spx_ret=("close_gspc", lambda x: pct(x.iloc[0], x.iloc[-1]))).round(2)

# ---------- 9. 输出 ----------
out = {
    "meta": {"n_days": n, "start": str(dates[0])[:10], "end": str(dates[-1])[:10],
             "cur_vix": round(cur_vix, 2), "cur_spx": round(cur_spx, 2),
             "cur_pctile": round(cur_pctile, 1),
             "vix_mean_all": round(float(vix.mean()), 2), "vix_median_all": round(float(np.median(vix)), 2),
             "vix_q25": round(float(np.percentile(vix, 25)), 2), "vix_q10": round(float(np.percentile(vix, 10)), 2),
             "spx_hist_high": round(spx_hist_high, 2), "spx_drawdown_from_high": round(spx_drawdown_from_high, 2),
             "cur_run_days_under15": int(run15)},
    "base_fwd": {f"T{n_}": base[n_] for n_ in FWDS},
    "by_start": {str(th): {f"T{n_}": by_start[th][n_] for n_ in FWDS} for th in THRESHOLDS},
    "by_day": {str(th): {f"T{n_}": by_day[th][n_] for n_ in FWDS} for th in THRESHOLDS},
    "run_stats": {str(th): run_stats[th] for th in THRESHOLDS},
    "run_detail": {str(th): run_detail[th] for th in THRESHOLDS},
    "life_tab_15": {str(D): life_tab_15[D] for D in life_tab_15},
    "life_tab_13": {str(D): life_tab_13[D] for D in life_tab_13},
    "break_to20": {str(th): break15[th] for th in THRESHOLDS},
    "high_scenario": {str(th): high_scen[th] for th in THRESHOLDS},
    "recent_monthly": recent_m.reset_index().to_dict("records"),
}

os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
with open(os.path.join(ROOT, "results", "vix_low_spx.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("saved: results/vix_low_spx.json")

# ---------- 控制台摘要 ----------
print(f"\n当前: VIX={cur_vix} (分位 {cur_pctile:.1f}%), SPX={cur_spx:.0f} (距历史高点 {spx_drawdown_from_high:.1f}%), 连续<15 天数={run15}")
print(f"\n基线 T+20: mean={base[20]['mean']}% win={base[20]['win']}% | T+60: mean={base[60]['mean']}% win={base[60]['win']}%")
for th in THRESHOLDS:
    s = by_start[th][20]
    if s is None:
        print(f"VIX<{th} 区间起点入场 T+20: 无样本"); continue
    print(f"VIX<{th} 区间起点入场 T+20: mean={s['mean']}% median={s['median']}% win={s['win']}% (n={s['n']}) | 基线 mean={base[20]['mean']}%")
    s60 = by_start[th][60]
    if s60:
        print(f"   T+60: mean={s60['mean']}% win={s60['win']}% | 基线 mean={base[60]['mean']}% win={base[60]['win']}%")
    rs = run_stats[th]
    print(f"   区间: {rs['n_runs']}段, 时长 中位{rs['len_median']}d/均值{rs['len_mean']}d/P90={rs['len_p90']}d/最长{rs['len_max']}d, 占全期 {rs['pct_time']}%")
print("\nVIX<15 条件剩余寿命表 (% 能再维持 ≥K 天):")
print("   已持续\\再维持   K=3    K=5    K=10   K=20   K=40   K=60")
for D in [1, 3, 5, 10, 20, 40]:
    row = life_tab_15[D]
    print(f"   D={D:<3d}        " + "  ".join(f"{row[K]:>5.1f}" if row[K] is not None else "   -" for K in [3, 5, 10, 20, 40, 60]))
