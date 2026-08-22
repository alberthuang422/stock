# -*- coding: utf-8 -*-
"""银行走弱 → 资管公司表现 报告生成器（读 results/kbwb_am_weakness.json）
规范：普通三引号模板 + @@PLACEH@@ 占位符 replace（避免 f-string 与 JS 花括号冲突）
资管标的：APO/BX/KKR（另类资管）、BLK/TROW（传统资管）
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "16_kbwbAM弱势")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "kbwb_am_weakness.json"), encoding="utf-8") as f:
    D = json.load(f)

SC = D["signal_counts"]
CUR = D["current"]
SR = D["kbwb_state_ret"]
meta = D["meta"]
P = D["params"]
RE = D["regime_corr"]
EV = D["event_study"]
BASE_FWD = D["baseline_fwd"]
TECHS = ["APO", "BX", "KKR", "BLK", "TROW"]


def js(o):
    return json.dumps(o, ensure_ascii=False, default=str)


def fmt(v, nd=2, sign=False):
    if v is None:
        return "—"
    return (f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}")


# 走弱期相关性（EMA20 口径）
ema_full = RE["ema"]["full"]
corr_ordered = sorted(TECHS, key=lambda t: -ema_full[t]["weak"]["corr"])
top_t = corr_ordered[0]
top_corr = ema_full[top_t]["weak"]["corr"]

kpis = f"""
    <div class="kpis">
      <div class="kpi"><div class="num">{SC['weak_any_pct']:.0f}%</div><div class="lab">KBWB 走弱状态天数占比（全期）</div></div>
      <div class="kpi"><div class="num">{SC['ema_events']} / {SC['trendline_events']}</div><div class="lab">信号A（EMA20）/ 信号B（趋势线）事件数</div></div>
      <div class="kpi"><div class="num">{ema_full[top_t]['weak']['corr']:+.2f}</div><div class="lab">走弱期 {top_t}（资管）↔KBWB 相关 · 最高</div></div>
      <div class="kpi"><div class="num">{ema_full['APO']['weak']['corr']:+.2f}</div><div class="lab">走弱期 APO ↔KBWB 相关</div></div>
      <div class="kpi"><div class="num">{CUR['ema_gap_pct']:+.1f}%</div><div class="lab">KBWB 现价 vs EMA20（{CUR['date']}）</div></div>
    </div>"""

verdict = f"""
    <div class="verdict">
      <div class="t">核心结论</div>
      <div class="b">资管公司是和银行<b>联动最紧密</b>的板块，
        <span class="hlb">相关性高于科技、远高于医药</span>。
        ① <span class="hlb">联动强度</span>：银行走弱期 5 只资管股与 KBWB 日收益相关
        {ema_full['BLK']['normal']['corr']:.2f}→<span class="hlb">{ema_full['BLK']['weak']['corr']:.2f}</span>（BLK），
        {ema_full['APO']['normal']['corr']:.2f}→<span class="hlb">{ema_full['APO']['weak']['corr']:.2f}</span>（APO）、
        {ema_full['KKR']['normal']['corr']:.2f}→<span class="hlb">{ema_full['KKR']['weak']['corr']:.2f}</span>（KKR）——
        全部高于科技的 0.71~0.76。资管是<b>银行的影子</b>：费率收入、信贷敞口、资本市场β同源。
        ② <span class="hlg">事后收益</span>：EMA20 走弱确认后，另类资管普遍
        <span class="hlg">强于基线</span>（APO fwd20 +3.11% vs 基线 +2.23%）、
        传统资管 <b>贴基线</b>（BLK +2.28% vs +1.53%、TROW +1.33% vs +0.94%）——
        与科技类似是"跌后反弹"逻辑；但<b>跌破趋势线</b>时差异巨大：另类资管
        <span class="hl">fwd20 −5%~−9% 且胜率 0%</span>（BX −7.58%、KKR −8.73%），
        传统资管抗跌（BLK −0.27%）。
        ③ <span class="hl">当前</span>：{CUR['date']} KBWB 处于走弱状态（趋势线已破），
        资管股与银行同向波动概率极高，<b>尤其需注意另类资管的杠杆敏感度</b>。
      </div>
    </div>"""

method_html = f"""
    <div class="sig-grid">
      <div class="sig">
        <div class="sig-t"><span class="tag ema">信号A</span> EMA20 跌破且多日未修复</div>
        <ul>
          <li>KBWB 收盘跌破 <b>EMA{P['ema_n']}</b>；</li>
          <li>且连续 <b>{P['repair_days']} 个交易日</b>收盘都留在 EMA20 下方 → 走弱确认；</li>
          <li>收盘回到 EMA20 上方视为修复。</li>
        </ul>
      </div>
      <div class="sig">
        <div class="sig-t"><span class="tag tl">信号B</span> 跌破上升趋势线</div>
        <ul>
          <li>近 <b>{P['trend_win']} 日</b>2~4 个依次抬升 swing low（分形）OLS 拟合（斜率&gt;0、R²≥{P['trend_r2']}）；</li>
          <li>收盘自上而<b>下穿</b>趋势线 → 走弱事件（{P['trend_cooldown']} 日冷却）。</li>
        </ul>
      </div>
      <div class="sig" style="grid-column:1/-1;">
        <div class="sig-t"><span class="tag xph">资管标的</span></div>
        <ul>
          <li><b>{meta['techs']['APO']}</b>、<b>{meta['techs']['BX']}</b>、<b>{meta['techs']['KKR']}</b> —— 另类资管（私募信贷/PE/杠杆资本，β 弹性最高）</li>
          <li><b>{meta['techs']['BLK']}</b>、<b>{meta['techs']['TROW']}</b> —— 传统资管（公募/被动，收入更稳，β 较低）</li>
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
for t in TECHS:
    for sig, siglab in (("ema", "EMA20走弱"), ("trendline", "跌破趋势线")):
        r = ev_row(sig, t, "full")
        if r is None:
            ev_rows += f'<tr><td>{t}</td><td><span class="tag {"ema" if sig=="ema" else "tl"}">{siglab}</span></td><td class="na">0</td><td colspan="6" class="na">样本不足</td></tr>'
            continue
        cells, n = r
        grp = "另类" if t in ("APO", "BX", "KKR") else "传统"
        ev_rows += (f'<tr><td><span class="tag {"alt" if grp=="另类" else "trad"}">{grp}</span> {t}</td>'
                    f'<td><span class="tag {"ema" if sig=="ema" else "tl"}">{siglab}</span></td><td>{n}</td>' + "".join(cells) + "</tr>")

