#!/usr/bin/env python3
"""生成 GILD 财报(2026-08-04)前后 vs IBB/XBI/XLV 板块对照 HTML 报告。
数据: data/<t>/*.csv (Yahoo 日线, adj_close 复权)。输出 reports/gild_earnings_window_report.html。
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

# ---- 归一化走势 (2026-06-01 起, 以 6/1 adj_close = 100) ----
start = "2026-06-01"
norm = {}
dates_n = None
for t in TICKERS:
    sub = D[t][D[t]["date"] >= start].reset_index(drop=True)
    base = sub.iloc[0]["adj_close"]
    norm[t] = [round(x / base * 100, 2) for x in sub["adj_close"]]
    if dates_n is None:
        dates_n = [d.strftime("%m-%d") for d in sub["date"]]

# ---- 窗口收益 ----
WINDOWS = [
    ("财报前主升段 6/10→7/7", "2026-06-10", "2026-07-07"),
    ("财报前回落段 7/7→8/3", "2026-07-07", "2026-08-03"),
    ("财报日当周 7/31→8/7", "2026-07-31", "2026-08-07"),
    ("财报后两日 8/4→8/6", "2026-08-04", "2026-08-06"),
    ("财报后修复段 8/6→8/14", "2026-08-06", "2026-08-14"),
    ("近一周 8/7→8/14", "2026-08-07", "2026-08-14"),
]
win_rows = []
for name, s, e in WINDOWS:
    row = {"win": name}
    for t in TICKERS:
        sub = D[t][(D[t]["date"] >= s) & (D[t]["date"] <= e)]
        row[t] = round(pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"]), 2)
    win_rows.append(row)

# ---- 财报后逐日 ----
daily = []
sub = D["GILD"][D["GILD"]["date"] >= "2026-08-04"]
idx = D["GILD"].set_index("date")
rows_map = {t: D[t].set_index("date") for t in TICKERS}
for i in range(1, len(sub)):
    d0, d1 = sub.iloc[i-1]["date"], sub.iloc[i]["date"]
    daily.append({
        "date": d1.strftime("%m-%d"),
        **{t: round((rows_map[t].loc[d1, "adj_close"] / rows_map[t].loc[d0, "adj_close"] - 1) * 100, 2) for t in TICKERS},
    })

# ---- 归一化区间高低点(6/1-8/3, 定位涨跌起点) ----
g6 = D["GILD"][(D["GILD"]["date"] >= "2026-06-01") & (D["GILD"]["date"] <= "2026-08-03")]
lo_d = g6.loc[g6["adj_close"].idxmin(), "date"].strftime("%m-%d")
hi_d = g6.loc[g6["adj_close"].idxmax(), "date"].strftime("%m-%d")

data_js = {
    "dates": dates_n,
    "norm": {t: norm[t] for t in TICKERS},
    "windows": win_rows,
    "daily": daily,
    "lo_d": lo_d, "hi_d": hi_d,
}
data_json = json.dumps(data_js, ensure_ascii=False)

T = {
    "GILD": "吉利德科学", "IBB": "生物科技ETF", "XBI": "小盘生物科技ETF", "XLV": "医疗保健精选ETF",
}
COLOR = {"GILD": "#1f4e79", "IBB": "#c0392b", "XBI": "#27ae60", "XLV": "#e67e22"}

# ---- 窗口表 HTML ----
th = "".join(f"<th>{t}<br><span class='sub'>{T[t]}</span></th>" for t in TICKERS)
trs = ""
for r in win_rows:
    tds = ""
    for t in TICKERS:
        v = r[t]
        cls = "up" if v >= 0 else "down"
        tds += f"<td class='{cls}'>{v:+.2f}%</td>"
    trs += f"<tr><td class='win'>{r['win']}</td>{tds}</tr>"

# ---- 逐日表 ----
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
<title>GILD 财报前后 vs 板块对照（IBB/XBI/XLV）</title>
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
</style>
</head>
<body>
<div class="wrap">
  <h1>GILD 财报（2026-08-04）前后：是板块主升浪，还是 GILD 独自的行情？</h1>
  <div class="meta">标的：GILD（吉利德科学）vs IBB / XBI / XLV ｜ 行情：Yahoo Finance 日线（复权价），截至 2026-08-14 ｜ 生成：2026-08-16</div>

  <div class="cards">
    <div class="card"><div class="k">财报前主升段（6/10→7/7）</div><div class="v up">GILD +13.0%</div><div class="s">IBB +19.5% ｜ XBI +27.3% ｜ XLV +8.1%<br>板块涨得比 GILD 更猛 → 主升浪是板块性的</div></div>
    <div class="card"><div class="k">财报日 8/4 当天</div><div class="v up">GILD +3.13%</div><div class="s">IBB +2.28% ｜ XBI +3.10% ｜ XLV -0.09%<br>板块齐涨，非 GILD 独有</div></div>
    <div class="card"><div class="k">财报后两日（8/4→8/6）</div><div class="v down">GILD -3.25%</div><div class="s">IBB +1.48% ｜ XBI +1.73% ｜ XLV +1.45%<br>只有 GILD 跌 → 真正的个股事件</div></div>
    <div class="card"><div class="k">最新（8/14 收）</div><div class="v up">GILD $138.36</div><div class="s">已突破 7/7 前高 $136.36，创财报后新高<br>“快速回落”仅持续 2 天即 V 型修复</div></div>
  </div>

  <div class="panel">
    <h2>① 结论</h2>
    <div class="concl">
      <b>“财报前涨很凶”是板块主升浪 + GILD 个股催化叠加，且 GILD 其实跑输板块</b>（6/10→7/7：XBI +27.3% &gt; IBB +19.5% &gt; GILD +13.0% &gt; XLV +8.1%）。真正<b>只有 GILD 独自演绎</b>的是财报后 8/5–8/6 的回落：板块同期齐涨（+1.5% 左右），仅 GILD 因财报账面净亏 $105 亿而回吐 -3.3%。随后市场认定亏损为收购一次性计提、主业 HIV 增长 +12%，2 天内修复并创新高——所以这不是“财报见光死”，而是“财报噪音吓退短线资金”。
    </div>
  </div>

  <div class="panel">
    <h2>② 归一化走势（2026-06-01 = 100）</h2>
    <div id="chart1" style="width:100%;height:400px;"></div>
    <div class="note">GILD 于 06-10 见底（相对板块晚一周），07-07 见顶后与板块一同回调；8/4 财报后两日独跌，随后 8/7 起领涨并创新高。</div>
  </div>

  <div class="panel">
    <h2>③ 关键窗口收益对照</h2>
    <div id="chart2" style="width:100%;height:360px;"></div>
    <table>
      <tr><th>窗口</th>""" + th + """</tr>
      """ + trs + """
    </table>
    <div class="note">红涨绿跌；收益为复权价（adj_close）区间涨跌幅。</div>
  </div>

  <div class="panel">
    <h2>④ 8/4 财报发布后逐日涨跌（%）</h2>
    <table>
      <tr><th>日期</th>""" + th + """</tr>
      """ + trd + """
    </table>
    <div class="note">8/5–8/6 为 GILD 独跌窗口：板块（IBB/XBI/XLV）连续两日收涨，GILD 两日合计 -3.25%；8/7 起修复，8/14 收 138.36 高于财报日收盘。</div>
  </div>

  <div class="panel">
    <h2>⑤ GILD 的“特别驱动”拆解：β（板块）与 α（个股）</h2>
    <table>
      <tr><th>阶段</th><th>板块同步性</th><th>GILD 个股驱动</th></tr>
      <tr><td class="win">6 月中旬–7/7<br>（财报前主升段）</td>
          <td><span class="tag">β 为主</span>板块主升浪：IBB +19.5%、XBI +27.3%，GILD 涨幅落后板块</td>
          <td>Trodelvy 一线 mTNBC 获批（6/24 美国 + 欧盟 27 国首个一线 ADC）；Yeztugo 每周口服 PrEP 获 FDA 受理（6/15）；ISL/LEN 每周口服 HIV III 期双达终点；HSBC 上调买入（7/6–7/7，目标 $133→$155）→ 7/7 单日 +5.2%</td></tr>
      <tr><td class="win">7/7–8/3<br>（财报前回落）</td>
          <td><span class="tag">β 同步</span>板块性回调：XBI -10.1%、IBB -6.2%，GILD -3.8% 居中</td>
          <td>无明显利空，随板块回调；期间 7/16 成交额全市场第一（机构抢跑财报）</td></tr>
      <tr><td class="win hl">8/4 财报日</td>
          <td><span class="tag">板块齐涨</span>IBB +2.3%、XBI +3.1% 同步大涨</td>
          <td>Q2 营收 $78.0 亿 +10%（超预期 5.4%）、HIV +12%、上调全年指引；GAAP 净亏 $104.96 亿（收购 IPR&D $112 亿 + Trodelvy 减值 $17.5 亿，一次性非现金）</td></tr>
      <tr><td class="win hl">8/5–8/6<br>（财报后回落）</td>
          <td><span class="tag">α 独立</span>板块仍在涨（IBB/XBI/XLV +1.4~1.7%），GILD 独自 -3.25%</td>
          <td>账面巨亏 $105 亿引发短线抛售；illustrative EPS $2.27（+13%）显示主业健康</td></tr>
      <tr><td class="win">8/7–8/14<br>（修复）</td>
          <td><span class="tag">α 领涨</span>GILD +3.9% vs IBB +0.3%、XBI 0.0%、XLV +1.0%</td>
          <td>市场消化“亏损是一次性计提”；8/27 BIC/LEN（每日一次 HIV 复方）PDUFA 临近，财报前即有预期抢跑</td></tr>
    </table>
  </div>

  <div class="panel">
    <h2>⑥ 一句话回答</h2>
    <ul>
      <li><b>IBB/XBI/XLV 在这段也是主升浪吗？</b> —— <b>是，而且是它们领涨</b>。财报前主升段 GILD +13%，板块 +8%~+27%，GILD 并未跑赢板块；“财报前涨很凶”主要是搭板块主升浪的便车，个股催化（Trodelvy 获批 + 长效 HIV 数据 + HSBC 上调）锦上添花。</li>
      <li><b>GILD 有特别的驱动因素吗？</b> —— 有，但体现在<b>财报后而非财报前</b>：8/5–8/6 板块齐涨、仅 GILD 独跌（Q2 账面净亏 $105 亿的财报噪音），这是 GILD 独有的 α 事件；且 2 天即修复、创新高，说明市场认定该亏损为收购一次性非现金计提，主业（HIV +12%、上调指引）才是定价核心。</li>
    </ul>
  </div>

  <div class="panel">
    <h2>数据来源</h2>
    <ul>
      <li><b>行情</b>：Yahoo Finance 日线（本机 Chrome 拉取），复权收盘价，截至 2026-08-14（GILD/IBB/XBI/XLV 各自交易日对齐）</li>
      <li><b>财报</b>：GILD 2026-08-04 发布 Q2 财报（10-Q/8-K，一手来源）：营收 $78.0 亿（+10%）、HIV $56.9 亿（+12%）、GAAP 净亏 $104.96 亿（Arcellx/Tubulis/Ouro 收购 IPR&D $112 亿 + Trodelvy 减值 $17.5 亿）、illustrative EPS $2.27（+13%）、上调全年指引</li>
      <li><b>催化剂</b>：公开新闻与研报（BellwetherBrief、StockToTrade、Zacks、Mitrade、AInvest、Longbridge 等，2026-06 ~ 08 报道）——<b>非一手来源，需核实原文</b></li>
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
  yAxis: { type: 'value', name: '归一化 (6/1=100)' },
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
out = os.path.join(ROOT, "reports", "gild_earnings_window_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out)
