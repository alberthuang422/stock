# -*- coding: utf-8 -*-
import json, subprocess
from datetime import datetime, timezone, timedelta
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H","Content-Type: application/json","-H","Accept: application/json, text/event-stream","-H","Authorization: Bearer "+tok]
_state = {"sid": None, "mid": 0}
def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl","-s","-D","hf_pre.txt","--max-time","60","-X","POST","https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]: cmd += ["-H", "Mcp-Session-Id: "+_state["sid"]]
    body = {"jsonrpc":"2.0","method":method,"params":params or {}}
    if not notify: body["id"] = _state["mid"]
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in open("hf_pre.txt", encoding="utf-8", errors="replace"):
        if line.lower().startswith("mcp-session-id"): _state["sid"] = line.split(":",1)[1].strip()
    return r.stdout.strip()

out = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"preprobe5","version":"1"}})
rpc("notifications/initialized", {}, notify=True)
BJ = timezone(timedelta(hours=8))

# 1) 盘前竞价 bar 回溯深度：5min et=2, 各历史日期
for D in ["2026-07-01","2026-05-01","2026-03-02","2026-01-05","2025-09-02","2025-03-03","2024-09-03"]:
    resp = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":"US.NVDA","ktype":6,"extended_time":2,"start":D,"end":D,"num":370,"autype":1}})
    try:
        j = json.loads(json.loads(resp)["result"]["content"][0]["text"])
        bars = j.get("data",{}).get("kline_list",[])
        pre = [b for b in bars if datetime.fromtimestamp(b["time_key"]/1000,BJ).date() == datetime.strptime(D,"%Y-%m-%d").date() and datetime.fromtimestamp(b["time_key"]/1000,BJ).hour >= 16 and datetime.fromtimestamp(b["time_key"]/1000,BJ).hour <= 21]
        tag = f"{len(pre)} 根: " + ", ".join(f"{datetime.fromtimestamp(b['time_key']/1000,BJ):%H:%M} O={b['open']}" for b in pre) if pre else "无盘前bar"
        print(f"{D}: 总{len(bars)}bar | 盘前 {tag}")
    except Exception as e:
        print(f"{D}: ERR {str(resp)[:120]}")

# 2) rt_data schema
tl = json.loads(rpc("tools/list", {}))
for t in tl["tools"]:
    if t["name"] in ("quote_rt_data","quote_rt_ticker"):
        print("==", t["name"], "params:", json.dumps(t.get("inputSchema",{}).get("properties",{}), ensure_ascii=False)[:400])
