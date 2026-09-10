# -*- coding: utf-8 -*-
"""生成 4h 价差突破对比 SVG（修订版）"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
BASE = r"C:\Users\Administrator\Desktop\stock"
d = json.load(open(BASE + r"\Temp\spread4h_chart.json", encoding="utf-8"))
t, s1, s2 = d["t"], d["s1"], d["s2"]
N = len(t)

X0, X1 = 74, 640
Y0, Y1 = 410, 112
vmin, vmax = 1.0, 3.8
def X(i): return X0 + (X1 - X0) * i / (N - 1)
def Y(v): return Y0 - (Y0 - Y1) * (v - vmin) / (vmax - vmin)

def find(prefix):
    for i, x in enumerate(t):
        if x.startswith(prefix):
            return i
    return None

i_brk = find("09-09 22:00")
i_brk2 = find("09-10 05:00")
i_0908 = find("09-08 02:00")

p1 = " ".join(f"{X(i):.1f},{Y(s1[i]):.1f}" for i in range(N))
p2 = " ".join(f"{X(i):.1f},{Y(s2[i]):.1f}" for i in range(N))

svg = []
A = svg.append
A('<svg viewBox="0 0 680 692" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,\'Segoe UI\',\'Microsoft YaHei\',sans-serif">')
A('<rect width="680" height="692" fill="#17191d" rx="10"/>')
A('<text x="24" y="30" fill="#e6e8ea" font-size="15" font-weight="700">4 小时价差核实：OCT-NOV vs NOV-DEC（08-26 → 09-10）</text>')
A('<text x="24" y="50" fill="#9aa0a6" font-size="10.5">由 CL2610 / CL2611 / CL2612 三条腿 4h K 线相减合成；数据截至 09-10 10:00（北京时间）</text>')

for v in (1.5, 2.0, 2.5, 3.0, 3.5):
    A(f'<line x1="{X0}" y1="{Y(v):.1f}" x2="{X1}" y2="{Y(v):.1f}" stroke="#2c3036" stroke-dasharray="3 5"/>')
    A(f'<text x="{X0-6}" y="{Y(v)+3.5:.1f}" fill="#9aa0a6" font-size="9.5" text-anchor="end">{v:.1f}</text>')
A(f'<line x1="{X0}" y1="{Y(1.0):.1f}" x2="{X1}" y2="{Y(1.0):.1f}" stroke="#3a3f46"/>')

# 前高虚线
A(f'<line x1="{X(i_0908)}" y1="{Y(3.50):.1f}" x2="{X1}" y2="{Y(3.50):.1f}" stroke="#56B4E9" stroke-width="1" stroke-dasharray="5 4" opacity="0.8"/>')
A(f'<line x1="{X(i_0908)}" y1="{Y(3.57):.1f}" x2="{X1}" y2="{Y(3.57):.1f}" stroke="#E69F00" stroke-width="1" stroke-dasharray="5 4" opacity="0.8"/>')

A(f'<polyline points="{p1}" fill="none" stroke="#56B4E9" stroke-width="2"/>')
A(f'<polyline points="{p2}" fill="none" stroke="#E69F00" stroke-width="2" stroke-dasharray="6 3"/>')

A(f'<line x1="{X(i_0908)}" y1="80" x2="{X(i_0908)}" y2="{Y(1.0):.1f}" stroke="#7a8089" stroke-width="1" stroke-dasharray="4 4"/>')
A(f'<text x="{X(i_0908)+4}" y="90" fill="#9aa0a6" font-size="9.5">09-08</text>')

# 突破标记
A(f'<circle cx="{X(i_brk):.1f}" cy="{Y(s2[i_brk]):.1f}" r="5" fill="none" stroke="#F0E442" stroke-width="1.8"/>')
A(f'<circle cx="{X(i_brk2):.1f}" cy="{Y(s2[i_brk2]):.1f}" r="4.5" fill="#F0E442"/>')
A(f'<circle cx="{X(N-1):.1f}" cy="{Y(s2[-1]):.1f}" r="3.5" fill="#E69F00"/>')
A(f'<circle cx="{X(N-1):.1f}" cy="{Y(s1[-1]):.1f}" r="3.5" fill="#56B4E9"/>')

# 图内结论
A('<text x="80" y="104" fill="#F0E442" font-size="10.5" font-weight="600">✅ NOV-DEC 突破：09-09 22:00 破盘整上沿 3.40，09-10 05:00 破 09-03 前高 3.57</text>')
A('<text x="80" y="122" fill="#56B4E9" font-size="10.5" font-weight="600">❌ OCT-NOV 未突破：最高 3.40，仍低于 09-04 前高 3.50</text>')

for lb, pre in [("08-26", "08-26"), ("08-31", "08-31"), ("09-03", "09-03"), ("09-05", "09-05"), ("09-08", "09-08"), ("09-10", "09-10")]:
    i = find(pre)
    if i is not None:
        A(f'<text x="{X(i):.1f}" y="430" fill="#9aa0a6" font-size="9.5" text-anchor="middle">{lb}</text>')

A('<line x1="24" y1="452" x2="44" y2="452" stroke="#56B4E9" stroke-width="2"/>')
A('<text x="50" y="456" fill="#c8cdd2" font-size="10.5">OCT-NOV (10-11)</text>')
A('<line x1="190" y1="452" x2="210" y2="452" stroke="#E69F00" stroke-width="2" stroke-dasharray="6 3"/>')
A('<text x="216" y="456" fill="#c8cdd2" font-size="10.5">NOV-DEC (11-12)</text>')
A('<text x="656" y="456" fill="#9aa0a6" font-size="9.5" text-anchor="end">虚线 = 09-04 / 09-03 前高</text>')

# OI 面板
A('<line x1="24" y1="478" x2="656" y2="478" stroke="#2c3036"/>')
A('<text x="24" y="502" fill="#e6e8ea" font-size="12" font-weight="600">持仓量：09-10 主力合约首次由 OCT 切换到 NOV —— 移仓正在发生</text>')
oi = d["oi"]
n_oi = len(oi["d"])
ix0, ix1 = 74, 480
iy0, iy1 = 632, 522
ovmin, ovmax = 130000, 300000
def OX(i): return ix0 + (ix1 - ix0) * i / (n_oi - 1)
def OY(v): return iy0 - (iy0 - iy1) * (v - ovmin) / (ovmax - ovmin)
po = " ".join(f"{OX(i):.1f},{OY(v):.1f}" for i, v in enumerate(oi["oct"]))
pn = " ".join(f"{OX(i):.1f},{OY(v):.1f}" for i, v in enumerate(oi["nov"]))
A(f'<polyline points="{po}" fill="none" stroke="#56B4E9" stroke-width="2"/>')
A(f'<polyline points="{pn}" fill="none" stroke="#E69F00" stroke-width="2" stroke-dasharray="6 3"/>')
A(f'<circle cx="{OX(n_oi-1):.1f}" cy="{OY(oi["nov"][-1]):.1f}" r="4" fill="#F0E442"/>')
A(f'<circle cx="{OX(n_oi-1):.1f}" cy="{OY(oi["oct"][-1]):.1f}" r="3.5" fill="#56B4E9"/>')
A(f'<text x="{OX(n_oi-1)+6:.1f}" y="{OY(oi["nov"][-1])+3.5:.1f}" fill="#F0E442" font-size="10" font-weight="600">NOV 226,184 ▲</text>')
A(f'<text x="{OX(n_oi-1)+6:.1f}" y="{OY(oi["oct"][-1])+3.5:.1f}" fill="#c8cdd2" font-size="10">OCT 214,897 ▼</text>')
A(f'<text x="{OX(0):.1f}" y="648" fill="#9aa0a6" font-size="9.5">08-13</text>')
A(f'<text x="{OX(n_oi-1):.1f}" y="648" fill="#E69F00" font-size="9.5" text-anchor="middle">09-10</text>')
A('<text x="516" y="536" fill="#c8cdd2" font-size="10.5">OCT 持仓：228,881 → 214,897</text>')
A('<text x="516" y="552" fill="#c8cdd2" font-size="10.5">（08-21 峰值 293,984 后一路降）</text>')
A('<text x="516" y="574" fill="#E69F00" font-size="10.5">NOV 持仓：142,347 → 226,184</text>')
A('<text x="516" y="590" fill="#E69F00" font-size="10.5">（+59%，09-10 完成反超）</text>')
A('<text x="516" y="614" fill="#F0E442" font-size="10.5" font-weight="600">= 紧张定价正迁向新主力 NOV</text>')
A('<text x="24" y="676" fill="#c8cdd2" font-size="10">⚠ 上图基于 4h K 线（富途仅更新至 09-10 10:00）。最新实时报价 OCT 97.45 / NOV 93.82 / DEC 89.91 → 10-11 = 3.63、11-12 = 3.91</text>')
A('<text x="24" y="690" fill="#c8cdd2" font-size="10">　 即 OCT-NOV 在 10:00 后的欧/美盘已追上并突破前高 3.50 —— 你看到的"未突破"是 10:00 前的状态</text>')
A("</svg>")

open(BASE + r"\Temp\widget.svg", "w", encoding="utf-8").write("\n".join(svg))
print("ok")
