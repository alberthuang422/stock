#!/usr/bin/env python3
"""生成 IBB vs GILD 相关性分析 HTML 报告（浅底深字研报风, ECharts）。
读 results/ibb_gild_corr.json, 输出 reports/ibb_gild_corr_report.html。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "ibb_gild_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

blocks = D["blocks"]
full, pre, post = blocks[0], blocks[1], blocks[2]
fisher = D["fisher"]

# 图表数据准备
roll_all = D["rolling60"]
roll_plot = [r for r in roll_all if r["corr"] is not None and r["date"] >= "2018-01-01"]
roll_dates = [r["date"] for r in roll_plot]
roll_vals = [r["corr"] for r in roll_plot]

monthly = [m for m in D["monthly"] if m["month"] >= "2024-01"]
m_dates = [m["month"] for m in monthly]
m_vals = [m["corr"] for m in monthly]

price = D["price_recent"]
p_dates = [p["date"] for p in price]
p_ibb = [p["ibb"] for p in price]
p_gild = [p["gild"] for p in price]
p_ratio = [p["ratio"] for p in price]

# 归一化价格（全期，用于大图）——从 JSON 没有全期价格，这里用近18个月价格归一化到100
base_ibb = p_ibb[0]; base_gild = p_gild[0]
p_ibb_norm = [round(v / base_ibb * 100, 2) for v in p_ibb]
p_gild_norm = [round(v / base_gild * 100, 2) for v in p_gild]

# 散点: 分界前后日收益 (从价格序列算不出日收益, 改为用 JSON 里的滚动数据不可行)
# 散点数据单独在分析脚本里没导出, 用近18月价格近似不准确; 改为展示相关性 vs 时间的动态图即可
# 补充一个"分阶段相关矩阵"用条形图

# 散点数据（近3年日收益, 分界前后分色）
scatter = D.get("scatter", [])
sc_before = [{"value": [s["x"], s["y"]], "date": s["date"]} for s in scatter if not s["after"]]
sc_after = [{"value": [s["x"], s["y"]], "date": s["date"]} for s in scatter if s["after"]]

data_js = {
    "roll_dates": roll_dates, "roll_vals": roll_vals,
    "m_dates": m_dates, "m_vals": m_vals,
    "p_dates": p_dates, "p_ibb": p_ibb, "p_gild": p_gild, "p_ratio": p_ratio,
    "p_ibb_norm": p_ibb_norm, "p_gild_norm": p_gild_norm,
    "sc_before": sc_before, "sc_after": sc_after,
    "split": D["split"],
}
data_json = json.dumps(data_js, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IBB vs GILD 相关性分析报告</title>
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

  <h1>IBB × GILD 相关性分析报告</h1>
  <div class="subtitle">纳斯达克生物科技 ETF（IBB）vs 吉利德科学（GILD）· 分阶段对比（2026-02 为界）· 数据截至 2026-08-14</div>

  <!-- 结论卡 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">全期日收益相关性（2015–2026）</div>
        <div class="v">0.58 <small>Pearson</small></div></div>
      <div class="kv"><div class="k">分界前（2015–2026.01）</div>
        <div class="v">0.58 <small>Pearson</small></div></div>
      <div class="kv"><div class="k">分界后（2026.02–08）</div>
        <div class="v">0.52 <small>Pearson</small></div></div>
    </div>
    <div class="concl">
      ① <b>分界后相关性温和下降</b>：0.579 → 0.515，但样本仅 135 日，Fisher z 检验 p=0.30，<b>未达统计显著</b>，不宜过度解读数值差。<br>
      ② <b>真正的变化在走势背离</b>：分界后 IBB 累计 <span class="up">+13.9%</span>，GILD 累计 <span class="down">−3.2%</span>，背离约 17 个百分点——IBB 逼近 52 周新高，GILD 距 2 月高点回落约 11%。<br>
      ③ <b>GILD 个股特有波动放大</b>：回归残差日波动从 1.34% 升至 1.47%，β 反而微升（0.62→0.64），说明拖累来自 GILD 自身事件（Q2 巨额收购性账面亏损），而非板块β减弱。<br>
      ④ <b>月度层面</b>：2026-08 月度相关性骤降至 <b>0.18</b>（年内最低），两者近期几乎脱钩。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价，2015-01-02 ~ 2026-08-14，2920 个共同交易日）；计算：日收益率 Pearson/Spearman 相关、OLS β 与残差波动、60 日滚动相关、Fisher z 检验。</div>
  </div>

  <!-- 标的卡片 -->
  <div class="card">
    <h2>标的基本信息</h2>
    <div class="grid4">
      <div class="kv"><div class="k">IBB · iShares 生物科技 ETF</div>
        <div class="v">$198.26 <small>2026-08-14 收盘</small></div>
        <div class="k" style="margin-top:6px;">跟踪纳斯达克生物技术指数，GILD 为第三大成分股（权重约 7%）</div></div>
      <div class="kv"><div class="k">GILD · 吉利德科学</div>
        <div class="v">$138.36 <small>2026-08-14 收盘</small></div>
        <div class="k" style="margin-top:6px;">HIV 抗病毒龙头，正在向肿瘤/自免多元化转型</div></div>
      <div class="kv"><div class="k">分界后走势</div>
        <div class="v"><span class="up">IBB +13.9%</span></div>
        <div class="v"><span class="down">GILD −3.2%</span></div></div>
      <div class="kv"><div class="k">GILD 对 IBB 的 β</div>
        <div class="v">0.64 <small>分界后</small></div>
        <div class="k" style="margin-top:6px;">全期 0.62 · 分界前 0.62</div></div>
    </div>
  </div>

  <!-- 归一化走势 -->
  <div class="card">
    <h2>2024 年以来走势：分化从 2026-02 后显著拉大 <span class="tag">归一化 100=基准日</span></h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note">以 2024-01-02 收盘价为 100。红色=IBB 走势，绿色=GILD 走势。2026-02 起两条曲线剪刀差快速扩大：IBB 受益板块并购潮与减肥药行情持续上行逼近 120（较基准 +20%），GILD 受 Q2 巨额收购性账面亏损拖累在 95-105 区间窄幅波动。</div>
  </div>

  <!-- 分阶段相关性表 -->
  <div class="card">
    <h2>分阶段相关性一览 <span class="tag">以 2026-02-01 为界</span></h2>
    <table>
      <tr><th>区间</th><th>样本(交易日)</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(GILD→IBB)</th><th>残差日波动</th><th>IBB 区间涨幅</th><th>GILD 区间涨幅</th></tr>
      <tr><td>全期（2015-01 ~ 2026-08）</td><td>2920</td><td>0.576</td><td>0.567</td><td>33.2%</td><td>0.621</td><td>1.34%</td><td class="up">+94.5%</td><td class="up">+43.0%</td></tr>
      <tr><td>分界前（2015-01 ~ 2026-01）</td><td>2785</td><td>0.579</td><td>0.572</td><td>33.6%</td><td>0.621</td><td>1.34%</td><td class="up">+69.1%</td><td class="up">+46.7%</td></tr>
      <tr><td>分界后（2026-02 ~ 2026-08）</td><td>135</td><td>0.515</td><td>0.493</td><td>26.5%</td><td>0.638</td><td>1.47%</td><td class="up">+13.9%</td><td class="down">−3.2%</td></tr>
    </table>
    <div class="note">
      解读：① 分界后 Pearson 0.579→0.515（−0.064），Spearman 0.572→0.493（−0.079），方向一致；② Fisher z 检验 p=0.30 &gt; 0.05，<b>下降未达统计显著</b>（135 日样本功效有限）；③ 分界后 R² 从 33.6% 降至 26.5%，GILD 约 74% 的日波动不再被 IBB 解释；④ β 不降反升，说明分界后 GILD 与板块同步性未减，超额波动来自个股特有因子。
    </div>
  </div>

  <!-- 60日滚动相关性 -->
  <div class="card">
    <h2>60 日滚动相关性：2018 年以来中枢下移，近期处于低位 <span class="tag">动态监测</span></h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note">红线为分界点（2026-02）。滚动 60 日相关性从 2025 年年中约 0.75~0.80 的高位回落至 2025 年末 0.35 附近，2026-02 后维持在 0.48~0.66 区间，最新（2026-08-14）为 0.47，接近近两年低位。</div>
  </div>

  <!-- 日收益散点 -->
  <div class="card">
    <h2>日收益散点：2023 年以来，分界后点云更"散" <span class="tag">近3年</span></h2>
    <div id="chart_scatter" class="chart"></div>
    <div class="note">横轴=IBB 日收益率(%), 纵轴=GILD 日收益率(%)。蓝点=分界前(2023-01 ~ 2026-01)，红点=分界后(2026-02 起)。分界后红点云更分散、且偏向"IBB 涨/GILD 不跟"的右下区域，直观反映两者联动减弱与个股利空拖累。分界前 Pearson 0.58 → 分界后 0.52。</div>
  </div>

  <!-- 月度相关性 -->
  <div class="card">
    <h2>月度相关性（2024 年以来）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月度相关性波动极大（2025-05 曾达 0.93，2025-03 仅 0.05），单月值参考意义有限；注意 2026-08 月内相关性仅 0.18（截至 8-14），为年内最低——近期两者几乎独立波动。</div>
  </div>

  <!-- 归因 -->
  <div class="card">
    <h2>为什么 2026-02 后分化？—— 板块β行情 vs 个股利空</h2>
    <div class="grid3">
      <div class="kv"><div class="k">IBB 走强（板块驱动）</div>
        <div class="v" style="font-size:15px;">并购潮 + 专利悬崖 + 减肥药</div>
        <div class="k" style="margin-top:6px;">2026 上半年生物医药并购约 $1,060–1,340 亿；Keytruda/Eliquis 等 2028 年前后专利悬崖（约 $2,300–3,000 亿收入）倒逼大药企买管线；GLP-1 减肥药赛道爆发、FDA 审批提速。IBB 前三大权重安进/福泰/吉利德合计超 23%，板块整体上行托底指数。</div></div>
      <div class="kv"><div class="k">GILD 跑输（个股事件）</div>
        <div class="v" style="font-size:15px;">Q2 收购性账面巨亏 $105 亿</div>
        <div class="k" style="margin-top:6px;">2026-08-04 发布 Q2：营收 $78 亿（+10%，超预期），但计提 Arcellx/Tubulis/Ouro 三笔收购 IPR&D 费用约 $112 亿 + Trodelvy 减值 $17.5 亿，GAAP 净亏 $105 亿（EPS −$8.45）。剔除后示意性 EPS $2.27（+13%），主业其实稳健——是账面代价而非经营恶化。</div></div>
      <div class="kv"><div class="k">结构性错位</div>
        <div class="v" style="font-size:15px;">GILD 是"买家"而非"受益者"</div>
        <div class="k" style="margin-top:6px;">本轮 IBB 行情主角是被并购溢价的中小 biotech 与减肥药龙头；GILD 作为并购买方不享受溢价，主业 HIV 与热门主题无关，反而因巨额收购产生账面费用拖累报表，被安进/福泰/礼来等上涨对冲后，IBB 仍创新高而 GILD 掉队。</div></div>
    </div>
    <div class="src">来源：GILD 2026-08-04 10-Q/8-K 及 Q2 财报解读（RTTNews、StockTitan、东吴证券医药行业点评 2026-08-07 等，非一手来源，需核实原文）；并购/行业背景为公开信息综述。数据截至 2026-08-14。</div>
  </div>

  <!-- 结论与展望 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>相关性仍在，但"锚"在变弱</b>：IBB 与 GILD 长期日收益相关约 0.58，分界后降至 0.52（未显著）。GILD 作为 IBB 成分股（权重约 7%），天然存在联动，但 2026 年个股事件驱动占比上升。</li>
      <li><b>监测信号</b>：若两者日收益相关性持续低于 0.45、且 GILD 残差波动继续放大，说明 GILD 已进入"独立行情"模式——此时 IBB 走势对 GILD 的参考意义下降，需按个股逻辑（管线/财报/收购整合）单独评估。</li>
      <li><b>反向提示</b>：Q2 巨亏属一次性非现金项，主业增长与分红未变（季度股息 $0.82），多数机构维持买入评级（一致目标价约 $157，来源：公开市场一致预期，需核实）——若市场从"账面亏损"叙事回归"主业现金流"，两者相关性可能回升。</li>
      <li><b>局限</b>：分界后仅 135 个交易日，统计功效有限；未扣交易成本；月度相关性受单日异常值扰动大；本报告为相关性/统计描述，不构成对任一标的的买卖建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 行情、公司 10-Q/8-K、券商点评等）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const SPLIT = DATA.split;
const SPLIT_DATE = new Date(SPLIT + "T00:00:00");

const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: { color: '#1f2733' } };

// 1) 归一化走势
echarts.init(document.getElementById('chart_norm')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['IBB 归一化', 'GILD 归一化'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.p_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '归一化价格', scale: true }, axisStyle),
  series: [
    { name: 'IBB 归一化', type: 'line', data: DATA.p_ibb_norm, showSymbol: false,
      lineStyle: { width: 2, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
      markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02 分界', color: '#5b6675', fontSize: 11 },
        lineStyle: { color: '#b9770e', type: 'dashed', width: 1 },
        data: [{ xAxis: DATA.p_dates.findIndex(d => d >= SPLIT) }] } },
    { name: 'GILD 归一化', type: 'line', data: DATA.p_gild_norm, showSymbol: false,
      lineStyle: { width: 2, color: '#1e8449' }, itemStyle: { color: '#1e8449' } }
  ]
});

// 2) 60日滚动相关性
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

// 3) 月度相关性
echarts.init(document.getElementById('chart_monthly')).setOption({
  tooltip: tooltipAxis,
  grid: { left: 55, right: 20, top: 24, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.m_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: 0, max: 1 }, axisStyle),
  series: [{
    name: '月度相关', type: 'bar', data: DATA.m_vals,
    itemStyle: { color: 'rgba(46,95,158,.65)', borderRadius: [3, 3, 0, 0] },
    markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02', color: '#b9770e', fontSize: 11 },
      lineStyle: { color: '#b9770e', type: 'dashed', width: 1 },
      data: [{ xAxis: DATA.m_dates.findIndex(d => d >= SPLIT) }] }
  }]
});

// 4) 日收益散点
echarts.init(document.getElementById('chart_scatter')).setOption({
  tooltip: {
    trigger: 'item',
    formatter: function (p) {
      const v = p.value;
      return p.seriesName + '<br/>' + p.data.date +
             '<br/>IBB 日收益: ' + v[0].toFixed(2) + '%<br/>GILD 日收益: ' + v[1].toFixed(2) + '%';
    },
    backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: { color: '#1f2733' }
  },
  legend: { data: ['分界前 (2023.01–2026.01)', '分界后 (2026.02–)'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'value', name: 'IBB 日收益 %', scale: true }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: 'GILD 日收益 %', scale: true }, axisStyle),
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

out_path = os.path.join(ROOT, "reports", "ibb_gild_corr_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", out_path, f"({len(html)/1024:.0f} KB)")
