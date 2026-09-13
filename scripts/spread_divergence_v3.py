#!/usr/bin/env python3
"""CL 月差背离 v3 —— 用户算法口径（同一价位月差记忆对比）

用户定义（2026-09-11 澄清）：
- 维护一张「价位 → 最近一次经过时的月差」表
- 价格重新回到某价位 x 时，对比新月差 y' 与上次月差 y
- 若 y' > y + δ（月差走扩）→ 记 1 票
- 滚动 win=5 个 bar 内 ≥ votes=3 票 → 命中（背离事件）
研究问题：命中后，月差继续走扩还是补跌收敛？

实现要点：
- 价位用 bucket(p)=round(p/eps) 分档，eps=0.10（$0.1 一档）
- last_y 每次经过都更新为最新月差 → 对比的是"最近两次经过同价位的月差"
- 命中去重：连续命中段合并为一个事件（冷却 win 根 bar），避免伪独立
- 对照组：全样本无条件前向 N bar 月差变化分布
"""
from __future__ import annotations
import json, os, glob
import numpy as np
import pandas as pd
from scipy import stats

DATA = "/Users/alberthuang/Desktop/股票分析/data/cl_contracts/1h"
OUT = "/Users/alberthuang/Desktop/股票分析/results/spread_divergence"
P = dict(eps=0.10, delta=0.03, win=5, votes=3, forward_N=24)


def ordered_files():
    files = sorted(glob.glob(os.path.join(DATA, "US.CL*.csv")))
    return [f for f in files if "current" not in f and "next" not in f]


def load_close(f):
    df = pd.read_csv(f)
    return df[["datetime", "close"]]


def detect_v3(x, y, eps, delta, win, votes):
    """返回 (vote_array, hit_indices去重后的事件触发点)。"""
    n = len(x)
    def bucket(p):
        return int(round(p / eps))
    last_y = {}
    vote = np.zeros(n, dtype=int)
    for t in range(n):
        b = bucket(x[t]); yt = y[t]
        if b in last_y and yt > last_y[b] + delta:
            vote[t] = 1
        last_y[b] = yt

    # 滚动 win 内 >= votes 命中；去重（命中后冷却 win bar）
    hits = []
    i = 0
    while i <= n - win:
        if vote[i:i + win].sum() >= votes:
            hits.append(i + win - 1)  # 事件确认点 = 窗口最后 bar
            i += win  # 冷却
        else:
            i += 1
    return vote, hits


def fwd_changes(y, hits, N):
    out = []
    for t in hits:
        if t + N < len(y):
            out.append(y[t + N] - y[t])
    return np.array(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    files = ordered_files()
    eps, delta, win, votes, N = P["eps"], P["delta"], P["win"], P["votes"], P["forward_N"]

    pair_report = {}
    all_hit_fwd, all_base = [], []
    total_votes = 0

    for i in range(len(files) - 1):
        a = load_close(files[i]); b = load_close(files[i + 1])
        m = pd.merge(a, b, on="datetime", suffixes=("_a", "_b")).sort_values("datetime")
        x = m.close_a.values; y = m.close_a.values - m.close_b.values
        n = len(x)
        code = (os.path.basename(files[i])[5:9] + "-" + os.path.basename(files[i + 1])[5:9])
        vote, hits = detect_v3(x, y, eps, delta, win, votes)
        fwd = fwd_changes(y, hits, N)
        base = fwd_changes(y, list(range(0, n - N)), N)
        total_votes += int(vote.sum())
        pair_report[code] = {
            "n_bars": n, "votes": int(vote.sum()), "hits": len(hits),
            "hit_rate": round(len(hits) / n, 4),
            "hit_fwd_mean": float(fwd.mean()) if len(fwd) else None,
            "hit_fwd_median": float(np.median(fwd)) if len(fwd) else None,
        }
        all_hit_fwd.append(fwd)
        all_base.append(base)

    hit_fwd = np.concatenate(all_hit_fwd) if all_hit_fwd else np.array([])
    base_fwd = np.concatenate(all_base) if all_base else np.array([])

    report = {
        "pair": "CL 相邻月合约 +1 跨期（13 腿 → 12 pair，Futu 同源 1h）",
        "granularity": "1h",
        "algo": "用户口径：价位→月差记忆对比，滚动5bar≥3票命中",
        "params": P,
        "total_votes": total_votes,
        "total_hits": int(np.sum([v["hits"] for v in pair_report.values()])),
        "per_pair": pair_report,
        "hit_fwd": {
            "n": int(len(hit_fwd)),
            "mean": float(hit_fwd.mean()) if len(hit_fwd) else None,
            "median": float(np.median(hit_fwd)) if len(hit_fwd) else None,
            "std": float(hit_fwd.std()) if len(hit_fwd) else None,
            "pct_走扩": float((hit_fwd > 0).mean()) if len(hit_fwd) else None,
        },
        "base_fwd": {
            "n": int(len(base_fwd)),
            "mean": float(base_fwd.mean()),
            "median": float(np.median(base_fwd)),
            "pct_走扩": float((base_fwd > 0).mean()),
        },
    }
    if len(hit_fwd) >= 8 and len(base_fwd) >= 30:
        tt = stats.ttest_ind(hit_fwd, base_fwd, equal_var=False)
        mw = stats.mannwhitneyu(hit_fwd, base_fwd)
        report["significance"] = {
            "ttest_t": float(tt.statistic), "ttest_p": float(tt.pvalue),
            "mw_p": float(mw.pvalue),
            "excess_mean": float(hit_fwd.mean() - base_fwd.mean()),
        }

    with open(os.path.join(OUT, "spread_divergence_v3.json"), "w") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, default=str)

    print(f"== v3 用户口径 汇总 == 总票数={total_votes} 总命中={report['total_hits']}")
    for k, v in pair_report.items():
        print(f"  {k}: bars={v['n_bars']} 票={v['votes']} 命中={v['hits']} "
              f"命中率={v['hit_rate']:.1%} 前向均值={v['hit_fwd_mean']}")
    print(f"\n命中组前向{N}h月差变化: n={report['hit_fwd']['n']} "
          f"mean={report['hit_fwd']['mean']:+.4f} median={report['hit_fwd']['median']:+.4f} "
          f"走扩率={report['hit_fwd']['pct_走扩']:.2f}")
    print(f"对照组前向{N}h月差变化: n={report['base_fwd']['n']} "
          f"mean={report['base_fwd']['mean']:+.4f} 走扩率={report['base_fwd']['pct_走扩']:.2f}")
    if "significance" in report:
        s = report["significance"]
        print(f"显著性: t={s['ttest_t']:.2f} p={s['ttest_p']:.4f} MW_p={s['mw_p']:.4f} "
              f"超额={s['excess_mean']:+.4f}")


if __name__ == "__main__":
    main()