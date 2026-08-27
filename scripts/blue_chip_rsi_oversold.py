# -*- coding: utf-8 -*-
"""
优质蓝筹股池 RSI14 超卖(下穿30)买入事件研究 —— T+5 / T+10 / T+20 表现
事件定义：Wilder RSI14(adj_close) 自上下穿 30 首日（前一日>=30，当日<30），当日收盘为基准买入。
口径：
  1) 主口径 = 下穿30首日（含密集重复）
  2) 稳健性 = cooldown=10 交易日去重（消除同一只票连续低位重复计数）
  3) 显著性修正 = 按日历日聚合（同日多票同时下穿属市场系统性下跌，独立性被高估）
对照：全历史所有交易日基率（73 只每只每天）；RSI>=30 日对照；SPY 同期 fwd 超额。
分维：板块（blue_chips.csv sector）/ 阶段(疫情前/灾后/本轮牛市) / 逐年 / 每只票。
T+N 口径：交易日数（shift(-N)，跳过周末假日），非自然日。
统计单位：一律百分数（×100）。输出 results/blue_chip_rsi_oversold.json，只打印汇总。
"""
import pandas as pd
import numpy as np
import json, os, glob, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

# ---------- 读取股票池 ----------
tickers = []
sectors = {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t)
        sectors[t] = row["sector"].strip()

SECTOR_CN = {
    "Technology": "科技",
    "Financials": "金融",
    "Industrials": "工业",
    "Healthcare": "医疗",
    "Consumer": "消费",
    "Materials_Utilities_Other": "材料/公用事业/其他",
}

# ---------- 加载函数 ----------
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

# ---------- 加载 SPY（对照）----------
spy = load_stock("SPY").rename(columns={"px": "spy"})

frames = []
meta_range = {}
loaded = []
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 260:   # 至少一年数据才算有效
        continue
    df["ticker"] = t
    df["sector"] = sectors[t]
    df["rsi"] = rsi_wilder(df["px"])
    for N in (5, 10, 20):
        df[f"fwd{N}"] = (df["px"].shift(-N) / df["px"] - 1) * 100
    df = df.merge(spy[["date", "spy"]], on="date", how="left")
    for N in (5, 10, 20):
        df[f"spy_fwd{N}"] = (df["spy"].shift(-N) / df["spy"] - 1) * 100
    df["cross30"] = (df["rsi"] < 30) & (df["rsi"].shift(1) >= 30)
    frames.append(df)
    meta_range[t] = [str(df["date"].min().date()), str(df["date"].max().date())]
    loaded.append(t)

pool = pd.concat(frames, ignore_index=True)
pool = pool.sort_values(["date", "ticker"]).reset_index(drop=True)

def stage_of(d):
    if d < pd.Timestamp("2020-02-20"):
        return "A_pre"
    if d <= pd.Timestamp("2022-12-31"):
        return "B_post"
    return "C_bull"

pool["stage"] = pool["date"].map(stage_of)

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

# ---------- 事件集 ----------
ev = pool[pool["cross30"]].copy()

# cooldown=10 每只票内部去重（连续重复下穿）
def apply_cd10(g):
    g = g.sort_values("date").reset_index(drop=True)
    keep = []
    last = -10**9
    for i in range(len(g)):
        pos = g.index[i]  # 在 pool 中的绝对行号
        # 需要按每票的时间顺序用绝对索引判定；这里改用累计顺序
        if i - last >= 10:
            keep.append(i)
            last = i
    return g.iloc[keep]

cd_rows = []
for t, g in ev.groupby("ticker"):
    g = g.sort_values("date").reset_index(drop=True)
    keep, last = [], -10**9
    for i in range(len(g)):
        if i - last >= 10:
            keep.append(i)
            last = i
    cd_rows.append(g.iloc[keep])
ev_cd10 = pd.concat(cd_rows, ignore_index=True)

# ---------- 日历日聚类（显著性修正）----------
def day_cluster(df):
    """按日历日聚合：同日多票事件取平均 fwd，得到一条'日事件'序列"""
    agg = []
    for N in (5, 10, 20):
        g = df.groupby("date")[f"fwd{N}"].mean().rename(f"fwd{N}")
        agg.append(g)
        gs = df.groupby("date")[f"spy_fwd{N}"].mean().rename(f"spy_fwd{N}")
        agg.append(gs)
    out = pd.concat(agg, axis=1).reset_index()
    return out

# ---------- 结果组装 ----------
def by_sector(df):
    return {sc: block(df[df["sector"] == sc]) for sc in SECTOR_CN}

