# -*- coding: utf-8 -*-
"""
ABBV / GILD 周线 MACD 柱负转正周 → 周内 4h RSI 超买 → 后续调整深度研究
核心问题：周线 MACD 能量柱在 0 轴上方刚刚转正的那一周，
          该周 4 小时级别大概率出现一次超买(RSI>70)，超买之后如何调整？调整深度大吗？

数据：
- 4h: 腾讯 CSV（BATS_*.csv），含 OHLCV + RSI + MACD/Histogram/Signal line 列（腾讯 MACD 口径 12/26/9）
- 周线: Yahoo adj_close (1wk)
"""
import pandas as pd
import numpy as np
import json
import os
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)

# ---------------- 工具 ----------------
def load_tencent_240(ticker):
    p = os.path.join(os.path.dirname(__file__), "..", "data", ticker, f"{ticker}_240_tencent.csv")
    df = pd.read_csv(p)
    # 腾讯 CSV 列：time,open,high,low,close,RSI,RSI-based MA,Regular Bullish,...,EMA,EMA,Volume,Histogram,MACD,Signal line
    # 重命名为标准列
    df = df.rename(columns={
        "time": "time",
        "open": "open", "high": "high", "low": "low", "close": "close",
        "Volume": "volume",
        "Histogram": "hist",
        "MACD": "dif",
        "Signal line": "dea",
    })
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    return df

def macd_12_26_9(close):
    """标准 MACD(12,26,9)：返回 DIF, DEA, HIST"""
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    hist = 2 * (dif - dea)
    return dif, dea, hist

# ---------------- 加载数据 ----------------
TICKERS = ["abbv", "gild"]
dfs = {}
for tk in TICKERS:
    d = load_tencent_240(tk)
    # 重算标准 MACD 校验腾讯列口径
    st_dif, st_dea, st_hist = macd_12_26_9(d["close"])
    # 腾讯 hist 与标准 hist 相关度
    c_hist = np.corrcoef(d["hist"].dropna(), st_hist.dropna())[0, 1]
    c_dif = np.corrcoef(d["dif"].dropna(), st_dif.dropna())[0, 1]
    dfs[tk] = d
    print(f"[{tk}] rows={len(d)}  {d['time'].iloc[0]} ~ {d['time'].iloc[-1]}")
    print(f"   腾讯hist vs 标准MACD hist 相关: {c_hist:.4f}   dif 相关: {c_dif:.4f}")

# ---------------- 对齐：4h bar → ISO 周 ----------------
def add_week_col(df):
    # 腾讯 time 是北京时间(+08:00)，取它所在 ISO 周
    df = df.copy()
    df["date"] = df["time"].dt.date
    # ISO 周编号（周一为一周开始）
    iso = pd.to_datetime(df["date"])
    df["iso_year"] = iso.dt.isocalendar().year
    df["iso_week"] = iso.dt.isocalendar().week
    return df

for tk in TICKERS:
    dfs[tk] = add_week_col(dfs[tk])

# ---------------- 周线数据 ----------------
weekly = {}
for tk in TICKERS:
    p = os.path.join(os.path.dirname(__file__), "..", "data", tk, f"{tk.upper()}, 1W.csv")
    w = pd.read_csv(p, parse_dates=["date"])
    w = w.sort_values("date").reset_index(drop=True)
    # 复权因子近似：adj_close / close 假设期内大体恒定，直接用 adj_close 价格
    weekly[tk] = w

# 周线 MACD
for tk in TICKERS:
    w = weekly[tk]
    w["dif"], w["dea"], w["hist"] = macd_12_26_9(w["adj_close"])
    # 周线 ISO 周
    iso = pd.to_datetime(w["date"])
    w["iso_year"] = iso.dt.isocalendar().year
    w["iso_week"] = iso.dt.isocalendar().week
    w["week_key"] = w["iso_year"].astype(str) + "-" + w["iso_week"].astype(str).str.zfill(2)
    weekly[tk] = w

# ---------------- 事件：周线 hist 负转正（hist<0 → hist>=0）周 ----------------
events = []
for tk in TICKERS:
    w = weekly[tk]
    for i in range(1, len(w)):
        prev_hist = w.loc[i - 1, "hist"]
        cur_hist = w.loc[i, "hist"]
        if np.isnan(prev_hist) or np.isnan(cur_hist):
            continue
        if prev_hist < 0 and cur_hist >= 0:
            events.append({
                "ticker": tk,
                "week_key": w.loc[i, "week_key"],
                "week_start": w.loc[i, "date"].strftime("%Y-%m-%d"),
                "prev_hist": prev_hist,
                "cur_hist": cur_hist,
            })

