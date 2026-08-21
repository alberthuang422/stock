# -*- coding: utf-8 -*-
"""银行走弱 → 医药股表现 报告生成器（读 results/kbwb_med_weakness.json）
规范：普通三引号模板 + @@PLACEH@@ 占位符 replace（避免 f-string 与 JS 花括号冲突）
XPH = 化学制药（SPDR Pharmaceuticals），XBI = 生物制药（SPDR Biotech）
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "15_kbwb_med_weakness")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "kbwb_med_weakness.json"), encoding="utf-8") as f:
    D = json.load(f)

SC = D["signal_counts"]
CUR = D["current"]
SR = D["kbwb_state_ret"]
meta = D["meta"]
P = D["params"]
RE = D["regime_corr"]
EV = D["event_study"]
BASE_FWD = D["baseline_fwd"]


def js(o):
    return json.dumps(o, ensure_ascii=False, default=str)


def fmt(v, nd=2, sign=False):
    if v is None:
        return "—"
    return (f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}")


# 从数据中提取关键数字
xph_r = RE["ema"]["full"]["XPH"]
xbi_r = RE["ema"]["full"]["XBI"]
xph_ev = EV["ema"]["full"]["XPH"]
xbi_ev = EV["ema"]["full"]["XBI"]
xph_b20, xbi_b20 = BASE_FWD["XPH"]["20"]["mean"], BASE_FWD["XBI"]["20"]["mean"]
xph_f20, xbi_f20 = xph_ev["20"]["mean"], xbi_ev["20"]["mean"]

kpis = f"""
    <div class="kpis">
      <div class="kpi"><div class="num">{SC['weak_any_pct']:.0f}%</div><div class="lab">KBWB 处于走弱状态的天数占比（全期）</div></div>
      <div class="kpi"><div class="num">{SC['ema_events']} / {SC['trendline_events']}</div><div class="lab">信号A（EMA20）/ 信号B（趋势线）事件数</div></div>
      <div class="kpi"><div class="num">{xph_r['weak']['corr']:+.2f}</div><div class="lab">走弱期 XPH（化学制药）↔KBWB 相关</div></div>
      <div class="kpi"><div class="num">{xbi_r['weak']['corr']:+.2f}</div><div class="lab">走弱期 XBI（生物制药）↔KBWB 相关</div></div>
      <div class="kpi"><div class="num">{CUR['ema_gap_pct']:+.1f}%</div><div class="lab">KBWB 现价 vs EMA20（{CUR['date']}）</div></div>
    </div>"""

verdict = f"""
    <div class="verdict">
      <div class="t">核心结论</div>
      <div class="b">医药和银行的联动<b>比科技弱一档，且两种制药反应不同</b>。
        ① <span class="hlb">联动强度</span>：银行走弱时化学制药 XPH 相关性
        {xph_r['normal']['corr']:.2f}→<span class="hlb">{xph_r['weak']['corr']:.2f}</span>（升幅大），
        生物制药 XBI 仅 {xbi_r['normal']['corr']:.2f}→<span class="hlb">{xbi_r['weak']['corr']:.2f}</span>（升幅小）——
        且都明显低于科技的 0.71~0.76，<b>医药受银行拖累的程度更轻</b>。
        ② <span class="hlg">事后收益</span>：与科技不同，银行走弱确认后医药<b>没有"跟着反弹"的现象</b>——
        XPH fwd20 <span class="hlg">{xph_f20:+.2f}%</span>（基线 {xph_b20:+.2f}%，略低）、
        XBI <span class="hlg">{xbi_f20:+.2f}%</span>（基线 {xbi_b20:+.2f}%，持平）——医药走自己的节奏。
        ③ <span class="hl">当前</span>：{CUR['date']} KBWB 处于走弱状态（趋势线已破、EMA20 下方），
        医药短期与银行同向概率上升，但<b>独立性仍强于科技</b>，更像防御属性而非跟跌资产。</b>
      </div>
    </div>"""

method_html = f"""
    <div class="sig-grid">
      <div class="sig">
        <div class="sig-t"><span class="tag ema">信号A</span> EMA20 跌破且多日未修复</div>
        <ul>
          <li>KBWB 收盘跌破 <b>EMA{P['ema_n']}</b>；</li>
          <li>且连续 <b>{P['repair_days']} 个交易日</b>收盘都留在 EMA20 下方 → 走弱确认；</li>
          <li>收盘回到 EMA20 上方视为修复，状态结束。</li>
        </ul>
      </div>
      <div class="sig">
        <div class="sig-t"><span class="tag tl">信号B</span> 跌破上升趋势线</div>
        <ul>
          <li>近 <b>{P['trend_win']} 日</b>内取最近 2~4 个依次抬升的 swing low（分形，左右各 3 根）；</li>
          <li>OLS 拟合，要求斜率 &gt; 0 且 R² ≥ {P['trend_r2']} → 有效上升趋势线；</li>
          <li>收盘自上方<b>下穿</b>趋势线 → 走弱事件（{P['trend_cooldown']} 日冷却去重）。</li>
        </ul>
      </div>
      <div class="sig" style="grid-column:1/-1;">
        <div class="sig-t"><span class="tag xph">医药标的</span></div>
        <ul>
          <li><b>XPH</b>（SPDR Pharmaceuticals ETF）——<b>化学制药</b>，覆盖传统大药企与仿制药；</li>
          <li><b>XBI</b>（SPDR Biotechnology ETF）——<b>生物制药</b>，等权编制，中小生物科技占比高、波动更大。</li>
        </ul>
      </div>
    </div>"""

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
    <div class="note">最近一次 EMA20 走弱确认：<b>{CUR['last_ema_event']}</b>。当前趋势线走弱信号已生效。</div>"""


