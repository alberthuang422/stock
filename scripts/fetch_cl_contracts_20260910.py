# -*- coding: utf-8 -*-
"""
CL(WTI) 各具体合约 K 线拉取 —— 日线 + 4小时(240min) —— 最近 6 个月
2026-09-10

Futu 覆盖范围（已核实 2026-09-10）：
  - 仅提供未到期合约，已到期合约（<=CL2609）返回空；故滚动口径只能用
    连续代码 US.CLcurrent(当期) / US.CLnext(下期)。
  - 具体合约可取：CL2610 起。

输出目录：data/cl_contracts/
  daily/US.CLxxxx.csv    date,open,high,low,close,volume,open_interest,settle
  4h/US.CLxxxx.csv       datetime,open,high,low,close,volume
  contract_info.json     合约静态信息（含 last_trade_time）
"""
import json, os, subprocess, time, datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "cl_contracts")
CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"

MIN_DATE = "2026-03-10"
END_DATE = "2026-09-10"
FORCE = os.environ.get("CL_FORCE") == "1"

SPECIFIC = ["US.CL2610", "US.CL2611", "US.CL2612",
            "US.CL2701", "US.CL2702", "US.CL2703"]
CONTINUOUS = ["US.CLcurrent", "US.CLnext"]
ALL = SPECIFIC + CONTINUOUS

tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
HDRS = ["-H", "Content-Type: application/json", "-H", "Accept: application/json, text/event-stream",
        "-H", f"Authorization: Bearer {tok}"]
_state = {"sid": None, "mid": 0}


def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", "/tmp/cl_fut.txt", "--max-time", "60", "-X", "POST",
           "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc": "2.0", "id": _state["mid"], "method": method, "params": params or {}}
    if notify:
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    cmd += ["-d", json.dumps(body)]
    for attempt in range(4):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            with open("/tmp/cl_fut.txt", encoding="utf-8", errors="replace") as f:
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
                       "clientInfo": {"name": "cl-contracts", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)


def dstr(k):
    """日线：date 为 int YYYYMMDD"""
    return f"{k['date']:08d}"[:4] + "-" + f"{k['date']:08d}"[4:6] + "-" + f"{k['date']:08d}"[6:8]


def tstr(k):
    """4h：time_key 为 ms epoch，按合约交易所时区换算"""
    tz = dt.timezone(dt.timedelta(hours=k.get("time_zone", 0)))
    return dt.datetime.fromtimestamp(k["time_key"] / 1000, tz).strftime("%Y-%m-%d %H:%M")


def pull(symbol, ktype, outdir):
    key = dstr if ktype == "2" else tstr
    fn = os.path.join(outdir, f"{symbol}.csv")
    min_rows = 100 if ktype == "2" else 700      # 断点续跑：已完整则不重复拉
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
            if pages == 0 and empty_retry < 4:          # 首屏空 → 大概率限流，重试
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


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "daily"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "4h"), exist_ok=True)
    init()

    # 静态信息
    infos = []
    for i in range(0, len(SPECIFIC), 5):
        r = rpc("tools/call", {"name": "quote_future_info", "arguments": {"code_list": SPECIFIC[i:i + 5]}})
        infos.extend(((r.get("data") or {}).get("future_info_list")) or [])
        time.sleep(0.3)
    r = rpc("tools/call", {"name": "quote_referencefuture_list", "arguments": {"symbol": "US.CLmain"}})
    refs = ((r.get("data") or {}).get("reference_list")) or []
    with open(os.path.join(OUT, "contract_info.json"), "w", encoding="utf-8") as f:
        json.dump({"future_info": infos,
                   "reference_listed": [x for x in refs if x["code"] in
                                        (SPECIFIC + CONTINUOUS + ["US.CLmain"])],
                   "fetched_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                  f, ensure_ascii=False, indent=1)
    print(f"contract_info: {len(infos)} 条")
    for it in infos:
        ltt = it.get("last_trade_time") or 0
        s = dt.datetime.fromtimestamp(ltt / 1000, dt.timezone.utc).strftime("%Y-%m-%d") if ltt else "N/A"
        print(f"  {it['code']:12s} {it['name']:22s} last_trade={s}")

    print("\n-- 拉取 K 线 --")
    for sym in ALL:
        pull(sym, "2", os.path.join(OUT, "daily"))
        time.sleep(0.6)
        pull(sym, "15", os.path.join(OUT, "4h"))
        time.sleep(0.6)
    print("DONE")