ev_df = pd.DataFrame(events)
print(f"\n周线MACD柱负转正事件总数: {len(ev_df)}  (abbv={len(ev_df[ev_df.ticker=='abbv'])}, gild={len(ev_df[ev_df.ticker=='gild'])})")

# 合并同花顺/腾讯 4h 数据按 week_key 对齐
# ---------------- 事件周内 4h 超买检测 ----------------
def rsi_14(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = ag / al
    return 100 - 100 / (1 + rs)

OB = 70  # RSI 超买线
for tk in TICKERS:
    d = dfs[tk]
    d["rsi14"] = rsi_14(d["close"])
    # 腾讯自带 RSI 列验证
    if "RSI" in d.columns:
        both = pd.concat([d["RSI"], d["rsi14"]], axis=1).dropna()
        c_rsi = np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1] if len(both) > 2 else np.nan
    else:
        c_rsi = np.nan
    print(f"[{tk}] 腾讯RSI vs 标准RSI14 相关: {c_rsi:.4f}")

    key = tk
    dfs[tk] = d

# 事件周内超买检测：事件周 week_key 内，4h RSI14 首次 >=70 的位置
ev_records = []
for _, ev in ev_df.iterrows():
    tk = ev["ticker"]
    wk = ev["week_key"]
    d = dfs[tk]
    mask = (d["iso_year"].astype(str) + "-" + d["iso_week"].astype(str).str.zfill(2)) == wk
    week_bars = d[mask]
    if len(week_bars) == 0:
        ev_records.append({**ev.to_dict(), "in_week_ob": None, "n_week_bars": 0})
        continue
    ob_mask = week_bars["rsi14"] >= OB
    n_ob = int(ob_mask.sum())
    # 首次超买位置
    first_t = None
    first_close = None
    if n_ob > 0:
        fb = week_bars[ob_mask].iloc[0]
        first_t = fb["time"]
        first_close = fb["close"]
    ev_records.append({
        **ev.to_dict(),
        "in_week_ob": n_ob > 0,
        "n_ob": n_ob,
        "first_ob_time": first_t,
        "first_ob_close": first_close,
    })

ev_ob = pd.DataFrame(ev_records)
ev_ob["week_has_ob"] = ev_ob["in_week_ob"].fillna(False) == True
print(f"\n事件周内含4h超买(RSI>=70): {ev_ob['week_has_ob'].sum()} / {len(ev_ob)}  ({ev_ob['week_has_ob'].mean()*100:.1f}%)")
print(f"  abbv: {(ev_ob[ev_ob.ticker=='abbv']['week_has_ob']).sum()} / {len(ev_ob[ev_ob.ticker=='abbv'])}")
print(f"  gild: {(ev_ob[ev_ob.ticker=='gild']['week_has_ob']).sum()} / {len(ev_ob[ev_ob.ticker=='gild'])}")

# 对照：非事件周（周线 hist 未负转正，且hist>=0 的区域——常态周）含超买的比例
ctrl_records = []
for tk in TICKERS:
    w = weekly[tk]
    d = dfs[tk]
    d["week_key"] = d["iso_year"].astype(str) + "-" + d["iso_week"].astype(str).str.zfill(2)
    ev_weeks = set(ev_df[ev_df.ticker == tk]["week_key"])
    # 对照组 = hist 周线 >=0 且不是转正周的周（常态强势周）
    for _, wrow in w.iterrows():
        if wrow["hist"] < 0 or np.isnan(wrow["hist"]):
            continue
        if wrow["week_key"] in ev_weeks:
            continue
        mask = d["week_key"] == wrow["week_key"]
        bars = d[mask]
        if len(bars) == 0:
            continue
        ob = int((bars["rsi14"] >= OB).sum())
        ctrl_records.append({
            "ticker": tk, "week_key": wrow["week_key"],
            "week_start": wrow["date"].strftime("%Y-%m-%d"),
            "n_bars": len(bars), "n_ob": ob, "has_ob": ob > 0,
        })
ctrl = pd.DataFrame(ctrl_records)
print(f"\n对照(强势周, hist>=0非转正): 总周数 {len(ctrl)}, 含超买周 {ctrl['has_ob'].sum()} ({(ctrl['has_ob'].mean()*100):.1f}%)")
print(f"  事件周 vs 对照周含超买率: {ev_ob['week_has_ob'].mean()*100:.1f}% vs {ctrl['has_ob'].mean()*100:.1f}%")

# ---------------- 核心：超买后的调整 ----------------
# t0 = 周内首次超买 bar；统计 t0 后 H 根 4h bar 的表现
HORIZONS = [3, 5, 10, 20, 40]

