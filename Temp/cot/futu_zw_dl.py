# -*- coding: utf-8 -*-
import json, subprocess, time, sys, datetime as dt

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}
HDRF = "/tmp/hf_zw.txt"

def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", HDRF, "--max-time", "50", "-X", "POST", "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]: cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify: body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    for attempt in range(4):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            for line in open(HDRF, encoding="utf-8", errors="replace"):
                if line.lower().startswith("mcp-session-id"):
                    _state["sid"] = line.split(":", 1)[1].strip()
        except FileNotFoundError: pass
        out = r.stdout.strip()
        if out:
            last = out.splitlines()[-1]
            try:
                d = json.loads(last[5:] if last.startswith("data:") else last)
                if "result" in d:
                    c = d["result"].get("content")
                    return json.loads(c[0]["text"]) if c else d["result"]
                if "error" in d: return {"_err": d["error"]}
            except Exception: pass
        time.sleep(1.0 * (attempt + 1) + 0.5)
    return {"_err": "exhausted"}

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "zw-dl", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)
time.sleep(0.4)

def page(end):
    r = rpc("tools/call", {"name": "quote_history_kline",
                           "arguments": {"symbol": "US.ZWmain", "ktype": "2", "end": end, "num": "370"}})
    kl = ((r.get("data") or {}).get("kline_list")) if isinstance(r, dict) else None
    return kl or []

out = []
end = dt.date(2026, 9, 5).strftime("%Y-%m-%d")
pages = 0
while True:
    kl = page(end)
    if not kl:
        print("EMPTY at end=", end); break
    out += kl
    pages += 1
    d0 = min(k["time_key"] for k in kl)
    t0 = dt.datetime.fromtimestamp(d0 / 1000)
    print(f"page {pages}: {len(kl)} rows  {t0:%Y-%m-%d} -> {end}  total {len(out)}", flush=True)
    if len(kl) < 370 or t0.year <= 1994:
        break
    end = (t0.date() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    time.sleep(0.4)

rows = sorted(out, key=lambda k: k["time_key"])
# 去重
seen = set(); uni = []
for k in rows:
    if k["time_key"] in seen: continue
    seen.add(k["time_key"]); uni.append(k)
print(f"total unique {len(uni)}  range {dt.datetime.fromtimestamp(uni[0]['time_key']/1000):%Y-%m-%d} -> {dt.datetime.fromtimestamp(uni[-1]['time_key']/1000):%Y-%m-%d}")
json.dump(uni, open("zw_main_hist.json", "w"))
print("keys:", list(uni[0].keys()))
