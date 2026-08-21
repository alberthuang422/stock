# -*- coding: utf-8 -*-
"""ETF 弱势状态窗口 × 成分股每次触支撑 事件研究

口径（用户 2026-08-21 确认）：
  A. ETF 弱势状态（EMA10/EMA20，两条件 OR）：
     入场：EMA10 死叉 EMA20（前日 EMA10>=EMA20 且当日 EMA10<EMA20）
           OR 收盘连续 3 日低于 EMA20；以确认日为窗口起点（无前视）。
     出场：收盘重新站上 EMA20 OR EMA10 金叉 EMA20，先到先出（事件日=出场前一日）。
  B. 窗口内成分股每次触支撑 = 事件（分形+ATR聚类支撑，复用 djia_sector_support.stock_support_days）。
     入场=触及日收盘。同股 7 交易日内重复触及按聚类折扣另报 dedup 口径。
  C. 标的池：道指 30 成分股 × 9 板块 SPDR ETF（XLC 2018-06 起有数据）。

对照：(a) 全交易日基线（每3日抽样）
      (b) 弱势窗外触支撑（同股，ETF 未处弱势）
      (c) 弱势窗内非触及日（每5日抽样）

输出：results/etf_weak_support.json + etf_weak_support_events.csv（控制台只打印 KPI）
"""
import os
import json

import numpy as np
import pandas as pd

import djia_sector_support as dss
from djia_sector_support import load, atr_series, swing_lows, stock_support_days, WARM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results")

SECTORS = {
    "XLF": ["JPM", "GS", "AXP", "V", "MA", "TRV"],
    "XLK": ["MSFT", "AAPL", "CSCO", "IBM", "CRM"],
    "XLI": ["CAT", "HON", "BA", "MMM"],
    "XLV": ["UNH", "JNJ", "AMGN", "MRK"],
    "XLP": ["WMT", "PG", "KO"],
    "XLY": ["AMZN", "HD", "MCD", "NKE"],
    "XLC": ["VZ", "DIS"],
    "XLE": ["CVX"],
    "XLB": ["SHW"],
}
START = pd.Timestamp("2000-01-01")   # 事件扫描起点（EMA 预热由 WARM 保证）
CLUSTER_GAP = 7                      # 同股事件聚类窗口（交易日）


def etf_weak_windows(etf):
    """状态机：返回弱势窗口列表 + EMA 序列"""
    closes = etf["adj_close"].values
    ema10 = pd.Series(closes).ewm(span=10, adjust=False).mean().values
    ema20 = pd.Series(closes).ewm(span=20, adjust=False).mean().values
    dates = etf["date"].values
    n = len(etf)
    windows = []
    in_weak = False
    streak = 0
    ws, reason = None, None
    for t in range(1, n):
        if t < WARM or pd.Timestamp(dates[t]) < START:
            continue
        cross_dn = ema10[t] < ema20[t] and ema10[t - 1] >= ema20[t - 1]
        cross_up = ema10[t] > ema20[t] and ema10[t - 1] <= ema20[t - 1]
        streak = streak + 1 if closes[t] < ema20[t] else 0
        if not in_weak:
            if cross_dn or streak >= 3:
                in_weak, ws = True, t
                reason = "死叉" if cross_dn else "连续3日低于EMA20"
        else:
            if closes[t] > ema20[t] or cross_up:
                windows.append({
                    "start": ws, "end": t - 1,
                    "entry_reason": reason,
                    "exit_reason": "站回EMA20" if closes[t] > ema20[t] else "EMA10金叉",
                })
                in_weak = False
    if in_weak:
        windows.append({"start": ws, "end": n - 1,
                        "entry_reason": reason, "exit_reason": "进行中"})
    return windows, ema10, ema20


