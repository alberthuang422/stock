# -*- coding: utf-8 -*-
"""拉取随机 10 只美股 2023-01-01 至今的日线（Yahoo 直连，period1/period2 显式）"""
import json
import os
import time
import datetime
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "resistance")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}


def fetch(ticker, period1, period2):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d"
           f"&period1={period1}&period2={period2}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def to_rows(j):
    r = j["chart"]["result"][0]
    ts = r["timestamp"]
    q = r["indicators"]["quote"][0]
    adj = (r["indicators"].get("adjclose") or [{}])[0].get("adjclose", [])
    rows = []
    for i, t in enumerate(ts):
        if i >= len(q["close"]) or q["close"][i] is None:
            continue
        d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
        date_str = f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
        a = adj[i] if i < len(adj) and adj[i] is not None else q["close"][i]
        rows.append([date_str, q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i], a])
    return rows


def main():
    with open(os.path.join(BASE, "Temp", "resistance_picks.json"), encoding="utf-8") as f:
        picks = json.load(f)["tickers"]
    p1 = int(datetime.datetime(2023, 1, 1).replace(tzinfo=datetime.timezone.utc).timestamp())
    p2 = int(time.time() + 86400)
    os.makedirs(DATA, exist_ok=True)
    for tk in picks:
        try:
            j = fetch(tk, p1, p2)
            rows = to_rows(j)
            fn = os.path.join(DATA, f"{tk}.csv")
            with open(fn, "w", encoding="utf-8") as f:
                f.write("date,open,high,low,close,volume,adj_close\n")
                for r in rows:
                    f.write(",".join(str(x) for x in r) + "\n")
            print(f"{tk}: {len(rows)} rows -> {fn}  (last {rows[-1][0]})")
        except Exception as e:
            print(f"{tk} FAIL: {e}")
        time.sleep(1)
    print("DONE")


if __name__ == "__main__":
    main()
