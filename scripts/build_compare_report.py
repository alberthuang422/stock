# -*- coding: utf-8 -*-
"""多股票严格口径回测对比报告 v2：含实盘化买入收益（入场点脱节检验）"""
import pandas as pd
import numpy as np
import json

BASE = "/Users/alberthuang/Desktop/股票分析"
res = json.load(open(f"{BASE}/results/all_stocks_backtest.json", encoding="utf-8"))
res = sorted(res, key=lambda r: r["ticker"])

tot_merged = sum(r["gold_merged"] for r in res)
tot_not = sum(r["not_stand_groups"] for r in res)
tot_h5 = sum(r["hold5"] for r in res)
tot_h3 = sum(r["hold3_base"] for r in res)
tot_hit = sum(r["buy_hit"] for r in res)
tot_miss = sum(r["buy_miss"] for r in res)

rows = []
for r in res:
    lift = r["h5_T5_win"] - r["all_T5_win"] if "all_T5_win" in r else None
    if lift is None:
        lift = r["h5_T5_win"]
    rows.append(
        f"<tr><td><b>{r['ticker'].upper()}</b></td>"
        f"<td>{r['start']}~{r['end']}</td><td>{r['days']}</td>"
        f"<td>{r['gold_merged']}</td><td>{r['not_stand_groups']}</td>"
        f"<td>{r['not_stand_groups']/r['gold_merged']*100:.0f}%</td>"
        f"<td>{r['hold5']}</td><td>{r['hold3_base']}</td>"
        f"<td>{r['buy_hit']} / {r['buy_miss']}</td><td>{r['buy_hit_rate']:.0f}%</td>"
        f"<td class='up'>{r['h5_T5_win']:.1f}%</td>"
        f"<td>{r['hit_orig_T5_win']:.1f}%</td>"
        f"<td class='{'up' if r['buy_T5_win'] >= 50 else 'dn'}'>{r['buy_T5_win']:.1f}%</td>"
        f"<td class='{'up' if r['buy_T5_avg'] > 0 else 'dn'}'>{r['buy_T5_avg']:+.2f}%</td>"
        f"<td>{r['h5_T20_win']:.1f}%</td></tr>")

tickers = [r["ticker"].upper() for r in res]
h5_win = [r["h5_T5_win"] for r in res]
orig_win = [r["hit_orig_T5_win"] for r in res]
buy_win = [r["buy_T5_win"] for r in res]

