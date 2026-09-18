# -*- coding: utf-8 -*-
"""
ENSO 与欧洲夏季高温的关系定量检验
==================================
核心问题：2026 年欧洲创纪录酷暑，与厄尔尼诺有多大关系？

方法：
 A. 用本地 ONI（1950-2026）做事件研究：El Nino / La Nina 年 -> 各参数 X 的冬季 D(-1)JF 值
 B. 用 NOAA PSL 拉取长序列（1948/1949 起）扩展样本：
      - n34_anom  : Nino3.4 月异常 (ERSSTv5? v4)  1948-
      - dmi       : Indian Ocean Dipole (DMI)     1948-  (欧洲夏季的另一候选驱动)
      - n34_ersst : nina34 绝对SST (用于交叉验证)
 C. 计算相关性矩阵 + 事件条件均值 + 块自助法(block bootstrap)检验
 D. 用 NOAAGlobalTemp 半球/全球陆地气温 做"全球背景 vs 欧洲 vs ENSO"的方差贡献拆解

输出：results/enso_europe_summer.json + results/enso_europe_summer_corr.csv
"""
import json, os, math, urllib.request, itertools
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)
CACHE = os.path.join(ROOT, "data", "enso")
os.makedirs(CACHE, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (research)"}


def fetch(url, fname, force=False):
    path = os.path.join(CACHE, fname)
    if os.path.exists(path) and not force:
        return open(path, "r", encoding="utf-8", errors="ignore").read()
    try:
        req = urllib.request.Request(url, headers=UA)
        t = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="ignore")
        open(path, "w", encoding="utf-8").write(t)
        return t
    except Exception as e:
        print(f"  [WARN] fetch failed {url}: {e}")
        return None


def parse_psl_wide(text):
    """PSL 格式：首行 '1948 2026'，随后 'YYYY v1..v12'，末行 -9999 或 footer"""
    out = {}
    if not text:
        return out
    for line in text.split("\n"):
        p = line.split()
        if len(p) >= 13 and p[0].isdigit() and len(p[0]) == 4:
            y = int(p[0])
            vals = []
            for v in p[1:13]:
                try:
                    f = float(v)
                except Exception:
                    f = np.nan
                if f <= -90:
                    f = np.nan   # -99.99 / -9999 缺测
                vals.append(f)
            if len(vals) == 12:
                out[y] = vals
    return out


def to_series(d):
    """dict{year: [12]} -> pd.Series(monthly), index=PeriodIndex(M)"""
    rows = []
    for y, vs in d.items():
        for m, v in enumerate(vs, 1):
            rows.append((pd.Period(f"{y}-{m:02d}", freq="M"), v))
    s = pd.Series({k: v for k, v in rows}).sort_index()
    return s.dropna()


def monthly_to_season(s, start_month, n=3):
    """滚动 n 月平均，标签为最后一个月的 Period"""
    r = s.rolling(n).mean()
    return r


# ------------------------------------------------------------------
print("[1] 加载本地 ONI (CPC, 1950-)")
oni_txt = open(os.path.join(ROOT, "data", "cotton", "raw", "oni_latest.txt"),
               encoding="utf-8", errors="ignore").read()
oni_rows = []
for line in oni_txt.split("\n"):
    p = line.split()
    if len(p) == 4 and len(p[0]) == 3:
        try:
            oni_rows.append((p[0], int(p[1]), float(p[3])))
        except Exception:
            pass
elif_raw = []
for line in oni_txt.split("\n"):
    p = line.split()
    if len(p) == 4 and len(p[0]) == 3:
        try:
            elif_raw.append((p[0], int(p[1]), float(p[2])))
        except Exception:
            pass
print(f"    ONI 3-month windows parsed: {len(oni_rows)}, 绝对SST: {len(elif_raw)}")

# ------------------------------------------------------------------
print("[2] 拉取 NOAA PSL 长序列")
raw = {}
raw["n34_anom"] = fetch("https://psl.noaa.gov/data/correlation/nina34.anom.data", "nina34.anom.data")
raw["n34_sst"] = fetch("https://psl.noaa.gov/data/correlation/nina34.data", "nina34.data")
raw["n3_anom"] = fetch("https://psl.noaa.gov/data/correlation/nina3.anom.data", "nina3.anom.data")
raw["n4_anom"] = fetch("https://psl.noaa.gov/data/correlation/nina4.anom.data", "nina4.anom.data")
raw["dmi"] = fetch("https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data", "dmi_had.long.data")
raw["n34_olr"] = fetch("https://psl.noaa.gov/data/correlation/olr.data", "olr.data")

