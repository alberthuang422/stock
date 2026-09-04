# 📊 美股研究 · 报告索引

> 本工作区全部研究报告的统一检索入口（报告存放在 `reports/` 目录）
> 最后更新：2026-09-03 ｜ 覆盖报告：88 份 HTML

---

## 🗂 分类总览

| 分类 | 核心内容 | 代表报告 |
|------|----------|----------|
| **1. 量化策略与回测** | MACD / 突破回踩 / 支撑位 / 超买 | 01、10、11、13、14~18 |
| **2. 相关性分析** | 板块 / 个股 / ETF 联动关系 | 02、05、19、23、24、26、27、37、38、43、50、51 |
| **3. 宏观利率与资产联动** | 曲线陡峭化对板块影响、利率风险 | 06、08、09、30 |
| **4. 行业景气度与资金流** | 景气核查、业绩传导、机构持仓 | 21、22、25、26、13F |
| **5. 个股基本面研究** | 深度研究（医药 / 消费 / 金融科技 / 电力） | 27、28、29、30 之前系列 |
| **6. 市场结构与情绪** | VIX、期权结构、异动归因 | 07、20 |

---

## 1️⃣ 量化策略与回测

技术择时 / 买点信号 / 回测验证

### MACD 水下金叉系列
- **[MACD 水下金叉回测报告](reports/01_MACD回测/MACD水下金叉回测报告.html)** · 水下金叉买点信号的回测验证
- **[多股票回测对比报告](reports/01_MACD回测/多股票回测对比报告.html)** · 多标的横向对比
- 个股回测（AMZN / BRK.B / GE / GS / JNJ / MS / NVDA / SPY / UNH）在同目录下
- **[公用事业 MACD 水下金叉回测](reports/18_公用事业MACD水下金叉回测/公用事业MACD水下金叉回测报告.html)** · 同一策略在公用事业板块的验证

### 突破与支撑
- **[GILD / ABBV 突破回踩](reports/11_gild突破回踩/gild_abbv_breakout_report.html)** · 突破买点与回踩确认分析
- **[支撑 / 阻力位 AI 识别 Demo](reports/13_kbwb支撑位/support_levels_ms_demo.html)** · 支撑位识别方法（MS 示例）
- **[下降趋势线突破识别方法](reports/13_kbwb支撑位/trendline_breakout_report.html)** · AI 识别趋势线突破的方法与证据
- **[月线 EMA20 支撑位买入回测](reports/月线EMA20支撑位买入_回测报告.html)** · 月线级别支撑位买入回测
- **[蓝筹区间下沿支撑 × 周线EMA20压制（三组对照）](reports/31_蓝筹区间下沿支撑_周线EMA20压制回测/index.html)** · 周线EMA20压制下支撑触达事件回测
- **[周线MACD能量柱收敛 × 支撑位（蓝筹）](reports/33_周线MACD收敛支撑位回测/index.html)** · 按MACD柱状态分组的支撑位回测
- **[周线高位死叉 × 回踩EMA20支撑（蓝筹）](reports/36_高位死叉回踩EMA20支撑/index.html)** · 高位死叉后回踩EMA20的回测

### 支撑 / 弱势板块研究
- **[道指板块支撑](reports/13_道指板块支撑/djia_sector_support_report.html)** · 道指板块支撑位放量/平量对比
- **[ETF 弱势支撑](reports/14_ETF弱势支撑/etf_weak_support_report.html)** · ETF 弱势位支撑分析
- **[KBWB 科技弱势](reports/14_kbwb科技弱势/kbwb_tech_weakness_report.html)** · 银行板块 ETF 中的科技弱项
- **[KBWB 医药弱势](reports/15_kbwb医药弱势/kbwb_med_weakness_report.html)** · 银行板块 ETF 中的医药弱项
- **[KBWB AM 弱势](reports/16_kbwbAM弱势/kbwb_am_weakness_report.html)** · 银行板块 ETF 中的资管弱项

