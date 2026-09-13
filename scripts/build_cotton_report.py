# -*- coding: utf-8 -*-
"""构建 93 号报告 v2：棉花库消比（剥离中国国储棉主口径）+ ENSO —— 2026-09-12 修订"""
import json
import os
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "reports", "93_棉花库消比与厄尔尼诺_20260912")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "index.html")

g = pd.read_csv(os.path.join(BASE, "data", "cotton", "cotton_global_sd.csv"))
g = g.rename(columns={g.columns[0]: "MY"}).set_index("MY")
M = pd.read_csv(os.path.join(BASE, "data", "cotton", "cotton_tradeable.csv"))
M = M.rename(columns={M.columns[0]: "MY"}).set_index("MY")
cx = pd.read_csv(os.path.join(BASE, "results", "cotton_enso_cross_exCN.csv"))
enso = json.load(open(os.path.join(BASE, "results", "cotton_enso.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(BASE, "results", "cotton_tradeable.json"), encoding="utf-8"))
fund = json.load(open(os.path.join(BASE, "results", "cotton_fundamentals.json"), encoding="utf-8"))
xcn = json.load(open(os.path.join(BASE, "results", "cotton_enso_cross_exCN.json"), encoding="utf-8"))

BALE_T = 480 * 0.45359237 / 1000

wb = load_workbook(os.path.join(BASE, "data", "sugar", "raw", "pink_sheet_2026.xlsx"),
                   read_only=True, data_only=True)
rows = list(wb["Monthly Prices"].iter_rows(values_only=True))
hdr = {str(x).strip(): i for i, x in enumerate(rows[4]) if x}
i_c = hdr["Cotton, A Index"]
pr = []
for r in rows[6:]:
    if r[0] and re.match(r"^\d{4}M\d{2}$", str(r[0])):
        v = pd.to_numeric(r[i_c], errors="coerce")
        if pd.notna(v):
            pr.append((str(r[0]), float(v)))
P = dict(pr)
KM = sorted(P)

# 图1 全球 vs 剥离中国库消比（双线）
d1 = []
for y in M.index:
    if y in g.index:
        d1.append([f"{int(y)}", round(float(g.loc[y, "StockToUse"]), 1),
                   round(float(M.loc[y, "R1_sur"]), 1)])

# 图2 产量/消费/库存（千吨）
rec = g.loc[2005:]
d2 = [[f"{int(y)}", round(float(rec.loc[y, "Production"] * BALE_T / 1000), 1),
       round(float(rec.loc[y, "Domestic Use"] * BALE_T / 1000), 1),
       round(float(rec.loc[y, "Ending Stocks"] * BALE_T / 1000), 1)] for y in rec.index]

# 图3 期限扫描
d3 = [[str(k), v] for k, v in enso["term_scan"].items()]

# 图4 事件 T12
e = cx.dropna(subset=["T12"]).copy()
d4 = [[r.onset, round(float(r.T12), 1), round(float(r.peak), 2)] for r in e.itertuples()]

# 图5 库存分组：两口径对照（4 根柱）
med_cn = xcn["median_exCN"]
med_w = xcn["median_w"]
d5 = [
    ["全球·低\n(<%.0f%%)" % med_w, xcn["low_exCN"]["T12_med"], xcn["low_exCN"]["win"]],
    ["全球·高\n(≥%.0f%%)" % med_w, None, None],  # 占位，用下面计算
    ["剥离中·低\n(<%.0f%%)" % med_cn, xcn["low_exCN"]["T12_med"], xcn["low_exCN"]["win"]],
    ["剥离中·高\n(≥%.0f%%)" % med_cn, xcn["high_exCN"]["T12_mean"], xcn["high_exCN"]["win"]],
]
# 全球高低（从 cross csv 重算）
cw = cx.dropna(subset=["T12"])
glo_lo = cw[cw.sur_w < med_w]["T12"]
glo_hi = cw[cw.sur_w >= med_w]["T12"]
cn_lo = cw[cw.sur_exCN < med_cn]["T12"]
cn_hi = cw[cw.sur_exCN >= med_cn]["T12"]
d5 = [
    ["全球·低", round(float(glo_lo.median()), 1), round(float((glo_lo > 0).mean() * 100), 0)],
    ["全球·高", round(float(glo_hi.median()), 1), round(float((glo_hi > 0).mean() * 100), 0)],
    ["剥离中·低", round(float(cn_lo.median()), 1), round(float((cn_lo > 0).mean() * 100), 0)],
    ["剥离中·高", round(float(cn_hi.median()), 1), round(float((cn_hi > 0).mean() * 100), 0)],
]
d5_mean = [
    ["全球·低", round(float(glo_lo.mean()), 1), round(float((glo_lo > 0).mean() * 100), 0)],
    ["全球·高", round(float(glo_hi.mean()), 1), round(float((glo_hi > 0).mean() * 100), 0)],
    ["剥离中·低", round(float(cn_lo.mean()), 1), round(float((cn_lo > 0).mean() * 100), 0)],
    ["剥离中·高", round(float(cn_hi.mean()), 1), round(float((cn_hi > 0).mean() * 100), 0)],
]

# 图6 R² 对比
IND = ["w_sur", "w_stocks", "R1_sur", "R2_sur", "core_sur", "core_sur_own", "core_share", "core_surplus", "big3_sur"]
LBL = tr["labels"]
d6 = [[LBL[c], tr["diff_full"][c]["R2"], tr["diff_2000_2026"][c]["R2"]] for c in IND]

# 图7 中国库存占比
piv = pd.read_csv(os.path.join(BASE, "data", "sugar", "raw", "psd", "psd_alldata.csv"), low_memory=False)
piv = piv[piv.Commodity_Code == 2631000].copy()
piv["Value"] = pd.to_numeric(piv.Value, errors="coerce")
pv = piv[piv.Attribute_Description == "Ending Stocks"].pivot_table(
    index="Market_Year", columns="Country_Name", values="Value", aggfunc="first")
yrs7 = list(range(2010, 2027))
d7_cn, d7_w, d7_share = [], [], []
for y in yrs7:
    cn = pv.loc[y, "China"] if pd.notna(pv.loc[y, "China"]) else 0
    w = float(g.loc[y, "Ending Stocks"])
    d7_cn.append(round(float(cn * BALE_T / 1000), 1))
    d7_w.append(round(float(w * BALE_T / 1000), 1))
    d7_share.append(round(float(cn / w * 100), 1) if w else None)

# 图8 路径对比
def path(year, mon, a, b):
    out = []
    for k in range(a, b + 1):
        m = mon + k
        y = year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        key = f"{y}M{m:02d}"
        out.append([k, P.get(key)])
    return out

p97 = path(1997, 5, -12, 18)
p26 = path(2026, 5, -12, 18)
d8_m = [x[0] for x in p97]
d8_97 = [x[1] for x in p97]
d8_26 = [x[1] for x in p26]

# 表格
sur_stats = fund["stock_to_use_stats"]
reg = enso["reg_H12"]

rows_diff = ""
for c in IND:
    f, a, b = tr["diff_full"][c], tr["diff_1960_1999"][c], tr["diff_2000_2026"][c]
    star = lambda p: "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))
    rows_diff += (f"<tr><td>{LBL[c]}</td><td class='num'>{f['r']:+.3f}{star(f['p'])}</td>"
                  f"<td class='num'>{f['R2']:.3f}</td><td class='num'>{a['r']:+.2f}</td>"
                  f"<td class='num'>{b['r']:+.2f}{star(b['p'])}</td><td class='num'>{b['R2']:.3f}</td></tr>")

band_rows = ""
BB = enso["by_band"]
BORDER = {"超强(>=2.0)": "超强 ≥2.0", "强(1.5-2.0)": "强 1.5–2.0",
          "中等(1.0-1.5)": "中等 1.0–1.5", "弱(0.5-1.0)": "弱 0.5–1.0"}
for b in BB:
    band_rows += (f"<tr><td>{BORDER.get(b['band'], b['band'])}</td><td class='num'>{b['n']}</td>"
                  f"<td class='num'>{b['T12_abs_mean']:+.1f}%</td><td class='num'>{b['T12_abs_med']:+.1f}%</td>"
                  f"<td class='num'>{b['win']:.0f}%</td><td class='num'>{b['T12_exc_mean']:+.1f}%</td>"
                  f"<td class='num'>{b['T24_abs_mean']:+.1f}%</td></tr>")

cur = tr["current"]
cur_rows = ""
for c in ["w_sur", "R1_sur", "R2_sur", "core_sur", "core_sur_own", "big3_sur"]:
    v = cur[c]
    cur_rows += (f"<tr><td>{LBL[c]}</td><td class='num'>{v['value']:,.1f}</td>"
                 f"<td class='num'>{v['pct']:.1f}%</td><td class='num'>{v['median']:,.1f}</td></tr>")

# 1972 跳槽表
jump_rows = ""
for r in cx[cx.onset.str.startswith("1972")].itertuples():
    jump_rows += (f"<tr><td>1972-06（峰值 {r.peak:.2f}）</td>"
                  f"<td class='num'>{r.sur_w:.1f}%</td><td class='num'>低（&lt;{med_w:.0f}%）</td>"
                  f"<td class='num'>{r.sur_exCN:.1f}%</td><td class='num'>高（≥{med_cn:.0f}%）</td>"
                  f"<td class='num red'>+{r.T12:.1f}%</td></tr>")

DD = json.dumps({"d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5, "d5m": d5_mean,
                 "d6": d6, "d7_cn": d7_cn, "d7_w": d7_w, "d7_share": d7_share,
                 "yrs7": [str(y) for y in yrs7], "d8_m": d8_m, "d8_97": d8_97, "d8_26": d8_26},
                ensure_ascii=False)

r1_cur = cur["R1_sur"]["value"]
r1_pct = cur["R1_sur"]["pct"]
r1_med = cur["R1_sur"]["median"]
sur_cur = sur_stats["current"]

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>93 · 棉花库消比（剥离中国国储棉主口径）与厄尔尼诺 · 2026-09-12</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --oi-green:#009E73;
        --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec; --card:#fff; --bg:#f5f7fa; --ref-bg:#eef2f7;}}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px;}}
  .wrap{{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}}
  .hero{{background:linear-gradient(135deg,#3a2a1a 0%,#6b4a26 100%);color:#fff;border-radius:12px;padding:28px 32px;margin-bottom:20px;}}
  .hero h1{{font-size:23px;margin-bottom:6px;line-height:1.45;}}
  .hero .meta{{font-size:12.5px;opacity:.85;margin-top:4px;}}
  .hero .sub{{margin-top:12px;font-size:14px;opacity:.96;border-top:1px solid rgba(255,255,255,.25);padding-top:10px;}}
  .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}}
  .kcard{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}}
  .kcard .lab{{font-size:12px;color:var(--sub);margin-bottom:3px;}}
  .kcard .val{{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;}}
  .kcard .note{{font-size:12px;color:var(--sub);margin-top:3px;}}
  .red{{color:#b2182b;}} .green{{color:#1a7a3a;}}
  h2{{font-size:19px;margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--oi-verm);}}
  h3{{font-size:16px;color:#6b4a26;margin:18px 0 8px;}}
  .panel{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin-bottom:16px;}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;}}
  th{{background:#eef2f7;color:#12365e;padding:6px 7px;text-align:left;border-bottom:2px solid var(--line);font-weight:600;}}
  td{{padding:5px 7px;border-bottom:1px solid var(--line);vertical-align:middle;}}
  tr:last-child td{{border-bottom:none;}}
  .num{{font-variant-numeric:tabular-nums;text-align:right;}}
  th.num{{text-align:right;}}
  .src{{font-size:11px;color:var(--sub);margin-top:7px;line-height:1.5;}}
  .callout{{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:14px 18px;margin:14px 0;font-size:13.5px;}}
  .warn{{background:#fdf2f2;border:1px solid #eccaca;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}}
  .ok{{background:#f0f8f4;border:1px solid #c9e5d6;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:13px;}}
  .chart{{width:100%;height:330px;}}
  .footer{{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}}
  code{{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px;}}
  ul{{padding-left:22px;}} li{{margin:4px 0;}}
  @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr);}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>棉花库消比（剥离中国国储棉主口径）· ENSO —— v2 修订</h1>
    <div class="meta">报告编号 93 ｜ 数据源：USDA FAS PSD（2026-09-11）＋ World Bank Pink Sheet 棉花 A Index（1960M01–2026M08）＋ NOAA CPC ONI ｜ 2026-09-12（v2：剥离中国重做）</div>
    <div class="sub">结论一句话（v2 修订）：<b>把中国国储棉从全球库存里剥离后，上一轮的"低库存 = 真利多"结论被推翻</b>——
    ① 全球库消比 {sur_cur:.1f}%（{sur_stats['percentile_since_1960']:.0f} 分位偏松）<b>是国储棉制造的假象</b>，剥离中国后仅 <b>{r1_cur:.1f}%（{r1_pct:.0f} 分位偏紧）</b>，2014 年 92.1% 的"历史峰值"在剥离后直接消失（剩 32.8%）；
    ② 但<b>剥离中国后，"低库存组 T+12 更好"不复存在</b>——低库存组中位从 +14.2% 塌到 <b>+2.6%（胜率 78%→56%）</b>，高库存组反而 +3.4%；
    ③ 根源 = <b>1972 年极端事件（T+12 +62.7%）在两种口径下"跳槽"</b>（全球口径归低库存、剥离后归高库存），且"低库存利多"的信号主要来自<b>中国库存低 → 中国补库需求</b>，剥离中国后这个需求侧信号就丢了。
    </b></div>
  </div>

  <div class="cards">
    <div class="kcard"><div class="lab">剥离中国 · 库消比（MY2026）</div><div class="val red">{r1_cur:.1f}%</div>
      <div class="note">{r1_pct:.0f} 分位 ｜ 中位 {r1_med:.1f}% ｜ 全球口径 {sur_cur:.1f}%</div></div>
    <div class="kcard"><div class="lab">2014 峰值（剥离后）</div><div class="val">32.8%</div>
      <div class="note">全球口径 92.1% 是国储收储造成 ｜ 剥离后峰值消失</div></div>
    <div class="kcard"><div class="lab">低库存组 T+12（剥离后）</div><div class="val">+2.6%</div>
      <div class="note">中位 ｜ 胜率 56% ｜ 全球口径曾 +14.2%/78%</div></div>
    <div class="kcard"><div class="lab">棉花 × ENSO（剥商品β）</div><div class="val">+{reg['ctrl_coef']:+.1f}%</div>
      <div class="note">t={reg['ctrl_t']:.2f} 不显著 ｜ 专属效应弱（不变）</div></div>
  </div>

  <h2>一、为什么必须剥离中国国储棉</h2>
  <div class="panel">
    <div id="c7" class="chart"></div>
    <div class="src">中国期末库存 vs 全球库存（左轴，百万吨）＋ 中国占全球份额（右轴）。
    <b>2014 年中国库存占全球 64.3%</b>（收储巅峰，库消比 192.5%），2026 年仍占 49.8%。
    <b>中国国储棉是"政策库存"，不参与或仅边际参与国际贸易</b>——把它算进"全球库消比"，会得出"全球偏松"的假象。</div>
  </div>
  <div class="panel">
    <div id="c1" class="chart"></div>
    <div class="src"><b>全球口径 vs 剥离中国口径的库消比（1960–2026）</b>。两条线在 2011 年后严重分叉：
    全球口径在 2014 年冲到 92.1%（国储收储），剥离中国口径只有 32.8% 且长期窄幅波动。
    MY2026 剥离中国 {r1_cur:.1f}%（23 分位偏紧）——<b>可贸易库存的实际松紧，与"全球偏松"的直观印象相反</b>。</div>
  </div>

  <h2>二、剥离中国后，"低库存 = 真利多"被推翻（本次修订的核心）</h2>
  <div class="panel">
    <div id="c5" class="chart"></div>
    <div class="src">厄尔尼诺事件按"事发榨季库消比"分组后的 T+12 棉价收益（中位，左轴）与胜率（右轴），
    <b>全球口径 vs 剥离中国口径对照</b>。全球口径下"低库存组"中位 +14.2%、胜率 78%；<b>剥离中国后低库存组只剩 +2.6%、胜率 56%</b>，高库存组反而 +3.4%、胜率 60%。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>1972-06 事件</th><th class="num">全球库消比</th><th>全球口径分组</th><th class="num">剥离中国库消比</th><th>剥离后分组</th><th class="num">T+12</th></tr>
      {jump_rows}
    </table>
    <div class="src">1972 年是"苏联抢购美国谷物 + 全球商品超级牛市"的极端年（棉价 T+12 暴涨 +62.7%）。
    它在全球口径下库消比 39.8%（&lt;中位 52.6%，归"低库存"），把低库存组均值拉到 +13.7%；
    <b>剥离中国后库消比 35.6%（≥中位 35.6%，恰好归"高库存"）</b>，于是"低库存更好"的结论随之反转。</div>
  </div>
  <div class="warn">
    <b>稳健性结论（诚实修正）：</b>"低库存组 T+12 更好"这一结论<b>对口径选择高度敏感，剥离中国后不成立</b>。
    剔除 1972 后全球口径低库存组中位仍 +13.6%、胜率 75%（低库存利多仍在），但剥离中国口径低库存组中位 +2.6%、胜率 56%
    （低库存<b>无优势甚至略差</b>）。<b>机制</b>：全球库消比的"低"主要由"中国库存低"驱动，而<b>中国库存低 = 中国要补库进口 = 需求侧利多</b>；
    剥离中国后，剩下的"可贸易库存低"丢了这层需求信号，只剩被宏观危机反复干扰的供给侧信号。
    这直接呼应白糖 91 号的结论——<b>盲目剥离中国有害</b>，只是棉花这里更彻底：剥离后连"方向"都变了。
  </div>

  <h2>三、棉花对 ENSO 的响应：有方向、无专属（不变）</h2>
  <div class="panel">
    <div id="c3" class="chart"></div>
    <div class="src">期限扫描 corr(ONI_t, 未来 H 月棉价对数收益)，峰值 H=12（r=+0.174）。此结论与口径无关（价格序列不变）。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>品种</th><th class="num">H=12 β</th><th class="num">t</th><th class="num">剥商品β后</th><th class="num">剥后 t</th><th>结论</th></tr>
      <tr><td><b>棉花（本报告）</b></td><td class="num">+5.45%/℃</td><td class="num">1.77</td><td class="num red">+1.17%/℃</td><td class="num red">0.48</td><td>边缘显著，<b>无专属效应</b></td></tr>
      <tr><td>橡胶（89 号）</td><td class="num">+12.3%/℃</td><td class="num">4.30</td><td class="num">+8.6%/℃</td><td class="num">强</td><td>强专属效应</td></tr>
      <tr><td>白糖（90 号）</td><td class="num">−2.18%/℃</td><td class="num">−0.49</td><td class="num">−7.49%/℃</td><td class="num">−1.66</td><td>无稳定正响应</td></tr>
    </table>
  </div>
  <div class="panel">
    <div id="c4" class="chart"></div>
    <div class="src">22 次厄尔尼诺事件的 T+12 收益（按峰值强度着色），高度发散。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>强度档</th><th class="num">n</th><th class="num">T+12 均值</th><th class="num">T+12 中位</th><th class="num">胜率</th><th class="num">T+12 超额</th><th class="num">T+24</th></tr>
      {band_rows}
    </table>
  </div>

  <h2>四、可贸易库存与解释力（全球口径仍最强）</h2>
  <div class="panel">
    <div id="c6" class="chart"></div>
    <div class="src">各口径解释力 R²（Δ指标 vs Δlog价格）。<b>全球库消比两窗口都最强（0.288/0.287）</b>；
    剥离中国（0.282/0.20）、剥离中印（0.253/0.18）、出口国口径（0.217/0.15）都更低、无反超。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>口径</th><th class="num">全样本 r</th><th class="num">R²</th><th class="num">1960–99 r</th><th class="num">2000–26 r</th><th class="num">R²</th></tr>
      {rows_diff}
    </table>
    <div class="src">n≈65。*** p&lt;0.01，** p&lt;0.05，* p&lt;0.10。⚠️ 注意：<b>剥离中国口径的解释力反而更低</b>（0.282 vs 全球 0.288），
    再次说明中国库存是棉价的<b>有效信号</b>而非噪声——剥离它不改善、反而略损解释力。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>口径</th><th class="num">当前值</th><th class="num">分位</th><th class="num">中位</th></tr>
      {cur_rows}
    </table>
    <div class="src">分位落差：全球 56.8%（60 分位）→ 剥离中国 28.5%（23 分位）→ 剥离中印 20.1%（6 分位）。
    但"可贸易库存偏紧"<b>不等于"价格必涨"</b>——见第二章的分组检验。</div>
  </div>

  <h2>五、类比年（剥离中国口径）与 2026 现状</h2>
  <div class="panel">
    <div id="c8" class="chart"></div>
    <div class="src">以 onset 为 T=0 的棉价路径：天气形态口径最像 1997-98（T12 −15.8%，宏观背锅）。
    剥离中国口径的基本面类比年最像 <b>MY1970</b>（同为"前 3 年去库末端"），但结局不明朗 → 类比相似度无预测力（同糖）。</div>
  </div>
  <div class="panel">
    <p>2026 现状（剥离中国视角）：</p>
    <ul>
      <li>棉价 1→8 月 <b>+25.2%</b>（95.7 美分/磅），ONI JJA +1.80、爬坡 +2.19（77 年最快）；</li>
      <li>可贸易库消比（剥离中国）<b>28.5%（23 分位偏紧）</b>，2026 事件事发榨季 MY2025 为 32.2%；</li>
      <li>但"低库存 = 利多"不成立（剥离后低库存组 T+12 中位仅 +2.6%），<b>不能据此做多</b>；</li>
      <li>真正可交易的信号仍是<b>中国国储政策</b>：中国库存 7.5 百万吨是双向阀门，棉价上行时中国抛储是最大边际利空。</li>
    </ul>
  </div>
  <div class="callout">
    <b>v2 相对 v1 的三点修正：</b>① 库存周期叙事：全球"2014 峰值 92.1%→去库"是国储收储/抛储的假象，剥离后 2014 仅 32.8%、长期窄幅；
    ② 核心结论反转：<b>"低库存=真利多"被推翻</b>（剥离中国后低库存组中位 +2.6%、胜率 56%，且 1972 极端值跳槽是主因）；
    ③ 方法沉淀：<b>凡用"库存状态"做天气弹性的调节变量，必须同时跑"全球 vs 剥离封闭库存"两口径</b>——单一口径可能给出方向性相反的结论。
  </div>

  <div class="footer">
    <b>数据与代码</b>：<code>scripts/cotton_fundamentals.py</code>（全球供需）、<code>cotton_tradeable.py</code>（可贸易库存）、
    <code>cotton_enso_cross_exCN.py</code>（剥离中国交叉，本次新增）、<code>build_cotton_report.py</code>（本页 v2）。
    结果 <code>results/cotton_*.json</code>、<code>data/cotton/*.csv</code>。<br>
    <b>口径</b>：棉花 PSD 单位 1000 480-lb Bales；库消比 = 期末库存 ÷ 国内消费（消费口径，不含出口）；市场年度 Aug–Jul；
    剥离中国 = (全球库存 − 中国国储) ÷ 全球消费。价格 = Pink Sheet "Cotton, A Index"（$/kg × 45.359 = 美分/磅）。<br>
    <b>免责</b>：年度样本 n≈65、事件 n=19、分组后每档 n≤10，重叠窗口与共线性使精确数值偏乐观，方向可信、点估计不可外推；不构成投资建议。
  </div>
</div>

__SCRIPT__
</body>
</html>
"""

SCRIPT = """
<script>
const DD = __DD__;
const RED='#b2182b', GRN='#1a7a3a', BLU='#0072B2', ORG='#E69F00', VERM='#D55E00', TEAL='#009E73';
const AX={axisLine:{lineStyle:{color:'#c8d3e0'}},axisLabel:{color:'#5a6a7d',fontSize:11},splitLine:{lineStyle:{color:'#eef2f7'}}};

// 图1 全球 vs 剥离中国
(function(){
  const ch=echarts.init(document.getElementById('c1'));
  ch.setOption({
    grid:{left:56,right:30,top:38,bottom:40},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d1.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:10,interval:5}},
    yAxis:{type:'value',name:'库消比 %',...AX},
    series:[
      {name:'全球口径',type:'line',data:DD.d1.map(x=>x[1]),symbol:'none',lineStyle:{color:'#8a97a6',width:1.5}},
      {name:'剥离中国',type:'line',data:DD.d1.map(x=>x[2]),symbol:'none',lineStyle:{color:VERM,width:2.5}}]
  });
})();

// 图3 期限扫描
(function(){
  const ch=echarts.init(document.getElementById('c3'));
  ch.setOption({
    grid:{left:56,right:30,top:38,bottom:40},
    tooltip:{trigger:'axis'},
    xAxis:{type:'category',name:'H 月',data:DD.d3.map(x=>x[0]),...AX},
    yAxis:{type:'value',name:'corr(ONI, fwd H)',...AX},
    series:[{name:'相关系数',type:'line',data:DD.d3.map(x=>x[1]),symbol:'circle',
      lineStyle:{color:BLU,width:2},itemStyle:{color:BLU},
      markPoint:{data:[{coord:['12',0.174],value:'H=12 峰 0.174',itemStyle:{color:RED}}]}}]
  });
})();

// 图4 事件 T12
(function(){
  const ch=echarts.init(document.getElementById('c4'));
  ch.setOption({
    grid:{left:56,right:30,top:38,bottom:50},
    tooltip:{formatter:p=>`${p.value[0]}<br>T+12 ${p.value[1]}%<br>峰值ONI ${p.value[2]}`},
    xAxis:{type:'category',data:DD.d4.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:9,rotate:45}},
    yAxis:{type:'value',name:'T+12 %',...AX},
    series:[{type:'bar',data:DD.d4.map(x=>({value:x[1],itemStyle:{color:x[2]>=2?'#b2182b':x[2]>=1.5?'#D55E00':x[2]>=1.0?'#E69F00':'#8a97a6'}})),barWidth:'60%'}]
  });
})();

// 图5 库存分组两口径对照
(function(){
  const ch=echarts.init(document.getElementById('c5'));
  ch.setOption({
    grid:{left:56,right:56,top:38,bottom:40},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d5.map(x=>x[0]),...AX},
    yAxis:[{type:'value',name:'T+12 中位 %',...AX},
           {type:'value',name:'胜率 %',...AX,splitLine:{show:false},min:0,max:100}],
    series:[
      {name:'T+12 中位',type:'bar',data:DD.d5.map(x=>x[1]),barWidth:'40%',
        itemStyle:{color:o=>o.dataIndex===0?RED:o.dataIndex===1?'#b8c2ce':o.dataIndex===2?'#D55E00':'#8a97a6'},
        label:{show:true,position:'top',formatter:p=>p.value+'%',color:'#1a2330'}},
      {name:'胜率',type:'line',yAxisIndex:1,data:DD.d5.map(x=>x[2]),symbol:'circle',
        lineStyle:{color:BLU,width:2},itemStyle:{color:BLU},
        label:{show:true,position:'bottom',formatter:p=>p.value+'%',fontSize:10,color:'#12365e'}}]
  });
})();

// 图6 R² 对比
(function(){
  const ch=echarts.init(document.getElementById('c6'));
  ch.setOption({
    grid:{left:52,right:24,top:38,bottom:90},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d6.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:10,rotate:30}},
    yAxis:{type:'value',name:'R²',...AX},
    series:[
      {name:'全样本 1960-2026',type:'bar',data:DD.d6.map(x=>x[1]),itemStyle:{color:VERM},barWidth:'38%'},
      {name:'近期 2000-2026',type:'bar',data:DD.d6.map(x=>x[2]),itemStyle:{color:ORG},barWidth:'38%'}]
  });
})();

// 图7 中国库存占比
(function(){
  const ch=echarts.init(document.getElementById('c7'));
  ch.setOption({
    grid:{left:56,right:56,top:38,bottom:40},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.yrs7,...AX,axisLabel:{color:'#5a6a7d',fontSize:10.5}},
    yAxis:[{type:'value',name:'百万吨',...AX},
           {type:'value',name:'中国占全球 %',...AX,splitLine:{show:false},max:100}],
    series:[
      {name:'中国库存',type:'bar',data:DD.d7_cn,itemStyle:{color:RED},barWidth:'50%'},
      {name:'全球库存',type:'bar',data:DD.d7_w,itemStyle:{color:'#d8c6a8'},barWidth:'50%'},
      {name:'中国占全球份额',type:'line',yAxisIndex:1,data:DD.d7_share,symbol:'circle',
        lineStyle:{color:BLU,width:2},itemStyle:{color:BLU},
        label:{show:true,position:'top',formatter:p=>p.value+'%',fontSize:10,color:'#12365e'}}]
  });
})();

// 图8 路径对比
(function(){
  const ch=echarts.init(document.getElementById('c8'));
  ch.setOption({
    grid:{left:56,right:30,top:38,bottom:40},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',name:'onset 后月数',data:DD.d8_m,...AX},
    yAxis:{type:'value',name:'$/kg',...AX},
    series:[
      {name:'1997-05 onset',type:'line',data:DD.d8_97,symbol:'none',lineStyle:{color:'#8a97a6',width:2,type:'dashed'}},
      {name:'2026-05 onset',type:'line',data:DD.d8_26,symbol:'none',lineStyle:{color:VERM,width:2.5}}]
  });
})();
</script>
"""

HTML = HTML.replace("__SCRIPT__", SCRIPT.replace("__DD__", DD))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print("wrote", OUT, len(HTML), "bytes")