def ev_row(sig, t, scope="full"):
    e = EV[sig][scope][t]
    b = BASE_FWD[t]
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


ev_rows = ""
for t in ("XPH", "XBI"):
    for sig, siglab in (("ema", "EMA20走弱"), ("trendline", "跌破趋势线")):
        r = ev_row(sig, t, "full")
        if r is None:
            ev_rows += f'<tr><td><span class="tag {"ema" if sig=="ema" else "tl"}">{siglab}</span></td><td>{t}</td><td class="na">0</td><td colspan="6" class="na">样本不足</td></tr>'
            continue
        cells, n = r
        ev_rows += (f'<tr><td><span class="tag {"ema" if sig=="ema" else "tl"}">{siglab}</span></td>'
                    f'<td>{t}</td><td>{n}</td>' + "".join(cells) + "</tr>")

base_rows = ""
for t in ("XPH", "XBI"):
    b = BASE_FWD[t]
    base_rows += (f'<tr class="baserow"><td><span class="tag base">基线</span></td><td>{t}</td><td>{b["5"]["n"]:,}</td>'
                  f'<td>{b["5"]["mean"]:+.2f}%</td><td class="sub2">—</td>'
                  f'<td>{b["10"]["mean"]:+.2f}%</td><td class="sub2">—</td>'
                  f'<td>{b["20"]["mean"]:+.2f}%</td><td class="sub2">—</td></tr>')

reg_rows = ""
for sig, siglab in (("ema", "EMA20走弱"), ("trendline", "跌破趋势线"), ("any", "任一信号合并")):
    for t in ("XPH", "XBI"):
        r = RE[sig]["full"][t]
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

# 与科技版的横向对比（硬编码科技版数值，来自 kbwb_tech_weakness.json 同窗口同口径）
cross_rows = ""
tech_ref = {"SOXX": (0.446, 0.709, 2.257, 2.81), "XLK": (0.459, 0.758, 1.698, 2.02)}
med_rows_data = {"XPH": (xph_r["normal"]["corr"], xph_r["weak"]["corr"], xph_b20, xph_f20),
                 "XBI": (xbi_r["normal"]["corr"], xbi_r["weak"]["corr"], xbi_b20, xbi_f20)}
