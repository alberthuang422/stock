# 工作交接文档（2026-08-29 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/YYYY-MM-DD.md`，长期要点见 `.workbuddy/memory/MEMORY.md`，报告检索入口为 `README.md`（6 大分类索引）。

## 一、当日工作全景

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| 宏观 | Jackson Hole 2026（Warsh 首秀）× 持仓六股 | 讲话=拒前瞻指引+通胀首要→9 月加息概率 1/3→57%、2Y +8bp 至 4.31%；SOFI 双杀（-3.28% 资金成本+消费信贷+crypto）、APO 逆势 +1.66%（浮息信贷重定价）；ABBV 近免疫；**口径：盘中快照非收盘定价，8 月就业+CPI 是 9/15-16 FOMC 前决定变量** |
| 分析 | KO/SBUX 补充 | KO +0.79%=纯避险赢家（债券代理属性强于 ABBV）；SBUX +0.88% 系自身业绩动量（FY26Q3 超预期+连 4 季同店正）非利率**——52 号确认用户持 SBUX 空头，上方 107.5-110.5 压力区，止损激进 >110.5 / 稳健 >113.5** |
| 54 | 宏观利率背景 × 六股影响 | 6 月来利差扩张=供给/期限溢价驱动（10Y+22bp vs 2Y+5bp，长端贡献 84%），8/28 起切换为加息预期熊平；敏感性回归（2026 日频 n=162）**SOFI 唯一显著（Δ10Y β=-0.24 R=-0.30，近 60 日 β=-0.42）**，MS edge，其余 4 只不显著；**排序 SOFI≫MS>APO≈ABBV≈JNJ≈CSCO** |
| 55 | 宏观背景常设入口（承接 54） | 蓝筹池 73 只入背景文件；**利差五阶段**：1/2→6/30 收窄→8/18 扩张（峰值 0.52）→8/26 回吐→8/28 Warsh 熊平（2Y 4.29-4.31、10Y 持平、30Y 反跌）→前瞻 9 月初非农+CPI 分水岭；⚠️ 54 号图 y 轴 0.6 截断 1 月 0.74 峰值，55 已修 |
| 56 | CCL 当前 RSI 档位买入回测（改版两次） | 最终口径=49 号「区间跌落买入」：**越跌越买只在 <30 档有效（T+20 +3.70%/超额 +1.50pp/胜率 64.6%），30-35 档是陷阱（−0.18%/−0.33pp）**；本轮牛市 35-40 −3.0%/30-35 −3.5% 失效、<30 +11.49% 一枝独秀；当前 RSI 35.44 非买点，等 <30 档+企稳确认；与 MCD（防御股三档全正超额全≤0）正好相反 |
| 57 | 农业股 × ENSO 回测 + 利率敏感性（15 标的，多次追加） | ①El Niño 非有效信号（22 次月频全不显著，仅 DE 窗口 70-80% 胜率）②**真信号在 La Niña——化肥链强正**（CF T+12 8/8 +67.5pp、MOS +35.1pp）③**利率上行化肥/农机反顺风**（MOS β10 +0.075 p=0.001、CF +0.073 p=0.009，控制 CPI 不变；DAR 长短端相反=曲线平坦化受益）④强 El Niño **越强越弱**（弱档期末 +4.7pp vs 超强档 −40.7pp），但 73% 样本先冲高后回撤（快钱窗口 onset 后 6 个月）；⑤2026 抢跑已发生（1-3 月 CF 峰值 +72.5pp），宏观托底非 2015 双逆风 |
| 其他 | 黄金/BTC × Warsh 证伪 | 8 月同涨引擎=财政主导→YCC 预期叙事；Warsh 独立+通胀首要=证伪→黄金 −1.7%、BTC 破 7.7 万；BTC 跌幅温和因 NVDA +8.7% AI 缓冲（呼应 50 号：BTC 非宏观单一函数） |
| 其他 | 消费股 SBUX/MCD/MO/PM 利率敏感 | 四只全部 no（Δ10Y β 均 |<0.06|）——印证"消费股无防御优势"；讲话当日普涨=**避险轮动（事件日属性）≠中期利率敏感度**，两码事 |
| 其他 | GE/HWM 利率敏感工业股 | **GE Δ10Y β=-0.19 R=-0.36 sig / HWM -0.14 R=-0.29 sig**（区别于消费股钝感）；机制=久期+美元+航司融资；8/28 实盘 HWM −2.04% 验证；基本面主引擎仍航空景气，利率只是边际扰动 |
| 其他 | 四巨头 FCF vs JNJ/ABBV | 2026Q2 单季 FCF：MSFT +196 亿唯一符合 KOL；GOOG/AMZN 为负、META +17 亿；JNJ 净债/EBITDA 0.8x=满分避险；**ABBV 现金流顶级（TTM FCF ~200 亿）但净债 642 亿、净债/EBITDA ~3.3x，"资产负债表健康"名不副实**；利率上行看 capex/OCF 强度而非市值 |
| 其他 | ABBV 回调表现验证 | 8 月窗口 +1.81%、8/18 避险日 +3.43% 领涨=KOL"抱团现金流"兑现；但估值 EV/EBITDA 25.9x 偏贵、继续发债（Apogee）→**纯避险首选 JNJ 非 ABBV** |
| 其他 | 期货月差 vs 裂解套利 | **月差更好操作**（2 腿同品种+跨期保证金优惠+交割收敛+Labor Day 季节性）；裂解 3 腿月份错配（汽油 9 月 vs 原油 10 月=不可交易组合）+结构性瓶颈做空过早风险大；**国内无成品油期货**（上期所仅 SC/FU/LU/BU） |
| 其他 | 做空月差 vs 做空裂解确定性 | FRED 3-2-1 裂解 2006 起 n=5065：当前 $65.8（分位 99.4%）；>50 历史 7 次完结全回归 $20-30（t+365 7/7）但 t+30 有继续新高先例 → **做空月差确定性更高**，做空裂解"方向对、时点极不确定" |
| 其他 | 汽油价格极限 | 三层天花板：需求破坏（$5 实证阈值：2022-06 破 $5 后需求 -5~8%）、政策干预（SPR/出口限制/RVP 豁免/暴利税）、供给响应（全球 ~9% 炼能离线、中东出口 2027 底恢复）；理论上限 ~$5-6/gal |
| 其他 | 资管分化 APO 独红 | 8/28 APO +1.20% vs KKR −0.59%/BX −0.87%：结构性（APO=浮息信贷+Athene SRE 利差引擎；KKR=PE buyout；BX=地产 40%）；**利率上行受益判据=SRE 利差收入占比，非信贷资产规模**；ARES 结构像但无 SRE 引擎不跟涨 |
| 其他 | 资管 ETF 结论 | 唯一对口 PSP 前十大无 APO（成分结构与 APO 逻辑相反）；**信贷+保险整合型资管无纯 ETF，个股是唯一直接表达** |
| 其他 | VST/CEG/XLU 利率逆风 | 8/28 整体跑输（CEG −2.00%/VST −1.95%），越成长股化跌越多；9 月 FOMC 分水岭，盯 10Y 4.65-4.7%（回落 4.3% 以下反弹信号） |
| 数据 | RB1! vs 单月合约口径 | **分析汽油趋势一律用 RB1!（连续主力）**，RBU2026 单一合约被基差/换月扭曲（8/14 后 RB1!-RBU2026 −0.426=单月溢价 14%）；连续合约换月有假跳空（14 次 >2.5% gap），做收益/回测须剔除或后复权（ratio=P_new/P_old） |
| 8/30 凌晨 | 农业股 × 地缘溢价剥离监测（**本 automation 入库**） | 并行会话新产出：CF/DAR 主升浪（1-2 月）与霍尔木兹紧张同期的对照检验——用"油价异动日 CF/DAR 是否跟跌"判断地缘溢价占比是否剥离；脚本 `agri_geo_premium_monitor.py` + `fetch_geo_cdp.cjs`（CL 增量至 08-27，CN 油价 8/27 单日 −8.4% 异动）+ results 2 json |
| — | 每日收尾交接 + GitHub 提交 | 本 automation：8/29 全天汇总入库并推送（详见第四节） |

