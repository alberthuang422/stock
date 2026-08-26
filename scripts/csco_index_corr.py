# -*- coding: utf-8 -*-
"""CSCO × 纳指(QQQ代理) / 道指(DJI) 相关性对比分析。

口径（与 KO×道指 / IHI×XBI / IBB×GILD 系列保持一致）：
  - 日收益率：close pct_change × 100，Pearson / Spearman
  - 参照1：QQQ（纳指100代理，1999-03 起，交集 1999-03 ~ 2026-08）
  - 参照2：DJI（道琼斯工业指数，2021-08 起，交集 2021-08 ~ 2026-08）
  - 分阶段：全期 / 分界前(<2026-02-01) / 分界后(>=2026-02-01) / 2025-09以来 / 2026以来
    （分界点沿用项目惯例 2026-02 结构断裂点；2025-09 为对照分析默认窗口起点）
  - Fisher z 检验分界前后相关系数差异显著性
  - 60 日滚动相关性（主口径）、月度/年度平均相关性
  - β、相对强弱（CSCO/INDEX 归一化 + 阶段超额）、极端日（|ret|>=3%）
输出 JSON 到 results/csco_index_corr.json，供 HTML 报告使用。
"""
import os
import json
from math import atanh, sqrt, erf

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

SPLIT = pd.Timestamp("2026-02-01")          # 结构断裂点（项目惯例）
WINDOW_START = pd.Timestamp("2025-09-01")   # 对照分析默认窗口起点
YTD_START = pd.Timestamp("2026-01-01")
ANCHOR_QQQ = pd.Timestamp("1999-03-10")     # QQQ 数据起点
ANCHOR_DJI = pd.Timestamp("2021-08-25")     # DJI 数据起点


