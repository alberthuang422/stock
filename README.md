# 📊 美股研究 · 报告索引

> 本工作区全部研究报告的统一检索入口（报告存放在 `reports/` 目录）
> 最后更新：2026-09-05 ｜ 编号报告 79 / 有效 HTML 112（15 份已归档）｜ 归档区：`reports/_archive_202609/`
>
> **📑 目录**：<a href="#sec1">1️⃣ 量化回测</a> ｜ <a href="#sec2">2️⃣ 相关性</a> ｜ <a href="#sec3">3️⃣ 宏观利率</a> ｜ <a href="#sec4">4️⃣ 景气/资金流</a> ｜ <a href="#sec5">5️⃣ 个股基本面</a> ｜ <a href="#sec6">6️⃣ 市场与情绪</a> ｜ <a href="#sec7">7️⃣ 农业/CFTC</a> ｜ <a href="#secA">按标的检索</a> ｜ <a href="#secArch">📦 归档区</a>

---

## 🆕 最近报告

| 报告 | 内容 |
|------|------|
| [79 CFTC 农产品持仓 32 年（1995-2026）](reports/79_CFTC农产品持仓32年_1995_2026/index.html) | 24 品种非商/商业多空 × 32 年全历史 |
| [78 银行弱势传导合集（原 14/15/16）](reports/78_银行弱势传导合集_KBWB/index.html) | KBWB 走弱 → 科技/医药/资管三板块传导 |
| [77 MCD RSI 低吸系列合集（原 46-49）](reports/77_MCD_RSI低吸系列合集/index.html) | RSI 低吸四方法迭代汇总 |
| [76 中期选举窗口波动率合集（原 37/38/42）](reports/76_中期选举窗口波动率合集/index.html) | SPX / 板块 / VIX 三视角事件研究 |
| [72 CFTC 农产品持仓 09-01](reports/72_CFTC农产品持仓_20260901/index.html) | 23 农产品市场非商业持仓 × 历史分位 |
| [70v2 震荡市个股突破 v2](reports/70_震荡市个股突破延续性_v2/index.html) | 严格口径震荡检测 × 首破回测（v1 结论未复现） |

---

## 🗂 分类总览

| 分类 | 核心内容 | 代表报告 |
|------|----------|----------|
| **1️⃣ 量化回测与择时** | MACD / 突破 / 支撑位 / RSI 低吸 / 事件统计 | 01、10-14、17、18、31-36、39-41、44、45、50、52、60、64、70v2、76、77 |
| **2️⃣ 相关性分析** | 板块 / 个股 / ETF 联动关系 | 02、03、05、19、23、24、27、32、35、37、38、43、51、53、63、69、78 |
| **3️⃣ 宏观利率与资产联动** | 曲线形态 → 板块 / 利率敏感性 | 06、08、09、30、54、55、61 |
| **4️⃣ 行业景气度与资金流** | 景气核查、业绩传导、机构持仓 | 21、22、25、26、13F |
| **5️⃣ 个股基本面研究** | 医药 / 消费 / 交运 / 金融科技 / 电力 | 27、28、29、62、67、71 |
| **6️⃣ 市场结构与情绪** | VIX、期权结构、异动归因、热度榜 | 07、20、66、hot 系列 |
| **7️⃣ 农业大宗与 CFTC 持仓** | ENSO / 化肥 / 谷物归因 / 持仓分位 | 57-59、68、72、79 |

---

<a id="sec1"></a>
## 1️⃣ 量化回测与择时

### 震荡市 × 突破
- **[震荡市个股突破延续性 v2（重做版）](reports/70_震荡市个股突破延续性_v2/index.html)** · 三支柱震荡识别 × 55日 Donchian 首破回测；严格口径下 v1 结论未复现（70 v2）
- ~~70 v1（初版口径）~~ **已归档**（[v1 原文](reports/_archive_202609/70_震荡市个股突破延续性_v1/index.html)，结论被 v2 否定，仅作对照）
- **[震荡市板块独立行情回测](reports/45_震荡市板块独立行情/index.html)** · 震荡市中板块独立趋势的统计识别

