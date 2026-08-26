# -*- coding: utf-8 -*-
"""构建研报38：CSCO × 纳指(QQQ) / 道指(DJI) 相关性对比
读取 results/csco_index_corr.json
输出 reports/38_思科纳指道指相关性/index.html（浅底深字研报风 + ECharts + Okabe-Ito 色弱安全）
红涨绿跌 + 色弱安全；静默写盘：只打印 written 路径与体积。
"""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "38_思科纳指道指相关性")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "csco_index_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

QQQ, DJI = D["pairs"][0], D["pairs"][1]
PA = {"QQQ": QQQ, "DJI": DJI}
COLOR = {"QQQ": "#0072B2", "DJI": "#E69F00"}     # 蓝 / 橙（Okabe-Ito）
LS = {"QQQ": "solid", "DJI": "dashed"}
NAME = {"QQQ": "CSCO×纳指100(QQQ)", "DJI": "CSCO×道指(DJI)"}
SHORT = {"QQQ": "纳指", "DJI": "道指"}

SPLIT = QQQ["split"]


def cls(v):
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
            f"<td>{b['ann_vol_sec']:.1f}/{b['ann_vol_idx']:.1f}</td>"
            f"<td>{b['sec_vol']:.2f}/{b['idx_vol']:.2f}</td>"
            f"<td class='{cls(b['sec_ret_total'])}'>{b['sec_ret_total']:+.1f}%</td>"
            f"<td class='{cls(b['idx_ret_total'])}'>{b['idx_ret_total']:+.1f}%</td>"
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
    tag = SHORT[p['tag']]
    return f"""
    <div class="kv"><div class="k">{tag} 大波动而 CSCO 不动</div>
      <div class="v">{e['idx_only']} <small>天</small></div>
      <div class="muted">CSCO 大幅异动时 {tag} 同步率 <b>{hit(e['hit_rate_idx_given_sec'])}</b></div></div>
    <div class="kv"><div class="k">CSCO 大波动而 {tag} 不动</div>
      <div class="v">{e['sec_only']} <small>天</small></div>
      <div class="muted">{tag} 大幅异动时 CSCO 同步率 <b>{hit(e['hit_rate_sec_given_idx'])}</b></div></div>
    <div class="kv"><div class="k">同日双方都异动</div>
      <div class="v">{e['both']} <small>天</small></div>
      <div class="muted">共同异动日相关 <b>{corr_txt}</b></div></div>
    <div class="kv"><div class="k">任一标的大幅异动</div>
      <div class="v">{e['either']} <small>天</small></div>
      <div class="muted">{e['start']} ~ {e['end']}，|日收益| ≥ 3%</div></div>"""


# ---------------- 图表数据 ----------------
# 注意：JSON 中 rolling60/monthly/yearly 的 corr 为百分数（×100），
# 注入 ECharts 时必须 ÷100 还原为 0~1 小数（历史坑 32/37 号）。
def build_roll(p):
    pts = [(d["date"], d["corr"] / 100) for d in p["rolling60"] if d["corr"] is not None]
    return {"date": [x[0] for x in pts], "corr": [x[1] for x in pts]}


years_all = sorted({y["year"] for p in [QQQ, DJI] for y in p["yearly"]})
y_series = {}
for tag in ["QQQ", "DJI"]:
    m = {y["year"]: y["corr"] / 100 for y in PA[tag]["yearly"]}
    y_series[tag] = [m.get(y) for y in years_all]


def build_monthly(p, limit=36):
    m = p["monthly"]
    m = m[-limit:]
    return {"month": [x["month"] for x in m], "corr": [x["corr"] / 100 for x in m]}


def build_norm(p):
    d = p["price_recent"]
    return {"date": [x["date"] for x in d],
            "sec": [x["sec"] for x in d],
            "idx": [x["idx"] for x in d]}


