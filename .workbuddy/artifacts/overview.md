# 工作交接文档（2026-08-26 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/YYYY-MM-DD.md`，长期要点见 `.workbuddy/memory/MEMORY.md`，报告检索入口为 `README.md`（6 大分类索引）。

## 一、当日工作全景

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| VIX研究 | VIX 低位 × SPY 事件研究（SPY 口径） | SPY ETF 1995 起 7964 交易日；VIX<15 共 178 段**中位仅持续 3 天**占全期 30.1%（自我强化：已 10 天再维持 ≥10 天概率 65.3%）；到 VIX 首破 20 中位 57 交易日；短持有（T+5/10）低位日略弱，**T+120 低位日显著更强**（<15 +0.80pp t=3.9；<12 +1.47pp t=6.2）→ 风险在低波动结束途中而非低波动本身 |
| 36 | 周线 0 轴上方高位死叉 × 回踩 EMA20(1~3%) | **反直觉：支撑未被削弱、破位率也未抬升**——A 组破位率 57.1% 反为三组最低（B 72.7% / C 63.9%），T+20 与随机基线打平；**10~16 周「首次回调」窗口是全部分档最弱段**（+2.63% vs 16-24 周 +7.07%/77%、24-40 周 +6.65%/75%）；DIF 回落 ≥25% 是主要样本杀手（n 37→14 且无收益提升）；A 组破位(n=7) fwd20 −9.95% vs 未破位 +19.59%，破位组 fwd60 仍收回 +8.1%（承接报告31深死叉逻辑） |
| GE | GE 周线数据刷新 + MACD/EMA 现状 | `GE, 1W.csv` 1914 行 1990-2026-08-25（adj_close 复权，与旧 `ge, W.csv` 1962 无复权版并存）；8 月中旬单周 −5.43%；**周线 MACD 刚现高位死叉**（本周 DIF 13.94 < DEA 14.93）但仍在 0 轴上方；EMA10 353.5 > EMA20 340.6 多头未破坏，价格 348.37 已跌破 EMA10 仍在 EMA20 上方 |
| 37 | KO vs XLV × 道琼斯相关性 | **XLV 相关 ≈ 2×KO**（Pearson 0.443 vs 0.232）；2026-02 分界后 **KO×道指 0.267→0.005 完全脱钩**（Fisher z=2.97，KO 2026 以来 +31.8% vs 道指 +10.3%，独立行情），XLV×道指 0.474→0.231 仍显著正相关；归因=板块 ETF β 贴大盘 vs 个股公司噪音稀释 |
| 修复 | 37/32 折线图单位错配（用户报 bug） | 根因：分析脚本 corr ×100 存百分数、build 注入 ECharts 未 ÷100 → 整线溢出画布（32/37 中招；23/26 正常）；全量扫描命中 2 份，build 补 `corr/100` + y 轴按极值校准；**已立铁律**（见第二节），交付前必跑 `scripts/_scan_corr_units.py` |
| 38 | CSCO vs 纳指/道指相关性 | **CSCO×纳指 27 年高相关 0.728/β0.98 但 2026-02 后断崖脱钩至 0.406**（z=5.9，R² 54%→16%）；×道指仅 0.365 弱联动（道指科技权重低，CSCO 从未是"道指股"）；2026 全部 ≥5% 大波动（02-12 −12.3%/05-14 +13.4%/08-13 −8.4%）均在财报日、指数零跟随；2026 相对纳指 +29.7pp/道指 +33.7pp 历史级超额 → 个股 alpha 期 = 与大盘相关最低期（同 37 KO 脱钩逻辑） |
| LLY | LLY 8/26 大跌归因调研（推特） | −3.49% 系 **GLP-1 减肥药链整体走弱非个股利空**（NVO −3.45%/MRNA −7.19%/HIMS −5.13%/XBI 回吐）；无降级/FDA 负面/管线失败；背景= Pepsi 停员工 GLP-1 覆盖（8/25-26）+ Reuters 约 14% 雇主 2027 放弃覆盖 → 支付端承压；LLY 起诉 FDA 将 retatrutide 归为生物制品（延专利）；8/24 冲 52 周新高 1247 后技术回调 |
| fintech | 2020-21 fintech 大行情与腰斩复盘（专家会话） | PYPL PE 峰 79.2x→11.8x、UPST 395x→58.8x、Block P/S 10.7x→2.0x、AFRM 20.5x→6.8x；上行=疫情数字化+零利率+财政刺激（TGA/支票/PPP）+零售交易潮；下行=2022 加息+风投断血（CB Insights 融资 −46%）+监管+盈利不达；2026 AFRM/Block 已修复、ARKF 横盘 |
| — | 每日收尾交接 + GitHub 提交 | 本 automation：8/26 全天汇总入库并推送（详见第四节） |

