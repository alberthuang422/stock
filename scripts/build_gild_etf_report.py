#!/usr/bin/env python3
"""生成 GILD 与 IBB/XBI/XLV 三只 ETF 影响对比报告。
读 results/gild_etf_compare.json, 输出 reports/gild_etf_compare_report.html。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "results", "gild_etf_compare.json"), encoding="utf-8") as f:
    D = json.load(f)

# 三阶段表（窗口 = 2025-09 起）
rows = []
for etf in ["IBB", "XBI", "XLV"]:
    o = D[etf]
    r = {"etf": etf}
    for blk in ["窗口内", "分界前", "分界后"]:
        b = o[blk]
        r[blk] = b
    r["fisher"] = o["fisher"]
    rows.append(r)

# 滚动 R2 序列（2025-09 起, 对齐三只）
roll_all = {}
for etf in ["IBB", "XBI", "XLV"]:
    rr = [x for x in D[etf]["roll_r2"] if x["r2"] is not None]
    roll_all[etf] = rr
dates = [x["date"] for x in roll_all["IBB"]]
r_ibb = [x["r2"] for x in roll_all["IBB"]]
r_xbi = [x["r2"] for x in roll_all["XBI"]]
r_xlv = [x["r2"] for x in roll_all["XLV"]]

# 价格走势 (2025-09 起, 三对 GILD vs ETF 归一化)
price = {etf: D[etf]["price"] for etf in ["IBB", "XBI", "XLV"]}
p_dates = [p["date"] for p in price["IBB"]]
p_etf = {etf: [p["e"] for p in price[etf]] for etf in ["IBB", "XBI", "XLV"]}
p_gild = [p["g"] for p in price["IBB"]]  # GILD 归一化(以2025-09为100), 同一序列

data_js = {
    "dates": dates, "r_ibb": r_ibb, "r_xbi": r_xbi, "r_xlv": r_xlv,
    "p_dates": p_dates, "p_ibb": p_etf["IBB"], "p_xbi": p_etf["XBI"], "p_xlv": p_etf["XLV"], "p_gild": p_gild,
}
data_json = json.dumps(data_js, ensure_ascii=False)

# 表格行
def fmt(v, suf=""):
    return f"{v}{suf}"

trs = ""
for r in rows:
    b = r["窗口内"]
    trs += f"""<tr>
      <td><b>{r['etf']}</b></td>
      <td>{r['窗口内']['pearson']:.3f}</td><td>{r['窗口内']['r2']*100:.1f}%</td><td>{r['窗口内']['beta']:.2f}</td><td>{r['窗口内']['resid_vol']:.2f}%</td>
      <td>{r['分界前']['pearson']:.3f}</td><td>{r['分界前']['r2']*100:.1f}%</td><td>{r['分界前']['beta']:.2f}</td>
      <td>{r['分界后']['pearson']:.3f}</td><td>{r['分界后']['r2']*100:.1f}%</td><td>{r['分界后']['beta']:.2f}</td><td>{r['分界后']['resid_vol']:.2f}%</td>
      <td>{r['fisher']['z']:.2f} / p={r['fisher']['p']:.2f}</td>
    </tr>"""

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GILD 与 IBB / XBI / XLV 影响对比报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root {{ --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#ffffff;
          --red:#c0392b; --green:#1e8449; --blue:#2e5f9e; --amber:#b9770e; --purple:#534ab7; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }}
  .wrap {{ max-width: 1080px; margin: 0 auto; }}
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
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }}
  th, td {{ padding: 8px 9px; text-align: right; border-bottom: 1px solid var(--line); }}
  th {{ background: #f1f4f9; font-weight: 600; }}
  th:first-child, td:first-child {{ text-align: left; }}
  .note {{ font-size: 12px; color: var(--sub); margin-top: 10px; }}
  .chart {{ width: 100%; height: 360px; }}
  .concl {{ border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }}
  .disclaimer {{ font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }}
  .src {{ font-size: 11.5px; color: var(--sub); margin-top: 8px; }}
  @media (max-width: 720px) {{ .grid3 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="wrap">

  <h1>GILD 与 IBB / XBI / XLV 影响对比报告</h1>
  <div class="subtitle">吉利德（GILD）对三只健康/生物科技 ETF 的敏感度 · 2025-09 以来 · 以 2026-02 为界 · 数据截至 2026-08-14</div>

  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">2025-09 以来解释力 R²</div><div class="v"><span class="up">XLV 26.2%</span></div></div>
      <div class="kv"><div class="k">分界后解释力 R²</div><div class="v"><span class="up">XLV 33.0%</span></div></div>
      <div class="kv"><div class="k">分界后 β</div><div class="v">XLV 0.94 <small>最高</small></div></div>
    </div>
    <div class="concl">
      ① <b>2025-09 以来窗口内 XLV 解释力最高（26.2%），分界后（2026-02 起）优势更明显</b>：XLV 的 R² 从分界前 16.5% 升至 33.0%（Fisher p=0.09，接近显著），IBB 仅 26.5%，XBI 只有 8.2%——<b>近期对 GILD 影响最大的是 XLV（健康护理大盘）</b>。<br>
      ② <b>分界前 XLV 曾明显掉队</b>：2025-09 ~ 2026-01 期间 XLV 解释力仅 16.5%（GILD +25.9% 大涨、XLV 只 +12.5%，GILD 当时走独立行情）；2026-02 后 GILD 转弱，重新回归 XLV 的节奏。<br>
      ③ <b>IBB 解释力中等且稳定</b>：分界前 21.2% → 分界后 26.5%，β 0.64——IBB 的行情由中小市值生物科技驱动（RVMD/NTRA 等），GILD 只跟一半。<br>
      ④ <b>XBI 基本脱钩</b>：两个阶段 R² 都不到 9%、β 0.27-0.32——2025-09 以来 XBI +69.5% 而 GILD 仅 +22.8%，小盘生物科技行情 GILD 完全不参与。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价，2025-09-01 ~ 2026-08-14）；计算：日收益率 Pearson 相关、OLS β、R²（ETF 解释 GILD 日波动的比例）、60 日滚动 R²、Fisher z 检验（分界前 vs 分界后）。</div>
  </div>

  <div class="card">
    <h2>三阶段回归全景表 <span class="tag">2025-09 起 · 以 2026-02-01 为界</span></h2>
    <table>
      <tr><th>ETF</th>
          <th colspan="4">2025-09 以来（全窗口）</th><th colspan="3">分界前（2025.09~2026.01）</th>
          <th colspan="4">分界后（2026.02~08）</th><th>Fisher z</th></tr>
      <tr><th></th><th>r</th><th>R²</th><th>β</th><th>残差</th><th>r</th><th>R²</th><th>β</th>
          <th>r</th><th>R²</th><th>β</th><th>残差</th><th>分界前vs后</th></tr>
      {trs}
    </table>
    <div class="note">R² = 该 ETF 日收益率能解释 GILD 日收益率波动的比例（"影响大小"的直接度量）；β = GILD 对该 ETF 的敏感度（ETF 涨 1% → GILD 涨 β%）；残差 = 剔除 ETF 影响后 GILD 的独立波动。分界前 101 日、分界后 135 日。</div>
  </div>

  <div class="card">
    <h2>60 日滚动 R²：2026-02 后 XLV 对 GILD 的解释力持续领先 <span class="tag">2025-09 起</span></h2>
    <div id="chart_r2" class="chart"></div>
    <div class="note">绿=IBB，紫=XLV，蓝=XBI。2025-09 ~ 2026-01 期间三条线接近（XLV 甚至一度最低）；2026-02 后 XLV（紫）明显领先、最新 ~30%，IBB 次之（~22%），XBI 最低（~6%）。</div>
  </div>

  <div class="card">
    <h2>2025-09 以来归一化走势：GILD 与 XLV 最同步 <span class="tag">归一化 100=基准日</span></h2>
    <div id="chart_price" class="chart"></div>
    <div class="note">实线=GILD（黑），虚线=三只 ETF（IBB 红 / XBI 蓝 / XLV 紫，以 2025-09-01 为 100）。2025-09~2026-01 GILD 走独立上行（涨幅超过三只 ETF）；2026-02 后 GILD 与 XLV 的节奏明显更接近（同涨同跌），与 IBB 次之，与 XBI 完全分叉（XBI 大涨 GILD 走弱）。</div>
  </div>

  <div class="card">
    <h2>解读与使用提示</h2>
    <ul style="list-style:none; padding:0; margin:0;">
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>判断 GILD 短期走势看 XLV 最有效</b>：2026-02 后 XLV 解释 GILD 波动的 33.0%，β 0.94 几乎 1:1——XLV 涨跌 1%，GILD 平均同向跟 0.94%。</li>
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>IBB 作参照中等有效</b>：分界后 R² 26.5%、β 0.64——IBB 涨 1% GILD 跟 0.64%；但因 IBB 行情由中小市值驱动，两者联动弱于 XLV。</li>
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>XBI 基本无用</b>：两阶段 R² 都不足 9%、β 0.27-0.32——XBI 的行情（小盘 biotech）与 GILD 几乎无关，2025-09 以来 XBI +69.5% 与 GILD +22.8% 的差距就是明证。</li>
      <li style="padding:8px 0 8px 18px; border-left:2px solid var(--line); margin-left:6px; position:relative;">
        <span style="position:absolute; left:-5px; top:14px; width:8px; height:8px; border-radius:50%; background:var(--blue);"></span>
        <b>局限</b>：R² 只反映统计联动，不一定是因果关系（三者都受宏观/利率影响）；GILD 的个股事件（如 Q2 财报巨亏）仍会产生独立波动（残差 ~1.4-1.6%）；窗口仅 11 个月。本报告为统计描述，不构成买卖建议。</li>
    </ul>
    <div class="disclaimer">免责声明：以上内容基于公开数据（Yahoo Finance 行情等）与量化统计，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>

<script>
const DATA = __DATA_JSON__;
const axisStyle = {{ axisLine: {{ lineStyle: {{ color: '#c9d2de' }} }}, axisLabel: {{ color: '#5b6675' }} }};
const tooltipAxis = {{ trigger: 'axis', backgroundColor: 'rgba(255,255,255,.96)', borderColor: '#d9e1ec', textStyle: {{ color: '#1f2733' }} }};

echarts.init(document.getElementById('chart_r2')).setOption({{
  tooltip: tooltipAxis,
  legend: {{ data: ['IBB', 'XBI', 'XLV'], top: 0 }},
  grid: {{ left: 55, right: 20, top: 34, bottom: 40 }},
  xAxis: Object.assign({{ type: 'category', data: DATA.dates }}, axisStyle),
  yAxis: Object.assign({{ type: 'value', name: '滚动R² %', min: 0, max: 60 }}, axisStyle),
  series: [
    {{ name: 'IBB', type: 'line', data: DATA.r_ibb, showSymbol: false, lineStyle: {{ width: 1.6, color: '#1e8449' }}, itemStyle: {{ color: '#1e8449' }} }},
    {{ name: 'XBI', type: 'line', data: DATA.r_xbi, showSymbol: false, lineStyle: {{ width: 1.6, color: '#2e5f9e' }}, itemStyle: {{ color: '#2e5f9e' }} }},
    {{ name: 'XLV', type: 'line', data: DATA.r_xlv, showSymbol: false, lineStyle: {{ width: 1.8, color: '#534ab7' }}, itemStyle: {{ color: '#534ab7' }} }}
  ]
}});

echarts.init(document.getElementById('chart_price')).setOption({{
  tooltip: tooltipAxis,
  legend: {{ data: ['GILD', 'IBB', 'XBI', 'XLV'], top: 0 }},
  grid: {{ left: 55, right: 20, top: 34, bottom: 40 }},
  xAxis: Object.assign({{ type: 'category', data: DATA.p_dates }}, axisStyle),
  yAxis: Object.assign({{ type: 'value', name: '归一化价格', scale: true }}, axisStyle),
  series: [
    {{ name: 'GILD', type: 'line', data: DATA.p_gild, showSymbol: false, lineStyle: {{ width: 2.2, color: '#2c2c2a' }}, itemStyle: {{ color: '#2c2c2a' }} }},
    {{ name: 'IBB', type: 'line', data: DATA.p_ibb, showSymbol: false, lineStyle: {{ width: 1.3, type: 'dashed', color: '#c0392b' }}, itemStyle: {{ color: '#c0392b' }} }},
    {{ name: 'XBI', type: 'line', data: DATA.p_xbi, showSymbol: false, lineStyle: {{ width: 1.3, type: 'dashed', color: '#2e5f9e' }}, itemStyle: {{ color: '#2e5f9e' }} }},
    {{ name: 'XLV', type: 'line', data: DATA.p_xlv, showSymbol: false, lineStyle: {{ width: 1.3, type: 'dashed', color: '#534ab7' }}, itemStyle: {{ color: '#534ab7' }} }}
  ]
}});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)

out_path = os.path.join(ROOT, "reports", "gild_etf_compare_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", out_path, f"({len(html)/1024:.0f} KB)")
