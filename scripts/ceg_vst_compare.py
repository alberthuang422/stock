# -*- coding: utf-8 -*-
"""CEG vs VST 股价表现对比分析（基于 Yahoo 日线 adj_close）
窗口：两家同时有数据的区间（CEG 2022-01-19 上市起）
基准：XLU（公用事业板块）、SPY（大盘）
"""
import json
import math
import os

import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(BASE, "..", "results")


def load(ticker):
    f = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(f, parse_dates=["date"])
    df = df[["date", "adj_close"]].rename(columns={"adj_close": "close"})
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df


def ret_series(df):
    s = df.set_index("date")["close"]
    return s.pct_change().dropna()


def max_drawdown(close_series):
    cummax = close_series.cummax()
    dd = close_series / cummax - 1
    return dd.min()


def ann_vol(ret, periods=252):
    return ret.std() * math.sqrt(periods)


def main():
    ceg = load("CEG")
    vst = load("VST")
    xlu = load("XLU")
    spy = load("SPY")

    # 统一窗口：CEG 上市日 ~ 最新
    start = ceg["date"].min()
    end = min(ceg["date"].max(), vst["date"].max(), xlu["date"].max(), spy["date"].max())
    print(f"统一窗口: {start.date()} ~ {end.date()}")

    def slice_df(df):
        return df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)

    ceg_s, vst_s, xlu_s, spy_s = (slice_df(d) for d in (ceg, vst, xlu, spy))

    # ---- 1. 累计收益 ----
    def cum_ret(df):
        return df["close"].iloc[-1] / df["close"].iloc[0] - 1

    cr = {"start": str(start.date()), "end": str(end.date()),
          "ceg": cum_ret(ceg_s), "vst": cum_ret(vst_s), "xlu": cum_ret(xlu_s), "spy": cum_ret(spy_s)}
    print("\n[1] 区间累计收益(上市以来)")
    for k in ("ceg", "vst", "xlu", "spy"):
        print(f"  {k.upper()}: {cr[k]*100:.1f}%")

    # ---- 2. 年度收益（2022 全年 ~ 2026 YTD）----
    yearly = {}
    for k, df in (("ceg", ceg), ("vst", vst), ("xlu", xlu), ("spy", spy)):
        df = df.copy()
        df["year"] = df["date"].dt.year
        d = {}
        for y, g in df.groupby("year"):
            if y < 2022:
                continue
            d[int(y)] = g["close"].iloc[-1] / g["close"].iloc[0] - 1
        yearly[k] = d
    print("\n[2] 年度收益")
    years = sorted({y for d in yearly.values() for y in d})
    print("  year | " + " | ".join(f"{k.upper():>8}" for k in ("ceg", "vst", "xlu", "spy")))
    for y in years:
        row = [yearly[k].get(y, float("nan")) for k in ("ceg", "vst", "xlu", "spy")]
        print(f"  {y} | " + " | ".join(f"{v*100:7.1f}%" if not math.isnan(v) else f"{'-':>8}" for v in row))

    # ---- 3. 最大回撤 / 年化波动 ----
    stats = {}
    for k, df in (("ceg", ceg_s), ("vst", vst_s), ("xlu", xlu_s), ("spy", spy_s)):
        s = df.set_index("date")["close"]
        r = s.pct_change().dropna()
        stats[k] = {
            "max_drawdown": float(max_drawdown(s)),
            "ann_vol": float(ann_vol(r)),
            "ann_ret": float((s.iloc[-1] / s.iloc[0]) ** (252 / len(s)) - 1),
            "sharpe": float((s.iloc[-1] / s.iloc[0]) ** (252 / len(s)) - 1) / float(ann_vol(r)) if ann_vol(r) > 0 else None,
            "last_close": float(s.iloc[-1]),
        }
    print("\n[3] 风险指标（上市以来窗口）")
    for k, v in stats.items():
        print(f"  {k.upper()}: 最大回撤 {v['max_drawdown']*100:.1f}%  年化波动 {v['ann_vol']*100:.1f}%  年化收益 {v['ann_ret']*100:.1f}%  最新收盘 {v['last_close']:.2f}")

    # ---- 4. 相关性（日收益）----
    ceg_r = ret_series(ceg_s).rename("ceg")
    vst_r = ret_series(vst_s).rename("vst")
    xlu_r = ret_series(xlu_s).rename("xlu")
    spy_r = ret_series(spy_s).rename("spy")
    corr_df = pd.concat([ceg_r, vst_r, xlu_r, spy_r], axis=1).dropna()
    corr = corr_df.corr()
    print("\n[4] 日收益相关性矩阵")
    print(corr.round(3).to_string())
    corr_out = {a: {b: float(corr.loc[a, b]) for b in corr.columns} for a in corr.columns}

    # 滚动 60 日相关性 CEG-VST
    roll = corr_df["ceg"].rolling(60).corr(corr_df["vst"])
    roll_df = pd.DataFrame({"date": roll.index, "corr_60d": roll.values}).dropna()
    print(f"\n  滚动60日 CEG-VST 相关: 均值 {roll.mean():.3f} 最新 {roll.iloc[-1]:.3f}")

    # ---- 5. 相对强弱：CEG vs VST 比值曲线关键点 ----
    m = pd.DataFrame({"ceg": ceg_s.set_index("date")["close"],
                      "vst": vst_s.set_index("date")["close"]}).dropna()
    ratio = m["ceg"] / m["vst"]
    ratio_norm = ratio / ratio.iloc[0]
    print(f"\n[5] CEG/VST 相对强弱: 起始比值 {ratio.iloc[0]:.2f} 最新 {ratio.iloc[-1]:.2f} (归一化 {ratio_norm.iloc[-1]:.2f})")
    print(f"  比值最高点 {ratio_norm.max():.2f} ({ratio_norm.idxmax().date()})  最低点 {ratio_norm.min():.2f} ({ratio_norm.idxmin().date()})")

    # ---- 6. 2025/2026 关键事件窗口股价反应 ----
    events = [
        ("2024-09-20", "微软×CEG 三里岛(Crane)20年核能PPA"),
        ("2025-01-06", "CEG 宣布收购 Calpine"),
        ("2025-03-03", "AWS×VST Comanche Peak 20年核能PPA"),
        ("2025-07-23", "Meta×CEG Clinton 20年核能PPA"),
        ("2025-10-29", "VST 完成 Lotus 2600MW 气电收购"),
        ("2026-01-07", "CEG 完成收购 Calpine(约$220亿)"),
    ]
    # 事件窗口：事件日前后各3个交易日的累计收益
    ev_out = []
    for ed, name in events:
        edt = pd.Timestamp(ed)
        ev = {"date": ed, "name": name}
        for k, df in (("ceg", ceg_s), ("vst", vst_s)):
            s = df.set_index("date")["close"]
            idx = s.index.searchsorted(edt)
            ev[k] = "in_window"
            if idx <= 0 or idx >= len(s) - 1:
                ev[k] = None
                continue
            # 前3日
            w_before = s.iloc[max(0, idx - 3):idx]
            w_after = s.iloc[idx:min(len(s), idx + 4)]
            ev[k + "_pre3"] = float(w_before.iloc[-1] / w_before.iloc[0] - 1) if len(w_before) > 1 else None
            ev[k + "_post3"] = float(w_after.iloc[-1] / w_after.iloc[0] - 1) if len(w_after) > 1 else None
            ev[k + "_cum5"] = float(s.iloc[min(len(s) - 1, idx + 5)] / s.iloc[idx] - 1) if idx + 5 < len(s) else None
        ev_out.append(ev)
        print(f"\n  [{ed}] {name}")
        for k in ("ceg", "vst"):
            e = ev[k]
            if e is None:
                print(f"    {k.upper()}: 事件日不在窗口")
            else:
                print(f"    {k.upper()}: 前3日 {ev[k+'_pre3']*100:+.1f}%  事件日后3日 {ev[k+'_post3']*100:+.1f}%  后5日 {ev[k+'_cum5']*100:+.1f}%")

    # ---- 7. 走势点序列（供 ECharts 归一化曲线）----
    # 每 5 个交易日采样
    def norm_series(df):
        s = df.set_index("date")["close"]
        return pd.DataFrame({"date": s.index, "v": s / s.iloc[0]})

    seq = {}
    for k, df in (("ceg", ceg_s), ("vst", vst_s), ("xlu", xlu_s), ("spy", spy_s)):
        ns = norm_series(df)
        seq[k] = {"dates": [d.strftime("%Y-%m-%d") for d in ns["date"][::5]],
                  "values": [float(v) for v in ns["v"][::5]]}

    # 年度收益序列（图）
    year_chart = {"years": years,
                  "ceg": [round(yearly["ceg"].get(y, float("nan")) * 100, 2) for y in years],
                  "vst": [round(yearly["vst"].get(y, float("nan")) * 100, 2) for y in years],
                  "xlu": [round(yearly["xlu"].get(y, float("nan")) * 100, 2) for y in years],
                  "spy": [round(yearly["spy"].get(y, float("nan")) * 100, 2) for y in years]}

    # 滚动相关性序列（图）
    roll_chart = {"dates": [d.strftime("%Y-%m-%d") for d in roll_df["date"][::10]],
                  "values": [round(float(v), 3) for v in roll_df["corr_60d"][::10]]}

    result = {
        "window": cr,
        "cum_ret": cr,
        "yearly": year_chart,
        "risk": stats,
        "corr_matrix": corr_out,
        "corr_roll": {"mean": float(roll.mean()), "latest": float(roll.iloc[-1])},
        "ratio": {"start": float(ratio.iloc[0]), "latest": float(ratio.iloc[-1]),
                  "norm_latest": float(ratio_norm.iloc[-1]),
                  "max": float(ratio_norm.max()), "max_date": str(ratio_norm.idxmax().date()),
                  "min": float(ratio_norm.min()), "min_date": str(ratio_norm.idxmin().date())},
        "events": ev_out,
        "norm_series": seq,
        "roll_chart": roll_chart,
    }
    with open(os.path.join(OUT, "ceg_vst_price.json"), "w") as f:
        json.dump(result, f, indent=1, default=str)
    print("\n结果已保存 results/ceg_vst_price.json")


if __name__ == "__main__":
    main()
