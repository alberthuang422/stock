# 自动化任务记忆：全股票支撑位计算（一次性）

## 2026-08-25 22:00 首次执行（完成）

- **任务**：按 skill `support-resistance-levels` 工作流 A，批量计算 data/ 下全部股票日线支撑位。
- **用户口径**（覆盖 skill 默认值）：±2% 支撑带容差（非 ATR）；swing 定位用 raw high/low、基准价与距离用 adj_close 复权；触碰≥3 次且首末跨度≥21 交易日；修复（刺穿下沿后 10 日内收盘回带内）计入；分档 1M+/3M+/6M+/1Y+。
- **结果**：levels_summary.csv **3550 行 / 100 只覆盖**（跳过 1：ibkr 目录仅含 BATS_IBKR 的 MACD 指标文件，缺 OHLCV 列）。
- **输出**：data/support_levels/{README.md, levels_summary.csv, touches/{ticker}.csv}，全部校验通过（带宽±2%、触碰≥3、跨度≥21、带无重叠、S1 最近、序号/计数一致）。
- **脚本**：scripts/compute_support_levels_all.py（可重复运行，幂等覆盖输出）。
- **关键实现要点**（复跑/复用必读）：
  - 进带判据 = K 线与带相交（low≤hi 且 high≥lo），否则历史低价期会被误计触碰；
  - 聚类合并判定 = 新元素下沿 ≤ 簇中心上沿（数学上保证带不重叠，勿用固定 2% 容差）；
  - BATS_* 文件仅当目录无普通 1D 文件时才回退使用；
  - 遍历时排除 support_levels 输出目录自身。