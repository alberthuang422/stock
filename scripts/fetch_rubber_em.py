#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拉取沪胶 RU / 顺丁 BR / 20号胶 NR 主连日线（东方财富 kline 接口）。
产出: data/rubber/<code>.csv  (date, open, close, high, low, volume, amount)
用法: python fetch_rubber_em.py
"""
import json
import os
import time
import urllib.request

BASE = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
SECIDS = {"RU": "113.ruM", "BR": "113.brM", "NR": "142.nrM"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rubber")


def fetch(secid):
    q = (f"?secid={secid}&fields1=f1,f2,f3,f4,f5"
         "&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=0&beg=19900101&end=20500101")
    req = urllib.request.Request(BASE + q, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    os.makedirs(OUT, exist_ok=True)
    for code, secid in SECIDS.items():
        js = fetch(secid)
        d = js.get("data")
        if not d or not d.get("klines"):
            print(f"[FAIL] {code} {secid}: no data")
            continue
        name = d["name"]
        lines = ["date,open,close,high,low,volume,amount"]
        for k in d["klines"]:
            p = k.split(",")
            lines.append(",".join(p[:7]))
        path = os.path.join(OUT, f"{code}.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[OK] {code} ({name}) {secid}: {len(lines)-1} bars "
              f"{d['klines'][0].split(',')[0]} -> {d['klines'][-1].split(',')[0]} -> {path}")
        time.sleep(0.4)


if __name__ == "__main__":
    main()
