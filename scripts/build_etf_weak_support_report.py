# -*- coding: utf-8 -*-
"""构建研报：ETF 弱势状态窗口 × 成分股每次触支撑 事件研究
读取 results/etf_weak_support.json
输出 reports/14_etf_weak_support/etf_weak_support_report.html
静默写盘：只打印 written 路径与体积。
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "14_etf_weak_support")

with open(os.path.join(RES, "etf_weak_support.json"), encoding="utf-8") as f:
    D = json.load(f)

ev = D["events"]
es = D["event_stats"]; dd = D["event_stats_dedup"]
ct = D["ctrl_touch_out_stats"]; cw = D["ctrl_window_day_stats"]; bl = D["baseline_stats"]
cls_d = D["classification"]; fl = D["filters"]; grid = D["stop_grid"]
ca = D["cluster_adjust"]; sub = ca["subgroups_t10"]
ws = D["window_summary"]; by_sector = D["by_sector"]

# ---------- 板块表 ----------
SEC_NOTE = {
    "XLF": "金融：6 只成分，事件最多", "XLK": "科技：聚类调整后唯一负超额板块（−0.45pp）",
    "XLI": "工业：正超额中等", "XLV": "医疗：显著正超额（+0.69pp, t=2.33）",
    "XLP": "必选消费：防御", "XLY": "可选消费", "XLC": "通信：2018-06 起，样本仅 42",
    "XLE": "能源：仅 CVX", "XLB": "材料：仅 SHW，T+10 最强（+2.00%/68%）",
}
sector_rows = []
for sec in ("XLF", "XLK", "XLI", "XLV", "XLP", "XLY", "XLC", "XLE", "XLB"):
    bs = by_sector.get(sec) or {}
    s10 = (bs.get("stats") or {}).get("10") or {}
    sg = sub.get({"XLF": None, "XLK": "XLK科技", "XLV": "XLV医疗", "XLB": "XLB材料"}.get(sec) or "", None)
    ex_txt = f"{sg['excess_pp']:+.2f}pp (t={sg['excess_t']})" if sg else "—"
    sector_rows.append(
        f"<tr><td><b>{sec}</b></td><td class='nowrap'>{bs.get('n', 0)}</td>"
        f"<td class='{'up' if (s10.get('mean') or 0)>=0 else 'dn'}'>{s10.get('mean')}% / {s10.get('win')}%</td>"
        f"<td class='nowrap'>{ex_txt}</td><td class='note2'>{SEC_NOTE[sec]}</td></tr>")

# ---------- 统计对比表 ----------
stat_rows = []
for k, lab in (("1", "T+1"), ("5", "T+5"), ("10", "T+10"), ("20", "T+20")):
    a = es[k]
    stat_rows.append(
        f"<tr><td class='nowrap'><b>{lab}</b></td><td class='nowrap'>{a['n']}</td>"
        f"<td class='nowrap'><b>{a['win']}%</b></td>"
        f"<td class='{'up' if a['mean']>=0 else 'dn'}'>{a['mean']:+.2f}%</td>"
        f"<td class='nowrap'>{a['median']:+.2f}%</td>"
        f"<td class='nowrap'>{a['p25']:+.2f}% / {a['p75']:+.2f}%</td>"
        f"<td class='dn nowrap'>{a['maxDD_mean']:+.2f}%</td>"
        f"<td class='nowrap'>{a['tstat']}</td></tr>")

# 聚类调整表
ca_rows = []
for k, lab in (("1", "T+1"), ("5", "T+5"), ("10", "T+10"), ("20", "T+20")):
    o = ca["by_horizon"][k]; e = ca["excess_vs_baseline"].get(k, {})
    et = e.get("excess_t")
    sig = "✗ 不显著" if (et is not None and abs(et) < 2) else ("✓ 显著" if et is not None else "—")
    ca_rows.append(
        f"<tr><td class='nowrap'><b>{lab}</b></td><td class='nowrap'>{o['n_events']} → {o['n_clusters']} 簇</td>"
        f"<td class='nowrap'>{o['cluster_mean']:+.2f}%</td>"
        f"<td class='nowrap'>{o['tstat_cluster']}</td>"
        f"<td class='nowrap'>{bl[k]['mean']:+.2f}%</td>"
        f"<td class='{'up' if (e.get('excess_mean') or 0)>0 else 'dn'}'>{e.get('excess_mean')}pp</td>"
        f"<td class='nowrap'>{et}</td><td class='nowrap'>{sig}</td></tr>")

# 子组聚类调整表（核心）
SUB_NOTE = {
    "全样本": "基准：超额不显著",
    "入场=连续3日低于EMA20": "<b>慢弱入场：显著正超额</b>（渐进阴跌，支撑消化充分）",
    "入场=死叉": "急跌入场：超额不显著（突发冲击，支撑易被击穿）",
    "窗末(>15日)": "<b>窗口越深超额越大</b>（弱势已被充分定价）",
    "窗中(6-15日)": "中等，边际显著",
    "窗初(0-5日)": "窗口刚启动，超额不显著",
    "个股缩量(<=1.0)": "<b>缩量回踩=抛压衰竭</b>，显著正超额",
    "偏离-2~-5%": "适度偏离最佳；过深(<=-5%)反而弱（趋势性破位）",
    "触次1-2": "新支撑（1-2触）好于老支撑（>=5触）",
    "触次>=5": "老支撑反复考验，超额转弱",
    "弱于板块(RS<0)": "弱中触支撑，超额不显著",
    "VIX>=30": "恐慌组绝对收益高但簇少(n=210)，超额边际",
    "XLV医疗": "防御板块支撑更真实",
    "XLB材料": "超额实际显著（见左列数值）；但为单股板块（仅 SHW），结论外推性有限",
    "XLK科技": "<b>唯一负超额</b>：高位支撑在趋势破位后连续失守",
    "慢弱+缩量交集": "双条件交集：样本内最强组合（数值见左列）——<b>后验筛选，置信度降级</b>",
    "慢弱+窗末交集": "双条件交集（数值见左列）——同为后验筛选，置信度降级",
}
_s1 = sub.get("慢弱+缩量交集") or {}
_s2 = sub.get("慢弱+窗末交集") or {}
sub_order = ["全样本", "入场=连续3日低于EMA20", "入场=死叉", "窗初(0-5日)", "窗中(6-15日)", "窗末(>15日)",
             "个股缩量(<=1.0)", "偏离-2~-5%", "触次1-2", "触次>=5", "弱于板块(RS<0)", "VIX>=30",
             "XLV医疗", "XLB材料", "XLK科技", "慢弱+缩量交集", "慢弱+窗末交集"]
sub_rows = []
for name in sub_order:
    r = sub.get(name)
    if not r:
        continue
    hl = "up" if (r.get("excess_pp") or 0) > 0.3 and (r.get("excess_t") or 0) >= 2 else \
         ("dn" if (r.get("excess_pp") or 0) < 0 else "")
    sub_rows.append(
        f"<tr><td><b>{name}</b></td><td class='nowrap'>{r['n']} / {r['clusters']}簇</td>"
        f"<td class='nowrap'>{r['mean']:+.2f}%</td>"
        f"<td class='nowrap'>{r['t_cluster']}</td>"
        f"<td class='{hl} nowrap'>{r['excess_pp']:+.2f}pp</td>"
        f"<td class='nowrap'>{r['excess_t']}</td>"
        f"<td class='nowrap'>{r['win_cluster']}%</td>"
        f"<td class='note2'>{SUB_NOTE.get(name, '')}</td></tr>")

# 止损网格表
stop_rows = []
for sx in ("stop1.0%", "stop2.0%", "stop3.0%"):
    tds = [f"<td><b>{sx.replace('stop','').replace('%','')}%</b></td>"]
    for tp in ("tp5%", "tp10%", "tphold%"):
        g = grid.get(f"{sx}/{tp}")
        if not g:
            tds.append("<td class='na'>—</td>")
            continue
        c = "up" if g["mean"] > 0 else "dn"
        tds.append(f"<td class='{c}'>{g['mean']:+.2f}% / {g['win']}%</td>")
    stop_rows.append("<tr>" + "".join(tds) + "</tr>")

# 事件明细表（前 120 条）
CLS_STYLE = {"V型反转": "cls-v", "死猫反弹": "cls-d", "支撑击穿": "cls-b", "横盘消化": "cls-s"}
ev_rows = []
for e in sorted(ev, key=lambda r: r["date"], reverse=True)[:120]:
    def fmt(v):
        if v is None: return "<td class='na'>—</td>"
        c = "up" if v > 0 else ("dn" if v < 0 else "")
        return f"<td class='{c}'>{v:+.2f}%</td>"
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td>{e['pair']}</td>"
        f"<td class='nowrap'>{e['support_touches']}</td>"
        f"<td class='nowrap'>{e['entry_reason'][:4]}…{'' if e['days_into_window'] is None else ' 第'+str(e['days_into_window'])+'日'}</td>"
        f"<td>{e['vix'] if e['vix'] is not None else '—'}</td>"
        f"{fmt(e['fwd1'])}{fmt(e['fwd5'])}{fmt(e['fwd10'])}{fmt(e['fwd20'])}"
        f"<td class='nowrap'>{'第'+str(e['support_broken_day'])+'日' if e['support_broken_day'] is not None else '守住'}</td>"
        f"<td><span class='cls {CLS_STYLE.get(e['cls'])}'>{e['cls']}</span></td></tr>")

# ---------- JS 数据 ----------
def pick(d, k, field):
    return ((d.get(str(k)) or {}).get(field))

js_data = {
    "groups": {
        "labels": ["T+1", "T+5", "T+10", "T+20"],
        "ev_win": [pick(es, k, "win") for k in (1, 5, 10, 20)],
        "ev_mean": [pick(es, k, "mean") for k in (1, 5, 10, 20)],
        "dd_win": [pick(dd, k, "win") for k in (1, 5, 10, 20)],
        "ct_win": [pick(ct, k, "win") for k in (1, 5, 10, 20)],
        "cw_win": [pick(cw, k, "win") for k in (1, 5, 10, 20)],
        "base_win": [pick(bl, k, "win") for k in (1, 5, 10, 20)],
        "ct_mean": [pick(ct, k, "mean") for k in (1, 5, 10, 20)],
        "cw_mean": [pick(cw, k, "mean") for k in (1, 5, 10, 20)],
        "base_mean": [pick(bl, k, "mean") for k in (1, 5, 10, 20)],
    },
    "cls": cls_d,
    "sector": {
        "labels": list(by_sector.keys()),
        "n": [by_sector[s]["n"] for s in by_sector],
        "win10": [pick(by_sector[s]["stats"], 10, "win") for s in by_sector],
        "mean10": [pick(by_sector[s]["stats"], 10, "mean") for s in by_sector],
    },
    "sub": [{"name": n, "n": sub[n]["n"], "excess": sub[n]["excess_pp"],
             "t": sub[n]["excess_t"], "win": sub[n]["win_cluster"]}
            for n in sub_order if sub.get(n)],
    "filters": {
        "vix": [{"name": k, "n": v["n"], "win10": pick(v.get("stats"), 10, "win"),
                 "mean10": pick(v.get("stats"), 10, "mean")} for k, v in fl["vix"].items()],
        "touches": [{"name": k, "n": v["n"], "win10": pick(v.get("stats"), 10, "win"),
                     "mean10": pick(v.get("stats"), 10, "mean")} for k, v in fl["touches"].items()],
        "win_pos": [{"name": k, "n": v["n"], "win10": pick(v.get("stats"), 10, "win"),
                     "mean10": pick(v.get("stats"), 10, "mean")} for k, v in fl["win_pos"].items()],
        "reason": [{"name": k, "n": v["n"], "win10": pick(v.get("stats"), 10, "win"),
                    "mean10": pick(v.get("stats"), 10, "mean")} for k, v in fl["entry_reason"].items()],
    },
    "stop_grid": [{"stop": sx, "tp": tp,
                   "mean": (grid.get(f"{sx}/{tp}") or {}).get("mean"),
                   "win": (grid.get(f"{sx}/{tp}") or {}).get("win")}
                  for sx in ("stop1.0%", "stop2.0%", "stop3.0%")
                  for tp in ("tp5%", "tp10%", "tphold%")],
    "gallery": D["gallery"],
    "win_agg": ws,
}

def clean_nan(o):
    if isinstance(o, dict): return {k: clean_nan(v) for k, v in o.items()}
    if isinstance(o, list): return [clean_nan(v) for v in o]
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))): return None
    return o
js_data = clean_nan(js_data)

N_EV = D["meta"]["total_events_naive"]; N_DD = D["meta"]["total_events_dedup7d"]

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ETF 弱势状态窗口 × 成分股触支撑 · 事件研究</title>
<script>__ECHARTS_LIB__</script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:13.5px;margin:14px 0 6px;color:#374151;}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:21px;font-weight:700;}
  .kpi .num.up{color:var(--verm);} .kpi .num.dn{color:var(--teal);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;}
  td.nowrap{white-space:nowrap;}
  .note2{color:var(--sub);font-size:11.5px;white-space:normal;min-width:200px;}
  td.up{color:var(--verm);font-weight:600;white-space:nowrap;} td.dn{color:var(--teal);font-weight:600;white-space:nowrap;} td.na{color:#c3c8cf;white-space:nowrap;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:380px;}
  .chart.sm{height:330px;} .chart.tall{height:430px;}
  .chart.k{width:100%;height:360px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;margin-top:10px;}
  .alert{background:#fdecec;border:1px solid #f3c8c8;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7a1f1f;margin-top:10px;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--verm);} .hlg{font-weight:700;color:var(--teal);} .hlb{font-weight:700;color:var(--blue);}
  .cls{padding:1px 7px;border-radius:5px;font-size:11px;font-weight:700;white-space:nowrap;}
  .cls-v{background:#fdeaea;color:#b02525;} .cls-d{background:#fff3e0;color:#b45309;}
  .cls-b{background:#e8f5ef;color:#0f7a53;} .cls-s{background:#eef0f4;color:#5b6472;}
  .gallery{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:12px;}
  .fig{border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:#fff;}
  .fig .ft{font-size:12.5px;font-weight:700;margin-bottom:2px;}
  .fig .fs{font-size:11px;color:var(--sub);margin-bottom:6px;}
  @media (max-width:900px){.gallery{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>ETF 弱势状态窗口 × 成分股每次触支撑 —— 历史走势与概率分析</h1>
    <div class="meta">样本：道指 30 成分股 × 9 只板块 SPDR ETF｜数据：2000-01 ~ 2026-08-20（XLC 自 2018-06；Yahoo 日线 adj_close 复权）｜弱势窗口：EMA10 死叉 EMA20 <b>或</b> 收盘连续 3 日低于 EMA20 → 收盘站回 EMA20 或金叉退出｜支撑：分形 swing-low + ATR 聚类（存活 ≥42 日、近 2 个月未被收盘击穿）｜窗口内<b>每次</b>触支撑计事件（同股 7 日聚类另报）｜入场 = 触及日收盘｜收益未扣成本</div>
    <div class="alert">
      <b>结论先行（四段式）：</b><br>
      <b>[前提校验]</b> "ETF 弱势状态内成分股触支撑是买点"——<b>整体层面不成立但结构上部分成立</b>。全样本 2934 个事件绝对收益为正（T+10 +0.89% / 胜率 58%），但这主要来自 2000 年以来美股的整体上行漂移：<b>按信号日聚类调整后，相对全交易日基线的超额仅 +0.10pp（t=0.65），不显著</b>。<br>
      <b>[关键数据]</b> 超额集中在"慢弱势"结构：<b>入场原因=连续 3 日低于 EMA20（渐进阴跌）的子组超额 +0.59pp（聚类 t=2.87，n=1442）</b>、窗口末期（&gt;15 日）+1.26pp（t=2.63）、个股缩量触及 +0.78pp（t=2.97）；而<b>死叉入场（突发冲击）超额 −0.15pp 不显著</b>、XLK 科技板块 −0.45pp 为唯一负超额。<br>
      <b>[对比]</b> 与同日共振研究（n=21，负期望）的关系：共振是"破位日×触支撑"的瞬时叠加，本研究的窗口口径把事件量放大 140 倍后显示——<b>弱势初期（死叉刚发生、窗口前 5 日）触支撑确实危险，但弱势延续到中后期、抛压衰竭（缩量）后的触支撑有真实正超额</b>。两个研究拼起来构成完整图景：破位日避让、阴跌中后期缩量回踩可参与。<br>
      <b>[置信度]</b> 全样本与子组方向判断置信度<b>高</b>（n=2934、聚类调整）；"慢弱+缩量"交集（n=__NS1__，超额 +__ES1__pp，t=__TS1__）为样本内最强组合，置信度<b>中</b>（存在后验选类风险，需样本外验证）。
    </div>
    <div class="kpis">
      <div class="kpi"><div class="num">2934 / 1994</div><div class="lab">事件数（naive / 7日聚类后），2069 个弱势窗口内</div></div>
      <div class="kpi"><div class="num up">+0.89% / 58%</div><div class="lab">T+10 均值 / 胜率（基线 +0.65% / 56%）</div></div>
      <div class="kpi"><div class="num dn">+0.10pp (t=0.65)</div><div class="lab">聚类调整后 T+10 超额基线 —— 全样本不显著</div></div>
      <div class="kpi"><div class="num up">+0.59pp (t=2.87)</div><div class="lab">慢弱入场（连续3日低于）子组超额 —— 显著</div></div>
      <div class="kpi"><div class="num">36.1% vs 37.2%</div><div class="lab">结局：V型反转 vs 支撑击穿（双峰，较共振研究明显改善）</div></div>
    </div>
  </div>

  <div class="card">
    <h2>一、弱势窗口概览</h2>
    <div style="font-size:12.5px;">
      <p>2000 年以来 9 只板块 ETF 共出现 <b>2069 个弱势窗口</b>：平均时长 <b>__WMEAN__ 日</b>（中位 __WMED__ 日），入场原因死叉 __NCROSS__ 次 / 连续 3 日低于 __NBELOW__ 次；退出方式站回 EMA20 __NEXIT1__ 次 / EMA10 金叉 __NEXIT2__ 次 / 进行中 __NEXIT3__ 次。</p>
      <p style="margin-top:6px;color:var(--sub);">弱势窗口高度频繁（年均约 8 次/板块）且短促——这解释了为什么"窗口内每次触支撑"能积累近 3000 个事件样本。窗口分布均匀：各板块 59~259 个（XLC 仅 59 个，因其 2018 年才上市）。</p>
    </div>
  </div>

  <div class="card">
    <h2>二、事件统计：绝对收益为正，但超额需聚类检验</h2>
    <h3>2.1 五组对比（naive 口径）</h3>
    <div id="ch_groups" class="chart"></div>
    <div class="note">对照说明：「窗外触支撑」= 同一批个股在 ETF <b>非</b>弱势状态下触及同类支撑（n=__NCT__，T+10 +0.55% / 56%）；「窗内非触及日」= 弱势窗口内未触支撑的普通交易日抽样（n=__NCW__，T+10 +0.66% / 56%）；「全交易日基线」（n=__NBL__，T+10 +0.65% / 56%）。naive 口径下事件组 T+10 +0.89% 高于全部三个对照，但差距仅 0.1~0.3pp。</div>
    <div class="scroll" style="margin-top:12px;">
    <table>
      <thead><tr><th>窗口</th><th>样本</th><th>胜率</th><th>均值</th><th>中位</th><th>P25 / P75</th><th>窗口内均值最大回撤</th><th>naive t</th></tr></thead>
      <tbody>__STAT_ROWS__</tbody>
    </table>
    </div>
    <h3>2.2 独立性检验：按信号日聚类（学术评审核心项）</h3>
    <div class="warn"><b>为什么必须做：</b>2934 个事件中 <b>46% 的信号日有多只个股同时触支撑</b>（最大同日簇 24 只——对应全市场普跌日）。这些同日事件共享同一宏观冲击，不是独立观测。直接对 2934 个事件做 t 检验会把有效样本夸大 2~3 倍。方法：按信号日聚类（同日多股收益取均值 → 1347 个独立簇），对簇均值做单样本 t 检验；超额 = 簇均值 − 全交易日基线均值。</div>
    <div class="scroll">
    <table>
      <thead><tr><th>窗口</th><th>事件→簇</th><th>簇均值</th><th>簇 t（绝对）</th><th>基线均值</th><th>超额</th><th>超额 t</th><th>判定</th></tr></thead>
      <tbody>__CA_ROWS__</tbody>
    </table>
    </div>
    <div class="keypoint"><b>解读：</b>绝对收益聚类调整后依然显著（T+10 簇均值 +0.75%，t=4.86）——触支撑的日子本身就不是坏日子。但<b>减去基线漂移后，全样本超额 +0.10pp 完全不显著（t=0.65）</b>。这意味着："弱势窗口内触支撑"作为一个<b>整体</b>并不比随机买入更好；<b>价值在于子结构分层</b>（见第四节）。这一发现与同日共振研究（负期望）不矛盾：共振是窗口初期最危险的瞬间，窗口口径将其稀释。</div>
  </div>

  <div class="card">
    <h2>三、结局分类：双峰结构，V 反与击穿各占 1/3 强</h2>
    <div style="display:flex;flex-wrap:wrap;gap:14px;">
      <div id="ch_cls" class="chart sm" style="flex:1;min-width:320px;"></div>
      <div style="flex:1.2;min-width:340px;font-size:12.5px;padding:8px 4px;">
        <p style="margin-bottom:8px;"><b>分类规则（与共振研究一致，可复现）：</b></p>
        <p>◆ <span class="cls cls-b">支撑击穿</span> 10 日内收盘 &lt; 带下沿 或 T+5&lt;−4%（37.2%）</p>
        <p>◆ <span class="cls cls-v">V型反转</span> T+5&gt;0 且 T+20&gt;0 且 5 日内最深回撤 &gt;−5%（36.1%）</p>
        <p>◆ <span class="cls cls-s">横盘消化</span> 其余（14.1%）</p>
        <p>◆ <span class="cls cls-d">死猫反弹</span> 10 日内最高反弹 ≥2% 但 T+10≤0 或 T+20&lt;−1%（12.6%）</p>
        <p style="margin-top:10px;color:var(--sub);">与同日共振研究对比（击穿 45% vs V反 25%），窗口口径下 <b>V 反比例显著回升</b>——窗口中后期触及的支撑已经历充分消化，守住概率更高。10 日击穿率 36.1% 仍是首要风险：约每 3 笔就有 1 笔支撑失守。</p>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>四、子结构分层：超额来自"慢弱势 + 抛压衰竭"（聚类调整口径）</h2>
    <h3>4.1 子组超额总表（T+10，按信号日聚类，超额 vs 全交易日基线）</h3>
    <div class="scroll">
    <table>
      <thead><tr><th>子组</th><th>事件 / 簇</th><th>簇均值</th><th>簇 t</th><th>超额</th><th>超额 t</th><th>簇胜率</th><th>解读</th></tr></thead>
      <tbody>__SUB_ROWS__</tbody>
    </table>
    </div>
    <div id="ch_sub" class="chart tall" style="margin-top:10px;"></div>
    <div class="keypoint"><b>机制解读（为什么"慢弱"有效）：</b>① <b>入场原因分层</b>——"连续 3 日低于 EMA20"确认的弱势是渐进阴跌，下跌动能在窗口内逐步衰竭，支撑触及对应的是抛压尾声；而"死叉"确认的弱势多为突发冲击（消息/系统性急跌），支撑面临的是动能峰值，击穿率高。② <b>窗口位置单调</b>——窗初 +0.49% → 窗中 +1.29% → 窗末 +1.75%（naive），聚类超额同步放大（−0.12pp → +0.49pp → +1.26pp）：弱势持续越久，触支撑的赔率越好。③ <b>缩量确认</b>——个股量比 ≤1.0 的触及（抛压衰竭的直接证据）超额 +0.78pp（t=2.97）；放量触及（n=2376）naive 均值 +0.70%、超额未达显著。④ <b>触次</b>——1-2 触的新支撑超额 +0.53pp（t=2.38），≥5 触的老支撑超额转弱（+0.08pp，不显著），与共振研究结论方向一致。</div>
    <h3>4.2 板块分层：医疗/材料显著，科技为负</h3>
    <div id="ch_sector" class="chart sm"></div>
    <div class="scroll" style="margin-top:10px;">
    <table>
      <thead><tr><th>板块</th><th>事件数</th><th>T+10 均值 / 胜率</th><th>聚类超额（有计算的）</th><th>说明</th></tr></thead>
      <tbody>__SECTOR_ROWS__</tbody>
    </table>
    </div>
    <div class="note"><b>XLK 科技是唯一聚类负超额板块</b>（−0.45pp）——与共振研究"XLK 击穿率 80%"一脉相承：科技股的支撑多形成于高位横盘，ETF 走弱后支撑连续失守。<b>XLV 医疗显著正超额</b>（+0.69pp，t=2.33）：防御板块的支撑更"真实"。<b>XLB 材料超额同样显著</b>（+1.35pp，t=2.57，T+10 +2.00%/68%），但为单股板块（仅 SHW），个股特异性强，结论外推性有限。</div>
  </div>

  <div class="card">
    <h2>五、风控与执行：止损网格</h2>
    <div style="display:flex;flex-wrap:wrap;gap:14px;">
      <div style="flex:1;min-width:300px;">
        <div class="scroll">
        <table>
          <thead><tr><th>止损(带下沿下方)</th><th>止盈 5%</th><th>止盈 10%</th><th>持有到期(T+20)</th></tr></thead>
          <tbody>__STOP_ROWS__</tbody>
        </table>
        </div>
        <div class="note">单元格 = 均值收益 / 胜率。与同日共振研究（12 组合全负）相反，本口径下<b>止损 3% 组合全部为正期望</b>：3% 止损 + 持有到期 +1.00% / 52.3%、3% 止损 + 止盈 5% 胜率 59.9%（最高）。止损 1% 依然被噪声扫损（持有到期胜率仅 44.8%）。<b>执行含义：止损必须给到支撑带下沿下方 3%，用空间换不被洗出</b>。</div>
      </div>
      <div id="ch_stop" class="chart sm" style="flex:1.1;min-width:330px;"></div>
    </div>
    <div class="alert"><b>可执行结论（样本内，需样本外验证）：</b>优选形态 = <b>ETF 因"连续 3 日低于 EMA20"进入弱势 + 窗口已持续 6 日以上 + 个股缩量（量比≤1）触及 1-4 触支撑</b>，入场 = 触及日收盘，止损 = 支撑带下沿下方 3%，持有 10~20 日或 +5% 止盈。规避：<b>死叉首日/窗口前 5 日</b>、<b>放量触及</b>、<b>XLK 科技板块</b>、≥5 触老支撑。该交集子组（慢弱+缩量，n=__NS1__）聚类超额 +__ES1__pp（t=__TS1__）——注意这是<b>样本内后验筛选</b>，实盘前应在 2026-08 之后的数据上验证。</div>
  </div>

  <div class="card">
    <h2>六、案例画廊：代表性事件（个股 K 线 + 支撑带 + 弱势窗口阴影 + VIX）</h2>
    <div class="note">每图两层：上为个股日 K（红涨绿跌，紫色虚线=支撑中值、橙色阴影=支撑带、◆=入场点、<b>灰色竖带=该 ETF 弱势窗口区间</b>），下为同期 VIX（20/30 阈值线）。窗口 = 事件前 25 ~ 事件后 15 交易日。</div>
    <div class="gallery" id="gallery"></div>
  </div>

  <div class="card">
    <h2>七、事件明细（最近 120 条，共 2934 条全量见 CSV）</h2>
    <div class="scroll" style="max-height:520px;overflow-y:auto;">
    <table>
      <thead><tr><th>信号日</th><th>组合</th><th>支撑</th><th>窗口入场/窗内第几日</th><th>VIX</th><th>T+1</th><th>T+5</th><th>T+10</th><th>T+20</th><th>击穿</th><th>结局</th></tr></thead>
      <tbody>__EV_ROWS__</tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>信号定义与方法局限（必读）</h2>
    <div style="font-size:12.5px;">
      <p><b>弱势窗口（ETF 侧）：</b>EMA10/EMA20；入场 = EMA10 死叉 EMA20（前日 ≥、当日 &lt;）<b>或</b>收盘连续 3 日低于 EMA20（以第 3 日为窗口起点，无前视）；出场 = 收盘重新站上 EMA20 <b>或</b> EMA10 金叉 EMA20，先到先出。窗口起点取"确认日"而非"发生日"，保证实盘可执行。</p>
      <p><b>支撑触及（个股侧）：</b>分形 swing-low（k=3）→ 0.75×ATR14 近 60 日中位数容差水平聚类 → 强支撑 = 存活 ≥42 交易日且近 42 交易日收盘未破带下沿 → 当日首次回踩（前 5 日低点在带上沿之上、当日低点入带、收盘守住带下沿）。窗口内每次满足即计事件。</p>
      <p style="margin-top:8px;"><b>主要局限：</b>① <b>多重检验风险</b>——17 个子组中报告了 5~6 个"显著"，按 5% 水平多重比较下部分是假阳性；"慢弱入场 + 窗末 + 缩量"三个变量高度相关（同一现象的不同侧面），不应视为三个独立证据；② 聚类调整只处理了同日相关，<b>未处理跨窗口重叠</b>（同一 ETF 相邻窗口、同股 7 日内重复触及已通过 dedup 口径另报：T+10 +0.74% / 56%，方向一致）；③ 超额 = 事件均值 − 无条件基线均值，<b>未做市场模型 β 调整</b>——弱势窗口内个股本身 β 偏高，正超额可能部分来自反弹 β；④ 幸存者偏差：池子为现存道指成分股（NVDA 2024 年才入指等，早期为事后映射）；⑤ 未计交易成本与滑点；⑥ XLC 样本仅 42（2018-06 起），其 T+10 −0.92% 不具备统计效力；⑦ 子组交集（慢弱+缩量等）为样本内后验筛选，<b>置信度降级</b>。数据源 Yahoo Finance 日线复权价，经本机 Chrome CDP 抓取。</p>
    </div>
    <div class="dis"><b>免责声明：</b>以上内容基于公开历史数据与量化统计，仅供研究参考，不构成投资建议。历史规律不预示未来表现；子组样本量有限，实际决策需结合当期宏观与个股基本面独立判断。市场有风险，投资需谨慎。</div>
  </div>

</div>
<script>
var DATA = __DATA_JSON__;
const C = {blue:'#0072B2',orange:'#E69F00',sky:'#56B4E9',purple:'#9467bd',verm:'#D55E00',teal:'#009E73',grey:'#8a919c'};
function fmt(v,suf){ return (v==null||isNaN(v)) ? '—' : v+suf; }

// 2.1 五组对比
(function(){
  const g = DATA.groups;
  echarts.init(document.getElementById('ch_groups')).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['事件·胜率','7日聚类·胜率','窗外触支撑·胜率','窗内非触·胜率','基线·胜率']},
    grid:{left:48,right:20,top:40,bottom:30},
    xAxis:{type:'category',data:g.labels},
    yAxis:[{type:'value',min:45,max:68,name:'胜率%',axisLabel:{formatter:'{value}%'}},
           {type:'value',name:'均值%',axisLabel:{formatter:'{value}%'}}],
    series:[
      {name:'事件·胜率',type:'line',data:g.ev_win,lineStyle:{width:3,color:C.verm},itemStyle:{color:C.verm},symbolSize:9,label:{show:true,fontSize:10,formatter:p=>p.value+'%'}},
      {name:'7日聚类·胜率',type:'line',data:g.dd_win,lineStyle:{width:2,color:C.orange},itemStyle:{color:C.orange},symbolSize:7},
      {name:'窗外触支撑·胜率',type:'line',data:g.ct_win,lineStyle:{width:1.6,type:'dashed',color:C.blue},itemStyle:{color:C.blue}},
      {name:'窗内非触·胜率',type:'line',data:g.cw_win,lineStyle:{width:1.6,type:'dotted',color:C.purple},itemStyle:{color:C.purple}},
      {name:'基线·胜率',type:'line',data:g.base_win,lineStyle:{width:1.6,type:'dotted',color:C.grey},itemStyle:{color:C.grey}},
      {name:'事件·均值',type:'bar',yAxisIndex:1,data:g.ev_mean,itemStyle:{color:p=>p.value>=0?'rgba(213,94,0,.28)':'rgba(0,158,115,.28)'},barWidth:24}
    ]
  });
})();

// 三、结局饼
(function(){
  const cc = DATA.cls.count;
  const items = [
    {name:'支撑击穿 ✗', value:cc['支撑击穿'], itemStyle:{color:C.teal}},
    {name:'V型反转 ✓', value:cc['V型反转'], itemStyle:{color:C.verm}},
    {name:'横盘消化 ~', value:cc['横盘消化'], itemStyle:{color:C.grey}},
    {name:'死猫反弹 △', value:cc['死猫反弹'], itemStyle:{color:C.orange}}
  ];
  echarts.init(document.getElementById('ch_cls')).setOption({
    tooltip:{formatter:'{b}: {c} 笔 ({d}%)'},
    legend:{bottom:0,textStyle:{fontSize:11}},
    series:[{type:'pie',radius:['42%','68%'],center:['50%','45%'],data:items,
      label:{formatter:'{b}\\n{d}%',fontSize:11}}]
  });
})();

// 4.1 子组超额（横向条形，核心图）
(function(){
  const d = DATA.sub;
  const sig = d.filter(x=>Math.abs(x.t)>=2);
  echarts.init(document.getElementById('ch_sub')).setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
      formatter:p=>{const x=d[d.length-1-p[0].dataIndex];return x.name+'<br/>n='+x.n+' ｜ 超额 '+x.excess+'pp ｜ t='+x.t+' ｜ 簇胜率 '+x.win+'%';}},
    grid:{left:170,right:60,top:20,bottom:30},
    xAxis:{type:'value',name:'聚类调整超额（pp，vs 全交易日基线）',axisLabel:{formatter:'{value}pp'}},
    yAxis:{type:'category',data:d.map(x=>x.name).reverse(),axisLabel:{fontSize:11}},
    series:[{type:'bar',data:d.map(x=>x.excess).reverse(),barWidth:14,
      itemStyle:{color:p=>{const x=d[d.length-1-p.dataIndex];const s=Math.abs(x.t)>=2;
        return x.excess>=0?(s?C.verm:'rgba(213,94,0,.35)'):(s?C.teal:'rgba(0,158,115,.35)');}},
      label:{show:true,position:'right',fontSize:10,formatter:p=>{const x=d[d.length-1-p.dataIndex];return x.excess+'pp'+(Math.abs(x.t)>=2?' ✦':'');}}}]
  });
})();

// 4.2 板块
(function(){
  const s = DATA.sector;
  echarts.init(document.getElementById('ch_sector')).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['事件数','T+10 胜率','T+10 均值']},
    grid:{left:48,right:52,top:40,bottom:30},
    xAxis:{type:'category',data:s.labels},
    yAxis:[{type:'value',name:'事件数'},{type:'value',min:0,max:100,axisLabel:{formatter:'{value}%'}}],
    series:[
      {name:'事件数',type:'bar',data:s.n,itemStyle:{color:C.sky},barWidth:24,label:{show:true,position:'top',fontSize:10}},
      {name:'T+10 胜率',type:'line',yAxisIndex:1,data:s.win10,lineStyle:{width:2.5,color:C.verm},itemStyle:{color:C.verm},symbolSize:8,label:{show:true,fontSize:10,formatter:p=>p.value+'%'}},
      {name:'T+10 均值',type:'line',yAxisIndex:1,data:s.mean10,lineStyle:{width:2,type:'dashed',color:C.purple},itemStyle:{color:C.purple}}
    ]
  });
})();

// 五、止损热力
(function(){
  const g = DATA.stop_grid;
  const stops = [...new Set(g.map(x=>x.stop))];
  const tps = [...new Set(g.map(x=>x.tp))].map(t=>t==='tphold%'?'持有到期':t.replace('tp',''));
  const vals = g.map(x=>[stops.indexOf(x.stop), tps.indexOf(x.tp==='tphold%'?'持有到期':x.tp.replace('tp','')), x.mean]);
  echarts.init(document.getElementById('ch_stop')).setOption({
    tooltip:{formatter:p=>{const v=p.value[2];return '止损'+stops[p.value[0]]+' × '+tps[p.value[1]]+'<br/>均值 '+(v==null?'—':v+'%');}},
    grid:{left:70,right:20,top:30,bottom:60},
    xAxis:{type:'category',data:stops,name:'止损（带下沿下方）',nameLocation:'middle',nameGap:28},
    yAxis:{type:'category',data:tps},
    visualMap:{min:-0.2,max:1.2,calculable:true,orient:'horizontal',left:'center',bottom:0,itemWidth:12,itemHeight:90,
      inRange:{color:['#bfe3d4','#f2f4f7','#f3c9a8']},text:['优','劣'],textStyle:{fontSize:10}},
    series:[{type:'heatmap',data:vals,label:{show:true,formatter:p=>p.value[2]==null?'—':p.value[2]+'%'},
      itemStyle:{borderColor:'#fff',borderWidth:2}}]
  });
})();

// 六、画廊（K线 + 窗口阴影 + VIX）
(function(){
  const box = document.getElementById('gallery');
  DATA.gallery.forEach((g,gi)=>{
    const fig = document.createElement('div'); fig.className='fig';
    const clsColor = {'V型反转':C.verm,'支撑击穿':C.teal,'死猫反弹':C.orange,'横盘消化':C.grey}[g.cls]||C.grey;
    const vixTag = g.vix_at_signal!=null ? ' ｜ VIX '+g.vix_at_signal : '';
    fig.innerHTML = '<div class="ft">'+g.pair+' · '+g.date+' <span style="color:'+clsColor+'">['+g.cls+']</span></div>'+
      '<div class="fs">弱势入场:'+g.entry_reason+' ｜ 支撑 '+fmt(g.support,'')+' 带['+fmt(g.support_band_lo,'')+'~'+fmt(g.support_band_hi,'')+'] '+g.support_touches+' ｜ 入场 '+g.entry+vixTag+' ｜ T+5 '+fmt(g.fwd5,'%')+' T+10 '+fmt(g.fwd10,'%')+' T+20 '+fmt(g.fwd20,'%')+
      (g.broken_day?(' ｜ <b style="color:'+C.teal+'">第'+g.broken_day+'日击穿</b>'):' ｜ 支撑守住')+'</div>'+
      '<div class="chart k" id="gk_'+gi+'"></div>';
    box.appendChild(fig);
    const vixMap = new Map(g.vix);
    const vixArr = g.dates.map(d=>vixMap.has(d)?vixMap.get(d):null);
    const evIdx = g.dates.indexOf(g.date);
    echarts.init(document.getElementById('gk_'+gi)).setOption({
      animation:false,
      tooltip:{trigger:'axis',axisPointer:{type:'cross'}},
      axisPointer:{link:[{xAxisIndex:'all'}]},
      grid:[{left:52,right:14,top:22,bottom:'34%'},{left:52,right:14,top:'72%',bottom:22}],
      xAxis:[
        {type:'category',data:g.dates,gridIndex:0,axisLabel:{fontSize:9,rotate:45,interval:8}},
        {type:'category',data:g.dates,gridIndex:1,axisLabel:{fontSize:9,rotate:45,interval:8}}
      ],
      yAxis:[
        {scale:true,gridIndex:0,splitLine:{lineStyle:{color:'#eef0f3'}},axisLabel:{fontSize:9}},
        {scale:true,gridIndex:1,splitLine:{lineStyle:{color:'#eef0f3'}},axisLabel:{fontSize:9},name:'VIX',nameTextStyle:{fontSize:9}}
      ],
      series:[
        {name:g.pair.split('/')[1]+' K线',type:'candlestick',data:g.ohlc,
          itemStyle:{color:C.verm,color0:C.teal,borderColor:C.verm,borderColor0:C.teal},
          markLine:{silent:true,symbol:'none',
            data:[
              {yAxis:g.support,lineStyle:{color:C.purple,type:'dashed',width:1.6},label:{formatter:'支撑 '+g.support,fontSize:9,color:C.purple,position:'insideStartTop'}},
              {xAxis:evIdx,lineStyle:{color:'#b45309',type:'solid',width:1},label:{formatter:'信号日',fontSize:9,color:'#b45309'}}
            ]},
          markArea:{silent:true,
            data:[
              g.win_start_idx!=null?[{xAxis:g.win_start_idx,itemStyle:{color:'rgba(120,130,145,.13)'}},{xAxis:g.win_end_idx}]:null,
              g.support_band_lo!=null?[{yAxis:g.support_band_lo,itemStyle:{color:'rgba(230,159,0,.12)'}},{yAxis:g.support_band_hi}]:null
            ].filter(x=>x)},
          markPoint:{symbolSize:12,data:[{coord:[evIdx,g.entry],value:'◆',itemStyle:{color:'#b45309'},label:{show:true,formatter:'◆入场',fontSize:9,color:'#b45309',position:'right'}}]}
        },
        {name:'VIX',type:'line',xAxisIndex:1,yAxisIndex:1,data:vixArr,showSymbol:false,lineStyle:{width:1.8,color:C.orange},
          areaStyle:{color:'rgba(230,159,0,.10)'},
          markLine:{silent:true,symbol:'none',data:[
            {yAxis:20,lineStyle:{color:C.grey,type:'dotted',width:1},label:{formatter:'20',fontSize:8,color:C.grey}},
            {yAxis:30,lineStyle:{color:C.verm,type:'dotted',width:1},label:{formatter:'30',fontSize:8,color:C.verm}},
            {xAxis:evIdx,lineStyle:{color:'#b45309',type:'solid',width:1},label:{show:false}}
          ]}}
      ]
    });
  });
})();
window.addEventListener('resize',()=>{document.querySelectorAll('[id^=ch_],[id^=gk_]').forEach(el=>{const c=echarts.getInstanceByDom(el);if(c)c.resize();});});
</script>
</body>
</html>
"""

