# -*- coding: utf-8 -*-
"""KBWB（Invesco KBW Bank ETF）vs MS（Morgan Stanley）相关性分析。

数据：data/kbwb/、data/ms/（Yahoo 1D，列 date,open,high,low,close,volume,adj_close）
窗口：两标的同时有数据区间（2011-11 起）
维度：
  1) 日收益 Pearson/Spearman 相关（全期 + 分阶段 + 近 1/3 年）
  2) 滚动 60 日 + 月频相关序列
  3) beta / R² / 残差波动（以 KBWB 为市场代理）
  4) 阶段收益 / 波动 / 回撤 / 夏普对比
  5) 相对强弱比值（KBWB/MS）
  6) 同涨同跌占比 + 条件收益（KBWB 涨/跌日 MS 表现）
输出 results/kbwb_ms_corr.json；控制台只打汇总 KPI。
"""
import os
import json
import math

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
SPLIT = pd.Timestamp("2026-02-01")  # 结构分界点（沿用项目口径）


def load(ticker: str) -> pd.DataFrame:
    p = os.path.join(DATA, ticker.lower(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change() * 100
    return df


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a[~np.isnan(a) & ~np.isnan(b)], b[~np.isnan(a) & ~np.isnan(b)]
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    return float(np.corrcoef(ra, rb)[0, 1])


def stats_block(kbwb: pd.DataFrame, ms: pd.DataFrame, name: str) -> dict:
    m = pd.merge(kbwb[["date", "ret"]], ms[["date", "ret"]],
                 on="date", suffixes=("_kbwb", "_ms")).dropna()
    if len(m) < 5:
        return {"name": name, "n": 0}
    x = m["ret_kbwb"].values  # KBWB 收益
    y = m["ret_ms"].values    # MS 收益
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman_v = spearman(x, y)
    beta = float(np.cov(y, x)[0, 1] / np.var(x))  # MS 对 KBWB 的 beta
    r2 = pearson * pearson
    resid = y - beta * x
    p_same = float(np.mean(np.sign(x) == np.sign(y)))  # 同向占比
    # 条件收益：KBWB 涨/跌日 MS 的日收益均值
    up_mask = x > 0
    dn_mask = x < 0
    ms_up = float(y[up_mask].mean()) if up_mask.sum() > 5 else None
    ms_dn = float(y[dn_mask].mean()) if dn_mask.sum() > 5 else None
    wr_kbwb = float(np.mean(x > 0))  # KBWB 上涨日占比
    return {
        "name": name,
        "n": int(len(m)),
        "start": str(m["date"].iloc[0].date()),
        "end": str(m["date"].iloc[-1].date()),
        "pearson": round(pearson, 4),
        "spearman": round(spearman_v, 4),
        "beta": round(beta, 3),          # MS ~ KBWB
        "r2": round(r2, 4),
        "resid_vol": round(float(resid.std()), 3),  # MS 残差日波动 %
        "p_same_dir": round(float(p_same) * 100, 1),   # 同涨同跌占比 %
        "wr_kbwb": round(wr_kbwb * 100, 1),            # KBWB 涨日占比 %
        "ms_ret_on_kbwb_up": round(ms_up, 3) if ms_up is not None else None,
        "ms_ret_on_kbwb_dn": round(ms_dn, 3) if ms_dn is not None else None,
    }


def price_stats(merged: pd.DataFrame, name: str) -> dict:
    """价格区间收益/波动/回撤（KBWB 与 MS）"""
    out = {"name": name}
    for sym in ("kbwb", "ms"):
        sub = merged.dropna(subset=[f"close_{sym}"])
        if len(sub) < 2:
            out[sym] = None
            continue
        s = sub[f"close_{sym}"]
        r = s.pct_change().dropna()
        cummax = s.cummax()
        dd = float((s / cummax - 1).min())
        total = float(s.iloc[-1] / s.iloc[0] - 1) * 100
        ann_ret = float((s.iloc[-1] / s.iloc[0]) ** (252 / len(s)) - 1) * 100
        vol = float(r.std() * math.sqrt(252)) * 100
        out[sym] = {
            "total_ret": round(total, 1),      # %
            "ann_ret": round(ann_ret, 1),      # %
            "ann_vol": round(vol, 1),          # %
            "max_dd": round(dd * 100, 1),      # %
            "sharpe": round(ann_ret / vol, 2) if vol > 0 else None,
            "n_days": int(len(s)),
        }
    return out


def main():
    kbwb = load("KBWB")
    ms = load("MS")
    m = pd.merge(kbwb[["date", "adj_close", "ret"]],
                 ms[["date", "adj_close", "ret"]],
                 on="date", suffixes=("_kbwb", "_ms")).dropna().reset_index(drop=True)
    m = m.rename(columns={"adj_close_kbwb": "close_kbwb", "adj_close_ms": "close_ms"})
    m["ratio"] = m["close_kbwb"] / m["close_ms"]
    print(f"统一窗口: {m['date'].iloc[0].date()} ~ {m['date'].iloc[-1].date()}  n={len(m)}")

    # ---- 基础分块 ----
    blocks = [
        stats_block(kbwb, ms, "全期"),
        stats_block(kbwb[kbwb["date"] < SPLIT], ms[ms["date"] < SPLIT], f"分界前 ({SPLIT.date()} 前)"),
        stats_block(kbwb[kbwb["date"] >= SPLIT], ms[ms["date"] >= SPLIT], f"分界后 ({SPLIT.date()} 起)"),
        stats_block(kbwb[kbwb["date"] >= "2023-01-01"], ms[ms["date"] >= "2023-01-01"], "近 3 年"),
        stats_block(kbwb[kbwb["date"] >= "2025-08-01"], ms[ms["date"] >= "2025-08-01"], "近 1 年"),
    ]

    # 分界前后相关性差异显著性（Fisher z）
    from math import atanh, sqrt, erf
    r1, n1 = blocks[1]["pearson"], blocks[1]["n"]
    r2, n2 = blocks[2]["pearson"], blocks[2]["n"]
    z = (atanh(r1) - atanh(r2)) / sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    p_val = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    fisher = {"z": round(float(z), 3), "p_value": round(float(p_val), 4),
              "sig": bool(p_val < 0.05)}

    # ---- 滚动 60 日相关 ----
    roll = m["ret_kbwb"].rolling(60).corr(m["ret_ms"])
    roll_series = [{"date": str(d.date()), "corr": None if np.isnan(v) else round(float(v), 3)}
                   for d, v in zip(m["date"], roll)]

    # ---- 月频相关（近 5 年，全部月份序列）----
    mm = m.set_index("date")
    monthly = (mm[["ret_kbwb", "ret_ms"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_kbwb"]["ret_ms"]).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 3)} for k, v in monthly.items()]
    monthly_3y = [x for x in monthly_series if x["month"] >= "2023-08"]
    print(f"月频相关: 均值 {monthly.mean():.3f} | 近36月均值 "
          f"{np.mean([x['corr'] for x in monthly_3y]):.3f} | 最新 {monthly.iloc[-1]:.3f} ({monthly.index[-1].date()})")

    # ---- 价格统计（全期 / 分界后 / 近1年）----
    def seg_pricestats(start=None):
        sub = m if start is None else m[m["date"] >= start]
        return price_stats(sub, str(sub["date"].iloc[0].date()) if len(sub) else "")

    price_blocks = {
        "full": price_stats(m, "全期"),
        "after_split": seg_pricestats("2026-02-01"),
        "last1y": seg_pricestats("2025-08-21"),
    }

    # ---- 相对强弱 ----
    ratio = m["ratio"] / m["ratio"].iloc[0]
    def date_at(idx):
        return str(m.loc[idx, "date"].date())
    ratio_info = {
        "start_ratio": round(float(m["ratio"].iloc[0]), 4),
        "latest_ratio": round(float(m["ratio"].iloc[-1]), 4),
        "norm_latest": round(float(ratio.iloc[-1]), 3),
        "max": round(float(ratio.max()), 3), "max_date": date_at(ratio.idxmax()),
        "min": round(float(ratio.min()), 3), "min_date": date_at(ratio.idxmin()),
    }

    # ---- 年度收益对比 ----
    yearly = {}
    for y, g in m.groupby(m["date"].dt.year):
        row = {}
        for sym in ("kbwb", "ms"):
            s = g[f"close_{sym}"]
            row[sym] = round(float(s.iloc[-1] / s.iloc[0] - 1) * 100, 1)
        row["diff"] = round(row["kbwb"] - row["ms"], 1)
        yearly[int(y)] = row
    years = sorted(yearly)
    print("\n年度收益 (KBWB vs MS, %):")
    for y in years:
        r = yearly[y]
        print(f"  {y}: KBWB {r['kbwb']:+.1f}  MS {r['ms']:+.1f}  差 {r['diff']:+.1f}")

    # ---- 日收益散点（近 3 年，分界前/后分色）----
    sc = m[m["date"] >= "2023-01-01"]
    scatter = [{"date": str(d.date()), "x": round(float(x), 3), "y": round(float(yv), 3),
                "after": bool(d >= SPLIT)}
               for d, x, yv in zip(sc["date"], sc["ret_kbwb"], sc["ret_ms"])]

    # ---- 近半年价格序列（归一化=1 起点，供双线图）----
    recent = m[m["date"] >= "2026-01-01"].copy()
    norm_k = recent["close_kbwb"] / recent["close_kbwb"].iloc[0]
    norm_m = recent["close_ms"] / recent["close_ms"].iloc[0]
    series_2026 = [{"date": str(d.date()),
                    "kbwb": round(float(k), 4), "ms": round(float(v), 4)}
                   for d, k, v in zip(recent["date"], norm_k, norm_m)]

    # 全期归一化（每 10 交易日采样）供长图
    nK = m["close_kbwb"] / m["close_kbwb"].iloc[0]
    nM = m["close_ms"] / m["close_ms"].iloc[0]
    full_series = [{"date": str(d.date()),
                    "kbwb": round(float(k), 3), "ms": round(float(v), 3)}
                   for d, k, v in zip(m["date"][::10], nK[::10], nM[::10])]

    # ---- 同涨同跌与条件统计（近 1 年）----
    last1y = m[m["date"] >= "2025-08-21"]
    p_same1y = float(np.mean(np.sign(last1y["ret_kbwb"]) == np.sign(last1y["ret_ms"]))) * 100

    out = {
        "split": str(SPLIT.date()),
        "period": {"start": str(m["date"].iloc[0].date()), "end": str(m["date"].iloc[-1].date()),
                   "n": int(len(m))},
        "blocks": blocks,
        "fisher": fisher,
        "rolling60": roll_series,
        "monthly": monthly_series,
        "price_blocks": price_blocks,
        "ratio": ratio_info,
        "yearly": yearly,
        "years": years,
        "scatter": scatter,
        "series_2026": series_2026,
        "full_series": full_series,
        "same_dir_1y": round(p_same1y, 1),
        "meta": {
            "kbwb": "Invesco KBW Bank ETF (KBWB)",
            "ms": "Morgan Stanley (MS)",
            "note": "周三 1D; adj_close 口径; KBWB 等权银行 ETF 覆盖传统银行+大行, MS 为投行, 故解析其与板块联动度的结构差异",
            "source": "Yahoo Finance 日线(复权收盘)",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        },
    }

    assert all(np.isfinite(b.get("pearson", 0)) for b in blocks), "NaN in blocks"
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "kbwb_ms_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nsaved: {path}")

    print("\n=== 分块相关（Pearson / Spearman / β / R² / 同向占比）===")
    for b in blocks:
        if b["n"]:
            print(f"  {b['name']:28s} n={b['n']:5d}  P={b['pearson']:.3f}  Sp={b['spearman']:.3f}  "
                  f"β={b['beta']:+.2f}  R²={b['r2']:.2f}  同向{b['p_same_dir']:.0f}%  "
                  f"KBWB涨日MS均{b['ms_ret_on_kbwb_up']:+.3f}% / KBWB跌日MS均{b['ms_ret_on_kbwb_dn']:+.3f}%")
    print(f"Fisher z: {fisher['z']}  p={fisher['p_value']}  {'显著' if fisher['sig'] else '不显著'}")
    print(f"同向占比(近1年): {p_same1y:.1f}%")
    for k, v in price_blocks.items():
        if v.get("kbwb"):
            print(f"  [{k}] KBWB 总收益 {v['kbwb']['total_ret']:+.1f}% / MS {v['ms']['total_ret']:+.1f}% | "
                  f"年化波动 KBWB {v['kbwb']['ann_vol']:.0f}% / MS {v['ms']['ann_vol']:.0f}% | "
                  f"最大回撤 KBWB {v['kbwb']['max_dd']:.0f}% / MS {v['ms']['max_dd']:.0f}%")
    print(f"相对强弱 KBWB/MS 归一化: 起点 1.00 → 最新 {ratio_info['norm_latest']:.2f} "
          f"(高点 {ratio_info['max']:.2f} {ratio_info['max_date']} / 低点 {ratio_info['min']:.2f} {ratio_info['min_date']})")


if __name__ == "__main__":
    main()