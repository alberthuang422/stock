# -*- coding: utf-8 -*-
"""
优质蓝筹股池 RSI 动态支撑位买入事件研究 —— T+5 / T+10 / T+20
（用户 08-27 需求：RSI 不进 30，改做"RSI 支撑位"附近买入；支撑位多次触碰确认、≤55、留缓冲、至少1个月未跌破）

口径（可复现规则）：
  支撑位 L(t) = 过去 120 交易日（约半年）RSI 的 15% 分位数，上限截断 55（不能太高）
  多次触碰确认  : 过去 120 日内 RSI 下探至 [.., L+2] 的"下探段数" ≥ 2
  未跌破≥1个月  : 近 20 交易日 RSI 最低 ≥ L - 2（支撑守住，含缓冲）
  买入触发      : RSI 从上方首日进入 [L-2, L+2]（触及/轻微下破，缓冲 ±2），当日收盘买入
  去重          : 同票 20 交易日 cooldown（避免同一段下探重复计）
T+N = N 个交易日（shift(-N)）。统计单位百分数×100。
对照：全历史基率、SPY 同期超额。分维度：板块/阶段/牛市逐年/每票。
输出 results/blue_chip_rsi_support.json，只打印汇总。
"""
import pandas as pd
import numpy as np
import json, os, glob, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

# 参数
LOOKBACK = 120   # 找支撑的回顾窗口（约半年）
QUANT = 0.15     # 支撑位 = 过去120日 RSI 分位数
BUF = 2.0        # 缓冲 ±2 RSI 点
MAX_SUP = 55.0   # 支撑位高度上限
HOLD = 20        # 未跌破门槛（≈1个月交易日）
MIN_SEGS = 2     # 多次触碰最少段数
COOL = 20        # 同票买入去重 cooldown

tickers = []
sectors = {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t)
        sectors[t] = row["sector"].strip()

SECTOR_CN = {
    "Technology": "Technology",  # 保持英文 key（对齐 by_sector），展示层再译
    "Financials": "Financials", "Industrials": "Industrials",
    "Healthcare": "Healthcare", "Consumer": "Consumer",
    "Materials_Utilities_Other": "Materials_Utilities_Other",
}

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

spy = load_stock("SPY").rename(columns={"px": "spy"})

frames = []
loaded = []
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < LOOKBACK + 40:
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

# ---------- 逐票检测支撑位买入事件 ----------
buy_rows = []
for t, g in pool.groupby("ticker"):
    g = g.sort_values("date").reset_index(drop=True)
    rsi = g["rsi"]
    L = rsi.rolling(LOOKBACK, min_periods=LOOKBACK).quantile(QUANT).clip(upper=MAX_SUP)
    below = rsi <= (L + BUF)
    seg_start = below & (~below.shift(1, fill_value=False))
    segs = seg_start.rolling(LOOKBACK, min_periods=LOOKBACK).sum()  # 过去120日下探段数
    rollmin20 = rsi.rolling(HOLD, min_periods=HOLD).min()
    not_broken = rollmin20 >= (L - BUF)
    in_band = (rsi >= L - BUF) & (rsi <= L + BUF)
    prev_above = rsi.shift(1) > (L + BUF)
    first_in = in_band & prev_above.fillna(False)
    buy = (segs >= MIN_SEGS) & not_broken & first_in & L.notna()
    # cooldown 去重
    last = -10**9
    for i in np.where(buy.values)[0]:
        if i - last >= COOL:
            row = g.iloc[i]
            buy_rows.append({
                "date": row["date"], "ticker": t, "sector": row["sector"],
                "rsi": float(row["rsi"]), "px": float(row["px"]),
                "support": float(L.iloc[i]),
                "stage": stage_of(row["date"]),
                "fwd5": row["fwd5"], "fwd10": row["fwd10"], "fwd20": row["fwd20"],
                "spy_fwd5": row["spy_fwd5"], "spy_fwd10": row["spy_fwd10"], "spy_fwd20": row["spy_fwd20"],
            })

ev = pd.DataFrame(buy_rows)

# ---------- 统计函数 ----------
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

def by_sector(df):
    return {sc: block(df[df["sector"] == sc]) for sc in sectors_in_order}

sectors_in_order = []
for sc in ["Technology", "Financials", "Industrials", "Healthcare", "Consumer", "Materials_Utilities_Other"]:
    if (ev["sector"] == sc).any() or True:
        sectors_in_order.append(sc)

