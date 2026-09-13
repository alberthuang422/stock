#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
厄尔尼诺（ENSO）对天然橡胶价格的促进作用 —— 定量事件研究 + 回归

数据源（权威公开源，本地缓存 Temp/rubber_enso/）：
  1) NOAA CPC ONI 月度指数 oni.ascii.txt（1950-2026，3 个月滑动中心值）
  2) World Bank Pink Sheet 月度商品价格（1960M01-2025M12）
     - Rubber, RSS3  ($/kg)   ★ 主口径：1960 起连续 66 年（TSR20 仅 1999 起，做辅助）
     - Rubber, TSR20 ($/kg)   辅助口径（1999-2025）
     - Crude oil, Brent       原油控制（合成胶替代链）
     - Non-energy index       商品指数控制（剔除大宗商品共同 β）
  3) 东方财富主连日线 data/rubber/：RU 1997-04~、NR 2019-08~、BR 2023-07~

方法：
  A. EN 事件识别：ONI >= +0.5 且连续 >= 5 个重叠 3 月季（NOAA 定义）
     强度档：弱 0.5-0.9 / 中 1.0-1.4 / 强 1.5-1.9 / 超强 >= 2.0
  B. 事件研究：锚定 ONI 中心月，T+3/6/12/24 累计对数收益；基线=全样本无条件均值
     显著性：Welch t + Mann-Whitney（重叠窗口使 t 偏乐观，故并列秩检验）
     稳健性：另报"无前视"版本（锚定 onset+1，因 ONI 中心值滞后约 1 个月公布）
  C. 回归：fwd_H r = a + b*ONI (+ 控制项)，Newey-West HAC t
  D. 不对称：拉尼娜对照；割胶季（6-10 月）子样本
  E. 结构稳定：1960-1999 vs 2000-2025
  F. 期限扫描：corr(ONI_t, fwd_H) for H = 0..36 个月

