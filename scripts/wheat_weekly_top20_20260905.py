# -*- coding: utf-8 -*-
"""
小麦各品种历史单周变动 TOP20（futures-only legacy 口径）
每个品种（SRW/HRW/HRS/三合约合计/黑海/白麦/杜伦麦）独立排队列：
  A. 非商业多头单周增仓 TOP20（nc_l 变，官方 Change 列优先，缺失用 diff）
  B. 非商业空头单周砍仓 TOP20（nc_s 减得最多的 20 周 = 回补）
  C. 净多头单周变化 TOP20（净多增加最多的 20 周）
附带变动后水平（该周收盘持仓）与变动前水平，供上下文判断。
"""
import csv, io, json, os, zipfile
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(BASE, "Temp", "cot")
OUT = os.path.join(BASE, "results", "cot")
os.makedirs(OUT, exist_ok=True)
YEARS = list(range(1995, 2027))

FAMILY = [
    ("SRW 软红冬 (CBOT)", [
        "WHEAT - CBT WHEAT",
        "WHEAT - CHICAGO BOARD OF TRADE",
        "WHEAT-SRW - CHICAGO BOARD OF TRADE"]),
    ("HRW 硬红冬 (CBOT)", [
        "WHEAT - KCBT WHEAT",
        "WHEAT - KANSAS CITY BOARD OF TRADE",
        "WHEAT-HRW - CHICAGO BOARD OF TRADE"]),
    ("HRS 硬红春 (MIAX)", [
        "WHEAT - MGE WHEAT",
        "WHEAT - MINNEAPOLIS GRAIN EXCHANGE",
        "WHEAT-HRSpring - MINNEAPOLIS GRAIN EXCHANGE",
        "WHEAT-HRSpring - MIAX FUTURES EXCHANGE"]),
    ("三合约合计 (SRW+HRW+HRS)", None),
    ("黑海金融小麦 (CBOT)", ["BLACK SEA WHEAT FINANCIAL - CHICAGO BOARD OF TRADE"]),
    ("白小麦 (MGE)", ["WHITE WHEAT - MGE WHITE WHEAT", "WHITE WHEAT - MINNEAPOLIS GRAIN EXCHANGE"]),
    ("硬质杜伦麦 (MGE)", ["HARD AMBER DURUM WHEAT - MINNEAPOLIS GRAIN EXCHANGE"]),
]
EXCLUDE = {"WHEAT -SRW CONSECUTIVE CSO - CHICAGO BOARD OF TRADE", "WHEAT - MIDAMERICA COMMODITY EXCHANGE"}

C_L = "Noncommercial Positions-Long (All)"
C_S = "Noncommercial Positions-Short (All)"
C_SP = "Noncommercial Positions-Spreading (All)"
C_CL = "Commercial Positions-Long (All)"
C_CS = "Commercial Positions-Short (All)"
C_OI = "Open Interest (All)"
CH_L, CH_S = "Change in Noncommercial-Long (All)", "Change in Noncommercial-Short (All)"


def gval(r, k):
    v = r.get(k, "").replace(",", "").strip()
    if v in ("", "."):
        return None
    try:
        return int(v)
    except ValueError:
        return None


def load_chain(names):
    out = {}
    for y in YEARS:
        fn = "fo2026.zip" if y == 2026 else f"hist_{y}.zip"
        p = os.path.join(TMP, fn)
        if not os.path.exists(p):
            continue
        with zipfile.ZipFile(p) as z:
            raw = z.read(z.namelist()[0]).decode("utf-8", "replace")
        for r in csv.DictReader(io.StringIO(raw)):
            nm = r["Market and Exchange Names"].strip()
            if nm not in names or nm in EXCLUDE:
                continue
            d = r["As of Date in Form YYYY-MM-DD"].strip()
            if d in out:
                continue
            out[d] = dict(date=d, nc_l=gval(r, C_L), nc_s=gval(r, C_S), nc_sp=gval(r, C_SP),
                          c_l=gval(r, C_CL), c_s=gval(r, C_CS), oi=gval(r, C_OI),
                          lchg=gval(r, CH_L), schg=gval(r, CH_S))
    return out


