# -*- coding: utf-8 -*-
"""62 号报告构建：CCL 嘉年华邮轮全面分析（基本面×估值×技术面×量化回测×行业×风险）
数据源：本地日线(data/ccl) + 4 套回测 JSON + agentic_search/westock 快照 + 公开报道(2026-09-01 时点)"""
import json, os, re, time

ROOT = r'C:\Users\Administrator\Desktop\stock'
OUT_DIR = os.path.join(ROOT, 'reports', '62_CCL全面分析')
os.makedirs(OUT_DIR, exist_ok=True)

def load(fp):
    with open(os.path.join(ROOT, fp), encoding='utf-8') as f:
        return json.load(f)

tech = load('Temp/ccl_fetch/tech.json')
band_buy = load('results/ccl_rsi_band_buy.json')
band_dip = load('results/ccl_rsi_band_dip.json')
sub30 = load('results/ccl_rsi_sub30_deep.json')
dca = load('results/ccl_rsi30_dca.json')

# ---------------- 图表数据 ----------------
C = {}
# 1) 近 500 日价格+均线+RSI
c5 = tech['chart500']
C['px500'] = {'d': [x['d'] for x in c5], 'px': [x['px'] for x in c5],
              'e20': [x['e20'] for x in c5], 'e50': [x['e50'] for x in c5],
              's200': [x['s200'] for x in c5], 'rsi': [x['rsi'] for x in c5]}
# 2) 长周期月度
C['long'] = {'d': [x[0] for x in tech['months_full']], 'c': [round(x[1], 2) for x in tech['months_full']]}
# 3) 年度收益
yr = tech['year_ret']
C['year'] = {'y': list(yr.keys()), 'r': [round(v, 1) for v in yr.values()]}
# 4) 季度财务（公开报道口径，FY 财年 12 月结）
C['fund'] = {
    'q': ['24Q4', '25Q1', '25Q2', '25Q3', '25Q4', '26Q1', '26Q2'],
    'rev': [59.4, 58.1, 63.3, 81.5, 63.3, 61.7, 66.6],
    'eps': [0.23, -0.06, 0.42, 1.33, 0.31, 0.19, 0.39]}
# 5) 估值对比（forward PE / EV-EBITDA，TIKR+ainvest 2026-07 口径）
C['val'] = {
    'name': ['CCL', 'RCL', 'NCLH'],
    'fwdPE': [11.3, 16.7, 12.5],
    'evEbitda': [8.2, 12.9, 9.7]}
# 6) 状态式 RSI 档位 fwd20 中位
bb = band_buy['by_band']
C['bt1'] = {'name': [], 'med': [], 'win': [], 'n': []}
for k in ['<30', '30-40', '40-50', '50-60', '60-70', '≥70']:
    s = bb[k]['fwd20']
    C['bt1']['name'].append('RSI ' + k)
    C['bt1']['med'].append(round(s['median'], 2))
    C['bt1']['win'].append(round(s['win'], 1))
    C['bt1']['n'].append(s['n'])
# 7) 越跌越买三档
bd = band_dip['by_band']
C['bt2'] = {'name': [], 'med': [], 'win': [], 'n': [], 'ex': []}
for k in ['35-40', '30-35', '<30']:
    s = bd[k]
    C['bt2']['name'].append('RSI ' + k)
    C['bt2']['med'].append(round(s['fwd20']['median'], 2))
    C['bt2']['win'].append(round(s['win20'], 1))
    C['bt2']['n'].append(s['fwd20']['n'])
    C['bt2']['ex'].append(round(s['ex20']['median'], 2))
# 8) dd60 分层
d60 = sub30['by_dd60']
C['bt3'] = {'name': [], 'med': [], 'win': [], 'n': []}
for k in ['dd60>-10', 'dd60 -20~-10', 'dd60 -30~-20', 'dd60<=-30']:
    s = d60[k]['fwd20']
    C['bt3']['name'].append(k.replace('dd60 ', 'dd60\n').replace('dd60>', 'dd60>\n'))
    C['bt3']['med'].append(round(s['median'], 2))
    C['bt3']['win'].append(round(d60[k]['win20'], 1))
    C['bt3']['n'].append(s['n'])
# 9) DCA 结算窗口
a = dca['agg']
C['bt4'] = {'name': ['周期末日', '末日+T5', '末日+T10', '末日+T20'],
            'med': [round(a['ret_end']['median'], 2), round(a['ret_t5']['median'], 2),
                    round(a['ret_t10']['median'], 2), round(a['ret_t20']['median'], 2)],
            'win': [round(a['ret_end']['win'], 1), round(a['ret_t5']['win'], 1),
                    round(a['ret_t10']['win'], 1), round(a['ret_t20']['win'], 1)]}

DATA_JS = 'var CHART = ' + json.dumps(C, ensure_ascii=False) + ';'

