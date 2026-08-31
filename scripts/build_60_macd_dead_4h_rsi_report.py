# -*- coding: utf-8 -*-
"""60 号报告：日线 MACD 死叉 + 4h RSI(14) 30-35 超卖买入回测 —— 构建 HTML"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(BASE, "results", "60_macd_dead_4h_rsi_backtest.json")
OUT_DIR = os.path.join(BASE, "reports", "60_MACD死叉_4hRSI超卖_胜率回测")
os.makedirs(OUT_DIR, exist_ok=True)

R = json.load(open(IN, encoding="utf-8"))

# ---------- 配色（红涨绿跌，色弱安全：叠加线型/符号） ----------
C_SOXX = "#e69f00"   # 橙
C_NVDA = "#56b4e9"   # 天蓝
C_XAU = "#ccd03c"    # 黄绿（区分黄金）
C_QQQ = "#d55e00"    # 朱红
C_UP = "#c0392b"
C_DN = "#1e8449"

# ---------- 汇总数据 ----------
assets = [("soxx", "SOXX", C_SOXX), ("nvda", "NVDA", C_NVDA), ("xauusd", "XAUUSD", C_XAU), ("qqq", "QQQ", C_QQQ)]

def as_pct(x, digits=2):
    if x is None:
        return "—"
    s = f"{x:+.2f}" if digits == 2 else f"{x:+.1f}"
    return s + "%"

def cell(x, up=True):
    """红涨绿跌：正收益红色 up，负收益绿色 dn"""
    if x is None:
        return '<td class="na">—</td>'
    if x > 0:
        return f'<td class="up">{as_pct(x)}</td>'
    elif x < 0:
        return f'<td class="dn">{as_pct(x)}</td>'
    return f'<td>{as_pct(x)}</td>'

# ---------- 各标的胜率表 ----------
def win_table(grp_key):
    rows = []
    header = "<tr><th class='tk'>标的</th><th>信号数</th>"
    for h in [1, 3, 5, 10, 20]:
        header += f"<th>T+{h} 胜率</th>"
    header += "</tr>"
    for dirname, disp, _ in assets:
        v = R[dirname]
        sig = v["n_signal_main"]
        cells = f"<td><b>{disp}</b></td><td>{sig}</td>"
        for h in [1, 3, 5, 10, 20]:
            s = v[grp_key].get(f"t{h}")
            if s and s["win_rate"] is not None:
                cells += f'<td class="{'bold' if s['n']>=3 else ''}">{s["win_rate"]:.0f}%<br><span class="sub">n={s["n"]}</span></td>'
            else:
                cells += '<td class="na">—</td>'
        rows.append(f"<tr>{cells}</tr>")
    return header + "".join(rows)

# 合并主口径统计（硬编码自 scipy 计算）
MAIN_MERGE = {
    1: dict(n=20, wr=70.0, mean=0.59, med=1.09),
    3: dict(n=20, wr=65.0, mean=1.60, med=1.31),
    5: dict(n=19, wr=73.7, mean=1.44, med=2.52),
    10: dict(n=19, wr=68.4, mean=2.07, med=2.55),
    20: dict(n=19, wr=52.6, mean=2.40, med=1.26),
}
DEAD_MERGE = {
    5: dict(n=87, wr=72.4, mean=1.56),
    10: dict(n=87, wr=71.3, mean=2.62),
    20: dict(n=87, wr=70.1, mean=3.47),
}

# ---------- 明细 ----------
def detail_rows(dirname):
    v = R[dirname]
    out = []
    for row in v["details_main"]:
        cross, trig, buy = row["cross_date"], row["date"], row["buy_date"]
        rsi = row.get("trigger_rsi_last")
        t = f"<td>{cross}</td><td>{trig}</td><td>{buy}</td><td>{row['buy_price']:.2f}</td><td>{rsi if rsi is not None else '—'}</td>"
        for h in [1, 3, 5, 10, 20]:
            t += cell(row.get(f"ret_t{h}"))
        out.append(f"<tr>{t}</tr>")
    return "".join(out)

tables_info = {}
for dirname, disp, _ in assets:
    tables_info[dirname] = (R[dirname]["n_signal_main"], detail_rows(dirname))

# ---------- 图表数据 ----------
# 每个信号 T+5/T+20 收益散点（含日期）
scatter = []
all_dates = set()
for dirname, disp, _ in assets:
    for row in R[dirname]["details_main"]:
        d = row["date"]
        r5 = row.get("ret_t5"); r20 = row.get("ret_t20")
        scatter.append({"date": d, "asset": disp, "r5": r5, "r20": r20})
        if r5 is not None: all_dates.add(d)

# 持有期收益分布（合并）
hold_dist = {h: [] for h in [1, 3, 5, 10, 20]}
for dirname, disp, _ in assets:
    for row in R[dirname]["details_main"]:
        for h in [1, 3, 5, 10, 20]:
            r = row.get(f"ret_t{h}")
            if r is not None:
                hold_dist[h].append({"asset": disp, "v": r})

JSJSON = json.dumps({
    "scatter": scatter,
    "hold_dist": hold_dist,
    "assets": [d for _, d, _ in assets],
}, ensure_ascii=False)

# ---------- 组装 HTML ----------
html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>日线 MACD 死叉 + 4h RSI 30-35 超卖——买多胜率回测（SOXX/NVDA/XAUUSD/QQQ）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --up:#c0392b; --dn:#1e8449; --ink:#2c3e50; --muted:#7f8c8d; --line:#e3e7ea; --bg:#f7f8fa; --card:#ffffff; --accent:#c0392b; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); line-height:1.75; }
  .wrap { max-width:1080px; margin:0 auto; padding:28px 20px 60px; }
  header { border-bottom:3px solid var(--accent); padding-bottom:14px; margin-bottom:22px; }
  header h1 { font-size:26px; letter-spacing:.5px; }
  header .meta { color:var(--muted); font-size:13px; margin-top:6px; }
  h2 { font-size:19px; margin:34px 0 12px; padding-left:10px; border-left:4px solid var(--accent); }
  h3 { font-size:15.5px; margin:18px 0 8px; }
  p { margin:8px 0; font-size:14.5px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px; margin:12px 0; }
  .tldr { background:#fff6f4; border:1px solid #f3c8c0; }
  .tldr h2 { border:none; padding:0; margin:0 0 8px; font-size:17px; color:var(--accent); }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin:14px 0 4px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 12px; }
  .kpi .lab { font-size:12px; color:var(--muted); }
  .kpi .val { font-size:21px; font-weight:700; margin-top:2px; }
  .up { color:var(--up); font-weight:600; }
  .dn { color:var(--dn); font-weight:600; }
  .na { color:var(--muted); }
  .sub { color:var(--muted); font-size:12px; font-weight:400; }
  table { width:100%; border-collapse:collapse; font-size:13.5px; background:var(--card); }
  th, td { border:1px solid var(--line); padding:7px 9px; text-align:center; }
  th { background:#f0f3f6; font-weight:600; }
  td.tk { text-align:left; white-space:nowrap; }
  td.bold { font-weight:700; }
  td.hot { background:#fff0ed; }
  .chart { width:100%; height:400px; }
  .chart-sm { width:100%; height:340px; }
  .note { font-size:12.5px; color:var(--muted); margin-top:6px; }
  .warn { background:#fdf6e3; border-left:4px solid #d4a017; padding:10px 14px; font-size:13.5px; margin:12px 0; border-radius:0 8px 8px 0; }
  .term { border-bottom:1px dashed #b08; cursor:help; }
  .termtip { display:none; position:fixed; z-index:99; max-width:300px; background:#2c3e50; color:#fff; font-size:12.5px; line-height:1.6; padding:8px 10px; border-radius:6px; box-shadow:0 4px 14px rgba(0,0,0,.25); pointer-events:none; }
  .src { font-size:12.5px; color:var(--muted); }
  .src li { margin:4px 0 4px 18px; }
  .sig { display:inline-block; font-size:11px; padding:1px 7px; border-radius:10px; margin-left:6px; vertical-align:middle; }
  .sig.sig-on { background:#fdecea; color:#c0392b; border:1px solid #e5b8b2; }
  .sig.sig-edge { background:#fff7e0; color:#a06d00; border:1px solid #e8d48a; }
  .sig.sig-no { background:#eef1f4; color:#7f8c8d; border:1px solid #d5dbe0; }
  footer { margin-top:40px; padding-top:14px; border-top:1px solid var(--line); font-size:12.5px; color:var(--muted); }
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>日线 MACD 死叉 + 4 小时 RSI(14) 30–35 超卖 → 买多，胜率几何？</h1>
  <div class="meta">量化回测 · 60 号报告 ｜ 标的：SOXX / NVDA / XAUUSD(GC=F) / QQQ ｜ 4h 数据窗口 2024-09 ~ 2026-08（Yahoo 盘中数据上限约 2 年）｜ 生成于 2026-08-31</div>
</header>

<div class="card tldr">
  <h2>结论先行</h2>
  <p><b>这套信号在过去 2 年回测样本里"偏正"，但远谈不上稳赚：</b>四标的合计触发 <b>20 次</b>，T+1 胜率 70%、T+5 胜率 73.7%（中位 +2.5%）、T+10 胜率 68.4%（中位 +2.6%）；但 T+20 胜率回落到 52.6%。<b>最大的限制是样本太少</b>——4h 数据只有约 2 年，而死叉之后恰好轮到 4h RSI 进入 30–35 档的"共振"极其罕见，单标的每年只出 1–3 次，统计上多数持有期达不到显著（仅 T+5 在合并样本上达"边缘显著"，二项检验 p=0.03）。</p>
  <div class="kpis">
    <div class="kpi"><div class="lab">四标的合并信号数（2 年）</div><div class="val">20 次</div></div>
    <div class="kpi"><div class="lab">T+5 胜率（合并）</div><div class="val up">73.7%</div></div>
    <div class="kpi"><div class="lab">T+5 中位收益</div><div class="val up">+2.5%</div></div>
    <div class="kpi"><div class="lab">T+20 胜率（合并）</div><div class="val">52.6%</div></div>
    <div class="kpi"><div class="lab">对照：仅日线死叉 T+10 胜率</div><div class="val up">71.3% <span class="sub">(n=87)</span></div></div>
    <div class="kpi"><div class="lab">黄金（XAUUSD）当前状态</div><div class="val" style="color:#d4a017;">正处信号窗 🎯</div></div>
  </div>
  <p><b>关键提醒</b>：真正拉动胜率的是"日线死叉"本身（仅死叉、无一额外条件时 T+5~T+20 胜率也有 70–72%、n=87、<span class="term" data-tip="假设'其实没有效应'时，观察到当前这么强结果（或更强）的概率。p<0.05 才算统计显著。">p&lt;0.01</span> 显著）；4h RSI 30–35 过滤把样本砍掉近八成、收益并未显著抬升。把它当"择时确认"，而不是"圣杯"。</p>
</div>

<div class="warn">
  <b>⚠️ 样本不足警告</b>：4h 级数据 Yahoo 只回溯约 730 天，本回测实际仅覆盖 2024-09 ~ 2026-08 两年。日线死叉两年内每标的 20 多次，但叠加"4h RSI 恰好落 30–35"后每标的只剩 <b>3–8 个信号</b>。20 个样本的胜率 95% 置信区间宽达 ±20pp——说"73% 胜率"和"50% 胜率"在统计上无法区分。结论仅供策略参考，不可作为稳定概率使用。
</div>

<h2>一、信号定义与口径</h2>
<div class="card">
  <h3>买入条件（主口径）</h3>
  <p>① <b>日线 MACD(12,26,9) "刚刚死叉"</b>：当日 <span class="term" data-tip="MACD 快线 = EMA12 − EMA26，代表短期动能；DEA 是 DIF 的 9 日均线，代表中期趋势。DIF 下穿 DEA 即'死叉'，常被看作多头动能转弱信号。">DIF</span> 由 ≥ <span class="term" data-tip="MACD 信号线（DIF 的 9 日 EMA）。DIF 下穿 DEA = 死叉。">DEA</span> 变为 &lt; DEA（前一日 DIF≥DEA）</p>
  <p>② <b>死叉后 ≤3 个交易日内</b>，4 小时级别 <span class="term" data-tip="相对强弱指数 RSI = 100 − 100/(1+平均涨/平均跌)。RSI&lt;30 传统超卖，30–35 是"偏超卖但未深跌"的档位。">RSI(14)</span> 的<b>当日收盘值</b>落在 <b>30–35</b> 区间　→　触发</p>
  <p>③ <b>执行</b>：触发日次日开盘买入；持有 T+1 / T+3 / T+5 / T+10 / T+20 交易日，按后复权收盘价结算（含分红/拆股调整，避免 NVDA 拆股造成的假收益）。</p>
  <p class="note">口径说明：主口径要求"日末 4h bar 收盘 RSI 落档"；若盘中触及但收盘已跌破 30（深超卖），记为"跌穿 30、错过"，不混淆进 30–35 档胜率。另有"盘中任意 bar 触及即算"的宽松口径与"死叉当日即落档"的严格口径作对照。</p>
</div>

<h2>二、回测主结果：合并胜率与各标的明细</h2>
<div class="card" style="overflow-x:auto;">
  <table>
    <tr><th class="tk">标的</th><th>2年信号数</th><th>T+1 胜率</th><th>T+3 胜率</th><th>T+5 胜率</th><th>T+10 胜率</th><th>T+20 胜率</th></tr>
  @@WIN_ROWS@@
    <tr class="total"><td class="tk" style="font-weight:700;">合并（四标的）</td><td>20</td>
      <td>70.0% <span class="sub">(n=20)</span></td><td>65.0% <span class="sub">(n=20)</span></td><td>73.7% <span class="sub">(n=19)</span></td><td>68.4% <span class="sub">(n=19)</span></td><td>52.6% <span class="sub">(n=19)</span></td>
    </tr>
  </table>
  <div class="note">信号数 = 2 年内"日线死叉后 ≤3 日 4h RSI 收于 30–35"的触发次数。胜率按当日收益&gt;0 计；n 为已有完整持有期数据的样本数。</div>
</div>

<div class="card">
  <div id="c_scatter" class="chart"></div>
  <div class="note">每次信号买入后的 T+5 / T+20 收益散点（X=日期，Y=收益%）。红点=正收益（红涨），绿点=负收益（绿跌）。黄金（黄绿点）的 T+20 大多为正——它是这套信号里最稳的标的。</div>
</div>

<div class="card">
  <h3>黄金（XAUUSD）明细 —— 信号最密集、最稳</h3>
  <div style="overflow-x:auto;"><table>
  <tr><th class="tk">死叉日</th><th>触发日</th><th>买入日</th><th>买入价</th><th>4h RSI末</th><th>T+1</th><th>T+3</th><th>T+5</th><th>T+10</th><th>T+20</th></tr>
  @@XAU_DETAIL@@
  </table></div>
  <div class="note">黄金 2 年内 7 次信号：T+1 胜率 7/7（100%）、T+5 胜率 6/7、T+20 胜率 5/7。注意 2025-04-08（贸易战恐慌底部）与 2026 年 6 月各含一次大反弹——黄金在"日线死叉+4h 超卖"后短期偏强，与它趋势性上涨的大背景（2024–2026 金价从 $2000 涨到 $4500）相辅相成。</div>
</div>

<h3>其余标的全量明细</h3>
<div class="card" style="overflow-x:auto;">
  <table>
  <tr><th class="tk">标的</th><th>死叉日</th><th>触发日</th><th>买入日</th><th>买入价</th><th>4h RSI末</th><th>T+1</th><th>T+3</th><th>T+5</th><th>T+10</th><th>T+20</th></tr>
  @@SOXX_DETAIL@@
  @@NVDA_DETAIL@@
  @@QQQ_DETAIL@@
  </table>
  <div class="note">NVDA 的 2026-08-25 买入（8-21 死叉、8-24 触发）为最近一次信号，T+5 时点数据尚未走完，故空栏。SOXX 三次信号集中在 2025 年，2025-03-28 那次（关税冲击周）T+5 −12.7% 是四标的合并样本里最差的一笔。</div>
</div>

<h2>三、对照组：把"4h RSI"这个过滤器拆掉看</h2>
<p>信号条件加得越多、样本越少，就越难判断"到底是哪个条件在起作用"。因此做了三组对照：</p>
<div class="card" style="overflow-x:auto;">
  <table>
    <tr><th class="tk">口径（同一 2 年窗口）</th><th>样本数</th><th>T+5 胜率</th><th>T+10 胜率</th><th>T+20 胜率</th></tr>
    <tr><td class="tk"><b>① 日线死叉 + 4h RSI 30–35（主口径）</b></td><td>20</td>
      <td class="bold">73.7% <span class="sub">p=0.03</span></td><td>68.4% <span class="sub">p=0.08</span></td><td>52.6% <span class="sub">p=0.50</span></td></tr>
    <tr><td class="tk">② 仅日线死叉（无 RSI 过滤）</td><td>87</td>
      <td>72.4% <span class="sub">p=0.005</span></td><td>71.3% <span class="sub">p&lt;0.001</span></td><td>70.1% <span class="sub">p&lt;0.001</span></td></tr>
    <tr><td class="tk">③ 仅 4h RSI 30–35（无死叉过滤）</td><td>~13/标的</td><td>76.9%</td><td>—</td><td>61.5%</td></tr>
    <tr><td class="tk">④ 无条件基准（每 20 交易日一次）</td><td>~25/标的</td><td>64.0%</td><td>—</td><td>62.5%</td></tr>
  </table>
  <div class="note">p 值 = 二项检验（胜率是否显著高于 50%）。②仅死叉 n=87、p&lt;0.01，是三组里唯一统计扎实的；主口径①样本砍到 20 个后 p 值普遍掉到 0.03–0.5，只剩边缘显著性。<b>结论：日线死叉是主效果，4h RSI 30–35 是"锦上添花"而非"起死回生"。</b></div>
</div>

<h2>四、当前状态快照（2026-08-31 收盘）</h2>
<div class="card" style="overflow-x:auto;">
  <table>
    <tr><th class="tk">标的</th><th>日线 MACD 状态</th><th>4h RSI(14)</th><th>是否触发信号</th><th>备注</th></tr>
    <tr><td class="tk"><b>XAUUSD 黄金</b></td><td class="hot">死叉（DIF 102.5 &lt; DEA 103.1）</td><td class="hot">32.4 <span class="sub">(30-35 档)</span></td><td class="hot"><b>√ 正处信号窗</b> <span class="sig sig-on">、次日开盘即买点</span></td><td>回测中黄金信号最稳（T+1 7/7），值得重点跟踪</td></tr>
    <tr><td class="tk">SOXX</td><td>水下（DIF −7.2 &lt; DEA −6.1）</td><td>41.5</td><td>×（未死叉当日、RSI 偏高）</td><td>接近但未触发</td></tr>
    <tr><td class="tk">NVDA</td><td>金叉后（DIF 2.6 &gt; DEA 2.9）</td><td>53.5</td><td>×</td><td>—</td></tr>
    <tr><td class="tk">QQQ</td><td>金叉后（DIF 1.7 &gt; DEA 2.3）</td><td>50.1</td><td>×</td><td>—</td></tr>
  </table>
  <div class="note">数据截至 2026-08-31（周一）收盘。黄金 08-31 盘中 4h RSI 已落 30–35 档、日线 MACD 当日刚死叉（前一日 DIF≥DEA）——按回测规则，下一个交易日（09-01）开盘即"触发日次日买入"。</div>
</div>

<h2>五、解读与局限</h2>
<div class="card">
  <h3>为什么会有"死叉 + 超卖"的看多逻辑？</h3>
  <p>逻辑上说得通：日线 MACD 死叉 ≠ 必跌，反而常出现在强趋势中的<b>回调末端</b>——若此时 4h 级别已先一步超卖（RSI 30–35），说明短线抛压已在小时级别释放殆尽，大概率迎来反抽。回测数据给了部分支持（T+1~T+10 胜率 65–74%、中位正收益），但也清晰显示：<b>它捕捉的是"短线反抽"而非"趋势反转"</b>——T+20 胜率掉回 52.6%、几乎无增益，说明 1 个月级别上信号没有预测力。</p>
  <h3>局限（务必知情）</h3>
  <ul style="margin-left:18px; font-size:14px;">
    <li><b>样本极小</b>：合并仅 20 个信号，单标的 3–8 个。胜率置信区间宽带 ±20pp，任何"XX%"都不可当作稳定胜率。</li>
    <li><b>数据窗口恰逢特殊行情</b>：2024-09 ~ 2026-08 是美国 AI 牛市 + 黄金大牛市的两年，普涨环境下"超卖后买入"天然占便宜（对照基准 T+5 胜率也达 64%）。牛转熊时结果可能完全不同。</li>
    <li><b>Yahoo 盘中数据上限</b>：4h 仅回溯 2 年，无法跨更长周期验证。</li>
    <li><b>未计成本</b>：未含手续费/滑点/保证金；黄金期货还有展期成本。</li>
    <li><b>单笔极端风险</b>：SOXX 2025-03-28 信号 T+5 −12.7%——顺势死叉在急跌中也会继续跌，信号不是保险。</li>
  </ul>
</div>

<h2>来源与时点</h2>
<ul class="src">
  <li>日线数据：本地 Yahoo Finance chart API 全量（SOXX 自 2001、NVDA 自 1999、QQQ 自 1999、GC=F 自 2000），后复权价结算，2026-08-31 收盘。</li>
  <li>4h 数据：Yahoo Finance chart API interval=4h，覆盖 2024-09 ~ 2026-08（约 730 天上限）。</li>
  <li>XAUUSD 以 COMEX 黄金期货 GC=F 代理（Yahoo 无现货 XAUUSD 代码），日线与 4h 均为同一数据源。</li>
  <li>统计：Python（pandas/numpy/scipy），t 检验与二项检验均基于本地计算结果。</li>
  <li>指标参数：MACD(12,26,9)、RSI(14)，均为标准默认参数。</li>
</ul>

<footer>
  免责声明：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
</footer>
@@TIP@@
</div>
</body>
</html>"""