## 二、重要方法论决策 / 新增约定（8/29）

1. **术语一律悬停浮窗，禁用速查表**（用户原话"把用户当白痴，不常见术语都要悬浮"）：正文所有专业术语（含 onset/SST/ENSO/β₁₀，共约 50 条）虚线下划线+悬停白话解释，**标注偏过不偏漏**；实现=TERMS 词典 + annotate_terms() 段落标注 + `.term`/`.termtip` CSS + 浮窗引擎 JS。
2. **`_BLOCK_RE` 必须带捕获组**（本次最深坑）：`re.split` 无捕获组会**丢弃全部 script/style 块**——上次 build 产物只剩浮窗引擎 1 个 script、canvas=0、ECharts/DET 全被删（63KB 损坏版）；另外按 `_TAG_SPLIT_RE` 分片只标文本节点防标签属性误标；改完 build 脚本先静态校验（script/canvas/ECharts 计数）再跑 CDP。
3. **ENSO 事件报告 double-label**（onset 年份+俗称，如 "2014-10（2015-16）"）：57 号按 onset 首月命名导致用户质疑"没看到 2015-16"，实为同一事件（2014-10→2016-05、峰值 ONI 2.59、20 个月）。
4. **事件月度状态标记按日历月推进**（57 号坑）：首版用 range(onset, end+1) 整数遍历产生幽灵月份键（计数 2942 vs 实际 920），须在真实 ym 集合内标记。
5. **ENSO 强度分档用峰值 ONI**（<1.5 弱 / 1.5-2.0 强 / ≥2.0 超强）：三档单调"越强越弱"比单一结论更精确；期末负超额多为先冲高后回撤（73% 样本 peak>0），分析须含最大超额/见顶 T/回撤起始四指标而非只看期末。
6. **事件明细长表加交互筛选**（强度/股票/显示行数下拉，data-band + filterEvents JS）：574/474 行全量可筛，验证脚本保留为正式回归工具（verify_agri_filters.cjs / verify_agri_terms.cjs）。
7. **RBOB 口径铁律**：趋势分析一律 RB1! 连续主力，单月合约（RBU2026）不作趋势依据；换月假跳空须剔除或后复权（ratio 必须用换月日两合约各自独立收盘价，不能用未复权连续序列相邻日跳空近似）。
8. **敏感度谱系新用例**：板块敏感性可用"利率事件日（JH 讲话）+ 日常回归"双向验证——事件日验证方向（避险轮动/重定价），回归给 β 量级；二者可能矛盾（消费股事件日普涨 vs β≈0），须分别表述。
9. **延续铁律**：60 日滚动主口径/显著性三档+p 值（sig/edge/no）/参数图例/R 与 β 同列/单位陷阱（corr ×100 入库 build ÷100）/7×24 资产收益全序列先算再 merge/README 登记前先 ls 校验/用户"空仓"=做空。

