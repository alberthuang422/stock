# -*- coding: utf-8 -*-
"""公用事业 ETF + 成分股 水下MACD回测（复用 01_MACD回测 严格口径）
数据: data/<ticker>/<TICKER>, 1D.csv（Yahoo 日线）→ 指标与收益一律用 adj_close（复权口径）
口径（与 macd_backtest.py / run_all.py 一致）:
  水下金叉 = DIF<0 且 DEA<0 时 DIF 上穿 DEA
  站上     = 金叉后 ≤3 日内收盘首次上穿(close>EMA10 且 close>EMA20)
  站稳     = S 起 y 天内最多 1 日跌破且次日收复（y=3/4/5）
  买入     = hold3 母集：买点=(金叉前10日盘整最高价 + 确认日EMA20)/2，
             确认日(hold3 最后一日)后 30 个交易日内 low≤买点 → 成交，否则错过
  合并     = 10 交易日内多次金叉合并计 1 次（用于「未站上」统计）
统计: 所有收益字段均为百分数数值(如 3.61 表示 +3.61%)，胜率为小数
"""
import pandas as pd
import numpy as np
import json

BASE = r"C:\Users\Administrator\Desktop\stock"
MERGE_WIN, HOLDY, PAN_GAP, LOOKBACK = 10, 3, 10, 30
GROUPS = {"ETF": ["xlu", "utes"], "IPP": ["vst", "ceg", "tln", "nrg"],
          "受管制": ["nee", "sre", "xel", "cnp", "etr", "lnt"]}
TICKERS = [t for g in GROUPS.values() for t in g]


def load(tk):
    path = f"{BASE}/data/{tk}/{tk.upper()}, 1D.csv"
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["date"])
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    adj = df["adj_close"].values.astype(float)
    # 复权因子（当日 adj/close 比值，日内在拆分/分红日为常数）
    fac = adj / close
    adj_high = high * fac
    adj_low = low * fac
    c = pd.Series(adj)
    ema10 = c.ewm(span=10, adjust=False).mean().values
    ema20 = c.ewm(span=20, adjust=False).mean().values
    dif = (c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()).values
    dea = pd.Series(dif).ewm(span=9, adjust=False).mean().values
    return df, adj, adj_high, adj_low, ema10, ema20, dif, dea


def backtest(df, adj, adj_high, adj_low, ema10, ema20, dif, dea):
    C, H, L = adj, adj_high, adj_low
    n = len(df)

    def above(i):
        return C[i] > ema10[i] and C[i] > ema20[i]

    gold = [i for i in range(1, n) if dif[i - 1] <= dea[i - 1] and dif[i] > dea[i] and dif[i] < 0 and dea[i] < 0]

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
        bp = (Hp + ema20[conf]) / 2.0
        end = min(conf + 1 + LOOKBACK, n)
        for B in range(conf + 1, end):
            if L[B] <= bp:
                return round(bp, 3), B, "hit"
        return round(bp, 3), None, "miss"

    def fwd(t, k):
        j = t + k
        return C[j] / C[t] - 1 if j < n else None

    nodes = []
    for t in gold:
        S = find_stand(t)
        if S is None:
            continue
        rec = {"idx": t, "date": df["time"].iloc[t].date().isoformat(),
               "stand_idx": S, "x_days": S - t,
               "hold3": bool(hold_ok(S, 3)) if hold_ok(S, 3) is not None else None,
               "hold4": bool(hold_ok(S, 4)) if hold_ok(S, 4) is not None else None,
               "hold5": bool(hold_ok(S, 5)) if hold_ok(S, 5) is not None else None,
               "ret5": None if fwd(t, 5) is None else round(fwd(t, 5) * 100, 2),
               "ret10": None if fwd(t, 10) is None else round(fwd(t, 10) * 100, 2),
               "ret20": None if fwd(t, 20) is None else round(fwd(t, 20) * 100, 2)}
        rec["buy_status"] = None
        if rec["hold3"]:
            bp, B, st = buy_logic(t, S)
            rec["buy_px"] = bp
            rec["buy_date"] = df["time"].iloc[B].date().isoformat() if B is not None else None
            rec["buy_status"] = st
            for k, col in ((5, "buy_ret5"), (10, "buy_ret10"), (20, "buy_ret20")):
                rec[col] = round((C[B + k] / bp - 1) * 100, 2) if st == "hit" and B + k < n else None
        nodes.append(rec)
    return nodes, gold


def merge_groups(gold):
    groups, cur = [], []
    for g in gold:
        if cur and g - cur[0] >= MERGE_WIN:
            groups.append(cur)
            cur = []
        cur.append(g)
    if cur:
        groups.append(cur)
    return groups


