# -*- coding: utf-8 -*-
"""构建研报 69：UNP × US10Y / QQQ / SOXX / DJI 分阶段相关性
读取 results/unp_multi_corr.json，输出 reports/69_UNP多基准分阶段相关性/index.html
浅底研报风 + ECharts + Okabe-Ito 色弱安全；红涨绿跌；静默写盘。
"""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "69_UNP多基准分阶段相关性")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "unp_multi_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

PA = {p["ref_tag"]: p for p in D["pairs"]}
SPLIT = "2025-07-28"

C_REF = {"US10Y": "#0072B2", "QQQ": "#E69F00", "SOXX": "#009E73", "DJI": "#CC79A7"}
LS_REF = {"US10Y": "solid", "QQQ": "dashed", "SOXX": "dashed", "DJI": "solid"}
SHORT = {"US10Y": "美债10Y", "QQQ": "纳指100", "SOXX": "费半", "DJI": "道指"}


def cls(v):
    if v is None:
        return "na"
    return "up" if v > 0 else "dn"


def block_table(p, title):
    rows = []
    for b in p["blocks"]:
        if b["n"] == 0:
            continue
        hl = " class='hl'" if ("STB受理后" in b["name"] or "公告" in b["name"]) else ""
        sigm = {"sig": "显著", "edge": "边缘", "no": "不显著"}[b["sig"]]
        rows.append(
            f"<tr{hl}><td class='nowrap'><b>{b['name']}</b></td>"
            f"<td>{b['n']}</td>"
            f"<td class='{cls(b['pearson'])}'>{b['pearson']:+.3f}</td>"
            f"<td>{b['p_value']:.4f}</td><td>{sigm}</td>"
            f"<td class='{cls(b['spearman'])}'>{b['spearman']:+.3f}</td>"
            f"<td>{b['r2']*100:.1f}%</td><td>{b['beta']:+.3f}</td>"
            f"<td class='{cls(b['sec_ret_total'])}'>{b['sec_ret_total']:+.1f}%</td>"
            f"<td class='{cls(b['ref_ret_total'])}'>{b['ref_ret_total']:+.1f}%</td>"
            f"<td class='{cls(b['excess_ret'])}'>{b['excess_ret']:+.1f}pp</td></tr>")
    ref_unit = "bp 变动" if p["ref_tag"] == "US10Y" else "价格涨幅"
    header = ("<tr><th>区间</th><th>样本</th><th>Pearson r</th><th>p 值</th><th>显著性</th>"
              "<th>Spearman ρ</th><th>R²</th><th>β</th>"
              f"<th>UNP 涨幅</th><th>基准{ref_unit}</th><th>超额</th></tr>")
    return (f"<div class='sect-title'>{title}</div>"
            f"<table>{header}{''.join(rows)}</table>")


def build_roll(p):
    pts = [(d["date"], d["corr"] / 100) for d in p["rolling60"] if d["corr"] is not None]
    return {"date": [x[0] for x in pts], "corr": [x[1] for x in pts]}


def build_norm(p):
    d = p["price"]
    return {"date": [x["date"] for x in d], "sec": [x["sec"] for x in d], "ref": [x["ref"] for x in d]}


