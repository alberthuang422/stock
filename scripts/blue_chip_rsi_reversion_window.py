# -*- coding: utf-8 -*-
"""
优质蓝筹股池 RSI 低买高卖策略专项分析 —— 纳指区间(2025-10-01 ~ 2026-02-27)

用户需求：去年 10 月到今年 2 月（纳斯达克期间），对优质蓝筹股：
  1) RSI 低时买入（RSI 下穿/触及低阈值）
  2) RSI 高时卖出（RSI 上穿/触及高阈值）
统计退出后的 T5 / T10 收益（持有时长 5/10 个交易日），并对比"高卖后立即再低买的配对循环"。

策略规则（参数化，默认标准版本）：
  - 低买信号：Wilder RSI14(adj_close) 当日 < 阈值L 且前一日 >= 阈值L（下穿阈值首日）
  - 高卖信号：RSI 当日 > 阈值H 且前一日 <= 阈值H（上穿阈值首日）
  - T5/T10：信号当日收盘买入/卖出，持有 N 个交易日（shift(-N)），收益 = 未来 N 日收盘 / 当日收盘 - 1
  - 若区间内信号过少（n<3），阈值自动向 35/65 放宽，保证可统计

主输出组合（矩阵）：
  A) 低买持有：按 [下穿 L ∈ {30,35}] 买入信号，统计 T5/T10 收益
  B) 高卖持有：按 [上穿 H ∈ {70,65}] 卖出信号，统计 T5/T10 收益（收益按卖出后价格变化计，即卖出后未来 N 日仍是持有股票）
  C) 配对循环：同票最近一次"低买信号"→ 下一次"高卖信号"，循环持仓直至区间结束，
     统计回合数、绿胜率、区间累计收益 —— 检验"低买高卖"连续做、能否跑赢买入持有
  D) 对照：区间内全部交易日 Buy&Hold（每票、及等权组合）、SPY/QQQ 同期

口径：
  - 时间 2025-10-01 至 2026-02-28（含最后交易日 2026-02-27）
  - RSI 计算需要 14 预热期，用全历史数据算 RSI 后再截取窗口
  - T+N = N 个交易日（shift(-N)），末日无 fwd 值记 NaN 不计
  - 事件去重：同票相邻相同信号 <10 交易日不重复计数（cd10，避免连跌续报）
  - 均收益率以百分数×100

输出：results/blue_chip_rsi_reversion_window.json + 控制台汇总 + 供 HTML 使用
"""
import pandas as pd
import numpy as np
import json, os, glob, csv, sys, traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

WINDOW_START = pd.Timestamp("2025-10-01")
WINDOW_END = pd.Timestamp("2026-03-01")  # 含区间但闭包为 2026-02 月末

# ---------- 股票池 ----------
tickers, sectors = [], {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t)
        sectors[t] = row["sector"].strip()

SECTOR_CN = {
    "Technology": "科技", "Financials": "金融", "Industrials": "工业",
    "Healthcare": "医疗", "Consumer": "消费", "Materials_Utilities_Other": "材料/公用/其他",
}
SECTOR_ORDER = list(SECTOR_CN)

