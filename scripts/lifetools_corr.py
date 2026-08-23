#!/usr/bin/env python3
"""A / WAT / DHR / TMO（生命科学工具四龙头）× IBB / XBI（双基准）分阶段相关性分析。

口径（与 IHI×XBI 保持一致）：
  - 日收益率：close pct_change × 100，Pearson / Spearman
  - 分阶段：全期 / 分界前(<2026-02-01) / 分界后(>=2026-02-01) / 2025-09以来 / 2026以来
  - Fisher z 检验分界前后相关系数差异显著性
  - 个股对基准的 beta（日收益回归）+ R² + 残差波动
  - 年度相关性、60 日滚动相关性
  - 相对强弱：个股 vs 基准各阶段超额收益
  - 极端日不对称（|ret|>=3%）：个股 vs 基准 谁主导
  - 四龙头内部相关性（DHR×TMO、WAT×TMO 等高相关对特别关注）
输出 JSON 到 results/lifetools_corr.json（供 HTML 报告）与 results/lifetools_corr_detail.json（完整）。
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

SPLIT = pd.Timestamp("2026-02-01")
WINDOW_START = pd.Timestamp("2025-09-01")
YTD_START = pd.Timestamp("2026-01-01")

STOCKS = ["A", "WAT", "DHR", "TMO"]
BENCHES = ["IBB", "XBI"]

def load(ticker: str) -> pd.DataFrame:
    p = os.path.join(DATA, ticker.lower(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 100
    return df

def pearson_spearman(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, None, 0
    p = float(np.corrcoef(a, b)[0, 1])
    s = float(pd.Series(a).rank().corr(pd.Series(b).rank()))
    return p, s, len(a)

def calc_mdd(prices: np.ndarray):
    if len(prices) < 2:
        return 0.0
    return float((prices / np.maximum.accumulate(prices) - 1).min() * 100)

def fisher_z_test(r1, n1, r2, n2):
    from math import atanh, sqrt, erf
    z = (atanh(r1) - atanh(r2)) / sqrt(1/(n1-3) + 1/(n2-3))
    p_val = 2 * (1 - 0.5 * (1 + erf(abs(z)/sqrt(2))))
    return round(float(z), 3), round(float(p_val), 4)

def stats_block(sta: pd.DataFrame, ben: pd.DataFrame, name: str, start=None, end=None):
    if start is not None:
        sta, ben = sta[sta["date"] >= start], ben[ben["date"] >= start]
    if end is not None:
        sta, ben = sta[sta["date"] < end], ben[ben["date"] < end]
    merged = pd.merge(sta[["date", "close", "ret"]], ben[["date", "close", "ret"]],
                      on="date", suffixes=("_s", "_b")).dropna()
    if len(merged) < 5:
        return {"name": name, "n": 0}
    x = merged["ret_b"].values   # 基准
    y = merged["ret_s"].values   # 个股
    p, s, n = pearson_spearman(y, x)
    beta = float(np.cov(y, x)[0, 1] / np.var(x)) if np.var(x) > 0 else np.nan
    resid = y - beta * x
    s_ret = (merged["close_s"].iloc[-1] / merged["close_s"].iloc[0] - 1) * 100
    b_ret = (merged["close_b"].iloc[-1] / merged["close_b"].iloc[0] - 1) * 100
    return {
        "name": name, "n": int(n),
        "pearson": round(p, 3), "spearman": round(s, 3),
        "beta": round(float(beta), 3), "r2": round(float(p * p), 3),
        "resid_vol": round(float(resid.std()), 2),
        "stock_ret": round(float(s_ret), 2), "bench_ret": round(float(b_ret), 2),
        "excess": round(float(s_ret - b_ret), 2),
        "stock_vol": round(float(merged["ret_s"].std()), 2),
        "bench_vol": round(float(merged["ret_b"].std()), 2),
        "mdd_stock": round(calc_mdd(merged["close_s"].values), 1),
        "mdd_bench": round(calc_mdd(merged["close_b"].values), 1),
        "start": str(merged["date"].iloc[0].date()),
        "end": str(merged["date"].iloc[-1].date()),
    }

def stocks_pair(sta: pd.DataFrame, ben: pd.DataFrame, name: str):
    merged = pd.merge(sta[["date", "close", "ret"]], ben[["date", "close", "ret"]],
                      on="date", suffixes=("_s", "_b")).dropna()
    return merged

def main():
    data = {t: load(t) for t in STOCKS}
    benches = {t: load(t) for t in BENCHES}
    # IHI 也载入用于报告里对照（可选）
    try:
        data["IHI"] = load("IHI")
    except Exception:
        pass

    pair_blocks = {}
    pair_roll = {}
    pair_yearly = {}
    pair_roll60_meta = {}
    stocks_vs_stocks = {}

    for st in STOCKS:
        for be in BENCHES:
            key = f"{st}×{be}"
            blocks = [
                stats_block(data[st], benches[be], "全期"),
                stats_block(data[st], benches[be], f"分界前 (< {SPLIT.date()})", end=SPLIT),
                stats_block(data[st], benches[be], f"分界后 (>= {SPLIT.date()})", start=SPLIT),
                stats_block(data[st], benches[be], "2025-09 以来", start=WINDOW_START),
                stats_block(data[st], benches[be], "2026 以来", start=YTD_START),
            ]
            # Fisher z 分界前 vs 后
            b_pre, b_post = blocks[1], blocks[2]
            fisher = None
            if b_pre["n"] > 5 and b_post["n"] > 5 and b_pre["pearson"] is not None and b_post["pearson"] is not None:
                z, pv = fisher_z_test(b_pre["pearson"], b_pre["n"], b_post["pearson"], b_post["n"])
                fisher = {"z": z, "p_value": pv, "sig": bool(pv < 0.05)}
            merged = pd.merge(data[st][["date", "close", "ret"]], benches[be][["date", "close", "ret"]],
                              on="date", suffixes=("_s", "_b")).dropna()
            # 60日滚动相关性（近3年出图）
            roll = merged["ret_s"].rolling(60).corr(merged["ret_b"]) * 100
            r3 = merged[merged["date"] >= "2023-01-01"]
            roll3 = roll[merged["date"] >= "2023-01-01"]
            roll_series = [{"date": str(d.date()),
                            "corr": None if np.isnan(v) else round(float(v), 2)}
                           for d, v in zip(r3["date"], roll3)]
            # 年度相关性
            mm = merged.set_index("date")
            yearly = (mm[["ret_s", "ret_b"]].groupby(mm.index.year)[["ret_s", "ret_b"]]
                      .corr().unstack()["ret_s"]["ret_b"] * 100).dropna()
            yearly_series = [{"year": int(k), "corr": round(float(v), 2)} for k, v in yearly.items()]
            # 价格序列（近 24 个月，归一化 100）
            recent = merged[merged["date"] >= "2024-06-01"]
            s0, b0 = recent["close_s"].iloc[0], recent["close_b"].iloc[0]
            price_series = [{
                "date": str(d.date()),
                "stock": round(float(s) / s0 * 100, 2),
                "bench": round(float(b) / b0 * 100, 2),
            } for d, s, b in zip(recent["date"], recent["close_s"], recent["close_b"])]
            # 散点（近3年）
            sc3 = merged[merged["date"] >= "2023-01-01"]
            scatter = [{"date": str(d.date()), "x": round(float(x), 3), "y": round(float(y), 3),
                        "after": bool(d >= SPLIT)}
                       for d, x, y in zip(sc3["date"], sc3["ret_b"], sc3["ret_s"])]
            # 极端日（2021+）
            ext = merged[merged["date"] >= "2021-01-01"]
            s_evts = ext[ext["ret_s"].abs() >= 3]
            b_evts = ext[ext["ret_b"].abs() >= 3]
            both = ext[(ext["ret_s"].abs() >= 3) & (ext["ret_b"].abs() >= 3)]
            extreme = {
                "start": str(ext["date"].iloc[0].date()),
                "stock_only": int(len(s_evts) - len(both)),
                "bench_only": int(len(b_evts) - len(both)),
                "both": int(len(both)),
                "hit_stock_given_bench": round(len(both) / len(b_evts) * 100, 1) if len(b_evts) else None,
                "hit_bench_given_stock": round(len(both) / len(s_evts) * 100, 1) if len(s_evts) else None,
            }
            pair_blocks[key] = blocks
            pair_roll[key] = roll_series
            pair_yearly[key] = yearly_series
            pair_roll60_meta[key] = {
                "price": price_series, "scatter": scatter, "extreme": extreme, "fisher": fisher,
            }

    # 四龙头相互之间（全期+分界后，特别关注 DHR×TMO 等同类并购整合体）
    for a in STOCKS:
        for b in STOCKS:
            if a >= b:
                continue
            key = f"{a}×{b}"
            blocks = [
                stats_block(data[a], data[b], "全期"),
                stats_block(data[a], data[b], f"分界后 (>= {SPLIT.date()})", start=SPLIT),
            ]
            stocks_vs_stocks[key] = blocks

    out = {
        "split": str(SPLIT.date()) if isinstance(SPLIT, pd.Timestamp) else SPLIT,
        "meta": {
            "stocks": {t: "生命科学工具/器械龙头" for t in STOCKS},
            "benches": {"IBB": "iShares 生物科技 ETF", "XBI": "SPDR 标普生物科技 ETF"},
            "source": "Yahoo Finance 日线（收盘价）",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        },
        "pair_blocks": pair_blocks,
        "pair_roll": pair_roll,
        "pair_yearly": pair_yearly,
        "pair_meta": pair_roll60_meta,
        "stocks_vs_stocks": stocks_vs_stocks,
    }
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "lifetools_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", path)
    # 精简打印：每个 pair 的分界前后 + 超额
    for key, blocks in pair_blocks.items():
        print(f"\n=== {key} ===")
        for b in [blocks[0], blocks[1], blocks[2], blocks[4]]:
            print(f"  {b['name']}: n={b['n']} r={b['pearson']} rho={b['spearman']} beta={b['beta']} "
                  f"R2={b['r2']} stock={b['stock_ret']}% bench={b['bench_ret']}% excess={b['excess']}pp")
    print("\n=== 四龙头内部（全期/分界后） ===")
    for key, blocks in stocks_vs_stocks.items():
        print(f"  {key}: 全期 r={blocks[0]['pearson']} | 分界后 r={blocks[1]['pearson']}")
    print("\n=== Fisher z（分界前 vs 后） ===")
    for key, meta in pair_roll60_meta.items():
        f = meta["fisher"]
        print(f"  {key}: z={f['z']} p={f['p_value']} sig={f['sig']}") if f else print(f"  {key}: n/a")

if __name__ == "__main__":
    main()