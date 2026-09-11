# -*- coding: utf-8 -*-
"""试拉 HO 各月合约日线（富途 history_kline），并列出 HO 相关合约列表"""
import json, os, subprocess, time

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}
OUT = os.path.dirname(os.path.abspath(__file__))


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", os.path.join(OUT, "_hdr2.txt"), "--max-time", "60", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            with open(os.path.join(OUT, "_hdr2.txt"), encoding="utf-8", errors="replace") as f:
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
                if "error" in d and attempt == 2:
                    return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.0 * (attempt + 1))
    return {"_err": "exhausted"}


def init():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "probe2", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)


init()
print("=== tools/list (只看名字) ===")
tl = rpc("tools/list")
if isinstance(tl, dict) and "tools" in tl:
    print([t["name"] for t in tl["tools"]])
else:
    print(str(tl)[:300])

for code in ["US.HO2611", "US.HOmain", "US.HOcurrent", "US.HO2610", "US.HO2612"]:
    r = rpc("tools/call", {"name": "quote_history_kline",
                           "arguments": {"symbol": code, "ktype": "2", "num": "6"}})
    if isinstance(r, dict) and "data" in r:
        kl = (r["data"] or {}).get("kline_list") or []
        print(f"\n{code}: n={len(kl)}")
        for k in kl[-4:]:
            print("   ", k)
    else:
        print(f"\n{code}: {str(r)[:200]}")
    time.sleep(0.6)
