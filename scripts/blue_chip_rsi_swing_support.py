# -*- coding: utf-8 -*-
"""
优质蓝筹股 RSI 摆动低点(swing low)聚集支撑位买入事件研究 —— T+5/T+10/T+20
（用户 08-27 纠正：支撑位不能用"分位数"，要用"摆动低点"本义）

口径（可复现规则）：
  swing low     : 某日 RSI 严格低于前后各 K 日的 RSI（K=5）
  有效支撑      : 过去 WIN=120 交易日内的、最近 M=3 个摆动低点，其 RSI 极差 ≤ CLUSTER_TOL（3 RSI 点）
                  → 这些"谷底"反复测试同一水平、都没跌破，形成支撑
  支撑位 S      : 这 M 个摆动低点的最低 RSI（真正的"跌不下去"的底线）
  买入触发      : RSI 从上方首日进入 [S-BUF, S+BUF]（触及/轻微下破，缓冲 BUF=2），当日收盘买入
  无前视        : 只用 ≤ t-K 已确认的 swing low；买入用当日收盘，收益 shift(-N)
  去重          : 同票 20 交易日 cooldown
T+N = N 个交易日。统计单位百分数×100。
输出 results/blue_chip_rsi_swing_support.json。
"""
import pandas as pd
import numpy as np
import json, os, glob, csv, bisect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

# 参数
K = 5            # swing low 半宽（前后各 K 日）
WIN = 120        # 支撑回顾窗口（约半年）
M = 3            # 最近 M 个摆动低点聚集
CLUSTER_TOL = 3.0  # 聚集阈值：RSI 极差 <= 3
BUF = 2.0        # 买入缓冲 ±2 RSI 点
COOL = 20        # 同票买入去重

tickers = []
sectors = {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t)
        sectors[t] = row["sector"].strip()

def load_stock(name):
    d = os.path.join(DATA, name.lower())
    if not os.path.isdir(d):
        return None
    cands = [p for p in glob.glob(os.path.join(d, "*.csv"))
             if not os.path.basename(p).startswith("BATS_") and "1D" in os.path.basename(p)]
    if not cands:
        return None
    df = pd.read_csv(sorted(cands)[0], parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    df = df.dropna(subset=["px"]).sort_values("date").reset_index(drop=True)
    return df

def rsi_wilder(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/period, adjust=False).mean()
    al = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = ag / al
    return 100 - 100/(1 + rs)

def swing_low_mask(arr, k):
    """某日严格低于前后各 k 日（含边界对齐）"""
    n = len(arr)
    mask = np.zeros(n, dtype=bool)
    for i in range(k, n - k):
        if arr[i] < arr[i-k:i].min() and arr[i] < arr[i+1:i+k+1].min():
            mask[i] = True
    return mask

spy = load_stock("SPY").rename(columns={"px": "spy"})

frames = []
loaded = []
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < WIN + K + 40:
        continue
    df["ticker"] = t
    df["sector"] = sectors[t]
    df["rsi"] = rsi_wilder(df["px"])
    for N in (5, 10, 20):
        df[f"fwd{N}"] = (df["px"].shift(-N) / df["px"] - 1) * 100
    df = df.merge(spy[["date", "spy"]], on="date", how="left")
    for N in (5, 10, 20):
        df[f"spy_fwd{N}"] = (df["spy"].shift(-N) / df["spy"] - 1) * 100
    frames.append(df)
    loaded.append(t)

pool = pd.concat(frames, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)

def stage_of(d):
    if d < pd.Timestamp("2020-02-20"):
        return "A_pre"
    if d <= pd.Timestamp("2022-12-31"):
        return "B_post"
    return "C_bull"
pool["stage"] = pool["date"].map(stage_of)

# ---------- 逐票检测 swing low 聚集支撑买入 ----------
buy_rows = []
diag = []  # 诊断：支撑位 S 的分布、聚集到的 swing low 数
for t, g in pool.groupby("ticker"):
    g = g.sort_values("date").reset_index(drop=True)
    rsi_arr = g["rsi"].values
    n = len(g)
    sl = swing_low_mask(rsi_arr, K)
    sl_pos = np.where(sl)[0]
    sl_pos = sl_pos[sl_pos < n - K]  # 只用已充分确认的
    last = -10**9
    for tt in range(WIN, n):
        lo = tt - WIN + 1
        hi = tt - K  # 只用 ≤ tt-K 已确认的 swing low
        if hi < lo:
            continue
        idxL = bisect.bisect_left(sl_pos, lo)
        idxR = bisect.bisect_right(sl_pos, hi)
        if idxR - idxL < M:
            continue
        lastM = sl_pos[idxR - M: idxR]
        vals = rsi_arr[lastM]
        if vals.max() - vals.min() > CLUSTER_TOL:
            continue  # 不聚集，不构成支撑
        S = vals.min()  # 支撑 = 最低的摆动低点
        rsi_t = rsi_arr[tt]
        rsi_prev = rsi_arr[tt - 1]
        # 买入：首日从上方进入 [S-BUF, S+BUF]
        if (S - BUF) <= rsi_t <= (S + BUF) and rsi_prev > (S + BUF):
            if tt - last < COOL:
                continue
            last = tt
            row = g.iloc[tt]
            buy_rows.append({
                "date": row["date"], "ticker": t, "sector": row["sector"],
                "rsi": float(rsi_t), "px": float(row["px"]),
                "support": float(S), "swing_lows": [float(x) for x in vals],
                "stage": stage_of(row["date"]),
                "fwd5": row["fwd5"], "fwd10": row["fwd10"], "fwd20": row["fwd20"],
                "spy_fwd5": row["spy_fwd5"], "spy_fwd10": row["spy_fwd10"], "spy_fwd20": row["spy_fwd20"],
            })

ev = pd.DataFrame(buy_rows)

def stats(s):
    s = pd.Series(s).dropna()
    if len(s) == 0:
        return {"n": 0}
    return {
        "n": int(len(s)),
        "mean": round(float(s.mean()), 3),
        "median": round(float(s.median()), 3),
        "win": round(float((s > 0).mean()) * 100, 1),
        "p25": round(float(s.quantile(0.25)), 3),
        "p75": round(float(s.quantile(0.75)), 3),
        "std": round(float(s.std(ddof=1)), 3) if len(s) > 1 else None,
        "t": round(float(s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))), 2) if len(s) > 1 and s.std(ddof=1) > 0 else None,
    }

