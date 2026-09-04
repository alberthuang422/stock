# -*- coding: utf-8 -*-
"""UNP × US10Y / QQQ / SOXX / DJI 四基准分阶段相关性分析。
口径（与 51 号 MCD/SBUX 系列一致，扩展 US10Y）：
  - 股票日收益率 pct_change×100；US10Y 用日变动 diff（bp）
  - 分阶段（按 UNP/铁路板块重要事件节点）：
      全期 / 合并公告前(<2025-07-28) / 合并公告~STB受理(2025-07-28~2026-05-28) /
      STB受理后(>=2026-05-28) / 2026 以来 / 2025-07 以来
  - Fisher z 检验阶段间相关差异；60 日滚动主口径；月度/年度
  - 极端日：|日收益|>=3%（US10Y 用 |Δ|>=5bp）
输出 results/unp_multi_corr.json
"""
import os, json
from math import atanh, sqrt, erf
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

ANCHOR = pd.Timestamp("2021-08-25")   # 与 51 号一致（原 DJI 交集起点；DJI 现为新浪 2004 起，仍保持可比）
EVT_ANNOUNCE = pd.Timestamp("2025-07-28")   # UP-NS 合并协议签署/公告
EVT_STB_ACCEPT = pd.Timestamp("2026-05-28") # STB 受理（完整申请）
YTD = pd.Timestamp("2026-01-01")

REFS = [
    ("US10Y", "美国10年期国债收益率 (DGS10)", "rate"),
    ("QQQ", "纳斯达克100 (QQQ)", "equity"),
    ("SOXX", "费城半导体 (SOXX)", "equity"),
    ("DJI", "道琼斯工业指数 (DJI)", "equity"),
]


def load_stock(ticker):
    df = pd.read_csv(os.path.join(DATA, "unp", f"{ticker}, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df[~df["date"].duplicated(keep="last")]
    df["ret"] = df["close"].pct_change() * 100
    return df


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
    df["ret"] = df["close"].pct_change() * 100
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
    z = (atanh(r1) - atanh(r2)) / sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
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
        "ref_vol_bp": (round(float(sub["ret_ref"].std()), 1) if sub["ret_ref"].abs().max() < 50 else None),
    }


def analyze_pair(sec, ref_tag, ref):
    merged = pd.merge(sec[["date", "close", "ret"]], ref[["date", "close", "ret"]],
                      on="date", suffixes=("_sec", "_ref")).dropna().reset_index(drop=True)
    merged = merged[merged["date"] >= ANCHOR].reset_index(drop=True)

    blocks = [
        stats_block(merged, "全期（2021-08 以来）"),
        stats_block(merged, "合并公告前 (<2025-07-28)", end=EVT_ANNOUNCE),
        stats_block(merged, "公告~STB受理 (2025-07-28~2026-05-28)", start=EVT_ANNOUNCE, end=EVT_STB_ACCEPT),
        stats_block(merged, "STB受理后 (>=2026-05-28)", start=EVT_STB_ACCEPT),
        stats_block(merged, "2026 以来", start=YTD),
        stats_block(merged, "2025-07 公告以来", start=EVT_ANNOUNCE),
    ]
    fishers = {}
    for a, b in [(1, 2), (2, 3), (1, 3)]:
        ba, bb = blocks[a], blocks[b]
        f = fisher_z_test(ba["pearson"], ba["n"], bb["pearson"], bb["n"]) if ba["n"] > 5 and bb["n"] > 5 else None
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

    # 方向拆解（仅对 US10Y 有意义；其他基准也算上行/下行日作参考）
    up, dn = merged[merged["ret_ref"] > 0], merged[merged["ret_ref"] < 0]
    direction = {
        "up": {"n": int(len(up)), "sec_med": round(float(up["ret_sec"].median()), 3),
               "win": round(float((up["ret_sec"] > 0).mean() * 100), 1)},
        "dn": {"n": int(len(dn)), "sec_med": round(float(dn["ret_sec"].median()), 3),
               "win": round(float((dn["ret_sec"] > 0).mean() * 100), 1)},
    }
    # 大波动日：基准 |Δ| 大的日子 UNP 表现
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
    unp = load_stock("UNP")
    out = {"meta": {
        "unp": "Union Pacific 联合太平洋 (UNP)",
        "split_events": {
            "announce": "2025-07-28 UP-NS 合并协议公告",
            "stb_accept": "2026-05-28 STB 受理完整申请",
        },
        "us10y_note": "US10Y 相关 = UNP 日收益 × DGS10 日变动(bp)，非价格相关",
        "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        "data_end": {"UNP": "2026-09-03", "DGS10": "2026-09-02", "QQQ": "2026-09-03", "SOXX": "2026-09-03", "DJI": "2026-09-03"},
    }, "pairs": []}
    for tag, label, kind in REFS:
        ref = load_ref(tag)
        out["pairs"].append(analyze_pair(unp, tag, ref))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "unp_multi_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, allow_nan=False)
    print("saved:", path)

    for pr in out["pairs"]:
        print(f"\n=== UNP × {pr['ref_label']} [{pr['period']['start']} ~ {pr['period']['end']}, n={pr['period']['n']}] ===")
        for b in pr["blocks"]:
            if b["n"] == 0:
                print(f"  {b['name']:<38} n=0")
                continue
            print(f"  {b['name']:<38} r={b['pearson']:<7} p={b['p_value']:<7} {b['sig']:<5} β={b['beta']:<7} UNP={b['sec_ret_total']:+8.1f}% 基准={b['ref_ret_total']:+8.1f}% 超额={b['excess_ret']:+8.1f}pp n={b['n']}")
        for k, f in pr["fishers"].items():
            print(f"    Fisher {k}: z={f['z']} p={f['p_value']} sig={f['sig']}")
        d = pr["direction"]
        print(f"    方向: 基准上行日(n={d['up']['n']}) UNP中位 {d['up']['sec_med']}% 胜率{d['up']['win']}% | 下行日(n={d['dn']['n']}) 中位 {d['dn']['sec_med']}% 胜率{d['dn']['win']}% | 大波动日(n={d['big_n']}) 中位 {d['big_sec_med']}%")


if __name__ == "__main__":
    main()
