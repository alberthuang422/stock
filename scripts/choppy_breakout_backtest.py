# -*- coding: utf-8 -*-
"""
震荡市 × 个股波段突破延续性回测（v1 依据用户 09-04 拍板口径）

口径要点
--------
【大盘震荡态 SPY，日频逐日，无前视】或逻辑：
  路径A 均线缠绕：Neck = (|MA30-MA60|+|MA60-MA120|+|MA30-MA120|)/(2*close) ≤ 0.03
        且 Neck20chg ≤ 0（20日前水平比，扩散收敛/持平），持续 ≥15 日（滚动全真窗口）
  路径B RSI中枢：RSI14 的 20 日均值 ∈ [40,60]，持续 ≥30 日（用户要求 RSI 路径持续更长）
  choppy_day = A ∨ B（任一路径激活即震荡态）
  震荡窗口：连续 choppy_day 比例 ≥60% 且长度 ≥15 交易日；首尾外扩 5 日（外扩日标 ext=True）

【个股突破事件】篮子 = blue_chips 73 + 热榜50（去重），ZigZag(K) pending 确认拐点：
  向上首破：收盘 > 最近已确认波段高点*(1+e)；向下首破：收盘 < 最近已确认波段低点*(1-e)
  e=0.5% 主口径（敏感 0.2/1.0），K=5% 主口径（敏感 8%）
  首破定义：前一日不在同向突破态；同向 20 交易日冷却；突破日 ∈ 震荡窗（A组）或趋势日（B组）

【统计】T+5/10/20/60（交易日）绝对收益、超额（减SPY同期）、假突破率
  （多头：T+10 内收盘跌回突破位下方；空头：T+10 内收盘收复突破位上方）、
  存活率（T+20 内未回撤 5%）、MAE（突破后 T+20 最大不利偏移 %）
  C组 = 该股全历史随机日（排除与A/B事件日±10日重叠）×200 抽样/票，作为无条件基线
  显著性：t 值；样本按 (ticker, 年) 聚类说明为上限
【节点分层】9月-10月底 / 中期选举前2月(2018-08~09,2022-08~09,2026-08~09) /
  大选前2月(2020-08~09,2024-08~09)——按事件日归窗（多窗重叠取并集单列）
输出 results/choppy_breakout.json + results/choppy_breakout_events.csv
"""
import pandas as pd
import numpy as np
import json, os, glob, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

# ---------------- 参数（冻结） ----------------
NECK_TH = 0.03        # 均线缠绕阈值
NECK_PERSIST = 15     # 缠绕持续天数
RSI_LO, RSI_HI = 40.0, 60.0
RSI_PERSIST = 30      # RSI路径持续天数（用户：不要太短）
WIN_MIN = 15          # 震荡窗口最短
WIN_FRAC = 0.60
EXT = 5               # 窗口首尾外扩
ZIG_K_MAIN, ZIG_K_ALT = 5.0, 8.0
BRK_E_MAIN = 0.005
BRK_E_SENS = [0.002, 0.010]
COOL = 20
FWD = (5, 10, 20, 60)
MAE_WIN = 20
STOP = 5.0            # 存活判定回撤 %
FAKE_WIN = 10         # 假突破判定窗口
FAKE_ADR_MULT = 1.5   # 假突破判定：偏离突破位 ≥1.5×ADR(20日平均真实波幅%)
N_RANDOM = 200        # C组每票抽样

# ---------------- 数据加载 ----------------
def load_stock(name):
    d = os.path.join(DATA, name.lower())
    if not os.path.isdir(d):
        return None
    cands = [p for p in glob.glob(os.path.join(d, "*.csv"))
             if not os.path.basename(p).startswith("BATS_") and "1D" in os.path.basename(p)]
    if not cands:
        return None
    df = pd.read_csv(sorted(cands)[0], parse_dates=["date"])
    cols = {"date": "date"}
    if "adj_close" in df.columns:
        cols["adj_close"] = "px"
    else:
        cols["close"] = "px"
    keep = list(cols.keys())
    if "high" in df.columns and "low" in df.columns:
        cols["high"] = "high"; cols["low"] = "low"; cols["close"] = "close"
        keep = list(dict.fromkeys(keep + ["high", "low", "close"]))
    df = df[keep].rename(columns=cols)
    df = df.dropna(subset=["px"]).sort_values("date").reset_index(drop=True)
    return df

