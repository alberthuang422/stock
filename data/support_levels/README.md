# 支撑位批量计算结果（data/support_levels）

生成时间：2026-08-25 22:14:38
覆盖：100 只代码 / 3550 条支撑位记录（levels_summary.csv）

## 口径说明（用户确认，覆盖 skill 默认值）

算法：工作流 A — swing 分形 + 水平聚类 + 评分（见 .workbuddy/skills/support-resistance-levels/SKILL.md）。

1. **数据**：`data/{ticker}/{ticker}, 1D.csv`（列 date,open,high,low,close,volume,adj_close），全历史不截窗。
2. **Swing 分形**：左右各 3 根 K 线的局部极值；定位局部低点用 **raw low**。
3. **支撑带基准价**：swing low 所在 K 线的 **adj_close（复权价）**。带 = 基准价 × (1 ± 2%)。
4. **水平聚类**：候选价为各 swing low 的 adj_close；按升序贪心合并，**合并判定 = 新元素下沿 ≤ 簇中心上沿（带相接/重叠即并线）**，聚类中心为加权均值。
5. **触碰判定**：当日 low ≤ 带高（band_hi）视为进入带。同一轮（连续无整日离开带，离开 = low > band_hi）只计 1 次；
   触碰代表日取轮内 close 最低日（touch_low/touch_close 为 raw 价格明细）。
   - 轮内任一日收盘 ≥ 带低（band_lo）→ 有效触碰；
   - 整轮收盘刺穿下沿（close < band_lo）→ 需「修复」：自轮末起 10 个交易日内收盘回带上方（close ≥ band_hi）才算有效触碰，否则不计（真破位剔除）。
6. **过滤**：有效触碰 ≥ 3 次 且 首末触碰跨度（交易日 index 差）≥ 21。
7. **分档（level）**：1Y+（span ≥ 252）/ 6M+（≥ 126）/ 3M+（≥ 63）/ 1M+（≥ 21）。
8. **dist_pct** = (last_close − support_mid) / support_mid × 100；last_close 为数据末日的 **adj_close**。
9. **status**：above（dist_pct > +3%）/ near（±3% 内）/ below（dist_pct < −3%，已跌破）。
10. **strength**：touches ≥ 6 且 span ≥ 126 → A；touches ≥ 4 且 span ≥ 63，或 touches ≥ 8 → B；其余 → C。

## 文件结构

- `levels_summary.csv`：每只股票每个支撑位一行（15 字段）
- `touches/{ticker}.csv`：逐次触碰明细（7 字段）
- `README.md`：本文件

## 字段字典

levels_summary.csv：
| 字段 | 说明 |
|---|---|
| ticker | 代码（目录名，小写） |
| support_id | 同股票内编号，S1 最靠近现价（按 abs(dist_pct) 升序） |
| support_mid | 支撑带基准价（adj_close 口径，聚类中心） |
| support_lo / support_hi | 带下沿 / 带上沿（mid × (1∓2%)） |
| touches | 有效触碰次数 |
| first_touch_date / last_touch_date | 首次 / 末次触碰日期 |
| span_trading_days | 首末触碰跨度（交易日 index 差） |
| level | 1M+ / 3M+ / 6M+ / 1Y+ |
| last_close_date / last_close | 数据集末日及 adj_close 收盘 |
| dist_pct | (last_close − mid)/mid × 100 |
| status | above / near / below |
| strength | A / B / C |

touches/{ticker}.csv：
| 字段 | 说明 |
|---|---|
| ticker | 代码 |
| support_id | 对应支撑编号 |
| support_mid | 支撑带基准价 |
| touch_seq | 该支撑内按时间顺序的触碰序号 |
| touch_date | 触碰代表日（轮内 close 最低日） |
| touch_low / touch_close | 该日 raw low / raw close（实时口径明细） |

## 跳过/异常清单（1 只）
- ibkr: 缺列 ['date', 'volume', 'adj_close']
