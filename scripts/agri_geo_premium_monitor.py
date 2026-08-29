# -*- coding: utf-8 -*-
"""
农业股 × 地缘溢价（霍尔木兹）剥离监测脚本

背景：2026 年 CF/DAR 主升浪（1-2 月）与霍尔木兹海峡紧张（IRGC 1 月威胁、2/28 冲突、
油轮停航）高度同期。本脚本用"油价异动 → CF/DAR 是否跟跌"的对照检验，判断
CF/DAR 相对 SPY 超额中的地缘溢价占比是否在剥离。

四项监测（全部本地数据可算，无需联网）：
  1. 相对强弱比率  CF/CL、DAR/CL 价格比，归一化 2025-12=100（脱钩拐点）
  2. 20/60 日滚动 β  CF ~ CL、DAR ~ CL（β 下降 = 能源敏感度在剥离）
  3. 60 日滚动相关  corr(CF, CL)、corr(DAR, CL)（联动衰减）
  4. 油价异动事件对照表  XLE/CL 单日异动 >= 阈值时，记录 CF/DAR 当日/次日反应
     （判定：油价跌 CF/DAR 跟跌 ⇒ 地缘占比高；不跟跌 ⇒ 已剥离剩基本面）

对照标：MOS（钾肥，无油气暴露=负对照）、TSN/HRL（能源成本端=反向对照）、XLE（纯能源锚）

输出：results/agri_geo_premium.json（全量指标）
      results/agri_geo_premium_report.json（简报：图数据 + 异动事件 + 一句结论）
运行：python scripts/agri_geo_premium_monitor.py
依赖：本地 data/{CF,DAR,MOS,TSN,HRL,XLE,CL}/ 下 1D CSV（拉数见 fetch_agri_cdp.cjs 或 fetch_geo_cdp.cjs）
"""
import json
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT_JSON = os.path.join(BASE, "results", "agri_geo_premium.json")
OUT_REPORT = os.path.join(BASE, "results", "agri_geo_premium_report.json")

PRICE_TICKERS = ["CF", "DAR", "MOS", "TSN", "HRL", "XLE", "CL"]
# 显示顺序
ORDER = ["CF", "DAR", "MOS", "TSN", "HRL", "XLE", "CL"]

# 判定阈值
OIL_MOVE_PCT = 3.0      # 油价单日异动阈值（%）
EVENT_LOOKBACK = 3      # 事件记录窗口：异动前后各约 3 交易日看反应
BETA_WINDOWS = [20, 60] # 滚动 β 窗口
CORR_WINDOW = 60        # 滚动相关窗口
BASELINE = pd.Timestamp("2025-12-01")  # 归一化基准


