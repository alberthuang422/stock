# -*- coding: utf-8 -*-
"""futu MCP 诊断：tools/list + 单次 HO 查询。2026-09-10"""
import json, subprocess, time, datetime as dt

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
_sid = {"v": None}


def call(method, params=None, notify=False, show=False):
    hdr = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
           "-H", f"Authorization: Bearer {tok}"]
    if _sid["v"]:
        hdr += ["-H", f"Mcp-Session-Id: {_sid['v']}"]
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        body["id"] = 1
    cmd = ["curl", "-s", "-i", "--max-time", "45", "-X", "POST", "https://mcp.futunn.com/mcp"] + hdr + ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout
    for line in out.splitlines():
        if line.lower().startswith("mcp-session-id"):
            _sid["v"] = line.split(":", 1)[1].strip()
    payload = [l for l in out.splitlines() if l.startswith("data:") or l.startswith('{"jsonrpc')]
    if show:
        print("  RAW:", out[:400].replace("\n", " | "))
    if not payload:
        return {}
    last = payload[-1]
    try:
        return json.loads(last[5:] if last.startswith("data:") else last)
    except Exception:
        return {"_raw": last[:300]}


r = call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                        "clientInfo": {"name": "diag", "version": "1"}})
print("initialize:", "OK" if "result" in r else str(r)[:200], "| session:", _sid["v"])
call("notifications/initialized", {}, notify=True)
time.sleep(0.4)

r = call("tools/list", {})
tools = (r.get("result") or {}).get("tools") or []
print(f"\ntools/list -> {len(tools)} tools")
names = [t["name"] for t in tools]
print("有 future 相关:", [n for n in names if "future" in n or "kline" in n])
for t in tools:
    if t["name"] in ("quote_future_info", "quote_history_kline", "quote_referencefuture_list"):
        print(f"\n--- {t['name']} ---")
        print(json.dumps(t.get("inputSchema"), ensure_ascii=False)[:900])

print("\n== 单次调用测试 ==")
for args in [{"code_list": ["US.HOmain"]}, {"code_list": '["US.HOmain"]'}]:
    r = call("tools/call", {"name": "quote_future_info", "arguments": args})
    print(f"  args={args} -> {json.dumps(r, ensure_ascii=False)[:300]}")

r = call("tools/call", {"name": "quote_history_kline",
                        "arguments": {"symbol": "US.HOmain", "ktype": "2", "num": "5"}})
print("  HOmain kline ->", json.dumps(r, ensure_ascii=False)[:400])
