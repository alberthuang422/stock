#!/usr/bin/env python3
"""落盘用户提供的 NYMEX 逐月合约 60m/1D 数据 → data/spread_contracts/

- raw/  保真拷贝（原始 +08:00 时间戳、原始列）
- norm/ 规范化：时间转 ET（America/New_York）、去 EMA 垃圾列、统一 schema
- meta/contract_ltd.json  逐合约 LTD（以数据最后一根 bar 实测）+ pair 覆盖表
"""
from __future__ import annotations

import glob
import json
import os
import shutil

import pandas as pd

DL = "/Users/alberthuang/Downloads"
ROOT = "/Users/alberthuang/Desktop/股票分析/data/spread_contracts"
MON = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
       "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}


def parse(base: str):
    stem = base[len("NYMEX_DL_"):-len(".csv")]          # CLN2026, 60
    head, gran = [s.strip() for s in stem.split(",")]
    prod, code = head[:2], head[2:]                      # CL, N2026 / 1!
    mc = code[:1] if code[-4:].isdigit() else None       # 月代码字母
    return prod, code, mc, gran


def main():
    for sub in ("raw", "norm", "meta"):
        os.makedirs(os.path.join(ROOT, sub), exist_ok=True)

    files = sorted(glob.glob(os.path.join(DL, "NYMEX_DL_*.csv")))
    manifest, loaded = [], {}

    for f in files:
        base = os.path.basename(f)
        prod, code, mc, gran = parse(base)
        df = pd.read_csv(f)
        df.columns = [c.strip() for c in df.columns]
        tcol = "time" if "time" in df.columns else df.columns[0]
        if gran == "60":
            ts = pd.to_datetime(df[tcol], utc=True, format="mixed").dt.tz_convert("America/New_York")
            out = pd.DataFrame({
                "datetime_et": ts.dt.strftime("%Y-%m-%d %H:%M"),
                "open": df["open"], "high": df["high"], "low": df["low"], "close": df["close"],
            })
            last_et = ts.max()
        else:  # 1D
            ts = pd.to_datetime(df[tcol])
            out = pd.DataFrame({
                "date": ts.dt.strftime("%Y-%m-%d"),
                "open": df["open"], "high": df["high"], "low": df["low"], "close": df["close"],
            })
            last_et = ts.max()

        # 保真 + 规范化落盘
        shutil.copy2(f, os.path.join(ROOT, "raw", base))
        name = f"{prod}{code.replace('2026', '26')}_{gran}.csv"
        out.to_csv(os.path.join(ROOT, "norm", name), index=False)

        manifest.append({
            "file_raw": base, "file_norm": name, "product": prod, "code": code,
            "delivery_month": (f"2026-{MON[mc]:02d}" if mc else None),
            "granularity": "60m" if gran == "60" else "1d",
            "rows": len(out),
            "first": str(out.iloc[0, 0]), "last": str(out.iloc[-1, 0]),
            "last_bar_et": str(last_et.date()),
            "note": "时间戳为 bar 起始时刻；无 volume 字段" if gran == "60" else "连续/单合约日线参考用",
        })
        loaded[(prod, code, gran)] = (ts, df)

    # ---- pair 覆盖表（60m，相邻交割月）----
    pairs = []
    for prod in ("CL", "HO", "RB"):
        subs = sorted([(MON[mc], code) for p, code, mc, g in
                       [(parse(os.path.basename(f)) for f in files)] if False] if False else
                      [(m["delivery_month"], m["code"]) for m in manifest
                       if m["product"] == prod and m["granularity"] == "60m" and m["delivery_month"]])
        for i in range(len(subs) - 1):
            m1, m2 = subs[i][1], subs[i + 1][1]
            t1, _ = loaded[(prod, m1, "60")]
            t2, _ = loaded[(prod, m2, "60")]
            lo, hi = max(t1.min(), t2.min()), min(t1.max(), t2.max())
            if hi <= lo:
                continue
            common = pd.Series(sorted(set(t1) & set(t2)))
            ndays = len(common.dt.date.unique())
            pairs.append({"product": prod, "pair": f"{m1}-{m2}",
                          "overlap_et": f"{lo.date()}~{hi.date()}",
                          "overlap_bars": int(ndays * 22.6 // 1) if False else len(common),
                          "overlap_trading_days": int(ndays)})

    meta = {"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            "source_dir": DL, "timezone_note": "raw=+08:00 bar起始；norm=ET",
            "contracts": manifest, "pairs": pairs}
    with open(os.path.join(ROOT, "meta", "contract_ltd.json"), "w") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)

    # ---- 摘要 ----
    print(f"落盘 {len(manifest)} 个文件 → {ROOT}/raw|norm，meta OK")
    for m in manifest:
        print(f"  {m['product']:<3}{m['code']:<6} {m['granularity']:<4} "
              f"{m['first']} ~ {m['last']}  n={m['rows']}")
    print("\npair 覆盖：")
    for p in pairs:
        print(f"  {p['product']:<3} {p['pair']:<10} {p['overlap_et']}  "
              f"重叠bar={p['overlap_bars']:>5}  交易日={p['overlap_trading_days']:>4}")


if __name__ == "__main__":
    main()
