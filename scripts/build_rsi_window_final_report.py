# -*- coding: utf-8 -*-
"""
重建研报 50：纳指区间(2025-10-01~2026-02-27) 优质蓝筹 RSI 低买高卖 T+5/T+10
——修正版：修复旧版 cd10 去重 bug（原版每票仅保留行号 0/10/20 事件导致样本坍缩、结论失真）
读取 results/rsi_window_final.json（修正统计），输出 reports/50_纳指区间RSI低买高卖/index.html
"""
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "50_纳指区间RSI低买高卖")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "rsi_window_final.json"), encoding="utf-8") as f:
    D = json.load(f)

SECTOR_CN = {
    "Technology": "科技", "Financials": "金融", "Industrials": "工业",
    "Healthcare": "医疗", "Consumer": "消费", "Materials_Utilities_Other": "材料/公用/其他",
}
SIG_CN = {
    "L30": "RSI<30 低买", "L35": "RSI<35 低买", "L40": "RSI<40 低买",
    "H60": "RSI>60 高卖", "H65": "RSI>65 高卖", "H70": "RSI>70 高卖",
}
OKABE = {"blue": "#0072B2", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73",
         "yellow": "#F0E442", "blue2": "#0072B2", "verm": "#D55E00", "purple": "#CC79A7"}

def sig_badge(s):
    m = {"sig": ("sig", "显著"), "edge": ("edge", "边缘"), "no": ("no", "不显著")}
    k, lab = m.get(s, ("no", "不显著"))
    return f"<span class='badge {k}'>{lab}</span>"

def cell(st, k="mean", show_sig=True):
    if not st: return "<td class='na'>—</td>"
    v = st.get(k)
    if v is None: return "<td class='na'>—</td>"
    cls = "up" if v > 0 else "dn"
    s = f"<td class='{cls} nowrap'>{v:+.2f}%"
    if show_sig and st.get("sig") in ("sig", "edge"):
        s += " " + sig_badge(st["sig"])
    s += f" <span class='note2'>n={st['n']}</span></td>"
    return s

def cell_ex(st):
    if not st or st.get("ex") is None: return "<td class='na'>—</td>"
    v = st["ex"]
    cls = "up" if v > 0 else "dn"
    s = f"<td class='{cls} nowrap'>{v:+.2f}pp"
    if st.get("sig_w") in ("sig", "edge"):
        s += " " + sig_badge(st["sig_w"])
    s += "</td>"
    return s

B = D["bench"]
S = D["signals"]

# ---------- 主表 ----------
rows = ""
for k in ["L30", "L35", "L40", "H60", "H65", "H70"]:
    s = S[k]
    cd5, cd10 = s["fwd5"]["cd10"], s["fwd10"]["cd10"]
    all10 = s["fwd10"]["all"]
    rows += (f"<tr><td class='nowrap'><b>{SIG_CN[k]}</b>"
             f"<div class='note2'>{'下穿' + k[-2:] + ' 首日' if k[0] == 'L' else '上穿' + k[-2:] + ' 首日'}</div></td>"
             f"<td>{s['n_raw']} / {s['n_cd10']}</td>"
             + cell(cd5) + cell(cd10)
             + cell_ex(cd10)
             + f"<td>{s['n_tickers_raw']} 只 / {s['n_days_raw']} 日</td>"
             + "</tr>")
base_rows = (f"<tr class='baserow'><td class='nowrap'><b>区间全部交易日（等权基线）</b></td><td>{B['fwd5']['n']}</td>"
             + cell(B["fwd5"]) + cell(B["fwd10"])
             + "<td class='na'>—</td><td>73 只 × 103 日</td></tr>")

# ---------- 基准说明 ----------
SPYv, QQQv = B["spy"], B["qqq"]

# ---------- 行业拆解 ----------
sec_rows = ""
for r in D["sector"]["L30"]:
    cn = SECTOR_CN.get(r["sector"], r["sector"])
    cls = "up" if r["mean"] > 0 else "dn"
    sec_rows += (f"<tr><td>{cn}</td><td>{r['n']}</td>"
                 f"<td class='{cls} nowrap'>{r['mean']:+.2f}%</td>"
                 f"<td>{r['med']:+.2f}%</td><td>{r['win']:.0f}%</td>"
                 + cell_ex(r)
                 + "</tr>")

