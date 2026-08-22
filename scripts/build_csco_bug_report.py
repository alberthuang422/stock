# -*- coding: utf-8 -*-
"""CSCO × BUG 相关性研报生成器（读 results/csco_bug_corr.json，仅 2026 年以来）"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "19_csco_bug网络安全")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "csco_bug_corr.json"), encoding="utf-8") as f:
    P = json.load(f)


def js(o):
    return json.dumps(o, ensure_ascii=False)


# ---------- 提取 ----------
win = P["window"]
cum = P["cum"]
ex = P["excess"]
stats = P["stats"]
cf = P["corr_full"]
cr60 = P["corr_roll"]
monthly = P["monthly"]
seesaw = P["seesaw"]
ratio = P["ratio"]
beta = P["beta"]
big_days = P["big_days"]
norm = P["norm_series"]
roll = P["roll_chart"]
rc = P["ratio_chart"]

# ---------- 表格行 ----------
mon_rows = ""
for m in monthly:
    def cls(v):
        return "up" if v > 0 else ("dn" if v < 0 else "")
    def fv(v, sign=True):
        if v is None:
            return '<td class="na">-</td>'
        s = f"{v:+.2f}%" if sign else f"{v:.2f}%"
        return f'<td class="{cls(v)}">{s}</td>'
    corr_txt = "—" if m["corr_cb"] is None else f"{m['corr_cb']:.2f}"
    mon_rows += f"""<tr>
      <td><b>{m['month']}</b></td>
      {fv(m['ret_csco'])}
      {fv(m['ret_bug'])}
      {fv(m['ret_spy'])}
      <td>{corr_txt}</td>
      <td>{m['n']}</td>
    </tr>"""

big_up = [d for d in big_days if d["type"] == "up"]
big_dn = [d for d in big_days if d["type"] == "dn"]

def stat_mean(grp, k):
    if not grp:
        return None
    return sum(d[k] for d in grp) / len(grp)

def med(grp, k):
    if not grp:
        return None
    vals = sorted(d[k] for d in grp)
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2

def same_rate(grp):
    if not grp:
        return None
    return sum(1 for d in grp if (d["bug"] > 0) == (d["csco"] > 0)) / len(grp)

def fmtp(v, sign=True):
    if v is None:
        return "—"
    return f"{v:+.2f}%" if sign else f"{v:.2f}%"

up_stats = {"n": len(big_up), "mean": stat_mean(big_up, "csco"), "med": med(big_up, "csco"), "same": same_rate(big_up)}
dn_stats = {"n": len(big_dn), "mean": stat_mean(big_dn, "csco"), "med": med(big_dn, "csco"), "same": same_rate(big_dn)}

big_rows = ""
for d in big_days[:14]:
    def bcls(v):
        return "up" if v > 0 else ("dn" if v < 0 else "")
    big_rows += f"""<tr>
      <td>{d['date']}</td>
      <td style="font-weight:700;color:{'var(--red)' if d['bug']>0 else 'var(--green)'};">{d['bug']:+.1f}%</td>
      <td class="{bcls(d['csco'])}">{d['csco']:+.1f}%</td>
      <td class="{bcls(d['spy'])}">{d['spy']:+.1f}%</td>
      <td>{'同步' if (d['bug']>0)==(d['csco']>0) else '背离'}</td>
    </tr>"""

# ---------- 图表数据 ----------
norm_dates = norm["csco"]["dates"]
norm_series = [
    {"name": "CSCO", "data": norm["csco"]["values"], "color": "#1e66d6"},
    {"name": "BUG", "data": norm["bug"]["values"], "color": "#7048e8"},
    {"name": "SPY", "data": norm["spy"]["values"], "color": "#9aa2ad", "dash": True},
]

roll_dates = roll["dates"]

# 月度柱状图数据
mon_dates = [m["month"] for m in monthly]
mon_csco = [m["ret_csco"] if m["ret_csco"] is not None else None for m in monthly]
mon_bug = [m["ret_bug"] if m["ret_bug"] is not None else None for m in monthly]
mon_spy = [m["ret_spy"] if m["ret_spy"] is not None else None for m in monthly]
mon_corr = [m["corr_cb"] if m["corr_cb"] is not None else None for m in monthly]

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSCO × BUG · 2026相关性分析 · 网络安全主题的「同涨不同频」</title>
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
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}}
  .kpi{{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
  .kpi .num{{font-size:20px;font-weight:700;}}
  .kpi .num.up{{color:var(--red);}} .kpi .num.dn{{color:var(--green);}}
  .kpi .lab{{color:var(--sub);font-size:12px;margin-top:2px;}}
  .verdict{{background:linear-gradient(135deg,#f6f3ff,#eef7f2);border:1px solid #e0d9f5;border-radius:12px;padding:16px 20px;margin-top:14px;}}
  .verdict .t{{font-size:13px;color:var(--sub);margin-bottom:6px;}}
  .verdict .b{{font-size:15.5px;font-weight:700;color:var(--ink);}}
  .verdict .b .hl{{color:var(--purple);}} .verdict .b .hlb{{color:var(--blue);}} .verdict .b .hlr{{color:var(--red);}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;}}
  th{{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}}
  td{{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}}
  td.up{{color:var(--red);font-weight:600;}} td.dn{{color:var(--green);font-weight:600;}} td.na{{color:#c3c8cf;}}
  .scroll{{overflow-x:auto;}}
  .chart{{width:100%;height:380px;}}
  .chart.sm{{height:320px;}}
  .note{{color:var(--sub);font-size:12px;margin-top:8px;}}
  .keypoint{{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}}
  .hl-box{{background:#fff3f3;border:1px solid #f5d5d5;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#8c2f2f;margin-top:10px;}}
  .warn{{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;}}
  .dis{{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}}
  .hl{{font-weight:700;color:var(--red);}} .hlg{{font-weight:700;color:var(--green);}} .hlb{{font-weight:700;color:var(--blue);}} .hlp{{font-weight:700;color:var(--purple);}}
  .tag{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}}
  .tag.csco{{background:#eef3fb;color:var(--blue);}} .tag.bug{{background:#f0edfb;color:var(--purple);}} .tag.spy{{background:#f0f1f3;color:#6b7280;}}
  .statline{{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;}}
  .stat{{background:#fbfcfe;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:12.5px;}}
  .stat b{{font-size:14px;}}
  .bigbar{{display:flex;flex-direction:column;gap:6px;margin-top:10px;}}
  .brow{{display:flex;align-items:center;gap:10px;font-size:12px;}}
  .binfo{{flex:none;width:230px;color:var(--sub);}}
  .btrack{{flex:1;background:#f3f5f8;border-radius:6px;height:20px;position:relative;overflow:hidden;}}
  .bfill{{position:absolute;top:0;bottom:0;border-radius:6px 0 0 6px;}}
  .blab{{flex:none;width:170px;font-weight:600;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>CSCO × BUG · 2026 相关性分析<br><span style="font-size:15px;color:var(--sub);font-weight:500;">网络安全主题的「同涨不同频」—— 思科与网络安全 ETF 的 159 个交易日解剖</span></h1>
    <div class="meta">窗口：{win['start']} ~ {win['end']}（{win['n']} 个交易日，Yahoo 前复权日线）｜BUG = Global X Cybersecurity ETF（网络安全主题）｜对照：SPY（大盘）｜行情截至 2026-08-20</div>

    <div class="verdict">
      <div class="t">▍一句话结论</div>
      <div class="b">2026 年 CSCO（<span class="hlr">+{cum['csco']*100:.1f}%</span>）与 BUG（<span class="hlr">+{cum['bug']*100:.1f}%</span>）双双大幅跑赢大盘（+{cum['spy']*100:.1f}%），但两者日收益相关仅 <span class="hlb">{cf['csco_bug']:.2f}</span>，甚至低于 CSCO 与 SPY 的相关（{cf['csco_spy']:.2f}）——<span class="hlp">同涨 ≠ 同步：CSCO 的上涨由个股自身驱动（4 月 +17.3%、5 月 +28.7% 但两月内相关仅 0.14），与网络安全主题（BUG）几乎不共振；BUG 的波动主要由自身主题风险驱动（2 月 −12.4% 时 CSCO 仅 −2.1% 不受牵连）。</span>整体看 CSCO 是「借了 AI 网络设备东风的安全硬件商」，BUG 是「纯主题 β」，两者的交集远小于多数人直觉。</div>
    </div>

    <div class="kpis">
      <div class="kpi"><div class="num">{cf['csco_bug']:.2f}</div><div class="lab">日收益相关 CSCO×BUG（2026）</div></div>
      <div class="kpi"><div class="num" style="color:var(--blue);">{cf['csco_spy']:.2f}</div><div class="lab">CSCO×SPY（对照）</div></div>
      <div class="kpi"><div class="num up">+{cum['csco']*100:.0f}%</div><div class="lab">CSCO 2026 YTD</div></div>
      <div class="kpi"><div class="num up">+{cum['bug']*100:.0f}%</div><div class="lab">BUG 2026 YTD</div></div>
      <div class="kpi"><div class="num" style="color:var(--amber);">{seesaw*100:.0f}%</div><div class="lab">日方向相反天数占比（跷跷板）</div></div>
      <div class="kpi"><div class="num" style="color:var(--purple);">0.11</div><div class="lab">滚动60日相关·最新</div></div>
    </div>
    <div class="statline">
      <div class="stat">CSCO 最大回撤 <b>{stats['csco']['max_drawdown']*100:.1f}%</b> · 年化波动 <b>{stats['csco']['ann_vol']*100:.0f}%</b></div>
      <div class="stat">BUG 最大回撤 <b>{stats['bug']['max_drawdown']*100:.1f}%</b> · 年化波动 <b>{stats['bug']['ann_vol']*100:.0f}%</b></div>
      <div class="stat">β CSCO~BUG <b>{beta['csco_bug']:.2f}</b> · CSCO~SPY <b>{beta['csco_spy']:.2f}</b></div>
    </div>
  </div>

  <div class="card">
    <h2>标的背景：为什么这组对比有意义？</h2>
    <div class="keypoint">
      <b>CSCO</b> —— 全球网络设备龙头，2026 年演绎「AI 网络设备」逻辑：数据中心交换机的 AI 升级周期 + 安全业务（Splunk）协同，年内 +{cum['csco']*100:.1f}%。市场有时把它当「基础设施硬件」、有时把它当「网络安全股」、有时把它当「AI 受益者」，三个身份的相关结构完全不同。<br><br>
      <b>BUG</b> —— Global X Cybersecurity ETF，跟踪 Indxx Cybersecurity Index，持仓以纯网络安全软件/服务商为主（Palo Alto、CrowdStrike、Zscaler、Fortinet 等约 40 只）。它是「网络安全主题 β」的干净代理。<br><br>
      <b>核心问题</b>：市场常把 CSCO 与网络安全主题混为一谈（CSCO 自身也有安全业务），但两者 2026 年的日收益相关实际只有 <b class="hlb">{cf['csco_bug']:.2f}</b> —— 若把 CSCO 当网络安全股对冲/配置，这个相关水平可能低于预期。
    </div>
  </div>

  <div class="card">
    <h2>一、2026 全景：同涨但不同频</h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note">归一化（2026-01-02 = 1）：CSCO +{cum['csco']*100:.1f}%、BUG +{cum['bug']*100:.1f}%、SPY +{cum['spy']*100:.1f}%。CSCO 的斜率变化集中在 4-5 月两次拉升（4 月 +17.3%：AI 网络订单周期；5 月 +28.7%：与 BUG 同步冲高但日相关仅 0.14），BUG 则 2 月深蹲（−12.4%）后 5 月才跟上。两者节奏差明显：<b>CSCO 先行、BUG 后至，且 8 月反向（CSCO −5.1% vs BUG +5.7%，月内相关 −0.01）</b>。</div>
  </div>

  <div class="card">
    <h2>二、相关性：日相关 0.19，滚动 60 日仅 0.11 且一路走低</h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note">滚动 60 日相关（CSCO×BUG 紫 / CSCO×SPY 蓝）：① 全期均值仅 0.22，2026 年以来从未突破 0.31；② <b>近期反而持续走低至 0.11（8 月相关已转负/近零）</b>——BUG 8 月 +5.7% 时 CSCO 下跌，主题与个股再次脱钩；③ CSCO×SPY 相关（约 0.40 稳定）始终高于 CSCO×BUG —— <b>CSCO 在 2026 年更像「大盘+α 股」而非「网络安全主题股」</b>。</div>
    <h3>月度收益与月内相关（红涨绿跌）</h3>
    <div id="chart_mon" class="chart sm"></div>
    <div class="scroll">
    <table>
      <thead><tr><th>月份</th><th>CSCO</th><th>BUG</th><th>SPY</th><th>月内日相关 C×B</th><th>交易日</th></tr></thead>
      <tbody>{mon_rows}</tbody>
    </table>
    </div>
    <div class="note">月内相关口径 = 当月所有交易日的日收益皮尔逊相关。8 月是唯一转负的月份（−0.01）：BUG 涨而 CSCO 跌。4 月相关 0.37 是峰值，但仍属中低水平。</div>
  </div>

  <div class="card">
    <h2>三、跷跷板与极端日：主题大涨日 CSCO 只跟一半</h2>
    <div class="statline">
      <div class="stat">方向相反天数占比 <b>{seesaw*100:.1f}%</b>（159 日中 {int(seesaw*win['n'])} 天 CSCO 与 BUG 反向）</div>
      <div class="stat">BUG 大涨日（|≥2%|，{up_stats['n']} 天）：CSCO 均值 <b class="hl">{fmtp(up_stats['mean'])}</b> · 同向率 <b>{up_stats['same']*100:.0f}%</b></div>
      <div class="stat">BUG 大跌日（{dn_stats['n']} 天）：CSCO 均值 <b class="hlg">{fmtp(dn_stats['mean'])}</b> · 同向率 <b>{dn_stats['same']*100:.0f}%</b></div>
    </div>
    <h3>BUG 单日 |涨跌| ≥ 2% 明细（按日期倒序，最多显示 14 天）</h3>
    <div class="scroll">
    <table>
      <thead><tr><th>日期</th><th>BUG</th><th>CSCO</th><th>SPY</th><th>同步/背离</th></tr></thead>
      <tbody>{big_rows}</tbody>
    </table>
    </div>
    <div class="note">BUG 出现 ±2% 以上剧烈波动的交易日共 {len(big_days)} 天（占 2026 全部交易日约 {len(big_days)/win['n']*100:.0f}%），高波动本身说明 BUG 是典型主题 ETF。但在这些极端日里 CSCO 同向率仅 57~62% —— <b>约 4 成的极端主题波动日 CSCO 完全不受影响，验证了两者的弱联动</b>。</div>
  </div>

  <div class="card">
    <h2>四、相对强弱：CSCO 上半年占优，5 月下旬起 BUG 反超</h2>
    <div id="chart_ratio" class="chart sm"></div>
    <div class="note">CSCO/BUG 归一化比值（2026-01-02 = 1）：CSCO 在 4-5 月中旬单边占优（5/15 峰值 1.47，即 CSCO 相对 BUG 多涨 47%），5 月下旬起 BUG 追赶反超，当前 1.08 —— 二者 2026 年整体涨幅几乎拉平，但路径完全不同。</div>
  </div>

  <div class="card">
    <h2>五、结论：同涨 ≠ 同步，三个层次看两者关系</h2>
    <div class="keypoint">
      <b>① 方向层（一致）</b>：2026 年都是 AI 网络安全需求上行周期的受益者，都大幅跑赢大盘（CSCO +{ex['csco_vs_spy']*100:+.0f}pp、BUG +{ex['bug_vs_spy']*100:+.0f}pp）——「中期趋势同向」成立。<br><br>
      <b>② 节奏层（不同步）</b>：日收益相关仅 0.19、滚动 60 日降至 0.11，月度节奏错位明显（2 月 BUG 深蹲 CSCO 无恙、5 月同涨但日相关低、8 月反向）。<b>CSCO 由个股 α 主导（AI 交换机的订单/财报驱动），BUG 由主题 β 主导（网络安全板块的资金流/情绪驱动），两者的「驱动器」不同。</b><br><br>
      <b>③ 结构层（长期）</b>：CSCO 的 β 结构更接近 SPY（1.15）+ 个股 α，BUG 的 β 结构更接近主题板块（波动 38% 接近 CSCO 但相关与 CSCO 仅 0.19）。<b>若把 CSCO 当作网络安全主题的替代持仓或对冲工具，0.19 的相关意味着几乎起不到对冲作用；要表达网络安全主题，BUG 是更纯净的工具。</b>
    </div>
    <div class="hl-box">
      <b>对投资者的含义：</b>① CSCO 2026 的上涨本质是「AI 数据中心资本开支 + 网络设备周期」逻辑，不是网络安全主题逻辑（其安全业务 Splunk 只是副线）；② 想投网络安全主题，CSCO 不是合格代理（相关 0.19、且对主题大跌日仅约 6 成同向）；③ 两个标的都涨背后是同一宏观背景（AI 开支+数字化安全需求），但作为交易品种它们 2026 年的日频联动远弱于直觉 —— 分散配置的意义比想象中更大。
    </div>
  </div>

  <div class="card">
    <div class="dis">
      数据来源：Yahoo Finance 日线（2026-01-02 ~ 2026-08-20，前复权 adj_close）；BUG = Global X Cybersecurity ETF（Indxx Cybersecurity Index）。相关/β/跷跷板均为日收益口径；β 为 CSCO 对 BUG / SPY 的 OLS 斜率；「BUG 大涨/大跌日」为单日收益绝对值 ≥2% 的交易日。月内相关样本量约 20 个交易日，噪声较大。
    </div>
    <div class="dis" style="margin-top:8px;">
      <b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
    </div>
  </div>

</div>
<script>
// ---------- 图1 归一化净值 ----------
(function(){{
  var c = document.getElementById('chart_norm');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['CSCO', 'BUG', 'SPY'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(norm_dates)} }},
    yAxis: {{ type: 'value', name: '归一化(2026-01-02=1)', scale: true }},
    series: {js(norm_series)}.map(function(s){{
      return {{
        name: s.name, type: 'line', showSymbol: false, smooth: false,
        data: s.data, lineStyle: {{ width: s.dash ? 1.5 : 2, type: s.dash ? 'dashed' : 'solid', color: s.color }},
        itemStyle: {{ color: s.color }}
      }};
    }})
  }});
}})();

// ---------- 图2 滚动60日相关 ----------
(function(){{
  var c = document.getElementById('chart_roll');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return v === null ? '-' : v.toFixed(2); }} }},
    legend: {{ data: ['CSCO×BUG', 'CSCO×SPY'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(roll_dates)} }},
    yAxis: {{ type: 'value', name: '滚动相关', min: -0.2, max: 0.8 }},
    series: [
      {{ name: 'CSCO×BUG', type: 'line', showSymbol: false, smooth: true, data: {js(roll['cb60'])},
         lineStyle: {{ width: 2.5, color: '#7048e8' }}, itemStyle: {{ color: '#7048e8' }},
         areaStyle: {{ color: 'rgba(112,72,232,.10)' }},
         markLine: {{ data: [{{ yAxis: {cf['csco_bug']:.3f}, name: '全期0.19', lineStyle: {{ type: 'dashed', color: '#7048e8' }} }}] }} }},
      {{ name: 'CSCO×SPY', type: 'line', showSymbol: false, smooth: true, data: {js(roll['cs60'])},
         lineStyle: {{ width: 2, color: '#1e66d6' }}, itemStyle: {{ color: '#1e66d6' }},
         markLine: {{ data: [{{ yAxis: {cf['csco_spy']:.3f}, name: '全期0.40', lineStyle: {{ type: 'dashed', color: '#1e66d6' }} }}] }} }}
    ]
  }});
}})();

// ---------- 图3 月度收益（红涨绿跌） ----------
(function(){{
  var c = document.getElementById('chart_mon');
  if (!c) return;
  var ch = echarts.init(c);
  var colors = {{ 'CSCO': '#1e66d6', 'BUG': '#7048e8', 'SPY': '#9aa2ad' }};
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return v === null ? '-' : v + '%'; }} }},
    legend: {{ data: ['CSCO', 'BUG', 'SPY'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(mon_dates)} }},
    yAxis: {{ type: 'value', name: '月度收益 %' }},
    series: [
      {{ name: 'CSCO', type: 'bar', barGap: 0.15, data: {js(mon_csco)}.map(function(v){{ return {{ value: v, itemStyle: {{ color: v >= 0 ? colors['CSCO'] : '#d64545' }} }}; }}) }},
      {{ name: 'BUG', type: 'bar', barGap: 0.15, data: {js(mon_bug)}.map(function(v){{ return {{ value: v, itemStyle: {{ color: v >= 0 ? colors['BUG'] : '#d64545' }} }}; }}) }},
      {{ name: 'SPY', type: 'line', showSymbol: false, smooth: true, data: {js(mon_spy)}, lineStyle: {{ width: 2, color: '#9aa2ad' }} }}
    ]
  }});
}})();

// ---------- 图4 相对强弱 ----------
(function(){{
  var c = document.getElementById('chart_ratio');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return v.toFixed(3); }} }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(rc['dates'])} }},
    yAxis: {{ type: 'value', name: 'CSCO/BUG (2026-01=1)', scale: true }},
    series: [{{
      name: 'CSCO/BUG 相对强弱', type: 'line', showSymbol: false, smooth: true,
      data: {js(rc['values'])},
      lineStyle: {{ width: 2.5, color: '#b45309' }},
      areaStyle: {{ color: 'rgba(180,83,9,.10)' }},
      markLine: {{ data: [{{ yAxis: 1, lineStyle: {{ type: 'dashed', color: '#9aa2ad' }} }}] }}
    }}]
  }});
}})();
</script>
</body>
</html>
"""

out_file = os.path.join(OUT, "csco_bug_corr_report.html")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_file} size={os.path.getsize(out_file)}")