D = {k: parse_psl_wide(v) for k, v in raw.items()}
for k, v in D.items():
    ys = sorted(v.keys())
    print(f"    {k}: {len(v)} years, {ys[0] if ys else '-'} ~ {ys[-1] if ys else '-'}")

S = {k: to_series(v) for k, v in D.items() if v}
for k, s in S.items():
    print(f"      {k}: {len(s)} months, {s.index[0]} ~ {s.index[-1]}")

# ------------------------------------------------------------------
print("[3] 构造年度指标")
# Nino3.4 DJF 平均（以 1 月为标签的冬季，即 1 月所属年份）
n34a = S.get("n34_anom")
dmi = S.get("dmi")

df = pd.DataFrame({"n34": n34a})
if dmi is not None:
    df["dmi"] = dmi
df["ym"] = df.index
df["year"] = [p.year for p in df.index]
df["month"] = [p.month for p in df.index]

def winter_mean(col, lag_year=1):
    """冬季 D(-1)JF 平均：以 1 月年份标记。lag_year=0 表示 JFM 用同年 1-3 月"""
    pass

# DJF：上年12月 + 当年1月 + 当年2月
recs = []
for y in sorted(df.year.unique()):
    def get(yy, mm):
        try:
            return float(df[(df.year == yy) & (df.month == mm)][col_name].iloc[0])
        except Exception:
            return np.nan
    recs.append(y)

def seasonal(col_name, months_offsets):
    """months_offsets: list of (year_offset, month)"""
    out = {}
    for y in sorted(df.year.unique()):
        vals = []
        for yo, m in months_offsets:
            sub = df[(df.year == y + yo) & (df.month == m)]
            if len(sub):
                v = sub[col_name].iloc[0]
                if pd.notna(v):
                    vals.append(v)
        if len(vals) == len(months_offsets):
            out[y] = float(np.mean(vals))
    return pd.Series(out).sort_index()

seasons = {
    "DJF": [(-1, 12), (0, 1), (0, 2)],       # 冬季，标年 y = 1月的年
    "JFM": [(0, 1), (0, 2), (0, 3)],
    "MAM": [(0, 3), (0, 4), (0, 5)],
    "AMJ": [(0, 4), (0, 5), (0, 6)],
    "MJJ": [(0, 5), (0, 6), (0, 7)],
    "JJA": [(0, 6), (0, 7), (0, 8)],
    "JAS": [(0, 7), (0, 8), (0, 9)],
    "SON": [(0, 9), (0, 10), (0, 11)],
    "OND": [(0, 10), (0, 11), (0, 12)],
}
ann = pd.DataFrame({k: seasonal("n34", v) for k, v in seasons.items()})
ann["dmi_SON"] = seasonal("dmi", seasons["SON"]) if dmi is not None else np.nan
ann["dmi_JJA"] = seasonal("dmi", seasons["JJA"]) if dmi is not None else np.nan
ann["dmi_DJF"] = seasonal("dmi", seasons["DJF"]) if dmi is not None else np.nan
ann = ann.dropna(subset=["JJA"])
print(f"    年度(季)表: {ann.index.min()} ~ {ann.index.max()}  n={len(ann)}")

# ------------------------------------------------------------------
print("[4] 同步拉取 HadCRUT5 区域气温 (CRU/UK Met Office)")
# CRU 文本格式：year, 12*月度值, 年度值  /  下一行: year, 12*覆盖百分比
CRU = {
    "gl": "https://crudata.uea.ac.uk/cru/data/temperature/HadCRUT5.1Analysis_gl.txt",
    "nh": "https://crudata.uea.ac.uk/cru/data/temperature/HadCRUT5.1Analysis_nh.txt",
    "sh": "https://crudata.uea.ac.uk/cru/data/temperature/HadCRUT5.1Analysis_sh.txt",
    "nh_land": "https://crudata.uea.ac.uk/cru/data/temperature/CRUTEM5.1_nh.txt",
    "gl_land": "https://crudata.uea.ac.uk/cru/data/temperature/CRUTEM5.1_gl.txt",
}
temp_raw = {k: fetch(u, f"cru_{k}.txt") for k, u in CRU.items()}

