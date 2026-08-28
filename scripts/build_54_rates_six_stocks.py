#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""54 号报告：宏观利率背景（利差扩张→熊平切换）× 六股影响（APO/MS/SOFI/CSCO/ABBV/JNJ）
数据源：FRED DGS2/DGS10（本地 data/us_treasury/，至 2026-08-26）+ 本地日线 + 交接文档（Warsh 8/28 讲话）
"""
import csv, math, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_fred(path):
    d = {}
    with open(path) as f:
        for r in csv.reader(f):
            if len(r) >= 2 and r[0][:4] == '2026' and r[1].strip() not in ('', '.'):
                try: d[r[0].strip()] = float(r[1].strip())
                except: pass
    return d

def load_px(path):
    rows = list(csv.reader(open(path)))
    hdr = [h.strip() for h in rows[0]]
    ci = hdr.index('date') if 'date' in hdr else 0
    cci = None
    for c in ('close', 'Close', 'adj close', 'Adj Close', 'AdjClose', 'CLOSE'):
        if c in hdr: cci = hdr.index(c); break
    if cci is None: cci = len(hdr) - 1
    d = {}
    for r in rows[1:]:
        if len(r) <= cci: continue
        try:
            v = float(r[cci].strip())
            if v > 0: d[r[ci].strip()] = v
        except: pass
    return d

d2 = load_fred(os.path.join(BASE, 'data/us_treasury/DGS2.csv'))
d10 = load_fred(os.path.join(BASE, 'data/us_treasury/DGS10.csv'))
alld = sorted(set(d2) & set(d10))

# 利率日变化（bp）
chg2, chg10, chgsp, spr = {}, {}, {}, {}
for i in range(1, len(alld)):
    a, b = alld[i-1], alld[i]
    chg2[b] = (d2[b] - d2[a]) * 100
    chg10[b] = (d10[b] - d10[a]) * 100
    spr[b] = d10[b] - d2[b]
    chgsp[b] = (spr[b] - (d10[a] - d2[a])) * 100

STOCKS = {'APO': 'apo/APO, 1D.csv', 'MS': 'ms/ms, 1D.csv', 'SOFI': 'sofi/sofi, 1D.csv',
          'CSCO': 'csco/csco, 1D.csv', 'ABBV': 'abbv/ABBV, 1D.csv', 'JNJ': 'jnj/JNJ, 1D.csv'}

def reg(xs, ys):
    n = len(xs)
    if n < 10: return None
    mx = sum(xs)/n; my = sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs); sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys)); syy = sum((y-my)**2 for y in ys)
    if sxx == 0 or syy == 0: return None
    b = sxy/sxx; r = sxy/math.sqrt(sxx*syy)
    se = math.sqrt(max((syy-b*sxy)/(n-2), 0)/sxx)
    t = b/se if se > 0 else 0
    return b, r, t, n

def pval(t, n):
    from math import erf, sqrt
    return 2 * (1 - 0.5 * (1 + erf(abs(t)/sqrt(2))))

def sig_label(p):
    return 'sig' if p < 0.01 else ('edge' if p < 0.05 else 'no')

sens = {}   # name -> {fac: {...}}
ret6 = {}   # 6月以来涨跌
last_px = {}
for name, p in STOCKS.items():
    px = load_px(os.path.join(BASE, 'data', p))
    ds = sorted(px)
    rets = {}
    for i in range(1, len(ds)):
        a, b = ds[i-1], ds[i]
        rets[b] = (px[b]/px[a] - 1) * 100
    last_px[name] = (ds[-1], px[ds[-1]])
    d61 = [d for d in ds if d >= '2026-06-01'][0]
    ret6[name] = px[ds[-1]]/px[d61] - 1
    sens[name] = {}
    for fac, chg in [('d2', chg2), ('d10', chg10), ('sp', chgsp)]:
        comm = sorted(set(rets) & set(chg))
        res = reg([chg[d] for d in comm], [rets[d] for d in comm])
        c60 = comm[-60:]
        res60 = reg([chg[d] for d in c60], [rets[d] for d in c60])
        if res and res60:
            b, r, t, n = res; b60, r60, t60, n60 = res60
            sens[name][fac] = dict(b=b, r=r, p=pval(t, n), n=n, b60=b60, r60=r60, p60=pval(t60, n60))

# 图表数据
chart_dates = alld
chart_2y = [d2[d] for d in alld]
chart_10y = [d10[d] for d in alld]
chart_sp = [d10[d]-d2[d] for d in alld]

key_nodes = ['2026-06-01', '2026-06-30', '2026-07-31', '2026-08-18', '2026-08-26']
node_rows = [(d, d2[d], d10[d], d10[d]-d2[d]) for d in key_nodes if d in d2]

# 扩张段分解
d_a, d_b = '2026-06-30', '2026-08-18'
exp = dict(d2=(d2[d_b]-d2[d_a])*100, d10=(d10[d_b]-d10[d_a])*100,
           sp=((d10[d_b]-d2[d_b])-(d10[d_a]-d2[d_a]))*100)

# 六股敏感性表行
def fmt_num(x): return f"{x:.3f}"
sens_rows = []
for name in ['SOFI', 'MS', 'APO', 'CSCO', 'ABBV', 'JNJ']:
    s = sens[name]
    row = []
    for fac in ['d2', 'd10', 'sp']:
        f = s[fac]
        row.append(dict(b=f['b'], r=f['r'], l=sig_label(f['p']), b60=f['b60'], r60=f['r60'], l60=sig_label(f['p60'])))
    sens_rows.append((name, row))

# ============ HTML ============
chart_data = json.dumps(dict(dates=chart_dates, y2=chart_2y, y10=chart_10y, sp=chart_sp))
sens_js = json.dumps({name: {f: sens[name][f] for f in ('d2', 'd10', 'sp')} for name in STOCKS})

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>54 · 宏观利率背景（利差扩张→熊平切换）× 六股影响</title>
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
.chart{width:100%;height:380px;margin:14px 0}
.note{font-size:12px;color:var(--muted);margin:6px 0 2px}
.exec{background:#fffbea;border:1px solid #f0dca0;border-radius:10px;padding:16px 20px;margin:16px 0}
.exec li{margin:6px 0}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.kv div{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.kv .k{font-size:12px;color:var(--muted)}.kv .v{font-size:17px;font-weight:700;margin-top:2px}
.stock{border:1px solid var(--line);border-radius:10px;margin:14px 0;overflow:hidden}
.stock-h{padding:12px 18px;font-size:15px;font-weight:700;display:flex;align-items:center;gap:10px;background:#f0f1f3}
.stock-b{padding:14px 18px}
.stock-b p{margin:8px 0;font-size:13.5px}
.stock-b ul{margin:6px 0 6px 20px;font-size:13.5px}
.stock-b li{margin:4px 0}
.legend{font-size:12px;color:var(--muted);margin-top:8px}
.warn{background:#fdf2f2;border:1px solid #f0c8c8;border-radius:8px;padding:12px 16px;font-size:13px;margin-top:10px}
.foot{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
</style>
</head>
<body><div class="wrap">

<h1>宏观利率背景（利差扩张 → 熊平切换）× 六股影响</h1>
<div class="sub">报告编号 54 ｜ 2026-08-29 ｜ 覆盖：APO / MS / SOFI / CSCO / ABBV / JNJ ｜ 数据：FRED 至 08-26、本地日线至 08-27、Warsh 讲话 08-28 盘中</div>

<div class="exec">
<b>一页结论</b>
<ul>
<li><b>6 月以来利差扩张是"长端供给/期限溢价"驱动，不是加息预期</b>：10Y +22bp vs 2Y 仅 +5bp（6/30→8/18），四大推力＝财政天量供给（赤字 1.8 万亿、债务 40 万亿）、AI 巨头超长债分流（年内 2000 亿美元+）、长期通胀预期固化（PCE 3.7%、65 个月超 2%）、海外买盘萎缩（6 月外资持仓 −721 亿美元）。机制＝期限溢价重定价，"短端下、长端上"背离。</li>
<li><b>8/28 Warsh Jackson Hole 首秀放鹰，驱动切换为"加息预期"，曲线转熊平</b>：9 月加息概率 35%→55.7%，2Y 跳升 8bp 至 4.31，10Y 持平 4.67~4.69，30Y 反跌至 5.16~5.18（通胀信誉保全）。</li>
<li><b>六股影响排序（利率负面敏感度）：SOFI ≫ MS &gt; APO ≈ ABBV ≈ JNJ ≈ CSCO</b>。SOFI 是唯一统计显著的（Δ10Y β=−0.24 全期 / −0.42 近 60 日，R=−0.51）；MS 近 60 日边缘负敏感；APO 对"走阔"敏感而非"熊平"（30 号报告），本轮切换反而缓解；ABBV/JNJ 低敏感防御、基本面主导（6 月以来 +21%/+21%）；CSCO 与利率基本脱钩，8 月下跌是财报/自身因素。</li>
</ul>
</div>

<h2>一、6 月以来利差扩张：原因拆解</h2>

<h3>1.1 数据事实：扩张完全由长端驱动</h3>
<table>
<tr><th>节点</th><th>2Y(%)</th><th>10Y(%)</th><th>10Y−2Y</th><th>阶段</th></tr>
@@NODES@@
</table>
<div class="note">利差 6 月末低点 +0.30 → 8/18 峰值 +0.52 → 8/26 +0.47。扩张段（6/30→8/18）：10Y +@@EXP10@@bp、2Y 仅 +@@EXP2@@bp → 利差 +@@EXPSP@@bp，<b>长端贡献约 @@PCT10@@%</b>。8/26 后因 8/19 财政部回购扩容干预与 8 月底数据降温小幅回吐。</div>

<div class="chart" id="c1"></div>
<div class="legend">2Y / 10Y 收益率（左轴，%）与 10Y−2Y 利差（右轴，%）｜ 2026 年日频（FRED）｜ 扩张段 = 长端（橙）快于短端（蓝）上行；8/28 讲话后 2Y 跳升而 10Y 持平 → 熊平（数据至 08-26，08-28 为盘中报道值）</div>

<h3>1.2 四大驱动（多源交叉印证：证券时报/21世纪/环球网/国盛/中航/中信）</h3>
<div class="card">
<p><b>① 财政供给天量扩容（最核心）</b>：联邦债务突破 40 万亿美元；2026 财年前 10 个月赤字 1.799 万亿美元、已超 2025 全年；国债净利息支出首次超越国防开支；8/13 三十年期新债以 5.216% 发行（2001 年以来新高）；8 月初财政部上调 Q3 借款预估 → 2027 年起长债放量预期升温。</p>
<p><b>② AI 基建发债分流长线资金</b>：科技巨头年内发债超 2000 亿美元且集中于长久期（2025 年以来新增企业债 5 年以上占 84%），20–40 年超长公司债直接分流养老金/保险资金——"AI 是长债利率最大的对手盘"（华泰）。</p>
<p><b>③ 长期通胀预期固化</b>：PCE 同比 3.7%、核心 3.3%、连续 65 个月超 2%；中东冲突推升油价 → 通胀担忧复燃；市场固化"利率更高、维持更久"交易。</p>
<p><b>④ 海外边际买盘萎缩</b>：6 月外资持有美债环比 −721 亿美元（日本 −264 亿、英国 −87 亿）；日本超长期国债收益率升破 4%（日债外溢）；新兴市场债券 1–7 月吸金 2144 亿美元分流。</p>
</div>

<h3>1.3 机制定性：期限溢价重定价，≠2022 式加息债熊</h3>
<div class="card">
<p><b>关键判断（国盛熊园）</b>：与 2022 年央行快速加息驱动的"债熊"不同，本轮更像<b>对长期利率中枢与久期风险补偿的重新定价</b>——长端上行几乎全部体现为<b>期限溢价</b>抬升。惠誉（库尔顿）亦指出主要是<b>实际收益率</b>上升、而非通胀预期；叠加 Warsh 执掌下政策路径不确定性抬升风险补偿。</p>
<p><b>机制</b>：短端（2Y）仍由政策利率预期主导（7–8 月数据走弱时 2Y 反而回落）；长端由供需格局与风险补偿主导（数据走弱压不住长端）→ 出现"短端下、长端上"的背离 → <b>利差扩张是结构性的，与加息预期无关</b>。这也是为什么 6–8 月利差扩张期间，2Y 仅 +5bp、市场对加息几乎零定价。</p>
</div>

<h2>二、8/28 Warsh 讲话：驱动切换，曲线转熊平</h2>

<h3>2.1 讲话要点（一手来源：federalreserve.gov + Reuters 直播）</h3>
<div class="card">
<ul>
<li><b>通胀是首要矛盾</b>："美联储现阶段的首要重点应该是价格"；7 月 PCE 3.7%（6 个月年化 4.1%）、核心 3.3%、连续 65 个月超 2%；今夏读数好于预期"但并未告诉我潜在趋势有意义的改善"。</li>
<li><b>最强鹰派信号句</b>："我们必须确信潜在通胀正清晰且以足够速度向 2% 移动——否则，我们就有工作要做（Otherwise, we have work to do）。"</li>
<li><b>金融条件不紧</b>：信用利差近历史低位、贷款条件转松，"很难把广泛金融条件描述为限制性的" → 为加息留余地。</li>
<li><b>拒绝前瞻指引</b>："你可以叫它大纲、路线图，就是别叫它前瞻指引"；"我承诺的是纪律，不是决定" → 市场进入无锚敏感期。</li>
<li><b>经济评估乐观</b>：经济"看起来走强了"；设备+无形资产投资 4Q 同比约 9%（2021 年来最快，过半与 AI 基建相关）；标普 500 盈利 +20%+。</li>
</ul>
</div>

<h3>2.2 市场即时反应（8/28 盘中）</h3>
<table>
<tr><th>指标</th><th>反应</th></tr>
<tr><td>9 月加息概率（CME FedWatch）</td><td>35% → <b>55.7%</b>（另有口径 46~50%；Polymarket 升破 50%）</td></tr>
<tr><td>2 年期美债收益率</td><td class="up">+6.6~10bp → 4.29~4.31%（一个月最高）</td></tr>
<tr><td>10 年期美债收益率</td><td>持平 ~ +2bp → 4.67~4.69%</td></tr>
<tr><td>30 年期美债收益率</td><td class="down">−0.7~3bp → 5.16~5.18%（通胀信誉保全 → 通胀溢价下降）</td></tr>
<tr><td>美股</td><td>标普 +0.3~0.4%、道指 +0.2%、纳指 +0.3%（讲话消化后收涨）</td></tr>
<tr><td>黄金 / 美元 / BTC</td><td>黄金转跌 −2%+ ｜ 美元 +0.36% 至 99.5 ｜ BTC −0.9% 至 7.94 万</td></tr>
</table>
<div class="note">2Y 定价政策路径（大涨）&gt; 10Y（加息预期推升 vs 通胀信誉保全压低通胀溢价，两股对冲）→ 净效果<b>利差收窄（熊平）</b>：10Y−2Y 由 8/26 的 0.47 收窄至约 0.38。</div>

<h3>2.3 驱动机制对照：两段利率行情完全不同</h3>
<table>
<tr><th></th><th>7 月 – 8 月中（扩张段）</th><th>8/28 起（收敛段）</th></tr>
<tr><td>主导力量</td><td>财政供给 / AI 发债 / 通胀溢价 / 海外减持 → <b>期限溢价</b></td><td>Warsh 鹰派 → <b>加息预期重定价</b></td></tr>
<tr><td>2Y</td><td>锚政策利率，波动小（+5bp）</td><td class="up">跳升 8bp（9 月加息概率 55.7%）</td></tr>
<tr><td>10Y</td><td class="up">主导上涨（+22~27bp）</td><td>持平（对冲）</td></tr>
<tr><td>30Y</td><td class="up">破 5.3%，2007 年来新高</td><td class="down">反跌（通胀溢价降）</td></tr>
<tr><td>利差形态</td><td>扩张（熊陡）</td><td>收敛（熊平）</td></tr>
<tr><td>性质</td><td>财政/主权信用风险重定价</td><td>政策紧缩风险重定价</td></tr>
</table>
<div class="note">⚠️ 交接文档判断：本次约 8 成是"事件噪音重定价"、2 成"趋势种子"；Warsh 无锚沟通下未来数周 2Y 双向大幅波动、利差反复属正常，<b>单日移动不能当趋势确认</b>。真分水岭在 9 月初 8 月非农 + CPI，以及 9/15–16 FOMC。</div>

<h2>三、六股影响：逐股拆解</h2>

<h3>3.1 利率敏感性实证（2026 年日频，n≈162）</h3>
<div class="note">回归：个股日收益（%）~ 当日利率变化（bp）。β = 利率每涨 1bp 当日股票平均涨跌（%）。显著性三档：<span class="tag sig">sig</span>p&lt;0.01 / <span class="tag edge">edge</span>0.01≤p&lt;0.05 / <span class="tag no">no</span>p≥0.05。同前表：近 60 日为最近 60 个交易日子样本。</div>
<table>
<tr><th>股票</th><th>Δ2Y β(全期)</th><th>R</th><th>Δ10Y β(全期)</th><th>R</th><th>Δ10Y β(近60日)</th><th>R</th><th>Δ利差 β(全期)</th><th>R</th></tr>
@@SENSROWS@@
</table>
<div class="note">解读：① <b>SOFI 是唯一统计显著的利率负敏感标的</b>，且近 60 日放大（Δ10Y β=−0.42、R=−0.51）——利率上行窗口对 SOFI 是明确逆风。② MS 近 60 日对 Δ10Y 呈边缘负敏感（R=−0.23）。③ APO/ABBV/JNJ/CSCO 日度敏感度均不显著——它们的利率影响来自<b>情景/基本面传导</b>而非日度 β。</div>

<div class="chart" id="c2"></div>
<div class="legend">六股对 Δ10Y 的敏感系数 β（每 bp 当日 %）：全期（蓝）vs 近 60 日（橙）｜ 负值 = 利率涨股票跌，红系；正值 = 利率涨股票涨，蓝系（Okabe-Ito）</div>

@@STOCKS@@

<h2>四、结论与操作含义</h2>
<div class="card">
<p><b>利率负面冲击敏感度排序：SOFI ≫ MS &gt; APO ≈ ABBV ≈ JNJ ≈ CSCO</b></p>
<ul>
<li><b>加息预期真正打击的是"高久期 + 消费信贷"（SOFI）与"投行活动"（MS 温和）</b>；9 月初非农+CPI 若强（加息坐实）→ 二者续压，若弱（加息证伪）→ SOFI 弹性修复最大（对称）。</li>
<li><b>医药双雄（ABBV/JNJ）低敏感 + 防御属性</b>：利率情景下相对占优；且 30Y 反跌（通胀溢价下降）对长久期资产估值是温和利好信号。基本面（+21%/+21%）是主驱动，08-27 ABBV 单日 −2.6% 的回落暂不支持利率归因。</li>
<li><b>APO 对"走阔"敏感而非"熊平"</b>（30 号报告：大幅走阔 &gt;+30bp/月 资管重挫 −6.8%、严格熊陡 +5.71%）：本轮从"供给型走阔"切到"加息型熊平"，反而缓解其压力；私募信贷浮动利率资产在加息中收益端改善，经济强劲 + 信用利差低位 → 违约风险低，基本面韧性。</li>
<li><b>CSCO 与利率基本脱钩</b>：别用利率叙事解释其 8 月 −7.6% 下跌（52 号已提示跌破 EMA50）；AI 基建（Warsh 口径 4Q 设备投资 +9% 过半 AI）是顺风，关注 11 月财报与 800G 订单。</li>
<li><b>对持仓结构的意义</b>：若倾向防御利率风险 → 医药/低估值科技占比可高于消费信贷/投行；SOFI 属"利率双向期权"，加仓应等 9 月数据窗口落地。</li>
</ul>
</div>

<div class="warn">
<b>风险提示</b>：① 数据截至 08-27 收盘 + 08-28 盘中报道，08-28 收盘数据与 9 月加息概率可能进一步变动；② Warsh 拒绝前瞻指引 → 市场无锚，单日利率/利差移动不代表趋势，9 月初数据是分水岭；③ 30Y 反跌若持续，说明市场相信"加息能保通胀信誉"，届时长久期资产（医药/公用事业）相对受益逻辑强化；若加息反而引发衰退担忧，则防御股与黄金同步受益。本文为基于公开信息的推演，不构成投资建议。
</div>

<div class="foot">
数据源：FRED（DGS2/DGS10，至 2026-08-26）、本地日线（至 08-26/27）、交接文档（Warsh 08-28 讲话，Reuters/CNBC/WSJ 多源）、证券时报/21 世纪/环球网（长端上行归因）。生成：2026-08-29。
</div>

</div>
<script>
const CHART_DATA = @@CHART_DATA@@;
const SENS = @@SENS_JS@@;
const chart1 = echarts.init(document.getElementById('c1'));
chart1.setOption({
  tooltip:{trigger:'axis'},
  legend:{data:['2Y','10Y','利差 10Y-2Y'],top:0},
  grid:{left:50,right:60,top:34,bottom:40},
  xAxis:{type:'category',data:CHART_DATA.dates,axisLabel:{fontSize:10}},
  yAxis:[
    {type:'value',name:'%',min:3.8,max:4.9,splitLine:{lineStyle:{color:'#eee'}}},
    {type:'value',name:'利差%',min:0.2,max:0.6,splitLine:{show:false}}
  ],
  series:[
    {name:'2Y',type:'line',data:CHART_DATA.y2,symbol:'none',lineStyle:{width:1.5,color:'#0072B2'},itemStyle:{color:'#0072B2'}},
    {name:'10Y',type:'line',data:CHART_DATA.y10,symbol:'none',lineStyle:{width:1.5,color:'#E69F00'},itemStyle:{color:'#E69F00'}},
    {name:'利差 10Y-2Y',type:'line',yAxisIndex:1,data:CHART_DATA.sp,symbol:'none',lineStyle:{width:2,color:'#D55E00'},itemStyle:{color:'#D55E00'},
     markPoint:{data:[{name:'扩张峰值 8/18',coord:['2026-08-18',0.52],symbolSize:44,label:{formatter:'峰值'}}]}}
  ]
});
const chart2 = echarts.init(document.getElementById('c2'));
const names = Object.keys(SENS);
const bAll = names.map(n=>+SENS[n].d10.b.toFixed(3));
const b60 = names.map(n=>+SENS[n].d10.b60.toFixed(3));
chart2.setOption({
  tooltip:{trigger:'axis'},
  legend:{data:['全期 β','近60日 β'],top:0},
  grid:{left:50,right:20,top:34,bottom:40},
  xAxis:{type:'category',data:names},
  yAxis:{type:'value',name:'β（每bp %）',splitLine:{lineStyle:{color:'#eee'}}},
  series:[
    {name:'全期 β',type:'bar',data:bAll.map(v=>({value:v,itemStyle:{color:v<0?'#D55E00':'#0072B2'}})),barWidth:'30%'},
    {name:'近60日 β',type:'bar',data:b60.map(v=>({value:v,itemStyle:{color:v<0?'#E69F00':'#185FA5'}})),barWidth:'30%'}
  ]
});
window.addEventListener('resize',()=>{chart1.resize();chart2.resize();});
</script>
</body></html>
"""

