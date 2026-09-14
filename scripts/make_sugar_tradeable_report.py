# -*- coding: utf-8 -*-
"""渲染 94 号报告：白糖可贸易国家全景（2000-2026）"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE, "data", "sugar", "tradeable_countries.json"), encoding="utf-8") as f:
    D = json.load(f)

YEARS = D["years"]
W = D["world"]
EXP = D["exporters"]
IMP = D["importers"]
EN = D["exporter_names"]
IN_ = D["importer_names"]
EUJ = D["eu_joined"]

# 欧盟并入 importers 序列（拼接）
IMP["E4"] = EUJ

def arr(src, cc, key):
    return [round(src[cc][str(y)][key], 1) for y in YEARS]

def warr(key):
    return [round(W[str(y)][key], 1) for y in YEARS]

stu = [round(W[str(y)]["176"] / W[str(y)]["126"] * 100, 1) for y in YEARS]
top4 = [D["top4_share"][str(y)] for y in YEARS]
exp_cons = [round(W[str(y)]["88"] / W[str(y)]["126"] * 100, 1) for y in YEARS]

# 其他出口国 = 世界出口 - 四强
others_exp = []
for i, y in enumerate(YEARS):
    we = W[str(y)]["88"]
    top = sum(EXP[cc][str(y)]["88"] for cc in ["BR", "TH", "AS", "IN"])
    others_exp.append(round(we - top, 1))

# 库存份额序列
stk_share_series = {}
for cc in ["BR", "TH", "IN", "CH"]:
    stk_share_series[cc] = [round(EXP.get(cc, IMP.get(cc))[str(y)]["176"] / W[str(y)]["176"] * 100, 1) for y in YEARS]
stk_others = [round(100 - sum(stk_share_series[cc][i] for cc in stk_share_series), 1) for i in range(len(YEARS))]

payload = {
    "years": YEARS,
    "world": {k: warr(k) for k in ["28", "126", "88", "57", "176"]},
    "stu": stu, "exp_cons": exp_cons, "top4": top4,
    "br": {k: arr(EXP, "BR", k) for k in ["28", "126", "88", "176"]},
    "th": {k: arr(EXP, "TH", k) for k in ["28", "126", "88", "176"]},
    "th_std": [D["thai_std"][str(y)] for y in YEARS],
    "in": {k: arr(EXP, "IN", k) for k in ["28", "126", "88", "176"]},
    "as": {k: arr(EXP, "AS", k) for k in ["28", "126", "88", "176"]},
    "ch": {k: arr(IMP, "CH", k) for k in ["28", "126", "57", "176"]},
    "id": {k: arr(IMP, "ID", k) for k in ["28", "126", "57", "176"]},
    "us": {k: arr(IMP, "US", k) for k in ["28", "126", "57", "176"]},
    "e4": {k: arr(IMP, "E4", k) for k in ["28", "126", "57", "88", "176"]},
    "exp_stack": {
        "BR": arr(EXP, "BR", "88"), "TH": arr(EXP, "TH", "88"),
        "IN": arr(EXP, "IN", "88"), "AS": arr(EXP, "AS", "88"), "OTH": others_exp},
    "stk_share": {**stk_share_series, "OTH": stk_others},
}

def tbl_exporter(cc):
    s = EXP[cc]
    def row(y):
        d = s[str(y)]
        return f"<tr><td>{cc} {EN[cc]}</td><td class='num'>{d['28']:,.0f}</td><td class='num'>{d['126']:,.0f}</td><td class='num'>{d['88']:,.0f}</td><td class='num'>{d['57']:,.0f}</td><td class='num'>{d['176']:,.0f}</td></tr>"
    return "".join(row(y) for y in [2000, 2006, 2012, 2018, 2026])

def tbl_importer(cc):
    s = IMP[cc]
    def row(y):
        d = s[str(y)]
        selfs = d["28"] / d["126"] * 100 if d["126"] else 0
        return f"<tr><td>{cc} {IN_.get(cc, '欧盟')}</td><td class='num'>{d['28']:,.0f}</td><td class='num'>{d['126']:,.0f}</td><td class='num'>{selfs:.0f}%</td><td class='num'>{d['57']:,.0f}</td><td class='num'>{d['176']:,.0f}</td></tr>"
    return "".join(row(y) for y in [2000, 2006, 2012, 2018, 2026])

exp_rows = "".join(tbl_exporter(cc) for cc in ["BR", "TH", "AS", "IN", "GT", "MX", "SF", "CO", "WZ", "CU", "AR"])
imp_rows = "".join(tbl_importer(cc) for cc in ["ID", "CH", "US", "E4", "MY", "KS", "BG", "RS", "AG", "NI", "SA", "JA"])

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>94 · 白糖可贸易国家全景 2000-2026 · 2026-09-14</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{{--oi-blue:#0072B2; --oi-orange:#E69F00; --oi-verm:#D55E00; --oi-green:#009E73;
        --oi-sky:#56B4E9; --oi-purple:#CC79A7; --oi-yellow:#F0E442; --oi-black:#000000;
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
  .red{{color:#b2182b;}} .green{{color:#1a7a3a;}} .blue{{color:#0072B2;}} .orange{{color:#b47400;}}
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
  .chart{{width:100%;height:360px;}}
  .chart-sm{{width:100%;height:300px;}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
  .footer{{margin-top:34px;padding:16px 20px;background:var(--ref-bg);border-radius:10px;font-size:12px;color:var(--sub);}}
  code{{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px;}}
  ul{{padding-left:22px;}} li{{margin:4px 0;}}
  @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr);}}.grid2{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>白糖可贸易国家全景（2000–2026）：产量、消费、出口、库存的四国格局与一次结构性断裂</h1>
    <div class="meta">报告编号 94 ｜ 数据源：USDA FAS PSD（2026-09-11 快照，本地 psd_alldata.csv）｜ 单位：千吨·原糖当量（raw value）｜ 2026-09-14</div>
    <div class="sub">结论一句话：<b>
    2000 年以来全球糖产量 +41%、消费 +38%，但出口 +63%——贸易占消费比重从 29.4% 升至 34.5%（2020 峰值 37.2%），糖正变得"更可贸易"；
    同时出口极度集中化：<b>前四国（巴西/泰国/印度/澳大利亚）出口份额 40.5% → 75.1%</b>，巴西一家占 54%。
    格局内最大的结构性变化有三处：<b>①巴西成为"零库存出口机器"（传导率 102%、库存占世界 0.5%）；②泰国 MY2019/20 起库存异常累积（存/用 11% → 145%，占世界库存 30.3%）——全球最大一笔"不可自由交易"的库存；③印度产量 +64% 几乎全部被国内消费吸收（传导率 −1.4%），出口是政策驱动的锯齿变量（放大倍数 9.3 倍）</b>。
    进口端，印尼已超越中国成为全球第一大进口国（消费 7.25 Mt、自给率仅 34.5%）。
    </b></div>
  </div>

  <div class="cards">
    <div class="kcard"><div class="lab">贸易/消费比重（2026）</div><div class="val">34.5%</div>
      <div class="note">2000 年 29.4% ｜ 2020 峰值 37.2%</div></div>
    <div class="kcard"><div class="lab">前四出口国份额</div><div class="val">75.1%</div>
      <div class="note">2000 年 40.5% ｜ 巴西独占 53.9%</div></div>
    <div class="kcard"><div class="lab">全球库消比 STU（2026）</div><div class="val">24.6%</div>
      <div class="note">2000 年 30.6% ｜ 2009 低点 17.8%</div></div>
    <div class="kcard"><div class="lab">泰国库存 / 世界库存</div><div class="val red">30.3%</div>
      <div class="note">2000 年 1.4% ｜ 存/用 144.7%（异常）</div></div>
  </div>

  <h2>一、全球盘子：产量、消费、贸易、库存的 26 年</h2>
  <div class="panel">
    <div id="c1" class="chart"></div>
    <div class="src">世界合计 = PSD 分国加总（skill 实测与官方 world 端点差额为 0）。产量/消费为柱与线（左轴，千吨），期末库存为面积（右轴），STU 库消比 = 期末库存 ÷ 总消费(126)（右轴，%）。</div>
  </div>
  <div class="panel">
    <h3>三个层级的读数</h3>
    <table>
      <tr><th>层级</th><th class="num">2000</th><th class="num">2010</th><th class="num">2020</th><th class="num">2026</th><th class="num">26年变化</th></tr>
      <tr><td>产量（千吨）</td><td class="num">130,764</td><td class="num">162,100</td><td class="num">180,262</td><td class="num">184,854</td><td class="num">+41.4%</td></tr>
      <tr><td>总消费 126（千吨）</td><td class="num">130,392</td><td class="num">156,188</td><td class="num">172,150</td><td class="num">180,536</td><td class="num">+38.4%</td></tr>
      <tr><td>出口（千吨）</td><td class="num">38,315</td><td class="num">53,939</td><td class="num">63,971</td><td class="num">62,324</td><td class="num">+62.7%</td></tr>
      <tr><td>期末库存（千吨）</td><td class="num">39,869</td><td class="num">28,781</td><td class="num">49,615</td><td class="num">44,410</td><td class="num">+11.4%</td></tr>
      <tr><td>贸易/消费</td><td class="num">29.4%</td><td class="num">34.5%</td><td class="num">37.2%</td><td class="num">34.5%</td><td class="num">+5.1pct</td></tr>
      <tr><td>库消比 STU</td><td class="num">30.6%</td><td class="num">18.4%</td><td class="num">28.8%</td><td class="num">24.6%</td><td class="num">−6.0pct</td></tr>
    </table>
    <ul>
      <li><b>出口增速 &gt; 消费增速</b>（+63% vs +38%）：糖的贸易依存度在 26 年里系统性上升，"可贸易"属性在增强——但 2020 年 37.2% 之后连续回落，贸易扩张已见顶。</li>
      <li><b>库存增速 &lt; 消费增速</b>（+11% vs +38%）：全球库存相对消费持续变薄（STU 30.6% → 24.6%）。这与 90 号报告"2021/22–2024/25 连续去库 4 年"一致。</li>
      <li><b>2008–2009 与 2019–2020 是两次明显的去库脉冲</b>（STU 分别触 19.2%/17.8% 和 27.4%→28.8% 回落段），对应两轮糖价周期。</li>
    </ul>
  </div>

  <h2>二、出口端：四国集中化与三种截然不同的出口模式</h2>
  <div class="panel">
    <div id="c2" class="chart"></div>
    <div class="src">世界出口构成（堆积面积，千吨）＋ 前四国份额（右轴虚线，%）。"其他"含危地马拉、墨西哥、南非、哥伦比亚、斯威士兰、阿根廷等。</div>
  </div>

  <div class="panel">
    <h3>2.1 巴西：零库存出口机器（传导率 102%）</h3>
    <div class="grid2">
      <div id="c_br" class="chart-sm"></div>
      <div>
        <table>
          <tr><th></th><th class="num">2000</th><th class="num">2026</th><th class="num">变化</th></tr>
          <tr><td>产量</td><td class="num">17,100</td><td class="num">42,500</td><td class="num red">+148%</td></tr>
          <tr><td>国内消费</td><td class="num">9,250</td><td class="num">9,000</td><td class="num green">−3%</td></tr>
          <tr><td>出口</td><td class="num">7,700</td><td class="num">33,600</td><td class="num red">+336%</td></tr>
          <tr><td>期末库存</td><td class="num">860</td><td class="num">221</td><td class="num green">−74%</td></tr>
          <tr><td>出口/产量</td><td class="num">45.0%</td><td class="num">79.1%</td><td class="num">—</td></tr>
          <tr><td>库存/世界库存</td><td class="num">2.2%</td><td class="num">0.5%</td><td class="num">—</td></tr>
        </table>
        <ul>
          <li><b>2000→2026 产量增量 +25,400 千吨，净出口增量 +25,900 千吨，传导率 102%</b>——巴西增产几乎 1:1 变成可贸易量，国内消费 26 年原地踏步（乙醇分流 + 消费饱和）。</li>
          <li>库存常年 &lt;100 万吨（2005–2009 出现 −285～−1,135 的负值，属 PSD 历史段记账瑕疵，已按惯例标注）：<b>巴西不囤货，是即产即运的流量型出口国</b>。</li>
          <li>含义：巴西减产的冲击<b>直接打进世界市场</b>（放大倍数仅 1.3 倍），没有任何库存缓冲可以吸收。</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="panel">
    <h3>2.2 泰国：从"第二出口国"到"全球库存池"（MY2019/20 断裂）</h3>
    <div class="grid2">
      <div id="c_th" class="chart-sm"></div>
      <div>
        <table>
          <tr><th></th><th class="num">2000</th><th class="num">2017峰值</th><th class="num">2026</th></tr>
          <tr><td>产量</td><td class="num">5,107</td><td class="num">14,710</td><td class="num">9,500</td></tr>
          <tr><td>出口</td><td class="num">3,394</td><td class="num">10,907</td><td class="num">6,000</td></tr>
          <tr><td>期末库存</td><td class="num">571</td><td class="num">6,841</td><td class="num red">13,454</td></tr>
          <tr><td>存/用 STD（含出口）</td><td class="num">11.1%</td><td class="num">—</td><td class="num red">144.7%</td></tr>
        </table>
        <ul>
          <li>2019/20 干旱（产量 14,581→7,587）后，<b>出口从未回到 10 Mt 台阶（2026 仅 6.0），库存却从 570 万吨一路堆到 1,345 万吨</b>——占世界库存 30.3%（2000 年仅 1.4%）。</li>
          <li>FAS 官方定性（2026-04 年报）：这是糖厂<b>真实持有、刻意维持</b>的库存（远超 OCSB 20 万吨安全线），但<b>"不是可自由交易的盈余"</b>——用于远期出口合同的定价筹码和对冲雨养甘蔗的产量波动。<b>同时它也是平衡表残差项</b>：FAS 两个官方来源对 MY2025/26 出口估计差 1 Mt，差额恰好全部落在库存上。</li>
          <li><b>含义：全球 44.4 Mt 库存里最大的一笔（13.5 Mt）对价格不敏感、不能指望释放</b>——"看全球库存总量"会系统性高估可用缓冲（91 号报告的核心论点的国别证据）。</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="panel">
    <h3>2.3 印度：产量 +64% 全被国内吃掉，出口是政策锯齿（放大倍数 9.3 倍）</h3>
    <div class="grid2">
      <div id="c_in" class="chart-sm"></div>
      <div>
        <table>
          <tr><th>出口制度阶段</th><th>区间</th><th class="num">出口范围（千吨）</th></tr>
          <tr><td>自给自足/禁出口</td><td>2003–2004、2008–2009</td><td class="num">40–250</td></tr>
          <tr><td>补贴出口窗口</td><td>2007、2010–2015</td><td class="num">1,260–6,014</td></tr>
          <tr><td>大出口期</td><td>2017–2022</td><td class="num">2,236–11,548</td></tr>
          <tr><td>收紧回落</td><td>2023–2026</td><td class="num">3,500–3,966</td></tr>
        </table>
        <ul>
          <li>产量 20,480→33,600（+64%），消费 17,845→31,000（+74%）——<b>消费增长快于产量，26 年净出口增量 ≈ 0（传导率 −1.4%）</b>。印度增产对世界市场<b>几乎没有贡献</b>。</li>
          <li>出口完全跟随政策（补贴/配额/禁令）：2021 峰值 11.5 Mt → 2026 仅 3.6 Mt。<b>出口/产量仅 10.7%，放大倍数 9.3 倍</b>——印度产量波动 1%，其出口须波动 9.3% 才能平衡，是四国中边际定价权重最高、但供给最不可靠的一环。</li>
          <li>库存 6,506（14.6% 世界份额）受出口政策直接支配，属"政策性库存"层。</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="panel">
    <h3>2.4 澳大利亚与第二梯队：小而稳的原糖出口带</h3>
    <div class="grid2">
      <div id="c_as" class="chart-sm"></div>
      <div>
        <ul>
          <li><b>澳大利亚</b>：产量 26 年稳定在 3,700–5,300 千吨区间，<b>出口/产量 86.3%</b>——典型的"种植即出口"结构，库存极薄（91 万吨）。产量受天气（QLD 降雨/Cyclone）驱动，是全球贸易流中可预测性最高的增量。</li>
          <li><b>第二梯队（各 1–3 Mt）</b>：危地马拉（+68% 出口，中南美精炼枢纽）、墨西哥（2000 净出口 155 → 2026 949，波动大）、斯威士兰（出口/产量 81%，依赖 EU 特惠市场）、哥伦比亚、南非、阿根廷。</li>
          <li><b>古巴是 26 年最大塌方</b>：出口 2,932 → <b>0</b>（2026，产量 3,500 → 100）。2000 年古巴还是世界第四大出口国，如今完全退出——这是"前四份额从 40.5% 升到 75.1%"的另一面：不是四强变强，<b>是长尾塌了 + 巴西独大</b>。</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="callout">
    <b>出口端小结——三种模式与一个塌方：</b>
    ① <b>巴西 = 流量型</b>（增产即出口、零库存、放大 1.3 倍）；
    ② <b>泰国 = 断裂型</b>（2019/20 后出口退坡、库存堆积成"死库存"）；
    ③ <b>印度 = 政策型</b>（产量增量不出口，出口跟着补贴/禁令锯齿，放大 9.3 倍）；
    ④ <b>古巴 = 塌方</b>（293 万吨 → 0）。世界市场的边际供给 = 巴西的天气与糖醇比 + 印度的政策 + 澳大利亚的气候，<b>泰国已经不在边际供给名单里</b>。
  </div>

  <h2>三、进口端：印尼登顶、中国筑底、欧盟转性</h2>
  <div class="panel">
    <div id="c3" class="chart"></div>
    <div class="src">四大进口方进口量（千吨）。欧盟 2000–2003 为 EU-15、2004–05 为 EU-25、2006 起 EU-27 口径（PSD 分段代码 E2/E3/E4 拼接）。</div>
  </div>
  <div class="panel">
    <div class="grid2">
      <div>
        <h3>3.1 印尼：全球第一大进口国</h3>
        <ul>
          <li>消费 3,300 → 7,250（<b>+120%</b>，增速全球主要经济体最快），自给率仅 <b>34.5%</b> 且持续下滑。</li>
          <li>进口 1,591 → 4,200，2020 峰值 6,124。<b>进口刚性 = 人口 + 人均消费升级 + 产量停滞（1,800→2,500）</b>，是国际贸易流中最稳定的"底仓买盘"。</li>
        </ul>
        <h3>3.2 中国：高库存 + 高进口并存的"政策市"</h3>
        <ul>
          <li>消费 8,650 → 16,750（+94%），产量 6,849 → 12,700，自给率 79% → 76%——<b>维持了四分之三自给</b>，靠配额+关税（配额内 15%）调节。</li>
          <li>进口 1,083 → 5,450（2020 峰值 6,379）；库存 1,004 → 4,023，<b>2014–15 峰值 10,391（世界库存 22%）</b>——国储糖收/抛储周期主导，库存与进口同向放大，是价格的"政策缓冲垫"。</li>
        </ul>
      </div>
      <div>
        <h3>3.3 欧盟：从净出口到净进口的结构转折</h3>
        <ul>
          <li>2000 年（EU-15）出口 6,607、净出口 +4,768；<b>2006 年糖业改革后出口断崖至 2,439</b>；2026 年出口 858、进口 2,550——<b>净进口 −1,692</b>。甜菜糖产量 18,519 → 14,353（−23%）。</li>
          <li>这是 26 年里进口端最大的制度性变化：欧盟从"世界第二大出口方"变成常量净进口方，<b>净减少全球贸易供给约 5–6 Mt</b>，与巴西增产在时间上接力。</li>
        </ul>
        <h3>3.4 其余进口方：自给率两极</h3>
        <ul>
          <li><b>完全依赖进口</b>（自给≈0）：马来西亚、韩国、阿尔及利亚、尼日利亚（产量可忽略）、沙特（精炼再出口模式）；<b>孟加拉国 1.8%</b>。</li>
          <li><b>俄罗斯是唯一反转者</b>：2000 年进口 1,550（当时全球前列）→ 2026 年 10，自给率 108.7%——甜菜糖复兴使其彻底退出进口市场，<b>又净减约 1.5 Mt 需求</b>。</li>
          <li>美国：自给率 71%，配额体系（TRQ）+ 墨西哥协定固定了进口结构（2,957），26 年几乎不变。</li>
        </ul>
      </div>
    </div>
  </div>

  <h2>四、库存的地理：谁拿着这 4,440 万吨？</h2>
  <div class="panel">
    <div id="c4" class="chart"></div>
    <div class="src">期末库存份额（% 世界库存）。巴西/泰国/印度/中国四国 + 其他。</div>
    <ul>
      <li><b>2000 年</b>：库存分散在进口国与印度（印度 30%、中国 2.5%、泰国 1.4%、巴西 2.2%）；</li>
      <li><b>2026 年</b>：泰国 30.3% + 印度 14.6% + 中国 9.1% = <b>54% 集中在三国</b>，其中泰国一笔就超过全部进口国库存之和（进口国 12 国合计 9,565 = 21.5%）。</li>
      <li><b>可动用性分层</b>（沿用 91 号报告框架）：泰国 13.5 Mt = 价格不敏感层；印度 6.5 Mt = 政策层；中国 4.0 Mt = 国储层；<b>真正市场化的净出口国库存（巴西+澳洲+危地马拉等）仅约 1.3 Mt ≈ 世界消费 2.6 天</b>。</li>
    </ul>
  </div>

  <div class="panel">
    <h3>4.1 泰国异常的精确刻画</h3>
    <div id="c5" class="chart"></div>
    <div class="src">泰国存/用 STD = 期末库存 ÷（总消费+出口），%。虚线 = 1.0（100%）警戒线。2019/20 前序列与印度、巴西同量级（0.27–0.64），之后水平跃迁脱钩。</div>
    <div class="warn">
      <b>口径警示：</b>泰国库存是平衡表残差项，水平精度不足（FAS 两个官方来源对同一市场年出口估计差 1 Mt、全部落在库存）。本报告所有涉及泰国库存的数字应视为"量级正确、水平存疑"。剔除泰国后全球 STU 口径会从 24.6% 降至约 17.5%——<b>全球库存叙事对该国的处理方式高度敏感</b>。
    </div>
  </div>

  <h2>五、结论（四段式）</h2>
  <div class="panel">
    <h3>[前提/背景校验]</h3>
    <ul>
      <li>数据源为 USDA FAS PSD 糖平衡表（0612000，2026-09-11 快照），151 国 × 2000–2026 共 27 个市场年，主 要国家恒等式校验 <b>0 处不平</b>（期初+产+进 = 总供给 = 总分配 = 消费+出+期末）。</li>
      <li>消费一律取 126（Total Disappearance）；单位千吨·原糖当量。MY2026 为预测值；分国市场年窗口不同（巴西 4–3 月 / 中印 10–9 月 / 泰国 12–11 月），跨年水平对比影响有限，时滞分析会有约 8 个月最大错位。</li>
      <li>巴西 2005–2009 期末库存负值（−285～−1,135）为 PSD 历史段记账瑕疵，不影响流量字段（产/消/出口）。</li>
    </ul>
    <h3>[关键数据与依据]</h3>
    <ul>
      <li>贸易/消费 29.4% → 34.5%（2020 峰 37.2%）；前四出口国份额 40.5% → 75.1%；巴西出口份额 20.1% → 53.9%。</li>
      <li>传导率（Δ净出口/Δ产量，2000→2026）：巴西 102%、泰国 59%、印度 −1.4%、澳大利亚（产量持平，净出口 +544）。</li>
      <li>放大倍数（1 ÷ 出口/产量，MY2026）：印度 9.3x、泰国 1.6x、巴西 1.3x、澳大利亚 1.2x。</li>
      <li>泰国 STD：11.1%（2000）→ 144.7%（2026），MY2019/20 水平跃迁；占世界库存 30.3%。</li>
      <li>进口端：印尼进口 4,200（第一大）、中国 5,450（含政策性脉冲）、欧盟净进口 −1,692（2006 转折）、俄罗斯归零。</li>
    </ul>
    <h3>[客观分析与对比]</h3>
    <ul>
      <li>与 91 号报告互证："全球库存总量"里 54% 在三个对价格不敏感/政策主导的国家手里，市场化缓冲极薄（净出口国库存 ≈ 2.6 天消费）——<b>总量指标系统性高估缓冲</b>。</li>
      <li>与 90 号报告互证：STU 24.6% 处于历史中低分位，但剔除泰国后仅 ~17.5%（剔泰+剔中 ~16.8%，历史最低区间）——<b>"紧不紧"取决于你信不信泰国的 1,345 万吨</b>。</li>
      <li>与棉花 93 号对比：糖的出口集中度（75%）显著高于棉花三硬格局，但糖有巴西这一个"零库存高传导"的单一支点，而棉花的缓冲分散在多国——糖的供给冲击传导更陡。</li>
    </ul>
    <h3>[结论与置信度]</h3>
    <ul>
      <li><b>高置信</b>：出口集中化（40.5→75.1%）、巴西流量型出口模式（传导率 ~100%、库存清零）、印尼登顶第一进口国、欧盟 2006 转净进口、古巴退出出口。</li>
      <li><b>中置信</b>：泰国库存的精确水平（残差项 + vintage 差异），但其"不可自由交易"的定性有 FAS 官方文字背书；印度出口的政策锯齿归因。</li>
      <li><b>低置信/未核实</b>：第二梯队国家（斯威士兰、危地马拉等）的年度精度；MY2026 各国为 FAS 预测值，尚未实现。</li>
      <li><b>跟踪节点</b>：印度 2026/27 出口政策（是否恢复配额）；泰国出口能否回到 8 Mt（验证库存释放意愿）；巴西 2027 制糖比。</li>
    </ul>
  </div>

  <h2>附录 A · 分国平衡表总表（千吨·原糖当量）</h2>
  <div class="panel">
    <h3>A1 主要出口国（产量 / 消费 / 出口 / 进口 / 期末库存）</h3>
    <table>
      <tr><th>国家</th><th class="num">产量</th><th class="num">消费</th><th class="num">出口</th><th class="num">进口</th><th class="num">期末库存</th></tr>
      {exp_rows}
    </table>
    <div class="src">年份列为 2000 / 2006 / 2012 / 2018 / 2026（MY 标签）。巴西 2005–2009 库存负值为源数据瑕疵。</div>
  </div>
  <div class="panel">
    <h3>A2 主要进口国（产量 / 消费 / 自给率 / 进口 / 期末库存）</h3>
    <table>
      <tr><th>国家</th><th class="num">产量</th><th class="num">消费</th><th class="num">自给率</th><th class="num">进口</th><th class="num">期末库存</th></tr>
      {imp_rows}
    </table>
  </div>

  <div class="footer">
    <b>口径与数据说明</b><br>
    · 数据源：USDA FAS PSD Open Data，商品 0612000（Sugar, Centrifugal），本地快照 psd_alldata.csv（2026-09-11 下载）。<br>
    · 消费用属性 126（Total Disappearance = 139 Human Dom. + 151 Other）；库存消费比 STU = 176/126；分国库存覆盖倍数 STD = 176/(126+88)。<br>
    · 欧盟序列拼接：E2（EU-15，≤2003）/ E3（EU-25，2004–05）/ E4（EU-27，≥2006）。<br>
    · MY2026 为预测值（FAS 2026-05 半年报 vintage）；历史年为最后一次批量修订值。市场年窗口分国不同（正文第五节）。<br>
    · 本报告为数据事实梳理，不构成投资建议。
  </div>
</div>

<script>
const P = {json.dumps(payload, ensure_ascii=False)};
const Y = P.years;
const C = {{blue:'#0072B2',orange:'#E69F00',verm:'#D55E00',green:'#009E73',sky:'#56B4E9',purple:'#CC79A7',yellow:'#E6B800',grey:'#8a97a8'}};
const axis = {{axisLine:{{lineStyle:{{color:'#c9d4e0'}}}},axisLabel:{{color:'#5a6a7d'}},splitLine:{{lineStyle:{{color:'#eef2f7'}}}}}};
function mk(id,opt){{const el=document.getElementById(id);if(!el)return;const ch=echarts.init(el);ch.setOption(opt);window.addEventListener('resize',()=>ch.resize());}}
const tip={{trigger:'axis',valueFormatter:v=>v==null?'-':v.toLocaleString()}};

// C1 世界
mk('c1',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:60,right:64,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'千吨',max:200000,...axis}},{{type:'value',name:'%',min:10,max:45,...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'产量',type:'bar',data:P.world['28'],itemStyle:{{color:C.sky,opacity:.55}},barWidth:'46%'}},
    {{name:'总消费',type:'line',data:P.world['126'],lineStyle:{{width:2.5,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'none'}},
    {{name:'期末库存',type:'line',yAxisIndex:1,data:P.world['176'],areaStyle:{{opacity:.12,color:C.orange}},lineStyle:{{width:2,color:C.orange,type:'dashed'}},itemStyle:{{color:C.orange}},symbol:'none'}},
    {{name:'库消比STU%',type:'line',yAxisIndex:1,data:P.stu,lineStyle:{{width:2,color:C.verm}},itemStyle:{{color:C.verm}},symbol:'none'}}
  ]
}});

// C2 出口堆积
mk('c2',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:60,right:64,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'千吨',...axis}},{{type:'value',name:'前四份额%',min:30,max:80,...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'巴西',type:'line',stack:'exp',data:P.exp_stack.BR,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.blue}}}},
    {{name:'泰国',type:'line',stack:'exp',data:P.exp_stack.TH,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.orange}}}},
    {{name:'印度',type:'line',stack:'exp',data:P.exp_stack.IN,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.green}}}},
    {{name:'澳大利亚',type:'line',stack:'exp',data:P.exp_stack.AS,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.purple}}}},
    {{name:'其他',type:'line',stack:'exp',data:P.exp_stack.OTH,areaStyle:{{opacity:.5}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.grey}}}},
    {{name:'前四国份额%',type:'line',yAxisIndex:1,data:P.top4,lineStyle:{{width:2,color:C.verm,type:'dashed'}},itemStyle:{{color:C.verm}},symbol:'none'}}
  ]
}});

// 四国小图
function small(id, name, prod, cons, exp, stk, imp){{
  const s=[{{name:'产量',type:'line',data:prod,lineStyle:{{width:2.2,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'none'}},
    {{name:'消费',type:'line',data:cons,lineStyle:{{width:2.2,color:C.purple}},itemStyle:{{color:C.purple}},symbol:'none'}},
    {{name:'出口',type:'line',data:exp,lineStyle:{{width:2.2,color:C.orange}},itemStyle:{{color:C.orange}},symbol:'none'}}];
  if(imp) s.push({{name:'进口',type:'line',data:imp,lineStyle:{{width:2,color:C.sky,type:'dashed'}},itemStyle:{{color:C.sky}},symbol:'none'}});
  s.push({{name:'期末库存',type:'bar',data:stk,itemStyle:{{color:'#b9c6d4',opacity:.7}},barWidth:'42%'}});
  mk(id,{{tooltip:tip,legend:{{top:0,itemWidth:14,textStyle:{{fontSize:11,color:'#1a2330'}}}},grid:{{left:56,right:16,top:34,bottom:28}},
    xAxis:{{type:'category',data:Y,axisLabel:{{color:'#5a6a7d',interval:5}}}},yAxis:{{type:'value',name:'千吨',...axis}},series:s}});
}}
small('c_br','巴西',P.br['28'],P.br['126'],P.br['88'],P.br['176']);
small('c_th','泰国',P.th['28'],P.th['126'],P.th['88'],P.th['176']);
small('c_in','印度',P.in['28'],P.in['126'],P.in['88'],P.in['176']);
small('c_as','澳大利亚',P.as['28'],P.as['126'],P.as['88'],P.as['176']);

// C3 进口
mk('c3',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:60,right:24,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:{{type:'value',name:'进口 千吨',...axis}},
  series:[
    {{name:'印尼',type:'line',data:P.id['57'],lineStyle:{{width:2.4,color:C.verm}},itemStyle:{{color:C.verm}},symbol:'none'}},
    {{name:'中国',type:'line',data:P.ch['57'],lineStyle:{{width:2.4,color:C.verm,type:'dashed'}},itemStyle:{{color:'#e37722'}},symbol:'none'}},
    {{name:'欧盟',type:'line',data:P.e4['57'],lineStyle:{{width:2.2,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'none'}},
    {{name:'美国',type:'line',data:P.us['57'],lineStyle:{{width:2.2,color:C.purple}},itemStyle:{{color:C.purple}},symbol:'none'}}
  ]
}});

// C4 库存份额
mk('c4',{{
  tooltip:tip, legend:{{top:0,textStyle:{{color:'#1a2330'}}}},
  grid:{{left:56,right:24,top:36,bottom:40}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:{{type:'value',name:'占世界库存 %',max:100,...axis}},
  series:[
    {{name:'泰国',type:'line',stack:'ss',data:P.stk_share.TH,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.orange}}}},
    {{name:'印度',type:'line',stack:'ss',data:P.stk_share.IN,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.green}}}},
    {{name:'中国',type:'line',stack:'ss',data:P.stk_share.CH,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.verm}}}},
    {{name:'巴西',type:'line',stack:'ss',data:P.stk_share.BR,areaStyle:{{opacity:.85}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.blue}}}},
    {{name:'其他',type:'line',stack:'ss',data:P.stk_share.OTH,areaStyle:{{opacity:.45}},lineStyle:{{width:0}},symbol:'none',itemStyle:{{color:C.grey}}}}
  ]
}});

// C5 泰国 STD
mk('c5',{{
  tooltip:tip,
  grid:{{left:60,right:60,top:30,bottom:40}},
  xAxis:{{type:'category',data:Y,...axis}},
  yAxis:[{{type:'value',name:'存/用 %',...axis}},{{type:'value',name:'千吨',...axis,splitLine:{{show:false}}}}],
  series:[
    {{name:'泰国 存/用 STD%',type:'bar',data:P.th_std,itemStyle:{{color:C.orange,opacity:.8}},barWidth:'55%',
      markLine:{{silent:true,symbol:'none',lineStyle:{{color:'#b2182b',type:'dashed'}},data:[{{yAxis:100,label:{{formatter:'100% 警戒线',color:'#b2182b'}}}}]}}}},
    {{name:'期末库存',type:'line',yAxisIndex:1,data:P.th['176'],lineStyle:{{width:2,color:C.blue}},itemStyle:{{color:C.blue}},symbol:'none'}},
    {{name:'出口',type:'line',yAxisIndex:1,data:P.th['88'],lineStyle:{{width:2,color:C.green,type:'dashed'}},itemStyle:{{color:C.green}},symbol:'none'}}
  ]
}});
</script>
</body>
</html>"""

out_dir = os.path.join(BASE, "reports", "94_白糖可贸易国家全景_2000_2026")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print("saved:", os.path.join(out_dir, "index.html"), len(HTML), "bytes")
