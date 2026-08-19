# -*- coding: utf-8 -*-
"""SOFI × Block(XYZ) × AFRM 财报对比 + US10Y 敏感性 —— 研报生成
读取 results/sofi_xyz_afrm_analysis.json + 硬编码财报数据（来源：各公司 2026-07/08 财报）
输出 reports/sofi_xyz_afrm_report.html
"""
import json

ANALYSIS = json.load(open("/Users/alberthuang/Desktop/股票分析/results/sofi_xyz_afrm_analysis.json", encoding="utf-8"))
OUT = "/Users/alberthuang/Desktop/股票分析/reports/sofi_xyz_afrm_report.html"

# ============ 基本面数据（最新已发季报；来源见表格注释） ============
FUND = {
    "SOFI": {
        "ticker": "SOFI", "name": "SoFi Technologies", "tag": "数字银行 · 个人贷款 · 全能金融App",
        "quarter": "2026 Q2（截至 6/30，7/29 发布）",
        "rev": 1218.7, "rev_yoy": 43.0, "rev_note": "总净营收 $12.19 亿",
        "gp": None, "gp_yoy": None,
        "key_growth": [("净利息收入", "+52%", "$7.88 亿"), ("费用类收入", "+38%", "交易/经纪/技术平台费"),
                       ("会员数", "+35%", "1580 万，单季新增 110 万"), ("产品渗透率", "51%", "会员购买 ≥2 产品比例（上年 35%）")],
        "ni": 156.6, "ni_yoy": 61.0, "eps": 0.12, "ni_margin": 12.8,
        "adj_margin": None, "adj_note": "调整后净利率 ~13%",
        "bs": {"负债率": "81.8%", "存款": "$455 亿（低成本资金）", "流动性": "速动 3.93（银行口径）"},
        "credit": "个人贷/学生贷/房贷发放量创纪录；扩展至小企业贷与房屋净值贷；管理层称信用表现良好",
        "cashflow": "银行模式，存款驱动的资产负债结构；Q2 新增存款支撑贷款扩张",
        "ps": 4.9, "mktcap": 23.6,
    },
    "XYZ": {
        "ticker": "XYZ", "name": "Block (原 Square)", "tag": "Square 商户收单 · Cash App 消费者 · Afterpay BNPL · 比特币",
        "quarter": "2026 Q2（截至 6/30，8/5 发布）",
        "rev": 6617.7, "rev_yoy": 9.3, "rev_note": "总营收 $66.18 亿（比特币收入 -12.8% 拖累）",
        "gp": 3170.0, "gp_yoy": 25.0, "gp_note": "毛利润 $31.7 亿创纪录",
        "key_growth": [("Cash App 毛利润", "+31%", "$19.7 亿"), ("Square 毛利润", "+13%", "$11.6 亿"),
                       ("Cash App 消费贷发放", "+59%", "$189 亿"), ("Square GPV", "+13.4%", "$728 亿，美国增速三年最高")],
        "ni": 88.5, "ni_yoy": -83.6, "eps": 0.15, "ni_margin": 1.3,
        "adj_margin": 27.0, "adj_note": "调整后经营利润率 27%（历史新高）；调整后经营利润 $8.64 亿 +57%；调整后 EPS $1.02 +65%",
        "bs": {"负债率": "43.8%", "现金类": "$88 亿流动性（其中现金 $79 亿）", "回购": "2026 年以来回购 1160 万股，剩余授权 $46 亿"},
        "credit": "贷款损失同比 +99%（随发放量 +59% 翻倍）；管理层称 cohort 损失率健康，短期 6 周产品为主",
        "cashflow": "Q2 经营现金流 $10.2 亿、自由现金流 $9.67 亿；持续正向",
        "ps": 1.9, "mktcap": 49.8,
    },
    "AFRM": {
        "ticker": "AFRM", "name": "Affirm Holdings", "tag": "BNPL 先买后付纯玩家 · 0% APR + 利息型分期",
        "quarter": "FY2026 Q3（截至 3/31，5/7 发布；Q4 8/27 待发）",
        "rev": 1038.8, "rev_yoy": 33.0, "rev_note": "总营收 $10.39 亿；GMV $116 亿 +35%（连续 10 季 30%+）",
        "gp": None, "gp_yoy": None,
        "key_growth": [("GMV", "+35%", "$116 亿，10 连季 >30%"), ("RLTC", "+41%", "$4.98 亿，占 GMV 4.3%"),
                       ("Affirm Card GMV", "+146%", "$21 亿，活跃卡户 440 万（翻倍）"), ("活跃商户", "+44%", "51.5 万家")],
        "ni": 102.9, "ni_yoy": None, "eps": 0.30, "ni_margin": 9.9,
        "adj_margin": 27.0, "adj_note": "调整后经营利润率 27%（上年 22%）；调整后经营利润 $2.81 亿 +62%",
        "bs": {"融资能力": "$282 亿（可支撑 >$650 亿 GMV）", "资金成本": "5.8%（同比 -126bp，三年半最低）",
               "证券化": "ABS + 债务融资为主，3 笔年度融资均超募"},
        "credit": "30+ 天逾期（月付 ex-Peloton）2.8% 稳定；拨备/贷款 6.0%；预付款上升（报税季季节性）",
        "cashflow": "自营贷款 (RLTC) 模式；融资依赖资本市场，成本随利率下行改善",
        "ps": 5.9, "mktcap": 24.8,
    },
}