## 二、重要方法论决策 / 新增约定（8/26）

1. **图表单位陷阱（铁律，历史坑第三次爆发）**：分析脚本把相关序列 ×100 存百分数（rolling60/monthly/yearly 的 `corr` 字段），**build 报告注入 ECharts 时必须 ÷100 还原为 0~1 小数**，否则整条折线超出画布（32/37 号报告中招；23/26 号有 `/100` 正确）。zscore / 价格归一化不用除。**预防**：交付前跑 `scripts/_scan_corr_units.py` 全量扫 yAxis 范围 vs 数据值域，命中即修。
2. **事件研究显著性必须互斥对照**：不能拿「事件=基线子集 vs 全集」做检验（t 虚高到 31 的坑），低位日 vs 非低位日互斥组 + Welch t（VIX 研究）。
3. **ECharts CDN 异步加载**：custom_html 初始化脚本必须加 echarts 就绪轮询，否则无头渲染下 canvas=0 且无报错（VIX dashboard 自检踩坑）。
4. **极小样本警示**：n 11~14 时统计功效极低，t 值仅作方向参考、显著性一律视作上限（报告36 A/B 组）；ex-post 参数扫描需固化 sensitivity 段 + dashboard「参数敏感性」图。
5. **Yahoo 周线未完成周拆分 bar**：周线最后一个 bar 是本周进行中数据，做 MACD/EMA 现状须以最后完整周（GE = 2026-08-17 周，收 348.37）为准，本周实时 bar（08-25 收 349.54）仅参考。

## 三、当日产出清单（reports/ 编号目录）

- `vix_low_spy_dashboard/`（VIX 低位 SPY 事件研究）+ `36_高位死叉回踩EMA20支撑/` + `37_ko_xlv_dji相关性/` + `38_思科纳指道指相关性/`
- 数据：`data/ge/GE, 1W.csv`（1914 行，1990-2026-08-25 复权）；`data/spy/SPY, 1D.csv` / `data/vix/VIX, 1D.csv` 尾部增量至 08-25/08-26（前缀数值与旧版完全一致）
- 脚本：`vix_low_spy.py`、`build_vix_low_spy_dashboard.py`、`macd_deadcross_ema20_backtest.py`、`build_macd_deadcross_dashboard.py`、`ko_xlv_dji_corr.py`、`build_ko_xlv_dji_report.py`、`csco_index_corr.py`、`build_csco_index_report.py`、`fetch_ge_weekly.cjs`、`ge_weekly_indicator_status.py`、`fetch_vix_spy_update.cjs`、`_scan_corr_units.py`；自检 `test_render_vix_spy.cjs` / `test_render_ko_dji.cjs` / `test_render_csco_index.cjs`
- 结果：`results/vix_low_spy.json`、`vix_low_spy_events.csv`（2395 事件日）、`macd_deadcross_stats.json`（含 sensitivity 段）、`ko_xlv_dji_corr.json`、`csco_index_corr.json`
- 有用工具：westock-data kline 解析 markdown 表格存 CSV 流程可复制（`data/dji/dji, 1D.csv`，指数无 adj_close 仅 close）

## 四、git 状态与本次提交（2026-08-27 00:0x，automation）

**前情**：8/26 白天已按主题提交 5 个（`196aaf3` VIX低位SPY → `9ee1ac8` 报告38，含报告36/37/单位修复），提交信息规范。远端 main 同步情况以 `git ls-remote` 验证。

