# -*- coding: utf-8 -*-
"""扫描所有报告：相关性图表 y轴单位错配（百分数corr vs 0~1轴）— 修正版"""
import re, os, json, glob

hits = []
for f in sorted(glob.glob('reports/*/index.html')) + sorted(glob.glob('reports/*.html')):
    try:
        html = open(f, encoding='utf-8').read()
    except Exception:
        continue
    axes = re.findall(r"yAxis: Object\.assign\(\{ type: 'value', name: '[^']*', min: ([-\d.]+), max: ([-\d.]+)", html)
    m = re.search(r'const (?:D|DATA) = (\{)', html)
    D = None
    if m:
        try:
            D = json.JSONDecoder().raw_decode(html, m.start(1))[0]
        except Exception:
            pass
    if D is None:
        continue
    vals = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == 'corr' and isinstance(v, list):
                    vals.extend(x for x in v if isinstance(x, (int, float)) and not isinstance(x, bool) and x is not None)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(D)
    if not vals:
        continue
    mx = max(abs(v) for v in vals)
    if not axes:
        continue
    axes_ok = all(float(lo) <= 1 and float(hi) <= 1.2 for lo, hi in axes)
    data_pct = mx > 1.5
    if axes_ok and data_pct:
        hits.append((f, mx))
        print(f'!! {os.path.relpath(f)}: max|corr|={mx:.1f} 轴={axes[0]} -> 折线溢出')
    elif not data_pct:
        pass
    else:
        print(f'?  {os.path.basename(f)}: max|corr|={mx:.1f} 轴={axes[0]}（人工复核）')

print()
print('命中错配报告数:', len(hits))