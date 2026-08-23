#!/usr/bin/env python3
"""IHI (iShares U.S. Medical Devices ETF) vs XBI (SPDR S&P Biotech ETF) 分阶段相关性分析。

口径（与 IBB×GILD 分析保持一致并扩展）：
  - 日收益率：close pct_change × 100，Pearson / Spearman
  - 分阶段：全期 / 分界前(<2026-02-01) / 分界后(>=2026-02-01) / 2025-09以来 / 2026以来
    （分界点沿用项目惯例 2026-02 结构断裂点；2025-09 为对照分析默认窗口起点）
  - Fisher z 检验分界前后相关系数差异显著性
  - IHI 对 XBI 的 beta（日收益回归）+ R² + 残差波动
  - 滚动 60 日相关性、月度平均相关性（全期）
  - 相对强弱：IHI/XBI 价格比（对数价差），各阶段超额收益
  - 极端日验证：单日 |ret| >= 3% 的日子归属谁、同日大波动相关
输出 JSON 到 results/ihi_xbi_corr.json，供 HTML 报告使用。
"""
import os, json
from math import atanh, sqrt, erf
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

SPLIT = pd.Timestamp("2026-02-01")          # 结构断裂点（项目惯例）
WINDOW_START = pd.Timestamp("2025-09-01")   # 对照分析默认窗口起点
YTD_START = pd.Timestamp("2026-01-01")

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
    # Spearman = 秩相关，用 pandas rank 计算，避免 scipy 依赖
    s = float(pd.Series(a).rank().corr(pd.Series(b).rank()))
    return p, s, len(a)

def stats_block(ihi: pd.DataFrame, xbi: pd.DataFrame, name: str, start=None, end=None):
    if start is not None:
        ihi = ihi[ihi["date"] >= start]
        xbi = xbi[xbi["date"] >= start]
    if end is not None:
        ihi = ihi[ihi["date"] < end]
        xbi = xbi[xbi["date"] < end]
    merged = pd.merge(ihi[["date", "close", "ret"]], xbi[["date", "close", "ret"]],
                      on="date", suffixes=("_ihi", "_xbi")).dropna()
    if len(merged) < 5:
        return {"name": name, "n": 0}
    x = merged["ret_xbi"].values
    y = merged["ret_ihi"].values
    p, s, n = pearson_spearman(y, x)
    beta = float(np.cov(y, x)[0, 1] / np.var(x)) if np.var(x) > 0 else np.nan
    resid = y - beta * x
    r2 = p * p
    i_ret = (merged["close_ihi"].iloc[-1] / merged["close_ihi"].iloc[0] - 1) * 100
    x_ret = (merged["close_xbi"].iloc[-1] / merged["close_xbi"].iloc[0] - 1) * 100
    # 超额：IHI 相对 XBI
    return {
        "name": name,
        "n": int(n),
        "start": str(merged["date"].iloc[0].date()),
        "end": str(merged["date"].iloc[-1].date()),
        "pearson": round(p, 3), "spearman": round(s, 3),
        "beta": round(float(beta), 3),
        "r2": round(float(r2), 3),
        "resid_vol": round(float(resid.std()), 2),
        "ihi_ret_total": round(float(i_ret), 2),
        "xbi_ret_total": round(float(x_ret), 2),
        "excess_ret": round(float(i_ret - x_ret), 2),
        "ihi_vol": round(float(merged["ret_ihi"].std()), 2),
        "xbi_vol": round(float(merged["ret_xbi"].std()), 2),
        "ann_vol_ihi": round(float(merged["ret_ihi"].std() * np.sqrt(252)), 1),
        "ann_vol_xbi": round(float(merged["ret_xbi"].std() * np.sqrt(252)), 1),
        "max_drawdown_ihi": round(float(calc_mdd(merged["close_ihi"].values)), 2),
        "max_drawdown_xbi": round(float(calc_mdd(merged["close_xbi"].values)), 2),
    }

def calc_mdd(prices: np.ndarray):
    if len(prices) < 2:
        return 0.0
    running_max = np.maximum.accumulate(prices)
    dd = (prices / running_max - 1) * 100
    return float(dd.min())

def fisher_z_test(r1, n1, r2, n2):
    z = (atanh(r1) - atanh(r2)) / sqrt(1/(n1-3) + 1/(n2-3))
    p_val = 2 * (1 - 0.5 * (1 + erf(abs(z)/sqrt(2))))
    return round(float(z), 3), round(float(p_val), 4)

