# -*- coding: utf-8 -*-
"""从 Futu MCP over-HTTP 拉取 APO 及另类资管同行日线，保存 CSV。参考 Temp/rsi_futu_354.py。"""
import json, subprocess, sys, time, os
import datetime as dt
import csv

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H","Content-Type: application/json","-H","Accept: application/json, text/event-stream","-H",f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}

def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl","-s","-D","/tmp/hf.txt","--max-time","45","-X","POST","https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]: cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc":"2.0","method":method,"params":params or {}} if notify else {"jsonrpc":"2.0","id":_state["mid"],"method":method,"params":params or {}}
    cmd += ["-d", json.dumps(body)]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        for line in open("/tmp/hf.txt", encoding="utf-8", errors="replace"):
            if line.lower().startswith("mcp-session-id"): _state["sid"] = line.split(":",1)[1].strip()
        out = r.stdout.strip()
        if out:
            last = out.splitlines()[-1]
            try:
                d = json.loads(last[5:] if last.startswith("data:") else last)
                if "result" in d:
                    if notify: return {}
                    c = d["result"].get("content")
                    if c: return json.loads(c[0]["text"])
                    return d["result"]
                if "error" in d and attempt == 2: return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.2*(attempt+1))
    return {"_err":"exhausted"}

def init():
    rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"f","version":"1"}})
    rpc("notifications/initialized", {}, notify=True)

def fetch(symbol, num=800):
    end = dt.date.today().strftime("%Y-%m-%d")
    # 只传 {symbol, end, num}，ktype 显式传会 schema 报错（历史教训）
    r = rpc("tools/call", {"name":"quote_history_kline","arguments":{"symbol":symbol,"end":end,"num":str(num)}})
    if "_err" in r: return None, r
    kl = (r.get("data") or {}).get("kline_list") or []
    rows = []
    for k in kl:
        if k.get("close") is None: continue
        rows.append([str(k["date"]), k.get("open"), k.get("high"), k.get("low"), k["close"], k.get("volume")])
    rows.sort(key=lambda x: x[0])
    return rows, None

def main():
    symbols = sys.argv[1:] or ["US.BX","US.KKR","US.OWL","US.TPG","US.ARES","US.CG","US.APO"]
    init()
    out_dir = r"C:/Users/Administrator/Desktop/stock/data/futu_peers"
    os.makedirs(out_dir, exist_ok=True)
    for sym in symbols:
        rows, err = fetch(sym)
        tag = sym.split(".")[-1]
        if err or not rows:
            print(f"{tag}: FAIL {err}", flush=True)
            continue
        path = os.path.join(out_dir, f"{tag}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date","open","high","low","close","volume"])
            w.writerows(rows)
        print(f"{tag}: {len(rows)} rows {rows[0][0]}~{rows[-1][0]} -> {path}", flush=True)
        time.sleep(0.3)

if __name__ == "__main__":
    main()