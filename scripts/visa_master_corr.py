# -*- coding: utf-8 -*-
"""V/MA（银行卡网络）× KBWB（银行板块ETF） + × QQQ/XLK（科技板块）相关性分析。

数据：data/v/ data/ma/ data/kbwb/ data/qqq/ data/xlk/（Yahoo 1D, adj_close 口径）
口径：60 日滚动为主口径（项目长期规则）；全期 + 分阶段 + 近3年/近1年 + 2026年以来
维度：
  1) 日收益 Pearson/Spearman 相关（V/MA 不同维度：vs 银行板块、vs 科技板块）
  2) 滚动 60 日相关序列（主口径）
  3) β / R² / 残差（以 KBWB/QQQ/XLK 为板块代理）
  4) 阶段收益/波动/回撤/夏普对比
  5) 相对强弱比值（KBWB/V 等）
  6) 同涨同跌占比 + 条件收益
  7) 2026-02 分界前后 Fisher z 检验（沿用项目口径）
输出 results/visa_master_corr.json
"""
import os
import json
import math

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
SPLIT = pd.Timestamp("2026-02-01")


def load(ticker: str) -> pd.DataFrame:
    p = os.path.join(DATA, ticker.lower(), f"{ticker.upper()}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change() * 100
    return df


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    mask = ~np.isnan(a) & ~np.isnan(b)
    a, b = a[mask], b[mask]
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    return float(np.corrcoef(ra, rb)[0, 1])


def pair_stats(x_df, y_df, xname, yname, name) -> dict:
    """x / y 两标的日收益相关性块"""
    m = pd.merge(x_df[["date", "ret"]], y_df[["date", "ret"]],
                 on="date", suffixes=(f"_{xname}", f"_{yname}")).dropna()
    if len(m) < 5:
        return {"name": name, "n": 0}
    x = m[f"ret_{xname}"].values
    y = m[f"ret_{yname}"].values
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman_v = spearman(x, y)
    beta = float(np.cov(y, x)[0, 1] / np.var(x))   # y 对 x 的 beta
    r2 = pearson * pearson
    resid = y - beta * x
    p_same = float(np.mean(np.sign(x) == np.sign(y)))
    up_mask = x > 0
    dn_mask = x < 0
    y_up = float(y[up_mask].mean()) if up_mask.sum() > 5 else None
    y_dn = float(y[dn_mask].mean()) if dn_mask.sum() > 5 else None
    x_up = float(x[up_mask].mean()) if up_mask.sum() > 5 else None
    x_dn = float(x[dn_mask].mean()) if dn_mask.sum() > 5 else None
    return {
        "name": name,
        "n": int(len(m)),
        "start": str(m["date"].iloc[0].date()),
        "end": str(m["date"].iloc[-1].date()),
        "pearson": round(pearson, 4),
        "spearman": round(spearman_v, 4),
        "beta": round(beta, 3),
        "r2": round(r2, 4),
        "resid_vol": round(float(resid.std()), 3),
        "resid_corr": round(float(np.corrcoef(resid, x)[0, 1]), 4),
        "p_same_dir": round(float(p_same) * 100, 1),
        "x_up_y_avg": round(y_up, 3) if y_up is not None else None,
        "x_dn_y_avg": round(y_dn, 3) if y_dn is not None else None,
        "x_up_avg": round(x_up, 3) if x_up is not None else None,
        "x_dn_avg": round(x_dn, 3) if x_dn is not None else None,
    }


def fisher_z(r1, n1, r2, n2):
    from math import atanh, sqrt, erf
    z = (atanh(r1) - atanh(r2)) / sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return {"z": round(float(z), 3), "p_value": round(float(p), 4), "sig": bool(p < 0.05)}


def price_stats(merged, xcol, ycol, xname, yname, name) -> dict:
    out = {"name": name}
    for sym, col in ((xname, xcol), (yname, ycol)):
        sub = merged.dropna(subset=[col])
        if len(sub) < 2:
            out[sym] = None
            continue
        s = sub[col]
        r = s.pct_change().dropna()
        cummax = s.cummax()
        dd = float((s / cummax - 1).min())
        total = float(s.iloc[-1] / s.iloc[0] - 1) * 100
        ann_ret = float((s.iloc[-1] / s.iloc[0]) ** (252 / len(s)) - 1) * 100
        vol = float(r.std() * math.sqrt(252)) * 100
        out[sym] = {
            "total_ret": round(total, 1),
            "ann_ret": round(ann_ret, 1),
            "ann_vol": round(vol, 1),
            "max_dd": round(dd * 100, 1),
            "sharpe": round(ann_ret / vol, 2) if vol > 0 else None,
            "n_days": int(len(s)),
        }
    return out


def clean(o):
    """json 序列化前清理：NaN→None, numpy 标量→原生"""
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return o


def main():
    v = load("V")
    ma = load("MA")
    kbwb = load("KBWB")
    qqq = load("QQQ")
    xlk = load("XLK")

    out = {
        "split": str(SPLIT.date()),
        "meta": {
            "note": "V/MA 为银行卡网络（支付清算赛道），KBWB 为银行板块 ETF（等权覆盖传统银行+大行），QQQ/XLK 为科技板块。相关性口径=日收益，60 日滚动为主口径。",
            "source": "Yahoo Finance 日线(复权收盘 adj_close)",
            "fetched": str(pd.Timestamp.now(tz="Asia/Shanghai").date()),
        },
        "pairs": {},
    }

    # ================= 任务1: V/MA × KBWB =================
    for sym in ("V", "MA"):
        x = v if sym == "V" else ma
        m = pd.merge(x[["date", "adj_close", "ret"]], kbwb[["date", "adj_close", "ret"]],
                     on="date", suffixes=(f"_{sym.lower()}", "_kbwb")).dropna().reset_index(drop=True)
        m = m.rename(columns={f"adj_close_{sym.lower()}": "close_x", "adj_close_kbwb": "close_y",
                              f"ret_{sym.lower()}": "ret_x", "ret_kbwb": "ret_y"})
        m["ratio"] = m["close_y"] / m["close_x"]   # KBWB / V 或 MA

        blocks = [
            pair_stats(x, kbwb, sym.lower(), "kbwb", "全期"),
            pair_stats(x[x["date"] < SPLIT], kbwb[kbwb["date"] < SPLIT], sym.lower(), "kbwb", f"分界前 ({SPLIT.date()} 前)"),
            pair_stats(x[x["date"] >= SPLIT], kbwb[kbwb["date"] >= SPLIT], sym.lower(), "kbwb", f"分界后 ({SPLIT.date()} 起)"),
            pair_stats(x[x["date"] >= "2023-01-01"], kbwb[kbwb["date"] >= "2023-01-01"], sym.lower(), "kbwb", "近 3 年"),
            pair_stats(x[x["date"] >= "2025-08-21"], kbwb[kbwb["date"] >= "2025-08-21"], sym.lower(), "kbwb", "近 1 年"),
            pair_stats(x[x["date"] >= "2026-01-01"], kbwb[kbwb["date"] >= "2026-01-01"], sym.lower(), "kbwb", "2026 年以来"),
        ]
        fisher = fisher_z(blocks[1]["pearson"], blocks[1]["n"], blocks[2]["pearson"], blocks[2]["n"])

        # 滚动 60 日（主口径）
        roll = m["ret_x"].rolling(60).corr(m["ret_y"])
        rolling60 = [{"date": str(d.date()), "corr": None if np.isnan(v) else round(float(v), 3)}
                     for d, v in zip(m["date"], roll)]
        # 最近 60 个交易日的滚动值
        roll_n = roll.dropna()
        latest_roll = round(float(roll_n.iloc[-1]), 3)
        roll_mean = round(float(roll_n.mean()), 3)
        roll_min = round(float(roll_n.min()), 3)
        roll_min_date = str(m["date"][roll_n.idxmin()].date())
        roll_max = round(float(roll_n.max()), 3)
        roll_max_date = str(m["date"][roll_n.idxmax()].date())

        # 月频相关
        mm = m.set_index("date")
        monthly = (mm[["ret_x", "ret_y"]].groupby(pd.Grouper(freq="ME"))
                   .corr().unstack()["ret_x"]["ret_y"]).dropna()
        monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 3)} for k, v in monthly.items()]
        monthly_3y = [x_ for x_ in monthly_series if x_["month"] >= "2023-08"]

        # 分年相关
        yearly_corr = {}
        for y, g in m.groupby(m["date"].dt.year):
            g2 = g.dropna(subset=["ret_x", "ret_y"])
            if len(g2) > 20:
                yearly_corr[int(y)] = round(float(g2["ret_x"].corr(g2["ret_y"])), 3)

        # 价格统计
        def seg(start=None):
            sub = m if start is None else m[m["date"] >= start]
            return price_stats(sub, "close_x", "close_y", sym, "kbwb", str(sub["date"].iloc[0].date()) if len(sub) else "")

        price_blocks = {"full": seg(), "after_split": seg("2026-02-01"),
                        "last1y": seg("2025-08-21"), "ytd": seg("2026-01-01")}

        # 相对强弱 KBWB/标的
        ratio = m["ratio"] / m["ratio"].iloc[0]
        ratio_info = {
            "start_ratio": round(float(m["ratio"].iloc[0]), 4),
            "latest_ratio": round(float(m["ratio"].iloc[-1]), 4),
            "norm_latest": round(float(ratio.iloc[-1]), 3),
            "max": round(float(ratio.max()), 3), "max_date": str(m["date"][ratio.idxmax()].date()),
            "min": round(float(ratio.min()), 3), "min_date": str(m["date"][ratio.idxmin()].date()),
        }

        # 年度收益
        yearly = {}
        for y, g in m.groupby(m["date"].dt.year):
            row = {}
            for k2, col in (("x", "close_x"), ("y", "close_y")):
                s = g[col]
                row[k2] = round(float(s.iloc[-1] / s.iloc[0] - 1) * 100, 1)
            row["diff"] = round(row["x"] - row["y"], 1)
            yearly[int(y)] = row

        # 散点（近3年分色）
        sc = m[m["date"] >= "2023-01-01"]
        scatter = [{"date": str(d.date()), "x": round(float(rx), 3), "y": round(float(ry), 3),
                    "after": bool(d >= SPLIT)}
                   for d, rx, ry in zip(sc["date"], sc["ret_x"], sc["ret_y"])]

        # 2026 年以来归一化
        recent = m[m["date"] >= "2026-01-01"].copy()
        nx = recent["close_x"] / recent["close_x"].iloc[0]
        ny = recent["close_y"] / recent["close_y"].iloc[0]
        series_2026 = [{"date": str(d.date()), "x": round(float(a), 4), "y": round(float(b), 4)}
                       for d, a, b in zip(recent["date"], nx, ny)]

        # 全期归一化（每 10 交易采样）
        nX = m["close_x"] / m["close_x"].iloc[0]
        nY = m["close_y"] / m["close_y"].iloc[0]
        full_series = [{"date": str(d.date()), "x": round(float(a), 3), "y": round(float(b), 3)}
                       for d, a, b in zip(m["date"][::10], nX[::10], nY[::10])]

        # 同向占比近1年
        last1y = m[m["date"] >= "2025-08-21"]
        p_same1y = float(np.mean(np.sign(last1y["ret_x"]) == np.sign(last1y["ret_y"]))) * 100

        out["pairs"][sym] = {
            "xname": sym, "yname": "KBWB",
            "period": {"start": str(m["date"].iloc[0].date()), "end": str(m["date"].iloc[-1].date()),
                       "n": int(len(m))},
            "blocks": blocks, "fisher": fisher,
            "rolling60": rolling60, "latest_roll": latest_roll,
            "roll_mean": roll_mean, "roll_min": roll_min, "roll_min_date": roll_min_date,
            "roll_max": roll_max, "roll_max_date": roll_max_date,
            "monthly": monthly_series,
            "monthly_mean_full": round(float(monthly.mean()), 3),
            "monthly_mean_3y": round(float(np.mean([x_["corr"] for x_ in monthly_3y])), 3),
            "monthly_latest": round(float(monthly.iloc[-1]), 3),
            "yearly_corr": yearly_corr,
            "price_blocks": price_blocks, "ratio": ratio_info,
            "yearly": yearly, "years": sorted(yearly),
            "scatter": scatter, "series_2026": series_2026, "full_series": full_series,
            "same_dir_1y": round(p_same1y, 1),
        }

    # ================= 任务2: V/MA × QQQ/XLK =================
    for sym in ("V", "MA"):
        x = v if sym == "V" else ma
        for tech, tname in (("QQQ", "QQQ"), ("XLK", "XLK")):
            t = qqq if tech == "QQQ" else xlk
            tk = tech.lower()
            m = pd.merge(x[["date", "adj_close", "ret"]], t[["date", "adj_close", "ret"]],
                         on="date", suffixes=(f"_{sym.lower()}", f"_{tk}")).dropna().reset_index(drop=True)
            m = m.rename(columns={f"adj_close_{sym.lower()}": "close_x", f"adj_close_{tk}": "close_y",
                                  f"ret_{sym.lower()}": "ret_x", f"ret_{tk}": "ret_y"})
            m["ratio"] = m["close_y"] / m["close_x"]

            blocks = [
                pair_stats(x, t, sym.lower(), tk, "全期"),
                pair_stats(x[x["date"] < SPLIT], t[t["date"] < SPLIT], sym.lower(), tk, f"分界前 ({SPLIT.date()} 前)"),
                pair_stats(x[x["date"] >= SPLIT], t[t["date"] >= SPLIT], sym.lower(), tk, f"分界后 ({SPLIT.date()} 起)"),
                pair_stats(x[x["date"] >= "2023-01-01"], t[t["date"] >= "2023-01-01"], sym.lower(), tk, "近 3 年"),
                pair_stats(x[x["date"] >= "2025-08-21"], t[t["date"] >= "2025-08-21"], sym.lower(), tk, "近 1 年"),
                pair_stats(x[x["date"] >= "2026-01-01"], t[t["date"] >= "2026-01-01"], sym.lower(), tk, "2026 年以来"),
            ]
            fisher = fisher_z(blocks[1]["pearson"], blocks[1]["n"], blocks[2]["pearson"], blocks[2]["n"])

            roll = m["ret_x"].rolling(60).corr(m["ret_y"])
            rolling60 = [{"date": str(d.date()), "corr": None if np.isnan(v) else round(float(v), 3)}
                         for d, v in zip(m["date"], roll)]
            roll_n = roll.dropna()
            latest_roll = round(float(roll_n.iloc[-1]), 3)
            roll_mean = round(float(roll_n.mean()), 3)
            roll_min = round(float(roll_n.min()), 3)
            roll_min_date = str(m["date"][roll_n.idxmin()].date())
            roll_max = round(float(roll_n.max()), 3)
            roll_max_date = str(m["date"][roll_n.idxmax()].date())

            mm = m.set_index("date")
            monthly = (mm[["ret_x", "ret_y"]].groupby(pd.Grouper(freq="ME"))
                       .corr().unstack()["ret_x"]["ret_y"]).dropna()
            monthly_series = [{"month": str(k.date())[:7], "corr": round(float(v), 3)} for k, v in monthly.items()]
            monthly_3y = [x_ for x_ in monthly_series if x_["month"] >= "2023-08"]

            yearly_corr = {}
            for y, g in m.groupby(m["date"].dt.year):
                g2 = g.dropna(subset=["ret_x", "ret_y"])
                if len(g2) > 20:
                    yearly_corr[int(y)] = round(float(g2["ret_x"].corr(g2["ret_y"])), 3)

            def seg(start=None):
                sub = m if start is None else m[m["date"] >= start]
                return price_stats(sub, "close_x", "close_y", sym, tname, str(sub["date"].iloc[0].date()) if len(sub) else "")

            price_blocks = {"full": seg(), "after_split": seg("2026-02-01"),
                            "last1y": seg("2025-08-21"), "ytd": seg("2026-01-01")}

            ratio = m["ratio"] / m["ratio"].iloc[0]
            ratio_info = {
                "start_ratio": round(float(m["ratio"].iloc[0]), 4),
                "latest_ratio": round(float(m["ratio"].iloc[-1]), 4),
                "norm_latest": round(float(ratio.iloc[-1]), 3),
                "max": round(float(ratio.max()), 3), "max_date": str(m["date"][ratio.idxmax()].date()),
                "min": round(float(ratio.min()), 3), "min_date": str(m["date"][ratio.idxmin()].date()),
            }

            yearly = {}
            for y, g in m.groupby(m["date"].dt.year):
                row = {}
                for k2, col in (("x", "close_x"), ("y", "close_y")):
                    s = g[col]
                    row[k2] = round(float(s.iloc[-1] / s.iloc[0] - 1) * 100, 1)
                row["diff"] = round(row["x"] - row["y"], 1)
                yearly[int(y)] = row

            sc = m[m["date"] >= "2023-01-01"]
            scatter = [{"date": str(d.date()), "x": round(float(rx), 3), "y": round(float(ry), 3),
                        "after": bool(d >= SPLIT)}
                       for d, rx, ry in zip(sc["date"], sc["ret_x"], sc["ret_y"])]

            recent = m[m["date"] >= "2026-01-01"].copy()
            nx = recent["close_x"] / recent["close_x"].iloc[0]
            ny = recent["close_y"] / recent["close_y"].iloc[0]
            series_2026 = [{"date": str(d.date()), "x": round(float(a), 4), "y": round(float(b), 4)}
                           for d, a, b in zip(recent["date"], nx, ny)]

            nX = m["close_x"] / m["close_x"].iloc[0]
            nY = m["close_y"] / m["close_y"].iloc[0]
            full_series = [{"date": str(d.date()), "x": round(float(a), 3), "y": round(float(b), 3)}
                           for d, a, b in zip(m["date"][::10], nX[::10], nY[::10])]

            last1y = m[m["date"] >= "2025-08-21"]
            p_same1y = float(np.mean(np.sign(last1y["ret_x"]) == np.sign(last1y["ret_y"]))) * 100

            key = f"{sym}_vs_{tname}"
            out["pairs"][key] = {
                "xname": sym, "yname": tname,
                "period": {"start": str(m["date"].iloc[0].date()), "end": str(m["date"].iloc[-1].date()),
                           "n": int(len(m))},
                "blocks": blocks, "fisher": fisher,
                "rolling60": rolling60, "latest_roll": latest_roll,
                "roll_mean": roll_mean, "roll_min": roll_min, "roll_min_date": roll_min_date,
                "roll_max": roll_max, "roll_max_date": roll_max_date,
                "monthly": monthly_series,
                "monthly_mean_full": round(float(monthly.mean()), 3),
                "monthly_mean_3y": round(float(np.mean([x_["corr"] for x_ in monthly_3y])), 3),
                "monthly_latest": round(float(monthly.iloc[-1]), 3),
                "yearly_corr": yearly_corr,
                "price_blocks": price_blocks, "ratio": ratio_info,
                "yearly": yearly, "years": sorted(yearly),
                "scatter": scatter, "series_2026": series_2026, "full_series": full_series,
                "same_dir_1y": round(p_same1y, 1),
            }

    out = clean(out)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "visa_master_corr.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---------- 控制台汇总 ----------
    print("=== 任务1: V/MA × KBWB（银行板块 ETF）===")
    for sym in ("V", "MA"):
        p = out["pairs"][sym]
        print(f"\n【{sym} × KBWB】窗口 {p['period']['start']} ~ {p['period']['end']} n={p['period']['n']}")
        for b in p["blocks"]:
            if b["n"]:
                print(f"  {b['name']:26s} n={b['n']:5d} P={b['pearson']:.3f} Sp={b['spearman']:.3f} "
                      f"β={b['beta']:+.2f} R²={b['r2']:.2f} 同向{b['p_same_dir']:.0f}%")
        f_ = p["fisher"]
        print(f"  Fisher z={f_['z']} p={f_['p_value']} {'显著' if f_['sig'] else '不显著'}")
        print(f"  60日滚动: 最新 {p['latest_roll']:.3f} | 均值 {p['roll_mean']:.3f} | 区间 "
              f"[{p['roll_min']:.2f} ({p['roll_min_date']}) ~ {p['roll_max']:.2f} ({p['roll_max_date']})]")
        print(f"  月频: 全期均值 {p['monthly_mean_full']:.3f} | 近36月 {p['monthly_mean_3y']:.3f} | 最新 {p['monthly_latest']:.3f}")
        print(f"  近1年同向占比 {p['same_dir_1y']:.1f}%")

    print("\n=== 任务2: V/MA × QQQ/XLK（科技板块）===")
    for key in ("V_vs_QQQ", "V_vs_XLK", "MA_vs_QQQ", "MA_vs_XLK"):
        p = out["pairs"][key]
        x_, y_ = p["xname"], p["yname"]
        print(f"\n【{x_} × {y_}】窗口 {p['period']['start']} ~ {p['period']['end']} n={p['period']['n']}")
        for b in p["blocks"]:
            if b["n"]:
                print(f"  {b['name']:26s} n={b['n']:5d} P={b['pearson']:.3f} Sp={b['spearman']:.3f} "
                      f"β={b['beta']:+.2f} R²={b['r2']:.2f} 同向{b['p_same_dir']:.0f}%")
        f_ = p["fisher"]
        print(f"  Fisher z={f_['z']} p={f_['p_value']} {'显著' if f_['sig'] else '不显著'}")
        print(f"  60日滚动: 最新 {p['latest_roll']:.3f} | 均值 {p['roll_mean']:.3f} | 区间 "
              f"[{p['roll_min']:.2f} ({p['roll_min_date']}) ~ {p['roll_max']:.2f} ({p['roll_max_date']})]")
        print(f"  近1年同向占比 {p['same_dir_1y']:.1f}%")

    print(f"\nsaved: {path}")


if __name__ == "__main__":
    main()