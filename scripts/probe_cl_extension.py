# -*- coding: utf-8 -*-
"""探测 CL 新合约（2704~2710）在富途的数据可用性 + 现有合约最新数据日期。"""
import os, sys, json, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_cl_contracts_20260910 as F

NEW = [f"US.CL27{m:02d}" for m in range(4, 11)]      # 2704..2710
EXIST = ["US.CL2610", "US.CL2611", "US.CL2703", "US.CLcurrent", "US.CLnext"]

if __name__ == "__main__":
    F.init()
    print("=== quote_future_info 批量查询 ===")
    for i in range(0, len(NEW), 5):
        r = F.rpc("tools/call", {"name": "quote_future_info", "arguments": {"code_list": NEW[i:i + 5]}})
        lst = ((r.get("data") or {}).get("future_info_list")) or []
        if not lst:
            print("  batch", NEW[i:i + 5], "-> 空", str(r)[:160])
        for x in lst:
            ltt = x.get("last_trade_time") or 0
            s = dt.datetime.fromtimestamp(ltt / 1000, dt.timezone.utc).strftime("%Y-%m-%d") if ltt else "N/A"
            print(f"  {x['code']:<12} {x.get('name',''):<20} last_trade={s}")

    print("\n=== 日线可用性（end=2026-09-11, num=370）===")
    for sym in NEW + EXIST:
        r = F.rpc("tools/call", {"name": "quote_history_kline",
                                 "arguments": {"symbol": sym, "ktype": "2", "end": "2026-09-11", "num": "370"}})
        kl = ((r.get("data") or {}).get("kline_list")) or []
        if not kl:
            print(f"  {sym:<14} EMPTY  ({str(r)[:110]})")
        else:
            f, l = kl[0], kl[-1]
            print(f"  {sym:<14} n={len(kl):<4} {F.dstr(f)} ~ {F.dstr(l)}  last_close={l.get('close')}  sc={l.get('sc_name','')}")
        import time as _t
        _t.sleep(0.4)
