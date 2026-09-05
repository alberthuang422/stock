# -*- coding: utf-8 -*-
"""80 号报告构建：小麦非商头寸暴增事件研究
读取 results/cot/wheat_surge_events_20260905.json 生成 reports/80_小麦COT非商暴增事件研究_20260905/index.html
风格对齐 79 号：浅底研报风 + Okabe-Ito + 红涨绿跌 + ECharts
"""
import json, os, html, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "reports", "80_小麦COT非商暴增事件研究_20260905")
os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.path.join(BASE, "results", "cot", "wheat_surge_events_20260905.json"), encoding="utf-8"))

WINDOWS = D["windows"]
groups = D["groups"]
base = D["base"]
thr = D["thresholds_summary"]

def pctstr(v, signed=True, nd=1):
    if v is None or (isinstance(v, float) and math.isnan(v)): return "—"
    s = f"{v*100:+.{nd}f}%" if signed else f"{v*100:.{nd}f}%"
    return s

def cls(v):
    if v is None: return ""
    if isinstance(v, float) and math.isnan(v): return ""
    return "pos" if v > 0 else ("neg" if v < 0 else "")

# ---- 分组统计关键口径表 ----
def group_row(g):
    r = [f"<td>{html.escape(g['label'])}</td><td class='ctr'>{g['n']}</td>"]
    for w in WINDOWS:
        s = g.get(f"fwd{w}", {})
        m = s.get("mean"); e = s.get("excess"); t = s.get("excess_t")
        if m is None or (isinstance(m, float) and math.isnan(m)):
            r.append("<td>—</td><td>—</td>"); continue
        tcell = ""
        if t is not None and not (isinstance(t, float) and math.isnan(t)):
            sig = " <span class='dim2'>"
            if abs(t) > 2.58: sig = " <span class='sig3'>"
            elif abs(t) > 1.96: sig = " <span class='sig2'>"
            tcell = f"{sig}(t={t:+.2f})</span>"
        r.append(f"<td class='{cls(m)}'>{pctstr(m)}</td>"
                 f"<td class='{cls(e)}'>{pctstr(e)}{tcell}</td>")
    return "<tr>" + "".join(r) + "</tr>"

rows_group_html = "".join(group_row(groups[k]) for k in
                          ["all_net", "net_multi", "net_cover", "net_start", "net_chase",
                           "net_keep", "net_revert", "long_surge_all", "short_cover_all"])

# 基线行
brow = ["<tr><td class='dim'>基线：2016+ 全样本周收益（非事件）</td><td class='ctr'>…</td>"]
for w in WINDOWS:
    b = base[f"fwd{w}"]
    brow.append(f"<td class='dim'>{pctstr(b['mean'])}</td><td class='dim'>基准</td>")
brow.append("</tr>")
baseline_html = "".join(brow)

# ---- 事件明细（小麦三合约合计，净多暴增，按日期倒序） ----
events_all = D["events"]
ev_net_total = [e for e in events_all if e["market"] == "小麦 三合约合计" and e["type"] == "net_surge"]
ev_net_total_sorted = sorted(ev_net_total, key=lambda x: x["date"])
def ev_row(e):
    share = e["share_long"]
    share_s = "—" if (share is None or (isinstance(share, float) and math.isnan(share))) else f"{share*100:.0f}%"
    share_c = cls(share - 0.5) if not (share is None or (isinstance(share, float) and math.isnan(share))) else ""
    ret = e["retention_4w"]
    ret_s = "—" if (ret is None or (isinstance(ret, float) and math.isnan(ret))) else f"{ret*100:.0f}%"
    cells = [f"<td>{e['date']}</td>", f"<td class='num'>{e['dnet']:,.0f}</td>",
             f"<td class='num'>{e['dlong']:,.0f}</td>", f"<td class='num'>{e['dshort']:,.0f}</td>",
             f"<td class='ctr {share_c}'>{share_s}</td>", f"<td class='ctr'>{e['cluster_len']}</td>",
             f"<td class='ctr'>{ret_s}</td>", f"<td class='num {cls(e['pre4'])}'>{pctstr(e['pre4'])}</td>"]
    for w in WINDOWS:
        v = e.get(f"fwd{w}")
        cells.append(f"<td class='num {cls(v)}'>{pctstr(v)}</td>")
    return "<tr>" + "".join(cells) + "</tr>"
