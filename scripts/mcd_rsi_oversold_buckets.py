# -*- coding: utf-8 -*-
"""
MCD 单股版：RSI 低位（下穿40首日）买入事件研究 —— RSI 低位分档
口径沿 39 号（blue_chip_rsi_oversold.py）扩展：事件阈值放宽到 40，覆盖整个低位区间。
  RSI     : Wilder RSI14(adj_close)
  事件     : RSI 自上下穿 40 首日（前一日>=40，当日<40），当日收盘买入
  T+N     : N 个交易日（shift(-N)）
  分档     : 按买入时 RSI 分  <30（超卖）/ 30-35 / 35-40（偏低回调）
  稳健性   : cd10 = 同票 10 交易日去重
附加：当前状态（现 RSI、是否在低位区间、最近一次信号）。
输出 results/mcd_rsi_oversold_buckets.json
"""
import pandas as pd
import numpy as np
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

TH = 40  # 下穿阈值

def load_stock(name):
    d = os.path.join(DATA, name.lower())
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
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = ag / al
    return 100 - 100 / (1 + rs)


def stage_of(d):
    if d < pd.Timestamp("2020-02-20"):
        return "A_pre"
    if d <= pd.Timestamp("2022-12-31"):
        return "B_post"
    return "C_bull"


STAGE_CN = {"A_pre": "疫情前(1995~2020-02)", "B_post": "疫情及股灾后(2020-02~2022-12)", "C_bull": "本轮牛市(2023~)"}

mcd = load_stock("MCD")
spy = load_stock("SPY")
assert mcd is not None and spy is not None

mcd["rsi"] = rsi_wilder(mcd["px"])
for N in (5, 10, 20):
    mcd[f"fwd{N}"] = (mcd["px"].shift(-N) / mcd["px"] - 1) * 100
mcd = mcd.merge(spy[["date", "px"]].rename(columns={"px": "spy"}), on="date", how="left")
for N in (5, 10, 20):
    mcd[f"spy_fwd{N}"] = (mcd["spy"].shift(-N) / mcd["spy"] - 1) * 100

mcd["cross"] = (mcd["rsi"] < TH) & (mcd["rsi"].shift(1) >= TH)
mcd["stage"] = mcd["date"].map(stage_of)

ev = mcd[mcd["cross"]].copy()

# cd10 去重
g = ev.sort_values("date").reset_index(drop=True)
keep, last = [], -10 ** 9
for i in range(len(g)):
    if i - last >= 10:
        keep.append(i)
        last = i
ev_cd10 = g.iloc[keep]


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


def bucket(r):
    if r < 30: return "<30"
    if r < 35: return "30-35"
    return "35-40"


ev = ev.copy()
ev["bucket"] = ev["rsi"].map(bucket)
ev_cd10 = ev_cd10.copy()
ev_cd10["bucket"] = ev_cd10["rsi"].map(bucket)

# 低位区间所有日对照（不限于下穿首日）
mcd_lt40 = mcd[mcd["rsi"] < 40].copy()
mcd_lt40["bucket"] = mcd_lt40["rsi"].map(bucket)

