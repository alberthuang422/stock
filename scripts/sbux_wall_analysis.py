import json

rows = json.load(open("C:/Users/Administrator/Desktop/stock/results/sbux_opt_rows.json", encoding="utf-8"))

# code 格式 US.SBUX260828C55000 -> exp = code[7:13] = "260828"
by_exp = {}
for r in rows:
    exp = r["code"][7:13]
    by_exp.setdefault(exp, []).append(r)

for exp in sorted(by_exp):
    lst = by_exp[exp]
    exp_disp = f"20{exp[:2]}-{exp[2:4]}-{exp[4:6]}"
    print(f"\n========== 到期 {exp_disp} ==========")
    calls = [r for r in lst if r["otype"]=="CALL"]
    puts  = [r for r in lst if r["otype"]=="PUT"]
    for side, name in [(calls,"CALL"), (puts,"PUT")]:
        valid = [r for r in side if r["oi"] and r["oi"]>0]
        valid.sort(key=lambda x: -x["oi"])
        print(f"  --- {name}: 有OI行权价 {len(valid)}/{len(side)}")
        print(f"  {'strike':>6} {'OI':>7} {'vol':>6} {'last':>8} {'IV':>6}")
        for r in valid:
            print(f"  {r['strike']:>6} {r['oi']:>7} {r['volume']:>6} {r['last']:>8.2f} {r['iv']:>6.2f}")
        tot = sum(r["oi"] for r in valid)
        if tot:
            wsum = sum(r["strike"]*r["oi"] for r in valid)
            print(f"  => 总OI={tot}, OI加权行权价={wsum/tot:.2f}")
