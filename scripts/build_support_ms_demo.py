# -*- coding: utf-8 -*-
"""支撑/阻力识别 demo — HTML 可视化（MS 近90个交易日 K 线 + 识别出的支撑/阻力水平 + 触及标记）"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "..", "results", "support_ms_demo.json"), encoding="utf-8") as f:
    D = json.load(f)

def js(o):
    return json.dumps(o, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>支撑/阻力位 AI 识别 demo · MS</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#d23b2e;--green:#1a9e4b;--blue:#1f4e79;--orange:#e67e22;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1180px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 4px;padding-left:10px;border-left:4px solid var(--blue);}
  .note{color:var(--sub);font-size:12px;margin:6px 0 12px;}
  .chart{width:100%;height:560px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:10px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;}
  .sup{color:#0aa06e;font-weight:700;} .res{color:#d23b2e;font-weight:700;}
  .badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .b-sup{background:#e6f4ee;color:#0aa06e;} .b-res{background:#fdeaea;color:#d23b2e;}
  .broken{color:#999;text-decoration:line-through;}
  .hl{font-weight:700;color:var(--blue);}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>支撑/阻力位 AI 识别 demo — Morgan Stanley (MS)</h1>
    <div class="meta">窗口 @@WINDOW@@ （@@N@@ 个交易日）· 现价 <b>@@LAST@@</b> · 聚类容差 ±@@TOL@@%（基于 ATR14 中位）</div>
    <h2>① 近 90 个交易日 K 线 + 识别出的水平</h2>
    <div class="note"><span class="badge b-sup">支撑</span> 绿色实线（触击后反弹）　<span class="badge b-res">阻力</span> 红色虚线（触击后回落）· 每条线标注触击次数与最近触击日</div>
    <div class="chart" id="ch_k"></div>
  </div>

  <div class="card">
    <h2>② 支撑位明细（近 18 个月，按重要性评分排序）</h2>
    <div class="note">评分 = 触击次数 ^1.2 × 触击后 5 日反弹中位 × 时间存活度。破位线（▲下方价格曾收盘穿透）标灰删划线。</div>
    <table>
      <tr><th>#</th><th>类型</th><th>水平（带）</th><th>触击次数</th><th>触击后5日反弹中位</th><th>首次/最后触击</th><th>存活天数</th><th>状态</th><th>评分</th></tr>
      @@ROWS@@
    </table>
  </div>

  <div class="card">
    <h2>③ 支撑有效性验证（近 18 个月）</h2>
    <div class="note">用统计回答问题："触击支撑位后真的更容易反弹吗？"</div>
    <table>
      <tr><th>口径</th><th>数值</th></tr>
      <tr><td>swing low 触击后 5 个交易日反弹中位（41 次触击）</td><td class="hl">@@TOUCH_MED@@</td></tr>
      <tr><td>对照：任意交易日 5 日收益中位（全窗口随机）</td><td>@@RAND_MED@@</td></tr>
      <tr><td>触击后 5 日出现更高价的胜率</td><td class="hl">@@WIN@@</td></tr>
    </table>
    <div class="note" style="color:#7c4a03;margin-top:8px">⚠ 注意：对照组是无条件基准，存在 up-bias（上升趋势中支撑位天然更有效）；更严格的检验需对照"同样位置但非 swing low 的随机点"，此处仅作演示示意。</div>
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
RED = "#d23b2e"; GREEN = "#0aa06e"; BLUE = "#1f4e79"; ORANGE = "#e67e22";

// ① K线 + 水平线
(function(){
  var ch = echarts.init(document.getElementById("ch_k"));
  var c = DATA.chart;
  var ohlc = c.open.map(function(o,i){ return [o, c.close[i], c.low[i], c.high[i]]; });
  // 支撑/阻力 markLine
  var supLines = DATA.supports.filter(function(l){ return !l.broken; }).slice(0,6).map(function(l){
    return { yAxis: l.price, lineStyle:{ color:GREEN, width:1.4 },
             label:{ formatter: "支撑 " + l.price.toFixed(0) + " · " + l.touches + "触", fontSize:9, color:GREEN, position:"insideEndTop" } };
  });
  var resLines = DATA.resists.filter(function(l){ return !l.broken; }).slice(0,6).map(function(l){
    return { yAxis: l.price, lineStyle:{ color:RED, width:1.4, type:"dashed" },
             label:{ formatter: "阻力 " + l.price.toFixed(0) + " · " + l.touches + "触", fontSize:9, color:RED, position:"insideEndBottom" } };
  });
  var marks = supLines.concat(resLines);
  ch.setOption({
    animation:false,
    tooltip:{ trigger:"axis", axisPointer:{ type:"cross" },
      formatter:function(ps){
        var p = ps[0]; var i = p.dataIndex;
        return c.dates[i] + "<br>O " + c.open[i] + "　H " + c.high[i] + "<br>L " + c.low[i] + "　C " + c.close[i];
      } },
    grid:{ left:60, right:20, top:30, bottom:45 },
    xAxis:{ type:"category", data:c.dates, axisLabel:{ fontSize:10, interval:9 } },
    yAxis:{ type:"value", scale:true, name:"价格" },
    dataZoom:[{ type:"inside", start:0, end:100 }],
    series:[{
      type:"candlestick", data:ohlc,
      itemStyle:{ color:RED, color0:GREEN, borderColor:RED, borderColor0:GREEN },
      markLine:{ silent:true, symbol:"none", data:marks }
    }]
  });
})();

// ② 明细表由 Python 端生成（@@ROWS@@）
</script>
</body>
</html>
"""

# 行生成
rows = ""
for r in (D["supports"] + D["resists"])[:14]:
    cls = "sup" if r["kind"] == "支撑" else "res"
    badge = "b-sup" if r["kind"] == "支撑" else "b-res"
    status_cell = f'<span class="badge {badge}">{r["kind"]}</span>'
    if r["broken"]:
        st = '<span class="broken">已破位/突破</span>'
    else:
        st = '<span class="badge b-sup" style="background:#e6f4ee;color:#0aa06e">有效</span>'
    rows += (f'<tr><td>#{r["rank"]}</td><td>{status_cell}</td>'
             f'<td class="{cls}">{r["price"]:.2f} <span style="color:#999;font-weight:400">({r["band_lo"]:.0f}~{r["band_hi"]:.0f})</span></td>'
             f'<td>{r["touches"]}</td><td class="{cls}">{"+" if r["react_med"]>0 else ""}{r["react_med"]:.2f}%</td>'
             f'<td>{r["first_touch"]} → {r["last_touch"]}</td><td>{r["days_live"]}</td><td>{st}</td><td>{r["score"]}</td></tr>')

repl = {
    "@@WINDOW@@": f'{D["window"]["start"]} ~ {D["window"]["end"]}',
    "@@N@@": str(D["window"]["n"]),
    "@@LAST@@": f'{D["window"]["last_close"]:.2f}',
    "@@TOL@@": f'{abs(D["window"]["tol"])/D["window"]["last_close"]*100:.1f}',
    "@@ROWS@@": rows,
    "@@TOUCH_MED@@": f'{D["validity"]["touch_med_5d_high"]:+.2f}%',
    "@@RAND_MED@@": f'{D["validity"]["random_med_5d_close"]:+.2f}%',
    "@@WIN@@": f'{D["validity"]["touch_win_rate"]:.1f}%',
}
for k, v in repl.items():
    html = html.replace(k, v)
html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + js(D) + ";")

out_dir = os.path.join(BASE, "..", "reports", "13_kbwb支撑位")
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, "support_levels_ms_demo.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {path} size={os.path.getsize(path)}")