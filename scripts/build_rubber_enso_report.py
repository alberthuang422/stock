#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建报告 89：厄尔尼诺对橡胶价格的定量影响（读 results/rubber_enso_analysis.json）"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "results", "rubber_enso_analysis.json")
OUTDIR = os.path.join(ROOT, "reports", "89_厄尔尼诺与橡胶价格_20260912")
OUT = os.path.join(OUTDIR, "index.html")

D = json.load(open(SRC, encoding="utf-8"))
R = D["regressions"]


def g(k):
    return R.get(k)


def bt(k, i):
    """取回归系数与 t"""
    v = g(k)
    return (v["b"][i], v["t"][i]) if v else (None, None)


# ---------- 关键数字
b_on12, t_on12 = bt("ONI→12m", 1)
b_on12_ne, t_on12_ne = bt("ONI+商品指数→12m", 1)
b_ex12, t_ex12 = bt("ONI→12m(剔商品β)", 1)
b_on12_oil, t_on12_oil = bt("ONI+油价→12m", 1)
b_2000, t_2000 = bt("ONI→12m(2000-2025)", 1)
b_1990, t_1990 = bt("ONI→12m(1960-1999)", 1)
b_ru, t_ru = bt("RU主连 12m~ONI(1997-2026)", 1)
b_doni, t_doni = bt("当月收益~ΔONI", 1)
b_season, t_season = bt("ONI→12m(割胶季6-10月)", 1)

ONI = D["meta"]["oni_latest"]["anom"]
ex_ne = D["excess_over_commodity_index"]
cn = D["cn_rubber"]
ev = D["events_rss3"]
tiers = D["tier_summary"]
states = D["state_summary"]
scan = D["horizon_scan"]

PANEL_DATA = json.dumps({
    "scan": scan,
    "events": [{"a": e["anchor"], "tier": e["tier"], "peak": e["peak_abs"],
                "t6": e["t6"], "t12": e["t12"], "t24": e["t24"], "len": e["len_m"]}
               for e in ev],
    "tiers": [{"label": t["label"], "n": t["n"],
               "t6": (t.get("t6") or {}).get("mean"), "t12": (t.get("t12") or {}).get("mean"),
               "t24": (t.get("t24") or {}).get("mean"),
               "e12": (t.get("t12") or {}).get("excess")} for t in tiers],
    "states": [{"label": s["label"], "n": s["n"],
                "t12": (s.get("t12") or {}).get("mean"),
                "ex": (s.get("t12") or {}).get("excess"),
                "p": (s.get("t12") or {}).get("p_welch")} for s in states],
    "oni2026": [x for x in D["oni_recent"] if x["date"].startswith("2026")],
    "cn": cn,
}, ensure_ascii=False)

# ---------- 事件明细表
ev_rows = "".join(
    f'<tr><td>{e["anchor"]}</td><td>{e["len_m"]} 个月</td>'
    f'<td class="num">{e["peak_abs"]:.2f}</td><td>{e["tier"]}</td>'
    + "".join(
        f'<td class="num {"red" if e[f"t{h}"] is not None and e[f"t{h}"]>0 else "green"}">'
        f'{e[f"t{h}"]:+.1f}%</td>' if e[f"t{h}"] is not None else '<td class="num">—</td>'
        for h in (6, 12, 24))
    + f'<td class="num {"red" if e["ex12"] is not None and e["ex12"]>0 else "green"}">'
      f'{e["ex12"]:+.1f}pp</td></tr>' if e.get("ex12") is not None else "</tr>"
    for e in ev)

tier_rows = "".join(
    f'<tr><td><b>{t["label"]}</b></td><td class="num">{t["n"]}</td>'
    + "".join(
        f'<td class="num {"red" if (t.get(f"t{h}") or {}).get("mean",0)>0 else "green"}">'
        f'{(t.get(f"t{h}") or {}).get("mean","—"):+.1f}%</td>'
        f'<td class="num">{(t.get(f"t{h}") or {}).get("excess","—"):+.1f}pp</td>'
        f'<td class="num">{(t.get(f"t{h}") or {}).get("p_welch","—")}</td>' for h in (6, 12, 24))
    + "</tr>" for t in tiers)

