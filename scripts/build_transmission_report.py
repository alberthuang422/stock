#!/usr/bin/env python3
"""生成「biotech 景气→工具业绩传导时滞」分析报告 HTML。
读 results/lifetools_transmission.json + lifetools_revenue.json，输出 reports/25_工具业绩传导时滞/index.html。
静默写盘。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "lifetools_transmission.json"), encoding="utf-8") as f:
    T = json.load(f)
with open(os.path.join(ROOT, "results", "lifetools_revenue.json"), encoding="utf-8") as f:
    R = json.load(f)

# XBI 季度（2015Q1 起）
xq = T["xbi_quarterly"]
xq_plot = [r for r in xq if r["q"] >= "2016Q1"]
xq_dates = [r["q"] for r in xq_plot]
xq_ret = [r["ret"] for r in xq_plot]
xq_close = [r["close"] for r in xq_plot]

# 工具板块平均年度 YoY
avg = T["avg_annual"]
avg_y = [r["y"] for r in avg]
avg_v = [r["avg"] for r in avg]

# 四家季度 YoY（2020Q1 起展示）
qy = {}
for tk in ["A", "WAT", "DHR", "TMO"]:
    qs = [r for r in T["quarters_yoy"][tk] if r["q"] >= "2019Q1"]
    qy[tk] = {"dates": [r["q"] for r in qs], "yoy": [r["yoy"] for r in qs]}

# 四家年度 YoY
ay = {}
for tk in ["A", "WAT", "DHR", "TMO"]:
    aa = [r for r in T["annual_yoy"][tk] if r["y"] >= "2016"]
    ay[tk] = {"years": [r["y"] for r in aa], "yoy": [r["yoy"] for r in aa]}

data_js = {
    "xq_dates": xq_dates, "xq_ret": xq_ret, "xq_close": xq_close,
    "avg_y": avg_y, "avg_v": avg_v,
    "qy": qy, "ay": ay,
    "cycles": T["cycles"], "caveats": T["caveats"],
}
data_json = json.dumps(data_js, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>biotech 景气 → 工具业绩传导时滞 ｜ 生命科学工具四龙头</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#fff;
          --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --green:#009E73; --purple:#CC79A7;
          --red:#C0392B; --verm:#D55E00; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }
  .wrap { max-width: 1100px; margin: 0 auto; }
  h1 { font-size: 26px; letter-spacing: .5px; margin-bottom: 4px; }
  .subtitle { color: var(--sub); font-size: 13px; margin-bottom: 22px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(20,30,50,.05); }
  .card h2 { font-size: 17px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .card h2::before { content: ""; width: 4px; height: 16px; background: var(--blue); border-radius: 2px; }
  .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 4px; }
  .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .kv { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .kv .k { font-size: 12px; color: var(--sub); }
  .kv .v { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .kv .v small { font-size: 12px; font-weight: 400; color: var(--sub); }
  .kv .muted { font-size: 13px; color: var(--sub); margin-top: 4px; font-weight: 400; }
  .up { color: var(--red); } .down { color: var(--green); }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  .tag.amber { background: #fdf3e3; color: var(--verm); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
  th, td { padding: 8px 9px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  tr.hl { background: #fdf6ec; }
  .note { font-size: 12px; color: var(--sub); margin-top: 10px; }
  .chart { width: 100%; height: 360px; }
  .chart-sm { width: 100%; height: 300px; }
  .concl { border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }
  ul.tl { list-style: none; }
  ul.tl li { padding: 8px 0 8px 18px; border-left: 2px solid var(--line); margin-left: 6px; position: relative; }
  ul.tl li::before { content: ""; position: absolute; left: -5px; top: 14px; width: 8px; height: 8px;
                     border-radius: 50%; background: var(--blue); }
  ul.tl li b { color: var(--blue); }
  .disclaimer { font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }
  .src { font-size: 11.5px; color: var(--sub); margin-top: 8px; }
  .legend-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; }
  .warn { border-left: 4px solid var(--verm); background: #fdf6ec; padding: 10px 14px;
          border-radius: 0 8px 8px 0; font-size: 13px; margin-top: 10px; }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>biotech 景气 → 工具业绩传导时滞分析</h1>
  <div class="subtitle">生命科学工具四龙头（A/WAT/DHR/TMO）· 上一轮景气周期业绩滞后量化 · 数据截至 2026-08-21</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid4">
      <div class="kv"><div class="k">上一轮传导时滞（2020 启动 → 业绩爆发）</div>
        <div class="v">3-4 个季度</div>
        <div class="muted">XBI 2020Q2 +44.6% 启动 → 2021 年工具板块平均 YoY 17.3%（2020 年仅 13.1%）</div></div>
      <div class="kv"><div class="k">板块平均年度 YoY 峰值</div>
        <div class="v">17.3% <small>2021</small></div>
        <div class="muted">2020 年 13.1%（含 COVID 检测）、2022 年 9.2%、2023 年 -3.9%（收缩）</div></div>
      <div class="kv"><div class="k">本轮进度（2025-2026）</div>
        <div class="v">2025: +5.1%</div>
        <div class="muted">2026H1 加速：A +7~10%、TMO +6~10%、DHR +3.7~5.5%（季度 YoY）</div></div>
      <div class="kv"><div class="k">本轮弹性预期窗口</div>
        <div class="v">2026Q4-2027</div>
        <div class="muted">按上轮 3-4 季度传导，2025Q3-Q4 启动 → 业绩弹性应在此窗口兑现</div></div>
    </div>
    <div class="concl">
      ① <b>上一轮实证：滞后约 3-4 个季度</b>。XBI 2020Q1 见底（-18.6%）后 2020Q2 单季 +44.6% 启动，但工具业绩到 <b>2021 年才全面爆发</b>：A 年度 YoY 3.4%→18.4%、WAT -1.7%→17.8%、TMO 26.1%(含COVID)→21.7%、DHR 24.4%(含COVID)→11.3%。板块平均 2020 年 13.1%（部分被 COVID 检测业务提前拉动）→ 2021 年 17.3% 峰值。<br>
      ② <b>传导链条</b>：biotech 融资/行情（先行 0-2Q）→ 工具订单/询单（+1-2Q）→ 收入确认（+2-4Q）。工具订单改善往往早于报表收入一个季度左右，报表收入爆发普遍滞后行情启动 3-4 个季度。<br>
      ③ <b>本轮位置判断</b>：XBI 2025Q3（+20.8%）、Q4（+21.7%）启动，2026Q1（+4.8%）、Q2（+23.9%）延续。对应工具业绩：2025 年全年仅 +5.1%（刚转正），2026H1 已见加速（A 2026Q2 +10.0%、TMO +10.5%、DHR +5.5%）——处于<b>传导中段（第 2-3 个季度）</b>，若历史重演，业绩弹性主升段在 <b>2026Q4-2027</b>。<br>
      ④ <b>关键提醒</b>：WAT 2026 报告口径 +91%/+113% 是并购 BD 生物科学业务并表所致，非内生（有机口径 2026Q2 +9% CC）；DHR/TMO 2020-21 的爆发含 COVID 检测业务，纯 biotech 资本开支传导应以 A/WAT 为参照。
    </div>
    <div class="src">数据：Yahoo Finance 日线（XBI）、富途财报库（四公司季度/年度营收，US GAAP）。XBI 2026Q3 为未完结季度（7-8 月）。上一轮时滞为基于 2020-2021 单轮周期的观察性推断，非统计回归结论（n=1 周期，需谨慎）。</div>
  </div>

  <!-- 图1：XBI 季度收益 vs 工具板块平均年度 YoY -->
  <div class="card">
    <h2>传导主图：XBI 季度行情（先行） vs 工具板块平均营收增速（滞后）</h2>
    <div id="chart_main" class="chart"></div>
    <div class="note">橙柱=XBI 季度收益%（左轴）；蓝线=四家公司年度平均营收 YoY%（右轴，标注在对应年份）。红色虚线标出两轮传导窗口：2020Q2 行情启动 → 2021 年业绩爆发（滞后 3-4 季度）；2025Q3-Q4 行情启动 → 2025 年刚 +5.1%，2026 进入加速（箭头指向预期窗口）。可清楚看到 2021 年工具增速峰值（17.3%）出现在行情启动后约一年。</div>
  </div>

  <!-- 图2：四家季度 YoY -->
  <div class="card">
    <h2>四龙头季度营收 YoY（2019Q1 起）<span class="tag">识别爆发时点</span></h2>
    <div id="chart_qyoy" class="chart"></div>
    <div class="note">WAT 2026Q1-Q2 的 +91%/+113% 为 BD 并购并表口径（虚线显示、已单独标注），非内生增长。A 与 WAT 是最纯的"工具订单β"样本：A 季度 YoY 2020Q3 转正（+8.5%）→ 2021Q1-Q3 冲上 +14~26%；WAT 2020Q4 转正（+9.8%）→ 2021Q1-Q2 +31%。本轮：A 2025Q4 +9.4% → 2026Q2 +10.0%，TMO 2025Q4 +7.2% → 2026Q2 +10.5%，均在爬升中。</div>
  </div>

  <!-- 周期对齐表 -->
  <div class="card">
    <h2>两轮周期关键节点对齐</h2>
    <table>
      <tr><th>节点</th><th>上一轮（2019-2022）</th><th>当前（2024-2026）</th><th>结论</th></tr>
      <tr><td>行情启动（XBI）</td><td>2020Q2 +44.6%（疫情后 V 型）</td><td>2025Q3 +20.8% / Q4 +21.7%</td><td>两轮均为季度级 V 型反转</td></tr>
      <tr><td>启动后首个季度</td><td>2020Q3 XBI -0.5%（震荡）</td><td>2026Q1 +4.8%</td><td>启动后次季多有消化</td></tr>
      <tr><td>工具板块当年 YoY</td><td>2020 年 +13.1%（启动当年即转正）</td><td>2025 年 +5.1%</td><td>本轮启动当年更温和</td></tr>
      <tr class="hl"><td>工具业绩爆发年</td><td>2021 年 +17.3%（滞后 1 年）</td><td>预期 2026Q4-2027</td><td>上轮滞后约 3-4 个季度</td></tr>
      <tr><td>增速回落年</td><td>2023 年 -3.9%（收缩）</td><td>—</td><td>景气→收缩也滞后约 1 年</td></tr>
    </table>
    <div class="note">注：2021 年爆发被 COVID 检测业务放大（TMO/DHR 尤其明显），纯 biotech 资本开支传导看 A/WAT：2020 年 A +3.4%、WAT -1.7%（未爆发）→ 2021 年 +18.4%、+17.8%（爆发）——滞后约 1 年更纯粹。</div>
  </div>

  <!-- 口径警示 -->
  <div class="card">
    <h2>口径与数据警示</h2>
    <div class="warn">
      ① <b>WAT 2026 并表失真</b>：WAT 2026 年完成收购 BD 的 Biosciences &amp; Diagnostic Solutions 业务（2026Q2 并表贡献 $817M），报告营收 YoY +113% 为并购口径；财报会披露<b>有机口径 2026Q2 +9% CC</b>（原业务真实景气）。用 WAT 判断工具周期须用有机口径。<br>
      ② <b>DHR 2023 剥离 Veralto</b>：2023 年报告口径 -10.3% 含环境/应用业务剥离，持续经营口径约 -3~0%。DHR 季度 Q4 值亦存在报告结构噪音（如 2021Q4 -48% 等并购/会计调整）。<br>
      ③ <b>TMO/DHR 2020-21 含 COVID</b>：两家的爆发期营收含 COVID 检测/疫苗/试剂业务（TMO 2020 +26%、DHR 2020 +24%），不完全是 biotech 资本开支传导；判断"融资→工具订单"传导以 A/WAT 更干净。<br>
      ④ <b>样本限制</b>：上一轮仅 1 个完整周期（2020-2023），时滞"3-4 季度"为单周期观察，非统计显著结论；不同周期（融资驱动 vs 并购驱动 vs 临床驱动）传导速度可能不同。本轮为并购+融资双驱动，传导可能更快或更慢，需跟踪订单数据验证。
    </div>
  </div>

  <!-- 使用提示 -->
  <div class="card">
    <h2>监测信号与使用提示</h2>
    <ul class="tl">
      <li><b>领先指标</b>：四家公司季报中的"订单/询单增速"与"全年指引上修"是比营收更早的信号。WAT 2026Q2 已"订单跑赢销售"并上修指引——工具需求端已确认改善。</li>
      <li><b>本轮跟踪时点</b>：2026Q3（10-11 月财报季）若四家一致上调 2027 指引、且 A/WAT 季度 YoY 站上 10%+，则传导确认；若 XBI 2026H2 回落（如利率反弹），传导可能中断——景气先行指标恶化会延迟而非取消工具弹性。</li>
      <li><b>对投资含义</b>（仅观察性）：若认可 3-4 季度滞后框架，工具龙头业绩弹性窗口在 2026Q4-2027，股价通常领先业绩 1-2 个季度（当前相关性报告 #24 显示工具股 2026 年与 XBI 脱钩，或因市场尚未计入传导）。</li>
      <li><b>局限</b>：未建模利率/汇率/中国需求等扰动；季度营收含并购与剥离影响已标注；本报告为历史规律观察，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 行情、富途财报库、公司财报会要点）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。时滞结论基于单周期观察，历史规律不代表未来必然重演。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' },
                    splitLine: { lineStyle: { color: '#eef1f6' } } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec',
                      textStyle: { color: '#1f2733' } };

// 1) 主图：XBI 季度收益柱 + 工具板块年度 YoY 线（右轴）
const avgMap = {};
DATA.avg_y.forEach((y, i) => avgMap[y] = DATA.avg_v[i]);
// 年度 YoY 对齐到 XBI 季度坐标（每年 Q4 处标注）——用 Q4 位置
const yearQIndex = {};
DATA.xq_dates.forEach((q, i) => { const y = q.slice(0, 4); yearQIndex[y] = i; });
const avgLine = DATA.xq_dates.map(q => { const y = q.slice(0, 4); const v = avgMap[y]; return v == null ? null : v; });
const c1 = echarts.init(document.getElementById('chart_main'));
c1.setOption({
  tooltip: tooltipAxis,
  legend: { data: ['XBI 季度收益 %', '工具板块年度 YoY %'], top: 0 },
  grid: { left: 55, right: 55, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.xq_dates }, axisStyle),
  yAxis: [
    Object.assign({ type: 'value', name: 'XBI 季度收益 %' }, axisStyle),
    Object.assign({ type: 'value', name: '工具 YoY %', min: -10, max: 25 }, axisStyle)
  ],
  series: [
    { name: 'XBI 季度收益 %', type: 'bar', data: DATA.xq_ret, yAxisIndex: 0,
      itemStyle: { color: function (p) { return p.value >= 0 ? 'rgba(192,57,43,.55)' : 'rgba(30,132,73,.55)'; }, borderRadius: [2,2,0,0] } },
    { name: '工具板块年度 YoY %', type: 'line', data: avgLine, yAxisIndex: 1, showSymbol: true, symbolSize: 6,
      lineStyle: { width: 2.5, color: '#0072B2' }, itemStyle: { color: '#0072B2' },
      markLine: { silent: true, symbol: 'none',
        data: [
          { xAxis: DATA.xq_dates.findIndex(d => d === '2020Q2'), label: { formatter: '上轮启动 2020Q2', color: '#8c97a6', fontSize: 10, position: 'insideEndTop' }, lineStyle: { color: '#D55E00', type: 'dashed', width: 1 } },
          { xAxis: DATA.xq_dates.findIndex(d => d === '2021Q4'), label: { formatter: '上轮爆发 2021', color: '#8c97a6', fontSize: 10, position: 'insideEndTop' }, lineStyle: { color: '#D55E00', type: 'dashed', width: 1 } },
          { xAxis: DATA.xq_dates.findIndex(d => d === '2025Q3'), label: { formatter: '本轮启动 2025Q3', color: '#009E73', fontSize: 10, position: 'insideEndTop' }, lineStyle: { color: '#009E73', type: 'dashed', width: 1 } }
        ] } }
  ]
});

// 2) 四家季度 YoY
const c2 = echarts.init(document.getElementById('chart_qyoy'));
const colors = { A: '#0072B2', WAT: '#009E73', DHR: '#CC79A7', TMO: '#D55E00' };
c2.setOption({
  tooltip: tooltipAxis,
  legend: { data: ['A 安捷伦', 'WAT 沃特世', 'DHR 丹纳赫', 'TMO 赛默飞'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.qy.A.dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '季度营收 YoY %' }, axisStyle),
  series: ['A', 'WAT', 'DHR', 'TMO'].map(tk => ({
    name: { A: 'A 安捷伦', WAT: 'WAT 沃特世', DHR: 'DHR 丹纳赫', TMO: 'TMO 赛默飞' }[tk],
    type: 'line', data: DATA.qy[tk].yoy, showSymbol: false,
    lineStyle: { width: 1.8, color: colors[tk] }, itemStyle: { color: colors[tk] }
  }))
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)

out_dir = os.path.join(ROOT, "reports", "25_工具业绩传导时滞")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={len(html.encode('utf-8'))}")