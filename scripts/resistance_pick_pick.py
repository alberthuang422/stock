# -*- coding: utf-8 -*-
"""随机挑选 10 只美股（固定种子可复现），输出 ticker 列表"""
import json
import random

# 美股流动性池（S&P 500 常见成分 + 热门标的，剔除低流动性/数据异常风险）
POOL = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "AMD", "NFLX",
    "ADBE", "CRM", "ORCL", "INTC", "QCOM", "TXN", "AMAT", "MU", "LRCX", "KLAC",
    "CSCO", "IBM", "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP",
    "UNH", "JNJ", "PFE", "MRK", "ABBV", "LLY", "TMO", "DHR", "ABT", "MDT",
    "XOM", "CVX", "COP", "SLB", "OXY", "EOG", "PSX", "VLO",
    "WMT", "COST", "PG", "KO", "PEP", "MCD", "SBUX", "NKE", "HD", "LOW",
    "DIS", "CMCSA", "T", "VZ", "BA", "CAT", "DE", "GE", "HON", "MMM",
    "UBER", "ABNB", "SHOP", "SNOW", "PLTR", "COIN", "MRNA", "GILD", "ISRG", "SYK",
    "RIVN", "LCID", "SPCE", "DKNG", "SQ", "PYPL", "ETSY", "Z", "ZM", "DOCU",
]

def main():
    random.seed(20260902)
    picks = random.sample(POOL, 10)
    print("SELECTED:", json.dumps(picks))
    with open("Temp/resistance_picks.json", "w", encoding="utf-8") as f:
        json.dump({"seed": 20260902, "pool_size": len(POOL), "tickers": picks}, f, ensure_ascii=False, indent=2)
    print("saved -> Temp/resistance_picks.json")

if __name__ == "__main__":
    main()
