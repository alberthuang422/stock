#!/usr/bin/env python3
"""生成 VIX 拉涨对 XLV/IBB/GILD/XBI 影响分析的 HTML 报告。
输出 reports/vix_impact_report.html。
"""
import os, json
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS = ["XLV", "IBB", "GILD", "XBI"]
NAMES = {"XLV": "XLV 医疗保健", "IBB": "IBB 生物科技", "GILD": "GILD 吉利德", "XBI": "XBI 小盘生物"}
COLOR = {"XLV": "#e67e22", "IBB": "#c0392b", "GILD": "#1f4e79", "XBI": "#27ae60"}

def load(t):
    df = pd.read_csv(os.path.join(ROOT, "data", t, f"{t}, 1D.csv"), parse_dates=["date"])
    return df[["date", "open", "high", "low", "close", "adj_close"]].sort_values("date").reset_index(drop=True)

def pct(a, b):
    return (b / a - 1) * 100

v = pd.read_csv(os.path.join(ROOT, "data", "vix", "VIX, 1D.csv"), parse_dates=["date"])
v = v[["date", "close"]].sort_values("date").reset_index(drop=True)
D = {t: load(t) for t in TICKERS}

# ---- 事件识别 (与 vix_impact.py 一致) ----
peaks = []
for i in range(2, len(v) - 2):
    if v.loc[i, "close"] >= 24 and v.loc[i, "close"] >= v.loc[i-2:i+3, "close"].max():
        peaks.append(i)
events = []
for pi in peaks:
    lo_idx = v.loc[max(0, pi - 30):pi, "close"].idxmin()
    vlo, vhi = v.loc[lo_idx, "close"], v.loc[pi, "close"]
    if (vhi - vlo) / vlo < 0.35:
        continue
    if events and (v.loc[pi, "date"] - v.loc[events[-1][1], "date"]).days < 120:
        prev_lo, prev_pk = events[-1]
        prev_gain = (v.loc[prev_pk, "close"] - v.loc[prev_lo, "close"]) / v.loc[prev_lo, "close"]
        if (vhi - vlo) / vlo > prev_gain * 1.15:
            events[-1] = (lo_idx, pi)
        continue
    events.append((lo_idx, pi))

# ---- 事件明细 + 窗口表现 + 见顶后修复 ----
ev_rows, fwd = [], {}
for k, (lo, pk) in enumerate(events):
    d_lo, d_pk = v.loc[lo, "date"], v.loc[pk, "date"]
    e = {
        "e": f"E{k+1}",
        "tag": "", "win": f"{d_lo.strftime('%y-%m-%d')} → {d_pk.strftime('%y-%m-%d')}",
        "vix": round(pct(v.loc[lo, "close"], v.loc[pk, "close"])),
        "lo": lo, "pk": pk,
    }
    # 事件标签
    if d_lo.year == 2020 and d_pk.month <= 4: e["tag"] = "COVID 崩盘"
    elif d_pk.year == 2020: e["tag"] = "疫情反复/选举"
    elif d_pk.month == 1 and d_pk.year == 2021: e["tag"] = "散户逼空"
    elif d_pk.year == 2021: e["tag"] = "Omicron"
    elif d_pk.year == 2022 and d_pk.month <= 6: e["tag"] = "2022 熊市"
    elif d_pk.year == 2022: e["tag"] = "2022 熊市"
    elif d_pk.year == 2023: e["tag"] = "SVB 银行危机"
    elif d_pk.year == 2024: e["tag"] = "日元套息平仓"
    elif d_pk.year == 2025 and d_pk.month <= 5: e["tag"] = "关税冲击"
    elif d_pk.year == 2025: e["tag"] = "Q4 波动"
    else: e["tag"] = "2026 年内回调"
    for t in TICKERS:
        sub = D[t][(D[t]["date"] >= d_lo) & (D[t]["date"] <= d_pk)]
        e[t] = round(pct(sub.iloc[0]["adj_close"], sub.iloc[-1]["adj_close"]), 1) if len(sub) >= 3 else None
    ev_rows.append(e)
    # fwd
    for t in TICKERS:
        d = D[t].reset_index(drop=True)
        m = d[d["date"] == d_pk]
        if not len(m): continue
        i = m.index[0]
        for n in [5, 10, 20]:
            if i + n < len(d):
                fwd.setdefault((t, n), []).append(pct(d.loc[i, "adj_close"], d.loc[i + n, "adj_close"]))

