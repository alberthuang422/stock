# -*- coding: utf-8 -*-
"""银行走弱 → 科技股表现 相关性分析

走弱信号（对 KBWB 定义，把"看图判断走弱"显式算法化）：
  信号A · EMA20 跌破且多日未修复：
    KBWB 收盘跌破 EMA20，且连续 N 日（默认 5）收盘都留在 EMA20 下方 → 走弱确认。
    事件点 = 确认当日；此后回到 EMA20 上方视为修复。
  信号B · 跌破上升趋势线：
    取近 60 日内最近 2~4 个依次抬升的 swing low（分形，左右各 3 根），OLS 拟合，
    要求斜率>0 且 R²≥0.6；当前收盘自上方下穿趋势线值 → 走弱事件（30 日冷却去重）。

分析对象（科技）：SOXX（半导体）、XLK（科技板块）。
输出维度：
  1) 事件研究：走弱信号后 SOXX/XLK 的 fwd1/5/10/20 收益 vs 全样本基线
  2) 状态条件相关：KBWB 处于走弱状态 vs 正常状态时，
     KBWB↔SOXX / KBWB↔XLK 日收益相关系数、科技条件收益
  3) 分信号类型（A/B）与分科技标的交叉
  4) 近 3 年 / 近 1 年子样本
输出 results/kbwb_tech_weakness.json；控制台打汇总 KPI。
"""
import os
import json
import math

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

TECHS = ["SOXX", "XLK"]

# ---------- 走弱信号参数 ----------
EMA_N = 20          # EMA 周期
REPAIR_DAYS = 5     # 跌破 EMA20 后连续 N 日未修复 → 确认走弱
TREND_WIN = 60      # 上升趋势线回看窗口
TREND_MIN, TREND_MAX = 2, 4
TREND_R2 = 0.60
TREND_GAP = 6
TREND_COOLDOWN = 30


def load(tk: str) -> pd.DataFrame:
    p = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df[["date", "adj_close", "open", "high", "low", "close", "volume"]].copy()
    df = df.rename(columns={"adj_close": "px"})
    df["ret"] = df["px"].pct_change() * 100
    return df


