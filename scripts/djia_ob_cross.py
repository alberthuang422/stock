# -*- coding: utf-8 -*-
"""
道指成分股横向事件研究：RSI14 上穿 70 后的 T+5/T+10/T+20 表现 + 窗口路径
检验 KO 报告的结论（超买无稳定看空 edge / 阶段分化 / 先冲高再回吐）是否普遍成立。

板块代表（道指 30 只中每板块选 1，最有代表性）：
  信息科技 AAPL / 金融 JPM / 医疗保健 UNH / 可选消费 MCD / 日常消费 KO(基准)
  工业 CAT / 能源 XOM / 材料 SHW / 电信 VZ

统一口径（保证可比）：
  - 数据起点统一 1995-01-03（9 只全部覆盖）
  - RSI14 Wilder(adj_close)，事件=自下而上首次上穿 70
  - 三阶段: A疫情前(~2020-02-19) / B疫情及股灾后(2020-02-20~2022-12-31) / C本轮牛市(2023~)
  - 窗口路径: runup=窗口内最高价(含盘中)相对事件收盘最大涨幅; peakdd=峰值→T+N收盘回撤; maxdd=峰值后峰谷回撤
  - 显式前看窗口 T+1..T+N，避免 rolling 回看污染
统计单位一律百分数。输出 results/djia_ob_cross.json
"""
import pandas as pd
import numpy as np
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

TICKERS = {
    "aapl": "信息科技", "jpm": "金融", "unh": "医疗保健", "mcd": "可选消费", "ko": "日常消费",
    "cat": "工业", "xom": "能源", "shw": "材料", "vz": "电信",
}
NAMES = {"aapl": "苹果", "jpm": "摩根大通", "unh": "联合健康", "mcd": "麦当劳", "ko": "可口可乐",
         "cat": "卡特彼勒", "xom": "埃克森美孚", "shw": "宣伟", "vz": "威瑞森"}
START = pd.Timestamp("1995-01-03")
STAGE_BOUND = pd.Timestamp("2020-02-20")
BULL_START = pd.Timestamp("2023-01-01")


def load_stock(ticker):
    cands = [p for p in glob.glob(os.path.join(DATA, ticker, "*.csv"))
             if not os.path.basename(p).startswith("BATS_")]
    f = sorted(cands)[0]
    df = pd.read_csv(f, parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    fac = df[col] / df["close"]
    df["hi"] = pd.to_numeric(df["high"], errors="coerce") * fac
    df["lo"] = pd.to_numeric(df["low"], errors="coerce") * fac
    df = df[["date", col, "hi", "lo"]].rename(columns={col: "px"})
    df = df.dropna(subset=["px"]).sort_values("date").reset_index(drop=True)
    return df[df["date"] >= START]


def rsi_14(close, period=14):
    d = close.diff()
    g = d.clip(lower=0)
    l = -d.clip(upper=0)
    return 100 - 100 / (1 + g.ewm(alpha=1 / period, adjust=False).mean() / l.ewm(alpha=1 / period, adjust=False).mean())


def add_windows(df, Ns=(5, 10, 20)):
    px_a = df["px"].values
    hi_a = df["hi"].values
    lo_a = df["lo"].values
    n = len(df)
    for N in Ns:
        df[f"fwd{N}"] = np.nan
        runup = np.full(n, np.nan)
        peakdd = np.full(n, np.nan)
        maxdd = np.full(n, np.nan)
        for i in range(n - 1):
            j1, j2 = i + 1, min(i + N, n - 1)
            seg_hi = hi_a[j1:j2 + 1]
            seg_lo = lo_a[j1:j2 + 1]
            if np.isnan(seg_hi).all():
                continue
            pk = np.nanmax(seg_hi)
            runup[i] = (pk / px_a[i] - 1) * 100
            last = px_a[j2]
            # 若最后一个可用日与事件日相同（未完窗口），不算 fwd
            if j2 > i:
                df.loc[df.index[i], f"fwd{N}"] = (last / px_a[i] - 1) * 100
            peakdd[i] = (last / pk - 1) * 100
            pk_idx = int(np.nanargmax(seg_hi))
            after = seg_lo[pk_idx:]
            if len(after) > 0 and not np.isnan(after).all() and j2 > i:
                mn = np.nanmin(after)
                maxdd[i] = (mn / pk - 1) * 100
        df[f"runup{N}"] = runup
        df[f"peakdd{N}"] = peakdd
        df[f"maxdd{N}"] = maxdd
    return df


def stage_of(d):
    if d < STAGE_BOUND:
        return "A_pre"
    if d <= pd.Timestamp("2022-12-31"):
        return "B_post"
    return "C_bull"


def stats(s):
    s = s.dropna()
    if len(s) == 0:
        return {"n": 0}
    return {
        "n": int(len(s)),
        "mean": round(float(s.mean()), 3),
        "median": round(float(s.median()), 3),
        "win": round(float((s > 0).mean()) * 100, 1),
        "p25": round(float(s.quantile(0.25)), 3),
        "p75": round(float(s.quantile(0.75)), 3),
        "t": round(float(s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))), 2) if len(s) > 1 and s.std(ddof=1) > 0 else None,
    }


