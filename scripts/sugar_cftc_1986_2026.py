# -*- coding: utf-8 -*-
"""
白糖 SUGAR NO. 11 全历史 CFTC 持仓序列（Futures-Only legacy 口径，1986 至今）

数据源：CFTC 官方 Futures-Only (deacot) 历史压缩包
  - deacot1986_2016.zip (FUT86_16.txt)  1986-01-15 ~ 2016-12-27
  - deacotYYYY.zip       (annual.txt)    2017 ~ 2026
口径说明：
  - 这是【纯期货】(Futures Only) 口径，不含期权；CFTC legacy 报告的 (All) 列自 1986 起全程统一。
  - 1986-09~1992-09 过渡期存在 Old/Other 两套细分，(All) = Old + Other，本序列一律取 (All)。
  - 频率：1986-1991 半月（每年 24 期，月中+月末）、1992 过渡（31 期）、1993 起周度（52 期）。
  - 交易所更名链（同一合约）：CSCE(1986-2004) → NYBOT(2005-2007) → ICE US(2007-)，无缝衔接。
字段（单位：张，contracts）：
  oi 未平仓 / nc_l 非商业多头 / nc_s 非商业空头 / nc_sp 非商业套利
  c_l 商业多头 / c_s 商业空头 / nr_l 非报告多头 / nr_s 非报告空头
  nc_net = nc_l - nc_s（非商业净头寸，正=净多，负=净空）
  c_net = c_l - c_s / nr_net = nr_l - nr_s
  *_chg 周变动（优先官方 Change 列，缺失回退自身 diff）
"""
import csv, io, json, os, zipfile
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEACOT = os.path.join(BASE, "Temp", "cot", "deacot")
OUT = os.path.join(BASE, "data", "sugar")
os.makedirs(OUT, exist_ok=True)

# 白糖 NO.11 市场名沿革（deacot 文件中的精确写法）
SUGAR_NAMES = [
    "SUGAR NO. 11 - COFFEE, SUGAR & COCOA EXCHANGE",      # 1986-1999 (CSCE)
    "SUGAR NO. 11 - COFFEE,COCOA AND SUGAR EXCHANG",       # 1999-2000
    "SUGAR NO. 11 - COFFEE,SUGAR AND COCOA EXCHANG",       # 2000-2002
    "SUGAR NO. 11 - COFFEE,SUGAR AND COCOA EXCHANGE",      # 2002-2003
    "SUGAR NO. 11 - COFFEE, SUGAR AND COCOA EXCHANGE",     # 2003-2004
    "SUGAR NO. 11 - NEW YORK BOARD OF TRADE",              # 2005-2007 (NYBOT)
    "SUGAR NO. 11 - ICE FUTURES U.S.",                     # 2007-      (ICE US)
]
NAME_SET = set(SUGAR_NAMES)

# 核心字段（读取时对 key 做 strip，兼容老文件前导空格）
KEYS = {
    "oi": "Open Interest (All)",
    "nc_l": "Noncommercial Positions-Long (All)",
    "nc_s": "Noncommercial Positions-Short (All)",
    "nc_sp": "Noncommercial Positions-Spreading (All)",
    "c_l": "Commercial Positions-Long (All)",
    "c_s": "Commercial Positions-Short (All)",
    "nr_l": "Nonreportable Positions-Long (All)",
    "nr_s": "Nonreportable Positions-Short (All)",
    "nc_l_chg": "Change in Noncommercial-Long (All)",
    "nc_s_chg": "Change in Noncommercial-Short (All)",
    "c_l_chg": "Change in Commercial-Long (All)",
    "c_s_chg": "Change in Commercial-Short (All)",
}


def gval(r, field):
    v = r.get(field, "").replace(",", "").strip()
    if v in ("", "."):
        return None
    try:
        return int(v)
    except ValueError:
        return None


