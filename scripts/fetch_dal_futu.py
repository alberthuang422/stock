# -*- coding: utf-8 -*-
"""
DAL + SPY 日线全量拉取（Futu MCP over-HTTP 直连）2026-09-02
Yahoo 403 / stooq 需 JS 验证，改走富途通道（记忆 09-01 实证：354/354 全成）
- autype 默认 1 前复权，ktype "2" 日线，num 370 分页往回翻
- 输出 data/dal/DAL, 1D.csv / data/spy/SPY, 1D.csv（覆盖，同源口径统一）
"""
import json, os, subprocess, sys, time, datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"

tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/hf_dal.txt", "--max-time", "45", "-X", "POST",
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
            with open("/tmp/hf_dal.txt", encoding="utf-8", errors="replace") as f:
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
                       "clientInfo": {"name": "dal-dl", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)


def fetch_page(symbol, end):
    r = rpc("tools/call", {"name": "quote_history_kline",
                           "arguments": {"symbol": symbol, "ktype": "2", "end": end, "num": "370"}})
    if "_err" in r:
        return None
    kl = (r.get("data") or {}).get("kline_list") or []
    return kl


def pull(symbol, min_date, dirname):
    end = dt.date(2026, 9, 1).strftime("%Y-%m-%d")
    rows = []
    pages = 0
    while True:
        kl = fetch_page(symbol, end)
        if not kl:
            print(f"[{symbol}] empty page at end={end}", flush=True)
            break
        pages += 1
        rows.extend(kl)
        first = min(str(k["date"]) for k in kl)
        if first <= min_date:
            break
        d0 = dt.date.fromisoformat(first) - dt.timedelta(days=1)
        end = d0.strftime("%Y-%m-%d")
        time.sleep(0.3)
    # 去重 + 升序
    seen, uniq = set(), []
    for k in sorted(rows, key=lambda x: str(x["date"])):
        d = str(k["date"])
        if d in seen:
            continue
        seen.add(d)
        uniq.append(k)
    fn = os.path.join(DATA, dirname, f"{dirname.upper()}, 1D.csv")
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    with open(fn, "w", encoding="utf-8") as f:
        f.write("date,open,high,low,close,volume,adj_close\n")
        for k in uniq:
            c = k.get("close")
            if c is None:
                continue
            f.write(f"{k['date']},{k.get('open')},{k.get('high')},{k.get('low')},"
                    f"{c},{k.get('volume')},{c}\n")
    print(f"[{symbol}] {pages} pages, {len(uniq)} rows -> {fn} | "
          f"{uniq[0]['date']} ~ {uniq[-1]['date']} | last close={uniq[-1]['close']}", flush=True)
    return len(uniq)


def main():
    init()
    # DAL 2007-05 上市；SPY 1993-01 起
    n1 = pull("US.DAL", "2007-04-01", "dal")
    time.sleep(0.5)
    n2 = pull("US.SPY", "1993-01-01", "spy")
    print(f"DONE dal={n1} spy={n2}")


if __name__ == "__main__":
    main()