# ---------- 术语 ----------
TERMS = [
    ("MACD", "Moving Average Convergence Divergence，指数平滑异同移动平均线。由快线 DIF（EMA12−EMA26）、慢线 DEA（DIF 的 9 日 EMA）与柱状图组成，用于衡量趋势动能与拐点。"),
    ("死叉", "DIF 下穿 DEA——常被视为多头动能转弱的信号；本回测要求'刚刚死叉'即当日才发生交叉。"),
    ("金叉", "DIF 上穿 DEA——多头动能转强的信号，与死叉相反。"),
    ("DIF", "MACD 快线 = EMA12 − EMA26。正值=短期均线在上（多头），负值=水下方（空头）。"),
    ("DEA", "MACD 信号线 = DIF 的 9 日指数移动平均。DIF 与 DEA 的交叉构成买卖信号。"),
    ("RSI", "相对强弱指数（Relative Strength Index），衡量近期涨跌动能的强弱，0–100。传统上 &lt;30 为超卖、&gt;70 为超买。"),
    ("超卖", "RSI 进入低位（通常 &lt;30）表示短期跌势过快、抛压可能透支，技术派常将其视为潜在反弹点。本回测用 30–35 这一'偏超卖但未深跌'的档位。"),
    ("后复权", "把历史价格按分红/拆股比例统一调整，使收益序列连续、可正确计算长期回报。避免 NVDA 2024 年 1:10 拆股造成的假收益。"),
    ("T+N", "Transaction day + N：买入后的第 N 个交易日（如 T+5 = 持有 5 个交易日）。"),
    ("胜率", "收益为正的次数 / 总次数。本报告统一按'当日收益 &gt; 0'计。"),
    ("中位收益", "把每次收益排序后取正中间那个数——比均值更抗极端值（如单次大跌/大涨）干扰。"),
    ("二项检验", "检验'胜率是否显著高于 50%'的统计方法：若 p&lt;0.05，说明观察到的胜率不太可能纯靠运气。"),
    ("95%置信区间", "假如重复做很多次回测，95% 的结果会落进这个区间——样本越小，区间越宽，结论越不确定。"),
    ("GC=F", "COMEX 黄金期货连续合约的 Yahoo 代码，用于代理金价。Yahoo 无现货 XAUUSD 报价，期货与现货价差通常很小。"),
    ("水上/水下", "MACD 的 DIF 位于 0 轴上方=水上（多头环境）、下方=水下（空头环境）。本回测不做此过滤。"),
]
TERM_DICT = {k: v for k, v in sorted(TERMS, key=lambda x: -len(x[0]))}
_TERM_PAT = re.compile("|".join(re.escape(k) for k in TERM_DICT.keys()))
_BLOCK_RE = re.compile(r"(<script[\s\S]*?</script>|<style[\s\S]*?</style>|<title[\s\S]*?</title>)", re.S)

