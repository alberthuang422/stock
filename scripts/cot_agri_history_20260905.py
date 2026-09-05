# -*- coding: utf-8 -*-
"""
CFTC COT 农产品持仓全历史分析（1995–2026，futures-only legacy 口径）
数据源：CFTC 官方历史压缩 deahistfo_1995~2003.zip（AnnualOF*.txt）+ deahistfo2004~2026.zip（annualof.txt）
输出：results/cot/agri_cot_history_1995_2026.json / .csv（全序列）+ 最新周快照

字段口径（全部为 "All" = 全合约口径，单位：张）：
  nc_l 非商业多头 / nc_s 非商业空头 / nc_sp 非商业套利
  c_l  商业多头   / c_s  商业空头
  nr_l 非报告多头 / nr_s 非报告空头
  nc_net 非商业净头寸 = nc_l - nc_s（净多头；负值即净空）
  官方周变动：nc_l_chg / nc_s_chg / c_l_chg / c_s_chg 优先取 CFTC 官方 Change 列，缺失时用自身 diff
"""
import csv, io, json, os, zipfile
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(BASE, "Temp", "cot")
OUT = os.path.join(BASE, "results", "cot")
os.makedirs(OUT, exist_ok=True)

YEARS = list(range(1995, 2027))

# ---------------- 市场名链：规范名 -> 全部历史实际名（按时间顺序） ----------------
# 交易所更名 / 合约口径调整时保持同一序列；首元素为最新名（含 "Contract Units" 语义一致）
ALIAS = {
    "WHEAT-SRW - CHICAGO BOARD OF TRADE": [
        "WHEAT-SRW - CHICAGO BOARD OF TRADE",                       # 2013-12 起（SRW 独立口径）
        "WHEAT - CHICAGO BOARD OF TRADE",                            # 1995-2013（CBOT 统合小麦）
        "WHEAT - CBT WHEAT",                                         # 1995-03~04（CBOT 简写）
    ],
    "WHEAT-HRW - CHICAGO BOARD OF TRADE": [
        "WHEAT-HRW - CHICAGO BOARD OF TRADE",                        # 2013-12 起
        "WHEAT - KANSAS CITY BOARD OF TRADE",                        # 1995-2013（KCBT 硬红冬麦）
        "WHEAT - KCBT WHEAT",
    ],
    "WHEAT-HRSpring - MIAX FUTURES EXCHANGE": [
        "WHEAT-HRSpring - MIAX FUTURES EXCHANGE",                    # 2024-11 起（MGE 更名 MIAX）
        "WHEAT-HRSpring - MINNEAPOLIS GRAIN EXCHANGE",               # 2014-03 起
        "WHEAT - MINNEAPOLIS GRAIN EXCHANGE",                        # 1995-2014（MGE 统合）
        "WHEAT - MGE WHEAT",
    ],
    "CORN - CHICAGO BOARD OF TRADE": [
        "CORN - CHICAGO BOARD OF TRADE", "CORN - CBT CORN"],
    "OATS - CHICAGO BOARD OF TRADE": [
        "OATS - CHICAGO BOARD OF TRADE", "OATS - CBT OATS"],
    "ROUGH RICE - CHICAGO BOARD OF TRADE": [
        "ROUGH RICE - CHICAGO BOARD OF TRADE", "ROUGH RICE - CBT ROUGH RICE"],
    "SOYBEANS - CHICAGO BOARD OF TRADE": [
        "SOYBEANS - CHICAGO BOARD OF TRADE", "SOYBEANS - CBT SOYBEANS"],
    "SOYBEAN OIL - CHICAGO BOARD OF TRADE": [
        "SOYBEAN OIL - CHICAGO BOARD OF TRADE", "SOYBEAN OIL - CBT SOYBEAN OIL"],
    "SOYBEAN MEAL - CHICAGO BOARD OF TRADE": [
        "SOYBEAN MEAL - CHICAGO BOARD OF TRADE", "SOYBEAN MEAL - CBT SOYBEAN MEAL"],
    "CANOLA - ICE FUTURES U.S.": ["CANOLA - ICE FUTURES U.S."],      # 2018 起（无更早记录）
    "COTTON NO. 2 - ICE FUTURES U.S.": [
        "COTTON NO. 2 - ICE FUTURES U.S.",                           # 2007 起
        "COTTON NO. 2 - NEW YORK BOARD OF TRADE",                    # 2005-2007
        "COTTON NO. 2 - NEW YORK COTTON EXCHANGE",                   # 1995-2004
        "COTTON NO. 2 - NYCE COTTON NO. 2"],
    "COCOA - ICE FUTURES U.S.": [
        "COCOA - ICE FUTURES U.S.", "COCOA - NEW YORK BOARD OF TRADE",
        "COCOA - COFFEE, SUGAR AND COCOA EXCHANGE", "COCOA - COFFEE,SUGAR AND COCOA EXCHANGE",
        "COCOA - COFFEE,SUGAR AND COCOA EXCHANG", "COCOA - COFFEE, SUGAR & COCOA EXCHANGE",
        "COCOA - CSCE COCOA"],
    "SUGAR NO. 11 - ICE FUTURES U.S.": [
        "SUGAR NO. 11 - ICE FUTURES U.S.", "SUGAR NO. 11 - NEW YORK BOARD OF TRADE",
        "SUGAR NO. 11 - COFFEE, SUGAR AND COCOA EXCHANGE", "SUGAR NO. 11 - COFFEE,SUGAR AND COCOA EXCHANGE",
        "SUGAR NO. 11 - COFFEE,SUGAR AND COCOA EXCHANG", "SUGAR NO. 11 - COFFEE, SUGAR & COCOA EXCHANGE",
        "SUGAR NO. 11 - CSCE SUGAR NO. 11"],
    "COFFEE C - ICE FUTURES U.S.": [
        "COFFEE C - ICE FUTURES U.S.", "COFFEE C - NEW YORK BOARD OF TRADE",
        "COFFEE C - COFFEE, SUGAR AND COCOA EXCHANGE", "COFFEE C - COFFEE,SUGAR AND COCOA EXCHANGE",
        "COFFEE C - COFFEE,SUGAR AND COCOA EXCHANG", "COFFEE C - COFFEE, SUGAR & COCOA EXCHANGE",
        "COFFEE C - CSCE COFFEE C"],
    "FRZN CONCENTRATED ORANGE JUICE - ICE FUTURES U.S.": [
        "FRZN CONCENTRATED ORANGE JUICE - ICE FUTURES U.S.",
        "FRZN CONCENTRATED ORANGE JUICE - NEW YORK BOARD OF TRADE",
        "FRZN CONCENTRATED ORANGE JUICE - NEW YORK COTTON EXCHANGE",
        "FRZN CONCENTRATED ORANGE JUICE - CITRUS ASSOC. OF NY COTTON EXCH",
        "FRZN CONCENTRATED ORANGE JUICE - CITRUS ASSOC. OF NY COTTON EXC",
        "FRZN CONCENTRATED ORANGE JUICE - CITRUS ASSOC. OF N Y COTTON EXCH INC",
        "FRZN CONCENTRATED ORANGE JUICE - CANY ORANGE JUICE"],
    "LIVE CATTLE - CHICAGO MERCANTILE EXCHANGE": [
        "LIVE CATTLE - CHICAGO MERCANTILE EXCHANGE", "LIVE CATTLE - CME LIVE CATTLE"],
    "FEEDER CATTLE - CHICAGO MERCANTILE EXCHANGE": [
        "FEEDER CATTLE - CHICAGO MERCANTILE EXCHANGE", "FEEDER CATTLE - CME FEEDER CATTLE"],
    "LEAN HOGS - CHICAGO MERCANTILE EXCHANGE": ["LEAN HOGS - CHICAGO MERCANTILE EXCHANGE"],  # 1996 起
    "MILK, Class III - CHICAGO MERCANTILE EXCHANGE": [
        "MILK, Class III - CHICAGO MERCANTILE EXCHANGE",             # 2007 起
        "MILK - CHICAGO MERCANTILE EXCHANGE"],                       # 1997-2007
    "BUTTER (CASH SETTLED) - CHICAGO MERCANTILE EXCHANGE": [
        "BUTTER (CASH SETTLED) - CHICAGO MERCANTILE EXCHANGE"],      # 2006 起（现金结算新版）
    "CHEESE (CASH-SETTLED) - CHICAGO MERCANTILE EXCHANGE": [
        "CHEESE (CASH-SETTLED) - CHICAGO MERCANTILE EXCHANGE"],      # 2012 起
    "DRY WHEY - CHICAGO MERCANTILE EXCHANGE": [
        "DRY WHEY - CHICAGO MERCANTILE EXCHANGE"],                   # 2012 起
    "NON FAT DRY MILK - CHICAGO MERCANTILE EXCHANGE": [
        "NON FAT DRY MILK - CHICAGO MERCANTILE EXCHANGE"],           # 2013 起
}