# ============ 汇总表行 ============
def fmt(v, suffix=""):
    if v is None: return "—"
    return f"{v}{suffix}"

def fmt_ni_yoy(v):
    if v is None:
        return "上年仅$0.03B"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.0f}%"

rows_growth = []
for tk in ["SOFI", "XYZ", "AFRM"]:
    f = FUND[tk]
    rows_growth.append(
        f"<tr><td><b>{f['ticker']}</b> {f['name']}</td><td>{f['quarter']}</td>"
        f"<td class='up'>{f['rev']/100:.2f}B ({f['rev_yoy']:+.0f}%)</td>"
        f"<td>{fmt(f['gp']/100 if f['gp'] else None, 'B')}{(' (' + str(f['gp_yoy']) + '%)') if f['gp'] else ''}</td>"
        f"<td>{f['ni']/100:.2f}B ({fmt_ni_yoy(f['ni_yoy'])})</td>"
        f"<td>{f['eps']:.2f}</td><td>{f['ni_margin']:.1f}%</td></tr>")

rows_health = []
for tk in ["SOFI", "XYZ", "AFRM"]:
    f = FUND[tk]
    bs = "；".join(f"{k} {v}" for k, v in f["bs"].items())
    rows_health.append(
        f"<tr><td><b>{f['ticker']}</b></td><td>{f['adj_margin'] if f['adj_margin'] else '—'}%</td>"
        f"<td>{bs}</td><td>{f['credit']}</td><td>{f['cashflow']}</td></tr>")

# ============ JSON for 图表 ============
A = ANALYSIS
D = {
    "rev": [FUND[t]["rev"]/100 for t in ["SOFI","XYZ","AFRM"]],
    "rev_yoy": [FUND[t]["rev_yoy"] for t in ["SOFI","XYZ","AFRM"]],
    "labels": ["SOFI", "XYZ(Block)", "AFRM"],
    "nav_dates": A["annualized"]["SOFI"]["dates"],
    "nav_sofi": A["annualized"]["SOFI"]["nav"],
    "nav_xyz": A["annualized"]["XYZ"]["nav"],
    "nav_afrm": A["annualized"]["AFRM"]["nav"],
    "y10_dates": A["annualized"]["10Y"]["dates"],
    "y10_level": A["annualized"]["10Y"]["level"],
    "roll_dates": A["rolling"]["SOFI"]["dates"],
    "roll_sofi": A["rolling"]["SOFI"]["corr"],
    "roll_xyz": A["rolling"]["XYZ"]["corr"],
    "roll_afrm": A["rolling"]["AFRM"]["corr"],
    "beta_full": [A["windows"]["full"][t]["beta_pct_per_10bp"] for t in ["SOFI","XYZ","AFRM"]],
    "beta_1y": [A["windows"]["1y"][t]["beta_pct_per_10bp"] for t in ["SOFI","XYZ","AFRM"]],
    "corr_full": [A["windows"]["full"][t]["corr"] for t in ["SOFI","XYZ","AFRM"]],
    "corr_1y": [A["windows"]["1y"][t]["corr"] for t in ["SOFI","XYZ","AFRM"]],
    "mon_up": [A["monthly"]["up_months"][t] for t in ["SOFI","XYZ","AFRM"]],
    "mon_down": [A["monthly"]["down_months"][t] for t in ["SOFI","XYZ","AFRM"]],
    "mon_all": [A["monthly"]["all_months"][t] for t in ["SOFI","XYZ","AFRM"]],
    "mon_n": {"up": A["monthly"]["n_up"], "down": A["monthly"]["n_down"]},
    "lvl_keys": None,  # 从第一个有数据的 ticker 取
    "lvl_sofi": None, "lvl_xyz": None, "lvl_afrm": None,
    "big": A["big_moves"],
    "ps": [FUND[t]["ps"] for t in ["SOFI","XYZ","AFRM"]],
    "mktcap": [FUND[t]["mktcap"] for t in ["SOFI","XYZ","AFRM"]],
    "by_year": A["monthly"]["by_year"],
    "drawdown": A["drawdown"], "drawdown_1y": A["drawdown_1y"],
    "roll_avg": {t: A["rolling"][t]["avg"] for t in ["SOFI","XYZ","AFRM"]},
    "roll_last": {t: A["rolling"][t]["last"] for t in ["SOFI","XYZ","AFRM"]},
}
# 利率分档统一 key 顺序
lvl = A["level_buckets"]["SOFI"]
D["lvl_keys"] = list(lvl.keys())
D["lvl_sofi"] = [round(lvl[k]["avg_ret"]*100, 1) for k in D["lvl_keys"]]
D["lvl_xyz"] = [round(A["level_buckets"]["XYZ"][k]["avg_ret"]*100, 1) for k in D["lvl_keys"]]
D["lvl_afrm"] = [round(A["level_buckets"]["AFRM"][k]["avg_ret"]*100, 1) for k in D["lvl_keys"]]