for t, (n_, w_, b20, f20) in {**tech_ref, **med_rows_data}.items():
    grp = "科技" if t in tech_ref else "医药"
    tagcls = "tech" if grp == "科技" else "xph"
    delta = "↑ 显著" if w_ - n_ > 0.2 else ("↑ 温和" if w_ - n_ > 0.1 else "→ 变化小")
    reb = f20 - b20
    cross_rows += (f'<tr><td><span class="tag {tagcls}">{grp}</span></td><td>{t}</td>'
                   f'<td>{n_:.2f}</td><td class="hlb">{w_:.2f}</td><td>{delta}</td>'
                   f'<td>{b20:+.2f}%</td><td class="{ "up" if f20>0 else "dn"}">{f20:+.2f}%</td>'
                   f'<td class="{ "up" if reb>0 else "dn"}">{reb:+.2f}</td></tr>')

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
<title>银行走弱 → 医药股表现 · KBWB vs XPH/XBI 条件相关性分析</title>
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
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);}
  .tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .tag.ema{background:#e8eef6;color:var(--blue);} .tag.tl{background:#fdeee0;color:#c05c0b;}
  .tag.base{background:#eef0f2;color:#8a9099;} .tag.tech{background:#efe9fb;color:var(--purple);} .tag.xph{background:#e8f5ee;color:var(--green);}
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
    <h1>银行走弱 → 医药股表现 · 条件相关性分析</h1>
    <div class="meta">@@META@@</div>
    @@KPIS@@
    @@VERDICT@@
  </div>

  <div class="card">
    <h2>① 走弱信号定义（KBWB）与医药标的</h2>
    @@METHOD@@
  </div>

  <div class="card">
    <h2>② 当前状态快照</h2>
    @@CURRENT@@
  </div>

  <div class="card">
    <h2>③ KBWB 近 3 年走势 · EMA20 与走弱区间</h2>
    <div class="chart" id="ch_price"></div>
    <div class="note">红色阴影 = 走弱状态区间（任一信号触发）。</div>
  </div>

  <div class="card">
    <h2>④ 事件研究 · 走弱信号后医药股前瞻收益</h2>
    <div class="chart sm" id="ch_ev"></div>
    <div class="scroll">
    <table>
      <tr><th>走弱信号</th><th>医药标的</th><th>事件数 n</th><th>fwd5 均值(胜率)</th><th>Δ基线</th><th>fwd10 均值(胜率)</th><th>Δ基线</th><th>fwd20 均值(胜率)</th><th>Δ基线</th></tr>
      @@EV_ROWS@@
      @@BASE_ROWS@@
    </table>
    </div>
    <div class="keypoint"><b>关键发现：</b>与科技股不同，银行走弱确认后医药股<b>没有显著的超额修复</b>——
      XPH（化学制药）fwd20 +0.74% <b>低于</b>基线 +0.91%，XBI（生物制药）+1.58% 与基线 +1.47% 基本持平。
      医药的上涨主要靠自身节奏（管线、政策、业绩），银行走弱对医药既不构成利空、也不构成额外利多；
      近 1 年样本中两者在信号后 20 日均有 +3.5% 左右，但 n=5，仅供参考。</div>
  </div>

  <div class="card">
    <h2>⑤ 状态条件相关 · 走弱期 vs 正常期 KBWB↔医药</h2>
    <div class="chart sm" id="ch_reg"></div>
    <div class="scroll">
    <table>
      <tr><th>走弱口径</th><th>医药标的</th><th>走弱期相关</th><th>走弱样本 n</th><th>正常期相关</th><th>正常样本 n</th><th>Δ相关</th><th>走弱期医药日均</th></tr>
      @@REG_ROWS@@
    </table>
    </div>
    <div class="keypoint"><b>机制解读：</b>银行走弱时，<b>化学制药 XPH 的联动抬升更明显</b>（0.46→0.66），
      生物制药 XBI 抬升较温和（0.40→0.55）。两者的绝对水平都低于科技（0.71~0.76），
      说明<b>医药整体比科技更"独立"</b>。与科技一致的是：银行<b>跌破上升趋势线</b>（结构性破位）时
      医药相关性同样回落（XPH 0.54→0.40、XBI 0.46→0.35，近 1 年甚至接近 0），医药走独立行情。</div>
  </div>

  <div class="card">
    <h2>⑥ 横向对比 · 银行走弱时 科技 vs 医药</h2>
    <div class="scroll">
    <table>
      <tr><th>板块</th><th>标的</th><th>正常期相关</th><th>走弱期相关</th><th>联动变化</th><th>基线 fwd20</th><th>走弱后 fwd20</th><th>Δ fwd20</th></tr>
      @@CROSS_ROWS@@
    </table>
    </div>
    <div class="note">同窗口、同口径（2011-11 起，信号A=EMA20 走弱）对比。科技：走弱后 fwd20 <b>超基线</b>且相关性升幅大；医药：fwd20 <b>贴基线或略低</b>，XPH 联动抬升居中、XBI 最独立。</div>
  </div>

  <div class="card">
    <h2>⑦ 近 2 年走弱事件清单（KBWB）</h2>
    <div class="scroll">
    <table>
      <tr><th>确认日期</th><th>信号类型</th><th>KBWB 后 10 日收益</th></tr>
      @@EV_LIST_ROWS@@
    </table>
    </div>
    <div class="note">银行自身走弱确认事件，供对照当前信号位置。</div>
  </div>

  <div class="card">
    <h2>⑧ 方法口径与局限</h2>
    <ul>
      <li><b>数据</b>：Yahoo Finance 日线复权收盘价；统一窗口 @@WIN_START@@ ~ @@WIN_END@@（共 @@N@@ 个交易日，KBWB/XPH/XBI 交集）。</li>
      <li><b>信号A</b>：收盘跌破 EMA@@EMA_N@@ 且连续 @@REPAIR@@ 日未收复 → 走弱确认；回到线上方即修复。</li>
      <li><b>信号B</b>：近 @@TREND_WIN@@ 日 2~4 个依次抬升 swing low OLS 拟合（斜率&gt;0、R²≥@@TREND_R2@@），收盘自上而下穿越 → 走弱事件（@@TREND_CD@@ 日冷却）。</li>
      <li><b>标的选择</b>：化学制药用 XPH（SPDR Pharmaceuticals，含大药企+仿制药），生物制药用 XBI（SPDR Biotech，等权、中小生物科技权重高、波动大）。项目本地另有 IBB（生物科技、市值加权），口径上 XBI 更贴合"生物制药板块"的等权表征。</li>
      <li><b>局限</b>：信号B 样本仅 5 例；相关性与事件统计均未控制利率、FDA 政策等医药特有驱动因子；XBI 等权编制使其与 KBWB（同为等权）结构相似，相关性对比时需注意权重口径差异。</li>
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
  var sig = DATA.event_study.ema.full, base = DATA.baseline_fwd;
  var vals = [base.XPH["20"].mean, sig.XPH["20"].mean, base.XBI["20"].mean, sig.XBI["20"].mean];
  var win  = [null, sig.XPH["20"].win, null, sig.XBI["20"].win];
  var cats = ["XPH 基线","XPH 走弱后","XBI 基线","XBI 走弱后"];
  ch.setOption({
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"},
      formatter:function(ps){ var p=ps[0]; var w=win[p.dataIndex]; return p.name + "<br>fwd20 均值: " + (p.value==null?"-":p.value.toFixed(2)+"%") + (w!=null?"<br>胜率: "+w.toFixed(0)+"%":""); } },
    grid:{ left:60, right:30, top:40, bottom:40 },
    xAxis:{ type:"category", data:cats, axisLabel:{ fontSize:11 } },
    yAxis:{ type:"value", name:"fwd20 均值 %", axisLabel:{ formatter:function(v){return v.toFixed(1);} } },
    series:[{ name:"fwd20", type:"bar", barWidth:"46%",
      data:vals.map(function(v,i){ return { value:v, itemStyle:{ color:(i%2===1)?RED:"#c9ccd2" } }; }),
      label:{ show:true, position:"top", formatter:function(p){ return (p.value==null?"":p.value.toFixed(2)+"%"); }, fontSize:11 } }]
  });
})();