# 目标市场（规范名）：(分组, 展示名, 规范名, CFTC 商品码)
TARGETS = [
    ("谷物", "小麦 SRW (CBOT)", "WHEAT-SRW - CHICAGO BOARD OF TRADE", "001"),
    ("谷物", "小麦 HRW (KCBT→CBOT)", "WHEAT-HRW - CHICAGO BOARD OF TRADE", "001"),
    ("谷物", "小麦 HRS (MGE→MIAX)", "WHEAT-HRSpring - MIAX FUTURES EXCHANGE", "001"),
    ("谷物", "玉米 (CBOT)", "CORN - CHICAGO BOARD OF TRADE", "002"),
    ("谷物", "燕麦 (CBOT)", "OATS - CHICAGO BOARD OF TRADE", "004"),
    ("谷物", "糙米 (CBOT)", "ROUGH RICE - CHICAGO BOARD OF TRADE", "039"),
    ("油籽", "大豆 (CBOT)", "SOYBEANS - CHICAGO BOARD OF TRADE", "005"),
    ("油籽", "豆油 (CBOT)", "SOYBEAN OIL - CHICAGO BOARD OF TRADE", "007"),
    ("油籽", "豆粕 (CBOT)", "SOYBEAN MEAL - CHICAGO BOARD OF TRADE", "026"),
    ("油籽", "油菜籽 (ICE)", "CANOLA - ICE FUTURES U.S.", "135"),
    ("软商品", "棉花 2号 (ICE)", "COTTON NO. 2 - ICE FUTURES U.S.", "033"),
    ("软商品", "可可 (ICE)", "COCOA - ICE FUTURES U.S.", "073"),
    ("软商品", "糖 11号 (ICE)", "SUGAR NO. 11 - ICE FUTURES U.S.", "080"),
    ("软商品", "咖啡 C (ICE)", "COFFEE C - ICE FUTURES U.S.", "083"),
    ("软商品", "冻橙汁 (ICE)", "FRZN CONCENTRATED ORANGE JUICE - ICE FUTURES U.S.", "040"),
    ("畜牧", "活牛 (CME)", "LIVE CATTLE - CHICAGO MERCANTILE EXCHANGE", "057"),
    ("畜牧", "育肥牛 (CME)", "FEEDER CATTLE - CHICAGO MERCANTILE EXCHANGE", "061"),
    ("畜牧", "瘦肉猪 (CME)", "LEAN HOGS - CHICAGO MERCANTILE EXCHANGE", "054"),
    ("乳品", "三级牛奶 (CME)", "MILK, Class III - CHICAGO MERCANTILE EXCHANGE", "052"),
    ("乳品", "黄油 (CME)", "BUTTER (CASH SETTLED) - CHICAGO MERCANTILE EXCHANGE", "050"),
    ("乳品", "奶酪 (CME)", "CHEESE (CASH-SETTLED) - CHICAGO MERCANTILE EXCHANGE", "063"),
    ("乳品", "乳清粉 (CME)", "DRY WHEY - CHICAGO MERCANTILE EXCHANGE", "063"),
    ("乳品", "脱脂奶粉 (CME)", "NON FAT DRY MILK - CHICAGO MERCANTILE EXCHANGE", "052"),
]
CANON2NAME = {t[2]: t for t in TARGETS}

