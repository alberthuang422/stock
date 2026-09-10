# -*- coding: utf-8 -*-
"""补拉 ZC(玉米)全历史 + CL(WTI)全历史（修 2026-09-10 截断/分页中断）"""
import json, os, subprocess, time, datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Temp")
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
S = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    S["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/hf_fix.txt", "--max-time", "45", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if S["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {S['sid']}"]
    body = {"jsonrpc": "2.0", "id": S["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        with open("/tmp/hf_fix.txt", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.lower().startswith("mcp-session-id"):
                    S["sid"] = line.split(":", 1)[1].strip()
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
                return json.loads(c[0]["text"]) if c else d["result"]
            if "error" in d:
                return {"_err": d["error"]}
        except Exception:
            pass
    return {"_err": "empty"}


def call_retry(symbol, end):
    for a in range(5):
        r = rpc("tools/call", {"name": "quote_history_kline",
                               "arguments": {"symbol": symbol, "ktype": "2", "end": end, "num": "370"}})
        if "_err" not in r:
            return r
        print(f"   retry{a} {symbol} {r['_err']}", flush=True)
        time.sleep(2.0 + a * 2)
    return {"_err": "giveup"}


def pull(symbol, min_date, outfn):
    end = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    rows, pages = [], 0
    while pages < 30:
        r = call_retry(symbol, end)
        if "_err" in r:
            print(f"[{symbol}] FAIL {r['_err']}", flush=True)
            return 0
        kl = (r.get("data") or {}).get("kline_list") or []
        if not kl:
            break
        pages += 1
        rows.extend(kl)
        first = str(min(str(k["date"]) for k in kl))
        if first <= min_date:
            break
        end = (dt.date(int(first[:4]), int(first[4:6]), int(first[6:8])) - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        time.sleep(1.0)
    seen, uniq = set(), []
    for k in sorted(rows, key=lambda x: str(x["date"])):
        d = str(k["date"])
        if d in seen or k.get("close") is None:
            continue
        seen.add(d)
        uniq.append(k)
    if not uniq:
        print(f"[{symbol}] EMPTY - skip write", flush=True)
        return 0
    tmp = os.path.join(OUT, outfn + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("date,open,high,low,close,volume\n")
        for k in uniq:
            f.write(f"{k['date']},{k.get('open')},{k.get('high')},{k.get('low')},{k['close']},{k.get('volume')}\n")
    os.replace(tmp, os.path.join(OUT, outfn))
    print(f"[{symbol}] {pages}p {len(uniq)}rows {uniq[0]['date']}~{uniq[-1]['date']} last={uniq[-1]['close']} -> {outfn}", flush=True)
    return len(uniq)


if __name__ == "__main__":
    print("cooling down 25s...", flush=True)
    time.sleep(25)
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "fix", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)
    time.sleep(0.5)
    n = 0
    for sym, fn in [("US.ZCmain", "agri_zc_main_1D.csv"), ("US.CLmain", "fut_cl_main_1D.csv")]:
        n += pull(sym, "2010-06-01", fn)
        time.sleep(1.5)
    print(f"DONE rows={n}")
