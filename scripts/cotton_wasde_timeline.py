#!/usr/bin/env python3
"""提取 2026 年各月 WASDE 中美棉 + 全球棉花的供需预测，构建 2026/27 预期时间线。

来源：
- 2026-01~04, 07~09: usda.gov 月度快照 CSV
- 2026-05, 06: NAL ESMIS 存档 xls（usda.gov 该两月 CSV 缺失）
"""
import csv, glob
import xlrd

BASE = "/Users/alberthuang/Desktop/股票分析/data/cotton/wasde_2026"

# ---------- 1) CSV 月度快照 ----------
def parse_csv(path):
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["Commodity"] == "Cotton" and row["Region"] in (
                "United States", "World", "China", "Brazil", "India"):
                out.append(row)
    return out

csv_rows = []
for m in ["2026-01", "2026-02", "2026-03", "2026-04", "2026-07", "2026-08", "2026-09"]:
    csv_rows += parse_csv(f"{BASE}/oce-wasde-report-data-{m}.csv")

# ---------- 2) xls（5/6 月）----------
XL_ATTRS = {
    "Planted": "Planted Area", "Harvested": "Harvested Area",
    "Yield per Harvested Acre": "Yield",
    "Beginning Stocks": "Beginning Stocks", "Production": "Production",
    "Imports": "Imports", "Supply, Total": "Total Supply",
    "Domestic Use": "Domestic Use", "Exports, Total": "Exports",
    "Use, Total": "Total Use", "Ending Stocks": "Ending Stocks",
    "Avg. Farm Price 3/": "Avg Farm Price",
}

def parse_xls(path):
    wb = xlrd.open_workbook(path)
    rows = []
    # 美棉 Page 17（US），世界棉 Page 26；先动态找
    pages = {}
    for p in range(8, 38):
        sh = wb.sheet_by_name(f"Page {p}")
        for r in range(min(8, sh.nrows)):
            v = str(sh.cell_value(r, 0))
            if "U.S. Cotton Supply and Use" in v:
                pages["United States"] = f"Page {p}"
            elif "World Cotton Supply and Use" in v and "United States" not in str(sh.cell_value(r, 0)):
                pages.setdefault("World", f"Page {p}")
    for region, sheet in pages.items():
        sh = wb.sheet_by_name(sheet)
        # 找表头行：含年份列标签
        years = {}
        for r in range(sh.nrows):
            for c in range(sh.ncols):
                v = str(sh.cell_value(r, c)).strip()
                if "2025/26" in v:
                    years[c] = "2025/26"
                elif "2026/27" in v:
                    years[c] = "2026/27"
            if years:
                hdr_r = r
        # 数据行
        for r in range(sh.nrows):
            label = str(sh.cell_value(r, 0)).strip()
            if label in XL_ATTRS:
                for c, yr in years.items():
                    v = str(sh.cell_value(r, c)).strip().replace("**", "").replace("*", "")
                    if v and v != "NA":
                        rows.append({"Region": region, "Attribute": XL_ATTRS[label],
                                     "MarketYear": yr, "Value": v,
                                     "ReportDate": "May 2026" if "0526" in path else "June 2026"})
        break  # years dict 是全 sheet 共享的，US 表即可
    return rows

xls_rows = parse_xls(f"{BASE}/wasde0526.xls") + parse_xls(f"{BASE}/wasde0626.xls")

# ---------- 3) 汇总成时间线 ----------
US_ATTRS = ["Planted Area", "Harvested Area", "Yield", "Production",
            "Exports", "Domestic Use", "Ending Stocks"]

# CSV 的单位与 xls 不同（千包/磅），只取美棉关键行
from collections import defaultdict
timeline = defaultdict(dict)  # (report, year) -> {attr: value}

for r in csv_rows:
    if r["Region"] != "United States":
        continue
    attr = r["Attribute"]
    if attr not in US_ATTRS:
        continue
    v = r["Value"]
    u = r["Unit"]
    timeline[(r["ReportDate"], r["MarketYear"])][attr] = f"{v} ({u.split(',')[0].strip()})"

for r in xls_rows:
    if r["Region"] != "United States" or r["Attribute"] not in US_ATTRS:
        continue
    timeline[(r["ReportDate"], r["MarketYear"])][r["Attribute"]] = r["Value"]

order = ["January 2026", "February 2026", "March 2026", "April 2026",
         "May 2026", "June 2026", "July 2026", "August 2026", "September 2026"]

print("=" * 110)
print("美棉（United States Cotton）WASDE 逐月预测时间线")
print("=" * 110)
for yr in ["2025/26", "2026/27"]:
    print(f"\n### 市场年度 {yr}  (棉花年度 8月-次年7月)")
    hdr = f"{'报告月份':<16}" + "".join(f"{a:<22}" for a in US_ATTRS)
    print(hdr)
    for rep in order:
        d = timeline.get((rep, yr))
        if not d:
            continue
        line = f"{rep:<16}"
        for a in US_ATTRS:
            line += f"{d.get(a, '—'):<22}"
        print(line)

# 世界棉花产量/期末库存
print("\n" + "=" * 110)
print("全球棉花（World Cotton）WASDE 逐月：产量 / 期末库存 / 库消比相关")
print("=" * 110)
for rep in order:
    for yr in ["2025/26", "2026/27"]:
        vals = {}
        for r in csv_rows:
            if r["ReportDate"] == rep and r["Region"] == "World" and r["MarketYear"] == yr:
                if r["Attribute"] in ("Production", "Ending Stocks", "Domestic Use"):
                    vals[r["Attribute"]] = r["Value"] + " " + r["Unit"].split(",")[0]
        if vals:
            print(f"{rep:<16} {yr:<9} " + " | ".join(f"{k}={v}" for k, v in vals.items()))

# xls 中的世界棉花
for r in xls_rows:
    if r["Region"] == "World" and r["Attribute"] in ("Production", "Ending Stocks", "Domestic Use"):
        print(f"{r['ReportDate']:<16} {r['MarketYear']:<9} {r['Attribute']}={r['Value']} (M 480lb bales)")
