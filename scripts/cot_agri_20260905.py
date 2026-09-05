# -*- coding: utf-8 -*-
"""
CFTC COT 农产品持仓分析（futures-only legacy 口径 + disaggregated 交叉验证）
数据源：CFTC 官方历史压缩文件 deahistfoYYYY.zip / fut_disagg_txt_YYYY.zip
输出：results/cot/agri_cot_<asof>.json  /  .csv
"""
import csv, io, json, os, zipfile, sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(BASE, "Temp", "cot")
OUT = os.path.join(BASE, "results", "cot")
os.makedirs(OUT, exist_ok=True)

YEARS = list(range(2010, 2027))  # futures-only 数据自 2010 年起下载（各品种实际起始见 nall）

# 市场名别名（交易所更名/合约改制时保持同一序列）
# HRS：Minneapolis Grain Exchange 于 2024-11 起更名为 MIAX Futures Exchange，合约本身不变
ALIAS = {
    "WHEAT-HRSpring - MIAX FUTURES EXCHANGE": [
        "WHEAT-HRSpring - MINNEAPOLIS GRAIN EXCHANGE",
        "WHEAT-HRSpring - MIAX FUTURES EXCHANGE",
    ],
}

# ---- 目标市场（futures-only legacy）：(分组, 展示名, 市场名精确匹配, commodity code)
TARGETS = [
    ("谷物", "小麦 SRW (CBOT)", "WHEAT-SRW - CHICAGO BOARD OF TRADE", "001"),
    ("谷物", "小麦 HRW (CBOT)", "WHEAT-HRW - CHICAGO BOARD OF TRADE", "001"),
    ("谷物", "小麦 HRS (MIAX)", "WHEAT-HRSpring - MIAX FUTURES EXCHANGE", "001"),
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
    ("软商品", "冷冻浓缩橙汁 (ICE)", "FRZN CONCENTRATED ORANGE JUICE - ICE FUTURES U.S.", "040"),
    ("畜牧", "活牛 (CME)", "LIVE CATTLE - CHICAGO MERCANTILE EXCHANGE", "057"),
    ("畜牧", "育肥牛 (CME)", "FEEDER CATTLE - CHICAGO MERCANTILE EXCHANGE", "061"),
    ("畜牧", "瘦肉猪 (CME)", "LEAN HOGS - CHICAGO MERCANTILE EXCHANGE", "054"),
    ("乳品", "三级牛奶 (CME)", "MILK, Class III - CHICAGO MERCANTILE EXCHANGE", "052"),
    ("乳品", "黄油 (CME)", "BUTTER (CASH SETTLED) - CHICAGO MERCANTILE EXCHANGE", "050"),
    ("乳品", "奶酪 (CME)", "CHEESE (CASH-SETTLED) - CHICAGO MERCANTILE EXCHANGE", "063"),
    ("乳品", "乳清粉 (CME)", "DRY WHEY - CHICAGO MERCANTILE EXCHANGE", "063"),
    ("乳品", "脱脂奶粉 (CME)", "NON FAT DRY MILK - CHICAGO MERCANTILE EXCHANGE", "052"),
]
NAME2META = {t[2]: t for t in TARGETS}

# 小麦三合约可加总（同为 5,000 蒲式耳/张）
WHEAT = ["WHEAT-SRW - CHICAGO BOARD OF TRADE",
         "WHEAT-HRW - CHICAGO BOARD OF TRADE",
         "WHEAT-HRSpring - MIAX FUTURES EXCHANGE"]


