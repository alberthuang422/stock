# -*- coding: utf-8 -*-
"""构建 91 号报告：白糖可贸易库存与价格解释力 —— 2026-09-12"""
import json
import os
import re

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "reports", "91_白糖可贸易库存与价格解释力_20260912")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "index.html")

J = json.load(open(os.path.join(BASE, "results", "sugar_tradeable.json"), encoding="utf-8"))
M = pd.read_csv(os.path.join(BASE, "data", "sugar", "sugar_tradeable.csv"))
M = M.rename(columns={M.columns[0]: "MY"}).set_index("MY")
LBL = J["labels"]

# 图1 双口径序列
S = M.loc[1990:].copy()
d1 = [[str(int(y)), round(float(S.loc[y, "w_sur"]), 2), round(float(S.loc[y, "core_sur_own"]), 2)]
      for y in S.index]

# 图2 散点：Δ指标 vs Δlog价格（2000-2026）
S2 = M.loc[2000:].copy()
sc = {}
for k, c in [("w", "w_sur"), ("c", "core_sur_own")]:
    dd = pd.DataFrame({"x": S2[c].diff(), "y": np.log(S2.px).diff()}).dropna()
    sc[k] = [[round(float(a), 3), round(float(b), 4)] for a, b in zip(dd.x, dd.y)]

# 图3 解释力 R² 对比
IND = ["w_sur", "w_stocks", "R1_sur", "R2_sur", "core_sur", "core_sur_own", "core_share", "core_surplus"]
d3 = [[LBL[c], J["diff_full"][c]["R2"], J["diff_2000_2026"][c]["R2"]] for c in IND]

# 图4 出口国库存构成（近 15 年）
piv = pd.read_csv(os.path.join(BASE, "data", "sugar", "raw", "psd", "psd_alldata.csv"), low_memory=False)
piv = piv[piv.Commodity_Code == 612000].copy()
piv["Value"] = pd.to_numeric(piv.Value, errors="coerce")
pv = piv[piv.Attribute_Description == "Ending Stocks"].pivot_table(
    index="Market_Year", columns="Country_Name", values="Value", aggfunc="first")
KEYS = [("Thailand", "泰国"), ("India", "印度"), ("Brazil", "巴西"),
        ("Australia", "澳大利亚"), ("Guatemala", "危地马拉"), ("Mexico", "墨西哥")]
yrs4 = [y for y in range(2011, 2026)]
d4 = []
for en, zh in KEYS:
    d4.append([zh] + [None if pd.isna(pv.loc[y, en]) else round(float(pv.loc[y, en] / 1000), 1) for y in yrs4])
tot = []
for y in yrs4:
    tot.append(round(float(sum(pv.loc[y, e] for e, _ in KEYS if not pd.isna(pv.loc[y, e])) / 1000), 1))
AXY = [str(y) for y in yrs4]

# 表格
rows_diff = ""
for c in IND:
    f, a, b = J["diff_full"][c], J["diff_1960_1999"][c], J["diff_2000_2026"][c]
    star = lambda p: "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))
    best = max(f["R2"], b["R2"])
    hl = (f["R2"] >= best) or (b["R2"] >= best)
    cls = ' style="background:#fff8ee"' if hl else ""
    rows_diff += (f"<tr{cls}><td>{LBL[c]}</td><td class='num'>{f['r']:+.3f}{star(f['p'])}</td>"
                  f"<td class='num'>{f['R2']:.3f}</td><td class='num'>{a['r']:+.2f}</td>"
                  f"<td class='num'>{b['r']:+.2f}{star(b['p'])}</td><td class='num'>{b['R2']:.3f}</td></tr>")

mv_rows = ""
MVN = {"['dw']": "仅 全球库消比(Δ)", "['dc']": "仅 出口国/全球消费(Δ)",
       "['dco']": "仅 出口国/自身消费(Δ)", "['dw', 'dc']": "两者同时",
       "['dw', 'dco']": "两者同时(用自身消费口径)"}
for k, v in J["multivariate_2000_2026"].items():
    co = " ｜ ".join(f"{kk}={vv:+.4f}(t={v['t'][kk]:.2f})" for kk, vv in v["coef"].items())
    mv_rows += f"<tr><td>{MVN.get(k,k)}</td><td class='num'>{v['R2']:.3f}</td><td>{co}</td></tr>"

cs = J["current"]
cur_rows = ""
for c in IND:
    v = cs[c]
    cur_rows += (f"<tr><td>{LBL[c]}</td><td class='num'>{v['value']:,.1f}</td>"
                 f"<td class='num'>{v['pct']:.1f}%</td><td class='num'>{v['median']:,.1f}</td>"
                 f"<td class='num'>{v['min']:,.1f}（{v['min_y']}）～ {v['max']:,.1f}（{v['max_y']}）</td></tr>")

