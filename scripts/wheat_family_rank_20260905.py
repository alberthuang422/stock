# -*- coding: utf-8 -*-
"""
小麦家族全品种排名（futures-only legacy 口径）
覆盖：当前活跃 3 链（SRW/HRW/HRS）+ 退市小麦（黑海金融小麦/白麦/杜伦麦）+ 三合约合计
输出：results/cot/wheat_family_rank_<asof>.csv / .json
口径：周变动优先取 CFTC 官方 Change 列（缺失用连续周 diff）
"""
import csv, io, json, os, zipfile
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(BASE, "Temp", "cot")
OUT = os.path.join(BASE, "results", "cot")
os.makedirs(OUT, exist_ok=True)
YEARS = list(range(1995, 2027))

# 小麦家族：展示名 -> [市场名链（时间正序）]
FAMILY = [
    ("小麦 SRW 软红冬 (CBOT)", [
        "WHEAT - CBT WHEAT",
        "WHEAT - CHICAGO BOARD OF TRADE",
        "WHEAT-SRW - CHICAGO BOARD OF TRADE"]),
    ("小麦 HRW 硬红冬 (CBOT)", [
        "WHEAT - KCBT WHEAT",
        "WHEAT - KANSAS CITY BOARD OF TRADE",
        "WHEAT-HRW - CHICAGO BOARD OF TRADE"]),
    ("小麦 HRS 硬红春 (MIAX)", [
        "WHEAT - MGE WHEAT",
        "WHEAT - MINNEAPOLIS GRAIN EXCHANGE",
        "WHEAT-HRSpring - MINNEAPOLIS GRAIN EXCHANGE",
        "WHEAT-HRSpring - MIAX FUTURES EXCHANGE"]),
    ("小麦 三合约合计 (SRW+HRW+HRS)", None),  # 合成
    ("黑海小麦金融 (CBOT, 已停)", [
        "BLACK SEA WHEAT FINANCIAL - CHICAGO BOARD OF TRADE"]),
    ("白小麦 (MGE, 已退市)", [
        "WHITE WHEAT - MGE WHITE WHEAT",
        "WHITE WHEAT - MINNEAPOLIS GRAIN EXCHANGE"]),
    ("硬质杜伦麦 (MGE, 已退市)", [
        "HARD AMBER DURUM WHEAT - MINNEAPOLIS GRAIN EXCHANGE"]),
]
EXCLUDE = {"WHEAT -SRW CONSECUTIVE CSO - CHICAGO BOARD OF TRADE",  # 价差期权非持仓
           "WHEAT - MIDAMERICA COMMODITY EXCHANGE"}               # 迷你合约，仅 1 年

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


def load_market(names):
    """返回 {date: dict}, 链内市场名同名日期去重（取首个非空）"""
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
            rec = dict(date=d,
                       nc_l=gval(r, C_L), nc_s=gval(r, C_S), nc_sp=gval(r, C_SP),
                       c_l=gval(r, C_CL), c_s=gval(r, C_CS), oi=gval(r, C_OI),
                       nc_l_chg=gval(r, CH_L), nc_s_chg=gval(r, CH_S))
            if d in out:  # 去重：保留已有（优先级按链顺序）
                continue
            out[d] = rec
    return out


def load_wheat_sum():
    """三合约合计：SRW/HRW/HRS 链同日期加总"""
    chains = {}
    for label, names in FAMILY[:3]:
        chains[label] = load_market(set(names))
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
            acc["date"] = d
            acc["nc_l_chg"], acc["nc_s_chg"] = None, None
            out[d] = acc
    return out


