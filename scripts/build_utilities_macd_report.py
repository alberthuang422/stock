# -*- coding: utf-8 -*-
"""公用事业 ETF + 成分股 MACD 水下金叉回测综合报告
输入: results/utilities_macd_backtest.json
输出: reports/18_公用事业MACD水下金叉回测/公用事业MACD水下金叉回测报告.html
结构: KPI → 分组总览(ETF/IPP/受管制) → 各股票逐层收益 → 入场点脱节检验 → 节点明细 → 结论
"""
import json

BASE = r"C:\Users\Administrator\Desktop\stock"
D = json.load(open(f"{BASE}/results/utilities_macd_backtest.json", encoding="utf-8"))
TICKERS = D["tickers"]
NODES = D["nodes"]
GROUPS = D["meta"]["groups"]
GROUP_NAMES = {"ETF": "ETF（公用事业指数）", "IPP": "IPP 独立发电商", "受管制": "受管制公用事业"}
TICKER_NAMES = {
    "XLU": "SPDR 公用事业 ETF", "UTES": "Virtus 公用事业 ETF",
    "VST": "Vistra", "CEG": "Constellation Energy", "TLN": "Talen Energy", "NRG": "NRG Energy",
    "NEE": "NextEra", "SRE": "Sempra", "XEL": "Xcel Energy", "CNP": "CenterPoint",
    "ETR": "Entergy", "LNT": "Alliant Energy",
}

# ---------- 汇总 ----------
tot_merged = sum(r["gold_merged"] for r in TICKERS)
tot_not = sum(r["not_stand_groups"] for r in TICKERS)
tot_h5 = sum(r["hold5"] for r in TICKERS)
tot_h3 = sum(r["hold3_base"] for r in TICKERS)
tot_hit = sum(r["buy_hit"] for r in TICKERS)
tot_miss = sum(r["buy_miss"] for r in TICKERS)
tot_rate = tot_hit / tot_h3 * 100

# ---------- 分组统计 ----------
group_rows = {}
group_charts = {}
for g in GROUPS:
    rs = [r for r in TICKERS if r["group"] == g]
    n_h5 = sum(r["hold5"] for r in rs)
    n_hit = sum(r["buy_hit"] for r in rs)
    # 聚合 h5 T+5 / 回踩T+5（逐信号合并）
    h5_r5, buy_r5 = [], []
    ticks = {r["ticker"] for r in rs}
    for nd in NODES:
        if nd["t"] in ticks:
            if nd["h5"] and nd["r5"] is not None:
                h5_r5.append(nd["r5"])
            if nd["bs"] == "hit" and nd["br5"] is not None:
                buy_r5.append(nd["br5"])
    gw = sum(1 for x in h5_r5 if x > 0) / len(h5_r5) * 100 if h5_r5 else None
    ga = sum(h5_r5) / len(h5_r5) if h5_r5 else None
    bw = sum(1 for x in buy_r5 if x > 0) / len(buy_r5) * 100 if buy_r5 else None
    ba = sum(buy_r5) / len(buy_r5) if buy_r5 else None
    # 更准确的加权（按信号等权 vs 按股票等权——用逐个信号聚合）
    group_rows[g] = {
        "n_stocks": len(rs), "n_h5": n_h5, "n_hit": n_hit,
        "h5_win": round(gw, 1) if gw is not None else None,
        "h5_avg": round(ga, 2) if ga is not None else None,
        "buy_win": round(bw, 1) if bw is not None else None,
        "buy_avg": round(ba, 2) if ba is not None else None,
        "n_sig": len(h5_r5), "n_buy": len(buy_r5),
    }
    group_charts[g] = {"tickers": [r["ticker"] for r in rs],
                       "orig": [r["orig_T5"]["win"] for r in rs],
                       "buy": [r["buy_T5"]["win"] for r in rs],
                       "h5": [r["h5_T5"]["win"] for r in rs]}

