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

out = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"preprobe4","version":"1"}})
rpc("notifications/initialized", {}, notify=True)

BJ = timezone(timedelta(hours=8))
resp = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":"US.NVDA","ktype":1,"extended_time":2,"start":"2026-09-03","end":"2026-09-04","num":370,"autype":1}})
j = json.loads(json.loads(resp)["result"]["content"][0]["text"])
bars = j["data"]["kline_list"]
ts = [datetime.fromtimestamp(b["time_key"]/1000, BJ) for b in bars]
def seg(h1,m1,h2,m2):
    return [(t,b) for t,b in zip(ts,bars) if (t.hour,t.minute) >= (h1,m1) and (t.hour,t.minute) <= (h2,m2) and t.date() == datetime(2026,9,3).date() or True]
# 分段统计（BJ 时钟）
segs = {
 "盘前 16:00~21:29 (04:00~09:29 ET)": (16,0,21,29),
 "RTH 21:30~04:00 (09:30~16:00 ET)": (21,30,23,59),
}
segs2 = {"RTH续 00:00~04:00 (BJ次日,=16:00ET前)": (0,0,4,0), "盘后 04:00~08:00 (16:00~20:00 ET)": (4,0,8,0), "夜间 08:00~12:00 (20:00~00:00 ET)": (8,0,11,59)}
def count_in(lo,hi, day):
    return sum(1 for t in ts if t.date()==day and lo <= (t.hour*60+t.minute) <= hi)
d3 = datetime(2026,9,3).date(); d4 = datetime(2026,9,4).date()
print("总 bar 数:", len(bars))
print("09-03 盘前 16:00~21:29:", count_in(16*60, 21*60+29, d3))
print("09-03 RTH 21:30~23:59:", count_in(21*60+30, 23*60+59, d3))
print("09-04 00:00~03:59 (RTH续):", count_in(0, 3*60+59, d4))
print("09-04 04:00~07:59 (盘后):", count_in(4*60, 7*60+59, d4))
print("09-04 08:00~11:59 (夜间):", count_in(8*60, 11*60+59, d4))
# 盘前那根 bar 明细
pre = [(t,b) for t,b in zip(ts,bars) if t.date()==d3 and (t.hour,t.minute) >= (16,0) and (t.hour,t.minute) <= (21,29)]
for t,b in pre:
    print(f"盘前bar {t:%H:%M} BJ: O={b['open']} H={b['high']} L={b['low']} C={b['close']} vol={b['volume']} turnover={b['turnover']:.0f}")
# 对照 08-21 RTH 收盘（前收）
resp2 = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":"US.NVDA","ktype":6,"extended_time":0,"start":"2026-09-02","end":"2026-09-04","num":10,"autype":1}})
j2 = json.loads(json.loads(resp2)["result"]["content"][0]["text"])
print("et=0 对照（09-02~09-04 日线粒度请求）:")
for b in j2["data"]["kline_list"][-3:]:
    print(" ", b["time_key"], b["open"], b["close"])
