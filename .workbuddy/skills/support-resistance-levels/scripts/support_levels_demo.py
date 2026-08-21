# -*- coding: utf-8 -*-
"""支撑/阻力位识别（任意标的日线）

方法论演示：把"看图识别支撑位"翻译成显式算法——
  ① Swing 分形识别（数字化"这里有个低点"）
  ② 水平聚类（数字化"这几个价位差不多，是一条线"）
  ③ 触及次数 + 触击后反应质量评分（数字化"这条线多重要"）
  ④ 破位检测（数字化"这条线还活着吗"）

用法:
  python support_levels_demo.py MS [--months 18] [--out results/support_ms_demo.json]
输出 JSON 供可视化；控制台只打摘要。
"""
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
# 向上查找含 data/ 的项目根（stock 根）
while ROOT and not os.path.isdir(os.path.join(ROOT, "data")):
    parent = os.path.dirname(ROOT)
    if parent == ROOT:
        break
    ROOT = parent
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

parser = argparse.ArgumentParser(description="支撑/阻力位识别")
parser.add_argument("ticker", nargs="?", default="MS", help="股票代码，如 GILD/CEG/VST/MS")
parser.add_argument("--months", type=int, default=18, help="识别窗口（月）")
parser.add_argument("--out", default=None, help="输出 JSON 路径")
args = parser.parse_args()

TICKER = args.ticker.upper()
MONTHS = args.months

def find_csv(tk):
    p = os.path.join(DATA, tk.lower())
    if not os.path.isdir(p):
        return None
    for f in os.listdir(p):
        if f.startswith("BATS_"):
            continue
        if f.endswith(".csv") and tk.upper() in f.upper():
            return os.path.join(p, f)
    return None

csv_path = find_csv(TICKER)
if not csv_path:
    print(f"未找到 {TICKER} 数据（data/{TICKER.lower()}/ 下无对应 CSV）")
    sys.exit(1)
df = pd.read_csv(csv_path, parse_dates=["date"])
df = df[["date", "open", "high", "low", "close"]].sort_values("date").reset_index(drop=True)
df = df.dropna()

# ---- ATR14（Wilder 平滑）----
prev = df["close"].shift(1)
tr = pd.concat([(df["high"] - df["low"]),
                (df["high"] - prev).abs(),
                (df["low"] - prev).abs()], axis=1).max(axis=1)
