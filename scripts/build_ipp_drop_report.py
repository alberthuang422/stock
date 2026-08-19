# -*- coding: utf-8 -*-
"""IPP 板块 2026-08-18 大跌归因报告生成器"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "07_ipp_drop")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "ipp_drop_0818.json")) as f:
    P = json.load(f)

def js(o):
    return json.dumps(o, ensure_ascii=False)

stats = P["stats"]
sector = P["sector"]
resid = P["stock_resid"]
hpct = P["hist_pct"]
norm = P["series"]["norm"]
dgs30 = P["series"]["dgs30"]

members = ["TLN", "NRG", "CEG", "VST"]

# ---- 图表数据 ----
# 1) 两日跌幅柱状（按 8/18 跌幅升序 → 最左最惨）
order = sorted(members, key=lambda k: stats[k]["ret_0818"])
daily = {
    "x": [f"{k}·{stats[k]['name'].split()[0]}" for k in order],
    "d17": [stats[k]["ret_0817"] for k in order],
    "d18": [stats[k]["ret_0818"] for k in order],
    "xlutes": [stats["XLU"]["ret_0818"], stats["UTES"]["ret_0818"]],
}

# 2) 近 6 个月归一化（2026-02-18=100）
norm_series = [
    {"name": "TLN", "data": norm["TLN"]["idx"], "color": "#c05c0b"},
    {"name": "NRG", "data": norm["NRG"]["idx"], "color": "#7d5ba6"},
    {"name": "CEG", "data": norm["CEG"]["idx"], "color": "#1e66d6"},
    {"name": "VST", "data": norm["VST"]["idx"], "color": "#0aa06e"},
    {"name": "UTES", "data": norm["UTES"]["idx"], "color": "#9aa4b2"},
    {"name": "XLU", "data": norm["XLU"]["idx"], "color": "#c3cad4"},
    {"name": "SPY", "data": norm["SPY"]["idx"], "color": "#888888", "dashed": True},
]
norm_dates = norm["TLN"]["date"]

# 3) 30Y 收益率 + 板块等权（双轴）
idx_avg = [round(sum(norm[k]["idx"][i] for k in members) / len(members), 2) for i in range(len(norm_dates))]

# 4) 个股 β 分解
resid_cat = {
    "x": [k for k in members],
    "actual": [resid[k]["actual"] for k in members],
    "expected": [resid[k]["expected"] for k in members],
    "beta": [resid[k]["beta"] for k in members],
}

# 5) 两天累计
cum2 = {}
for k in members:
    c = (1 + stats[k]["ret_0817"] / 100) * (1 + stats[k]["ret_0818"] / 100) - 1
    cum2[k] = round(c * 100, 2)

# ---- 表格行 ----
def cls(v):
    return "up" if v > 0 else ("dn" if v < 0 else "")

rows = ""
for k in members:
    s = stats[k]
    rows += f"""<tr>
      <td><b>{k}</b><br><span style="color:var(--sub);font-size:11px;">{s['name']}</span></td>
      <td class="{cls(s['ret_0817'])}">{s['ret_0817']:+.2f}%</td>
      <td class="{cls(s['ret_0818'])}">{s['ret_0818']:+.2f}%</td>
      <td class="{cls(cum2[k])}">{cum2[k]:+.2f}%</td>
      <td>{s['close_0818']:.2f}</td>
      <td class="{cls(s['ret_5d'])}">{s['ret_5d']:+.2f}%</td>
      <td class="{cls(s['ret_20d'])}">{s['ret_20d']:+.2f}%</td>
      <td>{s['vol_ratio']:.2f}x</td>
      <td>{s['off_hi52']:.1f}%<br><span style="color:var(--sub);font-size:11px;">{s['hi52_date']}</span></td>
      <td>{s['off_lo52']:+.1f}%</td>
      <td>{hpct[k]['pct_2025']:.1f}%</td>
    </tr>"""

rows2 = ""
for k in members:
    s = stats[k]
    r = resid[k]
    rows2 += f"""<tr>
      <td><b>{k}</b></td>
      <td>{r['beta']:.2f}</td>
      <td>{r['expected']:.2f}%</td>
      <td class="dn">{r['actual']:.2f}%</td>
      <td class="dn">{r['resid']:+.2f}pp</td>
      <td>{s['ret_hist_min']:.1f}%</td>
      <td>{s['ret_hist_p1']:.1f}%</td>
      <td>{'放量3.1倍，公司级抛压' if k=='TLN' else ('收在52周低点' if k=='NRG' else ('跟随板块，无个股新闻' if k in ('CEG','VST') else ''))}</td>
    </tr>"""

# ---- KPI ----
def kpi_num(v, c=""):
    return f'<div class="num {c}">{v}</div>'

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IPP 板块 2026-08-18 大跌归因 · TLN −11% 领跌</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}}
  .wrap{{max-width:1220px;margin:0 auto;}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}}
  h1{{font-size:21px;margin-bottom:4px;}}
  .meta{{color:var(--sub);font-size:12.5px;margin-bottom:14px;}}
  h2{{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}}
  h3{{font-size:14px;margin:14px 0 8px;color:var(--ink);}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:14px;}}
  .kpi{{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
  .kpi .num{{font-size:20px;font-weight:700;}}
  .kpi .num.up{{color:var(--red);}} .kpi .num.dn{{color:var(--green);}}
  .kpi .lab{{color:var(--sub);font-size:12px;margin-top:2px;}}
  .verdict{{background:linear-gradient(135deg,#fdf3f3,#eef7f2);border:1px solid #f0dada;border-radius:12px;padding:16px 20px;margin-top:14px;}}
  .verdict .t{{font-size:13px;color:var(--sub);margin-bottom:6px;}}
  .verdict .b{{font-size:15.5px;font-weight:700;color:var(--ink);}}
  .verdict .b .hl{{color:var(--purple);}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;}}
  th{{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}}
  td{{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}}
  td.up{{color:var(--red);font-weight:600;}} td.dn{{color:var(--green);font-weight:600;}} td.na{{color:#c3c8cf;}}
  .scroll{{overflow-x:auto;}}
  .chart{{width:100%;height:380px;}}
  .chart.sm{{height:320px;}}
  .note{{color:var(--sub);font-size:12px;margin-top:8px;}}
  .keypoint{{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}}
  .warn{{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;margin-top:10px;}}
  .dis{{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}}
  .hl{{font-weight:700;color:var(--red);}} .hlg{{font-weight:700;color:var(--green);}} .hlb{{font-weight:700;color:var(--blue);}} .hlp{{font-weight:700;color:var(--purple);}}
  .tag{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;margin-right:4px;}}
  .tag.tln{{background:#fdf1e7;color:#c05c0b;}} .tag.nrg{{background:#f1eaf8;color:#7d5ba6;}} .tag.ceg{{background:#eef3fb;color:var(--blue);}} .tag.vst{{background:#e9f7f1;color:#0a7a54;}}
  .step{{margin-bottom:14px;}}
  .step .st{{font-weight:700;color:var(--ink);}}
  .step .sd{{color:var(--sub);font-size:12.5px;margin-top:2px;}}
  .flow{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;}}
  .fnode{{flex:1;min-width:190px;background:#fbfcfe;border:1px solid var(--line);border-left:4px solid var(--amber);border-radius:8px;padding:10px 12px;font-size:12.5px;}}
  .fnode .ft{{font-weight:700;font-size:13px;}}
  .fnode .fs{{color:var(--sub);font-size:12px;margin-top:2px;}}
  .arrow{{align-self:center;color:var(--sub);font-weight:700;font-size:16px;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>独立电力生产商（IPP）板块 2026-08-18 大跌归因<br><span style="font-size:15px;color:var(--sub);font-weight:500;">TLN −11.0% 领跌 · 板块等权 −6.1% · 超额标普 −5.4pp —— 收益率飙升 × AI 电力主题撤退 × 个股利空叠加</span></h1>
    <div class="meta">行情截至 2026-08-18 美股收盘（Yahoo 日线）｜板块等权 = TLN/NRG/CEG/VST 四只独立发电商算术平均｜对照：UTES（被发电商重塑的电力 ETF）、XLU（传统公用事业）、SPY｜30Y = 美国 30 年期国债收益率（FRED DGS30）</div>

    <div class="verdict">
      <div class="t">▍一句话结论</div>
      <div class="b">8/18 的暴跌是 <span class="hlp">「宏观利率冲击 × AI 电力叙事集体撤退 × TLN 公司级利空」三层共振</span>：30 年期美债收益率盘中升破 5.32%（2007 年以来最高）→ 高估值长久期的 AI 电力主题遭整体再定价 → 板块等权 −6.12% 而标普仅 −0.68%；其中 TLN 因财报后目标价连环下调 + $9.84 亿 shelf 注册 + 降级，残差 −9.7pp、量比 3.1 倍，跌得最深；<b>而传统公用事业 XLU 仅 −0.36% —— 这不是「公用事业板块」下跌，是「AI 电力叙事」的挤兑。</b></div>
    </div>

    <div class="kpis">
      <div class="kpi"><div class="num dn">-6.12%</div><div class="lab">板块等权 8/18（TLN/NRG/CEG/VST）</div></div>
      <div class="kpi"><div class="num dn">-11.00%</div><div class="lab">TLN 单日跌幅（2025 以来 99.3% 的日子没这么大）</div></div>
      <div class="kpi"><div class="num dn">-5.44pp</div><div class="lab">板块超额标普（SPY −0.68%）</div></div>
      <div class="kpi"><div class="num" style="color:var(--amber);">5.32%+</div><div class="lab">30Y 美债收益率（2007-06 以来最高，盘中）</div></div>
      <div class="kpi"><div class="num" style="color:var(--blue);">1.22</div><div class="lab">板块 60 日 β（vs SPY，只解释 −0.8% 跌幅）</div></div>
      <div class="kpi"><div class="num dn">-5.29pp</div><div class="lab">板块残差（β 之外 = 叙事再定价）</div></div>
    </div>
  </div>

  <div class="card">
    <h2>一、当日全景：跌幅、量能与两连跌</h2>
    <div class="scroll">
    <table>
      <tr><th>标的</th><th>8/17 周一</th><th>8/18 周二</th><th>两日累计</th><th>8/18 收盘</th><th>5日</th><th>20日</th><th>量比(30日均)</th><th>距52周高</th><th>距52周低</th><th>跌幅罕见度*</th></tr>
      {rows}
      <tr style="background:#f8f9fb;"><td><b>XLU</b><br><span style="color:var(--sub);font-size:11px;">传统公用事业</span></td>
        <td class="{cls(stats['XLU']['ret_0817'])}">{stats['XLU']['ret_0817']:+.2f}%</td>
        <td class="{cls(stats['XLU']['ret_0818'])}">{stats['XLU']['ret_0818']:+.2f}%</td>
        <td class="{cls(round((1+stats['XLU']['ret_0817']/100)*(1+stats['XLU']['ret_0818']/100)-1,4)*100)}">{round((1+stats['XLU']['ret_0817']/100)*(1+stats['XLU']['ret_0818']/100)-1,4)*100:+.2f}%</td>
        <td>{stats['XLU']['close_0818']:.2f}</td>
        <td class="{cls(stats['XLU']['ret_5d'])}">{stats['XLU']['ret_5d']:+.2f}%</td>
        <td class="{cls(stats['XLU']['ret_20d'])}">{stats['XLU']['ret_20d']:+.2f}%</td>
        <td>{stats['XLU']['vol_ratio']:.2f}x</td>
        <td>{stats['XLU']['off_hi52']:.1f}%</td>
        <td>{stats['XLU']['off_lo52']:+.1f}%</td>
        <td class="na">-</td></tr>
      <tr style="background:#f8f9fb;"><td><b>UTES</b><br><span style="color:var(--sub);font-size:11px;">电力ETF</span></td>
        <td class="{cls(stats['UTES']['ret_0817'])}">{stats['UTES']['ret_0817']:+.2f}%</td>
        <td class="{cls(stats['UTES']['ret_0818'])}">{stats['UTES']['ret_0818']:+.2f}%</td>
        <td class="{cls(round((1+stats['UTES']['ret_0817']/100)*(1+stats['UTES']['ret_0818']/100)-1,4)*100)}">{round((1+stats['UTES']['ret_0817']/100)*(1+stats['UTES']['ret_0818']/100)-1,4)*100:+.2f}%</td>
        <td>{stats['UTES']['close_0818']:.2f}</td>
        <td class="{cls(stats['UTES']['ret_5d'])}">{stats['UTES']['ret_5d']:+.2f}%</td>
        <td class="{cls(stats['UTES']['ret_20d'])}">{stats['UTES']['ret_20d']:+.2f}%</td>
        <td>{stats['UTES']['vol_ratio']:.2f}x</td>
        <td>{stats['UTES']['off_hi52']:.1f}%</td>
        <td>{stats['UTES']['off_lo52']:+.1f}%</td>
        <td class="na">-</td></tr>
      <tr style="background:#f8f9fb;"><td><b>SPY</b><br><span style="color:var(--sub);font-size:11px;">标普500</span></td>
        <td class="{cls(stats['SPY']['ret_0817'])}">{stats['SPY']['ret_0817']:+.2f}%</td>
        <td class="{cls(stats['SPY']['ret_0818'])}">{stats['SPY']['ret_0818']:+.2f}%</td>
        <td class="{cls(round((1+stats['SPY']['ret_0817']/100)*(1+stats['SPY']['ret_0818']/100)-1,4)*100)}">{round((1+stats['SPY']['ret_0817']/100)*(1+stats['SPY']['ret_0818']/100)-1,4)*100:+.2f}%</td>
        <td>{stats['SPY']['close_0818']:.2f}</td>
        <td class="{cls(stats['SPY']['ret_5d'])}">{stats['SPY']['ret_5d']:+.2f}%</td>
        <td class="{cls(stats['SPY']['ret_20d'])}">{stats['SPY']['ret_20d']:+.2f}%</td>
        <td>{stats['SPY']['vol_ratio']:.2f}x</td>
        <td>{stats['SPY']['off_hi52']:.1f}%</td>
        <td>{stats['SPY']['off_lo52']:+.1f}%</td>
        <td class="na">-</td></tr>
    </table>
    </div>
    <div class="note">* 跌幅罕见度 = 2025-01-01 以来，单日跌幅「小于等于」8/18 跌幅的交易日占比（越小越罕见）。TLN 0.7% ≈ 2025 年以来只有 0.7% 的交易日跌得像 8/18 这么狠。SPY 两日 −1.1%，而板块 −8% 上下 —— <b>大跌是板块事件，不是大盘事件</b>。</div>
    <div id="chart_daily" class="chart"></div>
    <div class="note">8/17（周一）板块已先行走弱（TLN −1.6% / NRG −3.1%），8/18 收益率升破 5.3% 后加速放量下杀 —— 典型「预期松动 → 催化落地」两段式。</div>
  </div>

  <div class="card">
    <h2>二、归因链条：三层共振</h2>
    <div class="flow">
      <div class="fnode" style="border-left-color:var(--amber);"><div class="ft">① 宏观：30Y 收益率创 18 年新高</div><div class="fs">美伊谈判停滞 + 霍尔木兹风险 → 油价 84-91 美元 → 通胀预期 → 全球债券抛售（法债 2008 来最高、德 30Y 2011 水平、英债近 6%）；30Y 盘中 5.32%+、10Y 升至 2025-01 以来高位</div></div>
      <div class="arrow">→</div>
      <div class="fnode" style="border-left-color:var(--purple);"><div class="ft">② 板块：AI 电力叙事再定价</div><div class="fs">高估值长久期主题在利率上行期遭集体抛售（纳指 −1.33%、SOXX −4.96%、CoreWeave −12%）；IPP 作为「AI 数据中心电力」贝塔被集中减仓 —— β 只解释 −0.8%，板块残差 −5.3pp</div></div>
      <div class="arrow">→</div>
      <div class="fnode" style="border-left-color:var(--red);"><div class="ft">③ 个股：TLN 叠加公司级利空</div><div class="fs">8/5 财报后目标价连环下调（RJ 463→449 / OpCo 440→400）+ $9.84 亿 shelf 注册 + 至少 1 家降级 Hold → 残差 −9.7pp、量比 3.1x</div></div>
    </div>
    <div id="chart_yield" class="chart"></div>
    <div class="note">左轴 = 板块等权归一化（2026-02-18=100）；右轴 = 30Y 美债收益率（FRED，8/17 收盘 5.31%，8/18 盘中 5.32%+）。2 月以来板块见顶回落与收益率持续抬升几乎镜像 —— <b>利率是这根压舱石</b>。</div>
  </div>

  <div class="card">
    <h2>三、量化分解：β 之外的 5.3 个百分点从哪来</h2>
    <div class="keypoint">
      <b>用 60 日滚动 β（对 SPY）做市场因子剥离：</b>板块 8/18 实际 −6.12%，其中市场因子（SPY −0.68% × β 1.22）只贡献 −0.82%，<b>剩下 −5.29pp 是板块自身的再定价</b> —— 即资金对「AI 电力需求 + 高估值」叙事的集中撤退，而不是大盘拖累。四只个股全部跑出显著负残差：TLN −9.7pp &gt; NRG −5.1pp &gt; CEG −3.4pp &gt; VST −3.0pp。
    </div>
    <div class="scroll">
    <table>
      <tr><th>标的</th><th>60日β</th><th>β期望跌幅</th><th>实际跌幅</th><th>残差(实际−β期望)</th><th>历史单日最差</th><th>1%分位跌幅</th><th>说明</th></tr>
      {rows2}
    </table>
    </div>
    <div id="chart_resid" class="chart sm"></div>
    <div class="note">柱 = 8/18 实际跌幅；绿点 = 仅按市场 β 应跌的幅度。TLN 残差最深：公司级利空（目标价下调 / shelf 注册 / 降级）与板块杀跌同时砸下；NRG 无个股新闻、纯板块拖累，但收在 52 周低点（距低 +0.0%）—— 弱势股在板块 beta 冲击下没有支撑。</div>
  </div>

  <div class="card">
    <h2>四、为什么体感「跌这么多」：三层放大</h2>
    <div class="step">
      <div class="st">1）单日跌幅罕见：TLN 是 2025 年以来 0.7% 分位的极端跌幅</div>
      <div class="sd">NRG 3.7%、CEG 8.1%、VST 10.3% —— 四只全线落在最差 10% 分位以内；TLN 自 2023-06 上市以来单日 −11% 只在 2024-08 股灾（−13.5%）附近出现过。</div>
    </div>
    <div class="step">
      <div class="st">2）两日累计、放量确认：不是尾盘一根针</div>
      <div class="sd">8/17→8/18 累计 TLN −12.4%、NRG −8.5%、CEG −5.6%、VST −5.1%；TLN 量比 3.1x、CEG 成交额放大 66% —— 抛压是真实的机构减仓而非流动性稀薄。</div>
    </div>
    <div class="step">
      <div class="st">3）相对位置：板块已从 2025 年 9-10 月见顶后阴跌一年</div>
      <div class="sd">距 52 周高：NRG −37% / VST −36% / CEG −34% / TLN −29%；2026 年内最大回撤 VST −25.2%、TLN −27.8%、CEG −35.4%、NRG −37.2%。<b>8/18 不是新趋势的起点，而是长期回调中又一段加速</b> —— 高位获利盘 + 高估值 + 利率上行，任何风吹草动都容易被放大。</div>
    </div>
    <div id="chart_norm" class="chart"></div>
    <div class="note">近 6 个月归一化（2026-02-18=100）：板块 2 月见顶后单边下行，XLU/SPY 同期横盘 —— 板块走的是自己的「AI 电力估值修正」行情；8 月中旬起所有标的同步拐头向下，正是收益率再上台阶（8/14 5.25% → 8/17 5.31%）的窗口。</div>
  </div>

  <div class="card">
    <h2>五、后续观察点</h2>
    <div class="warn">
      <b>多空各自的验证信号：</b><br>
      ① <b>收益率</b>：30Y 是否站稳 5.3% 上方（美债供给/财政赤字/通胀粘性）—— 只要长端利率不再创新高，板块估值压力就缓解；<br>
      ② <b>TLN shelf</b>：$9.84 亿注册是「存量股东减持」还是「新发股本」—— 落地规模与方式决定供给冲击持续多久；<br>
      ③ <b>NRG</b>：52 周低点 $112.5 是最后防线，板块企稳前弱势股会领跌；<br>
      ④ <b>叙事层</b>：AI 电力需求（超大规模厂商 PPA、负荷增长展望）是否被利率上升「证伪」—— 8/18 更像估值挤兑而非需求恶化，若后续仍有大额 PPA/电价上调公告，板块可快速修复；<br>
      ⑤ <b>板块内部</b>：CEG/VST 残差明显小于 TLN/NRG，且 CEG 20 日仍 +1.8% —— 本轮抛售主要砸「弹性/题材」而非「现金牛」，分化反而提供了相对强度信号。
    </div>
    <div class="dis">数据来源：Yahoo Finance 日线（前复权）、FRED DGS30、公开新闻（Finwire/MarketBeat/同花顺/新华财经等）。本报告为历史行情复盘，不构成投资建议。</div>
  </div>

</div>
<script>
  const daily = {js(daily)};
  const normDates = {js(norm_dates)};
  const normSeries = {js(norm_series)};
  const idxAvg = {js(idx_avg)};
  const dgs = {js(dgs30)};
  const rc = {js(resid_cat)};

  // 图1：两日跌幅
  const c1 = echarts.init(document.getElementById('chart_daily'));
  c1.setOption({{
    tooltip: {{trigger:'axis', axisPointer:{{type:'shadow'}}, valueFormatter: v => v + '%'}},
    legend: {{data:['8/17 周一','8/18 周二'], top:0}},
    grid: {{left:44,right:16,top:32,bottom:24}},
    xAxis: {{type:'category', data: daily.x, axisLabel:{{color:'#6b7280'}}}},
    yAxis: {{type:'value', axisLabel:{{formatter:'{{value}}%', color:'#6b7280'}}}},
    series: [
      {{name:'8/17 周一', type:'bar', data: daily.d17.map(v=>+v.toFixed(2)), itemStyle:{{color:'#9aa4b2', borderRadius:[4,4,0,0]}}, barGap:'20%'}},
      {{name:'8/18 周二', type:'bar', data: daily.d18.map(v=>+v.toFixed(2)), itemStyle:{{color:'#0aa06e', borderRadius:[4,4,0,0]}}}},
    ]
  }});

  // 图2：30Y 收益率 + 板块等权（双轴）
  const c2 = echarts.init(document.getElementById('chart_yield'));
  c2.setOption({{
    tooltip: {{trigger:'axis'}},
    legend: {{data:['板块等权(左)','30Y美债收益率(右)'], top:0}},
    grid: {{left:44,right:48,top:32,bottom:24}},
    xAxis: {{type:'category', data: normDates, axisLabel:{{color:'#6b7280', interval: Math.floor(normDates.length/8)}}}},
    yAxis: [
      {{type:'value', name:'板块等权(归一化)', axisLabel:{{color:'#6b7280'}}, splitLine:{{lineStyle:{{color:'#eef0f3'}}}}}},
      {{type:'value', name:'30Y %', min:4.5, max:5.6, axisLabel:{{color:'#b45309', formatter:'{{value}}'}}, splitLine:{{show:false}}}},
    ],
    series: [
      {{name:'板块等权(左)', type:'line', data: idxAvg, smooth:true, symbol:'none', lineStyle:{{width:2, color:'#7048e8'}}}},
      {{name:'30Y美债收益率(右)', type:'line', data: dgs.yield, smooth:true, symbol:'none', lineStyle:{{width:2, color:'#b45309', type:'dashed'}}}},
    ]
  }});

  // 图3：个股 β 分解
  const c3 = echarts.init(document.getElementById('chart_resid'));
  c3.setOption({{
    tooltip: {{trigger:'axis', axisPointer:{{type:'shadow'}}, valueFormatter: v => v + '%'}},
    legend: {{data:['实际跌幅','β期望跌幅'], top:0}},
    grid: {{left:44,right:16,top:32,bottom:24}},
    xAxis: {{type:'category', data: rc.x, axisLabel:{{color:'#6b7280'}}}},
    yAxis: {{type:'value', axisLabel:{{formatter:'{{value}}%', color:'#6b7280'}}}},
    series: [
      {{name:'实际跌幅', type:'bar', data: rc.actual.map(v=>+v.toFixed(2)), itemStyle:{{color:'#0aa06e', borderRadius:[4,4,0,0]}}, label:{{show:true, position:'top', formatter:p=>p.value+'%', color:'#0aa06e', fontWeight:700}}}},
      {{name:'β期望跌幅', type:'bar', data: rc.expected.map(v=>+v.toFixed(2)), itemStyle:{{color:'#e8d9f7'}}, barGap:'30%'}},
    ]
  }});

  // 图4：近 6 个月归一化
  const c4 = echarts.init(document.getElementById('chart_norm'));
  c4.setOption({{
    tooltip: {{trigger:'axis'}},
    legend: {{data: normSeries.map(s=>s.name), top:0, type:'scroll'}},
    grid: {{left:44,right:16,top:32,bottom:24}},
    xAxis: {{type:'category', data: normDates, axisLabel:{{color:'#6b7280', interval: Math.floor(normDates.length/8)}}}},
    yAxis: {{type:'value', axisLabel:{{formatter:'{{value}}', color:'#6b7280'}}}},
    series: normSeries.map(s => ({{
      name: s.name, type:'line', data: s.data, smooth:true, symbol:'none',
      lineStyle: {{width: s.dashed ? 1.5 : 2, color: s.color, type: s.dashed ? 'dashed' : 'solid'}},
    }}))
  }});

  window.addEventListener('resize', () => [c1,c2,c3,c4].forEach(c=>c.resize()));
</script>
</body>
</html>
"""

out_path = os.path.join(OUT, "ipp_drop_0818_report.html")
with open(out_path, "w") as f:
    f.write(html)
print("已生成:", out_path, len(html), "字节")