JS = {
    "split1": SPLIT,
    "split2": "2026-05-28",
    "roll": {k: build_roll(PA[k]) for k in ["US10Y", "QQQ", "SOXX", "DJI"]},
    "norm": {k: build_norm(PA[k]) for k in ["QQQ", "SOXX", "DJI"]},
    "yearly": {k: {"years": [y["year"] for y in PA[k]["yearly"]],
                   "corr": [y["corr"] / 100 for y in PA[k]["yearly"]]} for k in ["US10Y", "QQQ", "SOXX", "DJI"]},
    "monthly": {k: {"m": [x["month"] for x in PA[k]["monthly"][-36:]],
                    "corr": [x["corr"] / 100 for x in PA[k]["monthly"][-36:]]} for k in ["QQQ", "SOXX", "DJI", "US10Y"]},
}

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UNP × US10Y/QQQ/SOXX/道指 分阶段相关性</title>
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
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; margin-top: 6px; }
  th, td { padding: 8px 8px; text-align: right; border-bottom: 1px solid var(--line); }
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
  @media (max-width: 720px) { .grid3 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>UNP × US10Y / QQQ / SOXX / 道指 分阶段相关性</h1>
  <div class="subtitle">联合太平洋（UNP）对四大基准的分阶段联动拆解 · 以 2025-07-28（UP-NS 合并公告）与 2026-05-28（STB 受理）为界 · 交集期 2021-08 ~ 2026-09 · 数据截至 2026-09-02/03</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">UNP × 道指（最强联动）</div>
        <div class="v"><span class="up">0.568</span> → <span class="na">0.093</span></div>
        <div class="muted">全期 <b>0.568</b>（β 0.877，四大基准中最高）<br>STB 受理后降至 <b>0.093</b>（不显著）<br>Fisher z=5.02（公告前 vs 受理后，p&lt;0.001）</div></div>
      <div class="kv"><div class="k">UNP × QQQ / SOXX（同步脱钩）</div>
        <div class="v"><span class="up">0.431/0.378</span> → <span class="dn">−0.17/−0.14</span></div>
        <div class="muted">公告前 0.431 / 0.378（均显著）<br>受理后 <b>−0.166 / −0.143</b>（转负，不显著）<br>两项 Fisher 均 p&lt;0.001（结构性变化）</div></div>
      <div class="kv"><div class="k">UNP × US10Y（天然弱）</div>
        <div class="v"><span class="dn">−0.06</span></div>
        <div class="muted">全期 −0.06（弱负，p=0.033 边缘）<br>仅 2022 加息年 r=−0.213 有点像样<br>非利率敏感结构：防守叙事弱于"贴大盘"</div></div>
    </div>
    <div class="concl">
      ① <b>UNP 的"大盘 beta"来自道指而非纳指</b>：全期 ×道指 0.568（β 0.877，道指动 1% UNP 平均跟 0.88%）＞ ×QQQ 0.357 ＞ ×SOXX 0.290；道指上行日 UNP 胜率 70%（中位 +0.52%），下行日胜率仅 31%（中位 −0.57%）——非对称明显。<br>
      ② <b>合并公告是联动结构的断裂点</b>：2025-07-28 公告后，与三大股指相关性全部腰斩以上（道指 0.624→0.398、QQQ 0.431→0.119、SOXX 0.378→0.127）；STB 受理后进一步降至 0.09 / −0.17 / −0.14。三次 Fisher z 检验均显著（p≤0.04）——<b>UNP 已从"贴大盘的蓝筹"切换为"合并事件驱动个股"</b>。<br>
      ③ <b>利率敏感性弱且结构松散</b>：全期 r=−0.06，仅 2022 年（激进加息）r=−0.21 有点像样；10Y 上行 8bp 以上的大波动日 UNP 中位 −0.18%（胜率 44%）、下行大波动日 +0.15%（胜率 56%）——方向符合"利率上行压制高股息/久期型资产"，但强度不足以构成交易信号。<br>
      ④ <b>超额收益集中在合并叙事期</b>：公告以来 UNP +26.1% vs 道指 +19.7%（超额 +6.4pp）、vs QQQ/SOXX 超额 −0.2 / −78pp（科技暴涨背景下）；2026 年 8-26 见顶 310.62 后一周回撤 −6.9%（09-01 单日 −3.34% = 除息 $1.42 + Bernstein 炉边谈 + STB 拉长程序），同期道指 +0.4%、QQQ +0.9%——短期走出独立下跌，但幅度属正常波动区间。
    </div>
    <div class="src">数据：UNP（Yahoo 日线 + 新浪补至 2026-09-03）、DGS10（FRED，2026-09-02）、QQQ/SOXX（Yahoo+新浪）、DJI（新浪 .dji 全历史，2026-08-21 收盘 53,277.01 已经 Bloomberg 口径核实替换本地旧源）。口径：日收益率 Pearson/Spearman（US10Y 为日变动 bp）×100 存储展示 ÷100；p 值 t 近似三档；60 日滚动主口径；Fisher z 检验阶段差异。</div>
  </div>

  <!-- 阶段划分说明 -->
  <div class="card">
    <h2>阶段划分依据（为什么选这两个节点）<span class="tag">重要事件节点</span></h2>
    <ul class="tl">
      <li><b>2025-07-28 · UP-NS 合并协议公告</b>：$85B 全股票+现金交易，$2.5B 反向分手费，承诺不使用 voting trust；7-30 STB 收到意向通知。UNP 的股价驱动从"货运周期+运营比率"切换为"合并套利+监管进度"——正是公告前后相关性结构断裂的机制。</li>
      <li><b>2026-05-28 · STB 受理完整申请</b>：2026-01-16 首次申请被 STB 判为不完整退回，4-30 重新递交，5-28 受理并要求补充信息；12 个月法定审查钟启动，程序表 8-18 公布（merits 截止 2026-11-18，最终决定 2027 年中后）。</li>
      <li><b>辅助节点</b>：2026-07-23 Q2 财报（adj EPS $3.41、OR 59.2% 改善 110bp、国内多式联运连续四季创纪录）；2026-08-31 除息 $1.42（+3% 提息，20 年连续增息）；2026-09-01 Bernstein 炉边谈（Vena 重申 $1.8B 收入协同、关闭不早于 2027Q3/Q4）。</li>
    </ul>
  </div>

  <!-- 60日滚动 -->
  <div class="card">
    <h2>60 日滚动相关性 · 四基准全景 <span class="tag">主口径</span></h2>
    <div id="chart_roll_all" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#CC79A7"></span>×道指（紫实）· <span class="legend-dot" style="background:#E69F00"></span>×纳指100（橙虚）· <span class="legend-dot" style="background:#009E73"></span>×费半（绿虚，色弱可用线型区分）· <span class="legend-dot" style="background:#0072B2"></span>×美债10Y（蓝实）。橙/绿竖虚线 = 2025-07-28 公告 / 2026-05-28 受理。道指线全程领跑且 2021-22 年高达 0.7-0.8；<b>2025 年中后三条股指线收敛到 0-0.3 区间，2026-05 后全部坠至 0 附近或转负</b>——滚动口径与分阶段静态口径互相印证。</div>
  </div>

  <!-- 分阶段总表 -->
  <div class="card">
    <h2>分阶段相关性总表 <span class="tag">p 值三档 · 超额=UNP−基准</span></h2>
    __TABLE_DJI__
    <div class="note"><b>×道指</b>：全期 0.568 显著；公告后 0.398（仍显著但 β 从 0.94 降到 0.68）；受理后 0.093 不显著。超额：公告以来 +6.4pp——道指跑输期 UNP 靠合并叙事撑住。</div>
    __TABLE_QQQ__
    <div class="note"><b>×纳指100</b>：公告前 0.431 显著 → 公告后 0.119 不显著（Fisher p&lt;0.001）→ 受理后 −0.166。<b>这是"科技驱动的市场里 UNP 掉队"的直接证据</b>：2026 以来 QQQ +17.1%、UNP +24.7%（靠合并溢价），但日度联动已死。</div>
    __TABLE_SOXX__
    <div class="note"><b>×费半</b>：结构与 QQQ 同款（0.378→0.127→−0.143）。费半 2026 以来 +60.1%（AI 半导体牛市），UNP 与之几乎完全脱钩（2026 r=0.001）——<b>UNP 不再从科技牛市分到任何日度资金流</b>。</div>
    __TABLE_US10Y__
    <div class="note"><b>×美债10Y</b>：r 为日收益×日变动(bp) 相关。全期 −0.06 弱负；分年度看仅 2022 年 −0.213（激进加息期，10Y 上行日 UNP 中位 −0.20%）；2023 后全部在 ±0.1 内（利率传导钝化）。<b>结论：UNP 不是好的"做空利率"工具，其股息率（1.8%）也不构成利率敏感结构</b>——它更像"贴道指的工业蓝筹"，而非债券代理。</div>
    <div class="note"><b>参数图例</b>：r=日收益线性相关；β=基准动 1% UNP 平均跟随 %（US10Y 的 β 为每 1bp 变动的 UNP 跟随 %）；R²=基准解释 UNP 日波动的比例；超额=区间 UNP 累计涨幅 − 基准累计（US10Y 为收益率水平变化，不构成超额口径，仅列参考）。</div>
  </div>

  <!-- 归一化走势 -->
  <div class="sect-title">归一化走势（2021-08-25 = 100）</div>

  <div class="card">
    <h2>UNP vs 三大股指：合并叙事 vs 科技牛市的分裂 <span class="tag">2021-08 起归一化</span></h2>
    <div id="chart_norm_eq" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#E69F00"></span>UNP（橙）· <span class="legend-dot" style="background:#8c97a6"></span>道指（灰）· <span class="legend-dot" style="background:#0072B2"></span>纳指100（蓝）· <span class="legend-dot" style="background:#009E73"></span>费半（绿）。2021-2024 UNP 平坦（五年横盘，+1.6%），2025-07 公告后开始拉出独立上涨（+26% 段），但同期费半 +129%/纳指 +28%——<b>UNP 的 2025-26 上涨是事件溢价而非板块 beta</b>。</div>
  </div>

  <!-- 年度相关 -->
  <div class="card">
    <h2>年度相关性（四基准）<span class="tag">自然年 Pearson</span></h2>
    <div id="chart_year" class="chart"></div>
    <div class="note">道指线（紫）逐年领先但 2026 年跌至 0.27；QQQ/SOXX 2026 年双双归零；US10Y 仅 2022 年 −0.21 突出。<b>2026 是 UNP "指数联动失效" 最彻底的一年——日度资金流已由合并事件主导</b>。</div>
  </div>

  <!-- 月度相关 -->
  <div class="card">
    <h2>月度相关性（近 36 个月）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月频波动大，但 2026 年起道指线多数月份跌破 0.2，QQQ/SOXX 频繁落至 0 轴下方（2026-07 SOXX 单月 −0.4）——月度口径同样确认脱钩。</div>
  </div>

  <!-- 方向拆解 -->
  <div class="card">
    <h2>方向拆解：UNP 对基准上/下行日的非对称反应 <span class="tag">全期 2021-08 ~ 2026-09</span></h2>
    <table>
      <tr><th>基准</th><th>上行日 n</th><th>UNP 中位</th><th>UNP 胜率</th><th>下行日 n</th><th>UNP 中位</th><th>UNP 胜率</th><th>大波动日定义</th><th>大波动日 UNP 中位</th></tr>
      <tr><td><b>道指</b></td><td>670</td><td class="up">+0.52%</td><td class="up">70.0%</td><td>592</td><td class="dn">−0.57%</td><td class="dn">30.6%</td><td>|日收益|≥2%</td><td>−0.17%（n=46）</td></tr>
      <tr><td><b>纳指100</b></td><td>684</td><td class="up">+0.30%</td><td class="up">60.1%</td><td>578</td><td class="dn">−0.28%</td><td class="dn">41.3%</td><td>|日收益|≥2%</td><td>+0.15%（n=182）</td></tr>
      <tr><td><b>费半</b></td><td>677</td><td class="up">+0.28%</td><td class="up">59.2%</td><td>582</td><td class="dn">−0.29%</td><td class="dn">42.3%</td><td>|日收益|≥2%</td><td>+0.15%（n=437）</td></tr>
      <tr><td><b>美债10Y</b></td><td>612</td><td class="dn">−0.09%</td><td class="dn">48.4%</td><td>575</td><td class="up">+0.15%</td><td class="up">54.3%</td><td>|Δ|≥8bp</td><td>−0.02%（n=237）</td></tr>
    </table>
    <div class="note"><b>读法</b>：道指上行日 UNP 胜率 70% vs 下行日 31%——UNP 的日度命运与道指高度绑定（历史上）；对 10Y 的反应方向正确（收益率下行日 UNP 反而涨）但幅度弱（中位差仅 0.24pp）。<b>注意</b>：方向拆解是全期口径，2025-07 后这些概率全部失效（联动已断），交易上不可直接套用。</div>
  </div>

  <!-- 结论 -->
  <div class="card">
    <h2>结论与监测点</h2>
    <ul class="tl">
      <li><b>回答"UNP 跟谁"：历史上跟道指最紧（0.57/β0.88），跟纳指/费半弱一半，跟利率基本无关（−0.06）。</b>但 2025-07 合并公告后这条规律已失效——当前 UNP 是"事件驱动个股"，指数 beta 处于历史最低区（受理后三条股指线 −0.17~+0.09 全不显著）。</li>
      <li><b>当前位置</b>：09-03 收盘 $289.15，距 08-26 高点 310.62 回撤 −6.9%（09-01 单日 −3.34% = 除息 $1.42 约 −0.46% + Bernstein 炉边谈 + STB 延长程序表的情绪冲击）；2026 以来仍 +24.7%（道指 +11.0%、QQQ +17.1%）。</li>
      <li><b>监测点</b>：① 2026-11-18 STB merits 意见截止 → 2027-05-28 最终简报 → 2027 年中后决定——每个节点都会带来一次"相关性回接/再脱钩"；② 若合并被附加重大条件或否决（触发 $2.5B 分手费），UNP 将快速回到"贴道指工业蓝筹"状态（预期 r 回到 0.4-0.6）；③ 60 日滚动相关若回升至 0.35+，意味着市场开始按"纯铁路资产"重新定价。</li>
      <li><b>局限与口径</b>：① 阶段划分 n=69（受理后）较短，统计功效有限；② 新浪 .dji 已核实（08-21 收盘 53,277.01 双源一致），但 2021-08 之前的道指历史来自新浪，与腾讯旧源存在微小口径差（已备份）；③ 相关性为观察统计非因果；④ UNP 收益率未剔除股息（dividend-adjusted 结论不受影响，因四基准同为价格口径对比）；⑤ 本报告不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（FRED、新浪财经、Yahoo、UP 官网、STB 官网）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。</div>
  </div>

</div>

<script>
const D = __DATA_JSON__;
const C = { US10Y:'#0072B2', QQQ:'#E69F00', SOXX:'#009E73', DJI:'#CC79A7' };
const LS = { US10Y:'solid', QQQ:'dashed', SOXX:'dashed', DJI:'solid' };
const NAME = { US10Y:'×美债10Y', QQQ:'×纳指100', SOXX:'×费半', DJI:'×道指' };
const axisStyle = { axisLine: { lineStyle: { color: '#c9d2de' } }, axisLabel: { color: '#5b6675' },
                    splitLine: { lineStyle: { color: '#eef1f6' } } };
const tooltipAxis = { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec',
                      textStyle: { color: '#1f2733' } };
function markEvents(catData) {
  const out = [];
  [['2025-07-28', '公告'], ['2026-05-28', 'STB受理']].forEach(([dt, lab]) => {
    const idx = catData.findIndex(d => d >= dt);
    if (idx >= 0) out.push({
      silent: true, symbol: 'none',
      label: { formatter: lab, color: '#D55E00', fontSize: 11 },
      lineStyle: { color: '#D55E00', type: 'dashed', width: 1 },
      data: [{ xAxis: idx }] });
  });
  return out;
}
function rollChart(id, keys) {
  echarts.init(document.getElementById(id)).setOption({
    tooltip: tooltipAxis,
    legend: { data: keys.map(k => NAME[k]), top: 0 },
    grid: { left: 55, right: 20, top: 40, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: D.roll[keys[0]].date, boundaryGap: false }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '60日滚动相关', min: -0.4, max: 0.9 }, axisStyle),
    series: keys.map(k => ({
      name: NAME[k], type: 'line', data: D.roll[k].corr, showSymbol: false,
      lineStyle: { width: 1.8, type: LS[k], color: C[k] }, itemStyle: { color: C[k] },
      markLine: k === 'DJI' ? markEvents(D.roll[k].date) : undefined
    }))
  });
}
rollChart('chart_roll_all', ['DJI', 'QQQ', 'SOXX', 'US10Y']);

