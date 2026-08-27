# -*- coding: utf-8 -*-
"""
优质蓝筹股池「贴 EMA20 小平台 + 缩量破位」事件研究 —— T+5 / T+10 / T+20 表现
背景条件（通俗版）：过去 BG_WIN(默认5，3~10 可调) 个交易日在 EMA20 均线上方窄幅横盘
  - 过去 BG_WIN 日每天收盘相对当日 EMA20 偏离: dev_min >= DEV_LO(-2.5)%（允许某日小破均线、次日快速修复）
  - 过去 BG_WIN 日每天收盘相对当日 EMA20 偏离: dev_max <= DEV_HI(+6)%（横盘在均线上方、不能涨太高）
  - 期间振幅 (max high / min low - 1) <= AMP_TOL(5)%  => 小型交易区间/小平台
事件日 t：
  1. 收盘下跌 (close < prev close)
  2. 成交量是近 VOL_WIN(10) 个交易日(含当日)第 1 或第 2 低（缩量，"近两周数一数二低"）
  3. 收盘价跌破平台下沿 = 过去 BG_WIN 日(不含当日)最低收盘（"把小型交易区间跌破了"）
口径（对齐报告39/40/41）：
  - T+N = N 个交易日（shift(-N)），基准=事件日收盘买入
  - 主口径=全部事件（含密集重复）；稳健性=cooldown=10 去重 + 日历日聚类（同日多票取均值）
  - 对照：全历史基率 / 贴线横盘缩量收跌但未破平台(对照A) / 贴线横盘收跌破平台但未缩量(对照B) / 纯背景(对照C)
  - 分维：板块 / 阶段(疫情前~2020-02-19, 灾后2020-02-20~2022-12-31, 本轮牛市2023-) / 逐年
  - 敏感性：BG_WIN(3/7/10) / DEV_HI / AMP_TOL / VOL_WIN / VOL_RANK / 破位基准(close/low)
  - 统计单位一律百分数(×100)。输出 results/blue_chip_ema20_shrink_break.json
"""
import pandas as pd
import numpy as np
import json, os, glob, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

# ---------- 参数 ----------
EMA_WIN = 20
BG_WIN = 5             # 背景横盘窗口（默认5日；用户口径 3~10）
DEV_LO = -2.5          # 收盘相对 EMA20 最低容忍%（允许偶破均线快速修复）
DEV_HI = 6.0           # 收盘相对 EMA20 最高容忍%（横盘在均线上方）
AMP_TOL = 5.0          # 平台振幅%（max high/min low - 1）
VOL_WIN = 10           # 量能窗口（近两周≈10交易日）
VOL_RANK = 2           # 当日量在前 VOL_WIN 日内第几低以内（1=最低,2=最低或次低）
BREAK_BY = "close"     # 破位基准：close=收盘跌破平台最低收盘；low=最低价跌破平台最低 low

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

# ---------- 加载函数（完整 OHLCV + adj_close） ----------
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
    need = ["date", "open", "high", "low", "close", "volume"]
    if not all(c in df.columns for c in need):
        return None
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[need + [col]].rename(columns={col: "px"})
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    df = df.dropna(subset=["px", "high", "low", "close"]).sort_values("date").reset_index(drop=True)
    return df

def ema(series, span=EMA_WIN):
    return series.ewm(span=span, adjust=False).mean()

# ---------- 加载 SPY（对照） ----------
spy = load_stock("SPY").rename(columns={"px": "spy"})[["date", "spy"]]

