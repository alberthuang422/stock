# -*- coding: utf-8 -*-
"""全覆盖审计：把共振事件扫描从 5板块×17股 扩到 9板块×全部30只道指成分股
目的：量化"被遗漏的同日共振事件"有多少、结论是否稳健。
复用 djia_sector_support.py 的信号函数（同口径）。
"""
import os, json, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from djia_sector_support import (
    load, etf_breakdown_days, stock_support_days, WARM, atr_series,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

# 原报告覆盖的 17 对
ORIG_PAIRS = [
    ("XLF", "JPM"), ("XLF", "AXP"), ("XLF", "GS"),
    ("XLK", "MSFT"), ("XLK", "AAPL"), ("XLK", "NVDA"), ("XLK", "CSCO"),
    ("XLI", "CAT"), ("XLI", "HON"), ("XLI", "BA"),
    ("XLV", "UNH"), ("XLV", "JNJ"), ("XLV", "AMGN"), ("XLV", "MRK"),
    ("XLP", "WMT"), ("XLP", "PG"), ("XLP", "KO"),
]
# 全覆盖：9 板块 × 全部 30 只道指成分股
FULL_PAIRS = [
    ("XLF", "JPM"), ("XLF", "GS"), ("XLF", "AXP"), ("XLF", "V"), ("XLF", "TRV"),
    ("XLK", "MSFT"), ("XLK", "AAPL"), ("XLK", "NVDA"), ("XLK", "CSCO"), ("XLK", "IBM"), ("XLK", "CRM"),
    ("XLI", "CAT"), ("XLI", "HON"), ("XLI", "BA"), ("XLI", "MMM"),
    ("XLV", "UNH"), ("XLV", "JNJ"), ("XLV", "AMGN"), ("XLV", "MRK"),
    ("XLP", "WMT"), ("XLP", "PG"), ("XLP", "KO"),
    ("XLE", "CVX"),
    ("XLY", "HD"), ("XLY", "MCD"), ("XLY", "NKE"), ("XLY", "AMZN"),
    ("XLB", "SHW"),
    ("XLC", "DIS"), ("XLC", "VZ"),
]

def grouped_stats(cache, items):
    ks = (1, 5, 10, 20)
    per_k = {str(k): [] for k in ks}
    for tk, t, entry in items:
        c = cache[tk]["adj_close"].values
        n = len(c)
        for k in ks:
            if t + k < n:
                per_k[str(k)].append((c[t + k] / entry - 1) * 100)
    agg = {}
    for k in ks:
        v = np.array(per_k[str(k)])
        if len(v) == 0:
            agg[str(k)] = None; continue
        agg[str(k)] = {
            "n": int(len(v)), "mean": round(float(v.mean()), 2),
            "median": round(float(np.median(v)), 2),
            "win": round(float(np.mean(v > 0)) * 100, 1),
            "std": round(float(v.std(ddof=1)), 2) if len(v) > 1 else 0,
        }
    return agg

def classify(cache, ev):
    f5, f10, f20 = ev.get("fwd5"), ev.get("fwd10"), ev.get("fwd20")
    if f10 is None or f20 is None:
        return "未完整"
    tk, t, entry = ev["ticker"], ev["t"], ev["entry"]
    c = cache[tk]["adj_close"].values
    hi10 = (np.max(c[t + 1:t + 11]) / entry - 1) * 100 if t + 10 < len(c) else None
    lo5 = (np.min(c[t + 1:t + 6]) / entry - 1) * 100
    if ev.get("support_broken_day") is not None or (f5 is not None and f5 < -4):
        return "支撑击穿"
    if hi10 is not None and hi10 >= 2 and (f10 <= 0 or f20 < -1):
        return "死猫反弹"
    if f5 is not None and f5 > 0 and f20 > 0 and lo5 > -5:
        return "V型反转"
    return "横盘消化"

def scan_pairs(pairs, cache):
    etf_break_cache = {}
    events = []
    for etf_tk, stk_tk in pairs:
        etf = cache.get(etf_tk)
        stk = cache.get(stk_tk)
        if etf is None or stk is None:
            continue
        if etf_tk not in etf_break_cache:
            etf_break_cache[etf_tk] = etf_breakdown_days(etf)
        breaks = etf_break_cache[etf_tk]
        touches = stock_support_days(stk)
        etf_idx = {d: i for i, d in enumerate(pd.Series(etf["date"].values).dt.normalize())}
        closes = stk["adj_close"].values
        dates = pd.Series(stk["date"].values).dt.normalize().values
        n = len(stk)
        for t in range(WARM, n):
            if t not in touches:
                continue
            d = dates[t]
            ei = etf_idx.get(d)
            if ei is None or ei not in breaks:
                continue
            tmeta = touches[t]
            entry = closes[t]
            lvl = tmeta["level"]
            broken = None
            for k2 in range(1, 11):
                if t + k2 < n and closes[t + k2] < lvl * 0.98:
                    broken = k2; break
            rec = {"pair": f"{etf_tk}/{stk_tk}", "sector": etf_tk, "ticker": stk_tk,
                   "date": str(pd.Timestamp(d).date()), "t": int(t), "entry": round(float(entry), 3),
                   "support_kinds": tmeta["kinds"], "support_broken_day": broken}
            for k in (1, 5, 10, 20):
                rec[f"fwd{k}"] = round((closes[t + k] / entry - 1) * 100, 2) if t + k < n else None
            rec["cls"] = classify(cache, rec)
            events.append(rec)
    return events

def main():
    cache = {}
    need = set()
    for a, b in FULL_PAIRS:
        need.add(a); need.add(b)
    missing = []
    for tk in need:
        try:
            cache[tk] = load(tk)
        except FileNotFoundError:
            missing.append(tk)
    if missing:
        print("数据缺失:", missing)

    full_ev = scan_pairs(FULL_PAIRS, cache)
    orig_ev = scan_pairs(ORIG_PAIRS, cache)

    def clean(o):
        if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [clean(x) for x in o]
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return round(float(o), 3)
        if isinstance(o, (np.bool_,)): return bool(o)
        if isinstance(o, float) and (np.isnan(o) or np.isinf(o)): return None
        return o

    full_stats = grouped_stats(cache, [(e["ticker"], e["t"], e["entry"]) for e in full_ev])
    orig_stats = grouped_stats(cache, [(e["ticker"], e["t"], e["entry"]) for e in orig_ev])

    def cls_count(evs):
        from collections import Counter
        c = Counter(e["cls"] for e in evs)
        tot = sum(v for k, v in c.items() if k != "未完整")
        return {k: {"n": int(v), "pct": round(v / tot * 100, 1) if tot else 0} for k, v in c.items()}

    # 新增部分 = 全覆盖 - 原配对
    orig_keys = set((e["ticker"], e["date"]) for e in orig_ev)
    added_ev = [e for e in full_ev if (e["ticker"], e["date"]) not in orig_keys]
    added_stats = grouped_stats(cache, [(e["ticker"], e["t"], e["entry"]) for e in added_ev])

    # 按板块拆分新增
    added_by_sector = {}
    for e in added_ev:
        added_by_sector.setdefault(e["sector"], []).append(e)

    out = {
        "orig_n": len(orig_ev), "full_n": len(full_ev), "added_n": len(added_ev),
        "orig_stats": orig_stats, "full_stats": full_stats, "added_stats": added_stats,
        "orig_cls": cls_count(orig_ev), "full_cls": cls_count(full_ev), "added_cls": cls_count(added_ev),
        "added_by_sector_n": {k: len(v) for k, v in added_by_sector.items()},
        "full_by_sector_n": pd.Series([e["sector"] for e in full_ev]).value_counts().to_dict(),
        "missing_data": missing,
        "added_events": clean(sorted(added_ev, key=lambda x: x["date"])),
        "full_events": clean(sorted(full_ev, key=lambda x: x["date"])),
    }
    out = clean(out)
    with open(os.path.join(RES, "djia_full_coverage_audit.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, allow_nan=False)

    # 控制台 KPI
    print(f"原配对(17对) 事件 {len(orig_ev)} → 全覆盖(30股×9板块) 事件 {len(full_ev)}，新增 {len(added_ev)}")
    for k in ("1", "5", "10", "20"):
        o, fu, ad = orig_stats[k], full_stats[k], added_stats[k]
        if not fu: continue
        print(f"T+{k:>2}: 原 n={o['n']} 均{o['mean']:+.2f}% 胜{o['win']:.0f}%"
              f" | 全覆盖 n={fu['n']} 均{fu['mean']:+.2f}% 胜{fu['win']:.0f}%"
              f" | 新增 n={ad['n']} 均{ad['mean']:+.2f}% 胜{ad['win']:.0f}%")
    print("结局 全覆盖:", {k: v["pct"] for k, v in out['full_cls'].items()})
    print("结局 新增部分:", {k: v["pct"] for k, v in out['added_cls'].items()})
    print("新增按板块:", out["added_by_sector_n"])
    print("written: results/djia_full_coverage_audit.json")

if __name__ == "__main__":
    main()