// 归一化：UNP + 三股指
(function () {
  const first = D.norm['QQQ'];
  echarts.init(document.getElementById('chart_norm_eq')).setOption({
    tooltip: tooltipAxis,
    legend: { data: ['UNP', '道指', '纳指100', '费半'], top: 0 },
    grid: { left: 55, right: 20, top: 34, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: first.date, boundaryGap: false }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '归一化（2021-08-25=100）', scale: true }, axisStyle),
    series: [
      { name: 'UNP', type: 'line', data: first.sec, showSymbol: false,
        lineStyle: { width: 2.4, color: '#E69F00' }, itemStyle: { color: '#E69F00' },
        markLine: markEvents(first.date) },
      { name: '道指', type: 'line', data: D.norm['DJI'].ref, showSymbol: false,
        lineStyle: { width: 1.6, color: '#8c97a6' }, itemStyle: { color: '#8c97a6' } },
      { name: '纳指100', type: 'line', data: D.norm['QQQ'].ref, showSymbol: false,
        lineStyle: { width: 1.6, color: '#0072B2' }, itemStyle: { color: '#0072B2' } },
      { name: '费半', type: 'line', data: D.norm['SOXX'].ref, showSymbol: false,
        lineStyle: { width: 1.6, type: 'dashed', color: '#009E73' }, itemStyle: { color: '#009E73' } }
    ]
  });
})();

