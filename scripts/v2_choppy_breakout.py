# -*- coding: utf-8 -*-
"""
70 号报告 v2 —— 震荡市个股假突破研究（重做）
口径来源：handoff/震荡市假突破研究_交接文档.md（v1.0 2026-09-04）
所有参数集中于 CONFIG；中途调口径只改这里，重跑全链条。
"""
import os, json
import numpy as np
import pandas as pd

# ---------------- CONFIG ----------------
CONFIG = {
    "data_dir": r"C:\Users\Administrator\Desktop\stock\data",
    "out_dir": r"C:\Users\Administrator\Desktop\stock\results\70_v2",
    "blue_chips": "blue_chips.csv",
    "start_date": "2010-01-01",
    "end_date": None,          # None = 用数据最后日期
    # Step1 震荡判定（三支柱，三选二）
    # 调参记录（09-04，依据交接文档 3.1 验收红线授权"先调支柱 C 阈值(±)"）：
    # 原始 C(|20r|<2% & cross>=4) 覆盖 24.0% <30%；网格测试 B 分位×C 阈值，
    # 综合覆盖率(30-45%)×真震荡窗命中×压力窗误判(2018Q4/2020.2-4/2022/2025.3-4≈0)，
    # 选定 B<0.30 + C(|20r|<3% & cross>=3)（B 分位保持文档原值 0.30）。
    "adx_len": 14, "adx_thresh": 20.0,
    "bb_len": 20, "bb_nstd": 2.0, "bb_rank_len": 250, "bb_rank_pct": 0.30,
    "c_ret_win": 20, "c_ret_thresh": 0.03, "c_cross_win": 20, "c_cross_min": 3, "c_ma_len": 20,
    "choppy_lo": 0.30, "choppy_hi": 0.45,   # 覆盖率验收红线
    # 备用定义（稳健性）
    "alt_a_er_len": 20, "alt_a_er_thresh": 0.2,
    "alt_b_rvol_len": 20, "alt_b_rank_len": 250, "alt_b_rank_pct": 0.30,
    "alt_c_reg_win": 60, "alt_c_pval": 0.10, "alt_c_r2": 0.10,
    # Step2 突破事件（口径 C 为主）
    "donchian_len": 55,
    "min_break_atr": 0.3,          # 毛刺过滤：收盘超出参考位 >=0.3*ATR
    "cooldown": 20,                # 同方向冷却期（交易日）
    "gap_skip_atr": 2.0,           # 跳空开盘越过参考位 >2*ATR → gap_skip
    "jump_filter": 0.40,           # 单日 |涨跌|>40% 剔除（拆股伪影双保险）
    "earnings_window": 1,          # 财报日 +-1 个交易日剔除
    "adr_len": 20,
    # Step3 假突破阶梯
    "ladder_ks": [0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0],
    "fwd_window": 10,              # dev_max 观察窗 T+10
    "main_thresh": 1.0,            # 二值结论默认阈值
    "alt_threshes": [0.5, 1.5],
    "cluster_len": 60,             # 聚类/块 bootstrap 块长（日）
    "n_boot": 2000, "boot_seed": 42,
    "bh_alpha": 0.05,
    # Step6 fade 回测
    "fade_entry_win": 5,           # T+5 内回踩入场
    "fade_stop_atr": 0.5,          # 止损：重新站上突破位 +0.5*ATR（向上突破做空）
    "fade_target_atr": 1.5,        # 目标：突破位 -1.5*ATR
    "fade_max_hold": 20,           # T+20 强制平仓
    "fuzzy_edge": 5,               # 震荡窗首尾 5 日模糊带
    "min_turnover_usd": 1e7,       # 流动性过滤：20日均成交额 > 1000万美元
    # 板块 beta（控制回归）
    "beta_len": 250,
}

CONFIG["out_dir_abs"] = CONFIG["out_dir"]
os.makedirs(CONFIG["out_dir"], exist_ok=True)