def build_rel(p):
    pts = [(d["date"], d["z"]) for d in p["rel_strength"] if d["z"] is not None]
    return {"date": [x[0] for x in pts], "z": [x[1] for x in pts]}


# ---------------- 关键结论数值 ----------------
q_all, q_pre, q_after, q_ytd = QQQ["blocks"][0], QQQ["blocks"][1], QQQ["blocks"][2], QQQ["blocks"][4]
d_all, d_pre, d_after, d_ytd = DJI["blocks"][0], DJI["blocks"][1], DJI["blocks"][2], DJI["blocks"][4]
fq = QQQ["fisher"]; fd = DJI["fisher"]
fq_txt = f"Fisher z={fq['z']}（p={fq['p_value']:.4f}）显著" if fq and fq["sig"] else "Fisher z 不显著"
fd_txt = f"Fisher z={fd['z']}（p={fd['p_value']:.4f}）不显著" if fd and not fd["sig"] else (f"Fisher z={fd['z']}（p={fd['p_value']:.4f}）显著" if fd else "样本不足")

# 2026 CSCO 大事件（≥5%）
big_2026 = [ev for ev in QQQ["big_events"] if ev["date"] >= "2026-01-01"]
big_rows = "\n".join(
    f"<tr><td class='nowrap'>{ev['date']}</td>"
    f"<td class='{cls(ev['ret'])}'>{ev['ret']:+.1f}%</td>"
    f"<td class='{cls(ev['idx'])}'>{ev['idx']:+.1f}%</td>"
    f"<td class='{cls(ev['ret']-ev['idx'])}'>{ev['ret']-ev['idx']:+.1f}pp</td></tr>"
    for ev in big_2026)

JS = {
    "split": SPLIT,
    "roll": {t: build_roll(PA[t]) for t in ["QQQ", "DJI"]},
    "years": years_all,
    "yearSeries": y_series,
    "monthly": {t: build_monthly(PA[t]) for t in ["QQQ", "DJI"]},
    "norm": {t: build_norm(PA[t]) for t in ["QQQ", "DJI"]},
    "rel": {t: build_rel(PA[t]) for t in ["QQQ", "DJI"]},
    "blocks": {t: PA[t]["blocks"] for t in ["QQQ", "DJI"]},
    "extreme": {t: PA[t]["extreme"] for t in ["QQQ", "DJI"]},
    "fisher": {t: PA[t]["fisher"] for t in ["QQQ", "DJI"]},
    "meta": D["meta"],
}

