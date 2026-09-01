# -*- coding: utf-8 -*-
"""富途行业板块 → 粗粒度桶 归并；加密关联/航天叙事单列。输出 code->{plates,bucket}"""
import json, collections

BASE = r"C:\Users\Administrator\Desktop\stock"
raw = json.load(open(BASE + r"\Temp\plate_354_raw.json", encoding="utf-8"))
hot = json.load(open(BASE + r"\Temp\hot_filtered.json", encoding="utf-8"))  # [rank, orig, code, name, ...]

# 加密关联（币价代理/矿/交易所，官方板块失真 → 单列）
CRYPTO = {"MSTR","COIN","CRCL","BMNR","PURR","ASST","BTDR","MARA","STRC","WULF",
          "RIOT","CIFR","QNT","BTCT","CLSK","BLSH","NCT","HUT","GEMI","SBET"}
# 商业航天/太空（官方多归航空航天或工业，叙事独立 → 单列）
SPACE = {"RKLB","ASTS","LUNR","RDW","SPCE","ACHR","JOBY","ONDS","RCAT","U"}

RULES = [  # (粗桶, [官方板块名子串]) 顺序匹配
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

# 接口未返回板块的 25 只 → 手工补（按富途行业口径常识归类）
MANUAL = {
    "US.ONDS":"军工/航天","US.UNH":"医药/生物","US.ADBE":"软件/SaaS","US.PYPL":"金融",
    "US.AIM":"医药/生物","US.CEG":"公用/电力","US.NEM":"材料","US.RBRK":"软件/SaaS",
    "US.JNJ":"医药/生物","US.TWLO":"软件/SaaS","US.SOUN":"软件/SaaS","US.NEE":"公用/电力",
    "US.ATI":"材料","US.NEOV":"工业/机械/运输","US.WTI":"能源","US.AMGN":"医药/生物",
    "US.SNAP":"互联网/电商","US.DKNG":"可选消费","US.CELH":"可选消费","US.CRS":"材料",
    "US.SQM":"材料","US.HD":"可选消费","US.BMY":"医药/生物","US.WYFI":"其他","US.FTAI":"工业/机械/运输",
}

# 接口无板块返回的知名大票 → 直接归类（Futu 行业口径常识）
KNOWN = {
    "NVDA":"半导体/AI硬件","INTC":"半导体/AI硬件","AVGO":"半导体/AI硬件","GOOGL":"互联网/电商",
    "BE":"工业/机械/运输","CRWD":"软件/SaaS","NOW":"软件/SaaS","AAOI":"半导体/AI硬件","CRM":"软件/SaaS",
    "ORCL":"软件/SaaS","GPRO":"可选消费","AXTI":"半导体/AI硬件","CRWV":"软件/SaaS","APP":"互联网/电商",
    "PANW":"软件/SaaS","TTWO":"互联网/电商","CRDO":"半导体/AI硬件","VRT":"工业/机械/运输",
    "HIMS":"医药/生物","NET":"软件/SaaS","RDDT":"互联网/电商","PFE":"医药/生物","V":"金融",
    "OKTA":"软件/SaaS","MRK":"医药/生物","HPE":"半导体/AI硬件","ISRG":"医药/生物","ALAB":"半导体/AI硬件",
    "SMR":"公用/电力","MDB":"软件/SaaS","AAL":"工业/机械/运输","CIEN":"通信","SNPS":"软件/SaaS",
    "FTNT":"软件/SaaS","INTU":"软件/SaaS","DDOG":"软件/SaaS","ETN":"工业/机械/运输","ZETA":"软件/SaaS",
    "VSH":"半导体/AI硬件","CVKD":"医药/生物","MO":"必选消费","QBTS":"半导体/AI硬件","KEEL":"工业/机械/运输",
    "AON":"金融","BG":"必选消费","NTAP":"半导体/AI硬件","ZS":"软件/SaaS","NVAX":"医药/生物",
    "BTAI":"医药/生物","ALM":"金融","AI":"软件/SaaS","DKS":"可选消费","M":"可选消费","EBAY":"互联网/电商",
    "SLS":"医药/生物","CTVA":"必选消费","CDNS":"软件/SaaS","NVT":"工业/机械/运输","FSLY":"软件/SaaS",
    "VELO":"其他","COKE":"必选消费","FPS":"其他","LVMUY":"可选消费","HYLN":"工业/机械/运输",
    "FLNC":"工业/机械/运输","HON":"工业/机械/运输","FUBO":"互联网/电商","MAR":"可选消费","INFQ":"软件/SaaS",
    "COSM":"其他","AUR":"其他","RDAC":"其他","ADI":"半导体/AI硬件","UPS":"工业/机械/运输",
    "AMSC":"工业/机械/运输","WYFI":"其他","ZDGE":"互联网/电商","KHC":"必选消费","LEN":"可选消费",
    "HE":"公用/电力","LPTH":"半导体/AI硬件","YMM":"其他","RSG":"工业/机械/运输","BZAI":"医药/生物",
    "DVLT":"其他","MBGYY":"可选消费","IFNNY":"半导体/AI硬件","A":"医药/生物","GH":"医药/生物",
    "MGM":"可选消费","SN":"可选消费","UUUU":"能源","LEU":"能源","AA":"材料","TTMI":"半导体/AI硬件",
    "OUST":"半导体/AI硬件","DAL":"工业/机械/运输","UAL":"工业/机械/运输",
}

def bucket(code, plates):
    if code in CRYPTO: return "加密关联"
    if code in SPACE:  return "航天/太空"
    if "US."+code in MANUAL: return MANUAL["US."+code]
    if code in KNOWN: return KNOWN[code]
    if not plates: return "其他"
    joined = "|".join(plates)
    for b, kws in RULES:
        for kw in kws:
            if kw in joined: return b
    return "其他"

out = {}
for r in hot:
    code = r[2]
    plates = raw.get("US." + code)
    out[code] = {"plates": plates or [], "bucket": bucket(code, plates)}

cnt = collections.Counter(v["bucket"] for v in out.values())
for b, n in cnt.most_common(): print(f"{n:4d}  {b}")
others = [(c, out[c]["plates"]) for c in out if out[c]["bucket"]=="其他"]
print("---- 其他:", others)
nop = [c for c in out if not out[c]["plates"]]
print("---- 无板块数据:", nop)
json.dump(out, open(BASE + r"\Temp\plate_bucket.json", "w", encoding="utf-8"), ensure_ascii=False)
print("saved plate_bucket.json")
