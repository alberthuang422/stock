# -*- coding: utf-8 -*-
"""每日热门美股 RSI 报告主控脚本（定时任务入口）
流程: token检查/刷新 -> 拉热门榜Top500 -> 三规则过滤 -> 批量RSI(260日线 Wilder14)
      -> 行业板块归并 -> 构建HTML(日期版+latest) -> 写自动化日志 -> git commit
用法: python daily_hot_rsi.py [YYYY-MM-DD]   （日期默认今天，用于覆盖/重跑）
依赖: Temp/ 下 fetch/rsi/plate/build 模块逻辑已内联或复用
"""
import json, subprocess, sys, time, os, csv, collections, datetime as dt

BASE = r"C:\Users\Administrator\Desktop\stock"
CRED = r"C:\Users\Administrator\.workbuddy\connectors\2e7b65ad-3a22-424a-a190-5066a615e2dc\.credentials.v3.json"
TOKEN_URL = "https://mcp.futunn.com/mcp"
AUTH_WELLKNOWN = "https://mcp.futunn.com/.well-known/oauth-authorization-server"
LOG_DIR = os.path.expanduser(r"~/.workbuddy/automation-logs")
DATE = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().strftime("%Y-%m-%d")
DATE_YMD = DATE.replace("-", "")
PY = r"C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

LOG = []

def log(msg):
    line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    LOG.append(line)

def write_log(success, note=""):
    os.makedirs(LOG_DIR, exist_ok=True)
    fname = os.path.join(LOG_DIR, f"{DATE}_daily-hot-rsi.log")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"执行时间: {dt.datetime.now().isoformat()}\n")
        f.write(f"任务: daily-hot-rsi (每日热门美股RSI报告)\n")
        f.write(f"结果: {'成功' if success else '失败'}\n")
        if note: f.write(f"说明: {note}\n")
        f.write("--- 日志 ---\n")
        f.write("\n".join(LOG))

