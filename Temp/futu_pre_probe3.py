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

out = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"preprobe3","version":"1"}})
rpc("notifications/initialized", {}, notify=True)

BJ = timezone(timedelta(hours=8))
def get_bars(params):
    resp = rpc("tools/call", {"name":"quote_history_kline","arguments":params})
    j = json.loads(json.loads(resp)["result"]["content"][0]["text"])
    if "data" not in j: return None, j.get("retMsg","?")
    return j["data"].get("kline_list", []), None

def probe(label, params, D=None):
    bars, err = get_bars(params)
    if bars is None: print(f"== {label}: ERR {err}"); return
    ts = [datetime.fromtimestamp(b["time_key"]/1000, BJ) for b in bars]
    n = len(bars)
    print(f"== {label}: {n} bars  [{ts[0]:%m-%d %H:%M} ~ {ts[-1]:%m-%d %H:%M} BJ]" if n else f"== {label}: 0 bars")
    if D and n:
        lo = D.replace(hour=16,minute=0); hi = D.replace(hour=21,minute=31)
        inw = [(t,b) for t,b in zip(ts,bars) if lo <= t <= hi]
        if inw:
            print(f"   盘前窗口 {len(inw)} bars  {inw[0][0]:%H:%M}~{inw[-1][0]:%H:%M}  开={inw[0][1]['open']} 收={inw[-1][1]['close']} 高={max(b['high'] for _,b in inw)} 低={min(b['low'] for _,b in inw)}")
        else:
            print("   盘前窗口: 0 bars")

# D=09-03
D = datetime(2026,9,3, tzinfo=BJ)
probe("1min et=2 09-03", {"symbol":"US.NVDA","ktype":1,"extended_time":2,"start":"2026-09-03","end":"2026-09-04","num":370,"autype":1}, D)
probe("5min et=2 09-03", {"symbol":"US.NVDA","ktype":6,"extended_time":2,"start":"2026-09-03","end":"2026-09-04","num":370,"autype":1}, D)
# 更旧 08-24
D8 = datetime(2026,8,24, tzinfo=BJ)
probe("5min et=2 08-24", {"symbol":"US.NVDA","ktype":6,"extended_time":2,"start":"2026-08-24","end":"2026-08-25","num":370,"autype":1}, D8)
probe("1min et=2 08-24", {"symbol":"US.NVDA","ktype":1,"extended_time":2,"start":"2026-08-24","end":"2026-08-25","num":370,"autype":1}, D8)
# 一个月前 08-04
D84 = datetime(2026,8,4, tzinfo=BJ)
probe("5min et=2 08-04", {"symbol":"US.NVDA","ktype":6,"extended_time":2,"start":"2026-08-04","end":"2026-08-05","num":370,"autype":1}, D84)
# num 上限测试：不传 num 或 num=1000
probe("1min et=2 09-03 num=1000", {"symbol":"US.NVDA","ktype":1,"extended_time":2,"start":"2026-09-03","end":"2026-09-04","num":1000,"autype":1}, D)
