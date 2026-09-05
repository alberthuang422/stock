# -*- coding: utf-8 -*-
import json, urllib.request

KEY = "ehGL5HsAui7weuiBEQFaY6"
title = "CFTC 农产品持仓｜截至 09-01"
body = """【谷物油籽：多头极端拥挤】
棉花 非商净多 13.31万 = 2010年来最高
豆粕 17.39万（99.8分位，距峰值仅 1,008张）
玉米 48.07万（97.2）大豆 24.91万（97.9）
豆油 94.4 分位｜油菜籽 96.9 分位
玉米 3周净多 18.3万→48.1万（增仓上行）

【小麦】6/30 −8.10万 → 7/21 翻多 → 9/1 +7.43万
本周单周 +5.01万，2026年内最高（3年分位100%）

【糖】7个月反转约45万张
−23.78万（2/17）→ +21.12万，3年分位97.5%

【畜牧乳品：历史级净空】
瘦肉猪 0.3分位（上周−4.05万为2010年来最空）
黄油 1.8｜脱脂奶粉 2.0｜奶酪 3年1.9
活牛 3年分位4.5%，本周减 1.19万

【逆势】可可空头回补 +7,113｜咖啡减多 −6,923

商业端对应大规模净空（玉米−42.9万、糖−27.1万、豆粕−20.2万、棉花−14.5万）→ 现货商高位套保
关键节点：9/11 USDA 作物产量报告 = 拥挤多头证伪点
明细：reports/72_CFTC农产品持仓_20260901/"""

data = json.dumps({"title": title, "body": body, "group": "COT"}).encode("utf-8")
req = urllib.request.Request(
    f"https://api.day.app/{KEY}", data=data,
    headers={"Content-Type": "application/json; charset=utf-8"})
print(urllib.request.urlopen(req, timeout=30).read().decode())