def load_price(ticker):
    """读本地 1D CSV，返回含 date/close 的 DataFrame（按日期升序）"""
    if ticker == "CL":
        path = os.path.join(DATA, "cl", "CL, 1D.csv")
    else:
        path = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    dc = "date" if "date" in df.columns else ("Date" if "Date" in df.columns else df.columns[0])
    cc = "close" if "close" in df.columns else ("Close" if "Close" in df.columns else ("adj_close" if "adj_close" in df.columns else df.columns[4]))
    df = df[[dc, cc]].rename(columns={dc: "date", cc: "close"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
    return df


def build_panel(start="2025-11-01"):
    """合并所有标的到统一日期面板（按日期 outer join）"""
    panel = None
    for tk in PRICE_TICKERS:
        df = load_price(tk)[["date", "close"]].rename(columns={"close": tk})
        panel = df if panel is None else panel.merge(df, on="date", how="outer")
    panel = panel.sort_values("date").reset_index(drop=True)
    # SPY 用于超额口径（如需）
    spy_path = os.path.join(DATA, "spy", "SPY, 1D.csv")
    if os.path.exists(spy_path):
        spy = pd.read_csv(spy_path)
        spy.columns = [c.strip() for c in spy.columns]
        dc = "date" if "date" in spy.columns else ("Date" if "Date" in spy.columns else spy.columns[0])
        cc = "close" if "close" in spy.columns else ("Close" if "Close" in spy.columns else ("adj_close" if "adj_close" in spy.columns else spy.columns[4]))
        spy = spy[[dc, cc]].rename(columns={dc: "date", cc: "SPY"})
        spy["date"] = pd.to_datetime(spy["date"], errors="coerce")
        spy["SPY"] = pd.to_numeric(spy["SPY"], errors="coerce")
        panel = panel.merge(spy, on="date", how="left")
    panel = panel[panel["date"] >= pd.Timestamp(start)].reset_index(drop=True)
    return panel


def rolling_beta(x, y, window):
    """滚动 β：y 回归 x（x=油，y=CF/DAR），只对非 NaN 区间计"""
    out = pd.Series(np.nan, index=x.index)
    for i in range(window, len(x)):
        a = x.iloc[i - window + 1: i + 1]
        b = y.iloc[i - window + 1: i + 1]
        m = a.notna() & b.notna()
        if m.sum() < window * 0.7:
            continue
        ax, by = a[m], b[m]
        if ax.std() == 0:
            continue
        beta = np.cov(ax, by)[0, 1] / ax.var()
        out.iloc[i] = beta
    return out


def main():
    panel = build_panel()
    # 日收益率（全序列先算再截取——注意：美股日线与 CL 期货/美元均有各自交易日，
    # 按日期对齐后 pct_change 需在合并后的面板上做，周末/假日缺失由 NaN 自然处理）
    ret = panel[PRICE_TICKERS + (["SPY"] if "SPY" in panel.columns else [])].pct_change() * 100

    # 1. 相对强弱：价格比 CF/CL, DAR/CL，归一化
    # 注意：ratio/beta/corr 均为 int 索引 Series，赋值到 date 索引 DataFrame 必须用 .values 按位置对齐
    ratio = pd.DataFrame(index=panel["date"])
    base = panel["date"] >= BASELINE
    for tk in ["CF", "DAR"]:
        r = panel[tk] / panel["CL"]
        # 归一化：基准日（首日有值）比值=100
        first_valid = r[base].dropna().iloc[0] if (r[base].dropna().shape[0] > 0) else np.nan
        ratio[f"{tk}/CL"] = (r / first_valid * 100).values if first_valid and not np.isnan(first_valid) else r.values

    # 2. 滚动 β
    beta = pd.DataFrame(index=panel["date"])
    for win in BETA_WINDOWS:
        for tk in ["CF", "DAR"]:
            b = rolling_beta(ret["CL"], ret[tk], win)
            beta[f"{tk}_b{win}"] = b.values

    # 3. 60 日滚动相关
    corr = pd.DataFrame(index=panel["date"])
    for tk in ["CF", "DAR"]:
        c = ret[tk].rolling(CORR_WINDOW).corr(ret["CL"])
        corr[f"{tk}/CL"] = c.values

    # 5. 创新高同步（判定三：XLE/CL 创新高 → CF/DAR 是否同步创新高）
    NH_WINDOW = 60
    newhi = {}
    for tk in ["XLE", "CL", "CF", "DAR"]:
        rollmax = panel[tk].rolling(NH_WINDOW, min_periods=NH_WINDOW).max()
        newhi[tk] = (panel[tk] >= rollmax).values
    oil_hi = newhi["XLE"] | newhi["CL"]   # 能源锚（XLE 或 CL）创 60 日新高
    nh_sync = []
    for i, d in enumerate(panel["date"]):
        if oil_hi[i]:
            nh_sync.append({
                "date": str(d.date()),
                "xle_hi": bool(newhi["XLE"][i]), "cl_hi": bool(newhi["CL"][i]),
                "cf_hi": bool(newhi["CF"][i]), "dar_hi": bool(newhi["DAR"][i]),
            })
    n_oil_hi = len(nh_sync)
    n_cf_hi = sum(1 for e in nh_sync if e["cf_hi"])
    n_dar_hi = sum(1 for e in nh_sync if e["dar_hi"])
    new_high_summary = {
        "window": NH_WINDOW,
        "oil_high_days": n_oil_hi,
        "cf_also_high_days": n_cf_hi,
        "dar_also_high_days": n_dar_hi,
        "cf_sync_rate": round(n_cf_hi / n_oil_hi, 3) if n_oil_hi else None,
        "dar_sync_rate": round(n_dar_hi / n_oil_hi, 3) if n_oil_hi else None,
        "recent": nh_sync[-12:],
    }

    # 4. 油价异动事件对照表
    events = []
    cl_ret = ret["CL"]
    sig_days = panel["date"][(cl_ret.abs() >= OIL_MOVE_PCT) & cl_ret.notna()]
    for d in sig_days:
        i = panel.index[panel["date"] == d][0]
        # 事件窗口：前 1 到后 2 个交易日的反应（含当日）
        lo, hi = max(0, i - 1), min(len(panel) - 1, i + 2)
        ev = {
            "date": str(d.date()),
            "oil_ret_pct": round(float(cl_ret.iloc[i]), 2),
            "direction": "油价大涨" if cl_ret.iloc[i] > 0 else "油价大跌",
        }
        for tk in ["CF", "DAR", "MOS", "XLE"]:
            ev[tk] = round(float(ret[tk].iloc[i]), 2) if not np.isnan(ret[tk].iloc[i]) else None
            # 次日累计反应
            if i + 1 <= len(ret) - 1:
                nxt = ret[tk].iloc[i + 1]
                ev[f"{tk}_nxt"] = round(float(nxt), 2) if not np.isnan(nxt) else None
        # 判定：油价大跌日，CF/DAR 是否跟跌
        judge = []
        for tk in ["CF", "DAR"]:
            v, vn = ev.get(tk), ev.get(f"{tk}_nxt")
            vals = [x for x in [v, vn] if x is not None]
            if ev["direction"] == "油价大跌" and vals:
                if min(vals) < 0:
                    judge.append(f"{tk}跟跌(占比高)")
                else:
                    judge.append(f"{tk}未跟跌(剥离中)")
        ev["judge"] = "；".join(judge) if judge else ""
        events.append(ev)
    events = sorted(events, key=lambda x: x["date"])

    # 区间累计涨跌（首尾）
    span_chg = {}
    for tk in ["CF", "DAR", "CL", "XLE", "SPY"]:
        s = panel[tk].dropna()
        span_chg[tk] = round(float((s.iloc[-1] / s.iloc[0] - 1) * 100), 2) if len(s) > 1 else None

    out = {
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "baseline": str(BASELINE.date()),
            "oil_move_pct": OIL_MOVE_PCT,
            "beta_windows": BETA_WINDOWS,
            "corr_window": CORR_WINDOW,
            "data_span": f"{panel['date'].min().date()} ~ {panel['date'].max().date()}",
            "note": "CF/DAR 地缘溢价剥离监测：油价异动日→CF/DAR 是否跟跌。跟跌=地缘占比高；不跟跌=剥离中。",
        },
        "span_chg_pct": span_chg,
        "new_high": new_high_summary,
        "panel_dates": [str(d.date()) for d in panel["date"]],
        "ratio": {k: [None if pd.isna(v) else round(float(v), 2) for v in ratio[k].values] for k in ratio.columns},
        "beta": {k: [None if pd.isna(v) else round(float(v), 3) for v in beta[k].values] for k in beta.columns},
        "corr60": {k: [None if pd.isna(v) else round(float(v), 4) for v in corr[k].values] for k in corr.columns},
        # latest 取「最后有效值」（CL 期货口径可能滞后股票 1 个交易日，末行可能 NaN）
        "latest": {
            "ratio_cf_cl": round(float(ratio["CF/CL"].dropna().iloc[-1]), 2) if ratio["CF/CL"].notna().any() else None,
            "ratio_dar_cl": round(float(ratio["DAR/CL"].dropna().iloc[-1]), 2) if ratio["DAR/CL"].notna().any() else None,
            "beta_cf_60": round(float(beta["CF_b60"].dropna().iloc[-1]), 3) if beta["CF_b60"].notna().any() else None,
            "beta_dar_60": round(float(beta["DAR_b60"].dropna().iloc[-1]), 3) if beta["DAR_b60"].notna().any() else None,
            "corr60_cf_cl": round(float(corr["CF/CL"].dropna().iloc[-1]), 4) if corr["CF/CL"].notna().any() else None,
            "corr60_dar_cl": round(float(corr["DAR/CL"].dropna().iloc[-1]), 4) if corr["DAR/CL"].notna().any() else None,
            "asof": {
                "stocks": str(panel["date"].iloc[-1].date()),
                "cl_last_valid": str(panel["date"][panel["CL"].notna()].iloc[-1].date()),
            },
        },
        "events": events,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)

    # ---- 简报 ----
    last = out["latest"]
    # 趋势判断：对比 β60 近 60 日 vs 前 60 日（如有足够数据）
    trend_notes = []
    # 趋势用 |β| 判定（β 可为负，符号变化不代表敏感度上升）
    for tk in ["CF", "DAR"]:
        b60 = beta[f"{tk}_b60"].dropna()
        if len(b60) >= 90:
            recent_avg = b60.iloc[-30:].abs().mean()
            prior_avg = b60.iloc[-90:-60].abs().mean()
            delta = recent_avg - prior_avg
            trend = "↑对油敏感度上升" if delta > 0.05 else ("↓对油敏感度下降(剥离)" if delta < -0.05 else "→平稳")
            trend_notes.append(f"{tk} |β60| 近30日均{recent_avg:.2f} vs 前30日均{prior_avg:.2f} → {trend}")
    # 最近一次油价大跌事件
    recent_big_drop = [e for e in events if e["direction"] == "油价大跌"][-3:] if events else []
    dump_evt = recent_big_drop[-1] if recent_big_drop else {}
    last_judge = dump_evt.get("judge", "")
    nh = out["new_high"]
    nh_note = (f"；判定三：能源锚(XLE/CL)创60日新高 {nh['oil_high_days']} 天中，CF 同步 {nh['cf_also_high_days']} 天"
               f"({nh['cf_sync_rate']})、DAR 同步 {nh['dar_also_high_days']} 天({nh['dar_sync_rate']})")
    conclusion = (
        f"截至 {out['meta']['data_span']}：CF/DAR 对油价 β60 分别为 {last.get('beta_cf_60')} / {last.get('beta_dar_60')}，"
        f"60日相关 {last.get('corr60_cf_cl')} / {last.get('corr60_dar_cl')}。区间涨跌 {out['span_chg_pct']}。"
        + ("；".join(trend_notes) if trend_notes else "")
        + (f"；最近一次油价大跌({dump_evt.get('date')}, {dump_evt.get('oil_ret_pct')}%)：{last_judge or '未判'}"
           if dump_evt else "")
        + nh_note
    )

    report = {
        "meta": out["meta"],
        "latest": last,
        "trend_notes": trend_notes,
        "recent_oil_drop_events": recent_big_drop,
        "new_high": nh,
        "span_chg_pct": span_chg,
        "conclusion": conclusion,
    }
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, default=str)

    print(f"written: {os.path.relpath(OUT_JSON, BASE)} ({os.path.getsize(OUT_JSON)}B)")
    print(f"written: {os.path.relpath(OUT_REPORT, BASE)} ({os.path.getsize(OUT_REPORT)}B)")
    print("\n=== 简报 ===")
    print(conclusion)
    print(f"\n最近油价大跌事件（最多3条）:")
    for e in recent_big_drop:
        print(f"  {e['date']} {e['direction']} {e['oil_ret_pct']:+.2f}%  "
              f"CF {e.get('CF')}→{e.get('CF_nxt')}  DAR {e.get('DAR')}→{e.get('DAR_nxt')}  {e['judge']}")


if __name__ == "__main__":
    main()