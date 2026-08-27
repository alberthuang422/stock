# -*- coding: utf-8 -*-
"""生成 reports/45_震荡市板块独立行情/index.html（读取 scripts/_45_data.json）
ECharts CDN；corr÷100 已在数据层保证 0~1；浅底深字；Okabe-Ito；明细独立tab。
只 print written: path size。"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(HERE, '..')
D = json.load(open(os.path.join(HERE, '_45_data.json'), encoding='utf-8'))
outdir = os.path.join(root, 'reports', '45_震荡市板块独立行情')
os.makedirs(outdir, exist_ok=True)

# Okabe-Ito 色板（色弱安全）
PAL = ['#0072B2','#E69F00','#56B4E9','#009E73','#CC79A7','#D55E00','#F0E442','#000000',
       '#0072B2','#E69F00','#56B4E9']
SECTORS = [c['sector'] for c in D['cur']]

DATA = json.dumps(D, ensure_ascii=False)

def cur_rows():
    r = ''
    for c in D['cur']:
        lab = c['label']
        cls = {'强势独立上涨':'s-up','弱势独立下跌':'s-dn','高波动跟随':'s-hv','跟随震荡':'s-fl'}.get(lab,'s-mid')
        up = '▲' if c['ret'] > 0 else ('▼' if c['ret'] < 0 else '')
        r += (f"<tr><td class='tk'>{c['sector']}</td>"
              f"<td class='num {'pos' if c['ret']>0 else 'neg'}'>{c['ret']:+.1f}% {up}</td>"
              f"<td class='num'>{c['ger']:.2f}</td>"
              f"<td class='num'>{('%.2f'%c['uper']) if c['uper'] is not None else '—'}<span class='n'>n{c['nup']}</span></td>"
              f"<td class='num'>{('%.2f'%c['dner']) if c['dner'] is not None else '—'}<span class='n'>n{c['ndn']}</span></td>"
              f"<td class='num'>{c['ep05']}</td><td class='num'>{c['er20']:.2f}</td>"
              f"<td class='num'>{c['hv']:.1f}</td><td class='num'>{c['sc']:.2f}</td><td class='num'>{c['c60']:.2f}</td>"
              f"<td class='lab {cls}'>{lab}</td></tr>")
    return r

def cont_rows():
    from collections import OrderedDict
    order = ['强势独立上涨','弱势独立下跌','跟随震荡']
    by = OrderedDict()
    for row in D['cont']:
        by.setdefault(row['标签'], []).append(row)
    out = ''
    for lab in order:
        rows = by.get(lab, [])
        for i, row in enumerate(rows):
            first = f"<td rowspan='{len(rows)}' class='lab'>{'<b>'+lab+'</b>' if lab!='跟随震荡' else lab+'(对照)'}</td>" if i == 0 else ''
            def cell(v, pp=False, tcol=False):
                if v == '—' or v is None: return "<td class='num'>—</td>"
                if tcol:
                    strong = abs(v) >= 2
                    return f"<td class='num {'sig' if strong else ''}'>{v}</td>"
                if pp:
                    return f"<td class='num {'pos' if v>0 else 'neg'}'>{v:+.2f}</td>"
                return f"<td class='num'>{v}</td>"
            out += (f"<tr>{first}<td class='num'>{row['T']}</td><td class='num'>{row['n']}</td>"
                    + cell(row['mean'], pp=True) + cell(row['med'], pp=True)
                    + cell(row['win']) + cell(row['t'], tcol=True)
                    + cell(row['bp']) + cell(row['tc'], tcol=True) + "</tr>")
    return out

def freq_rows():
    out = ''
    for c in D['freq']:
        tf = c['倾向频次']
        tfs = f"{tf*100:.0f}%" if tf is not None else '—'
        bar = f"<div class='bar'><div style='width:{0 if tf is None else tf*100/0.5*100:.0f}%'></div></div>" if tf else ''
        out += (f"<tr><td class='tk'>{c['sector']}</td><td class='num'>{c['主口径切片数']}</td>"
                f"<td class='num'>{c['独立次数']}</td><td class='num sig'>{tfs}</td>"
                f"<td class='num'>{c['强势次数']}</td><td class='num'>{c['弱势次数']}</td>"
                f"<td class='num'>{c['稳健次数']}</td>"
                f"<td class='num'>{c['EP05中位'] if c['EP05中位'] is not None else '—'}</td>"
                f"<td class='num'>{('%.1f%%'%c['区间涨跌中位']) if c['区间涨跌中位'] is not None else '—'}</td>"
                f"<td class='num faint'>{c['早期独立次数']}/{c['早期切片数']}</td></tr>")
    return out

def slice_rows():
    out = ''
    for s in D['slices']:
        out += (f"<div class='gantt-row'><div class='g-meta'><b>{s['id']}</b> "
                f"<span>{s['start']}~{s['end']}</span> <span class='n'>{s['length']}日</span> "
                f"SPY {s['spy']:+.1f}% ER{s['er']:.2f} 回撤{s['mdd']:.0f}%</div>"
                f"<div class='g-cells'>")
        for c in D['cur']:
            sec = c['sector']
            lab = s['labs'].get(sec, '')
            key = {'强势独立上涨':'U','弱势独立下跌':'D','高波动跟随':'H','跟随震荡':'F'}.get(lab,'')
            title = f"{sec}: {lab or '无数据'}"
            out += f"<span class='gc gc-{key}' title='{title}'>{sec.replace('XL','')}</span>"
        out += "</div></div>"
    return out

def detail_rows():
    out = ''
    for r in D['detail']:
        lab = r['标签']; cls = {'强势独立上涨':'s-up','弱势独立下跌':'s-dn','高波动跟随':'s-hv','跟随震荡':'s-fl'}.get(lab,'s-mid')
        def n(v): return '—' if v is None or (isinstance(v,float) and v!=v) else (f"{v:.2f}" if isinstance(v,float) else v)
        out += (f"<tr><td>{r['slice_id']}</td><td>{r['start']}</td><td>{r['end']}</td>"
                f"<td class='tk'>{r['sector']}</td><td class='num'>{n(r['区间涨跌pct'])}</td>"
                f"<td class='num'>{n(r['EP05'])}</td><td class='num'>{n(r['EP06'])}</td>"
                f"<td class='num'>{n(r['全局ER'])}</td><td class='num'>{n(r['上行ER'])}</td><td class='num'>{n(r['下行ER'])}</td>"
                f"<td class='num'>{n(r['n_up'])}</td><td class='num'>{n(r['n_dn'])}</td>"
                f"<td class='num'>{n(r['corr60均值'])}</td><td class='num'>{n(r['corr60最低'])}</td>"
                f"<td class='num'>{n(r['HV20'])}</td>"
                f"<td class='num'>{n(r['标签th3'])}</td><td class='num'>{n(r['标签th8'])}</td>"
                f"<td class='lab {cls}'>{lab}</td></tr>")
    return out

spy_chg = D['spy_chg']; ret_th = D['ret_th']
NS = D['说明']
# 强势独立上涨组 t聚类（T+20/60/120）
def cont_cell(lab, T, field):
    for r in D['cont']:
        if r['标签'] == lab and r['T'] == T: return r.get(field)
    return None
t20 = cont_cell('强势独立上涨','T+20','tc'); t60 = cont_cell('强势独立上涨','T+60','tc'); t120 = cont_cell('强势独立上涨','T+120','tc')
m20 = cont_cell('强势独立上涨','T+20','mean'); m120 = cont_cell('强势独立上涨','T+120','mean')

HTML = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>45 · 震荡市板块独立行情回测</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{{--bg:#f7f8fa;--card:#fff;--ink:#1a2028;--sub:#5b6672;--line:#e3e7ec;--acc:#0072B2;
--up:#D55E00;--dn:#009E73;--warn:#E69F00}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:26px;margin:0 0 4px}} .h1sub{{color:var(--sub);font-size:14px;margin-bottom:22px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px 24px;margin:18px 0;box-shadow:0 1px 3px rgba(20,30,40,.04)}}
h2{{font-size:19px;margin:0 0 14px;padding-left:11px;border-left:4px solid var(--acc)}}
h3{{font-size:16px;margin:20px 0 10px;color:var(--ink)}}
.concl{{background:#eef4fb;border-left:4px solid var(--acc);padding:16px 20px;border-radius:0 8px 8px 0;margin:10px 0}}
.concl b{{color:var(--acc)}}
.kpis{{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0}}
.kpi{{flex:1;min-width:150px;background:#fbfcfd;border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.kpi .v{{font-size:23px;font-weight:700;color:var(--acc)}} .kpi .l{{font-size:12.5px;color:var(--sub)}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}}
th,td{{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}}
th{{background:#f0f3f7;font-weight:600;color:#33414f;font-size:12.5px;position:sticky;top:0}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}} td.tk{{font-weight:700;color:var(--acc)}}
.pos{{color:var(--up)}} .neg{{color:var(--dn)}} .n{{color:var(--sub);font-size:11px;margin-left:3px}}
.faint{{color:var(--sub)}} .sig{{font-weight:700;color:#b3001b}}
td.lab{{font-weight:600}} .s-up{{color:var(--up)}} .s-dn{{color:var(--dn)}}
.s-hv{{color:#CC79A7}} .s-fl{{color:var(--sub)}} .s-mid{{color:#8a94a0}}
.tabs{{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 4px}}
.tab-btn{{padding:8px 16px;border:1px solid var(--line);background:#fff;border-radius:8px;cursor:pointer;font-size:14px;color:var(--sub)}}
.tab-btn.on{{background:var(--acc);color:#fff;border-color:var(--acc);font-weight:600}}
.pane{{display:none}} .pane.on{{display:block}}
.chart{{width:100%;height:360px}} .chart.tall{{height:440px}}
.note{{font-size:12.5px;color:var(--sub);margin-top:8px;line-height:1.6}}
.gantt-row{{margin:7px 0;display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.g-meta{{font-size:12px;color:var(--sub);width:100%;margin-bottom:2px}}
.g-cells{{display:flex;gap:3px}}
.gc{{width:34px;height:26px;line-height:26px;text-align:center;font-size:11px;font-weight:700;border-radius:4px;background:#eef1f4;color:#98a2ad}}
.gc-U{{background:var(--up);color:#fff}} .gc-D{{background:var(--dn);color:#fff}}
.gc-H{{background:#CC79A7;color:#fff}} .gc-F{{background:#cfd8e0;color:#33414f}}
.legend{{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--sub);margin:8px 0}}
.legend i{{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;margin-right:5px}}
.tbl-scroll{{max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:8px}}
.tag{{display:inline-block;background:#eef4fb;color:var(--acc);border-radius:5px;padding:1px 8px;font-size:12px;margin-right:6px}}
.warn-box{{background:#fdf3e6;border-left:4px solid var(--warn);padding:14px 18px;border-radius:0 8px 8px 0;margin:12px 0;font-size:14px}}
code{{background:#eef1f4;padding:1px 6px;border-radius:4px;font-size:12.5px}}
</style></head><body><div class="wrap">

<h1>震荡市板块独立行情回测</h1>
<div class="h1sub">大盘横盘期，哪些行业板块天然能走出独立流畅单边？独立行情能走多久？确认后追入有无超额？ · 1998 年以来 SPY 横盘切片 · 11 个 SPDR 板块 · 报告 45 · 2026-08</div>

<div class="card">
<h2>一、结论先行</h2>
<div class="concl">
<p><b>1. 震荡市里"独立流畅单边"是稀有事件，且天然分化不显著。</b>1998 年以来共识别 <b>16 段横盘切片（2010 后非 ongoing 主口径 {D['说明']['主口径切片数']} 段）</b>；bootstrap 500 等长随机窗口基线显示，绝大多数真实横盘切片的"独立标签板块数"落在随机基线范围内（经验 p 值多在 0.3~1.0）——<b>横盘≠必然板块分化</b>。</p>
<p><b>2. 唯一有稳定"独立倾向"的板块是 XLE（能源）。</b>主口径切片中 XLE 打出独立标签 <b>5/11 次（45%）</b>，为全表最高，且 4 次为三档阈值方向一致的"稳健"判定；本期 2025-11~2026-02 XLE +28% / corr60 0.17、2014-2016 能源独立行情等反复重现。XLC（通信）/XLP（必需消费）次之但样本少。</p>
<p><b>3. 独立行情"确认后追入"存在正向延续超额，持有期越长越显著。</b>被标"强势独立上涨"的板块自确认日（EP05≥5 首日）起，T+20 超额 SPY +1.72pp（胜率 80%）、T+60 +2.67pp、T+120 +10.55pp。切片 block bootstrap 聚类后 t 值 <b>T+20 {t20}（未过 2）/ T+60 {t60} / T+120 {t120}</b>——即短周期不显著、长周期越过 2。但<b>事件仅 {NS['事件数']} 个、覆盖 6 切片，对照"跟随震荡"组同持有期均值仅 +0.33/−0.73/−1.23pp（不显著）</b>，两组差随持有期拉大方向合理，但小样本下 T+120 显著性须视为<b>上限证据</b>而非确证。</p>
<p><b>4. 本期（2025-11~2026-02）复算确认</b>：XLE +{[c['ret'] for c in D['cur'] if c['sector']=='XLE'][0]:.0f}% / XLP +{[c['ret'] for c in D['cur'] if c['sector']=='XLP'][0]:.0f}% / XLB +{[c['ret'] for c in D['cur'] if c['sector']=='XLB'][0]:.0f}% 强势独立上涨；XLK 静态 corr 0.90、HV 全表最高 → 高波动跟随（非独立）。标签体系与文档预期一致（回归校验通过）。</p>
</div>
<div class="warn-box">⚠️ 本框架是<b>事后统计倾向，非实时可交易信号</b>——切片靠 120/60 日回看划定、确认日依赖 EP05 平台确立，均含前瞻。延续收益 t 值未过显著线时不硬解释（评审纪律）。</div>
<div class="kpis">
<div class="kpi"><div class="v">16</div><div class="l">历史横盘切片（1998 起）</div></div>
<div class="kpi"><div class="v">{ret_th}%</div><div class="l">区间涨跌标签阈值（75分位校准冻结）</div></div>
<div class="kpi"><div class="v">XLE 45%</div><div class="l">最高独立倾向频次（主口径）</div></div>
<div class="kpi"><div class="v">+10.6pp</div><div class="l">独立上涨 T+120 超额（t聚类{t120}）</div></div>
</div>
</div>

<div class="tabs">
<button class="tab-btn on" data-p="p1">本期打分</button>
<button class="tab-btn" data-p="p2">历史切片地图</button>
<button class="tab-btn" data-p="p3">板块倾向频次</button>
<button class="tab-btn" data-p="p4">延续收益</button>
<button class="tab-btn" data-p="p5">事件明细</button>
<button class="tab-btn" data-p="p6">口径与局限</button>
</div>

<div class="pane on" id="p1">
<div class="card">
<h2>二、本期（2025-11-03 ~ 2026-02-27，80 交易日）板块打分表</h2>
<p class="note">SPY 区间 {spy_chg:+.2f}%（横盘基准，全局 ER≈0.02）。红涨绿跌；上行/下行 ER 后 <code>n</code> 为波段数，n&lt;3 时降级仅用滚动 ER 平台。</p>
<table><thead><tr><th>板块</th><th>区间涨跌</th><th>全局ER</th><th>上行ER</th><th>下行ER</th><th>EP05(天)</th><th>ER20峰</th><th>HV20</th><th>静态corr</th><th>corr60均值</th><th>标签</th></tr></thead>
<tbody>{cur_rows()}</tbody></table>
<div class="legend"><span><i style="background:var(--up)"></i>强势独立上涨</span><span><i style="background:var(--dn)"></i>弱势独立下跌</span><span><i style="background:#CC79A7"></i>高波动跟随</span><span><i style="background:#cfd8e0"></i>跟随震荡</span></div>
</div>
<div class="card">
<h2>本期滚动 ER20 与 60 日相关时序</h2>
<div id="ch_er" class="chart"></div>
<div id="ch_cr" class="chart"></div>
<p class="note">左：ER20（越高越"流畅单边"），XLP 平台持续最长（EP05=11 天）；右：与 SPY 的 60 日滚动相关，XLE/XLP 相关向 0 附近坍缩 = 脱钩独立，XLK 维持 ~0.89 = 高 β 跟随下跌。</p>
</div>
</div>

<div class="pane" id="p2">
<div class="card">
<h2>三、1998 年以来 SPY 横盘切片地图</h2>
<p class="note">每行一个切片；格内为板块代码前缀（B/C/E/F/I/K/P/R/U/V/Y），颜色=该切片内该板块标签。灰=无数据（XLRE 2015、XLC 2018 才上市）。S16=本期。</p>
<div class="legend"><span><i style="background:var(--up)"></i>独立上涨</span><span><i style="background:var(--dn)"></i>独立下跌</span><span><i style="background:#CC79A7"></i>高波动跟随</span><span><i style="background:#cfd8e0"></i>跟随震荡</span><span><i style="background:#eef1f4"></i>无数据</span></div>
{slice_rows()}
</div>
</div>

<div class="pane" id="p3">
<div class="card">
<h2>四、板块独立倾向频次（主口径 = 2010 后非 ongoing 切片）</h2>
<div id="ch_freq" class="chart"></div>
<table><thead><tr><th>板块</th><th>参与切片</th><th>独立次数</th><th>倾向频次</th><th>强势</th><th>弱势</th><th>稳健</th><th>EP05中位</th><th>独立区间涨跌中位</th><th>2010前</th></tr></thead>
<tbody>{freq_rows()}</tbody></table>
<p class="note">倾向频次 = 独立标签次数 / 参与切片数；XLE 明显领先。2010 前切片单列稳健性（行业拆分前可比性弱）。</p>
</div>
</div>

<div class="pane" id="p4">
<div class="card">
<h2>五、延续收益事件研究（确认日 → T+N 相对 SPY 超额）</h2>
<p class="note">T+N 一律<b>交易日</b>。事件组=切片内被标独立方向且 EP05≥5 触发确认日的板块；对照组=同逻辑"跟随震荡"板块。t聚类 = 切片 block bootstrap(2000次)，显著性为上限。</p>
<table><thead><tr><th>组别</th><th>持有</th><th>n</th><th>均值(pp)</th><th>中位(pp)</th><th>胜率%</th><th>t(独立)</th><th>二项p</th><th>t(聚类)</th></tr></thead>
<tbody>{cont_rows()}</tbody></table>
<div id="ch_cont" class="chart"></div>
<div class="warn-box">独立上涨组均值/胜率随持有期递增（T+20 +1.7pp → T+120 +10.6pp，胜率 80%），方向一致；聚类 t 值 T+60（{t60}）、T+120（{t120}）越过 2，但 T+20（{t20}）未过，且事件仅 {NS['事件数']} 个跨 6 切片——<b>长周期呈弱显著、短周期不显著，如实报告为"正向、幅度随持有期放大，但小样本上限证据"</b>，不构成确证的交易信号。</div>
</div>
</div>

<div class="pane" id="p5">
<div class="card">
<h2>六、全部切片 × 板块打分明细（{len(D['detail'])} 行）</h2>
<p class="note">含 th=3%/8% 敏感性标签。缺失板块不在此表（切片早于其上市）。上行/下行 ER 空 = 该方向无波段(n=0)。</p>
<div class="tbl-scroll"><table><thead><tr><th>切片</th><th>起</th><th>止</th><th>板块</th><th>涨跌%</th><th>EP05</th><th>EP06</th><th>全局ER</th><th>上行ER</th><th>下行ER</th><th>n_up</th><th>n_dn</th><th>corr60均值</th><th>corr60最低</th><th>HV20</th><th>th3标签</th><th>th8标签</th><th>标签</th></tr></thead>
<tbody>{detail_rows()}</tbody></table></div>
</div>
</div>

<div class="pane" id="p6">
<div class="card">
<h2>七、口径、方法与局限</h2>
<h3>切片识别（find_choppy_slices.py）</h3>
<p>逐日标记"震荡态"= 滚动窗口 SPY 同时满足 ①全局 ER&lt;0.15 ②累计涨跌 ∈±5% ③最大回撤&gt;−12%。<b>双口径 120 日或 60 日</b>（纯 120 日会吸入前段单边行情，2025-11~2026-02 无法命中，故加 60 日回看，属文档 §5 决策规则内放宽）。连续震荡日间隔&lt;20 合并、边界外扩 10 日、裁边使整体|涨跌|≤5%、长度&lt;80 丢弃；非极大值抑制（ER 最低者优先、重叠&lt;50%）；剔除 2020-02~12 疫情年。<b>共 16 段</b>，平均 {sum(s['length'] for s in D['slices'])//16} 交易日。</p>
<h3>打分与标签（sector_wave_er.py 修正版）</h3>
<p>ZigZag（pending 确认机制，th 分档：切片&lt;120→3%，否则 5%，敏感性 3/5/8）拆波段；ER=|净变动|/路径长。滚动 ER20 平台 EP05/06 = ER&gt;阈值连续天数。相关性用日收益 60 日滚动。<b>标签=方向×流畅度二维矩阵</b>，n&lt;3 降级用滚动平台兜底。区间涨跌阈值 8% → 用全切片 |涨跌| 75 分位<b>校准为 {ret_th}% 并冻结</b>。</p>
<h3>三大局限</h3>
<p>① <b>统计独立性高估</b>：切片可能重叠、同切片多板块非独立 → 聚类修正 + t 标注为上限。② <b>构成偏差</b>：XLRE(2015)/XLC(2018) 上市晚、2015 前后行业拆分，主口径限 2010 后。③ <b>路径敏感 + 前瞻</b>：同一行情 th 不同结论可翻转（用三档一致性标"稳健/临界"）；切片与确认日皆事后划定，非实时信号。</p>
<p class="note">数据：data/spy 及 11 个 XL* 日线 adj_close（Yahoo，止 2026-08-26）。脚本：find_choppy_slices.py / scan_sector_independence.py / independence_persistence.py / build_45_*.py。结果：results/choppy_slices.csv、sector_independence_scan.csv、independence_stats.json、continuation_trades.csv。</p>
</div>
</div>

</div>
<script>
const D = {DATA};
const PAL = {json.dumps(PAL)};
document.querySelectorAll('.tab-btn').forEach(b=>b.onclick=()=>{{
  document.querySelectorAll('.tab-btn').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); document.getElementById(b.dataset.p).classList.add('on');
  Object.values(CH).forEach(c=>c&&c.resize());
}});
const CH = {{}};
function init() {{
  if(!window.echarts){{ setTimeout(init,120); return; }}
  // ER20 时序
  CH.er = echarts.init(document.getElementById('ch_er'));
  CH.er.setOption({{
    title:{{text:'滚动 ER20（流畅度）',left:8,top:4,textStyle:{{fontSize:14,color:'#33414f'}}}},
    tooltip:{{trigger:'axis',confine:true}}, legend:{{type:'scroll',bottom:0,textStyle:{{fontSize:11}}}},
    grid:{{top:34,left:44,right:18,bottom:52}},
    xAxis:{{type:'category',data:D.dates,axisLabel:{{fontSize:10,color:'#5b6672'}}}},
    yAxis:{{type:'value',min:0,max:1,axisLabel:{{formatter:'{{value}}'}}}},
    series:D.cur.map((c,i)=>({{name:c.sector,type:'line',smooth:true,showSymbol:false,lineStyle:{{width:c.sector==='XLE'||c.sector==='XLP'||c.sector==='XLK'?2.4:1.2,color:PAL[i%PAL.length]}},emphasis:{{focus:'series'}},data:D.er[c.sector]}}))
  }});
  // corr60 时序
  CH.cr = echarts.init(document.getElementById('ch_cr'));
  CH.cr.setOption({{
    title:{{text:'60 日滚动相关系数 vs SPY（0=脱钩）',left:8,top:4,textStyle:{{fontSize:14,color:'#33414f'}}}},
    tooltip:{{trigger:'axis',confine:true}}, legend:{{type:'scroll',bottom:0,textStyle:{{fontSize:11}}}},
    grid:{{top:34,left:44,right:18,bottom:52}},
    xAxis:{{type:'category',data:D.dates,axisLabel:{{fontSize:10,color:'#5b6672'}}}},
    yAxis:{{type:'value',min:-1,max:1}},
    series:D.cur.map((c,i)=>({{name:c.sector,type:'line',smooth:true,showSymbol:false,lineStyle:{{width:c.sector==='XLE'||c.sector==='XLP'||c.sector==='XLK'?2.4:1.2,color:PAL[i%PAL.length]}},emphasis:{{focus:'series'}},data:D.cr[c.sector]}}))
      .concat([{{name:'0线',type:'line',data:D.dates.map(()=>0),showSymbol:false,lineStyle:{{width:1,color:'#cfd8e0',type:'dashed'}},tooltip:{{show:false}},legendHoverLink:false}}])
  }});
  // 倾向频次柱
  CH.freq = echarts.init(document.getElementById('ch_freq'));
  CH.freq.setOption({{
    tooltip:{{trigger:'axis'}}, grid:{{top:20,left:44,right:18,bottom:36}},
    xAxis:{{type:'category',data:D.freq.map(c=>c.sector),axisLabel:{{fontSize:11}}}},
    yAxis:{{type:'value',name:'倾向频次',max:0.5,axisLabel:{{formatter:v=>(v*100)+'%'}}}},
    series:[{{type:'bar',data:D.freq.map(c=>({{value:c['倾向频次']||0,itemStyle:{{color:c.sector==='XLE'?'#D55E00':'#0072B2'}}}})),barWidth:'55%',label:{{show:true,position:'top',formatter:p=>(p.value*100).toFixed(0)+'%',fontSize:11}}}}]
  }});
  // 延续收益均值对比
  const ev = {{ '强势独立上涨':{{}}, '跟随震荡(对照)':{{}} }};
  D.cont.forEach(r=>{{ const g=r['标签']==='跟随震荡'?'跟随震荡(对照)':r['标签']; if(!g||g==='弱势独立下跌')return; ev[g]&&(ev[g][r.T]= (typeof r.mean==='number')?r.mean:0); }});
  CH.cont = echarts.init(document.getElementById('ch_cont'));
  CH.cont.setOption({{
    title:{{text:'独立上涨 vs 跟随震荡：各持有期均值超额(pp)',left:8,top:4,textStyle:{{fontSize:14,color:'#33414f'}}}},
    tooltip:{{trigger:'axis'}}, legend:{{bottom:0,textStyle:{{fontSize:12}}}}, grid:{{top:38,left:48,right:18,bottom:44}},
    xAxis:{{type:'category',data:['T+20','T+60','T+120']}},
    yAxis:{{type:'value',name:'超额 pp'}},
    series:[
      {{name:'强势独立上涨',type:'bar',data:['T+20','T+60','T+120'].map(t=>ev['强势独立上涨'][t]||0),itemStyle:{{color:'#D55E00'}},label:{{show:true,position:'top',formatter:p=>p.value.toFixed(1),fontSize:11}}}},
      {{name:'跟随震荡(对照)',type:'bar',data:['T+20','T+60','T+120'].map(t=>ev['跟随震荡(对照)'][t]||0),itemStyle:{{color:'#cfd8e0'}},label:{{show:true,position:'top',formatter:p=>p.value.toFixed(1),fontSize:11}}}}
    ]
  }});
}}
init();
window.addEventListener('resize',()=>Object.values(CH).forEach(c=>c&&c.resize()));
</script>
</body></html>"""

path = os.path.join(outdir, 'index.html')
with open(path, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f'written: {path} {os.path.getsize(path)}')
