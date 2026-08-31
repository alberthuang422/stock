# -*- coding: utf-8 -*-
"""
60 号报告：日线 MACD 死叉 + 4h RSI(14) 30-35 超卖 买入胜率回测
标的：SOXX / NVDA / XAUUSD(GC=F) / QQQ
数据：日线（全量历史）+ 4h（Yahoo 限 2024-09 起，约 2 年）
主口径：日线"刚死叉"日 → 死叉后 3 个交易日内 4h RSI(14) 触及 [30,35] 触发买入
        （触发日次日开盘买入，同时附"死叉当日即超卖"的严格口径与敏感性）
对照：仅死叉 / 仅 4h 超卖 / 无条件基准 三组
"""
import os
import json
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results")

ASSETS = [
    ("soxx", "SOXX", "费城半导体指数 ETF"),
    ("nvda", "NVDA", "英伟达"),
    ("xauusd", "XAUUSD", "黄金 (GC=F 期货代理)"),
    ("qqq", "QQQ", "纳指 100 ETF"),
]

HOLD_DAYS = [1, 3, 5, 10, 20]
RSI_LO, RSI_HI = 30.0, 35.0
DEAD_AFTER_WINDOW = 3  # 死叉后 N 个交易日内 4h RSI 触及超卖


def read_daily(dirname):
    fn = os.path.join(DATA, dirname, f"{dirname.upper()}, 1D.csv")
    df = pd.read_csv(fn)
    col_date = "date" if "date" in df.columns else df.columns[0]
    df[col_date] = pd.to_datetime(df[col_date])
    df = df.set_index(col_date).sort_index()
    df = df[["open", "high", "low", "close", "volume", "adj_close"]].astype(float)
    # 拆分/分红调整：构造连续价格序列（避免拆股造成假收益）
    # 因子当日恒定，后复权 open = open * (adj_close/close)
    df["adj_factor"] = df["adj_close"] / df["close"]
    df["open_adj"] = df["open"] * df["adj_factor"]
    df["close_adj"] = df["adj_close"]
    df["adj_factor"] = df["adj_factor"].fillna(1.0)
    return df[["open", "high", "low", "close", "volume", "adj_close", "open_adj", "close_adj"]]


def read_h4(dirname):
    fn = os.path.join(DATA, dirname, f"{dirname.upper()}, 4h.csv")
    df = pd.read_csv(fn)
    col_date = "date" if "date" in df.columns else df.columns[0]
    df[col_date] = pd.to_datetime(df[col_date])
    df = df.set_index(col_date).sort_index()
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def macd(close, fast=12, slow=26, signal=9):
    ema_f = close.ewm(span=fast, adjust=False).mean()
    ema_s = close.ewm(span=slow, adjust=False).mean()
    dif = ema_f - ema_s
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = (dif - dea) * 2
    return dif, dea, hist


def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    r = 100.0 - 100.0 / (1.0 + rs)
    r.iloc[0] = 50.0
    return r


def forward_returns(close, buy_price_dates, buy_idx, hold):
    """给定买入日期（索引对齐 close），返回 hold 个交易日后收盘相对买入价的收益"""
    out = {}
    for h in hold:
        rets = []
        for b in buy_idx:
            target = b + h
            if target >= len(close):
                rets.append(None)
                continue
            p0 = close.iloc[b]  # 次日开盘价暂用 close 占位，由调用方替换
            p1 = close.iloc[target]
            rets.append(p1 / p0 - 1.0)
        out[h] = rets
    return out


def summarize(rets_list):
    arr = np.array([r for r in rets_list if r is not None], dtype=float)
    if len(arr) == 0:
        return None
    wins = (arr > 0).mean()
    return {
        "n": int(len(arr)),
        "win_rate": round(float(wins) * 100, 1),
        "mean": round(float(arr.mean()), 2),
        "median": round(float(np.median(arr)), 2),
        "best": round(float(arr.max()), 2),
        "worst": round(float(arr.min()), 2),
        "avg_win": round(float(arr[arr > 0].mean()), 2) if (arr > 0).any() else None,
        "avg_loss": round(float(arr[arr <= 0].mean()), 2) if (arr <= 0).any() else None,
        "pl_ratio": round(float(abs(arr[arr > 0].mean() / arr[arr <= 0].mean())), 2) if (arr > 0).any() and (arr <= 0).any() else None,
    }


