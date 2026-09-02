# -*- coding: utf-8 -*-
import json, subprocess
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H","Content-Type: application/json","-H","Accept: application/json, text/event-stream","-H","Authorization: Bearer "+tok]
_state = {"sid": None, "mid": 0}
def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl","-s","-D","hf2.txt","--max-time","45","-X","POST","https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]: cmd += ["-H", "Mcp-Session-Id: "+_state["sid"]]
    body = {"jsonrpc":"2.0","method":method,"params":params or {}}
    if not notify: body["id"] = _state["mid"]
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in open("hf2.txt", encoding="utf-8", errors="replace"):
        if line.lower().startswith("mcp-session-id"): _state["sid"] = line.split(":",1)[1].strip()
    return r.stdout.strip()


out = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"t2","version":"1"}})
print("INIT ok")
rpc("notifications/initialized", {}, notify=True)

tests = [
    ("qhk US.BX num200", {"name":"quote_history_kline","arguments":{"symbol":"US.BX","num":"200"}}),
    ("qhk APO", {"name":"quote_history_kline","arguments":{"symbol":"APO","num":"200"}}),
    ("qhk 10503", {"name":"quote_history_kline","arguments":{"symbol":"10503","num":"200"}}),
    ("snapshot US.APO", {"name":"quote_market_snapshot","arguments":{"code_list":["US.APO"]}}),
    ("snapshot APO", {"name":"quote_market_snapshot","arguments":{"code_list":["APO"]}}),
    ("stock_quote US.APO", {"name":"quote_stock_quote","arguments":{"symbol":"US.APO","fields":["last_price","name"]}}),
    ("stock_basicinfo US.APO", {"name":"quote_stock_basicinfo","arguments":{"symbol":"US.APO"}}),
    ("trading_days", {"name":"quote_trading_days","arguments":{"market":"US","start":"2026-08-01","end":"2026-09-01"}}),
]
for label, params in tests:
    out = rpc("tools/call", params)
    print(f"== {label}:", out[:300])