# 小麦三合约合计（同为 5,000 蒲式耳/张）
WHEAT = "WHEAT (SRW+HRW+HRS)"

# 旧→新名映射
def build_canon():
    canon = {}
    for canon_name, names in ALIAS.items():
        for nm in names:
            canon[nm] = canon_name
    return canon

CANON = build_canon()

COL_L = "Noncommercial Positions-Long (All)"
COL_S = "Noncommercial Positions-Short (All)"
COL_SP = "Noncommercial Positions-Spreading (All)"
COL_CL = "Commercial Positions-Long (All)"
COL_CS = "Commercial Positions-Short (All)"
COL_NL = "Nonreportable Positions-Long (All)"
COL_NS = "Nonreportable Positions-Short (All)"
COL_OI = "Open Interest (All)"
CH_L = "Change in Noncommercial-Long (All)"
CH_S = "Change in Noncommercial-Short (All)"
CH_CL = "Change in Commercial-Long (All)"
CH_CS = "Change in Commercial-Short (All)"


def gval(r, k):
    v = r.get(k, "").replace(",", "").strip()
    if v in ("", "."):
        return None
    try:
        return int(v)
    except ValueError:
        return None


def load_all():
    """返回 {canon_name: {date_str: dict}} 全字段 dict"""
    data = {cn: {} for cn in CANON2NAME}
    for y in YEARS:
        fn = "fo2026.zip" if y == 2026 else f"hist_{y}.zip"
        p = os.path.join(TMP, fn)
        if not os.path.exists(p):
            print("!! 缺失 zip:", fn)
            continue
        with zipfile.ZipFile(p) as z:
            raw = z.read(z.namelist()[0]).decode("utf-8", "replace")
        n = 0
        for r in csv.DictReader(io.StringIO(raw)):
            nm_raw = r["Market and Exchange Names"].strip()
            cn = CANON.get(nm_raw)
            if cn is None or cn not in data:
                continue
            d = r["As of Date in Form YYYY-MM-DD"].strip()
            rec = dict(
                date=d, oi=gval(r, COL_OI),
                nc_l=gval(r, COL_L), nc_s=gval(r, COL_S), nc_sp=gval(r, COL_SP),
                c_l=gval(r, COL_CL), c_s=gval(r, COL_CS),
                nr_l=gval(r, COL_NL), nr_s=gval(r, COL_NS),
                nc_l_chg=gval(r, CH_L), nc_s_chg=gval(r, CH_S),
                c_l_chg=gval(r, CH_CL), c_s_chg=gval(r, CH_CS),
            )
            # 同 (market,date) 重复行保护（老文件可能存在）
            old = data[cn].get(d)
            if old is not None and all(old.get(k) is not None for k in ("nc_l", "c_l")):
                continue
            data[cn][d] = rec
            n += 1
        print(f"{y}: {fn} 目标市场行数 {n}")
    return data