# ---------------- 数据加载 ----------------
def load_ohlc(ticker_dir_name):
    """加载 {data_dir}/{ticker}/{ticker}, 1D.csv → DataFrame(date,open,high,low,close,volume,adj_close)"""
    p = os.path.join(CONFIG["data_dir"], ticker_dir_name, f"{ticker_dir_name}, 1D.csv")
    if not os.path.exists(p):
        p = os.path.join(CONFIG["data_dir"], ticker_dir_name, f"{ticker_dir_name.upper()}, 1D.csv")
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p)
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df

def load_spy():
    for name in ["SPY, 1D.csv", "BATS_SPY, 1D.csv"]:
        p = os.path.join(CONFIG["data_dir"], "spy", name)
        if os.path.exists(p):
            df = pd.read_csv(p)
            df.columns = [c.strip().lower() for c in df.columns]
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date").reset_index(drop=True)
    raise FileNotFoundError("SPY 1D not found")

# ---------------- 指标（防前视：全部只用 ≤ 当日数据）----------------
def wilder_ema(s, n):
    """Wilder 平滑 = EWM alpha=1/n，注意 pandas ewm 默认 adjust=True，须 adjust=False 且首值对齐。
    实务上用 alpha=1/n, adjust=True 与 Wilder 递推在长序列下收敛一致；为严格复现用递归实现太慢，
    采用 ewm(alpha=1/n, adjust=False)，min_periods=n。"""
    return s.ewm(alpha=1.0/n, adjust=False, min_periods=n).mean()

