# -*- coding: utf-8 -*-
"""
KMI (Kinder Morgan) × 天然气(NG=F) × 原油(CL=F) 相关性分析
口径：60 日滚动主口径；分阶段(结构性区段)；R 与 β 同列；sig/edge/no 三档 + p 值
对照：WMB(纯天然气中游同业)、XLE(能源板块)、SPY(大盘)
本地数据：data/{kmi,ng,cl,ung,wmb,xle,spy}/... 1D.csv（fetch: scripts/kmi_ng_cl_fetch.cjs）
输出：results/kmi_ng_cl_corr.json
"""
import json
import os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT_JSON = os.path.join(BASE, "results", "kmi_ng_cl_corr.json")

TICKERS = ["KMI", "NG=F", "CL=F", "UNG", "WMB", "XLE", "SPY"]
# 价格口径：期货用 close（前月连续合约，Yahoo adj 不可靠）；股票用 adj_close（含股息调整）
FUTURES = {"NG=F", "CL=F"}

def load_price(tk):
    m = {"KMI": ("kmi", "KMI, 1D.csv"), "NG=F": ("ng", "NG=F, 1D.csv"),
         "CL=F": ("cl", "CL, 1D.csv"), "UNG": ("ung", "UNG, 1D.csv"),
         "WMB": ("wmb", "WMB, 1D.csv"), "XLE": ("xle", "xle, 1D.csv"),
         "SPY": ("spy", "SPY, 1D.csv")}
    d, f = m[tk]
    df = pd.read_csv(os.path.join(DATA, d, f))
    df.columns = [c.strip() for c in df.columns]
    col = "close" if tk in FUTURES else "adj_close"
    if col not in df.columns:
        col = "close"
    df = df[["date", col]].rename(columns={col: tk})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[tk] = pd.to_numeric(df[tk], errors="coerce")
    return df.dropna(subset=["date", tk]).sort_values("date").reset_index(drop=True)


def sigflag(p):
    return "sig" if p < 0.01 else ("edge" if p < 0.05 else "no")


def pearson(x, y):
    m = x.notna() & y.notna()
    if m.sum() < 5:
        return None, None, None, int(m.sum())
    r, p = stats.pearsonr(x[m], y[m])
    return float(r), float(p), sigflag(p), int(m.sum())


def ols_beta(x, y):
    m = x.notna() & y.notna()
    if m.sum() < 5 or x[m].std() == 0:
        return None, None, int(m.sum())
    b = np.cov(x[m], y[m])[0, 1] / x[m].var()
    return float(b), None, int(m.sum())


PHASES = [
    ("P1 2011Q2–2014H1 页岩繁荣·高油价", "2011-02-14", "2014-06-30"),
    ("P2 2014H2–2016Q1 油价崩盘·股息削减", "2014-07-01", "2016-02-29"),
    ("P3 2016Q2–2019 低油价修复期", "2016-03-01", "2019-12-31"),
    ("P4 2020 COVID·负油价", "2020-01-02", "2020-12-31"),
    ("P5 2021–2022 能源大周期·气价飙升", "2021-01-01", "2022-12-30"),
    ("P6 2023–2024 高利率·AI 需求萌芽", "2023-01-03", "2024-12-31"),
    ("P7 2025–2026-09 天然气重估·当前", "2025-01-02", "2026-09-04"),
]
FULL = ("全期 2011-02–2026-09", "2011-02-14", "2026-09-04")

PAIRS = [("KMI", "NG=F"), ("KMI", "CL=F"), ("KMI", "XLE"), ("KMI", "SPY"),
         ("WMB", "NG=F"), ("WMB", "CL=F"), ("XLE", "CL=F"), ("XLE", "NG=F")]

# 事件窗口（关键检验）
EVENTS = {
    "ev_crash": {"label": "2014-06 油价见顶 → 2016-02 崩盘底", "a": "2014-06-20", "b": "2016-02-11"},
    "ev_covid_crash": {"label": "2020-02-19→03-23 COVID 恐慌下跌", "a": "2020-02-19", "b": "2020-03-23"},
    "ev_covid": {"label": "2020-04 负油价冲击月", "a": "2020-04-06", "b": "2020-04-30"},
    "ev_gas22up": {"label": "2022 气价狂飙段", "a": "2022-01-03", "b": "2022-08-22"},
    "ev_gas22dn": {"label": "2022 气价崩落段", "a": "2022-08-22", "b": "2023-02-28"},
    "ev_oil26": {"label": "2026-08-28→09-04 油价急拉(+9.7%)", "a": "2026-08-28", "b": "2026-09-04"},
}