# 核心结论卡片数值
kv1_qqq = f"0.{int(q_all['pearson']*1000) if q_all['pearson']*1000>=100 else q_all['pearson']:.3f}".replace("0.728", "0.728")
kv1 = f"<div class='v'>{q_all['pearson']:.3f} → <span class='na'>{q_after['pearson']:.3f}</span></div>"
kv2 = f"<div class='v'>{d_all['pearson']:.3f} → <span class='up'>{d_after['pearson']:.3f}</span></div>"

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSCO × 纳指 / 道指 相关性对比报告</title>
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

  <h1>CSCO × 纳指 / 道指 · 老牌科技股的两条联动线</h1>
  <div class="subtitle">思科（CSCO）对纳指100（QQQ 代理）与道琼斯工业指数（DJI）的分阶段联动拆解 · 以 2026-02-01 为结构断裂点 · CSCO×QQQ 交集 1999-03 ~ 2026-08（27 年）· CSCO×DJI 交集 2021-08 ~ 2026-08 · 数据截至 2026-08-25</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">CSCO × 纳指100(QQQ)</div>
        <div class="v">0.728 → <span class="na">0.406</span></div>
        <div class="muted">27 年全期 0.728（β≈0.98）<br>2026-02 后断崖降至 <b>0.406</b>（<b>__FQ_TXT__</b>）</div></div>
      <div class="kv"><div class="k">CSCO × 道琼斯(DJI)</div>
        <div class="v">0.365 → <span class="up">0.295</span></div>
        <div class="muted">5 年全期 0.365，分界后 0.295<br>（<b>__FD_TXT__</b>）</div></div>
      <div class="kv"><div class="k">谁更贴 CSCO</div>
        <div class="v">纳指 <span class="up">≈2 倍</span></div>
        <div class="muted">全期 QQQ 相关（0.728）约为 DJI（0.365）的 <b>2 倍</b>；<br>CSCO 是纳指血统科技股，与道指仅"泛蓝筹"弱联动</div></div>
    </div>
    <div class="concl">
      ① <b>CSCO 前半生是"纯粹纳指股"：1999-2026 年与纳指100 日收益相关高达 0.72、β≈0.98</b>——几乎 1:1 跟随纳指的互联网时代标志性权证（2000 年曾为全球市值第一）；而它与道指的 5 年相关仅 0.37（约纳指的半数），因为道指 30 只成分股池里科技权重低、CSCO 只是其中一只边缘成分。<br>
      ② <b>2026 年发生结构性脱钩：CSCO×纳指相关从 0.735 断崖降至 0.406（Fisher z=5.9，p&lt;0.001 显著），CSCO×道指仅从 0.393 降至 0.295（不显著）</b>。财报脉冲（2026-02-12 −12.3%、2026-05-14 +13.4%、2026-08-13 −8.4%，当日纳指仅 ±1~2%）把个股波动从大盘噪声中"撕"出来——CSCO 的大波动全靠财报事件，指数零跟随（35 号报告已证）。<br>
      ③ <b>2026 年 CSCO 相对两大指数均有显著超额</b>：相对纳指 +29.7pp、相对道指 +33.7pp（分界后）、2025-09 以来相对纳指 +37.6pp——AI 网络/安全叙事的估值修复 + 大盘科技分化（纳指权重集中在七巨头，CSCO 不在其列）共同贡献。个股 alpha 期 = 与大盘相关性最低的时期。
    </div>
    <div class="src">数据：CSCO/QQQ（Yahoo Finance 日线，复权收盘）；道琼斯工业指数（腾讯自选股 usDJI 收盘）。两组合独立交集：CSCO×QQQ 1999-03-11 ~ 2026-08-21（6905 个交易日），CSCO×DJI 2021-08-26 ~ 2026-08-24（1253 个交易日）。计算：日收益 Pearson/Spearman 相关、OLS β 与 R²、60 日滚动相关、Fisher z 检验（分界前后差异）。分界点沿用项目惯例 2026-02-01。</div>
  </div>

  <!-- 双组合滚动相关（主口径） -->
  <div class="card">
    <h2>60 日滚动相关性：27 年高水位，2026 骤然下探 <span class="tag">动态监测 · 主口径</span></h2>
    <div id="chart_roll_comp" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>CSCO×纳指（蓝，实线）· <span class="legend-dot" style="background:#E69F00"></span>CSCO×道指（橙，虚线）· 橙色竖虚线=2026-02 分界。27 年里 CSCO×纳指的 60 日滚动相关大多维持在 0.5-0.8 高水位（科网泡沫、2008、2015、2022 均有回落但回升），<b>2026-02 后跌至 0.3-0.4 区间，处于 27 年历史低位</b>；CSCO×道指 5 年全程在 0.2-0.6 之间摆动、2026 年进一步降至 0.3 附近——两条联动线同步松绑，个股 alpha 占主导。</div>
  </div>

  <!-- 分阶段总表 -->
  <div class="card">
    <h2>分阶段相关性总表 <span class="tag">以 2026-02-01 为界</span></h2>
    <table>
      <tr><th>组合 / 区间</th><th>样本</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(CSCO→指数)</th><th>年化波动 标/指</th><th>日波动 标/指</th><th>CSCO 涨幅</th><th>指数涨幅</th><th>超额</th></tr>
      __BLOCK_ROWS_QQQ__
    </table>
    <div class="note"><b>CSCO × 纳指</b>：27 年全期相关 0.728、R²=53%——纳指日收益能解释 CSCO 过半波动。分界前 β≈0.985（基本 1:1），<b>分界后 β 降至 0.758、R² 从 54% 跌至 16%</b>：2026 年以来 CSCO 与纳指方向虽大体一致，但个股自身事件（财报、AI 叙事）驱动的波动占比大增。超额：全期 −969pp（即 1999 年至今 CSCO 严重跑输纳指——2000 年泡沫顶 80 美元至今约 110 美元 vs 纳指 27 年 16 倍）；但<b>分界后 +23.8pp、2025-09 以来 +37.6pp、2026 以来 +29.7pp——本轮首次阶段性跑赢</b>。</div>
    <table>
      <tr><th>组合 / 区间</th><th>样本</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(CSCO→指数)</th><th>年化波动 标/指</th><th>日波动 标/指</th><th>CSCO 涨幅</th><th>指数涨幅</th><th>超额</th></tr>
      __BLOCK_ROWS_DJI__
    </table>
    <div class="note"><b>CSCO × 道指</b>：5 年相关稳定在 0.3-0.4 的"泛蓝筹弱联动"（分界前 0.393 → 分界后 0.295，Fisher z=1.23、p=0.22 不显著）。全期 CSCO 跑赢道指 +34.9pp，其中 2026 年贡献最大。β 分界后升至 0.961 仅是统计噪音（2026 年道指日波动极低 0.6%，CSCO 财报脉冲把斜率拉高）。<b>对道指,CSCO 从未是"大盘股"——它更多是"纳指里的科技票 + 自身事件驱动"</b>。</div>
  </div>

  <!-- 归一化走势 -->
  <div class="sect-title">归一化走势（交集起点 = 100）</div>

  <div class="card">
    <h2>CSCO vs 纳指（1999-03 起）：27 年剪刀差，2026 首次相对走强 <span class="tag">27 年全景</span></h2>
    <div id="chart_norm_qqq" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>CSCO（蓝）vs <span class="legend-dot" style="background:#8c97a6"></span>纳指（灰，对数缩放更完整但此处为线性）。1999-2002 CSCO 从泡沫顶暴跌 −80%+，此后 20 年总体跑输纳指（纳指权重转向苹果/微软/英伟达等），<b>直到 2026 年 CSCO 才出现近 27 年罕见的相对走强段</b>——这正是 2026 分界后相关脱钩的走势侧印证。</div>
  </div>

  <div class="card">
    <h2>CSCO vs 道指（2021-08 起）：大体同向的弱联动 <span class="tag">5 年交集</span></h2>
    <div id="chart_norm_dji" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#E69F00"></span>CSCO（橙）vs <span class="legend-dot" style="background:#8c97a6"></span>道指（灰）。2021-2025 两者方向大体一致（2022 同跌、2023-2024 同涨，CSCO 略弱），<b>2026 年 CSCO 斜率明显变陡、相对道指拉升约 +30pp</b>——弱联动结构下的一次个股强势期。</div>
  </div>

  <!-- 年度相关 -->
  <div class="card">
    <h2>年度相关性：纳指线 27 年全正（含弱化年份）、道指线 5 年稳定 <span class="tag">自然年 Pearson</span></h2>
    <div id="chart_year" class="chart"></div>
    <div class="note">CSCO×纳指的年相关自 1999 年逐年代际下行（0.8+ → 0.5-0.7），但 26 年全部保持正相关、且从未跌破 0.4（2026 年已跌至 0.41，处历史低区）；<b>CSCO×道指 5 年分别为 ~0.45/0.36/0.31/0.38/0.24（2026）</b>——两条线的年相关在 2026 年同步触底，个股 alpha 集中释放的年份，与大盘的联系最弱。</div>
  </div>

  <!-- 月度相关 -->
  <div class="card">
    <h2>月度相关性（近 36 个月）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月频视角两组相关都呈宽幅摆动。2026 年以来：<b>2026-02 财报暴跌月 CSCO×纳指单月相关 −0.46（方向相悖）</b>、2026-05 财报大涨月仅 +0.06、2026-08 −0.03——财报月相关往往被个股脉冲砸到 0 附近甚至转负；非财报月（如 2026-03/04/06/07）回到 +0.3-0.6。<b>月度证据与 35 号报告一致：CSCO 的"大盘联动"只在财报窗口外成立</b>。</div>
  </div>

  <!-- 极端日与大事件 -->
  <div class="card">
    <h2>极端日分析：谁的大波动里藏着谁？<span class="tag">|日收益| ≥ 3%</span></h2>
    <div class="grid4">
      __EXTREME_QQQ__
    </div>
    <div class="grid4" style="margin-top:12px">
      __EXTREME_DJI__
    </div>
    <div class="note">解读：<b>CSCO 与纳指的共同异动日相关 0.93（同涨同跌），但 CSCO 单独异动 829 天 vs 纳指单独异动 512 天</b>——CSCO 的公司个性事件远多于大盘系统事件；CSCO 大波动日纳指平均 30.0% 同步，纳指大波动日 CSCO 同步 40.9%（更贴近大盘方向）。<b>对道指更极端：CSCO 单独异动 63 天 vs 道指单独异动仅 10 天，共同异动只有 2 天（相关 −1.0，样本太少无意义）</b>——道指的波动几乎解释不了 CSCO，CSCO 的日常波动里没有多少"道指因子"。</div>
  </div>

  <!-- 2026 大事件表 -->
  <div class="card">
    <h2>2026 年 CSCO 大波动清单（单日 |±5%|，纳指同期对照）<span class="tag">财报脉冲</span></h2>
    <table>
      <tr><th>日期</th><th>CSCO</th><th>纳指(QQQ)</th><th>超额(pp)</th></tr>
      __BIG2026_ROWS__
    </table>
    <div class="note">2026 年 CSCO 全部 ≥5% 的大波动（共 __NBIG__ 次）均发生在 <b>财报日或其前后（2026-02-12 Q2 财报、2026-05-14 Q3 财报、2026-08-13 Q4 财报），纳指同期仅 ±0.5~3.4%</b>——个股事件完全主导单日波动。这与 31 号（CSCO×PANW/CRWD）和 19 号（CSCO×BUG）报告的结论一致：<b>CSCO 的技术面/主题相关性已让位于财报驱动的脉冲行情</b>。</div>
  </div>

  <!-- 相对强弱 -->
  <div class="card">
    <h2>相对强弱（价格比 250 日 zscore）<span class="tag">CSCO 相对指数</span></h2>
    <div id="chart_rel" class="chart"></div>
    <div class="note">zscore &gt; 0 表示 CSCO 相对指数走强。<b>2026 年 CSCO 相对纳指的 zscore 冲破 +2（历史级强），相对道指亦升至 +1.5 附近</b>——两条线的相对强弱同步进入极值区，正好对应相关性的历史低位。<b>相对强弱越极端 → 与大盘相关越低</b>，这再次验证：2026 的 CSCO 是"自己的故事"（AI 网络景气 + 财报超预期），而非"纳指/道指的跟班"。</div>
  </div>

  <!-- 归因 -->
  <div class="card">
    <h2>为什么 CSCO 与纳指强、与道指弱？—— 三重结构解释</h2>
    <div class="grid3">
      <div class="kv"><div class="k">纳指血统：β≈1 的科技权重股</div>
        <div class="v" style="font-size:15px;">1999-2026 β≈0.98</div>
        <div class="muted">CSCO 是 1990s 互联网泡沫的旗帜股，曾占纳指权重超 4%、全球市值第一；长期与纳指同属科技成长/利率敏感因子，日收益相关 0.73、β≈0.98（几乎 1:1）。道指 30 只成分以金融/工业/消费为主，科技仅微软/苹果/英伟达等少数，CSCO 在其中只是"凑数成分"。</div></div>
      <div class="kv"><div class="k">财报驱动：公司事件的"个性噪声"</div>
        <div class="v" style="font-size:15px;">2026 三次大波动全在财报</div>
        <div class="muted">2026-02-12 −12.3%、05-14 +13.4%、08-13 −8.4% 全部是财报日脉冲，指数零跟随。这类"个性波动"会将与大盘的相关性显著稀释——个股财报事件越多、越强烈，与指数的相关越低。CSCO 独特的财报频率/幅度（美国大型科技股中偏高的单次波动）使其脱钩更明显。</div></div>
      <div class="kv"><div class="k">2026 特别背景：AI 叙事重定价 + 纳指七巨头虹吸</div>
        <div class="v" style="font-size:15px;">相对纳指 +29.7pp</div>
        <div class="muted">2026 年 AI 网络设备/安全硬件需求重估（AI 数据中心网络升级受益股），CSCO 走出独立行情；同时纳指权重被七巨头（NVDA/MSFT/AMZN 等）进一步虹吸，CSCO 不在其列，因此纳指上涨时 CSCO 不再"到场"。个股 alpha 期 = 与大盘相关最低的时期（同理见 32 号 KO 脱钩 0.005）。</div></div>
    </div>
  </div>

  <!-- 结论 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>回答原始问题：CSCO 与纳指的相关性远大于道指</b>——全期 Pearson 0.728 vs 0.365（约 2 倍），Spearman 0.684 vs 0.398，β 0.982 vs 0.699。用 CSCO 表达"科技/纳指敞口"比"道指敞口"有效得多；用 CSCO 对冲道指几乎不成立。</li>
      <li><b>当前状态（2026）</b>：CSCO×纳指已从 0.735 断崖脱钩至 0.406（Fisher z=5.9 显著），CSCO×道指降至 0.295 但不显著；同时 CSCO 相对两指均有 +30pp 级超额。当前 CSCO ≈ "财报事件驱动 + 弱科技 beta"的独立标的，大盘 β 敞口已大幅收缩。</li>
      <li><b>监测信号</b>：若 CSCO×纳指 60 日滚动相关重回 +0.5 以上，说明 CSCO 重新"回到纳指阵营"（AI 叙事退潮、回归大盘同步）；若年报期（2026-09-16 前后）再出现 ±8% 级财报脉冲而纳指不动，则脱钩结构进一步固化。若想博"纳指β+安全边际"，当前 CSCO 相关低更适合作为分散项而非纯 β 工具。</li>
      <li><b>局限与口径</b>：① CSCO×QQQ 交集 27 年，但分界后仅 ~140 个交易日；CSCO×DJI 仅 5 年（道指数据源起点限制）；② QQQ 为 1999-03 上市后的纳指100 代理（非全纳指指数）；③ 相关性是统计描述非因果，财报日/政策事件会瞬时扭曲单月相关；④ 未核算交易成本与股息再投资细节。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance、腾讯自选股日线行情）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const D = __DATA_JSON__;
