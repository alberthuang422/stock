# -*- coding: utf-8 -*-
# 持仓标的综合分析：技术指标计算（2026-08-28，数据截至 08-27 收盘）
import csv, os, json, math

DATA = r"C:\Users\Administrator\Desktop\stock\data"
OUT = r"C:\Users\Administrator\Desktop\stock\results"
TICKERS = {
    "CSCO": "csco/csco, 1D.csv",
    "MCD": "mcd/mcd, 1D.csv",
    "VST": "vst/VST, 1D.csv",
    "APO": "apo/APO, 1D.csv",
    "ABBV": "abbv/ABBV, 1D.csv",
    "GILD": "gild/GILD, 1D.csv",
    "SBUX": "sbux/SBUX, 1D.csv",
    "XYZ": "xyz/xyz, 1D.csv",
    "SPY": "spy/SPY, 1D.csv",
    "QQQ": "qqq/QQQ, 1D.csv",
    "XLF": "xlf/xlf, 1D.csv",
    "XLV": "xlv/XLV, 1D.csv",
    "XLK": "xlk/xlk, 1D.csv",
    "XLP": "xlp/xlp, 1D.csv",
    "XLE": "xle/xle, 1D.csv",
    "XLRE": "xlre/XLRE, 1D.csv",
    "XLU": "xlu/xlu, 1D.csv",
}

def load(path):
    rows = []
    with open(os.path.join(DATA, path), encoding="utf-8") as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            if len(r) < 6 or not r[0] or not r[4]:
                continue
            try:
                rows.append({"date": r[0], "o": float(r[1]), "h": float(r[2]),
                             "l": float(r[3]), "c": float(r[4]), "v": float(r[5])})
            except ValueError:
                continue
    return rows

def ema(vals, n):
    k = 2 / (n + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out

def rsi14(closes):
    out = [None] * len(closes)
    if len(closes) < 15:
        return out
    g = l = 0.0
    for i in range(1, 15):
        d = closes[i] - closes[i - 1]
        g += max(d, 0)
        l += max(-d, 0)
    ag, al = g / 14, l / 14
    out[14] = 100 - 100 / (1 + (ag / al if al else 1e9))
    for i in range(15, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * 13 + max(d, 0)) / 14
        al = (al * 13 + max(-d, 0)) / 14
        out[i] = 100 - 100 / (1 + (ag / al if al else 1e9))
    return out

def atr14(rows):
    trs = []
    for i in range(1, len(rows)):
        tr = max(rows[i]["h"] - rows[i]["l"],
                 abs(rows[i]["h"] - rows[i - 1]["c"]),
                 abs(rows[i]["l"] - rows[i - 1]["c"]))
        trs.append(tr)
    out = [None] * len(rows)
    if len(trs) < 14:
        return out, None
    a = sum(trs[:14]) / 14
    out[15] = a
    for i in range(14, len(trs)):
        a = (a * 13 + trs[i]) / 14
        out[i + 1] = a
    return out, a

def pct(a, b):
    return (a / b - 1) * 100 if b else None

def main():
    result = {}
    for tk, path in TICKERS.items():
        rows = load(path)
        closes = [r["c"] for r in rows]
        n = len(rows)
        last = rows[-1]
        prev = rows[-2]
        d_ret = pct(last["c"], prev["c"])
        w_ret = pct(last["c"], closes[-6]) if n > 5 else None
        m_ret = pct(last["c"], closes[-22]) if n > 21 else None
        rsi = rsi14(closes)
        e10 = ema(closes, 10)[-1]
        e20 = ema(closes, 20)[-1]
        e50 = ema(closes, 50)[-1]
        e120 = ema(closes, 120)[-1]
        e200 = ema(closes, 200)[-1]
        # 近 20/60 日高低
        hi20 = max(r["h"] for r in rows[-20:])
        lo20 = min(r["l"] for r in rows[-20:])
        hi60 = max(r["h"] for r in rows[-60:])
        lo60 = min(r["l"] for r in rows[-60:])
        hi253 = max(r["h"] for r in rows[-253:])
        lo253 = min(r["l"] for r in rows[-253:])
        atrs, atr = atr14(rows)
        # RSI 分档
        r = rsi[-1]
        rsi_band = "超买(>=70)" if r >= 70 else "偏强(55-70)" if r >= 55 else \
                   "中性(45-55)" if r >= 45 else "偏弱(30-45)" if r >= 30 else "超卖(<30)"
        # 距 EMA20 偏离
        dev20 = pct(last["c"], e20)
        # MACD(12,26,9) 简算
        e12 = ema(closes, 12)[-1]
        e26 = ema(closes, 26)[-1]
        macd = e12 - e26
        def ema_series(vals, n):
            k = 2 / (n + 1)
            out = [vals[0]]
            for v in vals[1:]:
                out.append(v * k + out[-1] * (1 - k))
            return out
        dea_series = ema_series([e12 - e26 for e12, e26 in zip(ema(closes, 12), ema(closes, 26))], 9) if n > 60 else []
        dea = dea_series[-1] if dea_series else None
        macd_hist = macd - dea if dea is not None else None
        # 趋势判断
        trend = "多头" if last["c"] > e20 > e50 else "空头" if last["c"] < e20 < e50 else "震荡"
        # 20日窗口最短单边
        win20 = pct(hi20, lo20)
        result[tk] = {
            "date": last["date"], "close": round(last["c"], 2),
            "d_ret": round(d_ret, 2), "w_ret": round(w_ret, 2), "m_ret": round(m_ret, 2),
            "rsi": round(r, 1), "rsi_band": rsi_band,
            "e10": round(e10, 2), "e20": round(e20, 2), "e50": round(e50, 2),
            "e120": round(e120, 2), "e200": round(e200, 2), "dev20": round(dev20, 2),
            "hi20": round(hi20, 2), "lo20": round(lo20, 2),
            "hi60": round(hi60, 2), "lo60": round(lo60, 2),
            "hi253": round(hi253, 2), "lo253": round(lo253, 2),
            "atr": round(atr, 2) if atr else None,
            "atr_pct": round(atr / last["c"] * 100, 2) if atr else None,
            "macd": round(macd, 2), "dea": round(dea, 2) if dea else None,
            "macd_hist": round(macd_hist, 2) if macd_hist is not None else None,
            "trend": trend, "range20_pct": round(win20, 2),
            "vol_today": int(last["v"]), "vol_20avg": int(sum(r["v"] for r in rows[-20:]) / 20),
        }
    with open(os.path.join(OUT, "position_tech_20260828.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    # 控制台汇总
    hdr = ["ticker", "close", "d%", "w%", "m%", "RSI(带)", "EMA20", "dev20", "EMA50",
           "EMA200", "hi20", "lo20", "hi60", "lo60", "ATR%", "MACDhist", "trend", "rng20%"]
    print("|".join(hdr))
    for tk in TICKERS:
        d = result[tk]
        print("|".join([tk, str(d["close"]), str(d["d_ret"]), str(d["w_ret"]), str(d["m_ret"]),
                        f"{d['rsi']}({d['rsi_band']})", str(d["e20"]), str(d["dev20"]), str(d["e50"]),
                        str(d["e200"]), str(d["hi20"]), str(d["lo20"]), str(d["hi60"]), str(d["lo60"]),
                        str(d["atr_pct"]), str(d["macd_hist"]), d["trend"], str(d["range20_pct"])]))
    print("saved ->", os.path.join(OUT, "position_tech_20260828.json"))

if __name__ == "__main__":
    main()