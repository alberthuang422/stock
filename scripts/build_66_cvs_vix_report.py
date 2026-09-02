# -*- coding: utf-8 -*-
"""66 号报告构建：CVS × VIX>18 —— 高波动期 CVS 的表现拆解（2015–2026 回测）
口径：CVS 未复权 close（价格收益、不含股息，用户口径）；VIX CBOE 官方收盘；SPY 未复权对照。
图/表数据来源：data/cvs, data/vix(CBOE), data/spy 日线 + results/cvs_vix_analysis.json。
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = r'C:\Users\Administrator\Desktop\stock'
OUT_DIR = os.path.join(ROOT, 'reports', '66_CVS与VIX高波动期表现')
os.makedirs(OUT_DIR, exist_ok=True)
LIB = os.path.join(ROOT, 'Temp', 'ccl_fetch', 'echarts_lib.js')


def rd(fp):
    return pd.read_csv(os.path.join(ROOT, fp), parse_dates=['date']).sort_values('date').reset_index(drop=True)


cvs = rd('data/cvs/CVS, 1D.csv')[['date', 'close']].rename(columns={'close': 'cvs'})
vix = rd('data/vix/VIX, 1D.csv')[['date', 'close']].rename(columns={'close': 'vix'})
spy = rd('data/spy/SPY, 1D.csv')[['date', 'close']].rename(columns={'close': 'spy'})

df = cvs.merge(vix, on='date').merge(spy, on='date')
df = df[df.date >= '2015-01-01'].reset_index(drop=True)
for c in ['cvs', 'spy']:
    df[f'{c}_ret'] = df[c].pct_change() * 100
for n in (1, 5, 20, 60):
    df[f'cvs_fwd{n}'] = df.cvs.shift(-n) / df.cvs * 100 - 100
    df[f'spy_fwd{n}'] = df.spy.shift(-n) / df.spy * 100 - 100
    df[f'exfwd{n}'] = df[f'cvs_fwd{n}'] - df[f'spy_fwd{n}']
hi = df.vix > 18

# ---------- 图表数据 ----------
C = {}
C['dates'] = [d.strftime('%Y-%m-%d') for d in df.date]
C['cvs_idx'] = [round(x, 1) for x in (df.cvs / df.cvs.iloc[0] * 100)]
C['spy_idx'] = [round(x, 1) for x in (df.spy / df.spy.iloc[0] * 100)]
C['vix'] = [round(x, 2) for x in df.vix]
C['cvs_px'] = [round(x, 2) for x in df.cvs]

# 高/低组 fwd 中位（绝对 + 超额）
def med(s):
    return round(float(np.nanmedian(s)), 2)


C['fwd'] = {'x': ['T+1', 'T+5', 'T+20', 'T+60'],
            'abs_hi': [med(df[hi][f'cvs_fwd{n}']) for n in (1, 5, 20, 60)],
            'abs_lo': [med(df[~hi][f'cvs_fwd{n}']) for n in (1, 5, 20, 60)],
            'exc_hi': [med(df[hi][f'exfwd{n}']) for n in (1, 5, 20, 60)],
            'exc_lo': [med(df[~hi][f'exfwd{n}']) for n in (1, 5, 20, 60)]}

# VIX 分桶
bins = [0, 15, 18, 25, 35, 100]
labs = ['≤15', '15-18', '18-25', '25-35', '>35']
df['vb'] = pd.cut(df.vix, bins=bins, labels=labs)
bk = {'name': [], 'n': [], 'fwd20': [], 'win': [], 'exc': [], 'exwin': []}
for lb in labs:
    g = df[df.vb == lb]
    f = g.cvs_fwd20
    e = g.exfwd20
    bk['name'].append(lb)
    bk['n'].append(int(len(g)))
    bk['fwd20'].append(med(f))
    bk['win'].append(round(float((f > 0).mean() * 100), 1))
    bk['exc'].append(med(e))
    bk['exwin'].append(round(float((e > 0).mean() * 100), 1))
C['bucket'] = bk

# 冲击日（VIX 单日 +>=15% 且收>18）
vixp = df.vix.shift(1)
shock = ((df.vix / vixp - 1) >= 0.15) & (df.vix > 18)
sv = df[shock].reset_index()
C['shock'] = {'x': [int(r['index']) for _, r in sv.iterrows()],
              'exc': [round(float(r.cvs_ret - r.spy_ret), 2) for _, r in sv.iterrows()],
              'd0': [round(float(r.cvs_ret), 2) for _, r in sv.iterrows()],
              'd': [r.date.strftime('%Y-%m-%d') for _, r in sv.iterrows()]}

# 主要持续段条形（超额 pp 排序）
o = json.load(open(os.path.join(ROOT, 'results', 'cvs_vix_analysis.json'), encoding='utf-8'))
segs = o['tab_segments']
segs_s = sorted(segs, key=lambda x: x['cvs_exc_pp'])
C['seg'] = {'name': [f"{s['start']}~{s['end'][5:]} ({s['days']}d)" for s in segs_s],
            'exc': [s['cvs_exc_pp'] for s in segs_s]}

# 年度概览（表）
yr = []
for y, g in df.groupby(df.date.dt.year):
    yr.append({'y': int(y), 'n_hi': int((g.vix > 18).sum()), 'tot': int(len(g)),
               'cvs': round(float((g.cvs.iloc[-1] / g.cvs.iloc[0] - 1) * 100), 1),
               'spy': round(float((g.spy.iloc[-1] / g.spy.iloc[0] - 1) * 100), 1),
               'vix_mean': round(float(g.vix.mean()), 1)})
C['year'] = yr

last = df.iloc[-1]
hi_last = df[df.date >= last.date - pd.Timedelta(days=252)]
C['meta'] = {
    'last_date': last.date.strftime('%Y-%m-%d'),
    'cvs_now': round(float(last.cvs), 2),
    'vix_now': round(float(last.vix), 2),
    'wk52_lo': round(float(hi_last.cvs.min()), 2),
    'wk52_hi': round(float(hi_last.cvs.max()), 2),
    'n_days': int(len(df)), 'n_hi': int(hi.sum()),
    'cvs_cum': round(float((df.cvs.iloc[-1] / df.cvs.iloc[0] - 1) * 100), 1),
    'spy_cum': round(float((df.spy.iloc[-1] / df.spy.iloc[0] - 1) * 100), 1),
}

DATA_JS = 'var CHART=' + json.dumps(C, ensure_ascii=False) + ';'

# ---------- 年度表 HTML ----------
rows_html = []
for r in yr:
    exc = round(r['cvs'] - r['spy'], 1)
    cls = 'up' if r['cvs'] >= 0 else 'dn'
    cls2 = 'up' if exc >= 0 else 'dn'
    rows_html.append(
        f"<tr><td>{r['y']}</td><td>{r['n_hi']} / {r['tot']}</td>"
        f"<td>{round(r['n_hi'] / r['tot'] * 100)}%</td>"
        f"<td class='{cls}'>{r['cvs']:+.1f}%</td><td class='{'up' if r['spy'] >= 0 else 'dn'}'>{r['spy']:+.1f}%</td>"
        f"<td class='{cls2}'>{exc:+.1f}pp</td><td>{r['vix_mean']}</td></tr>")
YEAR_ROWS = '\n'.join(rows_html)

# 冲击日代表事件表（取全部 99 次的精华：超额正负幅度大的 + 每次系统性恐慌）
evt = o['tab_shocks']['events']
key = ['2020-03-09', '2020-03-12', '2020-03-16', '2015-08-24', '2018-02-05', '2018-02-08',
       '2020-02-27', '2018-12-24', '2024-08-05', '2022-05-09', '2025-04-03', '2025-04-04',
       '2026-01-20', '2021-01-27', '2016-06-24', '2024-12-18']
ev_map = {e['date']: e for e in evt}
ev_rows = []
for k in key:
    if k not in ev_map:
        continue
    e = ev_map[k]
    cls = 'up' if e['cvs_exc_d0'] >= 0 else 'dn'
    cls5 = 'up' if e['cvs_fwd5_exc'] >= 0 else 'dn'
    ev_rows.append(
        f"<tr><td>{e['date']}</td><td>{e['vix']:.1f}</td><td style='text-align:right'>+{e['vix_chg_pct']:.0f}%</td>"
        f"<td class='{'up' if e['cvs_d0'] >= 0 else 'dn'}' style='text-align:right'>{e['cvs_d0']:+.1f}%</td>"
        f"<td class='{cls}' style='text-align:right'>{e['cvs_exc_d0']:+.2f}pp</td>"
        f"<td class='{cls5}' style='text-align:right'>{e['cvs_fwd5_exc']:+.1f}pp</td></tr>")
EVENT_ROWS = '\n'.join(ev_rows)

# 持续段表
seg_rows = []
for s in segs:
    cls = 'up' if s['cvs_exc_pp'] >= 0 else 'dn'
    clsC = 'up' if s['cvs'] >= 0 else 'dn'
    clsS = 'up' if s['spy'] >= 0 else 'dn'
    seg_rows.append(
        f"<tr><td>{s['start']}</td><td>{s['end']}</td><td>{s['days']}</td>"
        f"<td>{s['vix_hi']:.0f} → {s['vix_end']:.0f}</td>"
        f"<td class='{clsC}' style='text-align:right'>{s['cvs']:+.1f}%</td>"
        f"<td class='{clsS}' style='text-align:right'>{s['spy']:+.1f}%</td>"
        f"<td class='{cls}' style='text-align:right'>{s['cvs_exc_pp']:+.1f}pp</td></tr>")
SEG_ROWS = '\n'.join(seg_rows)

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CVS × VIX&gt;18 · 高波动期表现拆解（66 号）</title>
__ECHARTS_LIB__
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
  h3{font-size:13.5px;margin:16px 0 8px;color:#374151;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;}
  .note2{color:var(--sub);font-size:11px;font-weight:400;}
  td.up{color:var(--verm);font-weight:600;} td.dn{color:var(--teal);font-weight:600;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .chart.tall{height:460px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
  .callout{border:1px solid #f0d9c0;background:#fdf6ec;border-radius:10px;padding:12px 16px;font-size:13px;margin:10px 0;}
  .callout.blue{border-color:#cfe0f5;background:#f0f6fd;}
  .verdict{border-left:4px solid var(--verm);background:#fdf3ee;padding:10px 14px;border-radius:0 8px 8px 0;margin:8px 0;font-size:13px;}
  .verdict.gr{border-left-color:var(--teal);background:#eef6f2;}
  .verdict.amber{border-left-color:var(--amber);background:#fdf6ec;}
  .src{color:var(--sub);font-size:11.5px;margin-top:8px;}
  .term{border-bottom:1px dashed var(--blue);cursor:help;position:relative;}
  .term .tip{display:none;position:absolute;bottom:130%;left:0;background:#1f2329;color:#fff;padding:7px 10px;border-radius:7px;font-size:11.5px;width:235px;z-index:50;box-shadow:0 3px 10px rgba(0,0,0,.25);font-weight:400;line-height:1.5;}
  .term:hover .tip{display:block;}
  .kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0;}
  @media(max-width:900px){.kpi-row{grid-template-columns:repeat(2,1fr);}}
  .kpi{background:#fafbfc;border:1px solid var(--line);border-radius:10px;padding:10px 12px;}
  .kpi .k{color:var(--sub);font-size:11px;}
  .kpi .v{font-size:17px;font-weight:700;margin-top:2px;}
  .kpi .v.up{color:var(--verm);} .kpi .v.dn{color:var(--teal);}
  .kpi .s{font-size:10.5px;color:var(--sub);}
  ul.tight{padding-left:20px;margin:6px 0;}
  ul.tight li{margin-bottom:4px;font-size:13px;}
  .tag{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:600;margin-right:4px;}
  .tag.r{background:#fdeaea;color:var(--verm);} .tag.g{background:#e6f4ee;color:var(--teal);}
  .tag.a{background:#fdf3e0;color:var(--amber);} .tag.b{background:#e8f0fa;color:var(--blue);}
  .mini{color:var(--sub);font-size:11px;margin-top:4px;}
  .red{color:var(--verm);font-weight:700;} .grn{color:var(--teal);font-weight:700;}
</style>
</head>
<body>
<div class="wrap">

<div class="card">
  <h1>CVS Health × VIX&gt;18 <span class="tag b">66 号</span><span class="tag a">问答转正式报告</span></h1>
  <div class="meta">研究问题：<b>VIX 处于较高位（&gt;18）时，CVS 的表现如何？</b>｜ 窗口 <b>2015-01-02 ~ 2026-09-01（2933 个交易日）</b>｜ 口径：CVS 采用<b>用户提供的 TradingView BATS:CVS 日线</b>（<b>前复权</b>，2010-12-31 ~ 2026-09-01，收益≈含分红总回报）；SPY 未复权收盘价对照；VIX 用 CBOE 官方每日收盘 ｜ 交叉验证：新浪美股未复权（1980 起）与富途前复权两通道互证一致（2022 高点 111.25 / 95.30）</div>

  <div class="callout blue">
    <b>一句话结论：</b>VIX&gt;18 对 CVS 的<b>绝对收益没有择时价值</b>（高组与低组未来 1/5/20/60 日中位收益几乎无差别，p=0.54），但高 VIX 状态下 CVS <b>相对 SPY 显著跑输更多</b>（fwd20 超额 −1.0pp / fwd60 −2.8pp，p&lt;0.001）——恐慌后大盘反弹 CVS 跟不上。CVS 仅在 VIX 单日飙升当天有微弱防御性（99 次冲击日中位跑赢 SPY +0.8pp、73% 跑赢率），5 日后消失。其长期走势由自身医保基本面事件主导，与 VIX 高低无稳定关系。口径稳健性：改用前复权（含息）复跑结论不变。
  </div>

  <h3>核心速览</h3>
  <div class="kpi-row">
    <div class="kpi"><div class="k">CVS 现价（09-01，前复权=原始价）</div><div class="v">$97.60</div><div class="s">52 周 __META_WK__</div></div>
    <div class="kpi"><div class="k">VIX（09-01，CBOE）</div><div class="v grn">16.34</div><div class="s">&lt;18，处低波动区</div></div>
    <div class="kpi"><div class="k">2015 以来累计（CVS）</div><div class="v up">+43.5%</div><div class="s">前复权含息 ｜ 未复权价 +2.6% ｜ SPY +270%</div></div>
    <div class="kpi"><div class="k">2022 高点（两口径）</div><div class="v">95.3 / 111.3</div><div class="s">前复权 / 未复权 @ 02-08</div></div>
    <div class="kpi"><div class="k">样本（交易日）</div><div class="v">2,933</div><div class="s">VIX&gt;18 占 1,186 日 = 40%</div></div>
    <div class="kpi"><div class="k">高 VIX 日 fwd20</div><div class="v">+0.46%</div><div class="s">vs 低 VIX 日 +0.54%（无差异）</div></div>
    <div class="kpi"><div class="k">高 VIX 日 fwd60 超额</div><div class="v dn">−2.8pp</div><div class="s">vs 低组 −1.1pp（p&lt;0.001）</div></div>
    <div class="kpi"><div class="k">冲击日当日超额</div><div class="v up">+0.78pp</div><div class="s">99 次 VIX 单日 +≥15%，73% 跑赢</div></div>
  </div>
</div>

<div class="card">
  <h2>一、数据与口径校验</h2>
  <p>CVS 价格序列采用<b>用户提供的 TradingView BATS:CVS 日线导出</b>（前复权，3940 行，2010-12-31 起），覆盖到 2026-09-01。为确认口径做三源互证：①该文件 2022-02-08 高点 95.30 与用户行情软件记忆一致；②富途 over-HTTP 前复权实测同点位 95.30/94.94 <b>逐位吻合</b>；③新浪美股未复权数据同日 111.25（真实成交价），复权因子随时间从 0.674（2011）单调收敛至 1.0（2026）= 分红回溯特征，与无拆股事实一致 → 数据可靠。VIX 走 <span class="term">CBOE 官方<span class="tip">VIX 由芝加哥期权交易所计算发布，本报告用官方 VIX_History.csv 每日收盘值，比第三方转载更权威；个别交易日第三方值与官方结算有 ~0.5 的小出入。</span></span> 官方文件；SPY 用本地 Yahoo（新浪接口六锚点交叉一致）。</p>
  <div class="grid2">
    <div>
      <h3>CVS 2022 高点：两口径对照（防拉错校验）</h3>
      <div class="scroll"><table>
        <tr><th>口径</th><th style="text-align:right">最高（2022-02-08）</th><th>含义</th></tr>
        <tr><td>未复权（本报告收益口径）</td><td style="text-align:right">111.25 / 收盘 110.83</td><td>真实历史成交价</td></tr>
        <tr><td>前复权 adj（行情软件默认）</td><td class="up" style="text-align:right">95.30 / 收盘 94.94</td><td>回溯扣减此后累计分红</td></tr>
      </table></div>
      <div class="mini">CVS 无拆股，~14% 差幅全部来自 2022-02-08 之后累计分红的回溯调整——两口径都对。本报告主数据（用户提供 TradingView 文件）即前复权：2022 高点 95.30，与富途前复权实测逐位一致。</div>
    </div>
    <div>
      <h3>收益口径（重要）</h3>
      <ul class="tight">
        <li>主收益序列 = <b>TradingView 前复权收盘价</b>：无分红的相邻两日收益与未复权一致，仅在<b>除息日多计当日分红</b> → 近似「含息总回报」口径。</li>
        <li>对照组已用<b>新浪未复权（纯价格、不含息）</b>完整复跑：fwd20/60 绝对收益整体低约 0.2 / 0.7pp，高/低 VIX 组之间的<b>差异与全部定性结论不变</b> → 股息口径不改变结论。</li>
        <li>VIX&gt;18 为「当日收盘 VIX 值」判定；fwdN = 当日收盘买入持有 N 个交易日的收益。</li>
        <li>超额 = CVS 收益 − SPY 同期收益（百分点 pp）。</li>
      </ul>
    </div>
  </div>
</div>

<div class="card">
  <h2>二、全景：11.7 年 CVS 与 VIX（2015 = 100）</h2>
  <div id="ch_pan" class="chart tall"></div>
  <div class="src">上：CVS（蓝，前复权）与 SPY（橙）价格指数，2015-01-02=100 —— CVS 含息累计 +43.5%（纯价格仅 +2.6%），SPY 翻了 2.7 倍；下：VIX 每日收盘（CBOE）+ 18 阈值线（红），阴影为 VIX&gt;18 的持续高波动窗口。可拖拽缩放。</div>
</div>

<div class="card">
  <h2>三、核心对比：VIX&gt;18 日 vs VIX≤18 日</h2>
  <div class="scroll"><table>
    <tr><th>状态（当日收盘 VIX）</th><th style="text-align:right">样本</th><th style="text-align:right">当日收益中位</th><th style="text-align:right">T+1 中位</th><th style="text-align:right">T+5 中位</th><th style="text-align:right">T+20 中位</th><th style="text-align:right">T+60 中位</th><th style="text-align:right">T+20 胜率</th><th style="text-align:right">T+60 胜率</th></tr>
    __TAB3_ROWS__
  </table></div>
  <div class="mini">显著性（Mann-Whitney U，高组 vs 低组）：绝对收益 T+20 p=0.54、T+60 p=0.28（<b>不显著</b>）；超额 T+20 p=0.0005、T+60 p&lt;0.0001（<b>显著为负</b>）。<br>注意：CVS 含息也长期跑输 SPY（2015 起 ~−227pp），低组超额已为负；高 VIX 把「跑输」进一步放大 ~1pp/月，但绝对收益两组打平 → 高 VIX 后 CVS 不是跌得更狠，而是大盘反弹它不跟。</div>
  <div class="grid2">
    <div><h3>CVS 绝对收益（中位 %）</h3><div id="ch_fwd_abs" class="chart"></div></div>
    <div><h3>相对 SPY 超额（中位 pp）</h3><div id="ch_fwd_exc" class="chart"></div></div>
  </div>
</div>

<div class="card">
  <h2>四、VIX 分桶：CVS 后 20 日表现</h2>
  <div class="grid2">
    <div id="ch_bucket" class="chart"></div>
    <div class="scroll"><table>
      <tr><th>VIX 桶</th><th style="text-align:right">样本</th><th style="text-align:right">fwd20 中位</th><th style="text-align:right">fwd20 胜率</th><th style="text-align:right">超额中位</th><th style="text-align:right">跑赢率</th></tr>
      __BUCKET_ROWS__
    </table>
    <div class="mini">读数：真正让 CVS <b>绝对</b>赚钱的是极端恐慌桶（VIX&gt;35，63 日，fwd20 中位 +4.3%、胜率 67%），但同期跑赢 SPY 的只有约 30%——那是市场 V 型反弹的 β 而非 CVS 的 α。18–25（普通偏高波动）与 ≤15（过热低波动）都平淡。CVS 相对舒适区在 15–18。</div></div>
  </div>
</div>

<div class="card">
  <h2>五、恐慌冲击日（VIX 单日 +≥15% 且收 &gt;18，99 次）</h2>
  <div class="grid2">
    <div><div id="ch_shock" class="chart"></div>
      <div class="mini">横轴=2015 起交易日序号；纵轴=当日 CVS 相对 SPY 超额（pp）。红点=当日跑赢。汇总：99 次冲击日 CVS 当日中位 −1.4%（SPY 中位 −2.2% 量级），<b>超额中位 +0.78pp、73% 跑赢率</b>——弱防御真实存在但幅度小；随后 5 日超额归零（中位 −0.14pp、胜率 50%）。</div>
    </div>
    <div>
      <h3>代表性冲击日明细</h3>
      <div class="scroll" style="max-height:420px;overflow-y:auto;"><table>
        <tr><th>日期</th><th style="text-align:right">VIX</th><th style="text-align:right">日涨幅</th><th style="text-align:right">CVS 当日</th><th style="text-align:right">当日超额</th><th style="text-align:right">fwd5 超额</th></tr>
        __EVENT_ROWS__
      </table></div>
    </div>
  </div>
</div>

<div class="card">
  <h2>六、持续高 VIX 段（≥10 个连续交易日 VIX&gt;18，2015 以来 20 段）</h2>
  <div class="grid2">
    <div id="ch_seg" class="chart"></div>
    <div class="scroll" style="max-height:460px;overflow-y:auto;"><table>
      <tr><th>起</th><th>止</th><th style="text-align:right">天数</th><th style="text-align:right">VIX 区间</th><th style="text-align:right">CVS</th><th style="text-align:right">SPY</th><th style="text-align:right">超额</th></tr>
      __SEG_ROWS__
    </table></div>
  </div>
  <div class="mini">左图按超额从负到正排列。两大超长段（2020-02~2021-03 共 279 日 / 2022-01~2023-01 共 263 日）CVS 均跑输（含息口径 −8.6 / −1.3pp）；2020 全年 CVS −5.0% vs SPY +15.1%，2022 CVS −8.5% vs SPY −19.9%（熊市里相对抗跌但绝对仍亏）。2018-12 与 2025-03~05 两段 CVS 暴跌 −17 / −13pp，主因是 CVS 自身财报指引下修（与 VIX 无因果关系）。</div>
</div>

<div class="card">
  <h2>七、逐年概览</h2>
  <div class="scroll"><table>
    <tr><th>年份</th><th style="text-align:right">VIX&gt;18 天数</th><th style="text-align:right">占比</th><th style="text-align:right">CVS 年收益</th><th style="text-align:right">SPY 年收益</th><th style="text-align:right">年超额</th><th style="text-align:right">VIX 均值</th></tr>
    __YEAR_ROWS__
  </table></div>
  <div class="mini">含息口径下 CVS 跑赢 SPY 的年份有 2015（+5pp）、2021（+22pp）、2022 熊市（+11pp）、2025（+70pp，自身业绩修复+医保情绪）、2026 至今（+13pp）；跑输最惨为 2024 财报暴雷年（−66pp）。高 VIX 占比较高的年份表现好坏仍取决于 CVS 自身事件：2020 疫情 VIX 均值 29.3 却跑输 20pp，2022 无自身暴雷则相对抗跌。</div>
</div>

<div class="card">
  <h2>八、结论与使用边界</h2>
  <div class="verdict"><b>1｜高 VIX 不是 CVS 的择时信号。</b>VIX&gt;18 与 ≤18 两状态下 CVS 未来 1/5/20/60 日绝对收益几乎相同（p=0.54）；把它当「恐慌买入」或「恐慌卖出」条件都没有统计支持。</div>
  <div class="verdict"><b>2｜高 VIX 后 CVS 跑输大盘显著放大。</b>fwd20/fwd60 超额 −1.0/−2.8pp（vs 低组 −0.1/−1.1pp，p&lt;0.001）——高波动期大盘均值回归快，CVS β 仅 0.66 且无弹性叙事，反弹跟不上。若需在 VIX&gt;18 时表达市场反弹，CVS 是差的载体。</div>
  <div class="verdict"><b>3｜唯一防御窗口：冲击日当天。</b>VIX 单日飙升 ≥15% 的 99 个交易日，CVS 当日中位跑赢 +0.8pp（73%）；但 5 日后优势消失——是「跌得比大盘少」，不是「逆势上涨」，也不可延续为策略。</div>
  <div class="verdict"><b>4｜CVS 由自身事件定价。</b>2024 年两次财报暴雷（一年内腰斩）与 2026-05~07 的大涨均与 VIX 无关；个股 alpha 分析应围绕医保赔付率（MLR）、药房报销与监管政策展开，VIX 只贡献当日 β 扰动。</div>
  <div class="verdict amber"><b>使用边界：</b>①CVS 收益基于前复权价（≈含息总回报）；以未复权价（不含息）复跑，fwd 绝对收益约低 0.2~0.7pp，高/低组差异与结论不变；②VIX&gt;18 覆盖 40% 交易日、长段高度连续（2020/2022 主导），逐日样本有自相关，故超额负差异应读作「长段事件的平均」而非 1186 个独立实验；③极端桶（&gt;35）仅 63 日样本；④2022 高点提示 95 为前复权口径（本报告主数据即前复权），未复权真实成交价为 111.3。</div>
  <h3>当前快照（2026-09-01）</h3>
  <p>VIX 16.34（低波动区，≤18），CVS 97.60（前复权，最新日与未复权同值）距 2026-07-21 高点 109.92 回落 11.2%。历史统计口径下：当前既不在高 VIX 状态、也无冲击日信号——上述「高 VIX 效应」均不适用于当下；CVS 后续走势仍以自身医保基本面为主线。</p>
</div>

<div class="src">数据：CVS = 用户提供 TradingView BATS:CVS（前复权）｜ VIX = CBOE VIX_History（官方）｜ SPY = 本地 Yahoo ｜ 构建：scripts/build_66_cvs_vix_report.py ｜ 明细：results/cvs_vix_analysis.json ｜ 生成于 2026-09-02（用户数据复跑版）。本报告为统计研究，不构成投资建议。</div>
</div>

<script>
__DATA_JS__
(function(){
var C={blue:'#0072B2',orange:'#E69F00',sky:'#56B4E9',purple:'#9467bd',verm:'#D55E00',teal:'#009E73',amber:'#b45309',ink:'#374151',sub:'#6b7280',grid:'#eef0f3'};
var $={extend:function(a,b){for(var k in b){a[k]=b[k];}return a;}};
function base(grid){
  return {animation:false,textStyle:{color:C.ink},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:'#e5e7eb',textStyle:{color:'#1f2329',fontSize:12}},
    grid:grid||{left:58,right:20,top:34,bottom:28},
    legend:{top:4,textStyle:{fontSize:11,color:C.ink}},
    xAxis:{type:'category',axisLabel:{color:'#4b5563',fontSize:10.5},axisLine:{lineStyle:{color:'#d1d5db'}}},
    yAxis:{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}}};
}
// 图1 全景 双panel
(function(){
  var el=document.getElementById('ch_pan'); if(!el)return;
  var ch=echarts.init(el); var d=CHART;
  ch.setOption({animation:false,textStyle:{color:C.ink},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:'#e5e7eb',textStyle:{color:'#1f2329',fontSize:12}},
    legend:{data:['CVS','SPY','VIX'],top:0,textStyle:{fontSize:11,color:C.ink}},
    axisPointer:{link:[{xAxisIndex:'all'}]},
    grid:[{left:52,right:52,top:26,height:'56%'},{left:52,right:52,top:'72%',height:'22%'}],
    xAxis:[{type:'category',data:d.dates,axisLabel:{show:false},axisLine:{lineStyle:{color:'#d1d5db'}}},
           {type:'category',data:d.dates,gridIndex:1,axisLabel:{color:'#4b5563',fontSize:9.5,interval:'auto'}}],
    yAxis:[{type:'value',scale:true,axisLabel:{color:'#4b5563',fontSize:10,formatter:'{value}'},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',scale:true,position:'right',axisLabel:{color:'#4b5563',fontSize:10,formatter:'{value}'},splitLine:{show:false}},
           {type:'value',gridIndex:1,scale:true,axisLabel:{color:'#4b5563',fontSize:10},splitLine:{lineStyle:{color:C.grid}}}],
    dataZoom:[{type:'inside',xAxisIndex:[0,1],start:0,end:100},
              {type:'slider',xAxisIndex:[0,1],start:0,end:100,bottom:0,height:16}],
    series:[
      {name:'CVS',type:'line',data:d.cvs_idx,symbol:'none',lineStyle:{color:C.blue,width:1.8},itemStyle:{color:C.blue}},
      {name:'SPY',type:'line',yAxisIndex:1,data:d.spy_idx,symbol:'none',lineStyle:{color:C.orange,width:1.6},itemStyle:{color:C.orange}},
      {name:'VIX',type:'line',xAxisIndex:1,yAxisIndex:2,data:d.vix,symbol:'none',lineStyle:{color:C.purple,width:1.3},
        markLine:{silent:true,symbol:'none',data:[{yAxis:18,lineStyle:{color:C.verm,type:'dashed'},label:{formatter:'VIX=18',color:C.verm,fontSize:10,position:'insideEndTop'}}]}}
    ]});
  window.addEventListener('resize',function(){ch.resize();});
})();
// 图2 高/低组 fwd 阶梯（绝对）
(function(){
  var el=document.getElementById('ch_fwd_abs'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.fwd;
  ch.setOption($.extend(base(),{legend:{data:['VIX>18','VIX<=18'],top:0},
    yAxis:{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{lineStyle:{color:C.grid}}},
    series:[
      {name:'VIX>18',type:'bar',data:d.abs_hi,barGap:'20%',itemStyle:{color:C.verm},
        label:{show:true,position:'top',fontSize:9.5,formatter:function(p){return p.value.toFixed(2)+'%';}}},
      {name:'VIX<=18',type:'bar',data:d.abs_lo,itemStyle:{color:C.sky},
        label:{show:true,position:'top',fontSize:9.5,formatter:function(p){return p.value.toFixed(2)+'%';}}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 图3 超额
(function(){
  var el=document.getElementById('ch_fwd_exc'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.fwd;
  function col(v){return v>=0?C.verm:C.teal;}
  ch.setOption($.extend(base(),{legend:{data:['VIX>18','VIX<=18'],top:0},
    yAxis:{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}pp'},splitLine:{lineStyle:{color:C.grid}}},
    series:[
      {name:'VIX>18',type:'bar',data:d.exc_hi.map(function(v){return {value:v,itemStyle:{color:col(v)}};}),barGap:'20%',
        label:{show:true,position:'top',fontSize:9.5,formatter:function(p){return p.value.toFixed(2)+'pp';}}},
      {name:'VIX<=18',type:'bar',data:d.exc_lo.map(function(v){return {value:v,itemStyle:{color:col(v)}};})}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 图4 分桶
(function(){
  var el=document.getElementById('ch_bucket'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.bucket;
  ch.setOption($.extend(base(),{legend:{data:['fwd20 中位','胜率'],top:0},
    grid:{left:52,right:48,top:34,bottom:30},
    yAxis:[{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',min:30,max:90,axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}%'},splitLine:{show:false}}],
    series:[
      {name:'fwd20 中位',type:'bar',data:d.fwd20.map(function(v){return {value:v,itemStyle:{color:v>=0?C.verm:C.teal}};}),barWidth:'40%',
        label:{show:true,position:'top',fontSize:9,formatter:function(p){return p.value.toFixed(2)+'%';}}},
      {name:'胜率',type:'line',yAxisIndex:1,data:d.win,symbol:'circle',symbolSize:6,lineStyle:{color:C.blue,width:1.6},itemStyle:{color:C.blue}}
    ]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
// 图5 冲击日散点
(function(){
  var el=document.getElementById('ch_shock'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.shock;
  ch.setOption({animation:false,textStyle:{color:C.ink},
    tooltip:{trigger:'item',backgroundColor:'#fff',borderColor:'#e5e7eb',textStyle:{color:'#1f2329',fontSize:12},
      formatter:function(p){var i=p.dataIndex;return d.d[i]+' &nbsp;VIX冲击日<br>CVS当日 <b>'+d.d0[i].toFixed(2)+'%</b> · 当日超额 <b>'+p.value[1].toFixed(2)+'pp</b>';}},
    grid:{left:52,right:20,top:30,bottom:28},
    xAxis:{type:'value',name:'2015→交易日序号',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}},
    yAxis:{type:'value',name:'当日超额 pp',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}},
    series:[{type:'scatter',symbolSize:8,
      data:d.x.map(function(x,i){return {value:[x,d.exc[i]],d0:d.d0[i],dt:d.d[i],itemStyle:{color:d.exc[i]>=0?C.verm:C.teal,opacity:.72}};}),
      markLine:{silent:true,symbol:'none',data:[{yAxis:0,lineStyle:{color:'#9ca3af',type:'dashed'}}]},
      markPoint:{data:[{type:'max',name:'最高超额',itemStyle:{color:C.verm}},{type:'min',name:'最低超额',itemStyle:{color:C.teal}}]}}
    ]});
  window.addEventListener('resize',function(){ch.resize();});
})();
// 图6 持续段条形
(function(){
  var el=document.getElementById('ch_seg'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.seg;
  ch.setOption($.extend(base(),{grid:{left:210,right:56,top:16,bottom:24},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
    xAxis:{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}pp'},splitLine:{lineStyle:{color:C.grid}}},
    yAxis:{type:'category',data:d.name,axisLabel:{color:'#4b5563',fontSize:9.5}},
    series:[{name:'CVS−SPY 超额',type:'bar',data:d.exc.map(function(v){return {value:v,itemStyle:{color:v>=0?C.verm:C.teal}};}),
      barWidth:'62%',label:{show:true,position:'right',fontSize:9,formatter:function(p){return p.value.toFixed(1)+'pp';}}}]}));
  window.addEventListener('resize',function(){ch.resize();});
})();
})();
</script>
</body>
</html>
"""

