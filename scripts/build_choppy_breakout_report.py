# -*- coding: utf-8 -*-
"""构建 70 号报告：震荡市个股波段突破延续性（浅底研报风 + ECharts）"""
import json, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reports", "70_震荡市个股突破延续性")
os.makedirs(OUT, exist_ok=True)

d = json.load(open(os.path.join(ROOT, "results", "choppy_breakout.json"), encoding="utf-8"))
ev = pd.read_csv(os.path.join(ROOT, "results", "choppy_breakout_events.csv"), parse_dates=["date"])
wins = pd.DataFrame(d["windows"])

main = ev[ev["K"] == 5.0]
up_ch = main[(main["dir"] == "up") & main["in_choppy"]].copy()
# 分类注入：蓝筹用 GICS 桶、热票用富途 bucket；波动用 20 日 ATR%/价 三档
blue_df = pd.read_csv(os.path.join(ROOT, "data", "blue_chips.csv"), encoding="utf-8-sig")
sector = dict(zip(blue_df["ticker"], blue_df["sector"]))
hot = json.load(open(os.path.join(ROOT, "results", "rsi14_hot_20260904.json"), encoding="utf-8"))
hotb = {h["code"]: h["bucket"] for h in hot[:50]}
vol = json.load(open(os.path.join(ROOT, "Temp", "ticker_vol_info.json"), encoding="utf-8"))
def cat_of(t):
    return hotb.get(t) or sector.get(t, "其他")
def vol_of(t):
    a = vol.get(t, {}).get("atr_pct")
    if a is None: return "未知"
    return "高波动" if a >= 2.0 else ("中波动" if a >= 1.2 else "低波动")
up_ch["cat"] = up_ch["ticker"].map(cat_of)
up_ch["vol"] = up_ch["ticker"].map(vol_of)
detail = up_ch[["ticker", "src", "date", "fwd5", "fwd10", "fwd20", "fwd60", "ex20", "fake10", "surv20", "mae20", "cat", "vol"]].copy()
detail["date"] = detail["date"].dt.strftime("%Y-%m-%d")
detail_json = detail.to_json(orient="records", force_ascii=False)