def parse_cru(text):
    """CRU 文本格式：数据行(i5,12f7.3,+年值) 与 覆盖率行(i5,12i7,+年值) 交替。
    -> {year: [12 monthly anomalies]}，覆盖率为 0 的月份标 NaN"""
    d = {}
    if not text:
        return d
    lines = [l for l in text.split("\n") if l.strip()]
    i = 0
    while i < len(lines):
        p = lines[i].split()
        if len(p) >= 13 and p[0].isdigit() and len(p[0]) == 4:
            y = int(p[0])
            try:
                vals = [float(v) for v in p[1:13]]
            except Exception:
                i += 1
                continue
            # 下一行若为同年的覆盖率行 -> 把覆盖率为 0 的月份标 NaN
            if i + 1 < len(lines):
                q = lines[i + 1].split()
                if len(q) >= 13 and q[0] == p[0] and q[1] != "-9.999":
                    try:
                        cov = [int(float(x)) for x in q[1:13]]
                        for j in range(12):
                            if cov[j] == 0:
                                vals[j] = np.nan
                        i += 1  # 跳过覆盖率行
                    except Exception:
                        pass
            # -9.999 / -9999 为缺测
            d[y] = [np.nan if v <= -9 else v for v in vals]
        i += 1
    return d

Ts = {k: parse_cru(v) for k, v in temp_raw.items()}
for k, v in Ts.items():
    ys = sorted(v.keys())
    if not ys:
        print(f"    [{k}] EMPTY")
        continue
    last = ys[-1]
    valid = [m for m in v[last] if np.isfinite(m)]
    print(f"    CRU[{k}]: {len(v)}y {ys[0]}~{last}  {last} 有效月={len(valid)} 末月值="
          f"{[round(x,3) for x in v[last] if np.isfinite(x)]}")

# 转成 monthly Series 便于取任意季节
S_CRU = {}
for k, d in Ts.items():
    rows = []
    for y, vs in d.items():
        for m, v in enumerate(vs, 1):
            if np.isfinite(v):
                rows.append((pd.Period(f"{y}-{m:02d}", freq="M"), v))
    if rows:
        S_CRU[k] = pd.Series(dict(rows)).sort_index()
        print(f"      S_CRU[{k}]: {len(S_CRU[k])} months {S_CRU[k].index[0]}~{S_CRU[k].index[-1]}")

# ------------------------------------------------------------------
print("[5] 相关性 & 事件研究")
import math

def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 8:
        return np.nan, np.nan, len(x)
    r = float(np.corrcoef(x, y)[0, 1])
    n = len(x)
    t = r * math.sqrt((n - 2) / max(1e-12, 1 - r ** 2))
    from scipy import stats as st
    p = float(2 * (1 - st.t.cdf(abs(t), n - 2)))
    return r, p, n