tickers, src = [], {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t); src[t] = "bluechip"
hot = json.load(open(os.path.join(OUT, "rsi14_hot_20260904.json"), encoding="utf-8"))
for h in hot[:50]:
    t = h["code"].strip()
    if t not in src:
        tickers.append(t); src[t] = "hot50"

spy = load_stock("SPY").rename(columns={"px": "spy"})
assert spy is not None and len(spy) > 5000, "SPY data missing"

# ---------------- 大盘震荡态 ----------------
def build_spy_regime(spy_df):
    df = spy_df.copy().reset_index(drop=True)
    df["ma30"] = df["spy"].rolling(30).mean()
    df["ma60"] = df["spy"].rolling(60).mean()
    df["ma120"] = df["spy"].rolling(120).mean()
    df["neck"] = (df["ma30"] - df["ma60"]).abs() + (df["ma60"] - df["ma120"]).abs() + (df["ma30"] - df["ma120"]).abs()
    df["neck"] = df["neck"] / (2 * df["spy"])
    df["neck20chg"] = df["neck"] - df["neck"].shift(20)
    d = df["spy"].diff()
    up = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    df["rsi14"] = 100 - 100 / (1 + up / dn)
    df["rsi20avg"] = df["rsi14"].rolling(20).mean()

    raw_a = (df["neck"] <= NECK_TH) & (df["neck20chg"] <= 1e-9) & (df["neck"].rolling(5).mean().diff() <= 1e-9)
    raw_b = df["rsi20avg"].between(RSI_LO, RSI_HI)

    # 滚动持续窗口激活（要求窗口内全真），一旦满足则整个窗口标 True
    a_state = np.zeros(len(df), dtype=bool)
    b_state = np.zeros(len(df), dtype=bool)
    av = raw_a.values; bv = raw_b.values
    a_s = a_state; b_s = b_state
    run = 0
    for i in range(len(df)):
        run = run + 1 if av[i] else 0
        if run >= NECK_PERSIST:
            a_s[i - NECK_PERSIST + 1: i + 1] = True
    run = 0
    for i in range(len(df)):
        run = run + 1 if bv[i] else 0
        if run >= RSI_PERSIST:
            b_s[i - RSI_PERSIST + 1: i + 1] = True
    df["path_a"] = pd.Series(a_state, index=df.index)
    df["path_b"] = pd.Series(b_state, index=df.index)
    df["choppy_raw"] = df["path_a"] | df["path_b"]

    # 连续震荡窗口：滑动 15 日窗内 raw 比例 ≥60% → 窗内全标 choppy_day
    cv = df["choppy_raw"].astype(int).values
    n = len(cv)
    csum = np.concatenate([[0], np.cumsum(cv)])
    day = np.zeros(n, dtype=bool)
    W = WIN_MIN
    for i in range(W - 1, n):
        frac = (csum[i + 1] - csum[i + 1 - W]) / W
        if frac >= WIN_FRAC:
            day[i + 1 - W: i + 1] = True
    df["choppy_day"] = day

    # 合并窗口（间隔<10日合并），≥WIN_MIN 才保留，首尾外扩 EXT
    idx = np.where(day)[0]
    windows = []
    if len(idx):
        s = p = idx[0]
        for x in idx[1:]:
            if x - p <= 10:
                p = x
            else:
                windows.append((s, p)); s = p = x
        windows.append((s, p))
    win_rows = []
    for s, e in windows:
        if e - s + 1 < WIN_MIN:
            continue
        s2 = max(0, s - EXT); e2 = min(n - 1, e + EXT)
        win_rows.append({"start": df["date"].iloc[s2], "end": df["date"].iloc[e2],
                         "len": e2 - s2 + 1, "core_start": df["date"].iloc[s], "core_end": df["date"].iloc[e]})
        df.loc[s2:e2, "choppy_day"] = True
    df["in_window"] = df["choppy_day"]
    df["choppy_a"] = df["path_a"]
    win_df = pd.DataFrame(win_rows)
    return df[["date", "spy", "choppy_day", "choppy_a"]], win_df

spy_reg, spy_wins = build_spy_regime(spy)
spy_reg.to_csv(os.path.join(OUT, "choppy_regime_spy.csv"), index=False)
spy_wins.to_csv(os.path.join(OUT, "choppy_regime_windows.csv"), index=False)
print(f"SPY 震荡窗数={len(spy_wins)} 覆盖天数={int(spy_reg['choppy_day'].sum())} ({spy_reg['choppy_day'].mean()*100:.1f}%)")