### 超买与事件统计
- **[周线超买](reports/12_周线超买/weekline_ob_report.html)** · 周线超买信号有效性的检验
- **[KO RSI 超买](reports/17_KO超买/ko_rsi_overbought_report.html)** · KO 的 RSI 超买信号回测
- **[道指板块超买横向](reports/34_道指板块超买横向/djia_ob_cross_report.html)** · 9 板块代表股 RSI 超买横比
- **[涨 3% 事件研究](reports/10_涨3%事件/3pct_event_report.html)** · 单日大涨后的统计规律
- **[中期选举前标普500波动率](reports/37_中期选举波动率/index.html)** · 中期选举窗口的波动率事件研究
- **[中期选举前标普板块波动率](reports/38_板块中期选举波动率/index.html)** · 各板块选举窗口波动率对比
- **[蓝筹 RSI 超卖买入](reports/39_蓝筹RSI超卖买入/index.html)** · 蓝筹 RSI 下穿30买入回测
- **[蓝筹 RSI 动态支撑位买入](reports/40_蓝筹RSI支撑位买入/index.html)** · RSI 动态支撑位附近买入回测
- **[蓝筹 RSI 摆动低点(swing low)聚集支撑买入](reports/41_蓝筹RSI摆动低点支撑买入/index.html)** · RSI 摆动低点聚集支撑的回测
- **[VIX 中期选举前抬升](reports/42_VIX中期选举抬升/index.html)** · VIX 在中期选举前的走势事件研究
- **[蓝筹贴EMA20缩量跌破平台](reports/44_贴EMA20缩量跌破平台/index.html)** · 贴EMA20缩量跌破平台的回测
- **[震荡市板块独立行情回测](reports/45_震荡市板块独立行情/index.html)** · 震荡市中板块独立趋势的统计识别
- **[MCD 单股 RSI 摆动低点支撑买入](reports/46_MCD_RSI摆动低点支撑买入/index.html)** · MCD 的 RSI 摆动低点信号回测
- **[MCD 单股 RSI 低位买入·RSI 分档](reports/47_MCD_RSI低位分档买入/index.html)** · MCD RSI 低位分档买入回测
- **[MCD RSI 低位窗口质量（maxGain + ER）](reports/48_MCD_RSI低位窗口质量/index.html)** · MCD 低位窗口反弹质量指标分析
- **[MCD RSI 区间跌落买入（越跌越买）](reports/49_MCD_RSI区间跌落买入/index.html)** · MCD 依 RSI 档位跌落的连续加仓回测
- **[纳指区间 RSI 低买高卖（修正版）](reports/50_纳指区间RSI低买高卖/index.html)** · 纳指横盘期 RSI 低买高卖配对回测
- **[CCL 嘉年华邮轮 · RSI 区间跌落买入（越跌越买）](reports/56_CCL_RSI档位买入/index.html)** · CCL 依 RSI 档位跌落的买入回测
- **[CCL 嘉年华邮轮 · 全面分析](reports/62_CCL全面分析/index.html)** · 基本面 × 估值 × 技术面 × 量化回测 × 行业 × 风险（62 号）
- **[DAL 达美航空 · RSI 区间跌落买入（越跌越买）](reports/64_DAL_RSI档位买入/index.html)** · 三档 332 次买入超额全 ≤0（−0.05/−0.93/−0.82pp），与 CCL 相反无超卖 α；本轮牛市三档全负、30-35 档胜率 26.3%；仅 dd250≤−35% + RSI<26 有 edge；d2m≤3"反弹快"=下跌中继（胜率 0%）；当前 RSI 29.5 触发 <30 但历史不支持买入（64 号）
- **[持仓组合技术面与操作建议](reports/52_持仓组合技术面与操作建议/index.html)** · 8 标的组合逐股技术面拆解

---

## 2️⃣ 相关性分析

板块 / 个股 / ETF 之间的联动关系拆解