def load_legacy():
    """返回 {(market, date): dict}；market 一律用规范名（TARGETS 第 3 项）"""
    canon = {}
    for mk in NAME2META:
        for nm in ALIAS.get(mk, [mk]):
            canon[nm] = mk
    data = {}
    for y in YEARS:
        p = os.path.join(TMP, "fo2026.zip" if y == 2026 else f"hist_{y}.zip")
        if not os.path.exists(p):
            continue
        with zipfile.ZipFile(p) as z:
            raw = z.read("annualof.txt").decode("utf-8", "replace")
        for r in csv.DictReader(io.StringIO(raw)):
            nm = canon.get(r["Market and Exchange Names"].strip())
            if nm is None:
                continue
            d = r["As of Date in Form YYYY-MM-DD"].strip()
            def g(k):
                v = r.get(k, "").replace(",", "").strip()
                return int(v) if v not in ("", ".") else None
            oi = g("Open Interest (All)")
            nc_l = g("Noncommercial Positions-Long (All)")
            nc_s = g("Noncommercial Positions-Short (All)")
            nc_sp = g("Noncommercial Positions-Spreading (All)")
            c_l = g("Commercial Positions-Long (All)")
            c_s = g("Commercial Positions-Short (All)")
            nr_l = g("Nonreportable Positions-Long (All)")
            nr_s = g("Nonreportable Positions-Short (All)")
            data[(nm, d)] = dict(date=d, market=nm, oi=oi,
                                 nc_l=nc_l, nc_s=nc_s, nc_sp=nc_sp,
                                 c_l=c_l, c_s=c_s, nr_l=nr_l, nr_s=nr_s,
                                 nc_net=None if (nc_l is None or nc_s is None) else nc_l - nc_s,
                                 c_net=None if (c_l is None or c_s is None) else c_l - c_s,
                                 nr_net=None if (nr_l is None or nr_s is None) else nr_l - nr_s)
    return data


def load_disagg():
    """disaggregated 补充：Managed Money 净头寸（futures-only）"""
    out = {}
    for y in YEARS:
        p = os.path.join(TMP, "disagg2026.zip" if y == 2026 else f"disagg_{y}.zip")
        if not os.path.exists(p):
            continue
        with zipfile.ZipFile(p) as z:
            nm = [i.filename for i in z.infolist() if i.filename.endswith(".txt")][0]
            raw = z.read(nm).decode("utf-8", "replace")
        for r in csv.DictReader(io.StringIO(raw)):
            mk = r["Market_and_Exchange_Names"].strip()
            if mk not in NAME2META:
                continue
            d = r["Report_Date_as_YYYY-MM-DD"].strip()
            def g(k):
                v = r.get(k, "").replace(",", "").strip()
                return int(v) if v not in ("", ".") else None
            mm_l, mm_s = g("M_Money_Positions_Long_All"), g("M_Money_Positions_Short_All")
            pm_l, pm_s = g("Prod_Merc_Positions_Long_All"), g("Prod_Merc_Positions_Short_All")
            out[(mk, d)] = dict(
                mm_net=None if (mm_l is None or mm_s is None) else mm_l - mm_s,
                mm_l=mm_l, mm_s=mm_s,
                pm_net=None if (pm_l is None or pm_s is None) else pm_l - pm_s)
    return out


def pctile(series, val):
    if val is None or not series:
        return None
    s = [x for x in series if x is not None]
    if not s:
        return None
    return round(100.0 * sum(1 for x in s if x <= val) / len(s), 1)