# ---------------- 1. Token 检查与刷新 ----------------
def get_token():
    """读凭证；若 accessToken 过期（expiresAt 为毫秒），尝试 refresh grant；写回新 token。返回 token 或 None"""
    cred = json.load(open(CRED, encoding="utf-8"))
    oa = cred["mcpOAuth"]["futu-mcp|e818c1846070ff2a"]
    now_ms = int(time.time() * 1000)
    exp = oa.get("expiresAt") or 0
    if exp > 1000000000000:  # 毫秒
        left_ms = exp - now_ms
    else:  # 秒
        left_ms = (exp - time.time()) * 1000
    log(f"token 剩余 {left_ms/60000:.0f} min")
    if left_ms > 5 * 60 * 1000:
        return oa["accessToken"]
    # 尝试 refresh grant
    refresh = oa.get("refreshToken")
    if not refresh:
        log("无 refreshToken，需手动重授权 (Temp/futu_oauth_reauth.py)")
        return None
    ci_map = cred.get("mcpClientInfo", {})
    ci = ci_map.get("futu-mcp|e818c1846070ff2a") or {}
    client_id = ci.get("client_id") or oa.get("client_id")
    log("accessToken 过期，尝试 refresh…")
    try:
        meta = json.loads(subprocess.run(["curl","-s","-m","20",AUTH_WELLKNOWN],capture_output=True,text=True).stdout)
        tok_url = meta.get("token_endpoint") or meta.get("token_endpoint_uri")
    except Exception as e:
        log(f"读取 oauth metadata 失败: {e}")
        tok_url = "https://webapi.futunn.com/oauth2/token"
    body = {"grant_type":"refresh_token","refresh_token":refresh}
    if client_id: body["client_id"] = client_id
    r = subprocess.run(["curl","-s","-m","30","-X","POST",tok_url,
        "-H","Content-Type: application/json","-d",json.dumps(body)],capture_output=True,text=True)
    try:
        j = json.loads(r.stdout)
    except Exception:
        j = {}
    if j.get("access_token"):
        oa["accessToken"] = j["access_token"]
        if j.get("refresh_token"): oa["refreshToken"] = j["refresh_token"]
        oa["expiresAt"] = int(time.time() * 1000) + int(j.get("expires_in", 7200)) * 1000
        json.dump(cred, open(CRED,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
        log(f"refresh OK，新 token 有效 {j.get('expires_in',7200)}s")
        return j["access_token"]
    log(f"refresh 失败: {r.stdout[:200] or r.stderr[:200]} → 需手动重授权 (Temp/futu_oauth_reauth.py)")
    return None

# ---------------- 2. MCP HTTP 客户端 ----------------
TOK = None
_state = {"sid": None, "mid": 0}

def rpc(method, params=None, notify=False, tries=3):
    cmd = ["curl","-s","-D",os.path.join(BASE,"Temp","_hf.txt"),"--max-time","45",
           "-X","POST",TOKEN_URL,"-H","Content-Type: application/json",
           "-H","Accept: application/json, text/event-stream","-H",f"Authorization: Bearer {TOK}"]
    if _state["sid"]: cmd += ["-H", f"Mcp-Session-Id: {_state['sid']}"]
    body = {"jsonrpc":"2.0","method":method,"params":params or {}} if notify else \
           {"jsonrpc":"2.0","id":_state["mid"]+1,"method":method,"params":params or {}}
    _state["mid"] += 1
    cmd += ["-d", json.dumps(body)]
    for attempt in range(tries):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            for line in open(os.path.join(BASE,"Temp","_hf.txt"), encoding="utf-8", errors="replace"):
                if line.lower().startswith("mcp-session-id"):
                    _state["sid"] = line.split(":",1)[1].strip()
        except Exception:
            pass
        out = r.stdout.strip()
        if out:
            last = out.splitlines()[-1]
            try:
                d = json.loads(last[5:] if last.startswith("data:") else last)
                if "result" in d:
                    c = d["result"].get("content")
                    if c: return json.loads(c[0]["text"])
                    return d["result"]
                if "error" in d and attempt == tries-1:
                    return {"_err": d["error"]}
            except Exception:
                pass
        time.sleep(1.5*(attempt+1))
    return {"_err":"exhausted"}

def init_mcp():
    rpc("initialize", {"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"daily","version":"1"}})
    rpc("notifications/initialized", {}, notify=True)

# ---------------- 3. 热门榜 + 过滤 ----------------
SCREEN_ARGS_BASE = {
    "limit": 300,
    "screen_queries": [
        {"simple_field_query": {"simple_field": 1, "screen_value_list": [2]}},  # MARKET=US
        {"simple_property_query": {"property": {"name": 2301}, "lower": {"value": 5000000000000, "includes": True}}},  # 市值>=50亿美元
    ],
    "retrieve_queries": [
        {"basic_property": {"name": 1101}},  # symbol
        {"basic_property": {"name": 1102}},  # name
        {"simple_property": {"name": 2201}},  # last x1e3
        {"simple_property": {"name": 2301}},  # mktcap x1e3
        {"cumulative_property": {"name": 3102, "days": 1}},  # chgRate x1e3
        {"featured_property": {"name": 5214}},  # 综合热度 x1e5
    ],
    "sort": {"direction": 2, "featured_property": {"name": 5214}},  # 热度降序
}

def fetch_hot_top500():
    """quote_stock_screen: US + 市值>=50亿$, 综合热度5214 desc, 分页300*2"""
    seen, page_key, page = {}, None, 0
    while page < 4:  # 最多 4 页=1200，取前 500
        args = json.loads(json.dumps(SCREEN_ARGS_BASE))
        if page_key: args["next_key"] = page_key
        r = rpc("tools/call", {"name":"quote_stock_screen","arguments":args})
        if "_err" in r:
            log(f"screen 第{page+1}页失败: {r['_err']}")
            break
        txt = r.get("ret_code") is not None and r or r
        if isinstance(r, dict) and r.get("ret_code") == 0:
            pass
        items = ((r.get("data") or {}).get("items")) or []
        log(f"screen 第{page+1}页: {len(items)} 条")
        for it in items:
            code = (it.get("code") or "").replace("US.","")
            if code: seen[code] = it
        pag = r.get("pagination") or {}
        page_key = pag.get("next_key")
        if not pag.get("has_more") or not page_key: break
        page += 1
    items = [seen[k] for k in list(seen)[:500]]
    json.dump(items, open(os.path.join(BASE,"Temp",f"hot500_{DATE_YMD}.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"热门榜合并: {len(items)} 只")
    return items

def build_rows_from_items(items):
    """解析 screen 条目 -> [rank, orig, code, name, heat, price, chg, cap]（从 x1e3/x1e5 还原）"""
    rows = []
    for i, it in enumerate(items, 1):
        res = it.get("results") or []
        def val(idx, key):
            # res[idx] 形如 {"basic_property_result":{...,"value":"..."}}
            if idx >= len(res): return None
            obj = res[idx]
            sub = obj.get(key) or {}
            v = sub.get("value")
            if v is None: v = (sub.get("res") or {}).get("sval")
            return v
        code = (it.get("code") or "").replace("US.","")
        name = val(1, "basic_property_result") or it.get("name") or it.get("sc_name") or ""
        price = val(2, "simple_property_result"); price = float(price)/1000 if price not in (None,"") else None
        cap = val(3, "simple_property_result"); cap = float(cap)/1000 if cap not in (None,"") else None
        chg = val(4, "cumulative_property_result"); chg = float(chg)/1000 if chg not in (None,"") else None
        heat = val(5, "featured_property_result"); heat = float(heat)/100000 if heat not in (None,"") else None
        rows.append([i, i, code, name, round(heat,1) if heat is not None else None,
                     round(price,2) if price else None, round(chg,2) if chg is not None else None,
                     round(cap,1) if cap else None])
    return rows

# 中概/ADR 判定集合（09-01 实证口径：146 只剔除 = 26 价格>500 + 120 中概/ADR；与当日过滤完全对齐）
CN_SET = {"SKHY","TSM","BABA","NIO","PDD","XPEV","LI","FUTU","BIDU","TCEHY","LX","JD","SY","MNSO",
          "BILI","ASX","UMC","TME","TCOM","DIDIY","HSAI","IQ","NTES","VIPS","VNET","TIGR","GDS",
          "ZH","GOTU","WB","JKS","CSIQ","EH","BYDDY","BEKE","QFIN","EDU","KC"}
ADR_SET = {"NOK","ARM","SHOP","MELI","SE","PONY","DUO","TEAM","GRAB","NVO","PBR","PBR.A","BHP",
           "HSBC","SIVEF","PMI","BTI","RY","SKM","TM","SONY","TSEM","CCJ","NTR","B","SCCO","BB",
           "ENB","STM","FN","CLS","ONON","CAN","WETO","XHLD","BULL","PRZO","HYMC","FTFT",
           "DDL","WCT","SLOIF","NCI","TYOYY","MRAAY","KLAR","KXIAY","XIACY","RDHL","ABCL","LABT",
           "WFF","NCPL","DPRO","AEHL","ONC","POET","PSQL","LKNCY","MPNGY","IREN","BZ","DE","LAC",
           "RITR","VIOT","YDDL","SMTC","ENGS","TJGC","AMBR","COOT","FINV","FROG","TRON",
           "CHA","CLGN","PASW","WRD","LOT","SMJF","OMH","DEO","BNTX"}
NON_CN_ADR_OK = {"TSLA","NVDA","AAPL","MSFT","AMZN","META","GOOGL","GOOG","AVGO","NFLX","AMD","INTC",
                 "CRM","ORCL","ADBE","CSCO","QCOM","TXN","MU","AMAT","LRCX","KLAC","ADI","PLTR","COIN"}

def filter_rules(rows):
    """三规则: 价格>$500 / 中概 / ADR。返回过滤后 [rank, orig, code, name, heat, price, chg, cap]"""
    out, skipped = [], collections.Counter()
    for r in rows:
        _, orig, code, name, heat, price, chg, cap = r
        if price is not None and price > 500:
            skipped["price>500"] += 1; continue
        if code in CN_SET and code not in NON_CN_ADR_OK:
            skipped["中概"] += 1; continue
        if code in ADR_SET and code not in NON_CN_ADR_OK:
            skipped["ADR"] += 1; continue
        r[0] = len(out) + 1
        out.append(r)
    log(f"过滤后 {len(out)} 只 (剔除: {dict(skipped)})")
    return out

# ---------------- 4. RSI 批量 ----------------
def wilder_rsi(closes, n=14):
    out=[None]*len(closes)
    if len(closes)<=n: return out
    g=sum(max(closes[i]-closes[i-1],0) for i in range(1,n+1))
    l=sum(max(closes[i-1]-closes[i],0) for i in range(1,n+1))
    ag,al=g/n,l/n
    def calc(ag,al):
        if ag==0 and al==0: return 50.0
        if al==0: return 100.0
        if ag==0: return 0.0
        return 100-100/(1+ag/al)
    out[n]=calc(ag,al)
    for i in range(n+1,len(closes)):
        ch=closes[i]-closes[i-1]
        ag=(ag*(n-1)+max(ch,0))/n; al=(al*(n-1)+max(-ch,0))/n
        out[i]=calc(ag,al)
    return out

def fetch_kline(symbol):
    r = rpc("tools/call", {"name":"quote_history_kline",
        "arguments":{"symbol":symbol,"end":DATE,"num":"260"}}, tries=3)
    if "_err" in r: return None
    kl = ((r.get("data") or {}).get("kline_list")) or []
    closes=[k["close"] for k in kl if k.get("close") is not None]
    dates=[str(k["date"]) for k in kl if k.get("close") is not None]
    return (closes, dates) if closes else None

def batch_rsi(rows):
    results, fails = [], []
    t0 = time.time()
    n = len(rows)
    for idx,(rank,orig,code,name,heat,price,chg,cap) in enumerate(rows):
        sym = "US." + code
        got = fetch_kline(sym)
        if not got or len(got[0]) < 20:
            got = fetch_kline(sym)
        if not got or len(got[0]) < 20:
            fails.append(code); continue
        closes, dates = got
        rsi = wilder_rsi(closes)
        i = len(closes)-1
        r_now, r5 = rsi[i], rsi[i-5] if i>=5 else None
        r20 = rsi[i-20] if i>=20 else None
        win60 = [x for x in rsi[-60:] if x is not None]
        last52 = closes[-252:] if len(closes)>=252 else closes
        hi, lo = max(last52), min(last52)
        results.append({"rank":rank,"code":code,"name":name,"last_date":dates[-1],
            "price":round(closes[-1],2),"rsi14":round(r_now,1) if r_now is not None else None,
            "rsi14_5d":round(r5,1) if r5 is not None else None,
            "rsi14_20d":round(r20,1) if r20 is not None else None,
            "rsi60_min":round(min(win60),1) if win60 else None,
            "rsi60_max":round(max(win60),1) if win60 else None,
            "hi52":round(hi,2),"lo52":round(lo,2),
            "off_hi52":round((closes[-1]/hi-1)*100,1),
            "ret20":round((closes[-1]/closes[-21]-1)*100,1) if len(closes)>21 else None,
            "ret60":round((closes[-1]/closes[-61]-1)*100,1) if len(closes)>61 else None,
            "bars":len(closes)})
        if (idx+1) % 50 == 0:
            log(f"  RSI {idx+1}/{n} | {time.time()-t0:.0f}s")
        time.sleep(0.25)
    log(f"RSI 完成 {len(results)} ok / {len(fails)} fail ({time.time()-t0:.0f}s)")
    if fails:
        log("失败重试…")
        for code in list(fails):
            got = fetch_kline("US."+code)
            if got and len(got[0]) >= 20:
                closes, dates = got
                rsi = wilder_rsi(closes); i = len(closes)-1
                r5 = rsi[i-5] if i>=5 else None; r20 = rsi[i-20] if i>=20 else None
                win60 = [x for x in rsi[-60:] if x is not None]
                last52 = closes[-252:] if len(closes)>=252 else closes
                hi, lo = max(last52), min(last52)
                rr = next((x for x in rows if x[2]==code), None)
                results.append({"rank":rr[0],"code":code,"name":rr[3],"last_date":dates[-1],
                    "price":round(closes[-1],2),"rsi14":round(rsi[i],1) if rsi[i] is not None else None,
                    "rsi14_5d":round(r5,1) if r5 is not None else None,
                    "rsi14_20d":round(r20,1) if r20 is not None else None,
                    "rsi60_min":round(min(win60),1) if win60 else None,
                    "rsi60_max":round(max(win60),1) if win60 else None,
                    "hi52":round(hi,2),"lo52":round(lo,2),
                    "off_hi52":round((closes[-1]/hi-1)*100,1),
                    "ret20":round((closes[-1]/closes[-21]-1)*100,1) if len(closes)>21 else None,
                    "ret60":round((closes[-1]/closes[-61]-1)*100,1) if len(closes)>61 else None,
                    "bars":len(closes)})
                fails.remove(code)
                time.sleep(0.25)
        log(f"重试后仍失败 {len(fails)}: {','.join(fails)}")
    results.sort(key=lambda x: x["rank"])
    return results, fails

# ---------------- 5. 板块归并（复用 plate_bucket 逻辑） ----------------
CRYPTO = {"MSTR","COIN","CRCL","BMNR","PURR","ASST","BTDR","MARA","STRC","WULF",
          "RIOT","CIFR","QNT","BTCT","CLSK","BLSH","NCT","HUT","GEMI","SBET"}
SPACE = {"RKLB","ASTS","LUNR","RDW","SPCE","ACHR","JOBY","ONDS","RCAT","U"}
RULES = [
    ("半导体/AI硬件", ["半导体","计算机硬件","科技仪器","光电子","电子元件","电路"]),
    ("软件/SaaS",    ["应用软件","软件基础设施","信息技术服务","数据处理"]),
    ("互联网/电商",  ["互联网","电子商务","广告","娱乐","游戏","媒体","流媒体","广播"]),
    ("金融",         ["资本","银行","保险","资产管理","信贷","金融数据","证券","支付","经纪"]),
    ("能源",         ["油气","煤","石油","天然气","炼化","能源设备","铀"]),
    ("公用/电力",    ["电力","公用","燃气","水务","核","太阳能"]),
    ("医药/生物",    ["生物","制药","药","医疗","健康","诊断","研究"]),
    ("可选消费",     ["汽车","零售","服装","鞋","餐厅","饮料","旅游","博彩","邮轮","酒店","度假","赌场","住宿","家庭","奢侈","耐用","住宅","家具","家电","消费"]),
    ("必选消费",     ["食品","烟草","农产品","农业投入","个人用品","超市","包装","农业"]),
    ("军工/航天",    ["航空航天","国防","军工"]),
    ("工业/机械/运输",["机械","建筑","金属","采矿","化工","设备","运输","铁路","船舶","工业","综合","环保","航空","废物","物流"]),
    ("通信",         ["电信","通讯","通信","光纤"]),
    ("地产",         ["房地产","REIT"]),
    ("材料",         ["材料","纸","化学","锂","铜","铝","黄金","贵金属","空壳"]),
]
KNOWN = json.load(open(os.path.join(BASE,"Temp","plate_bucket.json"),encoding="utf-8"))

def bucket(code, plates):
    if code in CRYPTO: return "加密关联"
    if code in SPACE:  return "航天/太空"
    if code in KNOWN and KNOWN[code].get("bucket"):
        return KNOWN[code]["bucket"]
    if not plates: return "其他"
    joined = "|".join(plates)
    for b, kws in RULES:
        for kw in kws:
            if kw in joined: return b
    return "其他"

def fetch_plates(codes):
    """逐只拉 INDUSTRY 板块；失败留空交给 KNOWN/规则"""
    raw = {}
    for i, code in enumerate(codes):
        sym = "US." + code
        r = rpc("tools/call", {"name":"quote_owner_plate","arguments":{"symbol":sym}}, tries=2)
        if "_err" not in r and (r.get("ret_code") == 0 or r.get("data")):
            inds = [s.get("plate_sc_name") or s.get("plate_name")
                    for s in ((r.get("data") or {}).get("sectors") or []) if s.get("plate_type")=="INDUSTRY"]
            raw[sym] = inds
        else:
            raw[sym] = None
        if (i+1) % 50 == 0: log(f"  plate {i+1}/{len(codes)}")
        time.sleep(0.25)
    out = {}
    for code in codes:
        out[code] = {"plates": raw.get("US."+code) or [], "bucket": bucket(code, raw.get("US."+code))}
    json.dump(out, open(os.path.join(BASE,"Temp",f"plate_bucket_{DATE_YMD}.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    n_other = sum(1 for v in out.values() if v["bucket"]=="其他")
    log(f"板块归并完成，其他={n_other}")
    return out

def attach_bucket(results, pb):
    for x in results:
        p = pb.get(x["code"], {})
        x["bucket"] = p.get("bucket", "其他")
        x["plates"] = p.get("plates", [])
    return results

# ---------------- 6. 构建 + 日志 + git ----------------
def build_html(results_json, date_ymd):
    out_date = os.path.join(BASE,"reports",f"hot_rsi_eval_{date_ymd}.html")
    out_latest = os.path.join(BASE,"reports","hot_rsi_latest.html")
    for out in (out_date, out_latest):
        r = subprocess.run([PY, os.path.join(BASE,"Temp","build_rsi_eval.py"), results_json, out],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            log(f"build 失败: {r.stderr[-500:]}")
            return None
    log(f"HTML 已生成: hot_rsi_eval_{date_ymd}.html + hot_rsi_latest.html")
    return out_date

def git_commit(date_str):
    files = ["results/", "data/", "reports/", "Temp/", "scripts/"]
    subprocess.run(["git","-C",BASE,"add"] + files, capture_output=True)
    r = subprocess.run(["git","-C",BASE,"commit","-m",f"{date_str}  msg: 热门RSI日报"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0:
        log("git commit OK")
    elif "nothing to commit" in r.stdout or "nothing to commit" in r.stderr:
        log("git: 无变更可提交")
    else:
        log(f"git commit 警告: {(r.stderr or r.stdout)[-200:]}")

def main():
    t0 = time.time()
    global TOK
    TOK = get_token()
    if not TOK:
        write_log(False, "token 过期且 refresh 失败，需手动重授权")
        sys.exit(1)
    init_mcp()
    # 3. 拉榜
    items = fetch_hot_top500()
    if not items:
        # 兜底：直接读上次榜单（报告仍可出，标注陈旧）
        try:
            items = json.load(open(os.path.join(BASE,"Temp","hot500_raw.json"),encoding="utf-8"))[:500]
            log("screen 失败，使用上次榜单兜底")
        except Exception:
            write_log(False, "拉榜失败且无兜底数据")
            sys.exit(1)
    rows = build_rows_from_items(items)
    # 4. 过滤
    rows = filter_rules(rows)
    if len(rows) < 50:
        log("过滤后样本过少，终止"); write_log(False, f"过滤后仅{len(rows)}只"); sys.exit(1)
    json.dump(rows, open(os.path.join(BASE,"Temp",f"hot_filtered_{DATE_YMD}.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    # 5. RSI
    results, fails = batch_rsi(rows)
    if len(results) < 50:
        write_log(False, f"RSI 成功数过少 {len(results)}"); sys.exit(1)
    results_json = os.path.join(BASE,"results",f"rsi14_hot_{DATE_YMD}.json")
    json.dump(results, open(results_json,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(BASE,"data",f"rsi14_hot_{DATE_YMD}.csv"),"w",newline="",encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys())); w.writeheader(); w.writerows(results)
    log(f"结果已存: rsi14_hot_{DATE_YMD}.json/csv ({len(results)} 行)")
    # 6. 板块
    pb = fetch_plates([x["code"] for x in results])
    results = attach_bucket(results, pb)
    # 修复 bucket 后重写 json（供 build 用）
    json.dump(results, open(results_json,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    # 7. 构建
    html = build_html(results_json, DATE_YMD)
    if not html:
        write_log(False, "HTML 构建失败"); sys.exit(1)
    # 8. 日志 + git
    have = [x for x in results if x["rsi14"] is not None]
    med = sorted(v["rsi14"] for v in have)[len(have)//2] if have else None
    note = (f"n={len(results)} (fail {len(fails)}), 中位RSI={med}, "
            f"超卖<30:{sum(1 for v in have if v['rsi14']<30)}, 超买>=70:{sum(1 for v in have if v['rsi14']>=70)}, "
            f"耗时{(time.time()-t0)/60:.0f}min, 报告: reports/hot_rsi_eval_{DATE_YMD}.html")
    write_log(True, note)
    git_commit(DATE)
    log("ALL DONE " + note)

if __name__ == "__main__":
    main()
