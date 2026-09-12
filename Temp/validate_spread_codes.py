# -*- coding: utf-8 -*-
"""验证 CL/HO 的 +1 相邻月差代码在富途是否有效（quote_market_snapshot）"""
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
    if j.get("refresh_token"):
        oa["refreshToken"] = j["refresh_token"]
    oa["expiresAt"] = int(time.time() * 1000) + int(j.get("expires_in", 7200)) * 1000
    json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return j["access_token"]

TOK = get_token()
_state = {"sid": None, "mid": 0}
HF = os.path.join(BASE, "Temp", "_val_hf.txt")

def rpc(method, params=None, notify=False, tries=2):
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
        time.sleep(1.0)
    return {"_err": "exhausted"}

def tool(name, args):
    return rpc("tools/call", {"name": name, "arguments": args})

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "val", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)

# CL 13 腿 2610~2710 -> 12 段 +1
cl_months = ["2610","2611","2612","2701","2702","2703","2704","2705","2706",
             "2707","2708","2709","2710"]
ho_months = cl_months  # 对称

cl_pairs = [f"US.CL{a}/CL{b}" for a, b in zip(cl_months, cl_months[1:])]
ho_pairs = [f"US.HO{a}/HO{b}" for a, b in zip(ho_months, ho_months[1:])]
all_pairs = cl_pairs + ho_pairs
print("CL +1 pairs:", cl_pairs)
print("HO +1 pairs:", ho_pairs)

# 批量 snapshot
r = tool("quote_market_snapshot", {"code_list": all_pairs})
snap_list = ((r.get("data") or {}).get("snapshot_list")) or []
valid = {x.get("code") for x in snap_list}
print("\n=== 验证结果 ===")
ok, bad = [], []
for p in all_pairs:
    if p in valid:
        ok.append(p)
    else:
        bad.append(p)
print("有效:", len(ok))
for p in all_pairs:
    mark = "OK " if p in valid else "NO "
    print(f"  {mark} {p}")
if bad:
    print("\n无效代码:", bad)
json.dump({"valid": ok, "invalid": bad}, open(os.path.join(BASE, "Temp", "spread_code_validate.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)