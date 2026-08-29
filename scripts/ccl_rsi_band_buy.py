# -*- coding: utf-8 -*-
"""
CCL RSI 档位买入回测 —— 用户自定义口径 2026-08-29
问题: 当前 CCL RSI14 = 34.99（落在 30-40 档），历史上 RSI 处于该档位（及全档位）时买入后的表现
口径:
  - 状态式信号: 当日收盘 RSI 处于某档位 → 当日收盘价买入（可用性: 当日收盘价=信号确定后即成交，偏乐观但口径一致）
  - 档位划分: <30 / 30-40 / 40-50 / 50-60 / 60-70 / ≥70
  - 窗口: T+5 / T+10 / T+20（交易日，fwdN = 未来 N 个交易日 adj_close 收益，百分数×100）
  - 超额: CCL fwd - SPY 同窗口 fwd（百分数差 pp）
  - 主口径: 状态全样本（RSI 处于档位的每一天）；附 cd10 去重对照（窗口重叠→独立性弱）
  - 显著性: 三档 sig(p<0.01)/edge(0.01≤p<0.05)/no(p≥0.05)，t 检验均值 vs 0 + 二项近似胜率 p
  - 分阶段: 疫情前(<2020-02-20) / 疫情~2022(至2022-12-31) / 本轮牛市(2023起)
输出 results/ccl_rsi_band_buy.json
"""
import csv, json, os, statistics as st
from collections import Counter
from math import sqrt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

def load(name):
    d = os.path.join(DATA, name)
    fn = [f for f in os.listdir(d) if "1D" in f and not f.startswith("BATS_")][0]
    px = {}
    with open(os.path.join(d, fn)) as f:
        for row in csv.DictReader(f):
            dt = row["date"].split(" ")[0]
            v = row["adj_close"] if row["adj_close"] else row["close"]
            if v:
                px[dt] = float(v)
    return px

ccl, spy = load("ccl"), load("spy")
dates = sorted(set(ccl) & set(spy))
px = [ccl[d] for d in dates]
sp = [spy[d] for d in dates]
n = len(dates)

# ---------- RSI14 (Wilder) ----------
alpha = 1 / 14
ag = al = 0.0
rsi = [None] * n
for i in range(1, n):
    dd = px[i] - px[i - 1]
    g = dd if dd > 0 else 0.0
    l = -dd if dd < 0 else 0.0
    ag += alpha * (g - ag)
    al += alpha * (l - al)
    rsi[i] = 100 - 100 / (1 + (ag / al if al > 0 else float("inf")))

# ---------- 当前档位 ----------
cur_rsi = rsi[-1]
def band_name(r):
    if r < 30: return "<30"
    if r < 40: return "30-40"
    if r < 50: return "40-50"
    if r < 60: return "50-60"
    if r < 70: return "60-70"
    return "≥70"
CUR_BAND = band_name(cur_rsi)
BANDS = ["<30", "30-40", "40-50", "50-60", "60-70", "≥70"]

# 当前 RSI 历史分位
rsi_hist = [r for r in rsi if r is not None]
cur_pct = 100 * sum(1 for r in rsi_hist if r <= cur_rsi) / len(rsi_hist)

def stage_of(d):
    if d < "2020-02-20":
        return "疫情前"
    if d <= "2022-12-31":
        return "疫情~2022"
    return "本轮牛市"

def wfeat(p, N, t):
    seg = p[t + 1:t + 1 + N]
    if len(seg) < N:
        return None
    maxg = max(seg) / p[t] - 1
    fwd = seg[-1] / p[t] - 1
    return {"maxg": maxg, "fwd": fwd}

WINS = (5, 10, 20)

# ---------- 状态式全样本事件 ----------
ev = []
for i in range(1, n - 20):
    if rsi[i] is None:
        continue
    b = band_name(rsi[i])
    feats = {"i": i}
    ok = True
    for NN in WINS:
        w = wfeat(px, NN, i)
        ws = wfeat(sp, NN, i)
        if w is None or ws is None:
            ok = False
            break
        feats[f"maxg{NN}"] = w["maxg"] * 100
        feats[f"fwd{NN}"] = w["fwd"] * 100
        feats[f"sfwd{NN}"] = ws["fwd"] * 100
    if ok:
        feats["date"] = dates[i]
        feats["rsi"] = round(rsi[i], 1)
        feats["band"] = b
        feats["ex20"] = round(feats["fwd20"] - feats["sfwd20"], 2)
        ev.append(feats)