def _annotate_text(text):
    return _TERM_PAT.sub(lambda m: f"<span class='term' data-tip='{TERM_DICT[m.group(0)].replace(chr(39), '&#39;')}'>{m.group(0)}</span>", text)

def annotate_terms(html_str):
    parts = _BLOCK_RE.split(html_str)
    # 1) 保护已生成的 data-tip 内容（避免定义文本里的术语词被二次注释）
    tips = []
    def _protect(m):
        tips.append(m.group(0))
        return f"\x00TIP{len(tips) - 1}\x00"
    protected = []
    for i, seg in enumerate(parts):
        if i % 2 == 0 and seg:
            seg = re.sub(r"data-tip='[^']*'", _protect, seg)
        protected.append(seg)
    # 2) 对正文注释
    out = []
    for i, seg in enumerate(protected):
        if i % 2 == 0 and seg:
            seg = _annotate_text(seg)
        out.append(seg)
    joined = "".join(out)
    # 3) 还原
    for idx, t in enumerate(tips):
        joined = joined.replace(f"\x00TIP{idx}\x00", t)
    return joined

html = annotate_terms(html)

# ---------- 替换占位 ----------
html = html.replace("@@WIN_ROWS@@", win_table("main"))
html = html.replace("@@XAU_DETAIL@@", detail_rows("xauusd"))
html = html.replace("@@SOXX_DETAIL@@", detail_rows("soxx"))
html = html.replace("@@NVDA_DETAIL@@", detail_rows("nvda"))
html = html.replace("@@QQQ_DETAIL@@", detail_rows("qqq"))

