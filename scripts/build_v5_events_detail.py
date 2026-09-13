#!/usr/bin/env python3
"""从 v5 bars 生成逐事件 detail（每个命中 ±24 bar 窗口），供逐事件上下双窗小图。"""
import json, os
BASE = "/Users/alberthuang/Desktop/股票分析"
OUT = os.path.join(BASE, "results/spread_divergence")
WIN = 24

for prod in ["CL", "HO", "RB"]:
    bars = json.load(open(f"{OUT}/v5_{prod}_bars.json"))
    hit_idx = [i for i, b in enumerate(bars) if b["hit"]]
    events = []
    for hi in hit_idx:
        lo = max(0, hi - WIN); hi2 = min(len(bars) - 1, hi + WIN)
        seg = bars[lo:hi2 + 1]
        votes = [j for j in range(len(seg)) if seg[j]["vote"]]
        trig = hi - lo
        ev = {
            "trigger_ts": bars[hi]["t"],
            "regime": bars[hi]["regime"],
            "regime_label": "走扩期" if bars[hi]["regime"] == 1 else "回落期",
            "ts": [s["t"] for s in seg],
            "x": [s["x"] for s in seg],
            "y": [s["y"] for s in seg],
            "voteIdx": votes,
            "triggerIdx": trig,
        }
        events.append(ev)
    out = {"product": prod, "n_events": len(events), "events": events}
    with open(f"{OUT}/v5_{prod}_events_detail.json", "w") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"{prod}: {len(events)} 个事件 已写出 v5_{prod}_events_detail.json")
