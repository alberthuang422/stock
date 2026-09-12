# -*- coding: utf-8 -*-
"""探针：quote_modify_user_security schema + HO/CL 合约列表 + 价差代码探测"""
import json, subprocess, time, os, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\Administrator\Desktop\stock"
CRED = r"C:\Users\Administrator\.workbuddy\connectors\2e7b65ad-3a22-424a-a190-5066a615e2dc\.credentials.v3.json"
TOKEN_URL = "https://mcp.futunn.com/mcp"

def get_token():
    cred = json.load(open(CRED, encoding="utf-8"))
    key = "futu-mcp|e818c1846070ff2a"
    oa = cred["mcpOAuth"][key]
    now_ms = int(time.time() * 1000)
    exp = oa.get("expiresAt") or 0
    left = (exp - now_ms) if exp > 1000000000000 else (exp - time.time()) * 1000
    if left > 5 * 60 * 1000:
        return oa["accessToken"]
    refresh = oa.get("refreshToken")
    ci = (cred.get("mcpClientInfo", {}).get(key) or {})
    client_id = ci.get("client_id") or oa.get("client_id")
    body = {"grant_type": "refresh_token", "refresh_token": refresh}
    if client_id:
        body["client_id"] = client_id
    r = subprocess.run(["curl", "-s", "-m", "30", "-X", "POST",
                        "https://webapi.futunn.com/oauth2/token",
                        "-H", "Content-Type: application/json", "-d", json.dumps(body)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    j = json.loads(r.stdout or "{}")
    oa["accessToken"] = j["access_token"]
    if j.get("refresh_token"):
        oa["refreshToken"] = j["refresh_token"]
    oa["expiresAt"] = int(time.time() * 1000) + int(j.get("expires_in", 7200)) * 1000
    json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return j["access_token"]

TOK = get_token()
_state = {"sid": None, "mid": 0}
HF = os.path.join(BASE, "Temp", "_probe_hf.txt")

def rpc(method, params=None, notify=False, tries=3):
    cmd = ["curl", "-s", "-D", HF, "--max-time", "70", "-X", "POST", TOKEN_URL,
           "-H", "Content-Type: application/json",
           "-H", "Accept: application/json, text/event-stream",
           "-H", "Authorization: Bearer " + TOK]
    if _state["sid"]:
        cmd += ["-H", "Mcp-Session-Id: " + _state["sid"]]
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    else:
        _state["mid"] += 1
        body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body, ensure_ascii=False)]
    for _ in range(tries):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            for line in open(HF, encoding="utf-8", errors="replace"):
                if line.lower().startswith("mcp-session-id"):
                    _state["sid"] = line.split(":", 1)[1].strip()
        except Exception:
            pass
        out = r.stdout.strip()
        if out:
            last = out.splitlines()[-1]
            try:
                d = json.loads(last[5:] if last.startswith("data:") else last)
                if "result" in d:
                    c = d["result"].get("content")
                    if c:
                        try:
                            return json.loads(c[0]["text"])
                        except Exception:
                            return c[0]["text"]
                    return d["result"]
                if "error" in d:
                    return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.2)
    return {"_err": "exhausted"}

def tool(name, args):
    return rpc("tools/call", {"name": name, "arguments": args})

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "probe", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)

print("=== quote_modify_user_security schema ===")
r = rpc("tools/list", {})
tools = (r.get("result") or {}).get("tools") or []
for t in tools:
    if t["name"] == "quote_modify_user_security":
        print(json.dumps(t.get("inputSchema"), ensure_ascii=False))
        print("description:", t.get("description", "")[:500])

print("\n=== HO reference future list ===")
r = tool("quote_referencefuture_list", {"symbol": "US.HOmain"})
refs = ((r.get("data") or {}).get("reference_list")) or []
print(json.dumps([x.get("code") for x in refs], ensure_ascii=False))

print("\n=== CL reference future list ===")
r = tool("quote_referencefuture_list", {"symbol": "US.CLmain"})
refs2 = ((r.get("data") or {}).get("reference_list")) or []
print(json.dumps([x.get("code") for x in refs2], ensure_ascii=False))