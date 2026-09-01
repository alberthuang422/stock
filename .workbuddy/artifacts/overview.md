# 工作交接文档（2026-09-01 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/2026-09-01.md`，长期要点见 `.workbuddy/memory/MEMORY.md`，报告检索入口为 `README.md`。

## 一、当日工作全景（9/1）

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| 56-深 | CCL RSI<30 细分下钻（`scripts/ccl_rsi_sub30_deep.py` → `results/ccl_rsi_sub30_deep.json`） | **最优组合 = RSI 28-30 × 距60日高点回撤≤-30%**：9 次 fwd20 中位 +24.5%、胜率 88.9%、超额 +18.3pp（年份分散，非单波行情）；**"反弹快"≠买点好**：d2m≤3（3天内见顶）12 次 fwd20 中位 −8.5%、胜率仅 8.3%（全为下跌中继/接飞刀）；真正好位置 = 深回撤 × 温和反弹且 20 日不破（fwd5>+5% 组 17 次 fwd20 +11.6%/胜率 88.2%） |
| 56-深 | RSI 阈值敏感性检验（9/1 晚追问） | **RSI 30 线本身无分层能力**：28-29 vs 29-30 几乎无差异（Mann-Whitney p=0.98）；控回撤后 RSI<30 vs ≥30 完全打平（+10.3% vs +10.7%）；**真正 alpha 是回撤深度**。唯一假信号 = 深跌 × RSI 30-35（n=17，fwd20 中 −4.2%、胜率 41%，下跌中继聚集地）；但深跌 × 35-40 反而极好（+13.6%/76.9%，跌透后首次反抽=V 转起点） |
| 56-DCA | CCL RSI<30 超卖期等额定投回测（`scripts/ccl_rsi30_dca.py` → `results/ccl_rsi30_dca.json`，80 周期） | **末日结算=亏钱**（中位 0%、均值 −1.4%、胜率仅 15%）；**延展 T+20 转正**（中位 +4.04%、胜率 67.5%、超额 +2.23pp）；**定投 > 一把梭**（T20 +4.04% vs +2.79%）；**⚠️资金加权缩水**——深熊周期吸走 32% 资金，资金加权 T20 仅 +1.08%（len≥5 组 −2.4%），真实体验是深熊越加越亏；持有 T+60 中位 +9.1%/超额 +5.3pp 显著更好；极端反例 2020-02-24（len=22）T20 −38.5%——RSI 30 作为 DCA 终止线太早，2020 见底在 4 月 |
| 低相关 | CCL × SPY 相关性 + 中期选举窗口（对话分析，未建报告） | 全期 r=0.565、各分阶段 0.55-0.60、60 日滚动均值 0.52-0.64，**无脱钩**；中期选举（6 次）前 30 日 CCL 平均 +3.7% vs SPY +3.6%（超额 +0.1pp），近三轮牛市期全为负超额（2014/2018/2022 = −2.9/−8.7/−6.4pp）→ **CCL 无独立选举行情，= 大盘 beta 翻版**；当前定位（08-27）：$24.95、距60日高 −18.8%、YTD +0.0% |
| 对冲 | SPY 12月 OTM10% Put vs 11月 VIX 期货（9/1 会话） | 两者皆劣选：11 月 VX 期货时间错配（11/18 到期常在恐慌回落后）+ 无事件即 −4050/合约收敛损耗，是"已付过溢价的彩票"；12 月 OTM put 盈亏平衡 SPY<683.5（−10.9%）+ 月均 theta 0.24%。**主推 SPY 12/18 熊市看跌价差 690/630**（~$425/10万，成本<0.5%，盈亏平衡 −10.5%）；有浮盈可换 collar；若坚持波动率多头买 12 月 VX（19.21）不买 11 月；真实尾部在 NVDA/纳指，仓位修剪优先于买指数保险 |
| 勘误 | "升水≠选举已计价"（9/1 续，用户质询成立） | contango 是 VIX 期货常态（约80%时间），15→19 斜率大部分是波动率风险溢价（正常 carry）；**但结论（11月VX劣选）经历史检验反而更强**：①曲线月间增量 11 月并无异常凸点、选举风险定价在**退潮**（Nov-Sep 陡峭化 4.3pt 收敛至 2.45）；②本地 VIX 1995-今日线实证 8 月下旬 VIX 14-16 → T+60 交易日中位 14.0/P90 18.0/@19.05 买 11/18 结算≈押注超 P90 分位；③历届中期选举选举日后 10-15 交易日 VIX 回落 15-20%。**方法教训：比较升水要与"该期限正常 carry"比，不能直接与现货比** |
| 富途 | Futu MCP 重新授权 + OAuth 修复（`Temp/futu_oauth_reauth.py`） | futu-mcp 是远程 OAuth 端点（mcp.futunn.com/mcp），全线 -32603 = access token 过期且 refresh 失效；修复脚本动态注册新 client → 本地 127.0.0.1:59407 回调 → 浏览器授权 → 回写 mcpOAuth credentials（备份 .bak）。**坑**：python urllib 不支持 https 必须走 curl 子进程；PowerShell Start-Process URL 含 & 必须整串引号。**新 token 仅 2h 有效，但 refreshToken 可自动续期（实测可用，授权一次撑一周+）** |
| 富途 | 热门股榜 354 只 RSI 评估（09-01 晚） | Yahoo/stooq 均不可用（403/空），改走 Futu MCP over-HTTP（curl+Bearer token，SSE 解析）；Wilder RSI14（`Temp/rsi_futu_354.py`）；限流 0.25s pacing + 指数退避重试后 **354/354 全成**。报告 `reports/hot354_rsi_eval_20260901.html`：中位 RSI 48.0、超卖 12/超买 20、仅 41% 五日回升；23 只贴 52 周高（炼化 CVX/SLB/VLO/MPC/PSX/COP + 软件 CRWD/NOW/CRM/SNOW）；优质超卖=EIX/PCG/HWM/RCL/MGM，垃圾超卖=FFAI/BTAI/GPUS/TENX/VEEA；刚脱超卖=APP/GME；**板块×RSI 交叉透视 + 组合筛选（分档/自定义区间/板块下拉/搜索）**；板块归并 329 接口 + 25 MANUAL + KNOWN 字典兜底（加密 20 只/航天 10 只单列） |
| 自动化 | 每日定时任务已建立（09-01） | 每天 07:00 自动跑 `scripts/daily_hot_rsi.py` → `reports/hot_rsi_eval_YYYYMMDD.html` + `hot_rsi_latest.html`。关键实现：①Futu OAuth expiresAt 为**毫秒**；②access token 2h 过期但 refreshToken 自动续期回写；③screen 正确参数=schema 版（pagination 在响应顶层 next_key）；④过滤规则与 09-01 实证口径零误差（354/354）；⑤0.25s 限速+指数退避；⑥日志落 `~/.workbuddy/automation-logs/`。自动化 id f78907c8 |

