# -*- coding: utf-8 -*-
"""
CCL RSI 区间跌落买入（阶梯式越跌越买）——复刻 49 号 MCD 口径 2026-08-29
区间: [40,∞) 不买 | [35,40) | [30,35) | [0,30)
触发: 当日收盘 RSI 档位 > 前日档位（更低位）→ 当日收盘买入，档位=当日档位
  例: RSI 36(35-40) 触发第1次; 次日 25(<30) 触发第2次; 跳过区间不补计; 同档内波动不触发
主口径无 cd10 去重（连续触发为设计意图）；另附 cd10 去重对照版
每个事件独立统计窗口 maxG / ER / fwd（T+5/10/20），SPY 同窗口对照
输出 results/ccl_rsi_band_dip.json
"""
import csv, json, os, statistics as st
from collections import Counter

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

BAND_NAME = {1: "35-40", 2: "30-35", 3: "<30"}
BK_ORDER = ["35-40", "30-35", "<30"]


def band(r):
    if r >= 40:
        return 0
    if r >= 35:
        return 1
    if r >= 30:
        return 2
    return 3


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
    path = sum(abs(p[j] - p[j - 1]) for j in range(t + 1, t + 1 + N))
    er = abs(seg[-1] - p[t]) / path if path > 0 else None
    return {"maxg": maxg, "fwd": fwd, "er": er}


WINS = (5, 10, 20)

# ---------- 事件（主口径：无去重） ----------
ev = []
for i in range(1, n - 20):
    b = band(rsi[i])
    if b >= 1 and rsi[i - 1] is not None and b > band(rsi[i - 1]):
        feats = {"i": i}
        ok = True
        for NN in WINS:
            w = wfeat(px, NN, i)
            ws = wfeat(sp, NN, i)
            if w is None or ws is None:
                ok = False
                break
            # 统一存百分数（×100），ER 存小数；与 48 号 JSON 口径一致
            feats[f"maxg{NN}"] = w["maxg"] * 100
            feats[f"fwd{NN}"] = w["fwd"] * 100
            feats[f"er{NN}"] = w["er"]
            feats[f"smaxg{NN}"] = ws["maxg"] * 100
            feats[f"sfwd{NN}"] = ws["fwd"] * 100
        if ok:
            feats["date"] = dates[i]
            feats["rsi"] = round(rsi[i], 1)
            feats["band"] = BAND_NAME[b]
            feats["ex"] = round(feats["fwd20"] - feats["sfwd20"], 2)
            ev.append(feats)


def cd10_filter(ev):
    keep, last = [], -10 ** 9
    for e in sorted(ev, key=lambda x: x["i"]):
        if e["i"] - last >= 10:
            keep.append(e)
            last = e["i"]
    return sorted(keep, key=lambda x: x["i"])


def agg(rows, key):
    xs = [r[key] for r in rows if r[key] is not None]
    if not xs:
        return None
    return {"n": len(xs), "mean": round(st.mean(xs), 2), "median": round(st.median(xs), 2)}


def stat_block(rows):
    out = {}
    for NN in WINS:
        out[f"maxg{NN}"] = agg(rows, f"maxg{NN}")
        out[f"fwd{NN}"] = agg(rows, f"fwd{NN}")
        out[f"er{NN}"] = agg(rows, f"er{NN}")
        out[f"win{NN}"] = (round(100 * sum(1 for r in rows if r[f"fwd{NN}"] is not None and r[f"fwd{NN}"] > 0) / max(1, sum(1 for r in rows if r[f"fwd{NN}"] is not None)), 1)
                           if any(r[f"fwd{NN}"] is not None for r in rows) else None)
    ex = [r["ex"] for r in rows]
    out["ex20"] = {"n": len(ex), "mean": round(st.mean(ex), 2), "median": round(st.median(ex), 2)}
    out["ever_positive"] = (round(100 * sum(1 for r in rows if r["maxg20"] is not None and r["maxg20"] > 0) / max(1, sum(1 for r in rows if r["maxg20"] is not None)), 1)
                            if any(r["maxg20"] is not None for r in rows) else None)
    return out


def by_band(ev):
    return {bk: stat_block([r for r in ev if r["band"] == bk]) for bk in BK_ORDER}


# ---------- 基率（全部重叠 20 日窗口） ----------
base_ev = []
for i in range(1, n - 20):
    w = wfeat(px, 20, i)
    ws = wfeat(sp, 20, i)
    if w and ws:
        base_ev.append({"maxg": w["maxg"] * 100, "fwd": w["fwd"] * 100, "er": w["er"],
                        "smaxg": ws["maxg"] * 100, "sfwd": ws["fwd"] * 100})
base = {"maxg": agg(base_ev, "maxg"), "fwd": agg(base_ev, "fwd"), "er": agg(base_ev, "er"),
        "smaxg": agg(base_ev, "smaxg"), "sfwd": agg(base_ev, "sfwd"),
        "ex": {"n": len(base_ev), "mean": round(st.mean([r["fwd"] - r["sfwd"] for r in base_ev]), 2),
               "median": round(st.median([r["fwd"] - r["sfwd"] for r in base_ev]), 2)}}

# ---------- 阶段 × 档 ----------
stage_band = {}
for stg in ["疫情前", "疫情~2022", "本轮牛市"]:
    sub = [r for r in ev if stage_of(r["date"]) == stg]
    stage_band[stg] = {bk: stat_block([r for r in sub if r["band"] == bk]) for bk in BK_ORDER}

# ---------- cd10 对照 ----------
ev_cd10 = cd10_filter(ev)
by_band_cd10 = by_band(ev_cd10)

# ---------- 年份分布 ----------
year_dist = [{"y": y, "n": c} for y, c in sorted(Counter(r["date"][:4] for r in ev).items())]

# ---------- 最近 5 次 ----------
recent = sorted(ev, key=lambda x: x["date"])[-5:][::-1]

for e in ev:
    e.pop("i", None)

res = {"meta": {"ticker": "CCL", "event": "RSI区间跌落买入：当日收盘RSI档位(35-40/30-35/<30)比前日更低位即当日收盘买入",
                "note": "主口径无cd10去重（连续加仓为设计意图，窗口重叠→独立性弱、显著性为上限）；附cd10去重对照版"},
       "n_total": len(ev), "n_cd10": len(ev_cd10),
       "base": base, "by_band": by_band(ev), "by_band_cd10": by_band_cd10,
       "stage_band": stage_band, "year_dist": year_dist,
       "events": ev, "recent": recent}

out_path = os.path.join(OUT, "ccl_rsi_band_dip.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

print(f"CCL {n} 根K线 | 区间跌落事件 {len(ev)}（cd10 {len(ev_cd10)}）")
print("[基率] maxG med %+.2f%% | fwd med %+.2f%% | ER med %.2f | SPY fwd med %+.2f%%" % (
    base["maxg"]["median"], base["fwd"]["median"], base["er"]["median"], base["sfwd"]["median"]))
for bk in BK_ORDER:
    s = res["by_band"][bk]
    s2 = res["by_band_cd10"][bk]
    print("[档 %s] n=%d (cd10 %d) | fwd20 med %+.2f%% | 胜率 %.1f%% | 超额 med %+.2fpp | 曾解套 %.1f%%" % (
        bk, s["fwd20"]["n"], s2["fwd20"]["n"], s["fwd20"]["median"], s["win20"], s["ex20"]["median"], s["ever_positive"]))
print("written:", out_path)
