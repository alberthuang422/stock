# 工作交接文档（2026-08-27 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/YYYY-MM-DD.md`，长期要点见 `.workbuddy/memory/MEMORY.md`，报告检索入口为 `README.md`（6 大分类索引）。

## 一、当日工作全景

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| 42 | VIX 中期选举前抬升（承接 37 号） | 前 20 日 VIX 均抬升 **+21.1%**、前 17 日峰值 ×1.214（约 3~4 周前启动），奇数年对照无抬升；幅度约为 SPY 已实现波动放大的 **7 成**（隐含波动定价更温和）；4/6 次抬升、2 次低波动年收缩，n=6 描述性规律；当前（08-26 VIX 15.69 低位）距 11-03 选举约 45 交易日，抬升窗口临近 |
| 教学 | 相关性分析方法论 9 步流程讲解 | 全流程：Yahoo 复权→日收益率→对齐交集→Pearson+Spearman→阶段切片→滚动60日→Fisher z→β/R²回归→极端日+超额压力测试；真实数据演示 IHI×XBI 脱钩（0.652→0.249，滚动曲线最近已破 0）；改进建议（显著带/偏相关/lead-lag/状态分组，不推荐 DCC）已入 MEMORY |
| 38 | 中期选举前标普板块波动率（扩展） | 11 板块事件研究：周期/资源类冲击最大——XLB 材料 **+43.8%** ≥ XLRE +41.0% > XLU +37.9% > XLI +33.9% > XLE +33.0% > XLY +32.7% > XLF +32.3% > XLP +23.2% > XLK +22.8% > XLV +20.6% > XLC +7.5%（SPY +30.8%）；科技/医疗/必需消费钝化 → 选举重定价集中在政策敏感型板块；板块 Welch t 全部 p≥0.15 不显著 |
| 周线 | 周线数据改为网络源重做 | `scripts/fetch_weekly_cdp.cjs`（CDP 原生 WebSocket 连本机 Chrome 9222）：102 个文件夹全部成功（含此前损坏的 dji 用 ^DJI）；清洗 open=0 填 close、未完成周填 close、目检 OHLC 违规=0；网络周末日=08-26 比本地日线更新鲜 |
| 39 | 蓝筹 RSI 超卖买入 | 72 只蓝筹 RSI14 下穿 30 首日（5,275 事件，1962 起）：**T+5 +1.00%/59.3%、T+10 +1.60%/60.2%、T+20 +2.85%/63.8%** ≈ 基率 2 倍；日历日聚类修正后 t=12.12 仍显著；相对 SPY 超额 T+20 +1.16pp（t=8.93）；仅疫情股灾期 T+5 失效；当前全池仅 TJX(22.8) RSI<30 |
| 40 | 蓝筹 RSI 动态支撑位买入 | 9,347 支撑买入事件 **整体 T+20 +1.45% ≈ 基率 +1.42% 几乎无 edge**；edge 全在支撑位 <35 档（+3.36%）；随支撑位抬高单调衰减——「放松到支撑位就买」不成立。⚠️ 该报告用分位数当支撑位属**口径错误**，已由 41 号纠正并加标注 |
| 41 | 蓝筹 RSI 摆动低点(swing low)聚集支撑 | 用户纠正口径（swing low 本义：低于前后各 5 日、最近 3 谷聚集极差≤3）：594 事件整体 T+20 +1.39% 仍≈基率；edge「两头强中间弱」——35-40 档 +2.97%/64.1%(t=3.24)、≥50 档 +2.41%（趋势回调），40-50 归零；K=3~10/M=2~4/TOL=2~4 参数扫描稳健。**终判：真正 edge 是「RSI 低位」本身，支撑位形态只是给低位包了层技术外衣（39/40/41 同源闭环）** |
| 稳健 | 去掉科技股稳健性检验 | 62 只（去科技）swing 支撑 T+20 +1.27%/59.1%、RSI<30 +2.69%/63.8%——结论不变；科技股本身是最弱板块之一，非 edge 来源 |
| 澄清 | RSI 支撑位 ≠ 价格支撑位 | 支撑位分档 ⇄ 价格动量：<35 档前120日 −12.2%（真下跌超卖）→ ≥50 档 +22.0%（上涨途中）；44% 事件落在无 edge 的 40-50 区间；加多头趋势过滤反而减 edge（376 件 +1.09% vs 全部 +1.39%），空头（价<MA120）最强 +1.90%——「多头回调追势」场景不成立 |
| 选股 | 富途选股器能力排查 + 美股优质股筛选 | 技术指标「筛选」整类不可用（invalid parameter）但「取回」可用 → 质量字段服务端筛 + RSI 取回客户端分档；产出 450 只美股（市值≥500亿美元）含 RSI14：<30 仅 TJX 1 只、30-40 25只、40-50 143只、50-70 253只、≥70 28只 |
| 数据 | data 目录成交量批量补充 | `scripts/supplement_volume.cjs`：253 个 OHLCV 文件，100 个需更新，全部成功（补列 1 文件 dji + 追加 519 行）；修复 CRLF 行尾污染坑 |
| 43 | ABBV × IBB × IHE 相关性 | 同窗口（2021-08~2026-08）**ABBV×IHE r=0.496 vs ×IBB 0.376（Steiger p<0.001）**，制药显著占优；2026-02 分界后 0.509 vs 0.414（p=0.059 边缘）阶段间无显著变化（Fisher）——制药占优是稳定结构；长窗口 2015 起板块属性从生物科技漂向传统制药（Humira 时代 vs 专利悬崖后防御化+Allergan）；日方差 75~86% 为自身特质；IHE/IBB 持仓均无 ABBV，无机械重叠 |
| 44 | 蓝筹贴 EMA20 缩量跌破平台 | 8,305 事件（1962 起，72 只）：**整体几乎无 edge**——T+5 +0.40%/T+10 +0.63%/T+20 +1.26% 与基率几乎重合，T+10/T+20 反略低于基率；缩量 vs 放量破位结果一样（缩量无信息）；仅本轮牛市最弱（T+5 +0.15%/51%）；附事件 K 线浏览器（369 个事件 candlestick + EMA20 + 平台下沿 + T+N pin） |
| ER | 板块波段 ER/流畅度分析框架（原型→45号报告） | zigzag 拐点拆波段→分段 ER→滚动 20 日平台→HV/corr 对照→截面分位标签；2025-11-03~2026-02-27 实测：波段 ER 普遍偏低（绝对阈值 0.7 几乎不触发），EP05/EP06 更有区分度；已发现 3 缺陷（波段太少噪音大/标签需叠方向/截面粗）；**阶段 B 批量扫描 + 倾向统计已完成并产出报告 45**（方案交接文档见 `reports/交接文档_震荡市板块独立行情回测.md`） |
| — | 每日收尾交接 + GitHub 提交 | 本 automation：8/27 全天汇总入库并推送（详见第四节） |

