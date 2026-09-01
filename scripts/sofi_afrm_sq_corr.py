# -*- coding: utf-8 -*-
"""SOFI / AFRM / XYZ(Block,SQ) 相关性分析
窗口：特朗普选举胜利（2024-11-05）前 1 个月至今 = 2024-10-05 ~ 最新
主口径：60 日滚动相关 + 全期矩阵 + 分阶段
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "sofi_afrm_sq_corr.json")

START = "2024-10-05"   # 选举前 1 个月
ELEC = "2024-11-05"    # 特朗普选举胜利日
TICKERS = {"SOFI": "SoFi", "XYZ": "Block(SQ)", "AFRM": "Affirm"}


def load(tk):
    df = pd.read_csv(f"{DATA}/{tk.lower()}/{tk}, 1D.csv", parse_dates=["date"])
    df = df.set_index("date").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df["ret"] = df["close"].pct_change() * 100
    return df


def pearson_p(x, y):
    x = x.dropna()
    y = y.reindex(x.index)
    m = pd.concat([x, y], axis=1).dropna()
    if len(m) < 15:
        return None, None, 0
    r, p = stats.pearsonr(m.iloc[:, 0], m.iloc[:, 1])
    return float(r), float(p), int(len(m))


def sig_label(p):
    if p is None:
        return "no"
    if p < 0.01:
        return "sig"
    if p < 0.05:
        return "edge"
    return "no"


def roll_corr(pa, pb, window=60):
    return pa["ret"].rolling(window).corr(pb["ret"]).dropna()


def main():
    px = {tk: load(tk.lower()) for tk in TICKERS}
    # 窗口截取
    w = {tk: px[tk].loc[px[tk].index >= START] for tk in TICKERS}
    # 统一到共同交易日
    common = w["SOFI"].index
    for tk in list(TICKERS)[1:]:
        common = common.intersection(w[tk].index)
    w = {tk: w[tk].loc[common] for tk in TICKERS}

    res = {"meta": {"start": START, "elec": ELEC, "end": str(common[-1].date()),
                    "n_days": int(len(common)),
                    "asof": str(common[-1].date()),
                    "note": "SQ=Block(XYZ) 2023-06 起更名"}}

    # ---- 1. 全期相关矩阵 ----
    mat = {}
    for a in TICKERS:
        mat[a] = {}
        for b in TICKERS:
            if a == b:
                mat[a][b] = {"r": 1.0, "p": 0.0, "n": int(len(common))}
            else:
                r, p, n = pearson_p(w[a]["ret"], w[b]["ret"])
                mat[a][b] = {"r": r, "p": p, "n": n, "sig": sig_label(p)}
    res["full_matrix"] = mat

    # ---- 2. 分阶段 ----
    phases = {
        "选举前1月": (START, "2024-11-05"),
        "选举后1月": ("2024-11-06", "2024-12-05"),
        "2025全年": ("2025-01-01", "2025-12-31"),
        "2026至今": ("2026-01-01", None),
        "近3月": (None, None),
        "近1月": (None, None),
    }
    phase_res = {}
    for pname, (s, e) in phases.items():
        sub = common
        if s:
            sub = sub[sub >= pd.Timestamp(s)]
        if e:
            sub = sub[sub <= pd.Timestamp(e)]
        if pname == "近3月":
            sub = common[common >= common[-1] - pd.Timedelta(days=92)]
        if pname == "近1月":
            sub = common[common >= common[-1] - pd.Timedelta(days=31)]
        if len(sub) < 15:
            phase_res[pname] = {"days": int(len(sub)), "skip": True}
            continue
        m = {}
        for a in TICKERS:
            m[a] = {}
            for b in TICKERS:
                if a == b:
                    m[a][b] = {"r": 1.0}
                else:
                    r, p, n = pearson_p(w[a]["ret"].loc[sub], w[b]["ret"].loc[sub])
                    m[a][b] = {"r": r, "p": p, "n": n, "sig": sig_label(p)}
        phase_res[pname] = {"days": int(len(sub)), "start": str(sub[0].date()), "end": str(sub[-1].date()), "matrix": m}
    res["phases"] = phase_res

    # ---- 3. 60 日滚动相关 ----
    rc = {}
    pairs = [("SOFI", "XYZ"), ("SOFI", "AFRM"), ("AFRM", "XYZ")]
    for a, b in pairs:
        c = roll_corr(w[a], w[b], 60)
        rc[f"{a}_{b}"] = {
            "dates": [d.strftime("%Y-%m-%d") for d in c.index],
            "r": [round(float(v), 4) for v in c.values],
        }
    res["rolling60"] = rc
    # 滚动统计摘要
    pair_sum = {}
    for key, (a, b) in {"sofi_xyz": ("SOFI", "XYZ"), "sofi_afrm": ("SOFI", "AFRM"), "afrm_xyz": ("AFRM", "XYZ")}.items():
        vals = rc[f"{a}_{b}"]["r"]
        s = pd.Series(vals, index=pd.to_datetime(rc[f"{a}_{b}"]["dates"]))
        pair_sum[key] = {
            "min": round(float(s.min()), 3), "max": round(float(s.max()), 3),
            "mean": round(float(s.mean()), 3), "median": round(float(s.median()), 3),
            "last": round(float(s.iloc[-1]), 3),
            "last_date": str(s.index[-1].date()),
            "latest_window_end": str(common[-1].date()),
        }
    res["rolling_summary"] = pair_sum

    # ---- 4. 归一化净值 + 统计 ----
    nav = {tk: (w[tk]["close"] / w[tk]["close"].iloc[0] * 100) for tk in TICKERS}
    res["nav"] = {tk: {
        "dates": [d.strftime("%Y-%m-%d") for d in nav[tk].index],
        "nav": [round(float(v), 2) for v in nav[tk].values],
    } for tk in TICKERS}
    res["stats"] = {}
    for tk in TICKERS:
        r = w[tk]["ret"]
        res["stats"][tk] = {
            "cum_ret_pct": round(float((w[tk]["close"].iloc[-1] / w[tk]["close"].iloc[0] - 1) * 100), 2),
            "annual_vol_pct": round(float(r.std() * np.sqrt(252)), 2),
            "daily_mean_pct": round(float(r.mean()), 4),
            "max_drawdown_pct": round(float((w[tk]["close"] / w[tk]["close"].cummax() - 1).min() * 100), 2),
        }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    # ---- 打印摘要 ----
    print(f"=== 窗口: {START} ~ {common[-1].date()} ({len(common)} 交易日) ===")
    print("\n全期相关矩阵:")
    for a in TICKERS:
        row = "  ".join(f"{b}={mat[a][b]['r']:.3f}" + (f"({mat[a][b]['sig']})" if a != b else "") for b in TICKERS)
        print(f"  {a}: {row}")
    print("\n分阶段 (SOFI×XYZ / SOFI×AFRM / AFRM×XYZ):")
    for pname, pr in phase_res.items():
        if pr.get("skip"):
            print(f"  {pname}: 样本不足")
            continue
        m = pr["matrix"]
        r1 = m['SOFI']['XYZ']['r']
        r2 = m['SOFI']['AFRM']['r']
        r3 = m['AFRM']['XYZ']['r']
        f = lambda v: f"{v:.3f}" if v is not None else "n/a"
        print(f"  {pname} [{pr['start']}~{pr['end']}, n={pr['days']}]: "
              f"{f(r1)} / {f(r2)} / {f(r3)}")
    print("\n60日滚动摘要:")
    for k, v in pair_sum.items():
        print(f"  {k}: min={v['min']} max={v['max']} mean={v['mean']} last={v['last']} ({v['last_date']})")
    print("\n统计:")
    for tk, s in res["stats"].items():
        print(f"  {tk}: 累计 {s['cum_ret_pct']}%  年化波动 {s['annual_vol_pct']}%  MDD {s['max_drawdown_pct']}%")


if __name__ == "__main__":
    main()