# ---------- 表格行 ----------
rows = []
for r in TICKERS:
    tk = r["ticker"]
    lift = r["h5_T5"]["win"] - r["base_T5"]["win"]
    rows.append(
        f"<tr><td><b>{tk}</b></td><td>{GROUP_NAMES[r['group']]}</td>"
        f"<td>{r['start']}~{r['end']}</td><td>{r['days']}</td>"
        f"<td>{r['gold_merged']}</td><td>{r['not_stand_groups']}</td>"
        f"<td>{r['not_stand_groups']/r['gold_merged']*100:.0f}%</td>"
        f"<td>{r['hold5']}</td><td>{r['hold3_base']}</td>"
        f"<td>{r['buy_hit']} / {r['buy_miss']}</td><td>{r['buy_hit_rate']:.0f}%</td>"
        f"<td>{r['base_T5']['win']:.1f}%</td>"
        f"<td class='up'>{r['h5_T5']['win']:.1f}%（{r['h5_T5']['avg']:+.2f}%）</td>"
        f"<td class='{'up' if r['h5_T10']['win']>=70 else 'dn'}'>{r['h5_T10']['win']:.1f}%（{r['h5_T10']['avg']:+.2f}%）</td>"
        f"<td>{r['h5_T20']['win']:.1f}%（{r['h5_T20']['avg']:+.2f}%）</td>"
        f"<td>{r['orig_T5']['win']:.1f}%</td>"
        f"<td class='{'up' if r['buy_T5']['avg']>0 else 'dn'}'>{r['buy_T5']['win']:.1f}%（{r['buy_T5']['avg']:+.2f}%）</td>"
        f"<td class='{'up' if r['buy_T20']['avg']>0 else 'dn'}'>{r['buy_T20']['win']:.1f}%（{r['buy_T20']['avg']:+.2f}%）</td></tr>")

# ---------- 节点明细表格行（仅 hold3 母集有买入信息，全部展示） ----------
node_rows = []
for nd in sorted(NODES, key=lambda x: (x["t"], x["d"])):
    tk = nd["t"]
    h5 = "✓" if nd["h5"] else ("—" if nd["h5"] is None else "✗")
    h3 = "✓" if nd["h3"] else ("—" if nd["h3"] is None else "✗")
    fmt_r = lambda v: f"{v:+.2f}%" if isinstance(v, (int, float)) else "—"
    hit_cls = ""
    if nd["bs"] == "hit":
        hit_cls = " class='hit'"
    bs = {"hit": "成交", "miss": "错过", None: "—"}.get(nd["bs"], "—")
    br5 = fmt_r(nd["br5"]); br10 = fmt_r(nd["br10"]); br20 = fmt_r(nd["br20"])
    cls = lambda v, base="": (f" class='up'" if isinstance(v, (int, float)) and v > 0
                              else (f" class='dn'" if isinstance(v, (int, float)) and v < 0 else ""))
    node_rows.append(
        f"<tr{hit_cls}><td><b>{tk}</b></td><td>{nd['d']}</td><td>{h3}</td><td>{h5}</td>"
        f"<td{cls(nd['r5'])}>{fmt_r(nd['r5'])}</td><td{cls(nd['r10'])}>{fmt_r(nd['r10'])}</td>"
        f"<td{cls(nd['r20'])}>{fmt_r(nd['r20'])}</td>"
        f"<td>{bs}</td><td{cls(nd['br5'])}>{br5}</td><td{cls(nd['br10'])}>{br10}</td>"
        f"<td{cls(nd['br20'])}>{br20}</td></tr>")

# ---------- 入场点脱节：每股 orig vs buy ----------
chart1_data = {"tickers": [r["ticker"] for r in TICKERS],
               "orig": [r["orig_T5"]["win"] for r in TICKERS],
               "buy": [r["buy_T5"]["win"] for r in TICKERS]}
