# -*- coding: utf-8 -*-
"""MOS vs CF 走势分化定量分析：多窗口涨跌幅、滚动相关性、相对强弱比。
输出 results/mos_cf_divergence.json 供 build 脚本注入报告。
"""
import json
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results", "mos_cf_divergence.json")

TICKERS = ["CF", "MOS", "NTR", "DAR", "XLE", "SPY"]


def load(tk):
    f = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(f, parse_dates=["date"])
    df = df.set_index("date").sort_index()
    return df["adj_close"].dropna()


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean(v) for v in x]
    if isinstance(x, (np.floating, np.integer)):
        x = float(x)
    if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
        return None
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, (pd.Timestamp,)):
        return str(x.date())
    return x


px = pd.DataFrame({tk: load(tk) for tk in TICKERS})
px = px.dropna()
ret = px.pct_change()

last_date = str(px.index[-1].date())

# ---- 多窗口涨跌幅（%） ----
windows = {
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "12M": 252,
    "YTD2026": None,
    "2Y": 504,
    "5Y": 1260,
    "since_2025-11-03": None,
}
perf = {}
for tk in TICKERS:
    perf[tk] = {}
    s = px[tk]
    for w, n in windows.items():
        if w == "YTD2026":
            base_idx = s.index[s.index < "2026-01-01"]
            base = s.loc[base_idx[-1]]
        elif w == "since_2025-11-03":
            sub = s.index[s.index >= "2025-11-03"]
            base = s.loc[sub[0]]
        else:
            if len(s) <= n:
                perf[tk][w] = None
                continue
            base = s.iloc[-1 - n]
        perf[tk][w] = (s.iloc[-1] / base - 1) * 100

# ---- 相关性矩阵（60 日、126 日、252 日窗口，日收益） ----
corr = {}
for wname, n in [("60D", 60), ("126D", 126), ("252D", 252)]:
    c = ret.iloc[-n:].corr()
    corr[wname] = {a: {b: c.loc[a, b] for b in TICKERS} for a in TICKERS}

# ---- CF×MOS 60 日滚动相关性 ----
roll_corr = ret["CF"].rolling(60).corr(ret["MOS"]).dropna()
roll_corr = roll_corr[roll_corr.index >= "2024-06-01"]

# ---- 相对强弱比 MOS/CF（归一化 2024-01-02=1） ----
ratio = (px["MOS"] / px["CF"])
ratio = ratio[ratio.index >= "2024-01-01"]
ratio_norm = ratio / ratio.iloc[0]

# ---- 归一化价格（2025-01-02=100）用于走势图 ----
norm_base_date = px.index[px.index >= "2025-01-01"][0]
norm = px[px.index >= "2025-01-01"] / px.loc[norm_base_date] * 100
# 再拉长到 2023-01 看全貌
norm2_base = px.index[px.index >= "2023-01-01"][0]
norm2 = px[px.index >= "2023-01-01"] / px.loc[norm2_base] * 100

# ---- 年化波动率（60 日） ----
vol60 = (ret.iloc[-60:].std() * np.sqrt(252) * 100).to_dict()

# ---- 最大回撤（2025-01 以来） ----
def max_dd(s):
    seg = s[s.index >= "2025-01-01"]
    peak = seg.cummax()
    dd = (seg / peak - 1) * 100
    return float(dd.min())

mdd = {tk: max_dd(px[tk]) for tk in TICKERS}

# ---- 最新价格 ----
last = {tk: float(px[tk].iloc[-1]) for tk in TICKERS}

out = {
    "as_of": last_date,
    "last_price": last,
    "perf_pct": perf,
    "corr": corr,
    "roll_corr_cf_mos": {str(d.date()): v for d, v in roll_corr.items()},
    "ratio_mos_cf_norm": {str(d.date()): v for d, v in ratio_norm.items()},
    "norm_2025": {tk: {str(d.date()): v for d, v in norm[tk].items()} for tk in TICKERS},
    "norm_2023": {tk: {str(d.date()): v for d, v in norm2[tk].items()} for tk in TICKERS},
    "vol60_ann_pct": vol60,
    "max_dd_since_2025_pct": mdd,
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(clean(out), f, ensure_ascii=False)

# 控制台摘要
print("as_of:", last_date)
print("\n== 多窗口涨跌幅(%) ==")
print(pd.DataFrame(perf).round(1).to_string())
print("\n== 60D 相关性 ==")
print(pd.DataFrame(corr['60D']).round(2).to_string())
print("\nvol60(%):", {k: round(v, 1) for k, v in vol60.items()})
print("maxDD since 2025(%):", {k: round(v, 1) for k, v in mdd.items()})
print("\nJSON ->", OUT)
