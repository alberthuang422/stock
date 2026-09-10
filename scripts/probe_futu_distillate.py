# -*- coding: utf-8 -*-
"""探测 富途 futures 是否覆盖馏分油（HO/ULSD/Gasoil）及其可拉取历史深度。2026-09-10"""
import json, subprocess, time

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_s = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    _s["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/p_fut.txt", "--max-time", "60", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _s["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_s['sid']}"]
    body = {"jsonrpc": "2.0", "id": _s["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    for a in range(4):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            for line in open("/tmp/p_fut.txt", encoding="utf-8", errors="replace"):
                if line.lower().startswith("mcp-session-id"):
                    _s["sid"] = line.split(":", 1)[1].strip()
        except FileNotFoundError:
            pass
        out = r.stdout.strip()
        if out:
            last = out.splitlines()[-1]
            try:
                d = json.loads(last[5:] if last.startswith("data:") else last)
                if notify:
                    return {}
                if "result" in d:
                    c = d["result"].get("content")
                    return json.loads(c[0]["text"]) if c else d["result"]
                if "error" in d and a == 3:
                    return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(0.8 * (a + 1))
    return {"_err": "exhausted"}


def init():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "probe", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)


init()

print("== quote_future_info 探测 ==")
cands = ["US.HOmain", "US.HO2610", "US.HO2611", "US.ULSDmain", "US.QGmain", "US.RBmain",
         "US.HOcurrent", "US.HOnext", "US.HOZ26", "US.HOF27", "US.HOG27"]
for c in cands:
    r = rpc("tools/call", {"name": "quote_future_info", "arguments": {"code_list": [c]}})
    data = r.get("data") or {}
    lst = data.get("future_info_list") or []
    if lst:
        it = lst[0]
        print(f"  OK  {c:14s} -> {it.get('code')} {it.get('name')} {it.get('exchange')} last_trade={it.get('last_trade_time')}")
    else:
        print(f"  --  {c:14s} -> {str(r)[:110]}")
    time.sleep(0.25)

print("\n== referencefuture_list ==")
for sym in ["US.CLmain", "US.HOmain", "US.RBmain"]:
    r = rpc("tools/call", {"name": "quote_referencefuture_list", "arguments": {"symbol": sym}})
    refs = ((r.get("data") or {}).get("reference_list")) or []
    print(f"  {sym}: {len(refs)} -> {[x.get('code') for x in refs][:14]}  {str(r)[:80] if not refs else ''}")
    time.sleep(0.25)

print("\n== 历史 K 线深度测试（日线，回看到 2020）==")
for sym in ["US.HOcurrent", "US.CLcurrent"]:
    got = []
    end = "2020-06-30"
    for page in range(3):
        r = rpc("tools/call", {"name": "quote_history_kline",
                               "arguments": {"symbol": sym, "ktype": "2", "end": end, "num": "370"}})
        kl = (r.get("data") or {}).get("kline_list") or []
        if not kl:
            print(f"  {sym}: page{page} EMPTY  {str(r)[:120]}")
            break
        dates = sorted(str(k["date"]) for k in kl)
        print(f"  {sym}: page{page} {len(kl)} bars {dates[0]} ~ {dates[-1]}")
        end = (time.strftime("%Y-%m-%d", time.strptime(dates[0], "%Y%m%d")))
        end = (time.strftime("%Y%m%d", time.strptime(dates[0], "%Y%m%d")))
        # 简化：往回再取一页
        y, m, d = int(dates[0][:4]), int(dates[0][4:6]), int(dates[0][6:8])
        import datetime as dt
        end = (dt.date(y, m, d) - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        time.sleep(0.4)
print("DONE")