本次 automation 补交 8/26 晚间未跟踪产出 + 交接文档/日志，按主题分 commit：
1. GE 周线数据 + 拉数/指标脚本（`data/ge/GE, 1W.csv` + `fetch_ge_weekly.cjs` + `ge_weekly_indicator_status.py`）
2. SPY/VIX 主数据尾部增量 + 增量拉数脚本（pandas 重写全文件，但前缀数值逐行校验 **0 处不一致**，仅尾部新增 VIX+4 至 08-26 / SPY+3 至 08-25）
3. 交接文档 + 项目日志（LLY 调研/报告38 追加）+ MEMORY 单位陷阱铁律 + 本 automation 执行历史

**有意未入库**：`data/tmp_vix_spy_update/`（拉数临时输出，数据已被主 CSV 吸收，目录名带 tmp 留作未跟踪）；`scripts/fetch_djia_week_0821.py`（8/21 遗留、无当日产出，历史惯例）。

**push**：以 `git ls-remote origin main` 验证远端 → 推送本次 + 全部积压本地提交 → 再验证远端新 HEAD 与本地一致。

## 五、重要过程 / 踩坑（8/26）

- **单位错配修复链条**：现象（用户报图异常）→ 扫描 `_scan_corr_units.py` 全量命中 32/37 → build 脚本 `corr/100` + y 轴极值校准 → `test_render_*.cjs`（playwright-core + 本机 Chrome）实际渲染验证三图 canvas 正常、overflow 为空、0 报错。
- **事件研究显著性初版坑**：VIX 研究初版拿「事件=基线子集 vs 全集」检验，t 虚高到 31——必须互斥对照组（低位日 vs 非低位日）。
- **周线数据注意**：Yahoo 周线末尾带未完成周 bar（GE 本周 08-24/08-25）；指标现状以最后完整周为准。
- **推特事件归因**："最新"时间线滚动加载受限，需多关键词并行 + 同链板块对照（NVO/XBI/HIMS/MRNA）判断板块 vs 个股（LLY 案例）。
- **报告38 日志追加时漏标题行**（内容行 65 起直接进入正文）——已补齐语义，后续追加日志注意保留 `## 报告N：` 标题格式。
- 高权限自我约束践行：全程仅 add/commit/push，未做任何删除/clean/reset，全部改动可 git 回滚（本次 3 个 commit 均只含新增文件或已入库文件覆盖）。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （≤50字）`、按主题分 commit、只本地 commit 不 push（除非用户明确要求，如本 automation）。
- 高权限自我约束：不做删除/clean/reset 等破坏性操作，全部改动可 git 回滚。
- 交付不附图；红涨绿跌 + Okabe-Ito 色弱安全（叠符号/线型）；严格口径（不要股息/容差缓冲）。
- 结论必须先核实数据，无法核实标注「未核实」；评审四段式；相关性以 60 日滚动为主口径。

## 七、遗留待办 / 下次继续

- **31 号正式报告补更（仍未执行）**：★超额口径轴 + 环境分层表（评审已出结论，报告正文未更新）；31 评审交接文档见报告目录内。
- **GE 周线高位死叉跟踪**：周一/二 DIF 已死叉 DEA 但 0 轴上方 + EMA 多头未破坏——是否跌破 EMA20（≈340.6 / 现值 348.37）是关键观察位，可作下次盘面确认点。
- **VIX 低位状态**：VIX<15 已持续多日（8/26 收 15.69 逼近阈值），低位自我强化规律可作波动监控参考。
- 支撑位 S1 状态追踪（59 near / 35 above / 6 below）——可作每日盘前观察清单；`compute_support_levels_all.py` 幂等可重跑。
- 生物医药跟踪点：HARMONi-3 终局（2026H2）、OMB 名单（2026-12）、工具弹性主升段预期 2026Q4-2027；XBI 2025-09 以来 +78.4% 链传导验证。
- **LLY 跟踪点**：retatrutide"生物制品"归类诉讼（涉专利延至 13 年）、Pepsi/雇主 GLP-1 覆盖动向（支付端压力是否扩散）；Zepbound 55+ 医保成本真实世界研究（被指未计药价）。
- Agent Reach 待配：xueqiu/OpenCLI/github auth/xiaoyuzhou Groq/exa 验证；X 搜索走 Chrome CDP 定案。
- KO：Q3（10 月）+ Fairlife 勒索软件事件；SBUX：等 FY26Q4 验证利润率，回调 $97-100 观察位。
- 未核实项留档：NVO 美国专利年份（2031 vs 2033 来源打架）——建议以 FDA Orange Book + 10-K 为准。