def main():
    panel = None
    for tk in TICKERS:
        df = load_price(tk)
        panel = df if panel is None else panel.merge(df, on="date", how="outer")
    panel = panel.sort_values("date").reset_index(drop=True)
    # 分析窗口：KMI 上市后
    w0 = panel["date"] >= pd.Timestamp("2011-02-01")
    panel = panel[w0].reset_index(drop=True)
    p_cols = TICKERS
    ret = panel[p_cols].pct_change() * 100  # 百分数日收益

    # ---- 分段相关性表（R / p / 显著性 / β / N）----
    seg_rows = []
    for label, a, b in [FULL] + PHASES:
        lo = (panel["date"] >= pd.Timestamp(a)) & (panel["date"] <= pd.Timestamp(b))
        x_ng, x_cl, x_xle, x_spy = ret["NG=F"][lo], ret["CL=F"][lo], ret["XLE"][lo], ret["SPY"][lo]
        y = ret["KMI"][lo]
        row = {"label": label}
        for tag, x in [("ng", x_ng), ("cl", x_cl), ("xle", x_xle), ("spy", x_spy)]:
            r, p, fl, n = pearson(x, y)
            b, _, _ = ols_beta(x, y)
            row[f"r_{tag}"] = None if r is None else round(r, 3)
            row[f"p_{tag}"] = None if p is None else round(p, 4)
            row[f"fl_{tag}"] = fl
            row[f"b_{tag}"] = None if b is None else round(b, 4)
            row[f"n_{tag}"] = n
        # 对照：WMB 同段 × NG/CL
        yw = ret["WMB"][lo]
        rw_ng, pw_ng, _, _ = pearson(x_ng, yw)
        rw_cl, pw_cl, _, _ = pearson(x_cl, yw)
        row["r_wmb_ng"] = None if rw_ng is None else round(rw_ng, 3)
        row["r_wmb_cl"] = None if rw_cl is None else round(rw_cl, 3)
        row["fl_wmb_ng"] = sigflag(pw_ng) if pw_ng is not None else None
        row["fl_wmb_cl"] = sigflag(pw_cl) if pw_cl is not None else None
        # 对照：XLE×CL（能源股 vs 油价已知脱钩）
        rxc, pxc, _, _ = pearson(x_xle, x_cl)
        row["r_xle_cl"] = None if rxc is None else round(rxc, 3)
        row["fl_xle_cl"] = sigflag(pxc) if pxc is not None else None
        seg_rows.append(row)

    # ---- 60 日滚动相关（全窗口，日频）----
    def rolling_corr(a, b, win=60):
        c = a.rolling(win, min_periods=win).corr(b)
        return [None if pd.isna(v) else round(float(v), 4) for v in c.values]
    corr_km_ng = rolling_corr(ret["KMI"], ret["NG=F"])
    corr_km_cl = rolling_corr(ret["KMI"], ret["CL=F"])
    corr_wmb_ng = rolling_corr(ret["WMB"], ret["NG=F"])
    corr_xle_cl = rolling_corr(ret["XLE"], ret["CL=F"])

    # ---- 最新 60/120/250 日现价相关 ----
    latest = {}
    for tag, x in [("ng", ret["NG=F"]), ("cl", ret["CL=F"]), ("xle", ret["XLE"]), ("spy", ret["SPY"])]:
        for win in [60, 120, 250]:
            c = ret["KMI"][-win:].corr(x[-win:])
            latest[f"corr{win}_{tag}"] = None if pd.isna(c) else round(float(c), 3)
        b = np.cov(x[-120:], ret["KMI"][-120:])[0, 1] / x[-120:].var() if len(x[-120:].dropna()) > 30 else None
        latest[f"beta120_{tag}"] = None if b is None else round(float(b), 4)
    # 60 日 β 现值
    for tag, x in [("ng", ret["NG=F"]), ("cl", ret["CL=F"])]:
        xx, yy = x[-60:].dropna(), ret["KMI"][-60:].dropna()
        b = np.cov(xx, yy)[0, 1] / xx.var()
        latest[f"beta60_{tag}"] = round(float(b), 4)

    # ---- 月度口径（长周期稳健对照）----
    mret = ret.groupby(panel["date"].dt.to_period("M")).apply(lambda g: (1 + g / 100).prod() - 1) * 100
    mdates = [str(p) for p in mret.index]
    monthly = {}
    for tag, xname in [("ng", "NG=F"), ("cl", "CL=F"), ("xle", "XLE"), ("spy", "SPY")]:
        r, p, fl, n = pearson(mret["KMI"], mret[xname])
        monthly[tag] = {"r": None if r is None else round(r, 3), "p": None if p is None else round(p, 4),
                        "flag": fl, "n": n}
        # 近 36 个月
        if n and n > 36:
            rr, pp, ff, nn = pearson(mret["KMI"].iloc[-36:], mret[xname].iloc[-36:])
            monthly[f"{tag}_36"] = {"r": None if rr is None else round(rr, 3),
                                    "p": None if pp is None else round(pp, 4), "flag": ff, "n": nn}

    # ---- 多元回归：控 SPY+XLE 后 NG/CL 还有多少增量解释力 ----
    def ols(X, y):
        X1 = np.column_stack([np.ones(len(y)), X])
        beta, _, _, _ = np.linalg.lstsq(X1, y, rcond=None)
        yhat = X1 @ beta
        resid = y - yhat
        dof = len(y) - X1.shape[1]
        s2 = (resid @ resid) / dof
        covb = s2 * np.linalg.inv(X1.T @ X1)
        se = np.sqrt(np.diag(covb))
        t = beta / se
        r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
        return beta, t, r2, len(y)
    mreg = {}
    for lbl, a, b in [("full", "2011-02-14", "2026-09-04"),
                      ("p23", "2023-01-03", "2026-09-04"),
                      ("p7", "2025-01-02", "2026-09-04")]:
        lo = (panel["date"] >= pd.Timestamp(a)) & (panel["date"] <= pd.Timestamp(b))
        y = ret["KMI"][lo].fillna(0).values
        X4 = ret[["SPY", "XLE", "NG=F", "CL=F"]][lo].fillna(0).values
        X2 = ret[["SPY", "XLE"]][lo].fillna(0).values
        b4, t4, r2_4, n = ols(X4, y)
        b2, t2, r2_2, _ = ols(X2, y)
        # 单独 NG/CL 单变量 R²
        def uv(col):
            X = ret[col][lo].fillna(0).values
            _, _, r2u, _ = ols(X.reshape(-1, 1), y)
            return r2u
        mreg[lbl] = {
            "n": n,
            "r2_spy_xle": round(r2_2, 4), "r2_full": round(r2_4, 4),
            "incr_r2_ng_cl_pp": round((r2_4 - r2_2) * 100, 3),
            "b_spy": round(float(b4[1]), 4), "t_spy": round(float(t4[1]), 2),
            "b_xle": round(float(b4[2]), 4), "t_xle": round(float(t4[2]), 2),
            "b_ng": round(float(b4[3]), 4), "t_ng": round(float(t4[3]), 2),
            "b_cl": round(float(b4[4]), 4), "t_cl": round(float(t4[4]), 2),
            "r2_ng_uv": round(uv("NG=F"), 4), "r2_cl_uv": round(uv("CL=F"), 4),
        }

    # ---- 事件窗口累计涨跌 ----
    events = []
    for key, ev in EVENTS.items():
        lo = (panel["date"] >= pd.Timestamp(ev["a"])) & (panel["date"] <= pd.Timestamp(ev["b"]))
        sub = panel[lo]
        row = {"key": key, "label": ev["label"], "span": f"{ev['a']}~{ev['b']}"}
        for tk in ["KMI", "WMB", "XLE", "SPY"]:
            s = sub[tk].dropna()
            row[f"chg_{tk}"] = round(float((s.iloc[-1] / s.iloc[0] - 1) * 100), 2) if len(s) > 1 else None
        for tk, col in [("NG=F", "ng"), ("CL=F", "cl")]:
            s = sub[tk].dropna()
            row[f"chg_{col}"] = round(float((s.iloc[-1] / s.iloc[0] - 1) * 100), 2) if len(s) > 1 else None
        events.append(row)
    # 事件单日细表：2020-04-20/21 负油价、2026-09 油急拉段日收益
    singledays = []
    for d in ["2020-04-20", "2020-04-21"]:
        i = panel.index[panel["date"] == pd.Timestamp(d)][0]
        sd = {"date": d}
        for tk in ["KMI", "CL=F", "NG=F", "XLE", "SPY"]:
            v = ret[tk].iloc[i]
            sd[tk] = round(float(v), 2) if not np.isnan(v) else None
        singledays.append(sd)
    oil26 = []
    lo = (panel["date"] >= pd.Timestamp("2026-08-28")) & (panel["date"] <= pd.Timestamp("2026-09-04"))
    for i in panel.index[lo]:
        sd = {"date": str(panel["date"].iloc[i].date())}
        for tk in ["KMI", "CL=F", "NG=F", "XLE", "SPY", "WMB"]:
            v = ret[tk].iloc[i]
            sd[tk] = round(float(v), 2) if not np.isnan(v) else None
        oil26.append(sd)

    # ---- 58 号报告同窗对照：XLE×CL / KMI×CL（2025-11-01 起，与监测报告口径一致）----
    lo58 = panel["date"] >= pd.Timestamp("2025-11-01")
    same58 = {}
    for tag, x, y in [("xle_cl", ret["XLE"], ret["CL=F"]), ("kmi_cl", ret["KMI"], ret["CL=F"]),
                      ("kmi_ng", ret["KMI"], ret["NG=F"]), ("kmi_xle", ret["KMI"], ret["XLE"])]:
        r, p, fl, n = pearson(x[lo58], y[lo58])
        same58[tag] = {"r": None if r is None else round(r, 3), "flag": fl, "n": n}

    # ---- 条件均值：油价大涨/大跌日 KMI 平均日收益（分两代：2011-2019 vs 2020+）----
    cond = []
    eras = [("2011-02–2019-12", "2011-02-14", "2019-12-31"), ("2020-01–2026-09", "2020-01-02", "2026-09-04")]
    for elabel, a, b in eras:
        lo = (panel["date"] >= pd.Timestamp(a)) & (panel["date"] <= pd.Timestamp(b))
        cl_ret_e = ret["CL=F"][lo]
        kmi_ret_e = ret["KMI"][lo]
        rows = pd.DataFrame({"cl": cl_ret_e, "kmi": kmi_ret_e}).dropna()
        rec = {"era": elabel, "n": len(rows)}
        for thr, tag in [(2.0, "cl_up2"), (-2.0, "cl_dn2")]:
            sub = rows[rows["cl"] >= thr] if thr > 0 else rows[rows["cl"] <= thr]
            rec[tag] = {"n": int(len(sub)),
                        "kmi_avg": round(float(sub["kmi"].mean()), 3) if len(sub) else None,
                        "cl_avg": round(float(sub["cl"].mean()), 2) if len(sub) else None}
        # 气价 ±3%
        ng_ret_e = ret["NG=F"][lo]
        rows2 = pd.DataFrame({"ng": ng_ret_e, "kmi": kmi_ret_e}).dropna()
        for thr, tag in [(3.0, "ng_up3"), (-3.0, "ng_dn3")]:
            sub = rows2[rows2["ng"] >= thr] if thr > 0 else rows2[rows2["ng"] <= thr]
            rec[tag] = {"n": int(len(sub)),
                        "kmi_avg": round(float(sub["kmi"].mean()), 3) if len(sub) else None,
                        "ng_avg": round(float(sub["ng"].mean()), 2) if len(sub) else None}
        cond.append(rec)

    # ---- KMI 2026 年高点与近期回撤 ----
    kmi26 = panel[(panel["date"] >= "2026-01-01") & panel["KMI"].notna()]
    i_peak = kmi26["KMI"].idxmax()
    kmi26_snap = {"peak_date": str(panel["date"].iloc[i_peak].date()),
                  "peak": round(float(panel["KMI"].iloc[i_peak]), 2),
                  "last": round(float(panel["KMI"].dropna().iloc[-1]), 2),
                  "dd_from_peak_pct": round(float((panel["KMI"].dropna().iloc[-1] / panel["KMI"].iloc[i_peak] - 1) * 100), 2)}

    # ---- 归一化价格 2011-02-14=100 ----
    norm = pd.DataFrame(index=panel["date"])
    base_day = panel["date"] >= pd.Timestamp("2011-02-14")
    for tk in ["KMI", "NG=F", "CL=F", "XLE", "SPY", "WMB", "UNG"]:
        s = panel[tk]
        fv = s[base_day].dropna().iloc[0] if s[base_day].notna().any() else np.nan
        norm[tk] = (s / fv * 100).values if not np.isnan(fv) else s.values
    norm_out = {k: [None if pd.isna(v) else round(float(v), 2) for v in norm[k].values] for k in norm.columns}

    # ---- 现价快照 ----
    snap = {}
    for tk in ["KMI", "NG=F", "CL=F", "UNG", "WMB", "XLE", "SPY"]:
        s = panel[tk].dropna()
        if len(s):
            snap[tk] = {"last": round(float(s.iloc[-1]), 2),
                        "date": str(panel["date"].iloc[panel.index[panel[tk].notna()][-1]].date()),
                        "min": round(float(s.min()), 2), "max": round(float(s.max()), 2)}
    # KMI 区间累计
    s = panel["KMI"].dropna()
    snap["KMI_chg_ytd"] = round(float((s.iloc[-1] / s[s.index >= s.index[-1] - 250].iloc[0] - 1) * 100), 2)

    dates = [str(d.date()) for d in panel["date"]]

    out = {
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "data_span": f"{panel['date'].min().date()} ~ {panel['date'].max().date()}",
            "corr_window": 60,
            "note": "股票用 adj_close（含股息），期货(NG=F/CL=F)用 close（前月连续）。收益为日频百分数。",
        },
        "dates": dates,
        "norm_price": norm_out,
        "seg": seg_rows,
        "latest": latest,
        "monthly": monthly,
        "mreg": mreg,
        "events": events,
        "singledays": singledays,
        "oil26": oil26,
        "same58": same58,
        "cond": cond,
        "kmi26_snap": kmi26_snap,
        "corr60": {"km_ng": corr_km_ng, "km_cl": corr_km_cl, "wmb_ng": corr_wmb_ng, "xle_cl": corr_xle_cl},
        "snapshot": snap,
        "full_last": {"kmi": round(float(ret["KMI"].dropna().iloc[-1]), 3),
                      "ng": round(float(ret["NG=F"].dropna().iloc[-1]), 3),
                      "cl": round(float(ret["CL=F"].dropna().iloc[-1]), 3)},
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    # 控制台简报
    print("=== 分段相关性 KMI×NG / KMI×CL ===")
    for r0 in seg_rows:
        print(f"{r0['label']:<32} NG r={r0['r_ng']} {r0['fl_ng']} β={r0['b_ng']} | CL r={r0['r_cl']} {r0['fl_cl']} β={r0['b_cl']} | XLE r={r0['r_xle']} | SPY r={r0['r_spy']} | WMB×NG r={r0['r_wmb_ng']} WMB×CL r={r0['r_wmb_cl']} | XLE×CL r={r0['r_xle_cl']}")
    print("=== 最新相关 ===", json.dumps(latest, ensure_ascii=False))
    print("=== 月度 ===", json.dumps(monthly, ensure_ascii=False))
    print("=== 多元回归 ===")
    for k, v in mreg.items():
        print(k, v)
    print("=== 事件 ===")
    for e in events:
        print(e["label"], {k: v for k, v in e.items() if k not in ("label", "key")})
    print("=== 2026-08-28~09-04 油急拉日线 ===")
    for sd in oil26:
        print(sd)
    print("=== 58 同窗(2025-11+) ===", json.dumps(same58, ensure_ascii=False))
    print("=== 条件均值 ===")
    for c in cond:
        print(c)
    print("=== KMI 2026 ===", json.dumps(kmi26_snap, ensure_ascii=False))

if __name__ == "__main__":
    main()
