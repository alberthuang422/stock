# -*- coding: utf-8 -*-
"""KO vs PEP 相对强弱量化分析（本地日线数据 1990~2026-08）"""
import os, sys, json
import pandas as pd
import numpy as np

DATA = r"C:/Users/Administrator/Desktop/stock/data"

def load(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df

ko = load("KO"); pep = load("PEP")
end = ko.index.max()
print("数据截至:", end.date())
print("PEP 截至:", pep.index.max().date())

# ---------- 1. 多窗口收益对比 ----------
windows = {
    "1M": 21, "3M": 63, "6M": 126, "YTD": None, "1Y": 252, "2Y": 504, "3Y": 756, "5Y": 1260
}
rows = []
for name, n in windows.items():
    if name == "YTD":
        start = pd.Timestamp(f"{end.year}-01-01")
        ko_ret = ko["adj_close"].loc[start:end].iloc[-1] / ko["adj_close"].loc[start:end].iloc[0] - 1
        pep_ret = pep["adj_close"].loc[start:end].iloc[-1] / pep["adj_close"].loc[start:end].iloc[0] - 1
    else:
        ko_ret = ko["adj_close"].iloc[-1] / ko["adj_close"].iloc[-1 - n] - 1
        pep_ret = pep["adj_close"].iloc[-1] / pep["adj_close"].iloc[-1 - n] - 1
    rows.append((name, ko_ret * 100, pep_ret * 100, (ko_ret - pep_ret) * 100))
print("\n=== 多窗口收益对比 (adj_close, %) ===")
for name, k, p, d in rows:
    print(f"{name:5s} KO {k:+7.2f} | PEP {p:+7.2f} | 差 {d:+7.2f}")

# ---------- 2. 相对强弱比率 (KO/PEP) ----------
df = pd.DataFrame({"KO": ko["adj_close"], "PEP": pep["adj_close"]}).dropna()
ratio = df["KO"] / df["PEP"]
# 找相对强弱低点/高点
print("\n=== 相对强弱比率 KO/PEP（基准 2015-01-01=1 未必直观，用水平值） ===")
print(f"当前比率: {ratio.iloc[-1]:.4f}")
base = ratio.asof("2015-01-05")
r2 = ratio / base
for d in ["2015-01-05", "2016-12-30", "2019-12-31", "2021-12-31", "2023-12-29", "2025-12-31", "2026-08-21"]:
    try:
        print(f"  {d}: {r2.asof(d):.3f}")
    except Exception:
        pass
# 最近 2 年内最低点
recent = ratio.loc["2024-06-30":]
print(f"2024-07 以来比率最低: {recent.min():.4f} @ {recent.idxmin().date()}")
print(f"2024-07 以来比率最高: {recent.max():.4f} @ {recent.idxmax().date()}")

# ---------- 3. KO 相对 PEP 的滚动超额收益（60日） ----------
ko_ret = ko["adj_close"].pct_change()
pep_ret = pep["adj_close"].pct_change()
roll_ko = (1 + ko_ret).rolling(63).apply(np.prod, raw=True) - 1
roll_pep = (1 + pep_ret).rolling(63).apply(np.prod, raw=True) - 1
excess = (roll_ko - roll_pep) * 100
print("\n=== 滚动 3M 超额收益（KO-PEP, %），近 2 年季度采样 ===")
sample = excess.loc["2024-07-01":].resample("QE").last()
for d, v in sample.items():
    print(f"  {d.date()}: {v:+.2f}")

# ---------- 4. 2026 年分月收益 ----------
print("\n=== 2026 年月度收益 (%) ===")
for tk, name in [(ko, "KO"), (pep, "PEP")]:
    m = tk["adj_close"].loc["2026-01-01":].resample("ME").last().pct_change().dropna() * 100
    print(f"  {name}: " + " ".join(f"{d.month:02d}月:{v:+.1f}" for d, v in m.items()))

# ---------- 5. 波动率与回撤 ----------
print("\n=== 波动率 (年化, 近1年) ===")
for tk, name in [(ko, "KO"), (pep, "PEP")]:
    v = tk["adj_close"].pct_change().loc["2025-08-21":].std() * np.sqrt(252) * 100
    print(f"  {name}: {v:.2f}%")
print("\n=== 最大回撤 (近1年) ===")
for tk, name in [(ko, "KO"), (pep, "PEP")]:
    s = tk["adj_close"].loc["2025-08-21":]
    dd = (s / s.cummax() - 1).min() * 100
    print(f"  {name}: {dd:.2f}%")

# ---------- 6. 关键转折点定位 ----------
print("\n=== KO 相对 PEP 由弱转强的拐点定位 ===")
# 用 120 日滚动比率变化找趋势切换
rr = ratio / ratio.shift(63) - 1  # 63日相对动量
# 找最近一次 rr 由负转正的持续区间
recent_rr = rr.loc["2024-01-01":]
# 输出按月滚动相对动量
mrr = recent_rr.resample("ME").last() * 100
for d, v in mrr.items():
    if d >= pd.Timestamp("2025-01-01"):
        print(f"  {d.date()}: KO相对PEP 63日动量 {v:+.2f}%")

# ---------- 7. Beta 与相关性 (近1年) ----------
joined = pd.DataFrame({"KO": ko_ret, "PEP": pep_ret}).dropna().loc["2025-08-21":]
beta = joined["KO"].cov(joined["PEP"]) / joined["PEP"].var()
corr = joined["KO"].corr(joined["PEP"])
print(f"\n近1年 KO~PEP 相关 {corr:.3f}, KO beta-to-PEP {beta:.2f}")

# ---------- 8. 保存 ----------
out = {
    "asof": str(end.date()),
    "windows": [{"window": w, "KO_pct": round(k, 2), "PEP_pct": round(p, 2), "diff_pct": round(d, 2)} for w, k, p, d in rows],
    "ratio_now": round(float(ratio.iloc[-1]), 4),
    "ratio_min_since_2024H2": (str(recent.idxmin().date()), round(float(recent.min()), 4)),
    "ratio_max_since_2024H2": (str(recent.idxmax().date()), round(float(recent.max()), 4)),
}
os.makedirs(r"C:/Users/Administrator/Desktop/stock/results", exist_ok=True)
with open(r"C:/Users/Administrator/Desktop/stock/results/ko_pep_relative.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n已保存 results/ko_pep_relative.json")