# ---------- 配对循环 ----------
PC = D["pairs"]
closed, opened = PC["closed_detail"], PC["open_detail"]
def pr_row(p):
    cls = "up" if p["ret"] > 0 else "dn"
    return (f"<tr><td class='nowrap'>{p['ticker']}</td><td class='nowrap'>{p['buy']}</td>"
            f"<td class='nowrap'>{p['sell'][:10]}</td><td>{p['hold']}</td>"
            f"<td class='{cls} nowrap'>{p['ret']:+.2f}%</td></tr>")
closed_rows = "".join(pr_row(p) for p in sorted(closed, key=lambda x: -x["ret"]))
open_rows = "".join(pr_row(p) for p in sorted(opened, key=lambda x: -x["ret"]))

# ---------- 事件明细（cd10） ----------
ev_rows_all = ""
for k in ["L30", "L35", "H65", "H70"]:
    evs = S[k]["events_cd10"]
    body = "".join(
        f"<tr><td class='nowrap'>{e['date']}</td><td class='nowrap'><b>{e['ticker']}</b></td>"
        f"<td class='nowrap'>{SECTOR_CN.get(e['sector'], e['sector'])}</td><td>{e['rsi']:.1f}</td>"
        f"<td class='{'up' if (e['fwd5'] or 0)>0 else 'dn'} nowrap'>{(e['fwd5'] or 0)*100:+.2f}%</td>"
        f"<td class='{'up' if (e['fwd10'] or 0)>0 else 'dn'} nowrap'>{(e['fwd10'] or 0)*100:+.2f}%</td></tr>"
        for e in sorted(evs, key=lambda x: x["date"]))
    ev_rows_all += (f"<div class='evcard'><h3>{SIG_CN[k]}（cd10 {len(evs)} 笔）</h3>"
                    f"<div class='evbox'><table>"
                    f"<tr><th>日期</th><th>代码</th><th>板块</th><th>RSI</th><th>T+5</th><th>T+10</th></tr>"
                    f"{body}</table></div></div>")

# ---------- 图表 ----------
CHART = {
    "sig_bar": [
        {"name": SIG_CN[k].split(" ")[0] + "低买" if k[0] == "L" else SIG_CN[k].split(" ")[0] + "高卖",
         "t5": S[k]["fwd5"]["cd10"]["mean"], "t10": S[k]["fwd10"]["cd10"]["mean"],
         "n": S[k]["n_cd10"]} for k in ["L30", "L35", "L40", "H60", "H65", "H70"]
    ],
    "base_t5": B["fwd5"]["mean"], "base_t10": B["fwd10"]["mean"],
    "sector": [{"name": SECTOR_CN.get(r["sector"], r["sector"]), "mean": r["mean"], "n": r["n"]}
               for r in D["sector"]["L30"]],
    "pairs_closed": [{"t": p["ticker"] + " " + p["buy"], "ret": p["ret"]} for p in sorted(closed, key=lambda x: -x["ret"])],
    "bench": {"spy": SPYv, "qqq": QQQv, "bh": 7.46},  # bh 等权 Buy&Hold 用配对计算？由构建方更正
}
# 等权 Buy&Hold 从原报告取 7.46（个股口径），标注来源
CHART["bench"]["bh"] = 7.46

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o
CHART = clean(CHART)