def grouped_stats(items, cache, ks=(1, 5, 10, 20)):
    """items: (tk, t, entry)"""
    per_k = {str(k): {"rets": [], "mdd": [], "mxb": []} for k in ks}
    for tk, t, entry in items:
        c = cache[tk]["adj_close"].values
        nn = len(c)
        for k in ks:
            if t + k >= nn:
                continue
            per_k[str(k)]["rets"].append((c[t + k] / entry - 1) * 100)
            lo = np.min(c[t + 1:t + k + 1]); hi = np.max(c[t + 1:t + k + 1])
            per_k[str(k)]["mdd"].append((lo / entry - 1) * 100)
            per_k[str(k)]["mxb"].append((hi / entry - 1) * 100)
    agg = {}
    for k in ks:
        v = np.array(per_k[str(k)]["rets"])
        if len(v) == 0:
            agg[str(k)] = None
            continue
        mean = float(v.mean()); std = float(v.std(ddof=1)) if len(v) > 1 else 0
        agg[str(k)] = {
            "n": int(len(v)), "mean": round(mean, 2), "median": round(float(np.median(v)), 2),
            "win": round(float(np.mean(v > 0)) * 100, 1), "std": round(std, 2),
            "p25": round(float(np.percentile(v, 25)), 2), "p75": round(float(np.percentile(v, 75)), 2),
            "tstat": round(mean / (std / np.sqrt(len(v))), 2) if std > 0 else None,
            "maxDD_mean": round(float(np.mean(per_k[str(k)]["mdd"])), 2),
            "maxDD_p10": round(float(np.percentile(per_k[str(k)]["mdd"], 10)), 2),
            "maxBounce_mean": round(float(np.mean(per_k[str(k)]["mxb"])), 2),
        }
    return agg


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(x) for x in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return round(float(o), 3)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)):
        return None
    return o


