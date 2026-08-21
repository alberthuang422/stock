# -*- coding: utf-8 -*-
"""道指板块"跌破上升趋势线" × 龙头股"触及2个月强支撑"共振事件研究

信号定义（显式数字化）：
  A. 板块 ETF 破位：swing low 分形(k=3)取最近2~3个依次抬高低点，
     OLS 拟合上升趋势线（斜率>0、线龄>=42交易日、3点拟合R2>=0.7、
     自第2锚点起收盘未下破线-0.25ATR）→ 当日收盘首次跌破线-0.1ATR。
     同 ETF 10 日冷却合并。
  B. 龙头股支撑触及（分形+ATR聚类法，不用均线）：
     ① swing low 分形(k=3)；② 以 tol=0.75×ATR14 60日中位数做水平聚类；
     ③ 强支撑 = 存活>=42交易日 且自首个锚点+3日后收盘从未跌破带下沿 band_lo；
     ④ 首次回踩：前5日 low>band_hi，当日 low<=band_hi 且 close>=band_lo。
  C. 复合事件 = A 与 B 同日发生。

对照：(a) 仅支撑触及（ETF 同日未破位）
      (b) 仅 ETF 破位（个股同日未触及支撑）
      (c) 个股全部交易日基线

输出：results/djia_sector_support.json（汇总）+ 事件明细 CSV
"""
import os
import json

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

PAIRS = [
    ("XLF", "JPM"), ("XLF", "AXP"), ("XLF", "GS"),
    ("XLK", "MSFT"), ("XLK", "AAPL"), ("XLK", "NVDA"), ("XLK", "CSCO"),
    ("XLI", "CAT"), ("XLI", "HON"), ("XLI", "BA"),
    ("XLV", "UNH"), ("XLV", "JNJ"), ("XLV", "AMGN"), ("XLV", "MRK"),
    ("XLP", "WMT"), ("XLP", "PG"), ("XLP", "KO"),
]

START = pd.Timestamp("2010-01-01")   # 事件扫描起点（数据充分性）
WARM = 260                           # 预热期（均线）
COOLDOWN = 10                        # 同 pair 事件冷却


def load(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk.lower()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]
    # 复权 OHLC（adj 因子缩放）
    f = df["adj_close"] / df["close"]
    df["adj_open"] = df["open"] * f
    df["adj_high"] = df["high"] * f
    df["adj_low"] = df["low"] * f
    return df