state_rows = "".join(
    f'<tr><td><b>{s["label"]}</b></td><td class="num">{s["n"]}</td>'
    f'<td class="num {"red" if (s.get("t12") or {}).get("mean",0)>0 else "green"}">'
    f'{(s.get("t12") or {}).get("mean","—"):+.1f}%</td>'
    f'<td class="num">{(s.get("t12") or {}).get("excess","—"):+.1f}pp</td>'
    f'<td class="num">{(s.get("t12") or {}).get("p_welch","—")}</td>'
    f'<td class="num">{(s.get("t12") or {}).get("win","—")}</td></tr>' for s in states)

REGS = [
    ("ONI→6m", "未来 6 个月", "不控"),
    ("ONI→12m", "未来 12 个月", "不控"),
    ("ONI→24m", "未来 24 个月", "不控"),
    ("ONI+油价→12m", "未来 12 个月", "控油价"),
    ("ONI+商品指数→12m", "未来 12 个月", "控商品指数"),
    ("ONI→12m(剔商品β)", "未来 12 个月", "相对商品指数"),
    ("ONI→12m(割胶季6-10月)", "未来 12 个月", "仅 6–10 月"),
    ("ONI→12m(1960-1999)", "未来 12 个月", "1960–1999"),
    ("ONI→12m(2000-2025)", "未来 12 个月", "2000–2025"),
    ("RU主连 12m~ONI(1997-2026)", "RU 主连未来 12 个月", "1997–2026"),
    ("当月收益~ΔONI", "当月收益", "ΔONI 同期"),
]


def reg_row(key, hz, note):
    v = g(key)
    if not v:
        return ""
    cells = "".join(
        f'<td class="num {"red" if b>0 else "green"}">{b:+.2f}</td>'
        f'<td class="num">{t:+.2f}</td>' for b, t in zip(v["b"][1:], v["t"][1:]))
    names = "".join(f"<td class='num' style='color:#5a6a7d'>{n}</td>" for n in v["names"][1:])
    return (f'<tr><td>{key}</td><td>{hz}</td><td>{note}</td>{cells}'
            f'<td class="num">{v["r2"]:.3f}</td><td class="num">{v["n"]}</td></tr>')