## 三、当日产出清单（reports/ 编号目录）

- 报告（新）：`54_宏观利率背景六股影响/`、`55_宏观背景/`（index.html + 宏观背景.md + 20260829_利率上行板块全景.md）、`56_CCL_RSI档位买入/`、`57_农业股ENSO与利率敏感性/`（index.html + runup_paths.html + 交接文档_ENSO回测与利率敏感性.md）
- 根目录：`宏观背景.md`（**宏观利率常设入口**，已在 MEMORY 索引定位）
- 脚本（新增）：`build_54_rates_six_stocks.py`、`build_55_macro_background.py`、`fetch_ccl_cdp.cjs`、`ccl_rsi_band_buy.py`/`build_ccl_rsi_report.py`、`ccl_rsi_band_dip.py`/`build_ccl_rsi_band_dip_report.py`、`agri_enso_analyze.py`/`agri_rate_sens.py`/`agri_verify.py`/`agri_strong_el_analyze.py`/`agri_runup_analyze.py`/`build_agri_enso_rate_report.py`/`fetch_agri_cdp.cjs`、`verify_agri_report.cjs`/`verify_agri_filters.cjs`/`verify_agri_terms.cjs`、`analyze_crack_spread_fred.py`、`_check_nfp_curve.py`（非农负月+10Y-30Y 分位核对，**本 automation 入库**）
- 结果：`results/agri_{enso,rate_sens,verify,strong_el,runup}.json`、`results/ccl_rsi_band_buy.json`、`results/ccl_rsi_band_dip.json`、`results/agri_geo_premium.json` + `_report.json`（**本 automation 入库**）
- 数据：`data/agri/raw/{oni.txt,dgs10,dgs2,cpi}.csv` + 14 只农业标的日线（data/{cf,dar,mos,tsn,hrl,adm,agco,bg,ctva,ntr,fmc,fpi,moo,dba,de}/）、`data/cl/CL, 1D.csv` 增量至 08-27（**本 automation**）

