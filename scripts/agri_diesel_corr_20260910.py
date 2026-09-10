# -*- coding: utf-8 -*-
"""
农产品 × 柴油（取暖油 HO）相关性研究 —— 多口径分析引擎
2026-09-10

为什么不能只用 60 日滚动相关：
  ① 水平价格×水平价格 = 共同趋势伪相关 -> 必须用日收益
  ② 农业有强季节周期，60 日窗口跨季节边界，把不同相关结构平均掉
  ③ 结构断裂（页岩油/疫情/俄乌）使全期单一数字无意义

输出: results/agri_diesel_corr_20260910.json 及配套 csv
"""
import json, os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP = os.path.join(BASE, "Temp")
RES = os.path.join(BASE, "results")

FILES = {
    "HO": "ho_main_1D.csv",        # 取暖油/ULSD 柴油期货主连
    "CL": "fut_cl_main_1D.csv",    # WTI 原油
    "RB": "fut_rb_main_1D.csv",    # RBOB 汽油
    "ZC": "agri_zc_main_1D.csv",   # 玉米
    "ZS": "agri_zs_main_1D.csv",   # 大豆
    "ZW": "agri_zw_main_1D.csv",   # 小麦
    "ZL": "fut_zl_main_1D.csv",    # 豆油
}
LABEL = {"HO": "柴油(HO)", "CL": "原油(WTI)", "RB": "汽油(RBOB)",
         "ZC": "玉米", "ZS": "大豆", "ZW": "小麦", "ZL": "豆油"}
AGRI = ["ZC", "ZS", "ZW", "ZL"]

SEASON = {1: "冬季(淡季)", 2: "冬季(淡季)", 3: "春季(播种)", 4: "春季(播种)", 5: "春季(播种)",
          6: "夏季(生长)", 7: "夏季(生长)", 8: "夏季(生长)",
          9: "秋季(收获)", 10: "秋季(收获)", 11: "秋季(收获)", 12: "冬季(淡季)"}
SEASON_ORDER = ["春季(播种)", "夏季(生长)", "秋季(收获)", "冬季(淡季)"]

PHASES = [
    ("P1 高油价末期", "2011-09-01", "2014-06-30"),
    ("P2 油价崩塌", "2014-07-01", "2016-12-31"),
    ("P3 低波动期", "2017-01-01", "2019-12-31"),
    ("P4 疫情冲击", "2020-01-01", "2020-12-31"),
    ("P5 通胀+俄乌双危机", "2021-01-01", "2022-12-31"),
    ("P6 后危机期", "2023-01-01", "2026-12-31"),
]


def load(fn):
    df = pd.read_csv(os.path.join(TEMP, fn))
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"]).set_index("date").sort_index()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df["close"]


def pair_stats(x, y):
    """对齐后返回 pearson/spearman/p/n"""
    idx = x.dropna().index.intersection(y.dropna().index)
    a, b = x.loc[idx].values, y.loc[idx].values
    if len(a) < 20:
        return None
    r, p = stats.pearsonr(a, b)
    rs, ps = stats.spearmanr(a, b)
    return {"r": round(float(r), 4), "p": float(p), "n": int(len(a)),
            "spearman": round(float(rs), 4), "sp_p": float(ps)}


def sig_tag(p):
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


# ---------------- 数据准备 ----------------
close = pd.DataFrame({k: load(v) for k, v in FILES.items()})
ret = np.log(close).diff() * 100

common = close.dropna().index                      # 全品种交集（小麦定调，2017-11起）
print(f"全品种交集: {common[0].date()} ~ {common[-1].date()}  n={len(common)}")

# 主分析窗口：柴油 × 玉米/大豆/豆油（长窗口），小麦单独
main_idx = close[["HO", "CL", "RB", "ZC", "ZS", "ZL"]].dropna().index
print(f"主窗口(HO+3农产+油品): {main_idx[0].date()} ~ {main_idx[-1].date()}  n={len(main_idx)}")

out = {"meta": {
    "generated": "2026-09-10",
    "main_window": [str(main_idx[0].date()), str(main_idx[-1].date()), len(main_idx)],
    "wheat_window": [str(common[0].date()), str(common[-1].date()), len(common)],
    "units": "log-return x100 (%), Pearson on daily returns unless noted",
    "label": LABEL,
}}

# ---------------- 模块 A：水平 vs 收益（伪相关证明） ----------------
A = {"level": {}, "return": {}}
for a in AGRI + ["CL", "RB"]:
    lvl = pair_stats(close.loc[main_idx, "HO"], close.loc[main_idx, a])
    rtn = pair_stats(ret.loc[main_idx, "HO"], ret.loc[main_idx, a])
    A["level"][a] = lvl
    A["return"][a] = rtn
    print(f"A {a:3s} 水平 r={lvl['r']:+.3f} -> 收益 r={rtn['r']:+.3f} ({sig_tag(rtn['p'])})")