### 医药板块内部
- **[GILD × XLV/IBB 系列](reports/02_gild_xlv_ibb相关性板块分析/ibb_gild_corr_report.html)**（8 份报告，建议从主报告看起）：
  - [IBB × GILD 相关性](reports/02_gild_xlv_ibb相关性板块分析/ibb_gild_corr_report.html)（相关度分析）
  - [IBB × AMGN / VRTX](reports/02_gild_xlv_ibb相关性板块分析/ibb_amgn_vrtx_report.html)、[AMGN × VRTX](reports/02_gild_xlv_ibb相关性板块分析/amgn_vrtx_corr_report.html)
  - [IBB 前十大权重](reports/02_gild_xlv_ibb相关性板块分析/ibb_top10_report.html)
  - [GILD 财报窗口反应](reports/02_gild_xlv_ibb相关性板块分析/gild_earnings_window_report.html)、[Q4 财报窗口](reports/02_gild_xlv_ibb相关性板块分析/gild_q4_earnings_window_report.html)
  - [GILD × ETF 对比](reports/02_gild_xlv_ibb相关性板块分析/gild_etf_compare_report.html)、[VIX 冲击影响](reports/02_gild_xlv_ibb相关性板块分析/vix_impact_report.html)
- **[药明康德 vs 美国药企](reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_bigpharma_report.html)** · 药明康德与美大药企相关性分析
  - [药明财务联动](reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_financial_link_report.html)
- **[CSCO × BUG 网络安全](reports/19_csco_bug网络安全/csco_bug_corr_report.html)** · CSCO 与网络安全板块相关性

### 子板块 / 跨板块
- **[IHI × XBI 器械 vs 生物科技](reports/23_ihi_xbi器械vs生物科技/index.html)** · 器械与生物科技板块相关性拆解
- **[IHI × XBI（13 日滚动重做版）](reports/26_ihi_xbi_13日滚动相关/index.html)** · 13 日窗口重做（辅助口径）
- **[工具四龙头 × IBB/XBI](reports/24_工具龙头_ibb_xbi相关性/index.html)** · 工具龙头与医药板块相关性拆解
- **[银行卡网络 V/MA](reports/27_银行卡网络_银行科技相关性/visa_master_corr_report.html)** · 支付网络 vs 银行/科技板块相关性拆解
- **[KBWB × MS](reports/13_kbwb支撑位/kbwb_ms_corr_report.html)** · 银行板块 ETF 与投行巨头相关性
- **[VST × UTES 分阶段演化](reports/05_vst_utes阶段分析/vst_utes_phase_report.html)** · VST 与 UTES 相关性的阶段演化
- **[KO × 科技/制药/医疗保健 相关性](reports/32_ko_科技医药相关性/index.html)** · KO 与三大板块相关性的分阶段拆解
- **[KO vs XLV × 道琼斯](reports/37_ko_xlv_dji相关性/index.html)** · KO/XLV 与道指的相关性对比
- **[CSCO × PANW/CRWD 相关性与脱钩](reports/31_网安vs网络设备/index.html)** · CSCO 与网安个股的相关性拆解
- **[CSCO × 纳指/道指 相关性](reports/38_思科纳指道指相关性/index.html)** · CSCO 与两大指数的相关性拆解
- **[ABBV × IBB/IHE 相关性](reports/43_ABBV_IBB_IHE_相关性/index.html)** · ABBV 与制药/生物科技指数相关性
- **[SOFI / XYZ × 比特币 季度分阶段相关性](reports/50_SOFI_BTC_相关性季度分阶段/index.html)** · SOFI/XYZ 与比特币季度分阶段相关性
- **[MCD / SBUX × 道琼斯 / XLY 相关性](reports/51_MCD_SBUX_DJI_XLY_相关性/index.html)** · 两消费股与道指/XLY 的 2×2 相关性
- **[SOFI / AFRM / UPST 财报交易日涨跌相关性](reports/53_金融科技财报日相关性/index.html)** · 金融科技三股财报日相关性事件研究
- **[SOFI × AFRM × Block(SQ) 相关性（选举后窗口）](reports/63_SOFI_AFRM_SQ相关性分析/index.html)** · 特朗普当选前1个月至今：全期 r=0.51~0.64 中高相关，60日滚动 0.19~0.91 大幅摆动，近3月收拢（AFRM×Block 0.789）
- **[UNP × US10Y/QQQ/SOXX/道指 分阶段相关性](reports/69_UNP多基准分阶段相关性/index.html)** · 联合太平洋对四基准的分阶段拆解（合并公告/STB 受理双断点）、方向拆解与超额归因