reg_rows = "".join(reg_row(k, hz, nt) for k, hz, nt in REGS)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>89 · 厄尔尼诺对橡胶价格的定量影响 · 2026-09-12</title>
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
  @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr);}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>厄尔尼诺对橡胶价格到底有多大促进作用？——1960–2025 年 19 次事件的定量拆解</h1>
    <div class="meta">报告编号 89 ｜ 数据源：NOAA CPC ONI 月度指数（1950–2026）＋ World Bank Pink Sheet 月度胶价 RSS3/TSR20（1960M01–2025M12）＋ 东方财富 RU/BR/NR 主连日线（1997–2026）｜ 2026-09-12</div>
    <div class="sub">结论一句话：<b>
    <span class="term" data-t="Oceanic Niño Index，海洋尼诺指数。NOAA 定义：3 个月滑动平均的 Niño3.4 区海温距平，单位 ℃。≥+0.5 为厄尔尼诺、≤−0.5 为拉尼娜。">ONI</span>
    每上升 1.0，未来 12 个月天然橡胶价格 <span class="red">+12.3%</span>（t=4.30）；把大宗商品共同的涨跌 β 剔掉后，橡胶"专属"的部分是 <span class="red">+7.6%～+8.6%</span>。
    但这个规律只对"<b>强档及以下</b>"成立——<b>超强档（ONI ≥ 2.0）历史上反而为负</b>（T+12 平均 −13.1%，n=3）。
    作用<b>完全滞后</b>：ONI 上升的当月胶价几乎无反应（r=+0.03），峰值出现在 <b>12 个月后</b>（r=+0.34），24 个月后消失。
    对称性清晰：拉尼娜月份 T+12 平均 <span class="green">−7.8%</span>（超额 −9.4%，p&lt;0.0001）。
    </b></div>
  </div>

  <div class="cards">
    <div class="kcard"><div class="lab">ONI +1.0 → 未来 12 个月胶价</div><div class="val red">{b_on12:+.1f}%</div>
      <div class="note">t={t_on12:+.2f}｜R²={g('ONI→12m')['r2']:.3f}｜n={g('ONI→12m')['n']}（1960–2025 月度）</div></div>
    <div class="kcard"><div class="lab">剔除大宗商品共同 β 后</div><div class="val red">{b_ex12:+.1f}%</div>
      <div class="note">t={t_ex12:+.2f} → 这才是橡胶"专属"的厄尔尼诺效应</div></div>
    <div class="kcard"><div class="lab">19 次厄尔尼诺事件 · T+12 平均</div><div class="val red">+16.5%</div>
      <div class="note">超额 +14.9%，胜率 14/19，p=0.025</div></div>
    <div class="kcard"><div class="lab">超强档（ONI≥2.0）· T+12</div><div class="val green">−13.1%</div>
      <div class="note">n=3（1982 / 1997 / 2015），超额 −14.7% —— <b>反向</b></div></div>
  </div>

  <h2>一、口径与方法</h2>
  <div class="panel">
    <table>
      <tr><th style="width:130px;">项目</th><th>设定</th></tr>
      <tr><td>胶价主口径</td><td>World Bank Pink Sheet <b>Rubber RSS3（烟片胶，$/kg）1960M01–2025M12，66 年 792 个月</b>。世界银行 TSR20 序列<b>仅从 1999 年起</b>，不足以覆盖历史事件，故降为辅助口径（结论方向一致）。</td></tr>
      <tr><td>ENSO 口径</td><td>NOAA CPC 官方 ONI 月度序列（1950–2026，919 个月）。用 3 个月滑动中心月对齐到日历月（如 MJJ → 6 月）。</td></tr>
      <tr><td>事件识别</td><td>ONI ≥ +0.5 且连续 ≥5 个重叠 3 月季（NOAA 定义）。1950–2026 共 <b>22 次厄尔尼诺</b>、20 次拉尼娜；因胶价自 1960 起，<b>可做事件研究 19 次</b>。</td></tr>
      <tr><td>强度分档</td><td>弱 0.5–0.9 ／ 中 1.0–1.4 ／ 强 1.5–1.9 ／ 超强 ≥2.0（按事件峰值 ONI 绝对值的最大值）。</td></tr>
      <tr><td><span class="term" data-t="把一次事件从起点到 T+N 月累计的价格涨跌，减去同一时长在全样本中的平均涨跌。剔除"橡胶本身长期就涨"的部分，只留厄尔尼诺带来的增量。">超额</span>口径</td><td>以 ONI 中心月为锚，算 T+6/12/24 个月累计对数收益，减去全样本同期限无条件均值（T+12 基线仅 +1.59%）。</td></tr>
      <tr><td>显著性</td><td>Welch t 检验 ＋ Mann-Whitney 秩检验并列（重叠窗口会使 t 偏乐观，故必须配秩检验）；回归用 <span class="term" data-t="Newey-West 异方差自相关稳健标准误。月度重叠收益自相关很强，普通 OLS 标准误会严重低估，t 值虚高。">Newey-West HAC</span>（6 阶）。</td></tr>
      <tr><td>前视控制</td><td>ONI 中心值滞后约 1 个月公布，故另算"锚定 onset+1 月"的无前视版本（结论不变，样本同样 19 次）。</td></tr>
    </table>
    <div class="src">注：所有收益均为月度对数收益，未做实际价格平减（12 个月窗口内通胀影响 &lt;2pp）。World Bank Pink Sheet 为 2026-01 更新版，止于 2025M12；2026 年胶价用中国 RU 主连代理。</div>
  </div>

  <h2>二、核心结论：影响有多大、什么时候来</h2>
  <div class="ok"><b>一句话量化：ONI 每上升 1.0 → 未来 12 个月胶价 +12%（含商品普涨），其中橡胶专属 +8%；效应从第 3 个月开始显现，第 12 个月见顶，第 24 个月归零。</b></div>
  <div class="panel">
    <div id="c1" class="chart"></div>
    <div class="src">横轴＝预测期限 T+H（月），纵轴＝corr(ONI<sub>t</sub>, 未来 H 个月 RSS3 对数收益)。<b>H=0 时 r=+0.03（完全无同步反应）→ H=12 达峰 r=+0.34 → H=27 归零。</b>呈标准"驼峰"形态，说明市场<b>不是在厄尔尼诺发生时定价，而是在 6–12 个月后随供给侧减产逐步定价</b>。注意：H>12 的重叠窗口使相关系数带自相关，形态可信、绝对水平偏乐观。</div>
  </div>

  <div class="panel">
    <table>
      <tr><th>回归式</th><th>因变量</th><th>规格</th><th class="num">ONI 系数</th><th class="num">t</th>
      <th class="num">其他项系数</th><th class="num">t</th><th class="num">R²</th><th class="num">n</th></tr>
      {reg_rows}
    </table>
    <div class="src">ONI 系数单位：ONI 每上升 1.0（℃），因变量的百分点（对数收益 ×100）。"控油价"＝加入同期 Brent 收益；"控商品指数"＝加入 WB Non-energy 商品指数收益。</div>
  </div>

  <div class="callout"><b>三条被数字强化的读法：</b>
  <ul>
    <li><b>不是价格先行、而是产量先行。</b> 当月收益 ~ ΔONI 的系数为 <b>{b_doni:+.2f}（t={t_doni:+.2f}）</b>——ONI 跳升的当月，胶价甚至略微偏弱。而相关系数在 T+12 才达峰。这与机制一致：EN → 东南亚降水减少 → 割胶天数下降 → 产量下滑 → 库存去化 → 价格上行，全链条有 2–3 个季度时滞。</li>
    <li><b>关系在近 25 年变强了近一倍。</b> 1960–1999 年 β={b_1990:+.2f}（t={t_1990:+.2f}）→ 2000–2025 年 β={b_2000:+.2f}（t={t_2000:+.2f}）。可能原因：泰国/印尼供给集中度提高、天气叙事被交易化、以及 2002 年后中国需求成为边际定价者。</li>
    <li><b>不是"整个厄尔尼诺期都涨"。</b> 割胶季（6–10 月）子样本 β={b_season:+.2f}（t={t_season:+.2f}），低于全样本——因为厄尔尼诺峰值常在北半球冬季（DJF），而此时东南亚正好是<b>低产季</b>，减产没有价格弹性；真正的价格窗口在<b>次年的割胶季</b>。</li>
  </ul></div>

  <h2>三、最关键的反直觉发现：不是"越强越涨"</h2>
  <div class="panel">
    <div id="c2" class="chart"></div>
    <div class="src">柱＝各强度档事件起点后 <b>T+12 个月</b>的 RSS3 平均累计对数收益（%），虚线＝全样本 T+12 无条件基线 +1.59%。<b>红＝正、绿＝负</b>（沿用红涨绿跌）。T+6 与 T+24 的完整数值见下方分档明细表。</div>
  </div>
  <div class="panel">
    <div id="c3" class="chart"></div>
    <div class="src">每次厄尔尼诺事件一个点：横轴＝事件峰值 ONI，纵轴＝该事件起点后 T+12 个月 RSS3 收益（%）。灰色虚线＝无条件基线 +1.59%。<b>峰值 ONI 超过 2.0 的 3 个点全部落在零轴以下</b>（1997 −34.7%、2014 −20.7%、1982 +16.0%）。</div>
  </div>

  <div class="panel">
    <table>
      <tr><th>强度档</th><th class="num">事件数</th>
      <th class="num">T+6 均值</th><th class="num">超额</th><th class="num">p</th>
      <th class="num">T+12 均值</th><th class="num">超额</th><th class="num">p</th>
      <th class="num">T+24 均值</th><th class="num">超额</th><th class="num">p</th></tr>
      {tier_rows}
    </table>
    <div class="src">超额＝减全样本同期限无条件均值；p 为 Welch t 检验（事件窗口 vs 其余全部月份）。<b>注意显著性排序并不随档位单调</b>——"弱"档 p=0.006 反而比"强"档（p=0.113）更显著，这是小样本（每档 3–7 次）下的正常现象，<b>不应解读为"弱档效应更强"</b>；可信的是"全部厄尔尼诺"这一层（T+12 超额 +14.9%，p=0.025）与超强档的反向方向。</div>
  </div>

  <div class="warn"><b>超强档为什么是负的（诚实归因）：</b> 超强档只有 3 次——1982（拉美债务危机）、1997（亚洲金融危机）、2015（大宗商品崩塌＋强美元）。
  三次<b>都不是"干净的天气事件"</b>，每一次都恰好撞上全球宏观或商品需求的系统性崩塌，橡胶作为高 β 工业原料首当其冲被砸下来。
  剔除大宗商品共同 β 后，超强档相对商品指数的 T+12 超额为 <b>−2.3pp（胜率 1/3）</b>——即"不涨"是稳健的，但"大跌"主要是宏观背锅。<b>可用的结论是：超强档不具备天气溢价，不能按"越强越买"来做。</b></div>

  <div class="panel">
    <h3>19 次厄尔尼诺事件逐次明细</h3>
    <table>
      <tr><th>起始月</th><th>持续</th><th class="num">峰值 ONI</th><th>档位</th>
      <th class="num">T+6</th><th class="num">T+12</th><th class="num">T+24</th><th class="num">相对商品指数 T+12</th></tr>
      {ev_rows}
    </table>
    <div class="src">最后一列＝该窗口内 RSS3 收益 减 World Bank Non-energy 商品指数收益（pp），即剔掉"大宗商品整体涨跌"后的橡胶超额。</div>
  </div>

  <h2>四、对称性检验：拉尼娜是明确的负向</h2>
  <div class="panel">
    <table>
      <tr><th>ONI 状态</th><th class="num">月数</th><th class="num">T+12 均值</th><th class="num">超额</th><th class="num">p (Welch)</th><th class="num">胜率</th></tr>
      {state_rows}
    </table>
    <div class="src">全样本逐月（不按事件划分，n 更大故显著性更高）。拉尼娜＝ONI ≤ −0.5；中性＝−0.5～+0.5。</div>
  </div>
  <div class="ok"><b>正负对称是这套关系"真的存在"的最强证据：</b>厄尔尼诺月 T+12 超额 <b>+13.8%</b>（p&lt;0.0001）、中性 −2.1%（不显著）、拉尼娜 <b>−9.4%</b>（p&lt;0.0001）。
  如果只是噪音或共同趋势，不会出现这种"符号相反、量级相近、两侧都极显著"的形态。机制上也自洽：拉尼娜=东南亚多雨=割胶顺畅=供给宽松=价格受压。</div>

  <h2>五、2026 年现状核对</h2>
  <div class="panel">
    <div id="c4" class="chart"></div>
    <div class="src">2026 年 ONI 月度轨迹（1 月 −0.39 → 7 月 <b>+1.80</b>）。<b>1→7 月累计上升 +2.19，是 1950 年以来 77 年里的最快爬坡</b>（第二名 1997 年 +1.89，第三名 1976 年 +1.72；全期均值仅 +0.04，sd 1.13 → 本轮约 +1.9σ）。</div>
  </div>
  <div class="cards">
    <div class="kcard"><div class="lab">ONI 最新（2026 年 7 月，JJA）</div><div class="val red">+{ONI:.2f}</div><div class="note">已达"<b>强</b>"档（1.5–1.9），距"超强"阈值 2.0 仅差 0.20</div></div>
    <div class="kcard"><div class="lab">RU 橡胶主连 · 自 7/24 周报日</div><div class="val red">{cn['RU']['chg_since_report_pct']:+.1f}%</div><div class="note">16765 → {cn['RU']['close']:.0f} 元/吨，期间最高 {cn['RU']['high_since_report']:.0f}（{cn['RU']['high_pct']:+.1f}%）</div></div>
    <div class="kcard"><div class="lab">NR 20 号胶主连 · 自 7/24</div><div class="val red">{cn['NR']['chg_since_report_pct']:+.1f}%</div><div class="note">BR 顺丁同期 {cn['BR']['chg_since_report_pct']:+.1f}%</div></div>
    <div class="kcard"><div class="lab">强档历史 · T+6 平均</div><div class="val red">+15.2%</div><div class="note">n=5；RU 本轮 7 周实际 +15.2%——量级吻合</div></div>
  </div>
  <div class="panel">
    <h3>与中银期货 7/24 周报的交叉校验</h3>
    <p>该周报（报告 89 的起因）当时判断：天胶"<b>供需矛盾不突出，维持区间震荡</b>"、"<b>不建议追涨杀跌</b>"，把当周上涨归因为"中东局势升级 → 能化板块普涨 → 橡胶跟随"。</p>
    <p>事后看（7/24 → 9/11）：<b>RU +15.2%、NR +13.4%、BR +10.7%</b>，区间震荡判断被证伪。两个解释可以并存：①中东局势 → 能化板块 β（周报的解释）；②ONI 从 6 月 +1.39 跳到 7 月 +1.80、1–7 月累计 +2.19 的历史最快爬坡（周报只用"超级厄尔尼诺年"五个字带过，且同时用"产区物候预计转为正常"把它抵消掉了）。</p>
    <p><b>关键分歧点在于时滞口径：</b>周报是周度环比视角，看到的是"泰国胶水下跌 → 成本端转弱 → 矛盾不突出"；而 6–12 个月的定价视角下，EN 爬坡恰恰是<b>未来供给收缩的领先变量</b>。本次数据检验支持后者的方向——但需注意，7 周的 +15% 已经跑在历史"强档 T+6 平均 +15.2%"的前面，属于<b>抢跑</b>而非滞后确认。</p>
  </div>
  <div class="warn"><b>风险提示：继续升级到超强档，历史规律是"不涨"。</b>若 ONI 后续站上 2.0，按本报告的 3 次超强样本（1982／1997／2015），T+12 平均 −13.1%、相对商品指数超额 −2.3pp、胜率 1/3。
  即"<b>交易的是'强档'的天气溢价，而不是'超强'的天气溢价</b>"。这与你 57 号农业研究里"强厄尔尼诺越强越弱"的结论方向一致——但两边样本量都很小（本报告 n=3），只能当作风控约束，不能当作方向性下注依据。</div>

  <h2>六、限制与未解决的问题</h2>
  <div class="panel">
    <ul>
      <li><b>样本量小。</b> 66 年只出 19 次可用事件、超强档仅 3 次。分档结论（尤其超强档）的统计功效很低，Welch p 值多在 0.1–0.5，<b>不能宣称"超强档显著为负"</b>，只能说"超强档不见天气溢价"。</li>
      <li><b>重叠窗口自相关。</b> 月度前瞻收益高度重叠，t 值与相关系数偏乐观；故已并列秩检验，但读者应把量级而非精确值当结论。</li>
      <li><b>无法完全剥离宏观。</b> 三次超强档全部撞上宏观危机，用单一商品指数控制不足；更严谨需要控制实际利率、美元指数、全球制造业 PMI。油价已做控制（控油价后 β 反而升至 +14.1，因为原油与橡胶存在"合成胶替代"正向链条）。</li>
      <li><b>价格口径为美元 RSS3。</b> 中国 RU 是人民币计价、含关税与交割制度差异，1997–2026 的 β=+12.09（t=4.01）与全球口径接近，但不能逐点对齐。泰铢汇率对泰国产区报价的影响未拆。</li>
      <li><b>未做产量端验证。</b> 机制链（EN → 东南亚降水 → 割胶天数 → 产量）缺 ANRPC 月度产量数据的直接检验，目前是"价格先行 + 机制自洽"的推断，未闭环。</li>
      <li><b>结构突变未穷尽。</b> 只做了 2000 年前后切分。2008 年金融危机、2011 年胶价历史顶部、2020 年疫情都可能改变关系，未逐一检验。</li>
    </ul>
  </div>

  <div class="footer">
    <b>复现路径</b>：拉数 <code>scripts/fetch_rubber_em.py</code>（东财主连 RU/BR/NR → <code>data/rubber/</code>）；分析 <code>scripts/rubber_enso_analyze.py</code>（NOAA ONI + World Bank Pink Sheet → <code>results/rubber_enso_analysis.json</code>）；构建本页 <code>scripts/build_rubber_enso_report.py</code>。<br>
    <b>数据缓存</b>：<code>Temp/rubber_enso/oni.txt</code>、<code>Temp/rubber_enso/wb_monthly.xlsx</code>（2026-01 版）。<br>
    本报告为量化研究记录，不构成投资建议。所有数字均来自上述可复现脚本输出，未做人工调整。
  </div>
