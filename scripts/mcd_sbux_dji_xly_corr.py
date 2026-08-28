# -*- coding: utf-8 -*-
"""MCD / SBUX × 道琼斯(DJI) / 消费精选(XLY) 相关性对比分析。

口径（与 KO×道指 / CSCO×指数 / ABBV×IBB 系列保持一致）：
  - 日收益率：close pct_change × 100，Pearson / Spearman / p 值三档
  - 分阶段：全期 / 分界前(<2026-02-01) / 分界后(>=2026-02-01) / 2025-09以来 / 2026以来
  - Fisher z 检验分界前后相关系数差异显著性
  - 60 日滚动相关性（主口径）、月度/年度平均相关性
  - 相对强弱：标的/基准归一化价格与各阶段超额收益
  - 极端日验证：单日 |ret| >= 3% 的日子归属谁
  - 显著性三档：sig(p<0.01) / edge(0.01<=p<0.05) / no(p>=0.05)，带 p 值列
  - 跨基准对比：同一标的 × DJI vs × XLY 的相关性差异（Steiger 依赖 r 的差异方向提示，
    用 Fisher z 比较两相关是否可区分——样本相同为成对，用 r12 与 r13/r23 简化为方向判断，
    正式检验以分阶段数值为准）
输出 JSON 到 results/mcd_sbux_dji_xly_corr.json，供 HTML 报告使用。
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

# 标的(sec) × 基准(ref)：MCD/SBUX 是 XLY 成分股（必需消费品/可选消费非耐久）
PAIRS = [
    ("MCD", "麦当劳 MCD"),
    ("SBUX", "星巴克 SBUX"),
]
REFS = [
    ("DJI", "道琼斯工业指数"),
    ("XLY", "可选消费精选 XLY"),
]


def load(ticker: str) -> pd.DataFrame:
    p = os.path.join(DATA, ticker.upper(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 100
    return df


def pearson_pvalue(r, n):
    """t 分布近似 p 值（无 scipy 依赖）"""
    if n < 3 or r >= 1 or r <= -1:
        return 1.0
    t = r * sqrt((n - 2) / max(1e-9, (1 - r * r)))
    # 正则化不完全 beta 用数值积分近似？——改用标准正态近似 t(n-2)（n=120+ 时足够）
    # 正态近似：p = 2*(1-Phi(|t|))
    # 对 n>=30 足够精确，n=1260 时 t≈z
    import math
    phi = 0.5 * (1 + erf(abs(t) / sqrt(2)))
    return float(2 * (1 - phi))


def sig_band(pv):
    if pv < 0.01:
        return "sig"
    if pv < 0.05:
        return "edge"
    return "no"


def pearson_spearman(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, None, 0, 1.0
    p = float(np.corrcoef(a, b)[0, 1])
    s = float(pd.Series(a).rank().corr(pd.Series(b).rank()))
    pv = pearson_pvalue(p, len(a))
    return p, s, len(a), pv


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


def stats_block(sec: pd.DataFrame, ref: pd.DataFrame, name: str, start=None, end=None, anchor=None):
    # 必须先锚定交集起点（DJI 2021-08-25），否则 MCD×XLY 会算到 1998 年
    if anchor is not None:
        sec = sec[sec["date"] >= anchor]
        ref = ref[ref["date"] >= anchor]
    if start is not None:
        sec = sec[sec["date"] >= start]
        ref = ref[ref["date"] >= start]
    if end is not None:
        sec = sec[sec["date"] < end]
        ref = ref[ref["date"] < end]
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_ref")).dropna()
    if len(merged) < 5:
        return {"name": name, "n": 0}
    x = merged["ret_ref"].values
    y = merged["ret_sec"].values
    p, s, n, pv = pearson_spearman(y, x)
    beta = float(np.cov(x, y)[0, 1] / np.var(x)) if np.var(x) > 0 else np.nan
    resid = y - beta * x
    r2 = p * p
    sec_ret = (merged["close_sec"].iloc[-1] / merged["close_sec"].iloc[0] - 1) * 100
    ref_ret = (merged["close_ref"].iloc[-1] / merged["close_ref"].iloc[0] - 1) * 100
    return {
        "name": name, "n": int(n),
        "start": str(merged["date"].iloc[0].date()),
        "end": str(merged["date"].iloc[-1].date()),
        "pearson": round(p, 3), "spearman": round(s, 3),
        "p_value": round(pv, 4), "sig": sig_band(pv),
        "beta": round(float(beta), 3),
        "r2": round(float(r2), 3),
        "resid_vol": round(float(resid.std()), 2),
        "sec_ret_total": round(float(sec_ret), 2),
        "ref_ret_total": round(float(ref_ret), 2),
        "excess_ret": round(float(sec_ret - ref_ret), 2),
        "sec_vol": round(float(merged["ret_sec"].std()), 2),
        "ref_vol": round(float(merged["ret_ref"].std()), 2),
        "ann_vol_sec": round(float(merged["ret_sec"].std() * np.sqrt(252)), 1),
        "ann_vol_ref": round(float(merged["ret_ref"].std() * np.sqrt(252)), 1),
        "max_drawdown_sec": round(float(calc_mdd(merged["close_sec"].values)), 2),
        "max_drawdown_ref": round(float(calc_mdd(merged["close_ref"].values)), 2),
    }


def analyze_pair(tag: str, label: str, sec: pd.DataFrame, ref_tag: str, ref: pd.DataFrame):
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_ref")).dropna().reset_index(drop=True)
    merged = merged[merged["date"] >= ANCHOR].reset_index(drop=True)
    merged["ratio"] = merged["close_sec"] / merged["close_ref"]

    blocks = [
        stats_block(sec, ref, "全期（交集）", anchor=ANCHOR),
        stats_block(sec, ref, f"分界前 (< {SPLIT.date()})", end=SPLIT, anchor=ANCHOR),
        stats_block(sec, ref, f"分界后 (>= {SPLIT.date()})", start=SPLIT, anchor=ANCHOR),
        stats_block(sec, ref, "2025-09 以来", start=WINDOW_START, anchor=ANCHOR),
        stats_block(sec, ref, "2026 以来", start=YTD_START, anchor=ANCHOR),
    ]
    # 长窗口补充（不计入主表）：MCD 1995 / SBUX 2014 / XLY 1998 起的完整历史
    long_block = stats_block(sec, ref, "长窗口（有数据即全期）")
    fisher = None
    b_pre, b_post = blocks[1], blocks[2]
    if b_pre["n"] > 5 and b_post["n"] > 5:
        z, pv = fisher_z_test(b_pre["pearson"], b_pre["n"], b_post["pearson"], b_post["n"])
        fisher = {"z": z, "p_value": pv, "sig": bool(pv < 0.05)}

    # 滚动 60 日相关性（主口径）
    roll60 = merged["ret_sec"].rolling(60).corr(merged["ret_ref"]) * 100
    roll_series = [{"date": str(d.date()),
                    "corr": None if np.isnan(v) else round(float(v), 2)}
                   for d, v in zip(merged["date"], roll60)]

    # 月度平均相关性
    mm = merged.set_index("date")
    monthly = (mm[["ret_sec", "ret_ref"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_sec"]["ret_ref"] * 100).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 2)} for k, v in monthly.items()]

    # 年度相关性
    yearly = (mm[["ret_sec", "ret_ref"]].groupby(mm.index.year)[["ret_sec", "ret_ref"]]
              .corr().unstack()["ret_sec"]["ret_ref"] * 100).dropna()
    yearly_series = [{"year": int(k), "corr": round(float(v), 2)} for k, v in yearly.items()]

    # 归一化价格（交集起点=100）
    k0 = merged["close_sec"].iloc[0]
    d0 = merged["close_ref"].iloc[0]
    price_series = [{
        "date": str(d.date()),
        "sec": round(float(k) / k0 * 100, 2),
        "ref": round(float(j) / d0 * 100, 2),
        "ratio": round(float(r), 4),
    } for d, k, j, r in zip(merged["date"], merged["close_sec"], merged["close_ref"], merged["ratio"])]

    # 相对强弱：sec/ref 价格比 zscore（滚动 250 日）
    ratio = merged["ratio"]
    zscore = (ratio - ratio.rolling(250).mean()) / ratio.rolling(250).std()
    rel_strength = [{"date": str(d.date()),
                     "ratio": round(float(r), 4),
                     "z": None if np.isnan(v) else round(float(v), 2)}
                    for d, r, v in zip(merged["date"], ratio, zscore)]

    # 极端日：交集期 |ret|>=3%
    ext = merged
    sec_evts = ext[ext["ret_sec"].abs() >= 3]
    ref_evts = ext[ext["ret_ref"].abs() >= 3]
    both = ext[(ext["ret_sec"].abs() >= 3) & (ext["ret_ref"].abs() >= 3)]
    either = ext[(ext["ret_sec"].abs() >= 3) | (ext["ret_ref"].abs() >= 3)]
    corr_ext = float(both["ret_sec"].corr(both["ret_ref"])) if len(both) > 1 else None
    extreme = {
        "start": str(ext["date"].iloc[0].date()),
        "end": str(ext["date"].iloc[-1].date()),
        "sec_only": int(len(sec_evts)), "ref_only": int(len(ref_evts)),
        "both": int(len(both)), "either": int(len(either)),
        "corr_on_extreme_days": corr_ext,
        "hit_rate_sec_given_ref": round(len(both) / len(ref_evts) * 100, 1) if len(ref_evts) else None,
        "hit_rate_ref_given_sec": round(len(both) / len(sec_evts) * 100, 1) if len(sec_evts) else None,
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
        "tag": tag, "label": label, "ref_tag": ref_tag, "ref_label": REFS_MAP[ref_tag],
        "split": str(SPLIT.date()),
        "period": {"start": str(merged["date"].iloc[0].date()),
                   "end": str(merged["date"].iloc[-1].date()),
                   "n": int(len(merged))},
        "blocks": blocks, "fisher": fisher, "long": long_block,
        "rolling60": roll_series, "monthly": monthly_series, "yearly": yearly_series,
        "price_recent": price_series,
        "rel_strength": rel_strength, "extreme": extreme, "excess_annual": excess_annual,
    }


REFS_MAP = {"DJI": "道琼斯工业指数", "XLY": "可选消费精选 XLY"}


def main():
    dji = load("DJI")
    xly = load("XLY")
    refs = {"DJI": dji, "XLY": xly}
    secs = {t: load(t) for t, _ in PAIRS}

    out = {"meta": {
        "ref_dji": "道琼斯工业指数 (DJI)",
        "ref_xly": "SPDR Consumer Discretionary Select Sector ETF 可选消费",
        "mcd": "McDonald's 麦当劳 (MCD)",
        "sbux": "Starbucks 星巴克 (SBUX)",
        "note": "MCD/SBUX 均为 XLY 成分股。DJI 数据起点 2021-08-25，交集 2021-08-25 ~ 2026-08-26",
        "source": "DJI: 腾讯自选股日线; MCD/SBUX/XLY: 本地日线收盘价",
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
    }, "pairs": []}

    for t, label in PAIRS:
        for rtag in ["DJI", "XLY"]:
            res = analyze_pair(t, label, secs[t], rtag, refs[rtag])
            out["pairs"].append(res)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "mcd_sbux_dji_xly_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, allow_nan=False)
    print("saved:", path)

    # 汇总打印
    print("\n=== MCD/SBUX × DJI/XLY 相关系数（Pearson）分阶段 ===")
    for pr in out["pairs"]:
        print(f"\n--- {pr['label']} × {pr['ref_label']} [{pr['period']['start']} ~ {pr['period']['end']}, n={pr['period']['n']}] ---")
        for b in pr["blocks"]:
            print(f"  {b['name']:<24} pearson={b['pearson']:<6} p={b['p_value']:<7} {b['sig']:<4} spearman={b['spearman']:<6} beta={b['beta']:<6} n={b['n']} 超额={b.get('excess_ret')}pp")
        f = pr["fisher"]
        if f:
            print(f"  Fisher z(分界前vs后) = {f['z']}, p={f['p_value']}, sig={f['sig']}")
        e = pr["extreme"]
        print(f"  极端日(|r|>=3%): sec={e['sec_only']} ref={e['ref_only']} both={e['both']} corr(同日)={e['corr_on_extreme_days']}")


if __name__ == "__main__":
    main()