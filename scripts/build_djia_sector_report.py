# -*- coding: utf-8 -*-
"""构建研报 v2：道指板块跌破上升趋势线 × 龙头股触及2个月强支撑（分形聚类口径）
读取 results/djia_sector_support.json + djia_sector_support_extra.json + djia_full_coverage_audit.json
输出 reports/13_道指板块支撑/djia_sector_support_report.html
静默写盘：只打印 written 路径与体积。
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "13_道指板块支撑")

with open(os.path.join(RES, "djia_sector_support.json"), encoding="utf-8") as f:
    D = json.load(f)
with open(os.path.join(RES, "djia_sector_support_extra.json"), encoding="utf-8") as f:
    X = json.load(f)
with open(os.path.join(RES, "djia_full_coverage_audit.json"), encoding="utf-8") as f:
    A = json.load(f)

ev = D["events"]
es = D["event_stats"]; ct = D["ctrl_touch_stats"]; cb = D["ctrl_break_stats"]; bl = D["baseline_stats"]
cls_d = D["classification"]
fl = D["filters"]
grid = D["stop_grid"]
by_year = X["by_year"]; by_sector = X["by_sector"]; br_sector = X["break_rate_by_sector"]
by_touch = X["by_touches"]; by_sage = X["by_support_age"]

# ---------- 第一部分：板块×龙头对应表 ----------
SECTOR_TABLE = [
    ("金融 XLF", "JPM（权重3.96%）· GS（11.41%，道指第一权重）· AXP（4.41%）；另有 V/MA/TRV",
     "XLF", "XLF 破位对道指拖动最直接；本口径下 XLF 共振击穿率 20% 反而不高"),
    ("科技 XLK", "MSFT（4.93%）· AAPL（3.42%）· NVDA（2.28%）· CSCO（1.04%）· CRM（2.35%）· IBM（3.67%）",
     "XLK", "本口径下最差：T+10 −7.27%，击穿率 80%——科技股支撑多为高位横盘，破位后趋势性强"),
    ("工业 XLI", "CAT（8.92%，道指第二权重）· HON（2.93%）· BA（2.99%）",
     "XLI", "样本仅 2 个且全部击穿，方向参考"),
    ("医疗 XLV", "UNH（3.40%）· JNJ（2.95%）· AMGN（4.72%）· MRK（1.50%）",
     "XLV", "唯一 T+10 均值为正的板块（+0.74%），击穿率 25%——防御属性的支撑更真实"),
    ("必选消费 XLP", "WMT（1.61%）· PG（1.96%）· KO（0.97%）",
     "XLP", "样本仅 1 个，不作结论"),
]
sector_rows = []
for name, stocks, sec, note in SECTOR_TABLE:
    pm = {k: v for k, v in D["pair_meta"].items() if k.startswith(sec + "/")}
    n_ev = sum(v["events"] for v in pm.values())
    pairs = "、".join(f"{k.split('/')[1]}({v['events']})" for k, v in pm.items())
    s10 = (by_sector.get(sec) or {}).get("10") or {}
    br = br_sector.get(sec)
    sector_rows.append(
        f"<tr><td><b>{name}</b></td><td>{stocks}</td>"
        f"<td>{n_ev}</td><td>{pairs}</td>"
        f"<td class='{'up' if (s10.get('mean') or 0)>=0 else 'dn'}'>{s10.get('mean')}% / {s10.get('win')}%</td>"
        f"<td>{br}%</td><td class='note2'>{note}</td></tr>")

# ---------- 事件明细表 ----------
CLS_STYLE = {"V型反转": "cls-v", "死猫反弹": "cls-d", "支撑击穿": "cls-b", "横盘消化": "cls-s"}
ev_rows = []
for e in sorted(ev, key=lambda r: r["date"], reverse=True):
    def fmt(v, pct=True):
        if v is None: return "<td class='na'>—</td>"
        c = "up" if v > 0 else ("dn" if v < 0 else "")
        return f"<td class='{c}'>{v:+.2f}%</td>" if pct else f"<td>{v}</td>"
    kinds = "+".join(e["support_kinds"])
    band = f"{e.get('support_band_lo')}~{e.get('support_band_hi')}"
    ev_rows.append(
        f"<tr class='{CLS_STYLE.get(e['cls'],'')}r'>"
        f"<td>{e['date']}</td><td>{e['pair']}</td><td>{kinds}<br><span class='note2'>带 {band}</span></td>"
        f"<td>{e['entry']:.2f}</td><td>{e['etf_vol_ratio']}</td>"
        f"<td>{'—' if e['rs5'] is None else e['rs5']}</td>"
        f"<td>{'—' if e['vix'] is None else e['vix']}</td>"
        f"{fmt(e['fwd1'])}{fmt(e['fwd5'])}{fmt(e['fwd10'])}{fmt(e['fwd20'])}"
        f"<td>{'—' if e['support_broken_day'] is None else '第'+str(e['support_broken_day'])+'日'}</td>"
        f"<td><span class='cls {CLS_STYLE.get(e['cls'])}'>{e['cls']}</span></td></tr>")

# ---------- 止损网格表 ----------
stop_order = ["stop0.5%", "stop1.0%", "stop2.0%", "stop3.0%"]
tp_order = ["tp5%", "tp10%", "tphold%"]
stop_rows = []
for sx in stop_order:
    tds = [f"<td><b>{sx.replace('stop','').replace('%','')}%</b></td>"]
    for tp in tp_order:
        key = f"{sx}/{tp}"
        g = grid.get(key)
        if not g:
            tds.append("<td class='na'>—</td>")
            continue
        c = "up" if g["mean"] > 0 else "dn"
        tds.append(f"<td class='{c}'>{g['mean']:+.2f}% / {g['win']}%</td>")
    stop_rows.append("<tr>" + "".join(tds) + "</tr>")

# ---------- 支撑质量分桶表 ----------
quality_rows = []
for b in ("2触", "3-4触", ">=5触"):
    v = by_touch.get(b) or {}
    t10 = v.get("10") or {}
    quality_rows.append(
        f"<tr><td>{b}</td><td class='nowrap'>{v.get('n','—')}</td>"
        f"<td class='{'up' if (t10.get('mean') or 0)>=0 else 'dn'}'>{t10.get('mean')}% / {t10.get('win')}%</td>"
        f"<td class='nowrap'>{t10.get('median')}%</td></tr>")
for b in ("42-90日", ">90日"):
    v = by_sage.get(b) or {}
    t10 = v.get("10") or {}
    quality_rows.append(
        f"<tr><td>支撑龄 {b}</td><td class='nowrap'>{v.get('n','—')}</td>"
        f"<td class='{'up' if (t10.get('mean') or 0)>=0 else 'dn'}'>{t10.get('mean')}% / {t10.get('win')}%</td>"
        f"<td class='nowrap'>{t10.get('median')}%</td></tr>")

# ---------- JS 数据 ----------
js_data = {
    "groups": {
        "labels": ["T+1", "T+5", "T+10", "T+20"],
        "ev_win": [es[str(k)]["win"] for k in (1, 5, 10, 20)],
        "ev_mean": [es[str(k)]["mean"] for k in (1, 5, 10, 20)],
        "touch_win": [ct[str(k)]["win"] for k in (1, 5, 10, 20)],
        "touch_mean": [ct[str(k)]["mean"] for k in (1, 5, 10, 20)],
        "break_win": [cb[str(k)]["win"] for k in (1, 5, 10, 20)],
        "break_mean": [cb[str(k)]["mean"] for k in (1, 5, 10, 20)],
        "base_win": [bl[str(k)]["win"] for k in (1, 5, 10, 20)],
        "base_mean": [bl[str(k)]["mean"] for k in (1, 5, 10, 20)],
        "ev_mdd": [es[str(k)]["maxDD_mean"] for k in (1, 5, 10, 20)],
    },
    "cls": cls_d,
    "sector": {
        "labels": sorted(by_sector.keys()),
        "win10": [((by_sector[s].get("10") or {}).get("win")) for s in sorted(by_sector)],
        "mean10": [((by_sector[s].get("10") or {}).get("mean")) for s in sorted(by_sector)],
        "n": [(by_sector[s].get("n")) for s in sorted(by_sector)],
        "break_rate": [br_sector.get(s) for s in sorted(by_sector)],
    },
    "year": {
        "labels": sorted(by_year.keys()),
        "n": [by_year[y]["n"] for y in sorted(by_year)],
        "win10": [((by_year[y].get("10") or {}).get("win")) for y in sorted(by_year)],
        "mean10": [((by_year[y].get("10") or {}).get("mean")) for y in sorted(by_year)],
    },
    "filters": {
        "macro": [{"name": k, "n": v["n"],
                   "win1": ((v.get("stats") or {}).get("1") or {}).get("win"),
                   "win10": ((v.get("stats") or {}).get("10") or {}).get("win"),
                   "mean10": ((v.get("stats") or {}).get("10") or {}).get("mean"),
                   "break_rate": v.get("break_rate")}
                  for k, v in fl["macro"].items() if v["n"] > 0],
        "etf_vol": [{"name": k, "n": v["n"],
                     "win5": ((v.get("stats") or {}).get("5") or {}).get("win"),
                     "win10": ((v.get("stats") or {}).get("10") or {}).get("win"),
                     "mean10": ((v.get("stats") or {}).get("10") or {}).get("mean")}
                    for k, v in fl["etf_vol"].items() if v["n"] > 0],
        "rs": [{"name": k, "n": v["n"],
                "win1": ((v.get("stats") or {}).get("1") or {}).get("win"),
                "win5": ((v.get("stats") or {}).get("5") or {}).get("win"),
                "win10": ((v.get("stats") or {}).get("10") or {}).get("win"),
                "mean10": ((v.get("stats") or {}).get("10") or {}).get("mean")}
               for k, v in fl["rs"].items()],
        "stk_shadow": fl["stk_shadow"], "stk_no_shadow": fl["stk_no_shadow"],
        "stk_low_vol": fl["stk_low_vol"], "stk_high_vol": fl["stk_high_vol"],
        "break_rate_all": fl["break_rate_all"],
    },
    "stop_grid": [{"stop": sx, "tp": tp,
                   "mean": (grid.get(f"{sx}/{tp}") or {}).get("mean"),
                   "win": (grid.get(f"{sx}/{tp}") or {}).get("win")}
                  for sx in stop_order for tp in tp_order],
    "audit": {
        "orig_n": A["orig_n"], "full_n": A["full_n"], "added_n": A["added_n"],
        "full_stats": A["full_stats"], "added_stats": A["added_stats"],
        "added_by_sector_n": A["added_by_sector_n"],
    },
    "gallery": D["gallery"],
}

def clean_nan(o):
    if isinstance(o, dict): return {k: clean_nan(v) for k, v in o.items()}
    if isinstance(o, list): return [clean_nan(v) for v in o]
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))): return None
    return o
js_data = clean_nan(js_data)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>道指板块趋势破位 × 龙头股强支撑（分形聚类口径 v2）· 共振事件研究</title>
<script>__ECHARTS_LIB__</script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;--amber:#b45309;}
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
  .flow{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:10px 0 4px;font-size:13px;}
  .fstep{background:#eef3fb;color:var(--blue);border:1px solid #d5e2f7;border-radius:6px;padding:2px 8px;font-weight:600;}
  .farrow{color:var(--sub);}
  .fstat{color:var(--sub);font-size:12px;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;}
  td.nowrap{white-space:nowrap;}
  .note2{color:var(--sub);font-size:11.5px;white-space:normal;min-width:220px;}
  td.up{color:var(--verm);font-weight:600;white-space:nowrap;} td.dn{color:var(--teal);font-weight:600;white-space:nowrap;} td.na{color:#c3c8cf;white-space:nowrap;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:380px;}
  .chart.sm{height:330px;} .chart.tall{height:430px;}
  .chart.k{width:100%;height:420px;}
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
    <h1>道指板块「跌破上升趋势线」× 龙头股「触及2个月强支撑」—— 历史走势与概率分析（分形聚类口径 v2）</h1>
    <div class="meta">样本：5 只道指行业 ETF（XLF/XLK/XLI/XLV/XLP）× 17 只道指成分龙头股｜数据：1995-01-03 ~ 2026-08-20（Yahoo 日线、adj_close 复权口径）｜<b>本版支撑位改用分形 swing-low + ATR 聚类法识别（不再使用均线）</b>，强支撑 = 存活 ≥42 交易日且近 2 个月收盘未被击穿的价位带｜同日共振事件 <b>21</b> 个｜收益为收盘价复权口径、未扣成本｜显著性数字应视为上限（见文末局限）</div>
    <div class="flow">
      <span class="fstep">① 板块 ETF 跌破 ≥2 个月上升趋势线</span><span class="farrow">＋</span>
      <span class="fstep">② 同日龙头股回踩 ≥2 个月分形支撑带且收盘守住下沿</span><span class="farrow">→</span>
      <span class="fstep">③ 以龙头股当日收盘为入场价</span><span class="farrow">→</span>
      <span class="fstep">④ 统计 T+1/5/10/20</span>
      <span class="fstat">　ETF 破位日 __NBREAK__ ｜个股支撑触及日 __NTOUCH__ ｜同日共振 <b>21</b></span>
    </div>
    <div class="alert">
      <b>结论先行（相对旧版均线口径的重大修正）：</b>改用严格的价格结构支撑（分形聚类、2 个月未破）后，该共振信号<b>整体为负期望</b>——T+10 均值 <b>−1.77%</b> / 胜率 40%，低于全交易日基线（+0.72% / 56%），也低于「仅支撑触及」与「仅破位」两个单条件对照。45% 的事件在 10 日内被收盘击穿支撑。<b>旧版（均线支撑口径）得出的"T+10 正超额"结论不成立</b>——那实际上捕捉的是"回踩均线"这一更弱、更宽的形态。本口径下唯一稳健的正期望子集是 <b>VIX≥30 恐慌环境（n=5，T+10 +1.88% / 80%）</b>与<b>个股当日带下影线止跌（n=6，T+10 +0.63% / 66.7%）</b>；样本量决定其余分组只能作方向参考。
    </div>
    <div class="kpis">
      <div class="kpi"><div class="num">21</div><div class="lab">同日共振事件（2000-09 ~ 2026-02，17 组合）</div></div>
      <div class="kpi"><div class="num dn">−1.77% / 40%</div><div class="lab">共振 T+10 均值 / 胜率（基线 +0.72% / 56%）</div></div>
      <div class="kpi"><div class="num dn">45.0%</div><div class="lab">结局为「支撑击穿」占比（10 日内收盘 &lt; 带下沿）</div></div>
      <div class="kpi"><div class="num">42.9%</div><div class="lab">全样本 10 日支撑击穿率（收盘口径）</div></div>
      <div class="kpi"><div class="num dn">−4.25%</div><div class="lab">T+10 窗口内平均最大回撤</div></div>
    </div>
  </div>

  <div class="card">
    <h2>口径变更说明（v1 均线 → v2 分形聚类，必读）</h2>
    <div style="font-size:12.5px;">
      <p><b>为什么换口径：</b>v1 的支撑定义包含「站上 ≥42 日后回踩 MA50/100/200」，实测 62 个事件中 61 个由均线触发——它本质是"上升趋势中回踩均线"，与用户要求的"2 个月没有成功下破的价格位置"不是同一对象。v2 完全弃用均线，采用支撑阻力位识别 skill 的四步法：① swing-low 分形（左右各 3 根严格极小值）；② 以 0.75×ATR14 近 60 日中位数为容差做水平聚类；③ 强支撑 = 存活 ≥42 交易日且<b>近 42 个交易日收盘从未跌破带下沿</b>；④ 当日首次回踩（前 5 日低点在带上沿之上、当日低点入带、收盘守住带下沿）。</p>
      <p style="margin-top:6px;"><b>口径收紧的代价：</b>同日共振样本从 62 → 21（诊断：破位日中约 50% 的候选支撑因"近 2 个月内曾被收盘击穿"淘汰、约 37% 因支撑龄不足淘汰——破位与强支撑在时间上天然互斥，趋势线跌破常发生在新的、尚年轻的支撑上）。<b>n=21 意味着所有子组统计只能作方向性证据</b>；为缓解遗漏，第七节给出了 30 股 × 9 板块的全覆盖审计（32 个事件）。</p>
    </div>
  </div>

  <div class="card">
    <h2>一、道指核心板块与龙头股对应表（权重与事件分布）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>板块 ETF</th><th>道指成分龙头（指数权重）</th><th>共振事件数</th><th>事件构成（个股×次数）</th><th>T+10 均值 / 胜率</th><th>支撑击穿率</th><th>说明</th></tr></thead>
      <tbody>__SECTOR_ROWS__</tbody>
    </table>
    </div>
    <div class="note">道指为<b>价格加权</b>指数：高价股拖动更大；权重为 2026-02-06 Slickcharts 口径。「支撑击穿率」= 共振后 10 个交易日内收盘价跌破支撑带下沿的比例。板块间样本量差异大（XLV 8 个 vs XLP 1 个），横向比较需谨慎。</div>
    <div id="ch_sector" class="chart sm" style="margin-top:10px;"></div>
  </div>

  <div class="card">
    <h2>二、龙头股后续表现与概率分布（T+1 / T+5 / T+10）</h2>
    <h3>2.1 共振信号 vs 三组对照：共振是"负叠加"，不是"正共振"</h3>
    <div id="ch_groups" class="chart"></div>
    <div class="note">对照组：「仅支撑触及」（个股触及支撑但板块同日未破位，n=__NCT__，T+10 +0.84% / 57%）、「仅破位」（板块破位但个股未触支撑，n=__NCB__，T+10 +1.11% / 58%）、「全交易日基线」（n=__NBL__，T+10 +0.72% / 56%）。<b>两个单条件各自都是正期望，同日叠加后反而显著转负（−1.77%）</b>——说明"板块趋势线跌破 + 个股正好回踩旧支撑"组合出现时，往往对应板块级下跌动能尚未衰竭、个股支撑是下跌途中被触及的"半山腰"，而非底部结构。</div>
    <div class="scroll" style="margin-top:12px;">
    <table>
      <thead><tr><th>窗口</th><th>样本</th><th>胜率</th><th>均值</th><th>中位</th><th>P25 / P75</th><th>窗口内均值最大回撤</th><th>回撤 P10（最差10%）</th></tr></thead>
      <tbody>__STAT_ROWS__</tbody>
    </table>
    </div>
    <h3>2.2 结局分类：击穿主导（45%），V 型反转仅 25%</h3>
    <div style="display:flex;flex-wrap:wrap;gap:14px;">
      <div id="ch_cls" class="chart sm" style="flex:1;min-width:320px;"></div>
      <div style="flex:1.2;min-width:340px;font-size:12.5px;padding:8px 4px;">
        <p style="margin-bottom:8px;"><b>分类规则（客观、可复现）：</b></p>
        <p>◆ <span class="cls cls-b">支撑击穿</span> 10 日内收盘 &lt; 带下沿 或 T+5&lt;−4%（9 笔，45.0%）</p>
        <p>◆ <span class="cls cls-v">V型反转</span> T+5&gt;0 且 T+20&gt;0 且 5 日内最深回撤 &gt;−5%（5 笔，25.0%）</p>
        <p>◆ <span class="cls cls-s">横盘消化</span> 其余（4 笔，20.0%）</p>
        <p>◆ <span class="cls cls-d">死猫反弹</span> 10 日内最高反弹 ≥2% 但 T+10≤0 或 T+20&lt;−1%（2 笔，10.0%）</p>
        <p style="margin-top:10px;color:var(--sub);">与旧均线口径（V反 40.3% vs 击穿 38.7% 的双峰）相比，严格价格支撑口径下<b>击穿成为主导结局</b>。机制解释：分形支撑带是"被市场反复验证过的旧低点"，板块趋势线跌破当日个股恰好回到旧低点，通常意味着下跌已持续一段时间、且该支撑即将面临真正的考验——历史数据表明它扛不住的概率（45%）明显高于扛住后走 V 反（25%）。</p>
      </div>
    </div>
    <h3>2.3 年度分布（T+10）</h3>
    <div id="ch_year" class="chart sm"></div>
    <div class="note">21 个事件散布于 14 个年份，单年最多 3 个（2018），<b>年度维度不具备统计效力，仅列分布</b>。方向上：2018（3 笔 T+10 +2.96% / 100%）为唯一集中且为正的年份（医药与金融的恐慌性急跌）；2020、2021、2025、2000 的事件 T+10 均为负。</div>
  </div>

  <div class="card">
    <h2>三、关键过滤条件与相对强度（RS）</h2>
    <div class="warn"><b>阅读前提：</b>n=21，以下每个子组样本多在 2~13 之间。所有分组结论均为<b>方向性证据</b>，不构成可交易的过滤规则；其中标注「样本不足」的组不应参与任何决策。</div>
    <h3>3.1 宏观环境：VIX 是唯一分层清晰的变量</h3>
    <div id="ch_vix" class="chart sm"></div>
    <div class="note"><b>VIX≥30（恐慌宣泄，n=5）是本口径下唯一稳健正期望环境</b>：T+1 +0.68% / 80%，T+10 +1.88% / 80%——危机日的支撑触及伴随全市场超卖，反弹兑现快。VIX&lt;20（n=11，T+10 −1.36% / 30%）为低波动阴跌，击穿率 45.5% 最高。<b>注意与旧版结论相反</b>：旧均线口径下"VIX 20~30 最佳"，本口径下该组反而最差（n=5，T+10 −6.26% / 20%，受 2021 年医疗与 2025 年科技各 1 笔深跌拖累）——两组 n 均≤11，VIX 中段环境的真实效应在现有样本下<b>无法判定</b>，此为明确的数据不足项。</div>
    <h3>3.2 个股当日止跌形态：下影线是唯一有效的微观确认</h3>
    <div class="scroll">
    <table>
      <thead><tr><th>个股当日特征</th><th>样本</th><th>T+1 胜率</th><th>T+5 胜率</th><th>T+10 均值 / 胜率</th></tr></thead>
      <tbody>__SHADOW_ROWS__</tbody>
    </table>
    </div>
    <div class="note"><b>下影线占比 ≥0.3 组（n=6）T+10 +0.63% / 66.7%，是全表唯一正期望子组</b>；无下影线组（n=15）T+10 −2.81% / 28.6%。方向明确但样本仅 6 个，只能作为"无下影线即放弃"的否决性参考。个股缩量触及仅 1 例（数据不足，不作结论）；个股量比&gt;1 组 n=20、T+10 −1.92%——触及强支撑的日子通常伴随放量抛压，这本身印证了"支撑正在被考验"而非"支撑已被确认"。</div>
    <h3>3.3 板块破位日量能</h3>
    <div id="ch_etfvol" class="chart sm"></div>
    <div class="note">平量破位（0.8~1.5 倍，n=13）T+10 −1.18% / 33.3%；放量破位（≥1.5 倍，n=8）T+10 −2.67% / 50%（中位 −0.53%，但尾部极差：T+20 均值 −4.14%、回撤 P10 达 −25%）。<b>两档均为负期望，放量组的尾部风险显著更大</b>。缩量破位 0 例。旧版"平量破位最优"的结论在新口径下不再成立。</div>
    <h3>3.4 相对强度（RS）：数据不足</h3>
    <div class="note">RS≥0（个股 5 日强于板块）仅 <b>2 例</b>，RS&lt;0 有 19 例——分形支撑口径下，触及支撑的个股几乎都弱于板块（逻辑自洽：正在回踩旧支撑的股票 5 日表现自然偏弱）。RS 维度<b>无法分层，数据不足，不作结论</b>。</div>
    <h3>3.5 支撑自身质量：触击次数与支撑龄</h3>
    <div class="scroll">
    <table>
      <thead><tr><th>支撑质量分桶</th><th>样本</th><th>T+10 均值 / 胜率</th><th>T+10 中位</th></tr></thead>
      <tbody>__QUALITY_ROWS__</tbody>
    </table>
    </div>
    <div class="note">3-4 触支撑（n=9）T+10 +0.74% / 62.5% 为唯一正分桶；≥5 触的"老支撑"反而最差（n=6，−4.51% / 16.7%）——被反复验证 5 次以上的旧低点一旦被板块级破位共振盯上，往往意味着更大级别的筹码松动。<b>该模式与教科书"触击越多越可靠"的直觉相反</b>，但 n 均≤9，只能记录、不能应用。</div>
  </div>

  <div class="card">
    <h2>四、假支撑失效风险与风控标准</h2>
    <h3>4.1 支撑在什么环境下最容易被击穿？</h3>
    <div class="scroll">
    <table>
      <thead><tr><th>环境分桶</th><th>样本</th><th>支撑击穿率</th><th>解读</th></tr></thead>
      <tbody>__BREAK_ROWS__</tbody>
    </table>
    </div>
    <div class="keypoint"><b>数据支持的高危环境（按击穿率排序）：</b>① <b>科技 XLK 破位</b>——击穿率 80%（4/5），科技股的分形支撑多形成于高位横盘，板块趋势线跌破后支撑连续失守；② <b>VIX&lt;20 低波动阴跌</b>——击穿率 45.5%，趋势性走弱中支撑被缓慢磨穿；③ 全样本基准 42.9%。相对安全：医疗 XLV（击穿率 25%，防御属性）、VIX≥30 恐慌日（40% 但反弹兑现快）。金融 XLF 击穿率 20%（n=5）好于预期，但 T+10 均值仍为负。</div>
    <h3>4.2 止损 × 止盈网格（入场=信号日收盘；止损=支撑带下沿×(1−X)，盘中触及按止损价成交、跳空按开盘价劣化；止盈=入场价×(1+Y)，收盘达标次日出；最长持有 20 日）</h3>
    <div style="display:flex;flex-wrap:wrap;gap:14px;">
      <div style="flex:1;min-width:300px;">
        <div class="scroll">
        <table>
          <thead><tr><th>止损(带下沿下方)</th><th>止盈 5%</th><th>止盈 10%</th><th>持有到期(T+20)</th></tr></thead>
          <tbody>__STOP_ROWS__</tbody>
        </table>
        </div>
        <div class="note">单元格 = 均值收益 / 胜率。<b>全部 12 个组合均为负期望</b>；相对最优为止损 2% + 持有到期（−0.40% / 40%），止损 0.5%~1% 被噪声扫损后胜率仅 30%~35%。网格的意义不是选参数，而是证明：<b>该信号在任何止损/止盈参数下都不具备正期望</b>。</div>
      </div>
      <div id="ch_stop" class="chart sm" style="flex:1.1;min-width:330px;"></div>
    </div>
    <div class="alert"><b>风控结论（基于数据，非预测）：</b>① 若仍要交易该形态，唯一有数据支撑的执行方式是：<b>仅接受 VIX≥30 且个股当日带下影线（占比≥0.3）的共振</b>（两个条件交集在样本中为 3 例，T+10 全部为正，但 n=3 只能视为案例提示而非规则）；② 止损统一设在支撑带下沿下方 2%（再紧会被噪声扫掉）；③ <b>默认建议是不参与</b>——21 笔全样本、32 笔全覆盖口径下 T+10 均为负，"板块破位 + 个股回踩旧支撑"在本数据集里是警示信号（确认下跌延续）而非买点。</div>
  </div>

  <div class="card">
    <h2>五、案例画廊：10 个代表性共振事件（个股 K 线 + 板块趋势线 + VIX）</h2>
    <div class="note">每图三层：左为龙头股日 K（红涨绿跌，紫色虚线为分形支撑带中值、橙色阴影区为支撑带 [下沿,上沿]、◆ 为入场），右上为板块 ETF 收盘价与被跌破的上升趋势线（破位日 ▼ 标记），右下为同期 <b>VIX 指数</b>（信号日以竖线标注）。窗口 = 事件前 55 ~ 事件后 22 交易日。</div>
    <div class="gallery" id="gallery"></div>
  </div>

  <div class="card">
    <h2>六、21 个共振事件明细</h2>
    <div class="scroll" style="max-height:560px;overflow-y:auto;">
    <table>
      <thead><tr><th>信号日</th><th>组合</th><th>支撑（触数 / 价位带）</th><th>入场价</th><th>ETF量比</th><th>RS5</th><th>VIX</th><th>T+1</th><th>T+5</th><th>T+10</th><th>T+20</th><th>支撑击穿</th><th>结局</th></tr></thead>
      <tbody>__EV_ROWS__</tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>七、覆盖完整性审计：是否遗漏了同日也在支撑上的权重股？</h2>
    <div style="font-size:12.5px;">
      <p>主分析只覆盖 5 个板块 × 17 只预设龙头。为回答"其他权重股同日触及支撑是否被漏掉"，对<b>全部 30 只道指成分股 × 9 个板块 ETF</b>（新增 XLY/XLE/XLB/XLC 与 XLY 对应权重股）重跑同一信号定义：</p>
      <p style="margin-top:6px;"><b>结果：21 → 32 个事件（新增 11 个）</b>。新增主要来自 XLY 可选消费（4）、XLC 通信（2）、XLK（2）；XLB 材料无新增。全覆盖口径 T+10 = −1.83% / 胜率 41.9%，与原 17 对（−1.77% / 40%）<b>方向一致</b>，结论不被覆盖范围改变。新增 11 笔自身 T+1 为正（+0.43% / 63.6%）但 T+10 同样为负（−1.94%），T+20 回正（+1.56%，受个别大反弹拉动，std=14.8%）——新增事件未推翻"负期望"结论，但提示样本扩展后尾部更厚。</p>
      <p style="margin-top:6px;color:var(--sub);">局限：全覆盖中 XLY 等板块的"道指权重股"映射采用当前成分（NVDA 2024 年才入指等），早期年份为事后映射。</p>
    </div>
  </div>

  <div class="card">
    <h2>信号定义与方法局限（必读）</h2>
    <div style="font-size:12.5px;">
      <p><b>板块破位（ETF 侧，与 v1 相同）：</b>swing-low 分形（左右各 3 根严格极小值）取最近 2~3 个依次抬高低点，OLS 拟合上升趋势线；要求线龄 ≥42 交易日、斜率 &gt;0、3 锚点时 R²≥0.7、自第 2 锚点起收盘未连续 2 日收于线下方 0.25×ATR 之外；破位 = 前一日收盘仍在线上、当日收盘首次跌破线值 −0.1×ATR；同一 ETF 10 日冷却；另要求破位日收盘仍高于 42 日前。</p>
      <p><b>个股支撑触及（v2 新口径，不含均线）：</b>① swing-low 分形（k=3）；② 以 0.75×ATR14 近 60 日中位数为容差水平聚类成支撑带 [中值−容差, 中值+容差]；③ 强支撑 = 首个分形确认起存活 ≥42 交易日，且<b>近 42 个交易日收盘从未跌破带下沿</b>；④ 当日首次回踩 = 前 5 日低点均在带上沿之上、当日低点入带、收盘 ≥ 带下沿。同日两条件同时满足 = 共振事件，入场价 = 当日收盘。</p>
      <p style="margin-top:8px;"><b>主要局限：</b>① <b>样本量是根本约束</b>——同日共振仅 21 个（全覆盖 32 个），所有子组 n&lt;15，本报告一切分组数字都是方向性证据，显著性一律视为上限；② 独立性：2 个交易日出现同日多股共振（2003-05-19 两笔、2018-02-05 三笔），同日事件共享同一宏观冲击，有效独立样本约 18~19 组；③ 幸存者偏差：标的池为现存道指成分股；④ 道指成分历经调整，早期年份板块归属为当前映射；⑤ 未计交易成本与滑点；⑥ 未做市场模型 β 调整，均值收益含市场上行漂移（已给基线对照）；⑦ 支撑带"近 42 日未破"的判定窗口为用户指定口径，窗口放宽/收紧会显著改变事件数（8→21 的敏感性已在诊断中验证）；⑧ VIX≥30、下影线等正期望子组存在后验选类风险，应视为样本内发现。数据源 Yahoo Finance 日线复权价，经本机 Chrome CDP 抓取。</p>
    </div>
    <div class="dis"><b>免责声明：</b>以上内容基于公开历史数据与量化统计，仅供研究参考，不构成投资建议。历史规律不预示未来表现；分组样本量有限，实际决策需结合当期宏观与个股基本面独立判断。市场有风险，投资需谨慎。</div>
  </div>

</div>
<script>
var DATA = __DATA_JSON__;
const C = {blue:'#0072B2',orange:'#E69F00',sky:'#56B4E9',purple:'#9467bd',verm:'#D55E00',teal:'#009E73',grey:'#8a919c'};
function fmt(v,suf){ return (v==null||isNaN(v)) ? '—' : v+suf; }

// 2.1 四组对比
(function(){
  const g = DATA.groups;
  echarts.init(document.getElementById('ch_groups')).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['共振信号·胜率','仅支撑触及·胜率','仅破位·胜率','基线·胜率']},
    grid:{left:48,right:20,top:40,bottom:30},
    xAxis:{type:'category',data:g.labels},
    yAxis:[{type:'value',min:30,max:70,name:'胜率%',axisLabel:{formatter:'{value}%'}},
           {type:'value',name:'均值%',axisLabel:{formatter:'{value}%'}}],
    series:[
      {name:'共振信号·胜率',type:'line',data:g.ev_win,lineStyle:{width:3,color:C.verm},itemStyle:{color:C.verm},symbolSize:9,label:{show:true,fontSize:10,formatter:p=>p.value+'%'}},
      {name:'仅支撑触及·胜率',type:'line',data:g.touch_win,lineStyle:{width:1.6,type:'dashed',color:C.blue},itemStyle:{color:C.blue}},
      {name:'仅破位·胜率',type:'line',data:g.break_win,lineStyle:{width:1.6,type:'dotted',color:C.orange},itemStyle:{color:C.orange}},
      {name:'基线·胜率',type:'line',data:g.base_win,lineStyle:{width:1.6,type:'dotted',color:C.grey},itemStyle:{color:C.grey}},
      {name:'共振·均值',type:'bar',yAxisIndex:1,data:g.ev_mean,itemStyle:{color:p=>p.value>=0?'rgba(213,94,0,.28)':'rgba(0,158,115,.28)'},barWidth:26}
    ]
  });
})();

// 2.2 结局分类
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

// 一、板块对比
(function(){
  const s = DATA.sector;
  echarts.init(document.getElementById('ch_sector')).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['共振事件数','T+10 胜率','支撑击穿率']},
    grid:{left:48,right:52,top:40,bottom:30},
    xAxis:{type:'category',data:s.labels},
    yAxis:[{type:'value',name:'事件数'},{type:'value',min:0,max:100,axisLabel:{formatter:'{value}%'}}],
    series:[
      {name:'共振事件数',type:'bar',data:s.n,itemStyle:{color:C.sky},barWidth:26,label:{show:true,position:'top',fontSize:10}},
      {name:'T+10 胜率',type:'line',yAxisIndex:1,data:s.win10,lineStyle:{width:2.5,color:C.verm},itemStyle:{color:C.verm},symbolSize:8,label:{show:true,fontSize:10,formatter:p=>p.value+'%'}},
      {name:'支撑击穿率',type:'line',yAxisIndex:1,data:s.break_rate,lineStyle:{width:2.5,type:'dashed',color:C.teal},itemStyle:{color:C.teal},symbolSize:8,label:{show:true,fontSize:10,formatter:p=>p.value+'%'}}
    ]
  });
})();

// 2.3 年度
(function(){
  const y = DATA.year;
  echarts.init(document.getElementById('ch_year')).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['事件数','T+10 均值','T+10 胜率']},
    grid:{left:44,right:52,top:40,bottom:30},
    xAxis:{type:'category',data:y.labels,axisLabel:{fontSize:10}},
    yAxis:[{type:'value',name:'n / 均值%'},{type:'value',min:0,max:100,axisLabel:{formatter:'{value}%'}}],
    series:[
      {name:'事件数',type:'bar',data:y.n,itemStyle:{color:'#d8dee6'},barWidth:16,label:{show:true,position:'top',fontSize:9}},
      {name:'T+10 均值',type:'bar',data:y.mean10,itemStyle:{color:p=>p.value>=0?'rgba(213,94,0,.75)':'rgba(0,158,115,.75)'},barWidth:8},
      {name:'T+10 胜率',type:'line',yAxisIndex:1,data:y.win10,lineStyle:{width:2,color:C.blue},itemStyle:{color:C.blue},symbolSize:6}
    ]
  });
})();

// 3.1 VIX / 宏观
(function(){
  const d = DATA.filters.macro.filter(x=>x.name.indexOf('VIX')===0||x.name.indexOf('SPY5日')===0);
  echarts.init(document.getElementById('ch_vix')).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['T+10 胜率','支撑击穿率','T+10 均值']},
    grid:{left:48,right:52,top:40,bottom:36},
    xAxis:{type:'category',data:d.map(x=>x.name+'\\nn='+x.n),axisLabel:{fontSize:10}},
    yAxis:[{type:'value',min:0,max:100,axisLabel:{formatter:'{value}%'}},{type:'value',axisLabel:{formatter:'{value}%'}}],
    series:[
      {name:'T+10 胜率',type:'bar',data:d.map(x=>x.win10),itemStyle:{color:C.verm},barWidth:20},
      {name:'支撑击穿率',type:'bar',data:d.map(x=>x.break_rate),itemStyle:{color:C.teal},barWidth:20},
      {name:'T+10 均值',type:'line',yAxisIndex:1,data:d.map(x=>x.mean10),lineStyle:{width:2.5,type:'dashed',color:C.purple},itemStyle:{color:C.purple},label:{show:true,formatter:p=>p.value+'%',fontSize:10}}
    ]
  });
})();

// 3.3 ETF 量能
(function(){
  const d = DATA.filters.etf_vol;
  echarts.init(document.getElementById('ch_etfvol')).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['T+5 胜率','T+10 胜率','T+10 均值']},
    grid:{left:48,right:52,top:40,bottom:30},
    xAxis:{type:'category',data:d.map(x=>x.name+'\\nn='+x.n)},
    yAxis:[{type:'value',min:0,max:100,axisLabel:{formatter:'{value}%'}},{type:'value',axisLabel:{formatter:'{value}%'}}],
    series:[
      {name:'T+5 胜率',type:'bar',data:d.map(x=>x.win5),itemStyle:{color:C.sky},barWidth:22},
      {name:'T+10 胜率',type:'bar',data:d.map(x=>x.win10),itemStyle:{color:C.verm},barWidth:22},
      {name:'T+10 均值',type:'line',yAxisIndex:1,data:d.map(x=>x.mean10),lineStyle:{width:2.5,type:'dashed',color:C.purple},itemStyle:{color:C.purple},label:{show:true,formatter:p=>p.value+'%',fontSize:10}}
    ]
  });
})();

// 4.2 止损热力
(function(){
  const g = DATA.stop_grid;
  const stops = [...new Set(g.map(x=>x.stop))];
  const tps = [...new Set(g.map(x=>x.tp))].map(t=>t==='tphold%'?'持有到期':t.replace('tp',''));
  const vals = g.map(x=>[stops.indexOf(x.stop), tps.indexOf(x.tp==='tphold%'?'持有到期':x.tp.replace('tp','')), x.mean]);
  echarts.init(document.getElementById('ch_stop')).setOption({
    tooltip:{formatter:p=>{const v=p.value[2];const tpName=tps[p.value[1]];return '止损'+stops[p.value[0]]+' × '+(tpName==='持有到期'?'持有到期':'止盈'+tpName)+'<br/>均值 '+(v==null?'—':v+'%');}},
    grid:{left:70,right:20,top:30,bottom:60},
    xAxis:{type:'category',data:stops,name:'止损（带下沿下方）',nameLocation:'middle',nameGap:28},
    yAxis:{type:'category',data:tps},
    visualMap:{min:-1.1,max:0.0,calculable:true,orient:'horizontal',left:'center',bottom:0,itemWidth:12,itemHeight:90,
      inRange:{color:[C.teal,'#f2f4f7','#f3d1b8']},text:['优','劣'],textStyle:{fontSize:10}},
    series:[{type:'heatmap',data:vals,label:{show:true,formatter:p=>p.value[2]==null?'—':p.value[2]+'%'},
      itemStyle:{borderColor:'#fff',borderWidth:2}}]
  });
})();

// 五、画廊（K线 + ETF趋势线 + VIX）
(function(){
  const box = document.getElementById('gallery');
  DATA.gallery.forEach((g,gi)=>{
    const fig = document.createElement('div'); fig.className='fig';
    const clsColor = {'V型反转':C.verm,'支撑击穿':C.teal,'死猫反弹':C.orange,'横盘消化':C.grey}[g.cls]||C.grey;
    const vixTag = g.vix_at_signal!=null ? ' ｜ VIX '+g.vix_at_signal : '';
    fig.innerHTML = '<div class="ft">'+g.pair+' · '+g.date+' <span style="color:'+clsColor+'">['+g.cls+']</span></div>'+
      '<div class="fs">支撑：'+g.support_kinds.join('+')+' 带 ['+fmt(g.support_band_lo,'')+'~'+fmt(g.support_band_hi,'')+'] ｜ 入场 '+g.entry+vixTag+' ｜ T+5 '+fmt(g.fwd5,'%')+' T+10 '+fmt(g.fwd10,'%')+' T+20 '+fmt(g.fwd20,'%')+
      (g.broken_day?(' ｜ <b style="color:'+C.teal+'">第'+g.broken_day+'日击穿</b>'):' ｜ 支撑守住')+'</div>'+
      '<div class="chart k" id="gk_'+gi+'"></div>';
    box.appendChild(fig);
    const etfClose = new Map(g.etf_close); const etfLine = new Map(g.etf_line); const vixMap = new Map(g.vix);
    const etfCloseArr = g.dates.map(d=>etfClose.has(d)?etfClose.get(d):null);
    const etfLineArr = g.dates.map(d=>etfLine.has(d)?etfLine.get(d):null);
    const vixArr = g.dates.map(d=>vixMap.has(d)?vixMap.get(d):null);
    const evIdx = g.dates.indexOf(g.date);
    const supKinds = g.support_kinds.join('+');
    echarts.init(document.getElementById('gk_'+gi)).setOption({
      animation:false,
      tooltip:{trigger:'axis',axisPointer:{type:'cross'}},
      axisPointer:{link:[{xAxisIndex:'all'}]},
      grid:[{left:52,right:'52%',top:22,bottom:'36%'},{left:'56%',right:14,top:22,bottom:'70%'},
            {left:'56%',right:14,top:'42%',bottom:22}],
      xAxis:[
        {type:'category',data:g.dates,gridIndex:0,axisLabel:{fontSize:9,rotate:45,interval:14}},
        {type:'category',data:g.dates,gridIndex:1,show:false},
        {type:'category',data:g.dates,gridIndex:2,axisLabel:{fontSize:9,rotate:45,interval:14}}
      ],
      yAxis:[
        {scale:true,gridIndex:0,splitLine:{lineStyle:{color:'#eef0f3'}},axisLabel:{fontSize:9}},
        {scale:true,gridIndex:1,splitLine:{lineStyle:{color:'#eef0f3'}},axisLabel:{fontSize:9},name:'ETF',nameTextStyle:{fontSize:9}},
        {scale:true,gridIndex:2,splitLine:{lineStyle:{color:'#eef0f3'}},axisLabel:{fontSize:9},name:'VIX',nameTextStyle:{fontSize:9}}
      ],
      series:[
        {name:g.pair.split('/')[1]+' K线',type:'candlestick',data:g.ohlc,
          itemStyle:{color:C.verm,color0:C.teal,borderColor:C.verm,borderColor0:C.teal},
          markLine:{silent:true,symbol:'none',
            data:[
              {yAxis:g.support,lineStyle:{color:C.purple,type:'dashed',width:1.6},label:{formatter:'支撑 '+g.support+' ('+supKinds+')',fontSize:9,color:C.purple,position:'insideStartTop'}},
              {xAxis:evIdx,lineStyle:{color:'#b45309',type:'solid',width:1},label:{formatter:'信号日',fontSize:9,color:'#b45309'}}
            ]},
          markArea: g.support_band_lo!=null ? {silent:true,itemStyle:{color:'rgba(230,159,0,.12)'},
            data:[[{yAxis:g.support_band_lo},{yAxis:g.support_band_hi}]]} : undefined,
          markPoint:{symbolSize:12,data:[{coord:[evIdx,g.entry],value:'◆',itemStyle:{color:'#b45309'},label:{show:true,formatter:'◆入场',fontSize:9,color:'#b45309',position:'right'}}]}
        },
        {name:g.pair.split('/')[0]+' 收盘',type:'line',xAxisIndex:1,yAxisIndex:1,data:etfCloseArr,showSymbol:false,lineStyle:{width:1.6,color:'#374151'},
          markPoint:{symbolSize:11,data:[{coord:[evIdx,etfCloseArr[evIdx]],value:'▼',itemStyle:{color:C.teal},symbol:'triangle',symbolRotate:180,label:{show:true,formatter:'破位',fontSize:9,color:C.teal,position:'bottom'}}]}},
        {name:'上升趋势线',type:'line',xAxisIndex:1,yAxisIndex:1,data:etfLineArr,showSymbol:false,lineStyle:{width:2,color:C.blue,type:'solid'}},
        {name:'VIX',type:'line',xAxisIndex:2,yAxisIndex:2,data:vixArr,showSymbol:false,lineStyle:{width:1.8,color:C.orange},
          areaStyle:{color:'rgba(230,159,0,.10)'},
          markLine:{silent:true,symbol:'none',data:[
            {yAxis:20,lineStyle:{color:C.grey,type:'dotted',width:1},label:{formatter:'20',fontSize:8,color:C.grey}},
            {yAxis:30,lineStyle:{color:C.verm,type:'dotted',width:1},label:{formatter:'30',fontSize:8,color:C.verm}},
            {xAxis:evIdx,lineStyle:{color:'#b45309',type:'solid',width:1},label:{show:false}}
          ]},
          markPoint: g.vix_at_signal!=null ? {symbolSize:10,data:[{coord:[evIdx,vixArr[evIdx]],symbol:'circle',itemStyle:{color:'#b45309'},label:{show:true,formatter:g.vix_at_signal,fontSize:9,color:'#b45309',position:'top'}}]} : undefined
        }
      ]
    });
  });
})();
window.addEventListener('resize',()=>{document.querySelectorAll('[id^=ch_],[id^=gk_]').forEach(el=>{const c=echarts.getInstanceByDom(el);if(c)c.resize();});});
</script>
</body>
</html>
"""