data = {"tickers": tickers, "h5_win": h5_win, "orig_win": orig_win, "buy_win": buy_win}

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>多股票 MACD 水下金叉回测对比（严格口径 + 实盘化买入收益）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#d97706;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1200px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:21px;font-weight:700;}
  .kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;white-space:nowrap;text-align:right;}
  td:first-child,td:nth-child(2){text-align:left;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .chart.sm{height:380px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .conc{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:14px 18px;font-size:13px;color:#17442f;margin-top:10px;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>MACD 水下金叉 · 站上 EMA10/20 · 站稳5天 —— 10 只股票统一回测（严格口径 + 买入收益）</h1>
    <div class="meta">标的：AMZN/BRK.B/GE/GS/IBKR/JNJ/MS/NVDA/SPY/UNH（BATS 日线，用户提供 CSV）｜严格口径：水下金叉→3日内收盘同时站上 EMA10/20（上穿）→站稳5天为「完全符合」标签｜<b>买入规则：站稳3天即可考虑买入（hold3母集），买点=（金叉前10日盘整最高价+确认日EMA20）/2，回踩到买点才成交，30日内未回踩=错过</b>｜收益不含成本</div>
    <div class="kpis">
      <div class="kpi"><div class="num">__TOT_MERGED__</div><div class="lab">合并后水下金叉（10日窗口）</div></div>
      <div class="kpi"><div class="num dn">__TOT_NOT__</div><div class="lab">未能站上均线（__TOT_NOT_PCT__）</div></div>
      <div class="kpi"><div class="num up">__TOT_H5__</div><div class="lab">hold5 完全符合信号（严格标签）</div></div>
      <div class="kpi"><div class="num">__TOT_H3__</div><div class="lab">hold3 母集（站稳3天即可考虑买入）</div></div>
      <div class="kpi"><div class="num">__TOT_HIT__</div><div class="lab">实际回踩成交（错过 __TOT_MISS__，成交率 __TOT_RATE__）</div></div>
    </div>
  </div>

  <div class="card">
    <h2>一、各股票回测总览（严格口径 + 买入）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>股票</th><th>数据区间</th><th>交易日</th><th>合并金叉</th><th>未站上</th><th>占比</th><th>hold5(完全符合)</th><th>hold3母集</th><th>成交/错过</th><th>成交率</th><th>hold5 T+5胜率</th><th>金叉日买入T+5(同批)</th><th>回踩买入T+5胜率</th><th>回踩买入T+5均值</th><th>hold5 T+20</th></tr></thead>
      <tbody>__ROWS__</tbody>
    </table>
    </div>
    <div class="note">「金叉日买入T+5(同批)」与「回踩买入T+5」统计的是<b>同一批实际成交的信号</b>，可直接对比：两者差距即入场点脱节造成的收益损耗。</div>
  </div>

  <div class="card">
    <h2>二、入场点脱节检验：金叉日买入 vs 回踩买点买入（T+5 胜率，%）</h2>
    <div id="chart1" class="chart"></div>
    <div class="note">蓝色=该批信号若在金叉日收盘即买入的胜率；橙色=等到站稳确认后回踩到买点再买入的胜率。<b>10 只股票中 9 只回踩买入胜率显著低于金叉日买入</b>（BRK.B 持平），入场点脱节问题普遍存在。</div>
  </div>

  <div class="card">
    <h2>三、结论：IBKR 结论适用性 + 买入收益修正</h2>
    <div class="conc">
      <b>① 信号规律跨股票成立（不变）：</b>10/10 只股票上「水下金叉+站上+站稳5天」筛选后的 T+5 胜率均大幅高于基线（76.7%~100%）。<br>
      <b>② 但实盘化买入后收益显著缩水（新结论）：</b>站稳3天确认、回踩买点再入场（成交率 69%~100%），T+5 胜率普遍降至 27%~62%（均值 −1.8%~+0.8%），仍显著低于同批金叉日买入（55%~79%）。「入场点与收益计算脱节」在几乎所有股票上验证成立。<br>
      <b>③ 被错过的信号不可交易：</b>成交率 69%~100%，错过的信号恰恰是金叉后强势不回踩的（其金叉日收益最好但实盘买不到）。<br>
      <b>④ 修正后的结论：</b>站稳3天确认比5天确认更好（成交率与 T+20 收益均有改善），但 T+5 期望收益仍接近零；该信号更适用于「金叉当天/次日快进快出」或<b>趋势启动预警</b>，坚持回踩买入需叠加其他过滤（如回踩不破EMA20、量能收缩）。<br>
      <b>⑤ 注意：</b>多数股票数据自 2016/2018 年起，成交样本 7~25 个，统计显著性有限；未计成本。
    </div>
    <div class="dis">数据来源：用户提供本地 CSV（BATS 日线）；指标口径经递推验证。基于历史数据回测，仅供研究参考。<br><br><b>免责声明：</b>以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>
<script>
const D = __DATA_JSON__;
const RED='#e03131', GREEN='#0aa06e', BLUE='#1e66d6', AMBER='#d97706';

echarts.init(document.getElementById('chart1')).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
  legend:{data:['金叉日买入·T+5胜率','回踩买点买入·T+5胜率']},
  grid:{left:48,right:20,top:40,bottom:50},
  xAxis:{type:'category',data:D.tickers},
  yAxis:{type:'value',min:0,max:110,axisLabel:{formatter:'{value}%'}},
  series:[
    {name:'金叉日买入·T+5胜率',type:'bar',data:D.orig_win,itemStyle:{color:BLUE},barGap:'20%'},
    {name:'回踩买点买入·T+5胜率',type:'bar',data:D.buy_win,itemStyle:{color:AMBER}}
  ]
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))
html = html.replace("__ROWS__", "\n".join(rows))
html = html.replace("__TOT_MERGED__", str(tot_merged))
html = html.replace("__TOT_NOT__", str(tot_not))
html = html.replace("__TOT_NOT_PCT__", f"{tot_not/tot_merged*100:.0f}%")
html = html.replace("__TOT_H5__", str(tot_h5))
html = html.replace("__TOT_H3__", str(tot_h3))
html = html.replace("__TOT_RATE__", f"{tot_hit/tot_h3*100:.0f}%")
html = html.replace("__TOT_HIT__", str(tot_hit))
html = html.replace("__TOT_MISS__", str(tot_miss))
out = f"{BASE}/reports/多股票回测对比报告.html"
open(out, "w", encoding="utf-8").write(html)
print("已生成:", out)
print(f"合计 hold5={tot_h5} 成交={tot_hit} 错过={tot_miss} 成交率={tot_hit/tot_h5*100:.0f}%")
