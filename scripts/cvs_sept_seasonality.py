# -*- coding: utf-8 -*-
"""CVS × SPY 每年 9 月季节性分析
口径：日复权收益按自然月累乘 → 9 月收益 = 8月末收盘→9月末收盘
- CVS 全历史（1973 起）与 SPY 可比区间（1993 起）双口径
- 月度收益全景：9 月在 12 个月中的排名
- 9 月 vs 非 9 月、胜率、分位数、t 检验
- CVS−SPY 超额（同一年配对）
"""
import json
import os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "cvs_sept_seasonality.json")


def load_px(tk):
    df = pd.read_csv(os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").dropna(subset=["adj_close"])
    return df.set_index("date")["adj_close"]


def monthly_ret(px):
    r = px.pct_change().dropna()
    m = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    m = m * 100  # %
    # 完整性判断：只有"最后一个数据月"可能是进行中的不完整月（如 2026-09 才过 1 天）。
    # 历史月其后仍有数据月 → 必然完整。避免用日历月末判断（月末落在周末会被误删）。
    last_key = m.index[-1]

    def is_complete(y, mo):
        if (y, mo) != last_key:
            return True
        end = pd.Timestamp(y, mo, 1) + pd.offsets.MonthEnd(0)
        days = px[(px.index.year == y) & (px.index.month == mo)].index
        return len(days) and days.max() >= end  # 数据确实走到了该月末

    idx = [(y, mo) for (y, mo) in m.index if is_complete(y, mo)]
    return m.loc[idx]


cvs = load_px("CVS")
spy = load_px("SPY")

mcvs_full = monthly_ret(cvs)          # 1973 起
# 可比区间：CVS 也裁剪到 SPY 起点之后，同一年份配对
cvs_93 = cvs[cvs.index >= pd.Timestamp("1993-01-01")]
mcvs_93 = monthly_ret(cvs_93)
mspy = monthly_ret(spy)

def stats_sep(m, name):
    sep = m.xs(9, level=1) if m.index.nlevels == 2 else m[m.index.get_level_values(1) == 9]
    other = m[m.index.get_level_values(1) != 9] if m.index.nlevels == 2 else m.drop(sep.index, errors='ignore')
    vals = sep.values
    t0, p0 = stats.ttest_1samp(vals, 0.0)
    years = [str(y) for y in sep.index.get_level_values(0)]
    return {
        "name": name, "n": int(len(vals)),
        "start": years[0], "end": years[-1],
        "mean": round(float(vals.mean()), 2),
        "med": round(float(np.median(vals)), 2),
        "win": round(float((vals > 0).mean()) * 100, 1),
        "best": round(float(vals.max()), 2),
        "worst": round(float(vals.min()), 2),
        "best_year": years[int(np.argmax(vals))],
        "worst_year": years[int(np.argmin(vals))],
        "t": round(float(t0), 2), "p": round(float(p0), 5),
        "other_months_mean": round(float(other.values.mean()), 2),
        "p90": round(float(np.percentile(vals, 90)), 2),
        "p25": round(float(np.percentile(vals, 25)), 2),
        "p75": round(float(np.percentile(vals, 75)), 2),
    }


# 月度全景：12 个月各自的平均收益与胜率（可比区间 1993 起，CVS 与 SPY）
def month_avg(m):
    rows = []
    for mo in range(1, 13):
        s = m[m.index.get_level_values(1) == mo]
        v = s.values
        rows.append({"month": mo, "mean": round(float(v.mean()), 2),
                     "med": round(float(np.median(v)), 2),
                     "win": round(float((v > 0).mean()) * 100, 1), "n": int(len(v))})
    return rows

full_stats = {
    "cvs_full": stats_sep(mcvs_full, "CVS 全历史(1973 起)"),
    "cvs_1993": stats_sep(mcvs_93, "CVS(1993 起)"),
    "spy_1993": stats_sep(mspy, "SPY(1993 起)"),
}

# 配对超额：同一年份 CVS_9 − SPY_9（1993-2026）
seps = pd.DataFrame({
    "cvs": mcvs_93.xs(9, level=1),
    "spy": mspy.xs(9, level=1),
}).dropna()
seps["ex"] = seps["cvs"] - seps["spy"]
t_ex, p_ex = stats.ttest_1samp(seps["ex"].values, 0.0)
excess_stats = {
    "n": int(len(seps)),
    "ex_mean": round(float(seps["ex"].mean()), 2),
    "ex_med": round(float(seps["ex"].median()), 2),
    "ex_win": round(float((seps["ex"] > 0).mean()) * 100, 1),  # CVS 跑赢 SPY 的年份占比
    "t": round(float(t_ex), 2), "p": round(float(p_ex), 5),
    "corr_cvs_spy_sep": round(float(seps["cvs"].corr(seps["spy"])), 3),
}

# 年度明细（1993 起，全部 9 月）
detail = []
for y, row in seps.iterrows():
    detail.append({"year": int(y), "cvs": round(float(row["cvs"]), 2),
                   "spy": round(float(row["spy"]), 2),
                   "ex": round(float(row["ex"]), 2)})

# 近 10 年（2017 起）
recent = [d for d in detail if d["year"] >= 2017]

# CVS 全历史 9 月明细（1973 起，含 SPY 缺失的早年）
sep_full = mcvs_full.xs(9, level=1)
detail_full = [{"year": int(y), "cvs": round(float(v), 2)}
               for y, v in sep_full.items()]

# 全历史 12 个月全景（CVS 1973 起）
month_cvs_full = month_avg(mcvs_full)
month_cvs_93 = month_avg(mcvs_93)
month_spy_93 = month_avg(mspy)

# 9 月内逐日表现（2020-2026，看 9 月弱是均匀走弱还是特定周）
def sept_daily(px, year):
    s = px[(px.index.year == year) & (px.index.month == 9)]
    if len(s) < 10:
        return None
    r = s.pct_change().dropna() * 100
    return [{"d": str(d.date()), "ret": round(float(v), 2)} for d, v in r.items()]

sept_daily_cvs = {y: sept_daily(cvs, y) for y in range(2020, 2027)}
sept_daily_spy = {y: sept_daily(spy, y) for y in range(2020, 2027)}

out = {
    "meta": {"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
             "note": "月收益 = 复权收盘价月度累乘(%)；9月 = 8月末→9月末"},
    "stats": full_stats,
    "excess": excess_stats,
    "detail_1993": detail,
    "detail_full": detail_full,
    "recent10": recent,
    "month_cvs_full": month_cvs_full,
    "month_cvs_93": month_cvs_93,
    "month_spy_93": month_spy_93,
    "sept_daily_cvs": sept_daily_cvs,
    "sept_daily_spy": sept_daily_spy,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT)

print("\n=== 9 月汇总 ===")
for k, v in full_stats.items():
    print(f"{v['name']:22s} n={v['n']:3d} 均值={v['mean']:+6.2f}% 中位={v['med']:+6.2f}% 胜率={v['win']:5.1f}% "
          f"最好={v['best']:+6.1f}%({v['best_year']}) 最差={v['worst']:+7.1f}%({v['worst_year']}) "
          f"t={v['t']:+5.2f} p={v['p']:.4f} 非9月均值={v['other_months_mean']:+6.2f}%")
print("\n=== 配对超额 CVS−SPY（1993-2026）===")
print(excess_stats)
print("\n=== 近 10 年 ===")
for d in recent:
    print(f"  {d['year']}: CVS {d['cvs']:+6.2f}%  SPY {d['spy']:+6.2f}%  超额 {d['ex']:+6.2f}%")

print("\n=== 12 个月均值排名（可比 1993 起）===")
for mo in [9]:
    a = next(x for x in month_spy_93 if x['month'] == 9)
    b = next(x for x in month_cvs_93 if x['month'] == 9)
    print(f"9月 SPY 均值 {a['mean']:+.2f}% 胜率 {a['win']}% | CVS 均值 {b['mean']:+.2f}% 胜率 {b['win']}%")
    print("SPY 月份排名:", sorted(month_spy_93, key=lambda x: -x['mean'])[:5])
    print("CVS 月份排名:", sorted(month_cvs_93, key=lambda x: -x['mean'])[:5])
    print("CVS(全历史)月份排名:", sorted(month_cvs_full, key=lambda x: -x['mean'])[:5])
