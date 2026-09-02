# MEMORY.md —— 股票分析项目长期记忆

> 项目：MACD 回测 + 相关性分阶段 + 个股财报/估值/景气度。脚本 scripts/（build_* 三段式：拉数→分析→构建），报告 reports/「编号_中文名」。
> **README.md 是唯一索引入口；新报告先落地文件再登记（标题+链接+一句话结论）。**

## 数据与拉数
- 币安 7×24 资产 ret 必须原始全序列先算再 merge（merge 后重算污染周五→周一，50 号实证）。
- **Yahoo 日线/盘中直连**（60 号实证，无需 CDP）：⚠️ **日线 range=max 返回月度采样假数据**（~302 行、日期全在月初），必须显式 `period1/period2`（如 1995→今）拉全量；⚠️ **4h 仅支持 range=2y（上限约 730 天）**，美股 2 根/日（ET 09:30/13:30），range=max 对 4h 无效。XAUUSD 无现货代码，用 **GC=F 黄金期货代理**。模板：scripts/fetch_macd_soxx_nvda_xau_qqq.py。
- **Yahoo 日线 CDP**：先 curl 探活 9222 复用；无实例则后台起 Chrome（`--remote-debugging-port=9222 --user-data-dir=Temp/chrome-cdp-xxx --no-sandbox --headless=new`）。**Windows Chrome 路径** `C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe`。fetch_*.cjs 原生 WS（建 tab→navigate→sleep→evaluate）。**收尾关 Chrome：reg 被策略禁用，用 PowerShell Get-CimInstance Win32_Process 按 CommandLine 关键字 Stop-Process**。增量补数模板 fetch_geo_cdp.cjs（只 append 新日期）。**尾 bar 体检**：成交量远低于常态=不完整 bar 须剔除（CL 08-27 25.6 万 vs 常态 360 万）。
- **Yahoo 直连 403 常态化（09-02 起，64 号 DAL + CVS×VIX 实证）**：requests/urllib/curl 带 UA 均被风控（返回中文验证页），Futu MCP 服务端 internal error 频发 → **备用通道①新浪美股日线** `https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php/var t=/US_MinKService.getDailyK?symbol=CVS`（JSONP，O/H/L/C/V 未复权全历史，SPY 与本地 Yahoo 六锚点价一致已验证；解析取 `var t=([...])` 的 JSON）**②CBOE VIX 官方** `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`（DATE,OPEN,HIGH,LOW,CLOSE，1990 起，比 Yahoo 权威——Yahoo VIX 个别日 close 与官方结算有出入如 08-26 15.69 vs 15.21）。SPY 等可复用本地全量（git 有历史）。
- venv `...python\envs\default\Scripts\python.exe`（含 scipy）。富途 MCP：期权 OI 用 quote_stock_quote；选股器技术指标筛选报 invalid parameter、取回可用；口径 市值×1e3、PE×1e5、RSI×1e3。
- **富途 MCP 通道（09-01）**：futu-mcp 是远程 OAuth 端点，token 2h 过期但 **refreshToken 可自动续期**（授权一次撑一周+，expiresAt 毫秒）；失效时重跑 Temp/futu_oauth_reauth.py（需浏览器授权，python urllib 不支持 https 走 curl 子进程）。**Yahoo/stooq 挂掉时用 Futu over-HTTP**：curl+Bearer → initialize 抓 Mcp-Session-Id → notifications/initialized → tools/call（SSE data: 行）；quote_history_kline 只传 {symbol,end,num}（ktype 显式传会 schema 报错）；**0.25s pacing + 指数退避**可 354/354 全成；热门度 sort featured_property=5214（综合）×1e5，分页 next_key 在响应顶层。
- 蓝筹池 73 只：data/blue_chips.csv。
- **项目级 skill `support-resistance-levels`** 在 `.workbuddy/skills/`，CLI `python support_levels_demo.py TICKER --months N`（默认 swing 3 K 线 ≈ 周级），4 步算法（swing+ATR 聚类+评分+破位检测），调用 `find_pivots(vals, n=40, kind=...)` 可把窗口扩到 40 根 ≈ 2 月级。**用户说"用 skill"时先查 `.workbuddy/skills/` 是否有现成**（65 号复盘教训）。

