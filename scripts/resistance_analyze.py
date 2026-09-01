# -*- coding: utf-8 -*-
"""
阻力位识别：2023-01-01 至今，日线
方法：pivot high（左右各 W 根K线内最高，W=21 对应约1个月，组合出 2个月级别高点）
      -> 聚类（价格相近的 pivot 合并成阻力带）-> 评分（触达次数×强度）-> 输出 top 阻力位
"""
import json
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "resistance_20260902.json")

START = "2023-01-01"
W = 20          # pivot 窗口：左右各 20 个交易日（约1个月），两根合起来是 2个月级别
CLUSTER_PCT = 0.02    # 聚类容差 2%
TOUCH_PCT = 0.015     # 触达判定容差 1.5%


def load(tk):
    fn = os.path.join(DATA, tk, f"{tk}, 1D.csv")
    df = pd.read_csv(fn, parse_dates=["date"])
    df = df[df["date"] >= START].reset_index(drop=True)
    return df


def find_pivot_highs(df, w):
    """左右各 w 根内最高 -> pivot high 索引"""
    highs = df["high"].values
    n = len(highs)
    idx = []
    for i in range(w, n - w):
        left = highs[i - w:i]
        right = highs[i + 1:i + w + 1]
        if highs[i] >= left.max() and highs[i] > right.max():
            idx.append(i)
    return idx


def cluster(pivots, pct):
    """价格聚类：贪心从最低价开始，价格差 <= pct 并入同一带"""
    pivots = sorted(pivots, key=lambda p: p["price"])
    bands = []
    for p in pivots:
        if not bands:
            bands.append([p])
            continue
        last_band = bands[-1]
        if p["price"] <= last_band[0]["price"] * (1 + pct):
            last_band.append(p)
        else:
            bands.append([p])
    return bands


def score_band(band):
    """带强度评分：触达次数（关键）* 带内pivot数 * 时间跨度"""
    prices = [p["price"] for p in band]
    return len(prices), min(prices), max(prices)


def touches(df, price, pct):
    """统计收盘价接近该价位的触达次数（含曾经站上/被压回）"""
    m = (df["close"] >= price * (1 - pct)) & (df["close"] <= price * (1 + pct))
    return int(m.sum())


def main():
    with open(os.path.join(BASE, "Temp", "resistance_picks.json"), encoding="utf-8") as f:
        picks = json.load(f)["tickers"]
    result = {}
    for tk in picks:
        df = load(tk)
        if len(df) < 60:
            result[tk] = {"error": "数据不足"}
            continue
        last_close = float(df["close"].iloc[-1])
        last_date = str(df["date"].iloc[-1].date())
        piv_idx = find_pivot_highs(df, W)
        pivots = [{"idx": i, "price": float(df["high"].iloc[i]), "date": str(df["date"].iloc[i].date())}
                  for i in piv_idx]
        bands = cluster(pivots, CLUSTER_PCT)
        # 过滤：带内至少2个 pivot（级别大），单 pivot 但触达>=4 次也算强阻力
        strong_bands = [b for b in bands if len(b) >= 2 or touches(df, float(np.median([p["price"] for p in b])), TOUCH_PCT) >= 4]
        # 按 (带内pivot数, 触达次数) 综合排序
        scored = []
        for b in strong_bands:
            prices = [p["price"] for p in b]
            center = float(np.median(prices))
            cnt = touches(df, center, TOUCH_PCT)
            first_date = min(p["date"] for p in b)
            last_touch_idx = df.index[(df["close"] >= center * (1 - TOUCH_PCT)) &
                                      (df["close"] <= center * (1 + TOUCH_PCT))]
            last_touch = str(df["date"].iloc[last_touch_idx[-1]].date()) if len(last_touch_idx) else last_date
            scored.append({
                "price": round(center, 2),
                "level": round(center / last_close * 100, 1),   # 相对现价 %
                "pivots": len(b),
                "touches": cnt,
                "first_date": first_date,
                "last_touch": last_touch,
                "band": [round(p, 2) for p in prices],
            })
        # 综合分：pivots*2 + log1p(touches)*3
        for s in scored:
            s["score"] = round(s["pivots"] * 2 + np.log1p(s["touches"]) * 3, 1)
        scored.sort(key=lambda s: (-s["score"], -s["pivots"]))
        # 只保留现价上方的阻力位（level >= 102）且至少触达过 1 次
        scored = [s for s in scored if s["level"] >= 102 and s["touches"] >= 1]
        top = scored[:5]
        result[tk] = {
            "last_close": round(last_close, 2),
            "last_date": last_date,
            "start": START,
            "resistance": top,
            "summary": {
                "total_pivots": len(pivots),
                "bands_found": len(strong_bands),
            }
        }
        print(f"{tk}: 现价 {last_close:.2f} ({last_date}) | pivots={len(pivots)} bands={len(strong_bands)}")
        for s in top:
            print(f"   {s['price']:>10.2f}  ▲ {s['level']-100:5.1f}%  pivots={s['pivots']} touches={s['touches']} score={s['score']}  {s['first_date']}~{s['last_touch']}")
        if not top:
            print("   (无现价上方阻力 —— 处于历史新高区域)")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
