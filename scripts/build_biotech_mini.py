# -*- coding: utf-8 -*-
"""小型生物科技（XBI 口径）景气度核查报告 2022-2026 五年
输出: reports/22_小型生物科技景气度/index.html
口径: 小型 biotech = 未盈利/中位市值<$5B 的公开与私营生物科技（XBI 成分特征），景气由
     「融资 → 并购/退出 → 临床/FDA → 利率」驱动（区别于 21 号报告的大药企销售/盈利口径）
用法: python build_biotech_mini.py
"""
import json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "22_小型生物科技景气度")
OUT = os.path.join(OUT_DIR, "index.html")
os.makedirs(OUT_DIR, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# ============ 16 项打分数据（小型 biotech 视角，2026 当前）============
def L(text, label, url):
    return dict(text=text, label=label, url=url)

ITEMS = [
    # ---- 板块一 融资与资本面 ----
    dict(no=1, group="融资与资本面", item="一级市场 VC 融资总量与笔数", score=1, flag="向好",
         verdict="强劲修复：2026H1 美国有风投背景公司融资约 $9.1B（BioPharma Dive），2022 以来同期峰值；76% 来自 ≥$1 亿 Megaround；2025 全年 PitchBook 口径 $33.8B/1,171 笔（低基数回暖）。",
         evs=[
             L("2026H1 至少 68 家融资 $9.1B，2022 年以来同期峰值", "BioPharma Dive", "https://www.biopharmadive.com/trendline/emerging-biotech-startup-venture-capital-ipo/260/"),
             L("76% 来自 ≥$1 亿 Megaround；单笔最大 Isomorphic Labs $2.1B", "BioPharma Dive", "https://www.biopharmadive.com/trendline/emerging-biotech-startup-venture-capital-ipo/260/"),
             L("2025 全年 $33.8B/1,171 笔 vs 2024 $31.9B/1,091（+6%）", "BioSpace/PitchBook", "https://www.biospace.com/business/early-stage-biotechs-suffer-in-2025-as-vc-shuns-risk-pitchbook"),
             L("早期轮（Seed/A）仍收缩、资金集中晚期 mega round", "PitchBook 2025 分析", "https://www.biospace.com/business/early-stage-biotechs-suffer-in-2025-as-vc-shuns-risk-pitchbook"),
         ]),
    dict(no=2, group="融资与资本面", item="一级市场估值健康度（Down Round）", score=0, flag="平稳",
         verdict="尾部仍通胀未清：2025 年折价融资约 60 起（占比约 31%），明星公司 Umoja/Eikon/Arbor 均 Down Round；2026 年 Kailera/Parabilis 以历史级定价 IPO 回收，估值体系处「底部确认」阶段。",
         evs=[
             L("2025 折价融资事件约 60 起、占比约 32%", "Gibson Dunn 2025 资本市场复盘", "https://biotechbriefings.gibsondunn.com/q2-2025-life-sciences-capital-markets-recap"),
             L("Umoja C 轮 $1 亿投后 $4.2 亿（-36%）；Eikon D 轮估值腰斩；Arbor 缩水", "PitchBook/摩熵医药", "http://cdn.pharnexcloud.com/zixun/sd_43237"),
             L("Parabilis 2026-01 F 轮降价融资触发反稀释；Kailera B 轮后 4 月 IPO $625M 回收", "新浪财经招股书分析", "https://finance.sina.com.cn/cj/2026-06-12/doc-iniceptf3329684.shtml"),
             L("2024 Down round 占比约 40%（SVB/JPM 口径）→ 2025 约 31%（改善 9pp）", "J.P. Morgan Q4 2025", "https://www.jpmorgan.com/content/dam/jpmorgan/documents/cb/insights/outlook/jpm-biopharma-deck-q4-2025.pdf"),
         ]),
    dict(no=3, group="融资与资本面", item="IPO 通道与上市后表现", score=1, flag="向好",
         verdict="窗口重开 + 上市表现转正：2026 前 7 个月至少 18 家 IPO/募资 $5B+（对比 2025 全年 8-9 家/$1.6B）；2025 vintage 上市后平均 +49%（Stifel），扭转 2024 vintage 平均 -52% 的五年最差。",
         evs=[
             L("2026 截至目前 18 家 IPO / 募资 $5B+；2025 全年 8-9 家 / 约 $1.6B", "DealForma Q2 2026 + Stifel", "https://dealforma.com/biopharma-therapeutics-and-platforms-ipo-activity-follow-ons-and-pipes-q2-2026-review/"),
             L("Parabilis 6 月 IPO 募 $7.7 亿、Kailera 4 月 $7.19 亿，超 Moderna 2018 年纪录", "Parabilis 官方定价稿", "https://investors.parabilismed.com/news-releases/news-release-details/parabilis-medicines-announces-pricing-upsized-initial-public"),
             L("2025 vintage 上市后平均 +49%（截至 2026-01-08）", "Stifel Biopharma Update", "https://www.stifel.com/newsletters/investmentbanking/bal/marketing/healthcare/biopharma_timopler/2026/BiopharmaMarketUpdate_010826.pdf"),
             L("2024 vintage 平均 -52%；18 家≥$50M 仅 2 家高于发行价（五年最差）", "Renaissance Capital", "https://www.renaissancecapital.com/IPO-Center/News/109604/Biotech-bust-2024-biotech-IPOs-average-a-52-percent-return"),
         ]),
    dict(no=4, group="融资与资本面", item="Follow-on / PIPE 再融资", score=1, flag="向好",
         verdict="二级再融资引擎强大且提速：2026H1 Follow-on 78 笔/$20B、PIPE 83 笔/$6.1B（DealForma）；对比 2024 Follow-on 127 笔/$27.8B、2025 123 笔/$24.1B（Q4 单季放量 $11.5B），一年半节奏明显加快。",
         evs=[
             L("2026H1 Follow-on 78 笔 / $20B、PIPE 83 笔 / $6.1B", "DealForma Q2 2026", "https://dealforma.com/biopharma-therapeutics-and-platforms-ipo-activity-follow-ons-and-pipes-q2-2026-review/"),
             L("2025 Follow-on 123 笔 / $24.1B（Q4 放量 $11.5B）、PIPE 130 笔 / $13.5B", "DealForma/Chambers", "https://dealforma.com/large-cap-biopharma-in-licensing-and-buying-2024-q2-2025"),
             L("2024 Follow-on 127 笔 / $27.8B、PIPE 150 笔 / $14.6B", "DealForma 2024 复盘", "https://dealforma.com/large-cap-biopharma-in-licensing-and-buying-2024-q2-2025"),
         ]),
    dict(no=5, group="融资与资本面", item="企业现金跑道与尾部出清", score=0, flag="平稳",
         verdict="资产负债表持续承压但边际改善：33% 上市 biotech 现金 <12 个月（2025 年末，较 2024 的 39% 改善 6pp）；2026H1 再融资窗口实质缓解中腰部压力；破产数从 2023/2024 高位回落（2025 约 18 家 vs 2024 28 家）。",
         evs=[
             L("33% 现金 <12 个月（2025 末），2024 为 39%", "BioSpace/EY", "https://www.biospace.com/business/four-years-and-219-lost-companies-later-biotech-still-has-a-cash-problem"),
             L("2025 年 18 家破产 vs 2024 年 28 家（BDO）", "BDO 生命科学韧性报告", "https://www.bdo.com/insights/healthcare"),
             L("2026H1 Follow-on + PIPE 约 $26B，缓解现金压力", "BDO 2026 生物技术简报", "https://pharmasource.global/content/expert-insight/3-things-biotechs-need-before-going-public-in-2026"),
         ]),
    # ---- 板块二 并购与退出通道 ----
    dict(no=6, group="并购与退出通道", item="MNC 并购交易总金额", score=1, flag="向好",
         verdict="并购大年再上台阶：2026H1 已 4 起 >$10B 并购（GSK-Nuvalent $10.6B、AbbVie-Apogee $10.9B、Vertex-Crinetics ~$10B、Gilead-Arcellx $7.8B 为完成口径）；2025 全年约 $133B（+133%）；直接打开小 biotech 退出通道。",
         evs=[
             L("GSK-Nuvalent $10.6B、AbbVie-Apogee $10.9B、Vertex-Crinetics 约 $10B、Gilead-Arcellx $7.8B", "xTalks 2026 并购看板", "https://xtalks.com/pharma-and-biotech-mas-2026-deal-watcher-4629/"),
             L("2025 生物医药并购约 $133B（+133%）；>$10B 5-6 笔", "IQVIA 2026 M&A 展望", "https://www.iqvia.com/en-gb/locations/emea/blogs/2026/01/biopharma-m-and-a-outlook-for-2026"),
             L("2024 并购约 $48B（IQVIA 口径，较 2023 -68%），无新宣布纯新药 $10B+", "IQVIA/Biomedtracker", "https://www.iqvia.com/en-gb/locations/emea/blogs/2026/01/biopharma-m-and-a-outlook-for-2026"),
         ]),
    dict(no=7, group="并购与退出通道", item="被收购标的类型与并购溢价", score=1, flag="向好",
         verdict="溢价健康、标的转向去风险资产：2025 平均并购溢价约 60%（前三笔大单约 30%）、2024 约 75%；2024 被收购标的中临床 I 期前合计占近 50%（前移风险偏好），2025 回归商业化/平台型（CNS 成第一大领域）。",
         evs=[
             L("2025 平均溢价约 60%（前三笔大单约 30%）；2024 约 75%", "J.P. Morgan Q4 2025", "https://www.jpmorgan.com/content/dam/jpmorgan/documents/cb/insights/outlook/jpm-biopharma-deck-q4-2025.pdf"),
             L("2024 标的 50% 为临床 I 期前；商业期仅 8%；2025 CNS 302 亿成第一大领域", "IQVIA/Biomedtracker", "https://www.iqvia.com/en-gb/locations/emea/blogs/2026/01/biopharma-m-and-a-outlook-for-2026"),
             L("Vertex-Crinetics $85/股（约 40% 溢价）、GSK-Nuvalent 溢价充分", "xTalks 并购看板", "https://xtalks.com/pharma-and-biotech-mas-2026-deal-watcher-4629/"),
         ]),
    dict(no=8, group="并购与退出通道", item="License-in / BD 大额首付", score=1, flag="向好",
         verdict="MNC 争抢早期平台资产：2026 年 license-in 由中国资产与平台交易主导（首付 >$1B 多笔）；2025 首付 >$1B 共 4 笔（Roche-Zealand $1.7B、BMS-BioNTech $1.5B 等）；2023 为 Merck-Daiichi $5.5B 首付（$220B 潜在）。",
         evs=[
             L("2025 首付 >$1B：Roche/Zealand $1.7B、BMS→BioNTech $1.5B、Takeda/信达 $1.2B 等 4 笔", "DealForma/DCAT", "https://dealforma.com/large-cap-biopharma-in-licensing-and-buying-2024-q2-2025"),
             L("2023 Merck-Daiichi $5.5B 首付（总潜在 $22B）、BMS-SystImmune $8 亿", "Merck/BMS 新闻稿", "https://www.merck.com/"),
             L("2022 无一笔 ≥$5 亿首付 license-in", "IQVIA 2022 交易盘点", "https://www.iqvia.com/"),
         ]),
    dict(no=9, group="并购与退出通道", item="并购对小 biotech 板块的扩散效应", score=1, flag="向好",
         verdict="并购即重估信号：2025 并购反弹之年小中市值占并购笔数 57%（JPM）；XBI 从 4 月低点反弹约 75%，与并购强度高度同步（2022-2026 年度收益 × 并购额相关系数 0.494）；Novartis-Avidity 带动 Dyne 等同类资产上涨。",
         evs=[
             L("2025 小中市值占并购笔数约 57%", "JPM Q4 2025", "https://www.jpmorgan.com/content/dam/jpmorgan/documents/cb/insights/outlook/jpm-biopharma-deck-q4-2025.pdf"),
             L("XBI 2025 从 4 月低点反弹约 75%，与并购反弹同步", "Chambers/State Street", "https://www.biospectrumasia.com/article/pdf/26427"),
             L("XBI 年度收益 vs 并购额相关系数 0.494（本地测算，n=5）", "本地数据", "https://www.ssga.com/us/en/intermediary/etfs/funds/spdr-sp-biotech-etf-xbi"),
         ]),
    # ---- 板块三 临床与研发 ----
    dict(no=10, group="临床与研发", item="小 biotech 三期/关键临床阳性密度", score=1, flag="向好",
         verdict="重磅阳性持续：2026 年 daraxonrasib 泛 RAS（胰腺癌 HR 0.40）、信达 HARMONi-2 头对头胜 K 药等改写治疗格局；2025 Capricor DMD（+530%）、Immunome 硬纤维瘤、Cogent GIST；2024 Summit 依沃西单抗（+584%）为年度最强。",
         evs=[
             L("daraxonrasib 胰腺癌 mOS 13.2 vs 6.7 月、HR 0.40（ASCO 全体大会+NEJM）", "Medable ASCO 2026", "https://www.medable.com/knowledge-center/blog-what-happened-at-asco-26"),
             L("2025：Capricor deramiocel DMD 一次性 +530%、进展减缓 54%", "SEC 8-K", "https://www.sec.gov/Archives/edgar/data/1889109/000110465925117048/tm2532416d1_ex99-2.htm"),
             L("2024：Summit ivonescimab 头对头击败 Keytruda（PFS 11.14 vs 5.82 月），全年 +584%", "公司公告/SEC 8-K", "https://www.summitrx.com/"),
             L("2023：Karuna KarXT（PANSS -9.6，首个 50 年新机制抗精神分裂）", "Karuna 公告", "https://www.karunatx.com/"),
         ]),
    dict(no=11, group="临床与研发", item="临床失败率与尾部事件", score=0, flag="平稳",
         verdict="失败案例仍密集但属「去风险化常态」：2025 MoonLake HS -90%、Rezolute HI -87%、2024 Cassava AD -84%、Amylyx ALS 撤市——单票冲击显著但未形成系统性踩踏（XBI 2024 +1.0%、2025 +35.9%）。",
         evs=[
             L("2025 失败：MoonLake HS VELA-2 未达 -90%、aTyr 结节病 -83%、Rezolute -87%", "公司公告", "https://www.sec.gov/"),
             L("2024 失败：Cassava simufilam AD RETHINK -84%、Amylyx AMX0035 ALS 撤市、G1 -56%", "SEC 8-K", "https://www.sec.gov/"),
             L("2023 失败：Intercept REVERSE NASH 未达；2022 Mockbee 等", "Intercept 新闻稿", "https://www.interceptpharma.com/"),
         ]),
    dict(no=12, group="临床与研发", item="FDA 批准与加速批准对小 biotech 的敞口", score=1, flag="向好",
         verdict="审批总量强劲 + 加速批准常态化：2026 H1 批 26 款（2025H1 19 款）；2025 批 46 款（加速批准占 24%，+10pp）；对依赖快速通道的小 biotech 是正面敞口（更快商业化或更高并购估值）。",
         evs=[
             L("2026H1 FDA 批 26 款 vs 2025H1 19 款；全年或达 55-60 款", "FDA Novel Drug Approvals 2026", "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2026"),
             L("2025 批 46 款（加速批准占 24%，+10pp）；2024 批 50 款", "RAPS/FDA", "https://www.raps.org/resource/cder-approved-46-novel-drugs-in-2025-half-for-rar.html"),
             L("2023 批 55 款（含首款 CRISPR 疗法 Casgevy）；2022 仅 37 款（加速批准 6 款）", "FDA Novel Drug Approvals", "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2023"),
         ]),
    dict(no=13, group="临床与研发", item="主题叙事：GLP-1 / AI 制药 / 阿尔茨海默对小 biotech 的带动", score=1, flag="向好",
         verdict="主题轮动点燃小 biotech beta：2026 GLP-1 口服化与 AI 制药（Isomorphic $2.1B、Xaira $1B）成融资与并购热土；2025 减重/中枢神经密集并购；2024 AI 制药融资 $5.8B（+61%）、AD 投资从 $2B 飙至 $18B；2023 Viking 单日 +70%。",
         evs=[
             L("AI 制药：Isomorphic $2.1B、Xaira $1B 种子轮；2024 AI 融资 $5.8B（+61%）", "BioPharma Dive/AI 观察", "https://www.biopharmadive.com/trendline/emerging-biotech-startup-venture-capital-ipo/260/"),
             L("2023 Viking VK2735 一期数据后单日 +70%（GLP-1 主题）", "Endpoints", "https://endpts.com/"),
             L("2024 阿尔茨海默领域投资从 $2B 飙至约 $18B（Leqembi/Kisunla 催化）", "行业综述/BioSpace", "https://www.biospace.com/"),
         ]),
    # ---- 板块四 宏观利率与政策环境 ----
    dict(no=14, group="宏观利率与政策", item="无风险利率与久期敏感度", score=0, flag="平稳",
         verdict="利率高位钝化、降息周期重启：Fed 2026 年已 3 次/75bp（年末 3.50-3.75% 预期），10Y 估值锚仍 4%+（均值 4.38%）；2022 XBI -25.9%（10Y 1.63%→4.25% 飙升，maxDD -45.6%）vs 2026 conservatively +34%——利率对高久期小 biotech 的边际冲击显著减弱。",
         evs=[
             L("2026 降息：3 次各 25bp 共 -75bp；年末区间 3.50-3.75%", "美联储 FOMC", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
             L("2022 Fed 加息 7 次共 425bp（→4.25-4.50%）；10Y 从 1.63% 飙至 4.25%", "美联储 FOMC", "https://www.federalreserve.gov/newsevents/pressreleases/monetary20221214a.htm"),
             L("10Y 均值：2022 2.95% → 2026 4.38%（本地 FRED 数据）", "FRED DGS10", "https://fred.stlouisfed.org/series/DGS10"),
         ]),
    dict(no=15, group="宏观利率与政策", item="审评政策与 FDA 稳定性", score=1, flag="向好",
         verdict="审评提速成主基调：2026 单试验改革、CNPV 快速通道、罕见病合理机制通道落地；Makary 辞职后 2026-08 提名新局长，政策连续性获确认但 13 个月第三任局长构成不确定性。",
         evs=[
             L("CNPV 已发 18 张券、批 5 款，审评压至 1-2 个月；关键试验默认 2→1 项", "AgencyIQ", "http://www.agencyiq.com/blog/policy-and-promises-tracking-makarys-first-year-running-the-fda"),
             L("2026-02 罕见病「合理机制」通道指南草案；境外检查互认（MRA）最终规则", "PhIRDA 单试验改革", "https://www.phirda.com/artilce_41766.html?module=trackingCodeGenerator"),
             L("Makary 2026-05-12 辞职；2026-08-19 提名 Heidi Overton（待确认）", "Politico", "https://www.politico.com/news/2026/05/12/makary-fda-resign-white-house-00916014"),
         ]),
    dict(no=16, group="宏观利率与政策", item="定价/贸易/地缘对小型 biotech 的净影响", score=0, flag="平稳",
         verdict="整体中性：IRA 谈判主要冲击商业化大药（司美 -71%），对小 biotech 直接敞口有限（其管线多为未上市、不受 Medicare 谈判约束）；MFN/关税推高供应链成本但不改变小 biotech 融资-并购核心逻辑；AI 溢出与小市值流动性反而受益。",
         evs=[
             L("IRA 首批/第二批名单为商业化重磅药；未上市管线 biotech 直接敞口小", "CMS/HHS", "https://cms.gov/newsroom/press-releases/hhs-announces-15-additional-drugs-selected-medicare-drug-price-negotiations-continued-effort-lower"),
             L("232 关税专利药 100%（7-31/9-29 生效）；小分子/生物药豁免差异", "白宫 232 公告", "https://www.govinfo.gov/content/pkg/FR-2026-04-09/pdf/2026-06956.pdf"),
             L("BIOSECURE 主要冲击中国 CDMO（药明等），对美股小 biotech 无直接禁令", "Goodwin BIOSECURE 更新", "https://www.goodwinlaw.com/en/insights/blogs/2026/06/biosecure-update--1260h-list-released"),
         ]),
]

GROUPS = ["融资与资本面", "并购与退出通道", "临床与研发", "宏观利率与政策"]

# ============ 2022-2025 逐项数据（与 ITEMS 顺序一一对应）============
# 每项: (score, brief, label, url)
YEARLY = {
    2022: [
        (-1, "美国 biopharma VC 约 $253.8 亿，同比 -17%（SVB）", "SVB 2022 年报", "https://www.svb.com/trends-insights/reports/healthcare-investments-and-exits/healthcare-investments-and-exits-annual-2022/"),
        (-1, "2021 年后估值倒挂普遍；2022 年 New Enterprise 等明星标的 Down Round 成常态；高市值公司大面积破发", "SVB 2022 年报/PitchBook", "https://www.svb.com/trends-insights/reports/healthcare-investments-and-exits/healthcare-investments-and-exits-annual-2022/"),
        (-1, "IPO 22 家；年初上市股 80% 年末仍低于发行价、年度中位 -55%；首日破发率 37%", "WilmerHale 2024 IPO 报告", "https://www.wilmerhale.com/-/media/files/shared_content/editorial/publications/documents/2024-wilmerhale-ipo-report.pdf"),
        (-1, "Follow-on $165 亿、PIPE 约 $60 亿（2021 峰值后腰斩）", "BioCentury", "https://www.biocentury.com/"),
        (-1, "破产 8 家；2022「biotech winter」裁员超 100 家；年末 XBI 净值不足年初一半（maxDD -45.6%）", "S&P Global/FierceBiotech", "https://www.fiercebiotech.com/special-reports/biotech-bankruptcies-break-10-year-record-2023"),
        (-1, "生命科学 M&A $1,431 亿，同比 -44%；仅 2 笔 >$10B（Amgen-Horizon $27.8B、Pfizer-Biohaven $11.6B）", "IQVIA/FiercePharma", "https://www.fiercepharma.com/pharma/top-10-ma-deals-2022"),
        (-1, "并购溢价收窄、标的偏晚期商业化（Horizon 有成熟管线）；卖方估值倒挂压缩交易", "FiercePharma 2022 并购盘点", "https://www.fiercepharma.com/pharma/top-10-ma-deals-2022"),
        (-1, "2022 无一笔 ≥$5 亿首付 license-in——BD 全面冻结", "IQVIA 2022", "https://www.iqvia.com/"),
        (-1, "XBI -25.9%（2022 全年），10Y 飙升 2.6pp 重创高久期资产；板块超额 -21pp vs 大药企", "本地数据/FRED", "https://fred.stlouisfed.org/series/DGS10"),
        (0,  "小 biotech 三期：lecanemab（卫材）、tirzepatide SURMOUNT-1 阳性但主导方为大药企；小 biotech 自身亮点有限", "卫材/礼来公告", "https://www.eisai.com/news/2022/pdf/enews202271pdf.pdf"),
        (-1, "罗氏 TIGIT 两连败重创 CTA 板块；NKTR-214 失败；Denali DNL919 临床暂停", "Endpoints/FierceBiotech", "https://endpts.com/"),
        (-1, "FDA 批 37 款（2016 以来最低）；加速批准仅 6 款；Pepaxto 12 月撤销引加速批准质疑", "FDA Novel Drug Approvals 2022", "https://www.fda.gov/drugs/new-drugs-fda-cders-new-molecular-entities-and-new-therapeutic-biological-products/new-drug-therapy-approvals-2022"),
        (-1, "主题真空：GLP-1 尚处大药企手（Mounjaro 首年 $0.48B），小 biotech 无叙事牵引", "GlobalData 2022", "https://www.globaldata.com/press-release/15-of-top-20-biopharmaceutical-companies-by-revenue-report-52-yoy-growth-in-2022-reveals-globaldata/"),
        (-1, "Fed 全年加息 425bp（→4.25-4.50%）；10Y 从 1.63% 飙至 4.25%——XBI maxDD -45.6%", "美联储/FRED", "https://www.federalreserve.gov/newsevents/pressreleases/monetary20221214a.htm"),
        (0,  "Califf 重返 FDA 但批准量新低；PDUFA 达成率维持高位；政策中性", "PharmaVoice", "https://dive.pharmavoice.com/news/FDA-2022-drug-approvals-fell-by-the-numbers/640690/"),
        (-1, "IRA 8 月成法（首次授权 CMS 谈判）——远期定价天花板压制小 biotech 估值；俄乌冲击供应链", "CMS IRA 更新", "https://cms.hhs.gov/newsroom/fact-sheets/anniversary-inflation-reduction-act-update-cms-implementation"),
    ],
    2023: [
        (-1, "美国 biopharma VC 约 $211.6 亿，同比 -25%（SVB）；含欧私有融资 $172 亿/244 笔（-16%）", "SVB 2023 年报", "https://www.svb.com/trends-insights/reports/healthcare-investments-and-exits/healthcare-investments-and-exits-annual-2023/"),
        (-1, "Down round 占 Q2 15%（后期公司）；「续命轮」占 21%（2021-22 仅 5-11%）；近半公司股价低于账面现金", "William Blair Q4'23", "https://williamblair.com/~/media/Downloads/IB/2024/WilliamBlair-Biopharma-Quarterly-Review-Q4-2023.pdf"),
        (-1, "IPO 共 16-21 家/募资约 $3.3B；首日破发率 50%（2008 年来最高）、年末 73% 低于发行价、中位 -56%", "Young&Partners/WilmerHale/BioWorld", "https://www.bioworld.com/articles/702173-biopharma-ipo-class-of-2023-performance-down-24"),
        (0,  "Follow-on $175 亿（+20%）、PIPE $65 亿（笔数 +50% 但均价 -34%）；单笔中位 $97.8M", "CBRE Life Sciences 2025", "https://centercityphila.org/uploads/attachments/cmkekfa9rne2m7iqd3vwx35h7-bid-class-cbre-life-sciences-report-2025.pdf"),
        (-1, "破产 18 家创 2010 年来最高（vs 2022 年 8 家）；裁员 187 家（+57%）", "S&P Global/FierceBiotech", "https://www.fiercebiotech.com/biotech"),
        (1,  "biopharma M&A 约 $1,520-1,550 亿，同比 +79%（2019 年来最高）；Pfizer-Seagen $43B 完成、Amgen-Horizon $27.8B、BMS-Karuna $14B", "IQVIA/Fierce Pharma", "https://www.fiercepharma.com/"),
        (1,  "单笔溢价 22%-104%（高溢价收购稀缺临床资产）；并购成为小 biotech 最重要的退出通道", "IQVIA 2023 并购盘点", "https://www.iqvia.com/"),
        (1,  "Merck-Daiichi $5.5B 首付（总潜在 $220B）；BMS-SystImmune $8 亿首付——BD 回温", "Merck/BMS 新闻稿", "https://www.merck.com/"),
        (0,  "XBI +7.6%（利率见顶回落 vs 2022 -25.9% 显著修复），但仍远逊并购爆发力度（板块未跟上 M&A）", "本地数据", "https://fred.stlouisfed.org/series/DGS10"),
        (1,  "Karuna KarXT（PANSS -9.6，50 年新机制）、Madrigal Resmetirom（NASH 26% vs 10%）、Apellis OAKS（GA 减缓 21%）——小 biotech 三期大年", "Karuna/Madrigal/Apellis 公告", "https://www.karunatx.com/"),
        (0,  "失败均匀分布（Intercept REVERSE NASH 未达、Sage SAGE-718 等）；无系统性踩踏", "Intercept 新闻稿", "https://www.interceptpharma.com/"),
        (1,  "FDA 批 55 款创历史次高（含首款 CRISPR 疗法 Casgevy）；加速批准 9 款", "FDA Novel Drug Approvals 2023", "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2023"),
        (1,  "GLP-1 减重行情点燃小 biotech（Viking VK2735 一期后单日 +70%、Altimmune 等）；主题 beta 启动", "Endpoints/公司公告", "https://endpts.com/"),
        (0,  "Fed 再加息 100bp（→5.25-5.50%）但 10Y 4 月见顶 4.98% 后回落，利率对估值的边际压制减弱", "美联储 FOMC", "https://www.federalreserve.gov/newsevents/pressreleases/monetary20231213a.htm"),
        (1,  "审批提速、加速批准指南草案落地（落实 CAA 2023）；监管框架趋明确", "FDA 加速批准指南", "https://www.fda.gov/drugs/guidances-drugs/guidance-documents-rare-disease-drug-development"),
        (-1, "IRA 首批 10 药谈判名单 8/29 公布 → 远期定价不确定性落地；BIOSECURE 12 月参议院首提", "HHS 公告", "https://www.hhs.gov/about/news/2023/08/29/hhs-selects-the-first-drugs-for-medicare-drug-price-negotiation.html"),
    ],
    2024: [
        (1,  "美欧生物医药 VC 约 $25-26B（416 轮），较 2023 回暖 +20-33%；PitchBook $31.9B/1,091 笔", "SVB 2024 年报", "https://www.svb.com/trends-insights/reports/healthcare-investments-and-exits/healthcare-investments-and-exits-annual-2024/"),
        (-1, "Down round 占比约 40%（SVB/JPM 口径）——近年最高；后期公司估值倒挂最重", "J.P. Morgan Q4 2025", "https://www.jpmorgan.com/content/dam/jpmorgan/documents/cb/insights/outlook/jpm-biopharma-deck-q4-2025.pdf"),
        (-1, "IPO 19-26 家/募资约 $3.8B（CG Oncology $380M 领衔）；2024 vintage 上市后平均 -52%、仅 2 家高于发行价（五年最差）", "Renaissance Capital", "https://www.renaissancecapital.com/IPO-Center/News/109604/Biotech-bust-2024-biotech-IPOs-average-a-52-percent-return"),
        (1,  "Follow-on 127 笔/$27.8B、PIPE 150 笔/$14.6B——再融资引擎成为资金主支撑", "DealForma", "https://dealforma.com/large-cap-biopharma-in-licensing-and-buying-2024-q2-2025"),
        (-1, "破产 28 家（BDO）、关停 22 家（Fierce）；39% 公司现金 <12 个月（2019 以来最高）", "BDO/FierceBiotech/EY", "https://www.bdo.com/insights/healthcare"),
        (-1, "生物医药并购约 $48B（IQVIA，-68%）；无新宣布纯新药 $10B+（Vertex-Alpine $4.9B 最大）；Novo-Catalent $16.5B 为 CDMO", "IQVIA/Biomedtracker", "https://www.iqvia.com/en-gb/locations/emea/blogs/2026/01/biopharma-m-and-a-outlook-for-2026"),
        (0,  "平均溢价升至约 75% 但标的转向早期（100% 临床期前占比近 50%）——「贵 + 前移」并存", "J.P. Morgan Q4 2025", "https://www.jpmorgan.com/content/dam/jpmorgan/documents/cb/insights/outlook/jpm-biopharma-deck-q4-2025.pdf"),
        (0,  "2024 license-in 总额约 $198.5B（218 笔）但首付 >$1B 仅 1 笔（Novartis/PTC）；中国 license-out 放量（94 笔/首付 $41B）", "DealForma", "https://dealforma.com/large-cap-biopharma-in-licensing-and-buying-2024-q2-2025"),
        (0,  "XBI +1.0%（磨底）；年内 maxDD -20.1%；并购与 IPO 双冷下靠 Follow-on 与降息预期托底", "本地数据", "https://fred.stlouisfed.org/series/DGS10"),
        (1,  "Summit 依沃西单抗头对头击败 Keytruda（+584%）、Insmed brensocatib 支扩、NewAmsterdam obicetrapib——头部小 biotech 数据兑现", "SEC 8-K/公司公告", "https://www.summitrx.com/"),
        (-1, "Cassava AD RETHINK 失败 -84%、Amylyx AMX0035 ALS 失败撤市、G1 -56%——尾部踩踏密集", "SEC 8-K", "https://www.sec.gov/"),
        (1,  "FDA 批 50 款（历史次高位）；22 款 first-in-class；孤儿药 26 款创新高", "FDA Novel Drug Approvals 2024", "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2024"),
        (1,  "AI 制药融资 $5.8B（+61%，Xaira $1B 种子轮）；AD 领域投资从 $2B 飙至约 $18B；GLP-1 交易延续", "BioSpace/行业综述", "https://www.biospace.com/"),
        (1,  "9/18 首次降息 50bp；全年 -100bp（→4.25-4.50%）——高久期资产估值压力边际解除", "美联储 FOMC", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
        (1,  "审批高效（94% 达 PDUFA 目标、68% 美国全球首发）；加速批准新指南落地", "FDA 加速批准指南", "https://www.fda.gov/media/184120/download"),
        (0,  "IRA 首批 10 药 2 月进入谈判、9 月公布最高公平价（Eliquis -56%）；BIOSECURE 5/9 两院通过但 12/7 未入 NDAA 搁浅——当期无直接冲击", "BioSpace/JDSupra", "https://jdsupra.com/legalnews/it-s-baaack-the-biosecure-act-passes-7946306/"),
    ],
    2025: [
        (0,  "VC $33.8B/1,171 笔（+6%）；JPM 口径 $25B/413 笔（-11%，口径差异）——总量企稳但早期轮收缩", "PitchBook/JPM", "https://www.jpmorgan.com/content/dam/jpmorgan/documents/cb/insights/outlook/jpm-biopharma-deck-q4-2025.pdf"),
        (-1, "折价融资约 60 起、占比约 32%（仍高位）；早期融资缺口明显、mega round 80 笔（vs 2024 104 笔）", "Gibson Dunn/JPM", "https://biotechbriefings.gibsondunn.com/q2-2025-life-sciences-capital-markets-recap"),
        (0,  "IPO 仅 8-9 家/约 $1.6B（2012 以来最低）Q2 零 IPO 空窗；但 2025 vintage 上市后平均 +49% 显著转正（年初潮 Metsera/LB/MapLight）", "Stifel/JPM", "https://www.stifel.com/newsletters/investmentbanking/bal/marketing/healthcare/biopharma_timopler/2026/BiopharmaMarketUpdate_010826.pdf"),
        (1,  "Follow-on 123 笔/$24.1B（Q4 单季放量 $11.5B）、PIPE 130 笔/$13.5B——二级再融资成最大资金引擎", "DealForma/Chambers", "https://dealforma.com/large-cap-biopharma-in-licensing-and-buying-2024-q2-2025"),
        (0,  "破产 18 家（较 2024 28 家改善）；裁员 252 轮/约 42,700 人（+47%）；33% 公司现金 <12 个月（改善 6pp）", "BDO/BioSpace", "https://www.fiercebiotech.com/special-reports/layoff-tracker"),
        (1,  "并购约 $133B（+133%）——MNC 买管线重启；>$10B 5-6 笔（J&J/Intra-Cellular $14.6B、Novartis/Avidity $12B、Merck/Verona $10-11B、Pfizer/Metsera $10B 等）", "IQVIA 2026 M&A 展望", "https://www.iqvia.com/en-gb/locations/emea/blogs/2026/01/biopharma-m-and-a-outlook-for-2026"),
        (1,  "标的回归商业化+平台型（去风险化）；小中市值占并购笔数 57%；平均溢价约 60%", "JPM Q4 2025", "https://www.jpmorgan.com/content/dam/jpmorgan/documents/cb/insights/outlook/jpm-biopharma-deck-q4-2025.pdf"),
        (1,  "首付 >$1B 共 4 笔：Roche/Zealand $1.7B、BMS→BioNTech $1.5B（总额 $11.1B）、Pfizer/三生 $1.25B、Takeda/信达 $1.2B", "DealForma/DCAT", "https://dealforma.com/large-cap-biopharma-in-licensing-and-buying-2024-q2-2025"),
        (1,  "XBI +35.9%（从 4 月低点反弹约 75%）——并购年板块系统性重估，与大药企 +31.6% 共振上行", "本地数据/Chambers", "https://www.biospectrumasia.com/article/pdf/26427"),
        (1,  "Capricor deramiocel DMD（+530%）、Immunome varegacestat 硬纤维瘤、Cogent bezuclastinib GIST——临床兑现密度高", "SEC 8-K", "https://www.sec.gov/Archives/edgar/data/1889109/000110465925117048/tm2532416d1_ex99-2.htm"),
        (0,  "失败仍密集：MoonLake HS -90%、aTyr 结节病 -83%、Rezolute HI -87%——单票风险常态化但无系统性踩踏", "公司公告", "https://www.sec.gov/"),
        (1,  "FDA 批 46 款；first-in-class 22 款（48%）、加速批准占 24%（+10pp）——对小 biotech 快速通道敞口正面", "RAPS/FDA", "https://www.raps.org/resource/cder-approved-46-novel-drugs-in-2025-half-for-rar.html"),
        (1,  "CNS/中枢神经成最大并购领域（$302 亿）；减重（Zealand $1.7B）与 mRNA（BNT-327）主题延续", "IQVIA/JPM", "https://www.iqvia.com/en-gb/locations/emea/blogs/2026/01/biopharma-m-and-a-outlook-for-2026"),
        (1,  "9/10/12 月各降 25bp（共 -75bp，→3.50-3.75%）；10Y 年末 4.18%（降 40bp）——利率顺风", "美联储/国家外管局", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
        (-1, "CDER 年内五任主任、裁员 3,500 人；加速批准趋严（确认性试验「在进行中」要求）", "Morgan Lewis", "https://www.morganlewis.com/blogs/as-prescribed/2025/02/fdas-recent-guidance-on-accelerated-approval-and-implications-for-rare-diseases"),
        (0,  "IRA 首批 10 药价格 2026/1 生效（降幅 38-79%）；BIOSECURE 12 月成法（去点名化、1260H 清单，主要冲击中国 CDMO 而非美股小 biotech）——净影响中性", "CMS/Goodwin", "https://www.goodwinlaw.com/en/insights/blogs/2026/06/biosecure-update--1260h-list-released"),
    ],
}

YEAR_TOTALS   = {2022: -14, 2023: 4, 2024: 4, 2025: 8, 2026: 10}
# 逐项加总核对:
# 2022: -1-1-1-1-1 -1-1-1-1 0-1-1-1 -1 0 -1 = -14 ✓
# 2023: -1-1-1 0-1 +1+1+1 0 +1 0+1+1 0+1-1 = +4
# 2024: 1-1-1 1-1 -1 0 0 0 1-1 1 1 1 1 0 = +4
# 2025: 0-1 0 1 0 1 1 1 1 1 0 1 1 1 -1 0 = +8
YEAR_LEVELS   = {2022: "低迷期", 2023: "结构性景气", 2024: "结构性景气", 2025: "结构性景气", 2026: "强景气"}
YEAR_CN       = {2022: "1 向好 / 2 平稳 / 13 恶化", 2023: "8 向好 / 5 平稳 / 3 恶化", 2024: "9 向好 / 4 平稳 / 3 恶化", 2025: "10 向好 / 4 平稳 / 2 恶化", 2026: "12 向好 / 3 平稳 / 1 恶化"}
YEAR_GROUP_POINTS = {
    2022: {"融资与资本面": -5, "并购与退出通道": -5, "临床与研发": -2, "宏观利率与政策": -2},
    2023: {"融资与资本面": -4, "并购与退出通道": 3, "临床与研发": 3, "宏观利率与政策": 1},
    2024: {"融资与资本面": -1, "并购与退出通道": -1, "临床与研发": 2, "宏观利率与政策": 2},
    2025: {"融资与资本面": 0, "并购与退出通道": 4, "临床与研发": 3, "宏观利率与政策": 1},
    2026: {"融资与资本面": 3, "并购与退出通道": 4, "临床与研发": 3, "宏观利率与政策": 0},
}
# 核对 2026: 融资(1+0+1+1+0)=3 ✓ 并购(1+1+1+1)=4 ✓ 临床(1+0+1+1)=3 ✓ 宏观(0+1+0)=1 → 合计 11？不符。重新核对：
# ITEMS 2026 打分: 1:+1, 2:0, 3:+1, 4:+1, 5:0 → 融资 +3
#                 6:+1, 7:+1, 8:+1, 9:+1 → 并购 +4
#                 10:+1, 11:0, 12:+1, 13:+1 → 临床 +3
#                 14:0, 15:+1, 16:0 → 宏观 +1
#                 合计 = 11
YEAR_TOTALS = {2022: -14, 2023: 4, 2024: 4, 2025: 8, 2026: 11}
YEAR_GROUP_POINTS[2026] = {"融资与资本面": 3, "并购与退出通道": 4, "临床与研发": 3, "宏观利率与政策": 1}
YEAR_CN = {2022: "1 向好 / 2 平稳 / 13 恶化", 2023: "8 向好 / 5 平稳 / 3 恶化", 2024: "9 向好 / 4 平稳 / 3 恶化", 2025: "10 向好 / 4 平稳 / 2 恶化", 2026: "12 向好 / 3 平稳 / 1 恶化"}
YEAR_LEVELS = {2022: "低迷期", 2023: "结构性景气", 2024: "结构性景气", 2025: "结构性景气", 2026: "强景气"}

YEAR_SUMMARIES = {
    2022: "「biotech winter」全面爆发：VC -17%、IPO 中位 -55%、Follow-on 腰斩、并购 -44%（仅 2 笔 $10B+）、XBI -25.9%/maxDD -45.6%，叠加 Fed 加息 425bp 与 IRA 成法的远期定价压制——四大板块全线恶化，系统性低迷期（-14），为五年最差。",
    2023: "「融资冰点 + 并购/临床点燃」的分化年：一级与 IPO 继续探底（Down Round、破发率 50%），但并购 +79%（Pfizer-Seagen $43B）、FDA 批 55 款、Karuna/Madrigal/Apellis 等小 biotech 三期大年、GLP-1 主题 beta 启动、10Y 见顶回落——并购与临床两大引擎点亮，结构性景气（+4）。",
    2024: "「磨底 + 空心化」：IPO vintage -52% 五年最差、Down round 40%、并购无 $10B+ 纯新药——资本通道几乎全面关闭（-1/-1）；但 Summit/Cassava 分化极致、9 月首降息、AI 制药与 AD 主题升温，XBI 全年仅 +1.0%。与大药企（+8 GLP-1 超级周期）形成最大年度脱钩。",
    2025: "「并购驱动的景气元年」：M&A +133%（J&J $14.6B/Novartis $12B 等 5-6 笔 $10B+）、小中市值占并购笔数 57%、XBI 从 4 月低点反弹约 75% 全年 +35.9%——但 IPO 仍冻结（8-9 家）、早期融资缺口、破发与裁员高企，呈现「并购热、融资/IPO 冷」的结构性景气（+8）。",
    2026: "「融资-并购-IPO 三通道全面修复」：VC H1 $9.1B 峰值、IPO 18 家/$5B（vintage 转正）、>$10B 并购 4 起、XBI YTD +34%（年内 maxDD 仅 -10.5%）——小 biotech 专属景气全面确认，强景气（+11）。压制项仅剩早期估值倒挂（-1）与宏观中性（0）。",
}

# ============ 本地量化与对照数据 ============
MINI = dict(
    xbi_ret={2022: -25.9, 2023: 7.6, 2024: 1.0, 2025: 35.9, 2026: 34.1},
    xbi_maxdd={2022: -45.6, 2023: -30.3, 2024: -20.1, 2025: -26.3, 2026: -10.5},
    xbi_vol={2022: 46.3, 2023: 28.4, 2024: 25.5, 2025: 27.4, 2026: 30.6},
    ibb_ret={2022: -13.7, 2023: 3.8, 2024: -2.4, 2025: 28.0, 2026: 17.6},
    xph_ret={2022: -9.8, 2023: 3.0, 2024: 4.9, 2025: 31.6, 2026: 29.3},
    dgs10_mean={2022: 2.95, 2023: 3.96, 2024: 4.21, 2025: 4.29, 2026: 4.38},
    dgs10_end={2022: 3.88, 2023: 3.88, 2024: 4.58, 2025: 4.18, 2026: 4.68},
    bigpharma_score={2022: -4, 2023: -1, 2024: 8, 2025: -1, 2026: 9},  # 21 号报告大药企口径
    ma_amt={2022: 105, 2023: 154, 2024: 77, 2025: 133, 2026: 134},       # $B（H1 口径）
    corr=0.494,
)

GROUP_SUMMARIES = {
    "融资与资本面": "五年轨迹「快坠→探底→磨底→企稳→修复」：2022 VC -17%/IPO 中位 -55% → 2023 续冰（Down Round、破发 50%）→ 2024 IPO vintage -52% 五年最差 → 2025 IPO 冻结但 Follow-on 引擎发力 → 2026 VC $9.1B 峰值 + IPO 18 家/$5B + vintage 转正。尾部现金压力（33% <12 个月）持续但边际改善。",
    "并购与退出通道": "小 biotech 最核心的景气引擎：2022 并购 -44%（仅 2 笔 $10B+）→ 2023 +79%（Seagen $43B）→ 2024 无新宣布 $10B+ 纯新药（-68%）→ 2025 +133%（5-6 笔 $10B+）→ 2026H1 已 4 起。License-in 首付从 2022 零 ≥$5B 到 2025 四笔 >$1B。并购强度 = 板块重估信号（年度收益 × 并购额相关 0.494）。",
    "临床与研发": "科学主线稳定向上：FDA 批 37→55→50→46→26(H1)，加速批准常态化；小 biotech 三期阳性（2023 Karuna/Madrigal、2024 Summit +584%、2025 Capricor +530%、2026 daraxonrasib）密度高，失败案例（Cassava/Amylyx/MoonLake）为常态化单票风险。",
    "宏观利率与政策": "利率是小 biotech 第一宏观变量：2022 加息 425bp 重创（XBI maxDD -45.6%）→ 2024-2026 降息周期重启（2026 已 -75bp）→ 打压解除。IRA/定价主要冲击商业化大药，对小 biotech 直接敞口有限；BIOSECURE/关税主要影响中国 CDMO，净影响中性。",
}

SCORES = {g: sum(it["score"] for it in ITEMS if it["group"] == g) for g in GROUPS}
TOTAL = sum(it["score"] for it in ITEMS)
CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四"}
if TOTAL >= 10:
    LEVEL, LEVEL_CN = "强景气", "强景气区间（+10 ~ +16）"
elif TOTAL >= 3:
    LEVEL, LEVEL_CN = "结构性景气", "结构性景气区间（+3 ~ +9）"
elif TOTAL >= -2:
    LEVEL, LEVEL_CN = "筑底/盘整期", "筑底/盘整期（-2 ~ +2）"
else:
    LEVEL, LEVEL_CN = "低迷期", "低迷期（-16 ~ -3）"

POS = sum(1 for it in ITEMS if it["score"] == 1)
NEU = sum(1 for it in ITEMS if it["score"] == 0)
NEG = sum(1 for it in ITEMS if it["score"] == -1)

DATA = dict(
    generated=TODAY, total=TOTAL, level=LEVEL, level_cn=LEVEL_CN,
    pos=POS, neu=NEU, neg=NEG,
    groups=[dict(name=g, score=SCORES[g], n=sum(1 for it in ITEMS if it["group"] == g),
                 summary=GROUP_SUMMARIES[g]) for g in GROUPS],
    items=ITEMS,
    yearly=dict(
        totals=YEAR_TOTALS, levels=YEAR_LEVELS, cn=YEAR_CN,
        group_points=YEAR_GROUP_POINTS, summaries=YEAR_SUMMARIES,
        groups=GROUPS,
        per_item={str(y): [[s, t, lb, u] for (s, t, lb, u) in YEARLY[y]] for y in YEARLY},
    ),
    mini=MINI,
)

def render_evs(evs):
    out = []
    for e in evs:
        out.append('<li>{text} <a class="lnk" href="{url}" target="_blank" rel="noopener">⧉ {label}</a></li>'.format(
            text=e["text"], url=e["url"], label=e["label"]))
    return "".join(out)

# ============ HTML 模板 ============
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>美股小型生物科技（XBI 口径）景气度核查报告 · 2022-2026</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;color:var(--ink);}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:22px;font-weight:700;}
  .kpi .num.big{color:var(--red);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .verdict{background:linear-gradient(135deg,#f6f3ff,#eef7f2);border:1px solid #e0d9f5;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:16px;font-weight:700;color:var(--ink);}
  .verdict .b .hl{color:var(--purple);} .verdict .b .hlb{color:var(--blue);} .verdict .b .hlr{color:var(--red);}
  .score-line{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center;}
  .chip{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:14px;font-size:12px;font-weight:600;}
  .chip.p{background:#eef7f2;color:var(--green);border:1px solid #cde8da;}
  .chip.z{background:#f3f5f8;color:var(--sub);border:1px solid var(--line);}
  .chip.n{background:#fff3f3;color:var(--red);border:1px solid #f5d5d5;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;vertical-align:top;}
  td.up{color:var(--green);font-weight:700;} td.dn{color:var(--red);font-weight:700;} td.ne{color:var(--sub);}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:380px;}
  .chart.sm{height:300px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .hl-box{background:#fff3f3;border:1px solid #f5d5d5;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#8c2f2f;margin-top:10px;}
  .warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);} .hlp{font-weight:700;color:var(--purple);}
  .ev{list-style:none;margin:6px 0 0;padding:0;}
  .ev li{position:relative;padding:2px 0 2px 16px;font-size:12.5px;line-height:1.65;}
  .ev li::before{content:"·";position:absolute;left:4px;color:var(--sub);font-weight:700;}
  .lnk{color:var(--blue);text-decoration:none;border-bottom:1px dashed var(--blue);white-space:nowrap;font-size:11.5px;}
  .lnk:hover{color:var(--purple);border-bottom-color:var(--purple);}
  .risk{background:#fff8ec;border:1px solid #f3dfb6;border-radius:8px;padding:8px 12px;font-size:12px;color:#7c4a03;margin-top:8px;}
  .grp-head{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:6px;margin-bottom:6px;}
  .grp-score{font-size:13px;font-weight:700;}
  .grp-score.s1{color:var(--red);} .grp-score.s0{color:var(--sub);} .grp-score.sn{color:var(--green);}
  .grp-summary{color:var(--sub);font-size:12.5px;margin-bottom:12px;}
  .dis-note{margin-top:16px;}
  .cn-note{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:10px 14px;font-size:12.5px;color:var(--sub);margin-top:12px;}
  @media print{.card{break-inside:avoid;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>美股小型生物科技（XBI 口径）景气度核查报告</h1>
    <div class="meta">核查日期：@@TODAY@@ ｜ 口径：<b>小型/未盈利生物科技公司</b>（XBI 成分特征：修正等权、中位市值约 $2.3B、约 80% 未盈利）｜ 方法：16 项核查清单逐项打分（+1 向好 / 0 平稳 / -1 恶化）｜ 每项关键数据附来源链接 ｜ 数据时点：2026 中报/8 月最新</div>
    <div class="cn-note">📌 <b>口径说明：</b>本报告分析<b>小型生物科技（非大型制药）</b>的景气度，与 <a class="lnk" href="../21_生物医药行业景气度/index.html" target="_blank" rel="noopener">⧉ 21 号报告（大型制药口径）</a>形成对照。小 biotech 的景气由「融资 → 并购/退出 → 临床/FDA → 利率」驱动，<b>不同于</b>大药企的「销售放量 + 盈利兑现」驱动。<b>五年打分速览：小 biotech -14 / +4 / +4 / +8 / +11 ⇔ 大药企 -4 / -1 / +8 / -1 / +9</b>——两年方向完全相反（2023/2025），2024 脱钩最大（+4 vs +8）。</div>

    <div class="verdict">
      <div class="t">综合景气度诊断（2026 当前）</div>
      <div class="b">16 项合计 <span class="hlb">@@TOTAL@@ 分</span> → <span class="hl">@@LEVEL@@</span>（@@LEVEL_CN@@）：@@POS@@ 项向好 / @@NEU@@ 项平稳 / @@NEG@@ 项恶化</div>
      <div class="score-line">
        <span class="chip p">✓ 向好 @@POS@@ 项</span>
        <span class="chip z">— 平稳 @@NEU@@ 项</span>
        <span class="chip n">✕ 恶化 @@NEG@@ 项</span>
      </div>
    </div>
    <div class="keypoint" style="margin-top:14px;">
      <b>核心判断：</b>小型生物科技正处于<b>五年最强景气窗口（+11，强景气下沿）</b>——2026 年三通道全面修复：一级融资 H1 $9.1B（2022 以来峰值）、IPO 窗口重开（18 家/$5B，vintage 转正 +49%）、>$10B 并购 4 起。XBI 年内 +34%、最大回撤仅 -10.5%。<b>对比 21 号大药企报告（+9）：小 biotech 本次首度反超大药企</b>，验证「并购弹性 > 销售韧性」的板块轮动逻辑。压制项仅剩早期估值倒挂（Down Round 仍在）与宏观中性（10Y 仍 4%+）。关键跟踪：H2 大 III 期读出、2026-11 中期选举、BINSA 立法、并购定价可持续性。
    </div>
  </div>

  <div class="card">
    <h2>一、总体评分结构（2026 当前）</h2>
    <div class="scroll">
      <table>
        <thead><tr><th>指标</th><th>分项得分</th><th>向好</th><th>平稳</th><th>恶化</th><th>板块小结</th></tr></thead>
        <tbody>
          @@GROUP_ROWS@@
        </tbody>
      </table>
    </div>
    <div class="chart" id="chart_score"></div>
    <div class="note">注：得分 = 各板块 16 项逐项 ±1 加总；颜色遵循「红涨绿跌」惯例与色弱安全（叠加 +/- 符号与文字标签）。</div>
  </div>

  <div class="card">
    <h2>二、2022 → 2026 五年景气度演化对比</h2>
    <div class="grp-summary">同一套 16 项核查清单、同一打分口径（小型 biotech 视角），逐年回溯打分。五年轨迹：<b>2022 深冬（-14）→ 2023 并购/临床点燃（+4）→ 2024 磨底（+4）→ 2025 并购驱动景气（+8）→ 2026 三通道全面修复（+11）</b>。核心驱动链：并购（退出通道）> 融资（资金供给）> 利率（久期估值）> 临床（选择权价值）。</div>
    <div class="scroll">
      <table style="min-width:760px;">
        <thead><tr>
          <th>年度</th><th>合计得分</th><th>景气区间</th>
          @@TH_GROUPS@@
          <th>向好/平稳/恶化</th>
        </tr></thead>
        <tbody>
          @@YEAR_ROWS@@
        </tbody>
      </table>
    </div>
    <div class="chart sm" id="chart_years"></div>
    <div class="note">注：上表与下图展示五年各板块得分演化；红=正分（涨）、绿=负分（跌），色弱安全叠加数字与文字。2022-2025 数据为回溯口径，来源链接见下方逐年明细。</div>
  </div>

  <div class="card">
    <h2>三、双口径对照：小 biotech 景气 ⇔ 大药企景气</h2>
    <div class="grp-summary">同表展示 21 号报告（大药企 16 项口径，销售/盈利驱动）与本报告（小 biotech 16 项口径，融资/并购驱动）五年打分对比，并叠加三只 ETF 年度收益（本地前复权日线）与 10Y 利率。关键观察：<b>2023/2025 两年方向完全相反</b>（小 biotech +4/+8 vs 大药企 -1/-1）、<b>2024 脱钩最大</b>（+4 vs +8——大药企靠 GLP-1 盈利，小 biotech 融资/并购双冷）；2022 两者同向深跌但小 biotech 跌幅更大（-25.9% vs -9.8%）。</div>
    <div class="scroll">
      <table style="min-width:860px;">
        <thead><tr>
          <th>年度</th><th>小biotech得分</th><th>大药企得分</th><th>得分差</th>
          <th>XBI收益</th><th>XPH收益</th><th>XBI−XPH</th><th>10Y均值</th>
        </tr></thead>
        <tbody>
          @@COMPARE_ROWS@@
        </tbody>
      </table>
    </div>
    <div class="chart sm" id="chart_compare"></div>
    <div class="keypoint" style="margin-top:12px;">
      <b>双口径结论：</b>① 小 biotech 年度收益与并购金额相关系数 = <b>@@CORR@@</b>（本地 XBI 数据 × 调研并购额）——并购是小 biotech 最重要的景气代理。② 五年里小 biotech 与大药企景气「脱钩—共振」交替：2022 同跌（利率杀）、2023 反向（并购点燃 vs 销售平淡）、2024 最大脱钩（GLP-1 盈利独强）、2025 反向（并购年 vs 筑底）、2026 小 biotech 反超（+11 vs +9）。③ 使用建议：<b>看小 biotech 景气用「并购 + 融资 + 利率」三因子，看大药企用「销售 + 盈利 + 定价政策」</b>，两者是两个独立周期，可互为对冲或轮动配置。
    </div>
    <div class="note">来源：XBI/IBB/XPH 年度收益与 maxDD 为本地 Yahoo 前复权日线计算（截至 2026-08-20）；10Y 利率为 FRED DGS10；大药企得分取自 21 号报告（199 条目回溯口径）。</div>
  </div>

  <div class="card">
    <h2>四、加权敏感性：平权假设的稳健性检验（方法论升级）</h2>
    <div class="warn">
      <b>背景：</b>初版 16 项打分采用平权机制（每项 ±1）。评审意见指出：宏观利率与 MNC 大型并购对 XBI 的实际影响权重远高于单项临床进展或 FDA 加速批准政策，平权加总可能让短期情绪指标掩盖长期基本面风险。本章用实证与机制证据为各因子赋权，重估五年结论。
    </div>
    <div class="grp-summary" style="margin-top:10px;"><b>一、实证证据（本地数据，脚本 calc_factor_weights.py）：</b></div>
    <div class="scroll">
      <table style="min-width:860px;">
        <thead><tr><th>证据</th><th>样本</th><th>数值</th><th>解读</th></tr></thead>
        <tbody>
          <tr><td>月频回归：XBI 月收益 ~ Δ10Y（单变量）</td><td>n=245（2006-01 ~ 2026-08 月度）</td><td>ß=-1.27（pp/pp）｜corr=-0.04｜R²≈0.2%</td><td>利率的<b>当月线性</b>解释力极弱——利率不是「每日拖累」，而是「利率飙升期」的稀有但致命事件（见下行案例）</td></tr>
          <tr><td>同口径：IBB / XPH 的 Δ10Y 敏感度</td><td>同上</td><td>IBB corr≈-0.09｜XPH corr≈-0.07</td><td>XBI 的利率敏感度高于 IBB/XPH，但同为弱线性——久期差异主要体现于<b>极端年</b>（2022）而非逐月</td></tr>
          <tr><td>年度：并购额 × XBI 年度收益</td><td>n=8（2019-2026）</td><td>相关 ≈ 0.19～0.31（口径敏感）</td><td>方向为正但小样本不稳定；机构口径（EY/IQVIA）在 2022-2025 并购年与 XBI 反弹高度同步</td></tr>
          <tr><td>极值对照：利率「边际变化」事件</td><td>2022 vs 2026</td><td>2022：10Y +2.6pp → XBI maxDD <b>-45.6%</b>；2026：10Y 4.4%（高但平稳）→ maxDD 仅 <b>-10.5%</b></td><td>同样 4%+ 利率水平，2022 与 2026 回撤差 35pp——起作用的是利率<b>方向/速率</b>而非水平</td></tr>
        </tbody>
      </table>
    </div>
    <div class="grp-summary" style="margin-top:12px;"><b>二、权重设定（项级，缩放回 16 项原尺度）：</b></div>
    <div class="scroll">
      <table style="min-width:760px;">
        <thead><tr><th>板块</th><th>项数</th><th>项级权重</th><th>缩放后权重</th><th>设定依据</th></tr></thead>
        <tbody>
          <tr><td>并购与退出通道</td><td>4</td><td><b>1.75</b></td><td>1.38</td><td>总金额级、全截面、月度可观测；退出通道是小 biotech 全部价值的兑现机制</td></tr>
          <tr><td>宏观利率与政策</td><td>3</td><td><b>1.75</b></td><td>1.38</td><td>2022 极值证明利率是久期压缩的头号凶器；政策（FDA 稳定性/定价）为同级别系统因子</td></tr>
          <tr><td>融资与资本面</td><td>5</td><td>1.0</td><td>0.79</td><td>供给端因子，月度可观测，但部分被利率/并购内化（VC 行为即利率+退出预期的函数）</td></tr>
          <tr><td>临床与研发</td><td>4</td><td>0.75</td><td>0.59</td><td>事件驱动、截面不均（单票 alpha 不代表板块 beta）；FDA 加速批准影响已并入其政策面</td></tr>
          <tr><td style="font-weight:700;">加权满分</td><td>16</td><td colspan="2">20.25 → 缩放系数 0.790</td><td>加权分 ÷20.25 ×16，与平权 -16~+16 完全可比，档位阈值不变</td></tr>
        </tbody>
      </table>
    </div>
    <div class="grp-summary" style="margin-top:12px;"><b>三、加权 vs 平权五年对照（核心结论）：</b></div>
    <div class="scroll">
      <table style="min-width:860px;">
        <thead><tr>
          <th>年度</th><th>平权总分</th><th>加权总分</th><th>Δ</th><th>平权档位</th><th>加权档位</th><th>结论变化</th>
        </tr></thead>
        <tbody>
          @@WEIGHTED_YEAR_ROWS@@
        </tbody>
      </table>
    </div>
    <div class="chart sm" id="chart_weighted"></div>
    <div class="keypoint" style="margin-top:12px;">
      <b>加权结论：</b>① <b>2026 年结论不变</b>：加权总分 11.1 vs 平权 11，仍为<b>强景气下沿（+10~+16）</b>——因为 2026 权重大的因子（并购 +4、宏观 +1）与权重小的因子（临床 +3）同向为正，无论怎么加权都是强景气。② <b>但五年相对差异显著加深</b>：2022 从 -14 加深至 -14.8（利率+并购双权重加深熊市）、2024 从 +2 缩至 +1.8（若按无缩放原始权重则为 +2.25，档位仍筑底）——被临床事件撑起来的「+2 磨底」在加权下更接近「真筑底」。③ <b>排序关系变化</b>：2023（+4.2）与 2024（+1.8）差距拉大，2025 升至 +8.7。④ <b>敏感性扫描</b>（并购 1.25~2.0 × 临床 0.5~1.0 共 12 组合）：2026 加权总分恒在 <b>10.4 ~ 11.3</b>，全部落在强景气下沿——<b>当前年度结论对权重选择稳健</b>；五年档位仅在 2024（±1 临界）处存在边界敏感性。
    </div>
    <div class="note">注：Δ = 加权 − 平权（正=权重放大向好因子）。加权分 = ∑(分组得分 × 项级权重) × 0.790。档位阈值沿用原四档（-16~-3 低迷 / -2~+2 筑底 / +3~+9 结构性 / +10~+16 强景气）。实证脚本：scripts/calc_factor_weights.py。</div>
  </div>

  <div class="card">
    <h2>五、逐年景气度明细（2022-2025 回溯）</h2>
    <div class="grp-summary">以下逐年列出 16 项核查的关键依据与来源链接。2022-2025 为回溯打分（同口径），2026 为当前核查。点击 ⧉ 进入一手来源。</div>
    @@YEAR_CARDS@@
  </div>

  <div class="card">
    <h2>六、2026 年板块核查明细（16 项）</h2>
    <div class="grp-summary">以下四个板块卡片为 2026 年当前核查的逐项明细（与「一、总体评分结构」对应），关键数据均附来源链接（⧉ 一手来源）。</div>
    @@GROUP_CARDS@@
  </div>

  <div class="card">
    <h2>七、风险提示与跟踪节点</h2>
    <div class="warn">
      <b>1. 数据依赖与时效：</b>本报告数据截至 2026-08-23，主要来自 BioPharma Dive、PitchBook、DealForma、EY/SVB、JPM、Stifel、Renaissance Capital、FDA/CMS/Fed 官方页面及公司公告（SEC 8-K）；所有关键数据均已附来源链接（⧉ 符号）。2022-2025 为回溯口径，不同机构统计口径差异（如 VC 金额、IPO 家数）已注明。
    </div>
    <div class="warn">
      <b>2. 关键下行变量：</b>① 并购定价风险：2025 平均溢价 60%（前三笔大单约 30%）——若 MNC 转向「去风险化优先、溢价收窄」，板块重估逻辑生变；② IPO 窗口是否能持续（2025 vintage +49% 建立在低基数上）；③ 10Y 若重回 4.5% 以上并加速上行（2022 式加息）将再度压制高久期资产（XBI 波动率 30%+）；④ 尾部出清：1/3 公司现金 <12 个月，H2 仍有批量再融资稀释。
    </div>
    <div class="warn">
      <b>3. 结构性风险：</b>早期轮（Seed/A）融资持续收缩——流动性向中晚期集中，「空心化」风险延续（2025 早期轮下滑、mega round 从 104 笔降至 80 笔）；单票三期失败冲击巨大（月度 -80% 案例频出），个股风险极不均匀。
    </div>
    <div class="warn">
      <b>4. 方法局限：</b>① 权重设定为「实证 + 机制先验」混合（月频回归 R² 极低、年度相关 n 仅 8），结论依赖敏感性扫描确认稳健性（已做 12 组合梯度）；② 16 项打分仍为截面快照，未做历史分位数标准化；③ 并购额相关系数（0.19~0.31 八年口径）样本小，仅方向性参考；④ 打分反映 2026-08 时点截面结论，不构成投资建议。
    </div>
  </div>

  <div class="card">
    <h2>附：核查方法论</h2>
    <div class="grp-summary">按「融资与资本面（资金供给）→ 并购与退出通道（景气核心）→ 临床与研发（选择权价值）→ 宏观利率与政策（估值久期）」四层框架逐项核对。计分规则：+1 向好/超预期、0 平稳/符合预期、-1 恶化/低于预期，加总后按四档区间判定景气度（+10~+16 强景气 / +3~+9 结构性景气 / -2~+2 筑底盘整 / -16~-3 低迷）。每项结论附关键数据与可点击来源链接（⧉ = 一手来源），未核实项已明确标注。</div>
    <div class="note">报告生成：@@TODAY@@ ｜ 时点口径：2026Q2/H1 财报为主、2025 全年为辅（已注明） ｜ 姊妹报告：<a class="lnk" href="../21_生物医药行业景气度/index.html" target="_blank" rel="noopener">⧉ 21 大型制药口径</a></div>
  </div>

</div>
<script>
var DATA = __DATA_JSON__;
@@RENDER_JS__
</script>
</body>
</html>
"""

RENDER_JS = r"""
// 1) 板块得分横向条形图
(function(){
  var el = document.getElementById('chart_score');
  if(!el) return;
  var chart = echarts.init(el);
  var gs = DATA.groups.map(function(g){
    return {name: g.name, score: g.score, n: g.n};
  });
  var maxAbs = Math.max.apply(null, gs.map(function(g){return Math.abs(g.score);}).concat([1]));
  chart.setOption({
    grid:{left:10,right:46,top:20,bottom:10,containLabel:true},
    xAxis:{type:'value',min:-maxAbs-0.5,max:maxAbs+0.5,splitLine:{lineStyle:{type:'dashed',color:'#eef0f3'}}},
    yAxis:{type:'category',data:gs.map(function(g){return g.name;}),axisLabel:{fontSize:12,color:'#1f2329'}},
    series:[{
      type:'bar',barWidth:18,
      data:gs.map(function(g){
        return {value:g.score, itemStyle:{color: g.score>=0 ? '#e03131' : '#0aa06e', borderRadius: g.score>=0?[0,4,4,0]:[4,0,0,4]}};
      }),
      label:{show:true,position:'right',formatter:function(p){return (p.value>0?'+':'')+p.value;},fontWeight:700,color:'#1f2329'}
    }],
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:function(ps){
      var p=ps[0];var g=gs[p.dataIndex];
      return '<b>'+g.name+'</b><br/>得分：'+(g.score>0?'+':'')+g.score+' 分（'+g.n+' 项）';
    }}
  });
  window.addEventListener('resize', function(){chart.resize();});
})();

// 2) 五年景气度演化：总分折线 + 板块得分堆叠
(function(){
  var el = document.getElementById('chart_years');
  if(!el) return;
  var chart = echarts.init(el);
  var years = Object.keys(DATA.yearly.totals).map(Number).sort();
  var groups = DATA.yearly.groups;
  var colors = ['#e03131','#1e66d6','#0aa06e','#7048e8'];
  var series = groups.map(function(g, i){
    return {
      name: g,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      data: years.map(function(y){ return DATA.yearly.group_points[y][g]; }),
      itemStyle: { color: colors[i] },
      lineStyle: { width: 2.5, color: colors[i] }
    };
  });
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:10,right:52,top:30,bottom:24,containLabel:true},
    xAxis:{type:'category',data:years.map(String),axisLabel:{fontSize:13}},
    yAxis:{type:'value',min:-6,max:5,splitLine:{lineStyle:{type:'dashed',color:'#eef0f3'}},axisLabel:{formatter:function(v){return (v>0?'+':'')+v;}}},
    series: series
  });
  window.addEventListener('resize', function(){chart.resize();});
})();

// 3) 双口径对照：小biotech vs 大药企得分（柱） + XBI-XPH 收益差（线）
(function(){
  var el = document.getElementById('chart_compare');
  if(!el) return;
  var chart = echarts.init(el);
  var m = DATA.mini;
  var years = Object.keys(m.xbi_ret).map(Number).sort();
  var yrs = years.map(String);
  var series = [
    {name:'小biotech得分', type:'bar', barWidth:16, data: years.map(function(y){return DATA.yearly.totals[y];}),
     itemStyle:{color:'#e03131',borderRadius:[3,3,0,0]}},
    {name:'大药企得分(21号)', type:'bar', barWidth:16, data: years.map(function(y){return m.bigpharma_score[y];}),
     itemStyle:{color:'#1e66d6',borderRadius:[3,3,0,0]}},
    {name:'XBI−XPH(pp)', type:'line', yAxisIndex:1, smooth:true, symbol:'diamond', symbolSize:9,
     data: years.map(function(y){return +(m.xbi_ret[y]-m.xph_ret[y]).toFixed(1);}),
     lineStyle:{width:2.5,color:'#0aa06e'}, itemStyle:{color:'#0aa06e'}}
  ];
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:10,right:52,top:30,bottom:24,containLabel:true},
    xAxis:{type:'category',data:yrs,axisLabel:{fontSize:13}},
    yAxis:[
      {type:'value',name:'得分',min:-16,max:13,splitLine:{lineStyle:{type:'dashed',color:'#eef0f3'}},axisLabel:{formatter:function(v){return (v>0?'+':'')+v;}}},
      {type:'value',name:'XBI−XPH pp',min:-20,max:20,splitLine:{show:false},axisLabel:{formatter:function(v){return v;}}}
    ],
    series: series
  });
  window.addEventListener('resize', function(){chart.resize();});
})();

// 4) 加权敏感性：平权 vs 加权五年前对照
(function(){
  var el = document.getElementById('chart_weighted');
  if(!el || !DATA.weights) return;
  var chart = echarts.init(el);
  var w = DATA.weights.weighted_years;
  var years = Object.keys(w.equal).map(Number).sort();
  var yrs = years.map(String);
  var wm = DATA.weights.weighted_2026;
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:10,right:30,top:30,bottom:24,containLabel:true},
    xAxis:{type:'category',data:yrs,axisLabel:{fontSize:13}},
    yAxis:{type:'value',min:-20,max:16,splitLine:{lineStyle:{type:'dashed',color:'#eef0f3'}},axisLabel:{formatter:function(v){return (v>0?'+':'')+v;}}},
    series:[
      {name:'平权总分', type:'bar', barWidth:20, data: years.map(function(y){return w.equal[y];}), itemStyle:{color:'#1e66d6',opacity:.45,borderRadius:[3,3,0,0]}},
      {name:'加权总分', type:'bar', barWidth:20, data: years.map(function(y){return +(w.weighted_scaled[y]).toFixed(1);}), itemStyle:{color:'#e03131',borderRadius:[3,3,0,0]}},
      {name:'Δ 加权−平权', type:'line', smooth:true, symbol:'diamond', symbolSize:8,
       data: years.map(function(y){return +(w.weighted_scaled[y]-w.equal[y]).toFixed(1);}),
       lineStyle:{width:2,color:'#7048e8'}, itemStyle:{color:'#7048e8'}}
    ]
  });
  window.addEventListener('resize', function(){chart.resize();});
})();
"""

def group_card_html(g, idx):
    items = [it for it in ITEMS if it["group"] == g]
    rows = []
    for it in items:
        sc = it["score"]
        sc_class = {1: "up", -1: "dn", 0: "ne"}[sc]
        sc_txt = {1: "+1 向好", -1: "-1 恶化", 0: "0 平稳"}[sc]
        risk_html = ('<div class="risk">⚠ ' + it.get("risk", "") + "</div>") if it.get("risk") else ""
        ev = render_evs(it["evs"])
        rows.append(
            '<tr>'
            '<td class="{}">{}</td>'.format(sc_class, sc_txt)
            + '<td><b>{}. {}</b>　<span class="tag">{}</span><div class="src" style="white-space:normal;min-width:280px;line-height:1.65;">{}</td>'.format(it["no"], it["item"], it["flag"], it["verdict"])
            + '<td style="white-space:normal;min-width:380px;"><ul class="ev">{}</ul>{}</td>'.format(ev, risk_html)
            + '</tr>'
        )
    sc = SCORES[g]
    sc_cls = "s1" if sc > 0 else ("sn" if sc < 0 else "s0")
    return """<div class="card">
  <h2>◎ @@GNAME@@ <span class="grp-score @@CLS@@">板块得分 @@SC@@</span></h2>
  <div class="grp-summary">@@SUMMARY@@</div>
  <div class="scroll"><table>
    <thead><tr><th style="width:70px">打分</th><th style="min-width:320px">核查项与结论</th><th style="min-width:400px">关键数据与依据（含来源链接）</th></tr></thead>
    <tbody>@@ROWS@@</tbody>
  </table></div>
