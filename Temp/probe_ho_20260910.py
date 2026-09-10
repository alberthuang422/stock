# -*- coding: utf-8 -*-
"""探测富途期货主连符号：取暖油/柴油 HO、豆油 ZL、汽油 RB、原油 CL"""
import json, subprocess, time

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
c = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]
print("expiresAt:", c.get("expiresAt"), "now_ms:", int(time.time() * 1000))
tok = c["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/hf_probe.txt", "--max-time", "45", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        with open("/tmp/hf_probe.txt", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.lower().startswith("mcp-session-id"):
                    _state["sid"] = line.split(":", 1)[1].strip()
    except FileNotFoundError:
        pass
    out = r.stdout.strip()
    if out:
        last = out.splitlines()[-1]
        try:
            d = json.loads(last[5:] if last.startswith("data:") else last)
            return d
        except Exception:
            return {"_raw": out[:300]}
    return {"_empty": True}


rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "probe", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)
time.sleep(0.3)

for sym in ["US.HOmain", "US.ULSDmain", "US.ZLmain", "US.RBmain", "US.CLmain",
            "US.ZCmain", "US.ZWmain", "US.ZSmain"]:
    r = rpc("tools/call", {"name": "quote_history_kline",
                           "arguments": {"symbol": sym, "ktype": "2",
                                         "end": "2026-09-09", "num": "2"}})
    if "result" in r:
        try:
            data = json.loads(r["result"]["content"][0]["text"])
            kl = (data.get("data") or {}).get("kline_list") or []
            print(f"{sym}: OK kl={len(kl)} last={kl[-1] if kl else None}")
        except Exception as e:
            print(f"{sym}: parse-fail {r['result']}")
    else:
        print(f"{sym}: ERR {str(r)[:200]}")
    time.sleep(0.35)
