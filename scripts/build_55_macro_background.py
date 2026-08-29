#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""55 号报告：宏观背景（蓝筹股池索引 + US10Y-US02Y 利差分阶段分析 + Jackson Hole 2026 Warsh 发言更新）
数据源：data/blue_chips.csv（蓝筹池）、data/us_treasury/DGS2.csv + DGS10.csv（FRED 至 2026-08-26）、
        交接文档_JacksonHole2026_Warsh讲话与美债利差.md、54 号报告、2026-08-28 收盘报道（WebSearch 多源）
产物：reports/55_宏观背景/index.html
"""
import csv, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, 'reports', '55_宏观背景')
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 1. FRED 数据（2026 年日频） ----------
def load_fred(path):
    d = {}
    with open(path) as f:
        for r in csv.reader(f):
            if len(r) >= 2 and r[0][:4] == '2026' and r[1].strip() not in ('', '.'):
                try:
                    d[r[0].strip()] = float(r[1].strip())
                except ValueError:
                    pass
    return d

d2 = load_fred(os.path.join(BASE, 'data/us_treasury/DGS2.csv'))
d10 = load_fred(os.path.join(BASE, 'data/us_treasury/DGS10.csv'))
alld = sorted(set(d2) & set(d10))
dates, y2, y10, sp = [], [], [], []
for dd in alld:
    dates.append(dd)
    y2.append(d2[dd]); y10.append(d10[dd]); sp.append(round(d10[dd] - d2[dd], 4))
chart_data = {'dates': dates, 'y2': y2, 'y10': y10, 'sp': sp}

# ---------- 2. 蓝筹股池 ----------
rows = list(csv.DictReader(open(os.path.join(BASE, 'data/blue_chips.csv'), encoding='utf-8-sig')))
SECTORS = ['Technology', 'Financials', 'Industrials', 'Healthcare', 'Consumer', 'Materials_Utilities_Other']
SECTOR_CN = {
    'Technology': '科技', 'Financials': '金融', 'Industrials': '工业',
    'Healthcare': '医疗健康', 'Consumer': '消费', 'Materials_Utilities_Other': '材料/公用/其他',
}
sector_tickers = {k: [r['ticker'] for r in rows if r['sector'] == k] for k in SECTORS}
n_total = len(rows)

# ---------- 3. 渲染 ----------
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>55 · 宏观背景（蓝筹池索引 + US10Y−US02Y 利差 + Jackson Hole 2026）</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
:root{--bg:#ffffff;--fg:#1a1a1a;--muted:#666;--line:#e5e5e5;--accent:#185FA5;--red:#D55E00;--green:#009E73;--card:#f7f8fa;--okb:#0072B2;--okc:#E69F00;--okr:#D55E00;--okg:#009E73;--okp:#CC79A7}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--fg);line-height:1.7;padding:32px 20px 60px}
.wrap{max-width:1080px;margin:0 auto}
h1{font-size:26px;font-weight:700;letter-spacing:.5px;margin-bottom:6px}
.sub{color:var(--muted);font-size:13px;margin-bottom:22px}
h2{font-size:20px;font-weight:600;margin:38px 0 14px;padding-left:12px;border-left:4px solid var(--accent)}
h3{font-size:16px;font-weight:600;margin:22px 0 10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}
th{background:#f0f1f3;font-weight:600;white-space:nowrap}
.up{color:var(--red);font-weight:600}.down{color:var(--green);font-weight:600}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;margin-left:6px}
.sig{background:#fde8e8;color:#A32D2D}.edge{background:#fdf3e0;color:#854F0B}.no{background:#eef0f2;color:#666}
.badge{display:inline-block;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:600;margin-right:8px}
.b-hi{background:#fde8e8;color:#A32D2D}.b-mid{background:#fdf3e0;color:#854F0B}.b-lo{background:#e8f5ee;color:#0F6E56}
.chart{width:100%;height:420px;margin:14px 0}
.note{font-size:12px;color:var(--muted);margin:6px 0 2px}
.exec{background:#fffbea;border:1px solid #f0dca0;border-radius:10px;padding:16px 20px;margin:16px 0}
.exec li{margin:6px 0}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.kv div{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.kv .k{font-size:12px;color:var(--muted)}.kv .v{font-size:17px;font-weight:700;margin-top:2px}
.legend{font-size:12px;color:var(--muted);margin-top:8px}
.warn{background:#fdf2f2;border:1px solid #f0c8c8;border-radius:8px;padding:12px 16px;font-size:13px;margin-top:10px}
.quote{background:#eef4fb;border-left:4px solid var(--accent);border-radius:0 8px 8px 0;padding:12px 16px;margin:12px 0;font-size:13.5px}
.foot{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
.tick{font-size:12px;line-height:1.9}
.ref{font-size:12.5px;color:#333}
.ref li{margin:5px 0}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
</style>
</head>
<body><div class="wrap">

<h1>宏观背景 · 蓝筹股池索引 + 美债利差分阶段分析 + Jackson Hole 2026</h1>
<div class="sub">背景文件 55 ｜ 2026-08-29 ｜ 数据：FRED 至 08-26、08-28 盘中/收盘为多源报道值 ｜ 体系：承接 54 号报告与交接文档（JH2026 Warsh 讲话与美债利差）</div>

<div class="exec">
<b>一页结论</b>
<ul>
<li><b>蓝筹股池</b>：用户自定义优质蓝筹 73 只（6 大行业，文件 <code>data/blue_chips.csv</code>），作为相关性 / 回测 / 对照基准的候选池；配套研究锚点 12 份报告（39/40/41/44 RSI 低位系列、31 区间下沿、34 道指超买、50 纳指区间低买、52 持仓组合等）。</li>
<li><b>US10Y−US02Y 最近开始扩大，主因是「长端供给 / 期限溢价」而非加息预期</b>：6/30 低点 +0.30 → 8/18 峰值 +0.52，扩张段 10Y +27bp vs 2Y 仅 +5bp（长端贡献约 84%）。四大推力＝财政天量供给（赤字 1.8 万亿、债务 40 万亿）、AI 巨头超长债分流（年内 2000 亿+）、通胀预期固化（PCE 3.7%、65 个月超 2%）、海外买盘萎缩（6 月外资持仓 −721 亿）。</li>
<li><b>8/28 Warsh 杰克逊霍尔首秀放鹰，驱动切换为「加息预期」，曲线由熊陡转熊平</b>：9 月加息概率 ~35%→55.7%~60%，2Y +8~10bp 至 4.29~4.31%，10Y 持平 4.67~4.69%，30Y 反跌（通胀信誉保全），利差收窄至 ~0.38。交接文档定性：约 8 成事件噪音、2 成趋势种子，<b>9 月初 8 月非农 + CPI 与 9/15–16 FOMC 是真分水岭</b>。</li>
<li><b>Jackson Hole 2026 发言更新</b>：Warsh（2026-05 上任，第 100 天）《In Our Time》——拒绝前瞻指引、拒绝机械反应函数、通胀为首要矛盾（"否则，我们就有工作要做"）、金融条件不紧、经济乐观；SPX +0.43%、道指 +0.38% 跑赢纳指 +0.22%，黄金 −0.6~2%、BTC −1.1%。</li>
</ul>
</div>

<h2>一、蓝筹股池索引（73 只 · 6 大行业）</h2>
<div class="card">
<p><b>池子定义</b>：用户自定义「优质蓝筹股清单」（2026-08-27 建池），存于 <code>data/blue_chips.csv</code>（列：ticker, sector）。用途＝相关性分析 / 回测 / 对照基准的<b>候选池</b>——后续任务直接读该文件即可，无需重复粘贴清单。</p>
<p><b>行业分布</b>：Technology 10 ｜ Financials 6 ｜ Industrials 11 ｜ Healthcare 12 ｜ Consumer 11 ｜ Materials/Utilities/Other 23，合计 <b>73</b> 只。</p>
</div>
<table>
<tr><th>行业</th><th>数量</th><th>标的代码</th></tr>
<tr><td>科技 Technology</td><td>10</td><td class="tick">MSFT, AAPL, GOOGL, CSCO, TXN, AVGO, ORCL, QCOM, ACN, IBM</td></tr>
<tr><td>金融 Financials</td><td>6</td><td class="tick">MA, V, AXP, BLK, JPM, BAC</td></tr>
<tr><td>工业 Industrials</td><td>11</td><td class="tick">CAT, DE, GE, ETN, HON, PH, ROK, TDG, UNP, FDX, UPS</td></tr>
<tr><td>医疗健康 Healthcare</td><td>12</td><td class="tick">LLY, NVO, REGN, ISRG, VRTX, MCK, JNJ, ABT, BDX, TMO, DHR, SYK</td></tr>
<tr><td>消费 Consumer</td><td>11</td><td class="tick">MCD, SBUX, NKE, HD, LOW, TJX, BKNG, CMG, ORLY, MAR, CPRT</td></tr>
<tr><td>材料/公用/其他</td><td>23</td><td class="tick">PCAR, WM, RSG, PG, KO, PEP, CL, KMB, GIS, HSY, MDLZ, COST, LMT, BRK.B, SPGI, ICE, AON, MMC, AJG, SO, DUK, NEE, AWK</td></tr>
</table>
<div class="note">注：BRK.B 为伯克希尔 B 类股；行业口径为池子自定义，非 GICS 严格分类。当前持仓（52 号）相关标的：ABBV/GILD（核心多）、CSCO/MCD/VST/APO（波段多）、SBUX/XYZ（空头）。</div>

<h3>1.2 蓝筹池研究锚点（历史报告索引）</h3>
<table>
<tr><th>报告</th><th>结论（一句话）</th></tr>
<tr><td><a href="../39_蓝筹RSI超卖买入/index.html">39 蓝筹RSI超卖买入</a></td><td>72 只蓝筹 RSI14 下穿 30 首日买入（5,275 事件）：T+20 +2.85%/胜率 63.8%，约为基率 2 倍；金融胜率最高（68.4%）、科技绝对收益最高（+3.83%）</td></tr>
<tr><td><a href="../40_蓝筹RSI支撑位买入/index.html">40 / <a href="../41_蓝筹RSI摆动低点支撑买入/index.html">41 RSI 支撑位系列</a></td><td>支撑位形态本身不给 edge，<b>真 edge 是「RSI 低位」本身</b>（40 号分位数口径错误已由 41 号纠正）</td></tr>
<tr><td><a href="../44_贴EMA20缩量跌破平台/index.html">44 贴EMA20缩量跌破平台</a></td><td>8,305 事件整体无 edge（T+20 +1.26% ≈ 基率 +1.42%）；缩量 vs 放量破位无差异</td></tr>
<tr><td><a href="../31_蓝筹区间下沿支撑_周线EMA20压制回测/index.html">31 区间下沿×周线EMA20压制</a></td><td>47 只低波动蓝筹 1,570 事件：压制不降胜率但抬升破位率；深死叉超跌反弹（T+60 +7.1%）</td></tr>
<tr><td><a href="../34_道指板块超买横向/index.html">34 道指板块超买横向</a></td><td>9 板块代表股 RSI 超买横比：9/9 先冲高再回吐，阶段分化因股而异</td></tr>
<tr><td><a href="../50_纳指区间RSI低买高卖/index.html">50 纳指区间 RSI 低买高卖</a></td><td>73 只蓝筹×103 交易日（2025-10~2026-02 横盘期）：RSI&lt;30 低买 T+10 +1.63%（胜率 62%），消费低买超额 +3.2pp 领跑、科技 −0.6%</td></tr>
<tr><td><a href="../52_持仓组合技术面与操作建议/index.html">52 持仓组合技术面</a></td><td>8 标的组合：核心多 ABBV/GILD + 波段多 CSCO/MCD/VST/APO + 空头 SBUX/XYZ；10Y−2Y 利差 6 月末 +27bp → 8 月末 +47bp 宏观佐证（本文档阶段分析承接）</td></tr>
<tr><td><a href="../54_宏观利率背景六股影响/index.html">54 宏观利率背景六股影响</a></td><td>利差扩张归因（期限溢价）+ 六股利率敏感度：SOFI ≫ MS &gt; APO ≈ ABBV ≈ JNJ ≈ CSCO（本文档二、三章的数据母体）</td></tr>
</table>

<h2>二、US10Y−US02Y 利差最近开始扩大：分阶段分析</h2>

<h3>2.1 分阶段全景（2026 年日频，FRED）</h3>
<div class="chart" id="c1"></div>
<div class="legend">2Y / 10Y 收益率（左轴 %）与 10Y−2Y 利差（右轴 %）｜ 阶段 ①扩张前（1 月 +0.72 高位 → 6/30 低点 +0.30）②扩张段（6/30→8/18，长端驱动熊陡）③回吐段（8/18→8/26）④Warsh 讲话后熊平（8/28 盘中估算 →~0.38）｜ 红系=利差上行（走阔），蓝系=收益率绝对水平</div>

<table>
<tr><th>阶段</th><th>区间</th><th>2Y(%)</th><th>10Y(%)</th><th>利差</th><th>主导驱动</th><th>形态</th></tr>
<tr><td><b>① 扩张前</b></td><td>1/2 → 6/30（上半年收窄段）</td><td>3.47→4.14</td><td>4.19→4.44</td><td>+0.72→<b>+0.30</b></td><td>年内高位 +0.72（1 月）单边收窄至 6 月末低点；短端上行（加息预期）+ 长端相对平稳</td><td>牛平</td></tr>
<tr><td><b>② 扩张段</b></td><td>6/30 → 8/18</td><td>4.14→4.19（+5bp）</td><td>4.44→4.71（<b>+27bp</b>）</td><td>+0.30→<b>+0.52</b>（+22bp）</td><td>财政供给 / AI 超长债 / 通胀固化 / 海外减持 → <b>期限溢价</b></td><td class="up">熊陡</td></tr>
<tr><td><b>③ 回吐段</b></td><td>8/18 → 8/26</td><td>4.19→4.19</td><td>4.71→4.66</td><td>+0.52→+0.47</td><td>财政部回购扩容干预 + 8 月底数据降温</td><td>缓牛</td></tr>
<tr><td><b>④ 熊平收敛</b></td><td>8/28 Warsh 讲话后</td><td class="up">+8~10bp → 4.29~4.31</td><td>持平 4.67~4.69</td><td>→ <b>~0.38</b></td><td>加息预期重定价（9 月加息概率 55.7%~60%）</td><td class="up">熊平</td></tr>
<tr><td><b>⑤ 前瞻（待验证）</b></td><td>9 月初 → Q4</td><td>方向未定</td><td>方向未定</td><td>分水岭</td><td>8 月非农 + CPI → 9/15–16 FOMC</td><td>待定</td></tr>
</table>
<div class="note">口径提示：①—③为 FRED 实际日频；④为 8/28 盘中多源报道值（Reuters/CNBC/华尔街见闻），FRED 尚未发布 8/27–8/28 官方值。</div>

<h3>2.2 阶段②（核心问题：为什么最近开始扩大）四大驱动</h3>
<div class="card">
<p><b>① 财政供给天量扩容（最核心）</b>：联邦债务突破 40 万亿美元；2026 财年前 10 个月赤字 1.799 万亿美元、已超 2025 全年；国债净利息支出首次超越国防开支；8/13 三十年期新债以 5.216% 发行（2001 年以来新高）；8 月初财政部上调 Q3 借款预估 → 2027 年起长债放量预期升温。</p>
<p><b>② AI 基建发债分流长线资金</b>：科技巨头年内发债超 2000 亿美元且集中于长久期（2025 年以来新增企业债 5 年以上占 84%），20–40 年超长公司债直接分流养老金/保险资金——"AI 是长债利率最大的对手盘"（华泰）。</p>
<p><b>③ 长期通胀预期固化</b>：PCE 同比 3.7%、核心 3.3%、连续 65 个月超 2%；中东冲突推升油价 → 通胀担忧复燃；市场固化"利率更高、维持更久"交易。</p>
<p><b>④ 海外边际买盘萎缩</b>：6 月外资持有美债环比 −721 亿美元（日本 −264 亿、英国 −87 亿）；日本超长期国债收益率升破 4%（日债外溢）；新兴市场债券 1–7 月吸金 2,144 亿美元分流。</p>
</div>

<h3>2.3 机制定性：期限溢价重定价，≠2022 式加息债熊</h3>
<div class="card">
<p><b>关键判断（国盛熊园）</b>：与 2022 年央行快速加息驱动的"债熊"不同，本轮更像<b>对长期利率中枢与久期风险补偿的重新定价</b>——长端上行几乎全部体现为<b>期限溢价</b>抬升。惠誉（库尔顿）亦指出主要是<b>实际收益率</b>上升、而非通胀预期；叠加 Warsh 执掌下政策路径不确定性抬升风险补偿。</p>
<p><b>机制</b>：短端（2Y）仍由政策利率预期主导（7–8 月数据走弱时 2Y 反而回落）；长端由供需格局与风险补偿主导（数据走弱压不住长端）→ 出现"短端下、长端上"的背离 → <b>利差扩张是结构性的，与加息预期无关</b>。这也是为什么 6–8 月利差扩张期间，2Y 仅 +5bp、市场对加息几乎零定价。</p>
</div>

<h3>2.4 阶段④：Warsh 讲话驱动切换（熊陡 → 熊平）</h3>
<table>
<tr><th></th><th>7 月 – 8 月中（扩张段 ②）</th><th>8/28 起（收敛段 ④）</th></tr>
<tr><td>主导力量</td><td>财政供给 / AI 发债 / 通胀溢价 / 海外减持 → <b>期限溢价</b></td><td>Warsh 鹰派 → <b>加息预期重定价</b></td></tr>
<tr><td>2Y</td><td>锚政策利率，波动小（+5bp）</td><td class="up">跳升 8~10bp（9 月加息概率 55.7%~60%）</td></tr>
<tr><td>10Y</td><td class="up">主导上涨（+22~27bp）</td><td>持平（对冲）</td></tr>
<tr><td>30Y</td><td class="up">破 5.3%，2007 年来新高</td><td class="down">反跌（通胀溢价降、信誉保全）</td></tr>
<tr><td>利差形态</td><td>扩张（熊陡）</td><td>收敛（熊平）</td></tr>
<tr><td>性质</td><td>财政/主权信用风险重定价</td><td>政策紧缩风险重定价</td></tr>
</table>
<div class="quote"><b>交接文档判断（8 成事件噪音 / 2 成趋势种子）</b>：Warsh 主动撤回口头锚定（不引导、不给承诺）→ 市场进入"无锚敏感"期，未来数周 2Y 双向大幅波动、利差反复属正常，<b>单日移动不能当趋势确认</b>。历史对照：2022 年 Powell 激进紧缩期 10Y−2Y 一度 &lt; −100bp 深度倒挂；若 9–12 月连续加息被坐实，曲线续平甚至翻负的空间真实存在，但需 2–3 个月验证。</div>

<h2>三、Jackson Hole 2026：美联储主席 Warsh 发言更新</h2>
<div class="card">
<p><b>基本信息</b>：2026-08-28（周五），堪萨斯城联储年会（主题"金融创新：对支付与政策的影响"），演讲《In Our Time》（我们所处的时代）。这是 <b>Kevin Warsh（2026-05 上任）任内第 100 天、首次 Jackson Hole 主旨演讲</b>。⚠️ 注意：2026 年美联储主席是 Warsh，Powell 已于 2026 年卸任，不再按 Powell 时代信息库回答。</p>
</div>

<h3>3.1 讲话关键数据（一手口径）</h3>
<table>
<tr><th>指标</th><th>数值</th></tr>
<tr><td>7 月 PCE 同比</td><td class="up">3.7%（6 个月年化 4.1%）</td></tr>
<tr><td>7 月核心 PCE 同比</td><td class="up">3.3%</td></tr>
<tr><td>通胀连续超 2% 目标月数</td><td>65 个月</td></tr>
<tr><td>失业率</td><td>4.1%（偏低、数年未变）</td></tr>
<tr><td>设备+无形资产投资 4Q 同比</td><td class="up">约 9%（2021 年来最快，过半与 AI 基建相关）</td></tr>
<tr><td>标普 500 盈利同比</td><td class="up">+20%+</td></tr>
<tr><td>政策利率</td><td>3.50%–3.75%（2025 年 12 月起未动）</td></tr>
<tr><td>PCE 篮子中年涨幅&gt;3% 项目占比</td><td class="up">54%（疫后峰值 77%、疫前 20 年均值 32%）</td></tr>
</table>

<h3>3.2 Warsh 核心立场（七点）</h3>
<div class="card">
<ul>
<li><b>1. 拒绝前瞻指引</b>："你可以叫它大纲、路线图，就是别叫它前瞻指引（just don't call it forward guidance）"；认为其"赖着不走（overstayed its welcome）"，主推 <b>"quieter Fed"（更安静的联储）</b>，应被结果而非解释评判。</li>
<li><b>2. 拒绝反应函数/利率路径</b>：否认 Taylor 式机械规则可行；结尾金句 <b>"我承诺的是纪律，不是决定"（committed to a discipline, not a decision）</b>。</li>
<li><b>3. 警惕"镜厅问题"（hall of mirrors）</b>：市场依据美联储指引定价、美联储又参考市场价格判断 → 双方同时忽视新的经济变化；市场应关注资产价格、收益率、汇率、信用条件、商品价格等真实经济信号，而非"猜美联储"。</li>
<li><b>4. 经济评估乐观</b>：经济"看起来走强了"；居民消费 4Q 增超 2%；私人国内最终购买（PDFP）年内年化约 3%；企业盈利 +20%+。</li>
<li><b>5. 通胀是首要矛盾</b>：<b>"美联储现阶段的首要重点应该是价格"</b>；"今夏读数好于预期，但并未告诉我潜在趋势有有意义的改善"。</li>
<li><b>6. 最强鹰派信号句</b>：<b>"我们必须确信潜在通胀正清晰且以足够速度向目标（2%）移动——否则，我们就有工作要做（Otherwise, we have work to do）。"</b>（被 FT 直接解读为"若通胀不快速下降，准备加息"）</li>
<li><b>7. 金融条件不紧 + AI 交工作组</b>：信用利差近历史低位、贷款条件转松，"很难把广泛金融条件描述为限制性的" → 为加息留余地；AI/生产率长期问题交 5 个工作组，明确其建议不影响当前政策周期决策。</li>
</ul>
</div>
<div class="note">补充（多源）：Warsh 还重申 2% 目标"坚定、固定、不容更改"；提出七条个人政策原则（区分当前趋势与过时数据、短期利率是核心工具、货币供应量仍相关等）；演讲<b>未提及</b>财政部债券回购计划与 Bessent 的紧张关系（经济学家视为重要缺项）。</div>

<h3>3.3 市场即时反应（8/28 盘中 + 收盘）</h3>
<table>
<tr><th>指标</th><th>反应</th></tr>
<tr><td>9 月加息概率（CME FedWatch）</td><td class="up">~35% → <b>55.7%~60%</b>（另有口径 40~50%；Polymarket 升破 50%）</td></tr>
<tr><td>2 年期美债收益率</td><td class="up">+6.6~10bp → 4.29~4.31%（一个月最高）</td></tr>
<tr><td>10 年期美债收益率</td><td>持平 ~ +2bp → 4.67~4.69%</td></tr>
<tr><td>30 年期美债收益率</td><td class="down">−0.7~3bp → 5.16~5.18%（通胀信誉保全 → 通胀溢价下降）</td></tr>
<tr><td>标普 500</td><td class="up">+0.43% → ~7,764（讲话消化后收涨）</td></tr>
<tr><td>道指 / 纳指 100</td><td class="up">道指 +0.38% → ~53,778（价值占优）｜ 纳指 100 +0.22% → ~29,706（高久期成长滞后）</td></tr>
<tr><td>黄金 / 美元 / BTC</td><td class="down">黄金转跌 −0.6%~−2% → ~$4,535~4,575 ｜ 美元 +0.36%（彭博美元指数一周高位） ｜ BTC −0.9~1.1% → ~$79,400</td></tr>
</table>
<div class="note">纳指跑输道指 = 加息预期下"价值 &gt; 高久期成长"的典型轮动信号；黄金受实际利率抬升打击；BTC 为最高 beta 风险资产跌幅最大。2Y 定价政策路径（大涨）&gt; 10Y（加息预期推升 vs 通胀信誉保全压低通胀溢价，两股对冲）→ 净效果<b>利差收窄（熊平）</b>：10Y−2Y 由 8/26 的 0.47 收窄至约 0.38。</div>

<h2>四、后续跟踪信号（交接给下个会话）</h2>
<div class="card">
<ul>
<li>① <b>9 月初 8 月非农 + CPI</b>：决定 2Y 与加息路径方向——强（加息坐实）→ 2Y 续升、利差续收窄甚至翻负；弱 → 2Y 回落、利差修复回 0.45+。</li>
<li>② <b>9/15–16 FOMC + 记者会</b>：Warsh 是否延续"不给指引"；7 月 FOMC 已有 3 名官员异议主张加息（Hammack/Schmid/Goolsbee 偏鹰）。</li>
<li>③ <b>US10Y 长端</b>：财政主导（40 万亿美债、Bessent 干预债市、特朗普施压降息）下长端是否继续走高——若长端再上而 2Y 因加息落地滞涨，利差可能二次走阔（供给驱动回归）。</li>
<li>④ <b>30Y 动向</b>：若持续下跌（市场相信"加息能保通胀信誉"）→ 长久期资产（医药/公用事业）相对受益逻辑强化；若加息引发衰退担忧 → 防御股与黄金同步受益。</li>
<li>⑤ <b>对持仓结构的含义</b>（承接 54 号）：SOFI ≫ MS &gt; APO ≈ ABBV ≈ JNJ ≈ CSCO——加息预期真正打击高久期+消费信贷与投行活动；医药双雄（ABBV/JNJ）与 KO 是利率情景下的防御压舱石；APO 对"大幅走阔"敏感而非熊平，本轮切换反缓解。</li>
</ul>
</div>

<h2>五、资料索引与体系说明</h2>
<div class="card">
<p><b>本文件在背景体系中的位置</b>：55 号「宏观背景」＝常设背景文件，聚合三大板块（蓝筹池索引 / 美债利差 / 央行沟通），供后续会话直接引用、滚动更新（每次宏观事件后增量修订本文件而非另起炉灶）。</p>
<ul class="ref">
<li><b>数据资产</b>：<code>data/blue_chips.csv</code>（蓝筹池）｜ <code>data/us_treasury/DGS2.csv</code>、<code>DGS10.csv</code>（FRED 日频，至 2026-08-26；FRED 直连可补：<code>fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2</code>）</li>
<li><b>一手来源</b>：Warsh 演讲原文 <code>federalreserve.gov/newsevents/speech/warsh20260828a.htm</code>；Reuters 直播、CNBC、WSJ（Nick Timiraos）解读；财联社/东方财富中文全文翻译。</li>
<li><b>关联文档</b>：<a href="../交接文档_JacksonHole2026_Warsh讲话与美债利差.md">交接文档（JH2026 Warsh 讲话与美债利差）</a>｜ <a href="../54_宏观利率背景六股影响/index.html">54 号（利差扩张→熊平×六股）</a>｜ <a href="../30_资管陡峭化/index.html">30 号（资管×走阔）</a>｜ <a href="../08_银行陡峭化/banks_steep_report.html">08 号（银行×陡峭化）</a>｜ <a href="../52_持仓组合技术面与操作建议/index.html">52 号（持仓组合）</a></li>
</ul>
</div>

<div class="warn">
<b>风险提示</b>：① 数据截至 08-27 收盘 + 08-28 盘中/收盘报道，FRED 官方值（8/27–8/28）与 9 月加息概率可能进一步变动；② Warsh 拒绝前瞻指引 → 市场无锚，单日利率/利差移动不代表趋势，9 月初数据是分水岭；③ 预测与情绪分析仅为基于公开信息的推演，不保证准确性。本文基于公开信息整理，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。
</div>

<div class="foot">
数据源：FRED（DGS2/DGS10，至 2026-08-26）、data/blue_chips.csv（蓝筹池 73 只）、交接文档（Warsh 08-28 讲话）、Reuters/CNBC/WSJ/财联社/华尔街见闻（8/28 反应，2026-08-29 检索）、54 号报告（利差归因与六股敏感度）。生成：2026-08-29。
</div>

</div>
<script>
const CHART_DATA = @@CHART@@;
const chart1 = echarts.init(document.getElementById('c1'));
chart1.setOption({
  tooltip:{trigger:'axis'},
  legend:{data:['2Y','10Y','利差 10Y-2Y'],top:0},
  grid:{left:50,right:60,top:34,bottom:40},
  xAxis:{type:'category',data:CHART_DATA.dates,axisLabel:{fontSize:10}},
  yAxis:[
    {type:'value',name:'%',min:3.3,max:4.9,splitLine:{lineStyle:{color:'#eee'}}},
    {type:'value',name:'利差%',min:0.1,max:0.8,splitLine:{show:false}}
  ],
  series:[
    {name:'2Y',type:'line',data:CHART_DATA.y2,symbol:'none',lineStyle:{width:1.5,color:'#0072B2'},itemStyle:{color:'#0072B2'}},
    {name:'10Y',type:'line',data:CHART_DATA.y10,symbol:'none',lineStyle:{width:1.5,color:'#E69F00'},itemStyle:{color:'#E69F00'}},
    {name:'利差 10Y-2Y',type:'line',yAxisIndex:1,data:CHART_DATA.sp,symbol:'none',lineStyle:{width:2,color:'#D55E00'},itemStyle:{color:'#D55E00'},
     markPoint:{data:[{name:'扩张峰值 8/18',coord:['2026-08-18',0.52],symbolSize:44,label:{formatter:'峰值'}}]},
     markArea:{silent:true,data:[
       [{name:'①扩张前',xAxis:'2026-01-02'},{xAxis:'2026-06-30'}],
       [{name:'②扩张段\n(长端驱动熊陡)',itemStyle:{color:'rgba(213,94,0,0.10)'},xAxis:'2026-06-30'},{xAxis:'2026-08-18'}],
       [{name:'③回吐段',itemStyle:{color:'rgba(0,0,0,0.04)'},xAxis:'2026-08-18'},{xAxis:'2026-08-26'}],
       [{name:'④Warsh后熊平(估算)',itemStyle:{color:'rgba(0,114,178,0.10)'},xAxis:'2026-08-26'},{xAxis:'2026-08-28'}]
     ]}
    }
  ]
});
window.addEventListener('resize',()=>{chart1.resize();});
</script>
</body></html>
"""

HTML = HTML.replace('@@CHART@@', json.dumps(chart_data, ensure_ascii=False))
out = os.path.join(OUT_DIR, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print('written:', out, os.path.getsize(out), 'bytes | blue_chips:', n_total, '| chart days:', len(dates))
