# -*- coding: utf-8 -*-
"""构建 90 号报告：白糖库消比 / 产量 / 需求 + 厄尔尼诺类比年 —— 2026-09-12"""
import json
import os
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "reports", "90_白糖库消比与厄尔尼诺类比_20260912")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "index.html")

g = pd.read_csv(os.path.join(BASE, "data", "sugar", "sugar_global_sd.csv"))
g = g.rename(columns={g.columns[0]: "MY"}).set_index("MY")
ev = pd.read_csv(os.path.join(BASE, "results", "sugar_enso_events.csv"))
cx = pd.read_csv(os.path.join(BASE, "results", "sugar_enso_cross.csv"))
fund = json.load(open(os.path.join(BASE, "results", "sugar_fundamentals.json"), encoding="utf-8"))
analog = pd.read_csv(os.path.join(BASE, "results", "sugar_analog_fundamental.csv"))

# ---------- 价格（Pink Sheet） ----------
wb = load_workbook(os.path.join(BASE, "data", "sugar", "raw", "pink_sheet_2026.xlsx"),
                   read_only=True, data_only=True)
rows = list(wb["Monthly Prices"].iter_rows(values_only=True))
hdr = {str(x).strip(): i for i, x in enumerate(rows[4]) if x}
i_s = hdr["Sugar, world"]
pr = []
for r in rows[6:]:
    if r[0] and re.match(r"^\d{4}M\d{2}$", str(r[0])):
        v = pd.to_numeric(r[i_s], errors="coerce")
        if pd.notna(v):
            pr.append((str(r[0]), float(v)))
P = dict(pr)
KM = sorted(P)

# ---------- 1. 库消比序列 ----------
sur = g["StockToUse"].dropna()
d1 = [[f"{int(y)}", round(float(sur[y]), 1)] for y in sur.index]
d1 = d1[-70:]

# ---------- 2. 产量 / 消费 / 过剩 ----------
rec = g.loc[2005:]
d2 = [[f"{int(y)}", round(float(rec.loc[y, "Production"] / 1000), 1),
       round(float(rec.loc[y, "Total Disappearance"] / 1000), 1),
       round(float(rec.loc[y, "ProdMinusUse"] / 1000), 1)] for y in rec.index]

# ---------- 3. 事件 T+12 ----------
e = cx.dropna(subset=["T12"]).copy()
d3 = [[r.onset, round(float(r.T12), 1), round(float(r.peak), 2)] for r in e.itertuples()]

# ---------- 4. 分档 ----------
def band(p):
    return "超强\n≥2.0" if p >= 2.0 else "强\n1.5-2.0" if p >= 1.5 else "中等\n1.0-1.5" if p >= 1.0 else "弱\n0.5-1.0"


e2 = cx.copy()
e2["band"] = e2.peak.apply(lambda p: band(p).replace("\n", " "))
bb = e2.dropna(subset=["T12"]).groupby("band").T12.agg(["size", "mean", "median"])
order = [b.replace("\n", " ") for b in ["超强\n≥2.0", "强\n1.5-2.0", "中等\n1.0-1.5", "弱\n0.5-1.0"]]
d4 = [[b, int(bb.loc[b, "size"]), round(float(bb.loc[b, "mean"]), 1),
       round(float(bb.loc[b, "median"]), 1)] for b in order if b in bb.index]

# ---------- 5. 库存分组 ----------
med = float(cx.stock_to_use.median())
lo = cx[(cx.stock_to_use < med)].dropna(subset=["T12"]).T12
hi = cx[(cx.stock_to_use >= med)].dropna(subset=["T12"]).T12
d5 = [["低库消比\n(<%.1f%%)" % med, round(float(lo.mean()), 1), round(float(lo.median()), 1),
       int(len(lo)), round(float((lo > 0).mean() * 100), 0)],
      ["高库消比\n(≥%.1f%%)" % med, round(float(hi.mean()), 1), round(float(hi.median()), 1),
       int(len(hi)), round(float((hi > 0).mean() * 100), 0)]]


# ---------- 6. 路径对比：1997 vs 2026（以 onset 为 T=0） ----------
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
d6_months = [x[0] for x in p97]
d6_97 = [x[1] for x in p97]
d6_26 = [x[1] for x in p26]

# ---------- 7. 分国别产量 ----------
ctry = fund["countries"]
CN_MAP = {"Brazil": "巴西", "India": "印度", "Thailand": "泰国", "China": "中国",
          "European Union": "欧盟", "Australia": "澳大利亚", "Pakistan": "巴基斯坦",
          "Mexico": "墨西哥", "Russia": "俄罗斯", "Guatemala": "危地马拉", "South Africa": "南非",
          "United States": "美国"}
yrs = [str(y) for y in range(2019, 2027)]
d7 = []
for c, zh in CN_MAP.items():
    p = ctry.get(c, {}).get("Production", {})
    if not p:
        continue
    row = [zh] + [p.get(y) for y in yrs]
    if row[6] is not None:
        d7.append(row)
d7.sort(key=lambda r: (r[6] if r[6] is not None else 0), reverse=True)
d7 = d7[:8]

# ---------- 8. 消费增速分年代 CAGR ----------
cons = g["Total Disappearance"].dropna()


def _cagr(a, b):
    s = cons.loc[a:b].dropna()
    return ((s.iloc[-1] / s.iloc[0]) ** (1 / (len(s) - 1)) - 1) * 100


PERIODS = [("1960s", 1960, 1969), ("1970s", 1970, 1979), ("1980s", 1980, 1989),
           ("1990s", 1990, 1999), ("2000s", 2000, 2009), ("2010s", 2010, 2019),
           ("近10年", 2016, 2026), ("近5年", 2021, 2026)]
d8 = [[lab, round(float(_cagr(a, b)), 2)] for lab, a, b in PERIODS]

# ---------- 9. 库存周期相位：以 onset 榨季为 T=0 的库消比路径 ----------
def _my_of(onset):
    y, m = int(onset[:4]), int(onset[5:7])
    return y if m >= 10 else y - 1          # 项目铁律：onset 在 1-9 月 -> 上一 MY


SUR_S = g["StockToUse"]
PHASE = [("1996/97", "1997-05"), ("2022/23", "2023-06"),
         ("1975/76", "1976-09"), ("2026/27", "2026-05")]
d9 = []
for lab, on in PHASE:
    my = _my_of(on)
    d9.append([lab] + [None if t not in SUR_S.index or pd.isna(SUR_S[t])
                       else round(float(SUR_S[t]), 1) for t in range(my - 4, my + 2)])
d9_x = ["T-4", "T-3", "T-2", "T-1", "T=0", "T+1"]

# ---------- 10. 基本面雷达（7 维，归一化到 1960-2026 历史区间位置） ----------
FEATS = ["sur", "d_sur", "balance_pct", "prod_yoy", "cons_yoy", "cum_d_sur_3y", "stocks_yoy"]
d10_axis = ["库消比", "库消比同比变动", "产需差率", "产量同比", "消费同比", "前3年库消比累计变动", "库存同比"]
gg = g.rename(columns={"StockToUse": "sur"}).copy()
gg["d_sur"] = gg["sur"].diff()
gg["balance_pct"] = (gg["Production"] - gg["Total Disappearance"]) / gg["Total Disappearance"] * 100
gg["prod_yoy"] = gg["Production"].pct_change() * 100
gg["cons_yoy"] = gg["Total Disappearance"].pct_change() * 100
gg["stocks_yoy"] = gg["Ending Stocks"].pct_change() * 100
gg["cum_d_sur_3y"] = gg["d_sur"].rolling(3).sum()
GG = gg[gg.index >= 1960]
d10 = []
for lab, my in [("2026 当前", 2025), ("1975/76", 1975), ("2022/23", 2022), ("1996/97", 1996)]:
    d10.append({"name": lab, "value": [
        round(float((GG.loc[my, f] - GG[f].min()) / (GG[f].max() - GG[f].min()) * 100), 1)
        for f in FEATS]})
CUM3 = {lab: round(float(GG.loc[_my_of(on), "cum_d_sur_3y"]), 1)
        for lab, on in [("1996/97", "1997-05"), ("2022/23", "2023-06"),
                        ("1975/76", "1976-09"), ("2026/27", "2026-05")]}

