# -*- coding: utf-8 -*-
"""本地 CSV（Yahoo 全量）+ 新浪补齐最近交易日 → 更新 SOFI/AFRM/XYZ 日线"""
import urllib.request
import re
import json
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")


def sina(sym):
    url = f"https://stock.finance.sina.com.cn/usstock/api/jsonp.php/var%20_=/US_MinKService.getDailyK?symbol={sym}&___qn=3"
    req = urllib.request.Request(url, headers={"Referer": "https://stock.finance.sina.com.cn/", "User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    m = re.search(r"=\s*\((.*)\)", txt, re.S)
    rows = json.loads(m.group(1))
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["d"])
    df["open"] = df["o"].astype(float)
    df["high"] = df["h"].astype(float)
    df["low"] = df["l"].astype(float)
    df["close"] = df["c"].astype(float)
    df["volume"] = df["v"].astype(float)
    return df.set_index("date")[["open", "high", "low", "close", "volume"]].sort_index()


for sym in ["sofi", "afrm", "xyz"]:
    csv_path = os.path.join(DATA, sym, f"{sym.upper()}, 1D.csv")
    local = pd.read_csv(csv_path, parse_dates=["date"]).set_index("date").sort_index()
    local = local[~local.index.duplicated(keep="last")]
    s = sina(sym)
    # 仅取本地缺失的日期（新浪最后覆盖到最新）
    missing = s.index.difference(local.index)
    add = s.loc[missing]
    add["adj_close"] = add["close"]
    merged = pd.concat([local, add]).sort_index()
    merged = merged[~merged.index.duplicated(keep="last")]
    merged.to_csv(csv_path, index_label="date")
    print(f"{sym}: local_last={local.index[-1].date()} +{len(missing)}天 -> merged_last={merged.index[-1].date()} 总行数={len(merged)}")
