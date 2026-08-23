import json

files = [
    r"C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-Desktop-stock/a3df5bb9-bf1b-4408-a366-f33d83b51d4d/tool-results/mcp-connector-proxy-futu-mcp_quote_stock_quote-1787385896117-e418ac.txt",
    r"C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-Desktop-stock/a3df5bb9-bf1b-4408-a366-f33d83b51d4d/tool-results/mcp-connector-proxy-futu-mcp_quote_stock_quote-1787385896002-c6a40d.txt",
]
rows = []
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    for q in d["data"]["quote_list"]:
        code = q["code"]
        if not code.startswith("US.SBUX26"):
            continue
        od = q.get("option_ex_data") or {}
        rows.append({
            "code": code,
            "strike": od.get("strike_price"),
            "otype": od.get("option_type"),
            "oi": od.get("open_interest"),
            "volume": q.get("volume"),
            "last": q.get("last_price"),
            "iv": od.get("implied_volatility"),
        })

print(f"total rows: {len(rows)}")
print(f"{'code':<24}{'strike':>6}{'type':>5}{'oi':>7}{'vol':>7}{'last':>8}{'iv':>7}")
for r in sorted(rows, key=lambda x: (x["code"][9:15], x["strike"] or 0, x["otype"])):
    print(f"{r['code']:<24}{r['strike']:>6}{r['otype']:>5}{r['oi']:>7}{r['volume']:>7}{r['last']:>8}{r['iv']:>7}")

json.dump(rows, open("C:/Users/Administrator/Desktop/stock/results/sbux_opt_rows.json","w"), indent=1)
print("saved -> results/sbux_opt_rows.json")