// 图⑤ 状态相关：走弱 vs 正常（EMA20 口径）
(function(){
  var ch = echarts.init(document.getElementById("ch_reg"));
  var r = DATA.regime_corr.ema.full;
  var cats = ["XPH 走弱期","XPH 正常期","XBI 走弱期","XBI 正常期"];
  var vals = [r.XPH.weak.corr, r.XPH.normal.corr, r.XBI.weak.corr, r.XBI.normal.corr];
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
    "@@META@@": (f'{meta["kbwb"]}（银行指数代理）→ 医药：XPH（化学制药）/ XBI（生物制药） · '
                 f'分析窗口 {D["period"]["start"]} ~ {D["period"]["end"]}（共 {D["period"]["n"]:,} 个交易日）· '
                 f'{meta["source"]} · 生成 {meta["fetched"]}'),
    "@@KPIS@@": kpis,
    "@@VERDICT@@": verdict,
    "@@METHOD@@": method_html,
    "@@CURRENT@@": current_html,
    "@@EV_ROWS@@": ev_rows,
    "@@BASE_ROWS@@": base_rows,
    "@@REG_ROWS@@": reg_rows,
    "@@CROSS_ROWS@@": cross_rows,
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

out_path = os.path.join(OUT_DIR, "kbwb_med_weakness_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={os.path.getsize(out_path)}")
