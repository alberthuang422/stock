# -*- coding: utf-8 -*-
"""富途 over-HTTP 拉取随机 10 只美股 2023-01-01 至今的日线（quote_history_kline）
经验：只传 {symbol, end, num}；0.25s pacing；token 2h 过期但 refreshToken 可自动续期
"""
import json
import os
import time
import subprocess
import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "resistance")
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"

def get_token():
    d = json.load(open(CRED, encoding="utf-8"))
    return list(d["mcpOAuth"].values())[0]["accessToken"]

_state = {"sid": None, "mid": 0}

def rpc(method, params=None, notify=False, session=None, token=None):
    _state["mid"] += 1
    hdrs = ["-H", "Content-Type: application/json",
            "-H", "Accept: application/json, text/event-stream",
            "-H", "Authorization: Bearer " + token]
    cmd = ["curl", "-s", "-D", os.path.join(BASE, "Temp", "hf2.txt"), "--max-time", "60",
           "-X", "POST", "https://mcp.futunn.com/mcp"] + hdrs
    sid = session if session else _state["sid"]
    if sid:
        cmd += ["-H", "Mcp-Session-Id: " + sid]
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        body["id"] = _state["mid"]
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sid2 = None
    for line in open(os.path.join(BASE, "Temp", "hf2.txt"), encoding="utf-8", errors="replace"):
        if line.lower().startswith("mcp-session-id"):
            sid2 = line.split(":", 1)[1].strip()
    return r.stdout.strip(), sid2

def parse_result(out):
    """SSE data: 行里提取 jsonrpc 响应"""
    for line in out.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except Exception:
                continue
    return None

def main():
    with open(os.path.join(BASE, "Temp", "resistance_picks.json"), encoding="utf-8") as f:
        picks = json.load(f)["tickers"]
    token = get_token()
    # initialize
    out, sid = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                  "clientInfo": {"name": "t", "version": "1"}}, token=token)
    _state["sid"] = sid if sid else _state["sid"]
    print("INIT sid:", _state["sid"])
    rpc("notifications/initialized", {}, notify=True, token=token)

    os.makedirs(DATA, exist_ok=True)
    ok = 0
    for tk in picks:
        sym = "US." + tk
        resp = None
        for attempt in range(4):
            out, _ = rpc("tools/call", {"name": "quote_history_kline",
                                        "arguments": {"symbol": sym, "end": "2026-09-02", "num": "1100"}},
                         token=token)
            resp = parse_result(out)
            if resp and "result" in resp and resp["result"].get("content"):
                break
            time.sleep(1.5 * (attempt + 1))
        if not resp:
            print(f"{tk} FAIL: no result, raw={out[:200]}")
            continue
        content = resp["result"]["content"][0]["text"]
        try:
            data = json.loads(content)
        except Exception:
            print(f"{tk} FAIL: content not json: {content[:200]}")
            continue
        # 结构探测
        if isinstance(data, dict) and "data" in data:
            klines = data["data"]
        elif isinstance(data, list):
            klines = data
        else:
            print(f"{tk} FAIL: unexpected shape: {str(data)[:200]}")
            continue
        if isinstance(klines, dict):
            for k in ("kline", "list", "items", "rows"):
                if k in klines:
                    klines = klines[k]
                    break
        if not isinstance(klines, list) or not klines:
            print(f"{tk} FAIL: empty klines, shape={str(data)[:200]}")
            continue
        rows = []
        for k in klines:
            if not isinstance(k, dict):
                continue
            # 时间字段兼容 time_key / timestamp / time
            ts = k.get("time_key") or k.get("timestamp") or k.get("time")
            if ts is None:
                continue
            if isinstance(ts, (int, float)) and ts > 10**11:
                ts = ts / 1000
            if isinstance(ts, str):
                try:
                    ts = datetime.datetime.strptime(ts[:10], "%Y-%m-%d").timestamp()
                except Exception:
                    continue
            d = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
            if d < "2023-01-01":
                continue
            o = k.get("open"); h = k.get("high"); l = k.get("low"); c = k.get("close"); v = k.get("volume")
            if None in (o, h, l, c):
                continue
            rows.append([d, o, h, l, c, v, c])
        rows.sort(key=lambda r: r[0])
        fn = os.path.join(DATA, f"{tk}.csv")
        with open(fn, "w", encoding="utf-8") as f:
            f.write("date,open,high,low,close,volume,adj_close\n")
            for r in rows:
                f.write(",".join(str(x) for x in r) + "\n")
        print(f"{tk}: {len(rows)} rows -> {fn}  (first {rows[0][0]} last {rows[-1][0]})")
        ok += 1
        time.sleep(0.3)
    print(f"DONE ok={ok}/{len(picks)}")

if __name__ == "__main__":
    main()
