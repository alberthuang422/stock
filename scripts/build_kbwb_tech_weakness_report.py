# -*- coding: utf-8 -*-
"""银行走弱 → 科技股表现 报告生成器（读 results/kbwb_tech_weakness.json）
规范：普通三引号模板 + @@PLACEH@@ 占位符 replace（避免 f-string 与 JS 花括号冲突）
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "14_kbwb科技弱势")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "kbwb_tech_weakness.json"), encoding="utf-8") as f:
    D = json.load(f)

SC = D["signal_counts"]
CUR = D["current"]
SR = D["kbwb_state_ret"]
meta = D["meta"]


def js(o):
    return json.dumps(o, ensure_ascii=False, default=str)


def fmt(v, nd=2, sign=False):
    if v is None:
        return "—"
    s = f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"
    return s


def ev_row(sig, t, scope="full"):
    e = D["event_study"][sig][scope][t]
    b = D["baseline_fwd"][t]
    if not e["n"]:
        return None
    cells = []
    for h in (5, 10, 20):
        m, w = e[str(h)]["mean"], e[str(h)]["win"]
        bm = b[str(h)]["mean"]
        diff = m - bm
        cls = "up" if m > 0 else "dn"
        cells.append(f'<td class="{cls}">{m:+.2f}% <span class="sub">({w:.0f}%)</span></td>')
        cells.append(f'<td class="sub2">{diff:+.2f}</td>')
    return cells, e["n"]


# ---- KPI ----
kpis = f"""
    <div class="kpis">
      <div class="kpi"><div class="num">{SC['weak_any_pct']:.0f}%</div><div class="lab">KBWB 处于走弱状态的天数占比（全期）</div></div>
      <div class="kpi"><div class="num">{SC['ema_events']}</div><div class="lab">信号A · EMA20 跌破{D['params']['repair_days']}日未修复 事件数</div></div>
      <div class="kpi"><div class="num">{SC['trendline_events']}</div><div class="lab">信号B · 跌破上升趋势线 事件数</div></div>
      <div class="kpi"><div class="num">{CUR['ema_gap_pct']:+.1f}%</div><div class="lab">KBWB 现价 vs EMA20（{CUR['date']}）</div></div>
      <div class="kpi"><div class="num">{fmt(SR['weak_mean'],3,True)}</div><div class="lab">走弱状态 KBWB 日均收益 %（vs 正常 {fmt(SR['normal_mean'],3,True)}）</div></div>
    </div>"""

verdict = f"""
    <div class="verdict">
      <div class="t">核心结论</div>
      <div class="b">银行走弱<b>不是科技股的看空信号，而是一个"联动加剧"信号</b>。
        ① <span class="hlg">前瞻收益</span>：KBWB 跌破 EMA20 且多日未修复后，SOXX/XLK 的
        fwd20 均值 <span class="hlg">+2.81% / +2.02%</span>，<b>高于</b>全样本基线（+2.26% / +1.70%），
        胜率升至 66~70% —— 银行技术性走弱后科技股反而偏强。
        ② <span class="hlb">相关机制</span>：走弱期间 KBWB↔科技日收益相关显著抬升
        （EMA20 走弱：SOXX 0.45→<span class="hlb">0.71</span>、XLK 0.46→<span class="hlb">0.76</span>），
        科技股被拉入银行主导的同向波动；但<b>结构性跌破趋势线</b>时相关性反而<b>回落</b>
        （SOXX 0.56→0.40），科技脱钩走独立行情。
        ③ <span class="hl">当前状态</span>：{CUR['date']} KBWB 已跌破 EMA20（{CUR['below_ema_days']} 日），
        且<span class="hl">趋势线走弱信号已触发</span> —— 银行处于走弱状态，科技股短期与银行同向波动概率上升。
      </div>
    </div>"""

# ---- 信号方法论 ----
P = D["params"]
method_html = f"""
    <div class="sig-grid">
      <div class="sig">
        <div class="sig-t"><span class="tag ema">信号A</span> EMA20 跌破且多日未修复</div>
        <ul>
          <li>KBWB 收盘跌破 <b>EMA{P['ema_n']}</b>；</li>
          <li>且连续 <b>{P['repair_days']} 个交易日</b>收盘都留在 EMA20 下方 → 走弱确认；</li>
          <li>收盘回到 EMA20 上方视为修复，状态结束。</li>
          <li>刻画「短期动能破位且无法快速收复」。</li>
        </ul>
      </div>
      <div class="sig">
        <div class="sig-t"><span class="tag tl">信号B</span> 跌破上升趋势线</div>
        <ul>
          <li>近 <b>{P['trend_win']} 日</b>内取最近 2~4 个依次抬升的 swing low（分形，左右各 3 根）；</li>
          <li>OLS 拟合，要求斜率 &gt; 0 且 R² ≥ {P['trend_r2']} → 有效上升趋势线；</li>
          <li>收盘自上方<b>下穿</b>趋势线 → 走弱事件（{P['trend_cooldown']} 日冷却去重）。</li>
          <li>刻画「中期结构破位」，比信号A更罕见、更重。</li>
        </ul>
      </div>
    </div>"""

# ---- 当前状态 ----
cur_active = CUR["trend_weak_active"] or CUR["ema_weak_active"]
cur_state = "走弱状态" if cur_active else "正常状态"
cur_badge = f'<span class="badge {"warn" if cur_active else "ok"}">{cur_state}</span>'
current_html = f"""
    <div class="curbox">
      <div class="cur-item"><div class="lab">交易日</div><div class="val">{CUR['date']}</div></div>
      <div class="cur-item"><div class="lab">KBWB 收盘</div><div class="val">{CUR['close']:.2f}</div></div>
      <div class="cur-item"><div class="lab">EMA20</div><div class="val">{CUR['ema20']:.2f}</div></div>
      <div class="cur-item"><div class="lab">距 EMA20</div><div class="val dn">{CUR['ema_gap_pct']:+.2f}%</div></div>
      <div class="cur-item"><div class="lab">连续跌破 EMA20</div><div class="val">{CUR['below_ema_days']} 日</div></div>
      <div class="cur-item"><div class="lab">EMA20 走弱确认</div><div class="val">{'已触发' if CUR['ema_weak_active'] else '未触发（需 5 日）'}</div></div>
      <div class="cur-item"><div class="lab">趋势线走弱</div><div class="val {'dn' if CUR['trend_weak_active'] else ''}">{'已触发' if CUR['trend_weak_active'] else '未触发'}</div></div>
      <div class="cur-item"><div class="lab">综合判定</div><div class="val">{cur_badge}</div></div>
    </div>
    <div class="note">最近一次 EMA20 走弱确认：<b>{CUR['last_ema_event']}</b>。当前趋势线走弱信号已生效，若 KBWB 收盘继续停留在 EMA20 下方达 5 日，则 EMA20 走弱信号也将叠加确认。</div>"""

# ---- 事件研究表（信号A，full 为主） ----
ev_rows = ""
for t in ("SOXX", "XLK"):
    for sig, siglab in (("ema", "EMA20走弱"), ("trendline", "跌破趋势线")):
        r = ev_row(sig, t, "full")
        if r is None:
            ev_rows += f'<tr><td><span class="tag {"ema" if sig=="ema" else "tl"}">{siglab}</span></td><td>{t}</td><td class="na">0</td><td colspan="6" class="na">样本不足</td></tr>'
            continue
        cells, n = r
        ev_rows += (f'<tr><td><span class="tag {"ema" if sig=="ema" else "tl"}">{siglab}</span></td>'
                    f'<td>{t}</td><td>{n}</td>' + "".join(cells) + "</tr>")

# 基线行
base_rows = ""
for t in ("SOXX", "XLK"):
    b = D["baseline_fwd"][t]
    base_rows += (f'<tr class="baserow"><td><span class="tag base">基线</span></td><td>{t}</td><td>{b["5"]["n"]:,}</td>'
                  f'<td>{b["5"]["mean"]:+.2f}%</td><td class="sub2">—</td>'
                  f'<td>{b["10"]["mean"]:+.2f}%</td><td class="sub2">—</td>'
                  f'<td>{b["20"]["mean"]:+.2f}%</td><td class="sub2">—</td></tr>')

# ---- 状态条件相关表 ----
reg_rows = ""
for sig, siglab in (("ema", "EMA20走弱"), ("trendline", "跌破趋势线"), ("any", "任一信号合并")):
    for t in ("SOXX", "XLK"):
        r = D["regime_corr"][sig]["full"][t]
        if not (r.get("weak") and r.get("normal")):
            reg_rows += f'<tr><td>{siglab}</td><td>{t}</td><td class="na" colspan="6">样本不足</td></tr>'
            continue
        wk, nm = r["weak"], r["normal"]
        dcorr = wk["corr"] - nm["corr"]
        dcls = "up" if dcorr > 0 else "dn"
        reg_rows += (f'<tr><td>{siglab}</td><td>{t}</td>'
                     f'<td class="hlb">{wk["corr"]:+.3f}</td><td class="sub2">n={wk["n"]}</td>'
                     f'<td>{nm["corr"]:+.3f}</td><td class="sub2">n={nm["n"]}</td>'
                     f'<td class="{dcls}">{dcorr:+.3f}</td>'
                     f'<td class="{"dn" if wk["tech_mean_ret"]<0 else "up"}">{wk["tech_mean_ret"]:+.3f}%</td></tr>')

# ---- 近 2 年走弱事件清单 ----
ev_list_rows = ""
for e in D["event_list_recent"]:
    sigcls = "ema" if "EMA" in e["signal"] else "tl"
    f10 = e.get("kbwb_f10")
    ev_list_rows += (f'<tr><td>{e["date"]}</td><td><span class="tag {sigcls}">{e["signal"]}</span></td>'
                     f'<td class="{"up" if (f10 or 0)>0 else "dn"}">{fmt(f10,1,True)}%</td></tr>')

html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>银行走弱 → 科技股表现 · KBWB vs SOXX/XLK 条件相关性分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#d23b2e;--green:#1a9e4b;--blue:#1f4e79;--orange:#e67e22;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:22px;font-weight:700;}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .verdict{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:15px;font-weight:600;line-height:1.85;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  td.sub2{color:var(--sub);font-size:11px;} span.sub{color:var(--sub);font-weight:400;font-size:11px;}
  tr.baserow td{background:#fafbfc;color:var(--sub);}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .chart.sm{height:330px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .warnbox{background:#fdf3f2;border:1px solid #f3c9c4;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#6e2018;margin-top:10px;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);}
  .tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .tag.ema{background:#e8eef6;color:var(--blue);} .tag.tl{background:#fdeee0;color:#c05c0b;} .tag.base{background:#eef0f2;color:#8a9099;}
  .sig-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px;}
  .sig{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:14px 16px;}
  .sig-t{font-weight:700;font-size:13.5px;margin-bottom:8px;}
  .sig ul{margin-left:18px;} .sig li{font-size:12.5px;color:#3a4048;margin:3px 0;}
  .curbox{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:10px;margin:6px 0 10px;}
  .cur-item{background:#fbfcfe;border:1px solid var(--line);border-radius:9px;padding:9px 12px;}
  .cur-item .lab{color:var(--sub);font-size:11px;} .cur-item .val{font-size:16px;font-weight:700;margin-top:2px;}
  .badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:700;}
  .badge.warn{background:#fdecea;color:var(--red);} .badge.ok{background:#e8f5ee;color:var(--green);}
  @media(max-width:720px){.sig-grid{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>银行走弱 → 科技股表现 · 条件相关性分析</h1>
    <div class="meta">@@META@@</div>
    @@KPIS@@
    @@VERDICT@@
  </div>

  <div class="card">
    <h2>① 走弱信号定义（KBWB）</h2>
    @@METHOD@@
  </div>

  <div class="card">
    <h2>② 当前状态快照</h2>
    @@CURRENT@@
  </div>

  <div class="card">
    <h2>③ KBWB 近 3 年走势 · EMA20 与走弱区间</h2>
    <div class="chart" id="ch_price"></div>
    <div class="note">红色阴影 = 走弱状态区间（任一信号触发）。可直观看到走弱多发生在回调/盘整段；2026-07 末趋势线走弱再度触发（图右端）。</div>
  </div>

  <div class="card">
    <h2>④ 事件研究 · 走弱信号后科技股前瞻收益</h2>
    <div class="chart sm" id="ch_ev"></div>
    <div class="scroll">
    <table>
      <tr><th>走弱信号</th><th>科技标的</th><th>事件数 n</th><th>fwd5 均值(胜率)</th><th>Δ基线</th><th>fwd10 均值(胜率)</th><th>Δ基线</th><th>fwd20 均值(胜率)</th><th>Δ基线</th></tr>
      @@EV_ROWS@@
      @@BASE_ROWS@@
    </table>
    </div>
    <div class="keypoint"><b>关键发现：</b>银行跌破 EMA20 且多日未修复后，SOXX/XLK 的 fwd20 均值（+2.81% / +2.02%）<b>高于</b>全样本基线（+2.26% / +1.70%），胜率升至 66~70%。银行技术性走弱<b>并不预示科技股下跌</b>——信号确认日往往已是回调中后段，其后科技股偏强，更像「轮动/错杀修复」而非「系统性风险传导」。跌破趋势线（结构性破位）样本仅 5 例：fwd5 科技股小幅走弱（SOXX −1.02%、胜率 25%），但 fwd10/20 转正。</div>
  </div>

  <div class="card">
    <h2>⑤ 状态条件相关 · 走弱期 vs 正常期 KBWB↔科技</h2>
    <div class="chart sm" id="ch_reg"></div>
    <div class="scroll">
    <table>
      <tr><th>走弱口径</th><th>科技标的</th><th>走弱期相关</th><th>走弱样本 n</th><th>正常期相关</th><th>正常样本 n</th><th>Δ相关</th><th>走弱期科技日均</th></tr>
      @@REG_ROWS@@
    </table>
    </div>
    <div class="keypoint"><b>机制解读：</b>走弱期间科技股与银行的日收益相关性<b>显著抬升</b>（EMA20 走弱：SOXX 0.45→<b>0.71</b>、XLK 0.46→<b>0.76</b>），说明银行走弱时科技股更容易被拉入同向波动（联动/传染）。但<b>结构性跌破趋势线</b>时相关性反而<b>下降</b>（SOXX 0.56→0.40、XLK 0.60→0.39），科技脱钩走独立行情。走弱期科技日均收益趋近于零（SOXX +0.006%），明显低于正常期（+0.17%）——银行走弱阶段科技股<b>失去日常上行动能</b>。</div>
  </div>

  <div class="card">
    <h2>⑥ 近 2 年走弱事件清单</h2>
    <div class="scroll">
    <table>
      <tr><th>确认日期</th><th>信号类型</th><th>KBWB 后 10 日收益</th></tr>
      @@EV_LIST_ROWS@@
    </table>
    </div>
    <div class="note">列示 2024-08 以来的走弱确认事件及其后 KBWB 自身 10 日表现，供对照当前信号位置。Δ收益为银行自身走势，非科技股。</div>
  </div>

  <div class="card">
    <h2>⑦ 方法口径与局限</h2>
    <ul>
      <li><b>数据</b>：Yahoo Finance 日线复权收盘价（adj_close）；统一窗口 @@WIN_START@@ ~ @@WIN_END@@（共 @@N@@ 个交易日，取 KBWB/SOXX/XLK 三者交集）。</li>
      <li><b>信号A</b>：收盘跌破 EMA@@EMA_N@@ 且连续 @@REPAIR@@ 日未收复 → 走弱确认；回到线上方即修复。</li>
      <li><b>信号B</b>：近 @@TREND_WIN@@ 日 2~4 个依次抬升 swing low（分形）OLS 拟合（斜率&gt;0、R²≥@@TREND_R2@@），收盘自上而下穿越 → 走弱事件（@@TREND_CD@@ 日冷却）。</li>
      <li><b>前瞻收益</b>：以信号确认日为 T0，统计科技标的 T+1/5/10/20 复权价收益，并与全样本同周期基线对比；收益口径为 100% 正常收益，未扣交易成本。</li>
      <li><b>状态相关</b>：走弱/正常两种状态下分别计算 KBWB↔科技日收益 Pearson 相关，要求单状态样本 ≥ 15。</li>
      <li><b>局限</b>：KBWB 为等权银行 ETF，SOXX/XLK 为行业 ETF，度量的是「板块 vs 板块」联动而非个股；信号B 样本量小（n=5），结论稳健性有限；相关性抬升可能部分由共同市场因子（利率、风险偏好）驱动，非纯银行→科技因果；未控制宏观变量。</li>
    </ul>
  </div>

  <div class="card dis">
    <div style="font-weight:600;margin-bottom:6px;">免责声明</div>
    本报告仅为数据分析参考，不构成任何投资建议。历史统计不代表未来表现，所有结论基于历史样本，存在区间依赖与小样本不确定性。
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
RED = "#d23b2e"; GREEN = "#1a9e4b"; ORANGE = "#e67e22"; BLUE = "#1f4e79"; GRAY = "#999";

// 走弱区间提取（供 markArea）
function weakAreas(chart){
  var areas = [], start = null;
  for (var i=0;i<chart.length;i++){
    if (chart[i].weak && start===null) start = chart[i].date;
    if ((!chart[i].weak || i===chart.length-1) && start!==null){
      var end = chart[i].weak ? chart[i].date : chart[Math.max(0,i-1)].date;
      areas.push([{xAxis:start},{xAxis:end}]);
      start = null;
    }
  }
  return areas;
}

// 图③ KBWB 价格 + EMA20 + 走弱阴影
(function(){
  var ch = echarts.init(document.getElementById("ch_price"));
  var d = DATA.chart;
  ch.setOption({
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":Number(v).toFixed(2)); } },
    legend:{ data:["KBWB 收盘","EMA20"], top:0 },
    grid:{ left:60, right:30, top:40, bottom:50 },
    xAxis:{ type:"category", data:d.map(function(x){return x.date;}), axisLabel:{ fontSize:10, interval: Math.floor(d.length/8) } },
    yAxis:{ type:"value", name:"价格", scale:true },
    dataZoom:[{ type:"inside", start:0, end:100 },{ type:"slider", height:16, bottom:8 }],
    series:[
      { name:"KBWB 收盘", type:"line", data:d.map(function(x){return x.close;}), showSymbol:false,
        lineStyle:{ color:BLUE, width:1.6 }, itemStyle:{ color:BLUE },
        markArea:{ silent:true, itemStyle:{ color:"rgba(210,59,46,0.10)" }, data:weakAreas(d) } },
      { name:"EMA20", type:"line", data:d.map(function(x){return x.ema;}), showSymbol:false,
        lineStyle:{ color:ORANGE, width:1.3, type:"dashed" }, itemStyle:{ color:ORANGE } }
    ]
  });
})();

// 图④ 事件研究 fwd20 vs 基线
(function(){
  var ch = echarts.init(document.getElementById("ch_ev"));
  var cats = [], sig = DATA.event_study.ema.full, base = DATA.baseline_fwd;
  var soxx = [base.SOXX["20"].mean, sig.SOXX["20"].mean, base.XLK["20"].mean, sig.XLK["20"].mean];
  var win  = [null, sig.SOXX["20"].win, null, sig.XLK["20"].win];
  cats = ["SOXX 基线","SOXX 走弱后","XLK 基线","XLK 走弱后"];
  ch.setOption({
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"},
      formatter:function(ps){ var p=ps[0]; var w=win[p.dataIndex]; return p.name + "<br>fwd20 均值: " + (p.value==null?"-":p.value.toFixed(2)+"%") + (w!=null?"<br>胜率: "+w.toFixed(0)+"%":""); } },
    grid:{ left:60, right:30, top:40, bottom:40 },
    xAxis:{ type:"category", data:cats, axisLabel:{ fontSize:11 } },
    yAxis:{ type:"value", name:"fwd20 均值 %", axisLabel:{ formatter:function(v){return v.toFixed(1);} } },
    series:[{ name:"fwd20", type:"bar", barWidth:"46%",
      data:soxx.map(function(v,i){ return { value:v, itemStyle:{ color:(i%2===1)?RED:"#c9ccd2" } }; }),
      label:{ show:true, position:"top", formatter:function(p){ return (p.value==null?"":p.value.toFixed(2)+"%"); }, fontSize:11 } }]
  });
})();

// 图⑤ 状态相关：走弱 vs 正常（EMA20 口径）
(function(){
  var ch = echarts.init(document.getElementById("ch_reg"));
  var r = DATA.regime_corr.ema.full;
  var cats = ["SOXX 走弱期","SOXX 正常期","XLK 走弱期","XLK 正常期"];
  var vals = [r.SOXX.weak.corr, r.SOXX.normal.corr, r.XLK.weak.corr, r.XLK.normal.corr];
  ch.setOption({
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"}, valueFormatter:function(v){ return (v==null?"-":Number(v).toFixed(3)); } },
    grid:{ left:60, right:30, top:40, bottom:40 },
    xAxis:{ type:"category", data:cats, axisLabel:{ fontSize:11 } },
    yAxis:{ type:"value", name:"日收益相关", min:0, max:1, axisLabel:{ formatter:function(v){return v.toFixed(2);} } },
    series:[{ name:"相关", type:"bar", barWidth:"46%",
      data:vals.map(function(v,i){ return { value:v, itemStyle:{ color:(i%2===0)?BLUE:"#c9ccd2" } }; }),
      label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(3); }, fontSize:11 } }]
  });
})();
</script>
</body>
</html>
"""

