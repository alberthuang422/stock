# -*- coding: utf-8 -*-
"""白糖可贸易国家分析（2000-2026）：产量/消费/出口/库存
数据源：data/sugar/raw/psd_alldata.csv（USDA FAS PSD，2026-09-11 快照）
输出：data/sugar/tradeable_countries.json
口径：属性码 28=产量 126=总消费(含151) 88=出口 57=进口 176=期末库存 20=期初库存
单位：千吨（原糖当量 raw value, unitId=8）
"""
import csv, json, os
csv.field_size_limit(10**9)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "sugar")
YEARS = list(range(2000, 2027))

# ---------- 1. 载入 ----------
data = {}
meta = {}
with open(os.path.join(DATA, "raw", "psd_alldata.csv"), encoding="utf-8", errors="replace") as f:
    r = csv.reader(f)
    next(r)
    for line in r:
        if line[0] == "0612000":
            cc, cn, my = line[2], line[3], int(line[4])
            data[(cc, my)] = {line[7].strip().lstrip("0") or "0": float(line[11])} \
                if (cc, my) not in data else data[(cc, my)] | {line[7].strip().lstrip("0") or "0": float(line[11])}
            meta[cc] = cn

def g(cc, y, attr):
    return data.get((cc, y), {}).get(attr, 0.0)

def series(cc, attr):
    return [g(cc, y, attr) for y in YEARS]

# ---------- 2. 主要可贸易国家（固定集合，按 2000-2026 平均净出口/净进口排序） ----------
EXPORTERS = ["BR", "TH", "AS", "IN", "GT", "MX", "SF", "CO", "WZ", "CU", "AR"]
EXPORTER_NAMES = {"BR": "巴西", "TH": "泰国", "AS": "澳大利亚", "IN": "印度", "GT": "危地马拉",
                  "MX": "墨西哥", "SF": "南非", "CO": "哥伦比亚",
                  "WZ": "斯威士兰", "CU": "古巴", "AR": "阿根廷"}
IMPORTERS = ["ID", "CH", "US", "E4", "MY", "KS", "BG", "RS", "AG", "NI", "SA", "JA"]
IMPORTER_NAMES = {"ID": "印尼", "CH": "中国", "US": "美国", "E4": "欧盟", "MY": "马来西亚",
                  "KS": "韩国", "BG": "孟加拉国", "RS": "俄罗斯", "AG": "阿尔及利亚",
                  "NI": "尼日利亚", "SA": "沙特阿拉伯", "JA": "日本"}

# ---------- 3. 恒等式校验（主要国家） ----------
id_fail = 0
for cc in EXPORTERS + IMPORTERS:
    for y in YEARS:
        d = data.get((cc, y), {})
        if not d:
            continue
        lhs = d.get("20", 0) + d.get("28", 0) + d.get("57", 0)
        s86 = d.get("86", 0)
        rhs = d.get("126", 0) + d.get("88", 0) + d.get("176", 0)
        s178 = d.get("178", 0)
        if abs(lhs - s86) > 5 or abs(rhs - s178) > 5 or abs(s86 - s178) > 5:
            id_fail += 1

# ---------- 4. 世界加总 ----------
world = {}
for y in YEARS:
    agg = {k: 0.0 for k in ["20", "28", "57", "88", "126", "176"]}
    for cc in meta:
        d = data.get((cc, y), {})
        if not d:
            continue
        for k in agg:
            agg[k] += d.get(k, 0)
    agg["stu"] = agg["176"] / agg["126"] * 100
    world[y] = agg

# ---------- 5. 分国序列 ----------
def cseries(cc):
    return {y: {k: g(cc, y, k) for k in ["20", "28", "57", "88", "126", "176"]} for y in YEARS}

out = {
    "meta": {
        "as_of": "2026-09-11 PSD 快照（本地 psd_alldata.csv）",
        "unit": "千吨，原糖当量（raw value）",
        "identity_fails": id_fail,
        "my_note": "MY2026=预测值；分国市场年窗口不同（巴西4-3月/中国印度10-9月/泰国12-11月）",
    },
    "years": YEARS,
    "world": {str(y): world[y] for y in YEARS},
    "exporters": {cc: cseries(cc) for cc in EXPORTERS},
    "importers": {cc: cseries(cc) for cc in IMPORTERS},
    "exporter_names": EXPORTER_NAMES,
    "importer_names": IMPORTER_NAMES,
}

