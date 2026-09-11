# -*- coding: utf-8 -*-
"""曲线形状份额演化：剔除价格水平影响，看 d1/d2/d3 各自占 3 月总月差的比例"""
import csv
rows = list(csv.DictReader(open("data/cl_contracts/spread/cl_spread_daily.csv", encoding="utf-8")))
cols = ["abs1_OCT26_NOV26", "abs1_NOV26_DEC26", "abs1_DEC26_JAN27"]
print(f"{'日期':<12}{'d1':>7}{'d2':>7}{'d3':>7}{'合计':>8}{'d1占%':>8}{'d2占%':>8}{'d3占%':>8}{'形状':>10}")
for r in rows[-45::5] + [rows[-1]]:
    a, b, c = (float(r[x]) for x in cols)
    s = a + b + c
    if s <= 0: continue
    sh = [a/s*100, b/s*100, c/s*100]
    if sh[0] > sh[1] > sh[2]: shape = "单调递减"
    elif sh[1] > sh[0] and sh[1] > sh[2]: shape = "峰在中段"
    elif sh[0] > sh[1] and sh[2] > sh[1]: shape = "谷在中段"
    else: shape = "前段最陡"
    print(f"{r['ts']:<12}{a:>7.2f}{b:>7.2f}{c:>7.2f}{s:>8.2f}{sh[0]:>8.1f}{sh[1]:>8.1f}{sh[2]:>8.1f}{shape:>10}")

print("\n== 全样本(128日)内 d2>d1 与 d1>d3 的成立频率 ==")
n = nA = nB = 0
for r in rows:
    a, b, c = (float(r[x]) for x in cols)
    if b <= 0 or a <= 0: continue
    n += 1
    if b > a: nA += 1
    if a > c: nB += 1
print(f"  样本 {n} 日 | d2>d1 占 {nA/n*100:.1f}% | d1>d3 占 {nB/n*100:.1f}% | 两者同时成立 {sum(1 for r in rows if (float(r[cols[1]])>float(r[cols[0]])>0 and float(r[cols[0]])>float(r[cols[2]])))/n*100:.1f}%")
