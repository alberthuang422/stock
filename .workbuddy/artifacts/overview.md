# 工作交接文档（2026-08-24 全天）

> 本文件是每日收尾交接文档，汇总当日工作产出、关键结论、git 状态与遗留待办，供后续会话快速恢复上下文。逐日明细见 `.workbuddy/memory/YYYY-MM-DD.md`，长期要点见 `.workbuddy/memory/MEMORY.md`。

## 一、当日工作全景

| # | 主题 | 核心结论（一句话） |
|---|---|---|
| 28 | KO vs PEP 相对强弱 + KO 基本面 | KO 全窗口碾压（YTD +33.6% vs +2.9%，3Y +64.5% vs -12.1%）；盈利质量差距（净利率 33% vs 12%）+ PEP 三重逆风（GLP-1 冲击零食、$4.56/加仑高油价、促销 -15%）；KO 74/100 Bullish，唯一短板估值 27.4x |
| 29 | SBUX 星巴克基本面 | 转型兑现真实但估值已定价大半：63/100 NEUTRAL；FY26Q3 全球同店 +7.9%、adj EPS $0.85 beat、上调指引；forward PE ~36x vs 同业中位 20x 偏贵；未持有不追高、等 FY26Q4 |
| 30 | 资管 APO/BX/KKR × US10Y-2Y 走阔 | ①走阔方向弱信号（R²<1%）；②**大幅走阔（>+30bp/月）资管重挫 -6.8%/31% vs 银行抗跌 = 走阔幅度代理危机烈度（2008/SVB）**；③严格熊陡资管最强（+5.71%/81.8%，与银行相反）；④走阔后 3 月超额 +8.6%、12 月 SPY 反超（超额偏短周期） |
| — | DHR vs TMO 生物科技卖铲人对比 | 商业模式 DHR 略优（毛利率 59.2%、经常性收入 81.9%、工艺锁定+DBS），资本回报 TMO 优（ROE 13% vs 7.1%、FCF $62.9亿、CDMO 抗周期）；DHR P/E 44.7x 溢价更贵 |
| — | US10Y-2Y × SBUX 传导 | 2026-08-20 读数 10Y 4.69%/2Y 4.19%，近 1 月 2Y -14bp → 温和牛陡；对 SBUX 中性偏负（贴现率↑压估值+咖啡豆成本），危机型深牛陡例外（避险资金流入） |
| — | 每日收尾交接 + GitHub 提交 | 本 automation：8/24 全天汇总入库并推送（详见第四节） |

## 二、重要方法论决策 / 新增约定（8/24）

1. **资管类结论一律以 2011-11 起同窗口（common）为准**——APO 2011 上市，早期窗口为空（30 号报告踩坑备忘）。
2. **buckets 中位数必须乘 100**（比率 → 百分数），30 号报告首版漏乘已修。
3. 报告 28 评分体系参考：五维（经营/负债/现金流/估值/资本配置）+ blend 权重修正（一次性、出表口径、多源一致）。
4. 项目惯例重申：file:// 协议下 fetch 本地 JSON 被 CORS 拦截 → **图表数据一律内联嵌入 HTML**。

## 三、当日产出清单（reports/ 编号）

- `28_ko_vs_pep_相对强弱研究.html`（KO vs PEP，含 KO 五维评分 74）
- `29_sbux基本面分析/sbux基本面分析-20260824.html`（ECharts 价格+10年财务，图/表切换）
- `30_资管陡峭化/index.html`（ECharts 8 图 8 表：五档/形态/回归/同窗口/24 段走阔明细/20 个月熊陡/7 案例/持有）
- `DHR_vs_TMO_生物科技卖铲人对比.html`（自包含对比表格+五维度+Bull/Bear+数据溯源）
- 脚本：`scripts/steep_am.py`、`scripts/ko_pep_relative.py`、`scripts/fetch_ko_pep_cdp.cjs`；结果 `results/steep_am.json`、`results/ko_pep_relative*.json`、`results/us10y_us2y_latest.json`
- 文档：`.workbuddy/artifacts/ko_pep_report_28_overview.md`

## 四、git 状态与本次提交（2026-08-25 00:0x，automation）

**前情**：8/24 白天已提交报告 28/30 + 日志（`0fc7c22`/`d333120`/`88a2ae4`/`965e888`）；本次 automation 补交遗留 + 更新交接文档。

本次提交（按主题分 commit）：
| commit | 内容 |
|---|---|
| `2026-08-24` | 报告 29 SBUX 基本面分析 |
| `2026-08-24` | DHR vs TMO 卖铲人对比 + US10Y-2Y 当日数据 |
| `2026-08-24` | KO vs PEP 报告 28 overview 文档补入库 |
| `2026-08-25` | 交接文档更新（8/24 全天汇总）+ 日志追加 |

**未入库（有意保留）**：`.workbuddy/tmp/`（临时工具脚本，从未跟踪）；`scripts/fetch_djia_week_0821.py`（8/21 遗留脚本，无当日产出，避免混入无关内容）。

**push**：原远端 `9e4b75f` → push 后以 `git ls-remote origin main` 验证新 HEAD。

## 五、重要过程 / 踩坑

- EDGAR 抓 10-K 必须合规 UA（`-A "Research research@example.com"`）否则 403；3MB HTML 用 curl 下载 + python 正则提段落/表格更快（`tmp/tables10k.py` 可复用）。
- 富途 `quote_valuation_detail` / `history_kline` 参数必须**字符串类型**，否则校验失败；估值分位对 SBUX 仅富途覆盖。
- DHR 2026H1 债务骤增系发债（4 月美元票据 + 6 月私募 CHF 23.83 亿、1.65%-2.51%），用途收购/回购，**非经营恶化**。
- SBUX 负股东权益 -$84.6 亿系举债回购所致（非资不抵债），杠杆已降至 2.9×；FY26Q4（10 月底）才是干净读数。
- 资管 vs 银行对利率形态**反应相反**（资管熊陡最强、银行加息陡最强）——验证用户关注点「形态决定一切」；大幅走阔=信用/流动性危机代理。

## 六、用户规则（长期，详见 ~/.workbuddy/MEMORY.md）

- git 提交格式 `yyyy-mm-dd  msg: （≤50字）`、按主题分 commit、只本地 commit 不 push（除非用户明确要求，如本 automation）。
- 交付不附图；红涨绿跌 + Okabe-Ito 色弱安全（叠符号/线型）；严格口径（不要股息/容差缓冲）。
- 结论必须先核实数据，无法核实标注「未核实」；评审四段式；相关性以 60 日滚动为主口径。

## 七、遗留待办 / 下次继续

- 工作区未提交项：仅 `fetch_djia_week_0821.py`（有意保留）与 `.workbuddy/tmp/`；其余已全部入库推送。
- 生物医药跟踪点：HARMONi-3 终局（2026H2）、OMB 名单（2026-12）、工具弹性主升段预期 2026Q4-2027（届时验证传导链）。
- SBUX：等 FY26Q4 验证利润率自主扩张，回调 $97-100 观察位；KO：Q3（10 月）+ Fairlife 勒索软件事件。
- 未核实项留档：NVO 美国专利年份（2031 vs 2033 来源打架）——建议以 FDA Orange Book + 10-K 为准。