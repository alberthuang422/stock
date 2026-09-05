# -*- coding: utf-8 -*-
"""Futu 指定日期盘前/盘后历史数据拉取器（2026-09-04 实测打通）

用法:
  python Temp/futu_premarket_hist.py US.NVDA 2026-09-03                  # 盘前 5min
  python Temp/futu_premarket_hist.py US.NVDA 2026-09-03 --ktype 1        # 1 分钟
  python Temp/futu_premarket_hist.py US.NVDA 2026-08-25 2026-08-28       # 日期范围
  python Temp/futu_premarket_hist.py US.NVDA 2026-09-03 --session post   # 盘后
  python Temp/futu_premarket_hist.py US.NVDA --live                      # 实时快照(盘前字段)

--session: pre(默认) | post | overnight | all
--out:     输出 CSV 路径（默认 results/premarket/{sym}_{session}_{D1}_{D2}.csv）

已知边界（探针实测）:
  - 历史扩展时段是稀疏采样: 04:00 ET 竞价 bar 几乎总在, 部分日期另有 04:00-05:00 ET
    连续 5min bar; 近期日期可能只有 1-2 根。非完整分钟线。
  - quote_history_kline: extended_time=2, 必须 start=D end=D+1（单日 start=end 退化）,
    time_key 为北京时间毫秒, num 上限 370。
  - end=D 锚点在 D 12:00 BJ, 向后回溯; overnight(08:00-16:00 BJ D+1) 需锚 end=D+2。
"""
import json, subprocess, sys, time, argparse, csv, os
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
BJ = timezone(timedelta(hours=8))
ET = ZoneInfo("America/New_York")
HDRS = None
_state = {"sid": None, "mid": 0}

def _tok():
    global HDRS
    tok = json.load(open(CRED, encoding="utf-8"))["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]["accessToken"]
    HDRS = ["-H", "Content-Type: application/json",
            "-H", "Accept: application/json, text/event-stream",
            "-H", "Authorization: Bearer " + tok]

def rpc(method, params=None, notify=False):
    _state["mid"] += 1
    cmd = ["curl", "-s", "-D", "hf_pre.txt", "--max-time", "60", "-X", "POST", "https://mcp.futunn.com/mcp"] + HDRS
    if _state["sid"]:
        cmd += ["-H", "Mcp-Session-Id: " + _state["sid"]]
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        body["id"] = _state["mid"]
    cmd += ["-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in open("hf_pre.txt", encoding="utf-8", errors="replace"):
        if line.lower().startswith("mcp-session-id"):
            _state["sid"] = line.split(":", 1)[1].strip()
    return r.stdout.strip()

def parse(resp):
    s = resp.strip()
    if s.startswith("data:"):
        s = s[5:].strip()
    return json.loads(s)

def init():
    _tok()
    rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "premarket-hist", "version": "1"}})
    rpc("notifications/initialized", {}, notify=True)

def get_kline(symbol, ktype, et, start, end, num=370):
    """返回 bar 列表（失败/空返回 []）"""
    resp = rpc("tools/call", {"name": "quote_history_kline", "arguments": {
        "symbol": symbol, "ktype": ktype, "extended_time": et,
        "start": start, "end": end, "num": num, "autype": 1}})
    try:
        j = parse(parse(resp)["result"]["content"][0]["text"])
        if j.get("ret_code") != 0 and "data" not in j:
            return []
        return j.get("data", {}).get("kline_list", [])
    except Exception:
        return []

# 会话窗口（北京时间，相对交易日 D）
WINDOWS = {
    "pre":       (0, 16*60,       21*60+30),   # D 16:00 ~ 21:30 BJ
    "post":      (1, 4*60,        8*60),       # D+1 04:00 ~ 08:00 BJ
    "overnight": (1, 8*60,        16*60),      # D+1 08:00 ~ 16:00 BJ
    "all":       (0, 16*60,       40*60),      # D 16:00 ~ D+1 16:00 BJ
}
# 需要锚定的 end 偏移（天）：窗口落进 [end_anchor-24h, end_anchor] 附近
ANCHOR = {"pre": 1, "post": 1, "overnight": 2, "all": 2}

def in_window(t: datetime, day: date, session: str) -> bool:
    off, lo, hi = WINDOWS[session]
    d0 = day + timedelta(days=off)
    if t.date() != d0:
        return False
    m = t.hour * 60 + t.minute
    return lo <= m <= hi

