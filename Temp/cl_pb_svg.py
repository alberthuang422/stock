# -*- coding: utf-8 -*-
import json,numpy as np
PA=json.loads("""[0.0,-0.092,-0.136,0.001,0.197,0.216,0.41,0.251,0.378,0.391,0.314,0.478,0.428,0.097,-0.203,-0.168,-0.315,-0.31,-0.405,-0.254,-0.306,0.293,0.227,0.048,0.382,0.28,0.35,0.375,0.362,0.232,0.299,0.226,0.325,-0.151,-0.732,-0.807,-0.841,-1.097,-0.824,-0.714,-0.807,-0.836,-0.644,-0.7,-0.601,-0.362,-0.529,-0.487,-0.412]""")
SA=json.loads("""[0.0,0.09,0.175,0.203,0.176,0.189,0.176,0.161,0.21,0.223,0.252,0.333,0.327,0.715,0.717,0.76,0.822,0.825,0.874,0.888,1.009,1.152,1.226,1.115,1.132,1.139,1.164,1.196,1.182,1.29,1.216,1.098,1.27,1.182,0.918,0.908,0.931,0.967,1.062,1.206,1.174,1.216,1.264,1.246,1.258,1.245,1.269,1.28,1.288]""")
PC=json.loads("""[0.0,0.099,0.259,0.228,0.781,0.608,0.473,0.419,0.277,0.139,0.077,0.267,0.194,0.184,0.086,0.294,0.145,0.727,0.632,0.368,0.398,0.484,0.296,0.402,0.477,0.476,0.511,0.394,0.579,0.252,0.768,0.605,0.59,0.547,0.31,0.118,0.173,0.262,0.279,0.328,0.17,0.481,0.281,0.262,0.324,0.302,0.308,0.274,0.382]""")
PROB={"A":{"12":{"pc":30.0,"pb":16.2},"24":{"pc":40.0,"pb":28.2},"48":{"pc":50.0,"pb":42.9}},
      "C":{"12":{"pc":20.0,"pb":14.8},"24":{"pc":30.0,"pb":22.0},"48":{"pc":30.0,"pb":26.9}}}
X0,X1=74,652; W=X1-X0
P1T,P1B=80,250
YMIN,YMAX=-1.25,1.05
def x(h): return X0+W*h/48
def y(v): return P1B-(v-YMIN)/(YMAX-YMIN)*(P1B-P1T)
def pl(vals,color,dash=""):
    d="M"+" L".join(f"{x(h):.0f},{y(v):.0f}" for h,v in enumerate(vals))
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.4"{(" stroke-dasharray=\""+dash+"\"") if dash else ""} stroke-linejoin="round"/>'
def band(m,s,color,op=.13):
    up=[m[i]+s[i] for i in range(len(m))]; lo=[m[i]-s[i] for i in range(len(m))]
    d="M"+" L".join(f"{x(i):.0f},{y(v):.0f}" for i,v in enumerate(up))+" L"+" L".join(f"{x(i):.0f},{y(v):.0f}" for i,v in reversed(list(enumerate(lo))))+" Z"
    return f'<path d="{d}" fill="{color}" opacity="{op}"/>'
g=[]
for v in (-1.0,-0.5,0.5,1.0):
    g.append(f'<line x1="{X0}" y1="{y(v):.0f}" x2="{X1}" y2="{y(v):.0f}" stroke="rgba(255,255,255,0.10)" stroke-width="1"/>')
    g.append(f'<text x="{X0-8}" y="{y(v)+4:.0f}" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">{v:+.1f}</text>')
g.append(f'<line x1="{X0}" y1="{y(0):.0f}" x2="{X1}" y2="{y(0):.0f}" stroke="rgba(255,255,255,0.45)" stroke-width="1.2" stroke-dasharray="4,3"/>')
g.append(f'<text x="{X1}" y="{y(0)-5:.0f}" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">事件点水平 = 0</text>')
ax="".join(f'<text x="{x(h):.0f}" y="{P1B+16:.0f}" text-anchor="middle" font-size="11" fill="var(--color-text-secondary)">{h}</text>' for h in (0,6,12,24,36,48)).replace('h<','<')
ax+=f'<text x="{(X0+X1)/2:.0f}" y="{P1B+33:.0f}" text-anchor="middle" font-size="11" fill="var(--color-text-secondary)">超买事件后经过的 4h bar（6 bar ≈ 1 个交易日）</text>'
# 最高点标记
pkA,pkC=23,10
mk=(f'<line x1="{x(pkA):.0f}" y1="{P1T-4:.0f}" x2="{x(pkA):.0f}" y2="{P1B:.0f}" stroke="#56B4E9" stroke-width="1" stroke-dasharray="3,3"/>'
    f'<text x="{x(pkA):.0f}" y="{P1T-8:.0f}" text-anchor="middle" font-size="10.5" fill="#56B4E9">A 中位峰 +23 bar</text>'
    f'<line x1="{x(pkC):.0f}" y1="{P1T-4:.0f}" x2="{x(pkC):.0f}" y2="{P1B:.0f}" stroke="#E69F00" stroke-width="1" stroke-dasharray="3,3"/>'
    f'<text x="{x(pkC):.0f}" y="{P1T-24:.0f}" text-anchor="middle" font-size="10.5" fill="#E69F00">C 中位峰 +10 bar</text>')
