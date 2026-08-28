# -*- coding: utf-8 -*-
"""
53号报告分析：SOFI / AFRM / UPST 财报交易日涨跌相关性
- 事件日 = 财报实际发布后的首个美股交易日（富途 dual-interface + AFRM FY22Q4 手工补入核实）
- 口径：日收益 pct_change(close)*100；事件窗口 T±5（交易日）
- 输出 analysis.json 供 build 脚本渲染
"""
import pandas as pd
import numpy as np
import json
from scipy import stats

DATA = r"C:/Users/Administrator/Desktop/stock/data"
OUT = r"C:/Users/Administrator/Desktop/stock/results/earn_corr_sofi_afrm_upst"
TICKERS = ["SOFI", "AFRM", "UPST"]

# 财报交易日清单（定稿，来源=富途 earnings_price_move+history 并集；AFRM 2022-08-26 由 SEC/BusinessWire 官方核实补入）
EARN = {
    "SOFI": ["2021-08-12","2021-11-10","2022-03-01","2022-05-10","2022-08-03","2022-11-01",
             "2023-01-30","2023-05-01","2023-07-31","2023-10-30","2024-01-29","2024-04-29",
             "2024-07-30","2024-10-29","2025-01-27","2025-04-29","2025-07-29","2025-10-28",
             "2026-01-30","2026-04-29","2026-07-29"],
    "AFRM": ["2021-02-11","2021-05-10","2021-09-09","2021-11-10","2022-02-10","2022-05-12",
             "2022-08-26","2022-11-08","2023-02-09","2023-05-10","2023-08-25","2023-11-09",
             "2024-02-09","2024-05-08","2024-08-29","2024-11-08","2025-02-07","2025-05-09",
             "2025-08-29","2025-11-07","2026-02-06","2026-05-08"],
    "UPST": ["2021-03-17","2021-05-11","2021-08-10","2021-11-09","2022-02-15","2022-05-09",
             "2022-08-09","2022-11-09","2023-02-15","2023-05-10","2023-08-09","2023-11-08",
             "2024-02-14","2024-05-08","2024-08-07","2024-11-08","2025-02-12","2025-05-07",
             "2025-08-06","2025-11-05","2026-02-11","2026-05-06","2026-08-05"],
}

def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)):
        return None
    return o

