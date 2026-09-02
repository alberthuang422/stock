# -*- coding: utf-8 -*-
"""
BATS CVS 1D（TradingView 导出）→ 项目 7 列格式，覆盖 data/cvs/CVS, 1D.csv
- 源: ~/Downloads/BATS_CVS, 1D.csv（time,open,high,low,close,RSI,...,Volume,... 共 17 列，复权口径）
- 目标: date,open,high,low,close,volume,adj_close（adj_close=close，源数据本身为复权价）
- 校验: 行数/日期单调/锚点（2022-02-08 高点≈95 前复权、2026-09-01 close 97.6）
"""
import os
import shutil

SRC = r"C:\Users\Administrator\Downloads\BATS_CVS, 1D.csv"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(BASE, "data", "cvs", "CVS, 1D.csv")

rows = []
with open(SRC, encoding="utf-8-sig") as f:
    header = f.readline().strip().split(",")
    idx = {c: i for i, c in enumerate(header)}
    for line in f:
        line = line.strip()
        if not line:
            continue
        p = line.split(",")
        d = p[idx["time"]]
        o, h, l, c = (p[idx[k]] for k in ("open", "high", "low", "close"))
        v = p[idx["Volume"]]
        rows.append((d, o, h, l, c, v, c))

assert len(rows) > 3900, f"行数异常: {len(rows)}"
assert all(rows[i][0] < rows[i + 1][0] for i in range(len(rows) - 1)), "日期非单调递增"
m = {r[0]: r for r in rows}
# 锚点校验：09-01 收盘 97.6；2022-02-08 前复权高点应 ~95（富途 95.30 锚）
last = rows[-1]
assert last[0] == "2026-09-01" and abs(float(last[4]) - 97.6) < 0.05, f"末日异常: {last}"
a = m.get("2022-02-08")
assert a is not None and abs(float(a[2]) - 95.30) < 1.0, f"2022-02-08 高点异常: {a[2] if a else '缺'}"

shutil.copyfile(SRC, os.path.join(BASE, "Temp", "bats_cvs_1d_raw.csv"))
with open(DST, "w", encoding="utf-8") as f:
    f.write("date,open,high,low,close,volume,adj_close\n")
    for r in rows:
        f.write(",".join(str(x) for x in r) + "\n")
print(f"OK {len(rows)} 行 {rows[0][0]} ~ {last[0]}")
print(f"锚点: 2022-02-08 high={float(a[2]):.2f} (富途前复权 95.30)")
print(f"      2026-09-01 close={float(last[4]):.2f}")
