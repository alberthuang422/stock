import json

files = [
    r"C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-Desktop-stock/a3df5bb9-bf1b-4408-a366-f33d83b51d4d/tool-results/mcp-connector-proxy-futu-mcp_quote_stock_quote-1787385896117-e418ac.txt",
    r"C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-Desktop-stock/a3df5bb9-bf1b-4408-a366-f33d83b51d4d/tool-results/mcp-connector-proxy-futu-mcp_quote_stock_quote-1787385896002-c6a40d.txt",
]
rows = []
spot = None
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    for q in d["data"]["quote_list"]:
        if q["code"] == "US.SBUX":
            spot = q["last_price"]
            continue
        od = q.get("option_ex_data") or {}
        rows.append({
            "exp": q["code"][7:13],
            "code": q["code"],
            "strike": od.get("strike_price"),
            "otype": od.get("option_type"),
            "oi": od.get("open_interest") or 0,
            "last": q.get("last_price"),
            "iv": od.get("implied_volatility"),
            "delta": od.get("delta"),
            "gamma": od.get("gamma"),
        })

print(f"现货 spot = {spot}\n")
by_exp = {}
for r in rows:
    by_exp.setdefault(r["exp"], []).append(r)

def f(x):
    return x if x is not None else 0.0

for exp in sorted(by_exp):
    lst = [r for r in by_exp[exp] if r["oi"] > 0 and r["gamma"] is not None]
    print(f"======== 到期 20{exp[:2]}-{exp[2:4]}-{exp[4:6]}  (有OI且有希腊字母的合约数 {len(lst)}) ========")

    # 1) 纯 OI walls
    calls = [r for r in lst if r["otype"]=="CALL"]
    puts  = [r for r in lst if r["otype"]=="PUT"]
    cw = max(calls, key=lambda r: r["oi"]); pw = max(puts, key=lambda r: r["oi"])
    print(f"[纯OI] CallWall={cw['strike']} (OI={cw['oi']}) | PutWall={pw['strike']} (OI={pw['oi']})")

    # 2) gamma 加权 wall: 每个行权价 Σ(OI*gamma)，call+put 合并
    gmap = {}
    dmap = {}
    for r in lst:
        k = r["strike"]
        g = r["oi"] * f(r["gamma"])
        d = r["oi"] * f(r["delta"])
        gmap[k] = gmap.get(k, 0) + g
        dmap[k] = dmap.get(k, 0) + d
    gs = sorted(gmap.items(), key=lambda kv: -kv[1])
    ds = sorted(dmap.items(), key=lambda kv: -kv[1])
    gw = gs[0][0]
    print(f"[Gamma加权] GammaWall={gw}  (GEX=Σ OI×γ)")
    print("  top5 行权价 GEX(Σ OI×γ, 相对单位): " + " | ".join(f"{k}:{v:.0f}" for k, v in gs[:5]))
    print("  top5 行权价 净Delta(Σ OI×Δ, call正put负): " + " | ".join(f"{k}:{v:+.0f}" for k, v in ds[:5]))

    # 3) 汇总
    tot_nc = sum(r["oi"]*f(r["delta"]) for r in calls)
    tot_np = sum(r["oi"]*f(r["delta"]) for r in puts)
    tot_g  = sum(gmap.values())
    print(f"  Call侧 Σ(OI×Δ)={tot_nc:+.0f} | Put侧 Σ(OI×Δ)={tot_np:+.0f} | 净 {tot_nc+tot_np:+.0f} (净正=多头主导)")
    print(f"  总GEX={tot_g:.0f} | GW占比 {gmap[gw]/tot_g*100:.1f}%")
    print()