def main():
    ihi = load("IHI")
    xbi = load("XBI")
    merged = pd.merge(ihi[["date", "close", "ret"]], xbi[["date", "close", "ret"]],
                      on="date", suffixes=("_ihi", "_xbi")).dropna().reset_index(drop=True)
    merged["ratio"] = merged["close_ihi"] / merged["close_xbi"]
    merged["spread"] = np.log(merged["close_ihi"]) - np.log(merged["close_xbi"])

    blocks = [
        stats_block(ihi, xbi, "全期"),
        stats_block(ihi, xbi, f"分界前 (< {SPLIT.date()})", end=SPLIT),
        stats_block(ihi, xbi, f"分界后 (>= {SPLIT.date()})", start=SPLIT),
        stats_block(ihi, xbi, f"2025-09 以来", start=WINDOW_START),
        stats_block(ihi, xbi, "2026 以来", start=YTD_START),
    ]
    # Fisher z：分界前 vs 分界后
    b_pre, b_post = blocks[1], blocks[2]
    fisher = None
    if b_pre["n"] > 5 and b_post["n"] > 5:
        z, pv = fisher_z_test(b_pre["pearson"], b_pre["n"], b_post["pearson"], b_post["n"])
        fisher = {"z": z, "p_value": pv, "sig": bool(pv < 0.05)}

    # 滚动 60 日相关性
    roll60 = merged["ret_ihi"].rolling(60).corr(merged["ret_xbi"]) * 100
    roll_series = [{"date": str(d.date()),
                    "corr": None if np.isnan(v) else round(float(v), 2)}
                   for d, v in zip(merged["date"], roll60)]
    # 滚动 60 日滚动超额（IHI - XBI 滚动累计，价格比 zscore）
    roll_ratio = merged["close_ihi"].rolling(60).mean() / merged["close_xbi"].rolling(60).mean()

    # 月度平均相关性（全期，有足够月度数据才保留 = len>=10）
    mm = merged.set_index("date")
    monthly = (mm[["ret_ihi", "ret_xbi"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_ihi"]["ret_xbi"] * 100).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 2)} for k, v in monthly.items()]

    # 年度相关性（含样本天数）
    yearly = (mm[["ret_ihi", "ret_xbi"]].groupby(mm.index.year)[["ret_ihi", "ret_xbi"]]
              .corr().unstack()["ret_ihi"]["ret_xbi"] * 100).dropna()
    yearly_series = [{"year": int(k), "corr": round(float(v), 2)} for k, v in yearly.items()]

    # 价格序列（近 24 个月 + 分界后）
    recent = merged[merged["date"] >= "2024-06-01"]
    price_series = [{
        "date": str(d.date()),
        "ihi": round(float(i), 2), "xbi": round(float(x), 2),
        "ratio": round(float(r), 4),
    } for d, i, x, r in zip(recent["date"], recent["close_ihi"], recent["close_xbi"], recent["ratio"])]

    # 分界前后价格（标准化起点=100，便于对比走势）
    norm_series = []
    for label, sub in [("pre", merged[merged["date"] < SPLIT]), ("post", merged[merged["date"] >= SPLIT])]:
        if len(sub) < 2:
            continue
        i0, x0 = sub["close_ihi"].iloc[0], sub["close_xbi"].iloc[0]
        norm_series.append([{
            "date": str(d.date()),
            "ihi": round(float(i) / i0 * 100, 2),
            "xbi": round(float(x) / x0 * 100, 2),
            "phase": label,
            "offset": 0,
        } for d, i, x in zip(sub["date"], sub["close_ihi"], sub["close_xbi"])])

    # 日收益散点（近 3 年，分界前后分色）
    sc = merged[merged["date"] >= "2023-01-01"]
    scatter = [{
        "date": str(d.date()),
        "x": round(float(x), 3), "y": round(float(y), 3),
        "after": bool(d >= SPLIT),
    } for d, x, y in zip(sc["date"], sc["ret_xbi"], sc["ret_ihi"])]

    # 极端日：|ret| >= 3% 归属统计（近 5 年）
    ext = merged[merged["date"] >= "2021-01-01"]
    ext_start = str(ext["date"].iloc[0].date())
    ihi_evts = ext[ext["ret_ihi"].abs() >= 3]
    xbi_evts = ext[ext["ret_xbi"].abs() >= 3]
    both = ext[(ext["ret_ihi"].abs() >= 3) & (ext["ret_xbi"].abs() >= 3)]
    either = ext[(ext["ret_ihi"].abs() >= 3) | (ext["ret_xbi"].abs() >= 3)]
    ext_list = None
    if len(both) > 0:
        corr_ext = float(both["ret_ihi"].corr(both["ret_xbi"]))
    else:
        corr_ext = None
    top_moves = both.nlargest(10, "ret_ihi") if len(both) else both
    extreme = {
        "start": ext_start,
        "ihi_only": int(len(ihi_evts)),
        "xbi_only": int(len(xbi_evts)),
        "both": int(len(both)),
        "either": int(len(either)),
        "corr_on_extreme_days": corr_ext,
        "hit_rate_ihi_given_xbi": round(len(both) / len(xbi_evts) * 100, 1) if len(xbi_evts) else None,
        "hit_rate_xbi_given_ihi": round(len(both) / len(ihi_evts) * 100, 1) if len(ihi_evts) else None,
    }

    # 各阶段换手/波动对比已含于 blocks，此处输出各阶段超额年化
    excess_annual = []
    for b in blocks:
        if b["n"] == 0:
            continue
        days = b["n"]
        yrs = days / 252
        excess_annual.append({
            "phase": b["name"],
            "n": b["n"],
            "excess_total": b["excess_ret"],
            "excess_annualized": round(b["excess_ret"] / yrs, 2) if yrs > 0.1 else None,
        })

    out = {
        "split": str(SPLIT.date()),
        "window_start": str(WINDOW_START.date()),
        "period": {"start": str(merged["date"].iloc[0].date()),
                   "end": str(merged["date"].iloc[-1].date()),
                   "n": int(len(merged))},
        "blocks": blocks,
        "fisher": fisher,
        "rolling60": roll_series,
        "monthly": monthly_series,
        "yearly": yearly_series,
        "price_recent": price_series,
        "norm_series": norm_series,
        "scatter": scatter,
        "extreme": extreme,
        "excess_annual": excess_annual,
        "meta": {
            "ihi": "iShares U.S. Medical Devices ETF",
            "xbi": "SPDR S&P Biotech ETF",
            "source": "Yahoo Finance 日线（收盘价）",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        }
    }
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "ihi_xbi_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", path)
    print("=== blocks ===")
    for b in blocks:
        print(json.dumps(b, ensure_ascii=False))
    print("=== fisher ===")
    print(json.dumps(fisher, ensure_ascii=False))
    print("=== extreme ===")
    print(json.dumps(extreme, ensure_ascii=False))

if __name__ == "__main__":
    main()