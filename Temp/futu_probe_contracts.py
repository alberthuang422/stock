# -*- coding: utf-8 -*-
"""探测富途可用的 WTI 月度合约范围"""
import json, subprocess, sys, time, os
sys.stdout.reconfigure(encoding="utf-8")

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
HF = os.path.join(BASE, "Temp", "_hf_pc.txt")

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

rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "probe2", "version": "1"}})
rpc("notifications/initialized", {}, notify=True)

# 候选：2026-10 起连续 24 个月 + 远季月
cands = []
for yy in (26, 27, 28, 29):
    for mm in range(1, 13):
        c = f"US.CL{yy}{mm:02d}"
        cands.append(c)
# 只要 >= 202610
cands = [c for c in cands if int(c[5:]) >= 2610]

res = tool("quote_market_snapshot", {"code_list": cands})
ok, bad = [], []
if isinstance(res, dict) and res.get("data"):
    for x in res["data"]["snapshot_list"]:
        lp = x.get("last_price")
        if lp and float(lp) > 0:
            ok.append((x["code"], x.get("name", ""), lp, x.get("update_time")))
        else:
            bad.append(x["code"])
else:
    print("snapshot raw:", json.dumps(res, ensure_ascii=False)[:800])

print(f"=== 可用合约 {len(ok)} 个 ===")
for c, nm, lp, ut in ok:
    print(f"  {c:<12} {nm:<20} last={lp:<9} upd={ut}")
print(f"\n=== 不可用 {len(bad)} 个 ===\n  {', '.join(bad)}")
json.dump({"ok": [c for c, *_ in ok], "bad": bad}, open(os.path.join(BASE, "Temp", "contracts_probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
