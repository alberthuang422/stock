# -*- coding: utf-8 -*-
"""KO × 道琼斯 vs XLV × 道琼斯 相关性对比分析。

口径（与 IHI×XBI / IBB×GILD / KO×板块 系列保持一致）：
  - 日收益率：close pct_change × 100，Pearson / Spearman
  - 分阶段：全期 / 分界前(<2026-02-01) / 分界后(>=2026-02-01) / 2025-09以来 / 2026以来
    （分界点沿用项目惯例 2026-02 结构断裂点；2025-09 为对照分析默认窗口起点）
  - Fisher z 检验分界前后相关系数差异显著性
  - 60 日滚动相关性（主口径）、月度/年度平均相关性
  - 相对强弱：KO/DJI、XLV/DJI 归一化价格与各阶段超额收益
  - 极端日验证：单日 |ret| >= 3% 的日子归属谁、同日大波动相关
输出 JSON 到 results/ko_xlv_dji_corr.json，供 HTML 报告使用。
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
ANCHOR = pd.Timestamp("2021-08-25")         # 交集起点（DJI 数据起点）

PAIRS = [
    ("KO", "可口可乐 KO"),
    ("XLV", "医疗保健 XLV"),
]


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
    """sec=KO或XLV, ref=DJI"""
    if start is not None:
        sec = sec[sec["date"] >= start]
        ref = ref[ref["date"] >= start]
    if end is not None:
        sec = sec[sec["date"] < end]
        ref = ref[ref["date"] < end]
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_dji")).dropna()
    if len(merged) < 5:
        return {"name": name, "n": 0}
    x = merged["ret_dji"].values   # 道指
    y = merged["ret_sec"].values   # KO 或 XLV
    p, s, n = pearson_spearman(y, x)
    beta = float(np.cov(y, x)[0, 1] / np.var(x)) if np.var(x) > 0 else np.nan
    resid = y - beta * x
    r2 = p * p
    sec_ret = (merged["close_sec"].iloc[-1] / merged["close_sec"].iloc[0] - 1) * 100
    dji_ret = (merged["close_dji"].iloc[-1] / merged["close_dji"].iloc[0] - 1) * 100
    return {
        "name": name, "n": int(n),
        "start": str(merged["date"].iloc[0].date()),
        "end": str(merged["date"].iloc[-1].date()),
        "pearson": round(p, 3), "spearman": round(s, 3),
        "beta": round(float(beta), 3),
        "r2": round(float(r2), 3),
        "resid_vol": round(float(resid.std()), 2),
        "sec_ret_total": round(float(sec_ret), 2),
        "dji_ret_total": round(float(dji_ret), 2),
        "excess_ret": round(float(sec_ret - dji_ret), 2),   # KO/XLV 相对道指（pp）
        "sec_vol": round(float(merged["ret_sec"].std()), 2),
        "dji_vol": round(float(merged["ret_dji"].std()), 2),
        "ann_vol_sec": round(float(merged["ret_sec"].std() * np.sqrt(252)), 1),
        "ann_vol_dji": round(float(merged["ret_dji"].std() * np.sqrt(252)), 1),
        "max_drawdown_sec": round(float(calc_mdd(merged["close_sec"].values)), 2),
        "max_drawdown_dji": round(float(calc_mdd(merged["close_dji"].values)), 2),
    }


def analyze_pair(tag: str, label: str, sec: pd.DataFrame, ref: pd.DataFrame):
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_dji")).dropna().reset_index(drop=True)
    merged = merged[merged["date"] >= ANCHOR].reset_index(drop=True)
    merged["ratio"] = merged["close_sec"] / merged["close_dji"]

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
    roll60 = merged["ret_sec"].rolling(60).corr(merged["ret_dji"]) * 100
    roll_series = [{"date": str(d.date()),
                    "corr": None if np.isnan(v) else round(float(v), 2)}
                   for d, v in zip(merged["date"], roll60)]

    # 月度平均相关性
    mm = merged.set_index("date")
    monthly = (mm[["ret_sec", "ret_dji"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_sec"]["ret_dji"] * 100).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 2)} for k, v in monthly.items()]

    # 年度相关性
    yearly = (mm[["ret_sec", "ret_dji"]].groupby(mm.index.year)[["ret_sec", "ret_dji"]]
              .corr().unstack()["ret_sec"]["ret_dji"] * 100).dropna()
    yearly_series = [{"year": int(k), "corr": round(float(v), 2)} for k, v in yearly.items()]

    # 归一化价格（交集起点=100）
    k0 = merged["close_sec"].iloc[0]
    d0 = merged["close_dji"].iloc[0]
    price_series = [{
        "date": str(d.date()),
        "sec": round(float(k) / k0 * 100, 2),
        "dji": round(float(j) / d0 * 100, 2),
        "ratio": round(float(r), 4),
    } for d, k, j, r in zip(merged["date"], merged["close_sec"], merged["close_dji"], merged["ratio"])]

    # 相对强弱：sec/DJI 价格比 zscore（滚动 250 日）
    ratio = merged["ratio"]
    zscore = (ratio - ratio.rolling(250).mean()) / ratio.rolling(250).std()
    rel_strength = [{"date": str(d.date()),
                     "ratio": round(float(r), 4),
                     "z": None if np.isnan(v) else round(float(v), 2)}
                    for d, r, v in zip(merged["date"], ratio, zscore)]

    # 极端日：交集期 |ret|>=3%
    ext = merged
    sec_evts = ext[ext["ret_sec"].abs() >= 3]
    dji_evts = ext[ext["ret_dji"].abs() >= 3]
    both = ext[(ext["ret_sec"].abs() >= 3) & (ext["ret_dji"].abs() >= 3)]
    either = ext[(ext["ret_sec"].abs() >= 3) | (ext["ret_dji"].abs() >= 3)]
    corr_ext = float(both["ret_sec"].corr(both["ret_dji"])) if len(both) > 1 else None
    extreme = {
        "start": str(ext["date"].iloc[0].date()),
        "end": str(ext["date"].iloc[-1].date()),
        "sec_only": int(len(sec_evts)), "dji_only": int(len(dji_evts)),
        "both": int(len(both)), "either": int(len(either)),
        "corr_on_extreme_days": corr_ext,
        "hit_rate_sec_given_dji": round(len(both) / len(dji_evts) * 100, 1) if len(dji_evts) else None,
        "hit_rate_dji_given_sec": round(len(both) / len(sec_evts) * 100, 1) if len(sec_evts) else None,
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
    }


def main():
    dji = load("DJI")
    secs = {t: load(t) for t, _ in PAIRS}
    out = {"meta": {
        "ref": "道琼斯工业指数 (DJI, 腾讯自选股 usDJI)",
        "ko": "Coca-Cola (KO)",
        "xlv": "SPDR Health Care Select Sector ETF 医疗保健",
        "source": "DJI: 腾讯自选股日线; KO/XLV: Yahoo Finance 日线（收盘价）",
        "note": "DJI 数据起点 2021-08-25，交集 2021-08-25 ~ 2026-08-25",
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
    }, "pairs": []}

    for t, label in PAIRS:
        res = analyze_pair(t, label, secs[t], dji)
        out["pairs"].append(res)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "ko_xlv_dji_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, allow_nan=False)
    print("saved:", path)

    # 汇总打印
    print("\n=== KO/XLV × 道琼斯 相关系数（Pearson）分阶段 ===")
    for pr in out["pairs"]:
        print(f"\n--- {pr['label']} [{pr['period']['start']} ~ {pr['period']['end']}, n={pr['period']['n']}] ---")
        for b in pr["blocks"]:
            print(f"  {b['name']:<24} pearson={b['pearson']:<6} spearman={b['spearman']:<6} beta={b['beta']:<6} n={b['n']} 超额={b.get('excess_ret')}pp")
        f = pr["fisher"]
        if f:
            print(f"  Fisher z(分界前vs后) = {f['z']}, p={f['p_value']}, sig={f['sig']}")
        e = pr["extreme"]
        print(f"  极端日(|r|>=3%): {e['sec_only']}/{e['dji_only']}/{e['both']} corr(同日)={e['corr_on_extreme_days']}")


if __name__ == "__main__":
    main()