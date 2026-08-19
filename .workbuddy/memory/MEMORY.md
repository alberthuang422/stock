# MEMORY.md —— 股票分析项目长期记忆

> 项目：MACD 回测 + 标的间相关性分析 + 个股财报/估值研究

## 数据与拉数
- 目录：data/<ticker>/、scripts/、reports/（HTML）、results/；.workbuddy/ 勿动。
- **Yahoo 拉数（唯一可靠）**：本机 Chrome CDP。后台启动 Chrome 二进制（--remote-debugging-port=9222 --user-data-dir=/tmp/wb-chrome-profile --no-sandbox --disable-gpu --no-first-run about:blank，run_in_background=true）→ playwright-core connectOverCDP → goto query1.finance.yahoo.com/v8/finance/chart/{ticker}?...&interval=1d&events=history&includeAdjustedClose=true → body.innerText 拿 JSON。requests 直连 403。
- **FRED 可直连**：`https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2`（/DGS10/...）curl 即可，无 403。缺失值读后 `pd.to_numeric(errors="coerce")` + dropna。
- venv python（有 pandas）：/Users/alberthuang/.workbuddy/binaries/python/envs/default/bin/python。

## 回测规则（用户确认口径）
水下金叉(DIF<0,DEA<0) → 金叉后3日内收盘上穿 EMA10&EMA20（严格无容差）→ 站稳 y=3/4/5 天（允许1天跌破次日收复）→ 买点=（金叉前10日盘整最高价+确认日EMA20）/2 → 30日内首次回踩(low≤买点)成交，未回踩=错过；收益金叉日收→T+N、买点→B+5/10/20；10日内多次金叉合并计1次。

## 核心发现（回测）
- 信号作过滤器有效：hold5 T+5 胜率 IBKR 52.7%→84.8%（10只均 56.5%→88.2%）。
- 等确认+回踩后 T+5 胜率缩水（75.8%→51.5%）；但 T+20 72.7% 反超金叉日 66.7% → 回踩买应持 20 天。
- 最差年份 2024（22%/−3.33%）、2018、2016；2017 最好 88%。信号"急跌后修复"最有效、"缓跌阴跌"易错。

## 用户偏好
- 严格口径：不要股息/容差缓冲；红涨绿跌；K 线成交点紫菱形（5日盈利）/黑菱形。
- 报告浅底深字研报风 + ECharts；交付前必须过 SSR 渲染测试（node --check 不够，用 chromium.launch executablePath 本机 Chrome 渲染）。
- 对照分析默认窗口 2025-09 起；超额分四档（分界前/后/2026分界前/2026以来）全给。
- 爱刨根问底：相关性→跷跷板→相对强弱→贡献归因→剔除归因，每层量化。
- **财报类问题先跟用户确认财报期**（曾把"财报"默认理解成 8/4 Q2，实际指 2/10 Q4）。

## 踩坑
- **美股历史点位分析必须用 adj_close（复权）口径，与用户看盘软件（腾讯自选股等）对齐**：未复权 close/high 会让历史高点偏高（SBUX 2021-07 高点未复权 $126.06 vs 复权 $111.54，差额=累计派息 ~$11.5/股）；复权后关键点位（高点/低点/突破日）全部变化，距前高空间判断会严重失真（-14.6% vs -3.5%）。Yahoo CSV 同时含 close 与 adj_close，分析脚本默认读 adj。PE/EPS 等估值指标基于未复权价÷EPS，不受影响。
- connectOverCDP 渲染报 "Browser context management is not supported"（拉数据仍用 CDP；渲染测试用 chromium.launch）。
- fetch 脚本必须放 scripts/ 下（/tmp 会因 __dirname 把 CSV 写到 /private/data）。
- itertuples 的 row.date 是 Timestamp 不能调用；json.dump 遇 numpy 先 int()/round()；resample("ME").corr() 不存在，用 groupby(pd.Grouper(freq="ME")).corr()；resample("ME").last() index 是 Timestamp 不是 Period。
- **Chrome CDP 启动**：`open -a "Google Chrome" --args` 激活已有实例参数不生效，必须二进制直接启动。
- data/<ticker>/ 若含 BATS_ 前缀旧文件，glob 先匹配干扰，load_stock 时过滤。
- Python f-string 嵌入大段 JS（单花括号）SyntaxError，用普通三引号 + @@PLACEH@@ + .replace()。