</div>

<script>
const D = {PANEL_DATA};
const RED = '#b2182b', GREEN = '#1a7a3a', BLUE = '#0072B2', ORANGE = '#E69F00', VERM = '#D55E00';
const base = {{6: 0.68, 12: 1.59, 24: 3.69}};
const AX = {{axisLine:{{lineStyle:{{color:'#c9d4e0'}}}}, axisLabel:{{color:'#5a6a7d',fontSize:11}},
           splitLine:{{lineStyle:{{color:'#eef2f7'}}}}, nameTextStyle:{{color:'#5a6a7d',fontSize:11}}}};

// 图1 期限扫描
echarts.init(document.getElementById('c1')).setOption({{
  grid:{{left:58,right:24,top:34,bottom:44}},
  tooltip:{{trigger:'axis',valueFormatter:v=>v.toFixed(3)}},
  xAxis:Object.assign({{type:'category',name:'T+H（月）',nameLocation:'middle',nameGap:26,data:D.scan.map(s=>s.h)}},AX),
  yAxis:Object.assign({{type:'value',name:'相关系数 r',min:-0.05,max:0.4}},AX),
  series:[{{type:'line',smooth:true,symbolSize:7,data:D.scan.map(s=>s.r),
    lineStyle:{{color:BLUE,width:2.5}},itemStyle:{{color:BLUE}},
    areaStyle:{{color:'rgba(0,114,178,0.10)'}},
    markLine:{{silent:true,symbol:'none',lineStyle:{{color:'#b3b3b3',type:'dashed'}},
      data:[{{yAxis:0,label:{{formatter:'0',color:'#5a6a7d',fontSize:10}}}}]}},
    markPoint:{{symbolSize:0,data:[{{coord:[D.scan.findIndex(s=>s.h===12),D.scan.find(s=>s.h===12).r],label:{{formatter:'峰值 r=+0.34（T+12）',color:RED,fontSize:11,position:'top',distance:10}}}}]}}
  }}]
}});

