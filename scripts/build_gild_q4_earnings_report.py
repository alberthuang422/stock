#!/usr/bin/env python3
"""生成 GILD 2026-02-10 Q4财报 前后 vs IBB/XBI/XLV 板块对照 HTML 报告。
数据: data/<t>/*.csv (Yahoo 日线, adj_close 复权)。输出 reports/gild_q4_earnings_window_report.html。
"""
import os, json
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(t):
    df = pd.read_csv(os.path.join(ROOT, "data", t, f"{t}, 1D.csv"), parse_dates=["date"])
    return df[["date", "close", "high", "adj_close"]].sort_values("date").reset_index(drop=True)

def pct(a, b):
    return (b / a - 1) * 100

TICKERS = ["GILD", "IBB", "XBI", "XLV"]
D = {t: load(t) for t in TICKERS}

# ---- 归一化走势 (2026-01-02 起) ----
start = "2026-01-02"
norm, dates_n = {}, None
for t in TICKERS:
    sub = D[t][D[t]["date"] >= start].reset_index(drop=True)
    base = sub.iloc[0]["adj_close"]
    norm[t] = [round(x / base * 100, 2) for x in sub["adj_close"]]
    if dates_n is None:
        dates_n = [d.strftime("%m-%d") for d in sub["date"]]