frames = []
meta_range = {}
loaded = []
df_by_ticker = {}    # 供 K 线抽取
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < EMA_WIN + BG_WIN + 30:
        continue
    df_by_ticker[t] = df
    df["ticker"] = t
    df["sector"] = sectors[t]
    df["ema20"] = ema(df["px"])
    df["dev"] = (df["px"] / df["ema20"] - 1) * 100          # 当日收盘相对当日 EMA20 偏离 %
    # 背景：过去 BG_WIN 日（不含当日）每天 dev in [DEV_LO, DEV_HI] 且振幅<=AMP_TOL
    dev_max = df["dev"].shift(1).rolling(BG_WIN).max()
    dev_min = df["dev"].shift(1).rolling(BG_WIN).min()
    hi_max = df["high"].shift(1).rolling(BG_WIN).max()
    lo_min = df["low"].shift(1).rolling(BG_WIN).min()
    df["bg_close"] = (dev_max <= DEV_HI) & (dev_min >= DEV_LO)
    df["bg_amp"] = (hi_max / lo_min - 1) * 100 <= AMP_TOL
    df["bg"] = df["bg_close"] & df["bg_amp"]
    # 平台下沿：过去 BG_WIN 日(不含当日)最低收盘 / 最低 low
    df["box_lo_close"] = df["close"].shift(1).rolling(BG_WIN).min()
    df["box_lo_low"] = df["low"].shift(1).rolling(BG_WIN).min()
    # 缩量：当日量在前 VOL_WIN 日（含当日）内第几低（升序 rank，1=最低）
    def vol_rank_arr(v, w=VOL_WIN):
        n = len(v)
        out = np.full(n, np.nan)
        for i in range(w - 1, n):
            win = v[i - w + 1:i + 1]
            out[i] = int((win < v[i]).sum()) + 1   # 比当日小的个数+1 = 升序 rank
        return out
    df["vol_rank"] = vol_rank_arr(df["volume"].to_numpy(dtype=float))
    df["shrink"] = df["vol_rank"] <= VOL_RANK
    # 事件
    df["down"] = df["close"] < df["close"].shift(1)
    df["break"] = df["close"] < df["box_lo_close"]          # 收盘跌破平台最低收盘
    df["break_low"] = df["low"] < df["box_lo_low"]          # 最低价跌破平台最低 low（敏感性）
    df["event"] = df["bg"] & df["down"] & df["shrink"] & df["break"]
    # fwd 收益（相对事件日收盘）
    for N in (5, 10, 20):
        df[f"fwd{N}"] = (df["px"].shift(-N) / df["px"] - 1) * 100
    df = df.merge(spy, on="date", how="left")
    for N in (5, 10, 20):
        df[f"spy_fwd{N}"] = (df["spy"].shift(-N) / df["spy"] - 1) * 100
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

# ---------- 对照分组 ----------
ev_main = pool[pool["event"]].copy()                      # 主事件
ctlA = pool[pool["bg"] & pool["down"] & pool["shrink"] & ~pool["break"]].copy()  # 缩量收跌但没破平台
ctlB = pool[pool["bg"] & pool["down"] & pool["break"] & ~pool["shrink"]].copy()  # 破平台收跌但没缩量
ctlC = pool[pool["bg"]].copy()                            # 纯背景（贴线横盘所有日）
ev_lowbreak = pool[pool["bg"] & pool["down"] & pool["shrink"] & pool["break_low"]].copy()  # 用 low 破位口径

# ---------- cd10 去重 ----------
def apply_cd10(ev):
    rows = []
    for t, g in ev.groupby("ticker"):
        g = g.sort_values("date").reset_index(drop=True)
        keep, last = [], -10 ** 9
        for i in range(len(g)):
            if i - last >= 10:
                keep.append(i)
                last = i
        rows.append(g.iloc[keep])
    return pd.concat(rows, ignore_index=True) if rows else ev.iloc[0:0]

ev_cd10 = apply_cd10(ev_main)

# ---------- 日历日聚类 ----------
def day_cluster(df):
    if len(df) == 0:
        return pd.DataFrame()
    agg = []
    for N in (5, 10, 20):
        agg.append(df.groupby("date")[f"fwd{N}"].mean().rename(f"fwd{N}"))
        agg.append(df.groupby("date")[f"spy_fwd{N}"].mean().rename(f"spy_fwd{N}"))
    return pd.concat(agg, axis=1).reset_index()

ev_day = day_cluster(ev_main)

# ---------- 结果组装 ----------
def by_sector(df):
    return {sc: block(df[df["sector"] == sc]) for sc in SECTOR_CN}

def by_stage(df):
    return {st: block(df[df["stage"] == st]) for st in ["A_pre", "B_post", "C_bull"]}

def by_year(df):
    return {str(y): block(df[df["date"].dt.year == y]) for y in sorted(df["date"].dt.year.unique())}

def per_ticker(df):
    return {t: {"sector": sectors[t], "n": int(len(g)), **block(g)} for t, g in df.groupby("ticker")}