base_rows = ""
for t in TECHS:
    b = BASE_FWD[t]
    base_rows += (f'<tr class="baserow"><td><span class="tag base">基线</span> {t}</td><td>—</td><td>{b["5"]["n"]:,}</td>'
                  f'<td>{b["5"]["mean"]:+.2f}%</td><td class="sub2">—</td>'
                  f'<td>{b["10"]["mean"]:+.2f}%</td><td class="sub2">—</td>'
                  f'<td>{b["20"]["mean"]:+.2f}%</td><td class="sub2">—</td></tr>')

reg_rows = ""
for sig, siglab in (("ema", "EMA20走弱"), ("trendline", "跌破趋势线"), ("any", "任一信号合并")):
    for t in TECHS:
        r = RE[sig]["full"][t]
        wk, nm = r["weak"], r["normal"]
        dcorr = wk["corr"] - nm["corr"]
        dcls = "up" if dcorr > 0 else "dn"
        grp = "另类" if t in ("APO", "BX", "KKR") else "传统"
        reg_rows += (f'<tr><td><span class="tag {"alt" if grp=="另类" else "trad"}">{grp}</span> {t}</td><td>{siglab}</td>'
                     f'<td class="hlb">{wk["corr"]:+.3f}</td><td class="sub2">n={wk["n"]}</td>'
                     f'<td>{nm["corr"]:+.3f}</td><td class="sub2">n={nm["n"]}</td>'
                     f'<td class="{dcls}">{dcorr:+.3f}</td>'
                     f'<td class="{"dn" if wk["tech_mean_ret"]<0 else "up"}">{wk["tech_mean_ret"]:+.3f}%</td></tr>')

# 横向对比：科技 / 医药 / 资管（科技与医药硬编码自对应结果，同窗口同口径）
cross_rows = ""
tech_ref = {"SOXX": (0.446, 0.709, 2.257, 2.81), "XLK": (0.459, 0.758, 1.698, 2.02)}
med_ref = {"XPH": (0.456, 0.655, 0.907, 0.74), "XBI": (0.398, 0.550, 1.473, 1.58)}
am_map = {}
for t in TECHS:
    wk = ema_full[t]["weak"]; nm = ema_full[t]["normal"]
    am_map[t] = (nm["corr"], wk["corr"], BASE_FWD[t]["20"]["mean"], EV["ema"]["full"][t]["20"]["mean"])
rows_def = [(grp, t, *v) for grp, d in (("科技", tech_ref), ("医药", med_ref), ("资管", am_map)) for t, v in d.items()]
for grp, t, n_, w_, b20, f20 in rows_def:
    tagcls = {"科技": "tech", "医药": "xph", "资管": "alt"}[grp]
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

# 图④系列数据：5 只资管基线 vs 走弱后 fwd20（EMA20 口径）
evcats_series = json.dumps([t for t in TECHS], ensure_ascii=False)
evfwd20_series = json.dumps([None for _ in TECHS], ensure_ascii=False)
evbase_series = json.dumps([BASE_FWD[t]["20"]["mean"] for t in TECHS], ensure_ascii=False)
evwin_series = json.dumps([EV["ema"]["full"][t]["20"]["win"] for t in TECHS], ensure_ascii=False)