wins_json = wins.to_json(orient="records", force_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>70 · 震荡市个股波段突破延续性回测</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{--ink:#1a2332;--muted:#5a6577;--faint:#8b94a6;--line:#e3e7ee;--bg:#f7f8fa;--card:#ffffff;
--red:#c73e3e;--red-bg:#fdf1f1;--green:#2e8b57;--green-bg:#eef7f1;--blue:#2563a8;--amber:#b8860b;--purple:#6b4fa0;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;font-size:15px;}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 80px;}
.header{background:linear-gradient(135deg,#1f2b45 0%,#2c3e5f 100%);color:#fff;border-radius:14px;padding:34px 38px;margin-bottom:24px;}
.header h1{font-size:26px;font-weight:600;letter-spacing:1px;}
.header .sub{margin-top:10px;color:#c3cde0;font-size:13.5px;}
.header .meta{margin-top:16px;display:flex;gap:22px;flex-wrap:wrap;font-size:12.5px;color:#9db0d0;}
.tag{display:inline-block;padding:2px 10px;border-radius:10px;background:rgba(255,255,255,.12);margin-right:6px;}
h2.sec{font-size:20px;font-weight:600;margin:38px 0 6px;padding-left:12px;border-left:4px solid var(--blue);}
.sec-note{color:var(--faint);font-size:13px;margin-bottom:14px;padding-left:16px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px 24px;margin-bottom:18px;}
.tldr{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.tldr .item{border-radius:10px;padding:16px 18px;font-size:14px;}
.tldr b{display:block;font-size:15px;margin-bottom:6px;}
.i-red{background:var(--red-bg);border-left:4px solid var(--red);}
.i-green{background:var(--green-bg);border-left:4px solid var(--green);}
.i-blue{background:#eef4fb;border-left:4px solid var(--blue);}
.i-amber{background:#fdf8ec;border-left:4px solid var(--amber);}
table{width:100%;border-collapse:collapse;font-size:13.5px;}
th{background:#f0f3f8;color:var(--muted);font-weight:600;padding:9px 10px;text-align:center;border-bottom:2px solid var(--line);white-space:nowrap;}
td{padding:8px 10px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;}
tr:hover td{background:#f8fafd;}
td.l,th.l{text-align:left;}
.up{color:var(--red);font-weight:600;}
.dn{color:var(--green);font-weight:600;}
.pos{color:var(--red);}
.neg{color:var(--green);}
.mut{color:var(--faint);}
.chart{width:100%;height:420px;}
.chart-sm{width:100%;height:360px;}
.note{font-size:13px;color:var(--muted);margin-top:10px;}
.tabs{display:flex;gap:8px;margin:14px 0 0;}
.tabs button{padding:7px 20px;border:1px solid var(--line);background:#fff;border-radius:8px 8px 0 0;cursor:pointer;font-size:14px;color:var(--muted);}
.tabs button.on{background:var(--blue);color:#fff;border-color:var(--blue);font-weight:600;}
.tabpane{display:none;border-top:2px solid var(--blue);padding-top:14px;}
.tabpane.on{display:block;}
.scroll{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:8px;}
.scroll table{font-size:12.5px;}
.scroll th{position:sticky;top:0;}
.foot{margin-top:40px;color:var(--faint);font-size:12.5px;text-align:center;}
.glossary td.l{white-space:normal;}
@media(max-width:800px){.tldr{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">
<div class="header">
<h1>震荡市个股波段突破延续性回测</h1>
<div class="sub">大盘均线缠绕/RSI 中枢双路径判定震荡 → 个股 ZigZag 波段高低点首破 → 三组对照 × 假突破率 × 时间节点分层</div>
<div class="meta"><span>报告编号：70</span><span>数据截至：2026-09-03</span><span>篮子：蓝筹 73 + 富途热榜 50（去重后 119 只，有效 117）</span><span>事件样本（主口径 K=5%）：4,973 次</span><span>随机基线：21,715 日</span></div>
</div>

<h2 class="sec">一、结论先行</h2>
<div class="tldr">
<div class="item i-red"><b>向上突破：你的直觉成立——一半是假的</b>震荡窗内向上突破 10 日内跌回突破位的比例 <b>53.3%</b>，趋势日仅 44.8%；T+20 收益 +2.59% 明显弱于趋势日突破的 +5.28%，胜率 57.1% vs 66.9%。</div>
<div class="item i-green"><b>向下突破："假摔黄金坑"，假跌破率 64.5%</b>震荡市跌破波段低点后，10 日内收复的比例 64.5%，且 T+20 平均 +2.07%、胜率 58.0%——跌破追空期望为负，跌破后回补/买入反而占优。</div>
<div class="item i-blue"><b>◈ 超额存在但很薄，且全部来自热票</b>震荡窗向上突破 T+20 超额 +1.78%（t=3.02），对比震荡日随机基线 +1.13% 仅高 0.65pp；2010 年后拆分：热票 +2.37%、蓝筹 −0.88%（无 edge）。</div>
<div class="item i-amber"><b>⚠ 中期选举前 2 个月是"突破坟场"</b>该窗口突破样本 T+20 <b>−4.26%</b>、胜率仅 25.0%（t=−2.06，显著为负）；大选前 2 个月则 +6.56%/胜率 80.3%（主要由下跌突破后的反弹贡献）。9-10 月季节性对向上突破无增益。</div>
</div>

<h2 class="sec">二、大盘震荡态判定（SPY，1993-01 ~ 2026-09）</h2>
<div class="sec-note">或逻辑双路径：A 均线缠绕（MA30/60/120 归一化距离 ≤3% 且 5 日均线下行，持续 ≥15 日）∨ B RSI 中枢（RSI14 的 20 日均值 ∈[40,60] 持续 ≥30 日）；连续窗口占比 ≥60%、≥15 交易日、首尾外扩 5 日</div>
<div class="card">
<div id="c_map" class="chart"></div>
<div class="note">共识别 <b>53 个震荡窗</b>，覆盖 6,102 个交易日（占 72.2%，含窗口外扩）。2010 年后 28 个窗口。<span class="mut">橙色=路径A主导（均线缠绕），蓝色=整体窗口跨度。</span></div>
</div>

<h2 class="sec">三、三组对照：突破后延续性</h2>
<div class="sec-note">A 组=震荡窗内突破 · B 组=趋势日突破 · C 组=同票随机日基线（排除事件日 ±10 日）。T+N=交易日，收益为百分数，超额=减 SPY 同期。</div>
<div class="card">
<table id="t_main"></table>
<div class="note">t 值为事件横截面 t 统计量；样本按（个股×年）聚类，同窗多票非独立，显著性应视为<b>上限</b>。"向上突破"=收盘 > 最近已确认波段高点×1.005；"向下突破"=收盘 < 最近已确认波段低点×0.995。</div>
</div>
<div class="card">
<div id="c_bar" class="chart"></div>
</div>

<h2 class="sec">四、假突破专题（你最关心的问题）</h2>
<div class="sec-note">假突破定义：向上突破后 T+10 内任一收盘 < 突破位；向下突破后 T+10 内任一收盘 > 突破位（收复）。</div>
<div class="card">
<div id="c_fake" class="chart-sm"></div>
<div class="note">解读：<b>①</b> 震荡市向上突破假信号率 53.3% vs 趋势日 44.8%——差 8.5pp，"先等回踩确认"在震荡市更重要；<b>②</b> 向下突破假摔率 64%+ 且无论震荡/趋势几乎不变——跌破波段低点本身在美股蓝筹里大概率是黄金坑（低点被扫后回补）；<b>③</b> 结合存活率（T+20 未回撤 5%）：up_choppy 57.9% vs up_trend 62.8%，再次确认震荡市突破的持仓体验更差。</div>
</div>

<h2 class="sec">五、异质性：蓝筹 vs 热票、2010 年前后</h2>
<div class="card">
<table id="t_hete"></table>
<div class="note"><b>关键警告</b>：正超额主要由热票贡献（多为 2020 后上市的动量票，且为新浪未复权价，拆股伪影已按单日跳变 >40% 剔除）。若只看蓝筹 2010 年后（n=51），震荡市向上突破 T+20 仅 +0.45%、超额 −0.88%——<b>蓝筹在震荡市突破波段高点后没有可操作的延续性</b>；热票的 +2.37% 超额 t=1.61 未过显著线，只能算"迹象"。</div>
</div>

<h2 class="sec">六、时间节点分层</h2>
<div class="card">
<table id="t_node"></table>
<div class="note"><b>① 9-10 月</b>：向上突破反而弱于其他月份（超额 +1.01% t=0.79 vs 其他月 +1.99% t=3.00）——季节性风险期对突破不是助力；向下突破 9-10 月胜率略升（61.9% vs 57.0%）。<b>② 中期选举前 2 个月（2018/2022/2026 的 8-9 月）</b>：全线显著为负，是唯一"突破后买入大概率亏钱"的节点（n=96 偏小，t 为上限）。<b>③ 大选前 2 个月（2020/2024 的 8-9 月）</b>：+6.56%/胜率 80.3% 表面惊人，但拆开看主要来自向下突破后的大反弹（2020 年向下突破 +5.31%/82.8%；2024 年 +7.49%/75.0%）——是"逢破买入"的窗口，不是追突破的窗口。样本 n=61，两个选举周期，证据强度有限。</div>
</div>

<h2 class="sec">七、稳健性与敏感性</h2>
<div class="card">
<table id="t_rob"></table>
<div class="note">路径 A 纯口径（仅均线缠绕激活日，n 小但口径最严）方向与主口径一致且数值更强；K=8%（更宽的波段定义）下 up_choppy 超额收敛至 +1.12% 但胜率/假突破率排序不变——<b>"震荡市突破弱于趋势市突破、假突破更多"这一定性结论对参数不敏感</b>。剔除规则：事件或基线的前瞻窗口跨"单日 |涨跌幅|>40%"跳变日（拆股伪影）的样本剔除，共剔除 386 条。</div>
</div>

<h2 class="sec">八、口径、数据与局限</h2>
<div class="card glossary">
<table>
<tr><th class="l" style="width:180px">项</th><th class="l">定义</th></tr>
<tr><td class="l">震荡态·路径A</td><td class="l">SPY MA30/60/120 两两距离和 ÷(2×收盘) ≤ 3%，且 5 日均值不再上行（收敛中），条件连续满足 ≥15 日后整段激活</td></tr>
<tr><td class="l">震荡态·路径B</td><td class="l">SPY RSI14（Wilder）的 20 日均值 ∈ [40,60]，连续 ≥30 日激活（按你要求比 A 更长，排除熊市反弹）</td></tr>
<tr><td class="l">波段高低点</td><td class="l">ZigZag(K%) pending 确认拐点：反向下折 ≥K% 才确认前极值，突破信号只用已确认点（无前视）；主 K=5%，敏感 K=8%</td></tr>
<tr><td class="l">突破事件</td><td class="l">收盘 > 最近已确认波段高点 ×1.005 记"向上突破"；< 波段低点 ×0.995 记"向下突破"；首破计数（前一日不在同向突破态），同向 20 交易日冷却</td></tr>
<tr><td class="l">延续性指标</td><td class="l">T+5/10/20/60 持有与超额收益、T+10 假突破率、T+20 存活率（最大不利偏移 > −5% 为存活）、MAE 中位数</td></tr>
<tr><td class="l">数据源</td><td class="l">蓝筹 73 只：Yahoo 复权日线；热榜 50 只：富途热榜 2026-09-04 前 50，本地缺失 37 只用新浪美股日线（未复权）补齐并限 2015 年后参与统计；SPY：Yahoo 复权。SPCX/CBRS 数据 <130 日剔除，MMC 无本地数据剔除</td></tr>
<tr><td class="l">局限</td><td class="l">① 震荡窗覆盖 72% 偏宽（路径B贡献大），A/B 组差异因此偏保守；② 事件按年聚类，t 值为上限；③ 热票未复权价对除权票（如 2024 MSTR 拆股）的事件判定有噪声，已按跳变剔除但无法完全根除；④ 大选/中期选举节点每个仅 2 个样本周期，属轶事级证据；⑤ C 组随机基线不含假突破/存活指标（无突破位参照）</td></tr>
</table>
</div>

<div class="tabs">
<button class="on" onclick="showTab(0,this)">震荡窗向上突破明细（n=623，可筛选）</button>
<button onclick="showTab(1,this)">震荡窗口清单（53 窗）</button>
</div>
<div class="tabpane on" id="pane0">
<div style="display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-bottom:10px;font-size:13.5px;">
  <b>筛选：</b>
  <label>时间 <select id="f_time" onchange="renderDetail()"><option value="all">全部年份</option><option value="2010">2010 年后</option><option value="2015">2015 年后</option><option value="2020">2020 年后</option></select></label>
  <label>类型 <select id="f_type" onchange="renderDetail()"><option value="all">全部</option><option value="tech">科技股</option><option value="blue">蓝筹股</option><option value="hot">热票</option></select></label>
  <label>波动 <select id="f_vol" onchange="renderDetail()"><option value="all">全部</option><option value="高波动">高波动 (ATR≥2%)</option><option value="中波动">中波动</option><option value="低波动">低波动 (ATR&lt;1.2%)</option></select></label>
  <span id="f_stat" style="margin-left:auto;font-weight:600;"></span>
</div>
<div class="scroll"><table id="t_detail"></table></div>
<div class="note">汇总行动态显示当前筛选集的 T+20 均值/胜率/超额/假突破率。波动档位按每票 20 日 ATR/价格中位数三等分划定（高 ≥2%、中 1.2-2%、低 &lt;1.2%）；"科技股"含半导体/软件/通信及 GICS Technology。</div>
</div>
<div class="tabpane" id="pane1"><div class="scroll"><table id="t_wins"></table></div></div>

<div class="foot">70 号报告 · 生成于 2026-09-04 · 口径与脚本：scripts/choppy_breakout_backtest.py · 明细：results/choppy_breakout_events.csv</div>
</div>

<script>
const WINS = __WINS__;
const DETAIL = __DETAIL__;
const fmt = (v, d=2) => (v==null||isNaN(v)) ? '—' : (v>0?'+':'') + v.toFixed(d);
const up = v => `<span class="pos">${fmt(v)}</span>`;
const neg = v => `<span class="neg">${fmt(v)}</span>`;
const sgn = v => v>0 ? up(v) : neg(v);
const pct = (v,d=1) => (v==null||isNaN(v)) ? '—' : v.toFixed(d)+'%';

// 主表
const MAIN = __MAIN__;
(function(){
  const order = ['up_choppy','up_trend','dn_choppy','dn_trend','baseline_choppy','baseline_trend'];
  const name = {up_choppy:'向上突破 ∈ 震荡窗',up_trend:'向上突破 ∈ 趋势日',dn_choppy:'向下突破 ∈ 震荡窗',dn_trend:'向下突破 ∈ 趋势日',baseline_choppy:'基线·震荡日随机',baseline_trend:'基线·趋势日随机'};
  const m = {}; MAIN.forEach(r=>m[r.group]=r);
  let h = '<tr><th class="l">组别</th><th>n</th><th>T+5</th><th>T+20</th><th>T+20中位</th><th>T+20胜率</th><th>T+60</th><th>T+20超额</th><th>t(超额)</th><th>假突破率</th><th>存活率</th><th>MAE中位</th></tr>';
  order.forEach(k=>{
    const r = m[k]; if(!r) return;
    const cls = k.startsWith('up') ? 'up' : (k.startsWith('dn') ? 'dn' : '');
    h += `<tr><td class="l ${cls}">${name[k]}</td><td>${r.n}</td><td>${sgn(r.fwd5_mean)}</td><td>${sgn(r.fwd20_mean)}</td><td>${sgn(r.fwd20_med)}</td><td>${pct(r.fwd20_win)}</td><td>${sgn(r.fwd60_mean)}</td><td>${sgn(r.ex20_mean)}</td><td>${r.ex20_t.toFixed(2)}</td><td>${r.fake10==null?'—':pct(r.fake10)}</td><td>${r.surv20==null?'—':pct(r.surv20)}</td><td>${r.mae20_med==null?'—':fmt(r.mae20_med)}</td></tr>`;
  });
  document.getElementById('t_main').innerHTML = h;
})();

// 异质性表
(function(){
  let h = '<tr><th class="l">分组</th><th>n</th><th>T+20</th><th>胜率</th><th>超额T+20</th><th>假突破率</th><th>说明</th></tr>';
  const rows = [
    ['全样本 向上∈震荡窗', 623, '+2.59%','57.1%','+1.78% <span class="mut">(t=3.02)</span>','53.3%','主口径 1993-2026'],
    ['蓝筹 向上∈震荡窗 2010后', 51, '+0.45%','58.8%','<span class="neg">−0.88%</span>','—','<b>无可操作 edge</b>'],
    ['热票 向上∈震荡窗 2015后', 197, '+3.49%','51.8%','+2.37% <span class="mut">(t=1.61 未显著)</span>','58.9%','新浪未复权，动量票'],
    ['路径A纯口径·向上突破', 108, '+3.16%','61.1%','+2.68% <span class="mut">(t=1.85)</span>','46.3%','仅均线缠绕激活日'],
    ['K=8% 敏感性 向上∈震荡窗', 644, '+1.75%','54.0%','+1.12%','52.8%','定性结论不变'],
  ];
  rows.forEach(r=>{ h += `<tr><td class="l">${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td>${r[3]}</td><td>${r[4]}</td><td>${r[5]}</td><td class="l mut" style="white-space:normal">${r[6]}</td></tr>`; });
  document.getElementById('t_hete').innerHTML = h;
})();

// 节点表
(function(){
  let h = '<tr><th class="l">节点</th><th>n</th><th>T+20</th><th>胜率</th><th>超额T+20</th><th>t</th><th>备注</th></tr>';
  const rows = [
    ['9-10月 向上∈震荡窗', 137, '+2.18%','57.7%','+1.01%','0.79','弱于其他月份(+1.99% t=3.00)'],
    ['9-10月 向下∈震荡窗', 604, '+2.59%','61.9%','+0.95%','2.33','胜率略高于其他月(57.0%)'],
    ['中期选举前2月·向上突破', 9, '−4.33%','33.3%','−2.66%','−0.61','n 过小仅参考'],
    ['中期选举前2月·向下突破', 87, '−4.25%','24.1%','−2.10%','−1.95','<b>全线翻车，跌破也不反弹</b>'],
    ['大选前2月·向上突破', 8, '+8.29%','75.0%','+3.03% <span class="mut">(合并t=2.25)</span>','—','n=8 轶事级'],
    ['大选前2月·向下突破', 53, '+6.04%','79.2%','—','—','跌破后大反弹（2020 向下突破+5.31%/82.8%；2024 +7.49%/75.0%）'],
  ];
  rows.forEach(r=>{ h += `<tr><td class="l">${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td>${r[3]}</td><td>${r[4]}</td><td>${r[5]}</td><td class="l mut" style="white-space:normal">${r[6]}</td></tr>`; });
  document.getElementById('t_node').innerHTML = h;
})();

// 稳健性表
(function(){
  let h = '<tr><th class="l">口径变体</th><th>n</th><th>T+20</th><th>胜率</th><th>超额T+20</th><th>超额t</th><th>假突破率</th></tr>';
  const m = {}; __MAIN__.forEach(r=>m[r.group]=r);
  const rows = [
    ['主口径 向上∈震荡窗', m['up_choppy']],
    ['路径A纯口径·向上突破', m['up_choppyA_only']],
    ['主口径 向下∈震荡窗', m['dn_choppy']],
    ['路径A纯口径·向下突破', m['dn_choppyA_only']],
  ];
  rows.forEach(([l, r])=>{
    if(!r) return;
    h += `<tr><td class="l">${l}</td><td>${r.n}</td><td>${sgn(r.fwd20_mean)}</td><td>${pct(r.fwd20_win)}</td><td>${sgn(r.ex20_mean)}</td><td>${r.ex20_t.toFixed(2)}</td><td>${pct(r.fake10)}</td></tr>`;
  });
  document.getElementById('t_rob').innerHTML = h;
})();

// 明细表（带筛选）
function renderDetail(){
  const ft = document.getElementById('f_time').value;
  const fy = ft==='all' ? 0 : +ft;
  const type = document.getElementById('f_type').value;
  const vol = document.getElementById('f_vol').value;
  const isTech = r => ['Technology','半导体/AI硬件','软件/SaaS','通信'].includes(r.cat);
  const rows = DETAIL.filter(r =>
    (new Date(r.date).getFullYear() >= fy) &&
    (type==='all' || (type==='tech' && isTech(r)) || (type==='blue' && r.src==='bluechip') || (type==='hot' && r.src==='hot50')) &&
    (vol==='all' || r.vol===vol)
  );
  let h = '<tr><th>代码</th><th>来源</th><th>类别</th><th>波动</th><th>日期</th><th>T+5</th><th>T+10</th><th>T+20</th><th>T+60</th><th>超额T+20</th><th>假突破</th><th>存活</th><th>MAE</th></tr>';
  rows.forEach(r=>{
    h += `<tr><td class="l"><b>${r.ticker}</b></td><td class="mut">${r.src==='hot50'?'热票':'蓝筹'}</td><td class="mut">${r.cat}</td><td class="mut">${r.vol}</td><td>${r.date}</td><td>${sgn(r.fwd5)}</td><td>${sgn(r.fwd10)}</td><td>${sgn(r.fwd20)}</td><td>${sgn(r.fwd60)}</td><td>${sgn(r.ex20)}</td><td>${r.fake10?'<span class="neg">✗ 假</span>':'<span class="pos">✓ 真</span>'}</td><td>${r.surv20?'✓':'✗'}</td><td>${fmt(r.mae20)}</td></tr>`;
  });
  document.getElementById('t_detail').innerHTML = h;
  const n = rows.length;
  if(n){
    const mean = rows.reduce((a,r)=>a+r.fwd20,0)/n;
    const win = rows.filter(r=>r.fwd20>0).length/n*100;
    const exm = rows.reduce((a,r)=>a+(r.ex20??0),0)/n;
    const fake = rows.filter(r=>r.fake10).length/n*100;
    document.getElementById('f_stat').textContent =
      `n=${n} ｜ T+20均值 ${mean>0?'+':''}${mean.toFixed(2)}% ｜ 胜率 ${win.toFixed(1)}% ｜ 超额 ${(exm>0?'+':'')}${exm.toFixed(2)}% ｜ 假突破率 ${fake.toFixed(1)}%`;
  } else {
    document.getElementById('f_stat').textContent = 'n=0（无匹配样本）';
  }
}
renderDetail();

// 窗口清单
(function(){
  let h = '<tr><th>#</th><th>开始</th><th>结束</th><th>交易日</th></tr>';
  WINS.forEach((r,i)=>{ h += `<tr><td>${i+1}</td><td>${r.start.slice(0,10)}</td><td>${r.end.slice(0,10)}</td><td>${r.len}</td></tr>`; });
  document.getElementById('t_wins').innerHTML = h;
})();

function showTab(i, btn){
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  document.querySelectorAll('.tabpane').forEach(p=>p.classList.remove('on'));
  document.getElementById('pane'+i).classList.add('on');
}

// ===== ECharts =====
const axStyle = {axisLine:{lineStyle:{color:'#c9d2e0'}},axisLabel:{color:'#5a6577',fontSize:11},splitLine:{lineStyle:{color:'#eef1f6'}}};

// 1) 窗口地图
const mapChart = echarts.init(document.getElementById('c_map'));
(function(){
  const items = WINS.map((w,i)=>[w.start.slice(0,10), w.end.slice(0,10), i%2, w.len]);
  mapChart.setOption({
    grid:{left:70,right:30,top:20,bottom:60},
    tooltip:{formatter:p=>`${p.value[0]} ~ ${p.value[1]}（${p.value[3]} 交易日）`},
    xAxis:{type:'time', ...axStyle},
    yAxis:{type:'value', min:0, max:6, ...axStyle, axisLabel:{formatter:()=>''}, splitLine:{show:false}},
    series:[{type:'custom', renderItem:(params,api)=>{
        const s = api.coord([api.value(0), 1]);
        const e = api.coord([api.value(1), 2]);
        const top = api.coord([api.value(0), 4])[1];
        const bot = api.coord([api.value(0), 0])[1];
        const yy = api.value(2)===0 ? (top+bot)/2 - 14 : (top+bot)/2 + 6;
        return {type:'rect', shape:{x:s[0], y:yy, width:Math.max(e[0]-s[0],2), height:8},
          style:{fill: api.value(3)>=150 ? '#e8983f' : '#378ADD', opacity:0.9}};
      },
      encode:{x:[0,1]}, data: items}]
  });
})();

// 2) 分组对比
const barChart = echarts.init(document.getElementById('c_bar'));
(function(){
  const cats = ['向上∈震荡窗','向上∈趋势日','向下∈震荡窗','向下∈趋势日','基线·震荡日','基线·趋势日'];
  const fwd = [2.59, 5.28, 2.07, 1.83, 1.88, 3.97];
  const ex = [1.78, 3.19, 0.73, 0.97, 1.13, 2.22];
  const win = [57.1, 66.9, 58.0, 57.7, 58.2, 62.9];
  barChart.setOption({
    legend:{top:0,textStyle:{color:'#5a6577'}},
    grid:{left:50,right:60,top:44,bottom:34},
    tooltip:{trigger:'axis'},
    xAxis:{type:'category', data:cats, ...axStyle, axisLabel:{...axStyle.axisLabel, interval:0}},
    yAxis:[{type:'value', name:'收益 %', ...axStyle},{type:'value', name:'胜率 %', min:40, max:80, ...axStyle, splitLine:{show:false}}],
    series:[
      {name:'T+20收益', type:'bar', data:fwd, itemStyle:{color:'#185FA5'}, barWidth:22, label:{show:true,position:'top',formatter:'{c}%',color:'#444',fontSize:11}},
      {name:'超额T+20', type:'bar', data:ex, itemStyle:{color:'#85b7eb'}, barWidth:22},
      {name:'T+20胜率', type:'line', yAxisIndex:1, data:win, itemStyle:{color:'#d85a30'}, lineStyle:{width:2}, symbolSize:7, label:{show:true,position:'top',formatter:'{c}%',color:'#993C1D',fontSize:11}}
    ]
  });
})();

// 3) 假突破率
const fakeChart = echarts.init(document.getElementById('c_fake'));
(function(){
  const cats = ['向上∈震荡窗','向上∈趋势日','向下∈震荡窗','向下∈趋势日'];
  const fake = [53.3, 44.8, 64.5, 64.0];
  const surv = [57.9, 62.8, 46.6, 47.4];
  fakeChart.setOption({
    legend:{top:0,textStyle:{color:'#5a6577'}},
    grid:{left:50,right:50,top:44,bottom:34},
    tooltip:{trigger:'axis', valueFormatter:v=>v+'%'},
    xAxis:{type:'category', data:cats, ...axStyle, axisLabel:{...axStyle.axisLabel, interval:0}},
    yAxis:{type:'value', name:'%', min:0, max:80, ...axStyle},
    series:[
      {name:'假突破率（10日内）', type:'bar', data:fake, barWidth:34, itemStyle:{color:'#d85a30'}, label:{show:true,position:'top',formatter:'{c}%',color:'#993C1D',fontSize:12}},
      {name:'存活率（T+20未回撤5%）', type:'bar', data:surv, barWidth:34, itemStyle:{color:'#5DCAA5'}, label:{show:true,position:'top',formatter:'{c}%',color:'#085041',fontSize:12}}
    ]
  });
})();

window.addEventListener('resize', ()=>{mapChart.resize();barChart.resize();fakeChart.resize();});
</script>
</body>
</html>"""

html = HTML.replace("__WINS__", wins_json).replace("__DETAIL__", detail_json).replace("__MAIN__", json.dumps(d["summary"], ensure_ascii=False))

path = os.path.join(OUT, "index.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {path} {os.path.getsize(path)}")
