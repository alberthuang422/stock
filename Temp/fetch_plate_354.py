# -*- coding: utf-8 -*-
"""批量拉取 354 只的富途行业板块（plate_type=INDUSTRY），限速+退避+断点续跑"""
import json, subprocess, time, os, sys

BASE = r"C:\Users\Administrator\Desktop\stock"
OUT = BASE + r"\Temp\plate_354_raw.json"
URL = "https://mcp.futunn.com/mcp"

cred = json.load(open(r"C:\Users\Administrator\.workbuddy\connectors\2e7b65ad-3a22-424a-a190-5066a615e2dc\.credentials.v3.json", encoding="utf-8"))
TOK = list(cred["mcpOAuth"].values())[0]["accessToken"]

def curl(payload, sid=None, hdr=False):
    args = ["curl", "-sS", "-m", "30", "-X", "POST", URL,
            "-H", "Content-Type: application/json",
            "-H", "Accept: application/json, text/event-stream",
            "-H", "Authorization: Bearer " + TOK]
    if sid: args += ["-H", "Mcp-Session-Id: " + sid]
    if hdr: args += ["-D", "-"]
    args += ["-d", json.dumps(payload)]
    return subprocess.run(args, capture_output=True, text=True).stdout

def parse_sse(txt):
    for line in txt.splitlines():
        if line.startswith("data:"):
            try: return json.loads(line[5:].strip())
            except Exception: pass
    try: return json.loads(txt)
    except Exception: return None

init = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"wb","version":"1"}}}
out = curl(init, hdr=True)
sids = [l.split(":",1)[1].strip() for l in out.splitlines() if l.lower().startswith("mcp-session-id")]
if not sids:
    print("INIT FAIL:", out[:300]); sys.exit(1)
SID = sids[0]
curl({"jsonrpc":"2.0","method":"notifications/initialized"}, SID)

rows = json.load(open(BASE + r"\Temp\hot_filtered.json", encoding="utf-8"))
symbols = ["US." + r[2] for r in rows]
done = {}
if os.path.exists(OUT):
    done = json.load(open(OUT, encoding="utf-8"))

def fetch(sym, tries=4):
    for t in range(tries):
        r = curl({"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"quote_owner_plate","arguments":{"symbol":sym}}}, SID)
        j = parse_sse(r)
        try:
            data = json.loads(j["result"]["content"][0]["text"])
        except Exception:
            data = None
        if data and data.get("ret_code") == 0:
            inds = [s.get("plate_sc_name") or s.get("plate_name") for s in data["data"]["sectors"] if s.get("plate_type") == "INDUSTRY"]
            return inds
        time.sleep(0.8 * (2**t))
    return None

fail = 0
for i, sym in enumerate(symbols):
    if sym in done and done[sym] is not None:
        continue
    v = fetch(sym)
    done[sym] = v
    if v is None: fail += 1
    if i % 25 == 0:
        json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{i+1}/{len(symbols)} done, fail={fail}", flush=True)
    time.sleep(0.25)
json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
n_none = sum(1 for v in done.values() if v is None)
print(f"ALL DONE total={len(done)} fail={n_none}")