# ---------- 6. 关键派生指标 ----------
# 6a. 出口集中度：前4出口国份额
exp4 = ["BR", "TH", "AS", "IN"]
concentration = []
for y in YEARS:
    we = world[y]["88"]
    top4 = sum(g(cc, y, "88") for cc in exp4)
    concentration.append(round(top4 / we * 100, 1))
out["top4_share"] = dict(zip(YEARS, concentration))

# 6a2. EU 拼接序列（E2=EU-15 1960-2003 / E3=EU-25 2004-2005 / E4=EU 2006-2026）
def eu(y):
    if y <= 2003:
        cc = "E2"
    elif y <= 2005:
        cc = "E3"
    else:
        cc = "E4"
    return {k: g(cc, y, k) for k in ["20", "28", "57", "88", "126", "176"]}
out["eu_joined"] = {str(y): eu(y) for y in YEARS}

# 6b. 传导率：产量上升年 Δ净出口/Δ产量（累计 2000→2026 与分段）
def trans_rate(cc, y0, y1):
    dnet = (g(cc, y1, "88") - g(cc, y1, "57")) - (g(cc, y0, "88") - g(cc, y0, "57"))
    dprod = g(cc, y1, "28") - g(cc, y0, "28")
    return dnet, dprod, (dnet / dprod if dprod else None)

tr = {}
for cc in ["BR", "TH", "IN", "AS"]:
    tr[cc] = {}
    for (a, b, lab) in [(2000, 2026, "2000-26"), (2000, 2010, "2000-10"), (2010, 2026, "2010-26"), (2019, 2026, "2019-26")]:
        dnet, dprod, rate = trans_rate(cc, a, b)
        tr[cc][lab] = {"dnet": round(dnet), "dprod": round(dprod),
                       "rate": round(rate * 100, 1) if rate is not None else None}
out["transmission"] = tr

# 6c. 弹性放大倍数（MY2026）：1 / (出口/产量)
amp = {}
for cc in ["BR", "TH", "IN", "AS"]:
    e, p = g(cc, 2026, "88"), g(cc, 2026, "28")
    amp[cc] = {"exp_share": round(e / p * 100, 1), "amplify": round(p / e, 1) if e else None}
out["amplify2026"] = amp

# 6d. 泰国异常：存/用（含出口用度）
th_std = {y: round(g("TH", y, "176") / (g("TH", y, "126") + g("TH", y, "88")) * 100, 1) for y in YEARS}
out["thai_std"] = th_std

# 6e. 库存份额（占世界期末库存）
stk_share = {}
for cc in EXPORTERS + IMPORTERS:
    stk_share[cc] = {y: round(g(cc, y, "176") / world[y]["176"] * 100, 1) for y in YEARS}
out["stock_share"] = stk_share

# 6f. 产量/消费/出口 增长分解 2000 vs 2026
growth = {}
for cc in ["BR", "TH", "AS", "IN", "GT", "MX", "CH", "ID", "US", "E4"]:
    growth[cc] = {
        "prod00": g(cc, 2000, "28"), "prod26": g(cc, 2026, "28"),
        "cons00": g(cc, 2000, "126"), "cons26": g(cc, 2026, "126"),
        "exp00": g(cc, 2000, "88"), "exp26": g(cc, 2026, "88"),
        "stk00": g(cc, 2000, "176"), "stk26": g(cc, 2026, "176"),
    }
out["growth"] = growth

with open(os.path.join(DATA, "tradeable_countries.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print("saved tradeable_countries.json")
print("identity fails:", id_fail)
print("top4 share 2000:", concentration[0], "-> 2026:", concentration[-1])
print("TH std 2000:", th_std[2000], "2019:", th_std[2019], "2026:", th_std[2026])
for cc in ["BR", "TH", "IN", "AS"]:
    print(cc, "transmission:", tr[cc]["2000-26"], "amplify:", amp[cc])
