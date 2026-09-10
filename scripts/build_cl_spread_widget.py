# -*- coding: utf-8 -*-
"""生成 CL 月差走势内联 SVG（日线，近月锚定 +1/+2/+3）"""
import csv

rows = list(csv.DictReader(open("data/cl_contracts/spread/cl_spread_daily.csv", encoding="utf-8")))
S = [("+1  OCT26−NOV26", "abs1_OCT26_NOV26", "#56B4E9", "", "c"),
     ("+2  OCT26−DEC26", "abs2_OCT26_DEC26", "#E69F00", "6 3", "s"),
     ("+3  OCT26−JAN27", "abs3_OCT26_JAN27", "#CC79A7", "2 3", "t")]
LP, RP, TP, BP = 60, 470, 42, 250
vals = [[float(r[k]) for r in rows] for _, k, _, _, _ in S]
allv = [v for s in vals for v in s]
lo, hi = min(min(allv), 0.0), max(allv)
pad = (hi - lo) * 0.06
lo -= pad
hi += pad
n = len(rows)
X = lambda i: LP + (RP - LP) * i / (n - 1)
Yv = lambda v: round(TP + (BP - TP) * (1 - (v - lo) / (hi - lo)), 1)

o = []
o.append('<svg viewBox="0 0 680 320" width="100%" role="img" xmlns="http://www.w3.org/2000/svg">')
o.append('<title>CL(WTI) 近月锚定月差走势 2026-03-10 至 2026-09-10</title>')
o.append('<desc>日线口径三条曲线：+1 OCT26-NOV26、+2 OCT26-DEC26、+3 OCT26-JAN27，单位美元每桶。</desc>')
for t in [2, 4, 6, 8, 10]:
    y = Yv(t)
    o.append(f'<line x1="{LP}" y1="{y}" x2="{RP}" y2="{y}" stroke="rgba(255,255,255,0.10)" stroke-width="0.5"/>')
    o.append(f'<text x="{LP-8}" y="{y}" fill="#9aa0a6" font-size="11" text-anchor="end" dominant-baseline="central">{t}</text>')
y0 = Yv(0)
o.append(f'<line x1="{LP}" y1="{y0}" x2="{RP}" y2="{y0}" stroke="rgba(255,255,255,0.32)" stroke-width="0.8" stroke-dasharray="2 2"/>')
o.append(f'<text x="{LP-8}" y="{y0}" fill="#9aa0a6" font-size="11" text-anchor="end" dominant-baseline="central">0</text>')
for i, r in enumerate(rows):
    if r["ts"][8:10] == "10" and r["ts"][5:7] in ("03", "05", "07"):
        x = round(X(i), 1)
        o.append(f'<line x1="{x}" y1="{y0 if y0>BP else BP}" x2="{x}" y2="{BP}" stroke="rgba(255,255,255,0.07)" stroke-width="0.5"/>')
        o.append(f'<text x="{x}" y="{BP+16}" fill="#9aa0a6" font-size="11" text-anchor="middle">{r["ts"][5:7]}/{r["ts"][2:4]}</text>')
o.append(f'<text x="{LP}" y="{BP+34}" fill="#9aa0a6" font-size="11">2026-03-10</text>')
o.append(f'<text x="{RP}" y="{BP+34}" fill="#9aa0a6" font-size="11" text-anchor="end">2026-09-10</text>')
for (lab, k, col, dash, mk), s in zip(S, vals):
    d = "M" + " L".join(f"{round(X(i),1)},{Yv(v)}" for i, v in enumerate(s))
    da = f' stroke-dasharray="{dash}"' if dash else ""
    o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"{da}/>')
    xe, ye = round(X(n - 1), 1), Yv(s[-1])
    if mk == "c":
        o.append(f'<circle cx="{xe}" cy="{ye}" r="3.2" fill="{col}"/>')
    elif mk == "s":
        o.append(f'<rect x="{xe-3}" y="{ye-3}" width="6" height="6" fill="{col}"/>')
    else:
        o.append(f'<polygon points="{xe},{ye-3.8} {xe-3.8},{ye+2.6} {xe+3.8},{ye+2.6}" fill="{col}"/>')
imin = min(range(n), key=lambda i: vals[0][i])
xi, yi = round(X(imin), 1), Yv(vals[0][imin])
o.append(f'<circle cx="{xi}" cy="{yi}" r="2.6" fill="none" stroke="#56B4E9" stroke-width="1.2"/>')
o.append(f'<text x="{xi-8}" y="{yi+18}" fill="#9aa0a6" font-size="11" text-anchor="middle">7/06 结构最平 +1=0.05</text>')
o.append('<text x="492" y="44" fill="#e8eaed" font-size="12" font-weight="500">近月锚定月差</text>')
last = [s[-1] for s in vals]
for i, (lab, k, col, dash, mk) in enumerate(S):
    ly = 70 + i * 30
    o.append(f'<line x1="492" y1="{ly}" x2="520" y2="{ly}" stroke="{col}" stroke-width="1.8"' + (f' stroke-dasharray="{dash}"' if dash else "") + '/>')
    o.append(f'<text x="528" y="{ly+4}" fill="#e8eaed" font-size="12">{lab}</text>')
    o.append(f'<text x="492" y="{ly+20}" fill="{col}" font-size="12" font-weight="500">{last[i]:+.2f} USD/bbl</text>')
o.append('<text x="492" y="196" fill="#9aa0a6" font-size="11">最新三档每月陡度</text>')
o.append('<text x="492" y="214" fill="#e8eaed" font-size="12">3.61 / 3.75 / 3.59</text>')
o.append('<text x="492" y="236" fill="#9aa0a6" font-size="11">→ 三档几乎同陡，</text>')
o.append('<text x="492" y="252" fill="#9aa0a6" font-size="11">  非某一档独强</text>')
o.append('<text x="492" y="284" fill="#9aa0a6" font-size="11">近月 OCT26 最后交易日 9/22</text>')
o.append('</svg>')
open("Temp/cl_spread_widget.svg", "w", encoding="utf-8").write("\n".join(o))
print(f"lo={lo:.2f} hi={hi:.2f} bytes={len(chr(10).join(o))}")
print("\n".join(o))