def cd10_filter(rows):
    keep, last = [], -10 ** 9
    for e in sorted(rows, key=lambda x: x["i"]):
        if e["i"] - last >= 10:
            keep.append(e)
            last = e["i"]
    return sorted(keep, key=lambda x: x["i"])

def ttest_p(xs):
    """均值 vs 0 双侧 t 检验 p 值（正态近似，n 小时视作上限）"""
    if len(xs) < 3:
        return None
    m = st.mean(xs)
    sd = st.stdev(xs) if len(xs) > 1 else 0.0
    if sd == 0:
        return None
    t = m / (sd / sqrt(len(xs)))
    df = len(xs) - 1
    # 近似: t 分布用正态（n 足够大）——精确用 beta 函数实现 Student t 尾概率
    import math
    x = df / (df + t * t)
    # I_x(df/2, 1/2) 不完全 beta 函数（正则化）→ 用 scipy 不可靠则自实现
    def betacf(a, b, x, itmax=200, eps=3e-12):
        qab = a + b; qap = a + 1.0; qam = a - 1.0
        c = 1.0; d = 1.0 - qab * x / qap
        if abs(d) < 1e-30: d = 1e-30
        d = 1.0 / d; h = d
        for m in range(1, itmax + 1):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30: d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30: c = 1e-30
            d = 1.0 / d; h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-30: d = 1e-30
            c = 1.0 + aa / c
            if abs(c) < 1e-30: c = 1e-30
            d = 1.0 / d; delt = d * c; h *= delt
            if abs(delt - 1.0) < eps: break
        return h
    def betai(a, b, x):
        if x <= 0.0: return 0.0
        if x >= 1.0: return 1.0
        bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return bt * betacf(a, b, x) / a
        return 1.0 - bt * betacf(b, a, 1.0 - x) / b
    p_two = betai(0.5 * df, 0.5, df / (df + t * t))
    return p_two

def binom_p(win, total):
    """胜率 vs 50% 二项近似 p（单侧 → 双侧×2）"""
    if total < 3 or win == 0 or win == total:
        return None
    p_hat = win / total
    z = (p_hat - 0.5) / sqrt(0.25 / total)
    import math
    p_one = 0.5 * math.erfc(z / sqrt(2))
    return min(1.0, 2 * p_one)

def sig(p):
    if p is None: return "-"
    if p < 0.01: return "sig"
    if p < 0.05: return "edge"
    return "no"

def stat_block(rows):
    out = {}
    for NN in WINS:
        xs = [r[f"fwd{NN}"] for r in rows if r[f"fwd{NN}"] is not None]
        mx = [r[f"maxg{NN}"] for r in rows if r[f"maxg{NN}"] is not None]
        if not xs:
            out[f"fwd{NN}"] = None
            continue
        win = sum(1 for x in xs if x > 0)
        p_mean = ttest_p(xs)
        p_win = binom_p(win, len(xs))
        out[f"fwd{NN}"] = {
            "n": len(xs), "mean": round(st.mean(xs), 2), "median": round(st.median(xs), 2),
            "std": round(st.stdev(xs), 2) if len(xs) > 1 else None,
            "win": round(100 * win / len(xs), 1),
            "p25": round(sorted(xs)[int(len(xs) * 0.25)], 2),
            "p75": round(sorted(xs)[int(len(xs) * 0.75)], 2),
            "p_mean": (round(p_mean, 4) if p_mean is not None else None),
            "sig_mean": sig(p_mean),
            "p_win": (round(p_win, 4) if p_win is not None else None),
            "sig_win": sig(p_win),
        }
        out[f"maxg{NN}"] = {"n": len(mx), "mean": round(st.mean(mx), 2), "median": round(st.median(mx), 2)}
    ex = [r["ex20"] for r in rows]
    if ex:
        out["ex20"] = {"n": len(ex), "mean": round(st.mean(ex), 2), "median": round(st.median(ex), 2),
                       "win": round(100 * sum(1 for x in ex if x > 0) / len(ex), 1)}
    else:
        out["ex20"] = None
    out["ever_positive"] = (round(100 * sum(1 for r in rows if r["maxg20"] is not None and r["maxg20"] > 0) / max(1, sum(1 for r in rows if r["maxg20"] is not None)), 1)
                            if any(r["maxg20"] is not None for r in rows) else None)
    return out

def by_band(rows):
    return {b: stat_block([r for r in rows if r["band"] == b]) for b in BANDS}

# ---------- 基率（全期所有日） ----------
base = stat_block(ev)

