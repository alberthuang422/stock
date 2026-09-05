# -*- coding: utf-8 -*-
"""补推 2026-09-04 晚间两条未推送要点：①富途盘前历史数据能力 ②8月非农"""
import json, urllib.request, time

KEY = "ehGL5HsAui7weuiBEQFaY6"

MSGS = [
    {
        "title": "补推·8月非农（9/4 发布）",
        "body": """新增就业 16.2 万（预期 5.5 万）
4σ 全年最大超预期、年内第二大单月增幅
失业率 4.1% 持平；6/7 月合计上修 5.5 万

市场反应：美元走高、金跌约 $80
10Y +3bp 至 4.792%
9/16 FOMC 加息押注升温
（沃勒鸽派讲话后回落约 50%）

结论：衰退证伪 → 交易主线转为紧缩预期
下周 CPI = 9/16 利率决议的关键输入
（数据来源：项目 9/4 工作记录）"""
    },
    {
        "title": "补推·富途盘前历史数据能力",
        "body": """【结论】富途 MCP 无完整历史盘前分钟线
近期日期的盘前历史 = 仅 1 根开盘竞价 bar
（16:00 BJ = 04:00 ET），无连续分时

【正确用法】
实时盘前：quote_market_snapshot
 + quote_rt_data
历史指定日：quote_history_kline
 extended_time=2 + start=D, end=D+1
 ⚠ end=D 或 start=end=D 会退化成 1 根日线 bar

【踩坑】
-32603 全接口报错 = access token 过期
 → refresh_token 静默续期，expires_in=7200
 勿先怀疑限流
服务器偶发缺 OHLC 占位 bar → 需过滤
time_key = 北京时间毫秒；num 上限 370

交付脚本：Temp/futu_premarket_hist.py"""
    },
]


def push(m):
    data = json.dumps({"title": m["title"], "body": m["body"], "group": "补推"}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.day.app/{KEY}", data=data,
        headers={"Content-Type": "application/json; charset=utf-8"})
    return urllib.request.urlopen(req, timeout=30).read().decode()


for m in MSGS:
    print(m["title"], "->", push(m))
    time.sleep(1)
