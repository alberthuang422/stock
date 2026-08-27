# -*- coding: utf-8 -*-
"""
MCD 单股版：RSI 摆动低点(swing low)聚集支撑位买入事件研究
口径与 41 号报告（blue_chip_rsi_swing_support.py）完全一致：
  swing low     : 某日 RSI 严格低于前后各 K=5 日的 RSI
  有效支撑      : 过去 WIN=120 日内最近 M=3 个摆动低点，RSI 极差 ≤ CLUSTER_TOL(3)
  支撑位 S      : 这 M 个摆动低点的最低 RSI
  买入触发      : RSI 从上方首日进入 [S-BUF, S+BUF]（BUF=2），当日收盘买入
  去重          : 同票 20 交易日 cooldown；T+N = N 个交易日
附加：当前状态诊断（最近收盘的 RSI、当前生效支撑位、是否位于触发区）。
输出 results/mcd_rsi_swing_support.json
"""
import pandas as pd
import numpy as np
import json, os, bisect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

K = 5
WIN = 120
M = 3
CLUSTER_TOL = 3.0
BUF = 2.0
COOL = 20


def load_stock(name):
    d = os.path.join(DATA, name.lower())
    cands = [p for p in glob_1d(d) if not os.path.basename(p).startswith("BATS_")]
    if not cands:
        return None
    df = pd.read_csv(sorted(cands)[0], parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    df = df.dropna(subset=["px"]).sort_values("date").reset_index(drop=True)
    return df


def glob_1d(d):
    import glob
    return [p for p in glob.glob(os.path.join(d, "*.csv")) if "1D" in os.path.basename(p)]


def rsi_wilder(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = ag / al
    return 100 - 100 / (1 + rs)


def swing_low_mask(arr, k):
    n = len(arr)
    mask = np.zeros(n, dtype=bool)
    for i in range(k, n - k):
        if arr[i] < arr[i - k:i].min() and arr[i] < arr[i + 1:i + k + 1].min():
            mask[i] = True
    return mask


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

g = mcd.sort_values("date").reset_index(drop=True)
rsi_arr = g["rsi"].values
n = len(g)
sl = swing_low_mask(rsi_arr, K)
sl_pos = np.where(sl)[0]
sl_pos = sl_pos[sl_pos < n - K]

buy_rows = []
active_support = []  # (day_idx, S, swing_low_vals, last_sl_date)
last = -10 ** 9
support_at = {}  # day_idx -> (S, vals)
for tt in range(WIN, n):
    lo = tt - WIN + 1
    hi = tt - K
    if hi < lo:
        continue
    idxL = bisect.bisect_left(sl_pos, lo)
    idxR = bisect.bisect_right(sl_pos, hi)
    if idxR - idxL < M:
        continue
    lastM = sl_pos[idxR - M: idxR]
    vals = rsi_arr[lastM]
    if vals.max() - vals.min() > CLUSTER_TOL:
        continue
    S = vals.min()
    support_at[tt] = (S, [float(x) for x in vals], g.iloc[lastM[-1]]["date"])
    rsi_t = rsi_arr[tt]
    rsi_prev = rsi_arr[tt - 1]
    if (S - BUF) <= rsi_t <= (S + BUF) and rsi_prev > (S + BUF):
        if tt - last < COOL:
            continue
        last = tt
        row = g.iloc[tt]
        buy_rows.append({
            "date": row["date"], "rsi": float(rsi_t), "px": float(row["px"]),
            "support": float(S), "swing_lows": [float(x) for x in vals],
            "prev_rsi": float(rsi_prev),
            "stage": stage_of(row["date"]),
            "fwd5": row["fwd5"], "fwd10": row["fwd10"], "fwd20": row["fwd20"],
            "spy_fwd5": row["spy_fwd5"], "spy_fwd10": row["spy_fwd10"], "spy_fwd20": row["spy_fwd20"],
        })

ev = pd.DataFrame(buy_rows)

# 当前日窗口诊断：最近120日 RSI 区间与所有摆动低点（即使不聚集）
lo0_, hi0_ = max(0, n - 1 - WIN + 1), n - 1 - K
idxL0_ = bisect.bisect_left(sl_pos, lo0_)
idxR0_ = bisect.bisect_right(sl_pos, hi0_)
win_sl = sl_pos[idxL0_:idxR0_]
last120_rsi = rsi_arr[lo0_:n]
curdiag = {
    "rsi_min_120d": round(float(last120_rsi.min()), 1),
    "rsi_max_120d": round(float(last120_rsi.max()), 1),
    "swing_lows_120d": [round(float(rsi_arr[i]), 1) for i in win_sl],
    "swing_low_dates_120d": [str(g["date"].iloc[i].date()) for i in win_sl],
}

# 当前状态（仅当前日 tt0=n-1 的 120 日窗口视角，不回退旧支撑） ----------
cur = g.iloc[-1]
cur_rsi = float(cur["rsi"])
tt0 = n - 1
cur_s_detail = None
if tt0 in support_at:
    cur_s, cur_s_vals, cur_s_lastdate = support_at[tt0]
    # 报告窗口内 swing low 数，供诊断说明
    lo0, hi0 = tt0 - WIN + 1, tt0 - K
    idxL0 = bisect.bisect_left(sl_pos, lo0)
    idxR0 = bisect.bisect_right(sl_pos, hi0)
    n_sl_in_win = idxR0 - idxL0
    cur_s_detail = (cur_s, cur_s_vals, cur_s_lastdate, n_sl_in_win)
in_zone = cur_s_detail is not None and (cur_s_detail[0] - BUF) <= cur_rsi <= (cur_s_detail[0] + BUF)
near_zone = cur_s_detail is not None and cur_rsi <= cur_s_detail[0] + BUF + 2

# 最近 400 交易日 RSI / 支撑轨迹（供图表）
last400 = g.iloc[-400:].copy()
chart_series = {
    "dates": [str(d.date()) for d in last400["date"]],
    "px": [round(float(x), 2) for x in last400["px"]],
    "rsi": [round(float(x), 1) for x in last400["rsi"]],
}
# 支撑线轨迹：每日期支撑位（若有）
sup_line = []
for dd in last400["date"]:
    idx_in_full = g.index[g["date"] == dd][0]
    if idx_in_full in support_at:
        sup_line.append(round(float(support_at[idx_in_full][0]), 1))
    else:
        sup_line.append(None)
chart_series["support_line"] = sup_line
# 买入触发点标注
ann = []


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


# 全部交易日基率
base = block(g)

# 分档
def spt_bucket(sv):
    if sv < 35: return "<35"
    if sv < 40: return "35-40"
    if sv < 45: return "40-45"
    if sv < 50: return "45-50"
    return ">=50"

exp = ev.copy()
if len(exp):
    exp["spt_bucket"] = exp["support"].map(spt_bucket)

# 后视战绩：最接近当前的第 1/2/3 个历史事件
recent_ev = ev.sort_values("date").tail(3) if len(ev) else pd.DataFrame()

res = {
    "meta": {
        "ticker": "MCD", "sector": "Consumer",
        "data_range": [str(g["date"].iloc[0].date()), str(g["date"].iloc[-1].date())],
        "params": {"k": K, "window": WIN, "min_swing_lows": M, "cluster_tol": CLUSTER_TOL, "buffer": BUF, "cooldown": COOL},
        "event": "RSI摆动低点(前后5日最低)最近3个聚集(极差≤3)→支撑=最低谷; RSI首日回落进[支撑±2]买入",
        "horizon": "T+N = N 个交易日",
        "stage_map": STAGE_CN,
    },
    "padding": {"n_bars": n, "n_swing_lows": int(len(sl_pos)), "last_date": str(g["date"].iloc[-1].date())},
    "baseline_all_days": base,
    "n_events": int(len(ev)),
    "events_all": block(exp) if len(exp) else {},
    "support_buckets": {bk: block(exp[exp["spt_bucket"] == bk]) for bk in ["<35", "35-40", "40-45", "45-50", ">=50"]} if len(exp) else {},
    "by_stage": {st: block(exp[exp["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]} if len(exp) else {},
    "current": {
        "as_of": str(g["date"].iloc[-1].date()),
        "px": round(float(cur["px"]), 2),
        "rsi": cur_rsi,
        "rsi_prev": round(float(rsi_arr[-2]), 1),
        "support": cur_s_detail[0] if cur_s_detail else None,
        "support_swing_lows": [round(x, 1) for x in cur_s_detail[1]] if cur_s_detail else None,
        "support_last_swing_low_date": str(cur_s_detail[2].date()) if cur_s_detail else None,
        "n_swing_lows_in_120d": cur_s_detail[3] if cur_s_detail else None,
        "in_buy_zone": bool(in_zone),
        "within_4pts_above": bool(near_zone),
        "diag": curdiag,
    },
    "recent_events": [
        {**{"date": str(r["date"].date())}, **{k: (round(float(r[k]), 2) if pd.notna(r[k]) else None) for k in
             ["px", "rsi", "support", "fwd5", "fwd10", "fwd20"]}}
        for _, r in recent_ev.iterrows()
    ] if len(recent_ev) else [],
    "events": [
        {**{"date": str(r["date"].date())}, **{
            "rsi": round(float(r["rsi"]), 1), "px": round(float(r["px"]), 2),
            "support": round(float(r["support"]), 1), "stage": r["stage"],
            "swing_lows": [round(x, 1) for x in r["swing_lows"]],
            "fwd5": round(float(r["fwd5"]), 2) if pd.notna(r["fwd5"]) else None,
            "fwd10": round(float(r["fwd10"]), 2) if pd.notna(r["fwd10"]) else None,
            "fwd20": round(float(r["fwd20"]), 2) if pd.notna(r["fwd20"]) else None,
        }}
        for _, r in ev.sort_values("date", ascending=False).iterrows()
    ],
    "chart": {
        "rsi": chart_series["rsi"], "px": chart_series["px"],
        "dates": chart_series["dates"], "support_line": chart_series["support_line"],
        "baseline_t20": base["T20"]["mean"],
    },
}


def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o


out_path = os.path.join(OUT, "mcd_rsi_swing_support.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)


def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0: return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% win={t['win']}% t={t.get('t')}"


print(f"MCD 数据 {n} 根K线 ({g['date'].iloc[0].date()} ~ {g['date'].iloc[-1].date()}) | swing low {len(sl_pos)} 个")
print(f"支撑买入事件: {len(ev)} 个")
if len(ev):
    eb = block(exp)
    print(f"[基率] T5:{fmt(base)} | T20:{fmt(base,'T20')}")
    print(f"[全部] T5:{fmt(eb)} | T20:{fmt(eb,'T20')} | 超额T20:{fmt(eb,'T20_ex_spy')}")
    for bk in ["<35", "35-40", "40-45", "45-50", ">=50"]:
        b = res["support_buckets"][bk]
        print(f"[支撑 {bk}] n={b.get('T5',{}).get('n','—')} | T5:{fmt(b)} | T20:{fmt(b,'T20')}")
    for st in ["A_pre", "B_post", "C_bull"]:
        print(f"[{STAGE_CN[st]}] T5:{fmt(res['by_stage'][st])} | T20:{fmt(res['by_stage'][st],'T20')}")
c = res["current"]
print(f"[当前] {c['as_of']} 收盘 {c['px']} | RSI={c['rsi']:.1f} (前日 {c['rsi_prev']})")
if c["support"]:
    print(f"[当前支撑] S={c['support']:.1f} 聚集谷值 {c['support_swing_lows']} (最近谷 {c['support_last_swing_low_date']})")
    print(f"[触发区] {'是 —— RSI 正落在 [S-2, S+2] 内' if c['in_buy_zone'] else '否'} | 距触发区上沿 {c['support']+2-c['rsi']:.1f} RSI 点")
else:
    print("[当前支撑] 当前日 120 日窗口内无有效 swing low 聚集（即近半年 RSI 摆动低点未在±3内聚集）")
    dg = res["current"]["diag"]
    print(f"[近120日 RSI] {dg['rsi_min_120d']} ~ {dg['rsi_max_120d']} | 摆动低点 {dg['swing_lows_120d']}")
print(f"written: {out_path}")