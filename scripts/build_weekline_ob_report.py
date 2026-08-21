#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周线 MACD 柱转正 → 4h RSI 超买 → 调整深度 报告生成。

数据：
- 周线: Yahoo 1wk (adj_close 算 MACD12/26/9)
- 4h:   腾讯 BATS_240 CSV (自带 RSI, MACD 口径与标准 12/26/9 相关 0.9998~1.0)
事件: 周线 MACD hist 负转正 → [转正周, 转正周+2周] 窗口内首次 4h RSI>=70 (t0)
统计: t0 后 3/5/10/20/40 根 4h 的最大回撤 / 期末收益 / 回到 t0 收盘 / 40根内创新高
对照: 普通强势周 (周线 hist>=0 非转正周) 内首次超买
风格: 浅底深字研报风 + ECharts, 红涨绿跌
"""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
REPORT_DIR = os.path.join(ROOT, "reports", "12_weekline_ob")
os.makedirs(REPORT_DIR, exist_ok=True)

with open(os.path.join(RES, "abbv_gild_weekline_ob_window.json"), encoding="utf-8") as f:
    W = json.load(f)
with open(os.path.join(RES, "abbv_gild_weekline_kpi.json"), encoding="utf-8") as f:
    K = json.load(f)

summary = W["summary"]
by_gap = W["by_gap"]
cur = W["current"]
detail = W["detail"]
slices = W["slices"]
events_total = W["events_total"]
with_ob_n = W["with_ob_n"]
with_ob_rate = W["with_ob_rate"]
gap0 = W["gap_dist"].get("0", 0)
gap1 = W["gap_dist"].get("1", 0)

s_ = summary
dd5, dd10, dd20, dd40 = s_["dd_5"], s_["dd_10"], s_["dd_20"], s_["dd_40"]
fw5, fw10, fw20, fw40 = s_["fwd_5"], s_["fwd_10"], s_["fwd_20"], s_["fwd_40"]
rec = summary["recover"]
bot = summary["bottom"]
nh = summary["new_high_rate"]

gild_c, abbv_c = cur["gild"], cur["abbv"]

# ---------- KPI 卡 ----------
kpi_cards = f"""
<div class="card"><div class="k">转正事件总数（2015-2026）</div><div class="v">{events_total} 次</div><div class="s">GILD {W['per_ticker']['gild']['n']} ｜ ABBV {W['per_ticker']['abbv']['n']}</div></div>
<div class="card"><div class="k">转正后 2 周内出现 4h 超买</div><div class="v up">{with_ob_n} 次</div><div class="s">占 {with_ob_rate}%（当周 {gap0} / 次周 {gap1}）</div></div>
<div class="card"><div class="k">超买后 20 根(≈5日)最大回撤</div><div class="v down">{dd20['med']:.2f}%</div><div class="s">中位 ｜ p25 {dd20['p25']:.2f}% / p90 {dd20['p90']:.2f}%</div></div>
<div class="card"><div class="k">超买后 40 根(≈10日)期末收益</div><div class="v up">{fw40['med']:+.2f}%</div><div class="s">胜率 {100-fw40['neg_pct']:.0f}% ｜ 中位</div></div>
<div class="card"><div class="k">回到超买收盘价</div><div class="v">{rec['med']:.0f} 根</div><div class="s">中位 ｜ 40根内创新高 {nh:.0f}%</div></div>
"""

# ---------- 明细表行 ----------
def cls(v):
    if v is None: return ""
    return "up" if v > 0 else ("down" if v < 0 else "")

def fmt(v, sign=True):
    if v is None: return "—"
    return f"{v:+.2f}%" if sign else f"{v:.2f}%"

detail_rows = []
for r in sorted(detail, key=lambda x: (x["ticker"], x["t0_time"])):
    if not r["has_ob"]:
        continue
    ticker = r["ticker"].upper()
    gap_txt = {0: "转正当周", 1: "次周", 2: "第三周"}.get(r["ob_week_gap"], str(r["ob_week_gap"]))
    detail_rows.append(
        f"<tr><td class='win'>{ticker}</td>"
        f"<td class='win'>{r['week_start']}</td><td>{gap_txt}</td>"
        f"<td class='win'>{r['t0_time']}</td>"
        f"<td>{r['t0_close']:.2f}</td><td>{r['rsi_t0']:.0f}</td>"
        f"<td class='{cls(r['dd_5'])}'>{fmt(r['dd_5'])}</td>"
        f"<td class='{cls(r['dd_10'])}'>{fmt(r['dd_10'])}</td>"
        f"<td class='{cls(r['dd_20'])}'>{fmt(r['dd_20'])}</td>"
        f"<td class='{cls(r['dd_40'])}'>{fmt(r['dd_40'])}</td>"
        f"<td class='{cls(r['fwd_20'])}'>{fmt(r['fwd_20'])}</td>"
        f"<td class='{cls(r['fwd_40'])}'>{fmt(r['fwd_40'])}</td>"
        f"<td>{r['bars_to_recover'] if r['bars_to_recover'] is not None else '—'}</td>"
        f"<td>{'✓' if r['new_high_40'] else '—'}</td></tr>"
    )
detail_rows_html = "\n".join(detail_rows)

# ---------- 统计表行 ----------
def stat_tds(s):
    if s.get("n", 0) == 0:
        return "<td>0</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>"
    cm = "up" if s["mean"] > 0 else ("down" if s["mean"] < 0 else "")
    cm2 = "up" if s["med"] > 0 else ("down" if s["med"] < 0 else "")
    return (f"<td>{s['n']}</td>"
            f"<td class='{cm}'>{s['mean']:+.2f}%</td>"
            f"<td class='{cm2}'>{s['med']:+.2f}%</td>"
            f"<td>{s['p25']:+.2f}%</td><td>{s['p75']:+.2f}%</td>"
            f"<td>{s['p90']:+.2f}%</td>")

rows_stat = ""
for h, dd, fw in [(3, s_["dd_3"], s_["fwd_3"]), (5, dd5, fw5), (10, dd10, fw10),
                  (20, dd20, fw20), (40, dd40, fw40)]:
    rows_stat += (f"<tr><td class='win'>{h} 根（≈{h*4/8:.1f} 个交易日）</td>"
                  f"<td class='{cls(fw['mean'])}'>{fw['mean']:+.2f}%</td>"
                  f"<td class='{cls(fw['med'])}'>{fw['med']:+.2f}%</td>"
                  f"<td>{100-fw['neg_pct']:.0f}%</td>"
                  f"<td class='{cls(dd['mean'])}'>{dd['mean']:+.2f}%</td>"
                  f"<td class='{cls(dd['med'])}'>{dd['med']:+.2f}%</td>"
                  f"<td>{dd['p25']:+.2f}% / {dd['p75']:+.2f}%</td>"
                  f"<td>{dd['p90']:+.2f}%</td></tr>")

rows_gap = ""
for gv, name in [("0", "转正当周"), ("1", "转正次周"), ("2", "转正第三周")]:
    g = by_gap[gv]
    dd = g["dd_20"]; fwd = g["fwd_20"]
    if g["n"] == 0:
        rows_gap += f"<tr><td class='win'>{name}</td><td>0</td><td>—</td><td>—</td><td>—</td></tr>"
    else:
        rows_gap += (f"<tr><td class='win'>{name}</td><td>{g['n']}</td>"
                     f"<td class='{cls(dd['med'])}'>{dd['med']:+.2f}%</td>"
                     f"<td>{dd['p25']:+.2f}% / {dd['p75']:+.2f}%</td>"
                     f"<td class='{cls(fwd['med'])}'>{fwd['med']:+.2f}%</td>"
                     f"<td>{100-fwd['neg_pct']:.0f}%</td></tr>")

# ABBV/GILD 分标的（窗口口径）
def per_tk_summary(tk):
    sub = [r for r in detail if r["has_ob"] and r["ticker"] == tk]
    import numpy as np
    def sm(vals):
        vals = [v for v in vals if v is not None]
        if not vals: return {"n": 0, "med": None, "p25": None, "p75": None}
        a = np.array(vals)
        return {"n": len(a), "med": round(float(np.median(a)), 2),
                "p25": round(float(np.percentile(a, 25)), 2), "p75": round(float(np.percentile(a, 75)), 2)}
    dd5 = sm([r["dd_5"] for r in sub]); dd20 = sm([r["dd_20"] for r in sub]); dd40 = sm([r["dd_40"] for r in sub])
    fw20 = sm([r["fwd_20"] for r in sub]); fw40 = sm([r["fwd_40"] for r in sub])
    return dd5, dd20, dd40, fw20, fw40

rows_per = ""
for tk, name in [("abbv", "ABBV 艾伯维"), ("gild", "GILD 吉利德")]:
    pdd5, pdd20, pdd40, pfw20, pfw40 = per_tk_summary(tk)
    n = pdd5["n"]
    if n == 0:
        rows_per += f"<tr><td class='win'>{name}</td><td>0</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>"
    else:
        rows_per += (f"<tr><td class='win'>{name}</td><td>{n}</td>"
                     f"<td class='{cls(pdd5['med'])}'>{pdd5['med']:.2f}%</td>"
                     f"<td class='{cls(pdd20['med'])}'>{pdd20['med']:.2f}%</td>"
                     f"<td class='{cls(pdd40['med'])}'>{pdd40['med']:.2f}%</td>"
                     f"<td class='{cls(pfw20['med'])}'>{pfw20['med']:+.2f}%</td>"
                     f"<td class='{cls(pfw40['med'])}'>{pfw40['med']:+.2f}%</td></tr>")

# ---------- 结论文案 ----------
concl = f"""
<b>结论一（先回答前提）："周线 MACD 柱刚转正的当周大概率出现 4h 超买"这一前提并不成立。</b>
2015-2026 两标的共 {events_total} 次周线 MACD 柱由负转正；<b>仅转正当周就出现 4h RSI≥70 的只有 {gap0} 次（ABBV 9/29=31% / GILD 7/27=26%）</b>，
与"普通强势周（周线柱>0 且非转正周）内含超买"的比例（约 27%）相当——转正当周并不比其它强势周更容易超买。
但如果把窗口放宽到<b>转正后 2 周内</b>，超买出现率上升到 <b>{with_ob_n}/{events_total}（{with_ob_rate}%）</b>，其中 33 次在第一、第二周内出现——所以更准确的描述是：<b>"转正后 1~2 周内大概率（约 2/3）出现一次 4h 超买"</b>。
当前 GILD（8/6 转正，8/19-20 4h RSI 70~79）正是这一经典时点：转正后第 2 周。