def load_sum():
    chains = {}
    for label, names in FAMILY[:3]:
        chains[label] = load_chain(set(names))
    dates = sorted({d for c in chains.values() for d in c})
    out = {}
    for d in dates:
        acc = {}
        for c in chains.values():
            r = c.get(d)
            if not r:
                continue
            for k in ["nc_l", "nc_s", "nc_sp", "c_l", "c_s", "oi"]:
                if r.get(k) is not None:
                    acc[k] = acc.get(k, 0) + r[k]
        if "nc_l" in acc:
            acc["date"], acc["lchg"], acc["schg"] = d, None, None
            out[d] = acc
    return out


def weekly(by_date):
    """返回 [{date, dl(多头变), ds(空头变), net(净), dnet(净变), level_*}] 按日期升序"""
    sdates = sorted(by_date)
    rows = []
    prev = None
    for d in sdates:
        r = by_date[d]
        l, s, sp = r["nc_l"], r["nc_s"], r["nc_sp"]
        net = None if (l is None or s is None) else l - s
        dl, ds = r.get("lchg"), r.get("schg")
        if prev:
            if dl is None and l is not None and prev["nc_l"] is not None:
                dl = l - prev["nc_l"]
            if ds is None and s is not None and prev["nc_s"] is not None:
                ds = s - prev["nc_s"]
        dnet = None
        if prev and net is not None:
            pn = prev.get("net")
            if pn is not None:
                dnet = net - pn
        rows.append(dict(date=d, dl=dl, ds=ds, net=net, dnet=dnet,
                         l_after=l, s_after=s, prev_l=prev["nc_l"] if prev else None,
                         prev_s=prev["nc_s"] if prev else None,
                         prev_net=prev.get("net") if prev else None))
        prev = dict(nc_l=l, nc_s=s, net=net)
    return rows


def topk(rows, key, n=20, reverse=True):
    """取前 n；key 为每行 dict 的字段名"""
    vals = [r for r in rows if r.get(key) is not None]
    vals.sort(key=lambda r: r[key], reverse=reverse)
    return vals[:n]


def main():
    result = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "families": {}}
    for label, names in FAMILY:
        by_date = load_sum() if names is None else load_chain(set(names))
        if not by_date:
            print("!! 无数据:", label)
            continue
        rows = weekly(by_date)
        fam = {
            "start": rows[0]["date"], "end": rows[-1]["date"], "n": len(rows),
            "long_up": topk(rows, "dl"),      # 多头增仓
            "short_cut": topk(rows, "ds", reverse=False),  # 空头砍仓（减得最多）
            "net_up": topk(rows, "dnet"),     # 净多增加
            "asof": rows[-1]["date"],
        }
        result["families"][label] = fam
        # 打印校验
        print(f"\n=== {label} ({fam['start']} ~ {fam['end']}, {len(rows)}周) ===")
        print(" 多头TOP3:", [(r['date'], r['dl']) for r in fam['long_up'][:3]])
        print(" 空头砍TOP3:", [(r['date'], r['ds']) for r in fam['short_cut'][:3]])
        print(" 净多TOP3:", [(r['date'], r['dnet']) for r in fam['net_up'][:3]])

    with open(os.path.join(OUT, "wheat_weekly_top20_20260901.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    # CSV：长表
    with open(os.path.join(OUT, "wheat_weekly_top20_20260901.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["family", "rank_type", "rank", "date", "chg", "level_after", "prev_level", "net_after"])
        for label, fam in result["families"].items():
            def emit(typ, items, key):
                for i, r in enumerate(items, 1):
                    w.writerow([label, typ, i, r["date"], r[key],
                                {"dl": "l_after", "ds": "s_after", "dnet": "net"}[key] and {"dl": r["l_after"], "ds": r["s_after"], "dnet": r["net"]}[key],
                                {"dl": r["prev_l"], "ds": r["prev_s"], "dnet": r["prev_net"]}[key],
                                r["net"]])
            emit("多头增仓", fam["long_up"], "dl")
            emit("空头砍仓", fam["short_cut"], "ds")
            emit("净多增加", fam["net_up"], "dnet")
    print("\nsaved", "wheat_weekly_top20_20260901.json/csv", "familes:", len(result["families"]))


if __name__ == "__main__":
    main()