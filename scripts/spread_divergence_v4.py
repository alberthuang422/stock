#!/usr/bin/env python3
"""CL 月差背离 v4 —— 近月月差口径（CLcurrent - CLnext，M1-M2）+ 换月剔除
用户定义：价位记忆对比 + 滚动5bar≥3票命中；研究背离后月差续扩还是补跌收敛。
v4 修正（相对 v3 的错误远月价差口径）：
  - 月差 y = CLcurrent.close - CLnext.close（真近月 M1-M2）
  - 价格 x = CLcurrent.close
  - 换月剔除：任一条腿 |ret|>2.5% 且两腿跳幅差>1.5% → 该 bar 记为 roll，其后 last_y 记忆重置
  - 阈值对齐：eps=0.5, delta=0.07（等比于远月 0.1档 delta=0.03）
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
from scipy import stats

BASE = "/Users/alberthuang/Desktop/股票分析"
DATA = os.path.join(BASE, "data/cl_contracts/1h")
OUT = os.path.join(BASE, "results/spread_divergence")
P = dict(eps=0.5, delta=0.07, win=5, votes=3, forward_Ns=[24, 48, 72],
         roll_ret=0.025, roll_diff=0.015)

def load(f):
    df = pd.read_csv(f)[["datetime", "close"]]
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.set_index("datetime").close

def detect_rolls(cur, nxt):
    """换月 bar 掩码：一条腿 |ret|>roll_ret 且两腿差>roll_diff。"""
    rc = cur.pct_change(); rn = nxt.pct_change()
    roll = np.zeros(len(cur), dtype=bool)
    for i in range(1, len(cur)):
        a, b = rc.iloc[i], rn.iloc[i]
        if pd.notna(a) and pd.notna(b):
            # 仅 next 腿单边跳（换月）；cur 主导的跳变是真实行情，保留
            if abs(b) > 0.015 and abs(b) > abs(a) and abs(b - a) > 0.01:
                roll[i] = True
    return roll

def detect(x, y, roll, eps, delta, win, votes):
    """返回 (vote, hits)。roll bar 处重置 last_y 记忆。"""
    n = len(x)
    def bucket(p): return int(round(p / eps))
    last_y = {}
    vote = np.zeros(n, dtype=int)
    for t in range(n):
        if roll[t]:
            last_y = {}  # 换月后电平跳变，记忆失效
            continue
        b = bucket(x[t]); yt = y[t]
        if b in last_y and yt > last_y[b] + delta:
            vote[t] = 1
        last_y[b] = yt
    hits, i = [], 0
    while i <= n - win:
        if vote[i:i+win].sum() >= votes:
            hits.append(i + win - 1); i += win
        else:
            i += 1
    return vote, hits

def fwd(y, hits, N):
    return np.array([y[t+N]-y[t] for t in hits if t+N < len(y)])

def fwd_price(x, hits, N):
    return np.array([x[t+N]-x[t] for t in hits if t+N < len(x)])

def main():
    os.makedirs(OUT, exist_ok=True)
    cur = load(os.path.join(DATA, "US.CLcurrent.csv"))
    nxt = load(os.path.join(DATA, "US.CLnext.csv"))
    m = pd.concat([cur, nxt], axis=1, join="inner").dropna()
    m.columns = ["cur", "next"]
    x = m.cur.values; y = m.cur.values - m.next.values
    t_axis = m.index.strftime("%Y-%m-%d %H:%M").tolist()
    n = len(x)
    roll = detect_rolls(m.cur, m.next)

    vote, hits = detect(x, y, roll, P["eps"], P["delta"], P["win"], P["votes"])

    # 逐 bar 记录（投票 + 触发，供画图）
    hit_set = set(hits)
    bars = [{"t": t_axis[i], "x": float(x[i]), "y": float(y[i]),
             "vote": int(vote[i]), "hit": 1 if i in hit_set else 0,
             "roll": 1 if roll[i] else 0} for i in range(n)]

    # 前向统计（多档）
    fwd_stats = {}
    for N in P["forward_Ns"]:
        fy = fwd(y, hits, N); fp = fwd_price(x, hits, N)
        by = fwd(y, list(range(0, n - N)), N); bp = fwd_price(x, list(range(0, n - N)), N)
        fwd_stats[str(N)] = {
            "hit_n": int(len(fy)),
            "hit_dy_mean": float(fy.mean()) if len(fy) else None,
            "hit_dy_median": float(np.median(fy)) if len(fy) else None,
            "hit_dy_pct_pos": float((fy > 0).mean()) if len(fy) else None,
            "hit_dx_mean": float(fp.mean()) if len(fp) else None,
            "hit_dx_pct_up": float((fp > 0).mean()) if len(fp) else None,
            "base_n": int(len(by)),
            "base_dy_mean": float(by.mean()) if len(by) else None,
            "base_dy_pct_pos": float((by > 0).mean()) if len(by) else None,
            "excess_dy": float(fy.mean() - by.mean()) if (len(fy) and len(by)) else None,
            "ttest_t": float(stats.ttest_ind(fy, by, equal_var=False).statistic) if len(fy) >= 8 else None,
            "ttest_p": float(stats.ttest_ind(fy, by, equal_var=False).pvalue) if len(fy) >= 8 else None,
        }

    report = {
        "pair": "CL 近月月差 M1-M2（US.CLcurrent - US.CLnext，Futu 连续代码 1h）",
        "algo": "价位记忆对比 + 滚动5bar≥3票命中（roll bar 处记忆重置）",
        "params": P,
        "n_bars": n,
        "n_roll_bars": int(roll.sum()),
        "roll_bars": [t_axis[i] for i in range(n) if roll[i]],
        "total_votes": int(vote.sum()),
        "total_hits": len(hits),
        "spread_range": [float(y.min()), float(y.max())],
        "fwd": fwd_stats,
    }

    with open(os.path.join(OUT, "spread_divergence_v4.json"), "w") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    # 画图用逐 bar 数据
    with open(os.path.join(OUT, "v4_bars.json"), "w") as fh:
        json.dump({"bars": bars, "hits": [t_axis[i] for i in hits]}, fh, ensure_ascii=False)

    print("== v4 近月月差口径 ==")
    print(f"  bars={n}  roll_bars={int(roll.sum())} {[t_axis[i] for i in range(n) if roll[i]]}")
    print(f"  月差区间 {y.min():+.2f} ~ {y.max():+.2f}  总票={int(vote.sum())}  总命中={len(hits)}")
    for N in P["forward_Ns"]:
        s = fwd_stats[str(N)]
        print(f"  前向{N}h: 命中n={s['hit_n']} 月差均变动 {s['hit_dy_mean']:+.3f} "
              f"(走扩率{s['hit_dy_pct_pos']:.1%}) | 期货价格 {s['hit_dx_mean']:+.3f} "
              f"(上涨率{s['hit_dx_pct_up']:.1%}) | 对照 {s['base_dy_mean']:+.3f} "
              f"超额={s['excess_dy']:+.3f} t={s['ttest_t']:.1f} p={s['ttest_p']:.4f}")

if __name__ == "__main__":
    main()
