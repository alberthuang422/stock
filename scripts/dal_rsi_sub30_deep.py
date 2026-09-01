# -*- coding: utf-8 -*-
"""
DAL RSI<30 细分下钻 —— 找"跌透后的最佳买点"（复刻 56 号 CCL 延展）2026-09-02
口径沿用 64 号主回测: 日 freq 复权价, RSI(14) Wilder, 当日收盘 RSI 从更高区跌入 <30 触发,
当日收盘买入, T+5/10/20, SPY 同窗口对照。
新增维度:
  dd60  = 触发日收盘 vs 前60日最高收盘回撤%
  dd250 = 同上 vs 前250日最高
  pl5   = 触发日前5日累计跌幅% (下跌动能)
  d2m   = 触发后 20 日内达到最高价的天数 (反弹速度, 越小越快)
  rsi   = 触发日 RSI 精值
输出 results/dal_rsi_sub30_deep.json
"""
import csv, json, os, statistics as st

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


dal, spy = load("dal"), load("spy")
dates = sorted(set(dal) & set(spy))
px = [dal[d] for d in dates]
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


def band(r):
    if r >= 40:
        return 0
    if r >= 35:
        return 1
    if r >= 30:
        return 2
    return 3


WINS = (5, 10, 20)

# ---------- 事件（同 64 主口径，只取 <30） ----------
ev = []
for i in range(1, n - 20):
    b = band(rsi[i])
    if b == 3 and rsi[i - 1] is not None and b > band(rsi[i - 1]):
        p0 = px[i]
        hi60 = max(px[i - 60:i]) if i >= 60 else max(px[:i])
        hi250 = max(px[i - 250:i]) if i >= 250 else max(px[:i])
        dd60 = (p0 / hi60 - 1) * 100
        dd250 = (p0 / hi250 - 1) * 100
        pl5 = (p0 / px[i - 5] - 1) * 100 if i >= 5 else None
        feats = {"i": i, "dd60": round(dd60, 1), "dd250": round(dd250, 1),
                 "pl5": round(pl5, 1) if pl5 is not None else None}
        ok = True
        for NN in WINS:
            seg = px[i + 1:i + 1 + NN]
            spg = sp[i + 1:i + 1 + NN]
            if len(seg) < NN:
                ok = False
                break
            maxg = max(seg) / p0 - 1
            fwd = seg[-1] / p0 - 1
            feats[f"maxg{NN}"] = round(maxg * 100, 2)
            feats[f"fwd{NN}"] = round(fwd * 100, 2)
            if NN == 20:
                ihi = seg.index(max(seg)) + 1
                feats["d2m"] = ihi
                feats["maxg20_hi"] = round(max(seg) / p0, 4)
            feats[f"sfwd{NN}"] = round((spg[-1] / sp[i] - 1) * 100, 2)
        if ok:
            feats["date"] = dates[i]
            feats["rsi"] = round(rsi[i], 1)
            feats["ex20"] = round(feats["fwd20"] - feats["sfwd20"], 2)
            ev.append(feats)

print(f"<30 事件: {len(ev)}")

for e in ev:
    e.pop("i", None)


def agg(rows, key):
    xs = [r[key] for r in rows if r[key] is not None]
    if not xs:
        return None
    return {"n": len(xs), "median": round(st.median(xs), 2), "mean": round(st.mean(xs), 2)}


def block(rows):
    out = {}
    for NN in WINS:
        out[f"fwd{NN}"] = agg(rows, f"fwd{NN}")
        out[f"maxg{NN}"] = agg(rows, f"maxg{NN}")
        wins = [r for r in rows if r[f"fwd{NN}"] > 0]
        out[f"win{NN}"] = round(100 * len(wins) / len(rows), 1) if rows else None
    out["ex20"] = agg(rows, "ex20")
    out["d2m"] = agg(rows, "d2m")
    ever = [r for r in rows if r["maxg20"] > 0]
    out["ever_positive"] = round(100 * len(ever) / len(rows), 1) if rows else None
    return out


def seg(rows, pred):
    return [r for r in rows if pred(r)]


res = {}
rsi_cuts = [("rsi<24", lambda r: r["rsi"] < 24),
            ("rsi24-26", lambda r: 24 <= r["rsi"] < 26),
            ("rsi26-28", lambda r: 26 <= r["rsi"] < 28),
            ("rsi28-30", lambda r: 28 <= r["rsi"] < 30)]