# ---- 窗口收益 ----
WINDOWS = [
    ("财报前主升段 1/5→2/11", "2026-01-05", "2026-02-11"),
    ("1月单月", "2026-01-02", "2026-01-30"),
    ("财报冲刺 1/30→2/11", "2026-01-30", "2026-02-11"),
    ("财报日前后 2/9→2/12", "2026-02-09", "2026-02-12"),
    ("财报后回落 2/17→3/27", "2026-02-17", "2026-03-27"),
    ("3月单月", "2026-03-02", "2026-03-31"),
]
win_rows = []
for name, s, e in WINDOWS:
    row = {"win": name}
    for t in TICKERS:
        sub = D[t][(D[t]["date"] >= s) & (D[t]["date"] <= e)]
        row[t] = round(pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"]), 2)
    win_rows.append(row)

# ---- 财报日前后逐日 (2/9-2/13) ----
daily = []
rows_map = {t: D[t].set_index("date") for t in TICKERS}
sub = D["GILD"][(D["GILD"]["date"] >= "2026-02-09") & (D["GILD"]["date"] <= "2026-02-13")]
for i in range(1, len(sub)):
    d0, d1 = sub.iloc[i-1]["date"], sub.iloc[i]["date"]
    daily.append({
        "date": d1.strftime("%m-%d"),
        **{t: round((rows_map[t].loc[d1, "adj_close"] / rows_map[t].loc[d0, "adj_close"] - 1) * 100, 2) for t in TICKERS},
    })

data_js = {
    "dates": dates_n,
    "norm": {t: norm[t] for t in TICKERS},
    "windows": win_rows,
    "daily": daily,
}
data_json = json.dumps(data_js, ensure_ascii=False)

T = {
    "GILD": "吉利德科学", "IBB": "生物科技ETF", "XBI": "小盘生物科技ETF", "XLV": "医疗保健精选ETF",
}
COLOR = {"GILD": "#1f4e79", "IBB": "#c0392b", "XBI": "#27ae60", "XLV": "#e67e22"}

th = "".join(f"<th>{t}<br><span class='sub'>{T[t]}</span></th>" for t in TICKERS)
trs = ""
for r in win_rows:
    tds = ""
    for t in TICKERS:
        v = r[t]
        cls = "up" if v >= 0 else "down"
        tds += f"<td class='{cls}'>{v:+.2f}%</td>"
    trs += f"<tr><td class='win'>{r['win']}</td>{tds}</tr>"

trd = ""
for r in daily:
    tds = ""
    for t in TICKERS:
        v = r[t]
        cls = "up" if v >= 0 else "down"
        tds += f"<td class='{cls}'>{v:+.2f}%</td>"
    trd += f"<tr><td class='win'>{r['date']}</td>{tds}</tr>"

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GILD Q4财报(2026-02-10)前后 vs 板块对照（IBB/XBI/XLV）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background:#f7f8fa; color:#222; margin:0; padding:24px; }
  .wrap { max-width:1080px; margin:0 auto; }
  h1 { font-size:22px; margin:0 0 4px; }
  .meta { color:#888; font-size:12px; margin-bottom:18px; }
  .cards { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px; }
  .card { flex:1; min-width:210px; background:#fff; border-radius:10px; padding:14px 16px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
  .card .k { font-size:12px; color:#888; margin-bottom:6px; }
  .card .v { font-size:20px; font-weight:700; }
  .card .s { font-size:12px; color:#999; margin-top:4px; }
  .up { color:#d23b2e; } .down { color:#1a9e4b; }
  .panel { background:#fff; border-radius:10px; padding:18px; margin-bottom:20px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
  .panel h2 { font-size:16px; margin:0 0 12px; }
  .note { font-size:12px; color:#888; margin-top:8px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { padding:7px 8px; border-bottom:1px solid #eee; text-align:right; }
  th { background:#fafbfc; color:#555; font-weight:600; text-align:right; }
  td.win, th:first-child { text-align:left; }
  .sub { font-size:11px; color:#aaa; font-weight:400; }
  .hl { background:#fff8e6; }
  ul { margin:8px 0; padding-left:20px; } li { margin:5px 0; line-height:1.6; }
  .tag { display:inline-block; background:#eef3fb; color:#1f4e79; border-radius:4px; padding:1px 7px; font-size:12px; margin-right:6px; }
  .concl { border-left:4px solid #1f4e79; background:#f4f7fb; padding:10px 14px; font-size:14px; line-height:1.8; }
  .vs { border-left:4px solid #c0392b; background:#fdf4f2; padding:10px 14px; font-size:13px; line-height:1.8; margin-top:12px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>GILD Q4 财报（2026-02-10 盘后发布）前后：板块主升浪，还是 GILD 独自的行情？</h1>
  <div class="meta">标的：GILD（吉利德科学）vs IBB / XBI / XLV ｜ 行情：Yahoo Finance 日线（复权价），截至 2026-08-14 ｜ 生成：2026-08-16</div>

  <div class="cards">
    <div class="card"><div class="k">财报前主升段（1/5→2/11）</div><div class="v up">GILD +31.7%</div><div class="s">IBB +3.2% ｜ XBI +3.8% ｜ XLV +0.8%<br>板块几乎没动 → GILD 独立行情，非板块主升浪</div></div>
    <div class="card"><div class="k">财报日（2/10 盘后）+ 次日</div><div class="v up">2/11 单日 +5.8%</div><div class="s">冲历史新高 $155.39<br>Q4 超预期 + 分红上调 + 分析师集体上调目标价</div></div>
    <div class="card"><div class="k">财报后回落（2/17→3/27）</div><div class="v down">GILD -13.1%</div><div class="s">IBB -7.8% ｜ XLV -8.6% ｜ XBI -4.0%<br>板块同步回调，GILD 跌得更深</div></div>
    <div class="card"><div class="k">回落主因</div><div class="v">2026 指引偏保守</div><div class="s">EPS 指引中值低于共识 + 医保定价/ACA 不确定 + 利好兑现</div></div>
  </div>

  <div class="panel">
    <h2>① 结论</h2>
    <div class="concl">
      <b>这次不是板块主升浪——是 GILD 独自的 α 行情</b>。财报前（1/5→2/11）GILD 暴涨 +31.7%，同期 IBB/XBI/XLV 仅 +0.8%~+3.8%（XLV 1 月还是负的），板块完全没参与。财报日 2/10 盘后发布 Q4（营收/EPS 双超预期、分红上调 3.8%），2/11 单日 +5.8% 冲历史新高 $155.39；随后 2/17 见顶回落，财报后至 3 月底 GILD -13.1%（板块同步回调 -4%~-8.6%，GILD 跌得更深，因 2026 全年指引中值低于共识 + 医保定价/ACA 不确定性 + 利好兑现）。
    </div>
    <div class="vs">
      <b>与 8 月 Q2 财报（2026-08-04）形态完全相反</b>：8 月那次是<b>板块主升浪</b>（6/10→7/7：XBI +27%、IBB +19% &gt; GILD +13%，GILD 跑输板块，财报后两日板块齐涨、仅 GILD 独跌）；2 月这次是<b>GILD 个股行情</b>（财报前独自 +31.7%、板块横盘，财报后 GILD 跌得比板块深）。同一个公司、两个财报窗口，板块联动度截然不同。
    </div>
  </div>

  <div class="panel">
    <h2>② 归一化走势（2026-01-02 = 100）</h2>
    <div id="chart1" style="width:100%;height:400px;"></div>
    <div class="note">GILD（深蓝）1 月独自陡峭上行、2/11 触历史高点，2/17 起回落；IBB/XBI/XLV 全程横盘-温和波动，从未走出主升浪。</div>
  </div>

  <div class="panel">
    <h2>③ 关键窗口收益对照</h2>
    <div id="chart2" style="width:100%;height:360px;"></div>
    <table>
      <tr><th>窗口</th>""" + th + """</tr>
      """ + trs + """
    </table>
    <div class="note">红涨绿跌；收益为复权价（adj_close）区间涨跌幅。财报日 2/10 盘后发布（当日常规交易反映的是财报前预期），2/11 为市场消化日。</div>
  </div>

  <div class="panel">
    <h2>④ 财报日前后逐日涨跌（%）</h2>
    <table>
      <tr><th>日期</th>""" + th + """</tr>
      """ + trd + """
    </table>
    <div class="note">2/10 财报日：GILD -2.94%（财报前获利回吐）；2/11：+5.82% 冲历史新高（Q4 超预期 + 分红上调 + 分析师集体上调目标价）；2/12：-2.56% 回落；2/17 见顶后进入持续回落。</div>
  </div>

  <div class="panel">
    <h2>⑤ GILD 的“特别驱动”拆解：为什么只有它涨/跌</h2>
    <table>
      <tr><th>阶段</th><th>板块同步性</th><th>GILD 个股驱动</th></tr>
      <tr><td class="win">1 月初–2/11<br>（财报前主升段）</td>
          <td><span class="tag">α 独立</span>板块横盘：IBB +3.2%、XBI +3.8%、XLV +0.8%，GILD 独自 +31.7%</td>
          <td>预期抢跑：1/7 UBS 上调至买入（目标 $112→$145）+ Citi 上调（$140）；1/12 JPM 医疗会议 CEO 宣布 Yeztugo 保险覆盖 &gt;80%（CVS 1/1 起纳入，90% 无自付）；1/26 BMO 上调至 $150 + UBS 再上调至 $155（股价 52 周新高、4 连涨）；12/22 许可 Assembly Biosciences HSV 长效口服管线；Yeztugo 2025 销售目标 $150M 提前达成</td></tr>
      <tr><td class="win">2/10 财报日（盘后）<br>→ 2/11 反应</td>
          <td><span class="tag">个股事件</span>板块 2/10 当天 -2.1%~-2.3%（随大盘），GILD 2/11 独涨 +5.8% 创新高</td>
          <td>Q4 营收 $79.3 亿（+5%，超预期）、调整后 EPS $1.86（超预期 $1.81）；季度分红上调 3.8% 至 $0.82；分析师集体上调目标价（Needham $140→$170、Scotiabank $177、Cantor $155、BofA $162）</td></tr>
      <tr><td class="win hl">2/17–3/27<br>（财报后回落）</td>
          <td><span class="tag">β+α 叠加</span>板块同步回调（IBB -7.8%、XLV -8.6%、XBI -4.0%），GILD -13.1% 跌得更深</td>
          <td>2026 指引偏保守（“beat the quarter, miss the year”）：EPS 指引 8.45–8.85 中值低于共识；产品销售额 296–300 亿低于预期；最惠国定价协议 + Medicare Part D 改革 + Biktarvy 入选 MFP 谈判；ACA 补贴到期致参保不确定；利好兑现（财报前涨太多）+ 1/23 CEO 10b5-1 减持 $15.6M</td></tr>
    </table>
  </div>

  <div class="panel">
    <h2>⑥ 一句话回答</h2>
    <ul>
      <li><b>IBB/XBI/XLV 在这段也是主升浪吗？</b> —— <b>不是</b>。财报前主升段 GILD +31.7%，板块仅 +0.8%~+3.8%（XLV 1 月 -0.5%），板块全程横盘；“涨很凶”完全是 GILD 个股事件（Yeztugo 放量叙事 + 分析师连环上调 + 财报预期抢跑），与板块无关。</li>
      <li><b>GILD 有什么特别的驱动吗？</b> —— 有，而且就是这次行情的主角：财报前的催化是 <b>Yeztugo（一年两次 HIV 预防针）保险覆盖突破 &gt;80% + UBS/Citi/BMO 连环上调目标价</b>；财报后回落则是 <b>2026 全年指引中值低于共识 + 医保定价/ACA 不确定 + 利好兑现</b>，且跌得比同步回调的板块更深（-13.1% vs -4%~-8.6%）。</li>
    </ul>
  </div>

  <div class="panel">
    <h2>数据来源</h2>
    <ul>
      <li><b>行情</b>：Yahoo Finance 日线（本机 Chrome 拉取），复权收盘价，截至 2026-08-14（GILD/IBB/XBI/XLV 各自交易日对齐）</li>
      <li><b>财报</b>：GILD 2026-02-10 盘后发布 Q4/FY2025 财报（一手来源）：Q4 营收 $79.3 亿（+5%，超预期 $76.8-76.9 亿）、调整后 EPS $1.86（超预期 $1.81）、季度股息上调 3.8% 至 $0.82；FY2026 指引：调整后 EPS $8.45-8.85（共识 $8.74-8.76）、产品销售额 $296-300 亿（共识约 $302 亿）</li>
      <li><b>催化剂</b>：公开新闻与研报（UBS/Citi/BMO 评级报告、JPM 医疗会议、Reuters/Investing/Benzinga 等 2026-01~02 报道）——<b>非一手来源，需核实原文</b></li>
    </ul>
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
var C = {"GILD":"#1f4e79","IBB":"#c0392b","XBI":"#27ae60","XLV":"#e67e22"};
var N = {"GILD":"GILD 吉利德","IBB":"IBB 生物科技","XBI":"XBI 小盘生物","XLV":"XLV 医疗保健"};

echarts.init(document.getElementById('chart1')).setOption({
  tooltip: { trigger: 'axis' },
  legend: { data: ['GILD 吉利德','IBB 生物科技','XBI 小盘生物','XLV 医疗保健'] },
  grid: { left: 50, right: 20, top: 40, bottom: 40 },
  xAxis: { type: 'category', data: DATA.dates },
  yAxis: { type: 'value', name: '归一化 (1/2=100)' },
  series: ['GILD','IBB','XBI','XLV'].map(function(k){
    return {
      name: N[k], type: 'line', smooth: true, showSymbol: false,
      lineStyle: { width: k==='GILD'?3.5:1.8, color: C[k] },
      itemStyle: { color: C[k] },
      data: DATA.norm[k]
    };
  })
});

echarts.init(document.getElementById('chart2')).setOption({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { data: ['GILD 吉利德','IBB 生物科技','XBI 小盘生物','XLV 医疗保健'] },
  grid: { left: 50, right: 20, top: 40, bottom: 60 },
  xAxis: { type: 'category', data: DATA.windows.map(function(w){return w.win;}), axisLabel: { interval: 0, rotate: 28, fontSize: 11 } },
  yAxis: { type: 'value', name: '区间涨跌幅 %' },
  series: ['GILD','IBB','XBI','XLV'].map(function(k){
    return {
      name: N[k], type: 'bar',
      itemStyle: { color: C[k], borderRadius: [2,2,0,0] },
      data: DATA.windows.map(function(w){
        var v = w[k];
        return { value: v, itemStyle: { color: v >= 0 ? C[k] : '#1a9e4b' } };
      })
    };
  })
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)
out = os.path.join(ROOT, "reports", "gild_q4_earnings_window_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out)
