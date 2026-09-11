# -*- coding: utf-8 -*-
"""CL / HO / RB 各具体合约 1 小时(60min) K 线拉取（ktype=9）

范式与 fetch_cl_contracts.py 一致：M1~M13 固定月 + 连续合约(current/next)。
输出：data/<commodity>_contracts/1h/US.<PREF>xxxx.csv
      data/<commodity>_contracts/contract_info.json（bootstrap RB 时一并写入）

ktype 权威枚举（futu MCP quote_history_kline，2026-09-11 核实）：
  1=1m 2=day 3=week 4=month 5=year 6=5m 7=15m 8=30m 9=60m(1h)
  10=3m 11=quarter 14=120m 15=240m(4h) 26=10m 29=180m

前置：token 过期先跑 scripts/futu_token_refresh.py
用法：
  python scripts/fetch_1h_contracts.py --commodity rb --dry      # 仅验证 RB 代码命名
  python scripts/fetch_1h_contracts.py --commodity cl           # 拉 CL 1h
  python scripts/fetch_1h_contracts.py                           # 拉 cl+ho+rb 1h
"""
import os
import sys
import json
import time
import datetime as dt
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_cl_contracts_20260910 as F  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KTYPE = "9"  # 60-min

SPEC = lambda pre: ["US.{}26{:02d}".format(pre, m) for m in (10, 11, 12)] + \
                   ["US.{}27{:02d}".format(pre, m) for m in range(1, 11)]
CONT = lambda pre: ["US.{}current".format(pre), "US.{}next".format(pre)]

COMM = {
    "cl": ("CL", "US.CLmain", os.path.join(BASE, "data", "cl_contracts")),
    "ho": ("HO", "US.HOmain", os.path.join(BASE, "data", "ho_contracts")),
    "rb": ("RB", "US.RBmain", os.path.join(BASE, "data", "rb_contracts")),
}


def fetch_info(pre, main_sym, out):
    """写 contract_info.json（RB bootstrap 用；CL/HO 更新同目录现有）"""
    specific = SPEC(pre)
    continuous = CONT(pre)
    infos = []
    for i in range(0, len(specific), 5):
        r = F.rpc("tools/call", {"name": "quote_future_info",
                                 "arguments": {"code_list": specific[i:i + 5]}})
        infos.extend(((r.get("data") or {}).get("future_info_list")) or [])
        time.sleep(0.3)
    r = F.rpc("tools/call", {"name": "quote_referencefuture_list", "arguments": {"symbol": main_sym}})
    refs = ((r.get("data") or {}).get("reference_list")) or []
    with open(os.path.join(out, "contract_info.json"), "w", encoding="utf-8") as f:
        json.dump({"future_info": infos,
                   "reference_listed": [x for x in refs if x.get("code") in (specific + continuous + [main_sym])],
                   "fetched_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f,
                  ensure_ascii=False, indent=1)
    print(f"  contract_info: {len(infos)} 条 -> {os.path.join(out, 'contract_info.json')}")
    for it in infos:
        ltt = it.get("last_trade_time") or 0
        s = dt.datetime.fromtimestamp(ltt / 1000, dt.timezone.utc).strftime("%Y-%m-%d") if ltt else "N/A"
        print(f"    {it['code']:12s} {it.get('name',''):20s} last_trade={s}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commodity", choices=["cl", "ho", "rb"], default="all",
                    help="默认拉全部 cl+ho+rb")
    ap.add_argument("--dry", action="store_true", help="仅验证代码命名，不拉 K 线")
    ap.add_argument("--incremental", action="store_true")
    ap.add_argument("--end", default=dt.date.today().isoformat())
    ap.add_argument("--min", dest="start", default="2026-03-10")
    a = ap.parse_args()

    F.MIN_DATE = a.start
    F.END_DATE = a.end
    F.FORCE = not a.incremental

    keys = ["cl", "ho", "rb"] if a.commodity == "all" else [a.commodity]
    F.init()
    print(f"end={a.end}  min={a.start}  ktype={KTYPE}(60min)  commodities={keys}")

    for k in keys:
        pre, main_sym, out = COMM[k]
        specific = SPEC(pre)
        continuous = CONT(pre)
        allsym = specific + continuous
        os.makedirs(os.path.join(out, "1h"), exist_ok=True)
        print(f"\n===== {k.upper()} ({pre}) {len(allsym)} 合约 =====")

        if a.dry:
            fetch_info(pre, main_sym, out)
            continue

        # 静态信息（bootstrap RB；CL/HO 刷新合同表）
        fetch_info(pre, main_sym, out)
        # 1h K 线
        print("  -- 1h K 线 --")
        for sym in allsym:
            F.pull(sym, KTYPE, os.path.join(out, "1h"))
            time.sleep(0.5)
    print("DONE")


if __name__ == "__main__":
    main()
