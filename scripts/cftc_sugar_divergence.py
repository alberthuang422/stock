# -*- coding: utf-8 -*-
"""97号：白糖 CFTC 非商业/商业持仓变动 x 价格变动 背离事件研究（2012-2026）
口径（grill-me 讨论 locking）:
- 持仓: data/sugar/sugar_cftc_futonly_1986_2026.csv (Futures Only), 窗口内 2012-01 起
- 价格: data/sugar/sb_price_daily.csv (ICEUS SB1! 1D, 2011-12-23 ~ 2026-09-18)
- 变动窗口: CFTC 报告日(周二收盘仓位快照) -> 下一报告周, 价格按周二对周二 pct_change
- 异常增仓: |Δnet|/OI 进入全样本前 5% 分位 且 |Δnet|>=10000 手
- 背离: 上述异常 且 |价格周变动| 处于全样本后 30% 分位 (价格未按持仓方向走)
- 事件簇: 相邻触发间隔 <4周 归并, 取簇首
- 前瞻: 4/8/13 周 (28/56/91 日), 基准率=全样本周度, lift + 单尾二项近似 p
- 版本: 非商业(nc_net) 与 商业(c_net) 双对照
"""
import csv, json, math, statistics
from datetime import date, timedelta

ROOT = "C:/Users/Administrator/Desktop/stock"
CFTC_CSV = ROOT + "/data/sugar/sugar_cftc_futonly_1986_2026.csv"
PX_CSV   = ROOT + "/data/sugar/sb_price_daily.csv"
OUT_JSON = ROOT + "/results/cftc_sugar_divergence_events.json"
OUT_SUM  = ROOT + "/results/cftc_sugar_divergence_summary.json"

START = date(2012, 1, 1)

def fnum(x):
    try: return float(x)
    except: return None

# ---------- load CFTC ----------
rows = list(csv.DictReader(open(CFTC_CSV, encoding="utf-8-sig")))
cftc = []
for r in rows:
    d = date.fromisoformat(r["date"])
    if d < START: continue
    cftc.append({
        "date": d,
        "oi": float(r["oi"]),
        "nc_net": float(r["nc_net"]),
        "c_net": float(r["c_net"]),
        "nc_l": float(r["nc_l"]), "nc_s": float(r["nc_s"]),
        "c_l": float(r["c_l"]), "c_s": float(r["c_s"]),
    })
cftc.sort(key=lambda x: x["date"])

# Δnet 与 Δoi
for i, r in enumerate(cftc):
    if i == 0:
        r["d_nc"], r["d_c"] = None, None
    else:
        r["d_nc"] = r["nc_net"] - cftc[i-1]["nc_net"]
        r["d_c"]  = r["c_net"]  - cftc[i-1]["c_net"]

# ---------- load price ----------
prows = list(csv.DictReader(open(PX_CSV, encoding="utf-8-sig")))
px = [(date.fromisoformat(r["time"]), float(r["close"])) for r in prows]
pdates = [d for d, _ in px]
pmap = dict(px)

def price_on_or_before(d):
    # 二分: 最后一个 <= d 的交易日
    import bisect
    i = bisect.bisect_right(pdates, d) - 1
    return px[i] if i >= 0 else None

def price_on_or_after(d):
    import bisect
    i = bisect.bisect_left(pdates, d)
    return px[i] if i < len(px) else None

# 每个报告周: 周二对周二价格变动
weeks = []
for i, r in enumerate(cftc):
    if i == 0: continue
    base = price_on_or_before(r["date"])
    nxt  = price_on_or_after(r["date"] + timedelta(days=7))
    if not base or not nxt or not r["d_nc"]: continue
    pct = (nxt[1] / base[1] - 1) * 100.0
    weeks.append({"date": r["date"], "pct": pct, **r})

# ---------- thresholds ----------
Abs_FLOOR_ODS = 10000.0
for grp in ("nc", "c"):
    ratios = [abs(w["d_" + grp]) / w["oi"] for w in weeks]
    ratio_thr = sorted(ratios)[int(round(0.95 * (len(ratios)-1)))]
    pct_abs   = [abs(w["pct"]) for w in weeks]
    pct_thr   = sorted(pct_abs)[int(round(0.30 * (len(pct_abs)-1)))]
    grp_thr = {"ratio_thr": ratio_thr * 100.0, "pct_thr": pct_thr}
    globals()[grp + "_thr"] = grp_thr

def find_events(grp):
    ratio_thr = globals()[grp + "_thr"]["ratio_thr"] / 100.0
    pct_thr   = globals()[grp + "_thr"]["pct_thr"]
    evs = []
    for w in weeks:
        dchange = w["d_" + grp]
        if dchange is None or w["oi"] <= 0: continue
        ratio = abs(dchange) / w["oi"]
        if ratio < ratio_thr or abs(dchange) < Abs_FLOOR_ODS: continue
        if abs(w["pct"]) >= pct_thr: continue   # 价格走了 → 共振, 非背离
        evs.append(w)
    # 4周聚类取簇首
    events, last = [], None
    for e in evs:
        if last is None or (e["date"] - last).days >= 28:
            events.append(e)
            last = e["date"]
    return events

def fwd_ret(dbase, days):
    tgt = price_on_or_after(dbase + timedelta(days=days))
    base = price_on_or_before(dbase)
    if not tgt or not base: return None
    return (tgt[1] / base[1] - 1) * 100.0

