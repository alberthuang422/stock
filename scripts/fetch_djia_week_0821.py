# 补拉道指 30 成分股上周(8/17-8/21)行情数据，计算周度涨跌幅
# 基准：8/14(上周五)收盘 -> 8/21(上周五)收盘
import json
import time
import urllib.request

DOW = [
    "AAPL", "AMGN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS", "GS",
    "HD", "HON", "IBM", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK", "MSFT",
    "NKE", "NVDA", "PG", "SHW", "TRV", "UNH", "V", "VZ", "WMT", "DOW",
]

P1 = 1786665600  # 2026-08-14 (含基准日)
P2 = 1787356800  # 2026-08-22

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
}


def fetch(sym):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
        f"?period1={P1}&period2={P2}&interval=1d&events=history"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def main():
    results = []
    for sym in DOW:
        try:
            data = fetch(sym)
            res = data["chart"]["result"][0]
            ts = res["timestamp"]
            q = res["indicators"]["quote"][0]
            rows = []
            for i, t in enumerate(ts):
                if q["close"][i] is None:
                    continue
                d = time.strftime("%Y-%m-%d", time.gmtime(t))
                rows.append((d, q["close"][i]))
            # 取区间首尾 (按交易日序列)
            if len(rows) < 2:
                print(f"{sym}: 数据不足 {len(rows)}")
                continue
            dates = [r[0] for r in rows]
            prev = rows[0][1]   # 基准日 8/14
            last_d = dates[-1]
            last = rows[-1][1]  # 最新日 (8/21 或更早)
            if last_d < "2026-08-21":
                print(f"{sym}: 最新数据仅到 {last_d}，缺失上周五")
            chg = (last / prev - 1) * 100
            results.append((sym, prev, last, last_d, chg))
            print(f"{sym:5s} {dates[0]}->{last_d}  收盘 {prev:.2f}->{last:.2f}  周涨跌 {chg:+.2f}%")
        except Exception as e:
            print(f"{sym}: ERROR {e}")
        time.sleep(0.4)

    print("\n=== 排序 (周跌幅最大在前) ===")
    results.sort(key=lambda x: x[4])
    for sym, prev, last, d, chg in results:
        print(f"{sym:5s} {chg:+7.2f}%  ({prev:.2f} -> {last:.2f} @ {d})")


if __name__ == "__main__":
    main()