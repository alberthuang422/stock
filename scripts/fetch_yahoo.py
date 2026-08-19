#!/usr/bin/env python3
"""从 Yahoo Finance chart API 拉取日线数据，保存为 CSV。

用法: python fetch_yahoo.py IBB GILD
输出: data/<ticker>/<TICKER>, 1D.csv
"""
import sys, os, time, json
import pandas as pd
import requests

BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json",
}
OUT_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def fetch(ticker: str, start_ts: int, end_ts: int) -> pd.DataFrame:
    url = BASE.format(ticker)
    params = {
        "period1": start_ts,
        "period2": end_ts,
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }
    for attempt in range(4):
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            break
        print(f"  {ticker} HTTP {r.status_code}, retry {attempt+1}", flush=True)
        time.sleep(2 + attempt * 2)
    else:
        raise RuntimeError(f"{ticker} 拉取失败: HTTP {r.status_code}")
    j = r.json()
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose", [None] * len(ts))
    df = pd.DataFrame({
        "date": pd.to_datetime(ts, unit="s", utc=True).tz_convert("America/New_York").date,
        "open": q["open"],
        "high": q["high"],
        "low": q["low"],
        "close": q["close"],
        "volume": q["volume"],
        "adj_close": adj,
    })
    df = df.dropna(subset=["close"])
    df = df.drop_duplicates(subset=["date"])
    return df

def main():
    tickers = sys.argv[1:] or ["IBB", "GILD"]
    end_ts = int(time.time())
    start_ts = int(pd.Timestamp("2015-01-01", tz="UTC").timestamp())
    for tk in tickers:
        df = fetch(tk, start_ts, end_ts)
        out_dir = os.path.join(OUT_ROOT, tk.lower())
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{tk.upper()}, 1D.csv")
        df.to_csv(out_path, index=False)
        print(f"{tk}: {len(df)} 行, {df['date'].iloc[0]} ~ {df['date'].iloc[-1]} -> {out_path}", flush=True)

if __name__ == "__main__":
    main()
