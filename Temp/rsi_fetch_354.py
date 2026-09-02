# -*- coding: utf-8 -*-
"""Fetch ~1y daily bars for the 354 filtered hot US stocks, compute Wilder RSI14."""
import csv, json, subprocess, time, math
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
NOW = int(time.time())
P1 = NOW - 420 * 86400  # ~14 months calendar -> ~280 trading days

def curl(url):
    r = subprocess.run(["curl", "-s", "--max-time", "20", "-H", f"User-Agent: {UA}", url],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout

def fetch(tkr):
    y = tkr.replace(".", "-")
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{y}?period1={P1}&period2={NOW}&interval=1d"
        try:
            d = json.loads(curl(url))
            res = d["chart"]["result"][0]
            closes = res["indicators"]["quote"][0]["close"]
            ts = res["timestamp"]
            pairs = [(t, c) for t, c in zip(ts, closes) if c is not None]
            if len(pairs) >= 30:
                return pairs
        except Exception:
            pass
        time.sleep(0.5)
    return None

def wilder_rsi(closes, n=14):
    # returns list aligned with closes (None for first n)
    out = [None] * len(closes)
    gains = losses = 0.0
    for i in range(1, n + 1):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0); losses += max(-ch, 0)
    ag, al = gains / n, losses / n
    out[n] = 100 - 100 / (1 + (ag / al if al > 0 else float("inf") if ag > 0 else 0)) if (ag + al) > 0 else 50.0
    if al == 0 and ag > 0: out[n] = 100.0
    for i in range(n + 1, len(closes)):
        ch = closes[i] - closes[i - 1]
        g, l = max(ch, 0), max(-ch, 0)
        ag = (ag * (n - 1) + g) / n
        al = (al * (n - 1) + l) / n
        out[i] = 100.0 if al == 0 and ag > 0 else (0.0 if ag == 0 and al > 0 else (100 - 100 / (1 + ag / al) if al > 0 else 50.0))
    return out

def main():
    rows = list(csv.DictReader(open(r"C:/Users/Administrator/Desktop/stock/data/hot_us_stocks_filtered_20260901.csv", encoding="utf-8-sig")))
    tasks = {r["code"].replace("US.", ""): r for r in rows}
    print("symbols:", len(tasks), flush=True)
    results, failed = {}, []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(fetch, t): t for t in tasks}
        for fu in as_completed(futs):
            t = futs[fu]
            pairs = fu.result()
            if pairs is None:
                failed.append(t)
            else:
                results[t] = pairs
    # retry failures once, serial
    still = []
    for t in list(failed):
        pairs = fetch(t)
        if pairs is None: still.append(t)
        else: results[t] = pairs
    print(f"fetched {len(results)}, failed {len(still)} in {time.time()-t0:.0f}s", flush=True)
    if still: print("STILL_FAILED:", ",".join(still), flush=True)

    out = []
    raw = {}
    for t, pairs in results.items():
        closes = [c for _, c in pairs]
        rsi = wilder_rsi(closes)
        i = len(closes) - 1
        r_now = rsi[i]; r_5 = rsi[i - 5] if i >= 5 else None; r_20 = rsi[i - 20] if i >= 20 else None
        r60 = [x for x in rsi[-60:] if x is not None]
        raw[t] = {"dates": [dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d") for ts, _ in pairs],
                  "closes": closes, "rsi": rsi}
        r = tasks[t]
        out.append({
            "rank": int(r["rank"]), "code": t, "name": r["name"],
            "heat": float(r["heat"]), "cap": float(r["mktcap_billion_usd"]),
            "price": closes[-1], "chg": float(r["chg_pct"]),
            "rsi14": None if r_now is None else round(r_now, 1),
            "rsi5d_ago": None if r_5 is None else round(r_5, 1),
            "rsi20d_ago": None if r_20 is None else round(r_20, 1),
            "rsi60_min": None if not r60 else round(min(r60), 1),
            "rsi60_max": None if not r60 else round(max(r60), 1),
            "hi52": round(max(closes[-252:] if len(closes) >= 252 else closes), 2),
            "ret20": round((closes[-1] / closes[-21] - 1) * 100, 1) if len(closes) > 21 else None,
            "bars": len(closes), "last_date": dt.datetime.utcfromtimestamp(pairs[-1][0]).strftime("%Y-%m-%d"),
        })
    out.sort(key=lambda x: x["rank"])
    json.dump(out, open(r"C:/Users/Administrator/Desktop/stock/results/rsi14_hot354_20260901.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(r"C:/Users/Administrator/Desktop/stock/data/rsi14_hot354_20260901.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    json.dump(raw, open(r"C:/Users/Administrator/Desktop/stock/Temp/rsi_series_354.json", "w", encoding="utf-8"))

    have = [o for o in out if o["rsi14"] is not None]
    over30 = sum(1 for o in have if o["rsi14"] < 30)
    over70 = sum(1 for o in have if o["rsi14"] > 70)
    print(f"RSI computed: {len(have)} | <30: {over30} | >70: {over70}", flush=True)
    print("sample:", json.dumps(out[0], ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