def pearson(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    if n < 3:
        return dict(r=None, p=None, n=n)
    r, p = stats.pearsonr(x[m], y[m])
    t = r * np.sqrt(n - 2) / np.sqrt(1 - r * r) if abs(r) < 1 else np.inf
    p_t = 2 * (1 - stats.t.cdf(abs(t), n - 2)) if np.isfinite(t) else 0.0
    sig = "sig" if p_t < 0.01 else ("edge" if p_t < 0.05 else "no")
    return dict(r=round(float(r), 4), p=round(float(p_t), 4), n=int(n), sig=sig)

def spearman(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    if n < 3:
        return dict(rho=None, n=n)
    rho, p = stats.spearmanr(x[m], y[m])
    return dict(rho=round(float(rho), 4), p=round(float(p), 4), n=int(n))

def ols_beta(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    if n < 3:
        return dict(beta=None, rsq=None, n=n)
    xc, yc = x[m], y[m]
    X = np.column_stack([np.ones(n), xc])
    b, res, *_ = np.linalg.lstsq(X, yc, rcond=None)
    yhat = X @ b
    ss_res = float(((yc - yhat) ** 2).sum())
    ss_tot = float(((yc - yc.mean()) ** 2).sum())
    rsq = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return dict(beta=round(float(b[1]), 4), rsq=round(float(rsq), 4), n=int(n))

def load():
    panels = {}
    for tk in TICKERS:
        df = pd.read_csv(f"{DATA}/{tk.lower()}/{tk}, 1D.csv", parse_dates=["date"])
        df = df[["date", "close", "adj_close"]].sort_values("date").reset_index(drop=True)
        df["ret"] = df["close"].pct_change() * 100.0
        panels[tk] = df.set_index("date")
    # 统一面板：共同交易区间（覆盖三家最晚上市 SOFI 2021-06-01）
    all_idx = None
    for tk in TICKERS:
        s = panels[tk]["ret"]
        all_idx = s.index if all_idx is None else all_idx.intersection(s.index)
    full = pd.DataFrame({tk: panels[tk]["ret"] for tk in TICKERS}, index=all_idx).dropna(how="any")
    full = full[full.index >= pd.Timestamp("2021-06-01")]  # SOFI 正式交易起
    return full, panels

def sig_band(n):
    return round(1.96 / np.sqrt(n - 2), 4)

def main():
    full, panels = load()
    idx = full.index

    events = []  # {tk, date}
    for tk, dates in EARN.items():
        for d in dates:
            ts = pd.Timestamp(str(d))
            if ts in idx:
                events.append({"tk": tk, "date": d})
            else:
                print(f"  [skip] {tk} {d} 不在共同面板")
    ev_df = pd.DataFrame(events).sort_values("date").reset_index(drop=True)
    print(f"事件数: {len(ev_df)} (SOFI {sum(ev_df.tk=='SOFI')}, AFRM {sum(ev_df.tk=='AFRM')}, UPST {sum(ev_df.tk=='UPST')})")
    print(f"面板区间: {idx.min().date()} ~ {idx.max().date()}, 交易日 {len(idx)}")

    ev_days = set(ev_df.date)
    all_days = set(d.strftime("%Y-%m-%d") for d in idx)
    non_ev = sorted(all_days - ev_days)

    pairs = [("SOFI", "AFRM"), ("SOFI", "UPST"), ("AFRM", "UPST")]
    out = {"meta": {"tickers": TICKERS, "n_events": len(ev_df), "start": str(idx.min().date()),
                    "end": str(idx.max().date()), "days": int(len(idx)),
                    "event_counts": {tk: int(sum(ev_df.tk == tk)) for tk in TICKERS},
                    "note": "事件日=财报发布后首个交易日；面板 2021-06-01 起（SOFI 上市）；AFRM 2026-08-27 盘后财报因共同面板缺 08-28 数据未纳入；AFRM FY22Q4=(2022-08-25盘后发布→08-26交易日) 官方核实补入"}}

    # ============ 1. 全期基线相关 ============
    out["baseline"] = {}
    out["baseline"]["full_period"] = {}
    for a, b in pairs:
        x, y = full[a].values, full[b].values
        pr = pearson(x, y); sp = spearman(x, y); be = ols_beta(x, y)
        out["baseline"]["full_period"][f"{a}~{b}"] = {**pr, **sp, **be, "sig_band": sig_band(len(x))}

    # ============ 1.5 事件样本（按日期去重） ============
    ev_df["d"] = pd.to_datetime(ev_df["date"])
    # 唯一事件日（同一天多票发报 = 单观测日）
    uni = ev_df.groupby("d").tk.apply(list).reset_index()
    uni.columns = ["d", "tickers"]
    uni = uni.sort_values("d").reset_index(drop=True)
    ev_days_u = uni["d"]
    n_evday = int(len(uni))
    ev_sub = full.loc[ev_days_u.values]  # 每日一行
    nev_sub = full.loc[non_ev]
    out["meta"]["n_event_days"] = n_evday
    # 补充：事件日当天发作票数分布
    out["meta"]["event_day_counts"] = {int(k): int(v) for k, v in uni["tickers"].apply(len).value_counts().sort_index().items()}
    print(f"唯一事件日: {n_evday}, 双发日: {int(sum(uni['tickers'].apply(len) == 2))}")

    # ============ 2. 事件日 vs 非事件日相关 ============
    out["event_vs_non"] = {}
    for a, b in pairs:
        xe, ye = ev_sub[a].values, ev_sub[b].values
        xn, yn = nev_sub[a].values, nev_sub[b].values
        re_ = pearson(xe, ye); rn_ = pearson(xn, yn)
        # Fisher z 两样本相关差异检验（独立近似）
        def fisher_z(r):
            return 0.5 * np.log((1 + r) / (1 - r))
        def z_test(r1, r2, n1, n2):
            if r1 is None or r2 is None: return None
            se = np.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
            z = (fisher_z(r1) - fisher_z(r2)) / se
            p = 2 * (1 - stats.norm.cdf(abs(z)))
            return dict(z=round(float(z), 3), p=round(float(p), 4))
        zt = z_test(re_["r"], rn_["r"], re_["n"], rn_["n"])
        out["event_vs_non"][f"{a}~{b}"] = {
            "event_day": {**re_, **spearman(xe, ye), **ols_beta(xe, ye)},
            "non_event_day": {**rn_, **spearman(xn, yn), **ols_beta(xn, yn)},
            "diff_test": zt}
    # 事件日 vs 非事件日的绝对波动对比（异动放大）
    out["event_vs_non"]["abs_ret"] = {}
    for tk in TICKERS:
        e_abs = ev_sub[tk].abs()
        n_abs = nev_sub[tk].abs()
        out["event_vs_non"]["abs_ret"][tk] = {
            "event_mean": round(float(e_abs.mean()), 3),
            "event_med": round(float(np.median(e_abs.values)), 3),
            "non_mean": round(float(n_abs.mean()), 3),
            "non_med": round(float(np.median(n_abs.values)), 3),
            "amp": round(float(e_abs.mean() / n_abs.mean()), 3)}

    # ============ 3. 按发财报票分组的事件日联动 ============
    by_grp = {}
    for gtk in TICKERS:
        sub = ev_df[ev_df.tk == gtk]
        # 按事件日取行（去重；若同日双发，行所属组以该日为准，但对其它票联动仍有效）
        days = pd.DatetimeIndex(sorted(set(pd.Timestamp(str(d)) for d in sub.date)))
        rows = full.loc[days]
        g = {"n": int(len(sub)), "n_days": int(len(days)), "events": sub.date.tolist()}
        # 发财报票的平均/中位当日涨跌
        g["earner_ret"] = {"mean": round(float(rows[gtk].mean()), 3),
                           "med": round(float(np.median(rows[gtk].values)), 3),
                           "win": round(float((rows[gtk] > 0).mean()), 4),
                           "abs_mean": round(float(rows[gtk].abs().mean()), 3)}
        # 其余两票联动（同向率、平均收益、跟随幅度）
        others = [t for t in TICKERS if t != gtk]
        g["others"] = {}
        for ot in others:
            x, y = rows[gtk].values, rows[ot].values
            same = float(((x > 0) & (y > 0) | (x < 0) & (y < 0)).mean())
            g["others"][ot] = {
                "corr_with_earner": pearson(x, y),
                "beta_on_earner": ols_beta(x, y),
                "same_dir_pct": round(same, 4),
                "mean_ret": round(float(y.mean()), 3),
                "med_ret": round(float(np.median(y)), 3),
                "abs_mean": round(float(np.abs(y).mean()), 3)}
        # 该组对外配对相关（两票口径）
        g["pair_corr"] = {}
        for pa, pb in pairs:
            if gtk in (pa, pb):
                g["pair_corr"][f"{pa}~{pb}"] = pearson(rows[pa].values, rows[pb].values)
        by_grp[gtk] = g
    out["by_earner"] = by_grp

    # ============ 4. 事件窗口 T-5 ~ T+5 相关曲线 ============
    # pooled 对齐：对每个 offset，取各事件那天三票收益集合 → 相关
    win = {}
    for off in range(-5, 6):
        cols = {tk: [] for tk in TICKERS}
        for _, ev in ev_df.iterrows():
            ts = pd.Timestamp(str(ev.date))
            pos = idx.get_loc(ts) + off
            if 0 <= pos < len(idx):
                d = idx[pos]
                for tk in TICKERS:
                    if d in panels[tk].index:
                        cols[tk].append(float(panels[tk].loc[d, "ret"]))
        win[off] = {}
        for a, b in pairs:
            n = min(len(cols[a]), len(cols[b]))
            x = np.array(cols[a][:n]); y = np.array(cols[b][:n])
            win[off][f"{a}~{b}"] = pearson(x, y)
    out["window"] = win

    # 事件日 vs 自身非事件日平均相关基线（对照组：随机日+/-同窗口）
    out["window_base"] = {}
    rng = np.random.default_rng(42)
    base_off_mean = {}
    for off in range(-5, 6):
        series = {a: {} for a in TICKERS}
        # 在非事件日随机抽样与事件数相同数量的"伪事件日"，求窗口相关，重复3次取平均
        acc = {f"{a}~{b}": [] for a, b in pairs}
        for rep in range(3):
            samp = rng.choice(non_ev, size=len(ev_df), replace=False)
            cols = {tk: [] for tk in TICKERS}
            for d in samp:
                ts = pd.Timestamp(str(d))
                pos = idx.get_loc(ts) + off
                if 0 <= pos < len(idx):
                    dd = idx[pos]
                    for tk in TICKERS:
                        if dd in panels[tk].index:
                            cols[tk].append(float(panels[tk].loc[dd, "ret"]))
            for a, b in pairs:
                n = min(len(cols[a]), len(cols[b]))
                if n > 2:
                    acc[f"{a}~{b}"].append(pearson(np.array(cols[a][:n]), np.array(cols[b][:n]))["r"])
        base_off_mean[f"{off}"] = {k: round(float(np.nanmean(v)), 4) if v else None for k, v in acc.items()}
    out["window_base"] = base_off_mean

    # ============ 5. 分阶段（年度 + 是否 2024 起） ============
    out["by_year"] = {}
    for y in sorted(set(d[:4] for d in ev_df.date)):
        sub = ev_df[ev_df.date.str.startswith(y)]
        if len(sub) == 0: continue
        days = pd.DatetimeIndex(sorted(set(pd.Timestamp(str(d)) for d in sub.date)))
        rows = full.loc[days]
        by = {"n": int(len(sub)), "n_days": int(len(days)), "event_dates": sub.date.tolist(),
              "mean_ret": {tk: round(float(rows[tk].mean()), 3) for tk in TICKERS},
              "abs_mean": {tk: round(float(rows[tk].abs().mean()), 3) for tk in TICKERS}}
        by["pair_corr"] = {}
        for a, b in pairs:
            by["pair_corr"][f"{a}~{b}"] = pearson(rows[a].values, rows[b].values)
        out["by_year"][y] = by

    # 阶段对比 2021-2023 vs 2024-2026
    for phase, mask in [("p1_2021_2023", ev_df.date < "2024-01-01"), ("p2_2024_2026", ev_df.date >= "2024-01-01")]:
        sub = ev_df[mask]
        if len(sub) == 0: continue
        days = pd.DatetimeIndex(sorted(set(pd.Timestamp(str(d)) for d in sub.date)))
        rows = full.loc[days]
        ph = {"n": int(len(sub)), "n_days": int(len(days))}
        ph["pair_corr"] = {}
        for a, b in pairs:
            ph["pair_corr"][f"{a}~{b}"] = pearson(rows[a].values, rows[b].values)
        ph["abs_mean"] = {tk: round(float(rows[tk].abs().mean()), 3) for tk in TICKERS}
        out["by_year"][phase] = ph

    # ============ 6. 双发日 & 特殊个案 ============
    dup_dates = ev_df.groupby("date").tk.apply(list)
    out["dual_events"] = {str(d): v for d, v in dup_dates.items() if len(v) >= 2}
    if out["dual_events"]:
        for d, tks in out["dual_events"].items():
            if pd.Timestamp(d) in ev_sub.index:
                r = ev_sub.loc[pd.Timestamp(d)]
                out["dual_events"][str(d)] = {"tickers": tks, "rets": {tk: round(float(r[tk]), 3) for tk in TICKERS}}
    # 事件日三票全同向/反向的统计
    rows = ev_sub
    sign = np.sign(rows.values)
    all_same = float((np.all(sign == sign[:, 0:1], axis=1)).mean())
    out["same_dir_all"] = {"pct_all_3_same": round(all_same, 4)}

    with open(f"{OUT}/analysis.json", "w", encoding="utf-8") as f:
        json.dump(clean(out), f, ensure_ascii=False, indent=1)
    print(f"written: {OUT}/analysis.json")

if __name__ == "__main__":
    main()