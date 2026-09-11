# -*- coding: utf-8 -*-
"""
4h RSI 超买  vs  4h 月差收敛  —— 事件研究
数据: data/cl_contracts/spread/cl_spread_4h.csv  (2026-03-10 ~ 2026-09-09, 770 bars)
价格: CLcurrent (=2610 近月) 4h close
口径: abs = 近月-远月 (>0 = backwardation);  收敛 := Δabs < 0
"""
import csv, json, math
import numpy as np

BASE = r"C:\Users\Administrator\Desktop\stock"
SPREAD = BASE + r"\data\cl_contracts\spread\cl_spread_4h.csv"

def load():
    rows = list(csv.DictReader(open(SPREAD, encoding="utf-8-sig")))
    ts = [r["ts"] for r in rows]
    def col(k):
        return np.array([float(r[k]) for r in rows])
    price = col("CL2610")
    spreads = {}
    for k in rows[0]:
        if k.startswith("abs"):
            spreads[k] = col(k)
    return ts, price, spreads

def rsi_wilder(close, n=14):
    d = np.diff(close)
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    out = np.full(len(close), np.nan)
    if len(close) <= n:
        return out
    au = up[:n].mean(); ad = dn[:n].mean()
    out[n] = 100.0 if ad == 0 else 100 - 100/(1 + au/ad)
    for i in range(n+1, len(close)):
        au = (au*(n-1) + up[i-1])/n
        ad = (ad*(n-1) + dn[i-1])/n
        out[i] = 100.0 if ad == 0 else 100 - 100/(1 + au/ad)
    return out

def fwd_change(x, h):
    """Δ over next h bars; last h entries = nan"""
    out = np.full(len(x), np.nan)
    out[:-h] = x[h:] - x[:-h]
    return out

def block_boot_diff(cond_mask, all_vals, block=12, nboot=5000, seed=7):
    """H0: conditional mean == unconditional mean. Stationary block bootstrap."""
    rng = np.random.default_rng(seed)
    idx_all = np.arange(len(all_vals))
    valid = ~np.isnan(all_vals)
    idx_all = idx_all[valid]; vals = all_vals[valid]
    mask = cond_mask[valid]
    obs = np.nanmean(vals[mask]) - np.nanmean(vals)
    n = len(vals)
    nb = int(np.ceil(n/block))
    diffs = np.empty(nboot)
    for b in range(nboot):
        starts = rng.integers(0, n, size=nb)
        sel = np.concatenate([np.arange(s, min(s+block, n)) for s in starts])[:n]
        v = vals[sel]; m = mask[sel]
        if m.sum() == 0:
            diffs[b] = np.nan; continue
        diffs[b] = v[m].mean() - v.mean()
    diffs = diffs[~np.isnan(diffs)]
    # two-sided p
    p = 2*min((diffs <= 0).mean(), (diffs >= 0).mean())
    return obs, float(p), float(np.percentile(diffs,2.5)), float(np.percentile(diffs,97.5))

def events_cross(mask, min_gap):
    """first bar crossing into mask from below, with min_gap between events"""
    ev = []
    last = -10**9
    prev = False
    for i in range(len(mask)):
        if mask[i] and not prev and (i - last) >= min_gap:
            ev.append(i); last = i
        prev = mask[i]
    return ev

ts, price, spreads = load()
N = len(ts)
print(f"bars={N}  {ts[0]} -> {ts[-1]}")

RSI_N = 14
OB = 70.0
rsi = rsi_wilder(price, RSI_N)

# 覆盖诊断
print(f"\nRSI({RSI_N}) 4h: mean={np.nanmean(rsi):.1f}  min={np.nanmin(rsi):.1f}  max={np.nanmax(rsi):.1f}")
for th in (70,75,80):
    m = rsi >= th
    print(f"  RSI>={th}: {int(np.nansum(m))} bars ({100*np.nansum(m)/np.sum(~np.isnan(rsi)):.1f}%)")

# 各段月差与价格的相关（水平）
print("\n[水平相关] corr(price, spread):")
for k,v in spreads.items():
    print(f"  {k:22s} {np.corrcoef(price, v)[0,1]:+.3f}")

# ============ 主分析: 价格 RSI 超买 -> 月差前向变化 ============
HORIZONS = [1,2,3,6,12,24]
print("\n" + "="*100)
print("A. 价格RSI(14)>=70 条件下的前向月差变化 (pooled, 全样本)")
print("="*100)
resA = {}
for k, sp in spreads.items():
    resA[k] = {}
    for h in HORIZONS:
        d = fwd_change(sp, h)
        m = (rsi >= OB)
        obs, p, lo, hi = block_boot_diff(m, d, block=max(6,h))
        base = np.nanmean(d)
        resA[k][h] = dict(cond=float(np.nanmean(d[m])), base=float(base), p=p, lo=lo, hi=hi)

focus = ["abs1_OCT26_NOV26","abs1_NOV26_DEC26","abs2_NOV26_JAN27","abs3_OCT26_JAN27","abs3_DEC26_MAR27"]
print(f"{'spread':22s}" + "".join([f"  h={h:<3d}" for h in HORIZONS]))
for k in focus:
    line = f"{k:22s}"
    for h in HORIZONS:
        r = resA[k][h]
        line += f"  {r['cond']:+.3f}"
    print(line)
