# -*- coding: utf-8 -*-
"""RB(RBOB 汽油) 曲线/月差结构位移诊断 —— 今日实时 vs 上一交易日(9/11)

口径（与 CL/HO 月差研究一致的四口径）：
  ①绝对 $（cents→$/gal，1 手 = 42,000 gal）
  ②占近腿 %
  ③日归一化对数斜率 365/Δ天 × ln(P近/P远)  ← 唯一严格可跨段比较
  ④历史分位（129 日样本，测「最异常」非「最陡」）

输出：results/rb_curve_shift_<date>.json  + 控制台表格
前置：scripts/futu_token_refresh.py 刷新 token（2h 有效）
"""
import os
import sys
import json
import glob
import datetime as dt

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_cl_contracts_20260910 as F  # noqa: E402

BASE = os.path.dirname(HERE)
DAILY = os.path.join(BASE, "data", "rb_contracts", "daily")
INFO = os.path.join(BASE, "data", "rb_contracts", "contract_info.json")
RES = os.path.join(BASE, "results")

LEGS = ["US.RB2610", "US.RB2611", "US.RB2612"] + ["US.RB27{:02d}".format(m) for m in range(1, 11)]
LABEL = {s: s.split(".")[1][2:] for s in LEGS}          # 2610, 2611, ...
M1 = "2610"


def ltd_map():
    info = json.load(open(INFO, encoding="utf-8"))
    out = {}
    for it in info["future_info"]:
        ts = it.get("last_trade_time") or 0
        if ts:
            out[it["code"]] = dt.datetime.fromtimestamp(
                ts / 1000, dt.timezone(dt.timedelta(hours=-4))).date()
    return out


