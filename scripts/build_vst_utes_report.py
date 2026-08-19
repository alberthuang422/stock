# -*- coding: utf-8 -*-
"""VST × UTES 分阶段相关性研报生成器（读 results/vst_utes_phase.json）"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "reports", "05_vst_utes")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "vst_utes_phase.json")) as f:
    P = json.load(f)


def js(o):
    return json.dumps(o, ensure_ascii=False)


# ---------- 提取 ----------
norm = P["norm_series"]
roll = P["roll_chart"]
yearly = P["yearly"]
phases = P["phases"]
cum = P["cum"]
ratio = P["ratio"]
rc = P["ratio_chart"]
corr_full = P["corr_full"]
corr_roll = P["corr_roll"]
win = P["window"]

# 归一化图
norm_dates = norm["vst"]["dates"]
norm_series = [
    {"name": "VST", "data": norm["vst"]["values"], "color": "#c05c0b"},
    {"name": "UTES", "data": norm["utes"]["values"], "color": "#1e66d6"},
    {"name": "XLU", "data": norm["xlu"]["values"], "color": "#0aa06e"},
]

# 阶段色带（markArea）
phase_mark = []
for ph in phases:
    phase_mark.append([
        {"xAxis": ph["p0"], "itemStyle": {"color": "rgba(112,72,232,0.06)"}},
        {"xAxis": ph["p1"]},
    ])

# 分阶段指标表行
phase_rows = ""
for ph in phases:
    def pct(v, signed=True):
        if v is None:
            return '<td class="na">-</td>'
        s = f"{v*100:+.1f}%" if signed else f"{v*100:.1f}%"
        cls = "up" if v > 0 else ("dn" if v < 0 else "")
        return f'<td class="{cls}">{s}</td>'

    def num(v, fmt="{:.2f}"):
        return f'<td>{fmt.format(v)}</td>' if v is not None else '<td class="na">-</td>'

    phase_rows += f"""<tr>
      <td><b>{ph['id']}</b></td>
      <td style="white-space:normal;min-width:150px;"><b>{ph['label']}</b><br><span style="color:var(--sub);font-size:11px;">{ph['sub']}</span></td>
      <td>{ph['n']}</td>
      {num(ph['corr_vu'], "{:.2f}")}
      {num(ph['corr_vx'], "{:.2f}")}
      {num(ph['beta'], "{:.2f}")}
      <td>{ph['seesaw']*100:.1f}%</td>
      {pct(ph['ret_vst'])}
      {pct(ph['ret_utes'])}
      {pct(ph['ret_xlu'])}
      {pct(ph['excess'])}
      <td>{ph['win_days']*100:.0f}%</td>
    </tr>"""

# 年度表
year_rows = ""
for y in yearly:
    def ycls(v):
        return "up" if v > 0 else ("dn" if v < 0 else "")
    year_rows += f"""<tr>
      <td><b>{y['year']}</b></td>
      <td>{y['corr_vu']:.2f}</td>
      <td>{y['corr_vx']:.2f}</td>
      <td class="{ycls(y['vst'])}">{y['vst']:+.1f}%</td>
      <td class="{ycls(y['utes'])}">{y['utes']:+.1f}%</td>
      <td class="{ycls(y['xlu'])}">{y['xlu']:+.1f}%</td>
      <td class="{ycls(y['vst'] - y['utes'])}">{y['vst'] - y['utes']:+.1f}pp</td>
    </tr>"""

# 阶段解读卡片
phase_cards = ""
for i, ph in enumerate(phases):
    # 卡片高亮色交替
    acc = ["var(--purple)", "var(--blue)", "var(--amber)", "var(--red)", "var(--green)"][i % 5]
    def pct2(v, signed=True):
        if v is None:
            return "-"
        return f"{v*100:+.1f}%" if signed else f"{v*100:.1f}%"
    phase_cards += f"""
    <div class="phcard" style="border-left:4px solid {acc};">
      <div class="phtag" style="background:{acc};">{ph['id']}</div>
      <div class="phtitle">{ph['label']} <span class="phsub">{ph['sub']}</span></div>
      <div class="phbody">
        <span class="chip">相关 {ph['corr_vu']:.2f}</span>
        <span class="chip">β {ph['beta']:.2f}</span>
        <span class="chip">跷跷板 {ph['seesaw']*100:.1f}%</span>
        <span class="chip" style="color:{'var(--red)' if ph['excess']>0 else 'var(--green)'};">超额 {pct2(ph['excess'])}</span>
        <div class="phevent">{ph['event']}</div>
        <div class="phnums">
          <span>VST <b style="color:{'var(--red)' if ph['ret_vst']>0 else 'var(--green)'};">{pct2(ph['ret_vst'])}</b></span>
          <span>UTES <b style="color:{'var(--red)' if ph['ret_utes']>0 else 'var(--green)'};">{pct2(ph['ret_utes'])}</b></span>
          <span>XLU <b style="color:{'var(--red)' if ph['ret_xlu']>0 else 'var(--green)'};">{pct2(ph['ret_xlu'])}</b></span>
          <span>年化波动 V/U <b>{ph['ann_vol_v']*100:.0f}%/{ph['ann_vol_u']*100:.0f}%</b></span>
        </div>
      </div>
    </div>"""

# 年度收益图数据
years_list = [y["year"] for y in yearly]
year_series = [
    {"name": "VST", "data": [y["vst"] for y in yearly]},
    {"name": "UTES", "data": [y["utes"] for y in yearly]},
    {"name": "XLU", "data": [y["xlu"] for y in yearly]},
]

# 分阶段相关/β 图数据
phase_ids = [ph["id"] for ph in phases]
phase_corr = [ph["corr_vu"] for ph in phases]
phase_beta = [ph["beta"] for ph in phases]
phase_excess = [round(ph["excess"] * 100, 1) if ph["excess"] is not None else None for ph in phases]

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VST × UTES · 分阶段相关性演化 · 从板块成员到板块放大器</title>
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
  .warn{{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;}}
  .dis{{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}}
  .hl{{font-weight:700;color:var(--red);}} .hlg{{font-weight:700;color:var(--green);}} .hlb{{font-weight:700;color:var(--blue);}} .hlp{{font-weight:700;color:var(--purple);}}
  .tag{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}}
  .tag.vst{{background:#fdf1e7;color:#c05c0b;}} .tag.utes{{background:#eef3fb;color:var(--blue);}} .tag.xlu{{background:#e9f7f1;color:#0a7a54;}}
  .phcard{{display:flex;gap:12px;background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-top:10px;align-items:flex-start;}}
  .phtag{{flex:none;color:#fff;font-weight:800;font-size:12px;border-radius:6px;padding:3px 9px;margin-top:2px;}}
  .phtitle{{font-weight:700;font-size:14px;}}
  .phsub{{color:var(--sub);font-weight:500;font-size:12px;margin-left:6px;}}
  .phbody{{flex:1;}}
  .chip{{display:inline-block;background:#fff;border:1px solid var(--line);border-radius:12px;padding:1px 10px;font-size:12px;margin-right:6px;margin-bottom:4px;font-weight:600;}}
  .phevent{{color:var(--sub);font-size:12.5px;margin-top:6px;}}
  .phnums{{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--sub);margin-top:8px;}}
  .timeline{{display:flex;gap:0;margin-top:14px;overflow-x:auto;padding-bottom:6px;}}
  .tseg{{flex:1;min-width:110px;border-radius:8px;padding:8px 10px;color:#fff;font-size:12px;}}
  .tseg .t{{font-weight:700;}} .tseg .s{{opacity:.85;font-size:11px;}}
  .hl-box{{background:#fff3f3;border:1px solid #f5d5d5;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#8c2f2f;margin-top:10px;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>VST × UTES · 分阶段相关性演化<br><span style="font-size:15px;color:var(--sub);font-weight:500;">从「板块成员」到「板块放大器」—— 个股与公用事业板块的八年关系变迁</span></h1>
    <div class="meta">窗口：{win['start']} ~ {win['end']}（{win['n']} 个交易日，Yahoo 前复权日线）｜UTES = Virtus Reaves Utilities ETF（主动管理公用事业 ETF，2026-04 前三大持仓 CEG 10.6% / VST 10.5% / TLN 10.1%）｜对照：XLU（S&amp;P 500 Utilities）｜行情截至 2026-08-14</div>

    <div class="verdict">
      <div class="t">▍一句话结论</div>
      <div class="b">VST 与 UTES 的日收益相关从 2018 年的 <span class="hlp">0.15 一路爬升到 2025 年峰值 0.89</span>（最新 0.76），8 年完成从「板块普通成员」到「板块放大器」（β 从 0.84 → 2.41）的质变；但 VST 与更宽的 XLU 相关始终只有 0.4 上下 —— <span class="hlp">高相关不是来自「公用事业板块」，而是来自 UTES 把 CEG/VST/TLN 这些 IPP 加仓到前三大重仓</span>。且超额收益与相关性负相关：<b>低相关期（S2/S3）VST 赚走全部 α（+276pp 超额），高相关期（S4/S5）VST 只剩 β 放大、一旦回调跌得更深。</b></div>
    </div>

    <div class="kpis">
      <div class="kpi"><div class="num">0.63</div><div class="lab">全期日收益相关 VST×UTES</div></div>
      <div class="kpi"><div class="num" style="color:var(--blue);">0.43</div><div class="lab">全期 VST×XLU（板块纯暴露参照）</div></div>
      <div class="kpi"><div class="num" style="color:var(--purple);">0.89 → 0.76</div><div class="lab">相关峰值 2025 → 滚动60日最新</div></div>
      <div class="kpi"><div class="num up">+{cum['vst']*100:.0f}%</div><div class="lab">VST 全期累计收益（2018 起）</div></div>
      <div class="kpi"><div class="num up">+{cum['utes']*100:.0f}%</div><div class="lab">UTES 同区间累计收益</div></div>
      <div class="kpi"><div class="num" style="color:var(--amber);">0.84 → 2.41</div><div class="lab">β 演化：S1 → S4（放大器化）</div></div>
    </div>
  </div>

  <div class="card">
    <h2>标的说明：为什么这组对比有意义？</h2>
    <div class="keypoint">
      <b>UTES 不是传统公用事业 ETF。</b> Virtus Reaves 是主动管理型，2026-04 前三大持仓是 <span class="tag vst">VST 10.5%</span><span class="tag utes">CEG 10.6%</span><span class="tag utes">TLN 10.1%</span> —— 三个都是 AI 电力概念 IPP（独立发电商），合计约 31%；传统公用事业（XEL/CNP/ETR/LNT/SRE/NRG/NEE）合计约 40%。它本质是「被发电商重塑的公用事业 ETF」。<br><br>
      <b>⚠ 自包含效应：</b>VST 是 UTES 第二大重仓（约 10.5%），「个股 vs 含自身的组合」相关天然偏高。因此报告全程给出 <span class="hlb">VST×XLU</span> 作为「更纯净的板块暴露」对照：全期 0.43 vs 0.63，两者之差（约 +0.2）就是 UTES 对 VST 的「专属重仓溢价」。
    </div>
    <div class="timeline">
      <div class="tseg" style="background:#7d8aa5;">S1 板块成员期<br><span class="s">2018.01~2021.02<br>相关 0.50 · β 0.84</span></div>
      <div class="tseg" style="background:#5c6b8a;">S2 风暴冲击期<br><span class="s">2021.03~2022.10<br>相关 0.54 · β 0.99</span></div>
      <div class="tseg" style="background:#3e7cb1;">S3 叙事发酵期<br><span class="s">2022.11~2024.08<br>相关 0.51 · β 1.15</span></div>
      <div class="tseg" style="background:#8a4fc7;">S4 主升浪<br><span class="s">2024.09~2025.12<br>相关 0.89 · β 2.41</span></div>
      <div class="tseg" style="background:#c76a4f;">S5 回调分化<br><span class="s">2026.01~至今<br>相关 0.83 · β 1.84</span></div>
    </div>
    <div class="note">阶段划分 = 事件驱动（德州暴风雪 / ChatGPT / 三里岛 PPA / AWS PPA / 2026 回调）+ 滚动相关结构双确认。断点与滚动相关爬升路径高度吻合。</div>
  </div>

  <div class="card">
    <h2>一、八年全景：VST 独自跑出 8 倍，相关性同步「追上来」</h2>
    <div id="chart_norm" class="chart"></div>
    <div class="note">归一化（2018-01-02=1）：VST 全期 +{cum['vst']*100:.0f}%、UTES +{cum['utes']*100:.0f}%、XLU +{cum['xlu']*100:.0f}%。三段式：2018-2022 跟板块横盘磨底 → 2023-2024 独立爆发（+256pp 超额，相关反而没跟上）→ 2024.09 后 UTES 重仓 IPP，两者开始同频起舞。</div>
  </div>

  <div class="card">
    <h2>二、相关性演化：0.15 → 0.89 的八年爬坡</h2>
    <div id="chart_roll" class="chart"></div>
    <div class="note">滚动 60 日相关（VST×UTES 紫 / VST×XLU 蓝 / UTES×XLU 灰）：① 2018-2020 低位震荡（0~0.4），VST 与板块几乎无关；② 2023 起 V×U 开始脱离 V×X —— UTES 因重仓 IPP 与 VST 走得更近，而 VST 与整个板块（XLU）依然若即若离（长期 0.3-0.5）；③ 2024-09 后 V×U 冲上 0.8+ 平台。UTES×XLU 反而从早期 0.9 降至 0.8 上下 —— <b>UTE 在「离开」传统公用事业、向 IPP 靠拢</b>。</div>
    <h3>年度相关与收益</h3>
    <div class="scroll">
    <table>
      <thead><tr><th>年份</th><th>相关 V×U</th><th>相关 V×X</th><th>VST</th><th>UTES</th><th>XLU</th><th>超额 V-U</th></tr></thead>
      <tbody>{year_rows}</tbody>
    </table>
    </div>
    <div class="note">2024 是「相关跳升 + VST 暴涨」同一年：VST +265.8%、相关 0.15→0.77；2025 相关登顶 0.89 但 VST 仅 +8.4%（跑输板块 14pp）—— <b>相关越高，VST 的独立 α 越少</b>。</div>
  </div>

  <div class="card">
    <h2>三、分阶段指标总表（红涨绿跌）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>阶段</th><th>名称</th><th>n</th><th>相关 V×U</th><th>相关 V×X</th><th>β(V~U)</th><th>跷跷板</th><th>VST</th><th>UTES</th><th>XLU</th><th>超额 V-U</th><th>跑赢日占比</th></tr></thead>
      <tbody>{phase_rows}</tbody>
    </table>
    </div>
    <div class="note">跷跷板 = 日收益方向相反天数占比（越低越同步）；跑赢日占比 = VST 单日跑赢 UTES 的天数比例（≈50% 即无稳定优势）。S3 的低相关+高超额是最大看点：<b>VST 的 α 全在「相关还没追上」的时候赚到的</b>。</div>
  </div>

  <div class="card">
    <h2>四、分阶段深度解读</h2>
    {phase_cards}
  </div>

  <div class="card">
    <h2>五、相对强弱：VST/UTES 比值的三段式</h2>
    <div id="chart_ratio" class="chart sm"></div>
    <div class="note">VST/UTES 比值（2018-01=1）：2022 前围绕 1 震荡（VST 不占优）→ 2023-2024 单边拉升至 {ratio['max']:.1f}（{ratio['max_date']}，VST 相对最强）→ 2025 起高位回落但仍 &gt;1.8。当前 {ratio['norm_latest']:.1f}：<b>VST 相对 UTES 仍强，但强势斜率已经钝化</b> —— 从「大 α」进入「β 时代」。</div>
  </div>

  <div class="card">
    <h2>六、结论：三个阶段三个身份</h2>
    <div class="keypoint">
      <b>① 2018-2022（S1/S2）· 板块成员：</b>VST 只是公用事业板块里一个 β≈1 的普通成员，一半交易日与板块方向相反（跷跷板最高 44.8%），超额收益来自个股修复（暴风雪后反转）。<br><br>
      <b>② 2022.11-2024.8（S3）· 独立 α 载体：</b>AI 电力叙事把 VST 变成「数据中心电力饥渴」的个股期权，两年 +289.6%，超额 +256pp —— 但此时 UTES 还没重仓 IPP，相关仅 0.51。<b>超额与相关负相关：市场还没把你当板块，才肯为你的故事单独定价。</b><br><br>
      <b>③ 2024.9 至今（S4/S5）· 板块放大器：</b>UTE 把 CEG/VST/TLN 加仓至前三（各 ~10%），相关跳到 0.89、β 翻倍至 2.41。VST 从此涨跌都放大板块 —— 2024-2025 主升浪里涨得更爽（+115% vs 44%），2026 回调里也跌得更狠（-10.1% vs -2.1%）。<b>它的定价锚从「自己的故事」变成了「AI 电力主题 + 板块 β」</b>。
    </div>
    <div class="hl-box">
      <b>对投资者的含义：</b>① 现在持有 VST 约等于「2.4 倍 β 的 AI 电力 ETF 仓位」，跟 UTES 一起持有是加杠杆不是分散；② 想看 VST 的「纯板块风险」看 XLU（相关仅 0.43），看「主题联动」看 UTES/CEG/TLN；③ VST 的超额行情历史上都出现在与板块脱钩的时期（相关低、故事独立），若相关维持 0.8+，VST 重回独立 α 需要新的个股级催化（新 PPA、FERC 裁决、电价冲击），否则只能跟板块 β 走。
    </div>
  </div>

  <div class="card">
    <div class="dis">
      数据来源：Yahoo Finance 日线（2018-01-02 ~ 2026-08-14，前复权 adj_close）；UTES 持仓构成：Virtus 官网（2026-04-13）；阶段事件：德州暴风雪（2021-02）、ChatGPT 发布（2022-11）、微软×CEG 三里岛 PPA（2024-09-20）、AWS×VST Comanche Peak PPA（2025-03-03）。相关/β/跷跷板均为日收益口径，β 为 VST 对 UTES 的 OLS 斜率。UTE 为主动管理 ETF，历史持仓构成会变化，2026-04 的持仓仅代表当期。
    </div>
    <div class="dis" style="margin-top:8px;">
      <b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
    </div>
  </div>

</div>
<script>
// ---------- 图1 归一化净值 + 阶段色带 ----------
(function(){{
  var c = document.getElementById('chart_norm');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['VST', 'UTES', 'XLU'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(norm_dates)} }},
    yAxis: {{ type: 'value', name: '归一化(2018-01=1)', scale: true }},
    series: {js(norm_series)}.map(function(s){{ return {{
      name: s.name, type: 'line', showSymbol: false, smooth: false,
      data: s.data, lineStyle: {{ width: 2 }},
      itemStyle: {{ color: s.color }},
      markArea: {{ silent: true, data: {js(phase_mark)} }}
    }}; }})
  }});
}})();

// ---------- 图2 滚动60日相关 ----------
(function(){{
  var c = document.getElementById('chart_roll');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return v === null ? '-' : v.toFixed(2); }} }},
    legend: {{ data: ['VST×UTES', 'VST×XLU', 'UTES×XLU'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(roll['dates'])} }},
    yAxis: {{ type: 'value', name: '60日滚动相关', min: -0.2, max: 1 }},
    series: [
      {{ name: 'VST×UTES', type: 'line', showSymbol: false, smooth: true, data: {js(roll['vu'])},
         lineStyle: {{ width: 2.5, color: '#7048e8' }}, itemStyle: {{ color: '#7048e8' }},
         areaStyle: {{ color: 'rgba(112,72,232,.10)' }},
         markLine: {{ data: [{{ yAxis: {corr_full['vst_utes']:.3f}, name: '全期0.63', lineStyle: {{ type: 'dashed', color: '#7048e8' }} }}] }} }},
      {{ name: 'VST×XLU', type: 'line', showSymbol: false, smooth: true, data: {js(roll['vx'])},
         lineStyle: {{ width: 2, color: '#1e66d6' }}, itemStyle: {{ color: '#1e66d6' }},
         markLine: {{ data: [{{ yAxis: {corr_full['vst_xlu']:.3f}, name: '全期0.43', lineStyle: {{ type: 'dashed', color: '#1e66d6' }} }}] }} }},
      {{ name: 'UTES×XLU', type: 'line', showSymbol: false, smooth: true, data: {js(roll['ux'])},
         lineStyle: {{ width: 1.5, color: '#9aa2ad' }}, itemStyle: {{ color: '#9aa2ad' }} }}
    ]
  }});
}})();

// ---------- 图3 年度收益 ----------
(function(){{
  var c = document.getElementById('chart_year');
  if (!c) return;
  var ch = echarts.init(c);
  var colors = {{ 'VST': '#c05c0b', 'UTES': '#1e66d6', 'XLU': '#0aa06e' }};
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return v + '%'; }} }},
    legend: {{ data: ['VST', 'UTES', 'XLU'] }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(years_list)} }},
    yAxis: {{ type: 'value', name: '年度收益 %' }},
    series: {js(year_series)}.map(function(s){{ return {{
      name: s.name, type: 'bar', barGap: 0.15,
      data: s.data.map(function(v){{ return {{ value: v, itemStyle: {{ color: v >= 0 ? colors[s.name] : '#d64545', borderRadius: [3,3,0,0] }} }}; }})
    }}; }})
  }});
}})();

// ---------- 图4 相对强弱 ----------
(function(){{
  var c = document.getElementById('chart_ratio');
  if (!c) return;
  var ch = echarts.init(c);
  ch.setOption({{
    tooltip: {{ trigger: 'axis', valueFormatter: function(v){{ return v.toFixed(2); }} }},
    grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
    xAxis: {{ type: 'category', data: {js(rc['dates'])} }},
    yAxis: {{ type: 'value', name: 'VST/UTES (2018=1)', scale: true }},
    series: [{{
      name: 'VST/UTES 相对强弱', type: 'line', showSymbol: false, smooth: true,
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

# 年度收益图插入（单独一个小卡在第二节后面太挤，直接放在相关性卡后）
# 为简洁，将年度收益图放进第二节卡片内：在 y 表前插入
html = html.replace('<h3>年度相关与收益</h3>',
                    '<h3>年度收益（红涨绿跌）</h3>\n    <div id="chart_year" class="chart sm"></div>\n    <h3>年度相关与收益明细</h3>')

out_file = os.path.join(OUT, "vst_utes_phase_report.html")
with open(out_file, "w") as f:
    f.write(html)
print("已生成:", out_file)