def node_html():
    rows = ""
    for i, (d, y2v, y10v, spv) in enumerate(node_rows):
        stage = ['6 月收窄段', '扩张起点', '扩张中段', '扩张峰值', '回吐段（财政部干预+数据降温）'][i] if i < 5 else ''
        rows += f"<tr><td>{d}</td><td>{y2v:.2f}</td><td>{y10v:.2f}</td><td>{spv:+.2f}</td><td>{stage}</td></tr>"
    return rows

def sens_rows_html():
    out = ""
    for name, row in sens_rows:
        c = [row[0], row[1], row[2]]  # d2, d10, sp
        out += (f"<tr><td><b>{name}</b></td>"
                f"<td>{c[0]['b']:+.3f}</td><td>{c[0]['r']:.2f} <span class='tag {c[0]['l']}'>{c[0]['l']}</span></td>"
                f"<td>{c[1]['b']:+.3f}</td><td>{c[1]['r']:.2f} <span class='tag {c[1]['l']}'>{c[1]['l']}</span></td>"
                f"<td>{c[1]['b60']:+.3f}</td><td>{c[1]['r60']:.2f} <span class='tag {c[1]['l60']}'>{c[1]['l60']}</span></td>"
                f"<td>{c[2]['b']:+.3f}</td><td>{c[2]['r']:.2f} <span class='tag {c[2]['l']}'>{c[2]['l']}</span></td></tr>")
    return out