chart2_data = group_charts

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公用事业 ETF + 成分股 MACD 水下金叉回测（严格口径 + 实盘化买入收益）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#d97706;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1240px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:21px;font-weight:700;}
  .kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .flow{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:10px 0 4px;font-size:13px;}
  .fstep{background:#eef3fb;color:var(--blue);border:1px solid #d5e2f7;border-radius:6px;padding:2px 8px;font-weight:600;}
  .farrow{color:var(--sub);}
  .fstat{color:var(--sub);font-size:12px;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;white-space:nowrap;text-align:right;}
  td:first-child,td:nth-child(2){text-align:left;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  tr.hit td{background:#eefaf5;}
  tr.hit td:first-child{border-left:3px solid var(--green);}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .chart.sm{height:330px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .conc{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:14px 18px;font-size:13px;color:#17442f;margin-top:10px;}
  .warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);}
  .badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .b-ETF{background:#e8f0fe;color:#1a56db;} .b-IPP{background:#fdecea;color:#c92a2a;} .b-受管制{background:#e6f4ea;color:#1a7f37;}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>公用事业板块 MACD 水下金叉回测 —— ETF（XLU/UTES）× 主要成分股（IPP + 受管制）</h1>
    <div class="meta">标的：XLU/UTES（板块 ETF）· VST/CEG/TLN/NRG（IPP 独立发电）· NEE/SRE/XEL/CNP/ETR/LNT（受管制公用事业）｜数据：Yahoo 日线 adj_close（复权口径，指标与收益均基于复权价）｜严格口径：水下金叉 → ≤3 日收盘同时站上 EMA10/20（无容差）→ 站稳 3/4/5 天（允许 1 日跌破次日收复）｜<b>买入规则：站稳3天即可考虑买入（hold3母集），买点=（金叉前10日盘整最高价+确认日EMA20）/2，回踩到买点才成交，30日内未回踩=错过</b>｜收益不含成本</div>
    <div class="flow">
      <span class="fstep">① 水下金叉</span><span class="farrow">→</span>
      <span class="fstep">② x≤3天站上 EMA10/20</span><span class="farrow">→</span>
      <span class="fstep">③ 站稳3天确认</span><span class="farrow">→</span>
      <span class="fstep">④ 回踩买点买入</span>
      <span class="fstat">　合并金叉 __TOT_MERGED__ → 未站上 __TOT_NOT__（__TOT_NOT_PCT__）→ hold3母集 __TOT_H3__（hold5=__TOT_H5__）→ 成交 __TOT_HIT__（错过 __TOT_MISS__，成交率 __TOT_RATE__）</span>
    </div>
    <div class="kpis">
      <div class="kpi"><div class="num up">__H5_T5_WIN__</div><div class="lab">hold5 完全符合信号 T+5 平均胜率（金叉日口径）</div></div>
      <div class="kpi"><div class="num up">__H5_T10_WIN__</div><div class="lab">hold5 信号 T+10 平均胜率</div></div>
      <div class="kpi"><div class="num dn">__BUY_T5_WIN__</div><div class="lab">回踩买点买入 T+5 平均胜率（同批信号）</div></div>
      <div class="kpi"><div class="num dn">__BUY_T5_AVG__</div><div class="lab">回踩买入 T+5 平均均值（%）</div></div>
      <div class="kpi"><div class="num">__TOT_RATE__</div><div class="lab">hold3 母集实际可成交比例（__TOT_MISS__ 错过）</div></div>
    </div>
  </div>

  <div class="card">
    <h2>一、分组总览：ETF vs IPP vs 受管制（hold5 确认后 T+5，金叉日口径）</h2>
    <div class="scroll"><table>
      <thead><tr><th>分组</th><th>股票数</th><th>hold5 信号</th><th>hold5 T+5 胜率</th><th>hold5 T+5 均值</th><th>成交信号</th><th>回踩买 T+5 胜率</th><th>回踩买 T+5 均值</th></tr></thead>
      <tbody>__GROUP_ROWS__</tbody>
    </table></div>
    <div id="chart2" class="chart sm"></div>
    <div class="note">图例：hold5 组（金叉日口径）vs 同批信号的回踩买点买入 T+5 胜率。虚线标注 50%。分组内部按股票展开。</div>
  </div>

  <div class="card">
    <h2>二、各标的回测总览（严格口径 + 买入）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>标的</th><th>分组</th><th>数据区间</th><th>交易日</th><th>合并金叉</th><th>未站上</th><th>占比</th><th>hold5(完全符合)</th><th>hold3母集</th><th>成交/错过</th><th>成交率</th><th>基线T+5</th><th>hold5 T+5（胜率/均值）</th><th>hold5 T+10（胜率/均值）</th><th>hold5 T+20（胜率/均值）</th><th>金叉日买T+5(同批)</th><th>回踩买入T+5（胜率/均值）</th><th>回踩买入T+20（胜率/均值）</th></tr></thead>
      <tbody>__ROWS__</tbody>
    </table>
    </div>
    <div class="note">「基线 T+5」=全历史任意日买入持有5日的胜率（对照）。「金叉日买入(同批)」与「回踩买入」统计同一批实际成交信号，可直接对比入场点脱节损耗。红涨绿跌（中国口径）。</div>
  </div>

  <div class="card">
    <h2>三、入场点脱节检验：金叉日买入 vs 回踩买点买入（T+5 胜率，%）</h2>
    <div id="chart1" class="chart"></div>
    <div class="note">蓝=该批信号若在金叉日收盘买入的胜率；橙=站稳确认后回踩到买点再买入的胜率。<b>观察：回踩买入胜率系统性低于金叉日买入（尤其 IPP 高波动标的），但受管制类部分标的表现更好</b>——板块内不同子类入场点损耗并不一致。</div>
  </div>

  <div class="card">
    <h2>四、全部站上信号节点明细（343 个 · 含买入信息）</h2>
    <div class="note">绿色高亮行 = 回踩成交；混排 hold5 ✓/✗ 与买入信息。T+5/10/20 为金叉日复权收益；买入 T+5/10/20 为买点成交后收益（%）。</div>
    <div class="scroll" style="margin-top:10px;max-height:560px;overflow-y:auto;">
    <table>
      <thead><tr><th>标的</th><th>金叉日</th><th>站稳3</th><th>hold5</th><th>T+5%</th><th>T+10%</th><th>T+20%</th><th>买入状态</th><th>买入T+5%</th><th>买入T+10%</th><th>买入T+20%</th></tr></thead>
      <tbody>__NODE_ROWS__</tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>五、结论：公用事业板块水下 MACD 信号的适用性</h2>
    <div class="conc" id="conclusion">
      <b>① 信号规律在公用事业板块同样成立：</b>12 只标的 hold5 确认后 T+5 胜率 70%～100%（均值普遍 +1.5%～+4.3%），远高于各自基线（56%～66%）。<br>
      <b>② 子类差异明显：</b>【受管制公用事业】hold5 T+5 胜率偏高（81%～100%）、回踩买入 T+5 均值多为正（NEE +2.82%、LNT +0.74%），入场点脱节损耗最小 —— 低波动、均值回归型，回踩策略可用；【IPP】hold5 T+5 均值最高（VST +2.95%、TLN +4.31%、CEG +4.28%），但回踩买入缩水最严重（VST 37.5%/−1.82%、CEG 40%/+3.33%），高波动导致强信号不回踩或回踩即破位 —— 更适合金叉当天/次日快进快出。<br>
      <b>③ ETF 与成分股一致：</b>XLU/UTES hold5 T+5 胜率 86%/86%，板块 ETF 同样适用该信号。<br>
      <b>④ 买入视角的修正：</b>与 01 回测结论一致 —— 「确认后回踩买点」策略整体不优于金叉日买入（12 只中多数回踩胜率低于金叉日胜率），受管制类接近持平甚至反超（XEL 80% vs 60%、LNT 62% vs 71%），IPP 类显著跑输。<br>
      <b>⑤ 局限：</b>hold5 样本每标的 6~26 个，IPP 尤其少（VST 10、TLN 6）；未计成本；收益口径为复权价；分组内股票数量不等（受管制 6 只、IPP 4 只）。
    </div>
    <div class="dis">数据来源：Yahoo Finance 日线（本地存储，复权 adj_close）；MACD(12,26,9) + EMA10/20 自算。基于历史数据回测，仅供研究参考。<br><br><b>免责声明：</b>以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>
<script>
const D = __DATA_JSON__;
const RED='#e03131', GREEN='#0aa06e', BLUE='#1e66d6', AMBER='#d97706';

echarts.init(document.getElementById('chart1')).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
  legend:{data:['金叉日买入·T+5胜率','回踩买点买入·T+5胜率']},
  grid:{left:50,right:20,top:40,bottom:50},
  xAxis:{type:'category',data:D.all.tickers,axisLabel:{rotate:30}},
  yAxis:{type:'value',min:0,max:110,axisLabel:{formatter:'{value}%'}},
  series:[
    {name:'金叉日买入·T+5胜率',type:'bar',data:D.all.orig,itemStyle:{color:BLUE},barGap:'20%'},
    {name:'回踩买点买入·T+5胜率',type:'bar',data:D.all.buy,itemStyle:{color:AMBER}}
  ]
});

const gd = document.getElementById('chart2');
if (gd) echarts.init(gd).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
  legend:{data:['hold5 T+5胜率','回踩买入 T+5胜率']},
  grid:{left:50,right:20,top:40,bottom:50},
  xAxis:{type:'category',data:D.groups.tickers,axisLabel:{rotate:30}},
  yAxis:{type:'value',min:0,max:100,splitLine:{lineStyle:{type:'dashed'}}},
  series:[
    {name:'hold5 T+5胜率',type:'bar',data:D.groups.h5,itemStyle:{color:BLUE},barGap:'30%'},
    {name:'回踩买入 T+5胜率',type:'bar',data:D.groups.buy,itemStyle:{color:AMBER}}
  ]
});
</script>
</body>
</html>
"""

# ---------- 填充 ----------
group_rows_h = ""
for g in GROUPS:
    gr = group_rows[g]
    n_sig = gr["n_sig"]; n_buy = gr["n_buy"]
    group_rows_h += (
        f"<tr><td><b><span class='badge b-{g}'>{GROUP_NAMES[g]}</span></b></td>"
        f"<td>{gr['n_stocks']}</td><td>{gr['n_h5']}（{n_sig}信号）</td>"
        f"<td class='up'>{gr['h5_win']:.1f}%</td><td>{gr['h5_avg']:+.2f}%</td>"
        f"<td>{gr['n_hit']}</td>"
        f"<td class='{'up' if gr['buy_win']>=50 else 'dn'}'>{gr['buy_win']:.1f}%</td>"
        f"<td class='{'up' if gr['buy_avg']>0 else 'dn'}'>{gr['buy_avg']:+.2f}%</td></tr>")

# 分组图表聚合 tickers（按组拼接）
group_tk, group_h5, group_buy, group_orig2 = [], [], [], []
for g in GROUPS:
    d = group_charts[g]
    group_tk += d["tickers"]
    group_h5 += d["h5"]
    group_buy += d["buy"]

r_by_tk = {r["ticker"]: r for r in TICKERS}
avg_h5w = sum(r["h5_T5"]["win"] for r in TICKERS) / len(TICKERS)
avg_h10w = sum(r["h5_T10"]["win"] for r in TICKERS) / len(TICKERS)
avg_bw = sum(r["buy_T5"]["win"] for r in TICKERS) / len(TICKERS)
avg_ba = sum(r["buy_T5"]["avg"] for r in TICKERS) / len(TICKERS)

data = {
    "all": {"tickers": [r["ticker"] for r in TICKERS],
            "orig": [r["orig_T5"]["win"] for r in TICKERS],
            "buy": [r["buy_T5"]["win"] for r in TICKERS]},
    "groups": {"tickers": group_tk, "h5": group_h5, "buy": group_buy},
}
D_JSON = json.dumps(data, ensure_ascii=False)

html = (html
        .replace("__DATA_JSON__", D_JSON)
        .replace("__ROWS__", "\n".join(rows))
        .replace("__GROUP_ROWS__", group_rows_h)
        .replace("__NODE_ROWS__", "\n".join(node_rows))
        .replace("__TOT_MERGED__", str(tot_merged))
        .replace("__TOT_NOT__", str(tot_not))
        .replace("__TOT_NOT_PCT__", f"{tot_not/tot_merged*100:.0f}%")
        .replace("__TOT_H5__", str(tot_h5))
        .replace("__TOT_H3__", str(tot_h3))
        .replace("__TOT_HIT__", str(tot_hit))
        .replace("__TOT_MISS__", str(tot_miss))
        .replace("__TOT_RATE__", f"{tot_rate:.0f}%")
        .replace("__H5_T5_WIN__", f"{avg_h5w:.1f}%")
        .replace("__H5_T10_WIN__", f"{avg_h10w:.1f}%")
        .replace("__BUY_T5_WIN__", f"{avg_bw:.1f}%")
        .replace("__BUY_T5_AVG__", f"{avg_ba:+.2f}%"))

import os
out_dir = f"{BASE}/reports/18_公用事业MACD水下金叉回测"
os.makedirs(out_dir, exist_ok=True)
out = f"{out_dir}/公用事业MACD水下金叉回测报告.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out} size={os.path.getsize(out)}")