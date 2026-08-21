---
name: support-resistance-levels
display_name: 支撑阻力与趋势线识别
description: 支撑/阻力位识别与下降趋势线突破检测（金融技术分析）。This skill should be used when the user asks to identify support/resistance levels from price data, detect trendlines or descending trendline breakouts, quantify "重要支撑位/阻力位", analyze key price levels for stocks/ETFs, or asks how to turn visual chart analysis (支撑位/趋势线/突破) into algorithmic rules. Triggers: "找支撑位/阻力位", "识别支撑", "趋势线突破", "下降趋势线", "key support levels", "trendline breakout detection". 将人眼看图识别支撑阻力/趋势线的过程翻译为显式算法（分形 swing + 水平聚类 + ATR 归一化容差 + 评分 + 破位检测），并给出事件研究验证。
agent_created: true
---

# 支撑阻力与趋势线识别（支撑/阻力 + 下降趋势线突破识别）

## Overview

人眼"看图看出支撑位/阻力位/趋势线"本质上是并行统计：多次触及、密集成交、长时间存活。本 skill 把这套直觉翻译成显式、可复现、可验证的算法，直接在日线数据上运行，并输出带评分的水平清单 + 事件研究统计。

使用场景：
- 用户问"XX 的重要支撑位在哪/阻力位在哪"
- 用户问"识别下降趋势线""趋势线突破了吗"
- 用户问"AI 如何看图识别支撑/趋势线"（方法论类）
- 需要将图表语言（支撑、阻力、趋势线、突破）量化成可回测规则

## 核心方法论（两条可独立使用的工作流）

### 工作流 A：支撑/阻力位识别（`scripts/support_levels_demo.py`）

**四步算法**（把"看图"显式化）：
1. **Swing 分形**：左右各 3 根 K 线的局部极值 → 数字化"这里有个低点/高点"
2. **水平聚类**：容差 = 0.75 × ATR14 中位（近 60 日）的一维贪心聚类 → 数字化"这几个价位差不多是一条线"。**必须用 ATR 归一化容差**（不同股票波动刻度不同）
3. **评分排序**：`score = 触击次数^1.2 × 触击后 5 日反弹/回落中位(%) × min(1, 存活天数/200)` → 数字化"这条线多重要"。破位线（近 10 日收盘穿透带边界）自动降级
4. **有效性验证**：把 swing low 触击后 5 日表现 vs 无条件对照（任意日 5 日收益）对比

运行方式：
```bash
python scripts/support_levels_demo.py <TICKER> [--months 18] [--out path]
```
- 默认输出 `results/support_<ticker>.json`
- 脚本自动向上查找含 `data/` 的目录（支持项目根与 skill 目录两种摆放）

**报告可视化**：参考项目 `scripts/build_support_ms_demo.py`（ECharts K 线 + markLine 支撑绿实线/阻力红虚线 + 触击次数标签，色弱安全：红涨绿跌 + 线型/符号区分 —— 项目硬规范）。

### 工作流 B：下降趋势线识别 + 突破事件研究（`scripts/trendline_breakout.py`）

**四步算法**：
1. **Swing high 分形**（左右 3 根）
2. **下降链拟合**：取最近 2~4 个**依次下降**的 swing high，OLS 拟合直线，要求斜率 < 0 且 R² ≥ 0.6 → 数字化"空头持续在更低位置卖出"
3. **趋势活性**：收盘须在线值下方 0.15×ATR 且近 3 日未越线 → 数字化"下降趋势还活着"
4. **突破事件**：收盘自下方上穿线值 = 事件；30 日冷却去重；记录突破日涨幅/量比/跳空（突破质量）；计算 fwd5/10/20 收益 vs 全史对照

运行方式：
```bash
python scripts/trendline_breakout.py [TICKER...] [--out path]
# 默认 GILD CEG VST MS；不传参即跑默认票池
python scripts/trendline_breakout.py MS
```

**已验证的实证结论（2026-08，四票 67 事件）——报告时直接引用**：
- 突破当天追入是差的：fwd5 中位 −0.33%、胜率 46%（对照 +0.34%/54%）
- 优势在 fwd10~fwd20：fwd20 中位 +2.28%、胜率 61%
- **质量过滤**：放量 ≥1.5x 的突破 fwd10 胜率 75%、fwd20 中位 +4.65% 胜率 83%；弱突破（涨<2%+缩量）fwd20 中位 −0.28%
- 结论口径：趋势线突破不是"当天买"信号，而是"放量突破 + 持有 10~20 日"的过滤条件

**报告可视化**：参考项目 `scripts/build_trendline_breakout_report.py`（方法论 4 步卡片 + 事件 vs 对照柱状 + 质量过滤分组柱状 + 案例 K 线带趋势线虚线 + 突破日标记）。

## 报告规范（项目硬性要求）

- 浅底深字研报风 + ECharts（CDN 引入 echarts@5）
- **红涨绿跌**，且色弱安全：不可只靠红绿区分，叠加线型（实线/虚线）、符号（▲▼◆）、数值标签
- 数据 JSON 注入用 `var DATA = __DATA_JSON__;` 占位符再 replace
- build 脚本必须静默写盘：只 print `written: <path> size=xxx`
- 交付前必须过 SSR 渲染测试（playwright-core + 本机 Chrome executablePath，`chromium.launch({executablePath})`，收集 pageerror/console error）

## 方法与局限（回复用户时必须声明）

- 线的画法有主观性：锚点选 2 个还是 4 个、线性 vs 对数刻度，结论可能不同——算法把自由度显式化，但非"唯一正确"
- 单日越线突破 fwd5 普遍负，假突破是常态，需回踩确认/两日确认
- 样本小（过滤后 n=10~12）、幸存者偏差（现存大票）
- 对照组须注明口径（无条件对照有 up-bias，严格做法是"同价格区间非事件随机点"）
- 所有"突破有 alpha"结论须标注为初步/样本内

## Resources

### scripts/
- `support_levels_demo.py`：支撑/阻力识别（CLI，任意 ticker）
- `trendline_breakout.py`：下降趋势线突破扫描 + 事件研究（CLI，任意票池）

### references/
- （可选扩展位：方法论详解文档可放这里，保持 SKILL.md 精简）

### assets/
- （预留：报告模板等）

## 已知迭代方向（下轮增强时参考）

- 成交量加权（POC/价值区间，把换手成本位纳入）
- 多时间周期融合（周线支撑优先级高于日线）
- 事件研究显著性检验（Fisher 精确/置换检验）
- 与均线突破（EMA20/50 上穿）并列对比，回答"趋势线突破是否有独立 alpha"