#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""涨≥3% 事件细分: 突破型(创120日新高 / +放量) vs 非突破型, 比较 T+1/T+5/T+10。
口径: adj_close(复权) 判定新高; volume 原始成交量判定放量(>20日均量1.5x)。
"""
import os, json
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PHARMA = ["GILD", "ABBV", "LLY", "AMGN", "VRTX", "MRK", "JNJ", "REGN", "BIIB"]
BIOTECH = ["ALNY", "NTRA", "ILMN", "RVMD", "ARGX"]
NS = (1, 5, 10)


def load(tkr):
    d = os.path.join(DATA, tkr.lower())
    f = [x for x in os.listdir(d) if x.endswith(".csv") and not x.startswith("BATS")][0]
    df = pd.read_csv(os.path.join(d, f), parse_dates=["date"])
    df = df[["date", "adj_close", "volume"]].dropna().sort_values("date").reset_index(drop=True)
    df["ret"] = df["adj_close"].pct_change()
    for N in NS:
        df[f"fwd{N}"] = df["adj_close"].shift(-N) / df["adj_close"] - 1.0
    # 突破判定: 当日收盘 > 此前120日最高收盘 (严格新高)
    df["hi120"] = df["adj_close"].rolling(120).max().shift(1)
    df["is_new_high"] = df["adj_close"] > df["hi120"]
    # 放量判定: 当日量 > 此前20日均量*1.5
    df["vma20"] = df["volume"].rolling(20).mean().shift(1)
    df["vol_surge"] = df["volume"] > df["vma20"] * 1.5
    return df


def stats(a):
    a = np.asarray(a, dtype=float)
    a = a[~np.isnan(a)]
    if len(a) == 0:
        return None
    return dict(n=int(a.size),
                mean=round(float(a.mean()) * 100, 2),
                med=round(float(np.median(a)) * 100, 2),
                win=round(float((a > 0).mean()) * 100, 1))


def report(pool, tkrs, tag):
    ev = []  # (tkr, date, is_nh, vol_surge, fwd dict)
    dfs = {t: load(t) for t in tkrs}
    for t in tkrs:
        df = dfs[t]
        m = df["ret"] >= 0.03
        for idx in df.index[m]:
            r = df.loc[idx]
            if not np.isfinite(r["fwd10"]):
                continue
            ev.append(dict(tkr=t, nh=bool(r["is_new_high"]), vs=bool(r["vol_surge"]),
                           f1=r["fwd1"], f5=r["fwd5"], f10=r["fwd10"]))
    print(f"\n===== {pool} ({tag}) =====")
    groups = [
        ("全部涨≥3%", lambda e: True),
        ("① 非突破(未创120日新高)", lambda e: not e["nh"]),
        ("② 突破(创120日新高)", lambda e: e["nh"]),
        ("②a 突破+放量", lambda e: e["nh"] and e["vs"]),
        ("②b 突破+缩量/平量", lambda e: e["nh"] and not e["vs"]),
    ]
    for name, fn in groups:
        sub = [e for e in ev if fn(e)]
        if not sub:
            print(f"  {name}: n=0")
            continue
        parts = [f"{name}: n={len(sub)}"]
        for N in NS:
            s = stats([e[f"f{N}"] for e in sub])
            parts.append(f"T+{N} {s['mean']:+.2f}/{s['med']:+.2f}/胜{s['win']}%")
        print("  " + " | ".join(parts))
    # 突破后失败率: T+5/T+10 收盘 < 突破日收盘
    sub = [e for e in ev if e["nh"]]
    if sub:
        print(f"  突破后收低于突破日: T+5 {(1-(np.array([e['f5'] for e in sub])>0).mean())*100:.1f}% | T+10 {(1-(np.array([e['f10'] for e in sub])>0).mean())*100:.1f}%")
    # 突破占比
    nh_n = sum(1 for e in ev if e["nh"])
    nhv_n = sum(1 for e in ev if e["nh"] and e["vs"])
    print(f"  新高突破占比: {nh_n}/{len(ev)} = {nh_n/len(ev)*100:.0f}% | 其中放量 {nhv_n}/{nh_n} = {nhv_n/max(nh_n,1)*100:.0f}%")


report("PHARMA", PHARMA, "涨≥3% 细分")
report("BIOTECH", BIOTECH, "涨≥3% 细分")
