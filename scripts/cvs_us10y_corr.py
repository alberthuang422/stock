# -*- coding: utf-8 -*-
"""
CVS × US10Y（DGS10 名义 10Y 收益率）滚动相关性分析 —— 复用 gold_us10y_corr.py 模板
数据:
  - CVS  : data/cvs/CVS, 1D.csv（BATS 前复权 close，2010-12-31~2026-09-01）
  - US10Y: data/us_treasury/DGS10.csv（FRED，1962~2026-08-31）
口径:
  - CVS 日收益率 pct_change×100；US10Y 日变动 diff（bp 单位：×100 后再 diff）
  - 主口径 60 日滚动相关（项目惯例），30 日辅助
  - 分段: 2022-01 加息周期起点 / 2024-04 CVS 财报暴雷点 前后
  - 方向拆解: US10Y 上行日 vs 下行日 的 CVS 当日表现；|Δ|≥5bp 大波动日
输出: results/cvs_us10y_corr.json
"""
import os
import json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")


def load_cvs():
    df = pd.read_csv(os.path.join(DATA, "cvs", "CVS, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df[["date", "close"]].rename(columns={"close": "cvs"})
    df["cvs_ret"] = df["cvs"].pct_change() * 100
    return df


def load_us10y():
    df = pd.read_csv(os.path.join(DATA, "us_treasury", "DGS10.csv"), parse_dates=["observation_date"])
    df = df[["observation_date", "DGS10"]].rename(columns={"observation_date": "date", "DGS10": "us10y"})
    df = df.dropna().sort_values("date").reset_index(drop=True)
    df["us10y_bp"] = df["us10y"] * 100
    df["us10y_chg"] = df["us10y_bp"].diff()
    return df


def pearson(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, int(len(a))
    return float(np.corrcoef(a, b)[0, 1]), int(len(a))


def roll(df, n):
    c = df["cvs_ret"].rolling(n).corr(df["us10y_chg"])
    return [{"date": d.strftime("%Y-%m-%d"), "r": (None if pd.isna(v) else round(float(v), 3))}
            for d, v in zip(df["date"], c)]


def static_stats(sub):
    r, n = pearson(sub["cvs_ret"].values, sub["us10y_chg"].values)
    # t 检验近似（Fisher 近似下的显著性边界 |r| > 2/sqrt(n)）
    sig = (r is not None) and abs(r) > 2 / np.sqrt(n)
    return {"r": (None if r is None else round(r, 3)), "n": n, "sig": bool(sig)}


def main():
    cvs, us10y = load_cvs(), load_us10y()
    df = cvs.merge(us10y, on="date", how="inner").dropna(subset=["cvs_ret", "us10y_chg"]).reset_index(drop=True)
    win = f"{df.date.iloc[0].date()} ~ {df.date.iloc[-1].date()}"
    out = {
        "window": win, "n": int(len(df)),
        "cvs_src": "BATS 前复权（TradingView，2026-09-02）",
        "us10y_src": f"FRED DGS10（~{us10y.date.iloc[-1].date()}）",
        "us10y_last": float(us10y.us10y.iloc[-1]),
        "cvs_last": float(df.cvs.iloc[-1]),
    }

    # 全期 + 近端静态
    out["full"] = static_stats(df)
    for n in (20, 40, 60):
        out[f"recent_{n}"] = static_stats(df.tail(n))

    # 滚动曲线
    out["roll60"] = roll(df, 60)
    out["roll30"] = roll(df, 30)
    r60 = pd.Series([x["r"] if x["r"] is not None else np.nan for x in out["roll60"]])
    out["roll60_stats"] = {
        "min": round(float(r60.min()), 3), "min_date": df.date.iloc[int(r60.idxmin())].strftime("%Y-%m-%d"),
        "max": round(float(r60.max()), 3), "max_date": df.date.iloc[int(r60.idxmax())].strftime("%Y-%m-%d"),
        "latest": out["recent_20"]["r"], "neg_share": round(float((r60 < 0).mean() * 100), 1),
        "abs_gt_03_share": round(float((r60.abs() > 0.3).mean() * 100), 1),
    }

    # 分段静态（加息周期 / CVS 财报暴雷）
    for lab, cond in [("pre_2022", df.date < "2022-01-01"), ("2022_2024", (df.date >= "2022-01-01") & (df.date < "2024-04-01")),
                      ("post_2024", df.date >= "2024-04-01")]:
        out[f"seg_{lab}"] = static_stats(df[cond])

    # 方向拆解：US10Y 上行/下行日
    up, dn = df[df.us10y_chg > 0], df[df.us10y_chg < 0]
    out["direction"] = {
        "up_days": {"n": int(len(up)), "cvs_med": round(float(up.cvs_ret.median()), 3),
                    "win": round(float((up.cvs_ret > 0).mean() * 100), 1)},
        "dn_days": {"n": int(len(dn)), "cvs_med": round(float(dn.cvs_ret.median()), 3),
                    "win": round(float((dn.cvs_ret > 0).mean() * 100), 1)},
    }

    # 大波动日 |Δ|>=5bp
    big = df[df.us10y_chg.abs() >= 5]
    big_up, big_dn = big[big.us10y_chg > 0], big[big.us10y_chg < 0]
    out["big_moves"] = {
        "n": int(len(big)),
        "bp_up": {"n": int(len(big_up)), "cvs_med": round(float(big_up.cvs_ret.median()), 3),
                  "win": round(float((big_up.cvs_ret > 0).mean() * 100), 1)},
        "bp_dn": {"n": int(len(big_dn)), "cvs_med": round(float(big_dn.cvs_ret.median()), 3),
                  "win": round(float((big_dn.cvs_ret > 0).mean() * 100), 1)},
    }

    # 分年度相关（细颗粒结构）
    yr = []
    for y, g in df.groupby(df.date.dt.year):
        r, n = pearson(g["cvs_ret"].values, g["us10y_chg"].values)
        yr.append({"y": int(y), "r": (None if r is None else round(r, 3)), "n": int(n)})
    out["yearly"] = yr

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "cvs_us10y_corr.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"窗口 {win}  n={len(df)}")
    print(f"全期 r={out['full']['r']} (n={out['full']['n']}, sig={out['full']['sig']})")
    print(f"近20={out['recent_20']} 近40={out['recent_40']} 近60={out['recent_60']}")
    print(f"roll60: {out['roll60_stats']}")
    print(f"分段: pre2022={out['seg_pre_2022']} 2022-2024={out['seg_2022_2024']} post2024={out['seg_post_2024']}")
    print(f"方向: {out['direction']}")
    print(f"大波动(>=5bp): {out['big_moves']}")
    print("年度:", [(d['y'], d['r']) for d in out['yearly']])


if __name__ == "__main__":
    main()