## 二、重要方法论决策 / 新增约定（9/1）

1. **RSI 30 线无独立分层能力（56 号口径修正）**：<30 档内 62% 样本挤在 28-30 窄带，其超额主要来自深跌子集；细分档位无单调性、不需改阈值。**主口径保持 "RSI<30 × dd60≤-30%"**，真正的区分变量是回撤深度而非 RSI 数值。
2. **"反弹快" 不是买点信号**：d2m≤3（3 天内见顶）= 下跌中继/接飞刀聚集地；好买点是"深回撤 × 温和快速反弹且 20 日不破"。
3. **DCA 变体经验**：`RSI<30 定投到回归 30` 结束时大概率浮亏，要等 T+20 才转正且资金加权后 edge 薄（深熊期资金暴露最大）；更优变体 = 定投起点设回撤阈值（dd60≤-30%）或终止线放宽至 RSI 回 40/C 定投与"一次性买入"正交——DCA 解决择时恐惧，代价是深熊资金暴露。
4. **VIX 分析口径**：比较期货升水要与"该期限正常 carry"比，不能直接与现货比（contango 是常态）；评估选举定价要用历史条件分布（如本地 VIX 数据 T+60 P90=18.0）+ 时点错配（11/18 到期常在恐慌回落后）。
5. **选股器筛选**：简单字段查询（simple_field_query/property_query）可用、技术指标筛选报 invalid parameter 不可用；热门度排序用 featured_property=5214（综合热度）×1e5。
6. **Futu MCP over-HTTP 通道**（Yahoo/stooq 挂掉时）：curl+Bearer token → initialize 抓 Mcp-Session-Id → notifications/initialized → tools/call，SSE data: 行解析；quote_history_kline 只传 {symbol,end,num}（ktype 显式传值 schema 报错）；**0.25s pacing + 指数退避**可做到 354/354 全成。
7. **延续铁律**：60 日滚动主口径/显著性三档+p 值/参数图例/R 与 β 同列/单位陷阱 corr ×100 入库 build ÷100/收益原始全序列先算再 merge/README 登记前先 ls 校验/术语悬停浮窗禁速查表/红涨绿跌+Okabe-Ito/交付克制/尾 bar 体检剔除不完整 bar。

