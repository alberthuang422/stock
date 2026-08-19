#!/usr/bin/env python3
"""生成 IBB × AMGN × VRTX 三方对比报告（浅底深字研报风, ECharts）。
读 results/ibb_amgn_vrtx.json, 输出 reports/ibb_amgn_vrtx_report.html。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "ibb_amgn_vrtx.json"), encoding="utf-8") as f:
    D = json.load(f)

pa_amgn = D["pa_ibb_amgn"]
pa_vrtx = D["pa_ibb_vrtx"]

# 归一化三方价格
p3 = D["prices3"]
p_dates = [p["date"] for p in p3]
p_ibb = [p["ibb"] for p in p3]
p_amgn = [p["amgn"] for p in p3]
p_vrtx = [p["vrtx"] for p in p3]

# 滚动相关
roll = D["roll"]
r_dates = [r["date"] for r in roll]
r_amgn = [r["ibb_amgn"] for r in roll]
r_vrtx = [r["ibb_vrtx"] for r in roll]

SPLIT = D["split"]

data_js = {
    "p_dates": p_dates, "p_ibb": p_ibb, "p_amgn": p_amgn, "p_vrtx": p_vrtx,
    "r_dates": r_dates, "r_amgn": r_amgn, "r_vrtx": r_vrtx,
    "split": SPLIT,
}
data_json = json.dumps(data_js, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IBB × AMGN × VRTX 三方对比报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#ffffff;
          --red:#c0392b; --green:#1e8449; --blue:#2e5f9e; --amber:#b9770e; --purple:#534ab7; }
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
  .hl { background: #fdf6e9; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>IBB × AMGN × VRTX 三方对比报告</h1>
  <div class="subtitle">生物科技板块 ETF vs 前两大权重股（安进 AMGN / 福泰 VRTX）· 分阶段对比（2026-02 为界）· 数据截至 2026-08-14</div>

  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">IBB × AMGN 分界后相关</div>
        <div class="v">0.552 <small>Pearson（↓ 0.65）</small></div></div>
      <div class="kv"><div class="k">IBB × VRTX 分界后相关</div>
        <div class="v">0.664 <small>Pearson（↑ 0.65）</small></div></div>
      <div class="kv"><div class="k">7/15 以来超额（vs IBB）</div>
        <div class="v"><span class="up">AMGN +11.5pp</span> / <span class="up">VRTX +1.6pp</span></div></div>
    </div>
    <div class="concl">
      ① <b>两大权重股 2026 年走出相反的"脱钩"方向</b>：AMGN 与 IBB 相关性分界后<b>下降</b>（0.654→0.552，Fisher p=0.07 接近显著），且 β 升、残差升——AMGN 走的是<b>独立强势（利好脱钩）</b>；VRTX 与 IBB 相关性<b>不降反升</b>（0.649→0.664），β 维持 0.93 高位、残差降——VRTX 是<b>紧密跟随板块但弹性不足</b>。<br>
      ② <b>分界后相对板块收益</b>：AMGN +20.5% vs IBB +13.9%（<b>跑赢 6.6pp</b>）；VRTX +7.2% vs IBB +13.9%（<b>跑输 6.7pp</b>）——一赢一输，几乎对称。<br>
      ③ <b>7/15 以来分化加剧</b>：AMGN 跑赢 IBB 52%（12/23 日），累计超额 <b>+11.5pp</b>（+15.9% vs +4.4%）；VRTX 跑赢 43%（10/23 日），累计超额仅 <b>+1.6pp</b>——最近一个月 AMGN 的强势是绝对的。<br>
      ④ <b>跷跷板占比都低</b>（AMGN 21.5% / VRTX 23.7%，远低于 GILD 的 34%）——两只大权重股与板块整体仍高度联动，分化体现在"幅度"而非"方向"。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价，2015-01-02 ~ 2026-08-14，2920 个共同交易日）；计算：日收益率 Pearson 相关、OLS β 与残差波动、60 日滚动相关、Fisher z 检验。</div>
  </div>

  <div class="card">
    <h2>2024 年以来归一化走势：VRTX 先强后弱，AMGN 后程反超 <span class="tag">归一化 100=基准日</span></h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note">红色=IBB，绿色=AMGN，紫色=VRTX（以 2024-01-02 收盘价为 100）。2024-2025 年 VRTX 大幅跑赢；2026 年 AMGN 后来居上：分界后 AMGN 跑赢 IBB 6.6pp 并持续创新高，VRTX 落后 IBB 6.7pp——三条线 2026 年 7 月后剪刀差明显。</div>
  </div>

  <div class="card">
    <h2>分阶段相关性对比：AMGN 脱钩，VRTX 更紧密 <span class="tag">以 2026-02-01 为界</span></h2>
    <table>
      <tr><th>对</th><th>区间</th><th>样本</th><th>Pearson r</th><th>β(对 IBB)</th><th>残差日波动</th><th>IBB 涨幅</th><th>成分股涨幅</th><th>相对 IBB</th></tr>
      <tr><td rowspan="3"><b>IBB × AMGN</b></td><td>全期</td><td>2920</td><td>0.649</td><td>0.677</td><td>1.21%</td><td class="up">+94.5%</td><td class="up">+162.8%</td><td class="up">+68.3pp</td></tr>
      <tr><td>分界前</td><td>2785</td><td>0.654</td><td>0.676</td><td>1.20%</td><td class="up">+69.1%</td><td class="up">+116.4%</td><td class="up">+47.3pp</td></tr>
      <tr><td><b>分界后</b></td><td>135</td><td class="hl">0.552 ↓</td><td class="hl">0.700 ↑</td><td class="hl">1.46% ↑</td><td class="up">+13.9%</td><td class="up">+20.5%</td><td class="up">+6.6pp</td></tr>
      <tr><td rowspan="3"><b>IBB × VRTX</b></td><td>全期</td><td>2920</td><td>0.650</td><td>0.920</td><td>1.64%</td><td class="up">+94.5%</td><td class="up">+317.9%</td><td class="up">+223.4pp</td></tr>
      <tr><td>分界前</td><td>2785</td><td>0.649</td><td>0.920</td><td>1.65%</td><td class="up">+69.1%</td><td class="up">+288.3%</td><td class="up">+219.2pp</td></tr>
      <tr><td><b>分界后</b></td><td>135</td><td class="hl">0.664 ↑</td><td class="hl">0.931 →</td><td class="hl">1.45% ↓</td><td class="up">+13.9%</td><td class="up">+7.2%</td><td class="down">−6.7pp</td></tr>
    </table>
    <div class="note">
      解读：① <b>AMGN 分界后相关性下降</b>（Fisher z=1.80, p=0.072，接近 10% 显著性水平），β 升到 0.70、残差波动升到 1.46%——AMGN 的上涨越来越由自身叙事（MariTide）驱动，而非板块 β；<br>
      ② <b>VRTX 分界后相关性反而升</b>（0.649→0.664），β 维持 0.93 高弹性、残差波动反而收窄到 1.45%——VRTX 紧跟板块、无独立行情，落后纯粹是"跟涨不足"（β 高但 α 为负）；<br>
      ③ 长期看 VRTX 与板块相关性和 AMGN 相近（0.65 vs 0.65），但 β 明显更高（0.92 vs 0.68）——VRTX 是板块的高贝塔成分。
    </div>
  </div>

  <div class="card">
    <h2>60 日滚动相关性：2026 年 AMGN 与板块走弱、VRTX 走强 <span class="tag">动态监测</span></h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note">绿线=IBB×AMGN 滚动相关，紫线=IBB×VRTX 滚动相关，红线为 2026-02 分界。2026 年以来 IBB×AMGN 相关性中枢下移（0.7→0.5 附近），IBB×VRTX 相关性中枢上移（0.5→0.7 附近）——两条线在 2026 年明显"剪刀差"，印证 AMGN 走独立行情、VRTX 更贴板块。</div>
  </div>

  <div class="card">
    <h2>相对强弱一览：跑赢 IBB 的天数占比 <span class="tag">口径：成分股日收益 &gt; IBB</span></h2>
    <div class="grid4">
      <div class="kv"><div class="k">AMGN 全期跑赢</div><div class="v">49.8% <small>(1454/2920)</small></div></div>
      <div class="kv"><div class="k">AMGN 分界后跑赢</div><div class="v">48.9% <small>(66/135)</small></div></div>
      <div class="kv"><div class="k">AMGN 7/15 以来</div><div class="v"><span class="up">52.2%</span> <small>(12/23)</small></div></div>
      <div class="kv"><div class="k">7/15 累计超额</div><div class="v"><span class="up">+11.5pp</span></div></div>
    </div>
    <div class="grid4" style="margin-top:12px;">
      <div class="kv"><div class="k">VRTX 全期跑赢</div><div class="v">50.1% <small>(1462/2920)</small></div></div>
      <div class="kv"><div class="k">VRTX 分界后跑赢</div><div class="v"><span class="down">43.0%</span> <small>(58/135)</small></div></div>
      <div class="kv"><div class="k">VRTX 7/15 以来</div><div class="v"><span class="down">43.5%</span> <small>(10/23)</small></div></div>
      <div class="kv"><div class="k">7/15 累计超额</div><div class="v"><span class="up">+1.6pp</span></div></div>
    </div>
    <div class="note">解读：AMGN 全期与分界后跑赢占比均约 50%（与板块五五开），但 7/15 以来升至 52% 且累计超额 +11.5pp——强势集中在最近一个月（MariTide 叙事 + Q2 超预期）；VRTX 全期 50.1% 跑赢（长期强），分界后掉到 43%（转弱），7/15 以来 43.5% 但累计超额仅 +1.6pp（靠跟涨、α 有限）。</div>
  </div>

  <div class="card">
    <h2>分界后联动结构：两只大权重股都高度贴板块 <span class="tag">2026-02 以来四象限</span></h2>
    <div class="grid4">
      <div class="kv"><div class="k">IBB×AMGN 同向</div><div class="v">105/135 <small>78%</small></div></div>
      <div class="kv"><div class="k">IBB×AMGN 跷跷板</div><div class="v">29/135 <small>21.5%</small></div></div>
      <div class="kv"><div class="k">IBB×VRTX 同向</div><div class="v">103/135 <small>76%</small></div></div>
      <div class="kv"><div class="k">IBB×VRTX 跷跷板</div><div class="v">32/135 <small>23.7%</small></div></div>
    </div>
    <div class="note">两只权重股与 IBB 的同向率都在 76-78%，跷跷板 21-24%——对比 GILD 与 IBB 的跷跷板 34%，<b>AMGN/VRTX 与板块的联动明显更紧密</b>。分化主要体现在"同向时的幅度差"：AMGN 同涨日涨更多（+20.5% vs +13.9%），VRTX 同涨日跟得少（+7.2% vs +13.9%）。</div>
  </div>

  <div class="card">
    <h2>归因：AMGN 的"独立强势" vs VRTX 的"贴板块弱弹性"</h2>
    <div class="grid3">
      <div class="kv"><div class="k">AMGN：利好脱钩</div>
        <div class="v" style="font-size:15px;">MariTide 叙事 + Q2 净利 +65.9%</div>
        <div class="k" style="margin-top:6px;">相关性降 + β 升 + 残差升 = 独立行情。驱动力是自身增长故事（月/季度给药减重药、营收创纪录），8/11 创历史新高 $421.79。7/15 以来对 IBB 超额 +11.5pp。</div></div>
      <div class="kv"><div class="k">VRTX：贴板块弱弹性</div>
        <div class="v" style="font-size:15px;">β 0.93 但 α 为负</div>
        <div class="k" style="margin-top:6px;">相关性升 + β 高位 + 残差降 = 完全跟随板块、无独立行情。7/6 $100 亿收购 Crinetics（102% 溢价）引发消化（7 连跌），8/7 财报 + 8/10 对手失败才修复。分界后对 IBB 跑输 6.7pp。</div></div>
      <div class="kv"><div class="k">对比 GILD</div>
        <div class="v" style="font-size:15px;">三只权重股三种形态</div>
        <div class="k" style="margin-top:6px;">GILD：利空脱钩（相关性降、β 升、残差升、跷跷板 34%）；AMGN：利好脱钩（相关性降、β 升、残差升、跷跷板 21%）；VRTX：贴板块（相关性升、β 高位、残差降、跷跷板 24%）。IBB 内部结构分化明显。</div></div>
    </div>
    <div class="src">来源：AMGN 8-K（2026-02-03）及 Q2 财报解读；VRTX Crinetics 收购公告及 Q2 财报（10-Q/8-K）；Sionna 临床失败报道（非一手来源需核实原文）。数据截至 2026-08-14。</div>
  </div>

  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>IBB 的前两大权重股 2026 年镜像分化</b>：AMGN 在跑赢（+6.6pp，7/15 后加速 +11.5pp），VRTX 在跑输（−6.7pp）——而 GILD 更是跑输 −17pp。想表达"生物科技板块"的 IBB，其内部三大权重（合计权重超 23%）表现从 +20.5% 到 −3.2% 不等。</li>
      <li><b>AMGN 的强势质量更高</b>：利好脱钩（相关性降但涨得多）意味着板块回调时 AMGN 也未必抗跌——β 反而升到 0.70，一旦 MariTide 三期数据（2026H2）不及预期，向下弹性同样大。</li>
      <li><b>VRTX 是"板块放大器"而非"选股标的"</b>：β 0.93 + 残差波动收敛 = 纯粹跟板块，α 有限。7/15 后虽小幅跑赢（+1.6pp），但主要靠 8/10 对手失败的脉冲，持续性待观察。</li>
      <li><b>监测信号</b>：若 IBB×AMGN 滚动相关跌破 0.45，说明 AMGN 已完全"个股化"；若 IBB×VRTX 滚动相关维持 0.7 上方，则 VRTX 继续是板块 β 工具。关注 MariTide 三期、Crinetics 交割、VRTX 估值消化。</li>
      <li><b>局限</b>：分界后仅 135 日，Fisher 检验功效有限；AMGN 相关下降 p=0.07 仅接近显著，需更多样本确认；本报告为统计描述，不构成买卖建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 行情、公司 8-K/10-Q、媒体报道等）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const SPLIT = DATA.split;
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: { color: '#1f2733' } };

echarts.init(document.getElementById('chart_norm')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['IBB', 'AMGN', 'VRTX'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.p_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '归一化价格', scale: true }, axisStyle),
  series: [
    { name: 'IBB', type: 'line', data: DATA.p_ibb, showSymbol: false,
      lineStyle: { width: 2, color: '#c0392b' }, itemStyle: { color: '#c0392b' },
      markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02', color: '#b9770e', fontSize: 11 },
        lineStyle: { color: '#b9770e', type: 'dashed', width: 1 },
        data: [{ xAxis: DATA.p_dates.findIndex(d => d >= SPLIT) }] } },
    { name: 'AMGN', type: 'line', data: DATA.p_amgn, showSymbol: false,
      lineStyle: { width: 2, color: '#1e8449' }, itemStyle: { color: '#1e8449' } },
    { name: 'VRTX', type: 'line', data: DATA.p_vrtx, showSymbol: false,
      lineStyle: { width: 2, color: '#534ab7' }, itemStyle: { color: '#534ab7' } }
  ]
});

echarts.init(document.getElementById('chart_roll')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['IBB×AMGN', 'IBB×VRTX'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.r_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: 0, max: 1 }, axisStyle),
  series: [
    { name: 'IBB×AMGN', type: 'line', data: DATA.r_amgn, showSymbol: false,
      lineStyle: { width: 1.6, color: '#1e8449' },
      markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02', color: '#b9770e', fontSize: 11 },
        lineStyle: { color: '#b9770e', type: 'dashed', width: 1 },
        data: [{ xAxis: DATA.r_dates.findIndex(d => d >= SPLIT) }] } },
    { name: 'IBB×VRTX', type: 'line', data: DATA.r_vrtx, showSymbol: false,
      lineStyle: { width: 1.6, color: '#534ab7' } }
  ]
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)

out_path = os.path.join(ROOT, "reports", "ibb_amgn_vrtx_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", out_path, f"({len(html)/1024:.0f} KB)")
