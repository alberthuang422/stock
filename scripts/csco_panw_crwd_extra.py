# -*- coding: utf-8 -*-
"""CSCO/PANW/CRWD 扩展分析：累计收益、脱钩拐点、极端日联动"""
import pandas as pd, numpy as np, json, math, os

DATA = r"C:\Users\Administrator\Desktop\stock\data"
OUT = r"C:\Users\Administrator\Desktop\stock\results"

def load(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")
    return df[["adj_close"]].dropna()[~df.index.duplicated(keep="last")].sort_index()

tks = ["CSCO", "PANW", "CRWD"]
px = pd.concat([load(t) for t in tks], axis=1); px.columns = tks
ret = np.log(px / px.shift(1)).dropna()
D0 = pd.Timestamp("2026-02-01")

# 1) 累计收益（2026-02 至今 / 2026 年初至今）
def cumret(series, start):
    s = series[series.index >= start]
    return float((np.exp(s.cumsum().iloc[-1]) - 1) * 100)

out = {}
out["累计收益"] = {
    "2026-02-01至今_%": {t: round(cumret(ret[t], pd.Timestamp("2026-02-01")), 1) for t in tks},
    "2026-01-01至今_%": {t: round(cumret(ret[t], pd.Timestamp("2026-01-01")), 1) for t in tks},
}

# 2) 脱钩拐点：CSCO×PANW / CSCO×CRWD 的 60 日滚动相关首次跌破 0.30（从 2025 高位下行起算）
r60_cp = ret["CSCO"].rolling(60).corr(ret["PANW"]).dropna()
r60_cc = ret["CSCO"].rolling(60).corr(ret["CRWD"]).dropna()
r60_pc = ret["PANW"].rolling(60).corr(ret["CRWD"]).dropna()

def first_below(series, thr, after="2025-01-01"):
    s = series[series.index >= pd.Timestamp(after)]
    hit = s[s < thr]
    return str(hit.index[0].date()) if len(hit) else None

out["脱钩拐点"] = {
    "CSCO×PANW r60 首破0.30": first_below(r60_cp, 0.30),
    "CSCO×CRWD r60 首破0.30": first_below(r60_cc, 0.30),
    "PANW×CRWD r60 首破0.75(2026年以来极值)": first_below(r60_pc, 0.75),
}

# 3) PANW×CRWD 滚动相关逐月均值（2026 年以来）
roll_months = r60_pc[r60_pc.index >= pd.Timestamp("2026-01-01")].groupby(pd.Grouper(freq="ME")).mean()
out["PANW×CRWD r60 逐月均值"] = {str(k.date())[:7]: round(float(v), 4) for k, v in roll_months.items()}

# 4) 极端日联动：2026-02 以来 |收益|≥2σ（自身当日）的日子，三家方向一致性
focus = ret[ret.index >= D0]
std = focus.std()
extreme_days = pd.DataFrame(index=focus.index)
for t in tks:
    extreme_days[t] = (focus[t].abs() >= 2 * std[t])
any_ext = extreme_days.any(axis=1)
days = focus[any_ext]
rows = []
for d, row in days.iterrows():
    signs = [1 if row[t] > 0 else (-1 if row[t] < 0 else 0) for t in tks]
    same_dir = len(set(signs)) == 1  # 三家同方向
    rows.append({
        "date": str(d.date()),
        "CSCO%": round(row["CSCO"]*100, 2), "PANW%": round(row["PANW"]*100, 2), "CRWD%": round(row["CRWD"]*100, 2),
        "三家同向": same_dir, "CSCO_与两网安同向": signs[0]==signs[1] and signs[0]==signs[2],
    })
out["极端日明细"] = rows
out["极端日统计"] = {
    "总极端日数": len(rows),
    "CSCO与其他两家同向天数": sum(1 for r in rows if r["CSCO_与两网安同向"]),
    "PANW与CRWD同向天数": sum(1 for r in rows if (r["PANW%"]>0)==(r["CRWD%"]>0)),
}

# 5) PANW×CRWD 8月滚动相关 max
aug = r60_pc[r60_pc.index >= pd.Timestamp("2026-08-01")]
out["PANW×CRWD 8月以来 r60"] = {"max": round(float(aug.max()),4), "末值": round(float(aug.iloc[-1]),4)}

print(json.dumps(out, ensure_ascii=False, indent=1))
with open(os.path.join(OUT, "csco_panw_crwd_extra.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("SAVED extra")