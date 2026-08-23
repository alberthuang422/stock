# -*- coding: utf-8 -*-
"""解析 3 批期权行情落盘文件 -> 按行权价聚合 OI -> 期权墙 + Max Pain -> results/option_walls_20260918.json"""
import json, re

TR = r"C:\Users\Administrator\.workbuddy\projects\c-Users-Administrator-Desktop-stock\ab20c1e2-c116-4fea-b6d5-226da7ee4e63\tool-results"
FILES = [
    f"{TR}\\mcp-connector-proxy-futu-mcp_quote_stock_quote-1787392425674-e1d8c4.txt",
    f"{TR}\\mcp-connector-proxy-futu-mcp_quote_stock_quote-1787392598018-61013d.txt",
    f"{TR}\\mcp-connector-proxy-futu-mcp_quote_stock_quote-1787392666052-7f1e9b.txt",
]

TICKERS = ["ABBV","GILD","LLY","JNJ","KO","SBUX","CSCO","AMZN"]

# 合约 code -> strike/type 映射（来自 chain 文件）
meta = {}
for tk in TICKERS:
    for r in json.load(open(rf"C:\Users\Administrator\Desktop\stock\results\chain_{tk}_20260918.json")):
        meta[r["code"]] = (tk, float(r["strike"]), r["type"])

quotes = {}
for f in FILES:
    d = json.load(open(f, encoding="utf-8"))
    for s in d["data"]["quote_list"]:
        oe = s.get("option_ex_data") or {}
        quotes[s["code"]] = {
            "oi": int(oe.get("open_interest") or 0),
            "vol": int(s.get("volume") or 0),
            "last": s.get("last_price"),
            "iv": oe.get("implied_volatility"),
            "delta": oe.get("delta"),
        }

print(f"parsed contracts: {len(quotes)} / expected 1074; matched meta: {sum(1 for c in quotes if c in meta)}")

result = {}
for tk in TICKERS:
    strikes = {}
    for code, q in quotes.items():
        m = re.match(rf"^US\.{tk}(\d{{6}})([CP])(\d+)$", code)
        if not m:
            continue
        k = int(m.group(3)) / 1000.0
        typ = m.group(2)
        strikes.setdefault(k, {"call_oi": 0, "put_oi": 0, "call_vol": 0, "put_vol": 0,
                               "call_iv": None, "put_iv": None})
        key = "call" if typ == "C" else "put"
        strikes[k][f"{key}_oi"] += q["oi"]
        strikes[k][f"{key}_vol"] += q["vol"]
        if q["iv"] is not None:
            strikes[k][f"{key}_iv"] = round(q["iv"], 1)
    ks = sorted(strikes)

    # Max Pain：到期价为 S 时，卖方总赔付 = ΣcallOI*max(0,S-K) + ΣputOI*max(0,K-S)，取最小值
    payouts = []
    for S in ks:
        pay = sum(c["call_oi"] * max(0.0, S - K) + c["put_oi"] * max(0.0, K - S)
                  for K, c in ((K2, strikes[K2]) for K2 in ks))
        payouts.append((S, pay))
    max_pain = min(payouts, key=lambda x: x[1])[0]

    wall_call_k = max(ks, key=lambda k: strikes[k]["call_oi"])
    wall_put_k = max(ks, key=lambda k: strikes[k]["put_oi"])
    tot_c = sum(c["call_oi"] for c in strikes.values())
    tot_p = sum(c["put_oi"] for c in strikes.values())

    result[tk] = {
        "strikes": [{"strike": k, **strikes[k]} for k in ks],
        "wall_call_strike": wall_call_k, "wall_call_oi": strikes[wall_call_k]["call_oi"],
        "wall_put_strike": wall_put_k, "wall_put_oi": strikes[wall_put_k]["put_oi"],
        "max_pain": max_pain,
        "total_call_oi": tot_c, "total_put_oi": tot_p,
        "pcr_oi": round(tot_p / tot_c, 3) if tot_c else None,
    }
    print(f"{tk}: strikes={len(ks)} CallWall={wall_call_k}({strikes[wall_call_k]['call_oi']}) "
          f"PutWall={wall_put_k}({strikes[wall_put_k]['put_oi']}) MaxPain={max_pain} "
          f"PCR={tot_p/tot_c:.2f}")

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, float) and o != o: return None
    return o

json.dump(clean(result), open(r"C:\Users\Administrator\Desktop\stock\results\option_walls_20260918.json", "w"), indent=1, ensure_ascii=False)
print("written: results/option_walls_20260918.json")
