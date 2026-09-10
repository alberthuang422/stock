# -*- coding: utf-8 -*-
"""
CL(WTI) 月差计算 —— 日线 + 4小时 —— 跨 1/2/3 个月全部组合
2026-09-10

口径（沿用项目 09-10 既定）：
  价差 = 近月 − 远月；>0 = backwardation，<0 = contango。单位 USD/bbl。
  「+1/+2/+3 月差」= 跨 1 / 2 / 3 个交割月的价差组合。
  ⚠️ 每档必须**并列输出两列**：绝对价差(abs) 与 每月陡度(per_month = abs / 跨月数)，
     并标注跨月数；两者结论不同，不可只给归一值。

合约梯（2026-09-10）：M1=CL2610 OCT26 / M2=CL2611 NOV26 / M3=CL2612 DEC26
                     M4=CL2701 JAN27 / M5=CL2702 FEB27 / M6=CL2703 MAR27

输出：
  data/cl_contracts/spread/cl_spread_daily.csv
  data/cl_contracts/spread/cl_spread_4h.csv
  data/cl_contracts/spread/cl_spread_summary.md
  data/cl_contracts/spread/cl_spread_meta.json
"""
import csv, json, os, datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, "data", "cl_contracts")
OUTS = os.path.join(ROOT, "spread")

LEGS = [("M1", "CL2610", "OCT26", "US.CL2610"),
        ("M2", "CL2611", "NOV26", "US.CL2611"),
        ("M3", "CL2612", "DEC26", "US.CL2612"),
        ("M4", "CL2701", "JAN27", "US.CL2701"),
        ("M5", "CL2702", "FEB27", "US.CL2702"),
        ("M6", "CL2703", "MAR27", "US.CL2703")]

# 跨月间隔 → 组合（索引对）；gap1=相邻月，gap2=跨2月，gap3=跨3月
COMBOS = {}
for g in (1, 2, 3):
    COMBOS[g] = [(LEGS[i][2], LEGS[i + g][2], i, i + g) for i in range(6 - g)]


