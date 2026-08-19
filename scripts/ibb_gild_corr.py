#!/usr/bin/env python3
"""IBB vs GILD 分阶段相关性分析。

从 data/ibb/ 与 data/gild/ 读 CSV（列: date, open, high, low, close, volume, adj_close），
计算:
  - 日收益率相关性（Pearson / Spearman），全期 + 分阶段
  - 滚动 60 日相关性序列
  - GILD 对 IBB 的 beta（日收益率回归）
  - 各阶段收益 / 波动 / 回撤统计
输出 JSON 到 results/ 供 HTML 报告使用。
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
SPLIT = pd.Timestamp("2026-02-01")  # 分界点: 2026-02 之前 vs 之后

def load(ticker: str) -> pd.DataFrame:
    p = os.path.join(DATA, ticker.lower(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 100
    return df

def pearson_spearman(a: np.ndarray, b: np.ndarray):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, None, len(a)
    p = np.corrcoef(a, b)[0, 1]
    from scipy.stats import spearmanr
    s = spearmanr(a, b).statistic
    return float(p), float(s), len(a)

def stats_block(ibb: pd.DataFrame, gild: pd.DataFrame, name: str):
    merged = pd.merge(ibb[["date", "ret"]], gild[["date", "ret"]],
                      on="date", suffixes=("_ibb", "_gild")).dropna()
    if len(merged) < 5:
        return {"name": name, "n": 0}
    p, s, n = pearson_spearman(merged["ret_ibb"].values, merged["ret_gild"].values)
    # beta = cov(r_gild, r_ibb) / var(r_ibb); 残差波动 = 个股特有波动
    x = merged["ret_ibb"].values
    y = merged["ret_gild"].values
    beta = float(np.cov(y, x)[0, 1] / np.var(x))
    resid = y - beta * x
    resid_vol = float(resid.std())
    r2 = p * p
    # 价格段收益
    ibb_sub = ibb[(ibb["date"] >= merged["date"].min()) & (ibb["date"] <= merged["date"].max())]
    gild_sub = gild[(gild["date"] >= merged["date"].min()) & (gild["date"] <= merged["date"].max())]
    ibb_ret_total = (ibb_sub["close"].iloc[-1] / ibb_sub["close"].iloc[0] - 1) * 100
    gild_ret_total = (gild_sub["close"].iloc[-1] / gild_sub["close"].iloc[0] - 1) * 100
    return {
        "name": name,
        "n": n,
        "start": str(merged["date"].iloc[0].date()),
        "end": str(merged["date"].iloc[-1].date()),
        "pearson": p, "spearman": s, "beta": beta, "r2": float(r2),
        "resid_vol": float(resid_vol),
        "ibb_ret_total": round(float(ibb_ret_total), 2),
        "gild_ret_total": round(float(gild_ret_total), 2),
        "ibb_vol": round(float(merged["ret_ibb"].std()), 2),   # 日波动率 %
        "gild_vol": round(float(merged["ret_gild"].std()), 2),
        "diff_ret": round(float(ibb_ret_total - gild_ret_total), 2),
    }

def main():
    ibb = load("IBB")
    gild = load("GILD")
    merged = pd.merge(ibb[["date", "close", "ret"]], gild[["date", "close", "ret"]],
                      on="date", suffixes=("_ibb", "_gild")).dropna().reset_index(drop=True)
    merged["ratio"] = merged["close_ibb"] / merged["close_gild"]
    merged["spread"] = np.log(merged["close_ibb"]) - np.log(merged["close_gild"])

    blocks = [
        stats_block(ibb, gild, "全期"),
        stats_block(ibb[ibb["date"] < SPLIT], gild[gild["date"] < SPLIT], f"分界前 ({SPLIT.date()})"),
        stats_block(ibb[ibb["date"] >= SPLIT], gild[gild["date"] >= SPLIT], f"分界后 ({SPLIT.date()})"),
    ]
    # Fisher z 检验: 分界前 vs 分界后 相关系数差异显著性
    from math import atanh, sqrt, erf
    def fisher_z(r): return atanh(r)
    r1, n1 = blocks[1]["pearson"], blocks[1]["n"]
    r2, n2 = blocks[2]["pearson"], blocks[2]["n"]
    z = (fisher_z(r1) - fisher_z(r2)) / sqrt(1/(n1-3) + 1/(n2-3))
    p_val = 2 * (1 - 0.5 * (1 + erf(abs(z)/sqrt(2))))  # 双尾
    fisher = {"z": round(float(z), 3), "p_value": round(float(p_val), 4),
              "sig": bool(p_val < 0.05)}
    # 滚动 60 日相关性
    roll = merged["ret_ibb"].rolling(60).corr(merged["ret_gild"]) * 100
    roll_series = [{"date": str(d.date()), "corr": None if np.isnan(v) else round(float(v), 2)}
                   for d, v in zip(merged["date"], roll)]
    # 月度平均相关性（近 3 年）
    mm = merged.set_index("date")
    monthly = (mm[["ret_ibb", "ret_gild"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_ibb"]["ret_gild"] * 100).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 2)} for k, v in monthly.items()]

    # 阶段内每日价格序列（近 18 个月 + 分界前后各自）
    recent = merged[merged["date"] >= "2024-01-01"]
    price_series = [{
        "date": str(d.date()),
        "ibb": round(float(i), 2), "gild": round(float(g2), 2),
        "ratio": round(float(r), 4),
    } for d, i, g2, r in zip(recent["date"], recent["close_ibb"], recent["close_gild"], recent["ratio"])]

    # 日收益散点（近 3 年，分界前后分色）
    scatter = []
    sc = merged[merged["date"] >= "2023-01-01"]
    for d, x, y in zip(sc["date"], sc["ret_ibb"], sc["ret_gild"]):
        scatter.append({
            "date": str(d.date()),
            "x": round(float(x), 3), "y": round(float(y), 3),
            "after": bool(d >= SPLIT),
        })

    out = {
        "split": str(SPLIT.date()),
        "period": {"start": str(merged["date"].iloc[0].date()), "end": str(merged["date"].iloc[-1].date()),
                   "n": int(len(merged))},
        "blocks": blocks,
        "fisher": fisher,
        "rolling60": roll_series,
        "monthly": monthly_series,
        "price_recent": price_series,
        "scatter": scatter,
        "meta": {
            "ibb": "iShares Biotechnology ETF",
            "gild": "Gilead Sciences Inc.",
            "source": "Yahoo Finance 日线(收盘价)",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        }
    }
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "ibb_gild_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", path)
    for b in blocks:
        print(json.dumps(b, ensure_ascii=False))

if __name__ == "__main__":
    main()
