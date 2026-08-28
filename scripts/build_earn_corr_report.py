# -*- coding: utf-8 -*-
"""构建研报 53：SOFI / AFRM / UPST 财报交易日涨跌相关性
读取 results/earn_corr_sofi_afrm_upst/analysis.json
输出 reports/53_金融科技财报日相关性/index.html
浅底深字研报风 + ECharts + Okabe-Ito 色弱安全；红涨绿跌；R 与 β 同列；全部小数(0~1)。
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "earn_corr_sofi_afrm_upst")
OUTD = os.path.join(ROOT, "reports", "53_金融科技财报日相关性")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "analysis.json"), encoding="utf-8") as f:
    D = json.load(f)

META = D["meta"]
BASE = D["baseline"]["full_period"]
EVN = D["event_vs_non"]
BYE = D["by_earner"]
WIN = D["window"]
WB = D["window_base"]
BY = D["by_year"]
DUEV = D["dual_events"]

def cls(v):
    if v is None: return "na"
    return "up" if v > 0 else "dn"

def p_fmt(p):
    if p is None: return "—"
    if p < 0.001: return "&lt;0.001"
    return f"{p:.3f}"

def sig_cell(q):
    s = q.get("sig")
    if s == "sig": return "<td class='sig'>显著</td>"
    if s == "edge": return "<td style='color:#E69F00;font-weight:600'>边缘</td>"
    return "<td class='na'>—</td>"

def r3(x): return f"{x:.3f}" if x is not None else "—"

def b2(x): return f"{x:.2f}" if x is not None else "—"

PAIR_CN = {"SOFI~AFRM": "SOFI×AFRM", "SOFI~UPST": "SOFI×UPST", "AFRM~UPST": "AFRM×UPST"}
TK_CN = {"SOFI": "SOFI", "AFRM": "AFRM", "UPST": "UPST"}

# ---- 事件日 vs 非事件日 表格行 ----
ev_rows = []
for k, v in EVN.items():
    if k == "abs_ret": continue
    e, nv, zt = v["event_day"], v["non_event_day"], v["diff_test"]
    dtxt = f"z={zt['z']:.2f} (p={p_fmt(zt['p'])})" if zt else "—"
    rsq_txt = f"{e.get('rsq',0)*100:.0f}%" if e.get('rsq') else "—"
    ev_rows.append(
        f"<tr><td><b>{PAIR_CN[k]}</b></td>"
        f"<td class='{cls(e['r'])}'>{r3(e['r'])}</td><td>{r3(e['rho'])}</td>{sig_cell(e)}<td>{p_fmt(e.get('p'))}</td>"
        f"<td>{b2(e.get('beta'))}</td><td>{rsq_txt}</td>"
        f"<td class='{cls(nv['r'])}'>{r3(nv['r'])}</td><td>{b2(nv.get('beta'))}</td>"
        f"<td class='sig'>{dtxt}</td></tr>")
EV_ROWS = "\n".join(ev_rows)

# ---- 绝对波动放大 卡片 ----
ABS = EVN["abs_ret"]
def abs_card(tk):
    a = ABS[tk]
    return (f"<div class='kv'><div class='k'>{tk} 财报日 vs 非财报日 |波动|</div>"
            f"<div class='v'>{a['event_mean']:.1f}% <small>vs {a['non_mean']:.1f}%</small></div>"
            f"<div class='muted'>放大 <b>{a['amp']:.1f}×</b> · 中位数 {a['event_med']:.1f}% vs {a['non_med']:.1f}%</div></div>")

# ---- 按发报票分组 ----
grp_rows = []
for tk in ["SOFI", "AFRM", "UPST"]:
    g = BYE[tk]
    er = g["earner_ret"]
    ot_links = []
    for ot in ["SOFI", "AFRM", "UPST"]:
        if ot == tk: continue
        o = g["others"].get(ot)
        if not o: continue
        same = o["same_dir_pct"]
        ot_links.append(
            f"<td><b>{ot}</b><div class='tsub'>同向率 {same*100:.0f}% · β {b2(o.get('beta_on_earner',{}).get('beta')) if o.get('beta_on_earner') else '—'}</div></td>"
            f"<td class='{cls(o['mean_ret'])}'>{o['mean_ret']:+.2f}%</td>"
            f"<td class='{cls(o['med_ret'])}'>{o['med_ret']:+.2f}%</td>"
            f"<td>{o['abs_mean']:.1f}%</td>"
            f"<td class='{cls(o['corr_with_earner'].get('r'))}'>{r3(o['corr_with_earner'].get('r'))}</td>")
    grp_rows.append(
        f"<tr><td><b>{tk}</b><div class='tsub'>{g['n_days']} 个事件日</div></td>"
        f"<td>{er['win']*100:.0f}%</td>"
        f"<td class='{cls(er['mean'])}'>{er['mean']:+.2f}%</td>"
        f"<td>{er['abs_mean']:.1f}%</td>"
        + "".join(ot_links) + "</tr>")
GRP_ROWS = "\n".join(grp_rows)

# ---- 按发报票分组的对外配对相关 ----
grp_pair_rows = []
for tk in ["SOFI", "AFRM", "UPST"]:
    g = BYE[tk]
    cells = ""
    for k2 in ["SOFI~AFRM", "SOFI~UPST", "AFRM~UPST"]:
        if k2 not in g["pair_corr"]: continue
        v = g["pair_corr"][k2]
        cells += f"<td><b>{PAIR_CN[k2]}</b><div class='tsub'>r={r3(v.get('r'))} · p={p_fmt(v.get('p'))}</div></td>"
    grp_pair_rows.append(f"<tr><td><b>{tk} 发报日</b><div class='tsub'>{g['n_days']} 个事件日</div></td>{cells}</tr>")
GRP_PAIR_ROWS = "\n".join(grp_pair_rows)

# ---- 年度表 ----
year_rows = []
YEARS_ORDER = [y for y in ["2021", "2022", "2023", "2024", "2025", "2026"] if y in BY]
for y in YEARS_ORDER:
    v = BY[y]
    pc = v["pair_corr"]
    pc_cells = "".join(
        f"<td class='{cls(pc[k2].get('r'))}'>{r3(pc[k2].get('r'))}</td>" for k2 in ["SOFI~AFRM", "SOFI~UPST", "AFRM~UPST"])
    ab = v["abs_mean"]
    mr = v["mean_ret"]
    year_rows.append(
        f"<tr><td><b>{y}</b><div class='tsub'>{v['n_days']} 日</div></td>"
        f"<td class='{cls(mr['SOFI'])}'>{mr['SOFI']:+.2f}%</td><td class='{cls(mr['AFRM'])}'>{mr['AFRM']:+.2f}%</td><td class='{cls(mr['UPST'])}'>{mr['UPST']:+.2f}%</td>"
        f"<td>{ab['SOFI']:.1f}%</td><td>{ab['AFRM']:.1f}%</td><td>{ab['UPST']:.1f}%</td>"
        + pc_cells + "</tr>")
# 阶段对比
ph_rows = []
for ph, lbl in [("p1_2021_2023", "2021–2023"), ("p2_2024_2026", "2024–2026")]:
    if ph not in BY: continue
    v = BY[ph]
    pc = v["pair_corr"]
    pc_cells = "".join(
        f"<td class='{cls(pc[k2].get('r'))}'>{r3(pc[k2].get('r'))}</td>" for k2 in ["SOFI~AFRM", "SOFI~UPST", "AFRM~UPST"])
    ph_rows.append(f"<tr><td><b>{lbl}</b><div class='tsub'>{v['n_days']} 日</div></td><td colspan='6' class='na'>—</td>" + pc_cells + "</tr>")
YEAR_ROWS = "\n".join(year_rows + ph_rows)

# ---- 窗口相关曲线 ----
WIN_SERIES = {k2: {"x": [], "y": []} for k2 in PAIR_CN}
OFFS = sorted(WIN.keys(), key=int)
for off in OFFS:
    for k2 in PAIR_CN:
        v = WIN[off].get(k2, {})
        WIN_SERIES[k2]["x"].append(int(off))
        WIN_SERIES[k2]["y"].append(v.get("r"))
WB_SERIES = {k2: {"x": [], "y": []} for k2 in PAIR_CN}
for off in OFFS:
    for k2 in PAIR_CN:
        v = WB[off].get(k2)
        WB_SERIES[k2]["x"].append(int(off))
        WB_SERIES[k2]["y"].append(v)

# ---- 双发日 ----
dual_rows = []
for d in sorted(DUEV):
    v = DUEV[d]
    tks = v["tickers"]
    rets = v["rets"]
    ret_cells = "".join(f"<td class='{cls(rets.get(t))}'>{rets.get(t):+.1f}%</td>" for t in ["SOFI", "AFRM", "UPST"])
    dual_rows.append(
        f"<tr><td><b>{d}</b></td><td>{'+'.join(TK_CN[t] for t in tks)}</td>{ret_cells}</tr>")
DUAL_ROWS = "\n".join(dual_rows)

# ---- 三票全同向 ----
SAME = D["same_dir_all"]["pct_all_3_same"]  # 0.5172
# 非事件日对照：0.6415（脚本外算得，硬编码注明）
SAME_NON = 0.6415

# ---- ECharts 注入 ----
JS = {
    "win": WIN_SERIES,
    "wbase": WB_SERIES,
    "offs": OFFS,
    "event_counts": {tk: META["event_counts"][tk] for tk in ["SOFI", "AFRM", "UPST"]},
    "dual": {d: {"tks": v["tickers"], "rets": v["rets"]} for d, v in DUEV.items()},
    "events_by_tk": {tk: BYE[tk]["events"] for tk in ["SOFI", "AFRM", "UPST"]},
    "year_order": YEARS_ORDER,
    "by_year": {y: {"n": BY[y]["n_days"], "pair": {k2: BY[y]["pair_corr"].get(k2, {}).get("r") for k2 in PAIR_CN}} for y in YEARS_ORDER},
}

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SOFI / AFRM / UPST 财报交易日涨跌相关性</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#fff;
          --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --green:#009E73; --purple:#CC79A7;
          --red:#C0392B; --verm:#D55E00; --grey:#8c97a6; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }
  .wrap { max-width: 1100px; margin: 0 auto; }
  h1 { font-size: 26px; letter-spacing: .5px; margin-bottom: 4px; }
  .subtitle { color: var(--sub); font-size: 13px; margin-bottom: 22px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(20,30,50,.05); }
  .card h2 { font-size: 17px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .card h2::before { content: ""; width: 4px; height: 16px; background: var(--blue); border-radius: 2px; }
  .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 4px; }
  .kv { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .kv .k { font-size: 12px; color: var(--sub); }
  .kv .v { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .kv .v small { font-size: 12px; font-weight: 400; color: var(--sub); }
  .kv .muted { font-size: 13px; color: var(--sub); margin-top: 4px; font-weight: 400; }
  .up { color: var(--red); } .dn { color: var(--green); } .na { color: var(--grey); }
  .sig { color: var(--verm); font-weight: 600; }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
  th, td { padding: 8px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  .tsub { font-size: 11px; color: var(--grey); font-weight: 400; }
  .note { font-size: 12.5px; color: var(--sub); margin-top: 10px; }
  .paramnote { font-size: 12px; color: var(--sub); background: #fbfcfe; border: 1px dashed var(--line);
               border-radius: 8px; padding: 8px 12px; margin: 10px 0 4px; line-height: 1.75; }
  .paramnote b { color: var(--ink); }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 300px; }
  .concl { border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }
  ul.tl { list-style: none; }
  ul.tl li { padding: 8px 0 8px 18px; border-left: 2px solid var(--line); margin-left: 6px; position: relative; }
  ul.tl li::before { content: ""; position: absolute; left: -5px; top: 14px; width: 8px; height: 8px;
                     border-radius: 50%; background: var(--blue); }
  ul.tl li b { color: var(--blue); }
  .legend-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; }
  .disclaimer { font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }
  .src { font-size: 11.5px; color: var(--sub); margin-top: 8px; }
  .pill { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
  .pill.sofi { background: #e7f0fa; color: #1e5e93; }
  .pill.afrm { background: #fdf1dd; color: #b5761c; }
  .pill.upst { background: #f3e8f5; color: #7d3c98; }
  @media (max-width: 720px) { .grid3 { grid-template-columns: 1fr 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>SOFI / AFRM / UPST · 财报交易日涨跌相关性</h1>
  <div class="subtitle">金融科技三剑客「谁发财报，当天相互联动怎样变化」· 事件研究（T0=财报发布后首个交易日）· 共同面板 2021-06-01 ~ 2026-08-26 · 62 个财报事件 / 58 个事件日 · 数据截至 2026-08-26</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">财报日相关（三对均值）</div>
        <div class="v">0.36 <small>vs 非财报日 0.63</small></div>
        <div class="muted">财报日联动 <b>显著更弱</b>（Fisher z 检验 3 对全部显著）</div></div>
      <div class="kv"><div class="k">财报日 |波动| 放大（自身）</div>
        <div class="v">1.8× ~ 2.6×</div>
        <div class="muted">UPST 放大最猛（2.55×），财报自身冲击主导当日</div></div>
      <div class="kv"><div class="k">三票同向概率</div>
        <div class="v"><span class="sig">51.7%</span> <small>vs 非财报日 64.2%</small></div>
        <div class="muted">财报日连方向一致性都变差——个股事件打破板块联动</div></div>
    </div>
    <div class="concl">
      ① <b>财报日显著「脱钩」</b>：三对组合在财报交易日的日收益相关 0.26~0.44，环比非财报日 0.62~0.64 明显更低；T+0 是三对组合 11 日窗口（T−5~T+5）中相关性<b>最低点</b>（"凹陷"），AFRM×UPST 从平时 0.64 → 财报日 0.26。<br>
      ② <b>谁发财报，当天主角是它自己</b>：发报票当日 |波动| 放大 1.8~2.6 倍（UPST 中位 |5.6%| 最烈），而其余两票平均跟涨跌 <b>不为 0 且方向逐票分化</b>（如 UPST 发布日 AFRM 平均 −2.7%）；三票同向概率从非财报日的 64% 降到 52%——财报个体冲击把"联动的三兄弟"拆成了"各说各话"。<br>
      ③ <b>×UPST 的传染最不对称</b>：SOFI 发财报日，UPST 同向率 76%、平均 −4.4%（SOFI 财报常与 UPST 同步承压）；但 UPST 发财报日，AFRM 相关仅 0.18、β≈0——UPST 暴涨暴跌基本不传染。AFRM 发报日 UPST 平均 +3.3%（AFRM 财报好时 UPST 常被带动）。<br>
      ④ <b>年度衰减趋势清晰</b>：事件日三对相关 2021（0.87~0.97，上市初抱团）→ 2022（0.56~0.66）→ 2023-2025（多数 0~0.36 甚至转负）→ 2026（0~0.52，AFRM×UPST≈0）。<b>财报日联动从"高度同步"走向"基本独立"</b>——三家公司商业模式与投资者结构分化是主因（UPST 高度依赖融资利差、AFRM 消费信贷、SOFI 银行+科技）。<br>
      ⑤ <b>双发日不是联动催化剂</b>：4 个双发日（2021-11-10 SOFI+AFRM、2023-05-10 UPST+AFRM、2024-05-08 AFRM+UPST、2024-11-08 UPST+AFRM）里 3 个是两张票各自爆点（UPST 2023-05-10 +34.6%、2024-11-08 +46.0%；AFRM 2024-05-08 −9.5%），第三票（SOFI）在 2024-11-08 大涨 +9.3%——虽无单日统计意义，但说明财报消息冲击是"一对多广播"，方向完全取决于各自超预期，无稳定传染模式。<br>
      ⑥ <b>操作含义</b>：财报窗口别把这三只当一回事——某只出财报当天，另外两只<b>没有稳定的统计联动可依赖</b>（方向 52% 随机、相关显著低于平时），押"财报联动交易"缺乏历史依据；真正可参考的是发报票自身波动放大倍数（UPST 最狠 2.6×）。
    </div>
    <div class="src">数据：三家日线来自 Yahoo Finance（close，美东交易日，复权口径 adj_close 校正）；财报交易日清单来自富途双接口（earnings_price_move × earnings_price_history 并集），AFRM FY2022Q4（2022-08-25 盘后 / 交易日 2022-08-26）由 SEC 8-K / Business Wire 官方稿核实补入。共同面板 2021-06-01 起（SOFI 上市首日后）。AFRM 2026-08-27 盘后财报因面板缺 08-28 数据不纳入。事件日=财报发布后首个完整交易日；同日双发按单一观测日计（58 个事件日）。</div>
  </div>

  <!-- 事件日 vs 非事件日 -->
  <div class="card">
    <h2>财报日 vs 非财报日：相关性系统性下降 <span class="tag">T0=财报发布后首个交易日</span></h2>
    <div class="paramnote"><b>参数图例：</b>① <b>r (Pearson)</b>=两票日收益线性相关（−1~1，越接近 1 越同涨同跌）；② <b>Spearman ρ</b>=秩相关，抗极端值（财报日常见 20%+ 极端日，ρ 比 r 更稳）；③ <b>显著性</b>三档：<b>显著</b> p&lt;0.01 / <b>边缘</b> 0.01≤p&lt;0.05 / — p≥0.05；④ <b>p 值</b>=r 的 t 检验双尾 p；⑤ <b>β</b>=前一票涨 1% 时后一票平均跟涨 %（敏感度）；⑥ <b>R²</b>=前一票波动解释后一票比例；⑦ <b>diff z</b>=Fisher z 两样本相关差异检验：z<0 说明事件日相关显著低于非事件日。</div>
    <table>
      <tr><th>配对</th><th>财报日 r</th><th>财报日 ρ</th><th>显著</th><th>p</th><th>β</th><th>R²</th><th>非财报日 r</th><th>非财报日 β</th><th>差异检验 (z)</th></tr>
      __EV_ROWS__
    </table>
    <div class="note"><b>三对组合财报日相关全部显著低于非财报日</b>（Fisher z：−2.03 ~ −3.34，p=0.001~0.042）。财报日相关 0.26~0.44 仍未归零（同受板块/利率环境影响），但相比平日 0.62~0.64 的"高联动常态"明显松绑。财报日 Spearman ρ 相对 r 的降幅较小（如 AFRM×UPST r 0.26 → ρ 0.45），说明极端日扰动把线性相关压低，而"方向大致一致"仍保留一部分——但方向一致性也只有 52%（见下）。</div>
    <div class="grid3">
      __ABS_CARDS__
    </div>
    <div class="note"><span class="legend-dot" style="background:#0072B2"></span>自身波动放大倍数：SOFI 1.8× / AFRM 1.9× / UPST 2.6×——UPST 财报日自身平均 |波幅| 高达 10.6%（中位 5.6%），远超 SOFI 5.5%。</div>
  </div>

  <!-- 窗口相关曲线 -->
  <div class="card">
    <h2>事件窗口 T−5 ~ T+5 相关性曲线：T+0 是"凹陷点" <span class="tag">pooled 事件对齐</span></h2>
    <div id="chart_win" class="chart"></div>
    <div class="note">实线=财报事件对齐窗口逐日三对相关；虚线=随机抽样非财报日同口径基线。三对组合的<b>事件日(T+0)相关均为窗口最低</b>（SOFI×AFRM 0.38 vs 基线 0.70、AFRM×UPST 0.26 vs 0.70），且明显低于 T−1（0.48~0.68）与 T+1（0.40~0.55）。财报发布把当天联动打断，次日即部分恢复。AFRM×UPST 的凹陷最深（−0.44），SOFI×AFRM 最浅（−0.32）——UPST 相关的那两对破坏更大。</div>
  </div>

  <!-- 按发报票分组 -->
  <div class="card">
    <h2>按「谁发财报」分组：传染方向完全不对称 <span class="tag">T0 当日</span></h2>
    <div class="paramnote"><b>参数图例：</b>① <b>胜率</b>=发报票当日上涨概率；② <b>发报票均值/|均值|</b>=当日收益均值 / 绝对波幅均值；③ <b>跟随票同向率</b>=与发报票同涨跌的比例；④ <b>跟随票均值</b>=跟随票当日平均收益（%）；⑤ <b>r</b>=跟随票×发报票当日相关。</div>
    <table>
      <tr><th>发报票</th><th>当日胜率</th><th>发报票均值</th><th>发报票 |均值|</th>
          <th>跟随1</th><th>跟随1均值</th><th>跟随1中位</th><th>跟随1 |均值|</th><th>r</th>
          <th>跟随2</th><th>跟随2均值</th><th>跟随2中位</th><th>跟随2 |均值|</th><th>r</th></tr>
      __GRP_ROWS__
    </table>
    <div class="note">读法：<b>SOFI 发报日</b>（n=21）UPST 同向率 76%、平均 −4.4%——SOFI 财报常与 UPST 同步走弱（两者贷超/信贷预期联动）；<b>AFRM 发报日</b>（n=20）UPST 平均 +3.3%——AFRM 财报好时 UPST 常被带动（同为消费信贷景气代理）；<b>UPST 发报日</b>（n=21）AFRM 相关仅 0.18、跟涨跌均值 ≈0——UPST 的暴涨暴跌（四次 |30%|+ 极端日）完全不传染给其他两家，因为市场把 UPST 事件读作「UPST 独有」而非「板块信号」。</div>
    <table style="margin-top:14px">
      <tr><th>分组</th><th colspan="3">发报日当天配对相关（若该票在配对内）</th></tr>
      __GRP_PAIR_ROWS__
    </table>
  </div>

  <!-- 年度 -->
  <div class="card">
    <h2>分年度演化：财报日联动逐年"脱钩" <span class="tag">事件日口径</span></h2>
    <div id="chart_year" class="chart-sm"></div>
    <div class="paramnote"><b>参数图例：</b><b>均值</b>=该年所有财报日的当日平均涨跌（%）；<b>|均值|</b>=平均绝对波幅（%）；<b>r</b>=该年事件日两票相关。</div>
    <table>
      <tr><th>年份</th><th>SOFI 均值</th><th>AFRM 均值</th><th>UPST 均值</th><th>SOFI |均值|</th><th>AFRM |均值|</th><th>UPST |均值|</th>
          <th>SOFI×AFRM</th><th>SOFI×UPST</th><th>AFRM×UPST</th></tr>
      __YEAR_ROWS__
    </table>
    <div class="note">2021 年上市初期财报日相关高达 0.87~0.97（"金融科技新贵"整体抱团），2022 年（加息+信贷恐慌）0.56~0.66，此后逐年断裂：2023~2025 多数配对 0~0.36 且 2025 年两对转负，2026 年 AFRM×UPST ≈0。<b>三家公司从"同一叙事"走向"各自基本面"</b>——UPST 仍是三票中波动最大、财报日最独立的一个。</div>
  </div>

  <!-- 双发日 -->
  <div class="card">
    <h2>四次「双发日」：各自爆点，无稳定传染 <span class="tag">同日两家发报</span></h2>
    <div class="paramnote"><b>参数图例：</b>当日三票收盘涨跌（%）；<b>粗体</b>标记当日发报票。</div>
    <table>
      <tr><th>日期</th><th>发报票</th><th>SOFI</th><th>AFRM</th><th>UPST</th></tr>
      __DUAL_ROWS__
    </table>
    <div class="note">4 次双发日里，发报票各自爆点（+34.6% / +46.0% / −9.5% / −15.4%）方向取决于各自超预期，无"双发必同向"规律；第三票 3/4 次跟随发报票方向（2024-11-08 SOFI +9.3% 同步 UPST +46%），但样本仅 4 次无统计意义。核心信息：<b>财报冲击是一对多的独立广播，板块内部不存在可交易的联动模式。</b></div>
  </div>

  <div class="disclaimer">本报告为统计描述性分析，不构成投资建议。财报日事件研究样本 58 个事件日，年度分档 n=5~12，双发日 n=4，统计功效有限，结论应视为「倾向」而非「定论」。子样本配对相关未校正多重检验。数据来源：Yahoo Finance 日线、富途行情接口（财报日）、SEC/Business Wire（AFRM FY22Q4 补入核实）。</div>
</div>

<script>
const JS = __JS_OBJ__;
const COL = { blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", green:"#009E73", purple:"#CC79A7", red:"#C0392B", grey:"#8c97a6" };
const PAIRS = ["SOFI~AFRM","SOFI~UPST","AFRM~UPST"];
const PAIR_CN = {"SOFI~AFRM":"SOFI×AFRM","SOFI~UPST":"SOFI×UPST","AFRM~UPST":"AFRM×UPST"};
const PAIR_COL = {"SOFI~AFRM":COL.blue,"SOFI~UPST":COL.orange,"AFRM~UPST":COL.purple};

// 窗口相关曲线
(function(){
  const el = document.getElementById("chart_win");
  const s = echarts.init(el);
  const series = [];
  PAIRS.forEach(p=>{
    series.push({ name: PAIR_CN[p], type:"line", data: JS.win[p].y, smooth:true, symbolSize:6,
      lineStyle:{width:2.5, color:PAIR_COL[p]}, itemStyle:{color:PAIR_COL[p]} });
    series.push({ name: PAIR_CN[p]+"（基线）", type:"line", data: JS.wbase[p].y, smooth:true, symbol:"none",
      lineStyle:{width:1.5, type:"dashed", color:PAIR_COL[p], opacity:0.45} });
  });
  s.setOption({
    grid:{left:50,right:30,top:40,bottom:40}, tooltip:{trigger:"axis"},
    legend:{data:["SOFI×AFRM","SOFI×UPST","AFRM×UPST"], top:0},
    xAxis:{type:"category", data:JS.offs.map(o=>o>0?"T+"+o:o===0?"T+0（财报日）":"T"+o), axisLabel:{fontSize:11}},
    yAxis:{type:"value", min:-0.1, max:1, name:"r", axisLabel:{formatter:v=>v.toFixed(1)},
      splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  });
  window.addEventListener("resize", ()=>s.resize());
})();

// 年度相关柱状（三对）
(function(){
  const el = document.getElementById("chart_year");
  const s = echarts.init(el);
  const years = JS.year_order;
  const series = PAIRS.map(p=>({
    name: PAIR_CN[p], type:"bar", barGap:"15%",
    itemStyle:{color:PAIR_COL[p]},
    data: years.map(y=>{ const v = JS.by_year[y] && JS.by_year[y].pair[p]; return v==null?null:+v.toFixed(3); })
  }));
  s.setOption({
    grid:{left:50,right:20,top:40,bottom:40}, tooltip:{trigger:"axis", valueFormatter:v=>v==null?"—":v},
    legend:{data:PAIRS.map(p=>PAIR_CN[p]), top:0},
    xAxis:{type:"category", data:years, axisLabel:{fontSize:12}},
    yAxis:{type:"value", min:-0.3, max:1, name:"r（年报关日相关）", axisLabel:{formatter:v=>v.toFixed(1)},
      splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  });
  window.addEventListener("resize", ()=>s.resize());
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__EV_ROWS__", EV_ROWS)
HTML = HTML.replace("__ABS_CARDS__", abs_card("SOFI") + abs_card("AFRM") + abs_card("UPST"))
HTML = HTML.replace("__GRP_ROWS__", GRP_ROWS)
HTML = HTML.replace("__GRP_PAIR_ROWS__", GRP_PAIR_ROWS)
HTML = HTML.replace("__YEAR_ROWS__", YEAR_ROWS)
HTML = HTML.replace("__DUAL_ROWS__", DUAL_ROWS)
HTML = HTML.replace("__JS_OBJ__", json.dumps(JS, ensure_ascii=False))

out = os.path.join(OUTD, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out} size={os.path.getsize(out)}")