by_year_labels = list(D["by_year"].keys())
by_year_y10 = [round(D["by_year"][y]["m10_chg"], 2) for y in by_year_labels]
by_year_sofi = [round(D["by_year"][y]["SOFI"], 1) for y in by_year_labels]
by_year_xyz = [round(D["by_year"][y]["XYZ"], 1) for y in by_year_labels]
by_year_afrm = [round(D["by_year"][y]["AFRM"], 1) for y in by_year_labels]

def js(o):
    return json.dumps(o, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SOFI × XYZ(Block) × AFRM 财报对比与 US10Y 敏感性 · 2026-08</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;--orange:#e8590c;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:19px;font-weight:700;}
  .kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);} .kpi .num.bl{color:var(--blue);} .kpi .num.pu{color:var(--purple);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  table{width:100%;border-collapse:collapse;font-size:12px;}
  th{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:5px 7px;border-bottom:1px solid #f0f1f3;white-space:normal;vertical-align:top;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:380px;}
  .chart.sm{height:330px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);}
  .lgd{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--ink);margin:8px 0 4px;}
  .lgd span{display:inline-flex;align-items:center;gap:5px;}
  .dot{display:inline-block;width:9px;height:9px;border-radius:50%;}
  .verdict{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-top:14px;}
  .verdict .box{border-radius:10px;padding:14px 16px;border:1px solid var(--line);}
  .verdict .box h3{font-size:14px;margin-bottom:6px;}
  .verdict .box.g{background:#eef7f2;border-color:#cde8da;} .verdict .box.g h3{color:#17442f;}
  .verdict .box.b{background:#eef3fb;border-color:#d5e2f7;} .verdict .box.b h3{color:#1a3a6e;}
  .verdict .box.o{background:#fff8ec;border-color:#f3dfb6;} .verdict .box.o h3{color:#7c4a03;}
  .score{display:inline-block;background:#1f2329;color:#fff;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:700;margin-left:6px;}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>三张「信用支付」面孔：SOFI × Block(XYZ) × AFRM 财报对比与 US10Y 敏感性</h1>
    <div class="meta">数据截至 2026-08-14（Yahoo 日线 + FRED DGS10）｜财报：SOFI 2026 Q2（7/29）、XYZ 2026 Q2（8/5）、AFRM FY2026 Q3（5/7，Q4 于 8/27 待发布）｜单位：美元｜红=增长/正收益，绿=下降/负收益（A股惯例）</div>
    <div class="verdict">
      <div class="box g"><h3>谁增长更好 → AFRM 质量最高，SOFI 增速最快</h3>
        AFRM：GMV +35%（连续 10 季 &gt;30%）、RLTC +41%、Card GMV +146%，<b>量价齐升、增长质量最高</b>；SOFI：净营收 +43% 最快，但更多靠净利息收入与会员渗透驱动；XYZ：总营收仅 +9.3%（比特币拖累），剔除后<b>毛利润 +25%</b>且利润弹性最大。</div>
      <div class="box b"><h3>谁更健康 → XYZ 资产负债表最干净</h3>
        负债率 43.8% + $88 亿流动性 + 季度自由现金流 $9.7 亿，<b>最稳健</b>；SOFI 是银行（负债率 81.8% 属常态，$455 亿低成本存款）；AFRM 依赖资本市场融资、信贷周期敞口最大（拨备 6.0%），但资金成本已降至三年半最低 5.8%。</div>
      <div class="box o"><h3>谁更受 US10Y 影响 → AFRM 双向弹性最大</h3>
        近 1 年 10Y 每 +10bp：AFRM 当日平均 −2.06%、XYZ −1.81%、SOFI −1.58%；10Y 大波动日（±12bp+）AFRM 双向反应最剧烈（涨息日 −2.84%，降息日 +0.56%）；<b>降息周期最受益、加息周期最受伤</b>；SOFI 对降息日几乎无反应（银行 NII 属性）。当下（2026-08）三家滚动 60 日相关均达 −0.55 ~ −0.61，利率是三家共同的最大压制项。</div>
    </div>
  </div>

  <div class="card">
    <h2>一、公司速览：三个「把钱借出去」的不同姿势</h2>
    <div class="scroll"><table>
      <thead><tr><th>公司</th><th>商业模式</th><th>资金端</th><th>资产端（收入引擎）</th><th>对利率的本质敞口</th></tr></thead>
      <tbody>
        <tr><td><b>SOFI</b> 数字银行</td><td>全能金融 App：个人贷/房贷/学生贷 + 银行牌照 + 会员订阅 + 投顾</td><td>$455 亿存款（低成本、粘性高）</td><td>净利息收入（占净营收 ~65%）+ 费用收入 + 技术平台</td><td><b>净息差敏感</b>：降息→贷款收益率与存款成本同降，NII 变化取决于利差；市场仍视为利率敏感成长股</td></tr>
        <tr><td><b>XYZ</b> 支付生态</td><td>Square 商户收单（GPV $728 亿）+ Cash App 消费者（贷款+交易+卡片）+ Afterpay BNPL + 比特币</td><td>$88 亿现金/证券，几乎零净债务</td><td>收单费率 + 贷款利息 + 比特币价差（$18.9 亿收入但毛利薄）+ 硬件</td><td><b>敞口最小</b>：收入高度多元，比特币对冲了一部分利率敏感度；借贷业务（$189 亿发放）是利率敞口主来源</td></tr>
        <tr><td><b>AFRM</b> BNPL 纯玩家</td><td>0% APR（商户付费）+ 利息型分期（消费者付费）+ Affirm Card；GMV $116 亿/季</td><td>证券化 ABS + 债务融资 + 资本合作（融资能力 $282 亿）</td><td>商户费 + 消费者利息（RLTC $4.98 亿）+ 卡网络费</td><td><b>融资成本敏感</b>：负债驱动放款，利率下行→资金成本降（已 −126bp 至 5.8%）+ 0% 产品更便宜→需求升，<b>双向放大</b></td></tr>
      </tbody></table>
    </div>
  </div>

  <div class="card">
    <h2>二、增长对比：谁增长更好</h2>
    <div id="chart_growth" class="chart"></div>
    <div class="note">左轴=最新季营收（十亿美元）；右轴=营收同比增速。口径：SOFI 总净营收 / XYZ 总营收（含比特币）/ AFRM 总营收。XYZ 总营收被比特币收入下滑（−12.8%）拖累，看毛利润口径更真实（+25%）。</div>
    <div class="scroll" style="margin-top:12px;"><table>
      <thead><tr><th>公司</th><th>最新季报</th><th>营收（同比）</th><th>毛利润（同比）</th><th>净利润（同比）</th><th>EPS</th><th>GAAP 净利率</th></tr></thead>
      <tbody>__ROWS_GROWTH__</tbody>
    </table></div>
    <div class="keypoint"><b>增长质量拆解：</b>AFRM 是「量价齐升」——GMV +35% 的同时 RLTC 率占 GMV 4.3%（+16bp）、Card GMV +146%，增长由产品渗透（商户 +44%、卡户翻倍）驱动，可持续性最强；SOFI 是「规模渗透」——会员 +35%、产品渗透率 35%→51%，靠交叉销售把单客价值拉高；XYZ 是「利润优先」——用户只 +3%（Cash App 月活 5900 万）但毛利润 +31%，靠每用户变现率提升（commerce monetization +12bp），同时把经营利润率做到历史新高 27%。</div>
  </div>

  <div class="card">
    <h2>三、盈利与健康度：谁更健康</h2>
    <div id="chart_profit" class="chart sm"></div>
    <div class="note">左=GAAP 净利率；右=调整后经营利润率（% of 毛利润 for XYZ / % of 营收 for AFRM；SOFI 无独立调整后经营利润率披露，用净利率）。XYZ GAAP 净利率仅 1.3% 系 $3.65 亿一次性法律拨备/重组费用，调整后经营利润率 27% 为历史新高；AFRM 刚实现 GAAP 盈利（净利 $1.03 亿 vs 上年 $280 万）。</div>
    <div class="scroll" style="margin-top:12px;"><table>
      <thead><tr><th>公司</th><th>调整后经营利润率</th><th>资产负债表</th><th>信贷质量</th><th>现金流 / 造血</th></tr></thead>
      <tbody>__ROWS_HEALTH__</tbody>
    </table></div>
    <div class="keypoint"><b>健康度结论：</b>XYZ 财务结构最干净（低负债+高现金+强自由现金流+回购 $46 亿余量），且贷款损失随发放量 +59% 翻倍仍称 cohort 健康——但需盯紧；SOFI 银行模式稳健（存款 $455 亿是护城河），健康度取决于利差与贷款信用周期；AFRM 盈利刚转正、拨备 6.0% 处于高位、资金链依赖资本市场再融资——<b>在三者中经营杠杆最高、对宏观（利率+消费信用）最敏感</b>。最大回撤佐证：上市以来 AFRM −94.7%、XYZ −86.1%、SOFI −83.3%；近 1 年 XYZ −38%、SOFI −36%、AFRM −49%。</div>
  </div>

  <div class="card">
    <h2>四、US10Y 敏感性：谁最受 10Y 影响（核心）</h2>
    <div class="lgd">
      <span><i class="dot" style="background:#1e66d6;"></i> SOFI</span>
      <span><i class="dot" style="background:#7048e8;"></i> XYZ</span>
      <span><i class="dot" style="background:#e8590c;"></i> AFRM</span>
      <span><i class="dot" style="background:#6b7280;"></i> US10Y（右轴，%）</span>
    </div>
    <div id="chart_nav" class="chart"></div>
    <div class="note">2021-01 起归一化净值（月末）与 US10Y 收益率。三家走势与 10Y 长期呈镜像：2021 低利率期普涨、2022 加息年普跌（AFRM 跌最狠）、2024-2025 利率回落期分化。XYZ 数据含 SQ 时代（2015-11 起），此处统一从 2021-01 起对齐。</div>

    <div id="chart_roll" class="chart"></div>
    <div class="note">滚动 60 日相关系数（个股日收益 vs US10Y 日变化）。负值=利率上行日股价跌。2022 加息期三家相关深度转负（−0.4~−0.5），2024 宽松预期期一度转正；<span class="hl">当前（2026-08-14）三家同时回到 −0.55 ~ −0.61 的极值区</span>，说明利率是当下三家股价的共同最大压制。</div>

    <div id="chart_beta" class="chart sm"></div>
    <div class="note">β = 个股日收益对 10Y 日变化的敏感度（% / 每 10bp）。全期（2021-01 起）与近 1 年（2025-08 起）均为负值。<b>近 1 年排序：AFRM（−2.06%/10bp）&gt; XYZ（−1.81%）&gt; SOFI（−1.58%）</b>——利率每上行 10bp，AFRM 当天平均跌 2.06%。</div>

    <div id="chart_mon" class="chart sm"></div>
    <div class="note">按自然月：US10Y 月内上行月 vs 下行月，三家平均月收益（%）。利率下行月 AFRM +8.5% 弹性最大、SOFI +5.3% 次之；上行月三家均为负（XYZ −3.3% 最弱）。利率方向月度相关系数：XYZ −0.37 &gt; AFRM −0.35 &gt; SOFI −0.26。</div>

    <div id="chart_lvl" class="chart sm"></div>
    <div class="note">按 10Y 收益率水平分档（2021-01 以来）的平均日收益（bp）。10Y 处于 4.5–5.0% 高位区间时三家平均日收益全为负（SOFI −27bp/日最惨、AFRM −10bp、XYZ −12bp）；4.0–4.5% 区间为正（SOFI +23bp 最受益）。</div>

    <div class="scroll" style="margin-top:12px;"><table>
      <thead><tr><th>10Y 单日大波动（|Δ10Y| ≥ 12bp，2021 年以来）</th><th>SOFI</th><th>XYZ</th><th>AFRM</th></tr></thead>
      <tbody>
        <tr><td>10Y 单日大涨日（N=43）：平均当日收益</td><td class="dn">−2.41%</td><td class="dn">−2.03%</td><td class="dn">−2.84%</td></tr>
        <tr><td>10Y 单日大跌日（N=38）：平均当日收益</td><td class="na">−0.01%</td><td class="up">+0.36%</td><td class="up">+0.56%</td></tr>
      </tbody></table></div>
    <div class="keypoint"><b>US10Y 敏感性结论：</b>① <b>AFRM 是纯正的高久期信用资产</b>——加息日跌最多（−2.84%）、降息日涨最多（+0.56%），月度利率下行弹性 +8.5%，因为它既是「消费者信贷」又靠「资本市场融资」，利率同时打需求端与成本端；② <b>XYZ 相关性最高（−0.25）但振幅居中</b>——作为金融科技支付龙头，被市场当作「利率定价的成长股」，但基本面现金充裕、对融资成本不敏感，跌多属估值层面；③ <b>SOFI 最特殊：涨息日跟跌（−2.41%）、降息日几乎不动（−0.01%）</b>——银行资产负债表使降息压缩净息差预期的利空抵消了估值利好，市场只给它「利率上行恐惧」不给「利率下行弹性」；④ 当下三家滚动相关均 −0.55 以下，<b>若 10Y 继续上行，AFRM 跌幅预期最大、SOFI 次之、XYZ 相对抗跌</b>；反之 10Y 回落，AFRM 弹性最大。</div>
  </div>

  <div class="card">
    <h2>五、估值对照（8/14 收盘，最新季年化口径）</h2>
    <div id="chart_ps" class="chart sm"></div>
    <div class="scroll" style="margin-top:12px;"><table>
      <thead><tr><th>公司</th><th>收盘价</th><th>市值（估算）</th><th>最新季营收年化</th><th>PS（年化）</th><th>估值解读</th></tr></thead>
      <tbody>
        <tr><td><b>SOFI</b></td><td>$18.29</td><td>~$236 亿</td><td>$48.7 亿（12.19×4）</td><td class="up">~4.9x</td><td>银行属性压估值；已连续盈利，PE ~40x 隐含高增长预期</td></tr>
        <tr><td><b>XYZ</b></td><td>$82.88</td><td>~$498 亿</td><td>$264.7 亿（66.18×4）</td><td class="up">~1.9x</td><td>三家中最便宜；P/毛利润 ~4.2x，利润率高增+回购支撑</td></tr>
        <tr><td><b>AFRM</b></td><td>$78.35</td><td>~$248 亿</td><td>$41.6 亿（10.39×4）</td><td class="up">~6.0x</td><td>估值最贵，定价「增长+利润率爬坡」；利率下行是重估催化剂</td></tr>
      </tbody></table></div>
  </div>

  <div class="card">
    <div class="warn"><b>口径与局限：</b>① 三家财季不完全对齐（AFRM 为 FY 财年，最新已发为 Q3 FY26 即自然年 2026 Q1；Q4 FY26 于 8/27 发布，届时应更新）；② 市值与 PS 为 8/14 收盘估算（股本取公开最新），仅作横向相对参考；③ US10Y 敏感性为日频统计相关/回归，反映历史同频波动，<b>不构成因果与预测</b>；④ 股价敏感性受财报事件、个股 alpha 干扰，滚动相关波动大；⑤ 利率水平分档样本量不同（4.5–5.0% 区间样本最多）。</div>
    <div class="dis">数据来源：Yahoo Finance 日线（SOFI/XYZ/AFRM，截至 2026-08-14）、FRED DGS10（10Y 美债收益率）、各公司 2026 年 7-8 月财报/电话会公开披露。量化部分由本地脚本计算。<br><br><b>免责声明：</b>以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>
<script>
const D = __JSON__;
const C = {sofi:'#1e66d6', xyz:'#7048e8', afrm:'#e8590c', y10:'#6b7280', red:'#e03131', green:'#0aa06e'};

// 二、增长
echarts.init(document.getElementById('chart_growth')).setOption({
  tooltip:{trigger:'axis'},
  legend:{data:['最新季营收($B)','营收同比(%)']},
  grid:{left:50,right:52,top:40,bottom:40},
  xAxis:{type:'category',data:D.labels},
  yAxis:[{type:'value',name:'$B',splitLine:{lineStyle:{color:'#eef0f3'}}},
         {type:'value',name:'同比%',axisLabel:{formatter:'{value}%'}}],
  series:[
    {name:'最新季营收($B)',type:'bar',data:D.rev,barWidth:'38%',
      itemStyle:{color:p=>['#1e66d6','#7048e8','#e8590c'][p.dataIndex]},
      label:{show:true,position:'top',formatter:p=>p.value.toFixed(2)+'B',fontSize:11,color:'#1f2329'}},
    {name:'营收同比(%)',type:'bar',data:D.rev_yoy,yAxisIndex:1,barWidth:'26%',
      itemStyle:{color:p=>D.rev_yoy[p.dataIndex]>=0?'#e03131':'#0aa06e',opacity:.75},
      label:{show:true,position:'top',formatter:p=>(p.value>=0?'+':'')+p.value+'%',fontSize:11,color:'#1f2329'}}
  ]
});

// 三、利润率
echarts.init(document.getElementById('chart_profit')).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
  legend:{data:['GAAP净利率','调整后经营利润率']},
  grid:{left:48,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:D.labels},
  yAxis:{type:'value',axisLabel:{formatter:'{value}%'}},
  series:[
    {name:'GAAP净利率',type:'bar',data:[12.8,1.3,9.9],barWidth:'32%',
      itemStyle:{color:'#1e66d6'},label:{show:true,position:'top',formatter:'{c}%'}},
    {name:'调整后经营利润率',type:'bar',data:[13,27,27],barWidth:'32%',
      itemStyle:{color:'#b45309'},label:{show:true,position:'top',formatter:'{c}%'}}
  ]
});

// 四-1 净值 vs 10Y
echarts.init(document.getElementById('chart_nav')).setOption({
  animation:false,
  tooltip:{trigger:'axis',axisPointer:{type:'cross'}},
  legend:{data:['SOFI','XYZ','AFRM','US10Y%']},
  grid:{left:55,right:55,top:45,bottom:45},
  xAxis:{type:'category',data:D.nav_dates,axisLabel:{fontSize:10}},
  yAxis:[{type:'value',name:'净值(2021-01=1)',scale:true,splitLine:{lineStyle:{color:'#eef0f3'}}},
         {type:'value',name:'10Y%',axisLabel:{formatter:'{value}%'},splitLine:{show:false}}],
  dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:2}],
  series:[
    {name:'SOFI',type:'line',data:D.nav_sofi,showSymbol:false,lineStyle:{width:1.6,color:C.sofi}},
    {name:'XYZ',type:'line',data:D.nav_xyz,showSymbol:false,lineStyle:{width:1.6,color:C.xyz}},
    {name:'AFRM',type:'line',data:D.nav_afrm,showSymbol:false,lineStyle:{width:1.6,color:C.afrm}},
    {name:'US10Y%',type:'line',data:D.y10_level,yAxisIndex:1,showSymbol:false,lineStyle:{width:1.6,color:C.y10,type:'dashed'}}
  ]
});

