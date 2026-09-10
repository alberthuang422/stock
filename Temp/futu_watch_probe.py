# -*- coding: utf-8 -*-
"""探查富途自选分组：列出分组 -> 定位「月差」-> 拉取成分"""
import json, subprocess, sys, time, os

BASE = r"C:\Users\Administrator\Desktop\stock"
CRED = r"C:\Users\Administrator\.workbuddy\connectors\2e7b65ad-3a22-424a-a190-5066a615e2dc\.credentials.v3.json"
TOKEN_URL = "https://mcp.futunn.com/mcp"
AUTH_WELLKNOWN = "https://mcp.futunn.com/.well-known/oauth-authorization-server"

def get_token():
    cred = json.load(open(CRED, encoding="utf-8"))
    key = "futu-mcp|e818c1846070ff2a"
    oa = cred["mcpOAuth"][key]
    now_ms = int(time.time() * 1000)
    exp = oa.get("expiresAt") or 0
    left_ms = (exp - now_ms) if exp > 1000000000000 else (exp - time.time()) * 1000
    print(f"[token] 剩余 {left_ms/60000:.1f} min", file=sys.stderr)
    if left_ms > 5 * 60 * 1000:
        return oa["accessToken"]
    refresh = oa.get("refreshToken")
    if not refresh:
        print("[token] 无 refreshToken", file=sys.stderr)
        return None
    ci = (cred.get("mcpClientInfo", {}).get(key) or {})
    client_id = ci.get("client_id") or oa.get("client_id")
    try:
        meta = json.loads(subprocess.run(["curl", "-s", "-m", "20", AUTH_WELLKNOWN], capture_output=True, text=True).stdout)
        tok_url = meta.get("token_endpoint") or "https://webapi.futunn.com/oauth2/token"
    except Exception:
        tok_url = "https://webapi.futunn.com/oauth2/token"
    body = {"grant_type": "refresh_token", "refresh_token": refresh}
    if client_id:
        body["client_id"] = client_id
    r = subprocess.run(["curl", "-s", "-m", "30", "-X", "POST", tok_url,
                        "-H", "Content-Type: application/json", "-d", json.dumps(body)],
                       capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
    except Exception:
        j = {}
    if j.get("access_token"):
        oa["accessToken"] = j["access_token"]
        if j.get("refresh_token"):
            oa["refreshToken"] = j["refresh_token"]
        oa["expiresAt"] = int(time.time() * 1000) + int(j.get("expires_in", 7200)) * 1000
        json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("[token] refresh OK", file=sys.stderr)
        return j["access_token"]
    print(f"[token] refresh 失败: {r.stdout[:300]}", file=sys.stderr)
    return None

TOK = get_token()
_state = {"sid": None, "mid": 0}
HF = os.path.join(BASE, "Temp", "_hf2.txt")

def rpc(method, params=None, notify=False, tries=2):
    cmd = ["curl", "-s", "-D", HF, "--max-time", "60", "-X", "POST", TOKEN_URL,
           "-H", "Content-Type: application/json",
           "-H", "Accept: application/json, text/event-stream",
           "-H", f"Authorization: Bearer {TOK}"]
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}} if notify else \
           {"jsonrpc": "2.0", "id": _state["mid"] + 1, "method": method, "params": params or {}}
    _state["mid"] += 1
    cmd += ["-d", json.dumps(body, ensure_ascii=False)]
    for attempt in range(tries):
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
                    print(f"[rpc:{method}] error={d['error']}", file=sys.stderr)
                    return {"_err": d["error"]}
            except Exception as e:
                print(f"[rpc:{method}] parse fail: {e} raw={out[:200]}", file=sys.stderr)
        time.sleep(1.2 * (attempt + 1))
    return {"_err": "exhausted"}

def call_tool(name, args):
    return rpc("tools/call", {"name": name, "arguments": args})

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "probe", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)

out = {"groups": None, "target": None, "members": None}
out["groups"] = call_tool("quote_user_security_group", {"group_type": "ALL"})
print("== GROUPS ==")
print(json.dumps(out["groups"], ensure_ascii=False, indent=1)[:4000])

# 尝试定位月差分组
names = []
g = out["groups"]
if isinstance(g, dict):
    for k in ("data", "groups", "group_list", "list"):
        if isinstance(g.get(k), list):
            names = g[k]
            break
elif isinstance(g, list):
    names = g
print("== NAME CANDIDATES ==", json.dumps(names, ensure_ascii=False)[:2000])

target = None
for item in names:
    s = json.dumps(item, ensure_ascii=False)
    if "月差" in s:
        target = item
        break
if target:
    print("== TARGET ==", json.dumps(target, ensure_ascii=False))
    gname = target.get("group_name") or target.get("name")
    out["members"] = call_tool("quote_user_security", {"group_name": gname})
    print("== MEMBERS ==")
    print(json.dumps(out["members"], ensure_ascii=False, indent=1)[:6000])
else:
    print("== 未找到含「月差」的分组 ==")

json.dump(out, open(os.path.join(BASE, "Temp", "futu_watch_probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved -> Temp/futu_watch_probe.json")
