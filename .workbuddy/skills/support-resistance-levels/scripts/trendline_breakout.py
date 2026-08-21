# -*- coding: utf-8 -*-
"""下降趋势线识别 + 突破检测（事件研究版）

方法论（把"看图看突破下降趋势线"翻译成显式算法）：
  ① Swing high 分形（左右各 3 根极值）→ 数字化"这里有个反弹高点"
  ② 下降链拟合：取最近 2~4 个依次降低的 swing high，OLS 拟合直线，
     要求斜率显著为负(斜率<0 且 R²≥0.6) → 数字化"空头持续在更低的价位卖出"
  ③ 趋势线活性：当前收盘价须位于线下方（线值 - 收盘 > 0.15×ATR）→ "下降趋势还在"
  ④ 突破事件：收盘价从下方上穿趋势线值；此后 30 日内不重复计数（冷却合并）
  ⑤ 事件研究：突破后 1/5/10/20 日收益 vs 对照（全部交易日 / 阴跌未突破日），
     并测"阳线突破""放量突破""两日确认"等过滤是否提升胜率

统计口径：正常 100% 收益
"""
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
while ROOT and not os.path.isdir(os.path.join(ROOT, "data")):
    parent = os.path.dirname(ROOT)
    if parent == ROOT:
        break
    ROOT = parent
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

parser = argparse.ArgumentParser(description="下降趋势线突破扫描")
parser.add_argument("tickers", nargs="*", default=["GILD", "CEG", "VST", "MS"],
                    help="股票代码列表（默认 GILD CEG VST MS）")
parser.add_argument("--out", default=None, help="输出 JSON 路径")
args = parser.parse_args()
TICKERS = [t.upper() for t in args.tickers]

