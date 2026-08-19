#!/usr/bin/env python3
"""药明康德 vs 美国大药企/板块指数 相关性分析。

核心问题：药明康德(2359.HK 为主)能在多大程度上反映美国制药公司景气度/制药周期？
分析维度:
  1. 配对相关性: WUXI-H vs ABBV/MRK/JNJ/LLY/GILD + 基准(IBB/XBI/XLV/SPY)，全期+分段
  2. 滚动 60 日相关性
  3. beta / R2 / 残差波动
  4. 领先/滞后交叉相关 (lag -5..+5)
  5. 月度相关性(近3年)
  6. 归一化净值(相对强弱曲线, 2021 起)
  7. 超额收益四档(事件分段)
  8. 关键事件窗口 (-5..+5 交易日) 反应
  9. A/H 对照
输出 JSON 到 results/wuxi_bigpharma.json
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

# 分段边界
SPLIT_2025_09 = pd.Timestamp("2025-09-01")   # 对照窗口起点(项目习惯)
SPLIT_2026_02 = pd.Timestamp("2026-02-01")   # 1260H 首轮公示冲击
SPLIT_2026_06 = pd.Timestamp("2026-06-08")   # 1260H 正式列入

TARGET = "WUXIH"   # 药明康德 H 股
TARGET_A = "WUXIA" # 药明康德 A 股

TICKERS = {
    "WUXIH": ("2359.hk", "2359.HK, 1D.csv", "药明康德H"),
    "WUXIA": ("603259.ss", "603259.SS, 1D.csv", "药明康德A"),
    "ABBV": ("abbv", "ABBV, 1D.csv", "艾伯维"),
    "MRK": ("mrk", "MRK, 1D.csv", "默沙东"),
    "JNJ": ("jnj", "JNJ, 1D.csv", "强生"),
    "LLY": ("lly", "LLY, 1D.csv", "礼来"),
    "GILD": ("gild", "GILD, 1D.csv", "吉利德"),
    "IBB": ("ibb", "IBB, 1D.csv", "IBB生物科技ETF"),
    "XBI": ("xbi", "XBI, 1D.csv", "XBI生物科技ETF"),
    "XLV": ("xlv", "XLV, 1D.csv", "XLV医疗保健ETF"),
    "SPY": ("spy", "SPY, 1D.csv", "SPY标普500ETF"),
}

BIG_PHARMA = ["ABBV", "MRK", "JNJ", "LLY", "GILD"]
BENCH = ["IBB", "XBI", "XLV", "SPY"]

def load(key: str) -> pd.DataFrame:
    d, fname, _ = TICKERS[key]
    p = os.path.join(DATA, d, fname)
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["close"].pct_change() * 100
    return df

def pearson_spearman(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, None, len(a)
    p = float(np.corrcoef(a, b)[0, 1])
    from scipy.stats import spearmanr
    s = float(spearmanr(a, b).statistic)
    return p, s, len(a)

def stats_block(w: pd.DataFrame, x: pd.DataFrame, name: str, start=None, end=None):
    """w: 药明, x: 对比标的。start/end 可选过滤"""
    if start is not None and end is not None:
        ww = w[(w["date"] >= start) & (w["date"] <= end)]
        xx = x[(x["date"] >= start) & (x["date"] <= end)]
    elif start is not None:
        ww = w[w["date"] >= start]
        xx = x[x["date"] >= start]
    elif end is not None:
        ww = w[w["date"] <= end]
        xx = x[x["date"] <= end]
    else:
        ww, xx = w, x
    m = pd.merge(ww[["date", "ret", "close"]], xx[["date", "ret", "close"]],
                 on="date", suffixes=("_w", "_x")).dropna()
    if len(m) < 10:
        return {"name": name, "n": 0}
    p, s, n = pearson_spearman(m["ret_w"].values, m["ret_x"].values)
    xv, yv = m["ret_x"].values, m["ret_w"].values
    beta = float(np.cov(yv, xv)[0, 1] / np.var(xv))
    resid = yv - beta * xv
    r2 = p * p if p is not None else 0
    ret_w = (m["close_w"].iloc[-1] / m["close_w"].iloc[0] - 1) * 100
    ret_x = (m["close_x"].iloc[-1] / m["close_x"].iloc[0] - 1) * 100
    return {
        "name": name, "n": n,
        "start": str(m["date"].iloc[0].date()), "end": str(m["date"].iloc[-1].date()),
        "pearson": round(p, 3) if p is not None else None,
        "spearman": round(s, 3) if s is not None else None,
        "r2": round(r2, 3), "beta": round(beta, 3),
        "resid_vol": round(float(resid.std()), 3),
        "w_ret": round(float(ret_w), 2), "x_ret": round(float(ret_x), 2),
        "w_vol": round(float(m["ret_w"].std()), 3), "x_vol": round(float(m["ret_x"].std()), 3),
        "excess": round(float(ret_w - ret_x), 2),
    }

def lag_corr(w_ret, x_ret, dates, max_lag=5):
    """corr(r_wuxi(t), r_x(t+k))：k>0 表示 x 领先 wuxi"""
    df = pd.DataFrame({"d": dates, "w": w_ret, "x": x_ret}).dropna()
    out = []
    for k in range(-max_lag, max_lag + 1):
        if k == 0:
            a, b = df["w"].values, df["x"].values
        elif k > 0:
            a, b = df["w"].values[: -k], df["x"].values[k:]
        else:
            a, b = df["w"].values[-k:], df["x"].values[:k]
        m = ~(np.isnan(a) | np.isnan(b))
        if m.sum() < 30:
            out.append({"lag": k, "corr": None})
            continue
        out.append({"lag": k, "corr": round(float(np.corrcoef(a[m], b[m])[0, 1]), 3)})
    return out

def main():
    data = {k: load(k) for k in TICKERS}
    w = data[TARGET]
    wa = data[TARGET_A]

    # ---- 1. 配对相关性(全期 + 分段) ----
    segments = [
        ("全期", None, None),
        ("2025-09 前", None, SPLIT_2025_09 - pd.Timedelta(days=1)),
        ("2025-09 起", SPLIT_2025_09, None),
        ("2026-02 前", None, SPLIT_2026_02 - pd.Timedelta(days=1)),
        ("2026-02 起(1260H冲击期)", SPLIT_2026_02, None),
        ("2026-06 起(列名+禁令期)", SPLIT_2026_06, None),
    ]
    pairwise = {}
    for k in BIG_PHARMA + BENCH:
        x = data[k]
        blocks = []
        for sname, st, en in segments:
            b = stats_block(w, x, sname, st, en)
            blocks.append(b)
        pairwise[k] = blocks

    # ---- 2. 滚动 60 日相关性(2023 起) ----
    m0 = pd.merge(w[["date", "ret"]], data["XBI"][["date", "ret"]],
                  on="date", suffixes=("_w", "_xbi")).dropna()
    rolling60 = []
    for k in BIG_PHARMA + BENCH:
        m = pd.merge(w[["date", "ret"]], data[k][["date", "ret"]],
                     on="date", suffixes=("_w", "_x")).dropna()
        m = m[m["date"] >= "2023-01-01"]
        corr = m["ret_w"].rolling(60).corr(m["ret_x"]) * 100
        rolling60.append({
            "ticker": k, "name": TICKERS[k][2],
            "series": [{"date": str(d.date()), "corr": None if np.isnan(v) else round(float(v), 2)}
                       for d, v in zip(m["date"], corr)]
        })

    # ---- 3. 领先/滞后交叉相关(全期) ----
    lagcorr = []
    for k in BIG_PHARMA + BENCH:
        m = pd.merge(w[["date", "ret"]], data[k][["date", "ret"]],
                     on="date", suffixes=("_w", "_x")).dropna()
        lagcorr.append({"ticker": k, "name": TICKERS[k][2],
                        "series": lag_corr(m["ret_w"].values, m["ret_x"].values, m["date"].values)})

    # ---- 4. 月度相关性(近 3 年) ----
    mm = pd.merge(w[["date", "ret"]], data["XBI"][["date", "ret"]],
                  on="date", suffixes=("_w", "_xbi")).dropna().set_index("date")
    monthly_all = {}
    for k in BIG_PHARMA + BENCH:
        m2 = pd.merge(w[["date", "ret"]], data[k][["date", "ret"]],
                      on="date", suffixes=("_w", "_x")).dropna().set_index("date")
        m2 = m2[m2.index >= "2023-08-01"]
        mc = (m2[["ret_w", "ret_x"]].groupby(pd.Grouper(freq="ME"))
              .corr().unstack()["ret_w"]["ret_x"] * 100).dropna()
        monthly_all[k] = [{"month": str(kk.date())[:7], "corr": round(float(v), 2)} for kk, v in mc.items()]

    # ---- 5. 归一化净值(2021 起) ----
    norm_net = {}
    for k in BIG_PHARMA + BENCH:
        m = pd.merge(w[["date", "close"]], data[k][["date", "close"]],
                     on="date", suffixes=("_w", "_x"))
        m = m[m["date"] >= "2021-01-01"]
        m["w_norm"] = m["close_w"] / m["close_w"].iloc[0] * 100
        m["x_norm"] = m["close_x"] / m["close_x"].iloc[0] * 100
        norm_net[k] = {
            "name": TICKERS[k][2],
            "series": [{"date": str(d.date()),
                        "wuxi": round(float(a), 2), "x": round(float(b), 2)}
                       for d, a, b in zip(m["date"], m["w_norm"], m["x_norm"])]
        }
    # 药明自身 + 基准净值(单独, 供主图)
    net_main = {}
    for k in ["WUXIH", "WUXIA", "IBB", "XBI", "XLV", "SPY"]:
        df = data[k][data[k]["date"] >= "2021-01-01"]
        df = df.copy()
        df["norm"] = df["close"] / df["close"].iloc[0] * 100
        net_main[k] = {"name": TICKERS[k][2],
                       "series": [{"date": str(d.date()), "v": round(float(v), 2)}
                                  for d, v in zip(df["date"], df["norm"])]}

    # ---- 6. 超额收益四档(事件分段) ----
    excess_segs = [
        ("2021-01-01~2024-12-31", pd.Timestamp("2021-01-01"), pd.Timestamp("2024-12-31")),
        ("2025-01-01~2025-08-31", pd.Timestamp("2025-01-01"), pd.Timestamp("2025-08-31")),
        ("2025-09-01~2026-02-01", SPLIT_2025_09, SPLIT_2026_02 - pd.Timedelta(days=1)),
        ("2026-02-02~2026-06-08", SPLIT_2026_02, SPLIT_2026_06 - pd.Timedelta(days=1)),
        ("2026-06-08 以来", SPLIT_2026_06, None),
    ]
    excess = []
    for k in BIG_PHARMA + BENCH:
        row = {"ticker": k, "name": TICKERS[k][2], "segs": []}
        for sname, st, en in excess_segs:
            b = stats_block(w, data[k], sname, st, en)
            row["segs"].append({**b, "name": sname})
        excess.append(row)

    # ---- 7. 关键事件窗口 (-5..+5 交易日) ----
    events = [
        ("2024-03-06", "BIOSECURE 参议院版提出(市场首波恐慌)"),
        ("2024-05-15", "众议院委员会通过 BIOSECURE"),
        ("2024-09-09", "众议院全会通过 BIOSECURE(306-81)"),
        ("2025-12-18", "FY2026 NDAA 签署, BIOSECURE 生效"),
        ("2026-02-13", "1260H 短暂公示后 1 小时撤回"),
        ("2026-06-08", "正式列入 1260H 名单"),
        ("2026-06-11", "起诉美国国防部"),
        ("2026-08-07", "法院批准初步禁令"),
    ]
    event_windows = []
    for ed, desc in events:
        t = pd.Timestamp(ed)
        # 找药明 H 上最近交易日 <= t
        idx = w[w["date"] <= t]["date"]
        if len(idx) == 0:
            continue
        t0 = idx.iloc[-1]
        pos = w.index[w["date"] == t0][0]
        lo, hi = max(0, pos - 5), min(len(w), pos + 6)
        seg = w.iloc[lo:hi]
        win = {"date": ed, "desc": desc, "wuxi": [], "xbi": [], "ibb": []}
        for _, r in seg.iterrows():
            d = r["date"]
            wuxi_v = r["close"]
            xbi_v = data["XBI"][data["XBI"]["date"] == d]["close"]
            ibb_v = data["IBB"][data["IBB"]["date"] == d]["close"]
            win["wuxi"].append(round(float(wuxi_v), 2))
            win["xbi"].append(None if len(xbi_v) == 0 else round(float(xbi_v.iloc[0]), 2))
            win["ibb"].append(None if len(ibb_v) == 0 else round(float(ibb_v.iloc[0]), 2))
        # 归一化到事件日 = 100
        base_w, base_x, base_i = win["wuxi"][5], win["xbi"][5], win["ibb"][5]
        win["wuxi_n"] = [round(v / base_w * 100, 2) if v else None for v in win["wuxi"]]
        win["xbi_n"] = [round(v / base_x * 100, 2) if v else None for v in win["xbi"]]
        win["ibb_n"] = [round(v / base_i * 100, 2) if v else None for v in win["ibb"]]
        win["dates"] = [str(d.date()) for d in seg["date"]]
        win["wuxi_5d"] = round((win["wuxi_n"][-1] - 100), 2) if len(win["wuxi_n"]) > 5 else None
        win["xbi_5d"] = round((win["xbi_n"][-1] - 100), 2) if len(win["xbi_n"]) > 5 else None
        win["ibb_5d"] = round((win["ibb_n"][-1] - 100), 2) if len(win["ibb_n"]) > 5 else None
        event_windows.append(win)

    # ---- 8. A/H 对照 ----
    m_ah = pd.merge(w[["date", "ret", "close"]], wa[["date", "ret", "close"]],
                    on="date", suffixes=("_h", "_a")).dropna()
    p_ah, s_ah, n_ah = pearson_spearman(m_ah["ret_h"].values, m_ah["ret_a"].values)
    ah_block = {"pearson": round(p_ah, 3), "spearman": round(s_ah, 3), "n": n_ah,
                "start": str(m_ah["date"].iloc[0].date()), "end": str(m_ah["date"].iloc[-1].date())}
    # A/H 分段
    ah_segs = []
    for sname, st, en in segments:
        b = stats_block(w, wa, sname, st, en)
        ah_segs.append(b)

    out = {
        "meta": {
            "target": "药明康德H(2359.HK) 主分析; 药明康德A(603259.SS) 对照",
            "source": "Yahoo Finance 日线(收盘价, 未复权close用于相对走势)",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
            "segments": [s[0] for s in segments],
        },
        "pairwise": pairwise,
        "rolling60": rolling60,
        "lagcorr": lagcorr,
        "monthly": monthly_all,
        "norm_net": norm_net,
        "net_main": net_main,
        "excess": excess,
        "events": event_windows,
        "ah": {"block": ah_block, "segs": ah_segs},
    }
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "wuxi_bigpharma.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", path)

    # 控制台摘要
    print("\n=== 全期相关性(药明H vs X) ===")
    for k in BIG_PHARMA + BENCH:
        b = pairwise[k][0]
        print(f"{k:5s} {TICKERS[k][2]:8s} pearson={b['pearson']} spearman={b['spearman']} beta={b['beta']} r2={b['r2']} n={b['n']}")
    print("\n=== 2026-02 起(1260H冲击期) ===")
    for k in BIG_PHARMA + BENCH:
        b = pairwise[k][4]
        print(f"{k:5s} pearson={b['pearson']} n={b['n']} wuxi={b['w_ret']}% x={b['x_ret']}% excess={b['excess']}pp")
    print("\n=== A/H 全期 ===", ah_block)
    print("\n=== 事件窗口(药明H 5日) ===")
    for ev in event_windows:
        print(f"{ev['date']} {ev['desc'][:24]:26s} wuxi={ev['wuxi_5d']}% xbi={ev['xbi_5d']}% ibb={ev['ibb_5d']}%")

if __name__ == "__main__":
    main()