def main():
    cache = {}

    def get(tk):
        if tk not in cache:
            cache[tk] = load(tk)
        return cache[tk]

    vix = get("VIX")
    spy = get("SPY")
    vix_close = vix["close"].values
    vix_idx = {d: i for i, d in enumerate(pd.Series(vix["date"].values).dt.normalize())}
    spy_close = spy["adj_close"].values
    spy_ma100 = pd.Series(spy_close).rolling(100).mean().values
    spy_idx = {d: i for i, d in enumerate(pd.Series(spy["date"].values).dt.normalize())}

    all_events = []
    ctrl_touch_out = []     # (tk, t, entry)
    ctrl_window_days = []
    window_summary = []
    pair_meta = {}
    missing = []

    for etf_tk, stks in SECTORS.items():
        try:
            etf = get(etf_tk)
        except FileNotFoundError:
            missing.append(etf_tk)
            continue
        windows, ema10, ema20 = etf_weak_windows(etf)
        etf_dates = pd.Series(etf["date"].values).dt.normalize().values
        etf_closes = etf["adj_close"].values
        etf_date_pos = {d: i for i, d in enumerate(etf_dates)}
        for w in windows:
            window_summary.append({
                "etf": etf_tk,
                "start": str(pd.Timestamp(etf_dates[w["start"]]).date()),
                "end": str(pd.Timestamp(etf_dates[w["end"]]).date()),
                "dur": int(w["end"] - w["start"] + 1),
                "entry_reason": w["entry_reason"], "exit_reason": w["exit_reason"],
            })
        weak_sets = []   # 每个元素 (ws_date, we_date, ws_idx, we_idx, entry_reason)
        for w in windows:
            weak_sets.append((w["start"], w["end"], w["entry_reason"]))

        for stk_tk in stks:
            try:
                stk = get(stk_tk)
            except FileNotFoundError:
                missing.append(stk_tk)
                continue
            touches = stock_support_days(stk)
            closes = stk["adj_close"].values
            dates = pd.Series(stk["date"].values).dt.normalize().values
            n = len(stk)
            nev = 0
            for t in range(WARM, n):
                d = dates[t]
                if d < START.to_datetime64():
                    continue
                if t not in touches:
                    continue
                # 找所属窗口（ETF 日历上包含该日期的窗口）
                hit = None
                for ws, we, rsn in weak_sets:
                    if ws > we:
                        continue
                    if etf_dates[ws] <= d <= etf_dates[we]:
                        hit = (ws, we, rsn)
                        break
                if hit is None:
                    ctrl_touch_out.append((stk_tk, t, closes[t]))
                    continue
                ws, we, rsn = hit
                nev += 1
                tm = touches[t]
                ei = etf_date_pos.get(d)
                days_into = int(ei - ws) if ei is not None else None
                # 事件日 ETF 状态
                etf_depth = round((etf_closes[ei] / ema20[ei] - 1) * 100, 2) if ei is not None else None
                ema_state = "EMA10<EMA20" if (ei is not None and ema10[ei] < ema20[ei]) else "EMA10>=EMA20"
                rs5 = None
                if t >= 5 and ei is not None and ei >= 5:
                    rs5 = round((closes[t] / closes[t - 5] - etf_closes[ei] / etf_closes[ei - 5]) * 100, 2)
                vx = vix_idx.get(d)
                sp = spy_idx.get(d)
                rec = {
                    "sector": etf_tk, "ticker": stk_tk, "pair": f"{etf_tk}/{stk_tk}",
                    "date": tm["date"], "t": int(t), "entry": round(float(closes[t]), 3),
                    "entry_reason": rsn, "days_into_window": days_into,
                    "etf_depth_pct": etf_depth, "ema_state": ema_state,
                    "support_level": tm["level"], "support_band_lo": tm["band_lo"],
                    "support_band_hi": tm["band_hi"], "support_age": tm["age"],
                    "support_touches": tm["kinds"][0], "n_levels": tm["n_levels"],
                    "lower_shadow": tm["lower_shadow"], "stk_vol_ratio": tm["vol_ratio"],
                    "stk_ret_day": tm["ret_day"], "rs5": rs5,
                    "vix": round(float(vix_close[vx]), 1) if vx is not None else None,
                    "spy_above_ma100": bool(spy_close[sp] > spy_ma100[sp]) if sp is not None and np.isfinite(spy_ma100[sp]) else None,
                    "etf_t_index": int(ei) if ei is not None else None,
                }
                for k in (1, 5, 10, 20):
                    rec[f"fwd{k}"] = round((closes[t + k] / closes[t] - 1) * 100, 2) if t + k < n else None
                blv = tm["band_lo"]
                broken_day = None
                for k2 in range(1, 11):
                    if t + k2 < n and closes[t + k2] < blv:
                        broken_day = k2
                        break
                rec["support_broken_day"] = broken_day
                all_events.append(rec)
            # 窗内非触及日对照（每5日抽样）
            for t in range(WARM, n, 5):
                d = dates[t]
                if d < START.to_datetime64() or t in touches:
                    continue
                for ws, we, rsn in weak_sets:
                    if etf_dates[ws] <= d <= etf_dates[we]:
                        ctrl_window_days.append((stk_tk, t, closes[t]))
                        break
            pair_meta[f"{etf_tk}/{stk_tk}"] = nev

    # ---- 聚类折扣（同股 7 日内） ----
    es = sorted(all_events, key=lambda e: (e["ticker"], e["t"]))
    last_t = {}
    dedup = []
    for e in es:
        lt = last_t.get(e["ticker"], -9999)
        if e["t"] - lt > CLUSTER_GAP:
            dedup.append(e)
        last_t[e["ticker"]] = e["t"]

    ev_stats = grouped_stats([(e["ticker"], e["t"], e["entry"]) for e in all_events], cache)
    dd_stats = grouped_stats([(e["ticker"], e["t"], e["entry"]) for e in dedup], cache)
    ct_stats = grouped_stats(ctrl_touch_out, cache)
    cw_stats = grouped_stats(ctrl_window_days, cache)
    baseline_items = []
    all_tks = sorted({tk for stks in SECTORS.values() for tk in stks})
    for tk in all_tks:
        c = cache[tk]["adj_close"].values
        for t in range(WARM, len(c) - 20, 3):
            baseline_items.append((tk, t, c[t]))
    base_stats = grouped_stats(baseline_items, cache)

    # ---- 结局分类 ----
    cls = {"V型反转": 0, "死猫反弹": 0, "支撑击穿": 0, "横盘消化": 0, "未完整": 0}
    for e in all_events:
        f5, f10, f20 = e.get("fwd5"), e.get("fwd10"), e.get("fwd20")
        if f10 is None or f20 is None:
            cls["未完整"] += 1
            e["cls"] = "未完整"
            continue
        tk, t, entry = e["ticker"], e["t"], e["entry"]
        c = cache[tk]["adj_close"].values
        hi10 = (np.max(c[t + 1:t + 11]) / entry - 1) * 100 if t + 10 < len(c) else None
        lo5 = (np.min(c[t + 1:t + 6]) / entry - 1) * 100
        if e["support_broken_day"] is not None or (f5 is not None and f5 < -4):
            cls["支撑击穿"] += 1; e["cls"] = "支撑击穿"
        elif hi10 is not None and hi10 >= 2 and (f10 <= 0 or f20 < -1):
            cls["死猫反弹"] += 1; e["cls"] = "死猫反弹"
        elif f5 is not None and f5 > 0 and f20 > 0 and lo5 > -5:
            cls["V型反转"] += 1; e["cls"] = "V型反转"
        else:
            cls["横盘消化"] += 1; e["cls"] = "横盘消化"
    cls_total = sum(v for k, v in cls.items() if k != "未完整")
    cls_pct = {k: round(v / cls_total * 100, 1) for k, v in cls.items()} if cls_total else {}

    # ---- 过滤维度 ----
    def subset_stats(pred):
        sel = [(e["ticker"], e["t"], e["entry"]) for e in all_events if pred(e)]
        return (grouped_stats(sel, cache) if sel else None), len(sel)

    filters = {}
    filters["vix"] = {}
    for name, lo, hi in (("VIX<20", 0, 20), ("VIX 20-30", 20, 30), ("VIX>=30", 30, 999)):
        s, ns = subset_stats(lambda e, lo=lo, hi=hi: e["vix"] is not None and lo <= e["vix"] < hi)
        filters["vix"][name] = {"n": ns, "stats": s}
    filters["touches"] = {}
    def tc(e):
        try:
            return int(e["support_touches"].split("(")[1].split("触")[0])
        except Exception:
            return None
    for name, lo, hi in (("1-2触", 1, 3), ("3-4触", 3, 5), (">=5触", 5, 99)):
        s, ns = subset_stats(lambda e, lo=lo, hi=hi: tc(e) is not None and lo <= tc(e) < hi)
        filters["touches"][name] = {"n": ns, "stats": s}
    filters["win_pos"] = {}
    for name, lo, hi in (("窗初(0-5日)", 0, 6), ("窗中(6-15日)", 6, 16), ("窗末(>15日)", 16, 9999)):
        s, ns = subset_stats(lambda e, lo=lo, hi=hi: e["days_into_window"] is not None and lo <= e["days_into_window"] < hi)
        filters["win_pos"][name] = {"n": ns, "stats": s}
    filters["entry_reason"] = {}
    for name in ("死叉", "连续3日低于EMA20"):
        s, ns = subset_stats(lambda e, name=name: e["entry_reason"] == name)
        filters["entry_reason"][name] = {"n": ns, "stats": s}
    filters["depth"] = {}
    for name, pred in (
        ("偏离0~-2%", lambda e: e["etf_depth_pct"] is not None and -2 < e["etf_depth_pct"] <= 0),
        ("偏离-2~-5%", lambda e: e["etf_depth_pct"] is not None and -5 < e["etf_depth_pct"] <= -2),
        ("偏离<=-5%", lambda e: e["etf_depth_pct"] is not None and e["etf_depth_pct"] <= -5),
    ):
        s, ns = subset_stats(pred)
        filters["depth"][name] = {"n": ns, "stats": s}
    filters["shape"] = {}
    s, ns = subset_stats(lambda e: e["lower_shadow"] >= 0.3)
    filters["shape"]["下影线>=0.3"] = {"n": ns, "stats": s}
    s, ns = subset_stats(lambda e: e["lower_shadow"] < 0.3)
    filters["shape"]["下影线<0.3"] = {"n": ns, "stats": s}
    s, ns = subset_stats(lambda e: e["stk_vol_ratio"] is not None and e["stk_vol_ratio"] <= 1.0)
    filters["shape"]["个股缩量(<=1.0)"] = {"n": ns, "stats": s}
    s, ns = subset_stats(lambda e: e["stk_vol_ratio"] is not None and e["stk_vol_ratio"] > 1.0)
    filters["shape"]["个股放量(>1.0)"] = {"n": ns, "stats": s}
    filters["rs"] = {}
    s, ns = subset_stats(lambda e: e["rs5"] is not None and e["rs5"] >= 0)
    filters["rs"]["强于板块(RS>=0)"] = {"n": ns, "stats": s}
    s, ns = subset_stats(lambda e: e["rs5"] is not None and e["rs5"] < 0)
    filters["rs"]["弱于板块(RS<0)"] = {"n": ns, "stats": s}
    filters["macro"] = {}
    for name, pred in (
        ("SPY在MA100上方", lambda e: e["spy_above_ma100"] is True),
        ("SPY在MA100下方", lambda e: e["spy_above_ma100"] is False),
    ):
        s, ns = subset_stats(pred)
        sel = [e for e in all_events if pred(e)]
        br = [e for e in sel if e["support_broken_day"] is not None]
        filters["macro"][name] = {"n": ns, "stats": s,
                                  "break_rate": round(len(br) / len(sel) * 100, 1) if sel else None}
    br_all = [e for e in all_events if e["support_broken_day"] is not None]
    filters["break_rate_all"] = round(len(br_all) / len(all_events) * 100, 1) if all_events else None

    # ---- 分板块 / 分标的 ----
    by_sector = {}
    for sec in SECTORS:
        sel = [(e["ticker"], e["t"], e["entry"]) for e in all_events if e["sector"] == sec]
        by_sector[sec] = {"n": len(sel), "stats": grouped_stats(sel, cache) if sel else None}

    # ---- 止损网格 ----
    def simulate(stop_x, tp_pct, max_hold=20):
        rets = []
        for e in all_events:
            tk, t, entry = e["ticker"], e["t"], e["entry"]
            df = cache[tk]
            c, o, lo = df["adj_close"].values, df["adj_open"].values, df["adj_low"].values
            lvl = e.get("support_band_lo") or e.get("support_level") or entry
            stop = lvl * (1 - stop_x)
            tp = entry * (1 + tp_pct) if tp_pct else None
            exit_ret = None
            nn = len(c)
            for k in range(1, max_hold + 1):
                if t + k >= nn:
                    break
                tt = t + k
                if lo[tt] <= stop:
                    px = min(o[tt], stop)
                    exit_ret = (px / entry - 1) * 100
                    break
                if tp is not None and c[tt] >= tp:
                    exit_ret = (tp / entry - 1) * 100
                    break
            if exit_ret is None and t + max_hold < nn:
                exit_ret = (c[t + max_hold] / entry - 1) * 100
            if exit_ret is not None:
                rets.append(exit_ret)
        v = np.array(rets)
        if len(v) == 0:
            return None
        return {"n": int(len(v)), "mean": round(float(v.mean()), 2),
                "median": round(float(np.median(v)), 2),
                "win": round(float(np.mean(v > 0)) * 100, 1)}

    grid = {}
    for sx in (0.01, 0.02, 0.03):
        for tp in (0.05, 0.10, None):
            key = f"stop{round(sx*100,1)}%/tp{int(tp*100) if tp else 'hold'}%"
            grid[key] = simulate(sx, tp)

    # ---- 画廊（代表性事件，≤8 张，窗口 [t-25, t+15]） ----
    vix_map = {str(pd.Timestamp(d).date()): float(c)
               for d, c in zip(vix["date"].values, vix["close"].values)}
    gallery = []
    picked_pairs = set()
    cands_pool = [e for e in all_events if e.get("cls") in ("V型反转", "支撑击穿", "死猫反弹", "横盘消化")
                  and e.get("fwd10") is not None]
    # 每板块取最近 1 个（优先击穿/V反结局），再按整体新近度补足至 8
    ordered = []
    for sec in SECTORS:
        sec_c = [e for e in cands_pool if e["sector"] == sec and e["pair"] not in picked_pairs]
        sec_c.sort(key=lambda e: (e["cls"] in ("支撑击穿", "V型反转"), e["date"]), reverse=True)
        if sec_c:
            ordered.append(sec_c[0])
            picked_pairs.add(sec_c[0]["pair"])
    rest = sorted([e for e in cands_pool if e["pair"] not in picked_pairs],
                  key=lambda e: e["date"], reverse=True)
    for e in rest:
        if len(ordered) >= 8:
            break
        ordered.append(e)
        picked_pairs.add(e["pair"])
    ordered.sort(key=lambda e: e["date"], reverse=True)
    for e in ordered[:8]:
        tk, t = e["ticker"], e["t"]
        df = cache[tk]
        etf_tk = e["sector"]
        etf = cache[etf_tk]
        a = max(0, t - 25)
        b = min(len(df) - 1, t + 15)
        dts = [str(pd.Timestamp(x).date()) for x in df["date"].values[a:b + 1]]
        ohlc = [[round(float(df["adj_open"].values[i]), 2), round(float(df["adj_close"].values[i]), 2),
                 round(float(df["adj_low"].values[i]), 2), round(float(df["adj_high"].values[i]), 2)]
                for i in range(a, b + 1)]
        # 该事件所属窗口的阴影区间（个股日历上）
        ws_idx, we_idx = None, None
        etf_dates = pd.Series(etf["date"].values).dt.normalize().values
        for wi, w in enumerate([w for w in etf_weak_windows(etf)[0]]):
            if etf_dates[w["start"]] <= np.datetime64(e["date"]) <= etf_dates[w["end"]]:
                ws_d = str(pd.Timestamp(etf_dates[w["start"]]).date())
                we_d = str(pd.Timestamp(etf_dates[w["end"]]).date())
                ws_idx = dts.index(ws_d) if ws_d in dts else 0
                we_idx = dts.index(we_d) if we_d in dts else len(dts) - 1
                break
        vix_pts = [[d, round(vix_map[d], 2)] for d in dts if d in vix_map]
        gallery.append({
            "pair": e["pair"], "date": e["date"], "cls": e["cls"],
            "dates": dts, "ohlc": ohlc,
            "support": e["support_level"], "support_band_lo": e["support_band_lo"],
            "support_band_hi": e["support_band_hi"], "support_touches": e["support_touches"],
            "entry": round(float(e["entry"]), 2),
            "win_start_idx": ws_idx, "win_end_idx": we_idx,
            "entry_reason": e["entry_reason"],
            "vix": vix_pts, "vix_at_signal": e.get("vix"),
            "fwd5": e.get("fwd5"), "fwd10": e.get("fwd10"), "fwd20": e.get("fwd20"),
            "broken_day": e.get("support_broken_day"),
        })
        picked_pairs.add(e["pair"])

    # ---- 输出 ----
    ev_for_json = []
    for e in sorted(all_events, key=lambda x: x["date"], reverse=True):
        e2 = {k: v for k, v in e.items() if k != "t"}
        ev_for_json.append(e2)

    wsd = pd.DataFrame(window_summary)
    win_agg = {
        "total_windows": len(window_summary),
        "by_etf": {etf: int((wsd["etf"] == etf).sum()) for etf in SECTORS},
        "dur_mean": round(float(wsd["dur"].mean()), 1) if len(wsd) else None,
        "dur_median": round(float(wsd["dur"].median()), 1) if len(wsd) else None,
        "entry_reason": wsd["entry_reason"].value_counts().to_dict() if len(wsd) else {},
        "exit_reason": wsd["exit_reason"].value_counts().to_dict() if len(wsd) else {},
    }

    result = {
        "meta": {
            "window": "2000-01-01 ~ 2026-08-20（XLC 自 2018-06）",
            "sectors": len(SECTORS), "stocks": len(all_tks),
            "total_events_naive": len(all_events),
            "total_events_dedup7d": len(dedup),
            "signal_def": {
                "etf_weak_entry": "EMA10死叉EMA20 OR 收盘连续3日低于EMA20（确认日为窗口起点）",
                "etf_weak_exit": "收盘站回EMA20 OR EMA10金叉EMA20，先到先出",
                "stock_touch": "分形swing-low+ATR聚类(存活>=42日,近42日未破带下沿) 首次回踩入带且收盘守band_lo",
                "entry_price": "触及日收盘",
                "cluster": "同股7交易日内重复触及：naive口径全计，dedup口径只取首次",
            },
        },
        "window_summary": win_agg,
        "event_stats": ev_stats,
        "event_stats_dedup": dd_stats,
        "ctrl_touch_out_stats": ct_stats,
        "ctrl_window_day_stats": cw_stats,
        "baseline_stats": base_stats,
        "classification": {"count": cls, "pct": cls_pct},
        "filters": filters,
        "by_sector": by_sector,
        "stop_grid": grid,
        "pair_meta": pair_meta,
        "missing": missing,
        "events": ev_for_json[:250],
        "gallery": gallery,
    }
    result = clean(result)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "etf_weak_support.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, allow_nan=False)
    rows = [{k: v for k, v in e.items()} for e in all_events]
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "etf_weak_support_events.csv"), index=False, encoding="utf-8-sig")

    # ---- 控制台只打 KPI ----
    print(f"弱势窗口 {win_agg['total_windows']} 个（平均 {win_agg['dur_mean']} 日）| 事件 naive={len(all_events)} dedup7d={len(dedup)}")
    for k in ("1", "5", "10", "20"):
        a, dd, b, cw, base = ev_stats.get(k), dd_stats.get(k), ct_stats.get(k), cw_stats.get(k), base_stats.get(k)
        if not a:
            continue
        print(f"T+{k:>2}: 事件 n={a['n']} 均{a['mean']:+.2f}% 胜率{a['win']:.0f}% DD{a['maxDD_mean']:+.2f}%"
              f" | dedup n={dd['n']} 均{dd['mean']:+.2f}%/{dd['win']:.0f}%"
              f" | 窗外触支撑 n={b['n']} 均{b['mean']:+.2f}%/{b['win']:.0f}%"
              f" | 窗内非触 n={cw['n']} 均{cw['mean']:+.2f}%/{cw['win']:.0f}%"
              f" | 基线 n={base['n']} 均{base['mean']:+.2f}%/{base['win']:.0f}%")
    print("结局占比:", cls_pct, "| 10日击穿率:", filters["break_rate_all"], "%")
    print("written: results/etf_weak_support.json + etf_weak_support_events.csv")


if __name__ == "__main__":
    main()