print("\n  基准(全样本均值):")
line = f"{'':22s}"
for h in HORIZONS:
    line += f"  {resA[focus[0]][h]['base']:+.3f}"
print(line)

print("\n  p值 (block bootstrap, H0: 条件均值=全样本均值):")
print(f"{'spread':22s}" + "".join([f"  h={h:<3d}" for h in HORIZONS]))
for k in focus:
    line = f"{k:22s}"
    for h in HORIZONS:
        p = resA[k][h]["p"]
        star = "*" if p < 0.05 else " "
        line += f" {p:.3f}{star}"
    print(line)

# ============ 事件法 ============
print("\n" + "="*100)
print("B. 事件法 (RSI 首次上穿 70, 事件间隔>=h) —— 收敛=Δ<0")
print("="*100)
resB = {}
for h in HORIZONS:
    ev = events_cross(rsi >= OB, min_gap=h)
    resB[h] = {}
    for k in focus:
        d = fwd_change(spreads[k], h)
        vals = np.array([d[i] for i in ev if not np.isnan(d[i])])
        resB[h][k] = dict(n=len(vals), mean=float(vals.mean()) if len(vals) else np.nan,
                          med=float(np.median(vals)) if len(vals) else np.nan,
                          pct_conv=float((vals<0).mean()*100) if len(vals) else np.nan)
    print(f"\n  h={h} 事件数={len(ev)}")
    print(f"    {'spread':22s} {'meanΔ':>8s} {'medΔ':>8s} {'收敛占比':>9s}")
    for k in focus:
        r = resB[h][k]
        print(f"    {k:22s} {r['mean']:+8.3f} {r['med']:+8.3f} {r['pct_conv']:8.1f}%")

# ============ C. 月差自身 RSI 超买 ============
print("\n" + "="*100)
print("C. 月差自身 4h RSI(14)>=70 -> 月差是否收敛 (经典均值回归检验)")
print("="*100)
resC = {}
for k in focus:
    sr = rsi_wilder(spreads[k], RSI_N)
    resC[k] = {}
    row = f"{k:22s}"
    for h in HORIZONS:
        d = fwd_change(spreads[k], h)
        m = (sr >= OB)
        if np.nansum(m) < 5:
            row += f"   n/a "; resC[k][h]=None; continue
        obs, p, lo, hi = block_boot_diff(m, d, block=max(6,h))
        resC[k][h] = dict(cond=float(np.nanmean(d[m])), base=float(np.nanmean(d)), p=p)
        row += f"  {obs:+.3f}{'*' if p<0.05 else ' '}"
    print(row)
print("   (值为 条件均值-全样本均值; * = p<0.05)")

# ============ D. 混淆检验: 价格自身在超买后怎么走 ============
print("\n" + "="*100)
print("D. 混淆检验: RSI>=70 后价格自身前向变化 (若价格不跌, 月差收敛就缺乏来源)")
print("="*100)
for h in HORIZONS:
    d = fwd_change(price, h)
    m = (rsi >= OB)
    obs, p, lo, hi = block_boot_diff(m, d, block=max(6,h))
    print(f"  h={h:<3d}  条件={np.nanmean(d[m]):+7.3f}  基准={np.nanmean(d):+7.3f}  差={obs:+7.3f}  p={p:.3f}")

# ============ E. 分阶段 ============
print("\n" + "="*100)
print("E. 分阶段 (切点 2026-07-10): 窗口一=3/10-7/10, 窗口二=7/10-9/09")
print("="*100)
CUT = None
for i,t in enumerate(ts):
    if t >= "2026-07-10":
        CUT = i; break
print(f"  切点 bar={CUT}  date={ts[CUT]}")
for name, sl in [("W1 3/10-7/10", slice(0,CUT)), ("W2 7/10-9/09", slice(CUT,None))]:
    pr = price[sl]; rs = rsi_wilder(pr, RSI_N)
    print(f"\n  --- {name}  (n={len(pr)})  RSI>=70 占比 {100*np.nansum(rs>=70)/np.sum(~np.isnan(rs)):.1f}% ---")
    for k in focus:
        sp = spreads[k][sl]
        d = fwd_change(sp, 12)
        m = rs >= OB
        if np.nansum(m) < 5:
            print(f"    {k:22s} 超买样本不足({int(np.nansum(m))})"); continue
        base = np.nanmean(d)
        print(f"    {k:22s} h=12  条件={np.nanmean(d[m]):+7.3f}  基准={base:+7.3f}  差={np.nanmean(d[m])-base:+7.3f}  收敛占比={100*np.nanmean(d[m]<0):5.1f}%")

out = dict(meta=dict(bars=N, start=ts[0], end=ts[-1], rsi_n=RSI_N, ob=OB),
           A=resA, B=resB, C=resC)
json.dump(out, open(BASE+r"\results\rsi_ob_spread_converge.json","w"), ensure_ascii=False, indent=1)
print("\n[saved] results/rsi_ob_spread_converge.json")
