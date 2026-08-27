#!/usr/bin/env python3
"""ABBV vs IBB(生物科技) vs IHE(传统制药) 相关性分析。

数据:
  - ABBV / IBB / XBI / XPH: data/<ticker>/<TICKER>, 1D.csv (Yahoo Finance, adj_close 复权)
  - IHE: data/ihe/IHE, 1D.csv (腾讯自选股前复权日线, 2021-08 起)

计算:
  - 三对 Pearson / Spearman 相关系数: 全期 + 分块(近3年/近1年/2026以来) + 分年度
  - 滚动 60 日 / 252 日相关性序列 (ABBV-IBB vs ABBV-IHE)
  - 月度平均相关性
  - ABBV 对 IBB / IHE 的 beta 与 R2
  - Steiger(1980) 检验: ABBV-IBB 与 ABBV-IHE 相关系数差异显著性(两依赖相关共享 ABBV)
  - 补充: ABBV vs IBB/XBI/XPH 长窗口(2015+)相关性
输出 JSON 到 results/ 供 HTML 报告使用。
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

def load(ticker: str) -> pd.DataFrame:
    p = os.path.join(DATA, ticker.lower(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    px = df["adj_close"] if "adj_close" in df.columns else df["close"]
    df["ret"] = px.pct_change() * 100
    return df

def corr_metrics(a: np.ndarray, b: np.ndarray):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, None, len(a)
    from scipy.stats import spearmanr
    p = float(np.corrcoef(a, b)[0, 1])
    s = float(spearmanr(a, b).statistic)
    return p, s, len(a)

def beta_r2(x: np.ndarray, y: np.ndarray):
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 3:
        return None, None
    beta = float(np.cov(y, x)[0, 1] / np.var(x))
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    return beta, r2

def steiger(r12, r13, r23, n):
    """Steiger(1980) 检验: H0: rho_12 == rho_13 (两相关系数共享同一变量)。
    返回 t 统计量与双尾 p 值。
    """
    from math import sqrt
    det = 1 - r12**2 - r13**2 - r23**2 + 2*r12*r13*r23
    rbar = (r12 + r13) / 2
    denom = sqrt(2 * ((n - 1) / (n - 3)) * det + rbar**2 * (1 - r23)**3)
    t = (r12 - r13) * sqrt((n - 1) * (1 + r23)) / denom
    # t 分布 df=n-3 双尾 p
    from scipy.stats import t as tdist
    p = 2 * (1 - tdist.cdf(abs(t), df=n - 3))
    return float(t), float(p)

def pair_stats(df_abbv, df_ib, df_ihe, xname, yname):
    """ABBV 对 X 与 ABBV 对 Y 及 X-Y 三对相关性块。
    全部指标在 ax/ay/xy 三者的公共日期区间上计算，保证窗口一致。
    """
    ax = pd.merge(df_abbv[["date", "ret"]], df_ib[["date", "ret"]], on="date", suffixes=("_a", "_x")).dropna()
    ay = pd.merge(df_abbv[["date", "ret"]], df_ihe[["date", "ret"]], on="date", suffixes=("_a", "_y")).dropna()
    xy = pd.merge(df_ib[["date", "ret"]], df_ihe[["date", "ret"]], on="date", suffixes=("_x", "_y")).dropna()
    common = set(ax["date"]) & set(ay["date"]) & set(xy["date"])
    ax = ax[ax["date"].isin(common)].sort_values("date").reset_index(drop=True)
    ay = ay[ay["date"].isin(common)].sort_values("date").reset_index(drop=True)
    xy = xy[xy["date"].isin(common)].sort_values("date").reset_index(drop=True)
    n = len(common)
    if n < 10:
        return None
    p_ax, s_ax, _ = corr_metrics(ax["ret_a"].values, ax["ret_x"].values)
    p_ay, s_ay, _ = corr_metrics(ay["ret_a"].values, ay["ret_y"].values)
    p_xy, s_xy, _ = corr_metrics(xy["ret_x"].values, xy["ret_y"].values)
    b_ax, r2_ax = beta_r2(ax["ret_x"].values, ax["ret_a"].values)
    b_ay, r2_ay = beta_r2(ay["ret_y"].values, ay["ret_a"].values)
    # 端点收益 (公共区间内)
    def seg_ret(df, col, d0, d1):
        sub = df[(df["date"] >= d0) & (df["date"] <= d1)]
        return (sub[col].iloc[-1] / sub[col].iloc[0] - 1) * 100
    d0, d1 = ax["date"].iloc[0], ax["date"].iloc[-1]
    ret_abbv = round(float(seg_ret(df_abbv, "adj_close", d0, d1)), 2)
    ret_x = round(float(seg_ret(df_ib, "adj_close", d0, d1)), 2)
    ret_y = round(float(seg_ret(df_ihe, "adj_close", d0, d1)), 2)
    t, p = steiger(p_ax, p_ay, p_xy, n)
    return {
        "label": f"ABBV-{xname} vs ABBV-{yname}",
        "n": n,
        "start": str(d0.date()),
        "end": str(d1.date()),
        "abbv_x_pearson": round(p_ax, 4), "abbv_x_spearman": round(s_ax, 4),
        "abbv_y_pearson": round(p_ay, 4), "abbv_y_spearman": round(s_ay, 4),
        "x_y_pearson": round(p_xy, 4),
        "abbv_x_beta": round(b_ax, 3) if b_ax is not None else None,
        "abbv_y_beta": round(b_ay, 3) if b_ay is not None else None,
        "abbv_x_r2": round(r2_ax, 4) if r2_ax is not None else None,
        "abbv_y_r2": round(r2_ay, 4) if r2_ay is not None else None,
        "corr_diff": round(p_ax - p_ay, 4),
        "steiger_t": round(t, 3), "steiger_p": round(p, 4),
        "ret_abbv": ret_abbv, "ret_x": ret_x, "ret_y": ret_y,
    }

def pair_full(df_abbv, df_x, xname):
    """补充长窗口: ABBV 对单指数 X 的全重叠窗口相关性 (不含 IHE, 2015+ 生效)。"""
    ax = pd.merge(df_abbv[["date", "ret"]], df_x[["date", "ret"]], on="date", suffixes=("_a", "_x")).dropna()
    if len(ax) < 60:
        return None
    p, s, n = corr_metrics(ax["ret_a"].values, ax["ret_x"].values)
    b, r2 = beta_r2(ax["ret_x"].values, ax["ret_a"].values)
    def seg_ret(df, col, d0, d1):
        sub = df[(df["date"] >= d0) & (df["date"] <= d1)]
        return (sub[col].iloc[-1] / sub[col].iloc[0] - 1) * 100
    d0, d1 = ax["date"].iloc[0], ax["date"].iloc[-1]
    return {
        "pair": f"ABBV-{xname}", "n": int(n), "start": str(d0.date()), "end": str(d1.date()),
        "pearson": round(p, 4), "spearman": round(s, 4),
        "beta": round(b, 3) if b is not None else None,
        "r2": round(r2, 4) if r2 is not None else None,
        "ret_abbv": round(float(seg_ret(df_abbv, "adj_close", d0, d1)), 2),
        "ret_x": round(float(seg_ret(df_x, "adj_close", d0, d1)), 2),
    }

def rolling_corr(m1, m2, win):
    return m1.rolling(win).corr(m2) * 100

def main():
    abbv = load("ABBV")
    ibb = load("IBB")
    ihe = load("IHE")
    xbi = load("XBI")
    xph = load("XPH")

    # 主窗口: 三个标的最早公共日期 (IHE 2021-08 起)
    m = pd.merge(abbv[["date", "close"]], ibb[["date", "close"]], on="date", suffixes=("_a", "_i"))
    m = pd.merge(m, ihe[["date", "close"]], on="date")
    m = m.dropna()
    win_start = m["date"].min()
    print("主窗口:", win_start.date(), "~", m["date"].max().date(), "n=", len(m))

    def sub(df, start=None, end=None, end_exclusive=False):
        d = df
        if start is not None: d = d[d["date"] >= start]
        if end is not None:
            d = d[d["date"] < end] if end_exclusive else d[d["date"] <= end]
        return d

    SPLIT = pd.Timestamp("2026-02-01")  # 项目惯例分界点: 分界前 < SPLIT, 分界后 >= SPLIT
    blocks = []
    for label, start, end, exc in [
        (f"全期 ({win_start.date()} 起)", None, None, False),
        ("分界前 (2026-02-01)", None, SPLIT, True),
        ("分界后 (2026-02-01)", SPLIT, None, False),
        ("近 3 年", pd.Timestamp("2023-08-01"), None, False),
        ("近 1 年", pd.Timestamp("2025-08-01"), None, False),
        ("2026 年以来", pd.Timestamp("2026-01-01"), None, False),
    ]:
        b = pair_stats(sub(abbv, start, end, exc), sub(ibb, start, end, exc), sub(ihe, start, end, exc), "IBB", "IHE")
        if b: b["block"] = label
        blocks.append(b)

    # Fisher z 检验: 分界前 vs 分界后, ABBV-IBB 与 ABBV-IHE 各自的两阶段差异
    from math import atanh, sqrt, erf
    def fisher_z(r): return atanh(r)
    def phase_fisher(pre_b, post_b, key):
        r1, n1 = pre_b[key], pre_b["n"]
        r2, n2 = post_b[key], post_b["n"]
        z = (fisher_z(r1) - fisher_z(r2)) / sqrt(1/(n1-3) + 1/(n2-3))
        p = 2 * (1 - 0.5 * (1 + erf(abs(z)/sqrt(2))))
        return {"z": round(float(z), 3), "p_value": round(float(p), 4), "sig": bool(p < 0.05)}
    pre_b = next(b for b in blocks if b and b["block"].startswith("分界前"))
    post_b = next(b for b in blocks if b and b["block"].startswith("分界后"))
    fisher = {
        "split": str(SPLIT.date()),
        "abbv_ibb": phase_fisher(pre_b, post_b, "abbv_x_pearson"),
        "abbv_ihe": phase_fisher(pre_b, post_b, "abbv_y_pearson"),
    }

    # 分年度 (2022 起有完整年)
    yearly = []
    for y in range(2022, 2027):
        s = pd.Timestamp(f"{y}-01-01"); e = pd.Timestamp(f"{y}-12-31") if y < 2026 else None
        b = pair_stats(sub(abbv, s, e), sub(ibb, s, e), sub(ihe, s, e), "IBB", "IHE")
        if b: b["block"] = f"{y}年"
        yearly.append(b)

    # 滚动相关性 (主窗口)
    merged = pd.merge(abbv[["date", "ret"]], ibb[["date", "ret"]], on="date", suffixes=("_a", "_i"))
    merged = pd.merge(merged, ihe[["date", "ret"]].rename(columns={"ret": "ret_y"}), on="date").dropna().reset_index(drop=True)
    roll60 = rolling_corr(merged["ret_a"], merged["ret_i"], 60)
    roll60b = rolling_corr(merged["ret_a"], merged["ret_y"], 60)
    roll252 = rolling_corr(merged["ret_a"], merged["ret_i"], 252)
    roll252b = rolling_corr(merged["ret_a"], merged["ret_y"], 252)
    def series(r, rb):
        out = []
        for d, v, v2 in zip(merged["date"], r, rb):
            if np.isnan(v) or np.isnan(v2): continue
            out.append({"date": str(d.date()), "abbv_ibb": round(float(v), 2), "abbv_ihe": round(float(v2), 2)})
        return out
    roll60_s = series(roll60, roll60b)
    roll252_s = series(roll252, roll252b)

    # 月度相关性 (仅保留重叠样本 >=10 日的月份, 剔除退化值)
    mm = merged.set_index("date")
    mon = mm[["ret_a", "ret_i", "ret_y"]].groupby(pd.Grouper(freq="ME")).corr().unstack()
    mon_cnt = mm[["ret_a", "ret_i", "ret_y"]].groupby(pd.Grouper(freq="ME")).size()
    monthly = []
    for k, v in mon.iterrows():
        if mon_cnt.get(k, 0) < 10: continue
        ri = v["ret_a"]["ret_i"] * 100
        ry = v["ret_a"]["ret_y"] * 100
        if np.isnan(ri) or np.isnan(ry): continue
        if abs(ri) > 99 or abs(ry) > 99: continue
        monthly.append({"month": str(k.date())[:7], "abbv_ibb": round(float(ri), 2), "abbv_ihe": round(float(ry), 2)})

    # 补充长窗口: ABBV vs IBB/XBI/XPH (2015+, 不含 IHE)
    sup_blocks = [pair_full(abbv, load(tk), tk) for tk in ["IBB", "XBI", "XPH"]]
    sup_blocks = [b for b in sup_blocks if b]
    sup_yearly = []
    for tk in ["IBB", "XBI", "XPH"]:
        df2 = load(tk)
        for y in range(2016, 2027):
            s = pd.Timestamp(f"{y}-01-01"); e = pd.Timestamp(f"{y}-12-31") if y < 2026 else None
            b = pair_full(sub(abbv, s, e), sub(df2, s, e), tk)
            if b and b["n"] >= 60:
                sup_yearly.append({"year": y, "pair": f"ABBV-{tk}", "pearson": b["pearson"],
                                  "spearman": b["spearman"], "beta": b["beta"]})

    out = {
        "window": {"start": str(merged["date"].iloc[0].date()), "end": str(merged["date"].iloc[-1].date()),
                   "n": int(len(merged))},
        "split": str(SPLIT.date()),
        "fisher": fisher,
        "blocks": [b for b in blocks if b],
        "yearly": [y for y in yearly if y],
        "rolling60": roll60_s,
        "rolling252": roll252_s,
        "monthly": monthly,
        "supplement": sup_blocks,
        "supplement_yearly": sup_yearly,
        "meta": {
            "abbv": "AbbVie 艾伯维 (大型生物制药, 免疫/肿瘤/神经科学/美学)",
            "ibb": "iShares Biotechnology ETF (ICE 生物科技指数, 247 只, 生物科技占 87%)",
            "ihe": "iShares U.S. Pharmaceuticals ETF (道琼斯美国精选制药指数, 60 只, JNJ+LLY 约 44%)",
            "sources": {
                "abbv": "Yahoo Finance 日线(adj_close 复权)",
                "ibb": "Yahoo Finance 日线(adj_close 复权)",
                "ihe": "腾讯自选股前复权日线(2021-08 起)",
                "xbi": "Yahoo Finance 日线(adj_close 复权)",
                "xph": "Yahoo Finance 日线(adj_close 复权)",
            },
            "holdings_note": "IHE 2026-08-20 持仓前 25 名无 ABBV; IBB 前 20 名无 ABBV —— 两指数当前均不含 ABBV, 相关性无机械重叠成分",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        }
    }
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "abbv_ibb_ihe_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", path)
    print("\n== 分块 ==")
    for b in out["blocks"]:
        print(b["block"], f"n={b['n']}", f"ABBV-IBB r={b['abbv_x_pearson']}", f"ABBV-IHE r={b['abbv_y_pearson']}",
              f"diff={b['corr_diff']}", f"Steiger p={b['steiger_p']}", f"beta_IBB={b['abbv_x_beta']} beta_IHE={b['abbv_y_beta']}")
    print("\n== 补充(2015+ 长窗口) ==")
    for b in out["supplement"]:
        print(b["pair"], f"r={b['pearson']}", f"beta={b['beta']}")

if __name__ == "__main__":
    main()