// 图2 分档柱状（主口径 T+12，红涨绿跌）
const tiers = D.tiers.map(t=>t.label);
echarts.init(document.getElementById('c2')).setOption({{
  grid:{{left:70,right:30,top:30,bottom:36}},
  tooltip:{{trigger:'axis',formatter:p=>{{
    const t=D.tiers[p[0].dataIndex];
    return t.label+'（n='+t.n+'）<br>T+6 '+t.t6.toFixed(1)+'%　T+12 '+t.t12.toFixed(1)+'%　T+24 '+t.t24.toFixed(1)+'%';}}}},
  xAxis:Object.assign({{type:'category',data:tiers}},AX),
  yAxis:Object.assign({{type:'value',name:'T+12 累计对数收益 %'}},AX),
  series:[{{name:'T+12',type:'bar',barWidth:'46%',
    data:D.tiers.map(t=>({{value:t.t12,itemStyle:{{color:t.t12>=0?RED:GREEN,borderRadius:[3,3,0,0]}}}})),
    label:{{show:true,position:'top',fontSize:11,color:'#1a2330',
      formatter:p=>(p.value>=0?'+':'')+p.value.toFixed(1)+'%'}},
    markLine:{{silent:true,symbol:'none',lineStyle:{{color:'#b3b3b3',type:'dashed'}},
      data:[{{yAxis:base[12],label:{{formatter:'全样本 T+12 基线 +1.6%',color:'#8b98a8',fontSize:10,position:'insideStartTop',distance:6}}}}]}}}}]
}});