res = {
    "meta": {
        "universe": "blue_chips.csv 优质蓝筹股池",
        "n_tickers_loaded": len(loaded),
        "n_tickers_pool": len(tickers),
        "skipped": [t for t in tickers if t not in loaded],
        "data_range": meta_range,
        "params": {
            "ema_win": EMA_WIN, "bg_win": BG_WIN,
            "dev_lo_pct": DEV_LO, "dev_hi_pct": DEV_HI, "amp_tol_pct": AMP_TOL,
            "vol_win": VOL_WIN, "vol_rank_le": VOL_RANK, "break_by": BREAK_BY,
        },
        "event": "背景=过去{0}日贴EMA20上方窄幅横盘(dev∈[{1},{2}]%, 振幅≤{3}%)；"
                 "事件=某日收跌+成交量近{VOL_WIN}日第{VOL_RANK}低+收盘跌破平台最低收盘".format(
                     BG_WIN, DEV_LO, DEV_HI, AMP_TOL, VOL_WIN=VOL_WIN, VOL_RANK=VOL_RANK),
        "horizon": "T+N = N 个交易日（shift(-N)），基准=事件日收盘",
        "stages": {
            "A_pre": "疫情前：~2020-02-19",
            "B_post": "疫情及股灾后：2020-02-20~2022-12-31",
            "C_bull": "本轮牛市：2023-01-01~",
        },
    },
    "n_events": {
        "total_days": int(pool["date"].nunique()),
        "main_all": int(len(ev_main)),
        "main_cd10": int(len(ev_cd10)),
        "day_clustered": int(ev_main["date"].nunique()),
        "ctlA_kept_box": int(len(ctlA)),
        "ctlB_no_shrink": int(len(ctlB)),
        "ctlC_bg_all": int(len(ctlC)),
        "low_break_alt": int(len(ev_lowbreak)),
    },
    "baseline_all_days": block(pool),
    "baseline_bg_only": block(ctlC),                        # 纯背景基率（贴线横盘所有日）
    "control_kept_box": block(ctlA),                        # 对照组A：缩量收跌但守住平台
    "control_no_shrink": block(ctlB),                       # 对照组B：破平台收跌但放量
    "events_main": {
        "block": block(ev_main),
        "day_clustered": block(ev_day),
        "by_sector": by_sector(ev_main),
        "by_stage": by_stage(ev_main),
        "by_year": by_year(ev_main),
    },
    "events_cd10": {
        "block": block(ev_cd10),
        "by_sector": by_sector(ev_cd10),
        "by_stage": by_stage(ev_cd10),
    },
    "events_low_break_alt": block(ev_lowbreak),             # 敏感性：用 low 破位
    "per_ticker": per_ticker(ev_cd10),
}

# ---------- 参数敏感性 ----------
def run_sensitivity():
    out = []
    params_grid = [
        ("BG_WIN=3", {"bw": 3}),
        ("BG_WIN=7", {"bw": 7}),
        ("BG_WIN=10", {"bw": 10}),
        ("DEV_HI=4", {"dh": 4.0}),
        ("DEV_HI=8", {"dh": 8.0}),
        ("AMP_TOL=3", {"amp": 3.0}),
        ("AMP_TOL=8", {"amp": 8.0}),
        ("VOL_WIN=14", {"vw": 14}),
        ("VOL_RANK=1", {"vr": 1}),
        ("VOL_RANK=3", {"vr": 3}),
        ("BREAK_BY=low", {"bb": "low"}),
    ]
    for label, p in params_grid:
        bw = p.get("bw", BG_WIN)
        dev_lo = DEV_LO
        dev_hi = p.get("dh", DEV_HI)
        amp = p.get("amp", AMP_TOL)
        vw = p.get("vw", VOL_WIN)
        vr = p.get("vr", VOL_RANK)
        bb = p.get("bb", BREAK_BY)
        fwd5, fwd10, fwd20 = [], [], []
        for t in loaded:
            df = load_stock(t)
            if df is None:
                continue
            df["ema20"] = ema(df["px"])
            df["dev"] = (df["px"] / df["ema20"] - 1) * 100
            dev_max = df["dev"].shift(1).rolling(bw).max()
            dev_min = df["dev"].shift(1).rolling(bw).min()
            hi_max = df["high"].shift(1).rolling(bw).max()
            lo_min = df["low"].shift(1).rolling(bw).min()
            bg = (dev_max <= dev_hi) & (dev_min >= dev_lo) & ((hi_max / lo_min - 1) * 100 <= amp)
            if bb == "low":
                box_lo = df["low"].shift(1).rolling(bw).min()
                brk = df["low"] < box_lo
            else:
                box_lo = df["close"].shift(1).rolling(bw).min()
                brk = df["close"] < box_lo
            down = df["close"] < df["close"].shift(1)
            vr_arr = np.full(len(df), np.nan)
            v = df["volume"].to_numpy(dtype=float)
            for i in range(vw - 1, len(df)):
                vr_arr[i] = int((v[i - vw + 1:i + 1] < v[i]).sum()) + 1
            shrink = vr_arr <= vr
            ev = bg & down & shrink & brk
            if ev.sum() == 0:
                continue
            idx = np.where(ev.to_numpy())[0]
            px = df["px"].to_numpy()
            for k in idx:
                if k + 20 < len(df):
                    fwd5.append((px[k + 5] / px[k] - 1) * 100)
                    fwd10.append((px[k + 10] / px[k] - 1) * 100)
                    fwd20.append((px[k + 20] / px[k] - 1) * 100)
        out.append({
            "label": label, "n": len(fwd10),
            **{f"T5": stats(pd.Series(fwd5)), f"T10": stats(pd.Series(fwd10)), f"T20": stats(pd.Series(fwd20))},
        })
    return out