def live_quotes():
    F.init()
    rows = {}
    for i in range(0, len(LEGS), 5):
        r = F.rpc("tools/call", {"name": "quote_stock_quote",
                                 "arguments": {"code_list": LEGS[i:i + 5]}})
        for q in (r.get("data") or {}).get("quote_list", []):
            rows[q["code"]] = q
    snap = {}
    for code, q in rows.items():
        snap[code] = {
            "quote_time_et": dt.datetime.fromtimestamp(
                (q.get("data_time") or 0) / 1000,
                dt.timezone(dt.timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M")
            if q.get("data_time") else None,
            "last": q.get("last_price"),
            "prev_settle": q.get("prev_close_price"),
            "last_settle": ((q.get("future_ex_data") or {}).get("last_settle_price")),
            "oi": (q.get("future_ex_data") or {}).get("position"),
            "oi_chg": (q.get("future_ex_data") or {}).get("position_change"),
            "volume": q.get("volume"),
            "high": q.get("high_price"), "low": q.get("low_price"),
            "data_time": q.get("data_time"), "data_date": q.get("data_date"),
        }
    return snap


def load_daily():
    out = {}
    for f in glob.glob(os.path.join(DAILY, "*.csv")):
        sym = os.path.basename(f)[:-4]
        if sym not in LEGS:
            continue
        df = pd.read_csv(f)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        out[sym] = df.set_index("date")
    return out


def main():
    now_et = dt.datetime.now(dt.timezone(dt.timedelta(hours=-4)))
    today = now_et.date()
    daily = load_daily()
    ltd = ltd_map()
    live = live_quotes()

    # 交易日定位
    dates = sorted(set().union(*[set(d.index) for d in daily.values()]))
    prev = [d for d in dates if d < today][-1]           # 上一交易日 = 9/11
    print("now ET =", now_et.strftime("%Y-%m-%d %H:%M"), "| 上一交易日 =", prev)

    def px(sym, day, field):
        d = daily.get(sym)
        if d is None or day not in d.index:
            return None
        v = d.loc[day, field]
        return None if pd.isna(v) else float(v)

    rows = []
    for s in LEGS:
        q = live.get(s, {})
        rows.append({
            "code": s, "label": LABEL[s], "ltd": ltd.get(s),
            "close_prev": px(s, prev, "close"),
            "settle_prev": px(s, prev, "settle") or px(s, prev, "close"),
            "oi_prev": px(s, prev, "open_interest"),
            "vol_prev": px(s, prev, "volume"),
            "live": q.get("last"),
            "live_vol": q.get("volume"),
            "live_oi": q.get("oi"),
            "live_oi_chg": q.get("oi_chg"),
            "live_high": q.get("high"), "live_low": q.get("low"),
            "settle_now": q.get("last_settle"),
            "quote_time_et": q.get("quote_time_et"),
            "stale": (q.get("last") is not None and q.get("prev_close_price") is not None
                      and abs(q["last"] - q["prev_close_price"]) < 1e-9),
        })
    df = pd.DataFrame(rows)

    # 缺失兜底：实时缺失 → 用今日日线收盘（部分交易时段）
    for i, r in df.iterrows():
        if r["live"] is None:
            v = px(r["code"], today, "close")
            if v is not None:
                df.at[i, "live"] = v
                df.at[i, "live_src"] = "daily_close(partial)"

    df["d_settle"] = df["live"] - df["settle_prev"]
    df["d_close"] = df["live"] - df["close_prev"]

    def spreads(col):
        v = df[col].tolist()
        out = {}
        for k in range(len(v) - 1):
            out["{}-{}".format(df.label[k], df.label[k + 1])] = (
                None if (v[k] is None or v[k + 1] is None) else round(v[k] - v[k + 1], 4))
        return out

    sp_prev_c, sp_prev_s, sp_now = spreads("close_prev"), spreads("settle_prev"), spreads("live")

    # 日归一化对数斜率（相邻段）
    slopes = {}
    for k in range(len(LEGS) - 1):
        a, b = LEGS[k], LEGS[k + 1]
        key = "{}-{}".format(LABEL[a], LABEL[b])
        dd = (ltd[b] - ltd[a]).days
        rec = {"days": dd}
        for tag, col in (("prev", "settle_prev"), ("now", "live")):
            pn, pf = df.loc[df.code == a, col].iloc[0], df.loc[df.code == b, col].iloc[0]
            rec[tag] = None if (pn is None or pf is None or pf <= 0) else \
                round(365.0 / dd * 100 * abs(float(__import__("math").log(pn / pf))), 3)
        rec["chg"] = None if (rec["prev"] is None or rec["now"] is None) else \
            round(rec["now"] - rec["prev"], 3)
        slopes[key] = rec

    # 历史分位（用日线收盘构建的 +1 月差序列）
    hist = {}
    for k in range(len(LEGS) - 1):
        a, b = LEGS[k], LEGS[k + 1]
        if a not in daily or b not in daily:
            continue
        x = (daily[a]["close"] - daily[b]["close"]).dropna()
        key = "{}-{}".format(LABEL[a], LABEL[b])
        cur = sp_now[key]
        hist[key] = {"n": int(len(x)), "pct": None if cur is None else
                     round(float((x <= cur).mean() * 100), 1),
                     "max": round(float(x.max()), 4), "min": round(float(x.min()), 4),
                     "med": round(float(x.median()), 4)}

    print("\n=== RB 曲线（$/gal）：9/11 结算 → 今日实时 ===")
    print(df[["label", "ltd", "settle_prev", "close_prev", "live", "d_settle",
              "vol_prev", "live_vol", "live_oi", "live_oi_chg",
              "quote_time_et", "stale"]].to_string(index=False))

    print("\n=== +1 月差（$/gal）===")
    t = pd.DataFrame({"prev_settle": pd.Series(sp_prev_s), "prev_close": pd.Series(sp_prev_c),
                      "now": pd.Series(sp_now)})
    t["Δ(settle→now)"] = (t["now"] - t["prev_settle"]).round(4)
    t["Δ(close→now)"] = (t["now"] - t["prev_close"]).round(4)
    t["hist_pct"] = [hist.get(i, {}).get("pct") for i in t.index]
    t["days"] = [slopes[i]["days"] for i in t.index]
    t["slope_prev"] = [slopes[i]["prev"] for i in t.index]
    t["slope_now"] = [slopes[i]["now"] for i in t.index]
    print(t.to_string())

    groups = {
        "近段 M1-M2..M3-M4": ["2610-2611", "2611-2612", "2612-2701"],
        "中段 M4-M5..M9-M10": ["2701-2702", "2702-2703", "2703-2704",
                               "2704-2705", "2705-2706", "2706-2707"],
        "远段 M10-M11..M12-M13": ["2707-2708", "2708-2709", "2709-2710"],
    }
    print("\n=== 分段合计（缺腿则按现有段求和并标注 n）===")
    gsum = {}
    for g, ks in groups.items():
        ok = [k for k in ks if sp_prev_s.get(k) is not None and sp_now.get(k) is not None]
        p = sum(sp_prev_s[k] for k in ok)
        n = sum(sp_now[k] for k in ok)
        dp = n - p
        med = sorted((sp_now[k] - sp_prev_s[k]) for k in ok)
        gsum[g] = {"prev": round(p, 4), "now": round(n, 4), "chg": round(dp, 4),
                   "n_seg": len(ok), "n_all": len(ks),
                   "chg_median": round(med[len(med) // 2], 4) if med else None}
        print("  {:24s} n={}/{} prev={:7.4f}  now={:7.4f}  Δsum={:+7.4f}  Δ中位={:+7.4f}".format(
            g, len(ok), len(ks), p, n, dp, gsum[g]["chg_median"]))

    out = {
        "generated_et": now_et.strftime("%Y-%m-%d %H:%M:%S"),
        "prev_session": str(prev),
        "snapshot_note": "now = 富途实时 last_price（盘中）；prev = 该日日线 close/settle",
        "curve": df.astype(object).where(pd.notna(df), None).to_dict("records"),
        "spread_prev_settle": sp_prev_s, "spread_prev_close": sp_prev_c, "spread_now": sp_now,
        "slopes": slopes, "hist": hist, "groups": gsum,
    }
    os.makedirs(RES, exist_ok=True)
    fn = os.path.join(RES, "rb_curve_shift_{}.json".format(today.strftime("%Y%m%d")))
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print("\n-> ", fn)


if __name__ == "__main__":
    main()