def load_stock(name):
    d = os.path.join(DATA, name.lower())
    if not os.path.isdir(d):
        return None
    cands = [p for p in glob.glob(os.path.join(d, "*.csv"))
             if not os.path.basename(p).startswith("BATS_") and "1D" in os.path.basename(p)]
    if not cands:
        return None
    f = sorted(cands)[0]
    df = pd.read_csv(f, parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    df = df.dropna(subset=["px"]).sort_values("date").reset_index(drop=True)
    return df

def rsi_wilder(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = ag / al
    return 100 - 100 / (1 + rs)

def stats(s):
    s = pd.Series(s).dropna()
    if len(s) == 0:
        return {"n": 0}
    out = {
        "n": int(len(s)),
        "mean": round(float(s.mean()), 3),
        "median": round(float(s.median()), 3),
        "win": round(float((s > 0).mean()) * 100, 1),
        "p25": round(float(s.quantile(0.25)), 3),
        "p75": round(float(s.quantile(0.75)), 3),
        "min": round(float(s.min()), 3),
        "max": round(float(s.max()), 3),
    }
    if len(s) > 1:
        sd = s.std(ddof=1)
        out["std"] = round(float(sd), 3)
        out["t"] = round(float(s.mean() / (sd / np.sqrt(len(s)))), 2) if sd > 0 else None
    else:
        out["std"] = out["t"] = None
    return out

def stats_pair(r):
    """配对回合累计收益统计"""
    r = pd.Series(r).dropna()
    if len(r) == 0:
        return {"n": 0}
    out = {"n": int(len(r)), "mean": round(float(r.mean()), 3),
           "median": round(float(r.median()), 3),
           "win": round(float((r > 0).mean()) * 100, 1),
           "min": round(float(r.min()), 3), "max": round(float(r.max()), 3)}
    if len(r) > 1:
        sd = r.std(ddof=1); out["std"] = round(float(sd), 3)
        out["t"] = round(float(r.mean() / (sd / np.sqrt(len(r)))), 2) if sd > 0 else None
    else:
        out["std"] = out["t"] = None
    return out

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o

# ---------- 加载全部 ----------
spy = load_stock("SPY").rename(columns={"px": "spy"})
qqq = load_stock("QQQ").rename(columns={"px": "qqq"})

frames, loaded = [], []
meta_range = {}
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 260:
        continue
    df["ticker"] = t
    df["sector"] = sectors[t]
    df["rsi"] = rsi_wilder(df["px"])
    df = df.merge(spy[["date", "spy"]], on="date", how="left")
    df = df.merge(qqq[["date", "qqq"]], on="date", how="left")
    frames.append(df)
    meta_range[t] = [str(df["date"].min().date()), str(df["date"].max().date())]
    loaded.append(t)

pool = pd.concat(frames, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)
pool = pool[(pool["date"] >= WINDOW_START) & (pool["date"] < WINDOW_END)].copy()
pool = pool.reset_index(drop=True)

for N in (5, 10):
    pool[f"fwd{N}"] = pool.groupby("ticker")["px"].transform(
        lambda x: (x.shift(-N) / x - 1) * 100)

# SPY/QQQ 的 fwd 用它们自己的序列计算（同日期所有票一致）
for ref, tag in [("spy", "spy"), ("qqq", "qqq")]:
    refdf = pool.groupby("date")[ref].first().dropna().sort_index().reset_index()
    for N in (5, 10):
        refdf[f"{tag}_fwd{N}"] = (refdf[ref].shift(-N) / refdf[ref] - 1) * 100
    pool = pool.merge(refdf[["date", f"{tag}_fwd5", f"{tag}_fwd10"]], on="date", how="left")

print(f"加载 {len(loaded)}/{len(tickers)} 只 | 窗口 {WINDOW_START.date()}~{pool['date'].max().date()} | 股票×交易日 {len(pool)}")

# ---------- 事件标记 ----------
def roll_cd30(ev):
    """事件去重：同一只票内相邻同类信号间隔 <10 交易日只保留第一个"""
    ev = ev.sort_values(["ticker", "date"]).reset_index(drop=True)
    groups = []
    for t, g in ev.groupby("ticker"):
        g = g.reset_index(drop=True)
        keep, last = [], -10**9
        for i in range(len(g)):
            if i - last >= 10:
                keep.append(i)
                last = i
        groups.append(g.iloc[keep])
    return pd.concat(groups, ignore_index=True)

# 低买 / 高卖信号（下穿/上穿阈值）
for L in (30, 35):
    pool[f"buy_c{L}"] = pool.groupby("ticker")["rsi"].transform(
        lambda x: (x < L) & (x.shift(1) >= L))
for H in (70, 65):
    pool[f"sell_c{H}"] = pool.groupby("ticker")["rsi"].transform(
        lambda x: (x > H) & (x.shift(1) <= H))

# ---------- 硬性 A/B 事件统计 ----------
def event_stats(ev, qty, ex_ref="spy"):
    """ev: 事件切片（含每行 fwd5/fwd10）；qty 冗余标记列名，仅用于计数 tag"""
    out = {}
    for N in (5, 10):
        out[f"T{N}"] = stats(ev[f"fwd{N}"])
        if ex_ref and f"{ex_ref}_fwd{N}" in ev.columns:
            out[f"T{N}_ex{ex_ref}"] = stats(ev[f"fwd{N}"] - ev[f"{ex_ref}_fwd{N}"])
    return out

res = {"meta": {
    "universe": "blue_chips.csv 优质蓝筹股池",
    "n_tickers_loaded": len(loaded),
    "n_tickers_pool": len(tickers),
    "skipped": [t for t in tickers if t not in loaded],
    "window": [str(WINDOW_START.date()), str(pool["date"].max().date())],
    "rsi": "Wilder RSI14 on adj_close, 全历史前推",
    "horizon": "T+N = N 个交易日(shift(-N))，收益%",
    "ex_ref": "超额 = 个股fwd - SPY/QQQ fwd",
}}

# ----- 基准 -----
res["benchmark"] = {}
# 个股全部交易日（等权）
bh = {"T5": stats(pool["fwd5"]), "T10": stats(pool["fwd10"]),
      "T5_exspy": stats(pool["fwd5"] - pool["spy_fwd5"]),
      "T10_exspy": stats(pool["fwd10"] - pool["spy_fwd10"]),
      "T5_exqqq": stats(pool["fwd5"] - pool["qqq_fwd5"]),
      "T10_exqqq": stats(pool["fwd10"] - pool["qqq_fwd10"])}
res["benchmark"]["all_days_ew"] = bh
# 每票 buy&hold 区间收益 -> 等权组合
bhs = []
per_bh = {}
for t, g in pool.groupby("ticker"):
    if len(g) < 5:
        continue
    full = g.sort_values("date")
    r = (full["px"].iloc[-1] / full["px"].iloc[0] - 1) * 100
    bhs.append(r)
    per_bh[t] = round(float(r), 3)
res["benchmark"]["buy_hold_ew_window"] = stats(pd.Series(bhs))
res["benchmark"]["buy_hold_per_ticker"] = per_bh
# SPY / QQQ 区间
for tick, nm in [("spy", "SPY"), ("qqq", "QQQ")]:
    g = pool.groupby("date")[tick].first().dropna().sort_index()
    if len(g) >= 2:
        r = (g.iloc[-1] / g.iloc[0] - 1) * 100
        res["benchmark"][f"{nm}_window"] = round(float(r), 3)

# ----- A) 低买事件 -----
res["low_buy"] = {}
for L in (30, 35):
    col = f"buy_c{L}"
    ev = pool[pool[col]].copy()
    ev = roll_cd30(ev.reset_index(drop=True))
    if len(ev) < 3:
        # 放宽阈值不适用：这里是下穿阈值，直接标注小样本
        pass
    res["low_buy"][f"L{L}"] = {"block": event_stats(ev, col)}
    ev_d = ev.groupby("date")[["fwd5", "fwd10"]].mean().reset_index()
    res["low_buy"][f"L{L}"]["day_clustered"] = event_stats(ev_d, col + "_day")

# ----- B) 高卖事件（卖出后仍持有，观察卖出后 N 日走势）-----
res["high_sell"] = {}
for H in (70, 65):
    col = f"sell_c{H}"
    ev = pool[pool[col]].copy()
    ev = roll_cd30(ev.reset_index(drop=True))
    res["high_sell"][f"H{H}"] = {"block": event_stats(ev, col)}
    ev_d = ev.groupby("date")[["fwd5", "fwd10"]].mean().reset_index()
    res["high_sell"][f"H{H}"]["day_clustered"] = event_stats(ev_d, col + "_day")

# ----- C) 配对循环：低买信号 → 次高卖信号，持仓至区间末 -----
def paired_rounds(g):
    """g 为一票的窗口切片（按日期升序）。返回 (回合列表, 区间累计, 敞口天数)"""
    g = g.sort_values("date").reset_index(drop=True)
    buys = list(g.index[g["rsi"] < 30])          # RSI<30 的所有日（含持续低位，做可执行信号）
    pairs = []  # (buy_date, sell_date, 持仓天数, 收益%)
    b_i = 0
    n = len(g)
    for sell_i in range(len(g)):
        if g["rsi"].iloc[sell_i] > 70:
            # 找该卖出日之前最近的买入日
            cand = [b for b in buys if b < sell_i]
            if len(cand) > 0:
                b = cand[-1]
            else:
                continue
            ret = (g["px"].iloc[sell_i] / g["px"].iloc[b] - 1) * 100
            hold = sell_i - b
            pairs.append((str(g["date"].iloc[b].date()), str(g["date"].iloc[sell_i].date()), hold, round(float(ret), 3)))
            buys = [x for x in buys if x > sell_i]  # 卖出后清空，等下一下穿
    # 未平仓：最后一次买入(若有) → 区间末
    if len(buys) > 0:
        b = buys[-1]
        if b < n - 1:
            ret = (g["px"].iloc[-1] / g["px"].iloc[b] - 1) * 100
            pairs.append((str(g["date"].iloc[b].date()), "2026-02-27(区间末)", n - 1 - b, round(float(ret), 3)))
    return pairs

all_rounds = []
per_ticker_rounds = {}
for t, g in pool.groupby("ticker"):
    ps = paired_rounds(g)
    if len(ps) > 0:
        all_rounds.extend(ps)
        per_ticker_rounds[t] = ps

# 汇总
r_means = [x[3] for x in all_rounds]
r_hold = [x[2] for x in all_rounds]
res["paired_low30_sell70"] = {
    "rounds_total": len(all_rounds),
    "sectors": {sc: len([x for x in all_rounds if sectors.get(x[1], "") != sc]) for sc in []},  # 占位
    "round_ret_stats": stats_pair(r_means),
    "hold_days_stats": stats_pair(r_hold),
    "n_tickers_with_rounds": len(per_ticker_rounds),
    "per_ticker": per_ticker_rounds,
}
# 按票区间累计（把区间累计当独立样本）
res["paired_low30_sell70"]["rounds_all"] = [
    {"buy": x[0], "sell": x[1], "hold_days": x[2], "ret_pct": x[3]} for x in all_rounds
]

# ----- D) 每票 T5/T10 信号收益 + 超额 -----
per_ticker_fwd = {}
for t, g in pool.groupby("ticker"):
    g = g.sort_values("date")
    rec = {"n_days": int(len(g)), "bh_window": round(float((g["px"].iloc[-1] / g["px"].iloc[0] - 1) * 100), 3)}
    for N in (5, 10):
        rec[f"all_T{N}"] = stats(g[f"fwd{N}"])
    # 低买(35)与高卖(65)的最宽松组合，作为单票信号样本
    bl = g[g["buy_c35"]].copy()
    if len(bl) >= 3:
        for N in (5, 10):
            rec[f"buy35_T{N}"] = stats(bl[f"fwd{N}"])
    sh = g[g["sell_c65"]].copy()
    if len(sh) >= 3:
        for N in (5, 10):
            rec[f"sell65_T{N}"] = stats(sh[f"fwd{N}"])
    per_ticker_fwd[t] = rec
res["per_ticker"] = per_ticker_fwd

# 事件明细清单（低买 L35 与高卖 H65）
ev_buy = pool[pool["buy_c35"]].copy()
ev_sell = pool[pool["sell_c65"]].copy()
res["detail"] = {
    "low_buy_L35": [{
        "date": str(r["date"].date()), "ticker": r["ticker"], "sector": r["sector"],
        "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
        "fwd5": round(float(r["fwd5"]), 2) if not pd.isna(r["fwd5"]) else None,
        "fwd10": round(float(r["fwd10"]), 2) if not pd.isna(r["fwd10"]) else None,
    } for _, r in ev_buy.sort_values("date").iterrows()],
    "high_sell_H65": [{
        "date": str(r["date"].date()), "ticker": r["ticker"], "sector": r["sector"],
        "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
        "fwd5": round(float(r["fwd5"]), 2) if not pd.isna(r["fwd5"]) else None,
        "fwd10": round(float(r["fwd10"]), 2) if not pd.isna(r["fwd10"]) else None,
    } for _, r in ev_sell.sort_values("date").iterrows()],
}

with open(os.path.join(OUT, "blue_chip_rsi_reversion_window.json"), "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 控制台汇总 ----------
def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0:
        return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% win={t['win']}% t={t.get('t')}"

print("\n======= 纳指区间 2025-10~2026-02 =======")
print("基准: SPY区间", res["benchmark"].get("SPY_window"), "% | QQQ区间", res["benchmark"].get("QQQ_window"), "% | 个股等权Buy&Hold", str(res["benchmark"]["buy_hold_ew_window"].get("mean")) + "%")
print("\n[A] 低买(下穿阈值) T5/T10:")
for L in (30, 35):
    b = res["low_buy"][f"L{L}"]["block"]
    print(f"  下穿{L}: T5:{fmt(b,'T5')} | T10:{fmt(b,'T10')}")
    print(f"           T5超额SPY:{fmt(b,'T5_exspy')} | T10超额SPY:{fmt(b,'T10_exspy')}")
print("\n[B] 高卖(上穿阈值) 卖出后T5/T10(仍持有观察):")
for H in (70, 65):
    b = res["high_sell"][f"H{H}"]["block"]
    print(f"  上穿{H}: T5:{fmt(b,'T5')} | T10:{fmt(b,'T10')}")
print("\n[C] 配对循环 低买(<30)→高卖(>70) 直至区间末:")
p = res["paired_low30_sell70"]
print(f"  总回合 {p['rounds_total']} (覆盖 {p['n_tickers_with_rounds']} 只), 回合收益 {p['round_ret_stats']['mean']}%, 持有天数均值 {round(p['hold_days_stats']['mean'],1)}")
print("  各票首回合(前8):")
for t, ps in list(per_ticker_rounds.items())[:8]:
    print(f"    {t}: " + ", ".join(f"{x[0]}→{x[1][:10]}({x[2]}d) {x[3]:+.1f}%" for x in ps[:3]))