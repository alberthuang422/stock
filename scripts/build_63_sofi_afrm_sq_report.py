# -*- coding: utf-8 -*-
"""63 号报告：SOFI / AFRM / XYZ(Block,SQ) 相关性分析 —— 构建 HTML
窗口：特朗普选举胜利（2024-11-05）前 1 个月至今 = 2024-10-05 ~ 2026-08-31
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(BASE, "results", "sofi_afrm_sq_corr.json")
OUT_DIR = os.path.join(BASE, "reports", "63_SOFI_AFRM_SQ相关性分析")
os.makedirs(OUT_DIR, exist_ok=True)

R = json.load(open(IN, encoding="utf-8"))

# ---------- 配色（红涨绿跌，色弱安全：Okabe-Ito + 线型） ----------
C_SOFI = "#e69f00"   # 橙
C_XYZ = "#56b4e9"    # 天蓝
C_AFRM = "#cc79a7"   # 紫红
C_UP = "#c0392b"
C_DN = "#1e8449"

ASSETS = [("SOFI", "SoFi", C_SOFI), ("XYZ", "Block(SQ)", C_XYZ), ("AFRM", "Affirm", C_AFRM)]

PAIRS = [("SOFI", "XYZ"), ("SOFI", "AFRM"), ("AFRM", "XYZ")]
PAIR_NAMES = {
    ("SOFI", "XYZ"): "SOFI × Block(SQ)",
    ("SOFI", "AFRM"): "SOFI × AFRM",
    ("AFRM", "XYZ"): "AFRM × Block(SQ)",
}
PAIR_COLORS = {("SOFI", "XYZ"): "#d55e00", ("SOFI", "AFRM"): "#e69f00", ("AFRM", "XYZ"): "#cc79a7"}

META = R["meta"]

def sig_badge(sig):
    if sig == "sig":
        return '<span class="sig sig-on">显著</span>'
    if sig == "edge":
        return '<span class="sig sig-edge">边缘</span>'
    return '<span class="sig sig-no">不显著</span>'

def fmt_p(p):
    if p is None:
        return "—"
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"

# ---------- 1. 全期相关矩阵表 ----------
mat = R["full_matrix"]
matrix_rows = []
tks = ["SOFI", "XYZ", "AFRM"]
matrix_rows.append("<tr><th class='tk'>日收益相关</th>" + "".join(f"<th>{t}</th>" for t in tks) + "</tr>")
for a in tks:
    cells = f"<td class='tk'><b>{a}</b></td>"
    for b in tks:
        v = mat[a][b]
        if a == b:
            cells += '<td class="bold">1.000</td>'
        else:
            r = v["r"]
            cls = "up" if r > 0.6 else ("bold" if r > 0.4 else "")
            cells += (f'<td class="{cls}">{r:.3f}<br><span class="sub">p={fmt_p(v["p"])}</span>'
                      f'<br>{sig_badge(v["sig"])}</td>')
    matrix_rows.append(f"<tr>{cells}</tr>")

# ---------- 2. 分阶段相关表 ----------
ph = R["phases"]
phase_rows = ""
for pname in ["选举前1月", "选举后1月", "2025全年", "2026至今", "近3月", "近1月"]:
    pr = ph[pname]
    if pr.get("skip"):
        phase_rows += f"<tr><td class='tk'><b>{pname}</b></td><td colspan='4' class='na'>样本不足（{pr['days']} 日）</td></tr>"
        continue
    m = pr["matrix"]
    cells = f"<td class='tk'><b>{pname}</b></td><td>{pr['start']} ~ {pr['end']}<br><span class='sub'>n={pr['days']} 日</span></td>"
    for (a, b) in PAIRS:
        v = m[a][b]
        r = v["r"]
        cells += f"<td>{r:.3f}<br><span class='sub'>p={fmt_p(v['p'])}</span><br>{sig_badge(v['sig'])}</td>"
    phase_rows += f"<tr>{cells}</tr>"

# ---------- 3. 滚动摘要表 ----------
rs = R["rolling_summary"]
roll_rows = ""
for key, label in [("sofi_xyz", "SOFI × Block(SQ)"), ("sofi_afrm", "SOFI × AFRM"), ("afrm_xyz", "AFRM × Block(SQ)")]:
    v = rs[key]
    roll_rows += (f"<tr><td class='tk'><b>{label}</b></td>"
                  f"<td>{v['min']:.2f}</td><td>{v['max']:.2f}</td>"
                  f"<td>{v['mean']:.2f}</td><td>{v['median']:.2f}</td>"
                  f"<td class='bold'>{v['last']:.2f}</td></tr>")

# ---------- 4. 统计表 ----------
st = R["stats"]
stat_rows = ""
for tk, disp, _ in ASSETS:
    s = st[tk]
    cum = s["cum_ret_pct"]
    cls = "up" if cum > 0 else "dn"
    stat_rows += (f"<tr><td class='tk'><b>{tk}</b> <span class='sub'>{disp}</span></td>"
                  f'<td class="{cls}">{cum:+.1f}%</td>'
                  f"<td>{s['annual_vol_pct']:.1f}%</td>"
                  f"<td class='dn'>{s['max_drawdown_pct']:.1f}%</td>"
                  f"<td>{s['daily_mean_pct']:.3f}%</td></tr>")

# ---------- 图表数据 ----------
nav = R["nav"]
JSJSON = json.dumps({
    "nav": {tk: nav[tk] for tk in nav},
    "rolling": {f"{a}_{b}": R["rolling60"][f"{a}_{b}"] for (a, b) in PAIRS},
    "pair_colors": {f"{a}_{b}": PAIR_COLORS[(a, b)] for (a, b) in PAIRS},
}, ensure_ascii=False)

# ---------- 术语 ----------
TERMS = [
    ("相关系数", "Pearson 相关系数 r，衡量两组日收益的线性联动：+1 完全同向、0 无关、−1 完全反向。金融中 r 通常偏正（同受大盘驱动），r≥0.6 才谈得上'同涨同跌'较强。"),
    ("显著性", "p&lt;0.01 为统计显著（sig）、p&lt;0.05 为边缘显著（edge）——表示观察到的相关不太可能纯靠运气。样本越小越难显著。"),
    ("60日滚动相关", "用过去 60 个交易日的收益窗口不断向前滑动计算相关，用于观察相关强度随时间的变化——比单一全期数字更能揭示'何时同步、何时脱钩'。"),
    ("日收益", "当日收盘相对前一收盘的涨跌幅（%）。相关性一律基于日收益而非价格水平，避免趋势造成的'伪相关'。"),
    ("选举前1月", "特朗普赢得 2024-11-05 美国总统选举前的 1 个月窗口（2024-10-07 起），用于捕捉'选举预期'阶段三只股票是否已开始同向联动。"),
    ("选举后1月", "选举结果落地后的 1 个月（2024-11-06 ~ 2024-12-05），观察'特朗普交易'行情中的同步性。"),
    ("Block(SQ)", "Block, Inc.（原 Square），2023 年 6 月股票代码由 SQ 更改为 XYZ。用户习惯仍称其为 SQ，本报告二者为同一公司。"),
    ("金融科技", "FinTech。SOFI（数字银行）、Block（支付+商家生态）、AFRM（BNPL 先买后付）同属金融科技板块，均对利率、信贷需求与风险偏好高度敏感。"),
    ("最大回撤", "从历史高点到后续低点的最大跌幅（%），衡量持有期间的极端痛苦程度。"),
    ("年化波动", "日收益标准差 × √252，折算为一年级别的波动率（%），衡量价格起伏剧烈程度。"),
]
TERM_DICT = {k: v for k, v in sorted(TERMS, key=lambda x: -len(x[0]))}
_TERM_PAT = re.compile("|".join(re.escape(k) for k in TERM_DICT.keys()))
_BLOCK_RE = re.compile(r"(<script[\s\S]*?</script>|<style[\s\S]*?</style>|<title[\s\S]*?</title>)", re.S)

def _annotate_text(text):
    return _TERM_PAT.sub(lambda m: f"<span class='term' data-tip='{TERM_DICT[m.group(0)].replace(chr(39), '&#39;')}'>{m.group(0)}</span>", text)

def annotate_terms(html_str):
    parts = _BLOCK_RE.split(html_str)
    tips = []
    def _protect(m):
        tips.append(m.group(0))
        return f"\x00TIP{len(tips) - 1}\x00"
    protected = []
    for i, seg in enumerate(parts):
        if i % 2 == 0 and seg:
            seg = re.sub(r"data-tip='[^']*'", _protect, seg)
        protected.append(seg)
    out = []
    for i, seg in enumerate(protected):
        if i % 2 == 0 and seg:
            seg = _annotate_text(seg)
        out.append(seg)
    joined = "".join(out)
    for idx, t in enumerate(tips):
        joined = joined.replace(f"\x00TIP{idx}\x00", t)
    return joined

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SOFI / AFRM / Block(SQ) 相关性分析——特朗普当选前1个月至今（2024-10 ~ 2026-08）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --up:#c0392b; --dn:#1e8449; --ink:#2c3e50; --muted:#7f8c8d; --line:#e3e7ea; --bg:#f7f8fa; --card:#ffffff; --accent:#c0392b; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); line-height:1.75; }
  .wrap { max-width:1080px; margin:0 auto; padding:28px 20px 60px; }
  header { border-bottom:3px solid var(--accent); padding-bottom:14px; margin-bottom:22px; }
  header h1 { font-size:24px; letter-spacing:.5px; }
  header .meta { color:var(--muted); font-size:13px; margin-top:6px; }
  h2 { font-size:19px; margin:34px 0 12px; padding-left:10px; border-left:4px solid var(--accent); }
  h3 { font-size:15.5px; margin:18px 0 8px; }
  p { margin:8px 0; font-size:14.5px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px; margin:12px 0; }
  .tldr { background:#fff6f4; border:1px solid #f3c8c0; }
  .tldr h2 { border:none; padding:0; margin:0 0 8px; font-size:17px; color:var(--accent); }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin:14px 0 4px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 12px; }
  .kpi .lab { font-size:12px; color:var(--muted); }
  .kpi .val { font-size:21px; font-weight:700; margin-top:2px; }
  .up { color:var(--up); font-weight:600; }
  .dn { color:var(--dn); font-weight:600; }
  .na { color:var(--muted); }
  .sub { color:var(--muted); font-size:12px; font-weight:400; }
  table { width:100%; border-collapse:collapse; font-size:13.5px; background:var(--card); }
  th, td { border:1px solid var(--line); padding:7px 9px; text-align:center; }
  th { background:#f0f3f6; font-weight:600; }
  td.tk { text-align:left; white-space:nowrap; }
  td.bold { font-weight:700; }
  td.hot { background:#fff0ed; }
  .chart { width:100%; height:400px; }
  .note { font-size:12.5px; color:var(--muted); margin-top:6px; }
  .warn { background:#fdf6e3; border-left:4px solid #d4a017; padding:10px 14px; font-size:13.5px; margin:12px 0; border-radius:0 8px 8px 0; }
  .term { border-bottom:1px dashed #b08; cursor:help; }
  .termtip { display:none; position:fixed; z-index:99; max-width:300px; background:#2c3e50; color:#fff; font-size:12.5px; line-height:1.6; padding:8px 10px; border-radius:6px; box-shadow:0 4px 14px rgba(0,0,0,.25); pointer-events:none; }
  .src { font-size:12.5px; color:var(--muted); }
  .src li { margin:4px 0 4px 18px; }
  .sig { display:inline-block; font-size:11px; padding:1px 7px; border-radius:10px; margin-left:6px; vertical-align:middle; }
  .sig.sig-on { background:#fdecea; color:#c0392b; border:1px solid #e5b8b2; }
  .sig.sig-edge { background:#fff7e0; color:#a06d00; border:1px solid #e8d48a; }
  .sig.sig-no { background:#eef1f4; color:#7f8c8d; border:1px solid #d5dbe0; }
  footer { margin-top:40px; padding-top:14px; border-top:1px solid var(--line); font-size:12.5px; color:var(--muted); }
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>SOFI × AFRM × Block(SQ)：选举后金融科技三兄弟的联动有多强？</h1>
  <div class="meta">相关性分析 · 63 号报告 ｜ 窗口：特朗普当选（2024-11-05）前 1 个月至今 = 2024-10-05 ~ 2026-08-31（476 交易日）｜ 生成于 2026-09-02</div>
</header>

<div class="card tldr">
  <h2>结论先行</h2>
  <p><b>三只金融科技股在选举后窗口整体'中高相关'，其中 SOFI×AFRM 最紧（全期 r=0.642）、AFRM×Block 次之（0.559）、SOFI×Block 最松（0.511），三者均统计显著（p&lt;0.001）。</b>但相关性并非恒定：<span class="term" data-tip="用过去 60 个交易日的收益窗口不断向前滑动计算相关，用于观察相关强度随时间的变化——比单一全期数字更能揭示'何时同步、何时脱钩'。">60 日滚动相关</span>在 0.19~0.91 之间大幅摆动，2025 年一度脱钩、近 3 个月重新收拢（AFRM×Block 滚到 0.789）。<b>同一板块、同受利率与风险偏好驱动，但个股自身 alpha（财报、业务叙事）会周期性把相关打散</b>——对冲/分散逻辑不能只看全期一个数。</p>
  <div class="kpis">
    <div class="kpi"><div class="lab">SOFI × AFRM 全期相关</div><div class="val up">0.642 <span class="sub">显著</span></div></div>
    <div class="kpi"><div class="lab">AFRM × Block(SQ) 全期</div><div class="val up">0.559 <span class="sub">显著</span></div></div>
    <div class="kpi"><div class="lab">SOFI × Block(SQ) 全期</div><div class="val up">0.511 <span class="sub">显著</span></div></div>
    <div class="kpi"><div class="lab">近3月最紧组合</div><div class="val" style="color:#cc79a7;">AFRM×Block 0.789</div></div>
  </div>
</div>

<div class="warn">
  <b>⚠️ 窗口口径说明</b>：本报告按要求只使用 <b>特朗普选举胜利前 1 个月（2024-10-05）至今</b> 的日线数据（共 476 个交易日）。"选举前1月"仅 22 个交易日、相关置信区间很宽（±0.4 量级），该阶段数字只能作方向参考，不能作精确估计；分阶段结论以 2025 全年 / 2026 至今 / 近 3 月为准。<span class="term" data-tip="Block, Inc.（原 Square），2023 年 6 月股票代码由 SQ 更改为 XYZ。用户习惯仍称其为 SQ，本报告二者为同一公司。">Block(SQ)</span> 数据即 XYZ（现代码）。
</div>

<h2>一、全景：选举后累计净值（起点 = 100）</h2>
<div class="card">
  <div id="c_nav" class="chart"></div>
  <div class="note">归一化净值（起点 2024-10-07 = 100）。SOFI 累计 +116% 领跑、AFRM +93% 次之、Block(SQ) 仅 +25%——走势方向大体同步但斜率分化明显，2026 年初以来 SOFI 与 AFRM 的强势与 Block 的相对落后肉眼可见。</div>
</div>

<h2>二、核心：全期相关矩阵（日收益，2024-10 ~ 2026-08）</h2>
<div class="card" style="overflow-x:auto;">
  <table>
    @@MATRIX_ROWS@@
  </table>
  <div class="note"><span class="term" data-tip="Pearson 相关系数 r，衡量两组日收益的线性联动：+1 完全同向、0 无关、−1 完全反向。金融中 r 通常偏正（同受大盘驱动），r≥0.6 才谈得上'同涨同跌'较强。">相关系数</span>基于日收益（%）计算；p 值来自 Pearson 检验。三对组合全部显著，但强度分三档：<b>SOFI×AFRM（0.642）&gt; AFRM×Block（0.559）&gt; SOFI×Block（0.511）</b>。</div>
</div>

<h2>三、相关性随时间变化：60 日滚动相关</h2>
<div class="card">
  <div id="c_roll" class="chart"></div>
  <div class="note">60 日滚动相关三对组合叠加（每对独立配色 + 线型）。<b>三个关键特征</b>：① 2025 年年中一度集体掉到 0.3 以下（个股行情主导期）；② 2026 年以来整体抬升、近 3 个月重新收拢到 0.5~0.8；③ AFRM×Block 近期上冲最猛（0.771），SOFI×Block 仍是三对里最松的一环。</div>
</div>

<h3>滚动相关统计摘要</h3>
<div class="card" style="overflow-x:auto;">
  <table>
    <tr><th class="tk">组合</th><th>最低</th><th>最高</th><th>均值</th><th>中位</th><th>最新（2026-08-31）</th></tr>
    @@ROLL_ROWS@@
  </table>
  <div class="note">滚动区间覆盖 2024-12 ~ 2026-08。三对组合的均值都在 0.49~0.62 的"中相关"区间，但单看极值（0.19 ~ 0.91）就知道：<b>用全期一个数描述这三只股票会严重低估波动</b>。</div>
</div>

<h2>四、分阶段拆解：选举前后与分年</h2>
<div class="card" style="overflow-x:auto;">
  <table>
    <tr><th class="tk">阶段</th><th>区间（交易日数）</th><th>SOFI × Block(SQ)</th><th>SOFI × AFRM</th><th>AFRM × Block(SQ)</th></tr>
    @@PHASE_ROWS@@
  </table>
  <div class="note">选举前 1 月（n=22）与选举后 1 月（n=21）样本量小、仅作方向参考。<b>结构性结论</b>：2025 全年 SOFI×AFRM 达 0.666；2026 年以来三对全部回落一档（SOFI×Block 仅 0.420）——个股行情重新主导；近 3 个月再度收拢且 AFRM×Block 反超成为最紧组合（0.789）。</div>
</div>

<h2>五、个体统计：谁更猛、谁更稳</h2>
<div class="card" style="overflow-x:auto;">
  <table>
    <tr><th class="tk">标的</th><th>区间累计收益</th><th>年化波动</th><th>最大回撤</th><th>日均收益</th></tr>
    @@STAT_ROWS@@
  </table>
  <div class="note">区间 = 2024-10-07 ~ 2026-08-31（476 交易日）。SOFI 与 AFRM 是高波动高弹性组合（年化波动 60%/71%），Block 相对温和但仍高达 52%。三者最大回撤都在 −53%~−56%——2025 年 4 月关税冲击与 2026 年初 AI 抛售期间同步深跌，<b>高相关期恰恰是回撤共振期，分散效果有限</b>。</div>
</div>

<h2>六、解读与局限</h2>
<div class="card">
  <h3>为什么相关会"时而紧、时而松"？</h3>
  <p>三者共同 β：利率预期（高久期成长股对长端利率极敏感）、信贷与消费需求、AI/加密叙事与风险偏好。共同 β 决定相关性的<b>下限</b>；个股 α（SOFI 的净息差与客户增长、AFRM 的 GMV 与坏账、Block 的 Cash App 加密收入）在财报季制造<b>脱钩窗口</b>——2025 年年中滚动相关跌到 0.2 附近，正是三家公司财报与业务叙事各自为政的阶段。</p>
  <h3>局限（务必知情）</h3>
  <ul style="margin-left:18px; font-size:14px;">
    <li><b>窗口起点人为设定</b>：起点选在选举前 1 个月，若换成其他起点（如 2023 年）全期相关会不同——本报告结论仅对"选举后 ~ 至今"这个窗口有效。</li>
    <li><b>相关 ≠ 因果</b>：高相关只能说明同涨同跌，无法区分是共同 β 还是彼此传导；也不含领先/滞后信息（本报告用同日收益）。</li>
    <li><b>短窗口样本小</b>：选举前/后各约 20 个交易日，Pearson 相关标准误 ±0.2 以上，数字仅供方向参考。</li>
    <li><b>单数据源风险</b>：日线价格来自 Yahoo 全量 + 新浪补齐最近 3 个交易日（两源重叠区间价格一致，仅 AFRM 上市首日有 0.875 的 IPO 定价差异，已剔除影响）。</li>
    <li><b>60 日滚动存在平滑滞后</b>：滚动窗口对"拐点"的捕捉约有 1 个月滞后，极值（0.19/0.91）实际发生时间早于显示点。</li>
  </ul>
</div>

<h2>来源与时点</h2>
<ul class="src">
  <li>日线数据：本地 Yahoo Finance chart API 全量（SOFI 自 2021、AFRM 自 2021、XYZ 自 2015），后复权价；2026-08-28 之后 3 个交易日由新浪美股日线补齐（2026-08-31 收盘）。</li>
  <li>窗口：2024-10-05（特朗普当选前 1 个月）~ 2026-08-31，共 476 个交易日。</li>
  <li>统计：Python（pandas / numpy / scipy），Pearson 相关 + t 分布 p 值；60 日滚动相关按日滑动。</li>
  <li>SQ 即 Block, Inc. 现代码 XYZ（2023-06 更名），本报告按用户口径称 Block(SQ)。</li>
</ul>

<footer>
  免责声明：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
</footer>
@@TIP@@
</div>
</body>
</html>"""

