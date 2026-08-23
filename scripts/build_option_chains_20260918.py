# -*- coding: utf-8 -*-
"""生成 8 只标的 2026-09-18 到期期权链合约列表（从已拉取的行权价清单构建）。"""
import json

EXP = "260918"

CHAINS = {
    "ABBV": [95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200,210,220,225,230,235,240,242.5,245,247.5,250,252.5,255,257.5,260,262.5,265,267.5,270,272.5,275,277.5,280,282.5,285,287.5,290,295,300,305,310,315,320,330,340,350,360],
    "GILD": [55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,152.5,155,157.5,160,162.5,165,167.5,170,175,180,185,190,195,200,210],
    "LLY": None,   # 从已解析文件读取
    "JNJ": [80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200,210,220,225,230,235,240,245,247.5,250,252.5,255,257.5,260,262.5,265,267.5,270,272.5,275,277.5,280,282.5,285,287.5,290,292.5,295,300,305,310,315,320,330,340,350,360,370,380],
    "KO": [32.5,35,37.5,40,42.5,45,47.5,50,52.5,55,57.5,60,62.5,65,67.5,70,72.5,75,77,77.5,78,79,80,81,82,82.5,83,84,85,86,87,87.5,88,89,90,91,92,92.5,93,94,95,96,97,97.5,98,99,100,101,102,105,110,115,120,125],
    "SBUX": [45,50,55,60,65,70,75,80,85,90] + list(range(91,119)) + [120,125,130,135,140,145,150,155,160],
    "CSCO": [32.5,35,37.5,40,42.5,45,47.5,50,55,57.5,60,62.5,65,67.5,70,72.5,75,77.5,80,82.5,85,87.5,90,92.5,95,97.5] + list(range(98,126)) + [130,135,140,145,150,155,160,165,170,175,180,185,190],
    "AMZN": list(range(105,305,5)) + [s/2 for s in range(475,566,5)] + list(range(305,365,5)) + [370,375,380,390,400,410],
}
# AMZN 半行权价实际存在的只有 237.5~282.5（无287.5）
CHAINS["AMZN"] = list(range(105,305,5)) + [237.5,242.5,247.5,252.5,257.5,262.5,267.5,272.5,277.5,282.5] + list(range(305,365,5)) + [370,375,380,390,400,410]

out_all = {}
for tk, strikes in CHAINS.items():
    if tk == "LLY":
        recs = json.load(open(r"C:\Users\Administrator\Desktop\stock\results\chain_LLY_20260918.json"))
        out_all[tk] = recs
        continue
    recs = []
    for s in strikes:
        tail = str(int(round(s * 1000)))
        recs.append({"code": f"US.{tk}{EXP}C{tail}", "strike": float(s), "type": "CALL"})
        recs.append({"code": f"US.{tk}{EXP}P{tail}", "strike": float(s), "type": "PUT"})
    out_all[tk] = recs

total = 0
for tk, recs in out_all.items():
    json.dump(recs, open(rf"C:\Users\Administrator\Desktop\stock\results\chain_{tk}_20260918.json", "w"), indent=1)
    total += len(recs)
    print(f"{tk}: {len(recs)} contracts ({len(set(r['strike'] for r in recs))} strikes)")

# 输出分批 code_list（<=400/批）
codes = []
for tk in ["ABBV","GILD","LLY","JNJ","KO","SBUX","CSCO","AMZN"]:
    codes += [r["code"] for r in out_all[tk]]
batches = [codes[i:i+400] for i in range(0, len(codes), 400)]
print(f"TOTAL {len(codes)} contracts -> {len(batches)} batches: {[len(b) for b in batches]}")
json.dump(batches, open(r"C:\Users\Administrator\Desktop\stock\results\oi_batches.json", "w"))
print("written: results/oi_batches.json")
