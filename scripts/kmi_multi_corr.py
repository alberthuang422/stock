# -*- coding: utf-8 -*-
"""KMI × US10Y / QQQ / SOXX / DJI 四基准分阶段相关性分析（81 号报告补充章节）。
口径（与 69 号 UNP / 51 号 MCD 系列一致）：
  - KMI 日收益率 pct_change×100（新浪未复权 close；无拆股，股息率低对该口径影响 <0.02%/日）
  - QQQ/SOXX 用 Yahoo 本地 adj_close 计算收益率（股息调整）；DJI 用 close（价格指数）
  - US10Y 用 DGS10 日变动 diff（bp）
  - 分阶段（按 KMI/中游行业重要节点）：
      全期(2021-08以来) / 加息周期(2021-08~2023-10) / 高利率平台期(2023-11~2025-07) /
      数据电力+LNG加速期(2025-08以来) / 2026 以来 / 近一年(2025-08以来)
  - 60 日滚动主口径；月度/年度；Fisher z 检验阶段间差异
  - 方向拆解（基准上行/下行日 KMI 表现 + 大波动日）
输出 results/kmi_multi_corr.json
"""
import os, json
from math import atanh, sqrt, erf
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

ANCHOR = pd.Timestamp("2021-08-25")        # 与 51/69 号一致
EVT_RATE_HIKE = pd.Timestamp("2023-10-31") # 加息周期顶点（美债 10Y 见顶 ~5%）
EVT_PLATFORM = pd.Timestamp("2025-07-31")  # 高利率平台期末（降息预期+AI电力发酵后）
EVT_ACCEL = pd.Timestamp("2025-08-01")     # 数据中心电力+LNG 出口加速期起点
YTD = pd.Timestamp("2026-01-01")

REFS = [
    ("US10Y", "美国10年期国债收益率 (DGS10)", "rate"),
    ("QQQ", "纳斯达克100 (QQQ)", "equity"),
    ("SOXX", "费城半导体 (SOXX)", "equity"),
    ("DJI", "道琼斯工业指数 (DJI)", "equity"),
]


