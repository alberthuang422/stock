#!/usr/bin/env python3
"""CL 月差「背离事件」回测 v2 —— 严格事件法 + 连续化状态法 双口径

研究问题：原油价格大涨带动月差走扩 → 价格回落到起涨位、但月差未同步回落
（= 近月白涨白跌、远月被永久压低）→ 月差后续是「继续走扩」还是「补跌收敛」？

两个口径（严格事件法样本极少是本身发现，故补连续化状态法）：
1. 严格事件法（round-trip 状态机）：价格从 trough 大涨 θ 达 peak 后回落 x≤x1 且 y>y1+δ，
   5 bar 内 ≥3 票确认。结果：半年单边上涨市 + 多 pair 合计仅个位数样本 → 无统计力，仅方向佐证。
2. 连续化状态法（主结论）：每个 bar 计算滚动 L 窗内"距峰值回吐 depth"与
   "月差相对峰值变化 dy_pk"，分背离组(depth≥τ 且 dy_pk≥0) vs 正常组(depth≥τ 且 dy_pk<0)，
   比较前向 N bar 月差变化分布（均值/中位/走扩率 + t 检验/MW 检验）。
   额外做 depth 分档梯度表 + 全样本对照。
"""
from __future__ import annotations
import json
import os
import glob
import numpy as np
import pandas as pd
from scipy import stats

DATA = "/Users/alberthuang/Desktop/股票分析/data/cl_contracts/1h"
OUT = "/Users/alberthuang/Desktop/股票分析/results/spread_divergence"
PARAMS = dict(L=24, tau=1.5, forward_N=24)
CONFIRM = dict(w=5, v=3)  # 严格事件法确认

CONTRACT_MONTH = {
    "2610": "OCT26", "2611": "NOV26", "2612": "DEC26", "2701": "JAN27",
    "2702": "FEB27", "2703": "MAR27", "2704": "APR27", "2705": "MAY27",
    "2706": "JUN27", "2707": "JUL27", "2708": "AUG27", "2709": "SEP27",
    "2710": "OCT27",
}


def ordered_files():
    files = sorted(glob.glob(os.path.join(DATA, "US.CL*.csv")))
    files = [f for f in files if "current" not in f and "next" not in f]
    return files


def load_close(f):
    df = pd.read_csv(f)
    return df[["datetime", "close"]]


def detect_events(x, y, L, theta, delta, confirm_w, confirm_v):
    """严格 round-trip 事件法（同 v1）。返回 (事件列表, n)。"""
    n = len(x)
    events = []
    cooldown_until = -1
    t = L
    while t < n:
        if t <= cooldown_until:
            t += 1
            continue
        w = x[t - L:t]
        pos_min = t - L + int(np.argmin(w))
        x1 = x[pos_min]
        seg = x[pos_min:t]
        pos_peak = pos_min + int(np.argmax(seg))
        x_peak = x[pos_peak]
        if x_peak - x1 < theta or not (pos_min < pos_peak < t):
            t += 1
            continue
        if not (x[t] <= x1 and y[t] > y[pos_min] + delta):
            t += 1
            continue
        y1 = y[pos_min]; votes = 0; trigger_t = None
        for j in range(t + 1, min(t + 1 + confirm_w, n)):
            if x[j] <= x1 and y[j] > y1 + delta:
                votes += 1
                if votes >= confirm_v:
                    trigger_t = j; break
        if trigger_t is None:
            t += 1
            continue
        events.append({"peak_pos": int(pos_peak), "peak_x": float(x_peak),
                       "rally": float(x_peak - x1), "anchor_pos": int(pos_min),
                       "trigger_pos": int(trigger_t),
                       "y_expand": float(y[trigger_t] - y1)})
        cooldown_until = trigger_t + CONFIRM.get("_fwd", 0)
        t = trigger_t + 1
    return events, n


def deviation_frame(x, y, L):
    """每个 bar 的距峰回吐 depth 与相对峰值月差变化 dy_pk。"""
    n = len(x)
    depth = np.full(n, np.nan)
    dy_pk = np.full(n, np.nan)
    for t in range(L, n):
        w = x[t - L:t + 1]
        pk = (t - L) + int(np.argmax(w))
        depth[t] = x[pk] - x[t]
        dy_pk[t] = y[t] - y[pk]
    return depth, dy_pk


def entries_from_mask(mask):
    """连续 True 段只取首 bar，防重叠自相关。"""
    e = []
    prev = False
    for t, c in enumerate(mask):
        c = bool(c)
        if c and not prev:
            e.append(t)
        prev = c
    return e


def fwd_changes(y, entries, N):
    out = []
    for t in entries:
        if t + N < len(y):
            out.append(y[t + N] - y[t])
    return np.array(out)


