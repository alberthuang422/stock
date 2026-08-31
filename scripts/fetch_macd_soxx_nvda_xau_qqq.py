# -*- coding: utf-8 -*-
"""
回测「日线MACD死叉 + 4h RSI 30-35 超卖」策略的数据准备脚本
- 日线增量更新：SOXX / NVDA / QQQ / GC=F(黄金, 代表XAUUSD)
- 4h 全量拉取（Yahoo 限最近 730 天）
直连 query1.finance.yahoo.com，无需 CDP
"""
import json
import os
import time
import datetime
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

# 标的 -> (目录名, 数据源ticker, 展示名)
TICKERS = [
    ("soxx",   "SOXX",  "SOXX"),
    ("nvda",   "NVDA",  "NVDA"),
    ("qqq",    "QQQ",   "QQQ"),
    ("xauusd", "GC=F",  "XAUUSD(GC=F)"),
]


def fetch(ticker, interval, period1=None, period2=None, range_=None):
    if range_:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={range_}"
    else:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}"
               f"&period1={period1}&period2={period2}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def to_rows(j, interval):
    r = j["chart"]["result"][0]
    ts = r["timestamp"]
    q = r["indicators"]["quote"][0]
    adj = (r["indicators"].get("adjclose") or [{}])[0].get("adjclose", [])
    rows = []
    for i, t in enumerate(ts):
        if i >= len(q["close"]) or q["close"][i] is None:
            continue
        d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
        date_str = f"{d.year:04d}-{d.month:02d}-{d.day:02d} {d.hour:02d}:{d.minute:02d}"
        # 日线保留纯日期
        if interval == "1d":
            date_str = date_str[:10]
        a = adj[i] if i < len(adj) and adj[i] is not None else q["close"][i]
        rows.append([date_str, q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i], a])
    return rows


def save_csv(dirname, interval, rows):
    d = os.path.join(DATA, dirname)
    os.makedirs(d, exist_ok=True)
    iv = "1D" if interval == "1d" else "4h"
    fn = os.path.join(d, f"{dirname.upper()}, {iv}.csv") if dirname != "xauusd" else os.path.join(d, f"XAUUSD, {iv}.csv")
    with open(fn, "w", encoding="utf-8") as f:
        f.write("date,open,high,low,close,volume,adj_close\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")
    return fn


def main():
    # 1) 日线更新：显式大 period 区间拉全量（range=max 会返回月度采样，必须用 period1/period2）
    for dirname, tk, _disp in TICKERS:
        j = fetch(tk, "1d", period1=int(datetime.datetime(1995, 1, 1).replace(tzinfo=datetime.timezone.utc).timestamp()),
                  period2=int(time.time() + 86400))
        rows = to_rows(j, "1d")
        fn = save_csv(dirname, "1d", rows)
        print(f"[1d] {tk}: {len(rows)} rows -> {fn}")
        time.sleep(1)

    # 2) 4h 拉取（币安式4根/日，Yahoo为2根/日，限730天）
    for dirname, tk, _disp in TICKERS:
        try:
            j = fetch(tk, "4h", range_="2y")
            rows = to_rows(j, "4h")
            fn = save_csv(dirname, "4h", rows)
            print(f"[4h] {tk}: {len(rows)} rows -> {fn}")
        except Exception as e:
            print(f"[4h] {tk} FAIL: {e}")
        time.sleep(1)

    print("DONE")


if __name__ == "__main__":
    main()