res["by_rsi"] = {k: block(seg(ev, p)) for k, p in rsi_cuts}
dd_cuts = [("dd60>-10", lambda r: r["dd60"] > -10),
           ("dd60 -20~-10", lambda r: -20 < r["dd60"] <= -10),
           ("dd60 -30~-20", lambda r: -30 < r["dd60"] <= -20),
           ("dd60<=-30", lambda r: r["dd60"] <= -30)]
res["by_dd60"] = {k: block(seg(ev, p)) for k, p in dd_cuts}
dd250_cuts = [("dd250>-20", lambda r: r["dd250"] > -20),
              ("dd250 -35~-20", lambda r: -35 < r["dd250"] <= -20),
              ("dd250<=-35", lambda r: r["dd250"] <= -35)]
res["by_dd250"] = {k: block(seg(ev, p)) for k, p in dd250_cuts}
grid = {}
for rk, rp in rsi_cuts:
    for dk, dp in dd_cuts:
        key = f"{rk} × {dk}"
        rows = seg(ev, lambda r, rp=rp, dp=dp: rp(r) and dp(r))
        if len(rows) >= 3:
            grid[key] = block(rows)
res["grid_rsi_dd60"] = grid
res["by_d2m"] = {"d2m<=3": block(seg(ev, lambda r: r["d2m"] <= 3)),
                 "d2m>3": block(seg(ev, lambda r: r["d2m"] > 3))}
res["by_pl5"] = {"pl5>=-5": block(seg(ev, lambda r: r["pl5"] >= -5)),
                 "pl5<-5": block(seg(ev, lambda r: r["pl5"] < -5))}
base_ev = []
for i in range(1, n - 20):
    segp = px[i + 1:i + 21]
    segs = sp[i + 1:i + 21]
    if len(segp) < 20:
        continue
    base_ev.append({"fwd20": (segp[-1] / px[i] - 1) * 100, "maxg20": (max(segp) / px[i] - 1) * 100,
                    "sfwd20": (segs[-1] / sp[i] - 1) * 100})
res["base"] = {"fwd20": agg(base_ev, "fwd20"), "maxg20": agg(base_ev, "maxg20"),
               "ex20": {"n": len(base_ev), "median": round(st.median([r["fwd20"] - r["sfwd20"] for r in base_ev]), 2)}}

res["events"] = ev

out_path = os.path.join(OUT, "dal_rsi_sub30_deep.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)


def show(title, d):
    print(f"\n=== {title} ===")
    print(f"{'分档':<22}{'n':>4}{'fwd5中':>8}{'fwd20中':>9}{'胜率20':>8}{'超额20中':>9}{'maxg20中':>9}{'d2m中':>7}")
    for k, v in d.items():
        if v and v["fwd20"] and v["fwd20"]["n"]:
            print(f"{k:<22}{v['fwd20']['n']:>4}{v['fwd5']['median']:>8.1f}{v['fwd20']['median']:>9.1f}"
                  f"{v['win20']:>7.1f}%{v['ex20']['median']:>9.1f}{v['maxg20']['median']:>9.1f}{v['d2m']['median']:>7.1f}")


show("RSI 细分四档 (<30 内)", res["by_rsi"])
show("回撤深度 dd60", res["by_dd60"])
show("回撤深度 dd250", res["by_dd250"])
show("反弹速度 d2m", res["by_d2m"])
show("前5日动能 pl5", res["by_pl5"])
print("\n=== 二维 grid (n>=3) ===")
for k, v in sorted(res["grid_rsi_dd60"].items(), key=lambda x: -(x[1]["fwd20"]["median"] or -99)):
    if v["fwd20"] and v["fwd20"]["n"]:
        print(f"{k:<34} n={v['fwd20']['n']:>3} fwd20中={v['fwd20']['median']:>7.1f} 胜率={v['win20']:>5.1f}% 超额中={v['ex20']['median']:>6.1f} maxg20中={v['maxg20']['median']:>6.1f}")
print("\n基率 fwd20中 %+.2f%% | maxg20中 %+.2f%% | 超额中 %+.2fpp" % (res["base"]["fwd20"]["median"], res["base"]["maxg20"]["median"], res["base"]["ex20"]["median"]))
print("\nwritten:", out_path)
