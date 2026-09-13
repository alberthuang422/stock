#!/usr/bin/env python3
"""体检 2026-09-11 用户提供的 15 个 NYMEX 下载 CSV（CL/HO/RB 各月合约 60m + RB 日线）。

目的（只读体检，不落库）：
1. 字段/粒度/时区是否一致
2. 每个合约的实际起止与 LTD 推断（验证 NYMEX「交割月前一月 25 日往回数第 3 个交易日」规则）
3. 月差对 (M1-M2) 的可重叠区间有多长 —— 决定回测样本量
4. 缺失/异常检测：无成交量字段、重复时间戳、OHLC 自洽性、长缺口
"""
from __future__ import annotations

import glob
import os
import re
import sys
from datetime import datetime

import pandas as pd

DL = "/Users/alberthuang/Downloads"
PATTERNS = ["NYMEX_DL_*.csv"]

MON2NUM = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
           "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}


def parse_symbol(fname: str):
    """从文件名解析 产品/交割月/年份/粒度。NYMEX_DL_CLQ2026, 60.csv"""
    base = os.path.basename(fname)
    m = re.match(r"NYMEX_DL_([A-Z]+)([A-Z0-9!]*)?,?\s*(\d+)([A-Z])?\.csv", base)
    stem = base[len("NYMEX_DL_"):]
    # 形如 "CLQ2026, 60.csv" / "RB1!, 1D.csv" / "RBU2026, 1D.csv"
    m2 = re.match(r"([A-Z]{2})([A-Z0-9!]+),\s*([0-9A-Za-z]+)\.csv$", stem)
    if not m2:
        return None
    prod, contract, gran = m2.group(1), m2.group(2), m2.group(3)
    # contract 形如 Q2026 或 1!
    mc = re.match(r"([FGHJKMNQUVXZ])(\d{4})$", contract)
    if mc:
        month = MON2NUM[mc.group(1)]
        year = int(mc.group(2))
        ctag = f"{mc.group(1)}{str(year)[2:]}"
    else:
        month, year, ctag = None, None, contract
    return {"product": prod, "contract": ctag, "month": month, "year": year,
            "gran_raw": gran, "fname": base}


def norm_gran(g: str) -> str:
    if g == "60":
        return "60m"
    if g.upper() == "1D":
        return "1d"
    if g.upper() == "4H":
        return "4h"
    return g


def load(fname: str) -> pd.DataFrame:
    df = pd.read_csv(fname)
    df.columns = [c.strip() for c in df.columns]
    tcol = "time" if "time" in df.columns else ("datetime" if "datetime" in df.columns else df.columns[0])
    df = df.rename(columns={tcol: "ts_raw"})
    has_tz = df["ts_raw"].astype(str).str.contains(r"[+-]\d{2}:\d{2}").any()
    df["ts"] = pd.to_datetime(df["ts_raw"], utc=True, format="mixed")
    # 注：utc=True 已统一为 tz-aware；纯日期文件会被当作 UTC 午夜，
    # 日线分析只用 .date()，不做时区换算（NYMEX 结算日本身就是自然日口径）。
    df["has_tz"] = has_tz
    return df


def ohlc_check(df: pd.DataFrame) -> dict:
    out = {}
    need = {"open", "high", "low", "close"}
    out["has_ohlc"] = need.issubset(set(df.columns))
    if not out["has_ohlc"]:
        return out
    d = df.dropna(subset=["open", "high", "low", "close"])
    out["rows"] = len(df)
    out["nan_ohlc"] = int(len(df) - len(d))
    out["bad_high_lt_low"] = int((d["high"] < d["low"]).sum())
    out["bad_high_lt_close"] = int((d["high"] < d["close"] - 1e-9).sum())
    out["bad_low_gt_close"] = int((d["low"] > d["close"] + 1e-9).sum())
    out["zero_close"] = int((d["close"] == 0).sum())
    out["neg_close"] = int((d["close"] < 0).sum())
    # 完全不动的 bar（open=high=low=close）占比：流动性极差的信号
    flat = (d["high"] == d["low"]) & (d["open"] == d["close"])
    out["pct_flat_bars"] = round(100.0 * flat.mean(), 2)
    return out


def dup_and_gap(df: pd.DataFrame, is_daily: bool) -> dict:
    out = {}
    out["dup_ts"] = int(df["ts"].duplicated().sum())
    out["monotonic"] = bool(df["ts"].is_monotonic_increasing)
    d = df.drop_duplicates("ts").sort_values("ts")
    if is_daily:
        return out
    diff = d["ts"].diff().dropna()
    out["gap_gt_6h"] = int((diff > pd.Timedelta(hours=6)).sum())
    out["max_gap_h"] = round(float(diff.max().total_seconds() / 3600), 1) if len(diff) else None
    return out


