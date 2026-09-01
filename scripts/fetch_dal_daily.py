# -*- coding: utf-8 -*-
"""
DAL 日线全量拉取（Yahoo 直连，无需 CDP）2026-09-02
DAL 2007-05-03 上市，显式 period1/period2 拉全量（range=max 会返回月度采样假数据）
"""
import json, os, time, datetime, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}


def fetch(ticker, interval, period1, period2):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}"
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
    p1 = int(datetime.datetime(1995, 1, 1).replace(tzinfo=datetime.timezone.utc).timestamp())
    p2 = int(time.time() + 86400)
    for dirname, tk in [("dal", "DAL")]:
        j = fetch(tk, "1d", p1, p2)
        rows = to_rows(j)
        fn = os.path.join(DATA, dirname, f"{dirname.upper()}, 1D.csv")
        with open(fn, "w", encoding="utf-8") as f:
            f.write("date,open,high,low,close,volume,adj_close\n")
            for r in rows:
                f.write(",".join(str(x) for x in r) + "\n")
        print(f"[1d] {tk}: {len(rows)} rows -> {fn}")
        print("  首日:", rows[0][0], "末日:", rows[-1][0], "末收盘:", rows[-1][4])
        time.sleep(1)


if __name__ == "__main__":
    main()