res["sensitivity"] = run_sensitivity()

# ---------- 事件明细（瘦身） ----------
ev_list = []
for _, r in ev_main.sort_values("date", ascending=False).iterrows():
    ev_list.append({
        "date": str(r["date"].date()), "ticker": r["ticker"], "sector": r["sector"],
        "px": round(float(r["px"]), 2),
        "dev_pct": round(float(r["dev"]), 2),
        "vol_rank": int(r["vol_rank"]),
        "stage": r["stage"],
        "fwd5": round(float(r["fwd5"]), 2) if not pd.isna(r["fwd5"]) else None,
        "fwd10": round(float(r["fwd10"]), 2) if not pd.isna(r["fwd10"]) else None,
        "fwd20": round(float(r["fwd20"]), 2) if not pd.isna(r["fwd20"]) else None,
    })
res["events"] = ev_list   # 全部事件明细（8305 条）

# ---------- 当前状态：最新日处于背景区间的票，以及最近事件 ----------
last_date = pool["date"].max()
recent_bg = pool[(pool["date"] == last_date) & pool["bg"]]
cur_bg = [{"ticker": r["ticker"], "dev": round(float(r["dev"]), 2),
           "vol_rank_last": int(r["vol_rank"]) if not np.isnan(r["vol_rank"]) else None}
          for _, r in recent_bg.iterrows()]
recent_ev = ev_main[ev_main["date"] >= (last_date - pd.Timedelta(days=45))]
cur_ev = [{"date": str(r["date"].date()), "ticker": r["ticker"],
           "fwd5": round(float(r["fwd5"]), 2) if not pd.isna(r["fwd5"]) else None,
           "fwd10": round(float(r["fwd10"]), 2) if not pd.isna(r["fwd10"]) else None}
          for _, r in recent_ev.sort_values("date", ascending=False).iterrows()]
res["current"] = {"as_of": str(last_date.date()), "bg_today": cur_bg, "recent_events_45d": cur_ev}

# ---------- K 线数据（事件浏览器用，独立文件） ----------
KWIN = 20            # 事件日前后各取多少交易日
N_KLINE = 400        # 内嵌 K 线的最近事件数
kline_events = []
for _, r in ev_main.sort_values("date", ascending=False).head(N_KLINE).iterrows():
    tdf = df_by_ticker.get(r["ticker"])
    if tdf is None:
        continue
    tdf = tdf.reset_index(drop=True)
    pos = int(np.flatnonzero(tdf["date"] == r["date"])[0])
    if pos - KWIN < 0 or pos + KWIN + 20 >= len(tdf):   # 需要前后 KWIN 且有未来数据
        continue
    lo, hi = pos - KWIN, pos + KWIN
    if r["date"] not in tdf["date"].to_numpy():
        continue
    k = {
        "dates": [str(d.date()) for d in tdf["date"].iloc[lo:hi + 1]],
        "ohlc": [[round(float(x), 3) for x in row] for row in tdf[["open", "high", "low", "close"]].iloc[lo:hi + 1].to_numpy()],
        "vols": [int(v) for v in tdf["volume"].iloc[lo:hi + 1].to_numpy()],
        "ema": [round(float(x), 3) if not np.isnan(x) else None for x in tdf["ema20"].iloc[lo:hi + 1].to_numpy()],
        "ev": KWIN,
    }
    kline_events.append({
        "date": str(r["date"].date()), "ticker": r["ticker"],
        "sector": SECTOR_CN.get(r["sector"], r["sector"]),
        "px": round(float(r["px"]), 2),
        "dev_pct": round(float(r["dev"]), 2),
        "vol_rank": int(r["vol_rank"]),
        "stage": r["stage"],
        "fwd5": round(float(r["fwd5"]), 2) if not pd.isna(r["fwd5"]) else None,
        "fwd10": round(float(r["fwd10"]), 2) if not pd.isna(r["fwd10"]) else None,
        "fwd20": round(float(r["fwd20"]), 2) if not pd.isna(r["fwd20"]) else None,
        "k": k,
    })
