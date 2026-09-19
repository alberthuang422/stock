# -*- coding: utf-8 -*-
"""稳健性对照：阈值(分位×价格分位)敏感性网格, 输出各格 n/胜率/均值/p"""
import json, math
from datetime import timedelta

ROOT = "C:/Users/Administrator/Desktop/stock"
OUT_JSON = ROOT + "/results/cftc_sugar_divergence_robust.json"

# 直接复用主脚本的数据装配: 导入模块会重跑主流程并产出主结果(无害)
import importlib
import cftc_sugar_divergence as M   # 提供 weeks, fwd_ret, Abs_FLOOR_ODS, p_one_sided_pos, bl_all

weeks, fwd_ret = M.weeks, M.fwd_ret
p_one = M.p_one_sided_pos
ABS_FLOOR = 10000.0

def variant(grp, ratio_q, pct_q, use_floor=True):
    ratios = sorted(abs(w["d_" + grp]) / w["oi"] for w in weeks)
    r_thr = ratios[int(round((1 - ratio_q) * (len(ratios) - 1)))]  # top ratio_q → 第(1-q)分位
    p_thrs = sorted(abs(w["pct"]) for w in weeks)
    p_thr = p_thrs[int(round(pct_q * (len(p_thrs) - 1)))]
    evs = []
    for w in sorted(weeks, key=lambda x: x["date"]):
        dc = w["d_" + grp]
        if dc is None: continue
        if abs(dc) / w["oi"] < r_thr: continue
        if use_floor and abs(dc) < ABS_FLOOR: continue
        if abs(w["pct"]) >= p_thr: continue
        if not evs or (w["date"] - next(e["date"] for e in reversed(evs))).days >= 28:
            evs.append(w)
    res = {}
    for days, lbl in ((28, "fwd4"), (56, "fwd8"), (91, "fwd13")):
        vals = [(e["date"], fwd_ret(e["date"], days)) for e in evs]
        vals = [v for _, v in vals if v is not None]
        if not vals: continue
        base = next(b for b in M.bl_all if b["lbl"] == lbl)
        p0 = base["win"] / 100.0
        k = sum(1 for v in vals if v > 0)
        res[lbl] = {"n": len(vals), "mean": round(sum(vals)/len(vals), 2),
                    "median": round(sorted(vals)[len(vals)//2], 2),
                    "win": round(100*k/len(vals), 1),
                    "lift": round(100*k/len(vals) - base["win"], 1),
                    "p": round(p_one(k, len(vals), p0), 4)}
    return res

grid = []
for grp, label in (("nc", "noncommercial"), ("c", "commercial")):
    for rq, pq in ((0.05, 0.30), (0.10, 0.40), (0.15, 0.40)):
        for use_floor in (True, False):
            r = variant(grp, rq, pq, use_floor)
            grid.append({"grp": label, "ratio_q": rq, "pct_q": pq,
                         "abs_floor": use_floor, "res": r})
            print(label, rq * 100, "%OI, price_q=", pq, "floor=", use_floor)
            for lbl, s in r.items():
                print("   ", lbl, s)

json.dump(grid, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", OUT_JSON)