def run_asset(dirname, disp, note):
    daily = read_daily(dirname)
    h4 = read_h4(dirname)
    close = daily["close"]           # 原始价（信号计算用）
    open_ = daily["open"]             # 原始开盘（信号口径）
    close_adj = daily["close_adj"]    # 后复权（收益结算用）
    open_adj = daily["open_adj"]      # 后复权开盘（买入执行价）

    # 日线 MACD
    dif, dea, hist = macd(close)
    daily["dif"], daily["dea"], daily["hist"] = dif, dea, hist
    cross_dead = (dif < dea) & (dif.shift(1) >= dea.shift(1))
    cross_dead_dates = daily.index[cross_dead.values]
    cross_dead_dates = [d for d in cross_dead_dates if d <= h4.index.max()]  # 4h 覆盖期内

    # 4h RSI
    h4["rsi"] = rsi(h4["close"])
    h4["rsi_touch_30_35"] = h4["rsi"].between(RSI_LO, RSI_HI)
    h4["rsi_deep"] = h4["rsi"] < RSI_LO
    # 每日聚合：当日最后一根 4h bar RSI、当日是否触及区间、是否深超卖
    day_last = h4.groupby(h4.index.date)["rsi"].last()
    day_touch = h4.groupby(h4.index.date)["rsi_touch_30_35"].any()
    day_touch_deep = h4.groupby(h4.index.date)["rsi_deep"].any()
    day_last = pd.Series(day_last.values, index=pd.to_datetime(day_last.index), name="rsi_4h_last")
    day_touch = pd.Series(day_touch.values, index=pd.to_datetime(day_touch.index), name="rsi_touch")
    day_touch_deep = pd.Series(day_touch_deep.values, index=pd.to_datetime(day_touch_deep.index), name="rsi_deep")

    # 交易日序列（日线索引，同时存在于 4h 覆盖期内）
    trade_days = daily.index[(daily.index >= h4.index.min().normalize()) & (daily.index <= h4.index.max().normalize())]
    pos = {d: i for i, d in enumerate(trade_days)}

    # ============ 信号识别 ============
    signals_strict = []  # 严格：死叉当日 4h RSI 日末落在 [30,35]
    signals_main = []    # 主口径：死叉后 ≤3 交易日内 4h RSI 日末首次落入 [30,35]
    signals_loose = []   # 宽松：死叉后 ≤3 交易日内盘中任意 4h bar RSI 触及 [30,35]
    miss_below30 = 0     # 死叉后窗口内日末 RSI 直接跌破30（不属"30-35档"，披露为错过）

    for d in cross_dead_dates:
        if d not in pos:
            continue
        di = pos[d]
        # 死叉当日 4h 信息
        last_rsi = day_last.get(d)
        touch = bool(day_touch.get(d, False))
        touch_deep = bool(day_touch_deep.get(d, False))

        rec_strict = {
            "cross_date": str(d.date()),
            "cross_day_rsi_last": round(float(last_rsi), 1) if pd.notna(last_rsi) else None,
            "cross_day_touch": touch,
            "cross_day_deep": touch_deep,
        }
        if touch and not touch_deep and last_rsi is not None and RSI_LO <= last_rsi <= RSI_HI:
            signals_strict.append((d, rec_strict))

        # 死叉后窗口内扫描
        trigger_main = None    # 日末收盘落 [30,35]
        trigger_loose = None   # 盘中触及 [30,35]（含当日日末在区间外但盘中曾落入）
        day_min_rsi = np.inf
        for off in range(0, DEAD_AFTER_WINDOW):
            ti = di + off
            if ti >= len(trade_days):
                break
            td = trade_days[ti]
            td_last = day_last.get(td)
            if pd.notna(td_last):
                day_min_rsi = min(day_min_rsi, float(td_last))
            td_touch = bool(day_touch.get(td, False))
            # 盘中触及（宽松）：任一根 4h bar 的 RSI 落在 [30,35]
            bars_today = h4.loc[h4.index.floor("D") == td]
            if len(bars_today) and bars_today["rsi"].between(RSI_LO, RSI_HI).any():
                if trigger_loose is None:
                    trigger_loose = (td, round(float(bars_today["rsi"].min()), 1))
            # 日末收盘在 [30,35]（主口径）
            if td_last is not None and RSI_LO <= td_last <= RSI_HI and trigger_main is None:
                trigger_main = (td, round(float(td_last), 1))
            if trigger_main is not None:
                break

        # 主口径：日末收盘落档
        if trigger_main is not None:
            td, td_rsi = trigger_main
            rec_main = dict(rec_strict)
            rec_main["trigger_date"] = str(td.date())
            rec_main["trigger_day_rsi_last"] = td_rsi
            rec_main["trigger_offset"] = int((pos[td] - di))
            signals_main.append((pos[td], rec_main))  # 位置索引

        # 宽松：盘中触及（一旦同期主口径也触发则合并，不重复）
        if trigger_loose is not None and trigger_main is None:
            td, rsi_min = trigger_loose
            rec_loose = dict(rec_strict)
            rec_loose["trigger_date"] = str(td.date())
            rec_loose["trigger_day_rsi_min"] = rsi_min
            rec_loose["trigger_offset"] = int((pos[td] - di))
            signals_loose.append((pos[td], rec_loose))

        # 窗口内日末跌破 30（越档下落，主口径未触发）
        if trigger_main is None and day_min_rsi < RSI_LO:
            miss_below30 += 1

    # 买入价：触发日次日开盘
    def buy_open(i):
        if i + 1 < len(trade_days):
            return open_adj.loc[trade_days[i + 1]], trade_days[i + 1]
        return None, None

    # 收益计算（统一用收盘价序列，索引对齐 trade_days）
    close_align = close_adj.reindex(trade_days)
    # 用位置索引计算
    def backtest(entries):
        """entries: list of (trigger_idx_in_trade_days, meta)"""
        res = {}
        details = []
        for (ti, meta) in entries:
            bp, bd = buy_open(ti)
            if bp is None or pd.isna(bp):
                continue
            bi = pos[bd]
            row = {"date": str(meta.get("trigger_date")), "buy_date": str(bd.date()),
                   "buy_price": round(float(bp), 2), "cross_date": meta.get("cross_date"),
                   "trigger_rsi_last": meta.get("trigger_day_rsi_last") or meta.get("cross_day_rsi_last")}
            for h in HOLD_DAYS:
                if bi + h < len(close_align):
                    p1 = close_align.iloc[bi + h]
                    row[f"ret_t{h}"] = round(float(p1 / bp - 1.0) * 100, 2)
                    row[f"close_t{h}"] = round(float(p1), 2)
                else:
                    row[f"ret_t{h}"] = None
            details.append(row)
        return details

    det_main = backtest(signals_main)
    det_strict = backtest([(pos[trig], m) for trig, m in signals_strict]) if signals_strict else []
    det_loose = backtest(signals_loose) if signals_loose else []

    # ============ 对照口径 ============
    # 1) 仅日线死叉（4h 覆盖期内所有死叉日，次日开盘买入）
    cross_in_range = [d for d in cross_dead_dates if d in pos]
    det_dead_only = backtest([(pos[d], {"trigger_date": str(d.date()), "cross_date": str(d.date())}) for d in cross_in_range])

    # 2) 仅 4h RSI 30-35（无死叉过滤）：所有触及日，但为减重叠，取每 3 交易日窗口首个触及日
    touch_days = [d for d in day_touch.index if d in pos and day_touch.get(d) and day_last.get(d) is not None and RSI_LO <= day_last.get(d) <= RSI_HI]
    touch_days = sorted(touch_days)
    dedup = []
    for td in touch_days:
        if not dedup or (pos[td] - pos[dedup[-1]]) >= 3:
            dedup.append(td)
    det_touch_only = backtest([(pos[td], {"trigger_date": str(td.date())}) for td in dedup])

    # 3) 无条件基准：覆盖期内每交易日（同日距≥20 去重叠）买入持有
    all_days = list(trade_days)
    dedup_all = [d for i, d in enumerate(all_days) if i % 20 == 0]
    det_buyhold = backtest([(pos[dd], {"trigger_date": str(dd.date())}) for dd in dedup_all])

    # 汇总
    def summarize_det(det, key_label):
        out = {}
        for h in HOLD_DAYS:
            vals = [r[f"ret_t{h}"] for r in det if r.get(f"ret_t{h}") is not None]
            s = summarize(vals)
            out[f"t{h}"] = s
        return out

    result = {
        "asset": disp,
        "note": note,
        "range_4h": [str(h4.index.min()), str(h4.index.max())],
        "n_cross_dead_hist": int(len(cross_dead_dates)),          # 全历史死叉数
        "n_cross_dead_4h": int(len(cross_in_range)),              # 4h 覆盖期内死叉数
        "n_signal_main": len(det_main),
        "n_signal_strict": len(det_strict),
        "n_signal_loose": len(det_loose),
        "n_miss_below30": int(miss_below30),
        "main": summarize_det(det_main, "main"),
        "strict": summarize_det(det_strict, "strict"),
        "loose": summarize_det(det_loose, "loose"),
        "dead_only": summarize_det(det_dead_only, "dead_only"),  # 仅死叉（4h 覆盖期内）
        "touch_only": summarize_det(det_touch_only, "touch_only"),
        "buyhold": summarize_det(det_buyhold, "buyhold"),
        "details_main": det_main,
        "details_strict": det_strict,
        "details_loose": det_loose,
        "details_dead_only": det_dead_only,
    }
    return result


def main():
    os.makedirs(OUT, exist_ok=True)
    results = {}
    for dirname, disp, note in ASSETS:
        # 忽略无信号资产时仍保留
        r = run_asset(dirname, disp, note)
        results[dirname] = r
        print(f"[{disp}] 4h死叉={r['n_cross_dead_4h']} 主口径信号={r['n_signal_main']} 严格={r['n_signal_strict']}"
              f" 宽松={r['n_signal_loose']} 跌穿30={r['n_miss_below30']}")
        for h in HOLD_DAYS:
            s = r["main"].get(f"t{h}")
            if s:
                print(f"   主口径 T+{h}: 胜率{s['win_rate']}% n={s['n']} 均值{s['mean']}% 中位{s['median']}%")

    fn = os.path.join(OUT, "60_macd_dead_4h_rsi_backtest.json")
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1, default=str)
    print("SAVED:", fn)


if __name__ == "__main__":
    main()