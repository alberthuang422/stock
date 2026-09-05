# -*- coding: utf-8 -*-
import json, urllib.request

KEY = "ehGL5HsAui7weuiBEQFaY6"
title = "小麦驱动归因报告（75号）已出"
body = (
"【75号报告：张靠故事，见顶=故事被终结】\n"
"① 供给脉冲型(天气/战争)8次：6/8 ≤2周即顶，中位0.4周\n"
"   ——被USDA数据证伪/他产区替代/计价出尽终结，保质期≤1作物季\n"
"② 需求/库存周期型(中国采购+俄出口税+去库)8次：0/8即顶\n"
"   ——中位44周、到顶+26%，2020-21牛市清一色，利多不断档\n"
"③ 牛市内供给叠加：3次全续涨，接力才是关键\n"
"\n"
"【四种终结武器】官方数据证伪(2015/16/17/24)\n"
"替代供给(2012/18/24俄对冲)、价格挤出需求(2017埃及弃美)、\n"
"利多出尽(2022战争+52.5%后1.8周见顶)\n"
"\n"
"【牛市11事件=台阶非独立顶】\n"
"2020-10→2021-05→2021-11→2022-03-07战争顶$12.94\n"
"四股驱动不断档(中国采购+俄税+去库+北美旱)\n"
"\n"
"【2026-09-01定位】黑海断供属①但含②(俄出口约束)成分\n"
"9/11 USDA+俄出口船期+停火 = 三个观察点"
)
data = json.dumps({"title": title, "body": body, "group": "COT"}).encode("utf-8")
req = urllib.request.Request(
    f"https://api.day.app/{KEY}", data=data,
    headers={"Content-Type": "application/json; charset=utf-8"})
print(urllib.request.urlopen(req, timeout=30).read().decode())