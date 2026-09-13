# -*- coding: utf-8 -*-
"""
白糖「基本面类比年」筛选 —— 不用 ENSO 强度，只用糖自身基本面
候选集：ENSO 事件年（enList from results/sugar_enso_events.csv）
匹配维度：库消比水位 / 库消比同比变化 / 产需差率(是否紧缺) / 产量同比 / 消费同比
          / 过去3年库消比累计变化(库存周期相位)
距离：各维度按全样本 sd 尺度化后的欧氏距离（越接近 0 越像）
对照：事件后 T+12 / T+24 糖价收益（绝对 + 剔 Non-energy 商品 β 的超额）
"""
import os, re, json
import numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pd.set_option("display.width", 240)

# ---------- 1. 全球平衡表 -> 基本面变量 ----------
g = pd.read_csv(os.path.join(BASE, "data", "sugar", "sugar_global_sd.csv")).sort_values("Market_Year")
g = g[g.Market_Year >= 1960].reset_index(drop=True)
g["prod_yoy"]   = g.Production.pct_change() * 100
g["cons_yoy"]   = g["Total Disappearance"].pct_change() * 100
g["stocks_yoy"] = g["Ending Stocks"].pct_change() * 100
g["d_sur"]      = g.StockToUse.diff()
g["balance_pct"] = (g.Production - g["Total Disappearance"]) / g["Total Disappearance"] * 100
g["cum_d_sur_3y"] = g.d_sur.rolling(3).sum()

FEATS = ["sur", "d_sur", "balance_pct", "prod_yoy", "cons_yoy", "cum_d_sur_3y", "stocks_yoy"]
g = g.rename(columns={"StockToUse": "sur"})
G = g.set_index("Market_Year")

# 尺度：全样本 sd（尺度化绝对距离，保留"水平"信息）
SC = {f: G[f].std() for f in FEATS}
print("=== 各维度全样本 sd（1960-2026）===")
print({k: round(v, 2) for k, v in SC.items()})

# ---------- 2. ENSO 事件 -> 受影响榨季 ----------
ev = pd.read_csv(os.path.join(BASE, "results", "sugar_enso_events.csv"))
def onset_to_my(s):
    y, m = int(s[:4]), int(s[5:7])
    return y if m >= 10 else y - 1          # 项目铁律：onset 10-12月 -> 当年 MY；1-9月 -> 上一 MY
ev["MY"] = ev.onset.map(onset_to_my)
ev = ev[ev.MY.between(1961, 2026)].copy()

# ---------- 3. 目标 = 2026 当前状态 ----------
TARGET_MY = 2025
tgt = {f: float(G.loc[TARGET_MY, f]) for f in FEATS}
print("\n=== 目标：2026 当前状态（以 MY%d = 2025/26 榨季为基准）===" % TARGET_MY)
print({k: round(v, 2) for k, v in tgt.items()})

# ---------- 4. 匹配 ----------
rows = []
for _, e in ev.iterrows():
    my = int(e.MY)
    r = {"onset": e.onset, "MY": my, "season": f"{my}/{str(my+1)[2:]}",
         "T12": e.T12_abs, "T24": e.T24_abs, "T12_exc": e.T12_exc, "T24_exc": e.T24_exc}
    if my not in G.index:
        continue
    d2 = 0.0
    for f in FEATS:
        v = G.loc[my, f]
        if pd.isna(v):
            d2 = np.nan; break
        r[f] = round(float(v), 2)
        d2 += ((v - tgt[f]) / SC[f]) ** 2
    r["dist"] = round(float(np.sqrt(d2)), 3) if not pd.isna(d2) else np.nan
    rows.append(r)
res = pd.DataFrame(rows).dropna(subset=["dist"]).sort_values("dist").reset_index(drop=True)
res["rank"] = res.index + 1

SHOW = ["rank", "onset", "season", "sur", "d_sur", "balance_pct", "prod_yoy", "cons_yoy",
        "cum_d_sur_3y", "stocks_yoy", "dist", "T12", "T24", "T12_exc", "T24_exc"]
print("\n=== 基本面距离最小的 10 个 ENSO 事件年 ===")
print(res[SHOW].head(10).to_string(index=False))

print("\n=== 目标值 vs 最像的 3 年（逐维对照）===")
cmp = pd.DataFrame({"2026(目标)": tgt})
for _, r in res.head(3).iterrows():
    cmp[r.season] = {f: r[f] for f in FEATS}
print(cmp.round(2).to_string())

# 稳健性：换 MY2026 为目标
tgt2 = {f: float(G.loc[2026, f]) for f in FEATS}
r2 = []
for _, e in ev.iterrows():
    my = int(e.MY); d2 = 0.0
    for f in FEATS:
        v = G.loc[my, f]
        if pd.isna(v): d2 = np.nan; break
        d2 += ((v - tgt2[f]) / SC[f]) ** 2
    r2.append({"season": e.onset, "dist2": round(float(np.sqrt(d2)), 3) if not pd.isna(d2) else np.nan})
r2 = pd.DataFrame(r2).sort_values("dist2").head(10)
print("\n=== 稳健性：以 MY26 预测值(库消比 24.6%)为目标，重排前 10 ===")
print(r2.to_string(index=False))

out = {
    "meta": {"purpose": "基本面类比年（剔除 ENSO 强度）", "target_MY": TARGET_MY,
             "features": FEATS, "scale_sd": {k: round(v, 3) for k, v in SC.items()},
             "metric": "按全样本 sd 尺度化的欧氏距离，越小越像",
             "caveat": "候选集仍为 ENSO 事件年；不含任何天气强度变量"},
    "target": {k: round(v, 2) for k, v in tgt.items()},
    "ranking": res[SHOW].fillna("").to_dict("records"),
}
with open(os.path.join(BASE, "results", "sugar_analog_fundamental.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
res.to_csv(os.path.join(BASE, "results", "sugar_analog_fundamental.csv"), index=False)
print("\nwrote results/sugar_analog_fundamental.{json,csv}")