### MACD 系列
- **[MACD 水下金叉回测报告](reports/01_MACD回测/MACD水下金叉回测报告.html)** · 水下金叉买点信号的回测验证
- **[多股票回测对比报告](reports/01_MACD回测/多股票回测对比报告.html)** · 多标的横向对比（AMZN/BRK.B/GE/GS/JNJ/MS/NVDA/SPY/UNH 个股回测同目录）
- **[公用事业 MACD 水下金叉回测](reports/18_公用事业MACD水下金叉回测/公用事业MACD水下金叉回测报告.html)** · 同一策略在公用事业板块的验证
- **[60 日线 MACD 死叉 × 4h RSI 超卖 买入回测](reports/60_MACD死叉_4hRSI超卖_胜率回测/index.html)** · 死叉 + 4h RSI 共振买多的胜率与显著性（60 号）

### 突破与支撑
- **[GILD / ABBV 突破回踩](reports/11_gild突破回踩/gild_abbv_breakout_report.html)** · 突破买点与回踩确认分析
- **[支撑 / 阻力位 AI 识别 Demo](reports/13_kbwb支撑位/support_levels_ms_demo.html)** · 支撑位识别方法（MS 示例）
- **[下降趋势线突破识别方法](reports/13_kbwb支撑位/trendline_breakout_report.html)** · AI 识别趋势线突破的方法与证据
- **[月线 EMA20 支撑位买入回测](reports/月线EMA20支撑位买入_回测报告.html)** · 月线级别支撑位买入回测
- **[蓝筹区间下沿支撑 × 周线EMA20压制（三组对照）](reports/31_蓝筹区间下沿支撑_周线EMA20压制回测/index.html)** · 周线EMA20压制下的支撑触达事件回测
- **[周线 MACD 能量柱收敛 × 支撑位（蓝筹）](reports/33_周线MACD收敛支撑位回测/index.html)** · 按 MACD 柱状态分组的支撑位回测
- **[周线高位死叉 × 回踩 EMA20 支撑（蓝筹）](reports/36_高位死叉回踩EMA20支撑/index.html)** · 高位死叉后回踩 EMA20 的回测
- **[道指板块支撑](reports/13_道指板块支撑/djia_sector_support_report.html)** · 道指板块支撑位放量 / 平量对比
- **[ETF 弱势支撑](reports/14_ETF弱势支撑/etf_weak_support_report.html)** · ETF 弱势位支撑分析
- **[蓝筹贴 EMA20 缩量跌破平台](reports/44_贴EMA20缩量跌破平台/index.html)** · 缩量跌破平台的回测

### RSI 低吸系列
- **[蓝筹 RSI 低吸系列](reports/39_蓝筹RSI超卖买入/index.html)**（[39 超卖&lt;30](reports/39_蓝筹RSI超卖买入/index.html) / [40 动态支撑](reports/40_蓝筹RSI支撑位买入/index.html) / [41 swing low 聚集](reports/41_蓝筹RSI摆动低点支撑买入/index.html)）· 72 蓝筹 RSI 低位买入三口径回测
- **[纳指区间 RSI 低买高卖（修正版）](reports/50_纳指区间RSI低买高卖/index.html)** · 纳指横盘期 RSI 低买高卖配对回测
- **[77 合集 · MCD RSI 低吸方法族（原 46-49）](reports/77_MCD_RSI低吸系列合集/index.html)** · 摆动低点 → 下穿40分档 → 窗口质量 ER → 越跌越买，四次方法迭代汇总（原文归档 _archive_202609）
- **[DAL 达美航空 · RSI 区间跌落买入（越跌越买）](reports/64_DAL_RSI档位买入/index.html)** · 三档分档买入回测、深度回撤过滤、当前 RSI 位置（64 号）
- ~~CCL RSI 档位买入（56 号）~~ **已归档**（[原文](reports/_archive_202609/56_CCL_RSI档位买入/index.html)；回测内容已并入 [62 号全面分析](reports/62_CCL全面分析/index.html) 第六章）

