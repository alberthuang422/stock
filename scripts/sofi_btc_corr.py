#!/usr/bin/env python3
"""SOFI / XYZ(Block) vs BTC(USDT) 相关性分析 —— 按日历季度分阶段（2023Q1 起）。

主分析 SOFI×BTC，对照组 XYZ×BTC（用户疑问：sofi/xyz 近期上涨是否由 BTC 驱动）。

数据:
  - SOFI / XYZ: data/<tk>/<TK>, 1D.csv (Yahoo Finance, adj_close 复权, 美东交易日)
  - BTC:  data/btcusdt/BTCUSDT, 1D.csv (Binance BTCUSDT 日线, close, UTC 日 K)

口径:
  - 主口径 60 日滚动相关（项目惯例），另附 252 日滚动作稳健性
  - 季度分阶段: 2023Q1 ~ 2026Q3，逐季 Pearson R / Spearman / β / R² / 显著带 ±1.96/√(n−2)
  - R 与 β 同列输出（项目口径）
  - 相关系数存 0~1 小数（不做 ×100）
输出 results/sofi_btc_corr.json
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
START = pd.Timestamp("2023-01-01")


def load_equity(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change() * 100
    return df[["date", "adj_close", "ret"]]


def load_btc():
    p = os.path.join(DATA, "btcusdt", "BTCUSDT, 1D.csv")
    df = pd.read_csv(p, parse_dates=["time"]).rename(columns={"time": "date"})
    df = df.sort_values("date").reset_index(drop=True)
    df = df[["date", "close"]].rename(columns={"close": "btc_close"})
    df["ret"] = df["btc_close"].pct_change() * 100
    return df


def pearson_spearman(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    if len(a) < 3:
        return None, None, len(a)
    from scipy.stats import spearmanr
    p = float(np.corrcoef(a, b)[0, 1])
    s = float(spearmanr(a, b).statistic)
    return p, s, len(a)


def beta_r2(x, y):
    """y 对 x 的 beta 与 R²（x=解释变量 BTC, y=被解释标的）"""
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 3:
        return None, None
    beta = float(np.cov(y, x)[0, 1] / np.var(x))
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    return beta, r2


def seg_stats(df, label):
    """df 需含列: date, ret_ek(标的收益), ret_b, px_ek, btc_close"""
    n = len(df)
    r, s, _ = pearson_spearman(df["ret_ek"].values, df["ret_b"].values)
    b, r2 = beta_r2(df["ret_b"].values, df["ret_ek"].values)
    band = 1.96 / np.sqrt(n - 2) if n > 3 else None
    ret_ek = (df["px_ek"].iloc[-1] / df["px_ek"].iloc[0] - 1) * 100
    ret_b = (df["btc_close"].iloc[-1] / df["btc_close"].iloc[0] - 1) * 100
    return {
        "label": label, "n": int(n),
        "r": round(r, 4) if r is not None else None,
        "spearman": round(s, 4) if s is not None else None,
        "beta": round(b, 4) if b is not None else None,
        "r2": round(r2, 4) if r2 is not None else None,
        "sig_band": round(band, 4) if band is not None else None,
        "sig": bool(band is not None and r is not None and abs(r) > band),
        "ret_ek": round(float(ret_ek), 2), "ret_btc": round(float(ret_b), 2),
        "start": str(df["date"].iloc[0].date()), "end": str(df["date"].iloc[-1].date()),
    }


def build_pair(df_ek, btc, name):
    m = pd.merge(df_ek, btc, on="date", suffixes=("_ek", "_b")).dropna()
    m = m[m["date"] >= START].reset_index(drop=True)
    m = m.rename(columns={"adj_close": "px_ek", "ret_ek": "ret_ek"})
    print(f"[{name}] 窗口 {m['date'].iloc[0].date()} ~ {m['date'].iloc[-1].date()}  n={len(m)}")

    # 全期
    full_r, full_s, _ = pearson_spearman(m["ret_ek"].values, m["ret_b"].values)
    full_b, full_r2 = beta_r2(m["ret_b"].values, m["ret_ek"].values)
    full_ret_ek = (m["px_ek"].iloc[-1] / m["px_ek"].iloc[0] - 1) * 100
    full_ret_b = (m["btc_close"].iloc[-1] / m["btc_close"].iloc[0] - 1) * 100
    full = {
        "r": round(full_r, 4), "spearman": round(full_s, 4),
        "beta": round(full_b, 4) if full_b is not None else None,
        "r2": round(full_r2, 4) if full_r2 is not None else None,
        "ret_ek": round(float(full_ret_ek), 2), "ret_btc": round(float(full_ret_b), 2),
    }

    # 季度
    quarters = [seg_stats(grp, str(k)) for k, grp in m.groupby(m["date"].dt.to_period("Q")) if len(grp) >= 5]
    # 年度
    yearly = [seg_stats(grp, f"{k}年") for k, grp in m.groupby(m["date"].dt.year) if len(grp) >= 20]

    # 滚动 60/252 R 与 β
    def rolling(df, win):
        out = []
        for i in range(win - 1, len(df)):
            w = df.iloc[i - win + 1: i + 1]
            r, _, _ = pearson_spearman(w["ret_ek"].values, w["ret_b"].values)
            b, r2 = beta_r2(w["ret_b"].values, w["ret_ek"].values)
            out.append({"date": str(df["date"].iloc[i].date()),
                        "r": round(r, 4) if r is not None else None,
                        "beta": round(b, 4) if b is not None else None})
        return out
    roll60 = rolling(m, 60)
    roll252 = rolling(m, 252)

    # 归一化价格（窗口起点 = 100）
    e0 = m["px_ek"].iloc[0]
    b0 = m["btc_close"].iloc[0]
    norm = [{"date": str(d.date()), "ek": round(float(e / e0 * 100), 2), "btc": round(float(b / b0 * 100), 2)}
            for d, e, b in zip(m["date"], m["px_ek"], m["btc_close"])]

    # BTC 单日 |ret|>=2% 日的标的平均表现
    big = m[np.abs(m["ret_b"]) >= 2.0]
    up, dn = big[big["ret_b"] >= 2.0], big[big["ret_b"] <= -2.0]
    btc_days = {
        "n_up": int(len(up)), "ek_avg_up": round(float(up["ret_ek"].mean()), 2) if len(up) else None,
        "n_dn": int(len(dn)), "ek_avg_dn": round(float(dn["ret_ek"].mean()), 2) if len(dn) else None,
    }

    # 最近 20 交易日窗口
    w20 = m.tail(20)
    r20 = float(w20["ret_ek"].corr(w20["ret_b"]))
    b20, r2_20 = beta_r2(w20["ret_b"].values, w20["ret_ek"].values)
    last20 = {
        "start": str(w20["date"].iloc[0].date()), "end": str(w20["date"].iloc[-1].date()), "n": int(len(w20)),
        "r": round(r20, 4), "beta": round(b20, 4) if b20 is not None else None,
        "r2": round(r2_20, 4) if r2_20 is not None else None,
        "ret_ek": round(float((w20["px_ek"].iloc[-1] / w20["px_ek"].iloc[0] - 1) * 100), 2),
        "ret_btc": round(float((w20["btc_close"].iloc[-1] / w20["btc_close"].iloc[0] - 1) * 100), 2),
        "sig_band": round(1.96 / np.sqrt(len(w20) - 2), 4),
    }

    return {
        "name": name, "window": {"start": str(m["date"].iloc[0].date()), "end": str(m["date"].iloc[-1].date()), "n": int(len(m))},
        "full": full, "quarters": quarters, "yearly": yearly,
        "rolling60": roll60, "rolling252": roll252, "norm": norm,
        "btc_days": btc_days, "last20": last20,
    }


def main():
    btc = load_btc()
    out = {
        "sofi": build_pair(load_equity("SOFI"), btc, "SOFI"),
        "xyz": build_pair(load_equity("XYZ"), btc, "XYZ"),
        "meta": {
            "sofi": "SoFi Technologies (金融科技, 数字银行/借贷/投资)",
            "xyz": "Block Inc. (原 Square, 支付/金融科技, 持币资产)",
            "btc": "Bitcoin (BTCUSDT, Binance 现货日线)",
            "sources": {
                "equity": "Yahoo Finance 日线 adj_close 复权 (美东交易日)",
                "btc": "Binance BTCUSDT 日线 close (UTC 日 K, 7x24)",
            },
            "note": "日期按字符串对齐: 标的美股交易日, BTC 为 UTC 日 K, 交集为共同日期; 日收益 pct_change×100; "
                    "相关/β 按日收益计算; 显著带 ±1.96/√(n−2); R 与 β 同列",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        },
    }
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "sofi_btc_corr.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("saved:", p)

    for name in ["SOFI", "XYZ"]:
        d = out[name.lower()]
        print(f"\n== {name} 全期 ==")
        print(f"r={d['full']['r']} spearman={d['full']['spearman']} beta={d['full']['beta']} r2={d['full']['r2']} "
              f"{name} {d['full']['ret_ek']}% BTC {d['full']['ret_btc']}%")
        print(f"== {name} 季度 ==")
        for q in d["quarters"]:
            print(f"{q['label']} n={q['n']} r={q['r']} sig={q['sig']} beta={q['beta']} r2={q['r2']} "
                  f"{name} {q['ret_ek']:+.1f}% BTC {q['ret_btc']:+.1f}%")
        print(f"== {name} 近20交易日 ==", d["last20"])
        print(f"== {name} BTC>=2% 日 ==", d["btc_days"])


if __name__ == "__main__":
    main()