P2T,P2B=348,450; YM=62.0
def y2(v): return P2B-(v/YM)*(P2B-P2T)
bars=""
for gi,(samp,bx0) in enumerate((("A",74),("C",380))):
    bw=26; gp=10
    bars+=f'<text x="{bx0}" y="{P2T-24:.0f}" font-size="12" font-weight="500" fill="var(--color-text-primary)">{"样本A 富途滚动近月月差（128 日）" if gi==0 else "样本C N−U 跨 2 月（10 个月）"}</text>'
    for k,H in enumerate(("12","24","48")):
        d=PROB[samp][H]
        for pi,(v,col,fill) in enumerate(((d["pc"],"#E69F00","solid"),(d["pb"],"#56B4E9","none"))):
            xx=bx0+k*78+pi*(bw+gp); hh=(v/YM)*(P2B-P2T); yy=P2B-hh
            if fill=="solid": bars+=f'<rect x="{xx}" y="{yy:.0f}" width="{bw}" height="{hh:.1f}" fill="{col}" rx="2"/>'
            else: bars+=f'<rect x="{xx}" y="{yy:.0f}" width="{bw}" height="{hh:.1f}" fill="none" stroke="{col}" stroke-width="1.8" rx="2"/>'
            bars+=f'<text x="{xx+bw/2}" y="{yy-5:.0f}" text-anchor="middle" font-size="10.5" fill="var(--color-text-primary)">{v:.0f}</text>'
        bars+=f'<text x="{bx0+k*78+37}" y="{P2B+16:.0f}" text-anchor="middle" font-size="11" fill="var(--color-text-secondary)">{H}h</text>'
g2="".join(f'<line x1="{X0}" y1="{y2(v):.0f}" x2="{X1}" y2="{y2(v):.0f}" stroke="rgba(255,255,255,0.10)" stroke-width="1"/>'
   f'<text x="{X0-8}" y="{y2(v)+4:.0f}" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">{v:.0f}%</text>' for v in (0,20,40,60))
lg=(f'<rect x="{X0}" y="{P2B+30}" width="13" height="11" fill="#E69F00" rx="2"/><text x="{X0+19}" y="{P2B+40}" font-size="11" fill="var(--color-text-primary)">超买后（条件）</text>'
    f'<rect x="{X0+132}" y="{P2B+30}" width="13" height="11" fill="none" stroke="#56B4E9" stroke-width="1.8" rx="2"/><text x="{X0+151}" y="{P2B+40}" font-size="11" fill="var(--color-text-primary)">任意时点（基准）</text>'
    f'<text x="{X1}" y="{P2B+40}" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">回落定义：月差自事件点下跌 ≥ $1.0</text>')
svg=f'''<svg viewBox="0 0 680 520" width="100%" role="img" xmlns="http://www.w3.org/2000/svg">
<title>4h RSI超买后月差路径：先冲高再回落</title>
<desc>上：超买事件后48bar的平均月差变化路径（含±1SE），两套样本均在+10~23bar先创新高；下：条件概率与基准概率对比</desc>
<text x="12" y="20" font-size="13.5" font-weight="500" fill="var(--color-text-primary)">超买后月差走得更高、再回落 —— 不是"信号即顶"</text>
<text x="12" y="38" font-size="11" fill="var(--color-text-secondary)">事件后平均路径（bar=0 为超买时刻；正值=月差继续走阔）</text>
{band(PA,SA,"#56B4E9",.10)}{pl(PA,"#56B4E9")}{pl(PC,"#E69F00","7,3")}
{mk}{''.join(g)}{ax}
<text x="{X0+8}" y="{P1T+8:.0f}" font-size="11" fill="#56B4E9">样本A 富途滚动近月（n=10）</text>
<text x="{X0+8}" y="{P1T+24:.0f}" font-size="11" fill="#E69F00">样本C N−U 跨2月（n=10）</text>
<text x="12" y="{P2T-46:.0f}" font-size="13.5" font-weight="500" fill="var(--color-text-primary)">条件概率只比"随便挑一个时点"高 4–13pp，且 n=10 不显著（二项 p=0.30–0.57）</text>
{''.join(g2)}{bars}{lg}
</svg>'''
open(r"C:/Users/Administrator/Desktop/stock/Temp/pb_widget.svg","w",encoding="utf-8").write(svg)
print("bytes",len(svg))