### 超买与事件统计
- **[涨 3% 事件研究](reports/10_涨3%事件/3pct_event_report.html)** · 单日大涨后的统计规律
- **[周线超买](reports/12_周线超买/weekline_ob_report.html)** · 周线超买信号有效性检验
- **[KO RSI 超买](reports/17_KO超买/ko_rsi_overbought_report.html)** · KO 的 RSI 超买信号回测
- **[道指板块超买横向](reports/34_道指板块超买横向/djia_ob_cross_report.html)** · 9 板块代表股 RSI 超买横比
- **[76 合集 · 中期选举窗口波动率（原 37/38/42）](reports/76_中期选举窗口波动率合集/index.html)** · 同一事件窗口三视角：SPX 波动 / 板块横比 / VIX 前抬升（原文归档 _archive_202609）
- **[持仓组合技术面与操作建议](reports/52_持仓组合技术面与操作建议/index.html)** · 8 标的组合逐股技术面拆解

---

<a id="sec2"></a>
## 2️⃣ 相关性分析

### 医药板块内部
- **[GILD × XLV/IBB 系列](reports/02_gild_xlv_ibb相关性板块分析/ibb_gild_corr_report.html)**（8 份报告，建议从主报告看起）：
  - [IBB × GILD 相关性](reports/02_gild_xlv_ibb相关性板块分析/ibb_gild_corr_report.html)（相关度分析）
  - [IBB × AMGN / VRTX](reports/02_gild_xlv_ibb相关性板块分析/ibb_amgn_vrtx_report.html)、[AMGN × VRTX](reports/02_gild_xlv_ibb相关性板块分析/amgn_vrtx_corr_report.html)
  - [IBB 前十大权重](reports/02_gild_xlv_ibb相关性板块分析/ibb_top10_report.html)
  - [GILD 财报窗口反应](reports/02_gild_xlv_ibb相关性板块分析/gild_earnings_window_report.html)、[Q4 财报窗口](reports/02_gild_xlv_ibb相关性板块分析/gild_q4_earnings_window_report.html)
  - [GILD × ETF 对比](reports/02_gild_xlv_ibb相关性板块分析/gild_etf_compare_report.html)、[VIX 冲击影响](reports/02_gild_xlv_ibb相关性板块分析/vix_impact_report.html)
- **[药明康德 vs 美国药企](reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_bigpharma_report.html)** · 药明康德与美大药企相关性（[药明财务联动](reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_financial_link_report.html)）
- **[ABBV × IBB/IHE 相关性](reports/43_ABBV_IBB_IHE_相关性/index.html)** · ABBV 与制药/生物科技指数相关性

### 子板块 / 跨板块
- **[IHI × XBI 器械 vs 生物科技](reports/23_ihi_xbi器械vs生物科技/index.html)** · 器械与生物科技板块相关性拆解
- ~~IHI × XBI（13 日滚动重做版，26 号）~~ **已归档**（[原文](reports/_archive_202609/26_ihi_xbi_13日滚动相关/index.html)）；13 日口径已被项目铁律否决，主报告见 [23 号](reports/23_ihi_xbi器械vs生物科技/index.html)
- **[工具四龙头 × IBB/XBI](reports/24_工具龙头_ibb_xbi相关性/index.html)** · 工具龙头与医药板块相关性拆解
- **[CSCO × BUG 网络安全](reports/19_csco_bug网络安全/csco_bug_corr_report.html)** · CSCO 与网络安全板块相关性
- **[CSCO × PANW/CRWD 相关性与脱钩](reports/35_网安vs网络设备/index.html)** · CSCO 与网安个股的相关性拆解
- **[CSCO × 纳指/道指 相关性](reports/38_思科纳指道指相关性/index.html)** · CSCO 与两大指数的相关性拆解
- **[银行卡网络 V/MA](reports/27_银行卡网络_银行科技相关性/visa_master_corr_report.html)** · 支付网络 vs 银行/科技板块
- **[KBWB × MS](reports/13_kbwb支撑位/kbwb_ms_corr_report.html)** · 银行板块 ETF 与投行巨头相关性
- **[78 合集 · 银行走弱 → 板块传导（原 14/15/16）](reports/78_银行弱势传导合集_KBWB/index.html)** · KBWB 走弱信号 × 科技/医药/资管三板块条件相关与前瞻收益（原文归档 _archive_202609）
- **[KO × 科技/制药/医疗保健 相关性](reports/32_ko_科技医药相关性/index.html)** · KO 与三大板块分阶段拆解
- **[KO vs XLV × 道琼斯](reports/37_ko_xlv_dji相关性/index.html)** · KO/XLV 与道指的相关性对比
- **[MCD / SBUX × 道琼斯 / XLY 相关性](reports/51_MCD_SBUX_DJI_XLY_相关性/index.html)** · 两消费股与道指/XLY 的 2×2 相关性
- **[VST × UTES 分阶段演化](reports/05_vst_utes阶段分析/vst_utes_phase_report.html)** · VST 与 UTES 相关性的阶段演化
- **[SOFI / XYZ × 比特币 季度分阶段相关性](reports/50_SOFI_BTC_相关性季度分阶段/index.html)** · SOFI/XYZ 与比特币季度分阶段相关
- **[SOFI / AFRM / UPST 财报交易日涨跌相关性](reports/53_金融科技财报日相关性/index.html)** · 金融科技三股财报日相关性事件研究
- **[SOFI × AFRM × Block(SQ) 相关性（选举后窗口）](reports/63_SOFI_AFRM_SQ相关性分析/index.html)** · 选举后窗口三股相关性 + 60 日滚动（63 号）
- **[UNP × US10Y/QQQ/SOXX/道指 分阶段相关性](reports/69_UNP多基准分阶段相关性/index.html)** · 合并公告 / STB 受理双断点分阶段拆解（69 号）

