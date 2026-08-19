# -*- coding: utf-8 -*-
"""批量回测 data/ 下所有股票（严格口径 + 实盘化买入收益）
1) 各股严格回测统计（金叉/站上/站稳/收益胜率）
2) 买入逻辑：hold5 确认后，买点=(盘整最高点+确认日EMA20)/2，回踩触发成交
3) 合并金叉统计：10交易日内多次金叉合并为1次，未站上次数
"""
import pandas as pd
import numpy as np
import json
import glob

BASE = "/Users/alberthuang/Desktop/股票分析"
MERGE_WIN = 10
HOLDY, PAN_GAP, LOOKBACK = 3, 10, 30

def load(path):
    df = pd.read_csv(path)
    df.columns = ["time", "open", "high", "low", "close", "ema20", "ema10", "hist", "dif", "dea"]
    df["time"] = pd.to_datetime(df["time"])
    return df

def backtest(df):
    C, H, L = df["close"].values, df["high"].values, df["low"].values
    E10, E20 = df["ema10"].values, df["ema20"].values
    DIF, DEA = df["dif"].values, df["dea"].values
    n = len(df)
    def above(i):
        return C[i] > E10[i] and C[i] > E20[i]
    gold = [i for i in range(1, n) if DIF[i-1] <= DEA[i-1] and DIF[i] > DEA[i] and DIF[i] < 0 and DEA[i] < 0]
    def find_stand(t):
        for S in range(t, min(t + 4, n)):
            if above(S) and not above(S - 1):
                return S
        return None
    def hold_ok(S, y):
        if S + y - 1 >= n:
            return None
        bl = [d for d in range(S, S + y) if not above(d)]
        if len(bl) == 0:
            return True
        if len(bl) >= 2:
            return False
        d = bl[0]
        return None if d + 1 >= n else above(d + 1)
    def buy_logic(t, S):
        p0 = t - PAN_GAP
        if p0 < 0:
            return None, None, None
        Hp = float(H[p0:t].max())
        conf = S + HOLDY - 1
        if conf >= n:
            return None, None, None
        bp = (Hp + E20[conf]) / 2.0
        end = min(conf + 1 + LOOKBACK, n)
        for B in range(conf + 1, end):
            if L[B] <= bp:
                return round(bp, 3), B, "hit"
        return round(bp, 3), None, "miss"
    def fwd(t, k):
        j = t + k
        return C[j] / C[t] - 1 if j < n else None
    # 节点明细
    nodes = []
    for t in gold:
        S = find_stand(t)
        if S is None:
            continue
        rec = {"idx": t, "gold_date": df["time"].iloc[t].date().isoformat(),
               "stand_idx": S, "x_days": S - t, "hold3": hold_ok(S, 3), "hold5": hold_ok(S, 5),
               "ret5": fwd(t, 5), "ret10": fwd(t, 10), "ret20": fwd(t, 20)}
        rec["buy_status"] = None
        if rec["hold3"]:
            bp, B, st = buy_logic(t, S)
            rec["buy_px"], rec["buy_date"], rec["buy_status"] = bp, (df["time"].iloc[B].date().isoformat() if B is not None else None), st
            for k, col in ((5, "buy_ret5"), (10, "buy_ret10"), (20, "buy_ret20")):
                rec[col] = round((C[B + k] / bp - 1) * 100, 2) if st == "hit" and B + k < n else None
        nodes.append(rec)
    return nodes, gold, df

def merge_groups(gold):
    groups, cur = [], []
    for g in gold:
        if cur and g - cur[0] >= MERGE_WIN:
            groups.append(cur); cur = []
        cur.append(g)
    if cur:
        groups.append(cur)
    return groups

def st_pct(vals):
    r = [x for x in vals if x is not None and pd.notna(x)]
    if not r:
        return None
    r = np.array(r, dtype=float)
    return {"n": len(r), "win": float((r > 0).mean()), "avg": float(r.mean()), "med": float(np.median(r))}

results = []
for path in sorted(glob.glob(f"{BASE}/data/*/*.csv")):
    ticker = path.split("/")[-2]
    df = load(path)
    nodes, gold, _ = backtest(df)
    n = len(df)
    h5 = [x for x in nodes if x["hold5"]]
    hit = [x for x in nodes if x["buy_status"] == "hit"]
    groups = merge_groups(gold)
    node_idx = {q["idx"] for q in nodes}
    standable = sum(1 for g in groups if any(x in node_idx for x in g))
    r = {
        "ticker": ticker,
        "start": df["time"].iloc[0].date().isoformat(),
        "end": df["time"].iloc[-1].date().isoformat(),
        "days": n,
        "gold_raw": len(gold), "gold_merged": len(groups),
        "not_stand_groups": len(groups) - standable,
        "pass_stand": len(nodes), "hold5": len(h5),
        "buy_hit": len(hit),
        "buy_miss": sum(1 for x in nodes if x["buy_status"] == "miss"),
        "hold3_base": sum(1 for x in nodes if x["hold3"]),
        "buy_hit_rate": round(len(hit) / sum(1 for x in nodes if x["hold3"]) * 100, 1),
    }
    # hold5 组原收益
    for k in (5, 10, 20):
        s = st_pct([None if x[f"ret{k}"] is None else x[f"ret{k}"] * 100 for x in h5])
        if s:
            r[f"h5_T{k}_win"] = round(s["win"] * 100, 1)
            r[f"h5_T{k}_avg"] = round(s["avg"], 2)
    # 买入收益（成交组，同批对比原收益）
    for k in (5, 10, 20):
        s_buy = st_pct([x[f"buy_ret{k}"] for x in hit])
        s_orig = st_pct([None if x[f"ret{k}"] is None else x[f"ret{k}"] * 100 for x in hit])
        if s_buy:
            r[f"buy_T{k}_win"] = round(s_buy["win"] * 100, 1)
            r[f"buy_T{k}_avg"] = round(s_buy["avg"], 2)
        if s_orig:
            r[f"hit_orig_T{k}_win"] = round(s_orig["win"] * 100, 1)
            r[f"hit_orig_T{k}_avg"] = round(s_orig["avg"], 2)
    results.append(r)

res_df = pd.DataFrame(results)
res_df.to_csv(f"{BASE}/results/all_stocks_backtest.csv", index=False, encoding="utf-8-sig")
with open(f"{BASE}/results/all_stocks_backtest.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
cols = ["ticker", "gold_merged", "not_stand_groups", "hold5", "buy_hit", "buy_miss", "buy_hit_rate",
        "h5_T5_win", "hit_orig_T5_win", "buy_T5_win", "buy_T5_avg",
        "h5_T10_win", "hit_orig_T10_win", "buy_T10_win", "buy_T10_avg",
        "h5_T20_win", "buy_T20_win"]
print(res_df[cols].to_string(index=False))
print("\nsaved: all_stocks_backtest.csv / .json")
