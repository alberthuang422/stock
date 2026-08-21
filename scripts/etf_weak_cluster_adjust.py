# -*- coding: utf-8 -*-
"""聚类独立性调整：事件按"信号日"聚类（同日多股共享宏观冲击），
计算聚类调整后的均值/t 统计量与有效独立样本数，并写回 JSON。"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

ev = pd.read_csv(os.path.join(RES, "etf_weak_support_events.csv"), encoding="utf-8-sig")
with open(os.path.join(RES, "etf_weak_support.json"), encoding="utf-8") as f:
    D = json.load(f)

out = {}
for k in (1, 5, 10, 20):
    col = f"fwd{k}"
    d = ev.dropna(subset=[col])
    # 按信号日聚类：同日多股取均值 → 得到一个簇均值序列
    clu = d.groupby("date")[col].mean()
    n_clu = len(clu)
    m = float(clu.mean())
    s = float(clu.std(ddof=1)) if n_clu > 1 else 0.0
    t = m / (s / np.sqrt(n_clu)) if s > 0 else None
    # 簇规模分布（同日多股事件占比）
    sizes = d.groupby("date").size()
    out[str(k)] = {
        "n_events": int(len(d)),
        "n_clusters": int(n_clu),
        "cluster_mean": round(m, 3),
        "cluster_std": round(s, 3),
        "tstat_cluster": round(t, 2) if t is not None else None,
        "naive_tstat": (D["event_stats"].get(str(k)) or {}).get("tstat"),
        "multi_day_pct": round(float((sizes > 1).mean()) * 100, 1),
        "max_cluster_size": int(sizes.max()),
        "win_cluster": round(float((clu > 0).mean()) * 100, 1),
    }

# 超额收益（事件 - 基线）的聚类调整
bl = D["baseline_stats"]
excess = {}
for k in (1, 5, 10, 20):
    col = f"fwd{k}"
    d = ev.dropna(subset=[col])
    clu = d.groupby("date")[col].mean()
    base = (bl.get(str(k)) or {}).get("mean")
    if base is None:
        continue
    ex = clu - base
    n_clu = len(ex)
    m = float(ex.mean())
    s = float(ex.std(ddof=1)) if n_clu > 1 else 0.0
    t = m / (s / np.sqrt(n_clu)) if s > 0 else None
    excess[str(k)] = {"excess_mean": round(m, 3), "excess_tstat": round(t, 2) if t is not None else None,
                      "baseline_mean": base}

D["cluster_adjust"] = {"by_horizon": out, "excess_vs_baseline": excess,
                       "method": "按信号日聚类（同日多股取均值后对簇均值做单样本t检验）；超额=簇均值-全交易日基线均值"}
with open(os.path.join(RES, "etf_weak_support.json"), "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=1, allow_nan=False)

for k in ("1", "5", "10", "20"):
    o = out[k]; e = excess.get(k, {})
    print(f"T+{k:>2}: 事件{o['n_events']} → 簇{o['n_clusters']}（多股同日{o['multi_day_pct']}%, 最大簇{o['max_cluster_size']}）"
          f" | 簇均值{o['cluster_mean']:+.2f}% t={o['tstat_cluster']}（naive t={o['naive_tstat']}）"
          f" | 超额基线 {e.get('excess_mean')}% t={e.get('excess_tstat')}")
print("written: cluster_adjust 已并入 etf_weak_support.json")