// 四-2 滚动相关
const rollDates = D.roll_dates;
const maxLen = Math.max(D.roll_sofi.length, D.roll_xyz.length, D.roll_afrm.length);
echarts.init(document.getElementById('chart_roll')).setOption({
  animation:false,
  tooltip:{trigger:'axis',valueFormatter:v=>v==null?'—':v.toFixed(2)},
  legend:{data:['SOFI','XYZ','AFRM']},
  grid:{left:48,right:20,top:40,bottom:45},
  xAxis:{type:'category',data:rollDates,axisLabel:{fontSize:10}},
  yAxis:{type:'value',min:-0.8,max:0.8,axisLabel:{formatter:v=>v.toFixed(1)},
    splitLine:{lineStyle:{color:'#eef0f3'}}},
  dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:2}],
  series:[
    {name:'SOFI',type:'line',data:D.roll_sofi,showSymbol:false,lineStyle:{width:1.4,color:C.sofi}},
    {name:'XYZ',type:'line',data:D.roll_xyz,showSymbol:false,lineStyle:{width:1.4,color:C.xyz}},
    {name:'AFRM',type:'line',data:D.roll_afrm,showSymbol:false,lineStyle:{width:1.4,color:C.afrm}},
    {type:'line',data:rollDates.map(()=>0),showSymbol:false,lineStyle:{width:1,type:'dashed',color:'#c8cdd3'},tooltip:{show:false},legendHoverLink:false}
  ]
});

