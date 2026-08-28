# -*- coding: utf-8 -*-
# 纳指区间(2025-10-01~2026-02-27) 蓝筹池 RSI 低买/高卖 T+5/T+10 最终版（修正 cd10 去重 bug）
# 产出 results/rsi_window_final.json，供重建报告 50
import pandas as pd, numpy as np, os, glob, csv, json

ROOT = r"C:\Users\Administrator\Desktop\stock"
DATA = os.path.join(ROOT, "data")
W0, W1 = "2025-10-01", "2026-02-27"
RENAME = {"MMC": "MRSH"}

tickers, sectors = [], {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t); sectors[t] = row["sector"].strip()

def load_stock(name):
    name = RENAME.get(name, name).lower()
    d = os.path.join(DATA, name)
    if not os.path.isdir(d): return None
    cands = [p for p in glob.glob(os.path.join(d, "*.csv"))
             if not os.path.basename(p).startswith("BATS_") and "1D" in os.path.basename(p)]
    if not cands: return None
    f = sorted(cands)[0]
    df = pd.read_csv(f, parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    return df.dropna(subset=["px"]).sort_values("date").reset_index(drop=True)

def rsi_wilder(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/period, adjust=False).mean()
    al = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = ag / al
    return 100 - 100/(1+rs)

def tstat(s, base_mean=None):
    s = np.asarray(s, dtype=float)
    n = len(s)
    if n == 0: return None
    m, med = s.mean(), np.median(s)
    win = (s > 0).mean()
    sd = s.std(ddof=1) if n > 1 else 0.0
    t = m / (sd/np.sqrt(n)) if sd > 0 else 0.0
    # 双尾 p（t 分布渐近正态）
    from math import erf
    p_t = 2*(1-0.5*(1+erf(abs(t)/np.sqrt(2))))
    # 二项胜率 p (vs 0.5)
    z = (win-0.5)/np.sqrt(0.25/n) if n > 1 else 0.0
    p_bin = 2*(1-0.5*(1+erf(abs(z)/np.sqrt(2))))
    # 与基准差的 Welch t
    ex = None; t_w = None; p_w = None
    if base_mean is not None:
        ex = m - base_mean
        v2 = np.var(s, ddof=1)/n if n > 1 else 0.0
        se = np.sqrt(v2)  # 基率 n 极大，视作常数
        t_w = ex/se if se > 0 else 0.0
        p_w = 2*(1-0.5*(1+erf(abs(t_w)/np.sqrt(2))))
    def sig(p):
        if p is None: return "no"
        if p < 0.01: return "sig"
        if p < 0.05: return "edge"
        return "no"
    return dict(n=n, mean=round(m*100,2), med=round(med*100,2), win=round(win*100,1),
                p25=round(np.percentile(s,25)*100,2), p75=round(np.percentile(s,75)*100,2),
                t=round(t,2), p=round(p_t,4), p_bin=round(p_bin,4),
                ex=round(ex*100,2) if ex is not None else None,
                t_w=round(t_w,2) if t_w is not None else None,
                p_w=round(p_w,4) if p_w is not None else None,
                sig=sig(p_t), sig_w=sig(p_w))

# ---------- 加载 + RSI + fwd ----------
frames = {}
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 260: continue
    df["rsi"] = rsi_wilder(df["px"])
    for N in (5, 10):
        df[f"fwd{N}"] = df["px"].shift(-N)/df["px"] - 1
    frames[t] = df
print("加载", len(frames), "只")

# 基准：窗口内全交易日 fwd5/fwd10
bs5, bs10 = [], []
for t, df in frames.items():
    w = df[(df["date"] >= W0) & (df["date"] <= W1)]
    bs5.append(w["fwd5"].dropna()); bs10.append(w["fwd10"].dropna())
b5 = pd.concat(bs5).values; b10 = pd.concat(bs10).values
bench = {"fwd5": tstat(b5), "fwd10": tstat(b10),
         "n_days": int(frames[tickers[0]][(frames[tickers[0]]["date"] >= W0) & (frames[tickers[0]]["date"] <= W1)].shape[0])}

# SPY/QQQ 区间收益
for ref, tag in [("SPY","spy"), ("QQQ","qqq")]:
    df = load_stock(ref)
    if df is None: continue
    w = df[(df["date"] >= W0) & (df["date"] <= W1)]
    bench[tag] = round((w["px"].iloc[-1]/w["px"].iloc[0]-1)*100, 2)

# ---------- 信号事件 ----------
SIG = {
    "L30": ("low", 30), "L35": ("low", 35), "L40": ("low", 40),
    "H60": ("high", 60), "H65": ("high", 65), "H70": ("high", 70),
}
events = {k: [] for k in SIG}
for t, df in frames.items():
    prev = df["rsi"].shift(1)
    w = df[(df["date"] >= W0) & (df["date"] <= W1)].copy()
    w["prev"] = prev.reindex(w.index)
    for k, (drc, thr) in SIG.items():
        if drc == "low":
            m = (w["rsi"] < thr) & (w["prev"] >= thr) & w["prev"].notna()
        else:
            m = (w["rsi"] > thr) & (w["prev"] <= thr) & w["prev"].notna()
        for _, r in w[m].iterrows():
            events[k].append(dict(ticker=t, sector=sectors[t], date=str(r["date"].date()),
                                  idx=int(r.name), rsi=round(float(r["rsi"]),1),
                                  fwd5=float(r["fwd5"]) if not pd.isna(r["fwd5"]) else None,
                                  fwd10=float(r["fwd10"]) if not pd.isna(r["fwd10"]) else None))

def cd10_filter(evs):
    """正确 cd10：同 ticker 相邻信号 idx 间隔 >=10 交易日取首"""
    keep = []
    for t, g in pd.DataFrame(evs).groupby("ticker"):
        g = g.sort_values("idx")
        last = -10**9
        for _, r in g.iterrows():
            if r["idx"] - last >= 10:
                keep.append(r.to_dict()); last = r["idx"]
    return keep

def build(k, base):
    raw = events[k]
    cd = cd10_filter(raw)
    out = {"raw": tstat([e["fwd5"] for e in raw if e["fwd5"] is not None], base), }  # placeholder
    # 分别算 fwd5 / fwd10
    out["fwd5"] = {"all": tstat([e["fwd5"] for e in raw if e["fwd5"] is not None], b5.mean()),
                   "cd10": tstat([e["fwd5"] for e in cd if e["fwd5"] is not None], b5.mean())}
    out["fwd10"] = {"all": tstat([e["fwd10"] for e in raw if e["fwd10"] is not None], b10.mean()),
                    "cd10": tstat([e["fwd10"] for e in cd if e["fwd10"] is not None], b10.mean())}
    out["n_raw"] = len(raw); out["n_cd10"] = len(cd)
    out["n_tickers_raw"] = len(set(e["ticker"] for e in raw))
    out["n_days_raw"] = len(set(e["date"] for e in raw))
    out["events_cd10"] = cd
    # 按日聚簇（每日等权 1 样本，消除同日挤单）
    day = pd.DataFrame(cd)
    if len(day):
        d5 = day.dropna(subset=["fwd5"]).groupby("date")["fwd5"].mean()
        d10 = day.dropna(subset=["fwd10"]).groupby("date")["fwd10"].mean()
        out["fwd5"]["by_day"] = tstat(d5.values, b5.mean())
        out["fwd10"]["by_day"] = tstat(d10.values, b10.mean())
    return out

res = {"bench": bench, "signals": {}}
for k in SIG:
    res["signals"][k] = build(k, None)

# ---------- 配对循环：下穿30买 → 上穿70卖（cd10 口径） ----------
pairs = []
for t, df in frames.items():
    prev = df["rsi"].shift(1)
    w = df[(df["date"] >= W0) & (df["date"] <= W1)].copy()
    w["prev"] = prev.reindex(w.index)
    w = w.reset_index(drop=True)
    buys = list(w.index[(w["rsi"] < 30) & (w["prev"] >= 30) & w["prev"].notna()])
    i = 0
    while i < len(buys):
        b = buys[i]
        # 找之后的第一次上穿70
        sell = None
        for j in range(b+1, len(w)):
            if w["rsi"].iloc[j] > 70 and (j == 0 or w["rsi"].iloc[j-1] <= 70):
                sell = j; break
        if sell is not None:
            ret = (w["px"].iloc[sell]/w["px"].iloc[b]-1)*100
            pairs.append({"ticker": t, "type": "closed", "buy": str(w["date"].iloc[b].date()),
                          "sell": str(w["date"].iloc[sell].date()), "hold": int(sell-b),
                          "ret": round(float(ret), 2)})
            i += 1
        else:
            # 未平仓：区间末
            ret = (w["px"].iloc[-1]/w["px"].iloc[b]-1)*100
            pairs.append({"ticker": t, "type": "open", "buy": str(w["date"].iloc[b].date()),
                          "sell": f"{W1}(区间末)", "hold": int(len(w)-1-b),
                          "ret": round(float(ret), 2)})
            i += 1
closed = [p for p in pairs if p["type"] == "closed"]
opened = [p for p in pairs if p["type"] == "open"]
res["pairs"] = {
    "closed": tstat([p["ret"]/100 for p in closed]),
    "open": tstat([p["ret"]/100 for p in opened]),
    "closed_n": len(closed), "open_n": len(opened),
    "closed_detail": closed, "open_detail": opened,
    "closed_avg_hold": round(np.mean([p["hold"] for p in closed]),1) if closed else None,
}

# ---------- 行业拆解（L30 / H70 cd10 T+10） ----------
sec = {}
for k in ["L30", "L35", "H65", "H70"]:
    cd = res["signals"][k]["events_cd10"]
    by = {}
    for e in cd:
        if e["fwd10"] is None: continue
        by.setdefault(e["sector"], []).append(e["fwd10"])
    rows = []
    for s, arr in by.items():
        if len(arr) < 3: continue
        st = tstat(arr, b10.mean())
        rows.append(dict(sector=s, **{kk: st[kk] for kk in ["n","mean","med","win","ex","sig_w"]}))
    rows.sort(key=lambda r: -r.get("mean") or 0)
    sec[k] = rows
res["sector"] = sec

with open(os.path.join(ROOT, "results", "rsi_window_final.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("written:", os.path.join(ROOT, "results", "rsi_window_final.json"), os.path.getsize(os.path.join(ROOT, "results", "rsi_window_final.json")), "bytes")

def p(s): 
    if not s: return "n=0"
    ex = f" 超额{s['ex']:+.2f}pp[{s['sig_w']}]" if s.get("ex") is not None else ""
    return f"n={s['n']} {s['mean']:+.2f}% med={s['med']:+.2f}% win={s['win']}% t={s['t']} p={s['p']} sig={s['sig']}{ex}"
print("\n=== 基准 ===")
print("T5:", p(bench["fwd5"])); print("T10:", p(bench["fwd10"]))
print("SPY", bench["spy"], "QQQ", bench["qqq"])
for k in SIG:
    s = res["signals"][k]
    print(f"\n[{k}] raw n={s['n_raw']} cd10 n={s['n_cd10']} ({s['n_tickers_raw']}票/{s['n_days_raw']}日)")
    print("  T5 all:", p(s["fwd5"]["all"]), "| cd10:", p(s["fwd5"]["cd10"]))
    print("  T10 all:", p(s["fwd10"]["all"]), "| cd10:", p(s["fwd10"]["cd10"]))
    if "by_day" in s["fwd10"]: print("  T10 cd10 by_day:", p(s["fwd10"]["by_day"]))
print("\n=== 配对循环（下穿30买→上穿70卖） ===")
print("closed:", p(res["pairs"]["closed"]), "avg_hold", res["pairs"]["closed_avg_hold"], "日")
print("open:", p(res["pairs"]["open"]))