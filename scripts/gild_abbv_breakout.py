#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GILD / ABBV 横盘突破扫描 + T+1 / T+5 / T+20 收益统计。

口径 (与报告附录一致):
- 通道: Donchian N=20, 上沿=rolling(20).high.max().shift(1), 下沿=rolling(20).low.min().shift(1)
- 横盘确认 (突破日 t 前 60 日窗口):
  1) 触及上沿邻近 high >= 0.975*上沿 的次数 >= 2
  2) 触及下沿邻近 low  <= 1.025*下沿 的次数 >= 2
  3) 带宽比 上沿/下沿 - 1 落在 [5%, 25%] (太窄=无操作价值, 太宽=单边趋势伪横盘)
- 突破: close[t-1] <= 上沿[t-1] 且 close[t] > 上沿[t-1] (收盘价有效上穿, 排除上影线假破)
  且当日涨跌幅 >= 2.5% (未复权 close, 与看盘软件一致)
- 合并: 相邻突破 30 交易日内只计第一次 (强势后连续上穿只算一笔)
- 收益: T+N 用 adj_close (复权) 计算, 与分红无关的价格涨幅
- 未来函数防护: 通道与判断全部只用 t-1 及以前信息

输出: results/gild_abbv_breakout/events.json, stats.json, baseline.json
"""
import os
import json
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "results", "gild_abbv_breakout")
os.makedirs(OUT_DIR, exist_ok=True)

TICKERS = ["GILD", "ABBV"]
N_CHANNEL = 20          # Donchian 通道周期
PRE_WIN = 60            # 横盘确认窗口
TOUCH_HI = 0.975       # 上沿触及带
TOUCH_LO = 1.025       # 下沿触及带
BAND_MIN, BAND_MAX = 0.05, 0.25   # 带宽比 [下沿->上沿], 相对上沿
MIN_GAIN = 2.5         # 突破日涨幅阈值 %
MERGE_DAYS = 30        # 相邻突破合并窗口
FWD = [1, 5, 20]
_LOCAL_PRE = 20
_LOCAL_POST = 20


def load(t):
    df = pd.read_csv(os.path.join(ROOT, "data", t, f"{t}, 1D.csv"), parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def scan(df):
    """返回突破事件 DataFrame: 含 date, close, gain%, upper, band, 及各 fwd 收益(adj_close 口径)。"""
    high, low, close = df["high"], df["low"], df["close"]
    up = high.rolling(N_CHANNEL).max().shift(1)     # 截至 t-1 的上沿
    dn = low.rolling(N_CHANNEL).min().shift(1)      # 截至 t-1 的下沿
    df = df.copy()
    df["upper"] = up
    df["lower"] = dn
    df["gain"] = close.pct_change() * 100
    df["ret1"] = df["adj_close"].shift(-1) / df["adj_close"] - 1
    df["ret5"] = df["adj_close"].shift(-5) / df["adj_close"] - 1
    df["ret20"] = df["adj_close"].shift(-20) / df["adj_close"] - 1

    rows = []
    idx = df.index
    for i in idx:
        if i < N_CHANNEL + 1 or pd.isna(df.loc[i, "upper"]) or pd.isna(df.loc[i, "lower"]):
            continue
        # 1) 收盘上穿前日上沿
        if not (df.loc[i - 1, "close"] <= df.loc[i - 1, "upper"] and df.loc[i, "close"] > df.loc[i - 1, "upper"]):
            continue
        # 2) 当日涨幅 >= 2.5%
        if pd.isna(df.loc[i, "gain"]) or df.loc[i, "gain"] < MIN_GAIN:
            continue
        # 3) 横盘确认: 前 PRE_WIN 日窗口
        j0 = max(N_CHANNEL, i - PRE_WIN)
        win = df.loc[j0:i - 1]
        if len(win) < PRE_WIN * 0.6:
            continue
        touch_hi = int((win["high"] >= win["upper"] * TOUCH_HI).sum())
        touch_lo = int((win["low"] <= win["lower"] * TOUCH_LO).sum())
        band = df.loc[i - 1, "upper"] / df.loc[i - 1, "lower"] - 1
        if touch_hi < 2 or touch_lo < 2:
            continue
        if not (BAND_MIN <= band <= BAND_MAX):
            continue
        rows.append((i, int(win.index[0]), int(win.index[-1])))

    # 合并相邻突破 (30 交易日内取首次)
    merged = []
    for item in rows:
        i = item[0]
        if merged and i - merged[-1][0] < MERGE_DAYS:
            continue
        merged.append(item)

    # 局部窗口边界 (取与局部K线一致的 pre/post)
    pre, post = _LOCAL_PRE, _LOCAL_POST

    recs = []
    for item in merged:
        i, b0, b1 = item
        # 区间首尾之保证金价与时间 (用于 markArea)
        l0, l1 = df.loc[b0, "low"], df.loc[b1, "low"]
        h0, h1 = df.loc[b0, "high"], df.loc[b1, "high"]
        # 平铺 xIdx (容器内全局索引), 区间内首个/末个 x 的下标
        # 局部图 K 线为 [i-pre, i+post], 区间 [b0,b1] 映射到 x = [b0-(i-pre), b1-(i-pre)]
        # 但局部图 xAxis 是 category, 所以用 'value' startIdx (0..n-1) 形式
        # ECharts markArea 用 xAxis 数值下标: 区间起止对应 (b0 - x0, b1 - x0), 其中 x0 = i - pre
        x0 = i - pre
        xL = b0 - x0
        xR = b1 - x0
        recs.append({
            "dt": df.loc[i, "date"].strftime("%Y-%m-%d"),
            "box_start": df.loc[b0, "date"].strftime("%Y-%m-%d"),
            "box_end": df.loc[b1, "date"].strftime("%Y-%m-%d"),
            "box_lo": round(float(min(l0, l1)), 2),
            "box_hi": round(float(max(h0, h1)), 2),
            "xL": xL, "xR": xR,
        })

    ev = df.loc[[it[0] for it in merged]].copy()
    ev = ev.reset_index(drop=True)
    ev["date"] = ev["date"].dt.strftime("%Y-%m-%d")
    ev["upper"] = ev["upper"].round(2)
    ev["lower"] = ev["lower"].round(2)
    ev["gain"] = ev["gain"].round(2)
    cols = ["date", "close", "gain", "upper", "lower"]
    cols += [f"ret{n}" for n in FWD]
    ev = ev[cols]
    for n in FWD:
        ev[f"ret{n}"] = (ev[f"ret{n}"] * 100).round(2)
    return ev, merged, recs


def stats(vals):
    v = vals.dropna()
    if len(v) == 0:
        return {"n": 0}
    return {
        "n": int(len(v)),
        "mean": round(float(v.mean()), 2),
        "median": round(float(v.median()), 2),
        "win": round(float((v > 0).mean() * 100), 1),
        "p25": round(float(v.quantile(0.25)), 2),
        "p75": round(float(v.quantile(0.75)), 2),
    }


def main():
    all_events = []
    all_boxes = []
    per_ticker = {}
    for t in TICKERS:
        df = load(t)
        ev, _, boxes = scan(df)
        ev.insert(0, "ticker", t)
        all_events.append(ev)
        all_boxes.extend(boxes)
        per_ticker[t] = {
            "n": int(len(ev)),
            "by_horizon": {f"T+{n}": stats(ev[f"ret{n}"]) for n in FWD},
            **{f"T+{n}": stats(ev[f"ret{n}"]) for n in FWD},
        }

    ev_df = pd.concat(all_events, ignore_index=True)
    # 全部合并统计
    pooled = {
        "n": int(len(ev_df)),
        "by_horizon": {f"T+{n}": stats(ev_df[f"ret{n}"]) for n in FWD},
        **{f"T+{n}": stats(ev_df[f"ret{n}"]) for n in FWD},
    }
    # 分年 (全部标的合并)
    ev_date = pd.to_datetime(ev_df["date"])
    by_year = {}
    for y in sorted(ev_date.dt.year.unique()):
        sub = ev_df[ev_date.dt.year == y]
        by_year[str(y)] = {
            "n": int(len(sub)),
            **{f"T+{n}": stats(sub[f"ret{n}"]) for n in FWD},
        }
    # 基线对照: 全部交易日随机 fwd (作为基准胜率)
    baseline = {}
    for t in TICKERS:
        df = load(t)
        for n in FWD:
            r = df["adj_close"].pct_change(n) * 100
            baseline[f"{t}_T+{n}"] = stats(r)

    recs = ev_df.to_dict(orient="records")
    with open(os.path.join(OUT_DIR, "events.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    payload = {"tickers": TICKERS, "per_ticker": per_ticker, "pooled": pooled,
               "by_year": by_year, "baseline": baseline, "boxes": all_boxes}
    with open(os.path.join(OUT_DIR, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print("=== 事件数 ===")
    for t in TICKERS:
        print(t, per_ticker[t]["n"])
    print("=== pooled 统计 ===")
    for n in FWD:
        s = pooled[f"T+{n}"]
        print(f"T+{n}: n={s['n']} mean={s['mean']}% med={s['median']}% win={s['win']}%")
    print("=== 分年 (all) ===")
    for y, s in by_year.items():
        print(y, s["n"], {f"T+{n}": (s[f'T+{n}'].get('mean'), s[f'T+{n}'].get('win')) for n in FWD})
    print("events.json lines:", len(recs))


if __name__ == "__main__":
    main()