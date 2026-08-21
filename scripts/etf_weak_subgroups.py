# -*- coding: utf-8 -*-
"""子组聚类调整超额（T+10），写回 etf_weak_support.json"""
import json
import numpy as np
import pandas as pd
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ev = pd.read_csv(os.path.join(ROOT, "results", "etf_weak_support_events.csv"), encoding="utf-8-sig")
D = json.load(open(os.path.join(ROOT, "results", "etf_weak_support.json"), encoding="utf-8"))
bl = D["baseline_stats"]

def cluster_excess(df, k=10):
    col = f"fwd{k}"
    d = df.dropna(subset=[col])
    if len(d) < 20: return None
    clu = d.groupby("date")[col].mean()
    m, s, n = float(clu.mean()), float(clu.std(ddof=1)), len(clu)
    base = bl[str(k)]["mean"]
    ex = clu - base
    t = float(ex.mean()) / (float(ex.std(ddof=1)) / np.sqrt(n)) if ex.std(ddof=1) > 0 else None
    return {"n": int(len(d)), "clusters": int(n),
            "mean": round(m, 2), "t_cluster": round(m/(s/np.sqrt(n)), 2) if s > 0 else None,
            "excess_pp": round(float(ex.mean()), 2), "excess_t": round(t, 2) if t else None,
            "win_cluster": round(float((clu > 0).mean()) * 100, 1)}

def tc(s):
    try: return int(s.split("(")[1].split("触")[0])
    except: return None
ev["tc"] = ev["support_touches"].map(tc)

groups = [
 ("全样本", ev),
 ("窗初(0-5日)", ev[ev["days_into_window"].between(0,5)]),
 ("窗中(6-15日)", ev[ev["days_into_window"].between(6,15)]),
 ("窗末(>15日)", ev[ev["days_into_window"]>15]),
 ("入场=连续3日低于EMA20", ev[ev["entry_reason"]=="连续3日低于EMA20"]),
 ("入场=死叉", ev[ev["entry_reason"]=="死叉"]),
 ("偏离-2~-5%", ev[ev["etf_depth_pct"].between(-5,-2)]),
 ("个股缩量(<=1.0)", ev[ev["stk_vol_ratio"]<=1.0]),
 ("弱于板块(RS<0)", ev[ev["rs5"]<0]),
 ("触次1-2", ev[ev["tc"].between(1,2)]),
 ("触次>=5", ev[ev["tc"]>=5]),
 ("VIX>=30", ev[ev["vix"]>=30]),
 ("XLV医疗", ev[ev["sector"]=="XLV"]),
 ("XLB材料", ev[ev["sector"]=="XLB"]),
 ("XLK科技", ev[ev["sector"]=="XLK"]),
 ("慢弱+缩量交集", ev[(ev["entry_reason"]=="连续3日低于EMA20")&(ev["stk_vol_ratio"]<=1.0)]),
 ("慢弱+窗末交集", ev[(ev["entry_reason"]=="连续3日低于EMA20")&(ev["days_into_window"]>15)]),
]
sub = {}
for name, g in groups:
    sub[name] = cluster_excess(g)
D["cluster_adjust"]["subgroups_t10"] = sub
with open(os.path.join(ROOT, "results", "etf_weak_support.json"), "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=1, allow_nan=False)
print("written: subgroups_t10 已并入（%d 组）" % len([v for v in sub.values() if v]))
