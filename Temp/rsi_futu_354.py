# -*- coding: utf-8 -*-
"""Pull 260 daily bars per ticker from Futu MCP (HTTP direct), compute Wilder RSI14 + context. Serial, ~6 min."""
import json, subprocess, sys, time
import datetime as dt

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H","Content-Type: application/json","-H","Accept: application/json, text/event-stream","-H",f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}

def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl","-s","-D","/tmp/hf.txt","--max-time","45","-X","POST","https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]: cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc":"2.0","method":method,"params":params or {}} if notify else {"jsonrpc":"2.0","id":_state["mid"],"method":method,"params":params or {}}
    cmd += ["-d", json.dumps(body)]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        for line in open("/tmp/hf.txt", encoding="utf-8", errors="replace"):
            if line.lower().startswith("mcp-session-id"): _state["sid"] = line.split(":",1)[1].strip()
        out = r.stdout.strip()
        if out:
            last = out.splitlines()[-1]
            try:
                d = json.loads(last[5:] if last.startswith("data:") else last)
                if "result" in d:
                    if notify: return {}
                    c = d["result"].get("content")
                    if c: return json.loads(c[0]["text"])
                    return d["result"]
                if "error" in d and attempt == 2: return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.5*(attempt+1))
    return {"_err":"exhausted"}

def init():
    rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"r","version":"1"}})
    rpc("notifications/initialized", {}, notify=True)

def wilder_rsi(closes, n=14):
    out=[None]*len(closes)
    if len(closes)<=n: return out
    g=sum(max(closes[i]-closes[i-1],0) for i in range(1,n+1))
    l=sum(max(closes[i-1]-closes[i],0) for i in range(1,n+1))
    ag,al=g/n,l/n
    def calc(ag,al):
        if ag==0 and al==0: return 50.0
        if al==0: return 100.0
        if ag==0: return 0.0
        return 100-100/(1+ag/al)
    out[n]=calc(ag,al)
    for i in range(n+1,len(closes)):
        ch=closes[i]-closes[i-1]
        ag=(ag*(n-1)+max(ch,0))/n; al=(al*(n-1)+max(-ch,0))/n
        out[i]=calc(ag,al)
    return out

def fetch(symbol):
    end = dt.date(2026,9,1).strftime("%Y-%m-%d")
    r = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":symbol,"ktype":"2","end":end,"num":"260"}})
    if "_err" in r: return None
    kl = (r.get("data") or {}).get("kline_list") or []
    closes=[k["close"] for k in kl if k.get("close") is not None]
    dates=[str(k["date"]) for k in kl if k.get("close") is not None]
    return closes, dates if closes else None

def main():
    init()
    rows = json.load(open(r"C:/Users/Administrator/Desktop/stock/Temp/hot_filtered.json", encoding="utf-8"))
    tasks = [(r[0], r[2], r[3], "US."+r[2]) for r in rows]  # rank, code, name, symbol
    print("symbols:", len(tasks), flush=True)
    results, fails = [], []
    t0=time.time()
    for idx,(rank,code,name,sym) in enumerate(tasks):
        got = fetch(sym)
        if not got or len(got[0]) < 20:
            got = fetch(sym)  # one retry
        if not got or len(got[0]) < 20:
            fails.append(code); continue
        closes,dates = got
        rsi = wilder_rsi(closes)
        i=len(closes)-1
        r_now=rsi[i]; r5=rsi[i-5] if i>=5 else None; r20=rsi[i-20] if i>=20 else None
        win60=[x for x in rsi[-60:] if x is not None]
        last52=closes[-252:] if len(closes)>=252 else closes
        hi=max(last52); lo=min(last52)
        row={"rank":rank,"code":code,"name":name,"last_date":dates[-1],
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
        results.append(row)
        if (idx+1)%25==0:
            print(f"  {idx+1}/{len(tasks)} | {time.time()-t0:.0f}s | {code} RSI={row['rsi14']}", flush=True)
    print(f"DONE {len(results)} ok, {len(fails)} fail in {time.time()-t0:.0f}s", flush=True)
    if fails: print("FAILS:", ",".join(fails), flush=True)
    out=r"C:/Users/Administrator/Desktop/stock/results/rsi14_hot354_20260901.json"
    json.dump(results, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    import csv
    with open(r"C:/Users/Administrator/Desktop/stock/data/rsi14_hot354_20260901.csv","w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0].keys())); w.writeheader(); w.writerows(results)
    have=[r for r in results if r["rsi14"] is not None]
    print(f"RSI<30:{sum(1 for r in have if r['rsi14']<30)} | 30-50:{sum(1 for r in have if 30<=r['rsi14']<50)} | 50-70:{sum(1 for r in have if 50<=r['rsi14']<70)} | >70:{sum(1 for r in have if r['rsi14']>=70)}", flush=True)

if __name__=="__main__":
    main()
