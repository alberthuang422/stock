#!/usr/bin/env python3
"""生成《药明康德财务增长 × 美国药企研发投入》关联报告(含时间窗口错配分析)。
读 results/wuxi_financial_link.json → reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_financial_link_report.html
"""
import os, json, re, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "reports", "03_wuxi_bigpharma药明康德vs美国药企")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(ROOT, "results", "wuxi_financial_link.json"), encoding="utf-8") as f:
    D = json.load(f)

S = D["series"]
YEARS = S["years"]

# ---- 动态表格 ----
# 药明财务表
wuxi_tbl = ""
wuxi_notes = {2015: "招股书口径", 2022: "含新冠商业化大订单", 2023: "新冠退坡+出售ATU/器械测试(终止经营)",
              2024: "地缘致部分美欧客户谨慎下单"}
for i, y in enumerate(YEARS):
    g = S["wuxi_g"][i]
    gs = "—" if g is None else (f'<span class="up">{g:+.1f}%</span>' if g > 0 else f'<span class="down">{g:+.1f}%</span>')
    note = wuxi_notes.get(y, "")
    wuxi_tbl += f"<tr><td>{y}</td><td>{S['wuxi_rev'][i]:.1f}</td><td>{gs}</td><td class='note'>{note}</td></tr>\n"

# 大药企合计表
bp_tbl = ""
for i, y in enumerate(YEARS):
    rg = S["bp_rev_g"][i]
    rdg = S["bp_rd_g"][i]
    rgs = "—" if rg is None else f"{rg:+.1f}%"
    rdgs = "—" if rdg is None else f"{rdg:+.1f}%"
    rd_note = ""
    if y == 2023: rd_note = "含MRK并购/合作支出~17B"
    elif y == 2018: rd_note = "含ABBV减值5.1B"
    elif y == 2024: rd_note = "含ABBV减值4.5B"
    bp_tbl += (f"<tr><td>{y}</td><td>{S['bp_rev'][i]:.1f}</td><td>{rgs}</td>"
               f"<td>{S['bp_rd'][i]:.1f}</td><td>{rdgs}</td><td class='note'>{rd_note}</td></tr>\n")

# 错位相关表
lag_tbl = ""
for k, v in D["lag"].items():
    label, kn = k.split("|")
    c = v["corr"]
    chtml = "—" if c is None else f'<b style="color:{("#c0392b" if abs(c) > 0.5 else "#1f2733")}">{c:+.3f}</b>'
    lag_tbl += f"<tr><td>{label}</td><td>{kn}</td><td>{chtml}</td><td>{v['n']}</td></tr>\n"
lag_tbl_ex = ""
for k, v in D["lag_ex2022"].items():
    label, kn = k.split("|")
    c = v["corr"]
    chtml = "—" if c is None else f'{c:+.3f}'
    lag_tbl_ex += f"<tr><td>{label}</td><td>{kn}</td><td>{chtml}</td><td>{v['n']}</td></tr>\n"

# 美国客户收入表
us_tbl = ""
for k, v in S["wuxi_us"].items():
    amt, g, pct = v
    ghtml = "—" if g is None else f'<span class="up">{g:+.1f}%</span>'
    us_tbl += f"<tr><td>{k}</td><td>{amt}</td><td>{ghtml}</td><td>{pct if pct else '—'}</td></tr>\n"

# 在手订单/合同负债表
bl_tbl = ""
for k, v in S["wuxi_backlog"].items():
    amt, g = v
    bl_tbl += f"<tr><td>{k}</td><td>{amt}</td><td><span class='up'>{g:+.1f}%</span></td></tr>\n"
cl_tbl = ""
for k, v in S["wuxi_contract_liab"].items():
    cl_tbl += f"<tr><td>{k}</td><td>{v}</td></tr>\n"

data_js = {
    "years": YEARS,
    "wuxi_g": S["wuxi_g"],
    "bp_rev_g": S["bp_rev_g"],
    "bp_rd_g": S["bp_rd_g"],
    "bp_rd_each": S["bp_rd_each"],
    "bp_rd_name": S["bp_rd_name"],
    "wuxi_rev": S["wuxi_rev"],
    "bp_rev": S["bp_rev"],
    "bp_rd": S["bp_rd"],
}