def main():
    legacy = load_legacy()
    dis = load_disagg()
    all_dates = sorted({k[1] for k in legacy})
    asof = all_dates[-1]
    prev = all_dates[-2]
    prev4 = all_dates[-5] if len(all_dates) >= 5 else all_dates[0]
    print("asof", asof, "prev", prev, "n_dates", len(all_dates))

    rows = []
    for grp, label, mk, code in TARGETS:
        cur = legacy.get((mk, asof))
        if not cur:
            print("!! missing", mk, asof)
            continue
        pv = legacy.get((mk, prev), {})
        p4 = legacy.get((mk, prev4), {})
        hist_net = [legacy[(mk, d)]["nc_net"] for (m2, d) in legacy if m2 == mk]
        hist_net.sort()
        # 3年 / 5年 窗口
        d3 = [d for d in all_dates if d >= "2023-09-01"]
        d5 = [d for d in all_dates if d >= "2021-09-01"]
        h3 = [legacy[(mk, d)]["nc_net"] for d in d3 if (mk, d) in legacy]
        h5 = [legacy[(mk, d)]["nc_net"] for d in d5 if (mk, d) in legacy]
        dm = dis.get((mk, asof), {})
        dm_pv = dis.get((mk, prev), {})
        oi = cur["oi"]

        def chg(a, b):
            return None if (a is None or b is None) else a - b
        rows.append(dict(
            group=grp, name=label, market=mk, code=code,
            oi=oi, oi_chg=chg(oi, pv.get("oi")), oi_chg4=chg(oi, p4.get("oi")),
            nc_l=cur["nc_l"], nc_s=cur["nc_s"], nc_sp=cur["nc_sp"],
            nc_net=cur["nc_net"], nc_net_chg=chg(cur["nc_net"], pv.get("nc_net")),
            nc_net_chg4=chg(cur["nc_net"], p4.get("nc_net")),
            nc_l_chg=chg(cur["nc_l"], pv.get("nc_l")), nc_s_chg=chg(cur["nc_s"], pv.get("nc_s")),
            c_l=cur["c_l"], c_s=cur["c_s"], c_net=cur["c_net"],
            c_net_chg=chg(cur["c_net"], pv.get("c_net")),
            nr_l=cur["nr_l"], nr_s=cur["nr_s"], nr_net=cur["nr_net"],
            nr_net_chg=chg(cur["nr_net"], pv.get("nr_net")),
            nc_l_pct=round(100.0 * cur["nc_l"] / oi, 1) if oi and cur["nc_l"] is not None else None,
            nc_s_pct=round(100.0 * cur["nc_s"] / oi, 1) if oi and cur["nc_s"] is not None else None,
            nc_net_pct=round(100.0 * cur["nc_net"] / oi, 1) if oi and cur["nc_net"] is not None else None,
            nc_ls=round(cur["nc_l"] / cur["nc_s"], 2) if cur["nc_s"] else None,
            pct_all=pctile(hist_net, cur["nc_net"]),
            pct_3y=pctile(h3, cur["nc_net"]),
            pct_5y=pctile(h5, cur["nc_net"]),
            n3=len(h3), n5=len(h5), nall=len(hist_net),
            hist_min=min(hist_net) if hist_net else None,
            hist_max=max(hist_net) if hist_net else None,
            mm_net=dm.get("mm_net"), mm_net_chg=chg(dm.get("mm_net"), dm_pv.get("mm_net")),
            pm_net=dm.get("pm_net"), pm_net_chg=chg(dm.get("pm_net"), dm_pv.get("pm_net")),
        ))

    # 小麦三合约合计
    def agg(mks, date, keys):
        tot = {}
        for mk in mks:
            r = legacy.get((mk, date))
            if not r:
                continue
            for k in keys:
                if r.get(k) is not None:
                    tot[k] = tot.get(k, 0) + r[k]
        return tot

    keys = ["oi", "nc_l", "nc_s", "nc_sp", "c_l", "c_s", "nr_l", "nr_s", "nc_net", "c_net", "nr_net"]
    wc, wp, wp4 = agg(WHEAT, asof, keys), agg(WHEAT, prev, keys), agg(WHEAT, prev4, keys)
    if wc:
        hnet = []
        for d in all_dates:
            a = agg(WHEAT, d, keys)
            if a.get("nc_net") is not None:
                hnet.append(a["nc_net"])
        h3 = []
        for d in d3:
            a = agg(WHEAT, d, keys)
            if a.get("nc_net") is not None:
                h3.append(a["nc_net"])
        rows.insert(3, dict(
            group="谷物", name="小麦 三合约合计", market="WHEAT (SRW+HRW+HRS)", code="001",
            oi=wc.get("oi"), oi_chg=wc.get("oi", 0) - wp.get("oi", 0) if wp.get("oi") else None,
            oi_chg4=wc.get("oi", 0) - wp4.get("oi", 0) if wp4.get("oi") else None,
            nc_l=wc.get("nc_l"), nc_s=wc.get("nc_s"), nc_sp=wc.get("nc_sp"),
            nc_net=wc.get("nc_net"),
            nc_net_chg=wc.get("nc_net", 0) - wp.get("nc_net", 0) if wp.get("nc_net") is not None else None,
            nc_net_chg4=wc.get("nc_net", 0) - wp4.get("nc_net", 0) if wp4.get("nc_net") is not None else None,
            nc_l_chg=wc.get("nc_l", 0) - wp.get("nc_l", 0) if wp.get("nc_l") is not None else None,
            nc_s_chg=wc.get("nc_s", 0) - wp.get("nc_s", 0) if wp.get("nc_s") is not None else None,
            c_l=wc.get("c_l"), c_s=wc.get("c_s"), c_net=wc.get("c_net"),
            c_net_chg=wc.get("c_net", 0) - wp.get("c_net", 0) if wp.get("c_net") is not None else None,
            nr_l=wc.get("nr_l"), nr_s=wc.get("nr_s"), nr_net=wc.get("nr_net"),
            nr_net_chg=wc.get("nr_net", 0) - wp.get("nr_net", 0) if wp.get("nr_net") is not None else None,
            nc_l_pct=round(100.0 * wc["nc_l"] / wc["oi"], 1) if wc.get("oi") and wc.get("nc_l") is not None else None,
            nc_s_pct=round(100.0 * wc["nc_s"] / wc["oi"], 1) if wc.get("oi") and wc.get("nc_s") is not None else None,
            nc_net_pct=round(100.0 * wc["nc_net"] / wc["oi"], 1) if wc.get("oi") and wc.get("nc_net") is not None else None,
            nc_ls=round(wc["nc_l"] / wc["nc_s"], 2) if wc.get("nc_s") else None,
            pct_all=pctile(hnet, wc.get("nc_net")), pct_3y=pctile(h3, wc.get("nc_net")), pct_5y=None,
            n3=len(h3), n5=0, nall=len(hnet),
            hist_min=min(hnet) if hnet else None, hist_max=max(hnet) if hnet else None,
            mm_net=None, mm_net_chg=None, pm_net=None, pm_net_chg=None,
        ))

    # 历史序列（近 156 周）供绘图
    series = {}
    win = all_dates[-156:]
    for grp, label, mk, code in TARGETS + [("谷物", "小麦 三合约合计", "WHEAT (SRW+HRW+HRS)", "001")]:
        if mk == "WHEAT (SRW+HRW+HRS)":
            vals = []
            for d in win:
                a = agg(WHEAT, d, keys)
                vals.append(a.get("nc_net"))
        else:
            vals = [legacy[(mk, d)]["nc_net"] if (mk, d) in legacy else None for d in win]
        series[label] = dict(dates=win, net=vals,
                             oi=[legacy[(mk, d)]["oi"] if (mk, d) in legacy else None for d in win])

    out = dict(asof=asof, prev=prev, prev4=prev4,
               generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
               source="CFTC COT futures-only (deahistfo) + disaggregated (fut_disagg_txt)",
               rows=rows, series=series)
    with open(os.path.join(OUT, f"agri_cot_{asof.replace('-','')}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # CSV
    cols = ["group", "name", "oi", "oi_chg", "nc_l", "nc_s", "nc_sp", "nc_net", "nc_net_chg",
            "nc_l_chg", "nc_s_chg", "nc_l_pct", "nc_s_pct", "nc_net_pct", "nc_ls",
            "c_l", "c_s", "c_net", "c_net_chg", "nr_l", "nr_s", "nr_net", "nr_net_chg",
            "pct_3y", "pct_5y", "hist_min", "hist_max", "mm_net", "mm_net_chg", "pm_net", "pm_net_chg"]
    with open(os.path.join(OUT, f"agri_cot_{asof.replace('-','')}.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("rows", len(rows), "->", os.path.join(OUT, f"agri_cot_{asof.replace('-','')}.json"))


if __name__ == "__main__":
    main()
