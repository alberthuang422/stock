# -*- coding: utf-8 -*-
"""构建研报51：MCD/SBUX × 道琼斯(DJI)/消费精选(XLY) 相关性
读取 results/mcd_sbux_dji_xly_corr.json
输出 reports/51_MCD_SBUX_DJI_XLY_相关性/index.html（浅底深字研报风 + ECharts + Okabe-Ito 色弱安全）
红涨绿跌 + 色弱安全；静默写盘：只打印 written 路径与体积。
"""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "51_MCD_SBUX_DJI_XLY_相关性")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "mcd_sbux_dji_xly_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

# 四组合索引 (sec, ref)
PA = {f"{p['tag']}×{p['ref_tag']}": p for p in D["pairs"]}
MCD_DJI, MCD_XLY = PA["MCD×DJI"], PA["MCD×XLY"]
SBUX_DJI, SBUX_XLY = PA["SBUX×DJI"], PA["SBUX×XLY"]

SPLIT = MCD_DJI["split"]

# Okabe-Ito 色弱安全
C_SEC = {"MCD": "#0072B2", "SBUX": "#E69F00"}       # 蓝 / 橙
C_REF = {"DJI": "#8c97a6", "XLY": "#CC79A7"}        # 灰 / 紫
NAME_SEC = {"MCD": "麦当劳 MCD", "SBUX": "星巴克 SBUX"}
SHORT_SEC = {"MCD": "MCD", "SBUX": "SBUX"}


def cls(v):
    if v is None:
        return "na"
    return "up" if v > 0 else "dn"


def sig_text(b):
    m = {"sig": "显著", "edge": "边缘", "no": "不显著"}
    return m[b["sig"]]


def block_table(comb, title, ptitle_class=""):
    rows = []
    for b in comb["blocks"]:
        if b["n"] == 0:
            continue
        hl = " class='hl'" if "分界后" in b["name"] else ""
        ex = b["excess_ret"]
        rows.append(
            f"<tr{hl}><td class='nowrap'><b>{b['name']}</b></td>"
            f"<td>{b['n']}</td>"
            f"<td class='{cls(b['pearson'])}'>{b['pearson']:.3f}</td>"
            f"<td>{b['p_value']:.4f}</td>"
            f"<td>{sig_text(b)}</td>"
            f"<td class='{cls(b['spearman'])}'>{b['spearman']:.3f}</td>"
            f"<td>{b['r2']*100:.1f}%</td>"
            f"<td>{b['beta']:.3f}</td>"
            f"<td>{b['ann_vol_sec']:.1f}/{b['ann_vol_ref']:.1f}</td>"
            f"<td class='{cls(b['sec_ret_total'])}'>{b['sec_ret_total']:+.1f}%</td>"
            f"<td class='{cls(b['ref_ret_total'])}'>{b['ref_ret_total']:+.1f}%</td>"
            f"<td class='{cls(ex)}'>{ex:+.1f}pp</td></tr>")
    header = ("<tr><th>区间</th><th>样本</th><th>Pearson r</th><th>p 值</th><th>显著性</th>"
              "<th>Spearman ρ</th><th>R²</th><th>β(标的→基准)</th><th>年化波动 标/基</th>"
              "<th>标的涨幅</th><th>基准涨幅</th><th>超额</th></tr>")
    return (f"<div class='sect-title'>{title}</div>"
            f"<table>{header}{''.join(rows)}</table>")


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
    tag = SHORT_SEC[p['tag']]
    rtag = p['ref_tag']
    return f"""
    <div class="kv"><div class="k">{tag} 异动而 {rtag} 不动</div>
      <div class="v">{e['sec_only']} <small>天</small></div>
      <div class="muted">{rtag} 大幅异动时 {tag} 同步率 <b>{hit(e['hit_rate_sec_given_ref'])}</b></div></div>
    <div class="kv"><div class="k">{rtag} 异动而 {tag} 不动</div>
      <div class="v">{e['ref_only']} <small>天</small></div>
      <div class="muted">{tag} 大幅异动时 {rtag} 同步率 <b>{hit(e['hit_rate_ref_given_sec'])}</b></div></div>
    <div class="kv"><div class="k">同日双方都异动</div>
      <div class="v">{e['both']} <small>天</small></div>
      <div class="muted">共同异动日相关 <b>{corr_txt}</b></div></div>
    <div class="kv"><div class="k">任一标的大幅异动</div>
      <div class="v">{e['either']} <small>天</small></div>
      <div class="muted">2021-08 ~ 2026-08，|日收益| ≥ 3%</div></div>"""


