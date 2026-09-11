# -*- coding: utf-8 -*-
"""CL(WTI) 月差计算 —— 日线 + 4小时 —— 合约梯扩展到 M13（CL2610 ~ CL2710）

沿革：由 cl_spread_20260910.py（6 腿）扩展为 13 腿，2026-09-11。
      **列名向后兼容**：原 6 腿版本的 abs1_OCT26_NOV26 等列名全部保留。

口径（沿用项目既定）：
  价差 = 近月 − 远月；>0 = backwardation，<0 = contango。单位 USD/bbl。
  abs{1,2,3} = 跨 1/2/3 个交割月的绝对价差；pm{1,2,3} = abs ÷ 跨月数（每月陡度）。
  ⚠️ abs 可直接挂单，pm 仅用于跨档比陡度；两者结论不同，不可混用。

输出（覆盖）：
  data/cl_contracts/spread/cl_spread_daily.csv
  data/cl_contracts/spread/cl_spread_4h.csv
  data/cl_contracts/spread/cl_spread_summary.md
  data/cl_contracts/spread/cl_spread_meta.json
"""
import csv
import json
import os
import datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, "data", "cl_contracts")
OUTS = os.path.join(ROOT, "spread")

LEGS = [("M1", "CL2610", "OCT26", "US.CL2610"),
        ("M2", "CL2611", "NOV26", "US.CL2611"),
        ("M3", "CL2612", "DEC26", "US.CL2612"),
        ("M4", "CL2701", "JAN27", "US.CL2701"),
        ("M5", "CL2702", "FEB27", "US.CL2702"),
        ("M6", "CL2703", "MAR27", "US.CL2703"),
        ("M7", "CL2704", "APR27", "US.CL2704"),
        ("M8", "CL2705", "MAY27", "US.CL2705"),
        ("M9", "CL2706", "JUN27", "US.CL2706"),
        ("M10", "CL2707", "JUL27", "US.CL2707"),
        ("M11", "CL2708", "AUG27", "US.CL2708"),
        ("M12", "CL2709", "SEP27", "US.CL2709"),
        ("M13", "CL2710", "OCT27", "US.CL2710")]
N = len(LEGS)
VOL_COLS = ["vol_M1", "vol_M6", "vol_M13"]

COMBOS = {g: [(LEGS[i][2], LEGS[i + g][2], i, i + g) for i in range(N - g)] for g in (1, 2, 3)}
SLOT2MONTH = {a: b for a, b, _, _ in LEGS}


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
    keys = sorted(px[LEGS[0][1]])
    keys = [k for k in keys if all(k in px[m] for _, m, _, _ in LEGS)]
    rows = []
    for k in keys:
        r = {"ts": k}
        for _, m, _, _ in LEGS:
            r[m] = px[m][k]["c"]
        for g, combos in COMBOS.items():
            for near, far, i, j in combos:
                a = r[LEGS[i][1]] - r[LEGS[j][1]]
                r[f"abs{g}_{near}_{far}"] = round(a, 4)
                r[f"pm{g}_{near}_{far}"] = round(a / g, 4)
        for c in VOL_COLS:
            m = SLOT2MONTH[c.replace("vol_", "")]
            r[c] = px[m][k]["v"]
        rows.append(r)
    return rows


def hdr():
    h = ["ts"] + [m for _, m, _, _ in LEGS]
    for g in (1, 2, 3):
        h += [f"abs{g}_{n}_{f}" for n, f, _, _ in COMBOS[g]]
    for g in (1, 2, 3):
        h += [f"pm{g}_{n}_{f}" for n, f, _, _ in COMBOS[g]]
    return h + VOL_COLS


