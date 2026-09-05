# -*- coding: utf-8 -*-
import json, subprocess, time, sys, datetime as dt

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}
HDRF = "/tmp/hf_wz.txt"

def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", HDRF, "--max-time", "45", "-X", "POST", "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]: cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify: body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
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
    return {"_err": "noresp"}

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "wz-probe", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)
time.sleep(0.3)

cands = ["US.ZWmain", "US.ZWH26", "FUT.ZWmain", "US.ZW", "ZWmain"]
for s in cands:
    r = rpc("tools/call", {"name": "quote_history_kline", "arguments": {"symbol": s, "ktype": "2", "end": "2026-09-01", "num": "20"}})
    rc = r.get("ret_code") if isinstance(r, dict) else None
    kl = ((r.get("data") or {}).get("kline_list")) if isinstance(r, dict) else None
    if rc == 0 and kl:
        print(f"{s}: OK n={len(kl)} 首条 {kl[0].get('time_key')} {kl[0].get('close')} 末条 {kl[-1].get('time_key')} {kl[-1].get('close')}")
    else:
        print(f"{s}: rc={rc} msg={(r.get('ret_msg') if isinstance(r,dict) else '')[:90]}")
    time.sleep(0.4)