# 第三节核心对比表 4 行（动态取自 results json，与复跑数据强一致）
FWD = o['tab_fwd_abs_exc']
D0 = o['tab_d0']


def row3(tag, label, is_abs, g):
    def fmtv(x, unit):
        return f'{x:+.2f}'.replace('-', '−') + unit
    d0v = D0[g]['cvs_d0_med'] if is_abs else D0[g]['cvs_exc_d0_med']
    unit = '%' if is_abs else 'pp'
    f = FWD[g]
    fe = FWD[g + '_exc']
    w20 = f['fwd20']['win'] if is_abs else fe['fwd20']['win']
    w60 = f['fwd60']['win'] if is_abs else fe['fwd60']['win']
    cls0 = 'dn' if d0v < 0 else ''
    cells = [f"<td class='{cls0}' style='text-align:right'>{fmtv(d0v, unit)}</td>"]
    for n in (1, 5, 20, 60):
        v = (f if is_abs else fe)[f'fwd{n}']['med']
        cls = 'dn' if v < 0 else ''
        cells.append(f"<td class='{cls}' style='text-align:right'>{fmtv(v, unit)}</td>")
    n = f"{o['hi_days'] if g == 'VIX>18' else o['lo_days']:,}"
    return (f"<tr><td><span class=\"tag {tag}\">{label}</span></td>"
            f"<td style='text-align:right'>{n}</td>{''.join(cells)}"
            f"<td style='text-align:right'>{w20:.1f}%</td><td style='text-align:right'>{w60:.1f}%</td></tr>")