def load_stock(ticker):
    df = pd.read_csv(os.path.join(DATA, ticker, f"{ticker}, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df[~df["date"].duplicated(keep="last")]
    # 有 adj_close 且与 close 有差异的用 adj_close（QQQ/SOXX Yahoo）；KMI 新浪未复权 adj==close
    price_col = "adj_close" if (("adj_close" in df.columns) and
                                (df["adj_close"].iloc[-100:].div(df["close"].iloc[-100:]).abs().sub(1).abs().max() > 1e-4)) else "close"
    df["ret"] = df[price_col].pct_change() * 100
    return df[["date", "close", "ret"]]


def load_ref(tag):
    if tag == "US10Y":
        df = pd.read_csv(os.path.join(DATA, "us_treasury", "DGS10.csv"))
        df = df.rename(columns={"observation_date": "date"})
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna().sort_values("date").reset_index(drop=True)
        df["ret"] = df["DGS10"].diff() * 100  # bp
        df["close"] = df["DGS10"]
        return df[["date", "close", "ret"]]
    df = pd.read_csv(os.path.join(DATA, tag.lower(), f"{tag}, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df[~df["date"].duplicated(keep="last")]
    price_col = "adj_close" if (("adj_close" in df.columns) and
                                (df["adj_close"].iloc[-100:].div(df["close"].iloc[-100:]).abs().sub(1).abs().max() > 1e-4)) else "close"
    df["ret"] = df[price_col].pct_change() * 100
    return df[["date", "close", "ret"]]


def pearson_pvalue(r, n):
    if n < 3 or r >= 1 or r <= -1:
        return 1.0
    t = r * sqrt((n - 2) / max(1e-9, (1 - r * r)))
    phi = 0.5 * (1 + erf(abs(t) / sqrt(2)))
    return float(2 * (1 - phi))


def sig_band(pv):
    return "sig" if pv < 0.01 else ("edge" if pv < 0.05 else "no")


def pearson_spearman(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, None, 0, 1.0
    p = float(np.corrcoef(a, b)[0, 1])
    s = float(pd.Series(a).rank().corr(pd.Series(b).rank()))
    return p, s, len(a), pearson_pvalue(p, len(a))


def fisher_z_test(r1, n1, r2, n2):
    if n1 < 6 or n2 < 6:
        return None
    z = (atanh(max(-0.999, min(0.999, r1))) - atanh(max(-0.999, min(0.999, r2)))) / sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return {"z": round(float(z), 3), "p_value": round(float(p), 4), "sig": bool(p < 0.05)}


def stats_block(merged, name, start=None, end=None):
    sub = merged
    if start is not None:
        sub = sub[sub["date"] >= start]
    if end is not None:
        sub = sub[sub["date"] < end]
    sub = sub.dropna(subset=["ret_sec", "ret_ref"])
    n = len(sub)
    if n < 5:
        return {"name": name, "n": 0}
    x, y = sub["ret_ref"].values, sub["ret_sec"].values
    p, s, n, pv = pearson_spearman(y, x)
    beta = float(np.cov(x, y)[0, 1] / np.var(x)) if np.var(x) > 0 else np.nan
    sec_ret = (sub["close_sec"].iloc[-1] / sub["close_sec"].iloc[0] - 1) * 100
    ref_ret = (sub["close_ref"].iloc[-1] / sub["close_ref"].iloc[0] - 1) * 100
    return {
        "name": name, "n": int(n),
        "start": str(sub["date"].iloc[0].date()), "end": str(sub["date"].iloc[-1].date()),
        "pearson": round(p, 3), "spearman": round(s, 3), "p_value": round(pv, 4), "sig": sig_band(pv),
        "beta": round(float(beta), 3), "r2": round(float(p * p), 3),
        "sec_ret_total": round(float(sec_ret), 2), "ref_ret_total": round(float(ref_ret), 2),
        "excess_ret": round(float(sec_ret - ref_ret), 2),
        "ann_vol_sec": round(float(sub["ret_sec"].std() * np.sqrt(252)), 1),
        "ann_vol_ref": round(float(sub["ret_ref"].std() * np.sqrt(252)), 1),
    }


def analyze_pair(sec, ref_tag, ref):
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_ref")).dropna().reset_index(drop=True)
    merged = merged[merged["date"] >= ANCHOR].reset_index(drop=True)

    blocks = [
        stats_block(merged, "全期（2021-08 以来）"),
        stats_block(merged, "加息周期 (2021-08~2023-10)", end=EVT_RATE_HIKE),
        stats_block(merged, "高利率平台期 (2023-11~2025-07)", start=EVT_RATE_HIKE, end=EVT_PLATFORM),
        stats_block(merged, "加速期 (2025-08 以来)", start=EVT_ACCEL),
        stats_block(merged, "2026 以来", start=YTD),
        stats_block(merged, "近一年 (2025-08 以来)", start=EVT_ACCEL),
    ]
    fishers = {}
    for a, b in [(1, 2), (2, 3), (1, 3)]:
        ba, bb = blocks[a], blocks[b]
        if ba["n"] > 5 and bb["n"] > 5:
            f = fisher_z_test(ba["pearson"], ba["n"], bb["pearson"], bb["n"])
            if f:
                fishers[f"{ba['name']} vs {bb['name']}"] = f

    roll60 = merged["ret_sec"].rolling(60).corr(merged["ret_ref"]) * 100
    roll_series = [{"date": str(d.date()), "corr": None if np.isnan(v) else round(float(v), 2)}
                   for d, v in zip(merged["date"], roll60)]

    mm = merged.set_index("date")
    monthly = (mm[["ret_sec", "ret_ref"]].groupby(pd.Grouper(freq="ME"))
               .corr().unstack()["ret_sec"]["ret_ref"] * 100).dropna()
    monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 2)} for k, v in monthly.items()]
    yearly = (mm[["ret_sec", "ret_ref"]].groupby(mm.index.year)[["ret_sec", "ret_ref"]]
              .corr().unstack()["ret_sec"]["ret_ref"] * 100).dropna()
    yearly_series = [{"year": int(k), "corr": round(float(v), 2)} for k, v in yearly.items()]

    k0, d0 = merged["close_sec"].iloc[0], merged["close_ref"].iloc[0]
    price_series = [{"date": str(d.date()),
                     "sec": round(float(k) / k0 * 100, 2), "ref": round(float(j) / d0 * 100, 2)}
                    for d, k, j in zip(merged["date"], merged["close_sec"], merged["close_ref"])]

    up, dn = merged[merged["ret_ref"] > 0], merged[merged["ret_ref"] < 0]
    direction = {
        "up": {"n": int(len(up)), "sec_med": round(float(up["ret_sec"].median()), 3),
               "win": round(float((up["ret_sec"] > 0).mean() * 100), 1)},
        "dn": {"n": int(len(dn)), "sec_med": round(float(dn["ret_sec"].median()), 3),
               "win": round(float((dn["ret_sec"] > 0).mean() * 100), 1)},
    }
    thr = 5 if ref_tag == "US10Y" else 2.0
    big = merged[merged["ret_ref"].abs() >= thr]
    direction["big_n"] = int(len(big))
    direction["big_sec_med"] = round(float(big["ret_sec"].median()), 3) if len(big) else None

    return {
        "ref_tag": ref_tag, "ref_label": dict((t, l) for t, l, _ in REFS)[ref_tag],
        "period": {"start": str(merged["date"].iloc[0].date()), "end": str(merged["date"].iloc[-1].date()),
                   "n": int(len(merged))},
        "blocks": blocks, "fishers": fishers,
        "rolling60": roll_series, "monthly": monthly_series, "yearly": yearly_series,
        "price": price_series, "direction": direction,
    }


def main():
    kmi = load_stock("KMI")
    out = {"meta": {
        "kmi": "Kinder Morgan 金德摩根 (KMI)",
        "split_events": {
            "2021-08": "锚点（与 51/69 号报告可比）",
            "2023-10-31": "加息周期顶点（美债10Y见顶~5%）",
            "2025-08-01": "数据中心电力 + LNG 出口加速期起点",
        },
        "us10y_note": "US10Y 相关 = KMI 日收益 × DGS10 日变动(bp)，非价格相关；负值=利率上行日 KMI 承压",
        "price_note": "KMI 用新浪未复权 close（无拆股，2011-02 起）；QQQ/SOXX 用 Yahoo 复权 adj_close；DJI 为价格指数。日收益率口径股息影响可忽略。",
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        "data_end": {"KMI": "2026-09-04", "DGS10": "2026-09-03", "QQQ": "2026-09-03", "SOXX": "2026-09-03", "DJI": "2026-09-03"},
    }, "pairs": []}
    for tag, label, kind in REFS:
        ref = load_ref(tag)
        out["pairs"].append(analyze_pair(kmi, tag, ref))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "kmi_multi_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, allow_nan=False)
    print("saved:", path)

    for pr in out["pairs"]:
        print(f"\n=== KMI × {pr['ref_label']} [{pr['period']['start']} ~ {pr['period']['end']}, n={pr['period']['n']}] ===")
        for b in pr["blocks"]:
            if b["n"] == 0:
                print(f"  {b['name']:<32} n=0")
                continue
            print(f"  {b['name']:<32} r={b['pearson']:<7} p={b['p_value']:<7} {b['sig']:<5} β={b['beta']:<7} KMI={b['sec_ret_total']:+8.1f}% 基准={b['ref_ret_total']:+8.1f}% 超额={b['excess_ret']:+8.1f}pp n={b['n']}")
        for k, f in pr["fishers"].items():
            print(f"    Fisher {k}: z={f['z']} p={f['p_value']} sig={f['sig']}")
        d = pr["direction"]
        print(f"    方向: 基准上行日(n={d['up']['n']}) KMI中位 {d['up']['sec_med']}% 胜率{d['up']['win']}% | 下行日(n={d['dn']['n']}) 中位 {d['dn']['sec_med']}% 胜率{d['dn']['win']}% | 大波动日(n={d['big_n']}) 中位 {d['big_sec_med']}%")


if __name__ == "__main__":
    main()