def adx_wilder(df, n=14):
    """ADX(14) Wilder 平滑。TR 含跳空项。返回 DataFrame(dx=adx, plus_di, minus_di)。"""
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h-l), (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    up = h.diff()
    dn = -l.diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    atr = wilder_ema(tr, n)
    plus_di = 100 * wilder_ema(plus_dm, n) / atr
    minus_di = 100 * wilder_ema(minus_dm, n) / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = wilder_ema(dx.fillna(0), n)
    return adx, plus_di, minus_di, atr

def bollinger_bw(df, n=20, nstd=2.0):
    m = df["close"].rolling(n).mean()
    sd = df["close"].rolling(n).std(ddof=0)
    return (m + nstd*sd - (m - nstd*sd)) / m

def rolling_pctile_rank(s, win=250):
    """过去 win 日的分位秩（含当日），输出 0-1。"""
    def rank_last(x):
        return (x <= x[-1]).mean()
    return s.rolling(win).apply(rank_last, raw=True)

def kaufman_er(df, n=20):
    """Kaufman 效率比 = |净变动| / Σ|逐日变动|"""
    change = df["close"].diff(n).abs()
    vol = df["close"].diff().abs().rolling(n).sum()
    return change / vol

def realized_vol_pctile(df, n=20, win=250, pct=0.30):
    r = np.log(df["close"]).diff()
    rv = r.rolling(n).std(ddof=0) * np.sqrt(252)
    return rolling_pctile_rank(rv, win), rv

def ma_cross_count(df, ma_len=20, win=20):
    """过去 win 日内收盘穿越 MA 的次数（上穿+下穿）"""
    ma = df["close"].rolling(ma_len).mean()
    above = (df["close"] > ma).astype(int)
    crosses = above.diff().abs()
    return crosses.rolling(win).sum()

def logreg_slope_pval_r2(df, win=60):
    """60 日对数价格线性回归：返回斜率 p 值与 R²（只用 ≤当日数据）。
    用滑动窗口批量计算（scipy linregress 向量化近似：用解析公式）。"""
    y = np.log(df["close"].values)
    n = len(df)
    x = np.arange(win, dtype=float)
    xbar = x.mean(); sxx = ((x-xbar)**2).sum()
    out_p = np.full(n, np.nan); out_r2 = np.full(n, np.nan)
    # 用 stride 滑窗
    from numpy.lib.stride_tricks import sliding_window_view
    if n < win: return out_p, out_r2
    W = sliding_window_view(y, win)   # shape (n-win+1, win)
    ybar = W.mean(axis=1)
    sxy = ((W - ybar[:,None]) * x).sum(axis=1)
    slope = sxy / sxx
    intercept = ybar - slope * xbar
    resid = W - (intercept[:,None] + slope[:,None]*x)
    sse = (resid**2).sum(axis=1)
    sst = ((W - ybar[:,None])**2).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r2 = 1 - sse/sst
    # t 检验 p 值（斜率）：t = slope/SE, SE^2 = sse/(win-2)/sxx
    from scipy import stats as sst_mod
    dof = win - 2
    se2 = (sse/dof)/sxx
    with np.errstate(divide="ignore", invalid="ignore"):
        tval = slope/np.sqrt(se2)
    pval = 2*(1 - sst_mod.t.cdf(np.abs(tval), dof))
    out_p[win-1:] = pval
    out_r2[win-1:] = r2
    return out_p, out_r2

# ---------------- Step 1: 震荡判定器 ----------------
def choppy_detector(spy, variant=None):
    """输出 SPY 逐日 pA/pB/pC/choppy(0/1)。variant=None 主口径；'altA'/'altB'/'altC' 备用定义（稳健性）"""
    d = spy.copy().reset_index(drop=True)
    adx, plus_di, minus_di, atr = adx_wilder(d, CONFIG["adx_len"])
    bw = bollinger_bw(d, CONFIG["bb_len"], CONFIG["bb_nstd"])
    bw_rank = rolling_pctile_rank(bw, CONFIG["bb_rank_len"])
    c_ret = d["close"].pct_change(CONFIG["c_ret_win"]).abs()
    crosses = ma_cross_count(d, CONFIG["c_ma_len"], CONFIG["c_cross_win"])

    pA = (adx < CONFIG["adx_thresh"]).astype(int)
    pB = (bw_rank < CONFIG["bb_rank_pct"]).astype(int)
    pC = ((c_ret < CONFIG["c_ret_thresh"]) & (crosses >= CONFIG["c_cross_min"])).astype(int)

    if variant is None:
        pass
    elif variant == "altA":
        er = kaufman_er(d, CONFIG["alt_a_er_len"])
        pA = (er < CONFIG["alt_a_er_thresh"]).astype(int)
    elif variant == "altB":
        _, rv = realized_vol_pctile(d, CONFIG["alt_b_rvol_len"], CONFIG["alt_b_rank_len"], CONFIG["alt_b_rank_pct"])
        pB = (rolling_pctile_rank(rv, CONFIG["alt_b_rank_len"]) < CONFIG["alt_b_rank_pct"]).astype(int)
    elif variant == "altC":
        pval, r2 = logreg_slope_pval_r2(d, CONFIG["alt_c_reg_win"])
        pC = ((pval > CONFIG["alt_c_pval"]) & (r2 < CONFIG["alt_c_r2"])).astype(int)

    choppy = ((pA + pB + pC) >= 2).astype(int)
    out = pd.DataFrame({
        "date": d["date"], "close": d["close"], "pA": pA, "pB": pB, "pC": pC,
        "choppy": choppy, "adx": adx, "bw_rank": bw_rank,
    })
    return out

def choppy_runs(ch):
    """震荡窗口起止列表 [(start,end, inclusive)]（连续 choppy=1 的段）"""
    ch = ch.reset_index(drop=True)
    runs, s = [], None
    for i, v in enumerate(ch["choppy"]):
        if v == 1 and s is None: s = i
        elif v == 0 and s is not None:
            runs.append((s, i-1)); s = None
    if s is not None: runs.append((s, len(ch)-1))
    return runs

# ---------------- Step 2: 突破事件提取（口径 C 55 日新高/新低）----------------
def atr14(df):
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h-l), (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    return wilder_ema(tr, 14)

def adr20(df):
    """ADR(20)%：日收益绝对值的 20 日均值×100，用突破日前一日为止的数据（防泄漏）。"""
    ret = df["close"].pct_change().abs()
    return ret.rolling(CONFIG["adr_len"]).mean().shift(1) * 100

def extract_events(df, ticker, sector, choppy_df, earnings_dates, cfg=CONFIG):
    """口径 C：收盘 > 过去55日最高收盘（前一日不满足）。向下镜像。
    返回事件 DataFrame。"""
    L = cfg["donchian_len"]
    d = df.copy().reset_index(drop=True)
    # 全部用 adj_close（复权口径）
    c = d["adj_close"].values
    n = len(d)
    ch_map = choppy_df.set_index("date")["choppy"]
    ch_arr = d["date"].map(ch_map).values  # NaN → 不在 SPY 索引（停牌等）
    events = []
    for i in range(L+1, n - cfg["fwd_window"]):   # 需要至少 fwd_window 前瞻数据
        # 拆股/跳变过滤（复权价下不应有；双保险用原始 close 涨跌幅）
        if i >= 1:
            r1 = abs(d["close"].iloc[i] / d["close"].iloc[i-1] - 1)
            if r1 > cfg["jump_filter"]: continue
        px = c[i]
        # 55 日窗口：i-L .. i-1（不含当日）
        win_hi = c[i-L:i].max(); win_lo = c[i-L:i].min()
        prev_hi = c[i-L-1:i-1].max(); prev_lo = c[i-L-1:i-1].min()
        a = d["atr"].iloc[i]
        if not np.isfinite(a) or a <= 0: continue
        # 流动性：20日均成交额（用 adj_close×volume 近似美元成交额）
        tv = (d["adj_close"] * d["volume"]).rolling(20).mean().iloc[i]
        if not np.isfinite(tv) or tv < cfg["min_turnover_usd"]: continue
        # ADR（截至前一日）
        adr = d["adr"].iloc[i]
        if not np.isfinite(adr) or adr <= 0: continue
        # 向上突破：当日收盘 > 前 L 日最高收盘，且前一日不满足
        up_new = px > win_hi
        up_prev = c[i-1] > prev_hi
        dn_new = px < win_lo
        dn_prev = c[i-1] < prev_lo
        direction = None
        if up_new and not up_prev: direction = "up"
        elif dn_new and not dn_prev: direction = "down"
        if direction is None: continue
        ref = win_hi if direction == "up" else win_lo
        brk = abs(px - ref) / a
        if brk < cfg["min_break_atr"]: continue      # 毛刺过滤
        # 跳空越过参考位 >2×ATR → gap_skip
        o = d["adj_close"].iloc[i]  # 近似：用收盘代替开盘判断（数据无独立 adj_open；用 open/adj 比例调整）
        adj_o = d["open"].iloc[i] * (d["adj_close"].iloc[i] / d["close"].iloc[i])
        gap_over = abs(adj_o - ref) / a if direction == "up" else abs(ref - adj_o) / a
        gap_skip = (adj_o > ref + cfg["gap_skip_atr"]*a) if direction == "up" else (adj_o < ref - cfg["gap_skip_atr"]*a)
        # 冷却期：同方向 20 个交易日内不重复（且前一日处于突破态不算新事件）
        # 在循环内不便回看，改为先收集再过滤
        dt = d["date"].iloc[i]
        ch = ch_arr[i]
        ch = 0 if (ch is None or (isinstance(ch, float) and np.isnan(ch))) else int(ch)
        ev = dict(ticker=ticker, sector=sector, date=dt, dir=direction, ref=ref,
                  close=px, atr=a, adr=adr, brk_atr=brk, gap_skip=bool(gap_skip),
                  choppy=ch, idx=i)
        # T+10 最大反向偏离（只看收盘）
        fwd = c[i+1 : i+1+cfg["fwd_window"]]
        if direction == "up":
            dev_max = max((ref - fwd).max() / ref, 0.0)
        else:
            dev_max = max((fwd - ref).max() / ref, 0.0)
        ev["dev_max"] = dev_max
        ev["dev_adr"] = dev_max / (adr/100.0)
        # 前瞻收益 T+N（以突破日收盘为基准）
        for N in (5, 10, 20):
            if i+1+N < n:
                ev[f"fwd{N}"] = (c[i+1+N] / px - 1) * 100
            else:
                ev[f"fwd{N}"] = np.nan
        # fade 回测在 Step6 基于本表逐事件前向重放
        events.append(ev)
    if not events: return pd.DataFrame()
    ev = pd.DataFrame(events)
    # 冷却期过滤（同方向间隔 ≥20 交易日；gap_skip 事件也占用冷却期吗？→ 占用，防密集）
    keep = []
    last_idx = {"up": -10**9, "down": -10**9}
    for _, row in ev.iterrows():
        if row["idx"] - last_idx[row["dir"]] >= cfg["cooldown"]:
            keep.append(True); last_idx[row["dir"]] = row["idx"]
        else:
            keep.append(False)
    ev = ev[keep].reset_index(drop=True)
    # 财报剔除：突破日 ±1 交易日内
    if earnings_dates:
        idx_arr = ev["idx"].values
        ed_idx = set()
        date_to_idx = {d["date"].iloc[k]: k for k in range(n)}
        for ed in earnings_dates:
            if ed in date_to_idx:
                j = date_to_idx[ed]
                for off in range(-cfg["earnings_window"], cfg["earnings_window"]+1):
                    if 0 <= j+off < n: ed_idx.add(j+off)
        ev = ev[~np.isin(idx_arr, list(ed_idx))].reset_index(drop=True)
    return ev

# ---------------- 主流程（Step1+2）----------------
def main():
    cfg = CONFIG
    spy = load_spy()
    print(f"SPY: {spy['date'].min().date()} ~ {spy['date'].max().date()}, {len(spy)} rows")
    ch = choppy_detector(spy)
    cov = ch["choppy"].mean()
    print(f"震荡覆盖率(全样本): {cov*100:.1f}%  (验收 30-45%)")
    ch.to_csv(os.path.join(cfg["out_dir"], "spy_choppy_main.csv"), index=False)
    # 四段已知时期人工抽查记录
    runs = choppy_runs(ch[ch["date"] >= cfg["start_date"]])
    print(f"震荡窗口数: {len(runs)}")

    bc = pd.read_csv(os.path.join(cfg["data_dir"], cfg["blue_chips"]), encoding="utf-8-sig")
    bc["ticker"] = bc["ticker"].str.strip().str.lower()
    bc["sector"] = bc["sector"].str.strip()

    all_ev = []
    for _, r in bc.iterrows():
        t = r["ticker"]
        df = load_ohlc(t)
        if df is None:
            print("MISS", t); continue
        df = df[df["date"] >= pd.Timestamp(cfg["start_date"])].reset_index(drop=True)
        if len(df) < cfg["donchian_len"] + cfg["fwd_window"] + cfg["adr_len"] + 50:
            print("SKIP(short)", t, len(df)); continue
        # 指标列（防前视：ATR/ADR 只用 ≤当日；ADR 已 shift(1)）
        d = df.copy()
        d["atr"] = atr14(d[["high","low","close"]].rename(columns={}))
        # atr14 expects df with high/low/close
        d["adr"] = adr20(d)
        # 财报日历
        edf_path = os.path.join(cfg["out_dir"], f"earnings_{t}.csv")
        edates = []
        if os.path.exists(edf_path):
            edates = [pd.Timestamp(x) for x in pd.read_csv(edf_path)["date"].dropna()]
        ev = extract_events(d, t, r["sector"], ch, edates)
        all_ev.append(ev)
        print(f"{t}: {len(ev)} events (up={int((ev['dir']=='up').sum()) if len(ev) else 0}, dn={int((ev['dir']=='down').sum()) if len(ev) else 0})")
    evall = pd.concat(all_ev, ignore_index=True)
    evall.to_csv(os.path.join(cfg["out_dir"], "events.csv"), index=False)
    print("TOTAL events:", len(evall))
    print("up:", int((evall['dir']=='up').sum()), "down:", int((evall['dir']=='down').sum()),
          "gap_skip:", int(evall['gap_skip'].sum()))

if __name__ == "__main__":
    main()