repl = {
    "@@META@@": (f'{meta["kbwb"]}（银行指数代理）→ 科技：SOXX / XLK · '
                 f'分析窗口 {D["period"]["start"]} ~ {D["period"]["end"]}（共 {D["period"]["n"]:,} 个交易日）· '
                 f'{meta["source"]} · 生成 {meta["fetched"]}'),
    "@@KPIS@@": kpis,
    "@@VERDICT@@": verdict,
    "@@METHOD@@": method_html,
    "@@CURRENT@@": current_html,
    "@@EV_ROWS@@": ev_rows,
    "@@BASE_ROWS@@": base_rows,
    "@@REG_ROWS@@": reg_rows,
    "@@EV_LIST_ROWS@@": ev_list_rows,
    "@@WIN_START@@": D["period"]["start"],
    "@@WIN_END@@": D["period"]["end"],
    "@@N@@": f'{D["period"]["n"]:,}',
    "@@EMA_N@@": str(P["ema_n"]),
    "@@REPAIR@@": str(P["repair_days"]),
    "@@TREND_WIN@@": str(P["trend_win"]),
    "@@TREND_R2@@": str(P["trend_r2"]),
    "@@TREND_CD@@": str(P["trend_cooldown"]),
}
for k, v in repl.items():
    html = html.replace(k, v)
html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + js(D) + ";")

out_path = os.path.join(OUT_DIR, "kbwb_tech_weakness_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={os.path.getsize(out_path)}")