# ---------------- 节点窗口 ----------------
def node_windows(d):
    y = d.year
    w = []
    w.append("sep_oct")
    if y in (2018, 2022, 2026) and d.month in (8, 9):
        w.append("midterm_pre2m")
    if y in (2020, 2024) and d.month in (8, 9):
        w.append("president_pre2m")
    return w

# ---------------- ZigZag pending 确认拐点（复用 45 号机制） ----------------
def zigzag_pivots(close, th):
    """返回已确认拐点列表 [(idx, price, 'H'|'L')]，无前视使用（突破信号仅用确认点）"""
    n = len(close)
    piv = []
    if n < 3:
        return piv
    direction = 0  # 1 up, -1 down, 0 unknown
    ext_i = 0
    pending_i = None
    for i in range(1, n):
        c = close[i]
        if direction == 0:
            if c >= close[ext_i] * (1 + th / 100):
                piv.append((ext_i, close[ext_i], "L")); direction = 1; ext_i = i
            elif c <= close[ext_i] * (1 - th / 100):
                piv.append((ext_i, close[ext_i], "H")); direction = -1; ext_i = i
            else:
                if c > close[ext_i]: ext_i = i
                elif c < close[ext_i]: ext_i = i
        elif direction == 1:
            if c > close[ext_i]:
                ext_i = i; pending_i = None
            elif c <= close[ext_i] * (1 - th / 100):
                piv.append((ext_i, close[ext_i], "H"))
                direction = -1; ext_i = i; pending_i = None
        else:
            if c < close[ext_i]:
                ext_i = i; pending_i = None
            elif c >= close[ext_i] * (1 + th / 100):
                piv.append((ext_i, close[ext_i], "L"))
                direction = 1; ext_i = i; pending_i = None
    return piv

# ---------------- 事件检测 ----------------
def detect_events(df, K_th, e):
    """df: 一只票的日线。返回事件列表"""
    px = df["px"].values
    piv = zigzag_pivots(px, K_th)
    piv = [(i, p, t) for (i, p, t) in piv if i < len(px) - 1]  # 确认点（i 之后至少 1 根K线已走完才可能确认）
    events = []
    last_up = last_dn = -10**9
    up_state = dn_state = False  # 当前是否处于突破态（未回补）
    up_ref = dn_ref = None
    pi = 0
    last_conf_h = last_conf_l = None
    for t in range(1, len(px)):
        # 更新已确认拐点：pivot 确认时刻 ≈ 反向下折被触发那根K线（这里近似：pivot idx 后第一次反向达标）
        while pi < len(piv) and piv[pi][0] < t - 1:
            _, p, typ = piv[pi]
            if typ == "H":
                last_conf_h = p
            else:
                last_conf_l = p
            pi += 1
        c = px[t]
        # 突破态维护
        if up_state and c < up_ref:
            up_state = False
        if dn_state and c > dn_ref:
            dn_state = False
        up_fire = dn_fire = False
        if last_conf_h is not None and c > last_conf_h * (1 + e) and not up_state and t - last_up >= COOL:
            up_fire = True; up_state = True; up_ref = last_conf_h; last_up = t
        if last_conf_l is not None and c < last_conf_l * (1 - e) and not dn_state and t - last_dn >= COOL:
            dn_fire = True; dn_state = True; dn_ref = last_conf_l; last_dn = t
        if up_fire or dn_fire:
            events.append({"t": t, "dir": "up" if up_fire else "dn",
                           "ref": up_ref if up_fire else dn_ref,
                           "px": c, "date": df["date"].iloc[t]})
    return events

# ---------------- 主循环 ----------------
rows = []
anom = []
spy_date = spy_reg["date"].values
spy_chop = spy_reg["choppy_day"].values
spy_map = {np.datetime64(d, "D"): c for d, c in zip(spy_date, spy_chop)}
spy_map_a = {np.datetime64(d, "D"): c for d, c in zip(spy_date, spy_reg["choppy_a"].values)}
spy_px = spy_reg.set_index("date")["spy"]