out["A_level_vs_return"] = A

# ---------------- 模块 B：60 日滚动相关（用户旧口径） ----------------
roll = {}
for a in AGRI:
    s = ret.loc[main_idx, ["HO", a]].dropna()
    r60 = s["HO"].rolling(60).corr(s[a])
    roll[a] = r60
    v = r60.dropna()
    out.setdefault("B_roll60", {})[a] = {
        "mean": round(float(v.mean()), 4), "median": round(float(v.median()), 4),
        "std": round(float(v.std()), 4), "min": round(float(v.min()), 4),
        "max": round(float(v.max()), 4),
        "share_positive": round(float((v > 0).mean()), 4),
        "share_sig_like": round(float((v.abs() > 0.3).mean()), 4),
    }
    print(f"B {a:3s} 60d滚动 均值={v.mean():+.3f} 区间[{v.min():+.2f},{v.max():+.2f}] 正值占比={(v>0).mean():.0%}")

roll_df = pd.DataFrame(roll)
roll_df = roll_df.resample("W-FRI").last().round(4)   # 抽稀到周，供绘图
roll_df.index = roll_df.index.strftime("%Y-%m-%d")
roll_df.to_csv(os.path.join(RES, "agri_diesel_roll60.csv"), encoding="utf-8")

# ---------------- 模块 C：窗口敏感性 ----------------
WINDOWS = [20, 30, 60, 120, 250]
C = {}
for a in AGRI:
    s = ret.loc[main_idx, ["HO", a]].dropna()
    row = {}
    for w in WINDOWS:
        v = s["HO"].rolling(w).corr(s[a]).dropna()
        row[w] = {"mean": round(float(v.mean()), 4), "median": round(float(v.median()), 4),
                  "std": round(float(v.std()), 4),
                  "share_positive": round(float((v > 0).mean()), 4)}
    C[a] = row
    print(f"C {a:3s} 窗口σ: " + " ".join(f"{w}d={row[w]['std']:.2f}" for w in WINDOWS))
out["C_window_sensitivity"] = C

# ---------------- 模块 D：季节性 ----------------
D = {"by_month": {}, "by_season": {}, "deseasonalized": {}, "season_of_window": {}}

# D1 按日历月分组（日收益相关）
for a in AGRI:
    s = ret.loc[main_idx, ["HO", a]].dropna()
    bym = {}
    for m in range(1, 13):
        sub = s[s.index.month == m]
        st = pair_stats(sub["HO"], sub[a])
        if st:
            bym[m] = st
    D["by_month"][a] = bym

# D2 按农事季节
for a in AGRI:
    s = ret.loc[main_idx, ["HO", a]].dropna()
    sd = {}
    for sz in SEASON_ORDER:
        months = [k for k, v in SEASON.items() if v == sz]
        sub = s[s.index.month.isin(months)]
        st = pair_stats(sub["HO"], sub[a])
        if st:
            sd[sz] = st
    D["by_season"][a] = sd
    txt = " | ".join(f"{k}:{v['r']:+.3f}{sig_tag(v['p'])}" for k, v in sd.items())
    print(f"D {a:3s} 分季节(原始): {txt}")

# D3 季节性剥离：日收益 - 各月均值
ret_ds = ret.copy()
for c in ret_ds.columns:
    mm = ret_ds[c].groupby(ret_ds.index.month).transform("mean")
    ret_ds[c] = ret_ds[c] - mm
for a in AGRI:
    st_raw = pair_stats(ret.loc[main_idx, "HO"], ret.loc[main_idx, a])
    st_ds = pair_stats(ret_ds.loc[main_idx, "HO"], ret_ds.loc[main_idx, a])
    D["deseasonalized"][a] = {"raw": st_raw, "deseason": st_ds,
                              "delta": round(st_ds["r"] - st_raw["r"], 4)}
    print(f"D {a:3s} 季节性剥离: {st_raw['r']:+.3f} -> {st_ds['r']:+.3f} (Δ{st_ds['r']-st_raw['r']:+.3f})")

# D4 60日滚动窗口所处季节的调制：按窗口结束月份归类，比较各季节窗口的滚动相关均值
for a in AGRI:
    r60 = roll[a].dropna()
    ses = pd.Series([SEASON[m] for m in r60.index.month], index=r60.index)
    g = r60.groupby(ses).mean()
    D["season_of_window"][a] = {k: round(float(g.get(k, np.nan)), 4) for k in SEASON_ORDER}
    print(f"D {a:3s} 60d滚动按窗口季节均值: " + " ".join(f"{k[:2]}={g.get(k,float('nan')):+.2f}" for k in SEASON_ORDER))
