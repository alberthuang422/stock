#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从日线数据补充周线数据。

周线约定（逆向工程自仓库已有的 `*, W.csv`）：
  1. 价格列使用复权价：adj_ratio = adj_close / close，作用于 open/high/low/close；
     close 直接用 adj_close。
  2. 按"周五结束"的自然周重采样：
       open  = 周内首交易日复权 open
       high  = 周内复权 high 最大值
       low   = 周内复权 low 最小值
       close = 周内末交易日复权 close (= adj_close)
       volume= 周内每日 volume 之和
  3. 周线日期标签取该周最后一个实际交易日（完整周=周五；末周不完整=最后交易日）。

每个 `X, 1D.csv` 对应生成 `X, W.csv`；若已存在则跳过。
"""
import os
import glob
import numpy as np
import pandas as pd

DATA_DIR = r"C:\Users\Administrator\Desktop\stock\data"


def is_supported(daily_path):
    """返回 (是否支持, 原因)。BATS 等已预计算 MACD 的指标文件不支持。"""
    try:
        cols = pd.read_csv(daily_path, nrows=0).columns
    except Exception as e:
        return False, f"read header failed: {e}"
    if "time" in cols and "date" not in cols:
        return False, "MACD/BATS 指标文件(非原始OHLCV)，跳过"
    need = {"date", "open", "high", "low", "close"}
    missing = need - set(cols)
    if missing:
        return False, f"缺少必要列 {sorted(missing)}"
    return True, ""


def daily_to_weekly(daily_path):
    df = pd.read_csv(daily_path)
    has_vol = "volume" in df.columns
    if not has_vol:
        df["volume"] = 0.0
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    close = df["close"].astype(float).values
    if "adj_close" in df.columns:
        adj = df["adj_close"].astype(float).values
    else:
        adj = close  # 指数等无复权
    ratio = np.where(close != 0, adj / close, 1.0)
    for c in ["open", "high", "low"]:
        df["adj_" + c] = df[c].astype(float).values * ratio
    df["adj_close_final"] = adj
    # 用 .values 避免 set_index 后的索引错位
    df["volume_f"] = df["volume"].astype(float).values if has_vol else 0.0

    df = df.set_index("date")
    agg = df.resample("W-FRI").agg(
        open=("adj_open", "first"),
        high=("adj_high", "max"),
        low=("adj_low", "min"),
        close=("adj_close_final", "last"),
        volume=("volume_f", "sum"),
        _ld=("adj_close_final", lambda s: s.index.max()),  # 安全：空组返回 NaT
    )
    agg = agg.dropna(subset=["close"]).copy()
    agg = agg.set_index("_ld")
    agg.index.name = "date"
    out = agg.reset_index()[["date", "open", "high", "low", "close", "volume"]]
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def validate(daily_path, weekly_path):
    gen = daily_to_weekly(daily_path)
    existing = pd.read_csv(weekly_path)
    existing["date"] = existing["date"].astype(str)
    gen["date"] = gen["date"].astype(str)
    m = existing.merge(gen, on="date", suffixes=("_exist", "_gen"), how="inner")
    cols = ["open", "high", "low", "close", "volume"]
    print(f"[validate] {os.path.basename(daily_path)}: rows exist={len(existing)} gen={len(gen)} merged={len(m)}")
    for c in cols:
        diff = (m[c + "_exist"] - m[c + "_gen"]).abs()
        rel = diff / m[c + "_exist"].abs().replace(0, np.nan)
        print(f"   {c:7s} max_abs={diff.max():.3e}  max_rel={rel.max():.3e}")
    return m


def main():
    daily_files = glob.glob(os.path.join(DATA_DIR, "*", "*, 1D.csv"))
    # 规范化分隔符：把 "X, 1D.csv" 的逗号+空格作为文件名一部分处理
    # glob 已正确匹配，下面用 os.path 解析
    to_generate = []
    skipped = []          # 已有 W.csv
    skipped_unsupported = []  # BATS/MACD 等
    for d in sorted(daily_files):
        folder = os.path.dirname(d)
        base = os.path.basename(d)            # e.g. "aapl, 1D.csv"
        stem = base[:-len(", 1D.csv")]        # e.g. "aapl"
        weekly_path = os.path.join(folder, stem + ", W.csv")
        if os.path.exists(weekly_path):
            skipped.append(weekly_path)
            continue
        ok, reason = is_supported(d)
        if not ok:
            skipped_unsupported.append((d, reason))
            continue
        to_generate.append((d, weekly_path))

    print(f"daily files found: {len(daily_files)}")
    print(f"already have W.csv (skip): {len(skipped)}")
    print(f"unsupported/skipped (BATS/MACD等): {len(skipped_unsupported)}")
    print(f"to generate: {len(to_generate)}")

    # 校验：用 aapl 对照已有周线
    aapl_d = os.path.join(DATA_DIR, "aapl", "aapl, 1D.csv")
    aapl_w = os.path.join(DATA_DIR, "aapl", "aapl, W.csv")
    if os.path.exists(aapl_d) and os.path.exists(aapl_w):
        validate(aapl_d, aapl_w)

    generated = []
    errors = []
    for d, w in to_generate:
        try:
            out = daily_to_weekly(d)
            out.to_csv(w, index=False)
            generated.append((w, len(out)))
        except Exception as e:
            errors.append((d, repr(e)))

    print(f"\n[done] generated: {len(generated)}  errors: {len(errors)}")
    for w, n in generated:
        print(f"   + {w}  ({n} rows)")
    for d, e in errors:
        print(f"   ! {d}  {e}")
    if skipped_unsupported:
        print(f"\n[skipped unsupported] {len(skipped_unsupported)}")
        for d, r in skipped_unsupported:
            print(f"   - {d}  ({r})")


if __name__ == "__main__":
    main()
