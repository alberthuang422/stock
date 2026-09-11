# -*- coding: utf-8 -*-
"""定向补拉 1h 里 EMPTY 的标的（避免全量重跑）"""
import os, sys, time, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import fetch_cl_contracts_20260910 as F

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KTYPE = "9"
F.MIN_DATE = "2026-03-10"
F.END_DATE = dt.date.today().isoformat()
F.FORCE = True

TARGETS = [
    ("US.CL2706", os.path.join(BASE, "data", "cl_contracts", "1h")),
    ("US.HO2701", os.path.join(BASE, "data", "ho_contracts", "1h")),
    ("US.HO2706", os.path.join(BASE, "data", "ho_contracts", "1h")),
    ("US.RB2701", os.path.join(BASE, "data", "rb_contracts", "1h")),
    ("US.RB2706", os.path.join(BASE, "data", "rb_contracts", "1h")),
    ("US.CLcurrent", os.path.join(BASE, "data", "cl_contracts", "1h")),
    ("US.HOcurrent", os.path.join(BASE, "data", "ho_contracts", "1h")),
    ("US.RBcurrent", os.path.join(BASE, "data", "rb_contracts", "1h")),
]

F.init()
for sym, out in TARGETS:
    # current 连续合约偶发空，多试几次
    for attempt in range(3):
        n = F.pull(sym, KTYPE, out)
        if n > 0:
            break
        time.sleep(3)
    print(f"  >> {sym}: {n} bars")
print("REFILL DONE")
