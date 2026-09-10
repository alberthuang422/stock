# -*- coding: utf-8 -*-
"""
农产品×柴油 相关性研究 - 期货主连日线拉取（Futu MCP over-HTTP）2026-09-10
- HOmain 取暖油/ULSD 柴油（美国柴油期货基准）
- ZLmain 豆油（生物柴油原料）、RBmain RBOB汽油、CLmain WTI原油
- ZC/ZW/ZS 农产主连同步刷新
输出 Temp/fut_<sym>_main_1D.csv
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
    cmd = ["curl", "-s", "-D", "/tmp/hf_fut.txt", "--max-time", "45", "-X", "POST",
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
            with open("/tmp/hf_fut.txt", encoding="utf-8", errors="replace") as f:
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
        time.sleep(1.2 * (attempt + 1))
    return {"_err": "exhausted"}


def init():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "fut-dl", "version": "1"}})
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
        if first <= min_date or pages > 25:
            break
        end = (dt.date.fromisoformat(f"{first[:4]}-{first[4:6]}-{first[6:8]}") - dt.timedelta(days=1)).strftime("%Y-%m-%d")
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
          f"last={uniq[-1]['close']} -> {outfn}", flush=True)
    return len(uniq)


if __name__ == "__main__":
    init()
    jobs = [("US.HOmain", "ho_main_1D.csv"),
            ("US.ZLmain", "fut_zl_main_1D.csv"),
            ("US.RBmain", "fut_rb_main_1D.csv"),
            ("US.CLmain", "fut_cl_main_1D.csv"),
            ("US.ZCmain", "agri_zc_main_1D.csv"),
            ("US.ZWmain", "agri_zw_main_1D.csv"),
            ("US.ZSmain", "agri_zs_main_1D.csv")]
    n = 0
    for sym, fn in jobs:
        n += pull(sym, "2010-06-01", fn)
        time.sleep(0.4)
    print(f"DONE total_rows={n}")