# ---------------- 图表数据 ----------------
# JSON 中 rolling60/monthly/yearly 的 corr 为百分数（×100，项目惯例），注入 ECharts 需 ÷100 还原（历史坑）
def build_roll(p):
    pts = [(d["date"], d["corr"] / 100) for d in p["rolling60"] if d["corr"] is not None]
    return {"date": [x[0] for x in pts], "corr": [x[1] for x in pts]}


def build_normalized(p):
    d = p["price_recent"]
    return {"date": [x["date"] for x in d],
            "sec": [x["sec"] for x in d],
            "ref": [x["ref"] for x in d]}


def build_rel(p):
    pts = [(d["date"], d["z"]) for d in p["rel_strength"] if d["z"] is not None]
    return {"date": [x[0] for x in pts], "z": [x[1] for x in pts]}


# 年度相关（四组合）
years_all = sorted({y["year"] for p in D["pairs"] for y in p["yearly"]})
year_series = {}
for key, p in PA.items():
    m = {y["year"]: y["corr"] / 100 for y in p["yearly"]}
    year_series[key] = [m.get(y) for y in years_all]

# 月度相关（近 36 个月）
monthly_series = {}
for key, p in PA.items():
    m = p["monthly"][-36:]
    monthly_series[key] = {"month": [x["month"] for x in m], "corr": [x["corr"] / 100 for x in m]}

# 关键数字注入
n = lambda p: p["period"]["n"] if p["period"]["n"] else 0

JS = {
    "split": SPLIT,
    "roll": {k: build_roll(PA[k]) for k in PA},
    "years": years_all,
    "yearSeries": year_series,
    "monthly": monthly_series,
    "norm": {k: build_normalized(PA[k]) for k in PA},
    "rel": {k: build_rel(PA[k]) for k in PA},
    "meta": D["meta"],
}

# 归一化走势（MCD 两组）
def norm_series(comb, ref):
    """返回 sec 与 ref 的归一化数组"""
    nrm = build_normalized(comb)
    return nrm