def block(df):
    out = {}
    for N in (5, 10, 20):
        out[f"T{N}"] = stats(df[f"fwd{N}"])
        out[f"T{N}_ex_spy"] = stats(df[f"fwd{N}"] - df[f"spy_fwd{N}"])
    return out

def day_cluster(df):
    agg = []
    for N in (5, 10, 20):
        agg.append(df.groupby("date")[f"fwd{N}"].mean().rename(f"fwd{N}"))
        agg.append(df.groupby("date")[f"spy_fwd{N}"].mean().rename(f"spy_fwd{N}"))
    return pd.concat(agg, axis=1).reset_index()

def support_bucket(sv):
    if sv < 35: return "<35"
    if sv < 40: return "35-40"
    if sv < 45: return "40-45"
    if sv < 50: return "45-50"
    return ">=50"

ev["spt_bucket"] = ev["support"].map(support_bucket)

res = {
    "meta": {
        "universe": "blue_chips.csv",
        "n_tickers": len(loaded),
        "skipped": [t for t in tickers if t not in loaded],
        "params": {"k": K, "window": WIN, "min_swing_lows": M, "cluster_tol": CLUSTER_TOL, "buffer": BUF, "cooldown": COOL},
        "event": "RSI摆动低点(前后5日最低)最近3个聚集(极差≤3)→支撑=最低谷; RSI首日回落进[支撑±2]买入",
        "horizon": "T+N = N 个交易日",
    },
    "n_events": {
        "total_days": int(pool["date"].nunique()),
        "support_buy": int(len(ev)),
        "day_clustered": int(ev["date"].nunique()) if len(ev) else 0,
    },
    "baseline_all_days": block(pool),
    "events_all": {
        "block": block(ev),
        "day_clustered": block(day_cluster(ev)),
        "by_sector": {sc: block(ev[ev["sector"] == sc]) for sc in ev["sector"].unique()} if len(ev) else {},
        "by_stage": {st: block(ev[ev["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]} if len(ev) else {},
        "bull_by_year": {str(y): block(ev[(ev["stage"] == "C_bull") & (ev["date"].dt.year == y)])
                         for y in sorted(ev[ev["stage"] == "C_bull"]["date"].dt.year.unique())} if len(ev) else {},
    },
    "support_buckets": {bk: block(ev[ev["spt_bucket"] == bk]) for bk in ["<35", "35-40", "40-45", "45-50", ">=50"]} if len(ev) else {},
    "per_ticker": {t: {"sector": sectors[t], "n": int(len(gg)), **block(gg)}
                   for t, gg in ev.groupby("ticker")} if len(ev) else {},
}

if len(ev):
    res["n_events"]["support_level_dist"] = {
        "mean": round(float(ev["support"].mean()), 1),
        "median": round(float(ev["support"].median()), 1),
        "p10": round(float(ev["support"].quantile(0.10)), 1),
        "p90": round(float(ev["support"].quantile(0.90)), 1),
    }
    res["n_events"]["buy_rsi_dist"] = {
        "mean": round(float(ev["rsi"].mean()), 1),
        "median": round(float(ev["rsi"].median()), 1),
    }

ev_list = []
for _, r in ev.sort_values("date", ascending=False).iterrows():
    ev_list.append({
        "date": str(r["date"].date()), "ticker": r["ticker"], "sector": r["sector"],
        "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
        "support": round(float(r["support"]), 1), "stage": r["stage"],
        "swing_lows": [round(x, 1) for x in r["swing_lows"]],
        "fwd5": round(float(r["fwd5"]), 2) if not pd.isna(r["fwd5"]) else None,
        "fwd10": round(float(r["fwd10"]), 2) if not pd.isna(r["fwd10"]) else None,
        "fwd20": round(float(r["fwd20"]), 2) if not pd.isna(r["fwd20"]) else None,
    })
res["events"] = ev_list

last_date = pool["date"].max()
res["current"] = {"as_of": str(last_date.date())}

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o

with open(os.path.join(OUT, "blue_chip_rsi_swing_support.json"), "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 汇总打印 ----------
def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0: return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% win={t['win']}% t={t.get('t')}"

b = res["baseline_all_days"]
ea = res["events_all"]["block"]; ea_d = res["events_all"]["day_clustered"]
print(f"加载 {len(loaded)}/{len(tickers)} 只 | 跳过 {res['meta']['skipped']}")
print(f"swing low 聚集支撑买入事件: {len(ev)} (日历日 {res['n_events'].get('day_clustered')})")
if len(ev):
    sd = res["n_events"]["support_level_dist"]; bd = res["n_events"]["buy_rsi_dist"]
    print(f"支撑位分布: 均值 {sd['mean']} 中位 {sd['median']} p10-p90 {sd['p10']}-{sd['p90']}")
    print(f"买入RSI分布: 均值 {bd['mean']} 中位 {bd['median']}")
print(f"[全历史基率] T5:{fmt(b)} | T10:{fmt(b,'T10')} | T20:{fmt(b,'T20')}")
print(f"[支撑买入 全部] T5:{fmt(ea)} | T10:{fmt(ea,'T10')} | T20:{fmt(ea,'T20')}")
print(f"[支撑买入 聚类] T5:{fmt(ea_d)} | T10:{fmt(ea_d,'T10')} | T20:{fmt(ea_d,'T20')}")
print(f"[超额exSPY] T5:{fmt(ea,'T5_ex_spy')} | T10:{fmt(ea,'T10_ex_spy')} | T20:{fmt(ea,'T20_ex_spy')}")
print("-- 支撑位高度分档 --")
for bk in ["<35", "35-40", "40-45", "45-50", ">=50"]:
    sb = res["support_buckets"].get(bk, {})
    print(f"[支撑 {bk}] n={sb.get('T5',{}).get('n','—')} | T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}")
for st, lab in [("A_pre", "疫情前"), ("B_post", "疫情及股灾后"), ("C_bull", "本轮牛市")]:
    sb = res["events_all"]["by_stage"].get(st, {})
    print(f"[{lab}] T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}")
print(f"written: {os.path.join(OUT, 'blue_chip_rsi_swing_support.json')}")