# 📊 美股研究 · 报告索引

> 本工作区全部研究报告的统一检索入口（报告存放在 `reports/` 目录）
> 最后更新：2026-08-25 ｜ 覆盖报告：62+ 份 HTML

---

## 🗂 分类总览

| 分类 | 核心内容 | 代表报告 |
|------|----------|----------|
| **1. 量化策略与回测** | MACD / 突破回踩 / 支撑位 / 超买 | 01、10、11、13、14~18 |
| **2. 相关性分析** | 板块 / 个股 / ETF 联动关系 | 02、05、19、23、24、26、27 |
| **3. 宏观利率与资产联动** | 曲线陡峭化对板块影响、利率风险 | 06、08、09、30 |
| **4. 行业景气度与资金流** | 景气核查、业绩传导、机构持仓 | 21、22、25、26、13F |
| **5. 个股基本面研究** | 深度研究（医药 / 消费 / 金融科技 / 电力） | 27、28、29、30 之前系列 |
| **6. 市场结构与情绪** | VIX、期权结构、异动归因 | 07、20 |

---

## 1️⃣ 量化策略与回测

技术择时 / 买点信号 / 回测验证

### MACD 水下金叉系列
- **[MACD 水下金叉回测报告](reports/01_MACD回测/MACD水下金叉回测报告.html)** · 核心策略：水下金叉→3 日内上穿 EMA10&20→站稳→买点=金叉前 10 日盘整高与确认日 EMA20 均值；20 日回踩成交后胜率显著提升
- **[多股票回测对比报告](reports/01_MACD回测/多股票回测对比报告.html)** · 多标的横向对比
- 个股回测（AMZN / BRK.B / GE / GS / JNJ / MS / NVDA / SPY / UNH）在同目录下
- **[公用事业 MACD 水下金叉回测](reports/18_公用事业MACD水下金叉回测/公用事业MACD水下金叉回测报告.html)** · 同一策略在公用事业板块的验证

### 突破与支撑
- **[GILD / ABBV 突破回踩](reports/11_gild突破回踩/gild_abbv_breakout_report.html)** · 突破买点 + 回踩确认
- **[支撑 / 阻力位 AI 识别 Demo](reports/13_kbwb支撑位/support_levels_ms_demo.html)** · 支撑位识别方法（MS 示例）
- **[下降趋势线突破识别方法](reports/13_kbwb支撑位/trendline_breakout_report.html)** · AI 识别「下降趋势线突破」的方法 + 证据
- **[月线 EMA20 支撑位买入回测](reports/月线EMA20支撑位买入_回测报告.html)** · 月线级别支撑位买入回测
- **[蓝筹区间下沿支撑 × 周线EMA20压制（三组对照）](reports/31_蓝筹区间下沿支撑_周线EMA20压制回测/index.html)** · 47只低波动蓝筹 1570个下沿触达事件；周线EMA20压制本身影响有限（A vs B T+20 差异不显著），死叉显著放大尾部风险（C组P10=-10.7% vs A组-6.7%、T+20破位率71.4% vs 62.8%）

### 支撑 / 弱势板块研究
- **[道指板块支撑](reports/13_道指板块支撑/djia_sector_support_report.html)** · 平量 T+10 胜率 81% vs 放量 54%
- **[ETF 弱势支撑](reports/14_ETF弱势支撑/etf_weak_support_report.html)** · ETF 弱势位支撑
- **[KBWB 科技弱势](reports/14_kbwb科技弱势/kbwb_tech_weakness_report.html)** · 银行板块 ETF 中的科技弱项
- **[KBWB 医药弱势](reports/15_kbwb医药弱势/kbwb_med_weakness_report.html)** · 银行板块 ETF 中的医药弱项
- **[KBWB AM 弱势](reports/16_kbwbAM弱势/kbwb_am_weakness_report.html)** · 银行板块 ETF 中的资管弱项

