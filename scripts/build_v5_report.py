#!/usr/bin/env python3
"""构建 85 号报告：CL/HO/RB 月差背离 —— 近月月差口径 × regime 依赖"""
import json, os

BASE = "/Users/alberthuang/Desktop/股票分析"
OUT = os.path.join(BASE, "results/spread_divergence")
REP = os.path.join(BASE, "reports", "85_月差背离三品种对比")

PROD_CN = {"CL": "CL 原油", "HO": "HO 取暖油", "RB": "RB 汽油"}
PROD_UNIT = {"CL": "美元/桶", "HO": "美元/加仑×42", "RB": "美元/加仑×42"}

def load_json(f):
    with open(os.path.join(OUT, f)) as fh:
        return json.load(fh)

sums = {}
evs = {}
for p in ["CL", "HO", "RB"]:
    sums[p] = load_json(f"spread_divergence_v5_{p}.json")
    evs[p] = load_json(f"v5_{p}_events_detail.json")

def fmt(x, nd=3):
    if x is None: return "—"
    return f"{x:+.{nd}f}"

def pct(x):
    if x is None: return "—"
    return f"{x*100:.0f}%"

def clr(v, inv=False):
    # 红涨绿跌：v>0 红，v<0 绿
    if v is None: return ""
    if v > 0: return "up"
    if v < 0: return "dn"
    return ""

# ===== 摘要卡片数据 =====
cards = {}
for p in ["CL", "HO", "RB"]:
    o = sums[p]
    cards[p] = {
        "n_hits": o["regime_split"]["ALL"]["n"],
        "rise_n": o["regime_split"]["RISE"]["n"],
        "fall_n": o["regime_split"]["FALL"]["n"],
        "spread_min": o["spread_range"][0],
        "spread_max": o["spread_range"][1],
        "all": o["regime_split"]["ALL"],
        "rise": o["regime_split"]["RISE"],
        "fall": o["regime_split"]["FALL"],
    }

# ===== 三品种对比表（走扩率）=====
def compare_rows():
    rows = []
    for N in ["24", "48", "72"]:
        row = {"N": N}
        cells = []
        for p in ["CL", "HO", "RB"]:
            c = cards[p]
            cells.append({
                "rise": pct(c["rise"][N]["dy_pct_pos"]),
                "rise_p": "" if c["rise"][N]["p"] is None else f"p={c['rise'][N]['p']:.3f}",
                "fall": pct(c["fall"][N]["dy_pct_pos"]),
                "fall_p": "" if c["fall"][N]["p"] is None else f"p={c['fall'][N]['p']:.3f}",
                "rise_dy": fmt(c["rise"][N]["dy_mean"], 2),
                "fall_dy": fmt(c["fall"][N]["dy_mean"], 2),
            })
        rows.append({"N": N, "cells": cells})
    return rows