# ---------------- 关键结论 ----
b = MCD_DJI["blocks"]
mcd_dji_all, mcd_dji_post = b[0], b[2]
mcd_xly_all, mcd_xly_post = MCD_XLY["blocks"][0], MCD_XLY["blocks"][2]
sbux_dji_all, sbux_dji_post = SBUX_DJI["blocks"][0], SBUX_DJI["blocks"][2]
sbux_xly_all, sbux_xly_post = SBUX_XLY["blocks"][0], SBUX_XLY["blocks"][2]

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCD/SBUX × 道琼斯/XLY 相关性</title>
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
  .legend { font-size: 12px; color: var(--sub); margin: 4px 0 8px; }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>MCD / SBUX × 道琼斯 / XLY 相关性分析</h1>
  <div class="subtitle">麦当劳（MCD）与星巴克（SBUX）对道琼斯工业指数（DJI）与可选消费板块（XLY）的分阶段联动拆解 · 以 2026-02-01 为结构断裂点 · 交集期 2021-08 ~ 2026-08 · 数据截至 2026-08-26</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">MCD × 基准</div>
        <div class="v"><span class="na">0.285</span> / <span class="na">0.329</span></div>
        <div class="muted">×道指 <b>0.285</b> / ×XLY <b>0.329</b>（全期）<br>2026-02 后 ×道指 <b>0.118</b>（不显著）<br>×XLY <b>0.189</b>（边缘）</div></div>
      <div class="kv"><div class="k">SBUX × 基准</div>
        <div class="v"><span class="na">0.294</span> / <span class="up">0.518</span></div>
        <div class="muted">×道指 <b>0.294</b> / ×XLY <b>0.518</b>（全期）<br>2026-02 后 ×道指 <b>0.183</b>（边缘）<br>×XLY <b>0.308</b>（显著）</div></div>
      <div class="kv"><div class="k">谁更贴基准</div>
        <div class="v">SBUX <span class="up">≈1.6×</span></div>
        <div class="muted">×XLY 全期 SBUX（0.518）约为 MCD（0.329）的 <b>1.6 倍</b>；<br>×道指二者接近（0.294 vs 0.285）</div></div>
    </div>
    <div class="concl">
      ① <b>SBUX 与消费板块（XLY）联动显著强于 MCD</b>：全期 Pearson 0.518 vs 0.329、Spearman 0.498 vs 0.323；SBUX 是 XLY 权重成分，β 0.685 vs 0.242，日收益中"消费板块因子"占比明显更高。<br>
      ② <b>与道指的关系两者接近</b>：MCD 0.285 / SBUX 0.294（全期），β 0.375 / 0.696——SBUX 波动大（年化 31.8% vs 17.7%），对道指的 β 高出近一倍。<br>
      ③ <b>2026-02 后全部转弱</b>：MCD×道指降至 0.118（不显著，Fisher z=2.23 p=0.026 显著减弱）、MCD×XLY 0.189（边缘）；SBUX×道指 0.183（边缘）、SBUX×XLY 0.308（仍显著）。标的自身 alpha 主导，指数联动减弱。<br>
      ④ <b>2026 年以来走势分化</b>：MCD 跑输（2026 以来 −11.6% vs 道指 +11.6%），SBUX 大反弹（+25.9% vs 道指 +11.6%），超额 +14.4pp——两者在 2026 年呈现相反的公司个性化行情。
    </div>
    <div class="src">数据：DJI（腾讯自选股 2021-08-25 起）、MCD/SBUX（本地日线收盘，Yahoo 口径复权），XLY（本地日线收盘）。交集取共同交易日，2021-08 ~ 2026-08，约 1254 个交易日。计算：日收益率 Pearson/Spearman 相关、p 值（t 近似）、OLS β、60 日滚动相关、Fisher z 检验（分界前后差异）。分界点沿用项目惯例 2026-02-01。</div>
  </div>

  <!-- 滚动相关对比 -->
  <div class="card">
    <h2>60 日滚动相关性 × 道指 <span class="tag">主口径</span></h2>
    <div id="chart_roll_dji" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>MCD×道指（蓝）· <span class="legend-dot" style="background:#E69F00"></span>SBUX×道指（橙）· 橙色竖虚线=2026-02 分界。MCD 与道指的 60 日相关长期在 0.2–0.5 区间波动，<b>2025 下半年起持续下滑并跌破 0.2，2026 年中低见 −0.1 附近</b>——MCD 独立走弱（大盘涨它跌）；SBUX 波动更大，2024 年一度归零，2025 年末快速回升后 2026 年再回落。</div>
  </div>

  <div class="card">
    <h2>60 日滚动相关性 × XLY <span class="tag">主口径</span></h2>
    <div id="chart_roll_xly" class="chart"></div>
    <div class="note">与消费板块的联动：<b>SBUX（橙）几乎全程高于 MCD（蓝）</b>，峰值可达 0.7+（2023 年中、2024 年末），MCD 峰值仅 ~0.55。2025 年起两条线同时向下走弱，2026 年 SBUX 在 0.2–0.4、MCD 在 0.1–0.3 区间——消费板块内部联动也在 2026 年整体松绑。</div>
  </div>

  <!-- 分阶段总表 - 四个组合 -->
  <div class="card">
    <h2>分阶段相关性总表 <span class="tag">以 2026-02-01 为界 · p 值三档</span></h2>
    __TABLE_MCD_DJI__
    <div class="note"><b>MCD × 道指</b>：全期 r=0.285（显著），β 0.375、R² 8.1%；分界后 r 跌至 0.118（p=0.161，不显著），R² 仅 1.4%——<b>道指日收益对 MCD 的解释力只剩 1.4%</b>。MCD 2026 以来 −11.6% vs 道指 +11.6%，超额 −23.2pp（公司层面：客流/通胀/消费降级压力）。</div>
    __TABLE_MCD_XLY__
    <div class="note"><b>MCD × XLY</b>：全期 r=0.329（显著）但长期历史（1998 起）高达 0.481——近五年联动显著弱化；分界后 0.189（边缘，p=0.023），2026 以来 0.205（显著）。MCD 2026 以来 −12.0% vs XLY −1.0%，超额 −11.0pp。</div>
    __TABLE_SBUX_DJI__
    <div class="note"><b>SBUX × 道指</b>：全期 r=0.294（显著），β 0.696——<b>SBUX 对道指的 β 是 MCD 的近 2 倍（波动是 2.4 倍）</b>；分界后 0.183（边缘，p=0.027）。2026 以来 +25.9% vs 道指 +11.6%，超额 +14.4pp，走出独立反弹。</div>
    __TABLE_SBUX_XLY__
    <div class="note"><b>SBUX × XLY</b>：全期 r=0.518（四组合最高），β 0.685、R² 26.8%；分界后降至 0.308 但仍显著（p=0.0001），2026 以来 0.322——<b>SBUX 仍是最"消费板块"的标的</b>。2026 以来 +29.2% vs XLY −1.0%，超额 +30.2pp，是 XLY 内部强势个股。</div>
    <div class="note"><b>参数图例</b>：r(Pearson)=日收益线性相关，−1~1；p 值=t 分布近似（三档：sig p&lt;0.01 / edge 0.01≤p&lt;0.05 / no p≥0.05）；ρ(Spearman)=秩相关抗极端值；R²=基准解释标的日收益波动的比例；β=基准涨 1% 时标的平均跟涨 %；年化波动=日波动×√252；超额=区间标的累计 − 基准累计（pp）。</div>
  </div>

  <!-- 归一化走势 -->
  <div class="sect-title">归一化走势（交集起点 = 100）</div>

  <div class="card">
    <h2>MCD vs 道指 / XLY：2026 年一路阴跌 <span class="tag">2021-08 起归一化</span></h2>
    <div id="chart_norm_mcd" class="chart"></div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>MCD（蓝）· <span class="legend-dot" style="background:#8c97a6"></span>道指（灰）· <span class="legend-dot" style="background:#CC79A7"></span>XLY（紫）。2021-2025 年 MCD 与两基准大体同向，2026 年起 <b>MCD 逆势单边下行、基准走平或上涨，剪刀差扩大至 −20pp 上下</b>——相关性降低的走势侧证据：MCD 的下跌不再由大盘解释。</div>
  </div>

  <div class="card">
    <h2>SBUX vs 道指 / XLY：2026 年 V 型反转独立上涨 <span class="tag">2021-08 起归一化</span></h2>
    <div id="chart_norm_sbux" class="chart"></div>
    <div class="note">SBUX 2021-2024 年持续跑输（股价自高点几乎腰斩），2026 年起 <b>V 型反转，反弹幅度远超两基准，相对 XLY 的超额扩大到 +30pp 以上</b>——高波动（年化 32%）+ 强公司 alpha 组合。</div>
  </div>

  <!-- 年度相关 -->
  <div class="card">
    <h2>年度相关性（四组合）<span class="tag">自然年 Pearson ×100</span></h2>
    <div id="chart_year" class="chart"></div>
    <div class="note"><b>SBUX×XLY（橙实）几乎每年都高于 MCD×XLY（蓝实）</b>，2022 年高达 0.73（消费板块同涨同跌）；<b>MCD 与两个基准的年相关呈逐年下降趋势</b>（2021 年 0.49/0.51 → 2026 年 0.12/0.20）——MCD 的"大盘 beta"5 年被公司 alpha 稀释；SBUX 年相关波动大，与个股事件（中国复苏、激进股东、换帅）周期相关。</div>
  </div>

  <!-- 月度相关 -->
  <div class="card">
    <h2>月度相关性（近 36 个月）<span class="tag">月频</span></h2>
    <div id="chart_monthly" class="chart-sm"></div>
    <div class="note">月频高波动，但结构清晰：<b>SBUX×XLY 多数月份在 0 轴以上、2024 年末一度冲到 0.8+</b>；MCD 两条线 2025 年起频繁落至 0 轴以下，2026-06 MCD×道指单月 −0.5、MCD×XLY −0.3——<b>MCD 与大盘/板块在 2026 年多个月份反向</b>。</div>
  </div>

  <!-- 极端日 -->
  <div class="card">
    <h2>极端日分析：2021-08 以来 |日收益| ≥ 3% 的归属 <span class="tag">不对称联动</span></h2>
    <div class="grid4">
      __EXTREME_MCD_DJI__
    </div>
    <div class="grid4" style="margin-top:12px">
      __EXTREME_MCD_XLY__
    </div>
    <div class="grid4" style="margin-top:12px">
      __EXTREME_SBUX_DJI__
    </div>
    <div class="grid4" style="margin-top:12px">
      __EXTREME_SBUX_XLY__
    </div>
    <div class="note">解读：<b>SBUX 自身极端日远多于 MCD</b>（约 104 vs 22 次），与其高波动一致；SBUX 与 XLY 共同异动日 30 天、相关 0.95（同涨同跌），与道指的共同异动日仅 6 天——<b>SBUX 波动属于"消费板块内部事件"，而非大盘事件</b>；MCD 极端日少（22 次），与任一基准的共同异动日都很少（1-4 天），公司事件独立性最高。</div>
  </div>

  <!-- 相对强弱 -->
  <div class="card">
    <h2>相对强弱（价格比 250 日 zscore）<span class="tag">近 4 年</span></h2>
    <div id="chart_rel" class="chart"></div>
    <div class="note">zscore &gt; 0 表示标的相对 XLY 走强。<b>MCD 的 zscore 2026 年跌至历史极值 −2 以下，SBUX 从深度负值快速翻正到 +2</b>——MCD 相对消费板块的趋势性走弱 vs SBUX 的相对强势，与二者 2026 年走势（MCD −11.6%、SBUX +29.2%）互为印证。</div>
  </div>

  <!-- 结论 -->
  <div class="card">
    <h2>结论与使用提示</h2>
    <ul class="tl">
      <li><b>回答原始问题：MCD/SBUX 与道指相关性相近（0.285/0.294），与 XLY 相关性 SBUX 显著更高（0.518 vs 0.329）</b>。若用两标的表达"消费板块敞口"，SBUX 是更好的消费 beta（跟 XLY 更紧、β 更大）；若表达"大盘敞口"，两者相关性相近但 SBUX 波动（β 0.696）是 MCD 的两倍。</li>
      <li><b>2026 现状：MCD 与两个基准相关性接近归零（0.12-0.21），SBUX 与 XLY 保住 0.31 显著正相关</b>。MCD 正陷入公司独立负面叙事（客流、消费降级），与大盘脱钩；SBUX 复苏反弹但仍跟随消费板块节奏。</li>
      <li><b>监测信号</b>：若 MCD×道指 60 日滚动相关回到 +0.25 以上、MCD 相对 XLY zscore 回正，说明 MCD 重回"随大盘"状态；若 SBUX×XLY 跌破 0.25，说明星巴克进入纯公司 alpha 阶段。</li>
      <li><b>局限与口径</b>：① 交集仅 5 年（道指数据源起点限制），分界后样本仅 ~140 个交易日，统计窗口较短；② 相关性是统计描述非因果；③ XLY 为板块 ETF 收盘价、DJI 为指数收盘（不复权，指数无股息）；④ 未核算交易成本。本报告为观察性统计，不构成投资建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（腾讯自选股、本地日线行情）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const D = __DATA_JSON__;