# ---------- 11. 天气相似度 vs 事后收益（证明相似度无预测力） ----------
NBJ = json.load(open(os.path.join(BASE, "results", "sugar_enso_cross.json"), encoding="utf-8"))["neighbors"]
d11 = []
for n in NBJ:
    t = float(n["T12"])
    if t == 0.0:                             # 1965-06 / 1991-06：绝对收益缺失，剔除
        continue
    d11.append([n["onset"], round(float(n["score"]), 2), round(t, 1)])
d11.sort(key=lambda r: r[1])

DD_JSON = json.dumps(
    {"d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5,
     "d6": {"m": d6_months, "a": d6_97, "b": d6_26}, "d7": d7, "d8": d8,
     "d9": d9, "d9x": d9_x, "d10": d10, "d10a": d10_axis, "d11": d11},
    ensure_ascii=False)
print("CUM3", CUM3, "d11", d11)
print("d8", d8)

# ---------- 关键数字 ----------
cur = int(g.index.max())
sur_now = float(g.loc[cur, "StockToUse"])
sur_pct = float((sur < sur_now).mean() * 100)
prod_now = float(g.loc[cur, "Production"] / 1000)
prod_prev = float(g.loc[cur - 1, "Production"] / 1000)
cons_now = float(g.loc[cur, "Total Disappearance"] / 1000)
stock_now = float(g.loc[cur, "Ending Stocks"] / 1000)
bal_now = float(g.loc[cur, "ProdMinusUse"] / 1000)


def rowshow(v, unit=1, nd=1):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v/unit:,.{nd}f}"


cty_rows = ""
for r in d7:
    tds = "".join(f'<td class="num">{rowshow(v, 1, 0)}</td>' for v in r[1:])
    cty_rows += f"<tr><td>{r[0]}</td>{tds}</tr>"

analog_rows = ""
for r in analog.head(6).itertuples():
    t12 = r.T12
    t12s = "—" if pd.isna(t12) else f"{t12:+.1f}%"
    cls = "" if pd.isna(t12) else ("red" if t12 > 0 else "green")
    t24s = "—" if pd.isna(r.T24) else f"{r.T24:+.1f}%"
    hit = " ★" if r.season in ("1975/76", "2022/23") else ""
    analog_rows += (f"<tr><td><b>{r.season}</b>{hit}</td><td>{r.onset}</td>"
                    f"<td class='num'>{r.sur:.1f}</td><td class='num'>{r.cum_d_sur_3y:+.1f}</td>"
                    f"<td class='num'>{r.balance_pct:+.1f}</td><td class='num'>{r.prod_yoy:+.1f}</td>"
                    f"<td class='num'>{r.cons_yoy:+.1f}</td><td class='num'><b>{r.dist:.2f}</b></td>"
                    f"<td class='num {cls}'>{t12s}</td><td class='num'>{t24s}</td></tr>")

ev_rows = ""
for r in cx.itertuples():
    t12 = getattr(r, "T12")
    cls = "" if pd.isna(t12) else ("red" if t12 > 0 else "green")
    t12s = "—" if pd.isna(t12) else f"{t12:+.1f}%"
    su = getattr(r, "stock_to_use")
    sus = "—" if pd.isna(su) else f"{su:.1f}"
    ev_rows += (f"<tr><td>{r.onset}</td><td>{r.peak_ym}</td><td class='num'>{r.peak:+.2f}</td>"
                f"<td class='num'>{sus}</td><td class='num'>{r.pre6_run_up if not pd.isna(r.pre6_run_up) else '—'}</td>"
                f"<td class='num {cls}'>{t12s}</td></tr>")