ev_net_html = "".join(ev_row(e) for e in ev_net_total_sorted)

latest = [e for e in ev_net_total if e["date"] >= "2026-09-01"][0] if any(e["date"] >= "2026-09-01" for e in ev_net_total) else ev_net_total_sorted[-1]

# 事件-价格时间轴数据（ECharts）：小麦全样本周收益（基线）+ 暴增事件散点
# 用 all_net 的均值段 + 事件日期序列
import csv
tv_dates, tv_close = [], []
with open(os.path.join(BASE, "data", "wheat_zw_weekly_tradingview.csv"), encoding="utf-8") as f:
    r = csv.reader(f); next(r)
    for row in r:
        if row[0] and row[4]:
            tv_dates.append(row[0]); tv_close.append(float(row[4]))

# 只留 2016+ 做趋势
idx16 = [i for i, ddt in enumerate(tv_dates) if ddt >= "2016-01-01"]
dates_16 = [tv_dates[i] for i in idx16]
close_16 = [tv_close[i] for i in idx16]
# 价格归一化到 2016 起点 = 100
base_close = close_16[0] if close_16 else 1
norm_16 = [round(c / base_close * 100, 2) for c in close_16]
# 事件散点（净多暴增，合计）→ 用事件日期在 index 上找对应归一价格
ev_dates = [e["date"] for e in ev_net_total_sorted]
ev_scatter = []
for e in ev_net_total_sorted:
    dte = e["date"]
    # 找 tv 中 ≥ dte 的第一根
    target = None
    for dd, cc in zip(tv_dates, tv_close):
        if dd >= dte:
            target = cc; break
    if target:
        ev_scatter.append({"date": dte, "price": round(target / base_close * 100, 2)})
ev_markpoints = [{"coord": [e["date"], e["price"]], "value": e["date"]} for e in ev_scatter]

def mini_card(t, v, sub=""):
    return f'<div class="mc"><div class="mn">{t}</div><div class="mv">{v}</div><div class="mm">{sub}</div></div>'

# 关键指标卡
g_all = groups["all_net"]; g_multi = groups["net_multi"]; g_cover = groups["net_cover"]; g_chase = groups["net_chase"]
latest_share = latest["share_long"] if not (latest["share_long"] is None or (isinstance(latest["share_long"], float) and math.isnan(latest["share_long"]))) else None

cards = "".join([
    mini_card("暴增事件数", f"{g_all['n']} 个", "小麦三合约合计·2016+"),
    mini_card("多头主导占比", f"{(g_multi['n']/g_all['n']*100):.0f}%", f"n={g_multi['n']}，其余为空头主导"),
    mini_card("多头主导 +12周", pctstr(g_multi['fwd12']['mean']), f"相对基线 {pctstr(g_multi['fwd12'].get('excess'))}"),
    mini_card("空头主导 +12周", pctstr(g_cover['fwd12']['mean']), f"相对基线 {pctstr(g_cover['fwd12'].get('excess'))}"),
    mini_card("最新事件", "2026-09-01", f"多头占比 {latest_share*100:.0f}%"),
    mini_card("最新 +1周后", pctstr(latest.get("fwd1")) if latest.get("fwd1") is not None else "待观察", "截至 09-04 收盘"),
])

