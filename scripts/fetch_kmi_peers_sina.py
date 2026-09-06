# -*- coding: utf-8 -*-
"""拉取 KMI + 中游同业日线（新浪美股全历史，未复权）
覆盖：KMI / WMB / ET / OKE / ENB / EPD（+补充 TRP/PBA/DTM 可选）
输出：data/<sym>/<SYM>, 1D.csv
"""
import urllib.request
import re
import json
import os
import time
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

SYMS = ["kmi", "wmb", "et", "oke", "enb", "epd", "trp", "pba", "dtm"]


def sina(sym):
    url = f"https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php/var%20t=/US_MinKService.getDailyK?symbol={sym}"
    req = urllib.request.Request(url, headers={"Referer": "https://stock.finance.sina.com.cn/", "User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    m = re.search(r"=\s*\((.*)\)", txt, re.S)
    rows = json.loads(m.group(1))
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["d"])
    for c_old, c_new in [("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("v", "volume")]:
        df[c_new] = df[c_old].astype(float)
    df["adj_close"] = df["close"]
    return df.set_index("date")[["open", "high", "low", "close", "volume", "adj_close"]].sort_index()


ok, fail = [], []
for t in SYMS:
    d = os.path.join(DATA, t.upper())
    csv_path = os.path.join(d, f"{t.upper()}, 1D.csv")
    if os.path.isfile(csv_path):
        print(f"skip {t} (exists)")
        continue
    try:
        s = sina(t)
        if s is None or len(s) < 100:
            fail.append((t, "rows<100" if s is not None else "empty"))
            continue
        os.makedirs(d, exist_ok=True)
        s.to_csv(csv_path, index_label="date")
        ok.append((t, len(s), s.index[0].date(), s.index[-1].date()))
        print(f"ok {t}: {len(s)} bars {s.index[0].date()} ~ {s.index[-1].date()}")
    except Exception as e:
        fail.append((t, str(e)[:100]))
        print(f"fail {t}: {str(e)[:100]}")
    time.sleep(0.8)

print("\n== summary ==")
print(f"ok={len(ok)} fail={len(fail)}")
for t, r in fail:
    print(f"  fail {t}: {r}")