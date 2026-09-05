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

def parse(resp):
    s = resp.strip()
    if s.startswith("data:"): s = s[5:].strip()
    return json.loads(s)

out = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"preprobe7","version":"1"}})
rpc("notifications/initialized", {}, notify=True)

# tools/list 拿 rt_data schema
tl = parse(rpc("tools/list", {}))
if "tools" in tl:
    for t in tl["tools"]:
        if t["name"] in ("quote_rt_data","quote_rt_ticker"):
            print("==", t["name"], "schema:", json.dumps(t.get("inputSchema",{}).get("properties",{}), ensure_ascii=False)[:500])
else:
    print("tools/list keys:", list(tl.keys()))

# rt_data 尝试多种参数名
for args in [
    {"symbol":"US.NVDA","ktype":1,"num":60},
    {"code":"US.NVDA","ktype":1,"count":60},
    {"security_code":"US.NVDA","ktype":1,"num":60},
]:
    resp = rpc("tools/call", {"name":"quote_rt_data","arguments":args})
    try:
        j = parse(parse(resp)["result"]["content"][0]["text"])
        print(f"rt_data {list(args.keys())}: ret={j.get('ret_code')} msg={j.get('ret_msg','')[:60]}")
        if j.get("ret_code") == 0 and isinstance(j.get("data"), dict):
            print("  data keys:", list(j["data"].keys()))
            print("  sample:", json.dumps(j["data"])[:400])
            break
    except Exception as e:
        print(f"rt_data {args}: parse err {str(resp)[:150]}")
