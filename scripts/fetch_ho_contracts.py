# -*- coding: utf-8 -*-
"""HO(ULSD 取暖油) 各具体合约 K 线拉取 —— 日线 + 4小时(240min)
范式同 fetch_cl_contracts.py（WTI），2026-09-11 起覆盖 M1~M13
（HO2610 ~ HO2710，即 2026-10 至 2027-10）。
数据源：富途 MCP（https://mcp.futunn.com/mcp），token 自动刷新。
输出：data/ho_contracts/{daily,4h}/US.HOxxxx.csv + contract_info.json

用法：
  python scripts/fetch_ho_contracts.py --dry        # 仅验证代码命名/可拉性，不拉 K 线
  python scripts/fetch_ho_contracts.py              # 全量重拉
  python scripts/fetch_ho_contracts.py --incremental  # 已最新则跳过
"""
import os
import sys
import json
import time
import datetime as dt
import argparse
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "ho_contracts")
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"

SPECIFIC = ["US.HO26{:02d}".format(m) for m in (10, 11, 12)] + \
           ["US.HO27{:02d}".format(m) for m in range(1, 11)]      # 2610..2710 = 13 腿
CONTINUOUS = ["US.HOcurrent", "US.HOnext"]
ALL = SPECIFIC + CONTINUOUS
MIN_DATE = "2026-03-10"
END_DATE = dt.date.today().isoformat()
FORCE = True


def get_token():
    cred = json.load(open(CRED, encoding="utf-8"))
    key = "futu-mcp|e818c1846070ff2a"
    oa = cred["mcpOAuth"][key]
    now_ms = int(time.time() * 1000)
    exp = oa.get("expiresAt") or 0
    left = (exp - now_ms) if exp > 1000000000000 else (exp - time.time()) * 1000
    if left > 5 * 60 * 1000:
        return oa["accessToken"]
    refresh = oa.get("refreshToken")
    if not refresh:
        raise RuntimeError("无 refreshToken，请先手动授权")
    ci = (cred.get("mcpClientInfo", {}).get(key) or {})
    client_id = ci.get("client_id") or oa.get("client_id")
    body = {"grant_type": "refresh_token", "refresh_token": refresh}
    if client_id:
        body["client_id"] = client_id
    r = subprocess.run(["curl", "-s", "-m", "30", "-X", "POST",
                        "https://webapi.futunn.com/oauth2/token",
                        "-H", "Content-Type: application/json", "-d", json.dumps(body)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    j = json.loads(r.stdout or "{}")
    if not j.get("access_token"):
        raise RuntimeError("refresh 失败: " + r.stdout[:300])
    oa["accessToken"] = j["access_token"]
    if j.get("refresh_token"):
        oa["refreshToken"] = j["refresh_token"]
    oa["expiresAt"] = int(time.time() * 1000) + int(j.get("expires_in", 7200)) * 1000
    json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return j["access_token"]


TOK = get_token()
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {TOK}"]
_state = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/ho_fut.txt", "--max-time", "60", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body, ensure_ascii=False)]
    for attempt in range(4):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            with open("/tmp/ho_fut.txt", encoding="utf-8", errors="replace") as f:
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
                if "error" in d and attempt == 3:
                    return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.0 * (attempt + 1))
    return {"_err": "exhausted"}


def init():
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "ho-contracts", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)


def dstr(k):
    return f"{k['date']:08d}"[:4] + "-" + f"{k['date']:08d}"[4:6] + "-" + f"{k['date']:08d}"[6:8]


def tstr(k):
    tz = dt.timezone(dt.timedelta(hours=k.get("time_zone", 0)))
    return dt.datetime.fromtimestamp(k["time_key"] / 1000, tz).strftime("%Y-%m-%d %H:%M")