def write(ktype, rows):
    H = hdr()
    fn = os.path.join(OUTS, f"cl_spread_{ktype}.csv")
    with open(fn, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(H)
        for r in rows:
            w.writerow([r.get(c, "") for c in H])
    print(f"-> {os.path.relpath(fn, BASE)}  {len(rows)} rows  {len(H)} cols  {rows[0]['ts']} ~ {rows[-1]['ts']}")
    return fn


def stat(rows, key):
    v = [r[key] for r in rows if key in r]
    if not v:
        return None
    return {"last": round(v[-1], 3), "mean": round(sum(v) / len(v), 3),
            "min": round(min(v), 3), "max": round(max(v), 3),
            "pctile": round(sum(1 for x in v if x <= v[-1]) / len(v) * 100, 1), "n": len(v)}


if __name__ == "__main__":
    os.makedirs(OUTS, exist_ok=True)
    res, lastrow, firstrow = {}, {}, {}
    for ktype in ("daily", "4h"):
        rows = build(ktype)
        write(ktype, rows)
        lastrow[ktype], firstrow[ktype] = rows[-1], rows[0]
        res[ktype] = {c: stat(rows, c) for c in hdr() if c.startswith(("abs", "pm"))}

    L = [f"# CL(WTI) 月差明细 — {firstrow['daily']['ts']} ~ {lastrow['daily']['ts']}", "",
         f"合约梯 {N} 腿：M1=CL2610 OCT26 → M{ N }=CL2710 OCT27。", "",
         "口径：价差 = 近月 − 远月（>0 = backwardation）。**abs = 绝对价差（USD/bbl，可直接挂单）；"
         "pm = 每月陡度（abs ÷ 跨月数，USD/月，仅用于跨档比陡度）**。", ""]
    for ktype, lab in (("daily", "日线"), ("4h", "4小时")):
        L += [f"## {lab}", "",
              "| 跨月 | 组合 | 最新 abs | 最新 pm | abs均值 | abs最小 | abs最大 | abs最新分位 |",
              "|---|---|---|---|---|---|---|---|"]
        for g in (1, 2, 3):
            for n_, f_, _, _ in COMBOS[g]:
                k = f"{n_}_{f_}"
                a, p = res[ktype][f"abs{g}_{k}"], res[ktype][f"pm{g}_{k}"]
                L.append(f"| +{g} | {n_}−{f_} | {a['last']:+.2f} | {p['last']:+.2f} | "
                         f"{a['mean']:+.2f} | {a['min']:+.2f} | {a['max']:+.2f} | {a['pctile']}% |")
        L.append("")
    L += ["## 三档汇总（绝对值 vs 陡度）", "",
          "| 档位 | 组合数 | 最新 abs 区间 | 最新 pm 均值 | 20日前 abs 均值 | 窗口起点 abs 均值 |",
          "|---|---|---|---|---|---|"]
    rows = build("daily")
    for g in (1, 2, 3):
        aa = [lastrow["daily"][f"abs{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g]]
        pp = [lastrow["daily"][f"pm{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g]]
        a20 = [rows[-21][f"abs{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g]]
        a0 = [rows[0][f"abs{g}_{n}_{f}"] for n, f, _, _ in COMBOS[g]]
        L.append(f"| +{g} | {len(COMBOS[g])} | {min(aa):+.2f} ~ {max(aa):+.2f} | "
                 f"{sum(pp)/len(pp):.2f} | {sum(a20)/len(a20):+.2f} | {sum(a0)/len(a0):+.2f} |")
    L.append("")
    with open(os.path.join(OUTS, "cl_spread_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("\n" + "\n".join(L[:14]))

    meta = {"generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "futu MCP quote_history_kline (ktype=2 日线 / ktype=15 240分钟)",
            "legs": [{"slot": a, "code": b, "month": c} for a, b, c, _ in LEGS],
            "combos": {f"+{g}": [f"{n}_{f}" for n, f, _, _ in COMBOS[g]] for g in (1, 2, 3)},
            "convention": "abs = 近月-远月 (USD/bbl)；pm = abs/跨月数 (USD/月)",
            "range": {"daily": [firstrow["daily"]["ts"], lastrow["daily"]["ts"]],
                      "4h": [firstrow["4h"]["ts"], lastrow["4h"]["ts"]]},
            "stats": res}
    with open(os.path.join(OUTS, "cl_spread_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    r = lastrow["daily"]
    print(f"\n[质量] 末行 vol_M1={r['vol_M1']:.0f}  vol_M6={r['vol_M6']:.0f}  vol_M13={r['vol_M13']:.0f}")
    print("[质量] 末行收盘: " + "  ".join(f"{m}={r[m]:.2f}" for _, m, _, _ in LEGS))
