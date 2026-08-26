#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中期选举前标普500（SPY）波动率放大研究 —— 事件研究

问题：2000 年以后，距离中期选举多久之前，标普500 波动率会明显变大？

设计（事件研究，无资金/仓位模拟）：
- 数据：data/spy/SPY, 1D.csv（Yahoo 日线，1995~2026，adj_close 复权），SPY 作为标普500代理
- 处理组：6 次中期选举（2002/2006/2010/2014/2018/2022，选举日=当年 11 月第一个周二）
- 对照组1：13 个奇数年（2001~2025，无联邦选举），伪事件日=当年 11 月第一个周二
- 对照组2：7 个总统大选年（2000~2024），伪事件日=当年 11 月第一个周二
- 波动率：vol10 = 日收益率(%,adj_close)的 10 交易日滚动标准差
- 基准 σ_base：事件日前 121~180 个交易日的 vol10 均值（约 3 个月前的平静水平，
  与任何 ≤90 交易日的前置窗口无时间重叠，避免"窗口吃了基准"）
- 放大倍数：各前置窗口（选举前 5/10/15/20/30/45/60/90 个交易日）vol10 均值 / σ_base
- 分段（完全无重叠）：选举前 1~30 / 31~60 / 61~90 交易日段内 ret 标准差 vs
  基准段（前 121~180 交易日）段内 ret 标准差
- 逐日曲线：选举前 t 个交易日（t=90..1）当日 vol10 / σ_base，跨事件平均