## 方法口径（铁律）
- **图表单位陷阱**：分析脚本 corr ×100 存百分数，build 注入 ECharts 必须 ÷100；交付前跑 scripts/_scan_corr_units.py。
- T+N=交易日；超额=减基准 fwdN；json.dump 前 clean()。
- **60 日滚动主口径**（13/30 仅辅助）；显著性三档 sig/edge/no + p 值列；**R 与 β 同列**；表格带参数图例；**术语一律悬停浮窗、禁速查表**（TERMS 词典 + annotate_terms，_BLOCK_RE 单捕获组）；红涨绿跌 + Okabe-Ito 叠符号线型；浅底研报风+ECharts；超长明细独立 tab。
- **pandas 坑（08-30）**：int 索引 Series 赋给 date 索引 DataFrame 全 NaN，必须 `.values` 按位置对齐（monitor 曾产出全 None）。
- **回测坑（08-31，60 号）**：①收益明细已是 % 后 summarize 勿再 ×100（产生双倍缩放）；②拆股标的（NVDA 2024 1:10）收益必须用 adj_close 后复权价结算，信号用原价；③术语词典定义文本会被二次注释成嵌套 span → annotate_terms 先保护 data-tip 内容再注释。
- 交付必须 present_files 打开预览；不附渲染截图；git 本地 commit `yyyy-mm-dd  msg: （≤50字）` -c user.name=Makemoney，push 走 ssh 443 且需用户明确要求。

