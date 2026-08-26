# -*- coding: utf-8 -*-
"""构建研报37：KO × 道琼斯 vs XLV × 道琼斯 相关性对比
读取 results/ko_xlv_dji_corr.json
输出 reports/37_ko_xlv_dji相关性/index.html（浅底深字研报风 + ECharts + Okabe-Ito 色弱安全）
红涨绿跌 + 色弱安全；静默写盘：只打印 written 路径与体积。
"""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "37_ko_xlv_dji相关性")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "ko_xlv_dji_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

KO, XLV = D["pairs"][0], D["pairs"][1]
PA = {"KO": KO, "XLV": XLV}
COLOR = {"KO": "#0072B2", "XLV": "#CC79A7"}     # 蓝 / 紫（Okabe-Ito）
LS = {"KO": "solid", "XLV": "dashed"}
NAME = {"KO": "可口可乐 KO", "XLV": "医疗保健 XLV"}
SHORT = {"KO": "KO", "XLV": "XLV"}

SPLIT = KO["split"]


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
        corr_cls = "na"
        rows.append(
            f"<tr{hl}><td class='nowrap'><b>{b['name']}</b></td>"
            f"<td>{b['n']}</td>"
            f"<td class='{cls(b['pearson'])}'>{b['pearson']:.3f}</td>"
            f"<td class='{cls(b['spearman'])}'>{b['spearman']:.3f}</td>"
            f"<td>{b['r2']*100:.1f}%</td>"
            f"<td>{b['beta']:.3f}</td>"
            f"<td>{b['ann_vol_sec']:.1f}/{b['ann_vol_dji']:.1f}</td>"
            f"<td>{b['sec_vol']:.2f}/{b['dji_vol']:.2f}</td>"
            f"<td class='{cls(b['sec_ret_total'])}'>{b['sec_ret_total']:+.1f}%</td>"
            f"<td class='{cls(b['dji_ret_total'])}'>{b['dji_ret_total']:+.1f}%</td>"
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
    <div class="kv"><div class="k">{tag} 异动而道指不动</div>
      <div class="v">{e['sec_only']} <small>天</small></div>
      <div class="muted">道指大幅异动时 {tag} 同步率 <b>{hit(e['hit_rate_sec_given_dji'])}</b></div></div>
    <div class="kv"><div class="k">道指异动而 {tag} 不动</div>
      <div class="v">{e['dji_only']} <small>天</small></div>
      <div class="muted">{tag} 大幅异动时道指同步率 <b>{hit(e['hit_rate_dji_given_sec'])}</b></div></div>
    <div class="kv"><div class="k">同日双方都异动</div>
      <div class="v">{e['both']} <small>天</small></div>
      <div class="muted">共同异动日相关 <b>{corr_txt}</b></div></div>
    <div class="kv"><div class="k">任一标的大幅异动</div>
      <div class="v">{e['either']} <small>天</small></div>
      <div class="muted">2021-08 ~ 2026-08，|日收益| ≥ 3%</div></div>"""


# ---------------- 图表数据 ----------------
# 注意：JSON 中 rolling60/monthly/yearly 的 corr 为百分数（×100，与项目惯例一致），
# 注入 ECharts 折线图时必须 ÷100 还原为 0~1 小数（历史坑：32/37 号曾整线溢出画布）。
# zscore / 价格归一化序列不需要 ÷100。
def build_roll(p):
    pts = [(d["date"], d["corr"] / 100) for d in p["rolling60"] if d["corr"] is not None]
    return {"date": [x[0] for x in pts], "corr": [x[1] for x in pts]}


years_all = sorted({y["year"] for p in [KO, XLV] for y in p["yearly"]})
y_series = {}
for tag in ["KO", "XLV"]:
    m = {y["year"]: y["corr"] / 100 for y in PA[tag]["yearly"]}
    y_series[tag] = [m.get(y) for y in years_all]


def build_monthly(p, limit=36):
    m = p["monthly"]
    m = m[-limit:]
    return {"month": [x["month"] for x in m], "corr": [x["corr"] / 100 for x in m]}


# 归一化价格（交集起点=100）
def build_norm(p):
    d = p["price_recent"]
    return {"date": [x["date"] for x in d],
            "sec": [x["sec"] for x in d],
            "dji": [x["dji"] for x in d]}


# 相对强弱 zscore
def build_rel(p):
    pts = [(d["date"], d["z"]) for d in p["rel_strength"] if d["z"] is not None]
    return {"date": [x[0] for x in pts], "z": [x[1] for x in pts]}


# ---------------- 关键结论内插 ----------------
# 全期 / 分界后 / 2026以来 相关系数
ko_all, ko_after, ko_ytd = KO["blocks"][0], KO["blocks"][2], KO["blocks"][4]
xl_all, xl_after, xl_ytd = XLV["blocks"][0], XLV["blocks"][2], XLV["blocks"][4]

JS = {
    "split": SPLIT,
    "roll": {t: build_roll(PA[t]) for t in ["KO", "XLV"]},
    "years": years_all,
    "yearSeries": y_series,
    "monthly": {t: build_monthly(PA[t]) for t in ["KO", "XLV"]},
    "norm": {t: build_norm(PA[t]) for t in ["KO", "XLV"]},
    "rel": {t: build_rel(PA[t]) for t in ["KO", "XLV"]},
    "blocks": {t: PA[t]["blocks"] for t in ["KO", "XLV"]},
    "extreme": {t: PA[t]["extreme"] for t in ["KO", "XLV"]},
    "fisher": {t: PA[t]["fisher"] for t in ["KO", "XLV"]},
    "meta": D["meta"],
}

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KO vs XLV × 道琼斯 相关性对比报告</title>
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

  <h1>KO vs XLV × 道琼斯 · 谁与大盘联动更紧？</h1>
  <div class="subtitle">可口可乐（KO）与医疗保健 ETF（XLV）对道琼斯工业指数的分阶段联动拆解 · 以 2026-02-01 为结构断裂点 · 交集期 2021-08 ~ 2026-08 · 数据截至 2026-08-25</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">KO × 道琼斯</div>
        <div class="v">0.232 → <span class="na">0.005</span></div>
        <div class="muted">全期 0.232 → 2026-02 后 <b>0.005</b>（几乎归零）<br>2026 以来 <b>−0.048</b>（转负）</div></div>
      <div class="kv"><div class="k">XLV × 道琼斯</div>
        <div class="v">0.443 → <span class="up">0.231</span></div>
        <div class="muted">全期 0.443 → 2026-02 后 <b>0.231</b>（仍显著正相关）<br>2026 以来 <b>0.229</b></div></div>
      <div class="kv"><div class="k">谁更贴道指</div>
        <div class="v">XLV <span class="up">≈2 倍</span></div>
        <div class="muted">全期 XLV 相关（0.443）约为 KO（0.232）的 <b>1.9 倍</b>；<br>2026 分界后 KO 脱钩至 0、XLV 仍 +0.23</div></div>
    </div>
    <div class="concl">
      ① <b>XLV 与道琼斯的日收益相关性（0.443）显著高于 KO（0.232），约为后者的两倍</b>：XLV 作为权重型医疗保健板块 ETF，内含多家道指成分股（UNH/JNJ/AMGN 等）+"防御+红利"被动资金属性，天然与大盘宽基同频；KO 虽是道指成分股，但其日波动高度聚焦于公司自身事件（财报复盘、饮料行业叙事），与大盘噪声关联弱。<br>
      ② <b>2026 年 KO 与道指几乎完全脱钩（0.267 → 0.005），XLV 虽减弱但保持正相关（0.474 → 0.231）</b>：KO 2026 年以来 +31.8% vs 道指 +10.3%，超额 +21.5pp，走出独立行情（防御资金回流 + 自身基本面），大盘涨跌不再解释 KO；XLV 与道指的联动虽从 0.47 降至 0.23（Fisher z=3.08 显著减弱），但并未归零，仍是"广义医疗随大盘"的结构。<br>
      ③ <b>极端日检验同样支持</b>：XLV 在道指大波动日的同步率 40%（KO 仅 30%），KO 自身异动日道指几乎不跟随（仅 13.6%）——KO 的日频波动里公司个性比例更高，XLV 的波动更接近大盘结构。
    </div>
    <div class="src">数据：道琼斯工业指数（腾讯自选股 usDJI，2021-08-25 起）、KO/XLV（Yahoo Finance 日线，复权收盘）。交集取三者共同交易日，2021-08-26 ~ 2026-08-21，约 1252 个交易日。计算：日收益率 Pearson/Spearman 相关、OLS β 与 R²、60 日滚动相关、Fisher z 检验（分界前后差异）。分界点沿用项目惯例 2026-02-01。</div>
  </div>

  <!-- 两组合滚动相关对比 -->
  <div class="card">
    <h2>60 日滚动相关性：XLV 全程在 KO 上方，2026 分化加剧 <span class="tag">动态监测 · 主口径</span></h2>
    <div id="chart_roll_comp" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>KO×道指（蓝，实线）· <span class="legend-dot" style="background:#CC79A7"></span>XLV×道指（紫，虚线）· 橙色竖虚线=2026-02 分界。五年来 XLV 的 60 日相关几乎全程显著高于 KO（大多在 0.3–0.6 vs 0.1–0.4）；<b>2026 年起两条线同时下滑，但 KO 更深——一度跌破 0 至 −0.06，XLV 仍守在 +0.11 上下</b>——KO 已脱离大盘噪声，XLV 只是"松绑"而未"脱钩"。</div>
  </div>

  <!-- 分阶段总表 -->
  <div class="card">
    <h2>分阶段相关性总表 <span class="tag">以 2026-02-01 为界</span></h2>
    <table>
      <tr><th>组合 / 区间</th><th>样本</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(标的→道指)</th><th>年化波动 标/指</th><th>日波动 标/指</th><th>标的涨幅</th><th>道指涨幅</th><th>超额</th></tr>
      __BLOCK_ROWS_KO__
    </table>
    <div class="note"><b>KO</b>：全期 64.0% vs 道指 49.9%，超额 +14.1pp；但超额全部来自 2026 分界后（+12.5pp）。分界后 Pearson 0.005、β 0.008、R²≈0——<b>道指日收益对 KO 的解释力从 7.1% 跌到几乎为零</b>。2026 以来相关转负（−0.048），大盘跌日 KO 偶尔逆势走强（防御资金切换），但幅度不大（|r| 仅 0.05）。</div>
    <table>
      <tr><th>组合 / 区间</th><th>样本</th><th>Pearson r</th><th>Spearman ρ</th><th>R²</th><th>β(标的→道指)</th><th>年化波动 标/指</th><th>日波动 标/指</th><th>标的涨幅</th><th>道指涨幅</th><th>超额</th></tr>
      __BLOCK_ROWS_XLV__
    </table>
    <div class="note"><b>XLV</b>：全期 27.9% vs 道指 49.9%，跑输 −22.0pp（2021-2025 医疗承压）；<b>分界后跑赢 +2.3pp、相关性从 0.47 降至 0.23</b>（Fisher z=3.08，p=0.002 显著减弱但仍显著为正）。XLV 的波动结构（年化 15-17%）与道指更接近，β 0.31-0.52——<b>它本质上仍是一只"随大盘的防御板块"，而 KO 是"随自己的消费个股"</b>。</div>
  </div>

  <!-- 归一化走势 -->
  <div class="sect-title">归一化走势（交集起点 = 100）</div>

  <div class="card">
    <h2>KO vs 道指：2026 年剪刀差，KO 独立走强 <span class="tag">2021-08 起归一化</span></h2>
    <div id="chart_norm_ko" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>KO（蓝）vs <span class="legend-dot" style="background:#8c97a6"></span>道指（灰）。2021-2025 年两者总体同向（KO 2022 抗跌、2023-2024 横盘），<b>2026 年起 KO 陡峭上行、道指震荡，剪刀差扩大至 +20pp 以上</b>——相关性归零的走势侧证据：KO 的上涨不再需要大盘配合。</div>
  </div>

  <div class="card">
    <h2>XLV vs 道指：宽基属性可见，走势大体同向 <span class="tag">2021-08 起归一化</span></h2>
    <div id="chart_norm_xlv" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#CC79A7"></span>XLV（紫）vs <span class="legend-dot" style="background:#8c97a6"></span>道指（灰）。XLV 2022 年随大盘下跌、2023-2024 跑输（医疗板块逆风）、2025 年中起修复，<b>全程与道指方向大体一致、斜率略缓</b>——这是它相关 0.44 的结构来源。它也解释了为何 XLV 相关性是 KO 的近两倍：板块 ETF 的行业内部足够分散，β 更接近 1 的资产。</div>
  </div>

  <!-- 年度相关 -->
  <div class="card">
    <h2>年度相关性：XLV 五年全正，KO 2026 转负 <span class="tag">自然年 Pearson ×100</span></h2>
    <div id="chart_year" class="chart"></div>
    <div class="note"><b>XLV 与道指的年相关 5 年全部为正且都在 0.23 以上</b>（57/56/51/48/34/23），虽然逐年走低（医疗板块 alpha 化），但从未失联；<b>KO 则从 2021 年 0.44 一路衰减至 2026 年 −0.05</b>——KO 的"大盘 beta"5 年内被公司 alpha 完全稀释。历史上看，个股相关天然低于板块 ETF（分散化差异），本组即实证。</div>
  </div>

  <!-- 月度相关 -->
  <div class="card">
    <h2>月度相关性（近 36 个月）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月频视角波动大，但结构清晰：<b>2024 年中之前两条线大体同步摆动（0~+0.7），2025 年起 KO 月相关频繁落至 0 轴以下，XLV 在 0 轴上方的时间明显更多</b>。2026-06 KO 单月相关 −0.59（KO 与大盘当月反向），XLV 仅 −0.09。</div>
  </div>

  <!-- 极端日 -->
  <div class="card">
    <h2>极端日分析：2021-08 以来 |日收益| ≥ 3% 的归属 <span class="tag">不对称联动</span></h2>
    <div class="grid4">
      __EXTREME_KO__
    </div>
    <div class="grid4" style="margin-top:12px">
      __EXTREME_XLV__
    </div>
    <div class="note">解读：KO 自身日波动小（~1.1%），单日 |≥3%| 仅 25 次（其中 22 次道指无同期 3% 波动），多由公司事件驱动——<b>KO 的大波动日大盘平均只有 13.6% 的同步率</b>；XLV 大异动 15 次中 4 次与道指同日，同步率 36.4%，且共同异动日两者相关 0.9996（几乎同涨同跌）。<b>极端日证据与全期一致：XLV 是"跟着大盘走的防御"，KO 是"自己的故事"</b>。</div>
  </div>

  <!-- 相对强弱 -->
  <div class="card">
    <h2>相对强弱（价格比 250 日 zscore）<span class="tag">近 4 年</span></h2>
    <div id="chart_rel" class="chart"></div>
    <div class="note">zscore &gt; 0 表示标的相对道指走强。<b>KO 的 zscore 2026 年飙升至 +2 以上（历史极值，对应 KO 相对道指的超额大涨），XLV 的 zscore 仅小幅回正（0~+1）</b>——KO 的相对强弱是"趋势性背离"，XLV 只是"温和修复"。相对强弱越极端，与大盘的相关越低，这与 2026 年 KO 相关归零互为印证。</div>
  </div>

  <!-- 归因 -->
  <div class="card">
    <h2>为什么 XLV 与道指联动更紧？—— 个股 vs 板块 ETF 的结构差异</h2>
    <div class="grid3">
      <div class="kv"><div class="k">分散化：板块 ETF 天然贴近大盘</div>
        <div class="v" style="font-size:15px;">β 接近市场的资产</div>
        <div class="muted">XLV 内含数百只医疗股加权，行业 beta 平均化后与道指的系统性因子（宏观、利率、风险偏好）重叠度高；KO 是单一标的，日收益 = 大盘 beta（~0.3）+ 大量公司特异波动，公司噪音稀释了与大盘的相关。</div></div>
      <div class="kv"><div class="k">道指成分：两者同为成员但角色不同</div>
        <div class="v" style="font-size:15px;">UNH/JNJ 权重 vs KO 权重</div>
        <div class="muted">道指中医疗权重由 UNH、JNJ、AMGN、MRK 等构成，XLV 与其重仓重叠，天然同涨同跌；KO 虽也是道指成分，但消费权重在道指中占比小，且 KO 自身事件（新品、汇率、回购）主导其日频波动。</div></div>
      <div class="kv"><div class="k">2026 特殊性：KO 脱钩、XLV 松绑</div>
        <div class="v" style="font-size:15px;">alpha 期 vs beta 期</div>
        <div class="muted">2026 年 KO 走出独立行情（相对道指 +21.5pp），防御资金在科技/大盘波动中流入高现金流消费股，相关转负/归零；XLV 2026 年跑赢道指但仅 +0.6pp（2026 以来），没有趋势性 alpha，仍是"随大盘的防御板块"，因此相关只降不脱。</div></div>
    </div>
  </div>

  <!-- 结论 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>回答原始问题：XLV 与道琼斯的相关性更大</b>——全期 Pearson 0.443 vs KO 0.232（约 1.9 倍），Spearman 0.430 vs 0.192（约 2.2 倍），60 日滚动五年内 XLV 几乎全程更高。若用 XLV 或 KO 去"对冲/跟踪道指"，XLV 相关性更高、跟随性更好；KO 现在（2026）几乎不跟大盘。</li>
      <li><b>当前状态（2026）</b>：KO × 道指已脱钩至统计零（0.005）、月度甚至转负；XLV × 道指虽从 0.47 降至 0.23（Fisher z=3.08 显著减弱）但仍为正相关。对冲/暴露判断应按"KO=独立敞口、XLV=低 beta 大盘敞口"处理。</li>
      <li><b>监测信号</b>：若 KO×道指 60 日滚动相关重新回到 +0.2 以上，说明 KO 重回"大盘同步"状态；若 XLV 相关跌破 0.15，说明医疗板块进入独立景气行情（类似 2025 年后制药/器械脱钩的结构）。</li>
      <li><b>局限与口径</b>：① 交集仅 5 年（道指数据源起点限制），分界后样本仅 ~139 个交易日，统计窗口较短；② KO/XLV 为 Yahoo 复权收盘、道指为腾讯自选股收盘价（指数不复权），指数无股息调整不影响收益相关；③ 相关性是统计描述非因果；④ 未核算交易成本。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（腾讯自选股、Yahoo Finance 日线行情）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const D = __DATA_JSON__;
const SPLIT = D.split;
const C = { KO:'#0072B2', XLV:'#CC79A7' };
const LS = { KO:'solid', XLV:'dashed' };
const NAME = { KO:'KO×道指', XLV:'XLV×道指' };
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
  legend: { data: ['KO×道指', 'XLV×道指'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.roll.KO.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '相关性', min: -0.6, max: 0.8 }, axisStyle),
  series: ['KO','XLV'].map(t => ({
    name: NAME[t], type: 'line', data: D.roll[t].corr, showSymbol: false,
    lineStyle: { width: 1.8, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: t === 'KO' ? markLineSplit(D.roll.KO.date) : undefined
  }))
});

// 2) 归一化走势（两张）
function normChart(id, tag, secColor) {
  const n = D.norm[tag];
  if (!n) return;
  echarts.init(document.getElementById(id)).setOption({
    tooltip: tooltipAxis,
    legend: { data: [tag === 'KO' ? 'KO' : 'XLV', '道指'], top: 0 },
    grid: { left: 55, right: 20, top: 34, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: n.date, boundaryGap: false }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '归一化（基准=100）', scale: true }, axisStyle),
    series: [
      { name: tag === 'KO' ? 'KO' : 'XLV', type: 'line', data: n.sec, showSymbol: false, lineStyle: { width: 2, color: secColor }, itemStyle: { color: secColor },
        markLine: markLineSplit(n.date) },
      { name: '道指', type: 'line', data: n.dji, showSymbol: false, lineStyle: { width: 1.8, type: 'dotted', color: '#8c97a6' }, itemStyle: { color: '#8c97a6' } }
    ]
  });
}
normChart('chart_norm_ko', 'KO', '#0072B2');
normChart('chart_norm_xlv', 'XLV', '#CC79A7');

// 3) 年度相关（两线）
echarts.init(document.getElementById('chart_year')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['KO×道指', 'XLV×道指'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.years.map(String) }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '年相关', min: -0.3, max: 0.8 }, axisStyle),
  series: ['KO','XLV'].map(t => ({
    name: NAME[t], type: 'line', data: D.yearSeries[t], showSymbol: true, symbolSize: 6,
    connectNulls: false, lineStyle: { width: 2, type: LS[t], color: C[t] }, itemStyle: { color: C[t] }
  }))
});

// 4) 月度相关（两线）
echarts.init(document.getElementById('chart_monthly')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['KO×道指', 'XLV×道指'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.monthly.KO.month, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '月相关', min: -0.8, max: 0.9 }, axisStyle),
  series: ['KO','XLV'].map(t => ({
    name: NAME[t], type: 'line', data: D.monthly[t].corr, showSymbol: false,
    lineStyle: { width: 1.6, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#8c97a6', type: 'dashed', width: 1 }, data: [{ yAxis: 0 }] }
  }))
});

// 5) 相对强弱 zscore
echarts.init(document.getElementById('chart_rel')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['KO相对道指', 'XLV相对道指'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.rel.KO.date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: 'zscore', scale: true }, axisStyle),
  series: ['KO','XLV'].map(t => ({
    name: t === 'KO' ? 'KO相对道指' : 'XLV相对道指', type: 'line', data: D.rel[t].z, showSymbol: false,
    lineStyle: { width: 1.8, type: LS[t], color: C[t] }, itemStyle: { color: C[t] },
    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#8c97a6', type: 'dashed', width: 1 }, data: [{ yAxis: 0 }] }
  }))
});
</script>
</body>
</html>
"""

# 注入表格与极端日
HTML = HTML.replace("__BLOCK_ROWS_KO__", block_rows(KO))
HTML = HTML.replace("__BLOCK_ROWS_XLV__", block_rows(XLV))
HTML = HTML.replace("__EXTREME_KO__", extreme_grid(KO))
HTML = HTML.replace("__EXTREME_XLV__", extreme_grid(XLV))
HTML = HTML.replace("__DATA_JSON__", json.dumps(JS, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")