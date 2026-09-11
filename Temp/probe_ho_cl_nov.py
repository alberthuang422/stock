# -*- coding: utf-8 -*-
"""探测 HO(取暖油) 与 CL(WTI) 各月合约：代码存在性 + 最新日线快照
2026-09-11
"""
import json, os, subprocess, time, datetime as dt

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}
OUT = os.path.dirname(os.path.abspath(__file__))


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", os.path.join(OUT, "_hdr.txt"), "--max-time", "60", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    for attempt in range(4):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            with open(os.path.join(OUT, "_hdr.txt"), encoding="utf-8", errors="replace") as f:
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
                if "result" in d:
                    if notify:
                        return {}
                    c = d["result"].get("content")
                    if c:
                        return json.loads(c[0]["text"])
                    return d["result"]
                if "error" in d and attempt == 3:
                    return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.0 * (attempt + 1))
    return {"_err": "exhausted"}


def init():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "probe", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)


init()

# 1) HO 合约代码探测
HO_CAND = ["US.HO2610", "US.HO2611", "US.HO2612", "US.HO2701", "US.HO2702",
           "US.HOmain", "US.HOcurrent", "US.HOnext"]
r = rpc("tools/call", {"name": "quote_future_info", "arguments": {"code_list": HO_CAND}})
print("=== future_info HO ===")
print(json.dumps(r, ensure_ascii=False)[:1800])

# 2) 实时快照
snap = ["US.CL2610", "US.CL2611", "US.CL2612", "US.CL2701", "US.CL2702", "US.CL2703",
        "US.CLcurrent", "US.CLnext"] + HO_CAND
r2 = rpc("tools/call", {"name": "quote_stock_quote", "arguments": {"code_list": snap}})
print("\n=== snapshot ===")
print(json.dumps(r2, ensure_ascii=False)[:4000])
