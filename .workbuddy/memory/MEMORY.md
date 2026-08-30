# MEMORY.md —— 股票分析项目长期记忆

> 项目：MACD 回测 + 相关性分阶段 + 个股财报/估值/景气度。脚本 scripts/（build_* 三段式：拉数→分析→构建），报告 reports/「编号_中文名」。
> **README.md 是唯一索引入口；新报告先落地文件再登记（标题+链接+一句话结论）。**

## 数据与拉数
- 币安 7×24 资产 ret 必须原始全序列先算再 merge（merge 后重算污染周五→周一，50 号实证）。
- **Yahoo 日线 CDP**：先 curl 探活 9222 复用；无实例则后台起 Chrome（`--remote-debugging-port=9222 --user-data-dir=Temp/chrome-cdp-xxx --no-sandbox --headless=new`）。**Windows Chrome 路径** `C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe`。fetch_*.cjs 原生 WS（建 tab→navigate→sleep→evaluate）。**收尾关 Chrome：reg 被策略禁用，用 PowerShell Get-CimInstance Win32_Process 按 CommandLine 关键字 Stop-Process**。增量补数模板 fetch_geo_cdp.cjs（只 append 新日期）。**尾 bar 体检**：成交量远低于常态=不完整 bar 须剔除（CL 08-27 25.6 万 vs 常态 360 万）。
- venv `...python\envs\default\Scripts\python.exe`（含 scipy）。富途 MCP：期权 OI 用 quote_stock_quote；选股器技术指标筛选报 invalid parameter、取回可用；口径 市值×1e3、PE×1e5、RSI×1e3。
- 蓝筹池 73 只：data/blue_chips.csv。

## 方法口径（铁律）
- **图表单位陷阱**：分析脚本 corr ×100 存百分数，build 注入 ECharts 必须 ÷100；交付前跑 scripts/_scan_corr_units.py。
- T+N=交易日；超额=减基准 fwdN；json.dump 前 clean()。
- **60 日滚动主口径**（13/30 仅辅助）；显著性三档 sig/edge/no + p 值列；**R 与 β 同列**；表格带参数图例；**术语一律悬停浮窗、禁速查表**（TERMS 词典 + annotate_terms，_BLOCK_RE 单捕获组）；红涨绿跌 + Okabe-Ito 叠符号线型；浅底研报风+ECharts；超长明细独立 tab。
- **pandas 坑（08-30）**：int 索引 Series 赋给 date 索引 DataFrame 全 NaN，必须 `.values` 按位置对齐（monitor 曾产出全 None）。
- 交付必须 present_files 打开预览；不附渲染截图；git 本地 commit `yyyy-mm-dd  msg: （≤50字）` -c user.name=Makemoney，push 走 ssh 443 且需用户明确要求。

## 关键结论（压缩）
- 50 SOFI/XYZ×BTC 弱-中相关（r≈0.3、R²<10%），2026Q3 近波非 BTC 驱动；分阶段按日历季度。
- 21/22 生物医药景气双口径（大药企 vs 小 biotech 方向可相反）；23 IHI×XBI 2026-02 脱钩（0.666→0.249）；24 工具龙头对 XBI 脱钩、WAT 最韧 DHR 最惨；25 工具业绩滞后 3-4 季度，弹性主升段 2026Q4-2027。
- CEG/VST 相关 0.70 同仓两表达；US2Y 弱+US10Y 强陡罕见；银行×走阔形态决定一切；30 资管大幅走阔重挫。
- 57 农业：厄尔尼诺非信号、拉尼娜化肥链强正（CF T+12 8/8）；利率上行化肥/农机正敏感；强厄尔尼诺"越强越弱"快顶（2023 模板 T+2.7，成因=快爬坡×种植季抢跑×档位）；交接文档含快顶模板。**57附 绝对收益版（08-30）**：拉尼娜 CF T+12 +77.1% vs SPY+8.1%；强厄尔尼诺三档 T+24 中位期末 弱+35.5%/强+21.6%/超强−3.4%（绝对亏损仅超强档）；**⚠️ 主报告 p 值 bug**（手写 t CDF 45 组合错 42 个，scipy 重算拉尼娜 CF 月均 +5.79% sig）主报告 index.html 未修待确认。
- **57/58 追加·2026 厄尔尼诺研判（08-30 会话）**：ONI 至 MJJ26 +1.39 未达超强但爬坡史上最快（超 1997/2015 同期）；类比=海温像 1997、形态像 2023、宏观 β 像 2009。CF 收盘新高止于 03-30，残差分解（1.08×XLE）：拉尼娜最强期残差为负、3 月单月 +13.7pp 化肥脉冲后衰减至 +6.3pp；7 月 onset T+1 抢跑 8 月即回吐。**历史厄尔尼诺 CF−XLE（T+24）：2006 +743pp / 2009 +35 / 2015-16 −34（CF −54.8% 跑输 SPY 66pp，唯一超强先例）/ 2023 +48 / 本轮仅 +9.5pp** → 历史正超额皆非能源主导（"以前厄尔尼诺 CF 有超额"=均值假象，6 窗口 4 负），本轮首次能源锚供超额大头、非能源腿上市以来最弱；超强确认则上调 2015 剧本。判定节点 9 月初 ASO / 10 月初 SON。DAR 已见顶信号最明确（08-18 后 7 日 −10% 脱锚）。
- **58 CF/DAR 地缘溢价脱钩（08-30，2025-11 起；双口径，详见交接文档）**：**CL 口径**——油价≥3% 大跌 CF 0 跟跌/DAR 1 次弱跟跌；3 月起 CF×CL −0.32、DAR×CL −0.26 显著负。**XLE 口径（追问补算，推翻"脱钩独立走"）**——CF×XLE +0.58、DAR×XLE +0.44（3 月后 +0.59/+0.52），控 SPY/XLF/XLI/XLV 后 b_XLE=+1.08(t=9.4)/+0.70(t=7.7) 稳健；**XLE×CL 全期仅 −0.07 = 能源股已与油价脱钩**。→ 正确表述：**脱的是油价锚、不是能源板块锚**，CF 对 XLE 的 β≈1.1。判定三不受影响：能源锚新高 34 天 CF 同步 26%（引擎切换）/DAR 62%。区间 CF+48.9%/DAR+87.2% vs CL+22.8%/SPY+12.8%。待办：主报告仍 CL 单口径未改；NG 天然气链条属推断未核实。

## 报告索引
- 宏观常设入口 `宏观背景.md`（利率上行×板块全景）；21-25 生物医药/工具链；30 资管；37/38 中期选举；50 SOFI×BTC；52 持仓；54/55 宏观利率；56 CCL RSI；57 农业 ENSO+利率；58 农业地缘脱钩。