nb = json.load(open(os.path.join(BASE, "results", "sugar_enso_cross.json"), encoding="utf-8"))["neighbors"]
nb_rows = "".join(
    f"<tr><td>{n['onset']}</td><td class='num'>{n['peak']:+.2f}</td><td class='num'>{n['ramp']}</td>"
    f"<td class='num'>{n['stock_to_use']}</td><td class='num {'red' if n['T12']>0 else 'green'}'>{n['T12']:+.1f}%</td>"
    f"<td class='num'>{n['score']:.2f}</td></tr>" for n in nb[:6])

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>90 · 白糖库消比、库存周期与厄尔尼诺类比年（v2）· 2026-09-12</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --oi-green:#009E73;
        --ink:#1a2330; --sub:#5a6a7d; --line:#dde4ec; --card:#fff; --bg:#f5f7fa; --ref-bg:#eef2f7;}}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.75;font-size:15px;}}
  .wrap{{max-width:1180px;margin:0 auto;padding:24px 20px 60px;}}
  .hero{{background:linear-gradient(135deg,#12365e 0%,#1d5c93 100%);color:#fff;border-radius:12px;padding:28px 32px;margin-bottom:20px;}}
  .hero h1{{font-size:23px;margin-bottom:6px;line-height:1.45;}}
  .hero .meta{{font-size:12.5px;opacity:.85;margin-top:4px;}}
  .hero .sub{{margin-top:12px;font-size:14px;opacity:.96;border-top:1px solid rgba(255,255,255,.25);padding-top:10px;}}
  .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}}
  .kcard{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}}
  .kcard .lab{{font-size:12px;color:var(--sub);margin-bottom:3px;}}
  .kcard .val{{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;}}
  .kcard .note{{font-size:12px;color:var(--sub);margin-top:3px;}}
  .red{{color:#b2182b;}} .green{{color:#1a7a3a;}}
  h2{{font-size:19px;margin:34px 0 12px;padding-left:12px;border-left:4px solid var(--oi-blue);}}
  h3{{font-size:16px;color:#12365e;margin:18px 0 8px;}}
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
  .chart{{width:100%;height:340px;}}
  .footer{{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}}
  .term{{border-bottom:1px dashed #8aa0b8;cursor:help;position:relative;}}
  .term:hover::after{{content:attr(data-t);position:absolute;left:0;top:130%;z-index:99;
    background:#12365e;color:#fff;font-size:12px;line-height:1.5;padding:8px 11px;border-radius:7px;
    width:290px;white-space:normal;box-shadow:0 6px 20px rgba(0,0,0,.22);font-weight:400;}}
  code{{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px;}}
  ul{{padding-left:22px;}} li{{margin:4px 0;}}
  .tag{{display:inline-block;font-size:11px;padding:1px 7px;border-radius:20px;background:#eef2f7;color:#3b5670;margin-right:6px;}}
  @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr);}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>白糖：库消比、产量、需求，以及本轮厄尔尼诺该参考哪一年</h1>
    <div class="meta">报告编号 90 ｜ v2 重排版 ｜ 数据源：USDA FAS PSD（2026-09-11 快照）＋ World Bank Pink Sheet 世界糖价（1960M01–2026M08）＋ NOAA CPC ONI/RONI（1950–2026-08）＋ ISO 2026-08 季度展望 ｜ 2026-09-12</div>
    <div class="sub"><b>
    全球库消比（USDA PSD 口径）<b>{sur_now:.1f}%</b>，且刚走完 <b>4 年去库</b>（2021/22–2024/25 累计 −7.4 Mt）。口径上请注意：<b>ISO 新口径给的是 44.15%</b>，
    两者分母几乎相同、<b>差异全在库存定义</b>（PSD 44.4 Mt vs ISO 79.4 Mt），<b>不可跨机构比较绝对水平</b>。<br>
    本报告把"<b>该参考哪一年</b>"拆成<b>两种口径</b>分别回答——因为<b>换一组匹配维度，就会换出一个答案</b>：
    <b>天气形态口径 → 1997-98</b>（起始同为 5 月、爬坡速度史上第 2、当时库消比 24.7% 与今天几乎相同）；
    <b>基本面口径 → 2022/23 与 1975/76 并列</b>，而 1997-98 退到第 4。
    <b>这个落差本身就是线索：1997-98 站在"累库周期末端"，而当前站在"去库周期末端"。</b><br>
    贯穿全篇的警示：<b>糖价对厄尔尼诺并没有稳定的正向响应</b>（ONI 每 +1.0 → 未来 12 个月糖价 <span class="green">−2.2%</span>，t=−0.49，不显著），
    且<b>恰恰是低库存年份的事件后表现更差</b>（T+12 均值 <span class="green">−15.3%</span> vs 高库存 <span class="red">+18.0%</span>）。
    </b></div>
  </div>

  <div class="cards">
    <div class="kcard"><div class="lab">全球库消比（2026/27，PSD 口径）</div><div class="val">{sur_now:.1f}%</div>
      <div class="note">1960 年以来 {sur_pct:.0f} 分位 ｜ <b>不可与 ISO 的 44.15% 直接比较</b></div></div>
    <div class="kcard"><div class="lab">全球产量（2026/27 预测）</div><div class="val">{prod_now:,.1f} Mt</div>
      <div class="note">同比 <span class="green">{(prod_now-prod_prev)/prod_prev*100:+.1f}%</span>（{prod_prev:,.1f} → {prod_now:,.1f}）</div></div>
    <div class="kcard"><div class="lab">全球消费（2026/27 预测）</div><div class="val">{cons_now:,.1f} Mt</div>
      <div class="note">同比 {cons_now/float(g.loc[cur-1,'Total Disappearance']/1000)*100-100:+.2f}% ｜ 几乎零增长</div></div>
    <div class="kcard"><div class="lab">产需差（2026/27）</div><div class="val red">+{bal_now:,.0f} 万吨</div>
      <div class="note">USDA 口径过剩 ｜ ISO 同口径为缺口 20 万吨</div></div>
  </div>

  <div class="warn">
    <b>⚠️ 先看口径：这张表里的"过剩还是短缺"，两家机构结论方向相反。</b><br>
    <b>USDA PSD</b>：2026/27 产量 {prod_now:,.1f} Mt、消费 {cons_now:,.1f} Mt → <b>过剩 {bal_now:,.0f} 万吨</b>。<br>
    <b>ISO（2026-08 展望）</b>：2026/27 产量 180.1 Mt、消费 180.4 Mt → <b>缺口 20 万吨</b>；且把 2025/26 过剩从 5 月的 220 万吨<u>连续第四次下调</u>至 110 万吨。<br>
    两者消费口径几乎一致（{cons_now:.1f} vs 179.6 Mt），<b>分歧全在产量口径（差约 5 Mt / 2.7%）</b>——
    USDA 的 186.1 Mt 比 ISO 的 180.7 Mt 高。所以"全球是过剩还是短缺"在本题上<u>不是一个事实判断，而是口径选择</u>。
    本报告所有自身计算统一采用 <b>USDA PSD 一条口径</b>，ISO/Czarnikow/StoneX 仅作外部参照，不混算。
  </div>

  <h2>一、白糖基本面：库消比、产量、需求</h2>

  <h3>1.1 库消比：口径不同，同一个"全球库消比"能从 24.6% 排到 52.7%</h3>
  <div class="warn">
    <b>⚠️ 先锁口径：下面这个 {sur_now:.1f}% 用的是 USDA PSD 定义，它不能与 ISO 报告里的 44.15% 直接比较——两者分母几乎相同，差异 100% 在"库存"这个分子。</b>
    全球消费：USDA 179.8 Mt vs ISO 179.7 Mt（差 0.1 Mt）；
    全球期末库存：<b>USDA 44.4 Mt vs ISO 新口径 79.4 Mt（差 35 Mt）</b>。对照表见本节末。
  </div>
  <div class="panel">
    <div id="c1" class="chart"></div>
    <div class="src">口径：期末库存 ÷ 总消费（Total Disappearance），USDA PSD，榨季 Oct–Sep，Market_Year Y = Y/Y+1 榨季。
    世界总量由 194 个国别加总，欧盟按 EU-15(1960–2003) → EU-25(2004–2005) → European Union(2006–) 三段拼接以避免重复或漏计。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>指标</th><th class="num">2024/25</th><th class="num">2025/26</th><th class="num">2026/27 预测</th><th>判断</th></tr>
      <tr><td>期末库存（Mt）</td><td class="num">{float(g.loc[2024,'Ending Stocks']/1000):,.1f}</td><td class="num">{float(g.loc[2025,'Ending Stocks']/1000):,.1f}</td><td class="num">{stock_now:,.1f}</td><td>连续两年回升</td></tr>
      <tr><td>库消比</td><td class="num">{float(g.loc[2024,'StockToUse']):.1f}%</td><td class="num">{float(g.loc[2025,'StockToUse']):.1f}%</td><td class="num">{sur_now:.1f}%</td><td>仍在近 10 年均值 {fund['stock_to_use_stats']['avg_10y']}% 之下</td></tr>
      <tr><td>历史分位（1960 起）</td><td class="num">—</td><td class="num">—</td><td class="num">{sur_pct:.0f}%</td><td>偏低但不极端</td></tr>
      <tr><td>历史分位（近 15 年窗口）</td><td class="num">—</td><td class="num">—</td><td class="num">≈31%</td><td><b>近 15 年维度明显偏紧</b></td></tr>
    </table>
    <div class="src">⚠️ <b>窗口选择会改变结论（同一口径内）</b>：把窗口从 1960 年收到近 15 年，当前库消比分位由 {sur_pct:.0f}% 降到约 31%（2011–2026 区间只高于 2011/2024/2025/2016 四年）。
    ISO 在<b>它自己的新口径序列</b>里把 2024/25 的 44.06% 称作"16 年历史低点"，44.15% 仅高出 0.09pp——绝对水平虽不可比，但"<b>近十几年库存持续偏低、且本榨季得不到有效回补</b>"这个方向判断，两套口径一致。
    历史区间 {fund['stock_to_use_stats']['min']}%（{fund['stock_to_use_stats']['min_year']} 年，糖价史诗级牛市起点）～ {fund['stock_to_use_stats']['max']}%（{fund['stock_to_use_stats']['max_year']} 年）。</div>
  </div>

  <div class="panel">
    <h3>⚠️ 同一个 2025/26 榨季，"全球库消比"六家能差出一倍</h3>
    <table>
      <tr><th>来源</th><th>库存口径</th><th class="num">全球期末库存</th><th class="num">库消比</th></tr>
      <tr><td><b>USDA PSD（本报告口径）</b></td><td>194 国中 151 个有数据国家的期末结转库存加总</td><td class="num">44.4 Mt</td><td class="num"><b>{sur_now:.1f}%</b></td></tr>
      <tr><td><b>ISO 2026-05 新口径</b>（Updated End Stocks）</td><td>首度扣除"原糖→精炼糖"的加工与溶解损耗</td><td class="num">79.4 Mt</td><td class="num"><b>44.15%</b></td></tr>
      <tr><td>ISO 旧口径（同期）</td><td>未扣损耗</td><td class="num">95.0 Mt</td><td class="num">52.74%</td></tr>
      <tr><td>GlobalData（日本 ALIC 2026-06 引用）</td><td>平衡表口径</td><td class="num">—</td><td class="num">46.2%</td></tr>
      <tr><td>《甘蔗糖业》2026(4) 引 ISO/泛糖</td><td>—</td><td class="num">—</td><td class="num">51.8%</td></tr>
      <tr><td>StoneX 等（未修偏基准）</td><td>—</td><td class="num">—</td><td class="num">39.6%–42.4%</td></tr>
    </table>
    <div class="src"><b>差异全部来自分子（库存）的定义与覆盖面</b>，分母（全球消费 ≈180 Mt）各家一致。
    为什么 PSD 显著更低：①43 个国家完全无库存数据；②库存高度集中，前 12 国占 75%（泰国 1,345 万吨、印度 651 万吨、中国 402 万吨）；③许多进口国/消费国的渠道库存与政府储备未纳入，属系统性低估。
    （自检：PSD 的 Total Distribution 已含 Ending Stocks —— 151 国中 101 国出现 Supply−Distribution−Stocks≠0，正是这个包含关系所致。）<br>
    <b>用法建议</b>：判断"全球实物缓冲"用 ISO 口径（覆盖完整）；判断"可贸易缓冲与价格弹性"用国别结构 + PSD（巴西 22 万吨这类信号，ISO 的加总数看不出来）。<b>无论哪个口径，都不要跨机构比较绝对水平</b>。</div>
  </div>
  <div class="callout">
    <b>怎么读这个库消比：</b>本轮的问题不在于"库存绝对低"，而在于<b>库存结构极不均衡</b>——
    巴西期末库存仅 <b>22 万吨</b>（库消比 2.5%，几乎零缓冲），而中国恢复到 402 万吨（24.0%）、泰国 1,345 万吨（出口国的结转）。
    全球缓冲主要压在<b>不参与国际贸易的中国库存</b>上，一旦南半球出现供给扰动，可贸易缓冲比 24.6% 这个数字看上去要紧得多。
  </div>

  <h3>1.2 产量与需求</h3>
  <div class="panel">
    <div id="c8" class="chart" style="height:300px"></div>
    <div class="src">全球食糖消费的<b>分年代年均复合增速（CAGR）</b>，USDA PSD 口径。趋势极清晰：1960–70 年代 3.4–3.5% → 1980–2000 年代 1.7–2.0% → 2010 年代 1.09% → <b>近 10 年 0.61%、近 5 年 0.57%</b>。</div>
  </div>
  <div class="callout">
    <b>消费增速的关键信号：已经低于人口增速。</b>
    近 10 年全球消费 CAGR <b>+0.61%</b>，而同期人口 CAGR 约 <b>+1.00%</b> → <b>人均消费以每年约 −0.4% 的速度下降</b>（22.9 kg/人 → 22.7 → 21.9）。
    这是"消费见顶"的典型形态，也是糖价长期中枢缺乏需求侧支撑的根本原因。驱动因素：发达国家糖税与健康消费、代糖替代（F55 果葡糖浆长期低于白糖价格、赤藓糖醇/甜菊糖渗透）、<b>GLP-1 减重药物普及</b>、以及中国人口自然增长率转负（2025 年 −2.41‰）。
    推论：<b>糖价的边际驱动几乎全部来自供给侧</b>——为什么天气叙事对糖价的影响力显得这么大，答案在分母这里。
  </div>
  <div class="panel">
    <div id="c2" class="chart"></div>
    <div class="src">单位：百万吨。柱=产量，线=消费，虚线柱=产需差（右轴）。2026/27 为 USDA 2026-05 版预测（FAS 半年报仅 5 月/11 月更新，故非最新月度值）。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>国别/地区（千吨）</th>{"".join(f'<th class="num">{y}</th>' for y in yrs)}</tr>
      {cty_rows}
    </table>
    <div class="src">USDA PSD 分国别产量。2026 = 2026/27 榨季预测。<b>注意中国行与国内口径不同</b>：PSD 2025/26 给 1,260 万吨，中国糖业协会/农业农村部口径为 <b>1,295 万吨</b>（差 35 万吨，属发布时点差异而非口径差异——2024/25 两口径均为 1,116 万吨，完全吻合）。</div>
  </div>
  <div class="callout">
    <b>产量端的三个看点：</b>
    ①<b>泰国已进入减产</b>——PSD 从 1,126 万吨下调至 <b>950 万吨</b>（−176 万吨），泰国糖业协会更悲观，称可能跌破 1,000 万吨；
    ②<b>印度是最大不确定性</b>——PSD 仍假设增产 +360 万吨至 3,360 万吨，但印度糖业协会已把 2025/26 净产糖从 3,100 万吨下调至 <b>2,790–2,930 万吨</b>，这个假设有下修风险；
    ③<b>欧盟因高温干旱下调</b>——欧委会 8 月把 EU-27 产量估至 1,340 万吨，同比 −19%，比 6 月再降 70 万吨。<br>
    <b>需求端</b>：全球消费 2025/26 +0.5%（ISO 口径 +90 万吨至 1.796 亿吨），2026/27 预计再 +80 万吨——<b>增速低于产量波动一个数量级</b>，
    意味着糖价的驱动几乎全部来自供给侧，这也解释了为什么天气叙事对糖价的影响力会这么大。
  </div>

  <h3>1.3 库存周期位置：刚走完四年去库，2025/26 才刚翻头</h3>
  <div class="panel">
    <div id="c9" class="chart" style="height:300px"></div>
    <div class="src">横轴为"以各事件 onset 所在榨季为 T=0"的偏移年；纵轴为全球库消比（USDA PSD 口径，%）。
    四条线分别是天气口径选出的 1996/97、基本面口径选出的 2022/23 与 1975/76，以及本轮 2026/27。</div>
  </div>
  <div class="warn">
    <b>这张图是理解后文"为什么两种口径会选出不同的年份"的关键。</b>
    1996/97 那一次，事发前两年库消比从 19.1% 一路冲到 <b>26.1%</b>——它是一场<b>累库周期末端</b>的天气事件；
    而本轮是<b>去库周期末端</b>：2021/22 起连续四年去库，期末库存从 49.4 Mt 降到 42.1 Mt（<b>−14.9%</b>），库消比 28.9% → 24.0%，2025/26 才转微弱累库。
    用"过去三年库消比累计变动"量化：<b>1996/97 = {CUM3['1996/97']:+.1f} pct</b>（累库），<b>2026/27 = {CUM3['2026/27']:+.1f} pct</b>（去库）——<b>符号相反</b>。
  </div>
  <div class="panel">
    <table>
      <tr><th>榨季</th><th class="num">期末库存 Mt</th><th class="num">同比变动 Mt</th><th class="num">库消比</th><th>阶段</th></tr>
      <tr><td>2020/21</td><td class="num">{float(g.loc[2020,'Ending Stocks']/1000):.1f}</td><td class="num red">+2.4</td><td class="num">{float(g.loc[2020,'StockToUse']):.1f}%</td><td>最后一个累库年</td></tr>
      <tr><td>2021/22</td><td class="num">{float(g.loc[2021,'Ending Stocks']/1000):.1f}</td><td class="num green">−2.5</td><td class="num">{float(g.loc[2021,'StockToUse']):.1f}%</td><td>去库 · 第 1 年</td></tr>
      <tr><td>2022/23</td><td class="num">{float(g.loc[2022,'Ending Stocks']/1000):.1f}</td><td class="num green">−1.6</td><td class="num">{float(g.loc[2022,'StockToUse']):.1f}%</td><td>去库 · 第 2 年</td></tr>
      <tr><td>2023/24</td><td class="num">{float(g.loc[2023,'Ending Stocks']/1000):.1f}</td><td class="num green">−0.7</td><td class="num">{float(g.loc[2023,'StockToUse']):.1f}%</td><td>去库 · 第 3 年</td></tr>
      <tr><td>2024/25</td><td class="num">{float(g.loc[2024,'Ending Stocks']/1000):.1f}</td><td class="num green">−2.6</td><td class="num">{float(g.loc[2024,'StockToUse']):.1f}%</td><td><b>去库谷底</b></td></tr>
      <tr><td>2025/26</td><td class="num">{float(g.loc[2025,'Ending Stocks']/1000):.1f}</td><td class="num red">+1.3</td><td class="num">{float(g.loc[2025,'StockToUse']):.1f}%</td><td>转微弱累库</td></tr>
      <tr><td>2026/27 预测</td><td class="num">{stock_now:.1f}</td><td class="num red">+0.9</td><td class="num">{sur_now:.1f}%</td><td>微弱累库延续</td></tr>
    </table>
    <div class="src">USDA PSD 口径。<b>四年累计去库 −7.4 Mt（−14.9%）。</b>当前 44.2 Mt 在近 16 年（2011–2026）窗口中约处 44 分位、库消比约 25 分位。
    ⚠️ 这轮"累库"的成色很差：2024/25 → 2026/27 全球净增 2.16 Mt，其中<b>中国 +2.38、泰国 +2.15（合计 +4.53）</b>，被印尼 −1.32、美国 −0.74、巴西 −0.35 等对冲——<b>是缓冲在两国堆积、其余产地被抽干，而不是全面过剩</b>。</div>
  </div>
  <div class="callout">
    <b>⚠️ 全球与国内方向相反，这是本榨季最核心的错位。</b>
    全球只是"微弱累库"，而<b>国内是剧烈累库</b>：2025/26 全国产糖 <b>1,295 万吨</b>（同比 +16%，12 年新高），
    工业库存 6 月底 449 万吨（<b>同比 +98.7%，近乎翻倍</b>）→ 7 月底 372 万吨（+130.8%）→ 8 月底约 210 万吨（去年同期仅 116 万吨）；
    累计销糖率 71.3%，同比放缓 14.3 个百分点；广西第三方仓库库存 208 万吨，处近五年同期高位。
    这是典型的"<b>增产 + 销不动</b>"被动累库。<br>
    ⚠️ 口径提醒：PSD 的 China Ending Stocks（MY2026 = 402 万吨）含国储与商业库存，<b>不等于</b>国内糖业协会的"工业库存"（8 月底 210 万吨），两者不可混用。
  </div>

  <h2>二、先说清楚：糖价对厄尔尼诺并没有稳定的正向响应</h2>

  <h3>2.1 当前 ENSO 状态：强度中等偏强、爬坡史无前例</h3>
  <div class="panel">
    <table>
      <tr><th>口径</th><th>最新值</th><th>对应档位</th><th>说明</th></tr>
      <tr><td>ONI（legacy，3 月滑动）</td><td class="num">JJA 2026 <b>+1.80</b></td><td>强档（1.5–2.0）</td><td>本报告事件分档统一用 ONI，因它覆盖 1950 年至今</td></tr>
      <tr><td>RONI（2026-02 起官方口径）</td><td class="num">JJA 2026 <b>+1.36</b></td><td>中等档（1.0–1.5）</td><td>RONI 系统性低于 ONI 约 0.42–0.59℃，换口径会掉一档</td></tr>
      <tr><td>Niño3.4 月度（最快）</td><td class="num">2026-08 <b>+1.67</b></td><td>—</td><td>比季滑动指数早约 1 个月</td></tr>
      <tr><td>1 月→7 月爬坡</td><td class="num"><b>+2.19</b></td><td>1950 年以来第 1</td><td>第二名是 1997 年的 +1.89</td></tr>
      <tr><td>CPC 官方概率（2026-08-13）</td><td class="num">&gt;90% / 69%</td><td>very strong</td><td>秋冬季达 very strong；OND2026 RONI ≥ +2.5 的概率 69%</td></tr>
    </table>
    <div class="src">⚠️ 三套口径给出"强档 / 中等档 / very strong"三个不同答案，这本身就是信息：<b>已确认强度不低，但尚未到超强</b>。
    经验规律：1950 年以来 9 次峰值 ≥+1.5 的事件，峰值<u>全部</u>落在 11 月–次年 1 月。故本轮峰值窗口预计 <b>2026-11 ～ 2027-01</b>。</div>
  </div>

  <h3>2.2 22 次历史事件：糖价对厄尔尼诺没有稳定的正向响应</h3>
  <div class="panel">
    <div id="c3" class="chart"></div>
    <div class="src">柱=每次事件从 onset+1 月（无前视）起算的 T+12 糖价对数收益（%）。红涨绿跌。数据：World Bank Pink Sheet "Sugar, world" 月均现货（1960M01–2026M08），单位换算后约等于美分/磅 × 45.36。</div>
  </div>
  <div class="warn">
    <b>这是本报告与"厄尔尼诺=糖价上涨"直觉最大的冲突点。</b>
    期限扫描显示 <code>corr(ONI_t, 未来 12 个月糖价收益) = −0.039</code>，H=0、3、6、9、12 个月全部接近 0；
    回归 <code>fwd12 = a + b·ONI</code> 得 <b>b = −2.18%/℃（t = −0.49，n=788）</b>，加入商品指数控制后 b = −7.49%（t = −1.66）——<b>仍然不显著</b>。
    对比同项目 89 号报告：橡胶的同口径系数是<b> +12.3%/℃（t = 4.30）</b>。同一个指数、同一套方法、同一个价格源，<b>糖的反应约等于零甚至偏负</b>。
  </div>
  <div class="panel">
    <h3>为什么糖不像橡胶那样响应？</h3>
    <ul>
      <li><b>地理对冲</b>：厄尔尼诺让印度、泰国、澳大利亚、南非干旱（利多），但让<b>巴西中南部</b>（占全球出口约一半）降雨增多（多数年份利多种植）。最大产区与受损产区的效应部分抵消。</li>
      <li><b>糖醇切换阀门</b>：巴西的甘蔗可以在糖与乙醇之间切换。糖价一涨、制糖比一升，供给立刻回来——<b>供给弹性被乙醇通道大幅提高</b>，这是橡胶（树龄刚性、7 年投产周期）完全没有的机制。</li>
      <li><b>抢跑</b>：ENSO 提前 3–6 个月可预报。检验显示 <code>corr(onset 前 6 月涨幅, 后 12 月收益) = −0.34</code>（p=0.155，n=19）——<b>预报期涨得越多，兑现后越差</b>。</li>
      <li><b>宏观主导</b>：三次超强事件（1982/1997/2015）全部撞上宏观危机（拉美债务、亚洲金融危机、商品崩塌），T+12 为 +47.0% / −32.9% / −11.8%，离散度极大。</li>
    </ul>
  </div>

  <h3>2.3 强度分档与库存交叉：低库存年份反而更差</h3>
  <div class="panel">
    <div id="c4" class="chart"></div>
    <div class="src">左：按峰值强度分档的 T+12 均值/中位（n=22 次事件，其中 18 次有完整价格）。右：按事件发生时全球库消比高低分组。</div>
  </div>
  <div class="panel">
    <table>
      <tr><th>分组</th><th class="num">样本数</th><th class="num">T+12 均值</th><th class="num">T+12 中位</th><th class="num">胜率</th></tr>
      {"".join(f"<tr><td>{r[0].replace(chr(10),' ')}</td><td class='num'>{r[3]}</td><td class='num {'red' if r[1]>0 else 'green'}'>{r[1]:+.1f}%</td><td class='num {'red' if r[2]>0 else 'green'}'>{r[2]:+.1f}%</td><td class='num'>{r[4]}%</td></tr>" for r in d5)}
    </table>
    <div class="src">库消比分组以 26.1% 为中位切分。⚠️ 每组样本仅 9–10 个，且重叠窗口使显著性偏乐观，<b>方向可参考、精确数值不可外推</b>。</div>
  </div>
  <div class="callout">
    <b>反直觉但可解释</b>：低库消比组的 T+12 均值 <span class="green">−15.3%</span>、胜率仅 <b>11%</b>；高库消比组 <span class="red">+18.0%</span>、胜率 <b>70%</b>。
    机制是<b>定价充分性</b>：库存紧时，"天气要来了"这件事已经被市场提前交易进价格（该组 onset 前 6 个月平均已涨 <b>+10.4%</b>），事件兑现即利多出尽；
    库存宽松时市场不设防，真实减产反而构成超预期。
    <b>当前库消比 24.6% 落在"低库存"组</b>（< 26.1%）。值得注意：换成 ISO 口径（44.15%、16 年低点附近）得到的也是"库存偏紧"这一定性结论——<b>两个口径在方向一致，只是绝对数值不可比</b>。按历史规律，低库存组正属于事件后表现偏差的那一类。
  </div>

  <h2>三、类比年：换一组匹配维度，就换一个答案</h2>
  <div class="callout">
    <b>这是 v2 重排版最大的变化。</b>原版只给了一个答案（1997-98），而那个答案来自一组
    <b>只含天气形态与库存水位、不含任何宏观/贸易流/供给方向变量</b>的维度。换个问法，就会出现另一个答案。
    下面把<b>两种口径并列呈现</b>，并把它们的<b>分歧点精确定位</b>出来——这个分歧点本身才是最有用的信息。
  </div>

  <h3>3.1 口径一 · 天气形态最近邻 → 1997-98</h3>
  <div class="warn">
    <b>先锁死这个"像"的口径：只含 4 个维度，一个宏观变量都没有。</b><br>
    <code>score = |爬坡速度 − 2.19| + |起始月 − 5|/3 + |峰值ONI − 2.4|/0.8 + |库消比 − 24.6%|/5</code><br>
    即<b>爬坡速度、起始月份、峰值强度、事发榨季库消比</b>四项。它回答的是"<b>天气冲击的节奏像不像</b>"，
    <b>不回答"接下来涨还是跌"</b>。原版标题里的"类比年"容易被读成后者，v2 改称<b>"天气形态最近邻"</b>。
  </div>
  <div class="panel">
    <table>
      <tr><th>候选年份</th><th class="num">峰值 ONI</th><th class="num">1→7 月爬坡</th><th class="num">事发榨季库消比</th><th class="num">T+12 糖价</th><th class="num">相似度（越小越像）</th></tr>
      {nb_rows}
    </table>
    <div class="src">目标参数取 2026 当前状态（爬坡 +2.19、起始 5 月、预期峰值 ≈+2.4、库消比 24.6%）。</div>
  </div>
  <div class="ok">
    <b>在天气口径下，答案是 1997-98，而且是断层第一。</b>四项参数里三项几乎重合——
    起始月同为 <b>5 月</b>；爬坡速度 1.89 vs 2.19（史上第 2 vs 第 1）；事发榨季库消比 <b>24.7% vs 24.6%</b>；
    峰值同为 12 月、同为超强档（+2.37）。相似度得分 0.36，第二名 2023-06 为 1.71，<b>差距近 5 倍</b>。
  </div>
  <div class="panel">
    <div id="c6" class="chart"></div>
    <div class="src">两条路径以各自 onset 月为 T=0（1997-05 / 2026-05），纵轴为世界糖价（$/kg）。2026 只到 T+3（2026-08）。</div>
  </div>

  <h3>3.2 但天气口径的相似度，对未来收益没有预测力</h3>
  <div class="warn">
    <b>1997-98 的结局是跌的：T+12 −32.9%、T+24 −65.4%。</b>
    原因是那一年糖价被<b>亚洲金融危机</b>的需求崩塌压过——厄尔尼诺造成的减产是真的，但需求端塌得更快。<br>
    更关键的是：<b>同一批"天气很接近"的邻居，结局完全无序</b>——最像的 1997-05 是 <span class="green">−32.9%</span>，
    第 3 像的 1972-06 却是 <span class="red">+56.0%</span>，第 6 像的 1963-07 是 <span class="green">−44.2%</span>，
    <b>首尾相差 89 个百分点</b>。
  </div>
  <div class="panel">
    <div id="c11" class="chart" style="height:320px"></div>
    <div class="src">纵轴按"天气形态相似度"从高到低排列（越靠上越像），横轴为事件后 12 个月糖价收益（绝对）。
    若相似度有预测力，条形应从下往上有序变化——<b>实际是无序的</b>。</div>
  </div>
  <div class="warn">
    <b>一个更硬的反证：1972-06 那个 +56.0%，扣掉商品指数后只剩 −5.4%。</b>
    也就是说那次"暴涨"几乎全是大宗商品整体牛市（World Bank Non-energy 指数 1972-06 → 1973-06 涨约 61%），
    <b>糖本身并没有跑赢</b>。<br>
    结论：<b>同一类天气参数、同样接近的库存状态，结局由宏观与贸易流决定，不来自天气本身。</b>
  </div>

  <h3>3.3 口径二 · 基本面最近邻 → 2022/23 与 1975/76</h3>
  <div class="panel">
    <div class="warn" style="margin-top:0">
      <b>换一组维度：去掉天气强度，只用糖自身基本面（7 个维度，同样不含任何天气变量）——</b><br>
      库消比水位 ｜ 库消比同比变动 ｜ 产需差率（是否紧缺）｜ 产量同比 ｜ 消费同比 ｜
      <b>前 3 年库消比累计变动（库存周期相位）</b> ｜ 库存同比。<br>
      距离 = 各维度按 1960–2026 全样本标准差尺度化后的欧氏距离，越小越像。候选集仍是同一批 ENSO 事件年。
      （糖没有权威公开的"产能"序列——压榨产能不披露——供给侧以<b>产量同比</b>做代理。）
    </div>
    <table>
      <tr><th>榨季</th><th>onset</th><th class="num">库消比</th><th class="num">前3年累计变动</th><th class="num">产需差率</th><th class="num">产量同比</th><th class="num">消费同比</th><th class="num">基本面距离</th><th class="num">T+12</th><th class="num">T+24</th></tr>
      {analog_rows}
    </table>
    <div class="src">★ = 两种目标口径（MY2025 实际值 / MY2026 预测值）下平均排名并列第一。
    目标状态：库消比 24.1%、前 3 年累计变动 −1.6、产需差率 +3.5%、产量同比 +3.2%、消费同比 +2.6%。
    T+12 / T+24 为事件后 12 / 24 个月糖价绝对收益。</div>
  </div>
  <div class="panel">
    <div id="c10" class="chart" style="height:390px"></div>
    <div class="src">七个基本面维度各自归一化到 1960–2026 历史区间的相对位置（0% = 历史最低，100% = 历史最高）。
    <b>注意 1996/97 那条红色虚线在"前 3 年库消比累计变动"一轴上的尖峰</b>——这是它与当前唯一严重失配的维度。</div>
  </div>

  <h3>3.4 分歧点定位：1997-98 只输在一个维度上</h3>
  <div class="ok">
    <b>七个维度里，1997-98 有六个与当前相当接近</b>——库消比 24.7% vs 24.1%、产需差率 +3.1% vs +3.5%、
    消费同比 +2.8% vs +2.6%、库消比同比变动 −1.4 vs +0.1、产量同比 +0.5% vs +3.2%、库存同比 −2.8% vs +3.0%。<br>
    <b>唯一严重失配的是「前 3 年库消比累计变动」：1997-98 = {CUM3['1996/97']:+.1f} pct，2026 = {CUM3['2026/27']:+.1f} pct。</b>
    1993/94 到 1995/96 连续两年大幅累库（库消比 19.1% → 26.1%），所以 1997 那次是<b>累库周期末端</b>的天气事件；
    而当前是<b>去库四年之后的低位</b>。<b>库存周期相位正好相反——这不只是宏观背景不同，是糖自身的周期位置不同。</b>
  </div>
  <div class="callout">
    <b>顺带一个反证：用基本面选出来的年份，天气强度参差不齐。</b>
    1975/76 是弱事件（峰值 0.84）、1990/91 中等（1.54）、2003/04 最弱（0.71），只有 2022/23 是强事件（1.99）。
    <b>这恰好说明：天气强度不该拿来选类比年——候选年份的强度分布几乎与"像不像"无关。</b>
  </div>

  <h3>3.5 结论：该拿哪一年、怎么用</h3>
  <div class="panel">
    <table>
      <tr><th>用途</th><th>用哪一年</th><th>它给的信息</th></tr>
      <tr><td><b>看天气冲击的节奏</b></td><td><b>1997-98</b></td><td>5 月起步、12 月见峰、超强档——是<b>路径模板</b>，不是结局模板</td></tr>
      <tr><td><b>看基本面状态的历史对应</b></td><td><b>2022/23</b>（并列第一，且本身是强事件）</td><td>T+12 −19.0%、T+24 −34.0%：<b>去库后期 + 低库消比 + 强厄尔尼诺 + 价格已抢跑 → 天气兑现即利多出尽</b></td></tr>
      <tr><td>交叉验证</td><td>1975/76（并列第一，弱事件）</td><td>T+12 −11.8%、T+24 <span class="red">+10.5%</span>——<b>同样接近的基本面，结局可以相反</b></td></tr>
    </table>
  </div>
  <div class="warn">
    <b>最重要的提醒：即使换成基本面口径，匹配度依然不预测结局。</b>
    两个并列第一的 T+24 <b>一正一负</b>（1975/76 <span class="red">+10.5%</span> vs 2022/23 <span class="green">−34.0%</span>）；
    前 5 名的 T+12 为 −11.8 / −19.0 / n/a / −32.9 / +30.2，中位约 <b>−19%</b>——
    <b>短期偏空的倾向是有的，但样本太小（有效值仅 4 个），不构成统计证据。</b><br>
    真正可用的读法：<b>把 2022/23 当"状态模板"</b>——同为"去库后期 + 低库消比 + 强厄尔尼诺 + 价格抢跑"。
    但要盯住一条差异：2022/23 之后两年全球产量继续增长、压过了天气影响；而当前机构一致预期 2026/27 是<b>减产</b>。
    <b>这一条不成立，路径就会分叉。</b>
  </div>

  <h3>3.6 2026 与 1997 的关键差异（逐项）</h3>
  <div class="panel">
    <table>
      <tr><th>维度</th><th>1997-98</th><th>2026-27</th><th>对价格的含义</th></tr>
      <tr><td>起始月 / 爬坡速度</td><td>1997-05 / +1.89</td><td>2026-05 / +2.19</td><td>几乎一致，天气冲击节奏可类比</td></tr>
      <tr><td>事发榨季库消比</td><td>24.7%</td><td>24.6%</td><td>缓冲水位相同</td></tr>
      <tr><td>巴西库存</td><td>86 万吨（MY1996/97）</td><td>22 万吨（MY2026/27 预测，库消比 2.5%）</td><td>今天巴西缓冲更薄，供给扰动放大倍数更高</td></tr>
      <tr><td>价格起点（各自 onset 月）</td><td>10.9 美分/磅（1997-05）</td><td>15.4 美分/磅（2026-05）；至 8 月已达 17.2</td><td><b>起点高出 42%</b>，抢跑已发生，与"低库存组"特征吻合</td></tr>
      <tr><td>宏观背景</td><td>亚洲金融危机（需求崩塌）</td><td>中东地缘冲突推升油价（利多乙醇平价）</td><td>方向相反：1997 宏观利空，2026 宏观偏利多糖</td></tr>
      <tr><td>贸易流</td><td>巴西大幅增产</td><td>巴西减产、泰国减产、印度进口（2016 年来首次放行 100 万吨）</td><td>2026 供给端更紧，但已被部分定价</td></tr>
      <tr><td>机构共识</td><td>由过剩转向短缺</td><td>已从过剩叙事全面转向短缺（ISO 连续四次下调）</td><td>叙事已完成切换，增量信息变少</td></tr>
    </table>
  </div>

  <h2>四、口径说明（本次数据的审计结果）</h2>
  <div class="panel">
    <table>
      <tr><th>环节</th><th>采用口径</th><th>已知风险 / 处理</th></tr>
      <tr><td>全球供需总量</td><td>USDA FAS PSD，分国别加总</td><td>欧盟按 EU-15(1960–2003)/EU-25(2004–05)/EU(2006–) 三段拼接，成员国不重复计；历史实体（苏联 1960–88、南斯拉夫 1960–91、捷克斯洛伐克 1960–88、东德 1960–73）单独加回，与后继国不重叠。<b>校验：1990/2000/2010/2020/2026 与公认量级偏差均 ≤0.5%</b></td></tr>
      <tr><td>库消比</td><td>期末库存 ÷ 总消费</td><td><b>终稿口径</b>。PSD 每个（国别,年,属性）只有 1 条最新修订值（实测 max=1），<b>无法重建"当年公布值"</b>，故历史百分位与当年市场认知存在系统性差异（历史值普遍被上修 → 当前相对显得更松）</td></tr>
      <tr><td>榨季归属</td><td>Oct–Sep，MY = 起始年</td><td>事件与榨季的匹配按"onset 在 10–12 月 → 当年榨季，1–9 月 → 上一榨季"；另给"受影响榨季"列做交叉验证</td></tr>
      <tr><td>糖价序列</td><td>World Bank Pink Sheet "Sugar, world"（ISA 日均价月均）</td><td>现货月均，非期货；与 ICE 期货点位<u>不可逐点对齐</u>。2026M08 = 0.380 $/kg = 17.2 美分/磅，与 ISO 公布的 8 月 ISA 月均 17.4 美分一致</td></tr>
      <tr><td>ENSO 指数</td><td>ONI（事件分档）</td><td>ONI 为 legacy，2026-02 起官方改用 RONI。历史事件无 RONI 长序列，故分档统一用 ONI，并单独提示当前 RONI 值（低约 0.44℃）</td></tr>
      <tr><td>外部分歧</td><td>ISO / Czarnikow / StoneX 仅作参照</td><td>USDA 产量口径比 ISO 高约 5 Mt（2.7%），导致 2026/27"过剩 504 万吨"与"缺口 20 万吨"方向相反，<b>报告内不混算</b></td></tr>
      <tr><td><b>类比年匹配（天气口径）</b></td><td>4 维加权标准化距离：爬坡速度 / 起始月 / 峰值强度 / 库消比</td><td>⚠️ <b>不含任何宏观、贸易流、供给方向变量</b>，只刻画"天气冲击的形态"。<b>已实证：该相似度对事件后 12 个月收益无预测力</b>（最像的 1997-05 为 −32.9%，第 3 像的 1972-06 为 +56.0%）。<b>只能当路径模板，不能当结局模板。</b></td></tr>
      <tr><td><b>类比年匹配（基本面口径）</b></td><td>7 维尺度化欧氏距离：库消比水位 / 库消比同比变动 / 产需差率 / 产量同比 / 消费同比 / <b>前 3 年库消比累计变动</b> / 库存同比</td><td>同样不含天气强度变量。等权、按 1960–2026 全样本 sd 尺度化。<b>稳健性</b>：分别以 MY2025 实际值、MY2026 预测值为目标各跑一次，取平均排名。⚠️ 匹配度同样不预测结局（并列第一的两者 T+24 一正一负）。</td></tr>
      <tr><td>"产能"代理说明</td><td>产量同比</td><td>糖的压榨产能无权威公开序列（各国糖厂产能利用率不披露），故供给侧以<b>产量同比</b>代理。这是本报告在"产能"维度上的已知妥协。</td></tr>
      <tr><td>国内产销库存</td><td>中国糖业协会 + 广西/云南糖业协会月度数据（转引）</td><td>与 PSD 的 China Ending Stocks <b>口径不同</b>（后者含国储与商业库存），<b>不可混用或相加</b>。国内数据经新华财经、广发期货周报、卓创资讯交叉核对。</td></tr>
    </table>
  </div>

  <div class="footer">
    <b>数据与代码</b>：<code>scripts/sugar_fundamentals.py</code>（供需与库消比，含欧盟拼接）、
    <code>scripts/sugar_enso_analyze.py</code>（事件研究与期限扫描）、
    <code>scripts/sugar_enso_cross.py</code>（强度 × 库存交叉 + 天气形态相似度）、
    <code>scripts/sugar_analog_fundamental.py</code>（<b>基本面口径类比年，v2 新增</b>）、
    <code>scripts/build_sugar_report.py</code>（本页）。<br>
    数据落盘 <code>data/sugar/</code>，结果 <code>results/sugar_*.json|csv</code>。<br>
    <b>v2 重排版改动</b>：① 新增 1.3 节（库存周期位置：四年去库与「全球与国内方向相反」）；② 原「2.4 类比年筛选」的措辞由<b>「类比年」正名为「天气形态最近邻」</b>，并显式声明其维度不含宏观；
    ③ 新增第三章，把<b>基本面口径</b>与天气口径并列，并定位二者的分歧点（库存周期相位）；④ 新增三张图（库存相位 / 基本面雷达 / 相似度与收益无序性）；⑤ 口径说明补入两套匹配方法的定义与已知风险。<br>
    <b>免责</b>：本文所有结论基于公开数据与统计推断，样本量小、重叠窗口使显著性偏乐观，不构成投资建议。投资有风险，决策需谨慎。
  </div>
</div>

__SCRIPT__
</body>
</html>
"""

SCRIPT = """
<script>
const DD = __DD__;
const RED='#b2182b', GRN='#1a7a3a', BLU='#0072B2', ORG='#E69F00', VERM='#D55E00', TEAL='#009E73', GRY='#8a97a6';
const AX={axisLine:{lineStyle:{color:'#c8d3e0'}},axisLabel:{color:'#5a6a7d',fontSize:11},splitLine:{lineStyle:{color:'#eef2f7'}}};

// 图1 库消比 1960-2026
(function(){
  const ch=echarts.init(document.getElementById('c1'));
  const yrs=DD.d1.map(x=>x[0]), vals=DD.d1.map(x=>x[1]);
  ch.setOption({
    grid:{left:56,right:24,top:34,bottom:44},
    tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
    xAxis:{type:'category',data:yrs,...AX,axisLabel:{color:'#5a6a7d',fontSize:10,interval:9}},
    yAxis:{type:'value',name:'库消比 %',nameTextStyle:{color:'#5a6a7d',fontSize:11},...AX,min:15,max:36},
    series:[{name:'全球糖库消比',type:'line',data:vals,symbol:'none',
      lineStyle:{width:1.8,color:BLU},areaStyle:{color:'rgba(0,114,178,.10)'},
      markLine:{silent:true,symbol:'none',label:{fontSize:10,color:'#5a6a7d'},
        data:[{yAxis:25.7,lineStyle:{color:GRY,type:'dashed'},label:{formatter:'中位 25.7%'}},
              {yAxis:24.6,lineStyle:{color:RED,type:'dotted'},label:{formatter:'当前 24.6%',color:RED}}]},
      markPoint:{symbolSize:44,data:[
        {coord:['2009',17.9],value:'17.9',itemStyle:{color:ORG},label:{color:'#fff',fontSize:10}},
        {coord:[yrs[yrs.length-1],24.6],value:'24.6',itemStyle:{color:RED},label:{color:'#fff',fontSize:10}}]}}]
  });
})();

// 图8 消费增速分年代
(function(){
  const ch=echarts.init(document.getElementById('c8'));
  ch.setOption({
    grid:{left:56,right:24,top:30,bottom:44},
    tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
    xAxis:{type:'category',data:DD.d8.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:11}},
    yAxis:{type:'value',name:'CAGR %',...AX},
    series:[{type:'bar',barWidth:'52%',
      data:DD.d8.map(x=>({value:x[1],
        itemStyle:{color:x[1]>=1.5?BLU:(x[1]>=1.0?ORG:VERM)}})),
      label:{show:true,position:'top',fontSize:10.5,color:'#5a6a7d',formatter:p=>p.value+'%'}}]
  });
})();

// 图2 产量 / 消费 / 产需差
(function(){
  const ch=echarts.init(document.getElementById('c2'));
  ch.setOption({
    grid:{left:58,right:64,top:38,bottom:40},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d2.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:10}},
    yAxis:[{type:'value',name:'Mt',...AX,min:140,max:200},
           {type:'value',name:'产需差 Mt',...AX,splitLine:{show:false}}],
    series:[
      {name:'产量',type:'bar',data:DD.d2.map(x=>x[1]),itemStyle:{color:BLU},barWidth:'42%'},
      {name:'消费',type:'bar',data:DD.d2.map(x=>x[2]),itemStyle:{color:ORG},barWidth:'42%'},
      {name:'产需差(右)',type:'line',yAxisIndex:1,data:DD.d2.map(x=>x[3]),symbolSize:5,
        lineStyle:{color:TEAL,width:2},itemStyle:{color:TEAL}}]
  });
})();

// 图3 各事件 T+12
(function(){
  const ch=echarts.init(document.getElementById('c3'));
  ch.setOption({
    grid:{left:52,right:22,top:34,bottom:66},
    tooltip:{trigger:'axis',formatter:p=>{const i=p[0].dataIndex;
      return DD.d3[i][0]+'<br/>峰值ONI '+DD.d3[i][2]+'<br/>T+12 '+DD.d3[i][1]+'%';}},
    xAxis:{type:'category',data:DD.d3.map(x=>x[0]),...AX,axisLabel:{color:'#5a6a7d',fontSize:9.5,rotate:55}},
    yAxis:{type:'value',name:'T+12 %',...AX},
    series:[{type:'bar',barWidth:'62%',
      data:DD.d3.map(x=>({value:x[1],itemStyle:{color:x[1]>0?RED:GRN}}))}]
  });
})();

// 图4 强度分档 + 库存分组
(function(){
  const ch=echarts.init(document.getElementById('c4'));
  const bd=DD.d4.map(x=>x[0]);
  ch.setOption({
    grid:{left:52,right:22,top:40,bottom:56},
    tooltip:{trigger:'axis'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:bd.concat(DD.d5.map(x=>x[0])),...AX,
      axisLabel:{color:'#5a6a7d',fontSize:10.5,lineHeight:13,interval:0}},
    yAxis:{type:'value',name:'T+12 %',...AX},
    series:[
      {name:'T+12 均值',type:'bar',barGap:'0%',
        data:DD.d4.map(x=>x[2]).concat(DD.d5.map(x=>x[1])),
        itemStyle:{color:p=>p.dataIndex<DD.d4.length?BLU:ORG}},
      {name:'T+12 中位',type:'bar',
        data:DD.d4.map(x=>x[3]).concat(DD.d5.map(x=>x[2])),
        itemStyle:{color:'#b8c6d6'}}]
  });
})();

// 图6 1997 vs 2026 路径
(function(){
  const ch=echarts.init(document.getElementById('c6'));
  ch.setOption({
    grid:{left:58,right:24,top:38,bottom:44},
    tooltip:{trigger:'axis',formatter:p=>{let s='T'+p[0].axisValue+' 月<br/>';
      p.forEach(q=>s+=q.seriesName+': '+q.data+' $/kg<br/>');return s;}},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d6.m.map(String),...AX,name:'T+月',nameTextStyle:{fontSize:10}},
    yAxis:{type:'value',name:'$/kg',...AX,scale:true},
    series:[
      {name:'1997-98',type:'line',data:DD.d6.a,symbolSize:4,
        lineStyle:{color:VERM,width:2.2},itemStyle:{color:VERM}},
      {name:'2026-27',type:'line',data:DD.d6.b,symbolSize:4,
        lineStyle:{color:BLU,width:2.2,type:'dashed'},itemStyle:{color:BLU}}]
  });
})();

// 图9 库存周期相位（以 onset 榨季为 T=0 的库消比路径）
(function(){
  const ch=echarts.init(document.getElementById('c9'));
  const COL={'1996/97':VERM,'2022/23':TEAL,'1975/76':ORG,'2026/27':BLU};
  ch.setOption({
    grid:{left:56,right:52,top:44,bottom:40},
    tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
    legend:{top:4,textStyle:{fontSize:11,color:'#5a6a7d'}},
    xAxis:{type:'category',data:DD.d9x,...AX,name:'相对 onset 榨季',nameTextStyle:{fontSize:10}},
    yAxis:{type:'value',name:'库消比 %',...AX,scale:true},
    series:DD.d9.map(r=>({name:r[0],type:'line',data:r.slice(1),symbolSize:5,
      lineStyle:{color:COL[r[0]],width:r[0]==='2026/27'?3:2,type:r[0]==='1996/97'?'dashed':'solid'},
      itemStyle:{color:COL[r[0]]}}))
  });
})();

// 图10 基本面雷达
(function(){
  const ch=echarts.init(document.getElementById('c10'));
  const COL={'2026 当前':'#1a2330','1975/76':ORG,'2022/23':TEAL,'1996/97':VERM};
  ch.setOption({
    tooltip:{},
    legend:{bottom:0,textStyle:{fontSize:11,color:'#5a6a7d'}},
    radar:{indicator:DD.d10a.map(t=>({name:t,max:100})),radius:'60%',center:['50%','47%'],
      axisName:{color:'#5a6a7d',fontSize:11},
      splitLine:{lineStyle:{color:'#e6ecf3'}},splitArea:{areaStyle:{color:['#fff','#fafcfe']}},
      axisLine:{lineStyle:{color:'#dde4ec'}}},
    series:[{type:'radar',symbolSize:4,data:DD.d10.map(d=>({name:d.name,value:d.value,
      lineStyle:{color:COL[d.name],width:d.name==='2026 当前'?3:1.8,type:d.name==='1996/97'?'dashed':'solid'},
      itemStyle:{color:COL[d.name]},areaStyle:{opacity:0.06}}))}]
  });
})();

// 图11 天气相似度 vs 事后收益
(function(){
  const ch=echarts.init(document.getElementById('c11'));
  const d=DD.d11.slice().reverse();
  const COL={'1996/97':VERM,'2022/23':TEAL,'1975/76':ORG,'2026/27':BLU};
  ch.setOption({
    grid:{left:84,right:58,top:16,bottom:36},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
      formatter:p=>{const i=p[0].dataIndex;return d[i][0]+'<br/>天气相似度得分 '+d[i][1]+'（越小越像）<br/>T+12 '+d[i][2]+'%';}},
    xAxis:{type:'value',name:'T+12 %',...AX,min:-60,max:75},
    yAxis:{type:'category',data:d.map(r=>r[0]+'  ('+r[1]+')'),...AX,
      axisLabel:{color:'#5a6a7d',fontSize:10.5}},
    series:[{type:'bar',barWidth:'58%',
      data:d.map(r=>({value:r[2],itemStyle:{color:r[2]>0?RED:GRN},
        label:{position:r[2]>0?'right':'left'}})),
      label:{show:true,fontSize:10.5,color:'#5a6a7d',
        formatter:p=>(p.value>0?'+':'')+p.value+'%'}}]
  });
})();
</script>
"""

HTML = HTML.replace("__SCRIPT__", SCRIPT.replace("__DD__", DD_JSON))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print("wrote", OUT, len(HTML), "bytes")
print("sur", sur_now, "pct", sur_pct, "prod", prod_now, "cons", cons_now, "bal", bal_now)
print("d4", d4)
print("d5", d5)
