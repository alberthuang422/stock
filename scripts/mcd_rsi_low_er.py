# -*- coding: utf-8 -*-
"""
MCD RSI 低位（下穿40）事件窗口质量分析：
  ① 窗口内最大涨幅   = max(px[T+1..T+N]) / px[T] - 1   （持有 N 日期间最高点比买入价）
  ② 效率比率 ER      = |px[T+N]-px[T]| / Σ|px[i]-px[i-1]|  (i=T+1..T+N)  （Kaufman ER，0~1）
  ③ SPY 同窗口对照（max_gain / ER / fwdN）→ 回答"为什么 MCD 超额少"
基率：全部交易日 20 日窗口的 max_gain、ER 分布（重叠窗口）。
事件口径与 47 v2 一致：下穿40首日，cd10 去重主口径（另附全部）。
输出 results/mcd_rsi_low_er.json
"""
import pandas as pd
import numpy as np
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

TH = 40
N = 20


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


def bucket(r):
    if r < 30: return "<30"
    if r < 35: return "30-35"
    return "35-40"


mcd = load_stock("MCD")
spy = load_stock("SPY")
assert mcd is not None and spy is not None

df = mcd.merge(spy[["date", "px"]].rename(columns={"px": "spy"}), on="date", how="left")
df["rsi"] = rsi_wilder(df["px"])
df["stage"] = df["date"].map(stage_of)
df["cross"] = (df["rsi"] < TH) & (df["rsi"].shift(1) >= TH)

px = df["px"].values
spy_px = df["spy"].values
n = len(df)

# ---------- 逐日窗口指标（重叠窗口，向量化加速） ----------
def window_feats(px_arr, N=20):
    n_ = len(px_arr)
    maxg = np.full(n_, np.nan)
    er = np.full(n_, np.nan)
    fwd = np.full(n_, np.nan)
    diffs = np.abs(np.diff(px_arr))  # len n_-1, diff[i] = |px[i+1]-px[i]|
    for t in range(n_ - N):
        seg = px_arr[t + 1:t + N + 1]
        maxg[t] = seg.max() / px_arr[t] - 1
        fwd[t] = seg[-1] / px_arr[t] - 1
        path = diffs[t:t + N].sum()
        if path > 0:
            er[t] = abs(seg[-1] - px_arr[t]) / path
    return maxg, er, fwd

m_maxg, m_er, m_fwd = window_feats(px, N)
s_maxg, s_er, s_fwd = window_feats(spy_px, N)

WINS = (5, 10, 20)
for NN in WINS:
    g_, e_, f_ = window_feats(px, NN)
    df[f"m_maxg{NN}"] = g_ * 100
    df[f"m_er{NN}"] = e_
    df[f"m_fwd{NN}"] = f_ * 100

df["m_maxg"] = m_maxg * 100
df["m_er"] = m_er
df["s_maxg"] = s_maxg * 100
df["s_er"] = s_er
df["m_fwd"] = m_fwd * 100
df["s_fwd"] = s_fwd * 100
df["ex"] = df["m_fwd"] - df["s_fwd"]

ev = df[df["cross"]].copy().sort_values("date").reset_index(drop=True)
ev["bucket"] = ev["rsi"].map(bucket)

# cd10 去重：事件日相隔 ≥10 个交易日（df 为 range 位置索引，行号即交易日序号）
cross_idx = df.index[df["cross"]].tolist()
keep_idx = []
last_row = -10 ** 9
for ri in cross_idx:
    if ri - last_row >= 10:
        keep_idx.append(ri)
        last_row = ri
ev_cd10 = df.loc[keep_idx].copy().sort_values("date").reset_index(drop=True)
ev_cd10["bucket"] = ev_cd10["rsi"].map(bucket)


def stats(s):
    s = pd.Series(s).dropna()
    if len(s) == 0:
        return {"n": 0}
    return {
        "n": int(len(s)),
        "mean": round(float(s.mean()), 3),
        "median": round(float(s.median()), 3),
        "p25": round(float(s.quantile(0.25)), 3),
        "p75": round(float(s.quantile(0.75)), 3),
    }


def blk(df_):
    out = {}
    for k, lab in [("m_maxg", "MCD窗口最大涨幅%"), ("s_maxg", "SPY窗口最大涨幅%"),
                   ("m_er", "MCD ER"), ("s_er", "SPY ER"),
                   ("m_fwd", "MCD T+20%"), ("s_fwd", "SPY T+20%"), ("ex", "超额T+20pp")]:
        out[k] = stats(df_[k])
    return out


