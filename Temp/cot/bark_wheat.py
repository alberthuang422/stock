# -*- coding: utf-8 -*-
import json, urllib.request

KEY = "ehGL5HsAui7weuiBEQFaY6"
title = "小麦 COT 增仓定位｜31.5年样本"
body = (
"【小麦三合约合计 · 2026-09-01 周】\n"
"单周多头 +36,782 = 1995 年以来全样本(1641周)第 5 大，99.8 分位\n"
"· OI 归一化 +3.97% = 99.1 分位（历史中位仅 +0.04%）→ 非市场膨胀假象\n"
"· 净头寸单周 +50,125 = 99.0 分位\n"
"\n"
"排在前面的只有：1996-01-30 +69,306、1997-09-02 +41,827、1995-04~05 两次 +3.8万（均为 1995-97 大牛市）、2004-03-23 +30,637\n"
"→ 2026-09-01 是 1997 年以来 9 月初窗口(109周)第 2 大增仓，非季节性常规\n"
"\n"
"【速度极端、存量不极端】\n"
"· 4周累计多头 +53,160 = 99.1 分位\n"
"· 8/11→9/1 净头寸 −7,703 → +74,288（三周拉回 8.2 万张）\n"
"· 当前净 +74,288 绝对分位仅 85.4%；净/OI 7.3% = 74.9 分位\n"
"· 2026 年 1/20 曾净空 −119,818 → 8 个月摆动 19.4 万张\n"
"\n"
"数据边界：futures-only（现报告口径）官方历史 1995-03-21 起 1,642 周；期货+期权合并口径可回溯 1986 年起"
)
data = json.dumps({"title": title, "body": body, "group": "COT"}).encode("utf-8")
req = urllib.request.Request(
    f"https://api.day.app/{KEY}", data=data,
    headers={"Content-Type": "application/json; charset=utf-8"})
print(urllib.request.urlopen(req, timeout=30).read().decode())