def fetch(symbol, d1, d2, ktype, session):
    days = []
    d = d1
    while d <= d2:
        days.append(d)
        d += timedelta(days=1)
    rows = []
    for i, day in enumerate(days):
        end = (day + timedelta(days=ANCHOR[session])).strftime("%Y-%m-%d")
        start = day.strftime("%Y-%m-%d")
        bars = get_kline(symbol, ktype, 2, start, end)
        for b in bars:
            if "open" not in b:
                continue  # 服务器偶发返回缺 OHLC 的占位 bar（今日盘后/未来时段占位）
            t = datetime.fromtimestamp(b["time_key"] / 1000, BJ)
            if in_window(t, day, session):
                rows.append({
                    "time_bj": t.strftime("%Y-%m-%d %H:%M"),
                    "time_et": t.astimezone(ET).strftime("%Y-%m-%d %H:%M"),
                    "open": b["open"], "high": b["high"], "low": b["low"], "close": b["close"],
                    "volume": b["volume"], "turnover": round(b.get("turnover", 0), 2),
                })
        if i < len(days) - 1:
            time.sleep(0.3)  # pacing
    rows.sort(key=lambda r: r["time_bj"])
    return rows

def prev_rth_close(symbol, day):
    """前一交易日 RTH 收盘：回看最多 5 天，取 D 日 00:00 BJ 前最后一根 RTH 5min bar（含 D 00:00~04:00 BJ 尾段=上一 RTH 收尾）"""
    bars = get_kline(symbol, 6, 0, (day - timedelta(days=5)).strftime("%Y-%m-%d"),
                     day.strftime("%Y-%m-%d"), num=370)
    c = None
    for b in bars:
        if "open" not in b:
            continue
        t = datetime.fromtimestamp(b["time_key"] / 1000, BJ)
        if t.date() < day or (t.date() == day and (t.hour * 60 + t.minute) <= 4 * 60):
            c = b["close"]
    return c

def live_snapshot(symbol):
    resp = rpc("tools/call", {"name": "quote_market_snapshot", "arguments": {"code_list": [symbol]}})
    j = parse(parse(resp)["result"]["content"][0]["text"])
    lst = j["data"]["snapshot_list"] if isinstance(j.get("data"), dict) else j["data"]
    s = lst[0]
    keys = ["update_time", "market_state", "cur_price", "last_close",
            "pre_price", "pre_change_rate" if "pre_change_rate" in s else "pre_volume",
            "pre_volume", "pre_high", "pre_low",
            "after_price", "after_change_rate", "after_volume", "after_high", "after_low",
            "overnight_price", "overnight_volume"]
    out = {k: s[k] for k in keys if k in s}
    # update_time 转北京时间
    if "update_time" in out and isinstance(out["update_time"], (int, float)):
        out["update_time_bj"] = datetime.fromtimestamp(out.pop("update_time") / 1000, BJ).strftime("%Y-%m-%d %H:%M:%S")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("d1", nargs="?", help="YYYY-MM-DD")
    ap.add_argument("d2", nargs="?", help="YYYY-MM-DD（可选，默认=d1）")
    ap.add_argument("--ktype", type=int, default=6, help="1=1分钟 6=5分钟（默认6）")
    ap.add_argument("--session", default="pre", choices=["pre", "post", "overnight", "all"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--live", action="store_true", help="只拉实时快照")
    args = ap.parse_args()

    init()

    if args.live:
        snap = live_snapshot(args.symbol)
        print(json.dumps(snap, ensure_ascii=False, indent=2))
        return

    if not args.d1:
        print("需要日期参数（或 --live）")
        return
    d1 = datetime.strptime(args.d1, "%Y-%m-%d").date()
    d2 = datetime.strptime(args.d2, "%Y-%m-%d").date() if args.d2 else d1

    rows = fetch(args.symbol, d1, d2, args.ktype, args.session)
    if not rows:
        print(f"{args.symbol} {args.d1}~{args.d2} {args.session}: 0 bars（无数据/休市日）")
        return

    out = args.out or os.path.join("..", "results", "premarket",
        f"{args.symbol.replace('.','_')}_{args.session}_{args.d1}_{args.d2 or args.d1}.csv")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # 摘要（按日分组）
    pc = prev_rth_close(args.symbol, d2)
    print(f"{args.symbol} {args.d1}~{args.d2} session={args.session} ktype={args.ktype}: {len(rows)} bars -> {os.path.normpath(out)}")
    by_day = {}
    for r in rows:
        by_day.setdefault(r["time_bj"][:10], []).append(r)
    for day, rs in sorted(by_day.items()):
        o, c = rs[0]["open"], rs[-1]["close"]
        h = max(r["high"] for r in rs); l = min(r["low"] for r in rs)
        v = sum(r["volume"] for r in rs)
        chg = f"  vs前RTH收 {pc} → {(c/pc-1)*100:+.2f}%" if pc else ""
        print(f"  {day}: {len(rs)} bars  {rs[0]['time_et'][11:]}~{rs[-1]['time_et'][11:]} ET  "
              f"O={o} H={h} L={l} C={c} V={v}{chg}")

if __name__ == "__main__":
    main()
