# -*- coding: utf-8 -*-
"""
CL +1 月差：中端为何走强——形态诊断（前端独陡 vs 中端 hump）
输出：results/cl_mid_why_diagnostics.json
"""
import pandas as pd, numpy as np, json, os, datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGS = ["CL2610","CL2611","CL2612","CL2701","CL2702","CL2703","CL2704","CL2705","CL2706","CL2707","CL2708","CL2709","CL2710"]
ci = json.load(open(os.path.join(BASE,"data/cl_contracts/contract_info.json"), encoding="utf-8"))
EXP = {x["code"].replace("US.",""): (dt.datetime.fromtimestamp(x["last_trade_time"]/1000, dt.timezone.utc) - dt.timedelta(hours=4)).date()
       for x in ci["future_info"] if x["code"].replace("US.","") in LEGS}
d = pd.read_csv(os.path.join(BASE,"data/cl_contracts/spread/cl_spread_daily.csv"))
d["ts"] = pd.to_datetime(d["ts"]); d = d.sort_values("ts").reset_index(drop=True)

CODES = [("OCT26","NOV26"),("NOV26","DEC26"),("DEC26","JAN27"),("JAN27","FEB27"),
         ("FEB27","MAR27"),("MAR27","APR27"),("APR27","MAY27"),("MAY27","JUN27"),
         ("JUN27","JUL27"),("JUL27","AUG27"),("AUG27","SEP27"),("SEP27","OCT27")]
COL = [f"abs1_{a}_{b}" for a, b in CODES]
SEG = [f"M{i+1}-M{i+2}" for i in range(12)]

# 每日：日归一化对数斜率（严格可比口径）
slop = pd.DataFrame(index=d.index)
for k, (c, seg) in enumerate(zip(COL, SEG)):
    a, b = LEGS[k], LEGS[k+1]
    gap = (EXP[b] - EXP[a]).days
    slop[seg] = 365.0/gap*np.log(d[a]/d[b])*100
slop["ts"] = d["ts"].values

print("【1】日归一化对数斜率（年化 %）：谁最陡？")
print(f"{'date':<11}" + "".join(f"{s:>8}" for s in SEG))
for lab in ["2026-03-10","2026-05-19","2026-07-23","2026-08-05","2026-08-27","2026-09-10","2026-09-11"]:
    r = slop[slop.ts == lab]
    if len(r):
        print(f"{lab:<11}" + "".join(f"{r[s].iloc[0]:>8.1f}" for s in SEG))
print("\n每日最陡段（argmax）分布：")
arg = slop[SEG].idxmax(axis=1)
vc = arg.value_counts()
for s in SEG:
    if s in vc.index:
        print(f"  {s:<9} {vc[s]:>3} 天 ({vc[s]/len(arg)*100:>5.1f}%)")

print("\n【2】前 3 段（M1-M3）斜率均值 vs 中端（M4-M9）斜率均值 —— 谁更陡")
d2 = d.copy()
for k, (c, seg) in enumerate(zip(COL, SEG)):
    d2[seg] = slop[seg]
d2["sl_front"] = d2[SEG[0:3]].mean(axis=1)
d2["sl_mid"]   = d2[SEG[3:9]].mean(axis=1)
d2["sl_back"]  = d2[SEG[9:12]].mean(axis=1)
print(f"{'date':<11}{'front':>8}{'mid':>8}{'back':>8}{'front>mid?':>12}")
for lab in ["2026-03-10","2026-04-20","2026-05-19","2026-06-20","2026-07-23","2026-08-05","2026-08-27","2026-09-10","2026-09-11"]:
    r = d2[d2.ts == lab]
    if len(r):
        r = r.iloc[0]
        print(f"{lab:<11}{r['sl_front']:>8.1f}{r['sl_mid']:>8.1f}{r['sl_back']:>8.1f}{('是' if r['sl_front']>r['sl_mid'] else '否'):>12}")
k = (d2["sl_front"] > d2["sl_mid"]).sum()
print(f"→ 全样本 {len(d2)} 天中，前端斜率均值 > 中端的天数：{k} 天（{k/len(d2)*100:.1f}%）")

