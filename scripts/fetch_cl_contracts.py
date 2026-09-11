# -*- coding: utf-8 -*-
"""CL(WTI) 各具体合约 K 线拉取 —— 日线 + 4小时(240min)（通用版）

沿革：由 fetch_cl_contracts_20260910.py 通用化，2026-09-11 起覆盖 M1~M13
      （CL2610 ~ CL2710，即 2026-10 至 2027-10）。

复用旧脚本的 rpc 实现（富途 MCP 端点 https://mcp.futunn.com/mcp），仅覆盖
其模块级 MIN_DATE / END_DATE / FORCE 后调用 pull()，保证逻辑与历史一致。

前置：token 过期时先跑 scripts/futu_token_refresh.py

用法：
  python scripts/fetch_cl_contracts.py                    # 默认全量重拉
  python scripts/fetch_cl_contracts.py --end 2026-09-11   # 指定结束日
  python scripts/fetch_cl_contracts.py --min 2025-03-24   # 指定起始日（拉更长历史）
  python scripts/fetch_cl_contracts.py --incremental      # 已有文件且已最新则跳过

输出：data/cl_contracts/{daily,4h}/US.CLxxxx.csv + contract_info.json
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

SPECIFIC = ["US.CL26{:02d}".format(m) for m in (10, 11, 12)] + \
           ["US.CL27{:02d}".format(m) for m in range(1, 11)]      # 2610..2710 = 13 腿
CONTINUOUS = ["US.CLcurrent", "US.CLnext"]
ALL = SPECIFIC + CONTINUOUS
OUT = F.OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", default=dt.date.today().isoformat())
    ap.add_argument("--min", dest="start", default="2026-03-10")
    ap.add_argument("--incremental", action="store_true",
                    help="已有文件且末行日期已覆盖到 end 前 1 自然日时跳过")
    a = ap.parse_args()

    F.MIN_DATE = a.start
    F.END_DATE = a.end
    F.FORCE = not a.incremental

    os.makedirs(os.path.join(OUT, "daily"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "4h"), exist_ok=True)
    F.init()
    print(f"end={a.end}  min={a.start}  force={F.FORCE}  contracts={len(ALL)}")

    # ---- 静态信息 ----
    infos = []
    for i in range(0, len(SPECIFIC), 5):
        r = F.rpc("tools/call", {"name": "quote_future_info",
                                 "arguments": {"code_list": SPECIFIC[i:i + 5]}})
        infos.extend(((r.get("data") or {}).get("future_info_list")) or [])
        time.sleep(0.3)
    r = F.rpc("tools/call", {"name": "quote_referencefuture_list", "arguments": {"symbol": "US.CLmain"}})
    refs = ((r.get("data") or {}).get("reference_list")) or []
    with open(os.path.join(OUT, "contract_info.json"), "w", encoding="utf-8") as f:
        json.dump({"future_info": infos,
                   "reference_listed": [x for x in refs if x.get("code") in (SPECIFIC + CONTINUOUS + ["US.CLmain"])],
                   "fetched_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f,
                  ensure_ascii=False, indent=1)
    print(f"\ncontract_info: {len(infos)} 条")
    for it in infos:
        ltt = it.get("last_trade_time") or 0
        s = dt.datetime.fromtimestamp(ltt / 1000, dt.timezone.utc).strftime("%Y-%m-%d") if ltt else "N/A"
        print(f"  {it['code']:12s} {it.get('name',''):20s} last_trade={s}")

    print("\n-- 拉取 K 线 --")
    for sym in ALL:
        F.pull(sym, "2", os.path.join(OUT, "daily"))
        time.sleep(0.5)
        F.pull(sym, "15", os.path.join(OUT, "4h"))
        time.sleep(0.5)
    print("DONE")


if __name__ == "__main__":
    main()