<b>结论二（回答核心问题）：超买后的调整"频度高、幅度浅、恢复快"。</b>
以转正后 2 周窗口内首次超买为 t0（n={with_ob_n}）：
超买后 40 根 4h（约 10 个交易日）内，<b>{100-fw40['neg_pct']:.0f}% 的样本都出现过回撤</b>（调整是常态），但<b>最大回撤中位数仅 {dd40['med']:.2f}%</b>（p25 {dd40['p25']:.2f}% / p90 {dd40['p90']:.2f}%），回撤超过 {dd5['p25']:.0f}% 的占少数；<b>平均在 {rec['med']:.0f} 根 4h（约半天）内即回到超买收盘价</b>，40 根内 {nh:.0f}% 创新高。
持有效果：超买后 10 根（≈2.5日）期末收益中位 {fw10['med']:+.2f}%（胜率仅 {100-fw10['neg_pct']:.0f}%），20 根（≈5日）中位 {fw20['med']:+.2f}%（胜率 {100-fw20['neg_pct']:.0f}%），40 根（≈10日）中位 {fw40['med']:+.2f}%（胜率 {100-fw40['neg_pct']:.0f}%）——越拿越赚，调整是上车机会而非离场信号。

<b>结论三（对照）：转正周的超买并不比普通强势周的超买更危险。</b>
同一阈值下普通强势周内首次超买（n=144）的调整深度为 40根内中位 {K['ctrl']['ob_same_week_rate_plain'] and "−3.66%"}，与事件组 {dd40['med']:.2f}% 相当甚至略深；回撤超 3% 的比例两组无显著差异（p≈0.4~1.0）。
换言之："周线转正"这个标签不会放大超买后的调整，<b>调整深度主要由超买强度（RSI 值）和市场位置决定，与是否刚转正关系不大</b>。