---

## 3️⃣ 宏观利率与资产联动

收益率曲线形态 → 板块表现

- **[银行 × 曲线陡峭化](reports/08_银行陡峭化/banks_steep_report.html)** · 银行股与曲线陡峭化关系分析
- **[银行熊陡](reports/09_银行熊陡/banks_bear_steep_report.html)** · 熊陡形态下银行表现
- **[陡峭化 × 消费股](reports/06_陡峭化消费股/steep_ko_pm_mo_report.html)** · 陡峭化对消费龙头的敏感性分析
- **[资管 × 曲线陡峭化](reports/30_资管陡峭化/index.html)** · 资管股对曲线陡峭化的敏感性
- **[Apollo 全球资管深度研究](reports/61_Apollo全球资管深度研究.html)** · APO 全周期量价、财务与估值、同行对比、驱动拆解
- **[全球 10Y 国债收益率风险](reports/global-bond-yields-risk-20260817.html)** · 收益率创高全景与风险分层评估
- **[宏观利率背景 × 六股影响](reports/54_宏观利率背景六股影响/index.html)** · 利差变动下六股的利率敏感度分析
- **[宏观背景（常设背景文件）](reports/55_宏观背景/index.html)** · 蓝筹池索引、利差与 Jackson Hole 更新
- **[利率上行 × 板块全景（2026-08-29 md）](reports/55_宏观背景/20260829_利率上行板块全景.md)** · 当日讨论固化：利率传导与板块影响全景
- **[57 农业股 × ENSO 回测 + 利率敏感性](reports/57_农业股ENSO与利率敏感性/index.html)** · 农业股对 ENSO 事件回测与利率敏感度
- **[57附 农业股 ENSO + 利率敏感性（绝对收益版）](reports/57_农业股ENSO与利率敏感性/绝对收益版.html)** · ENSO 回测的绝对收益口径重算
- **[58 农业股（CF/DAR）地缘溢价脱钩监测](reports/58_农业股地缘溢价脱钩监测/index.html)** · CF/DAR 与油价相关性的脱钩监测
- **[59 MOS vs CF：都是化肥股，走势为何差这么大](reports/59_MOS与CF化肥走势分化/index.html)** · MOS 与 CF 走势分化的归因拆解
- **[68 上周谷物暴涨归因调查（小麦/玉米/大豆）](reports/68_谷物暴涨归因调查_20260903/index.html)** · 08-24~28 周 CBOT 三品种暴涨：分品种主因拆解（黑海断供/美欧减产预期差/中国需求）、事件时间线与 37 条编号出处（数据/推论逐条可点击溯源）；第七节库存专题（三层库存结构/97% 口径还原/停火≠流量恢复/USDA PSD 分段历史比较 2015-20 vs 2021-25）
- **[60 日线MACD死叉 × 4hRSI超卖 买入胜率回测](reports/60_MACD死叉_4hRSI超卖_胜率回测/index.html)** · SOXX/NVDA/XAUUSD/QQQ 死叉+4h RSI 30-35 共振买多的胜率与显著性（2年4h样本，n=20 主口径 vs n=87 仅死叉对照）

---

## 4️⃣ 行业景气度与资金流

景气核查 / 业绩传导 / 机构持仓

