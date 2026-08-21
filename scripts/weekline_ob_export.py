# -*- coding: utf-8 -*-
"""导出汇总 JSON + 每个 t0 的 4h K线切片（含 t0 前后 bars），供报告画图"""
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
    return df.sort_values("time").reset_index(drop=True)

def rsi_14(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + ag / al)

def macd_12_26_9(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    return dif, dea, 2 * (dif - dea)

TICKERS = ["abbv", "gild"]
dfs = {}
for tk in TICKERS:
    d = load_tencent_240(tk)
    d["rsi14"] = rsi_14(d["close"])
    # 腾讯自带 RSI 列（用户软件口径），缺失时用重算值
    if "RSI" in d.columns:
        d["rsi36"] = pd.to_numeric(d["RSI"], errors="coerce").fillna(d["rsi14"])
    else:
        d["rsi36"] = d["rsi14"]
    d["dif4h"], d["dea4h"], d["hist4h"] = macd_12_26_9(d["close"])
    d["time_s"] = d["time"].dt.strftime("%m-%d %H:%M")
    dfs[tk] = d

# 读取窗口口径 detail
with open(os.path.join(OUT, "abbv_gild_weekline_ob_window.json"), encoding="utf-8") as f:
    W = json.load(f)

detail = [r for r in W["detail"] if r["has_ob"]]

# 每个 t0 的切片（t0-6 ~ t0+20, 4h bars）
slices = []
for r in detail:
    tk = r["ticker"]
    d = dfs[tk]
    t0 = pd.Timestamp(r["t0_time"])
    # 匹配：date + HH:MM 前缀（腾讯 time 带 +08:00 时区后缀）
    t0_s = t0.strftime("%Y-%m-%d %H:%M")
    d["t0match"] = d["time"].dt.strftime("%Y-%m-%d %H:%M")
    m = d["t0match"] == t0_s
    if m.sum() == 0:
        print("  !!! no match for", t0_s, tk)
        continue
    i = int(d.index[m][0])
    lo, hi = max(0, i - 6), min(len(d), i + 21)
    seg = d.iloc[lo:hi]
    start_of_focus = None
    slices.append({
        "ticker": tk,
        "week_start": r["week_start"],
        "t0_time": r["t0_time"],
        "t0_close": r["t0_close"],
        "rsi_t0": r["rsi_t0"],
        "ob_week_gap": r["ob_week_gap"],
        "dd_5": r["dd_5"], "dd_10": r["dd_10"], "dd_20": r["dd_20"], "dd_40": r["dd_40"],
        "fwd_5": r["fwd_5"], "fwd_10": r["fwd_10"], "fwd_20": r["fwd_20"], "fwd_40": r["fwd_40"],
        "bars_to_recover": r["bars_to_recover"],
        "new_high_40": r["new_high_40"],
        "t0_off": int(i - lo),  # t0 在切片中的位置
        "bars": [
            {"t": seg.iloc[j]["time_s"], "o": seg.iloc[j]["open"], "h": seg.iloc[j]["high"],
             "l": seg.iloc[j]["low"], "c": seg.iloc[j]["close"], "v": float(seg.iloc[j]["volume"]),
             "r": round(float(seg.iloc[j]["rsi36"]), 1) if not pd.isna(seg.iloc[j]["rsi36"]) else None}
            for j in range(len(seg))
        ],
    })

W["slices"] = slices
with open(os.path.join(OUT, "abbv_gild_weekline_ob_window.json"), "w", encoding="utf-8") as f:
    json.dump(W, f, ensure_ascii=False, indent=1, default=str)

# 汇总 KPI JSON（给报告用）
kpi = {
    "events_total": W["events_total"],
    "with_ob_n": W["with_ob_n"],
    "with_ob_rate": W["with_ob_rate"],
    "ob_same_week": W["gap_dist"].get("0", 0),
    "ob_next_week": W["gap_dist"].get("1", 0),
    "summary": W["summary"],
    "by_gap": W["by_gap"],
    "current": W["current"],
    "ctrl": {
        "ob_same_week_rate_plain": 28.6,  # 仅转正当周口径：事件周内超买率
    },
}
with open(os.path.join(OUT, "abbv_gild_weekline_kpi.json"), "w", encoding="utf-8") as f:
    json.dump(kpi, f, ensure_ascii=False, indent=1, default=str)

print(f"slices 数: {len(slices)}")
print("样例:", json.dumps(slices[0]["bars"][:3], ensure_ascii=False))
print("DONE")