## 二、重要方法论决策 / 新增约定（8/27）

1. **「支撑位」必须用 swing low（局部极小）+ 聚集确认定义，不能用分位数/统计低位定义**——后者回答「RSI 有多低可能到」而非「RSI 在哪里反转」。40 号用「120 日 15% 分位」当支撑位属口径错误（15% 分位中位 41.7 vs 120 日 min 中位 29.4），41 号纠正后结论不变：**edge 只在 RSI<30~40 的低位，与定义方式无关（39/40/41 三报告反复验证）**。
2. **技术形态（平台/缩量/支撑位）本身不给 edge**：41 号 swing low 修正定义后整体仍 ≈ 基率；44 号缩量破平台整体仍 ≈ 基率、缩量 vs 放量无差异——连续两报告再次验证「真超额只来自 RSI<30 深度超卖的均值回归」。
3. **富途选股器**：技术指标筛选类后端一律 `invalid parameter`（连 MACD_DIF>0 都报），但取回正常（RSI 动态 period=11 日线 ×1e3）；可行方案=质量字段（市值/PE/股息）服务端筛 + RSI 取回客户端分档。
4. **周线数据统一规则**：价格用复权价（adj_ratio 作用于 O/H/L，close=adj_close）；按「周五结束」自然周重采样；日期标签=最后实际交易日；跳过 BATS_*（预计算 MACD 指标文件非原始 OHLCV）。
5. **网络拉数与周线/日线区分**：Yahoo chart 接口必须带 period1+period2 或 range（只给 period1 Bad Request）；`range=max` 老标的会被降采样成季线，日线须 2y/5y 或明确区间；周线文件须 `interval=1wk`。
6. **Yahoo 周线末尾带未完成周 bar**：MACD/EMA 现状以最后完整周为准（GE 案例）。
7. **CRLF 行尾污染**（历史坑）：批量处理 CSV 须先 `replace(/\r\n/g,'\n').replace(/\r/g,'\n')` 归一化，否则 `,volume` 拼到 `close\r` 后面损坏列结构（dji 一度中招）。
8. **事件研究显著性必须互斥对照**：不能拿「事件=基线子集 vs 全集」做检验（VIX 研究教训，t 虚高到 31）。
9. **相关性分阶段惯例**：以 2026-02-01 为结构断裂点；分阶段比较用 Fisher z 检验阶段间差异。
10. **上周（8/26）延续铁律**：图表单位陷阱（corr ×100 入库、build 须 ÷100，交付前跑 `scripts/_scan_corr_units.py`）；SSR 渲染验证保留。

