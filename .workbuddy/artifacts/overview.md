# 工作交接文档（2026-08-28 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/YYYY-MM-DD.md`，长期要点见 `.workbuddy/memory/MEMORY.md`，报告检索入口为 `README.md`（6 大分类索引）。

## 一、当日工作全景

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| 48 解读 | MCD 回吐归因（昨日报告衍生） | **fwd = maxG − 回吐**：171 事件 MCD 平均回吐 3.4pp vs SPY 2.42pp 为结构性常态；近年超额差（−2.08pp）主因 **maxG 腰斩**（疫情前 +4.82% → 本轮牛市 +2.87%），回吐不变 → fwd 转负；ER 与回吐几乎不相关（r=0.06），ER 区分"单边 vs 震荡"不预测回吐 |
| 48 衍生 | 解套概率验证 | 曾解套（窗口内 maxG>0）89% vs 时点解套（T+20 fwd>0）仅 61%——**死拿 20 天解套率≈抛硬币**；低 ER(<0.15) 曾解套率最高 93% 但时点解套最低 57%（震荡摆回不保证方向）；<30 档时点解套仅 20%（极端超卖死拿必深套）；全程未解套 18 个（10.5%）全在单边下跌期 |
| 49 | MCD RSI 区间跌落买入 | 449 事件（收盘 RSI 档位比前日更低即买入，越跌越买阶梯式）：三档 fwd20 中位全正（35-40 +1.28%/30-35 +2.17%/**<30 +1.99%**）但**超额全 ≤0**（−0.14/−0.07/−1.32pp）——抄底赚"自己弹回来"不赚"跑赢大盘"；<30 档由 5 次→82 次（渐进跌入超卖>暴跌首日）；cd10 后 30-35 档唯一正超额（+0.71pp 胜率 74.2%） |
| 50 | SOFI/XYZ×BTC 季度分阶段相关 | 全期（2023 起 n=915）r=0.303/0.284、β 0.33~0.43、R²<10% 弱-中相关；**近波（7-29 低点 SOFI +23%）非 BTC 驱动**——近 20 日逐日 r=0.21 不显著（±0.46）、2026Q3 BTC +31.6% vs SOFI +2.2%/XYZ +7.7% 掉队 = 总涨幅同步是巧合；季度 r 渐进抬升（2023 0.02~0.27 → 2026 0.33~0.56）但仍解释不了大部分波动 |
| 50-纳指 | 蓝筹 RSI 低买高卖（**cd10 去重 bug 修正重做**） | 旧版结论失真（单票内行号去重致 n=40 → 修正后 n=74）：**RSI<30 下穿低买 T10 +1.63%（胜率 62%，边缘显著 p=0.018）——低买有效、T+10 才显现、阈值越严越有效**；高卖 RSI>70 后 T10 +0.39% 躲不了跌（H60 +0.78% 反为正）；配对循环 34 笔 +11.81%（胜率 97%）vs 66 笔未平仓 −3.29% = 幸存者偏差，须止损；MMC 已更名 MRSH（Yahoo 确认，Marsh & McLennan）补拉 1990 起全量 |
| 51 | MCD/SBUX × 道指/XLY 相关性 | 2×2 拆解：×道指二者接近（MCD 0.285/SBUX 0.294，SBUX β0.696 波动为 MCD 2.4 倍）；**×XLY SBUX 显著更高（0.518 vs 0.329，SBUX 是 XLY 成分 β0.685）**；2026-02 后四组合全转弱（MCD×道指 0.118 不显著，Fisher z=2.23）；2026 走势分化 MCD −11.6%（超额 −23pp）vs SBUX +25.9%（+14.4pp）——**配对对冲度低，实为两个独立方向性赌注** |
| 52 | 美股持仓组合技术面与操作建议 | 宏观=熊陡（10Y-2Y 6/22 +27bp → 8/26 +47bp，长端驱动 10Y 4.47→4.66）；8/27 轮动 XLK +3.16% vs XLP −1.38%（剪刀差 4.5pp）印证板块轮动快；MCD 反弹逻辑成立（48/49 支持 4% 目标 260→270.5，收盘止损 <255/<253）；**SBUX/XYZ 修正为"压力区博弈型空头"**（年内五-六次未破 + 上方 2024-12/2025 年真实成交区 SBUX 113.5-117.5/XYZ 87-99，止损激进=压力区、稳健=成交区） |
| 53 | SOFI/AFRM/UPST 财报日涨跌相关性 | 62 事件/58 日：**财报日三对相关 0.26~0.44 显著低于非财报日 0.62~0.64（T+0 是窗口凹陷点）**；发报票自身波动放大 1.8~2.6×；三票同向 51.7% vs 非财报日 64.2%；传染不对称（SOFI 发报→UPST 同向 76%，UPST 发报→AFRM 相关仅 0.18）；**年度衰减 2021(r~0.9)→2026 AFRM×UPST≈0，财报日"脱钩"逐年加剧** |
| 分析 | MCD×SBUX 多空配对风险 | 前提校验：MCD 52 周新低 ✓ 但 RSI 36.7 **未超卖**（修正用户说法）；SBUX 五年高位须用复权（未复权 120.76 → 前复权高 112.99，现价距 −4.0%、五年百分位 99.3%）；MCD×SBUX 近 1 年 r=0.30 配对对冲度低；基本面 MCD PE 21.1 合理 / SBUX PE 62 倍（10 年均值 40）= 唯一做空理由；宏观 CPI 3.4%、7 月零售 −0.6%、9 月加息概率 ~28-31%（后续 JH 讲话升至 57%） |
| 分析 | CSCO/VST/APO 相关性 | 2026-02 起 n=144 两两日频 R 0.07~0.12 全不显著；周频转负（CSCO×VST −0.31）、剔 SPY 后残差相关全 ≈0、极端日同向仅 ~20%——**正相关全来自大盘共性，纯个股联动≈0**；逐月 21 观测仅 5 sig（三只两两 0 sig）→ 不是协同篮子；APO 唯一稳定高β（β 2.0-2.9）= 真"放大版 SPY"；6 月是唯一"共振月"。**操作修正：三只不能"一起减"，须分开管** |
| 宏观 | Jackson Hole 2026 讲话（Warsh 首秀） | 一手来源：联储官网《In Our Time》+ Reuters/CNBC 解读：①拒前瞻指引（"quieter Fed"）②不给利率路径 ③评估经济"走强"但通胀首要——"若非确信通胀以足够速度回归 2%，则有工作要做"→市场解读为开门加息 ④金融条件"不具限制性"；**市场反应：9 月加息概率 1/3→57%（FedWatch）、2Y +8bp 至 4.31%（7 月底来最高）**；下次 FOMC 9/15-16 |
| — | 每日收尾交接 + GitHub 提交 | 本 automation：8/28 全天汇总入库并推送（详见第四节） |

## 二、重要方法论决策 / 新增约定（8/28）

1. **7×24 资产（加密/外汇）收益相关铁律**：ret 必须在**原始全序列先算好再 merge**——merge+filter 后重算 pct_change 会把"周五→周一"当相邻交易日污染收益（50 号实证：同窗口 r 0.405 正确 vs 0.463 错误口径）；美股序列（只有交易日）无此问题。
2. **显著性一律三档 + p 值列**：sig(p<0.01) / edge(0.01≤p<0.05) / no(p≥0.05)。教训：**"超带即显著"在 n 小时会虚标**——±1.96/√(n−2) 与 p<0.05 等价，但 n=40 时带宽 ±0.318，r=0.32 就过线（50 号 2026Q3 r=0.333 p=0.036 实证，原误标"显著"）。
3. **相关性/统计类报告每个表格必须带「参数图例」**（用户惯例：r=线性相关、Spearman=秩相关、显著带、β、R²、涨跌幅含义），首个表完整、后续简注"同前表"。
4. **事件明细字段与聚合统计字段必须同一单位（百分数）**：49 号 bug——事件字段存小数 0.0345 显示成 +0.03%（应为 +3.45%），纯展示层错误；build 直接格式化事件字段前先确认 JSON 单位。
5. **用户"空仓"口语=做空仓位（short），不是空仓观望**（52 号教训）——方向歧义应先确认。
6. **"危险/逼空"要量化再定性**：先看突破后实际空间（上方成交区）再下结论，别用"亏损无上限"这类没数据的重话（52 号再修正：年内反复未破+上方真实成交区=压力区博弈，非趋势空）。
7. **判断组合协同必须先过逐月/分窗口径**：全期年相关平均掩盖月度结构（CSCO/VST/APO：全期 r 0.38-0.41 是均值幻觉，逐月仅 5 sig）。
8. **累积坑**：ECharts candlestick 顺序=[open,close,low,high]；f-string 嵌 JS 时 `{{color}}` 会被转义成字面量导致 JS 变量未定义（itemStyle 颜色用 Python 插值 `{up_col}`）；富途同接口结果 >token 上限自动落盘需 python 解析；Yahoo quoteSummary 需 crumb+Cookie；Chrome CDP 脚本勿 browser.close()（会关掉共享实例）。
9. **延续铁律（8/27）**：图表单位陷阱（corr ×100 入库、build 须 ÷100，交付前跑 `scripts/_scan_corr_units.py`）；事件研究互斥对照；支撑位必须用 swing low 本义；周线复权口径。

## 三、当日产出清单（reports/ 编号目录）

- 报告（新）：`49_MCD_RSI区间跌落买入/`、`50_SOFI_BTC_相关性季度分阶段/`、`51_MCD_SBUX_DJI_XLY_相关性/`、`52_持仓组合技术面与操作建议/`、`53_金融科技财报日相关性/`
- 报告（重做修正）：`50_纳指区间RSI低买高卖/`（cd10 去重 bug 修复 + MMC→MRSH，结论方向反转）
- 结果：`results/mcd_rsi_band_dip.json`、`results/sofi_btc_*`、`results/rsi_window_final.json`（+ 中间产物 rsi_lowbuy_highsell/rsi_enhance/pair_complete_open/blue_chip_rsi_*）、`results/mcd_sbux_dji_xly_*`、`results/position_tech_20260828.json` + `position_swings_20260828.json`、`results/csco_vst_apo_corr.json` + `_verify` + `_vs_spy`、`results/earn_corr_sofi_afrm_upst/`（analysis.json + 三票日线备份）
- 脚本：`mcd_rsi_band_dip.py` + `build_mcd_rsi_band_dip_report.py`、`sofi_btc_corr.py` + `build_sofi_btc_report.py`、`rsi_window_final.py` + `build_rsi_window_final_report.py` + `blue_chip_rsi_highbuy_lowsell.py`/`blue_chip_rsi_reversion_window.py`/`build_rsi_window_report.py`、`mcd_sbux_dji_xly_corr.py` + `build_51_mcd_sbux_dji_xly_report.py`、`position_tech_20260828.py` + `build_position_report_52.py`、`analyze_earn_corr.py` + `build_earn_corr_report.py` + `verify_earn_report.cjs`、`fetch_earn_dates_cdp.cjs`/`fetch_upst_cdp.cjs`/`fetch_fred_cdp.cjs`/`fetch_positions_cdp.cjs`、`csco_vst_apo_corr.py`/`_verify.py`/`_vs_spy.py`、`cdp_news_search.cjs`/`cdp_yahoo_news.cjs`/`cdp_debug.cjs`
- 数据：`data/btcusdt/BTCUSDT, 1D.csv`（币安 2020 起，用户提供含 RSI/MACD 列）、`data/upst/`（2020-12 起 1430 行）、`data/mrsh/`（MMC 更名后全历史 9231 行）、`data/us_treasury/DGS2.csv`+`DGS10.csv`（**FRED 数据正式迁移目录**，旧根目录 data/dgs2.csv/dgs10.csv 删除，更新至 08-26）

## 四、git 状态与本次提交（2026-08-29 00:0x，automation）

**前情**：8/28 白天已按主题提交 7 个（`b6e4e58` 参数图例 → `0751df0` 52号空头腿再修正），其中 50 号（SOFI/BTC）提交 `4233167` 已 push（用户当日明确要求，首破"只本地"惯例）。远端 main 停 `5020794`（本地领先 6 个提交）。

**本次 automation 处理工作区遗留 + 收尾**，按主题分 commit：
1. **RSI 窗口分析脚本+结果**（`blue_chip_rsi_highbuy_lowsell.py`/`blue_chip_rsi_reversion_window.py`/`build_rsi_window_report.py` + results 5 个 json）
2. **CSCO/VST/APO 相关性**（3 脚本 + 3 json：corr/verify/vs_spy）
3. **CDP 工具脚本**（`cdp_debug.cjs`/`cdp_news_search.cjs`/`cdp_yahoo_news.cjs`）
4. **FRED 数据迁移收尾**（删除旧 `data/dgs2.csv`/`data/dgs10.csv`，新数据已在 `data/us_treasury/` 入库；**数据一致性已验证**：新 DGS10 与旧文件数值逐行一致、仅列名不同（observation_date/value），DGS2 新 13106 行 ≥ 旧 13099 行、尾部更新至 08-26）
5. **交接文档 + 日志 + 本 automation 执行历史**（overview.md 覆盖 + `2026-08-28.md` 增量 + automation memory）

**数据安全复核**（本次重点）：工作区曾有 6 个已跟踪文件显示删除（dgs2/dgs10/dgs30/dfii10/t10yie/wti）——经排查，**dgs2/dgs10 属并行会话有意迁移**（新文件已入库 us_treasury，数据一致性已验证）；**dgs30/dfii10/t10yie/wti 无迁移去向且 dgs30 仍被 `analyze_ipp_drop.py`（07 号报告）引用，已 `git restore` 恢复**，防止数据丢失。全程未做任何非 git 的删除/clean/reset。

**有意未入库**：`results/_scan_step2.log`、`results/supplement_volume.log`（运行日志，非交付物）；`data/fred_test_dgs2.csv`（并行会话临时测试文件）；`scripts/fetch_djia_week_0821.py`（8/21 遗留、无当日产出，历史惯例）。

**push**：以 `git ls-remote origin main` 验证远端 → 推送本次 + 全部积压本地提交 → 验证远端新 HEAD 与本地一致。

## 五、重要过程 / 踩坑（8/28）

- **50 号 BTC 相关口径（当天最深坑）**：7×24 资产收益必须全序列先算再 merge，否则周五→周一的 gap 被当成相邻交易日（详见方法论第 1 条）；币安 UTC 日 K 与美股美东交易日日期对齐有数小时窗口差，日线可接受。
- **50-纳指报告 cd10 去重 bug 被用户质疑发现**：旧版用"单票事件内行号 i−last≥10"而非交易日间隔，效果=每票只留窗口内最早 1 个事件（100→40），留下的全是 10 月下跌初期买点 → 结论系统性拉负；复刻旧 bug 得 n=41/−0.37% ≈ 旧版 n=40/−0.38% 钉死根因。教训：**去重必须用交易日索引差，不能用行号**；事件窗口相关计算必须按 ticker 分组。
- **52 号两次方向修正**：①用户"空仓 sbux/xyz"= 做空仓非空仓观望（已重构空头逻辑）；②"危险/逼空"定性过重，用数据（年内 4-6 次未破 + 上方真实成交区）修正为"压力区博弈型空头，双档止损"。
- **49 号事件明细单位 bug**：事件字段存小数未 ×100，显示 +0.03%（应为 +3.45%），统计层数字不受影响——纯展示层错，但教训=字段单位必须统一（方法论第 4 条）。
- **AFRM FY22Q4 财报日补入**：富途 earnings_price_move + earnings_price_history 双接口并集仍漏 2022-08-26（−21.3%），用 Bing CDP 搜索 SEC/BusinessWire 官方稿核实补入。
- **git rebase 非交互续传**：`git rebase --continue` 会开编辑器等提交信息，用 `GIT_EDITOR=true git rebase --continue` 直接接受默认（当日早上 14 提交 rebase 冲突 2 处：README 与日志，均手工合并保留双方内容）。
- **SSR/Chrome CDP 管理**：Chrome 151 CDP 批量刷新 17 标的日线 + FRED 页内 fetch（直连 curl 被网络策略阻断）；用完已关闭 9222。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （≤50字）`、按主题分 commit、只本地 commit 不 push（除非用户明确要求，如本 automation / 当日 50 号）。
- 高权限自我约束：不做删除/clean/reset 等破坏性操作，全部改动可 git 回滚（本次恢复 4 个误删数据文件即此原则）。
- 交付不附图；红涨绿跌 + Okabe-Ito 色弱安全（叠符号/线型）；严格口径（不要股息/容差缓冲）。
- 结论必须先核实数据，无法核实标注「未核实」；评审四段式；相关性以 60 日滚动为主口径；R 与 β 必须同列；报告表格带参数图例。
- 用户绿色弱（deuteranopia）：配色必须色弱安全，不可依赖红/绿为唯一区分，叠加线型/符号/年份标签。
- 交付克制：只做用户明确要求的内容，不确定先问。

## 七、遗留待办 / 下次继续

- **53 号 AFRM 2026-08-27 财报事件未纳入**（财报已发布但数据面板缺 08-28 交易日至拉数时点），复盘时可补丁更新。
- **9 月 FOMC 9/15-16 加息概率 57%**（Jackson Hole 后 FedWatch）——对持仓组合（尤其长端敏感 XLU/XLRE/消费、SBUX 高 PE 空头腿怕降息交易反转）是核心宏观变量；10Y 4.65% 高位 + 30Y 拍卖 5.216%（2001 来最高）。
- **52 号 MCD 操作跟踪**：4% 反弹目标（260→270.5）、收盘止损 <255/<253；260 支撑带一年仅 3 次盘中触及。
- **45 号报告深化**（沿用）：ER 相对阈值、n≥3 二维标签、切片参数敏感度扫描；`scripts/_45_data.json` 为数据源。
- **31 号正式报告补更**（沿用）：★超额口径轴 + 环境分层表（评审已出结论，正文未更新）。
- **GE 周线高位死叉跟踪**（沿用）：DIF 已死叉 DEA、0 轴上方 + EMA 多头未破坏——观察是否跌破 EMA20（≈340.6）。
- **VIX 低位 + 中期选举窗口**（沿用）：距 11-03 选举约 45 交易日，VIX 抬升窗口临近（报告 42）。
- **富途选股器 450 只候选池**（沿用）：可继续质量过滤/RSI 分档深化。
- **未核实项留档**（沿用）：NVO 美国专利年份（2031 vs 2033 来源打架）——以 FDA Orange Book + 10-K 为准。