## 四、git 状态与本次提交（2026-08-30 00:0x，automation）

**前情**：8/29 白天已按主题提交 8 个（`eb0d515` 57号报告 → `39eba89` 57号交接文档+术语悬浮，含 55 号补全、56 号、git pull 冲突解决、交付规则变更等）；全部**未 push**，远端 main 停 `98ebde0`（本地领先 8 个提交）。

**本次 automation 处理工作区遗留 + 收尾**，按主题分 commit：
1. **57 号追问越权 + CL 数据增量**（日志 23:30-23:45 两段：2015-16 负超额机制 + 2026 抢跑实证；`data/cl/CL, 1D.csv` 尾部 +08-27 行，diff 仅新增 1 行无覆盖）
2. **农业股地缘溢价监测**（8/30 凌晨并行会话产出：`agri_geo_premium_monitor.py` + `fetch_geo_cdp.cjs` + results 2 json，脚本注释完整、CL 依赖已入库）
3. **非农/长端核对脚本**（`_check_nfp_curve.py`，FRED PAYEMS/DGS10/DGS30 核对用，无对应报告产出）
4. **交接文档 + 日志集中收尾**（overview.md 覆盖 8/29 全天 + MEMORY.md 压缩清理 + automation memory）

**重复文件说明**：`reports/57_农业股ENSO与利率敏感性/厄尔尼诺x农业股.html` 为 57 号重做过程中的同名旧备份（与 index.html 内容 100% 相同、时间早于正式版），**按"不做删除操作"原则保留为未跟踪，不入库**，用户确认后可删。

**有意未入库**（延续惯例）：`results/_scan_step2.log`、`results/supplement_volume.log`（运行日志）；`scripts/fetch_djia_week_0821.py`（8/21 遗留）。

**push**：用户明确要求"提交到 github 即可"→ 以 `git ls-remote origin main` 验证远端 → 推送全部积压（本地领先 8 + 本次 4 ≈ 12 个提交）→ 验证远端新 HEAD 与本地一致（SSH 443 通道）。

## 五、重要过程 / 踩坑（8/29）

