# -*- coding: utf-8 -*-
"""HO(馏分油) 数据可达性探测：主连/连续近远月/具体合约 + 历史深度。2026-09-10"""
import json, subprocess, time, datetime as dt

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
_sid = {"v": None}


def call(method, params=None, notify=False):
    hdr = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
           "-H", f"Authorization: Bearer {tok}"]
    if _sid["v"]:
        hdr += ["-H", f"Mcp-Session-Id: {_sid['v']}"]
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        body["id"] = 1
    cmd = ["curl", "-s", "-i", "--max-time", "45", "-X", "POST", "https://mcp.futunn.com/mcp"] + hdr + ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.lower().startswith("mcp-session-id"):
            _sid["v"] = line.split(":", 1)[1].strip()
    pay = [l for l in r.stdout.splitlines() if l.startswith("data:") or l.startswith('{"jsonrpc')]
    if not pay:
        return {}
    try:
        return json.loads(pay[-1][5:] if pay[-1].startswith("data:") else pay[-1])
    except Exception:
        return {"_raw": pay[-1][:200]}


def tool(name, args):
    r = call("tools/call", {"name": name, "arguments": args})
    if "result" in r:
        c = r["result"].get("content")
        if c:
            try:
                return json.loads(c[0]["text"])
            except Exception:
                return {"_raw": str(c)[:200]}
        return r["result"]
    return r


call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "p2", "version": "1"}})
call("notifications/initialized", {}, notify=True)
time.sleep(0.3)

print("== A. 连接自检：HOmain 最近2根 ==")
r = tool("quote_history_kline", {"symbol": "US.HOmain", "ktype": "2", "end": "2026-09-09", "num": "2"})
kl = (r.get("data") or {}).get("kline_list") or []
print("  ", "OK" if kl else json.dumps(r, ensure_ascii=False)[:250], kl[-1] if kl else "")

print("\n== B. 具体合约 / 连续代码探测（quote_future_info）==")
cands = ["US.HOcurrent", "US.HOnext", "US.HO2610", "US.HO2611", "US.HO2701",
         "US.RBcurrent", "US.RBnext", "US.ZLcurrent", "US.ZLnext"]
r = tool("quote_future_info", {"code_list": cands})
lst = (r.get("data") or {}).get("future_info_list") or []
ok = {x["code"] for x in lst}
for c in cands:
    print(f"  {'OK ' if c in ok else '-- '}{c}")
print("  raw:", json.dumps(r, ensure_ascii=False)[:200])

print("\n== C. 连续近/远月历史深度（日线，回看到 2011）==")
for sym in ["US.HOcurrent", "US.HOnext", "US.CLcurrent", "US.CLnext"]:
    got, end, pages = {}, "2026-09-09", 0
    while pages < 12:
        r = tool("quote_history_kline", {"symbol": sym, "ktype": "2", "end": end, "num": "370"})
        kl = (r.get("data") or {}).get("kline_list") or []
        if not kl:
            if pages == 0:
                print(f"  {sym}: 空/错误 -> {json.dumps(r, ensure_ascii=False)[:150]}")
            break
        pages += 1
        for k in kl:
            got[str(k["date"])] = k.get("close")
        first = min(str(k["date"]) for k in kl)
        if first <= "20110101":
            break
        end = (dt.date(int(first[:4]), int(first[4:6]), int(first[6:8])) - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        time.sleep(0.35)
    if got:
        ks = sorted(got)
        print(f"  {sym}: {pages}p {len(ks)}bars {ks[0]} ~ {ks[-1]}  last={got[ks[-1]]}")