const SPLIT = D.split;
const C = { 'MCD×DJI':'#0072B2', 'SBUX×DJI':'#E69F00', 'MCD×XLY':'#56B4E9', 'SBUX×XLY':'#D55E00' };
const LS = { 'MCD×DJI':'solid', 'SBUX×DJI':'solid', 'MCD×XLY':'dashed', 'SBUX×XLY':'dashed' };
const NAME = { 'MCD×DJI':'MCD×道指', 'SBUX×DJI':'SBUX×道指', 'MCD×XLY':'MCD×XLY', 'SBUX×XLY':'SBUX×XLY' };
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
function rollChart(id, keys) {
  echarts.init(document.getElementById(id)).setOption({
    tooltip: tooltipAxis,
    legend: { data: keys.map(k => NAME[k]), top: 0 },
    grid: { left: 55, right: 20, top: 40, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: D.roll[keys[0]].date, boundaryGap: false }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '相关性', min: -0.6, max: 0.9 }, axisStyle),
    series: keys.map(k => ({
      name: NAME[k], type: 'line', data: D.roll[k].corr, showSymbol: false,
      lineStyle: { width: 1.8, type: LS[k], color: C[k] }, itemStyle: { color: C[k] },
      markLine: k.endsWith('DJI') ? markLineSplit(D.roll[k].date) : undefined
    }))
  });
}
rollChart('chart_roll_dji', ['MCD×DJI', 'SBUX×DJI']);
rollChart('chart_roll_xly', ['MCD×XLY', 'SBUX×XLY']);

