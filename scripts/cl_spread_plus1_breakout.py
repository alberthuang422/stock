# -*- coding: utf-8 -*-
"""
CL +1 相邻月差：中端强度是否同步抬升 + 7/23 高点的突破盘点。
输出：results/cl_spread_plus1_breakout.json + 控制台表
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

r723  = d[d["ts"] == "2026-07-23"].iloc[0]
r910  = d[d["ts"] == "2026-09-10"].iloc[0]
r911  = d[d["ts"] == "2026-09-11"].iloc[0]
pre   = d[d["ts"] <= "2026-07-23"]          # 含 7/23
pre23 = d[d["ts"] <  "2026-07-23"]          # 不含 7/23
post  = d[d["ts"] >  "2026-07-23"]

rows = []
for seg, c in zip(SEG, COL):
    v723, v910, v911 = r723[c], r910[c], r911[c]
    premax, premax_d = pre23[c].max(), pre23.loc[pre23[c].idxmax(), "ts"]
    allmax, allmax_d = d[c].max(), d.loc[d[c].idxmax(), "ts"]
    rows.append(dict(
        seg=seg,
        v723=round(v723, 2),
        premax=round(premax, 2), premax_d=str(premax_d.date()),
        v910=round(v910, 2), v911=round(v911, 2),
        allmax=round(allmax, 2), allmax_d=str(allmax_d.date()),
        chg=round(v910 - v723, 2),
        pct=round((v910 / v723 - 1) * 100, 0) if v723 else np.nan,
        brk_723   = v910 > v723,                      # 突破 7/23 点位
        brk_pre   = v910 > premax,                    # 突破 7/23 之前的一切
        brk_all   = abs(allmax - v910) < 1e-9,        # 9/10 即全样本最高
    ))
t = pd.DataFrame(rows)

pd.set_option("display.width", 220)
print("【A】+1 月差：7/23 基准 → 9/10（收盘） 单位 USD/桶")
print(t[["seg","v723","premax","premax_d","v910","v911","allmax","allmax_d","chg","pct","brk_723","brk_pre","brk_all"]].to_string(index=False))

print("\n【B】突破盘点")
def tag(r):
    if r["brk_723"] and r["brk_pre"] and r["brk_all"]:
        return "✅ 三重突破（>7/23，>此前一切，9/10 即 128 日 ATH）"
    if r["brk_723"] and not r["brk_pre"]:
        return f"⚠️ 仅超 7/23 点位，但未超 7/23 前的 {r['premax']:.2f}（{r['premax_d']}）"
    if not r["brk_723"]:
        return f"❌ 未破 7/23（差 {r['v910']-r['v723']:+.2f}）"
    return "?"
for _, r in t.iterrows():
    print(f"  {r['seg']:<9} 7/23={r['v723']:>5.2f} → 9/10={r['v910']:>5.2f}  {r['pct']:>+6.0f}%   {tag(r)}")

print("\n【C】曲线形状进化（+1 月差）")
print(f"{'段':<9}{'7/23':>8}{'8/27':>8}{'9/10':>8}{'7/23→9/10':>12}{'份额7/23':>10}{'份额9/10':>10}")
r827 = d[d["ts"] == "2026-08-27"].iloc[0]
s723 = sum(r723[c] for c in COL); s910 = sum(r910[c] for c in COL)
for seg, c in zip(SEG, COL):
    print(f"{seg:<9}{r723[c]:>8.2f}{r827[c]:>8.2f}{r910[c]:>8.2f}{r910[c]-r723[c]:>+12.2f}{r723[c]/s723*100:>9.1f}%{r910[c]/s910*100:>9.1f}%")
print(f"{'合计':<9}{s723:>8.2f}{sum(r827[c] for c in COL):>8.2f}{s910:>8.2f}{s910-s723:>+12.2f}")

print("\n【D】分组平均变化（9/10 vs 7/23, USD）")
for name, sl in [("前端 M1-M3", t.iloc[0:3]), ("中端 M4-M9", t.iloc[3:9]), ("远端 M10-M12", t.iloc[9:12])]:
    print(f"  {name:<14} 均值 {sl['chg'].mean():+.2f}  中位 {sl['chg'].median():+.2f}  区间 [{sl['chg'].min():+.2f}, {sl['chg'].max():+.2f}]  "
          f"相对涨幅中位 {sl['pct'].median():+.0f}%")

print("\n【E】点位 vs 峰值 说明")
print("  M1-M2 的 7/23 值 4.08 是单日事件尖峰（7/22 收 2.73 → 7/23 4.08 → 7/27 崩回 2.10）")
print(f"  9/10 收盘 M1-M2 = {r910[COL[0]]:.2f} → {'已越过尖峰' if r910[COL[0]]>4.08 else '未越过尖峰'}")

out = dict(ts723="2026-07-23", rows=t.to_dict("records"),
           agg=dict(front=round(t.iloc[0:3]['chg'].mean(),2),
                    mid=round(t.iloc[3:9]['chg'].mean(),2),
                    back=round(t.iloc[9:12]['chg'].mean(),2)),
           sum723=round(s723,2), sum910=round(s910,2))
os.makedirs(os.path.join(BASE,"results"), exist_ok=True)
json.dump(out, open(os.path.join(BASE,"results","cl_spread_plus1_breakout.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nsaved -> results/cl_spread_plus1_breakout.json")
