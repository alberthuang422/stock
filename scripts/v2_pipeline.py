# -*- coding: utf-8 -*-
"""Step 2-6 主管线：事件提取 → 阶梯 → 稳健性 → 回归 → fade 回测。
依赖 v2_choppy_breakout.py 的函数与 CONFIG。产出全部 CSV 到 results/70_v2/。
用法：python v2_pipeline.py [earnings_csv]"""
import sys, os, json
import numpy as np
import pandas as pd
sys.path.insert(0, r"C:\Users\Administrator\Desktop\stock\scripts")
from v2_choppy_breakout import (CONFIG, load_ohlc, load_spy, choppy_detector,
                                adx_wilder, atr14, adr20, choppy_runs)

OUT = CONFIG["out_dir"]
cfg = CONFIG

# ---------------- Step 2: 事件提取（向量化冷却/财报过滤） ----------------
def extract_events_fast(df, ticker, sector, ch_map, earn_idx, fwd_window=10):
    """口径 C 55日新高/新低。df 含 atr/adr 列（已防泄漏）。earn_idx: 财报日所在行号集合"""
    L = cfg["donchian_len"]; n = len(df)
    c = df["adj_close"].values
    atr = df["atr"].values; adr = df["adr"].values
    o_raw = df["open"].values; cl_raw = df["close"].values
    adj_ratio = df["adj_close"].values / df["close"].values
    tvol = (df["adj_close"] * df["volume"]).rolling(20).mean().values
    dates = df["date"].values
    # 滚动窗口最大/最小（不含当日）：用 shift
    s = pd.Series(c)
    roll_hi = s.rolling(L).max().shift(1).values       # i-L..i-1
    roll_lo = s.rolling(L).min().shift(1).values
    prev_hi = s.shift(1).rolling(L).max().shift(1).values  # i-L-1..i-2
    prev_lo = s.shift(1).rolling(L).min().shift(1).values
    # 当日创 55 日新高 & 昨收未创（昨收的 55 日窗口 = c[i-56..i-2] = prev_hi）
    up_new = (c > roll_hi) & (s.shift(1).values <= prev_hi)
    dn_new = (c < roll_lo) & (s.shift(1).values >= prev_lo)
    # 跳变过滤（复权后不应有，双保险用原始价）
    jump = np.zeros(n, bool)
    r1 = np.abs(cl_raw[1:] / cl_raw[:-1] - 1)
    jump[1:] = r1 > cfg["jump_filter"]
    valid = (np.arange(n) > L) & (np.arange(n) < n - fwd_window)
    valid &= ~jump & np.isfinite(atr) & (atr > 0) & np.isfinite(adr) & (adr > 0)
    valid &= np.isfinite(tvol) & (tvol > cfg["min_turnover_usd"])
    valid &= np.isfinite(roll_hi) & np.isfinite(roll_lo)
    direction = np.where(up_new & valid, 1, np.where(dn_new & valid, -1, 0))
    idxs = np.where(direction != 0)[0]
    events = []
    for i in idxs:
        d = int(direction[i])
        ref = roll_hi[i] if d == 1 else roll_lo[i]
        brk = abs(c[i] - ref) / atr[i]
        if brk < cfg["min_break_atr"]: continue
        adj_o = o_raw[i] * adj_ratio[i]
        gap_skip = (adj_o > ref + cfg["gap_skip_atr"]*atr[i]) if d == 1 else (adj_o < ref - cfg["gap_skip_atr"]*atr[i])
        fwd = c[i+1:i+1+fwd_window]
        # 最大反向偏离（交接文档 3.3）：向上突破 dev_max = max_j (ref - close_j)/ref；
        # 未触回时 max 为负（负值 = 突破后最接近 ref 的顺向距离），k=0 档 P(dev≥0)=触回率。
        dev_max = ((ref - fwd).max()/ref) if d == 1 else ((fwd - ref).max()/ref)
        ev = dict(ticker=ticker, sector=sector, date=pd.Timestamp(dates[i]), dir="up" if d==1 else "down",
                  ref=ref, close=c[i], atr=atr[i], adr=adr[i], brk_atr=brk, gap_skip=bool(gap_skip),
                  choppy=int(ch_map.get(pd.Timestamp(dates[i]), 0)), idx=i, dev_max=dev_max,
                  dev_adr=dev_max / (adr[i]/100.0))
        for N in (5, 10, 20):
            ev[f"fwd{N}"] = (c[i+1+N]/c[i]-1)*100 if i+1+N < n else np.nan
        events.append(ev)
    if not events: return pd.DataFrame()
    ev = pd.DataFrame(events)
    # 冷却期（同方向 ≥20 交易日；严格按事件表顺序）
    keep, last = [], {"up": -10**9, "down": -10**9}
    for idx, d in zip(ev["idx"], ev["dir"]):
        if idx - last[d] >= cfg["cooldown"]:
            keep.append(True); last[d] = idx
        else: keep.append(False)
    ev = ev[keep].reset_index(drop=True)
    # 财报 ±1 交易日
    if earn_idx:
        bad = set()
        for j in earn_idx:
            for off in range(-cfg["earnings_window"], cfg["earnings_window"]+1):
                bad.add(j+off)
        ev = ev[~ev["idx"].isin(bad)].reset_index(drop=True)
    return ev