// 年度相关（柱状分组）
(function () {
  const years = D.yearly['DJI'].years;
  echarts.init(document.getElementById('chart_year')).setOption({
    tooltip: tooltipAxis,
    legend: { data: years.length ? ['×道指','×纳指100','×费半','×美债10Y'] : [], top: 0 },
    grid: { left: 55, right: 20, top: 40, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: years }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '年度相关', min: -0.4, max: 0.8 }, axisStyle),
    series: ['DJI', 'QQQ', 'SOXX', 'US10Y'].map(k => ({
      name: NAME[k], type: 'bar', barMaxWidth: 18,
      data: D.yearly[k].corr, itemStyle: { color: C[k] }
    }))
  });
})();

// 月度相关（近36个月，折线）
(function () {
  const keys = ['DJI', 'QQQ', 'SOXX', 'US10Y'];
  echarts.init(document.getElementById('chart_monthly')).setOption({
    tooltip: tooltipAxis,
    legend: { data: keys.map(k => NAME[k]), top: 0 },
    grid: { left: 55, right: 20, top: 40, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: D.monthly['DJI'].m.map(s => s.slice(2)) }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '月度相关', min: -0.7, max: 0.9 }, axisStyle),
    series: keys.map(k => ({
      name: NAME[k], type: 'line', data: D.monthly[k].corr, showSymbol: false,
      lineStyle: { width: 1.6, type: LS[k], color: C[k] }, itemStyle: { color: C[k] }
    }))
  });
})();
</script>
</body>
</html>"""

for k, p in PA.items():
    HTML = HTML.replace(f"__TABLE_{k}__", block_table(p, f"UNP × {SHORT[k]}"))

HTML = HTML.replace("__DATA_JSON__", json.dumps(JS, ensure_ascii=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("written:", out, os.path.getsize(out), "bytes")