def fill_stats(data):
    """净头寸、官方变动缺值时回退 diff、%OI"""
    for cn, by_date in data.items():
        sdates = sorted(by_date)
        prev = None
        for d in sdates:
            rec = by_date[d]
            nc_l, nc_s, c_l, c_s = rec["nc_l"], rec["nc_s"], rec["c_l"], rec["c_s"]
            rec["nc_net"] = None if (nc_l is None or nc_s is None) else nc_l - nc_s
            rec["c_net"] = None if (c_l is None or c_s is None) else c_l - c_s
            oi = rec["oi"]
            rec["nc_l_pct"] = round(100.0 * nc_l / oi, 1) if (oi and nc_l is not None) else None
            rec["nc_s_pct"] = round(100.0 * nc_s / oi, 1) if (oi and nc_s is not None) else None
            # 变动回退
            if prev is not None:
                for k, pk in [("nc_l_chg", "nc_l"), ("nc_s_chg", "nc_s"),
                              ("c_l_chg", "c_l"), ("c_s_chg", "c_s")]:
                    if rec.get(k) is None and rec.get(pk) is not None and prev.get(pk) is not None:
                        rec[k] = rec[pk] - prev[pk]
            prev = rec


def agg_wheat(by_dates, keys):
    tot = {}
    for cn in [t[2] for t in TARGETS if t[1].startswith("小麦")]:
        r = by_dates.get(cn)
        if not r:
            continue
        for k in keys:
            if r.get(k) is not None:
                tot[k] = tot.get(k, 0) + r[k]
    return tot