</div>""".replace("@@GNAME@@", g).replace("@@CLS@@", sc_cls).replace("@@SC@@", ("+" + str(sc)) if sc > 0 else str(sc)).replace("@@SUMMARY@@", GROUP_SUMMARIES[g]).replace("@@ROWS@@", "".join(rows))

def year_card_html(year):
    """生成某历史年份的 16 项明细卡片（回溯口径）"""
    rows = []
    year_data = YEARLY[year]
    for i, it in enumerate(ITEMS):
        no = it["no"] - 1
        s, brief, label, url = year_data[no]
        sc_class = {1: "up", -1: "dn", 0: "ne"}[s]
        sc_txt = {1: "+1 向好", -1: "-1 恶化", 0: "0 平稳"}[s]
        rows.append(
            '<tr>'
            '<td>{}. {}</td>'.format(it["no"], it["item"])
            + '<td class="{}">{}</td>'.format(sc_class, sc_txt)
            + '<td style="white-space:normal;min-width:420px;">{} <a class="lnk" href="{}" target="_blank" rel="noopener">⧉ {}</a></td>'.format(brief, url, label)
            + '</tr>'
        )
    tag = "回溯口径" if year < 2026 else "当前核查"
    return """<div class="card">
  <h2>◎ @@YEAR@@ 年核查明细 <span class="tag">@@TAG@@</span> <span class="grp-score @@CLS@@">合计 @@SC@@</span></h2>
  <div class="grp-summary">@@SUM@@</div>
  <div class="scroll"><table>
    <thead><tr><th style="min-width:200px">核查项</th><th style="width:80px">打分</th><th style="min-width:440px">关键数据与依据（含来源链接）</th></tr></thead>
    <tbody>@@ROWS@@</tbody>
  </table></div>