## 三、当日产出清单（reports/ 编号目录）

- 报告（新）：`42_VIX中期选举抬升/`、`38_板块中期选举波动率/`、`39_蓝筹RSI超卖买入/`、`40_蓝筹RSI支撑位买入/`、`41_蓝筹RSI摆动低点支撑买入/`、`43_ABBV_IBB_IHE_相关性/`、`44_贴EMA20缩量跌破平台/`、`45_震荡市板块独立行情/`
- 交接文档：`reports/交接文档_震荡市板块独立行情回测.md`（45 号报告方案，阶段 A 原型已跑通）
- 结果：`results/vix_midterm_vol_*.csv`、`sector_midterm_vol_trades.csv`、`blue_chip_rsi_oversold.json`、`blue_chip_rsi_support.json`、`blue_chip_rsi_swing_support.json`、`abbv_ibb_ihe_corr.json`、`blue_chip_ema20_shrink_break.json`+`_kline.json`（638KB+2.0MB）、`futu_bluechip_500b_with_rsi.csv`（450 只）、板块 ER 原型 `choppy_slices.csv`/`scan_slices.json`/`continuation_trades.csv`/`independence_stats.json`/`sector_independence_scan.csv`/`_45_detail_ready.csv`
- 脚本：`vix_midterm_vol.py`/`build_vix_midterm_dashboard.py`/`plot_vix_midterm_vol.py`、`sector_midterm_vol_backtest.py`/`plot_*`/`build_*`、`fetch_sector_etfs_cdp.cjs`、`fetch_weekly_cdp.cjs`/`gen_weekly.py`、`blue_chip_rsi_oversold.py`/`blue_chip_rsi_support.py`/`blue_chip_rsi_swing_support.py` + 对应 build 脚本、`fetch_blue_chips_missing.cjs`（补齐 45 只蓝筹日线，72/73，MMC 暂缺）、`abbv_ibb_ihe_corr.py`/`build_abbv_ibb_ihe_report.py`、`blue_chip_ema20_shrink_break.py`/`build_blue_chip_ema20_shrink_break_report.py`/`test_render_ema20_break.cjs`、`supplement_volume.cjs`/`fix_dji_volume.cjs`、`sector_wave_er.py`/`find_choppy_slices.py`/`scan_sector_independence.py`/`independence_persistence.py`/`build_45_report.py`
- 数据：`data/ihe/IHE, 1D.csv`（新，westock 拉取 2021-08 起 1255 行）；全部 `*.W.csv` 周线网络重做；100 个 OHLCV 文件 volume 补充（dji 由 `fix_dji_volume.cjs` 重建）

## 四、git 状态与本次提交（2026-08-28 00:0x，automation）

**前情**：8/27 白天已按主题提交 8 个：`5dc10ee`（日志+README+显著带口径）→ `e915e56`（报告38+XLU/XLRE数据）→ `c1603fa`（报告37+事件研究脚本）→ `47564f0`（报告42 VIX+周线数据重做）→ `009ee00`（报告44 + K线浏览器）。远端 main 停 `5dc10ee`（积压 2 个提交未推送）。

本次 automation 补交 8/27 晚间未跟踪产出 + 交接文档/日志，按主题分 commit：
1. **报告 43 ABBV×IBB×IHE + data/ihe 数据**（`reports/43_ABBV_IBB_IHE_相关性/` + `data/ihe/IHE, 1D.csv` + 脚本 + json）
2. **板块波段 ER 原型**（`scripts/sector_wave_er.py`/`find_choppy_slices.py`/`scan_sector_independence.py`/`independence_persistence.py`/`build_45_report.py`/`_45_data.json` + results 6 个文件 + `reports/交接文档_震荡市板块独立行情回测.md`）
3. **成交量批量补充数据 + 脚本**（data/ 全部 CSV 修改 + `supplement_volume.cjs`/`fix_dji_volume.cjs`；volume 增量为新追加行，无破坏）
4. **交接文档 + 日志 + README + MEMORY + 本 automation 执行历史**

