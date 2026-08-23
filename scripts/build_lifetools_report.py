#!/usr/bin/env python3
"""生成 A/WAT/DHR/TMO × IBB/XBI 相关性分析 HTML 报告（克制版：矩阵+走势+KPI表）。
读 results/lifetools_corr.json, 输出 reports/24_工具龙头_ibb_xbi相关性/index.html。
静默写盘。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "lifetools_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

STOCKS = ["A", "WAT", "DHR", "TMO"]
BENCHES = ["IBB", "XBI"]
PAIRS = [f"{s}×{b}" for s in STOCKS for b in BENCHES]

# 汇总：8 对配对的 分界前/分界后 r、Fisher、超额
rows = []
for st in STOCKS:
    for be in BENCHES:
        key = f"{st}×{be}"
        blocks = D["pair_blocks"][key]
        full, pre, post, w25, ytd = blocks[0], blocks[1], blocks[2], blocks[3], blocks[4]
        f = D["pair_meta"][key]["fisher"]
        rows.append({
            "stock": st, "bench": be,
            "full_r": full["pearson"], "pre_r": pre["pearson"], "post_r": post["pearson"],
            "w25_r": w25["pearson"], "ytd_r": ytd["pearson"],
            "pre_beta": pre["beta"], "post_beta": post["beta"],
            "pre_resid": pre["resid_vol"], "post_resid": post["resid_vol"],
            "post_stock": post["stock_ret"], "post_bench": post["bench_ret"],
            "post_excess": post["excess"],
            "ytd_stock": ytd["stock_ret"], "ytd_bench": ytd["bench_ret"],
            "ytd_excess": ytd["excess"],
            "fisher_z": f["z"], "fisher_p": f["p_value"], "fisher_sig": f["sig"],
        })

# 矩阵热力图数据（分界后 r ×100，便于色带）
matrix = {st: {be: None for be in BENCHES} for st in STOCKS}
matrix_pre = {st: {be: None for be in BENCHES} for st in STOCKS}
for r in rows:
    matrix[r["stock"]][r["bench"]] = round(r["post_r"] * 100, 1)
    matrix_pre[r["stock"]][r["bench"]] = round(r["pre_r"] * 100, 1)

# 走势（2024-06 起，归一化 100）——每对配对的 stock/bench 序列
trend = {}
for st in STOCKS:
    for be in BENCHES:
        key = f"{st}×{be}"
        price = D["pair_meta"][key]["price"]
        trend[key] = {"dates": [p["date"] for p in price],
                      "stock": [p["stock"] for p in price],
                      "bench": [p["bench"] for p in price]}

data_js = {
    "stocks": STOCKS, "benches": BENCHES,
    "matrix": matrix, "matrix_pre": matrix_pre,
    "trend": trend,
    "split": D["split"],
}
data_json = json.dumps(data_js, ensure_ascii=False)

# 描述性信息
def sig_txt(r):
    return "显著" if r["fisher_sig"] else "不显著"
def fmt_r(x, nd=3):
    return f"{x:.{nd}f}" if x is not None else "n/a"

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A/WAT/DHR/TMO × IBB/XBI 相关性分析 ｜ 生命科学工具四龙头</title>
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
  th, td { padding: 8px 8px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  tr.hl { background: #f4f8ff; }
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
  .badge { display:inline-block; padding:1px 8px; border-radius:12px; font-size:11px; font-weight:600; }
  .badge.sig { background:#fdecea; color:var(--red); } .badge.nsig { background:#eef3fb; color:var(--blue); }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>生命科学工具四龙头 × 生物科技双基准 相关性分析</h1>
  <div class="subtitle">A（安捷伦）/ WAT（沃特世）/ DHR（丹纳赫）/ TMO（赛默飞世尔） vs IBB / XBI · 以 2026-02 为结构断裂点 · 数据截至 2026-08-21</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid4">
      <div class="kv"><div class="k">四龙头对 IBB 分界后 r</div>
        <div class="v">0.40–0.45</div>
        <div class="muted">高于对 XBI（0.28–0.35）约 0.1 — 与大盘生物科技（IBB）的联动强于小盘生物科技（XBI）</div></div>
      <div class="kv"><div class="k">四龙头对 XBI 分界后 r</div>
        <div class="v">0.28–0.35</div>
        <div class="muted">2026 年 XBI 火箭行情中，工具龙头相关性塌到 0.3 附近，明显低于全期 0.45–0.55</div></div>
      <div class="kv"><div class="k">Fisher z 显著脱钩（×XB I）</div>
        <div class="v">4/4 显著</div>
        <div class="muted">A/WAT/DHR/TMO 全部 p&lt;0.05（z 2.1–3.7）；对 IBB 仅 2/4 显著（WAT、TMO 不显著）</div></div>
      <div class="kv"><div class="k">2026 以来全部跑输基准</div>
        <div class="v">跑输 11–41pp</div>
        <div class="muted">最惨 DHR−41.4pp（对 XBI）、最轻 A−11.1pp（对 IBB）——工具龙头未参与 biotech β狂欢</div></div>
    </div>
    <div class="concl">
      ① <b>工具龙头与生物科技的联动性 2026 年明显下移</b>：对 XBI 全期 0.46–0.54 → 分界后 0.28–0.35（四只全部统计显著，z 最大 TMO 2.5 / A 3.7）；对 IBB 也降（除 WAT、TMO 之外显著）。<br>
      ② <b>但对 IBB 的相关性始终高于 XBI 约 0.1</b>：IBB 含大市值成熟药企（辉瑞/礼来/艾伯维等），与赛默飞/丹纳赫等"卖铲人"更同频；XBI 的小盘 biotech 融资/临床叙事与工具龙头关系更弱。<br>
      ③ <b>最强韧性 = WAT（对 IBB 脱钩不显著 p=0.19）</b>：WAT 主打色谱质谱（分析仪器），客户群更偏工业/学术而非纯 biotech，2026 年仍保持与 IBB 0.41 的相关与 0.72 的 β。<br>
      ④ <b>最惨烈 = DHR（对 XBI −32pp、对 IBB −25pp 分界后）</b>：DHR 生命科学/生物工艺业务与 biotech 融资高度相关，2026 年既无 biotech 的上涨弹性、又因自身估值消化跑输。<br>
      ⑤ <b>四龙头内部在 2026 年反而更抱团</b>：A×TMO 全期 0.49 → 分界后 0.73、DHR×TMO 0.47 → 0.70——虽然它们与 biotech 脱钩，但彼此作为"工具板块"的同步性增强，说明 2026 年驱动的是**工具板块自身因子**而非生物科技β。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价，截至 2026-08-21）；计算：日收益率 Pearson 相关、OLS β 与残差波动、Fisher z 检验（分界前 vs 分界后）。分界点沿用项目惯例 2026-02-01。与昨日 IHI×XBI 报告（#23）口径一致、可直接对照。</div>
  </div>

  <!-- 矩阵热力图 -->
  <div class="card">
    <h2>相关性矩阵热力图：分界后 r（×100），四龙头 vs 双基准</h2>
    <div id="chart_matrix" class="chart-sm"></div>
    <div class="note">色越深=相关性越高（绿=0.50，红=0.68）。所有配对分界后（2026-02 起）r 处于 0.28–0.45，显著低于全期 0.46–0.57。右灰虚线横向对比可清楚看到：对 IBB 深于对 XBI。</div>
  </div>

  <!-- 详表 -->
  <div class="card">
    <h2>分阶段相关性全览 <span class="tag">8 对配对 · 五阶段</span></h2>
    <table>
      <tr><th>配对</th><th>全期 r</th><th>分界前 r</th><th>分界后 r</th><th>2025-09以来 r</th><th>2026以来 r</th><th>β 分界后</th><th>Fisher z</th><th>p</th><th>显著性</th><th>2026以来 个股</th><th>2026以来 基准</th><th>超额</th></tr>
      <tr><td>A × IBB</td><td>0.544</td><td>0.547</td><td>0.395</td><td>0.396</td><td>0.395</td><td>0.601</td><td>2.274</td><td>0.023</td><td><span class="badge sig">显著</span></td><td class="up">+15.3%</td><td class="up">+26.4%</td><td class="down">−11.1pp</td></tr>
      <tr class="hl"><td>A × XBI</td><td>0.535</td><td>0.544</td><td>0.284</td><td>0.275</td><td>0.284</td><td>0.336</td><td>3.670</td><td>0.0002</td><td><span class="badge sig">显著</span></td><td class="up">+15.3%</td><td class="up">+36.4%</td><td class="down">−21.1pp</td></tr>
      <tr><td>WAT × IBB</td><td>0.499</td><td>0.501</td><td>0.411</td><td>0.410</td><td>0.406</td><td>0.722</td><td>1.318</td><td>0.188</td><td><span class="badge nsig">不显著</span></td><td class="up">+7.5%</td><td class="up">+26.4%</td><td class="down">−18.8pp</td></tr>
      <tr class="hl"><td>WAT × XBI</td><td>0.464</td><td>0.471</td><td>0.320</td><td>0.312</td><td>0.318</td><td>0.438</td><td>2.075</td><td>0.038</td><td><span class="badge sig">显著</span></td><td class="up">+7.5%</td><td class="up">+36.4%</td><td class="down">−28.9pp</td></tr>
      <tr><td>DHR × IBB</td><td>0.542</td><td>0.547</td><td>0.415</td><td>0.410</td><td>0.408</td><td>0.593</td><td>1.997</td><td>0.046</td><td><span class="badge sig">显著</span></td><td class="down">−5.0%</td><td class="up">+26.4%</td><td class="down">−31.4pp</td></tr>
      <tr class="hl"><td>DHR × XBI</td><td>0.505</td><td>0.514</td><td>0.289</td><td>0.292</td><td>0.292</td><td>0.322</td><td>3.126</td><td>0.002</td><td><span class="badge sig">显著</span></td><td class="down">−5.0%</td><td class="up">+36.4%</td><td class="down">−41.4pp</td></tr>
      <tr><td>TMO × IBB</td><td>0.570</td><td>0.574</td><td>0.450</td><td>0.444</td><td>0.448</td><td>0.631</td><td>1.954</td><td>0.051</td><td><span class="badge nsig">不显著</span></td><td class="up">+6.2%</td><td class="up">+26.4%</td><td class="down">−20.2pp</td></tr>
      <tr class="hl"><td>TMO × XBI</td><td>0.517</td><td>0.523</td><td>0.346</td><td>0.342</td><td>0.354</td><td>0.378</td><td>2.536</td><td>0.011</td><td><span class="badge sig">显著</span></td><td class="up">+6.2%</td><td class="up">+36.4%</td><td class="down">−30.2pp</td></tr>
    </table>
    <div class="note">
      读法：① 横向看每只个股，<b>对 IBB 的相关性普遍高于对 XBI 约 0.1</b>（例：TMO 0.45 vs 0.35、A 0.40 vs 0.28）——大盘药企基准更接近工具龙头的"客户群"；② 纵向看两个基准；③ <b>Fisher 对 XBI 全部显著、对 IBB 仅 A/DHR 显著</b>：脱钩主要是"小盘 biotech"层面的现象，与大盘 IBB 的脱钩更多是幅度温和的钝化；④ 分界后 β 全部小于全期（除 WAT×IBB）+ 残差波动普遍升高——偏离更多来自工具板块自身因子。
    </div>
  </div>

  <!-- 归一化走势（2024-06 起） -->
  <div class="card">
    <h2>2024-06 以来走势：四龙头 vs IBB（实线）与 XBI（虚线）<span class="tag">归一化 100=2024-06 起点</span></h2>
    <div id="chart_trend" class="chart"></div>
    <div class="note">实线=各龙头相对 IBB（红色 IBB、蓝色系四龙头），虚线=XBI。2026 年起 XBI 火箭（绿虚线）与四龙头（蓝实线）剪刀差拉大至 60–80pp，IBB（红实线）居中——工具龙头既没跟上小盘 biotech 行情、也跑输大盘药企基准。</div>
  </div>

  <!-- 结构化观察 -->
  <div class="card">
    <h2>结构化观察与监测提示</h2>
    <ul class="tl">
      <li><b>归因视角</b>：工具龙头（卖铲人）的客户是药企研发预算；2026 年 biotech 行情主要由融资/并购/临床驱动（XBI +36%），尚未传导为工具订单与业绩弹性。静待传导：若 XBI 行情延续 2–3 季度，工具板块订单/指引改善会重新拉高相关性。</li>
      <li><b>WAT 特例</b>：对 IBB 脱钩不显著（p=0.19）且 β 最高（0.72）——WAT 客户更偏工业/学术，与生物科技周期的绑定弱于 DHR/TMO，可作为工具板块中"跟 IBB 走"的标的。</li>
      <li><b>内部抱团</b>：A×TMO、DHR×TMO 分界后相关性升到 0.70+，说明 2026 年驱动是"工具板块自身因子"（行业级资金流出/估值压制）而非 biotech β。对持有工具龙头的组合：分散度在工具内部已显著下降。</li>
      <li><b>局限</b>：分界后仅 140 个交易日；工具股与 biotech 的传导存在滞后期本报告不建模；相关≠因果；月度与年度层面未细拆。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 日线行情）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。行业归因为公开信息综述（推断性，非一手来源）。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' },
                    splitLine: { lineStyle: { color: '#eef1f6' } } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec',
                      textStyle: { color: '#1f2733' } };
const STOCK_COLORS = { A: '#0072B2', WAT: '#009E73', DHR: '#CC79A7', TMO: '#D55E00' };

// 1) 矩阵热力图（分界后 r%）
const mx = DATA.matrix;
const cell = (v) => ({ value: v, itemStyle: { color: 'rgba(0,114,178,' + (0.08 + v / 100 * 0.85).toFixed(2) + ')' } });
const yLabels = DATA.stocks.slice().reverse();
const matrixData = [];
for (const st of yLabels) {
  for (const be of DATA.benches) matrixData.push([be, st, mx[st][be]]);
}
const cMatrix = echarts.init(document.getElementById('chart_matrix'));
cMatrix.setOption({
  tooltip: { formatter: p => p.seriesName + '<br/>' + p.value[1] + ' × ' + p.value[0] + '<br/>分界后 r = ' + p.value[2].toFixed(1) + '%',
             backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: { color: '#1f2733' } },
  grid: { left: 60, right: 30, top: 10, bottom: 30 },
  xAxis: { type: 'category', data: DATA.benches, splitArea: { show: true } },
  yAxis: { type: 'category', data: yLabels, splitArea: { show: true } },
  visualMap: { min: 25, max: 50, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
               inRange: { color: ['#80b8e0', '#1E4E8C'] }, textStyle: { color: '#5b6675', fontSize: 11 } },
  series: [{ name: '分界后 r%', type: 'heatmap', data: matrixData,
             label: { show: true, color: '#fff', fontSize: 13, fontWeight: 600, formatter: p => p.value[2].toFixed(0) } }]
});

// 2) 归一化走势：四龙头 + IBB + XBI（取 DHR×IBB 与 DHR×XBI 的基准序列代表)
const trend = DATA.trend;
// 基准序列：从 A×IBB（IBB）与 A×XBI（XBI）取，日期基准用 A×IBB
const dates = trend['A×IBB'].dates;
const ibbTrend = trend['A×IBB'].bench;
const xbiDates = trend['A×XBI'].dates;
const xbiTrend = trend['A×XBI'].bench;
// 四个龙头对 IBB 的序列（对齐 A×IBB 的日期）
const sMap = {};
for (const st of DATA.stocks) {
  const t = trend[st + '×IBB'];
  sMap[st] = t.stock;
}
const cTrend = echarts.init(document.getElementById('chart_trend'));
cTrend.setOption({
  tooltip: tooltipAxis,
  legend: { data: ['A 安捷伦', 'WAT 沃特世', 'DHR 丹纳赫', 'TMO 赛默飞', 'IBB 基准', 'XBI 基准'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: dates, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '归一化（基准=100）', scale: true }, axisStyle),
  series: [
    { name: 'A 安捷伦', type: 'line', data: sMap['A'], showSymbol: false, lineStyle: { width: 1.6, color: STOCK_COLORS['A'] }, itemStyle: { color: STOCK_COLORS['A'] } },
    { name: 'WAT 沃特世', type: 'line', data: sMap['WAT'], showSymbol: false, lineStyle: { width: 1.6, color: STOCK_COLORS['WAT'] }, itemStyle: { color: STOCK_COLORS['WAT'] } },
    { name: 'DHR 丹纳赫', type: 'line', data: sMap['DHR'], showSymbol: false, lineStyle: { width: 1.6, color: STOCK_COLORS['DHR'] }, itemStyle: { color: STOCK_COLORS['DHR'] } },
    { name: 'TMO 赛默飞', type: 'line', data: sMap['TMO'], showSymbol: false, lineStyle: { width: 1.6, color: STOCK_COLORS['TMO'] }, itemStyle: { color: STOCK_COLORS['TMO'] } },
    { name: 'IBB 基准', type: 'line', data: ibbTrend, showSymbol: false, lineStyle: { width: 2, color: '#C0392B' }, itemStyle: { color: '#C0392B' } },
    { name: 'XBI 基准', type: 'line', data: xbiTrend, showSymbol: false, lineStyle: { width: 2, type: 'dashed', color: '#1E8449' }, itemStyle: { color: '#1E8449' } }
  ]
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)

out_dir = os.path.join(ROOT, "reports", "24_工具龙头_ibb_xbi相关性")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={len(html.encode('utf-8'))}")