#!/usr/bin/env python3
"""生成《药明康德 × 美国制药景气》HTML 报告。
读 results/wuxi_bigpharma.json，输出 reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_bigpharma_report.html
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "reports", "03_wuxi_bigpharma药明康德vs美国药企")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(ROOT, "results", "wuxi_bigpharma.json"), encoding="utf-8") as f:
    D = json.load(f)

# ---- 预处理：大药企均值滚动相关、均值超额 ----
bp = ["ABBV", "MRK", "JNJ", "LLY", "GILD"]
bp_name = {"ABBV": "艾伯维", "MRK": "默沙东", "JNJ": "强生", "LLY": "礼来", "GILD": "吉利德"}
bp_color = {"ABBV": "#8e6bb5", "MRK": "#2e5f9e", "JNJ": "#b9770e", "LLY": "#1e8449", "GILD": "#c0392b"}
bench_color = {"IBB": "#5b9bd5", "XBI": "#ed7d31", "XLV": "#70ad47", "SPY": "#7f7f7f"}
main_color = {"WUXIH": "#c0392b", "WUXIA": "#e67e22", "IBB": "#5b9bd5", "XBI": "#ed7d31", "XLV": "#70ad47", "SPY": "#9aa0a6"}

# 滚动相关: 找公共日期（用 XBI 的日期为基准）
xbi_dates = [p["date"] for p in D["rolling60"][0]["series"]]  # ticker 顺序: BIG_PHARMA+BENCH
bp_roll = {k: {p["date"]: p["corr"] for p in next(r["series"] for r in D["rolling60"] if r["ticker"] == k)}
           for k in bp}
roll_common = []
for d in xbi_dates:
    vals = [bp_roll[k].get(d) for k in bp]
    vals = [v for v in vals if v is not None]
    if len(vals) >= 3:
        roll_common.append({"date": d, "avg": round(sum(vals) / len(vals), 2)})

# 分段超额: 大药企均值
excess_avg = []
seg_names = ["2021-01-01~2024-12-31", "2025-01-01~2025-08-31", "2025-09-01~2026-02-01",
             "2026-02-02~2026-06-08", "2026-06-08 以来"]
seg_labels = ["2021~2024", "2025H1", "2025-09~2026-02", "2026-02~06-08", "2026-06-08 以来"]
for i, sn in enumerate(seg_names):
    exs = []
    for k in bp:
        for e in D["excess"]:
            if e["ticker"] == k:
                for s in e["segs"]:
                    if s["name"] == sn:
                        exs.append(s["excess"])
    if exs:
        excess_avg.append({"seg": sn, "label": seg_labels[i], "avg": round(sum(exs) / len(exs), 2)})

# 事件窗口
events = D["events"]

# A/H 分阶段
ah_segs = {b["name"]: b["pearson"] for b in D["ah"]["segs"]}
ah_pre = ah_segs.get("2026-02 前")
ah_post = ah_segs.get("2026-02 起(1260H冲击期)")
ah_full = D["ah"]["block"]["pearson"]

# 相关矩阵行
pair_rows = []
for k in ["ABBV", "MRK", "JNJ", "LLY", "GILD", "IBB", "XBI", "XLV", "SPY"]:
    blocks = {b["name"]: b for b in D["pairwise"][k]}
    row = {"k": k, "name": D["meta"]["target"] if False else
           {"ABBV": "艾伯维", "MRK": "默沙东", "JNJ": "强生", "LLY": "礼来", "GILD": "吉利德",
            "IBB": "IBB生物科技ETF", "XBI": "XBI生物科技ETF", "XLV": "XLV医疗保健ETF", "SPY": "SPY标普500ETF"}[k],
           "vals": [blocks[bname]["pearson"] for bname in
                    ["全期", "2025-09 前", "2025-09 起", "2026-02 前", "2026-02 起(1260H冲击期)", "2026-06 起(列名+禁令期)"]],
           "r2": blocks["全期"]["r2"], "beta": blocks["全期"]["beta"], "n": blocks["全期"]["n"]}

# 超额表
excess_rows = []
for e in D["excess"]:
    segs = {s["name"]: s for s in e["segs"]}
    row = {"k": e["ticker"], "name": e["name"],
           "vals": [segs[sn]["excess"] for sn in seg_names],
           "wret": [segs[sn]["w_ret"] for sn in seg_names]}
    excess_rows.append(row)

data_js = {
    "pair_rows": pair_rows,
    "excess_rows": excess_rows,
    "excess_avg": excess_avg,
    "roll_xbi": next(r["series"] for r in D["rolling60"] if r["ticker"] == "XBI"),
    "roll_ibb": next(r["series"] for r in D["rolling60"] if r["ticker"] == "IBB"),
    "roll_bp_avg": roll_common,
    "monthly_xbi": D["monthly"]["XBI"][-24:],
    "monthly_llly": D["monthly"]["LLY"][-24:],
    "monthly_ibb": D["monthly"]["IBB"][-24:],
    "net_main": D["net_main"],
    "net_pharma": {k: D["norm_net"][k]["series"] for k in bp},
    "net_pharma_name": {k: D["norm_net"][k]["name"] for k in bp},
    "events": [{"date": e["date"], "desc": e["desc"],
                "wuxi": e["wuxi_5d"], "xbi": e["xbi_5d"], "ibb": e["ibb_5d"]} for e in events],
    "ah": D["ah"],
    "bp_name": bp_name, "bp_color": bp_color,
    "bench_color": bench_color, "main_color": main_color,
}

def esc(v):
    return json.dumps(v, ensure_ascii=False)

# ---- 动态生成第三节相关性表 ----
BENCH = ["IBB", "XBI", "XLV", "SPY"]
SEG_HDRS = ["全期", "2025-09 前", "2025-09 起", "2026-02 前", "2026-02 起<br>(1260H冲击)", "2026-06 起<br>(列名+禁令)"]
def fmt_corr(v):
    return "—" if v is None else f"{v:.3f}" if v < 0 or v > 0.1 else f"{v:.3f}"
pair_tbl_rows = ""
for r in pair_rows:
    bg = ' style="background:#f6f8fb;"' if r["k"] in BENCH else ""
    bold = "<b>" if r["k"] in BENCH else ""
    bclose = "</b>" if r["k"] in BENCH else ""
    cells = "".join(f"<td>{fmt_corr(v)}</td>" for v in r["vals"])
    pair_tbl_rows += (f"<tr{bg}><td>{bold}{r['name']}{bclose}</td>{cells}"
                      f"<td>{r['r2']*100:.1f}%</td><td>{r['beta']:.2f}</td></tr>\n")

# 动态生成第七节超额表 (仅 5 大药企 + IBB/XBI, 与表头 7 列对应)
excess_show = ["ABBV", "MRK", "JNJ", "LLY", "GILD", "IBB", "XBI"]
excess_tbl_rows = ""
for r in excess_rows:
    if r["k"] not in excess_show:
        continue
    cells = ""
    for v, wr in zip(r["vals"], r["wret"]):
        cls = "up" if v > 0 else ("down" if v < 0 else "")
        cells += f'<td class="{cls}">{v:+.1f}</td>'
    bg = ' style="background:#f6f8fb;"' if r["k"] in BENCH else ""
    bold = "<b>" if r["k"] in BENCH else ""
    bclose = "</b>" if r["k"] in BENCH else ""
    excess_tbl_rows += f"<tr{bg}><td>{bold}{r['name']}{bclose}</td>{cells}</tr>\n"

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>药明康德 × 美国制药景气 · 相关性分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#ffffff;
          --red:#c0392b; --green:#1e8449; --blue:#2e5f9e; --amber:#b9770e; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }
  .wrap { max-width: 1080px; margin: 0 auto; }
  h1 { font-size: 26px; letter-spacing: .5px; margin-bottom: 4px; }
  .subtitle { color: var(--sub); font-size: 13px; margin-bottom: 22px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(20,30,50,.05); }
  .card h2 { font-size: 17px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .card h2::before { content: ""; width: 4px; height: 16px; background: var(--blue); border-radius: 2px; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 4px; }
  .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .kv { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .kv .k { font-size: 12px; color: var(--sub); }
  .kv .v { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .kv .v small { font-size: 12px; font-weight: 400; color: var(--sub); }
  .up { color: var(--red); } .down { color: var(--green); }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; margin-top: 6px; }
  th, td { padding: 9px 10px; text-align: right; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; }
  th:first-child, td:first-child { text-align: left; }
  .note { font-size: 12px; color: var(--sub); margin-top: 10px; }
  .chart { width: 100%; height: 340px; }
  .chart-sm { width: 100%; height: 280px; }
  .concl { border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }
  .concl b { color: var(--blue); }
  .disclaimer { font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }
  .src { font-size: 11.5px; color: var(--sub); margin-top: 8px; }
  .flow { display: flex; flex-direction: column; gap: 0; margin-top: 6px; }
  .frow { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; align-items: stretch; }
  .fbox { border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; background: var(--bg); }
  .fbox .fh { font-size: 13px; font-weight: 700; margin-bottom: 6px; }
  .fbox .fb { font-size: 12.5px; color: var(--sub); }
  .fbox.hl { border-color: var(--blue); background: #f4f8ff; }
  .farrow { text-align: center; font-size: 18px; color: var(--blue); line-height: 2.2; }
  .legend-row { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12.5px; color: var(--sub); margin-bottom: 6px; }
  .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: -1px; }
  @media (max-width: 720px) { .grid3, .grid4, .grid2, .frow { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>药明康德 × 美国制药景气：它到底在反映什么周期？</h1>
  <div class="subtitle">药明康德（603259.SH / 2359.HK） vs 美国大型药企（ABBV / MRK / JNJ / LLY / GILD）· 相关性、领先滞后与事件冲击拆解 · 数据截至 2026-08-14</div>

  <div class="card">
    <h2>一、核心结论</h2>
    <div class="grid4">
      <div class="kv"><div class="k">药明H vs 5 大药企 · 全期日收益相关</div>
        <div class="v">≈ 0.02 <small>均值 Pearson</small></div>
        <div class="k" style="margin-top:6px;">R² &lt; 0.5%，几乎零联动</div></div>
      <div class="kv"><div class="k">药明H vs 板块指数 · 全期相关</div>
        <div class="v">0.095–0.115 <small>vs XBI / IBB</small></div>
        <div class="k" style="margin-top:6px;">美股 biotech 领先药明 1 天（lag −1 相关 0.18）</div></div>
      <div class="kv"><div class="k">2026-02 以来（1260H 冲击期）</div>
        <div class="v"><span class="up">药明H +80.4%</span></div>
        <div class="k" style="margin-top:6px;">大药企均值 +10.6% · XBI +23.6% → 完全独立行情</div></div>
      <div class="kv"><div class="k">A/H 同股联动</div>
        <div class="v">0.825 <small>日收益相关</small></div>
        <div class="k" style="margin-top:6px;">A 股受北向/情绪扰动，H 股与美股联动更强</div></div>
    </div>
    <div class="concl">
      <b>药明康德反映的是「全球创新药研发外包周期」，不是美国大药企的「销售景气 / 股价周期」。</b><br>
      ① 美国客户收入占比约 <b>72%</b>、2026 年中在手订单 <b>+25.2%</b>（664.3 亿元）、小分子 D&amp;M +72.7% / TIDES +44.3% —— 订单景气是真实的，但它由「大药企研发预算 + biotech 融资 + 外包率」驱动，而不是药企卖药好不好。<br>
      ② 股价层面：与 ABBV / MRK / JNJ / LLY / GILD 的<b>全期日收益相关性几乎为 0</b>（均值 0.02，R²&lt;0.5%），月度相关正负交替、无稳定方向 —— 用大药企股价看药明、或用药明看大药企股价，都无效。<br>
      ③ 药明的超额波动主要来自 <b>地缘政治事件</b>（BIOSECURE / 1260H：2024-03 单日窗口 −9.7% vs XBI −3.0%）与<b>自身订单兑现</b>（2026-02 以来 +80% vs GILD −3.2%），是典型的「个股 alpha 行情」。
    </div>
    <div class="src">数据：Yahoo Finance 日线（收盘价）；药明H 2018-12-13 ~ 2026-08-14（1833 个共同交易日）；美国客户占比/在手订单/业绩指引为 2026 年中报口径（公司公告，2026-08-04 披露）。</div>
  </div>

  <div class="card">
    <h2>二、传导逻辑：药明康德收入的「景气决定式」</h2>
    <div class="flow">
      <div class="frow">
        <div class="fbox hl"><div class="fh">① 上游需求（研发周期景气）</div>
          <div class="fb">美国大药企研发预算（2025 Top16 合计 <b>−3.6%</b>，但礼来 +21.4%、阿斯利康 +5%、诺华 +12%、GSK +19%）<br>+ Biotech 融资（2026H1 VC 融资 $163 亿、BD 交易 $1667 亿，显著回暖）<br>+ 研发外包率持续上行（GLP-1 / TIDES / ADC 分子复杂度提升）</div></div>
        <div class="farrow">→</div>
        <div class="fbox"><div class="fh">② 中游传导（CXO 订单）</div>
          <div class="fb">药明康德在手订单 <b>664.3 亿元（+25.2%）</b>、合同负债 35.8 亿<br>美国客户 &gt;1000 家、收入占比约 <b>72%</b>（2025 全年 312.5 亿元 +34.3%）</div></div>
        <div class="farrow">→</div>
        <div class="fbox"><div class="fh">③ 药明康德股价</div>
          <div class="fb">= 订单景气 × 估值（历史上被打断过：2021 估值泡沫破裂、2024-2026 BIOSECURE / 1260H 地缘折价）</div></div>
      </div>
      <div style="text-align:center; color:var(--sub); font-size:12px; padding:6px 0;">────── 分隔线：两条景气线只在「研发投入」处交汇 ──────</div>
      <div class="frow">
        <div class="fbox"><div class="fh">大药企股价 = f(产品销售 / 管线催化)</div>
          <div class="fb">礼来 +366%（2021-2024，GLP-1 产品放量）；艾伯维专利悬崖后靠收购续命；吉利德靠个股事件<br>—— 与「研发外包需求」在股价层面几乎无关（R²&lt;0.5%）</div></div>
        <div class="farrow" style="color:var(--sub);">↕</div>
        <div class="fbox"><div class="fh">药明康德 = f(研发外包需求)</div>
          <div class="fb">订单 +25%、TIDES +44%、指引上调 70 亿 —— 反映的是「行业在研发上花多少钱」，不是「药卖得好不好」</div></div>
        <div class="farrow" style="color:var(--sub);">↕</div>
        <div class="fbox"><div class="fh">观察药明景气的更优代理</div>
          <div class="fb">XBI / IBB（biotech 融资周期）· 大药企 R&amp;D 预算（尤其 LLY / AZN / NVS / GSK）· BD 交易额 —— 都比大药企股价更贴近药明的收入决定式</div></div>
      </div>
    </div>
    <div class="src">研发投入数据：2025 财年公司披露口径（默沙东 $157.9 亿 −12%、强生 $146.6 亿 −14.9%、礼来 $133.4 亿 +21.4%、艾伯维 $91 亿 −28.9%，Top16 合计 −3.6%），需核实原文；融资/BD 数据：2026 上半年行业统计（非一手来源）。</div>
  </div>

  <div class="card">
    <h2>三、相关性全景：跟谁都不亲，跟 biotech 勉强沾边</h2>
    <table>
      <tr><th>药明H vs</th><th>全期</th><th>2025-09 前</th><th>2025-09 起</th><th>2026-02 前</th><th>2026-02 起<br>(1260H冲击)</th><th>2026-06 起<br>(列名+禁令)</th><th>全期 R²</th><th>β</th></tr>
      __PAIR_TBL__
    </table>
    <div class="note">※ 全期 n=1833 个共同交易日（2018-12 ~ 2026-08）。所有相关性均在 0.05 以下（大药企）或 0.12 以下（板块指数）——即使是「同赛道」的 IBB / XBI，日收益层面的联动也弱到无法作为彼此的指示器。唯一例外：2026-06-08 列名后的修复期（约 47 个交易日）药明与 SPY / IBB 短期相关升至 0.40 / 0.20，属「共同事件驱动」的临时共振，样本小、不改变全期结论。</div>
    <div class="legend-row" style="margin-top:14px;"><span><span class="dot" style="background:#ed7d31;"></span>药明H vs XBI</span><span><span class="dot" style="background:#5b9bd5;"></span>药明H vs IBB</span><span><span class="dot" style="background:#8e6bb5;"></span>药明H vs 5大药企均值</span></div>
    <div id="chart1" class="chart"></div>
    <div class="note">60 日滚动相关性（2023 起）：多数时间在 ±0.2 之间来回摆动，几乎没有持续正相关的区间 —— 药明 H 的日波动由自身事件主导，与美股医药资产只是「偶尔共振」。</div>
  </div>

  <div class="card">
    <h2>四、月度相关性：正负交替，无稳定方向</h2>
    <div class="legend-row"><span><span class="dot" style="background:#ed7d31;"></span>药明H vs XBI</span><span><span class="dot" style="background:#1e8449;"></span>药明H vs 礼来 LLY</span></div>
    <div id="chart2" class="chart-sm"></div>
    <div class="note">近 24 个月（2024-09 ~ 2026-08）：药明H vs XBI 月相关在 −62%（2025-01，地缘冲击独立下跌）到 +63%（2026-08，禁令+中报共振）之间剧烈摆动；vs LLY 同样无系统方向。负相关月份多对应「药明独自被地缘利空砸 / 独自修复」的时期。</div>
  </div>

  <div class="card">
    <h2>五、相对强弱：2021 年以来三条完全不同的叙事</h2>
    <div class="legend-row">
      <span><span class="dot" style="background:#c0392b;"></span>药明康德H</span>
      <span><span class="dot" style="background:#e67e22;"></span>药明康德A</span>
      <span><span class="dot" style="background:#5b9bd5;"></span>IBB</span>
      <span><span class="dot" style="background:#ed7d31;"></span>XBI</span>
      <span><span class="dot" style="background:#70ad47;"></span>XLV</span>
      <span><span class="dot" style="background:#9aa0a6;"></span>SPY</span>
    </div>
    <div id="chart3" class="chart"></div>
    <div class="note">2021-01 起归一化净值（=100）：药明 H 经历「2021 见顶 → 2022-2024 杀估值 + BIOSECURE 打击（最低约 −70%）→ 2025 起 V 型修复」；礼来同期 +366%、SPY +110% —— 药明的「研发景气」在股价上被估值消化与地缘折价完全吞掉，直到 2025 年才重新定价。</div>
    <div class="legend-row" style="margin-top:10px;">
      <span><span class="dot" style="background:#c0392b;"></span>药明康德H</span>
      <span><span class="dot" style="background:#8e6bb5;"></span>艾伯维</span>
      <span><span class="dot" style="background:#2e5f9e;"></span>默沙东</span>
      <span><span class="dot" style="background:#b9770e;"></span>强生</span>
      <span><span class="dot" style="background:#1e8449;"></span>礼来</span>
      <span><span class="dot" style="background:#c0392b;"></span>吉利德</span>
    </div>
    <div id="chart4" class="chart"></div>
    <div class="note">药明 vs 5 大药企：除了 2021 年共同见顶外，走势几乎无交集 —— 药明 2022-2024 深熊时礼来在狂奔（GLP-1），2025-2026 药明修复时吉利德在创新低。两条线的驱动因子（研发外包 vs 产品销售）完全不同。</div>
  </div>

  <div class="card">
    <h2>六、事件冲击：BIOSECURE / 1260H 才是药明的「主驱动」</h2>
    <div id="chart5" class="chart"></div>
    <table>
      <tr><th>事件日期</th><th>事件</th><th>药明H 5日</th><th>IBB 5日</th><th>XBI 5日</th></tr>
      <tr><td>2024-03-06</td><td>BIOSECURE 参议院版提出（市场首波恐慌）</td><td class="down">-9.7%</td><td class="up">+0.3%</td><td class="down">-3.0%</td></tr>
      <tr><td>2024-05-15</td><td>众议院委员会口头通过 BIOSECURE</td><td class="down">-5.5%</td><td class="up">+1.8%</td><td class="up">+1.5%</td></tr>
      <tr><td>2024-09-09</td><td>众议院全会 306-81 通过（靴子落地）</td><td class="up">+4.9%</td><td class="up">+2.5%</td><td class="up">+3.5%</td></tr>
      <tr><td>2025-12-18*</td><td>FY2026 NDAA 签署，BIOSECURE 生效（去点名、衔接1260H）</td><td class="down">-2.0%</td><td class="up">+2.8%</td><td class="up">+2.8%</td></tr>
      <tr><td>2026-02-13</td><td>1260H 短暂公示后 1 小时撤回</td><td class="down">-2.7%</td><td class="up">+1.6%</td><td class="up">+4.4%</td></tr>
      <tr><td>2026-06-08</td><td>正式列入 1260H 名单（利空钝化）</td><td class="up">+3.2%</td><td class="up">+3.2%</td><td class="up">+6.2%</td></tr>
      <tr><td>2026-06-11</td><td>药明起诉美国国防部</td><td class="up">+4.3%</td><td class="up">+1.9%</td><td class="up">+6.0%</td></tr>
      <tr><td>2026-08-07</td><td>法院批准初步禁令（诉讼期免受1260H不利影响）</td><td class="up">+2.7%</td><td class="up">+0.3%</td><td class="up">+0.0%</td></tr>
    </table>
    <div class="note">※ 2025-12-18 为 NDAA 签署月（具体签署日以白宫公告为准）；2026 年各日期均来自公司公告（港交所披露易）与公开报道。规律：<b>利空砸盘时药明独自跌（远超板块），利空落地/反转时药明独自涨（远超板块）</b> —— 地缘事件是药明 2024 年以来最大的股价驱动，与大药企景气无关。</div>
  </div>

  <div class="card">
    <h2>七、分段超额：药明 vs 大药企 / biotech 指数的「脱钩账本」</h2>
    <table>
      <tr><th>区间</th><th>艾伯维</th><th>默沙东</th><th>强生</th><th>礼来</th><th>吉利德</th><th>IBB</th><th>XBI</th></tr>
      __EXCESS_TBL__
    </table>
    <div class="note">数值 = 药明H 区间收益 − 标的区间收益（pp）。三阶段特征：① 2021-2024 药明大幅跑输（尤其对礼来 −423pp，GLP-1 产品周期 vs CXO 杀估值）；② 2025H1 药明 V 型修复反超；③ 2026-06 列名后药明走出独立主升（+63% vs 大药企均值 +10%）—— 每一段的「超额」都由药明自身的事件/估值驱动，而非与美国药企的同向联动。</div>
  </div>

  <div class="card">
    <h2>八、领先 / 滞后：美股 biotech 领先药明 1 个交易日（但强度很弱）</h2>
    <table>
      <tr><th>药明H vs</th><th>0 期相关</th><th>最优滞后</th><th>最优相关</th><th>解读</th></tr>
      <tr><td>IBB</td><td>0.115</td><td>-1 天（IBB 领先）</td><td>0.181</td><td>美股 T 日收盘 → 港股 T+1 跟随（跨时区属性）</td></tr>
      <tr><td>XBI</td><td>0.095</td><td>-1 天（XBI 领先）</td><td>0.178</td><td>同上，biotech 情绪隔夜传导</td></tr>
      <tr><td>SPY</td><td>0.099</td><td>-1 天（SPY 领先）</td><td>0.127</td><td>大盘 beta 的隔夜传导</td></tr>
      <tr><td>5 大药企</td><td>0.02</td><td>无一致模式</td><td>≤0.06</td><td>噪音级，无任何领先/滞后关系</td></tr>
    </table>
    <div class="note">对板块指数存在「美股先动、药明次日跟」的跨市场节奏（lag −1 相关 0.18 vs 同日 0.12），但强度仍弱；对大药企无任何可辨识的领先滞后关系 —— 药明不是美国大药企的领先指标，也不是滞后指标。</div>
  </div>

  <div class="card">
    <h2>九、A / H 对照与综合结论</h2>
    <div class="grid3">
      <div class="kv"><div class="k">A/H 日收益相关（全期）</div><div class="v">0.825</div>
        <div class="k" style="margin-top:6px;">2018-12 起 1800 个共同交易日</div></div>
      <div class="kv"><div class="k">A/H 分阶段</div><div class="v">__AH_PRE__ → __AH_POST__</div>
        <div class="k" style="margin-top:6px;">2026-02 前 → 2026-02 起（冲击期共同事件驱动，A/H 反而更同步）</div></div>
      <div class="kv"><div class="k">结论定位</div><div class="v">研发外包景气</div>
        <div class="k" style="margin-top:6px;">≠ 大药企销售景气（R²&lt;0.5%）</div></div>
    </div>
    <div class="concl">
      <b>多大程度反映美国制药景气度？</b> 一句话：<b>反映「研发投入周期」的强度高，反映「大药企股价/销售景气」的强度≈0</b>。<br>
      ① <b>如果你要的是「美国药企卖药景气」</b>（礼来 GLP-1 放量、艾伯维专利悬崖这类）—— 药明康德完全不反映，看药企自己的财报与管线即可。<br>
      ② <b>如果你要的是「全球研发外包景气」</b>（biotech 融资、BD 交易、大药企研发预算）—— 药明康德的订单（+25.2%）、TIDES（+44.3%）、指引上调是最直接的读数，但请用 <b>XBI / biotech 融资额 / 大药企 R&amp;D 预算</b>做先行观察，而不是大药企股价。<br>
      ③ <b>反向警示</b>：2026-02 以来药明 +80% 而吉利德 −3.2% —— 「药明强」绝不能推导出「美国药企强」，反之亦然。两者分属研发周期与产品周期，中间只隔着一层「研发外包率」的弹性。<br>
      ④ 2026 年药明的超额主要由 1260H 禁令与中报驱动，地缘事件的「脱敏→修复」路径仍是未来最大变量（初步禁令≠终审，正式名单 2026-12-18 前仍需观察）。
    </div>
    <div class="src">A/H 分阶段：2026-02 前 0.86 / 2026-02 起 0.69（Pearson）。报告数据：Yahoo Finance 日线（2015/2018 起 ~ 2026-08-14）；基本面与事件：药明康德 2026 年中报（公司公告）、港交所披露易公告（2026-06/08）、财联社/时代财经等媒体报道（需核实原文）。</div>
  </div>

  <div class="disclaimer">
    <b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
  </div>

</div>
<script>
const DATA = """ + esc(data_js) + """;
const AX = { axisLine: { lineStyle: { color: '#d5dce6' } }, axisLabel: { color: '#5b6675', fontSize: 11 } };
const TL = { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e3e8ef', textStyle: { color: '#1f2733', fontSize: 12 } };

// chart1: 滚动60日相关
(() => {
  const dates = DATA.roll_xbi.map(p => p.date);
  const s1 = DATA.roll_xbi.map(p => p.corr);
  const s2 = DATA.roll_ibb.map(p => p.corr);
  const s3 = DATA.roll_bp_avg.map(p => p.corr);
  echarts.init(document.getElementById('chart1')).setOption({
    tooltip: TL,
    legend: { data: ['vs XBI', 'vs IBB', 'vs 5大药企均值'], textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 46, right: 16, top: 34, bottom: 26 },
    xAxis: { type: 'category', data: dates, ...AX },
    yAxis: { type: 'value', name: '相关(%)', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
    series: [
      { name: 'vs XBI', type: 'line', showSymbol: false, data: s1, lineStyle: { width: 1.4 }, color: '#ed7d31' },
      { name: 'vs IBB', type: 'line', showSymbol: false, data: s2, lineStyle: { width: 1.4 }, color: '#5b9bd5' },
      { name: 'vs 5大药企均值', type: 'line', showSymbol: false, data: s3, lineStyle: { width: 2 }, color: '#8e6bb5' }
    ]
  });
})();

// chart2: 月度相关
(() => {
  const months = DATA.monthly_xbi.map(p => p.month);
  const xb = DATA.monthly_xbi.map(p => p.corr);
  const ly = DATA.monthly_llly.map(p => p.corr);
  const mk = arr => arr.map(v => ({ value: v, itemStyle: { color: v >= 0 ? '#c0392b' : '#1e8449' } }));
  echarts.init(document.getElementById('chart2')).setOption({
    tooltip: TL,
    legend: { data: ['vs XBI', 'vs LLY'], textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 46, right: 16, top: 34, bottom: 26 },
    xAxis: { type: 'category', data: months, ...AX },
    yAxis: { type: 'value', name: '相关(%)', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
    series: [
      { name: 'vs XBI', type: 'bar', barGap: '-100%', barWidth: 6, data: mk(xb) },
      { name: 'vs LLY', type: 'bar', barWidth: 6, data: mk(ly) }
    ]
  });
})();

// chart3: 净值主图
(() => {
  const keys = ['WUXIH', 'WUXIA', 'IBB', 'XBI', 'XLV', 'SPY'];
  const dates = DATA.net_main['WUXIH'].series.map(p => p.date);
  const series = keys.map(k => ({
    name: DATA.net_main[k].name,
    type: 'line', showSymbol: false,
    data: DATA.net_main[k].series.map(p => p.v),
    lineStyle: { width: k === 'WUXIH' ? 3 : 1.5 },
    color: DATA.main_color[k]
  }));
  echarts.init(document.getElementById('chart3')).setOption({
    tooltip: TL,
    legend: { data: series.map(s => s.name), textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 50, right: 16, top: 36, bottom: 26 },
    xAxis: { type: 'category', data: dates, ...AX },
    yAxis: { type: 'value', name: '2021-01=100', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
    series
  });
})();

// chart4: 药明 vs 大药企净值
(() => {
  const dates = DATA.net_pharma['ABBV'].map(p => p.date);
  const phSeries = Object.keys(DATA.net_pharma).map(k => ({
    name: DATA.net_pharma_name[k],
    type: 'line', showSymbol: false,
    data: DATA.net_pharma[k].map(p => p.v),
    lineStyle: { width: 1.4 },
    color: DATA.bp_color[k]
  }));
  const wuxi = DATA.net_main['WUXIH'].series.map(p => p.v);
  const all = [{ name: '药明康德H', type: 'line', showSymbol: false, data: wuxi, lineStyle: { width: 3 }, color: '#c0392b' }, ...phSeries];
  echarts.init(document.getElementById('chart4')).setOption({
    tooltip: TL,
    legend: { data: all.map(s => s.name), textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 50, right: 16, top: 36, bottom: 26 },
    xAxis: { type: 'category', data: dates, ...AX },
    yAxis: { type: 'value', name: '2021-01=100', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
    series: all
  });
})();

// chart5: 事件窗口
(() => {
  const names = DATA.events.map(e => e.date);
  const mk = arr => arr.map(v => v === null ? { value: 0, itemStyle: { color: '#ccc' } } : { value: v });
  echarts.init(document.getElementById('chart5')).setOption({
    tooltip: TL,
    legend: { data: ['药明H 5日', 'IBB 5日', 'XBI 5日'], textStyle: { color: '#5b6675', fontSize: 11 } },
    grid: { left: 46, right: 16, top: 36, bottom: 60 },
    xAxis: { type: 'category', data: names, axisLabel: { color: '#5b6675', fontSize: 10, rotate: 30 }, axisLine: { lineStyle: { color: '#d5dce6' } } },
    yAxis: { type: 'value', name: '事件日前后5日涨跌(%)', ...AX, splitLine: { lineStyle: { color: '#eef1f6' } } },
    series: [
      { name: '药明H 5日', type: 'bar', data: mk(DATA.events.map(e => e.wuxi)), color: '#c0392b' },
      { name: 'IBB 5日', type: 'bar', data: mk(DATA.events.map(e => e.ibb)), color: '#5b9bd5' },
      { name: 'XBI 5日', type: 'bar', data: mk(DATA.events.map(e => e.xbi)), color: '#ed7d31' }
    ]
  });
})();
</script>
</body>
</html>
"""

out_path = os.path.join(OUT_DIR, "wuxi_bigpharma_report.html")
html = html.replace("__PAIR_TBL__", pair_tbl_rows)
html = html.replace("__EXCESS_TBL__", excess_tbl_rows)
html = html.replace("__AH_PRE__", f"{ah_pre:.2f}")
html = html.replace("__AH_POST__", f"{ah_post:.2f}")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", out_path)

# JS 语法自检
import subprocess, tempfile, re
scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
for i, s in enumerate(scripts):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
        tf.write("const echarts = {init: () => ({setOption: () => {}})};\n" + s)
        jsp = tf.name
    r = subprocess.run(["/Users/alberthuang/.workbuddy/binaries/node/versions/22.22.2/bin/node", "--check", jsp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"JS SYNTAX ERROR in script {i}:\n{r.stderr[:2000]}")
    else:
        print(f"script {i}: node --check OK")
    os.unlink(jsp)