def esc(v):
    return json.dumps(v, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>药明康德财务增长 × 美国药企研发投入 · 错配传导分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#ffffff;
          --red:#c0392b; --green:#1e8449; --blue:#2e5f9e; --amber:#b9770e; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }
  .wrap { max-width: 1080px; margin: 0 auto; }
  h1 { font-size: 25px; letter-spacing: .5px; margin-bottom: 4px; }
  .subtitle { color: var(--sub); font-size: 13px; margin-bottom: 22px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(20,30,50,.05); }
  .card h2 { font-size: 17px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .card h2::before { content: ""; width: 4px; height: 16px; background: var(--blue); border-radius: 2px; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 4px; }
  .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .kv { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .kv .k { font-size: 12px; color: var(--sub); }
  .kv .v { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .kv .v small { font-size: 12px; font-weight: 400; color: var(--sub); }
  .up { color: var(--red); } .down { color: var(--green); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
  th, td { padding: 8px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  td.note { font-size: 11.5px; color: var(--sub); }
  .note { font-size: 12px; color: var(--sub); margin-top: 10px; }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 280px; }
  .concl { border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }
  .concl b { color: var(--blue); }
  .disclaimer { font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }
  .src { font-size: 11.5px; color: var(--sub); margin-top: 8px; }
  .flow { display: flex; flex-direction: column; gap: 0; margin-top: 6px; }
  .frow { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; gap: 8px; align-items: stretch; }
  .fbox { border: 1px solid var(--line); border-radius: 10px; padding: 11px 13px; background: var(--bg); }
  .fbox .fh { font-size: 13px; font-weight: 700; margin-bottom: 5px; }
  .fbox .fb { font-size: 12.5px; color: var(--sub); }
  .fbox.hl { border-color: var(--blue); background: #f4f8ff; }
  .farrow { display: flex; align-items: center; font-size: 15px; color: var(--blue); font-weight: 700; }
  .legend-row { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12.5px; color: var(--sub); margin-bottom: 6px; }
  .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: -1px; }
  .pill { display:inline-block; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .pill.blue { background:#eef3fb; color:var(--blue); } .pill.amber { background:#fdf3e3; color:var(--amber); }
  @media (max-width: 720px) { .grid3, .grid4, .grid2, .frow { grid-template-columns: 1fr; } .farrow { justify-content: center; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>药明康德财务增长 × 美国药企研发投入：代工生意的「订船 → 出口」传导</h1>
  <div class="subtitle">从财报增速看药明康德（603259.SH / 2359.HK）与美国大药企（ABBV/MRK/JNJ/LLY/GILD）的关联 · 重点检验时间窗口错配 · 数据截至 2025 年报 / 2026 中报</div>

  <div class="card">
    <h2>一、核心结论</h2>
    <div class="grid4">
      <div class="kv"><div class="k">药明收入增速 vs 大药企营收增速（同步）</div>
        <div class="v">+0.10</div><div class="k" style="margin-top:6px;">弱相关 —— 药企「卖药」≠ 药明「研发服务」</div></div>
      <div class="kv"><div class="k">药明收入增速 vs 大药企研发投入增速（同步）</div>
        <div class="v">−0.24</div><div class="k" style="margin-top:6px;">无稳定同步关系（口径污染 + 结构性错配）</div></div>
      <div class="kv"><div class="k">药明在手订单增速 → 次年收入</div>
        <div class="v"><span class="up">+47%→+15.8%→+38.9%</span></div>
        <div class="k" style="margin-top:6px;">订单(2024末) → 2025 收入 → 2026H1 收入：错配 1~1.5 年</div></div>
      <div class="kv"><div class="k">药明美国客户收入增速</div>
        <div class="v"><span class="up">+7.7%→+34.3%→+61.5%</span></div>
        <div class="k" style="margin-top:6px;">2024(剔除特定项目) → 2025 → 2026H1：美国景气最直接读数</div></div>
    </div>
    <div class="concl">
      <b>财务层面，「代工」的关联真实存在，但关联不在「增速同步」上，而在「订单 → 收入」的错配传导上。</b><br>
      ① <b>与大药企营收增速几乎无关</b>（同步相关 0.10）：大药企营收是「卖药」结果（礼来 GLP-1 卖爆、艾伯维专利悬崖），与研发外包需求是两套周期 —— 药明 2022 年 +71.8% 时大药企合计仅 +5.1%。<br>
      ② <b>与大药企研发投入增速也无稳定同步关系</b>（−0.24）：总量口径被并购污染（默沙东 2023 R&amp;D +47% 其实是收购 Prometheus 等交易支出，不是外包需求）、被地缘打断（2024 BIOSECURE 致美欧客户谨慎下单）。<br>
      ③ <b>真正成立的传导是药明自己的「订船 → 出口」</b>：在手订单 2024 末 +47.0% → 2025 收入 +15.8% → 2026H1 收入 +38.9%；合同负债 2021-2023 连降（29.9→19.6 亿）对应 2023-2024 收入停滞，2024-2025 回升对应 2025-2026 加速 —— <b>订单/合同负债领先收入约 1~1.5 年</b>。<br>
      ④ <b>结构性研发才是药明订单的真实驱动</b>：礼来研发 +21.4%（GLP-1）→ 药明 TIDES 订单（2024 末 +103.9%、2025 末 +20.2%）→ TIDES 收入（2025 +96%、2026H1 +44.3%）—— 同步性极高（产能当年爬坡）。
    </div>
    <div class="src">数据：药明康德 A 股年报/招股书（CAS 口径，人民币亿元）；5 大药企 10-K（GAAP，十亿美元，R&amp;D 为全口径含并购/减值）；2026H1 为 2026-08-04 披露中报。年度样本仅 9-10 个点，错位相关系数仅作方向性参考。</div>
  </div>

  <div class="card">
    <h2>二、「订船 → 运费 → 出口」传导模型</h2>
    <div class="flow">
      <div class="frow">
        <div class="fbox hl"><div class="fh">L0 需求启动（t0）</div>
          <div class="fb">美国大药企研发预算 + biotech 融资 + BD 交易<br>例：2026H1 融资回暖（VC $163 亿 / BD $1667 亿）；礼来研发 +21.4% 加注 GLP-1</div></div>
        <div class="farrow">→ <span style="font-size:11px;color:var(--sub);">0.5~1年</span></div>
        <div class="fbox hl"><div class="fh">L1 订船（t0+~1年）= 在手订单/合同负债</div>
          <div class="fb">药明在手订单 664.3 亿（2026H1，≈ 全年收入的 1.2 倍）<br>合同负债 27.1 亿（2025 末）—— 已签未交付的「运力池」</div></div>
        <div class="farrow">→ <span style="font-size:11px;color:var(--sub);">1~1.5年</span></div>
        <div class="fbox"><div class="fh">L2 出口（t0+1~2年）= 收入确认</div>
          <div class="fb">2024 末订单 +47% → 2025 收入 +15.8% → 2026H1 +38.9%<br>美国客户收入 2026H1 +61.5%</div></div>
      </div>
      <div style="text-align:center; color:var(--sub); font-size:12px; padding:8px 0;">
        ⚠ 市场与「运费」的类比：股价先行反应订单预期（2025-2026 药明 A/H 大涨），收入后 1-2 年才兑现 —— 但 2024 年 BIOSECURE 曾把「订船」直接打断（客户转观望），这是该链条唯一被外力切断的一次。
      </div>
    </div>
  </div>

  <div class="card">
    <h2>三、增速对照：药明 vs 大药企（同步视图，2016-2025）</h2>
    <div class="legend-row"><span><span class="dot" style="background:#c0392b;"></span>药明康德收入增速（左轴）</span><span><span class="dot" style="background:#2e5f9e;"></span>5大药企营收增速（右轴）</span><span><span class="dot" style="background:#b9770e;"></span>5大药企研发投入增速（右轴）</span></div>
    <div id="chart1" class="chart"></div>
    <div class="note">三个序列几乎没有「同步峰谷」：药明 2016-2021 稳定高增（23-38%）而大药企营收增速只有 2-13%；2022 药明脉冲（新冠订单）与大药企无关；2023-2024 药明停滞时大药企 R&amp;D 却在 2023 冲高（并购口径）。「同步相关」≈ 0 是数据层面的铁证：<b>药企卖药好 ≠ 药明接单好</b>。</div>
  </div>

  <div class="card">
    <h2>四、错位视图：把大药企研发投入「前移 1 年」再看</h2>
    <div class="legend-row"><span><span class="dot" style="background:#c0392b;"></span>药明收入增速（当年）</span><span><span class="dot" style="background:#b9770e;"></span>大药企研发投入增速（前移1年）</span></div>
    <div id="chart2" class="chart"></div>
    <table>
      <tr><th>药明收入增速 vs</th><th>错位</th><th>相关系数</th><th>样本</th></tr>
      __LAG_TBL__
    </table>
    <div class="note">结论：无论同步还是错位 1 年，药明收入增速与大药企总量研发投入增速都没有稳健的相关（受并购口径与 2022 新冠极端值影响）。<b>「总量研发投入」不是药明收入的好先行指标 —— 需要下钻到结构性部分（GLP-1/TIDES/ADC）和药明自己的订单。</b>年度样本极小（n≤10），以上系数仅供方向参考，不做统计推断。</div>
  </div>

  <div class="card">
    <h2>五、结构性研发才是真驱动：5 大药企研发投入拆开看</h2>
    <div id="chart3" class="chart"></div>
    <div class="note">礼来（红）研发十年近 3 倍（4.8→13.3B）、且是唯一连续增长的 —— 它的 GLP-1/TIDES 产能外包直接对应药明 TIDES 订单（2024 末 +103.9%）与收入（2025 +96%）。默沙东 2023 的 30.5B 与艾伯维 2018/2024 的尖峰都是并购/减值口径，不是真实外包需求。<b>看药明的需求，盯「结构性加投方」（礼来/阿斯利康/诺华/GSK）+ biotech 融资，而不是五家合计。</b></div>
  </div>

  <div class="card">
    <h2>六、药明内部传导：在手订单 / 合同负债 → 收入（错配 1~1.5 年）</h2>
    <div class="grid2">
      <div>
        <div class="note" style="margin-bottom:4px;"><b>在手订单（持续经营口径）→ 收入</b></div>
        <table>
          <tr><th>时点</th><th>在手订单(亿元)</th><th>同比</th></tr>
          __BL_TBL__
        </table>
        <div class="note">2024 末订单 +47% → 2025 收入 +15.8%（持续经营 +21.4%）→ 2026H1 +38.9%（持续经营 +48%）：订单是收入的「领先 1~1.5 年」读数，公司据此把 2026 指引上调至 585-605 亿。</div>
      </div>
      <div>
        <div class="note" style="margin-bottom:4px;"><b>合同负债（预收款，亿元）→ 收入</b></div>
        <table>
          <tr><th>年末</th><th>合同负债(亿元)</th></tr>
          __CL_TBL__
        </table>
        <div class="note">合同负债 2021-2023 连降（29.9→19.6）对应 2023-2024 收入停滞（+2.5%/−2.7%）；2024-2025 回升（22.5→27.1）对应 2025-2026 收入加速 —— 与在手订单互为印证。</div>
      </div>
    </div>
    <div id="chart4" class="chart"></div>
  </div>

  <div class="card">
    <h2>七、美国客户收入：药明身上的「美国景气温度计」</h2>
    <table>
      <tr><th>报告期</th><th>美国客户收入(亿元)</th><th>同比</th><th>占持续经营收入</th></tr>
      __US_TBL__
    </table>
    <div class="note">2021 年后公司披露口径从「美国客户」改为「境外」，2024 起恢复美国明细。曲线看得很清楚：2024 年受 BIOSECURE 压制仅 +7.7%（剔除特定项目）→ 2025 +34.3% → 2026H1 +61.5%（占比 77%）—— <b>美国客户的研发外包需求 2025-2026 在强劲修复，这就是药明订单/收入的美国侧基本面。</b></div>
    <div class="concl">
      <b>综合判断（回答「药明增长和国外制药巨头增长是否有关联」）：</b><br>
      ① 与「卖药增长」（大药企营收）—— <b>无关</b>（同步相关 0.10，且 2022 极端背离）；<br>
      ② 与「研发投入增长」—— <b>总量无关、结构性相关</b>（盯 LLY/AZN/NVS/GSK 等结构性加投方 + biotech 融资，而非五家合计）；<br>
      ③ 与「美国客户研发外包需求」—— <b>直接相关</b>（美国收入 2026H1 +61.5%、在手订单 +25.2% 即最硬证据），但存在 1~1.5 年确认时滞；<br>
      ④ <b>应用提示</b>：想从药明反推美国景气，应看「在手订单增速 + 美国客户收入增速 + biotech 融资」这三个领先读数；药明收入增速本身滞后 1-2 年，不宜当实时景气计。反向同理：药明订单强 ≠ 大药企销售强（两者差着一层「研发外包率」的弹性）。
    </div>
  </div>

  <div class="card">
    <h2>八、数据附表</h2>
    <div class="note" style="margin-bottom:4px;"><b>药明康德历年财务（人民币亿元，CAS）</b></div>
    <table>
      <tr><th>年度</th><th>营业收入</th><th>同比</th><th>备注</th></tr>
      __WUXI_TBL__
    </table>
    <div class="note" style="margin-bottom:4px; margin-top:14px;"><b>5 大药企合计（十亿美元，GAAP）</b></div>
    <table>
      <tr><th>年度</th><th>合计营收</th><th>营收增速</th><th>合计研发投入</th><th>研发增速</th><th>备注</th></tr>
      __BP_TBL__
    </table>
    <div class="src">药明财务：2015-2017 招股书、2018-2025 年报、2026H1 中报（公司公告）；5 大药企：10-K GAAP（营收/研发费用全口径，macrotrends/statista/公司公告汇总，需核实原文）。错位相关系数为年度数据 Pearson，样本 n=8-10，仅方向性参考。</div>
  </div>

  <div class="disclaimer">
    <b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
  </div>

</div>
<script>
const DATA = """ + esc(data_js) + """;
const AX = { axisLine: { lineStyle: { color: '#d5dce6' } }, axisLabel: { color: '#5b6675', fontSize: 11 } };
const TL = { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e3e8ef', textStyle: { color: '#1f2733', fontSize: 12 } };

// chart1 同步增速
(() => {
  echarts.init(document.getElementById('chart1')).setOption({
    tooltip: TL,
    legend: { data: ['药明收入增速', '5大药企营收增速', '5大药企研发投入增速'], textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 52, right: 52, top: 36, bottom: 26 },
    xAxis: { type: 'category', data: DATA.years, ...AX },
    yAxis: [
      { type: 'value', name: '药明增速(%)', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
      { type: 'value', name: '大药企增速(%)', ...AX, splitLine: { show: false } }
    ],
    series: [
      { name: '药明收入增速', type: 'line', data: DATA.wuxi_g, yAxisIndex: 0, lineStyle: { width: 3 }, color: '#c0392b', symbol: 'circle', symbolSize: 6 },
      { name: '5大药企营收增速', type: 'line', data: DATA.bp_rev_g, yAxisIndex: 1, lineStyle: { width: 1.6 }, color: '#2e5f9e' },
      { name: '5大药企研发投入增速', type: 'line', data: DATA.bp_rd_g, yAxisIndex: 1, lineStyle: { width: 1.6 }, color: '#b9770e' }
    ]
  });
})();

// chart2 错位: 药明增速(t) vs R&D增速(t-1)
(() => {
  const years = DATA.years.slice(1); // 2016..2025
  const wg = DATA.wuxi_g.slice(1);
  const rdLag = DATA.bp_rd_g.slice(0, -1); // R&D 前移1年: 2016年药明 vs 2015年R&D -> 直接错位展示用 t-1 映射
  echarts.init(document.getElementById('chart2')).setOption({
    tooltip: TL,
    legend: { data: ['药明收入增速(t)', '大药企研发投入增速(t-1)'], textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 52, right: 52, top: 36, bottom: 26 },
    xAxis: { type: 'category', data: years, ...AX },
    yAxis: [
      { type: 'value', name: '药明增速(%)', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
      { type: 'value', name: '研发增速(%)', ...AX, splitLine: { show: false } }
    ],
    series: [
      { name: '药明收入增速(t)', type: 'line', data: wg, yAxisIndex: 0, lineStyle: { width: 3 }, color: '#c0392b', symbol: 'circle', symbolSize: 6 },
      { name: '大药企研发投入增速(t-1)', type: 'line', data: rdLag, yAxisIndex: 1, lineStyle: { width: 1.6 }, color: '#b9770e' }
    ]
  });
})();

// chart3 5大药企研发投入拆解
(() => {
  const keys = Object.keys(DATA.bp_rd_each);
  const series = keys.map(k => ({
    name: DATA.bp_rd_name[k], type: 'line', showSymbol: false,
    data: DATA.bp_rd_each[k], lineStyle: { width: 1.6 }
  }));
  const colors = { '艾伯维': '#8e6bb5', '默沙东': '#2e5f9e', '强生': '#b9770e', '礼来': '#c0392b', '吉利德': '#1e8449' };
  series.forEach(s => s.color = colors[s.name]);
  echarts.init(document.getElementById('chart3')).setOption({
    tooltip: TL,
    legend: { data: keys.map(k => DATA.bp_rd_name[k]), textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 52, right: 16, top: 36, bottom: 26 },
    xAxis: { type: 'category', data: DATA.years, ...AX },
    yAxis: { type: 'value', name: '研发投入(十亿美元)', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
    series
  });
})();

// chart4 药明收入规模 + 增速
(() => {
  const g = DATA.wuxi_g.map(v => v === null ? 0 : v);
  echarts.init(document.getElementById('chart4')).setOption({
    tooltip: TL,
    legend: { data: ['营业收入(亿元)', '收入增速(%)'], textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 52, right: 52, top: 36, bottom: 26 },
    xAxis: { type: 'category', data: DATA.years, ...AX },
    yAxis: [
      { type: 'value', name: '收入(亿元)', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
      { type: 'value', name: '增速(%)', ...AX, splitLine: { show: false } }
    ],
    series: [
      { name: '营业收入(亿元)', type: 'bar', data: DATA.wuxi_rev, yAxisIndex: 0, barWidth: 18, color: '#5b9bd5' },
      { name: '收入增速(%)', type: 'line', data: g, yAxisIndex: 1, lineStyle: { width: 2.5 }, color: '#c0392b', symbol: 'circle', symbolSize: 5 }
    ]
  });
})();
</script>
</body>
</html>
"""

html = html.replace("__LAG_TBL__", lag_tbl)
html = html.replace("__BL_TBL__", bl_tbl)
html = html.replace("__CL_TBL__", cl_tbl)
html = html.replace("__US_TBL__", us_tbl)
html = html.replace("__WUXI_TBL__", wuxi_tbl)
html = html.replace("__BP_TBL__", bp_tbl)

out_path = os.path.join(OUT_DIR, "wuxi_financial_link_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", out_path)

# JS 自检
scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
for i, s in enumerate(scripts):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
        tf.write("const echarts = {init: () => ({setOption: () => {}})};\n" + s)
        jsp = tf.name
    r = subprocess.run(["/Users/alberthuang/.workbuddy/binaries/node/versions/22.22.2/bin/node", "--check", jsp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"JS SYNTAX ERROR in script {i}:\n{r.stderr[:1500]}")
    else:
        print(f"script {i}: node --check OK")
    os.unlink(jsp)