---

<a id="sec3"></a>
## 3️⃣ 宏观利率与资产联动

收益率曲线形态 → 板块表现；全球利率环境 → 长久期资产

- **[陡峭化 × 消费股](reports/06_陡峭化消费股/steep_ko_pm_mo_report.html)** · 陡峭化对消费龙头（KO/PM/MO）的敏感性
- **[银行 × 曲线陡峭化](reports/08_银行陡峭化/banks_steep_report.html)** · 银行股与曲线陡峭化关系分析
- **[银行熊陡](reports/09_银行熊陡/banks_bear_steep_report.html)** · 熊陡形态下银行表现
- **[资管 × 曲线陡峭化](reports/30_资管陡峭化/index.html)** · 资管股对曲线陡峭化的敏感性
- **[宏观利率背景 × 六股影响](reports/54_宏观利率背景六股影响/index.html)** · 利差变动下六股的利率敏感度分析
- **[宏观背景（常设背景文件）](reports/55_宏观背景/index.html)** · 蓝筹池索引、利差与宏观事件更新
- **[20260829 利率上行 × 板块全景（md）](reports/55_宏观背景/20260829_利率上行板块全景.md)** · 当日讨论固化：利率传导与板块影响
- **[全球 10Y 国债收益率风险](reports/global-bond-yields-risk-20260817.html)** · 收益率创高全景与风险分层评估
- **[Apollo 全球资管深度研究](reports/61_Apollo全球资管深度研究.html)** · APO 量价周期、财务估值、同行对比、驱动拆解

---

<a id="sec4"></a>
## 4️⃣ 行业景气度与资金流

- **[生物医药行业景气度](reports/21_生物医药行业景气度/index.html)** · 大药企 16 项景气指标核查
- **[小型生物科技（XBI）景气度](reports/22_小型生物科技景气度/index.html)** · 小 biotech 专用景气指标核查
- **[千亿美元药企专利悬崖](reports/26_千亿美元药企专利悬崖/index.html)** · 15 家巨头专利悬崖与管线接力
- **[biotech 景气 → 工具业绩传导时滞](reports/25_工具业绩传导时滞/index.html)** · 融资行情到订单收入的传导链条
- **[2026 Q2 13F 全量资金流](reports/13f_q2_2026_sector_flow.html)** · 全行业加仓 / 减持全景

---

<a id="sec5"></a>
## 5️⃣ 个股基本面研究

### 🏥 医药健康
- **[诺华 NVS 全面研究](reports/27_nvs诺华深度研究/index.html)** · 基本面与专利悬崖应对
- **[艾伯维 ABBV 全面研究](reports/28_abbv艾伯维深度研究/index.html)** · 基本面与大单品切换
- **[DHR vs TMO 生物科技卖铲人对比](reports/DHR_vs_TMO_生物科技卖铲人对比.html)** · 生命科学工具龙头基本面对比

