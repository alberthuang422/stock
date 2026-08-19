#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析：历史上 "US2Y 走弱（收益率下行）+ US10Y 走强（收益率上行）" 时期，KO/PM/MO 表现
口径说明：本脚本主口径 = 收益率口径：ΔUS2Y < 0 且 ΔUS10Y > 0（曲线陡峭化，短端降长端升）
另附反向口径 ΔUS2Y > 0 且 ΔUS10Y < 0（价格口径下的"2Y 弱 + 10Y 强"）作为对照。
"""
import pandas as pd
import numpy as np
import json, os

DATA = "/Users/alberthuang/Desktop/股票分析/data"
OUT = "/Users/alberthuang/Desktop/股票分析/results"

def load_yield(name):
    df = pd.read_csv(os.path.join(DATA, f"{name}.csv"), parse_dates=["observation_date"])
    df.columns = ["date", "y"]
    df = df.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df = df.dropna().reset_index(drop=True)
    return df

def load_stock(name):
    # data/<name>/<name>, 1D.csv（跳过旧的 BATS_ 前缀文件）
    import glob
    cands = [p for p in glob.glob(os.path.join(DATA, name, "*.csv"))
             if not os.path.basename(p).startswith("BATS_")]
    f = sorted(cands)[0]
    df = pd.read_csv(f, parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df

# ---------- 1. 数据 ----------
d2 = load_yield("dgs2")   # 1976-06 起
d10 = load_yield("dgs10") # 1962 起

# 月度序列：月末值（该月最后一个有数据的交易日）
def monthly_last(df):
    m = df.set_index("date")["y"].resample("ME").last().dropna()
    return m

m2 = monthly_last(d2)
m10 = monthly_last(d10)
monthly = pd.DataFrame({"y2": m2, "y10": m10}).dropna()
monthly["d2"] = monthly["y2"].diff()
monthly["d10"] = monthly["y10"].diff()
monthly = monthly.dropna()  # 1976-07 起
# 剔除 2026-08（未完整月，无月末值则自动剔除；若有则标记）
monthly = monthly[monthly.index <= "2026-07-31"]

stocks = {s: load_stock(s) for s in ["ko", "mo", "pm", "gspc", "xlp"]}

# 每个月的首/末交易日（用于区间收益）
def month_edges(df):
    df = df.copy()
    df["ym"] = df["date"].dt.to_period("M")
    first = df.groupby("ym")["date"].min()
    last = df.groupby("ym")["date"].max()
    return first, last

edges = {s: month_edges(stocks[s]) for s in stocks}

def ret_in_window(sym, start, end):
    """start/end 为 pd.Timestamp，返回 [start, end] 区间收盘收益"""
    df = stocks[sym]
    s = df[df["date"] >= start]
    if s.empty: return None
    a = s.iloc[0]["px"]
    e = df[df["date"] <= end]
    if e.empty: return None
    b = e.iloc[-1]["px"]
    if a <= 0 or b <= 0: return None
    return b / a - 1.0

def ret_over_period(sym, months):
    """months: list of Period('M')；收益 = 段首月首交易日 → 段末月最后交易日"""
    if not months: return None
    first, last = edges[sym]
    start = first.get(months[0])
    end = last.get(months[-1])
    if start is None or end is None: return None
    return ret_in_window(sym, start, end)

# ---------- 2. 时期识别 ----------
def find_episodes(cond, monthly_df):
    """cond: Series(bool) 按月的满足条件；连续 True 合并为时期（最少 1 个月）"""
    eps = []
    cur = []
    for i, idx in enumerate(monthly_df.index):
        if cond.iloc[i]:
            cur.append(idx)
        else:
            if cur:
                eps.append(cur); cur = []
    if cur: eps.append(cur)
    return eps

def describe_episode(months, monthly_df, label):
    sub = monthly_df.loc[months]
    start = months[0]
    end = months[-1]
    if len(months) == 1:
        # 单月时期：累计变化 = 该月环比变化
        y2_chg = sub.iloc[0]["d2"]
        y10_chg = sub.iloc[0]["d10"]
        y2_s = monthly_df.loc[start, "y2"] - y2_chg
        y10_s = monthly_df.loc[start, "y10"] - y10_chg
    else:
        y2_s = monthly_df.loc[start, "y2"]
        y2_e = monthly_df.loc[end, "y2"]
        y10_s = monthly_df.loc[start, "y10"]
        y10_e = monthly_df.loc[end, "y10"]
        y2_chg = y2_e - y2_s
        y10_chg = y10_e - y10_s
    y2_e = y2_s + y2_chg
    y10_e = y10_s + y10_chg
    return {
        "label": label,
        "start": str(start),
        "end": str(end),
        "months": len(months),
        "y2_chg": round(y2_chg * 100, 2),   # bp 变化（整段累计）
        "y10_chg": round(y10_chg * 100, 2),
        "slope_chg": round(((y10_e - y2_e) - (y10_s - y2_s)) * 100, 2),
        "y2_avg_monthly_chg": round(sub["d2"].mean() * 100, 2),
        "y10_avg_monthly_chg": round(sub["d10"].mean() * 100, 2),
    }

def build_table(cond, monthly_df, label):
    eps = find_episodes(cond, monthly_df)
    rows = []
    for i, months in enumerate(eps):
        base = describe_episode(months, monthly_df, f"{label}#{i+1}")
        for sym in ["ko", "mo", "pm", "gspc", "xlp"]:
            r = ret_over_period(sym, months)
            base[f"ret_{sym}"] = round(r * 100, 2) if r is not None else None
        for sym in ["ko", "mo", "pm"]:
            g = base.get("ret_gspc")
            r = base.get(f"ret_{sym}")
            if r is not None and g is not None:
                base[f"xs_{sym}"] = round(r - g, 2)
            else:
                base[f"xs_{sym}"] = None
        rows.append(base)
    return rows

# 主口径：Δ2Y < 0 且 Δ10Y > 0（收益率口径，宽松）
cond_loose = (monthly["d2"] < 0) & (monthly["d10"] > 0)
# 主口径（显著版）：Δ2Y ≤ -10bp 且 Δ10Y ≥ +10bp
cond_sig = (monthly["d2"] <= -0.10) & (monthly["d10"] >= 0.10)
# 主口径（强显著）：Δ2Y ≤ -20bp 且 Δ10Y ≥ +20bp
cond_strong = (monthly["d2"] <= -0.20) & (monthly["d10"] >= 0.20)
# 反向口径（价格口径的 2Y 弱 10Y 强）：Δ2Y > 0 且 Δ10Y < 0
cond_rev = (monthly["d2"] > 0) & (monthly["d10"] < 0)
# 反向显著
cond_rev_sig = (monthly["d2"] >= 0.10) & (monthly["d10"] <= -0.10)

t_loose = build_table(cond_loose, monthly, "STEEP_LOOSE")
t_sig = build_table(cond_sig, monthly, "STEEP_SIG")
t_strong = build_table(cond_strong, monthly, "STEEP_STRONG")
t_rev = build_table(cond_rev, monthly, "FLAT_REV")
t_rev_sig = build_table(cond_rev_sig, monthly, "FLAT_REV_SIG")

# ---------- 2b. 周频口径（补充，样本更多） ----------
def weekly_last(df):
    return df.set_index("date")["y"].resample("W-FRI").last().dropna()

w2 = weekly_last(d2)
w10 = weekly_last(d10)
weekly = pd.DataFrame({"y2": w2, "y10": w10}).dropna()
weekly["d2"] = weekly["y2"].diff()
weekly["d10"] = weekly["y10"].diff()
weekly = weekly.dropna()
weekly = weekly[weekly.index <= "2026-08-08"]

# 周窗口区间收益：段内第一个交易日至最后一个交易日（index 为周五日期）
def ret_over_weeks(sym, weeks):
    if not weeks: return None
    start = weeks[0] - pd.Timedelta(days=6)  # 段首周的起点下限
    end = weeks[-1]                          # 段末周周五
    df = stocks[sym]
    s = df[df["date"] >= start]
    if s.empty: return None
    a = s.iloc[0]["px"]
    e = df[df["date"] <= end]
    if e.empty: return None
    b = e.iloc[-1]["px"]
    if a <= 0 or b <= 0: return None
    return b / a - 1.0

def build_weekly_table(cond, weekly_df, label):
    eps = find_episodes(cond, weekly_df)
    rows = []
    for i, weeks in enumerate(eps):
        sub = weekly_df.loc[weeks]
        start, end = weeks[0], weeks[-1]
        if len(weeks) == 1:
            y2c, y10c = sub.iloc[0]["d2"], sub.iloc[0]["d10"]
        else:
            y2c = weekly_df.loc[end, "y2"] - weekly_df.loc[start, "y2"]
            y10c = weekly_df.loc[end, "y10"] - weekly_df.loc[start, "y10"]
        row = {
            "label": f"{label}#{i+1}",
            "start": str(start),
            "end": str(end),
            "weeks": len(weeks),
            "y2_chg": round(y2c * 100, 2),
            "y10_chg": round(y10c * 100, 2),
        }
        for sym in ["ko", "mo", "pm", "gspc", "xlp"]:
            r = ret_over_weeks(sym, weeks)
            row[f"ret_{sym}"] = round(r * 100, 2) if r is not None else None
        for sym in ["ko", "mo", "pm"]:
            g = row.get("ret_gspc"); r = row.get(f"ret_{sym}")
            row[f"xs_{sym}"] = round(r - g, 2) if (r is not None and g is not None) else None
        rows.append(row)
    return rows

w_loose = build_weekly_table((weekly["d2"] < 0) & (weekly["d10"] > 0), weekly, "W_LOOSE")
w_sig = build_weekly_table((weekly["d2"] <= -0.10) & (weekly["d10"] >= 0.10), weekly, "W_SIG")
w_sig15 = build_weekly_table((weekly["d2"] <= -0.15) & (weekly["d10"] >= 0.15), weekly, "W_SIG15")
w_rev = build_weekly_table((weekly["d2"] > 0) & (weekly["d10"] < 0), weekly, "W_REV")
w_rev_sig = build_weekly_table((weekly["d2"] >= 0.10) & (weekly["d10"] <= -0.10), weekly, "W_REV_SIG")

# ---------- 2c. 分档统计（月频宽松，按幅度） ----------
def bucket_stats(cond, monthly_df, sym, label):
    """按 2Y/10Y 幅度分档看 sym 收益"""
    eps = find_episodes(cond, monthly_df)
    out = {}
    buckets = {
        "B1_2Y深降_10Y显著升": lambda r: r["y2_chg"] <= -10 and r["y10_chg"] >= 10,
        "B2_2Y微降_10Y显著升": lambda r: r["y2_chg"] > -10 and r["y10_chg"] >= 10,
        "B3_2Y深降_10Y微升": lambda r: r["y2_chg"] <= -10 and r["y10_chg"] < 10,
        "B4_双向弱": lambda r: r["y2_chg"] > -10 and r["y10_chg"] < 10,
    }
    for bname, f in buckets.items():
        sel = [r for r in eps if f(describe_episode(r, monthly_df, label))]
        vals = []
        for r in sel:
            rv = ret_over_period(sym, r)
            if rv is not None: vals.append(rv)
        out[bname] = {
            "n": len(sel),
            "win_rate": round(np.mean([v > 0 for v in vals]) * 100, 1) if vals else None,
            "median": round(np.median(vals) * 100, 2) if vals else None,
            "mean": round(np.mean(vals) * 100, 2) if vals else None,
        }
    return out

bucket_ko = bucket_stats(cond_loose, monthly, "ko", "B")
bucket_mo = bucket_stats(cond_loose, monthly, "mo", "B")
bucket_pm = bucket_stats(cond_loose, monthly, "pm", "B")
bucket_gspc = bucket_stats(cond_loose, monthly, "gspc", "B")

# ---------- 3. 汇总统计 ----------
def summarize(rows, syms):
    n = len(rows)
    out = {"n_episodes": n}
    for sym in syms:
        vals = [r[f"ret_{sym}"] for r in rows if r.get(f"ret_{sym}") is not None]
        xsv = [r[f"xs_{sym}"] for r in rows if r.get(f"xs_{sym}") is not None]
        out[sym] = {
            "n": len(vals),
            "win_rate": round(np.mean([v > 0 for v in vals]) * 100, 1) if vals else None,
            "median": round(np.median(vals), 2) if vals else None,
            "mean": round(np.mean(vals), 2) if vals else None,
            "min": round(min(vals), 2) if vals else None,
            "max": round(max(vals), 2) if vals else None,
            "xs_median": round(np.median(xsv), 2) if xsv else None,
            "xs_win_rate": round(np.mean([v > 0 for v in xsv]) * 100, 1) if xsv else None,
        }
    return out

syms_all = ["ko", "mo", "pm", "gspc", "xlp"]
sum_loose = summarize(t_loose, syms_all)
sum_sig = summarize(t_sig, syms_all)
sum_strong = summarize(t_strong, syms_all)
sum_rev = summarize(t_rev, syms_all)
sum_rev_sig = summarize(t_rev_sig, syms_all)

# ---------- 4. 全样本基准（任意月份组合的表现）----------
# 随机/全月份基准：所有连续 k 个月窗口（k=1..12）的平均收益分布 → 用于对照
def baseline_stats(sym, max_k=12):
    df = stocks[sym]
    first, last = edges[sym]
    ym_list = [p for p in monthly.index if p in first.index and p in last.index]
    vals = []
    for k in range(1, max_k + 1):
        for i in range(len(ym_list) - k + 1):
            months = ym_list[i:i + k]
            r = ret_over_period(sym, months)
            if r is not None:
                vals.append((k, r))
    return vals

base_ko = baseline_stats("ko")
base_mo = baseline_stats("mo")
base_pm = baseline_stats("pm")
base_gspc = baseline_stats("gspc")

# 时期月度数量分布 vs 基准中位数（按时期长度匹配）
def period_baseline(sym, rows, base):
    """每个时期的收益 vs 同长度随机窗口收益分布的分位数"""
    out = []
    for r in rows:
        k = r["months"]
        same = [v for (kk, v) in base if kk == k]
        rv = r.get(f"ret_{sym}")
        if rv is None or not same:
            out.append(None)
            continue
        pct = np.mean([v < rv / 100 for v in same]) * 100
        out.append(round(pct, 1))
    return out

pct_ko = period_baseline("ko", t_sig, base_ko)
pct_mo = period_baseline("mo", t_sig, base_mo)
pct_pm = period_baseline("pm", t_sig, base_pm)

result = {
    "window": f"{monthly.index[0]} ~ {monthly.index[-1]}",
    "n_months": len(monthly),
    "cond_counts": {
        "loose": int(cond_loose.sum()),
        "sig": int(cond_sig.sum()),
        "strong": int(cond_strong.sum()),
        "rev": int(cond_rev.sum()),
        "rev_sig": int(cond_rev_sig.sum()),
    },
    "episodes": {
        "loose": t_loose,
        "sig": t_sig,
        "strong": t_strong,
        "rev": t_rev,
        "rev_sig": t_rev_sig,
    },
    "weekly_episodes": {
        "loose": w_loose,
        "sig": w_sig,
        "sig15": w_sig15,
        "rev": w_rev,
        "rev_sig": w_rev_sig,
    },
    "summary": {
        "loose": sum_loose,
        "sig": sum_sig,
        "strong": sum_strong,
        "rev": sum_rev,
        "rev_sig": sum_rev_sig,
    },
    "weekly_summary": {
        "loose": summarize(w_loose, syms_all),
        "sig": summarize(w_sig, syms_all),
        "sig15": summarize(w_sig15, syms_all),
        "rev": summarize(w_rev, syms_all),
        "rev_sig": summarize(w_rev_sig, syms_all),
    },
    "buckets": {
        "ko": bucket_ko,
        "mo": bucket_mo,
        "pm": bucket_pm,
        "gspc": bucket_gspc,
    },
    "baseline": {
        "ko_all_windows_median_by_k": {k: round(np.median([v for kk, v in base_ko if kk == k]) * 100, 2) for k in range(1, 13)},
        "mo_all_windows_median_by_k": {k: round(np.median([v for kk, v in base_mo if kk == k]) * 100, 2) for k in range(1, 13)},
        "pm_all_windows_median_by_k": {k: round(np.median([v for kk, v in base_pm if kk == k]) * 100, 2) for k in range(1, 13)},
        "gspc_all_windows_median_by_k": {k: round(np.median([v for kk, v in base_gspc if kk == k]) * 100, 2) for k in range(1, 13)},
    },
    "pctile_vs_baseline_sig": {
        "ko": pct_ko, "mo": pct_mo, "pm": pct_pm,
    },
}

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "steep_episodes.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)

# ---------- 控制台摘要 ----------
print(f"分析窗口: {result['window']} ({result['n_months']} 个月)")
print(f"满足月份数: 宽松(Δ2Y<0&Δ10Y>0)={result['cond_counts']['loose']}, 显著(±10bp)={result['cond_counts']['sig']}, 强(±20bp)={result['cond_counts']['strong']}")
print(f"反向(Δ2Y>0&Δ10Y<0)={result['cond_counts']['rev']}, 反向显著={result['cond_counts']['rev_sig']}")
print()
print("=== 月频宽松口径 时期全表（按 10Y 升幅排序） ===")
for r in sorted(t_loose, key=lambda x: x["y10_chg"], reverse=True):
    pm_s = r.get("ret_pm")
    print(f"  {r['start']} ~ {r['end']} ({r['months']}M) | 2Y {r['y2_chg']:+.0f}bp 10Y {r['y10_chg']:+.0f}bp | KO {r.get('ret_ko')}% MO {r.get('ret_mo')}% PM {pm_s}% GSPC {r.get('ret_gspc')}%")
print()
print("=== 月频显著(±10bp) 时期列表 ===")
for r in t_sig:
    pm_s = r.get("ret_pm")
    print(f"  {r['start']} ~ {r['end']} ({r['months']}M) | 2Y {r['y2_chg']:+.0f}bp 10Y {r['y10_chg']:+.0f}bp | KO {r.get('ret_ko')}% MO {r.get('ret_mo')}% PM {pm_s}% GSPC {r.get('ret_gspc')}%")
print()
print("=== 周频显著(±10bp) 时期（前 25） ===")
for r in sorted(w_sig, key=lambda x: x["y10_chg"] + x["y2_chg"].__abs__(), reverse=True)[:25]:
    print(f"  {r['start']} ~ {r['end']} ({r['weeks']}W) | 2Y {r['y2_chg']:+.0f}bp 10Y {r['y10_chg']:+.0f}bp | KO {r.get('ret_ko')}% MO {r.get('ret_mo')}% PM {r.get('ret_pm')}% GSPC {r.get('ret_gspc')}%")
print()
for k, v in result["summary"].items():
    print(f"[月频 {k}] n={v['n_episodes']}")
    for sym in ["ko", "mo", "pm", "gspc"]:
        s = v.get(sym)
        if s and s.get("n"):
            print(f"   {sym.upper():5s} 胜率{s['win_rate']}% 中位{s['median']}% 平均{s['mean']}% 超额中位{s['xs_median']}% 超额胜率{s['xs_win_rate']}%")
for k, v in result["weekly_summary"].items():
    print(f"[周频 {k}] n={v['n_episodes']}")
    for sym in ["ko", "mo", "pm", "gspc"]:
        s = v.get(sym)
        if s and s.get("n"):
            print(f"   {sym.upper():5s} 胜率{s['win_rate']}% 中位{s['median']}% 平均{s['mean']}% 超额中位{s['xs_median']}% 超额胜率{s['xs_win_rate']}%")
print()
print("=== 分档（月频宽松时期，按幅度） ===")
for bname in ["B1_2Y深降_10Y显著升", "B2_2Y微降_10Y显著升", "B3_2Y深降_10Y微升", "B4_双向弱"]:
    line = f"  {bname}: "
    for sym in ["ko", "mo", "pm", "gspc"]:
        b = result["buckets"][sym][bname]
        line += f"{sym.upper()} n{b['n']} 胜率{b['win_rate']}% 中位{b['median']}% | "
    print(line)
