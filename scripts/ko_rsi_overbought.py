# -*- coding: utf-8 -*-
"""
KO 日线 RSI14 进入超买区间(上穿70)后的 T+5 / T+10 表现
事件定义：RSI14(adj_close, Wilder) 自下而上穿越 70 的首日（前一日<70，当日>=70），以当日收盘为基准。
阶段划分：
  A 疫情前        : 数据起点 ~ 2020-02-19（美股疫情暴跌前夜，SPY 2020-02-19 见顶）
  B 疫情及股灾后  : 2020-02-20 ~ 2022-12-31（细分 B1 暴跌+V反 / B2 放水牛 / B3 2022熊市）
  C 本轮牛市      : 2023-01-01 ~ 今（自 2022-10 低点反转后的牛市，另按 2023/2024/2025/2026YTD 逐年）
对照：全历史所有交易日基率；RSI<70 日；SPY / XLP 同期 fwd 超额。
统计单位：一律百分数（×100）。结果写 results/ko_rsi_overbought.json（不打印明细）。
"""
import pandas as pd
import numpy as np
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

def load_stock(name):
    cands = [p for p in glob.glob(os.path.join(DATA, name, "*.csv"))
             if not os.path.basename(p).startswith("BATS_")]
    f = sorted(cands)[0]
    df = pd.read_csv(f, parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df

def rsi_14(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = ag / al
    return 100 - 100 / (1 + rs)

ko = load_stock("ko")
spy = load_stock("spy").rename(columns={"px": "spy"})
xlp = load_stock("xlp").rename(columns={"px": "xlp"})

ko["rsi"] = rsi_14(ko["px"])
for N in (5, 10, 20):
    ko[f"fwd{N}"] = (ko["px"].shift(-N) / ko["px"] - 1) * 100

ko = ko.merge(spy[["date", "spy"]], on="date", how="left") \
       .merge(xlp[["date", "xlp"]], on="date", how="left")
for N in (5, 10, 20):
    ko[f"spy_fwd{N}"] = (ko["spy"].shift(-N) / ko["spy"] - 1) * 100
    ko[f"xlp_fwd{N}"] = (ko["xlp"].shift(-N) / ko["xlp"] - 1) * 100

ko["cross70"] = (ko["rsi"] >= 70) & (ko["rsi"].shift(1) < 70)
ko["cross75"] = (ko["rsi"] >= 75) & (ko["rsi"].shift(1) < 75)

def stage_of(d):
    if d < pd.Timestamp("2020-02-20"):
        return "A_pre"
    if d <= pd.Timestamp("2022-12-31"):
        return "B_post"
    return "C_bull"

def substage_of(d):
    if d < pd.Timestamp("2020-02-20"): return "A 疫情前(1995~2020-02)"
    if d < pd.Timestamp("2020-06-01"): return "B1 暴跌+V反(2020-02~05)"
    if d <= pd.Timestamp("2021-12-31"): return "B2 放水牛(2020-06~2021)"
    if d <= pd.Timestamp("2022-12-31"): return "B3 2022熊市"
    return "C 本轮牛市(2023~)"

def bull_year_of(d):
    return str(d.year) + ("YTD" if d.year == 2026 else "")

def stats(df, col):
    s = df[col].dropna()
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
        out[f"T{N}"] = stats(df, f"fwd{N}")
        out[f"T{N}_ex_spy"] = stats(df.assign(x=df[f"fwd{N}"] - df[f"spy_fwd{N}"]), "x")
        out[f"T{N}_ex_xlp"] = stats(df.assign(x=df[f"fwd{N}"] - df[f"xlp_fwd{N}"]), "x")
    return out

ev_all = ko[ko["cross70"]].copy()
ev_all["stage"] = ev_all["date"].map(stage_of)
ev_all["substage"] = ev_all["date"].map(substage_of)

# cooldown=10 稳健性：事件后 10 个交易日内再上穿不重复计
ev_cd = []
last = -10**9
for i, row in ev_all.iterrows():
    if i - last >= 10:
        ev_cd.append(i); last = i
ev_cd10 = ev_all.loc[ev_cd]

res = {
    "meta": {
        "ticker": "KO",
        "data_range": [str(ko["date"].min().date()), str(ko["date"].max().date())],
        "rsi": "Wilder RSI14 on adj_close",
        "event": "RSI 上穿 70 首日，当日收盘为基准",
        "stages": {
            "A_pre": "疫情前：~2020-02-19",
            "B_post": "疫情及股灾后：2020-02-20~2022-12-31",
            "C_bull": "本轮牛市：2023-01-01~",
        },
    },
    "n_events": {"all": len(ev_all), "cd10": len(ev_cd10),
                 "by_stage": ev_all["stage"].value_counts().to_dict()},
    "baseline_all_days": block(ko),
    "ctrl_rsi_lt70": block(ko[ko["rsi"] < 70]),
    "event_stats_all": block(ev_all),
    "event_stats_cd10": block(ev_cd10),
    "by_stage": {st: block(ev_all[ev_all["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]},
    "by_substage": {ss: block(ev_all[ev_all["substage"] == ss])
                    for ss in ev_all["substage"].unique()},
    "bull_by_year": {y: block(ev_all[(ev_all["stage"] == "C_bull") &
                                     (ev_all["date"].map(bull_year_of) == y)])
                     for y in sorted(ev_all[ev_all["stage"] == "C_bull"]["date"].map(bull_year_of).unique())},
    "pre_by_year": {str(y): block(ev_all[(ev_all["stage"] == "A_pre") & (ev_all["date"].dt.year == y)])
                    for y in sorted(ev_all[ev_all["stage"] == "A_pre"]["date"].dt.year.unique())},
    "rsi75_robust": block(ko[ko["cross75"]]),
}

# 事件明细（瘦身：只留必要列）
ev_list = []
for _, r in ev_all.iterrows():
    ev_list.append({
        "date": str(r["date"].date()), "rsi": round(float(r["rsi"]), 1),
        "px": round(float(r["px"]), 2), "stage": r["stage"], "substage": r["substage"],
        "fwd5": None if pd.isna(r["fwd5"]) else round(float(r["fwd5"]), 2),
        "fwd10": None if pd.isna(r["fwd10"]) else round(float(r["fwd10"]), 2),
        "fwd20": None if pd.isna(r["fwd20"]) else round(float(r["fwd20"]), 2),
        "spy5": None if pd.isna(r["spy_fwd5"]) else round(float(r["spy_fwd5"]), 2),
        "spy10": None if pd.isna(r["spy_fwd10"]) else round(float(r["spy_fwd10"]), 2),
        "spy20": None if pd.isna(r["spy_fwd20"]) else round(float(r["spy_fwd20"]), 2),
        "xlp5": None if pd.isna(r["xlp_fwd5"]) else round(float(r["xlp_fwd5"]), 2),
        "xlp10": None if pd.isna(r["xlp_fwd10"]) else round(float(r["xlp_fwd10"]), 2),
        "xlp20": None if pd.isna(r["xlp_fwd20"]) else round(float(r["xlp_fwd20"]), 2),
    })
res["events"] = ev_list

# 当前状态
last_row = ko.iloc[-1]
in_ob = bool(last_row["rsi"] >= 70)
# 当前若处于超买段，找该段起点
if in_ob:
    below = ko.index[ko["rsi"] < 70]
    seg_start = below.max() + 1 if len(below) else ko.index.min()
    seg = ko.loc[seg_start:]
    cur = {"in_overbought": True, "days_in_segment": int(len(seg)),
           "segment_start": str(seg["date"].iloc[0].date()),
           "rsi_now": round(float(last_row["rsi"]), 1),
           "px_now": round(float(last_row["px"]), 2),
           "as_of": str(last_row["date"].date())}
else:
    cur = {"in_overbought": False, "rsi_now": round(float(last_row["rsi"]), 1),
           "px_now": round(float(last_row["px"]), 2),
           "as_of": str(last_row["date"].date())}
res["current"] = cur

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, float) and (np.isnan(o)): return None
    return o

with open(os.path.join(OUT, "ko_rsi_overbought.json"), "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 汇总 KPI（只打印摘要） ----------
def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0: return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% win={t['win']}%"

print(f"数据范围: {res['meta']['data_range']}  | 当前RSI={cur['rsi_now']} 超买中={cur['in_overbought']}")
print(f"上穿70事件总数: {len(ev_all)}  (cooldown10: {len(ev_cd10)})")
print(f"  全历史基率: T5: {fmt(res['baseline_all_days'])} | T10: {fmt(res['baseline_all_days'],'T10')} | T20: {fmt(res['baseline_all_days'],'T20')}")
print(f"  RSI<70对照: T5: {fmt(res['ctrl_rsi_lt70'])} | T10: {fmt(res['ctrl_rsi_lt70'],'T10')} | T20: {fmt(res['ctrl_rsi_lt70'],'T20')}")
for st, lab in [("A_pre", "疫情前"), ("B_post", "疫情及股灾后"), ("C_bull", "本轮牛市")]:
    b = res["by_stage"][st]
    print(f"  [{lab}] T5: {fmt(b)} | T10: {fmt(b,'T10')} | T20: {fmt(b,'T20')}")
for ss in sorted(res["by_substage"]):
    b = res["by_substage"][ss]
    print(f"    {ss}: T5: {fmt(b)} | T10: {fmt(b,'T10')} | T20: {fmt(b,'T20')}")
print(f"  RSI>=75 稳健性: T5: {fmt(res['rsi75_robust'])} | T10: {fmt(res['rsi75_robust'],'T10')} | T20: {fmt(res['rsi75_robust'],'T20')}")
print(f"written: {os.path.join(OUT, 'ko_rsi_overbought.json')}")
