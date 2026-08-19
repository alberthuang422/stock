# -*- coding: utf-8 -*-
"""UTES 前十大成分股 2026 年相对 ETF 表现与权重归因
权重快照：2026-04-13 Virtus 官网（主动管理 ETF，权重会变，归因为静态近似）
"""
import json
import math
import os

import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(BASE, "..", "results")

# 前十大持仓权重（2026-04-13 Virtus 官网快照）
HOLDINGS = {
    "CEG": 10.61, "VST": 10.50, "TLN": 10.06, "XEL": 7.45, "CNP": 6.88,
    "ETR": 5.46, "LNT": 5.09, "SRE": 5.00, "NRG": 4.98, "NEE": 4.92,
}
GROUPS = {
    "IPP/发电商": ["CEG", "VST", "TLN", "NRG"],
    "传统受管制定价": ["XEL", "CNP", "ETR", "LNT", "SRE", "NEE"],
}


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
    utes = load("UTES")
    dfs = {t: load(t) for t in HOLDINGS}

    # 2026 窗口
    for t, df in dfs.items():
        df["year"] = df["date"].dt.year
    utes["year"] = utes["date"].dt.year

    def ytd_ret(df, y0=2025, y1=2026):
        d0 = df[df["year"] == y0]
        d1 = df[df["year"] == y1]
        if len(d0) == 0 or len(d1) == 0:
            return None
        return float(d1["close"].iloc[-1] / d0["close"].iloc[-1] - 1)

    def mdd_2026(df):
        d26 = df[df["year"] == 2026]
        if len(d26) == 0:
            return None, None, None
        s = d26.set_index("date")["close"]
        dd = s / s.cummax() - 1
        return float(dd.min()), str(dd.idxmin().date()), str(s.idxmax().date())

    utes_ytd = ytd_ret(utes)
    print(f"UTES 2026 YTD: {utes_ytd*100:+.1f}%")

    rows = []
    for t, w in HOLDINGS.items():
        df = dfs[t]
        r = ytd_ret(df)
        mdd, mdd_d, pk_d = mdd_2026(df)
        # 2026 年与 UTES 的日收益相关
        r_t = ret_series(df).rename(t.lower())
        r_u = ret_series(utes).rename("utes")
        m = pd.concat([r_t, r_u], axis=1).dropna()
        m26 = m[m.index.year == 2026]
        corr26 = float(m26[t.lower()].corr(m26["utes"])) if len(m26) > 20 else None
        # 超额（相对 UTES）
        exc = (r - utes_ytd) if r is not None else None
        # 权重贡献（静态近似）
        contrib = (w * r) if r is not None else None
        rows.append({"ticker": t, "weight": w, "ytd": r, "mdd": mdd, "mdd_date": mdd_d,
                     "peak_date": pk_d, "corr26": corr26, "excess": exc, "contrib": contrib})

    rows.sort(key=lambda x: x["contrib"], reverse=True)

    print("\n[1] 前十大成分股 2026 表现与归因（按权重贡献排序）")
    print(f"{'T':5} {'权重%':>6} {'YTD':>8} {'超额':>8} {'最大回撤':>8} {'谷底':>10} {'相关26':>7} {'贡献pp':>7}")
    for r in rows:
        print(f"{r['ticker']:5} {r['weight']:6.1f} "
              f"{r['ytd']*100:+7.1f}% {r['excess']*100:+7.1f}% "
              f"{r['mdd']*100:7.1f}% {str(r['mdd_date']):>10} "
              f"{r['corr26'] if r['corr26'] else 0:.2f} {r['contrib']:+6.1f}")

    tot_contrib = sum(r["contrib"] for r in rows if r["contrib"] is not None)
    print(f"\n  前十合计权重 {sum(HOLDINGS.values()):.1f}%, 静态加权贡献 {tot_contrib*100:+.1f}pp (UTES 实际 {utes_ytd*100:+.1f}%)")

    # 分组统计
    print("\n[2] 分组对比（简单平均）")
    for gname, members in GROUPS.items():
        rs = [rows[i]["ytd"] for i, r in enumerate(rows) if r["ticker"] in members and rows[i]["ytd"] is not None]
        mds = [rows[i]["mdd"] for i, r in enumerate(rows) if r["ticker"] in members and rows[i]["mdd"] is not None]
        wsum = sum(HOLDINGS[m] for m in members)
        csum = sum(r["contrib"] for r in rows if r["ticker"] in members and r["contrib"] is not None)
        avg = sum(rs) / len(rs)
        avg_mdd = sum(mds) / len(mds)
        print(f"  {gname} ({len(members)}只, 权重{wsum:.1f}%): 平均YTD {avg*100:+.1f}%  平均回撤 {avg_mdd*100:.1f}%  合计贡献 {csum*100:+.1f}pp")

    # 谁拖累 / 谁支撑（相对 UTES）
    print("\n[3] 相对 UTES 排序")
    drag = [r for r in rows if r["excess"] is not None and r["excess"] < -0.03]
    lift = [r for r in rows if r["excess"] is not None and r["excess"] > 0.03]
    print("  拖累(超额<-3pp):", ", ".join(f"{r['ticker']}({r['excess']*100:+.1f}pp)" for r in sorted(drag, key=lambda x: x["excess"])))
    print("  支撑(超额>+3pp):", ", ".join(f"{r['ticker']}({r['excess']*100:+.1f}pp)" for r in sorted(lift, key=lambda x: -x["excess"])))

    # 月度收益（看拖累时段）
    print("\n[4] 月度收益（%）")
    mt = {}
    for t, df in dfs.items():
        d26 = df[df["year"] == 2026]
        mt[t] = {}
        for m in range(1, 9):
            dm = d26[d26["date"].dt.month == m]
            mt[t][m] = (dm["close"].iloc[-1] / dm["close"].iloc[0] - 1) * 100 if len(dm) > 1 else None
    mu = {}
    d26u = utes[utes["year"] == 2026]
    for m in range(1, 9):
        dm = d26u[d26u["date"].dt.month == m]
        mu[m] = (dm["close"].iloc[-1] / dm["close"].iloc[0] - 1) * 100 if len(dm) > 1 else None
    print(f"{'T':5} " + " ".join(f"{m:>6}月" for m in range(1, 9)))
    print(f"{'UTES':5} " + " ".join(f"{mu[m]:+6.1f}" if mu[m] is not None else "     -" for m in range(1, 9)))
    for t in HOLDINGS:
        print(f"{t:5} " + " ".join(f"{mt[t][m]:+6.1f}" if mt[t][m] is not None else "     -" for m in range(1, 9)))

    result = {"utes_ytd": utes_ytd, "holdings": HOLDINGS, "rows": rows,
              "groups": {g: {"members": mem} for g, mem in GROUPS.items()}}
    with open(os.path.join(OUT, "utes_holdings_2026.json"), "w") as f:
        json.dump(result, f, indent=1, default=str)
    print("\n已保存 results/utes_holdings_2026.json")


if __name__ == "__main__":
    main()
