# -*- coding: utf-8 -*-
"""富途 MCP 自选分组管理：查看/新增/删除分组成分。

端点：https://mcp.futunn.com/mcp（refresh_token 公共客户端）
核心工具：
  quote_user_security_group(group_type)  -> 分组列表
  quote_user_security(group_name)        -> 分组成分
  quote_modify_user_security(...)        -> 增删成分

用法：
  python scripts/futu_watch_manage.py list                      # 列出所有分组
  python scripts/futu_watch_manage.py members 月差               # 列出分组成分
  python scripts/futu_watch_manage.py add 月差 US.CL2610/CL2611 ...   # 加成分
  python scripts/futu_watch_manage.py del 月差 US.CL2610/CL2611 ...   # 删成分
"""
import json
import subprocess
import time
import os
import sys

BASE = r"C:\Users\Administrator\Desktop\stock"
CRED = r"C:\Users\Administrator\.workbuddy\connectors\2e7b65ad-3a22-424a-a190-5066a615e2dc\.credentials.v3.json"
TOKEN_URL = "https://mcp.futunn.com/mcp"
AUTH_WELLKNOWN = "https://mcp.futunn.com/.well-known/oauth-authorization-server"

sys.stdout.reconfigure(encoding="utf-8")


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
    if not refresh:
        raise RuntimeError("无 refreshToken")
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
    if not j.get("access_token"):
        raise RuntimeError("refresh 失败: " + r.stdout[:300])
    oa["accessToken"] = j["access_token"]
    if j.get("refresh_token"):
        oa["refreshToken"] = j["refresh_token"]
    oa["expiresAt"] = int(time.time() * 1000) + int(j.get("expires_in", 7200)) * 1000
    json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return j["access_token"]


TOK = get_token()
_state = {"sid": None, "mid": 0}
HF = os.path.join(BASE, "Temp", "_watch_mgr_hf.txt")


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
            except Exception as e:
                last_err = repr(e)
        time.sleep(1.2)
    return {"_err": "exhausted"}


def tool(name, args):
    return rpc("tools/call", {"name": name, "arguments": args})


def groups():
    g = tool("quote_user_security_group", {"group_type": "ALL"})
    if isinstance(g, dict):
        return g.get("data", {}).get("group_list", []) or g.get("group_list", [])
    return []


def members(group_name):
    m = tool("quote_user_security", {"group_name": group_name})
    return m


def main():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "watch_mgr", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)

    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "list":
        for g in groups():
            print(f"{g.get('group_name')}  [{g.get('group_type')}]")
    elif cmd == "members":
        gn = sys.argv[2] if len(sys.argv) > 2 else "月差"
        m = members(gn)
        print(json.dumps(m, ensure_ascii=False, indent=1))
    elif cmd in ("add", "del"):
        gn = sys.argv[2]
        codes = sys.argv[3:]
        print(f"{cmd} 分组[{gn}] codes={len(codes)} 个")
        r = tool("quote_modify_user_security",
                 {"group_name": gn, "op": "ADD" if cmd == "add" else "DEL",
                  "code_list": codes})
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("未知命令:", cmd)


if __name__ == "__main__":
    main()