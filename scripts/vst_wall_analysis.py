import json

files = [
    r"C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-Desktop-stock/a3df5bb9-bf1b-4408-a366-f33d83b51d4d/tool-results/mcp-connector-proxy-futu-mcp_quote_stock_quote-1787390002445-e07a78.txt",
    r"C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-Desktop-stock/a3df5bb9-bf1b-4408-a366-f33d83b51d4d/tool-results/mcp-connector-proxy-futu-mcp_quote_stock_quote-1787390012824-0b5e4e.txt",
]
rows = []
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    for q in d["data"]["quote_list"]:
        code = q["code"]
        if not code.startswith("US.") or "26" not in code:
            continue
        i = code.index("26")
        exp = code[i:i+6]
        od = q.get("option_ex_data") or {}
        rows.append({
            "exp": exp,
            "code": code,
            "strike": od.get("strike_price"),
            "otype": od.get("option_type"),
            "oi": od.get("open_interest") or 0,
            "volume": q.get("volume") or 0,
            "last": q.get("last_price"),
            "iv": od.get("implied_volatility"),
            "delta": od.get("delta"),
            "gamma": od.get("gamma"),
        })

json.dump(rows, open("C:/Users/Administrator/Desktop/stock/results/vst_opt_rows.json","w"), indent=1)
print(f"total option rows: {len(rows)}")

def f(x):
    return x if x is not None else 0.0

by_exp = {}
for r in rows:
    by_exp.setdefault(r["exp"], []).append(r)

for exp in sorted(by_exp):
    lst = [r for r in by_exp[exp] if r["oi"] > 0]
    print(f"\n========== 到期 20{exp[:2]}-{exp[2:4]}-{exp[4:6]} | 有OI合约 {len(lst)}/{len(by_exp[exp])} ==========")
    calls = [r for r in lst if r["otype"]=="CALL"]
    puts  = [r for r in lst if r["otype"]=="PUT"]

    for side, name in [(calls,"CALL"), (puts,"PUT")]:
        side_sorted = sorted(side, key=lambda x: -x["oi"])
        print(f"  [{name}] 总OI={sum(r['oi'] for r in side)}")
        for r in side_sorted[:8]:
            print(f"    K={r['strike']:>7} OI={r['oi']:>6} Vol={r['volume']:>5} last={r['last']:>7} IV={r['iv'] if r['iv'] is not None else 0:>6.1f}  Δ={f(r['delta']):+.2f} γ={f(r['gamma']):.3f}")

    gmap, dmap = {}, {}
    gex_total = 0
    for r in lst:
        k = r["strike"]
        g = r["oi"]*f(r["gamma"]); gex_total += g
        gmap[k] = gmap.get(k, 0) + g
        dmap[k] = dmap.get(k, 0) + r["oi"]*f(r["delta"])
    gs = sorted(gmap.items(), key=lambda kv: -kv[1])
    ds = sorted(dmap.items(), key=lambda kv: -kv[1])
    tot_nc = sum(r["oi"]*f(r["delta"]) for r in calls)
    tot_np = sum(r["oi"]*f(r["delta"]) for r in puts)
    print(f"  [Gamma Wall] = {gs[0][0]} (GEX={gs[0][1]:.0f}, 总GEX={gex_total:.0f}, 占比{gs[0][1]/gex_total*100:.0f}%) | top5: " + " | ".join(f"{k}:{v:.0f}" for k,v in gs[:5]))
    print(f"  [Delta Wall] top5: " + " | ".join(f"{k}:{v:+.0f}" for k,v in ds[:5]))
    print(f"  净Delta: call={tot_nc:+.0f} put={tot_np:+.0f} 净={tot_nc+tot_np:+.0f}")
