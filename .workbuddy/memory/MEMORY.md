# MEMORY.md —— 股票分析项目长期记忆

> 项目：MACD 回测 + 相关性分阶段分析 + 个股财报/估值/景气度研究
> 逐日明细见 .workbuddy/memory/YYYY-MM-DD.md，脚本 scripts/，报告 reports/（中文目录名）
> **报告检索：README.md 是唯一入口（6 大分类索引），每出新报告必须同步更新 README 对应分类（标题+链接+一句话结论）**

## 数据与拉数
- Yahoo 日线唯一可靠途径：本机 Chrome CDP 原生 WebSocket（Chrome `run_in_background=true`，端口 `localhost:9222`，拉数脚本 `dangerouslyDisableSandbox=true`）。模板 scripts/fetch_banks_cdp.cjs（建 tab→navigate→sleep→Runtime.evaluate→close；新版 Chrome PUT /json/new 忽略 url，须建 tab 后 navigate）。用完必须关闭 Chrome(9222 进程树)+cdp-proxy。
- FRED 直连：`https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2`，缺失转 NaN dropna。
- venv：`C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`；node：`C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2\node.exe`，npm 装到 `...\node\workspace\node_modules\`（需自建目录）。
- 期权数据（富途 futu MCP 唯一来源）：expiration_date 拿到期日 → option_chain 拿该日全部合约（无 OI）→ **OI/量/IV/希腊字母逐合约 quote_stock_quote（code_list≤400，option_ex_data.open_interest）**；返回值过大自动落盘 .workbuddy/projects/.../tool-results/*.txt 用 python 解析。**quote_financials_statements 只传 symbol 可用，加 financial_type/statement_type 必校验失败**。

## 回测/方法要点
- **T+N 口径（08-25 明确）：T+5/T+10/T+20 等，数字一律指交易日数，非日历日期+N**。即 T+5=事件后第 5 个交易日、T+10=第 10 个交易日……fwdN 即 N 个交易日未来收益，用交易日对齐（跳过周末/假日），绝不用自然日或日期相减。
- 水下金叉→3日内上穿EMA10&20→站稳→买点=(金叉前10日盘整高+确认日EMA20)/2→30日回踩成交；hold5 T+5 胜率 52.7%→84.8%（确认+回踩后），T+20 反超（72.7%）→ 回踩买应持 20 天。
- 事件研究流程：池子→adj_close→pct_change→fwdN→mask→对照→**超额=基准 fwdN（非价格）merge 相减**→stats(n,mean,med,win%,std,p25/75,t,二项近似)。独立性最易高估（聚类/拥挤日）、显著性一律视作上限（skill quant-report-review）。
- 历史点位用 adj_close 复权口径；回报统计一律百分数（×100）；json.dump 前 clean() 转 None、numpy 转 int；ECharts markArea 二维数组；f-string 嵌 JS 用 @@PLACEH@@+.replace()。

## 用户偏好（长期规则）
- **Git 提交（08-22/08-23）**：格式 `yyyy-mm-dd  msg: （≤50字）`；按主题分开 commit，不混无关内容；**只本地 commit，不 push**；用 `git -c user.name="Makemoney" -c user.email="alberthuang422@gmail.com"`。
- **交付不附图（08-23）**：报告不再附渲染截图（SSR 测试保留仅验证）；删除历史全部 results/*.png；test_render_*.cjs 已去掉截图逻辑。
- 严格口径：不要股息/容差缓冲；**红涨绿跌 + 色弱安全（Okabe-Ito，叠符号/线型）**；报告浅底深字研报风+ECharts；对照默认窗口 2025-09 起、超额分四档；报告目录中文名「编号_中文名」；财报问题先确认财报期。
- **相关性分析口径（08-23 设定，已修正）**：以 **60 日滚动为主口径**（历史一致）。13 日曾试点但被实证否定——单点 SE=0.32（±0.62）、极端日扭曲（2026-04"回弹 0.76"在 120 日口径仅 0.42，噪音假象）、lag1 自相关 0.94+；结论一律以 60/120 日为准，13/30 日仅辅助。
- **Dashboard 布局（08-25 设定）**：超长事件清单（数百~上千条）**另起独立选项卡「事件明细」收录**，主 tab 只留结论/图表/对照表，不放明细表（构建脚本里把 trades_table 模块 tab 改为独立 tab 并追加）。
- Token 优化：build 脚本只 print `written: path size`；报告 JSON 瘦身（画廊只注入代表事件）；分析脚本只打汇总；拉数→分析→报告拆三段。

## 关键结论（2026-08）
- **景气度 21 号（中国+10 强景气下沿）→ 美股口径 +9 结构性景气上沿 → 三年 2024+8/2025-1/2026+9 V型 → 五年 2022 -4/2023 -1/2024 +8/2025 -1/2026 +9 深V；口径辨析：16 项清单=大药企销售盈利驱动 ≠ XBI 小biotech（融资→并购→临床），XBI×并购金额相关 0.494，2024 方向分歧=脱钩实证**。22 号小biotech 专用 16 项：2022 -14/2023 +4/2024 +4/2025 +8/2026 +11，与 21 号 2023/2025 方向相反。
- **药明**：日相关 vs 5 大药企 0.01-0.04、vs IBB/XBI 0.10-0.12 → 全球研发外包景气代理，≠美大药企销售代理；药明强≠大药企强。
- **IBB/GILD/AMGN/VRTX**：IBB×GILD 0.576；AMGN 利好脱钩、VRTX β0.93 贴板块弱弹性、GILD 利空脱钩；引擎=NTRA/ILMN/RVMD+中小市值；ALNY 最大反向（−46.4pp）。
- **IHI×XBI（23 号）**：2026-02 起脱钩——全期 0.652 → 分界前 0.666 → 分界后 0.249（Fisher z=6.34）；XBI 2025-09 以来 +78.4% vs IHI −8.9%。极端日联动单向：XBI 主导、IHI 钝化，仅宏观冲击日同步。
- **工具龙头 A/WAT/DHR/TMO×IBB/XBI（24 号）**：对 XBI 分界后 0.28-0.35 全显著脱钩，对 IBB 0.40-0.45 更韧；最韧 WAT（客户偏工业/学术），最惨 DHR（与 biotech 融资绑定深）；四龙头内部 2026 更抱团。
- **工具业绩传导时滞（25 号）**：上一轮约 3-4 季度——XBI 2020Q2 +44.6% → 2021 工具板块 YoY 峰值 17.3%；链条=融资/行情(0-2Q)→订单(+1-2Q)→收入(+2-4Q)。本轮：XBI 2025Q3/Q4 启动 → 工具 2026H1 加速（A +10.0%），**弹性主升段预期 2026Q4-2027**。口径：WAT 2026 +91%/+113% 是并表 BD Biosciences（有机仅 +9%）；DHR 2023 剥离 Veralto；TMO/DHR 2020-21 含 COVID。
- **CEG vs VST**：2022 以来打平；2026 YTD 双杀；相关 0.70。同一仓位两种表达，同时持有=加杠杆非分散。
- **VST×UTES**：β 0.84→2.41，α 全在低相关期赚；2026 回调解剖 VST 跌盈利质量 vs CEG 跌政策+估值。
- **US2Y弱+US10Y强陡**：50 年仅 6.3% 月份；消费股无防御优势，危机型深陡例外。
- **IPP 8/18 大跌**：残差 −5.29pp=叙事再定价，非 β。
- **银行×走阔**：走阔方向 R²<1% 不可靠；形态决定一切（加息陡最强、牛陡跑输）。

## 报告索引（重要）
- 21/22：生物医药景气度（大药企/小biotech 双口径，来源链接 129）；23 IHI×XBI 器械vs生物科技；24 工具龙头×IBB/XBI；25 工具业绩传导时滞；13 道指板块支撑（平量 T+10 胜率 81% vs 放量 54%）；12 周线超买（前提不成立）；11 横盘突破（50 笔 T+20 +3.05%/66%）；10 涨3%事件。
- **30 资管×曲线陡峭化（08-24 首做）**：APO/BX/KKR×US10Y-US2Y。主口径同 08/09 银行（月频 Δslope + 形态分解 + 2011-11 同窗口对照）。核心：走阔方向弱信号（R²<1%）；**大幅走阔（>+30bp/月）资管重挫（-6.8%/31%）vs 银行抗跌——走阔幅度代理危机烈度（2008/SVB）**；严格熊陡资管最强（+5.71%/81.8%，二项 p=0.033）与银行相反（银行加息陡最强）；走阔后 3 月 am3 +8.6% 跑赢、12 月 SPY 反超 → 超额偏短周期。报告编号 30 承接 29。