def load(ticker: str) -> pd.DataFrame:
    p = os.path.join(DATA, ticker.lower(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    if "close" not in df.columns:
        raise ValueError(f"{ticker} 缺 close 列: {df.columns.tolist()}")
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
    running_max = np.maximum.accumulate(prices)
    dd = (prices / running_max - 1) * 100
    return float(dd.min())


def fisher_z_test(r1, n1, r2, n2):
    z = (atanh(r1) - atanh(r2)) / sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    p_val = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return round(float(z), 3), round(float(p_val), 4)


def stats_block(sec: pd.DataFrame, ref: pd.DataFrame, name: str, start=None, end=None):
    if start is not None:
        sec = sec[sec["date"] >= start]
        ref = ref[ref["date"] >= start]
    if end is not None:
        sec = sec[sec["date"] < end]
        ref = ref[ref["date"] < end]
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_idx")).dropna()
    if len(merged) < 5:
        return {"name": name, "n": 0}
    x = merged["ret_idx"].values   # 指数
    y = merged["ret_sec"].values   # CSCO
    p, s, n = pearson_spearman(y, x)
    beta = float(np.cov(y, x)[0, 1] / np.var(x)) if np.var(x) > 0 else np.nan
    resid = y - beta * x
    r2 = p * p
    sec_ret = (merged["close_sec"].iloc[-1] / merged["close_sec"].iloc[0] - 1) * 100
    idx_ret = (merged["close_idx"].iloc[-1] / merged["close_idx"].iloc[0] - 1) * 100
    return {
        "name": name, "n": int(n),
        "start": str(merged["date"].iloc[0].date()),
        "end": str(merged["date"].iloc[-1].date()),
        "pearson": round(p, 3), "spearman": round(s, 3),
        "beta": round(float(beta), 3),
        "r2": round(float(r2), 3),
        "resid_vol": round(float(resid.std()), 2),
        "sec_ret_total": round(float(sec_ret), 2),
        "idx_ret_total": round(float(idx_ret), 2),
        "excess_ret": round(float(sec_ret - idx_ret), 2),   # CSCO 相对指数（pp）
        "sec_vol": round(float(merged["ret_sec"].std()), 2),
        "idx_vol": round(float(merged["ret_idx"].std()), 2),
        "ann_vol_sec": round(float(merged["ret_sec"].std() * np.sqrt(252)), 1),
        "ann_vol_idx": round(float(merged["ret_idx"].std() * np.sqrt(252)), 1),
        "max_drawdown_sec": round(float(calc_mdd(merged["close_sec"].values)), 2),
        "max_drawdown_idx": round(float(calc_mdd(merged["close_idx"].values)), 2),
    }


def analyze_pair(tag: str, label: str, sec: pd.DataFrame, ref: pd.DataFrame, anchor: pd.Timestamp):
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_idx")).dropna().reset_index(drop=True)
    merged = merged[merged["date"] >= anchor].reset_index(drop=True)
    merged["ratio"] = merged["close_sec"] / merged["close_idx"]

    blocks = [
        stats_block(sec, ref, "全期（交集）"),
        stats_block(sec, ref, f"分界前 (< {SPLIT.date()})", end=SPLIT),
        stats_block(sec, ref, f"分界后 (>= {SPLIT.date()})", start=SPLIT),
        stats_block(sec, ref, "2025-09 以来", start=WINDOW_START),
        stats_block(sec, ref, "2026 以来", start=YTD_START),
    ]
    fisher = None
    b_pre, b_post = blocks[1], blocks[2]
    if b_pre["n"] > 5 and b_post["n"] > 5:
        z, pv = fisher_z_test(b_pre["pearson"], b_pre["n"], b_post["pearson"], b_post["n"])
        fisher = {"z": z, "p_value": pv, "sig": bool(pv < 0.05)}

    # 滚动 60 日相关性（主口径）
    roll60 = merged["ret_sec"].rolling(60).corr(merged["ret_idx"]) * 100
    roll_series = [{"date": str(d.date()),
                    "corr": None if np.isnan(v) else round(float(v), 2)}
                   for d, v in zip(merged["date"], roll60)]

    # 月度平均相关性
    mm = merged.set_index("date")
    monthly = (mm[["ret_sec", "ret_idx"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_sec"]["ret_idx"] * 100).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 2)} for k, v in monthly.items()]

    # 年度相关性
    yearly = (mm[["ret_sec", "ret_idx"]].groupby(mm.index.year)[["ret_sec", "ret_idx"]]
              .corr().unstack()["ret_sec"]["ret_idx"] * 100).dropna()
    yearly_series = [{"year": int(k), "corr": round(float(v), 2)} for k, v in yearly.items()]

    # 归一化价格（交集起点=100）
    k0 = merged["close_sec"].iloc[0]
    d0 = merged["close_idx"].iloc[0]
    price_series = [{
        "date": str(d.date()),
        "sec": round(float(k) / k0 * 100, 2),
        "idx": round(float(j) / d0 * 100, 2),
        "ratio": round(float(r), 4),
    } for d, k, j, r in zip(merged["date"], merged["close_sec"], merged["close_idx"], merged["ratio"])]

    # 相对强弱：CSCO/INDEX 价格比 zscore（滚动 250 日）
    ratio = merged["ratio"]
    zscore = (ratio - ratio.rolling(250).mean()) / ratio.rolling(250).std()
    rel_strength = [{"date": str(d.date()),
                     "ratio": round(float(r), 4),
                     "z": None if np.isnan(v) else round(float(v), 2)}
                    for d, r, v in zip(merged["date"], ratio, zscore)]

    # 极端日：交集期 |ret|>=3%
    ext = merged
    sec_evts = ext[ext["ret_sec"].abs() >= 3]
    idx_evts = ext[ext["ret_idx"].abs() >= 3]
    both = ext[(ext["ret_sec"].abs() >= 3) & (ext["ret_idx"].abs() >= 3)]
    either = ext[(ext["ret_sec"].abs() >= 3) | (ext["ret_idx"].abs() >= 3)]
    corr_ext = float(both["ret_sec"].corr(both["ret_idx"])) if len(both) > 1 else None
    extreme = {
        "start": str(ext["date"].iloc[0].date()),
        "end": str(ext["date"].iloc[-1].date()),
        "sec_only": int(len(sec_evts)), "idx_only": int(len(idx_evts)),
        "both": int(len(both)), "either": int(len(either)),
        "corr_on_extreme_days": corr_ext,
        "hit_rate_sec_given_idx": round(len(both) / len(idx_evts) * 100, 1) if len(idx_evts) else None,
        "hit_rate_idx_given_sec": round(len(both) / len(sec_evts) * 100, 1) if len(sec_evts) else None,
    }

    # 各阶段超额年化
    excess_annual = []
    for b in blocks:
        if b["n"] == 0:
            continue
        yrs = b["n"] / 252
        excess_annual.append({
            "phase": b["name"], "n": b["n"],
            "excess_total": b["excess_ret"],
            "excess_annualized": round(b["excess_ret"] / yrs, 2) if yrs > 0.1 else None,
        })

    # 大事件清单（CSCO 单日 |ret|>=5%，标注财报日期附近）
    big_evts = [
        {"date": str(d.date()), "ret": round(float(r), 2), "idx": round(float(i), 2)}
        for d, r, i in zip(ext["date"], ext["ret_sec"], ext["ret_idx"])
        if abs(ext.loc[ext["date"] == d, "ret_sec"].iloc[0]) >= 5.0
    ]

    return {
        "tag": tag, "label": label,
        "split": str(SPLIT.date()),
        "period": {"start": str(merged["date"].iloc[0].date()),
                   "end": str(merged["date"].iloc[-1].date()),
                   "n": int(len(merged))},
        "blocks": blocks, "fisher": fisher,
        "rolling60": roll_series, "monthly": monthly_series, "yearly": yearly_series,
        "price_recent": price_series,
        "rel_strength": rel_strength, "extreme": extreme, "excess_annual": excess_annual,
        "big_events": big_evts,
    }


def main():
    qqq = load("QQQ")
    dji = load("DJI")
    csco = load("CSCO")
    out = {"meta": {
        "sec": "思科 CSCO (NASDAQ: CSCO)",
        "ref1": "纳指100 QQQ ETF（NASDAQ 代理，1999-03-10 起）",
        "ref2": "道琼斯工业指数 DJI（腾讯自选股 usDJI，2021-08-25 起）",
        "source": "CSCO/QQQ: Yahoo Finance 日线（复权收盘）; DJI: 腾讯自选股日线（收盘价，指数不复权）",
        "note": "两组合独立交集：CSCO×QQQ 1999-03 ~ 2026-08；CSCO×DJI 2021-08 ~ 2026-08",
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
    }, "pairs": []}

    res_q = analyze_pair("QQQ", "CSCO × 纳指100(QQQ)", csco, qqq, ANCHOR_QQQ)
    res_d = analyze_pair("DJI", "CSCO × 道琼斯(DJI)", csco, dji, ANCHOR_DJI)
    out["pairs"] = [res_q, res_d]

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "csco_index_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, allow_nan=False)
    print("saved:", path)

    # 汇总打印
    print("\n=== CSCO × 指数 相关系数（Pearson）分阶段 ===")
    for pr in out["pairs"]:
        print(f"\n--- {pr['label']} [{pr['period']['start']} ~ {pr['period']['end']}, n={pr['period']['n']}] ---")
        for b in pr["blocks"]:
            print(f"  {b['name']:<24} pearson={b['pearson']:<6} spearman={b['spearman']:<6} beta={b['beta']:<6} n={b['n']} 超额={b.get('excess_ret')}pp")
        f = pr["fisher"]
        if f:
            print(f"  Fisher z(分界前vs后) = {f['z']}, p={f['p_value']}, sig={f['sig']}")
        e = pr["extreme"]
        print(f"  极端日(|r|>=3%): sec_only={e['sec_only']} idx_only={e['idx_only']} both={e['both']} corr(同日)={e['corr_on_extreme_days']}")
        if pr["big_events"]:
            print(f"  CSCO 单日|>=5%|大事件 {len(pr['big_events'])} 条:")
            for ev in pr["big_events"]:
                print(f"    {ev['date']}  CSCO {ev['ret']:+.1f}%  指数 {ev['idx']:+.1f}%")


if __name__ == "__main__":
    main()