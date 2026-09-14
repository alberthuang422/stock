# -*- coding: utf-8 -*-
"""RB(RBOB 汽油) 各具体合约 K 线拉取 —— 日线 + 60min（ktype=2 / 9）

复用 fetch_cl_contracts_20260910 的 MCP RPC 通道，仅换品种/输出目录。
输出：data/rb_contracts/daily/US.RBxxxx.csv  date,open,high,low,close,volume,open_interest,settle
      data/rb_contracts/1h/US.RBxxxx.csv     datetime,open,high,low,close,volume
      data/rb_contracts/contract_info.json   静态信息（含 last_trade_time）

前置：token 过期先跑 scripts/futu_token_refresh.py（access token 仅 2h 有效）
用法：python scripts/fetch_rb_contracts.py [--dry]
"""
import os
import sys
import json
import time
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_cl_contracts_20260910 as F  # noqa: E402

BASE = os.path.dirname(HERE)
OUT = os.path.join(BASE, "data", "rb_contracts")

SPECIFIC = ["US.RB2610", "US.RB2611", "US.RB2612"] + \
           ["US.RB27{:02d}".format(m) for m in range(1, 11)]
CONTINUOUS = ["US.RBcurrent", "US.RBnext"]
ALL = SPECIFIC + CONTINUOUS


def main():
    dry = "--dry" in sys.argv
    F.OUT = OUT
    F.MIN_DATE = "2026-03-10"
    F.END_DATE = dt.date.today().isoformat()
    F.FORCE = True

    os.makedirs(os.path.join(OUT, "daily"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "1h"), exist_ok=True)
    F.init()
    print("END_DATE =", F.END_DATE, flush=True)

    infos = []
    for i in range(0, len(SPECIFIC), 5):
        r = F.rpc("tools/call", {"name": "quote_future_info",
                                 "arguments": {"code_list": SPECIFIC[i:i + 5]}})
        infos.extend(((r.get("data") or {}).get("future_info_list")) or [])
        time.sleep(0.3)
    r = F.rpc("tools/call", {"name": "quote_referencefuture_list",
                             "arguments": {"symbol": "US.RBmain"}})
    refs = ((r.get("data") or {}).get("reference_list")) or []
    with open(os.path.join(OUT, "contract_info.json"), "w", encoding="utf-8") as f:
        json.dump({"future_info": infos,
                   "reference_listed": [x for x in refs
                                        if x.get("code") in (ALL + ["US.RBmain"])],
                   "fetched_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                  f, ensure_ascii=False, indent=1)
    print("contract_info:", len(infos), "条", flush=True)
    for it in infos:
        ltt = it.get("last_trade_time") or 0
        s = dt.datetime.fromtimestamp(ltt / 1000,
                                      dt.timezone(dt.timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M") if ltt else "N/A"
        print("   {:12s} {:24s} last_trade={}".format(it.get("code", ""),
                                                      it.get("name", ""), s), flush=True)
    if dry:
        return

    for sym in ALL:
        F.pull(sym, "2", os.path.join(OUT, "daily"))
        time.sleep(0.5)
        F.pull(sym, "9", os.path.join(OUT, "1h"))
        time.sleep(0.5)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
