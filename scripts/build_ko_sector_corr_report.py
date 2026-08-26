# -*- coding: utf-8 -*-
"""构建研报32：KO × 科技(XLK)/制药(XPH,代理IHE)/医疗保健(XLV) 分阶段相关性分析
读取 results/ko_sector_corr.json
输出 reports/32_ko_科技医药相关性/index.html（浅底深字研报风 + ECharts + Okabe-Ito 色弱安全）
静默写盘：只打印 written 路径与体积。
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "32_ko_科技医药相关性")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "ko_sector_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

PAIRS = D["pairs"]
PA = {p["tag"]: p for p in PAIRS}
XLK, XPH, XLV = PA["XLK"], PA["XPH"], PA["XLV"]

COLOR = {"XLK": "#0072B2", "XPH": "#E69F00", "XLV": "#CC79A7"}
LINESTYLE = {"XLK": "solid", "XPH": "dashed", "XLV": "dotted"}
NAME = {"XLK": "科技 XLK", "XPH": "制药 XPH", "XLV": "医疗保健 XLV"}
SHORT = {"XLK": "科技", "XPH": "制药", "XLV": "医疗"}

# ---------------- 表格构建 ----------------
def cls(v, invert=False):
    """红涨绿跌。corr 正负用符号辅助；涨跌用 up/dn"""
    if v is None:
        return "na"
    return "up" if v > 0 else "dn"

def block_rows(p):
    rows = []
    for b in p["blocks"]:
        if b["n"] == 0:
            continue
        hl = " class='hl'" if "分界后" in b["name"] else ""
        ex = b["excess_ret"]
        rows.append(
            f"<tr{hl}><td class='nowrap'><b>{b['name']}</b></td>"
            f"<td>{b['n']}</td>"
            f"<td class='{cls(b['pearson'])}'>{b['pearson']:.3f}</td>"
            f"<td class='{cls(b['spearman'])}'>{b['spearman']:.3f}</td>"
            f"<td>{b['r2']*100:.1f}%</td>"
            f"<td>{b['beta']:.3f}</td>"
            f"<td>{b['ann_vol_ko']:.1f}/{b['ann_vol_sec']:.1f}</td>"
            f"<td class='{cls(b['ko_ret_total'])}'>{b['ko_ret_total']:+.1f}%</td>"
            f"<td class='{cls(b['sec_ret_total'])}'>{b['sec_ret_total']:+.1f}%</td>"
            f"<td class='{cls(ex)}'>{ex:+.1f}pp</td></tr>")
    return "\n".join(rows)

def fisher_text(p):
    f = p["fisher"]
    if not f:
        return "样本不足，未做检验"
    sig = "显著" if f["sig"] else "不显著"
    return f"Fisher z = {f['z']}（p = {f['p_value']:.4f}）<b>{'结构变化' if f['sig'] else '无显著变化'}</b>"

def extreme_grid(p):
    e = p["extreme"]
    def hit(v):
        return "—" if v is None else f"{v:.1f}%"
    corr_txt = "—" if e["corr_on_extreme_days"] is None else f"{e['corr_on_extreme_days']:.2f}"
    return f"""
    <div class="kv"><div class="k">KO 异动而板块不动</div>
      <div class="v">{e['ko_only']} <small>天</small></div>
      <div class="muted">板块大幅异动时 KO 同步率 <b>{hit(e['hit_rate_sec_given_ko'])}</b></div></div>
    <div class="kv"><div class="k">板块异动而 KO 不动</div>
      <div class="v">{e['sec_only']} <small>天</small></div>
      <div class="muted">KO 大幅异动时板块同步率 <b>{hit(e['hit_rate_ko_given_sec'])}</b></div></div>
    <div class="kv"><div class="k">同日双方都异动</div>
      <div class="v">{e['both']} <small>天</small></div>
      <div class="muted">共同异动日相关 <b>{corr_txt}</b></div></div>
    <div class="kv"><div class="k">任一标的大幅异动</div>
      <div class="v">{e['either']} <small>天</small></div>
      <div class="muted">2021-01 ~ 2026-08，|日收益| ≥ 3%</div></div>"""

# ---------------- 图表数据（JS 注入） ----------------
# 注意：JSON 中 rolling60/monthly/yearly 的 corr 为百分数（×100，与项目惯例一致），
# 注入 ECharts 折线图时必须 ÷100 还原为 0~1 小数（历史坑：32/37 号曾整线溢出画布）。
# zscore / 归一化价格不需要 ÷100。
# 60日滚动相关：三组合对齐到各自时间轴，全部输出，前端只画 2020 之后
def build_roll(p):
    pts = [(d["date"], d["corr"] / 100) for d in p["rolling60"] if d["corr"] is not None]
    return {"date": [x[0] for x in pts], "corr": [x[1] for x in pts]}

# 年度相关（三序列）
years_all = sorted({y["year"] for p in PAIRS for y in p["yearly"]})
y_series = {}
for tag in ["XLK", "XPH", "XLV"]:
    m = {y["year"]: y["corr"] / 100 for y in PA[tag]["yearly"]}
    y_series[tag] = [m.get(y) for y in years_all]

# 月度相关（近 36 个月，三组合）
def build_monthly(p, limit=36):
    m = p["monthly"]
    m = m[-limit:]
    return {"month": [x["month"] for x in m], "corr": [x["corr"] / 100 for x in m]}

# 归一化价格（分界前后）——用近 3 年的价格做 100 基准更直观
def build_norm_recent(p, anchor="2023-06-01"):
    """以 2023-06 起算归一化（含分界前后）"""
    for n in p["norm_series"]:
        if n["phase"] == "pre":
            pre = n
    # 直接从价格序列构建：取 2023-06 之后的所有日期
    recent = [x for x in p["price_recent"] if x["date"] >= anchor]
    return {
        "date": [x["date"] for x in recent],
        "ko": [round(x["ko"] / p["price_recent"][0]["ko"] * 100, 2) for x in recent],
        "sec": [round(x["sec"] / p["price_recent"][0]["sec"] * 100, 2) for x in recent],
    } if len(recent) else None

# 相对强弱 zscore（每组合近 3 年）
def build_rel(p, anchor="2023-06-01"):
    pts = [(d["date"], d["z"]) for d in p["rel_strength"]
           if d["date"] >= anchor and d["z"] is not None]
    return {"date": [x[0] for x in pts], "z": [x[1] for x in pts]}

SPLIT = XLK["split"]

JS = {
    "split": SPLIT,
    "roll": {t: build_roll(PA[t]) for t in ["XLK", "XPH", "XLV"]},
    "years": years_all,
    "yearSeries": y_series,
    "monthly": {t: build_monthly(PA[t]) for t in ["XLK", "XPH", "XLV"]},
    "norm": {t: build_norm_recent(PA[t]) for t in ["XLK", "XPH", "XLV"]},
    "rel": {t: build_rel(PA[t]) for t in ["XLK", "XPH", "XLV"]},
    "blocks": {t: PA[t]["blocks"] for t in ["XLK", "XPH", "XLV"]},
    "extreme": {t: PA[t]["extreme"] for t in ["XLK", "XPH", "XLV"]},
    "fisher": {t: PA[t]["fisher"] for t in ["XLK", "XPH", "XLV"]},
    "meta": D["meta"],
}

# ---------------- HTML 模板 ----------------
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KO × 科技/制药/医疗保健 相关性分析报告</title>
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
  .up { color: var(--red); } .dn { color: var(--green); } .na { color: var(--grey); }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; margin-top: 6px; }
  th, td { padding: 9px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  tr.hl { background: #f4f8ff; }
  .note { font-size: 12.5px; color: var(--sub); margin-top: 10px; }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 280px; }
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
  .sect-title { font-size: 19px; font-weight: 700; margin: 26px 0 12px; display: flex; align-items: center; gap: 8px; }
  .sect-title::before { content: ""; width: 5px; height: 18px; background: var(--verm); border-radius: 2px; }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>KO × 科技 / 制药 / 医疗保健 · 相关性分析报告</h1>
  <div class="subtitle">可口可乐（KO）分别对科技（XLK）、制药（XPH 代理 IHE）、医疗保健（XLV）的分阶段联动拆解 · 以 2026-02-01 为结构断裂点 · 数据截至 2026-08-21</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">KO × 科技 XLK</div>
        <div class="v">0.30 → <span class="dn">−0.40</span></div>
        <div class="muted">全期 0.298 → 2026-02 后 <b>−0.397</b>（由正转负）<br>Fisher z = 8.63（p&lt;0.001）<b>极显著转负</b></div></div>
      <div class="kv"><div class="k">KO × 制药 XPH（代理 IHE）</div>
        <div class="v">0.41 → <span class="na">0.03</span></div>
        <div class="muted">分界前 0.407 → 分界后 <b>0.026</b>（衰减至零）<br>Fisher z = 4.67（p&lt;0.001）<b>显著脱钩</b></div></div>
      <div class="kv"><div class="k">KO × 医疗保健 XLV</div>
        <div class="v">0.43 → <span class="up">0.41</span></div>
        <div class="muted">分界前 0.431 → 分界后 <b>0.406</b>（保持稳定）<br>Fisher z = 0.35（p=0.73）<b>无显著变化</b></div></div>
    </div>
    <div class="concl">
      ① <b>KO 与科技的日收益相关性由正转负（0.31 → −0.40，Fisher z=8.63）</b>：2026 年 KO 与科技板块呈现显著反向联动——科技回调日 KO 往往逆势走强，防御资金在科技波动中流向 KO 这类现金流消费股。<br>
      ② <b>KO 与制药（XPH）的相关性衰减至统计零（0.41 → 0.03）</b>：制药板块 2025Q4 起走出独立行情（2025-09 以来 XPH +51.8% vs KO +31.1%），其驱动因子（GLP-1、大药企景气、创新管线）已与 KO 的消费防御逻辑脱钩。<br>
      ③ <b>KO 与广义医疗保健（XLV）的相关性 20 年稳定在 0.4 附近、2026 分界后依然 0.41</b>：XLV 内含保险/服务等宽防御构成，与 KO 的"防御+被动资金"属性同频，两者联动是结构性的、非阶段性。<br>
      ④ <b>极值日体现不对称</b>：KO 与 XLV 共同异动日相关高达 0.99（宏观冲击日完全同步），而与 XLK 共同异动日相关仅 0.49——KO 的"保险柜"属性更贴近广义医疗保健而非科技。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价）。KO×XLK/KO×XLV 全期 1998-12 ~ 2026-08（6957 交易日）；KO×XPH 2006-06 ~ 2026-08（5071 交易日，XPH 数据起点限制）。计算：日收益率 Pearson/Spearman 相关、OLS β 与 R²、60 日滚动相关、Fisher z 检验。分界点沿用项目惯例 2026-02-01。注：用户原指 IHE（iShares 美国制药 ETF），本地无该数据，以成分高度重叠的 XPH（SPDR 标普制药 ETF）代理，两者同属美国大型制药板块。</div>
  </div>

  <!-- 三组合滚动相关对比 -->
  <div class="card">
    <h2>60 日滚动相关性：2026 年三线彻底分化 <span class="tag">动态监测 · 2007 以来</span></h2>
    <div id="chart_roll_comp" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>KO×XLK（科技，实线）· <span class="legend-dot" style="background:#E69F00"></span>KO×XPH（制药，虚线）· <span class="legend-dot" style="background:#CC79A7"></span>KO×XLV（医疗保健，点线）· 橙色竖虚线=2026-02 分界。三条曲线 20 年来长期在 0.2–0.6 区间同向波动（宏观风险溢价驱动），<b>2026 年初起彻底分化：科技线俯冲转负（最低约 −0.4），制药线塌向零轴，唯医疗保健线维持 0.3–0.4</b>——KO 的板块联动结构出现历史罕见的"三向分裂"。</div>
  </div>

  <!-- 分阶段总表 -->
  <div class="card">
    <h2>三组合分阶段相关性总表 <span class="tag">以 2026-02-01 为界 · 完整覆盖</span></h2>
    <table>
      <tr><th>组合 / 区间</th><th>样本</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(KO→板块)</th><th>年化波动 KO/板块</th><th>KO 区间涨幅</th><th>板块区间涨幅</th><th>KO 超额</th></tr>
      __BLOCK_ROWS_XLK__
    </table>
    <div class="note">科技：KO 全期累计 +160.5% vs XLK +1017.3%（跑输 857pp），但 2026 年以来 KO +31.8% 反超 XLK +27.0%（+4.8pp）；分界后相关性 −0.397，R² 却升至 15.8%——<b>反向联动比正向联动"更紧"</b>，科技日波动（30.3%）是 KO（20.7%）的 1.5 倍，KO 在科技大跌日具备显著防御价值。</div>
    <table>
      <tr><th>组合 / 区间</th><th>样本</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(KO→板块)</th><th>年化波动 KO/板块</th><th>KO 区间涨幅</th><th>板块区间涨幅</th><th>KO 超额</th></tr>
      __BLOCK_ROWS_XPH__
    </table>
    <div class="note">制药：KO 与 XPH 全期几乎等幅（+323.4% vs +359.1%），历史上同为"现金流防御"资产、相关 0.41。<b>2025-09 以来 XPH 大涨（+51.8%）而相关跌至 0.07</b>——制药已脱离消费防御因子，被自身的行业景气（GLP-1 减重药、大药企创新管线）单独定价。</div>
    <table>
      <tr><th>组合 / 区间</th><th>样本</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(KO→板块)</th><th>年化波动 KO/板块</th><th>KO 区间涨幅</th><th>板块区间涨幅</th><th>KO 超额</th></tr>
      __BLOCK_ROWS_XLV__
    </table>
    <div class="note">医疗保健：相关性 20 年稳定（0.406–0.431，Fisher z 不显著），β 稳定在 0.4–0.5。2026 年以来 KO +30.9% vs XLV +10.9%（超额 +20.1pp）——<b>同为防御，KO 本轮跑赢广义医疗保健约 20 个百分点</b>，但二者联动结构未变。</div>
  </div>

  <!-- 归一化走势 -->
  <div class="sect-title">分界前后走势拆解（归一化 = 100）</div>

  <div class="card">
    <h2>KO × 科技 XLK：2026 年走势背离，防御资金切换 <span class="tag">2023-06 起归一化</span></h2>
    <div id="chart_norm_xlk" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#1f2733"></span>KO（黑）vs <span class="legend-dot" style="background:#0072B2"></span>XLK（蓝）。2023–2025 年 KO 长期横盘、科技一路新高，两者走势无关（相关 0.31 只是日频噪声共动）；<b>2026 年科技高位剧烈波动、KO 逆势上涨，形成清晰剪刀差</b>——这解释了相关由正转负：科技回落日，资金流入 KO 防御。</div>
  </div>

  <div class="card">
    <h2>KO × 制药 XPH：医药独立行情拉开与 KO 的距离 <span class="tag">2023-06 起归一化</span></h2>
    <div id="chart_norm_xph" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#1f2733"></span>KO（黑）vs <span class="legend-dot" style="background:#E69F00"></span>XPH（橙）。2023–2024 年 KO 与制药走势同步（相关 0.4 以上），<b>2025Q4 起 XPH 受制药行业景气驱动加速上行，KO 温和上涨</b>——两者同属防御却走出不同斜率，日度联动随之衰减至零。</div>
  </div>

  <div class="card">
    <h2>KO × 医疗保健 XLV：联动最稳的一组 <span class="tag">2023-06 起归一化</span></h2>
    <div id="chart_norm_xlv" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#1f2733"></span>KO（黑）vs <span class="legend-dot" style="background:#CC79A7"></span>XLV（紫）。两条曲线几乎全程同向（2026 年以来 KO +30.9% vs XLV +10.9% 力度不同但方向一致），相关维持 0.4——<b>广义医疗保健（含保险/服务权重）与 KO 共享"防御+必选"定价因子，是三者中与 KO 结构最稳定的一组。</b></div>
  </div>

  <!-- 年度相关 -->
  <div class="card">
    <h2>年度相关性：2026 年"三向分裂"为 20 年之最 <span class="tag">自然年 Pearson ×100</span></h2>
    <div id="chart_year" class="chart"></div>
    <div class="note">三条线 2006–2025 年间几乎完全同步（同受宏观周期驱动），<b>2026 年首次裂成三支：科技 −40、制药 +3、医疗保健 +34</b>。历史参照：KO×XLK 在 2000 年科网泡沫破裂时也曾转负（−32），2026 年的 −40 是有数据以来最深负值——防御/进攻切换是 KO 与科技关联的常态剧本，但本轮幅度创纪录。</div>
  </div>

  <!-- 月度相关 -->
  <div class="card">
    <h2>月度相关性（近 36 个月）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月度视角：2023–2025 年三条线在 −0.2 ~ +0.6 之间摆动但大体同向（蓝色科技线偏低、紫色医疗线偏高）；<b>2025Q4 起科技线多次转负、制药线缓慢走低、医疗线保持正值</b>——分化是渐进发生的，2026-02 分界点捕捉的是分化加速完成段。</div>
  </div>

  <!-- 极端日 -->
  <div class="card">
    <h2>极端日分析：2021 年以来 |日收益| ≥ 3% 的归属 <span class="tag">不对称联动</span></h2>
    <div class="grid3">
      <div class="kv"><div class="k">KO × 科技 XLK</div>
        <div class="v">7 <small>天同日异动</small></div>
        <div class="muted">XLK 大异动 86 天中 KO 仅 8.9% 同步；KO 大异动 31 天中 XLK 29.2% 同步。<b>科技是"单向波动源"</b>，KO 几乎不接招。</div></div>
      <div class="kv"><div class="k">KO × 制药 XPH</div>
        <div class="v">4 <small>天同日异动</small></div>
        <div class="muted">XPH 大异动 38 天中 KO 11.8% 同步；共同异动日相关 0.89（制药大跌通常也是系统性风险日）。</div></div>
      <div class="kv"><div class="k">KO × 医疗保健 XLV</div>
        <div class="v">3 <small>天同日异动</small></div>
        <div class="muted">共同异动日相关高达 <b>0.99</b>；XLV 大异动 15 天中 KO 有 25% 同步——<b>广义医疗保健与 KO 在宏观冲击日几乎完全同涨同跌</b>。</div></div>
    </div>
    <div class="note">解读：KO 自身低波动（年化 ~20%），极少单日 |≥3%|（近 5 年仅 24 次），因此"极端日"主要由板块贡献。关键差异在<b>同步日相关</b>：与 XLV 同步日相关 0.99、与 XPH 0.89、与 XLK 仅 0.49——KO 与广义医疗保健在系统性冲击面前的"反应一致性"远高于与科技。</div>
  </div>

  <!-- 相对强弱 -->
  <div class="card">
    <h2>KO / 板块 相对强弱（价格比 250 日 zscore）<span class="tag">近 3 年</span></h2>
    <div id="chart_rel" class="chart"></div>
    <div class="note">zscore &gt; 0 表示 KO 相对该板块走强。<b>2025 年底以来三条线全线抬升：KO 相对科技 z 一度升至 +2 以上（历史极值），相对制药稳定为正，相对医疗保健小幅上行</b>——2026 年是 KO 相对三大板块全面走强的年份，与"防御资金回流消费"的市场叙事一致。</div>
  </div>

  <!-- 归因 -->
  <div class="card">
    <h2>为什么 2026 年三向分裂？—— 防御、进攻与行业因子的再平衡</h2>
    <div class="grid3">
      <div class="kv"><div class="k">KO × 科技：防御 vs 进攻反转</div>
        <div class="v" style="font-size:15px;">科技高波动 + 资金再平衡</div>
        <div class="muted">2026 年科技板块高位波动加剧（年化波动 26→30%），配置资金在科技回调日流入必选消费防御（KO 2026 以来 +31.8%）。历史上 2000、2022 年都出现过同类切换，本轮 KO×XLK 相关 −0.40 为有数据以来最深（2000 年为 −0.32）。</div></div>
      <div class="kv"><div class="k">KO × 制药：行业因子取代防御因子</div>
        <div class="v" style="font-size:15px;">医药进入独立景气周期</div>
        <div class="muted">2025Q4 起制药板块受 GLP-1 减重药放量、大药企创新管线与并购景气驱动强势上行（2025-09 以来 +51.8%），定价因子从"现金流防御"切换到"行业景气"。与 KO 的相关性由 0.41 衰减至 0.03——<b>制药正在从"KO 的同类"变成"KO 的对立面"</b>。</div></div>
      <div class="kv"><div class="k">KO × 医疗保健：防御锚不变</div>
        <div class="v" style="font-size:15px;">广义医疗仍是 KO 的"同类"</div>
        <div class="muted">XLV 内含保险公司（UNH 等权重）与医疗服务的"宽防御"构成，与 KO 共享必选消费+红利+防御资金偏好，相关 20 年稳定 0.4。本轮 KO 跑赢 XLV +20.1pp（2026 以来）说明同为防御，KO 的弹性更强，但<b>联动结构未变——XLV 依然是 KO 最可靠的板块参照系</b>。</div></div>
    </div>
  </div>

  <!-- 结论 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>KO 的"防御定位"在板块结构上高度分化</b>：与广义医疗保健（XLV）的稳定正相关（~0.4）是 20 年结构；与科技（XLK）2026 年转为 −0.40 的深度负相关；与制药（XPH）衰减至 0。笼统说"KO 是防御板块"已不准确——它与哪个"防御"同频取决于该板块的具体构成。</li>
      <li><b>组合含义</b>：当前 KO 与科技构成有效的天然对冲（科技大跌日 KO 走强）；KO 对 XLV 是"同类增强"而非分散（两者同涨同跌）；KO 对制药则已近乎独立敞口——若持有制药多头，KO 不再提供板块内对冲，但可提供风格对冲。</li>
      <li><b>监测信号</b>：若 KO×科技 60 日滚动相关回到 +0.1 上方且月度相关连续转正，说明防御资金切换结束；若 KO×制药相关回升至 0.3+，说明制药重新回到现金流定价。在此之前按"三向分裂"状态处理。</li>
      <li><b>局限与口径</b>：① 分界后样本仅 ~140 个交易日，负相关与零相关的统计窗口较短（Fisher z 虽显著，但结论以 60 日滚动趋势为辅证）；② IHE 无本地数据，以 XPH 代理，两者成分高度重叠但非同一标的，个别时段相关数值可能略有偏差；③ 相关性是统计描述非因果，归因为公开信息综述（推断性）；④ 未核算交易成本与股息再投资。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 日线行情）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。行业景气归因部分为公开信息推断性综述，若需确证需另行核实。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const D = __DATA_JSON__;
const SPLIT = D.split;
const C = { XLK:'#0072B2', XPH:'#E69F00', XLV:'#CC79A7' };
const LS = { XLK:'solid', XPH:'dashed', XLV:'dotted' };
const NAME = { XLK:'科技 XLK', XPH:'制药 XPH', XLV:'医疗保健 XLV' };
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' },
                    splitLine: { lineStyle: { color: '#eef1f6' } } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec',
                      textStyle: { color: '#1f2733' } };
const splitIdx = (arr, date) => arr.findIndex(d => d >= date);

function markLineSplit(catData) {
  const idx = splitIdx(catData, SPLIT);
  return idx >= 0 ? { silent: true, symbol: 'none', label: { formatter: '2026-02 分界', color: '#D55E00', fontSize: 11 },
      lineStyle: { color: '#D55E00', type: 'dashed', width: 1 }, data: [{ xAxis: idx }] } : undefined;
}

// 1) 三组合 60 日滚动相关对比
echarts.init(document.getElementById('chart_roll_comp')).setOption({
  tooltip: tooltipAxis,
  legend: { data: Object.values(NAME), top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.roll.XLK.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: -0.7, max: 1.0 }, axisStyle),
  series: ['XLK','XPH','XLV'].map(t => ({
    name: NAME[t], type: 'line', data: D.roll[t].corr, showSymbol: false,
    lineStyle: { width: 1.6, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: t === 'XLK' ? markLineSplit(D.roll.XLK.date) : undefined
  }))
});

// 2) 归一化走势（三组合各一张）
function normChart(id, tag, koColor, secColor) {
  const n = D.norm[tag];
  if (!n) return;
  echarts.init(document.getElementById(id)).setOption({
    tooltip: tooltipAxis,
    legend: { data: ['KO', NAME[tag]], top: 0 },
    grid: { left: 55, right: 20, top: 34, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: n.date, boundaryGap: false }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '归一化（基准=100）', scale: true }, axisStyle),
    series: [
      { name: 'KO', type: 'line', data: n.ko, showSymbol: false, lineStyle: { width: 2, color: '#1f2733' }, itemStyle: { color: '#1f2733' },
        markLine: markLineSplit(n.date) },
      { name: NAME[tag], type: 'line', data: n.sec, showSymbol: false, lineStyle: { width: 2, type: 'dashed', color: secColor }, itemStyle: { color: secColor } }
    ]
  });
}
normChart('chart_norm_xlk', 'XLK', '#1f2733', C.XLK);
normChart('chart_norm_xph', 'XPH', '#1f2733', C.XPH);
normChart('chart_norm_xlv', 'XLV', '#1f2733', C.XLV);

// 3) 年度相关（三线）
echarts.init(document.getElementById('chart_year')).setOption({
  tooltip: tooltipAxis,
  legend: { data: Object.values(NAME), top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.years.map(String) }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '年相关', min: -0.6, max: 1.0 }, axisStyle),
  series: ['XLK','XPH','XLV'].map(t => ({
    name: NAME[t], type: 'line', data: D.yearSeries[t], showSymbol: true, symbolSize: 5,
    connectNulls: false, lineStyle: { width: 1.8, type: LS[t], color: C[t] }, itemStyle: { color: C[t] }
  }))
});

// 4) 月度相关（三线）
echarts.init(document.getElementById('chart_monthly')).setOption({
  tooltip: tooltipAxis,
  legend: { data: Object.values(NAME), top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.monthly.XLK.month, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '月相关', min: -0.8, max: 0.9 }, axisStyle),
  series: ['XLK','XPH','XLV'].map(t => ({
    name: NAME[t], type: 'line', data: D.monthly[t].corr, showSymbol: false,
    lineStyle: { width: 1.5, type: LS[t], color: C[t] }, itemStyle: { color: C[t] }
  }))
});

// 5) 相对强弱 zscore
echarts.init(document.getElementById('chart_rel')).setOption({
  tooltip: tooltipAxis,
  legend: { data: Object.values(NAME), top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.rel.XLK.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: 'zscore', scale: true }, axisStyle),
  series: ['XLK','XPH','XLV'].map(t => ({
    name: NAME[t], type: 'line', data: D.rel[t].z, showSymbol: false,
    lineStyle: { width: 1.6, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#8c97a6', type: 'dashed', width: 1 }, data: [{ yAxis: 0 }] }
  }))
});
</script>
</body>
</html>
"""

# 注入表格
HTML = HTML.replace("__BLOCK_ROWS_XLK__", block_rows(XLK))
HTML = HTML.replace("__BLOCK_ROWS_XPH__", block_rows(XPH))
HTML = HTML.replace("__BLOCK_ROWS_XLV__", block_rows(XLV))
HTML = HTML.replace("__DATA_JSON__", json.dumps(JS, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")