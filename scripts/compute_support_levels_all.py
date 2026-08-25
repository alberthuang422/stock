# -*- coding: utf-8 -*-
"""批量支撑位计算 — 工作流 A（swing 分形 + 水平聚类 + 评分）全量版

用户口径（2026-08-25 确认，覆盖 skill 默认值）：
  1. 支撑带容差 ±2%（带 = 基准价×(1±2%)），不用 skill 默认 ATR 容差
  2. swing 分形定位局部极值用 raw high/low；但支撑带基准价与所有距离/百分比计算
     统一用 adj_close 复权口径（swing low 所在 K 线的 adj_close 作为候选基准价）
  3. 有效触碰 ≥3 次；"刺穿下沿但后续收盘回到带上方（修复）"也算触碰；
     同一轮连续在带内只计 1 次（一轮 = 连续无整日离开带的时段，离开 = low > band_hi）
  4. 首末触碰跨度（交易日 index 差）≥21 才成支撑；分档 1M+/3M+/6M+/1Y+
  5. 全部代码都算，不剔除；异常（缺列/空数据）跳过并列出

输出（三级）：
  - data/support_levels/levels_summary.csv  每只股票每个支撑位一行 + 状态/强度
  - data/support_levels/touches/{ticker}.csv 逐次触碰明细
  - data/support_levels/README.md           口径说明 + 字段字典 + 时间戳
"""
import os
import sys
import csv
import json
from datetime import datetime

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(DATA, "support_levels")
TOUCH_DIR = os.path.join(OUT_DIR, "touches")

REQUIRED_COLS = ["date", "open", "high", "low", "close", "volume", "adj_close"]

# ---- 用户口径参数 ----
BAND_PCT = 0.02          # 支撑带 ±2%
MIN_TOUCHES = 3          # 有效触碰 ≥3
MIN_SPAN = 21            # 首末触碰跨度 ≥21 交易日
REPAIR_WIN = 10          # 刺穿下沿后的修复窗口（交易日）：期内收盘回带上方视为修复
FRACTAL_N = 3            # 分形左右 K 线数

# span 分档阈值（交易日）
LEVELS = [(252, "1Y+"), (126, "6M+"), (63, "3M+"), (21, "1M+")]

# strength 分档规则
STRENGTH_A = (6, 126)   # touches>=6 且 span>=126
STRENGTH_B = (4, 63)    # (touches>=4 且 span>=63) 或 touches>=8


