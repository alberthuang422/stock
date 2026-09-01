# -*- coding: utf-8 -*-
"""APO 深度研究报告量化底稿（61 号）。
主口径：本地日线 adj_close（APO 2011-03-30 起 / BX / KKR / SPY，截至 2026-08-27）。
输出 results/61_apo_stats.json
"""
import json, os
import pandas as pd
import numpy as np

ROOT = r"C:\Users\Administrator\Desktop\stock\data"
def load(ticker):
    p = os.path.join(ROOT, ticker.lower(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.dropna(subset=["adj_close"]).sort_values("date").reset_index(drop=True)
    return df

apo = load("APO"); bx = load("BX"); kkr = load("KKR"); spy = load("SPY")
print("APO:", apo.date.min().date(), "->", apo.date.max().date(), len(apo))
print("BX :", bx.date.min().date(), "->", bx.date.max().date(), len(bx))
print("KKR:", kkr.date.min().date(), "->", kkr.date.max().date(), len(kkr))
print("SPY:", spy.date.min().date(), "->", spy.date.max().date(), len(spy))

def ser(df): return df.set_index("date")["adj_close"].astype(float)

sa, sb, sk, ss = ser(apo), ser(bx), ser(kkr), ser(spy)

def ret_series(s, start, end):
    w = s.loc[start:end]
    return w.iloc[-1] / w.iloc[0] - 1 if len(w) >= 2 else None

out = {}
# 基础快照
last = apo.iloc[-1]
out["snapshot"] = {
    "date": str(last.date.date()),
    "close": round(float(last.close), 2),
    "adj_close": round(float(last.adj_close), 2),
    "high52w": round(float(apo.adj_close.tail(252).max()), 2),
    "low52w": round(float(apo.adj_close.tail(252).min()), 2),
    "ytd2026": round(float(sa.loc["2026-01-01":].iloc[-1] / sa.loc["2025-12-31"] - 1) * 100, 2) if (sa.index >= "2025-12-31").any() else None,
}
# 修正 YTD：用 2025 最后一个交易日
prev = sa.loc[: "2025-12-31"]
if len(prev):
    out["snapshot"]["ytd2026"] = round((sa.loc["2026-01-01":].iloc[-1] / prev.iloc[-1] - 1) * 100, 2)

def perf(s, start, end, label):
    w = s.loc[start:end]
    if len(w) < 2: return None
    years = (w.index[-1] - w.index[0]).days / 365.25
    tot = w.iloc[-1] / w.iloc[0] - 1
    cagr = (1 + tot) ** (1 / years) - 1 if years > 0 else None
    daily = w.pct_change().dropna()
    vol = daily.std() * np.sqrt(252)
    dd = (w / w.cummax() - 1).min()
    return {"start": str(w.index[0].date()), "end": str(w.index[-1].date()),
            "total_pct": round(tot * 100, 2), "cagr_pct": round(cagr * 100, 2) if cagr else None,
            "ann_vol_pct": round(vol * 100, 2), "max_dd_pct": round(dd * 100, 2)}

# 区间表现主表（APO/SPY/BX/KKR 同口径：各自数据内最接近的起始日）
periods = {
    "1Y": ("2025-08-28", "2026-08-27"),
    "3Y": ("2023-08-28", "2026-08-27"),
    "5Y": ("2021-08-27", "2026-08-27"),
    "10Y": ("2016-08-29", "2026-08-27"),
    "2026YTD": ("2025-12-31", "2026-08-27"),
    "IPO": ("2011-03-30", "2026-08-27"),
}
# 用数据实际存在日期锚定：取每个数据里 >= 起始日的第一天
def anchor_start(s, dstr):
    d = pd.Timestamp(dstr)
    return s.index[s.index >= d][0]

res = {}
for label, (sd, ed) in periods.items():
    row = {}
    for name, s in [("APO", sa), ("SPY", ss), ("BX", sb), ("KKR", sk)]:
        if s.index.min().date().isoformat() > sd:  # 数据起点晚于区间起点则跳过
            continue
        a = anchor_start(s, sd)
        p = perf(s, a, ed, label)
        if p: row[name] = {"total_pct": p["total_pct"], "cagr_pct": p["cagr_pct"], "ann_vol_pct": p["ann_vol_pct"], "max_dd_pct": p["max_dd_pct"]}
    res[label] = row
out["periods"] = res

# 年度收益（2016-2026YTD，APO vs SPY vs BX vs KKR）
def yearly(s):
    s = s.copy()
    years = sorted(set(s.index.year))
    rows = {}
    for y in years:
        w = s[s.index.year == y]
        if len(w) < 2: continue
        rows[y] = round((w.iloc[-1] / w.iloc[0] - 1) * 100, 2)
    return rows

out["yearly"] = {"APO": yearly(sa), "SPY": yearly(ss), "BX": yearly(sb), "KKR": yearly(sk)}

# 60 日滚动相关性 APO vs SPY/BX/KKR（主口径 60 日）
def rolling_corr(a, b, win=60):
    a = a.reindex(a.index.union(b.index)).ffill()
    b = b.reindex(a.index).ffill()
    ra, rb = a.pct_change(), b.pct_change()
    df = pd.concat([ra, rb], axis=1, keys=["a", "b"]).dropna()
    c = df["a"].rolling(win).corr(df["b"])
    return [[str(d.date()), None if pd.isna(v) else round(float(v), 3)] for d, v in c.items()]

out["corr60"] = {
    "APO_vs_SPY": rolling_corr(sa, ss),
    "APO_vs_BX": rolling_corr(sa, sb),
    "APO_vs_KKR": rolling_corr(sa, sk),
}
# 全区间线性相关
def full_corr(a, b):
    a = a.reindex(a.index.union(b.index)).ffill()
    b = b.reindex(a.index).ffill()
    ra, rb = a.pct_change(), b.pct_change()
    df = pd.concat([ra, rb], axis=1, keys=["a", "b"]).dropna()
    return round(float(df["a"].corr(df["b"])), 3)
out["full_corr_daily"] = {
    "APO_vs_SPY": full_corr(sa, ss),
    "APO_vs_BX": full_corr(sa, sb),
    "APO_vs_KKR": full_corr(sa, sk),
    "BX_vs_KKR": full_corr(sb, sk),
}

# APO 近 60 日表现（对照本地最后 60 交易日）
w60 = sa.loc["2026-06-01":]
out["last60_pct"] = round((w60.iloc[-1] / w60.iloc[0] - 1) * 100, 2)

# 每股分红记录（从检索源：季度 0.5625）
out["dividend"] = {"qtr_per_share": 0.5625, "annualized": 2.25}

# 关键财务（检索源 2026Q2，标注时点便于 HTML 呈现）
out["fy2026q2"] = {
    "revenue_bn": 11.209, "rev_yoy_pct": 62.7, "net_income_bn": 1.314, "ni_yoy_pct": 115.0,
    "gaap_eps_basic": 2.18, "gaap_eps_diluted": 2.11,
    "fre_m": 785, "fre_eps": 1.26, "fre_yoy_pct": 25.2,
    "sre_m": 877, "sre_eps": 1.41, "sre_yoy_pct": 11.0,
    "ani_m": 1300, "ani_eps": 2.11,
    "aum_bn": 10500, "aum_yoy_pct": 25.0, "fgaum_bn": 8580, "fgaum_yoy_pct": 34.0,
    "inflows_bn": 600, "inflows_ytd_bn": 2980, "dry_powder_bn": 820,
    "origination_q_bn": 740, "origination_ytd_bn": 1500, "origination_ttm_bn": 3200,
    "fre_margin_pct": 58.5, "perpetual_pct_aum": 60, "perpetual_pct_fgaum": 70,
}
out["valuation_snapshot"] = {
    "date": "2026-09-01", "price": 131.29, "mktcap_bn": 101.8, "pe_ttm": 46.7,
    "pb_ttm": 3.95, "div_yield_pct": 1.63,
    "analyst_n": 23, "buy_pct": 74, "hold_pct": 26, "sell_pct": 0,
    "target_avg": 154.26, "target_high": 173.0, "target_low": 130.0,
}
out["peers"] = [
    {"ticker": "BX", "name": "Blackstone", "aum_bn": 13460, "mktcap_bn": 163.7, "pe_ttm": 30.6, "pb": 11.4, "div_yield": 3.82, "price": 136.98},
    {"ticker": "APO", "name": "Apollo Global", "aum_bn": 10470, "mktcap_bn": 101.8, "pe_ttm": 46.7, "pb": 4.0, "div_yield": 1.64, "price": 131.29},
    {"ticker": "KKR", "name": "KKR", "aum_bn": 7960, "mktcap_bn": 99.3, "pe_ttm": 34.1, "pb": 3.4, "div_yield": 0.71, "price": 106.57},
    {"ticker": "OWL", "name": "Blue Owl", "aum_bn": 3190, "mktcap_bn": 18.5, "pe_ttm": 148.9, "pb": 4.0, "div_yield": 7.73, "price": 11.78},
    {"ticker": "TPG", "name": "TPG", "aum_bn": 3060, "mktcap_bn": 20.5, "pe_ttm": 78.3, "pb": 7.1, "div_yield": 4.27, "price": 52.49},
]

os.makedirs(r"C:\Users\Administrator\Desktop\stock\results", exist_ok=True)
with open(r"C:\Users\Administrator\Desktop\stock\results\61_apo_stats.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written results/61_apo_stats.json")
print(json.dumps({k: out[k] for k in ["snapshot", "full_corr_daily", "last60_pct"]}, indent=1, ensure_ascii=False))
print("periods:", json.dumps(out["periods"], indent=1, ensure_ascii=False))