## 三、当日产出清单（9/1）

- **报告**：`reports/hot354_rsi_eval_20260901.html`（354 只 RSI + 板块透视 + 组合筛选，README 已登记）、`reports/hot_us_stocks_top300_20260901.html`、`reports/hot_us_stocks_top500_filtered_20260901.html`（热度榜，前次提交已含）
- **脚本**（scripts/）：`daily_hot_rsi.py`（每日定时任务入口，前次提交已含）、`ccl_rsi_sub30_deep.py`（前次提交已含）、`ccl_rsi30_dca.py`（本次新提交）
- **Temp/**：`futu_oauth_reauth.py`、`build_rsi_eval.py`（参数化构建）、`rsi_futu_354.py`、`rsi_retry_merge.py`、`fetch_plate_354.py`、`plate_bucket.py` 等（流水线前身，前次提交已含主要文件；本次仍有未跟踪中间产物不处理）
- **结果**（results/）：`ccl_rsi_sub30_deep.json`（前次提交已含）、`ccl_rsi30_dca.json`（本次新提交）、`rsi14_hot354_20260901.json`（前次提交已含）
- **数据**（data/）：`hot_us_stocks_20260901.csv`、`hot_us_stocks_filtered_20260901.csv`、`rsi14_hot354_20260901.csv`（前次提交已含）
- **README.md**：60 号、61 号相关、hot354 已登记
- **自动化**：每日 07:00 定时任务（id f78907c8，daily_hot_rsi.py）

## 四、git 状态与本次提交（2026-09-02 00:1x，每日交接）

**前情**：9/1 白天已按主题提交——`0f1483e`（富途热门 RSI 流水线 + 每日定时任务，17 文件）→ `654e59b`（CCL RSI<30 深度分析补交）。**本次交接前工作区剩余**：`.workbuddy/memory/2026-09-01.md`（+17 行：CCL×SPY 相关/VIX 对冲补记，未入库）、`results/ccl_rsi30_dca.json` + `scripts/ccl_rsi30_dca.py`（9/1 深夜 CCL DCA 回测产出，未入库）、`Temp/` 一批中间产物（按惯例不提交、不删除）。

**本次动作**（用户明确要求"提交到 github 即可"，已获 push 授权）：
1. 覆盖更新 `overview.md`（9/1 全天汇总，本文档）
2. `MEMORY.md` 补 9/1 要点（CCL 深分/DCA、RSI 30 无分层、Futu OAuth/限速通道、VIX 对冲结论、每日任务）
3. commit ①：CCL DCA 回测（脚本+结果）—— 主题独立
4. commit ②：交接文档 + 9/1 日志 + MEMORY 更新 —— 交接收尾
5. push（先试 ssh 22，被 reset 则走 ssh.github.com:443）→ ls-remote 验证远端与本地一致

**安全说明**：全程仅 add/commit/push；无删除/clean/reset/force；Temp/ 及任何未跟踪文件不做处理；全部改动可 git 回滚。

## 五、重要过程 / 踩坑（9/1）

- **Futu OAuth 全链路故障**：access token 2h 过期、refresh 也曾失效（invalid_grant "sig is invalid"）→ 需重授权；修复后确认 **refreshToken 可自动续期**（授权一次撑一周+），expiresAt 是毫秒单位。
- **python urllib 不支持 https**（该构建环境）：Futu/HTTPS 请求必须走 curl 子进程。
- **Futu MCP over-HTTP 三坑**：ktype 显式传值 schema 报错（只传 {symbol,end,num}）；分页 next_key 在响应顶层；**0.25s 限速**——持续突发首轮 174/354 失败，加指数退避后全成。
- **行情源不可用**：Yahoo/stooq 当天均 403/空，富途 MCP 成为备用通道（现已是每日任务数据源）。
- **中位数陷阱（DCA 回测）**：80 周期中 35 个 1 天假信号（占周期数 44% 只投 $1），把"每周期中位数"钉在 0/正；必须做**资金加权**才能反映真实体验（末日 −5.2%、T20 +1.08% vs 等权 +4.04%）。
- **未核实/遗留标注**：CCL 深分最优组合 9 次事件高度依赖 2008/2020 尾部行情（样本局限）；2020-04-01 +80.7% 是单次极值；VIX 曲线月间增量按 8/25 报道口径、本地数据已复核。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md + 项目 MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （简短内容，≤50字）`、按主题分 commit、**默认只本地 commit 不 push（用户明确要求才 push，本次已获授权）**。
- **高权限自我约束（用户本次明确叮嘱）**：不做删除/clean/reset/force 等破坏性操作，全部改动可 git 回滚；push 前先确认工作区状态。
- 交付必须产物展示（present_files + 自动打开预览）；交付不附图；HTML 报告出完后 CDP 无头验证兜底。
- 术语悬停浮窗不用速查表；红涨绿跌 + Okabe-Ito 色弱安全（叠线型/符号）；报告表格参数图例；R 与 β 同列。
- 结论必须先核实数据、无法核实标注「未核实」；评审四段式；相关性 60 日滚动主口径；交付克制（只做用户明确要求的内容）。
- CDP 仅在推特/X 抓取或常规手段不可行时启用，用完必关。

## 七、遗留待办 / 下次继续

- **★ CCL 落地**：当前 $24.95、距60日高 −18.8%、距250日高 −25.4%（08-27）；若选举前抛压带入 RSI<30 × dd60≤-30% 深跌区 = 历史最优买点（9 次 fwd20 中位 +24.5%）；已持有者参考 56 号"超卖后需脉冲窗口，非即时反弹"。
- **★ 每日 07:00 富途热榜 RSI 任务**（f78907c8）：跑 `scripts/daily_hot_rsi.py`，产出 hot_rsi_eval_YYYYMMDD.html；首跑请校验与 09-01 口径一致性；若 OAuth 过期跑 `Temp/futu_oauth_reauth.py`。
- **★ XAUUSD 60 号信号窗复核**：09-01 开盘原为买点（日线刚死叉 + 4h RSI 32.4），需在下次会话核对 T+5/T+10 实际走势与胜率预期是否兑现。
- **9/4 8 月非农分水岭**（沿用）：若为负（连续 2 月）→ 按先例=衰退起点解读，9/15-16 FOMC 加息概率大幅回吐；落地后复核 10Y-2Y/10Y-30Y 精确值（8/28 后未核实）。
- **58 号主报告修订**（沿用）：仍是 CL 单口径旧版，须补 XLE 双口径表述（"脱油价锚、未脱能源板块锚"，CF 对 XLE β≈1.1）。
- **57 附 p 值 bug**（沿用）：主报告 index.html 手写 t CDF 错误待修（附版 scipy 已对）。
- **9 月 ASO ONI 发布后**（沿用）：复核残差表 onset 后是否重新扩张；ASO≥+1.5 则上调 2015 剧案权重。
- **待验证**（沿用）：拉 NG=F + 谷物期货（玉米/大豆/棕榈）验证 CF 成本链与厄尔尼诺→谷物→化肥传导。
- **52 号 MCD 操作跟踪**（沿用）：4% 反弹目标（260→270.5）、收盘止损 <255/<253。
- **Temp/**：`_hf.txt`、`hot300.txt`、`rsi_run.log`、`rsi_retry.log`、`futu_oauth.log`、`plate_354_raw.json`、`memory_removed_2e7b65ad.md`、`gold_us10y_chart.json`、`dgs10_latest.csv` 等为中间产物，保留未跟踪，需时可随时重拉。