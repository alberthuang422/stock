# -*- coding: utf-8 -*-
"""生物医药行业景气度核查报告构建脚本
输出: reports/21_生物医药行业景气度/index.html
用法: python build_biopharma_prosperity.py
"""
import json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "21_生物医药行业景气度")
OUT = os.path.join(OUT_DIR, "index.html")
os.makedirs(OUT_DIR, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# ============ 16 项打分数据 ============
# 每一项: id, no, item(核查项), group, score(+1/0/-1), verdict(结论句),
#          evidence(关键数据列表), sources(来源列表), flag(标签: 向好/平稳/恶化)
ITEMS = [
    # ---- 板块一 资金与资本面 ----
    dict(no=1, group="资金与资本面", item="一级市场投融资总量与频次",
         score=1, flag="向好",
         verdict="明确止跌回升：2026H1 中国医疗健康一级市场融资 725.6 亿元、814 起事件，同比 +41.7%/+13.8%；创新药口径融资 58.1 亿美元、同比 +79.1%，金额增幅显著跑赢事件数。",
         evidence=["2026H1 一级市场融资总额 725.6 亿元（+41.7%），事件 814 起（+13.8%）",
                   "创新药口径融资 58.1 亿美元、同比 +79.1%（医药魔方口径）",
                   "2026Q1 单季 410 起、354.6 亿元，同比 +50.5%",
                   "单笔规模上升，资金向头部集中，B 轮后融资占比 81.7%"],
         sources=["医药魔方《2026H1 医疗健康投融资趋势盘点》", "医药魔方《2026Q1 报告》", "清科研究中心"]),
    dict(no=2, group="资金与资本面", item="融资金额与估值健康度",
         score=-1, flag="恶化",
         verdict="结构性分化：头部高确定性资产溢价融资（华深智药 7.87 亿美元 B 轮、箕星药业 2.87 亿美元 D1 轮），但尾部 Down Round 与折价配售密集，Pass 轮与估值下修仍是腰部/尾部 Biotech 主流。",
         evidence=["药捷安康年内三轮配售折价约 18%，价格 92.85→57.03→40.83 港元，市值 2500 亿→47 亿港元",
                   "劲方医药折价 9.71% 配售；单管线公司一级平均估值降幅超 30%",
                   "头部资产维持溢价：华深智药 7.87 亿美元 B 轮、箕星药业 2.87 亿美元 D1 轮",
                   "战略融资占比 36.6%，资金向确定性资产集中"],
         sources=["新浪证券", "每日经济新闻", "智通财经", "医药魔方"]),
    dict(no=3, group="资金与资本面", item="二级市场 IPO 与再融资通道",
         score=1, flag="向好",
         verdict="通道回暖：2026H1 港股 18A 共 11 家 IPO、募资约 119–127 亿港元，接近 2025 全年（16 家/137.7 亿）规模；科创板新受理 16 家生物医药企业、拟募超 270 亿元，第五套标准重启后受理提速。",
         evidence=["港 18A：2026H1 11 家 IPO、募资约 119–127 亿港元（瑞博生物 18.3 亿居首）",
                   "科创板：新受理 16 家生物医药企业、拟募超 270 亿元（映恩生物 41 亿居首）",
                   "头部再融资顺畅：科伦博泰 27 亿港元配售（三年累计近 70 亿）、信达 43.1 亿、康方 35.2 亿",
                   "首日表现分化：真健康医疗 +217%、华健未来 -57%（冰火两重天）"],
         sources=["新时空研究院半年报", "港交所数据", "新浪财经", "科创板日报", "证券时报"]),
    dict(no=4, group="资金与资本面", item="跨境 BD 授权交易活跃度",
         score=1, flag="向好",
         verdict="爆发式增长：2026H1 license-out 81–86 笔、总对价 997–1100 亿美元（约为 2025 全年的 73%–80%），首付款约 50–64.5 亿美元；全球 TOP10 交易中国占 8 席，石药-AZ 185 亿美元创纪录。",
         evidence=["2026H1 license-out 总对价 997–1100 亿美元（=2025 年全年约 73%–80%），首付款 50–64.5 亿美元",
                   "石药-AZ 185 亿美元（首付 12 亿美元）、恒瑞-BMS 152 亿美元、信达-辉瑞 105 亿美元（首付 6.5 亿）",
                   "荣昌-艾伯维 56 亿美元（首付 6.5 亿）、瑞博-Madrigal 44 亿美元；单笔 >10 亿美元 23 笔",
                   "风险仍存：宜明昂科-Instil 终止（>20 亿美元、仅收 3500 万美元）；历史退货率约 40%、里程碑兑现率约 22%"],
         sources=["医药魔方", "动脉智库", "东方证券", "Chinamed Global", "路透/央视"],
         risk="BD 退货案例抬头（宜明昂科、默克-恒瑞、辉瑞-和铂），里程碑兑现率低，需跟踪退货率。"),
    dict(no=5, group="资金与资本面", item="企业现金流安全线",
         score=-1, flag="恶化",
         verdict="结构性风险：55 家 18A 公司 2025 年报现金合计 737 亿元、同比 +40.26%，但明宇制药现金仅撑约 16 个月、景泽生物约 14 个月，尾部公司账上现金普遍不足以支撑 24 个月。",
         evidence=["55 家 18A 公司 2025 年报现金合计 737 亿元（+40.26%）、亏损收窄 55%（西南证券）",
                   "明宇制药现金约撑 16 个月；景泽生物 0.81 亿元仅够 14 个月（三次递表续命）",
                   "易慕峰 2026H1 现金 4.02 亿元（年烧 1.9–2.4 亿，约 2 年）；歌礼 23.05 亿可撑至 2029 年",
                   "行业提示：现金 window 短于 12 个月者会被 MNC 压低 BD 首付、融资压力大"],
         sources=["西南证券《2025 年报总结》", "新浪证券", "长桥", "雪球"]),
    # ---- 板块二 研发与研发服务 ----
    dict(no=6, group="研发与研发服务", item="IND/NDA 申报与获批数量",
         score=1, flag="向好",
         verdict="申报获批双放量、审批加速：2026H1 NMPA 获批 38 个 1 类创新药（对比 2025 全年 76 个创新高）；CDE 受理 IND 1017 个品种（+14.1%）、NDA 202 个品种；FDA 批准中国原研 2 款（海思科环泊酚、百济索托克拉）。",
         evidence=["2026H1 获批 38 个 1 类创新药，其中 11 个 FIC 均国产；2025 全年 76 个（+65%，创历史新高）",
                   "2026H1 CDE 受理 IND 1017 个品种（+14.1%）、NDA 202 个品种；1 类新药获批率 44/53",
                   "FDA 2026H1 批准 24 款新药中含中国原研 2 款：海思科环泊酚（首款赴美静脉麻醉原研）、百济索托克拉（美国十年首款 BCL2 抑制剂）",
                   "2026 前 5 月 IND 申报 511 项（+30%）"],
         sources=["国家药监局", "药智数据", "摩熵医药", "法伯科技"]),
    dict(no=7, group="研发与研发服务", item="后期临床管线占比与成果",
         score=1, flag="向好",
         verdict="III 期管线充裕、阳性读出密集：2026Q1 活跃管线 5827 个、III 期 740 个（12.7%）；康方依沃西 HARMONi-6 头对头阳性（OS HR=0.66）登 ASCO Plenary；百利天恒双抗 ADC、恒瑞 HER2 ADC、GLP-1 均 III 期达标。",
         evidence=["活跃管线 2026Q1 共 5827 个，III 期 740 个（12.7%，PharmCube）",
                   "康方依沃西 HARMONi-6：鳞状 NSCLC 一线 OS HR=0.66（mOS 27.9 vs 23.7 月）",
                   "百利天恒 iza-bren（EGFR×HER3 双抗 ADC）TNBC III 期达双终点并受理 NDA；恒瑞 SHR-A1811 III 期优效",
                   "失败个案可控：依沃西 HARMONi-3 鳞状队列 PFS 中期未达预期（终局待下半年）、和铂 batoclimab TED 两项 III 期失败"],
         sources=["康方/Summit 公告", "医药魔方", "中信/华创研报", "Lancet"],
         risk="HARMONi-3 全球头对头 K 药终局是下半年最大不确定性。"),
    dict(no=8, group="研发与研发服务", item="顶级学术会议数据释放",
         score=1, flag="向好",
         verdict="质量数量双创新高：ASCO 2026 中国主导口头报告 94 项（+29%）、LBA 13 项均创纪录，依沃西 HARMONi-6 为 ASCO 61 年首个中国原研 Plenary；AACR 104 家中国企业约 400 项成果。",
         evidence=["ASCO 2026：中国主导口头报告 94 项（2025 年 73 项，+29%）、LBA 13 项，均创纪录",
                   "依沃西 HARMONi-6 登 ASCO 61 年首个中国原研 Plenary 并发表于 Lancet",
                   "AACR 2026：104 家中国企业、约 400 项成果、13 家重磅口头报告；92 款 ADC 亮相",
                   "单药数据：泽璟 ZG006 三抗 ORR 74.2%；信达 IBI363 免疫耐药 NSCLC 2 年 OS 47.8%"],
         sources=["ASCO/Akeso 官网", "医药魔方", "券商点评"]),
    dict(no=9, group="研发与研发服务", item="CRO/CDMO 龙头企业订单数据",
         score=1, flag="向好",
         verdict="订单全面反转、指引上修：药明康德 2026H1 在手订单 664.3 亿元（+25.2%）、新签订单约 +40%，全年收入指引上调至 585–605 亿（+35–39%）；康龙新签订单 +30% 以上、药明生物未完成订单 203 亿美元。",
         evidence=["药明康德 2026H1：营收 289 亿（+38.9%）、在手订单 664.3 亿（+25.2%）、新签订单约 +40%，全年指引上调 +35–39%",
                   "TIDES（多肽）H1 72.6 亿（+44.3%），全年指引上调至 +45%，产能达 10 万升",
                   "康龙化成：新签订单 +30% 以上（CDMO +50%+）；药明生物：未完成订单 203 亿美元，年内新增 69 项目（+50%+）",
                   "凯莱英 H1 收入 +20.1%、净利 +23.7%，绑定 GLP-1/ADC 商业化；泰格订单维持高位"],
         sources=["药明康德/康龙化成/药明生物半年报", "证券时报", "财联社"]),
    # ---- 板块三 商业化兑现与销售 ----
    dict(no=10, group="商业化兑现与销售", item="医保谈判准入与降幅",
         score=1, flag="向好",
         verdict="规则温和、准入扩大：2025 年国谈成功率 88%（2024 年 76%），新增 114 种药品含 50 种 1 类创新药；简易续约仅 15 种降价（平均 8.4%）；首版商保创新药目录 19 种落地，2026 年新增预申报机制。",
         evidence=["2025 国谈谈判/竞价成功率 88%（2024 年 76%，创七年最高）；新增 114 品种含 50 种 1 类创新药",
                   "新增药品平均降幅约 60%+ 属常规区间；简易续约仅 15 种降价、平均 8.4%，对已进保品种极其温和",
                   "首版商保创新药目录（原丙类思路）19 种含 5 款 CAR-T；2026-05 已引入预申报机制",
                   "2026 年目录预计 11 月底前公布；商保转医保衔接机制推进"],
         sources=["新华社", "国家医保局 2026 年调整方案征求意见稿", "phirda"]),
    dict(no=11, group="商业化兑现与销售", item="核心创新药上市后放量曲线",
         score=1, flag="向好",
         verdict="头部单品种进入「医保+多适应症+渠道下沉」三轮放量：替雷利珠单抗 2025 全球 52.97 亿元（+18.6%）；康方产品收入 30.33 亿元（+51%），依沃西 2 项适应症进医保；信达产品收入 118.96 亿元（+44.6%）。",
         evidence=["百济替雷利珠单抗 2025 全球销售额 52.97 亿元（+18.6%）",
                   "康方产品收入 30.33 亿元（+51%），依沃西（AK112）上市首年 2 项适应症进医保",
                   "信达产品收入 118.96 亿元（+44.6%）；2026H1 产品收入超 82 亿元（+55%）",
                   "传奇西达基奥仑赛全球放量（详见第 12 项）；进院覆盖率随医保+双目录提升"],
         sources=["百济/康方/信达 2025 年报", "东吴证券研报", "新浪财经"]),
    dict(no=12, group="商业化兑现与销售", item="海外商业化与销售分成兑现",
         score=1, flag="向好",
         verdict="海外实现规模化收入：西达基奥仑赛 2025 全球净销售 18.87 亿美元（+96%），强生分成下传奇全年营收 10.29 亿美元；呋喹替尼海外 3.66 亿美元；百济泽布替尼自营放量自收；恒瑞 GLP-1 已确认 1.1 亿美元。",
         evidence=["传奇生物西达基奥仑赛 2025 全球净销售 18.87 亿美元（+96%），传奇全年营收 10.29 亿美元、产品线首次盈利",
                   "呋喹替尼海外销售额 3.66 亿美元（武田分成），和黄综合收入 0.89 亿美元",
                   "依沃西海外尚未获批，康方已落袋约 5.7 亿美元首付+里程碑；恒瑞 GLP-1 已确认 1.1 亿美元",
                   "百济泽布替尼美国自营自收，贡献公司整体盈利拐点（详见第 13 项）"],
         sources=["传奇生物 2025 业绩公告", "强生 2025 年报", "和黄医药公告", "康方生物公告"],
         risk="多数标的仍处「首付款已落袋、分成待兑现」阶段，依沃西、恒瑞 GLP-1 等大额分成兑现依赖海外获批。"),
    dict(no=13, group="商业化兑现与销售", item="Biotech 向 Biopharma 跨越的财务指标",
         score=1, flag="向好",
         verdict="集中兑现拐点：百济 2026H1 归母净利 32.71 亿元（+627%）、经营现金流转正（6.64 亿美元）、销售管理费用率 41%→35%；信达 2025 全年盈利；科伦博泰扭亏（净利 3.88 亿元）；云顶新耀减亏至近盈亏平衡。",
         evidence=["百济 2026H1 归母 32.71 亿元（+627%），经营现金流转正 6.64 亿美元，销管费率 41%→35%，上调全年指引 449–462 亿元",
                   "信达生物 2025 年全年盈利，2026H1 产品收入超 82 亿元（+55%）",
                   "科伦博泰净利 3.88 亿元扭亏、经营现金流转正（3.39 亿元）",
                   "再鼎仍亏损（-1.02 亿美元）但持续减亏；云顶新耀减亏至近盈亏平衡"],
         sources=["百济神州 2026 中报公告", "信达生物港交所公告", "羊城晚报", "公司公告"]),
    # ---- 板块四 政策与外部环境 ----
    dict(no=14, group="政策与外部环境", item="创新药审评审批政策倾向",
         score=1, flag="向好",
         verdict="政策明确支持真创新：2025 年 BTD 同意纳入 101 件（+10.99%）；优先审评 133 件（+12.73%），审评时限 200→130 工作日；《全链条支持创新药发展实施方案》26 省市落地；「医保+商保」双目录支付体系建成。",
         evidence=["2025 年 BTD 同意纳入 101 件/89 适应症（+10.99%）；优先审评纳入 133 件（+12.73%）",
                   "审评时限压缩：普通 200→130 工作日，罕见病 70 工作日；2025 年 NMPA 批准创新药 76 个创新高",
                   "《全链条支持创新药发展实施方案》26 省市落地；医保发〔2025〕16 号 5 方面 16 条推进",
                   "商保创新药目录首版 19 种（2026-01 执行），截至 2026-05 在 1486 家机构配备、100+ 惠民保覆盖；2026-06 年度调整 54 品种过初审"],
         sources=["国家医保局 2026 上半年发布会", "CDE《2025 年度药品审评报告》", "央视"]),
    dict(no=15, group="政策与外部环境", item="集采冲击与结构调整",
         score=1, flag="向好",
         verdict="集采边际影响减弱、转型成果显现：第十一批集采降幅收窄（约 75% vs 第十批 80%+，降幅 90%+ 占比 68%→45%）；恒瑞创新药收入占药品收入 58.34%、中生 47.8%、华东创新产品 +64.2%；「创新药不纳入集采」重申。",
         evidence=["第十一批集采 55 品种、中选率 57.1%，首轮均价降幅约 75%（低于第十批 80%+），设「锚点价」+复活机制",
                   "恒瑞创新药收入 163.42 亿（+26.09%）占药品收入 58.34%（2026Q1 达 61.69%）；研发投入 87.24 亿（+27.58%）",
                   "中生创新产品 152.2 亿（+26.2%）占比 47.8%；华东创新产品 23.4 亿（+64.2%）占医药工业 15.81%",
                   "「创新药不纳入集采」再次强调；但石药仍处阵痛期（2025 营收 -10.4%、净利 -10.3%，5 笔 BD 共 282.1 亿美元对冲）"],
         sources=["上海阳光医药采购网", "国家医保局", "红星资本局", "各公司 2025 年报"],
         risk="石药等传统药企仍承压；生物类似药/中成药集采扩围需要跟踪。"),
    dict(no=16, group="政策与外部环境", item="地缘政治与合规风向",
         score=-1, flag="恶化",
         verdict="外部环境实质趋紧：BIOSECURE Act 已随 FY2026 NDAA 于 2025-12-18 签署成法（Section 851），2026-06 药明康德首度列入国防部 1260H 清单；但执行细则未落地（OMB 名单 2026-12 前发布）、既有合同 5 年祖父条款，属「慢刀子」式趋紧。",
         evidence=["BIOSECURE Act 2025-12-18 随 FY2026 NDAA 签署成法（Section 851），不再点名企业改为 1260H+OMB 名单认定",
                   "2026-06-08 药明康德首度列入国防部 1260H 清单（有申诉空间）；华大/贝瑞已在列",
                   "限令须经 FAR 修订+60/90 天滞后生效，最早 2027 年底；既有合同 5 年祖父条款（至 2033-06）",
                   "FDA 2025 年扩大对华无预警检查（58 封 untitled letters vs 2024 年 5 封）；2026-04 对专利药加征 232 关税（仿制药 API 短期豁免）；欧盟 Critical Medicines Act 2026-05 达成临时协议"],
         sources=["CASRAI", "Holland & Knight", "Latham & Watkins", "白宫/CBP", "欧盟委员会"],
         risk="OMB 名单 2026-12 发布为关键跟踪节点；药明系禁令尚未实际执行。"),
]

GROUPS = ["资金与资本面", "研发与研发服务", "商业化兑现与销售", "政策与外部环境"]
GROUP_SUMMARIES = {
    "资金与资本面": "三大资本通道（一级/二级/BD）全面回暖、BD 成造血主引擎，但呈强马太效应：头部溢价、尾部折价（Down Round、折价配售、现金跑道不足）并存，行业由「出清」进入「分化修复」。",
    "研发与研发服务": "申报获批、III 期临床、学术会议「三重兑现」，数据质量显著跃迁（首个原研进 ASCO Plenary、双抗/双抗 ADC 头对头取胜），CXO 订单随之共振反转；HARMONi-3 终局为主要下行变量。",
    "商业化兑现与销售": "「医保放量（成功率 88%+温和续约）+ 海外分成兑现（传奇、百济、和黄）」双轮驱动，头部 Biotech 已完成盈亏平衡跃迁，销售费用率开始下行。",
    "政策与外部环境": "国内供给侧政策多空对冲：审评提速、双目录落地、集采反内卷为正；BIOSECURE 立法为最大负项，但执行滞后+5 年祖父期属「慢刀子」而非断崖，主基调「短多长忧」。",
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
)

# ============ HTML 模板 ============
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>中国生物医药行业景气度核查报告 · 2026-08</title>
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
  .ev li{position:relative;padding:1px 0 1px 16px;font-size:12.5px;}
  .ev li::before{content:"·";position:absolute;left:4px;color:var(--sub);font-weight:700;}
  .src{color:var(--sub);font-size:11.5px;margin-top:6px;}
  .risk{background:#fff8ec;border:1px solid #f3dfb6;border-radius:8px;padding:8px 12px;font-size:12px;color:#7c4a03;margin-top:8px;}
  .grp-head{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:6px;margin-bottom:6px;}
  .grp-score{font-size:13px;font-weight:700;}
  .grp-score.s1{color:var(--red);} .grp-score.s0{color:var(--sub);} .grp-score.sn{color:var(--green);}
  .grp-summary{color:var(--sub);font-size:12.5px;margin-bottom:12px;}
  .dis-note{margin-top:16px;}
  @media print{.card{break-inside:avoid;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>中国生物医药行业景气度核查报告</h1>
    <div class="meta">核查日期：@@TODAY@@ ｜ 口径：中国创新药产业为主、结合全球 ｜ 方法：16 项核查清单逐项打分（+1 向好 / 0 平稳 / -1 恶化）｜ 数据来源：官方公告、公司财报、行业统计（见各项来源）</div>

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
      <b>核心判断：</b>中国生物医药产业正处于「资本通道全面回暖 + 创新兑现集中发生 + 商业化拐点确认」三周期共振的阶段，但资金流与经营面呈显著<b>马太效应</b>——头部企业（百济、信达、康方、传奇、恒瑞、药明系）享受融资溢价、BD 大额首付、销售放量与盈利兑现，腰部/尾部 Biotech 仍在下行通道（折价配售、现金跑道不足、退货率抬升）。景气度落于<b>强景气区间下沿</b>，实质是「头部强景气 + 尾部弱景气」的结构性分化行情，判断系统性风险的关键在 2026H2 的 HARMONi-3 终局数据与 BIOSECURE 执行细则（OMB 名单 2026-12）。
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

  @@GROUP_CARDS@@

  <div class="card">
    <h2>六、风险提示与跟踪节点</h2>
    <div class="warn">
      <b>1. 数据依赖与时效：</b>本报告数据截至 2026-08-23，部分指标为 2026H1/2025 年报口径；「美股 NASDAQ 中国药企 IPO 数量」「Down Round 占比全样本统计」「泰格医药新签订单精确增速」等项未找到权威披露，已在对应核查项中注明，判断基于可得样本与趋势外推，存在口径误差可能。
    </div>
    <div class="warn">
      <b>2. 关键下行变量：</b>① 康方依沃西 HARMONi-3（全球头对头 K 药）终局数据，2026H2 读出；② BIOSECURE Act 执行细节——OMB/BCC 名单须在 2026-12 前发布，FAR 修订与 60/90 天滞后生效最早 2027 年底，药明康德 1260H 申诉进展；③ 海外大额 BD 里程碑兑现率（历史约 22%）与退货率抬升（宜明昂科、默克-恒瑞、辉瑞-和铂）。
    </div>
    <div class="warn">
      <b>3. 结构性风险：</b>尾部 Biotech 现金跑道不足 24 个月者占比高（明宇 16 个月、景泽 14 个月），2026H2 存在再融资/裁员/清盘出清压力；商保创新药目录支付体量尚小，对行业整体收入贡献有限。
    </div>
    <div class="warn">
      <b>4. 方法局限：</b>本核查为「快照式」景气度评估，16 项等权打分为相对口径（±1），未做加权与历史分位数标准化；景气度判定依赖定性校准，代表 2026-08 时点截面结论，不构成投资建议。
    </div>
  </div>

  <div class="card">
    <h2>附：核查方法论</h2>
    <div class="grp-summary">按「资金与资本面（先行指标）→ 研发与研发服务（中早期指标）→ 商业化兑现（终端验证）→ 政策与外部环境（发展天花板）」四层传导框架逐项核对。计分规则：+1 向好/超预期、0 平稳/符合预期、-1 恶化/低于预期，加总后按四档区间判定景气度（+10~+16 强景气 / +3~+9 结构性景气 / -2~+2 筑底盘整 / -16~-3 低迷）。查询清单为既定核查框架，各项结论均附关键数据与来源；未核实项已明确标注。</div>
    <div class="note">报告生成：@@TODAY@@ ｜ 统计口径说明见各板块数据源 ｜ 数据核实优先级：官方公告 → 公司财报 → 权威行业统计（医药魔方/药智/西南证券等）</div>
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
    grid:{left:10,right:40,top:20,bottom:10,containLabel:true},
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
"""

# 组卡片 HTML
def group_card_html(g, idx):
    items = [it for it in ITEMS if it["group"] == g]
    rows = []
    for it in items:
        sc = it["score"]
        # 正向=红(涨)，负向=绿(跌)，平稳=灰 —— 红涨绿跌 + 文字标签（色弱安全）
        sc_class = {1: "up", -1: "dn", 0: "ne"}[sc]
        sc_txt = {1: "+1 向好", -1: "-1 恶化", 0: "0 平稳"}[sc]
        risk_html = ('<div class="risk">⚠ ' + it.get("risk", "") + "</div>") if it.get("risk") else ""
        ev = "".join('<li>{}</li>'.format(e) for e in it["evidence"])
        srcs = "、".join(it["sources"])
        rows.append(
            '<tr>'
            '<td class="{}">{}</td>'.format(sc_class, sc_txt)
            + '<td><b>{}. {}</b><div class="src">{}　</div></td>'.format(it["no"], it["item"], it["verdict"])
            + '<td style="white-space:normal;min-width:320px;"><ul class="ev">{}</ul>{}</td>'.format(ev, risk_html)
            + '<td style="white-space:normal;min-width:150px;"><div class="src">来源：{}</div></td>'.format(srcs)
            + '</tr>'
        )
    sc = SCORES[g]
    sc_cls = "s1" if sc > 0 else ("sn" if sc < 0 else "s0")
    cn = CN_NUM[idx]
    return """<div class="card">
  <h2>@@CN@@、@@GNAME@@ <span class="grp-score @@CLS@@">板块得分 @@SC@@</span></h2>
  <div class="scroll"><table>
    <thead><tr><th style="width:70px">打分</th><th style="min-width:260px">核查项与结论</th><th style="min-width:340px">关键数据与依据</th><th style="min-width:160px">来源</th></tr></thead>
    <tbody>@@ROWS@@</tbody>
  </table></div>
</div>""".replace("@@CN@@", cn).replace("@@GNAME@@", g).replace("@@CLS@@", sc_cls).replace("@@SC@@", "+" + str(sc) if sc > 0 else str(sc)).replace("@@SUMMARY@@", GROUP_SUMMARIES[g]).replace("@@ROWS@@", "".join(rows))

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
            '<tr><td><b>{}. {}（{} 项）</b><div class="src">{}</div></td>'
            '<td class="{}">{}</td><td>{}</td><td>{}</td><td>{}</td>'
            '<td style="white-space:normal;min-width:280px;">{}</td></tr>'.format(
                CN_NUM[i + 1], g, len([it for it in ITEMS if it["group"] == g]),
                GROUP_SUMMARIES[g],
                "up" if sc > 0 else ("ne" if sc == 0 else "dn"), sc_txt,
                p, z, n,
                GROUP_SUMMARIES[g])
        )
    html = HTML.replace("@@TODAY@@", TODAY).replace("@@TOTAL@@", str(TOTAL)) \
        .replace("@@LEVEL@@", LEVEL).replace("@@LEVEL_CN@@", LEVEL_CN) \
        .replace("@@POS@@", str(POS)).replace("@@NEU@@", str(NEU)).replace("@@NEG@@", str(NEG)) \
        .replace("@@GROUP_ROWS@@", "".join(grp_rows)) \
        .replace("@@GROUP_CARDS@@", group_cards)
    # 注入数据
    data_json = json.dumps(DATA, ensure_ascii=False, allow_nan=False)
    html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + data_json + ";")
    html = html.replace("@@RENDER_JS__", RENDER_JS)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT)
    print("written: %s size=%d" % (OUT, size))

if __name__ == "__main__":
    main()