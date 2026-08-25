# 工作交接文档（2026-08-25 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/YYYY-MM-DD.md`，长期要点见 `.workbuddy/memory/MEMORY.md`，报告检索入口为 `README.md`（6 大分类索引）。

## 一、当日工作全景

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| README | 报告索引新建 | 62 份 HTML 建立 6 大分类目录 + README 索引（51 条链接校验无死链）；**新约定：每出新报告必须同步更新 README 对应分类（标题+链接+一句话结论）** |
| 17重做 | KO RSI 超买（数据更至 8/21） | 超买≠必回调结论维持；新增"窗口路径"维度：全样本 T+20 runup +3.46% vs peakdd −3.42%/maxdd −5.25%——"先冲高 3.5% 再回吐大半"；本轮牛市回吐最浅，Deep RSI≥75 负期望 |
| 31 | 蓝筹区间下沿支撑 × 周线EMA20压制 | 死叉显著放大尾部风险（C 破位率 71.4% vs A 62.8%）；**评审修正：压制成本=破位率非胜率**（随机日对照 57.1%，A/B 有 ~+0.5pp alpha）、B 组优势系牛市环境假象、浅死叉=下跌中继/深死叉=超跌反弹（深档 T60 反超 +4.20pp） |
| 32 | KO × XLK/XPH/XLV 相关性 | **20 年首次三线分裂**：KO×XLK 分界后转负 −0.397（防御切换）、×XPH 脱钩至 0.026（制药独立景气 +51.8%）、×XLV 稳 0.4；2026 年度 KO×XLK −40 比 2000 年更深 |
| 33 | 周线MACD收敛 × 支撑位 | **强否定：收敛无增量 alpha**（CVG T+20 1.79%/59.8% vs NEG 1.59%/62.4%，t=0.49）；支撑位本身 ~+0.5pp 微弱正偏；收敛长度无单调性（4 根最优、≥6 衰减）；周线数据落盘 data/（47 只 1962–2026） |
| 34 | 道指 9 板块代表股 RSI 超买横向 | 超买无看空 edge 可复制，但**最强的普适规律=窗口路径 9/9 全中**（runup +3.25~+8.91%、peakdd −3.26~−5.20%）；回吐率防御股最高（VZ 1.03/KO 1.00）成长最低（AAPL 0.58） |
| 35 | CSCO×PANW/CRWD 相关性 | PANW×CRWD 高度抱团且逐月增强（静态 0.84、r60 末值 0.89）——AI 安全单一仓位；CSCO×网安全面脱钩（0.23/0.18）；CSCO 极端日全是财报反应日，网安零跟随；CSCO 提供真实跨链条分散 |
| — | 同花顺 Financial-API MCP | 4 个托管 HTTP MCP 端点接入（A股 21+4+2+28 工具），仅覆盖 A 股；美股研究线仍靠富途 MCP + CDP |
| — | Agent Reach 安装 | 隔离 venv v1.5.0（自有 ~/.agent-reach/config.yaml），P2 安全；Twitter 已配 Cookie，**search 404（上游接口失效）→ 用户定案：X 搜索固定走 Chrome CDP，feed 通道保留** |
| — | 全股票批量支撑位（自动化 22:00） | **3550 行支撑位 / 100 只覆盖**（跳过 ibkr）；data/support_levels/ 三层输出全部校验通过；S1 状态 59 near / 35 above / 6 below，强度 A/B/C=82/12/7% |
| — | 每日收尾交接 + GitHub 提交 | 本 automation：8/25 全天汇总入库并推送（详见第四节） |

## 二、重要方法论决策 / 新增约定（8/25）

1. **窗口路径计算改用显式前看窗口 T+1..T+N**——`shift(-1)+rolling(N)` 会回看污染（混入事件日前数值）；high/low 按 adj_close/close 复权因子折算（17 重做、34 号复用）。
2. **事件研究"胜率"必须看相对随机日/环境调整后的增量**（31 评审）：绝对胜率 62.8% 是蓝筹+事件日相对随机日的正常提升，压制组的真实代价是破位率与尾部。
3. **IHE 数据缺失 → 以 XPH（SPDR 标普制药）代理**（同属美大型制药板块，成分高度重叠），须在报告中注明代理关系（32 号）。
4. **执行环境新约定**：Agent Reach 上游工具在自身 venv Scripts 目录，调用需加 PATH；**主联网流程（搜索/网页）仍一律走 Chrome CDP**。
5. **执行环境能力边界**：同花顺 MCP 仅 A 股（无港股/美股/分钟K/宏观/研报）；f-string 嵌 JS 用 @@PLACEH@@+.replace()（35 号踩坑）已于 08-24 前定稿，本次复验。

## 三、当日产出清单（reports/ 编号目录）

