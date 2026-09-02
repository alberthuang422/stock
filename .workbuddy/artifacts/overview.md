# 工作交接文档（2026-09-02 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/2026-09-02.md`，长期要点见 `.workbuddy/memory/MEMORY.md`，报告检索入口为 `README.md`。

## 一、当日工作全景（9/2）

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| 64 号 | DAL 达美 RSI 档位买入回测（`reports/64_DAL_RSI档位买入/`） | **与 56 号 CCL 结论完全相反：DAL 无超卖 α**——332 次三档买入 fwd20 超额全 ≤0；alpha 全在疫情前（<30 档 +3.24pp），本轮牛市三档全负（30-35 档最惨 −7.54%/胜率 26.3%）；仅 dd250≤−35% + RSI<26 有 edge；d2m≤3"反弹快"=下跌中继（fwd20 −10.4%/胜率 0%，与 CCL 一致）。当前 RSI 29.5、dd250 −18.2% → **历史统计不支持买入**。DCA 补测：等额定投资金加权 T20 +1.03% 跑输 SPY 定投 −2.06pp，"alpha 系 2008-09 金融危机 V 反的历史巧合" |
| 64 号·通道 | Futu over-HTTP 拉数通道走通 | Yahoo 403、stooq 反爬下：refreshToken 静默续期成功（无需浏览器）、DAL 4869 根全量 + SPY 两源拼接（08-27 价 771.10 完美衔接）；kline date 为 int yyyyMMdd 须转字符串；旧文件末行无换行会粘连 |
| 61 号 | Apollo (APO) 全球资管深度研究 | 10Y CAGR 26.6%（vs SPY 15.3%）但 2025 −11.5%/2026 YTD −7.8%——"高增长叙事 vs 渠道景气走弱"验证期；TTM PE 46.7x 贵于 BX 30.6x/KKR 34.1x。坑：gen_data 月末对齐 bug（各标的数据截止日不同 → union 后同月双点互缺）→ 改每月取最新交易日 + ffill |
| 63 号 | SOFI × AFRM × Block 相关性（当选后窗口 2024-10~今，476 日） | 全期相关 SOFI×AFRM 0.642 / AFRM×Block 0.559 / SOFI×Block 0.511 均显著；60 日滚动 0.19~0.91 大幅摆动，近 3 月 AFRM×Block 0.789 反超；累计 SOFI +116% / AFRM +93% / Block +25%。数据补齐用新浪美股 JSONP（与本地 Yahoo 六锚点一致） |
| 62 号 | CCL 嘉年华邮轮全面分析（基本面×估值×技术×量化） | 基本面强（五纪录、预订 93%、BBB-、回购开启）但 YTD −17%——背离；fwd PE ~11× 折价 36%；历史最优买点 RSI<30×dd60≤−30%×d2m>3 当前双条件未触发，右侧确认=站回 EMA20（$26.7） |
| 62 号·晚 | CCL 债务/利率/敏感度横向对比（官方源核实） | 净杠杆 3.1× vs RCL 2.6×/NCLH 5.3×——偏高但已入投资级下沿；固定债务 84.6%，US10Y+100bp 仅 +$13M/年可忽略；FY26 敏感性 **需求(yield)＞燃油（三巨头唯一不对冲）＞利率**；电话会"量平价升利更快"，下半年 yield 指引砍至 1.75% 致 Q3 EPS 指引 miss 砸盘 |
| 65 号 | 随机 10 只美股阻力位（`reports/resistance_10stocks_20260902.html`） | **方法教训：用户说"用 skill"必须先查 `.workbuddy/skills/`**（本项目已有 support-resistance-levels skill，初版自写后返工重做）；skill 算法 100% 复用 + swing_n 扩到 40（≈2 月级）；KKR/NRG/ACN/BG/XOM/NEE/ABT/SPGI/TROW/TDG，每只现价上方 1-4 个阻力位 |
| XLY | 2026-07-23 单日 −4.61% 成因核查（问答） | TSLA FCF 转负 −14.5% + GOOGL capex 恐慌外溢（AMZN −4.6%）+ 油价破百/10Y 4.7% 三层成因；TSLA+AMZN 贡献 ≈3.0pp ≈ 65%；次日修复 → 单日恐慌事件非基本面恶化 |
| 66 号 | CVS × VIX>18 高波动期表现（`reports/66_CVS与VIX高波动期表现/`） | **VIX>18 对 CVS 无绝对择时价值（p=0.54）但超额显著为负**（fwd20 −1.0pp/fwd60 −2.8pp）——恐慌后 SPY 反弹 CVS 跟不上；冲击日仅当日弱防御；CVS 是自身事件定价。数据源两换：Yahoo 403 → 新浪+CBOE 官方（旧 Yahoo 08-26 15.69 为异数）→ **用户 TradingView BATS 前复权（2022 高点 95.30 与富途 autype=1 逐位一致）**；口径切换后定性结论全不变 |
| 66 号·问答 | CVS × US10Y 相关性 | 全期弱正相关 +0.159 但 **2022 起实质性脱钩**（年度 |r|<0.08）；与 66 号互洽：VIX/10Y 对 CVS 均无稳定交易含义 |
| 自动化 | 每日 07:00 热榜 RSI 任务（f78907c8）首跑成功 | Top500→过滤 407→RSI 成功 270（137 失败率 33.7%，疑似富途限流加重，token 正常）；中位 RSI 48.2、超卖 12/超买 8；产出 hot_rsi_eval_20260902.html；git af24ab9 |