def load(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df[["date", "open", "high", "low", "close", "volume"]].sort_values("date").reset_index(drop=True)
    return df.dropna().reset_index(drop=True)

def add_atr(df, n=14):
    prev = df["close"].shift(1)
    tr = pd.concat([(df["high"] - df["low"]),
                    (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(alpha=1 / n, adjust=False).mean()
    return df

def swing_highs(df, k=3):
    """返回 swing high 的索引列表（分形：左右各 k 根的最大值）"""
    h = df["high"].values
    idx = []
    for i in range(k, len(df) - k):
        w = h[i - k:i + k + 1]
        if h[i] == w.max() and (w == h[i]).sum() == 1:
            idx.append(i)
    return idx

def fit_line(xs, ys):
    """OLS 拟合，返回 (slope, intercept, r2)"""
    x = np.array(xs, float)
    y = np.array(ys, float)
    if len(x) < 2:
        return None
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return b, a, r2

def scan_ticker(tk):
    df = add_atr(load(tk))
    n = len(df)
    h = df["high"].values
    c = df["close"].values
    o = df["open"].values
    v = df["volume"].values
    atr = df["atr"].values

    wins = 60         # 回看窗口（根）
    mink = 2          # 下降链最少高点数
    maxk = 4          # 最多用 4 个高点拟合
    r2_min = 0.60     # 拟合质量
    gap_min = 6       # 两个高点之间最少隔 6 根
    atr_close = 0.15  # 收盘须在线下方 0.15×ATR 才算"趋势存活"
    cooldown = 30     # 突破后冷却

    events = []       # 突破事件
    active_lines = {} # 供可视化：t -> 线参数

    last_ev = -9999
    for t in range(wins + maxk, n):
        # 找窗口内 swing high
        lo = t - wins
        sw = [i for i in swing_highs(df.iloc[lo:t + 1])]
        if len(sw) < mink:
            continue
        sw = [lo + i for i in sw]  # 全局索引
        # 取最近至多 maxk 个高点，且时间上依次至少隔 gap_min
        chain = []
        for i in reversed(sw):
            if chain and chain[-1] - i < gap_min:
                continue
            chain.append(i)
            if len(chain) >= maxk:
                break
        chain = chain[::-1]
        if len(chain) < mink:
            continue
        # 高点价格必须依次下降（严格递减，允许微小相等）
        pxs = [h[i] for i in chain]
        if not all(pxs[j + 1] < pxs[j] for j in range(len(pxs) - 1)):
            continue
        fit = fit_line(chain, pxs)
        if fit is None:
            continue
        slope, intercept, r2 = fit
        if slope >= 0 or r2 < r2_min:
            continue
        # 当前线值
        line_val = slope * t + intercept
        atr_now = atr[t]
        # 活性：最近 3 根收盘都在线下方·且有一定距离（趋势未被突破）
        below = all(c[t - j] < line_val - atr_close * atr_now for j in range(min(3, t - lo)))
        if not below:
            # 若窗口内最近已突破过（收盘高于线值），仍记录突破时刻用
            pass
        # 突破：当日收盘上穿线值，且前一日在线下方
        if t >= 1 and c[t - 1] < line_val - atr_close * atr_now and c[t] > line_val:
            if t - last_ev >= cooldown:
                events.append({
                    "t": t, "date": str(df["date"].iloc[t].date()),
                    "price": round(float(c[t]), 2),
                    "line_val": round(float(line_val), 2),
                    "slope_per_day": round(float(slope), 4),
                    "r2": round(float(r2), 3),
                    "touch_highs": len(chain),
                    "rise_pct": round((c[t] / c[t - 1] - 1) * 100, 2),  # 突破日涨幅
                    "gap_pct": round((o[t] / c[t - 1] - 1) * 100, 2),    # 跳空
                    "vol_ratio": round(float(v[t]) / float(np.median(v[max(0, t - 20):t])), 2),
                    "atr_pct": round(float(atr_now) / c[t] * 100, 2),
                    "above_pct": round((c[t] / line_val - 1) * 100, 2),  # 收盘高于线 %
                })
                last_ev = t
        # 记录线（仅当活性成立）
        if below:
            active_lines[t] = {
                "line_val": float(line_val), "slope": float(slope), "intercept": float(intercept),
                "anchors": chain, "r2": float(r2),
            }

    # ---- 事件研究 ----
    res = []
    for ev in events:
        t = ev["t"]
        row = {"date": ev["date"], "price": ev["price"], "rise_pct": ev["rise_pct"],
               "vol_ratio": ev["vol_ratio"], "atr_pct": ev["atr_pct"]}
        for k in (1, 5, 10, 20):
            if t + k < n:
                row[f"fwd{k}"] = round((c[t + k] / c[t] - 1) * 100, 2)
            else:
                row[f"fwd{k}"] = None
        res.append(row)

    # 对照：全部交易日 fwd
    def fwd_array(k):
        return np.array([(c[t + k] / c[t] - 1) * 100 for t in range(0, n - k)])

    def stats(vals):
        v = np.array(vals)
        if len(v) == 0:
            return None
        return {"n": int(len(v)), "mean": round(float(v.mean()), 2),
                "median": round(float(np.median(v)), 2),
                "win": round(float(np.mean(v > 0)) * 100, 1)}

    out = {
        "ticker": tk,
        "window": {"start": str(df["date"].iloc[0].date()), "end": str(df["date"].iloc[-1].date()), "n": int(n)},
        "events": res,
        "ctrl": {str(k): stats([(c[t + k] / c[t] - 1) * 100 for t in range(0, n - k)]) for k in (1, 5, 10, 20)},
        "latest_line": None,
        "active_count": len(active_lines),
        "last_active_date": str(df["date"].iloc[max(active_lines)].date()) if active_lines else None,
        "last_active": (active_lines[max(active_lines)] if active_lines else None),
        "chart_line": None,
    }
    # 若最后 10 日内有活性趋势线 → 供报告展示"当前状态"
    if active_lines:
        lt = max(active_lines)
        if n - lt <= 10:
            lv = active_lines[lt]
            out["latest_line"] = {
                "from_idx": lt - 5, "to_idx": min(n - 1, lt + 5),
                "line_val": round(lv["line_val"], 2), "slope": round(lv["slope"], 4),
                "intercept": round(lv["intercept"], 2), "anchors": lv["anchors"], "r2": lv["r2"],
                "asof": str(df["date"].iloc[lt].date()),
            }
    # 找"最近一次突破"作为可视化案例（取最近 120 根内的最后一笔）
    recent_ev = [ev for ev in events if ev["t"] >= n - 150]
    if recent_ev:
        last_evt = recent_ev[-1]
        t0 = last_evt["t"]
        # 重建当时的线（用事件前一天的线参数）
        # 简化：从 events 里已有 line 参数，重算
        # 扫描最后一次带活性线的时刻
        cand = [t for t in active_lines if t <= t0]
        if cand:
            tt = max(cand)
            lv = active_lines[tt]
            seg = df.iloc[tt - (len(lv["anchors"]) + 3):t0 + 21]
            out["chart_line"] = {
                "ev_date": last_evt["date"],
                "ev_idx": t0,
                "line_anchor_idx": tt,  # 线定义时刻
                "fitted_from": lv["anchors"],
                "slope": lv["slope"], "intercept": lv["intercept"],
                "line_val_at_ev": round(float(lv["slope"] * t0 + lv["intercept"]), 2),
                "seg_start": str(seg["date"].iloc[0].date()),
                "seg_end": str(seg["date"].iloc[-1].date()),
            }
    return out

def main():
    all_out = {}
    for tk in TICKERS:
        r = scan_ticker(tk)
        all_out[tk] = r
        ev = r["events"]
        print(f"\n[{tk}] 窗口 {r['window']['start']} ~ {r['window']['end']}  突破事件 {len(ev)} 个")
        if ev:
            es = ev[-5:]
            for e in es:
                print(f"   {e['date']}  收盘{e['price']:.2f}（上穿线值±） 涨 {e['rise_pct']:+.2f}%  "
                      f"量比 {e['vol_ratio']:.1f}  fwd5={e.get('fwd5')}%  fwd20={e.get('fwd20')}%")
            # 汇总
            for k in (5, 10, 20):
                vals = [e.get(f"fwd{k}") for e in ev]
                vals = [v for v in vals if v is not None]
                if vals:
                    ctrlk = r["ctrl"][str(k)]
                    v = np.array(vals)
                    print(f"   fwd{k}: 突破 n={len(v)} 均{np.mean(v):+.2f}% 中位{np.median(v):+.2f}% 胜率{np.mean(v>0)*100:.0f}% | "
                          f"对照全史 n={ctrlk['n']} 均{ctrlk['mean']:+.2f}% 中位{ctrlk['median']:+.2f}% 胜率{ctrlk['win']:.0f}%")
    out_path = args.out or os.path.join(OUT, "trendline_breakout.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_out, f, ensure_ascii=False, indent=1, default=str)
    print(f"\nsaved: {out_path}")

if __name__ == "__main__":
    main()