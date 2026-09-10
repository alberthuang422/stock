# -*- coding: utf-8 -*-
"""月差分组分析：曲线 / 价差水平 / 周月变化 / 历史分位"""
import json, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\Administrator\Desktop\stock"
d = json.load(open(BASE + r"\results\futu_monthspread_raw.json", encoding="utf-8"))

legs = {x["code"]: x for x in d["snapshot_legs"]["data"]["snapshot_list"]}
order = ["US.CL2610", "US.CL2611", "US.CL2612", "US.CL2701", "US.CL2702", "US.CL2703"]
labels = {"US.CL2610": "OCT26", "US.CL2611": "NOV26", "US.CL2612": "DEC26",
          "US.CL2701": "JAN27", "US.CL2702": "FEB27", "US.CL2703": "MAR27"}

ut = legs["US.CL2610"].get("update_time")
ts = dt.datetime.fromtimestamp(ut / 1000, dt.timezone(dt.timedelta(hours=8)))
print(f"数据时间(北京): {ts:%Y-%m-%d %H:%M:%S}   来源: 富途 / CME")
print()
print("=== 1) 当前原油远期曲线 (WTI, USD/bbl) ===")
print(f"{'合约':<8}{'最新':>9}{'前收':>9}{'日变':>9}{'日变%':>9}{'结算':>9}")
for k in order:
    x = legs[k]
    last, prev = x.get("last_price"), x.get("prev_close_price")
    settle = x.get("future_ex_data", {}).get("last_settle_price")
    chg = (last - prev) if (last and prev) else 0
    print(f"{labels[k]:<8}{last:>9.2f}{prev:>9.2f}{chg:>+9.2f}{(chg/prev*100):>8.2f}%{settle:>9.2f}")
print()

print("=== 2) 跨期价差 (近月 − 远月, USD/bbl) ===")
sp = {x["code"]: x for x in d["snapshot_spreads"]["data"]["snapshot_list"]}
pairs = [("US.CL2610/CL2611", "OCT-NOV", "M1-M2 前端"),
         ("US.CL2611/CL2612", "NOV-DEC", "M2-M3 次段"),
         ("US.CL2610/CL2612", "OCT-DEC", "M1-M3 合计"),
         ("US.CL2612/CL2701", "DEC-JAN", "M3-M4 中段"),
         ("US.CL2611/CL2701", "NOV-JAN", "M2-M4"),
         ("US.CL2611/CL2702", "NOV-FEB", "M2-M5"),
         ("US.CL2612/CL2703", "DEC-MAR", "M3-M6")]
print(f"{'价差':<10}{'段位':<12}{'最新':>8}{'前收':>8}{'日变':>8}{'52w高':>8}{'52w低':>8}")
for code, name, seg in pairs:
    x = sp.get(code)
    if not x:
        continue
    last, prev = x.get("last_price"), x.get("prev_close_price")
    print(f"{name:<10}{seg:<12}{last:>8.2f}{prev:>8.2f}{last-prev:>+8.2f}"
          f"{x.get('highest52weeks_price',0):>8.2f}{x.get('lowest52weeks_price',0):>8.2f}")
print()

print("=== 3) 日变动分解 (恒等式 M1-M3 = M1-M2 + M2-M3) ===")
chg = {k: legs[k]["last_price"] - legs[k]["prev_close_price"] for k in order}
d12 = chg["US.CL2610"] - chg["US.CL2611"]
d23 = chg["US.CL2611"] - chg["US.CL2612"]
d13 = chg["US.CL2610"] - chg["US.CL2612"]
print(f"Δ(M1-M2) = {d12:+.2f}   Δ(M2-M3) = {d23:+.2f}   Δ(M1-M3) = {d13:+.2f}   (校验 {d12+d23:+.2f})")
if d13:
    print(f"走阔占比: 前端 {d12/d13*100:.0f}% / 次段 {d23/d13*100:.0f}%")
print()

print("=== 4) 日线历史变化 (腿合约合成) ===")
kl = {}
for k in order:
    r = d["kline"].get(k)
    if isinstance(r, dict) and isinstance(r.get("data"),dict) and r["data"].get("kline_list"):
        kl[k] = r["data"]["kline_list"]
for k in order:
    if k in kl:
        print(f"{labels[k]}: {len(kl[k])} bars  {kl[k][0].get('time_key')} -> {kl[k][-1].get('time_key')}")
    else:
        print(f"{labels[k]}: 无数据")
print()
if len(kl) >= 3:
    n = min(len(v) for v in kl.values())
    def ser(a, b):
        return [round(float(kl[a][i]["close"]) - float(kl[b][i]["close"]), 4) for i in range(n)]
    print(f"{'价差':<10}{'现值':>8}{'5日前':>9}{'20日前':>9}{'60日前':>9}{'Δ20d':>8}{'Δ60d':>8}")
    for a, b, nm in [("US.CL2610", "US.CL2611", "OCT-NOV"), ("US.CL2611", "US.CL2612", "NOV-DEC"),
                     ("US.CL2610", "US.CL2612", "OCT-DEC"), ("US.CL2611", "US.CL2701", "NOV-JAN")]:
        if a not in kl or b not in kl:
            continue
        s = ser(a, b)
        v = s[-1]
        p5 = s[-6] if len(s) > 6 else float("nan")
        p20 = s[-21] if len(s) > 21 else float("nan")
        p60 = s[-61] if len(s) > 61 else float("nan")
        print(f"{nm:<10}{v:>8.2f}{p5:>9.2f}{p20:>9.2f}{p60:>9.2f}{v-p20:>+8.2f}{v-p60:>+8.2f}")
    print()
    print("日期锚点(最新):", kl[order[0]][-1]["time_key"])
    for back in (5, 20, 60):
        if len(kl[order[0]]) > back:
            print(f"  {back}日前 =", kl[order[0]][-1 - back]["time_key"])
    # 分位
    print()
    print("=== 5) 价差历史分位 (近%d个交易日) ===" % n)
    for a, b, nm in [("US.CL2610", "US.CL2611", "OCT-NOV"), ("US.CL2611", "US.CL2612", "NOV-DEC"),
                     ("US.CL2610", "US.CL2612", "OCT-DEC"), ("US.CL2611", "US.CL2701", "NOV-JAN")]:
        if a not in kl or b not in kl:
            continue
        s = ser(a, b)
        v = s[-1]
        pct = sum(1 for x in s if x <= v) / len(s) * 100
        print(f"{nm:<10} 现值 {v:>6.2f}  区间[{min(s):>6.2f}, {max(s):>6.2f}]  分位 {pct:>5.0f}%")
