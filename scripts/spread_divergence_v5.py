#!/usr/bin/env python3
"""月差背离 v5 —— 通用脚本：CL/HO/RB 近月月差 + regime 客观分类
口径：
  - 月差 y = current - next（近月 M1-M2），价格 x = current.close
  - 换月：next 腿单边跳（|next_ret|>1.5% 且 > |cur_ret| 且差>1%）→ roll，重置记忆
  - 阈值按各自同价位月差 std 对齐（delta ≈ 0.10 倍同价位 std）
  - regime 客观分类：rolling 月差 sma(24h) vs sma(120h)，短期>长期=走扩期，否则=回落期
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
from scipy import stats

BASE = "/Users/alberthuang/Desktop/股票分析"
OUT = os.path.join(BASE, "results/spread_divergence")

# 各品种参数：eps=价格分档(各自计价单位), scale=月差换算到「美元/桶」的倍率,
# delta=背离阈值（按 0.10 倍同价位 std 对齐，量纲=美元/桶）。
# HO/RB 价差原本是 美元/加仑，1桶=42加仑，故 ×42。
PRODUCTS = {
  "CL": dict(eps=0.5,  scale=1,  delta=0.07),
  "HO": dict(eps=0.02, scale=42, delta=0.26),
  "RB": dict(eps=0.02, scale=42, delta=0.27),
}
WIN, VOTES, FWD_Ns = 5, 3, [24, 48, 72]
ROLL_RET, ROLL_DIFF = 0.015, 0.01

def load(f):
    df = pd.read_csv(f)[["datetime", "close"]]
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.set_index("datetime").close

def run(prod, cfg):
    data = f"{BASE}/data/{prod.lower()}_contracts/1h"
    cur = load(f"{data}/US.{prod}current.csv")
    nxt = load(f"{data}/US.{prod}next.csv")
    m = pd.concat([cur, nxt], axis=1, join="inner").dropna()
    m.columns = ["cur", "next"]
    scale = cfg["scale"]
    x = m.cur.values
    y = (m.cur.values - m.next.values) * scale   # 统一到 美元/桶
    t_axis = m.index
    n = len(x)

    # 换月检测
    rc = m.cur.pct_change(); rn = m.next.pct_change()
    roll = np.zeros(n, dtype=bool)
    for i in range(1, n):
        a, b = rc.iloc[i], rn.iloc[i]
        if pd.notna(a) and pd.notna(b):
            if abs(b) > ROLL_RET and abs(b) > abs(a) and abs(b - a) > ROLL_DIFF:
                roll[i] = True

    # 检测背离（下一次经过同价位，月差走扩 > delta）
    eps, delta = cfg["eps"], cfg["delta"]
    def bucket(p): return int(round(p / eps))
    last_y = {}; vote = np.zeros(n, dtype=int)
    for t in range(n):
        if roll[t]:
            last_y = {}; continue
        b = bucket(x[t]); yt = y[t]
        if b in last_y and yt > last_y[b] + delta:
            vote[t] = 1
        last_y[b] = yt
    hits, i = [], 0
    while i <= n - WIN:
        if vote[i:i+WIN].sum() >= VOTES:
            hits.append(i + WIN - 1); i += WIN
        else:
            i += 1
    hit_set = set(hits)

    # regime 客观分类：月差 sma(24) vs sma(120)
    s = pd.Series(y)
    sma_s = s.rolling(24).mean()
    sma_l = s.rolling(120).mean()
    regime = np.where(sma_s.values > sma_l.values, 1, 0)  # 1=走扩期

    bars = []
    for k in range(n):
        bars.append({
            "t": str(t_axis[k]), "x": float(x[k]), "y": float(y[k]),
            "vote": int(vote[k]), "hit": 1 if k in hit_set else 0,
            "roll": 1 if roll[k] else 0, "regime": int(regime[k]),
        })

    def fwd_y(idxs, N):
        return np.array([y[t+N]-y[t] for t in idxs if t+N < n])
    def fwd_x(idxs, N):
        return np.array([x[t+N]-x[t] for t in idxs if t+N < n])

    hit_idx = np.array(hits)
    out = {"product": prod, "params": cfg, "n_bars": n, "n_roll": int(roll.sum()),
           "roll_bars": [str(t_axis[k]) for k in range(n) if roll[k]],
           "n_votes": int(vote.sum()), "n_hits": len(hits),
           "spread_range": [float(y.min()), float(y.max())],
           "regime_split": {}}

    # 全样本 + 分 regime
    all_base = list(range(0, n))
    res = {}
    for label, idx in [("ALL", hit_idx), ("RISE", hit_idx[regime[hit_idx]==1]),
                       ("FALL", hit_idx[regime[hit_idx]==0])]:
        res[label] = {"n": len(idx)}
        for N in FWD_Ns:
            fy = fwd_y(idx, N); fx = fwd_x(idx, N); by = fwd_y(all_base, N)
            res[label][str(N)] = {
                "n": int(len(fy)),
                "dy_mean": float(fy.mean()) if len(fy) else None,
                "dy_pct_pos": float((fy>0).mean()) if len(fy) else None,
                "dx_mean": float(fx.mean()) if len(fx) else None,
                "excess": float(fy.mean()-by.mean()) if len(fy) else None,
                "t": float(stats.ttest_ind(fy, by, equal_var=False).statistic) if len(fy)>=8 else None,
                "p": float(stats.ttest_ind(fy, by, equal_var=False).pvalue) if len(fy)>=8 else None,
            }
    out["regime_split"] = res
    with open(f"{OUT}/spread_divergence_v5_{prod}.json", "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    with open(f"{OUT}/v5_{prod}_bars.json", "w") as fh:
        json.dump(bars, fh, ensure_ascii=False)
    return out

def print_summary(o):
    print(f"\n===== {o['product']}  (eps={o['params']['eps']}, delta={o['params']['delta']}) =====")
    print(f"  bars={o['n_bars']} roll={o['n_roll']} {o['roll_bars']}  月差区间 {o['spread_range']}")
    print(f"  总票={o['n_votes']} 总命中={o['n_hits']}")
    for label in ["ALL", "RISE", "FALL"]:
        r = o["regime_split"][label]
        line = f"  [{label:4s}] n={r['n']:3d}"
        for N in FWD_Ns:
            d = r[str(N)]
            line += f" | {N}h dy={d['dy_mean']:+.4f}(走扩{d['dy_pct_pos']:.0%})"
        print(line)
    # 显著性
    for label in ["RISE", "FALL"]:
        r = o["regime_split"][label]
        d = r["24"]
        print(f"  [{label}] 24h: t={d['t']:.2f} p={d['p']:.4f}")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for prod, cfg in PRODUCTS.items():
        o = run(prod, cfg)
        print_summary(o)