STOCK_HTML = {
'SOFI': """<div class="stock"><div class="stock-h"><span class="badge b-hi">高利率暴露</span>SOFI · SoFi Technologies（金融科技 / 消费信贷）<span style="font-size:12px;color:#666">6 月以来 +1.4%</span></div><div class="stock-b">
<p><b>利率传导机制</b>：①成长股高久期估值（折现率敏感，β 最高）；②消费信贷需求与拖欠率对融资成本高度敏感；③高波动 beta 在 risk-off 时放大。是六股中<b>唯一的"利率单边暴露"标的</b>。</p>
<p><b>实证</b>：Δ10Y 全期 β=−0.24（R=−0.30，<span class="tag sig">sig</span>）；<b>近 60 日放大至 β=−0.42、R=−0.51（sig）</b>——10Y 每涨 1bp 当日平均跌 0.42%，利率上行窗口是明确逆风；Δ2Y 亦显著（−0.18 / 近 60 日 −0.27）。</p>
<p><b>Warsh 情景影响</b>：<b class="down">负面</b>。9 月加息概率 35%→55.7% 的重定价首当其冲打击高久期+信贷标的；若 9/15–16 FOMC 落地加息，SOFI 承压最重。但这是<b>双向期权</b>：若 9 月初非农+CPI 走弱、加息证伪，SOFI 弹性修复也最大（对称性）。</p>
<p><b>操作含义</b>：9 月数据窗口（非农+CPI）落地前回避加仓；持仓者关注 8/28 后 2Y 冲高带来的回调压力，跌破 60 日 EMA 为风险信号。</p></div></div>""",
'MS': """<div class="stock"><div class="stock-h"><span class="badge b-mid">中性偏空</span>MS · Morgan Stanley（投行 + 财富管理）<span style="font-size:12px;color:#666">6 月以来 +1.5%</span></div><div class="stock-b">
<p><b>利率传导机制</b>：①投行条线（IPO/并购/资本市场）对融资成本敏感——加息降温活动；②财富管理/交易条线受益于利率高位（现金类产品利差）与波动放大（FICC）；③较高估值（PE~20+）受折现率压制。三力并存，净效应偏温和。</p>
<p><b>实证</b>：全期 Δ10Y β=−0.06（不显著）；<b>近 60 日 β=−0.10、R=−0.23（edge）</b>——长端上行对 MS 有温和负向拖累，与投行活动降温的直觉一致。</p>
<p><b>Warsh 情景影响</b>：<b class="down">温和负面</b>。加息预期 → 资本市场活动降温（逆风）；但利率高位 + 波动上升 → 财富管理与交易受益（顺风）；Warsh 称经济走强（盈利 +20%+）→ 风险资产环境尚可，投行业务不至于崩。净效应：估值承压为主，盈利韧性为缓冲。</p>
<p><b>操作含义</b>：利率上行对 MS 是"慢变量"拖累而非脉冲冲击；关注并购/IPO 活动月度数据验证，跌出近 60 日 R=−0.23 的敏感区间后低吸逻辑仍成立。</p></div></div>""",
'APO': """<div class="stock"><div class="stock-h"><span class="badge b-lo">相对中性</span>APO · Apollo Global Management（另类资管 / 私募信贷）<span style="font-size:12px;color:#666">6 月以来 +4.1%</span></div><div class="stock-b">
<p><b>利率传导机制（承接 30 号报告）</b>：APO 对<b>曲线形态</b>敏感而非利率水平——大幅走阔（&gt;+30bp/月，供给危机型）资管重挫 −6.8%（31% 胜率）；严格熊陡（长端快涨）反而最强 +5.71%（81.8% 胜率）。私募信贷资产多挂浮动利率，加息中收益端改善；风险在融资成本与流动性收紧。</p>
<p><b>实证</b>：Δ2Y/Δ10Y/Δ利差全期与近 60 日均不显著（|R|≤0.17）——日度利率变化对 APO 无统计意义，印证其驱动在"曲线形态事件"而非单日。</p>
<p><b>Warsh 情景影响</b>：<b class="up">相对中性偏多</b>。本轮从"供给型大幅走阔"（7–8 月，APO 的敏感形态）切到"加息型熊平"（8/28 起）——<b>熊平不是 APO 的历史重灾区形态</b>；叠加经济强劲（Warsh 口径）+ 信用利差低位 → 私募信贷违约风险低，基本面韧性。主要风险是流动性收紧超预期（回购/融资成本）与金融条件骤紧。</p>
<p><b>操作含义</b>：利率情景下 APO 优于 SOFI/MS；若担心"加息引发信用事件"，APO 是观察私募信贷利差的风向标，利差走阔 + 违约率抬头才需警惕。</p></div></div>""",
'CSCO': """<div class="stock"><div class="stock-h"><span class="badge b-lo">利率脱钩</span>CSCO · Cisco（网络设备 / AI 基建卖铲人）<span style="font-size:12px;color:#666">6 月以来 −7.6%</span></div><div class="stock-b">
<p><b>利率传导机制</b>：①低估值（PE~15）+ 高股息 → 折现率敏感度低；②AI 基建叙事（Warsh 口径：设备+无形资产投资 4Q 同比约 9%、过半与 AI 基建相关）→ 800G 交换机需求顺风；③企业 IT 支出周期与利率弱相关。</p>
<p><b>实证</b>：Δ2Y β=+0.03、Δ10Y β=+0.02（均不显著，|R|≤0.06）——<b>利率变化对 CSCO 几乎无解释力</b>。其 6 月以来 −7.6% 主要由 8/13 财报脉冲后回落等自身因素驱动（承接 31/38 号报告：财报事件独立于大盘），52 号已提示跌破 EMA50 的波段逆风。</p>
<p><b>Warsh 情景影响</b>：<b class="up">中性</b>。加息预期本身不伤 CSCO；利率情景对它的意义仅在于：若加息引发整体 risk-off（高估值成长杀跌），CSCO 作为低估值防御科技反而相对占优。真正的变量是 AI 资本开支节奏与 11 月财报。</p>
<p><b>操作含义</b>：<b>不要用利率叙事解释 CSCO 的 8 月下跌</b>；当前技术面（EMA50 下方）独立于利率，按 52 号组合报告的波段框架处理。</p></div></div>""",
'ABBV': """<div class="stock"><div class="stock-h"><span class="badge b-lo">低敏感防御</span>ABBV · AbbVie（制药，免疫管线龙头）<span style="font-size:12px;color:#666">6 月以来 +21.2%</span></div><div class="stock-b">
<p><b>利率传导机制</b>：长久期现金流资产，理论上对折现率敏感；但防御属性在 risk-off（加息引发的波动）时吸引资金，且 30Y 反跌（通胀溢价下降）反而利好长久期资产估值。基本面（Skyrizi/Rinvoq 增长）是主驱动。</p>
<p><b>实证</b>：Δ10Y 全期 β=−0.05（不显著），近 60 日 β=−0.01（几乎归零）——<b>利率敏感度很低，6 月以来的 +21% 与利率无关</b>。8/27 单日 −2.6%（258.15）回落暂不支持利率归因（回归不显著），更可能为获利回吐/个股消息。</p>
<p><b>Warsh 情景影响</b>：<b class="up">相对占优</b>。加息预期若引发整体波动，医药防御属性受益；即使利率上行，ABBV 的低敏感度意味着估值冲击有限。潜在逆风：若加息过度导致衰退担忧，药企需求韧性强但板块 beta 仍跟随大盘。</p>
<p><b>操作含义</b>：利率情景下医药双雄是组合的"压舱石"；ABBV 基本面逻辑（专利悬崖后的增长接力）不因利率改变。</p></div></div>""",
'JNJ': """<div class="stock"><div class="stock-h"><span class="badge b-lo">低敏感防御</span>JNJ · Johnson &amp; Johnson（医疗综合 / 高股息）<span style="font-size:12px;color:#666">6 月以来 +20.8%</span></div><div class="stock-b">
<p><b>利率传导机制</b>：与 ABBV 同属长久期防御资产；高股息（~3%）提供缓冲，且股息相对无风险利率的吸引力在"利率见顶预期"阶段回升。医疗业务需求刚性 → 加息对盈利端几乎无影响。</p>
<p><b>实证</b>：Δ10Y 全期 β=−0.04（不显著）；<b>近 60 日转正（β=+0.02）</b>——利率上行时段 JNJ 甚至微正相关（防御资金流入），六股中利率免疫最强。</p>
<p><b>Warsh 情景影响</b>：<b class="up">占优</b>。加息预期 → 防御资金再平衡 → JNJ/ABBV 相对受益；30Y 反跌（通胀信誉保全）对高股息长久期资产估值温和利好。风险仅在于大盘系统性下杀时的 beta 拖累（非利率本身）。</p>
<p><b>操作含义</b>：利率风险对冲属性最强的标的；与 ABBV 同属防御压舱石，注意二者已同涨 +21%/+21%，组合内需防"防御板块拥挤回撤"。</p></div></div>""",
}

html = (TEMPLATE
        .replace('@@NODES@@', node_html())
        .replace('@@EXP10@@', f"{exp['d10']:.0f}")
        .replace('@@EXP2@@', f"{exp['d2']:.0f}")
        .replace('@@EXPSP@@', f"{exp['sp']:.0f}")
        .replace('@@PCT10@@', f"{abs(exp['d10'])/(abs(exp['d10'])+abs(exp['d2']))*100:.0f}")
        .replace('@@SENSROWS@@', sens_rows_html())
        .replace('@@CHART_DATA@@', chart_data)
        .replace('@@SENS_JS@@', sens_js))

STOCK_BLOCK = "\n".join(STOCK_HTML[n] for n in ['SOFI', 'MS', 'APO', 'CSCO', 'ABBV', 'JNJ'])
html = html.replace('@@STOCKS@@', STOCK_BLOCK)

outdir = os.path.join(BASE, 'reports', '54_宏观利率背景六股影响')
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"written: {out} size={os.path.getsize(out)}")
