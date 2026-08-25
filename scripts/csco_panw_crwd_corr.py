# -*- coding: utf-8 -*-
"""
CSCO / PANW / CRWD 相关性分析
口径：日线对数收益；静态 Pearson 相关；60 日滚动相关（主口径，历史报告一致）
窗口：2026-02-01 起（滚动 warmup 用 2025-10 前拉的数据）
分段：2026-02至04 / 05至07 / 08月以来 + 2025-01~2026-01(断裂前对照)
"""
import pandas as pd, numpy as np, json, os, math

DATA = r"C:\Users\Administrator\Desktop\stock\data"
OUT = r"C:\Users\Administrator\Desktop\stock\results"

def load(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")
    df = df[["adj_close"]].dropna()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df

tks = ["CSCO", "PANW", "CRWD"]
px = pd.concat([load(t) for t in tks], axis=1)
px.columns = tks
ret = np.log(px / px.shift(1)).dropna()

# 聚焦窗口 2026-02 起
D0 = pd.Timestamp("2026-02-01")
focus = ret[ret.index >= D0]
print("focus 窗口:", focus.index[0].date(), "~", focus.index[-1].date(), "共", len(focus), "日")

def pearson_r(a, b):
    m = a.notna() & b.notna()
    if m.sum() < 3: return None
    x, y = a[m], b[m]
    if x.std() == 0 or y.std() == 0: return None
    return float(x.corr(y))

def r_z(r): return 0.5 * math.log((1+r)/(1-r)) if r is not None and abs(r) < 1 else None
def z_r(z): return math.tanh(z) if z is not None else None

# 正态 CDF（无 scipy 依赖，Abramowitz-Stegun 近似，误差<1e-7）
def _ncdf(x):
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    d = 0.3989422804014327 * math.exp(-x*x/2.0)
    p = d * t * (0.319381530 + t*(-0.356563782 + t*(1.781477937 + t*(-1.821255978 + t*1.330274429))))
    return 1.0 - p if x > 0 else p
def p_from_z(z): return 2.0 * (1.0 - _ncdf(abs(z)))

# 1) 静态相关矩阵（focus 窗口）
pairs = [("CSCO","PANW"), ("CSCO","CRWD"), ("PANW","CRWD")]
static = {}
for a,b in pairs:
    m = focus[[a,b]].dropna()
    r = pearson_r(focus[a], focus[b])
    n = len(m)
    # 显著性（Fisher z 双侧，H0: rho=0）
    z = r_z(r); p = p_from_z(z*math.sqrt(n-3)) if z is not None else None
    static[f"{a}×{b}"] = {"r": round(r,4), "n": n, "p": round(p,6) if p is not None else None, "窗口": f"{m.index[0].date()}~{m.index[-1].date()}"}
    print(f"静态 {a}×{b}: r={r:.4f} n={n} p={p:.4f}")

# 2) 分月段静态相关（各段 dropna 后算 r + n）
seg_defs = {
    "2026-02~04":  ("2026-02-01","2026-04-30"),
    "2026-05~07":  ("2026-05-01","2026-07-31"),
    "2026-08至今":  ("2026-08-01","2099-12-31"),
    "2025-01~2026-01": ("2025-01-01","2026-01-31"),  # 断裂前对照
    "2026上半年":  ("2026-01-01","2026-06-30"),
    "2026-02至今":  ("2026-02-01","2099-12-31"),
}
seg = {}
for name,(s,e) in seg_defs.items():
    sub = ret[(ret.index>=pd.Timestamp(s)) & (ret.index<=pd.Timestamp(e))]
    seg[name] = {}
    for a,b in pairs:
        m = sub[[a,b]].dropna().dropna()
        if len(m) < 5: seg[name][f"{a}×{b}"] = None; continue
        r = float(np.corrcoef(m[a], m[b])[0,1])
        n = len(m)
        z = 0.5*math.log((1+r)/(1-r))
        p = p_from_z(z*math.sqrt(n-3))
        seg[name][f"{a}×{b}"] = {"r": round(r,4), "n": n, "p": round(p,6)}
    print(name, {k: (v["r"] if v else None) for k,v in seg[name].items()})

# 3) 60 日滚动相关（主口径；加 30 日辅助）
roll = {}
for a,b in pairs:
    roll[f"{a}×{b}"] = {
        "r60": ret[a].rolling(60).corr(ret[b]),
        "r30": ret[a].rolling(30).corr(ret[b]),
    }

# 滚动相关聚焦窗口内的均值/分位（仅聚焦窗口内取值）
roll_sum = {}
for a,b in pairs:
    r60 = roll[f"{a}×{b}"]["r60"].dropna()
    r60f = r60[r60.index>=D0]
    q = r60f.quantile([0, .25, .5, .75, 1.0])
    roll_sum[f"{a}×{b}"] = {
        "窗口内均值": round(float(r60f.mean()),4),
        "窗口内中位": round(float(r60f.median()),4),
        "分位数": {f"q{k*25}": round(float(v),4) for k,v in q.items()},
        "首值(2026-02起第1个完整窗口)": round(float(r60f.iloc[0]),4),
        "末值": round(float(r60f.iloc[-1]),4),
    }
    print(f"滚动60 {a}×{b}: 均值={roll_sum[f'{a}×{b}']['窗口内均值']} 末值={roll_sum[f'{a}×{b}']['末值']}")

# 4) 方差比 / 相对波动（focus 窗口年化波动率）
vol = focus.std() * math.sqrt(252)
print("\n年化波动率(2026-02至今):", {k: round(v*100,1) for k,v in vol.items()}, "%")

# 5) 相关性水位对比（聚焦 vs 全期 vs 前一年）——用于判断是否处于高/低相关区
for name,(s,e) in [("全历史", (None,None)), ("2024全年",("2024-01-01","2024-12-31")), ("2025全年",("2025-01-01","2025-12-31"))]:
    sub = ret if name=="全历史" else ret[(ret.index>=pd.Timestamp(s)) & (ret.index<=pd.Timestamp(e))]
    vals = []
    for a,b in pairs:
        m = sub[[a,b]].dropna()
        vals.append(round(float(np.corrcoef(m[a],m[b])[0,1]),4))
    print(f"{name} 静态相关:", vals)

# 6) 滚动序列导出（供报告用，含 warmup 起始）
roll_out = pd.DataFrame(index=ret.index)
for a,b in pairs:
    roll_out[f"{a}×{b}_60"] = roll[f"{a}×{b}"]["r60"]
    roll_out[f"{a}×{b}_30"] = roll[f"{a}×{b}"]["r30"]
roll_out = roll_out.dropna(how="all")
# 导出聚焦窗口段（2026-02 前用 warmup 淡色）
roll_out_focus = roll_out[roll_out.index >= pd.Timestamp("2025-10-01")]
roll_out_focus.to_csv(os.path.join(OUT, "csco_panw_crwd_rollcorr.csv"))

# 保存结果
out = {
    "meta": {"窗口": "2026-02-01 至今", "口径": "日线对数收益, 静态Pearson + 60日滚动(主) + 30日(辅)",
             "数据": {t: f"{px[t].dropna().index[0].date()}~{px[t].dropna().index[-1].date()}" for t in tks},
             "年化波动2026-02至今%": {k: round(v*100,1) for k,v in vol.items()}},
    "static_focus": static,
    "segments": seg,
    "rolling_summary": roll_sum,
}
with open(os.path.join(OUT, "csco_panw_crwd_corr.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nSAVED:", os.path.join(OUT, "csco_panw_crwd_corr.json"))