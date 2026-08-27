#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIX 中期选举前抬升研究 —— 事件研究（对照报告 37 的 SPY 口径）

问题：中期选举前，VIX（隐含波动率）相对平静期抬升多少？与 SPY 已实现波动率放大的时序是否同源？

设计（与 midterm_vol_backtest.py 完全同口径，仅指标换成 VIX）：
- 数据：data/vix/VIX, 1D.csv（Yahoo 日线，1995~2026，close）
- 处理组：6 次中期选举（2002/2006/2010/2014/2018/2022，选举日=当年 11 月第一个周一后的周二）
- 对照组1：13 个奇数年（无联邦选举）
- 对照组2：7 个总统大选年
- 指标 Im：VIX 收盘价的 10 交易日滚动均值（平滑，避免单日尖峰抖动）
- 基准 σ_base：事件日前 121~180 个交易日的 Im 均值（约 3 个月前平静水平）
- 抬升倍数：各前置窗口（5/10/15/20/30/45/60/90）Im 均值 / σ_base
- 分段：前 1~30 / 31~60 / 61~90 交易日段内 Im 均值 / 基准均值
- 逐日曲线：事件前 t 个交易日（t=90..1）Im / σ_base，跨事件平均
- 补充：每个事件窗口内 VIX 绝对峰值（max high）与窗口 VIX 均值

