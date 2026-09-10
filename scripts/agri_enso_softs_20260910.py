# -*- coding: utf-8 -*-
"""
厄尔尼诺 × 农产品商品（ETN 代理）事件研究 —— 2026-09-10
用途：回答「厄尔尼诺受益农产品有哪些」，用可获取的连续价格序列做实证锚点。

数据源：新浪美股日线 JSONP（US_MinKService.getDailyK，未复权全历史；这些 ETN 不分红，价格口径可直接用）
  CANE=糖  NIB=可可  JO=咖啡  WEAT=小麦  CORN=玉米  SOYB=大豆  DBA=农业综合
口径：
  - 事件窗口 A（预报→峰值）：onset 前 3 个月月末 → peak 月 + 3 个月月末（ENSO 提前 3-6 月可预报，价格抢跑）
  - 事件窗口 B（确认→1年）：onset 月月末 → onset + 12 个月月末
  - 2026 YTD：2025-12-31 → 最新
输出 results/agri_enso_softs_20260910.json + data/<t>/<t>_sina.csv
"""
import json
import os
import subprocess
import time

import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "agri_enso_softs_20260910.json")

TICKERS = ["CANE", "NIB", "JO", "WEAT", "CORN", "SOYB", "DBA"]
NAME = {"CANE": "白糖(ETN)", "NIB": "可可(ETN)", "JO": "咖啡(ETN)", "WEAT": "小麦(ETN)",
        "CORN": "玉米(ETN)", "SOYB": "大豆(ETN)", "DBA": "农业综合(ETN)"}