TAB3_ROWS = '\n'.join([
    row3('a', 'VIX &gt; 18（绝对收益）', True, 'VIX>18'),
    row3('g', 'VIX ≤ 18（绝对收益）', True, 'VIX<=18'),
    row3('a', 'VIX &gt; 18（相对 SPY 超额）', False, 'VIX>18'),
    row3('g', 'VIX ≤ 18（相对 SPY 超额）', False, 'VIX<=18'),
])

# 组装（模板占位符）
bk_rows = []
for i, lb in enumerate(labs):
    cls = 'up' if bk['fwd20'][i] >= 0 else 'dn'
    cls2 = 'up' if bk['exc'][i] >= 0 else 'dn'
    bk_rows.append(
        f"<tr><td>{lb}</td><td style='text-align:right'>{bk['n'][i]}</td>"
        f"<td class='{cls}' style='text-align:right'>{bk['fwd20'][i]:+.2f}%</td>"
        f"<td style='text-align:right'>{bk['win'][i]:.0f}%</td>"
        f"<td class='{cls2}' style='text-align:right'>{bk['exc'][i]:+.2f}pp</td>"
        f"<td style='text-align:right'>{bk['exwin'][i]:.0f}%</td></tr>")
BUCKET_ROWS = '\n'.join(bk_rows)

M = C['meta']
html = HTML.replace('__ECHARTS_LIB__', '<script>' + open(LIB, encoding='utf-8').read() + '</script>')
html = html.replace('__DATA_JS__', DATA_JS)
html = html.replace('__BUCKET_ROWS__', BUCKET_ROWS)
html = html.replace('__TAB3_ROWS__', TAB3_ROWS)
html = html.replace('__EVENT_ROWS__', EVENT_ROWS)
html = html.replace('__SEG_ROWS__', SEG_ROWS)
html = html.replace('__YEAR_ROWS__', YEAR_ROWS)
html = html.replace('__META_WK__', f"${M['wk52_lo']:.2f} ~ ${M['wk52_hi']:.2f}")

out = os.path.join(OUT_DIR, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('written:', out)
print('size: %.0f KB' % (os.path.getsize(out) / 1024))
for k in ['__ECHARTS_LIB__', '__DATA_JS__', '__BUCKET_ROWS__', '__EVENT_ROWS__', '__SEG_ROWS__', '__YEAR_ROWS__', '__META_WK__']:
    assert k not in html, f'未替换占位符: {k}'
print('OK: 占位符全部替换')
