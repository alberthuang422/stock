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

out = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"preprobe10","version":"1"}})
rpc("notifications/initialized", {}, notify=True)
BJ = timezone(timedelta(hours=8))
print(f"本机当前时间: {datetime.now(BJ):%Y-%m-%d %H:%M:%S} BJ")

resp = rpc("tools/call", {"name":"quote_market_snapshot","arguments":{"code_list":["US.NVDA"]}})
sj = parse(parse(resp)["result"]["content"][0]["text"])
snap_d = sj["data"]
print("snapshot data type:", type(snap_d).__name__, "| keys:" , list(snap_d.keys()) if isinstance(snap_d, dict) else "")
if isinstance(snap_d, dict):
    lst = next((v for v in snap_d.values() if isinstance(v, list)), None)
else:
    lst = snap_d
if lst:
    snap = lst[0]
    for k in ["market_state","update_time","cur_price","last_close","after_price","after_change_rate","after_volume","after_high","after_low","overnight_price","pre_price","pre_volume"]:
        if k in snap: print(f"  {k}: {snap[k]}")

resp = rpc("tools/call", {"name":"quote_rt_data","arguments":{"symbol":"US.NVDA","ktype":1,"num":60}})
j = parse(parse(resp)["result"]["content"][0]["text"])
pts = j["data"]["section_list"][0]["point_list"]
print(f"rt_data: {len(pts)} 点")
days = {}
for p in pts:
    t = datetime.fromtimestamp(p["time"]/1000, BJ)
    days.setdefault(t.date(), []).append(t)
for d, ts in sorted(days.items()):
    print(f"  {d}: {len(ts)} 点  {ts[0]:%H:%M}~{ts[-1]:%H:%M} BJ")
print("  前3点:", [(datetime.fromtimestamp(p['time']/1000,BJ).strftime('%H:%M'), p['cur_price'], p['volume']) for p in pts[:3]])
print("  后3点:", [(datetime.fromtimestamp(p['time']/1000,BJ).strftime('%H:%M'), p['cur_price'], p['volume']) for p in pts[-3:]])