def by_stage(df):
    return {st: block(df[df["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]}

def by_year(df, stage=None):
    d = df if stage is None else df[df["stage"] == stage]
    return {str(y): block(d[d["date"].dt.year == y]) for y in sorted(d["date"].dt.year.unique())}

def per_ticker(df):
    out = {}
    for t, g in df.groupby("ticker"):
        out[t] = {"sector": sectors[t], "n": int(len(g)), **block(g)}
    return out

# 每只票 RSI<30 事件的样本量分布（含从未超卖的票）
ev_count = ev.groupby("ticker").size().to_dict()
n_events_by_ticker = {t: int(ev_count.get(t, 0)) for t in tickers}

res = {
    "meta": {
        "universe": "blue_chips.csv 优质蓝筹股池",
        "n_tickers_loaded": len(loaded),
        "n_tickers_pool": len(tickers),
        "skipped": [t for t in tickers if t not in loaded],
        "data_range": meta_range,
        "rsi": "Wilder RSI14 on adj_close",
        "event": "RSI 下穿 30 首日（前一日>=30，当日<30），当日收盘买入",
        "horizon": "T+N = N 个交易日（shift(-N)）",
        "stages": {
            "A_pre": "疫情前：~2020-02-19",
            "B_post": "疫情及股灾后：2020-02-20~2022-12-31",
            "C_bull": "本轮牛市：2023-01-01~",
        },
    },
    "n_events": {
        "total_days": int(pool["date"].nunique()),
        "cross30_all": int(len(ev)),
        "cross30_cd10": int(len(ev_cd10)),
        "day_clustered": int(ev["date"].nunique()),
    },
    "baseline_all_days": block(pool),
    "baseline_rsi_lt30": block(pool[pool["rsi"] < 30]),          # 所有 RSI<30 日（含持续在低位）
    "baseline_rsi_ge30": block(pool[pool["rsi"] >= 30]),
    "events_all": {
        "block": block(ev),
        "day_clustered": block(day_cluster(ev)),
        "by_sector": by_sector(ev),
        "by_stage": by_stage(ev),
        "by_year": by_year(ev),
        "bull_by_year": by_year(ev, "C_bull"),
    },
    "events_cd10": {
        "block": block(ev_cd10),
        "day_clustered": block(day_cluster(ev_cd10)),
        "by_sector": by_sector(ev_cd10),
        "by_stage": by_stage(ev_cd10),
    },
    "per_ticker": per_ticker(ev_cd10),
    "n_events_by_ticker": n_events_by_ticker,
}

# 事件明细（瘦身）
ev_list = []
for _, r in ev.sort_values("date", ascending=False).iterrows():
    ev_list.append({
        "date": str(r["date"].date()), "ticker": r["ticker"], "sector": r["sector"],
        "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
        "stage": r["stage"],
        "fwd5": round(float(r["fwd5"]), 2) if not pd.isna(r["fwd5"]) else None,
        "fwd10": round(float(r["fwd10"]), 2) if not pd.isna(r["fwd10"]) else None,
        "fwd20": round(float(r["fwd20"]), 2) if not pd.isna(r["fwd20"]) else None,
    })
res["events"] = ev_list

# 当前状态：73 只里当前哪些 RSI<30 / 最近下穿30
cur = []
last_date = pool["date"].max()
recent = pool[pool["date"] == last_date]
recent_low = recent[recent["rsi"] < 30]
for _, r in recent_low.iterrows():
    cur.append({"ticker": r["ticker"], "rsi": round(float(r["rsi"]), 1), "as_of": str(r["date"].date())})
res["current"] = {"as_of": str(last_date.date()), "rsi_below_30": cur}

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o

with open(os.path.join(OUT, "blue_chip_rsi_oversold.json"), "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 汇总打印 ----------
def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0: return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% win={t['win']}% t={t.get('t')}"

b = res["baseline_all_days"]
ea = res["events_all"]["block"]; ea_d = res["events_all"]["day_clustered"]
ec = res["events_cd10"]["block"]
print(f"加载 {len(loaded)}/{len(tickers)} 只 | 跳过 {res['meta']['skipped']}")
print(f"交易日总数 {res['n_events']['total_days']} | 下穿30事件 {len(ev)} (cd10:{len(ev_cd10)}, 日历日:{ev['date'].nunique()})")
print(f"[全历史基率] T5:{fmt(b,'T5')} | T10:{fmt(b,'T10')} | T20:{fmt(b,'T20')}")
print(f"[RSI<30 所有日] T5:{fmt(res['baseline_rsi_lt30'])} | T10:{fmt(res['baseline_rsi_lt30'],'T10')} | T20:{fmt(res['baseline_rsi_lt30'],'T20')}")
print(f"[RSI>=30 对照] T5:{fmt(res['baseline_rsi_ge30'])} | T10:{fmt(res['baseline_rsi_ge30'],'T10')} | T20:{fmt(res['baseline_rsi_ge30'],'T20')}")
print(f"[下穿30 全部] T5:{fmt(ea)} | T10:{fmt(ea,'T10')} | T20:{fmt(ea,'T20')}")
print(f"[下穿30 日历日聚类] T5:{fmt(ea_d)} | T10:{fmt(ea_d,'T10')} | T20:{fmt(ea_d,'T20')}")
print(f"[下穿30 cd10去重] T5:{fmt(ec)} | T10:{fmt(ec,'T10')} | T20:{fmt(ec,'T20')}")
print(f"[TODO 超额exSPY 全部] T5:{fmt(ea,'T5_ex_spy')} | T10:{fmt(ea,'T10_ex_spy')} | T20:{fmt(ea,'T20_ex_spy')}")
for st, lab in [("A_pre", "疫情前"), ("B_post", "疫情及股灾后"), ("C_bull", "本轮牛市")]:
    sb = res["events_all"]["by_stage"][st]
    print(f"[{lab}] T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}  (n={sb.get('T5',{}).get('n')})")
for sc, lab in SECTOR_CN.items():
    sb = res["events_all"]["by_sector"].get(sc, {})
    if not sb.get("T5", {}).get("n"): continue
    print(f"[{lab}] T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}")
print("当前 RSI<30:", [(c["ticker"], c["rsi"]) for c in res["current"]["rsi_below_30"]])
print(f"written: {os.path.join(OUT, 'blue_chip_rsi_oversold.json')}")