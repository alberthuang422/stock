# -*- coding: utf-8 -*-
"""dump tools/list 完整结果，提取 quote_modify_user_security schema"""
import json, subprocess, time, os, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\Administrator\Desktop\stock"
CRED = r"C:\Users\Administrator\.workbuddy\connectors\2e7b65ad-3a22-424a-a190-5066a615e2dc\.credentials.v3.json"
TOKEN_URL = "https://mcp.futunn.com/mcp"

def get_token():
    cred = json.load(open(CRED, encoding="utf-8"))
    key = "futu-mcp|e818c1846070ff2a"
    oa = cred["mcpOAuth"][key]
    if (oa.get("expiresAt") or 0) > int(time.time() * 1000) + 5 * 60 * 1000:
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
    json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return j["access_token"]

TOK = get_token()
_state = {"sid": None, "mid": 0}
HF = os.path.join(BASE, "Temp", "_tls.txt")

def rpc(method, params=None, notify=False):
    cmd = ["curl", "-s", "-D", HF, "--max-time", "90", "-X", "POST", TOKEN_URL,
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
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        for line in open(HF, encoding="utf-8", errors="replace"):
            if line.lower().startswith("mcp-session-id"):
                _state["sid"] = line.split(":", 1)[1].strip()
    except Exception:
        pass
    return r.stdout.strip()

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "dump", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)
time.sleep(0.3)
out = rpc("tools/list", {})
# 保存原始
open(os.path.join(BASE, "Temp", "tools_list_raw.txt"), "w", encoding="utf-8").write(out)
lines = [l for l in out.splitlines() if l.strip()]
last = lines[-1]
d = json.loads(last[5:] if last.startswith("data:") else last)
tools = (d.get("result") or {}).get("tools") or []
for t in tools:
    if t["name"] == "quote_modify_user_security":
        print(json.dumps(t, ensure_ascii=False, indent=1))