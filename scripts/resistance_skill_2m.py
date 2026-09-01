# -*- coding: utf-8 -*-
"""基于项目 skill `support-resistance-levels` 的支撑/阻力识别
将 swing 窗口从默认 3 根 K 线（约 1 周）扩展为 40 根（约 2 个月），匹配"2 个月级别"诉求
其余算法（ATR 归一化容差 + 评分 + 破位检测）100% 复用 skill 脚本
"""
import os
import sys
import json
import argparse
import subprocess
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "resistance_skill")
os.makedirs(OUT, exist_ok=True)


def find_csv(tk):
    p = os.path.join(DATA, tk.lower())
    if not os.path.isdir(p):
        return None
    for f in os.listdir(p):
        if f.startswith("BATS_"):
            continue
        if f.endswith(".csv") and tk.upper() in f.upper():
            return os.path.join(p, f)
    return None


def analyze(ticker, months, swing_n=40):
    csv_path = find_csv(ticker)
    if not csv_path:
        return {"error": "no data"}
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df[["date", "open", "high", "low", "close"]].sort_values("date").reset_index(drop=True)
    df = df.dropna()
    prev = df["close"].shift(1)
    tr = pd.concat([(df["high"] - df["low"]),
                    (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1)
    df["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    cutoff = pd.Timestamp.now() - pd.DateOffset(months=months)
    df = df[df["date"] >= cutoff].reset_index(drop=True)
    N = len(df)
    if N < 100:
        return {"error": "data too short"}
    high, low, close = df["high"].values, df["low"].values, df["close"].values
    atr_med = float(np.median(df["atr14"].tail(60)))
    tol = 0.75 * atr_med

    # ① Swing 分形 —— 窗口扩到 40 根 K 线（≈2 个月）
    def find_pivots(vals, n, kind):
        idxs = []
        for i in range(n, len(vals) - n):
            w = vals[i - n:i + n + 1]
            if (vals[i] == w.min() if kind == "low" else vals[i] == w.max()) and (w == vals[i]).sum() == 1:
                idxs.append(i)
        return idxs
    piv_low = find_pivots(low, swing_n, "low")
    piv_high = find_pivots(high, swing_n, "high")

    # ② 一维水平聚类（贪心，容差 tol 内并为一带）
    def cluster(prices, tol):
        if not prices:
            return []
        ps = sorted(prices)
        clusters = []
        for p in ps:
            if clusters and abs(p - clusters[-1]["center"]) <= tol:
                c = clusters[-1]
                c["count"] += 1
                c["center"] = (c["center"] * (c["count"] - 1) + p) / c["count"]
                c["items"].append(p)
            else:
                clusters.append({"center": p, "count": 1, "items": [p]})
        return clusters
    supports = cluster([low[i] for i in piv_low], tol)
    resists = cluster([high[i] for i in piv_high], tol)

    # ③ 评分
    def evaluate(levels, kind):
        out = []
        for lv in levels:
            c = lv["center"]
            touch_idxs = [i for i in piv_low if abs(low[i] - c) <= tol] if kind == "sup" else \
                         [i for i in piv_high if abs(high[i] - c) <= tol]
            reacts = []
            for i in touch_idxs:
                if i + 5 >= N:
                    continue
                if kind == "sup":
                    reacts.append(high[i + 1:i + 6].max() / low[i] - 1)
                else:
                    reacts.append(low[i + 1:i + 6].min() / high[i] - 1)
            react_med = float(np.median(reacts)) if reacts else None
            if not touch_idxs:
                continue
            first_t = df["date"].iloc[min(touch_idxs)]
            last_t = df["date"].iloc[max(touch_idxs)]
            days_live = (df["date"].iloc[-1] - first_t).days
            band_edge = c - tol if kind == "sup" else c + tol
            recent_close = close[-10:]
            broken = bool((recent_close < band_edge).any()) if kind == "sup" else bool((recent_close > band_edge).any())
            score = (len(touch_idxs) ** 1.2) * max(abs(react_med or 0.001), 0.001) * min(1, days_live / 200) * 100
            out.append({
                "kind": "支撑" if kind == "sup" else "阻力",
                "price": round(c, 2),
                "band_lo": round(c - tol, 2), "band_hi": round(c + tol, 2),
                "touches": len(touch_idxs),
                "react_med_pct": round((react_med or 0) * 100, 2),
                "first_touch": str(first_t.date()), "last_touch": str(last_t.date()),
                "days_live": int(days_live),
                "broken": broken,
                "score": round(score, 2),
            })
        out.sort(key=lambda x: -x["score"])
        for i, r in enumerate(out):
            r["rank"] = i + 1
        return out

    sup_list = evaluate(supports, "sup")
    res_list = evaluate(resists, "res")
    return {
        "ticker": ticker.upper(),
        "window": {"start": str(df["date"].iloc[0].date()), "end": str(df["date"].iloc[-1].date()),
                   "n": int(N), "last_close": round(float(close[-1]), 2),
                   "atr_med": round(atr_med, 2), "tol": round(tol, 2),
                   "swing_window": swing_n, "months": months},
        "supports": sup_list,
        "resists": res_list,
        "summary": {
            "piv_low": len(piv_low), "piv_high": len(piv_high),
            "support_clusters": len(supports), "resist_clusters": len(resists),
        }
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--months", type=int, default=43)
    ap.add_argument("--swing-n", type=int, default=40)
    args = ap.parse_args()
    results = {}
    for tk in args.tickers:
        out = analyze(tk, args.months, args.swing_n)
        if "error" in out:
            print(f"{tk}: {out['error']}")
            continue
        # 只保留现价上方的阻力位（用户要"阻力位"，不要支撑位）
        last = out["window"]["last_close"]
        res_above = [r for r in out["resists"] if r["price"] >= last * 1.02]
        res_above.sort(key=lambda r: r["price"])
        out["resists_above"] = res_above
        results[tk] = out
        fn = os.path.join(OUT, f"{tk.lower()}.json")
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"{tk}: 现价 {last:.2f}  swing_n={args.swing_n}  阻力位(上) {len(res_above)} 个  -> {fn}")
    # 汇总
    summary_path = os.path.join(OUT, "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("summary ->", summary_path)


if __name__ == "__main__":
    main()