**有意未入库**：`results/_scan_step2.log`、`results/supplement_volume.log`（运行日志，非交付物）；`scripts/fetch_djia_week_0821.py`（8/21 遗留、无当日产出，历史惯例）。

**push**：以 `git ls-remote origin main` 验证远端 → 推送本次 + 全部积压本地提交 → 再验证远端新 HEAD 与本地一致。

## 五、重要过程 / 踩坑（8/27）

- **40 号口径错误被用户当场纠正**：分位数支撑位与「支撑=跌不下去」本义自相矛盾（15% 分位下跌破天数平均 20.6 天）。教训：用户对技术定义极敏感，先用 swing low 本义对齐再计算。
- **SSR 渲染验证**：Write 工具写临时 .cjs 后 `rm -f` 有竞态（MODULE_NOT_FOUND），39 号后改用 `node -e` 内联脚本；playwright-core 实际路径 = `.workbuddy/binaries/node/workspace/node_modules`。
- **Yahoo 接口坑**（supplement_volume 踩到）：range=max 老标的降采样成季线、只给 period1 报 Bad Request、周线文件塞日线 bar、CRLF 污染列结构——均已修复并固化到脚本。
- **westockdata 拉 US ETF**：`search IHE --type etf` 得 usIHE.AM、`kline --fq qfq` 只回 5 年（上限约 5 年，--start 无效）。
- **浏览器渲染自检经验**：Chrome CDP 监听绑定（::1 vs 127.0.0.1）排查；custom_html 注入 echarts 需 setTimeout 轮询就绪。
- **高权限自我约束**（安全惯例延续）：全程仅 add/commit/push，未做删除/clean/reset/checkout 等破坏性操作，全部改动可 git 回滚；提交前人工抽查 diff（dji 修复后 OHLC 合规、aapl 仅尾部 +4 行 volume 追加）。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （≤50字）`、按主题分 commit、只本地 commit 不 push（除非用户明确要求，如本 automation）。
- 高权限自我约束：不做删除/clean/reset 等破坏性操作，全部改动可 git 回滚。
- 交付不附图；红涨绿跌 + Okabe-Ito 色弱安全（叠符号/线型）；严格口径（不要股息/容差缓冲）。
- 结论必须先核实数据，无法核实标注「未核实」；评审四段式；相关性以 60 日滚动为主口径；R 与 β 必须同列。
- 用户绿色弱（deuteranopia）：配色必须色弱安全，不可依赖红/绿为唯一区分，叠加线型/符号/年份标签。
- 交付克制：只做用户明确要求的内容，不确定先问。

## 七、遗留待办 / 下次继续

- **45 号报告（板块震荡市独立行情统计倾向）**：已交付（`reports/45_震荡市板块独立行情/` + `scripts/build_45_html.py`），后续可按需深化——ER 相对阈值、n≥3 二维标签、切片参数敏感性扫描；`scripts/_45_data.json` 为数据源（93KB，已入库）。
- **31 号正式报告补更（仍未执行）**：★超额口径轴 + 环境分层表（评审已出结论，报告正文未更新）；31 评审交接文档见报告目录内。
- **MMC 数据缺口**：blue_chips 池唯一缺（Yahoo 接口返回 delisted 实为在市），可换 westock 重试。
- **GE 周线高位死叉跟踪**：DIF 已死叉 DEA 但 0 轴上方 + EMA 多头未破坏——是否跌破 EMA20（≈340.6）是关键观察位。
- **VIX 低位 + 中期选举窗口**：距 11-03 选举约 45 交易日，VIX 抬升窗口临近（参考报告 42）。
- **富途选股器**：450 只候选池可继续做质量过滤/RSI 分档深化，RSI<35 深度超卖 8 只可作买点观察清单。
- **生物医药跟踪点**：HARMONi-3 终局（2026H2）、OMB 名单（2026-12）、工具弹性主升段预期 2026Q4-2027。
- **LLY 跟踪点**：retatrutide"生物制品"归类诉讼、Pepsi/雇主 GLP-1 覆盖动向（支付端压力是否扩散）。
- 未核实项留档：NVO 美国专利年份（2031 vs 2033 来源打架）——建议以 FDA Orange Book + 10-K 为准。