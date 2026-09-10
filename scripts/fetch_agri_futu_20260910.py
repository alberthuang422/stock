# -*- coding: utf-8 -*-
"""
玉米/大豆/小麦主连日线拉取（Futu MCP over-HTTP）2026-09-10
用途：SPY/QQQ 下跌波段中农产品表现统计
- 富途主连：US.ZCmain(玉米) / US.ZSmain(大豆) / US.ZWmain(小麦)，历史约到 2011-07/09
- 输出 Temp/agri_z{cs w}_main_1D.csv
"""
import json, os, subprocess, sys, time, datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Temp")
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"

tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/hf_agri.txt", "--max-time", "45", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            with open("/tmp/hf_agri.txt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.lower().startswith("mcp-session-id"):
                        _state["sid"] = line.split(":", 1)[1].strip()
        except FileNotFoundError:
            pass
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
        time.sleep(1.5 * (attempt + 1))
    return {"_err": "exhausted"}


def init():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "agri-dl", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)


def pull(symbol, min_date, outfn):
    end = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    rows, pages = [], 0
    while True:
        r = rpc("tools/call", {"name": "quote_history_kline",
                               "arguments": {"symbol": symbol, "ktype": "2", "end": end, "num": "370"}})
        if "_err" in r:
            print(f"[{symbol}] ERROR {r['_err']}", flush=True)
            return 0
        kl = (r.get("data") or {}).get("kline_list") or []
        if not kl:
            break
        pages += 1
        rows.extend(kl)
        first = min(str(k["date"]) for k in kl)
        if first <= min_date:
            break
        end = (dt.date.fromisoformat(first) - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        time.sleep(0.3)
    seen, uniq = set(), []
    for k in sorted(rows, key=lambda x: str(x["date"])):
        d = str(k["date"])
        if d in seen or k.get("close") is None:
            continue
        seen.add(d)
        uniq.append(k)
    fn = os.path.join(OUT, outfn)
    with open(fn, "w", encoding="utf-8") as f:
        f.write("date,open,high,low,close,volume\n")
        for k in uniq:
            f.write(f"{k['date']},{k.get('open')},{k.get('high')},{k.get('low')},"
                    f"{k['close']},{k.get('volume')}\n")
    print(f"[{symbol}] {pages}p {len(uniq)}rows {uniq[0]['date']}~{uniq[-1]['date']} "
          f"last={uniq[-1]['close']} -> {fn}", flush=True)
    return len(uniq)


if __name__ == "__main__":
    init()
    n = 0
    for sym, fn in [("US.ZCmain", "agri_zc_main_1D.csv"),
                    ("US.ZSmain", "agri_zs_main_1D.csv"),
                    ("US.ZWmain", "agri_zw_main_1D.csv")]:
        n += pull(sym, "2011-01-01", fn)
        time.sleep(0.4)
    print(f"DONE rows={n}")