## 二、重要方法论决策 / 新增约定（9/2）

1. **数据源优先级重排（Yahoo 403 常态化后）**：①新浪美股日线 JSONP（`US_MinKService.getDailyK`，未复权全历史，SPY 六锚点验证）→ ②CBOE 官方 VIX（比 Yahoo 权威）→ ③Futu over-HTTP（refreshToken 自动续期，0.25s pacing + 指数退避可全成）→ ④用户 TradingView 导出（BATS 前复权，最可信对图源）。
2. **CVS 收益口径（用户口径）**：分析收益一律用**未复权 close = 不含股息**；前复权仅用于对图校验（用户 95 记忆=前复权口径）。66 号 v2 主数据已切 BATS 前复权，报告中两口径并列。
3. **"用 skill" 先查现成**：用户说"用 X 找出 Y"时先 `ls .workbuddy/skills/` → 读 SKILL.md → 复用其脚本，避免自写返工（65 号教训）。
4. **热榜选股 skill 方案已评估待开工**：support-resistance 算法零新写，需补 ①热榜日线批量补拉（本地覆盖率仅 20%）②±2-3% 邻近筛选 ③join rsi14 ④AI 精判层校准（规则提取+回归测试路线，5-10 个标注例子即可启动）。
5. **渲染验证降级先例**：本环境 headless Chrome GPU 进程持续崩溃（0xC0000142/-1073741510，两日复现）→ 静态检查（node --check + 占位符校验）为兜底；确需真实渲染时用一次会话快速验证。
6. **cp 备份时序**：覆盖主数据文件前必须先备份（9/2 曾备份成新数据靠 git 找回）。
7. **延续铁律**：60 日滚动主口径/显著性三档+p 值/红涨绿跌+Okabe-Ito/术语悬停浮窗/交付克制/尾 bar 体检/README 登记前先 ls 校验。

## 三、当日产出清单（9/2）