### 🛒 消费 / 出行
- **[星巴克 SBUX 基本面分析](reports/29_sbux基本面分析/sbux基本面分析-20260824.html)** · 2026-08 全面基本面
- ~~SBUX 财报与估值研究（07 号早期版）~~ **已归档**（[原文](reports/_archive_202609/07_sbux星巴克/sbux_report.html)，已被上方 29 号全面版覆盖）
- **[KO vs PEP 相对强弱](reports/28_ko_vs_pep_相对强弱研究.html)** · KO 与百事相对强弱拆解
- **[PG 宝洁深度分析](reports/67_PG宝洁深度分析/index.html)** · FY2026 财报、问题分层、估值同业对比（67 号）
- **[UNP 联合太平洋基本面深度分析](reports/71_UNP基本面深度分析/index.html)** · SEC XBRL 财务拆解、UP-NS 合并三情景、估值对比（71 号）
- **[CCL 嘉年华邮轮 · 全面分析](reports/62_CCL全面分析/index.html)** · 基本面 × 估值 × 量化回测 × 行业 × 风险（62 号，含 56 号 RSI 回测沉淀）

### 💳 金融科技
- **[SOFI × Block × AFRM](reports/sofi_xyz_afrm_report.html)** · 财报对比与 US10Y 敏感性

### ⚡ 电力 / 公用事业
- **[CEG vs VST 电力双雄](reports/04_ceg_vst电力股对比/ceg_vst_compare_report.html)** · CEG 与 VST 双雄对比分析

---

<a id="sec6"></a>
## 6️⃣ 市场结构与情绪

- **[IPP 大跌归因](reports/07_ipp大跌归因/ipp_drop_0818_report.html)** · 8/18 IPP 大跌归因
- **[VIX 低位分析](reports/vix_low_spx_report.html)** · VIX 低位下 SPX 后续与持续性
- **[VIX 低位 × SPY 事件研究](reports/vix_low_spy_dashboard/index.html)** · VIX 低位日的 SPY 事件研究
- **[66 CVS × VIX>18 高波动期表现](reports/66_CVS与VIX高波动期表现/index.html)** · VIX>18 状态分桶、恐慌冲击日与持续高波动段拆解
- **[期权墙八标的](reports/20_期权墙八标的/index.html)** · 2026-09-18 到期期权持仓结构分析
- **[富途热门股 Top500 过滤版](reports/hot_us_stocks_top500_filtered_20260901.html)** · 热度榜剔除 &gt;500$/中概/ADR 后 354 只明细
- **[热门股池 RSI 评估](reports/hot354_rsi_eval_20260901.html)** · 354 只 RSI14 分布、超买超卖分层、17 板块交叉透视

---

<a id="sec7"></a>
## 7️⃣ 农业大宗与 CFTC 持仓

### ENSO 与化肥股
- **[57 农业股 × ENSO 回测 + 利率敏感性](reports/57_农业股ENSO与利率敏感性/index.html)** · 化肥股对拉尼娜/厄尔尼诺的事件回测
- **[57附 绝对收益版](reports/57_农业股ENSO与利率敏感性/绝对收益版.html)** · ENSO 回测的绝对收益口径重算
- **[58 农业股（CF/DAR）地缘溢价脱钩监测](reports/58_农业股地缘溢价脱钩监测/index.html)** · CF/DAR 与油价相关性的脱钩监测
- **[59 MOS vs CF 走势分化](reports/59_MOS与CF化肥走势分化/index.html)** · 同为化肥股走势分化的归因

### 谷物暴涨与 CFTC 持仓
- **[68 谷物暴涨归因调查（08-24~28 周）](reports/68_谷物暴涨归因调查_20260903/index.html)** · 小麦/玉米/大豆分品种主因拆解 + 37 条出处逐条可溯源 + 库存专题
- **[72 CFTC 农产品持仓（09-01）](reports/72_CFTC农产品持仓_20260901/index.html)** · 23 农产品市场非商业/商业/非报告持仓 × 2010 年以来历史分位
- **[79 CFTC 农产品持仓 32 年全史（1995-2026）](reports/79_CFTC农产品持仓32年_1995_2026/index.html)** · 非商/商业多空 + 周变动 + 净多/净空 × 32 年（1643 周）全历史曲线与极值分位

