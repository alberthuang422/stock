# -*- coding: utf-8 -*-
"""事件研究：蓝筹周线「0轴上方高位刚死叉 + 跌破EMA10但收于EMA20上方1~3% + 多头排列未破坏
+ 距上次DIF上穿0轴10~16周（首次动能衰竭）」—— EMA20 支撑有效性检验

严格无前视：全部周线指标用「已完成周序列 + 当周 to-date 值」递推（同报告33）。

分组（周线频率，事件=回踩EMA20的当周）：
- A=死叉回踩（当周刚触发MACD死叉 DIF下穿DEA）+ 窗口10~16周   → 用户信号
- B=未死叉回踩（当周柱仍>0）+ 窗口10~16周                    → 隔离死叉因子
- C=死叉回踩 + 窗口外（距0轴上穿<10或>16周）                  → 隔离首次回调窗口因子
公共条件：0轴上方(dif>0且dea>0) + EMA10>EMA20 + close<EMA10
         + close 在 EMA20 上方 1%~3% + DIF 较近26周峰值回落≥25%
破位率：窗口内周收盘最低 < 事件周EMA20 × 0.98
度量：fwd T ∈ {5,10,20,60} 周（周线级别）；超额=个股 - SPY 同窗周收益
环境：事件周前 8 周 SPY 收益；事件聚集：同周 ≥3 股
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
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
EMA_FAST, EMA_SLOW = 10, 20
PULLBACK_LOW, PULLBACK_HIGH = 0.01, 0.03     # 收盘在 EMA20 上方 1%~3%
DIFF_DRAW_DOWN = 0.25                          # DIF 较近26周峰值回落 ≥25%
WINDOW_MIN, WINDOW_MAX = 10, 16                # 距上次DIF上穿0轴 10~16 周
BREAK_MULT = 0.98                              # 破位：周收盘最低 < EMA20×0.98
MIN_COOLDOWN = 4                               # 事件间最小间隔（周）
WEEK_MIN = 40                                  # 预热周数
ZERO_CROSS_LOOKBACK = 60                       # 找最近0轴上穿的回看周数
HORIZONS = [5, 10, 20, 60]
SPY_ENV_PRE = 8                                # 环境窗口（周）

GROUP_A, GROUP_B, GROUP_C = "A", "B", "C"
GROUP_DESC = {
    "A": "高位刚死叉回踩EMA20 + 距0轴上穿10~16周",
    "B": "未死叉回踩EMA20 + 距0轴上穿10~16周",
    "C": "高位刚死叉回踩EMA20 + 窗口外",
}


def load_weekly(symbol):
    path = os.path.join(DATA_DIR, symbol, f"{symbol}, W.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def weekly_from_daily(symbol):
    """对无 W.csv 的标的（如 SPY 基准）从日线聚合（W-FRI 周期，与 gen_weekly 一致）"""
    path = os.path.join(DATA_DIR, symbol, f"{symbol}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    if "adj_close" in df.columns and not df["adj_close"].isna().all():
        ratio = df["adj_close"] / df["close"]
        for col in ("open", "high", "low"):
            df[col] = df[col] * ratio
        df["close"] = df["adj_close"]
    period = df["date"].dt.to_period("W-FRI")
    wk = df.groupby(period, sort=True).agg(
        date=("date", "last"), open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"), volume=("volume", "sum")).reset_index(drop=True)
    return wk


def compute_weekly_state(df):
    """无前视周线状态：MACD DIF/DEA/hist + EMA10/20 + 最近0轴上穿周距 + DIF峰值回落
    全部当周 to-date 递推（用已完成周序列的 EMA + 当周 close）。"""
    close = df["close"].values
    n = len(df)

    # 已完成周序列 EMA（含当前周，最后值即当前周收盘）
    ema12_s = pd.Series(close).ewm(span=MACD_FAST, adjust=False).mean()
    ema26_s = pd.Series(close).ewm(span=MACD_SLOW, adjust=False).mean()
    dif_s = (ema12_s - ema26_s).values
    dea_s = dif_s * 0  # placeholder
    for i in range(len(dif_s)):
        if i == 0:
            dea_s[i] = dif_s[i]
        else:
            dea_s[i] = (2.0 / (MACD_SIGNAL + 1)) * dif_s[i] + (1 - 2.0 / (MACD_SIGNAL + 1)) * dea_s[i - 1]
    hist_s = dif_s - dea_s

    ema10_s = pd.Series(close).ewm(span=EMA_FAST, adjust=False).mean().values
    ema20_s = pd.Series(close).ewm(span=EMA_SLOW, adjust=False).mean().values

    # 当周 to-date 递推（只依赖上一周完成的 EMA 状态 + 当周 close）
    a12, a26, a9 = 2.0 / (MACD_FAST + 1), 2.0 / (MACD_SLOW + 1), 2.0 / (MACD_SIGNAL + 1)
    a10, a20 = 2.0 / (EMA_FAST + 1), 2.0 / (EMA_SLOW + 1)
    dif_cur = np.full(n, np.nan)
    dea_cur = np.full(n, np.nan)
    hist_cur = np.full(n, np.nan)
    ema10_cur = np.full(n, np.nan)
    ema20_cur = np.full(n, np.nan)
    for i in range(n):
        if i == 0:
            dif_cur[i] = (a12 - a26) * close[i]
            dea_cur[i] = dif_cur[i]
        else:
            dif_cur[i] = (a12 * close[i] + (1 - a12) * ema12_s[i - 1]) - \
                         (a26 * close[i] + (1 - a26) * ema26_s[i - 1])
            dea_cur[i] = a9 * dif_cur[i] + (1 - a9) * dea_s[i - 1]
        hist_cur[i] = dif_cur[i] - dea_cur[i]
        if i == 0:
            ema10_cur[i] = ema10_s[i]
            ema20_cur[i] = ema20_s[i]
        else:
            ema10_cur[i] = a10 * close[i] + (1 - a10) * ema10_s[i - 1]
            ema20_cur[i] = a20 * close[i] + (1 - a20) * ema20_s[i - 1]

    # 最近一次 DIF 上穿 0 轴的周序号（完成序列；上穿=前一周期 dif<=0 且本周期 dif>0）
    zero_cross_pos = np.full(n, -1)
    last = -1
    for i in range(n):
        if i > 0 and dif_s[i - 1] <= 0 and dif_s[i] > 0:
            last = i
        zero_cross_pos[i] = last
    # 距 0 轴上穿的周数（事件周 pos - 最近上穿 pos；60周内无上穿=999）
    weeks_since_cross = np.full(n, np.nan)
    for i in range(n):
        z = zero_cross_pos[i]
        if z < 0:
            weeks_since_cross[i] = np.nan
        elif i - z > ZERO_CROSS_LOOKBACK:
            weeks_since_cross[i] = 999.0
        else:
            weeks_since_cross[i] = float(i - z)
    # DIF 峰值（近26周完成序列）+ 回落
    dif_peak = np.full(n, np.nan)
    dif_drawdown = np.full(n, np.nan)
    for i in range(n):
        lo = max(0, i - 25)
        peak = float(np.nanmax(dif_s[lo:i + 1]))
        dif_peak[i] = peak
        if peak > 0:
            dif_drawdown[i] = 1.0 - dif_cur[i] / peak if np.isfinite(dif_cur[i]) else np.nan
    return (dif_cur, dea_cur, hist_cur, ema10_cur, ema20_cur,
            weeks_since_cross, dif_drawdown)


def detect_events(df, st):
    (dif_cur, dea_cur, hist_cur, ema10_cur, ema20_cur,
     weeks_since_cross, dif_drawdown) = st
    close = df["close"].values
    n = len(df)
    events = []
    last_event = -10 ** 9
    for i in range(WEEK_MIN, n):
        if i - last_event < MIN_COOLDOWN:
            continue
        c = close[i]
        e20 = ema20_cur[i]
        if not (math.isfinite(c) and math.isfinite(e20) and e20 > 0 and math.isfinite(dif_cur[i])):
            continue
        if not (math.isfinite(ema10_cur[i]) and math.isfinite(hist_cur[i])):
            continue
        wsc = weeks_since_cross[i]
        if not math.isfinite(wsc):
            continue
        # ---- 公共条件 ----
        above_zero = dif_cur[i] > 0 and dea_cur[i] > 0
        bull_align = ema10_cur[i] > e20
        pullback = (c < ema10_cur[i]) and (PULLBACK_LOW <= (c / e20 - 1.0) <= PULLBACK_HIGH)
        # 死叉当周：本周 hist<0 且上周 hist>=0
        dead_now = hist_cur[i] < 0 and (i == 0 or hist_cur[i - 1] >= 0)
        # DIF 回落
        dd = dif_drawdown[i]
        dif_retr = math.isfinite(dd) and (dd >= DIFF_DRAW_DOWN)
        if not (above_zero and bull_align and pullback and dif_retr):
            continue
        in_window = WINDOW_MIN <= wsc <= WINDOW_MAX
        if dead_now and in_window:
            group = GROUP_A
        elif hist_cur[i] >= 0 and in_window:
            group = GROUP_B
        elif dead_now and not in_window:
            group = GROUP_C
        else:
            continue
        events.append({
            "symbol": df["symbol"][0],
            "event_date": df["date"][i].strftime("%Y-%m-%d"),
            "w": i,
            "group": group,
            "close": float(c),
            "ema10": float(ema10_cur[i]),
            "ema20": float(e20),
            "diff_cur": float(dif_cur[i]),
            "dea_cur": float(dea_cur[i]),
            "hist_cur": float(hist_cur[i]),
            "weeks_since_cross": float(wsc),
            "diff_drawdown": float(dd) if math.isfinite(dd) else None,
        })
        last_event = i
    return events


def fwd_metrics(df, ev, close, spy_close_arr, spy_date_index):
    n = len(df)
    i = ev["w"]
    e20 = ev["ema20"]
    out = {}
    ev_date = df["date"][i]
    spy_pos = spy_date_index.get(ev_date)
    for T in HORIZONS:
        if i + T < n:
            out[f"fwd{T}"] = (close[i + T] / close[i] - 1.0) * 100.0
        else:
            out[f"fwd{T}"] = None
        if spy_pos is not None and spy_pos + T < len(spy_close_arr):
            if out[f"fwd{T}"] is not None:
                s0, s1 = spy_close_arr[spy_pos], spy_close_arr[spy_pos + T]
                if s0 > 0:
                    out[f"exc{T}"] = out[f"fwd{T}"] - (s1 / s0 - 1.0) * 100.0
                else:
                    out[f"exc{T}"] = None
            else:
                out[f"exc{T}"] = None
        else:
            out[f"exc{T}"] = None
        end = min(i + T, n - 1)
        if end >= i + 1:
            w = close[i + 1:end + 1]
            out[f"broken{T}"] = int(bool((w < e20 * BREAK_MULT).any()))
        else:
            out[f"broken{T}"] = None
    # 环境：事件周前 8 周 SPY 收益
    if spy_pos is not None and spy_pos - SPY_ENV_PRE >= 0:
        s0, s1 = spy_close_arr[spy_pos - SPY_ENV_PRE], spy_close_arr[spy_pos]
        if s0 > 0:
            out["spy_pre8"] = (s1 / s0 - 1.0) * 100.0
        else:
            out["spy_pre8"] = None
    else:
        out["spy_pre8"] = None
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
    # SPY 周线
    spy = weekly_from_daily("spy")
    spy_close = spy["close"].values
    spy_di = {d: k for k, d in enumerate(spy["date"])}

    all_events = []
    per_symbol = {}
    for sym in UNIVERSE:
        df = load_weekly(sym)
        df["symbol"] = sym
        st = compute_weekly_state(df)
        evs = detect_events(df, st)
        close = df["close"].values
        for ev in evs:
            m = fwd_metrics(df, ev, close, spy_close, spy_di)
            ev.update(m)
            all_events.append(ev)
        per_symbol[sym] = len(evs)
        print(f"  {sym:>9s}: {len(evs):3d}")

    ev_df = pd.DataFrame(all_events)
    if len(ev_df) == 0:
        print("NO EVENTS"); return
    ev_df = ev_df.drop(columns=["w"])
    col_order = ["symbol", "event_date", "group", "close", "ema10", "ema20",
                 "diff_cur", "dea_cur", "hist_cur", "weeks_since_cross",
                 "diff_drawdown", "spy_pre8"] + \
                [c for T in HORIZONS for c in (f"fwd{T}", f"exc{T}")] + \
                [f"broken{T}" for T in HORIZONS]
    ev_df = ev_df[col_order]
    ev_csv = os.path.join(OUT_DIR, "macd_deadcross_events.csv")
    ev_df.to_csv(ev_csv, index=False, encoding="utf-8")

    groups = [GROUP_A, GROUP_B, GROUP_C]
    ev_df["year"] = ev_df["event_date"].str[:4]
    stats = {"n_total": int(len(all_events)), "per_symbol": per_symbol,
             "group_desc": GROUP_DESC, "horizons": HORIZONS,
             "params": {"macd": [12, 26, 9], "ema": [10, 20],
                        "band_pct": [PULLBACK_LOW * 100, PULLBACK_HIGH * 100],
                        "window_weeks": [WINDOW_MIN, WINDOW_MAX],
                        "diff_drawdown": DIFF_DRAW_DOWN,
                        "break_mult": BREAK_MULT}}
    g2df = {g: ev_df[ev_df["group"] == g] for g in groups}
    stats["n_group"] = {g: int(len(d)) for g, d in g2df.items()}

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
            }
        row["ttest"] = {
            "A_vs_B": t_two_sample(g2df[GROUP_A][fcol].dropna().values,
                                    g2df[GROUP_B][fcol].dropna().values),
            "A_vs_C": t_two_sample(g2df[GROUP_A][fcol].dropna().values,
                                   g2df[GROUP_C][fcol].dropna().values),
        }
        horizon_stats[T] = row
    stats["horizon"] = horizon_stats

    # 环境分层（SPY前8周）
    env_buckets = [(-999, -3, "<-3%"), (-3, 0, "-3~0%"), (0, 3, "0~3%"), (3, 999, ">3%")]
    env_stats = {}
    for g, d in g2df.items():
        rows = []
        for lo, hi, name in env_buckets:
            sub = d[(d["spy_pre8"].fillna(-999) >= lo) & (d["spy_pre8"].fillna(999) < hi)]
            f = sub["fwd20"].dropna()
            b = sub["broken20"].dropna()
            e = sub["exc20"].dropna()
            rows.append({
                "bucket": name, "n": int(len(f)),
                "mean_fwd20": float(f.mean()) if len(f) else None,
                "exc_mean": float(e.mean()) if len(e) else None,
                "win_rate": float((f > 0).mean() * 100) if len(f) else None,
                "broken_rate": float(b.mean() * 100) if len(b) else None,
            })
        env_stats[g] = rows
    stats["env8"] = env_stats

    stats["year"] = {g: d.groupby("year").size().to_dict() for g, d in g2df.items()}

    # 事件聚集（同周 >=3 股）
    date_cnt = ev_df.groupby("event_date").size()
    total_days = int(len(date_cnt))
    ge3 = int((date_cnt >= 3).sum())
    ge3_ev = int(ev_df["event_date"].isin(date_cnt[date_cnt >= 3].index).sum())
    stats["clustering"] = {
        "event_days": total_days, "days_ge3": ge3,
        "pct_days_ge3": float(ge3 / total_days * 100) if total_days else None,
        "events_in_ge3_days": ge3_ev,
        "pct_events_in_ge3_days": float(ge3_ev / len(ev_df) * 100) if len(ev_df) else None,
    }

    with open(os.path.join(OUT_DIR, "macd_deadcross_stats.json"), "w",
              encoding="utf-8") as f:
        json.dump(clean(stats), f, ensure_ascii=False, indent=1)

    print(f"\n总事件: {len(all_events)}  A={stats['n_group']['A']} B={stats['n_group']['B']} C={stats['n_group']['C']}")
    for T in HORIZONS:
        r = horizon_stats[T]
        line = [f"T+{T}"]
        for g in groups:
            x = r[g]
            line.append(f"{g}: n={x['n']:3d} m={x['mean']:6.2f} med={x['median']:6.2f} "
                        f"win={x['win_rate']:5.1f} exc={x['exc_mean']:6.2f} broken={x['broken_rate']:5.1f}")
        print("  " + " | ".join(line))
    print(f"  ttest: A-B={horizon_stats[20]['ttest']['A_vs_B']:.2f} A-C={horizon_stats[20]['ttest']['A_vs_C']:.2f}")
    print(f"  broken A vs B: {horizon_stats[20]['A']['broken_rate']:.1f} vs {horizon_stats[20]['B']['broken_rate']:.1f}")

    # ---------------- 敏感性检验（写入 stats.sensitivity） ----------------
    sens = sensitivity_analysis()
    stats["sensitivity"] = sens
    with open(os.path.join(OUT_DIR, "macd_deadcross_stats.json"), "w",
              encoding="utf-8") as f:
        json.dump(clean(stats), f, ensure_ascii=False, indent=1)
    print("\n敏感性: (详见 stats.sensitivity)")
    print(f"  DIF回落扫描: " + " | ".join(f"{k}:n={v['n']} fwd20={v['fwd20']:+.2f}% win={v['win']:.0f}%"
                                          for k, v in sens["dif_thresh"].items()))
    print(f"  窗口分档: " + " | ".join(f"{k}:n={v['n']} fwd20={v['fwd20']:+.2f}% win={v['win']:.0f}%"
                                       for k, v in sens["window_buckets"].items()))
    print(f"  窗口内死叉vs未死叉: 死叉 n={sens['dead_vs_nodead']['dead']['n']} "
          f"fwd20={sens['dead_vs_nodead']['dead']['fwd20']:+.2f}% / 未死叉 n={sens['dead_vs_nodead']['nodead']['n']} "
          f"fwd20={sens['dead_vs_nodead']['nodead']['fwd20']:+.2f}%")
    print(f"written: {ev_csv}")
    print(f"written: {os.path.join(OUT_DIR, 'macd_deadcross_stats.json')}")


def sensitivity_analysis():
    """放宽/收紧关键参数，检验结论稳健性（不重复全量fwd，只算T+20）"""
    rows_all = []  # 所有满足「多头回踩公共条件」的事件，带死叉/窗口/回落标记
    spy = weekly_from_daily("spy")
    spy_close = spy["close"].values
    spy_di = {d: k for k, d in enumerate(spy["date"])}
    for sym in UNIVERSE:
        df = load_weekly(sym)
        df["symbol"] = sym
        st = compute_weekly_state(df)
        dif_cur, dea_cur, hist_cur, e10, e20, wsc, dd = st
        close = df["close"].values
        n = len(df)
        prev_hist = np.roll(hist_cur, 1)
        for i in range(WEEK_MIN, n):
            c = close[i]
            if not (math.isfinite(c) and math.isfinite(e20[i]) and e20[i] > 0
                    and math.isfinite(dif_cur[i]) and math.isfinite(wsc[i])):
                continue
            bull = dif_cur[i] > 0 and dea_cur[i] > 0 and e10[i] > e20[i]
            pullback = c < e10[i] and PULLBACK_LOW <= (c / e20[i] - 1.0) <= PULLBACK_HIGH
            if not (bull and pullback):
                continue
            dead = bool(hist_cur[i] < 0 and (i == 0 or hist_cur[i - 1] >= 0))
            ddr = float(dd[i]) if math.isfinite(dd[i]) else None
            fwd20 = (close[min(i + 20, n - 1)] / c - 1.0) * 100.0 if i + 20 < n else None
            spy_pos = spy_di.get(df["date"][i])
            exc20 = None
            if spy_pos is not None and spy_pos + 20 < len(spy_close) and fwd20 is not None:
                s0, s1 = spy_close[spy_pos], spy_close[spy_pos + 20]
                if s0 > 0:
                    exc20 = fwd20 - (s1 / s0 - 1.0) * 100.0
            rows_all.append({
                "dead": dead, "wsc": float(wsc[i]), "dd": ddr,
                "fwd20": fwd20, "exc20": exc20,
            })
    ev = pd.DataFrame(rows_all)
    out = {}

    def summarize(d):
        f = d["fwd20"].dropna()
        if not len(f):
            return {"n": 0, "fwd20": None, "win": None}
        return {"n": int(len(f)), "fwd20": float(f.mean()), "win": float((f > 0).mean() * 100)}

    # 1) DIF 回落阈值扫描（死叉+10~16周）
    out["dif_thresh"] = {}
    for thr in (0.0, 0.15, 0.25, 0.35):
        sub = ev[(ev["dead"]) & (ev["wsc"].between(WINDOW_MIN, WINDOW_MAX)) & (ev["dd"] >= thr)]
        out["dif_thresh"][f">={thr:.2f}"] = summarize(sub)
    # 2) 窗口分档（死叉、无 DIF 回落约束）
    dead = ev[ev["dead"]]
    out["window_buckets"] = {}
    for lo, hi in ((5, 10), (10, 16), (16, 24), (24, 40)):
        sub = dead[dead["wsc"].between(lo, hi)]
        out["window_buckets"][f"{lo}-{hi}w"] = summarize(sub)
    # 3) 窗口内 死叉 vs 未死叉（无 DIF 回落约束）
    w = ev[ev["wsc"].between(WINDOW_MIN, WINDOW_MAX)]
    out["dead_vs_nodead"] = {
        "dead": summarize(w[w["dead"]]),
        "nodead": summarize(w[~w["dead"]]),
    }
    return out


if __name__ == "__main__":
    main()