def p_one_sided_pos(k, n, p0):
    if n == 0: return None
    mu, sd = n * p0, math.sqrt(n * p0 * (1 - p0))
    if sd == 0: return None
    z = (k - 0.5 - mu) / sd
    return 0.5 * math.erfc(z / math.sqrt(2))

def stats(events, dbase_key="date"):
    res = {}
    for fwd_days, lbl in ((28, "fwd4"), (56, "fwd8"), (91, "fwd13")):
        vals = []
        for e in events:
            v = fwd_ret(e[dbase_key], fwd_days)
            if v is not None: vals.append((e["date"], v))
        if not vals: continue
        xs = [v for _, v in vals]
        res[lbl] = {"n": len(vals), "mean": statistics.mean(xs),
                    "median": statistics.median(xs),
                    "win": 100.0 * sum(1 for x in xs if x > 0) / len(xs)}
    return res

# ---------- baseline (all weeks) ----------
baseline = {}
bl_all = []
for fwd_days, lbl in ((28, "fwd4"), (56, "fwd8"), (91, "fwd13")):
    xs = [(w["date"], fwd_ret(w["date"], fwd_days)) for w in weeks]
    xs = [(d, v) for d, v in xs if v is not None]
    vals = [v for _, v in xs]
    bl_all.append({"lbl": lbl, "n": len(vals), "mean": statistics.mean(vals),
                   "median": statistics.median(vals),
                   "win": 100.0 * sum(1 for v in vals if v > 0) / len(vals),
                   "vals": vals})
    baseline[lbl] = bl_all[-1]

# ---------- mechanism segments ----------
SEGMENTS = [
    ("2012-2016 熊市回落+厄尼诺反弹", date(2012,1,1),  date(2016,12,31)),
    ("2017-2019 底部探底区间",        date(2017,1,1),  date(2019,12,31)),
    ("2020-2024 上行与高位震荡",      date(2020,1,1),  date(2024,12,31)),
    ("2025+ 缺口定价行情",            date(2025,1,1),  date(2026,12,31)),
]

out = {"meta": {
    "window": "2012-01-01 ~ 2026-09-08(cftc) / 2026-09-18(price)",
    "abs_floor_lots": Abs_FLOOR_ODS,
    "nc_thr": globals()["nc_thr"], "c_thr": globals()["c_thr"],
    "n_weeks_matched": len(weeks),
    "cluster_rule": "gap>=28d new event; take first of cluster",
}, "baseline": bl_all, "groups": {}}

for grp, label in (("nc", "noncommercial"), ("c", "commercial")):
    evs = find_events(grp)
    st = {}
    for fwd_days, lbl in ((28, "fwd4"), (56, "fwd8"), (91, "fwd13")):
        xs = [(e["date"], fwd_ret(e["date"], fwd_days)) for e in evs]
        xs = [(d, v) for d, v in xs if v is not None]
        vals = [v for _, v in xs]
        if not vals: continue
        base = next(b for b in bl_all if b["lbl"] == lbl)
        p0 = base["win"] / 100.0
        k = sum(1 for v in vals if v > 0)
        st[lbl] = {"n": len(vals), "mean": statistics.mean(vals),
                   "median": statistics.median(vals),
                   "win": 100.0 * k / len(vals),
                   "lift_win_pp": (100.0 * k / len(vals)) - base["win"],
                   "p_binom_pos": p_one_sided_pos(k, len(vals), p0)}
    # 机制段
    segs = []
    for name, d0, d1 in SEGMENTS:
        sub = [e for e in evs if d0 <= e["date"] <= d1]
        segs.append({"name": name, "n_raw": len(sub),
                     "events": [{"date": str(e["date"]),
                                 "d_" + grp: e["d_" + grp],
                                 "ratio_pct": 100*abs(e["d_"+grp])/e["oi"],
                                 "pct": e["pct"],
                                 "fwd4": fwd_ret(e["date"],28),
                                 "fwd8": fwd_ret(e["date"],56),
                                 "fwd13": fwd_ret(e["date"],91)} for e in sub]})
    detail = [{"date": str(e["date"]),
               "d": e["d_"+grp], "oi": e["oi"],
               "ratio_pct": 100*abs(e["d_"+grp])/e["oi"],
               "pct": e["pct"],
               "fwd4": fwd_ret(e["date"],28),
               "fwd8": fwd_ret(e["date"],56),
               "fwd13": fwd_ret(e["date"],91)} for e in evs]
    out["groups"][label] = {"thr": globals()[grp + "_thr"], "events": detail,
                            "stats": st, "segments": segs}

json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("weeks:", len(weeks))
print("nc_thr(5%:", round(out['meta']['nc_thr']['ratio_thr'],2), "%OI ; 30% price:", round(out['meta']['nc_thr']['pct_thr'],2), "%)")
print("c_thr(5%:", round(out['meta']['c_thr']['ratio_thr'],2), "%OI ; 30% price:", round(out['meta']['c_thr']['pct_thr'],2), "%)")
for g in ("noncommercial", "commercial"):
    e = out["groups"][g]["events"]
    print(g, "events:", len(e))
    for s in out["groups"][g]["stats"].items():
        print(" ", s[0], s[1])
with open(OUT_SUM, "w", encoding="utf-8") as fo:
    json.dump({k: v for k, v in out.items() if k != "baseline" or True}, fo, ensure_ascii=False, indent=1)
