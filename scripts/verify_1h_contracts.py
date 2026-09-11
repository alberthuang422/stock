# -*- coding: utf-8 -*-
"""校验 1h 合约 K 线产物：行数 / 日期范围 / 空文件标记"""
import os, glob, csv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMM = ["cl", "ho", "rb"]
THRESH = 1000  # 1h 低于此行数视为异常（180 天约 3000+ 根理论值）

for c in COMM:
    d = os.path.join(BASE, "data", f"{c}_contracts", "1h")
    files = sorted(glob.glob(os.path.join(d, "*.csv")))
    print(f"\n===== {c.upper()} 1h : {len(files)} 文件 =====")
    tot = 0
    bad = 0
    for fn in files:
        name = os.path.basename(fn)
        with open(fn, encoding="utf-8") as f:
            rows = list(csv.reader(f))
        n = len(rows) - 1
        tot += n
        if n == 0:
            print(f"  [EMPTY] {name}")
            bad += 1
            continue
        first, last = rows[1][0], rows[-1][0]
        flag = "  <-- 偏少" if n < THRESH else ""
        if n < THRESH:
            bad += 1
        print(f"  {name:16s} {n:5d} bars  {first} ~ {last}{flag}")
    print(f"  合计 {tot} bars, 异常 {bad}")
