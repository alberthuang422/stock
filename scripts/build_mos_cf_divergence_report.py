# -*- coding: utf-8 -*-
"""59 MOS vs CF 走势分化研报构建：读 results/mos_cf_divergence.json → 注入 ECharts → HTML。"""
import json
import os
import re as _re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "results", "mos_cf_divergence.json"), encoding="utf-8"))
OUT_DIR = os.path.join(ROOT, "reports", "59_MOS与CF化肥走势分化")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 基本面数据（来源：agentic_search / westock-data，见页脚来源区） ----------
QUARTERS = ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]
CF_Q = {  # 百万美元
    "rev":  [1663, 1890, 1659, 1872, 1986, 2222],
    "ni":   [312, 386, 353, 404, 615, 727],
    "gm":   [40.7, 44.8, 42.3, 41.1, 43.2, 54.4],
}
MOS_Q = {  # 百万美元
    "rev":  [2621, 3006, 3452, 2974, 2998, 2824],
    "ni":   [238, 411, 411, -520, -258, -273],
    "gm":   [18.6, 17.3, 16.0, 11.5, 7.9, 7.6],
}
PERF = DATA["perf_pct"]
PERF_WINDOWS = ["1M", "3M", "6M", "YTD2026", "12M", "2Y", "5Y"]
WIN_LABEL = {"1M": "近1月", "3M": "近3月", "6M": "近6月", "YTD2026": "2026年初至今", "12M": "近12月", "2Y": "近2年", "5Y": "近5年"}
TICKERS = ["CF", "MOS", "NTR", "DAR", "XLE", "SPY"]
TK_NAME = {
    "CF": "CF Industries（氮肥）", "MOS": "Mosaic（磷肥+钾肥）", "NTR": "Nutrien（综合）",
    "DAR": "Darling（动物油脂）", "XLE": "能源ETF", "SPY": "标普500",
}

DATA_BLOB = {
    "as_of": DATA["as_of"],
    "norm2023": {k: {"d": list(v.keys()), "v": [round(x, 2) for x in v.values()]} for k, v in DATA["norm_2023"].items()},
    "roll_corr": {"d": list(DATA["roll_corr_cf_mos"].keys()), "v": [round(x, 3) for x in DATA["roll_corr_cf_mos"].values()]},
    "ratio": {"d": list(DATA["ratio_mos_cf_norm"].keys()), "v": [round(x, 4) for x in DATA["ratio_mos_cf_norm"].values()]},
    "perf": PERF,
    "quarters": QUARTERS,
    "cf_q": CF_Q,
    "mos_q": MOS_Q,
}

# ---------- 表格：多窗口涨跌幅 ----------
def fmt_pct(x):
    if x is None:
        return "—"
    cls = "up" if x > 0 else ("dn" if x < 0 else "")
    sign = "+" if x > 0 else ""
    return f'<span class="{cls}">{sign}{x:.1f}%</span>'

perf_rows = ""
for tk in TICKERS:
    cells = "".join(f"<td>{fmt_pct(PERF[tk][w])}</td>" for w in PERF_WINDOWS)
    perf_rows += f'<tr><td class="tk"><b>{tk}</b><br><span class="sub">{TK_NAME[tk]}</span></td>{cells}</tr>'

# ---------- 表格：季度财务对比 ----------
fin_rows = ""
for i, q in enumerate(QUARTERS):
    cf_yoy = ""
    mos_yoy = ""
    if i >= 4:
        cf_yoy = f'（同比 {(CF_Q["ni"][i]/CF_Q["ni"][i-4]-1)*100:+.0f}%）'
        mos_yoy = "（转亏）" if MOS_Q["ni"][i] < 0 < MOS_Q["ni"][i-4] else ""
    fin_rows += f"""<tr>
      <td>{q}</td>
      <td>{CF_Q['rev'][i]:,}</td><td class="{'up' if CF_Q['ni'][i]>0 else 'dn'}">{CF_Q['ni'][i]:,}{cf_yoy}</td><td>{CF_Q['gm'][i]:.1f}%</td>
      <td>{MOS_Q['rev'][i]:,}</td><td class="{'up' if MOS_Q['ni'][i]>0 else 'dn'}">{MOS_Q['ni'][i]:,}{mos_yoy}</td><td>{MOS_Q['gm'][i]:.1f}%</td>
    </tr>"""