## 脚本索引
- 回测：macd_backtest.py / run_all.py；报告：build_report.py / build_compare_report.py。
- 拉数：fetch_yahoo_cdp.cjs（可用模板）；新 ticker：复制改 TICKERS/P 起止。
- 相关性/对比：ibb_gild_corr.py / ibb_top10_corr.py / build_*_report.py 系列 / wuxi_bigpharma_corr.py / fetch_wuxi_bigpharma.cjs / ceg_vst_compare.py / fetch_ceg_vst.cjs / vst_utes_corr.py / fetch_utes.cjs / build_vst_utes_report.py / fetch_ko_pm_mo.cjs / steep_ko_pm_mo.py / build_steep_report.py / test_render_*.cjs。
- 产物：results/ 数据、reports/ 报告。

## 关键结论（2026-08）
- **IBB×GILD**：全期 0.576 / 分界(2026-02-01)后 0.515（Fisher p=0.30 不显著）；分界后 IBB +13.85% vs GILD −3.17%；β 0.62→0.64 = 个股事件脱钩。
- **AMGN×VRTX**：全期 0.482 / 分界后 0.518；分界后 AMGN +20.5% vs VRTX +7.2%，β 降残差降 = VRTX 跟涨不足非脱钩。
- **三方**：AMGN=利好脱钩；VRTX=贴板块弱弹性(β0.93 跑输 −6.7pp)；GILD=利空脱钩。
- **前十大**：前3（AMGN/VRTX/GILD）净拖累（剔除后 IBB +16.2% vs +15.0%）；引擎=NTRA/ILMN/RVMD+前10外中小市值；ALNY 最大反向（相关 0.32、超额 −46.4pp）。
- **GILD vs ETF**：R² XLV 26.2%（分界后 33%）> IBB 24.5% > XBI 8.5%；分界后 β XLV 0.94 / IBB 0.64 / XBI 0.27。
- **GILD 2/10 Q4 窗口**：财报前 1/5→2/11 独自 +31.7%（板块横盘）=个股 α；2/11 新高 $155.39；财报后 2/17→3/27 −13.1%。催化=Yeztugo+UBS/Citi/BMO 上调；回落=指引保守+利好兑现。**与 8/4 Q2（板块主升浪、GILD 跑输）形态相反**。
- **药明康德（2026-08-16）**：日收益相关 vs 5 大药企 0.01-0.04（R²<0.5%）、vs IBB/XBI 0.10-0.12。**药明 ≠ 美国大药企销售景气代理，= 全球研发外包景气代理**（美国收入 72%、在手订单 +25.2%、TIDES +44.3%）。2026-02 以来药明H +80.4% vs 大药企均值 +10.6% = 完全独立行情。**反向警示：药明强≠大药企强**。BIOSECURE 路径：2024-03 参议院版 −9.7% → 2024-09 众议院 +4.9% → 2025-12 NDAA 签署 → 2026-06-08 正式列名 +3.2%（钝化）→ 2026-08-07 初步禁令 +2.7%。跨市场：美股 biotech 领先药明 1 交易日（lag −1 相关 0.18）；A/H 相关 0.825。
- **CEG vs VST（2026-08-16）**：2022-01 以来几乎打平（+597.7% vs +611.7%）；2026 YTD 双杀（CEG −22.6% vs VST −10.1%，XLU +4%=个股杀估值）；日收益相关 0.70、滚动 60 日 0.79。**CEG=AI 电力定价锚+稀缺资产**（21 反应堆、三里岛 PPA、净利率 9.1% vs 4.2%、负债 67% vs 87%）；**VST=弹性+性价比+回购**（PPA 3.8GW、前瞻 PE ~18x、2026 EBITDA +22%、股本 −30%）。**同一仓位两种表达，同时持有=加杠杆非分散**。
- **VST × UTES 5 阶段**：UTES 本质=被发电商重塑的公用事业 ETF（前三大 CEG/VST/TLN ~31%）；自包含效应：V×U 0.630 vs V×X 0.433（+0.20 重仓溢价）。S1 板块成员 0.50/β0.84 → S2 风暴 0.54/β0.99 → S3 叙事发酵 0.51/β1.15（VST +289.6% vs UTES +33.3% 超额 +256.3pp，低相关期赚走全部 α）→ S4 主升浪 0.89/β2.41 → S5 回调分化 0.83/β1.84。**β 0.84→2.41，α 在低相关期全赚，高相关期只剩 β 放大**。
- **2026 回调解剖**：VST 最大回撤 −25.1%(5/19) vs CEG −35.2%(7/1) vs UTES −11% vs XLU −9.1%；两者下跌均几乎全是个股残差。VST 跌盈利质量（3/4 季度 miss、套保浮亏、D/E 6.01）；CEG 跌政策+估值（PJM 上限提案、Calpine 整合、指引保守、35x 起点）。形态：CEG 集中急杀、VST 多段阴跌。
- **US2Y 弱 + US10Y 强陡峭化（2026-08-18）**：50 年仅 38/601 月（6.3%）满足；显著版（2Y≤−10bp & 10Y≥+10bp）仅 1998-10、2008-09~10 两例。消费股整体无防御优势（KO +0.5%/MO −0.6%/PM −0.7% vs 标普 +1.3%）；危机型深陡例外 B1 档 KO +2.8% vs 标普 −6.4%（1998-10 KO +20.1%）。机制：10Y 升→贴现率升→长久期估值承压；危机时防御资金流入压过估值压力。报告 reports/06_steep_ko_pm_mo/steep_ko_pm_mo_report.html。
- **IPP 板块 8/18 大跌（2026-08-19）**：TLN −11.0%（量比 3.1x）/ NRG −5.6% / CEG −4.1% / VST −3.8%；板块等权 −6.12%，XLU −0.36%、SPY −0.68%，**超额 SPY −5.44pp**。三层归因：① 30Y 5.32%+（2007 来最高）+ 美伊/油价 → 长端利率飙升；② AI 电力叙事集体撤退（XLU 横盘 vs IPP 普跌=主题挤兑）；③ TLN 财报后目标价连环下调（RJ 463→449、OpCo 440→400）+ $9.84 亿 shelf + 降级 Hold。β 分解：60日 β 1.22 只能解释 −0.82%，**板块残差 −5.29pp = 叙事再定价**；个股残差 TLN −9.7 / NRG −5.1 / CEG −3.4 / VST −3.0。罕见度（2025 来分位）：TLN 0.7% / NRG 3.7% / CEG 8.1% / VST 10.3%。**背景 = 板块 2025-09~10 见顶后已阴跌一年（距 52 周高 NRG −37% / VST −36% / CEG −34% / TLN −29%），8/18 不是新趋势起点**。报告 reports/07_ipp_drop/ipp_drop_0818_report.html。

## CDP 拉数规范（2026-08-19 验证）
- **Chrome CDP 必须 `run_in_background=true` 启动**（sandbox Bash `&` 后台启动会被 shell 退出回收）。命令：`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/wb-chrome-profile --no-sandbox --disable-gpu --no-first-run about:blank`
- **后续拉数脚本必须 `dangerouslyDisableSandbox=true`**（sandbox 内的 Bash 连不上 localhost:9222）。
- **playwright 高层 API 在此 Chrome 模式受限**（`browser.newPage()` 报 `Browser context management is not supported`），**改用原生 CDP**：PUT `/json/new` 建 tab → WS `Page.enable` + `Page.navigate` → sleep 5-7s → `Runtime.evaluate document.body.innerText` → `PUT /json/close/<id>`。模板 `scripts/fetch_ipp_power_cdp.cjs`（Node 22 内置 WebSocket，无需 npm 依赖）。**新版 Chrome `PUT /json/new?url=...` 的 url 参数会被忽略**，必须建 tab 后再 navigate。

## 已知局限
- 回测样本小（hold5=33）、未扣成本；药明相关性 R²<0.5% 样本 2018-12~2026-08（n=1833）；分阶段 n<100 统计稳定性弱。
