# MEMORY.md —— 股票分析项目长期记忆

> 项目：MACD 回测 + 标的间相关性分析 + 个股财报/估值研究
> 业务：基础回测结论见下，逐日明细见 .workbuddy/memory/YYYY-MM-DD.md，报告脚本见 scripts/

## 数据与拉数
- 目录：data/<ticker>/（Yahoo 1D/1W + 用户下载腾讯 *_240_tencent.csv）、scripts/、reports/、results/；.workbuddy/ 勿动。
- **Yahoo 拉数（唯一可靠）**：本机 Chrome CDP 原生 WebSocket。**Chrome 须 `run_in_background=true` 启动**（sandbox Bash `&` 会被回收）；端口绑定 IPv6，用 `localhost:9222`；**拉数脚本须 `dangerouslyDisableSandbox=true`**。模板：scripts/fetch_banks_cdp.cjs（建 tab → Page.navigate → sleep 7s → Runtime.evaluate → close；Node22 内置 WebSocket，无需依赖。**新版 Chrome PUT /json/new 的 url 参数被忽略，须建 tab 后 navigate**）。
- **FRED 可直连**：`https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2`（/DGS10/...）curl 即可；缺失值读后 `pd.to_numeric(errors="coerce")` + dropna。
- venv python：`C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`。
- node：`C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2\node.exe`；npm 装到 `C:\Users\Administrator\.workbuddy\binaries\node\workspace\node_modules\`（**目录需自行 mkdir**）。

## 回测规则（用户确认口径）
水下金叉(DIF<0,DEA<0) → 金叉后3日内收盘上穿 EMA10&EMA20（严格无容差）→ 站稳 y=3/4/5 天（允许1天跌破次日收复）→ 买点=（金叉前10日盘整最高价+确认日EMA20）/2 → 30日内首次回踩(low≤买点)成交，未回踩=错过；收益金叉日收→T+N、买点→B+5/10/20；10日内多次金叉合并计1次。结果：hold5 T+5 胜率 52.7%→84.8%（10只均 56.5%→88.2%）；等确认+回踩 T+5 缩水但 T+20 反超（72.7% vs 66.7%）→ 回踩买应持 20 天；最差年 2024（22%/−3.33%）、2018、2016；2017 最好 88%。

## 用户偏好
- **Git 提交规范（2026-08-22 设定）**：每次提交 message 格式统一为 `yyyy-mm-dd  msg: （做什么，<=50字）`，如 `2026-08-21  msg: 横盘突破/道指共振等7项分析`。提交用 `git -c user.name="Makemoney" -c user.email="alberthuang422@gmail.com"`（全局未配置）。
- 严格口径：不要股息/容差缓冲；红涨绿跌（**色弱安全**：不可只靠红绿区分，叠符号/线型/标签）；K 线成交点紫菱形/黑菱形。
- 报告浅底深字研报风 + ECharts；交付前必须过 SSR 渲染测试（test_render_*.cjs，chromium.launch executablePath 本机 Chrome）。**数据 JSON 注入用 `var DATA = __DATA_JSON__;` 占位符**。
- 对照分析默认窗口 2025-09 起；超额分四档（分界前/后/2026分界前/2026以来）全给。
- 爱刨根问底：相关性→跷跷板→相对强弱→贡献归因→剔除归因，每层量化。
- **财报类问题先确认财报期**（曾把"财报"默认理解成 8/4 Q2，实际指 2/10 Q4）。
- **报告目录一律中文命名**（2026-08-22 用户要求，必守）：reports/ 目录名用「编号_中文名」格式（如 04_ceg_vst电力股对比、06_陡峭化消费股、10_涨3%事件），与已有 01~17 目录风格统一；英文代号可保留为前缀。散落 html 也要归入中文目录。生成新报告时同样遵循（build 脚本 OUT 路径用中文目录名）。

## Token 优化规范（2026-08-21 用户要求，必守）
单轮分析任务实测约 80 万 token，人工审计三大浪费：① 每轮重复注入系统提示（~40%）；② build 脚本把整个 HTML 打回控制台（~35%）；③ 报告 JSON 注入体积过大 / 试错重跑。
- **build 脚本必须静默写盘**：只 print(`written: <path> size=xxx`)，禁止 print 整个 HTML（含 var DATA= 大 JSON）。除非调试，否则不打印正文。
- **报告 JSON 注入瘦身**：K 线画廊只注入代表性事件（前 8~12 个或懒加载），不要全量 36 张；K 线窗口默认 [t0-3, t0+10]，不全程 [t0-6, t0+21]。主 KPI/表格数据保留。
- **分析脚本输出裁剪**：只打印汇总 KPI + 结果写 JSON；不打印每事件明细/全量列表。
- **大任务拆会话**：拉数→分析→报告分三段，中间靠 results/*.json + .workbuddy/memory/ 衔接，减少系统提示重复注入。
- **减少试错循环**：先 `python -c` 单步验证数据再生成；修完一次跑完整验证，避免"跑→看→改→重跑"循环。自主确认改进后记入当日日志。

## 踩坑（高频）
- **美股历史点位分析必须用 adj_close（复权）口径**与腾讯自选股对齐：未复权历史高点偏高（SBUX 2021-07 未复权 $126.06 vs 复权 $111.54）。PE/EPS 估值指标基于未复权价÷EPS 不受影响。**电力/部分标的 close==adj_close「勿复权」规则不适用（TLN/CEG/VST/NRG 几乎不分红）**。
- fetch 脚本必须放 scripts/ 下（__dirname 决定输出路径）。itertuples 的 row.date 是 Timestamp；json.dump 遇 numpy 先 int()/round()；resample("ME").corr() 不存在 → groupby(pd.Grouper(freq="ME")).corr()。
- data/<ticker>/ 若含 BATS_ 前缀旧文件（腾讯格式）glob 会干扰，load_stock 过滤。
- Python f-string 嵌入大段 JS 用普通三引号 + @@PLACEH@@ + .replace()（单花括号 SyntaxError）。
- **统计单位陷阱**：所有回报统计字段一律百分数（×100），否则混读出 0.01% 离谱值。口径区分必标注（时期 vs 单月）。
- **ECharts markArea** data 必须是二维数组 `[ [start,end],... ]`；markPoint 优先 `{xAxis,yAxis}`；markArea 阴影超窗静默裁掉，须动态重建窗口。
- **json.dumps allow_nan=False 报错**：分析里有 NaN 先 clean() 递归转 None 再 dump。
- **模块级大段 f-string + 函数内同名变量会互相覆盖**（全局 dd40/fw40 被 per_tk_summary 遮蔽→KeyError），函数内变量加前缀规避。
- numpy int 键存 JSON 变 float 字符串 '0.0'，`.get("0")` 取不到，读取时 int(float(k)) 转回。
- 腾讯 *240* CSV 时间带 +08:00 时区，与 naive 匹配用 "%Y-%m-%d %H:%M" 前缀比对。
- Git Bash 无 sleep。playwright 高层 API 在 Chrome CDP 受限，用 chromium.launch({executablePath})。

## 脚本索引（重要报告）
- 回测：macd_backtest.py / run_all.py；报告 build_report.py / build_compare_report.py。
- **横盘突破（08-21）**：gild_abbv_breakout.py → reports/11。Donchian N=20+shift(1)；突破=close 上穿前日上沿+涨≥2.5%；横盘=前60日触上下沿带各≥2次+带宽比∈[5%,25%]；30日合并。50笔 T+20 +3.05%/66%（中位+4.3%）；2016 最差、2020 最好。
- **周线转正→4h超买（08-21）**：weekline_ob_{analyze,ctrl,window,export}.py + build_weekline_ob_report.py → reports/12_周线超买。事件=周线 MACD hist 负转正；超买=转正后2周窗口内 4h RSI14≥70（t0）。**结论：转正当周超买仅 28.6%（vs 对照 27.1%，前提不成立）；放宽 2 周窗口 → 64.3%（当周16/次周17/第3周3）。t0 后 40 根 4h：maxDD 中位 −3.65%(p90 −0.67%)，回 t0 收盘中位 1.5 根，40 根内新高 97.2%，期末 +3.43% 胜率60%。对照(n=144) −3.66% 无显著差异。当前 GILD=8/6 转正第2周经典超买点。**
- **板块破位×龙头支撑共振（08-21）**：djia_sector_support.py + djia_sector_support_extra.py + build_djia_sector_report.py → reports/13_道指板块支撑。口径：ETF swing-low 分形 OLS 上升趋势线(线龄≥42日/R²≥0.7)收盘首破 × 个股同日触及≥2月支撑(120日最低 or MA50/100/200)。n=62：T+1 62.9% 胜率、T+5 盲点(53%)、T+10 +1.42%/69.4%、T+20 +2.23%/71%；结局双峰 V反40% vs 击穿39%。**最有效过滤=ETF 破位日量能（平量 T+10 胜率81% vs 放量54%）；VIX 20-30 反弹最好、VIX<20 阴跌击穿率最高；XLF 击穿率62.5% 最差；止损=支撑下方2%+持有到期期望最优。**
- **事件研究（08-20）**：event_3pct_analyze.py → reports/10。adj_close 日涨≥3% → fwd1/5/10；分制药/生科池；10日冷却 + 小涨日/非事件日双对照 + 超额（SPY/XLV/IBB）分档分年。
- 相关性/对比：ibb_gild_corr.py / ibb_top10_corr.py / ceg_vst_compare.py / vst_utes_corr.py / wuxi_bigpharma_corr.py / steep_ko_pm_mo.py / steep_banks.py / steep_banks_bear.py / ibb_amgn_vrtx 系列。

## 事件研究方法（reusable）
流程：定义池子 → load adj_close → pct_change 算 ret → fwdN = shift(-N)/close−1 → mask evt → 需 fwd10 非 NaN → 对照=非evt/小涨 → **超额须把基准的 fwdN（不是价格）merge 后相减** → stats(n, mean, med, win%, std, p25/p75, t检验, 胜率二项近似)。池子按波动分组避免高波动主导。稳健性加 cooldown 剔除重叠。**报告评审规范（见用户级 skill quant-report-review）**：独立性假设最易高估（聚类/去拥挤日）、超额=α 须市场模型、幸存者偏差要披露、后验切类标"样本内"、显著性数字一律视作上限。

## 关键结论（2026-08）
- **药明康德**：日收益相关 vs 5 大药企 0.01-0.04、vs IBB/XBI 0.10-0.12 → **药明=全球研发外包景气代理，≠美国大药企销售代理**；2026-02 以来 +80.4% vs 大药企 +10.6% 完全独立；**药明强≠大药企强**。
- **IBB/GILD/AMGN/VRTX 三方**：IBB×GILD 0.576（分界后 0.515）；AMGN×VRTX 0.482/0.518。AMGN=利好脱钩、VRTX=贴板块弱弹性(β0.93)、GILD=利空脱钩。前十大前3净拖累，引擎=NTRA/ILMN/RVMD+中小市值；ALNY 最大反向(超额−46.4pp)。
- **GILD 2/10 Q4 窗口**：财报前 1/5→2/11 独自+31.7%（个股α，2/11 新高$155.39）→ 财报后 −13.1%；催化 Yeztugo+上调，回落=指引保守。与 8/4 Q2（板块主升浪 GILD 跑输）形态相反。
- **CEG vs VST**：2022 以来打平（+597.7% vs +611.7%）；2026 YTD 双杀（−22.6% vs −10.1%）；相关 0.70/60日 0.79。CEG=AI 电力定价锚+稀缺资产；VST=弹性+性价比+回购。**同一仓位两种表达，同时持有=加杠杆非分散**。
- **VST×UTES 5 阶段**：β 0.84→2.41，α 全在低相关期赚（S3 超额+256.3pp），高相关期只剩 β 放大；2026 回调解剖：VST 跌盈利质量 maxDD −25.1%，CEG 跌政策+估值 −35.2%。
- **US2Y弱+US10Y强陡（08-18）**：50 年仅 6.3% 月份满足，显著版仅 1998-10/2008-09~10 两例；消费股整体无防御优势（KO +0.5% vs SPY +1.3%），危机型深陡例外（B1 KO +2.8% vs SPY −6.4%）。报告 06。
- **IPP 8/18 大跌（08-19）**：TLN −11%/NRG −5.6%/CEG −4.1%/VST −3.8%；板块超额 SPY −5.44pp；60日β1.22 只能解释 −0.82% → **残差 −5.29pp=叙事再定价**；背景=板块已阴跌一年非新趋势起点。报告 07。
- **银行×走阔（08-19）**：走阔方向本身 R²<1% 不可靠；**形态决定一切**——加息陡 bank3 +1.75% vs SPY +0.47%（最强）、熊陡略胜、牛陡跑输（衰退担忧压过息差）。当前 2026-08 slope 51bp=长端领涨型，偏利好但 8/18 提醒斜率急升伴波动。报告 08。

## 已知局限
- 回测样本小（hold5=33）、未扣成本；事件研究分阶段 n<100 稳定性弱；池子仅现存大票有幸存者偏差。