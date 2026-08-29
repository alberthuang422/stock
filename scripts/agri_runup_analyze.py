# -*- coding: utf-8 -*-
"""
El Niño 全事件分档 + 窗口内路径四指标分析（重做版，覆盖 22 次 El Niño 全部有数据部分）
指标（对每事件×标的，T+24 逐月累计超额路径 vs SPY）：
  1. max_excess : 窗口内最大累计超额（pp）—— run-up 峰值
  2. end_excess : 最终累计超额（pp，T+24，另附 T+12 期末值便于与旧口径衔接）
  3. peak_t     : 最大超额发生的 T+N（onset 后第 N 个月，1=onset 月）
  4. dd_start_t : 回撤起始 T+N —— 见顶后首个累计超额 < 峰值−5pp 的月份；全程未跌破=null（未显著回撤）
分档：弱 El Niño（峰值 ONI < +1.5）/ 强（+1.5 ≤ peak < +2.0）/ 超强（≥ +2.0）
输出 results/agri_runup.json（含事件级汇总、标的级汇总、三档汇总、全明细 events_detail 带 path）
"""
import json
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "agri_runup.json")

TICKERS = ["DE", "AGCO", "MOS", "CF", "NTR", "CTVA", "FMC", "ADM", "BG",
           "DAR", "FPI", "TSN", "HRL", "MOO", "DBA"]
SUB = {"DE": "农机", "AGCO": "农机", "MOS": "化肥", "CF": "化肥", "NTR": "化肥",
       "ADM": "粮商", "BG": "粮商", "CTVA": "种子植保", "FMC": "种子植保",
       "DAR": "油脂加工", "FPI": "农业REIT", "TSN": "肉类", "HRL": "肉类",
       "MOO": "农业ETF", "DBA": "商品ETF"}

DD_TOL = 5.0      # 回撤起始判定容差（pp）：见顶后跌破 峰值−5pp 即算开始回撤
WINDOW = 24       # 路径窗口（T+24）

# ---------- 1. ONI 解析 ----------
seas_to_mon = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
               "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
