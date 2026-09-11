# -*- coding: utf-8 -*-
"""KMI 条件收益研究（主口径 = KMI 自身绝对收益 %）

三个问题：
  A. VIX 抬升时 KMI 表现
  B. 中期选举窗口 KMI 表现
  C. 10Y 抬升时 KMI 表现
附带 SPY 同日/同期收益作为"市场背景参照列"（非主口径，仅用于判断抗跌与否）。

数据：
  KMI  data/KMI/KMI, 1D.csv
  SPY  data/spy/SPY, 1D.csv
  VIX  data/vix/VIX, 1D.csv
  DGS10 data/us_treasury/DGS10.csv

口径：
  - 收益 = pct_change*100（%）；正=涨。未扣股息
  - 分档统计：均值 / 中位数 / 胜率 / n / t / p（单样本 t 检验 H0: 均值=0）
  - 事件研究：触发日后 fwd5/20/60 交易日累计收益，与全样本同长窗口基准率对比
  - 事件去重：触发日之间至少间隔 20 个交易日（避免同一波动簇重复计数）
  - 样本 n<8 → reliable=False；n<30 → 标注"样本偏小"
输出：results/kmi_conditions_analysis.json
"""
import os, json
from math import sqrt, erf
from datetime import date as _date
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
HORIZONS = [5, 20, 60]


def pearson_pvalue(r, n):
    if n < 3 or r >= 1 or r <= -1:
        return 1.0
    t = r * sqrt((n - 2) / max(1e-9, (1 - r * r)))
    phi = 0.5 * (1 + erf(abs(t) / sqrt(2)))
    return float(2 * (1 - phi))


def load_local(folder, name, px_col="close"):
    df = pd.read_csv(os.path.join(DATA, folder, name), parse_dates=["date"])
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    df["px"] = df[px_col]
    df["ret"] = df["px"].pct_change() * 100
    return df[["date", "px", "ret"]]