def build_all_events(ch, earn_map, variant_ch=None):
    ch_map = ch.set_index("date")["choppy"]
    bc = pd.read_csv(os.path.join(cfg["data_dir"], cfg["blue_chips"]), encoding="utf-8-sig")
    bc["ticker"] = bc["ticker"].str.strip().str.lower(); bc["sector"] = bc["sector"].str.strip()
    all_ev = []
    for _, r in bc.iterrows():
        t = r["ticker"]
        df = load_ohlc(t)
        if df is None: continue
        df = df[df["date"] >= pd.Timestamp(cfg["start_date"])].reset_index(drop=True)
        if len(df) < cfg["donchian_len"] + cfg["fwd_window"] + cfg["adr_len"] + 50:
            continue
        df["atr"] = atr14(df[["high","low","close"]].assign(high=df["high"], low=df["low"], close=df["close"]))
        df["atr"] = atr14(df)
        df["adr"] = adr20(df)
        earn_idx = set()
        if earn_map is not None and t in earn_map.groups:
            edates = earn_map.get_group(t)["date"]
            d2i = {d.date(): i for i, d in enumerate(df["date"])}
            for ed in edates:
                e = pd.Timestamp(ed).date()
                if e in d2i: earn_idx.add(d2i[e])
        ev = extract_events_fast(df, t, r["sector"], ch_map, earn_idx)
        all_ev.append(ev)
    return pd.concat(all_ev, ignore_index=True) if all_ev else pd.DataFrame()

# ---------------- Step 3: 阶梯 + 主对照 ----------------
def ladder_table(ev):
    ks = cfg["ladder_ks"]
    rows = []
    for (chop, dr), g in ev.groupby(["choppy", "dir"]):
        dev = g["dev_adr"].values
        for k in ks:
            rows.append(dict(choppy=chop, dir=dr, k=k, n=len(dev),
                             rate=float((dev >= k).mean())))
    lad = pd.DataFrame(rows)
    piv = lad.pivot_table(index=["k","dir"], columns="choppy", values=["rate","n"])
    return lad