const SPLIT = D.split;
const C = { QQQ:'#0072B2', DJI:'#E69F00' };
const LS = { QQQ:'solid', DJI:'dashed' };
const NAME = { QQQ:'CSCO×纳指100(QQQ)', DJI:'CSCO×道指(DJI)' };
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

// 1) 双组合 60 日滚动相关对比
echarts.init(document.getElementById('chart_roll_comp')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['CSCO×纳指100(QQQ)', 'CSCO×道指(DJI)'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.roll.QQQ.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: -0.3, max: 0.9 }, axisStyle),
  series: ['QQQ','DJI'].map(t => ({
    name: NAME[t], type: 'line', data: D.roll[t].corr, showSymbol: false,
    lineStyle: { width: 1.8, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: t === 'QQQ' ? markLineSplit(D.roll.QQQ.date) : undefined
  }))
});

// 2) 归一化走势（两张）
function normChart(id, tag, secColor) {
  const n = D.norm[tag];
  if (!n) return;
  echarts.init(document.getElementById(id)).setOption({
    tooltip: tooltipAxis,
    legend: { data: ['CSCO', tag === 'QQQ' ? '纳指(QQQ)' : '道指(DJI)'], top: 0 },
    grid: { left: 55, right: 20, top: 34, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: n.date, boundaryGap: false }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '归一化（基准=100）', scale: true }, axisStyle),
    series: [
      { name: 'CSCO', type: 'line', data: n.sec, showSymbol: false, lineStyle: { width: 2, color: secColor }, itemStyle: { color: secColor },
        markLine: markLineSplit(n.date) },
      { name: tag === 'QQQ' ? '纳指(QQQ)' : '道指(DJI)', type: 'line', data: n.idx, showSymbol: false, lineStyle: { width: 1.8, type: 'dotted', color: '#8c97a6' }, itemStyle: { color: '#8c97a6' } }
    ]
  });
}
normChart('chart_norm_qqq', 'QQQ', '#0072B2');
normChart('chart_norm_dji', 'DJI', '#E69F00');