def load(ktype, sym):
    fn = os.path.join(ROOT, "daily" if ktype == "daily" else "4h", f"{sym}.csv")
    out = {}
    with open(fn, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = r["date"] if ktype == "daily" else r["datetime"]
            try:
                out[k] = {"c": float(r["close"]), "v": float(r["volume"] or 0)}
            except (TypeError, ValueError):
                continue
    return out


def build(ktype):
    px = {m: load(ktype, s) for _, m, _, s in LEGS}
    keys = sorted(px["CL2610"])
    keys = [k for k in keys if all(k in px[m] for _, m, _, _ in LEGS)]
    rows = []
    for k in keys:
        r = {"ts": k}
        for _, m, _, _ in LEGS:
            r[m] = px[m][k]["c"]
        for g, combos in COMBOS.items():
            for near, far, i, j in combos:
                a = r[LEGS[i][1]] - r[LEGS[j][1]]
                key = f"{near}_{far}"
                r[f"abs{g}_{key}"] = a
                r[f"pm{g}_{key}"] = a / g
        r["vol_M1"] = px["CL2610"][k]["v"]
        r["vol_M6"] = px["CL2703"][k]["v"]
        rows.append(r)
    return rows


def hdr():
    h = ["ts"] + [m for _, m, _, _ in LEGS]
    for g in (1, 2, 3):
        h += [f"abs{g}_{n}_{f}" for n, f, _, _ in COMBOS[g]]
    for g in (1, 2, 3):
        h += [f"pm{g}_{n}_{f}" for n, f, _, _ in COMBOS[g]]
    return h + ["vol_M1", "vol_M6"]


def write(ktype, rows):
    H = hdr()
    fn = os.path.join(OUTS, f"cl_spread_{ktype}.csv")
    with open(fn, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(H)
        for r in rows:
            w.writerow([r.get(c, "") for c in H])
    print(f"-> {os.path.relpath(fn, BASE)}  {len(rows)} rows  {len(H)} cols  "
          f"{rows[0]['ts']} ~ {rows[-1]['ts']}")
    return fn


def stat(rows, key):
    v = [r[key] for r in rows if key in r]
    if not v:
        return None
    return {"last": round(v[-1], 3), "mean": round(sum(v) / len(v), 3),
            "min": round(min(v), 3), "max": round(max(v), 3),
            "pctile": round(sum(1 for x in v if x <= v[-1]) / len(v) * 100, 1),
            "n": len(v)}


if __name__ == "__main__":
    os.makedirs(OUTS, exist_ok=True)
    res, lastrow = {}, {}
    for ktype in ("daily", "4h"):
        rows = build(ktype)
        write(ktype, rows)
        lastrow[ktype] = rows[-1]
        res[ktype] = {c: stat(rows, c) for c in hdr() if c.startswith(("abs", "pm"))}

    L = ["# CL(WTI) 月差明细 — 2026-03-10 ~ 2026-09-10", "",
         "口径：价差 = 近月 − 远月（>0 = backwardation）。**abs = 绝对价差（USD/bbl，可直接挂单）；"
         "pm = 每月陡度（abs ÷ 跨月数，USD/月，仅用于跨档比陡度）**。", ""]
    for ktype, lab in (("daily", "日线"), ("4h", "4小时")):
        L += [f"## {lab}", "",
              "| 跨月 | 组合 | 最新 abs | 最新 pm | abs均值 | abs最小 | abs最大 | abs今日分位 |",
              "|---|---|---|---|---|---|---|---|"]
        for g in (1, 2, 3):
            for n, f, _, _ in COMBOS[g]:
                k = f"{n}_{f}"
                a, p = res[ktype][f"abs{g}_{k}"], res[ktype][f"pm{g}_{k}"]
                L.append(f"| +{g} | {n}−{f} | {a['last']:+.2f} | {p['last']:+.2f} | "
                         f"{a['mean']:+.2f} | {a['min']:+.2f} | {a['max']:+.2f} | {a['pctile']}% |")
        L.append("")
    # 三档汇总
    L += ["## 三档汇总（绝对值 vs 陡度）", "",
          "| 档位 | 组合数 | 最新 abs 区间 | 最新 pm 均值 | 20日前 abs 均值 | 窗口起点 abs 均值 |",
          "|---|---|---|---|---|---|"]
    for ktype in ("daily",):
        rows = build(ktype)
        for g in (1, 2, 3):
            aa = [r[f"abs{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g] for r in [lastrow[ktype]]]
            pp = [r[f"pm{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g] for r in [lastrow[ktype]]]
            a20 = [rows[-21][f"abs{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g]]
            a0 = [rows[0][f"abs{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g]]
            L.append(f"| +{g} | {len(COMBOS[g])} | {min(aa):+.2f} ~ {max(aa):+.2f} | "
                     f"{sum(pp)/len(pp):.2f} | {sum(a20)/len(a20):+.2f} | {sum(a0)/len(a0):+.2f} |")
    L.append("")
    with open(os.path.join(OUTS, "cl_spread_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("\n" + "\n".join(L))

    meta = {"generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "futu MCP quote_history_kline (ktype=2 日线 / ktype=15 240分钟)",
            "legs": [{"slot": a, "code": b, "month": c} for a, b, c, _ in LEGS],
            "combos": {f"+{g}": [f"{n}_{f}" for n, f, _, _ in COMBOS[g]] for g in (1, 2, 3)},
            "convention": "abs = 近月-远月 (USD/bbl)；pm = abs/跨月数 (USD/月)",
            "stats": res}
    with open(os.path.join(OUTS, "cl_spread_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    # 数据质量：远端合约成交量
    r = lastrow["daily"]
    print(f"\n[质量] 末行 vol_M1={r['vol_M1']:.0f}  vol_M6={r['vol_M6']:.0f}")
