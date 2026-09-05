# -*- coding: utf-8 -*-
import json, urllib.request

KEY = "ehGL5HsAui7weuiBEQFaY6"
title = "小麦极端增仓→见顶回测（2011后20事件）"
body = (
"【历史规律：单周多头暴增 ≥1.5万张后】\n"
"① 35% 事件 1-2 周内就是顶：\n"
"   2012-07 干旱顶(+7.4%)、2015/16/17/18 反弹顶、2022-02 俄乌战争 1.8周打满+52.5%后见顶\n"
"② 65% 事件续涨 7-10 个月：\n"
"   见顶中位 41周(9.5月)、事件日→顶中位 +29%（2020-21 牛市最高 +78%）\n"
"③ 无论哪类：事件后4周 84% 概率回吐\n"
"   中位 -4.8%（对照全体周 -0.4%）→ 单周暴增当周别追\n"
"\n"
"【2026-09-01 推演(+36,782=2011后最大)】\n"
"· 若 9/11 USDA 证伪/停火利空 → 1-2 周内见顶\n"
"· 若供给冲击延续 → 顶在 2027 年 3-6 月，或还有 +29~50%\n"
"· 分型信号：事件后 4-8 周是否创新高\n"
"(历史项：2022 战争顶=CBOT $12.94 天价)"
)
data = json.dumps({"title": title, "body": body, "group": "COT"}).encode("utf-8")
req = urllib.request.Request(
    f"https://api.day.app/{KEY}", data=data,
    headers={"Content-Type": "application/json; charset=utf-8"})
print(urllib.request.urlopen(req, timeout=30).read().decode())