def by_stage(df):
    return {st: block(df[df["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]}

def by_year(df, stage=None):
    d = df if stage is None else df[df["stage"] == stage]
    return {str(y): block(d[d["date"].dt.year == y]) for y in sorted(d["date"].dt.year.unique())}

def per_ticker(df):
    out = {}
    for t, gg in df.groupby("ticker"):
        out[t] = {"sector": sectors[t], "n": int(len(gg)), **block(gg)}
    return out

res = {
    "meta": {
        "universe": "blue_chips.csv 优质蓝筹股池",
        "n_tickers": len(loaded),
        "skipped": [t for t in tickers if t not in loaded],
        "params": {
            "lookback": LOOKBACK, "quantile": QUANT, "max_support_rsl": MAX_SUP,
            "buffer": BUF, "hold_days": HOLD, "min_touch_segments": MIN_SEGS, "cooldown": COOL,
        },
        "event": "RSI 动态支撑位(120日15%分位,≤55,缓冲±2,≥2次触碰,20日未跌破) 首日进入[L-2,L+2]买入",
        "horizon": "T+N = N 个交易日",
    },
    "n_events": {
        "total_days": int(pool["date"].nunique()),
        "support_buy": int(len(ev)),
        "day_clustered": int(ev["date"].nunique()),
        "per_ticker_dist": None,
    },
    "baseline_all_days": block(pool),
    "events_all": {
        "block": block(ev),
        "day_clustered": block(day_cluster(ev)),
        "by_sector": by_sector(ev),
        "by_stage": by_stage(ev),
        "bull_by_year": by_year(ev, "C_bull"),
    },
    "per_ticker": per_ticker(ev),
}

# 买入时 RSI 与支撑位分布诊断
res["n_events"]["support_level_dist"] = {
    "mean": round(float(ev["support"].mean()), 1) if len(ev) else None,
    "median": round(float(ev["support"].median()), 1) if len(ev) else None,
    "p10": round(float(ev["support"].quantile(0.10)), 1) if len(ev) else None,
    "p90": round(float(ev["support"].quantile(0.90)), 1) if len(ev) else None,
}
res["n_events"]["buy_rsi_dist"] = {
    "mean": round(float(ev["rsi"].mean()), 1) if len(ev) else None,
    "median": round(float(ev["rsi"].median()), 1) if len(ev) else None,
}

# ---------- 支撑位高度分档（关键下钻：edge 是否集中在低位支撑）----------
def support_bucket(sv):
    if sv < 35: return "<35"
    if sv < 40: return "35-40"
    if sv < 45: return "40-45"
    if sv < 50: return "45-50"
    return ">=50"
ev["spt_bucket"] = ev["support"].map(support_bucket)
res["support_buckets"] = {
    bk: block(ev[ev["spt_bucket"] == bk])
    for bk in ["<35", "35-40", "40-45", "45-50", ">=50"]
}

ev_list = []
for _, r in ev.sort_values("date", ascending=False).iterrows():
    ev_list.append({
        "date": str(r["date"].date()), "ticker": r["ticker"], "sector": r["sector"],
        "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
        "support": round(float(r["support"]), 1), "stage": r["stage"],
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

with open(os.path.join(OUT, "blue_chip_rsi_support.json"), "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 汇总打印 ----------
def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0: return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% win={t['win']}% t={t.get('t')}"

b = res["baseline_all_days"]
ea = res["events_all"]["block"]; ea_d = res["events_all"]["day_clustered"]
print(f"加载 {len(loaded)}/{len(tickers)} 只 | 跳过 {res['meta']['skipped']}")
print(f"支撑位买入事件: {len(ev)} (日历日 {ev['date'].nunique()})")
print(f"支撑位分布: 均值 {res['n_events']['support_level_dist']['mean']} 中位 {res['n_events']['support_level_dist']['median']} p10-p90 {res['n_events']['support_level_dist']['p10']}-{res['n_events']['support_level_dist']['p90']}")
print(f"买入RSI分布: 均值 {res['n_events']['buy_rsi_dist']['mean']} 中位 {res['n_events']['buy_rsi_dist']['median']}")
print(f"[全历史基率] T5:{fmt(b)} | T10:{fmt(b,'T10')} | T20:{fmt(b,'T20')}")
print(f"[支撑买入 全部] T5:{fmt(ea)} | T10:{fmt(ea,'T10')} | T20:{fmt(ea,'T20')}")
print(f"[支撑买入 日历日聚类] T5:{fmt(ea_d)} | T10:{fmt(ea_d,'T10')} | T20:{fmt(ea_d,'T20')}")
print(f"[超额exSPY 全部] T5:{fmt(ea,'T5_ex_spy')} | T10:{fmt(ea,'T10_ex_spy')} | T20:{fmt(ea,'T20_ex_spy')}")
print("-- 支撑位高度分档 --")
for bk in ["<35", "35-40", "40-45", "45-50", ">=50"]:
    sb = res["support_buckets"].get(bk, {})
    print(f"[支撑 {bk}] 事件n={sb.get('T5',{}).get('n','—')} | T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}")
for st, lab in [("A_pre", "疫情前"), ("B_post", "疫情及股灾后"), ("C_bull", "本轮牛市")]:
    sb = res["events_all"]["by_stage"][st]
    print(f"[{lab}] T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}")
for sc in sectors_in_order:
    sb = res["events_all"]["by_sector"].get(sc, {})
    if not sb.get("T5", {}).get("n"): continue
    print(f"[{sc}] T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}")
print(f"written: {os.path.join(OUT, 'blue_chip_rsi_support.json')}")