---

<a id="secA"></a>
## 🔍 按标的检索（跨分类串联）

同标的研究常横跨量化/相关性/基本面多条线，下表把主要标的的散落报告串起来（按需点开，非重复研究）：

| 标的 | 涉及报告 |
|------|----------|
| **KO 可口可乐** | 06（陡峭化）· 17（超买）· 28（基本面 vs PEP）· 32（×科技医药）· 37（×XLV/道指） |
| **CSCO 思科** | 19（×BUG 网安）· 35（×PANW/CRWD）· 38（×纳指/道指） |
| **SOFI 系** | 顶层 sofi_xyz_afrm（财报+US10Y）· 50（×BTC）· 53（财报日）· 63（×AFRM/SQ） |
| **MCD 麦当劳** | 77 合集（46-49 RSI 低吸族）· 51（×道指/XLY） |
| **GILD 吉利德** | 02（×IBB/XLV/财报窗）· 10（涨3%）· 11（突破回踩）· 12（周线超买） |
| **ABBV 艾伯维** | 11（突破）· 28（基本面深度）· 43（×IBB/IHE） |
| **UNP 联合太平洋** | 69（×四基准相关）→ 71（基本面深度） |
| **CCL 嘉年华** | 62 全面（含 56 号 RSI 沉淀）；64 DAL 为行业可比 |
| **NVS / PG / SBUX / CVS / DAL** | 27 / 67 / 29 / 66 / 64（各单点深度） |
| **CF/DAR/MOS 农业股** | 57（ENSO）· 58（脱钩）· 59（分化）· 68/72/79（谷物+CFTC） |
| **工具链 A/DHR/TMO/WAT** | 23（IHI×XBI）· 24（×IBB/XBI）· 25（业绩时滞）· DHR_vs_TMO（基本面） |
| **电力 IPP：CEG/VST/UTES/TLN** | 04（CEG vs VST）· 05（VST×UTES）· 07（8/18 大跌归因）· 18（公用事业 MACD） |

---

<a id="secArch"></a>
## 📦 归档区（reports/_archive_202609/，2026-09-05 治理）

> 归档 ≠ 删除：内容与 git 历史完整保留，链接仍可打开对照。归档对象 = **被吸收 / 被替代 / 冗余**的报告。
> 治理方案与全量盘点明细见 [00_报告治理_20260905](reports/00_报告治理_20260905/index.html)

| 归档单元 | 原因 | 替代入口 |
|----------|------|----------|
| 56 CCL RSI 档位买入 | 回测被 62 号第六章完整吸收 | 62 号 |
| 07_sbux 星巴克早期版 | 被 29 号全面版覆盖 | 29 号 |
| 70 v1 震荡市突破 | 结论被 v2 严格口径否定 | 70 v2 |
| 26 IHI×XBI 13日滚动 | 13 日口径被铁律否决（60 日为主） | 23 号 |
| hot_us_stocks_top300（09-01） | 同日被 Top500 过滤版替代 | hot354 / 500 版 |
| 46/47/48/49 MCD RSI 四连 | 已并入合集 | 77 合集 |
| 37/38/42 中期选举三份 | 已并入合集 | 76 合集 |
| 14/15/16 KBWB 弱势三份 | 已并入合集 | 78 合集 |

---

## 📝 维护说明

- **新增报告后请同步更新本文件**：在对应分类下追加一行 = 标题（含编号）+ 相对链接 + **一句话简介（≤25 字，只讲分析对象与方法，结论与数据留在报告内）**；新报告同步登记到顶部「🆕 最近报告」
- 报告目录命名规范：`编号_中文名`（如 `30_资管陡峭化`）
- 编号冲突（如 13、27、28、37、38、50 出现两个目录）为历史遗留，以目录内中文名区分
- 深度研究类报告（21+）统一使用 `index.html` 作为入口
- **治理惯例（2026-09-05 起）**：多篇同族迭代报告 → 先并入新编号合集（76+），原文移入 `_archive_202609/`；合集页以「导览 + Tab iframe 原文」结构，不重写原文内容