# ---------- 统计行 ----------
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
        f"<td class='dn nowrap'>{a['maxDD_p10']:+.2f}%</td></tr>")

# 3.2 形态行
def shadow_row(name, seg):
    s = seg.get("stats") or {}
    t1, t5, t10 = (s.get("1") or {}), (s.get("5") or {}), (s.get("10") or {})
    return (f"<tr><td>{name}</td><td class='nowrap'>{seg['n']}</td>"
            f"<td class='nowrap'>{t1.get('win')}%</td><td class='nowrap'>{t5.get('win')}%</td>"
            f"<td class='nowrap'>{t10.get('mean')}% / {t10.get('win')}%</td></tr>")
shadow_rows = [
    shadow_row("下影线占比 ≥0.3（盘中下探后收回）", fl["stk_shadow"]),
    shadow_row("下影线占比 &lt;0.3", fl["stk_no_shadow"]),
    shadow_row("个股量比 ≤1.0（缩量触及）", fl["stk_low_vol"]),
    shadow_row("个股量比 &gt;1.0（放量触及）", fl["stk_high_vol"]),
]

# 4.1 击穿环境行（全部来自数据）
mac = fl["macro"]
def _br(name):
    return (mac.get(name) or {}).get("break_rate")
break_rows = [
    ("<b>全样本</b>", 21, fl["break_rate_all"], "共振信号的基准击穿风险（收盘跌破带下沿）"),
    ("科技 XLK 破位", 5, br_sector.get("XLK"), "⚠ 最差：高位横盘支撑，破位后趋势性失守"),
    ("VIX &lt;20（低波动阴跌）", 11, _br("VIX<20"), "⚠ 趋势性走弱，支撑被缓慢磨穿"),
    ("VIX 20~30（中等波动）", 5, _br("VIX 20-30"), "样本小；T+10 均值 −6.26% 为最差环境（受个别深跌拖累）"),
    ("VIX ≥30（恐慌宣泄）", 5, _br("VIX>=30(恐慌)"), "击穿率不高且反弹兑现快，唯一正期望环境"),
    ("SPY 5 日跌 &gt;3%（市场急跌）", 5, _br("SPY5日跌>3%(市场急跌)"), "急跌组 T+10 胜率 80%（n=5，方向参考）"),
    ("医疗 XLV 破位", 8, br_sector.get("XLV"), "防御属性，击穿率最低且 T+10 均值为正"),
    ("金融 XLF 破位", 5, br_sector.get("XLF"), "击穿率好于预期，但 T+10 均值仍为负"),
    ("工业 XLI 破位", 2, br_sector.get("XLI"), "样本仅 2 且全击穿，方向参考"),
    ("必选 XLP 破位", 1, br_sector.get("XLP"), "样本不足，不作结论"),
]
br_html = []
for name, n, br, note in break_rows:
    br_html.append(f"<tr><td>{name}</td><td class='nowrap'>{n}</td>"
                   f"<td class='nowrap'><b>{'—' if br is None else str(br)+'%'}</b></td>"
                   f"<td class='note2'>{note}</td></tr>")