// 四-3 β
echarts.init(document.getElementById('chart_beta')).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'%/10bp'},
  legend:{data:['全期β','近1年β']},
  grid:{left:50,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:D.labels},
  yAxis:{type:'value',axisLabel:{formatter:'{value}'}},
  series:[
    {name:'全期β',type:'bar',data:D.beta_full.map(v=>+v.toFixed(2)),barWidth:'30%',
      itemStyle:{color:'#9aa2ab'},label:{show:true,position:'top',formatter:'{c}'}},
    {name:'近1年β',type:'bar',data:D.beta_1y.map(v=>+v.toFixed(2)),barWidth:'30%',
      itemStyle:{color:p=>['#1e66d6','#7048e8','#e8590c'][p.dataIndex]},
      label:{show:true,position:'top',formatter:'{c}',fontWeight:'bold'}}
  ]
});

// 四-4 月度方向
echarts.init(document.getElementById('chart_mon')).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'%'},
  legend:{data:['10Y上行月(共'+D.mon_n.up+'个)','10Y下行月(共'+D.mon_n.down+'个)','全部月份']},
  grid:{left:48,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:D.labels},
  yAxis:{type:'value',axisLabel:{formatter:'{value}%'}},
  series:[
    {name:'10Y上行月(共'+D.mon_n.up+'个)',type:'bar',data:D.mon_up.map(v=>+v.toFixed(2)),barWidth:'22%',
      itemStyle:{color:'#e03131'},label:{show:true,position:'top',formatter:'{c}%'}},
    {name:'10Y下行月(共'+D.mon_n.down+'个)',type:'bar',data:D.mon_down.map(v=>+v.toFixed(2)),barWidth:'22%',
      itemStyle:{color:'#0aa06e'},label:{show:true,position:'top',formatter:'{c}%'}},
    {name:'全部月份',type:'bar',data:D.mon_all.map(v=>+v.toFixed(2)),barWidth:'22%',
      itemStyle:{color:'#9aa2ab'},label:{show:true,position:'top',formatter:'{c}%'}}
  ]
});

