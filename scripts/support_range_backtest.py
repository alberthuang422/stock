# -*- coding: utf-8 -*-
"""事件研究：蓝筹股「区间下沿触达 + 周线EMA20压制」三组对照

严格无前视：所有指标只用事件日及其之前的数据计算。

事件定义
--------
1) 震荡区间（日线，复权价）：
   - 以「事件日前20个交易日」为观察窗（不含事件日）。
   - 窗内收盘相对日线EMA20 至少各发生1次上穿/下穿，穿叉方向交替，
     最近一次穿叉距事件日 <= 10 个交易日，窗内振幅 max(H)/min(L)-1 <= 35%。
   - 该「震荡状态」须连续维持 >= 20 个交易日（区间维持时间 >= 20日）。
   - 区间下沿 lower = 窗内 min(低点)，上沿 upper = max(高点)，中轨 mid=(lower+upper)/2。
2) 日线条件：事件日收盘 <= lower * (1 + 0.5%)（触达下沿）。
3) 周线条件（当周周线 = 本周迄今收盘，即事件日收盘）：
   - 周线收盘 < 周线EMA20（当周值用递推：EMA = a*今日收盘 + (1-a)*上周EMA，a=2/(span+1)）
   - 周线EMA20 > 周线EMA50（未死叉）
4) 事件日 = 日线条件 且 周线条件 同日成立；同一触达连续段内只保留首次，
   事件之间最少间隔 10 个交易日（缓解前向窗口重叠）。

三组
----
A: 触下沿 + 周线收于周EMA20下方（压制） + 未死叉
B: 触下沿 + 周线收于周EMA20上方（无压制，纯下沿支撑）
C: 触下沿 + 周线收于周EMA20下方（压制） + 已死叉（周EMA20 <= 周EMA50）

度量（事件后 T ∈ {5,10,20,60} 交易日，收盘复权价）
----
- 破位率：T日内收盘最低 < lower*0.98（跌破下沿2%视为支撑失效）
- 反弹：N日收益 均值/中位数/胜率；触中轨天数（60日窗口内首次收盘>=mid，未触及记NaN）
- 最大回撤：事件后20日内收盘 peak-to-trough
- 振幅分桶：事件日振幅 (upper/lower-1) 分桶统计

输出：support_range_events.csv（逐事件）+ support_range_stats.json（分组统计）
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

# 参数
RANGE_DAYS = 20          # 观察窗
MIN_RUN = 20             # 区间最短维持交易日
MAX_AMP = 0.35           # 区间振幅上限
LAST_CROSS_DAYS = 10     # 最近一次穿叉距事件日的上限
TOUCH_TOL = 0.005        # 触达容差 0.5%
BREAK_MULT = 0.98        # 破位阈值：跌破下沿 2%
MIN_COOLDOWN = 10        # 事件间最小间隔（交易日）
DAILY_MIN_IDX = 80       # 日线EMA20收敛 + 观察窗
WEEK_MIN_POS = 60        # 周线EMA50收敛（周数）
HORIZONS = [5, 10, 20, 60]
MDD_DAYS = 20
MID_LOOKBACK = 60        # 触中轨观察窗口

GROUP_A, GROUP_B, GROUP_C = "A", "B", "C"
GROUP_DESC = {
    "A": "触下沿+周线EMA20压制+未死叉",
    "B": "触下沿+周线在EMA20上方(无压制)",
    "C": "触下沿+周线EMA20压制+已死叉",
}


def load_daily(symbol):
    path = os.path.join(DATA_DIR, symbol, f"{symbol}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    if "adj_close" not in df.columns or df["adj_close"].isna().all():
        df["adj_close"] = df["close"]
    # 复权因子统一应用到 OHLC（保持口径一致）
    ratio = df["adj_close"] / df["close"]
    for col in ("open", "high", "low"):
        df[col] = df[col] * ratio
    df["close"] = df["adj_close"]
    return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def compute_daily_state(df):
    n = len(df)
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    ema20 = pd.Series(close).ewm(span=20, adjust=False).mean().values

    # 穿叉（点事件）：用 t-1 与 t 的收盘/EMA
    cross_dir = np.zeros(n, dtype=int)  # +1 上穿, -1 下穿, 0 无
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
        w = slice(s, t)  # [t-20, t-1]
        # 振幅
        lo, hi = low[w].min(), high[w].max()
        if lo <= 0 or hi / lo - 1 > MAX_AMP:
            continue
        # 穿叉
        idx = np.where(cross_dir[s:t] != 0)[0] + s
        if len(idx) < 2:
            continue
        dirs = cross_dir[idx]
        if not (dirs.max() > 0 and dirs.min() < 0):
            continue  # 需同时有上穿与下穿
        if np.any(dirs[1:] == dirs[:-1]):
            continue  # 方向必须交替
        if idx[-1] < t - LAST_CROSS_DAYS:
            continue  # 最近一次穿插距今过久
        qualify[t] = True
        lower[t], upper[t] = lo, hi
        mid[t] = (lo + hi) / 2.0
        amp[t] = (hi / lo - 1.0) * 100.0
    return close, ema20, qualify, lower, upper, mid, amp


def compute_weekly_state(df):
    """返回 (week_pos, weekly_close, ema20_asof, ema50_asof, suppress, deathcross)
    用已完成周序列的EMA + 当周值的递推，避免前视。"""
    close = df["close"].values
    n = len(df)
    period = df["date"].dt.to_period("W-FRI")
    wk = pd.DataFrame({"period": period, "close": close})
    weekly_last = wk.groupby("period")["close"].last()
    ema20_w = weekly_last.ewm(span=20, adjust=False).mean()
    ema50_w = weekly_last.ewm(span=50, adjust=False).mean()
    pos_map = {p: i for i, p in enumerate(weekly_last.index)}

    a20 = 2.0 / (20 + 1)
    a50 = 2.0 / (50 + 1)

    week_pos = np.full(n, -1, dtype=int)
    ema20_asof = np.full(n, np.nan)
    ema50_asof = np.full(n, np.nan)
    suppress = np.zeros(n, dtype=bool)
    deathcross = np.zeros(n, dtype=bool)
    for i in range(n):
        p = period.iloc[i]
        pos = pos_map.get(p, -1)
        if pos < 1:
            continue
        week_pos[i] = pos
        e20_prev = ema20_w.iloc[pos - 1]
        e50_prev = ema50_w.iloc[pos - 1]
        e20 = a20 * close[i] + (1 - a20) * e20_prev
        e50 = a50 * close[i] + (1 - a50) * e50_prev
        ema20_asof[i] = e20
        ema50_asof[i] = e50
        suppress[i] = close[i] < e20
        deathcross[i] = e20 <= e50
    return week_pos, ema20_asof, ema50_asof, suppress, deathcross


def detect_events(df, close, qualify, lower, upper, mid, amp,
                  week_pos, ema20_asof, ema50_asof, suppress, deathcross):
    n = len(df)
    events = []
    last_event = -10 ** 9
    run_start = None
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
        sup = bool(suppress[t])
        dc = bool(deathcross[t])
        if sup and not dc:
            group = GROUP_A
        elif not sup:
            group = GROUP_B
        elif sup and dc:
            group = GROUP_C
        else:
            continue
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
            "suppress": sup,
            "deathcross": dc,
            "ema20_w": float(ema20_asof[t]),
            "ema50_w": float(ema50_asof[t]),
        })
        last_event = t
    return events


def event_metrics(df, ev, close):
    """事件后度量；全部用收盘复权价。返回 dict。"""
    n = len(df)
    t = ev["t"]
    lower = ev["lower"]
    mid = ev["mid"]
    out = {}
    for T in HORIZONS:
        if t + T < n:
            out[f"fwd{T}"] = (close[t + T] / close[t] - 1.0) * 100.0
            if T == 20:
                out["fwd20_date"] = df["date"][t + 20].strftime("%Y-%m-%d")
        else:
            out[f"fwd{T}"] = None
            if T == 20:
                out["fwd20_date"] = None
        # 破位率：T日内收盘最低 < lower*0.98
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
    # 20日最大回撤（收盘，peak-to-trough）
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
    """json 序列化清洗：numpy→原生、nan→None"""
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
    all_events = []
    per_symbol = {}
    for sym in UNIVERSE:
        df = load_daily(sym)
        df["symbol"] = sym
        close, ema20, qualify, lower, upper, mid, amp = compute_daily_state(df)
        week_pos, e20a, e50a, suppress, dc = compute_weekly_state(df)
        evs = detect_events(df, close, qualify, lower, upper, mid, amp,
                            week_pos, e20a, e50a, suppress, dc)
        for ev in evs:
            m = event_metrics(df, ev, close)
            ev.update(m)
            all_events.append(ev)
        per_symbol[sym] = len(evs)
        print(f"  {sym:>9s}: {len(evs):3d} events")

    ev_df = pd.DataFrame(all_events)
    ev_df = ev_df.drop(columns=["t"])
    ev_df = ev_df[["symbol", "event_date", "group", "close", "lower", "upper",
                   "mid", "amp_pct", "suppress", "deathcross", "ema20_w",
                   "ema50_w", "days_to_mid", "mdd20_pct", "fwd20_date"] +
                  [f"fwd{T}" for T in HORIZONS] +
                  [f"broken{T}" for T in HORIZONS]]
    ev_csv = os.path.join(OUT_DIR, "support_range_events.csv")
    ev_df.to_csv(ev_csv, index=False, encoding="utf-8")

    # ---------------- 统计 ----------------
    ev_df["year"] = ev_df["event_date"].str[:4]
    stats = {"n_total": len(all_events), "per_symbol": per_symbol,
             "group_desc": GROUP_DESC, "horizons": HORIZONS}
    g2df = {g: ev_df[ev_df["group"] == g] for g in (GROUP_A, GROUP_B, GROUP_C)}
    stats["n_group"] = {g: int(len(d)) for g, d in g2df.items()}

    # 1) 各horizon：n/均值/中位数/胜率/破位率/单样本t
    horizon_stats = {}
    for T in HORIZONS:
        fcol, bcol = f"fwd{T}", f"broken{T}"
        row = {}
        for g, d in g2df.items():
            f = d[fcol].dropna()
            b = d[bcol].dropna()
            row[g] = {
                "n": int(len(f)),
                "mean": float(f.mean()) if len(f) else None,
                "median": float(f.median()) if len(f) else None,
                "win_rate": float((f > 0).mean() * 100) if len(f) else None,
                "broken_rate": float(b.mean() * 100) if len(b) else None,
                "t_one": t_one_sample(f.values),
                "n_broken": int(int(b.sum())) if len(b) else None,
            }
        # 两样本 Welch t：A vs B, A vs C
        row["ttest"] = {
            "A_vs_B": t_two_sample(g2df[GROUP_A][fcol].dropna().values,
                                    g2df[GROUP_B][fcol].dropna().values),
            "A_vs_C": t_two_sample(g2df[GROUP_A][fcol].dropna().values,
                                   g2df[GROUP_C][fcol].dropna().values),
        }
        horizon_stats[T] = row
    stats["horizon"] = horizon_stats

    # 2) 触中轨 + 20日回撤
    mid_stats = {}
    mdd_stats = {}
    for g, d in g2df.items():
        dm = d["days_to_mid"].dropna()
        mid_stats[g] = {
            "n": int(len(d)),
            "n_reached": int(len(dm)),
            "pct_reached_60d": float(len(dm) / len(d) * 100) if len(d) else None,
            "median_days": float(dm.median()) if len(dm) else None,
            "mean_days": float(dm.mean()) if len(dm) else None,
        }
        mm = d["mdd20_pct"].dropna()
        mdd_stats[g] = {
            "n": int(len(mm)),
            "mean": float(mm.mean()) if len(mm) else None,
            "median": float(mm.median()) if len(mm) else None,
        }
    stats["days_to_mid"] = mid_stats
    stats["mdd20"] = mdd_stats

    # 3) 振幅分桶（T=20）
    buckets = [(0, 5, "<5%"), (5, 10, "5-10%"), (10, 20, "10-20%"), (20, 999, ">=20%")]
    amp_stats = {}
    for g, d in g2df.items():
        bs = []
        for lo, hi, name in buckets:
            sub = d[(d["amp_pct"] >= lo) & (d["amp_pct"] < hi)]
            f = sub["fwd20"].dropna()
            b = sub["broken20"].dropna()
            bs.append({
                "bucket": name,
                "n": int(len(f)),
                "mean_fwd20": float(f.mean()) if len(f) else None,
                "win_rate": float((f > 0).mean() * 100) if len(f) else None,
                "broken_rate": float(b.mean() * 100) if len(b) else None,
            })
        amp_stats[g] = bs
    stats["amp_bucket"] = amp_stats

    # 4) 时间分布（年份）
    year_stats = {}
    for g, d in g2df.items():
        year_stats[g] = d.groupby("year").size().to_dict()
    stats["year"] = year_stats

    # 5) 事件后收益分布分位数（T=20 核心口径）
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

    with open(os.path.join(OUT_DIR, "support_range_stats.json"), "w",
              encoding="utf-8") as f:
        json.dump(clean(stats), f, ensure_ascii=False, indent=1)

    # ---------------- 控制台汇总 ----------------
    print(f"\n总事件数: {len(all_events)}")
    print(f"  A组({GROUP_DESC['A']}): {stats['n_group']['A']}")
    print(f"  B组({GROUP_DESC['B']}): {stats['n_group']['B']}")
    print(f"  C组({GROUP_DESC['C']}): {stats['n_group']['C']}")
    print("\nT=20 对比 (均值%/中位数%/胜率%/破位率%):")
    for g in (GROUP_A, GROUP_B, GROUP_C):
        r = horizon_stats[20][g]
        print(f"  {g}: n={r['n']:4d} mean={r['mean']:6.2f} med={r['median']:6.2f} "
              f"win={r['win_rate']:5.1f} broken={r['broken_rate']:5.1f} "
              f"t_one={r['t_one']:.2f}")
    print(f"  ttest T=20: A-B={horizon_stats[20]['ttest']['A_vs_B']:.2f} "
          f"A-C={horizon_stats[20]['ttest']['A_vs_C']:.2f}")
    print(f"\nwritten: {ev_csv}")
    print(f"written: {os.path.join(OUT_DIR, 'support_range_stats.json')}")


if __name__ == "__main__":
    main()
