# -*- coding: utf-8 -*-
"""验证：CVS 前复权价 2022 高点是否 ≈95（用户口径）。
复用富途 over-HTTP：get_token(refresh) + rpc，quote_history_kline 只传 {symbol,end,num}。
"""
import json
import subprocess
import sys
import time

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
AUTH_WELLKNOWN = "https://webapi.futunn.com/.well-known/oauth-authorization-server"


def get_token():
    cred = json.load(open(CRED, encoding="utf-8"))
    oa = cred["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]
    now_ms = int(time.time() * 1000)
    exp = oa.get("expiresAt") or 0
    left_ms = exp - now_ms if exp > 1000000000000 else (exp - time.time()) * 1000
    print(f"token 剩余 {left_ms/60000:.0f} min")
    if left_ms > 5 * 60 * 1000:
        return oa["accessToken"]
    refresh = oa.get("refreshToken")
    if not refresh:
        print("无 refreshToken")
        return None
    ci = (cred.get("mcpClientInfo") or {}).get("futu-mcp|e818c1846070ff2a") or {}
    client_id = ci.get("client_id") or oa.get("client_id")
    try:
        meta = json.loads(subprocess.run(["curl", "-s", "-m", "20", AUTH_WELLKNOWN],
                                         capture_output=True, text=True).stdout)
        tok_url = meta.get("token_endpoint") or meta.get("token_endpoint_uri")
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
        print("refresh OK")
        return j["access_token"]
    print("refresh 失败:", r.stdout[:200])
    return None


tok = get_token()
if not tok:
    sys.exit(1)
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/hf2.txt", "--max-time", "45", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        body["id"] = _state["mid"]
    cmd += ["-d", json.dumps(body)]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        for line in open("/tmp/hf2.txt", encoding="utf-8", errors="replace"):
            if line.lower().startswith("mcp-session-id"):
                _state["sid"] = line.split(":", 1)[1].strip()
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
        time.sleep(1.2 * (attempt + 1))
    return {"_err": "exhausted"}


def main():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "v", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)
    # 前复权(默认 autype=1)，end 2022-12-31 回拉 370 根覆盖 2022 全年
    r = rpc("tools/call", {"name": "quote_history_kline",
                           "arguments": {"symbol": "US.CVS", "end": "2022-12-31", "num": "370"}})
    if "_err" in r:
        print("FAIL", r)
        return
    kl = (r.get("data") or {}).get("kline_list") or []
    rows = [(str(k["date"]), k.get("high"), k.get("close")) for k in kl if k.get("close") is not None]
    rows.sort()
    y22 = [x for x in rows if x[0][:4] == "2022"]
    if not y22:
        print("无 2022 数据，rows:", len(rows), rows[:2], rows[-2:])
        return
    mh = max(y22, key=lambda x: x[1])
    mc = max(y22, key=lambda x: x[2])
    print(f"前复权 2022 最高盘中: {mh[1]} @ {mh[0]}")
    print(f"前复权 2022 最高收盘: {mc[2]} @ {mc[0]}")
    print(f"2022 收盘区间: {min(x[2] for x in y22):.2f} ~ {max(x[2] for x in y22):.2f} | 条数 {len(y22)}")


if __name__ == "__main__":
    main()