fwd_mean = {f"{t}_{n}": round(float(np.mean(fwd[(t, n)])), 2) for t in TICKERS for n in [5, 10, 20]}

# ---- 全期统计 ----
ret_df = pd.DataFrame({"date": v["date"]})
for t in TICKERS:
    ret_df[t] = ret_df["date"].map(D[t].set_index("date")["adj_close"].pct_change() * 100)
v["dvix"] = v["close"].pct_change() * 100
full = ret_df.merge(v[["date", "dvix"]], on="date").dropna()
corr_all = {t: round(full["dvix"].corr(full[t]), 3) for t in TICKERS}
corr_year = {}
full["year"] = full["date"].dt.year
for y in sorted(full["year"].unique()):
    sub = full[full["year"] == y]
    if len(sub) >= 50:
        corr_year[str(y)] = {t: round(sub["dvix"].corr(sub[t]), 2) for t in TICKERS}
up, dn = full[full["dvix"] > 0], full[full["dvix"] < 0]
updn = {t: {"up": round(up[t].mean(), 3), "dn": round(dn[t].mean(), 3)} for t in TICKERS}
buckets = []
for lo, hi, name in [(0, 15, "VIX<15"), (15, 20, "15-20"), (20, 30, "20-30"), (30, 999, ">30")]:
    sd = v[(v["close"] >= lo) & (v["close"] < hi)]["date"]
    buckets.append({"name": name, "n": len(sd), **{t: round(full[full["date"].isin(sd)][t].mean(), 3) for t in TICKERS}})

# ---- 事件统计汇总 ----
stat = {t: {"n_up": 0, "n_all": 0, "avg": 0.0} for t in TICKERS}
for e in ev_rows:
    for t in TICKERS:
        if e[t] is not None:
            stat[t]["n_all"] += 1
            stat[t]["avg"] += e[t]
            if e[t] > 0: stat[t]["n_up"] += 1
for t in TICKERS:
    stat[t]["avg"] = round(stat[t]["avg"] / stat[t]["n_all"], 1)

# ---- K 线数据 (GILD/IBB/XLV, 对齐 VIX 日期, [open, close, low, high]) ----
# TradingView VIX 含 22 个美股休市日(节假日), 标的无数据 -> reindex+ffill 前向填充
kline = {}
for t in ["GILD", "IBB", "XLV"]:
    d2 = D[t].set_index("date")[["open", "high", "low", "close"]].reindex(v["date"]).ffill()
    kline[t] = [[round(r.open, 2), round(r.close, 2), round(r.low, 2), round(r.high, 2)] for r in d2.itertuples()]

data_js = {
    "vix_dates": [d.strftime("%Y-%m-%d") for d in v["date"]],
    "vix_close": [round(x, 1) for x in v["close"]],
    "ohlc": kline,
    "events": ev_rows,
    "fwd": fwd_mean,
    "corr": corr_all,
    "corr_year": corr_year,
    "updn": updn,
    "buckets": buckets,
    "stat": stat,
}
data_json = json.dumps(data_js, ensure_ascii=False)

