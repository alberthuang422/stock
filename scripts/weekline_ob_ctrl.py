# -*- coding: utf-8 -*-
"""
对照与灵敏度分析：
1) 对照组 = 普通强势周 (周线 hist>=0 且非转正周) 内首次 4h RSI>=70 → 同样统计调整深度
   → 回答：转正周的超买 vs 普通强势周的超买，调整深度有无差异
2) RSI 阈值灵敏度 65 / 70 / 75
3) 当前状态（2026-08-20 收盘）：周线 hist / 4h RSI / 距最近转正
4) 超买在周内出现时点（周一第几根）
"""
import pandas as pd
import numpy as np
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)

def load_tencent_240(ticker):
    p = os.path.join(os.path.dirname(__file__), "..", "data", ticker, f"{ticker}_240_tencent.csv")
    df = pd.read_csv(p)
    df = df.rename(columns={"time": "time", "open": "open", "high": "high", "low": "low",
                            "close": "close", "Volume": "volume", "Histogram": "hist",
                            "MACD": "dif", "Signal line": "dea"})
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    return df

def macd_12_26_9(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    hist = 2 * (dif - dea)
    return dif, dea, hist

def rsi_14(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = ag / al
    return 100 - 100 / (1 + rs)

TICKERS = ["abbv", "gild"]
dfs = {}
for tk in TICKERS:
    d = load_tencent_240(tk)
    d["rsi14"] = rsi_14(d["close"])
    iso = pd.to_datetime(d["time"].dt.date)
    d["iso_year"] = iso.dt.isocalendar().year
    d["iso_week"] = iso.dt.isocalendar().week
    d["week_key"] = d["iso_year"].astype(str) + "-" + d["iso_week"].astype(str).str.zfill(2)
    d["dow"] = pd.to_datetime(d["time"].dt.date).dt.dayofweek  # 0=Mon
    d["bar_in_week"] = d.groupby("week_key").cumcount()        # 周内第几根(0起)
    dfs[tk] = d

weekly = {}
for tk in TICKERS:
    p = os.path.join(os.path.dirname(__file__), "..", "data", tk, f"{tk.upper()}, 1W.csv")
    w = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    w["dif"], w["dea"], w["hist"] = macd_12_26_9(w["adj_close"])
    iso = pd.to_datetime(w["date"])
    w["iso_year"] = iso.dt.isocalendar().year
    w["iso_week"] = iso.dt.isocalendar().week
    w["week_key"] = w["iso_year"].astype(str) + "-" + w["iso_week"].astype(str).str.zfill(2)
    weekly[tk] = w

HORIZONS = [3, 5, 10, 20, 40]

def fwd_metrics(d, t0_idx, horiz):
    max_idx = len(d) - 1
    if t0_idx + horiz > max_idx:
        return None
    t0_close = d["close"].iloc[t0_idx]
    seg_low = d["low"].iloc[t0_idx + 1: t0_idx + horiz + 1].min()
    seg_high = d["high"].iloc[t0_idx + 1: t0_idx + horiz + 1].max()
    end_close = d["close"].iloc[t0_idx + horiz]
    max_dd = (seg_low / t0_close - 1) * 100
    max_ru = (seg_high / t0_close - 1) * 100
    fwd_ret = (end_close / t0_close - 1) * 100
    return {"max_dd": max_dd, "max_runup": max_ru, "fwd_ret": fwd_ret}

def timing(d, t0_idx):
    max_idx = len(d) - 1
    end = min(t0_idx + 40, max_idx)
    closes = d["close"]
    t0_close = closes.iloc[t0_idx]
    seg = d.loc[t0_idx + 1: end]
    low_pos = seg["low"].values.argmin()
    bars_to_bottom = low_pos + 1
    rec = None
    for j, v in enumerate(seg["close"].values):
        if v >= t0_close:
            rec = j + 1
            break
    ref_high = d["high"].iloc[max(0, t0_idx - 20): t0_idx + 1].max()
    new_high = False
    nh_idx = None
    for j in range(t0_idx + 1, end + 1):
        if d["high"].iloc[j] > ref_high:
            new_high = True
            nh_idx = j - t0_idx
            break
    return bars_to_bottom, rec, new_high, nh_idx

def find_first_ob(d, week_key, thr=70):
    m = d["week_key"] == week_key
    sub = d[m]
    if len(sub) == 0:
        return None
    ob = sub[sub["rsi14"] >= thr]
    if len(ob) == 0:
        return None
    return ob.index[0]  # teoricamente pos label

# 事件周集合
ev_weeks = {}
for tk in TICKERS:
    w = weekly[tk]
    evs = []
    for i in range(1, len(w)):
        if w.loc[i - 1, "hist"] < 0 and w.loc[i, "hist"] >= 0:
            evs.append(w.loc[i, "week_key"])
    ev_weeks[tk] = set(evs)

# ---------------- 分组 t0 提取 ----------------
def collect_group(tk, week_keys, thr=70, label=""):
    d = dfs[tk]
    recs = []
    for wk in week_keys:
        t0_idx = find_first_ob(d, wk, thr)
        if t0_idx is None:
            continue
        fm40 = fwd_metrics(d, t0_idx, max(HORIZONS))
        if fm40 is None:
            continue
        tm = timing(d, t0_idx)
        rec = {
            "ticker": tk, "week_key": wk, "t0_idx": int(t0_idx),
            "t0_time": d.loc[t0_idx, "time"].strftime("%Y-%m-%d %H:%M"),
            "t0_close": round(float(d.loc[t0_idx, "close"]), 2),
            "rsi_t0": round(float(d.loc[t0_idx, "rsi14"]), 1),
            "dow": int(d.loc[t0_idx, "dow"]),
            "bar_in_week": int(d.loc[t0_idx, "bar_in_week"]),
            "n_ob_week": int((d[d["week_key"] == wk]["rsi14"] >= thr).sum()),
            "bars_to_bottom": tm[0], "bars_to_recover": tm[1],
            "new_high_40": bool(tm[2]), "bars_to_nh": tm[3],
        }
        for h in HORIZONS:
            fh = fwd_metrics(d, t0_idx, h)
            if fh is None:
                rec[f"dd_{h}"] = None; rec[f"ru_{h}"] = None; rec[f"fwd_{h}"] = None
            else:
                rec[f"dd_{h}"] = round(fh["max_dd"], 2)
                rec[f"ru_{h}"] = round(fh["max_runup"], 2)
                rec[f"fwd_{h}"] = round(fh["fwd_ret"], 2)
        recs.append(rec)
    return recs

ev_group, ctrl_group = [], []
for tk in TICKERS:
    w = weekly[tk]
    ctrl_keys = []
    for _, r in w.iterrows():
        if r["hist"] < 0 or np.isnan(r["hist"]):
            continue
        if r["week_key"] in ev_weeks[tk]:
            continue
        ctrl_keys.append(r["week_key"])
    ev_group += collect_group(tk, ev_weeks[tk], 70, "event")
    ctrl_group += collect_group(tk, ctrl_keys, 70, "ctrl")

ev_df = pd.DataFrame(ev_group)
ctrl_df = pd.DataFrame(ctrl_group)
print(f"事件组 t0(转正周内超买): {len(ev_df)}  对照组 t0(普通强势周内超买): {len(ctrl_df)}")

def summarize(nums):
    nums = [x for x in nums if x is not None and not (isinstance(x, float) and np.isnan(x))]
    if len(nums) == 0:
        return {"n": 0}
    nums = np.array(nums, dtype=float)
    return {
        "n": int(len(nums)), "mean": round(float(nums.mean()), 2), "med": round(float(np.median(nums)), 2),
        "p10": round(float(np.percentile(nums, 10)), 2), "p25": round(float(np.percentile(nums, 25)), 2),
        "p75": round(float(np.percentile(nums, 75)), 2), "p90": round(float(np.percentile(nums, 90)), 2),
        "min": round(float(nums.min()), 2), "max": round(float(nums.max()), 2),
        "neg_pct": round(float((nums < 0).mean() * 100), 1),
    }

def group_summary(g, label):
    out = {"label": label, "n": len(g)}
    for h in HORIZONS:
        out[f"dd_{h}"] = summarize(g[f"dd_{h}"].tolist())
        out[f"fwd_{h}"] = summarize(g[f"fwd_{h}"].tolist())
    out["recover"] = summarize(g["bars_to_recover"].replace({None: np.nan}).tolist())
    out["bottom"] = summarize(g["bars_to_bottom"].tolist())
    out["new_high_rate"] = round(float(g["new_high_40"].mean() * 100), 1) if len(g) else None
    return out

ev_sum = group_summary(ev_df, "转正周超买")
ctrl_sum = group_summary(ctrl_df, "普通强势周超买")

print("\n===== 事件组 vs 对照组 =====")
for h in HORIZONS:
    a = ev_sum[f"dd_{h}"]
    b = ctrl_sum[f"dd_{h}"]
    print(f"dd_{h}: 事件组 中位 {a['med']}% (p25 {a['p25']}/p75 {a['p75']}) | 对照 中位 {b['med']}% (p25 {b['p25']}/p75 {b['p75']})")
for h in HORIZONS:
    a = ev_sum[f"fwd_{h}"]
    b = ctrl_sum[f"fwd_{h}"]
    print(f"fwd_{h}: 事件组 中位 {a['med']}% 胜率{100-a['neg_pct']}% | 对照 中位 {b['med']}% 胜率{100-b['neg_pct']}%")
print(f"40根内创新高: 事件 {ev_sum['new_high_rate']}% vs 对照 {ctrl_sum['new_high_rate']}%")
print(f"回到t0收盘: 事件 中位{ev_sum['recover']['med']}根 vs 对照 中位{ctrl_sum['recover']['med']}根")

# Fisher 精确/近似：事件组 vs 对照组 调整>3% 的比例差异（二项近似）
def prop_test(a_n, a_k, b_n, b_k):
    # 二项比例 z 检验
    pa, pb = a_k / a_n, b_k / b_n
    p = (a_k + b_k) / (a_n + b_n)
    se = np.sqrt(p * (1 - p) * (1 / a_n + 1 / b_n))
    z = (pa - pb) / se if se > 0 else 0
    from math import erf, sqrt
    pv = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return round(pa * 100, 1), round(pb * 100, 1), round(pv, 3)

for h in HORIZONS:
    a = ev_df[f"dd_{h}"]
    b = ctrl_df[f"dd_{h}"]
    pa, pb, pv = prop_test(len(a), int((a < -3).sum()), len(b), int((b < -3).sum()))
    print(f"回撤超3%比例 h={h}: 事件 {pa}% vs 对照 {pb}% (p={pv})")

# ---------------- 阈值灵敏度 ----------------
sens = {}
for thr in [65, 70, 75]:
    ev_list, ctrl_list = [], []
    for tk in TICKERS:
        w_list = list(ev_weeks[tk])
        c_true = []
        for _, r in weekly[tk].iterrows():
            if r["hist"] < 0 or np.isnan(r["hist"]) or r["week_key"] in ev_weeks[tk]:
                continue
            c_true.append(r["week_key"])
        ev_list += collect_group(tk, w_list, thr)
        ctrl_list += collect_group(tk, c_true, thr)
    sens[str(thr)] = {
        "event_n": len(ev_list), "ctrl_n": len(ctrl_list),
        "event_dd5": summarize([x["dd_5"] for x in ev_list]),
        "ctrl_dd5": summarize([x["dd_5"] for x in ctrl_list]),
        "event_dd20": summarize([x["dd_20"] for x in ev_list]),
        "ctrl_dd20": summarize([x["dd_20"] for x in ctrl_list]),
        "event_fwd20": summarize([x["fwd_20"] for x in ev_list]),
        "ctrl_fwd20": summarize([x["fwd_20"] for x in ctrl_list]),
    }
    print(f"\n阈值 {thr}: 事件n={len(ev_list)} 对照n={len(ctrl_list)}")

# ---------------- 超买时点在周内分布 ----------------
dow_dist = ev_df["dow"].value_counts().sort_index()
bar_dist = ev_df["bar_in_week"].value_counts().sort_index()
print("\n事件组超买出现日(0=周一):", dow_dist.to_dict())
print("周内第几根bar:", bar_dist.to_dict())

# ---------------- 当前状态 ----------------
cur = {}
for tk in TICKERS:
    d = dfs[tk]
    w = weekly[tk]
    last_bar = d.iloc[-1]
    last_w = w.iloc[-1]
    # 当前周线 hist 与最近一次转正
    recent_cross = None
    for i in range(len(w) - 1, 0, -1):
        if w.loc[i - 1, "hist"] < 0 and w.loc[i, "hist"] >= 0:
            recent_cross = w.loc[i, "week_start"] if "week_start" in w.columns else w.loc[i, "date"].strftime("%Y-%m-%d")
            break
    cur[tk] = {
        "last_4h_time": d.loc[last_bar.name, "time"].strftime("%Y-%m-%d %H:%M"),
        "rsi14_now": round(float(last_bar["rsi14"]), 1),
        "close_now": round(float(last_bar["close"]), 2),
        "weekly_hist_now": round(float(last_w["hist"]), 3),
        "weekly_dif_now": round(float(last_w["dif"]), 3),
        "weekly_dea_now": round(float(last_w["dea"]), 3),
        "recent_cross_week": str(recent_cross),
        "last_week_key": last_w["week_key"],
        "in_event_week": last_w["week_key"] in ev_weeks[tk],
    }

print("\n===== 当前状态 =====")
for tk, v in cur.items():
    print(f"[{tk.upper()}] 4h@ {v['last_4h_time']} close={v['close_now']} RSI={v['rsi14_now']} | 周线 hist={v['weekly_hist_now']} 最近转正周={v['recent_cross_week']} 本周是转正周={v['in_event_week']}")

out = {
    "meta": {
        "horizons": HORIZONS,
        "ob_threshold": 70,
        "event_weeks_total": {tk: len(ev_weeks[tk]) for tk in TICKERS},
    },
    "groups": {"event": ev_sum, "ctrl": ctrl_sum},
    "sensitivity": sens,
    "dow_dist": {str(k): int(v) for k, v in dow_dist.items()},
    "bar_dist": {str(k): int(v) for k, v in bar_dist.items()},
    "current": cur,
    "events_detail": ev_df.to_dict("records"),
    "ctrl_detail": ctrl_df.to_dict("records"),
}
with open(os.path.join(OUT, "abbv_gild_weekline_ob_ctrl.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("\nSaved:", os.path.join(OUT, "abbv_gild_weekline_ob_ctrl.json"))
print("DONE")