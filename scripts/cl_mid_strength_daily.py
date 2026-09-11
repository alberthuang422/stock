# -*- coding: utf-8 -*-
"""
CL +1 月差：中端（M4-M9）逐日走强路径分析
输出：results/cl_mid_strength_daily.json + 控制台表
"""
import pandas as pd, numpy as np, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(os.path.join(BASE, "data/cl_contracts/spread/cl_spread_daily.csv"))
d["ts"] = pd.to_datetime(d["ts"]); d = d.sort_values("ts").reset_index(drop=True)

CODES = [("OCT26","NOV26"),("NOV26","DEC26"),("DEC26","JAN27"),("JAN27","FEB27"),
         ("FEB27","MAR27"),("MAR27","APR27"),("APR27","MAY27"),("MAY27","JUN27"),
         ("JUN27","JUL27"),("JUL27","AUG27"),("AUG27","SEP27"),("SEP27","OCT27")]
COL = [f"abs1_{a}_{b}" for a, b in CODES]
SEG = [f"M{i+1}-M{i+2}" for i in range(12)]
for s, c in zip(SEG, COL):
    d[s] = d[c]

d["front"] = d[SEG[0:3]].sum(axis=1)
d["mid"]   = d[SEG[3:9]].sum(axis=1)
d["back"]  = d[SEG[9:12]].sum(axis=1)
d["tot"]   = d[SEG].sum(axis=1)
d["mf"]    = d["mid"] / d["front"]          # 中端/前端
d["mf_ma5"] = d["mf"].rolling(5).mean()
d["mid_pct"] = d["mid"].rank(pct=True) * 100

BASE_DAY = "2026-07-23"
b = d[d.ts == BASE_DAY].iloc[0]
for g in ["front", "mid", "back", "tot"]:
    d[f"idx_{g}"] = d[g] / b[g] * 100

# ---- 各段首次收复 7/23 水平 ----
print("【1】各段首次收盘收复 7/23 水平（含 7/23 之后）")
post = d[d.ts > BASE_DAY]
first = []
for s in SEG:
    v = b[s]
    hit = post[post[s] >= v]
    first.append((s, round(v, 2), str(hit.ts.iloc[0].date()) if len(hit) else "未收复", round(hit[s].iloc[0], 2) if len(hit) else None))
for g in ["front", "mid", "back", "tot"]:
    v = b[g]
    hit = post[post[g] >= v]
    first.append((g.upper(), round(v, 2), str(hit.ts.iloc[0].date()) if len(hit) else "未收复", round(hit[g].iloc[0], 2) if len(hit) else None))
print(f"{'组/段':<10}{'7/23值':>8}{'首次收复':>12}{'当日值':>8}")
for a, v, dt, hv in first:
    print(f"{a:<10}{v:>8.2f}{dt:>12}{'' if hv is None else f'{hv:>8.2f}'}")

# ---- 逐日明细（8/04 起）----
print("\n【2】逐日明细（USD/桶）：金额 + 日变化 + 相对强度")
w = d[d.ts >= "2026-08-04"].copy()
print(f"{'date':<11}{'total':>7}{'Δ':>7}{'front':>7}{'Δ':>7}{'mid':>7}{'Δ':>7}{'back':>7}{'Δ':>6}{'mid/front':>10}{'ma5':>6}{'idx_mid':>9}{'idx_front':>10}")
prev = None
for _, r in w.iterrows():
    dt_ = "" if prev is None else f"{r['tot']-prev['tot']:+.2f}"
    df_ = "" if prev is None else f"{r['front']-prev['front']:+.2f}"
    dm_ = "" if prev is None else f"{r['mid']-prev['mid']:+.2f}"
    db_ = "" if prev is None else f"{r['back']-prev['back']:+.2f}"
    print(f"{str(r['ts'].date()):<11}{r['tot']:>7.2f}{dt_:>7}{r['front']:>7.2f}{df_:>7}{r['mid']:>7.2f}{dm_:>7}{r['back']:>7.2f}{db_:>6}{r['mf']:>10.2f}{r['mf_ma5']:>6.2f}{r['idx_mid']:>9.0f}{r['idx_front']:>10.0f}")
    prev = r

# ---- 比值结构统计 ----
def stat(a, z):
    sl = d[(d.ts >= a) & (d.ts <= z)]
    return len(sl), (sl["mf"] >= 1).sum(), round(sl["mf"].median(), 2)
print("\n【3】中端/前端 比值结构（mf>=1 的天数占比）")
for a, z, lab in [("2026-07-06","2026-07-17","7/06-7/17"),
                  ("2026-07-20","2026-08-06","7/20-8/06"),
                  ("2026-08-07","2026-09-10","8/07-9/10"),
                  ("2026-08-31","2026-09-10","8/31-9/10")]:
    n, k, med = stat(a, z)
    print(f"  {lab:<12} n={n:>3}  mf>=1 天数 {k:>3} ({k/n*100:>5.0f}%)  中位 {med}")

# ---- 增量归因（自 8/25 起）----
print("\n【4】增量贡献拆解")
for a, lab in [("2026-08-25","8/25→9/10"), ("2026-07-23","7/23→9/10"), ("2026-03-10","3/10→9/10")]:
    s0 = d[d.ts == a].iloc[0]; s1 = d[d.ts == "2026-09-10"].iloc[0]
    df, dm, db = s1["front"]-s0["front"], s1["mid"]-s0["mid"], s1["back"]-s0["back"]
    tt = df + dm + db
    print(f"  {lab:<12} 合计 {s0['tot']:.2f}→{s1['tot']:.2f} (+{tt:.2f})  前端 +{df:.2f}({df/tt*100:.0f}%)  中端 +{dm:.2f}({dm/tt*100:.0f}%)  远端 +{db:.2f}({db/tt*100:.0f}%)")

# ---- 中端 6 段逐日（近 12 日）----
print("\n【5】中端 6 段逐日值（USD）")
w2 = d[d.ts >= "2026-08-25"]
print(f"{'date':<11}" + "".join(f"{s:>9}" for s in SEG[3:9]) + f"{'sum':>8}")
for _, r in w2.iterrows():
    print(f"{str(r['ts'].date()):<11}" + "".join(f"{r[s]:>9.2f}" for s in SEG[3:9]) + f"{r['mid']:>8.2f}")

out = dict(base=BASE_DAY,
           first_reclaim={a: dict(v723=v, date=dt, val=hv) for a, v, dt, hv in first},
           rows=w[["ts","tot","front","mid","back","mf","idx_mid","idx_front","idx_back"]].assign(
                 ts=lambda x: x["ts"].dt.strftime("%Y-%m-%d")).to_dict("records"))
os.makedirs(os.path.join(BASE, "results"), exist_ok=True)
json.dump(out, open(os.path.join(BASE, "results", "cl_mid_strength_daily.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nsaved -> results/cl_mid_strength_daily.json")