### 超买与事件统计
- **[周线超买](reports/12_周线超买/weekline_ob_report.html)** · 周线超买信号（前提不成立的论证）
- **[KO RSI 超买](reports/17_KO超买/ko_rsi_overbought_report.html)** · 个股 RSI 超买回测（超买≠必回调；窗口路径：20 日内平均先冲 +3.46% 再回吐 ≈3.4%）
- **[涨 3% 事件研究](reports/10_涨3%事件/3pct_event_report.html)** · 单日大涨后的统计规律

---

## 2️⃣ 相关性分析

板块 / 个股 / ETF 之间的联动关系拆解

### 医药板块内部
- **[GILD × XLV/IBB 系列](reports/02_gild_xlv_ibb相关性板块分析/ibb_gild_corr_report.html)**（8 份报告，建议从主报告看起）：
  - [IBB × GILD 相关性](reports/02_gild_xlv_ibb相关性板块分析/ibb_gild_corr_report.html)（相关 0.576）
  - [IBB × AMGN / VRTX](reports/02_gild_xlv_ibb相关性板块分析/ibb_amgn_vrtx_report.html)、[AMGN × VRTX](reports/02_gild_xlv_ibb相关性板块分析/amgn_vrtx_corr_report.html)
  - [IBB 前十大权重](reports/02_gild_xlv_ibb相关性板块分析/ibb_top10_report.html)
  - [GILD 财报窗口反应](reports/02_gild_xlv_ibb相关性板块分析/gild_earnings_window_report.html)、[Q4 财报窗口](reports/02_gild_xlv_ibb相关性板块分析/gild_q4_earnings_window_report.html)
  - [GILD × ETF 对比](reports/02_gild_xlv_ibb相关性板块分析/gild_etf_compare_report.html)、[VIX 冲击影响](reports/02_gild_xlv_ibb相关性板块分析/vix_impact_report.html)
- **[药明康德 vs 美国药企](reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_bigpharma_report.html)** · 日相关仅 0.01-0.04：研发外包景气代理 ≠ 美大药企销售代理
  - [药明财务联动](reports/03_wuxi_bigpharma药明康德vs美国药企/wuxi_financial_link_report.html)
- **[CSCO × BUG 网络安全](reports/19_csco_bug网络安全/csco_bug_corr_report.html)** · 2026 相关性，同涨不同频

### 子板块 / 跨板块
- **[IHI × XBI 器械 vs 生物科技](reports/23_ihi_xbi器械vs生物科技/index.html)** · 2026-02 起脱钩：全期 0.652 → 分界后 0.249（Fisher z=6.34）
- **[IHI × XBI（13 日滚动重做版）](reports/26_ihi_xbi_13日滚动相关/index.html)** · 13 日窗口重做（辅助口径）
- **[工具四龙头 × IBB/XBI](reports/24_工具龙头_ibb_xbi相关性/index.html)** · A/WAT/DHR/TMO：对 XBI 分界后 0.28-0.35 全显著脱钩，对 IBB 更韧
- **[银行卡网络 V/MA](reports/27_银行卡网络_银行科技相关性/visa_master_corr_report.html)** · 支付网络 vs 银行 / 科技板块相关性拆解
- **[KBWB × MS](reports/13_kbwb支撑位/kbwb_ms_corr_report.html)** · 银行板块 ETF 与投行巨头相关性
- **[VST × UTES 分阶段演化](reports/05_vst_utes阶段分析/vst_utes_phase_report.html)** · β 0.84→2.41，α 全在低相关期赚
- **[KO × 科技/制药/医疗保健 相关性](reports/32_ko_科技医药相关性/index.html)** · KO×XLK 分界后由正转负 −0.40（z=8.63）、KO×XPH(代理IHE) 衰减至 0.03（z=4.67）、KO×XLV 稳定 0.41（不显著）——防御结构三向分裂

---

## 3️⃣ 宏观利率与资产联动

收益率曲线形态 → 板块表现