# ---------- 替换占位 ----------
html = html.replace("@@MATRIX_ROWS@@", "\n".join(matrix_rows))
html = html.replace("@@PHASE_ROWS@@", phase_rows)
html = html.replace("@@ROLL_ROWS@@", roll_rows)
html = html.replace("@@STAT_ROWS@@", stat_rows)

# ---------- 术语注释 ----------
html = annotate_terms(html)

# ---------- 图表 ----------
charts = """<script>
const D = @@JSJSON@@;
const UP='#c0392b', DN='#1e8449';
const NAV_COLORS = {'SOFI':'#e69f00','XYZ':'#56b4e9','AFRM':'#cc79a7'};
const NAV_NAMES = {'SOFI':'SOFI (SoFi)','XYZ':'XYZ (Block/SQ)','AFRM':'AFRM (Affirm)'};

// 图1：归一化净值
const navDates = D.nav.SOFI.dates;
const navSeries = Object.keys(NAV_COLORS).map(tk=>({
  name: NAV_NAMES[tk], type:'line', data: D.nav[tk].nav, smooth:true,
  symbol:'none', lineStyle:{width:2.5, color:NAV_COLORS[tk]},
  itemStyle:{color:NAV_COLORS[tk]}
}));
echarts.init(document.getElementById('c_nav')).setOption({
  tooltip:{trigger:'axis', formatter:function(ps){let s=ps[0].axisValue+'<br>';ps.forEach(p=>{s+=p.marker+p.seriesName+': <b>'+p.value.toFixed(1)+'</b><br>';});return s;}},
  legend:{top:0, textStyle:{color:'#555'}},
  grid:{left:60,right:20,top:36,bottom:40},
  xAxis:{type:'category',data:navDates,axisLabel:{color:'#666',interval:50,rotate:0,fontSize:10},axisLine:{lineStyle:{color:'#bbb'}}},
  yAxis:{type:'value',scale:true,axisLabel:{color:'#555'},splitLine:{lineStyle:{color:'#e5e9f0'}},axisLine:{show:false}},
  series: navSeries
});

// 图2：60日滚动相关
const rollDates = D.rolling.SOFI_XYZ.dates;
const lineStyles = ['solid','dashed','dotted'];
let ri = 0;
const rollSeries = Object.keys(D.rolling).map(k=>{
  const st = lineStyles[ri++ % 3];
  return {
    name: {'SOFI_XYZ':'SOFI × Block(SQ)','SOFI_AFRM':'SOFI × AFRM','AFRM_XYZ':'AFRM × Block(SQ)'}[k]||k,
    type:'line', data:D.rolling[k].r, smooth:false,
    symbol:'none', lineStyle:{width:2.2, color:D.pair_colors[k], type:st},
    itemStyle:{color:D.pair_colors[k]}
  };
});
echarts.init(document.getElementById('c_roll')).setOption({
  tooltip:{trigger:'axis', valueFormatter:v=>v==null?'—':v.toFixed(3),
    formatter:function(ps){let s=ps[0].axisValue+'<br>';ps.forEach(p=>{s+=p.marker+p.seriesName+': <b>'+p.value.toFixed(3)+'</b><br>';});return s;}},
  legend:{top:0, textStyle:{color:'#555'}},
  grid:{left:60,right:20,top:36,bottom:40},
  xAxis:{type:'category',data:rollDates,axisLabel:{color:'#666',interval:50,rotate:0,fontSize:10},axisLine:{lineStyle:{color:'#bbb'}}},
  yAxis:{type:'value',min:0,max:1,axisLabel:{color:'#555'},splitLine:{lineStyle:{color:'#e5e9f0'}},axisLine:{show:false}},
  series: rollSeries
});
</script>"""
charts = charts.replace("@@JSJSON@@", JSJSON)
html = html.replace("</body>", charts + "</body>")

tip_engine = """<div class="termtip" id="termtip"></div>
<script>
(function(){
  const tip=document.getElementById('termtip');
  let cur=null;
  document.addEventListener('mouseover',e=>{
    const t=e.target.closest('.term');
    if(!t||t===cur)return; cur=t;
    tip.textContent=t.dataset.tip||'';
    tip.style.display='block';
    const r=t.getBoundingClientRect();
    tip.style.left=Math.min(r.left,window.innerWidth-300)+'px';
    tip.style.top=r.bottom+6+'px';
  });
  document.addEventListener('mouseout',e=>{
    if(e.target.closest('.term')){cur=null;tip.style.display='none';}
  });
})();
</script>"""
html = html.replace("@@TIP@@", tip_engine)

out = os.path.join(OUT_DIR, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("SAVED:", out, f"({os.path.getsize(out)/1024:.0f} KB)")