产出：results/rubber_enso_analysis.json + 控制台摘要
"""
import json
import os
import re

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, "Temp", "rubber_enso")
OUT = os.path.join(ROOT, "results", "rubber_enso_analysis.json")

SEASON_CENTER = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
                 "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
TIER = [(2.0, "超强"), (1.5, "强"), (1.0, "中"), (0.5, "弱")]
HORIZONS = (3, 6, 12, 24)
TODAY = pd.Timestamp("2026-09-12")


# ---------------------------------------------------------------- 数据装载
def load_oni():
    rows = []
    with open(os.path.join(TMP, "oni.txt"), encoding="utf-8", errors="ignore") as f:
        for ln in f:
            p = ln.split()
            if len(p) != 4 or p[0] not in SEASON_CENTER or not re.match(r"^\d+$", p[1]):
                continue
            rows.append((p[0], int(p[1]), float(p[3]), SEASON_CENTER[p[0]]))
    df = pd.DataFrame(rows, columns=["season", "year", "anom", "cm"])
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["cm"], day=1))
    df = df.sort_values("date").drop_duplicates("date").set_index("date")
    return df[["season", "anom"]]


def load_pink():
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(TMP, "wb_monthly.xlsx"),
                                read_only=True, data_only=True)
    cols = {"TSR20": 55, "RSS3": 56, "Brent": 2}
    rec = {}
    for r in wb["Monthly Prices"].iter_rows(min_row=7, values_only=True):
        if not r[0] or not re.match(r"^\d{4}M\d{2}$", str(r[0])):
            continue
        rec[pd.to_datetime(str(r[0]).replace("M", "-") + "-01")] = {
            k: (float(r[i]) if isinstance(r[i], (int, float)) else np.nan)
            for k, i in cols.items()}
    px = pd.DataFrame.from_dict(rec, orient="index").sort_index()
    idx_cols = {"Energy": 2, "NonEnergy": 4, "Agri": 5}
    rec2 = {}
    for r in wb["Monthly Indices"].iter_rows(min_row=10, values_only=True):
        if not r[0] or not re.match(r"^\d{4}M\d{2}$", str(r[0])):
            continue
        rec2[pd.to_datetime(str(r[0]).replace("M", "-") + "-01")] = {
            k: (float(r[i]) if isinstance(r[i], (int, float)) else np.nan)
            for k, i in idx_cols.items()}
    return px.join(pd.DataFrame.from_dict(rec2, orient="index").sort_index(), how="left")


def load_cn_daily(code):
    df = pd.read_csv(os.path.join(ROOT, "data", "rubber", f"{code}.csv"),
                     parse_dates=["date"]).set_index("date").sort_index()
    df = df[df.index <= TODAY]
    v = df["volume"]
    if len(v) > 25 and v.iloc[-1] < v.iloc[-21:-1].mean() * 0.5:
        df = df.iloc[:-1]          # 尾 bar 体检：量不足常态一半 => 不完整 bar，剔除
    return df


# ---------------------------------------------------------------- 统计工具
def ols_nw(y, X, lags=6):
    X = np.asarray(X, float); y = np.asarray(y, float)
    ok = ~(np.isnan(y) | np.isnan(X).any(axis=1))
    y, X = y[ok], X[ok]
    n, k = X.shape
    if n < k + 5:
        return None
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    Xe = X * e[:, None]
    S = Xe.T @ Xe
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = Xe[L:].T @ Xe[:-L]
        S += w * (G + G.T)
    se = np.sqrt(np.diag(XtXi @ S @ XtXi))
    tss = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (e ** 2).sum() / tss if tss > 0 else np.nan
    return {"b": b, "se": se, "t": b / se, "r2": float(r2),
            "r2adj": float(1 - (1 - r2) * (n - 1) / (n - k)), "n": int(n)}


def _fmt(res, names):
    if res is None:
        return None
    return {"names": names,
            "b": [round(float(x), 3) for x in res["b"]],
            "se": [round(float(x), 3) for x in res["se"]],
            "t": [round(float(x), 2) for x in res["t"]],
            "r2": round(res["r2"], 4), "n": res["n"]}


def fwd(px, h):
    return np.log(px.shift(-h) / px) * 100


def find_events(oni, sign=1, min_len=5, thr=0.5):
    flags = (oni["anom"] * sign) >= thr
    ev, run = [], []
    for dt, fl in flags.items():
        if fl:
            run.append(dt)
        else:
            if len(run) >= min_len:
                ev.append(run)
            run = []
    if len(run) >= min_len:
        ev.append(run)
    out = []
    for r in ev:
        sub = oni.loc[r]
        pk = sub["anom"].abs().max()
        tier = next((t for th, t in TIER if pk >= th), "edge")
        out.append({"onset": r[0].strftime("%Y-%m"), "end": r[-1].strftime("%Y-%m"),
                    "peak_abs": round(float(pk), 2),
                    "peak_signed": round(float(sub.loc[sub["anom"].abs().idxmax(), "anom"]), 2),
                    "len_m": len(r),
                    "tier": tier if sign > 0 else "拉尼娜"})
    return out


# ---------------------------------------------------------------- 主流程
def main():
    oni = load_oni()
    pink = load_pink()
    last_oni = oni.iloc[-1]
    df = pink.join(oni[["anom"]], how="left")
    df["oni"] = df["anom"]
    for h in HORIZONS:
        for tag, col in (("rss", "RSS3"), ("tsr", "TSR20"), ("oil", "Brent"),
                         ("ne", "NonEnergy")):
            df[f"{tag}{h}"] = fwd(df[col], h)
    df["mon"] = df.index.month
    df["state"] = np.where(df["oni"] >= 0.5, "厄尔尼诺",
                          np.where(df["oni"] <= -0.5, "拉尼娜", "中性"))
    df["era"] = np.where(df.index < "2000-01-01", "1960-1999", "2000-2025")

    el = find_events(oni, 1)
    la = find_events(oni, -1)
    print(f"[ONI] 最新 {last_oni.name:%Y-%m}({last_oni['season']}) = {last_oni['anom']:+.2f}"
          f" | ONI 样本 {oni.index.min():%Y-%m}~{oni.index.max():%Y-%m} n={len(oni)}")
    print(f"[事件] 厄尔尼诺 {len(el)} 次 / 拉尼娜 {len(la)} 次")
    print(f"[价格] RSS3 {df['RSS3'].first_valid_index():%Y-%m}~"
          f"{df['RSS3'].last_valid_index():%Y-%m} 全样本；"
          f"TSR20 仅 {df['TSR20'].first_valid_index():%Y-%m} 起 -> RSS3 作主口径")

    # ---------------- B. 事件研究
    def event_returns(events, col, shift=0):
        recs = []
        for ev in events:
            a = pd.Timestamp(ev["onset"] + "-01") + pd.DateOffset(months=shift)
            if a not in df.index or pd.isna(df.loc[a, col]):
                continue
            row = dict(ev, anchor=a.strftime("%Y-%m"))
            for h in HORIZONS:
                row[f"t{h}"] = _rnd(df[f"{col[:0]}{col}"].pipe(lambda _: None)) if False else None
            recs.append((a, row))
        return recs

    def build(events, col, shift=0):
        """以 col（RSS3/TSR20/Brent/NonEnergy）计事件窗口收益。"""
        w = {"RSS3": "rss", "TSR20": "tsr", "Brent": "oil", "NonEnergy": "ne"}[col]
        recs = []
        for ev in events:
            a = pd.Timestamp(ev["onset"] + "-01") + pd.DateOffset(months=shift)
            if a not in df.index or pd.isna(df.loc[a, col]):
                continue
            row = dict(ev, anchor=a.strftime("%Y-%m"))
            for h in HORIZONS:
                v = df.loc[a, f"{w}{h}"]
                row[f"t{h}"] = round(float(v), 1) if pd.notna(v) else None
            row["ex12"] = round(float(df.loc[a, "rss12"] - df.loc[a, "ne12"]), 1) \
                if pd.notna(df.loc[a, "rss12"]) and pd.notna(df.loc[a, "ne12"]) else None
            recs.append(row)
        return recs

    ev_rss = build(el, "RSS3")
    ev_rss_nl = build(el, "RSS3", shift=1)     # 无前视
    ev_tsr = build(el, "TSR20")
    ev_oil = build(el, "Brent")
    ev_ne = build(el, "NonEnergy")
    la_rss = build(la, "RSS3")

    base = {h: {"mean": float(df[f"rss{h}"].dropna().mean()),
                "median": float(df[f"rss{h}"].dropna().median()),
                "sd": float(df[f"rss{h}"].dropna().std()),
                "n": int(df[f"rss{h}"].notna().sum())} for h in HORIZONS}

    allmon = {h: df[f"rss{h}"].dropna().values for h in HORIZONS}

    def summ(recs, label):
        o = {"label": label, "n": len(recs)}
        for h in HORIZONS:
            v = np.array([r[f"t{h}"] for r in recs if r.get(f"t{h}") is not None])
            if len(v) < 2:
                o[f"t{h}"] = None
                continue
            a = allmon[h]
            rest = np.setdiff1d(a, v)
            o[f"t{h}"] = {
                "mean": round(float(v.mean()), 1), "median": round(float(np.median(v)), 1),
                "excess": round(float(v.mean() - a.mean()), 1),
                "win": f"{int((v > 0).sum())}/{len(v)}",
                "p_welch": round(float(stats.ttest_ind(v, rest, equal_var=False).pvalue), 4),
                "p_mw": round(float(stats.mannwhitneyu(v, rest, alternative="two-sided").pvalue), 4),
                "n": int(len(v)),
            }
        return o

    tiers = [summ([r for r in ev_rss
                   if next(t for _th, t in TIER if r["peak_abs"] >= _th) == tn], tn)
             for _th, tn in TIER]
    tiers.append(summ(ev_rss, "厄尔尼诺合计"))
    # EN 窗口内"橡胶 - NonEnergy 商品指数"的超额（剔除大宗商品共同 β）
    b_ex = float((df["rss12"] - df["ne12"]).dropna().mean())
    ex_ne = []
    for label, recs in [("厄尔尼诺合计", ev_rss)] + \
            [(tn, [r for r in ev_rss
                   if next(t for _th, t in TIER if r["peak_abs"] >= _th) == tn])
             for _th, tn in TIER]:
        v = np.array([r["ex12"] for r in recs if r.get("ex12") is not None])
        if len(v) < 2:
            continue
        ex_ne.append({"label": label, "n": int(len(v)),
                      "mean_rel_ne": round(float(v.mean()), 1),
                      "excess_over_baseline": round(float(v.mean() - b_ex), 1),
                      "win": f"{int((v > 0).sum())}/{len(v)}"})
    states = [summ([{"t%d" % h: _v(df.loc[d, "rss%d" % h]) for h in HORIZONS}
                    for d in df.index if df.loc[d, "state"] == st], st)
              for st in ("厄尔尼诺", "中性", "拉尼娜")]

    # ---------------- C. 回归
    regs = {}
    for h in (6, 12, 24):
        y = df[f"rss{h}"]
        regs[f"ONI→{h}m"] = _fmt(ols_nw(y, np.c_[np.ones(len(df)), df["oni"]]), ["const", "ONI"])
        regs[f"ONI+油价→{h}m"] = _fmt(
            ols_nw(y, np.c_[np.ones(len(df)), df["oni"], df[f"oil{h}"]]),
            ["const", "ONI", "Brent"])
        regs[f"ONI+商品指数→{h}m"] = _fmt(
            ols_nw(y, np.c_[np.ones(len(df)), df["oni"], df[f"ne{h}"]]),
            ["const", "ONI", "NonEnergy"])
    # 剔除商品共同 β 后的"橡胶超额"回归
    df["ex_ne12"] = df["rss12"] - df["ne12"]
    regs["ONI→12m(剔商品β)"] = _fmt(
        ols_nw(df["ex_ne12"], np.c_[np.ones(len(df)), df["oni"]]), ["const", "ONI"])
    # 割胶季 6-10 月
    s = df[df["mon"].isin([6, 7, 8, 9, 10])]
    regs["ONI→12m(割胶季6-10月)"] = _fmt(
        ols_nw(s["rss12"], np.c_[np.ones(len(s)), s["oni"]]), ["const", "ONI"])
    # 分时期
    for era in ("1960-1999", "2000-2025"):
        e = df[df["era"] == era]
        regs[f"ONI→12m({era})"] = _fmt(
            ols_nw(e["rss12"], np.c_[np.ones(len(e)), e["oni"]]), ["const", "ONI"])
    # 同期：当月收益 ~ ΔONI / ONI 水平
    df["mret"] = np.log(df["RSS3"] / df["RSS3"].shift(1)) * 100
    df["doni"] = df["oni"].diff()
    regs["当月收益~ΔONI"] = _fmt(
        ols_nw(df["mret"], np.c_[np.ones(len(df)), df["doni"]]), ["const", "dONI"])
    # 中国 RU 主连（1997-2026，自身口径）
    ru = load_cn_daily("RU")
    ru_m = ru["close"].resample("MS").last().dropna()
    ru_m = ru_m[ru_m.index >= "1997-05-01"]
    ru12 = np.log(ru_m.shift(-12) / ru_m) * 100
    ruo = oni["anom"].reindex(ru_m.index)
    regs["RU主连 12m~ONI(1997-2026)"] = _fmt(
        ols_nw(ru12, np.c_[np.ones(len(ru_m)), ruo]), ["const", "ONI"])

    # ---------------- F. 期限扫描
    scan = []
    for h in range(0, 37, 3):
        yy = fwd(df["RSS3"], h)
        ok = pd.DataFrame({"y": yy, "o": df["oni"]}).dropna()
        if h == 0:
            ok = pd.DataFrame({"y": df["mret"], "o": df["oni"]}).dropna()
        if len(ok) > 30:
            r, p = stats.pearsonr(ok["o"], ok["y"])
            scan.append({"h": h, "r": round(float(r), 3), "p": round(float(p), 5),
                         "n": int(len(ok))})

    # ---------------- 当前状态
    cn = {}
    d0 = pd.Timestamp("2026-07-24")
    for code in ("RU", "BR", "NR"):
        d = load_cn_daily(code)
        up = d[d.index <= d0]
        cur = float(d["close"].iloc[-1])
        cn[code] = {"last_date": d.index[-1].strftime("%Y-%m-%d"), "close": cur,
                    "report_date_close": float(up["close"].iloc[-1]) if len(up) else None,
                    "chg_since_report_pct": round(cur / float(up["close"].iloc[-1]) * 100 - 100, 2)
                    if len(up) else None,
                    "high_since_report": float(d.loc[d.index > d0, "high"].max()) if len(d[d.index > d0]) else None,
                    "history_from": d.index[0].strftime("%Y-%m")}
        cn[code]["high_pct"] = round(cn[code]["high_since_report"] / cn[code]["report_date_close"] * 100 - 100, 2)

    res = {
        "meta": {"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                 "oni_latest": {"date": last_oni.name.strftime("%Y-%m"),
                                "season": last_oni["season"], "anom": float(last_oni["anom"])},
                 "oni_source": "NOAA CPC oni.ascii.txt",
                 "price_source": "World Bank Pink Sheet monthly (1960M01-2025M12)",
                 "primary_series": "Rubber RSS3 $/kg (1960-2025, 66y)",
                 "cn_source": "东方财富主连日线 data/rubber/",
                 "n_el": len(el), "n_la": len(la)},
        "oni_recent": [{"date": d.strftime("%Y-%m"), "anom": round(float(v), 2)}
                       for d, v in oni["anom"].tail(14).items()],
        "el_events": el, "la_events": la,
        "events_rss3": ev_rss, "events_rss3_nolookahead": ev_rss_nl,
        "events_tsr20": ev_tsr, "events_brent": ev_oil, "events_nonenergy": ev_ne,
        "la_events_rss3": la_rss,
        "baseline_uncond": {str(k): v for k, v in base.items()},
        "tier_summary": tiers, "state_summary": states,
        "excess_over_commodity_index": {"baseline_rel_ne12": round(b_ex, 1), "by_tier": ex_ne},
        "regressions": regs, "horizon_scan": scan, "cn_rubber": cn,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(_clean(res), f, ensure_ascii=False, indent=1)

    # ---------------- 打印
    print("\n=== 无条件基线（RSS3 月度对数收益 %，1960-2025）===")
    for h in HORIZONS:
        b = base[h]
        print(f"  T+{h:>2}m 均值 {b['mean']:+.2f}%  中位 {b['median']:+.2f}%  sd {b['sd']:.1f}  n={b['n']}")

    print("\n=== EN 事件（RSS3）===")
    for r in ev_rss:
        print(f"  {r['anchor']} {r['tier']:<3} peak{r['peak_abs']:>4} {r['len_m']:>2}m | "
              + " ".join(f"T+{h}:{r[f't{h}'] if r[f't{h}'] is not None else 'na':>6}" for h in HORIZONS))
    print(f"  (共 {len(el)} 次 EN 事件，RSS3 可得 {len(ev_rss)} 次；"
          f"无前视口径 {len(ev_rss_nl)} 次)")

    print("\n=== 分档汇总（超额 vs 无条件）===")
    for t in tiers:
        if not t.get("t12"):
            continue
        ln = f"  {t['label']:<8} n={t['n']:>2} |"
        for h in (6, 12, 24):
            v = t.get(f"t{h}")
            if v:
                ln += f" T+{h}:{v['mean']:>+6.1f}%(超{v['excess']:>+5.1f},p={v['p_welch']:.3f})"
        print(ln)

    print("\n=== ONI 状态（逐月，RSS3）===")
    for s in states:
        v = s.get("t12")
        if v:
            print(f"  {s['label']:<6} n={s['n']:>4} T+12m {v['mean']:+.1f}% 超额 {v['excess']:+.1f}% "
                  f"(p_welch={v['p_welch']:.4f}, p_MW={v['p_mw']:.4f})")

    print("\n=== 回归（因变量=未来H月 RSS3 对数收益 %）===")
    for k, v in regs.items():
        if v:
            print(f"  {k:<28} " + "  ".join(f"{n}={b:+.2f}(t={t:+.2f})"
                                            for n, b, t in zip(v["names"], v["b"], v["t"]))
                  + f"   R2={v['r2']:.3f} n={v['n']}")

    print("\n=== 期限扫描 corr(ONI_t, fwd_H) ===")
    print("  " + "  ".join(f"H={s['h']}:{s['r']:+.2f}" for s in scan))

    print(f"\n=== EN 窗口内 橡胶−商品指数(NonEnergy) T+12m 超额 "
          f"(全样本基线 {b_ex:+.1f}pp) ===")
    for e in ex_ne:
        print(f"  {e['label']:<8} n={e['n']:>2} 相对商品指数 {e['mean_rel_ne']:>+7.1f}pp "
              f"超额 {e['excess_over_baseline']:>+7.1f}pp  胜率 {e['win']}")

    print("\n=== 中国主连（vs 2026-07-24 周报发布日）===")
    print(" ", json.dumps(cn, ensure_ascii=False))


def _v(x):
    return None if pd.isna(x) else round(float(x), 1)


def _rnd(x):
    return x


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (isinstance(o, float) and np.isnan(o)) or np.isnan(o) else float(o)
    return o


if __name__ == "__main__":
    main()