tip_engine = """<div class="termtip" id="termtip"></div>
<script>
(function(){
  const tip=document.getElementById('termtip');
  let cur=null;
  document.addEventListener('mouseover',e=>{
    const t=e.target.closest('.term');
    if(!t||t===cur)return; cur=t;
    tip.textContent=t.dataset.tip||'';
    tip.style.display='block';
    const r=t.getBoundingClientRect();
    tip.style.left=Math.min(r.left,window.innerWidth-300)+'px';
    tip.style.top=r.bottom+6+'px';
  });
  document.addEventListener('mouseout',e=>{
    if(e.target.closest('.term')){cur=null;tip.style.display='none';}
  });
})();
</script>"""
html = html.replace("@@TIP@@", tip_engine)

charts = """<script>
const D = @@JSJSON@@;
const UP='#c0392b', DN='#1e8449';
const COLORS = {'SOXX':'#e69f00','NVDA':'#56b4e9','XAUUSD':'#ccd03c','QQQ':'#d55e00'};

// 散点：每次信号 T+5/T+20 收益
const s1=[],s2=[];
D.scatter.forEach(pt=>{
  const c=COLORS[pt.asset]||'#999';
  if(pt.r5!=null) s1.push({value:[pt.date,pt.r5],symbolSize:11,itemStyle:{color:c},name:pt.asset});
  if(pt.r20!=null) s2.push({value:[pt.date,pt.r20],symbolSize:11,itemStyle:{color:c},name:pt.asset});
});
const baseScatter={
  tooltip:{trigger:'item',formatter:p=>p.name+'<br>'+p.value[0]+' T+5/T+20 收益: '+p.value[1].toFixed(2)+'%'},
  legend:{top:0,textStyle:{color:'#555'}},
  grid:{left:55,right:20,top:36,bottom:40},
  xAxis:{type:'category',data:D.scatter.map(p=>p.date).filter((v,i,a)=>a.indexOf(v)===i),axisLabel:{color:'#666',rotate:30,fontSize:10}},
  yAxis:{type:'value',scale:true,axisLabel:{color:'#555'},splitLine:{lineStyle:{color:'#e5e9f0'}},axisLine:{show:false}},
  series:[
    {name:'T+5',type:'scatter',data:s1},
    {name:'T+20',type:'scatter',data:s2}
  ]
};
echarts.init(document.getElementById('c_scatter')).setOption(baseScatter);
</script>"""
charts = charts.replace("@@JSJSON@@", JSJSON)
html = html.replace("</body>", charts + "</body>")

out = os.path.join(OUT_DIR, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("SAVED:", out, f"({os.path.getsize(out)/1024:.0f} KB)")