# ---------------- HTML 模板 ----------------
HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CCL 嘉年华邮轮 · 全面分析（62 号）</title>
__ECHARTS_LIB__
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;--amber:#b45309;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:13.5px;margin:16px 0 8px;color:#374151;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;}
  .note2{color:var(--sub);font-size:11px;font-weight:400;}
  td.up{color:var(--verm);font-weight:600;white-space:nowrap;}
  td.dn{color:var(--teal);font-weight:600;white-space:nowrap;}
  td.na{color:#c3c8cf;white-space:nowrap;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .callout{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}
  .callout.blue{border-color:#cfe0f5;background:#f0f6fd;}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
  .term{border-bottom:1px dashed var(--blue);cursor:help;position:relative;}
  .term .tip{display:none;position:absolute;bottom:130%;left:0;background:#1f2329;color:#fff;padding:7px 10px;border-radius:7px;font-size:11.5px;width:230px;z-index:50;box-shadow:0 3px 10px rgba(0,0,0,.25);font-weight:400;line-height:1.5;}
  .term:hover .tip{display:block;}
  .kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0;}
  @media(max-width:900px){.kpi-row{grid-template-columns:repeat(2,1fr);}}
  .kpi{background:#fafbfc;border:1px solid var(--line);border-radius:10px;padding:10px 12px;}
  .kpi .k{color:var(--sub);font-size:11px;}
  .kpi .v{font-size:17px;font-weight:700;margin-top:2px;}
  .kpi .v.up{color:var(--verm);} .kpi .v.dn{color:var(--teal);}
  .kpi .s{font-size:10.5px;color:var(--sub);}
  .grid1{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid1{grid-template-columns:1fr;}}
  ul.tight{padding-left:20px;margin:6px 0;}
  ul.tight li{margin-bottom:4px;font-size:13px;}
  .tag{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:600;margin-right:4px;}
  .tag.r{background:#fdeaea;color:var(--verm);} .tag.g{background:#e6f4ee;color:var(--teal);}
  .tag.a{background:#fdf3e0;color:var(--amber);} .tag.b{background:#e8f0fa;color:var(--blue);}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>CCL · 嘉年华邮轮全面分析 <span class="tag b">62 号</span></h1>
  <div class="meta">基本面 × 估值 × 技术面 × 量化回测 × 行业格局 × 风险 ｜ 数据时点：<b>2026-09-01</b>（价格快照 23.44 美元）；技术面基于本地日线 <b>2026-08-27</b> 收盘（24.95）｜ 回测数据 2000-01 ~ 2026-08 ｜ 公开财务数据：westock / MarketBeat / TipRanks / TIKR / Zacks 等（2026-07 ~ 09 报道）</div>

  <div class="callout blue">
    <b>一句话结论：</b>基本面在持续兑现（Q2 FY2026 创纪录、预订满、S&amp;P 上调至 BBB- 投资级、去杠杆 3.1x），但股价 YTD −17%、贴近 52 周低，是典型的「基本面与股价背离」。估值（forward PE ~11×、EV/EBITDA ~8×）显著低于同业与行业均值，市场担忧集中于中东冲突压欧洲 yield、加勒比供给 +27%、杠杆仍高三件事。量化回测给出明确的抄底纪律：<b>RSI&lt;30 × 60 日回撤 ≤−30% 是历史最优买点组合（fwd20 中位 +24.5%、胜率 88.9%）</b>，而当前 RSI 35.4 尚未触发——右侧确认前不急于左侧重仓。
  </div>

  <h3>核心速览</h3>
  <div class="kpi-row">
    <div class="kpi"><div class="k">现价（09-01）</div><div class="v">$23.44</div><div class="s">52 周区间 23.45–34.03</div></div>
    <div class="kpi"><div class="k">YTD / 1Y</div><div class="v dn">−17.0% / −20.5%</div><div class="s">SPY 1Y ≈ +18.9%</div></div>
    <div class="kpi"><div class="k">TTM PE / Fwd PE</div><div class="v">10.6 / 11.3×</div><div class="s">行业均值 fwd PE 16.65</div></div>
    <div class="kpi"><div class="k">EV/EBITDA</div><div class="v">8.1–8.2×</div><div class="s">RCL 12.9× / NCLH 9.7×</div></div>
    <div class="kpi"><div class="k">FY2026 指引 EPS</div><div class="v up">$2.22</div><div class="s">上调 +$0.01（回购）</div></div>
    <div class="kpi"><div class="k">净债务 / EBITDA</div><div class="v">3.1×</div><div class="s">FY2025 末 3.4× → 持续去杠杆</div></div>
    <div class="kpi"><div class="k">RSI14（08-27）</div><div class="v">35.4</div><div class="s">30–40 档，未触超卖</div></div>
    <div class="kpi"><div class="k">分析师共识</div><div class="v up">Strong Buy</div><div class="s">均值目标 $35.30（+27.8%）</div></div>
  </div>
</div>

<div class="card">
  <h2>一、公司概况与商业模式</h2>
  <p>嘉年华邮轮（Carnival Corporation &amp; plc，NYSE: CCL）是全球最大的邮轮运营商，9 大品牌覆盖从大众市场到奢华市场（Carnival Cruise Line、Princess、Holland America、Costa、AIDA、Cunard、Seabourn、P&amp;O 等），运营 90+ 艘船舶、约 25 万下铺位（lower berths）。收入两大来源：<span class="term">船票<span class="tip">乘客船票收入：按舱位、航线、航期定价，Q2 反映提前预订（booked position）与现价（close-in）销售。</span></span> + <span class="term">船上消费<span class="tip">酒水、赌场、岸上游、特色餐饮、零售等，margin 高于船票，是利润率扩张的关键杠杆。</span></span>，另加自有/运营的目的地（Celebration Key、RelaxAway Half Moon Cay 等，Paradise Collection 预计明年超 900 万人次到访）。</p>
  <div class="grid1">
    <div>
      <h3>收入结构（FY2025，全年 266 亿美元）</h3>
      <table>
        <tr><th>业务板块</th><th style="text-align:right">收入（亿美元）</th><th style="text-align:right">占比</th></tr>
        <tr><td>北美邮轮运营</td><td class="nowrap" style="text-align:right">176.04</td><td class="up" style="text-align:right">66.1%</td></tr>
        <tr><td>欧洲邮轮运营</td><td class="nowrap" style="text-align:right">84.67</td><td style="text-align:right">31.8%</td></tr>
        <tr><td>邮轮支持</td><td class="nowrap" style="text-align:right">3.09</td><td style="text-align:right">1.2%</td></tr>
        <tr><td>旅游及其他</td><td class="nowrap" style="text-align:right">2.41</td><td style="text-align:right">0.9%</td></tr>
      </table>
      <div class="src">来源：westock 主营构成（截至 2025-11-30）</div>
    </div>
    <div>
      <h3>商业模式要点</h3>
      <ul class="tight">
        <li>高固定成本 + 高经营杠杆：船队折旧/人工/燃油占比高，上座率与净票价（net per diem）是利润核心驱动。</li>
        <li>强季节性：Q3（暑期，欧洲+阿拉斯加）为盈利高峰，Q1 最弱。</li>
        <li>需求顺周期：可选消费属性，宏观衰退时量价双杀（2020 年极端案例）。</li>
        <li>供给端纪律：维持每年 1–2 艘交付节奏（已订 Princess 2035/2038/2039），重点转向船队现代化（Holland America "Evolution" 六船改造）与自有目的地变现。</li>
        <li>2026-05-07 完成 DLC 结构统一（单一股票、单一上市），降低行政成本、利于指数纳入。</li>
      </ul>
    </div>
  </div>
</div>

<div class="card">
  <h2>二、最新业绩：Q2 FY2026（截至 2026-05-31）</h2>
  <div class="callout blue"><b>定性：</b>收入、净收益率（net yield）、EBITDA、净利、客户存款五创纪录，但营收小幅低于预期、全年 yield 指引下调——「量价强、指引收」的分歧型财报。</div>
  <div class="grid1">
    <div>
      <h3>关键财务数据</h3>
      <table>
        <tr><th>指标</th><th style="text-align:right">Q2 FY26</th><th style="text-align:right">同比</th><th style="text-align:right">说明</th></tr>
        <tr><td>营收</td><td class="nowrap" style="text-align:right">$66.6 亿</td><td class="up" style="text-align:right">+5.3%</td><td>略低于预期 $66.9 亿</td></tr>
        <tr><td>调整后净利</td><td class="nowrap" style="text-align:right">$5.69 亿</td><td class="up" style="text-align:right">+20%+</td><td>超 3 月指引 $1.0 亿（≈$0.07/股）</td></tr>
        <tr><td>调整后 EPS</td><td class="nowrap" style="text-align:right">$0.41</td><td class="up" style="text-align:right">—</td><td>超一致预期 $0.34</td></tr>
        <tr><td>净收益率 Net Yield</td><td class="nowrap" style="text-align:right">+2.2%</td><td class="up" style="text-align:right">—</td><td>CC 口径</td></tr>
        <tr><td>经营现金流</td><td class="nowrap" style="text-align:right">$26.1 亿</td><td class="up" style="text-align:right">—</td><td>—</td></tr>
        <tr><td>自由现金流</td><td class="nowrap" style="text-align:right">$17.3 亿</td><td class="up" style="text-align:right">—</td><td>资本开支占营收 13.1%</td></tr>
        <tr><td>客户存款</td><td class="nowrap" style="text-align:right">$90 亿</td><td class="up" style="text-align:right">历史新高</td><td>反映未来航程预订现金</td></tr>
      </table>
      <div class="src">来源：westock 财务指标（20260623 发布）+ TipRanks/MarketBeat 财报报道</div>
    </div>
    <div>
      <h3>预订与指引</h3>
      <ul class="tight">
        <li><b>FY2026 已预订 93%</b>，2027 预订量与价格均领先去年同期 → 需求侧确定性高。</li>
        <li>FY2026 EPS 指引上调至 <b>$2.22</b>（中值，回购贡献 +$0.01）。</li>
        <li>全年净 yield 增长指引下调至 <b>~2.25%</b>（约 −100bp，主要因中东冲突扰动欧洲航线；管理层定性为「暂时性」）。</li>
        <li>单位邮轮成本（除燃料）同比基本持平，比 3 月指引优 ~250bp；燃料效率同比 +5% 以上（去年 +6% 以上）→ 成本侧持续兑现。</li>
        <li>成本节省已嵌入全年指引（约 $0.06/股），另有折旧/燃料/净利息等 ~$0.08/股顺风。</li>
        <li>2026-05-07 DLC 统一完成；回购已执行 &gt;1700 万股 ≈ $4.5 亿（授权 $25 亿），2026 年合计返还股东 ≈ $13 亿（回购+分红）。</li>
      </ul>
    </div>
  </div>
  <h3>近 7 个季度营收与 EPS（GAAP）</h3>
  <div id="ch_fund" class="chart" style="height:320px"></div>
  <div class="src">来源：westock/MarketBeat/TipRanks 财报序列；FY2025 全年：营收 $266 亿（+6%）、净利 $27.6 亿、EPS $2.22。注：2025 财年口径为 12 月年结。</div>
</div>

<div class="card">
  <h2>三、资产负债表与去杠杆进展</h2>
  <div class="grid1">
    <div>
      <h3>债务与杠杆</h3>
      <table>
        <tr><th>指标</th><th style="text-align:right">数值</th><th>说明</th></tr>
        <tr><td>总资产 / 总负债</td><td class="nowrap" style="text-align:right">$522 / $392 亿</td><td>资产负债率 75.1%</td></tr>
        <tr><td>净债务</td><td class="nowrap" style="text-align:right">≈$239 亿</td><td>截至 2026-05-31</td></tr>
        <tr><td>净债务/调整后 EBITDA</td><td class="nowrap" style="text-align:right">3.1×</td><td>FY25 末 3.4× → Q1 3.3× → Q2 3.1×</td></tr>
        <tr><td>债务/权益</td><td class="nowrap" style="text-align:right">~192%</td><td>疫情期再融资遗留</td></tr>
        <tr><td>评级</td><td class="nowrap" style="text-align:right">BBB-（S&amp;P）</td><td>2026-06 上调（Fitch 2025-10 已给）</td></tr>
      </table>
      <div class="src">来源：westock 财务指标 + TIKR（净债务 $239 亿、3.1×）+ S&amp;P 评级行动报道</div>
    </div>
    <div>
      <h3>去杠杆路径与资本返还</h3>
      <ul class="tight">
        <li>S&amp;P 上调理由：FY2026 已订 93%、2027 领先、预计 FFO/债务 ~25%（升级阈值 3.75×）。Fitch 2025-10 已先达投资级；Moody's 尚未跟随。</li>
        <li>共识预期：净债务 FY2025 末 $247 亿 → FY2030 ≈$157 亿，杠杆 &lt;2×。</li>
        <li>资本返还开启：2026 年回购 $4.5 亿（授权 $25 亿）+ 年股息 $0.15/股（收益率 ~2.3%）。</li>
        <li>投资级评级解锁债券指数纳入与机构配置，是估值修复的制度性催化。</li>
      </ul>
    </div>
  </div>
  <div class="verdict gr"><b>点评：</b>杠杆是 CCL 相对同业最大的折价因子（RCL 已更快去杠杆），但趋势方向正确且已跨过投资级门槛。利率下行周期中利息负担的边际改善将成为 2027 年 EPS 的顺风（CEO 提及净利息为指引顺风项之一）。</div>
</div>

<div class="card">
  <h2>四、估值分析：便宜，但折价有原因</h2>
  <div id="ch_val" class="chart" style="height:320px"></div>
  <table style="margin-top:10px">
    <tr><th>估值指标</th><th style="text-align:right">CCL</th><th style="text-align:right">RCL</th><th style="text-align:right">NCLH</th><th>对比结论</th></tr>
    <tr><td>Forward PE</td><td class="up" style="text-align:right">11.3×</td><td style="text-align:right">16.7×</td><td style="text-align:right">12.5×</td><td>CCL 较 RCL 折价 ~32%</td></tr>
    <tr><td>TTM PE（7 月口径）</td><td class="up" style="text-align:right">11.8×</td><td style="text-align:right">17.2×</td><td style="text-align:right">15.7×</td><td>三家最低</td></tr>
    <tr><td>EV/EBITDA（fwd）</td><td class="up" style="text-align:right">8.1–8.2×</td><td style="text-align:right">12.9–14.1×</td><td style="text-align:right">8.6–9.7×</td><td>三家最低</td></tr>
    <tr><td>vs 行业均值</td><td class="up" style="text-align:right">10.6× fwd PE</td><td colspan="2" style="text-align:right">行业均值 16.65×</td><td>折价 ~36%</td></tr>
  </table>
  <div class="src">来源：Zacks（CCL fwd PE 10.64 vs 行业 16.65）、TIKR（8.2×/11.3× vs RCL 12.9×/16.7× vs NCLH 9.7×/12.5×）、ainvest（TTM 口径）。数值随价格时点略有差异。</div>

  <h3>折价的三个归因</h3>
  <ul class="tight">
    <li><b>船队老龄化：</b>Holland America 等品牌存在 2002 年入役的 Vista 级船，餐饮/娱乐/设施体验落后于 RCL 的 Icon 级新船 → 定价能力与净收益率上限受压（"Evolution" 翻新计划正是回应，Oosterdam 2027 秋启动）。</li>
    <li><b>杠杆与资本结构：</b>D/E ~192%、净债务 $239 亿，风险溢价高于 RCL。</li>
    <li><b>盈利质量：</b>FY2026 共识 EPS 预计同比 −1.8%（yield 指引下调 + 中东扰动），增长质量弱于 RCL 的双位数。</li>
  </ul>

  <h3>卖方与模型估值</h3>
  <div class="grid1">
    <div>
      <table>
        <tr><th>口径</th><th style="text-align:right">目标价</th><th style="text-align:right">空间</th></tr>
        <tr><td>分析师均值（27 家）</td><td class="nowrap" style="text-align:right">$35.30</td><td class="up" style="text-align:right">+27.8%</td></tr>
        <tr><td>Street 最高</td><td class="nowrap" style="text-align:right">$45</td><td class="up" style="text-align:right">+62.9%</td></tr>
        <tr><td>Bernstein（Hold）</td><td class="nowrap" style="text-align:right">$28.70</td><td class="up" style="text-align:right">+3.9%</td></tr>
        <tr><td>TIKR 模型（中值）</td><td class="nowrap" style="text-align:right">≈$53</td><td class="up" style="text-align:right">+83%（15%/年）</td></tr>
      </table>
      <div class="src">来源：Barchart（27 家，20 Strong Buy / 1 Moderate Buy / 6 Hold，共识 Strong Buy）、TIKR 估值模型（营收 +4%/年、净利率 →13%、EPS CAGR 9%）</div>
    </div>
    <div>
      <div class="callout amber"><b>价值陷阱 vs 折价修复？</b>8× EV/EBITDA 已计入「老船 + 高杠杆 + 增长放缓」的大部分负面。修复路径 = ① 去杠杆继续（2027 净利息改善）② Holland America 翻新后 yield 上行验证 ③ 加勒比供给消化后定价回稳。三者任一兑现都会触发估值向 10–12× 修复；反之（衰退 + 供给过剩并行）则维持低估值甚至下探。</div>
    </div>
  </div>
</div>

<div class="card">
  <h2>五、股价历史与技术面</h2>
  <div id="ch_long" class="chart" style="height:340px"></div>
  <div class="src">月度收盘价（对数轴），2000-01 ~ 2026-08。阶段收益：疫情前（2000–2019）+74.6% ｜ 疫情期（2020–2022）−84.1% ｜ 复苏牛市（2023 起）+218.1%。</div>
  <div id="ch_px" class="chart" style="height:460px;margin-top:6px"></div>
  <div class="src">近 500 日（约 2 年）：收盘价 + EMA20/50 + SMA200，副图为 RSI14（Wilder）。红涨绿跌。</div>

  <h3>关键技术状态（08-27 收盘 $24.95）</h3>
  <div class="kpi-row">
    <div class="kpi"><div class="k">RSI14</div><div class="v">35.4</div><div class="s">30–40 档</div></div>
    <div class="kpi"><div class="k">EMA20 / 乖离</div><div class="v dn">$26.73 / −6.7%</div><div class="s">压制</div></div>
    <div class="kpi"><div class="k">EMA50 / 乖离</div><div class="v dn">$27.11 / −8.0%</div><div class="s">压制</div></div>
    <div class="kpi"><div class="k">SMA200 / 乖离</div><div class="v dn">$27.58 / −9.5%</div><div class="s">压制</div></div>
    <div class="kpi"><div class="k">60 日回撤</div><div class="v dn">−18.8%</div><div class="s">未到 −30% 深跌阈值</div></div>
    <div class="kpi"><div class="k">250 日回撤</div><div class="v dn">−25.4%</div><div class="s">距 52 周高 −26.7%</div></div>
    <div class="kpi"><div class="k">52 周区间</div><div class="v">23.45–34.03</div><div class="s">09-01 收 23.44 ≈ 区间下沿</div></div>
    <div class="kpi"><div class="k">3Y 收益</div><div class="v up">+61.9%</div><div class="s">牛市 +218% 后回吐</div></div>
  </div>
  <div class="verdict amber"><b>技术判断：</b>均线空头排列（EMA20 &lt; EMA50 &lt; SMA200）且价格全部跌破，趋势偏弱；RSI 35.4 处于 30–40 档、接近 30–35「下跌中段」陷阱区（见第七章回测证据）。价格在 52 周低 23.45 附近获得支撑（09-01 收 23.44 恰触前低），但企稳需先收复 EMA20（$26.7）。</div>
  <h3>年度收益（红涨绿跌）</h3>
  <div id="ch_year" class="chart" style="height:300px"></div>
  <div class="src">数据：本地日线 adj_close 计算（2016–2026YTD）。2020 −56.9%、2022 −59.9%（两轮疫情/加息熊市），2023 +130.0%（复苏主升）。</div>
</div>

<div class="card">
  <h2>六、量化回测专章（56 号沉淀 · 4 套口径 · 2000-2026）</h2>
  <div class="callout blue">本专章回答：<b>「CCL 跌到什么位置值得买？」</b>——基于 26 年日线（6703 根）的 4 套 RSI/回撤/DCA 回测。所有收益均为持有 T+N 交易日的 fwd 收益（%），超额 = CCL − SPY 同期。状态式信号因窗口重叠，显著性视为上限。</div>

  <h3>6.1 状态式：RSI 档位当日买入（当日收盘 RSI 处于档位 → 买入持有 T+20）</h3>
  <div id="ch_bt1" class="chart" style="height:330px"></div>
  <table style="margin-top:8px">
    <tr><th>RSI 档位</th><th style="text-align:right">样本数</th><th style="text-align:right">fwd20 中位</th><th style="text-align:right">胜率</th><th style="text-align:right">显著性</th></tr>
    <tr><td>&lt;30</td><td style="text-align:right">274</td><td class="up" style="text-align:right">+3.60%</td><td class="up" style="text-align:right">65.7%</td><td>均值不显著 / 胜率显著</td></tr>
    <tr><td>30–40</td><td style="text-align:right">963</td><td class="up" style="text-align:right">+1.07%</td><td class="up" style="text-align:right">55.0%</td><td>均值+胜率均显著</td></tr>
    <tr><td>40–50</td><td style="text-align:right">1832</td><td class="up" style="text-align:right">+1.44%</td><td class="up" style="text-align:right">55.9%</td><td>均值+胜率均显著</td></tr>
    <tr><td>50–60</td><td style="text-align:right">1960</td><td class="dn" style="text-align:right">−0.51%</td><td class="dn" style="text-align:right">47.7%</td><td>不显著（最差档）</td></tr>
    <tr><td>60–70</td><td style="text-align:right">1228</td><td class="up" style="text-align:right">+0.66%</td><td style="text-align:right">52.9%</td><td>胜率显著</td></tr>
    <tr><td>≥70</td><td style="text-align:right">425</td><td class="up" style="text-align:right">+0.76%</td><td style="text-align:right">55.5%</td><td>显著</td></tr>
  </table>
  <div class="verdict"><b>解读：</b>RSI&lt;50 的状态买入普遍有正收益（fwd20 中位 +1.1~+3.6%），但 <b>50–60 档反而最差</b>——横盘/阴跌中段的「看似便宜」最不可买。RSI&lt;30 的 fwd20 中位（+3.6%）与胜率（65.7%）显著优于其他档，验证「超卖后买入」方向有效。</div>

  <h3>6.2 越跌越买：RSI 区间跌落买入（跌入更低档即买一次，T+20）</h3>
  <div id="ch_bt2" class="chart" style="height:330px"></div>
  <table style="margin-top:8px">
    <tr><th>触发档</th><th style="text-align:right">事件数</th><th style="text-align:right">fwd20 中位</th><th style="text-align:right">胜率</th><th style="text-align:right">超额（vs SPY）</th><th style="text-align:right">10 日去重后 fwd20</th></tr>
    <tr><td>35–40（首跌档）</td><td style="text-align:right">249</td><td class="up" style="text-align:right">+1.41%</td><td style="text-align:right">55.8%</td><td style="text-align:right">+0.42pp</td><td style="text-align:right">+1.31%（n=150）</td></tr>
    <tr><td>30–35（⚠️ 陷阱区）</td><td style="text-align:right">146</td><td class="dn" style="text-align:right">−0.18%</td><td class="dn" style="text-align:right">49.3%</td><td class="dn" style="text-align:right">−0.68pp</td><td style="text-align:right">−0.36%（n=40）</td></tr>
    <tr><td>&lt;30（深超卖）</td><td style="text-align:right">79</td><td class="up" style="text-align:right">+3.70%</td><td class="up" style="text-align:right">64.6%</td><td class="up" style="text-align:right">+0.74pp</td><td class="up" style="text-align:right">+4.46%（n=13，胜率 84.6%）</td></tr>
  </table>
  <div class="verdict"><b>核心发现：30–35 档是「下跌中段」而非超卖。</b>触发后 20 日内有 51% 概率继续跌破 RSI 30（35–40 档仅 30%）。CCL 高波动下，跌入 30–35 的「第一次抄底」多为接飞刀；真正有效买点是<b>跌穿 30 之后</b>（fwd20 中位 +3.7%、去重后 +4.46%、胜率 84.6%）。</div>

  <h3>6.3 深跌分层：RSI&lt;30 × 60 日回撤（alpha 在回撤深度，不在 RSI 数值）</h3>
  <div id="ch_bt3" class="chart" style="height:330px"></div>
  <table style="margin-top:8px">
    <tr><th>分组</th><th style="text-align:right">样本</th><th style="text-align:right">fwd20 中位</th><th style="text-align:right">胜率</th><th style="text-align:right">fwd20 均值</th></tr>
    <tr><td>dd60 &gt; −10%（浅回撤）</td><td style="text-align:right">2</td><td class="dn" style="text-align:right">−1.78%</td><td style="text-align:right">50.0%</td><td class="dn" style="text-align:right">−1.78%</td></tr>
    <tr><td>dd60 −20 ~ −10%</td><td style="text-align:right">33</td><td class="up" style="text-align:right">+3.52%</td><td style="text-align:right">66.7%</td><td class="up" style="text-align:right">+1.74%</td></tr>
    <tr><td>dd60 −30 ~ −20%</td><td style="text-align:right">26</td><td class="up" style="text-align:right">+1.92%</td><td style="text-align:right">57.7%</td><td class="dn" style="text-align:right">−3.08%</td></tr>
    <tr><td><b>dd60 ≤ −30%（深跌）</b></td><td style="text-align:right">18</td><td class="up" style="text-align:right"><b>+14.07%</b></td><td class="up" style="text-align:right"><b>72.2%</b></td><td class="up" style="text-align:right">+13.22%</td></tr>
    <tr><td>其中 RSI 28–30 × dd60≤−30%</td><td style="text-align:right">9</td><td class="up" style="text-align:right"><b>+24.48%</b></td><td class="up" style="text-align:right"><b>88.9%</b></td><td class="up" style="text-align:right">+21.02%</td></tr>
  </table>
  <ul class="tight" style="margin-top:8px">
    <li><b>RSI 30 线本身无分层能力：</b>控制回撤深度后，&lt;30 vs ≥30 的 fwd20 中位打平（~+10% vs ~+11%）——市场常用的「RSI&lt;30 抄底」单独用无效。</li>
    <li><b>唯一假信号：</b>RSI 快速跌至低位但 <b>d2m≤3</b>（3 日内从高位急杀，「反弹快」外观）→ n=12，fwd20 中位 <b>−8.51%</b>、胜率仅 8.3%——急跌不买。</li>
    <li><b>真信号：</b>深跌持续（d2m&gt;3）→ n=67，fwd20 中位 +4.46%、胜率 74.6%；深跌 × RSI 28–30 为历史最优组合。</li>
    <li>案例：2023-10-27（dd60 −38.3%、RSI 28）fwd20 <b>+31.4%</b>；2026-03-12（dd60 −29.3%）fwd20 <b>+17.0%</b>；2025-03-06（dd60 −26.7% 但 d2m=12）fwd20 <b>−17.2%</b>（反例：深度不够）。</li>
  </ul>
  <div class="verdict gr"><b>结论：CCL 的可靠抄底条件 = RSI&lt;30 × 60 日回撤 ≤−30% × 非急杀（d2m&gt;3）</b>，历史上 9–18 次触发，fwd20 中位 +14~24%、胜率 72–89%。当前（08-27）RSI 35.4、dd60 −18.8% —— 两个条件都未满足。</div>

  <h3>6.4 定投视角：RSI&lt;30 期间等额定投（$1/日，RSI≥30 停止）</h3>
  <div id="ch_bt4" class="chart" style="height:330px"></div>
  <table style="margin-top:8px">
    <tr><th>结算时点</th><th style="text-align:right">中位收益</th><th style="text-align:right">胜率</th><th>含义</th></tr>
    <tr><td>周期末日（RSI 回 30）</td><td class="dn" style="text-align:right">0.00%</td><td class="dn" style="text-align:right">15.0%</td><td>「RSI 回 30 就卖」在底部区割肉，平均 −1.4%</td></tr>
    <tr><td>末日 + T5</td><td class="up" style="text-align:right">+2.67%</td><td class="up" style="text-align:right">73.8%</td><td>—</td></tr>
    <tr><td>末日 + T10</td><td class="up" style="text-align:right">+1.79%</td><td style="text-align:right">65.0%</td><td>—</td></tr>
    <tr><td><b>末日 + T20</b></td><td class="up" style="text-align:right"><b>+4.04%</b></td><td class="up" style="text-align:right"><b>67.5%</b></td><td>SPY 同期定投 +2.94%（胜率 76.2%）</td></tr>
  </table>
  <ul class="tight" style="margin-top:8px">
    <li>80 个 RSI&lt;30 周期；<b>本轮牛市（2023 起）阶段 T+20 中位 +11.91%、胜率 76.9%</b>，显著优于疫情前（+3.28%）。</li>
    <li>⚠️ 等权中位数受个别假信号污染：资金加权口径仅 ≈+1.08%（深熊定投期吸走 32% 资金摊薄收益）；T+60 中位更高（≈+9.1%）。</li>
    <li>实用含义：RSI&lt;30 定投 ≠ 止损信号；延长持有至 T+20/60 才兑现统计优势，末日即卖是最差选择。</li>
  </ul>
</div>

<div class="card">
  <h2>七、行业格局与竞争</h2>
  <div class="grid1">
    <div>
      <h3>三大上市邮轮对比</h3>
      <table>
        <tr><th>公司</th><th>定位</th><th>增长/估值特征</th></tr>
        <tr><td><b>CCL</b></td><td>全球最大、品牌最全（大众→奢华）</td><td>1–2 艘/年 + 船队现代化；fwd PE 11×，最低</td></tr>
        <tr><td><b>RCL</b></td><td>新船 + 生态系统（Icon 级、Royal Beach Club、Perfect Day）</td><td>双位数增长，fwd PE 16.7×，溢价最高</td></tr>
        <tr><td><b>NCLH</b></td><td>中高端</td><td>2026 开局落后预订曲线，转型中；SG&amp;A 节省 $1.25 亿目标；fwd PE 12.5×</td></tr>
      </table>
      <div class="src">来源：Nasdaq/Zacks 行业报道、TIKR 估值对比</div>
    </div>
    <div>
      <h3>供需焦点</h3>
      <ul class="tight">
        <li><b>供给：</b>加勒比运力两年 +27%（CCL CEO 主动披露，已计入规划）；秋季/冬季加勒比航线出现更激进折价，NCLH 半年促销被指「疫情后最激进」。→ 2027 定价是核心变量。</li>
        <li><b>需求：</b>CCL 2026 已订 93%、2027 量价领先；RCL 双位数增长预期——需求侧整体健康。</li>
        <li><b>地缘：</b>中东冲突延长压制地中海（欧洲区）yield，管理层定性暂时性；红海绕行推高燃油/航程成本。</li>
        <li><b>汇率/油价：</b>欧洲收入占比 32%，欧元波动影响折算；燃油效率年改善 +5% 对冲部分油价风险。</li>
      </ul>
    </div>
  </div>
</div>

<div class="card">
  <h2>八、风险因素</h2>
  <table>
    <tr><th>风险</th><th>影响路径</th><th>当前状态</th></tr>
    <tr><td>需求/衰退</td><td>可选消费首当其冲：船票量价 + 船上消费双降</td><td>预订满，未现；但宏观下行是尾部风险</td></tr>
    <tr><td>杠杆与利率</td><td>净债务 $239 亿、3.1×；高利率压制净利息</td><td>投资级已获，利率下行反而顺风</td></tr>
    <tr><td>燃料成本</td><td>油价上行直接侵蚀成本端</td><td>效率 +5% 对冲；中东扰动油价</td></tr>
    <tr><td>地缘</td><td>中东冲突延长 → 地中海航线/yield 持续承压</td><td>正在发生（全年指引 −100bp 已计提）</td></tr>
    <tr><td>供给过剩</td><td>加勒比 +27% 运力 → 2027 折价战</td><td>折价已现（秋季/冬季），NCLH 促销最激进</td></tr>
    <tr><td>执行</td><td>Holland America Evolution 翻新 ROI、自有目的地变现不及预期</td><td>2027 起验证</td></tr>
    <tr><td>汇率</td><td>非美收入 32%，欧元/英镑波动</td><td>中性</td></tr>
  </table>
</div>

<div class="card">
  <h2>九、结论与情景</h2>
  <div class="callout blue"><b>综合判断（置信度：中高）：</b>CCL 是「基本面修复 + 估值折价」组合，基本面拐点已确认（预订、去杠杆、评级、回购），股价拐点未确认（技术弱势、中东扰动、供给担忧）。量化纪律给出明确的行动框架——<b>未触发 RSI&lt;30 × dd60≤−30% 前，左侧仓位保持克制；右侧以站回 EMA20（$26.7）为确认</b>。</div>
  <table>
    <tr><th>情景</th><th>触发条件</th><th>估值锚</th><th>12 个月区间</th><th>概率</th></tr>
    <tr><td class="up">乐观（折价修复）</td><td>去杠杆 + 回购 + 2027 定价回稳，估值修复至 12–13×</td><td>fwd EPS $2.59（FY27E）</td><td class="up">$31–34（+32~45%）</td><td>~35%</td></tr>
    <tr><td>基准（震荡消化）</td><td>中东影响消退但加勒比折价延续，估值 10–11×</td><td>FY26 $2.22–2.59</td><td>$24–29（+2~24%）</td><td>~45%</td></tr>
    <tr><td class="dn">悲观（戴维斯双杀）</td><td>宏观衰退 + 供给过剩并行，估值回落至 7–8×</td><td>EPS 下修</td><td class="dn">$18–22（−23~−6%）</td><td>~20%</td></tr>
  </table>
  <div class="src">情景为分析性估计（非预测）；分析师均值目标 $35.30（+27.8%）。回测支撑：历史最优买点组合（RSI&lt;30×dd60≤−30%）fwd20 中位 +24.5%——若未来 1–2 个月内触发，从当前价位起的反弹弹性可观。</div>
  <div class="verdict gr"><b>操作框架（供参考，非投资建议）：</b>① 左侧：等待 RSI&lt;30 且 60 日回撤 ≥30% 且非 3 日急杀，分批建仓；② 右侧：日线站回 EMA20 且 EMA20 拐头向上确认趋势反转；③ 仓位：CCL 与 SPY 相关性高（全期 r≈0.57），β≈1.1–1.2，需用仓位而非择时控制组合风险；④ 跟踪：Q3 财报（预计 2026-09-17）、加勒比 2027 定价、中东局势、季度净债务/EBITDA。</div>
</div>

<div class="card">
  <div class="meta">数据来源与口径说明：① 技术面/回测：本地日线（Yahoo 后复权 adj_close，2000-01-03 ~ 2026-08-27，6703 根）+ 4 套回测 JSON（results/ccl_rsi_band_buy / band_dip / sub30_deep / rsi30_dca）；② 基本面/估值：westock 财务指标快照（2026-09-01）、MarketBeat/TipRanks 财报（2026-06-23 发布 Q2）、Zacks/TIKR/ainvest/Nasdaq 行业与估值报道（2026-07）；③ 现价 23.44 美元为 2026-09-01 westock 快照，与本地 08-27 收盘 24.95 存在 3 个交易日时差，报告中已分别标注；④ 分析师目标价与情景区间为公开信息引用或分析性估计，不构成投资建议。红涨绿跌；术语悬停释义。</div>
</div>

</div>

<script>
__DATA_JS__
(function(){
var C={blue:'#0072B2',orange:'#E69F00',sky:'#56B4E9',purple:'#9467bd',verm:'#D55E00',teal:'#009E73',amber:'#b45309',ink:'#374151',sub:'#6b7280',grid:'#eef0f3'};
function ex(a,b){for(var k in b)a[k]=b[k];return a;}
var $={extend:ex};
function base(grid){
  return {animation:false,textStyle:{color:C.ink},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:'#e5e7eb',textStyle:{color:'#1f2329',fontSize:12}},
    grid:grid||{left:52,right:18,top:30,bottom:28},
    legend:{top:2,textStyle:{fontSize:11,color:C.ink}},
    xAxis:{type:'category',axisLabel:{color:'#4b5563',fontSize:10.5},axisLine:{lineStyle:{color:'#d1d5db'}}},
    yAxis:{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}}};
}
// 近500日 价格+均线+RSI 双panel
(function(){
  var el=document.getElementById('ch_px'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.px500;
  ch.setOption({animation:false,textStyle:{color:C.ink},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:'#e5e7eb',textStyle:{color:'#1f2329',fontSize:12}},
    legend:{data:['收盘价','EMA20','EMA50','SMA200'],top:0,textStyle:{fontSize:11,color:C.ink}},
    axisPointer:{link:[{xAxisIndex:'all'}]},
    grid:[{left:52,right:18,top:28,height:'52%'},{left:52,right:18,top:'78%',height:'16%'}],
    xAxis:[{type:'category',data:d.d,axisLabel:{show:false},axisLine:{lineStyle:{color:'#d1d5db'}}},
           {type:'category',data:d.d,gridIndex:1,axisLabel:{color:'#4b5563',fontSize:9.5,interval:40}}],
    yAxis:[{type:'value',scale:true,axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',gridIndex:1,min:0,max:100,axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}'},splitLine:{show:false}}],
    series:[
      {name:'收盘价',type:'line',data:d.px,symbol:'none',lineStyle:{color:C.blue,width:1.8},itemStyle:{color:C.blue}},
      {name:'EMA20',type:'line',data:d.e20,symbol:'none',lineStyle:{color:C.orange,width:1.2}},
      {name:'EMA50',type:'line',data:d.e50,symbol:'none',lineStyle:{color:C.purple,width:1.2}},
      {name:'SMA200',type:'line',data:d.s200,symbol:'none',lineStyle:{color:C.teal,width:1.2}},
      {name:'RSI14',type:'line',xAxisIndex:1,yAxisIndex:1,data:d.rsi,symbol:'none',lineStyle:{color:C.sky,width:1.3},areaStyle:{color:'rgba(86,180,233,.12)'}}
    ]});
  window.addEventListener('resize',function(){ch.resize();});
})();
// 长周期月度
(function(){
  var el=document.getElementById('ch_long'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.long;
  ch.setOption($.extend(base(),{legend:{data:['月度收盘（对数轴）'],top:0,textStyle:{fontSize:11,color:C.ink}},
    yAxis:{type:'log',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}},
    xAxis:{type:'category',data:d.d,axisLabel:{color:'#4b5563',fontSize:10,interval:35}},
    series:[{name:'月度收盘（对数轴）',type:'line',data:d.c,symbol:'none',lineStyle:{color:C.blue,width:1.5},itemStyle:{color:C.blue},
      markArea:{silent:true,data:[[{xAxis:'2020-03',itemStyle:{color:'rgba(213,94,0,.08)'}},{xAxis:'2022-12'}]],
        label:{show:false}}}]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 年度收益 红涨绿跌
(function(){
  var el=document.getElementById('ch_year'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.year;
  ch.setOption($.extend(base(),{grid:{left:44,right:14,top:16,bottom:26},
    xAxis:{type:'category',data:d.y,axisLabel:{color:'#4b5563',fontSize:10.5,interval:0,rotate:35}},
    yAxis:{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{lineStyle:{color:C.grid}}},
    series:[{type:'bar',data:d.r.map(function(v){return {value:v,itemStyle:{color:v>=0?C.verm:C.teal}};}),
      barWidth:'52%',label:{show:true,position:'top',fontSize:9,color:'#4b5563',formatter:function(p){return p.value.toFixed(1)+'%';}}}]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 季度财务
(function(){
  var el=document.getElementById('ch_fund'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.fund;
  ch.setOption($.extend(base(),{legend:{data:['营收(亿美元)','GAAP EPS(美元)'],top:0,textStyle:{fontSize:11,color:C.ink}},
    grid:{left:50,right:48,top:30,bottom:26},
    yAxis:[{type:'value',name:'营收 $亿',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',name:'EPS $',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{show:false}}],
    series:[
      {name:'营收(亿美元)',type:'bar',data:d.rev,barWidth:'46%',itemStyle:{color:C.sky},label:{show:true,position:'top',fontSize:9,color:'#4b5563'}},
      {name:'GAAP EPS(美元)',type:'line',yAxisIndex:1,data:d.eps,symbol:'circle',symbolSize:6,lineStyle:{color:C.verm,width:1.8},itemStyle:{color:C.verm},
        label:{show:true,position:'top',fontSize:9,color:C.verm,formatter:function(p){return p.value.toFixed(2);}}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 估值对比
(function(){
  var el=document.getElementById('ch_val'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.val;
  ch.setOption($.extend(base(),{legend:{data:['Forward PE','EV/EBITDA'],top:0,textStyle:{fontSize:11,color:C.ink}},
    grid:{left:50,right:18,top:30,bottom:26},
    yAxis:{type:'value',name:'倍数',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}×'},splitLine:{lineStyle:{color:C.grid}}},
    series:[
      {name:'Forward PE',type:'bar',data:d.fwdPE,barWidth:'34%',itemStyle:{color:C.blue},label:{show:true,position:'top',fontSize:10,color:C.ink,formatter:function(p){return p.value+'×';}}},
      {name:'EV/EBITDA',type:'bar',data:d.evEbitda,barWidth:'34%',itemStyle:{color:C.orange},label:{show:true,position:'top',fontSize:10,color:C.ink,formatter:function(p){return p.value+'×';}}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 回测1 状态式档位
(function(){
  var el=document.getElementById('ch_bt1'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.bt1;
  ch.setOption($.extend(base(),{legend:{data:['fwd20 中位','胜率'],top:0,textStyle:{fontSize:11,color:C.ink}},
    grid:{left:52,right:48,top:30,bottom:26},
    yAxis:[{type:'value',name:'fwd20 中位 %',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',name:'胜率 %',min:40,max:75,axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{show:false}}],
    series:[
      {name:'fwd20 中位',type:'bar',data:d.med,barWidth:'46%',itemStyle:{color:function(p){return p.value>=0?C.verm:C.teal;}},
        label:{show:true,position:'top',fontSize:9,formatter:function(p){return p.value.toFixed(2)+'%';}}},
      {name:'胜率',type:'line',yAxisIndex:1,data:d.win,symbol:'circle',symbolSize:6,lineStyle:{color:C.blue,width:1.6},itemStyle:{color:C.blue},
        label:{show:true,position:'top',fontSize:9,color:C.blue,formatter:function(p){return p.value+'%';}}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 回测2 越跌越买
(function(){
  var el=document.getElementById('ch_bt2'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.bt2;
  ch.setOption($.extend(base(),{legend:{data:['fwd20 中位','超额(pp)'],top:0,textStyle:{fontSize:11,color:C.ink}},
    grid:{left:52,right:48,top:30,bottom:26},
    yAxis:[{type:'value',name:'fwd20 中位 %',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',name:'超额 pp',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{show:false}}],
    series:[
      {name:'fwd20 中位',type:'bar',data:d.med,barWidth:'40%',itemStyle:{color:function(p){return p.value>=0?C.verm:C.teal;}},
        label:{show:true,position:'top',fontSize:10,formatter:function(p){return p.value.toFixed(2)+'%';}}},
      {name:'超额(pp)',type:'line',yAxisIndex:1,data:d.ex,symbol:'circle',symbolSize:6,lineStyle:{color:C.blue,width:1.6},itemStyle:{color:C.blue},
        label:{show:true,position:'top',fontSize:9,color:C.blue,formatter:function(p){return p.value>0?'+'+p.value.toFixed(2):p.value.toFixed(2);}}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 回测3 dd60 分层
(function(){
  var el=document.getElementById('ch_bt3'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.bt3;
  ch.setOption($.extend(base(),{legend:{data:['fwd20 中位','胜率'],top:0,textStyle:{fontSize:11,color:C.ink}},
    grid:{left:52,right:48,top:30,bottom:26},
    xAxis:{type:'category',data:d.name,axisLabel:{color:'#4b5563',fontSize:10.5}},
    yAxis:[{type:'value',name:'fwd20 中位 %',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',name:'胜率 %',min:40,max:90,axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{show:false}}],
    series:[
      {name:'fwd20 中位',type:'bar',data:d.med,barWidth:'42%',itemStyle:{color:function(p){return p.value>=0?C.verm:C.teal;}},
        label:{show:true,position:'top',fontSize:9,formatter:function(p){return p.value.toFixed(2)+'%';}}},
      {name:'胜率',type:'line',yAxisIndex:1,data:d.win,symbol:'circle',symbolSize:6,lineStyle:{color:C.blue,width:1.6},itemStyle:{color:C.blue},
        label:{show:true,position:'top',fontSize:9,color:C.blue,formatter:function(p){return p.value+'%';}}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 回测4 DCA
(function(){
  var el=document.getElementById('ch_bt4'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.bt4;
  ch.setOption($.extend(base(),{legend:{data:['中位收益','胜率'],top:0,textStyle:{fontSize:11,color:C.ink}},
    grid:{left:52,right:48,top:30,bottom:26},
    yAxis:[{type:'value',name:'中位收益 %',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',name:'胜率 %',min:0,max:100,axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{show:false}}],
    series:[
      {name:'中位收益',type:'bar',data:d.med,barWidth:'44%',itemStyle:{color:function(p){return p.value>=0?C.verm:C.teal;}},
        label:{show:true,position:'top',fontSize:9,formatter:function(p){return p.value.toFixed(2)+'%';}}},
      {name:'胜率',type:'line',yAxisIndex:1,data:d.win,symbol:'circle',symbolSize:6,lineStyle:{color:C.blue,width:1.6},itemStyle:{color:C.blue},
        label:{show:true,position:'top',fontSize:9,color:C.blue,formatter:function(p){return p.value+'%';}}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
})();
</script>
</body>
</html>
"""

# 组装
lib = open(os.path.join(ROOT, 'Temp', 'ccl_fetch', 'echarts_lib.js'), encoding='utf-8').read()
html = HTML.replace('__ECHARTS_LIB__', '<script>' + lib + '</script>')
html = html.replace('__DATA_JS__', DATA_JS)
out = os.path.join(OUT_DIR, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('written:', out, os.path.getsize(out) / 1024, 'KB')
