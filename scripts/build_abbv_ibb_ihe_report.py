# -*- coding: utf-8 -*-
"""构建研报：ABBV × IBB(生物科技) × IHE(传统制药) 相关性对比
读取 results/abbv_ibb_ihe_corr.json
输出 reports/43_ABBV_IBB_IHE_相关性/index.html（浅底深字研报风 + ECharts + Okabe-Ito 色弱安全）
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "43_ABBV_IBB_IHE_相关性")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "abbv_ibb_ihe_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

def cls(v):
    if v is None: return "na"
    return "up" if v > 0 else "dn"

def p_fmt(p):
    if p is None: return "—"
    if p < 0.001: return "<0.001"
    return f"{p:.3f}"

def block_rows(rows, kind="block"):
    out = []
    for b in rows:
        if kind == "block":
            out.append(
                f"<tr><td><b>{b['block']}</b><div class='tsub'>{b['start']} ~ {b['end']} · n={b['n']}</div></td>"
                f"<td class='{cls(b['abbv_x_pearson'])}'>{b['abbv_x_pearson']:.3f}</td>"
                f"<td class='{cls(b['abbv_y_pearson'])}'>{b['abbv_y_pearson']:.3f}</td>"
                f"<td class='{cls(b['corr_diff'])}'>{b['corr_diff']:+.3f}</td>"
                f"<td>{p_fmt(b['steiger_p'])}</td>"
                f"<td>{b['abbv_x_beta']:.2f}</td>"
                f"<td>{b['abbv_y_beta']:.2f}</td>"
                f"<td class='{cls(b['ret_abbv'])}'>{b['ret_abbv']:+.1f}%</td>"
                f"<td class='{cls(b['ret_x'])}'>{b['ret_x']:+.1f}%</td>"
                f"<td class='{cls(b['ret_y'])}'>{b['ret_y']:+.1f}%</td></tr>")
        else:
            out.append(
                f"<tr><td><b>{b['block']}</b></td>"
                f"<td class='{cls(b['abbv_x_pearson'])}'>{b['abbv_x_pearson']:.3f}</td>"
                f"<td class='{cls(b['abbv_y_pearson'])}'>{b['abbv_y_pearson']:.3f}</td>"
                f"<td class='{cls(b['corr_diff'])}'>{b['corr_diff']:+.3f}</td>"
                f"<td>{p_fmt(b['steiger_p'])}</td>"
                f"<td class='{cls(b['ret_abbv'])}'>{b['ret_abbv']:+.1f}%</td>"
                f"<td class='{cls(b['ret_x'])}'>{b['ret_x']:+.1f}%</td>"
                f"<td class='{cls(b['ret_y'])}'>{b['ret_y']:+.1f}%</td></tr>")
    return "\n".join(out)

def sup_rows():
    out = []
    for s in D["supplement"]:
        out.append(
            f"<tr><td><b>{s['pair']}</b></td>"
            f"<td>{s['start']} ~ {s['end']}<br><span class='tsub'>n={s['n']}</span></td>"
            f"<td class='{cls(s['pearson'])}'>{s['pearson']:.3f}</td>"
            f"<td>{s['spearman']:.3f}</td>"
            f"<td>{s['beta']:.2f}</td>"
            f"<td>{s['r2']*100:.1f}%</td>"
            f"<td class='{cls(s['ret_abbv'])}'>{s['ret_abbv']:+.1f}%</td>"
            f"<td class='{cls(s['ret_x'])}'>{s['ret_x']:+.1f}%</td></tr>")
    return "\n".join(out)

# ---------------- 图表数据注入 ----------------
by_block = {b["block"]: b for b in D["blocks"]}
full = next(b for b in D["blocks"] if b and b["block"].startswith("全期"))
pre = by_block["分界前 (2026-02-01)"]
post = by_block["分界后 (2026-02-01)"]
last3 = by_block["近 3 年"]
last1 = by_block["近 1 年"]
ytd = by_block["2026 年以来"]
FISHER = D["fisher"]
SPLIT = D["split"]

years = [b["block"] for b in D["yearly"]]
y_ibb = [b["abbv_x_pearson"] for b in D["yearly"]]
y_ihe = [b["abbv_y_pearson"] for b in D["yearly"]]

mon = D["monthly"][-36:]
r60 = D["rolling60"]

sup_pairs = [s["pair"] for s in D["supplement"]]
sup_pearson = [s["pearson"] for s in D["supplement"]]
sup_beta = [s["beta"] for s in D["supplement"]]
sup_corr_label = ["IBB", "XBI", "XPH"]

lw_years = sorted({s["year"] for s in D["supplement_yearly"]})
lw = {tk: [] for tk in ["IBB", "XBI", "XPH"]}
for tk in ["IBB", "XBI", "XPH"]:
    m = {s["year"]: s["pearson"] for s in D["supplement_yearly"] if s["pair"] == f"ABBV-{tk}"}
    lw[tk] = [m.get(y) for y in lw_years]

JS = {
    "r60": {"date": [x["date"] for x in r60],
            "abbv_ibb": [x["abbv_ibb"] / 100 for x in r60],
            "abbv_ihe": [x["abbv_ihe"] / 100 for x in r60]},
    "years": years,
    "y_ibb": y_ibb, "y_ihe": y_ihe,
    "monthly": {"month": [x["month"] for x in mon],
                "abbv_ibb": [x["abbv_ibb"] / 100 for x in mon],
                "abbv_ihe": [x["abbv_ihe"] / 100 for x in mon]},
    "sup_pairs": sup_pairs, "sup_pearson": sup_pearson, "sup_beta": sup_beta,
    "sup_label": sup_corr_label,
    "lw_years": lw_years, "lw": lw,
    "split": SPLIT,
    "fisher": FISHER,
    "meta": D["meta"],
}

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ABBV × IBB × IHE 相关性对比报告</title>
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
  .kv { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .kv .k { font-size: 12px; color: var(--sub); }
  .kv .v { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .kv .v small { font-size: 12px; font-weight: 400; color: var(--sub); }
  .kv .muted { font-size: 13px; color: var(--sub); margin-top: 4px; font-weight: 400; }
  .up { color: var(--red); } .dn { color: var(--green); } .na { color: var(--grey); }
  .sig { color: var(--verm); }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
  th, td { padding: 8px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  .tsub { font-size: 11px; color: var(--grey); font-weight: 400; }
  .note { font-size: 12.5px; color: var(--sub); margin-top: 10px; }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 290px; }
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
  .pill { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
  .pill.bb { background: #fdf1dd; color: #b5761c; }
  .pill.ihe { background: #e7f0fa; color: #1e5e93; }
  @media (max-width: 720px) { .grid3 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>ABBV × IBB × IHE · 相关性对比报告</h1>
  <div class="subtitle">艾伯维（ABBV）与 <b>生物科技（IBB）</b>、<b>传统制药（IHE）</b> 的日收益联动拆解 · 以 <b>2026-02-01 为分界分阶段计算</b> · 主窗口 2021-08-26 ~ 2026-08-26 · 数据截至 2026-08-26 收盘</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论（分阶段）</h2>
    <div class="grid3">
      <div class="kv"><div class="k">分界前（2021-08 ~ 2026-01，n=__PRE_N__）</div>
        <div class="v"><span class="pill bb">IBB 0.369</span> &nbsp;<span class="pill ihe">IHE 0.493</span></div>
        <div class="muted">制药显著更高 <b>+0.124</b>，Steiger p&lt;0.001</div></div>
      <div class="kv"><div class="k">分界后（2026-02 ~ 2026-08，n=__POST_N__）</div>
        <div class="v"><span class="pill bb">IBB 0.414</span> &nbsp;<span class="pill ihe">IHE 0.509</span></div>
        <div class="muted">制药仍更高 <b>+0.095</b>，p=0.059 边缘不显著（样本仅 143 日）</div></div>
      <div class="kv"><div class="k">β 系数（两阶段均如此）</div>
        <div class="v"><span class="pill bb">0.39→0.47</span> &nbsp;<span class="pill ihe">0.71→0.71</span></div>
        <div class="muted">对制药 β 稳定在 0.7+，明显高于生物科技</div></div>
    </div>
    <div class="concl">
      ① <b>分界前（2021-08 ~ 2026-01）</b>：ABBV 与制药 IHE 的相关性 <b>显著高于</b> 生物科技 IBB——Pearson 0.493 vs 0.369（+0.124，Steiger p&lt;0.001），β 0.71 vs 0.39，R² 24.3% vs 13.7%。该阶段含 2022 年生物科技熊市（IBB −13.6% 而 ABBV +24.0%），制药占优最突出。<br>
      ② <b>分界后（2026-02 ~ 2026-08）</b>：制药依然占优——0.509 vs 0.414（+0.095），β 0.71 vs 0.47，R² 25.9% vs 17.1%。方向与分界前一致，但分界后仅 143 个交易日，差异未达 5% 显著（p=0.059，边缘）。<br>
      ③ <b>阶段间结构稳定</b>：Fisher z 检验显示，分界前后 ABBV×IBB（0.369→0.414，p=0.56）与 ABBV×IHE（0.493→0.509，p=0.81）的相关性<b>均无显著变化</b>——"制药占优"不是某个阶段的现象，而是贯穿全窗口的稳定结构。<br>
      ④ <b>长窗口（2015 起，XBI/XPH 补充）呈时间依赖</b>：2015–2020 年 ABBV 与生物科技联动略强（2016 年 IBB 0.65 vs XPH 0.60），2020 年起制药反超并持续占优——ABBV 板块属性随时间从生物科技向传统制药漂移（Humira 专利悬崖后的防御化 + Allergan 并购）。<br>
      ⑤ <b>前提</b>：IHE（2026-08-20 持仓前 25 名）与 IBB（前 20 名）当前<b>均不含 ABBV</b>，相关性无机械抬升，反映的是真实板块联动。
    </div>
    <div class="src">数据：ABBV / IBB 来自 Yahoo Finance 日线（adj_close 复权），IHE 来自腾讯自选股前复权日线（2021-08 起，含 2024-03 的 3:1 拆股调整），XBI/XPH 来自 Yahoo Finance。计算：日收益率 Pearson/Spearman 相关、OLS β 与 R²、60 日滚动相关、Steiger(1980) 两依赖相关差异检验（r₁₂=ABBV×IBB、r₁₃=ABBV×IHE 共享 ABBV，故用完整三相关矩阵做依赖校正）、Fisher z 分阶段差异检验。<b>分界点沿用项目惯例 2026-02-01；全部指标均在三标的重叠日期区间上计算，保证口径一致。</b></div>
  </div>

  <!-- 滚动相关 -->
  <div class="card">
    <h2>60 日滚动相关性：制药线长期在生物科技线上方 <span class="tag">动态监测 · 2021-08 起</span></h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#E69F00"></span>ABBV×IBB（生物科技，橙）· <span class="legend-dot" style="background:#0072B2"></span>ABBV×IHE（制药，蓝）· 红色竖虚线=2026-02-01 分界。滚动 60 日相关系数。<b>蓝色制药线在多数时段位于橙色生物科技线上方（均值 46.8 vs 36.6）且更稳定</b>；两条线 2023–2024 年多次收敛甚至交叉，2025 年下半年起再度拉开——制药联动占优是持续性的，分界前后均成立，但并非所有时段。</div>
  </div>

  <!-- 分阶段总表 -->
  <div class="card">
    <h2>分阶段统计总表 <span class="tag">以 2026-02-01 为界</span></h2>
    <table>
      <tr><th>区间</th><th>ABBV×IBB r</th><th>ABBV×IHE r</th><th>差值</th><th>Steiger p</th><th>β(IBB)</th><th>β(IHE)</th><th>ABBV 涨</th><th>IBB 涨</th><th>IHE 涨</th></tr>
      __BLOCK_ROWS__
    </table>
    <div class="note">分界前 n=1111、分界后 n=143。R² 视角：两阶段 IHE 解释 ABBV 日收益方差的 24%–26%，IBB 仅 14%–17%——<b>约四分之三是自身特质</b>。</div>
  </div>

  <!-- 分年度 -->
  <div class="card">
    <h2>分年度相关系数：2022 年制药显著占优，其余年份接近 <span class="tag">自然年 Pearson</span></h2>
    <div id="chart_year" class="chart-sm"></div>
    <div class="note">2022 年制药相关性 0.576 显著高于生物科技 0.336（p&lt;0.001）——分界前制药占优的最突出年份；2023/2025/2026 年制药小幅领先（+0.04~+0.07，不显著）；2024 年完全持平（0.302/0.302）。</div>
    <table>
      <tr><th>年份</th><th>ABBV×IBB r</th><th>ABBV×IHE r</th><th>差值</th><th>Steiger p</th><th>ABBV 区间涨</th><th>IBB 涨</th><th>IHE 涨</th></tr>
      __YEAR_ROWS__
    </table>
    <div class="note">收益口径：区间首尾复权收盘价累计涨跌幅，不含成本。2026 年为截至 08-26 的年内表现。</div>
  </div>

  <!-- 月度相关 -->
  <div class="card">
    <h2>月度相关性（近 36 个月）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月度视角：两条线长期在 −0.3 ~ +0.8 间摆动，<b>蓝色制药线多数月份位于橙色生物科技线上方</b>；2025 年全年两者同处高位，2026 年以来制药线再度明显领先（2026 年月均 ABBV×IHE ≈ 0.53 vs ABBV×IBB ≈ 0.46）。</div>
  </div>

  <!-- 长窗口补充 -->
  <div class="card">
    <h2>2015 年起长窗口补充：相关性随时间从生物科技漂向制药 <span class="tag">IBB / XBI / XPH</span></h2>
    <div id="chart_lw" class="chart"></div>
    <div class="note">分年度折线（2016–2026）：<b>2015–2020 年 ABBV 与生物科技（IBB，橙）的联动普遍强于制药（XPH，蓝），2020 年制药首次反超，2021 年起制药端持续占优</b>——ABBV 免疫学管线（Humira → Skyrizi/Rinvoq）与并购（Allergan 2020）带来的业务结构变化，在日频联动上同步体现为"从生物科技属性向传统制药属性漂移"。</div>
    <div id="chart_sup" class="chart-sm"></div>
    <div class="note">全期对比（2015-01 ~ 2026-08）：ABBV×IBB 0.488 ≈ ABBV×XPH 0.476，均明显高于小盘生物科技 XBI 0.400（β 仅 0.33）——<b>ABBV 与大型生物科技及大型制药的联动相当，与小盘高波动生物科技风格差异最大</b>。</div>
    <table>
      <tr><th>组合</th><th>窗口</th><th>Pearson r</th><th>Spearman ρ</th><th>β</th><th>R²</th><th>ABBV 区间涨</th><th>指数区间涨</th></tr>
      __SUP_ROWS__
    </table>
    <div class="note">ABBV 自 2015-01 以来累计 +551.6%，远超三个指数（IBB +116.9%、XBI +173.2%、XPH +60.8%）——相关性强弱与涨跌无关，2022 年 ABBV 大涨而生物科技大跌，正是相关最低的年份之一。</div>
  </div>

  <!-- 分块总表 -->
  <div class="card">
    <h2>分阶段统计总表 <span class="tag">完整覆盖</span></h2>
    <table>
      <tr><th>区间</th><th>ABBV×IBB r</th><th>ABBV×IHE r</th><th>差值</th><th>Steiger p</th><th>β(IBB)</th><th>β(IHE)</th><th>ABBV 涨</th><th>IBB 涨</th><th>IHE 涨</th></tr>
      __BLOCK_ROWS__
    </table>
    <div class="note">近 1 年与 2026 年以来 ABBV×IHE 均领先（0.52/0.53 vs 0.45/0.46），差值 −0.07 左右，样本有限、p≈0.07–0.12 边际不显著；全期显著性主要由 2022 年贡献。R² 视角：全期 IHE 解释 ABBV 日收益方差的 24.6%，IBB 仅 14.1%——<b>约四分之三是自身特质</b>。</div>
  </div>

  <!-- 结论 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>核心答案</b>：<b>分界前（2021-08 ~ 2026-01）制药相关性显著高于生物科技</b>（IHE 0.493 vs IBB 0.369，Steiger p&lt;0.001）；<b>分界后（2026-02 ~ 2026-08）制药仍占优</b>（0.509 vs 0.414，方向一致，p=0.059 边缘不显著）。两阶段之间两对相关性均无显著变化（Fisher p&gt;0.55）——"制药占优"是贯穿全窗口的稳定结构。</li>
      <li><b>β 口径最稳健</b>：无论分界前后，ABBV 对 IHE 的 β 都稳定在 0.71 左右，对 IBB 仅 0.39→0.47——即使相关系数差异在分界后未达显著，敏感性口径的差距始终明确。</li>
      <li><b>长窗口补充（2015 起）</b>：2015–2020 年 ABBV 与生物科技联动略强（2016 年 IBB 0.65 vs XPH 0.60），2020 年起制药反超并持续占优——ABBV 板块属性随时间从生物科技向传统制药漂移（Humira 专利悬崖后防御化 + Allergan 并购），分阶段结论与长窗口趋势方向一致。</li>
      <li><b>组合含义</b>：若用板块指数对冲/复制 ABBV 敞口，IHE 是比 IBB 更贴近的参照（β 0.71 vs 0.39–0.47）；但两阶段 IHE 也只能解释 ABBV 日收益方差的约 1/4，IBB 更只有 1/7——ABBV 的特质性远大于板块系统性风险，指数对冲效果有限。</li>
      <li><b>局限与口径</b>：① 分界后仅 143 个交易日，分界后的相关差异未达 5% 显著（p=0.059）是样本量限制，需以 60 日滚动趋势为辅证；② IHE 数据仅 5 年（腾讯自选股），更早历史以 XPH 代理（成分高度重叠但非同一标的）；③ 持仓快照仅验证当前（2026-08）IHE/IBB 不含 ABBV，历史上是否曾纳入需另核实，不影响本窗口结论；④ 相关性为统计描述非因果，板块漂移归因为公开信息推断；⑤ 未核算交易成本与股息再投资。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。指数持仓与板块归因为公开信息整理，若需确证需另行核实。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const D = __DATA_JSON__;
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' },
                    splitLine: { lineStyle: { color: '#eef1f6' } } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec',
                      textStyle: { color: '#1f2733' } };
const NAME = { abbv_ibb: 'ABBV×IBB 生物科技', abbv_ihe: 'ABBV×IHE 制药' };
const COL = { abbv_ibb: '#E69F00', abbv_ihe: '#0072B2' };
const LW = { IBB: 'ABBV×IBB 生物科技', XBI: 'ABBV×XBI 小盘生物科技', XPH: 'ABBV×XPH 制药' };
const LWC = { IBB: '#E69F00', XBI: '#CC79A7', XPH: '#0072B2' };
const LWL = { IBB: 'solid', XBI: 'dashed', XPH: 'solid' };
const SPLIT = D.split;

// 1) 60 日滚动相关
echarts.init(document.getElementById('chart_roll')).setOption({
  tooltip: tooltipAxis,
  legend: { data: [NAME.abbv_ibb, NAME.abbv_ihe], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.r60.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关', min: -0.5, max: 0.9 }, axisStyle),
  series: [
    { name: NAME.abbv_ibb, type: 'line', data: D.r60.abbv_ibb, showSymbol: false,
      lineStyle: { width: 1.6, color: COL.abbv_ibb }, itemStyle: { color: COL.abbv_ibb } },
    { name: NAME.abbv_ihe, type: 'line', data: D.r60.abbv_ihe, showSymbol: false,
      lineStyle: { width: 1.6, color: COL.abbv_ihe }, itemStyle: { color: COL.abbv_ihe },
      markLine: { silent: true, symbol: 'none',
        label: { formatter: '2026-02 分界', color: '#D55E00', fontSize: 11, position: 'insideEndTop' },
        lineStyle: { color: '#D55E00', type: 'dashed', width: 1 },
        data: [{ xAxis: D.r60.date.findIndex(d => d >= SPLIT) }] } }
  ]
});

// 2) 分年度（成组柱）
echarts.init(document.getElementById('chart_year')).setOption({
  tooltip: tooltipAxis,
  legend: { data: [NAME.abbv_ibb, NAME.abbv_ihe], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 30 },
  xAxis: Object.assign({ type: 'category', data: D.years }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '年相关', min: 0, max: 0.8 }, axisStyle),
  series: [
    { name: NAME.abbv_ibb, type: 'bar', data: D.y_ibb, barGap: '20%',
      itemStyle: { color: COL.abbv_ibb }, label: { show: true, position: 'top', fontSize: 11, formatter: '{c}' } },
    { name: NAME.abbv_ihe, type: 'bar', data: D.y_ihe, barGap: '20%',
      itemStyle: { color: COL.abbv_ihe }, label: { show: true, position: 'top', fontSize: 11, formatter: '{c}' } }
  ]
});

// 3) 月度相关（近 36 个月）
echarts.init(document.getElementById('chart_monthly')).setOption({
  tooltip: tooltipAxis,
  legend: { data: [NAME.abbv_ibb, NAME.abbv_ihe], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.monthly.month, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '月相关', min: -0.8, max: 0.9 }, axisStyle),
  series: [
    { name: NAME.abbv_ibb, type: 'line', data: D.monthly.abbv_ibb, showSymbol: false,
      lineStyle: { width: 1.5, color: COL.abbv_ibb }, itemStyle: { color: COL.abbv_ibb } },
    { name: NAME.abbv_ihe, type: 'line', data: D.monthly.abbv_ihe, showSymbol: false,
      lineStyle: { width: 1.5, color: COL.abbv_ihe }, itemStyle: { color: COL.abbv_ihe } }
  ]
});

// 4) 长窗口分年度折线（ABBV vs IBB/XBI/XPH）
echarts.init(document.getElementById('chart_lw')).setOption({
  tooltip: tooltipAxis,
  legend: { data: [LW.IBB, LW.XBI, LW.XPH], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.lw_years.map(String), boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '年相关', min: 0, max: 0.8 }, axisStyle),
  series: ['IBB', 'XBI', 'XPH'].map(t => ({
    name: LW[t], type: 'line', data: D.lw[t], showSymbol: true, symbolSize: 6,
    lineStyle: { width: 1.8, type: LWL[t], color: LWC[t] }, itemStyle: { color: LWC[t] }
  }))
});

// 5) 长窗口全期（成组柱: r 与 beta 双轴）
echarts.init(document.getElementById('chart_sup')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['Pearson r', 'β'], top: 0 },
  grid: { left: 55, right: 55, top: 40, bottom: 30 },
  xAxis: Object.assign({ type: 'category', data: D.sup_label }, axisStyle),
  yAxis: [
    Object.assign({ type: 'value', name: 'r', min: 0, max: 0.6 }, axisStyle),
    Object.assign({ type: 'value', name: 'β', min: 0, max: 0.6 }, axisStyle)
  ],
  series: [
    { name: 'Pearson r', type: 'bar', data: D.sup_pearson, barGap: '20%',
      itemStyle: { color: '#56B4E9' }, label: { show: true, position: 'top', fontSize: 11, formatter: '{c}' } },
    { name: 'β', type: 'bar', yAxisIndex: 1, data: D.sup_beta, barGap: '20%',
      itemStyle: { color: '#CC79A7' }, label: { show: true, position: 'top', fontSize: 11, formatter: '{c}' } }
  ]
});
</script>
</body>
</html>
"""

HTML = HTML.replace("__BLOCK_ROWS__", block_rows(D["blocks"]))
HTML = HTML.replace("__YEAR_ROWS__", block_rows(D["yearly"], kind="year"))
HTML = HTML.replace("__SUP_ROWS__", sup_rows())
HTML = HTML.replace("__PRE_N__", str(pre["n"]))
HTML = HTML.replace("__POST_N__", str(post["n"]))
HTML = HTML.replace("__DATA_JSON__", json.dumps(JS, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")
