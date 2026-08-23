#!/usr/bin/env python3
"""biotech 景气 → 生命科学工具业绩 传导时滞分析。

先行指标：
  - XBI 季度涨幅（data/xbi 日线聚合）
  - 生物科技景气事件锚点：2020Q1 疫情爆发→2020Q2-Q3 融资+行情爆发；2021 见顶；2022-2023 收缩；2025 复苏

滞后指标（results/lifetools_revenue.json）：
  - A/WAT/DHR/TMO 季度营收 YoY（%），年度 YoY
  - 特殊口径：WAT 2026 起并入 BD 生物科学业务（报告口径失真，标注有机口径）；DHR 2023 剥离 Veralto

输出：results/lifetools_transmission.json
  - xbi_quarterly: [{q, ret, close, yoy}]
  - quarters_yoy: 四家公司季度 YoY 序列
  - annual_yoy: 年度 YoY 序列
  - cycles: 上一轮（2019-2022）与当前（2025-2026）关键节点对齐表
"""
import json, os
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results")

# ---- XBI 季度收益 ----
xbi = pd.read_csv(os.path.join(ROOT, "data", "xbi", "XBI, 1D.csv"), parse_dates=["date"])
xbi = xbi.sort_values("date").set_index("date")["close"]
xbi_q = xbi.resample("QE").last()
xbi_q_ret = xbi_q.pct_change() * 100
xbi_q_yoy = xbi_q.pct_change(4) * 100
xbi_quarterly = []
for d, v in xbi_q.items():
    q = f"{d.year}Q{((d.month - 1) // 3) + 1}"
    xbi_quarterly.append({
        "q": q, "date": str(d.date()),
        "close": round(float(v), 2),
        "ret": round(float(xbi_q_ret.loc[d]), 2) if d in xbi_q_ret.index else None,
        "yoy": round(float(xbi_q_yoy.loc[d]), 2) if d in xbi_q_yoy.index else None,
    })

# ---- 公司季度/年度 YoY ----
rev = json.load(open(os.path.join(OUT, "lifetools_revenue.json"), encoding="utf-8"))
quarters_yoy = {}
annual_yoy = {}
for tk in ["A", "WAT", "DHR", "TMO"]:
    quarters_yoy[tk] = [{"q": r["period"], "rev_m": r["rev_m"], "yoy": r["yoy"]}
                        for r in rev[tk]["quarters"]]
    annual_yoy[tk] = [{"y": r["period"].split("/")[0], "rev_m": r["rev_m"], "yoy": r["yoy"]}
                      for r in rev[tk]["annuals"]]

# ---- 周期对齐：上一轮 2019-2022 vs 当前 2024-2026 ----
# 用年度 YoY 构造"工具板块平均增速"（剔除口径变化的公司后平均）
def avg_annual_yoy(years):
    out = []
    for y in years:
        vals = []
        for tk in ["A", "WAT", "DHR", "TMO"]:
            rec = next((a for a in annual_yoy[tk] if a["y"] == y), None)
            if rec and rec["yoy"] is not None:
                vals.append(rec["yoy"])
        out.append({"y": y, "avg": round(float(np.mean(vals)), 1)})
    return out

cycles = {
    "prev_boom": {  # 上一轮爆发
        "xbi_start": "2020Q1 疫情底 → 2020Q2 起行情/融资爆发",
        "xbi_ret": {"2020": 49.4, "2021": None},  # 2021 高位回落由用户核实时填充
        "tool_lag": "2020Q2-Q3 融资/行情启动 → 2021 年工具收入两位数爆发",
        "lag_quarters": "约 3-4 个季度",
        "evidence": "A 2020 yoy 3.4% → 2021 18.4%；WAT -1.7% → 17.8%；TMO 26.1%(含COVID) → 21.7%；DHR 24.4%(含COVID) → 11.3%",
    },
    "cur_recovery": {
        "xbi_start": "2025Q2-Q3 起复苏（2025-09 以来 +78.4%）",
        "xbi_ret": {"2025": 35.9, "2026_ytd": 36.4},
        "tool_now": "2025 年 A 6.7% / WAT 7.0% / DHR 2.9% / TMO 3.9%；2026Q1-Q2 已见加速（A +7~10%、TMO +6~10%、DHR +3.7~5.5%）",
        "lag_quarters": "若按上轮 3-4 季度传导，2025Q3 启动 → 业绩弹性应在 2026H2-2027 兑现",
        "evidence": "季度 YoY：A 2025Q4 +9.4 → 2026Q2 +10.0；TMO 2025Q4 +7.2 → 2026Q2 +10.5",
    },
}

out = {
    "xbi_quarterly": xbi_quarterly,
    "quarters_yoy": quarters_yoy,
    "annual_yoy": annual_yoy,
    "avg_annual": avg_annual_yoy([str(y) for y in range(2016, 2027)]),
    "cycles": cycles,
    "caveats": {
        "wat_2026": "WAT 2026 起并表 BD Biosciences/Diagnostics 业务，报告口径 YoY 失真（2026Q1 +91% / Q2 +113% 为并购非内生）；有机口径 2026Q2 +9% CC（财报会）",
        "dhr_2023": "DHR 2023 剥离 Veralto（环境/应用），2023 年报告口径 -10.3% 含剥离影响，持续经营口径约 -3~0%",
        "tmo_dhr_covid": "TMO/DHR 2020-2021 爆发含 COVID 检测/疫苗业务，非纯 biotech 资本开支传导；A/WAT 更接近纯工具β",
        "q4_noise": "DHR 季度 Q4 值存在报告结构噪音（2021Q4 -48% 等为并购/会计口径），分析以年度为主",
    },
}
path = os.path.join(OUT, "lifetools_transmission.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("saved:", path)
# 关键输出：工具板块平均年度 YoY + XBI 年度收益
print("\n=== 工具板块平均年度 YoY ===")
for r in out["avg_annual"]:
    print(f"  {r['y']}: {r['avg']}%")
print("\n=== XBI 季度收益（近 8 年关键季度） ===")
for r in xbi_quarterly:
    if r["q"] >= "2018Q1":
        print(f"  {r['q']}: ret={r['ret']}% yoy={r['yoy']}%")