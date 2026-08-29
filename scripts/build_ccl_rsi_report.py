# -*- coding: utf-8 -*-
"""
CCL RSI 档位买入回测报告
读取 results/ccl_rsi_band_buy.json + data/ccl 日线
输出 reports/56_CCL_RSI档位买入/index.html
"""
import os, json, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "56_CCL_RSI档位买入")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "ccl_rsi_band_buy.json"), encoding="utf-8") as f:
    D = json.load(f)

# ---------- 读日线（近 500 日价格 + RSI 曲线用） ----------
px_rows = []
with open(os.path.join(ROOT, "data", "ccl", "CCL, 1D.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        d = row["date"].split(" ")[0]
        v = row["adj_close"] if row["adj_close"] else row["close"]
        if v:
            px_rows.append([d, float(v)])
px_rows.sort()
# 算 RSI（pandas 同口径）
import statistics as st
try:
    import pandas as pd, numpy as np
    df = pd.DataFrame(px_rows, columns=["date", "px"])
    c = df["px"]
    delta = c.diff(); gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1/14, adjust=False).mean(); al = loss.ewm(alpha=1/14, adjust=False).mean()
    rsi_series = (100 - 100/(1+ag/al)).tolist()
    px_series = c.tolist()
except Exception as e:
    print("pandas RSI fail:", e); rsi_series = [None]*len(px_rows); px_series = [x[1] for x in px_rows]
N_LAST = 420
recent_px = px_rows[-N_LAST:]
recent_rsi = rsi_series[-N_LAST:]
chart_curve = [{"d": r[0], "px": round(r[1], 2), "rsi": (None if v is None else round(v, 1))}
               for r, v in zip(recent_px, recent_rsi)]

# ---------- 数据块 ----------
BANDS = ["<30", "30-40", "40-50", "50-60", "60-70", "≥70"]
M = D["meta"]
base = D["base"]

def fwd_block(s, key="fwd20"):
    if not s or s.get(key) is None:
        return {"n": 0, "mean": None, "median": None, "win": None, "p_win": None, "sig_win": "-",
                "ex20": None, "ever": None}
    b = s[key]
    return {"n": b["n"], "mean": b["mean"], "median": b["median"], "win": b["win"],
            "p_win": b.get("p_win"), "sig_win": b.get("sig_win", "-"),
            "ex20": (s.get("ex20") or {}).get("median"),
            "ever": s.get("ever_positive")}

def fmt(v, suf="%"):
    return "—" if v is None else f"{v:+.2f}{suf}"

def sig_badge(p, tag):
    if p is None:
        return "<span class='sig no'>—</span>"
    cls = "sig" if tag == "sig" else ("edge" if tag == "edge" else "no")
    return f"<span class='sig {cls}'>{tag}</span>"

# 表1 全档位
rows1 = []
chart_band = []
for b in BANDS:
    s = D["by_band"][b]
    blk = fwd_block(s)
    rows1.append(f"""<tr>
      <td class='nowrap'><b>RSI {b}</b></td>
      <td>{blk['n']}</td>
      <td class='num'>{fmt(blk['median'])}</td>
      <td class='num'>{fmt(blk['mean'])}</td>
      <td class='num'>{fmt(blk['ex20'])}</td>
      <td class='num'>{blk['win']}%</td>
      <td>{sig_badge(blk['p_win'], blk['sig_win'])}</td>
      <td class='num'>{blk['ever']}%</td></tr>""")
    chart_band.append({"bk": b, "med": blk["median"], "win": blk["win"],
                       "ex": blk["ex20"], "n": blk["n"], "cur": (b == M["cur_band"])})

# 表2 当前档位多口径
rows2 = []
chart_multi = []
def row_cur(tag, label):
    s = D["cur_band"][tag]
    blk = fwd_block(s)
    nkey = {"all": "n_all", "cd10": "n_cd10", "narrow_325_375": "n_narrow", "first_enter": "n_first"}[tag]
    n = D["cur_band"][nkey]
    hl = ' class="hl"' if tag == "all" else ""
    rows2.append(f"""<tr{hl}>
      <td class='nowrap'><b>{label}</b></td>
      <td>{n}</td>
      <td class='num'>{fmt(blk['median'])}</td>
      <td class='num'>{fmt(blk['mean'])}</td>
      <td class='num'>{fmt(blk['ex20'])}</td>
      <td class='num'>{blk['win']}%</td>
      <td>{sig_badge(blk['p_win'], blk['sig_win'])}</td>
      <td class='num'>{blk['ever']}%</td></tr>""")
    chart_multi.append({"lab": label, "med": blk["median"], "win": blk["win"],
                        "ex": blk["ex20"], "n": n})
    return blk
b_all = row_cur("all", "全样本（状态式）")
row_cur("cd10", "去重（cd10）")
row_cur("narrow_325_375", "窄窗 RSI 32.5-37.5")
row_cur("first_enter", "首次进入档位")

# 表3 档内细分 + 阶段（fwd20）
sub_data = None
# 档内细分/阶段数据从补充分析（结果已在 JSON 的 stage_cur）
rows3 = []
chart_stage = []
for stg in ["疫情前", "疫情~2022", "本轮牛市"]:
    s = D["stage_cur"][stg]
    blk = fwd_block(s)
    rows3.append(f"""<tr>
      <td class='nowrap'><b>{stg}</b></td>
      <td>{blk['n']}</td>
      <td class='num'>{fmt(blk['median'])}</td>
      <td class='num'>{fmt(blk['mean'])}</td>
      <td class='num'>{fmt(blk['ex20'])}</td>
      <td class='num'>{blk['win']}%</td>
      <td>{sig_badge(blk['p_win'], blk['sig_win'])}</td></tr>""")
    chart_stage.append({"stg": stg, "med": blk["median"], "ex": blk["ex20"], "win": blk["win"], "n": blk["n"]})

# 表4 最近事件
rows4 = []
for e in D["recent"]:
    cls5 = "up" if e["fwd5"] > 0 else "dn"
    cls10 = "up" if e["fwd10"] > 0 else "dn"
    cls20 = "up" if e["fwd20"] > 0 else "dn"
    clsex = "up" if e["ex20"] > 0 else "dn"
    rows4.append(f"""<tr>
      <td class='nowrap'>{e['date']}</td>
      <td class='num'>{e['rsi']:.1f}</td>
      <td class='num {cls5}'>{e['fwd5']:+.2f}%</td>
      <td class='num {cls10}'>{e['fwd10']:+.2f}%</td>
      <td class='num {cls20}'>{e['fwd20']:+.2f}%</td>
      <td class='num {clsex}'>{e['ex20']:+.2f}pp</td></tr>""")

# 年度分布
chart_year = [{"y": int(d["y"]), "n": d["n"]} for d in D["year_dist"]]

# ---------- JS 数据 ----------
js = {
    "curve": chart_curve,
    "band": chart_band,
    "multi": chart_multi,
    "stage": chart_stage,
    "year": chart_year,
    "base": {"med": base["fwd20"]["median"], "win": base["fwd20"]["win"],
             "n": base["fwd20"]["n"], "ex": (base.get("ex20") or {}).get("median")},
    "cur": {"rsi": M["cur_rsi"], "band": M["cur_band"], "pct": M["cur_pct"], "end": M["data_end"]},
}
JS = json.dumps(js, ensure_ascii=False)

cur_band = M["cur_band"]
cur_pct = M["cur_pct"]

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CCL 嘉年华邮轮 · 当前 RSI 档位买入回测</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root {{
  --bg:#f7f7f4; --card:#ffffff; --line:#e3e2dc; --ink:#1f2328; --sub:#6b7078;
  --up:#c0392b; --dn:#1e8449; --upbg:#fdecea; --dnbg:#e9f7ef;
  --sig:#c0392b; --edge:#d68910; --no:#95a5a6;
  --accent:#8e6b3a;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--ink); font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; line-height:1.65; }}
.wrap {{ max-width:1080px; margin:0 auto; padding:28px 20px 60px; }}
h1 {{ font-size:24px; margin:6px 0 4px; }}
.sub {{ color:var(--sub); font-size:13px; margin-bottom:18px; }}
.meta {{ color:var(--sub); font-size:12px; margin-top:6px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:18px 20px; margin:16px 0; }}
.card h2 {{ font-size:17px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid var(--line); }}
.tldr {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }}
.tldr .item {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
.tldr .k {{ font-size:12px; color:var(--sub); }}
.tldr .v {{ font-size:22px; font-weight:700; margin-top:2px; }}
.tldr .d {{ font-size:12px; color:var(--sub); margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th,td {{ padding:7px 9px; text-align:left; border-bottom:1px solid var(--line); }}
th {{ background:#f2f1ec; color:var(--sub); font-weight:600; white-space:nowrap; }}
td.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
td.hl {{ background:var(--upbg); }}
.up {{ color:var(--up); }} .dn {{ color:var(--dn); }}
.sig {{ font-size:11px; padding:2px 7px; border-radius:4px; color:#fff; font-weight:600; }}
.sig.sig {{ background:var(--sig); }} .sig.edge {{ background:var(--edge); }} .sig.no {{ background:var(--no); }}
.na {{ color:#aaa; }}
.chart {{ width:100%; height:340px; margin:8px 0; }}
.chart.tall {{ height:400px; }}
.note {{ font-size:12px; color:var(--sub); margin-top:6px; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
@media(max-width:760px){{ .grid2 {{ grid-template-columns:1fr; }} }}
.badge {{ display:inline-block; background:var(--accent); color:#fff; font-size:11px; border-radius:4px; padding:2px 8px; margin-left:6px; vertical-align:middle; }}
.concl {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:8px; padding:16px 18px; margin:16px 0; }}
.concl li {{ margin:6px 0 6px 18px; }}
.disclaimer {{ font-size:12px; color:var(--sub); border-top:1px solid var(--line); margin-top:26px; padding-top:12px; }}
.legend {{ font-size:12px; color:var(--sub); background:#f2f1ec; border-radius:6px; padding:10px 14px; margin-bottom:10px; }}
.legend b {{ color:var(--ink); }}
</style>
</head>
<body>
<div class="wrap">

<h1>CCL（嘉年华邮轮）· 当前 RSI 档位买入后的表现<span class="badge">56 号回测</span></h1>
<div class="sub">回测口径：日线 RSI14（Wilder 平滑，adj_close 复权）分档 → 当日收盘价买入 → 持有 T+5/T+10/T+20 交易日 · 超额 = CCL 收益 − SPY 同窗口收益（pp）· 数据：Yahoo Finance chart API 日线，2000-01-03 ~ {M['data_end']}（Yahoo 未同步 08-28）</div>

<div class="tldr">
  <div class="item"><div class="k">当前 RSI14（08-27 收盘）</div><div class="v">{M['cur_rsi']:.1f}</div><div class="d">历史 {cur_pct:.1f}% 分位 · 档位 <b>RSI {cur_band}</b></div></div>
  <div class="item"><div class="k">RSI {cur_band} 档历史买入 T+20</div><div class="v up">{b_all['median']:+.2f}%</div><div class="d">中位数 · 胜率 {b_all['win']}%（p={b_all['p_win']}，显著）</div></div>
  <div class="item"><div class="k">T+20 超额 vs SPY</div><div class="v" style="color:var(--sub)">{b_all['ex20']:+.2f}pp</div><div class="d">中位数 · 本轮牛市（2023 起）为 <span class="dn">{D['stage_cur']['本轮牛市']['ex20']['median']:+.2f}pp</span></div></div>
  <div class="item"><div class="k">全期基率 T+20（随机日买入）</div><div class="v">{fmt(base['fwd20']['median'])}</div><div class="d">胜率 {base['fwd20']['win']}% · 结论需对照基率</div></div>
</div>

<div class="card">
<h2>一、核心结论</h2>
<ul>
  <li><b>绝对收益为正但无超额：</b>RSI 30-40 档（当前所在档）历史 963 次买入，T+20 中位 <b class="up">+1.07%</b>、胜率 <b>55.0%</b>（p=0.0018 显著）——但与全期基率 +0.72% 几乎持平，<b>相对 SPY 超额中位仅 +0.03pp</b>，即该档位本身不提供择时优势，收益主要来自 CCL 长期上行。</li>
  <li><b>真正有 edge 的是更超卖档：</b>RSI &lt;30 档 T+20 中位 +3.60%、胜率 65.7%、超额 +1.82pp（全档最强）；当前 RSI 35.4 尚未进入该档（近 60 日 RSI&lt;30 天数 = 0）。</li>
  <li><b>近两年档位已失效：</b>2025 年以来 30-40 档买入 59 次，T+20 中位 <b class="dn">−1.73%</b>、超额 <b class="dn">−2.39pp</b>、胜率降至 47.5%——本轮行情中"RSI 偏低就买"策略显著跑输（本轮牛市阶段 n=133、超额 −1.97pp、胜率 51.1% 不显著）。</li>
  <li><b>档内分化：</b>30-35 子档（超额 +0.81pp、胜率 57.5%）明显优于 35-40 子档（−0.36pp、47.6%），当前 35.4 恰在两档交界附近偏上沿。</li>
  <li><b>当前形态：</b>价 24.95 处近 20/60 日新低、跌破 EMA20/50/200（−6.7%/−8.0%/−8.2%）、2026 YTD <b class="dn">−18.0%</b>——RSI 35.4 反映的是下跌中继而非超卖反转，历史统计不支撑"此处低吸有超额"。</li>
</ul>
</div>

<div class="card">
<h2>二、当前 RSI 位置与价格背景</h2>
<div id="chart_curve" class="chart tall"></div>
<div class="note">近 {N_LAST} 个交易日 · 灰带 = RSI 30-40 当前档位 · 价格复权（adj_close）</div>
</div>

<div class="card">
<h2>三、全档位买入表现（T+20，按 RSI 档位分）</h2>
<div class="legend"><b>参数图例：</b>RSI14 = 14 日相对强弱（Wilder），0-100，&lt;30 超卖 / &gt;70 超买；T+20 = 买入后第 20 个交易日的 adj_close 收益（%）；超额 = CCL fwd − SPY 同窗口 fwd（pp，&gt;0 跑赢大盘）；胜率 = fwd&gt;0 占比；显著性 = 胜率 vs 50% 二项检验（<span class='sig sig'>sig</span> p&lt;0.01 / <span class='sig edge'>edge</span> 0.01≤p&lt;0.05 / <span class='sig no'>no</span> p≥0.05，样本重叠时视作上限）。</div>
<div id="chart_band" class="chart"></div>
<table>
<tr><th>RSI 档位</th><th>样本数</th><th>T+20 中位</th><th>T+20 均值</th><th>超额中位</th><th>胜率</th><th>显著性</th><th>曾浮盈率</th></tr>
{''.join(rows1)}
<tr style="background:#f2f1ec"><td class='nowrap'><b>全期基率（随机日）</b></td><td>{base['fwd20']['n']}</td>
<td class='num'>{fmt(base['fwd20']['median'])}</td><td class='num'>{fmt(base['fwd20']['mean'])}</td>
<td class='num'>{fmt((base.get('ex20') or {{}}).get('median'))}</td><td class='num'>{base['fwd20']['win']}%</td>
<td>{sig_badge(base['fwd20']['p_win'], base['fwd20']['sig_win'])}</td><td class='num'>{base['ever_positive']}%</td></tr>
</table>
<div class="note">解读：&lt;30 档胜率 65.7% 且超额 +1.82pp 为全档最强；30-40 档（当前）绝对收益与基率持平、超额≈0；50-60 档是唯一负收益档（T+20 中位 −0.51%）。</div>
</div>

<div class="grid2">
<div class="card">
<h2>四、当前档位 30-40 多口径验证</h2>
<table>
<tr><th>口径</th><th>样本</th><th>T+20 中位</th><th>均值</th><th>超额中位</th><th>胜率</th><th>显著性</th><th>曾浮盈率</th></tr>
{''.join(rows2)}
</table>
<div class="note">全样本含连续停留（窗口重叠→独立性弱）；cd10 = 每 10 个交易日取首日；窄窗 = RSI 32.5-37.5 精确贴近当前值；首次进入 = 仅档位边界穿越日。四口径方向一致：绝对收益微正、超额≈0。</div>
</div>
<div class="card">
<h2>五、阶段分解（30-40 档）</h2>
<div id="chart_stage" class="chart" style="height:260px"></div>
<table>
<tr><th>阶段</th><th>样本</th><th>T+20 中位</th><th>均值</th><th>超额中位</th><th>胜率</th><th>显著性</th></tr>
{''.join(rows3)}
</table>
<div class="note">疫情~2022 高收益系 2020 年暴跌 80%+ 后 V 型反弹（均值回归极端样本）；本轮牛市阶段超额转负，为"近两年失效"提供证据。</div>
</div>
</div>

<div class="card">
<h2>六、年度分布与近期事件</h2>
<div class="grid2">
  <div><div id="chart_year" class="chart" style="height:260px"></div>
  <div class="note">RSI 30-40 档买入信号年度分布（样本数）</div></div>
  <div>
  <table>
  <tr><th>日期</th><th>RSI</th><th>T+5</th><th>T+10</th><th>T+20</th><th>超额 T+20</th></tr>
  {''.join(rows4)}
  </table>
  <div class="note">最近 8 次进入 RSI 30-40 档的买入结果（2026 年为主）</div>
  </div>
</div>
</div>

<div class="concl">
<h2 style="margin:0 0 8px">七、操作含义（条件化）</h2>
<ul>
  <li><b>仅凭"RSI 处于 30-40 档"买入 CCL 无历史超额</b>——过去 26 年该信号 T+20 中位 +1.07% 与随机买入无异，且近两年已转负（−2.39pp）。当前 RSI 35.4 恰好落在档内中上沿，不构成统计意义上的买点。</li>
  <li><b>若要按 RSI 抄底，等 &lt;30 档</b>——该档是唯一同时满足高胜率（65.7%）+ 正超额（+1.82pp）的区间；当前距 30 尚有约 5 点，可设 RSI 跌破 30 且出现企稳（如收复 EMA20 或放量阳线）再评估。</li>
  <li><b>档内 30-35 &gt; 35-40</b>：若坚持在 30-40 区间分批，历史更支持 30-35 下沿而非当前 35.4 位置。</li>
  <li><b>趋势背景权重高于 RSI 档位</b>：当前价跌破全部均线、2026 YTD −18%、52 周位置仅 13.3%，属下跌趋势中的 RSI 低位——弱趋势中的低 RSI 是"接飞刀"而非"抄底"，需右侧确认信号配合。</li>
  <li><b>反向声音</b>：2026 年 3-7 月多次 30-40 档买入 T+20 有 +9.8%~+25.2% 的高光（邮轮旺季+需求回暖行情），易让人高估该档位胜率——这些事件多数发生在 EMA20 上方或趋势初期，与当前形态（跌破全部均线、创新低）不可比。</li>
</ul>
</div>

<div class="disclaimer">
<b>数据来源</b>：Yahoo Finance chart API 日线（adj_close 复权，2000-01-03 ~ 2026-08-27），SPY 同日对照；RSI14 按 Wilder 平滑计算；统计口径与 48/49/50 号报告一致。<br>
<b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
</div>

</div>

<script>
const DATA = {JS};
const UP = '#c0392b', DN = '#1e8449', GRAY = '#95a5a6', GOLDL = '#8e6b3a';

// 曲线：价格 + RSI 双轴
(function () {{
  const el = document.getElementById('chart_curve');
  const d = DATA.curve;
  const dates = d.map(x => x.d);
  const px = d.map(x => x.px);
  const rsi = d.map(x => x.rsi);
  echarts.init(el).setOption({{
    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
    legend: {{ data: ['价格(adj)', 'RSI14'] }},
    grid: [{{ left: 50, right: 50, top: 30, height: '52%' }}, {{ left: 50, right: 50, top: '68%', height: '24%' }}],
    xAxis: [
      {{ type: 'category', data: dates, gridIndex: 0, axisLabel: {{ show: false }} }},
      {{ type: 'category', data: dates, gridIndex: 1, axisLabel: {{ show: true, rotate: 45, fontSize: 10 }} }}
    ],
    yAxis: [
      {{ type: 'value', gridIndex: 0, scale: true, name: '价格' }},
      {{ type: 'value', gridIndex: 1, min: 0, max: 100, name: 'RSI', splitLine: {{ show: false }} }}
    ],
    series: [
      {{ name: '价格(adj)', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: px, showSymbol: false, lineStyle: {{ width: 1.6, color: GOLDL }} }},
      {{ name: 'RSI14', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: rsi, showSymbol: false, lineStyle: {{ width: 1.4, color: UP }},
        markArea: {{
          silent: true,
          itemStyle: {{ color: 'rgba(200,60,50,0.10)' }},
          data: [[{{ yAxis: 30, name: '30-40档' }}, {{ yAxis: 40 }}]]
        }} }}
    ]
  }});
}})();

// 全档位柱状
(function () {{
  const el = document.getElementById('chart_band');
  const d = DATA.band;
  const colors = d.map(x => x.cur ? GOLDL : GRAY);
  echarts.init(el).setOption({{
    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
    legend: {{ data: ['T+20中位收益%', '胜率%', '超额中位pp'] }},
    xAxis: {{ type: 'category', data: d.map(x => 'RSI ' + x.bk) }},
    yAxis: [{{ type: 'value', name: '收益%' }}, {{ type: 'value', name: '胜率%', max: 100, splitLine: {{ show: false }} }}],
    series: [
      {{ name: 'T+20中位收益%', type: 'bar', data: d.map(x => ({{ value: x.med, itemStyle: {{ color: x.med >= 0 ? UP : DN }} }})), barWidth: 18 }},
      {{ name: '超额中位pp', type: 'bar', data: d.map(x => ({{ value: x.ex, itemStyle: {{ color: x.ex >= 0 ? 'rgba(192,57,43,0.35)' : 'rgba(30,132,73,0.35)' }} }})), barWidth: 18 }},
      {{ name: '胜率%', type: 'line', yAxisIndex: 1, data: d.map(x => x.win), lineStyle: {{ width: 2, color: GOLDL }}, itemStyle: {{ color: GOLDL }} }}
    ]
  }});
}})();

// 多口径
(function () {{
  const el = document.getElementById('chart_multi');
  if (!el) return;
  const d = DATA.multi;
  echarts.init(el).setOption({{
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['T+20中位%', '超额中位pp'] }},
    xAxis: {{ type: 'category', data: d.map(x => x.lab) }},
    yAxis: {{ type: 'value', name: '%' }},
    series: [
      {{ name: 'T+20中位%', type: 'bar', data: d.map(x => ({{ value: x.med, itemStyle: {{ color: x.med >= 0 ? UP : DN }} }})), barWidth: 20 }},
      {{ name: '超额中位pp', type: 'bar', data: d.map(x => ({{ value: x.ex, itemStyle: {{ color: x.ex >= 0 ? 'rgba(192,57,43,0.35)' : 'rgba(30,132,73,0.35)' }} }})), barWidth: 20 }}
    ]
  }});
}})();

// 阶段
(function () {{
  const el = document.getElementById('chart_stage');
  const d = DATA.stage;
  echarts.init(el).setOption({{
    tooltip: {{ trigger: 'axis' }},
    legend: {{ data: ['T+20中位%', '超额中位pp'] }},
    xAxis: {{ type: 'category', data: d.map(x => x.stg) }},
    yAxis: {{ type: 'value', name: '%' }},
    series: [
      {{ name: 'T+20中位%', type: 'bar', data: d.map(x => ({{ value: x.med, itemStyle: {{ color: x.med >= 0 ? UP : DN }} }})), barWidth: 26 }},
      {{ name: '超额中位pp', type: 'bar', data: d.map(x => ({{ value: x.ex, itemStyle: {{ color: x.ex >= 0 ? 'rgba(192,57,43,0.35)' : 'rgba(30,132,73,0.35)' }} }})), barWidth: 26 }}
    ]
  }});
}})();

// 年度分布
(function () {{
  const el = document.getElementById('chart_year');
  const d = DATA.year;
  echarts.init(el).setOption({{
    tooltip: {{ trigger: 'axis' }},
    xAxis: {{ type: 'category', data: d.map(x => x.y) }},
    yAxis: {{ type: 'value', name: '信号数' }},
    series: [{{ name: '信号数', type: 'bar', data: d.map(x => x.n), itemStyle: {{ color: GOLDL }} }}]
  }});
}})();
</script>
</body>
</html>
"""

out_path = os.path.join(OUTD, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out_path, len(html), "bytes")
