# -*- coding: utf-8 -*-
"""
MACD水下金叉 + 快速站上EMA10/20 + 站稳3-5天 回测 v5.1（含实盘化买入收益，仅对 hold5 确认信号）
买点: 盘整区间(金叉日前10交易日)最高价 H 与 确认日EMA20 的中点
触发: 确认日(hold5窗口最后一天)后 30 个交易日内首次 low<=买点 → 以买点成交；否则错过
统计口径统一: summary 中 avg/med/std/min/max 均为百分比数值(如3.61表示3.61%)，win_rate 为小数
"""
import pandas as pd
import numpy as np
import json
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--path", default="/Users/alberthuang/Desktop/股票分析/data/ibkr/BATS_IBKR, 1D.csv")
ap.add_argument("--out", default="/Users/alberthuang/Desktop/股票分析/results/signal_nodes.csv")
ap.add_argument("--sum", default="/Users/alberthuang/Desktop/股票分析/results/summary_stats.json")
ap.add_argument("--ticker", default="ibkr")
ap.add_argument("--hold", type=int, default=3, help="确认站稳天数（默认3天即可考虑买入）")
args = ap.parse_args()

HOLDY = args.hold
PAN_GAP = 10
LOOKBACK = 30

df = pd.read_csv(args.path)
df.columns = ["time", "open", "high", "low", "close", "ema20", "ema10", "hist", "dif", "dea"]
df["time"] = pd.to_datetime(df["time"])
C, H, L = df["close"].values, df["high"].values, df["low"].values
E10, E20 = df["ema10"].values, df["ema20"].values
DIF, DEA = df["dif"].values, df["dea"].values
n = len(df)

def above(i):
    return C[i] > E10[i] and C[i] > E20[i]

gold_cross = [i for i in range(1, n) if DIF[i-1] <= DEA[i-1] and DIF[i] > DEA[i] and DIF[i] < 0 and DEA[i] < 0]

def find_stand(t):
    for S in range(t, min(t + 4, n)):
        if above(S) and not above(S - 1):
            return S
    return None

def hold_ok(S, y):
    if S + y - 1 >= n:
        return None
    below = [d for d in range(S, S + y) if not above(d)]
    if len(below) == 0:
        return True
    if len(below) >= 2:
        return False
    d = below[0]
    if d + 1 >= n:
        return None
    return True if above(d + 1) else False

def buy_logic(t, S):
    """仅对通过 hold5 的信号调用。返回 (buy_px, B, status)"""
    p0 = t - PAN_GAP
    if p0 < 0:
        return None, None, None
    Hp = float(H[p0:t].max())
    conf = S + HOLDY - 1
    if conf >= n:
        return None, None, None
    buy_px = (Hp + E20[conf]) / 2.0
    end = min(conf + 1 + LOOKBACK, n)
    for B in range(conf + 1, end):
        if L[B] <= buy_px:
            return round(buy_px, 3), B, "hit"
    return round(buy_px, 3), None, "miss"

def fwd_ret(t, k):
    j = t + k
    return C[j] / C[t] - 1 if j < n else None

rows = []
for t in gold_cross:
    S = find_stand(t)
    if S is None:
        continue
    rec = {"idx": t, "gold_date": df["time"].iloc[t].date(), "gold_close": round(C[t], 3),
           "stand_idx": S, "stand_date": df["time"].iloc[S].date(), "x_days": S - t}
    for y in (3, 4, 5):
        rec[f"hold{y}"] = hold_ok(S, y)
    for k in (5, 10, 20):
        r = fwd_ret(t, k)
        rec[f"ret{k}"] = round(r * 100, 2) if r is not None else None
    # 买入逻辑：站稳3天即可考虑买入（hold3 确认）
    if rec["hold3"]:
        bp, B, st = buy_logic(t, S)
        rec["buy_px"] = bp
        rec["buy_date"] = df["time"].iloc[B].date().isoformat() if B is not None else None
        rec["buy_status"] = st
        for k in (5, 10, 20):
            if st == "hit" and B is not None and B + k < n:
                rec[f"buy_ret{k}"] = round((C[B + k] / bp - 1) * 100, 2)
            else:
                rec[f"buy_ret{k}"] = None
    else:
        rec["buy_px"] = rec["buy_date"] = rec["buy_status"] = None
        for k in (5, 10, 20):
            rec[f"buy_ret{k}"] = None
    rows.append(rec)

res = pd.DataFrame(rows)

def stats_pct(vals):
    """vals 为百分比数值列表；返回 avg/med/std/min/max 为百分比数值，win_rate 为小数"""
    r = [x for x in vals if x is not None and pd.notna(x)]
    if not r:
        return None
    r = np.array(r, dtype=float)
    return {"n": len(r), "win_rate": float((r > 0).mean()), "avg": float(r.mean()),
            "med": float(np.median(r)), "std": float(r.std()),
            "min": float(r.min()), "max": float(r.max())}

h5 = [r["idx"] for r in rows if r["hold5"]]
h3 = [r["idx"] for r in rows if r["hold3"]]
hit = [r for r in rows if r["buy_status"] == "hit"]
groups = {
    "all_gold": gold_cross, "pass_stand": [r["idx"] for r in rows],
    "pass_hold3": [r["idx"] for r in rows if r["hold3"]],
    "pass_hold4": [r["idx"] for r in rows if r["hold4"]],
    "pass_hold5": h5,
}
summary = {}
for gname, idxs in groups.items():
    summary[gname] = {"count": len(idxs)}
    idxset = set(idxs)
    for k in (5, 10, 20):
        st = stats_pct([r[f"ret{k}"] for r in rows if r["idx"] in idxset])
        if st:
            summary[gname][f"ret{k}"] = st

# 买入对比（同批 hold5 成交信号：金叉日买入 vs 回踩买点买入）
summary["_buy"] = {
    "hold3": len(h3), "hit": len(hit), "miss": sum(1 for r in rows if r["buy_status"] == "miss"),
    "hit_rate": len(hit) / len(h3) if h3 else None,
}
for k in (5, 10, 20):
    orig = stats_pct([r[f"ret{k}"] for r in hit])
    buy = stats_pct([r[f"buy_ret{k}"] for r in hit])
    if orig:
        summary["_buy"][f"orig_ret{k}"] = orig
    if buy:
        summary["_buy"][f"buy_ret{k}"] = buy

print(f"===== {args.ticker} 确认站稳={HOLDY}天 =====")
print(f"金叉:{len(gold_cross)} 站上:{len(rows)} hold3母集:{len(h3)} (hold5:{len(h5)}) | 买入成交:{len(hit)} 错过:{summary['_buy']['miss']} "
      f"成交率:{summary['_buy']['hit_rate']*100:.0f}%")
for k in (5, 10, 20):
    o = summary["_buy"].get(f"orig_ret{k}")
    b = summary["_buy"].get(f"buy_ret{k}")
    if o and b:
        print(f"  T+{k}: 金叉日买入 胜率={o['win_rate']*100:.1f}% 均值={o['avg']:+.2f}% | "
              f"回踩买点买入 胜率={b['win_rate']*100:.1f}% 均值={b['avg']:+.2f}% (n={b['n']})")

res.to_csv(args.out, index=False, encoding="utf-8-sig")
with open(args.sum, "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "ticker": args.ticker, "hold_confirm": HOLDY,
               "gold_dates": [df["time"].iloc[t].date().isoformat() for t in gold_cross]},
              f, ensure_ascii=False, indent=1, default=str)
print("saved ->", args.out, "/", args.sum)
