#!/usr/bin/env python3
"""CL 月差「背离事件」回测（水平版 round-trip 事件研究）

研究问题：原油价格大涨带动月差走扩 → 价格回落到起涨位、但月差未同步回落
（= 近月白涨白跌、远月被永久压低一个台阶）→ 月差后续是「继续走扩」还是「补跌收敛」？

口径（与 2026-09-11 交接定稿一致）：
- x = 近月价格（OCT6 CL2610 close）；y = 月差 = 近月 − 次月（OCT−NOV）
- 数据：data/cl_contracts/1h（Futu 同源、带 volume，13 腿全月合约对齐）
- 事件 = 水平版 round-trip：回看窗口 L 内价格从 trough 大涨 ≥θ 达 peak，
  随后回落至 x2 ≤ x1（回到起涨位），且 y2 > y1 + δ（月差未回落反而走扩）
- 确认：回落信号后 5 bar 内 ≥3 bar 满足 (x≤x1 且 y>y1+δ)，事件时间=第 3 票 bar
- 前向观察 N bar 的月差变化；冷却期=N（防前向窗口重叠）
- 对照组 = 全样本无条件前向 N bar 月差变化分布（事件研究的对照）
"""
from __future__ import annotations
import json
import os
import numpy as np
import pandas as pd
from scipy import stats

DATA = "/Users/alberthuang/Desktop/股票分析/data/cl_contracts/1h"
OUT = "/Users/alberthuang/Desktop/股票分析/results/spread_divergence"

# 主口径参数（可被 argv 覆盖做敏感性）
P = dict(L=24, theta=1.5, delta=0.15, confirm_w=5, confirm_v=3, forward_N=24)


def load_pair(near="US.CL2610.csv", far="US.CL2611.csv"):
    a = pd.read_csv(os.path.join(DATA, near))
    b = pd.read_csv(os.path.join(DATA, far))
    assert (a.datetime.values == b.datetime.values).all(), "双腿时间戳不对齐"
    df = pd.DataFrame({
        "ts": a.datetime.values,
        "x": a.close.values,          # 近月价格
        "y": a.close.values - b.close.values,  # 月差
    })
    return df


def detect_events(x, y, L, theta, delta, confirm_w, confirm_v, forward_N):
    """单遍滚动窗口法检测水平版 round-trip 背离事件。返回事件列表。
    事件时刻 = 确认期累计到第 confirm_v 票的 bar（最早可交易时点，无前视）。
    """
    n = len(x)
    events = []
    cooldown_until = -1  # 冷却期：此 bar 之前不识别新事件
    t = L
    while t < n:
        if t <= cooldown_until:
            t += 1
            continue
        # 回看窗口 [t-L, t)
        w = x[t - L:t]
        pos_min_local = int(np.argmin(w))
        pos_min = t - L + pos_min_local  # trough 全局位置
        x1 = x[pos_min]
        # trough 之后到 t 之间的 peak（顺序必须 先低后高再回）
        seg = x[pos_min:t]
        pos_peak_local = int(np.argmax(seg))
        pos_peak = pos_min + pos_peak_local
        x_peak = x[pos_peak]
        # 条件1：大涨（trough→peak 至少 θ）
        if x_peak - x1 < theta:
            t += 1
            continue
        # 条件2：顺序正确（低→高→回）
        if not (pos_min < pos_peak < t):
            t += 1
            continue
        # 条件3（回落信号）：当前价回到起涨位以下 且 月差走扩
        if not (x[t] <= x1 and y[t] > y[pos_min] + delta):
            t += 1
            continue
        # ---- 确认期：S 之后 confirm_w bar 内 ≥confirm_v 票 ----
        y1 = y[pos_min]
        votes = 0
        trigger_t = None
        for j in range(t + 1, min(t + 1 + confirm_w, n)):
            if x[j] <= x1 and y[j] > y1 + delta:
                votes += 1
                if votes >= confirm_v:
                    trigger_t = j
                    break
        if trigger_t is None:
            t += 1
            continue
        # 事件成立
        events.append({
            "anchor_pos": int(pos_min), "anchor_x": float(x1), "anchor_y": float(y1),
            "peak_pos": int(pos_peak), "peak_x": float(x_peak),
            "rally": float(x_peak - x1),
            "signal_pos": int(t),
            "trigger_pos": int(trigger_t),
            "y_at_trigger": float(y[trigger_t]),
            "y_expand": float(y[trigger_t] - y1),
        })
        # 前向观察 + 冷却
        cooldown_until = trigger_t + forward_N
        t = trigger_t + 1

    # ---- 前向观察 ----
    for ev in events:
        te = ev["trigger_pos"]
        if te + forward_N < n:
            y0 = y[te]
            fwd = y[te + 1: te + 1 + forward_N]
            ev["fwd_n"] = len(fwd)
            ev["fwd_dy_tN"] = float(y[te + forward_N] - y0)          # 终点净变化
            ev["fwd_dy_max"] = float(fwd.max() - y0)                  # 最高走扩（正值=继续走扩）
            ev["fwd_dy_min"] = float(fwd.min() - y0)                  # 最深收敛（负值=补跌）
            ev["fwd_dy_mean"] = float(fwd.mean() - y0)
            ev["fwd_dir"] = "走扩" if ev["fwd_dy_tN"] > 0 else "收敛"
        else:
            ev["fwd_n"] = None
    return events, n