CSS = """
<style>
body{margin:0;background:#f7f7f5;color:#1a1a1a;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.7}
.wrap{max-width:1080px;margin:0 auto;padding:26px 22px 40px}
h1{font-size:23px;margin:6px 0 4px;font-weight:700}
h2{font-size:16px;margin:22px 0 8px;border-left:4px solid #0072B2;padding-left:10px}
h3{font-size:14px;margin:10px 0 6px;color:#333}
.sub{font-size:12.5px;color:#666;margin:3px 0}
.meta{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;font-size:12.5px;color:#444;margin:16px 0 6px}
.alert{background:#fffdf5;border:1px solid #e8dcc0;border-left:4px solid #E69F00;border-radius:6px;padding:13px 16px;font-size:13px;margin:14px 0}
.kbox{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:16px 18px;margin:14px 0}
.tw{overflow-x:auto;background:#fff;border:1px solid #e6e4df;border-radius:8px}
th{background:#f0efe9;color:#333;font-weight:600;padding:8px 9px;text-align:right;border-bottom:1.5px solid #ddd9d0;position:sticky;top:0;font-size:11.5px;white-space:nowrap}
td{padding:7px 9px;font-size:12px;border-bottom:1px solid #f0efe9;text-align:right;white-space:nowrap}
.ctr{text-align:center}
.num{font-variant-numeric:tabular-nums}
.pos{color:#C8102E}
.neg{color:#009E73}
.dim{color:#888;font-size:11.5px}
.dim2{color:#999;font-size:11px}
.sig2{color:#0052A5;font-weight:700}
.sig3{color:#A32D2D;font-weight:700}
.mcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin:10px 0}
.mc{background:#fff;border:1px solid #e6e4df;border-radius:7px;padding:9px 12px}
.mn{font-size:12px;font-weight:600;color:#333}
.mv{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}
.mm{font-size:10.5px;color:#888}
.chart{background:#fff;border:1px solid #e6e4df;border-radius:8px;height:340px;margin:14px 0}
.note{font-size:12px;color:#666;background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;margin-top:10px}
.note li{margin:5px 0}
.tag{display:inline-block;background:#eef3f7;color:#0072B2;border-radius:4px;padding:1px 7px;font-size:11px;margin-right:6px}
.foot{margin-top:34px;font-size:11.5px;color:#999;border-top:1px solid #e6e4df;padding-top:12px}
</style>
"""

ECharts = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>'

html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>小麦非商头寸暴增事件研究 · 80号</title>
{CSS}
{ECharts}
</head><body><div class="wrap">

<h1>小麦非商业头寸"暴增"事件研究</h1>
<div class="sub">持仓口径：CFTC COT futures-only legacy，<b>小麦三合约合计（SRW+HRW+HRS）</b>为主，SRW/HRW/HRS 分合约对照</div>
<div class="sub">事件定义：周 Δ非商净多 / Δ多头 / Δ空头 超 2016+ 历史分位（p90 / p90 / p10），间隔≤4周聚类为一事件 ｜ 价格：CBOT 小麦主力连续周线（TradingView），2016+ 真实价格段 ｜ 生成：2026-09-05</div>

<div class="meta">
<b>核心问题</b>：CFTC 非商业头寸暴增之后，小麦价格会不会涨？"短暂 vs 持久"的暴增如何区分？<br>
<b>方法</b>：事件研究 —— 2016 年以来全部净多暴增事件（n={g_all['n']}），按 <b>来源（多头主导 vs 空头主导）× 位置（事件前4周价格）</b> 分组，测未来 +1/+2/+4/+8/+12 周收益，并与 2016+ 全样本基线对照。
</div>

<h2>一、结论速览</h2>
<div class="mcards">{cards}</div>
<div class="alert">
<b>三个核心发现：</b><br>
① <b>暴增本身不是看涨信号</b>：全部净多暴增后 +12 周均值 <b>{pctstr(g_all['fwd12']['mean'])}</b>，与基线（{pctstr(base['fwd12']['mean'])}）几乎无差 —— "暴增 → 涨"是事后归因错觉。<br>
② <b>方向性拆解有效</b>：<b>多头主导</b>（主动做多 ≥50%）暴增后 +12 周 <span class="pos">{pctstr(g_multi['fwd12']['mean'])}</span>（n={g_multi['n']}），<b>空头主导</b>（空头砍仓贡献 &gt;50%）后 +12 周 <span class="neg">{pctstr(g_cover['fwd12']['mean'])}</span>（n={g_cover['n']}）—— 差 <b>{pctstr(g_multi['fwd12']['mean']-g_cover['fwd12']['mean'])}</b>。<br>
③ <b>危险组合</b>：空头深度砍仓 + 事件前价格已大涨 = 顶部信号（2023-06-20 / 2024-04-30 / 2025-02-04 均 +12 周 −15% 以上）。
</div>

<h2>二、事件收益分组统计（小麦三合约合计）</h2>
<div class="tw">
<table>
<thead><tr>
<th>分组</th><th class="ctr">n</th>
{''.join(f'<th colspan="2">{w}周均值 / 超额</th>' for w in WINDOWS)}
</tr></thead>
<tbody>
{rows_group_html}
{baseline_html}
</tbody>
</table>
</div>
<div class="note">超额 = 事件组均值 − 2016+ 全样本同窗口均值；括号为池化 t 值（|t|&gt;1.96 显著、&gt;2.58 高度显著）。颜色红涨绿跌。</div>