DD = json.dumps({"d1": d1, "sc": sc, "d3": d3, "d4": d4, "tot": tot, "axy": AXY}, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>91 · 白糖可贸易库存与价格解释力 · 2026-09-12</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --oi-green:#009E73;
        --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec; --card:#fff; --bg:#f5f7fa; --ref-bg:#eef2f7;}}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px;}}
  .wrap{{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}}
  .hero{{background:linear-gradient(135deg,#12365e 0%,#1d5c93 100%);color:#fff;border-radius:12px;padding:28px 32px;margin-bottom:20px;}}
  .hero h1{{font-size:23px;margin-bottom:6px;line-height:1.45;}}
  .hero .meta{{font-size:12.5px;opacity:.85;margin-top:4px;}}
  .hero .sub{{margin-top:12px;font-size:14px;opacity:.96;border-top:1px solid rgba(255,255,255,.25);padding-top:10px;}}
  .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}}
  .kcard{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}}
  .kcard .lab{{font-size:12px;color:var(--sub);margin-bottom:3px;}}
  .kcard .val{{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;}}
  .kcard .note{{font-size:12px;color:var(--sub);margin-top:3px;}}
  .red{{color:#b2182b;}} .green{{color:#1a7a3a;}}
  h2{{font-size:19px;margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--oi-blue);}}
  h3{{font-size:16px;color:#12365e;margin:18px 0 8px;}}
  .panel{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:16px;}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;}}
  th{{background:#eef2f7;color:#12365e;padding:6px 7px;text-align:left;border-bottom:2px solid var(--line);font-weight:600;}}
  td{{padding:5px 7px;border-bottom:1px solid var(--line);vertical-align:middle;}}
  tr:last-child td{{border-bottom:none;}}
  .num{{font-variant-numeric:tabular-nums;text-align:right;}}
  th.num{{text-align:right;}}
  .src{{font-size:11px;color:var(--sub);margin-top:7px;line-height:1.5;}}
  .callout{{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:14px 18px;margin:14px 0;font-size:13.5px;}}
  .warn{{background:#fdf2f2;border:1px solid #eccaca;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}}
  .ok{{background:#f0f8f4;border:1px solid #c9e5d6;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}}
  .chart{{width:100%;height:330px;}}
  .footer{{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}}
  code{{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px;}}
  ul{{padding-left:22px;}} li{{margin:4px 0;}}
  @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr);}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>白糖"可贸易库存"实测：它真的比全球总量更能解释糖价吗？</h1>
    <div class="meta">报告编号 91 ｜ 数据源：USDA FAS PSD（2026-09-11 快照）＋ World Bank Pink Sheet 世界糖价（1960M01–2026M08）｜ 2026-09-12</div>
    <div class="sub">结论一句话：<b>
    直觉上"巴西只剩 22 万吨、中国 400 万吨不参与贸易，所以可贸易缓冲比全球总量紧得多"——
    <b>实测部分成立但方向要改</b>：1960–2026 全样本下<b>全球库消比</b>反而更强（R²=0.289）；
    但把窗口收到 <b>2000 年后</b>，<b>出口国库存/自身消费</b>反超（r=−0.51, R²=0.255 vs 全球 0.187），
    且<b>两者同放时全球口径失去全部显著性（t=0.13）</b>——增量信息几乎都在出口国口径里。
    同时证伪两件事：<b>"可出口盈余"这类流量指标完全无效</b>（r=−0.118, p=0.35）；<b>盲目剥离中国/印度有害</b>（2000 年后剥离中印 → r 从 −0.43 崩到 −0.06）。
    </b></div>
  </div>

  <div class="cards">
    <div class="kcard"><div class="lab">最佳单一口径（2000 年后）</div><div class="val">R²=0.255</div>
      <div class="note">出口国库存 ÷ 出口国自身消费 ｜ 全球库消比仅 0.187</div></div>
    <div class="kcard"><div class="lab">出口国库存/自身消费（当前）</div><div class="val">{cs['core_sur_own']['value']:.1f}%</div>
      <div class="note">历史中位 {cs['core_sur_own']['median']:.1f}% ｜ <span class="red">高于中位</span></div></div>
    <div class="kcard"><div class="lab">出口国占全球库存份额</div><div class="val">{cs['core_share']['value']:.1f}%</div>
      <div class="note">历史中位 {cs['core_share']['median']:.1f}% ｜ 2018 峰值 55.0%</div></div>
    <div class="kcard"><div class="lab">"可出口盈余"解释力</div><div class="val green">不显著</div>
      <div class="note">r=−0.118, p=0.35 ｜ 三个窗口全部失效</div></div>
  </div>

  <h2>一、为什么怀疑"全球总量"这个口径</h2>
  <div class="panel">
    <p>USDA PSD 口径下全球期末库存 44.4 Mt，但这笔库存的<b>可动用性差异极大</b>：</p>
    <ul>
      <li><b>中国 402 万吨</b>——基本不出口，是封闭库存，只通过进口需求间接影响国际市场；</li>
      <li><b>印度 651 万吨</b>——受出口配额与禁令约束，可贸易性打折；</li>
      <li><b>泰国 1,345 万吨</b>——真正的出口国结转，可直接进入国际贸易；</li>
      <li><b>巴西 22 万吨</b>——全球最大出口国，但库里几乎是空的（库消比 2.5%）。</li>
    </ul>
    <p>于是很自然的假设是：<b>用"可贸易库存"代替"全球库存"应该更能解释糖价</b>。本报告就是对这个假设做实测——结论是<b>一半成立、一半被证伪</b>。</p>
  </div>

  <h2>二、两种构造路线与两个必须避开的坑</h2>
  <div class="panel">
    <table>
      <tr><th>路线</th><th>构造</th><th>说明</th></tr>
      <tr><td><b>A 剥离法</b></td><td>R1 = 全球 − 中国；R2 = 全球 − 中国 − 印度</td><td>固定国家，序列连续，不引入集合切换噪声</td></tr>
      <tr><td><b>B 出口国法</b></td><td>10 国净出口集合（巴西/泰国/澳大利亚/印度/危地马拉/墨西哥/南非/哥伦比亚/乌克兰/阿根廷）</td>
        <td>覆盖全球净出口：1960 年 17% → 2000 年 60% → <b>2010 年后 91%+</b></td></tr>
    </table>
    <div class="src">集合用<b>净出口</b>（Exports − Imports）筛选，主动排除阿联酋、沙特这类"进口原糖精炼再出口"的再出口国——它们的库存不是真实缓冲。</div>
  </div>
  <div class="warn">
    <b>坑 1 —— 水平相关全是假的。</b>直接对"库存水平"与"价格水平"做相关，会得到 <b>r = +0.42</b> 的<u>正相关</u>（库存越多价格越高），
    完全违反商品常识。原因是两者都有长期上行趋势 → <b>共同趋势造成的伪相关</b>。
    本报告主口径一律改用<b>一阶差分</b>（Δ指标 vs Δlog价格），伪相关随即消失并转为正确的负号。<br>
    <b>坑 2 —— 动态集合会毁掉差分。</b>若每年重选"覆盖率 80%"的国家集合，成员切换会造成跳变
    （实测 2018 年印度被纳入，可贸易库存一夜从 7,891 跳到 26,301 千吨，<b>3.3 倍</b>），
    这种噪声会把真实的差分信号完全淹没。→ 必须用<b>固定集合</b>。
  </div>

  <h2>三、实测结果</h2>
  <div class="panel">
    <div id="c1" class="chart"></div>
    <div class="src">两个口径的历史轨迹（1990 年起）。<b>注意 2018 年是两条线的共同高点</b>——那一年出口国库存/自身消费达 53.2%、占全球库存 55.0%，
    对应糖价 0.28 $/kg 的低位；此后缓冲逐步变薄，价格中枢上移。</div>
  </div>
  <h3>3.1 各口径的解释力（Δ指标 vs Δlog价格）</h3>
  <div class="panel">
    <table>
      <tr><th>口径</th><th class="num">全样本 r</th><th class="num">全样本 R²</th><th class="num">1960–99 r</th><th class="num">2000–26 r</th><th class="num">2000–26 R²</th></tr>
      {rows_diff}
    </table>
    <div class="src">n≈65（年度，1960–2026）。*** p&lt;0.01，** p&lt;0.05，* p&lt;0.10。底色标出该行较优的窗口。</div>
  </div>
  <div class="panel">
    <div id="c3" class="chart"></div>
    <div class="src">R² 对比：全样本（1960–2026）vs 近期（2000–2026）。<b>两个窗口的最优口径不是同一个</b>——这是本报告最重要的细节。</div>
  </div>
  <div class="callout">
    <b>读法：</b>全样本下<b>全球库消比</b>最强（R²=0.289）；但 2000 年后<b>出口国库存/自身消费</b>反超（R²=0.255 vs 0.187），
    <b>出口国占全球库存份额</b>也从 0.083 跳到 0.220。<b>即：越靠近当代，"可贸易"这个维度的信息量越大</b>，与全球化、贸易集中度上升的事实一致。
  </div>

  <h3>3.2 谁含有谁的增量信息？（2000–2026 多元，HAC 标准误）</h3>
  <div class="panel">
    <table>
      <tr><th>回归设定</th><th class="num">R²</th><th>系数（t 值）</th></tr>
      {mv_rows}
    </table>
    <div class="src">⚠️ 两个口径高度共线，因此同时入模后各自的 t 值都会下降（多重共线性），
    <b>要看的是"全球口径的 t 是否塌掉"</b>。实测：同时入模后全球库消比 t 从 −2.59 掉到 <b>0.13</b>（完全不显著），
    而出口国口径仍保留 t=−1.89。<b>结论：全球库消比在出口国口径之外几乎没有独立信息。</b></div>
  </div>

  <h3>3.3 被证伪的两件事</h3>
  <div class="warn">
    <b>① "可出口盈余"（出口国产量 − 消费）完全无效。</b>三个窗口的 r 分别是 −0.118 / −0.15 / −0.15，p=0.35，<b>全不显著</b>。
    它是<b>流量</b>指标，而价格由<b>存量缓冲</b>定价——这条对实务有直接含义：<b>不要用"今年过剩/短缺多少"去做价格判断，要看库存存量</b>。<br>
    <b>② 盲目剥离中国、印度有害。</b>只剥中国：r 从 −0.538 → −0.534（几乎无变化，说明中国库存与全球周期同步，剥了不增加信息）；
    再剥印度：2000 年后 r 从 −0.43 <b>崩到 −0.06</b>（完全失效）。原因见下。
  </div>

  <h2>四、为什么"巴西空了"不等于"可贸易缓冲紧了"</h2>
  <div class="panel">
    <div id="c4" class="chart"></div>
    <div class="src">主要出口国期末库存（百万吨）。泰国、印度、巴西、澳大利亚、危地马拉、墨西哥。</div>
  </div>
  <div class="ok">
    <b>关键修正：泰国接过了巴西的缓冲角色。</b>
    巴西库存确实只剩 <b>22 万吨</b>（库消比 2.5%，几乎零缓冲），但泰国持有 <b>1,345 万吨</b>——
    相当于泰国自身年消费（约 330 万吨）的 <b>4 倍</b>。出口国整体库存/自身消费为 <b>{cs['core_sur_own']['value']:.1f}%（MY2025）</b>，历史中位 {cs['core_sur_own']['median']:.1f}%，<b>并不处于紧张状态</b>。<br>
    同时这也解释了"为什么剥离印度会毁掉解释力"：<b>印度库存是缓冲的重要一部分</b>，而且它的升降与价格是<b>同向</b>关系
    （印度库存高 → 出口能力弱 → 利多；库存低 → 出口放量 → 利空），与"库存高即利空"的直觉相反，
    硬把它从分母里抠掉，反而破坏了信号。
  </div>

  <h3>4.1 当前各口径水平（MY2025，最新完整年度）</h3>
  <div class="panel">
    <table>
      <tr><th>口径</th><th class="num">当前值</th><th class="num">1960 起分位</th><th class="num">历史中位</th><th class="num">历史区间</th></tr>
      {cur_rows}
    </table>
    <div class="src">⚠️ 库存类指标（尤其是"全球库存""出口国库存"）有强长期趋势，<b>分位数本身意义有限</b>，
    应看<b>变化方向</b>：出口国占全球库存份额从 2018 年峰值 55.0% 回落至 {cs['core_share']['value']:.1f}%，
    出口国库存/自身消费从 2018 年 53.2% 回落至 {cs['core_sur_own']['value']:.1f}%——<b>缓冲在变薄，但仍高于历史中位</b>。</div>
  </div>

  <h2>五、结论与使用方式</h2>
  <div class="panel">
    <table>
      <tr><th>问题</th><th>结论</th></tr>
      <tr><td>"可贸易库存"比全球总量更能解释糖价吗？</td>
        <td><b>长期看不是；2000 年后是。</b>全样本全球库消比更强（0.289 vs 0.212）；2000 年后出口国口径反超（0.255 vs 0.187）</td></tr>
      <tr><td>该用哪个口径？</td>
        <td><b>做当代判断 → 出口国库存/自身消费</b>；做长历史回溯 → 全球库消比。两者高度共线，不必都用</td></tr>
      <tr><td>要不要剥离中国/印度？</td>
        <td><b>不要。</b>剥离中国无收益，剥离印度在 2000 年后会毁掉信号</td></tr>
      <tr><td>能不能用"过剩/缺口"判断价格？</td>
        <td><b>不能。</b>流量指标三个窗口全部不显著（p=0.35），价格由存量缓冲定价</td></tr>
      <tr><td>巴西库存见底意味着什么？</td>
        <td>意味着<b>巴西单独</b>没有缓冲，但泰国 1,345 万吨补位，出口国整体并不紧。真正要盯的是<b>泰国库存 + 印度出口政策</b></td></tr>
    </table>
  </div>
  <div class="callout">
    <b>可交易的三条推论：</b>
    ① 盯<b>泰国库存 ÷ 泰国消费</b>与<b>印度库存变化方向</b>，这比盯全球总量更贴近当代价格；
    ② 别把"产需缺口"当价格信号（ISO 的 −20 万吨缺口这类数字对价格的解释力为零）；
    ③ 高库存本身不是空头信号——<b>要看库存涨在哪</b>：涨在出口国手里才有意义（本报告 core_share 口径 R² 从 0.083 升到 0.220 即是证据）。
  </div>

  <div class="footer">
    <b>数据与代码</b>：<code>scripts/sugar_tradeable.py</code>（构造＋差分检验＋HAC 多元）、<code>scripts/build_sugar_tradeable_report.py</code>（本页）。
    结果 <code>results/sugar_tradeable.json</code>、<code>data/sugar/sugar_tradeable.csv</code>。
    数据源与 90 号同：USDA FAS PSD（2026-09-11）＋ World Bank Pink Sheet 2026-09 版。<br>
    <b>免责</b>：样本为年度（n≈65），重叠窗口与多重共线性使精确数值偏乐观，方向可信、点估计不可外推；不构成投资建议。
  </div>
</div>

__SCRIPT__
</body>
</html>
"""

SCRIPT = """
<script>
const DD = __DD__;
const RED='#b2182b', GRN='#1a7a3a', BLU='#0072B2', ORG='#E69F00', VERM='#D55E00', TEAL='#009E73';
const AX={axisLine:{lineStyle:{color:'#c8d3e0'}},axisLabel:{color:'#5a6a7d',fontSize:11},splitLine:{lineStyle:{color:'#eef2f7'}}};

// 图1 双口径序列
(function(){
  const ch=echarts.init(document.getElementById('c1'));
  ch.setOption({
    grid:{left:56,right:60,top:38,bottom:40},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d1.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:10,interval:2}},
    yAxis:[{type:'value',name:'全球库消比 %',...AX},
           {type:'value',name:'出口国/自身消费 %',...AX,splitLine:{show:false}}],
    series:[
      {name:'全球库消比',type:'line',data:DD.d1.map(x=>x[1]),symbol:'none',lineStyle:{color:BLU,width:2}},
      {name:'出口国库存/自身消费',type:'line',yAxisIndex:1,data:DD.d1.map(x=>x[2]),symbol:'none',
        lineStyle:{color:VERM,width:2}}]
  });
})();

// 图3 R² 对比
(function(){
  const ch=echarts.init(document.getElementById('c3'));
  ch.setOption({
    grid:{left:52,right:24,top:38,bottom:76},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d3.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:10,rotate:28}},
    yAxis:{type:'value',name:'R²',...AX},
    series:[
      {name:'全样本 1960-2026',type:'bar',data:DD.d3.map(x=>x[1]),itemStyle:{color:BLU},barWidth:'38%'},
      {name:'近期 2000-2026',type:'bar',data:DD.d3.map(x=>x[2]),itemStyle:{color:ORG},barWidth:'38%'}]
  });
})();

// 图4 出口国库存构成
(function(){
  const ch=echarts.init(document.getElementById('c4'));
  ch.setOption({
    grid:{left:56,right:24,top:38,bottom:40},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.axy,...AX,axisLabel:{color:'#5a6a7d',fontSize:10.5}},
    yAxis:{type:'value',name:'百万吨',...AX},
    series:DD.d4.map((row,i)=>({
      name:row[0],type:'bar',stack:'s',barWidth:'58%',
      itemStyle:{color:[TEAL,VERM,BLU,ORG,GRN,'#8a97a6'][i]},
      data:row.slice(1)}))
  });
})();
</script>
"""

HTML = HTML.replace("__SCRIPT__", SCRIPT.replace("__DD__", DD))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print("wrote", OUT, len(HTML), "bytes")
print("d3", d3)
print("core_sur_own cur", cs['core_sur_own'])
