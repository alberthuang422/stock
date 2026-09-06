# -*- coding: utf-8 -*-
"""在 81 号 KMI 报告 index.html 中插入"相关性分析"章节（⑧ 前后）。
读取 results/kmi_multi_corr.json，生成章节 HTML 并注入：
  1. TOC 加入"⑧ 相关性分析"，原 ⑧⑨ 顺延为 ⑨⑩
  2. HTML 主体插入 id=s8 章节（含 4 基准分阶段表格、滚动相关图、基准走势图、方向拆解表）
  3. 原 s7.3 的"KMI×DGS10 ≈−0.5 未核实引用"更正为实测结论
  4. 原 s8/s9（投资观点、数据来源）id 顺延为 s9/s10，TOC href 同步
静默写盘，不打印。
"""
import os, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "reports", "81_KMI金德摩根深度分析", "index.html")

with open(REPORT, encoding="utf-8") as f:
    html = f.read()

with open(os.path.join(ROOT, "results", "kmi_multi_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

PA = {p["ref_tag"]: p for p in D["pairs"]}

# ---------- 样式补充（相位图 / hl 高亮行） ----------
extra_css = """
.phase{width:100%;height:120px;}
.phase svg text{font-size:10px;fill:#5b6672;}
.sect-title{font-weight:700;color:var(--ink);margin:14px 0 6px;font-size:15px;border-left:4px solid var(--blue);padding-left:8px;}
.hl{background:#f0f7fd;}
.hl2{background:#fdf3e0;}
.excess-hl{background:#e4f4ef;}
"""
html = html.replace("</style>", extra_css + "</style>", 1)

# ---------- 数据序列 ----------
def roll(p):
    pts = [(d["date"], d["corr"] / 100) for d in p["rolling60"] if d["corr"] is not None]
    return {"date": [x[0] for x in pts], "corr": [x[1] for x in pts]}

def norm(p):
    d = p["price"]
    return {"date": [x["date"] for x in d], "sec": [x["sec"] for x in d], "ref": [x["ref"] for x in d]}

roll60 = {k: roll(PA[k]) for k in ["US10Y", "QQQ", "SOXX", "DJI"]}

# ---------- 每个基准的表格块 ----------
C_REF = {"US10Y": "#0072B2", "QQQ": "#E69F00", "SOXX": "#009E73", "DJI": "#CC79A7"}
SHORT = {"US10Y": "美债10Y", "QQQ": "纳指100", "SOXX": "费半", "DJI": "道指"}

def cls(v):
    if v is None:
        return "na"
    return "up" if v > 0 else "dn"

# 语义化阶段行加亮
HL_BLOCKS = {"加速期 (2025-08 以来)": "hl", "高利率平台期 (2023-11~2025-07)": ""}

def block_table(p):
    rows = []
    for b in p["blocks"]:
        if b["n"] == 0:
            continue
        hl = f" class='{HL_BLOCKS.get(b['name'], '')}'"
        sigm = {"sig": "显著", "edge": "边缘", "no": "不显著"}[b["sig"]]
        rows.append(
            f"<tr{hl}><td><b>{b['name']}</b></td>"
            f"<td class='num'>{b['n']}</td>"
            f"<td class='num {cls(b['pearson'])}'>{b['pearson']:+.3f}</td>"
            f"<td class='num'>{b['p_value']:.4f}</td><td>{sigm}</td>"
            f"<td class='num {cls(b['spearman'])}'>{b['spearman']:+.3f}</td>"
            f"<td class='num'>{b['r2']*100:.1f}%</td>"
            f"<td class='num {cls(b['beta'])}'>{b['beta']:+.3f}</td>"
            f"<td class='num'>{b['sec_ret_total']:+.1f}%</td>"
            f"<td class='num'>{b['ref_ret_total']:+.1f}%</td>"
            f"<td class='num {cls(b['excess_ret'])}'>{b['excess_ret']:+.1f}pp</td></tr>")
    ref_unit = "收益变动(bp)" if p["ref_tag"] == "US10Y" else "涨跌"
    header = ("<tr><th>区间</th><th>样本</th><th>Pearson r</th><th>p 值</th><th>显著性</th>"
              "<th>Spearman ρ</th><th>R²</th><th>β</th>"
              f"<th>KMI 涨幅</th><th>基准{ref_unit}</th><th>超额</th></tr>")
    return f"<table>{header}{''.join(rows)}</table>"

# Fisher 摘要
def fisher_str(p):
    fs = p["fishers"]
    if not fs:
        return ""
    out = []
    order = [k for k in fs if "平台期" in k and "加速期" in k] + [k for k in fs if "加息" in k and "加速期" in k]
    for k in order:
        f = fs[k]
        mark = "✅" if f["sig"] else ""
        out.append(f"<span>{k.replace(' (2023-11~2025-07)','').replace(' (2025-08 以来)','')}：z={f['z']} p={f['p_value']} {mark}</span>")
    return f"<div class='note' style='margin-top:6px'>阶段间差异（Fisher z 检验）：{'　'.join(out)}</div>"

def dir_table(p):
    d = p["direction"]
    up, dn, big = d["up"], d["dn"], d["big_n"]
    big_str = f"{d['big_sec_med']:+.2f}%" if d["big_sec_med"] is not None else "—"
    return f"""<table>
<tr><th>基准方向日</th><th>天数</th><th>KMI 当日收益中位</th><th>KMI 上涨天数占比</th></tr>
<tr><td><b>基准上行日</b>（{SHORT[p['ref_tag']]} > 0）</td><td class='num'>{up['n']}</td>
<td class='num {cls(up['sec_med'])}'>{up['sec_med']:+.3f}%</td><td class='num'>{up['win']}%</td></tr>
<tr><td><b>基准下行日</b>（{SHORT[p['ref_tag']]} < 0）</td><td class='num'>{dn['n']}</td>
<td class='num {cls(dn['sec_med'])}'>{dn['sec_med']:+.3f}%</td><td class='num'>{dn['win']}%</td></tr>
<tr><td><b>基准大波动日</b>（|Δ| 超阈值）</td><td class='num'>{big}</td>
<td class='num {cls(d['big_sec_med'])}'>{big_str}</td><td class='num'>—</td></tr>
</table>"""

# ---------- 章节 HTML ----------
sections = []
for tag in ["US10Y", "QQQ", "SOXX", "DJI"]:
    p = PA[tag]
    tag_color = C_REF[tag]
    chart_id = f"corr_roll_{tag}"
    norm_id = f"corr_norm_{tag}" if tag != "US10Y" else None
    if tag == "US10Y":
        lead = ("<p><b>读法</b>：此口径为 <b>KMI 日收益 × DGS10 日变动(bp)</b>——衡量利率<b>变化</b>当天 KMI 的方向敏感度（负值=利率上行日 KMI 承压）。"
                "全期 r≈0.00、各阶段均不显著：<b>日度上 KMI 对利率变动基本免疫</b>，符合其 65% 照付不议合同+低杠杆（3.6×）的基本面特征。"
                "⚠️ 原报告 §7.3 引用的『KMI×DGS10 区间相关 ≈−0.5』为价格<b>水平</b>伪相关（KMI 股价与收益率同向上行的趋势叠加，实为 +0.52），与日变动口径结论相反，本版已更正（见 §7.3）。</p>")
    elif tag == "QQQ":
        lead = ("<p><b>读法</b>：全期 r=0.27 显著正相关（β≈0.27，KMI 曾是『类股指』中游）；但 <b>2025-08 数据中心/LNG 加速期以来 r 反转为 −0.157（p=0.008，显著）</b>，"
                "2026 年 −0.221 进一步走负——KMI 已从『跟涨纳指』切换为『与科技成长此消彼长』。Fisher 检验：平台期→加速期 z=6.86、加息期→加速期 z=7.26，阶段差异 p<0.001，为全报告最强结构断裂。</p>")
    elif tag == "SOXX":
        lead = ("<p><b>读法</b>：全期 r=0.22 显著正相关（β 仅 0.13，弹性弱于 QQQ——半导体与防御型中游本就联动浅）；加速期 r=−0.104（p=0.08，边缘），"
                "2026 年 −0.158（p=0.039，显著）。Fisher 检验两段断裂均 p<0.001。KMI 与半导体呈『温和反周期』——费半大起大落时 KMI 反而相对抗跌（低 β + 类债属性）。</p>")
    else:
        lead = ("<p><b>读法</b>：道指是 KMI 的历史主锚——全期 r=0.43（β≈0.65），加息期最高达 0.55（β 0.82）；但加速期 r 崩塌至 −0.048（不显著），"
                "Fisher 检验 z=7.37 / 9.04（p<0.001）：<b>KMI 已从『道指高 β 中游』脱钩</b>，股价驱动让位于自身项目积压（$9.6B）与电力/LNG 叙事，与道指（金融+工业周期）的相关性被结构性稀释。</p>")
    norm_html = ""
    if norm_id:
        norm_html = f'<div class="card"><h3>KMI 与 {SHORT[tag]} 归一化走势（{p["period"]["start"]} → {p["period"]["end"]}）</h3><div id="{norm_id}" class="chart-sm"></div>' \
                    f'<p class="note">100 起点归一；趋势同向≠相关性（存在伪相关风险），以 60 日滚动 r 为准。</p></div>'
    sections.append(f"""
<div class="card">
<h3>KMI × {SHORT[tag]}（{p['ref_label']}）</h3>
{lead}
{block_table(p)}
{fisher_str(p)}
</div>
<div class="card"><h3>60 日滚动相关系数</h3><div id="{chart_id}" class="chart"></div>
<p class="note">滚动窗 60 交易日；阴影区：加息周期（~2023-10）/ 高利率平台期（2023-11~2025-07）/ 加速期（2025-08~）。虚线为皮尔逊 r 显著阈值（|r|>0.25，n≈60）。</p></div>
{norm_html}
<div class="card"><h3>方向拆解（全期 2021-08 以来）</h3>{dir_table(p)}</div>
""")

section_html = f"""
<h2 id="s8">⑧ 相关性分析（本次新增）</h2>
<div class="card" style="border-left:5px solid var(--vermil)">
<b>核心结论</b>：KMI×US10Y 日度相关 ≈0（利率免疫）；KMI×道指全期 0.43 为唯一强正相关但已脱钩（加速期 −0.05 不显著）；KMI×QQQ/SOXX 于 2025-08 起由正转负（QQQ 最显著，Fisher p<0.001），<b>2025-08 是 KMI 市场联动结构的分水岭</b>——从此 KMI 主要由自身项目积压与电力/LNG 叙事驱动，而非股指 β。
</div>
{''.join(sections[:4])}
<hr>
<h3 style="margin-top:22px">补充：价格水平口径核验（对照 §7.3 历史引用）</h3>
<div class="card">
<p>原报告引用『KMI×DGS10 区间相关 ≈−0.5（未单独重跑，方向性参考）』，本版实际重跑（2021-08 以来，n=1252）：</p>
<table>
<tr><th>口径</th><th>Pearson</th><th>说明</th></tr>
<tr><td>KMI 价格水平 × DGS10 水平</td><td class="num up">+0.523</td><td>趋势伪相关——两序列各自 2021→2026 同向上行所致，无因果意义</td></tr>
<tr><td>KMI 日收益 × DGS10 日变动(bp)</td><td class="num">+0.004</td><td>有效口径：日度敏感度≈0，不显著</td></tr>
</table>
<p class="note">结论<b>更正</b>：KMI 对利率是『水平免疫、估值倍数敏感』——10Y 上行压估值倍数（§7.3 的 0.5–1× EV/EBITDA 折价机制仍成立），但日度股价对利率变化无明显反应；原『≈−0.5』引用与实测方向相反，予以废弃。</p>
</div>
"""

# 插入位置：原 <h2 id="s8">⑧ 投资观点 之前
html = html.replace('<h2 id="s8">⑧ 投资观点</h2>', section_html + '<h2 id="s9">⑨ 投资观点</h2>', 1)
# 原 s9 -> s10（数据来源）
html = html.replace('<h2 id="s9">⑨ 数据来源与时效性</h2>', '<h2 id="s10">⑩ 数据来源与时效性</h2>', 1)

# ---------- TOC 更新 ----------
old_toc = ('<a href="#s7">⑦ 宏观与能源政策</a><a href="#s8">⑧ 投资观点</a><a href="#s9">⑨ 数据来源与时效</a>')
new_toc = ('<a href="#s7">⑦ 宏观与能源政策</a><a href="#s8">⑧ 相关性分析</a>'
           '<a href="#s9">⑨ 投资观点</a><a href="#s10">⑩ 数据来源与时效</a>')
if old_toc in html:
    html = html.replace(old_toc, new_toc, 1)
else:
    # 容错：TOC 可能已含其他结构
    html = re.sub(r'(<a href="#s8">⑧ 投资观点</a>)(<a href="#s9">⑨ 数据来源与时效</a>)',
                  '<a href="#s8">⑧ 相关性分析</a><a href="#s9">⑨ 投资观点</a><a href="#s10">⑩ 数据来源与时效</a>', html, count=1)
    html = re.sub(r'(<a href="#s7">⑦ 宏观与能源政策</a>)',
                  r'\1<a href="#s8">⑧ 相关性分析</a>', html, count=1)

# ---------- §7.3 更正 ----------
old_73 = '<p>中游资产久期长（合同 10–20 年），股价对 10Y 高度敏感（本报告引用历史观测：KMI×DGS10 区间相关约 −0.5，<b>未单独重跑、方向性参考</b>）。对冲项：'
new_73 = ('<p>中游资产久期长（合同 10–20 年），估值对 10Y 高度敏感。本报告已实测（§8，2021-08 以来 n=1252）：'
          '<b>KMI×DGS10 日变动相关 ≈0（不显著）</b>——股价日度对利率变化免疫；价格水平口径的 +0.52 为趋势伪相关，'
          '原「区间相关约 −0.5、未重跑」引用废弃。真正的利率传导在估值倍数（10Y 上行 100bp 压缩 EV/EBITDA 约 0.5–1×）。对冲项：')
if old_73 in html:
    html = html.replace(old_73, new_73, 1)

# ---------- 数据来源表新增行 ----------
old_src = '<tr><td>行业/政策（EIA、FERC、EPA、关税）</td>'
new_src = ('<tr><td>相关性分析（KMI × US10Y/QQQ/SOXX/DJI）</td><td>本地日线 + FRED DGS10，60 日滚动</td><td>截至 2026-09-03 收盘</td></tr>\n'
           '<tr><td>行业/政策（EIA、FERC、EPA、关税）</td>')
if old_src in html:
    html = html.replace(old_src, new_src, 1)

# ---------- 注入 JS：滚动相关图 + 归一化走势图 ----------
roll_chart_js = []
for tag in ["US10Y", "QQQ", "SOXX", "DJI"]:
    d = roll60[tag]
    seg_colors = ["rgba(0,114,178,0.06)", "rgba(230,159,0,0.06)", "rgba(0,158,115,0.06)"]
    roll_chart_js.append(f"""
(function(){{
  var el = document.getElementById('corr_roll_{tag}');
  if(!el) return;
  var ch = echarts.init(el);
  var dates = {json.dumps(d['date'], ensure_ascii=False)};
  var vals = {json.dumps(d['corr'], ensure_ascii=False)};
  var markAreas = [
    {{name:'加息周期',xAxis:'2021-08-25',itemStyle:{{color:'rgba(0,114,178,0.07)'}}}},
    {{name:'利率平台',xAxis:'2023-11-01',itemStyle:{{color:'rgba(230,159,0,0.07)'}}}},
    {{name:'加速期',xAxis:'2025-08-01',itemStyle:{{color:'rgba(0,158,115,0.07)'}}}}
  ];
  ch.setOption({{
    tooltip:{{trigger:'axis',valueFormatter:function(v){{return v==null?'—':v.toFixed(2);}}}},
    grid:{{left:48,right:20,top:30,bottom:28}},
    xAxis:{{type:'category',data:dates,boundaryGap:false,axisLabel:{{interval:Math.floor(dates.length/6)}}}},
    yAxis:{{type:'value',min:-1,max:1,splitLine:{{lineStyle:{{type:'dashed'}}}},
           axisLabel:{{formatter:function(v){{return v.toFixed(1);}}}}}},
    series:[
      {{type:'line',data:vals,smooth:true,symbol:'none',lineStyle:{{color:'{C_REF[tag]}',width:2}},
       markArea:{{silent:true,data:[
         [markAreas[0],{{xAxis:'2023-10-31'}}],
         [markAreas[1],{{xAxis:'2025-07-31'}}],
         [markAreas[2],{{xAxis:dates[dates.length-1]}}]
       ]}},
       markLine:{{silent:true,symbol:'none',data:[
         {{yAxis:0,lineStyle:{{color:'#9a948a',type:'dashed'}}}},
         {{yAxis:0.25,lineStyle:{{color:'#9a948a',type:'dotted'}},label:{{formatter:'r=0.25'}}}},
         {{yAxis:-0.25,lineStyle:{{color:'#9a948a',type:'dotted'}},label:{{formatter:'r=-0.25'}}}}
       ]}}
      }}
    ]
  }});
  window.addEventListener('resize', function(){{ch.resize();}});
}})();
""")

norm_chart_js = []
for tag in ["QQQ", "SOXX", "DJI"]:
    d = norm(PA[tag])
    norm_chart_js.append(f"""
(function(){{
  var el = document.getElementById('corr_norm_{tag}');
  if(!el) return;
  var ch = echarts.init(el);
  ch.setOption({{
    tooltip:{{trigger:'axis'}},
    legend:{{data:['KMI','{SHORT[tag]}']}},
    grid:{{left:48,right:20,top:32,bottom:28}},
    xAxis:{{type:'category',data:{json.dumps(d['date'], ensure_ascii=False)},boundaryGap:false,axisLabel:{{interval:Math.floor({len(d['date'])}/6)}}}},
    yAxis:{{type:'value',name:'指数(100)'}},
    series:[
      {{name:'KMI',type:'line',data:{json.dumps(d['sec'], ensure_ascii=False)},smooth:true,symbol:'none',lineStyle:{{color:'{C_REF[tag]}',width:2}}}},
      {{name:'{SHORT[tag]}',type:'line',data:{json.dumps(d['ref'], ensure_ascii=False)},smooth:true,symbol:'none',lineStyle:{{color:'#9a948a',width:1.5,dash:[4,3]}}}}
    ]
  }});
  window.addEventListener('resize', function(){{ch.resize();}});
}})();
""")

js_block = "\n" + "\n".join(roll_chart_js + norm_chart_js) + "\n"
# 注入到 resize 监听之前
html = html.replace("window.addEventListener('resize', function(){ [c1,c2,c3,c4,c5,c6].forEach(function(ch){ch.resize();}); });",
                    "window.addEventListener('resize', function(){ [c1,c2,c3,c4,c5,c6].forEach(function(ch){ch.resize();}); });\n" + js_block, 1)

# ---------- 首页 meta 与页脚更新 ----------
html = html.replace("81 · KMI 金德摩根全面深度分析 ｜ 报告日 2026-09-06 ｜ 数据截至 2026-09-04 收盘 ｜ 由 WorkBuddy 生成",
                    "81 · KMI 金德摩根全面深度分析 ｜ 报告日 2026-09-06 ｜ 数据截至 2026-09-04 收盘（相关性章节截至 2026-09-03）｜ 由 WorkBuddy 生成", 1)

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(html)
print("updated:", REPORT)