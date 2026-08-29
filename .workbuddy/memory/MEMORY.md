# MEMORY.md —— 股票分析项目长期记忆

> 项目：MACD 回测 + 相关性分阶段分析 + 个股财报/估值/景气度研究
> 逐日明细 `.workbuddy/memory/YYYY-MM-DD.md` ｜ 脚本 `scripts/` ｜ 报告 `reports/编号_中文名/`
> **报告检索：README.md 唯一入口（6 大分类索引），每出新报告必须同步更新 README 对应分类**
> **宏观利率常设入口：根目录 `宏观背景.md`（完整版 `reports/55_宏观背景/20260829_利率上行板块全景.md`）**

## 数据与拉数
- **币安 BTCUSDT 日线 `data/btcusdt/BTCUSDT, 1D.csv`**（用户提供 2020 起，含 RSI/MACD 列）。**7×24 资产（加密/外汇）收益铁律：ret 必须在原始全序列先算再 merge**——merge+filter 后重算 pct_change 会把周五→周一当相邻交易日污染收益（50 号实证同窗口 r 0.405 vs 0.463）；美股序列无此问题。
- **Yahoo 日线唯一可靠途径：本机 Chrome CDP**（端口 9222，模板 `scripts/fetch_banks_cdp.cjs`，`dangerouslyDisableSandbox=true`）；用完必须关闭 Chrome 窗口树 + cdp-proxy；macOS 启动命令与备注见 8/28 日志。
- **FRED 直连** `fredgraph.csv?id=xxx` 即可（DGS2/DGS10 等），缺失转 NaN dropna。
- **富途 MCP 关键限制（08-27 实证）**：技术指标**筛选**类参数一律 `invalid parameter`（连 MACD_DIF>0 都报）；但指标**取回**正常（name=52=RSI动态、period=11=日线、indicator_params=[14]）。缩放：市值 ×1e3（value/1000=美元）、PE/PB ×1e5、股息率 ×1e3、**RSI ×1e3**。期权：expiration_date→option_chain→逐合约 quote（OI 在 option_ex_data.open_interest）。返回过大自动落盘 tool-results/*.txt 用 python 解析。
- 蓝筹池：`data/blue_chips.csv`（73 只，列 ticker, sector）。venv：`C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`；node 22。
- **RBOB 口径（8/29）**：分析汽油趋势一律用 RB1!（连续主力），单月合约（如 RBU2026）受基差/换月扭曲；换月日有假跳空，做收益/回测需剔除或后复权（ratio=P_new/P_old 从最新合约向旧锚缩放）。

## 回测/方法要点
- **图表单位陷阱（历史坑）**：关联序列 ×100 存百分数（corr 字段），**build 报告注入 ECharts 时 ÷100 还原**；交付前跑 `scripts/_scan_corr_units.py`。
- **T+N 一律指交易日数**（非自然日）：T+5=事件后第 5 个交易日，fwdN=N 交易日未来收益，用交易日对齐，绝不用自然日相减。
- 事件研究流程：池子→adj_close→pct_change→fwdN→mask→对照→**超额=基准 fwdN（非价格）merge 相减**→stats（n,mean,med,win%,std,p25/75,t,二项近似）。独立性最易高估，显著性一律视作上限。
- 历史点位用 adj_close；回报统计一律百分数（×100）；json.dump 前 clean() 转 None、numpy 转 int；ECharts markArea 二维数组；f-string 嵌 JS 用 @@PLACEH@@+.replace()。
- 水下金叉→3 日内上穿 EMA10&20→站稳→买点=(金叉前 10 日盘整高+确认日 EMA20)/2→30 日回踩成交；hold5 胜率 52.7%→84.8%，**但 T+20 反超（72.7%）→ 回踩买应持 20 天**。
- 相关性以 **60 日滚动为主口径**（13/30 日仅辅助，13 日单点 SE=0.32 被实证否定）；显著性三档 sig(p<0.01)/edge(0.01≤p<0.05)/no(p≥0.05) + p 值列（"超带即显著"在 n 小时会虚标）。

## 用户偏好（长期规则）
- **Git 提交**：格式 `yyyy-mm-dd  msg: （≤50字）`；按主题分开 commit，不混无关内容；**默认只本地 commit，用户明确要求时才 push**；用 `git -c user.name="Makemoney" -c user.email="alberthuang422@gmail.com"`。
- **GitHub 推送走 SSH 443**（22 端口直连超时，`~/.ssh/config` 已配 `ssh.github.com:443`）；push 命令仍需 `dangerouslyDisableSandbox=true`。
- **交付必须产物展示（08-29 晚设定）**：HTML 报告/网页类交付完成后必须 `present_files` 展示并自动打开预览；CDP 无头渲染验证（canvas 数+无 pageerror）作为兜底。
- **术语一律悬停浮窗，禁用速查表（08-29 设定）**：正文所有专业术语（含不常见的 onset/SST/ENSO/β₁₀）必须虚线下划线+悬停白话解释，标注偏过不偏漏。实现：TERMS 词典 + annotate_terms() + `.term`/`.termtip` CSS + 浮窗 JS；**`_BLOCK_RE` 必须带捕获组否则 re.split 丢 script/style 块**；按 `_TAG_SPLIT_RE` 分片只标文本节点。
- 严格口径：不要股息/容差缓冲；**红涨绿跌 + Okabe-Ito 色弱安全（叠线型/符号，用户绿色弱）**；报告浅底深字研报风+ECharts；对照默认窗口 2025-09 起、超额分四档；报告目录中文名「编号_中文名」；财报问题先确认财报期。
- **相关性报告 R 与 β 同列**；**每个表格带「参数图例」**（r/ρ/显著带/β/R²/涨跌幅含义，后续表简注"同前表"）。
- **README 登记前先 `ls` 校验文件落地**（曾死链）；交付不附图（SSR 测试仅验证）。
- 高权限自我约束：**不做删除/clean/reset 等破坏性操作**，全部改动可 git 回滚；事件明细超长表另起独立选项卡；Token 优化（build 只 print written、JSON 瘦身）。
- 用户"空仓"口语=做空仓位（short）；"危险/逼空"须先量化再定性；板块问题优先逻辑推新标的，避免被持仓/历史报告锚定。

## 关键结论（2026-08）
- **SOFI/XYZ×BTC（50 号）**：全期 r 0.303/0.284 弱-中相关；近波非 BTC 驱动（逐日 r=0.21 不显著、2026Q3 BTC +31.6% vs 二者 +2~8%）；季度 r 渐进抬升（2023 0.02~0.27 → 2026 0.33~0.56）。**分阶段口径：按日历季度**。
- **景气度（21/22）**：大药企口径（销售盈利驱动）五年 2022 -4/2023 -1/2024 +8/2025 -1/2026 +9 深V；小 biotech 口径（融资→并购→临床）2022 -14/2023 +4/2024 +4/2025 +8/2026 +11，与药企口径方向相反；XBI×并购金额 r=0.494。
- 药明：vs 大药企 0.01-0.04、vs IBB/XBI 0.10-0.12 → 研发外包景气代理，≠美大药企代理。
- **IBB×GILD 0.576**；引擎=NTRA/ILMN/RVMD+中小市值；ALNY 最大反向。**IHI×XBI（23）**：2026-02 后脱钩 0.652→0.249（Fisher z=6.34），XBI +78% vs IHI −9%。**工具链条（24/25）**：对 XBI 脱钩对 IBB 韧；业绩传导时滞 3-4 季度，本轮弹性主升段预期 2026Q4-2027。
- **CEG vs VST**：相关 0.70，同时持有=加杠杆非分散；VST β 0.84→2.41 成长股化，2026 回调节奏 VST 盈利质量 vs CEG 政策+估值。
- **US2Y弱+US10Y强陡**：50 年仅 6.3% 月份，消费股无防御优势（危机型深陡例外）；银行×走阔 R²<1%，形态决定一切（加息陡最强）；资管（30 号）严格熊陡 +5.71%/81.8% vs 大幅走阔 −6.8%（幅度代理危机烈度）。
- **57 号农业股（8/29）**：El Niño 非有效信号（22 次月频全不显著）；真信号在 **La Niña 化肥链强正**（CF T+12 8/8 +67.5pp）；**利率上行化肥/农机反顺风**（MOS β10 +0.075 p=0.001，控制 CPI 不变）；DAR 长短端相反=曲线平坦化受益；**强 El Niño 越强越弱**（期末负但 73% 窗口内先冲高，快钱窗口=onset 后 6 个月内）；2026 抢跑已发生（1-3 月主升浪、CF 峰值 +72.5pp），宏观托底（供给收紧）非 2015 双逆风。
- **56 号 CCL RSI**：越跌越买只在 <30 档有效（+3.70%/超额 +1.50pp），30-35 是陷阱（−0.18%）；近两年档位失效；与 MCD（防御股）正好相反。

## 报告索引（README 唯一入口；以下为高频引用锚点）
- 55 宏观背景（利率上行板块全景：传导三路径/受益受伤梯队/路径设定=温和加息 1-2 次）；54 宏观利率×六股（SOFI Δ10Y β=-0.24 唯一显著）；52 持仓组合技术面（SBUX/XYZ 压力区空头双档止损）；50 SOFI/BTC；49 MCD RSI 跌落买入（超额全≤0）；48 MCD 回吐= maxG−回吐；47 MCD maxG。
- 37 中期选举×波动；38 板块维度中期选举；30 资管×曲线陡峭化；31 蓝筹下沿支撑×周线EMA20；21/22 生物医药景气度；23 IHI×XBI；24/25 工具龙头+传导时滞；56 CCL RSI；57 农业 ESPO（含 交接文档）；51 MCD/SBUX×道指/XLY；53 金融科技财报日相关；42 VIX 低位×SPY；45 板块ER原型。