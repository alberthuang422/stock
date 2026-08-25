#!/usr/bin/env python3
"""KO (可口可乐) × XLK(科技) / XPH(制药,代理IHE) / XLV(医疗保健) 相关性分析。

口径（与 IHI×XBI / IBB×GILD 系列保持一致）：
  - 日收益率：close pct_change × 100，Pearson / Spearman
  - 分阶段：全期 / 分界前(<2026-02-01) / 分界后(>=2026-02-01) / 2025-09以来 / 2026以来
    （分界点沿用项目惯例 2026-02 结构断裂点；2025-09 为对照分析默认窗口起点）
  - Fisher z 检验分界前后相关系数差异显著性
  - KO 对板块的 beta（日收益回归）+ R²
  - 滚动 60 日相关性（主口径）、月度/年度平均相关性
  - 相对强弱：KO/板块价格比（对数价差），各阶段超额收益
  - 极端日验证：单日 |ret| >= 3% 的日子归属谁、同日大波动相关
输出 JSON 到 results/ko_sector_corr.json，供 HTML 报告使用。
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

PAIRS = [
    ("XLK", "科技 XLK", "SPDR 科技板块 ETF"),
    ("XPH", "制药 XPH(代理IHE)", "SPDR 标普制药 ETF"),
    ("XLV", "医疗保健 XLV", "SPDR 医疗保健 ETF"),
]

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
    running_max = np.maximum.accumulate(prices)
    dd = (prices / running_max - 1) * 100
    return float(dd.min())

def fisher_z_test(r1, n1, r2, n2):
    z = (atanh(r1) - atanh(r2)) / sqrt(1/(n1-3) + 1/(n2-3))
    p_val = 2 * (1 - 0.5 * (1 + erf(abs(z)/sqrt(2))))
    return round(float(z), 3), round(float(p_val), 4)

def stats_block(ko: pd.DataFrame, sec: pd.DataFrame, name: str, start=None, end=None):
    if start is not None:
        ko = ko[ko["date"] >= start]
        sec = sec[sec["date"] >= start]
    if end is not None:
        ko = ko[ko["date"] < end]
        sec = sec[sec["date"] < end]
    merged = pd.merge(ko[["date", "close", "ret"]], sec[["date", "close", "ret"]],
                      on="date", suffixes=("_ko", "_sec")).dropna()
    if len(merged) < 5:
        return {"name": name, "n": 0}
    x = merged["ret_sec"].values   # 板块
    y = merged["ret_ko"].values    # KO
    p, s, n = pearson_spearman(y, x)
    beta = float(np.cov(y, x)[0, 1] / np.var(x)) if np.var(x) > 0 else np.nan
    resid = y - beta * x
    r2 = p * p
    ko_ret = (merged["close_ko"].iloc[-1] / merged["close_ko"].iloc[0] - 1) * 100
    sec_ret = (merged["close_sec"].iloc[-1] / merged["close_sec"].iloc[0] - 1) * 100
    return {
        "name": name, "n": int(n),
        "start": str(merged["date"].iloc[0].date()),
        "end": str(merged["date"].iloc[-1].date()),
        "pearson": round(p, 3), "spearman": round(s, 3),
        "beta": round(float(beta), 3),
        "r2": round(float(r2), 3),
        "resid_vol": round(float(resid.std()), 2),
        "ko_ret_total": round(float(ko_ret), 2),
        "sec_ret_total": round(float(sec_ret), 2),
        "excess_ret": round(float(ko_ret - sec_ret), 2),   # KO 相对板块（pp）
        "ko_vol": round(float(merged["ret_ko"].std()), 2),
        "sec_vol": round(float(merged["ret_sec"].std()), 2),
        "ann_vol_ko": round(float(merged["ret_ko"].std() * np.sqrt(252)), 1),
        "ann_vol_sec": round(float(merged["ret_sec"].std() * np.sqrt(252)), 1),
        "max_drawdown_ko": round(float(calc_mdd(merged["close_ko"].values)), 2),
        "max_drawdown_sec": round(float(calc_mdd(merged["close_sec"].values)), 2),
    }

def analyze_pair(tag: str, label: str, desc: str, ko: pd.DataFrame, sec: pd.DataFrame):
    merged = pd.merge(ko[["date", "close", "ret"]], sec[["date", "close", "ret"]],
                      on="date", suffixes=("_ko", "_sec")).dropna().reset_index(drop=True)
    merged["ratio"] = merged["close_ko"] / merged["close_sec"]
    merged["spread"] = np.log(merged["close_ko"]) - np.log(merged["close_sec"])

    blocks = [
        stats_block(ko, sec, "全期"),
        stats_block(ko, sec, f"分界前 (< {SPLIT.date()})", end=SPLIT),
        stats_block(ko, sec, f"分界后 (>= {SPLIT.date()})", start=SPLIT),
        stats_block(ko, sec, "2025-09 以来", start=WINDOW_START),
        stats_block(ko, sec, "2026 以来", start=YTD_START),
    ]
    fisher = None
    b_pre, b_post = blocks[1], blocks[2]
    if b_pre["n"] > 5 and b_post["n"] > 5:
        z, pv = fisher_z_test(b_pre["pearson"], b_pre["n"], b_post["pearson"], b_post["n"])
        fisher = {"z": z, "p_value": pv, "sig": bool(pv < 0.05)}

    # 滚动 60 日相关性（主口径）
    roll60 = merged["ret_ko"].rolling(60).corr(merged["ret_sec"]) * 100
    roll_series = [{"date": str(d.date()),
                    "corr": None if np.isnan(v) else round(float(v), 2)}
                   for d, v in zip(merged["date"], roll60)]

    # 月度平均相关性
    mm = merged.set_index("date")
    monthly = (mm[["ret_ko", "ret_sec"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_ko"]["ret_sec"] * 100).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 2)} for k, v in monthly.items()]

    # 年度相关性
    yearly = (mm[["ret_ko", "ret_sec"]].groupby(mm.index.year)[["ret_ko", "ret_sec"]]
              .corr().unstack()["ret_ko"]["ret_sec"] * 100).dropna()
    yearly_series = [{"year": int(k), "corr": round(float(v), 2)} for k, v in yearly.items()]

    # 价格序列（近 24 个月 + 分界后）
    recent = merged[merged["date"] >= "2024-06-01"]
    price_series = [{
        "date": str(d.date()),
        "ko": round(float(k), 2), "sec": round(float(s), 2),
        "ratio": round(float(r), 4),
    } for d, k, s, r in zip(recent["date"], recent["close_ko"], recent["close_sec"], recent["ratio"])]

    # 标准化价格（分界前后，起点=100）
    norm_series = []
    for ph, sub in [("pre", merged[merged["date"] < SPLIT]), ("post", merged[merged["date"] >= SPLIT])]:
        if len(sub) < 2:
            continue
        k0, s0 = sub["close_ko"].iloc[0], sub["close_sec"].iloc[0]
        norm_series.append({
            "phase": ph,
            "start": str(sub["date"].iloc[0].date()),
            "end": str(sub["date"].iloc[-1].date()),
            "series": [{
                "date": str(d.date()),
                "ko": round(float(k) / k0 * 100, 2),
                "sec": round(float(s) / s0 * 100, 2),
            } for d, k, s in zip(sub["date"], sub["close_ko"], sub["close_sec"])],
        })

    # 相对强弱：KO/板块 价格比 zscore（滚动 250 日）
    ratio = merged["ratio"]
    zscore = (ratio - ratio.rolling(250).mean()) / ratio.rolling(250).std()
    rel_strength = [{"date": str(d.date()),
                     "ratio": round(float(r), 4),
                     "z": None if np.isnan(v) else round(float(v), 2)}
                    for d, r, v in zip(merged["date"], ratio, zscore)]

    # 极端日：近 5 年 |ret|>=3%
    ext = merged[merged["date"] >= "2021-01-01"]
    ko_evts = ext[ext["ret_ko"].abs() >= 3]
    sec_evts = ext[ext["ret_sec"].abs() >= 3]
    both = ext[(ext["ret_ko"].abs() >= 3) & (ext["ret_sec"].abs() >= 3)]
    either = ext[(ext["ret_ko"].abs() >= 3) | (ext["ret_sec"].abs() >= 3)]
    corr_ext = float(both["ret_ko"].corr(both["ret_sec"])) if len(both) > 1 else None
    extreme = {
        "start": str(ext["date"].iloc[0].date()),
        "ko_only": int(len(ko_evts)), "sec_only": int(len(sec_evts)),
        "both": int(len(both)), "either": int(len(either)),
        "corr_on_extreme_days": corr_ext,
        "hit_rate_ko_given_sec": round(len(both) / len(sec_evts) * 100, 1) if len(sec_evts) else None,
        "hit_rate_sec_given_ko": round(len(both) / len(ko_evts) * 100, 1) if len(ko_evts) else None,
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
        "tag": tag, "label": label, "desc": desc,
        "split": str(SPLIT.date()),
        "period": {"start": str(merged["date"].iloc[0].date()),
                   "end": str(merged["date"].iloc[-1].date()),
                   "n": int(len(merged))},
        "blocks": blocks, "fisher": fisher,
        "rolling60": roll_series, "monthly": monthly_series, "yearly": yearly_series,
        "price_recent": price_series, "norm_series": norm_series,
        "rel_strength": rel_strength, "extreme": extreme, "excess_annual": excess_annual,
    }

def main():
    ko = load("KO")
    xs = {t: load(t) for t, _, _ in PAIRS}
    out = {"meta": {
        "ko": "Coca-Cola (KO)",
        "xlk": "SPDR Technology Select Sector ETF",
        "xph": "SPDR S&P Pharmaceuticals ETF (代理 IHE iShares 美国制药)",
        "xlv": "SPDR Health Care Select Sector ETF",
        "source": "Yahoo Finance 日线（收盘价）",
        "note": "用户原指 IHE(制药)，本地无 IHE 数据，用成分高度重叠的 XPH 代理；四标的取交集 2006-2026",
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
    }, "pairs": []}

    for t, label, desc in PAIRS:
        res = analyze_pair(t, label, desc, ko, xs[t])
        out["pairs"].append(res)
        xs[t] = res  # placeholder not needed

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "ko_sector_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", path)

    # 汇总打印
    print("\n=== KO × 各板块 相关系数（Pearson）分阶段 ===")
    for pr in out["pairs"]:
        print(f"\n--- {pr['label']} [{pr['period']['start']} ~ {pr['period']['end']}, n={pr['period']['n']}] ---")
        for b in pr["blocks"]:
            print(f"  {b['name']:<22} pearson={b['pearson']:<6} spearman={b['spearman']:<6} beta={b['beta']:<6} n={b['n']}")
        f = pr["fisher"]
        if f:
            print(f"  Fisher z(分界前vs后) = {f['z']}, p={f['p_value']}, sig={f['sig']}")
        e = pr["extreme"]
        print(f"  极端日(近5年|r|>=3%): KO仅={e['ko_only']} 板块仅={e['sec_only']} 同日={e['both']} corr(同日)={e['corr_on_extreme_days']}")

if __name__ == "__main__":
    main()