def load_ticker_data(tick_dir):
    """返回 (ticker, df) 或 (ticker, None, reason)。选 *, 1D.csv 且非 BATS_ 前缀。
    BATS_* 为备用源：仅当目录中没有非 BATS 的 1D 文件时才使用 BATS 文件（如 ibkr）。"""
    ticker = os.path.basename(tick_dir.rstrip("/\\"))
    if not os.path.isdir(tick_dir):
        return ticker, None, "目录不存在"
    plain = [f for f in os.listdir(tick_dir)
             if f.endswith(".csv") and ", 1D" in f and not f.startswith("BATS_")]
    files = plain if plain else [f for f in os.listdir(tick_dir)
                                 if f.endswith(".csv") and ", 1D" in f]
    if not files:
        return ticker, None, "未找到日线文件(*, 1D.csv)"
    path = os.path.join(tick_dir, files[0])
    try:
        df = pd.read_csv(path)
    except Exception as e:
        return ticker, None, f"读取失败: {e}"
    if df.empty:
        return ticker, None, "数据为空"
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        return ticker, None, f"缺列 {missing}"
    df = df[REQUIRED_COLS].copy()
    df = df.dropna(subset=["high", "low", "close", "adj_close"]).reset_index(drop=True)
    if len(df) < MIN_SPAN + FRACTAL_N * 2 + 10:
        return ticker, None, f"有效行数过少({len(df)})"
    for c in ["open", "high", "low", "close", "adj_close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["high", "low", "close", "adj_close"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).reset_index(drop=True)
    if len(df) < MIN_SPAN + FRACTAL_N * 2 + 10:
        return ticker, None, f"数值清洗后行数过少({len(df)})"
    return ticker, df, None


def find_pivots(vals, n=3, kind="low"):
    """swing 分形：左右各 n 根 K 线的局部极值（唯一）。返回 index 列表。"""
    idxs = []
    for i in range(n, len(vals) - n):
        w = vals[i - n:i + n + 1]
        if kind == "low":
            if vals[i] == w.min() and (w == vals[i]).sum() == 1:
                idxs.append(i)
        else:
            if vals[i] == w.max() and (w == vals[i]).sum() == 1:
                idxs.append(i)
    return idxs


def greedy_cluster(centers, band_pct):
    """一维贪心聚类（按值升序）。合并判定 = 新元素下沿 <= 簇中心上沿，即:
       p*(1-band) <= c*(1+band) ⟺ p <= c*(1+band)/(1-band) ≈ c*1.040816
    该判定数学上保证合并后的带（center±band%）互不重叠。返回 [(center, item_count, items)]"""
    if not centers:
        return []
    ps = sorted(centers)
    cl = []
    for p in ps:
        if cl:
            c0, n0, items = cl[-1]
            if p * (1 - band_pct) <= c0 * (1 + band_pct):
                new_c = (c0 * n0 + p) / (n0 + 1)
                cl[-1] = (new_c, n0 + 1, items + [p])
            else:
                cl.append((p, 1, [p]))
        else:
            cl.append((p, 1, [p]))
    return cl


def compute_support_levels(df):
    """主算法。返回 support 列表（dict），按 |dist_pct| 升序（S1 最靠近现价）。"""
    N = len(df)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    close = df["close"].values.astype(float)
    adj = df["adj_close"].values.astype(float)
    dates = df["date"]

    piv_low = find_pivots(low, FRACTAL_N, "low")
    if len(piv_low) < MIN_TOUCHES:
        return []

    # 候选支撑价 = swing low 所在 K 线的 adj_close（复权口径）
    cand_prices = sorted(float(adj[i]) for i in piv_low if adj[i] > 0)
    if not cand_prices:
        return []

    clusters = greedy_cluster(cand_prices, BAND_PCT)
    supports = []
    for center, n_items, _ in clusters:
        if center <= 0:
            continue
        band_lo = center * (1 - BAND_PCT)
        band_hi = center * (1 + BAND_PCT)

        # ---- 触碰轮次切分 ----
        # 进带判据：K 线与带区间相交（low<=band_hi 且 high>=band_lo）。
        # 仅 low<=band_hi 会错误地把"价格远低于带的历史期"全部算进带（如 AAPL 支撑带 320
        # 会把 1997 年 0.3 元的 K 线算成带内，导致单轮横跨数十年）。K 线必须真正穿入带区。
        in_band = (low <= band_hi) & (high >= band_lo)
        rounds = []  # (start_idx, end_idx) 闭区间；断开 = 完全在带外（上方 low>band_hi 或下方 high<band_lo）
        i = 0
        while i < N:
            if in_band[i]:
                j = i
                while j + 1 < N and in_band[j + 1]:
                    j += 1
                rounds.append((i, j))
                i = j + 1
            else:
                i += 1

        # ---- 逐轮判定有效性 ----
        valid_touches = []  # (touch_idx, touch_low, touch_close)
        must_repair = []    # 全轮收盘在下沿下方的轮（待修复判定）
        for (s, e) in rounds:
            win_close = close[s:e + 1]
            if (win_close >= band_lo).any():
                # 轮内收盘回到带内/上方 → 直接有效
                k = s + int(np.argmin(win_close))
                valid_touches.append((k, float(low[k]), float(close[k])))
            else:
                # 整轮收盘刺穿下沿（close < band_lo）→ 需要修复：
                # 自轮末起 REPAIR_WIN 个交易日内收盘回到带内（close >= band_lo）才算修复
                must_repair.append((s, e))
        for (s, e) in must_repair:
            k = s + int(np.argmin(close[s:e + 1]))
            repaired = False
            for t in range(e + 1, min(N, e + 1 + REPAIR_WIN)):
                if close[t] >= band_lo:
                    repaired = True
                    break
            if repaired:
                valid_touches.append((k, float(low[k]), float(close[k])))

        if len(valid_touches) < MIN_TOUCHES:
            continue

        valid_touches.sort(key=lambda x: x[0])
        first_idx = valid_touches[0][0]
        last_idx = valid_touches[-1][0]
        span = last_idx - first_idx  # 交易日 index 差
        if span < MIN_SPAN:
            continue

        level = "1M+"
        for thr, name in LEVELS:
            if span >= thr:
                level = name
                break

        # 触碰去重兜底（理论上 rounds 已保证，防御相邻合并）
        unique = []
        for vt in valid_touches:
            if not unique or vt[0] - unique[-1][0] > 0:
                unique.append(vt)
        valid_touches = unique

        last_close = float(adj[-1])
        last_close_date = dates.iloc[-1]
        dist_pct = (last_close - center) / center * 100.0
        if dist_pct > 3.0:
            status = "above"
        elif dist_pct < -3.0:
            status = "below"
        else:
            status = "near"

        n_t = len(valid_touches)
        if n_t >= STRENGTH_A[0] and span >= STRENGTH_A[1]:
            strength = "A"
        elif (n_t >= STRENGTH_B[0] and span >= STRENGTH_B[1]) or n_t >= 8:
            strength = "B"
        else:
            strength = "C"

        # touch 明细记录（轮内收盘最低日）
        touches_rec = []
        seq = 1
        for (k, tl, tc) in valid_touches:
            touches_rec.append({
                "touch_seq": seq, "touch_date": str(dates.iloc[k].date()),
                "touch_low": round(tl, 6), "touch_close": round(tc, 6),
            })
            seq += 1

        supports.append({
            "support_mid": round(center, 6),
            "support_lo": round(band_lo, 6),
            "support_hi": round(band_hi, 6),
            "touches": n_t,
            "first_touch_date": str(dates.iloc[first_idx].date()),
            "last_touch_date": str(dates.iloc[last_idx].date()),
            "span_trading_days": int(span),
            "level": level,
            "last_close_date": str(last_close_date.date()),
            "last_close": round(last_close, 6),
            "dist_pct": round(dist_pct, 2),
            "status": status,
            "strength": strength,
            "touches_rec": touches_rec,
        })

    # S1 最靠近现价：按 |dist_pct| 升序编号
    supports.sort(key=lambda x: abs(x["dist_pct"]))
    for i, s in enumerate(supports, 1):
        s["support_id"] = f"S{i}"
        s["touches_rec"] = sorted(s["touches_rec"], key=lambda r: r["touch_seq"])
    return supports


def main():
    os.makedirs(TOUCH_DIR, exist_ok=True)
    summary_rows = []
    skipped = []
    tickers_ok = []

    tick_dirs = sorted(
        [os.path.join(DATA, d) for d in os.listdir(DATA)
         if os.path.isdir(os.path.join(DATA, d))
         and d != "support_levels"]  # 排除输出目录自身
    )
    for td in tick_dirs:
        ticker, df, err = load_ticker_data(td)
        if err:
            skipped.append((ticker, err))
            print(f"  SKIP {ticker}: {err}")
            continue
        try:
            supports = compute_support_levels(df)
        except Exception as e:
            skipped.append((ticker, f"计算异常: {e}"))
            print(f"  SKIP {ticker}: 计算异常 {e}")
            continue

        if not supports:
            skipped.append((ticker, "无满足条件的支撑位(触碰<3或跨度<21)"))
            print(f"  SKIP {ticker}: 无满足条件的支撑位")
            continue

        # 写触碰明细
        touch_path = os.path.join(TOUCH_DIR, f"{ticker}.csv")
        with open(touch_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "ticker", "support_id", "support_mid", "touch_seq",
                "touch_date", "touch_low", "touch_close"])
            w.writeheader()
            for s in supports:
                for r in s["touches_rec"]:
                    w.writerow({
                        "ticker": ticker, "support_id": s["support_id"],
                        "support_mid": s["support_mid"],
                        "touch_seq": r["touch_seq"], "touch_date": r["touch_date"],
                        "touch_low": r["touch_low"], "touch_close": r["touch_close"],
                    })

        for s in supports:
            summary_rows.append({
                "ticker": ticker, "support_id": s["support_id"],
                "support_mid": s["support_mid"], "support_lo": s["support_lo"],
                "support_hi": s["support_hi"], "touches": s["touches"],
                "first_touch_date": s["first_touch_date"],
                "last_touch_date": s["last_touch_date"],
                "span_trading_days": s["span_trading_days"], "level": s["level"],
                "last_close_date": s["last_close_date"], "last_close": s["last_close"],
                "dist_pct": s["dist_pct"], "status": s["status"],
                "strength": s["strength"],
            })
        tickers_ok.append(ticker)
        print(f"  OK {ticker}: {len(supports)} 个支撑位（{df['date'].iloc[-1].date()} 收盘 {supports[0]['last_close']}）")

    # ---- 汇总 ----
    summary_path = os.path.join(OUT_DIR, "levels_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "ticker", "support_id", "support_mid", "support_lo", "support_hi",
            "touches", "first_touch_date", "last_touch_date", "span_trading_days",
            "level", "last_close_date", "last_close", "dist_pct", "status", "strength"])
        w.writeheader()
        w.writerows(summary_rows)

    # ---- README ----
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    readme = f"""# 支撑位批量计算结果（data/support_levels）

生成时间：{now}
覆盖：{len(tickers_ok)} 只代码 / {len(summary_rows)} 条支撑位记录（levels_summary.csv）

## 口径说明（用户确认，覆盖 skill 默认值）

算法：工作流 A — swing 分形 + 水平聚类 + 评分（见 .workbuddy/skills/support-resistance-levels/SKILL.md）。

1. **数据**：`data/{{ticker}}/{{ticker}}, 1D.csv`（列 date,open,high,low,close,volume,adj_close），全历史不截窗。
2. **Swing 分形**：左右各 {FRACTAL_N} 根 K 线的局部极值；定位局部低点用 **raw low**。
3. **支撑带基准价**：swing low 所在 K 线的 **adj_close（复权价）**。带 = 基准价 × (1 ± {BAND_PCT*100:.0f}%)。
4. **水平聚类**：候选价为各 swing low 的 adj_close；按升序贪心合并，**合并判定 = 新元素下沿 ≤ 簇中心上沿（带相接/重叠即并线）**，聚类中心为加权均值。
5. **触碰判定**：当日 low ≤ 带高（band_hi）视为进入带。同一轮（连续无整日离开带，离开 = low > band_hi）只计 1 次；
   触碰代表日取轮内 close 最低日（touch_low/touch_close 为 raw 价格明细）。
   - 轮内任一日收盘 ≥ 带低（band_lo）→ 有效触碰；
   - 整轮收盘刺穿下沿（close < band_lo）→ 需「修复」：自轮末起 {REPAIR_WIN} 个交易日内收盘回带上方（close ≥ band_hi）才算有效触碰，否则不计（真破位剔除）。
6. **过滤**：有效触碰 ≥ {MIN_TOUCHES} 次 且 首末触碰跨度（交易日 index 差）≥ {MIN_SPAN}。
7. **分档（level）**：1Y+（span ≥ 252）/ 6M+（≥ 126）/ 3M+（≥ 63）/ 1M+（≥ 21）。
8. **dist_pct** = (last_close − support_mid) / support_mid × 100；last_close 为数据末日的 **adj_close**。
9. **status**：above（dist_pct > +3%）/ near（±3% 内）/ below（dist_pct < −3%，已跌破）。
10. **strength**：touches ≥ 6 且 span ≥ 126 → A；touches ≥ 4 且 span ≥ 63，或 touches ≥ 8 → B；其余 → C。

## 文件结构

- `levels_summary.csv`：每只股票每个支撑位一行（15 字段）
- `touches/{{ticker}}.csv`：逐次触碰明细（7 字段）
- `README.md`：本文件

## 字段字典

levels_summary.csv：
| 字段 | 说明 |
|---|---|
| ticker | 代码（目录名，小写） |
| support_id | 同股票内编号，S1 最靠近现价（按 abs(dist_pct) 升序） |
| support_mid | 支撑带基准价（adj_close 口径，聚类中心） |
| support_lo / support_hi | 带下沿 / 带上沿（mid × (1∓2%)） |
| touches | 有效触碰次数 |
| first_touch_date / last_touch_date | 首次 / 末次触碰日期 |
| span_trading_days | 首末触碰跨度（交易日 index 差） |
| level | 1M+ / 3M+ / 6M+ / 1Y+ |
| last_close_date / last_close | 数据集末日及 adj_close 收盘 |
| dist_pct | (last_close − mid)/mid × 100 |
| status | above / near / below |
| strength | A / B / C |

touches/{{ticker}}.csv：
| 字段 | 说明 |
|---|---|
| ticker | 代码 |
| support_id | 对应支撑编号 |
| support_mid | 支撑带基准价 |
| touch_seq | 该支撑内按时间顺序的触碰序号 |
| touch_date | 触碰代表日（轮内 close 最低日） |
| touch_low / touch_close | 该日 raw low / raw close（实时口径明细） |

## 跳过/异常清单（{len(skipped)} 只）
"""
    if skipped:
        for t, r in skipped:
            readme += f"- {t}: {r}\n"
    else:
        readme += "- 无\n"

    with open(os.path.join(OUT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"\n===== 汇总 =====")
    print(f"levels_summary.csv 总行数: {len(summary_rows)}")
    print(f"覆盖代码数: {len(tickers_ok)}")
    print(f"跳过/异常: {len(skipped)}")
    for t, r in skipped:
        print(f"  - {t}: {r}")
    print(f"written: {summary_path} rows={len(summary_rows)}")
    print(f"written: {os.path.join(OUT_DIR, 'README.md')} size={os.path.getsize(os.path.join(OUT_DIR, 'README.md'))}")


if __name__ == "__main__":
    main()