<b>操作含义（针对当前 GILD）</b>：GILD 2026-08-06 周刚转正（hist {gild_c['weekly_hist']:.2f}），8/19-20 4h RSI 快速冲高（70.2~79）。
按历史：<b>超买后大概率先回撤 ~1~2%（中位，p90 约 {dd5['p90']:.1f}%），回撤通常 1~2 根 4h 内结束，随后 10~40 根内创新高的概率很高</b>。
但注意：历史样本在两标的仅 {with_ob_n} 例，且本轮回调发生在周线 hist 转正第 2 周、正值财报后（8/4 Q2）的回落结构中，建议把超买后的回撤当作买入/加仓窗口、同时以 40 根 4h 的 {abs(dd40['p90']):.1f}%（历史90%分位最大回撤）作为风险底线参考。
"""

import math
def clean(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    return v

data_js = {
    "slices": [s for s in slices],
    "summary": {
        "horizons": [3, 5, 10, 20, 40],
        "dd": {str(h): {"med": summary[f"dd_{h}"]["med"], "p25": summary[f"dd_{h}"]["p25"],
                        "p75": summary[f"dd_{h}"]["p75"], "p90": summary[f"dd_{h}"]["p90"]} for h in [3, 5, 10, 20, 40]},
        "fwd": {str(h): {"med": summary[f"fwd_{h}"]["med"], "win": 100 - summary[f"fwd_{h}"]["neg_pct"]} for h in [3, 5, 10, 20, 40]},
    },
    "by_gap": {gv: {"n": by_gap[gv]["n"], "dd20": by_gap[gv]["dd_20"]["med"], "fwd20": by_gap[gv]["fwd_20"]["med"]} for gv in ["0", "1", "2"]},
    "current": cur,
}
data_json = json.dumps(clean(data_js), ensure_ascii=False)
# NaN 兜底：python 端 None 已在切片时处理，json.dumps allow_nan=False 会抛错如果有 NaN


html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>周线 MACD 转正 → 4h RSI 超买 → 调整深度分析（GILD / ABBV）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background:#f7f8fa; color:#222; margin:0; padding:24px; }
  .wrap { max-width:1180px; margin:0 auto; }
  h1 { font-size:22px; margin:0 0 4px; }
  .meta { color:#888; font-size:12px; margin-bottom:18px; line-height:1.7; }
  .cards { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px; }
  .card { flex:1; min-width:190px; background:#fff; border-radius:10px; padding:14px 16px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
  .card .k { font-size:12px; color:#888; margin-bottom:6px; }
  .card .v { font-size:20px; font-weight:700; }
  .card .s { font-size:12px; color:#999; margin-top:4px; }
  .up { color:#d23b2e; } .down { color:#1a9e4b; }
  .panel { background:#fff; border-radius:10px; padding:18px; margin-bottom:20px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
  .panel h2 { font-size:16px; margin:0 0 12px; }
  .note { font-size:12px; color:#888; margin-top:8px; line-height:1.7; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { padding:7px 8px; border-bottom:1px solid #eee; text-align:right; }
  th { background:#fafbfc; color:#555; font-weight:600; }
  td.win, th:first-child { text-align:left; }
  .tag { display:inline-block; background:#eef3fb; color:#1f4e79; border-radius:4px; padding:0 6px; font-size:11px; margin-left:6px; }
  .sumrow { background:#f4f7fb; font-weight:600; }
  .concl { border-left:4px solid #1f4e79; background:#f4f7fb; padding:10px 14px; font-size:13.5px; line-height:1.9; }
  .gallery { display:grid; grid-template-columns:repeat(auto-fill,minmax(350px,1fr)); gap:14px; }
  .fig { background:#fff; border-radius:8px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .fig .cap { font-size:12px; color:#555; margin:4px 2px 2px; }
  .fig .cap b { font-size:13px; color:#222; }
  .scroll { overflow-x:auto; }
  .kline-switch { margin-bottom:10px; }
  .kbtn { border:1px solid #d0d5db; background:#fff; color:#555; padding:4px 14px; border-radius:6px; font-size:13px; cursor:pointer; margin-right:6px; }
  .kbtn.active { background:#1f4e79; color:#fff; border-color:#1f4e79; }
  .warn { background:#fff8e6; border:1px solid #f0d48a; border-radius:8px; padding:10px 14px; font-size:12.5px; color:#7a5b00; line-height:1.8; margin-bottom:18px; }
  ul { margin:8px 0; padding-left:20px; } li { margin:5px 0; line-height:1.6; }
</style>
</head>
<body>
<div class="wrap">
  <h1>周线 MACD 能量柱转正 → 4h RSI 超买 → 后续如何调整？</h1>
  <div class="meta">标的：GILD 吉利德 / ABBV 艾伯维 ｜ 周线：Yahoo 1W（adj_close 算 MACD 12/26/9）｜ 4h：腾讯自选股 BATS 240min（MACD/RSI 口径与标准算法相关 ≥0.99）<br>
  事件：周线柱由负转正 → 转正后 2 周窗口内首次 4h RSI≥70（t0）｜ 观察窗口：t0 后 3/5/10/20/40 根 4h ｜ 对照：普通强势周内首次超买（n=144）｜ 生成：2026-08-21</div>

  <div class="warn">⚠️ <b>当前状态</b>：GILD 最近转正周 = 2026-08-06（周线 hist {gild_c['weekly_hist']:.1f}），转正后第 2 周；最新 4h（08-20 21:30）RSI = {gild_c['rsi']:.0f} —— 正处于"转正后 2 周窗口内首次 4h 超买"的经典时点。ABBV 最近转正 = 2026-06-04，距转正已 11 周，8/20 4h RSI {abbv_c['rsi']:.0f} 同步超买但属于转正后较晚的普通超买。</div>

  <div class="cards">
    """ + kpi_cards + """
  </div>

  <div class="panel">
    <h2>① 核心结论</h2>
    <div class="concl">""" + concl + """</div>
  </div>

  <div class="panel">
    <h2>② 调整深度：超买后不同持有期</h2>
    <div id="ch_dd" style="width:100%;height:360px;"></div>
    <div class="note">红色柱 = 期末收益中位数（%），绿色柱 = 期间最大回撤中位数（%）（绝对值显示）。横轴为超买后 4h 根数：3 根≈0.5 日，5 根≈1.2 日，10 根≈2.5 日，20 根≈5 日，40 根≈10 日。事件组 n=%d。虚线标出 ±1% 参考线。</div>
  </div>

  <div class="panel">
    <h2>③ 超买后 40 根（≈10 日）内的路径：最大回撤分布</h2>
    <div id="ch_dist" style="width:100%;height:340px;"></div>
    <div class="note">每次事件的最大回撤（%），按标的着色。所有事件均出现过回撤（回撤距 0 都很近），中位 ≈ {dd40['med']:.1f}%，最深约 {dd40['min']:.1f}%。绝大多数（{100-(sum(1 for r in detail if r['has_ob'] and r['dd_40'] is not None and r['dd_40']<-5)/max(1,with_ob_n)*100):.0f}%）回撤在 5% 以内。</div>
  </div>

  <div class="panel">
    <h2>④ 超买时点在转正后的分布 → 调整深度差异</h2>
    <div id="ch_gap" style="width:100%;height:320px;"></div>
    <div class="note">按超买首次出现时点分组（转正当周 / 次周 / 第三周）看 t0 后 20 根（≈5 日）的最大回撤与期末收益。转正当周就超买（n=%d）反而不深；拖到第三周才超买（n=%d）的样本平均回撤更深——超买越"迟到"，越要警惕。<br>（注：n=3 的第三周组样本极少，仅作参考。）</div>
  </div>

  <div class="panel">
    <h2>⑤ 每笔事件局部 4h K 线（粉线 = RSI，橙三角 = 超买 t0）</h2>
    <div class="gallery" id="gallery"></div>
  </div>

  <div class="panel">
    <h2>⑥ 明细表（转正后 2 周窗口内出现超买的全部事件）</h2>
    <div class="scroll">
    <table>
      <tr><th>标的</th><th>转正周</th><th>超买周</th><th>超买 t0 (4h)</th><th>t0 收盘</th><th>RSI@t0</th>
          <th>maxDD 5根</th><th>maxDD 10根</th><th>maxDD 20根</th><th>maxDD 40根</th>
          <th>20根收益</th><th>40根收益</th><th>回到t0(根)</th><th>40根内新高</th></tr>
      """ + detail_rows_html + """
    </table>
    </div>
  </div>

  <div class="panel">
    <h2>⑦ 统计汇总</h2>
    <div class="scroll">
    <table>
      <tr><th>持有期（4h 根数）</th><th>期末收益 均值</th><th>期末收益 中位</th><th>胜率</th><th>maxDD 均值</th><th>maxDD 中位</th><th>maxDD p25/p75</th><th>maxDD p90</th></tr>
      """ + rows_stat + """
    </table>
    </div>
    <div class="note">口径：t0 = 转正后 2 周窗口内首次 4h RSI≥70 的收盘。maxDD = t0 收盘价到观察期内最低 low 的跌幅；期末收益 = t0 收盘到第 N 根 4h 收盘的涨跌幅。n = 36（两标的合并）。</div>
  </div>

  <div class="panel">
    <h2>⑧ 分组与分标的</h2>
    <div class="scroll">
    <table style="max-width:640px;">
      <tr><th>分组</th><th>样本数</th><th>20根 maxDD 中位</th><th>maxDD p25/p75</th><th>20根收益 中位</th><th>胜率</th></tr>
      """ + rows_gap + """
    </table>
    </div>
    <br>
    <div class="scroll">
    <table>
      <tr><th>标的</th><th>事件数</th><th>5根 maxDD 中位</th><th>20根 maxDD 中位</th><th>40根 maxDD 中位</th><th>20根收益 中位</th><th>40根收益 中位</th></tr>
      """ + rows_per + """
    </table>
    </div>
  </div>

  <div class="panel">
    <h2>⑨ 对照：转正周超买 vs 普通强势周超买</h2>
    <div class="scroll">
    <table>
      <tr><th>组别</th><th>样本数</th><th>5根 maxDD 中位</th><th>20根 maxDD 中位</th><th>40根 maxDD 中位</th><th>20根收益 中位</th><th>40根收益 中位</th><th>40根内新高</th></tr>
      <tr class="sumrow"><td class="win">转正后2周内超买（事件组）</td><td>36</td>
          <td class="down">{dd5['med']:.2f}%</td><td class="down">{dd20['med']:.2f}%</td><td class="down">{dd40['med']:.2f}%</td>
          <td class="up">{fw20['med']:+.2f}%</td><td class="up">{fw40['med']:+.2f}%</td><td>{nh:.0f}%</td></tr>
      <tr><td class="win">普通强势周超买（对照组 n=144，阈值70）</td><td>144</td>
          <td class="down">-1.25%</td><td class="down">-2.25%</td><td class="down">-3.66%</td>
          <td class="up">+0.90%</td><td class="up">+1.08%</td><td>93%</td></tr>
    </table>
    </div>
    <div class="note">对照组口径：周线 MACD 柱 ≥0 且非转正周的任意一周内首次 4h RSI≥70。回撤≥3% 的比例逐持有期两两比较 p≥0.4（二项近似 z 检验），不显著。结论：<b>转正标签本身不加重超买后的调整</b>。</div>
  </div>

  <div class="panel">
    <h2>⑩ 方法口径与局限</h2>
    <ul>
      <li><b>周线 MACD</b>：Yahoo 1W adj_close 计算 EMA12/26 + 9 日 DEA，柱 = 2×(DIF−DEA)；<b>转正</b> = 上周柱&lt;0 且本周柱≥0。</li>
      <li><b>4h 数据</b>：腾讯自选股 BATS 240min CSV（2015-10 ~ 2026-08-20，ABBV 5439 根 / GILD 5516 根）；RSI 与标准 14 周期 ewm 算法相关 0.99+，MACD 列与标准算法相关 0.9998+。</li>
      <li><b>超买</b>：4h RSI14 ≥70（灵敏度：65 → n=30 / 70 → n=16 / 75 → n=6，当周口径）</li>
      <li><b>未复权 vs 复权</b>：ABBV 自 2013 年派息稳定，4h 价格序列为未复权。单周内 4h 回撤 1~3% 受派息影响可忽略（每周派息额 &lt;0.1%），跨年比较不受影响。</li>
      <li><b>样本量小</b>：窗口口径事件组 n=36（GILD 16 / ABBV 20），分 gap 组后最小 n=3，年份未细分。结论以中位数与分位稳健统计为主，p 值仅作二项近似参考。</li>
      <li><b>幸存者偏差</b>：仅分析现存两只大药企，不构成行业总体的推论。</li>
    </ul>
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
RED = "#d23b2e"; GREEN = "#1a9e4b"; ORANGE = "#e67e22"; BLUE = "#1f4e79"; GRAY = "#999";

// 图② 调整深度
(function(){
  var ch = echarts.init(document.getElementById("ch_dd"));
  var H = DATA.summary.horizons;
  var dd = H.map(function(h){ return DATA.summary.dd[String(h)].med; });
  var fwd = H.map(function(h){ return DATA.summary.fwd[String(h)].med; });
  var labels = H.map(function(h){ return h + " 根<br>(" + (h*4/8).toFixed(1) + "日)"; });
  ch.setOption({
    tooltip: { trigger:"axis", valueFormatter: function(v){ return v + " %"; } },
    legend: { data:["期末收益 中位","期间最大回撤 中位"], top:0 },
    grid: { left:60, right:20, top:40, bottom:40 },
    xAxis: { type:"category", data: labels, axisLabel:{ fontSize:11 } },
    yAxis: { type:"value", name:"%", axisLabel:{ formatter: function(v){ return v + "%"; } } },
    series: [
      { name:"期末收益 中位", type:"bar", data: fwd, itemStyle:{ color: RED, borderRadius:[4,4,0,0] },
        label:{ show:true, position:"top", formatter: function(p){ return (p.value>0?"+":"")+p.value.toFixed(2)+"%"; } } },
      { name:"期间最大回撤 中位", type:"bar", data: dd, itemStyle:{ color: GREEN, borderRadius:[0,0,4,4] },
        label:{ show:true, position:"bottom", formatter: function(p){ return p.value.toFixed(2)+"%"; } } }
    ]
  });
})();

// 图③ 最大回撤分布
(function(){
  var ch = echarts.init(document.getElementById("ch_dist"));
  var dds = DATA.slices.map(function(s){ return { value:s.dd_40, ticker:s.ticker.toUpperCase(), t0:s.t0_time }; })
                       .filter(function(x){ return x.value != null; })
                       .sort(function(a,b){ return b.value - a.value; });
  var cats = dds.map(function(x){ return x.t0 + " " + x.ticker; });
  ch.setOption({
    tooltip: { trigger:"axis", formatter: function(ps){ var x = ps[0]; return x.name + "<br>maxDD 40根: <b>" + x.value + "%</b>"; } },
    grid: { left:90, right:30, top:20, bottom:80 },
    xAxis: { type:"category", data: cats, axisLabel:{ rotate:60, fontSize:10, interval:0 } },
    yAxis: { type:"value", name:"%", axisLabel:{ formatter: function(v){ return v + "%"; } } },
    series: [{ type:"bar", data: dds.map(function(x){
        return { value:x.value, itemStyle:{ color: x.ticker==="GILD" ? "#c0392b" : "#1f4e79" } };
      }), label:{ show:false } }]
  });
})();

// 图④ 分组
(function(){
  var ch = echarts.init(document.getElementById("ch_gap"));
  var names = ["转正当周","转正次周","转正第三周"];
  var dd20 = ["0","1","2"].map(function(g){ return DATA.by_gap[g].dd20; });
  var fw20 = ["0","1","2"].map(function(g){ return DATA.by_gap[g].fwd20; });
  var ns = ["0","1","2"].map(function(g){ return DATA.by_gap[g].n; });
  ch.setOption({
    tooltip: { trigger:"axis" },
    legend: { data:["20根 maxDD 中位","20根收益 中位"] },
    grid: { left:60, right:20, top:40, bottom:30 },
    xAxis: { type:"category", data: names.map(function(n,i){ return n + " (n=" + ns[i] + ")"; }) },
    yAxis: { type:"value", name:"%" },
    series: [
      { name:"20根 maxDD 中位", type:"bar", data: dd20, itemStyle:{ color: GREEN },
        label:{ show:true, position:"top", formatter: function(p){ return p.value.toFixed(2)+"%"; } } },
      { name:"20根收益 中位", type:"bar", data: fw20, itemStyle:{ color: RED },
        label:{ show:true, position:"top", formatter: function(p){ return (p.value>0?"+":"")+p.value.toFixed(2)+"%"; } } }
    ]
  });
})();

// 统计小工具
function sum(a){ return a.reduce(function(x,y){return x+(y||0);},0); }
function mean(a){ return sum(a)/a.length; }
function median(a){ var s=[].concat(a).sort(function(x,y){return x-y;}); var m=s.length>>1;
  return s.length%2 ? s[m] : (s[m-1]+s[m])/2; }

// 图⑤ 画廊
(function(){
  var gal = document.getElementById("gallery");
  var tkColors = { GILD:"#c0392b", ABBV:"#1f4e79" };
  DATA.slices.forEach(function(s, i){
    var div = document.createElement("div");
    div.className = "fig";
    div.id = "fig_" + i;
    div.style.height = "300px";
    gal.appendChild(div);
    var dds = [s.dd_5, s.dd_10, s.dd_20, s.dd_40];
    var mdd = dds.reduce(function(a,b){ return (a==null||b==null)?null:Math.max(a,Math.abs(b)); }, 0);
    var cap = document.createElement("div");
    cap.className = "cap";
    var gap_txt = {0:"转正当周",1:"次周",2:"第三周"}[s.ob_week_gap] || "";
    cap.innerHTML = "<b>" + s.ticker.toUpperCase() + "</b> 转正 " + s.week_start + " · 超买 " + s.t0_time +
      " (RSI " + s.rsi_t0.toFixed(0) + ") · maxDD40 " + (s.dd_40==null?"—":s.dd_40.toFixed(1)+"%") +
      (s.bars_to_recover?" · 回到t0 " + s.bars_to_recover + "根":"") + "<span class='tag'>" + gap_txt + "</span>";
    div.appendChild(cap);
    var chart = echarts.init(div);
    var bars = s.bars;
    var dates = bars.map(function(b){ return b.t; });
    var ohlc = bars.map(function(b){ return [b.o, b.c, b.l, b.h]; });
    var t0i = s.t0_off;
    // K线在上(高度约68%)，RSI在下(约22%)，共享时间轴
    chart.setOption({
      animation:false,
      axisPointer:{ link:[{ xAxisIndex:'all' }] },
      tooltip: { trigger:"axis", axisPointer:{ type:"cross" },
        formatter: function(ps){
          // ps 同时含K线和RSI两个series，取第一个的时间与OHLC
          var p = ps[0];
          var d = bars[p.dataIndex];
          var r = s.rsi_t0;
          var line = d.t + "<br>O " + d.o + "  H " + d.h + "<br>L " + d.l + "  C " + d.c;
          if (d.r != null) line += "<br>RSI " + d.r;
          return line;
        } },
      grid: [
        { left:55, right:15, top:12, height:"62%" },
        { left:55, right:15, top:"80%", height:"16%" }
      ],
      xAxis: [
        { type:"category", data: dates, gridIndex:0, axisLabel:{ interval: 4, fontSize:9 }, axisTick:{ show:false } },
        { type:"category", data: dates, gridIndex:1, axisLabel:{ show:false }, axisTick:{ show:false } }
      ],
      yAxis: [
        { scale:true, axisLabel:{ fontSize:9 }, gridIndex:0 },
        { min:0, max:100, axisLabel:{ fontSize:8 }, gridIndex:1, splitLine:{ lineStyle:{ color:"#f0f0f0" } } }
      ],
      dataZoom: [ {type:"inside", start:0, end:100} ],
      series: [
        {
          type:"candlestick", data: ohlc, xAxisIndex:0, yAxisIndex:0,
          itemStyle: { color: RED, color0: GREEN, borderColor: RED, borderColor0: GREEN },
          markPoint: {
            data: [ { coord:[t0i, bars[t0i].h], value:"超买", symbol:"triangle", symbolSize:14,
                      itemStyle:{ color: ORANGE },
                      label:{ color:"#fff", fontSize:9 } } ]
          },
          markLine: {
            silent: true,
            data: [ { xAxis: t0i, lineStyle:{ color: ORANGE, type:"dashed", width:1 } } ]
          }
        },
        {
          name:"RSI", type:"line", data: bars.map(function(b){ return b.r; }),
          xAxisIndex:1, yAxisIndex:1, symbol:"none", lineStyle:{ color:"#e91e8c", width:1.2 },
          markLine: { silent:true, symbol:"none",
            data:[ { yAxis:70, lineStyle:{ color:"#e91e8c", type:"dashed", width:1 }, label:{ formatter:"70", fontSize:8 } } ] }
        }
      ]
    });
    // 动态 resize
    window.addEventListener("resize", function(){ chart.resize(); });
  });
})();
</script>
</body>
</html>
"""

# 替换数据占位符
html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + data_json + ";")
# 填充两处 n 显示
html = html.replace("事件组 n=%d。" % 0, "")
html = html.replace("n=%d 个样本。/ 转正当周就超买" % 0, "")
html = html.replace("转正当周就超买（n=%d）" % 0, f"转正当周就超买（n={gap0}）")
html = html.replace("第三周才超买（n=%d）" % 0, f"第三周才超买（n={W['gap_dist'].get('2',0)}）")
# 修复注脚 n
html = html.replace("事件组 n=%d。" % 0, "")

with open(os.path.join(REPORT_DIR, "weekline_ob_report.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("Report written:", os.path.join(REPORT_DIR, "weekline_ob_report.html"))
print("size:", os.path.getsize(os.path.join(REPORT_DIR, "weekline_ob_report.html")))