def load_zip(path):
    """读取 zip 内 txt，返回按 strip 后 key 的 dict 行列表"""
    with zipfile.ZipFile(path) as z:
        raw = z.read(z.namelist()[0]).decode("utf-8", "replace")
    rows = []
    for r in csv.DictReader(io.StringIO(raw)):
        rr = {k.strip(): v for k, v in r.items()}
        if rr.get("Market and Exchange Names", "").strip() not in NAME_SET:
            continue
        rows.append(rr)
    return rows


def main():
    by_date = {}
    # 1) 1986-2016 完整包
    p = os.path.join(DEACOT, "deacot1986_2016.zip")
    if os.path.exists(p):
        for r in load_zip(p):
            d = r["As of Date in Form YYYY-MM-DD"].strip()
            rec = {k: gval(r, f) for k, f in KEYS.items()}
            rec["date"] = d
            by_date[d] = rec
    # 2) 2017-2026 逐年
    for y in range(2017, 2027):
        p = os.path.join(DEACOT, f"deacot{y}.zip")
        if not os.path.exists(p):
            print("!! 缺失:", f"deacot{y}.zip")
            continue
        for r in load_zip(p):
            d = r["As of Date in Form YYYY-MM-DD"].strip()
            rec = {k: gval(r, f) for k, f in KEYS.items()}
            rec["date"] = d
            by_date[d] = rec

    dates = sorted(by_date)
    print("白糖序列:", dates[0], "~", dates[-1], "共", len(dates), "期")

    # 3) 衍生字段 + 变动回退
    prev = None
    for d in dates:
        rec = by_date[d]
        for ln, sh, net in [("nc_l", "nc_s", "nc_net"), ("c_l", "c_s", "c_net"), ("nr_l", "nr_s", "nr_net")]:
            rec[net] = None if (rec[ln] is None or rec[sh] is None) else rec[ln] - rec[sh]
        # 官方变动缺失回退 diff
        if prev is not None:
            for k, pk in [("nc_l_chg", "nc_l"), ("nc_s_chg", "nc_s"), ("c_l_chg", "c_l"), ("c_s_chg", "c_s")]:
                if rec.get(k) is None and rec.get(pk) is not None and prev.get(pk) is not None:
                    rec[k] = rec[pk] - prev[pk]
        prev = rec

    COLS = ["date", "oi", "nc_l", "nc_s", "nc_sp", "c_l", "c_s", "nr_l", "nr_s",
            "nc_net", "c_net", "nr_net", "nc_l_chg", "nc_s_chg", "c_l_chg", "c_s_chg"]

    # 4) 输出 CSV
    csv_path = os.path.join(OUT, "sugar_cftc_futonly_1986_2026.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for d in dates:
            w.writerow([by_date[d].get(c) for c in COLS])

    # 5) 输出 JSON（含元信息 + 序列）
    json_path = os.path.join(OUT, "sugar_cftc_futonly_1986_2026.json")
    series = {c: [by_date[d].get(c) for d in dates] for c in COLS}
    meta = dict(
        market="SUGAR NO. 11 (World Raw Sugar, ICE Futures U.S.)",
        cftc_code="080",
        report="Futures-Only (legacy, deacot)",
        unit="contracts (112,000 lbs each)",
        start=dates[0], end=dates[-1], n=len(dates),
        freq="1986-1991 半月 / 1992 过渡 / 1993- 周度",
        exchange_chain="CSCE(1986-2004) -> NYBOT(2005-2007) -> ICE US(2007-)",
        note="(All) 列总口径，不含期权；1986-1992 过渡期 Old+Other 合并即 All",
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        columns=COLS,
    )
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dict(meta=meta, dates=dates, series=series), f, ensure_ascii=False)

    print("CSV ->", csv_path)
    print("JSON ->", json_path)
    # 最新一期
    last = by_date[dates[-1]]
    print("最新:", last)


if __name__ == "__main__":
    main()
