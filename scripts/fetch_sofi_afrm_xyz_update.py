# -*- coding: utf-8 -*-
"""SOFI / AFRM / XYZ(Block) 日线全量更新（Yahoo 直连，无需 CDP）
同时探测 SQ 旧代码是否有效。
"""
import json
import os
import time
import datetime
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

TICKERS = [("sofi", "SOFI"), ("afrm", "AFRM"), ("xyz", "XYZ")]


def fetch(ticker, period1, period2):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d"
           f"&period1={period1}&period2={period2}&events=history&includeAdjustedClose=true")
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
    p1 = int(datetime.datetime(2015, 1, 1).replace(tzinfo=datetime.timezone.utc).timestamp())
    p2 = int(time.time() + 86400)
    for dirname, tk in TICKERS:
        try:
            j = fetch(tk, p1, p2)
            rows = to_rows(j)
            d = os.path.join(DATA, dirname)
            os.makedirs(d, exist_ok=True)
            fn = os.path.join(d, f"{tk}, 1D.csv")
            with open(fn, "w", encoding="utf-8") as f:
                f.write("date,open,high,low,close,volume,adj_close\n")
                for r in rows:
                    f.write(",".join(str(x) for x in r) + "\n")
            print(f"[OK] {tk}: {len(rows)} rows, {rows[0][0]} ~ {rows[-1][0]} -> {fn}")
        except Exception as e:
            print(f"[FAIL] {tk}: {e}")
        time.sleep(1)

    # 探测 SQ 旧代码
    try:
        j = fetch("SQ", p1, p2)
        r = j["chart"]["result"][0]
        print(f"[PROBE] SQ: meta.symbol={r.get('meta', {}).get('symbol')}, "
              f"longName={r.get('meta', {}).get('longName')}, rows={len(r.get('timestamp', []))}")
    except Exception as e:
        print(f"[PROBE] SQ: 无有效数据 ({e})")
        try:
            print("  原始响应:", json.dumps(json.loads(str(e)))[:300] if False else "n/a")
        except Exception:
            pass


if __name__ == "__main__":
    main()
