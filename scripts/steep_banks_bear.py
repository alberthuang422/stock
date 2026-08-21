#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
熊陡专题：JPM/MS/BAC 在「熊陡」及「长端领涨型走阔」下的表现
口径：
  严格熊陡 = Δ2Y < 0 且 Δ10Y > 0（经典定义，37 个月）
  长端领涨 = Δslope > 0 且 Δ10Y > 0 且 Δ10Y >= Δ2Y（近似口径，含严格熊陡子集）
    子类A 严格熊陡：2Y 降 10Y 升
    子类B 2Y 平（|Δ2Y|<=5bp）10Y 升：长端单边走阔
    子类C 加息陡长端领涨：2Y 升 10Y 升更快
同时给出当前（2026-08-14）多窗口形态判定（近1/3/6/12月 2Y/10Y/slope 变化）
"""
import pandas as pd
import numpy as np
import json, os, glob

DATA = r"C:\Users\Administrator\Desktop\stock\data"
OUT = r"C:\Users\Administrator\Desktop\stock\results"
os.makedirs(OUT, exist_ok=True)

SYMS = ["jpm", "bac", "ms", "gs", "kre", "xlf", "gspc"]

def load_yield(name):
    df = pd.read_csv(os.path.join(DATA, f"{name}.csv"), parse_dates=["observation_date"])
    df.columns = ["date", "y"]
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    return df.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)

def load_stock(name):
    cands = [p for p in glob.glob(os.path.join(DATA, name, "*.csv"))
             if not os.path.basename(p).startswith("BATS_")]
    df = pd.read_csv(sorted(cands)[0], parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    return df[["date", col]].rename(columns={col: "px"}).dropna().sort_values("date").reset_index(drop=True)

d2 = load_yield("dgs2")
d10 = load_yield("dgs10")
stocks = {s: load_stock(s) for s in SYMS}

# ---------- 当前形态判定 ----------
daily = pd.merge(d2[["date", "y"]], d10[["date", "y"]], on="date", suffixes=("2", "10")).dropna()
daily["slope"] = daily["y10"] - daily["y2"]
now_state = []
for wd, name in [(21, "近1月"), (63, "近3月"), (126, "近6月"), (252, "近12月")]:
    w = daily.iloc[-wd - 1:]
    s, e = w.iloc[0], w.iloc[-1]
    d2c = (e["y2"] - s["y2"]) * 100
    d10c = (e["y10"] - s["y10"]) * 100
    sc = (e["slope"] - s["slope"]) * 100
    if d2c < 0 and d10c > 0: typ = "熊陡(2Y降10Y升)"
    elif d2c < 0 and d10c <= 0: typ = "牛陡(2Y降10Y降)"
    elif d2c > 0 and d10c > 0: typ = "加息陡(2Y升10Y升)"
    elif d2c <= 0 and d10c > 0: typ = "近似熊陡(2Y平/降10Y升)"
    else: typ = "其他/收窄"
    now_state.append({"window": name, "start": str(s["date"].date()), "end": str(e["date"].date()),
                      "d2_bp": round(d2c, 1), "d10_bp": round(d10c, 1),
                      "slope_bp": round(sc, 1), "type": typ})
now_state.append({"window": "当前点位", "end": str(daily.iloc[-1]["date"].date()),
                  "y2": daily.iloc[-1]["y2"], "y10": daily.iloc[-1]["y10"],
                  "slope_bp": round(daily.iloc[-1]["slope"] * 100, 1)})

# ---------- 月度 ----------
def monthly_last(df):
    return df.set_index("date")["y"].resample("ME").last().dropna()

m2 = monthly_last(d2)
m10 = monthly_last(d10)
monthly = pd.DataFrame({"y2": m2, "y10": m10}).dropna()
monthly["slope"] = monthly["y10"] - monthly["y2"]
monthly["dslope"] = monthly["slope"].diff()
monthly["d2"] = monthly["y2"].diff()
monthly["d10"] = monthly["y10"].diff()
monthly = monthly.dropna()
monthly["slope"] = monthly["y10"] - monthly["y2"]
monthly = monthly[monthly.index <= "2026-07-31"]

def month_edges(df):
    df = df.copy()
    df["ym"] = df["date"].dt.to_period("M")
    return df.groupby("ym")["date"].min(), df.groupby("ym")["date"].max()

edges = {s: month_edges(stocks[s]) for s in SYMS}

def ret_in_window(sym, start, end):
    df = stocks[sym]
    s = df[df["date"] >= start]
    if s.empty: return None
    e = df[df["date"] <= end]
    if e.empty: return None
    a, b = s.iloc[0]["px"], e.iloc[-1]["px"]
    if a <= 0 or b <= 0: return None
    return b / a - 1.0

def ret_over_period(sym, months):
    if not months: return None
    if sym == "bank3":
        vals = [ret_over_period(s, months) for s in ["jpm", "bac", "ms"]]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None
    first, last = edges[sym]
    start, end = first.get(months[0]), last.get(months[-1])
    if start is None or end is None: return None
    return ret_in_window(sym, start, end)

def find_episodes(cond):
    eps, cur = [], []
    for i, idx in enumerate(monthly.index):
        if cond.iloc[i]: cur.append(idx)
        else:
            if cur: eps.append(cur); cur = []
    if cur: eps.append(cur)
    return eps

def classify(y2c, y10c):
    if y2c < 0 and y10c > 0: return "熊陡(2Y降10Y升)"
    if y2c < 0 and y10c <= 0: return "牛陡(2Y降10Y降)"
    return "加息陡(2Y升10Y升)"

def single_month_stats(mask, syms=("jpm", "bac", "ms", "bank3", "gspc")):
    out = {}
    idxs = monthly.index[mask]
    for sym in syms:
        vals, xs = [], []
        for idx in idxs:
            r = ret_over_period(sym, [idx])
            if r is None: continue
            vals.append(r)
            g = ret_over_period("gspc", [idx])
            if sym != "gspc" and g is not None: xs.append(r - g)
        v = np.array(vals)
        if not len(v): out[sym] = None; continue
        d = {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1),
             "median": round(np.median(v) * 100, 2), "mean": round(np.mean(v) * 100, 2)}
        if xs:
            d["xs_median"] = round(np.median(xs) * 100, 2)
            d["xs_win_rate"] = round(np.mean(np.array(xs) > 0) * 100, 1)
        out[sym] = d
    return out

# 严格熊陡 & 长端领涨（月度）
m_bear = (monthly["d2"] < 0) & (monthly["d10"] > 0)                       # 严格熊陡
m_lead = (monthly["dslope"] > 0) & (monthly["d10"] > 0) & (monthly["d10"] >= monthly["d2"])  # 长端领涨
m_leadA = m_lead & (monthly["d2"] < 0)                                     # A 严格熊陡
m_leadB = m_lead & (monthly["d2"].abs() <= 0.05) & (monthly["d2"] >= 0)    # B 2Y平
m_leadC = m_lead & (monthly["d2"] > 0.05)                                  # C 加息陡长端领涨

stat_bear = single_month_stats(m_bear)
stat_lead = single_month_stats(m_lead)
stat_A = single_month_stats(m_leadA)
stat_B = single_month_stats(m_leadB)
stat_C = single_month_stats(m_leadC)

# 熊陡月份明细（年份分布 + 每月）
bear_month_rows = []
for i, idx in enumerate(monthly.index):
    if m_bear.iloc[i]:
        r = ret_over_period("bank3", [idx])
        g = ret_over_period("gspc", [idx])
        bear_month_rows.append({
            "month": str(idx)[:7], "y2_chg": round(monthly.loc[idx, "d2"] * 100, 1),
            "y10_chg": round(monthly.loc[idx, "d10"] * 100, 1),
            "slope_chg": round(monthly.loc[idx, "dslope"] * 100, 1),
            "bank3": round(r * 100, 2) if r is not None else None,
            "gspc": round(g * 100, 2) if g is not None else None,
        })

# B 子类（2Y 平 + 10Y 升）月份明细——当前最接近的形态
leadB_month_rows = []
for i, idx in enumerate(monthly.index):
    if m_leadB.iloc[i]:
        r = ret_over_period("bank3", [idx])
        g = ret_over_period("gspc", [idx])
        leadB_month_rows.append({
            "month": str(idx)[:7], "y2_chg": round(monthly.loc[idx, "d2"] * 100, 1),
            "y10_chg": round(monthly.loc[idx, "d10"] * 100, 1),
            "slope_chg": round(monthly.loc[idx, "dslope"] * 100, 1),
            "bank3": round(r * 100, 2) if r is not None else None,
            "gspc": round(g * 100, 2) if g is not None else None,
        })

# 时期口径（严格熊陡 & 长端领涨）
def describe_episode(months):
    sub = monthly.loc[months]
    start, end = months[0], months[-1]
    if len(months) == 1:
        y2c, y10c = sub.iloc[0]["d2"], sub.iloc[0]["d10"]
    else:
        y2c = monthly.loc[end, "y2"] - monthly.loc[start, "y2"]
        y10c = monthly.loc[end, "y10"] - monthly.loc[start, "y10"]
    row = {"start": str(start)[:7], "end": str(end)[:7], "months": len(months),
           "y2_chg": round(y2c * 100, 1), "y10_chg": round(y10c * 100, 1),
           "slope_chg": round((y10c - y2c) * 100, 1), "type": classify(y2c, y10c)}
    for sym in SYMS:
        r = ret_over_period(sym, months)
        row[f"ret_{sym}"] = round(r * 100, 2) if r is not None else None
    vals = [row[f"ret_{s}"] for s in ["jpm", "bac", "ms"] if row.get(f"ret_{s}") is not None]
    row["ret_bank3"] = round(np.mean(vals), 2) if vals else None
    g = row.get("ret_gspc")
    if row.get("ret_bank3") is not None and g is not None:
        row["xs_bank3"] = round(row["ret_bank3"] - g, 2)
    return row

ep_bear = [describe_episode(m) for m in find_episodes(m_bear)]
ep_lead = [describe_episode(m) for m in find_episodes(m_lead)]

# ---------- 周频（长端领涨） ----------
def weekly_last(df):
    return df.set_index("date")["y"].resample("W-FRI").last().dropna()

w2 = weekly_last(d2)
w10 = weekly_last(d10)
weekly = pd.DataFrame({"y2": w2, "y10": w10}).dropna()
weekly["slope"] = weekly["y10"] - weekly["y2"]
weekly["dslope"] = weekly["slope"].diff()
weekly["d2"] = weekly["y2"].diff()
weekly["d10"] = weekly["y10"].diff()
weekly = weekly.dropna()
weekly = weekly[weekly.index <= "2026-08-08"]

def ret_over_weeks(sym, weeks):
    if not weeks: return None
    if sym == "bank3":
        vals = [ret_over_weeks(s, weeks) for s in ["jpm", "bac", "ms"]]
        vals = [v for v in vals if v is not None]
        return float(np.mean(vals)) if vals else None
    start = weeks[0] - pd.Timedelta(days=6)
    end = weeks[-1]
    df = stocks[sym]
    s = df[df["date"] >= start]
    if s.empty: return None
    e = df[df["date"] <= end]
    if e.empty: return None
    a, b = s.iloc[0]["px"], e.iloc[-1]["px"]
    if a <= 0 or b <= 0: return None
    return b / a - 1.0

def weekly_cond_stats(mask, syms=("jpm", "bac", "ms", "bank3", "gspc")):
    out = {}
    idxs = weekly.index[mask]
    for sym in syms:
        vals, xs = [], []
        for idx in idxs:
            r = ret_over_weeks(sym, [idx])
            if r is None: continue
            vals.append(r)
            g = ret_over_weeks("gspc", [idx])
            if sym != "gspc" and g is not None: xs.append(r - g)
        v = np.array(vals)
        if not len(v): out[sym] = None; continue
        d = {"n": int(len(v)), "win_rate": round(np.mean(v > 0) * 100, 1),
             "median": round(np.median(v) * 100, 2), "mean": round(np.mean(v) * 100, 2)}
        if xs:
            d["xs_median"] = round(np.median(xs) * 100, 2)
        out[sym] = d
    return out

w_bear = (weekly["d2"] < 0) & (weekly["d10"] > 0)
w_lead = (weekly["dslope"] > 0) & (weekly["d10"] > 0) & (weekly["d10"] >= weekly["d2"])
w_lead_sig = w_lead & (weekly["d10"] >= 0.10)  # 10Y 升≥10bp/周 的长端领涨
wstat_bear = weekly_cond_stats(w_bear)
wstat_lead = weekly_cond_stats(w_lead)
wstat_lead_sig = weekly_cond_stats(w_lead_sig)

# ---------- 长端领涨期后持有 ----------
def forward_ret(sym, anchor_date):
    df = stocks[sym]
    s = df[df["date"] <= anchor_date]
    if s.empty: return None
    a = s.iloc[-1]["px"]
    out = {}
    for k, tag in [(3, "m3"), (6, "m6"), (12, "m12")]:
        end = anchor_date + pd.DateOffset(months=k)
        e = df[(df["date"] > anchor_date) & (df["date"] <= end)]
        if e.empty: out[tag] = None; continue
        out[tag] = round((e.iloc[-1]["px"] / a - 1) * 100, 2)
    return out

def fwd_summary(rows, tag):
    out = {}
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        vals = [r[sym][tag] for r in rows if r.get(sym) and r[sym].get(tag) is not None]
        if not vals: out[sym] = None; continue
        out[sym] = {"n": len(vals), "win_rate": round(np.mean([v > 0 for v in vals]) * 100, 1),
                    "median": round(np.median(vals), 2), "mean": round(np.mean(vals), 2)}
    return out

fwd_rows = []
for e in ep_lead:
    last = edges["jpm"][1]
    anchor = last.get(pd.Period(e["end"], "M"))
    if anchor is None: continue
    row = {"label": f"{e['start']}~{e['end']}", "slope_chg": e["slope_chg"]}
    for sym in ["jpm", "bac", "ms", "bank3", "gspc"]:
        if sym == "bank3":
            parts = [forward_ret(s, anchor) for s in ["jpm", "bac", "ms"]]
            parts = [p for p in parts if p]
            fv = {}
            if parts:
                for tag in ["m3", "m6", "m12"]:
                    vals = [p[tag] for p in parts if p.get(tag) is not None]
                    fv[tag] = round(np.mean(vals), 2) if vals else None
            row[sym] = fv
        else:
            row[sym] = forward_ret(sym, anchor)
    fwd_rows.append(row)

# ---------- 案例（日频） ----------
CASES = [
    ("c1998", "1998-10-01", "1998-10-31", "1998-10 · LTCM 后严格熊陡（2Y -18bp / 10Y +20bp）"),
    ("c2013", "2013-05-01", "2013-09-30", "2013-05~09 · Taper 长端领涨（10Y +120bp）"),
    ("c2016", "2016-11-01", "2016-12-30", "2016-11~12 · Trump 交易长端领涨"),
    ("c2021", "2021-01-01", "2021-03-31", "2021-01~03 · Reflation 长端领涨"),
    ("c2024", "2024-09-01", "2024-12-31", "2024-09~12 · 降息+长端反弹"),
    ("c2020", "2020-02-01", "2020-05-31", "对照·2020-02~05 危机牛陡（2Y 崩）"),
]

def case_daily(cid, start, end, label):
    d2w = d2[(d2["date"] >= start) & (d2["date"] <= end)]
    d10w = d10[(d10["date"] >= start) & (d10["date"] <= end)]
    merged = pd.merge(d2w[["date", "y"]], d10w[["date", "y"]], on="date", suffixes=("2", "10")).dropna()
    dates = [str(d)[:10] for d in merged["date"]]
    y2v = [round(v, 3) for v in merged["y2"]]
    y10v = [round(v, 3) for v in merged["y10"]]
    slope_v = [round(a - b, 3) for a, b in zip(y10v, y2v)]
    rets, ret_dates = {}, dates
    for sym in ["jpm", "bac", "ms", "kre", "gspc"]:
        df = stocks[sym]
        w = df[(df["date"] >= start) & (df["date"] <= end)].copy()
        if w.empty: rets[sym] = None; continue
        b0 = w.iloc[0]["px"]
        rets[sym] = [round((p / b0 - 1) * 100, 2) for p in w["px"]]
        ret_dates = [str(d)[:10] for d in w["date"]]
    sl = (y10v[-1] - y2v[-1] - (y10v[0] - y2v[0])) * 100
    return {"id": cid, "label": label, "dates": dates, "y2": y2v, "y10": y10v,
            "slope": slope_v, "slope_chg_bp": round(sl, 1), "ret_dates": ret_dates, "rets": rets}

cases = [case_daily(cid, s, e, lbl) for cid, s, e, lbl in CASES]

case_summary = []
for c in cases:
    s, e = c["dates"][0], c["dates"][-1]
    row = {"label": c["label"], "slope_chg": c["slope_chg_bp"]}
    for sym in ["jpm", "bac", "ms", "kre", "gspc"]:
        df = stocks[sym]
        w = df[(df["date"] >= s) & (df["date"] <= e)]
        row[sym] = round((w.iloc[-1]["px"] / w.iloc[0]["px"] - 1) * 100, 2) if not w.empty else None
    vals = [row[s] for s in ["jpm", "bac", "ms"] if row.get(s) is not None]
    row["bank3"] = round(np.mean(vals), 2) if vals else None
    case_summary.append(row)

# ---------- 输出 ----------
result = {
    "now_state": now_state,
    "monthly_window": f"{monthly.index[0]} ~ {monthly.index[-1]}",
    "cond_counts": {
        "bear_strict": int(m_bear.sum()),
        "lead_total": int(m_lead.sum()),
        "lead_A_strict": int(m_leadA.sum()),
        "lead_B_flat2y": int(m_leadB.sum()),
        "lead_C_riserate": int(m_leadC.sum()),
    },
    "stats": {
        "bear_strict": stat_bear, "lead_total": stat_lead,
        "lead_A": stat_A, "lead_B": stat_B, "lead_C": stat_C,
    },
    "bear_month_rows": bear_month_rows,
    "leadB_month_rows": leadB_month_rows,
    "episodes": {"bear": ep_bear, "lead": ep_lead},
    "weekly": {
        "cond_counts": {"bear": int(w_bear.sum()), "lead": int(w_lead.sum()), "lead_sig10": int(w_lead_sig.sum())},
        "stats": {"bear": wstat_bear, "lead": wstat_lead, "lead_sig10": wstat_lead_sig},
    },
    "forward": {"rows": fwd_rows, "m3": fwd_summary(fwd_rows, "m3"),
                "m6": fwd_summary(fwd_rows, "m6"), "m12": fwd_summary(fwd_rows, "m12")},
    "cases": cases,
    "case_summary": case_summary,
}

with open(os.path.join(OUT, "steep_banks_bear.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)

# 控制台摘要
print("=== 当前形态判定 ===")
for s in now_state:
    if "type" in s:
        print(f"  {s['window']} ({s['start']}~{s['end']}): 2Y {s['d2_bp']:+.0f}bp 10Y {s['d10_bp']:+.0f}bp slope {s['slope_bp']:+.0f}bp => {s['type']}")
    else:
        print(f"  {s['window']}: 2Y {s['y2']}% 10Y {s['y10']}% slope {s['slope_bp']}bp")
print()
cc = result["cond_counts"]
print(f"月频: 严格熊陡 {cc['bear_strict']}月 | 长端领涨合计 {cc['lead_total']}月 (A严格熊陡 {cc['lead_A_strict']} / B 2Y平 {cc['lead_B_flat2y']} / C加息陡长端领涨 {cc['lead_C_riserate']})")
for k, name in [("bear_strict", "严格熊陡"), ("lead_total", "长端领涨合计"), ("lead_A", "A严格熊陡"), ("lead_B", "B 2Y平"), ("lead_C", "C加息陡长端领涨")]:
    st = result["stats"][k]
    if st.get("bank3"):
        b = st["bank3"]
        print(f"  [{name}] n={b['n']}月 bank3 中位{b['median']}% 胜率{b['win_rate']}% 超额{b.get('xs_median')}pp | SPY {st['gspc']['median']}%")
print()
print("=== 严格熊陡月份明细（全部） ===")
for r in bear_month_rows:
    print(f"  {r['month']}: 2Y {r['y2_chg']:+.0f} 10Y {r['y10_chg']:+.0f} | bank3 {r['bank3']}% SPY {r['gspc']}%")
print()
print("=== B子类（2Y平+10Y升）月份明细 ===")
for r in leadB_month_rows:
    print(f"  {r['month']}: 2Y {r['y2_chg']:+.0f} 10Y {r['y10_chg']:+.0f} slope {r['slope_chg']:+.0f} | bank3 {r['bank3']}% SPY {r['gspc']}%")
print()
print("=== 周频 ===")
for k, name in [("bear", "严格熊陡"), ("lead", "长端领涨"), ("lead_sig10", "长端领涨10Y≥10bp/周")]:
    st = result["weekly"]["stats"][k]
    if st.get("bank3"):
        b = st["bank3"]
        print(f"  [{name}] n={b['n']}周 bank3 中位{b['median']}% 胜率{b['win_rate']}% | SPY {st['gspc']['median']}%")
print()
print("=== 长端领涨期后持有 ===")
for tag, nm in [("m3", "后3月"), ("m6", "后6月"), ("m12", "后12月")]:
    s = result["forward"][tag]
    if s and s.get("bank3"):
        print(f"  {nm}: bank3 中位 {s['bank3']['median']}% 胜率 {s['bank3']['win_rate']}% | SPY {s['gspc']['median']}%")
print()
print("=== 案例 ===")
for c in case_summary:
    print(f"  {c['label'][:36]}: slope {c['slope_chg']:+.0f}bp | BK3 {c['bank3']}% JPM {c['jpm']}% BAC {c['bac']}% MS {c['ms']}% KRE {c['kre']}% SPY {c['gspc']}%")
print()
print("JSON saved:", os.path.join(OUT, "steep_banks_bear.json"))