def atr_series(df, n=14):
    prev = df["adj_close"].shift(1)
    tr = pd.concat([df["adj_high"] - df["adj_low"],
                    (df["adj_high"] - prev).abs(),
                    (df["adj_low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def swing_lows(lows, k=3):
    """分形低点索引（窗口内严格最小）"""
    idx = []
    for i in range(k, len(lows) - k):
        w = lows[i - k:i + k + 1]
        if lows[i] == w.min() and (w == lows[i]).sum() == 1:
            idx.append(i)
    return idx


def etf_breakdown_days(etf):
    """返回 ETF 的"跌破上升趋势线"交易日集合 {t: 元数据}"""
    df = etf
    n = len(df)
    lows = df["adj_low"].values
    closes = df["adj_close"].values
    atr = atr_series(df).values
    vols = df["volume"].values.astype(float)
    vma20 = pd.Series(vols).rolling(20).mean().values
    dates = df["date"].values

    breaks = {}
    last_ev = -9999
    win = 90          # 回看窗口
    tol_live = 0.25   # 活性容差 ×ATR
    tol_break = 0.10  # 破位判定容差

    for t in range(max(WARM, 60), n):
        if t - last_ev < COOLDOWN:
            continue
        lo = t - win
        sl = [i for i in swing_lows(lows[lo:t])]  # 截至今日前（不含当日）
        sl = [lo + i for i in sl]
        if len(sl) < 2:
            continue
        # 取最近至多3个低点、间隔>=10、价格严格抬升
        chain = []
        for i in reversed(sl):
            if chain and chain[-1] - i < 10:
                continue
            chain.append(i)
            if len(chain) >= 3:
                break
        chain = chain[::-1]
        if len(chain) < 2:
            continue
        pxs = [lows[i] for i in chain]
        if not all(pxs[j + 1] > pxs[j] for j in range(len(pxs) - 1)):
            continue
        # 线龄>=42交易日（约2个月）
        if t - chain[0] < 42:
            continue
        # OLS
        x = np.array(chain, float)
        y = np.array(pxs, float)
        slope, intercept = np.polyfit(x, y, 1)
        if slope <= 0:
            continue
        if len(chain) >= 3:
            yhat = intercept + slope * x
            ss_res = float(((y - yhat) ** 2).sum())
            ss_tot = float(((y - y.mean()) ** 2).sum())
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            if r2 < 0.70:
                continue
        else:
            r2 = 1.0
        # 前一日未破（收盘>=线-0.1ATR）→ 当日为首次跌破
        line_t = slope * t + intercept
        line_prev = slope * (t - 1) + intercept
        if closes[t - 1] < line_prev - tol_break * atr[t - 1]:
            continue
        if closes[t] >= line_t - tol_break * atr[t]:
            continue
        # 活性验证：自第2锚点起至前一日，收盘未连续2日收于线-tol下方
        ok = True
        consec = 0
        for d in range(chain[1] + 1, t):
            lv = slope * d + intercept
            if closes[d] < lv - tol_live * atr[d]:
                consec += 1
                if consec >= 2:
                    ok = False
                    break
            else:
                consec = 0
        if not ok:
            continue
        # 额外：此前2个月为涨势（收盘高于42日前）
        if closes[t] <= closes[t - 42]:
            continue
        breaks[t] = {
            "date": str(pd.Timestamp(dates[t]).date()),
            "line_val": round(float(line_t), 3),
            "line_slope": float(slope),
            "line_intercept": float(intercept),
            "anchors": [[str(pd.Timestamp(dates[i]).date()), round(float(lows[i]), 3)] for i in chain],
            "age_days": int(t - chain[0]),
            "touches": len(chain),
            "r2": round(float(r2), 3),
            "ret_day": round((closes[t] / closes[t - 1] - 1) * 100, 2),
            "vol_ratio": round(float(vols[t] / vma20[t]), 2) if vma20[t] > 0 else None,
        }
        last_ev = t
    return breaks


def stock_support_days(stk):
    """个股"触及>=2个月强支撑"交易日 {t: 元数据}。
    支撑位 = skill 四步法（support-resistance-levels）：
      ① 分形 swing low（左右各3根严格极小值）
      ② ATR 容差水平聚类（tol = 0.75 × ATR14 近60日中位）
      ③ 强支撑 = 自首个分形低点确认起存活>=42交易日（约2个月），
         且期间从未收盘跌破带下沿（band_lo = center − tol）
      ④ 当日首次回踩：近5日 low 均在带上沿之上，当日 low 入带且收盘守住带下沿
    """
    df = stk
    n = len(df)
    lows = df["adj_low"].values
    highs = df["adj_high"].values
    closes = df["adj_close"].values
    opens = df["adj_open"].values
    vols = df["volume"].values.astype(float)
    vma20 = pd.Series(vols).rolling(20).mean().values
    dates = df["date"].values
    atr = atr_series(df).values
    atr_med60 = pd.Series(atr).rolling(60).median().values

    piv = swing_lows(lows, 3)  # 全局分形低点（在 i+3 日确认）

    touches = {}
    lookback = 252  # 候选分形低点回看窗口（约1年）
    for t in range(max(WARM, 100), n):
        am = atr_med60[t - 1]
        if not np.isfinite(am) or am <= 0:
            continue
        tol = 0.75 * am
        # 候选：已确认（i+3 < t）且在回看窗内
        cand = [i for i in piv if i + 3 < t and i >= t - lookback]
        if not cand:
            continue
        # 贪心水平聚类
        cand.sort(key=lambda i: lows[i])
        clusters = []
        for i in cand:
            p = lows[i]
            if clusters and abs(p - clusters[-1]["center"]) <= tol:
                c = clusters[-1]
                c["count"] += 1
                c["center"] = (c["center"] * (c["count"] - 1) + p) / c["count"]
                c["idxs"].append(i)
            else:
                clusters.append({"center": p, "count": 1, "idxs": [i]})
        day_levels = []
        for c in clusters:
            center = c["center"]
            band_lo = center - tol
            band_hi = center + tol
            first = min(c["idxs"])
            age = t - (first + 3)          # 自确认日起的存活交易日
            if age < 42:
                continue                    # 不足2个月
            # 「2个月没有成功下破」= 最近42交易日收盘未跌破带下沿（非整个存活期）
            if (closes[max(first + 3, t - 42):t] < band_lo).any():
                continue                    # 近2个月曾被收盘下破
            if not (lows[t - 5:t] > band_hi).all():
                continue                    # 近5日已贴/入带，非"刚好回踩"
            if lows[t] <= band_hi and closes[t] >= band_lo:
                day_levels.append({
                    "center": center, "band_lo": band_lo, "band_hi": band_hi,
                    "touches": c["count"], "age": int(age), "first_idx": int(first),
                })
        if not day_levels:
            continue
        lv = max(day_levels, key=lambda x: x["touches"])  # 触击次数最多者为主支撑
        rng = highs[t] - lows[t]
        body_lower = min(opens[t], closes[t]) - lows[t]
        touches[t] = {
            "date": str(pd.Timestamp(dates[t]).date()),
            "kinds": [f"分形支撑({lv['touches']}触)"],
            "level": round(float(lv["center"]), 3),
            "band_lo": round(float(lv["band_lo"]), 3),
            "band_hi": round(float(lv["band_hi"]), 3),
            "age": lv["age"],
            "n_levels": len(day_levels),
            "lower_shadow": round(float(body_lower / rng), 2) if rng > 0 else 0.0,
            "vol_ratio": round(float(vols[t] / vma20[t]), 2) if vma20[t] > 0 else 0.0,
            "ret_day": round((closes[t] / closes[t - 1] - 1) * 100, 2),
        }
    return touches


def fwd_stats(rows, closes):
    """对 (t, entry) 列表计算前瞻统计"""
    n_rows = len(closes)
    ks = (1, 5, 10, 20)
    agg = {}
    for k in ks:
        rets, mdd, mxb = [], [], []
        for t, entry in rows:
            if t + k >= n_rows:
                continue
            rets.append((closes[t + k] / entry - 1) * 100)
            lo_win = np.min(closes[t + 1:t + k + 1]) if k >= 1 else entry
            hi_win = np.max(closes[t + 1:t + k + 1]) if k >= 1 else entry
            mdd.append((lo_win / entry - 1) * 100)
            mxb.append((hi_win / entry - 1) * 100)
        if not rets:
            agg[str(k)] = None
            continue
        v = np.array(rets)
        mean = float(v.mean())
        std = float(v.std(ddof=1)) if len(v) > 1 else 0.0
        agg[str(k)] = {
            "n": int(len(v)),
            "mean": round(mean, 2),
            "median": round(float(np.median(v)), 2),
            "win": round(float(np.mean(v > 0)) * 100, 1),
            "std": round(std, 2),
            "p25": round(float(np.percentile(v, 25)), 2),
            "p75": round(float(np.percentile(v, 75)), 2),
            "tstat": round(mean / (std / np.sqrt(len(v))), 2) if std > 0 else None,
            "maxDD_mean": round(float(np.mean(mdd)), 2),
            "maxDD_p10": round(float(np.percentile(mdd, 10)), 2),
            "maxBounce_mean": round(float(np.mean(mxb)), 2),
        }
    return agg


def main():
    cache = {}

    def get(tk):
        if tk not in cache:
            cache[tk] = load(tk)
        return cache[tk]

    spy = get("SPY")
    vix = get("VIX")
    spy_close = spy["adj_close"].values
    spy_ma100 = pd.Series(spy_close).rolling(100).mean().values
    vix_close = vix["close"].values
    spy_idx = {d: i for i, d in enumerate(pd.Series(spy["date"].values).dt.normalize())}
    vix_idx = {d: i for i, d in enumerate(pd.Series(vix["date"].values).dt.normalize())}

    all_events = []
    ctrl_touch = []      # (pair, t, entry)
    ctrl_break = []
    pair_meta = {}
    insufficient = []

    for etf_tk, stk_tk in PAIRS:
        try:
            etf = get(etf_tk)
            stk = get(stk_tk)
        except FileNotFoundError:
            insufficient.append(f"{etf_tk}/{stk_tk}: 数据缺失")
            continue
        # 对齐：以个股日历为主轴，ETF 按日期映射
        etf_idx = {d: i for i, d in enumerate(pd.Series(etf["date"].values).dt.normalize())}
        breaks = etf_breakdown_days(etf)
        touches = stock_support_days(stk)
        closes = stk["adj_close"].values
        dates = pd.Series(stk["date"].values).dt.normalize().values
        n = len(stk)

        etf_closes = etf["adj_close"].values
        etf_dates = pd.Series(etf["date"].values).dt.normalize().values

        pair_events = []
        pair_touch_only = []
        pair_break_only = []
        for t in range(WARM, n):
            d = dates[t]
            ei = etf_idx.get(d)
            is_break = ei is not None and ei in breaks
            is_touch = t in touches
            if is_break and is_touch:
                pair_events.append((t, closes[t], touches[t], breaks[ei], ei))
            elif is_touch:
                pair_touch_only.append((t, closes[t]))
            elif is_break:
                pair_break_only.append((t, closes[t]))

        pair_meta[f"{etf_tk}/{stk_tk}"] = {
            "events": len(pair_events),
            "touch_only": len(pair_touch_only),
            "break_only": len(pair_break_only),
            "range": f"{str(pd.Timestamp(dates[0]).date())}~{str(pd.Timestamp(dates[-1]).date())}",
        }

        for t, entry, tmeta, bmeta, ei in pair_events:
            # 相对强度：个股5日收益 vs ETF 5日收益
            rs5 = None
            if t >= 5 and ei >= 5:
                rs5 = round((closes[t] / closes[t - 5] - etf_closes[ei] / etf_closes[ei - 5]) * 100, 2)
            # 宏观状态（字典精确映射，用事件自身日期）
            ed = dates[t]
            sp = spy_idx.get(ed)
            vx = vix_idx.get(ed)
            spy_above_ma100 = bool(spy_close[sp] > spy_ma100[sp]) if sp is not None and np.isfinite(spy_ma100[sp]) else None
            spy_ret5 = round((spy_close[sp] / spy_close[sp - 5] - 1) * 100, 2) if sp is not None and sp >= 5 else None
            vix_val = round(float(vix_close[vx]), 1) if vx is not None else None

            rec = {
                "pair": f"{etf_tk}/{stk_tk}", "sector": etf_tk, "ticker": stk_tk,
                "date": tmeta["date"], "t": int(t),
                "entry": round(float(entry), 3),
                "support_level": tmeta["level"],
                "support_band_lo": tmeta.get("band_lo"), "support_band_hi": tmeta.get("band_hi"),
                "support_kinds": tmeta["kinds"], "support_age": tmeta["age"],
                "support_touches": tmeta["kinds"][0],
                "lower_shadow": tmeta["lower_shadow"], "stk_vol_ratio": tmeta["vol_ratio"],
                "stk_ret_day": tmeta["ret_day"],
                "etf_ret_day": bmeta["ret_day"], "etf_vol_ratio": bmeta["vol_ratio"],
                "line_age": bmeta["age_days"], "line_r2": bmeta["r2"],
                "line_slope": bmeta.get("line_slope"), "line_intercept": bmeta.get("line_intercept"),
                "line_anchors": bmeta.get("anchors"), "etf_t_index": int(ei),
                "rs5": rs5,
                "spy_above_ma100": spy_above_ma100, "spy_ret5": spy_ret5,
                "vix": vix_val,
            }
            # 前瞻
            for k in (1, 5, 10, 20):
                rec[f"fwd{k}"] = round((closes[t + k] / entry - 1) * 100, 2) if t + k < n else None
            # 支撑击穿（10日内收盘 < 带下沿 band_lo）
            blv = tmeta.get("band_lo", tmeta["level"] * 0.98)
            broken_day = None
            for k2 in range(1, 11):
                if t + k2 < n and closes[t + k2] < blv:
                    broken_day = k2
                    break
            rec["support_broken_day"] = broken_day
            all_events.append(rec)

        ctrl_touch.extend([(stk_tk,) + r for r in pair_touch_only])
        ctrl_break.extend([(stk_tk,) + r for r in pair_break_only])

    # ---- 汇总统计 ----
    def rows_to_fwd(items):
        """items: (tk, t, entry)"""
        out = []
        for it in items:
            tk, t, entry = it[0], it[1], it[2]
            out.append((t, entry, tk))
        return out

    ev_rows = [(e["t"], e["entry"]) for e in all_events]
    # 按个股分组计算（前瞻需各股自身序列）
    def grouped_stats(items):
        # items: (tk, t, entry)
        ks = (1, 5, 10, 20)
        per_k = {str(k): {"rets": [], "mdd": [], "mxb": []} for k in ks}
        for tk, t, entry in items:
            c = cache[tk]["adj_close"].values
            n = len(c)
            for k in ks:
                if t + k >= n:
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

    ev_stats = grouped_stats([(e["ticker"], e["t"], e["entry"]) for e in all_events])
    ct_stats = grouped_stats(ctrl_touch)
    cb_stats = grouped_stats(ctrl_break)
    # 基线：全部 pair 个股的全部交易日（抽样每5日以控内存）
    baseline_items = []
    for tk in sorted({p[1] for p in PAIRS}):
        c = cache[tk]["adj_close"].values
        for t in range(WARM, len(c) - 20, 3):
            baseline_items.append((tk, t, c[t]))
    base_stats = grouped_stats(baseline_items)

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
        if e["support_broken_day"] is not None or f5 is not None and f5 < -4:
            cls["支撑击穿"] += 1
            e["cls"] = "支撑击穿"
        elif hi10 is not None and hi10 >= 2 and (f10 <= 0 or f20 < -1):
            cls["死猫反弹"] += 1
            e["cls"] = "死猫反弹"
        elif f5 is not None and f5 > 0 and f20 > 0 and lo5 > -5:
            cls["V型反转"] += 1
            e["cls"] = "V型反转"
        else:
            cls["横盘消化"] += 1
            e["cls"] = "横盘消化"
    cls_total = sum(v for k, v in cls.items() if k != "未完整")
    cls_pct = {k: round(v / cls_total * 100, 1) for k, v in cls.items()} if cls_total else {}

    # ---- 过滤条件 ----
    def subset_stats(pred):
        sel = [(e["ticker"], e["t"], e["entry"]) for e in all_events if pred(e)]
        return grouped_stats(sel) if sel else None, len(sel)

    filters = {}
    # 1) ETF 破位日量能
    filters["etf_vol"] = {}
    for name, lo, hi in (("缩量(<0.8)", 0, 0.8), ("平量(0.8-1.5)", 0.8, 1.5), ("放量(>=1.5)", 1.5, 99)):
        s, n_sel = subset_stats(lambda e: e["etf_vol_ratio"] is not None and lo <= e["etf_vol_ratio"] < hi)
        filters["etf_vol"][name] = {"n": n_sel, "stats": s}
    # 2) 个股止跌形态：下影线占比>=0.3；个股缩量（量比<=1.0）
    s, n_sel = subset_stats(lambda e: e["lower_shadow"] >= 0.3)
    filters["stk_shadow"] = {"n": n_sel, "stats": s}
    s, n_sel = subset_stats(lambda e: e["lower_shadow"] < 0.3)
    filters["stk_no_shadow"] = {"n": n_sel, "stats": s}
    s, n_sel = subset_stats(lambda e: e["stk_vol_ratio"] is not None and e["stk_vol_ratio"] <= 1.0)
    filters["stk_low_vol"] = {"n": n_sel, "stats": s}
    s, n_sel = subset_stats(lambda e: e["stk_vol_ratio"] is not None and e["stk_vol_ratio"] > 1.0)
    filters["stk_high_vol"] = {"n": n_sel, "stats": s}
    # 3) RS：个股5日相对ETF
    filters["rs"] = {}
    for name, lo, hi in (("强于板块(RS>=0)", 0, 99), ("弱于板块(RS<0)", -99, 0)):
        s, n_sel = subset_stats(lambda e: e["rs5"] is not None and lo <= e["rs5"] < hi)
        filters["rs"][name] = {"n": n_sel, "stats": s}
    # 4) 宏观
    filters["macro"] = {}
    for name, pred in (
        ("SPY在MA100上方", lambda e: e["spy_above_ma100"] is True),
        ("SPY在MA100下方", lambda e: e["spy_above_ma100"] is False),
        ("SPY5日跌>3%(市场急跌)", lambda e: e["spy_ret5"] is not None and e["spy_ret5"] < -3),
        ("VIX<20", lambda e: e["vix"] is not None and e["vix"] < 20),
        ("VIX 20-30", lambda e: e["vix"] is not None and 20 <= e["vix"] < 30),
        ("VIX>=30(恐慌)", lambda e: e["vix"] is not None and e["vix"] >= 30),
    ):
        s, n_sel = subset_stats(pred)
        # 支撑击穿率
        sel = [e for e in all_events if pred(e)]
        br = [e for e in sel if e["support_broken_day"] is not None]
        filters["macro"][name] = {
            "n": n_sel, "stats": s,
            "break_rate": round(len(br) / len(sel) * 100, 1) if sel else None,
        }
    # 全样本击穿率
    br_all = [e for e in all_events if e["support_broken_day"] is not None]
    filters["break_rate_all"] = round(len(br_all) / len(all_events) * 100, 1) if all_events else None

    # ---- 止损/止盈网格 ----
    def simulate(stop_x, tp_pct, max_hold=20):
        """entry=信号日收盘；止损=支撑*(1-x)，盘中触及按止损价成交（跳空按开盘）；
        止盈=entry*(1+tp)，收盘达到次日出；超时按持有期末收盘"""
        rets = []
        for e in all_events:
            tk, t, entry = e["ticker"], e["t"], e["entry"]
            df = cache[tk]
            c, o, lo, hi = df["adj_close"].values, df["adj_open"].values, df["adj_low"].values, df["adj_high"].values
            lvl = df["adj_close"].values[t]  # placeholder
            # 支撑位取 meta level
            lvl = e["_level"]
            stop = lvl * (1 - stop_x)
            tp = entry * (1 + tp_pct) if tp_pct else None
            exit_ret = None
            n = len(c)
            for k in range(1, max_hold + 1):
                if t + k >= n:
                    break
                tt = t + k
                if lo[tt] <= stop:
                    px = min(o[tt], stop)  # 跳空劣化
                    exit_ret = (px / entry - 1) * 100
                    break
                if tp is not None and c[tt] >= tp:
                    exit_ret = (tp / entry - 1) * 100
                    break
            if exit_ret is None and t + max_hold < n:
                exit_ret = (c[t + max_hold] / entry - 1) * 100
            if exit_ret is not None:
                rets.append(exit_ret)
        v = np.array(rets)
        if len(v) == 0:
            return None
        return {"n": int(len(v)), "mean": round(float(v.mean()), 2),
                "median": round(float(np.median(v)), 2),
                "win": round(float(np.mean(v > 0)) * 100, 1)}

    for e in all_events:
        # 止损基准：支撑带下沿 band_lo（新口径，分形聚类法）；缺失时退化为支撑中值
        e["_level"] = e.get("support_band_lo") or e.get("support_level", e["entry"])
    grid = {}
    for sx in (0.005, 0.01, 0.02, 0.03):
        for tp in (0.05, 0.10, None):
            key = f"stop{int(sx*1000)/10}%/tp{int(tp*100) if tp else 'hold'}%"
            grid[key] = simulate(sx, tp)

    # ---- 输出 ----
    # 清洗 numpy 类型
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

    ev_for_json = []
    for e in sorted(all_events, key=lambda x: x["date"], reverse=True):
        e2 = {k: v for k, v in e.items() if k not in ("t", "_level")}
        ev_for_json.append(e2)

    # ---- K 线画廊：代表性事件的 OHLC + ETF 趋势线 + VIX ----
    # 每板块取 V反/击穿 各 1（不足则用其它结局补足），上限 10 张
    vix_map = {str(pd.Timestamp(d).date()): float(c)
               for d, c in zip(vix["date"].values, vix["close"].values)}
    gallery = []
    picked = set()
    wanted_cls = ("V型反转", "支撑击穿", "死猫反弹", "横盘消化")
    for etf_tk in ("XLI", "XLK", "XLV", "XLF", "XLP"):
        for want_c in wanted_cls:
            cands = [e for e in all_events if e["sector"] == etf_tk and e.get("cls") == want_c
                     and e["pair"] not in picked and e.get("line_anchors")]
            if not cands:
                continue
            e = max(cands, key=lambda x: x["date"])
            picked.add(e["pair"])
            tk, t = e["ticker"], e["t"]
            df = cache[tk]
            etf = cache[etf_tk]
            a = max(0, t - 55)
            b = min(len(df) - 1, t + 22)
            dts = [str(pd.Timestamp(x).date()) for x in df["date"].values[a:b + 1]]
            ohlc = [[round(float(df["adj_open"].values[i]), 2), round(float(df["adj_close"].values[i]), 2),
                     round(float(df["adj_low"].values[i]), 2), round(float(df["adj_high"].values[i]), 2)]
                    for i in range(a, b + 1)]
            vol = [int(df["volume"].values[i]) for i in range(a, b + 1)]
            ma50 = pd.Series(df["adj_close"].values).rolling(50).mean().values
            ma100 = pd.Series(df["adj_close"].values).rolling(100).mean().values
            ma200 = pd.Series(df["adj_close"].values).rolling(200).mean().values
            ma = lambda arr: [round(float(arr[i]), 2) if np.isfinite(arr[i]) else None for i in range(a, b + 1)]
            # ETF 趋势线 + ETF 收盘序列（同日历窗口）
            line_pts = []
            etf_close_pts = []
            slope, intercept = e["line_slope"], e["line_intercept"]
            ei0 = e["etf_t_index"]
            for i in range(max(0, ei0 - 60), min(len(etf), ei0 + 23)):
                d_i = str(pd.Timestamp(etf["date"].values[i]).date())
                if d_i in dts:
                    etf_close_pts.append([d_i, round(float(etf["adj_close"].values[i]), 3)])
                    if i <= ei0 + 3:
                        line_pts.append([d_i, round(float(slope * i + intercept), 3)])
            # VIX 序列（同日历窗口）
            vix_pts = [[d, round(vix_map[d], 2)] for d in dts if d in vix_map]
            gallery.append({
                "pair": e["pair"], "date": e["date"], "cls": e["cls"],
                "dates": dts, "ohlc": ohlc, "vol": vol,
                "ma50": ma(ma50), "ma100": ma(ma100), "ma200": ma(ma200),
                "support": round(float(e["support_level"]), 2),
                "support_band_lo": e.get("support_band_lo"),
                "support_band_hi": e.get("support_band_hi"),
                "support_touches": e.get("support_touches"),
                "support_kinds": e["support_kinds"],
                "entry": round(float(e["entry"]), 2),
                "etf_close": etf_close_pts,
                "etf_line": line_pts,
                "vix": vix_pts,
                "etf_break_date": e["date"],
                "etf_ret_day": e.get("etf_ret_day"),
                "etf_vol_ratio": e.get("etf_vol_ratio"),
                "stk_ret_day": e.get("stk_ret_day"),
                "vix_at_signal": e.get("vix"),
                "fwd5": e.get("fwd5"), "fwd10": e.get("fwd10"), "fwd20": e.get("fwd20"),
                "broken_day": e.get("support_broken_day"),
            })
            if len([g for g in gallery if g["pair"]]) >= 10:
                break
        if len(gallery) >= 10:
            break

    result = {
        "meta": {
            "window": "1995-01-03 ~ 2026-08-20（事件自预热期后起，实际最早 2000）",
            "pairs": len(PAIRS),
            "total_events": len(all_events),
            "signal_def": {
                "etf_break": "swing-low分形+OLS上升趋势线(线龄>=42日,斜率>0,3点R2>=0.7,未破) 首次收盘跌破线-0.1ATR",
                "stock_touch": "分形swing-low+ATR聚类(存活>=42日,未破带下沿) 首次回踩至支撑带[band_lo,band_hi]内且收盘守住band_lo",
            },
        },
        "pair_meta": pair_meta,
        "event_stats": ev_stats,
        "ctrl_touch_stats": ct_stats,
        "ctrl_break_stats": cb_stats,
        "baseline_stats": base_stats,
        "classification": {"count": cls, "pct": cls_pct},
        "filters": filters,
        "stop_grid": grid,
        "insufficient": insufficient,
        "events": ev_for_json[:200],
        "gallery": gallery,
    }
    result = clean(result)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "djia_sector_support.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, allow_nan=False)

    # 明细 CSV
    rows = [{k: v for k, v in e.items() if k not in ("_level",)} for e in all_events]
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "djia_sector_support_events.csv"), index=False, encoding="utf-8-sig")

    # ---- 控制台只打印汇总 ----
    print(f"总事件 {len(all_events)}  | pair 明细: " + ", ".join(f"{k}={v['events']}" for k, v in pair_meta.items()))
    for k in ("1", "5", "10", "20"):
        a, b, c_, d = ev_stats.get(k), ct_stats.get(k), cb_stats.get(k), base_stats.get(k)
        if not a:
            continue
        print(f"T+{k:>2}: 共振 n={a['n']} 均{a['mean']:+.2f}% 胜率{a['win']:.0f}% DD{a['maxDD_mean']:+.2f}%"
              f" | 仅支撑 n={b['n']} 均{b['mean']:+.2f}% 胜率{b['win']:.0f}%"
              f" | 仅破位 n={c_['n']} 均{c_['mean']:+.2f}% 胜率{c_['win']:.0f}%"
              f" | 基线 n={d['n']} 均{d['mean']:+.2f}% 胜率{d['win']:.0f}%")
    print("结局分类占比:", cls_pct)
    print("全样本10日支撑击穿率:", filters["break_rate_all"], "%")
    print("written: results/djia_sector_support.json + events.csv")


if __name__ == "__main__":
    main()