def rate_diff_ci(ev, k, n_boot=None, seed=None):
    """震荡-趋势 率差 + 95% CI（按震荡窗口聚类的 block bootstrap：
    以事件日所在连续震荡/趋势段的段 id 为重抽样单元，段内事件整体抽）"""
    n_boot = n_boot or cfg["n_boot"]; seed = seed or cfg["boot_seed"]
    g1 = ev[(ev["choppy"]==1)]["dev_adr"] >= k   # 注意：choppy=1 是"突破日当天为震荡日"
    g0 = ev[(ev["choppy"]==0)]["dev_adr"] >= k
    x1, x0 = g1.values.astype(float), g0.values.astype(float)
    obs = x1.mean() - x0.mean()
    rng = np.random.default_rng(seed)
    # block：以 60 日历日为块长（用天数差，避免 datetime64[us]/[ns] 单位歧义）
    def blocks(dates):
        days = np.asarray((pd.to_datetime(dates) - pd.Timestamp("2010-01-01")) / pd.Timedelta(days=1))
        return (days // cfg["cluster_len"]).astype(int)
    d1 = ev[(ev["choppy"]==1)]["date"].values; d0 = ev[(ev["choppy"]==0)]["date"].values
    b1 = blocks(d1); b0 = blocks(d0)
    ub1 = np.unique(b1); ub0 = np.unique(b0)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        # 重抽块（保持各块内事件）
        pb1 = rng.choice(ub1, len(ub1), replace=True)
        pb0 = rng.choice(ub0, len(ub0), replace=True)
        s1 = np.concatenate([x1[b1==b] for b in pb1]) if len(ub1) else x1
        s0 = np.concatenate([x0[b0==b] for b in pb0]) if len(ub0) else x0
        diffs[i] = (s1.mean() if len(s1) else 0) - (s0.mean() if len(s0) else 0)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return obs, lo, hi

def fisher_test(ev, k):
    from scipy.stats import fisher_exact
    a = ((ev["choppy"]==1) & (ev["dev_adr"]>=k)).sum(); b = ((ev["choppy"]==1) & (ev["dev_adr"]<k)).sum()
    c_ = ((ev["choppy"]==0) & (ev["dev_adr"]>=k)).sum(); d_ = ((ev["choppy"]==0) & (ev["dev_adr"]<k)).sum()
    odds, p = fisher_exact([[a,b],[c_,d_]])
    return dict(k=k, a=int(a), b=int(b), c=int(c_), d=int(d_), odds=float(odds), p=float(p))

def bh_adjust(pvals):
    p = np.asarray(pvals); n = len(p)
    order = np.argsort(p); ranked = p[order]
    q = ranked * n / (np.arange(n)+1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n); out[order] = np.clip(q, 0, 1)
    return out

# ---------------- Step 6: fade 回测 ----------------
def fade_backtest(ev_all):
    """入场=突破后 T+5 内收盘回踩突破位；做空(向上突破)/做多(向下破位)。
    止损=收盘重新越过 ref±0.5ATR；目标=ref∓1.5ATR；T+20 强平。逐笔记录。"""
    trades = []
    bc_cache = {}
    for _, e in ev_all.iterrows():
        t = e["ticker"]
        if t not in bc_cache:
            df = load_ohlc(t)
            df = df[df["date"] >= pd.Timestamp(cfg["start_date"])].reset_index(drop=True)
            bc_cache[t] = df
        df = bc_cache[t]
        i = int(e["idx"]); n = len(df)
        c = df["adj_close"].values
        a = e["atr"]; ref = e["ref"]; d = e["dir"]
        entry, entry_i, hit = None, None, False
        for j in range(i+1, min(i+1+cfg["fade_entry_win"], n)):
            if d == "up" and c[j] <= ref:
                entry, entry_i, hit = c[j], j, True; break
            if d == "down" and c[j] >= ref:
                entry, entry_i, hit = c[j], j, True; break
        if not hit: continue
        stop = ref + cfg["fade_stop_atr"]*a if d == "up" else ref - cfg["fade_stop_atr"]*a
        target = ref - cfg["fade_target_atr"]*a if d == "up" else ref + cfg["fade_target_atr"]*a
        exit_px, exit_i, reason = None, None, None
        for j in range(entry_i, min(entry_i+cfg["fade_max_hold"]+1, n)):
            cj = c[j]
            if d == "up":
                if cj >= stop: exit_px, exit_i, reason = cj, j, "stop"; break
                if cj <= target: exit_px, exit_i, reason = cj, j, "target"; break
            else:
                if cj <= stop: exit_px, exit_i, reason = cj, j, "stop"; break
                if cj >= target: exit_px, exit_i, reason = cj, j, "target"; break
        if exit_px is None:
            j = min(entry_i+cfg["fade_max_hold"], n-1)
            exit_px, exit_i, reason = c[j], j, "timeout"
        pnl_pct = (entry-exit_px)/entry*100 if d == "up" else (exit_px-entry)/entry*100
        pnl_atr = (entry-exit_px)/a if d == "up" else (exit_px-entry)/a
        trades.append(dict(ticker=t, sector=e["sector"], dir=d, break_date=e["date"],
                           entry_date=df["date"].iloc[entry_i], exit_date=df["date"].iloc[exit_i],
                           hold=exit_i-entry_i, entry=entry, exit=exit_px, ref=ref, atr=a,
                           pnl_pct=pnl_pct, pnl_atr=pnl_atr, reason=reason,
                           choppy=int(e["choppy"])))
    return pd.DataFrame(trades)

def fuzzy_edge_mask(ev, ch):
    """震荡窗首尾 5 日模糊带标记（不改变事件，仅打标）"""
    runs = choppy_runs(ch)
    dates = ch["date"].values
    edge_dates = set()
    for s, e_ in runs:
        for k in range(cfg["fuzzy_edge"]):
            for idx in (s-1-k, s, s+1+k, e_-1-k, e_, e_+1+k):
                if 0 <= idx < len(dates): edge_dates.add(dates[idx])
    ev = ev.copy()
    ev["fuzzy"] = ev["date"].isin(pd.to_datetime(list(edge_dates)))
    return ev

# ---------------- 主流程 ----------------
def main():
    earn_csv = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "earnings_all.csv")
    spy = load_spy()
    ch = choppy_detector(spy)
    ch.to_csv(os.path.join(OUT, "spy_choppy_main.csv"), index=False)
    earn_map = None
    if os.path.exists(earn_csv):
        edf = pd.read_csv(earn_csv); edf["date"] = pd.to_datetime(edf["date"])
        earn_map = edf.groupby("ticker")
        print(f"earnings loaded: {len(edf)} rows")
    else:
        print("WARN: no earnings csv → 财报过滤不生效")
    print("Step2 提取事件...")
    ev = build_all_events(ch, earn_map)
    ev.to_csv(os.path.join(OUT, "events.csv"), index=False)
    print(f"events={len(ev)} up={int((ev['dir']=='up').sum())} down={int((ev['dir']=='down').sum())} "
          f"gap_skip={int(ev['gap_skip'].sum())} 上下比 1:{(ev['dir']=='down').sum()/(ev['dir']=='up').sum():.2f}")
    # 主统计排除 gap_skip
    evm = ev[~ev["gap_skip"]].copy()
    print("Step3 阶梯...")
    lad = ladder_table(evm)
    lad.to_csv(os.path.join(OUT, "ladder.csv"), index=False)
    # 率差 CI
    rows = []
    for k in cfg["ladder_ks"]:
        for dr in ("up","down"):
            sub = evm[evm["dir"]==dr]
            obs, lo, hi = rate_diff_ci(sub, k)
            rows.append(dict(dir=dr, k=k, diff=obs, lo=lo, hi=hi))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "ladder_diff_ci.csv"), index=False)
    # Fisher @主阈值+备选
    fr = []
    for dr in ("up","down"):
        for k in [1.0, 0.5, 1.5]:
            fr.append(dict(dir=dr, **fisher_test(evm[evm["dir"]==dr], k)))
    fdf = pd.DataFrame(fr)
    fdf["p_bh"] = bh_adjust(fdf["p"].values)
    fdf.to_csv(os.path.join(OUT, "fisher_tests.csv"), index=False)
    print("ladder diff(1.0):", fdf[fdf["k"]==1.0][["dir","odds","p","p_bh"]].to_string(index=False))
    print("Step6 fade 回测...")
    tr = fade_backtest(evm)
    tr.to_csv(os.path.join(OUT, "strategy_trades.csv"), index=False)
    print(f"trades={len(tr)}")
    print("up pnl mean/trades:", tr[tr["dir"]=="up"]["pnl_pct"].agg(["mean","count"]).to_dict())
    print("down pnl mean/trades:", tr[tr["dir"]=="down"]["pnl_pct"].agg(["mean","count"]).to_dict())
    return ev, tr

if __name__ == "__main__":
    main()
