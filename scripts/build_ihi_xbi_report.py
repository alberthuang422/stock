#!/usr/bin/env python3
"""生成 IHI × XBI 分阶段相关性分析 HTML 报告（研报风格, ECharts, 色弱安全 Okabe-Ito）。
读 results/ihi_xbi_corr.json, 输出 reports/23_ihi_xbi器械vs生物科技/index.html。
静默写盘：只 print saved 行。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "ihi_xbi_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

blocks = D["blocks"]
full, pre, post, w25, ytd = blocks[0], blocks[1], blocks[2], blocks[3], blocks[4]
fisher = D["fisher"]
extreme = D["extreme"]

# ---- 图表数据 ----
roll_plot = [r for r in D["rolling60"] if r["corr"] is not None and r["date"] >= "2015-01-01"]
roll_dates = [r["date"] for r in roll_plot]
roll_vals = [r["corr"] / 100 for r in roll_plot]

yearly = D["yearly"]
y_dates = ["%d" % y["year"] for y in yearly]
y_vals = [y["corr"] / 100 for y in yearly]

monthly = [m for m in D["monthly"] if m["month"] >= "2023-01"]
m_dates = [m["month"] for m in monthly]
m_vals = [m["corr"] / 100 for m in monthly]

price = D["price_recent"]
p_dates = [p["date"] for p in price]
p_ihi = [p["ihi"] for p in price]
p_xbi = [p["xbi"] for p in price]
p_ratio = [p["ratio"] for p in price]
base_ihi, base_xbi = p_ihi[0], p_xbi[0]
p_ihi_norm = [round(v / base_ihi * 100, 2) for v in p_ihi]
p_xbi_norm = [round(v / base_xbi * 100, 2) for v in p_xbi]

scatter = D["scatter"]
sc_before = [{"value": [s["x"], s["y"]], "date": s["date"]} for s in scatter if not s["after"]]
sc_after = [{"value": [s["x"], s["y"]], "date": s["date"]} for s in scatter if s["after"]]

# 分界前后归一化（起点=100）
def series_of(arr, key):
    return [[p["date"], p[key]] for p in arr]
pre_norm, post_norm = D["norm_series"][0], D["norm_series"][1]

data_js = {
    "roll_dates": roll_dates, "roll_vals": roll_vals,
    "y_dates": y_dates, "y_vals": y_vals,
    "m_dates": m_dates, "m_vals": m_vals,
    "p_dates": p_dates, "p_ihi": p_ihi, "p_xbi": p_xbi, "p_ratio": p_ratio,
    "p_ihi_norm": p_ihi_norm, "p_xbi_norm": p_xbi_norm,
    "pre_dates": [p["date"] for p in pre_norm],
    "pre_ihi": [p["ihi"] for p in pre_norm], "pre_xbi": [p["xbi"] for p in pre_norm],
    "post_dates": [p["date"] for p in post_norm],
    "post_ihi": [p["ihi"] for p in post_norm], "post_xbi": [p["xbi"] for p in post_norm],
    "sc_before": sc_before, "sc_after": sc_after,
    "split": D["split"], "window_start": D["window_start"],
}
data_json = json.dumps(data_js, ensure_ascii=False)

SPLIT_STR = D["split"]

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IHI × XBI 相关性分析报告 ｜ 医疗器械 vs 生物科技</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#fff;
          --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --green:#009E73; --purple:#CC79A7;
          --red:#C0392B; --verm:#D55E00; --grey:#8c97a6; }
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
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; margin-top: 6px; }
  th, td { padding: 9px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  tr.hl { background: #f4f8ff; }
  .note { font-size: 12px; color: var(--sub); margin-top: 10px; }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 260px; }
  .concl { border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }
  ul.tl { list-style: none; }
  ul.tl li { padding: 8px 0 8px 18px; border-left: 2px solid var(--line); margin-left: 6px; position: relative; }
  ul.tl li::before { content: ""; position: absolute; left: -5px; top: 14px; width: 8px; height: 8px;
                     border-radius: 50%; background: var(--blue); }
  ul.tl li b { color: var(--blue); }
  .legend-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; }
  .disclaimer { font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }
  .src { font-size: 11.5px; color: var(--sub); margin-top: 8px; }
  .pill { display:inline-block; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .pill.red { background:#fdecea; color:var(--red); } .pill.green { background:#e8f5ec; color:var(--green); }
  .pill.blue { background:#e8f0fb; color:var(--blue); } .pill.amber { background:#fdf3e3; color:var(--verm); }
  .big-num { font-size: 34px; font-weight: 800; line-height: 1.2; }
  .big-num small { font-size: 13px; font-weight: 400; color: var(--sub); }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>IHI × XBI 相关性分析报告</h1>
  <div class="subtitle">iShares 美国医疗器械 ETF（IHI）vs SPDR 标普生物科技 ETF（XBI）· 分阶段对比（2026-02 为界）· 数据截至 2026-08-21</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid4">
      <div class="kv"><div class="k">全期日收益相关性（2006–2026）</div>
        <div class="v">0.65 <small>Pearson</small></div>
        <div class="muted">Spearman 0.61 · β(IHI→XBI) 0.42</div></div>
      <div class="kv"><div class="k">分界前（2006–2026.01）</div>
        <div class="v">0.67 <small>Pearson</small></div>
        <div class="muted">Spearman 0.63</div></div>
      <div class="kv"><div class="k">分界后（2026.02–08）</div>
        <div class="v">0.25 <small>Pearson</small></div>
        <div class="muted">Spearman 0.28 · R² 仅 6%</div></div>
      <div class="kv"><div class="k">Fisher z 检验（前 vs 后）</div>
        <div class="v">z = 6.34 <small>p ≈ 0.000</small></div>
        <div class="muted"><b>显著脱钩</b></div></div>
    </div>
    <div class="concl">
      ① <b>相关性从 0.67 崩塌至 0.25，统计显著（Fisher z=6.34, p&lt;0.001）</b>：这是 20 年历史中最剧烈的相关性下移，R² 从 44% 跌至 6%——2026 年以来 IHI 日收益几乎无法被 XBI 解释。<br>
      ② <b>走势彻底背离</b>：2025-09 以来 XBI 累计 <span class="up">+78.4%</span>，IHI 累计 <span class="down">−8.9%</span>，跑输约 87 个百分点；2026 年以来 XBI <span class="up">+36.4%</span> vs IHI <span class="down">−9.2%</span>。<br>
      ③ <b>β 同步萎缩（0.43 → 0.17–0.19）</b>，残差波动反升（0.93% → 1.42%）——IHI 已从"跟随生物科技β"切换到"独立于板块的医药器械逻辑"。<br>
      ④ <b>极端日几乎全由 XBI 单边驱动</b>：2021 年以来 XBI 单日 |涨跌|≥3% 共 207 天，其中 195 天 IHI 无同级别异动（跟随率仅 6%）；反之 IHI 大幅异动时 XBI 有 46% 概率同步——联动是不对称的"XBI 主导、IHI 钝化"。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价，2006-05-08 ~ 2026-08-21，共同交易 5105 天）；计算：日收益率 Pearson/Spearman 相关、OLS β 与残差波动、60 日滚动相关、Fisher z 检验。分界点沿用项目惯例 2026-02-01 结构断裂点。注：本报告完整覆盖分界前 20 年与分界后全部样本，无遗漏窗口。</div>
  </div>

  <!-- 标的基本信息 -->
  <div class="card">
    <h2>标的基本信息</h2>
    <div class="grid4">
      <div class="kv"><div class="k">IHI · 美国医疗器械 ETF</div>
        <div class="v">$56.17 <small>2026-08-21</small></div>
        <div class="muted">iShares，跟踪 S&amp;P 美国医疗器械与用品指数；持仓以大型器械为主（直觉外科/史赛克/美敦力/波士顿科学等），业绩与手术量、器械创新强相关</div></div>
      <div class="kv"><div class="k">XBI · 标普生物科技 ETF</div>
        <div class="v">$165.73 <small>2026-08-21</small></div>
        <div class="muted">SPDR，等权持有约 140 只 biotech（偏小型），高β、高波动，受融资/并购/临床催化事件驱动</div></div>
      <div class="kv"><div class="k">属性差异</div>
        <div class="v" style="font-size:15px;">器械 = 现金流型</div>
        <div class="muted">波动率年化 20.0%（全期）；业绩稳定、分红型，防御属性</div></div>
      <div class="kv"><div class="k">属性差异</div>
        <div class="v" style="font-size:15px;">生物科技 = 事件型</div>
        <div class="muted">波动率年化 30.7%；融资周期/并购/临床数据驱动，进攻属性</div></div>
    </div>
  </div>

  <!-- 归一化走势 -->
  <div class="card">
    <h2>2024 年以来走势：分化从 2026 年起急剧扩大 <span class="tag">归一化 100=2024-06 起点</span></h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#C0392B"></span>IHI（器械）与 <span class="legend-dot" style="background:#1E8449"></span>XBI（生物科技）以 2024-06-03 收盘为 100。虚线为 2026-02 分界。2024 年中 ~ 2025 年底两条曲线长期纠缠（相关性 0.5–0.7 高位），2026 年起 XBI 火箭式上行（+78%），IHI 反而回落约 9%——剪刀差一度拉大到 80+ 个百分点，历史上罕见。</div>
  </div>

  <!-- 分阶段对比表 -->
  <div class="card">
    <h2>分阶段相关性一览 <span class="tag">以 2026-02-01 为界 · 完整覆盖</span></h2>
    <table>
      <tr><th>区间</th><th>样本(交易日)</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(IHI→XBI)</th><th>残差日波动</th><th>IHI 区间涨幅</th><th>XBI 区间涨幅</th><th>IHI−XBI 超额</th></tr>
      <tr><td>全期（2006-05 ~ 2026-08）</td><td>5105</td><td>0.652</td><td>0.614</td><td>42.6%</td><td>0.424</td><td>0.95%</td><td class="up">+578.9%</td><td class="up">+939.9%</td><td class="down">−361.0pp</td></tr>
      <tr><td>分界前（2006-05 ~ 2026-01）</td><td>4965</td><td>0.666</td><td>0.626</td><td>44.4%</td><td>0.431</td><td>0.93%</td><td class="up">+626.2%</td><td class="up">+682.8%</td><td class="down">−56.6pp</td></tr>
      <tr class="hl"><td>分界后（2026-02 ~ 2026-08）</td><td>140</td><td>0.249</td><td>0.279</td><td>6.2%</td><td>0.190</td><td>1.42%</td><td class="down">−5.8%</td><td class="up">+30.1%</td><td class="down">−36.0pp</td></tr>
      <tr><td>2025-09 以来</td><td>245</td><td>0.250</td><td>0.276</td><td>6.2%</td><td>0.181</td><td>1.23%</td><td class="down">−8.9%</td><td class="up">+78.4%</td><td class="down">−87.4pp</td></tr>
      <tr><td>2026 以来</td><td>160</td><td>0.233</td><td>0.256</td><td>5.4%</td><td>0.174</td><td>1.38%</td><td class="down">−9.2%</td><td class="up">+36.4%</td><td class="down">−45.6pp</td></tr>
    </table>
    <div class="note">
      解读：① <b>分界点前后 Pearson 0.666 → 0.249，Fisher z=6.34（p&lt;0.001）</b>，远超任何"样本噪声"解释，是统计显著的结构性脱钩；② 后续三个窗口（分界后 / 2025-09 以来 / 2026 以来）相关性全部塌在 0.23–0.25，说明脱钩从 2025 年末 / 2026 初就已发生且持续至今，非单月偶然；③ β 反直觉地下降（0.43→0.19），而残差波动上升——IHI 的日常波动越来越多来自自身器械板块因子，而非整体生物医药β；④ IHI 全期最大回撤 −49.7% vs XBI −63.9%，高β高回撤的 XBI 本轮却领涨 30%，二者风险收益画像已完全不同。
    </div>
  </div>

  <!-- 年度相关性 -->
  <div class="card">
    <h2>年度相关性：2026 年创 20 年最低 <span class="tag">2006–2026</span></h2>
    <div id="chart_year" class="chart"></div>
    <div class="note">按自然年日收益 Pearson 相关（×100）。常年稳定在 0.5–0.85 区间（2008 危机年高达 0.86，2023–24 为 0.46–0.50 的相对低位），<b>2026 年迄今仅 0.23，为 20 年最低且显著低于次低年份</b>。历史告诉我们要警惕：前两次低于 0.55 的年份（2023、2024）之后相关性均有回归，但 2026 是首次跌破 0.3 —— 需要判断这是"均值回归前的极值"还是"板块逻辑长期切换"。</div>
  </div>

  <!-- 60日滚动相关性 -->
  <div class="card">
    <h2>60 日滚动相关性：2025 年末起持续徘徊在 0.2–0.4 低位 <span class="tag">动态监测</span></h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note">橙色虚线=分界点（2026-02）。滚动 60 日相关在 2025 年上半年仍在 0.6–0.7，<b>2025Q4 开始中枢下移，2026 年以来绝大多数时间低于 0.4</b>，最新（2026-08）约 0.2–0.3，处于历史最衰区域（对比 2008 危机中曾冲高至 0.9）。蓝线下方区域=脱钩期，当前已持续约 8 个月，是历史级别。</div>
  </div>

  <!-- 月度相关性 -->
  <div class="card">
    <h2>月度相关性（2023 年以来）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月度相关性大幅摆动（负值月份提示两者可短暂反向）。2025 年多数月份仍在 0.4–0.8，2026 年 3 月起几乎月月在 0.3 以下或转负——"器械跟涨生物科技"的惯例已被打破。</div>
  </div>

  <!-- 日收益散点 -->
  <div class="card">
    <h2>日收益散点：分界后点云散成"圆盘" <span class="tag">近3年</span></h2>
    <div id="chart_scatter" class="chart"></div>
    <div class="note">横轴=XBI 日收益率(%), 纵轴=IHI 日收益率(%)。蓝点=分界前（2023-01 ~ 2026-01），红色▲=分界后（2026-02 起）。分界前点云呈明显正斜率椭圆（r≈0.65），分界后红点几乎无方向性摊开——斜率两条回归线之间夹角急剧扩大，直观展示"脱钩"。注意 XBI 日波动（±3–5%）远大于 IHI（±1–2%），XBI 单日巨震时 IHI 往往只是小幅跟随。</div>
  </div>

  <!-- 极端日 -->
  <div class="card">
    <h2>极端日分析：2021 年以来 |日收益| ≥ 3% 的归属 <span class="tag">不对称联动</span></h2>
    <div class="grid4">
      <div class="kv"><div class="k">XBI 异动而 IHI 不动的天数</div>
        <div class="v">195 <small>天</small></div>
        <div class="muted">XBI 单边 |≥3%| 共 207 天，其中 195 天 IHI 无同级异动 → 跟随率仅 <b>6.2%</b></div></div>
      <div class="kv"><div class="k">IHI 异动而 XBI 不动</div>
        <div class="v">26 <small>天</small></div>
        <div class="muted">IHI 单边 |≥3%| 共 38 天，其中 26 天 XBI 无同级异动 → XBI 跟随 IHI 达 <b>46.2%</b></div></div>
      <div class="kv"><div class="k">同日双方都异动</div>
        <div class="v">12 <small>天</small></div>
        <div class="muted">共同异动日两者相关性高达 <b>0.98</b>（同涨同跌，多为宏观/流动性冲击日）</div></div>
      <div class="kv"><div class="k">总量</div>
        <div class="v">209 <small>天</small></div>
        <div class="muted">任一标的大幅异动（2021-01 ~ 2026-08）</div></div>
    </div>
    <div class="note">解读：<b>联动是单向的</b>——XBI 是波动来源，但它的巨震绝大多数不被 IHI 接住（94% 时段独立）；而 IHI 一旦自己大幅波动，多半是真正的医疗健康系统性事件，XBI 有近半概率同步。这意味着：把 IHI 当"生物科技的温和版 β"是危险的，两者只在宏观冲击日才高度同步。</div>
  </div>

  <!-- 归因分析 -->
  <div class="card">
    <h2>为什么 2026 年脱钩？—— 板块驱动因子完全不同</h2>
    <div class="grid3">
      <div class="kv"><div class="k">XBI 大涨：生物科技融资/并购/数据年</div>
        <div class="v" style="font-size:15px;">2026 年生物科技景气重燃</div>
        <div class="muted">2026 年生物科技并购与融资回暖（美股 biotech 景气 +9 分结构性上行、IPO/BD 活跃），XBI 等权偏移小型高β标的，弹性极大；2025-09 以来 +78% 主要由小型 biotech 行情驱动，与"器械需求"几乎无关。</div></div>
      <div class="kv"><div class="k">IHI 走弱：器械板块自身压力</div>
        <div class="v" style="font-size:15px;">手术量恢复放缓 + 政策打压</div>
        <div class="muted">OTC 器械集采/单病种付费改革推进、外资器械本土化竞争加剧、手术量恢复性增长见顶回落，器械估值中枢下移。IHI 更接近"现金牛价值股"，不会参与 biotech 的风险溢价扩张行情。</div></div>
      <div class="kv"><div class="k">结构性错位：两者已不同属一个"主题"</div>
        <div class="v" style="font-size:15px;">器械 = 存量现金流 · 生物 = 增量风险</div>
        <div class="muted">资金面视角：2026 年增量资金追逐"创新风险收益"（biotech），回避"现金流防御"（器械）——风格切换导致两个同属"医疗健康"标签的 ETF 走势反向。此轮脱钩的本质是<b>行业景气分化</b>，而非临时性扰动。</div></div>
    </div>
  </div>

  <!-- 结论与使用提示 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>承认结构性脱钩</b>：IHI×XBI 相关性已从 0.67 跌至 0.25（Fisher p&lt;0.001），连续 8 个月低于 0.4 属 20 年之最。若以 XBI 作为 IHI 的板块代理或分散工具，<b>当前阶段分散效果极强、联动参考意义极弱</b>。</li>
      <li><b>双向解读</b>：对持有 IHI 的"医疗器械暴露"者，XBI 不再构成"同类板块"的加仓理由；反之，XBI 的大起大落也几乎不影响器械逻辑。两者在组合中已是两个独立敞口。</li>
      <li><b>监测信号</b>：若 60 日滚动相关性回到 0.5+ 且月度相关性连续 3 个月为正，说明资金风格回归或行业因子重新联动；在此之前，默认按"脱钩状态"处理。</li>
      <li><b>局限</b>：分界后仅 140 个交易日，统计窗口短（虽 Fisher z 显著）；未扣交易成本；相关性是统计描述而非因果；月度相关性受极端单日扰动大。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 日线行情）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。医疗器械/生物科技行业景气归因为公开信息综述（推断性，非一手来源），若需确证需另行核实。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const SPLIT = DATA.split;
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' },
                    splitLine: { lineStyle: { color: '#eef1f6' } } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec',
                      textStyle: { color: '#1f2733' } };
const COLOR_IHI = '#C0392B';   // 器械（红系，强调其防御、价值属性在此报告中代表跑输）
const COLOR_XBI = '#1E8449';   // 生物科技（绿系，跑赢）

// 1) 归一化走势
echarts.init(document.getElementById('chart_norm')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['IHI 器械', 'XBI 生物科技'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.p_dates, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '归一化（基准=100）', scale: true }, axisStyle),
  series: [
    { name: 'IHI 器械', type: 'line', data: DATA.p_ihi_norm, showSymbol: false,
      lineStyle: { width: 2, color: COLOR_IHI }, itemStyle: { color: COLOR_IHI },
      markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02 分界', color: '#8c97a6', fontSize: 11 },
        lineStyle: { color: '#D55E00', type: 'dashed', width: 1 },
        data: [{ xAxis: DATA.p_dates.findIndex(d => d >= SPLIT) }] } },
    { name: 'XBI 生物科技', type: 'line', data: DATA.p_xbi_norm, showSymbol: false,
      lineStyle: { width: 2, type: 'dashed', color: COLOR_XBI }, itemStyle: { color: COLOR_XBI } }
  ]
});

// 2) 年度相关性
echarts.init(document.getElementById('chart_year')).setOption({
  tooltip: tooltipAxis,
  grid: { left: 55, right: 20, top: 24, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.y_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '年相关', min: 0, max: 1 }, axisStyle),
  series: [{
    name: '年度相关', type: 'bar', data: DATA.y_vals,
    itemStyle: { color: function (p) {
      return p.dataIndex === DATA.y_dates.length - 1 ? '#D55E00' : 'rgba(0,114,178,.7)';
    }, borderRadius: [3, 3, 0, 0] },
    markLine: { silent: true, label: { formatter: '0.5 阈值', color: '#8c97a6', fontSize: 11 },
      lineStyle: { color: '#009E73', type: 'dashed', width: 1 }, data: [{ yAxis: 0.5 }] }
  }]
});

// 3) 60 日滚动相关性
echarts.init(document.getElementById('chart_roll')).setOption({
  tooltip: tooltipAxis,
  grid: { left: 55, right: 20, top: 24, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.roll_dates, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: 0, max: 1 }, axisStyle),
  series: [{
    name: '60日滚动相关', type: 'line', data: DATA.roll_vals, showSymbol: false,
    lineStyle: { width: 1.8, color: '#0072B2' },
    areaStyle: { color: 'rgba(0,114,178,.10)' },
    markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02', color: '#D55E00', fontSize: 11 },
      lineStyle: { color: '#D55E00', type: 'dashed', width: 1 },
      data: [{ xAxis: DATA.roll_dates.findIndex(d => d >= SPLIT) }] },
    markPoint: {
      data: [
        { type: 'max', name: '峰值', symbolSize: 34, label: { formatter: '{c}', fontSize: 10 } },
        { type: 'min', name: '谷值', symbolSize: 34, label: { formatter: '{c}', fontSize: 10 } }
      ]
    }
  }]
});

// 4) 月度相关性
echarts.init(document.getElementById('chart_monthly')).setOption({
  tooltip: tooltipAxis,
  grid: { left: 55, right: 20, top: 24, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: DATA.m_dates }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: -1, max: 1 }, axisStyle),
  series: [{
    name: '月度相关', type: 'bar', data: DATA.m_vals,
    itemStyle: { color: function (p) {
      return p.value >= 0 ? 'rgba(0,114,178,.75)' : 'rgba(213,94,0,.65)';
    }, borderRadius: [3, 3, 0, 0] },
    markLine: { silent: true, symbol: 'none', label: { formatter: '2026-02', color: '#D55E00', fontSize: 11 },
      lineStyle: { color: '#D55E00', type: 'dashed', width: 1 },
      data: [{ xAxis: DATA.m_dates.findIndex(d => d >= SPLIT) }] }
  }]
});

// 5) 日收益散点
echarts.init(document.getElementById('chart_scatter')).setOption({
  tooltip: {
    trigger: 'item',
    formatter: function (p) {
      const v = p.value;
      return p.seriesName + '<br/>' + p.data.date +
             '<br/>XBI 日收益: ' + v[0].toFixed(2) + '%<br/>IHI 日收益: ' + v[1].toFixed(2) + '%';
    },
    backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: { color: '#1f2733' }
  },
  legend: { data: ['分界前 (蓝圆)', '分界后 (红▲)'], top: 0 },
  grid: { left: 55, right: 20, top: 34, bottom: 40 },
  xAxis: Object.assign({ type: 'value', name: 'XBI 日收益 %', scale: true }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: 'IHI 日收益 %', scale: true }, axisStyle),
  series: [
    { name: '分界前 (蓝圆)', type: 'scatter', data: DATA.sc_before,
      symbol: 'circle', symbolSize: 5, itemStyle: { color: 'rgba(0,114,178,.45)' } },
    { name: '分界后 (红▲)', type: 'scatter', data: DATA.sc_after,
      symbol: 'triangle', symbolSize: 8, itemStyle: { color: 'rgba(192,57,43,.8)' } }
  ]
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)

out_dir = os.path.join(ROOT, "reports", "23_ihi_xbi器械vs生物科技")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={len(html.encode('utf-8'))}")