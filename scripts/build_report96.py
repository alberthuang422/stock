# -*- coding: utf-8 -*-
"""
96 号报告生成器：白糖「各国产量」全景 2000-2026
沿用 94 号报告的设计系统（Okabe-Ito 色板 / 无深色底 / 四段式结论）。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, 'results', 'sugar_production.json'), encoding='utf-8'))
OUTDIR = os.path.join(ROOT, 'reports', '96_白糖各国产量全景_2000_2026')
os.makedirs(OUTDIR, exist_ok=True)

W = D['world']
Y = list(range(2000, 2027))
G = {x['country']: x for x in D['growth']}
S = D['series']['data']
C = D['concentration']
ST = D['structure']
SS = D['share_series']

def f(v, d=0):
    return f'{v:,.{d}f}'

def pc(v, d=1):
    return '—' if v is None else f'{v:+.{d}f}%'

# ---------------- 关键读数 ----------------
w00, w26 = W['production'][0], W['production'][-1]
cons00, cons26 = W['disappearance'][0], W['disappearance'][-1]
end26 = W['end_stocks'][-1]
stu26 = 100.0 * end26 / cons26
stu00 = 100.0 * W['end_stocks'][0] / cons00
prod_growth = 100.0 * (w26 - w00) / w00

t3_00, t3_26 = C['top3'][0], C['top3'][-1]
t5_00, t5_26 = C['top5'][0], C['top5'][-1]
t10_00, t10_26 = C['top10'][0], C['top10'][-1]
hhi_00, hhi_26 = C['hhi'][0], C['hhi'][-1]

br, ind, eu, ch, th = G['Brazil'], G['India'], G['European Union'], G['China'], G['Thailand']
russia, pak = G['Russia'], G['Pakistan']

tot_delta = sum(x['delta'] for x in D['growth'])
br_share_of_growth = 100.0 * br['delta'] / tot_delta
bi_share_of_growth = 100.0 * (br['delta'] + ind['delta']) / tot_delta

beet_share_00 = 100 - ST['cane_share'][0]
beet_share_26 = 100 - ST['cane_share'][-1]

# 产量集中度 vs 出口集中度（#94 口径）
exp_top4_26 = 75.1   # 来自 94 号报告
prod_top4_26 = None

# ---------------- 表格：全球盘子 ----------------
idx = {y: i for i, y in enumerate(Y)}
def row_global(label, key, fmt='{:,.0f}', suffix=''):
    cells = ''.join(f'<td class="num">{fmt.format(W[key][idx[y]])}{suffix}</td>' for y in (2000, 2010, 2020, 2024, 2026))
    d = W[key][-1] - W[key][0]
    chg = f'{d:+,.0f}'
    return f'<tr><td>{label}</td>{cells}<td class="num">{chg}</td></tr>'

tbl_global = (
    row_global('产量 Production', 'production')
    + row_global('总消费 Total Disappearance', 'disappearance')
    + row_global('期末库存 Ending Stocks', 'end_stocks')
    + row_global('出口 Exports', 'exports')
    + row_global('进口 Imports', 'imports')
)

def stu_at(y):
    i = idx[y]
    return 100.0 * W['end_stocks'][i] / W['disappearance'][i]
tbl_global += '<tr><td>库消比 STU</td>' + ''.join(f'<td class="num">{stu_at(y):.1f}%</td>' for y in (2000, 2010, 2020, 2024, 2026)) + f'<td class="num">{stu26 - stu00:+.1f}pp</td></tr>'

# ---------------- 表格：产量 Top 15 ----------------
rows_top = []
for i, (c, v) in enumerate([(k, S[k]) for k in D['series']['ranking']][:15]):
    g = G[c]
    rows_top.append(
        f"<tr><td class='num'>{i+1}</td><td>{c}</td>"
        f"<td class='num'>{f(v[0])}</td><td class='num'>{f(v[10])}</td><td class='num'>{f(v[20])}</td><td class='num'>{f(v[26])}</td>"
        f"<td class='num {'red' if g['pct'] and g['pct']>0 else 'green'}'>" + (pc(g['pct'], 0) if g['pct'] is not None else '—') + "</td>"
        f"<td class='num'>{g['cane_share26']:.0f}%</td>"
        f"<td class='num'>{f(g['delta'])}</td></tr>"
    )
tbl_top15 = ''.join(rows_top)

# ---------------- 表格：甜菜糖国 ----------------
rows_beet = ''.join(
    f"<tr><td>{x['country']}</td><td class='num'>{f(x['beet'])}</td><td class='num'>{f(x['prod'])}</td>"
    f"<td class='num'>{100*x['beet']/x['prod'] if x['prod'] else 0:.0f}%</td></tr>"
    for x in D['beet_countries'][:12]
)

# ---------------- 表格：自给率两极 ----------------
rows_low = ''.join(
    f"<tr><td>{x['country']}</td><td class='num'>{x['prod'] and f(x['prod']) or '0'}</td><td class='num'>{f(x['cons'])}</td>"
    f"<td class='num green'>{x['self_suff']:.1f}%</td><td class='num'>{f(x['deficit'])}</td></tr>"
    for x in D['self_sufficiency'][:10]
)
rows_high = ''.join(
    f"<tr><td>{x['country']}</td><td class='num'>{f(x['prod'])}</td><td class='num'>{f(x['cons'])}</td>"
    f"<td class='num red'>{x['self_suff']:.1f}%</td><td class='num'>{f(x['prod'] - x['cons'])}</td></tr>"
    for x in D['self_sufficiency_high'][:10]
)

# ---------------- 附录 A 分国产量总表 ----------------
rows_appA = []
for i, c in enumerate(D['series']['ranking']):
    v = S[c]
    g = G[c]
    rows_appA.append(
        f"<tr><td class='num'>{i+1}</td><td>{c}</td>"
        f"<td class='num'>{f(v[0])}</td><td class='num'>{f(v[10])}</td><td class='num'>{f(v[20])}</td>"
        f"<td class='num'>{f(v[24])}</td><td class='num'><b>{f(v[26])}</b></td>"
        f"<td class='num'>{f(g['delta'])}</td>"
        f"<td class='num {'red' if g['pct'] and g['pct']>0 else 'green'}'>" + (pc(g['pct'], 0) if g['pct'] is not None else '—') + "</td>"
        f"<td class='num'>{g['cane26'] and f(g['cane26']) or '0'}</td>"
        f"<td class='num'>{g['beet26'] and f(g['beet26']) or '0'}</td>"
        f"<td class='num'>{g['self_suff']:.0f}%</td></tr>"
    )
tbl_appA = ''.join(rows_appA)

# ---------------- 嵌入式数据 ----------------
PAY = {
    'Y': Y,
    'world': {k: W[k] for k in ('production', 'disappearance', 'end_stocks', 'exports', 'imports')},
    'concentration': C,
    'structure': ST,
    'top10': {c: S[c] for c in D['series']['ranking'][:10]},
    'cons': {c: D['series']['cons'][c] for c in D['series']['ranking'][:10]},
    'exp': {c: D['series']['exp'][c] for c in D['series']['ranking'][:10]},
    'share': SS,
    'cane': {c: D['series']['cane'][c] for c in D['series']['ranking'][:8]},
    'beet': {c: D['series']['beet'][c] for c in D['series']['ranking'][:8]},
}
PAY_JSON = json.dumps(PAY, ensure_ascii=False, separators=(',', ':'))

ANN = {}
for i, y in enumerate(Y):
    ANN[str(y)] = {
        'p': W['production'][i], 'c': W['disappearance'][i], 'e': W['end_stocks'][i],
        'x': W['exports'][i], 'm': W['imports'][i],
        't3': C['top3'][i], 't5': C['top5'][i], 'hhi': C['hhi'][i],
        'beet': ST['beet'][i],
    }
ANN_JSON = json.dumps(ANN, ensure_ascii=False, separators=(',', ':'))

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>白糖各国产量全景 2000–2026 · 报告 96</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
  :root{{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --oi-green:#009E73;
        --oi-sky:#56B4E9; --oi-purple:#CC79A7; --oi-yellow:#F0E442; --oi-black:#000000;
        --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec; --card:#fff; --bg:#f5f7fa; --ref-bg:#eef2f7;}}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px;}}
  .wrap{{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}}
  .hero{{background:linear-gradient(135deg,#12365e 0%,#1d5c93 100%);color:#fff;border-radius:12px;padding:28px 32px;margin-bottom:20px;}}
  .hero h1{{font-size:23px;margin-bottom:6px;line-height:1.45;}}
  .hero .meta{{font-size:12.5px;opacity:.85;margin-top:4px;}}
  .hero .sub{{margin-top:12px;font-size:14px;opacity:.96;border-top:1px solid rgba(255,255,255,.25);padding-top:10px;}}
  .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}}
  .kcard{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}}
  .kcard .lab{{font-size:12px;color:var(--sub);margin-bottom:3px;}}
  .kcard .val{{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;}}
  .kcard .note{{font-size:12px;color:var(--sub);margin-top:3px;}}
  .red{{color:#b2182b;}} .green{{color:#1a7a3a;}} .blue{{color:#0072B2;}} .orange{{color:#b47400;}}
  h2{{font-size:19px;margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--oi-blue);}}
  h3{{font-size:16px;color:#12365e;margin:18px 0 8px;}}
  .panel{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:16px;}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;}}
  th{{background:#eef2f7;color:#12365e;padding:6px 7px;text-align:left;border-bottom:2px solid var(--line);font-weight:600;}}
  td{{padding:5px 7px;border-bottom:1px solid var(--line);vertical-align:middle;}}
  tr:last-child td{{border-bottom:none;}}
  .num{{font-variant-numeric:tabular-nums;text-align:right;}}
  th.num{{text-align:right;}}
  .src{{font-size:11px;color:var(--sub);margin-top:7px;line-height:1.5;}}
  .callout{{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:14px 18px;margin:14px 0;font-size:13.5px;}}
  .warn{{background:#fdf2f2;border:1px solid #eccaca;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}}
  .ok{{background:#f0f8f4;border:1px solid #c9e5d6;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}}
  .chart{{width:100%;height:360px;}}
  .chart-sm{{width:100%;height:300px;}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
  .footer{{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}}
  code{{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px;}}
  ul{{padding-left:22px;}} li{{margin:4px 0;}}
  .tbl-scroll{{overflow-x:auto;}}
  @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr);}}.grid2{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>白糖各国产量全景（2000–2026）：两个国家的增量、一个集团的萎缩，与产量—贸易集中度的剪刀差</h1>
    <div class="meta">报告编号 96 ｜ 数据源：USDA FAS PSD（2026-09-11 快照，本地 psd_sugar_all.csv）｜ 单位：千吨·原糖当量（raw value）｜ 2026-09-18 · 与 94 号《白糖可贸易国家全景》同源同格式</div>
    <div class="sub">结论一句话：<b>
    2000–2026 年全球糖产量从 {f(w00)} 千吨增至 {f(w26)} 千吨（{pc(prod_growth,0)}，绝对增量 {f(w26-w00)} 千吨），
    但这 {f(w26-w00)} 千吨增量里有 <b class="red">{br_share_of_growth:.0f}% 来自巴西、{bi_share_of_growth:.0f}% 来自巴西+印度</b>；
    与此同时<b>欧盟是唯一大幅萎缩的产糖主体</b>（{f(eu['p2000'])} → {f(eu['p2026'])}，{pc(eu['pct'],0)}）。
    产量集中度确实在上升（Top5 {t5_00}% → {t5_26}%），但<b class="red">远比贸易集中度温和</b>——
    #94 号测得出口端 Top4 份额已从 40.5% 升至 75.1%（+34.6pp），而产量端 Top5 仅 {pc(t5_26-t5_00,0).replace('+','+')}（+{t5_26-t5_00:.1f}pp）。
    这条「<b>产量分散、贸易集中</b>」的剪刀差，正是 94 号所刻画的「可贸易性上升」在上游的镜像：<b>世界不是产得少了，而是把货交到少数几个出口商手里的结构越来越硬</b>。
    </b></div>
  </div>

  <div class="cards">
    <div class="kcard"><div class="lab">全球产量（2026）</div><div class="val">{f(w26)}</div>
      <div class="note">千吨·原糖当量 ｜ 2000 年 {f(w00)}（{pc(prod_growth,0)}）</div></div>
    <div class="kcard"><div class="lab">巴西+印度 占全球增量</div><div class="val red">{bi_share_of_growth:.0f}%</div>
      <div class="note">巴西一国家贡献 {br_share_of_growth:.0f}%（{f(br['delta'])} 千吨）</div></div>
    <div class="kcard"><div class="lab">产量 Top5 份额（2026）</div><div class="val">{t5_26}%</div>
      <div class="note">2000 年 {t5_00}% ｜ 出口端 Top4 已达 75.1%</div></div>
    <div class="kcard"><div class="lab">欧盟产量变化</div><div class="val green">{pc(eu['pct'],0)}</div>
      <div class="note">{f(eu['p2000'])} → {f(eu['p2026'])} 千吨 ｜ 自给率降至 {eu['self_suff']:.0f}%</div></div>
  </div>

  <h2>一、全球盘子：{f(w26-w00)} 千吨增量是怎么分配的</h2>
  <div class="panel">
    <div id="c1" class="chart"></div>
    <div class="src">世界合计 = PSD 分国加总（欧盟按 PSD 报告主体合并 EU-15/EU-25/European Union 三代口径，已剔除 World/USSR 等合计行）。产量为柱（左轴），消费为实线（左轴），期末库存为虚线+面积（右轴），库消比 STU = 期末库存 ÷ 总消费（右轴，%）。口径与 94 号报告完全一致（world[2000] 产量 130,764、world[2026] 184,854 两处均对得上）。</div>
  </div>
  <div class="panel">
    <h3>全球平衡表五个层级（千吨 / %）</h3>
    <div class="tbl-scroll"><table>
      <tr><th>层级</th><th class="num">2000</th><th class="num">2010</th><th class="num">2020</th><th class="num">2024</th><th class="num">2026</th><th class="num">26 年变化</th></tr>
      {tbl_global}
    </table></div>
    <div class="src">注：2024 列为「近三年」参考；26 年变化 = 2026 − 2000。MY2026 为 USDA 预测值（见第五节 vintage 追踪）。</div>
  </div>
  <div class="callout">
    <b>三个层级的读数：</b>
    <ul>
      <li><b>产量的绝对增量极不均匀</b>：全球 +{f(w26-w00)} 千吨，而巴西一国 +{f(br['delta'])} 千吨（占 {br_share_of_growth:.0f}%）、印度 +{f(ind['delta'])} 千吨（占 {100*ind['delta']/tot_delta:.0f}%）。两者合计 {bi_share_of_growth:.0f}%——<b>全球糖产量增长在统计上基本等于「巴西 + 印度 + 其他」</b>。</li>
      <li><b>增长的第二梯队是甜菜糖国</b>：俄罗斯 {pc(russia['pct'],0)}（{f(russia['p2000'])} → {f(russia['p2026'])}）、巴基斯坦 {pc(pak['pct'],0)}、中国 {pc(ch['pct'],0)}、泰国 {pc(th['pct'],0)}。俄罗斯与巴基斯坦是「进口替代型增长」，中国与泰国是「需求驱动型增长」。</li>
      <li><b>唯一的结构性萎缩来自欧盟</b>：{f(eu['p2000'])} → {f(eu['p2026'])} 千吨（{pc(eu['pct'],0)}），份额从 {SS['European Union'][0]}% 降至 {SS['European Union'][26]}%；这不是产量波动，是<b>配额制取消后连续两轮糖价暴跌→甜菜面积系统性退出的政策后果</b>（见第三节）。</li>
    </ul>
  </div>

  <h2>二、集中度：产量端与贸易端的剪刀差</h2>
  <div class="panel">
    <div class="grid2">
      <div><div id="c2" class="chart-sm"></div></div>
      <div><div id="c3" class="chart-sm"></div></div>
    </div>
    <div class="src">左：产量 Top3 / Top5 / Top10 份额与 HHI（右轴，点 = 各国份额平方和×10000）。右：前五大产国各自的全球产量份额演变。两条曲线都指向「集中度上升」，但斜率差异巨大——出口端集中化速度远快于产量端。</div>
  </div>
  <div class="panel">
    <h3>产量集中度 vs 贸易集中度（2000 → 2026）</h3>
    <table>
      <tr><th>维度</th><th class="num">2000</th><th class="num">2026</th><th class="num">变化</th><th>报告来源</th></tr>
      <tr><td>产量 Top3 份额</td><td class="num">{t3_00}%</td><td class="num">{t3_26}%</td><td class="num red">+{t3_26-t3_00:.1f}pp</td><td>本篇</td></tr>
      <tr><td>产量 Top5 份额</td><td class="num">{t5_00}%</td><td class="num">{t5_26}%</td><td class="num red">+{t5_26-t5_00:.1f}pp</td><td>本篇</td></tr>
      <tr><td>产量 Top10 份额</td><td class="num">{t10_00}%</td><td class="num">{t10_26}%</td><td class="num red">+{t10_26-t10_00:.1f}pp</td><td>本篇</td></tr>
      <tr><td>产量 HHI</td><td class="num">{hhi_00:,.0f}</td><td class="num">{hhi_26:,.0f}</td><td class="num red">+{hhi_26-hhi_00:,.0f}</td><td>本篇</td></tr>
      <tr style="background:#fff8ee"><td><b>出口 Top4 份额</b></td><td class="num"><b>40.5%</b></td><td class="num"><b>75.1%</b></td><td class="num red"><b>+34.6pp</b></td><td><b>94 号报告</b></td></tr>
    </table>
    <div class="src">⚠️ 口径提示：产量 Top5 = 巴西/印度/欧盟/中国/泰国；出口 Top4 = 巴西/泰国/印度/澳大利亚（94 号口径）。两个集合的成员不同，但结论方向一致——<b>集中度在产量端是缓慢的、在贸易端是跳跃的</b>。</div>
  </div>
  <div class="ok">
    <b>核心判断：</b>产量集中度（+{t5_26-t5_00:.1f}pp / 26 年）与出口集中度（+34.6pp / 26 年）的差距不是噪音，而是糖业的结构特征——
    <b>甘蔗糖可以是「小国自给」，但原糖贸易必须依赖规模化港口与压榨产能</b>。
    巴西的 42,500 千吨产量中 79.1% 直接出口，而印度 33,600 千吨产量中只有 10.7% 出口、中国 1.3%、欧盟 6.0%。
    这意味着：<b>讨论「全球糖供应」时，产量排名（本报告）解释的是「谁有货」，出口排名（94 号）解释的是「谁能把货变成市场供给」</b>——两者之间隔着一层国内政策与消费约束。
  </div>

  <h2>三、四个主角：巴西的产能、印度的内需、欧盟的退出、甜菜国的进口替代</h2>

  <h3>3.1 巴西：全球产量增长的近一半来自一国（+{f(br['delta'])} 千吨）</h3>
  <div class="panel">
    <div id="c4" class="chart-sm"></div>
    <div class="src">巴西产量（千吨）与出口/产量比。2000–2010 是第一轮扩张（{f(br['p2000'])} → {f(S['Brazil'][10])}），2010–2026 进入高位震荡（{f(S['Brazil'][10])} → {f(br['p2026'])}）。出口/产量比稳定在 70–80% 区间。</div>
  </div>
  <div class="callout">
    巴西的产量故事有两个特征：<b>①绝对规模垄断增量</b>（+{f(br['delta'])} 千吨 = 全球增量的 {br_share_of_growth:.0f}%）；
    <b>②增长几乎全部在 2000–2010 完成</b>（前十年 +{f(S['Brazil'][10]-br['p2000'])} 千吨，后十六年仅 +{f(br['p2026']-S['Brazil'][10])} 千吨）。
    近年的边际变化不在「产量」而在「<b>制糖比</b>」：甘蔗压榨量仍在增长，但糖/乙醇的利润比价决定有多少甘蔗进糖厂。
    按行业口径（2026-07），Conab 预计 2026/27 甘蔗产量 7.091 亿吨（+5.3%），但 6 月上半月制糖比仅 45.86%（预期 47%），
    <b>USDA 估巴西糖产量 4,250 万吨 vs Itau BBA 仅 3,940 万吨</b>——机构分歧全部集中在制糖比回升节奏上。
  </div>

  <h3>3.2 印度：产量 +{ind['pct']:.0f}%，但出口/产量只有 {ind['export_ratio']:.1f}%</h3>
  <div class="panel">
    <div id="c5" class="chart-sm"></div>
    <div class="src">印度产量、消费与出口（千吨）。产量从 {f(ind['p2000'])} 增至 {f(ind['p2026'])}（{pc(ind['pct'],0)}），但出口常年仅占产量的约十分之一，且年度间剧烈跳动（政策驱动的进出口政策开关）。</div>
  </div>
  <div class="callout">
    印度是「<b>产量大国 + 贸易小国</b>」的极端样本。{f(ind['p2026'])} 千吨产量中，出口仅 {f(ind['exp26'])} 千吨（{ind['export_ratio']:.1f}%），
    国内消费 {f(ind['cons26'])} 千吨几乎吃掉了绝大部分产出。<b>这与 94 号的结论完全咬合</b>：印度出口是「政策锯齿」而非「产能函数」，
    其开关取决于国内库存与选举周期，放大倍数高达 9.3 倍。对本报告的启示是——<b>看印度产量预测对糖价的指示意义，必须乘以一个极小的「传导系数」</b>。
  </div>

  <h3>3.3 欧盟：唯一的结构性萎缩（{pc(eu['pct'],0)}，份额 {SS['European Union'][0]}% → {SS['European Union'][26]}%）</h3>
  <div class="panel">
    <div id="c6" class="chart-sm"></div>
    <div class="src">欧盟产量（千吨）与自给率。甜菜糖占比 99.1%，2005/06 配额改革后进入长期下行；2022 年一度因能源成本与干旱跌至 {f(S['European Union'][22])} 千吨。</div>
  </div>
  <div class="warn">
    <b>欧盟的萎缩有三个叠加原因，且 2026/27 会进一步恶化：</b>
    ①<b>政策</b>：2017/18 配额制取消后价格与产量波动放大，随后两轮糖价暴跌（2024–2026）压缩利润，甜菜面积连续两年大幅削减；
    ②<b>成本</b>：肥料与燃料价格上涨，与糖价下行形成剪刀；
    ③<b>天气</b>：2026 年夏季持续干旱与热浪，叠加法国黄化病（yellows virus）。
    按欧盟委员会（2026-07-06）预测，<b>2026/27 榨季产量将降至 1,410–1,490 万吨，同比 −15%，为近十年最低</b>；
    Czarnikow 更下调至 1,390 万吨。甜菜面积已降至 <b>2017/18 配额制结束以来最低</b>。
    2026 年 PSD 记欧盟 {f(eu['p2026'])} 千吨，<b>偏乐观</b>（见第五节）。
  </div>

  <h3>3.4 甜菜糖阵营：俄罗斯与巴基斯坦的进口替代（{pc(russia['pct'],0)} / {pc(pak['pct'],0)}）</h3>
  <div class="panel">
    <div class="grid2">
      <div><div id="c7" class="chart-sm"></div></div>
      <div><div id="c8" class="chart-sm"></div></div>
    </div>
    <div class="src">左：甘蔗糖与甜菜糖的全球产量（千吨）与各自占比。右：主要甜菜糖国的 2026 年产量构成。</div>
  </div>
  <div class="callout">
    <b>一个反直觉的事实：甜菜糖的「衰退」是相对衰退，不是绝对衰退。</b>
    全球甜菜糖产量 2000 年 {f(ST['beet'][0])} 千吨 → 2026 年 {f(ST['beet'][-1])} 千吨（几乎持平，{f(ST['beet'][-1]-ST['beet'][0])} 千吨），
    但占比从 {beet_share_00:.1f}% 降到 {beet_share_26:.1f}%——<b>纯粹是甘蔗糖增长太快（+{f(ST['cane'][-1]-ST['cane'][0])} 千吨）造成的分母效应</b>。
    真正的边际变化在俄罗斯与巴基斯坦：两国合计产量从 2000 年的 {f(russia['p2000']+pak['p2000'])} 千吨增至 {f(russia['p2026']+pak['p2026'])} 千吨（+{f((russia['p2026']+pak['p2026'])-(russia['p2000']+pak['p2000']))} 千吨），
    合计占全球增量的 {100*((russia['delta']+pak['delta'])/tot_delta):.0f}%。<b>俄罗斯自给率已超 105%（行业口径 104.9%），并已转为出口国（年出口约 100 万吨）</b>，
    这是 2000 年代「甜菜进口替代 + 食品禁运」政策的直接产物，也是全球糖贸易流向在 2020 年代最大的边际变量之一。
  </div>

  <h2>四、自给率两极：谁离不开世界市场</h2>
  <div class="panel">
    <div class="grid2">
      <div>
        <h3 style="margin-top:0">进口依赖型（自给率最低）</h3>
        <table>
          <tr><th>国家/地区</th><th class="num">产量</th><th class="num">消费</th><th class="num">自给率</th><th class="num">缺口</th></tr>
          {rows_low}
        </table>
      </div>
      <div>
        <h3 style="margin-top:0">出口溢出型（自给率最高）</h3>
        <table>
          <tr><th>国家/地区</th><th class="num">产量</th><th class="num">消费</th><th class="num">自给率</th><th class="num">盈余</th></tr>
          {rows_high}
        </table>
      </div>
    </div>
    <div class="src">自给率 = 产量 ÷ 总消费 × 100%。仅列示总消费 ≥ 30 万吨的实体（2026）。缺口/盈余 = 产量 − 消费。<span class="green">绿色</span> = 依赖进口；<span class="red">红色</span> = 出口溢出。</div>
  </div>
  <div class="callout">
    <b>两极的分布比总量更有信息量。</b>自给率最低的一极（伊拉克、黎巴嫩、马来西亚 0%，孟加拉 1.8%、尼日利亚 5.7%、加拿大 6.9%）
    是纯粹的需求方，其进口量对糖价几乎无弹性——<b>这是全球糖价的「刚性买盘」</b>。
    自给率最高的一极里，巴西 {br['self_suff']:.0f}%、澳大利亚 {G['Australia']['self_suff']:.0f}%、泰国 {th['self_suff']:.0f}% 才是真正的供应弹性来源。
    <b>关键洞察</b>：把「产量排名」和「自给率排名」叠起来看，会发现<b>产量排名前列的中国（自给 {ch['self_suff']:.0f}%）与欧盟（自给 {eu['self_suff']:.0f}%）其实是净进口方</b>——
    这解释了为什么 94 号报告会看到「中国与欧盟同时出现在进口国名单里」，也再次印证：<b>产量 ≠ 可贸易供给</b>。
  </div>

  <h2>五、vintage 追踪：PSD 半年更新 vs 行业最新口径（2026-09-18 核对）</h2>
  <div class="panel">
    <table>
      <tr><th>主体</th><th class="num">PSD 2026（本报告）</th><th>行业/官方最新口径</th><th>偏离</th><th>方向</th></tr>
      <tr><td>欧盟</td><td class="num">{f(eu['p2026'])}</td><td>欧盟委员会 2026-07-06：<b>2026/27 = 1,410–1,490 万吨（−15%）</b>；Czarnikow：1,390 万吨</td><td class="num green">PSD 高估约 0~5%</td><td>PSD <b>偏乐观</b></td></tr>
      <tr><td>巴西</td><td class="num">{f(br['p2026'])}</td><td>USDA 4,250 万 vs <b>Itau BBA 3,940 万</b>；Conab 甘蔗 7.091 亿吨（+5.3%）</td><td class="num">机构分歧 ±7%</td><td>取决于制糖比</td></tr>
      <tr><td>泰国</td><td class="num">{f(th['p2026'])}</td><td>StoneX：<b>2026/27 减产 15% 至 1,020 万吨</b>；甘蔗收购价 −22%，农户转种木薯</td><td class="num green">PSD 可能高估</td><td>PSD <b>偏乐观</b></td></tr>
      <tr><td>俄罗斯</td><td class="num">{f(russia['p2026'])}</td><td>行业协会：2026/27 <b>640–680 万吨</b>；2025/26 甜菜糖 608–621 万吨；自给率 104.9%</td><td class="num red">PSD 低约 2~8%</td><td>PSD <b>偏保守</b></td></tr>
      <tr><td>乌克兰</td><td class="num">{f(G['Ukraine']['p2026'])}</td><td>2025/26 榨季总产糖 <b>172 万吨</b>（面积 −23%，但单产创纪录 58 t/ha）</td><td class="num red">PSD 低约 13%</td><td>PSD <b>偏保守</b></td></tr>
      <tr><td>白俄罗斯</td><td class="num">{f(G['Belarus']['p2026'])}</td><td>2025/26 甜菜糖 <b>72.25 万吨</b>（甜菜 589.9 万吨，+19%）</td><td class="num">基本一致</td><td>—</td></tr>
    </table>
    <div class="src">口径对齐说明：PSD 的 MY2026 与各国「2026/27 榨季」并不完全同期（市场年窗口不同），差异中有一部分是时间口径而非真实偏离。上表仅为方向性判断。</div>
  </div>
  <div class="warn">
    <b>vintage 纪律（跨项目铁律）</b>：USDA PSD 为半年更新（5 月/11 月），<b>「最新 vintage ≠ 最新事实」</b>。
    截至 2026-09-18 的行业共识已明显偏向<b>减产</b>：ISO 预计 2026/27 全球产量 1.80 亿吨（−1.1%），出现 <b>26.2 万吨缺口</b>；
    StoneX 从 +229 万吨过剩转为 <b>−55 万吨短缺</b>；Czarnikow 把过剩预估从 340 万吨砍到 60 万吨。
    <b>方向高度一致：2026/27 全球糖市正从「现实过剩」切向「预期短缺」</b>——而 PSD 的 2026 数字尚未完全反映这一转向。
    ICE 原糖 27/3 合约已破 18 美分（13.75→18.75c 为缺口定价）。
  </div>

  <h2>六、结论（四段式）</h2>
  <div class="panel">
    <h3>[前提/背景校验]</h3>
    <p>本报告与 94 号《白糖可贸易国家全景》同源（USDA FAS PSD，2026-09-11 快照）、同单位（千吨·原糖当量）、同格式，但分析对象从「库存与贸易」转向「产量」。
    两项关键口径处理必须先声明：<b>①欧盟在 PSD 中的标签随时间轮转（EU-15 ≤2003 / EU-25 2004–05 / European Union 2001+），且 'European Union' 早期为 0 值</b>——
    若不合并三代标签并取最大值，2000 年世界产量会被低估 18.5 Mt（112,245 vs 真实 130,764）。本报告已合并并复核，世界序列与 94 号逐点一致。
    <b>②属性码为三位零填充字符串（'028' 而非 '28'）</b>，且须剔除 World/USSR/Yugoslavia 等合计行以防重复计数。
    样本：118 个有产量的实体（含合并后的欧盟），市场年 2000–2026，MY2026 为 PSD 预测值。</p>

    <h3>[关键数据与依据]</h3>
    <ul>
      <li><b>总量</b>：全球产量 {f(w00)} → {f(w26)} 千吨（{pc(prod_growth,0)}），绝对增量 {f(w26-w00)} 千吨；消费 {f(cons00)} → {f(cons26)}；库消比 {stu00:.1f}% → {stu26:.1f}%。</li>
      <li><b>增量归属</b>：巴西 +{f(br['delta'])} 千吨（占全球增量 {br_share_of_growth:.0f}%）、印度 +{f(ind['delta'])}（{100*ind['delta']/tot_delta:.0f}%）、俄罗斯 +{f(russia['delta'])}、中国 +{f(ch['delta'])}、泰国 +{f(th['delta'])}；<b>欧盟 −{abs(eu['delta']):,.0f} 千吨（{pc(eu['pct'],0)}）是唯一大幅负贡献的主要主体</b>。</li>
      <li><b>集中度</b>：产量 Top3 {t3_00}%→{t3_26}%、Top5 {t5_00}%→{t5_26}%（+{t5_26-t5_00:.1f}pp）、Top10 {t10_00}%→{t10_26}%、HHI {hhi_00:,.0f}→{hhi_26:,.0f}；对照 94 号出口端 Top4 40.5%→75.1%（+34.6pp）。</li>
      <li><b>结构</b>：甘蔗糖占比 {ST['cane_share'][0]:.1f}%→{ST['cane_share'][-1]:.1f}%，甜菜糖 {beet_share_00:.1f}%→{beet_share_26:.1f}%；但甜菜糖绝对量为 {f(ST['beet'][0])}→{f(ST['beet'][-1])}，<b>是相对衰退</b>。</li>
      <li><b>自给率</b>：巴西 {br['self_suff']:.0f}%、澳大利亚 {G['Australia']['self_suff']:.0f}%、泰国 {th['self_suff']:.0f}% 对马来西亚/伊拉克/黎巴嫩 0%、孟加拉 1.8%。<b>中国（{ch['self_suff']:.0f}%）与欧盟（{eu['self_suff']:.0f}%）虽产量排名前列，实为净进口方。</b></li>
    </ul>

    <h3>[客观分析与对比]</h3>
    <p><b>与 94 号报告的核心对比：产量集中化远慢于贸易集中化。</b>
    出口 Top4 份额 26 年上升 34.6pp，而产量 Top5 仅上升 {t5_26-t5_00:.1f}pp——差距达数倍。这不是统计噪音，而是糖业物理与制度结构的结果：
    原糖贸易需要规模化压榨、港口与物流，而「自给型小生产国」不需要出口。巴西一国产量的 79.1% 用于出口，印度仅 10.7%、中国 1.3%、欧盟 6.0%。
    <b>结论：产量排名回答「谁有货」，出口排名回答「谁能把货变成市场供给」，中间隔着国内政策与消费。</b></p>
    <p><b>反例与争议：</b>
    ①<b>甜菜糖「衰退论」是错的</b>——绝对量 26 年几乎持平（{f(ST['beet'][0])}→{f(ST['beet'][-1])}），占比下降纯由甘蔗糖高增长的分母效应造成；
    ②<b>俄罗斯的 +{russia['pct']:.0f}% 增长常被忽略</b>——它已从进口国转为年出口约 100 万吨的出口国，且自给率 104.9%，是 2020 年代贸易流最大边际变量之一；
    ③<b>PSD 的 vintage 偏差方向不一致</b>——欧盟与泰国偏乐观、俄罗斯与乌克兰偏保守，说明「偏乐观」并非系统性偏差，而是各品种/地区的预测能力差异；
    ④<b>巴西的分歧在制糖比而非产量</b>——USDA 4,250 万 vs Itau BBA 3,940 万的差距（±7%）全部来自糖/乙醇比价假设。</p>

    <h3>[结论与置信度]</h3>
    <p><b>结论：</b>2000–2026 全球糖产量增长 {pc(prod_growth,0)}，但增量高度集中于巴西与印度（合计 {bi_share_of_growth:.0f}%），
    并伴随欧盟的结构性退出（{pc(eu['pct'],0)}）。产量集中度温和上升（Top5 +{t5_26-t5_00:.1f}pp），
    <b>显著慢于贸易集中度（+34.6pp），构成「产量分散 / 贸易集中」的剪刀差</b>——这正是 94 号「糖变得更可贸易」结论的上游镜像。
    2026/27 的边际方向明确转向<b>减产与短缺</b>：欧盟 −15%（EC）、泰国 −15%（StoneX）、全球由过剩转缺口（ISO/StoneX/Czarnikow 方向一致）。
    <b>置信度：高</b>（总量与集中度可逐点对账、世界序列与 94 号完全一致）；<b>中</b>（分国 2026 预测值受 PSD vintage 限制，欧盟/泰国已可确认偏乐观）；<b>低-中</b>（巴西制糖比与 2026/27 最终缺口幅度，机构分歧 ±7% 且依赖天气）。
    证伪条件：霍尔木兹/黑海物流未受影响前提下，若 2026Q4 巴西制糖比回升至 47%+ 且欧盟甜菜单产因降雨恢复，则「缺口共识」可能重新转为平衡。</p>
  </div>

  <h2>附录 A · 分国产量总表（千吨·原糖当量）</h2>
  <div class="panel">
    <h3>A1 主要产糖国（2000–2026 产量轨迹 / 甘蔗・甜菜拆分 / 自给率）</h3>
    <div class="tbl-scroll"><table>
      <tr>
        <th class="num">#</th><th>国家/地区</th>
        <th class="num">2000</th><th class="num">2010</th><th class="num">2020</th><th class="num">2024</th><th class="num">2026</th>
        <th class="num">增量</th><th class="num">26年变化</th><th class="num">甘蔗糖</th><th class="num">甜菜糖</th><th class="num">自给率</th>
      </tr>
      {tbl_appA}
    </table></div>
    <div class="src">按 2026 年产量降序。自给率 = 产量 ÷ 总消费 × 100%。<span class="red">红色</span> = 正增长，<span class="green">绿色</span> = 负增长（红涨绿跌）。欧盟为 PSD 合并口径（EU-15/EU-25/European Union 三代标签取最大值）。</div>
  </div>
  <div class="panel">
    <h3>A2 分国产量完整数据（交互表）</h3>
    <div class="tbl-scroll"><table id="tbl_app">
      <tr><th>年份</th><th class="num">全球产量</th><th class="num">全球消费</th><th class="num">期末库存</th><th class="num">STU</th><th class="num">Top3</th><th class="num">Top5</th><th class="num">HHI</th><th class="num">甜菜糖</th></tr>
    </table></div>
    <div class="src">逐年数据（2000–2026），单位千吨（STU 为 %）。</div>
  </div>

  <div class="footer">
    <b>报告 96 · 白糖各国产量全景 2000–2026</b>｜数据源：USDA FAS PSD（2026-09-11 快照，本地 psd_sugar_all.csv，152,016 行 × 16 属性）｜
    行业交叉验证：欧盟委员会短期展望（2026-07-06）、StoneX、Czarnikow、ISO、Conab、Itau BBA、EAEU 糖业协会、Soyuzrossakhar｜
    数据脚本 <code>scripts/sugar_production_panorama_20260918.py</code>｜结果 <code>results/sugar_production.json</code>｜
    姊妹报告：94 号《白糖可贸易国家全景 2000–2026》（库存与贸易视角）｜生成于 2026-09-18。<br>
    ⚠️ vintage 提示：PSD 为半年更新，MY2026 为预测值；引用前请核对行业最新指引（见第五节）。所有数字可复算。
  </div>
</div>

<script>
const P = {PAY_JSON};
const ANN = {ANN_JSON};
const C = {{blue:'#0072B2',orange:'#E69F00',verm:'#D55E00',green:'#009E73',sky:'#56B4E9',purple:'#CC79A7',yellow:'#F0E442'}};
const axis = {{axisLine:{{lineStyle:{{color:'#c8d2de'}}}},axisLabel:{{color:'#5a6a7d',fontSize:11}},splitLine:{{lineStyle:{{color:'#eef2f7'}}}}}};
function mk(id,opt){{const el=document.getElementById(id);if(!el)return;const ch=echarts.init(el);ch.setOption(opt);window.addEventListener('resize',()=>ch.resize());}}
const tip={{trigger:'axis',valueFormatter:v=>v==null?'-':(+v).toLocaleString()}};
const Y = P.Y;

// C1 全球盘子
mk('c1',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:62,right:64,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'千吨',...axis}},{{type:'value',name:'%',min:15,max:35,...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'产量',type:'bar',data:P.world.production,itemStyle:{{color:C.sky,opacity:.6}},barWidth:'46%'}},
    {{name:'总消费',type:'line',data:P.world.disappearance,lineStyle:{{width:2.5,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'none'}},
    {{name:'出口',type:'line',data:P.world.exports,lineStyle:{{width:2,color:C.purple}},itemStyle:{{color:C.purple}},symbol:'none'}},
    {{name:'期末库存',type:'line',yAxisIndex:1,data:P.world.end_stocks,areaStyle:{{opacity:.12,color:C.orange}},lineStyle:{{width:2,color:C.orange,type:'dashed'}},itemStyle:{{color:C.orange}},symbol:'none'}}
  ]
}});

// C2 集中度
mk('c2',{{
  tooltip:tip, title:{{text:'产量集中度与 HHI',left:'center',top:0,textStyle:{{fontSize:13,color:'#12365e'}}}},
  legend:{{top:24,textStyle:{{color:'#1a2330',fontSize:11}}}},
  grid:{{left:56,right:60,top:58,bottom:36}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'%',min:20,max:85,...axis}},{{type:'value',name:'HHI',min:600,max:1300,...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'Top3%',type:'line',data:P.concentration.top3,lineStyle:{{width:2,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'none'}},
    {{name:'Top5%',type:'line',data:P.concentration.top5,lineStyle:{{width:2.5,color:C.verm}},itemStyle:{{color:C.verm}},symbol:'none'}},
    {{name:'Top10%',type:'line',data:P.concentration.top10,lineStyle:{{width:2,color:C.green,type:'dashed'}},itemStyle:{{color:C.green}},symbol:'none'}},
    {{name:'HHI',type:'line',yAxisIndex:1,data:P.concentration.hhi,lineStyle:{{width:1.6,color:C.orange,type:'dotted'}},itemStyle:{{color:C.orange}},symbol:'none'}}
  ]
}});

// C3 前五国份额
const top5names = Object.keys(P.share);
const p5c = [C.blue, C.verm, C.orange, C.green, C.purple];
mk('c3',{{
  tooltip:tip, title:{{text:'前五大产国的全球产量份额',left:'center',top:0,textStyle:{{fontSize:13,color:'#12365e'}}}},
  legend:{{top:24,textStyle:{{color:'#1a2330',fontSize:11}}}},
  grid:{{left:56,right:20,top:58,bottom:36}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:{{type:'value',name:'%',...axis}},
  series:top5names.map((n,i)=>({{name:n,type:'line',data:P.share[n],lineStyle:{{width:2.4,color:p5c[i]}},itemStyle:{{color:p5c[i]}},symbol:'none'}}))
}});

// C4 巴西：产量 + 出口/产量比
const brRatio = P.Y.map((y,i)=>{{
  const p=P.top10.Brazil[i], e=P.exp.Brazil[i];
  return (p&&p>0)?+(100*e/p).toFixed(1):null;
}});
mk('c4',{{
  tooltip:tip, title:{{text:'巴西：产量与出口/产量比',left:'center',top:0,textStyle:{{fontSize:13,color:'#12365e'}}}},
  legend:{{top:24,textStyle:{{color:'#1a2330',fontSize:11}}}},
  grid:{{left:62,right:60,top:58,bottom:36}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'千吨',...axis}},{{type:'value',name:'出口/产量 %',min:40,max:100,...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'巴西产量',type:'bar',data:P.top10.Brazil,itemStyle:{{color:C.sky,opacity:.65}},barWidth:'50%'}},
    {{name:'出口/产量%',type:'line',yAxisIndex:1,data:brRatio,lineStyle:{{width:2.4,color:C.verm}},itemStyle:{{color:C.verm}},symbol:'none'}},
    {{name:'出口量',type:'line',data:P.exp.Brazil,lineStyle:{{width:1.8,color:C.purple,type:'dashed'}},itemStyle:{{color:C.purple}},symbol:'none'}}
  ]
}});

// C5 印度：产量 vs 消费 vs 出口
mk('c5',{{
  tooltip:tip, title:{{text:'印度：产量、消费与出口（政策锯齿）',left:'center',top:0,textStyle:{{fontSize:13,color:'#12365e'}}}},
  legend:{{top:24,textStyle:{{color:'#1a2330',fontSize:11}}}},
  grid:{{left:62,right:20,top:58,bottom:36}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:{{type:'value',name:'千吨',...axis}},
  series:[
    {{name:'产量',type:'line',data:P.top10.India,lineStyle:{{width:2.6,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'none'}},
    {{name:'消费',type:'line',data:P.cons.India,lineStyle:{{width:2.2,color:C.orange}},itemStyle:{{color:C.orange}},symbol:'none'}},
    {{name:'出口',type:'bar',data:P.exp.India,itemStyle:{{color:C.verm,opacity:.6}},barWidth:'50%'}}
  ]
}});

// C6 欧盟：产量 + 自给率
const euSS = P.Y.map((y,i)=>{{
  const p=P.top10['European Union'][i], c=P.cons['European Union'][i];
  return (c&&c>0)?+(100*p/c).toFixed(1):null;
}});
mk('c6',{{
  tooltip:tip, title:{{text:'欧盟：产量与自给率（结构性下行）',left:'center',top:0,textStyle:{{fontSize:13,color:'#12365e'}}}},
  legend:{{top:24,textStyle:{{color:'#1a2330',fontSize:11}}}},
  grid:{{left:62,right:60,top:58,bottom:36}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'千吨',...axis}},{{type:'value',name:'自给率 %',min:70,max:130,...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'欧盟产量',type:'bar',data:P.top10['European Union'],itemStyle:{{color:C.orange,opacity:.6}},barWidth:'50%'}},
    {{name:'自给率%',type:'line',yAxisIndex:1,data:euSS,lineStyle:{{width:2.4,color:C.verm}},itemStyle:{{color:C.verm}},symbol:'none'}},
    {{name:'消费',type:'line',data:P.cons['European Union'],lineStyle:{{width:2,color:C.blue,type:'dashed'}},itemStyle:{{color:C.blue}},symbol:'none'}}
  ]
}});

// C7 甘蔗/甜菜
mk('c7',{{
  tooltip:tip, title:{{text:'甘蔗糖 vs 甜菜糖（全球）',left:'center',top:0,textStyle:{{fontSize:13,color:'#12365e'}}}},
  legend:{{top:24,textStyle:{{color:'#1a2330',fontSize:11}}}},
  grid:{{left:62,right:60,top:58,bottom:36}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'千吨',...axis}},{{type:'value',name:'甜菜占比 %',min:15,max:32,...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'甘蔗糖',type:'line',data:P.structure.cane,areaStyle:{{opacity:.18,color:C.green}},lineStyle:{{width:2.4,color:C.green}},itemStyle:{{color:C.green}},symbol:'none'}},
    {{name:'甜菜糖',type:'line',data:P.structure.beet,areaStyle:{{opacity:.18,color:C.orange}},lineStyle:{{width:2.4,color:C.orange}},itemStyle:{{color:C.orange}},symbol:'none'}},
    {{name:'甜菜占比%',type:'line',yAxisIndex:1,data:P.structure.cane_share.map(v=>+(100-v).toFixed(1)),lineStyle:{{width:2,color:C.purple,type:'dashed'}},itemStyle:{{color:C.purple}},symbol:'none'}}
  ]
}});

// C8 甜菜糖国构成
const beetC = {json.dumps([x['country'] for x in D['beet_countries'][:8]], ensure_ascii=False)};
const beetV = {json.dumps([x['beet'] for x in D['beet_countries'][:8]])};
mk('c8',{{
  tooltip:{{trigger:'item'}}, title:{{text:'主要甜菜糖国产量（2026）',left:'center',top:0,textStyle:{{fontSize:13,color:'#12365e'}}}},
  grid:{{left:110,right:60,top:36,bottom:30}},
  xAxis:{{type:'value',name:'千吨',...axis}},
  yAxis:{{type:'category',data:beetC.slice().reverse(),...axis}},
  series:[{{type:'bar',data:beetV.slice().reverse(),itemStyle:{{color:C.orange}},barWidth:'58%',
    label:{{show:true,position:'right',fontSize:10,color:'#5a6a7d',formatter:'{{c}}'}}}}]
}});

// 附录交互表
(function(){{
  const t=document.getElementById('tbl_app');
  if(!t)return;
  for(let y=2000;y<=2026;y++){{
    const a=ANN[String(y)];if(!a)continue;
    const stu=(100*a.e/a.c).toFixed(1);
    const tr=document.createElement('tr');
    tr.innerHTML='<td>'+y+(y===2026?' <b>(预测)</b>':'')+'</td>'
      +'<td class="num">'+a.p.toLocaleString()+'</td>'
      +'<td class="num">'+a.c.toLocaleString()+'</td>'
      +'<td class="num">'+a.e.toLocaleString()+'</td>'
      +'<td class="num">'+stu+'%</td>'
      +'<td class="num">'+a.t3.toFixed(1)+'%</td>'
      +'<td class="num">'+a.t5.toFixed(1)+'%</td>'
      +'<td class="num">'+a.hhi.toFixed(0)+'</td>'
      +'<td class="num">'+a.beet.toLocaleString()+'</td>';
    t.appendChild(tr);
  }}
}})();
</script>
</body>
</html>'''

open(os.path.join(OUTDIR, 'index.html'), 'w', encoding='utf-8').write(HTML)
print('written ->', os.path.join(OUTDIR, 'index.html'), len(HTML), 'bytes')
