# -*- coding: utf-8 -*-
"""VST × UTES 分阶段相关性分析（正式版）
UTES = Virtus Reaves Utilities ETF（主动管理公用事业 ETF，2026-04 前三大持仓 CEG/VST/TLN 各约10%）
对照：XLU（S&P 500 Utilities ETF，板块宽度参照）
阶段划分：事件驱动 + 滚动相关结构双确认
"""
import json
import math
import os

import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(BASE, "..", "results")


def load(ticker):
    f = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(f, parse_dates=["date"])
    df = df[["date", "adj_close"]].rename(columns={"adj_close": "close"})
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df


def ret_series(df):
    s = df.set_index("date")["close"]
    return s.pct_change().dropna()


def main():
    vst = load("VST")
    utes = load("UTES")
    xlu = load("XLU")

    start = max(vst["date"].min(), utes["date"].min(), xlu["date"].min())
    end = min(vst["date"].max(), utes["date"].max(), xlu["date"].max())

    def sl(df):
        return df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)

    vst_s, utes_s, xlu_s = sl(vst), sl(utes), sl(xlu)

    vst_r = ret_series(vst_s).rename("vst")
    utes_r = ret_series(utes_s).rename("utes")
    xlu_r = ret_series(xlu_s).rename("xlu")
    m = pd.concat([vst_r, utes_r, xlu_r], axis=1).dropna()

    # ---- 全期 ----
    corr_vu = float(m["vst"].corr(m["utes"]))
    corr_vx = float(m["vst"].corr(m["xlu"]))
    corr_ux = float(m["utes"].corr(m["xlu"]))

    # ---- 滚动 60 日相关 ----
    roll = pd.DataFrame({
        "vst_utes": m["vst"].rolling(60).corr(m["utes"]),
        "vst_xlu": m["vst"].rolling(60).corr(m["xlu"]),
        "utes_xlu": m["utes"].rolling(60).corr(m["xlu"]),
    }).dropna()
    roll_chart = {
        "dates": [d.strftime("%Y-%m-%d") for d in roll.index[::5]],
        "vu": [round(float(v), 3) for v in roll["vst_utes"][::5]],
        "vx": [round(float(v), 3) for v in roll["vst_xlu"][::5]],
        "ux": [round(float(v), 3) for v in roll["utes_xlu"][::5]],
    }

    # ---- 年度相关 / 收益 ----
    years = sorted(m.index.year.unique())
    yearly = []
    for y in years:
        g = m[m.index.year == y]

        def yret(df, year):
            d = df[df["date"].dt.year == year]
            return float(d["close"].iloc[-1] / d["close"].iloc[0] - 1) if len(d) > 1 else None

        yearly.append({
            "year": int(y),
            "corr_vu": round(float(g["vst"].corr(g["utes"])), 3),
            "corr_vx": round(float(g["vst"].corr(g["xlu"])), 3),
            "vst": round(yret(vst_s, y) * 100, 1),
            "utes": round(yret(utes_s, y) * 100, 1),
            "xlu": round(yret(xlu_s, y) * 100, 1),
        })

    # ---- 阶段定义（事件驱动，滚动相关确认）----
    phases_def = [
        {"id": "S1", "label": "板块成员期", "sub": "2018.01 ~ 2021.02",
         "p0": "2018-01-01", "p1": "2021-02-28",
         "event": "德州暴风雪（2021-02）之前：VST 还是传统综合电力商，与公用事业板块同涨同跌、各走各路，一半交易日方向相反（跷跷板 44.8%），相关性贴近板块天然水平。"},
        {"id": "S2", "label": "风暴与加息冲击期", "sub": "2021.03 ~ 2022.10",
         "p0": "2021-03-01", "p1": "2022-10-31",
         "event": "2021-02 德州暴风雪让 VST 单季巨亏，2022 美联储激进加息、公用事业防御属性凸显。VST 走独立修复行情（+39.3% vs 板块 +19.8%），相关仍只有 0.54。"},
        {"id": "S3", "label": "AI 电力叙事发酵期", "sub": "2022.11 ~ 2024.08",
         "p0": "2022-11-01", "p1": "2024-08-31",
         "event": "ChatGPT 发布（2022-11）点燃 AI 算力需求叙事，数据中心电力饥渴开始被定价。VST 独立暴涨 +289.6%（相关仅 0.51）—— 超额全部来自个股 α，不是板块。"},
        {"id": "S4", "label": "AI 电力主升浪", "sub": "2024.09 ~ 2025.12",
         "p0": "2024-09-01", "p1": "2025-12-31",
         "event": "微软×CEG 三里岛 PPA（2024-09-20）确立核电估值范式，AWS×VST Comanche Peak（2025-03）紧随其后。UTE 把 VST/CEG/TLN 加仓到前三大重仓（各约10%），VST 与 UTES 相关跳升至 0.89、β 2.41 —— 从板块成员变成板块放大器。"},
        {"id": "S5", "label": "回调分化期", "sub": "2026.01 ~ 至今",
         "p0": "2026-01-01", "p1": "2026-08-14",
         "event": "AI 电力交易回调：VST -10.1% vs UTES -2.1% vs XLU +4.0%。相关仍高（0.83）但超额转负 —— 板块未跌，杀的是 VST 的估值，高 β 放大下行。"},
    ]

    def cret(df, p0t, p1t):
        d = df[(df["date"] >= p0t) & (df["date"] <= p1t)]
        return float(d["close"].iloc[-1] / d["close"].iloc[0] - 1) if len(d) > 1 else None

    phases = []
    for ph in phases_def:
        p0t, p1t = pd.Timestamp(ph["p0"]), pd.Timestamp(ph["p1"])
        g = m[(m.index >= p0t) & (m.index <= p1t)]
        vu = float(g["vst"].corr(g["utes"])) if len(g) > 10 else None
        vx = float(g["vst"].corr(g["xlu"])) if len(g) > 10 else None
        ux = float(g["utes"].corr(g["xlu"])) if len(g) > 10 else None
        beta = float(g["vst"].cov(g["utes"]) / g["utes"].var()) if len(g) > 10 and g["utes"].var() > 0 else None
        seesaw = float((np.sign(g["vst"]) != np.sign(g["utes"])).mean()) if len(g) > 0 else None
        both_up = float(((g["vst"] > 0) & (g["utes"] > 0)).mean())
        both_dn = float(((g["vst"] < 0) & (g["utes"] < 0)).mean())
        v_c, u_c, x_c = cret(vst_s, p0t, p1t), cret(utes_s, p0t, p1t), cret(xlu_s, p0t, p1t)
        ann_vol_v = float(g["vst"].std() * math.sqrt(252)) if len(g) > 10 else None
        ann_vol_u = float(g["utes"].std() * math.sqrt(252)) if len(g) > 10 else None
        # 超额胜率：VST 跑赢 UTES 的交易日占比（日超额>0）
        win = float((g["vst"] - g["utes"] > 0).mean())
        phases.append({
            "id": ph["id"], "label": ph["label"], "sub": ph["sub"],
            "event": ph["event"],
            "p0": ph["p0"], "p1": ph["p1"],
            "n": int(len(g)),
            "corr_vu": vu, "corr_vx": vx, "corr_ux": ux,
            "beta": beta, "seesaw": seesaw,
            "both_up": both_up, "both_dn": both_dn,
            "ret_vst": v_c, "ret_utes": u_c, "ret_xlu": x_c,
            "excess": (v_c - u_c) if (v_c is not None and u_c is not None) else None,
            "ann_vol_v": ann_vol_v, "ann_vol_u": ann_vol_u,
            "win_days": win,
        })

    # ---- 归一化净值（5日采样）----
    def norm_series(df):
        s = df.set_index("date")["close"]
        return pd.DataFrame({"date": s.index, "v": s / s.iloc[0]})

    seq = {}
    for k, df in (("vst", vst_s), ("utes", utes_s), ("xlu", xlu_s)):
        ns = norm_series(df)
        seq[k] = {"dates": [d.strftime("%Y-%m-%d") for d in ns["date"][::5]],
                  "values": [round(float(v), 3) for v in ns["v"][::5]]}

    # ---- 相对强弱 VST/UTES ----
    m2 = pd.DataFrame({"vst": vst_s.set_index("date")["close"],
                       "utes": utes_s.set_index("date")["close"]}).dropna()
    ratio = m2["vst"] / m2["utes"]
    ratio_norm = ratio / ratio.iloc[0]
    ratio_chart = {"dates": [d.strftime("%Y-%m-%d") for d in ratio_norm.index[::5]],
                   "values": [round(float(v), 3) for v in ratio_norm[::5]]}

    # ---- 全期累计 ----
    cum = {"vst": float(vst_s["close"].iloc[-1] / vst_s["close"].iloc[0] - 1),
           "utes": float(utes_s["close"].iloc[-1] / utes_s["close"].iloc[0] - 1),
           "xlu": float(xlu_s["close"].iloc[-1] / xlu_s["close"].iloc[0] - 1),
           "start": str(start.date()), "end": str(end.date())}

    result = {
        "window": {"start": str(start.date()), "end": str(end.date()), "n": int(len(m))},
        "corr_full": {"vst_utes": corr_vu, "vst_xlu": corr_vx, "utes_xlu": corr_ux},
        "corr_roll": {"latest_vu": round(float(roll["vst_utes"].iloc[-1]), 3),
                      "mean_vu": round(float(roll["vst_utes"].mean()), 3),
                      "latest_vx": round(float(roll["vst_xlu"].iloc[-1]), 3),
                      "max_vu": round(float(roll["vst_utes"].max()), 3),
                      "min_vu": round(float(roll["vst_utes"].min()), 3)},
        "yearly": yearly,
        "phases": phases,
        "cum": cum,
        "norm_series": seq,
        "ratio": {"start": float(ratio.iloc[0]), "latest": float(ratio.iloc[-1]),
                  "norm_latest": float(ratio_norm.iloc[-1]),
                  "max": float(ratio_norm.max()), "max_date": str(ratio_norm.idxmax().date()),
                  "min": float(ratio_norm.min()), "min_date": str(ratio_norm.idxmin().date())},
        "ratio_chart": ratio_chart,
        "roll_chart": roll_chart,
    }

    with open(os.path.join(OUT, "vst_utes_phase.json"), "w") as f:
        json.dump(result, f, indent=1, default=str)
    print("结果已保存 results/vst_utes_phase.json")
    print(f"全期相关: V×U {corr_vu:.3f}  V×X {corr_vx:.3f}  U×X {corr_ux:.3f}")
    print(f"滚动60日 V×U: 均值 {roll['vst_utes'].mean():.3f} 最新 {roll['vst_utes'].iloc[-1]:.3f}")
    for ph in phases:
        print(f"  {ph['id']} {ph['label']}: n={ph['n']} corr={ph['corr_vu']:.2f} β={ph['beta']:.2f} "
              f"跷跷板={ph['seesaw']*100:.1f}% VST={ph['ret_vst']*100:+.1f}% UTES={ph['ret_utes']*100:+.1f}% 超额={ph['excess']*100:+.1f}pp")


if __name__ == "__main__":
    main()
