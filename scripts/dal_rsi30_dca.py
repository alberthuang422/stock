# -*- coding: utf-8 -*-
"""
DAL RSI<30 超卖期定投回测 2026-09-02（复刻 56 号 CCL 口径）
规则: RSI(14, Wilder) 跌破 30 当日起, 每个交易日收盘投入等额 $1; RSI 回升至 >=30 停止。
结算:
  A 主口径: 周期末日(最后一个 RSI<30 日)收盘结算
  B 延展:   周期末日 + T+5/10/20 交易日结算
对照:
  - 首日一把梭: 周期首日一次买入等额成本(金额=周期天数), 同结算日结算
  - SPY 同期: 同一周期对 SPY 做同样定投
输出 results/dal_rsi30_dca.json
"""
import csv, json, os, statistics as st
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")


def load(name):
    d = os.path.join(DATA, name)
    fn = [f for f in os.listdir(d) if "1D" in f and not f.startswith("BATS_")][0]
    px = {}
    with open(os.path.join(d, fn)) as f:
        for row in csv.DictReader(f):
            dt = row["date"].split(" ")[0]
            v = row["adj_close"] if row["adj_close"] else row["close"]
            if v:
                px[dt] = float(v)
    return px


dal, spy = load("dal"), load("spy")
dates = sorted(set(dal) & set(spy))
px = [dal[d] for d in dates]
sp = [spy[d] for d in dates]
n = len(dates)

alpha = 1 / 14
ag = al = 0.0
rsi = [None] * n
for i in range(1, n):
    dd = px[i] - px[i - 1]
    g = dd if dd > 0 else 0.0
    l = -dd if dd < 0 else 0.0
    ag += alpha * (g - ag)
    al += alpha * (l - al)
    rsi[i] = 100 - 100 / (1 + (ag / al if al > 0 else float("inf")))


def stage_of(d):
    if d < "2020-02-20":
        return "疫情前"
    if d <= "2022-12-31":
        return "疫情~2022"
    return "本轮牛市"


# ---------- 超卖周期: RSI<30 连续区段 ----------
periods = []
i = 1
while i < n:
    if rsi[i] is not None and rsi[i] < 30:
        start = i
        while i < n and rsi[i] is not None and rsi[i] < 30:
            i += 1
        periods.append((start, i - 1))  # [start, end] 均为 RSI<30 日
    else:
        i += 1

# ---------- 每个周期的定投结算 ----------
rows = []
for start, end in periods:
    if end + 20 >= n:  # 需要 T+20 完整样本
        continue
    L = end - start + 1  # 定投次数
    shares = sum(1.0 / px[j] for j in range(start, end + 1))
    cost = L
    mkt_end = shares * px[end]
    ret_end = mkt_end / cost - 1
    ext = {}
    for NN in (5, 10, 20):
        j = end + NN
        mkt = shares * px[j]
        ext[f"ret_t{NN}"] = mkt / cost - 1
    lump_end = px[end] / px[start] - 1
    s_shares = sum(1.0 / sp[j] for j in range(start, end + 1))
    s_ret_end = (s_shares * sp[end]) / cost - 1
    s_ret_t20 = (s_shares * sp[end + 20]) / cost - 1
    s_lump_end = sp[end] / sp[start] - 1

    rows.append({
        "start": dates[start], "end": dates[end], "len": L,
        "rsi_start": round(rsi[start], 1), "rsi_end": round(rsi[end], 1),
        "px_start": round(px[start], 2), "px_end": round(px[end], 2),
        "dd60_start": round((px[start] / max(px[max(0, start - 59):start + 1]) - 1) * 100, 1),
        "ret_end": round(ret_end * 100, 2),
        "ret_t5": round(ext["ret_t5"] * 100, 2),
        "ret_t10": round(ext["ret_t10"] * 100, 2),
        "ret_t20": round(ext["ret_t20"] * 100, 2),
        "lump_end": round(lump_end * 100, 2),
        "lump_t20": round(px[end + 20] / px[start] - 1, 4) * 100,
        "spy_ret_end": round(s_ret_end * 100, 2),
        "spy_ret_t20": round(s_ret_t20 * 100, 2),
        "spy_lump_end": round(s_lump_end * 100, 2),
        "ex_end": round(ret_end * 100 - s_ret_end * 100, 2),
        "ex_t20": round(ext["ret_t20"] * 100 - s_ret_t20 * 100, 2),
        "stage": stage_of(dates[start]),
    })


def agg(key, rows):
    xs = [r[key] for r in rows if r[key] is not None]
    if not xs:
        return None
    return {"n": len(xs), "mean": round(st.mean(xs), 2), "median": round(st.median(xs), 2),
            "min": round(min(xs), 2), "max": round(max(xs), 2),
            "win": round(100 * sum(1 for x in xs if x > 0) / len(xs), 1)}