// 归一化走势
function normChart(id, keys) {
  const first = D.norm[keys[0]];
  echarts.init(document.getElementById(id)).setOption({
    tooltip: tooltipAxis,
    legend: { data: keys.map(k => k.split('×')[0] === 'MCD' ? (k.endsWith('DJI') ? 'MCD' : 'MCD') : (k.endsWith('DJI') ? 'SBUX' : 'SBUX')), top: 0 },
    grid: { left: 55, right: 20, top: 34, bottom: 40 },
    xAxis: Object.assign({ type: 'category', data: first.date, boundaryGap: false }, axisStyle),
    yAxis: Object.assign({ type: 'value', name: '归一化（基准=100）', scale: true }, axisStyle),
    series: [
      { name: keys[0].split('×')[0], type: 'line', data: first.sec, showSymbol: false,
        lineStyle: { width: 2, color: keys[0].split('×')[0] === 'MCD' ? '#0072B2' : '#E69F00' },
        itemStyle: { color: keys[0].split('×')[0] === 'MCD' ? '#0072B2' : '#E69F00' },
        markLine: markLineSplit(first.date) },
      { name: '道指', type: 'line', data: D.norm[keys[0]].ref, showSymbol: false,
        lineStyle: { width: 1.8, type: 'dotted', color: '#8c97a6' }, itemStyle: { color: '#8c97a6' } },
      { name: 'XLY', type: 'line', data: D.norm[keys[1]].ref, showSymbol: false,
        lineStyle: { width: 1.6, type: 'dashed', color: '#CC79A7' }, itemStyle: { color: '#CC79A7' } }
    ]
  });
}
normChart('chart_norm_mcd', ['MCD×DJI', 'MCD×XLY']);
normChart('chart_norm_sbux', ['SBUX×DJI', 'SBUX×XLY']);