df["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()

# ---- 识别窗口：近 N 个月（当前级别的支撑/阻力）----
cutoff = pd.Timestamp.now() - pd.DateOffset(months=MONTHS)
df = df[df["date"] >= cutoff].reset_index(drop=True)
N = len(df)
high, low, close = df["high"].values, df["low"].values, df["close"].values
atr_med = float(np.median(df["atr14"].tail(60)))
tol = 0.75 * atr_med  # 同一水平的价格容差（约 1% 现价量级）
print(f"[{TICKER}] 窗口 {df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}  n={N}  现价={close[-1]:.2f}")
print(f"  ATR14 中位(近60日)={atr_med:.2f}  水平聚类容差 tol={tol:.2f} (±{tol/close[-1]*100:.1f}%)")


# ---- ① 分形 swing（左右各 3 根 K 线的极值）----
def find_pivots(vals, n=3, kind="low"):
    idxs = []
    for i in range(n, len(vals) - n):
        w = vals[i - n:i + n + 1]
        if (vals[i] == w.min() if kind == "low" else vals[i] == w.max()) and (w == vals[i]).sum() == 1:
            idxs.append(i)
    return idxs


piv_low = find_pivots(low, 3, "low")
piv_high = find_pivots(high, 3, "high")
print(f"swing low 数={len(piv_low)}  swing high 数={len(piv_high)}")


# ---- ② 一维水平聚类（贪心，容差 tol 内并为一带）----
def cluster(prices, tol):
    """prices: 聚类依据（swing 价）. 返回 [{"center","count","items"}] 已按 center 排序"""
    if not prices:
        return []
    ps = sorted(prices)
    clusters = []
    for p in ps:
        if clusters and abs(p - clusters[-1]["center"]) <= tol:
            c = clusters[-1]
            c["count"] += 1
            c["center"] = (c["center"] * (c["count"] - 1) + p) / c["count"]
            c["items"].append(p)
        else:
            clusters.append({"center": p, "count": 1, "items": [p]})
    return clusters


supports = cluster([low[i] for i in piv_low], tol)
resists = cluster([high[i] for i in piv_high], tol)


# ---- ③ 评分：触击次数 × 触击后反应质量 × 时间持久度 ----
def evaluate(levels, kind):
    out = []
    for lv in levels:
        c = lv["center"]
        touch_idxs = [i for i in piv_low if abs(low[i] - c) <= tol] if kind == "sup" else \
                     [i for i in piv_high if abs(high[i] - c) <= tol]
        # 触击后 5 日最高反弹 / 最低回落
        reacts = []
        for i in touch_idxs:
            if i + 5 >= N:
                continue
            if kind == "sup":
                reacts.append(high[i + 1:i + 6].max() / low[i] - 1)
            else:
                reacts.append(low[i + 1:i + 6].min() / high[i] - 1)
        react_med = float(np.median(reacts)) if reacts else None
        first_t = df["date"].iloc[min(touch_idxs)]
        last_t = df["date"].iloc[max(touch_idxs)]
        days_live = (df["date"].iloc[-1] - first_t).days
        # 破位：最近 10 日内收盘穿透带边界（支撑看下沿，阻力看上沿）
        band_edge = c - tol if kind == "sup" else c + tol
        recent_close = close[-10:]
        broken = bool((recent_close < band_edge).any()) if kind == "sup" else bool((recent_close > band_edge).any())
        # 评分：触击次数 + 反应中位(%)，缺反应视为 0
        if kind == "sup" and (react_med is None or len(touch_idxs) < 1):
            continue
        if kind == "res" and (react_med is None or len(touch_idxs) < 1):
            continue
        score = (len(touch_idxs) ** 1.2) * max(react_med, 0.001) * min(1, days_live / 200) * 100
        out.append({
            "rank": 0,
            "kind": "支撑" if kind == "sup" else "阻力",
            "price": round(c, 2),
            "band_lo": round(c - tol, 2), "band_hi": round(c + tol, 2),
            "touches": len(touch_idxs),
            "react_med": round(react_med * 100, 2),   # %
            "first_touch": str(first_t.date()), "last_touch": str(last_t.date()),
            "days_live": int(days_live),
            "broken": broken,
            "score": round(score, 2),
        })
    out.sort(key=lambda x: -x["score"])
    for i, r in enumerate(out):
        r["rank"] = i + 1
    return out


sup_list = evaluate(supports, "sup")
res_list = evaluate(resists, "res")

# 有效性统计：所有 swing low 触击后 5 日反弹 vs 随机 5 日
rand5 = []
for i in range(0, N - 5):
    rand5.append(close[i + 5] / close[i] - 1)
sup5 = []
for i in piv_low:
    if i + 5 < N:
        sup5.append(high[i + 1:i + 6].max() / low[i] - 1)
valid = {
    "touch_n": len(sup5),
    "touch_med_5d_high": round(float(np.median(sup5)) * 100, 2),
    "random_med_5d_close": round(float(np.median(rand5)) * 100, 2),
    "touch_win_rate": round(float(np.mean([x > 0 for x in sup5])) * 100, 1),
}

# ---- 图数据：近 90 个交易日 K 线 + top 支撑/阻力 ----
CHART_N = 90
cdf = df.tail(CHART_N).reset_index(drop=True)
chart = {
    "dates": [str(d.date()) for d in cdf["date"]],
    "open": [round(float(x), 2) for x in cdf["open"]],
    "high": [round(float(x), 2) for x in cdf["high"]],
    "low": [round(float(x), 2) for x in cdf["low"]],
    "close": [round(float(x), 2) for x in cdf["close"]],
}
# 取落在图价格范围内的 top 支撑/阻力
price_lo, price_hi = min(cdf["low"]) * 0.99, max(cdf["high"]) * 1.01
def in_range(lv):
    return price_lo <= lv["price"] <= price_hi
levels_chart = [r for r in sup_list if in_range(r)][:6] + [r for r in res_list if in_range(r)][:6]

out = {
    "ticker": TICKER,
    "window": {"start": str(df["date"].iloc[0].date()), "end": str(df["date"].iloc[-1].date()),
               "n": int(N), "last_close": round(float(close[-1]), 2),
               "atr_med": round(atr_med, 2), "tol": round(tol, 2)},
    "supports": sup_list, "resists": res_list,
    "validity": valid,
    "chart": chart, "levels_chart": levels_chart,
}
os.makedirs(OUT, exist_ok=True)
out_path = args.out or os.path.join(OUT, f"support_{TICKER.lower()}.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"\nsaved: {out_path}")
print(f"\n=== 支撑位 Top（近{MONTHS}个月）===")
for r in sup_list[:8]:
    flag = " ⚠已破位" if r["broken"] else ""
    print(f"  #{r['rank']} {r['price']:.2f} 触击{r['touches']}次 反弹中位{r['react_med']:+.2f}% "
          f"首次{r['first_touch']} 最后{r['last_touch']} 存活{r['days_live']}天 分{r['score']}{flag}")
print(f"=== 阻力位 Top ===")
for r in res_list[:6]:
    flag = " ⚠已突破" if r["broken"] else ""
    print(f"  #{r['rank']} {r['price']:.2f} 触击{r['touches']}次 回落中位{r['react_med']:+.2f}% "
          f"最后{r['last_touch']} 分{r['score']}{flag}")
print(f"\n=== 支撑有效性验证 ===")
print(f"  swing low 触击后 5 日反弹中位 {valid['touch_med_5d_high']:+.2f}%（胜率 {valid['touch_win_rate']}%）")
print(f"  对照：任意日 5 日收益中位 {valid['random_med_5d_close']:+.2f}%")