// 3) 年度相关（两线）
echarts.init(document.getElementById('chart_year')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['CSCO×纳指100(QQQ)', 'CSCO×道指(DJI)'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.years.map(String) }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '年相关', min: 0, max: 0.9 }, axisStyle),
  series: ['QQQ','DJI'].map(t => ({
    name: NAME[t], type: 'line', data: D.yearSeries[t], showSymbol: true, symbolSize: 6,
    connectNulls: false, lineStyle: { width: 2, type: LS[t], color: C[t] }, itemStyle: { color: C[t] }
  }))
});

// 4) 月度相关（两线）
echarts.init(document.getElementById('chart_monthly')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['CSCO×纳指100(QQQ)', 'CSCO×道指(DJI)'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.monthly.QQQ.month, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '月相关', min: -0.8, max: 1 }, axisStyle),
  series: ['QQQ','DJI'].map(t => ({
    name: NAME[t], type: 'line', data: D.monthly[t].corr, showSymbol: false,
    lineStyle: { width: 1.6, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#8c97a6', type: 'dashed', width: 1 }, data: [{ yAxis: 0 }] }
  }))
});

// 5) 相对强弱 zscore
echarts.init(document.getElementById('chart_rel')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['CSCO相对纳指', 'CSCO相对道指'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.rel.QQQ.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: 'zscore', scale: true }, axisStyle),
  series: ['QQQ','DJI'].map(t => ({
    name: t === 'QQQ' ? 'CSCO相对纳指' : 'CSCO相对道指', type: 'line', data: D.rel[t].z, showSymbol: false,
    lineStyle: { width: 1.8, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#8c97a6', type: 'dashed', width: 1 }, data: [{ yAxis: 0 }] }
  }))
});
</script>
</body>
</html>
"""

# 注入
HTML = HTML.replace("__BLOCK_ROWS_QQQ__", block_rows(QQQ))
HTML = HTML.replace("__BLOCK_ROWS_DJI__", block_rows(DJI))
HTML = HTML.replace("__EXTREME_QQQ__", extreme_grid(QQQ))
HTML = HTML.replace("__EXTREME_DJI__", extreme_grid(DJI))
HTML = HTML.replace("__BIG2026_ROWS__", big_rows)
HTML = HTML.replace("__NBIG__", str(len(big_2026)))
HTML = HTML.replace("__FQ_TXT__", fq_txt)
HTML = HTML.replace("__FD_TXT__", fd_txt)
HTML = HTML.replace("__DATA_JSON__", json.dumps(JS, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")