// 年度相关（四组合）
echarts.init(document.getElementById('chart_year')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['MCD×道指', 'SBUX×道指', 'MCD×XLY', 'SBUX×XLY'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.years.map(String) }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '年相关', min: -0.3, max: 0.9 }, axisStyle),
  series: ['MCD×DJI','SBUX×DJI','MCD×XLY','SBUX×XLY'].map(k => ({
    name: NAME[k], type: 'line', data: D.yearSeries[k], showSymbol: true, symbolSize: 6,
    connectNulls: false, lineStyle: { width: 2, type: LS[k], color: C[k] }, itemStyle: { color: C[k] }
  }))
});

// 月度相关（四组合）
const mkeys = ['MCD×DJI','SBUX×DJI','MCD×XLY','SBUX×XLY'];
echarts.init(document.getElementById('chart_monthly')).setOption({
  tooltip: tooltipAxis,
  legend: { data: mkeys.map(k => NAME[k]), top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.monthly[mkeys[0]].month, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: '月相关', min: -0.8, max: 0.9 }, axisStyle),
  series: mkeys.map(k => ({
    name: NAME[k], type: 'line', data: D.monthly[k].corr, showSymbol: false,
    lineStyle: { width: 1.5, type: LS[k], color: C[k] }, itemStyle: { color: C[k] },
    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#8c97a6', type: 'dashed', width: 1 }, data: [{ yAxis: 0 }] }
  }))
});