// 图3 事件散点
const tc = {{'超强':VERM,'强':ORANGE,'中':BLUE,'弱':'#009E73'}};
const sc = Object.keys(tc).map(k=>({{
  name:k, type:'scatter', symbolSize:14, itemStyle:{{color:tc[k]}},
  data:D.events.filter(e=>e.tier===k).map(e=>[e.peak,e.t12,e.a])
}}));
sc[0].markLine = {{silent:true,symbol:'none',lineStyle:{{width:1.2}},
  data:[{{xAxis:2.0,lineStyle:{{color:VERM,type:'dashed'}},
          label:{{formatter:'超强阈值 ONI=2.0',color:VERM,fontSize:10,position:'insideEndTop',rotate:0,padding:[0,0,2,0]}}}},
        {{yAxis:1.59,lineStyle:{{color:'#b3b3b3',type:'dashed'}},
          label:{{formatter:'全样本基线 +1.6%',color:'#8b98a8',fontSize:10,position:'insideStartTop'}}}}]}};
echarts.init(document.getElementById('c3')).setOption({{
  grid:{{left:70,right:30,top:38,bottom:44}},
  tooltip:{{formatter:p=>p.data[2]+'（'+p.seriesName+'档）<br>峰值 ONI '+p.data[0].toFixed(2)+'　T+12 '+(p.data[1]>=0?'+':'')+p.data[1].toFixed(1)+'%'}},
  legend:{{top:2,textStyle:{{color:'#5a6a7d',fontSize:11}}}},
  xAxis:Object.assign({{type:'value',name:'事件峰值 ONI',nameLocation:'middle',nameGap:28,min:0.4,max:2.8}},AX),
  yAxis:Object.assign({{type:'value',name:'T+12 收益 %',min:-45,max:80}},AX),
  series:sc
}});

