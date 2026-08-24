# -*- coding: utf-8 -*-
"""筛选蓝筹池：从 data/ 已有个股CSV中挑出「低波动 + 优质」的大盘蓝筹。

口径（均在最终报告中披露）：
- 候选池 = 已知大盘蓝筹个股（手工名单，排除ETF/指数/宏观CSV）
- 波动率 = 近5年(2021-08~2026-08)日收益年化标准差
- 质量代理 = 入池标的本身为大型成熟蓝筹（盈利稳定、行业龙头）；
  另要求上市数据 >= 2000 个交易日，数据覆盖至 2026-01 之后（数据新鲜）
- 过滤：年化波动率 <= 阈值(默认0.32) 且 近5年区间内样本 >= 600 天
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# 明确排除的 ETF / 指数 / 宏观文件（目录名）
EXCLUDE = {
    "spy", "qqq", "soxx", "ibb", "xbi", "ihi", "utes", "xlb", "xlc", "xle",
    "xlf", "xli", "xlk", "xlp", "xlu", "xlv", "xly", "xph", "kbwb", "kre",
    "kie", "bug", "vix",
}
# 宏观/利率 CSV（非目录，直接跳过）

# 蓝筹候选名单（大盘成熟股，行业龙头；包含药明康德 H/A）
BLUECHIP_CANDIDATES = [
    # 科技/消费科技
    "aapl", "msft", "amzn", "nvda", "crm", "csco", "ibm", "orcl",
    # 消费
    "ko", "pep", "pg", "wmt", "mcd", "nke", "sbux", "dis", "hd", "mo", "pm",
    # 医疗
    "jnj", "mrk", "lly", "abbv", "amgn", "gild", "biib", "vrtx", "regn",
    "tmo", "dhr", "wat", "unh",
    # 工业
    "mmm", "ba", "cat", "cvx", "ge", "hon", "lnt", "shw", "xom",
    # 金融
    "axp", "gs", "jpm", "ma", "ms", "v", "blk", "bx", "kkr", "apo",
    "ibkr", "trow", "trv", "brk.b",
    # 电信/公用
    "vz", "ceg", "vst", "nee", "sre", "xel", "etr", "cnp", "nrg",
    # 中国蓝筹（H/A）
    "2359.hk", "603259.ss",
]


def load_daily(symbol):
    path = os.path.join(DATA_DIR, symbol, f"{symbol}, 1D.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    if "adj_close" not in df.columns or df["adj_close"].isna().all():
        df["adj_close"] = df["close"]
    return df


def main():
    vol_cutoff = float(sys.argv[1]) if len(sys.argv) > 1 else 0.32
    rows = []
    loaded, missing = [], []
    for sym in BLUECHIP_CANDIDATES:
        df = load_daily(sym)
        if df is None or len(df) < 2000 or df["date"].max() < pd.Timestamp("2026-01-01"):
            missing.append(sym)
            continue
        # 近5年
        cutoff = df["date"].max() - pd.DateOffset(years=5)
        recent = df[df["date"] >= cutoff]
        if len(recent) < 600:
            missing.append(sym)
            continue
        ret = recent["adj_close"].pct_change().dropna()
        ann_vol = float(ret.std() * np.sqrt(252))
        # 近5年累计收益（质量信号之一，不硬过滤）
        cum = float(recent["adj_close"].iloc[-1] / recent["adj_close"].iloc[0] - 1)
        rows.append({
            "symbol": sym, "n_days": len(df), "start": str(df["date"].iloc[0])[:10],
            "end": str(df["date"].iloc[-1])[:10], "ann_vol": ann_vol, "cum5y": cum,
        })
        loaded.append(sym)

    df_out = pd.DataFrame(rows).sort_values("ann_vol")
    passed = df_out[df_out["ann_vol"] <= vol_cutoff]
    print(f"# 候选 {len(BLUECHIP_CANDIDATES)} 只，成功加载 {len(loaded)} 只，缺失/数据不足 {len(missing)} 只: {missing}")
    print(f"# 波动率阈值 {vol_cutoff:.0%} 下入围 {len(passed)} 只\n")
    for _, r in df_out.iterrows():
        mark = " *" if r["symbol"] in set(passed["symbol"]) else ""
        print(f"{r['symbol']:>10s}  n={r['n_days']:5d}  {r['start']}~{r['end']}  "
              f"annVol={r['ann_vol']:.1%}  cum5y={r['cum5y']:+.1%}{mark}")
    print("\nUNIVERSE=" + ",".join(passed["symbol"].tolist()))


if __name__ == "__main__":
    main()
