# -*- coding: utf-8 -*-
"""Retry the failed tickers with pacing, merge into results."""
import sys, json, time, csv
sys.path.insert(0, r"C:/Users/Administrator/Desktop/stock/Temp")
import rsi_futu_354 as R

def calc_rows(code, closes, dates, rank, name):
    rsi = R.wilder_rsi(closes)
    i = len(closes)-1
    r_now=rsi[i]; r5=rsi[i-5] if i>=5 else None; r20=rsi[i-20] if i>=20 else None
    win60=[x for x in rsi[-60:] if x is not None]
    last52=closes[-252:] if len(closes)>=252 else closes
    hi=max(last52); lo=min(last52)
    return {"rank":rank,"code":code,"name":name,"last_date":dates[-1],
        "price":round(closes[-1],2),
        "rsi14":round(r_now,1) if r_now is not None else None,
        "rsi14_5d":round(r5,1) if r5 is not None else None,
        "rsi14_20d":round(r20,1) if r20 is not None else None,
        "rsi60_min":round(min(win60),1) if win60 else None,
        "rsi60_max":round(max(win60),1) if win60 else None,
        "hi52":round(hi,2),"lo52":round(lo,2),
        "off_hi52":round((closes[-1]/hi-1)*100,1),
        "ret20":round((closes[-1]/closes[-21]-1)*100,1) if len(closes)>21 else None,
        "ret60":round((closes[-1]/closes[-61]-1)*100,1) if len(closes)>61 else None,
        "bars":len(closes)}

R.init()
meta = {r[2]: (r[0], r[3]) for r in json.load(open(r"C:/Users/Administrator/Desktop/stock/Temp/hot_filtered.json", encoding="utf-8"))}  # code->(rank,name)
existing = {r["code"]: r for r in json.load(open(r"C:/Users/Administrator/Desktop/stock/results/rsi14_hot354_20260901.json", encoding="utf-8"))}
fails = [c for c in meta if c not in existing]
print("to retry:", len(fails), flush=True)

def fetch_retry(sym, tries=4):
    for a in range(tries):
        r = R.rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":sym,"ktype":"2","end":"2026-09-01","num":"260"}})
        if "_err" not in r:
            kl = (r.get("data") or {}).get("kline_list") or []
            if kl:
                closes=[k["close"] for k in kl if k.get("close") is not None]
                dates=[str(k["date"]) for k in kl if k.get("close") is not None]
                if len(closes)>=20: return closes, dates
        time.sleep(1.2*(a+1))
    return None

ok, still = 0, []
t0=time.time()
for idx, code in enumerate(fails):
    sym = "US."+code
    got = fetch_retry(sym)
    if got:
        rank, name = meta[code]
        existing[code] = calc_rows(code, got[0], got[1], rank, name)
        ok+=1
    else:
        still.append(code)
    if (idx+1)%20==0:
        print(f"  {idx+1}/{len(fails)} ok={ok} fail={len(still)} | {time.time()-t0:.0f}s", flush=True)
    time.sleep(0.25)

print(f"RETRY DONE recovered={ok} still_fail={len(still)} in {time.time()-t0:.0f}s", flush=True)
if still: print("STILL:", ",".join(still), flush=True)

merged = sorted(existing.values(), key=lambda x: x["rank"])
json.dump(merged, open(r"C:/Users/Administrator/Desktop/stock/results/rsi14_hot354_20260901.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
with open(r"C:/Users/Administrator/Desktop/stock/data/rsi14_hot354_20260901.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f, fieldnames=list(merged[0].keys())); w.writeheader(); w.writerows(merged)
have=[r for r in merged if r["rsi14"] is not None]
print(f"TOTAL {len(merged)} rows, RSI present {len(have)}", flush=True)
print(f"RSI<30:{sum(1 for r in have if r['rsi14']<30)} | 30-50:{sum(1 for r in have if 30<=r['rsi14']<50)} | 50-70:{sum(1 for r in have if 50<=r['rsi14']<70)} | >=70:{sum(1 for r in have if r['rsi14']>=70)}", flush=True)
