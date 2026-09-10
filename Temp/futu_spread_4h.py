# -*- coding: utf-8 -*-
"""拉取 CL2610/2611/2612 的 4 小时 K 线（用于跨期价差合成）"""
import json, subprocess, sys, time, os
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\Administrator\Desktop\stock"
CRED = r"C:\Users\Administrator\.workbuddy\connectors\2e7b65ad-3a22-424a-a190-5066a615e2dc\.credentials.v3.json"
TOKEN_URL = "https://mcp.futunn.com/mcp"
TODAY = "2026-09-10"

def get_token():
    cred = json.load(open(CRED, encoding="utf-8"))
    key = "futu-mcp|e818c1846070ff2a"
    oa = cred["mcpOAuth"][key]
    now_ms = int(time.time() * 1000)
    exp = oa.get("expiresAt") or 0
    left_ms = (exp - now_ms) if exp > 1000000000000 else (exp - time.time()) * 1000
    if left_ms > 5 * 60 * 1000:
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
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    if j.get("access_token"):
        oa["accessToken"] = j["access_token"]
        if j.get("refresh_token"):
            oa["refreshToken"] = j["refresh_token"]
        oa["expiresAt"] = int(time.time() * 1000) + int(j.get("expires_in", 7200)) * 1000
        json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return j["access_token"]
    print("refresh failed", file=sys.stderr)
    return None

TOK = get_token()
_state = {"sid": None, "mid": 0}
HF = os.path.join(BASE, "Temp", "_hf_4h.txt")

def rpc(method, params=None, notify=False, tries=3):
    cmd = ["curl", "-s", "-D", HF, "--max-time", "70", "-X", "POST", TOKEN_URL,
           "-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
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
                    print(f"[{method}] {d['error']}", file=sys.stderr)
                    return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.5 * (attempt + 1))
    return {"_err": "exhausted"}

def tool(name, args):
    return rpc("tools/call", {"name": name, "arguments": args})

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "h4", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)

LEGS = ["US.CL2610", "US.CL2611", "US.CL2612"]
out = {"ktype": 15, "legs": {}}
for c in LEGS:
    r = tool("quote_history_kline", {"symbol": c, "end": TODAY, "num": 370, "ktype": 15, "autype": 0})
    bars = []
    try:
        bars = r["data"]["kline_list"]
    except Exception:
        print(c, "raw:", json.dumps(r, ensure_ascii=False)[:300])
    out["legs"][c] = bars
    print(f"{c:<12} bars={len(bars)}")
    if bars:
        print("   first:", bars[0].get("time_key"), " last:", bars[-1].get("time_key"))
    time.sleep(1.3)

json.dump(out, open(os.path.join(BASE, "results", "futu_spread_4h_raw.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved -> results/futu_spread_4h_raw.json")