def st_pct(vals, full=False):
    r = [x for x in vals if x is not None and pd.notna(x)]
    if not r:
        return None
    r = np.array(r, dtype=float)
    d = {"n": len(r), "win": float((r > 0).mean()), "avg": float(r.mean()), "med": float(np.median(r))}
    if full:
        d.update({"std": float(r.std()), "min": float(r.min()), "max": float(r.max())})
    return d


def main():
    results, all_nodes = [], []
    for tk in TICKERS:
        df, adj, ah, al, e10, e20, dif, dea = load(tk)
        nodes, gold = backtest(df, adj, ah, al, e10, e20, dif, dea)
        n = len(df)
        h5 = [x for x in nodes if x["hold5"]]
        hit = [x for x in nodes if x["buy_status"] == "hit"]
        groups = merge_groups(gold)
        node_idx = {q["idx"] for q in nodes}
        standable = sum(1 for g in groups if any(x in node_idx for x in g))
        h3_base = sum(1 for x in nodes if x["hold3"])
        r = {
            "ticker": tk.upper(), "group": next(g for g, ts in GROUPS.items() if tk in ts),
            "start": df["time"].iloc[0].date().isoformat(), "end": df["time"].iloc[-1].date().isoformat(),
            "days": n,
            "gold_raw": len(gold), "gold_merged": len(groups),
            "not_stand_groups": len(groups) - standable,
            "pass_stand": len(nodes), "hold3_base": h3_base, "hold5": len(h5),
            "buy_hit": len(hit), "buy_miss": sum(1 for x in nodes if x["buy_status"] == "miss"),
            "buy_hit_rate": round(len(hit) / h3_base * 100, 1) if h3_base else None,
        }
        # 基线（全历史任意日 T+5）
        base5 = [adj[i + 5] / adj[i] - 1 for i in range(n - 5)]
        b5 = st_pct([x * 100 for x in base5])
        r["base_T5"] = {"win": round(b5["win"] * 100, 1), "avg": round(b5["avg"], 2), "n": b5["n"]}
        # hold5 组
        for k in (5, 10, 20):
            s = st_pct([x[f"ret{k}"] for x in h5], full=True)
            if s:
                r[f"h5_T{k}"] = {"win": round(s["win"] * 100, 1), "avg": round(s["avg"], 2),
                                 "med": round(s["med"], 2), "std": round(s["std"], 2),
                                 "min": round(s["min"], 2), "max": round(s["max"], 2), "n": s["n"]}
        # 买入（成交组，同批对比）
        for k in (5, 10, 20):
            sb = st_pct([x[f"buy_ret{k}"] for x in hit])
            so = st_pct([x[f"ret{k}"] for x in hit])
            if sb:
                r[f"buy_T{k}"] = {"win": round(sb["win"] * 100, 1), "avg": round(sb["avg"], 2),
                                  "med": round(sb["med"], 2), "n": sb["n"]}
            if so:
                r[f"orig_T{k}"] = {"win": round(so["win"] * 100, 1), "avg": round(so["avg"], 2), "n": so["n"]}
        # 节点入库（瘦身字段）
        for x in nodes:
            all_nodes.append({"t": tk.upper(), "g": next(g for g, ts in GROUPS.items() if tk in ts),
                              "d": x["date"], "h5": x["hold5"], "h3": x["hold3"],
                              "r5": x["ret5"], "r10": x["ret10"], "r20": x["ret20"],
                              "bs": x["buy_status"], "br5": x.get("buy_ret5"),
                              "br10": x.get("buy_ret10"), "br20": x.get("buy_ret20")})
        results.append(r)
        print(f"{tk.upper():5s} 金叉{len(gold):3d}/合{len(groups):3d} 未站上{len(groups)-standable:2d} "
              f"站上{len(nodes):3d} hold3={h3_base:3d} hold5={len(h5):3d} "
              f"成交{len(hit):2d}/错过{sum(1 for x in nodes if x['buy_status']=='miss'):2d} "
              f"| h5 T+5胜率 {r['h5_T5']['win']:.1f}% 均值{r['h5_T5']['avg']:+.2f}% | "
              f"回踩买 T+5胜率 {r['buy_T5']['win']:.1f}% 均值{r['buy_T5']['avg']:+.2f}%")

    out_json = {"meta": {"rule": "水下金叉→≤3日站上EMA10/20→站稳3/4/5(允许1日跌破次日收复)→hold3母集回踩买点(盘整高点+EMA20)/2成交",
                         "price_basis": "adj_close(复权)", "merged_win": MERGE_WIN,
                         "groups": GROUPS},
                "tickers": results, "nodes": all_nodes}
    with open(f"{BASE}/results/utilities_macd_backtest.json", "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=1)
    pd.DataFrame(results).to_csv(f"{BASE}/results/utilities_macd_backtest.csv",
                                 index=False, encoding="utf-8-sig")
    print("saved -> results/utilities_macd_backtest.json / .csv, nodes=", len(all_nodes))


if __name__ == "__main__":
    main()