- `17_KO超买/`（重做版，窗口路径维度）
- `31_蓝筹区间下沿支撑_周线EMA20压制回测/`（含 `交接文档_评审结论.md`——31 评审二轮：死叉深度两极分化/环境分层，**遗留：建议补★超额口径轴+环境分层表到正式报告，未执行**）
- `32_ko_科技医药相关性/`、`33_周线MACD收敛支撑位回测/`、`34_道指板块超买横向/`、`35_网安vs网络设备/`
- 数据：`data/support_levels/`（levels_summary.csv 3550 行 + touches/{ticker}.csv + README.md）；`data/<sym>/<sym>,W.csv`（47 只周线落盘）
- 脚本：`scripts/ko_sector_corr.py`、`compute_support_levels_all.py`、`screen_bluechip_universe.py`、`support_range_backtest.py`、`build_support_range_dashboard.py`、`macd_converge_support_backtest.py`、`gen_weekly_bluechips.py`、`djia_ob_cross.py`、`csco_panw_crwd_corr.py(+extra)`、`html_to_notion_blocks.py`、`notion_create_page.py`（Notion 报告同步工具，08-25 01:0x）
- 结果：`results/ko_sector_corr.json`、`djia_ob_cross.json`、`csco_panw_crwd_{corr,extra}.json` + `rollcorr.csv`

## 四、git 状态与本次提交（2026-08-26 00:0x，automation）

**前情**：8/25 白天已按主题提交报告 17重做/31/32/33/34/35 + README + 日志（`ff15d72`~`5bc023e`，共 54 个提交未推送）。远端 main 停 `ff15d72`。

本次 automation 补交 8/25 晚间/遗留未跟踪产出 + 更新交接文档，按主题分 commit（详见第五节各 commit）。

**有意未入库**：`scripts/fetch_djia_week_0821.py`（8/21 遗留、无当日产出）；`.workbuddy/tmp/`（临时工具脚本，从未跟踪）。

**push**：原远端 `ff15d72` → 推送全部 54+ 本地提交 → 以 `git ls-remote origin main` 验证新 HEAD 与本地一致。

## 五、重要过程 / 踩坑（8/25）

- **报告目录编号冲突两次**（32 与 KO×科技重合、35 与 31 重合）：必须 `ls reports/` 核对编号后再定；未跟踪目录 mv 后旧目录在 git 不留痕，add 需用新路径、build/test 脚本 OUTD 路径与 docstring 要逐个同步。
- 事件研究 memory 要点：事件聚集（同日 ≥3 股系统性大跌）→ t 值一律视为上限（31 评审）；深死叉=深熊超跌反弹（T60 +7.08%），浅死叉=下跌中继（T20 −0.02%）。
- playground/CDP：先用 taskkill 清残留、LOCALAPPDATA 路径、headless=new、用完关 Chrome(9222)+cdp-proxy（8/25 CSCO 数据经 CDP 拉 PANW/CRWD 刷新至 08-24）。
- 富途/财务核实：CSCO 极端日 02-12/05-14/08-13 全为财报反应日（盘后 earnings_price_history 核实），网安零跟随。
- 支撑位批量计算关键实现：进带判据 = K 线与带相交（low≤hi 且 high≥lo）；聚类合并 = 新元素下沿 ≤ 簇中心上沿（数学保证带不重叠）；repair=轮末 10 交易日内收盘回 band_lo 计入。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （≤50字）`、按主题分 commit、只本地 commit 不 push（除非用户明确要求，如本 automation）。
- 高权限自我约束：不做删除/clean/reset 等破坏性操作，全部改动可 git 回滚。
- 交付不附图；红涨绿跌 + Okabe-Ito 色弱安全（叠符号/线型）；严格口径（不要股息/容差缓冲）。
- 结论必须先核实数据，无法核实标注「未核实」；评审四段式；相关性以 60 日滚动为主口径。

## 七、遗留待办 / 下次继续

- **31 号正式报告建议补更（未执行）**：★超额口径轴 + 环境分层表（评审已出结论，报告正文未更新）；31 评审交接文档见报告目录内。
- 支撑位 S1 状态追踪（59 near / 35 above / 6 below）——可作每日盘前观察清单；`compute_support_levels_all.py` 幂等可重跑。
- 生物医药跟踪点：HARMONi-3 终局（2026H2）、OMB 名单（2026-12）、工具弹性主升段预期 2026Q4-2027；XBI 2025-09 以来 +78.4% 链传导验证。
- Agent Reach 待配：xueqiu/OpenCLI/github auth/xiaoyuzhou Groq/exa 验证；X 搜索走 Chrome CDP 定案。
- KO：Q3（10 月）+ Fairlife 勒索软件事件；SBUX：等 FY26Q4 验证利润率，回调 $97-100 观察位。
- 未核实项留档：NVO 美国专利年份（2031 vs 2033 来源打架）——建议以 FDA Orange Book + 10-K 为准。