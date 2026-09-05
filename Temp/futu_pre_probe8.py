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
    for line in open("hf_pre.txt", encoding="utf-8", errors="decode_errors" if False else "replace"):
        if line.lower().startswith("mcp-session-id"): _state["sid"] = line.split(":",1)[1].strip()
    return r.stdout.strip()

def parse(resp):
    s = resp.strip()
    if s.startswith("data:"): s = s[5:].strip()
    return json.loads(s)

out = rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"preprobe8","version":"1"}})
rpc("notifications/initialized", {}, notify=True)
BJ = timezone(timedelta(hours=8))

# 1) 今日实时盘前分钟线：时间范围 + 涵盖时段
resp = rpc("tools/call", {"name":"quote_rt_data","arguments":{"symbol":"US.NVDA","ktype":1,"num":60}})
j = parse(parse(resp)["result"]["content"][0]["text"])
sec = j["data"]["section_list"][0]
pts = sec["point_list"]
t0 = datetime.fromtimestamp(pts[0]["time"]/1000, BJ)
t1 = datetime.fromtimestamp(pts[-1]["time"]/1000, BJ)
print(f"rt_data 1min num=60: {len(pts)} 点, 范围 {t0:%m-%d %H:%M} ~ {t1:%m-%d %H:%M} BJ")
print(f"  当前价 {sec.get('cur_price', pts[-1]['cur_price'])}, last_close={sec['last_close']}")
# 分段
from collections import Counter
cnt = Counter()
for p in pts:
    t = datetime.fromtimestamp(p["time"]/1000, BJ)
    if t.date() == t1.date():
        cnt[f"{t.hour//2*2:02d}h"] += 1
print("  时段分布(BJ):", dict(cnt))

# 2) rt_ticker 实时逐笔
resp = rpc("tools/call", {"name":"quote_rt_ticker","arguments":{"symbol":"US.NVDA","num":20}})
j2 = parse(parse(resp)["result"]["content"][0]["text"])
if j2.get("ret_code") == 0 and j2.get("data"):
    d2 = j2["data"]
    print("rt_ticker data keys:", list(d2.keys()) if isinstance(d2,dict) else type(d2).__name__)
    print("  sample:", json.dumps(d2)[:350])