def main():
    files = []
    for p in PATTERNS:
        files += sorted(glob.glob(os.path.join(DL, p)))
    rows = []
    loaded = {}
    for f in files:
        info = parse_symbol(f)
        if info is None:
            print(f"[SKIP] 无法解析文件名: {os.path.basename(f)}", file=sys.stderr)
            continue
        info["gran"] = norm_gran(info["gran_raw"])
        df = load(f)
        loaded[(info["product"], info["contract"], info["gran"])] = df
        info["first"] = str(df["ts"].min())
        info["last"] = str(df["ts"].max())
        info["n"] = len(df)
        info["cols"] = ",".join([c for c in df.columns if c not in ("ts", "ts_raw", "has_tz")])
        info["tz_in_file"] = bool(df["has_tz"].iloc[0])
        info.update(ohlc_check(df))
        info.update(dup_and_gap(df, info["gran"] == "1d"))
        rows.append(info)

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 60)
    show = ["product", "contract", "gran", "n", "first", "last", "tz_in_file",
            "rows", "nan_ohlc", "bad_high_lt_low", "dup_ts", "monotonic",
            "pct_flat_bars", "gap_gt_6h", "max_gap_h"]
    show = [c for c in show if c in df.columns]
    print("=" * 130)
    print("【1】逐文件体检")
    print("=" * 130)
    print(df[show].to_string(index=False))

    print()
    print("=" * 130)
    print("【2】字段与粒度差异")
    print("=" * 130)
    for _, r in df.iterrows():
        print(f"  {r['product']:<3} {r['contract']:<5} {r['gran']:<4} cols=[{r['cols']}]")

    # ---- LTD 推断：用数据最后一根 bar 所在交易日 ----
    print()
    print("=" * 130)
    print("【3】LTD 推断（用每个合约最后一根 bar 的日期）")
    print("=" * 130)
    ltd = {}
    for _, r in df[df["gran"] == "60m"].iterrows():
        d = loaded[(r["product"], r["contract"], r["gran"])]
        # 文件内带 +08:00 时区 → 转 ET 取交易日
        det = d["ts"].dt.tz_convert("America/New_York")
        last_et = det.max()
        ltd[(r["product"], r["contract"])] = last_et
        ym = "n/a" if pd.isna(r["year"]) else f"{int(r['year'])}-{int(r['month']):02d}"
        print(f"  {r['product']:<3} {r['contract']:<5} 交割月={ym}  "
              f"最后bar(ET)={last_et.strftime('%Y-%m-%d %H:%M %a')}  数据起点(ET)="
              f"{det.min().strftime('%Y-%m-%d')}")

    # ---- 月差对重叠区间 ----
    print()
    print("=" * 130)
    print("【4】月差对 (M1−M2) 可用重叠区间 —— 决定样本量")
    print("=" * 130)
    for prod in ["CL", "HO", "RB"]:
        sub = df[(df["product"] == prod) & (df["gran"] == "60m")].copy()
        if sub.empty:
            print(f"  {prod}: 无 60m 数据")
            continue
        sub["key"] = sub["year"].fillna(0) * 100 + sub["month"].fillna(0)
        sub = sub.sort_values("key")
        items = []
        for _, r in sub.iterrows():
            d = loaded[(r["product"], r["contract"], r["gran"])]
            det = d["ts"].dt.tz_convert("America/New_York")
            items.append((r["contract"], r["key"], det))
        print(f"\n  --- {prod} ---")
        for i in range(len(items) - 1):
            c1, k1, t1 = items[i]
            c2, k2, t2 = items[i + 1]
            lo = max(t1.min(), t2.min())
            hi = min(t1.max(), t2.max())
            if hi <= lo:
                print(f"  {c1}−{c2}: 无重叠")
                continue
            both = t1[(t1 >= lo) & (t1 <= hi)]
            other = t2[(t2 >= lo) & (t2 <= hi)]
            common = both.isin(set(other))
            nbar = int(common.sum())
            ndays = both[common].dt.normalize().nunique()
            print(f"  {c1}−{c2}: {lo.strftime('%Y-%m-%d')} ~ {hi.strftime('%Y-%m-%d')}  "
                  f"重叠bar={nbar:>5}  重叠交易日={ndays:>3}  "
                  f"(注：含 {c1} 的 LTD 前脏区)")

    # ---- 缺口日历 ----
    print()
    print("=" * 130)
    print("【5】60m 序列的大缺口（>6h）位置，判断是否非交易时段还是真缺数据")
    print("=" * 130)
    for (prod, contract, gran), d in loaded.items():
        if gran != "60m":
            continue
        det = d["ts"].dt.tz_convert("America/New_York").sort_values()
        diff = det.diff()
        big = diff[diff > pd.Timedelta(hours=6)]
        if len(big) == 0:
            continue
        locs = []
        for idx in big.index[:6]:
            prev = det.shift(1).loc[idx]
            locs.append(f"{prev.strftime('%m-%d %H:%M')}→{det.loc[idx].strftime('%m-%d %H:%M')}({diff.loc[idx].total_seconds()/3600:.0f}h)")
        print(f"  {prod}{contract}: {len(big)} 处 >6h  | " + "; ".join(locs))


if __name__ == "__main__":
    main()