# ===== 序列(供regime背景图：月差轨线 + regime分段着色) =====
def regime_series(p):
    o = sums[p]
    bars = evs[p]
    return None

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>85 · 月差背离：CL/HO/RB 三品种 —— 走扩期续扩还是回落期收敛</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{{
  --bg:#f7f6f3; --card:#ffffff; --ink:#26313d; --sub:#5b6672; --line:#e3e0d8;
  --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --purple:#CC79A7;
  --vermil:#D55E00; --green:#009E73; --grey:#9a948a;
  --red:#C0392B; --down:#1E8449;
}}
*{{box-sizing:border-box; margin:0; padding:0;}}
body{{background:var(--bg); color:var(--ink); font-family:"Microsoft YaHei","PingFang SC",sans-serif; font-size:15px; line-height:1.7;}}
.wrap{{max-width:1240px; margin:0 auto; padding:28px 20px 60px;}}
h1{{font-size:26px; letter-spacing:.5px;}}
.meta{{color:var(--sub); font-size:13px; margin-top:6px;}}
.head{{border-bottom:3px solid var(--blue); padding-bottom:14px; margin-bottom:20px;}}
.kpis{{display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:18px 0;}}
.kpi{{background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 12px;}}
.kpi .t{{font-size:12.5px; color:var(--sub);}}
.kpi b{{font-size:20px; display:block; margin-top:2px;}}
.kpi .s{{font-size:12px; color:var(--sub);}}
h2{{font-size:20px; margin:36px 0 12px; padding-left:10px; border-left:5px solid var(--blue);}}
h3{{font-size:16px; margin:22px 0 8px; color:#1d2833;}}
.card{{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:18px 20px; margin-bottom:14px;}}
.chart{{width:100%; height:400px;}}
.grid2{{display:grid; grid-template-columns:1fr 1fr; gap:14px;}}
table{{width:100%; border-collapse:collapse; font-size:13.5px; background:var(--card);}}
th{{background:#eef1f4; color:var(--ink); font-weight:600; text-align:left; position:sticky; top:0;}}
th,td{{padding:7px 9px; border-bottom:1px solid var(--line);}}
tr:hover td{{background:#f6f9fc;}}
.num{{text-align:right; font-variant-numeric:tabular-nums;}}
.note{{font-size:12.5px; color:var(--sub);}}
.concl{{border-left:5px solid var(--orange);}}
.toc{{display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 4px;}}
.toc a{{text-decoration:none; color:var(--blue); background:var(--card); border:1px solid var(--line); border-radius:16px; padding:3px 14px; font-size:13px;}}
.toc a:hover{{background:#eaf3fa;}}
ul.tight li{{margin:6px 0;}}
ol.tight li{{margin:8px 0;}}
ul.tight{{padding-left:20px;}}
ol.tight{{padding-left:20px;}}
.foot{{margin-top:40px; color:var(--sub); font-size:12px; border-top:1px solid var(--line); padding-top:12px;}}
.disclaimer{{background:#f4f1ea; border:1px dashed var(--grey); border-radius:8px; padding:10px 14px; font-size:12.5px; color:var(--sub); margin-top:16px;}}
.ok{{background:#e4f4ef; border-left:4px solid var(--green); padding:10px 14px; border-radius:6px; font-size:13.5px;}}
.up{{color:var(--red); font-weight:700;}}
.dn{{color:var(--down); font-weight:700;}}
code{{background:#eef1f4; padding:1px 6px; border-radius:4px; font-size:13px; font-family:"SF Mono",Consolas,monospace;}}
.warn{{background:#fdf3ec; border-left:4px solid var(--vermil); padding:10px 14px; border-radius:6px; font-size:13.5px;}}
/* tabs */
.tabs{{display:flex; gap:8px; margin:16px 0 4px; flex-wrap:wrap;}}
.tab{{cursor:pointer; padding:7px 18px; border-radius:8px; border:1px solid var(--line); background:var(--card); color:var(--sub); font-size:14px; transition:all .15s;}}
.tab.active{{background:var(--blue); color:#fff; border-color:var(--blue); font-weight:500;}}
.regime-chip{{display:inline-block; font-size:11px; padding:1px 8px; border-radius:10px; margin-left:6px; vertical-align:middle;}}
.regime-rise{{background:#fdf0dc; color:#b06010;}}
.regime-fall{{background:#e4f4ef; color:#0f6e56;}}
.ev-grid{{display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:12px; margin-top:8px;}}
.ev-box{{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px 12px;}}
.ev-canvas{{width:100%; height:230px;}}
@media (max-width:900px){{ .kpis{{grid-template-columns:repeat(2,1fr);}} .grid2{{grid-template-columns:1fr;}} .ev-grid{{grid-template-columns:1fr;}} }}
</style>
</head>
<body>
<div class="wrap">

<div class="head">
  <h1>85 · 月差背离：CL / HO / RB 三品种对比</h1>
  <div class="meta">「同价位、月差走扩」背离后，月差是续扩还是收敛 ｜ 报告日 2026-09-11 ｜ 数据：Futu <code>current−next</code> 近月月差（M1−M2）× 1 小时 ｜ 口径：价位记忆对比 + 滚动 5 根内 ≥3 票命中 ｜ HO/RB 月差已 ×42 统一到美元/桶</div>
  <div class="toc">
    <a href="#s0">摘要</a><a href="#s1">算法与口径</a><a href="#s2">三品种对比</a>
    <a href="#s3">逐事件小图</a><a href="#s4">机制解读</a><a href="#s5">局限</a>
  </div>
</div>

<div class="warn"><b>口径更正声明</b>：84 号报告曾用「远月连续 +1 价差（2610−2611 起）」作为月差，实测只有 2~3 美元，与近月月差（3–4 月高达 9~15 美元）严重不符。本文改用 <code>US.CLcurrent − US.CLnext</code>（真近月 M1−M2），并同步修正 HO/RB 的「加仑→桶」单位（×42）。结论以本文为准。</div>

<h2 id="s0">摘要 · 结论先行</h2>
<div class="card concl">
<ol class="tight">
<li><b>核心问题</b>：价格回到曾到过的价位，该价位上的月差却比上次更宽（背离）。此后月差继续走扩，还是补跌收敛？</li>
<li><b>答案不是单一的「续扩」或「收敛」，而是取决于 regime（当时的月差趋势状态）。</b>把命中事件按「月差处于走扩期 or 回落期」分开后，方向出现明显分化。</li>
<li><b>CL</b>：走扩期背离 → 月差继续走扩（48h +0.66、72h +0.78 美元/桶）；回落期背离 → 月差补跌收敛（48h −0.39 显著 p=0.04、72h −0.52 p=0.07）。这是你 3–4 月「月差到 9」直觉的注脚——那阵还在走扩，背离后确实继续冲。</li>
<li><b>HO（取暖油）反过来了</b>：即便身处走扩期，背离后月差也强收敛（48h −1.45 p=0.005、72h −1.82 p=0.0002），走扩率只剩 19%。是典型的均值回归型月差。</li>
<li><b>RB（汽油）与 CL 同向但样本最少</b>：走扩期背离后 48h +0.75（p=0.05），方向偏续扩，但仅 17 个样本，不宜下重结论。</li>
<li><b>共同点</b>：三品种在<b>回落期</b>背离后，72h 走扩率全部 &lt;50%（39% / 33% / 43%）——「月差见顶回落后，背离不再意味续扩」这一点跨品种一致。</li>
</ol>
</div>

<div class="kpis">
  <div class="kpi"><div class="t">命中事件总数</div><b>{cards['CL']['n_hits']+cards['HO']['n_hits']+cards['RB']['n_hits']}</b><div class="s">CL {cards['CL']['n_hits']} ｜ HO {cards['HO']['n_hits']} ｜ RB {cards['RB']['n_hits']}</div></div>
  <div class="kpi"><div class="t">品种核心差异</div><b style="font-size:15px;">CL regime 依赖<br>HO 强收敛 · RB 偏续扩</b></div>
  <div class="kpi"><div class="t">月差量级(桶)</div><b style="font-size:15px;">CL −0.1~16<br>HO −2.9~19 · RB +1.4~19</b></div>
  <div class="kpi"><div class="t">HO/RB 单位</div><b>×42</b><div class="s">加仑 → 桶，统一口径</div></div>
</div>

<h2 id="s1">算法与口径</h2>
<div class="card">
<h3>你的算法（价位记忆对比）</h3>
<ul class="tight">
<li>维护一张「价位 → 最近一次经过时的月差」映射表；价格重新回到某价位 <code>x</code> 时，对比新的月差 <code>y'</code> 与上次 <code>y</code>。</li>
<li>若 <code>y' &gt; y + δ</code>（同价位月差走扩）→ 记 1 票；滚动 <b>5 根 bar</b> 内凑满 <b>3 票</b> 即「命中」（背离事件）。</li>
<li>前向观察 24 / 48 / 72 小时，看命中后月差是续扩（+）还是收敛（−）。</li>
</ul>
<h3>本期修正（相对 84 号）</h3>
<ul class="tight">
<li><b>月差口径</b>：由「远月 +1 价差」改为 <code>current − next</code>（真近月 M1−M2 连续代码）。</li>
<li><b>单位</b>：HO/RB 月差原为美元/加仑，×42 统一到美元/桶，方可与 CL 比较。</li>
<li><b>换月剔除</b>：仅当 <code>next</code> 腿单边跳（|ret|&gt;1.5% 且 &gt;cur 腿且差 &gt;1%）时判为换月伪跳、重置记忆；cur 腿主导的跳变是真实行情、保留（如 CL 4/2 挤仓）。</li>
<li><b>阈值对齐</b>：δ 按各品种「同价位月差 std 的 0.10 倍」等比设定（CL 0.07 美元/桶、HO 0.26、RB 0.27）。</li>
<li><b>regime 客观分类</b>：月差 <code>SMA(24h)</code> vs <code>SMA(120h)</code>，短期&gt;长期 = 走扩期，否则 = 回落期。</li>
</ul>
</div>

<h2 id="s2">三品种对比</h2>
<div class="card">
<div id="c_cmp" class="chart" style="height:420px;"></div>
<p class="note">纵轴 = 背离命中后月差的「走扩率」（&gt;50% 表示背离后月差更倾向于继续走扩；&lt;50% 倾向收敛）。橙 = 走扩期命中，青 = 回落期命中，三档色阶对应 24/48/72 小时前向，虚线为 50% 无方向基准。</p>
</div>

<div class="card">
<h3>走扩率对比表（背离后月差续扩占比）</h3>
<table>
<thead><tr><th>前向</th><th>CL 走扩期</th><th>CL 回落期</th><th>HO 走扩期</th><th>HO 回落期</th><th>RB 走扩期</th><th>RB 回落期</th></tr></thead>
<tbody>
"""

for row in compare_rows():
    c = row["cells"]
    html += f"""<tr><td><b>{row['N']}h</b></td>
<td class="num">{c[0]['rise']} <span class="note">{c[0]['rise_p']}</span></td>
<td class="num">{c[0]['fall']} <span class="note">{c[0]['fall_p']}</span></td>
<td class="num">{c[1]['rise']} <span class="note">{c[1]['rise_p']}</span></td>
<td class="num">{c[1]['fall']} <span class="note">{c[1]['fall_p']}</span></td>
<td class="num">{c[2]['rise']} <span class="note">{c[2]['rise_p']}</span></td>
<td class="num">{c[2]['fall']} <span class="note">{c[2]['fall_p']}</span></td></tr>
"""

html += """</tbody></table>
<p class="note">走扩率 &gt;50% = 偏续扩（红底候选），&lt;50% = 偏收敛。括号 p 为命中组 vs 全样本对照的 t 检验。</p>
</div>

<h2 id="s2b">命中后月差平均变化（美元/桶）</h2>
<div class="card">
<table>
<thead><tr><th>品种</th><th>区间</th><th>走扩期 24/48/72h</th><th>回落期 24/48/72h</th><th>全样本 24/48/72h</th></tr></thead>
<tbody>
"""

for p in ["CL", "HO", "RB"]:
    c = cards[p]
    html += f"""<tr>
<td><b>{PROD_CN[p]}</b></td>
<td class="num">n={c['n_hits']}<br><span class="note">走扩{c['rise_n']}/回落{c['fall_n']}</span></td>
<td class="num"><span class="{clr(c['rise']['24']['dy_mean'])}">{fmt(c['rise']['24']['dy_mean'],2)}</span> / <span class="{clr(c['rise']['48']['dy_mean'])}">{fmt(c['rise']['48']['dy_mean'],2)}</span> / <span class="{clr(c['rise']['72']['dy_mean'])}">{fmt(c['rise']['72']['dy_mean'],2)}</span></td>
<td class="num"><span class="{clr(c['fall']['24']['dy_mean'])}">{fmt(c['fall']['24']['dy_mean'],2)}</span> / <span class="{clr(c['fall']['48']['dy_mean'])}">{fmt(c['fall']['48']['dy_mean'],2)}</span> / <span class="{clr(c['fall']['72']['dy_mean'])}">{fmt(c['fall']['72']['dy_mean'],2)}</span></td>
<td class="num"><span class="{clr(c['all']['24']['dy_mean'])}">{fmt(c['all']['24']['dy_mean'],2)}</span> / <span class="{clr(c['all']['48']['dy_mean'])}">{fmt(c['all']['48']['dy_mean'],2)}</span> / <span class="{clr(c['all']['72']['dy_mean'])}">{fmt(c['all']['72']['dy_mean'],2)}</span></td>
</tr>
"""

html += """</tbody></table>
<p class="note">红=续扩（正值），绿=收敛（负值）。HO 走扩期 48/72h 为深绿（−1.45 / −1.82，p≤0.005），是三品种中最强的均值回归信号。</p>
</div>

<h2 id="s3">逐事件小图 · 每个命中点一张图（价格 / 月差上下双窗）</h2>
<p class="note">每个触发事件一张小图：上窗 = 近月价格（蓝线），下窗 = 月差（橙线）。<b>黄色竖线</b> = 触发 bar，<b>红色散点</b> = 投票 bar（5 中 3 的 3 票所在）。右下角颜色标记该事件所属 regime（橙=走扩期、绿=回落期）。</p>

<div class="tabs">
  <div class="tab active" data-p="CL">CL 原油（{cards['CL']['n_hits']} 事件）</div>
  <div class="tab" data-p="HO">HO 取暖油（{cards['HO']['n_hits']} 事件）</div>
  <div class="tab" data-p="RB">RB 汽油（{cards['RB']['n_hits']} 事件）</div>
</div>

<div id="c_events" class="ev-grid"></div>

<h2 id="s4">机制解读</h2>
<div class="card">
<ul class="tight">
<li><b>CL 的 regime 依赖</b>：近月月差是「现货紧张 + 挤仓」的温度计。走扩期（3–4 月，backwardation 一路冲到 16 美元/桶）里，同价背离是趋势的一部分，动量会继续推着月差走扩；一旦月差见顶回落（5 月起），背离就变成对过度定价的修正，月差单边收敛。这解释了为什么「恒定收敛」或「恒定续扩」都不对。</li>
<li><b>HO 的均值回归</b>：取暖油价差波动更受库存/天气周期驱动，缺乏 CL 那样的持续挤仓叙事，故即便短期走扩，背离后也更快被拉回。72h 走扩率仅 19%，方向高度显著。</li>
<li><b>RB 与 CL 同向但弱</b>：样本仅 31（数据 4/20 才起，少 600 根 bar），信号指向续扩但不稳，可能只是数据起始时间短导致 regime 划分偏少。</li>
<li><b>交易含义</b>：做「背离收敛」策略时，<b>CL 要先看 regime</b>——走扩期别急着做收敛，回落期顺收敛方向；<b>HO 反可优先做收敛</b>（最显著）；RB 目前证据不足。</li>
</ul>
</div>

<h2 id="s5">局限</h2>
<div class="card">
<ul class="tight">
<li><b>样本期短</b>：仅 2026-03-10 ~ 09-11，约 6 个月、含一轮完整的「走扩→回落」周期，但只有一轮，regime 规律的稳健性待更长历史验证。</li>
<li><b>regime 划分是事后定义</b>：SMA(24) vs SMA(120) 是客观规则，但「24/120」窗口本身是主观选择；改用其他窗口可能移动分类边界。</li>
<li><b>连续代码含换月缝合</b>：current/next 是拼接序列，虽已按「next 腿单边跳」剔除换月点，但换月前后一段的月差仍可能有连续性瑕疵。</li>
<li><b>RB 起点晚</b>：RB 数据 4/20 才开始，缺 3–4 月 CL/HO 那波核心走扩期，跨品种横向可比性受限。</li>
<li><b>未做交易成本/滑点</b>：月差 1h 粒度从信号到成交存在执行滑点，实测收益会打折。</li>
</ul>
</div>

<div class="disclaimer">本报告仅用于研究与数据分析，不构成任何投资建议。期货月差交易存在重大风险，历史规律不保证未来重现。</div>
<div class="foot">报告 85 · 月差背离三品种对比 ｜ 生成 2026-09-11 ｜ 数据源 Futu（US.CL/HO/RB current·next 1h）｜ 脚本 scripts/spread_divergence_v5.py + build_v5_report.py</div>

</div>

<script>
const PROD_CN = {CL:"CL 原油", HO:"HO 取暖油", RB:"RB 汽油"};
const EVENTS = """

ev_json = {}
for p in ["CL", "HO", "RB"]:
    ev_json[p] = evs[p]["events"]
html += json.dumps(ev_json, ensure_ascii=False)

html += """;

let CUR_P = 'CL';
function renderEvents() {
  const evs = EVENTS[CUR_P];
  const grid = document.getElementById('c_events');
  grid.innerHTML = '';
  evs.forEach((ev, mi) => {
    const box = document.createElement('div');
    box.className = 'ev-box';
    const head = document.createElement('div');
    head.style.cssText = 'display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#5b6672;margin-bottom:4px;';
    const chip = (ev.regime===1) ? '<span class="regime-chip regime-rise">走扩期</span>' : '<span class="regime-chip regime-fall">回落期</span>';
    head.innerHTML = '<span><b>#'+(mi+1)+'</b> '+ev.trigger_ts+'</span>'+chip;
    box.appendChild(head);
    const cv = document.createElement('div');
    cv.id = 'ev_'+CUR_P+'_'+mi;
    cv.className = 'ev-canvas';
    box.appendChild(cv);
    grid.appendChild(box);
  });
  evs.forEach((ev, mi) => {
    const ch = echarts.init(document.getElementById('ev_'+CUR_P+'_'+mi));
    const votePts = ev.voteIdx.map(k => ({ value: [ev.ts[k], ev.x[k]] }));
    ch.setOption({
      tooltip: { trigger: 'axis' },
      axisPointer: { link: [{ xAxisIndex: 'all' }] },
      grid: [
        { left: 46, right: 16, top: 8, height: 78 },
        { left: 46, right: 16, top: 106, height: 66 }
      ],
      xAxis: [
        { type: 'category', gridIndex: 0, data: ev.ts, axisLabel: { show: false }, axisTick:{show:false} },
        { type: 'category', gridIndex: 1, data: ev.ts, axisLabel: { formatter: v => v.slice(5, 16), fontSize: 8.5, interval: Math.max(Math.floor(ev.ts.length/4),1) }, axisTick:{show:false} }
      ],
      yAxis: [
        { type: 'value', gridIndex: 0, name: '价格', nameTextStyle:{fontSize:8}, axisLabel:{fontSize:8}, scale:true, splitLine:{lineStyle:{color:'#eef1f4'}} },
        { type: 'value', gridIndex: 1, name: '月差', nameTextStyle:{fontSize:8}, axisLabel:{fontSize:8}, scale:true, splitLine:{lineStyle:{color:'#eef1f4'}} }
      ],
      series: [
        { name:'价格', type:'line', xAxisIndex:0, yAxisIndex:0, data:ev.x, showSymbol:false, lineStyle:{width:1.2,color:'#0072B2'}, itemStyle:{color:'#0072B2'},
          markLine:{ silent:true, symbol:'none', lineStyle:{color:'#F5B800',width:1.4}, data:[{xAxis:ev.triggerIdx}] } },
        { name:'投票点', type:'scatter', xAxisIndex:0, yAxisIndex:0, data:votePts, symbolSize:5, itemStyle:{color:'#D55E00'}, z:8 },
        { name:'月差', type:'line', xAxisIndex:1, yAxisIndex:1, data:ev.y, showSymbol:false, lineStyle:{width:1.2,color:'#E69F00'}, itemStyle:{color:'#E69F00'},
          markLine:{ silent:true, symbol:'none', lineStyle:{color:'#F5B800',width:1.4}, data:[{xAxis:ev.triggerIdx}] } }
      ]
    });
  });
}

function renderCmp() {
  const ch = echarts.init(document.getElementById('c_cmp'));
  const labels = ['CL 原油','HO 取暖油','RB 汽油'];
  const data = {
    labels,
    datasets: [
      { label:'走扩期 24h', data:[52,42,71], backgroundColor:'#F4C077' },
      { label:'走扩期 48h', data:[52,32,71], backgroundColor:'#EF9F27' },
      { label:'走扩期 72h', data:[46,19,76], backgroundColor:'#BA7517' },
      { label:'回落期 24h', data:[50,59,57], backgroundColor:'#9FE1CB' },
      { label:'回落期 48h', data:[36,56,50], backgroundColor:'#1D9E75' },
      { label:'回落期 72h', data:[39,33,43], backgroundColor:'#0F6E56' }
    ]
  };
  // 用 echarts 而非 chartjs，保持单一图表库
  ch.setOption({
    title: { text: '背离后月差走扩率（%）', left:'center', textStyle:{fontSize:14,fontWeight:500} },
    tooltip: { trigger:'axis', axisPointer:{type:'shadow'},
      formatter: function(ps){ let s=ps[0].name+'<br/>'; ps.forEach(p=>{ if(p.seriesName!=='基准50%') s+=p.marker+p.seriesName+': '+p.value+'%<br/>'; }); return s; } },
    legend: { bottom: 0, data:['走扩期 24h','走扩期 48h','走扩期 72h','回落期 24h','回落期 48h','回落期 72h','基准50%'], textStyle:{fontSize:11} },
    grid: { left: 50, right: 20, top: 56, bottom: 70 },
    xAxis: { type:'category', data: labels, axisLabel:{fontSize:12} },
    yAxis: { type:'value', min:0, max:80, axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef1f4'}} },
    series: [
      { name:'走扩期 24h', type:'bar', data:[52,42,71], itemStyle:{color:'#F4C077'}, barMaxWidth:18 },
      { name:'走扩期 48h', type:'bar', data:[52,32,71], itemStyle:{color:'#EF9F27'}, barMaxWidth:18 },
      { name:'走扩期 72h', type:'bar', data:[46,19,76], itemStyle:{color:'#BA7517'}, barMaxWidth:18 },
      { name:'回落期 24h', type:'bar', data:[50,59,57], itemStyle:{color:'#9FE1CB'}, barMaxWidth:18 },
      { name:'回落期 48h', type:'bar', data:[36,56,50], itemStyle:{color:'#1D9E75'}, barMaxWidth:18 },
      { name:'回落期 72h', type:'bar', data:[39,33,43], itemStyle:{color:'#0F6E56'}, barMaxWidth:18 },
      { name:'基准50%', type:'line', data:[50,50,50], itemStyle:{color:'#888780'}, lineStyle:{color:'#888780',type:'dashed'}, symbol:'none' }
    ]
  });
}

document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    CUR_P = t.dataset.p;
    renderEvents();
  });
});

renderCmp();
renderEvents();
window.addEventListener('resize', () => { echarts.getInstanceByDom(document.getElementById('c_cmp')).resize(); });
</script>
</body>
</html>
"""

os.makedirs(REP, exist_ok=True)
with open(os.path.join(REP, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(html)
print("已写出", os.path.join(REP, "index.html"), "大小", len(html))
