# -*- coding: utf-8 -*-
"""CSCO × BUG 相关性分析（仅 2026 年以来）
BUG = Global X Cybersecurity ETF（网络安全主题）
对照基准：SPY（大盘）
核心问题：思科（网络设备+安全转型）是否与网络安全主题同步？
"""
import json
import math
import os

import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(BASE, "..", "results")

START = "2026-01-01"


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


def clean(v):
    """NaN/inf -> None，np 标量转原生"""
    if v is None:
        return None
    if isinstance(v, (float, np.floating)):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(float(v), 6)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def main():
    csco = load("CSCO")
    bug = load("BUG")
    spy = load("SPY")

    start = pd.Timestamp(START)
    end = min(csco["date"].max(), bug["date"].max(), spy["date"].max())

    def slice_df(df):
        return df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)

    cs, bs, ss = (slice_df(d) for d in (csco, bug, spy))
    n = len(cs)
    print(f"统一窗口: {cs['date'].iloc[0].date()} ~ {cs['date'].iloc[-1].date()}  ({n} 个交易日)")

    # ---- 1. 收益表现 ----
    def cum_ret(df):
        return df["close"].iloc[-1] / df["close"].iloc[0] - 1

    cu = {"csco": cum_ret(cs), "bug": cum_ret(bs), "spy": cum_ret(ss)}
    print("\n[1] 2026YTD 累计收益")
    for k in ("csco", "bug", "spy"):
        print(f"  {k.upper()}: {cu[k]*100:+.1f}%")

    # 超额（累计，pp）
    ex = {
        "csco_vs_spy": cu["csco"] - cu["spy"],
        "bug_vs_spy": cu["bug"] - cu["spy"],
        "csco_vs_bug": cu["csco"] - cu["bug"],
    }
    print("  超额 CSCO-SPY: %+.1fpp  BUG-SPY: %+.1fpp  CSCO-BUG: %+.1fpp" % tuple(v * 100 for v in ex.values()))

    # ---- 2. 风险指标 ----
    stats = {}
    for k, df in (("csco", cs), ("bug", bs), ("spy", ss)):
        s = df.set_index("date")["close"]
        r = s.pct_change().dropna()
        stats[k] = {
            "max_drawdown": clean(max_drawdown(s)),
            "ann_vol": clean(r.std() * math.sqrt(252)),
            "ann_ret": clean((s.iloc[-1] / s.iloc[0]) ** (252 / len(s)) - 1),
            "last_close": clean(s.iloc[-1]),
        }
    print("\n[2] 风险指标")
    for k, v in stats.items():
        print(f"  {k.upper()}: 最大回撤 {v['max_drawdown']*100:.1f}%  年化波动 {v['ann_vol']*100:.1f}%  年化收益 {v['ann_ret']*100:+.1f}%")

    # ---- 3. 相关性 ----
    cr_ = ret_series(cs).rename("csco")
    br = ret_series(bs).rename("bug")
    sr = ret_series(ss).rename("spy")
    j = pd.concat([cr_, br, sr], axis=1).dropna()
    corr = j.corr()
    corr_full = {
        "csco_bug": clean(corr.loc["csco", "bug"]),
        "csco_spy": clean(corr.loc["csco", "spy"]),
        "bug_spy": clean(corr.loc["bug", "spy"]),
    }
    print("\n[3] 日收益相关(2026以来)")
    print(corr.round(3).to_string())

    # 滚动 30/60 日相关（CSCO×BUG + CSCO×SPY 对照）
    roll60_cb = j["csco"].rolling(60).corr(j["bug"])
    roll60_cs = j["csco"].rolling(60).corr(j["spy"])
    roll30_cb = j["csco"].rolling(30).corr(j["bug"])
    rdf = pd.DataFrame({
        "date": roll60_cb.index,
        "cb60": roll60_cb.values, "cs60": roll60_cs.values,
        "cb30": roll30_cb.values,
    }).dropna()
    print(f"\n  滚动60日 CSCO×BUG: 均值 {roll60_cb.mean():.3f} 最新 {roll60_cb.iloc[-1]:.3f}  区间[{roll60_cb.min():.3f},{roll60_cb.max():.3f}]")
    print(f"  滚动60日 CSCO×SPY: 均值 {roll60_cs.mean():.3f} 最新 {roll60_cs.iloc[-1]:.3f}")

    # ---- 4. 月度收益 + 月度相关 ----
    mdf = pd.DataFrame({"date": j.index, "csco": j["csco"], "bug": j["bug"], "spy": j["spy"]})
    mdf["ym"] = mdf["date"].dt.to_period("M")
    monthly = []
    for ym, g in mdf.groupby("ym"):
        rec = {
            "month": str(ym),
            "ret_csco": clean(g["csco"].sum() * 100),
            "ret_bug": clean(g["bug"].sum() * 100),
            "ret_spy": clean(g["spy"].sum() * 100),
            "corr_cb": clean(g["csco"].corr(g["bug"])),  # 月度内日收益相关
            "n": int(len(g)),
        }
        monthly.append(rec)
        print(f"  {ym}: CSCO {rec['ret_csco']:+.1f}%  BUG {rec['ret_bug']:+.1f}%  SPY {rec['ret_spy']:+.1f}%  月内相关 {rec['corr_cb']}")

    # ---- 5. 跷跷板 ----
    opp = (np.sign(j["csco"]) != np.sign(j["bug"])).mean()
    print(f"\n[5] 跷跷板(日方向相反天数占比): {opp*100:.1f}%")

    # ---- 6. 相对强弱 CSCO/BUG ----
    pr = pd.DataFrame({"csco": cs.set_index("date")["close"], "bug": bs.set_index("date")["close"]}).dropna()
    ratio = pr["csco"] / pr["bug"]
    ratio_norm = ratio / ratio.iloc[0]
    print(f"\n[6] CSCO/BUG 比值: 归一化最新 {ratio_norm.iloc[-1]:.3f}  高点 {ratio_norm.max():.3f} ({ratio_norm.idxmax().date()})  低点 {ratio_norm.min():.3f} ({ratio_norm.idxmin().date()})")

    # ---- 7. 极端日：BUG 单日 |涨跌|>=2% 时 CSCO 表现 ----
    thr = 0.02
    big = j[(j["bug"].abs() >= thr)].copy()
    big_days = []
    for dt, row in big.iterrows():
        big_days.append({
            "date": dt.strftime("%Y-%m-%d"),
            "bug": clean(row["bug"] * 100),
            "csco": clean(row["csco"] * 100),
            "spy": clean(row["spy"] * 100),
            "type": "up" if row["bug"] > 0 else "dn",
        })
    print(f"\n[7] BUG |日涨跌|>=2% 共 {len(big_days)} 天")
    if len(big_days):
        up_days = [d for d in big_days if d["type"] == "up"]
        dn_days = [d for d in big_days if d["type"] == "dn"]
        for t, lab, grp in (("up", "BUG大涨日", up_days), ("dn", "BUG大跌日", dn_days)):
            if not grp:
                print(f"  {lab}: 无")
                continue
            cs_m = np.mean([d["csco"] for d in grp])
            cs_med = np.median([d["csco"] for d in grp])
            same_dir = np.mean([np.sign(d["csco"]) == np.sign(d["bug"]) for d in grp]) * 100
            print(f"  {lab} ({len(grp)}天): CSCO 均值 {cs_m:+.2f}% 中位 {cs_med:+.2f}% 同向率 {same_dir:.0f}%")

    # ---- 8. β ----
    beta_cb = float(np.polyfit(j["bug"], j["csco"], 1)[0])
    beta_cs = float(np.polyfit(j["spy"], j["csco"], 1)[0])
    print(f"\n[8] β: CSCO~BUG {beta_cb:.3f}  CSCO~SPY {beta_cs:.3f}")

    # ---- 序列（图表用，5日采样）----
    def norm_series(df):
        s = df.set_index("date")["close"]
        return pd.DataFrame({"date": s.index, "v": s / s.iloc[0]})

    seq = {}
    for k, df in (("csco", cs), ("bug", bs), ("spy", ss)):
        ns = norm_series(df)
        seq[k] = {"dates": [d.strftime("%Y-%m-%d") for d in ns["date"][::5]],
                  "values": [float(v) for v in ns["v"][::5]]}

    roll_chart = {
        "dates": [d.strftime("%Y-%m-%d") for d in rdf["date"][::3]],
        "cb60": [clean(v) for v in rdf["cb60"][::3]],
        "cs60": [clean(v) for v in rdf["cs60"][::3]],
        "cb30": [clean(v) for v in rdf["cb30"][::3]],
    }
    ratio_chart = {"dates": [d.strftime("%Y-%m-%d") for d in ratio_norm.index[::5]],
                   "values": [clean(v) for v in ratio_norm[::5]]}

    result = {
        "window": {"start": str(cs["date"].iloc[0].date()), "end": str(cs["date"].iloc[-1].date()), "n": n},
        "cum": cu,
        "excess": ex,
        "stats": stats,
        "corr_full": corr_full,
        "corr_roll": {"mean60": clean(roll60_cb.mean()), "latest60": clean(roll60_cb.iloc[-1]),
                      "min60": clean(roll60_cb.min()), "max60": clean(roll60_cb.max()),
                      "mean_cs60": clean(roll60_cs.mean()), "latest_cs60": clean(roll60_cs.iloc[-1])},
        "monthly": monthly,
        "seesaw": clean(opp),
        "ratio": {"norm_latest": clean(float(ratio_norm.iloc[-1])),
                  "max": clean(float(ratio_norm.max())), "max_date": str(ratio_norm.idxmax().date()),
                  "min": clean(float(ratio_norm.min())), "min_date": str(ratio_norm.idxmin().date())},
        "big_days": big_days,
        "beta": {"csco_bug": clean(beta_cb), "csco_spy": clean(beta_cs)},
        "norm_series": seq,
        "roll_chart": roll_chart,
        "ratio_chart": ratio_chart,
    }
    with open(os.path.join(OUT, "csco_bug_corr.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    print("\n结果已保存 results/csco_bug_corr.json")


if __name__ == "__main__":
    main()