def get_kmi():
    df = pd.read_csv(os.path.join(DATA, "KMI", "KMI, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    d = float((df["adj_close"] / df["close"] - 1).abs().max())
    col = "adj_close" if d > 1e-4 else "close"
    df["px"] = df[col]
    df["ret"] = df["px"].pct_change() * 100
    return df[["date", "px", "ret"]], col, d


def get_vix():
    df = pd.read_csv(os.path.join(DATA, "vix", "VIX, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    df["vix"] = df["close"]
    df["d_vix"] = df["vix"].diff()
    df["vix_chg5"] = df["vix"].pct_change(5) * 100
    return df[["date", "vix", "d_vix", "vix_chg5"]]


def get_dgs10():
    df = pd.read_csv(os.path.join(DATA, "us_treasury", "DGS10.csv"))
    df = df.rename(columns={"observation_date": "date"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna().sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    df["y10"] = df["DGS10"]
    df["d_bp"] = df["y10"].diff() * 100
    df["bp20"] = (df["y10"] - df["y10"].shift(20)) * 100
    df["bp60"] = (df["y10"] - df["y10"].shift(60)) * 100
    return df[["date", "y10", "d_bp", "bp20", "bp60"]]


def block(vals, name=None):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], dtype=float)
    n = len(v)
    if n == 0:
        return {"n": 0, "reliable": False}
    out = {"n": int(n)}
    if n == 1:
        out.update({"mean": round(float(v[0]), 3), "median": round(float(v[0]), 3),
                    "win": round(float((v > 0).mean() * 100), 1), "reliable": False})
        return out
    t, p = stats.ttest_1samp(v, 0.0)
    out.update({
        "mean": round(float(v.mean()), 3), "median": round(float(np.median(v)), 3),
        "win": round(float((v > 0).mean() * 100), 1), "sd": round(float(v.std(ddof=1)), 2),
        "t": round(float(t), 2), "p": round(float(p), 4),
        "reliable": bool(n >= 30),
    })
    if n >= 8:
        try:
            _, pw = stats.wilcoxon(v)
            out["wilcoxon_p"] = round(float(pw), 4)
        except Exception:
            pass
    return out


def fwd_returns(px, idx, horizons):
    out = {}
    n = len(px)
    for h in horizons:
        j = idx + h
        out[h] = float((px[j] / px[idx] - 1) * 100) if j < n else None
    return out


def dedupe(idxs, gap=20):
    out, last = [], -10 ** 9
    for i in idxs:
        if i - last >= gap:
            out.append(i)
            last = i
    return out


def event_study(pxm, spym, idxs, horizons=HORIZONS):
    base_k = {h: [] for h in horizons}
    base_s = {h: [] for h in horizons}
    for i in range(len(pxm)):
        fk = fwd_returns(pxm, i, horizons)
        fs = fwd_returns(spym, i, horizons)
        for h in horizons:
            base_k[h].append(fk[h])
            base_s[h].append(fs[h])
    fk_all, fs_all = {h: [] for h in horizons}, {h: [] for h in horizons}
    for i in idxs:
        fk = fwd_returns(pxm, i, horizons)
        fs = fwd_returns(spym, i, horizons)
        for h in horizons:
            fk_all[h].append(fk[h])
            fs_all[h].append(fs[h])
    return {
        "kmi_fwd": {str(h): block(fk_all[h]) for h in horizons},
        "spy_fwd": {str(h): block(fs_all[h]) for h in horizons},
        "baseline": {str(h): block(base_k[h]) for h in horizons},
        "baseline_spy": {str(h): block(base_s[h]) for h in horizons},
        "excess_vs_baseline": {str(h): round((block(fk_all[h]).get("median") or 0) - (block(base_k[h]).get("median") or 0), 3)
                               for h in horizons},
    }


def first_tuesday_nov(y):
    d1 = _date(y, 11, 1)
    fm = 1 + (0 - d1.weekday()) % 7
    return pd.Timestamp(_date(y, 11, fm + 1))


def main():
    kmi, price_col, adj_diff = get_kmi()
    spy = load_local("spy", "SPY, 1D.csv")
    vix, y10 = get_vix(), get_dgs10()
    pxk = kmi["px"].values

    res = {"meta": {
        "subject": "KMI (Kinder Morgan) 条件收益研究 · 主口径 KMI 绝对收益 %",
        "kmi_range": [str(kmi["date"].iloc[0].date()), str(kmi["date"].iloc[-1].date())],
        "kmi_last": round(float(kmi["px"].iloc[-1]), 2),
        "kmi_rows": int(len(kmi)), "price_col": price_col,
        "adj_close_vs_close_maxdiff": round(adj_diff, 6),
        "horizons_days": HORIZONS,
        "notes": [
            "主口径 = KMI 自身绝对收益（未扣股息；KMI 年化股息率 ~4%，日均 drag ≈ -0.016%/日）",
            "SPY 列为市场背景参照，非主结论",
            "事件样本已按间隔 ≥20 交易日去重",
            "fwd 基准率用全样本同长度窗口（存在重叠，仅作水平参照）",
        ],
        "generated": str(pd.Timestamp.now(tz="Asia/Shanghai")),
    }}

    # ================= A. VIX =================
    A = {}
    m = pd.merge(kmi, vix, on="date", how="inner").reset_index(drop=True)
    m = pd.merge(m, spy.rename(columns={"px": "spy_px", "ret": "spy_ret"}), on="date", how="left")
    pxm, spym = m["px"].values, m["spy_px"].values
    A["sample"] = {"n": int(len(m)), "range": [str(m["date"].iloc[0].date()), str(m["date"].iloc[-1].date())]}

    bins = [(-np.inf, -5), (-5, -2), (-2, 0), (0, 2), (2, 5), (5, np.inf)]
    labels = ["VIX 大跌 ≤-5", "VIX 跌 -5~-2", "VIX 微跌 -2~0", "VIX 微涨 0~+2", "VIX 涨 +2~+5", "VIX 大涨 >+5"]
    A["by_daily_change"] = []
    for (lo, hi), lab in zip(bins, labels):
        msk = (m["d_vix"] > lo) & (m["d_vix"] <= hi)
        A["by_daily_change"].append({
            "bucket": lab, "d_vix_range": [None if lo == -np.inf else lo, None if hi == np.inf else hi],
            "kmi_same_day": block(m.loc[msk, "ret"]),
            "spy_same_day": block(m.loc[msk, "spy_ret"]),
        })
    sub = m.dropna(subset=["d_vix", "ret"])
    r = float(np.corrcoef(sub["d_vix"], sub["ret"])[0, 1])
    A["corr_dvix_kmi"] = {"r": round(r, 3), "n": int(len(sub)), "p": round(pearson_pvalue(r, len(sub)), 4)}

    A["events_up5"] = []
    for thr in [20, 30, 50]:
        raw = m.index[m["vix_chg5"] >= thr].tolist()
        dd = dedupe(raw, 20)
        st = event_study(pxm, spym, dd)
        st.update({"trigger": f"VIX 5 日累计涨幅 ≥ +{thr}%", "n_raw": len(raw), "n_dedup": len(dd)})
        A["events_up5"].append(st)

    A["by_vix_level"] = []
    for lo, hi in [(0, 15), (15, 20), (20, 25), (25, 30), (30, 100)]:
        msk = (m["vix"] > lo) & (m["vix"] <= hi)
        idxs = m.index[msk].tolist()
        A["by_vix_level"].append({
            "bucket": f"VIX {lo}-{hi}",
            "kmi_same_day": block(m.loc[msk, "ret"]),
            "kmi_fwd20": block([fwd_returns(pxm, i, [20])[20] for i in idxs]),
            "spy_fwd20": block([fwd_returns(spym, i, [20])[20] for i in idxs]),
        })
    A["current"] = {
        "vix": round(float(m["vix"].iloc[-1]), 2), "date": str(m["date"].iloc[-1].date()),
        "vix_20d_low": round(float(m["vix"].iloc[-20:].min()), 2),
        "rise_from_20d_low_pct": round(float(m["vix"].iloc[-1] / m["vix"].iloc[-20:].min() - 1) * 100, 1),
        "vix_chg5_pct": round(float(m["vix_chg5"].iloc[-1]), 1),
    }
    res["A_vix"] = A

    # ================= C. 10Y =================
    C = {}
    my = pd.merge(kmi, y10, on="date", how="inner").reset_index(drop=True)
    my = pd.merge(my, spy.rename(columns={"px": "spy_px", "ret": "spy_ret"}), on="date", how="left")
    pxy, spyy = my["px"].values, my["spy_px"].values
    C["sample"] = {"n": int(len(my)), "range": [str(my["date"].iloc[0].date()), str(my["date"].iloc[-1].date())]}

    ybins = [(-np.inf, -10), (-10, -5), (-5, 0), (0, 5), (5, 10), (10, np.inf)]
    ylabels = ["10Y 大降 ≤-10bp", "10Y 降 -10~-5bp", "10Y 微降 -5~0bp", "10Y 微升 0~+5bp", "10Y 升 +5~+10bp", "10Y 大升 >+10bp"]
    C["by_daily_change"] = []
    for (lo, hi), lab in zip(ybins, ylabels):
        msk = (my["d_bp"] > lo) & (my["d_bp"] <= hi)
        C["by_daily_change"].append({
            "bucket": lab, "kmi_same_day": block(my.loc[msk, "ret"]),
            "spy_same_day": block(my.loc[msk, "spy_ret"]),
        })
    suby = my.dropna(subset=["d_bp", "ret"])
    ry = float(np.corrcoef(suby["d_bp"], suby["ret"])[0, 1])
    C["corr_db10_kmi"] = {"r": round(ry, 3), "n": int(len(suby)), "p": round(pearson_pvalue(ry, len(suby)), 4)}

    C["events"] = []
    for col, span, thr in [("bp20", 20, 25), ("bp20", 20, 50), ("bp60", 60, 50), ("bp60", 60, 100)]:
        raw = my.index[my[col] >= thr].tolist()
        dd = dedupe(raw, 20)
        st = event_study(pxy, spyy, dd)
        st.update({"trigger": f"{span} 日累计 10Y +{thr}bp 以上", "n_raw": len(raw), "n_dedup": len(dd)})
        C["events"].append(st)

    C["by_y10_level"] = []
    for lo, hi in [(0, 2), (2, 3), (3, 4), (4, 4.5), (4.5, 10)]:
        msk = (my["y10"] > lo) & (my["y10"] <= hi)
        idxs = my.index[msk].tolist()
        C["by_y10_level"].append({
            "bucket": f"10Y {lo}-{hi}%",
            "kmi_same_day": block(my.loc[msk, "ret"]),
            "kmi_fwd20": block([fwd_returns(pxy, i, [20])[20] for i in idxs]),
            "spy_fwd20": block([fwd_returns(spyy, i, [20])[20] for i in idxs]),
        })
    C["current"] = {
        "y10": round(float(my["y10"].iloc[-1]), 2), "date": str(my["date"].iloc[-1].date()),
        "bp20": round(float(my["bp20"].iloc[-1]), 1), "bp60": round(float(my["bp60"].iloc[-1]), 1),
    }
    res["C_y10"] = C

    # ================= B. 中期选举 =================
    B = {}
    mid_years = [2014, 2018, 2022]
    all_years = list(range(2011, 2027))

    def window_ret(df, ev, pre, post):
        pos = df.index[df["date"] <= ev]
        if len(pos) == 0:
            return None
        D = int(pos[-1])
        o = {"event_date": str(ev.date()), "D": D}
        if D - pre >= 0:
            o["pre"] = float((df["px"].iloc[D] / df["px"].iloc[D - pre] - 1) * 100)
        if D + post < len(df):
            o["post"] = float((df["px"].iloc[D + post] / df["px"].iloc[D] - 1) * 100)
            if D - pre >= 0:
                o["total"] = float((df["px"].iloc[D + post] / df["px"].iloc[D - pre] - 1) * 100)
        return o

    kmi2 = kmi.copy()
    B["midterm_events"] = []
    for y in mid_years:
        d = first_tuesday_nov(y)
        w = window_ret(kmi2, d, 20, 20)
        w60 = window_ret(kmi2, d, 60, 60)
        B["midterm_events"].append({"year": y, "date": str(d.date()),
                                    "w20": w, "w60": w60})

    def collect(key, group):
        out = {}
        for name, pre, post in [("pre20_post20", 20, 20), ("pre60_post60", 60, 60)]:
            pass
        return out

    def rng(years, pre, post):
        rows = []
        for y in years:
            d = first_tuesday_nov(y)
            if d > kmi2["date"].iloc[-1]:
                continue
            w = window_ret(kmi2, d, pre, post)
            if w and "post" in w:
                rows.append({"year": y, "event_date": w["event_date"], **{k: v for k, v in w.items() if k not in ("D", "event_date")}})
        return rows

    mid_rows20 = rng(mid_years, 20, 20)
    ctrl_rows20 = rng([y for y in all_years if y not in mid_years], 20, 20)
    mid_rows60 = rng(mid_years, 60, 60)
    ctrl_rows60 = rng([y for y in all_years if y not in mid_years], 60, 60)

    B["windows"] = {
        "midterm": {
            "n": len(mid_rows20),
            "pre20": block([r.get("pre") for r in mid_rows20]),
            "post20": block([r.get("post") for r in mid_rows20]),
            "pre60": block([r.get("pre") for r in mid_rows60]),
            "post60": block([r.get("post") for r in mid_rows60]),
            "rows20": mid_rows20, "rows60": mid_rows60,
        },
        "control_other_nov": {
            "n": len(ctrl_rows20),
            "pre20": block([r.get("pre") for r in ctrl_rows20]),
            "post20": block([r.get("post") for r in ctrl_rows20]),
            "pre60": block([r.get("pre") for r in ctrl_rows60]),
            "post60": block([r.get("post") for r in ctrl_rows60]),
            "rows20": ctrl_rows20, "rows60": ctrl_rows60,
        },
    }
    # Welch 对比（中期 vs 对照）
    def welch(a, b):
        a = [x for x in a if x is not None and np.isfinite(x)]
        b = [x for x in b if x is not None and np.isfinite(x)]
        if len(a) < 2 or len(b) < 2:
            return None
        t, p = stats.ttest_ind(a, b, equal_var=False)
        return {"t": round(float(t), 2), "p": round(float(p), 4), "n_a": len(a), "n_b": len(b)}
    B["midterm_vs_control"] = {
        "pre20": welch([r.get("pre") for r in mid_rows20], [r.get("pre") for r in ctrl_rows20]),
        "post20": welch([r.get("post") for r in mid_rows20], [r.get("post") for r in ctrl_rows20]),
        "pre60": welch([r.get("pre") for r in mid_rows60], [r.get("pre") for r in ctrl_rows60]),
        "post60": welch([r.get("post") for r in mid_rows60], [r.get("post") for r in ctrl_rows60]),
    }
    pend = first_tuesday_nov(2026)
    B["pending_2026"] = {"date": str(pend.date()), "days_to": int((pend - kmi2["date"].iloc[-1]).days),
                         "trading_days_to": int(pd.bdate_range(kmi2["date"].iloc[-1], pend).size - 1)}
    res["B_midterm"] = B

    with open(os.path.join(OUT, "kmi_conditions_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, allow_nan=False)
    print("saved: results/kmi_conditions_analysis.json")

    # ---------------- 打印 ----------------
    def line_block(s):
        return f"{s.get('median','-'):>8} {s.get('mean','-'):>8} {s.get('win','-'):>7} {s.get('n','-'):>6} {s.get('p','-'):>8}"

    print("\n########## A. VIX 抬升 × KMI ##########")
    print(f"n={A['sample']['n']}  {A['sample']['range'][0]}~{A['sample']['range'][1]}")
    print(f"corr(ΔVIX, KMI当日) r={A['corr_dvix_kmi']['r']} p={A['corr_dvix_kmi']['p']}")
    print(f"{'档':<16}{'KMI中位':>8}{'KMI均值':>8}{'胜率':>7}{'n':>6}{'p':>8}   | SPY中位")
    for b in A["by_daily_change"]:
        print(f"{b['bucket']:<16}{line_block(b['kmi_same_day'])}   | {b['spy_same_day'].get('median','-')}")
    print("\n-- VIX 5日抬升事件（去重）：KMI 未来收益（中位/基准中位）--")
    for e in A["events_up5"]:
        s = f"{e['trigger']:<26} n={e['n_raw']}→{e['n_dedup']:<4}"
        for h in ["5", "20", "60"]:
            s += f" | f{h}: {e['kmi_fwd'][h].get('median')} (基准{e['baseline'][h].get('median')}) p={e['kmi_fwd'][h].get('p')}"
        print(s)
        s2 = " " * 26 + "  SPY 对照:"
        for h in ["5", "20", "60"]:
            s2 += f" f{h}: {e['spy_fwd'][h].get('median')}"
        print(s2)
    print("\n-- VIX 水平分档 --")
    for b in A["by_vix_level"]:
        print(f"{b['bucket']:<12} 当日中位 {b['kmi_same_day'].get('median'):>7} (n={b['kmi_same_day'].get('n')}) | fwd20中位 {b['kmi_fwd20'].get('median'):>7} 胜率{b['kmi_fwd20'].get('win'):>6} p={b['kmi_fwd20'].get('p')} (SPY {b['spy_fwd20'].get('median')})")
    print("当前:", A["current"])

    print("\n########## C. 10Y 抬升 × KMI ##########")
    print(f"n={C['sample']['n']}  {C['sample']['range'][0]}~{C['sample']['range'][1]}")
    print(f"corr(Δ10Y bp, KMI当日) r={C['corr_db10_kmi']['r']} p={C['corr_db10_kmi']['p']}")
    for b in C["by_daily_change"]:
        print(f"{b['bucket']:<18}{line_block(b['kmi_same_day'])}   | SPY中位 {b['spy_same_day'].get('median')}")
    print("\n-- 10Y 抬升事件（去重）--")
    for e in C["events"]:
        s = f"{e['trigger']:<26} n={e['n_raw']}→{e['n_dedup']:<4}"
        for h in ["5", "20", "60"]:
            s += f" | f{h}: {e['kmi_fwd'][h].get('median')} (基准{e['baseline'][h].get('median')}) p={e['kmi_fwd'][h].get('p')}"
        print(s)
        print(" " * 26 + "  SPY 对照:" + "".join(f" f{h}: {e['spy_fwd'][h].get('median')}" for h in ["5", "20", "60"]))
    print("\n-- 10Y 水平分档 --")
    for b in C["by_y10_level"]:
        print(f"{b['bucket']:<12} 当日中位 {b['kmi_same_day'].get('median'):>7} (n={b['kmi_same_day'].get('n')}) | fwd20中位 {b['kmi_fwd20'].get('median'):>7} 胜率{b['kmi_fwd20'].get('win'):>6} p={b['kmi_fwd20'].get('p')} (SPY {b['spy_fwd20'].get('median')})")
    print("当前:", C["current"])

    print("\n########## B. 中期选举 × KMI ##########")
    for e in B["midterm_events"]:
        print(f"  {e['year']} ({e['date']}): 前20 {e['w20'].get('pre'):+.2f}% 后20 {e['w20'].get('post'):+.2f}% | 前60 {e['w60'].get('pre'):+.2f}% 后60 {e['w60'].get('post'):+.2f}%")
    print("中期组:", {k: B["windows"]["midterm"][k] for k in ["n", "pre20", "post20", "pre60", "post60"]})
    print("对照组:", {k: B["windows"]["control_other_nov"][k] for k in ["n", "pre20", "post20", "pre60", "post60"]})
    print("Welch:", B["midterm_vs_control"])
    print("2026 待发生:", B["pending_2026"])


if __name__ == "__main__":
    main()