def pull(symbol, ktype, outdir):
    key = dstr if ktype == "2" else tstr
    fn = os.path.join(outdir, f"{symbol}.csv")
    min_rows = 100 if ktype == "2" else 700
    if os.path.exists(fn) and not FORCE:
        with open(fn, encoding="utf-8") as f:
            n = sum(1 for _ in f) - 1
        if n >= min_rows:
            print(f"  [{symbol} k{ktype}] cached {n} bars -> skip", flush=True)
            return n
    rows, pages, end = {}, 0, END_DATE
    empty_retry = 0
    while True:
        r = rpc("tools/call", {"name": "quote_history_kline",
                               "arguments": {"symbol": symbol, "ktype": ktype,
                                             "end": end, "num": "370"}})
        if "_err" in r:
            print(f"  [{symbol} k{ktype}] ERROR {str(r['_err'])[:120]}", flush=True)
            return 0
        kl = (r.get("data") or {}).get("kline_list") or []
        if not kl:
            if pages == 0 and empty_retry < 4:
                empty_retry += 1
                time.sleep(2.0 * empty_retry)
                continue
            break
        pages += 1
        for k in kl:
            if k.get("close") is not None:
                rows[key(k)] = k
        earliest = min(key(k) for k in kl)[:10]
        if earliest <= MIN_DATE or pages > 30:
            break
        end = (dt.date.fromisoformat(earliest) - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        time.sleep(0.35)

    ts = sorted(t for t in rows if t[:10] >= MIN_DATE)
    fn = os.path.join(outdir, f"{symbol}.csv")
    with open(fn, "w", encoding="utf-8") as f:
        if ktype == "2":
            f.write("date,open,high,low,close,volume,open_interest,settle\n")
            for t in ts:
                k = rows[t]
                f.write(f"{t},{k.get('open')},{k.get('high')},{k.get('low')},{k.get('close')},"
                        f"{k.get('volume')},{k.get('open_interest')},{k.get('settle_price')}\n")
        else:
            f.write("datetime,open,high,low,close,volume\n")
            for t in ts:
                k = rows[t]
                f.write(f"{t},{k.get('open')},{k.get('high')},{k.get('low')},{k.get('close')},{k.get('volume')}\n")
    if ts:
        last = rows[ts[-1]]
        print(f"  [{symbol} k{ktype}] {pages}p {len(ts)} bars  {ts[0]} ~ {ts[-1]}  "
              f"last={last.get('close')}  {last.get('sc_name', '')}", flush=True)
    else:
        print(f"  [{symbol} k{ktype}] EMPTY", flush=True)
    return len(ts)


def main():
    global END_DATE, FORCE
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="仅验证代码命名/可拉性，不拉 K 线")
    ap.add_argument("--incremental", action="store_true")
    ap.add_argument("--end", default=END_DATE)
    a = ap.parse_args()
    END_DATE = a.end
    FORCE = not a.incremental

    os.makedirs(os.path.join(OUT, "daily"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "4h"), exist_ok=True)
    init()

    # ---- 代码命名验证 + 静态信息 ----
    r = rpc("tools/call", {"name": "quote_referencefuture_list", "arguments": {"symbol": "US.HOmain"}})
    refs = ((r.get("data") or {}).get("reference_list")) or []
    print(f"\n[reference HOmain] 共 {len(refs)} 条候选代码（前 20）:")
    for x in refs[:20]:
        print(f"  {x.get('code'):14s} {x.get('name','')}")
    print(f"\nSPECIFIC(13) = {SPECIFIC}")
    print(f"CONTINUOUS = {CONTINUOUS}")

    infos = []
    for i in range(0, len(SPECIFIC), 5):
        r = rpc("tools/call", {"name": "quote_future_info",
                               "arguments": {"code_list": SPECIFIC[i:i + 5]}})
        infos.extend(((r.get("data") or {}).get("future_info_list")) or [])
        time.sleep(0.3)

    if a.dry:
        print(f"\n[DRY] future_info 命中 {len(infos)} 条:")
        for it in infos:
            ltt = it.get("last_trade_time") or 0
            s = dt.datetime.fromtimestamp(ltt / 1000, dt.timezone.utc).strftime("%Y-%m-%d") if ltt else "N/A"
            print(f"  {it['code']:12s} {it.get('name',''):20s} last_trade={s}")
        print("[DRY] 退出（未拉 K 线）")
        return

    with open(os.path.join(OUT, "contract_info.json"), "w", encoding="utf-8") as f:
        json.dump({"future_info": infos,
                   "reference_listed": [x for x in refs if x.get("code") in (SPECIFIC + CONTINUOUS + ["US.HOmain"])],
                   "fetched_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f,
                  ensure_ascii=False, indent=1)
    print(f"\ncontract_info: {len(infos)} 条")
    for it in infos:
        ltt = it.get("last_trade_time") or 0
        s = dt.datetime.fromtimestamp(ltt / 1000, dt.timezone.utc).strftime("%Y-%m-%d") if ltt else "N/A"
        print(f"  {it['code']:12s} {it.get('name',''):20s} last_trade={s}")

    print("\n-- 拉取 K 线 --")
    for sym in ALL:
        pull(sym, "2", os.path.join(OUT, "daily"))
        time.sleep(0.5)
        pull(sym, "15", os.path.join(OUT, "4h"))
        time.sleep(0.5)
    print("DONE")


if __name__ == "__main__":
    main()