def add_atr(df, n=14):
    prev = df["px"].shift(1)
    tr = pd.concat([(df["high"] - df["low"]),
                    (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(alpha=1 / n, adjust=False).mean()
    return df


def swing_lows(df, k=3):
    """分形 swing low：左右各 k 根内的唯一最小值"""
    l = df["low"].values
    idx = []
    for i in range(k, len(df) - k):
        w = l[i - k:i + k + 1]
        if l[i] == w.min() and (w == l[i]).sum() == 1:
            idx.append(i)
    return idx


def fit_line(xs, ys):
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


def signal_ema(kbwb: pd.DataFrame):
    """信号A：EMA20 跌破且 REPAIR_DAYS 日未修复。返回 (确认日索引集合, 走弱状态布尔序列)"""
    px = kbwb["px"]
    ema = px.ewm(span=EMA_N, adjust=False).mean()
    below = px < ema                       # 收盘在 EMA20 下方
    # 连续在下方天数
    grp = (below != below.shift()).cumsum()
    streak = below.groupby(grp).cumcount() + 1
    below = below.values
    streak = streak.fillna(0).values
    # 状态：连续下方天数 >= REPAIR_DAYS 即为走弱状态
    weak_state = below & (streak >= REPAIR_DAYS)
    # 事件点：状态由 False 转 True 的那一天
    confirm_idx = list(np.where(weak_state & ~np.roll(weak_state, 1))[0])
    if confirm_idx and confirm_idx[0] == 0:
        confirm_idx = confirm_idx[1:]
    return confirm_idx, weak_state


def signal_trendline(kbwb: pd.DataFrame):
    """信号B：跌破上升趋势线。返回 (事件日索引集合, 走弱状态布尔序列)"""
    df = add_atr(kbwb.copy())
    n = len(df)
    l = df["low"].values
    c = df["px"].values
    events = []
    weak_state = np.zeros(n, dtype=bool)
    last_ev = -10 ** 9
    for t in range(TREND_WIN + TREND_MAX, n):
        lo = t - TREND_WIN
        sw = [i for i in swing_lows(df.iloc[lo:t + 1])]
        if len(sw) < TREND_MIN:
            continue
        sw = [lo + i for i in sw]
        chain = []
        for i in reversed(sw):
            if chain and chain[-1] - i < TREND_GAP:
                continue
            chain.append(i)
            if len(chain) >= TREND_MAX:
                break
        chain = chain[::-1]
        if len(chain) < TREND_MIN:
            continue
        pxs = [l[i] for i in chain]
        if not all(pxs[j + 1] > pxs[j] for j in range(len(pxs) - 1)):
            continue  # 必须依次抬升
        fit = fit_line(chain, pxs)
        if fit is None:
            continue
        slope, intercept, r2 = fit
        if slope <= 0 or r2 < TREND_R2:
            continue
        line_val = slope * t + intercept
        line_prev = slope * (t - 1) + intercept
        # 跌破：收盘在线下方 → 走弱状态
        if c[t] < line_val:
            weak_state[t] = True
            # 事件：自上方下穿（昨日收盘在线上）+ 冷却去重
            if c[t - 1] >= line_prev and t - last_ev >= TREND_COOLDOWN:
                events.append(t)
                last_ev = t
    return events, weak_state


def fwd_ret(df, idx, h):
    """idx 起 h 日后收益 %（复权价口径）"""
    j = idx + h
    if j >= len(df):
        return None
    return float(df["px"].iloc[j] / df["px"].iloc[idx] - 1) * 100


def baseline_fwd(df, min_idx=0):
    """全样本基线 fwd 收益（用于对照）"""
    out = {}
    for h in (1, 5, 10, 20):
        v = []
        for i in range(min_idx, len(df) - h):
            v.append(df["px"].iloc[i + h] / df["px"].iloc[i] - 1)
        v = np.array(v) * 100
        out[h] = {"mean": round(float(v.mean()), 3), "med": round(float(np.median(v)), 3),
                  "win": round(float((v > 0).mean()) * 100, 1), "n": int(len(v))}
    return out


def event_study(df, event_idx, min_idx=0):
    ev = [i for i in event_idx if i >= min_idx and i + 20 < len(df)]
    out = {"n": len(ev)}
    for h in (1, 5, 10, 20):
        v = np.array([fwd_ret(df, i, h) for i in ev])
        out[h] = {"mean": round(float(v.mean()), 3), "med": round(float(np.median(v)), 3),
                  "win": round(float((v > 0).mean()) * 100, 1)} if len(v) else None
    out["dates"] = [str(df["date"].iloc[i].date()) for i in ev]
    return out


def corr(x, y):
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 10 or np.var(x) == 0 or np.var(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def regime_corr(kbwb, tech, weak_state, min_idx=0):
    """走弱状态 vs 正常状态下 KBWB↔tech 日收益相关 + tech 条件收益"""
    m = pd.merge(kbwb[["date", "ret"]], tech[["date", "ret"]],
                 on="date", suffixes=("_b", "_t")).reset_index(drop=True)
    # 对齐 weak_state 到 merge 后的日期
    st = pd.Series(weak_state, index=kbwb["date"])
    m["weak"] = m["date"].map(st).fillna(False).values
    m = m[m.index >= 0].reset_index(drop=True)
    if min_idx:
        cutoff = kbwb["date"].iloc[min_idx]
        m = m[m["date"] >= cutoff].reset_index(drop=True)
    xb, xt = m["ret_b"].values, m["ret_t"].values
    wk = m["weak"].values
    out = {"n_total": int(len(m)), "n_weak": int(wk.sum())}
    for label, mask in (("weak", wk), ("normal", ~wk)):
        if mask.sum() < 15:
            out[label] = None
            continue
        out[label] = {
            "corr": round(corr(xb[mask], xt[mask]), 4),
            "n": int(mask.sum()),
            "tech_mean_ret": round(float(xt[mask].mean()), 4),      # tech 日均 %
            "tech_on_bankdn": round(float(xt[mask & (xb < 0)].mean()), 4)
                if (mask & (xb < 0)).sum() > 10 else None,          # 银行跌日 tech 均 %
            "bank_dn_share": round(float((xb[mask] < 0).mean()) * 100, 1),
        }
    return out


def current_status(kbwb, ema_state, tl_state):
    """KBWB 当前走弱状态快照"""
    ema = kbwb["px"].ewm(span=EMA_N, adjust=False).mean()
    below = (kbwb["px"] < ema).values
    cnt = 0
    for v in reversed(below):
        if v:
            cnt += 1
        else:
            break
    px = float(kbwb["px"].iloc[-1])
    ema_v = float(ema.iloc[-1])
    return {
        "date": str(kbwb["date"].iloc[-1].date()),
        "close": round(px, 2),
        "ema20": round(ema_v, 2),
        "ema_gap_pct": round((px / ema_v - 1) * 100, 2),
        "below_ema_days": int(cnt),
        "below_ema": bool(below[-1]),
        "ema_weak_active": bool(ema_state[-1]),
        "trend_weak_active": bool(tl_state[-1]),
        "last_ema_event": str(kbwb["date"].iloc[signal_ema(kbwb)[0][-1]].date()) if signal_ema(kbwb)[0] else None,
    }


def build_chart(kbwb, ema_state, tl_state):
    """近 3 年 KBWB 价格 + EMA20 + 走弱状态（供报告图）"""
    ema = kbwb["px"].ewm(span=EMA_N, adjust=False).mean()
    sub = kbwb[kbwb["date"] >= "2023-08-01"].reset_index(drop=True)
    ema_s = ema[sub.index + (len(kbwb) - len(sub))]
    out = []
    for i in range(len(sub)):
        gi = i + (len(kbwb) - len(sub))
        out.append({
            "date": str(sub["date"].iloc[i].date()),
            "close": round(float(sub["px"].iloc[i]), 2),
            "ema": round(float(ema_s.iloc[i]), 2),
            "weak": bool(ema_state[gi] or tl_state[gi]),
        })
    return out


def main():
    kbwb = load("KBWB")
    techs = {t: load(t) for t in TECHS}

    # 统一窗口起点 = 三者都有数据的起点
    start = kbwb["date"].iloc[0]
    for t in TECHS:
        start = max(start, techs[t]["date"].iloc[0])
    kbwb = kbwb[kbwb["date"] >= start].reset_index(drop=True)
    techs = {t: techs[t][techs[t]["date"] >= start].reset_index(drop=True) for t in TECHS}
    print(f"统一窗口: {kbwb['date'].iloc[0].date()} ~ {kbwb['date'].iloc[-1].date()}  n={len(kbwb)}")

    # ---------- 信号 ----------
    ema_ev, ema_state = signal_ema(kbwb)
    tl_ev, tl_state = signal_trendline(kbwb)
    # 合并走弱状态（任一信号触发即为走弱）
    weak_any = ema_state | tl_state
    print(f"信号A(EMA20 跌破{REPAIR_DAYS}日未修复) 事件 {len(ema_ev)} 次；状态天数 {int(ema_state.sum())}")
    print(f"信号B(跌破上升趋势线) 事件 {len(tl_ev)} 次；状态天数 {int(tl_state.sum())}")
    print(f"合并走弱状态天数 {int(weak_any.sum())} ({weak_any.mean()*100:.1f}%)")

    # 分阶段最小索引
    def min_idx(datestr):
        arr = kbwb[kbwb["date"] >= datestr].index
        return int(arr[0]) if len(arr) else 0

    # ---------- 事件研究 ----------
    ev_study = {}
    for sig_name, ev_idx in (("ema", ema_ev), ("trendline", tl_ev)):
        block = {}
        for scope, mi in (("full", 0), ("3y", min_idx("2023-08-01")), ("1y", min_idx("2025-08-01"))):
            block[scope] = {t: event_study(techs[t], ev_idx, mi) for t in TECHS}
        ev_study[sig_name] = block

    # 基线
    base = {t: baseline_fwd(techs[t]) for t in TECHS}

    # ---------- 状态条件相关 ----------
    regime = {}
    for sig_name, state in (("ema", ema_state), ("trendline", tl_state), ("any", weak_any)):
        block = {}
        for scope, mi in (("full", 0), ("3y", min_idx("2023-08-01")), ("1y", min_idx("2025-08-01"))):
            block[scope] = {t: regime_corr(kbwb, techs[t], state, mi) for t in TECHS}
        regime[sig_name] = block

    # ---------- 走弱状态期间 KBWB 自身表现 ----------
    m_kbwb = kbwb[["date", "ret"]].copy()
    m_kbwb["weak"] = weak_any
    kb_weak = m_kbwb[m_kbwb["weak"]]["ret"]
    kb_norm = m_kbwb[~m_kbwb["weak"]]["ret"]

    # ---------- 走弱事件清单（近 2 年，供报告展示） ----------
    ev_list = []
    seen = set()
    for sig, ev_idx in (("EMA20跌破未修复", ema_ev), ("跌破上升趋势线", tl_ev)):
        for i in ev_idx:
            d = str(kbwb["date"].iloc[i].date())
            if kbwb["date"].iloc[i] >= pd.Timestamp("2024-08-01") and d not in seen:
                seen.add(d)
                ev_list.append({"date": d, "signal": sig,
                                "kbwb_f10": fwd_ret(kbwb, i, 10)})
    ev_list.sort(key=lambda x: x["date"])

    out = {
        "params": {"ema_n": EMA_N, "repair_days": REPAIR_DAYS, "trend_win": TREND_WIN,
                   "trend_r2": TREND_R2, "trend_cooldown": TREND_COOLDOWN},
        "period": {"start": str(kbwb["date"].iloc[0].date()),
                   "end": str(kbwb["date"].iloc[-1].date()), "n": int(len(kbwb))},
        "signal_counts": {
            "ema_events": len(ema_ev), "ema_state_days": int(ema_state.sum()),
            "trendline_events": len(tl_ev), "trendline_state_days": int(tl_state.sum()),
            "weak_any_days": int(weak_any.sum()),
            "weak_any_pct": round(float(weak_any.mean()) * 100, 1),
        },
        "baseline_fwd": base,
        "event_study": ev_study,
        "regime_corr": regime,
        "kbwb_state_ret": {"weak_mean": round(float(kb_weak.mean()), 4) if len(kb_weak) else None,
                           "normal_mean": round(float(kb_norm.mean()), 4) if len(kb_norm) else None,
                           "weak_days": int(len(kb_weak)), "normal_days": int(len(kb_norm))},
        "event_list_recent": ev_list,
        "current": current_status(kbwb, ema_state, tl_state),
        "chart": build_chart(kbwb, ema_state, tl_state),
        "meta": {"kbwb": "Invesco KBW Bank ETF（银行指数代理）",
                 "techs": {"SOXX": "iShares Semiconductor ETF（半导体）", "XLK": "Technology Select Sector SPDR（科技板块）"},
                 "note": "走弱=跌破EMA20多日未修复 或 跌破上升趋势线；事件研究统计信号后科技股前瞻收益，状态相关统计走弱期 KBWB↔科技 日收益相关",
                 "source": "Yahoo Finance 日线(复权收盘)",
                 "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date())},
    }

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "kbwb_tech_weakness.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nsaved: {path}")

    # ---------- 控制台汇总 ----------
    print("\n=== 基线前瞻收益（全样本，均值 %）===")
    for t in TECHS:
        b = base[t]
        print(f"  {t}: fwd1 {b[1]['mean']:+.3f}  fwd5 {b[5]['mean']:+.3f}  "
              f"fwd10 {b[10]['mean']:+.3f}  fwd20 {b[20]['mean']:+.3f}")

    for sig in ("ema", "trendline"):
        print(f"\n=== 事件研究 [{sig}] · 走弱信号后科技股前瞻收益（均值 % / 胜率 %）===")
        for scope in ("full", "3y", "1y"):
            line = f"  [{scope:4s}] "
            for t in TECHS:
                e = ev_study[sig][scope][t]
                if e["n"]:
                    line += f"{t} n={e['n']:2d} fwd5 {e[5]['mean']:+.2f}({e[5]['win']:.0f}%) fwd10 {e[10]['mean']:+.2f}({e[10]['win']:.0f}%) fwd20 {e[20]['mean']:+.2f}({e[20]['win']:.0f}%) | "
                else:
                    line += f"{t} n=0 | "
            print(line)

    print("\n=== 状态条件相关 · KBWB↔科技 日收益相关系数 ===")
    for sig in ("ema", "trendline", "any"):
        for scope in ("full", "3y", "1y"):
            line = f"  [{sig:9s}/{scope:4s}] "
            for t in TECHS:
                r = regime[sig][scope][t]
                if r["weak"] and r["normal"]:
                    line += (f"{t}: 走弱corr {r['weak']['corr']:+.3f}(n={r['weak']['n']}, tech均{r['weak']['tech_mean_ret']:+.3f}%) "
                             f"vs 正常corr {r['normal']['corr']:+.3f} | ")
                else:
                    line += f"{t}: 样本不足 | "
            print(line)

    print(f"\nKBWB 自身: 走弱状态日均 {out['kbwb_state_ret']['weak_mean']:+.3f}% "
          f"vs 正常日均 {out['kbwb_state_ret']['normal_mean']:+.3f}%")


if __name__ == "__main__":
    main()
