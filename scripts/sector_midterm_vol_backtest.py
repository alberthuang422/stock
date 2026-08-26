#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中期选举前标普板块 ETF 波动率放大研究 —— 板块维度事件研究

问题：哪个标普板块受中期选举影响最大（波动放大最明显）？

口径（与报告 37 SPY 版完全一致）：
- 波动率：vol10 = 日收益率(%, adj_close)的 10 交易日滚动标准差
- 基准：选举日前 121~180 个交易日 vol10 均值（与 ≤90 日前置窗口无时间重叠）
- 窗口：选举前 5/10/15/20/30/45/60/90 个交易日累积放大倍数
- 分段：前 1~30 / 31~60 / 61~90 日（段内独立标准差）
- 处理组：6 次中期选举（2002/2006/2010/2014/2018/2022）
- 对照组：13 个奇数年（无选举）+ 7 个总统大选年，伪事件日=当年 11 月第一个周一后的周二

板块覆盖：9 个板块 ETF 全史（1998~，6 次中期全含）；XLRE(2015~)/XLC(2018~) 仅含
2018/2022 两次（结果标注样本数）。

输出：
- results/sector_midterm_vol_trades.csv    板块×中期选举事件明细（58 行）
- results/sector_midterm_vol_stats.json    板块×窗口统计、对照、影响排序
- results/sector_midterm_vol_summary.json  事件级统计
"""
from __future__ import annotations

import json
import os
from datetime import date

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT_TRADES = os.path.join(ROOT, "results", "sector_midterm_vol_trades.csv")
OUT_STATS = os.path.join(ROOT, "results", "sector_midterm_vol_stats.json")
OUT_SUMMARY = os.path.join(ROOT, "results", "sector_midterm_vol_summary.json")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]
SEGS = [(1, 30), (31, 60), (61, 90)]

SECTORS = {
    "XLK": "科技", "XLE": "能源", "XLV": "医疗保健", "XLF": "金融",
    "XLP": "必需消费", "XLU": "公用事业", "XLI": "工业", "XLY": "可选消费",
    "XLB": "材料", "XLRE": "房地产", "XLC": "通信服务",
}
# 成立早于 2002 年首次中期选举 → 全史覆盖 6 次；否则只覆盖 2018/2022
FULL_HISTORY = {"XLK", "XLE", "XLV", "XLF", "XLP", "XLU", "XLI", "XLY", "XLB"}
GROUPS = {"midterm": "中期选举", "offyear": "奇数年(无选举)", "pres": "总统大选年"}


def first_tuesday_nov(y: int) -> date:
    """当年 11 月第一个周一之后的周二（美国选举日法定规则）。"""
    d1 = date(y, 11, 1)
    fm = 1 + (0 - d1.weekday()) % 7
    return date(y, 11, fm + 1)


MIDTERM = [first_tuesday_nov(y) for y in [2002, 2006, 2010, 2014, 2018, 2022]]
OFFYEAR = [first_tuesday_nov(y) for y in [2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]]
PRES = [first_tuesday_nov(y) for y in [2000, 2004, 2008, 2012, 2016, 2020, 2024]]


def load_series(sym: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA, sym.lower(), f"{sym}, 1D.csv"), parse_dates=["date"])
    df = df[["date", "adj_close"]].sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change() * 100.0
    df["vol10"] = df["ret"].rolling(10).std()
    return df


def analyze(df: pd.DataFrame, ev_date: date):
    mask = df["date"] <= pd.Timestamp(ev_date)
    if not mask.any():
        return None
    D = int(df.index[mask][-1])
    if D - 180 < 0:
        return None
    base = float(df.loc[D - 180:D - 121, "vol10"].mean())
    base_ret_std = float(df.loc[D - 180:D - 121, "ret"].std())
    sig = {k: float(df.loc[D - k:D - 1, "vol10"].mean()) / base for k in WINDOWS}
    seg = {f"s{a}_{b}": float(df.loc[D - b:D - a, "ret"].std()) / base_ret_std for a, b in SEGS}
    curve = {t: float(df.loc[D + t, "vol10"]) / base for t in range(-90, 0)}
    return D, base, sig, seg, curve


def main():
    os.makedirs(OUT_TRADES and os.path.dirname(OUT_TRADES), exist_ok=True)

    all_rows = []      # 板块×事件（三组全含，用于组内统计）
    for sym, name in SECTORS.items():
        df = load_series(sym)
        eligible = [d for d in MIDTERM if (df["date"] <= pd.Timestamp(d)).sum() > 180]
        specs = ([(d, "midterm", f"{sym} {d.year} 中期") for d in eligible]
                 + [(d, "offyear", f"{sym} {d.year} 奇数对照") for d in OFFYEAR if (df["date"] <= pd.Timestamp(d)).sum() > 180]
                 + [(d, "pres", f"{sym} {d.year} 大选对照") for d in PRES if (df["date"] <= pd.Timestamp(d)).sum() > 180])
        for d, g, lab in specs:
            r = analyze(df, d)
            if r is None:
                continue
            D, base, sig, seg, curve = r
            all_rows.append({
                "label": lab, "group": g, "sector": sym, "sector_name": name,
                "event_date": d.isoformat(),
                "entry_date": str(df.loc[D - 10, "date"].date()),
                "exit_date": str(df.loc[D, "date"].date()),
                "entry_price": round(float(df.loc[D - 10, "adj_close"]), 2),
                "exit_price": round(float(df.loc[D, "adj_close"]), 2),
                "pnl_pct": round((sig[10] - 1.0) * 100, 2),
                "base_vol": round(base, 3),
                **{f"v{k}": round((sig[k] - 1.0) * 100, 1) for k in WINDOWS},
                **{k: round((v - 1.0) * 100, 1) for k, v in seg.items()},
            })

    mid_rows = [r for r in all_rows if r["group"] == "midterm"]

    # ---- trades.csv：板块×中期选举 ----
    cols = ["label", "sector", "sector_name", "event_date", "entry_date", "exit_date",
            "entry_price", "exit_price", "pnl_pct", "base_vol"] + [f"v{k}" for k in WINDOWS] \
        + [f"s{a}_{b}" for a, b in SEGS]
    pd.DataFrame(mid_rows)[cols].to_csv(OUT_TRADES, index=False, encoding="utf-8")

    # ---- 板块统计（中期组）----
    sec_stats = {}
    for sym in SECTORS:
        rows = [r for r in mid_rows if r["sector"] == sym]
        s = {"n": len(rows), "years": [r["event_date"][:4] for r in rows]}
        for k in WINDOWS:
            vals = [r[f"v{k}"] for r in rows]
            s[f"v{k}"] = {"mean": round(float(np.mean(vals)), 1),
                          "median": round(float(np.median(vals)), 1),
                          "hit_p20": round(100.0 * np.mean([v >= 20 for v in vals]), 0)}
        for a, b in SEGS:
            vals = [r[f"s{a}_{b}"] for r in rows]
            s[f"s{a}_{b}"] = round(float(np.mean(vals)), 1)
        # 逐日平均曲线（用于对比图）
        curves = []
        for r in rows:
            dfx = load_series(sym)
            rr = analyze(dfx, date.fromisoformat(r["event_date"]))
            if rr:
                curves.append(rr[4])
        s["avg_curve"] = {str(t): round(float(np.mean([c[t] for c in curves])), 4) for t in range(-90, 0)} if curves else {}
        sec_stats[sym] = s

    # ---- 对照组板块统计（奇数年，v15/v20 主窗口）----
    ctrl = {}
    for sym in SECTORS:
        rows = [r for r in all_rows if r["group"] == "offyear" and r["sector"] == sym]
        ctrl[sym] = {"n": len(rows),
                     "v15": round(float(np.mean([r["v15"] for r in rows])), 1) if rows else None,
                     "v20": round(float(np.mean([r["v20"] for r in rows])), 1) if rows else None}

    # ---- 相对 SPY 的超额放大（v20）----
    spy_v20 = sec_stats["XLK"] and None  # SPY 不在板块列表，单独算
    df_spy = load_series("SPY")
    spy_v20_m, spy_v20_ctrl = [], []
    for d in MIDTERM:
        r = analyze(df_spy, d)
        if r:
            spy_v20_m.append((r[2][20] - 1.0) * 100)
    for d in OFFYEAR:
        r = analyze(df_spy, d)
        if r:
            spy_v20_ctrl.append((r[2][20] - 1.0) * 100)

    # ---- 排序：v20 平均放大最大→最小 ----
    ranking = sorted(
        [(sym, sec_stats[sym]["v20"]["mean"], sec_stats[sym]["v20"]["hit_p20"], sec_stats[sym]["n"])
         for sym in SECTORS],
        key=lambda x: -x[1],
    )

    # 显著性：板块 v20 中期组 vs 该板块奇数年组（Welch）
    sig_comp = {}
    for sym in SECTORS:
        m = [r["v20"] for r in mid_rows if r["sector"] == sym]
        o = [r["v20"] for r in all_rows if r["group"] == "offyear" and r["sector"] == sym]
        if len(m) >= 2 and len(o) >= 2:
            t, p = stats.ttest_ind(m, o, equal_var=False)
            sig_comp[sym] = {"t": round(float(t), 2), "p": round(float(p), 4)}
        else:
            sig_comp[sym] = {"t": None, "p": None}

    payload = {
        "meta": {
            "strategy_name": "中期选举前标普板块波动率放大（板块对比）",
            "sectors": SECTORS, "windows": WINDOWS,
            "report_kind": "event_study", "event_overview_mode": "stats",
            "full_history_sectors": sorted(FULL_HISTORY),
            "n_midterm_total": len(mid_rows),
        },
        "sectors": sec_stats,
        "control_offyear": ctrl,
        "spy": {"v20_midterm_mean": round(float(np.mean(spy_v20_m)), 1) if spy_v20_m else None,
                "v20_offyear_mean": round(float(np.mean(spy_v20_ctrl)), 1) if spy_v20_ctrl else None},
        "ranking": [{"symbol": s, "v20_mean": m, "hit_p20": h, "n": n} for s, m, h, n in ranking],
        "significance": sig_comp,
    }
    with open(OUT_STATS, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---- summary.json ----
    pnls = [r["pnl_pct"] for r in mid_rows]
    summary = {
        "meta": {"strategy_name": "中期选举前标普板块波动率放大（板块对比）",
                 "report_kind": "event_study", "pnl_pct_definition": "板块×事件：选举前10交易日波动放大%",
                 "generated_at": pd.Timestamp.now().isoformat()},
        "summary": {"total_trades": len(pnls),
                    "avg_return_pct": round(float(np.mean(pnls)), 2),
                    "median_return_pct": round(float(np.median(pnls)), 2),
                    "best_trade_pct": round(float(np.max(pnls)), 2),
                    "worst_trade_pct": round(float(np.min(pnls)), 2),
                    "win_rate_pct": round(100.0 * np.mean([p > 0 for p in pnls]), 1)},
    }
    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ---- 汇总打印 ----
    print(f"板块×中期选举事件数: {len(mid_rows)}")
    print("\n板块 v15/v20 平均放大% + ≥+20%命中率 + 对照(v20) + Welch p:")
    print("板块".ljust(8), "样本".ljust(6), "v15".rjust(7), "v20".rjust(7),
          "hit%".rjust(6), "对照v20".rjust(8), "p(v20)".rjust(8))
    for sym, m, h, n in ranking:
        c = ctrl[sym]["v20"]
        p = sig_comp[sym]["p"]
        print(f"{sym}({SECTORS[sym]})".ljust(8), str(n).ljust(6),
              str(sec_stats[sym]['v15']['mean']).rjust(7), str(m).rjust(7),
              str(int(h)).rjust(6), str(c).rjust(8), str(p).rjust(8))
    print(f"\nSPY v20: 中期平均 {payload['spy']['v20_midterm_mean']}% / 奇数年平均 {payload['spy']['v20_offyear_mean']}%")
    print("\n各板块 8 窗口放大% 矩阵:")
    hdr = "板块".ljust(8) + "".join(str(k).rjust(8) for k in WINDOWS)
    print(hdr)
    for sym in ranking:
        s = sec_stats[sym[0]]
        print(sym[0].ljust(8) + "".join(str(s[f"v{k}"]["mean"]).rjust(8) for k in WINDOWS))
    print(f"\nwritten: {OUT_TRADES} / {OUT_STATS} / {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