- **build 产物被 `re.split` 静默毁坏**（当日最深坑）：无捕获组的 `_BLOCK_RE` 丢 script/style 块 → 57 号产物一度只剩浮窗引擎、canvas=0。修复=捕获组保留 + 静态校验脚本（script/canvas/ECharts 计数）先行 + CDP 无头兜底（termN/glossRemoved/hover 行为断言）。
- **57 号 CDP 验证 Chrome 三崩**：GPU 虚拟化 shared context 失败（`--disable-software-rasterizer` 重启稳定；删旧 user-data-dir 换 r4 目录）；Chrome 用完已关闭（9222 dead）。教训：Windows 上 Chrome CDP 挂载必须独立 user-data-dir，勿与常驻实例共用。
- **ONI 月份解析 numpy int64**：divmod 结果 float 需 int()（三处），漏一处导致样本 n=1 静默（la_avg12 首版）——统计类脚本跑完先看 n 合理性。
- **git pull 冲突（02:10）**：本地/远端同日日志撞同一追加位置，远端版+本地 4 段按时间线合并（--ours 取合并版）→ merge commit fd1894c；遗留 `stash@{0}`（3 行 JH 交接）保留备查。
- **README 死链教训**：55 号 md 只写日志未落地，11:44 登记后发现死链，19:55 据日志重建补全——**登记索引项前先 `ls`**（已入 MEMORY 长期规则）。
- **RBOB 换月跳空实证**：2026-08-14 主力换月 RB1! 隔夜 "-8.5%"（未复权），实际 9 月合约当日真实 +2.1%——"假跳空"= 两合约价差，back-adjusted 用 ratio=P_new/P_old=0.9125 修正。
- **月份×档位勾稽**：2025 起 CCL 档位失效（59 次 T+20 −1.73%/超额 −2.39pp）与阶段×档分解互相印证，否则会被全期正收益误导。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md + 项目 MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （≤50字）`、按主题分 commit、**默认只本地 commit 不 push（用户明确要求才 push，本 automation 已获授权）**。
- **高权限自我约束（用户本次明确叮嘱）**：不做删除/clean/reset 等破坏性操作，全部改动可 git 回滚（本次重复文件也未删除，仅保留为未跟踪）。
- 交付必须产物展示（present_files + 自动打开预览）；交付不附图；HTML 报告出完后 CDP 无头验证兜底。
- 术语悬停浮窗不用速查表；红涨绿跌 + Okabe-Ito 色弱安全（叠线型/符号，用户绿色弱）；报告表格参数图例；R 与 β 同列。
- 结论必须先核实数据，无法核实标注「未核实」；评审四段式；相关性 60 日滚动主口径；交付克制（只做用户明确要求的内容）。

## 七、遗留待办 / 下次继续

- **9/15-16 FOMC 是核心分水岭**：加息概率 57%（JH 后 FedWatch）；9 月初非农+CPI 数据决定方向——数据弱→黄金/BTC/长久期弹性最大，数据强→续压。对持仓组合（SBUX 高 PE 空头腿怕降息反转、XLU/电力怕加息、SOFI 双向期权）是核心变量。
- **57 号遗留**：`厄尔尼诺x农业股.html` 重复文件待用户确认删除；强事件 2026 抢跑跟踪（9-10 月 WASDE/收割季是否兑现减产；关税致美豆出口 13 年最低是特有逆风）；README 57 条目如补交接文档行待办。
- **地缘溢价监测初版已入库**：可跑 `python scripts/agri_geo_premium_monitor.py` 复算；后续如出正式报告，README 分类登记。
- **56 号 CCL**：当前 RSI 35.44 非买点，等 <30 档（T+20 +3.70%）+ 企稳确认（收复 EMA20/放量阳线）；Yahoo 未同步 08-28 数据待补。
- **54 号图表补修**（可选）：y 轴利差上限 0.6 截断 1 月 0.74 峰值（55 号已修，54 未动）。
- **52 号 MCD 操作跟踪**（沿用）：4% 反弹目标（260→270.5）、收盘止损 <255/<253。
- **45 号报告深化 / 31 号补更 / GE 周线高位死叉 / VIX 中期选举窗口 / 富途选股器 450 池**（沿用，详见 8/28 交接）。