#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 GILD/ABBV 横盘突破 T+N 收益分析报告 (带 K 线与突破标记)。

- 每标的: 全史 K 线总览图 (markPoint 橙色三角标记全部突破, markLine 显示突破日)
- 每笔突破: 局部 K 线图 [突破前 20 交易日 ~ 突破后 20 交易日], 标出:
  通道上沿(虚线)/突破日(橙色三角+日期标签)/突破 K 线
- 统计: pooled / 分标的 / 分年 / 基线对照 (全部交易日 T+N)
- 风格: 浅底深字研报风 + ECharts, 红涨绿跌
"""
import os
import json
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "results", "gild_abbv_breakout")
REPORT_DIR = os.path.join(ROOT, "reports", "11_gild突破回踩")
os.makedirs(REPORT_DIR, exist_ok=True)

TICKERS = ["GILD", "ABBV"]
NAMES = {"GILD": "GILD 吉利德", "ABBV": "ABBV 艾伯维"}
COLORS = {"GILD": "#c0392b", "ABBV": "#1f4e79"}
RED, GREEN = "#d23b2e", "#1a9e4b"
ORANGE = "#e67e22"
PRE, POST = 20, 20   # 局部图: 突破前 20 / 后 20 交易日
N_CHANNEL = 20


def load(t):
    df = pd.read_csv(os.path.join(ROOT, "data", t, f"{t}, 1D.csv"), parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def pct(a, b):
    return round((b / a - 1) * 100, 2)


def local_data(df, i0, pre=PRE, post=POST):
    """局部 K 线窗口 [i0-pre, i0+post], 返回 ohlc/dates/upper。"""
    a, b = max(0, i0 - pre), min(len(df), i0 + post + 1)
    sub = df.iloc[a:b].reset_index(drop=True)
    u = df["high"].rolling(N_CHANNEL).max().shift(1)
    ohlc = [[round(r.open, 2), round(r.close, 2), round(r.low, 2), round(r.high, 2)]
            for r in sub.itertuples()]
    dates = [d.strftime("%Y-%m-%d") for d in sub["date"]]
    upper = [round(float(u.loc[i]), 2) if not pd.isna(u.loc[i]) else None
             for i in sub.index + a]
    # 突破日在局部窗口中的下标
    idx_brk = i0 - a
    return {
        "dates": dates, "ohlc": ohlc, "upper": upper,
        "brk_idx": idx_brk,
        "brk_date": dates[idx_brk],
    }


def local_data_box(df, i0, box, post=POST, lead=2):
    """动态局部窗口: 从横盘区间起点往前 lead 根到突破后 post 交易日, 使矩形阴影完整可见。
    返回含 box 相对坐标的 dict。"""
    b0 = df.index[df["date"] == pd.Timestamp(box["box_start"])][0]
    a = max(0, b0 - lead)
    b = min(len(df), i0 + post + 1)
    sub = df.iloc[a:b].reset_index(drop=True)
    u = df["high"].rolling(N_CHANNEL).max().shift(1)
    ohlc = [[round(r.open, 2), round(r.close, 2), round(r.low, 2), round(r.high, 2)]
            for r in sub.itertuples()]
    dates = [d.strftime("%Y-%m-%d") for d in sub["date"]]
    upper = [round(float(u.loc[i]), 2) if not pd.isna(u.loc[i]) else None
             for i in sub.index + a]
    idx_brk = i0 - a
    b1 = df.index[df["date"] == pd.Timestamp(box["box_end"])][0]
    xL = b0 - a
    xR = b1 - a
    return {
        "dates": dates, "ohlc": ohlc, "upper": upper,
        "brk_idx": idx_brk,
        "brk_date": dates[idx_brk],
        "box": {**box, "xL": xL, "xR": xR},
    }


def main():
    events = json.load(open(os.path.join(OUT_DIR, "events.json"), encoding="utf-8"))
    stats = json.load(open(os.path.join(OUT_DIR, "stats.json"), encoding="utf-8"))
    ev_df = pd.DataFrame(events)
    boxes = stats["boxes"]

    # ---- 每个交易日的全局行情 (用于全史 K 线) ----
    allk = {}
    dfs = {}
    for t in TICKERS:
        df = load(t)
        dfs[t] = df
        allk[t] = {
            "dates": [d.strftime("%Y-%m-%d") for d in df["date"]],
            "ohlc": [[round(r.open, 2), round(r.close, 2), round(r.low, 2), round(r.high, 2)]
                     for r in df.itertuples()],
        }

    # ---- 每笔突破的局部数据 ----
    locals_js = {}
    detail_rows = []
    for t in TICKERS:
        df = dfs[t]
        evs = ev_df[ev_df["ticker"] == t].sort_values("date").reset_index(drop=True)
        arr = []
        for _, e in evs.iterrows():
            i0 = df.index[df["date"] == pd.Timestamp(e["date"])][0]
            local = local_data_box(df, i0, next((b for b in boxes if b["dt"] == e["date"]), None))
            arr.append(local)
        locals_js[t] = arr

    # ---- 明细表行 ----
    label_map = {"ret1": "T+1", "ret5": "T+5", "ret20": "T+20"}
    for _, e in ev_df.iterrows():
        fwds = [(label_map[f"ret{n}"], e[f"ret{n}"]) for n in [1, 5, 20]]
        tds = ""
        for name, v in fwds:
            if pd.isna(v):
                tds += "<td>—</td>"
            else:
                cls = "up" if v > 0 else ("down" if v < 0 else "")
                tds += f"<td class='{cls}'>{v:+.2f}%</td>"
        detail_rows.append(
            f"<tr><td class='win'>{t}</td><td class='win'>{e['date']}</td>"
            f"<td>{e['close']:.2f}</td><td class='up'>{e['gain']:+.2f}%</td>"
            f"<td>{e['upper']:.2f}</td><td>{e['lower']:.2f}</td>{tds}</tr>"
        )
    detail_rows_html = "\n".join(detail_rows)

    # ---- 统计表行 ----
    def stat_tds(s):
        if s.get("n", 0) == 0:
            return "<td>0</td><td>—</td><td>—</td><td>—</td><td>—</td>"
        cls_m = "up" if s["mean"] > 0 else ("down" if s["mean"] < 0 else "")
        cls_w = "up" if s["win"] >= 50 else ("down" if s["win"] < 50 else "")
        return (f"<td>{s['n']}</td>"
                f"<td class='{cls_m}'>{s['mean']:+.2f}%</td>"
                f"<td class='{cls_m}'>{s['median']:+.2f}%</td>"
                f"<td class='{cls_w}'>{s['win']:.0f}%</td>"
                f"<td>{s['p25']:+.2f}% / {s['p75']:+.2f}%</td>")

    st = stats
    rows_pooled = ""
    for n in [1, 5, 20]:
        s = st["pooled"][f"T+{n}"]
        rows_pooled += f"<tr><td class='win'>全部（GILD+ABBV）· T+{n}</td>{stat_tds(s)}</tr>"
    for t in TICKERS:
        for n in [1, 5, 20]:
            s = st["per_ticker"][t][f"T+{n}"]
            rows_pooled += f"<tr><td class='win'>{t} · T+{n}</td>{stat_tds(s)}</tr>"

    rows_year = ""
    for y in sorted(st["by_year"].keys()):
        s = st["by_year"][y]
        tds = f"<td>{s['n']}</td>"
        for n in [1, 5, 20]:
            ss = s[f"T+{n}"]
            cls = "up" if ss["mean"] > 0 else ("down" if ss["mean"] < 0 else "")
            tds += f"<td class='{cls}'>{ss['mean']:+.2f}%</td>"
        rows_year += f"<tr><td class='win'>{y}</td>{tds}</tr>"

    rows_base = ""
    for t in TICKERS:
        for n in [1, 5, 20]:
            s = st["baseline"][f"{t}_T+{n}"]
            rows_base += f"<tr><td class='win'>{t} 全部交易日 · T+{n}</td>{stat_tds(s)}</tr>"

    # KPI 卡
    p5, p20 = st["pooled"]["T+5"], st["pooled"]["T+20"]
    g5 = st["per_ticker"]["GILD"]["T+5"]
    a20 = st["per_ticker"]["ABBV"]["T+20"]
    kpi_cards = f"""
    <div class="card"><div class="k">突破样本数（2015-2026）</div><div class="v">{st['pooled']['n']} 笔</div><div class="s">GILD {st['per_ticker']['GILD']['n']} ｜ ABBV {st['per_ticker']['ABBV']['n']}</div></div>
    <div class="card"><div class="k">T+5 平均 / 胜率</div><div class="v {'up' if p5['mean']>0 else 'down'}">{p5['mean']:+.2f}%</div><div class="s">胜率 {p5['win']:.0f}% ｜ 中位 {p5['median']:+.2f}%</div></div>
    <div class="card"><div class="k">T+20 平均 / 胜率</div><div class="v {'up' if p20['mean']>0 else 'down'}">{p20['mean']:+.2f}%</div><div class="s">胜率 {p20['win']:.0f}% ｜ 中位 {p20['median']:+.2f}%</div></div>
    <div class="card"><div class="k">GILD vs ABBV · T+5 胜率</div><div class="v">{g5['win']:.0f}% / {st['per_ticker']['ABBV']['T+5']['win']:.0f}%</div><div class="s">GILD {g5['mean']:+.2f}% ｜ ABBV {st['per_ticker']['ABBV']['T+5']['mean']:+.2f}%</div></div>
    <div class="card"><div class="k">ABBV · T+20</div><div class="v {'up' if a20['mean']>0 else 'down'}">{a20['mean']:+.2f}%</div><div class="s">胜率 {a20['win']:.0f}% ｜ 中位 {a20['median']:+.2f}%</div></div>
    """

    data_js = {
        "tickers": TICKERS,
        "allk": allk,
        "locals": locals_js,
        "events": events,
    }
    data_json = json.dumps(data_js, ensure_ascii=False)

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GILD / ABBV 横盘突破 T+N 收益分析</title>
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
  .note { font-size:12px; color:#888; margin-top:8px; line-height:1.7; }
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
  .gallery { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:14px; }
  .fig { background:#fff; border-radius:8px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .fig .cap { font-size:12px; color:#555; margin:4px 2px 2px; }
  .fig .cap b { font-size:13px; color:#222; }
  ul { margin:8px 0; padding-left:20px; } li { margin:5px 0; line-height:1.6; }
  .scroll { overflow-x:auto; }
</style>
</head>
<body>
<div class="wrap">
  <h1>GILD / ABBV 横盘突破后的 T+1 / T+5 / T+20 表现</h1>
  <div class="meta">Yahoo Finance 日线（复权价口径计算收益）｜ 2015-01-02 ~ 2026-08-14 ｜ 突破口径：20日 Donchian 通道 + 收盘有效上穿 + 当日涨幅 ≥2.5% + 横盘确认 ｜ 生成：2026-08-21</div>

  <div class="cards">
    """ + kpi_cards + """
  </div>

  <div class="panel">
    <h2>① 核心结论</h2>
    <div class="concl">
      <b>横盘放量突破在两只大药企上整体偏正，且"越拿越久越值钱"</b>：2015-2026 共 50 笔有效横盘突破，T+1 平均 +0.44%（胜率 52%）、T+5 平均 +0.34%（胜率 52%）、<b>T+20 平均 +3.05%、胜率 66%、中位 +4.3%</b>——短周期（1~5 日）几乎没有方向性优势，收益主要靠持有 20 个交易日兑现。分标的看，ABBV 的 T+5 胜率（~<span id="abbv5w">—</span>%）与均值略优于 GILD；GILD 短期波动更大（2016/2017 出现多笔假突破）。分年看，2016 年最差（T+5 平均 −3.08%、胜率 0%），2020 年最好（T+5 +2.64%、胜率 100%）。与"全部交易日"基线对照，T+20 胜率 66% vs 基线 ~52%、均值 3.05% vs ~1%——突破信号的增量主要在中长周期。
    </div>
  </div>

  <div class="panel">
    <h2>② 全史 K 线 · 突破标记（橙三角 = 每次横盘突破，点击切换标的）</h2>
    <div class="kline-switch">
      <button class="kbtn active" data-t="GILD">GILD 吉利德</button>
      <button class="kbtn" data-t="ABBV">ABBV 艾伯维</button>
    </div>
    <div id="chart_overview" style="width:100%;height:520px;"></div>
    <div class="note">K 线红涨绿跌；橙色三角（▼）标记每笔横盘突破的突破日 K 线。滚动条可缩放查看历史。</div>
  </div>

  <div class="panel">
    <h2>③ 每笔突破 · 局部 K 线（突破前 20 日 → 突破后 20 日）</h2>
    <div class="gallery" id="gallery"></div>
    <div class="note">每张图：K 线 + 上方蓝色虚线为当日 Donchian 上沿（突破参照线）。<b>浅蓝矩形阴影 = 该突破所对应的横盘区间</b>（突破前 60 日窗口内、确认了上下沿各 ≥2 次触及的那段箱体）；<b>橙色三角</b>与横轴日期加粗标出突破 K 线（收盘有效上穿上沿且当日涨幅 ≥2.5%）。右上角标注该笔 T+1 / T+5 / T+20 收益。</div>
  </div>

  <div class="panel">
    <h2>④ 统计表</h2>
    <h3 style="font-size:14px;">全部突破 · 分标的 × 持有期</h3>
    <table>
      <tr><th>分组</th><th>样本</th><th>平均</th><th>中位</th><th>胜率</th><th>P25 / P75</th></tr>
      """ + rows_pooled + """
    </table>
    <div class="note">胜率 = 收益 &gt; 0 的占比（%）。T+N 收益按复权价（含分红再投价格调整）计算，与看盘软件的"未复权价"在长周期上略有差异，但短周期（T+1/T+5）几乎一致。</div>

    <h3 style="font-size:14px;margin-top:16px;">分年（全部突破合并）</h3>
    <div class="scroll">
    <table>
      <tr><th>年份</th><th>样本</th><th>T+1 平均</th><th>T+5 平均</th><th>T+20 平均</th></tr>
      """ + rows_year + """
    </table>
    </div>

    <h3 style="font-size:14px;margin-top:16px;">基线对照（该标的全部交易日的无条件 T+N）</h3>
    <table>
      <tr><th>分组</th><th>样本</th><th>平均</th><th>中位</th><th>胜率</th><th>P25 / P75</th></tr>
      """ + rows_base + """
    </table>
    <div class="note">基线 = 不筛选任何信号、任意交易日起持有 N 日的平均表现，用于衡量突破信号的"增量"。</div>
  </div>

  <div class="panel">
    <h2>⑤ 每笔突破明细</h2>
    <div class="scroll">
    <table>
      <tr><th>标的</th><th>突破日</th><th>收盘价</th><th>当日涨幅</th><th>上沿</th><th>下沿</th><th>T+1</th><th>T+5</th><th>T+20</th></tr>
      """ + detail_rows_html + """
    </table>
    </div>
  </div>

  <div class="panel">
    <h2>数据口径与局限</h2>
    <ul>
      <li><b>数据</b>：Yahoo Finance 日线（本机 Chrome 拉取），GILD / ABBV 均 2015-01-02 ~ 2026-08-14，含 open/high/low/close/adj_close。收益一律用 adj_close 复权口径，突破判断用未复权 close。</li>
      <li><b>横盘区间</b>：Donchian 通道 N=20，上沿 = 近 20 日 high 最大值（取昨日并 shift(1)，避免未来函数），下沿 = 近 20 日 low 最小值。突破前 60 个交易日需同时满足：① 触及上沿带（high ≥ 97.5% 上沿）≥ 2 次；② 触及下沿带（low ≤ 102.5% 下沿）≥ 2 次；③ 带宽比 = 上沿/下沿−1 ∈ [5%, 25%]（5% 以下太窄无交易价值，25% 以上视为趋势而非横盘）。</li>
      <li><b>突破</b>：close[t−1] ≤ 上沿[t−1] 且 close[t] &gt; 上沿[t−1]（收盘价有效上穿，排除上影线诱多）；当日涨幅 ≥ 2.5%（未复权 close，与看盘软件一致）。相邻突破 30 交易日内合并为一次（取首次），避免同一波强势重复计数。</li>
      <li><b>收益</b>：T+N = 突破日复权收盘 → N 个交易日后复权收盘的涨跌幅（%），N∈{1,5,20}；数据末段（近 20 日）的突破无完整远期收益，标注 "—"。</li>
      <li><b>局限</b>：样本 50 笔（GILD 23 / ABBV 27），分年后每年仅 2~7 笔，统计意义有限；未区分财报/市场整体环境（如 2016-11-09 特朗普当选日 GILD 单日 +5.98% 属事件驱动而非纯技术突破）；阈值（N=20、2.5%、2 次触及等）为固定设定，不同参数结果会变。</li>
    </ul>
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
var RED = '#d23b2e', GREEN = '#1a9e4b';
var N = {"GILD":"GILD 吉利德","ABBV":"ABBV 艾伯维"};

// ② 全史 K 线总览
(function(){
  var cur = 'GILD';
  var chart = echarts.init(document.getElementById('chart_overview'));
  function render(t){
    var k = DATA.allk[t];
    var evs = DATA.events.filter(function(e){ return e.ticker === t; });
    var idxOf = {};
    k.dates.forEach(function(d,i){ idxOf[d] = i; });
    chart.setOption({
      animation:false,
      axisPointer:{ link:[{xAxisIndex:'all'}] },
      tooltip:{ trigger:'axis', axisPointer:{type:'cross'} },
      legend:{ data:['日K'], top:0 },
      grid:{ left:58, right:22, top:30, height:'82%' },
      xAxis:{ type:'category', data:k.dates, gridIndex:0, axisLabel:{fontSize:10, interval:'auto'} },
      yAxis:{ scale:true, gridIndex:0, splitLine:{ lineStyle:{color:'#eef0f3'} } },
      dataZoom:[
        { type:'inside', xAxisIndex:0, start:60 },
        { type:'slider', xAxisIndex:0, start:60, height:18, bottom:2 }
      ],
      series:[{
        name:'日K', type:'candlestick', data:k.ohlc,
        itemStyle:{ color:RED, color0:GREEN, borderColor:RED, borderColor0:GREEN },
        markPoint:{
          symbol:'triangle', symbolSize:14, symbolOffset:[0,-30],
          label:{ show:true, fontSize:9, fontWeight:'bold', color:'#b25a00', position:'top' },
          data: evs.map(function(e){
            return { coord:[idxOf[e.date], e.close], value:'↑'+e.gain.toFixed(1)+'%',
                     itemStyle:{ color:'#e67e22' } };
          })
        }
      }]
    }, true);
  }
  render('GILD');
  document.querySelectorAll('.kbtn').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.kbtn').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      render(btn.dataset.t);
    });
  });
})();

// ③ 每笔突破局部 K 线缩略图
(function(){
  var gal = document.getElementById('gallery');
  DATA.tickers.forEach(function(t){
    DATA.locals[t].forEach(function(ev, i){
      var div = document.createElement('div');
      div.className = 'fig';
      var cid = 'k_' + t + '_' + i;
      div.style.height = '340px';
      div.innerHTML = '<div id="' + cid + '" style="width:100%;height:280px;"></div>' +
        '<div class="cap"><b>' + ev.brk_date + '</b> · ' + N[t] + ' 突破' +
        ' <span class="up">▲</span><span style="font-size:12px;color:#555;">T+1</span> ' +
        (ev.t ? '' : '') + '</div>';
      gal.appendChild(div);
      var chart = echarts.init(document.getElementById(cid));
      chart.setOption({
        animation:false,
        axisPointer:{ link:[{xAxisIndex:'all'}] },
        tooltip:{ trigger:'axis', axisPointer:{type:'cross'} },
        grid:{ left:50, right:20, top:28, height:'72%' },
        xAxis:{ type:'category', data:ev.dates, gridIndex:0,
                axisLabel:{ fontSize:9, interval: Math.floor(ev.dates.length/6) } },
        yAxis:{ scale:true, gridIndex:0, splitLine:{ lineStyle:{color:'#eef0f3'} } },
        series:[{
          name:'日K', type:'candlestick', data:ev.ohlc,
          itemStyle:{ color:RED, color0:GREEN, borderColor:RED, borderColor0:GREEN },
          markLine:{
            silent:true, symbol:'none',
            label:{ show:false },
            lineStyle:{ color:'#56B4E9', type:'dashed', width:1 },
            data:[{ yAxis: ev.upper[ev.brk_idx] }]
          },
          markArea:{
            silent:true,
            itemStyle:{ color:'rgba(86,180,233,0.16)', borderColor:'#2f80b8', borderWidth:1 },
            label:{ show:true, fontSize:10, color:'#1f5c8a', position:'insideTop', formatter:'横盘区间' },
            data: ev.box ? [[
                { xAxis: ev.box.xL, yAxis: ev.box.box_hi },
                { xAxis: ev.box.xR, yAxis: ev.box.box_lo }
            ]] : []
          },
          markPoint:{
            symbol:'triangle', symbolSize:13, symbolOffset:[0,-28],
            label:{ show:true, fontSize:10, fontWeight:'bold', color:'#b25a00', position:'top' },
            data:[{ coord:[ev.brk_idx, ev.ohlc[ev.brk_idx][2]], value:'突破', itemStyle:{ color:'#e67e22' } }]
          }
        }]
      });
    });
  });
})();
</script>
</body>
</html>
"""
    html = html.replace('__DATA_JSON__', data_json)
    out = os.path.join(REPORT_DIR, "gild_abbv_breakout_report.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("written:", out)


if __name__ == "__main__":
    main()