def group_stats(dy, base=None):
    if len(dy) == 0:
        return None
    r = {"n": int(len(dy)), "mean": float(dy.mean()),
         "median": float(np.median(dy)), "std": float(dy.std()),
         "pct_走扩": float((dy > 0).mean())}
    if base is not None and len(dy) >= 8 and len(base) >= 30:
        tt = stats.ttest_ind(dy, base, equal_var=False)
        r["ttest_t"] = float(tt.statistic); r["ttest_p"] = float(tt.pvalue)
        r["mw_p"] = float(stats.mannwhitneyu(dy, base).pvalue)
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    files = ordered_files()
    rng = np.random.default_rng(42)
    L, tau, N = PARAMS["L"], PARAMS["tau"], PARAMS["forward_N"]

    print(F"合约池 {len(files)} 腿：", [os.path.basename(f)[5:9] for f in files])

    # ---- 收集所有 pair ----
    pair_report = {}
    strict_total = 0
    dev_all, norm_all = [], []
    all_fwd_dev, all_fwd_norm = np.array([]), np.array([])
    depth_buckets = {"中部回吐": [], "深处回吐": []}
    all_base = np.array([])

    for i in range(len(files) - 1):
        a = load_close(files[i]); b = load_close(files[i + 1])
        m = pd.merge(a, b, on="datetime", suffixes=("_a", "_b")).sort_values("datetime")
        x = m.close_a.values; y = m.close_a.values - m.close_b.values
        n = len(x)
        code = (os.path.basename(files[i])[5:9] + "-" + os.path.basename(files[i + 1])[5:9])
        # 严格事件
        ev, _ = detect_events(x, y, L, 1.5, 0.15, CONFIRM["w"], CONFIRM["v"])
        strict_total += len(ev)
        # 连续化
        depth, dy_pk = deviation_frame(x, y, L)
        valid = ~np.isnan(depth)
        dev_mask = valid & (depth >= tau) & (dy_pk >= 0)
        norm_mask = valid & (depth >= tau) & (dy_pk < 0)
        ev_dev = entries_from_mask(dev_mask)
        ev_norm = entries_from_mask(norm_mask)
        fdev = fwd_changes(y, ev_dev, N)
        fnorm = fwd_changes(y, ev_norm, N)
        base = fwd_changes(y, list(range(L, n - N)), N)
        pair_report[code] = {
            "n_bars": n,
            "strict_events": len(ev),
            "dev_entries": len(ev_dev),
            "norm_entries": len(ev_norm),
            "dev_mean": float(fdev.mean()) if len(fdev) else None,
        }
        dev_all.append(fdev); norm_all.append(fnorm)
        all_base = np.append(all_base, base)

    all_fwd_dev = np.concatenate(dev_all) if dev_all else np.array([])
    all_fwd_norm = np.concatenate(norm_all) if norm_all else np.array([])

    report = {
        "pair": "CL 相邻月合约 +1 跨期（13 腿 → 12 pair，Futu 同源 1h）",
        "granularity": "1h",
        "params": PARAMS,
        "confirm_strict": CONFIRM,
        "ts_note": "2026-03-10 ~ 2026-09-11（半年），单边上涨市",
        "strict_events_total": strict_total,
        "strict_note": "严格 round-trip 事件法在半年单边上涨市样本 <10，无统计推断力，仅作方向佐证；主结论用连续化状态法",
        "per_pair": pair_report,
        "continuous": {
            "dev": group_stats(all_fwd_dev, all_base),
            "norm": group_stats(all_fwd_norm, all_base),
            "base": group_stats(all_base),
            "dev_vs_norm": None,
        },
    }
    if len(all_fwd_dev) >= 8 and len(all_fwd_norm) >= 8:
        tt = stats.ttest_ind(all_fwd_dev, all_fwd_norm, equal_var=False)
        mw = stats.mannwhitneyu(all_fwd_dev, all_fwd_norm)
        report["continuous"]["dev_vs_norm"] = {
            "ttest_t": float(tt.statistic), "ttest_p": float(tt.pvalue),
            "mw_p": float(mw.pvalue),
        }

    # ---- depth 分档（在最主要 pair 2610-2611 上做梯度）----
    a = load_close(files[0]); b = load_close(files[1])
    mm = pd.merge(a, b, on="datetime", suffixes=("_a", "_b")).sort_values("datetime")
    x = mm.close_a.values; y = mm.close_a.values - mm.close_b.values
    depth, dy_pk = deviation_frame(x, y, L)
    valid = ~np.isnan(depth)
    grad = []
    for lo, hi, lab in [(0, 1, "回吐<1$"), (1, 2, "回吐1-2$"), (2, 3.5, "回吐2-3.5$"), (3.5, 99, "回吐>3.5$")]:
        for sign, slab in [("≥0", "月差未回落"), ("<0", "月差同步收敛")]:
            if sign == "≥0":
                mk = valid & (depth >= lo) & (depth < hi) & (dy_pk >= 0)
            else:
                mk = valid & (depth >= lo) & (depth < hi) & (dy_pk < 0)
            es = entries_from_mask(mk)
            fd = fwd_changes(y, es, N)
            if len(fd) >= 3:
                grad.append({"depth": lab, "dy_sign": slab,
                             **group_stats(fd)})
    report["gradient_2610_2611"] = grad

    with open(os.path.join(OUT, "spread_divergence_v2.json"), "w") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, default=str)

    # ---- 控制台 ----
    print(f"\n严格事件法合计: {strict_total} 个（<10 无统计力）")
    c = report["continuous"]
    for g in ("base", "dev", "norm"):
        s = c[g]
        print(f"\n[{g}] n={s['n']} mean={s['mean']:+.4f} median={s['median']:+.4f} "
              f"走扩率={s['pct_走扩']:.2f}  {'p='+format(s.get('ttest_p'),'.3f') if s.get('ttest_p') is not None else ''}")
    if c["dev_vs_norm"]:
        dvn = c["dev_vs_norm"]
        print(f"\n[背离 vs 正常 两组差异] t={dvn['ttest_t']:.2f} p={dvn['ttest_p']:.3f} MW_p={dvn['mw_p']:.3f}")
    print("\n逐 pair：")
    for k, v in pair_report.items():
        print(f"  {k} bars={v['n_bars']} 严格={v['strict_events']} "
              f"背离进入={v['dev_entries']} 正常进入={v['norm_entries']} dev_mean={v['dev_mean']}")
    print("\ndepth 分档梯度（2610-2611）：")
    for g in grad:
        print(f"  {g['depth']:<12} {g['dy_sign']:<8} n={g['n']:>3} mean={g['mean']:+.4f} "
              f"走扩率={g['pct_走扩']:.2f}")


if __name__ == "__main__":
    main()