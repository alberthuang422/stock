# -*- coding: utf-8 -*-
"""拉取 KMI（CIK 0001506307）SEC XBRL 财务核心指标
companyconcept API → 输出 results/kmi_xbrl.json
口径：us-gaap 标准 tag，年度=财年（KMI 财年=自然年），单季度从 10-Q 提取
"""
import urllib.request
import json
import os
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "results", "kmi_xbrl.json")

CIK = "CIK0001506307"
UA = {"User-Agent": "Research research@example.com"}

# tag → 中文名
TAGS = {
    "Revenues": "营收",
    "OperatingIncomeLoss": "营业利润",
    "NetIncomeLoss": "净利润",
    "NetIncomeLossAvailableToCommonStockholdersBasic": "普通股净利",
    "NetCashProvidedByUsedInOperatingActivities": "经营现金流",
    "PaymentsToAcquirePropertyPlantAndEquipment": "资本开支",
    "CommonStockDividendsPerShareDeclared": "每股股息(宣告)",
    "PaymentsOfDividendsCommonStock": "普通股股息支付",
    "LongTermDebtNoncurrent": "长期债务(非流动)",
    "LongTermDebtCurrent": "长期债务(流动)",
    "LinesOfCreditCurrent": "循环额度(流动)",
    "StockholdersEquity": "股东权益",
    "Assets": "总资产",
    "DepreciationDepletionAndAmortization": "折旧摊销",
    "InterestExpense": "利息费用",
    "CommonStockSharesOutstanding": "流通股数",
    "WeightedAverageNumberOfDilutedSharesOutstanding": "摊薄股数",
}


def get(tag):
    url = f"https://data.sec.gov/api/xbrl/companyconcept/{CIK}/us-gaap/{tag}.json"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(1)  # 校验不是假 200
            if raw != b"{":
                print(f"  {tag}: NOT JSON (假 200)")
                return None
            r.close()
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  {tag}: {str(e)[:80]}")
        return None


out = {}
for tag, cn in TAGS.items():
    d = get(tag)
    time.sleep(0.25)
    if not d:
        out[tag] = {"cn": cn, "error": "fetch failed"}
        continue
    units = d.get("units", {})
    # 优先 USD，其次 USD/shares
    usd = units.get("USD") or units.get("USD/shares") or units.get("shares")
    rows = usd if usd else []
    # 年度序列：取 FY 且 form 10-K
    years = {}
    quarters = []
    for r in rows:
        fy = r.get("fy")
        fp = r.get("fp")
        form = r.get("form", "")
        val = r.get("val")
        end = r.get("end")
        start = r.get("start")
        if fy is None or val is None:
            continue
        if fp == "FY":
            # 保留每财年最后一次报告
            years[fy] = {"end": end, "val": val, "form": form}
        elif fp in ("Q1", "Q2", "Q3", "Q4") and form in ("10-Q", "10-K"):
            quarters.append({"fy": fy, "fp": fp, "end": end, "start": start, "val": val, "form": form})
    # 去重季度（同 end 保留最后一次）
    qseen = {}
    for q in quarters:
        qseen[q["end"]] = q
    out[tag] = {
        "cn": cn,
        "years": {str(k): v for k, v in sorted(years.items())},
        "quarters": sorted(qseen.values(), key=lambda x: x["end"]),
    }
    print(f"ok {tag}: {len(years)} 年度, {len(qseen)} 季度")

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved ->", OUT)