def block(df, Ns=(5, 10, 20)):
    out = {}
    for N in Ns:
        out[f"T{N}"] = stats(df[f"fwd{N}"])
        out[f"T{N}_runup"] = stats(df[f"runup{N}"])
        out[f"T{N}_peakdd"] = stats(df[f"peakdd{N}"])
        out[f"T{N}_maxdd"] = stats(df[f"maxdd{N}"])
    return out


def analyze(ticker):
    df = load_stock(ticker)
    df["rsi"] = rsi_14(df["px"])
    df = add_windows(df)
    df["cross70"] = (df["rsi"] >= 70) & (df["rsi"].shift(1) < 70)
    df["cross75"] = (df["rsi"] >= 75) & (df["rsi"].shift(1) < 75)
    ev = df[df["cross70"]].copy()
    ev["stage"] = ev["date"].map(stage_of)

    res = {
        "ticker": ticker, "name": NAMES[ticker], "sector": TICKERS[ticker],
        "data_range": [str(df["date"].min().date()), str(df["date"].max().date())],
        "n_days": int(len(df)),
        "n_events": int(len(ev)),
        "n_events_by_stage": {k: int(v) for k, v in ev["stage"].value_counts().items()},
        "baseline": block(df),
        "event_all": block(ev),
        "by_stage": {st: block(ev[ev["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]},
        "rsi75": block(df[df["cross75"]]),
        "events": [
            {"date": str(r["date"].date()), "rsi": round(float(r["rsi"]), 1),
             "px": round(float(r["px"]), 2), "stage": r["stage"],
             "fwd5": None if pd.isna(r["fwd5"]) else round(float(r["fwd5"]), 2),
             "fwd10": None if pd.isna(r["fwd10"]) else round(float(r["fwd10"]), 2),
             "fwd20": None if pd.isna(r["fwd20"]) else round(float(r["fwd20"]), 2),
             "runup20": None if pd.isna(r["runup20"]) else round(float(r["runup20"]), 2),
             "peakdd20": None if pd.isna(r["peakdd20"]) else round(float(r["peakdd20"]), 2),
             "maxdd20": None if pd.isna(r["maxdd20"]) else round(float(r["maxdd20"]), 2)}
            for _, r in ev.iterrows()],
    }
    return res


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o) if not np.isnan(o) else None
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


all_res = {}
for t in TICKERS:
    all_res[t] = analyze(t)

with open(os.path.join(OUT, "djia_ob_cross.json"), "w", encoding="utf-8") as f:
    json.dump(clean(all_res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 打印摘要 ----------
print(f"{'ticker':6s} {'板块':6s} {'n_ev':>4s} {'全T5%':>7s} {'全T20%':>7s} {'牛T5%':>7s} {'牛T20%':>7s} {'r20%':>6s} {'pdd20%':>7s} {'md20%':>7s}")
for t, r in all_res.items():
    ea = r["event_all"]; bs = r["by_stage"]["C_bull"]
    print(f"{t:6s} {r['sector']:6s} {r['n_events']:4d} "
          f"{ea['T5']['mean']:+6.2f} {ea['T20']['mean']:+6.2f} "
          f"{bs['T5']['mean']:+6.2f} {bs['T20']['mean']:+6.2f} "
          f"{ea['T20_runup']['mean']:+5.2f} {ea['T20_peakdd']['mean']:+6.2f} {ea['T20_maxdd']['mean']:+6.2f}")
print(f"written: {os.path.join(OUT, 'djia_ob_cross.json')}")