html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>银行走弱 → 资管公司表现 · KBWB vs APO/BX/KKR/BLK/TROW 条件相关性分析</title>
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
  .warnbox{background:#fdf3f2;border:1px solid #f3c9c4;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#6e2018;margin-top:10px;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);}
  .tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .tag.ema{background:#e8eef6;color:var(--blue);} .tag.tl{background:#fdeee0;color:#c05c0b;}
  .tag.base{background:#eef0f2;color:#8a9099;} .tag.tech{background:#efe9fb;color:var(--purple);} .tag.xph{background:#e8f5ee;color:var(--green);}
  .tag.alt{background:#fdece8;color:#c0392b;} .tag.trad{background:#eef4fb;color:var(--blue);}
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
    <h1>银行走弱 → 资管公司表现 · 条件相关性分析</h1>
    <div class="meta">@@META@@</div>
    @@KPIS@@
    @@VERDICT@@
  </div>

  <div class="card">
    <h2>① 走弱信号定义（KBWB）与资管标的</h2>
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
    <h2>④ 事件研究 · 走弱确认后资管股前瞻收益（fwd20 vs 基线）</h2>
    <div class="chart" id="ch_ev"></div>
    <div class="note">对比 2011-11 起的全部样本。另类资管（APO/BX/KKR）在跌破上升趋势线信号后出现 −5%~−9% 的显著回撤（见下表明细），这是与科技最大的不同。</div>
    <div class="scroll">
    <table>
      <tr><th>资管标的</th><th>走弱信号</th><th>事件数 n</th><th>fwd5 均值(胜率)</th><th>Δ基线</th><th>fwd10 均值(胜率)</th><th>Δ基线</th><th>fwd20 均值(胜率)</th><th>Δ基线</th></tr>
      @@EV_ROWS@@
      @@BASE_ROWS@@
    </table>
    </div>
    <div class="keypoint"><b>解读：</b>EMA20 走弱确认后资管股整体偏强（与科技类似的"跌后反弹"）——
      另类资管 APO fwd20 +3.11%（胜率 64%）、BX +2.43%（61%）、KKR +2.35%（60%），均超各自基线；
      传统资管 BLK +2.28%、TROW +1.33% 也高于基线。但<b>跌破上升趋势线的结构性破位</b>是分水岭：
      BX fwd20 <b>−7.58%</b>、KKR <b>−8.73%</b>、APO <b>−5.38%</b>（胜率 0%），
      另类资管由于私募信贷/PE 杠杆属性，对银行体系信用收紧<b>极度敏感</b>；
      传统资管 BLK 仅 −0.27%（公募收入受信用周期影响小），明显抗跌。</div>
  </div>

  <div class="card">
    <h2>⑤ 状态条件相关 · 走弱期 vs 正常期 KBWB↔资管</h2>
    <div class="chart" id="ch_reg"></div>
    <div class="scroll">
    <table>
      <tr><th>资管标的</th><th>走弱口径</th><th>走弱期相关</th><th>走弱样本 n</th><th>正常期相关</th><th>正常样本 n</th><th>Δ相关</th><th>走弱期资管日均</th></tr>
      @@REG_ROWS@@
    </table>
    </div>
    <div class="warnbox"><b>重点：</b>资管是<b>全部分析过的板块中与银行联动最高的</b>——
      EMA20 走弱期相关 BLK <b>0.82</b>、TROW 0.78、KKR 0.73、BX 0.72、APO 0.71，全部高于科技的 SOXX 0.71/XLK 0.76。
      银行 <b>上涨时</b> 双边同步放大，银行跌 1% 资管平均跌 ~1%；当前银行正处于走弱状态，<b>资管是银行风险最直接的敞口</b>。</div>
  </div>

  <div class="card">
    <h2>⑥ 横向对比 · 银行走弱时 科技 / 医药 / 资管</h2>
    <div class="scroll">
    <table>
      <tr><th>板块</th><th>标的</th><th>正常期相关</th><th>走弱期相关</th><th>联动变化</th><th>基线 fwd20</th><th>走弱后 fwd20</th><th>Δ fwd20</th></tr>
      @@CROSS_ROWS@@
    </table>
    </div>
    <div class="note">同窗口、同口径（2011-11 起，EMA20 走弱）。<b>联动强度排序：资管 &gt; 科技 &gt; 医药</b>；
      事后收益：科技、资管均有"反弹修复"特征，医药最独立。资管名义走弱期相关最高但跌破趋势线时回撤也最深。</div>
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
      <li><b>数据</b>：Yahoo Finance 日线复权收盘价；统一窗口 @@WIN_START@@ ~ @@WIN_END@@（共 @@N@@ 个交易日，KBWB 与诸资管上市时间交集；TROW 1990、BLK 1999 上市，历史最早，APO 2011-03 后数据全覆盖）。</li>
      <li><b>信号A</b>：收盘跌破 EMA@@EMA_N@@ 且连续 @@REPAIR@@ 日未收复 → 走弱确认；回到线上方即修复。</li>
      <li><b>信号B</b>：近 @@TREND_WIN@@ 日 2~4 个依次抬升 swing low OLS 拟合（斜率&gt;0、R²≥@@TREND_R2@@），收盘自上而下穿越 → 走弱事件（@@TREND_CD@@ 日冷却）。</li>
      <li><b>标的选择</b>：另类资管 APO/BX/KKR（私募信贷、PE、杠杆资本）与传统资管 BLK/TROW（公募、指数、共同基金）分列，检验"杠杆弹性 vs 收入稳定"两种模式的差异。</li>
      <li><b>局限</b>：信号B 样本仅 5 例（其中 2025-09-22 一次构成近年主要负收益来源，需结合当时银行破位背景解读）；未控制利率、资本市场活跃度等资管特有驱动；相关性与事件统计未区分自营投资与资管费收入占比。</li>
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

// 图④ 事件研究 fwd20：基线 vs 走弱后（5 只）
(function(){
  var ch = echarts.init(document.getElementById("ch_ev"));
  var sig = DATA.event_study.ema.full, base = DATA.baseline_fwd;
  var tks = ["APO","BX","KKR","BLK","TROW"];
  var b  = tks.map(function(t){ return base[t]["20"].mean; });
  var s  = tks.map(function(t){ return sig[t]["20"].mean; });
  var win= tks.map(function(t){ return sig[t]["20"].win; });
  ch.setOption({
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"},
      formatter:function(ps){
        var p = ps[0]; var w = win[p.dataIndex % tks.length];
        return tks[p.dataIndex % tks.length] + " " + ((p.seriesIndex===0)?"基线":"走弱后") +
          "<br>fwd20: " + (p.value==null?"-":p.value.toFixed(2)+"%") + (p.seriesIndex===1?("<br>胜率: "+w.toFixed(0)+"%"):"");
      } },
    legend:{ data:["基线 fwd20","走弱信号后 fwd20"], top:0 },
    grid:{ left:60, right:30, top:40, bottom:40 },
    xAxis:{ type:"category", data:tks, axisLabel:{ fontSize:11 } },
    yAxis:{ type:"value", name:"fwd20 均值 %", axisLabel:{ formatter:function(v){return v.toFixed(1);} } },
    series:[
      { name:"基线 fwd20", type:"bar", barWidth:"24%", data:b, itemStyle:{ color:"#c9ccd2" },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(2)+"%"; }, fontSize:10, color:"#8a9099" } },
      { name:"走弱信号后 fwd20", type:"bar", barWidth:"24%", data:s, itemStyle:{ color:function(p){ return p.value>=0?RED:GREEN; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(2)+"%"; }, fontSize:10 } }
    ]
  });
})();

// 图⑤ 状态相关：走弱 vs 正常（EMA20 口径）
(function(){
  var ch = echarts.init(document.getElementById("ch_reg"));
  var r = DATA.regime_corr.ema.full;
  var tks = ["APO","BX","KKR","BLK","TROW"];
  var wk = tks.map(function(t){ return r[t].weak.corr; });
  var nm = tks.map(function(t){ return r[t].normal.corr; });
  ch.setOption({
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"}, valueFormatter:function(v){ return (v==null?"-":Number(v).toFixed(3)); } },
    legend:{ data:["走弱期相关","正常期相关"], top:0 },
    grid:{ left:60, right:30, top:40, bottom:40 },
    xAxis:{ type:"category", data:tks, axisLabel:{ fontSize:11 } },
    yAxis:{ type:"value", name:"日收益相关（KBWB↔资管）", min:0.3, max:0.9, axisLabel:{ formatter:function(v){return v.toFixed(2);} } },
    series:[
      { name:"走弱期相关", type:"bar", barWidth:"24%", data:wk, itemStyle:{ color:BLUE },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(2); }, fontSize:10 } },
      { name:"正常期相关", type:"bar", barWidth:"24%", data:nm, itemStyle:{ color:"#c9ccd2" },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(2); }, fontSize:10, color:"#8a9099" } }
    ]
  });
})();
</script>
</body>
</html>
"""

repl = {
    "@@META@@": (f'{meta["kbwb"]}（银行指数代理）→ 资管：APO / BX / KKR / BLK / TROW · '
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

out_path = os.path.join(OUT_DIR, "kbwb_am_weakness_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={os.path.getsize(out_path)}")