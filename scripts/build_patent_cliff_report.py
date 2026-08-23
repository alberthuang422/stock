#!/usr/bin/env python3
"""生成「千亿美元市值药企专利悬崖与管线接力」分析报告 HTML。
输出 reports/26_千亿美元药企专利悬崖/index.html。静默写盘。
数据口径：市值 companiesmarketcap 2026-08-23；LOE 以美国主要专利到期为主线。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "reports", "26_千亿美元药企专利悬崖")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------- 数据 ----------------
# 公司: [名称, 市值串, 市值亿美元, 核心药+LOE 要点, 接力管线, 风险层, 悬崖集中度评分(0-10), 接力质量评分(0-10), 独占性到(final year)]
COMPANIES = [
    # 高危
    ["BMS", "百时美施贵宝", "~980", "Eliquis 2028-04 · Opdivo 2028 · Eliquis EU 2026-05\n双药合计约占营收近半",
     "Cobenfy（2026 上市）· milvexian 抗凝 P3 读数约 2027 · Qvantig（Opdivo 皮下针）· Carvykti/Breyanzi",
     "高危", 10, 4, 2028],
    ["MRK", "默沙东", "~3300", "Keytruda 2028-12（约占总营收 49%）· Januvia 2026-05 · Gardasil 9 2028 前后",
     "Keytruda Qlex 皮下针（预计转化 30-40%）· Winrevair（~$11亿/2026）· MK-0616 口服 PCSK9 · mRNA-4157 肿瘤疫苗",
     "高危", 10, 6, 2028],
    ["PFE", "辉瑞", "~1350", "Ibrance 2027-02 · Eliquis 美国 2028-04（EU 2026-05）· Xtandi/Prevnar13 2027-28",
     "Seagen ADC 平台（Padcev）· Vyndaqel 家族（~$43亿）· Metsera 口服 GLP-1（2026 启动 P3）· DMD 基因治疗",
     "高危", 9, 5, 2028],
    ["NVS", "诺华", "~2940", "Entresto 美国 2025-07 已过（26Q1 销额 -42%）· Promacta/Tasigna 2026 专利侵蚀",
     "Kisqali（+55%）· Pluvicto PLT（+70%）· Kesimpta（+56%）· Scemblix（+64%）· 收购 Anthos/Tourmaline",
     "高危", 8, 8, 2026],
    ["SNY", "赛诺菲", "~1280", "Dupixent 美国化合物专利 2031-03（制剂可延至 2045）· 当前 Q1 销 €41.7亿(+31%)",
     "amlitelimab 2026-07 终止 · lunsekimig AD P2 失败 · fitusiran（2025-12 获批）· Sarclisa（+30%）· ayvakit/altuviiio",
     "高危", 7, 3, 2031],
    # 中危
    ["AZN", "阿斯利康", "~2480", "Farxiga 2026-04 · Brilinta ~2026 · Lynparza 2027-28 · Tagrisso 2030-32（最重磅）",
     "Enhertu（全球最成功 ADC）· Imfinzi · Ultomiris（+53%）· Wainzua（ATTR 放量中）",
     "中危", 6, 7, 2032],
    ["RHHBY", "罗氏", "~3630", "Ocrevus 2029 · Tecentriq 近期竞争侵蚀（2026 增速放缓）",
     "Ocrevus 皮下针 Zunovo · fenebrutinib（MS P3 达标，肝毒性顾虑）· Vabysmo · Aled Piv（AD P3 2026 启动）",
     "中危", 6, 6, 2029],
    ["NVO", "诺和诺德", "~2260", "Ozempic/Wegovy 美国 2031-33（口径不一）· 加拿大 2026 首仿 · 2027 起主动降价",
     "CagriSema（PDUFA 2026-10-25，疗效弱于替尔泊肽）· amycretin（P3）",
     "中危", 5, 6, 2033],
    # 低危
    ["LLY", "礼来", "~10900", "tirzepatide 2036（制剂/装置至 2039-41）· 全行业保护期最长",
     "orforglipron 口服 GLP-1（2026-04 已获批）· retatrutide（P3）· 21 项 GLP + 38 项寡核糖体管线",
     "低危", 2, 10, 2041],
    ["GILD", "吉利德", "~2380", "Biktarvy 和解推迟至 2036-04 · Trodelvy 2028 左右（规模小）",
     "Yeztugo（PrEP 半年针，~$10亿/2026）· BIC/LEN 每周口服（PDUFA 2026-08-27）· Duvystat（亨廷顿 P3 转二线）",
     "低危", 2, 8, 2036],
    ["ABBV", "艾伯维", "~4570", "Humira 悬崖已过（26 营收 -66%）· Skyrizi/Rinvoq 2033-37（儿科+适应症多维专利）",
     "Skyrizi（+35%）· Rinvoq（+25%）· Emraclidine 精神分裂 P3 · Tavapadon 帕金森 P3 · Epcoritamab",
     "低危", 2, 8, 2037],
    ["JNJ", "强生", "~6530", "Stelara 2025-07 已过（26Q1 营收 -54%）· Darzalex 2029（+20% 增长）",
     "Tremfya（IBD/银屑病高增长）· Icotyde · Carvykti CAR-T（~$25亿指引）· Spravato",
     "低危", 3, 9, 2029],
    ["AMGN", "安进", "~1580", "老品种陆续到期，2030 前无单一大品种断崖 · 生物类似药持续侵蚀",
     "Repatha（+23%）· Evenity（+30%）· Tezspire（+60%）· Uplizna · MariTide（肥胖，2026 底-2027 递交）",
     "低危", 3, 7, 2031],
    ["VRTX", "福泰", "~1300", "CFTR 组合拳 2037-40（孤儿药壁垒，行业最坚固护城河之一）",
     "povetacicept（IgA 肾病，PDUFA 2026-11-30）· Journavx（非阿片镇痛 2025-01 上市）· VX-522",
     "低危", 1, 8, 2040],
    ["GSK", "葛兰素史克", "~1020", "管线/悬崖细节未完整核实（⚠️未核实）",
     "Arexvy（RSV 疫苗）、Jemperli、Omjjara —— 公开确认品种，LOE 待补",
     "低危", 4, 5, None],
]

# 年份暴露（亿美元，美国主要口径品牌收入近似）
YEAR_LOE_EXPOSURE = [
    {"y": 2026, "label": "Januvia / Entresto 已过 / Eliquis EU / Farxiga / Brilinta / Promacta", "amt": 220},
    {"y": 2027, "label": "Ibrance / Lynparza / Xtandi / Prevnar13", "amt": 260},
    {"y": 2028, "label": "Keytruda / Opdivo / Eliquis US / Gardasil9（超级悬崖年）", "amt": 480},
    {"y": 2029, "label": "Ocrevus / Darzalex", "amt": 260},
    {"y": 2030, "label": "Tagrisso 开始 / 无密集", "amt": 120},
    {"y": 2031, "label": "Dupixent / Ozempic 中段 / 安进老品种尾部", "amt": 320},
    {"y": 2032, "label": "Tagrisso 尾声", "amt": 60},
    {"y": 2033, "label": "Skyrizi 边缘 / Ozempic 尾部", "amt": 150},
    {"y": 2036, "label": "Biktarvy / tirzepatide 主体", "amt": 60},
]

# 接力质量 vs 悬崖集中度（散点：x=集中度, y=接力质量, 颜色按风险层）
SCATTER = [
    {"ticker": "BMS", "x": 10, "y": 4, "risk": "高危"},
    {"ticker": "MRK", "x": 10, "y": 6, "risk": "高危"},
    {"ticker": "PFE", "x": 9, "y": 5, "risk": "高危"},
    {"ticker": "NVS", "x": 8, "y": 8, "risk": "高危"},
    {"ticker": "SNY", "x": 7, "y": 3, "risk": "高危"},
    {"ticker": "AZN", "x": 6, "y": 7, "risk": "中危"},
    {"ticker": "RHHBY", "x": 6, "y": 6, "risk": "中危"},
    {"ticker": "NVO", "x": 5, "y": 6, "risk": "中危"},
    {"ticker": "LLY", "x": 2, "y": 10, "risk": "低危"},
    {"ticker": "GILD", "x": 2, "y": 8, "risk": "低危"},
    {"ticker": "ABBV", "x": 2, "y": 8, "risk": "低危"},
    {"ticker": "JNJ", "x": 3, "y": 9, "risk": "低危"},
    {"ticker": "AMGN", "x": 3, "y": 7, "risk": "低危"},
    {"ticker": "VRTX", "x": 1, "y": 8, "risk": "低危"},
    {"ticker": "GSK", "x": 4, "y": 5, "risk": "低危"},
]

data_js = {
    "year": YEAR_LOE_EXPOSURE,
    "scatter": SCATTER,
}
data_json = json.dumps(data_js, ensure_ascii=False)

# 表格行
rows = []
for tk, name, mcap, loe, pipe, risk, conc, relay, final in COMPANIES:
    badge = {"高危": "badge-hi", "中危": "badge-mid", "低危": "badge-lo"}[risk]
    loe_html = loe.replace("\n", "<br>")
    final_txt = (str(final) + " 及以后") if final else "未核实"
    rows.append(f"""        <tr class="risk-{risk}">
          <td class="tk"><b>{tk}</b><span class="co">{name}</span><span class="mcap">{mcap} 亿美元</span></td>
          <td>{loe_html}</td>
          <td>{pipe}</td>
          <td><span class="badge {badge}">{risk}</span></td>
          <td class="num">{conc}/10</td>
          <td class="num">{relay}/10</td>
          <td class="num">{final_txt}</td>
        </tr>""")
rows_html = "\n".join(rows)

# 逻辑注入 JS 中的全部 JSON 用 @@DATA@@ 占位（避免 f-string 转义地狱）
html_tpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>千亿美元药企专利悬崖与管线接力 ｜ 15 家全球制药巨头</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root { --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#fff;
          --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --green:#009E73; --purple:#CC79A7;
          --red:#C0392B; --verm:#D55E00; --gold:#E69F00; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }
  .wrap { max-width: 1120px; margin: 0 auto; }
  h1 { font-size: 26px; letter-spacing: .5px; margin-bottom: 4px; }
  .subtitle { color: var(--sub); font-size: 13px; margin-bottom: 22px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(20,30,50,.05); }
  .card h2 { font-size: 17px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .card h2::before { content: ""; width: 4px; height: 16px; background: var(--blue); border-radius: 2px; }
  .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 4px; }
  .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .kv { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .kv .k { font-size: 12px; color: var(--sub); }
  .kv .v { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .kv .v small { font-size: 12px; font-weight: 400; color: var(--sub); }
  .kv .muted { font-size: 12.5px; color: var(--sub); margin-top: 4px; font-weight: 400; }
  .up { color: var(--red); } .down { color: var(--green); }
  .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }
  .tag.amber { background: #fdf3e3; color: var(--verm); }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; margin-top: 6px; }
  th, td { padding: 9px 10px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }
  th { background: #f1f4f9; font-weight: 600; white-space: nowrap; }
  td.tk { white-space: nowrap; }
  td.tk .co { display: block; font-size: 11px; color: var(--sub); font-weight: 400; }
  td.tk .mcap { display: block; font-size: 10.5px; color: var(--sub); font-weight: 400; }
  td.num { text-align: center; white-space: nowrap; }
  tr.risk-高危 { border-left: 3px solid var(--verm); }
  tr.risk-中危 { border-left: 3px solid var(--gold); }
  tr.risk-低危 { border-left: 3px solid var(--green); }
  .badge { display: inline-block; font-size: 11px; padding: 2px 9px; border-radius: 20px; white-space: nowrap; }
  .badge-hi { background: #fdecea; color: var(--verm); border: 1px solid #f5c6bd; }
  .badge-mid { background: #fdf6ec; color: #a16207; border: 1px solid #f0d9a8; }
  .badge-lo { background: #eaf6f1; color: var(--green); border: 1px solid #b8e0cf; }
  .chart { width: 100%; height: 380px; }
  .chart-sm { width: 100%; height: 320px; }
  .concl { border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }
  .warn { border-left: 4px solid var(--verm); background: #fdf6ec; padding: 10px 14px;
          border-radius: 0 8px 8px 0; font-size: 13px; margin-top: 10px; }
  .note { font-size: 12px; color: var(--sub); margin-top: 10px; }
  .src { font-size: 11.5px; color: var(--sub); margin-top: 8px; line-height: 1.7; }
  .legend-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; }
  .disclaimer { font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }
  @media (max-width: 720px) { .grid3, .grid4 { grid-template-columns: 1fr 1fr; } .chart, .chart-sm { height: 300px; } }
</style>
</head>
<body>
<div class="wrap">

  <h1>千亿美元市值药企：专利悬崖时间表与管线接力评估</h1>
  <div class="subtitle">15 家研发型药企（市值 ≥ $100B，companiesmarketcap 2026-08-23 口径）· LOE 以美国主要专利到期为主线 · 数据截至 2026-08-23</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>核心结论</h2>
    <div class="grid4">
      <div class="kv"><div class="k">身负悬崖风险的公司数</div>
        <div class="v">15 <small>家</small></div>
        <div class="muted">市值 ≥ $100B 研发型药企；CVS 因零售属性排除</div></div>
      <div class="kv"><div class="k">超级悬崖年</div>
        <div class="v">2028</div>
        <div class="muted">Keytruda + Opdivo + Eliquis + Gardasil9 单年约 $400-500 亿品牌收入承压</div></div>
      <div class="kv"><div class="k">综合风险最高</div>
        <div class="v">BMS</div>
        <div class="muted">双抗单品 2028 双到期，约占营收近半；纠缠窗口最紧</div></div>
      <div class="kv"><div class="k">护城河最远</div>
        <div class="v">礼来</div>
        <div class="muted">tirzepatide 专利至 2036（制剂/装置至 2039-41），行业保护期最长</div></div>
    </div>
    <div class="grid3" style="margin-top:12px;">
      <div class="kv"><div class="k">高危梯队</div>
        <div class="v" style="font-size:16px;">BMS / MRK / PFE / NVS / SNY</div>
        <div class="muted">2026-2028 密集到期，接力要么未兑现要么差距悬殊</div></div>
      <div class="kv"><div class="k">中危梯队</div>
        <div class="v" style="font-size:16px;">AZN / 罗氏 / NVO</div>
        <div class="muted">有断崖但时间带更宽，新品种梯队基本成型</div></div>
      <div class="kv"><div class="k">低危梯队</div>
        <div class="v" style="font-size:16px;">LLY / GILD / ABBV / JNJ / AMGN / VRTX / GSK</div>
        <div class="muted">专利墙买到 2030s 后半，或已成功穿越（JNJ/ABBV）</div></div>
    </div>
  </div>

  <!-- 按年暴露 -->
  <div class="card">
    <h2>① 专利悬崖按年暴露（品牌收入近似，亿美元）<span class="tag amber">峰值 = 2028</span></h2>
    <div id="chart_year" class="chart"></div>
    <div class="note">口径：美国主要专利到期的品牌药年度收入近似（2026 含已过悬崖的 Entresto 冲击 + Eliquis 欧洲）；2028 超级悬崖年显著凸起。</div>
  </div>

  <!-- 风险矩阵 -->
  <div class="card">
    <h2>② 悬崖集中度 × 接力质量矩阵</h2>
    <div id="chart_scatter" class="chart-sm"></div>
    <div class="note">右上角（低悬崖 + 高接力质量）= 时间站在自己这边：LLY / VRTX / GILD / JNJ / ABBV；左下区域 = BMS / SNY / PFE 最危险。</div>
  </div>

  <!-- 逐一拆解 -->
  <div class="card">
    <h2>③ 逐公司：核心药 LOE × 接力管线</h2>
    <table>
      <thead><tr>
        <th>公司</th><th>核心药品 & 悬崖时点（美国口径）</th><th>接力管线（已上市 + 临近获批）</th>
        <th>风险层</th><th>集中度</th><th>接力质量</th><th>独占至</th>
      </tr></thead>
      <tbody>
@@ROWS@@
      </tbody>
    </table>
    <div class="warn">⚠️ GSK 市值处于临界（约 $102-112B）边缘入选；管线/悬崖细节未完整核实，Arexvy / Jemperli / Omjjara 为公开确认品种，LOE 待补。诺和诺德美国专利确切到期日（2031 vs 2033）不同数据库口径不一；第三方机构（theraradar 等）预测为低置信度参考，最终以 FDA Orange Book + 各公司 10-K 为准。</div>
  </div>

  <!-- 行业判断 -->
  <div class="card">
    <h2>④ 行业性判断</h2>
    <div class="concl"><b>2028 超级悬崖年</b>：Keytruda（~$317亿）+ Opdivo（~$100亿）+ Eliquis（~$130亿，BMS 摊分）+ Gardasil 9 单年约 $400-500 亿品牌收入面临专利到期，为行业史上最集中断崖；叠加 IRA 首轮降价（2028-01 生效）三方承压最重。</div>
    <div class="concl" style="border-color:var(--orange);background:#fdf8f0;"><b>生物类似药 ≠ 小分子仿制药</b>：小分子（Eliquis/Ibrance）断崖式（-80~90%）；大分子生物类似药（Keytruda/Opdivo/Ocrevus）阶梯式年侵蚀（-20~30%/年），给皮下针等生命周期管理留出 3-5 年爬坡窗口。</div>
    <div class="concl" style="border-color:var(--green);background:#f1faf6;"><b>接力成功共性</b>：要么悬崖已提前买走时间（吉利德 Biktarvy 和解、福泰孤儿药壁垒、礼来多专利墙），要么新品种在悬崖前 2-3 年已放量（JNJ/ABBV/NVS）；反面教材是赛诺菲——2031 到期但接班资产 2026 连挫。</div>
  </div>

  <!-- 风险排序 -->
  <div class="card">
    <h2>⑤ 综合风险排序（悬崖 + 接力缺口）</h2>
    <div class="concl"><b>BMS &gt; MRK &gt; PFE ≈ SNY &gt; NVS &gt; RHHBY ≈ AZN ≈ NVO &gt; AMGN ≈ JNJ ≈ GSK(未核实) &gt; ABBV &gt; VRTX ≈ GILD ≈ LLY</b></div>
    <div class="note">一句话：BMS / MRK / PFE 是「2028 前必答题」——需靠 III 期新药 + 皮下针在 24-30 个月内扛住约 $400-500 亿集体悬崖；LLY / GILD / VRTX / ABBV 把悬崖买到 2030s 后半，属于时间站在自己一边的玩家。</div>
  </div>

  <div class="src">
    <b>来源</b>：companiesmarketcap（市值，2026-08-23 实时口径）；各公司 2026Q1/Q2 财报与投资者会议（营收占比/增速）；FDA 相关数据（LOE 时点）；GeneOnline / DrugPatentWatch / PharmDossier 等行业数据库交叉验证。<br>
    口径说明：CVS Health（约 $121B）市值达标但属零售药房/分销商，剔除；GSK 临界入选（约 $102-112B）。未核实项：GSK 管线细节、NVO 美国专利确切年份、第三方数据库预测数据——建议以 FDA Orange Book + 各公司 10-K 复核。
  </div>

  <div class="disclaimer">以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。</div>
</div>

<script>
const DATA = @@DATA@@;
// ① 按年暴露柱状图
(function(){
  const el = document.getElementById('chart_year');
  const years = DATA.year.map(d => d.y);
  const amts = DATA.year.map(d => d.amt);
  const labels = DATA.year.map(d => d.label);
  const chart = echarts.init(el);
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: function(ps){
      const p = ps[0]; return '<b>' + p.axisValue + ' 年</b><br>' + labels[p.dataIndex] + '<br>约 <b>$' + p.value + ' 亿</b>';
    }},
    grid: { left: 60, right: 24, top: 30, bottom: 56 },
    xAxis: { type: 'category', data: years, axisLabel: { fontSize: 12 } },
    yAxis: { type: 'value', name: '亿美元', nameTextStyle: { fontSize: 11 } },
    series: [{
      type: 'bar', data: amts, barWidth: '46%',
      itemStyle: { color: function(p){ return p.dataIndex === 3 ? '#D55E00' : '#0072B2'; },
                   borderRadius: [4,4,0,0] },
      label: { show: true, position: 'top', fontSize: 11, formatter: function(p){ return '$' + p.value + '亿'; } }
    }]
  });
})();
// ② 风险矩阵散点
(function(){
  const el = document.getElementById('chart_scatter');
  const colorMap = { '高危': '#D55E00', '中危': '#E69F00', '低危': '#009E73' };
  const series = [];
  for (const r of Object.keys(colorMap)) {
    const pts = DATA.scatter.filter(d => d.risk === r);
    series.push({
      name: r, type: 'scatter', data: pts.map(d => [d.x, d.y]),
      symbolSize: 22,
      itemStyle: { color: colorMap[r], opacity: 0.85, borderColor: '#fff', borderWidth: 1.5 },
      label: { show: true, position: 'top', fontSize: 11, formatter: function(p){ return pts[p.dataIndex].ticker; } }
    });
  }
  const chart = echarts.init(el);
  chart.setOption({
    tooltip: { formatter: function(p){
      const d = p.data;
      const item = DATA.scatter.find(s => s.x === d[0] && s.y === d[1]);
      return '<b>' + item.ticker + '</b><br>悬崖集中度 ' + item.x + '/10 · 接力质量 ' + item.y + '/10';
    }},
    legend: { top: 0, data: ['高危','中危','低危'] },
    grid: { left: 48, right: 30, top: 40, bottom: 44 },
    xAxis: { type: 'value', name: '悬崖集中度 →', min: 0, max: 10.8, nameLocation: 'middle',
             nameGap: 24, nameTextStyle: { fontSize: 12 } },
    yAxis: { type: 'value', name: '接力质量 →', min: 0, max: 11, nameLocation: 'middle',
             nameGap: 28, nameTextStyle: { fontSize: 12 } },
    series: series,
    animation: false
  });
})();
</script>
</body>
</html>
"""

html = html_tpl.replace("@@DATA@@", data_json).replace("@@ROWS@@", rows_html)

out = os.path.join(OUT_DIR, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written: %s %d" % (out, os.path.getsize(out)))