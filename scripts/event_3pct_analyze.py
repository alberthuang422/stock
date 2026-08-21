#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""事件研究：生物医药股当日涨>=3% 后 T+1/T+5/T+10 表现。

口径:
- 收益全部用 adj_close(复权) 口径, 与看盘软件对齐
- 事件 = 当日日收益 >= +3.0% (严格阈值, 无容差)
- 事件后收益 fwdN = 事件日收盘 -> 事件后第 N 个交易日收盘 的持有收益(N=1,5,10)
- 事件日需具备 T+10 数据, 尾部不足 10 个交易日的事件剔除
- 对照 A: 该股全部非事件日 (常态基线)
- 对照 B: 该股 0 < 日收益 < 3% 的"小涨日" (最贴近的替代场景)
- 超额收益: 事件后个股 fwdN - 同期基准 fwdN (基准: SPY 市场 / 制药池->XLV / 生科池->IBB)
输出: results/event_3pct_biopharma.json
"""
import json, os, math
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results", "event_3pct_biopharma.json")

PHARMA = ["GILD", "ABBV", "LLY", "AMGN", "VRTX", "MRK", "JNJ", "REGN", "BIIB"]
BIOTECH = ["ALNY", "NTRA", "ILMN", "RVMD", "ARGX"]
BENCH_MAP = {"PHARMA": "XLV", "BIOTECH": "IBB"}
NS = (1, 5, 10)
EVT_TH = 0.03  # 事件阈值 +3%


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def load_ticker(tkr):
    d = os.path.join(DATA, tkr.lower())
    files = [f for f in os.listdir(d) if f.endswith(".csv") and not f.startswith("BATS")]
    if not files:
        raise FileNotFoundError(tkr)
    path = os.path.join(d, files[0])
    df = pd.read_csv(path, parse_dates=["date"])
    df = df[["date", "adj_close"]].dropna()
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change()
    for N in NS:
        df[f"fwd{N}"] = df["adj_close"].shift(-N) / df["adj_close"] - 1.0
    return df


def load_bench(tkr):
    df = load_ticker(tkr)[["date"] + [f"fwd{N}" for N in NS]]
    return df.rename(columns={f"fwd{N}": f"b_fwd{N}" for N in NS})


def stats(arr):
    """返回事件/对照数组的统计量(全部转 Python float/int)"""
    a = np.asarray(arr, dtype=float)
    a = a[~np.isnan(a)]
    n = int(a.size)
    if n == 0:
        return None
    mean = float(a.mean())
    med = float(np.median(a))
    win = float((a > 0).mean())
    std = float(a.std(ddof=1)) if n > 1 else 0.0
    p25 = float(np.percentile(a, 25))
    p75 = float(np.percentile(a, 75))
    t = mean / (std / math.sqrt(n)) if std > 0 else 0.0
    # 胜率 vs 50% 二项检验 (正态近似, 双尾)
    if n > 0:
        z = (win - 0.5) / math.sqrt(0.25 / n)
        p_binom = float(2.0 * (1.0 - norm_cdf(abs(z))))
    else:
        p_binom = 1.0
    return {"n": n, "mean": round(mean * 100, 2), "med": round(med * 100, 2),
            "win": round(win * 100, 1), "std": round(std * 100, 2),
            "p25": round(p25 * 100, 2), "p75": round(p75 * 100, 2),
            "t": round(t, 2), "p_binom": round(p_binom, 4)}


def sub_stats(df, mask, cols=("fwd1", "fwd5", "fwd10")):
    out = {}
    for c in cols:
        s = stats(df.loc[mask, c].values)
        if s:
            out[c.replace("fwd", "T")] = s
    return out


def pool_stats(tick_dfs, tickers, evt_mask_fn, need_fwd10=True, cooldown=0):
    """合并事件样本: pooled + per-ticker
    cooldown: 若 >0, 距上一次已纳入事件不足 cooldown 个交易日的事件被跳过(剔除重叠)"""
    rows = []
    for tkr in tickers:
        df = tick_dfs[tkr]
        m = evt_mask_fn(df)
        last_i = -10 ** 9
        for idx in df.index[m]:
            if idx - last_i < cooldown:
                continue
            r = df.loc[idx]
            fwd10 = r.get("fwd10")
            if need_fwd10 and (fwd10 is None or math.isnan(fwd10)):
                continue
            last_i = idx
            def _f(v):
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    return None
                return float(v)
            rows.append({
                "tkr": tkr,
                "date": str(r["date"].date()),
                "ret": float(r["ret"]),
                "fwd1": _f(r.get("fwd1")),
                "fwd5": _f(r.get("fwd5")),
                "fwd10": _f(r.get("fwd10")),
                "xs_spy1": _f(r.get("xs_spy1")), "xs_spy5": _f(r.get("xs_spy5")), "xs_spy10": _f(r.get("xs_spy10")),
                "xs_sec1": _f(r.get("xs_sec1")), "xs_sec5": _f(r.get("xs_sec5")), "xs_sec10": _f(r.get("xs_sec10")),
            })
    return rows


def main():
    tickers_all = PHARMA + BIOTECH
    dfs = {}
    for t in tickers_all + ["SPY", "XLV", "IBB"]:
        dfs[t] = load_ticker(t)
        print(f"loaded {t}: {len(dfs[t])} rows, {dfs[t]['date'].min().date()} ~ {dfs[t]['date'].max().date()}")

    # 超额收益: 把基准 fwd 合并到个股 df
    benchs = {t: load_bench(t) for t in ["SPY", "XLV", "IBB"]}
    for t in tickers_all:
        bdf = dfs[t].merge(benchs["SPY"], on="date", how="left")
        for N in NS:
            bdf[f"xs_spy{N}"] = bdf[f"fwd{N}"] - bdf[f"b_fwd{N}"]
        bname = BENCH_MAP["PHARMA"] if t in PHARMA else BENCH_MAP["BIOTECH"]
        bdf = bdf.drop(columns=[f"b_fwd{N}" for N in NS])
        bdf = bdf.merge(benchs[bname], on="date", how="left")
        for N in NS:
            bdf[f"xs_sec{N}"] = bdf[f"fwd{N}"] - bdf[f"b_fwd{N}"]
        dfs[t] = bdf

    result = {"meta": {
        "pharma": PHARMA, "biotech": BIOTECH,
        "ns": list(NS), "evt_th": EVT_TH,
        "range": f"{dfs['GILD']['date'].min().date()} ~ {dfs['GILD']['date'].max().date()}",
    }}

    # ---------------- 事件与对照统计 ----------------
    def evt_mask(df):
        return df["ret"] >= EVT_TH

    def ctrl_mask(df):
        return df["ret"] < EVT_TH

    def small_up_mask(df):
        return (df["ret"] > 0) & (df["ret"] < EVT_TH)

    pools = {"PHARMA": PHARMA, "BIOTECH": BIOTECH}
    pooled = {}
    ctrl = {}
    excess = {}
    tickers_out = {}

    for pool, tkrs in pools.items():
        ev_rows = pool_stats(dfs, tkrs, evt_mask)
        ev_rows_cd = pool_stats(dfs, tkrs, evt_mask, cooldown=10)  # 稳健性: 10日冷却
        pooled[pool] = {
            "n_evt": len(ev_rows),
            "ret_mean": round(float(np.mean([r["ret"] for r in ev_rows])) * 100, 2),
            "ret_med": round(float(np.median([r["ret"] for r in ev_rows])) * 100, 2),
        }
        # 冷却版汇总 (稳健性, 剔除 10 日内重叠事件)
        cd = {"n": len(ev_rows_cd)}
        for N in NS:
            vals = [r[f"fwd{N}"] for r in ev_rows_cd if r[f"fwd{N}"] is not None]
            cd[f"T{N}"] = stats(vals)
        pooled[pool]["cooldown10"] = cd
        # pooled 事件统计 (T+1/T+5/T+10)
        for N in NS:
            vals = [r[f"fwd{N}"] for r in ev_rows if r[f"fwd{N}"] is not None]
            pooled[pool][f"T{N}"] = stats(vals)
        # 分档
        for tag, lo, hi in [("35", 0.03, 0.05), ("5p", 0.05, np.inf)]:
            sub = [r for r in ev_rows if lo <= r["ret"] < hi]
            pooled[pool][f"band_{tag}"] = {
                "n": len(sub),
                "ret_mean": round(float(np.mean([r["ret"] for r in sub])) * 100, 2),
            }
            for N in NS:
                vals = [r[f"fwd{N}"] for r in sub if r[f"fwd{N}"] is not None]
                pooled[pool][f"band_{tag}"][f"T{N}"] = stats(vals)
        # 超额 (相对 SPY / 相对板块)
        for N in NS:
            xs_spy = [r[f"xs_spy{N}"] for r in ev_rows if r[f"xs_spy{N}"] is not None]
            xs_sec = [r[f"xs_sec{N}"] for r in ev_rows if r[f"xs_sec{N}"] is not None]
            excess[f"{pool}_T{N}"] = {
                "xs_spy": stats(xs_spy),
                "xs_sec": stats(xs_sec),
            }
        # 对照: 全体非事件日 + 小涨日
        ctrl_rows = pool_stats(dfs, tkrs, ctrl_mask)
        small_rows = pool_stats(dfs, tkrs, small_up_mask)
        ctrl[pool] = {"all": {}, "small_up": {}}
        for N in NS:
            vals = [r[f"fwd{N}"] for r in ctrl_rows if r[f"fwd{N}"] is not None]
            ctrl[pool]["all"][f"T{N}"] = stats(vals)
            vals = [r[f"fwd{N}"] for r in small_rows if r[f"fwd{N}"] is not None]
            ctrl[pool]["small_up"][f"T{N}"] = stats(vals)
        # 个股明细
        per = {}
        for tkr in tkrs:
            sub_rows = [r for r in ev_rows if r["tkr"] == tkr]
            if not sub_rows:
                continue
            d = {"n": len(sub_rows),
                 "n_year": round(len(sub_rows) / 11.6, 1),  # 年均事件次数 (数据约 11.6 年)
                 "ret_mean": round(float(np.mean([r["ret"] for r in sub_rows])) * 100, 2),
                 "events": [{"date": r["date"], "ret": round(r["ret"] * 100, 2),
                             "fwd1": None if r["fwd1"] is None else round(r["fwd1"] * 100, 2),
                             "fwd5": None if r["fwd5"] is None else round(r["fwd5"] * 100, 2),
                             "fwd10": round(r["fwd10"] * 100, 2)} for r in sub_rows]}
            for N in NS:
                vals = [r[f"fwd{N}"] for r in sub_rows if r[f"fwd{N}"] is not None]
                d[f"T{N}"] = stats(vals)
                xs = [r[f"xs_spy{N}"] for r in sub_rows if r[f"xs_spy{N}"] is not None]
                d[f"xs_spy{N}"] = stats(xs)
            per[tkr] = d
        tickers_out[pool] = per
        # 年份分布 (事件后 T+5/T+10)
        yrs = {}
        for r in ev_rows:
            y = r["date"][:4]
            yrs.setdefault(y, []).append(r)
        years_out = []
        for y in sorted(yrs):
            rows = yrs[y]
            d = {"year": y, "n": len(rows)}
            for N in (5, 10):
                vals = [r[f"fwd{N}"] for r in rows if r[f"fwd{N}"] is not None]
                d[f"T{N}"] = stats(vals)
            years_out.append(d)
        pooled[pool]["years"] = years_out

    result["pooled"] = pooled
    result["ctrl"] = ctrl
    result["excess"] = excess
    result["tickers"] = tickers_out

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("saved:", OUT)

    # 快速预览
    for pool in pools:
        p = pooled[pool]
        print(f"\n=== {pool} ===")
        print(f"事件数 {p['n_evt']} | 事件日均涨 {p['ret_mean']}%")
        for N in NS:
            s = p[f"T{N}"]
            print(f"  T+{N}: n={s['n']} mean={s['mean']}% med={s['med']}% win={s['win']}% t={s['t']}")
        print(f"  对照-小涨日:")
        for N in NS:
            s = ctrl[pool]["small_up"][f"T{N}"]
            print(f"    T+{N}: n={s['n']} mean={s['mean']}% med={s['med']}% win={s['win']}%")


if __name__ == "__main__":
    main()