# ---- HTML 表格 ----
th = "".join(f"<th>{t}<br><span class='sub'>{NAMES[t].split(' ', 1)[1]}</span></th>" for t in TICKERS)
trs = ""
for e in ev_rows:
    tds = ""
    for t in TICKERS:
        val = e[t]
        cls = "up" if val is not None and val > 0 else ("down" if val is not None else "")
        tds += f"<td class='{cls}'>{val if val is not None else '—':+}%</td>" if val is not None else f"<td>—</td>"
    trs += f"<tr><td class='win'>{e['e']}<span class='tag'>{e['tag']}</span><br><span class='sub'>{e['win']}</span></td><td class='sub'>VIX {e['vix']:+}%</td>{tds}</tr>"

# 统计行
trs_stat = "<tr class='sumrow'><td class='win'>平均 / 逆势上涨次数</td><td>—</td>"
for t in TICKERS:
    trs_stat += f"<td><b>{stat[t]['avg']:+.1f}%</b> / {stat[t]['n_up']}次</td>"
trs_stat += "</tr>"

# 分年相关表
rows_corr = ""
for y in sorted(corr_year.keys()):
    rows_corr += f"<tr><td class='win'>{y}</td>" + "".join(f"<td class='{('down' if corr_year[y][t] < 0 else 'up')}'>{corr_year[y][t]:+.2f}</td>" for t in TICKERS) + "</tr>"

# VIX 分桶表
rows_bk = ""
for b in buckets:
    rows_bk += f"<tr><td class='win'>{b['name']}</td><td>{b['n']}</td>" + "".join(f"<td class='{('down' if b[t] < 0 else 'up')}'>{b[t]:+.3f}%</td>" for t in TICKERS) + "</tr>"