kline_res = {
    "meta": {"event": "贴EMA20平台缩量跌破箱体", "kwin": KWIN, "n_embedded": len(kline_events),
             "total_events": int(len(ev_main)), "note": "内嵌最近 N 个事件 K 线，事件日居中(索引=kwin)，前后各 kwin 个交易日"},
    "events": kline_events,
}

# ---------- 写盘 ----------
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o

with open(os.path.join(OUT, "blue_chip_ema20_shrink_break.json"), "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)

with open(os.path.join(OUT, "blue_chip_ema20_shrink_break_kline.json"), "w", encoding="utf-8") as f:
    json.dump(clean(kline_res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 汇总打印 ----------
def fmt(s, k="T5"):
    t = s.get(k, {})
    if not t or t.get("n", 0) == 0: return "n=0"
    return f"n={t['n']} mean={t['mean']:+.2f}% med={t['median']:+.2f}% win={t['win']}% t={t.get('t')}"

print(f"加载 {len(loaded)}/{len(tickers)} 只 | 跳过 {res['meta']['skipped']}")
print(f"交易日总数 {res['n_events']['total_days']} | 主事件 {len(ev_main)} (cd10:{len(ev_cd10)}, 日历日:{ev_main['date'].nunique()})")
print(f"对照样本: A守住平台 {len(ctlA)} | B放量破位 {len(ctlB)} | C纯背景 {len(ctlC)}")
b = res["baseline_all_days"]
print(f"[全历史基率] T5:{fmt(b)} | T10:{fmt(b,'T10')} | T20:{fmt(b,'T20')}")
bg = res["baseline_bg_only"]
print(f"[纯背景贴线横盘] T5:{fmt(bg)} | T10:{fmt(bg,'T10')} | T20:{fmt(bg,'T20')}")
for lab, c in [("对照A 缩量守平台", res["control_kept_box"]),
               ("对照B 放量破平台", res["control_no_shrink"])]:
    print(f"[{lab}] T5:{fmt(c)} | T10:{fmt(c,'T10')} | T20:{fmt(c,'T20')}")
ea = res["events_main"]["block"]; ea_d = res["events_main"]["day_clustered"]
ec = res["events_cd10"]["block"]
print(f"[主事件 全部] T5:{fmt(ea)} | T10:{fmt(ea,'T10')} | T20:{fmt(ea,'T20')}")
print(f"[主事件 日历日聚类] T5:{fmt(ea_d)} | T10:{fmt(ea_d,'T10')} | T20:{fmt(ea_d,'T20')}")
print(f"[主事件 cd10去重] T5:{fmt(ec)} | T10:{fmt(ec,'T10')} | T20:{fmt(ec,'T20')}")
print(f"[主事件 exSPY超额 全部] T5:{fmt(ea,'T5_ex_spy')} | T10:{fmt(ea,'T10_ex_spy')} | T20:{fmt(ea,'T20_ex_spy')}")
print(f"[敏感性 low破位] T5:{fmt(res['events_low_break_alt'])} | T10:{fmt(res['events_low_break_alt'],'T10')} | T20:{fmt(res['events_low_break_alt'],'T20')}")
for st, lab in [("A_pre", "疫情前"), ("B_post", "疫情及股灾后"), ("C_bull", "本轮牛市")]:
    sb = res["events_main"]["by_stage"][st]
    print(f"[{lab}] T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}  (n={sb.get('T5',{}).get('n')})")
for sc, lab in SECTOR_CN.items():
    sb = res["events_main"]["by_sector"].get(sc, {})
    if not sb.get("T5", {}).get("n"): continue
    print(f"[{lab}] T5:{fmt(sb)} | T10:{fmt(sb,'T10')} | T20:{fmt(sb,'T20')}")
print("--- 参数敏感性 ---")
for s in res["sensitivity"]:
    print(f"{s['label']:12s} n={s['n']:5d} T5:{fmt(s,'T5')} | T10:{fmt(s,'T10')}")
print("当前贴线横盘标的(最新日):", [(c["ticker"], c["dev"]) for c in res["current"]["bg_today"]][:15])
print(f"written: {os.path.join(OUT, 'blue_chip_ema20_shrink_break.json')}")
print(f"kline embedded: {len(kline_events)} events -> {os.path.join(OUT, 'blue_chip_ema20_shrink_break_kline.json')}")