out = {
    "meta": {"ticker": "DAL", "rule": "RSI14<30 期间每日收盘等额定投 $1, RSI>=30 停止; 周期=[首次<30, 末日<30]",
             "settle": "A=周期末日收盘; B=末日+T5/10/20; 对照: 首日一把梭同成本 / SPY 同期定投"},
    "n_periods": len(rows),
    "len_dist": dict(sorted(Counter(r["len"] for r in rows).items())),
    "agg": {
        "ret_end": agg("ret_end", rows),
        "ret_t5": agg("ret_t5", rows),
        "ret_t10": agg("ret_t10", rows),
        "ret_t20": agg("ret_t20", rows),
        "lump_end": agg("lump_end", rows),
        "lump_t20": agg("lump_t20", rows),
        "spy_ret_end": agg("spy_ret_end", rows),
        "spy_ret_t20": agg("spy_ret_t20", rows),
        "ex_end": agg("ex_end", rows),
        "ex_t20": agg("ex_t20", rows),
        "spy_lump_end": agg("spy_lump_end", rows),
    },
    "by_stage": {s: {"ret_end": agg("ret_end", [r for r in rows if r["stage"] == s]),
                     "ret_t20": agg("ret_t20", [r for r in rows if r["stage"] == s]),
                     "ex_end": agg("ex_end", [r for r in rows if r["stage"] == s]),
                     "ex_t20": agg("ex_t20", [r for r in rows if r["stage"] == s]),
                     "n": sum(1 for r in rows if r["stage"] == s)}
                 for s in ["疫情前", "疫情~2022", "本轮牛市"]},
    "by_len": {k: {"ret_end": agg("ret_end", [r for r in rows if r["len"] == k]),
                   "ret_t20": agg("ret_t20", [r for r in rows if r["len"] == k]),
                   "n": sum(1 for r in rows if r["len"] == k)}
               for k in sorted(set(r["len"] for r in rows))},
    "events": rows,
}
out_path = os.path.join(OUT, "dal_rsi30_dca.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"DAL 超卖周期数: {len(rows)}  长度分布: {out['len_dist']}")
a = out["agg"]
print("\n[主口径 A: 周期末日结算]")
print("定投:   n=%d  中位=%+.2f%%  均值=%+.2f%%  胜率=%.1f%%  min=%+.1f%% max=%+.1f%%" % (
    a["ret_end"]["n"], a["ret_end"]["median"], a["ret_end"]["mean"], a["ret_end"]["win"], a["ret_end"]["min"], a["ret_end"]["max"]))
print("一把梭: 中位=%+.2f%%  均值=%+.2f%%  胜率=%.1f%%" % (
    a["lump_end"]["median"], a["lump_end"]["mean"], a["lump_end"]["win"]))
print("SPY定投:中位=%+.2f%%  均值=%+.2f%%  胜率=%.1f%%" % (
    a["spy_ret_end"]["median"], a["spy_ret_end"]["mean"], a["spy_ret_end"]["win"]))
print("超额vs: 中位=%+.2fpp 均值=%+.2fpp" % (a["ex_end"]["median"], a["ex_end"]["mean"]))
print("\n[延展 B: 末日+T20 结算]")
print("定投:   中位=%+.2f%%  均值=%+.2f%%  胜率=%.1f%%" % (
    a["ret_t20"]["median"], a["ret_t20"]["mean"], a["ret_t20"]["win"]))
print("一把梭: 中位=%+.2f%%  均值=%+.2f%%  胜率=%.1f%%" % (
    a["lump_t20"]["median"], a["lump_t20"]["mean"], a["lump_t20"]["win"]))
print("SPY定投:中位=%+.2f%%  均值=%+.2f%%  胜率=%.1f%%" % (
    a["spy_ret_t20"]["median"], a["spy_ret_t20"]["mean"], a["spy_ret_t20"]["win"]))
print("超额vs: 中位=%+.2fpp 均值=%+.2fpp" % (a["ex_t20"]["median"], a["ex_t20"]["mean"]))
print("\n[分阶段 末日结算]")
for s in ["疫情前", "疫情~2022", "本轮牛市"]:
    b = out["by_stage"][s]
    if b["n"]:
        print("  %-8s n=%2d 中位=%+.2f%% 胜率=%.1f%% 超额中=%+.2fpp (T20: %+.2f%%/超额%+.2fpp)" % (
            s, b["n"], b["ret_end"]["median"], b["ret_end"]["win"], b["ex_end"]["median"],
            b["ret_t20"]["median"], b["ex_t20"]["median"]))
print("\n[长度分层 末日结算]")
for k in sorted(out["by_len"]):
    b = out["by_len"][k]
    print("  长度%2d天: n=%2d 中位=%+.2f%% 胜率=%.1f%% (T20中位 %+.2f%%)" % (
        k, b["n"], b["ret_end"]["median"], b["ret_end"]["win"], b["ret_t20"]["median"]))
print("\nwritten:", out_path)
