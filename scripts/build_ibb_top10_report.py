#!/usr/bin/env python3
"""生成 IBB 前十大成分股对照分析报告（浅底深字研报风, ECharts）。
读 results/ibb_top10_corr.json, 输出 reports/ibb_top10_report.html。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "ibb_top10_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

h = D["holdings"]
SPLIT = D["split"]
D715 = D["d715"]

def g(x, k, default="—"):
    if x is None or x.get(k) is None:
        return default
    v = x[k]
    if isinstance(v, float):
        return round(v, 4)
    return v

# 表格行
rows = []
for it in h:
    tk, name, w = it["ticker"], it["name"], it["weight"]
    pre, post = it.get("pre"), it.get("post")
    d715 = it.get("d715_strong")
    ytd_pre, ytd = it.get("ytd_pre"), it.get("ytd")
    post_ex = (post["y_ret"] - post["x_ret"]) if post else None
    pre_ex = pre["excess"] if pre else None
    ytd_pre_ex = ytd_pre["excess"] if ytd_pre else None
    ytd_ex = ytd["excess"] if ytd else None
    rows.append({
        "tk": tk, "name": name, "w": w,
        "n": it["n_total"], "start": it["start"],
        "r_all": g(it.get("all"), "pearson"), "r_pre": g(pre, "pearson"), "r_post": g(post, "pearson"),
        "beta_post": g(post, "beta"), "resid_post": g(post, "resid_vol"),
        "x_post": g(post, "x_ret"), "y_post": g(post, "y_ret"),
        "post_ex": round(post_ex, 1) if post_ex is not None else None,
        "pre_ex": round(pre_ex, 1) if pre_ex is not None else None,
        "ytd_pre_ex": round(ytd_pre_ex, 1) if ytd_pre_ex is not None else None,
        "ytd_ex": round(ytd_ex, 1) if ytd_ex is not None else None,
        "strong_post": g(it.get("after_strong"), "pct"),
        "strong_d715": g(d715, "pct"),
        "seesaw": g(it.get("seesaw_after"), "pct"),
        "fisher_p": g(it.get("fisher"), "p"),
    })

# 按权重排序
rows.sort(key=lambda r: r["w"], reverse=True)

# 排序数据：分界后超额
ex_sorted = sorted([r for r in rows if r["post_ex"] is not None], key=lambda r: r["post_ex"])
ex_names = [f"{r['tk']} {r['name'][:8]}" for r in ex_sorted]
ex_vals = [r["post_ex"] for r in ex_sorted]
ex_colors = ["#c0392b" if v > 0 else "#1e8449" for v in ex_vals]

# 2026 年内分界前 vs 分界后超额对比（按分界后超额排序）
ex_cmp_sorted = sorted([r for r in rows if r["post_ex"] is not None], key=lambda r: r["post_ex"])
cmp_names = [f"{r['tk']}" for r in ex_cmp_sorted]
cmp_ytd_pre = [r["ytd_pre_ex"] if r["ytd_pre_ex"] is not None else 0 for r in ex_cmp_sorted]
cmp_post = [r["post_ex"] if r["post_ex"] is not None else 0 for r in ex_cmp_sorted]
cmp_ytd = [r["ytd_ex"] if r["ytd_ex"] is not None else 0 for r in ex_cmp_sorted]

# 相关性变化 (分界前 vs 分界后)
rel_names = [r["tk"] for r in rows]
rel_pre = [r["r_pre"] if isinstance(r["r_pre"], (int, float)) else None for r in rows]
rel_post = [r["r_post"] if isinstance(r["r_post"], (int, float)) else None for r in rows]

# 跷跷板
ss_names = [r["tk"] for r in rows]
ss_vals = [r["seesaw"] if isinstance(r["seesaw"], (int, float)) else 0 for r in rows]

# 7/15以来跑赢
d715_names = [r["tk"] for r in rows]
d715_vals = [r["strong_d715"] if isinstance(r["strong_d715"], (int, float)) else 0 for r in rows]

data_js = {
    "ex_names": ex_names, "ex_vals": ex_vals, "ex_colors": ex_colors,
    "cmp_names": cmp_names, "cmp_ytd_pre": cmp_ytd_pre, "cmp_post": cmp_post, "cmp_ytd": cmp_ytd,
    "rel_names": rel_names, "rel_pre": rel_pre, "rel_post": rel_post,
    "ss_names": ss_names, "ss_vals": ss_vals,
    "d715_names": d715_names, "d715_vals": d715_vals,
    "split": SPLIT, "d715": D715,
}
data_json = json.dumps(data_js, ensure_ascii=False)

# 表格 HTML
trs = []
for r in rows:
    ex_cls = "up" if (r["post_ex"] or 0) > 0 else "down"
    ex_txt = f'{r["post_ex"]:+.1f}pp' if r["post_ex"] is not None else "—"
    pre_cls = "up" if (r["pre_ex"] or 0) > 0 else "down"
    pre_txt = f'{r["pre_ex"]:+.1f}pp' if r["pre_ex"] is not None else "—"
    yp_cls = "up" if (r["ytd_pre_ex"] or 0) > 0 else "down"
    yp_txt = f'{r["ytd_pre_ex"]:+.1f}pp' if r["ytd_pre_ex"] is not None else "—"
    ytd_cls = "up" if (r["ytd_ex"] or 0) > 0 else "down"
    ytd_txt = f'{r["ytd_ex"]:+.1f}pp' if r["ytd_ex"] is not None else "—"
    short_note = " <span style='color:#b9770e;font-size:11px'>短样本</span>" if r["n"] < 2000 else ""
    trs.append(f"""<tr>
      <td><b>{r['tk']}</b> {r['name']}{short_note}</td>
      <td>{r['w']:.1f}%</td>
      <td>{r['n']}</td>
      <td>{r['start']}</td>
      <td>{r['r_all']}</td>
      <td>{r['r_pre']}</td>
      <td>{r['r_post']}</td>
      <td>{r['beta_post']}</td>
      <td>{r['resid_post']}</td>
      <td>{r['y_post']}</td>
      <td class="{pre_cls}">{pre_txt}</td>
      <td class="{ex_cls}">{ex_txt}</td>
      <td class="{yp_cls}">{yp_txt}</td>
      <td class="{ytd_cls}">{ytd_txt}</td>
      <td>{r['strong_post']}</td>
      <td>{r['strong_d715']}</td>
      <td>{r['seesaw']}</td>
    </tr>""")
table_html = "".join(trs)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IBB 前十大成分股对照分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root {{ --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#ffffff;
          --red:#c0392b; --green:#1e8449; --blue:#2e5f9e; --amber:#b9770e; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; }}
  h1 {{ font-size: 26px; letter-spacing: .5px; margin-bottom: 4px; }}
  .subtitle {{ color: var(--sub); font-size: 13px; margin-bottom: 22px; }}
  .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(20,30,50,.05); }}
  .card h2 {{ font-size: 17px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
  .card h2::before {{ content: ""; width: 4px; height: 16px; background: var(--blue); border-radius: 2px; }}
  .grid3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 4px; }}
  .kv {{ background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }}
  .kv .k {{ font-size: 12px; color: var(--sub); }}
  .kv .v {{ font-size: 20px; font-weight: 700; margin-top: 2px; }}
  .kv .v small {{ font-size: 12px; font-weight: 400; color: var(--sub); }}
  .up {{ color: var(--red); }} .down {{ color: var(--green); }}
  .tag {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; margin-top: 6px; }}
  th, td {{ padding: 7px 8px; text-align: right; border-bottom: 1px solid var(--line); white-space: nowrap; }}
  th {{ background: #f1f4f9; font-weight: 600; }}
  th:first-child, td:first-child {{ text-align: left; }}
  .note {{ font-size: 12px; color: var(--sub); margin-top: 10px; }}
  .chart {{ width: 100%; height: 360px; }}
  .concl {{ border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }}
  .disclaimer {{ font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }}
  .src {{ font-size: 11.5px; color: var(--sub); margin-top: 8px; }}
  .hl {{ background: #fdf6e9; padding: 1px 5px; border-radius: 4px; font-weight: 600; }}
  .scroll {{ overflow-x: auto; }}
  @media (max-width: 720px) {{ .grid3 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="wrap">

  <h1>IBB 前十大成分股对照分析报告</h1>
  <div class="subtitle">iShares 生物科技 ETF（IBB）vs 前十大持仓 · 分阶段对比（{SPLIT} 为界）· 数据截至 2026-08-14</div>

  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">前十大合计权重</div><div class="v">~45% <small>238-252 只持仓</small></div></div>
      <div class="kv"><div class="k">分界后超额分布</div><div class="v"><span class="up">+95.8pp</span> ~ <span class="down">−46.4pp</span></div></div>
      <div class="kv"><div class="k">分界后相关性区间</div><div class="v">0.32 ~ 0.66 <small>Pearson</small></div></div>
    </div>
    <div class="concl">
      ① <b>内部结构剧烈分化</b>：分界后相对 IBB，涨幅从 <span class="up">RVMD +95.8pp</span>、<span class="up">ILMN +21.4pp</span>、<span class="up">NTRA +20.3pp</span> 到 <span class="down">GILD −17.0pp</span>、<span class="down">ARGX −12.0pp</span>、<span class="down">ALNY −46.4pp</span>——同样一只 ETF，成分股半年表现横跨 140pp。<br>
      ② <b>大市值权重股相对平庸</b>：权重最大的 AMGN/VRTX/GILD/REGN（合计 ~28.6%）分界后对 IBB 超额为 −6.7 ~ +6.6pp，整体拖累指数；真正的 alpha 来自中小市值（RVMD/NTRA/ILMN）。<br>
      ③ <b>个股化脱钩加剧</b>：分界后相关性显著下降的有 ALNY（0.55→0.32）、ILMN（0.60→0.32）、BIIB（0.55→0.40）、AMGN（0.65→0.55）——这些股票在走独立行情；而 VRTX（→0.66）、NTRA（→0.52）、ARGX（→0.55）反而更贴板块。<br>
      ④ <b>跷跷板结构</b>：ALNY 37%、ILMN 36%、GILD 34% 最高（个股事件驱动强）；AMGN 21.5%、RVMD 22% 最低（独立强势型）。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价）；权重为 2026-08 公开披露口径（Morningstar/iShares 等，需以官方最新披露为准）；计算：日收益率 Pearson 相关、OLS β、残差波动、跑赢天数占比、跷跷板占比。RVMD（2020-02 上市）、ARGX（2017-05）、NTRA（2015-07）样本较短。</div>
  </div>

  <div class="card">
    <h2>分阶段相关性全景表 <span class="tag">以 {SPLIT} 为界</span></h2>
    <div class="scroll">
    <table>
      <tr><th>成分股</th><th>权重</th><th>样本</th><th>起始</th><th>全期 r</th><th>分界前 r</th><th>分界后 r</th><th>β 分界后</th><th>残差 分界后</th><th>分界后涨幅</th><th>分界前超额</th><th>分界后超额</th><th>2026分界前超额</th><th>2026以来超额</th><th>跑赢 分界后</th><th>跑赢 7/15后</th><th>跷跷板</th></tr>
      {table_html}
    </table>
    </div>
    <div class="note">说明：超额 = 成分股涨幅 − IBB 涨幅；分界前 = 各股上市日 ~ 2026-01-30，分界后 = 2026-02-01 ~ 2026-08-14（IBB +13.85%），2026分界前 = 2026-01-01 ~ 2026-01-30（IBB +2.03%），2026以来 = 2026-01-01 ~ 2026-08-14（IBB +17.31%）。跑赢占比 = 该股日收益 &gt; IBB 的天数比例；跷跷板 = 反向波动天数占比（分界后）。短样本标的（RVMD/ARGX/NTRA）对比时注意。</div>
  </div>

  <div class="card">
    <h2>2026 年内三阶段超额：分界前 vs 分界后 vs 全年 <span class="tag">超额 = 股票 − IBB</span></h2>
    <div id="chart_cmp" class="chart"></div>
    <div class="note">蓝=2026 分界前（1 月，20 个交易日）超额，红=分界后（2-8 月）超额，灰=2026 全年累计超额。注意 2026 分界前仅有 20 个交易日、且 IBB 只涨 +2.03%，单月超额易被个别事件放大（如 GILD 1 月 +16.7%）；全年的"总账"看灰柱。</div>
  </div>

  <div class="card">
    <h2>分界后相对 IBB 超额：冰火两重天 <span class="tag">2026-02 以来</span></h2>
    <div id="chart_ex" class="chart"></div>
    <div class="note">红=跑赢板块，绿=跑输板块。RVMD（+95.8pp）为极端值（2020 年上市的早期管线公司，2026 年暴涨）；剔除 RVMD 后，ILMN +21.4pp、NTRA +20.3pp 领先，ALNY −46.4pp 最差、GILD −17.0pp 次之。</div>
  </div>

  <div class="card">
    <h2>相关性变化：谁在脱钩、谁在贴板块 <span class="tag">分界前 vs 分界后</span></h2>
    <div id="chart_rel" class="chart"></div>
    <div class="note">绿色=分界前，红色=分界后。相关性大幅下降（ALNY、ILMN、BIIB、AMGN）说明个股进入独立行情；上升或持平（VRTX、NTRA、ARGX）说明仍紧密跟随板块。</div>
  </div>

  <div class="card">
    <h2>跷跷板占比：个股事件驱动强度 <span class="tag">2026-02 以来</span></h2>
    <div id="chart_ss" class="chart"></div>
    <div class="note">跷跷板占比越高，说明该股与板块"反向波动"的日子越多——ALNY（37%）、ILMN（36%）、GILD（34%）是个股事件主导型；AMGN（21.5%）、RVMD（22%）是独立强势型（同向跟涨但涨更多）。</div>
  </div>

  <div class="card">
    <h2>7 月中旬以来跑赢占比 <span class="tag">自 {D715}</span></h2>
    <div id="chart_d715" class="chart"></div>
    <div class="note">REGN、ALNY、ILMN 在最近一个月明显跑赢板块（56.5%），而 ARGX（34.8%）、GILD/VRTX/BIIB/RVMD（43-44%）偏弱——注意 GILD 7/15 后跑赢 52.2% 但累计超额有限（前文分析过是脉冲式修复）。</div>
  </div>

  <div class="card">
    <h2>解读与使用提示</h2>
    <ul style="list-style:none; padding:0; margin:0;">
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>IBB 的收益其实由少数成分股贡献</b>：分界后指数 +13.9%，但内部 4 只大权重（AMGN/VRTX/GILD/REGN，28.6% 权重）合计超额约 −24pp，全靠 RVMD/NTRA/ILMN 等中小市值拉回——买 IBB 等于押注这些"小而猛"的管线公司继续兑现。</li>
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>相关性已不能代表成分股表现</b>：ALNY 与 IBB 相关 0.32、ILMN 0.32——用 IBB 对冲/预测这两只股票意义很小；而 VRTX（0.66）仍可当板块 β 工具。</li>
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>ALNY 是最大反向案例</b>：相关性从 0.55 崩到 0.32、跷跷板 37%、超额 −46.4pp——个股利空（需核实具体事件）完全盖过板块行情，若持有它不可用板块逻辑解释。</li>
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>局限</b>：权重为时点快照（随行情波动）；RVMD/ARGX/NTRA 样本短；分界后仅 135 日；未验证各股具体催化剂（除 AMGN/VRTX/GILD 已归因外）。本报告为统计描述，不构成买卖建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 行情、iShares/Morningstar 持仓披露等）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const axisStyle = {{ axisLine: {{ lineStyle: {{ color: '#c9d2de' }} }}, axisLabel: {{ color: '#5b6675' }} }};
const tooltipAxis = {{ trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: {{ color: '#1f2733' }} }};

echarts.init(document.getElementById('chart_cmp')).setOption({{
  tooltip: tooltipAxis,
  legend: {{ data: ['2026分界前超额', '分界后超额', '2026全年超额'], top: 0 }},
  grid: {{ left: 70, right: 30, top: 34, bottom: 40 }},
  xAxis: Object.assign({{ type: 'category', data: DATA.cmp_names }}, axisStyle),
  yAxis: Object.assign({{ type: 'value', name: '超额 (pp)', scale: true }}, axisStyle),
  series: [
    {{ name: '2026分界前超额', type: 'bar', data: DATA.cmp_ytd_pre, barWidth: 10,
      itemStyle: {{ color: 'rgba(46,95,158,.75)', borderRadius: [3,3,0,0] }} }},
    {{ name: '分界后超额', type: 'bar', data: DATA.cmp_post, barWidth: 10,
      itemStyle: {{ color: 'rgba(192,57,43,.8)', borderRadius: [3,3,0,0] }} }},
    {{ name: '2026全年超额', type: 'line', data: DATA.cmp_ytd, symbolSize: 6,
      lineStyle: {{ width: 1.5, color: '#5f5e5a' }}, itemStyle: {{ color: '#5f5e5a' }} }}
  ]
}});

echarts.init(document.getElementById('chart_ex')).setOption({{
  tooltip: tooltipAxis,
  grid: {{ left: 120, right: 30, top: 20, bottom: 40 }},
  xAxis: Object.assign({{ type: 'value', name: '相对 IBB 超额 (pp)' }}, axisStyle),
  yAxis: Object.assign({{ type: 'category', data: DATA.ex_names }}, axisStyle),
  series: [{{ type: 'bar', data: DATA.ex_vals.map((v, i) => ({{ value: v, itemStyle: {{ color: DATA.ex_colors[i] }} }})),
    label: {{ show: true, position: 'right', formatter: p => p.value + 'pp', fontSize: 11, color: '#5b6675' }},
    barWidth: 16 }}]
}});

echarts.init(document.getElementById('chart_rel')).setOption({{
  tooltip: tooltipAxis,
  legend: {{ data: ['分界前', '分界后'], top: 0 }},
  grid: {{ left: 60, right: 20, top: 34, bottom: 40 }},
  xAxis: Object.assign({{ type: 'category', data: DATA.rel_names }}, axisStyle),
  yAxis: Object.assign({{ type: 'value', name: 'Pearson r', min: 0, max: 0.8 }}, axisStyle),
  series: [
    {{ name: '分界前', type: 'bar', data: DATA.rel_pre, barWidth: 12,
      itemStyle: {{ color: 'rgba(30,132,73,.65)', borderRadius: [3,3,0,0] }} }},
    {{ name: '分界后', type: 'bar', data: DATA.rel_post, barWidth: 12,
      itemStyle: {{ color: 'rgba(192,57,43,.75)', borderRadius: [3,3,0,0] }} }}
  ]
}});

echarts.init(document.getElementById('chart_ss')).setOption({{
  tooltip: tooltipAxis,
  grid: {{ left: 60, right: 20, top: 24, bottom: 40 }},
  xAxis: Object.assign({{ type: 'category', data: DATA.ss_names }}, axisStyle),
  yAxis: Object.assign({{ type: 'value', name: '跷跷板占比 %', min: 0, max: 45 }}, axisStyle),
  series: [{{ type: 'bar', data: DATA.ss_vals, barWidth: 16,
    itemStyle: {{ color: 'rgba(46,95,158,.7)', borderRadius: [3,3,0,0] }},
    label: {{ show: true, position: 'top', formatter: p => p.value + '%', fontSize: 10, color: '#5b6675' }} }}]
}});

echarts.init(document.getElementById('chart_d715')).setOption({{
  tooltip: tooltipAxis,
  grid: {{ left: 60, right: 20, top: 24, bottom: 40 }},
  xAxis: Object.assign({{ type: 'category', data: DATA.d715_names }}, axisStyle),
  yAxis: Object.assign({{ type: 'value', name: '跑赢占比 %', min: 0, max: 70 }}, axisStyle),
  series: [{{ type: 'bar', data: DATA.d715_vals, barWidth: 16,
    itemStyle: {{ color: 'rgba(185,119,14,.75)', borderRadius: [3,3,0,0] }},
    label: {{ show: true, position: 'top', formatter: p => p.value + '%', fontSize: 10, color: '#5b6675' }} }}]
}});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)

out_path = os.path.join(ROOT, "reports", "ibb_top10_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", out_path, f"({len(html)/1024:.0f} KB)")