def unconditional_baseline(y, forward_N, n, rng=None):
    """全样本无条件前向 N bar 月差变化分布（对照组）。"""
    ends = n - forward_N
    if ends <= 0:
        return []
    idx = np.arange(0, ends)
    if rng is not None and len(idx) > 5000:
        idx = rng.choice(idx, 5000, replace=False)
    out = [float(y[i + forward_N] - y[i]) for i in idx]
    return out


def summary(events, base, forward_N, tag=""):
    dys = [e["fwd_dy_tN"] for e in events if e.get("fwd_n")]
    if not dys:
        return None
    dys = np.array(dys)
    base = np.array(base)
    up = (dys > 0).mean()
    r = {
        "tag": tag, "n_events": len(events), "n_valid": len(dys),
        "mean_dy": float(dys.mean()), "median_dy": float(np.median(dys)),
        "std_dy": float(dys.std()),
        "pct_走扩": float(up),
        "base_mean": float(base.mean()),
        "base_median": float(np.median(base)),
        "base_pct_pos": float((base > 0).mean()),
        "excess_mean": float(dys.mean() - base.mean()),
        "excess_pct_走扩": float(up - (base > 0).mean()),
    }
    # 显著性：事件前向变化 vs 无条件
    if len(dys) >= 8 and len(base) >= 30:
        t_stat, p_val = stats.ttest_ind(dys, base, equal_var=False)
        r["ttest_t"] = float(t_stat)
        r["ttest_p"] = float(p_val)
        mw = stats.mannwhitneyu(dys, base, alternative="two-sided")
        r["mw_p"] = float(mw.pvalue)
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    df = load_pair()
    x, y = df.x.values, df.y.values
    n = len(x)
    rng = np.random.default_rng(42)
    base = unconditional_baseline(y, P["forward_N"], n, rng)

    # ---- 主口径 ----
    events, _ = detect_events(x, y, **{k: P[k] for k in
        ("L", "theta", "delta", "confirm_w", "confirm_v", "forward_N")})
    report = {
        "pair": "OCT26_NOV26 (CL2610-CL2611)",
        "granularity": "1h",
        "n_bars": n,
        "ts_start": str(df.ts.iloc[0]), "ts_end": str(df.ts.iloc[-1]),
        "params": P.copy(),
        "baseline": {"n": len(base), "mean": float(np.mean(base)),
                     "median": float(np.median(base)), "pct_pos": float((np.array(base) > 0).mean())},
        "events": events,
    }
    report["main_summary"] = summary(events, base, P["forward_N"], tag="main")

    # ---- 敏感性扫描 ----
    sens = []
    for theta in (1.0, 1.5, 2.5):
        for delta in (0.10, 0.15, 0.25):
            ev2, _ = detect_events(x, y, P["L"], theta, delta,
                                   P["confirm_w"], P["confirm_v"], P["forward_N"])
            s = summary(ev2, base, P["forward_N"], tag=f"θ={theta},δ={delta}")
            if s:
                sens.append(s)
    for Nd in (12, 24, 48):
        ev3, _ = detect_events(x, y, P["L"], P["theta"], P["delta"],
                               P["confirm_w"], P["confirm_v"], Nd)
        b3 = unconditional_baseline(y, Nd, n, rng)
        s = summary(ev3, b3, Nd, tag=f"N={Nd}")
        if s:
            sens.append(s)
    report["sensitivity"] = sens

    with open(os.path.join(OUT, "spread_divergence.json"), "w") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, default=str)

    # ---- 控制台摘要 ----
    print(f"bars={n}  {df.ts.iloc[0]} ~ {df.ts.iloc[-1]}")
    print(f"主口径事件: n={len(events)}  有效={sum(1 for e in events if e.get('fwd_n'))}")
    ms = report["main_summary"]
    if ms:
        for k in ("n_events", "n_valid", "mean_dy", "median_dy", "pct_走扩",
                  "base_mean", "base_pct_pos", "excess_mean", "excess_pct_走扩",
                  "ttest_p", "mw_p"):
            print(f"  {k} = {ms.get(k)}")
    print("\n敏感性：")
    for s in sens:
        print(f"  {s['tag']:<20} n={s['n_events']:>3} valid={s['n_valid']:>3} "
              f"mean_dy={s['mean_dy']:+.3f} pct走扩={s['pct_走扩']:.2f} "
              f"excess_mean={s['excess_mean']:+.3f}")


if __name__ == "__main__":
    main()