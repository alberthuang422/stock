#!/usr/bin/env python3
"""生成 AMGN × VRTX 相关性分析 HTML 报告（浅底深字研报风, ECharts）。
读 results/amgn_vrtx_corr.json, 输出 reports/amgn_vrtx_corr_report.html。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "amgn_vrtx_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

blocks = D["blocks"]
full, pre, post = blocks[0], blocks[1], blocks[2]
fisher = D["fisher"]

roll_all = D["rolling60"]
roll_plot = [r for r in roll_all if r["corr"] is not None and r["date"] >= "2018-01-01"]
roll_dates = [r["date"] for r in roll_plot]
roll_vals = [r["corr"] for r in roll_plot]

monthly = D["monthly"]
m_dates = [m["month"] for m in monthly]
m_vals = [m["corr"] for m in monthly]

price = D["prices"]
p_dates = [p["date"] for p in price]
p_a = [p["a"] for p in price]
p_v = [p["v"] for p in price]
base_a, base_v = p_a[0], p_v[0]
p_a_norm = [round(v / base_a * 100, 2) for v in p_a]
p_v_norm = [round(v / base_v * 100, 2) for v in p_v]

scatter = D["scatter"]
sc_before = [{"value": [s["x"], s["y"]], "date": s["date"]} for s in scatter if not s["after"]]
sc_after = [{"value": [s["x"], s["y"]], "date": s["date"]} for s in scatter if s["after"]]

quad = D["quad"]
seesaw = D["seesaw_after"]
rel = D["rel"]
rel_month = rel["rel_month"]

# 各月相关性（用于报告文字）
m_2026 = {x["month"]: x["corr"] for x in monthly if x["month"] >= "2026-02"}

data_js = {
    "roll_dates": roll_dates, "roll_vals": roll_vals,
    "m_dates": m_dates, "m_vals": m_vals,
    "p_dates": p_dates, "p_a_norm": p_a_norm, "p_v_norm": p_v_norm,
    "sc_before": sc_before, "sc_after": sc_after,
    "split": D["split"],
}
data_json = json.dumps(data_js, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AMGN vs VRTX 相关性分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#ffffff;
          --red:#c0392b; --green:#1e8449; --blue:#2e5f9e; --amber:#b9770e; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }
  .wrap { max-width: 1080px; margin: 0 auto; }
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
  .up { color: var(--red); } .down { color: var(--green); }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; margin-top: 6px; }
  th, td { padding: 9px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  .note { font-size: 12px; color: var(--sub); margin-top: 10px; }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 260px; }
  ul.tl { list-style: none; }
  ul.tl li { padding: 8px 0 8px 18px; border-left: 2px solid var(--line); margin-left: 6px; position: relative; }
  ul.tl li::before { content: ""; position: absolute; left: -5px; top: 14px; width: 8px; height: 8px;
                     border-radius: 50%; background: var(--blue); }
  ul.tl li b { color: var(--blue); }
  .concl { border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }
  .disclaimer { font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }
  .src { font-size: 11.5px; color: var(--sub); margin-top: 8px; }
  .pill { display:inline-block; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .pill.red { background:#fdecea; color:var(--red); } .pill.green { background:#e8f5ec; color:var(--green); }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>AMGN × VRTX 相关性分析报告</h1>
  <div class="subtitle">安进（AMGN）vs 福泰制药（VRTX）· 分阶段对比（2026-02 为界）· 数据截至 2026-08-14</div>

  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">全期日收益相关性（2015–2026）</div>
        <div class="v">0.48 <small>Pearson</small></div></div>
      <div class="kv"><div class="k">分界前（2015–2026.01）</div>
        <div class="v">0.48 <small>Pearson</small></div></div>
      <div class="kv"><div class="k">分界后（2026.02–08）</div>
        <div class="v">0.52 <small>Pearson</small></div></div>
    </div>
    <div class="concl">
      ① <b>与 IBB×GILD 相反：分界后相关性不降反升</b>（0.481 → 0.518），两者在 2026 年的同向联动反而增强；Fisher z 检验 p=0.58，差异同样不显著。<br>
      ② <b>长期 VRTX 明显强于 AMGN</b>（全期 +318% vs +163%），但 <b>分界后 AMGN 反超</b>：AMGN +20.5% vs VRTX +7.2%。驱动完全倒挂：AMGN 靠减肥药 MariTide 叙事创新高，VRTX 因 $100 亿高溢价收购 Crinetics 引发消化。<br>
      ③ <b>分界后 β 降、残差波动降</b>（0.66→0.58 / 1.90%→1.66%）——与 IBB×GILD 的"β升残差升"相反，说明 VRTX 的弱势是"跟涨不足"，而非独立事件驱动的脱钩。<br>
      ④ <b>7 月中旬以来 VRTX 明显跑输</b>：仅 30%（7/23 日）跑赢 AMGN；AMGN +15.9% vs VRTX +6.0%，差约 10pp——但这是 AMGN 的强势，不是 VRTX 的崩盘。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价，2015-01-02 ~ 2026-08-14，2920 个共同交易日）；计算：日收益率 Pearson/Spearman 相关、OLS β 与残差波动、60 日滚动相关、Fisher z 检验。</div>
  </div>

  <div class="card">
    <h2>标的基本信息</h2>
    <div class="grid4">
      <div class="kv"><div class="k">AMGN · 安进</div>
        <div class="v">$415.21 <small>2026-08-14 收盘</small></div>
        <div class="k" style="margin-top:6px;">IBB 第一大权重股；减肥药 MariTide 叙事 + Q2 净利 +65.9%</div></div>
      <div class="kv"><div class="k">VRTX · 福泰制药</div>
        <div class="v">$505.75 <small>2026-08-14 收盘</small></div>
        <div class="k" style="margin-top:6px;">IBB 第二大权重股；CF 囊性纤维化龙头，7/6 宣布 $100 亿收购 Crinetics</div></div>
      <div class="kv"><div class="k">分界后走势</div>
        <div class="v"><span class="up">AMGN +20.5%</span></div>
        <div class="v"><span class="up">VRTX +7.2%</span></div></div>
      <div class="kv"><div class="k">VRTX 对 AMGN 的 β</div>
        <div class="v">0.58 <small>分界后</small></div>
        <div class="k" style="margin-top:6px;">全期 0.65 · 分界前 0.66</div></div>
    </div>
  </div>

  <div class="card">
    <h2>2024 年以来走势：长期 VRTX 强，2026-02 后 AMGN 反超 <span class="tag">归一化 100=基准日</span></h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note">以 2024-01-02 收盘价为 100。红色=AMGN，绿色=VRTX。VRTX 长期斜率更陡（2024-2025 大幅跑赢），但 2026-02 后 AMGN 加速追赶并在 7 月中旬后明显反超——两条曲线在 2026 年 7 月后出现剪刀差反转。</div>
  </div>

  <div class="card">
    <h2>分阶段相关性一览 <span class="tag">以 2026-02-01 为界</span></h2>
    <table>
      <tr><th>区间</th><th>样本(交易日)</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(VRTX→AMGN)</th><th>残差日波动</th><th>AMGN 区间涨幅</th><th>VRTX 区间涨幅</th></tr>
      <tr><td>全期（2015-01 ~ 2026-08）</td><td>2920</td><td>0.482</td><td>0.517</td><td>23.3%</td><td>0.654</td><td>1.89%</td><td class="up">+162.8%</td><td class="up">+317.9%</td></tr>
      <tr><td>分界前（2015-01 ~ 2026-01）</td><td>2785</td><td>0.481</td><td>0.514</td><td>23.1%</td><td>0.659</td><td>1.90%</td><td class="up">+116.4%</td><td class="up">+288.3%</td></tr>
      <tr><td>分界后（2026-02 ~ 2026-08）</td><td>135</td><td>0.518</td><td>0.574</td><td>26.9%</td><td>0.578</td><td>1.66%</td><td class="up">+20.5%</td><td class="up">+7.2%</td></tr>
    </table>
    <div class="note">
      解读：① 分界后 Pearson 0.481→0.518（+0.037）、Spearman 0.514→0.574（+0.060），方向一致——2026 年两者<b>联动反而加强</b>，与 IBB×GILD（相关下降）形成镜像；② Fisher z 检验 p=0.58，变化未达统计显著；③ 分界后 β 从 0.66 降至 0.58、残差波动从 1.90% 降至 1.66%——VRTX 对 AMGN 的敏感度下降且自身波动收敛，说明分界后 VRTX 的落后更多是"β 弹性不足 + 涨幅跟不上"，而不是脱钩。
    </div>
  </div>

  <div class="card">
    <h2>60 日滚动相关性：分界后中枢明显抬升 <span class="tag">动态监测</span></h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note">红线为分界点（2026-02）。滚动 60 日相关性从 2025 年的 0.3~0.5 区间抬升至 2026 年 0.5~0.7 区间，最新（2026-08-14）约 0.55——两者近期同向联动在增强而非减弱。</div>
  </div>

  <div class="card">
    <h2>日收益散点：2023 年以来，分界后点云更"聚拢" <span class="tag">近3年</span></h2>
    <div id="chart_scatter" class="chart"></div>
    <div class="note">横轴=AMGN 日收益率(%), 纵轴=VRTX 日收益率(%)。蓝点=分界前(2023-01 ~ 2026-01)，红点=分界后(2026-02 起)。分界后红点云相对更集中在对角线附近（同向联动增强），右下区域（AMGN涨/VRTX不跟）的点比 IBB×GILD 少——VRTX 的落后主要是弹性不足而非反向。</div>
  </div>

  <div class="card">
    <h2>联动结构拆解：分界后同向 73%，跷跷板 27% <span class="tag">2026-02 以来</span></h2>
    <div class="grid4">
      <div class="kv"><div class="k">同涨</div><div class="v">49 天 <small>36%</small></div></div>
      <div class="kv"><div class="k">同跌</div><div class="v">49 天 <small>36%</small></div></div>
      <div class="kv"><div class="k">AMGN涨·VRTX跌</div><div class="v">20 天 <small>15%</small></div></div>
      <div class="kv"><div class="k">AMGN跌·VRTX涨</div><div class="v">16 天 <small>12%</small></div></div>
    </div>
    <div class="note">
      同向合计 73%（98/135），跷跷板 27%（36/135）——比 IBB×GILD 的 34% 跷跷板明显更低，是"高联动、弱分化"结构。<br>
      条件分布：AMGN 上涨日（69 天）VRTX 平均 <span class="up">+0.86%</span>、71% 日子跟涨；AMGN 下跌日（65 天）VRTX 平均 <span class="down">−0.76%</span>、仅 25% 日子上涨——标准的高 β 联动，VRTX 不是"反向"而是"跟跌跟涨但弹性偏弱"。
    </div>
  </div>

  <div class="card">
    <h2>为什么 7 月中旬后 VRTX 跑输 AMGN？—— 增长叙事 vs 并购消化</h2>
    <div class="grid3">
      <div class="kv"><div class="k">AMGN 走强（增长叙事）</div>
        <div class="v" style="font-size:15px;">MariTide 减肥药 + Q2 超预期</div>
        <div class="k" style="margin-top:6px;">7 月中旬后稳步走高（7/16 +3.7%、7/28 +4.5%、8/5 +4.6%），8/11 创历史新高 $421.79。驱动力：MariTide 月/季度给药的差异化减重叙事 + Q2 净利 $23.75 亿（同比 +65.85%）大超预期 + 营收 $100.7 亿（+10%）创纪录。</div></div>
      <div class="kv"><div class="k">VRTX 跑输（并购消化）</div>
        <div class="v" style="font-size:15px;">$100 亿收购 Crinetics</div>
        <div class="k" style="margin-top:6px;">7/6 宣布以 102% 溢价全现金收购 Crinetics（史上最大并购），市场对估值/稀释/整合担忧：7/8 −4.6%、当周 −8.1%，7 月中旬出现 2021 年来最长 7 连跌，从 52 周高点 $533 回落至 ~$477。8/7 Q2 财报（+2.5%）和 8/10 竞争对手 Sionna 的 CF 药失败（+5.6%）才推动修复。</div></div>
      <div class="kv"><div class="k">本质差异</div>
        <div class="v" style="font-size:15px;">"主动增长" vs "被动消化"</div>
        <div class="k" style="margin-top:6px;">AMGN 靠自身营收超预期 + 管线叙事持续走高；VRTX 走的是"利空消化→被动修复"路径（靠对手失败修复）。盈利动能：AMGN 净利 +65.9% vs VRTX +6.5%（增速从 Q1 的 +61% 明显放缓）。</div></div>
    </div>
    <div class="src">来源：AMGN 8-K（2026-02-03）、Q2 财报解读（Reuters/FiercePharma/TIKR 等，非一手来源需核实原文）；VRTX Crinetics 收购公告、Q2 财报（10-Q/8-K）、Sionna 临床失败报道。数据截至 2026-08-14。</div>
  </div>

  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>与 IBB×GILD 完全镜像</b>：那组是"相关降 + 成分股因个股利空脱钩"；这组是"相关升 + 大权重股跟涨但弹性不足"。VRTX 与 AMGN 的联动在 2026 年反而更紧密。</li>
      <li><b>相对强弱已切换</b>：全期 VRTX 跑赢 51% vs 分界后 46% vs 7 月中旬后 30%——VRTX 相对 AMGN 的强势地位自 2026-02 后逐步丧失，7 月中旬后尤其明显。若 AMGN 的 MariTide 三期数据（2026H2-2027）持续兑现，这个剪刀差可能延续。</li>
      <li><b>监测信号</b>：关注 MariTide 三期读数（AMGN 强势的根基）与 VRTX 的 Crinetics 交割（Q3）及 Palsonify 商业化——前者决定 AMGN 能否延续超额，后者决定 VRTX 能否止住相对弱势。</li>
      <li><b>局限</b>：分界后仅 135 日，Fisher 检验功效有限；AMGN 也有 Tavneos 退市争议、生物类似药侵蚀等隐忧；VRTX 高估值（滚动 PE ~29）是潜在回撤来源。本报告为统计描述，不构成买卖建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 行情、公司 8-K/10-Q、媒体报道等）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const SPLIT = DATA.split;
const SPLIT_DATE = new Date(SPLIT + "T00:00:00");

const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: { color: '#1f2733' } };

echarts.init(document.getElementById('chart_norm')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['AMGN 归一化', 'VRTX 归一化'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.p_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '归一化价格', scale: true }, axisStyle),
  series: [
    { name: 'AMGN 归一化', type: 'line', data: DATA.p_a_norm, showSymbol: false,
      lineStyle: { width: 2, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
      markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02 分界', color: '#5b6675', fontSize: 11 },
        lineStyle: { color: '#b9770e', type: 'dashed', width: 1 },
        data: [{ xAxis: DATA.p_dates.findIndex(d => d >= SPLIT) }] } },
    { name: 'VRTX 归一化', type: 'line', data: DATA.p_v_norm, showSymbol: false,
      lineStyle: { width: 2, color: '#1e8449' }, itemStyle: { color: '#1e8449' } }
  ]
});

echarts.init(document.getElementById('chart_roll')).setOption({
  tooltip: tooltipAxis,
  grid: { left: 55, right: 20, top: 24, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.roll_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: 0, max: 1 }, axisStyle),
  series: [{
    name: '60日滚动相关', type: 'line', data: DATA.roll_vals, showSymbol: false,
    lineStyle: { width: 1.6, color: '#2e5f9e' },
    areaStyle: { color: 'rgba(46,95,158,.10)' },
    markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02', color: '#b9770e', fontSize: 11 },
      lineStyle: { color: '#b9770e', type: 'dashed', width: 1 },
      data: [{ xAxis: DATA.roll_dates.findIndex(d => d >= SPLIT) }] },
    markPoint: {
      data: [
        { type: 'max', name: '峰值', symbolSize: 34, label: { formatter: '{c}', fontSize: 10 } },
        { type: 'min', name: '谷值', symbolSize: 34, label: { formatter: '{c}', fontSize: 10 } }
      ]
    }
  }]
});

echarts.init(document.getElementById('chart_scatter')).setOption({
  tooltip: {
    trigger: 'item',
    formatter: function (p) {
      const v = p.value;
      return p.seriesName + '<br/>' + p.data.date +
             '<br/>AMGN 日收益: ' + v[0].toFixed(2) + '%<br/>VRTX 日收益: ' + v[1].toFixed(2) + '%';
    },
    backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: { color: '#1f2733' }
  },
  legend: { data: ['分界前 (2023.01–2026.01)', '分界后 (2026.02–)'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'value', name: 'AMGN 日收益 %', scale: true }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: 'VRTX 日收益 %', scale: true }, axisStyle),
  series: [
    { name: '分界前 (2023.01–2026.01)', type: 'scatter', data: DATA.sc_before,
      symbolSize: 5, itemStyle: { color: 'rgba(46,95,158,.45)' } },
    { name: '分界后 (2026.02–)', type: 'scatter', data: DATA.sc_after,
      symbolSize: 7, itemStyle: { color: 'rgba(192,57,43,.75)' } }
  ]
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)

out_path = os.path.join(ROOT, "reports", "amgn_vrtx_corr_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", out_path, f"({len(html)/1024:.0f} KB)")
