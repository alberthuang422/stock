# -*- coding: utf-8 -*-
"""
SPY/QQQ 下跌波段中 玉米/大豆/小麦 表现统计 2026-09-10
口径：
- SPY 下跌波段 = 从局部高点回撤 ≥10% 的 peak→trough 区间（收复新高才闭合）
- 玉米/大豆：富途主连 2011-09 起；小麦：TradingView(2016-09~2017-11) 拼接富途(2017-11 起)
- 另做 60 日滚动条件统计（SPY 60 日收益分桶 × 农产品同期表现）
输出 results/agri_in_spy_downtrend_20260910.json
"""
import json, os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_spy(fn, col):
    df = pd.read_csv(os.path.join(BASE, fn), parse_dates=["date"]).set_index("date")
    return df[col].astype(float).sort_index()


spy = load_spy("data/spy/SPY, 1D.csv", "adj_close")
qqq = load_spy("data/qqq/QQQ, 1D.csv", "adj_close")
corn = load_spy("Temp/agri_zc_main_1D.csv", "close")
soy = load_spy("Temp/agri_zs_main_1D.csv", "close")
w_tv = load_spy("data/wheat_zw_1D.csv", "close")
w_fu = load_spy("Temp/agri_zw_main_1D.csv", "close")
wheat = pd.concat([w_tv[w_tv.index < "2017-11-06"], w_fu]).sort_index()
wheat = wheat[~wheat.index.duplicated(keep="last")]

AGRI = {"corn": corn, "soy": soy, "wheat": wheat}
SAMPLE_START = "2011-09-02"

# ---------- 1. SPY 下跌波段识别（回撤≥10%，peak→trough，收复新高闭合） ----------
def find_legs(px, thresh=-0.10, start=SAMPLE_START):
    p = px[px.index >= start]
    legs, peak, peak_d, trough, trough_d, in_leg = [], None, None, None, None, False
    for d, v in p.items():
        if peak is None or v > peak:
            if in_leg:  # 收复新高，闭合
                legs.append((peak_d, trough_d, peak, trough))
                in_leg = False
            peak, peak_d = v, d
            trough, trough_d = v, d
        dd = v / peak - 1
        if dd <= thresh and not in_leg:
            in_leg = True
            trough, trough_d = v, d
        if in_leg and v < trough:
            trough, trough_d = v, d
    if in_leg:  # 未闭合
        legs.append((peak_d, trough_d, peak, trough))
    return legs

legs = find_legs(spy)

episodes = []
for pk, tr, pv, tv_ in legs:
    row = {"peak": str(pk.date()), "trough": str(tr.date()),
           "days": (tr - pk).days, "spy_ret": round((tv_ / pv - 1) * 100, 1)}
    q = qqq[(qqq.index >= pk) & (qqq.index <= tr)]
    row["qqq_ret"] = round((q.iloc[-1] / q.iloc[0] - 1) * 100, 1) if len(q) > 1 else None
    for name, s in AGRI.items():
        w = s[(s.index >= pk) & (s.index <= tr)]
        row[name] = round((w.iloc[-1] / w.iloc[0] - 1) * 100, 1) if len(w) > 1 else None
    episodes.append(row)

# ---------- 2. 日度条件统计：下跌波段日 vs 其他日 ----------
day_stats = {}
leg_days = set()
for pk, tr, _, _ in legs:
    leg_days |= set(pd.date_range(pk, tr).date)

spy_d = spy[spy.index >= SAMPLE_START]
spy_ret = spy_d.pct_change()
for name, s in AGRI.items():
    r = s.pct_change().dropna()
    r = r[r.index >= max(pd.Timestamp(SAMPLE_START), r.index.min())]
    idx = r.index.intersection(spy_ret.index)
    r, sr = r[idx], spy_ret[idx]
    in_leg = np.array([d.date() in leg_days for d in idx])
    d_in, d_out = r[in_leg], r[~in_leg]
    day_stats[name] = {
        "n_leg": int(in_leg.sum()), "n_out": int((~in_leg).sum()),
        "leg_mean_bp": round(float(d_in.mean()) * 1e4, 2),
        "out_mean_bp": round(float(d_out.mean()) * 1e4, 2),
        "leg_pos_rate": round(float((d_in > 0).mean()) * 100, 1),
        "out_pos_rate": round(float((d_out > 0).mean()) * 100, 1),
        "corr_spy_leg": round(float(pd.Series(d_in).corr(pd.Series(sr[in_leg]))), 3),
        "corr_spy_out": round(float(pd.Series(d_out).corr(pd.Series(sr[~in_leg]))), 3),
        "corr_spy_all": round(float(r.corr(sr)), 3),
    }

# ---------- 3. 60 日滚动条件统计 ----------
def rolling_cond(win=60):
    out = {}
    spy_r = spy_d.pct_change(win)
    for name, s in AGRI.items():
        ar = s.pct_change(win)
        idx = ar.index.intersection(spy_r.index)
        ar, sr = ar[idx].dropna(), spy_r[idx]
        both = pd.concat([sr.rename("spy"), ar.rename("agri")], axis=1).dropna()
        buckets = {}
        for label, m in [("spy60<-8%", both.spy < -0.08),
                         ("-8%~-2%", (both.spy >= -0.08) & (both.spy < -0.02)),
                         ("-2%~+2%", (both.spy >= -0.02) & (both.spy <= 0.02)),
                         (">+2%", both.spy > 0.02)]:
            sub = both[m]
            buckets[label] = {"n": len(sub),
                              "agri_mean": round(float(sub.agri.mean()) * 100, 1) if len(sub) else None,
                              "agri_median": round(float(sub.agri.median()) * 100, 1) if len(sub) else None,
                              "pos_rate": round(float((sub.agri > 0).mean()) * 100, 1) if len(sub) else None}
        # 深跌桶里 农产品 vs SPY 方向一致性
        deep = both[both.spy < -0.08]
        out[name] = {"buckets": buckets,
                     "corr60_all": round(float(both.spy.corr(both.agri)), 3),
                     "corr60_deep": round(float(deep.spy.corr(deep.agri)), 3) if len(deep) > 10 else None}
    return out

roll60 = rolling_cond(60)

# ---------- 4. 汇总 ----------
res = {"sample": {"corn_soy": "2011-09-02~2026-09-08", "wheat": "2016-09-05~2026-09-08",
                  "spy_bench": "SPY adj_close, 回撤≥10% peak→trough"},
       "episodes": episodes, "day_stats": day_stats, "roll60": roll60}
fn = os.path.join(BASE, "results/agri_in_spy_downtrend_20260910.json")
json.dump(res, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", fn)

pd.set_option("display.width", 160)
print("\n=== SPY 下跌波段（回撤≥10%）期间表现（%） ===")
print(pd.DataFrame(episodes).to_string(index=False))
print("\n=== 日度条件统计（下跌波段日 vs 其他日） ===")
print(pd.DataFrame(day_stats).T.to_string())
print("\n=== 60 日滚动分桶 ===")
for name, d in roll60.items():
    print(f"\n[{name}] corr60_all={d['corr60_all']} corr60_deep={d['corr60_deep']}")
    print(pd.DataFrame(d["buckets"]).T.to_string())