def stats(by_date):
    if not by_date:
        return None
    sdates = sorted(by_date)
    cur, pv = by_date[sdates[-1]], by_date[sdates[-2]] if len(sdates) > 1 else None
    p4 = by_date[sdates[-5]] if len(sdates) >= 5 else None
    nets = []
    for d in sdates:
        r = by_date[d]
        if r["nc_l"] is not None and r["nc_s"] is not None:
            nets.append((r["nc_l"] - r["nc_s"], d))
    nets.sort()
    cur_net = None if (cur["nc_l"] is None or cur["nc_s"] is None) else cur["nc_l"] - cur["nc_s"]
    def chg(k, base):
        if cur.get(k) is not None:
            return cur[k]
        if base and cur.get(k) is None and base.get(k) is not None and cur.get(k) is not None:
            return cur[k] - base[k]
        # diff 兜底
        kcols = {"nc_l_chg": "nc_l", "nc_s_chg": "nc_s"}
        col = kcols.get(k)
        if col and base and cur.get(col) is not None and base.get(col) is not None:
            return cur[col] - base[col]
        return None
    net_chg_1w = None
    if pv and cur_net is not None:
        pv_net = None if (pv["nc_l"] is None or pv["nc_s"] is None) else pv["nc_l"] - pv["nc_s"]
        if pv_net is not None:
            net_chg_1w = cur_net - pv_net
    net_chg_4w = None
    if p4 and cur_net is not None:
        p4n = None if (p4["nc_l"] is None or p4["nc_s"] is None) else p4["nc_l"] - p4["nc_s"]
        if p4n is not None:
            net_chg_4w = cur_net - p4n
    return dict(
        name="", start=sdates[0], end=sdates[-1], n=len(sdates),
        oi=cur["oi"], nc_l=cur["nc_l"], nc_s=cur["nc_s"], nc_sp=cur["nc_sp"],
        nc_l_chg1=chg("nc_l_chg", pv), nc_s_chg1=chg("nc_s_chg", pv),
        nc_l_chg4=None, nc_s_chg4=None,
        nc_net=cur_net, nc_net_chg1=net_chg_1w, nc_net_chg4=net_chg_4w,
        c_l=cur["c_l"], c_s=cur["c_s"], c_net=None if (cur["c_l"] is None or cur["c_s"] is None) else cur["c_l"] - cur["c_s"],
        hist_max=nets[-1][0] if nets else None, hist_max_d=nets[-1][1] if nets else None,
        hist_min=nets[0][0] if nets else None, hist_min_d=nets[0][1] if nets else None,
    )


def main():
    rows = []
    for label, names in FAMILY:
        if names is None:
            by_date = load_wheat_sum()
        else:
            by_date = load_market(set(names))
        st = stats(by_date)
        if not st:
            print("!! 无数据:", label)
            continue
        st["name"] = label
        rows.append(st)
    asof = max(r["end"] for r in rows)

    # 4 周变动（用序列重算，避免官方 Change 缺失）
    for label, names in FAMILY[:3]:
        pass
    # 用已存长表补 4 周（此处简单：读历史 json 系列）
    try:
        hist = json.load(open(os.path.join(OUT, "agri_cot_history_1995_2026.json"), encoding="utf-8"))
        s = hist["series"]
        for r in rows:
            ss = s.get(r["name"])
            if not ss or len(ss["nc_net"]) < 5:
                continue
            n = ss["nc_net"]
            if n[-1] is not None and n[-5] is not None:
                r["nc_net_chg4"] = n[-1] - n[-5]
            if ss.get("nc_l") and ss["nc_l"][-1] is not None and ss["nc_l"][-5] is not None:
                r["nc_l_chg4"] = ss["nc_l"][-1] - ss["nc_l"][-5]
            if ss.get("nc_s") and ss["nc_s"][-1] is not None and ss["nc_s"][-5] is not None:
                r["nc_s_chg4"] = ss["nc_s"][-1] - ss["nc_s"][-5]
    except Exception as e:
        print("4周补充失败(不影响主榜):", e)

    cols = ["name", "start", "end", "n", "oi", "nc_l", "nc_l_chg1", "nc_l_chg4",
            "nc_s", "nc_s_chg1", "nc_s_chg4", "nc_net", "nc_net_chg1", "nc_net_chg4",
            "c_net", "hist_max", "hist_max_d", "hist_min", "hist_min_d"]
    with open(os.path.join(OUT, f"wheat_family_rank_{asof.replace('-','')}.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    out = dict(asof=asof, generated=datetime.now().strftime("%Y-%m-%d %H:%M"), rows=rows)
    with open(os.path.join(OUT, f"wheat_family_rank_{asof.replace('-','')}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"asof={asof} 品种数={len(rows)}\n")
    hdr = f"{'品种':<26}{'截止':<12}{'周数':>5}{'非商多':>9}{'多变1w':>9}{'非商空':>9}{'空变1w':>9}{'净多':>9}{'净变1w':>9}{'净变4w':>9}"
    print(hdr)
    for r in sorted(rows, key=lambda x: -x["nc_net_chg1"] if x["nc_net_chg1"] is not None else 1e9):
        f = lambda v: "" if v is None else f"{v:+,}"
        print(f"{r['name']:<24}{r['end']:<12}{r['n']:>5}{f(r['nc_l']):>9}{f(r['nc_l_chg1']):>9}{f(r['nc_s']):>9}{f(r['nc_s_chg1']):>9}{f(r['nc_net']):>9}{f(r['nc_net_chg1']):>9}{f(r['nc_net_chg4']):>9}")


if __name__ == "__main__":
    main()