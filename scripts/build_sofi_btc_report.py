# -*- coding: utf-8 -*-
"""构建研报：SOFI / XYZ(Block) × BTC 季度分阶段相关性
读取 results/sofi_btc_corr.json
输出 reports/50_SOFI_BTC_相关性季度分阶段/index.html
（浅底深字研报风 + ECharts + Okabe-Ito 色弱安全；红涨绿跌；R 与 β 同列；相关存 0~1 小数）
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "50_SOFI_BTC_相关性季度分阶段")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "sofi_btc_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

SOFI = D["sofi"]
XYZ = D["xyz"]
META = D["meta"]

def cls(v):
    if v is None: return "na"
    return "up" if v > 0 else "dn"

def q_rows(pair):
    out = []
    for q in pair["quarters"]:
        sig_txt = "显著" if q["sig"] else "—"
        sig_cls = "sig" if q["sig"] else "na"
        r = f"{q['r']:.3f}" if q["r"] is not None else "—"
        sp = f"{q['spearman']:.3f}" if q["spearman"] is not None else "—"
        b = f"{q['beta']:.2f}" if q["beta"] is not None else "—"
        r2 = f"{q['r2']*100:.0f}%" if q["r2"] is not None else "—"
        out.append(
            f"<tr><td><b>{q['label']}</b><div class='tsub'>{q['start'][5:]} ~ {q['end'][5:]} · n={q['n']}</div></td>"
            f"<td class='{cls(q['r'])}'>{r}</td><td>{sp}</td>"
            f"<td>{q['sig_band']:.3f}</td><td class='{sig_cls}'>{sig_txt}</td>"
            f"<td>{b}</td><td>{r2}</td>"
            f"<td class='{cls(q['ret_ek'])}'>{q['ret_ek']:+.1f}%</td>"
            f"<td class='{cls(q['ret_btc'])}'>{q['ret_btc']:+.1f}%</td></tr>")
    return "\n".join(out)

def year_rows(pair):
    out = []
    for y in pair["yearly"]:
        sig_txt = "显著" if y["sig"] else "—"
        sig_cls = "sig" if y["sig"] else "na"
        r = f"{y['r']:.3f}" if y["r"] is not None else "—"
        b = f"{y['beta']:.2f}" if y["beta"] is not None else "—"
        r2 = f"{y['r2']*100:.0f}%" if y["r2"] is not None else "—"
        out.append(
            f"<tr><td><b>{y['label']}</b><div class='tsub'>n={y['n']}</div></td>"
            f"<td class='{cls(y['r'])}'>{r}</td>"
            f"<td>{y['sig_band']:.3f}</td><td class='{sig_cls}'>{sig_txt}</td>"
            f"<td>{b}</td><td>{r2}</td>"
            f"<td class='{cls(y['ret_ek'])}'>{y['ret_ek']:+.1f}%</td>"
            f"<td class='{cls(y['ret_btc'])}'>{y['ret_btc']:+.1f}%</td></tr>")
    return "\n".join(out)

def full_row(pair):
    f = pair["full"]
    sig_txt = "显著" if abs(f["r"]) > 1.96 / (pair["window"]["n"] - 2) ** 0.5 else "—"
    sig_cls = "sig" if sig_txt == "显著" else "na"
    return (
        f"<tr><td><b>全期</b><div class='tsub'>{pair['window']['start']} ~ {pair['window']['end']} · n={pair['window']['n']}</div></td>"
        f"<td class='{cls(f['r'])}'>{f['r']:.3f}</td><td>{f['spearman']:.3f}</td>"
        f"<td>{1.96/(pair['window']['n']-2)**0.5:.3f}</td><td class='{sig_cls}'>{sig_txt}</td>"
        f"<td>{f['beta']:.2f}</td><td>{f['r2']*100:.0f}%</td>"
        f"<td class='{cls(f['ret_ek'])}'>{f['ret_ek']:+.1f}%</td>"
        f"<td class='{cls(f['ret_btc'])}'>{f['ret_btc']:+.1f}%</td></tr>")

# ---- 注入 JS ----
q_lab = [q["label"] for q in SOFI["quarters"]]
JS = {
    "norm": {"date": [x["date"] for x in SOFI["norm"]],
             "sofi": [x["ek"] for x in SOFI["norm"]],
             "xyz": [x["ek"] for x in XYZ["norm"]],
             "btc": [x["btc"] for x in SOFI["norm"]]},
    "roll60": {"date": [x["date"] for x in SOFI["rolling60"]],
               "r_sofi": [x["r"] for x in SOFI["rolling60"]],
               "r_xyz": [x["r"] for x in XYZ["rolling60"]],
               "band": round(1.96 / (60 - 2) ** 0.5, 4)},
    "q": {"labels": q_lab,
          "sofi_r": [q["r"] for q in SOFI["quarters"]],
          "sofi_sig": [q["sig"] for q in SOFI["quarters"]],
          "xyz_r": [q["r"] for q in XYZ["quarters"]],
          "xyz_sig": [q["sig"] for q in XYZ["quarters"]]},
    "last20": {"sofi": SOFI["last20"], "xyz": XYZ["last20"]},
    "btc_days": {"sofi": SOFI["btc_days"], "xyz": XYZ["btc_days"]},
    "meta": META,
}

F = SOFI["full"]
FX = XYZ["full"]

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SOFI / XYZ × 比特币 · 季度分阶段相关性</title>
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
  .sig { color: var(--verm); font-weight: 600; }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
  th, td { padding: 8px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  .tsub { font-size: 11px; color: var(--grey); font-weight: 400; }
  .note { font-size: 12.5px; color: var(--sub); margin-top: 10px; }
  .paramnote { font-size: 12px; color: var(--sub); background: #fbfcfe; border: 1px dashed var(--line);
               border-radius: 8px; padding: 8px 12px; margin: 10px 0 4px; line-height: 1.75; }
  .paramnote b { color: var(--ink); }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 300px; }
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
  .pill.sofi { background: #e7f0fa; color: #1e5e93; }
  .pill.xyz { background: #fdf1dd; color: #b5761c; }
  .pill.btc { background: #f3e8f5; color: #7d3c98; }
  .big { font-size: 30px; font-weight: 800; }
  @media (max-width: 720px) { .grid3 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>SOFI / Block(XYZ) × 比特币 · 季度分阶段相关性</h1>
  <div class="subtitle">SoFi（SOFI）与 Block（XYZ）近一年涨幅是否为 BTC 上涨所驱动？· 按<b>日历季度分阶段</b>（2023Q1 起，不用单一分界点）· 60 日滚动为主口径 · 窗口 2023-01-03 ~ 2026-08-26（n=915）· 数据截至 2026-08-26</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">SOFI × BTC 全期（2023 起）</div>
        <div class="v">r = <span class="sig">0.303</span> · β = 0.43</div>
        <div class="muted">R² = 9.2% —— BTC 仅解释 SOFI 日波动的 <b>9%</b></div></div>
      <div class="kv"><div class="k">XYZ × BTC 全期（2023 起）</div>
        <div class="v">r = <span class="sig">0.284</span> · β = 0.33</div>
        <div class="muted">R² = 8.1% —— 与 SOFI 同量级，均属弱-中相关</div></div>
      <div class="kv"><div class="k">近 20 交易日（07-30 ~ 08-26）</div>
        <div class="v">SOFI r = 0.21 <span class="na">不显著</span></div>
        <div class="muted">SOFI +14.4% vs BTC +22.0% —— 日度节奏与 BTC 几乎无关</div></div>
    </div>
    <div class="concl">
      ① <b>全期弱-中相关，BTC 解释力有限</b>：2023 年以来 SOFI×BTC 日相关 r=0.303、XYZ×BTC r=0.284，β 0.33~0.43——BTC 单日涨 1%，SOFI 平均只跟 0.43%。R² 均不足 10%，<b>两标的 9 成以上的日波动是自身因素</b>（财报、盈利、估值、利率）。<br>
      ② <b>相关性高度分阶段</b>：2023 年 SOFI 与 BTC 基本不相关（各季度 r 0.02~0.27，多数不显著）；2024Q4（r=0.55）、2026Q1（r=0.56）为两个峰值季；2025 全年稳定在 0.28~0.41。但<b>每个高相关季度都有明显背离样本</b>——2024Q1 SOFI −24.4% 而 BTC +57.5%、2024Q3 SOFI +22.2% 而 BTC +0.7%、2026Q2 SOFI +14.7% 而 BTC −13.9%。<br>
      ③ <b>直接回答疑问：「最近这波」不是 BTC 拉的</b>：7-29 低点以来 SOFI 反弹约 +23%，与 BTC 同期涨幅（约 +22~24%）总涨幅<b>巧合同步</b>；但按最近 20 个交易日逐日收益算，SOFI×BTC r=0.21（显著带 ±0.46，<b>不显著</b>）、β=0.32、R²=4.3%——上涨的<b>日度节奏几乎不由 BTC 决定</b>。<br>
      ④ <b>XYZ 直接证伪「BTC 驱动」</b>：近 20 交易日 XYZ 仅 +0.6% 而 BTC +22.0%；2026Q3 至今 XYZ +7.7% vs BTC +31.6%（r=0.15 不显著）——若真由 BTC 驱动，XYZ 不可能在 BTC 大涨 22% 时纹丝不动。<br>
      ⑤ <b>2026Q3 整体同样掉队</b>：BTC 季度 +31.6%，SOFI 仅 +2.2%（7 月先跌 17% 再反弹）、XYZ 仅 +7.7%——BTC 大涨而金融科技股显著跑输，进一步排除 BTC 是主要驱动。<br>
      ⑥ <b>正相关 ≠ 驱动</b>：两者同受风险偏好/流动性等宏观因子影响（β 0.3~0.5 为背景联动），但 SOFI/XYZ 的行情主逻辑仍是<b>自身基本面</b>（SOFI 盈利与信贷质量、XYZ 支付与持币敞口），BTC 是顺风背景板而非发动机。
    </div>
    <div class="src">数据：SOFI/XYZ 来自 Yahoo Finance 日线（adj_close 复权，美东交易日）；BTC 来自 Binance BTCUSDT 日线（close，UTC 日 K）；交集日期 2023-01-03 ~ 2026-08-26，n=915。计算：日收益率 Pearson/Spearman 相关、OLS β 与 R²、60 日滚动相关、季度分阶段显著带 ±1.96/√(n−2)（60 日 ≈ ±0.26）。R 与 β 同列输出。</div>
  </div>

  <!-- 归一化价格 -->
  <div class="card">
    <h2>归一化价格走势：2023 年以来 SOFI 大涨 3 倍，与 BTC 同向但节奏不同 <span class="tag">2023-01 起点 = 100</span></h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>SOFI（蓝，+318.7%）· <span class="legend-dot" style="background:#E69F00"></span>XYZ（橙，+28.6%）· <span class="legend-dot" style="background:#CC79A7"></span>BTC（紫，+373.9%）。SOFI 的涨幅主要来自 2023 年（+121%）与 2024Q4（+101.8%）、2025 年（+85.3%），2026Q1 一度大跌 42% 后 7-29 低点反弹；XYZ 长期落后 BTC，仅 2024Q4 有脉冲。三条线<b>长期同向上行，但 SOFI 的斜率变化点（2023 末 / 2024 末 / 2026 初）与 BTC 并不对齐</b>——2025 年 BTC 全年 −9.6% 而 SOFI +85.3%，方向完全相反。</div>
  </div>

  <!-- 60 日滚动 -->
  <div class="card">
    <h2>60 日滚动相关性：长期 0.2~0.5 区间，近期小幅抬升 <span class="tag">动态监测 · 灰色虚线=±1.96/√(n−2) 显著带</span></h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>SOFI×BTC（蓝）· <span class="legend-dot" style="background:#E69F00"></span>XYZ×BTC（橙）。滚动 60 日日收益相关。<b>两条线长期在 0.15~0.55 之间摆动，多数时段高于显著带（±0.26）</b>——弱到中等且统计显著的稳定联动；2024Q4（BTC 突破 10 万叙事）与 2026Q1（双双大跌）是两轮峰值；2023 年 SOFI 线长期贴近 0（当年基本脱钩）。<b>最近 60 日 SOFI×BTC 约 0.34~0.41、XYZ×BTC 约 0.25~0.30，均显著但明显弱于 2026Q1 的 0.56</b>——联动没有在近期创新高。</div>
  </div>

  <!-- SOFI 季度表 -->
  <div class="card">
    <h2>SOFI × BTC 季度分阶段总表 <span class="tag">R 与 β 同列</span></h2>
    <div class="paramnote"><b>参数图例：</b>① <b>r (Pearson)</b>=日收益线性相关，−1~1，越接近 1 同涨同跌越强；② <b>Spearman ρ</b>=按收益大小排名后的秩相关，抗极端值，衡量单调联动；③ <b>显著带 ±</b>=±1.96/√(n−2)，|r| 超过此带即「显著」（统计上区别于 0）；④ <b>β</b>=敏感度，BTC 日收益每涨 1% 标的平均跟涨百分之几；⑤ <b>R²</b>=BTC 能解释标的日波动的比例（0~100%，越大联动越强）；⑥ <b>SOFI 涨 / BTC 涨</b>=该区间首尾复权收盘价累计涨跌幅。</div>
    <table>
      <tr><th>季度</th><th>r (Pearson)</th><th>Spearman ρ</th><th>显著带 ±</th><th>显著性</th><th>β (SOFI~BTC)</th><th>R²</th><th>SOFI 涨</th><th>BTC 涨</th></tr>
      __SOFI_FULL_ROW__
      __SOFI_Q_ROWS__
    </table>
    <div class="note">显著带 = ±1.96/√(n−2)（n≈60 → ±0.26）；「显著」= |r| 超过显著带。2026Q3 为 07-01 ~ 08-26（40 个交易日）。<b>关键观察：SOFI 的季度涨跌与 r 高低无单调关系——2024Q1（r=0.41）SOFI 大跌 24% 而 BTC 大涨 57%；2024Q3（r=0.41）SOFI 涨 22% 而 BTC 几乎没动</b>。2026Q3 BTC +31.6% 时 SOFI 仅 +2.2%。</div>
  </div>

  <!-- XYZ 季度表 -->
  <div class="card">
    <h2>XYZ × BTC 季度分阶段总表 <span class="tag">对照组</span></h2>
    <div class="paramnote"><b>参数图例：</b>同 SOFI 表——① r=日收益线性相关（−1~1）；② Spearman ρ=秩相关；③ 显著带 ±=±1.96/√(n−2)，|r| 超带即显著；④ β=BTC 涨 1% 时 XYZ 平均跟涨 %；⑤ R²=BTC 对 XYZ 日波动的解释比例；⑥ XYZ 涨 / BTC 涨=区间累计涨跌幅。</div>
    <table>
      <tr><th>季度</th><th>r (Pearson)</th><th>Spearman ρ</th><th>显著带 ±</th><th>显著性</th><th>β (XYZ~BTC)</th><th>R²</th><th>XYZ 涨</th><th>BTC 涨</th></tr>
      __XYZ_FULL_ROW__
      __XYZ_Q_ROWS__
    </table>
    <div class="note">XYZ（Block）因持有比特币资产（约 8~9 千枚 BTC 的资产负债表敞口）常被归类为「比特币概念股」，但数据显示其与 BTC 的日收益联动（全期 r=0.284）与 SOFI（0.303）同一量级，<b>并无额外 beta</b>；2023Q4 甚至出现 XYZ +79.1% 而 BTC 仅 +53.0%（r=−0.01 完全脱钩）——持仓 BTC 不改变股价驱动逻辑。</div>
  </div>

  <!-- 季度 R 对比柱状图 -->
  <div class="card">
    <h2>季度相关系数对比：两个标的节奏高度同步，但均非「BTC 概念」<span class="tag">深色=显著 · 浅色=不显著</span></h2>
    <div id="chart_q" class="chart"></div>
    <div class="note">SOFI×BTC（蓝）与 XYZ×BTC（橙）逐季 r。两条线走势几乎同步（二者同受金融科技×加密市场情绪影响），峰值都在 2024Q4 与 2026Q1；2023 年多数季度不显著。<b>2026 年以来季度 r 在 0.33~0.56，比 2023 年（0.02~0.27）明显抬升——联动增强是真实的，但 R² 仍只有 11%~31%</b>。</div>
  </div>

  <!-- 近期特写 -->
  <div class="card">
    <h2>「最近这波上涨」特写：总涨幅同步是巧合，日度节奏无关 <span class="tag">近 20 交易日</span></h2>
    <div class="grid3">
      <div class="kv"><div class="k">SOFI 近 20 交易日（07-30~08-26）</div>
        <div class="v"><span class="up">+14.4%</span> vs BTC <span class="up">+22.0%</span></div>
        <div class="muted">r=0.21（显著带 ±0.46 <span class="na">不显著</span>）· β=0.32 · R²=4.3%</div></div>
      <div class="kv"><div class="k">XYZ 近 20 交易日（07-30~08-26）</div>
        <div class="v"><span class="up">+0.6%</span> vs BTC <span class="up">+22.0%</span></div>
        <div class="muted">r=0.20（<span class="na">不显著</span>）· β=0.20 · R²=4.1% —— BTC 大涨 22% 而 XYZ 几乎没动</div></div>
      <div class="kv"><div class="k">BTC 单日 ≥2% 大涨日（全期 182 天）</div>
        <div class="v">SOFI 平均 <span class="up">+1.68%</span> / XYZ <span class="up">+1.16%</span></div>
        <div class="muted">跟涨但不及 BTC 本身涨幅；BTC ≥2% 大跌日（162 天）SOFI −1.41% / XYZ −1.36%</div></div>
    </div>
    <div class="note">7-29 低点（15.25 美元）以来 SOFI 约 +23%，与 BTC 同期约 +23% 的总涨幅<b>数字上完全一致</b>，但逐日对齐后的相关性 r≈0.21 不显著、β≈0.32——这波 SOFI 反弹的<b>每一个交易日节奏</b>与 BTC 的日涨跌基本独立。同期 BTC≥2% 的大涨日 SOFI 平均仅 +1.8%（4 天中 2 天 SOFI 同步 ≥2%），也不构成「BTC 每涨 SOFI 必涨」的强耦合。归因更合理的方向：SOFI 自身 7-29 前后出现的事件性回调（单日 −9%）后的修复 + 金融科技板块情绪，BTC 同涨只是同一宏观顺风下的背景。</div>
  </div>

  <!-- 分年度 -->
  <div class="card">
    <h2>分年度汇总 <span class="tag">自然年 Pearson</span></h2>
    <div class="paramnote"><b>参数图例：</b>r / 显著带 ± / β / R² 含义同季度表（按自然年整段计算）；「涨」=该自然年首尾累计涨跌幅（2026 年为截至 08-26 的年内表现）。</div>
    <table>
      <tr><th>年份</th><th>r (SOFI×BTC)</th><th>显著带 ±</th><th>显著性</th><th>β</th><th>R²</th><th>SOFI 涨</th><th>BTC 涨</th></tr>
      __SOFI_Y_ROWS__
    </table>
    <table>
      <tr><th>年份</th><th>r (XYZ×BTC)</th><th>显著带 ±</th><th>显著性</th><th>β</th><th>R²</th><th>XYZ 涨</th><th>BTC 涨</th></tr>
      __XYZ_Y_ROWS__
    </table>
    <div class="note">分年度视角：SOFI×BTC 相关从 2023 年的 0.12（几乎无联动）逐年抬升到 2024 年 0.37、2025 年 0.37、2026 年以来 0.41——<b>联动增强是渐进趋势而非某一事件突变</b>；XYZ×BTC 则 2023~2026 稳定在 0.13~0.35。2026 年（截至 08-26）SOFI −31.4% 而 BTC −12.2%，即便相关性处于历史高位，涨跌方向也由自身决定；2025 年 BTC −9.6% 而 SOFI +85.3%，更是反向样本。</div>
  </div>

  <!-- 结论 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>核心答案</b>：<b>SOFI/XYZ 最近这波上涨基本不是 BTC 驱动的</b>。全期（2023 起）日相关仅 0.28~0.30（β 0.33~0.43，R² &lt;10%）；最近 20 个交易日相关不显著（r≈0.21，显著带 ±0.46）；2026Q3 BTC +31.6% 而 SOFI +2.2%、XYZ +7.7%，BTC 大涨时两标的明显掉队。</li>
      <li><b>总涨幅巧合</b>：7-29 低点以来 SOFI 约 +23% 与 BTC 同期约 +23% 数字巧合，但逐日相关不显著——<b>用「总涨幅同步」判断驱动关系是陷阱</b>，正确做法是对齐日收益看相关/β。</li>
      <li><b>联动在增强（趋势项）</b>：季度 r 从 2023 年的 0.02~0.27 抬升到 2024Q4/2026Q1 的 0.55~0.56，2025 年以来稳定显著（0.33~0.46）——金融科技×加密的同频在变强，BTC 作为背景 beta 的权重上升，但仍解释不了大部分波动（R² 11%~31%）。</li>
      <li><b>β 的含义</b>：全期 β=0.43（SOFI）/0.33（XYZ）意味着 BTC 每涨 1%，SOFI 平均跟 0.43%——若把 BTC 当作情绪风向标，SOFI 的弹性不足一半；即便未来 BTC 续涨，对 SOFI 的拉动也有限。</li>
      <li><b>局限与口径</b>：① 币安 BTC 为 UTC 日 K、美股为美东交易日，日期字符串对齐存在约数小时窗口差异，日线口径可接受但不精确；② 相关性是统计描述非因果，归因推断基于公开信息；③ 本报告未含期权/期货联动、也未控制 SPY/纳指等大盘因子——SOFI 与 BTC 的联动可能部分来自「成长股×风险偏好」的共同宏观因子；④ 数据截至 2026-08-26。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const D = __DATA_JSON__;
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' },
                    splitLine: { lineStyle: { color: '#eef1f6' } } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec',
                      textStyle: { color: '#1f2733' } };
const C = { sofi: '#0072B2', xyz: '#E69F00', btc: '#CC79A7', grey: '#8c97a6', verm: '#D55E00' };

// 1) 归一化价格
echarts.init(document.getElementById('chart_norm')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['SOFI', 'XYZ', 'BTC'], top: 0 },
  grid: { left: 60, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.norm.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '归一化(2023起=100)' }, axisStyle),
  series: [
    { name: 'SOFI', type: 'line', data: D.norm.sofi, showSymbol: false, lineStyle: { width: 1.8, color: C.sofi }, itemStyle: { color: C.sofi } },
    { name: 'XYZ', type: 'line', data: D.norm.xyz, showSymbol: false, lineStyle: { width: 1.4, color: C.xyz }, itemStyle: { color: C.xyz } },
    { name: 'BTC', type: 'line', data: D.norm.btc, showSymbol: false, lineStyle: { width: 1.6, color: C.btc }, itemStyle: { color: C.btc } }
  ]
});

// 2) 60 日滚动相关 + 显著带
const band = D.roll60.band;
echarts.init(document.getElementById('chart_roll')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['SOFI×BTC', 'XYZ×BTC'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.roll60.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '滚动 60 日 r', min: -0.3, max: 0.8 }, axisStyle),
  series: [
    { name: 'SOFI×BTC', type: 'line', data: D.roll60.r_sofi, showSymbol: false,
      lineStyle: { width: 1.8, color: C.sofi }, itemStyle: { color: C.sofi } },
    { name: 'XYZ×BTC', type: 'line', data: D.roll60.r_xyz, showSymbol: false,
      lineStyle: { width: 1.4, color: C.xyz }, itemStyle: { color: C.xyz } },
    { name: '显著带', type: 'line', data: [], markLine: { silent: true, symbol: 'none',
      label: { formatter: '±' + band.toFixed(2), color: C.grey, fontSize: 10, position: 'insideEndTop' },
      lineStyle: { color: C.grey, type: 'dashed', width: 1 },
      data: [{ yAxis: band }, { yAxis: -band }] } }
  ]
});

// 3) 季度 r 柱状图（显著实色 / 不显著浅色）
const sofiBarColor = p => p.dataIndex === -1 ? C.sofi : (D.q.sofi_sig[p.dataIndex] ? C.sofi : '#c9d2de');
const xyzBarColor = p => D.q.xyz_sig[p.dataIndex] ? C.xyz : '#e8d9b0';
echarts.init(document.getElementById('chart_q')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['SOFI×BTC', 'XYZ×BTC'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.q.labels }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '季度 r', min: -0.2, max: 0.8 }, axisStyle),
  series: [
    { name: 'SOFI×BTC', type: 'bar', data: D.q.sofi_r, barGap: '20%',
      itemStyle: { color: sofiBarColor }, label: { show: true, position: 'top', fontSize: 10, formatter: p => D.q.sofi_sig[p.dataIndex] ? p.value.toFixed(2) + ' *' : p.value.toFixed(2) } },
    { name: 'XYZ×BTC', type: 'bar', data: D.q.xyz_r, barGap: '20%',
      itemStyle: { color: xyzBarColor }, label: { show: true, position: 'top', fontSize: 10, formatter: p => D.q.xyz_sig[p.dataIndex] ? p.value.toFixed(2) + ' *' : p.value.toFixed(2) } }
  ]
});
</script>
</body>
</html>
"""

HTML = HTML.replace("__SOFI_FULL_ROW__", full_row(SOFI))
HTML = HTML.replace("__SOFI_Q_ROWS__", q_rows(SOFI))
HTML = HTML.replace("__XYZ_FULL_ROW__", full_row(XYZ))
HTML = HTML.replace("__XYZ_Q_ROWS__", q_rows(XYZ))
HTML = HTML.replace("__SOFI_Y_ROWS__", year_rows(SOFI))
HTML = HTML.replace("__XYZ_Y_ROWS__", year_rows(XYZ))
HTML = HTML.replace("__DATA_JSON__", json.dumps(JS, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")
