# -*- coding: utf-8 -*-
"""生物医药行业景气度核查报告构建脚本（美股非中国公司视角）
输出: reports/21_生物医药行业景气度/index.html
用法: python build_biopharma_prosperity.py
"""
import json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "21_生物医药行业景气度")
OUT = os.path.join(OUT_DIR, "index.html")
os.makedirs(OUT_DIR, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# ============ 16 项打分数据（美股非中国公司视角）============
# 每项: no, item, group, score(+1/0/-1), verdict, evs=[(text, label, url), ...], risk(可选)
def L(text, label, url):
    return dict(text=text, label=label, url=url)

ITEMS = [
    # ---- 板块一 资金与资本面 ----
    dict(no=1, group="资金与资本面", item="一级市场投融资总量与频次", score=1, flag="向好",
         verdict="强劲复苏但\"选择性繁荣\"：2026H1 美国有风投背景的生物科技公司融资约 $9.1B（BioPharma Dive），为 2022 年以来同期最高，76% 来自 ≥$1 亿 Megaround；2025 全年 PitchBook 口径 $33.8B/1,171 笔。",
         evs=[
             L("2026H1 至少 68 家有风投背景公司融资 $9.1B，为 2022 年以来同期峰值", "BioPharma Dive", "https://www.biopharmadive.com/trendline/emerging-biotech-startup-venture-capital-ipo/260/"),
             L("76% 来自 ≥$1 亿 Megaround；单笔最大 Isomorphic Labs $2.1B（AI 制药）", "BioPharma Dive", "https://www.biopharmadive.com/trendline/emerging-biotech-startup-venture-capital-ipo/260/"),
             L("2025 全年美国 VC 融资 $33.8B / 1,171 笔（2024：$31.9B / 1,091）", "BioSpace/PitchBook", "https://www.biospace.com/business/early-stage-biotechs-suffer-in-2025-as-vc-shuns-risk-pitchbook"),
             L("SVB 口径：2025 美国+欧洲医疗健康 VC 合计 $46.8B，同比下滑", "SVB H1 2026 报告解读", "https://www.linkedin.com/posts/davidhcrean_svb-h1-2026-healthcare-ugcPost-7432195688668622848-y5MZ"),
         ]),
    dict(no=2, group="资金与资本面", item="融资金额与估值健康度", score=0, flag="平稳",
         verdict="估值倒挂仍普遍但出现分层修复：2025 年一批明星 Biotech 经历 Down Round（Umoja -36%、Eikon 腰斩、Arbor 缩水），但 2026 年 Kailera、Parabilis 以历史级 IPO 定价回收，估值体系处\"底部确认\"阶段。",
         evs=[
             L("Umoja Biopharma C 轮 $1 亿、投后 $4.2 亿（2021 年 $6.6 亿，-36%）", "PitchBook/摩熵医药", "http://cdn.pharnexcloud.com/zixun/sd_43237"),
             L("Eikon Therapeutics D 轮 $3.51 亿：估值 $36.4 亿 → $18.5 亿（腰斩）；Arbor $5.75 亿 → $2.39 亿", "PitchBook/摩熵医药", "http://cdn.pharnexcloud.com/zixun/sd_43237"),
             L("Parabilis Medicines 2026-01 F 轮降价融资 $3.052 亿（每股 $6.1644 < E 轮 $6.2281，触发反稀释）", "新浪财经招股书分析", "https://finance.sina.com.cn/cj/2026-06-12/doc-iniceptf3329684.shtml"),
             L("修复信号：Kailera B 轮 $600M 后 4 月 IPO 募 $625M；Parabilis IPO 定价 $20/股历史级回收", "新浪财经招股书分析", "https://finance.sina.com.cn/cj/2026-06-12/doc-iniceptf3329684.shtml"),
         ]),
    dict(no=3, group="资金与资本面", item="二级市场 IPO 与再融资通道", score=1, flag="向好",
         verdict="窗口重开年：2026 年前 7 个月至少 18 家生物科技 IPO、募资 $5B+（对比 2025 全年 8 家/$1.7B），Follow-on 78 笔/$20B、PIPE 83 笔/$6.1B，双通道资本侧翼充足。",
         evs=[
             L("2026 截至目前 18 家 IPO / 募资 $5B+；2025 全年 8 家 / 约 $1.7B", "DealForma Q2 2026 复盘", "https://dealforma.com/biopharma-therapeutics-and-platforms-ipo-activity-follow-ons-and-pipes-q2-2026-review/"),
             L("Parabilis 6 月 IPO 募 $7.7 亿（超规格定价）；Kailera 4 月 $7.19 亿，均超 Moderna 2018 年纪录", "Parabilis 官方定价稿", "https://investors.parabilismed.com/news-releases/news-release-details/parabilis-medicines-announces-pricing-upsized-initial-public"),
             L("H1 13 家 IPO 募约 $4.5B，中位募资约 $3 亿", "BioTech Today IPO 复盘", "https://biotech-today.com/biotech-ipos-surge-in-h1-2026-shattering-records-and-doubling-last-years-total/"),
             L("再融资：上半年 Follow-on 78 笔 / $20B、PIPE 83 笔 / $6.1B", "DealForma Q2 2026 复盘", "https://dealforma.com/biopharma-therapeutics-and-platforms-ipo-activity-follow-ons-and-pipes-q2-2026-review/"),
         ]),
    dict(no=4, group="资金与资本面", item="跨境 BD / 并购活跃度", score=1, flag="向好",
         verdict="MNC 买管线进入\"抢购模式\"：2026 上半年至少 4 起 >$10B 并购（GSK-Nuvalent、AbbVie-Apogee、Vertex-Crinetics、Gilead-Arcellx），>20 亿美元 license-in 由全球创新（含中国资产）主导；并购退出通畅直接抬升板块中枢。",
         evs=[
             L("GSK-Nuvalent $10.6B（6 月）；AbbVie-Apogee $10.9B（$135.11/股）；Vertex-Crinetics 约 $10B（$85/股）", "xTalks 2026 并购看板", "https://xtalks.com/pharma-and-biotech-mas-2026-deal-watcher-4629/"),
             L("Gilead-Arcellx $7.8B（4 月完成）；Gilead-Tubulis $5B；Biogen-Apellis $5.6B", "Gilead 官方新闻稿", "https://www.gilead.com/news/news-details/2026/gilead-sciences-completes-acquisition-of-arcellx-ahead-of-potential-commercial-launch-of-anito-cel"),
             L("AbbVie-Apogee $10.9B 官方确认", "AbbVie 投资者官网", "https://investors.abbvie.com/node/21441/html"),
             L("上半年 38-41 起并购、近 2/3 ≥$1B；license-in 含中国资产大额交易（BD 全球热度）", "LifeScienceDaily $1B 清单", "https://lifesciencedaily.news/biotech-ma-2026-every-1b-deal-so-far-and-what-is-driving-them/"),
         ]),
    dict(no=5, group="资金与资本面", item="企业现金流安全线", score=0, flag="平稳",
         verdict="行业资产负债表仍未完全出清：2025 年末仅 45% 非商业化成熟公司现金可支撑 >24 个月、33% 不足 12 个月；但 2026 年再融资窗口（H1 Follow-on+PIPE 约 $26B）实质缓解了中腰部公司压力。",
         evs=[
             L("EY：约 45% 公司现金可支撑 >24 个月、33% 不足 12 个月（2025 年末）", "EY Biotech Beyond Borders 2026", "https://www.ey.com/content/dam/ey-unified-site/ey-com/en-gl/campaigns/life-sciences-securing-value-data-driven-platforms/documents/ey-gl-beyond-borders-biotech-report-06-2026.pdf"),
             L("公开 Biotech 数量连续 4 年下降：2025 年末 758 家 vs 2021 年 977 家", "EY Biotech Beyond Borders 2026", "https://www.ey.com/content/dam/ey-unified-site/ey-com/en-gl/campaigns/life-sciences-securing-value-data-driven-platforms/documents/ey-gl-beyond-borders-biotech-report-06-2026.pdf"),
             L("2026 上半年 Follow-on + PIPE 合计约 $26B，缓解现金压力", "BDO 2026 生物技术简报", "https://pharmasource.global/content/expert-insight/3-things-biotechs-need-before-going-public-in-2026"),
         ]),
    # ---- 板块二 研发与研发服务 ----
    dict(no=6, group="研发与研发服务", item="IND/NDA 申报与获批数量", score=1, flag="向好",
         verdict="FDA 审批节奏稳健爬坡：2026H1 批准 26 款新药（2025H1 为 19 款），截至 8 月已批 30 款，按节奏 2026 全年或达 55-60 款，站上\"批准 >45 款\"常态化区间；全球首创药频出（口服 GLP-1、口服激素降解剂等）。",
         evs=[
             L("FDA 2026 已批 30 款新药（截至 8 月）；H1 26 款 vs 2025H1 19 款", "FDA Novel Drug Approvals 2026", "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2026"),
             L("2025 全年批准 46 款（NME 34 + BLA 12），2024 约 50 款", "FDA Novel Drug Approvals 2025", "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2025"),
             L("获批代表作：礼来口服 GLP-1 Foundayo（orforglipron，4/1，全球首个非肽 GLP-1）", "FDA Notable Approvals", "https://www.fda.gov/drugs/news-events-human-drugs/notable-approvals-drugs"),
             L("H1 审批维持稳定（肿瘤/罕见病主导）", "BioSpace H1 2026 审批复盘", "https://www.biospace.com/fda/despite-chaos-and-churn-fda-decisions-hold-mostly-steady-in-h1-2026"),
         ]),
    dict(no=7, group="研发与研发服务", item="后期临床管线占比与成果", score=1, flag="向好",
         verdict="重磅读出含金量高、失败个案可控：礼来 ACHIEVE-4（口服 GLP-1 心血管获益）、Revolution Medicines 泛 RAS 抑制剂（胰腺癌 mOS 13.2 vs 6.7 月、HR 0.40）为年度标志性阳性；诺和神衰 EVOKE、AZ Wainua 失败形成局部扰动，未动摇主线。",
         evs=[
             L("礼来 ACHIEVE-4：orforglipron MACE-3 风险↓23%、全因死亡↓57%（4 月读出）", "礼来官方新闻稿", "https://investor.lilly.com/node/54126"),
             L("RASolute 302：daraxonrasib 胰腺癌 mOS 13.2 vs 6.7 月、HR 0.40，ASCO 全体大会+NEJM 同步", "Medable ASCO 2026 全景", "https://www.medable.com/knowledge-center/blog-what-happened-at-asco-26"),
             L("失败：诺和口服司美格鲁肽早期 AD（EVOKE，3,808 例未达 CDR-SB 主要终点，2 月读出）", "代谢科学 GLP-1/AD 转载", "https://metabolicscience.org/glp-1/glp1-alzheimers-disease"),
             L("失败：AZ Wainua（ATTR 心肌病）III 期未达终点、股价 -9%；Neumora navacaprant 两项失败裁员 35%", "Irish Times / Xtalks", "https://xtalks.com/clinical-trial-failures-of-2026-4821/"),
         ],
         risk="GLP-1 口服与 RAS 平台突破主导叙事；H2 关注礼来 retatrutide 与 CagriSema 等 20+ III 期读出。"),
    dict(no=8, group="研发与研发服务", item="顶级学术会议数据释放", score=0, flag="平稳",
         verdict="ASCO/AACR 2026 美国本土公司仍为主角：daraxonrasib（胰腺癌新标准）、J&J Rybrevant 组合 41 个月 mOS、默沙东 ADC+IO HR 0.65、再生元 CR 85% 均为重磅；中国药企 LBA 数量创历史新高但未夺主位。",
         evs=[
             L("ASCO 2026 要点：daraxonrasib、J&J mOS 41 个月、默沙东 sacro-TMT+Keytruda PFS HR 0.65、Regeneron odronextamab CR 85%、礼来 retatrutide 减重 28.7%", "bpiq ASCO 2026 复盘", "https://www.bpiq.com/post/asco-2026-recap-five-days-of-adcs-bispecifics-cell-therapy-and-precision-oncology"),
             L("AACR 2026：Neomorph 分子胶 NEO-811、TNG961 等备受关注，美企主场", "搜狐 AACR 盘点", "https://www.sohu.com/a/1016794624_122655588"),
             L("中国药企 ASCO LBA 数量创纪录（康方 HARMONi-6 mOS 27.9 月），但数据量级不及美企", "Medable ASCO 2026 要点", "https://www.medable.com/knowledge-center/blog-what-happened-at-asco-26"),
         ]),
    dict(no=9, group="研发与研发服务", item="CRO/CDMO 龙头企业订单数据", score=1, flag="向好",
         verdict="美国研发服务链显著复苏并加速：IQVIA Q2 研发解决方案净新增订单 $31.5 亿（+19%）、在手 $342 亿、全年指引上调；Thermo Fisher/Charles River/Sotera 全面上调指引；中美 CXO 同步修复（药明 H1 在手订单 664 亿元）。",
         evs=[
             L("IQVIA 2026Q2：营收 $43.7 亿（+8.7%），研发净新增订单 $31.5 亿（+19%）、订单/簿比 1.22x、在手 $342 亿，全年指引上调", "IQVIA Q2 2026 财报", "https://www.iqvia.com/newsroom/2026/07/iqvia-reports-second-quarter-2026-results"),
             L("Charles River Q2 内生增长转正 0.1%（近 4 年新高）、上调 2026 指引；Sotera Q2 营收 $3.21 亿（+9.2%）", "CRL Q2 2026 SEC 原文", "https://www.sec.gov/Archives/edgar/data/1100682/000110068226000115/crl2q26earningsrelease.htm"),
             L("Thermo Fisher Q2 营收 $119.9 亿（+10%）、内生 +5%、全年指引上调", "Thermo Fisher Q2 2026", "https://www.investing.com/news/transcripts/earnings-call-transcript-thermo-fisher-tops-q2-2026-estimates-and-lifts-outlook-93CH-4809188"),
             L("对照：药明康德 H1 在手订单 664 亿元（+25.2%），中美 CXO 同步复苏", "药明康德 H1 2026 业绩", "https://www.wuxiapptec.com/news/wuxi-news/wuxi-apptec-delivers-strong-result-driven-by-crdmo-model"),
         ]),
    # ---- 板块三 商业化兑现与销售 ----
    dict(no=10, group="商业化兑现与销售", item="核心创新药上市后放量曲线", score=1, flag="向好",
         verdict="GLP-1 与肿瘤免疫双主线延续高景气：礼来 Mounjaro 99.4 亿（+91%）、Zepbound 49.3 亿（+46%），H1 合计 277 亿美元（+88%）；Darzalex 42.1 亿（+19%）；吉利德 Yeztugo 环比 +40%；Dupixent 全球 60 亿（+38%）。",
         evs=[
             L("礼来 2026Q2：Mounjaro $99.4 亿（+91%）、Zepbound $49.3 亿（+46%）、H1 合计 $277 亿（+88%），全年指引升至 $85-87B", "礼来 2026Q2 财报", "https://investor.lilly.com/news-releases/news-release-details/lilly-reports-second-quarter-2026-financial-results-raises-full"),
             L("诺和诺德：司美格鲁肽全系 H1 $175 亿；2026 指引上修至 -6%~0%", "诺和诺德 H1-2026", "https://global.pharmcube.com/news/detail/4b83364f0f1f46719d789156add44a79?type=dailyNews"),
             L("默沙东 Keytruda Q2 $116 亿（+9%，含 QLEX）；强生 Darzalex $42.1 亿（+19%）、Tremfya $20.5 亿（+72%）", "强生 2026Q2 财报", "https://www.jnj.com/media-center/press-releases/johnson-johnson-reports-q2-2026-results-raises-2026-outlook"),
             L("吉利德：Biktarvy $37.7 亿（+7%）、Yeztugo（lenacapavir）Q2 $2.32 亿环比 +40%、全年指引上调至 $10 亿；再生元 Dupixent 全球 $60 亿（+38%）", "吉利德 2026Q2 SEC 财报", "https://www.sec.gov/Archives/edgar/data/882095/000088209526000028/exhibit991earningspressrel.htm"),
         ]),
    dict(no=11, group="商业化兑现与销售", item="Biotech 向 Biopharma 跨越的财务指标", score=1, flag="向好",
         verdict="中型 Biotech 批量跨越盈利拐点：VRTX Q2 GAAP 净利 $11 亿、REGN 净利 $13 亿、ALNY 净利 $1.64 亿（转正，AMVUTTRA 单季破 $10 亿）、ARGX 净利 $4.72 亿（+93%）、LEGN 单季扭亏、ILMN 净利 $2.07 亿。",
         evs=[
             L("福泰 Q2 GAAP 净利 $11 亿（+6%），指引抬升至 $13.1-13.2B", "Vertex 2026Q2 财报", "https://investors.vrtx.com/news-releases/news-release-details/vertex-reports-second-quarter-2026-financial-results"),
             L("再生元 Q2 净利 $13 亿、Non-GAAP EPS $14.29；Sanofi 合作开发余额已清偿", "再生元 2026Q2 财报", "https://investor.regeneron.com/static-files/81b30ae7-65ea-4118-90e1-102ecf9849cf"),
             L("ALNY 净利 $1.64 亿转正（AMVUTTRA 单季 >$10 亿）；ARGX 净利 $4.72 亿（+93%）、VYVGART $15.2 亿（+60%）", "Alnylam 2026Q2 财报", "https://investors.alnylam.com/press-release?id=29986"),
             L("LEGN 单季扭亏 $0.33 亿（CARVYKTI +50%）；ILMN GAAP 净利 $2.07 亿", "传奇生物 2026Q2 SEC", "https://www.sec.gov/Archives/edgar/data/1801198/000180119826000022/a991earningsreleaseq22026.htm"),
         ]),
    dict(no=12, group="商业化兑现与销售", item="海外商业化与销售分成兑现", score=1, flag="向好",
         verdict="Royalty/里程碑在 2026 密集兑现为现金流：ALNY 特许权使用费收入 $0.72 亿（+79%，诺华 Leqvio）；LEGN 获强生里程碑 $0.56 亿；再生元 Sanofi 合作利润份额 $20.3 亿（+59%）；礼来获 BI Jardiance 里程碑 $2.5 亿。",
         evs=[
             L("ALNY 特许权使用费收入 $0.72 亿（+79%，诺华 Leqvio 分成放量）", "Alnylam 2026Q2 财报", "https://investors.alnylam.com/press-release?id=29986"),
             L("LEGN Q2 获强生里程碑 $0.56 亿；CARVYKTI 销售 +50%", "传奇生物 2026Q2 SEC", "https://www.sec.gov/Archives/edgar/data/1801198/000180119826000022/a991earningsreleaseq22026.htm"),
             L("再生元 Sanofi 合作利润份额 $20.3 亿（+59%）", "再生元 2026Q2 财报", "https://investor.regeneron.com/static-files/81b30ae7-65ea-4118-90e1-102ecf9849cf"),
             L("礼来获 BI Jardiance 里程碑 $2.5 亿；BMS licensing income $0.5 亿", "Fierce Pharma 综述", "http://fiercepharma.com/pharma/despite-tempered-sales-outlook-gilead-positions-yeztugo-dominate-hiv-prep-market-sales-surge"),
         ]),
    dict(no=13, group="商业化兑现与销售", item="销售费用率与盈利质量", score=1, flag="向好",
         verdict="费用率控制与利润率兑现为 2026 共同主题：礼来 Q2 销售费用占收入 15%（2025 同期 17.7%）、辉瑞 SI&A 下降、BIIB 营业利润率 16.7%、MRNA 研发+销售费用双降；商业化效率整体提升。",
         evs=[
             L("礼来 Q2 销售费用 $34.3 亿、占收入 15%（vs 2025 同期 17.7%）→ 盈利质量提升", "礼来 2026Q2 财报", "https://investor.lilly.com/node/54786/html"),
             L("辉瑞 SI&A 同比下降 1%；默沙东 SG&A 占收入 23.1%", "辉瑞 2026Q2 财报", "https://investors.pfizer.com/Investors/news-events/News/news-details/2026/Pfizer-Reports-Second-Quarter-Results-And-Raises-Midpoint-of-2026-Revenue-Guidance/default.aspx"),
             L("再生元 2026 指引 R&D $6.5-6.6B（约 40% 收入）、SG&A $2.8-3.0B", "再生元 2026 指引", "https://newsroom.regeneron.com/node/32231/html"),
             L("MRNA Q2 R&D $6.5 亿、SG&A $2.2 亿（双降）；BIIB 营业利润率 16.7%", "Moderna 2026Q2 财报", "http://investors.modernatx.com/quarterly-results"),
         ]),
    # ---- 板块四 政策与外部环境 ----
    dict(no=14, group="政策与外部环境", item="创新药审评审批政策倾向", score=1, flag="向好",
         verdict="审评\"提速\"成主基调：2025 年 CDER 批 46 款（高于 1993 年以来年均 36 款）；礼来 orforglipron 经 CNPV 通道 50 天创速批纪录；单试验改革、罕见病合理机制通道落地；Makary 辞职后 2026-08 提名新局长，政策连续性获确认但存不确定性。",
         evs=[
             L("2025 年 CDER 批 46 款新药（高于 1993 年以来年均 36 款）", "FDA Regulatory Impact Analyses", "https://www.fda.gov/economic-impact-analyses-fda-regulations"),
             L("CNPV 已发 18 张券、批 5 款，审评压至 1-2 个月；orforglipron 50 天速批；关键试验默认 2 项→1 项（2026-02）", "AgencyIQ Makary 政策追踪", "http://www.agencyiq.com/blog/policy-and-promises-tracking-makarys-first-year-running-the-fda"),
             L("2026-02 罕见病\"合理机制\"通道指南草案；境外检查互认（MRA）最终规则", "PhIRDA 单试验改革", "https://www.phirda.com/artilce_41766.html?module=trackingCodeGenerator"),
             L("Makary 2026-05-12 辞职，Kyle Diamantas 代理，2026-08-19 提名 Heidi Overton（待参议院确认）", "Politico", "https://www.politico.com/news/2026/05/12/makary-fda-resign-white-house-00916014"),
         ],
         risk="FDA 领导层动荡（13 个月内第三任）是 2026 下半年最大监管变量。"),
    dict(no=15, group="政策与外部环境", item="医保/定价机制冲击（IRA 谈判）", score=-1, flag="恶化",
         verdict="定价压制制度化并继续加压：首批 10 药 Medicare 价格 2026-01 生效、降幅 38%-79%；第二批 15 药价格 2025-11 公布（净支出降 36%，司美格鲁肽 -71%）、2027 生效；叠加特朗普 MFN（TrumpRx 司美约 $350/月），美国药价天花板系统性下移。",
         evs=[
             L("首批 10 药 2026-01-01 生效：降幅 38%-79%，Medicare 年省约 $60 亿", "CMS 新闻稿", "https://cms.gov/newsroom/press-releases/hhs-announces-15-additional-drugs-selected-medicare-drug-price-negotiations-continued-effort-lower"),
             L("第二批 15 药（2025-11-25 公布、2027 生效）：净支出降 36%（约 $85 亿）；司美格鲁肽 $959→$274（-71%）", "Reuters", "https://www.reuters.com/business/healthcare-pharmaceuticals/us-negotiated-medicare-prices-15-more-drugs-test-cost-savings-promise-2025-11-25/"),
             L("目录价降幅 38%-85%（Calquence -40%、Ibrance -50%、Janumet -85%）；多近专利悬崖，实际冲击或有限", "Fierce Healthcare 逐药价格", "https://www.fiercehealthcare.com/pharma/medicare-unveils-price-reductions-15-drugs-including-novos-semaglutide"),
             L("特朗普 MFN：16 家药企签约、TrumpRx 2026-02 上线（Ozempic 约 $350/月）；以关税豁免绑定价；小分子 9 年/生物 13 年豁免期统一化未立法", "PharmaBoardroom 2026 趋势", "https://pharmaboardroom.com/articles/5-key-us-industry-trends-to-watch-in-2026/"),
         ]),
    dict(no=16, group="政策与外部环境", item="地缘政治与合规风向", score=-1, flag="恶化",
         verdict="外部合规成本系统性抬升：BIOSECURE Act 2025-12 成法、2026-06 药明康德等 28 家列入国防部 1260H（禁令最早 2028 生效、5 年祖父期）；对华专利药 232 关税 100%、BINSA 两院推进、FDA 对华执法量 +59%；美国药企供应链\"变贵、变快受限\"，属制度化趋紧而非断崖。",
         evs=[
             L("BIOSECURE 2025-12-18 随 FY2026 NDAA 生效；2026-06 药明康德等 28 家列入 1260H（药明已起诉国防部）；禁令最早 2028、现有合同 5 年祖父期", "Goodwin BIOSECURE/1260H 更新", "https://www.goodwinlaw.com/en/insights/blogs/2026/06/biosecure-update--1260h-list-released"),
             L("约 120 款在美药由中国 CDMO 生产、79% 受访药企有对华 CDMO 合作；美国贡献药明约 2/3-3/4 收入", "C&EN 药明入黑名单分析", "https://cen.acs.org/business/outsourcing/pentagon-ruling-hits-chinas-wuxi/104/web/2026/06"),
             L("232 关税（2026-04-09 公告）：专利药及 API 征 100%（7-31/9-29 生效）、仿制药/API 暂免、签 MFN+回流协议 2029 前免税", "白宫 232 公告原文", "https://www.govinfo.gov/content/pkg/FR-2026-04-09/pdf/2026-06956.pdf"),
             L("BINSA（2026-06 众议院、08 参议院）拟将生物技术纳入 COINS 出境投资审查（涉中美许可交易约 $1,360 亿）；FDA 2025 财年药品警告信 303 封（+59%）", "Slotkin 参议员 BINSA 公告", "https://www.slotkin.senate.gov/2026/08/06/slotkin-ricketts-introduce-bipartisan-legislation-to-keep-biotech-industry-in-america-not-china/"),
         ],
         risk="下半年跟踪：Overton 确认程序、BINSA 立法进程、2026-11 中期选举、OMB/BCC 名单发布。"),
]

GROUPS = ["资金与资本面", "研发与研发服务", "商业化兑现与销售", "政策与外部环境"]

# ============ 2024 / 2025 年逐项数据（美股口径，同 16 项清单，与 ITEMS 顺序一一对应）============
# 每项: (score, brief, label, url)
YEARLY = {
    2024: [
        (1,  "美欧生物医药 VC 约 $25-26B（416 轮），较 2023 约 $20B 增 20-30%", "SVB 2024 年报", "https://www.svb.com/trends-insights/reports/healthcare-investments-and-exits/healthcare-investments-and-exits-annual-2024/"),
        (0,  "折价/平价轮占比约 28% 创近年新高，但 biopharma 折价轮已开始回落", "GVB 2024 年中报", "https://www.gvbworld.com/trends-insights/reports/healthcare-investments-and-exits/2024-mid-year/index.html"),
        (1,  "IPO 30 家/募资约 $4.0B（vs 2023 年 18 家/$2.9B，+39%）；CG Oncology $437M 居首", "EY Beyond Borders 2025", "https://www.ey.com/zh_tw/insights/health/beyond-borders-2025"),
        (-1, "生物医药 M&A 约 $79B vs 2023 约 $158B 腰斩；全年无 >$10B 制药并购（Novo-Catalent $16.5B 为 CDMO）", "BioSpace 并购盘点", "https://www.biospace.com/business/pharma-has-kept-m-a-spending-small-this-year-with-just-one-deal-topping-5b"),
        (-1, "39% 公司现金 <12 个月（2019 以来最高）；上市 biotech 783 家 vs 2022 年 939 家，破产密集", "EY Beyond Borders 2025", "https://www.ey.com/zh_tw/insights/health/beyond-borders-2025"),
        (1,  "FDA 批 50 款（34 NME+16 BLA），略降于 2023 年 55 款但居历史次高位；22 款 first-in-class", "FDA Novel Drug Approvals 2024", "https://www.fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2024"),
        (1,  "Kisunla（AD）7 月、Cobenfy（精神分裂首创新机制）9 月获批；orforglipron III 期减重达标；ATTAIN-1 不及预期", "礼来官方新闻稿", "https://e.lilly/4673Bo6"),
        (1,  "洛拉替尼 CROWN 5 年 PFS 60%、T-DXd DB-06、ADRIATIC mOS 55.9 月改写指南；中国 ADC 军团崛起", "国信证券 ASCO 总结", "https://pdf.dfcfw.com/pdf/H3_AP202407111637793753_1.pdf"),
        (-1, "CRO 仍处低谷：IQVIA +2.8%（$154.1 亿）、Charles River -1.9% 净利降 95%、2025 指引再降", "医药魔方 CRO TOP10", "https://www.phirda.com/artilce_39111.html"),
        (1,  "替尔泊肽合计 $164.6 亿（+208%）、司美全系约 $293 亿（+38%）、Keytruda $294.8 亿（+18%）", "礼来 Q4 官方", "https://investor.lilly.com/node/51906"),
        (1,  "AMGN $334 亿（+19%）、REGN $142 亿（+8%）、BIIB FCF 翻倍、VRTX $110 亿（+12%）盈利现金流稳健", "Amgen 2024Q4 财报", "https://investors.amgen.com/news-releases/news-release-details/amgen-reports-fourth-quarter-and-full-year-2024-financial"),
        (1,  "Royalty Pharma 组合收入约 $28 亿（+13%）、synthetic royalty $925M 创纪录", "Royalty Pharma", "https://www.royaltypharma.com/?p=5831"),
        (1,  "礼来 MS&A 占总收入 19%（收入 +32%）、Non-GAAP 营业利润率升至 32%（净利 +102%）", "礼来 Q4 官方", "https://investor.lilly.com/node/51906"),
        (1,  "审批高效：50 款、94% 达成 PDUFA 目标、68% 美国全球首发；加速批准新指南落地", "FDA 加速批准指南", "https://www.fda.gov/media/184120/download"),
        (0,  "IRA 首批 10 药 2 月报价、9 月公布最高公平价（Eliquis -56%），2026 生效；当期无直接冲击", "BioSpace 谈判参与", "https://www.biospace.com/ten-pharma-companies-register-to-participate-in-medicare-drug-price-negotiation-program"),
        (1,  "BIOSECURE 5/9 月两院通过但 12/7 未被纳入 NDAA、118 届国会立法流产；当年无实质冲击", "JDSupra 立法史", "https://jdsupra.com/legalnews/it-s-baaack-the-biosecure-act-passes-7946306/"),
    ],
    2025: [
        (0,  "VC 融资总额约 $338 亿/1,171 笔，与 2024 年基本持平（$319 亿/1,091）", "BioSpace/PitchBook", "https://www.biospace.com/business/early-stage-biotechs-suffer-in-2025-as-vc-shuns-risk-pitchbook"),
        (-1, "折价融资事件约 60 起、占比约 32%；Q2 后 IPO 上市后平均 -18.7%", "Gibson Dunn 资本市场复盘", "https://biotechbriefings.gibsondunn.com/q2-2025-life-sciences-capital-markets-recap"),
        (-1, "IPO 仅 8 家/约 $1.6B（2024 年 19 家）；年初潮后半年冻结，Follow-on Q2 掉 49%", "Patient Daily 复盘", "https://patientdaily.com/biotech-ipo-activity-slows-sharply-in-2025-as-investor-scrutiny-increases"),
        (1,  "MNC 并购约 $1,330 亿（+133%），≥$10B 4-5 起：J&J/Intra-Cellular $146 亿、Novartis/Avidity $120 亿", "IQVIA M&A 展望", "https://www.iqvia.com/en-gb/locations/emea/blogs/2026/01/biopharma-m-and-a-outlook-for-2026"),
        (-1, "33% 上市 Biotech 现金 <12 个月（较 2024 年 39% 改善 6pp）；约 11 家公司倒闭", "BioSpace/EY", "https://www.biospace.com/business/four-years-and-219-lost-companies-later-biotech-still-has-a-cash-problem"),
        (1,  "FDA 批 46 款（NME 34+BLA 12）；first-in-class 22 款（占 48%），加速批准占 24%（+10pp）", "RAPS 审批盘点", "https://www.raps.org/resource/cder-approved-46-novel-drugs-in-2025-half-for-rar.html"),
        (0,  "阳性：VRTX 非阿片止痛 Journavx、礼来 retatrutide/orforglipron III 期成功；失败：诺和司美 AD（EVOKE）双失败、BMS Cobenfy 三期失败", "Patient Daily 失败盘点", "https://patientdaily.com/stories/677147914-major-clinical-trial-failures-mark-challenging-year-for-biopharma-companies"),
        (1,  "ASCO 2025 中国 LBA 11 项、ADC 研究近半（百利天恒双抗 ADC 领跑）；美国药企稳定", "摩熵/药研", "https://www.pharnexcloud.com/zixun/trz_47816"),
        (-1, "复苏弱：IQVIA +5.87%（在手订单 +4.1%）、Thermo Fisher +3.9%、Charles River -0.85% 承压", "新浪财经梳理", "https://cj.sina.cn/articles/view/5557080256/14b3a50c002001k1o4"),
        (1,  "Mounjaro $229.6 亿（+99%）、Zepbound $135.4 亿（+175%）、Keytruda $316.8 亿（+7%）、Dupixent $178 亿（+26%）", "礼来 2025 财报", "https://investor.lilly.com/node/53786"),
        (1,  "VRTX $120.7 亿（+9%）、REGN $143.4 亿（+1%）、礼来 $651.8 亿（+44%）净利 +95%、AMGN $368 亿（+10%）", "AMGN 2025 全年财报", "https://www.nasdaq.com/press-release/amgen-reports-fourth-quarter-and-full-year-2025-financial-results-2026-02-03"),
        (1,  "Royalty Pharma 组合分账收入 $32.54 亿（+16%）、royalty 市场规模 $100 亿新高", "Royalty Pharma 2025", "https://www.royaltypharma.com/news/royalty-pharma-reports-q4-and-full-year-2025-results/"),
        (0,  "礼来 SG&A 率约 37%；辉瑞 SG&A 率约 38%，盈利质量改善但费用刚性", "辉瑞 2025 全年业绩", "https://investors.pfizer.com/Investors/news-events/News/news-details/2026/Pfizer-Reports-Solid-Full-Year-2025-Results-And-Reaffirms-2026-Guidance/default.aspx"),
        (-1, "CDER 年内五任主任、裁员 3,500 人；加速批准趋严（确认性试验「在进行中」要求）", "Morgan Lewis 分析", "https://www.morganlewis.com/blogs/as-prescribed/2025/02/fdas-recent-guidance-on-accelerated-approval-and-implications-for-rare-diseases"),
        (-1, "IRA 首批 10 药谈判价公布、降幅 38-79%（均约 50%），2026/1 生效；Amgen Otezla 减值 $12 亿", "CMS 新闻稿", "https://cms.gov/newsroom/press-releases/hhs-announces-15-additional-drugs-selected-medicare-drug-price-negotiations-continued-effort-lower"),
        (-1, "BIOSECURE 2025-12-18 随 FY2026 NDAA 成法（药明系未被点名）；MFN 定价行政令 4 月落地", "Latham & Watkins", "https://www.lw.com/admin/upload/SiteAttachments/BIOSECURE-Act-Becomes-Law-Limiting-Grants-With-Biotechnology-Companies-of-Concern.pdf"),
    ],
}

# 逐年总览
YEAR_TOTALS   = {2024: 8, 2025: -1, 2026: 9}
YEAR_LEVELS   = {2024: "结构性景气", 2025: "筑底/盘整期", 2026: "结构性景气"}
YEAR_CN       = {2024: "11 向好 / 2 平稳 / 3 恶化", 2025: "6 向好 / 3 平稳 / 7 恶化", 2026: "11 向好 / 3 平稳 / 2 恶化"}
YEAR_GROUP_POINTS = {
    2024: {"资金与资本面": 0, "研发与研发服务": 2, "商业化兑现与销售": 4, "政策与外部环境": 2},
    2025: {"资金与资本面": -2, "研发与研发服务": 1, "商业化兑现与销售": 3, "政策与外部环境": -3},
    2026: {"资金与资本面": 3, "研发与研发服务": 3, "商业化兑现与销售": 4, "政策与外部环境": -1},
}
YEAR_SUMMARIES = {
    2024: "GLP-1 超级周期点燃、IPO 与授权交易回暖、FDA 批 50 款，典型「K 型分化」结构性景气年——头部繁荣（礼来/诺和/辉瑞放量）、尾部出清（39% 现金<12 月、M&A 腰斩、CRO 低谷）并存。",
    2025: "「资金通道收紧 + 政策扰动密集」的筑底年：IPO 骤降至 8 家、折价融资 32%、BIOSECURE 年末成法、IRA 首批降价公布；但并购转暖（+133%）与创新资产（GLP-1/ADC）基本面强劲提供向上弹性，逐项重算合计 -1 落筑底区间上沿。",
    2026: "「融资-退出双修复 + 商业放量验证 + 盈利拐点确认」上升周期：VC $9.1B 峰值、IPO 18 家/$5B、>$10B 并购 4 起、中型 Biotech 批量盈利；压制端为 IRA+MFN 定价与 BIOSECURE/关税合规成本，结构性景气上沿（+9）。",
}

GROUP_SUMMARIES = {
    "资金与资本面": "2026 美股生物科技处于\"融资-退出双修复\"周期：一级总量创新高（H1 $9.1B）、IPO 窗口重开（18 家/$5B）、MNC >$10B 并购密集（4 起）三轮共振；但早期融资缺口、1/3 公司 <12 个月现金与估值倒挂仍存。较中国口径（+1）偏强：美股资本通道更宽、IPO 全球首选。",
    "研发与研发服务": "FDA 审批节奏高位（H1 26 款）、重磅读出含金量高（口服 GLP-1 心血管获益、泛 RAS 抑制剂胰腺癌 HR 0.40）、CRO/CDMO 订单全面反转（IQVIA 在手 $342 亿）；ASCO/AACR 美企主场。较中国口径（+4）略低一分：学术会议主场优势对等、但中国数据质量跃迁更快。",
    "商业化兑现与销售": "GLP-1 与肿瘤免疫双主线验证、中型 Biotech（ALNY/ARGX/LEGN/VRTX/REGN）批量盈利与现金流双转正；Royalty/里程碑密集兑现。与中国口径（+4）同为最强板块，但美国体量高一个量级。",
    "政策与外部环境": "审评提速（+1）与 IRA 定价压制（-1）、地缘合规趋紧（-1）对冲，净影响中性偏负；罕见病豁免、MFN/本土化布局药企为结构性赢家。较中国口径（+1）弱：中国有政策强支持（国谈温和+双目录），美国则面临 IRA+MFN 定价天花板。",
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
)

def md_link(label, url):
    """返回 markdown 风格链接文本用于 JS 数据；HTML 卡片直接渲染 <a>"""
    return '[' + label + '](' + url + ')'

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
<title>美股生物科技行业景气度核查报告 · 2026-08</title>
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
    <h1>美股生物科技行业景气度核查报告</h1>
    <div class="meta">核查日期：@@TODAY@@ ｜ 口径：<b>美股上市的非中国生物科技公司</b>（美国 MNC 药企 + 美国/欧洲 Biotech ADR）｜ 方法：16 项核查清单逐项打分（+1 向好 / 0 平稳 / -1 恶化）｜ 每项关键数据附来源链接 ｜ 数据时点：2026 中报/8 月最新</div>
    <div class="cn-note">📌 <b>口径说明：</b>本报告按用户要求分析<b>美股上市的非中国公司</b>（礼来/诺和/默沙东/强生/BMS/吉利德/VRTX/REGN/ALNY/ARGX/LEGN 等），中国创新药仅在第 4/9/16 项及板块小结处作为对照提及。<b>中国口径对照</b>（上一版核查）：总分 +10 = 强景气；美股口径本版 +9 = 结构性景气上沿 —— 差异主要在政策板块（中国强支持 vs 美国 IRA 定价压制）。</div>

    <div class="verdict">
      <div class="t">综合景气度诊断</div>
      <div class="b">16 项合计 <span class="hlb">@@TOTAL@@ 分</span> → <span class="hl">@@LEVEL@@</span>（@@LEVEL_CN@@）：@@POS@@ 项向好 / @@NEU@@ 项平稳 / @@NEG@@ 项恶化</div>
      <div class="score-line">
        <span class="chip p">✓ 向好 @@POS@@ 项</span>
        <span class="chip z">— 平稳 @@NEU@@ 项</span>
        <span class="chip n">✕ 恶化 @@NEG@@ 项</span>
      </div>
    </div>
    <div class="keypoint" style="margin-top:14px;">
      <b>核心判断：</b>美国生物科技处于「融资-退出双修复 + 商业放量验证 + 盈利拐点确认」的上升周期：一级融资 H1 $9.1B（2022 年以来峰值）、IPO 窗口重开（18 家/$5B）、MNC >$10B 并购 4 起、GLP-1 双雄带动板块 beta、中型 Biotech（ALNY/ARGX/LEGN）单季盈利与现金流双转正。压制因素集中在<b>定价端</b>：IRA 谈判（司美格鲁肽 -71%）与 MFN 下美国药价天花板系统性下移，叠加 BIOSECURE/232 关税/BINSA 推高供应链合规成本。景气度落于<b>结构性景气上沿（+9）</b>——「板块中枢向上、个股分化加大」，下半年关键变量：FDA 局长确认、BINSA 立法、2026-11 中期选举、H2 大 III 期读出。
    </div>
  </div>

  <div class="card">
    <h2>一、总体评分结构</h2>
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
    <h2>二、2024 → 2025 → 2026 三年景气度演化对比</h2>
    <div class="grp-summary">同一套 16 项核查清单、同一打分口径（美股上市非中国公司），逐年回溯打分。2024 = 结构性景气（+8，GLP-1 超级周期）→ 2025 = 筑底（-1，IPO 冻结/BIOSECURE 成法/IRA 降价）→ 2026 = 结构性景气上沿（+9，融资-退出双修复+盈利拐点）。三年呈现明显的「V 型修复」，且 2026 的修复由商业化兑现与资本通道共同驱动，质量高于 2024 年。</div>
    <div class="scroll">
      <table style="min-width:720px;">
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
    <div class="note">注：上表与上图展示三年各板块得分演化；红=正分（涨）、绿=负分（跌），色弱安全叠加数字与文字。2024/2025 数据为回溯口径，来源链接见下方逐年明细。</div>
  </div>

  <div class="card">
    <h2>三、逐年景气度明细（2024 / 2025 回溯 + 2026）</h2>
    <div class="grp-summary">以下逐年列出 16 项核查的关键依据与来源链接。2024/2025 为回溯打分（同口径），2026 为当前核查。点击 ⧉ 进入一手来源（FDA/CMS/SEC/公司新闻稿/权威行业统计）。</div>
    @@YEAR_CARDS@@
  </div>

  <div class="card">
    <h2>四、2026 年板块核查明细（16 项）</h2>
    <div class="grp-summary">以下四个板块卡片为 2026 年当前核查的逐项明细（与「一、总体评分结构」对应），关键数据均附来源链接（⧉ 一手来源）。</div>
    @@GROUP_CARDS@@
  </div>

  <div class="card">
    <h2>五、风险提示与跟踪节点</h2>
    <div class="warn">
      <b>1. 数据依赖与时效：</b>本报告数据截至 2026-08-23，主要来自各公司 2026Q2/H1 财报、FDA/CMS/GovInfo 官方页面及行业统计（BioPharma Dive、PitchBook、DealForma、EY/SVB、Fierce Pharma 等）；所有关键数据均已附来源链接（⧉ 符号）。美股 NASDAQ 前 8 月 IPO 精确家数、Down Round 全样本占比等官方口径存在统计差异，已采用主流口径并注明。
    </div>
    <div class="warn">
      <b>2. 关键下行变量：</b>① 定价：IRA 第二轮（2027 生效）+ MFN/TrumpRx，大药企重磅药单价承压（K 药、GLP-1 系）；② 地缘：BIOSECURE 禁令最早 2028、BINSA 立法推进、232 关税 7-31/9-29 生效，依赖中国 CDMO 的美企（药明供应约 120 款在美药）面临转产压力；③ 临床：H2 关注礼来 retatrutide、CagriSema 等 20+ III 期读出与 K 药/司美专利悬崖（2031-2033）。
    </div>
    <div class="warn">
      <b>3. 结构性风险：</b>早期 Biotech 融资缺口仍在（2025 早期轮次下滑）、33% 公司现金 <12 个月；2026H1 已有 8 款新药被 FDA 拒批；诺和 AD（EVOKE）与 AZ（Wainua）大型失败对个股冲击显著。
    </div>
    <div class="warn">
      <b>4. 方法局限：</b>本核查为「快照式」景气度评估，16 项等权打分为相对口径（±1），未加权、未做历史分位数标准化；景气度判定代表 2026-08 时点截面结论，不构成投资建议。
    </div>
  </div>

  <div class="card">
    <h2>附：核查方法论</h2>
    <div class="grp-summary">按「资金与资本面（先行指标）→ 研发与研发服务（中早期指标）→ 商业化兑现（终端验证）→ 政策与外部环境（发展天花板）」四层传导框架逐项核对。计分规则：+1 向好/超预期、0 平稳/符合预期、-1 恶化/低于预期，加总后按四档区间判定景气度（+10~+16 强景气 / +3~+9 结构性景气 / -2~+2 筑底盘整 / -16~-3 低迷）。查询清单为既定核查框架；每项结论附关键数据与<b>可点击来源链接</b>（⧉ = 一手来源，FDA/CMS/SEC/公司官方新闻稿优先），未核实项已明确标注。</div>
    <div class="note">报告生成：@@TODAY@@ ｜ 时点口径：2026Q2/H1 财报为主、2025 全年为辅（已注明） ｜ 历史同类报告：reports/21（上一版为中国口径）</div>
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

// 2) 三年景气度演化：总分折线 + 板块得分堆叠
(function(){
  var el = document.getElementById('chart_years');
  if(!el) return;
  var chart = echarts.init(el);
  var years = Object.keys(DATA.yearly.totals).map(Number).sort();
  var groups = DATA.yearly.groups;
  var series = groups.map(function(g){
    return {
      name: g,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineWidth: 2.5,
      data: years.map(function(y){ return DATA.yearly.group_points[y][g]; }),
      itemStyle: { color: null }
    };
  });
  var colors = ['#e03131','#1e66d6','#0aa06e','#7048e8'];
  series.forEach(function(s, i){ s.itemStyle.color = colors[i]; s.lineStyle = {width: 2.5, color: colors[i]}; s.itemStyle.color = colors[i]; });
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{top:0, textStyle:{fontSize:12}},
    grid:{left:10,right:52,top:30,bottom:24,containLabel:true},
    xAxis:{type:'category',data:years.map(String),axisLabel:{fontSize:13}},
    yAxis:{type:'value',min:-4,max:5,splitLine:{lineStyle:{type:'dashed',color:'#eef0f3'}},axisLabel:{formatter:function(v){return (v>0?'+':'')+v;}}},
    series: series
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
    cn = CN_NUM[idx]
    return """<div class="card">
  <h2>@@CN@@、@@GNAME@@ <span class="grp-score @@CLS@@">板块得分 @@SC@@</span></h2>
  <div class="grp-summary">@@SUMMARY@@</div>
  <div class="scroll"><table>
    <thead><tr><th style="width:70px">打分</th><th style="min-width:320px">核查项与结论</th><th style="min-width:400px">关键数据与依据（含来源链接）</th></tr></thead>
    <tbody>@@ROWS@@</tbody>
  </table></div>
</div>""".replace("@@CN@@", cn).replace("@@GNAME@@", g).replace("@@CLS@@", sc_cls).replace("@@SC@@", ("+" + str(sc)) if sc > 0 else str(sc)).replace("@@SUMMARY@@", GROUP_SUMMARIES[g]).replace("@@ROWS@@", "".join(rows))

def year_card_html(year):
    """生成某历史年份的 16 项明细卡片（2024/2025 回溯）"""
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
  <h2>三、@@YEAR@@ 年核查明细 <span class="tag">@@TAG@@</span> <span class="grp-score @@CLS@@">合计 @@SC@@</span></h2>
  <div class="grp-summary">@@SUM@@</div>
  <div class="scroll"><table>
    <thead><tr><th style="min-width:200px">核查项</th><th style="width:80px">打分</th><th style="min-width:440px">关键数据与依据（含来源链接）</th></tr></thead>
    <tbody>@@ROWS@@</tbody>
  </table></div>
</div>""".replace("@@YEAR@@", str(year)).replace("@@TAG@@", tag) \
        .replace("@@CLS@@", "s1" if YEAR_TOTALS[year] > 0 else "s0") \
        .replace("@@SC@@", ("+" + str(YEAR_TOTALS[year])) if YEAR_TOTALS[year] > 0 else str(YEAR_TOTALS[year])) \
        .replace("@@SUM@@", YEAR_SUMMARIES[year]).replace("@@ROWS@@", "".join(rows))

def main():
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
    # 三年对比表
    th_groups = "".join('<th>{}</th>'.format(g) for g in GROUPS)
    year_rows = []
    for y in [2024, 2025, 2026]:
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
    year_cards = year_card_html(2024) + year_card_html(2025)
    html = HTML.replace("@@TODAY@@", TODAY).replace("@@TOTAL@@", str(TOTAL)) \
        .replace("@@LEVEL@@", LEVEL).replace("@@LEVEL_CN@@", LEVEL_CN) \
        .replace("@@POS@@", str(POS)).replace("@@NEU@@", str(NEU)).replace("@@NEG@@", str(NEG)) \
        .replace("@@GROUP_ROWS@@", "".join(grp_rows)) \
        .replace("@@GROUP_CARDS@@", group_cards) \
        .replace("@@TH_GROUPS@@", th_groups) \
        .replace("@@YEAR_ROWS@@", "".join(year_rows)) \
        .replace("@@YEAR_CARDS@@", year_cards)
    data_json = json.dumps(DATA, ensure_ascii=False, allow_nan=False)
    html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + data_json + ";")
    html = html.replace("@@RENDER_JS__", RENDER_JS)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT)
    print("written: %s size=%d" % (OUT, size))

if __name__ == "__main__":
    main()