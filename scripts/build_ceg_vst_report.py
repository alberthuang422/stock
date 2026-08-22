# -*- coding: utf-8 -*-
"""CEG vs VST 对比研报生成器（读 results/ceg_vst_price.json + 基本面数据）"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "04_ceg_vst电力股对比")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "ceg_vst_price.json")) as f:
    P = json.load(f)

# ---------- 数据提取 ----------
norm = P["norm_series"]
yearly = P["yearly"]
risk = P["risk"]
corr = P["corr_matrix"]
ratio = P["ratio"]
roll = P["roll_chart"]
events = P["events"]
cum = P["cum_ret"]

def js(o):
    return json.dumps(o, ensure_ascii=False)

# 事件窗口图数据：只取后3日与后5日
ev_dates = [e["date"] + " " + e["name"][:14] for e in events]
ev_ceg_p3 = []
ev_vst_p3 = []
ev_ceg_p5 = []
ev_vst_p5 = []
for e in events:
    ev_ceg_p3.append(None if e.get("ceg_post3") is None else round(e["ceg_post3"] * 100, 2))
    ev_vst_p3.append(None if e.get("vst_post3") is None else round(e["vst_post3"] * 100, 2))
    ev_ceg_p5.append(None if e.get("ceg_cum5") is None else round(e["ceg_cum5"] * 100, 2))
    ev_vst_p5.append(None if e.get("vst_cum5") is None else round(e["vst_cum5"] * 100, 2))

# 年度收益图
years = yearly["years"]
year_series = [
    {"name": "CEG", "data": yearly["ceg"]},
    {"name": "VST", "data": yearly["vst"]},
    {"name": "XLU", "data": yearly["xlu"]},
    {"name": "SPY", "data": yearly["spy"]},
]

# 归一化走势图（上市以来）
norm_dates = norm["ceg"]["dates"]
norm_series = [
    {"name": "CEG", "data": [round(v, 3) for v in norm["ceg"]["values"]]},
    {"name": "VST", "data": [round(v, 3) for v in norm["vst"]["values"]]},
    {"name": "XLU", "data": [round(v, 3) for v in norm["xlu"]["values"]]},
    {"name": "SPY", "data": [round(v, 3) for v in norm["spy"]["values"]]},
]

# 相对强弱
ratio_dates = P["ratio_dates"] if "ratio_dates" in P else None

# 滚动相关性
roll_dates = roll["dates"]
roll_vals = roll["values"]

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CEG vs VST · AI 电力双雄对比 · 谁更重要？</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}}
  .wrap{{max-width:1220px;margin:0 auto;}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}}
  h1{{font-size:21px;margin-bottom:4px;}}
  .meta{{color:var(--sub);font-size:12.5px;margin-bottom:14px;}}
  h2{{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}}
  h3{{font-size:14px;margin:14px 0 8px;color:var(--ink);}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:14px;}}
  .kpi{{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
  .kpi .num{{font-size:21px;font-weight:700;}}
  .kpi .num.up{{color:var(--red);}} .kpi .num.dn{{color:var(--green);}}
  .kpi .lab{{color:var(--sub);font-size:12px;margin-top:2px;}}
  .verdict{{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}}
  .verdict .t{{font-size:13px;color:var(--sub);margin-bottom:6px;}}
  .verdict .b{{font-size:16px;font-weight:700;color:var(--ink);}}
  .verdict .b .hl{{color:var(--blue);}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;}}
  th{{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}}
  td{{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}}
  td.up{{color:var(--red);font-weight:600;}} td.dn{{color:var(--green);font-weight:600;}} td.na{{color:#c3c8cf;}}
  td.win{{background:#fff3f3;font-weight:700;}}
  .scroll{{overflow-x:auto;}}
  .chart{{width:100%;height:380px;}}
  .chart.sm{{height:320px;}}
  .note{{color:var(--sub);font-size:12px;margin-top:8px;}}
  .keypoint{{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}}
  .warn{{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;}}
  .dis{{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}}
  .hl{{font-weight:700;color:var(--red);}} .hlg{{font-weight:700;color:var(--green);}} .hlb{{font-weight:700;color:var(--blue);}}
  .tag{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}}
  .tag.ceg{{background:#eef3fb;color:var(--blue);}} .tag.vst{{background:#fdf1e7;color:#c05c0b;}}
  .ratio{{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;}}
  .rbox{{flex:1;min-width:150px;background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:10px 14px;}}
  .rbox .v{{font-size:18px;font-weight:700;}} .rbox .l{{color:var(--sub);font-size:12px;}}
  .tabbar{{display:flex;gap:8px;margin-bottom:10px;}}
  .tabbtn{{padding:4px 14px;border:1px solid var(--line);border-radius:16px;background:#fff;font-size:12.5px;cursor:pointer;color:var(--sub);}}
  .tabbtn.on{{background:var(--blue);color:#fff;border-color:var(--blue);font-weight:600;}}
  .tabbody{{display:none;}} .tabbody.on{{display:block;}}
  .tl{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:13px;}}
  .tl .badge{{padding:3px 10px;border-radius:8px;font-weight:700;font-size:12.5px;}}
  .badge.ceg{{background:#eef3fb;color:var(--blue);}} .badge.vst{{background:#fdf1e7;color:#c05c0b;}} .badge.draw{{background:#f3f5f8;color:var(--sub);}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>CEG（Constellation Energy）vs VST（Vistra）· AI 电力双雄对比</h1>
    <div class="meta">对比窗口：2022-01-19 ~ 2026-08-14（CEG 上市起，Yahoo 前复权日线，基准 XLU/SPY）｜财务：FY2025 年报口径（截至 2025-12-31）｜行情截至 2026-08-14 收盘，美股休市中</div>

    <div class="verdict">
      <div class="t">▍综合判断：谁更重要？</div>
      <div class="b"><span class="tag ceg">CEG</span> 是这轮 AI 电力行情的 <span class="hlb">「定价锚 + 稀缺资产」</span>：纯核电 21 座反应堆不可复制、微软三里岛交易开创核电 PPA 估值范式，行业地位与资产稀缺性更「重要」；
      <span class="tag vst">VST</span> 是 <span class="hl">「弹性 + 性价比」</span> 角色：AI 核电 PPA 总量更大（约 3.8GW vs 1.96GW）、前瞻估值更低、2026 盈利加速，但高杠杆（87% vs 67%）与多元化燃料组合使其「稀缺性」打折。<br>
      一句话：<b>论板块定价权与资产护城河，CEG 更重要；论 2026 当期性价比与盈利弹性，VST 更占优。</b></div>
    </div>

    <div class="kpis">
      <div class="kpi"><div class="num up">+597.7%</div><div class="lab">CEG 上市以来累计收益</div></div>
      <div class="kpi"><div class="num up">+611.7%</div><div class="lab">VST 同区间累计收益（几乎打平）</div></div>
      <div class="kpi"><div class="num">27.6× / 25.0×</div><div class="lab">PE TTM：CEG / VST（前瞻约 18× 更低）</div></div>
      <div class="kpi"><div class="num up">-50.7% / -48.8%</div><div class="lab">历史最大回撤：CEG / VST（同量级高波动）</div></div>
      <div class="kpi"><div class="num">0.70</div><div class="lab">日收益相关性（滚动60日最新 0.79，同涨同跌加剧）</div></div>
    </div>
  </div>

  <div class="card">
    <h2>一、上市以来走势：殊途同归，节奏各异</h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note">归一化（上市首日=1）对数视图：2022 CEG 先行走强（+107%），2024 VST 爆发（+266%），2025 CEG 反超（+46% vs +8%），2026 双双回调（CEG -23% 更深）。五年累计几乎打平，但「谁领涨」每年都在换人。</div>
    <div class="ratio">
      <div class="rbox"><div class="v">CEG/VST 最新比值 {ratio['latest']:.2f}</div><div class="l">起始 {ratio['start']:.2f} → 归一化 {ratio['norm_latest']:.2f}（≈1 即长期平手）</div></div>
      <div class="rbox"><div class="v" style="color:var(--blue);">{ratio['max']:.2f}（{ratio['max_date']}）</div><div class="l">比值最高点 = CEG 相对最强（2022-10）</div></div>
      <div class="rbox"><div class="v" style="color:#c05c0b;">{ratio['min']:.2f}（{ratio['min_date']}）</div><div class="l">比值最低点 = VST 相对最强（2024-11）</div></div>
    </div>
  </div>

  <div class="card">
    <h2>二、年度收益：谁领跑谁垫底（红涨绿跌）</h2>
    <div id="chart_year" class="chart sm"></div>
    <div class="note">2024 是 VST 的年份（+266%，S&P500 年度涨幅冠军级行情）；2022/2025 是 CEG 的年份；2026 YTD 两者都跌但 CEG 跌得更狠（-23% vs -10%），板块 XLU 逆势 +4%、SPY +14% —— <b>2026 的回调是「个股/主题杀估值」而非板块系统性下跌</b>。</div>
  </div>

  <div class="card">
    <h2>三、相对强弱与相关性：同主题，但同涨同跌在加剧</h2>
    <div class="chart" id="chart_corr"></div>
    <div class="note">滚动 60 日 CEG-VST 日收益相关：均值 0.62，最新 0.79 —— 随着 AI 电力主题深化，两者走势越来越同步，个股事件驱动差异在收敛；但相关系数仍低于 1，<b>主题内轮动（谁领涨）依然每年切换</b>。</div>
  </div>

  <div class="card">
    <h2>四、关键事件窗口股价反应（事件日后 3 日 / 5 日累计）</h2>
    <div id="chart_ev" class="chart"></div>
    <div class="note">同一事件对两家影响不对称：CEG 的微软三里岛 PPA（2024-09）公布后 VST 涨得更多（+10% vs +3%）—— 板块效应外溢；CEG 收购 Calpine 完成（2026-01）时 VST 反而 +11.6%，市场对 CEG 整合的担忧>对资产扩表的兴奋。<b>CEG 利好在板块内「外溢」，VST 利好更多「独享」</b>。</div>
  </div>

  <div class="card">
    <h2>五、基本面与业务对比（FY2025 年报口径）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>维度</th><th>CEG（星座能源）</th><th>VST（瑞致达）</th><th>谁占优</th></tr></thead>
      <tbody>
        <tr><td>业务定位</td><td><b>美国最大核电运营商</b>，21 座反应堆/12 厂址约 22GW；收购 Calpine 后约 55GW、约 90% 零碳</td><td>美国最大非监管（merchant）发电商，核+气+煤+光伏+储能约 41-44GW，覆盖 ERCOT/PJM 高增长市场</td><td><span class="tag ceg">CEG · 纯核电稀缺</span></td></tr>
        <tr><td>营收（FY25）</td><td>$255.3 亿（+8.3%）</td><td>$177.4 亿（+2.9%）</td><td><span class="tag ceg">CEG</span></td></tr>
        <tr><td>净利（GAAP）</td><td>$23.19 亿（-38.1%，套保浮亏拖累）</td><td>$9.44 亿（-66.6%，套保+利息+并购）</td><td><span class="tag ceg">CEG · 幅度小</span></td></tr>
        <tr><td>调整后盈利</td><td>调整后经营 EPS $9.39（+8.3%）</td><td>调整后 EBITDA $59.12 亿（+4.8%，创纪录）</td><td><span class="tag draw">口径不同</span></td></tr>
        <tr><td>2026 指引</td><td>调整后经营 EPS $11.00-12.00（+20% 中枢）</td><td>调整后 EBITDA $68-76 亿（+22% 中枢）</td><td><span class="tag draw">增速相当</span></td></tr>
        <tr><td>市值 / PE TTM</td><td>约 $1001 亿 / <b>27.6×</b></td><td>约 $497 亿 / <b>25.0×</b>（前瞻约 18×）</td><td><span class="tag vst">VST · 更便宜</span></td></tr>
        <tr><td>资产负债率</td><td><b>67.1%</b>（长期借款 $191 亿）</td><td><b>87.1%</b>（长期借款 $177 亿，并购杠杆高）</td><td><span class="tag ceg">CEG · 财务更稳</span></td></tr>
        <tr><td>ROE</td><td>15.3%（经营驱动）</td><td>43.1%（杠杆放大，非效率优势）</td><td><span class="tag ceg">CEG · 质量更高</span></td></tr>
        <tr><td>股东回报</td><td>股息率 0.59%</td><td>股息率 0.62%、连续 17 季派息、2021 以来回购约 $59 亿（股本 -30%）</td><td><span class="tag vst">VST · 更积极</span></td></tr>
        <tr><td>AI 核电 PPA</td><td>微软 835MW（$110-115/MWh 高价）+ Meta Clinton 1121MW（$85-90/MWh）+ CyrusOne 380MW 等，明确核长约约 1.96GW</td><td>AWS Comanche Peak 1200MW + Meta 约 2600MW + 光伏 200MW，核电 PPA 合计约 <b>3.8GW</b></td><td><span class="tag vst">VST · 总量更大</span><br><span class="tag ceg">CEG · 单价更高</span></td></tr>
        <tr><td>关键执行风险</td><td>三里岛/Crane 重启（2027 目标）、FERC 共址监管、客户集中</td><td>高杠杆、Moss Landing 电池事故、套保浮亏、气电价格依赖</td><td><span class="tag draw">各有软肋</span></td></tr>
      </tbody>
    </table>
    </div>
    <div class="note">数据来源：FY2025 年报/财报指引（CEG、VST，2026-02 前后披露）；估值与市值：westock-data 行情接口 2026-08-14；AI 合同：公司公告与公开新闻（需核实原文）。CEG 资产负债率两源口径 67.1%（westock）/74%（neodata），此处取结构化数据。</div>
  </div>

  <div class="card">
    <h2>六、为什么「CEG 更重要」：三层推演</h2>
    <div class="keypoint">
      <b>① 定价权层面：</b>微软三里岛 20 年 PPA（$110-115/MWh，市场价 2 倍+）由 CEG 首创，定义了整个核电 PPA 的估值范式 —— 后续 VST 的 AWS/Meta 合同都是在这一锚定下定价的。CEG 是「规则的制定者」，VST 是「规则的跟随者」。<br><br>
      <b>② 资产稀缺性层面：</b>核电 21 反应堆（22GW）是美国不可复制的存量基荷，新核电 2028 年前无增量；CEG 的「重启停机核电站」模式（三里岛）更使其成为唯一能立刻交付 500MW+ 清洁基荷的卖家。VST 的核电机组（6 座、约 6.4GW）规模小一个量级，增长更多靠气电并购 —— 可替代性更高。<br><br>
      <b>③ 财务质量层面：</b>净利率（9.1% vs 4.2%）、资产负债率（67% vs 87%）、利润波动（套保浮亏幅度 CEG 更小）全面占优。高 ROE 是 VST 的杠杆幻觉，不是经营效率优势。
    </div>
    <div class="warn" style="margin-top:10px;">
      <b>反向声音（VST 为什么可能更值得持有）：</b>① 2026 指引 EBITDA +22% vs CEG EPS +20%，且前瞻 PE 约 18× 远低于 CEG 的约 24× —— <b>市场已为 CEG 的「稀缺性」付了溢价，若三里岛重启延期或电价回落，杀估值空间更大（2026 YTD CEG -23% vs VST -10% 已现端倪）</b>；② VST 核电 PPA 总量 3.8GW 实为行业最大，AWS+Meta 双客户更分散；③ 连续回购+派息，股东回报更实在。
    </div>
  </div>

  <div class="card">
    <h2>七、结论</h2>
    <div class="tl">
      <span class="badge ceg">核心持仓（锚）</span><span>：CEG —— 买的是「AI 电力主题的稀缺定价权」，适合看好核电 20 年景气、能承受高波动与执行风险的配置型资金。</span>
    </div>
    <div class="tl" style="margin-top:8px;">
      <span class="badge vst">进攻/性价比（矛）</span><span>：VST —— 买的是「低估值 + 2026 盈利加速 + 回购」，适合认为主题未结束、但想避开 CEG 高估值挤泡沫风险的投资者。</span>
    </div>
    <div class="tl" style="margin-top:8px;">
      <span class="badge draw">主题风险提示</span><span>：两者日收益相关 0.70、滚动 60 日 0.79，<b>本质上是一个仓位的两种表达</b>，组合里同时持有是「加杠杆」不是「分散」；2026 年板块未跌而两者双杀，提示当前定价已充分计入 AI 电力预期，边际催化（新 PPA、FERC 裁决、电价）决定后续方向。</span>
    </div>
  </div>

  <div class="card">
    <div class="dis">
      数据来源：Yahoo Finance 日线（2022-01-19 ~ 2026-08-14，前复权）；CEG/VST FY2025 年报与 2026 指引（公司披露）；估值与市值数据来自 westock-data 行情接口（2026-08-14）；AI 电力合同信息来自公司公告与公开新闻（The Globe and Mail、Investors.com、Asset Market News 等，2024-09 ~ 2026-02，非一手来源需核实原文）。年度收益为自然年口径，2026 为 YTD。分析基于公开数据与量化计算，可能存在口径差异与延迟。
    </div>
    <div class="dis" style="margin-top:8px;">
      <b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
    </div>
  </div>

</div>
<script>
// ---------- 图1 归一化走势 ----------
(function(){{
  var c = document.getElementById('chart_norm');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['CEG', 'VST', 'XLU', 'SPY'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(norm_dates)} }},
    yAxis: {{ type: 'value', name: '归一化(首日=1)', scale: true }},
    series: {js(norm_series)}.map(function(s){{ return {{
      name: s.name, type: 'line', showSymbol: false, smooth: false,
      data: s.data,
      lineStyle: {{ width: 2 }},
      itemStyle: {{ color: s.name === 'CEG' ? '#1e66d6' : s.name === 'VST' ? '#c05c0b' : s.name === 'XLU' ? '#0aa06e' : '#9aa2ad' }}
    }}; }})
  }});
}})();

// ---------- 图2 年度收益 ----------
(function(){{
  var c = document.getElementById('chart_year');
  if (!c) return;
  var ch = echarts.init(c);
  var colors = {{ 'CEG': '#1e66d6', 'VST': '#c05c0b', 'XLU': '#0aa06e', 'SPY': '#9aa2ad' }};
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return v + '%'; }} }},
    legend: {{ data: ['CEG', 'VST', 'XLU', 'SPY'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(years)} }},
    yAxis: {{ type: 'value', name: '年度收益 %' }},
    series: {js(year_series)}.map(function(s){{ return {{
      name: s.name, type: 'bar', barGap: 0.15,
      data: s.data.map(function(v){{ return {{
        value: v,
        itemStyle: {{ color: v >= 0 ? colors[s.name] : '#d64545', borderRadius: [3,3,0,0] }}
      }}; }})
    }}; }})
  }});
}})();

// ---------- 图3 滚动相关性 ----------
(function(){{
  var c = document.getElementById('chart_corr');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return (v === null || v === undefined) ? '-' : v.toFixed(2); }} }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(roll_dates)} }},
    yAxis: {{ type: 'value', name: '60日滚动相关', min: 0, max: 1 }},
    series: [{{
      name: 'CEG-VST 滚动60日相关',
      type: 'line', showSymbol: false, smooth: true,
      data: {js(roll_vals)},
      lineStyle: {{ width: 2, color: '#7048e8' }},
      areaStyle: {{ color: 'rgba(112,72,232,.12)' }},
      markLine: {{ data: [{{ yAxis: 0.616, name: '均值0.62' }}], lineStyle: {{ type: 'dashed', color: '#9aa2ad' }} }}
    }}]
  }});
}})();

// ---------- 图4 事件窗口 ----------
(function(){{
  var c = document.getElementById('chart_ev');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return (v === null || v === undefined) ? '-' : v.toFixed(1) + '%'; }} }},
    legend: {{ data: ['CEG 后3日', 'VST 后3日', 'CEG 后5日', 'VST 后5日'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 70 }},
    xAxis: {{ type: 'category', data: {js(ev_dates)}, axisLabel: {{ rotate: 25, fontSize: 10 }} }},
    yAxis: {{ type: 'value', name: '累计收益 %' }},
    series: [
      {{ name: 'CEG 后3日', type: 'bar', data: {js(ev_ceg_p3)}, itemStyle: {{ color: '#1e66d6' }} }},
      {{ name: 'VST 后3日', type: 'bar', data: {js(ev_vst_p3)}, itemStyle: {{ color: '#7ea7e8' }} }},
      {{ name: 'CEG 后5日', type: 'bar', data: {js(ev_ceg_p5)}, itemStyle: {{ color: '#c05c0b' }} }},
      {{ name: 'VST 后5日', type: 'bar', data: {js(ev_vst_p5)}, itemStyle: {{ color: '#e0a37e' }} }}
    ]
  }});
}})();
</script>
</body>
</html>
"""

out_file = os.path.join(OUT, "ceg_vst_compare_report.html")
with open(out_file, "w") as f:
    f.write(html)
print("已生成:", out_file)