def forward_stats(d, t0_idx, horiz):
    """从 t0_idx 起的调整统计。返回 dict 或 None（数据不足）"""
    close = d["close"]
    high = d["high"]
    low = d["low"]
    max_idx = len(d) - 1
    if t0_idx + horiz > max_idx:
        return None
    t0_close = close.iloc[t0_idx]
    seg_low = low.iloc[t0_idx + 1: t0_idx + horiz + 1].min()  # 不含t0本身
    seg_high = high.iloc[t0_idx + 1: t0_idx + horiz + 1].max()
    end_close = close.iloc[t0_idx + horiz]
    max_drawdown = (seg_low / t0_close - 1) * 100
    max_runup = (seg_high / t0_close - 1) * 100
    fwd_ret = (end_close / t0_close - 1) * 100
    return {
        "max_dd": max_drawdown,        # 最大回撤 %
        "max_runup": max_runup,        # 最大冲高 %
        "fwd_ret": fwd_ret,            # H 根后收益 %
    }

# 触底时间/恢复时间（以 40 根为观察窗）
def timing_stats(d, t0_idx, window=40):
    """返回 (触底所需bar数, 回到t0close所需bar数, window内是否有新高)"""
    max_idx = len(d) - 1
    end = min(t0_idx + window, max_idx)
    closes = d["close"]
    t0_close = closes.iloc[t0_idx]
    seg = slice(t0_idx + 1, end + 1)
    seg_low = d["low"].iloc[seg]
    seg_high = d["high"].iloc[seg]
    bottom_pos = seg_low.idxmin()  # 需要原始位置
    # idxmin 返回 label
    low_pos = seg_low.values.argmin()
    bars_to_bottom = low_pos + 1  # 第几根触及最低
    # 回到 t0 close：最早收盘 >= t0_close
    rec = None
    for j, v in enumerate(closes.iloc[seg].values):
        if v >= t0_close:
            rec = j + 1
            break
    # 新高：close 创新高（> t0 之前20根最高close）
    ref_high = d["high"].iloc[max(0, t0_idx - 20): t0_idx + 1].max()
    new_high = False
    nh_idx = None
    for j in range(t0_idx + 1, end + 1):
        if d["high"].iloc[j] > ref_high:
            new_high = True
            nh_idx = j - t0_idx
            break
    return bars_to_bottom, rec, new_high, nh_idx

# 计算每个事件的首个超买点后续表现
obs = []
for _, ev in ev_ob.iterrows():
    tk = ev["ticker"]
    if pd.isna(ev["first_ob_time"]):
        continue
    d = dfs[tk]
    t0_idx = d.index[d["time"] == ev["first_ob_time"]].tolist()
    if not t0_idx:
        continue
    t0_idx = t0_idx[0]
    fs = forward_stats(d, t0_idx, max(HORIZONS))
    if fs is None:
        continue
    ts = timing_stats(d, t0_idx, 40)
    obs.append({
        "ticker": tk,
        "week_key": ev["week_key"],
        "week_start": ev["week_start"],
        "t0_time": pd.Timestamp(ev["first_ob_time"]).strftime("%Y-%m-%d %H:%M"),
        "t0_close": round(float(ev["first_ob_close"]), 2),
        "n_ob_in_week": int(ev["n_ob"]),
        **{f"dd_{h}": None for h in HORIZONS},
        **{f"runup_{h}": None for h in HORIZONS},
        **{f"fwd_{h}": None for h in HORIZONS},
        "bars_to_bottom": ts[0], "bars_to_recover": ts[1],
        "new_high_40": bool(ts[2]), "bars_to_newhigh": ts[3],
    })
    for h in HORIZONS:
        fs_h = forward_stats(d, t0_idx, h)
        if fs_h is None:
            continue
        obs[-1][f"dd_{h}"] = round(fs_h["max_dd"], 2)
        obs[-1][f"runup_{h}"] = round(fs_h["max_runup"], 2)
        obs[-1][f"fwd_{h}"] = round(fs_h["fwd_ret"], 2)

obs_df = pd.DataFrame(obs)
print(f"\n有效观测(有完整40根4h后续): {len(obs_df)}")
obs_df.to_csv(os.path.join(OUT, "abbv_gild_week_ob_events.csv"), index=False, encoding="utf-8-sig")

# ---------------- 统计汇总 ----------------
def summarize(nums):
    nums = np.array([x for x in nums if x is not None and not (isinstance(x, float) and np.isnan(x))])
    if len(nums) == 0:
        return None
    return {
        "n": int(len(nums)), "mean": round(float(np.mean(nums)), 2), "med": round(float(np.median(nums)), 2),
        "p10": round(float(np.percentile(nums, 10)), 2), "p25": round(float(np.percentile(nums, 25)), 2),
        "p75": round(float(np.percentile(nums, 75)), 2), "p90": round(float(np.percentile(nums, 90)), 2),
        "min": round(float(np.min(nums)), 2), "max": round(float(np.max(nums)), 2),
        "neg_pct": round(float((nums < 0).mean() * 100), 1),
    }

