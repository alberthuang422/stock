# -*- coding: utf-8 -*-
"""CVS 中期选举（11月第一个周二）前后 1 个月窗口表现
- 事件：偶数年 11 月第一个周二；CVS 1973 起数据 → 1974-2022 共 13 届中期选举
- 主口径：Yahoo close 纯价格（拆股调整、股息不调），SPY 同口径
- 窗口（交易日）：pre=[T-21,T-1] 前1月 / day0=[T-1,T+1] / post=[T+1,T+21] 后1月 / full=[T-21,T+21]
- 对照：总统选举年同窗口
"""
import json
import os
from datetime import date, timedelta
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "cvs_midterm_event.json")


def load_close(tk):
    df = pd.read_csv(os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").dropna(subset=["close"]).set_index("date")["close"]
    return df


def first_tuesday_nov(y):
    d = date(y, 11, 1)
    while d.weekday() != 1:  # 0=周一
        d += timedelta(days=1)
    return d


def window_rets(px, ev, pre=21, post=21):
    """返回 dict：各窗口累计收益%"""
    ts = pd.Timestamp(ev)
    idx = px.index
    # 定位 T（≤选举日的最后交易日）
    pre_rows = idx[idx < ts]
    if len(pre_rows) < pre + 3:
        return None
    t_pos = len(pre_rows) - 1  # 选举日当日或前一日
    i_start, i_end = t_pos - pre, t_pos + post
    if i_end >= len(idx):
        i_end = len(idx) - 1
    s = px.iloc[i_start:i_end + 1]
    if len(s) < pre + post - 5:
        return None
    cum = {}
    cum["pre"] = round(float((s.iloc[pre] / s.iloc[0] - 1) * 100), 2)
    cum["post"] = round(float((s.iloc[-1] / s.iloc[pre] - 1) * 100), 2)
    cum["full"] = round(float((s.iloc[-1] / s.iloc[0] - 1) * 100), 2)
    cum["day0"] = round(float((s.iloc[pre + 1] / s.iloc[pre - 1] - 1) * 100), 2)
    return cum


cvs = load_close("CVS")
spy = load_close("SPY")

mid_ys = [y for y in range(1974, 2027, 4)]   # 偶数非总统年 = 中期选举
pres_ys = [y for y in range(1976, 2027, 4)]


def run(px_name, years):
    px = cvs if px_name == "CVS" else spy
    rows = []
    for y in years:
        ev = first_tuesday_nov(y)
        if y == 2026:  # 尚未发生
            continue
        w = window_rets(px, ev)
        if w is None:
            continue
        rows.append({"year": y, **w})
    df = pd.DataFrame(rows)
    out = {}
    for wkey, label in [("pre", "前1月"), ("post", "后1月"), ("full", "前后共2月"), ("day0", "选举日±1")]:
        v = df[wkey].values
        t0, p0 = stats.ttest_1samp(v, 0.0)
        out[wkey] = {
            "label": label, "n": int(len(v)),
            "mean": round(float(v.mean()), 2), "med": round(float(np.median(v)), 2),
            "win": round(float((v > 0).mean()) * 100, 1),
            "best": round(float(v.max()), 2), "worst": round(float(v.min()), 2),
            "t": round(float(t0), 2), "p": round(float(p0), 5),
            "pos_frac_p90": round(float(np.percentile(v, 90)), 2),
        }
    return {"rows": rows, "stats": out}


res = {
    "meta": {"note": "Yahoo close 纯价格口径；窗口=交易日；事件=11月第一个周二；2026-11-03 为下一届(未发生)"},
    "CVS_midterm": run("CVS", mid_ys),
    "CVS_president": run("CVS", pres_ys),
    "SPY_midterm": run("SPY", mid_ys),
    "SPY_president": run("SPY", pres_ys),
}

# 配对超额（CVS vs SPY，同期中期选举）
px_cvs, px_spy = cvs, spy
ex_rows = []
for y in mid_ys:
    if y == 2026:
        continue
    wc, ws = window_rets(px_cvs, first_tuesday_nov(y)), window_rets(px_spy, first_tuesday_nov(y))
    if wc and ws:
        ex_rows.append({"year": y, **{k: round(v - ws[k], 2) for k, v in wc.items()}})
ex = pd.DataFrame(ex_rows)
res["CVS_minus_SPY_midterm"] = {}
for wkey in ["pre", "post", "full", "day0"]:
    v = ex[wkey].values
    t0, p0 = stats.ttest_1samp(v, 0.0)
    res["CVS_minus_SPY_midterm"][wkey] = {
        "n": len(v), "mean": round(float(v.mean()), 2), "med": round(float(np.median(v)), 2),
        "win": round(float((v > 0).mean()) * 100, 1), "t": round(float(t0), 2), "p": round(float(p0), 5)}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("written:", OUT)

print("\n=== CVS 中期选举窗口统计 ===")
for k, v in res["CVS_midterm"]["stats"].items():
    print(f"{v['label']:12s} n={v['n']:3d} 均值={v['mean']:+6.2f}% 中位={v['med']:+6.2f}% 胜率={v['win']:5.1f}% 最好={v['best']:+6.1f}% 最差={v['worst']:+7.1f}% t={v['t']:+5.2f} p={v['p']:.4f}")
print("\n=== CVS 总统选举窗口（对照）===")
for k, v in res["CVS_president"]["stats"].items():
    print(f"{v['label']:12s} n={v['n']:3d} 均值={v['mean']:+6.2f}% 中位={v['med']:+6.2f}% 胜率={v['win']:5.1f}% t={v['t']:+5.2f} p={v['p']:.4f}")
print("\n=== CVS−SPY 超额（中期选举）===")
for k, v in res["CVS_minus_SPY_midterm"].items():
    print(f"{v['n']}届 {k:6s}: 超额均值 {v['mean']:+6.2f}% 中位 {v['med']:+6.2f}% 跑赢占比 {v['win']:5.1f}% p={v['p']:.4f}")
print("\n=== CVS 各届明细（中期选举）===")
for r in res["CVS_midterm"]["rows"]:
    print(f"  {r['year']}: 前1月 {r['pre']:+6.2f}%  选举日±1 {r['day0']:+6.2f}%  后1月 {r['post']:+6.2f}%  全程 {r['full']:+6.2f}%")