- **[银行 × 曲线陡峭化](reports/08_银行陡峭化/banks_steep_report.html)** · 走阔方向 R²<1% 不可靠，形态决定一切（加息陡最强、牛陡跑输）
- **[银行熊陡](reports/09_银行熊陡/banks_bear_steep_report.html)** · 熊陡形态下银行表现
- **[陡峭化 × 消费股](reports/06_陡峭化消费股/steep_ko_pm_mo_report.html)** · KO/PM/MO：消费股无防御优势，危机型深陡例外
- **[资管 × 曲线陡峭化](reports/30_资管陡峭化/index.html)** · APO/BX/KKR：大幅走阔（>+30bp/月）资管重挫 −6.8%/31%，严格熊陡资管最强 +5.71%
- **[全球 10Y 国债收益率风险](reports/global-bond-yields-risk-20260817.html)** · 收益率创高全景与风险分层评估

---

## 4️⃣ 行业景气度与资金流

景气核查 / 业绩传导 / 机构持仓

- **[生物医药行业景气度](reports/21_生物医药行业景气度/index.html)** · 大药企 16 项清单口径，2022-2026 V 型（+8/-1/+9）
- **[小型生物科技（XBI）景气度](reports/22_小型生物科技景气度/index.html)** · 小 biotech 专用 16 项清单，2022-2026（-14/+4/+4/+8/+11），与大药企口径方向相反
- **[千亿美元药企专利悬崖](reports/26_千亿美元药企专利悬崖/index.html)** · 15 家全球制药巨头的专利悬崖与管线接力
- **[biotech 景气 → 工具业绩传导时滞](reports/25_工具业绩传导时滞/index.html)** · 融资/行情→订单→收入链条，弹性主升段预期 2026Q4-2027
- **[2026 Q2 13F 全量资金流](reports/13f_q2_2026_sector_flow.html)** · 全行业加仓 / 减持全景

---

## 5️⃣ 个股基本面研究

### 🏥 医药健康
- **[诺华 NVS 全面研究](reports/27_nvs诺华深度研究/index.html)** · 穿越史上最大专利悬崖的转型样本
- **[艾伯维 ABBV 全面研究](reports/28_abbv艾伯维深度研究/index.html)** · 全球药企史上最成功的大单品切换样本
- **[DHR vs TMO 生物科技卖铲人对比](reports/DHR_vs_TMO_生物科技卖铲人对比.html)** · 生命科学工具/耗材龙头基本面对比（注意：WAT/DHR 含并表与剥离口径）

### 🛒 消费
- **[星巴克 SBUX 基本面分析](reports/29_sbux基本面分析/sbux基本面分析-20260824.html)** · 2026-08 全面基本面
- **[SBUX 财报与估值研究](reports/07_sbux星巴克/sbux_report.html)** · PE 虚高之谜、2021 高点突破、2015 年对比复盘
- **[KO vs PEP 相对强弱](reports/28_ko_vs_pep_相对强弱研究.html)** · KO 基本面分析暨 vs 百事相对强势拆解

### 💳 金融科技
- **[SOFI × Block × AFRM](reports/sofi_xyz_afrm_report.html)** · 财报对比与 US10Y 敏感性

### ⚡ 电力 / 公用事业
- **[CEG vs VST 电力双雄](reports/04_ceg_vst电力股对比/ceg_vst_compare_report.html)** · AI 电力双雄对比：同一仓位的两种表达，同时持有≈加杠杆

---

## 6️⃣ 市场结构与情绪

- **[IPP 大跌归因](reports/07_ipp大跌归因/ipp_drop_0818_report.html)** · 8/18 大跌残差 −5.29pp=叙事再定价，非 β
- **[VIX 低位分析](reports/vix_low_spx_report.html)** · VIX 低位下 SPX 后续行情与低位持续性
- **[期权墙八标的](reports/20_期权墙八标的/index.html)** · 2026-09-18 到期期权持仓结构分析

---

## 📝 维护说明

- **新增报告后请同步更新本文件**：在对应分类下追加一行（标题 + 相对链接 + 一句话结论）
- 报告目录命名规范：`编号_中文名`（如 `30_资管陡峭化`）
- 编号冲突（如 07、13、14、26、27、28 出现两个目录）为历史遗留，以目录内中文名区分
- 深度研究类报告（21+）统一使用 `index.html` 作为入口