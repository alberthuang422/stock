# -*- coding: utf-8 -*-
"""
CVS × IHE（iShares 美国制药 ETF）日收益相关性分析
数据:
  - CVS : data/cvs/CVS, 1D.csv（Yahoo adj_close 前复权，2010-12-31 起）
  - IHE : data/ihe/IHE, 1D.csv（Yahoo adj_close 前复权，2021-08-26 起）
口径（项目铁律）:
  - 两者均日收益率 pct_change×100
  - 主口径 60 日滚动相关，30 日辅助
  - 分段（与 66 号 / cvs_us10y_corr.py 对齐）:
      pre_2022    ~2021-12-31   （IHE 上市初期/宽松末段）
      2022_2024   2022-01-01~2024-03-31（加息周期 + CVS 暴雷前）
      post_2024   2024-04-01~   （CVS 2024-04 财报暴雷 / 换帅转型）
输出: results/cvs_ihe_corr.json
"""
import os
import json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")


def load(sym, col="adj_close", path=None):
    p = path or os.path.join(DATA, sym.lower(), f"{sym}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df[["date", col]].rename(columns={col: sym.lower()})
    df[f"{sym.lower()}_ret"] = df[sym.lower()].pct_change() * 100
    return df


def pearson(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, int(len(a))
    r = float(np.corrcoef(a, b)[0, 1])
    # Fisher 近似的显著性边界 |r| > 2/sqrt(n)（p≈0.05），与项目历史脚本一致
    return round(r, 3), int(len(a))


def static_stats(sub):
    r, n = pearson(sub["cvs_ret"].values, sub["ihe_ret"].values)
    return {"r": r, "n": n, "sig": bool(r is not None and abs(r) > 2 / np.sqrt(n))}


def roll(df, n):
    c = df["cvs_ret"].rolling(n).corr(df["ihe_ret"])
    return [{"date": d.strftime("%Y-%m-%d"), "r": (None if pd.isna(v) else round(float(v), 3))}
            for d, v in zip(df["date"], c)]


def main():
    cvs, ihe = load("CVS"), load("IHE")
    df = cvs.merge(ihe, on="date", how="inner").dropna(subset=["cvs_ret", "ihe_ret"]).reset_index(drop=True)

    # IHE 缺失复权价的日剔除（adj_close 为 0 或 NaN 会导致假收益率）
    bad = df[(df["cvs_ret"].abs() > 50) | (df["ihe_ret"].abs() > 50)]
    if len(bad):
        print(f"[warn] 剔除极端收益率 {len(bad)} 行: {list(bad.date.dt.strftime('%Y-%m-%d'))}")
        df = df[(df["cvs_ret"].abs() <= 50) & (df["ihe_ret"].abs() <= 50)].reset_index(drop=True)

    win = f"{df.date.iloc[0].date()} ~ {df.date.iloc[-1].date()}"
    out = {
        "pair": "CVS × IHE (iShares 美国制药 ETF)",
        "window": win, "n": int(len(df)),
        "cvs_src": "Yahoo adj_close（data/cvs）",
        "ihe_src": "Yahoo adj_close（data/ihe）",
        "cvs_last": float(df.cvs.iloc[-1]), "ihe_last": float(df.ihe.iloc[-1]),
    }

    # 全期 + 近端静态
    out["full"] = static_stats(df)
    for n in (20, 40, 60, 120):
        out[f"recent_{n}"] = static_stats(df.tail(n))

    # 滚动曲线
    out["roll60"] = roll(df, 60)
    out["roll30"] = roll(df, 30)
    r60 = pd.Series([x["r"] if x["r"] is not None else np.nan for x in out["roll60"]])
    r30 = pd.Series([x["r"] if x["r"] is not None else np.nan for x in out["roll30"]])
    out["roll60_stats"] = {
        "min": round(float(r60.min()), 3), "min_date": df.date.iloc[int(r60.idxmin())].strftime("%Y-%m-%d"),
        "max": round(float(r60.max()), 3), "max_date": df.date.iloc[int(r60.idxmax())].strftime("%Y-%m-%d"),
        "latest": out["recent_60"]["r"],
        "neg_share": round(float((r60 < 0).mean() * 100), 1),
        "abs_gt_03_share": round(float((r60.abs() > 0.3).mean() * 100), 1),
        "median": round(float(r60.median()), 3),
    }

    # 分段静态（对齐 66 号/cvs_us10y 分段）
    segs = [
        ("pre_2022", df.date < "2022-01-01"),
        ("2022_2024", (df.date >= "2022-01-01") & (df.date < "2024-04-01")),
        ("post_2024", df.date >= "2024-04-01"),
    ]
    for lab, cond in segs:
        sub = df[cond]
        out[f"seg_{lab}"] = {**static_stats(sub), "n_days": int(len(sub)),
                             "start": sub.date.iloc[0].strftime("%Y-%m-%d"), "end": sub.date.iloc[-1].strftime("%Y-%m-%d")}

    # 方向拆解：IHE 涨/跌日 CVS 的当日表现（CVS 是否跟随制药板块方向）
    up, dn = df[df.ihe_ret > 0], df[df.ihe_ret < 0]
    out["direction"] = {
        "ihe_up": {"n": int(len(up)), "cvs_med": round(float(up.cvs_ret.median()), 3),
                   "cvs_win": round(float((up.cvs_ret > 0).mean() * 100), 1)},
        "ihe_dn": {"n": int(len(dn)), "cvs_med": round(float(dn.cvs_ret.median()), 3),
                   "cvs_win": round(float((dn.cvs_ret > 0).mean() * 100), 1)},
    }

    # 大波动日（IHE |ret|>=2%）
    big = df[df.ihe_ret.abs() >= 2]
    big_up, big_dn = big[big.ihe_ret > 0], big[big.ihe_ret < 0]
    out["big_moves"] = {
        "n": int(len(big)),
        "ihe_up": {"n": int(len(big_up)), "cvs_med": round(float(big_up.cvs_ret.median()), 3),
                   "cvs_win": round(float((big_up.cvs_ret > 0).mean() * 100), 1)},
        "ihe_dn": {"n": int(len(big_dn)), "cvs_med": round(float(big_dn.cvs_ret.median()), 3),
                   "cvs_win": round(float((big_dn.cvs_ret > 0).mean() * 100), 1)},
    }

    # 分年度
    out["yearly"] = [{"y": int(y), **static_stats(g)} for y, g in df.groupby(df.date.dt.year)]

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "cvs_ihe_corr.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"窗口 {win}  n={len(df)}")
    print(f"全期 r={out['full']['r']} (n={out['full']['n']}, sig={out['full']['sig']})")
    print(f"近20={out['recent_20']} 近40={out['recent_40']} 近60={out['recent_60']} 近120={out['recent_120']}")
    print(f"roll60: {out['roll60_stats']}")
    for lab, _ in segs:
        s = out[f"seg_{lab}"]
        print(f"分段 {lab}: r={s['r']} n={s['n']} sig={s['sig']} ({s['start']}~{s['end']})")
    print(f"方向: {out['direction']}")
    print(f"大波动(IHE>=2%): {out['big_moves']}")
    print("年度:", [(d['y'], d['r']) for d in out['yearly']])


if __name__ == "__main__":
    main()