<h2>三、小麦价格与暴增事件时间轴</h2>
<div class="chart" id="cprice"></div>
<script>
(function() {{
  var el = document.getElementById('cprice'); if (!el) return;
  var ch = echarts.init(el);
  ch.setOption({{
    grid: {{left: 60, right: 30, top: 40, bottom: 60}},
    tooltip: {{trigger: 'axis', textStyle: {{fontSize: 12}}}},
    legend: {{data: ['小麦归一价(2016=100)', '净多暴增事件'], top: 8, textStyle: {{fontSize: 11, color: '#555'}}}},
    xAxis: {{type: 'category', data: {json.dumps(dates_16)}, axisLabel: {{fontSize: 9, color: '#777', rotate: 45}}}},
    yAxis: {{type: 'value', name: '归一价格', nameTextStyle: {{fontSize: 10, color: '#666'}}, axisLabel: {{fontSize: 10, color: '#666'}}}},
    series: [
      {{name: '小麦归一价(2016=100)', type: 'line', data: {json.dumps(norm_16)}, showSymbol: false, lineStyle: {{width: 1.3, color: '#666666'}}}},
      {{name: '净多暴增事件', type: 'scatter', data: {json.dumps([e['date'] for e in ev_scatter])}, symbol: 'circle', symbolSize: 7,
        itemStyle: {{color: '#C8102E'}},
        markPoint: {{data: {json.dumps(ev_markpoints)}, symbol: 'pin', symbolSize: 22,
                    label: {{show: true, fontSize: 8, color: '#fff', formatter: ' '}}}}
      }}
    ]
  }});
  window.addEventListener('resize', function() {{ ch.resize(); }});
}})();
</script>

<h2>四、三因子判别框架</h2>
<div class="kbox">
<h3>怎么区分"短暂脉冲"与"持久行情"？</h3>
<p>不是看暴增本身维持了多久（那是结果），而是看三个决定因子：</p>
<table>
<thead><tr><th style="text-align:left">因子</th><th colspan="2" style="text-align:left">含义与证据</th></tr></thead>
<tbody>
<tr><td class="ctr"><b>来源</b></td><td>多头主动加仓（多头主导）→ 往往代表真实看涨信念</td><td>空头砍仓（净多增但空头减更多）→ 往往是"止损式的被动上涨""顶部信号"</td></tr>
<tr><td class="ctr"><b>位置</b></td><td>事件前 4 周价格 ≤0% = 启动型，多头提前布局</td><td>≥5% = 追涨型，追高风险，拥挤之后易均值回归</td></tr>
<tr><td class="ctr"><b>连续性</b></td><td>多周集群（2-6 周） = 资金持续流入，趋势延续</td><td>单周脉冲 + 立刻回吐 = 短期博弈，不可持续</td></tr>
</tbody>
</table>
<p class="dim">2020 年为什么"久"：2020-07/08/10 三次暴增构成<b>多周集群</b> + 部分<b>多头主导</b>（占比 36-53%），价格站上供需故事（干旱+中国采购），不是靠持仓本身维持。</p>
</div>

<h2>五、事件明细（小麦三合约合计 · 净多暴增，按日期）</h2>
<div class="tw">
<table>
<thead><tr>
<th>事件日</th><th>Δ净多</th><th>Δ多头</th><th>Δ空头</th><th class="ctr">多头占比</th><th class="ctr">连续周</th><th class="ctr">4周保留</th><th>前4周价</th>
{''.join(f'<th>{w}周后</th>' for w in WINDOWS)}
</tr></thead>
<tbody>
{ev_net_html}
</tbody>
</table>
</div>
<div class="note">多头占比 = 事件 Δ多头 / Δ净多（≥50% 为多头主导）；4周保留 = 事件净多增量在 +4 周后仍保留比例（≤0 为完全回吐）。最新 2026-09-01 已标出。</div>

<div class="foot">
数据源：CFTC COT futures-only 1995-2026（results/cot/agri_cot_history_1995_2026.json） ｜ 价格：TradingView CBOT 小麦主力连续周线 ｜ 脚本：scripts/cot_wheat_surge_events_20260905.py + scripts/build_cot_surge_report_20260905.py ｜ 明细：results/cot/wheat_surge_events_20260905.json/.csv
</div>

</div></body></html>"""

with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_doc)
print("已生成", os.path.join(OUT, "index.html"), len(html_doc), "bytes")