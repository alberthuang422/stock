# -*- coding: utf-8 -*-
"""XLY 成分股 2026-07-23 单日表现核查
本地 csv 已有成分 + Yahoo 直连补拉 TSLA/RCL
"""
import json
import os
import time
import datetime
import urllib.request
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

# (本地目录, 展示名, 大致权重%)
LOCAL = [
    ("amzn", "AMZN 亚马逊", 22.0),
    ("xly",  "XLY 可选消费ETF", None),
    ("hd",   "HD 家得宝", 7.0),
    ("mcd",  "MCD 麦当劳", 5.0),
    ("bkng", "BKNG Booking", 4.5),
    ("tjx",  "TJX", 4.0),
    ("sbux", "SBUX 星巴克", 3.0),
    ("low",  "LOW 劳氏", 3.0),
    ("mar",  "MAR 万豪", 2.5),
    ("cmg",  "CMG Chipotle", 1.8),
    ("nke",  "NKE 耐克", 1.8),
]
FETCH = [("tsla", "TSLA 特斯拉", 14.0), ("rcl", "RCL 皇家加勒比", 2.0)]


def fetch_yahoo(ticker, p1, p2):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&period1={p1}&period2={p2}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.load(r)
    rows = []
    for res in j["chart"]["result"]:
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        for i, t in enumerate(ts):
            if q["close"][i] is None:
                continue
            d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
            rows.append([d.strftime("%Y-%m-%d"), q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]])
    return rows


def read_local(dirname):
    cands = [os.path.join(DATA, dirname, f"{dirname.upper()}, 1D.csv"),
             os.path.join(DATA, dirname, f"{dirname}, 1D.csv")]
    for p in cands:
        if os.path.exists(p):
            return pd.read_csv(p, parse_dates=["date"])
    raise FileNotFoundError(cands)


def pct_table(df):
    """返回 {date: close} 及涨跌幅"""
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 100
    return df


def main():
    out = []
    # 本地
    for dirname, name, w in LOCAL:
        df = read_local(dirname)
        df = pct_table(df)
        row = {"ticker": dirname.upper(), "name": name, "w": w}
        for d in ["2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23", "2026-07-24", "2026-07-27"]:
            sub = df[df["date"] == d]
            row[f"close_{d}"] = round(float(sub["close"].iloc[0]), 2) if len(sub) else None
            row[f"ret_{d}"] = round(float(sub["ret"].iloc[0]), 2) if len(sub) else None
        out.append(row)

    # Yahoo 补拉
    p1 = int(datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc).timestamp())
    p2 = int(datetime.datetime(2026, 9, 1, tzinfo=datetime.timezone.utc).timestamp())
    for dirname, name, w in FETCH:
        rows = fetch_yahoo(dirname.upper(), p1, p2)
        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        df = pct_table(df)
        row = {"ticker": dirname.upper(), "name": name, "w": w}
        for d in ["2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23", "2026-07-24", "2026-07-27"]:
            sub = df[df["date"] == d]
            row[f"close_{d}"] = round(float(sub["close"].iloc[0]), 2) if len(sub) else None
            row[f"ret_{d}"] = round(float(sub["ret"].iloc[0]), 2) if len(sub) else None
        out.append(row)
        time.sleep(1)

    odf = pd.DataFrame(out)
    print(odf[["ticker", "name", "w", "ret_2026-07-22", "ret_2026-07-23", "ret_2026-07-24", "close_2026-07-23"]].to_string(index=False))
    odf.to_csv(os.path.join(BASE, "results", "xly_components_20260723.csv"), index=False, encoding="utf-8-sig")
    print("\nsaved -> results/xly_components_20260723.csv")


if __name__ == "__main__":
    main()
