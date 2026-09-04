# -*- coding: utf-8 -*-
"""财报日历抓取：富途 over-HTTP（quote_financials_earnings_price_history），73 只蓝筹全历史财报披露日。
输出 results/70_v2/earnings_all.csv（ticker,date）。0.4s pacing + 退避。"""
import json, subprocess, time, os, sys

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
OUT = r"C:\Users\Administrator\Desktop\stock\results\70_v2\earnings_all.csv"
BC = r"C:\Users\Administrator\Desktop\stock\data\blue_chips.csv"

tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H","Content-Type: application/json","-H","Accept: application/json, text/event-stream","-H","Authorization: Bearer "+tok]
_state = {"sid": None, "mid": 0}

def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl","-s","-D","hf3.txt","--max-time","45","-X","POST","https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]: cmd += ["-H","Mcp-Session-Id: "+_state["sid"]]
    body = {"jsonrpc":"2.0","method":method,"params":params or {}}
    if not notify: body["id"] = _state["mid"]
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        for line in open("hf3.txt", encoding="utf-8", errors="replace"):
            if line.lower().startswith("mcp-session-id"): _state["sid"] = line.split(":",1)[1].strip()
    except FileNotFoundError: pass
    return r.stdout.strip()

rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"earnfetch","version":"1"}})
rpc("notifications/initialized", {}, notify=True)

import pandas as pd
bc = pd.read_csv(BC, encoding="utf-8-sig")
tickers = bc["ticker"].str.strip().str.lower().tolist()
tickers = [t for t in tickers if t != "mmc"]  # 本地无数据

rows, fails = [], []
for i, t in enumerate(tickers):
    ok = False
    for attempt in range(4):
        out = rpc("tools/call", {"name":"quote_financials_earnings_price_history","arguments":{"symbol":"US."+t.upper()}})
        try:
            j = json.loads(out)
            txt = j["result"]["content"][0]["text"]
            d = json.loads(txt)
            if d.get("ret_code") == 0:
                for rec in d["data"]["records"]:
                    s = rec.get("pub_trading_day_str") or (rec.get("pub_time_str","")[:10])
                    if s and len(s)==10:
                        rows.append({"ticker": t, "date": s})
                ok = True
                break
        except Exception:
            pass
        time.sleep(1.5 * (attempt+1))
    if not ok:
        fails.append(t)
        print("FAIL", t, out[:120])
    time.sleep(0.4)
    if (i+1) % 10 == 0: print(f"{i+1}/{len(tickers)} done, rows={len(rows)}", flush=True)

df = pd.DataFrame(rows).drop_duplicates()
df.to_csv(OUT, index=False)
print("SAVED", OUT, len(df), "rows; fails:", fails)