// 相对强弱 zscore
const rkeys = ['MCD×XLY', 'SBUX×XLY'];
echarts.init(document.getElementById('chart_rel')).setOption({
  tooltip: tooltipAxis,
  legend: { data: ['MCD相对XLY', 'SBUX相对XLY'], top: 0 },
  grid: { left: 55, right: 20, top: 40, bottom: 40 },
  xAxis: Object.assign({ type: 'category', data: D.rel[rkeys[0]].date, boundaryGap: false }, axisStyle),
  yAxis: Object.assign({ type: 'value', name: 'zscore', scale: true }, axisStyle),
  series: [
    { name: 'MCD相对XLY', type: 'line', data: D.rel['MCD×XLY'].z, showSymbol: false,
      lineStyle: { width: 1.8, type: 'solid', color: '#0072B2' }, itemStyle: { color: '#0072B2' },
      markLine: { silent: true, symbol: 'none', lineStyle: { color: '#8c97a6', type: 'dashed', width: 1 }, data: [{ yAxis: 0 }] } },
    { name: 'SBUX相对XLY', type: 'line', data: D.rel['SBUX×XLY'].z, showSymbol: false,
      lineStyle: { width: 1.8, type: 'solid', color: '#E69F00' }, itemStyle: { color: '#E69F00' } }
  ]
});
</script>
</body>
</html>
"""

# 注入表格与极端日
HTML = HTML.replace("__TABLE_MCD_DJI__", block_table(MCD_DJI, "MCD × 道指"))
HTML = HTML.replace("__TABLE_MCD_XLY__", block_table(MCD_XLY, "MCD × XLY"))
HTML = HTML.replace("__TABLE_SBUX_DJI__", block_table(SBUX_DJI, "SBUX × 道指"))
HTML = HTML.replace("__TABLE_SBUX_XLY__", block_table(SBUX_XLY, "SBUX × XLY"))
HTML = HTML.replace("__EXTREME_MCD_DJI__", extreme_grid(MCD_DJI))
HTML = HTML.replace("__EXTREME_MCD_XLY__", extreme_grid(MCD_XLY))
HTML = HTML.replace("__EXTREME_SBUX_DJI__", extreme_grid(SBUX_DJI))
HTML = HTML.replace("__EXTREME_SBUX_XLY__", extreme_grid(SBUX_XLY))
HTML = HTML.replace("__DATA_JSON__", json.dumps(JS, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")