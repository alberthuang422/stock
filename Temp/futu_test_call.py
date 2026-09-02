# -*- coding: utf-8 -*-
import json, subprocess
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H","Content-Type: application/json","-H","Accept: application/json, text/event-stream","-H","Authorization: Bearer "+tok]
_state = {"sid": None, "mid": 0}
def rpc(method, params=None, notify=False, session=None):
    _state["mid"] += 1
    cmd = ["curl","-s","-D","hf2.txt","--max-time","45","-X","POST","https://mcp.futunn.com/mcp"] + HDRS
    sid = session if session else _state["sid"]
    if sid: cmd += ["-H", "Mcp-Session-Id: "+sid]
    body = {"jsonrpc":"2.0","method":method,"params":params or {}}
    if not notify: body["id"] = _state["mid"]
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sid2 = None
    for line in open("hf2.txt", encoding="utf-8", errors="replace"):
        if line.lower().startswith("mcp-session-id"): sid2 = line.split(":",1)[1].strip()
    return r.stdout.strip(), sid2

# init
out, sid = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"t","version":"1"}})
_state["sid"] = sid if sid else _state["sid"]
print("INIT sid:", _state["sid"])
rpc("notifications/initialized", {}, notify=True)

# 测试1: num 字符串 800, 只带 symbol/end/num
out1, _ = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":"US.BX","end":"2026-09-01","num":"260"}})
print("T1 num=str260:", out1[:400])

# 测试2: num 字符串 800
out2, _ = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":"US.BX","end":"2026-09-01","num":"800"}})
print("T2 num=str800:", out2[:400])

# 测试3: num 整数
out3, _ = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":"US.BX","end":"2026-09-01","num":260}})
print("T3 num=int260:", out3[:400])

# 测试4: ktype 显式
out4, _ = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":"US.BX","ktype":"2","end":"2026-09-01","num":"260"}})
print("T4 ktype:", out4[:400])