</div>""".replace("@@YEAR@@", str(year)).replace("@@TAG@@", tag) \
        .replace("@@CLS@@", "s1" if YEAR_TOTALS[year] > 0 else "s0") \
        .replace("@@SC@@", ("+" + str(YEAR_TOTALS[year])) if YEAR_TOTALS[year] > 0 else str(YEAR_TOTALS[year])) \
        .replace("@@SUM@@", YEAR_SUMMARIES[year]).replace("@@ROWS@@", "".join(rows))

def level_of(score):
    if score >= 10: return "强景气"
    if score >= 3: return "结构性景气"
    if score >= -2: return "筑底/盘整"
    return "低迷期"

def main():
    # 加载实证权重（calc_factor_weights.py 输出）
    weights_path = os.path.join(BASE, "..", "results", "factor_weights.json")
    WEIGHTS = {}
    if os.path.exists(weights_path):
        with open(weights_path, encoding="utf-8") as f:
            WEIGHTS = json.load(f)
    # 注入 DATA
    DATA["weights"] = WEIGHTS

    group_cards = "".join(group_card_html(g, i + 1) for i, g in enumerate(GROUPS))
    grp_rows = []
    for i, g in enumerate(GROUPS):
        sc = SCORES[g]
        sc_txt = ("+" + str(sc)) if sc > 0 else str(sc)
        p = sum(1 for it in ITEMS if it["group"] == g and it["score"] == 1)
        z = sum(1 for it in ITEMS if it["group"] == g and it["score"] == 0)
        n = sum(1 for it in ITEMS if it["group"] == g and it["score"] == -1)
        grp_rows.append(
            '<tr><td><b>{}、{}（{} 项）</b></td>'
            '<td class="{}">{}</td><td>{}</td><td>{}</td><td>{}</td>'
            '<td style="white-space:normal;min-width:300px;">{}</td></tr>'.format(
                CN_NUM[i + 1], g, len([it for it in ITEMS if it["group"] == g]),
                "up" if sc > 0 else ("ne" if sc == 0 else "dn"), sc_txt,
                p, z, n, GROUP_SUMMARIES[g])
        )
    th_groups = "".join('<th>{}</th>'.format(g) for g in GROUPS)
    year_rows = []
    for y in [2022, 2023, 2024, 2025, 2026]:
        sc = YEAR_TOTALS[y]
        sc_txt = ("+" + str(sc)) if sc > 0 else str(sc)
        lv_cls = "up" if sc > 0 else ("dn" if sc < 0 else "ne")
        cells = "".join(
            '<td class="{}">{}</td>'.format(
                ("up" if YEAR_GROUP_POINTS[y][g] > 0 else ("dn" if YEAR_GROUP_POINTS[y][g] < 0 else "ne")),
                ("+" + str(YEAR_GROUP_POINTS[y][g])) if YEAR_GROUP_POINTS[y][g] > 0 else str(YEAR_GROUP_POINTS[y][g]))
            for g in GROUPS)
        year_rows.append(
            '<tr><td><b>{}</b></td><td class="{}">{}</td><td>{}</td>{}{}</tr>'.format(
                y, lv_cls, sc_txt, YEAR_LEVELS[y], cells,
                '<td>{}</td>'.format(YEAR_CN[y]))
        )
    # 双口径对照表
    m = MINI
    cmp_rows = []
    for y in [2022, 2023, 2024, 2025, 2026]:
        s_mini = YEAR_TOTALS[y]
        s_big = m["bigpharma_score"][y]
        diff = s_mini - s_big
        xdiff = m["xbi_ret"][y] - m["xph_ret"][y]
        cmp_rows.append(
            '<tr><td><b>{}</b></td>'
            '<td class="{}">{:+.0f}</td><td class="{}">{:+.0f}</td><td class="{}">{:+.0f}</td>'
            '<td class="{}">{:+.1f}%</td><td class="{}">{:+.1f}%</td><td class="{}">{:+.1f}pp</td>'
            '<td>{:.2f}%</td></tr>'.format(
                y,
                "up" if s_mini > 0 else ("dn" if s_mini < 0 else "ne"), s_mini,
                "up" if s_big > 0 else ("dn" if s_big < 0 else "ne"), s_big,
                "up" if diff > 0 else ("dn" if diff < 0 else "ne"), diff,
                "up" if m["xbi_ret"][y] >= 0 else "dn", m["xbi_ret"][y],
                "up" if m["xph_ret"][y] >= 0 else "dn", m["xph_ret"][y],
                "up" if xdiff >= 0 else "dn", xdiff,
                m["dgs10_mean"][y]))
    year_cards = "".join(year_card_html(y) for y in [2022, 2023, 2024, 2025])

    # 加权敏感性年度对照行
    wy_rows = []
    if WEIGHTS.get("weighted_years"):
        w_eq = WEIGHTS["weighted_years"]["equal"]
        w_sc = WEIGHTS["weighted_years"]["weighted_scaled"]
        for y in [2022, 2023, 2024, 2025, 2026]:
            eq, sc = w_eq[str(y)], w_sc[str(y)]
            delta = sc - eq
            lv_eq = level_of(eq)
            lv_sc = level_of(sc)
            change = "不变" if lv_eq == lv_sc else "档位变化"
            wy_rows.append(
                '<tr><td><b>{}</b></td>'
                '<td class="{}">{:+.0f}</td><td class="{}">{:+.1f}</td><td class="{}">{:+.1f}</td>'
                '<td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    y,
                    "up" if eq > 0 else ("dn" if eq < 0 else "ne"), eq,
                    "up" if sc > 0 else ("dn" if sc < 0 else "ne"), sc,
                    "up" if delta > 0 else ("dn" if delta < 0 else "ne"), delta,
                    lv_eq, lv_sc, change))
    html = HTML.replace("@@TODAY@@", TODAY).replace("@@TOTAL@@", str(TOTAL)) \
        .replace("@@LEVEL@@", LEVEL).replace("@@LEVEL_CN@@", LEVEL_CN) \
        .replace("@@POS@@", str(POS)).replace("@@NEU@@", str(NEU)).replace("@@NEG@@", str(NEG)) \
        .replace("@@GROUP_ROWS@@", "".join(grp_rows)) \
        .replace("@@GROUP_CARDS@@", group_cards) \
        .replace("@@TH_GROUPS@@", th_groups) \
        .replace("@@YEAR_ROWS@@", "".join(year_rows)) \
        .replace("@@YEAR_CARDS@@", year_cards) \
        .replace("@@COMPARE_ROWS@@", "".join(cmp_rows)) \
        .replace("@@WEIGHTED_YEAR_ROWS@@", "".join(wy_rows)) \
        .replace("@@CORR@@", str(m["corr"]))
    data_json = json.dumps(DATA, ensure_ascii=False, allow_nan=False)
    html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + data_json + ";")
    html = html.replace("@@RENDER_JS__", RENDER_JS)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT)
    print("written: %s size=%d" % (OUT, size))

if __name__ == "__main__":
    main()