- **[生物医药行业景气度](reports/21_生物医药行业景气度/index.html)** · 大药企 16 项景气指标核查
- **[小型生物科技（XBI）景气度](reports/22_小型生物科技景气度/index.html)** · 小 biotech 专用景气指标核查
- **[千亿美元药企专利悬崖](reports/26_千亿美元药企专利悬崖/index.html)** · 15 家巨头的专利悬崖与管线接力
- **[biotech 景气 → 工具业绩传导时滞](reports/25_工具业绩传导时滞/index.html)** · 融资行情到订单收入的传导链条
- **[2026 Q2 13F 全量资金流](reports/13f_q2_2026_sector_flow.html)** · 全行业加仓 / 减持全景

---

## 5️⃣ 个股基本面研究

### 🏥 医药健康
- **[诺华 NVS 全面研究](reports/27_nvs诺华深度研究/index.html)** · 诺华基本面与专利悬崖应对分析
- **[艾伯维 ABBV 全面研究](reports/28_abbv艾伯维深度研究/index.html)** · 艾伯维基本面与大单品切换分析
- **[DHR vs TMO 生物科技卖铲人对比](reports/DHR_vs_TMO_生物科技卖铲人对比.html)** · 生命科学工具龙头基本面对比

### 🛒 消费
- **[星巴克 SBUX 基本面分析](reports/29_sbux基本面分析/sbux基本面分析-20260824.html)** · 2026-08 全面基本面
- **[SBUX 财报与估值研究](reports/07_sbux星巴克/sbux_report.html)** · SBUX 财报与估值分析
- **[KO vs PEP 相对强弱](reports/28_ko_vs_pep_相对强弱研究.html)** · KO 与百事相对强弱拆解
- **[PG 宝洁深度分析](reports/67_PG宝洁深度分析/index.html)** · FY2026 财报拆解、五大问题严重度分层、估值与同业对比、跟踪点（67 号）

### 💳 金融科技
- **[SOFI × Block × AFRM](reports/sofi_xyz_afrm_report.html)** · 财报对比与 US10Y 敏感性

### ⚡ 电力 / 公用事业
- **[CEG vs VST 电力双雄](reports/04_ceg_vst电力股对比/ceg_vst_compare_report.html)** · CEG 与 VST 双雄对比分析

---

## 6️⃣ 市场结构与情绪

- **[IPP 大跌归因](reports/07_ipp大跌归因/ipp_drop_0818_report.html)** · 8/18 IPP 大跌的归因分析
- **[VIX 低位分析](reports/vix_low_spx_report.html)** · VIX 低位下 SPX 后续与持续性
- **[VIX 低位 × SPY 事件研究](reports/vix_low_spy_dashboard/index.html)** · VIX 低位日的 SPY 事件研究
- **[66 · CVS × VIX>18 高波动期表现](reports/66_CVS与VIX高波动期表现/index.html)** · VIX>18 状态下 CVS 当日与未来 1/5/20/60 日表现、VIX 分桶、恐慌冲击日与持续高波动段拆解
- **[期权墙八标的](reports/20_期权墙八标的/index.html)** · 2026-09-18 到期期权持仓结构分析
- **[富途热门股Top500过滤版](reports/hot_us_stocks_top500_filtered_20260901.html)** · 热度榜剔除>500$/中概/ADR 后 354 只明细
- **[热门股池RSI评估](reports/hot354_rsi_eval_20260901.html)** · 354 只 Wilder RSI14 分布、超买超卖分层、17 板块×RSI 交叉透视与组合筛选（分档×分板块×搜索）

---

## 📝 维护说明

- **新增报告后请同步更新本文件**：在对应分类下追加一行（标题 + 相对链接 + 分析主题简介（≤25 字，只讲做了什么分析、不讲结论））
- 报告目录命名规范：`编号_中文名`（如 `30_资管陡峭化`）
- 编号冲突（如 07、13、14、26、27、28 出现两个目录）为历史遗留，以目录内中文名区分
- 深度研究类报告（21+）统一使用 `index.html` 作为入口