print("\n【3】份额结构（+1 月差合计占比 %）")
d2["front"] = d2[SEG[0:3]].sum(axis=1); d2["mid"] = d2[SEG[3:9]].sum(axis=1)
d2["back"] = d2[SEG[9:12]].sum(axis=1); d2["tot"] = d2[SEG].sum(axis=1)
for lab in ["2026-03-10","2026-04-20","2026-05-19","2026-07-23","2026-08-05","2026-08-27","2026-09-10"]:
    r = d2[d2.ts == lab].iloc[0]
    print(f"  {lab}  前端 {r['front']/r['tot']*100:>4.1f}%  中端 {r['mid']/r['tot']*100:>4.1f}%  远端 {r['back']/r['tot']*100:>4.1f}%  合计 {r['tot']:.2f}")

print("\n【4】中端/前端 比值：全样本分布")
d2["mf"] = d2["mid"]/d2["front"]
print(f"  全样本 129 日：≥1 的天数 {(d2['mf']>=1).sum()} 天（{(d2['mf']>=1).mean()*100:.0f}%），中位 {d2['mf'].median():.2f}，区间 [{d2['mf'].min():.2f}, {d2['mf'].max():.2f}]")
for a, b, lab in [("2026-03-10","2026-05-08","3/10-5/08"),("2026-05-11","2026-07-17","5/11-7/17"),
                  ("2026-07-20","2026-08-06","7/20-8/06"),("2026-08-07","2026-09-11","8/07-9/11")]:
    w = d2[(d2.ts >= a) & (d2.ts <= b)]
    print(f"  {lab:<12} n={len(w):>3}  ≥1 天数 {(w['mf']>=1).sum():>3} ({(w['mf']>=1).mean()*100:>5.0f}%)  中位 {w['mf'].median():.2f}")

print("\n【5】持仓量分布（9/11 收盘，手）")
oi = {}
for L in LEGS:
    t = pd.read_csv(os.path.join(BASE, f"data/cl_contracts/daily/US.{L}.csv")); t["date"] = pd.to_datetime(t["date"])
    oi[L] = (t.iloc[-1]["open_interest"], t.iloc[-1]["close"])
tot_oi = sum(v[0] for v in oi.values())
for L in LEGS:
    print(f"  {L:<9} OI {oi[L][0]:>9,.0f}  占 13 腿 {oi[L][0]/tot_oi*100:>5.1f}%   收 {oi[L][1]:>7.2f}")

print("\n【6】中端/前端 比值 vs 价格水平 & 总陡度 相关性")
sub = d2[["mf","tot"]].copy(); sub["px"] = d2["CL2610"]
sub["dte"] = [ (EXP["CL2610"] - t.date()).days for t in d2["ts"] ]
print(f"  corr(mf, 2610收盘价)  = {sub['mf'].corr(sub['px']):+.3f}")
print(f"  corr(mf, 月差总额)     = {sub['mf'].corr(sub['tot']):+.3f}")
print(f"  corr(mf, 2610 剩余到期日) = {sub['mf'].corr(sub['dte']):+.3f}")

print("\n【7】远端 M10-M13 的历史峰值（说明远端不自洽）")
for c, seg in zip(COL[9:12], SEG[9:12]):
    mx = d2[c].max(); md = d2.loc[d2[c].idxmax(), "ts"].date()
    print(f"  {seg:<9} 全样本峰值 {mx:.2f} @ {md}   现值 {d2[c].iloc[-2]:.2f}")

out = dict(argmax_counts={k:int(v) for k,v in vc.items()},
           front_gt_mid_days=int(k), n_days=int(len(d2)),
           mf_median=float(d2['mf'].median()),
           corr=dict(px=float(sub['mf'].corr(sub['px'])), tot=float(sub['mf'].corr(sub['tot'])), dte=float(sub['mf'].corr(sub['dte']))),
           oi={L:int(oi[L][0]) for L in LEGS})
json.dump(out, open(os.path.join(BASE,"results","cl_mid_why_diagnostics.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("\nsaved -> results/cl_mid_why_diagnostics.json")
