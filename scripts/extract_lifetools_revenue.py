#!/usr/bin/env python3
"""从富途落盘的财报 JSON 提取四家生命科学工具龙头（A/WAT/DHR/TMO）季度营收序列。

输入：C:/Users/Administrator/.workbuddy/projects/.../tool-results/ 下的 mcp-connector-proxy-futu-mcp_quote_financials_statements-*.txt
      （按调用顺序对应 A/WAT/DHR/TMO，每个含 50 期）
输出：results/lifetools_revenue.json —— 各公司单季度营收（百万美元）+ YoY + 年度营收
"""
import json, glob, os

TR = r"C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-Desktop-stock/176282ed-7381-4c31-99d4-f55a48bc5dd5/tool-results"
OUT = r"C:/Users/Administrator/Desktop/stock/results"
TICKERS = ["A", "WAT", "DHR", "TMO"]

def load_json_from_txt(p):
    raw = open(p, encoding="utf-8").read()
    i, j = raw.find("{"), raw.rfind("}")
    return json.loads(raw[i:j+1])

files = sorted(glob.glob(os.path.join(TR, "mcp-connector-proxy-futu-mcp_quote_financials_statements-*.txt")))
assert len(files) >= 4, f"需 4 个文件，实际 {len(files)}"

result = {}
for tk, f in zip(TICKERS, files[:4]):
    d = load_json_from_txt(f)
    reports = d["data"]["report_list"]
    quarters, annuals = [], []
    for rp in reports:
        ft = rp["financial_type"]
        rev = rp["item_list"][0]["data"] / 1e6
        yoy = rp["item_list"][0].get("yoy")
        rec = {
            "period": rp["period_text"],
            "fy": rp.get("fiscal_year"),
            "rev_m": round(rev, 1),
            "yoy": round(yoy, 1) if yoy is not None else None,
        }
        if ft in (1, 2, 3, 4):
            quarters.append(rec)
        elif ft == 7:
            annuals.append(rec)
    quarters.sort(key=lambda x: x["period"])
    annuals.sort(key=lambda x: x["period"])
    result[tk] = {"quarters": quarters, "annuals": annuals}

os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "lifetools_revenue.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("saved:", path)
for tk in TICKERS:
    q = result[tk]["quarters"]
    print(f"\n=== {tk} 季度数={len(q)} 范围={q[0]['period']}~{q[-1]['period']} ===")
    for rec in q:
        print(f"  {rec['period']}: rev={rec['rev_m']} yoy={rec['yoy']}")