# 窗口统计占位符
er = ws["entry_reason"]; xr = ws["exit_reason"]
html = HTML
html = html.replace("__WMEAN__", str(ws["dur_mean"]))
html = html.replace("__WMED__", str(ws["dur_median"]))
html = html.replace("__NCROSS__", str(er.get("死叉", 0)))
html = html.replace("__NBELOW__", str(er.get("连续3日低于EMA20", 0)))
html = html.replace("__NEXIT1__", str(xr.get("站回EMA20", 0)))
html = html.replace("__NEXIT2__", str(xr.get("EMA10金叉", 0)))
html = html.replace("__NEXIT3__", str(xr.get("进行中", 0)))
html = html.replace("__STAT_ROWS__", "".join(stat_rows))
html = html.replace("__CA_ROWS__", "".join(ca_rows))
html = html.replace("__SUB_ROWS__", "".join(sub_rows))
html = html.replace("__SECTOR_ROWS__", "".join(sector_rows))
html = html.replace("__STOP_ROWS__", "".join(stop_rows))
html = html.replace("__EV_ROWS__", "".join(ev_rows))
html = html.replace("__NCT__", str(ct["1"]["n"]))
html = html.replace("__NCW__", str(cw["1"]["n"]))
html = html.replace("__NBL__", str(bl["1"]["n"]))
# 交集子组数字（动态取自聚类调整结果，避免硬编码脱节）
html = html.replace("__NS1__", str(_s1.get("n", "—")))
html = html.replace("__ES1__", str(_s1.get("excess_pp", "—")))
html = html.replace("__TS1__", str(_s1.get("excess_t", "—")))
with open(os.path.join(ROOT, "scripts", "lib", "echarts.min.js"), encoding="utf-8") as f:
    html = html.replace("__ECHARTS_LIB__", f.read())
html = html.replace("__DATA_JSON__", json.dumps(js_data, ensure_ascii=False, separators=(",", ":")))

os.makedirs(OUTD, exist_ok=True)
out = os.path.join(OUTD, "etf_weak_support_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out} size={os.path.getsize(out)//1024}KB")
