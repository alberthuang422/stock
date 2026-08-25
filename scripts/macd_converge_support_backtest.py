# -*- coding: utf-8 -*-
"""事件研究：蓝筹股「日线区间下沿触达 × 周线MACD能量柱收敛」分组对照

严格无前视：所有指标只用事件日及其之前的数据计算（日线区间用 [t-20,t-1] 窗、
周线 MACD 用已完成周序列 + 当周 to-date 值递推）。

事件定义（沿用报告31的日线区间逻辑 + 新增周线MACD条件）
--------
1) 震荡区间（日线，复权价）：
   - 事件日前20个交易日观察窗（不含事件日）；窗内收盘相对日线EMA20交替穿叉、
     最近一次穿叉距事件日<=10日、振幅 max(H)/min(L)-1 <= 35%；
   - 该震荡状态连续维持 >= 20 交易日；
   - 下沿 lower = 窗内 min(低点)，上沿 upper = max(高点)，中轨 mid=(lower+upper)/2。
2) 日线触达：事件日收盘 <= lower * (1 + 0.5%)。
3) 周线条件（当周周线=本周迄今收盘，MACD 12/26/9，能量柱 = DIF - DEA）：
   - hist_cur = 当周柱；hist_prev1 = 上周柱；hist_prev2 = 上上周柱（均当日已知）
   - 收敛 CVG：hist_prev2 > 0 且 hist_prev2 > hist_prev1 > hist_cur
     （能量柱至少3根逐周递减，起点在水上；是否已回水下不设限）
   - 对照组：
     POS = 当周柱 > 0 且 非CVG（水上扩张/其他）
     NEG = 当周柱 <= 0 且 非CVG（水下）
4) 事件日 = 日线触达 且 周线条件同日成立；同一触达连续段内只保留首次，
   事件之间最少间隔 10 交易日。

度量（事件后 T ∈ {5,10,20,60} 交易日，收盘复权价）
----
- fwdN：个股收益%；excN：个股 − SPY 同窗收益%（交易日对齐）
- 破位率：T日内收盘最低 < lower*0.98
- 触中轨天数、20日最大回撤
- CVG 组内再分「仍在水上 / 已回水下」；SPY 前20日环境分层；事件聚集统计

输出：macd_support_events.csv（逐事件）+ macd_support_stats.json（分组统计）
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
)
OUT_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()

UNIVERSE = [
    "ko", "brk.b", "jnj", "mcd", "pg", "pep", "cnp", "lnt", "xel", "mo",
    "trv", "wmt", "vz", "etr", "hon", "sre", "v", "pm", "abbv", "ma",
    "amgn", "jpm", "hd", "gild", "mrk", "cvx", "csco", "xom", "nee", "shw",
    "blk", "tmo", "aapl", "msft", "gs", "mmm", "ms", "vrtx", "dhr", "axp",
    "dis", "ibm", "trow", "ge", "regn", "sbux", "cat",
]
# 周线MACD参数
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9

# 事件参数（与报告31一致）
RANGE_DAYS = 20          # 观察窗
MIN_RUN = 20             # 区间最短维持交易日
MAX_AMP = 0.35           # 区间振幅上限
LAST_CROSS_DAYS = 10     # 最近一次穿叉距事件日的上限
TOUCH_TOL = 0.005        # 触达容差 0.5%
BREAK_MULT = 0.98        # 破位阈值：跌破下沿 2%
MIN_COOLDOWN = 10        # 事件间最小间隔（交易日）
DAILY_MIN_IDX = 80       # 日线EMA20收敛 + 观察窗
WEEK_MIN_POS = 60        # 周线EMA/MACD平稳（周数）
HORIZONS = [5, 10, 20, 60]
MDD_DAYS = 20
MID_LOOKBACK = 60        # 触中轨观察窗口

GROUP_CVG, GROUP_POS, GROUP_NEG = "CVG", "POS", "NEG"
GROUP_DESC = {
    "CVG": "周线MACD柱收敛(>=3根递减,起点水上)+触支撑",
    "POS": "当周柱水上(非收敛)+触支撑",
    "NEG": "当周柱水下(非收敛)+触支撑",
}


def load_daily(symbol):
    path = os.path.join(DATA_DIR, symbol, f"{symbol}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    if "adj_close" not in df.columns or df["adj_close"].isna().all():
        df["adj_close"] = df["close"]
    ratio = df["adj_close"] / df["close"]
    for col in ("open", "high", "low"):
        df[col] = df[col] * ratio
    df["close"] = df["adj_close"]
    return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def load_daily_map():
    """symbol -> daily DataFrame（含复权OHLC）"""
    out = {}
    for sym in UNIVERSE:
        try:
            out[sym] = load_daily(sym)
        except Exception as e:
            print(f"  WARN {sym}: {e}")
    return out


def compute_daily_state(df):
    n = len(df)
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    ema20 = pd.Series(close).ewm(span=20, adjust=False).mean().values

    cross_dir = np.zeros(n, dtype=int)
    for i in range(1, n):
        if close[i - 1] <= ema20[i - 1] and close[i] > ema20[i]:
            cross_dir[i] = 1
        elif close[i - 1] >= ema20[i - 1] and close[i] < ema20[i]:
            cross_dir[i] = -1

    qualify = np.zeros(n, dtype=bool)
    lower = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    mid = np.full(n, np.nan)
    amp = np.full(n, np.nan)

    for t in range(RANGE_DAYS, n):
        s = t - RANGE_DAYS
        w = slice(s, t)
        lo, hi = low[w].min(), high[w].max()
        if lo <= 0 or hi / lo - 1 > MAX_AMP:
            continue
        idx = np.where(cross_dir[s:t] != 0)[0] + s
        if len(idx) < 2:
            continue
        dirs = cross_dir[idx]
        if not (dirs.max() > 0 and dirs.min() < 0):
            continue
        if np.any(dirs[1:] == dirs[:-1]):
            continue
        if idx[-1] < t - LAST_CROSS_DAYS:
            continue
        qualify[t] = True
        lower[t], upper[t] = lo, hi
        mid[t] = (lo + hi) / 2.0
        amp[t] = (hi / lo - 1.0) * 100.0
    return close, qualify, lower, upper, mid, amp


def compute_weekly_macd(df):
    """无前视周线MACD：已完成周序列的EMA + 当周(含今日)值递推。
    返回 dict: week_pos[i]周序号, hist_cur[i], hist_prev1[i], hist_prev2[i],
    ema20_w[i], ema50_w[i], suppress[i], deathcross[i]"""
    close = df["close"].values
    n = len(df)
    period = df["date"].dt.to_period("W-FRI")
    wk = pd.DataFrame({"period": period, "close": close})
    weekly_last = wk.groupby("period")["close"].last()

    # 已完成周序列的 EMA（含当前周，因为 that 序列最后一根就是当前周的 close）
    ema12_w = weekly_last.ewm(span=MACD_FAST, adjust=False).mean()
    ema26_w = weekly_last.ewm(span=MACD_SLOW, adjust=False).mean()
    dif_series = ema12_w - ema26_w
    dea_series = dif_series.ewm(span=MACD_SIGNAL, adjust=False).mean()
    hist_series = dif_series - dea_series
    e20_w = weekly_last.ewm(span=20, adjust=False).mean()
    e50_w = weekly_last.ewm(span=50, adjust=False).mean()

    pos_map = {p: i for i, p in enumerate(weekly_last.index)}
    hist_all = hist_series.values  # 已完成周序列的 hist（numpy，index=周序号）
    a12, a26, a9 = 2.0 / (MACD_FAST + 1), 2.0 / (MACD_SLOW + 1), 2.0 / (MACD_SIGNAL + 1)
    a20, a50 = 2.0 / 21.0, 2.0 / 51.0

    week_pos = np.full(n, -1, dtype=int)
    hist_cur = np.full(n, np.nan)
    hist_prev1 = np.full(n, np.nan)
    hist_prev2 = np.full(n, np.nan)
    ema20_w_a = np.full(n, np.nan)
    ema50_w_a = np.full(n, np.nan)
    suppress = np.zeros(n, dtype=bool)
    deathcross = np.zeros(n, dtype=bool)

    def hist_at(pos):
        """周序号 pos 的 hist（电流当周则用已完成周序列，非当周直接用序列值）；pos 越界返回 nan"""
        if pos < 0 or pos >= len(hist_all):
            return np.nan
        return float(hist_all[pos])

    for i in range(n):
        p = period.iloc[i]
        pos = pos_map.get(p, -1)
        if pos < 2:
            continue
        week_pos[i] = pos
        # 当周值递推（只用前一周完成的 EMA 状态 + 本周 close）
        c = close[i]
        dif = (a12 * c + (1 - a12) * ema12_w.iloc[pos - 1]) - \
              (a26 * c + (1 - a26) * ema26_w.iloc[pos - 1])
        dea = a9 * dif + (1 - a9) * dea_series.iloc[pos - 1]
        hist_cur[i] = dif - dea
        hist_prev1[i] = hist_at(pos - 1)
        hist_prev2[i] = hist_at(pos - 2)
        e20_prev = e20_w.iloc[pos - 1]
        e50_prev = e50_w.iloc[pos - 1]
        ema20_w_a[i] = a20 * c + (1 - a20) * e20_prev
        ema50_w_a[i] = a50 * c + (1 - a50) * e50_prev
        suppress[i] = c < ema20_w_a[i]
        deathcross[i] = ema20_w_a[i] <= ema50_w_a[i]
    return week_pos, hist_cur, hist_prev1, hist_prev2, hist_series, ema20_w_a, ema50_w_a, suppress, deathcross


def detect_events(df, close, qualify, lower, upper, mid, amp,
                  week_pos, hc, hp1, hp2, hist_series, e20w, e50w, suppress, deathcross):
    n = len(df)
    events = []
    last_event = -10 ** 9
    run_start = None
    hist_all = hist_series.values
    for t in range(RANGE_DAYS, n):
        if qualify[t]:
            if run_start is None:
                run_start = t
            run_len = t - run_start + 1
        else:
            run_start = None
            continue
        if run_len < MIN_RUN:
            continue
        if t < DAILY_MIN_IDX or week_pos[t] < WEEK_MIN_POS:
            continue
        if t - last_event < MIN_COOLDOWN:
            continue
        if not (close[t] <= lower[t] * (1 + TOUCH_TOL)):
            continue
        hc_v, hp1_v, hp2_v = hc[t], hp1[t], hp2[t]
        if not (math.isfinite(hc_v) and math.isfinite(hp1_v) and math.isfinite(hp2_v)):
            continue
        # 分组
        if hp2_v > 0 and hp1_v < hp2_v and hc_v < hp1_v:
            group = GROUP_CVG
        elif hc_v > 0:
            group = GROUP_POS
        else:
            group = GROUP_NEG
        # 连续递减根数（从当周向前数，含当周）：更早的柱 > 更近的柱 即为递减段
        pos_w = week_pos[t]
        k = 0
        prev_h = hc_v
        growing = True
        j = 1
        while growing:
            h = hist_at_if(hist_all, pos_w - j)
            if math.isnan(h):
                break
            if h > prev_h:
                k += 1
                prev_h = h
                j += 1
            else:
                growing = False
        # k = 当前柱往前连续递减的根数（不含当前柱）；总收敛长度 = k+1
        conv_len = int(k + 1)
        events.append({
            "symbol": df["symbol"][0],
            "event_date": df["date"][t].strftime("%Y-%m-%d"),
            "t": t,
            "group": group,
            "close": float(close[t]),
            "lower": float(lower[t]),
            "upper": float(upper[t]),
            "mid": float(mid[t]),
            "amp_pct": float(amp[t]),
            "hist_cur": float(hc_v),
            "hist_prev1": float(hp1_v),
            "hist_prev2": float(hp2_v),
            "conv_len": conv_len,
            "suppress_w": bool(suppress[t]),
            "deathcross_w": bool(deathcross[t]),
            "ema20_w": float(e20w[t]),
            "ema50_w": float(e50w[t]),
        })
        last_event = t
    return events


def hist_at_if(hist_all, pos):
    if pos < 0 or pos >= len(hist_all):
        return np.nan
    return float(hist_all[pos])


def fwd_metrics(df, ev, close, spy_close_by_date, spy_dateset):
    """事件后度量；个股相对收益 + SPY 超额（交易日对齐）。返回 dict。"""
    n = len(df)
    t = ev["t"]
    lower = ev["lower"]
    mid = ev["mid"]
    out = {}
    ev_date = df["date"][t]
    # SPY 中事件日的位次（用日期索引，避免两个市场交易日不一致）
    spy_pos = None
    if ev_date in spy_dateset:
        spy_pos = spy_dateset[ev_date]
    for T in HORIZONS:
        if t + T < n:
            out[f"fwd{T}"] = (close[t + T] / close[t] - 1.0) * 100.0
            out[f"fwd{T}_date"] = df["date"][t + T].strftime("%Y-%m-%d")
        else:
            out[f"fwd{T}"] = None
            out[f"fwd{T}_date"] = None
        # SPY 超额：与个股同结束日对齐
        if spy_pos is not None and spy_pos + T < len(spy_close_by_date):
            if t + T < n:
                s0 = spy_close_by_date[spy_pos]
                s1 = spy_close_by_date[spy_pos + T]
                if s0 > 0 and math.isfinite(s0) and math.isfinite(s1):
                    out[f"exc{T}"] = (s1 / s0 - 1.0) * 100.0
                else:
                    out[f"exc{T}"] = None
            else:
                out[f"exc{T}"] = None
        else:
            out[f"exc{T}"] = None
        if out[f"fwd{T}"] is not None and out[f"exc{T}"] is not None:
            out[f"exc{T}"] = out[f"fwd{T}"] - out[f"exc{T}"]
        # 破位率
        end = min(t + T, n - 1)
        if end >= t + 1:
            w = close[t + 1:end + 1]
            out[f"broken{T}"] = int(bool((w < lower * BREAK_MULT).any()))
        else:
            out[f"broken{T}"] = None
    # 触中轨天数
    days_to_mid = None
    for k in range(1, MID_LOOKBACK + 1):
        if t + k >= n:
            break
        if close[t + k] >= mid:
            days_to_mid = k
            break
    out["days_to_mid"] = days_to_mid
    # 20日最大回撤
    end = min(t + MDD_DAYS, n - 1)
    w = close[t + 1:end + 1]
    if len(w) >= 2:
        peak = w[0]
        mdd = 0.0
        for c in w[1:]:
            if c > peak:
                peak = c
            if peak > 0:
                mdd = max(mdd, (peak - c) / peak)
        out["mdd20_pct"] = mdd * 100.0
    else:
        out["mdd20_pct"] = None
    # SPY 环境：事件日前20日 SPY 收益
    if spy_pos is not None and spy_pos - 20 >= 0:
        s0 = spy_close_by_date[spy_pos - 20]
        s1 = spy_close_by_date[spy_pos]
        if s0 > 0:
            out["spy_pre20"] = (s1 / s0 - 1.0) * 100.0
        else:
            out["spy_pre20"] = None
    else:
        out["spy_pre20"] = None
    return out


def t_one_sample(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 3 or np.std(x, ddof=1) == 0:
        return None
    return float(np.mean(x) / (np.std(x, ddof=1) / np.sqrt(len(x))))


def t_two_sample(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    if len(x) < 3 or len(y) < 3:
        return None
    vx, vy = np.var(x, ddof=1), np.var(y, ddof=1)
    if vx == 0 and vy == 0:
        return None
    se = math.sqrt(vx / len(x) + vy / len(y))
    if se == 0:
        return None
    return float((np.mean(x) - np.mean(y)) / se)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        f = float(o)
        return f if math.isfinite(f) else None
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    return o


def main():
    dailies = load_daily_map()
    # SPY
    spy = load_daily("spy")
    spy_close = spy["close"].values
    spy_date_set = {d: i for i, d in enumerate(spy["date"])}

    all_events = []
    per_symbol = {}
    for sym, df in dailies.items():
        df["symbol"] = sym
        close, qualify, lower, upper, mid, amp = compute_daily_state(df)
        wk = compute_weekly_macd(df)
        evs = detect_events(df, close, qualify, lower, upper, mid, amp, *wk)
        for ev in evs:
            m = fwd_metrics(df, ev, close, spy_close, spy_date_set)
            ev.update(m)
            all_events.append(ev)
        per_symbol[sym] = len(evs)
        print(f"  {sym:>9s}: {len(evs):3d} events")

    ev_df = pd.DataFrame(all_events)
    ev_df = ev_df.drop(columns=["t"])
    col_order = ["symbol", "event_date", "group", "close", "lower", "upper", "mid",
                 "amp_pct", "hist_cur", "hist_prev1", "hist_prev2", "conv_len",
                 "suppress_w", "deathcross_w", "ema20_w", "ema50_w", "days_to_mid",
                 "mdd20_pct", "spy_pre20"] + \
                [c for T in HORIZONS for c in (f"fwd{T}", f"exc{T}", f"fwd{T}_date")] + \
                [f"broken{T}" for T in HORIZONS]
    ev_df = ev_df[col_order]
    ev_csv = os.path.join(OUT_DIR, "macd_support_events.csv")
    ev_df.to_csv(ev_csv, index=False, encoding="utf-8")

    # ---------------- 统计 ----------------
    ev_df["year"] = ev_df["event_date"].str[:4]
    stats = {"n_total": len(all_events), "per_symbol": per_symbol,
             "group_desc": GROUP_DESC, "horizons": HORIZONS,
             "params": {"macd": [MACD_FAST, MACD_SLOW, MACD_SIGNAL],
                        "conv_len": 3, "conv_start_positive": True}}
    g2df = {g: ev_df[ev_df["group"] == g] for g in (GROUP_CVG, GROUP_POS, GROUP_NEG)}
    stats["n_group"] = {g: int(len(d)) for g, d in g2df.items()}

    # 1) horizon 统计（绝对 + 超额）
    horizon_stats = {}
    for T in HORIZONS:
        fcol, ecol, bcol = f"fwd{T}", f"exc{T}", f"broken{T}"
        row = {}
        for g, d in g2df.items():
            f = d[fcol].dropna()
            e = d[ecol].dropna()
            b = d[bcol].dropna()
            row[g] = {
                "n": int(len(f)),
                "mean": float(f.mean()) if len(f) else None,
                "median": float(f.median()) if len(f) else None,
                "win_rate": float((f > 0).mean() * 100) if len(f) else None,
                "exc_mean": float(e.mean()) if len(e) else None,
                "exc_median": float(e.median()) if len(e) else None,
                "exc_win_rate": float((e > 0).mean() * 100) if len(e) else None,
                "broken_rate": float(b.mean() * 100) if len(b) else None,
                "t_one": t_one_sample(f.values),
                "n_broken": int(int(b.sum())) if len(b) else None,
            }
        row["ttest"] = {
            "CVG_vs_POS": t_two_sample(g2df[GROUP_CVG][fcol].dropna().values,
                                        g2df[GROUP_POS][fcol].dropna().values),
            "CVG_vs_NEG": t_two_sample(g2df[GROUP_CVG][fcol].dropna().values,
                                       g2df[GROUP_NEG][fcol].dropna().values),
        }
        horizon_stats[T] = row
    stats["horizon"] = horizon_stats

    # 2) CVG 内部：仍在水上 vs 已回水下（当周柱 <= 0）
    cvg = g2df[GROUP_CVG].copy()
    cvg["in_water"] = cvg["hist_cur"] > 0
    cvg_sub = {}
    for label, sub in (("水上", cvg[cvg["in_water"]]), ("已回水下", cvg[~cvg["in_water"]])):
        d = {"n": int(len(sub))}
        for T in HORIZONS:
            f = sub[f"fwd{T}"].dropna()
            e = sub[f"exc{T}"].dropna()
            b = sub[f"broken{T}"].dropna()
            d[f"T{T}"] = {
                "mean": float(f.mean()) if len(f) else None,
                "median": float(f.median()) if len(f) else None,
                "win_rate": float((f > 0).mean() * 100) if len(f) else None,
                "exc_mean": float(e.mean()) if len(e) else None,
                "broken_rate": float(b.mean() * 100) if len(b) else None,
            }
        cvg_sub[label] = d
    stats["cvg_sub"] = cvg_sub

    # 3) 环境分层（SPY 前20日）
    env_buckets = [(-999, -5, "<-5% 深跌"), (-5, -1, "-5~-1% 回调"),
                   (-1, 1, "-1~+1% 震荡"), (1, 999, ">+1% 上行")]
    env_stats = {}
    for g, d in g2df.items():
        rows = []
        for lo, hi, name in env_buckets:
            sub = d[(d["spy_pre20"].fillna(-999) >= lo) & (d["spy_pre20"].fillna(999) < hi)]
            f = sub["fwd20"].dropna()
            e = sub["exc20"].dropna()
            b = sub["broken20"].dropna()
            rows.append({
                "bucket": name,
                "n": int(len(f)),
                "mean_fwd20": float(f.mean()) if len(f) else None,
                "exc_mean": float(e.mean()) if len(e) else None,
                "win_rate": float((f > 0).mean() * 100) if len(f) else None,
                "broken_rate": float(b.mean() * 100) if len(b) else None,
            })
        env_stats[g] = rows
    stats["env20"] = env_stats

    # 4) 年份分布
    stats["year"] = {g: d.groupby("year").size().to_dict() for g, d in g2df.items()}

    # 5) 事件聚集：同日 >= 3 股
    date_cnt = ev_df.groupby("event_date").size()
    clustered = int((date_cnt >= 3).sum())
    total_days = int(len(date_cnt))
    cluster_ev = int(ev_df["event_date"].isin(date_cnt[date_cnt >= 3].index).sum())
    stats["clustering"] = {
        "event_days": total_days,
        "days_ge3": clustered,
        "pct_days_ge3": float(clustered / total_days * 100) if total_days else None,
        "events_in_ge3_days": cluster_ev,
        "pct_events_in_ge3_days": float(cluster_ev / len(ev_df) * 100) if len(ev_df) else None,
    }

    # 6) fwd20 分布分位
    dist = {}
    for g, d in g2df.items():
        f = d["fwd20"].dropna()
        dist[g] = {
            "p10": float(f.quantile(0.10)) if len(f) else None,
            "p25": float(f.quantile(0.25)) if len(f) else None,
            "p75": float(f.quantile(0.75)) if len(f) else None,
            "p90": float(f.quantile(0.90)) if len(f) else None,
        }
    stats["fwd20_dist"] = dist

    with open(os.path.join(OUT_DIR, "macd_support_stats.json"), "w",
              encoding="utf-8") as f:
        json.dump(clean(stats), f, ensure_ascii=False, indent=1)

    # ---------------- 控制台汇总 ----------------
    print(f"\n总事件数: {len(all_events)}")
    for g in (GROUP_CVG, GROUP_POS, GROUP_NEG):
        print(f"  {g}({GROUP_DESC[g]}): {stats['n_group'][g]}")
    print("\nT 对比 (n / 均值% / 中位% / 胜率% / 超额均值% / 破位率%):")
    for T in HORIZONS:
        r = horizon_stats[T]
        line = [f"T+{T}"]
        for g in (GROUP_CVG, GROUP_POS, GROUP_NEG):
            x = r[g]
            line.append(f"{g}: n={x['n']:4d} m={x['mean']:6.2f} med={x['median']:6.2f} "
                        f"win={x['win_rate']:5.1f} exc={x['exc_mean']:6.2f} "
                        f"broken={x['broken_rate']:5.1f}")
        print("  " + " | ".join(line))
    print(f"\nCVG 组内分层:")
    for label, d in cvg_sub.items():
        x = d["T20"]
        print(f"  {label}: n={d['n']:4d} m={x['mean']:6.2f} med={x['median']:6.2f} "
              f"win={x['win_rate']:5.1f} exc={x['exc_mean']:6.2f} broken={x['broken_rate']:5.1f}")
    print(f"\n事件聚集: 同日>=3股 {stats['clustering']['days_ge3']} 天 / {total_days} 天 "
          f"({stats['clustering']['pct_days_ge3']:.0f}%)，涉及 "
          f"{stats['clustering']['events_in_ge3_days']} 事件 "
          f"({stats['clustering']['pct_events_in_ge3_days']:.0f}%)")
    print(f"written: {ev_csv}")
    print(f"written: {os.path.join(OUT_DIR, 'macd_support_stats.json')}")


if __name__ == "__main__":
    main()