// 四-5 利率分档
echarts.init(document.getElementById('chart_lvl')).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'bp/日'},
  legend:{data:['SOFI','XYZ','AFRM']},
  grid:{left:48,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:D.lvl_keys},
  yAxis:{type:'value',axisLabel:{formatter:'{value}bp'}},
  series:[
    {name:'SOFI',type:'bar',data:D.lvl_sofi,barWidth:'20%',itemStyle:{color:C.sofi}},
    {name:'XYZ',type:'bar',data:D.lvl_xyz,barWidth:'20%',itemStyle:{color:C.xyz}},
    {name:'AFRM',type:'bar',data:D.lvl_afrm,barWidth:'20%',itemStyle:{color:C.afrm}}
  ]
});

// 五、PS
echarts.init(document.getElementById('chart_ps')).setOption({
  tooltip:{trigger:'axis',valueFormatter:v=>v+'x'},
  grid:{left:48,right:20,top:40,bottom:40},
  xAxis:{type:'category',data:D.labels},
  yAxis:{type:'value',axisLabel:{formatter:'{value}x'}},
  series:[{type:'bar',data:D.ps.map(v=>+v.toFixed(1)),barWidth:'40%',
    itemStyle:{color:p=>['#1e66d6','#7048e8','#e8590c'][p.dataIndex]},
    label:{show:true,position:'top',formatter:'{c}x',fontSize:13,fontWeight:'bold'}}]
});
</script>
</body>
</html>
"""

HTML = HTML.replace("__ROWS_GROWTH__", "\n".join(rows_growth))
HTML = HTML.replace("__ROWS_HEALTH__", "\n".join(rows_health))
HTML = HTML.replace("__JSON__", js(D))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print("written:", OUT, len(HTML), "bytes")