for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 130:
        print(f"skip {t}: no data / too short")
        continue
    df = df.merge(spy_reg[["date", "spy"]], on="date", how="inner")
    if len(df) < 130:
        continue
    if src[t] == "hot50":
        df = df[df["date"] >= "2015-01-01"].reset_index(drop=True)
        if len(df) < 130:
            continue
    df["choppy"] = df["date"].map(lambda d: spy_map.get(np.datetime64(d, "D"), False))
    df["choppy_a"] = df["date"].map(lambda d: spy_map_a.get(np.datetime64(d, "D"), False))
    ret_abs = df["px"].pct_change().abs()
    jumps = set(np.where(ret_abs > 0.40)[0])  # 拆股伪影日（单日跳变>40%）
    if {"high", "low", "close"}.issubset(df.columns):
        pc = df["close"].shift(1)
        tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    else:
        tr = df["px"].diff().abs()
    df["adr_pct"] = tr.rolling(20).mean() / df["px"] * 100
    for K_th in (ZIG_K_MAIN, ZIG_K_ALT):
        ev = detect_events(df, K_th, BRK_E_MAIN)
        for evd in ev:
            ti = evd["t"]
            fwd_ok = ti + FWD[-1] < len(df)
            px0 = evd["px"]
            bad = [j for j in jumps if ti - 1 <= j <= ti + FWD[-1]]
            if bad:
                anom.append({"ticker": t, "date": str(evd["date"]), "dir": evd["dir"], "K": K_th, "fwd20": None})
                continue
            rec = {"t": ti, "ticker": t, "src": src[t], "K": K_th, "date": evd["date"], "dir": evd["dir"],
                   "in_choppy": bool(df["choppy"].iloc[ti]), "in_choppy_a": bool(df["choppy_a"].iloc[ti])}
            for N in FWD:
                rec[f"fwd{N}"] = (df["px"].iloc[ti + N] / px0 - 1) * 100 if ti + N < len(df) else None
                rec[f"spy_fwd{N}"] = (df["spy"].iloc[ti + N] / df["spy"].iloc[ti] - 1) * 100 if ti + N < len(df) else None
            for N in FWD:
                rec[f"ex{N}"] = (rec[f"fwd{N}"] - rec[f"spy_fwd{N}"]) if rec[f"fwd{N}"] is not None else None
            # 假突破：T+10 内价格偏离突破位 ≥1.5×ADR%（用户 09-04 修订口径）
            ref = evd["ref"]
            adr0 = df["adr_pct"].iloc[ti]
            fake = False
            if not np.isnan(adr0):
                th = FAKE_ADR_MULT * adr0
                for j in range(1, FAKE_WIN + 1):
                    if ti + j >= len(df):
                        break
                    c2 = df["px"].iloc[ti + j]
                    dev = (ref - c2) / ref * 100 if evd["dir"] == "up" else (c2 - ref) / ref * 100
                    if dev >= th:
                        fake = True; break
            rec["fake10"] = fake
            # 存活：T+20 内最大不利偏移 < STOP
            worst = 0.0
            for j in range(1, MAE_WIN + 1):
                if ti + j >= len(df):
                    break
                c2 = df["px"].iloc[ti + j]
                dd = (c2 / px0 - 1) * 100 if evd["dir"] == "up" else (px0 / max(c2, 1e-9) - 1) * 100
                worst = min(worst, dd)
            rec["mae20"] = worst
            rec["surv20"] = worst > -STOP
            # 节点
            rec["nodes"] = ";".join(node_windows(evd["date"]))
            rows.append(rec)

ev_df = pd.DataFrame(rows)
ev_df.to_csv(os.path.join(OUT, "choppy_breakout_events.csv"), index=False)
print(f"events total={len(ev_df)}  by K: {ev_df.groupby('K').size().to_dict()}")

# ---------------- C组随机基线 ----------------
rng = np.random.default_rng(42)
base_rows = []
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 200:
        continue
    df = df.merge(spy_reg[["date", "spy"]], on="date", how="inner")
    if src[t] == "hot50":
        df = df[df["date"] >= "2015-01-01"].reset_index(drop=True)
        if len(df) < 200:
            continue
    df["choppy"] = df["date"].map(lambda d: spy_map.get(np.datetime64(d, "D"), False))
    df["choppy_a"] = df["date"].map(lambda d: spy_map_a.get(np.datetime64(d, "D"), False))
    ret_abs = df["px"].pct_change().abs()
    jumps = set(np.where(ret_abs > 0.40)[0])
    ev_days = set(ev_df[(ev_df["ticker"] == t) & (ev_df["K"] == ZIG_K_MAIN)]["t"]) if len(ev_df) else set()
    cand = [i for i in range(130, len(df) - FWD[-1] - 1) if i not in ev_days
            and all((i + a) not in ev_days for a in range(-10, 11))]
    if len(cand) < 50:
        continue
    pick = rng.choice(cand, size=min(N_RANDOM, len(cand)), replace=False)
    for i in pick:
        px0 = df["px"].iloc[i]
        if px0 <= 0:
            continue
        bad = [j for j in jumps if i - 1 <= j <= i + FWD[-1]]
        if bad:
            anom.append({"ticker": t, "date": str(df["date"].iloc[i]), "dir": "base", "K": np.nan, "fwd20": None})
            continue
        fw = {N: (df["px"].iloc[i + N] / px0 - 1) * 100 for N in FWD}
        rec = {"t": i, "ticker": t, "src": src[t], "K": np.nan, "date": df["date"].iloc[i], "dir": "base",
               "in_choppy": bool(df["choppy"].iloc[i]), "in_choppy_a": bool(df["choppy_a"].iloc[i])}
        for N in FWD:
            rec[f"fwd{N}"] = fw[N]
            rec[f"spy_fwd{N}"] = (df["spy"].iloc[i + N] / df["spy"].iloc[i] - 1) * 100
            rec[f"ex{N}"] = rec[f"fwd{N}"] - rec[f"spy_fwd{N}"]
        rec["fake10"] = np.nan; rec["mae20"] = np.nan; rec["surv20"] = np.nan; rec["nodes"] = ""
        base_rows.append(rec)