# ---------- 1. 拉数（新浪 JSONP） ----------
def fetch(t):
    d = os.path.join(DATA, t.lower())
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, f"{t}_sina.csv")
    if os.path.exists(fp) and os.path.getsize(fp) > 5000:
        return pd.read_csv(fp, parse_dates=["date"])
    url = ("https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php/var%20_x=/"
           f"US_MinKService.getDailyK?symbol={t}&___qn=3")
    raw = subprocess.run(["curl", "-s", "--max-time", "30", url],
                         capture_output=True, text=True).stdout
    i, j = raw.find("(["), raw.rfind("])")
    if i < 0 or j < 0:
        raise RuntimeError(f"{t}: bad payload {raw[:120]}")
    rows = json.loads(raw[i + 1:j + 1])
    df = pd.DataFrame(rows)
    df = df.rename(columns={"d": "date", "c": "close", "o": "open", "h": "high", "l": "low", "v": "volume"})
    df["date"] = pd.to_datetime(df["date"])
    for c in ("close", "open", "high", "low", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[["date", "open", "high", "low", "close", "volume"]].sort_values("date")
    df = df[df["close"] > 0].reset_index(drop=True)
    df.to_csv(fp, index=False)
    time.sleep(1.0)
    return df

px = {}
for t in TICKERS:
    try:
        px[t] = fetch(t)
        print(t, len(px[t]), px[t]["date"].iloc[0].date(), "->", px[t]["date"].iloc[-1].date())
    except Exception as e:
        print("FAIL", t, e)

# ---------- 2. ONI 事件 ----------
seas_to_mon = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
               "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
rows = []
with open(os.path.join(DATA, "agri", "raw", "oni.txt"), encoding="utf-8") as f:
    for line in f:
        p = line.split()
        if len(p) < 4 or p[0] not in seas_to_mon:
            continue
        try:
            rows.append({"year": int(p[1]), "month": seas_to_mon[p[0]], "oni": float(p[3])})
        except ValueError:
            continue
oni = pd.DataFrame(rows).sort_values(["year", "month"]).reset_index(drop=True)
vals = {(int(r.year), int(r.month)): float(r.oni) for r in oni.itertuples()}
keys = sorted(vals)

events = []
i = 0
while i < len(keys):
    if vals[keys[i]] >= 0.5:
        j = i
        while j < len(keys) and vals[keys[j]] >= 0.5:
            j += 1
        if j - i >= 5:
            seg = keys[i:j]
            pk = max(seg, key=lambda k: vals[k])
            events.append({"onset": keys[i], "end": keys[j - 1], "peak_ym": pk,
                           "peak": round(vals[pk], 2), "len": j - i})
        i = j
    else:
        i += 1


def shift(ym, n):
    y, m = ym
    m += n
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return (y, m)


def close_at(t, ym, side="<=="):
    """取 ym 当月最后一个交易日收盘（或之前）"""
    df = px[t]
    m = df[(df["date"].dt.year == ym[0]) & (df["date"].dt.month == ym[1])]
    return float(m["close"].iloc[-1]) if len(m) else None


# 新增 2026 进行中事件（ONI 尾部仍在 0.5 以上）
tail_on = [(y, m) for (y, m) in keys if (y, m) >= (2026, 4)]
cur = {"onset": (2026, 4), "peak": None, "ongoing": True}

res = {}
for t in px:
    rec = {"name": NAME[t], "events": [], "ytd2026": None}
    for ev in events:
        o, pk = ev["onset"], ev["peak_ym"]
        a0, a1 = shift(o, -3), shift(pk, 3)
        c0, c1 = close_at(t, a0), close_at(t, a1)
        b0, b1 = close_at(t, o), close_at(t, shift(o, 12))
        d = {"onset": f"{o[0]}-{o[1]:02d}", "peak": ev["peak"], "peak_ym": f"{pk[0]}-{pk[1]:02d}"}
        if c0 and c1:
            d["A_forecast_to_peak3"] = round((c1 / c0 - 1) * 100, 1)
        if b0 and b1:
            d["B_onset_to_12m"] = round((b1 / b0 - 1) * 100, 1)
        if "A_forecast_to_peak3" in d or "B_onset_to_12m" in d:
            rec["events"].append(d)
    for k, lab in (("A_forecast_to_peak3", "A"), ("B_onset_to_12m", "B")):
        v = [e[k] for e in rec["events"] if k in e]
        if v:
            rec[f"avg_{lab}"] = round(float(np.mean(v)), 1)
            rec[f"med_{lab}"] = round(float(np.median(v)), 1)
            rec[f"win_{lab}"] = round(float(np.mean([x > 0 for x in v])) * 100)
            rec[f"n_{lab}"] = len(v)
    # 2026 YTD
    c_end = float(px[t]["close"].iloc[-1])
    base = px[t][px[t]["date"] <= "2025-12-31"]
    if len(base):
        rec["ytd2026"] = round((c_end / float(base["close"].iloc[-1]) - 1) * 100, 1)
    rec["last"] = {"date": str(px[t]["date"].iloc[-1].date()), "close": round(c_end, 2)}
    res[t] = rec

out = {
    "tickers": TICKERS, "names": NAME,
    "el_events_all": [{"onset": f"{e['onset'][0]}-{e['onset'][1]:02d}",
                       "end": f"{e['end'][0]}-{e['end'][1]:02d}",
                       "peak": e["peak"], "peak_ym": f"{e['peak_ym'][0]}-{e['peak_ym'][1]:02d}",
                       "len": e["len"]} for e in events],
    "current_event": {"onset": "2026-04", "oni_tail": "MJJ 2026 +1.39",
                      "cpc_20260813": "El Nino Advisory; >90% very strong for fall/winter 2026-27; 69% chance OND2026 RONI>=+2.5 historic"},
    "coverage": {t: {"start": str(px[t]["date"].iloc[0].date()), "end": str(px[t]["date"].iloc[-1].date()),
                     "n": len(px[t])} for t in px},
    "result": res,
    "meta": {"source": "Sina US daily (unadjusted, ETN no dividend)", "window_A": "onset-3m -> peak+3m",
             "window_B": "onset -> +12m"}
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nwritten:", OUT)
print("\n=== 事件窗口 A（onset-3m → peak+3m，%）===")
for t, r in sorted(res.items(), key=lambda x: -(x[1].get("avg_A") or -999)):
    print(f"{t:5s} {NAME[t]:12s} n={r.get('n_A',0)} avg={r.get('avg_A')} med={r.get('med_A')} win={r.get('win_A')}% "
          f"| YTD26={r['ytd2026']}")
print("\n=== 单事件明细 A / B ===")
for t, r in res.items():
    print(t, [(e["onset"], e.get("A_forecast_to_peak3"), e.get("B_onset_to_12m")) for e in r["events"]])