## 关键结论（压缩）
- 50 SOFI/XYZ×BTC 弱-中相关（r≈0.3、R²<10%），2026Q3 近波非 BTC 驱动；分阶段按日历季度。
- 21/22 生物医药景气双口径（大药企 vs 小 biotech 方向可相反）；23 IHI×XBI 2026-02 脱钩（0.666→0.249）；24 工具龙头对 XBI 脱钩、WAT 最韧 DHR 最惨；25 工具业绩滞后 3-4 季度，弹性主升段 2026Q4-2027。
- CEG/VST 相关 0.70 同仓两表达；US2Y 弱+US10Y 强陡罕见；银行×走阔形态决定一切；30 资管大幅走阔重挫。
- 57 农业：厄尔尼诺非信号、拉尼娜化肥链强正（CF T+12 8/8）；利率上行化肥/农机正敏感；强厄尔尼诺"越强越弱"快顶（2023 模板 T+2.7，成因=快爬坡×种植季抢跑×档位）；交接文档含快顶模板。**57附 绝对收益版（08-30）**：拉尼娜 CF T+12 +77.1% vs SPY+8.1%；强厄尔尼诺三档 T+24 中位期末 弱+35.5%/强+21.6%/超强−3.4%（绝对亏损仅超强档）；**⚠️ 主报告 p 值 bug**（手写 t CDF 45 组合错 42 个，scipy 重算拉尼娜 CF 月均 +5.79% sig）主报告 index.html 未修待确认。
- **57/58 追加·2026 厄尔尼诺研判（08-30 会话）**：ONI 至 MJJ26 +1.39 未达超强但爬坡史上最快（超 1997/2015 同期）；类比=海温像 1997、形态像 2023、宏观 β 像 2009。CF 收盘新高止于 03-30，残差分解（1.08×XLE）：拉尼娜最强期残差为负、3 月单月 +13.7pp 化肥脉冲后衰减至 +6.3pp；7 月 onset T+1 抢跑 8 月即回吐。**历史厄尔尼诺 CF−XLE（T+24）：2006 +743pp / 2009 +35 / 2015-16 −34（CF −54.8% 跑输 SPY 66pp，唯一超强先例）/ 2023 +48 / 本轮仅 +9.5pp** → 历史正超额皆非能源主导（"以前厄尔尼诺 CF 有超额"=均值假象，6 窗口 4 负），本轮首次能源锚供超额大头、非能源腿上市以来最弱；超强确认则上调 2015 剧本。判定节点 9 月初 ASO / 10 月初 SON。DAR 已见顶信号最明确（08-18 后 7 日 −10% 脱锚）。
- **58 CF/DAR 地缘溢价脱钩（08-30，2025-11 起；双口径，详见交接文档）**：**CL 口径**——油价≥3% 大跌 CF 0 跟跌/DAR 1 次弱跟跌；3 月起 CF×CL −0.32、DAR×CL −0.26 显著负。**XLE 口径（追问补算，推翻"脱钩独立走"）**——CF×XLE +0.58、DAR×XLE +0.44（3 月后 +0.59/+0.52），控 SPY/XLF/XLI/XLV 后 b_XLE=+1.08(t=9.4)/+0.70(t=7.7) 稳健；**XLE×CL 全期仅 −0.07 = 能源股已与油价脱钩**。→ 正确表述：**脱的是油价锚、不是能源板块锚**，CF 对 XLE 的 β≈1.1。判定三不受影响：能源锚新高 34 天 CF 同步 26%（引擎切换）/DAR 62%。区间 CF+48.9%/DAR+87.2% vs CL+22.8%/SPY+12.8%。待办：主报告仍 CL 单口径未改；NG 天然气链条属推断未核实。
- **60 MACD 死叉×4hRSI超卖 买入回测（08-31，SOXX/NVDA/XAUUSD/QQQ）**：合并仅 20 信号（2 年 4h 样本），T+1 胜率 70%/T+5 73.7%/T+10 68.4%/T+20 掉回 52.6%——捕捉短线反抽非趋势反转。**对照组：仅日线死叉 n=87、T+5~T+20 胜率 70-72%、p<0.01 显著 → 主效果是死叉本身，4h RSI 30-35 过滤砍 8 成样本且仅边缘显著**。黄金信号最稳（7 信号 T+1 7/7）。**当前快照（08-31 收盘）：XAUUSD 正处信号窗（日线刚死叉+4h RSI 32.4）→ 09-01 开盘即买点；SOXX 水下接近未触发**。详见 results/60_*.json。
- **56 号 CCL 深分 + DCA（09-01）**：①**最优组合 = RSI 28-30 × dd60≤-30%**（9 次 fwd20 中位 +24.5%/胜率 88.9%/超额 +18.3pp）；d2m≤3"反弹快"=下跌中继（12 次 fwd20 −8.5%/胜率 8.3%）。②**RSI 30 线无分层能力**（控回撤后 <30 vs ≥30 打平 +10.3% vs +10.7%），真 alpha 是回撤深度；唯一假信号=深跌×RSI 30-35（n=17 中继，fwd20 −4.2%），深跌×35-40 反而极好（n=26 +13.6%）。③**RSI<30 等额定投**：末日结算亏钱（胜率 15%）、T+20 转正（中位 +4.04%）但**资金加权仅 +1.08%**（深熊吸走 32% 资金）、T+60 +9.1% 更好；RSI 30 作 DCA 终止线太早（2020 见底在 4 月）；等权中位数受 1 天假信号污染需资金加权复核。脚本 scripts/ccl_rsi30_dca.py + sub30_deep.py。
- **CCL 无选举行情（09-01）**：CCL×SPY 全期 r=0.565 无脱钩，中期选举 6 次前 30 日平均超额 +0.1pp（近三轮牛市期全负：2014/2018/2022 = −2.9/−8.7/−6.4pp）——选举前走势=大盘 β 翻版。
- **CCL 债务横向对比（09-02 官方源核实）**：CCL 净杠杆 3.1×（公司口径，FY25 末 3.4×→Q2 3.1×）、总债务 $248.9 亿（半年 −$17.5 亿）、上半年利息 $577M（−20%）、客户存款 $90 亿新高、S&P/Fitch BBB-（Moody's 未跟随）。同业：RCL S&P 调整口径 2026E 2.6×/评级 BBB（2026-02-02 上调，高于 CCL 两档）、TTM EBITDA $73 亿已略超 CCL 全年指引 $70 亿；NCLH 5.3×（自报）才是真高杠杆。行业常态 3-4×。结论：CCL 偏高但已入投资级下沿，"相对 RCL 的杠杆折价"成立。**利率结构（09-02 Q2 10-Q 逐笔核实）：固定 84.6%（$216 亿）/浮动 15.4%（$39.5 亿，其中 SOFR 仅 $13 亿、EURIBOR $26 亿、均 0% floor）；US10Y+100bp 直接利息仅 +$13M/年≈EPS+$0.01 可忽略；到期墙 2028-08 $2.4B@4.0% 为首个大额，2026-27 仅 ~$1.3B；未提取出口信贷 $10.8B 提款时才定价。** **FY26 官方敏感性表（对调整净利）：yield±1%=±$204M ＞ 燃油±10%=±$145M（CCL 三巨头中唯一不对冲；RCL 60% 对冲后仅 $57M、NCLH ~$90M）＞ 除燃料成本±1%=±$114M ＞ 浮动利率±100bp=±$42M（官方印证前测 $39.5M）＞ 汇率±1%=±$27M。燃油 FY26 计划 $16.3 亿（2.8M 吨 @$524，含排放配额）占营收 ~6-9%（2022 高峰 17.7%）；效率 +5%/年对冲（2011 来省 18%）。需求(yield)＞燃油＞利率。**Q2 电话会（6/23）：2027 预订量价齐领先、欧洲 2027 量 +mid-teens @更高价、booking curve 史上最远、客户存款 $90 亿新高（未来 12 月容量 flat）；下半年 yield 指引 cc 从 2.75% 砍到 1.75%（地缘）→Q3 EPS 指引 $1.35 vs 共识 $1.42 砸盘 6-9%；FY26 EPS $2.22/EBITDA $7.11B。量价拆解：容量 +2.0%(全年 +0.9% 主动控量)/yield +2.2%(12 季连续纪录)/ticket +4.1%/onboard +7.5%/调整净利 +21%——麦当劳式"量平价升利更快"，载体=onboard 高毛利+私人目的地（Celebration Key/Half Moon Cay），机制=主动 price integrity 非被动涨价；风险=2027 加勒比供给 +27%×NCLH 激进促销。
- **SPY 对冲评估（09-01）**：11 月 VX 期货劣选（11/18 到期时点错配 + 无事件 −4050/合约 carry）；12 月 OTM10% put 劣选（盈亏平衡 −10.9% + theta 0.24%/月）；**主推 12/18 熊市价差 690/630（成本<0.5%、盈亏平衡 −10.5%）**；比较期货升水须与该期限正常 carry 比（contango 常态，不能直接比现货）。**Futu OAuth：refreshToken 可自动续期（授权一次撑一周+）**。

## 报告索引
- 宏观常设入口 `宏观背景.md`（利率上行×板块全景）；21-25 生物医药/工具链；30 资管；37/38 中期选举；50 SOFI×BTC；52 持仓；54/55 宏观利率；56 CCL RSI；57 农业 ENSO+利率；58 农业地缘脱钩；59 MOS/CF 分化；60 MACD 死叉×4hRSI 超卖回测；61 APO 资管深度；62 CCL 全面；63 SOFI×AFRM×SQ 相关性；64 DAL RSI 跌落买入。
- **65 随机 10 只美股阻力位** `reports/resistance_10stocks_20260902.html`（KKR/NRG/ACN/BG/XOM/NEE/ABT/SPGI/TROW/TDG，2023-01 至今，swing 40 K 线 ≈ 2 月级）。
- 富途热榜：`reports/hot354_rsi_eval_20260901.html`（RSI+板块透视+组合筛选）；每日 07:00 任务 f78907c8 → `hot_rsi_eval_YYYYMMDD.html`。