- **报告**（reports/，均已登记 README）：64 号 DAL RSI 档位买入、61 号 APO 深度、63 号 SOFI/AFRM/SQ 相关性、62 号 CCL 全面、65 号随机 10 只阻力位、66 号 CVS×VIX 高波动期（v2 BATS 口径）、hot_rsi_eval_20260902.html
- **脚本**（scripts/）：build_64_dal_rsi_report.py、verify_64_dal_report.cjs、dal_rsi30_dca.py、build_61_apo_report.py（gen_data 修复）、build_62_ccl_report.py、build_66_cvs_vix_report.py、fetch_cvs_vix.py、analyze_cvs_vix.py、convert_bats_cvs.py、cvs_us10y_corr.py、xly_components_0723.py 等
- **数据**（data/）：`cvs/CVS, 1D.csv`（BATS 前复权主文件）、`cvs/CVS_sina_raw, 1D.csv`（未复权备份）、DGS10 更新至 08-31
- **结果**（results/）：cvs_vix_analysis.json、cvs_us10y_corr.json、61_apo_stats.json、sofi_afrm_sq_corr.json、xly_components_20260723.csv、resistance_skill/*.json
- **git**：9/2 全天已按主题 11 个 commit（63 补交 → 65 号 → XLY → 66 号系列 5 个 → 66 号复跑 → CVS×US10Y → 每日热榜 af24ab9），已 push origin/main

## 四、git 状态与本次提交（2026-09-03 02:0x，每日交接）

**前情**：9/2 白天产出已全部按主题入库并 push（见上）。本次交接前工作区剩余：`.workbuddy/memory/2026-09-02.md`（+15 行：CVS×US10Y/每日 RSI/CCL 债务对比补记）、`.workbuddy/memory/MEMORY.md`（CCL 债务对比条目）、`.workbuddy/memory/automations/f78907c8…/memory.md`（每日任务自动化记忆）、`hf2.txt`（Temp 性质调试残留，**不提交不删除**）。

**本次动作**（用户授权"提交到 github 即可"，push 已获授权）：
1. 补齐 9/2 日志（CCL 债务对比一节）
2. 覆盖更新 `overview.md`（9/2 全天汇总，本文档）
3. commit：交接文档 + 9/2 日志 + MEMORY 更新 + 自动化记忆
4. push → ls-remote 验证远端与本地一致

**安全说明**：全程仅 add/commit/push；无删除/clean/reset/force；`hf2.txt` 与 Temp/ 未跟踪文件不做处理；全部改动可 git 回滚。

## 五、重要过程 / 踩坑（9/2）

- **Yahoo 直连 403 全禁**（UA/域名均失效）+ stooq 反爬 → 新浪/CBOE/Futu/TradingView 四通道建立（见方法决策 1）。
- **VIX 权威口径**：CBOE 官方 vs Yahoo 个别日 close 有出入（08-26 15.69 vs 15.21 官方结算），以后 VIX 一律用 CBOE。
- **复权口径陷阱**：新浪未复权 2022 高点 111.25 vs 前复权 95.30 差异全为分红回溯（无拆股）；两口径都正确，关键是分析目的明确（含息/不含息）。
- **Futu 限流加重**：每日任务首跑 270/407（33.7% 失败），token 正常 → 次日观察是否需加大退避间隔。
- **headless Chrome GPU 崩溃复现**（64/66 号两日）→ 静态验证兜底已成既定流程。
- **月末对齐 bug**（61 号）：多标的数据截止日不同时 union 月度对齐会产生双点互缺，须"每月取最新交易日 + ffill"。
- **热榜本地覆盖率仅 20%**：每日任务只产 RSI/热度，K 线分析前须先批量补拉日线。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md + 项目 MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （≤50字）`、按主题分 commit；**默认只本地 commit，push 需用户明确要求（每日交接任务已获授权）**。
- **高权限自我约束**：不做删除/clean/reset/force 等破坏性操作；全部改动可 git 回滚；push 前确认工作区状态。
- 交付必须产物展示（present_files）；交付不附图；术语悬停浮窗；红涨绿跌 + Okabe-Ito 色弱安全。
- 结论必须先核实数据、无法核实标注「未核实」；评审四段式；相关性 60 日滚动主口径；交付克制。
- CDP 仅在推特/X 抓取或常规手段不可行时启用，用完必关。

## 七、遗留待办 / 下次继续

- **★ 每日 07:00 热榜 RSI 任务观察**：9/2 失败率 33.7%（疑似限流加重），连续两日高失败则加大退避间隔或分时段重试。
- **★ 选股 skill 开工**（用户已定方案）：热榜 → 支撑/阻力邻近（±2-3%）× RSI 配合筛选；先批量补拉热榜日线，AI 精判层准备 5-10 个标注例子（含反例）。
- **★ XAUUSD 60 号信号窗复核**：09-01 开盘买点（日线死叉 + 4h RSI 32.4），核对 T+5/T+10 实际走势。
- **CCL 落地跟踪**：Q3 EPS 指引 miss 后观察是否带入 RSI<30 × dd60≤-30% 深跌区（历史最优买点）；右侧确认=站回 EMA20（$26.7）。
- **9/4 8 月非农分水岭**（沿用）：若为负 → 衰退起点解读；落地后复核 10Y-2Y/10Y-30Y。
- **66 号双口径已闭环**；58 号主报告修订（XLE 双口径表述）、57 附 p 值 bug 修复（沿用待办）。
- **9 月 ASO ONI 发布后**（沿用）：复核残差表；ASO≥+1.5 则上调 2015 剧案权重。
- **52 号 MCD 操作跟踪**（沿用）：4% 反弹目标（260→270.5）、收盘止损 <255/<253。
- **Temp/ 与 hf2.txt**：中间产物保留未跟踪，需时可随时重拉。