summary = {}
for tk in TICKERS:
    sub = obs_df[obs_df["ticker"] == tk]
    summary[tk] = {}
    for h in HORIZONS:
        summary[tk][f"dd_{h}"] = summarize(sub[f"dd_{h}"].tolist())
        summary[tk][f"fwd_{h}"] = summarize(sub[f"fwd_{h}"].tolist())
    summary[tk]["recover"] = summarize(sub["bars_to_recover"].replace({None: np.nan}).tolist())
    summary[tk]["bottom"] = summarize(sub["bars_to_bottom"].tolist())
    summary[tk]["new_high_rate"] = round(float(sub["new_high_40"].mean() * 100), 1) if len(sub) else None
    summary[tk]["n"] = len(sub)

all_summary = {}
for h in HORIZONS:
    all_summary[f"dd_{h}"] = summarize(obs_df[f"dd_{h}"].tolist())
    all_summary[f"fwd_{h}"] = summarize(obs_df[f"fwd_{h}"].tolist())
all_summary["recover"] = summarize(obs_df["bars_to_recover"].replace({None: np.nan}).tolist())
all_summary["bottom"] = summarize(obs_df["bars_to_bottom"].tolist())
all_summary["new_high_rate"] = round(float(obs_df["new_high_40"].mean() * 100), 1)

# 按年份
obs_df["year"] = obs_df["t0_time"].str[:4]
year_sum = {}
for y in sorted(obs_df["year"].unique()):
    sub = obs_df[obs_df["year"] == y]
    year_sum[y] = {"n": len(sub), "dd_5": summarize(sub["dd_5"].tolist()), "dd_20": summarize(sub["dd_20"].tolist())}

# ---------------- 汇总 JSON ----------------
out_json = {
    "meta": {
        "tickers": TICKERS,
        "ob_threshold": OB,
        "horizons": HORIZONS,
        "source_4h": "腾讯 BATS 240min CSV",
        "source_weekly": "Yahoo 1wk adj_close",
        "events_total": int(len(ev_ob)),
        "events_with_ob": int(ev_ob["week_has_ob"].sum()),
        "events_ob_rate": round(float(ev_ob["week_has_ob"].mean() * 100), 1),
        "ctrl_weeks": int(len(ctrl)),
        "ctrl_ob_rate": round(float(ctrl["has_ob"].mean() * 100), 1),
    },
    "per_ticker": {tk: {
        "events": int(len(ev_ob[ev_ob.ticker == tk])),
        "with_ob": int(ev_ob[ev_ob.ticker == tk]["week_has_ob"].sum()),
        "ob_rate": round(float(ev_ob[ev_ob.ticker == tk]["week_has_ob"].mean() * 100), 1),
    } for tk in TICKERS},
    "summary": all_summary,
    "per_ticker_summary": summary,
    "year_summary": year_sum,
    "events": ev_ob.to_dict("records"),
    "obs": obs_df.to_dict("records"),
}
with open(os.path.join(OUT, "abbv_gild_weekline_ob.json"), "w", encoding="utf-8") as f:
    json.dump(out_json, f, ensure_ascii=False, indent=1, default=str)

print("\n===== 合并统计（两标的） =====")
for h in HORIZONS:
    s = all_summary[f"dd_{h}"]
    f = all_summary[f"fwd_{h}"]
    print(f"t0后{h}根: 最大回撤 中位 {s['med']}% (p25 {s['p25']} / p75 {s['p75']}), 有回撤占 {s['neg_pct']}%; 期末收益 中位 {f['med']}% 胜率 {100-(f['neg_pct'])}%")
r = all_summary["recover"]
print(f"回到t0收盘: 中位 {r['med']} 根 4h (p25 {r['p25']} / p75 {r['p75']})")
print(f"40根内创新高率: {all_summary['new_high_rate']}%")
print("\n===== 分标的 =====")
for tk in TICKERS:
    s = summary[tk]
    print(f"\n[{tk}] n={s['n']}")
    for h in HORIZONS:
        d = s[f"dd_{h}"]
        f = s[f"fwd_{h}"]
        print(f"  t0后{h}根: 回撤中位 {d['med']}% (p25 {d['p25']}/p75 {d['p75']}), 期末中位 {f['med']}% 胜率 {100-f['neg_pct']}%")
    print(f"  回到t0收盘 中位 {s['recover']['med']} 根; 40根内创新高 {s['new_high_rate']}%")

print("\nDONE")