def main():
    data = load_all()
    fill_stats(data)

    all_dates = sorted({d for cn in data for d in data[cn]})
    asof = all_dates[-1]
    print("asof", asof, "n_dates", len(all_dates))

    KEYS = ["oi", "nc_l", "nc_s", "nc_sp", "c_l", "c_s", "nr_l", "nr_s",
            "nc_net", "c_net", "nc_l_chg", "nc_s_chg", "c_l_chg", "c_s_chg"]

    # ---- 每品种序列 + 快照 ----
    series = {}
    rows = []
    for grp, label, cn, code in TARGETS:
        by_date = data[cn]
        sdates = sorted(by_date)
        if not sdates:
            continue
        cur = by_date[asof]
        pv = None
        hist = {k: [] for k in KEYS}
        for d in sdates:
            rec = by_date[d]
            for k in KEYS:
                if rec.get(k) is not None:
                    hist[k].append(rec[k])
        # 快照：变动用官方（当前周列），与上一周 diff 相比取官方
        idx = sdates.index(asof)
        pv = by_date[sdates[idx - 1]] if idx > 0 else None
        def diff(k):
            if cur.get(k) is not None:
                return cur[k]
            if pv and cur.get(k) is not None and pv.get(k) is not None:
                return cur[k] - pv[k]
            return None
        rows.append(dict(
            group=grp, name=label, market=cn, code=code,
            asof=asof, start=sdates[0], end=sdates[-1], n=len(sdates),
            oi=cur["oi"], nc_l=cur["nc_l"], nc_s=cur["nc_s"],
            nc_l_chg=diff("nc_l_chg"), nc_s_chg=diff("nc_s_chg"),
            c_l=cur["c_l"], c_s=cur["c_s"], c_l_chg=diff("c_l_chg"), c_s_chg=diff("c_s_chg"),
            c_net=cur["c_net"],
            nc_net=cur["nc_net"], nc_short=None if cur["nc_net"] is None else -cur["nc_net"],
            nc_net_chg=diff("nc_net"),  # net 无官方列，用自身 diff
            nc_l_pct=cur["nc_l_pct"], nc_s_pct=cur["nc_s_pct"],
            hist_max_net=max(hist["nc_net"]) if hist["nc_net"] else None,
            hist_min_net=min(hist["nc_net"]) if hist["nc_net"] else None,
            hist_max_net_date=None, hist_min_net_date=None,
        ))
        # 极值日期
        nmax, nmin = max(hist["nc_net"]) if hist["nc_net"] else None, min(hist["nc_net"]) if hist["nc_net"] else None
        if nmax is not None:
            rows[-1]["hist_max_net_date"] = next(d for d in sdates if by_date[d]["nc_net"] == nmax)
        if nmin is not None:
            rows[-1]["hist_min_net_date"] = next(d for d in sdates if by_date[d]["nc_net"] == nmin)

        series[label] = dict(dates=sdates, start=sdates[0], end=sdates[-1], n=len(sdates))
        for k in KEYS + ["nc_net", "c_net"]:
            series[label][k] = [by_date[d].get(k) for d in sdates]

    # ---- 小麦三合约合计 ----
    sw = sorted(data["WHEAT-SRW - CHICAGO BOARD OF TRADE"])
    sd = []  # 三合约齐全的日期（并集）
    sd = sorted({d for cn in [t[2] for t in TARGETS if t[1].startswith("小麦")] for d in data[cn]})
    sdates = sd
    hist = {k: [] for k in KEYS}
    for d in sdates:
        a = agg_wheat({t[2]: data[t[2]].get(d) for t in TARGETS if t[1].startswith("小麦")}, KEYS)
        for k in KEYS:
            if a.get(k) is not None:
                hist[k].append(a[k])
    cur = agg_wheat({t[2]: data[t[2]].get(asof) for t in TARGETS if t[1].startswith("小麦")}, KEYS)
    idx = len(sdates) - 1
    pv = agg_wheat({t[2]: data[t[2]].get(sdates[idx-1]) for t in TARGETS if t[1].startswith("小麦")}, KEYS) if idx > 0 else {}
    def wdiff(k, v, pc):
        if v is None: return None
        return v - pc if (pc is not None and v is not None) else None
    rows2 = dict(
        group="谷物", name="小麦 三合约合计", market=WHEAT, code="001",
        asof=asof, start=sdates[0], end=sdates[-1], n=len(sdates),
        oi=cur.get("oi"), nc_l=cur.get("nc_l"), nc_s=cur.get("nc_s"),
        nc_l_chg=wdiff("nc_l_chg", cur.get("nc_l"), pv.get("nc_l")) if cur.get("nc_l_chg") is None else cur.get("nc_l_chg"),
        nc_s_chg=wdiff("nc_s_chg", cur.get("nc_s"), pv.get("nc_s")) if cur.get("nc_s_chg") is None else cur.get("nc_s_chg"),
        c_l=cur.get("c_l"), c_s=cur.get("c_s"),
        c_l_chg=wdiff("c_l_chg", cur.get("c_l"), pv.get("c_l")) if cur.get("c_l_chg") is None else cur.get("c_l_chg"),
        c_s_chg=wdiff("c_s_chg", cur.get("c_s"), pv.get("c_s")) if cur.get("c_s_chg") is None else cur.get("c_s_chg"),
        c_net=cur.get("c_net"),
        nc_net=cur.get("nc_net"), nc_short=None if cur.get("nc_net") is None else -cur["nc_net"],
        nc_net_chg=wdiff("nc_net", cur.get("nc_net"), pv.get("nc_net")),
        nc_l_pct=round(100.0 * cur["nc_l"] / cur["oi"], 1) if cur.get("oi") and cur.get("nc_l") is not None else None,
        nc_s_pct=round(100.0 * cur["nc_s"] / cur["oi"], 1) if cur.get("oi") and cur.get("nc_s") is not None else None,
        hist_max_net=max(hist["nc_net"]) if hist["nc_net"] else None,
        hist_min_net=min(hist["nc_net"]) if hist["nc_net"] else None,
        hist_max_net_date=next((d for d in sdates if agg_wheat({t[2]: data[t[2]].get(d) for t in TARGETS if t[1].startswith("小麦")}, KEYS).get("nc_net") == max(hist["nc_net"])), None) if hist["nc_net"] else None,
        hist_min_net_date=next((d for d in sdates if agg_wheat({t[2]: data[t[2]].get(d) for t in TARGETS if t[1].startswith("小麦")}, KEYS).get("nc_net") == min(hist["nc_net"])), None) if hist["nc_net"] else None,
    )
    rows.append(rows2)
    s_wh = {"dates": sdates, "start": sdates[0], "end": sdates[-1], "n": len(sdates)}
    for k in KEYS + ["nc_net", "c_net"]:
        s_wh[k] = [agg_wheat({t[2]: data[t[2]].get(d) for t in TARGETS if t[1].startswith("小麦")}, KEYS).get(k) for d in sdates]
    series["小麦 三合约合计"] = s_wh

    out = dict(
        asof=asof, generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        years_covered="1995-03-21 ~ " + asof,
        source="CFTC COT futures-only legacy (deahistfo_1995~2003 + deahistfo2004~2026)",
        n_dates=len(all_dates), rows=rows, series=series,
    )
    with open(os.path.join(OUT, "agri_cot_history_1995_2026.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---- CSV：长表（每品种每日期一行）----
    cols = ["market", "date"] + KEYS
    with open(os.path.join(OUT, "agri_cot_history_1995_2026.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for label, s in series.items():
            for i, d in enumerate(s["dates"]):
                row = [label, d] + [s[k][i] for k in KEYS]
                w.writerow(row)

    # ---- 快照 CSV（最新周，用户核心视角）----
    scol = ["group", "name", "start", "n", "oi", "nc_l", "nc_l_chg", "nc_s", "nc_s_chg",
            "c_l", "c_l_chg", "c_s", "c_s_chg", "nc_net", "nc_net_chg", "nc_short",
            "nc_l_pct", "nc_s_pct", "hist_max_net", "hist_max_net_date", "hist_min_net", "hist_min_net_date"]
    with open(os.path.join(OUT, f"agri_cot_snapshot_{asof.replace('-','')}.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=scol, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("done: rows", len(rows), "| series", len(series))


if __name__ == "__main__":
    main()