# ---------- 相关性矩阵表（60D） ----------
C60 = DATA["corr"]["60D"]
corr_head = "".join(f"<th>{t}</th>" for t in TICKERS)
corr_rows = ""
for a in TICKERS:
    cells = ""
    for b in TICKERS:
        v = C60[a][b]
        hot = ' class="hot"' if (a in ("CF", "MOS") and b in ("CF", "MOS") and a != b) else ""
        cells += f"<td{hot}>{v:.2f}</td>"
    corr_rows += f"<tr><td class='tk'><b>{a}</b></td>{cells}</tr>"

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MOS vs CF：都是化肥股，走势为何差这么大？</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --up:#c0392b; --dn:#1e8449; --ink:#2c3e50; --muted:#7f8c8d; --line:#e3e7ea; --bg:#f7f8fa; --card:#ffffff; --accent:#c0392b; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); line-height:1.75; }
  .wrap { max-width:1080px; margin:0 auto; padding:28px 20px 60px; }
  header { border-bottom:3px solid var(--accent); padding-bottom:14px; margin-bottom:22px; }
  header h1 { font-size:26px; letter-spacing:.5px; }
  header .meta { color:var(--muted); font-size:13px; margin-top:6px; }
  h2 { font-size:19px; margin:34px 0 12px; padding-left:10px; border-left:4px solid var(--accent); }
  h3 { font-size:15.5px; margin:18px 0 8px; }
  p { margin:8px 0; font-size:14.5px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px; margin:12px 0; }
  .tldr { background:#fff6f4; border:1px solid #f3c8c0; }
  .tldr h2 { border:none; padding:0; margin:0 0 8px; font-size:17px; color:var(--accent); }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin:14px 0 4px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 12px; }
  .kpi .lab { font-size:12px; color:var(--muted); }
  .kpi .val { font-size:21px; font-weight:700; margin-top:2px; }
  .up { color:var(--up); font-weight:600; }
  .dn { color:var(--dn); font-weight:600; }
  .sub { color:var(--muted); font-size:12px; font-weight:400; }
  table { width:100%; border-collapse:collapse; font-size:13.5px; background:var(--card); }
  th, td { border:1px solid var(--line); padding:7px 9px; text-align:center; }
  th { background:#f0f3f6; font-weight:600; }
  td.tk { text-align:left; white-space:nowrap; }
  td.hot { background:#fff0ed; font-weight:700; color:var(--accent); }
  .chart { width:100%; height:400px; }
  .chart-sm { width:100%; height:340px; }
  .note { font-size:12.5px; color:var(--muted); margin-top:6px; }
  .vs { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
  @media (max-width:760px){ .vs{grid-template-columns:1fr;} }
  .biz { border-radius:10px; padding:16px 18px; border:1px solid var(--line); }
  .biz.cf { background:#fdf3f2; border-color:#eecccc; }
  .biz.mos { background:#f0f7f1; border-color:#cfe3d2; }
  .biz h3 { margin-top:0; }
  .biz ul { margin:8px 0 0 18px; font-size:14px; }
  .biz li { margin:5px 0; }
  .chain { display:flex; align-items:stretch; gap:8px; flex-wrap:wrap; margin:10px 0; }
  .chain .node { flex:1 1 150px; background:var(--card); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-size:13.5px; text-align:center; }
  .chain .arrow { align-self:center; color:var(--muted); font-size:18px; }
  .node.bad { background:#fdf3f2; border-color:#eecccc; }
  .node.good { background:#f0f7f1; border-color:#cfe3d2; }
  .term { border-bottom:1px dashed #b08; cursor:help; }
  .termtip { display:none; position:fixed; z-index:99; max-width:300px; background:#2c3e50; color:#fff; font-size:12.5px; line-height:1.6; padding:8px 10px; border-radius:6px; box-shadow:0 4px 14px rgba(0,0,0,.25); pointer-events:none; }
  .src { font-size:12.5px; color:var(--muted); }
  .src li { margin:4px 0 4px 18px; }
  footer { margin-top:40px; padding-top:14px; border-top:1px solid var(--line); font-size:12.5px; color:var(--muted); }
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>MOS vs CF：都是化肥股，走势为什么差这么大？</h1>
  <div class="meta">股票分析 · 59 号报告 ｜ 行情截至 2026-08-27 收盘（本地 Yahoo 复权日线）；财务数据截至 2026Q2 ｜ 生成于 2026-08-30</div>
</header>

<div class="card tldr">
  <h2>结论先行</h2>
  <p><b>MOS 和 CF 名义上都叫"化肥股"，但它们是两门完全不同的生意。</b>CF 是纯玩家，用美国本土廉价天然气造氮肥（合成氨/尿素），卖全球价；MOS 主做磷肥+钾肥，必须外购硫磺做原料、且近四成收入押在巴西。<b>2026 年 2 月底美以伊冲突、3 月 2 日伊朗封锁霍尔木兹海峡，对两者构成方向相反的冲击</b>：全球约 1/3 海运化肥、近一半硫磺贸易经此海峡——尿素价格暴涨（新奥尔良港一度 +44%）让 CF 吃到"产品涨价、成本不动"的稀缺溢价；硫磺从每吨 150–180 美元飙到 850–900 美元，则把 MOS 的磷肥业务直接打进亏损（"每吨亏钱"）。于是 2026 年至今 CF 大涨、MOS 原地踏步还一度腰斩，两者 60 日滚动相关性已跌到 0.26——走势脱钩不是市场错了，是基本面本来就是反着走的。</p>
  <div class="kpis">
    <div class="kpi"><div class="lab">CF · 2026 年初至今</div><div class="val up">+64.9%</div></div>
    <div class="kpi"><div class="lab">MOS · 2026 年初至今</div><div class="val">+0.5%</div></div>
    <div class="kpi"><div class="lab">近 12 月 CF vs MOS</div><div class="val"><span class="up">+48.1%</span> / <span class="dn">−26.1%</span></div></div>
    <div class="kpi"><div class="lab">60 日滚动相关性（CF×MOS）</div><div class="val">0.26</div></div>
    <div class="kpi"><div class="lab">CF 2026Q2 净利（同比）</div><div class="val up">7.27 亿美元（+88%）</div></div>
    <div class="kpi"><div class="lab">MOS 连续亏损</div><div class="val dn">3 个季度</div></div>
  </div>
</div>

<h2>一、走势对比：一条海峡，剪出两个方向</h2>
<div class="card">
  <div id="c_price" class="chart"></div>
  <div class="note">归一化：2023-01 首个交易日=100。竖线：2026-02-28 美以伊冲突爆发（"Operation Epic Fury"），03-02 伊朗封锁霍尔木兹海峡。参数：本地 Yahoo 复权收盘价，2023-01 ~ 2026-08-27。</div>
</div>
<p>2025 年上半年之前，CF 和 MOS 大体还是同涨同跌的"化肥兄弟"。真正的分水岭在 <b>2026 年 2 月末</b>：冲突爆发后 12 天内化肥价格普涨约 30%，但随后市场迅速给两家公司重新定价——CF 在 3 月单月暴涨约 30%、3 月 30 日创下 140.66 美元历史新高；MOS 则在 2025-10（单月约 −12%）和 2026-03（约 −19.5%）两度重挫，2026 年一度跌至 52 周低点 19.80 美元。到 8 月底，CF 2026 年涨幅 +64.9%，MOS 只有 +0.5%（行情口径：本地日线至 08-27；westock 08-28 收盘 CF 125.79 / MOS 23.60）。</p>

<div class="card">
  <div id="c_perf" class="chart-sm"></div>
  <div class="note">多窗口涨跌幅（%），基于复权收盘价。参数：窗口=21/63/126/252/504/1260 交易日，YTD 以 2025 年最后一个交易日为基期。</div>
</div>

<div class="card" style="overflow-x:auto;">
  <table>
    <tr><th>标的</th><th>近1月</th><th>近3月</th><th>近6月</th><th>2026年初至今</th><th>近12月</th><th>近2年</th><th>近5年</th></tr>
    __PERF_ROWS__
  </table>
  <div class="note">涨跌幅=区间复权价变动。值得注意的是拉长到 5 年：CF +222% vs MOS −9%——分化并非 2026 年才有，但霍尔木兹危机把剪刀差急剧拉大。DAR（动物油脂/生物柴油链）同期 +57% 是农业链另一条独立主线。</div>
</div>

<h2>二、业务本质：氮与磷，成本与市场的三重不同</h2>
<div class="vs">
  <div class="biz cf">
    <h3>CF Industries（CF）—— 氮肥纯玩家</h3>
    <ul>
      <li><b>产品</b>：合成氨（产能约 1085 万吨，全球第一）、尿素、UAN、硝酸铵——全是氮肥</li>
      <li><b>原料</b>：天然气（制氨的氢源），全部来自美国/加拿大本土，Henry Hub 气价区域定价、冲突后仅小幅上行</li>
      <li><b>市场</b>：2025 年北美收入占约 85%，中东断供后全球买家抢非中东货源，CF 坐收稀缺溢价</li>
      <li><b>冲击性质</b>：产品涨价 ↑↑，成本几乎不动 → 利润剪刀差扩张</li>
    </ul>
  </div>
  <div class="biz mos">
    <h3>Mosaic（MOS）—— 磷肥+钾肥</h3>
    <ul>
      <li><b>产品</b>：磷肥（2025 年营收占 32%）+ 钾肥（22%）+ 巴西化肥分销（40%，最大单一业务）</li>
      <li><b>原料</b>：磷肥必须用硫磺制磷酸——全球约一半海运硫磺经霍尔木兹海峡，MOS 是硫磺净买家</li>
      <li><b>市场</b>：巴西占营收近 39%，正遭遇信贷紧缩+中国低价磷肥进口冲击，2026Q1 已计提 4.42 亿美元巴西矿山减值</li>
      <li><b>冲击性质</b>：原料成本暴涨 ↑↑↑，而磷肥可被农民减量（需求弹性大）→ 两头挤压</li>
    </ul>
  </div>
</div>

<h2>三、传导链：同一场危机，一边是红利、一边是成本</h2>
<div class="card">
  <div class="chain">
    <div class="node">2026-02-28 美以伊冲突爆发</div>
    <div class="arrow">→</div>
    <div class="node">03-02 伊朗封锁霍尔木兹海峡<br><span class="sub">≈1/3 海运化肥、44% 尿素、近半硫磺经此</span></div>
    <div class="arrow">→</div>
    <div class="node">全球供给冲击</div>
  </div>
  <div class="chain">
    <div class="node good">尿素 12 天涨约 30%<br>新奥尔良港 $475→峰值 $683/吨（高盛口径累计 +50~70%）</div>
    <div class="arrow">→</div>
    <div class="node good"><b>CF 受益</b>：按全球高价卖、用便宜美国气生产；2026Q2 毛利率 54.4%（+12pp），净利 +88%</div>
  </div>
  <div class="chain">
    <div class="node bad">硫磺 $150–180 → $850–900/吨（部分到岸近 $1000）<br>+ 外购氨同步昂贵</div>
    <div class="arrow">→</div>
    <div class="node bad"><b>MOS 受损</b>：磷肥吨毛利转负（2026Q2 约 −4 美元/吨），巴西矿减产关停，连亏 3 季</div>
  </div>
  <div class="note">事件与价格来源：高盛 2026-04-14 研报（腾讯新闻转述）、财联社 2026-05-25（Hexagon/CRU 口径）、Benzinga 2026-03、公开报道 2026-06——均为非一手来源，需核实原文。需求端同样不对称：氮肥是玉米等作物的"刚需"，磷/钾肥价高时农民可减量；叠加美国玉米价跌至约 $4.5/蒲式耳（2022 年高点 $7–8），农民购买力下降进一步压制 MOS 的定价能力。</div>
</div>

<h2>四、业绩对照：利润表把剪刀差写在了明面上</h2>
<div class="card">
  <div id="c_fin" class="chart"></div>
  <div class="note">柱=单季净利润（百万美元，左轴），线=毛利率（%，右轴）。来源：westock-data 季度财务数据，2025Q1–2026Q2，美元。</div>
</div>
<div class="card" style="overflow-x:auto;">
  <table>
    <tr>
      <th rowspan="2">季度</th><th colspan="3">CF Industries</th><th colspan="3">Mosaic</th>
    </tr>
    <tr><th>营收</th><th>净利润</th><th>毛利率</th><th>营收</th><th>净利润</th><th>毛利率</th></tr>
    __FIN_ROWS__
  </table>
  <div class="note">单位：百万美元。来源：westock-data 季度财务（2025Q1–2026Q2）。CF 净利率从 18.8% 一路升到 32.7%；MOS 毛利率从 18.6% 崩到 7.6%，2025Q4 起连续三季亏损（含巴西矿山减值等非现金项目）。</div>
</div>

<h2>五、定量视角：它们已经不再是"同一只股票"了</h2>
<div class="card">
  <div id="c_corr" class="chart-sm"></div>
  <div class="note">CF×MOS 60 日滚动相关系数（日收益率口径，2024-06 起）。参数：滚动窗口=60 交易日。2026 年 3 月起相关性持续走低、多次贴近 0——两票价格驱动因子已实质性分离。</div>
</div>
<div class="vs">
  <div class="card" style="margin:0;">
    <h3>60 日相关系数矩阵（日收益率）</h3>
    <table>
      <tr><th></th>__CORR_HEAD__</tr>
      __CORR_ROWS__
    </table>
    <div class="note">窗口=最近 60 交易日。CF×MOS 仅 0.26（126 日 0.27、252 日 0.40）；CF 与 NTR（同为氮肥链）0.67，与 XLE 0.56。MOS 与谁都不太相关——它的驱动是硫磺成本与巴西，自有逻辑。</div>
  </div>
  <div class="card" style="margin:0;">
    <div id="c_ratio" class="chart-sm"></div>
    <div class="note">MOS/CF 相对强弱比（2024-01 首个交易日=1）。曲线一路向南=CF 持续跑赢：2024 年初以来该比值跌去约 60%，即 MOS 相对 CF 的比价创出多年新低。</div>
  </div>
</div>
<div class="kpis">
  <div class="kpi"><div class="lab">60 日年化波动率 CF / MOS</div><div class="val">37.4% / 47.4%</div></div>
  <div class="kpi"><div class="lab">2025 年以来最大回撤 CF / MOS</div><div class="val"><span class="dn">−29.2%</span> / <span class="dn">−45.7%</span></div></div>
  <div class="kpi"><div class="lab">最新价（08-27 收盘）</div><div class="val">CF $125.71 · MOS $23.76</div></div>
  <div class="kpi"><div class="lab">PE(TTM) / PB（08-28，westock）</div><div class="val">CF 9.3 / 3.3 · MOS 亏损 / 0.65</div></div>
</div>
<div class="note">参数：年化波动率=60 日日收益标准差×√252；最大回撤区间 2025-01-01 起。估值快照：westock 行情 2026-08-28（CF 市值约 190 亿美元、股息率 1.67%；MOS 市值约 75 亿美元、股息率 3.73%）。</div>

<h2>六、往后看什么</h2>
<p><b>CF 的命门是"地缘溢价能维持多久"</b>：美伊已达成初步停战协议，但航运恢复以月计、被毁基础设施重建以年计（北达科他州立大学农业经济学家 Shawn Arita 判断溢价完全消退"更像 2028 年的故事"，转引自公开报道、需核实原文）。若海峡快速复航、尿素价格回落，CF 当前利润中枢会下修——华泰研究 2026-06-09 首评给 195.72 美元目标价（14× 2026E PE，需核实原文），隐含的正是"2–3 年高景气"假设。<b>MOS 的看点在"成本见顶后的修复弹性"</b>：钾肥分部仍稳定盈利（2026Q2 营业利润 1.95 亿美元），若硫磺价格随复航回落、巴西需求企稳，0.65 倍 PB 的估值有修复空间；但资产负债表承压（长期债务约 49 亿美元、2026Q2 自由现金流 −1.5 亿美元），修复节奏存疑。一句话：<b>CF 赌的是"稀缺持续"，MOS 赌的是"成本回落"，两个赌注互斥——这就是走势背离的根源。</b></p>

<h2>来源与时点</h2>
<ul class="src">
  <li>行情/归一化/相关性：本地 Yahoo 复权日线（data/cf、data/mos 等，截至 2026-08-27 收盘）</li>
  <li>季度财务：westock-data（CF/MOS，2025Q1–2026Q2，美元）</li>
  <li>估值/市值快照：westock 行情，2026-08-28</li>
  <li>事件与商品价格：高盛研报 2026-04-14（腾讯新闻转述）、财联社 2026-05-25、Benzinga 2026-03-16、公开报道 2026-06-16、华泰研究 2026-06-09 —— 均为非一手来源，需核实原文</li>
</ul>

<footer>
  免责声明：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
</footer>
</div>

<div class="termtip" id="termtip"></div>
<script>
const DATA = __DATA__;
const UP='#c0392b', DN='#1e8449';
const TKN={CF:'CF',MOS:'MOS',NTR:'NTR',DAR:'DAR',XLE:'XLE',SPY:'SPY'};
const COLORS={CF:UP,MOS:DN,NTR:'#e69f00',DAR:'#0072B2',XLE:'#8c6d31',SPY:'#666666'};

function mkAxis(){return {axisLine:{lineStyle:{color:'#b8c2cc'}},axisLabel:{color:'#5a6b7b'},splitLine:{lineStyle:{color:'#eef1f4'}}};}

/* 图1：归一化价格 */
(function(){
  const el=document.getElementById('c_price'); if(!el) return;
  const ds=DATA.norm2023;
  const dates=ds.CF.d;
  const series=['CF','MOS','NTR','DAR','XLE','SPY'].map(function(tk){
    return {name:tk,type:'line',showSymbol:false,data:ds[tk].v,lineStyle:{width:tk==='CF'||tk==='MOS'?2.4:1.2,type:(tk==='SPY')?'dashed':'solid'},itemStyle:{color:COLORS[tk]}};
  });
  let idx=-1;
  for(let i=0;i<dates.length;i++){ if(dates[i]>='2026-02-28'){ idx=i; break; } }
  if(idx>=0){
    series[0].markLine={symbol:'none',label:{formatter:'2026-02-28 冲突爆发 → 03-02 海峡封锁',color:'#c0392b',fontSize:11},lineStyle:{color:'#c0392b',type:'dashed'},data:[{xAxis:idx}]};
    series[0].markPoint={symbolSize:1,label:{show:true,formatter:'CF 历史新高',color:'#c0392b',fontSize:11,offset:[0,-8]},data:[{type:'max',name:'CF峰值'}]};
  }
  echarts.init(el).setOption({
    tooltip:{trigger:'axis',valueFormatter:function(v){return v==null?'—':(+v).toFixed(1);}},
    legend:{data:['CF','MOS','NTR','DAR','XLE','SPY'],top:0},
    grid:{left:52,right:18,top:36,bottom:54},
    xAxis:Object.assign({type:'category',data:dates},mkAxis()),
    yAxis:Object.assign({type:'value',name:'2023-01=100',scale:true},mkAxis()),
    dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:12}],
    series:series
  });
})();

/* 图2：多窗口涨跌幅 */
(function(){
  const el=document.getElementById('c_perf'); if(!el) return;
  const wins=['1M','3M','6M','YTD2026','12M','2Y','5Y'];
  const wl=['近1月','近3月','近6月','2026 YTD','近12月','近2年','近5年'];
  const tks=['CF','MOS','NTR','DAR','XLE','SPY'];
  const series=tks.map(function(tk){
    return {name:tk,type:'bar',data:wins.map(function(w){return DATA.perf[tk][w];}),itemStyle:{color:COLORS[tk]},barMaxWidth:16};
  });
  echarts.init(el).setOption({
    tooltip:{trigger:'axis',valueFormatter:function(v){return v==null?'—':(+v).toFixed(1)+'%';}},
    legend:{data:tks,top:0},
    grid:{left:52,right:18,top:36,bottom:30},
    xAxis:Object.assign({type:'category',data:wl},mkAxis()),
    yAxis:Object.assign({type:'value',name:'%'},mkAxis()),
    series:series
  });
})();

/* 图3：季度净利润 + 毛利率 */
(function(){
  const el=document.getElementById('c_fin'); if(!el) return;
  const q=DATA.quarters;
  echarts.init(el).setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['CF 净利润','MOS 净利润','CF 毛利率','MOS 毛利率'],top:0},
    grid:{left:60,right:56,top:40,bottom:30},
    xAxis:Object.assign({type:'category',data:q},mkAxis()),
    yAxis:[
      Object.assign({type:'value',name:'净利润(百万$)'},mkAxis()),
      Object.assign({type:'value',name:'毛利率(%)',min:0,max:60,splitLine:{show:false}},mkAxis())
    ],
    series:[
      {name:'CF 净利润',type:'bar',data:DATA.cf_q.ni,itemStyle:{color:UP},barMaxWidth:26},
      {name:'MOS 净利润',type:'bar',data:DATA.mos_q.ni,itemStyle:{color:DN},barMaxWidth:26},
      {name:'CF 毛利率',type:'line',yAxisIndex:1,data:DATA.cf_q.gm,lineStyle:{color:UP,type:'dashed',width:2},itemStyle:{color:UP},symbol:'circle',symbolSize:6},
      {name:'MOS 毛利率',type:'line',yAxisIndex:1,data:DATA.mos_q.gm,lineStyle:{color:DN,type:'dashed',width:2},itemStyle:{color:DN},symbol:'circle',symbolSize:6}
    ]
  });
})();

/* 图4：60 日滚动相关性 */
(function(){
  const el=document.getElementById('c_corr'); if(!el) return;
  echarts.init(el).setOption({
    tooltip:{trigger:'axis',valueFormatter:function(v){return v==null?'—':(+v).toFixed(2);}},
    grid:{left:52,right:18,top:26,bottom:50},
    xAxis:Object.assign({type:'category',data:DATA.roll_corr.d},mkAxis()),
    yAxis:Object.assign({type:'value',name:'相关系数',min:-1,max:1},mkAxis()),
    dataZoom:[{type:'inside'}],
    series:[{
      name:'CF×MOS 60日滚动相关',type:'line',showSymbol:false,data:DATA.roll_corr.v,
      lineStyle:{color:'#7b4ea3',width:2},itemStyle:{color:'#7b4ea3'},
      markLine:{symbol:'none',label:{show:false},lineStyle:{color:'#999',type:'dotted'},data:[{yAxis:0}]}
    }]
  });
})();

/* 图5：MOS/CF 相对强弱 */
(function(){
  const el=document.getElementById('c_ratio'); if(!el) return;
  echarts.init(el).setOption({
    title:{text:'MOS/CF 相对强弱比',left:'center',textStyle:{fontSize:13,color:'#2c3e50'}},
    tooltip:{trigger:'axis',valueFormatter:function(v){return v==null?'—':(+v).toFixed(3);}},
    grid:{left:52,right:18,top:40,bottom:30},
    xAxis:Object.assign({type:'category',data:DATA.ratio.d},mkAxis()),
    yAxis:Object.assign({type:'value',name:'2024-01=1',scale:true},mkAxis()),
    series:[{name:'MOS/CF',type:'line',showSymbol:false,data:DATA.ratio.v,lineStyle:{color:'#0072B2',width:2},itemStyle:{color:'#0072B2'},areaStyle:{color:'rgba(0,114,178,0.06)'}}]
  });
})();

window.addEventListener('resize',function(){
  ['c_price','c_perf','c_fin','c_corr','c_ratio'].forEach(function(id){
    const el=document.getElementById(id);
    if(el && el.__ec){ el.__ec.resize(); }
  });
});
</script>
<script>
(function(){
  const tip=document.getElementById('termtip');
  let cur=null;
  document.addEventListener('mouseover',e=>{
    const t=e.target.closest('.term');
    if(!t||t===cur)return; cur=t;
    tip.textContent=t.dataset.tip||'';
    tip.style.display='block';
    const r=t.getBoundingClientRect();
    tip.style.left=Math.min(r.left,window.innerWidth-320)+'px';
    tip.style.top=r.bottom+6+'px';
  });
  document.addEventListener('mouseout',e=>{
    if(e.target.closest('.term')){cur=null;tip.style.display='none';}
  });
})();
</script>
</body>
</html>
"""

html = html.replace("__DATA__", json.dumps(DATA_BLOB, ensure_ascii=False))
html = html.replace("__PERF_ROWS__", perf_rows)
html = html.replace("__FIN_ROWS__", fin_rows)
html = html.replace("__CORR_HEAD__", corr_head)
html = html.replace("__CORR_ROWS__", corr_rows)

# ---------- 术语悬停浮窗 ----------
TERMS = [
    ("氮肥", "以氮元素为核心的肥料（尿素、合成氨、UAN、硝酸铵等），玉米等作物追肥刚需，价格弹性小。CF 是纯氮肥玩家。"),
    ("磷肥", "以磷元素为核心的肥料（DAP 磷酸二铵、MAP 等），生产需用硫磺制磷酸；价高时农民可减量，需求弹性大于氮肥。"),
    ("钾肥", "以钾元素为核心的肥料（氯化钾等），MOS 唯一稳定盈利的分部，不受硫磺成本影响。"),
    ("霍尔木兹海峡", "波斯湾出口咽喉。全球约 1/3 海运化肥、43–44% 尿素、近一半硫磺、15–20% 贸易氨经此运输；2026-03-02 起被伊朗封锁。"),
    ("尿素", "用量最大的氮肥。新奥尔良港价格冲突前约 $475/吨，冲突后峰值 $683（+44%），高盛口径累计 +50–70%。"),
    ("合成氨", "尿素等氮肥的中间体，由天然气制取。CF 合成氨产能约 1085 万吨，全球第一。"),
    ("UAN", "尿素硝酸铵溶液，液态氮肥，美国大田主流追肥品种之一，CF 主力产品。"),
    ("DAP", "磷酸二铵，主流磷肥品种。冲突后巴西/印度到岸价一度升至 $930–935/吨（印度招标，2022 年 7 月以来最高）。"),
    ("硫磺", "制磷酸的必需原料。全球约一半海运硫磺经霍尔木兹海峡；价格从 $150–180/吨飙至 $850–900/吨（部分到岸近 $1000）。"),
    ("Henry Hub", "美国天然气定价基准。美国气价区域定价，冲突后仅小幅上行，与欧洲/亚洲气价暴涨形成对比——这是 CF 成本优势的来源。"),
    ("归一化", "把各标的期初价格设为 100，之后按涨跌幅换算，便于不同价位股票同图比较。"),
    ("滚动相关", "在固定窗口（本报告 60 交易日）内逐日计算的日收益率相关系数，反映两标的近期同涨同跌程度；0.26 属弱相关。"),
    ("年化波动率", "日收益率标准差×√252，衡量近期价格波动大小。"),
    ("最大回撤", "从区间内峰值到其后最低点的最大跌幅，衡量持有期间的最坏体验。"),
    ("PE", "市盈率=股价/每股收益。TTM 指最近 4 个季度滚动。MOS 因 TTM 亏损，PE 为负、无意义，改用 PB（市净率）看估值。"),
    ("稀缺溢价", "供给中断时，买家为锁定非中断区货源愿意多付的价差。CF 位于北美、不受海峡影响，直接吃到这份溢价。"),
    ("YTD", "Year-To-Date，年初至今涨跌幅。"),
]
TERM_DICT = {k: v for k, v in sorted(TERMS, key=lambda x: -len(x[0]))}
_BLOCK_RE = _re.compile(r"(<script[\s\S]*?</script>|<style[\s\S]*?</style>|<title[\s\S]*?</title>)", _re.S)

def _annotate_text(seg):
    # 单次扫描 + 回调替换，避免已插入 span 的属性文本被二次替换（嵌套污染）
    pat = _re.compile("|".join(_re.escape(k) for k in TERM_DICT))
    return pat.sub(lambda m: f'<span class="term" data-tip="{TERM_DICT[m.group(0)]}">{m.group(0)}</span>', seg)

parts = _BLOCK_RE.split(html)
html = "".join((_annotate_text(seg) if (i % 2 == 0 and seg) else (seg or "")) for i, seg in enumerate(parts))

out_path = os.path.join(OUT_DIR, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("WROTE", out_path, len(html), "chars")
