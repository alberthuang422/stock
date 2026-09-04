# -*- coding: utf-8 -*-
"""为震荡市突破回测补拉热榜个股日线（新浪全历史，未复权）
范围：results/rsi14_hot_20260904.json 前 50 中本地缺 1D 数据的票
输出：data/<sym>/<SYM>, 1D.csv（含 adj_close=close，标记 raw_source=sina）
注意：新浪为未复权价；突破/回撤类事件研究对未复权敏感（除权日会产生假突破），
      报告口径节须注明；若票有除权，事件统计以价格行为为主可接受。
"""
import urllib.request
import re
import json
import os
import time
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

hot = json.load(open(os.path.join(BASE, "results", "rsi14_hot_20260904.json"), encoding="utf-8"))
top50 = [h["code"] for h in hot[:50]]


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
for t in top50:
    d = os.path.join(DATA, t.lower())
    csv_path = os.path.join(d, f"{t.upper()}, 1D.csv")
    if os.path.isfile(csv_path):
        continue
    try:
        s = sina(t.lower())
        if s is None or len(s) < 60:
            fail.append((t, "rows<60" if s is not None else "empty"))
            continue
        os.makedirs(d, exist_ok=True)
        s.to_csv(csv_path, index_label="date")
        ok.append((t, len(s), s.index[0].date(), s.index[-1].date()))
        print(f"ok {t}: {len(s)} bars {s.index[0].date()} ~ {s.index[-1].date()}")
    except Exception as e:
        fail.append((t, str(e)[:80]))
        print(f"fail {t}: {str(e)[:80]}")
    time.sleep(0.8)

print("\n== summary ==")
print(f"ok={len(ok)} fail={len(fail)}")
for t, r in fail:
    print(f"  fail {t}: {r}")