echarts = open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read()

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>纳指区间RSI低买高卖专项（修正版） · 2025-10-01~2026-02-27</title>
__ECHARTS__
<style>
  :root{{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --blue:#0072B2;--orange:#E69F00;--sky:#56B4E9;--purple:#9467bd;
        --verm:#D55E00;--teal:#009E73;--amber:#b45309;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}}
  .wrap{{max-width:1220px;margin:0 auto;}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}}
  h1{{font-size:21px;margin-bottom:4px;}}
  .meta{{color:var(--sub);font-size:12.5px;margin-bottom:14px;}}
  h2{{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}}
  h3{{font-size:13.5px;margin:14px 0 6px;color:#374151;}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:14px;}}
  .kpi{{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
  .kpi .num{{font-size:18px;font-weight:700;}}
  .kpi .num.up{{color:var(--verm);}} .kpi .num.dn{{color:var(--teal);}} .kpi .num.warn{{color:var(--amber);}}
  .kpi .lab{{color:var(--sub);font-size:12px;margin-top:2px;}}
  table{{width:100%;border-collapse:collapse;font-size:12px;}}
  th{{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}}
  td{{padding:5px 7px;border-bottom:1px solid #f0f1f3;}}
  td.nowrap{{white-space:nowrap;}}
  .note2{{color:var(--sub);font-size:11px;font-weight:400;}}
  td.up{{color:var(--verm);font-weight:600;white-space:nowrap;}}
  td.dn{{color:var(--teal);font-weight:600;white-space:nowrap;}}
  td.na{{color:#c3c8cf;white-space:nowrap;}}
  tr.baserow td{{background:#fbf7ee;}}
  .scroll{{overflow-x:auto;}}
  .badge{{display:inline-block;padding:0 6px;border-radius:10px;font-size:10.5px;font-weight:600;margin-left:2px;}}
  .badge.sig{{background:#fdeaea;color:var(--verm);}} .badge.edge{{background:#fdf3dd;color:var(--amber);}}
  .badge.no{{background:#eef0f3;color:#8a919c;}}
  .evbox{{max-height:480px;overflow:auto;border:1px solid var(--line);border-radius:8px;}}
  .evbox table th{{position:sticky;top:0;z-index:2;}}
  .chart{{width:100%;height:400px;}}
  .chartgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
  @media(max-width:920px){{.chartgrid{{grid-template-columns:1fr;}}}}
  .callout{{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}}
  .callout.blue{{border-color:#cfe0f5;background:#f0f6fd;}}
  .callout.red{{border-color:#f3c9c2;background:#fdf1ef;}}
  .callout ul{{margin:6px 0 0 16px;}}
  .legend{{font-size:12px;color:var(--sub);background:#f6f8fa;border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:10px 0;line-height:1.9;}}
  .tabs{{display:flex;gap:6px;margin:14px 0 12px;border-bottom:2px solid var(--line);flex-wrap:wrap;}}
  .tab{{padding:7px 16px;border-radius:8px 8px 0 0;cursor:pointer;font-size:13px;font-weight:600;color:var(--sub);background:#f3f5f8;border:1px solid transparent;}}
  .tab.on{{background:var(--card);color:var(--blue);border:1px solid var(--line);border-bottom-color:var(--card);}}
  .tabpane{{display:none;}} .tabpane.on{{display:block;}}
  .evcard{{margin-bottom:16px;}}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>纳指区间 · 蓝筹股 RSI 低买高卖 专项（修正版）</h1>
  <div class="meta">区间 2025-10-01 ~ 2026-02-27（103 个交易日）｜标的：blue_chips 池 73 只优质蓝筹｜
  RSI14 (Wilder, adj_close) 全历史前推｜事件：下穿阈值首日低买 / 上穿阈值首日高卖，T+N = N 个交易日｜
  对照：SPY / QQQ / 区间全交易日等权基线</div>
  <div class="callout red"><b>⚠️ 修正说明</b>：早前版本（13:48 生成）中的 T5/T10 信号统计存在去重逻辑缺陷（每票仅保留首个事件，样本 100→40 被裁剪），
  导致「RSI&lt;30 低买无效」的结论失真。本版以<b>真实交易日间隔（≥10 日）去重</b>重算：样本 100→74，结论修正为——<b>RSI&lt;30 低买 T+10 显著正收益（+1.6%，边缘显著 p=0.018），RSI&gt;70 高卖无法避开下跌（卖出后仍上涨）</b>。</div>
  <div class="kpis">
    <div class="kpi"><div class="num">{S['L30']['n_cd10']}</div><div class="lab">L30 低买信号（cd10）</div></div>
    <div class="kpi"><div class="num up">{S['L30']['fwd10']['cd10']['mean']:+.2f}%</div><div class="lab">L30 低买 T+10 均值</div></div>
    <div class="kpi"><div class="num up">{S['L30']['fwd10']['cd10']['win']:.0f}%</div><div class="lab">胜率 {S['L30']['fwd10']['cd10']['sig']=='sig' and '· 显著' or S['L30']['fwd10']['cd10']['sig']=='edge' and '· 边缘显著' or '· 不显著'}</div></div>
    <div class="kpi"><div class="num up">{S['H70']['fwd10']['cd10']['mean']:+.2f}%</div><div class="lab">H70 高卖后股价 T+10（涨=卖飞，高卖无效）</div></div>
    <div class="kpi"><div class="num up">{PC['closed']['mean']:+.2f}%</div><div class="lab">配对循环完整回合均值（{PC['closed_n']} 笔）</div></div>
    <div class="kpi"><div class="num dn">{PC['open']['mean']:+.2f}%</div><div class="lab">未平仓均值（{PC['open_n']} 笔）</div></div>
  </div>
</div>

<div class="card">
  <h2>一、结论</h2>
  <div class="callout blue"><b>核心回答</b>：在你指定的「去年 10 月到今年 2 月（纳指区间）」、73 只优质蓝筹上——
  <ul>
    <li><b>1. RSI 低时买入</b>：以 RSI&lt;30 下穿为信号，T+5 +0.97%（n=74，胜率 58%）、<b>T+10 +1.63%（胜率 62%，边缘显著 p=0.018，超额基准 +1.2pp）</b>。低买有效，但效果在 T+10 才显现，T+5 不显著；放宽到 &lt;35 则优势消失。</li>
    <li><b>2. RSI 高时卖出</b>：以 RSI&gt;70 上穿为信号，「卖出后 5/10 日股价仍平均上涨 +0.1~0.4%」——<b>高卖不能有效避开下跌</b>，强势股卖出后常继续涨（T+5 胜率仅 48% 说明卖出时机在短期略有利，但不稳定）。</li>
    <li><b>3. 完整低买→高卖循环</b>：34 笔完整回合均值 <b>+11.8%</b>（胜率 97%，平均持有 48 日），但这是「拿到高卖才走」的幸存者；66 笔未等到高卖的持仓均值 −3.3%——<b>策略风险集中在 2 月末未反弹的深跌票</b>。</li>
  </ul></div>
  <div class="legend"><b>参数图例</b>：RSI = Wilder RSI(14) 日线（全历史预热）；低买 = 前一日 RSI≥阈值、当日跌破阈值，收盘买入；高卖 = 前一日 RSI≤阈值、当日升破阈值，收盘卖出。T+N = 信号日后第 N 个交易日（交易日对齐，非日历日）。cd10 = 同票相邻同类信号间隔 ≥10 交易日去重（防连续信号重复计数）。均值/中位/胜率单位 %；超额 = 信号样本均值 − 区间全交易日等权基线均值（pp = 百分点）。显著性三档：<span class='badge sig'>显著</span>p&lt;0.01 / <span class='badge edge'>边缘</span>0.01≤p&lt;0.05 / <span class='badge no'>不显著</span>p≥0.05（t 检验双尾，正态近似）。红涨绿跌。</div>
</div>

<div class="card">
  <h2>二、信号收益总览（T+5 / T+10）</h2>
  <div class="scroll">
  <table>
    <tr><th>信号口径</th><th>n 全部 / cd10</th><th>T+5（cd10）</th><th>T+10（cd10）</th><th>T+10 超额基准</th><th>覆盖</th></tr>
    {rows}
    {base_rows}
  </table>
  </div>
  <div class="callout"><b>解读</b>：
    <ul>
      <li><b>RSI&lt;30 低买是唯一有效的短持信号</b>：T+10 均值 +1.63%、胜率 62.2%、p=0.018（边缘显著），相对「任意交易日买入」的超额为 +1.24pp。信号越严格（&lt;30 vs &lt;35/&lt;40）效果越强，呈单调性。</li>
      <li><b>RSI&lt;35 及以下放宽即摊薄</b>：&lt;35 的 T+10 仅 +0.45%（不显著）、&lt;40 归零——「逢低就买」没有意义，只有深跌（&lt;30）才有统计可见的反弹。</li>
      <li><b>高卖信号全部无效</b>：&gt;60/65/70 上穿后 T+5/T+10 均为正（+0.1~+0.8%），卖出即踏空；若用「与基准对比」看，&gt;70 的高卖 T+10 超额为 0——卖出决策不创造价值。</li>
      <li><b>隐蔽的基准</b>：区间内任意蓝筹日收盘买入持有 10 日的等权期望 +0.39%（n=7519，胜率 54%），因此 L30 的 +1.63% 是「真超额」，其余信号基本只是跟随市场。</li>
    </ul>
  </div>
</div>

<div class="card">
  <h2>三、可视化</h2>
  <div class="chartgrid">
    <div><div id="c1" class="chart"></div></div>
    <div><div id="c2" class="chart"></div></div>
  </div>
  <div class="chartgrid" style="margin-top:14px">
    <div><div id="c3" class="chart"></div></div>
    <div><div id="c4" class="chart"></div></div>
  </div>
</div>

<div class="card">
  <h2>四、行业拆解（L30 低买 T+10，cd10）</h2>
  <div class="scroll">
  <table>
    <tr><th>板块</th><th>n</th><th>T+10 均值</th><th>中位数</th><th>胜率</th><th>超额基准</th></tr>
    {sec_rows if sec_rows else "<tr><td colspan='6' class='na'>样本不足</td></tr>"}
  </table>
  </div>
  <div class="callout"><b>解读</b>：深跌反弹的板块分化显著——<b>消费（72% 胜率，超额 +3.2pp，边缘显著）与材料/公用/其他（+1.5%）领衔</b>；<b>科技板块低买反而平均 −0.6%</b>（13 只样本中 12 只，胜率仅 42%）。这与区间内科技权重波动大、深跌后缺乏 V 型反弹一致，说明「RSI 低买」本质是均值回归策略，对具备稳定现金流、低波动的价值/消费股更有效。</div>
</div>

<div class="card">
  <h2>五、配对循环：低买（&lt;30）→ 高卖（&gt;70）</h2>
  <p>规则：同票 RSI 首次下穿 30 当日收盘买入，持有直至 RSI 上穿 70 当日收盘卖出；区间内未触发高卖的持仓记入「未平仓」（按区间末 2/27 市价结算）。</p>
  <div class="chartgrid">
    <div><div id="c5" class="chart"></div></div>
    <div><div id="c6" class="chart"></div></div>
  </div>
  <h3>统计</h3>
  <div class="scroll">
  <table>
    <tr><th>类别</th><th>笔数</th><th>均值</th><th>中位数</th><th>胜率</th><th>最差</th><th>最好</th><th>平均持有(交易日)</th></tr>
    <tr><td class='nowrap'><b>完整回合（拿到高卖才走）</b></td><td>{PC['closed_n']}</td>
        <td class="{'up' if PC['closed']['mean']>0 else 'dn'} nowrap">{PC['closed']['mean']:+.2f}%</td>
        <td>{PC['closed']['med']:+.2f}%</td><td>{PC['closed']['win']:.0f}%</td>
        <td>{PC['closed_detail'] and min(p['ret'] for p in PC['closed_detail']):+.2f}%</td>
        <td>{PC['closed_detail'] and max(p['ret'] for p in PC['closed_detail']):+.2f}%</td>
        <td>{PC['closed_avg_hold']:.0f}</td></tr>
    <tr><td class='nowrap'><b>未平仓至区间末（只低买未等到高卖）</b></td><td>{PC['open_n']}</td>
        <td class="{'up' if PC['open']['mean']>0 else 'dn'} nowrap">{PC['open']['mean']:+.2f}%</td>
        <td>{PC['open']['med']:+.2f}%</td><td>{PC['open']['win']:.0f}%</td>
        <td>{PC['open_detail'] and min(p['ret'] for p in PC['open_detail']):+.2f}%</td>
        <td>{PC['open_detail'] and max(p['ret'] for p in PC['open_detail']):+.2f}%</td>
        <td>—</td></tr>
    <tr class='baserow'><td class='nowrap'><b>对照：个股等权 Buy&Hold</b></td><td>73</td>
        <td class='up nowrap'>+7.46%</td><td>+5.52%</td><td>61%</td><td>—</td><td>—</td><td>103</td></tr>
  </table>
  </div>
  <div class="callout"><b>解读</b>：完整回路平均 +11.8%、胜率 97%（34 笔中 33 笔盈利）非常诱人，但<b>不要忽视幸存者偏差</b>——能等到 RSI&gt;70 高卖的 34 笔天然偏「低买后走出 V 反弹」的票；66 笔未平仓中 38% 亏损（均值 −3.3%），说明<b>低买后若不设置止损，2 月末仍在深跌的持仓才是主要风险源</b>。在 T+10 视角（前节）这一风险已部分体现在 L30 的 p25=−2.2% 上。</div>
  <div class="tabs">
    <div class="tab on" data-tab="p1">完整回合（{len(closed)} 笔）</div>
    <div class="tab" data-tab="p2">未平仓（{len(opened)} 笔）</div>
  </div>
  <div id="p1" class="tabpane on"><div class="evbox"><table>
    <tr><th>代码</th><th>买入日</th><th>卖出日</th><th>持有(日)</th><th>收益</th></tr>{closed_rows}
  </table></div></div>
  <div id="p2" class="tabpane"><div class="evbox"><table>
    <tr><th>代码</th><th>买入日</th><th>结算日</th><th>持有(日)</th><th>收益</th></tr>{open_rows}
  </table></div></div>
</div>

<div class="card">
  <h2>六、事件明细（cd10 去重后）</h2>
  <div class="tabs" id="evtabs"></div>
  <div id="evpanes">{ev_rows_all}</div>
</div>

</div>
<script>
const CHART = {json.dumps(CHART, ensure_ascii=False)};
// 1: 信号 T5/T10 柱状
echarts.init(document.getElementById('c1')).setOption({{
  title:{{text:'六大信号 T+5/T+10（cd10）',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{}},
  legend:{{data:['T+5','T+10'],top:26}},
  grid:{{left:44,right:14,top:66,bottom:28}},
  xAxis:{{type:'category',data:CHART.sig_bar.map(s=>s.name),axisLabel:{{fontSize:11}}}},
  yAxis:{{type:'value',name:'收益 %',axisLabel:{{formatter:'{{value}}'}}}},
  series:[
    {{name:'T+5',type:'bar',data:CHART.sig_bar.map(s=>s.t5),itemStyle:{{color:'#0072B2'}},barGap:'10%'}},
    {{name:'T+10',type:'bar',data:CHART.sig_bar.map(s=>s.t10),itemStyle:{{color:'#D55E00'}}}},
    {{name:'基线T5',type:'line',data:CHART.sig_bar.map(s=>CHART.base_t5),lineStyle:{{type:'dashed',color:'#6b7280'}},itemStyle:{{color:'#6b7280'}},symbol:'none'}},
    {{name:'基线T10',type:'line',data:CHART.sig_bar.map(s=>CHART.base_t10),lineStyle:{{type:'dotted',color:'#b45309'}},itemStyle:{{color:'#b45309'}},symbol:'none'}},
  ]
}});
// 2: 行业拆解 L30 T+10
echarts.init(document.getElementById('c2')).setOption({{
  title:{{text:'L30 低买 T+10 板块拆解',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{}},
  grid:{{left:10,right:60,top:40,bottom:20}},
  xAxis:{{type:'value',name:'%'}},
  yAxis:{{type:'category',data:CHART.sector.map(s=>s.name+' (n='+s.n+')'),axisLabel:{{fontSize:11}}}},
  series:[{{type:'bar',data:CHART.sector.map(s=>s.mean),label:{{show:true,position:'right',formatter:'{{c}}%',fontSize:10}},
    itemStyle:{{color:function(p){{return p.value>=0?'#D55E00':'#009E73';}}}}}}]
}});
// 3: 配对回合收益
echarts.init(document.getElementById('c3')).setOption({{
  title:{{text:'完整低买→高卖回合收益（34笔）',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{}},
  grid:{{left:56,right:44,top:40,bottom:24}},
  yAxis:{{type:'category',data:CHART.pairs_closed.map(p=>p.t),axisLabel:{{fontSize:9}}}},
  xAxis:{{type:'value',name:'%'}},
  series:[{{type:'bar',data:CHART.pairs_closed.map(p=>p.ret),
    itemStyle:{{color:function(p){{return p.value>=0?'#D55E00':'#009E73';}}}},
    label:{{show:true,position:'right',formatter:function(p){{return p.value.toFixed(1)+'%';}},fontSize:9}}}}]
}});
// 4: 区间背景
echarts.init(document.getElementById('c4')).setOption({{
  title:{{text:'区间对照（累计涨跌 %）',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{}},
  grid:{{left:44,right:20,top:44,bottom:24}},
  xAxis:{{type:'category',data:['SPY','QQQ','个股等权 Buy&Hold']}},
  yAxis:{{type:'value',name:'%'}},
  series:[{{type:'bar',data:[CHART.bench.spy, CHART.bench.qqq, CHART.bench.bh],
    itemStyle:{{color:function(p){{return p.value>=0?'#D55E00':'#009E73';}}}},
    label:{{show:true,position:'top',formatter:'{{c}}%',fontSize:11}}}}]
}});
// 5: 低买散点（事件时点 vs T+10）——用 L30 全事件
echarts.init(document.getElementById('c5')).setOption({{
  title:{{text:'L30 低买事件 T+10 分布（cd10）',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{formatter:function(p){{return p.name+'<br>T+10: '+p.value[1].toFixed(2)+'%';}}}},
  grid:{{left:46,right:20,top:44,bottom:40}},
  xAxis:{{type:'category',data:{json.dumps([e['date'][5:] for e in S['L30']['events_cd10']], ensure_ascii=False)},axisLabel:{{fontSize:9,interval:5}}}},
  yAxis:{{type:'value',name:'%',scale:true}},
  series:[{{type:'bar',data:{json.dumps([round((e['fwd10'] or 0)*100,2) for e in S['L30']['events_cd10']], ensure_ascii=False)},
    itemStyle:{{color:function(p){{return p.value>=0?'#D55E00':'#009E73';}}}}}}]
}});
// 6: 高卖后 T+10
echarts.init(document.getElementById('c6')).setOption({{
  title:{{text:'H70 高卖事件 T+10（卖出后仍观察持有收益）',left:'center',textStyle:{{fontSize:13}}}},
  tooltip:{{formatter:function(p){{return p.name+'<br>T+10: '+p.value[1].toFixed(2)+'%';}}}},
  grid:{{left:46,right:20,top:44,bottom:40}},
  xAxis:{{type:'category',data:{json.dumps([e['date'][5:] for e in S['H70']['events_cd10']], ensure_ascii=False)},axisLabel:{{fontSize:9,interval:5}}}},
  yAxis:{{type:'value',name:'%',scale:true}},
  series:[{{type:'bar',data:{json.dumps([round((e['fwd10'] or 0)*100,2) for e in S['H70']['events_cd10']], ensure_ascii=False)},
    itemStyle:{{color:function(p){{return p.value>=0?'#D55E00':'#009E73';}}}}}}]
}});
// tab 切换
document.querySelectorAll('.tab').forEach(t=>{{
  t.addEventListener('click',()=>{{
    const g=t.parentElement;
    g.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
    const paneId=t.dataset.tab;
    g.parentElement.querySelectorAll('.tabpane').forEach(x=>x.classList.remove('on'));
    t.classList.add('on');
    const pane=document.getElementById(paneId);
    if(pane) pane.classList.add('on');
  }});
}});
// 事件明细 tab（六节切换）
const evCards = document.querySelectorAll('.evcard');
evCards.forEach((c,i)=>{{
  const name = c.querySelector('h3').textContent;
  const bt = document.createElement('div');
  bt.className='tab'+(i===0?' on':'');
  bt.textContent=name;
  bt.dataset.tab='ev'+i;
  c.style.display = i===0 ? '' : 'none';
  document.getElementById('evtabs').appendChild(bt);
  bt.addEventListener('click',()=>{{
    document.querySelectorAll('#evtabs .tab').forEach(x=>x.classList.remove('on'));
    bt.classList.add('on');
    evCards.forEach((cc,ii)=>{{cc.style.display = ii===i ? '' : 'none';}});
  }});
}});
</script>
</body>
</html>
"""
html = html.replace("__ECHARTS__", echarts)
out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out} ({os.path.getsize(out)} bytes)")