oni_rows = []
with open(os.path.join(DATA, "agri", "raw", "oni.txt"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("SEAS"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            seas, yr, anom = parts[0], int(parts[1]), float(parts[3])
        except (ValueError, IndexError):
            continue
        mon = seas_to_mon.get(seas)
        if mon is not None:
            oni_rows.append({"year": int(yr), "month": int(mon), "oni": float(anom)})
oni = pd.DataFrame(oni_rows).sort_values(["year", "month"]).reset_index(drop=True)
oni = oni[(oni["year"] >= 1950) & oni["oni"].notna()].copy()
oni["ym"] = oni["year"].astype(int) * 100 + oni["month"].astype(int)
oni_val = dict(zip(oni["ym"], oni["oni"]))

def el_events():
    vals = {int(k): float(v) for k, v in oni_val.items()}
    yms = sorted(vals.keys())
    evs = []
    i = 0
    n = len(yms)
    while i < n:
        if vals[yms[i]] >= 0.5:
            j = i
            while j < n and vals[yms[j]] >= 0.5:
                j += 1
            if j - i >= 5:
                evs.append({
                    "onset": int(yms[i]), "end": int(yms[j - 1]),
                    "peak": max(vals[yms[k]] for k in range(i, j)),
                    "len": j - i,
                    "peak_ym": int(yms[i + int(np.argmax([vals[yms[k]] for k in range(i, j)]))]),
                })
            i = j
        else:
            i += 1
    return evs

events = el_events()

def tier(peak):
    if peak >= 2.0:
        return "vstrong"
    if peak >= 1.5:
        return "strong"
    return "weak"

def ym_to_label(ym):
    return f"{int(ym) // 100}-{int(ym) % 100:02d}"

# ---------- 2. 月度收益 ----------
def monthly_df(ticker):
    path = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    m = df["adj_close"].resample("ME").last().dropna()
    ret = m.pct_change().dropna() * 100
    r = pd.DataFrame({"ret": ret})
    r["ym"] = r.index.year.astype(int) * 100 + r.index.month.astype(int)
    return r

mrets = {t: monthly_df(t) for t in TICKERS}
mrets["SPY"] = monthly_df("SPY")

# ---------- 3. 逐月累计收益路径（onset 起 WINDOW 个月） ----------
def window_path(ticker, onset_ym, months):
    df = mrets[ticker]
    cy = int(onset_ym)
    if cy not in set(df["ym"]):
        return None
    yy, mm = divmod(cy, 100)
    for _ in range(months):
        mm += 1
        if mm > 12:
            mm, yy = 1, yy + 1
    end_ym = yy * 100 + mm
    sub = df[(df["ym"] >= cy) & (df["ym"] < end_ym)]["ret"]
    if len(sub) < max(2, months - 2):
        return None
    acc = 1.0
    path = []
    for r in sub:
        acc *= (1 + r / 100.0)
        path.append((acc - 1) * 100)
    return path

def path_metrics(ticker, onset_ym, months):
    """返回窗口内路径四指标字典（含 T+12 期末供衔接）。"""
    pt = window_path(ticker, onset_ym, months)
    ps = window_path("SPY", onset_ym, months)
    if pt is None or ps is None:
        return None
    n = min(len(pt), len(ps))
    if n < max(2, months - 2):
        return None
    ex = [pt[i] - ps[i] for i in range(n)]
    peak = max(ex)
    pidx = int(np.argmax(ex))
    peak_t = pidx + 1
    # 回撤起始：见顶后首个 < 峰值−5pp 的月份
    dd_start_t = None
    for k in range(pidx + 1, n):
        if ex[k] < peak - DD_TOL:
            dd_start_t = k + 1
            break
    # T+12 期末值（若窗口覆盖）
    end12 = None
    if n >= 12:
        end12 = ex[11]
    return {"n_m": n,
            "max_excess": round(peak, 1),
            "peak_t": peak_t,
            "dd_start_t": dd_start_t,
            "end_excess": round(ex[-1], 1),
            "end_excess12": round(end12, 1) if end12 is not None else None,
            "dd": round(peak - ex[-1], 1),
            "path": [round(x, 1) for x in ex]}

# ---------- 4. 逐事件计算 ----------
ev_records = []
for e in events:
    rec = {"onset": ym_to_label(e["onset"]), "end": ym_to_label(e["end"]),
           "oni_peak": round(e["peak"], 2), "len_m": e["len"],
           "tier": tier(e["peak"]), "tickers": {}}
    for t in TICKERS:
        st = path_metrics(t, e["onset"], WINDOW)
        if st:
            rec["tickers"][t] = st
    ev_records.append(rec)

# ---------- 5. 事件级汇总（有数据标的） ----------
ev_summary = []
for r in ev_records:
    ts = r["tickers"]
    if not ts:
        ev_summary.append({"onset": r["onset"], "oni_peak": r["oni_peak"], "tier": r["tier"], "n": 0})
        continue
    vals = list(ts.values())
    n = len(vals)
    ev_summary.append({
        "onset": r["onset"], "oni_peak": r["oni_peak"], "tier": r["tier"], "n": n,
        "avg_max": round(float(np.mean([v["max_excess"] for v in vals])), 1),
        "avg_end": round(float(np.mean([v["end_excess"] for v in vals])), 1),
        "avg_dd": round(float(np.mean([v["dd"] for v in vals])), 1),
        "avg_peak_t": round(float(np.mean([v["peak_t"] for v in vals])), 1),
        "n_updown": int(sum(1 for v in vals if v["max_excess"] > 0 and v["end_excess"] < 0)),
        "n_alldown": int(sum(1 for v in vals if v["max_excess"] <= 0)),
    })

# ---------- 6. 标的级汇总（按档合并） ----------
by_ticker_tier = {}
for t in TICKERS:
    by_ticker_tier[t] = {}
    for tr in ("weak", "strong", "vstrong", "all"):
        rows = []
        for r in ev_records:
            if tr != "all" and r["tier"] != tr:
                continue
            if t in r["tickers"]:
                rows.append({**r["tickers"][t], "onset": r["onset"], "oni_peak": r["oni_peak"], "tier": r["tier"]})
        if not rows:
            by_ticker_tier[t][tr] = None
            continue
        by_ticker_tier[t][tr] = {
            "sub": SUB[t], "n": len(rows),
            "avg_max": round(float(np.mean([x["max_excess"] for x in rows])), 1),
            "avg_end": round(float(np.mean([x["end_excess"] for x in rows])), 1),
            "avg_end12": round(float(np.mean([x["end_excess12"] for x in rows if x.get("end_excess12") is not None])), 1)
            if any(x.get("end_excess12") is not None for x in rows) else None,
            "avg_dd": round(float(np.mean([x["dd"] for x in rows])), 1),
            "avg_peak_t": round(float(np.mean([x["peak_t"] for x in rows])), 1),
            "avg_dd_start": round(float(np.mean([x["dd_start_t"] for x in rows if x.get("dd_start_t") is not None])), 1)
            if any(x.get("dd_start_t") is not None for x in rows) else None,
            "n_dd_trig": int(sum(1 for x in rows if x.get("dd_start_t") is not None)),
            "n_updown": int(sum(1 for x in rows if x["max_excess"] > 0 and x["end_excess"] < 0)),
            "n_alldown": int(sum(1 for x in rows if x["max_excess"] <= 0)),
            "cases": [{"onset": x["onset"], "oni_peak": x["oni_peak"], "tier": x["tier"],
                       "max": x["max_excess"], "peak_t": x["peak_t"],
                       "dd_start": x["dd_start_t"], "end": x["end_excess"], "end12": x["end_excess12"]}
                      for x in rows],
        }

# ---------- 7. 分档汇总（跨标的 × 事件样本） ----------
tier_summary = []
for tr, tr_cn in (("weak", "弱厄尔尼诺(<+1.5°C)"), ("strong", "强厄尔尼诺(1.5~2.0°)"),
                  ("vstrong", "超强厄尔尼诺(≥2.0°C)")):
    rows = []
    for r in ev_records:
        if r["tier"] != tr:
            continue
        rows += list(r["tickers"].values())
    tier_summary.append({
        "tier": tr, "tier_cn": tr_cn,
        "n_ev": sum(1 for r in ev_records if r["tier"] == tr),
        "n_ev_data": len(set(x["onset"] for r in ev_records if r["tier"] == tr and r["tickers"] for x in [r])),
        "n_samples": len(rows),
        "avg_max": round(float(np.mean([x["max_excess"] for x in rows])), 1) if rows else None,
        "med_max": round(float(np.median([x["max_excess"] for x in rows])), 1) if rows else None,
        "avg_end": round(float(np.mean([x["end_excess"] for x in rows])), 1) if rows else None,
        "med_end": round(float(np.median([x["end_excess"] for x in rows])), 1) if rows else None,
        "avg_dd": round(float(np.mean([x["dd"] for x in rows])), 1) if rows else None,
        "avg_peak_t": round(float(np.mean([x["peak_t"] for x in rows])), 1) if rows else None,
        "avg_dd_start": round(float(np.mean([x["dd_start_t"] for x in rows if x.get("dd_start_t") is not None])), 1)
        if rows and any(x.get("dd_start_t") is not None for x in rows) else None,
        "n_updown_pct": round(float(np.mean([x["max_excess"] > 0 and x["end_excess"] < 0 for x in rows])) * 100, 0) if rows else None,
        "n_alldown_pct": round(float(np.mean([x["max_excess"] <= 0 for x in rows])) * 100, 0) if rows else None,
    })

# ---------- 8. 输出 ----------
out = {
    "meta": {"window_months": WINDOW, "dd_tol_pp": DD_TOL,
             "note": "超额路径 = 标的逐月复利累计收益 − SPY 同期（pp）；max_excess=T+24 窗口内最大累计超额；peak_t=见顶月(1=onset月)；dd_start_t=见顶后首个跌破 峰值−5pp 的月份(未跌破=null)；end_excess=T+24 期末；end_excess12=T+12 期末"},
    "tier_summary": tier_summary,
    "event_summary": ev_summary,
    "by_ticker_tier": by_ticker_tier,
    "events_detail": ev_records,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT, os.path.getsize(OUT), "bytes")
print("事件:", len(events), "| weak:", sum(1 for e in events if tier(e["peak"]) == "weak"),
      "| strong:", sum(1 for e in events if tier(e["peak"]) == "strong"),
      "| vstrong:", sum(1 for e in events if tier(e["peak"]) == "vstrong"))
print("\n== 分档汇总 ==")
for ts in tier_summary:
    print(f"  {ts['tier']:8s} 事件{ts['n_ev']}次(有数据{ts['n_ev_data']}) 样本{ts['n_samples']} | "
          f"avg_max={ts['avg_max']} avg_end={ts['avg_end']} avg_dd={ts['avg_dd']} "
          f"avg_peak_t=T+{ts['avg_peak_t']} avg_dd_start=T+{ts['avg_dd_start']} "
          f"冲高转负{ts['n_updown_pct']}% 全程阴跌{ts['n_alldown_pct']}%")
print("\n== 有数据事件明细 ==")
for s in ev_summary:
    if s["n"] == 0:
        continue
    print(f"  {s['onset']} ({s['tier']:8s} ONI {s['oni_peak']}): n={s['n']} avg_max={s['avg_max']} "
          f"avg_end={s['avg_end']} avg_peak_t=T+{s['avg_peak_t']} 冲高转负 {s['n_updown']}/{s['n']}")