# VIX 涨跌日表
rows_ud = ""
for t in TICKERS:
    rows_ud += f"<tr><td class='win'>{t}</td><td class='down'>{updn[t]['up']:+.3f}%</td><td class='up'>{updn[t]['dn']:+.3f}%</td><td class='down'>{updn[t]['up']-updn[t]['dn']:+.3f}%</td></tr>"

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VIX 拉涨对 XLV/IBB/GILD/XBI 的影响分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background:#f7f8fa; color:#222; margin:0; padding:24px; }
  .wrap { max-width:1120px; margin:0 auto; }
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
  .tag { display:inline-block; background:#eef3fb; color:#1f4e79; border-radius:4px; padding:0 6px; font-size:11px; margin-left:6px; }
  .sumrow { background:#f4f7fb; font-weight:600; }
  .concl { border-left:4px solid #1f4e79; background:#f4f7fb; padding:10px 14px; font-size:14px; line-height:1.8; }
  .kline-switch { margin-bottom:8px; }
  .kbtn { border:1px solid #d0d5db; background:#fff; color:#555; padding:4px 14px; border-radius:6px; font-size:13px; cursor:pointer; margin-right:6px; }
  .kbtn.active { background:#1f4e79; color:#fff; border-color:#1f4e79; }
  ul { margin:8px 0; padding-left:20px; } li { margin:5px 0; line-height:1.6; }
</style>
</head>
<body>
<div class="wrap">
  <h1>VIX 拉涨时，XLV / IBB / GILD / XBI 谁抗跌、谁受伤？</h1>
  <div class="meta">VIX：TradingView 日线（2020-01-21 ~ 2026-08-14，用户提供并已存入 data/vix/）｜ 标的：Yahoo Finance 日线（复权价）｜ 生成：2026-08-16</div>

  <div class="cards">
    <div class="card"><div class="k">全期 ΔVIX 日收益相关</div><div class="v">GILD −0.23</div><div class="s">IBB −0.53 ｜ XBI −0.49 ｜ XLV −0.51<br>GILD 对 VIX 最“脱敏”</div></div>
    <div class="card"><div class="k">VIX 拉升事件平均涨跌（11 次）</div><div class="v">GILD +0.6%</div><div class="s">XLV −4.7% ｜ IBB −6.8% ｜ XBI −9.7%<br>GILD 平均几乎不跌，XBI 平均跌近 10%</div></div>
    <div class="card"><div class="k">VIX 拉升时逆势上涨次数</div><div class="v">GILD 6/11</div><div class="s">XLV 2/11 ｜ IBB 1/11 ｜ XBI 2/11<br>GILD 半数事件逆势收涨</div></div>
    <div class="card"><div class="k">2026 年内事件（1/22→3/6）</div><div class="v up">GILD +9.8%</div><div class="s">VIX +89% 期间 GILD 逆势大涨<br>XLV −3.5% ｜ IBB −5.7% ｜ XBI −5.8%</div></div>
  </div>

  <div class="panel">
    <h2>① 结论</h2>
    <div class="concl">
      <b>VIX 拉升 = 板块普跌，但“跌多跌少”差异巨大，GILD 是明显的避风港</b>：2020-2026 共 11 次显著的 VIX 低点→高点拉升（VIX +48%~+504%），期间 XBI 平均 −9.7%、IBB −6.8%、XLV −4.7%，而 <b>GILD 平均 +0.6%，11 次里 6 次逆势上涨</b>（2020-03 COVID +2.9%、2021-12 Omicron +2.9%、2022-04 熊市 +1.8%、2024-08 套息平仓 +9.4%、2026-03 年内回调 +9.8%）。原因：GILD 是现金流稳定、股息率 ~2.3% 的大药企，风格接近防御型 XLV 而非高 beta 的小盘生物科技 XBI；且 2024 年以来 GILD 与 VIX 的日收益相关已降至 −0.09~−0.16（2020-2022 为 −0.33~−0.38），脱敏趋势明显。VIX 见顶后所有标的均修复，高 beta 的 XBI 反弹弹性最大（20 日 +4.3% vs GILD +3.5%）。
    </div>
  </div>

  <div class="panel">
    <h2>② VIX 走势 + IBB/XLV/GILD K 线（阴影区 = 11 次拉升事件）</h2>
    <div class="kline-switch">
      <button class="kbtn active" data-t="GILD">GILD 吉利德</button>
      <button class="kbtn" data-t="IBB">IBB 生物科技</button>
      <button class="kbtn" data-t="XLV">XLV 医疗保健</button>
    </div>
    <div id="chart1" style="width:100%;height:560px;"></div>
    <div class="note">上图（主图）：GILD / IBB / XLV K 线，点击按钮切换；下图：VIX 曲线。红色阴影 = VIX 低点→高点拉升窗口（+35% 以上，峰值相隔 ≥120 日）。红涨绿跌。</div>
  </div>

  <div class="panel">
    <h2>③ 事件窗口：VIX 拉升期间各标的涨跌（%）</h2>
    <div id="chart2" style="width:100%;height:420px;"></div>
    <table>
      <tr><th>事件（VIX 低点→高点）</th><th>VIX 涨幅</th>""" + th + """</tr>
      """ + trs + trs_stat + """
    </table>
    <div class="note">红涨绿跌；负值越深 = VIX 拉升期间跌得越多。GILD 列 6 次为正。</div>
  </div>

  <div class="panel">
    <h2>④ VIX 见顶后：修复弹性（11 次事件均值，%）</h2>
    <div id="chart3" style="width:100%;height:320px;"></div>
    <div class="note">VIX 见顶后 5/10/20 个交易日各标的平均收益：全部为正，XBI 反弹弹性最大。</div>
  </div>

  <div class="panel">
    <h2>⑤ 全期统计</h2>
    <h3 style="font-size:14px;">ΔVIX vs 标的日收益相关（分年）</h3>
    <table>
      <tr><th>年份</th>""" + th + """</tr>
      """ + rows_corr + """
      <tr class="sumrow"><td class="win">全期</td>""" + "".join(f"<td>{corr_all[t]:+.3f}</td>" for t in TICKERS) + """</tr>
    </table>
    <div class="note">GILD 全期 −0.23 最低；2024 起 −0.09~−0.16，已基本与 VIX 脱敏。</div>

    <h3 style="font-size:14px;margin-top:16px;">VIX 上涨日 vs 下跌日：标的平均日收益（%）</h3>
    <table>
      <tr><th>标的</th><th>VIX 上涨日</th><th>VIX 下跌日</th><th>差值</th></tr>
      """ + rows_ud + """
    </table>
    <div class="note">VIX 上涨日所有标的平均下跌，GILD 跌最少（−0.26%/日），XBI 跌最多（−0.89%/日）。</div>

    <h3 style="font-size:14px;margin-top:16px;">VIX 水平分桶：标的当日收益均值（%）</h3>
    <table>
      <tr><th>VIX 区间</th><th>样本日</th>""" + th + """</tr>
      """ + rows_bk + """
    </table>
    <div class="note">VIX &gt; 30 时四者全跌，GILD 跌最少（−0.17%/日），XBI 跌最多（−0.39%/日）；VIX &lt; 20 时普遍正收益。</div>
  </div>

  <div class="panel">
    <h2>数据来源与局限</h2>
    <ul>
      <li><b>VIX</b>：TradingView（TVC_VIX）日线，2020-01-21 ~ 2026-08-14，已存入 <code>data/vix/VIX, 1D.csv</code>（date/open/high/low/close）</li>
      <li><b>标的</b>：Yahoo Finance 日线复权价（本机 Chrome 拉取），IBB/GILD/XBI/XLV 均为 2015-01-02 ~ 2026-08-14</li>
      <li><b>方法</b>：事件识别 = VIX 局部峰值（≥24 且前后 2 日最高）向前 30 交易日找低点，涨幅 ≥35%，峰值相隔 ≥120 日视为独立事件；事件窗口收益用复权价区间涨跌幅</li>
      <li><b>局限</b>：事件窗口内 GILD/IBB 可能包含个股财报等干扰（如 2024-08、2026-03 GILD 逆势涨含财报/催化剂成分）；XBI 等权、IBB 市值加权，成分随时间变化；样本 11 个事件，统计意义有限</li>
    </ul>
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
var C = {"XLV":"#e67e22","IBB":"#c0392b","GILD":"#1f4e79","XBI":"#27ae60"};
var N = {"XLV":"XLV 医疗保健","IBB":"IBB 生物科技","GILD":"GILD 吉利德","XBI":"XBI 小盘生物"};

// chart1: 上 = K 线主图 (GILD/IBB/XLV 可切换) + 事件阴影 / 下 = VIX 副图 + 事件阴影
var RED = '#d23b2e', GREEN = '#1a9e4b';
var curK = 'GILD';
var kChart = echarts.init(document.getElementById('chart1'));
kChart.setOption({
  axisPointer: { link: [{ xAxisIndex: 'all' }] },
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross', label: { show: false } },
    formatter: function(params) {
      if (!params || !params.length) return '';
      var idx = params[0].dataIndex;
      var out = ['<b>' + DATA.vix_dates[idx] + '</b>'];
      params.forEach(function(p) {
        if (p.seriesName === 'K线') {
          var o = p.value;
          if (o && o.length >= 5) {
            out.push('K线(' + curK + '): 开 ' + o[1] + ' / 收 ' + o[2] + ' / 低 ' + o[3] + ' / 高 ' + o[4]);
          }
        } else if (p.seriesName === 'VIX') {
          out.push('VIX: ' + (p.value === null || p.value === undefined ? '-' : p.value));
        }
      });
      return out.join('<br/>');
    }
  },
  legend: { data: ['K线', 'VIX'], top: 0 },
  grid: [
    { left: 58, right: 22, top: '8%', height: '54%' },
    { left: 58, right: 22, top: '70%', height: '20%' }
  ],
  xAxis: [
    { type: 'category', data: DATA.vix_dates, gridIndex: 0, axisLabel: { fontSize: 10 } },
    { type: 'category', data: DATA.vix_dates, gridIndex: 1, axisLabel: { show: false }, axisTick: { show: false } }
  ],
  yAxis: [
    { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: '#eef0f3' } } },
    { scale: true, gridIndex: 1, name: 'VIX', splitLine: { lineStyle: { color: '#eef0f3' } } }
  ],
  dataZoom: [
    { type: 'inside', xAxisIndex: [0, 1], start: 0 },
    { type: 'slider', xAxisIndex: [0, 1], start: 0, height: 18, bottom: 2 }
  ],
  series: [
    {
      name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: DATA.ohlc.GILD,
      itemStyle: { color: RED, color0: GREEN, borderColor: RED, borderColor0: GREEN },
      markArea: {
        itemStyle: { color: 'rgba(200,40,40,0.10)' },
        label: { show: true, fontSize: 11, color: '#8c2f2a', position: 'insideTop' },
        data: DATA.events.map(function(e){ return [{ name: e.tag, xAxis: e.lo }, { xAxis: e.pk }]; })
      }
    },
    {
      name: 'VIX', type: 'line', xAxisIndex: 1, yAxisIndex: 1, showSymbol: false,
      lineStyle: { width: 1.4, color: '#444' }, data: DATA.vix_close,
      markArea: {
        itemStyle: { color: 'rgba(200,40,40,0.10)' },
        data: DATA.events.map(function(e){ return [{ xAxis: e.lo }, { xAxis: e.pk }]; })
      }
    }
  ]
});
document.querySelectorAll('.kbtn').forEach(function(btn){
  btn.addEventListener('click', function(){
    document.querySelectorAll('.kbtn').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
    curK = btn.dataset.t;
    kChart.setOption({ series: [{ type: 'candlestick', data: DATA.ohlc[btn.dataset.t] }] });
  });
});

// chart2: 事件窗口涨跌
echarts.init(document.getElementById('chart2')).setOption({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { data: ['XLV 医疗保健','IBB 生物科技','GILD 吉利德','XBI 小盘生物'] },
  grid: { left: 50, right: 20, top: 40, bottom: 80 },
  xAxis: { type: 'category', data: DATA.events.map(function(e){ return e.e + ' ' + e.tag; }), axisLabel: { interval: 0, rotate: 40, fontSize: 11 } },
  yAxis: { type: 'value', name: '窗口涨跌 %' },
  series: ['XLV','IBB','GILD','XBI'].map(function(k){
    return {
      name: N[k], type: 'bar',
      itemStyle: { color: C[k], borderRadius: [2,2,0,0] },
      data: DATA.events.map(function(e){
        var val = e[k];
        if (val === null || val === undefined) return { value: 0, itemStyle: { color: '#eee' } };
        return { value: val, itemStyle: { color: C[k] } };
      })
    };
  })
});

// chart3: 见顶后修复
echarts.init(document.getElementById('chart3')).setOption({
  tooltip: { trigger: 'axis' },
  legend: { data: ['5日','10日','20日'] },
  grid: { left: 50, right: 20, top: 40, bottom: 40 },
  xAxis: { type: 'category', data: ['XLV 医疗保健','IBB 生物科技','GILD 吉利德','XBI 小盘生物'] },
  yAxis: { type: 'value', name: '平均修复 %' },
  series: [
    { name: '5日', type: 'bar', itemStyle: { color: '#8fb3d9' }, data: ['XLV','IBB','GILD','XBI'].map(function(t){ return DATA.fwd[t + '_5']; }) },
    { name: '10日', type: 'bar', itemStyle: { color: '#4a7fb5' }, data: ['XLV','IBB','GILD','XBI'].map(function(t){ return DATA.fwd[t + '_10']; }) },
    { name: '20日', type: 'bar', itemStyle: { color: '#1f4e79' }, data: ['XLV','IBB','GILD','XBI'].map(function(t){ return DATA.fwd[t + '_20']; }) }
  ]
});
</script>
</body>
</html>
"""

html = html.replace("__DATA_JSON__", data_json)
out = os.path.join(ROOT, "reports", "02_gild_xlv_ibb相关性板块分析", "vix_impact_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out)
