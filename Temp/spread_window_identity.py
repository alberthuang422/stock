# -*- coding: utf-8 -*-
"""滚动窗口价差的恒等分解：S(k,w) - S(k+1,w) = d_k - d_{k+w}"""
import csv, json

rows = list(csv.DictReader(open("data/cl_contracts/spread/cl_spread_daily.csv", encoding="utf-8")))
cur = rows[-1]
P = [float(cur[k]) for k in ["CL2610", "CL2611", "CL2612", "CL2701", "CL2702", "CL2703"]]
N = ["10月", "11月", "12月", "1月", "2月", "3月"]

d = [P[i] - P[i + 1] for i in range(5)]          # 相邻1月
print("== 9/10 相邻月差 d1..d5 ==")
for i, v in enumerate(d):
    print(f"  d{i+1} {N[i]}-{N[i+1]}: {v:.2f}")

print("\n== 用户的两组对比 ==")
print(f"  [A] 2610-2611={d[0]:.2f}  vs  2611-2612={d[1]:.2f}   -> 前者小 {d[0] < d[1]}   (即 d1 < d2)")
print(f"     等价于: d2 - d1 = {d[1]-d[0]:+.2f}")
P2_1 = P[0] - P[2]; P2_2 = P[1] - P[3]
print(f"  [B] 2610-2612={P2_1:.2f}  vs  2611-2701={P2_2:.2f}  -> 后者小 {P2_2 < P2_1}  (即 d1+d2 < d2+d3)")
print(f"     等价于: d1 - d3 = {d[0]-d[2]:+.2f}        (中间腿 d2={d[1]:.2f} 两边共享,被约掉)")
print(f"\n  两式联立 ⇒ d2 > d1 > d3 : {d[1]:.2f} > {d[0]:.2f} > {d[2]:.2f}  -> {d[1] > d[0] > d[2]}")
print("  ⇒ 只要相邻月差是『峰形』，A 与 B 必然同时成立，无矛盾。")

print("\n== 恒等式验证 S(k,w)-S(k+1,w) = d_k - d_{k+w} ==")
print(f"{'窗宽w':<6}{'窗口k':<18}{'S(k,w)':>9}{'S(k+1,w)':>10}{'差':>8}{'= d_k - d_k+w':>16}")
for w in (1, 2, 3):
    for k in range(0, 5 - w):
        Sk = P[k] - P[k + w]; Sk1 = P[k + 1] - P[k + 1 + w]
        rhs = d[k] - d[k + w]
        print(f"{w:<6}{N[k]+'-'+N[k+w]:<18}{Sk:>9.2f}{Sk1:>10.2f}{Sk-Sk1:>8.2f}{rhs:>16.2f}")

print("\n== 曲线曲率（蝶式）==")
for i in range(4):
    print(f"  (d{i+1}-d{i+2}) = {d[i]-d[i+1]:+.2f}")

print("\n== 相对水平（占近腿%）==")
for i in range(5):
    print(f"  {N[i]}→{N[i+1]}: {d[i]/P[i]*100:.3f}%")

print("\n== d1..d3 近 45 个交易日轨迹（每5日采样）==")
print(f"{'日期':<12}{'d1(10-11)':>11}{'d2(11-12)':>11}{'d3(12-1)':>11}{'d2>d1?':>8}{'d1>d3?':>8}")
for r in rows[-45::5] + [rows[-1]]:
    a, b, c = (float(r[c]) for c in ["abs1_OCT26_NOV26", "abs1_NOV26_DEC26", "abs1_DEC26_JAN27"])
    print(f"{r['ts']:<12}{a:>11.2f}{b:>11.2f}{c:>11.2f}{('是' if b>a else '否'):>8}{('是' if a>c else '否'):>8}")