def block_boot_p(x, y, block=5, nsim=4000, seed=42):
    """块自助法：检验 r 的显著性（处理序列自相关）"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    if n < 20:
        return np.nan
    rng = np.random.default_rng(seed)
    obs = np.corrcoef(x, y)[0, 1]
    nb = int(np.ceil(n / block))
    cnt = 0
    for _ in range(nsim):
        starts = rng.integers(0, n, nb)
        idx = np.concatenate([np.arange(s, s + block) % n for s in starts])[:n]
        xr, yr = x[idx], y[idx]
        if np.std(xr) < 1e-9 or np.std(yr) < 1e-9:
            continue
        rr = np.corrcoef(xr, yr)[0, 1]
        if abs(rr) >= abs(obs):
            cnt += 1
    return (cnt + 1) / (nsim + 1)

# ---- 5.1 把 CRU 气温转成季节序列，并入 ann ----
res = {"meta": {}, "corr": [], "events": {}, "regions": {}, "leadlag": []}
results_corr = []

def seasons_from_series(s):
    """monthly Series -> {season: {year: value}}；季节标签为该季节最后一个月的年"""
    out = {}
    dfx = pd.DataFrame({"v": s})
    dfx["year"] = [p.year for p in dfx.index]
    dfx["month"] = [p.month for p in dfx.index]
    for name, offs in seasons.items():
        d = {}
        for y in sorted(dfx.year.unique()):
            vals = []
            for yo, m in offs:
                sub = dfx[(dfx.year == y + yo) & (dfx.month == m)]
                if len(sub) and pd.notna(sub["v"].iloc[0]):
                    vals.append(float(sub["v"].iloc[0]))
            if len(vals) == len(offs):
                d[y] = float(np.mean(vals))
        out[name] = pd.Series(d).sort_index()
    return out

# 区域定义：NH 夏季 = JJA；欧洲维度在 HadCRUT NH 之外，另用 NH 陆地(CRUTEM)作对照
REG = {}
for key in ["gl", "nh", "sh", "nh_land", "gl_land"]:
    if key in S_CRU:
        REG[key] = seasons_from_series(S_CRU[key])

for key, sd in REG.items():
    for sname, ser in sd.items():
        ann[f"T_{key}_{sname}"] = [ser.get(y, np.nan) for y in ann.index]

# 欧洲夏季 = NH 夏季气温（重灾季） + NH 陆地（大陆性更强）
TARGET_EU = ["T_nh_JJA", "T_nh_land_JJA", "T_gl_JJA"]
TARGET_EU_ANN = ["T_nh_JJA", "T_nh_land_JJA"]

print("\n[5.1] ENSO 季节 -> 后续 NH 夏季气温")
print(f"    可用目标列: {[c for c in ann.columns if c.startswith('T_')]}")

# ============================================================
# A. 同步检验（同一日历年的 ENSO 季节 vs 北半球夏季气温）
#    + 去趋势 / 一阶差分 三口径对照（核心：剔除共同增温趋势）
# ============================================================
print("\n[A] 同期相关：ENSO 季节 vs 北半球夏季气温（三口径对照）")
det = []


def detrend(s):
    s = pd.Series(s).astype(float)
    m = s.notna()
    if m.sum() < 10:
        return s
    x = np.arange(len(s))
    coef = np.polyfit(x[m], s[m], 1)
    return pd.Series(s.values - np.polyval(coef, x), index=s.index)


TGT = {"NH_land_JJA": "T_nh_land_JJA", "NH_JJA": "T_nh_JJA", "GLB_JJA": "T_gl_JJA"}
PRED = {"ENSO_DJF(y-1)": ("DJF", -1), "ENSO_MAM": ("MAM", 0), "ENSO_AMJ": ("AMJ", 0),
        "ENSO_MJJ": ("MJJ", 0), "ENSO_JJA": ("JJA", 0), "ENSO_SON(y-1)": ("SON", -1),
        "ENSO_OND(y-1)": ("OND", -1)}

for pname, (pcol, poff) in PRED.items():
    if pcol not in ann.columns:
        continue
    for tname, tcol in TGT.items():
        if tcol not in ann.columns:
            continue
        x = pd.Series([ann[pcol].get(i + poff, np.nan) for i in ann.index], index=ann.index)
        y = ann[tcol]
        r0, p0, n0 = pearson(x, y)
        r1, p1, _ = pearson(detrend(x), detrend(y))
        r2, p2, _ = pearson(x.diff(), y.diff())
        det.append({"pred": pname, "target": tname,
                    "r_raw": r0, "p_raw": p0,
                    "r_detrend": r1, "p_detrend": p1,
                    "r_diff": r2, "p_diff": p2,
                    "n": n0, "bb_block": block_boot_p(x, y)})

dd = pd.DataFrame(det)
print(dd.round(3).to_string(index=False))

# 关键提炼
print("\n  >>> 关键提炼（r_raw -> r_detrend）")
for tname in TGT:
    sub = dd[dd.target == tname].copy()
    hr = sub.loc[sub.r_raw.abs().idxmax()]
    print(f"    {tname}: 最强原始 r={hr.r_raw:+.3f} ({hr.pred}, p={hr.p_raw:.4f}) "
          f"-> 去趋势后 r={hr.r_detrend:+.3f} (p={hr.p_detrend:.3f}) "
          f"| 差分后 r={hr.r_diff:+.3f} (p={hr.p_diff:.3f})")

# ============================================================
# B. 提前量检验：ENSO 冬季(y) -> 次年 NH 夏季(y+1)
# ============================================================
print("\n[B] 提前量：ENSO 年 y 的冬季 -> 年 y+1 的北半球夏季")
lead = []
for lag in [1, 2]:
    for pcol in ["DJF", "JFM", "MAM", "AMJ"]:
        if pcol not in ann.columns:
            continue
        for tname, tcol in TGT.items():
            y = pd.Series([ann[tcol].get(i + lag, np.nan) for i in ann.index], index=ann.index)
            r, p, n = pearson(ann[pcol], y)
            bb = block_boot_p(ann[pcol], y)
            rd, pd_, _ = pearson(detrend(ann[pcol]), detrend(y))
            lead.append({"ensn": pcol + "(y)", "target": tname + f"(y+{lag})", "lag": lag,
                         "r_raw": r, "p_raw": p, "r_detrend": rd, "p_detrend": pd_,
                         "bb": bb, "n": n})
ld = pd.DataFrame(lead)
print(ld.round(3).to_string(index=False))

# ============================================================
# C. 方差分解：ENSO 能解释多少 vs 背景增温能解释多少
# ============================================================
print("\n[C] 方差分解：NH 陆地夏季气温的解释力归因")
var_expl = {}
dx = np.arange(len(ann))
for tname, tcol in TGT.items():
    y = ann[tcol].astype(float)
    m = y.notna()
    if m.sum() < 30:
        continue
    # (1) 仅时间趋势
    c1 = np.polyfit(dx[m], y[m], 1)
    fit1 = np.polyval(c1, dx[m])
    r2_trend = 1 - ((y[m] - fit1) ** 2).sum() / ((y[m] - y[m].mean()) ** 2).sum()
    # (2) 仅 ENSO MJJ
    x_e = ann["MJJ"].astype(float)
    mm = m & x_e.notna()
    r2_enso = np.corrcoef(x_e[mm], y[mm])[0, 1] ** 2
    # (3) 趋势 + ENSO 双变量
    X = np.column_stack([np.ones(mm.sum()), dx[mm], x_e[mm]])
    beta, *_ = np.linalg.lstsq(X, y[mm], rcond=None)
    fit3 = X @ beta
    r2_both = 1 - ((y[mm] - fit3) ** 2).sum() / ((y[mm] - y[mm].mean()) ** 2).sum()
    # (4) 双变量下 ENSO 的偏 t
    resid = y[mm] - X[:, [0, 1]] @ np.linalg.lstsq(X[:, [0, 1]], y[mm], rcond=None)[0]
    xe_res = x_e[mm] - X[:, [0, 1]] @ np.linalg.lstsq(X[:, [0, 1]], x_e[mm], rcond=None)[0]
    from scipy import stats as st
    r_partial = np.corrcoef(xe_res, resid)[0, 1]
    k = mm.sum() - 3
    t_part = r_partial * np.sqrt(k / max(1e-12, 1 - r_partial ** 2))
    p_part = 2 * (1 - st.t.cdf(abs(t_part), k))
    var_expl[tname] = {"r2_trend_only": round(float(r2_trend), 3),
                       "r2_enso_only": round(float(r2_enso), 3),
                       "r2_trend_plus_enso": round(float(r2_both), 3),
                       "r2_incremental_enso": round(float(r2_both - r2_trend), 4),
                       "partial_r_enso": round(float(r_partial), 3),
                       "partial_p_enso": round(float(p_part), 4),
                       "beta_trend_per_decade": round(float(beta[1] * 10), 3),
                       "beta_enso": round(float(beta[2]), 3),
                       "n": int(mm.sum())}
    print(f"    {tname}: 纯趋势 R²={r2_trend:.3f} | ENSO单独 R²={r2_enso:.3f} | "
          f"趋势+ENSO R²={r2_both:.3f} => ENSO 增量 R²={r2_both-r2_trend:+.4f} "
          f"(偏 r={r_partial:+.3f}, p={p_part:.3f})")

# ============================================================
# D. 事件研究
# ============================================================
print("\n[D] 事件研究：按 DJF El Nino 强度分组 -> 同期/次年 NH 陆地夏季气温")
ev = ann.copy()


def tier(v):
    if pd.isna(v):
        return None
    if v >= 1.5:
        return "1_strong_EL"
    if v >= 0.5:
        return "2_weak_EL"
    if v <= -1.5:
        return "4_strong_LA"
    if v <= -0.5:
        return "5_weak_LA"
    return "3_neutral"


ev["tier_DJF"] = ev["DJF"].apply(tier)
ev["tier_MJJ"] = ev["MJJ"].apply(tier)
for tcol in ["T_nh_land_JJA", "T_nh_JJA"]:
    ev[tcol + "_next"] = [ann[tcol].get(i + 1, np.nan) for i in ann.index]

events_out = {}
for tcol in ["tier_DJF", "tier_MJJ"]:
    for tgt in ["T_nh_land_JJA", "T_nh_JJA", "T_gl_JJA", "T_nh_land_JJA_next"]:
        gg = ev.groupby(tcol)[tgt].agg(["count", "mean", "median", "std"]).round(3)
        events_out[tcol + "->" + tgt] = gg.to_dict(orient="index")
        print(f"\n  [{tcol} -> {tgt}]")
        print(gg.to_string())

from scipy import stats as st
cmp_out = {}
for tgt in ["T_nh_land_JJA", "T_nh_JJA", "T_gl_JJA"]:
    a = ev.loc[ev["tier_DJF"] == "1_strong_EL", tgt].dropna()
    b = ev.loc[ev["tier_DJF"] == "3_neutral", tgt].dropna()
    c = ev.loc[ev["tier_DJF"] == "4_strong_LA", tgt].dropna()
    if len(a) > 2 and len(b) > 2:
        t, p = st.ttest_ind(a, b, equal_var=False)
        cmp_out["strongEL_vs_neutral_" + tgt] = {
            "n_EL": int(len(a)), "mean_EL": round(float(a.mean()), 3),
            "n_neutral": int(len(b)), "mean_neutral": round(float(b.mean()), 3),
            "diff": round(float(a.mean() - b.mean()), 3),
            "t": round(float(t), 3), "p": round(float(p), 4)}
        print(f"\n  t-test {tgt}: strongEL={a.mean():.3f}(n={len(a)}) vs neutral={b.mean():.3f}"
              f"(n={len(b)}) diff={a.mean()-b.mean():+.3f} t={t:.2f} p={p:.4f}")
    if len(c) > 2 and len(b) > 2:
        t, p = st.ttest_ind(c, b, equal_var=False)
        cmp_out["strongLA_vs_neutral_" + tgt] = {
            "n_LA": int(len(c)), "mean_LA": round(float(c.mean()), 3),
            "n_neutral": int(len(b)), "mean_neutral": round(float(b.mean()), 3),
            "diff": round(float(c.mean() - b.mean()), 3),
            "t": round(float(t), 3), "p": round(float(p), 4)}
        print(f"  t-test {tgt}: strongLA={c.mean():.3f}(n={len(c)}) vs neutral={b.mean():.3f}"
              f" diff={c.mean()-b.mean():+.3f} t={t:.2f} p={p:.4f}")

# ============================================================
# E. 强 EN 年清单 + 近年对照
# ============================================================
print("\n[E] 强 El Nino 年（DJF ONI >= 1.5）")
strong = ev[ev["DJF"] >= 1.5][["DJF", "T_nh_land_JJA", "T_nh_land_JJA_next",
                               "T_nh_JJA", "T_gl_JJA"]].round(3)
print(strong.to_string())
res["strong_EL_years"] = strong.to_dict(orient="index")

mid = ev[(ev["DJF"] > 0.9) & (ev["DJF"] < 1.5)]
res["moderate_EL_years"] = mid[["DJF", "T_nh_land_JJA", "T_nh_JJA"]].round(3).to_dict(orient="index")

print("\n  近年对照（2015-2026）：")
rec = ev.loc[[y for y in range(2015, 2027) if y in ev.index],
             ["DJF", "MAM", "AMJ", "MJJ", "T_nh_land_JJA", "T_nh_JJA", "T_gl_JJA"]].round(3)
print(rec.to_string())
res["recent"] = rec.to_dict(orient="index")

# ============================================================
# F. 2026 现状分位
# ============================================================
res["meta"] = {
    "sample": str(ann.index.min()) + "-" + str(ann.index.max()),
    "n": int(len(ann)),
    "latest_year": int(ann.index.max()),
    "note": "ONI/n34 来自 NOAA PSL 与 CPC 本地文件；气温来自 HadCRUT5/CRUTEM5 "
            "(CRU + UK Met Office v5.1, 更新至 2026-07)",
}
pct = {}
for c in ["DJF", "MAM", "AMJ", "MJJ", "JJA", "SON", "OND"]:
    if c in ann.columns and pd.notna(ann.loc[2026, c]):
        pct[c] = {"value": round(float(ann.loc[2026, c]), 3),
                  "pctile": float(round((ann[c] < ann.loc[2026, c]).mean() * 100, 1)),
                  "n": int(ann[c].notna().sum())}
res["meta"]["enso_2026"] = pct

t26 = {}
for c in ["T_nh_land_MJJ", "T_nh_land_JJA", "T_nh_JJA", "T_gl_JJA"]:
    if c in ann.columns and pd.notna(ann.loc[2026, c]):
        t26[c] = {"value": round(float(ann.loc[2026, c]), 3),
                  "pctile": float(round((ann[c] < ann.loc[2026, c]).mean() * 100, 1)),
                  "mean_1991_2020": round(float(ann.loc[1991:2020, c].mean()), 3),
                  "anom_vs_9120": round(float(ann.loc[2026, c] - ann.loc[1991:2020, c].mean()), 3),
                  "rank_desc": int((ann[c] > ann.loc[2026, c]).sum() + 1),
                  "n": int(ann[c].notna().sum())}
res["meta"]["temp_2026"] = t26
print("\n[F] 2026 现状:")
print(json.dumps(res["meta"]["enso_2026"], ensure_ascii=False, indent=1))
print(json.dumps(t26, ensure_ascii=False, indent=1))

# ============================================================
# G. 2026 情景反事实：若 ENSO 贡献取上界，能解释多少？
# ============================================================
print("\n[G] 反事实：用历史强 EN 条件均值差反推 2026（用 MJJ，因 8 月未更新）")
cf = {}
CFTGT = {"NH_land_MJJ": "T_nh_land_MJJ", "NH_MJJ": "T_nh_MJJ",
         "GLB_MJJ": "T_gl_MJJ", "NH_land_JJA": "T_nh_land_JJA"}
for tname, tcol in CFTGT.items():
    if tcol not in ann.columns or pd.isna(ann.loc[2026, tcol]):
        continue
    obs = ann.loc[2026, tcol]
    base = ann.loc[1991:2020, tcol].mean()
    a = ev.loc[ev["tier_MJJ"] == "2_weak_EL", tcol].dropna()
    b = ev.loc[ev["tier_MJJ"] == "3_neutral", tcol].dropna()
    effect = float(a.mean() - b.mean()) if len(a) > 2 else np.nan
    cf[tname] = {"obs_2026": round(float(obs), 3),
                 "baseline_1991_2020": round(float(base), 3),
                 "total_anomaly": round(float(obs - base), 3),
                 "ENSO_cond_mean_effect": round(effect, 3) if np.isfinite(effect) else None,
                 "n_EL": int(len(a)), "n_neutral": int(len(b)),
                 "ENSO_share_pct": (round(effect / (obs - base) * 100, 1)
                                    if np.isfinite(effect) and abs(obs - base) > 1e-9 else None)}
    print(f"    {tname}: 2026={obs:.3f} vs 1991-2020={base:.3f} => 总异常 {obs-base:+.3f}；"
          f"ENSO 条件均值效应 {effect:+.3f} (n={len(a)} vs {len(b)})"
          f" => 占比 ≈ {cf[tname]['ENSO_share_pct']}%")
res["counterfactual"] = cf

res["corr_sameyear"] = dd.to_dict(orient="records")
res["corr_leadlag"] = ld.to_dict(orient="records")
res["variance_decomp"] = var_expl
res["events"] = events_out
res["compare"] = cmp_out
json.dump(res, open(os.path.join(RES, "enso_europe_summer.json"), "w"),
          ensure_ascii=False, indent=1)
ann.to_csv(os.path.join(RES, "enso_europe_seasonal_table.csv"), encoding="utf-8-sig")
print("\n[OK] results/enso_europe_summer.json + enso_europe_seasonal_table.csv")