out["D_seasonality"] = D

# ---------------- 模块 E：分阶段 ----------------
E = {}
for a in AGRI:
    E[a] = {}
    for name, s0, s1 in PHASES:
        idx = main_idx[(main_idx >= s0) & (main_idx <= s1)]
        if len(idx) < 60:
            continue
        st_r = pair_stats(ret.loc[idx, "HO"], ret.loc[idx, a])
        st_l = pair_stats(close.loc[idx, "HO"], close.loc[idx, a])
        if st_r:
            E[a][name] = {"ret_r": st_r["r"], "ret_p": st_r["p"], "n": st_r["n"],
                          "level_r": st_l["r"] if st_l else None, "spearman": st_r["spearman"]}
    txt = " | ".join(f"{k.split()[0]}:{v['ret_r']:+.3f}{sig_tag(v['ret_p'])}" for k, v in E[a].items())
    print(f"E {a:3s} 分阶段: {txt}")
out["E_phases"] = E

# ---------------- 模块 F：领先-滞后 ----------------
F = {}
for a in AGRI:
    s = ret.loc[main_idx, ["HO", a]].dropna()
    row = {}
    for lag in range(-10, 11):
        r = s["HO"].corr(s[a].shift(lag))
        row[lag] = round(float(r), 4)
    F[a] = row
    best = max(row, key=lambda k: abs(row[k]))
    print(f"F {a:3s} 最大|r| lag={best} r={row[best]:+.3f}  (lag>0 = 柴油领先)")
out["F_lead_lag"] = F

# ---------------- 模块 G：机制通道 ----------------
G = {}
pairs = [("HO", "CL", "柴油×原油(能源成本通道)"),
         ("ZL", "HO", "豆油×柴油(生物柴油通道)"),
         ("ZC", "RB", "玉米×汽油(乙醇通道)"),
         ("ZS", "HO", "大豆×柴油"),
         ("ZW", "HO", "小麦×柴油")]

# 裂解价差：柴油 - 原油（美元/加仑口径换算：CL 美元/桶 ÷42）
crack = close["HO"] - close["CL"] / 42.0
crack_ret = np.log(crack).diff() * 100
for x, y, desc in pairs:
    idx = close[[x, y]].dropna().index if y != "HO" or x != "ZL" else main_idx
    idx = ret[[x, y]].dropna().index.intersection(main_idx)
    st = pair_stats(ret.loc[idx, x], ret.loc[idx, y])
    st_lvl = pair_stats(close.loc[idx, x], close.loc[idx, y])
    G[f"{x}-{y}"] = {"desc": desc, "ret_r": st["r"], "p": st["p"], "n": st["n"],
                     "level_r": st_lvl["r"] if st_lvl else None,
                     "spearman": st["spearman"]}
    print(f"G {x}-{y}: 描述={desc} 收益r={st['r']:+.3f}{sig_tag(st['p'])} 水平r={st_lvl['r']:+.3f}")

# 农产品 vs 裂解价差
G["crack"] = {}
for a in AGRI:
    idx = crack_ret.dropna().index.intersection(ret[a].dropna().index).intersection(main_idx)
    st = pair_stats(crack_ret.loc[idx], ret.loc[idx, a])
    st_lvl = pair_stats(crack.loc[idx], close.loc[idx, a])
    G["crack"][a] = {"ret_r": st["r"], "p": st["p"], "n": st["n"],
                     "level_r": st_lvl["r"] if st_lvl else None}
    print(f"G crack×{a}: 收益r={st['r']:+.3f}{sig_tag(st['p'])}")
out["G_channels"] = G

# ---------------- 模块 H：绘图数据 ----------------
# 归一化价格曲线（月度，供总览图）
norm = close.loc[main_idx].resample("ME").last()
norm = norm / norm.iloc[0] * 100
norm.index = norm.index.strftime("%Y-%m")
plot_prices = {"dates": list(norm.index), **{k: [None if pd.isna(v) else round(float(v), 2) for v in norm[k]] for k in norm.columns}}
out["plot_prices"] = plot_prices

# 同比变化（12M）相关散点数据
yoy = (close.pct_change(252) * 100).loc[main_idx]
yoy_m = yoy.resample("ME").last().dropna(how="all")
yoy_m.index = yoy_m.index.strftime("%Y-%m")
out["plot_yoy"] = {"dates": list(yoy_m.index),
                   **{k: [None if pd.isna(v) else round(float(v), 2) for v in yoy_m[k]] for k in yoy_m.columns}}

with open(os.path.join(RES, "agri_diesel_corr_20260910.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nDONE -> results/agri_diesel_corr_20260910.json")