# ---------- 当前档位聚焦 ----------
cur_ev = [r for r in ev if r["band"] == CUR_BAND]
cur_cd10 = cd10_filter(cur_ev)
# 窄窗敏感性: 当前 RSI ±2.5 窗口 [32.5, 37.5)
narrow_ev = [r for r in ev if 32.5 <= r["rsi"] < 37.5]
# 首次进入当前档位（事件式: 前日不在该档位）
first_ev = []
prev_in = False
for r in sorted(ev, key=lambda x: x["i"]):
    if r["band"] == CUR_BAND:
        if not prev_in:
            first_ev.append(r)
        prev_in = True
    else:
        prev_in = False

# ---------- 阶段 × 当前档位 ----------
stage_cur = {}
for stg in ["疫情前", "疫情~2022", "本轮牛市"]:
    sub = [r for r in cur_ev if stage_of(r["date"]) == stg]
    stage_cur[stg] = stat_block(sub)

# ---------- 年度分布（当前档位） ----------
year_dist = [{"y": y, "n": c} for y, c in sorted(Counter(r["date"][:4] for r in cur_ev).items())]

# ---------- 最近 8 次（当前档位） ----------
recent = sorted(cur_ev, key=lambda x: x["date"])[-8:][::-1]

# ---------- 当前档位 RSI 分布 ----------
cur_rsi_list = [r["rsi"] for r in cur_ev]

# ---------- 对照: 全部档位状态式 ----------
by_band_all = by_band(ev)
by_band_cd10 = by_band(cd10_filter(ev))

for e in ev:
    e.pop("i", None)

res = {
    "meta": {"ticker": "CCL", "event": "RSI 档位状态买入：当日收盘 RSI 处于档位 → 当日收盘价买入，持有 T+N 交易日",
             "cur_rsi": round(cur_rsi, 2), "cur_band": CUR_BAND, "cur_pct": round(cur_pct, 1),
             "data_end": dates[-1], "n_bars": n,
             "note": "状态式信号（连续停留=连续信号，窗口重叠→独立性强、显著性为上限）；超额=CCL fwd - SPY 同窗口 fwd(pp)；fwd=maxG 用 adj_close"},
    "base": base,
    "by_band": by_band_all, "by_band_cd10": by_band_cd10,
    "cur_band": {"all": stat_block(cur_ev), "cd10": stat_block(cur_cd10),
                 "narrow_325_375": stat_block(narrow_ev),
                 "first_enter": stat_block(first_ev),
                 "n_all": len(cur_ev), "n_cd10": len(cur_cd10), "n_narrow": len(narrow_ev), "n_first": len(first_ev)},
    "stage_cur": stage_cur,
    "year_dist": year_dist,
    "cur_rsi_dist": {"mean": round(st.mean(cur_rsi_list), 1), "median": round(st.median(cur_rsi_list), 1),
                     "min": round(min(cur_rsi_list), 1), "max": round(max(cur_rsi_list), 1)},
    "recent": recent,
}
out_path = os.path.join(OUT, "ccl_rsi_band_buy.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

# ---------- 打印摘要 ----------
def brief(tag, s):
    if not s or not s.get("fwd20"):
        print(f"[{tag}] n=0"); return
    f = s["fwd20"]
    print(f"[{tag}] n={f['n']} | fwd20 mean {f['mean']:+.2f}% med {f['median']:+.2f}% | 胜率 {f['win']}% (p={f['p_win']},{f['sig_win']}) | 超额med {s['ex20']['median']:+.2f}pp | 曾浮盈 {s['ever_positive']}%")

print(f"CCL {n} 根K线 | 数据截止 {dates[-1]} | 当前 RSI14 = {cur_rsi:.2f}（档位 {CUR_BAND}，历史分位 {cur_pct:.1f}%）")
print("[基率全期]")
brief("base", base)
print("[全档位状态式]")
for b in BANDS:
    brief(f"档位 {b}", by_band_all[b])
print("[当前档位 30-40] 主口径 vs cd10 vs 窄窗32.5-37.5 vs 首次进入")
for tag, s in [("all", res["cur_band"]["all"]), ("cd10", res["cur_band"]["cd10"]),
               ("narrow", res["cur_band"]["narrow_325_375"]), ("first", res["cur_band"]["first_enter"])]:
    brief(tag, s)
print("[阶段分解-当前档位]")
for stg in ["疫情前", "疫情~2022", "本轮牛市"]:
    brief(stg, stage_cur[stg])
print("written:", out_path)