base_df = pd.DataFrame(base_rows)
base_df.to_csv(os.path.join(OUT, "choppy_breakout_baseline.csv"), index=False)
print(f"baseline n={len(base_df)}")

# ---------------- 汇总统计 ----------------
def tstat(x):
    x = pd.Series(x).dropna()
    if len(x) < 3:
        return np.nan
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))

def summarize(g, label):
    out = {"group": label, "n": len(g)}
    for N in FWD:
        out[f"fwd{N}_mean"] = g[f"fwd{N}"].mean()
        out[f"fwd{N}_med"] = g[f"fwd{N}"].median()
        out[f"fwd{N}_win"] = (g[f"fwd{N}"] > 0).mean() * 100
        out[f"fwd{N}_t"] = tstat(g[f"fwd{N}"])
        out[f"ex{N}_mean"] = g[f"ex{N}"].mean()
        out[f"ex{N}_med"] = g[f"ex{N}"].median()
        out[f"ex{N}_t"] = tstat(g[f"ex{N}"])
    out["fake10"] = g["fake10"].mean() * 100 if g["fake10"].notna().any() else np.nan
    out["surv20"] = g["surv20"].mean() * 100 if g["surv20"].notna().any() else np.nan
    out["mae20_med"] = g["mae20"].median() if g["mae20"].notna().any() else np.nan
    return out

main = ev_df[ev_df["K"] == ZIG_K_MAIN]
summary = []
for dirv in ("up", "dn"):
    for chopv in (True, False):
        g = main[(main["dir"] == dirv) & (main["in_choppy"] == chopv)]
        if len(g):
            summary.append(summarize(g, f"{dirv}_{'choppy' if chopv else 'trend'}"))
        if chopv:
            ga = main[(main["dir"] == dirv) & main["in_choppy_a"]]
            if len(ga):
                summary.append(summarize(ga, f"{dirv}_choppyA_only"))
g = base_df
if len(g):
    summary.append(summarize(g, "baseline_all"))
    summary.append(summarize(g[g["in_choppy"]], "baseline_choppy"))
    summary.append(summarize(g[~g["in_choppy"]], "baseline_trend"))

# 节点分层（主口径 K=5）
node_sum = []
for node in ("sep_oct", "midterm_pre2m", "president_pre2m"):
    g = main[main["nodes"].str.contains(node, na=False)]
    if len(g):
        node_sum.append(summarize(g, f"node_{node}"))
    gb = base_df[base_df["nodes"].str.contains(node, na=False)] if len(base_df) else g
    if len(gb):
        node_sum.append(summarize(gb, f"node_{node}_base"))

json.dump({"summary": summary, "node_summary": node_sum, "anomalies": anom,
           "windows": spy_wins.to_dict("records"),
           "params": {"NECK_TH": NECK_TH, "NECK_PERSIST": NECK_PERSIST, "RSI_PERSIST": RSI_PERSIST,
                      "ZIG_K": [ZIG_K_MAIN, ZIG_K_ALT], "E": [BRK_E_MAIN] + BRK_E_SENS}},
          open(os.path.join(OUT, "choppy_breakout.json"), "w"), ensure_ascii=False, indent=1, default=str)
print("summary groups:", [s["group"] for s in summary])
print(f"anomalies dropped: {len(anom)}")
print("done -> results/choppy_breakout.json")
