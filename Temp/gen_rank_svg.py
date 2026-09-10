# -*- coding: utf-8 -*-
"""生成 12条月差 × 5种排序口径 的名次矩阵 SVG"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

rows = [
    ('NOV26-DEC26', [8, 5, 1, 6, 1], 4.2),
    ('JAN27-MAR27', [4, 2, 3, 1, 11], 4.2),
    ('NOV26-FEB27', [1, 6, 4, 5, 6], 4.4),
    ('DEC26-MAR27', [2, 3, 7, 3, 10], 5.0),
    ('FEB27-MAR27', [9, 1, 2, 2, 12], 5.2),
    ('OCT26-DEC26', [5, 9, 5, 11, 2], 6.4),
    ('NOV26-JAN27', [6, 8, 6, 8, 5], 6.6),
    ('DEC26-FEB27', [7, 7, 9, 4, 8], 7.0),
    ('OCT26-JAN27', [3, 10, 10, 10, 4], 7.4),
    ('JAN27-FEB27', [10, 4, 8, 7, 9], 7.6),
    ('DEC26-JAN27', [11, 11, 11, 9, 7], 9.8),
    ('OCT26-NOV26', [12, 12, 12, 12, 3], 10.2),
]

def cell_color(r):
    if r <= 3:   return '#0C447C', '#FFFFFF'
    if r <= 6:   return '#378ADD', '#FFFFFF'
    if r <= 9:   return '#B5D4F4', '#042C53'
    return '#E6F1FB', '#0C447C'

L = []
A = L.append
H = 424
A(f'<svg viewBox="0 0 680 {H}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg" '
  f'font-family="-apple-system,\'Segoe UI\',\'Microsoft YaHei\',sans-serif">')
A('<title>WTI 12条月差在5种排序口径下的名次矩阵</title>')
A('<desc>12 条月差价差，按绝对幅度、相对幅度、归一陡度、波动归一、自8月26日累计五种口径排名的名次矩阵，1 表示该口径下最强。</desc>')

# 表头
x_comb, w_comb = 40, 104
cols = [('A 绝对$', 148), ('B 相对%', 222), ('C 陡度', 296), ('D 波动σ', 370), ('E 自0826', 444), ('均名次', 526)]
w = 68
A('<rect x="40" y="34" width="562" height="26" rx="5" fill="none" stroke="#5F5E5A" stroke-width="0.5"/>')
A(f'<text x="46" y="51" font-size="11" fill="#B4B2A9">组合</text>')
for name, cx in cols:
    A(f'<text x="{cx+34}" y="51" font-size="11" fill="#B4B2A9" text-anchor="middle">{name}</text>')

y0 = 66
rh = 27
for i, (nm, ranks, avg) in enumerate(rows):
    y = y0 + i*rh
    if i % 2 == 0:
        A(f'<rect x="40" y="{y}" width="562" height="{rh}" fill="#2C2C2A" opacity="0.35"/>')
    A(f'<text x="46" y="{y+18}" font-size="11.5" fill="#F1EFE8">{nm}</text>')
    for j, r in enumerate(ranks):
        cx = 148 + j*74
        f, t = cell_color(r)
        A(f'<rect x="{cx}" y="{y+2.5}" width="{w}" height="{rh-6}" rx="4" fill="{f}"/>')
        A(f'<text x="{cx+w/2}" y="{y+18}" font-size="11.5" fill="{t}" text-anchor="middle" font-weight="500">{r}</text>')
    # 均名次
    cx = 526
    strong = avg <= 5.0
    f = '#0F6E56' if strong else '#444441'
    t = '#FFFFFF' if strong else '#D3D1C7'
    A(f'<rect x="{cx}" y="{y+2.5}" width="{w}" height="{rh-6}" rx="4" fill="{f}"/>')
    A(f'<text x="{cx+w/2}" y="{y+18}" font-size="11.5" fill="{t}" text-anchor="middle" font-weight="500">{avg}</text>')

yb = y0 + 12*rh + 14
A(f'<text x="40" y="{yb}" font-size="11" fill="#B4B2A9">深色 = 名次靠前（1 = 该口径最强）｜ 均名次 ≤5.0 用绿色标注 ｜ 名次越低越好</text>')
A(f'<text x="40" y="{yb+17}" font-size="11" fill="#888780">口径：A 突破绝对幅度($/bbl) ｜ B 相对突破幅度(%) ｜ C 归一陡度($/月) ｜ D 突破/近60日4h变动σ ｜ E 自08-26累计扩张陡度($/月)</text>')
A('</svg>')
open('Temp/rank_matrix.svg', 'w', encoding='utf-8').write('\n'.join(L))
print('H =', H, ' elements =', len(L))
