# -*- coding: utf-8 -*-
"""VST 2026 回调解剖 + CEG/UTES/XLU 对比
回答：回调阶段 VST 为什么比板块跌得深？跟 CEG 比谁更狠？
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
    ceg = load("CEG")
    utes = load("UTES")
    xlu = load("XLU")

    # 2026 窗口：以 2025-12-31 收盘为基准
    for df in (vst, ceg, utes, xlu):
        df["year"] = df["date"].dt.year

    def ytd_ret(df, y0=2025, y1=2026):
        base = df[(df["year"] == y0)].iloc[-1]["close"]
        cur = df[(df["year"] == y1)]["close"].iloc[-1]
        return cur / base - 1

    print("=" * 70)
    print("[1] 2026 YTD 收益（基准 2025-12-31 收盘）")
    for k, df in (("VST", vst), ("CEG", ceg), ("UTES", utes), ("XLU", xlu)):
        r = ytd_ret(df)
        print(f"  {k}: {r*100:+.1f}%")

    # 2026 年内从年内高点的最大回撤（只看 2026 年数据）
    print("\n[2] 2026 年内最大回撤（自 2026 年局部高点）")
    dd_stats = {}
    for k, df in (("VST", vst), ("CEG", ceg), ("UTES", utes), ("XLU", xlu)):
        d26 = df[df["year"] == 2026].copy()
        s = d26.set_index("date")["close"]
        peak = s.cummax()
        dd = s / peak - 1
        mdd = dd.min()
        mdd_date = dd.idxmin()
        peak_date = peak.idxmax()
        dd_stats[k] = {"mdd": float(mdd), "mdd_date": str(mdd_date.date()),
                       "peak_date": str(peak_date.date()),
                       "peak_close": float(peak.max()),
                       "cur_close": float(s.iloc[-1])}
        print(f"  {k}: 最大回撤 {mdd*100:.1f}% ({mdd_date.date()})  年内高点 {peak_date.date()} ({peak.max():.1f})  最新 {s.iloc[-1]:.1f}")

    # 月度收益（2026-01 ~ 2026-08）
    print("\n[3] 2026 月度收益（%）")
    month_tbl = []
    for m in range(1, 9):
        row = {"m": m}
        for k, df in (("VST", vst), ("CEG", ceg), ("UTES", utes), ("XLU", xlu)):
            d = df[(df["year"] == 2026) & (df["date"].dt.month == m)]
            r = d["close"].iloc[-1] / d["close"].iloc[0] - 1 if len(d) > 1 else None
            row[k] = r * 100 if r is not None else None
        month_tbl.append(row)
        print(f"  {row['m']:>2}月 | " + " | ".join(f"{row[k]:+6.1f}" if row[k] is not None else "    -" for k in ("VST", "CEG", "UTES", "XLU")))

    # 下跌段识别：VST 与 CEG 年内最大连续下跌段（峰谷）
    print("\n[4] 2026 主要下跌段（收盘峰→谷, 回撤≥10% 或前3大）")
    for k in ("VST", "CEG", "UTES"):
        df = {"VST": vst, "CEG": ceg, "UTES": utes}[k]
        d26 = df[df["year"] == 2026].copy().reset_index(drop=True)
        s = d26.set_index("date")["close"]
        # 找所有峰谷：局部高点之后到下一个局部低点
        segs = []
        i = 0
        while i < len(s) - 1:
            # 找峰
            while i < len(s) - 1 and s.iloc[i + 1] >= s.iloc[i]:
                i += 1
            if i >= len(s) - 1:
                break
            peak_i = i
            # 找谷（允许小反弹，取后续最低）
            valley_i = i + 1
            for j in range(i + 2, len(s)):
                if s.iloc[j] < s.iloc[valley_i]:
                    valley_i = j
                # 若反弹超过前峰 50%，结束该段
                if s.iloc[j] > s.iloc[peak_i] * (1 - (s.iloc[peak_i] - s.iloc[valley_i]) / s.iloc[peak_i] / 2):
                    break
            dd = s.iloc[valley_i] / s.iloc[peak_i] - 1
            if dd < -0.05:
                segs.append({"from": s.index[peak_i], "to": s.index[valley_i],
                             "peak": float(s.iloc[peak_i]), "valley": float(s.iloc[valley_i]),
                             "dd": float(dd), "days": valley_i - peak_i})
            i = valley_i + 1 if valley_i + 1 < len(s) else len(s)
        segs.sort(key=lambda x: x["dd"])
        print(f"  {k}:")
        for sg in segs[:4]:
            print(f"    {sg['from'].date()} → {sg['to'].date()} ({sg['days']}日): {sg['dd']*100:.1f}%  {sg['peak']:.1f}→{sg['valley']:.1f}")

    # β 拆解：2026 年 VST 对板块回归，拆 β 贡献 + 个股 α
    print("\n[5] 2026 年 VST/CEG 跌幅的 β 拆解（对 XLU 板块）")
    vst_r = ret_series(vst).rename("vst")
    ceg_r = ret_series(ceg).rename("ceg")
    xlu_r = ret_series(xlu).rename("xlu")
    utes_r = ret_series(utes).rename("utes")
    m = pd.concat([vst_r, ceg_r, xlu_r, utes_r], axis=1).dropna()
    m26 = m[m.index.year == 2026]
    for tk in ("VST", "CEG"):
        col = tk.lower()
        # 对 XLU
        beta_x = float(m26[col].cov(m26["xlu"]) / m26["xlu"].var())
        alpha_x = float(m26[col].mean() - beta_x * m26["xlu"].mean())
        # 对 UTES
        beta_u = float(m26[col].cov(m26["utes"]) / m26["utes"].var())
        alpha_u = float(m26[col].mean() - beta_u * m26["utes"].mean())
        # 累计
        cum_tk = float((1 + m26[col]).prod() - 1)
        cum_xlu = float((1 + m26["xlu"]).prod() - 1)
        cum_utes = float((1 + m26["utes"]).prod() - 1)
        beta_part_x = beta_x * cum_xlu
        alpha_part_x = cum_tk - beta_part_x
        print(f"  {tk}: 2026累计 {cum_tk*100:+.1f}% | 对XLU β {beta_x:.2f} → 板块贡献 {beta_part_x*100:+.1f}pp + 个股残差 {alpha_part_x*100:+.1f}pp")
        print(f"      对UTES β {beta_u:.2f} → 板块贡献 {beta_u*cum_utes*100:+.1f}pp + 个股残差 {(cum_tk-beta_u*cum_utes)*100:+.1f}pp")

    # 全窗口 β（对照，S4/S5 合并）
    m24_25 = m[(m.index >= "2024-09-01") & (m.index <= "2025-12-31")]
    m26b = m[m.index.year == 2026]
    print("\n[6] β 对照（VST/CEG 对 UTES）")
    for tk in ("VST", "CEG"):
        col = tk.lower()
        b_s4 = float(m24_25[col].cov(m24_25["utes"]) / m24_25["utes"].var())
        b_s5 = float(m26b[col].cov(m26b["utes"]) / m26b["utes"].var())
        print(f"  {tk}: S4(2024.09-2025.12) β {b_s4:.2f} → S5(2026) β {b_s5:.2f}")

    # 波动率对比
    print("\n[7] 2026 年化波动率（%）")
    for tk in ("VST", "CEG", "UTES", "XLU"):
        col = tk.lower()
        print(f"  {tk}: {m26[col].std()*math.sqrt(252)*100:.0f}%")

    # 输出 JSON
    result = {
        "ytd_2026": {k: ytd_ret({"VST": vst, "CEG": ceg, "UTES": utes, "XLU": xlu}[k]) for k in ("VST", "CEG", "UTES", "XLU")},
        "mdd_2026": dd_stats,
        "monthly_2026": month_tbl,
        "beta_decomp": {},
    }
    for tk in ("VST", "CEG"):
        col = tk.lower()
        result["beta_decomp"][tk] = {
            "beta_xlu": round(float(m26[col].cov(m26["xlu"]) / m26["xlu"].var()), 2),
            "beta_utes": round(float(m26[col].cov(m26["utes"]) / m26["utes"].var()), 2),
            "cum": round(float((1 + m26[col]).prod() - 1), 4),
            "cum_xlu": round(float((1 + m26["xlu"]).prod() - 1), 4),
            "cum_utes": round(float((1 + m26["utes"]).prod() - 1), 4),
        }
    with open(os.path.join(OUT, "vst_2026_pullback.json"), "w") as f:
        json.dump(result, f, indent=1, default=str)
    print("\n已保存 results/vst_2026_pullback.json")


if __name__ == "__main__":
    main()