输出：
- results/midterm_vol_trades.csv        6 行中期选举事件明细（pnl_pct=-10日窗口放大%）
- results/midterm_vol_all_events.csv   26 行全部事件（含两组对照）
- results/midterm_vol_group_stats.json 三组 × 各窗口统计（均值/中位/t/p）+ 逐日平均曲线
- reports/37_中期选举波动率/*.png      matplotlib 图（3 张）
"""
from __future__ import annotations

import json
import os
from datetime import date

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "spy", "SPY, 1D.csv")
OUT_TRADES = os.path.join(ROOT, "results", "midterm_vol_trades.csv")
OUT_ALL = os.path.join(ROOT, "results", "midterm_vol_all_events.csv")
OUT_SUMMARY = os.path.join(ROOT, "results", "midterm_vol_summary.json")
OUT_STATS = os.path.join(ROOT, "results", "midterm_vol_group_stats.json")
OUT_DIR = os.path.join(ROOT, "reports", "37_中期选举波动率")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]          # 累积窗口（交易日）
SEGS = [(1, 30), (31, 60), (61, 90)]                # 分段（交易日区间，段内独立std）
BASE_LO, BASE_HI = 121, 180                         # 基准段：前 121~180 交易日

GROUPS = {
    "midterm": "中期选举",
    "offyear": "奇数年(无选举)",
    "pres": "总统大选年",
}


def first_tuesday_nov(y: int) -> date:
    """当年 11 月第一个周一之后的周二（美国选举日法定规则：the Tuesday next
    after the first Monday in November）。注意不是"11 月第一个周二"——
    后者在 2016(大选)/2022(中期) 会差一周。"""
    d1 = date(y, 11, 1)
    first_monday = 1 + (0 - d1.weekday()) % 7
    return date(y, 11, first_monday + 1)


MIDTERM_DATES = [first_tuesday_nov(y) for y in [2002, 2006, 2010, 2014, 2018, 2022]]
OFFYEAR_DATES = [first_tuesday_nov(y) for y in [2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]]
PRES_DATES = [first_tuesday_nov(y) for y in [2000, 2004, 2008, 2012, 2016, 2020, 2024]]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["date"])
    df = df[["date", "adj_close"]].sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change() * 100.0          # 日收益率（%）
    df["vol10"] = df["ret"].rolling(10).std()                 # 10 日滚动波动率（日化 %）
    return df


def event_index(df: pd.DataFrame, ev_date: date) -> int:
    mask = df["date"] <= pd.Timestamp(ev_date)
    pos = df.index[mask]
    if len(pos) == 0:
        raise ValueError(f"事件日 {ev_date} 无前置数据")
    return int(pos[-1])


def analyze(df: pd.DataFrame, ev_date: date):
    """返回 (基准波动率, 各窗口放大倍数, 分段倍数, 逐日曲线)。"""
    D = event_index(df, ev_date)
    base = float(df.loc[D - BASE_HI:D - BASE_LO, "vol10"].mean())
    base_ret_std = float(df.loc[D - BASE_HI:D - BASE_LO, "ret"].std())

    sig = {k: float(df.loc[D - k:D - 1, "vol10"].mean()) / base for k in WINDOWS}
    seg = {f"seg{a}_{b}": float(df.loc[D - b:D - a, "ret"].std()) / base_ret_std
           for a, b in SEGS}
    curve = {t: float(df.loc[D + t, "vol10"]) / base for t in range(-90, 0)}
    return D, base, sig, seg, curve


def make_row(df: pd.DataFrame, ev_date: date, group: str, label: str) -> dict:
    D, base, sig, seg, _ = analyze(df, ev_date)
    pnl_pct = (sig[10] - 1.0) * 100.0           # 主指标：选举前 10 个交易日波动放大 %
    return {
        "label": label,
        "group": group,
        "group_name": GROUPS[group],
        "event_date": ev_date.isoformat(),
        "entry_date": str(df.loc[D - 10, "date"].date()),
        "exit_date": str(df.loc[D, "date"].date()),
        "entry_price": round(float(df.loc[D - 10, "adj_close"]), 2),
        "exit_price": round(float(df.loc[D, "adj_close"]), 2),
        "pnl_pct": round(pnl_pct, 2),
        "base_vol": round(base, 3),
        **{f"v{k}": round((sig[k] - 1.0) * 100, 1) for k in WINDOWS},
        **{k.replace("seg", "s"): round((v - 1.0) * 100, 1) for k, v in seg.items()},
    }


def ttest_vs_zero(vals: list[float]):
    """单样本 t 检验（H0: 均值=0，即放大倍数为 1）。"""
    vals = np.asarray(vals, dtype=float)
    n = len(vals)
    mean = float(vals.mean())
    sd = float(vals.std(ddof=1))
    if n < 2 or sd == 0:
        return {"mean": round(mean, 1), "t": None, "p": None, "n": n}
    t = mean / (sd / np.sqrt(n))
    p = float(stats.t.sf(abs(t), n - 1) * 2)
    return {"mean": round(mean, 1), "t": round(float(t), 2), "p": round(p, 4), "n": n}


def welch_ttest(a: list[float], b: list[float]):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return {"t": round(float(t), 2), "p": round(float(p), 4)}


def group_stats(rows: list[dict]) -> dict:
    out = {"n": len(rows)}
    for k in WINDOWS:
        vals = [r[f"v{k}"] for r in rows]
        out[f"v{k}"] = ttest_vs_zero(vals)
    for a, b in SEGS:
        key = f"seg{a}_{b}"
        vals = [r[key.replace("seg", "s")] for r in rows]
        out[key] = ttest_vs_zero(vals)
    # 逐日平均放大曲线（跨事件平均）
    curves = []
    for r in rows:
        _, _, _, _, c = analyze(load_cache, date.fromisoformat(r["event_date"]))
        curves.append(c)
    avg_curve = {}
    if curves:
        for t in range(-90, 0):
            avg_curve[str(t)] = round(float(np.mean([c[t] for c in curves])), 4)
    out["avg_curve"] = avg_curve
    return out


load_cache = None  # 占位，实际在 main 中赋值


def main():
    global load_cache
    df = load_data()
    load_cache = df
    os.makedirs(OUT_DIR, exist_ok=True)

    specs = (
        [(d, "midterm", f"{d.year} 中期选举") for d in MIDTERM_DATES]
        + [(d, "offyear", f"{d.year} 奇数年对照") for d in OFFYEAR_DATES]
        + [(d, "pres", f"{d.year} 大选年对照") for d in PRES_DATES]
    )
    all_rows = [make_row(df, d, g, lab) for d, g, lab in specs]
    midterm_rows = [r for r in all_rows if r["group"] == "midterm"]

    # ---- 写 trades.csv（事件研究，6 行中期选举）----
    cols = ["label", "group_name", "event_date", "entry_date", "exit_date",
            "entry_price", "exit_price", "pnl_pct", "base_vol"]
    for k in WINDOWS:
        cols.append(f"v{k}")
    for a, b in SEGS:
        cols.append(f"s{a}_{b}")
    pd.DataFrame(midterm_rows)[cols].to_csv(OUT_TRADES, index=False, encoding="utf-8")

    # ---- 写 all_events.csv（26 行，含对照）----
    pd.DataFrame(all_rows)[cols].to_csv(OUT_ALL, index=False, encoding="utf-8")

    # ---- 组统计 ----
    gs = {g: group_stats([r for r in all_rows if r["group"] == g]) for g in GROUPS}

    # 组间对比（中期 vs 奇数年 / 中期 vs 大选年），各窗口
    comp = {}
    for k in WINDOWS:
        m = [r[f"v{k}"] for r in midterm_rows]
        o = [r[f"v{k}"] for r in all_rows if r["group"] == "offyear"]
        p = [r[f"v{k}"] for r in all_rows if r["group"] == "pres"]
        comp[f"v{k}"] = {
            "midterm_vs_offyear": welch_ttest(m, o),
            "midterm_vs_pres": welch_ttest(m, p),
        }
    for a, b in SEGS:
        key = f"seg{a}_{b}"
        m = [r[key.replace("seg", "s")] for r in midterm_rows]
        o = [r[key.replace("seg", "s")] for r in all_rows if r["group"] == "offyear"]
        p = [r[key.replace("seg", "s")] for r in all_rows if r["group"] == "pres"]
        comp[key] = {
            "midterm_vs_offyear": welch_ttest(m, o),
            "midterm_vs_pres": welch_ttest(m, p),
        }

    # 二项检验：中期组放大 ≥ +20%（v10）的次数 vs 奇数年放大率
    offy_rate = np.mean([r["v10"] >= 20 for r in all_rows if r["group"] == "offyear"])
    m_k = sum(1 for r in midterm_rows if r["v10"] >= 20)
    m_n = len(midterm_rows)
    binom_p = float(stats.binom.sf(m_k - 1, m_n, offy_rate))  # P(X>=m_k)
    binom = {"midterm_hits": m_k, "midterm_n": m_n, "offyear_rate": round(offy_rate, 3),
             "binom_p_vs_offyear": round(binom_p, 4)}

    payload = {
        "meta": {
            "strategy_name": "中期选举前标普500波动率放大（事件研究）",
            "symbol": "SPY",
            "start": "2000-11-07", "end": "2025-11-04",
            "market": "us", "report_kind": "event_study",
            "event_overview_mode": "stats",
            "n_midterm": len(midterm_rows), "n_offyear": 13, "n_pres": 7,
            "windows": WINDOWS,
        },
        "groups": gs,
        "comparisons": comp,
        "binomial": binom,
    }
    with open(OUT_STATS, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---- 事件级 summary.json（事件研究口径：无 Sharpe/回撤）----
    pnls = [r["pnl_pct"] for r in midterm_rows]
    summary = {
        "meta": {
            "strategy_name": "中期选举前标普500波动率放大（事件研究）",
            "symbol": "SPY", "start": "2000-11-05", "end": "2025-11-04",
            "market": "us", "report_kind": "event_study",
            "event_overview_mode": "stats",
            "pnl_pct_definition": "选举前10个交易日平均波动率相对基准的放大%",
            "generated_at": pd.Timestamp.now().isoformat(),
        },
        "summary": {
            "total_trades": len(pnls),
            "avg_return_pct": round(float(np.mean(pnls)), 2),
            "median_return_pct": round(float(np.median(pnls)), 2),
            "best_trade_pct": round(float(np.max(pnls)), 2),
            "worst_trade_pct": round(float(np.min(pnls)), 2),
            "win_rate_pct": round(100.0 * np.mean([p > 0 for p in pnls]), 1),
        },
    }
    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ---- 汇总打印 ----
    print(f"事件数: 中期选举 {len(midterm_rows)} / 奇数年对照 13 / 大选年对照 7")
    print("\n累积窗口平均波动放大倍数（均值%，vs 基准=0%）:")
    hdr = "窗口(前N交易日)".ljust(12) + "".join(str(k).rjust(8) for k in WINDOWS)
    print(hdr)
    for g in GROUPS:
        line = GROUPS[g].ljust(12)
        for k in WINDOWS:
            line += str(gs[g][f"v{k}"]["mean"]).rjust(8)
        print(line)
    print("\n分段（段内独立std，放大%）：")
    for a, b in SEGS:
        line = f"前{a}-{b}日".ljust(12)
        for g in GROUPS:
            line += f"{GROUPS[g][:6]}:{gs[g][f'seg{a}_{b}']['mean']} ".rjust(10)
        print(line)
    print("\n中期 vs 奇数年 差异显著性(p):")
    for k in WINDOWS:
        c = comp[f"v{k}"]["midterm_vs_offyear"]
        print(f"  v{k:>3}: t={c['t']}, p={c['p']}")
    print(f"\n二项检验: 中期 v10≥+20% 次数 {binom['midterm_hits']}/{binom['midterm_n']}, "
          f"奇数年率 {binom['offyear_rate']}, 二项p={binom['binom_p_vs_offyear']}")

    # ---- 持续抬升判定（跨事件平均曲线）----
    # 口径1：找平均放大 ≥ 阈值的最长窗口（起点 t 最负，即最早进入高位区）
    # 口径2：找平均放大最大的窗口起点（峰值窗口）
    print("\n持续抬升判定（跨事件平均曲线）:")
    for g in GROUPS:
        curve = gs[g]["avg_curve"]
        longest = None
        for thr in (1.2, 1.3):
            for t in range(-90, 0):
                seg = [curve[str(tt)] for tt in range(t, 0)]
                if np.mean(seg) >= thr:
                    longest = (thr, t)
                    break
            if longest:
                thr, t = longest
                print(f"  {GROUPS[g]}: 平均≥×{thr} 的最长窗口 = 选举前 {abs(t)} 个交易日")
            else:
                print(f"  {GROUPS[g]}: 平均≥×{thr} 的最长窗口 = 无")
        best_t, best_m = None, 0.0
        for t in range(-90, 0):
            seg = [curve[str(tt)] for tt in range(t, 0)]
            m = float(np.mean(seg))
            if m > best_m:
                best_m, best_t = m, t
        if best_t:
            print(f"  {GROUPS[g]}: 峰值窗口 = 选举前 {abs(best_t)} 个交易日（平均 ×{best_m:.3f}）")

    print(f"\nwritten: {OUT_TRADES} / {OUT_ALL} / {OUT_SUMMARY} / {OUT_STATS}")


if __name__ == "__main__":
    main()