n_break = sum(v["break_only"] for v in D["pair_meta"].values())
n_touch = sum(v["touch_only"] for v in D["pair_meta"].values())

html = HTML
html = html.replace("__SECTOR_ROWS__", "".join(sector_rows))
html = html.replace("__EV_ROWS__", "".join(ev_rows))
html = html.replace("__STOP_ROWS__", "".join(stop_rows))
html = html.replace("__STAT_ROWS__", "".join(stat_rows))
html = html.replace("__SHADOW_ROWS__", "".join(shadow_rows))
html = html.replace("__QUALITY_ROWS__", "".join(quality_rows))
html = html.replace("__BREAK_ROWS__", "".join(br_html))
html = html.replace("__NBREAK__", str(n_break))
html = html.replace("__NTOUCH__", str(n_touch))
html = html.replace("__NCT__", str(ct["1"]["n"]))
html = html.replace("__NCB__", str(cb["1"]["n"]))
html = html.replace("__NBL__", str(bl["1"]["n"]))
# 内联 ECharts（自包含、离线可用）
with open(os.path.join(ROOT, "scripts", "lib", "echarts.min.js"), encoding="utf-8") as f:
    html = html.replace("__ECHARTS_LIB__", f.read())
html = html.replace("__DATA_JSON__", json.dumps(js_data, ensure_ascii=False, separators=(",", ":")))

os.makedirs(OUTD, exist_ok=True)
out = os.path.join(OUTD, "djia_sector_support_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out} size={os.path.getsize(out)//1024}KB")