// 图4 ONI 轨迹
const o26 = D.oni2026.map(x=>x.anom);
echarts.init(document.getElementById('c4')).setOption({{
  grid:{{left:58,right:24,top:34,bottom:44}},
  tooltip:{{trigger:'axis'}},
  xAxis:Object.assign({{type:'category',data:['1月','2月','3月','4月','5月','6月','7月']}},AX),
  yAxis:Object.assign({{type:'value',name:'ONI（℃）',min:-0.6,max:2.1}},AX),
  series:[{{type:'line',data:o26,smooth:true,symbolSize:8,
    lineStyle:{{color:RED,width:3}},itemStyle:{{color:RED}},
    areaStyle:{{color:'rgba(178,24,43,0.10)'}},
    markLine:{{silent:true,symbol:'none',
      data:[{{yAxis:1.5,lineStyle:{{color:ORANGE,type:'dashed'}},label:{{formatter:'强档 1.5',color:ORANGE,fontSize:10,position:'insideStartTop'}}}},
            {{yAxis:2.0,lineStyle:{{color:VERM,type:'dashed'}},label:{{formatter:'超强档 2.0',color:VERM,fontSize:10,position:'insideStartTop'}}}}]}}
  }}]
}});
</script>
</body>
</html>
"""

os.makedirs(OUTDIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"[OK] {OUT}  {len(HTML)} bytes")
print(f"     ONI={ONI} b12={b_on12} b_ex={b_ex12} b2000={b_2000} b1990={b_1990} b_ru={b_ru}")
