# -*- coding: utf-8 -*-
"""
补充口径：周线 MACD 柱负转正后 WINDOW=2 周窗口内(含转正周)首次 4h RSI>=70
→ 统计该超买后调整深度。与"仅转正当周"口径对比，更贴近用户实际场景。
同时输出每个事件的 (转正周, 超买周, 相隔周数) 对照当前 GILD 场景。
"""
import pandas as pd
import numpy as np
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "results")

def load_tencent_240(ticker):
    p = os.path.join(os.path.dirname(__file__), "..", "data", ticker, f"{ticker}_240_tencent.csv")
    df = pd.read_csv(p)
    df = df.rename(columns={"time": "time", "open": "open", "high": "high", "low": "low",
                            "close": "close", "Volume": "volume", "Histogram": "hist",
                            "MACD": "dif", "Signal line": "dea"})
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)

def macd_12_26_9(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    return dif, dea, 2 * (dif - dea)

def rsi_14(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + ag / al)

TICKERS = ["abbv", "gild"]
dfs, weekly = {}, {}
for tk in TICKERS:
    d = load_tencent_240(tk)
    d["rsi14"] = rsi_14(d["close"])
    iso = pd.to_datetime(d["time"].dt.date)
    d["iso_year"] = iso.dt.isocalendar().year
    d["iso_week"] = iso.dt.isocalendar().week
    d["week_key"] = d["iso_year"].astype(str) + "-" + d["iso_week"].astype(str).str.zfill(2)
    d["bar_in_week"] = d.groupby("week_key").cumcount()
    d["dow"] = iso.dt.dayofweek
    dfs[tk] = d

    p = os.path.join(os.path.dirname(__file__), "..", "data", tk, f"{tk.upper()}, 1W.csv")
    w = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    w["dif"], w["dea"], w["hist"] = macd_12_26_9(w["adj_close"])
    iso = pd.to_datetime(w["date"])
    w["iso_year"] = iso.dt.isocalendar().year
    w["iso_week"] = iso.dt.isocalendar().week
    w["week_key"] = w["iso_year"].astype(str) + "-" + w["iso_week"].astype(str).str.zfill(2)
    weekly[tk] = w

# 所有转正周 + 有序周列表
crosses = {}   # tk -> list of (idx_in_weekly, week_key, week_start)
week_order = {}  # tk -> sorted week_keys
for tk in TICKERS:
    w = weekly[tk]
    cross = []
    for i in range(1, len(w)):
        if w.loc[i - 1, "hist"] < 0 and w.loc[i, "hist"] >= 0:
            cross.append({
                "idx": i, "week_key": w.loc[i, "week_key"],
                "week_start": w.loc[i, "date"].strftime("%Y-%m-%d"),
                "hist0": w.loc[i, "hist"],
            })
    crosses[tk] = cross
    week_order[tk] = w["week_key"].tolist()

HORIZONS = [3, 5, 10, 20, 40]

def fwd_metrics(d, t0_idx, horiz):
    if t0_idx + horiz > len(d) - 1:
        return None
    t0_close = d["close"].iloc[t0_idx]
    seg_low = d["low"].iloc[t0_idx + 1: t0_idx + horiz + 1].min()
    seg_high = d["high"].iloc[t0_idx + 1: t0_idx + horiz + 1].max()
    end_close = d["close"].iloc[t0_idx + horiz]
    return {
        "max_dd": (seg_low / t0_close - 1) * 100,
        "max_runup": (seg_high / t0_close - 1) * 100,
        "fwd_ret": (end_close / t0_close - 1) * 100,
    }

def timing(d, t0_idx, window=40):
    end = min(t0_idx + window, len(d) - 1)
    t0_close = d["close"].iloc[t0_idx]
    seg = d.loc[t0_idx + 1: end]
    bars_to_bottom = seg["low"].values.argmin() + 1
    rec = None
    for j, v in enumerate(seg["close"].values):
        if v >= t0_close:
            rec = j + 1
            break
    ref_high = d["high"].iloc[max(0, t0_idx - 20): t0_idx + 1].max()
    new_high, nh_idx = False, None
    for j in range(t0_idx + 1, end + 1):
        if d["high"].iloc[j] > ref_high:
            new_high, nh_idx = True, j - t0_idx
            break
    return bars_to_bottom, rec, new_high, nh_idx

def summarize(nums):
    nums = np.array([x for x in nums if x is not None and not (isinstance(x, float) and np.isnan(x))], dtype=float)
    if len(nums) == 0:
        return {"n": 0}
    return {
        "n": int(len(nums)), "mean": round(float(nums.mean()), 2), "med": round(float(np.median(nums)), 2),
        "p10": round(float(np.percentile(nums, 10)), 2), "p25": round(float(np.percentile(nums, 25)), 2),
        "p75": round(float(np.percentile(nums, 75)), 2), "p90": round(float(np.percentile(nums, 90)), 2),
        "min": round(float(nums.min()), 2), "max": round(float(nums.max()), 2),
        "neg_pct": round(float((nums < 0).mean() * 100), 1),
    }

# 对每个转正事件：在 [转正周, 转正周+1 周] 窗口内找首次超买
records = []
for tk in TICKERS:
    w_order = week_order[tk]
    order_pos = {wk: i for i, wk in enumerate(w_order)}
    for c in crosses[tk]:
        pos = order_pos[c["week_key"]]
        window_keys = w_order[pos: pos + 3]  # 转正周 + 后2周（含本周末周，最多3个周key）
        d = dfs[tk]
        sub = d[d["week_key"].isin(window_keys)]
        ob = sub[sub["rsi14"] >= 70]
        if len(ob) == 0:
            records.append({"ticker": tk, **c, "has_ob": False, "ob_week_gap": None})
            continue
        first = ob.iloc[0]
        t0_idx = first.name
        gap = order_pos[first["week_key"]] - pos
        fm = fwd_metrics(d, t0_idx, max(HORIZONS))
        tm = timing(d, t0_idx)
        rec = {
            "ticker": tk, **c, "has_ob": True, "ob_week_gap": int(gap),
            "ob_week_key": first["week_key"],
            "t0_time": first["time"].strftime("%Y-%m-%d %H:%M"),
            "t0_close": round(float(first["close"]), 2),
            "rsi_t0": round(float(first["rsi14"]), 1),
            "ob_bar_in_week": int(first["bar_in_week"]),
            "ob_dow": int(first["dow"]),
            "n_ob_window": int((d["week_key"].isin(window_keys) & (d["rsi14"] >= 70)).sum()),
            "bars_to_bottom": tm[0], "bars_to_recover": tm[1],
            "new_high_40": bool(tm[2]), "bars_to_nh": tm[3],
        }
        for h in HORIZONS:
            fh = fwd_metrics(d, t0_idx, h)
            rec[f"dd_{h}"] = round(fh["max_dd"], 2) if fh else None
            rec[f"ru_{h}"] = round(fh["max_runup"], 2) if fh else None
            rec[f"fwd_{h}"] = round(fh["fwd_ret"], 2) if fh else None
        records.append(rec)

rec_df = pd.DataFrame(records)
with_ob = rec_df[rec_df["has_ob"]].copy()
print(f"转正事件总数: {len(rec_df)}")
print(f"转正后2周窗口内出现4h超买: {with_ob['ticker'].count()} / {len(rec_df)}  ({with_ob['ticker'].count()/len(rec_df)*100:.1f}%)")
print(f"  其中转正当周出现: {(with_ob['ob_week_gap']==0).sum()}  下一周: {(with_ob['ob_week_gap']==1).sum()}  下下周: {(with_ob['ob_week_gap']==2).sum()}")
for tk in TICKERS:
    sub = with_ob[with_ob["ticker"] == tk]
    tot = len(rec_df[rec_df["ticker"] == tk])
    print(f"  {tk}: {len(sub)}/{tot}  ({len(sub)/tot*100:.1f}%)")

def group_summary(g):
    out = {"n": len(g)}
    for h in HORIZONS:
        out[f"dd_{h}"] = summarize(g[f"dd_{h}"].tolist())
        out[f"fwd_{h}"] = summarize(g[f"fwd_{h}"].tolist())
    out["recover"] = summarize(g["bars_to_recover"].replace({None: np.nan}).tolist())
    out["bottom"] = summarize(g["bars_to_bottom"].tolist())
    out["new_high_rate"] = round(float(g["new_high_40"].mean() * 100), 1) if len(g) else None
    return out

agg = group_summary(with_ob)
print("\n===== 转正后2周窗口内超买 → 调整深度（合并 n=%d）=====" % agg["n"])
for h in HORIZONS:
    d, f = agg[f"dd_{h}"], agg[f"fwd_{h}"]
    print(f"h={h}: 最大回撤 中位 {d['med']}% (p25 {d['p25']} / p75 {d['p75']}, p90 {d['p90']}) | 期末 中位 {f['med']}% 胜率 {100-f['neg_pct']}% | 回撤>3% {sum(1 for v in with_ob[f'dd_{h}'] if v is not None and v < -3)}/{d['n']}")
print(f"回到t0收盘: 中位 {agg['recover']['med']} 根 (p25 {agg['recover']['p25']}/p75 {agg['recover']['p75']}); 40根内创新高 {agg['new_high_rate']}%; 触底 中位 {agg['bottom']['med']} 根")

# 按 gap 分组
by_gap = {}
for gv in [0, 1, 2]:
    sub = with_ob[with_ob["ob_week_gap"] == gv]
    by_gap[str(gv)] = group_summary(sub)
    if len(sub):
        dd20 = sub["dd_20"].tolist()
        print(f"gap={gv} (n={len(sub)}): fwd_20 中位 {by_gap[str(gv)]['fwd_20']['med']}%, dd_20 中位 {by_gap[str(gv)]['dd_20']['med']}%")

# 当前状态卡
cur = {}
for tk in TICKERS:
    d, w = dfs[tk], weekly[tk]
    last = w.iloc[-1]
    crosses_tk = crosses[tk]
    last_cross = crosses_tk[-1] if crosses_tk else None
    cur[tk] = {
        "last_4h": d.iloc[-1]["time"].strftime("%Y-%m-%d %H:%M"),
        "close": round(float(d.iloc[-1]["close"]), 2),
        "rsi": round(float(d.iloc[-1]["rsi14"]), 1),
        "weekly_hist": round(float(last["hist"]), 3),
        "last_cross_week": last_cross["week_start"] if last_cross else None,
        "cross_to_now_weeks": (len(week_order[tk]) - 1 - last_cross["idx"]) if last_cross else None,
    }
    print(f"\n[{tk.upper()}] 4h@ {cur[tk]['last_4h']} RSI={cur[tk]['rsi']} | 周线hist={cur[tk]['weekly_hist']} | 最近转正={cur[tk]['last_cross_week']} (距今{cur[tk]['cross_to_now_weeks']}周)")

out = {
    "meta": {"window_weeks": 3, "thr": 70, "horizons": HORIZONS},
    "events_total": int(len(rec_df)),
    "with_ob_n": int(len(with_ob)),
    "with_ob_rate": round(float(len(with_ob) / len(rec_df) * 100), 1),
    "gap_dist": {str(k): int(v) for k, v in with_ob["ob_week_gap"].value_counts().sort_index().items()},
    "per_ticker": {tk: {"n": int(len(rec_df[rec_df.ticker == tk])),
                        "with_ob": int(len(with_ob[with_ob.ticker == tk])),
                        "rate": round(float(len(with_ob[with_ob.ticker == tk]) / max(1, len(rec_df[rec_df.ticker == tk])) * 100), 1)}
                   for tk in TICKERS},
    "summary": agg,
    "by_gap": by_gap,
    "current": cur,
    "detail": with_ob.to_dict("records"),
}
with open(os.path.join(OUT, "abbv_gild_weekline_ob_window.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("\nSaved window json")