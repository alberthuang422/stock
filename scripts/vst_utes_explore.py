# -*- coding: utf-8 -*-
"""VST × UTES 分阶段相关性分析（探索版）
UTES = Virtus Reaves Utilities ETF（主动管理公用事业 ETF，VST 为其前三大持仓）
对照：XLU（S&P 500 Utilities ETF）
"""
import json
import math
import os

import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")


def load(ticker):
    f = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(f, parse_dates=["date"])
    df = df[["date", "adj_close"]].rename(columns={"adj_close": "close"})
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df


def ret_series(df):
    s = df.set_index("date")["close"]
    return s.pct_change().dropna()


def main():
    vst = load("VST")
    utes = load("UTES")
    xlu = load("XLU")

    start = max(vst["date"].min(), utes["date"].min(), xlu["date"].min())
    end = min(vst["date"].max(), utes["date"].max(), xlu["date"].max())
    print(f"统一窗口: {start.date()} ~ {end.date()}")

    def sl(df):
        return df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)

    vst_s, utes_s, xlu_s = sl(vst), sl(utes), sl(xlu)

    vst_r = ret_series(vst_s).rename("vst")
    utes_r = ret_series(utes_s).rename("utes")
    xlu_r = ret_series(xlu_s).rename("xlu")
    m = pd.concat([vst_r, utes_r, xlu_r], axis=1).dropna()

    # ---- 1. 全期相关 ----
    print("\n[1] 全期日收益相关")
    print(m.corr().round(3).to_string())
    print(f"  VST×UTES: {m['vst'].corr(m['utes']):.3f}  VST×XLU: {m['vst'].corr(m['xlu']):.3f}  UTES×XLU: {m['utes'].corr(m['xlu']):.3f}")

    # ---- 2. 滚动 60 日相关：结构变化 ----
    roll = pd.DataFrame({
        "vst_utes": m["vst"].rolling(60).corr(m["utes"]),
        "vst_xlu": m["vst"].rolling(60).corr(m["xlu"]),
        "utes_xlu": m["utes"].rolling(60).corr(m["xlu"]),
    })
    print("\n[2] 滚动60日相关统计")
    for c in roll.columns:
        print(f"  {c}: 均值 {roll[c].mean():.3f}  最新 {roll[c].iloc[-1]:.3f}  最大 {roll[c].max():.3f}  最小 {roll[c].min():.3f}")

    # 滚动相关的低点/高点时段
    print("\n  VST×UTES 滚动相关 <-0.2 或 阶段低点:")
    r = roll["vst_utes"].dropna()
    # 找滚动相关的局部低点（每 60 日内的最小值且低于 0.3）
    lows = []
    for i in range(60, len(r) - 60):
        win = r.iloc[i - 30:i + 30]
        if r.iloc[i] == win.min() and r.iloc[i] < 0.35:
            lows.append((r.index[i], r.iloc[i]))
    for d, v in lows[::3]:
        print(f"    {d.date()}  corr={v:.2f}")

    # ---- 3. 年度相关 + 年度收益 ----
    print("\n[3] 年度相关与收益")
    yrs = sorted(m.index.year.unique())
    print("  year | corr V×U | corr V×X | VST | UTES | XLU")
    for y in yrs:
        g = m[m.index.year == y]
        cs = m["vst"].loc[m.index.year == y]
        # 年度收益从价格算
        def yret(df, year):
            d = df[df["date"].dt.year == year]
            if len(d) < 2:
                return float("nan")
            return d["close"].iloc[-1] / d["close"].iloc[0] - 1
        print(f"  {y} | {g['vst'].corr(g['utes']):.2f} | {g['vst'].corr(g['xlu']):.2f} | "
              f"{yret(vst_s, y)*100:6.1f}% | {yret(utes_s, y)*100:6.1f}% | {yret(xlu_s, y)*100:6.1f}%")

    # ---- 4. 候选阶段（事件驱动）----
    phases = [
        ("S1", "2018-01-01", "2021-02-28", "合并前稳态期（德州暴风雪前）"),
        ("S2", "2021-03-01", "2022-10-31", "暴风雪损失+加息冲击期"),
        ("S3", "2022-11-01", "2024-08-31", "AI 电力叙事萌芽至发酵"),
        ("S4", "2024-09-01", "2025-12-31", "AI 电力主升浪（三里岛 PPA 后）"),
        ("S5", "2026-01-01", "2026-12-31", "AI 交易回调分化期"),
    ]
    print("\n[4] 候选阶段指标")
    for pid, p0, p1, desc in phases:
        p0t, p1t = pd.Timestamp(p0), pd.Timestamp(p1)
        g = m[(m.index >= p0t) & (m.index <= p1t)]
        if len(g) < 30:
            print(f"  {pid} {desc}: 样本不足 ({len(g)})")
            continue
        # β: vst ~ utes
        beta = g["vst"].cov(g["utes"]) / g["utes"].var()
        seesaw = (np.sign(g["vst"]) != np.sign(g["utes"])).mean()
        # 同向且都涨 / 都跌
        both_up = ((g["vst"] > 0) & (g["utes"] > 0)).mean()
        both_dn = ((g["vst"] < 0) & (g["utes"] < 0)).mean()

        def cret(df, p0t, p1t):
            d = df[(df["date"] >= p0t) & (df["date"] <= p1t)]
            return d["close"].iloc[-1] / d["close"].iloc[0] - 1 if len(d) > 1 else float("nan")

        v_c, u_c, x_c = cret(vst_s, p0t, p1t), cret(utes_s, p0t, p1t), cret(xlu_s, p0t, p1t)
        print(f"\n  {pid} {desc}")
        print(f"    区间 {g.index[0].date()} ~ {g.index[-1].date()}  n={len(g)}")
        print(f"    相关: V×U {g['vst'].corr(g['utes']):.3f}  V×X {g['vst'].corr(g['xlu']):.3f}  U×X {g['utes'].corr(g['xlu']):.3f}")
        print(f"    β(V~U) {beta:.2f} | 跷跷板 {seesaw*100:.1f}% | 同涨 {both_up*100:.1f}% 同跌 {both_dn*100:.1f}%")
        print(f"    收益: VST {v_c*100:+.1f}%  UTES {u_c*100:+.1f}%  XLU {x_c*100:+.1f}%  超额(V-U) {(v_c-u_c)*100:+.1f}pp")


if __name__ == "__main__":
    main()