res = {
    "meta": {
        "ticker": "MCD", "sector": "Consumer",
        "data_range": [str(mcd["date"].iloc[0].date()), str(mcd["date"].iloc[-1].date())],
        "rsi": "Wilder RSI14 on adj_close",
        "event": f"RSI 下穿 {TH} 首日（前一日>={TH}，当日<{TH}），当日收盘买入",
        "horizon": "T+N = N 个交易日",
        "bucket": "按买入时 RSI 分档：<30 超卖 / 30-35 / 35-40 偏低回调",
        "stage_map": STAGE_CN,
    },
    "baseline_all_days": block(mcd),
    "baseline_lt30": block(mcd[mcd["rsi"] < 30]),       # 所有 RSI<30 日
    "baseline_lt40": block(mcd_lt40),                   # 所有 RSI<40 日
    "baseline_buckets": {bk: block(mcd_lt40[mcd_lt40["bucket"] == bk]) for bk in ["<30", "30-35", "35-40"]},
    "n_events": {"cross%d_all" % TH: int(len(ev)), "cross%d_cd10" % TH: int(len(ev_cd10))},
    "events_all": {
        "block": block(ev),
        "day_clustered": block(day_cluster(ev)),
        "by_stage": {st: block(ev[ev["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]},
    },
    "events_cd10": {"block": block(ev_cd10)},
    "buckets_all": {bk: block(ev[ev["bucket"] == bk]) for bk in ["<30", "30-35", "35-40"]},
    "buckets_cd10": {bk: block(ev_cd10[ev_cd10["bucket"] == bk]) for bk in ["<30", "30-35", "35-40"]},
    "by_year": {str(y): block(ev[ev["date"].dt.year == y]) for y in sorted(ev["date"].dt.year.unique())},
    "current": {
        "as_of": str(mcd["date"].iloc[-1].date()),
        "px": round(float(mcd["px"].iloc[-1]), 2),
        "rsi": round(float(mcd["rsi"].iloc[-1]), 1),
        "rsi_prev": round(float(mcd["rsi"].iloc[-2]), 1),
        "below_30": bool(mcd["rsi"].iloc[-1] < 30),
        "below_35": bool(mcd["rsi"].iloc[-1] < 35),
        "below_40": bool(mcd["rsi"].iloc[-1] < 40),
    },
    "events": [
        {**{"date": str(r["date"].date())}, **{
            "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
            "stage": r["stage"], "bucket": r["bucket"],
            "fwd5": round(float(r["fwd5"]), 2) if pd.notna(r["fwd5"]) else None,
            "fwd10": round(float(r["fwd10"]), 2) if pd.notna(r["fwd10"]) else None,
            "fwd20": round(float(r["fwd20"]), 2) if pd.notna(r["fwd20"]) else None,
        }}
        for _, r in ev.sort_values("date", ascending=False).iterrows()
    ],
    "events_cd10_list": [
        {**{"date": str(r["date"].date())}, **{
            "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
            "stage": r["stage"],
            "fwd5": round(float(r["fwd5"]), 2) if pd.notna(r["fwd5"]) else None,
            "fwd10": round(float(r["fwd10"]), 2) if pd.notna(r["fwd10"]) else None,
            "fwd20": round(float(r["fwd20"]), 2) if pd.notna(r["fwd20"]) else None,
        }}
        for _, r in ev_cd10.sort_values("date", ascending=False).iterrows()
    ],
    "chart": {
        "dates": [str(d.date()) for d in (mcd["date"].iloc[-600:])],
        "px": [round(float(x), 2) for x in mcd["px"].iloc[-600:]],
        "rsi": [round(float(x), 1) for x in mcd["rsi"].iloc[-600:]],
        "ev_dates": [str(d.date()) for d in ev["date"]],
        "ev_rsi": [round(float(x), 1) for x in ev["rsi"]],
        "cur_rsi": round(float(mcd["rsi"].iloc[-1]), 1),
    },
}


def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o


out_path = os.path.join(OUT, "mcd_rsi_oversold_buckets.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)


def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0: return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% win={t['win']}% t={t.get('t')}"


b = res["baseline_all_days"]
ea = res["events_all"]["block"]
ec = res["events_cd10"]["block"]
print(f"MCD 数据 {len(mcd)} 根K线 ({mcd['date'].iloc[0].date()} ~ {mcd['date'].iloc[-1].date()})")
print(f"下穿{TH}事件: 全部 {len(ev)} | cd10去重 {len(ev_cd10)}")
print(f"[基率] T5:{fmt(b)} | T10:{fmt(b,'T10')} | T20:{fmt(b,'T20')}")
print(f"[RSI<30所有日] T5:{fmt(res['baseline_lt30'])} | T20:{fmt(res['baseline_lt30'],'T20')}")
print(f"[RSI<40所有日] T5:{fmt(res['baseline_lt40'])} | T20:{fmt(res['baseline_lt40'],'T20')}")
print(f"[下穿{TH} 全部] T5:{fmt(ea)} | T10:{fmt(ea,'T10')} | T20:{fmt(ea,'T20')} | 超额T20:{fmt(ea,'T20_ex_spy')}")
print(f"[下穿{TH} cd10] T5:{fmt(ec)} | T10:{fmt(ec,'T10')} | T20:{fmt(ec,'T20')}")
for bk in ["<30", "30-35", "35-40"]:
    bb = res["buckets_all"][bk]
    bl = res["baseline_buckets"][bk]
    print(f"[下穿档 {bk}] n={bb.get('T5',{}).get('n','—')} | T5:{fmt(bb)} | T10:{fmt(bb,'T10')} | T20:{fmt(bb,'T20')} | 超额T20:{fmt(bb,'T20_ex_spy')} | (同档所有日T20:{fmt(bl,'T20')})")
for st in ["A_pre", "B_post", "C_bull"]:
    sb = res["events_all"]["by_stage"][st]
    print(f"[{STAGE_CN[st]}] n={sb.get('T5',{}).get('n')} | T5:{fmt(sb)} | T20:{fmt(sb,'T20')}")
c = res["current"]
print(f"[当前] {c['as_of']} 收盘 {c['px']} | RSI={c['rsi']}{'（<30 超卖中）' if c['below_30'] else ('（30-35）' if c['below_35'] else ('（35-40）' if c['below_40'] else '（>40 非低位）'))}")
print(f"written: {out_path}")