# 基率：全部有完整窗口的交易日
valid = df.dropna(subset=["m_fwd"])
base = blk(valid)

# 分档（cd10 主口径 + 全部）
buckets_cd10 = {bk: blk(ev_cd10[ev_cd10["bucket"] == bk]) for bk in ["<30", "30-35", "35-40"]}
buckets_all = {bk: blk(ev[ev["bucket"] == bk]) for bk in ["<30", "30-35", "35-40"]}

# 分阶段（cd10）
stage_cd10 = {}
for st in ["A_pre", "B_post", "C_bull"]:
    sub = ev_cd10[ev_cd10["stage"] == st]
    stage_cd10[st] = blk(sub) if len(sub) else {"_empty": True}

# 近年（2023~）与早期对比（cd10 内近年事件）
res = {
    "meta": {
        "ticker": "MCD", "event": f"RSI下穿{TH}首日买入, 窗口N={N}交易日",
        "defs": {
            "max_gain": "max(px[t+1..t+N])/px[t]-1，窗口内最高点相对买入价",
            "er": "Kaufman 效率比率 |px[t+N]-px[t]| / Σ|Δpx| (0~1，越高越单边流畅)",
            "base": "全部交易日重叠20日窗口的分布",
        },
    },
    "base": base,
    "cd10_n": int(len(ev_cd10)),
    "buckets_cd10": buckets_cd10,
    "buckets_all": buckets_all,
    "stage_cd10": stage_cd10,
    "events_cd10": [
        {**{"date": str(r["date"].date()), "rsi": round(float(r["rsi"]), 1), "bucket": r["bucket"]},
         **{"px": (round(float(r["px"]), 2) if pd.notna(r["px"]) else None)},
         **{f"m_maxg{NN}": (round(float(r[f"m_maxg{NN}"]), 2) if pd.notna(r[f"m_maxg{NN}"]) else None) for NN in WINS},
         **{f"m_er{NN}": (round(float(r[f"m_er{NN}"]), 2) if pd.notna(r[f"m_er{NN}"]) else None) for NN in WINS},
         **{f"m_fwd{NN}": (round(float(r[f"m_fwd{NN}"]), 2) if pd.notna(r[f"m_fwd{NN}"]) else None) for NN in WINS},
         **{k: (round(float(r[k]), 2) if pd.notna(r[k]) else None) for k in
            ["s_maxg", "s_er", "m_fwd", "s_fwd", "ex"]}}
        for _, r in ev_cd10.sort_values("date", ascending=False).iterrows()
    ],
}


def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o


out_path = os.path.join(OUT, "mcd_rsi_low_er.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)


def fm(s):
    if not s or s.get("n", 0) == 0 or s.get("_empty"): return "—"
    return f"n={s['n']} mean={s['mean']:+.2f} med={s['median']:+.2f}"


print(f"MCD {n} 根K线 | 下穿{TH}事件 {len(ev)} (cd10 {len(ev_cd10)}) | 窗口 {N} 日")
print(f"[基率·全部20日窗口] MCD maxGain:{fm(base['m_maxg'])} | MCD ER:{fm(base['m_er'])} | SPY maxGain:{fm(base['s_maxg'])} | SPY ER:{fm(base['s_er'])}")
print(f"[基率] MCD T20:{fm(base['m_fwd'])} | SPY T20:{fm(base['s_fwd'])} | 超额:{fm(base['ex'])}")
print("-- cd10 事件分档 --")
for bk in ["<30", "30-35", "35-40"]:
    b = buckets_cd10[bk]
    print(f"[档 {bk}] MCD maxGain:{fm(b['m_maxg'])} | MCD ER:{fm(b['m_er'])} | SPY maxGain:{fm(b['s_maxg'])} | SPY ER:{fm(b['s_er'])} | 超额:{fm(b['ex'])}")
print("-- cd10 分阶段 --")
for st, lab in [("A_pre", "疫情前"), ("B_post", "疫情及股灾后"), ("C_bull", "本轮牛市")]:
    b = stage_cd10[st]
    print(f"[{lab}] n={b.get('m_maxg',{}).get('n','—')} | MCD maxGain:{fm(b['m_maxg'])} | MCD ER:{fm(b['m_er'])} | 超额:{fm(b['ex'])}")
print(f"written: {out_path}")