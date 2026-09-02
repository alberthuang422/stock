# -*- coding: utf-8 -*-
"""
CVS + VIX 日线获取（2026-09-02，Yahoo 直连 403 后的替代通道）
- CVS(新浪未复权): 新浪美股 US_MinKService.getDailyK，1980 起全历史 → 存 CVS_sina_raw, 1D.csv
  ⚠️ 主数据已切换为用户提供的 TradingView BATS:CVS 前复权（data/cvs/CVS, 1D.csv），
     新浪未复权仅作对照备份，勿再覆盖主文件。
- VIX: CBOE 官方 VIX_History.csv（1990 起，权威收盘口径）→ data/vix/VIX, 1D.csv
"""
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def curl(url, out, timeout=60):
    subprocess.run(["curl", "-s", "-m", str(timeout), "-A", UA, url, "-o", out],
                   check=True, timeout=timeout + 30)


def load_sina_cvs():
    raw_path = os.path.join(BASE, "Temp", "cvs_raw.js")
    curl("https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php/var%20t=/US_MinKService.getDailyK?symbol=CVS",
         raw_path)
    raw = open(raw_path, encoding="utf-8", errors="replace").read()
    m = re.search(r"\((\[.*\])\)", raw, re.S)
    if not m:
        raise RuntimeError("新浪返回解析失败")
    rows = json.loads(m.group(1))
    out = []
    for r in rows:
        out.append([r["d"], r["o"], r["h"], r["l"], r["c"], r["v"], r["c"]])  # adj_close 未复权 = close
    return out


def load_cboe_vix():
    csv_path = os.path.join(BASE, "Temp", "vix_hist.csv")
    curl("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv", csv_path)
    out = []
    for line in open(csv_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("DATE"):
            continue
        p = line.split(",")  # DATE,OPEN,HIGH,LOW,CLOSE
        dt = p[0].split("/")
        d = f"{dt[2]}-{dt[0]:0>2}-{dt[1]:0>2}"
        out.append([d, p[1], p[2], p[3], p[4], "0", p[4]])
    return out


def save(dirname, ticker, rows):
    d = os.path.join(DATA, dirname)
    os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, f"{ticker}, 1D.csv")
    with open(fn, "w", encoding="utf-8") as f:
        f.write("date,open,high,low,close,volume,adj_close\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")
    return fn


def main():
    which = sys.argv[1:] or ["cvs", "vix"]
    if "cvs" in which:
        rows = load_sina_cvs()
        fn = save("cvs", "CVS_sina_raw", rows)
        print(f"CVS(新浪未复权备份): {len(rows)} 行 {rows[0][0]} ~ {rows[-1][0]} -> {fn}")
    if "vix" in which:
        rows = load_cboe_vix()
        fn = save("vix", "VIX", rows)
        print(f"VIX: {len(rows)} 行 {rows[0][0]} ~ {rows[-1][0]} -> {fn}")


if __name__ == "__main__":
    main()