输出：
- results/vix_midterm_vol_trades.csv        6 行中期事件明细
- results/vix_midterm_vol_all_events.csv   26 行（含对照）
- results/vix_midterm_vol_group_stats.json 三组 × 窗口统计 + 逐日曲线
- reports/42_VIX中期选举抬升/*.png         3 张图（放大曲线/窗口对比/个体）
"""
from __future__ import annotations

import json
import os
from datetime import date

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "vix", "VIX, 1D.csv")
OUT_TRADES = os.path.join(ROOT, "results", "vix_midterm_vol_trades.csv")
OUT_ALL = os.path.join(ROOT, "results", "vix_midterm_vol_all_events.csv")
OUT_STATS = os.path.join(ROOT, "results", "vix_midterm_vol_group_stats.json")
OUT_DIR = os.path.join(ROOT, "reports", "42_VIX中期选举抬升")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]
SEGS = [(1, 30), (31, 60), (61, 90)]
BASE_LO, BASE_HI = 121, 180

GROUPS = {"midterm": "中期选举", "offyear": "奇数年(无选举)", "pres": "总统大选年"}


def first_tuesday_nov(y: int) -> date:
    """当年 11 月第一个周一之后的周二（美国选举日法定规则）。"""
    d1 = date(y, 11, 1)
    first_monday = 1 + (0 - d1.weekday()) % 7
    return date(y, 11, first_monday + 1)


MIDTERM_DATES = [first_tuesday_nov(y) for y in [2002, 2006, 2010, 2014, 2018, 2022]]
OFFYEAR_DATES = [first_tuesday_nov(y) for y in [2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]]
PRES_DATES = [first_tuesday_nov(y) for y in [2000, 2004, 2008, 2012, 2016, 2020, 2024]]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["date"])
    df = df[["date", "close", "high"]].sort_values("date").reset_index(drop=True)
    # 10 日滚动均值平滑 VIX（对齐报告37的 vol10 窗口感）
    df["im"] = df["close"].rolling(10).mean()
    return df


def event_index(df: pd.DataFrame, ev_date: date) -> int:
    mask = df["date"] <= pd.Timestamp(ev_date)
    pos = df.index[mask]
    if len(pos) == 0:
        raise ValueError(f"事件日 {ev_date} 无前置数据")
    return int(pos[-1])


def analyze(df: pd.DataFrame, ev_date: date):
    D = event_index(df, ev_date)
    base = float(df.loc[D - BASE_HI:D - BASE_LO, "im"].mean())
    base_raw = float(df.loc[D - BASE_HI:D - BASE_LO, "close"].mean())

    sig = {k: float(df.loc[D - k:D - 1, "im"].mean()) / base for k in WINDOWS}
    seg = {f"seg{a}_{b}": float(df.loc[D - b:D - a, "im"].mean()) / base for a, b in SEGS}
    curve = {t: float(df.loc[D + t, "im"]) / base for t in range(-90, 0)}
    win_abs = {k: {"mean": float(df.loc[D - k:D - 1, "close"].mean()),
                   "max": float(df.loc[D - k:D - 1, "high"].max())} for k in WINDOWS}
    return D, base, base_raw, sig, seg, curve, win_abs


def make_row(df: pd.DataFrame, ev_date: date, group: str, label: str) -> dict:
    D, base, base_raw, sig, seg, _, win_abs = analyze(df, ev_date)
    pnl_pct = (sig[10] - 1.0) * 100.0
    return {
        "label": label,
        "group": group,
        "group_name": GROUPS[group],
        "event_date": ev_date.isoformat(),
        "entry_date": str(df.loc[D - 10, "date"].date()),
        "exit_date": str(df.loc[D, "date"].date()),
        "base_vix": round(base_raw, 2),
        "pnl_pct": round(pnl_pct, 2),
        "win10_mean_vix": round(win_abs[10]["mean"], 2),
        "win10_max_vix": round(win_abs[10]["max"], 2),
        "win20_max_vix": round(win_abs[20]["max"], 2),
        **{f"v{k}": round((sig[k] - 1.0) * 100, 1) for k in WINDOWS},
        **{k.replace("seg", "s"): round((v - 1.0) * 100, 1) for k, v in seg.items()},
    }


def ttest_vs_zero(vals: list[float]):
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


def group_stats(rows: list[dict], df: pd.DataFrame) -> dict:
    out = {"n": len(rows)}
    for k in WINDOWS:
        out[f"v{k}"] = ttest_vs_zero([r[f"v{k}"] for r in rows])
    for a, b in SEGS:
        out[f"seg{a}_{b}"] = ttest_vs_zero([r[f"s{a}_{b}"] for r in rows])
    curves = []
    for r in rows:
        _, _, _, _, _, c, _ = analyze(df, date.fromisoformat(r["event_date"]))
        curves.append(c)
    avg_curve = {}
    if curves:
        for t in range(-90, 0):
            avg_curve[str(t)] = round(float(np.mean([c[t] for c in curves])), 4)
    out["avg_curve"] = avg_curve
    return out


def main():
    df = load_data()
    os.makedirs(OUT_DIR, exist_ok=True)

    specs = (
        [(d, "midterm", f"{d.year} 中期选举") for d in MIDTERM_DATES]
        + [(d, "offyear", f"{d.year} 奇数年对照") for d in OFFYEAR_DATES]
        + [(d, "pres", f"{d.year} 大选年对照") for d in PRES_DATES]
    )
    all_rows = [make_row(df, d, g, lab) for d, g, lab in specs]
    midterm_rows = [r for r in all_rows if r["group"] == "midterm"]

    cols = ["label", "group_name", "event_date", "entry_date", "exit_date",
            "base_vix", "pnl_pct", "win10_mean_vix", "win10_max_vix", "win20_max_vix"]
    for k in WINDOWS:
        cols.append(f"v{k}")
    for a, b in SEGS:
        cols.append(f"s{a}_{b}")
    pd.DataFrame(midterm_rows)[cols].to_csv(OUT_TRADES, index=False, encoding="utf-8")
    pd.DataFrame(all_rows)[cols].to_csv(OUT_ALL, index=False, encoding="utf-8")

    gs = {g: group_stats([r for r in all_rows if r["group"] == g], df) for g in GROUPS}

    comp = {}
    for k in WINDOWS:
        m = [r[f"v{k}"] for r in midterm_rows]
        o = [r[f"v{k}"] for r in all_rows if r["group"] == "offyear"]
        p = [r[f"v{k}"] for r in all_rows if r["group"] == "pres"]
        comp[f"v{k}"] = {
            "midterm_vs_offyear": welch_ttest(m, o),
            "midterm_vs_pres": welch_ttest(m, p),
        }

    offy_rate = np.mean([r["v10"] >= 20 for r in all_rows if r["group"] == "offyear"])
    m_k = sum(1 for r in midterm_rows if r["v10"] >= 20)
    m_n = len(midterm_rows)
    binom_p = float(stats.binom.sf(m_k - 1, m_n, offy_rate))
    binom = {"midterm_hits": m_k, "midterm_n": m_n, "offyear_rate": round(offy_rate, 3),
             "binom_p_vs_offyear": round(binom_p, 4)}

    payload = {
        "meta": {
            "strategy_name": "VIX中期选举前抬升（事件研究）",
            "symbol": "VIX",
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

    print(f"事件数: 中期选举 {len(midterm_rows)} / 奇数年对照 13 / 大选年对照 7")
    print("\n累积窗口 VIX 抬升（均值%，vs 基准=0%）:")
    hdr = "窗口(前N交易日)".ljust(12) + "".join(str(k).rjust(8) for k in WINDOWS)
    print(hdr)
    for g in GROUPS:
        line = GROUPS[g].ljust(12)
        for k in WINDOWS:
            line += str(gs[g][f"v{k}"]["mean"]).rjust(8)
        print(line)
    print("\n分段（VIX 均值 / 基准）：")
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

    print("\n6 次中期事件明细:")
    for r in midterm_rows:
        print(f"  {r['event_date']}: base={r['base_vix']} v10={r['v10']}% "
              f"v20={r['v20']}% | 前10日VIX均值={r['win10_mean_vix']} 峰值={r['win10_max_vix']}")

    print("\n持续抬升判定:")
    for g in GROUPS:
        curve = gs[g]["avg_curve"]
        best_t, best_m = None, 0.0
        for t in range(-90, 0):
            seg = [curve[str(tt)] for tt in range(t, 0)]
            m = float(np.mean(seg))
            if m > best_m:
                best_m, best_t = m, t
        if best_t:
            print(f"  {GROUPS[g]}: 峰值窗口 = 选举前 {abs(best_t)} 个交易日（平均 ×{best_m:.3f}）")

    print(f"\nwritten: {OUT_TRADES} / {OUT_ALL} / {OUT_STATS}")


if __name__ == "__main__":
    main()