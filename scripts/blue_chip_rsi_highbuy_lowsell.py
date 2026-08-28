# -*- coding: utf-8 -*-
"""
蓝筹股池 RSI 高买低卖 全历史回测（镜像 MCD 越跌越买 的反向结构）
用户澄清方向：1) RSI 高位时买入（追高） 2) RSI 低位时卖出（割在低位）

事件定义（与 mcd_rsi_band_dip.py 结构对称，方向相反）：
  A) 高买事件 = RSI 从低位档升入更高档首日 → 当日收盘买入
     档位: [60,65) / [65,70) / >=70   （60/65/70 三道上行门槛，越涨越追）
  B) 低卖事件 = RSI 从高位档跌入更低档首日 → 当日收盘卖出
     档位: [35,40) / [30,35) / <30    （40/35/30 三道下行门槛，越跌越卖）
  C) 配对循环 = 高买(上穿阈值首日)买入 → 低卖(下穿阈值首日)卖出 重复；未平仓计入 open
每个事件独立统计 T+5/T+10/T+20 的 maxG / ER / fwd，SPY 同窗口对照（超额=事件 fwd - SPY fwd）。
主口径无 cd10 去重（连续追高为设计意图）；另附 cd10 对照（间隔>=10交易日取首）。
输出 results/blue_chip_rsi_highbuy_lowsell.json
"""
import pandas as pd
import numpy as np
import json, os, glob, csv
from collections import Counter
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

tickers, sectors = [], {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t)
        sectors[t] = row["sector"].strip()

SECTOR_CN = {
    "Technology": "科技", "Financials": "金融", "Industrials": "工业",
    "Healthcare": "医疗", "Consumer": "消费", "Materials_Utilities_Other": "材料/公用/其他",
}
WINS = (5, 10, 20)

def load_stock(name):
    d = os.path.join(DATA, name.lower())
    if not os.path.isdir(d):
        return None
    cands = [p for p in glob.glob(os.path.join(d, "*.csv"))
             if not os.path.basename(p).startswith("BATS_") and "1D" in os.path.basename(p)]
    if not cands:
        return None
    f = sorted(cands)[0]
    df = pd.read_csv(f, parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    df = df[["date", col]].rename(columns={col: "px"})
    df = df.dropna(subset=["px"]).sort_values("date").reset_index(drop=True)
    return df

def rsi_wilder(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = ag / al
    return pd.Series(100 - 100 / (1 + rs), index=close.index)

spy = load_stock("SPY").rename(columns={"px": "spy"})

def wfeat(px_arr, t, N):
    seg = px_arr[t + 1:t + 1 + N]
    if len(seg) < N:
        return None
    maxg = max(seg) / px_arr[t] - 1
    fwd = seg[-1] / px_arr[t] - 1
    path = sum(abs(px_arr[j] - px_arr[j - 1]) for j in range(t + 1, t + 1 + N))
    er = abs(seg[-1] - px_arr[t]) / path if path > 0 else None
    return {"maxg": maxg, "fwd": fwd, "er": er}

def agg(rows, key):
    xs = [r[key] for r in rows if r[key] is not None]
    if not xs:
        return None
    return {"n": len(xs), "mean": round(st.mean(xs), 3), "median": round(st.median(xs), 3)}

def stat_block(rows):
    out = {}
    for NN in WINS:
        out[f"maxg{NN}"] = agg(rows, f"maxg{NN}")
        out[f"fwd{NN}"] = agg(rows, f"fwd{NN}")
        out[f"er{NN}"] = agg(rows, f"er{NN}")
        non = [r for r in rows if r[f"fwd{NN}"] is not None]
        out[f"win{NN}"] = round(100 * sum(1 for r in non if r[f"fwd{NN}"] > 0) / len(non), 1) if non else None
    ex = [r["ex"] for r in rows if r["ex"] is not None]
    out["ex20"] = {"n": len(ex), "mean": round(st.mean(ex), 2), "median": round(st.median(ex), 2)} if ex else {"n": 0}
    ep = [r for r in rows if r["maxg20"] is not None and r["maxg20"] > 0]
    out["ever_positive"] = round(100 * len(ep) / sum(1 for r in rows if r["maxg20"] is not None), 1) if sum(1 for r in rows if r["maxg20"] is not None) else None
    return out

def cd10_filter(ev):
    """每票内按 i 间隔 >=10 取首"""
    keep = []
    for t, g in ev.groupby("ticker"):
        g = g.sort_values("i")
        last = -10 ** 9
        for _, row in g.iterrows():
            if row["i"] - last >= 10:
                keep.append(row)
                last = row["i"]
    return pd.DataFrame(keep)

def stage_of(d):
    if d < "2020-02-20":
        return "疫情前"
    if d <= "2022-12-31":
        return "疫情~2022"
    return "本轮牛市"

def band_high(r):
    if r >= 70: return 3
    if r >= 65: return 2
    if r >= 60: return 1
    return 0

def band_low(r):
    if r < 30: return 3
    if r < 35: return 2
    if r < 40: return 1
    return 0

H_BAND = {3: ">=70", 2: "65-70", 1: "60-65"}
L_BAND = {3: "<30", 2: "30-35", 1: "35-40"}
H_ORDER = [">=70", "65-70", "60-65"]
L_ORDER = ["<30", "30-35", "35-40"]

# ---------- 逐票计算 ----------
high_events, low_events, base_rows = [], [], []
pair_all, pair_open = [], []
n_loaded = 0
spy_dates = set(spy["date"])

for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 300:
        continue
    n_loaded += 1
    df = df.merge(spy[["date", "spy"]], on="date", how="left").sort_values("date").reset_index(drop=True)
    df["rsi"] = rsi_wilder(df["px"])
    n = len(df)
    px = df["px"].values
    sp = df["spy"].values

    # A) 高买事件：RSI 升入更高档首日
    hb = [0] * n
    for i in range(n):
        r = df["rsi"].iloc[i]
        hb[i] = band_high(r if not pd.isna(r) else 0)
    for i in range(1, n - 20):
        if hb[i] >= 1 and hb[i] > hb[i - 1]:
            feats = {"i": i, "ticker": t, "sector": sectors[t],
                     "date": str(df["date"].iloc[i].date()), "band": H_BAND[hb[i]],
                     "rsi": round(float(df["rsi"].iloc[i]), 1), "px": round(float(px[i]), 2)}
            ok = True
            for NN in WINS:
                w = wfeat(px, i, NN)
                if w is None:
                    ok = False; break
                feats[f"maxg{NN}"] = round(w["maxg"] * 100, 2)
                feats[f"fwd{NN}"] = round(w["fwd"] * 100, 2)
                feats[f"er{NN}"] = round(w["er"], 3) if w["er"] is not None else None
            if ok:
                feats["sfwd20"] = None
                high_events.append(feats)

    # B) 低卖事件：RSI 跌入更低档首日
    lb = [0] * n
    for i in range(n):
        r = df["rsi"].iloc[i]
        lb[i] = band_low(r if not pd.isna(r) else 0)
    for i in range(1, n - 20):
        if lb[i] >= 1 and lb[i] > lb[i - 1]:
            feats = {"i": i, "ticker": t, "sector": sectors[t],
                     "date": str(df["date"].iloc[i].date()), "band": L_BAND[lb[i]],
                     "rsi": round(float(df["rsi"].iloc[i]), 1), "px": round(float(px[i]), 2)}
            ok = True
            for NN in WINS:
                w = wfeat(px, i, NN)
                if w is None:
                    ok = False; break
                feats[f"maxg{NN}"] = round(w["maxg"] * 100, 2)
                feats[f"fwd{NN}"] = round(w["fwd"] * 100, 2)
                feats[f"er{NN}"] = round(w["er"], 3) if w["er"] is not None else None
            if ok:
                feats["sfwd20"] = None
                low_events.append(feats)

    # C) 配对循环：上穿65买入 → 下穿35卖出（主）+ 上穿70/下穿30（严格对照）
    rsi_arr = df["rsi"].values
    for hth, lth, tag in [(65, 35, "H65_L35"), (70, 30, "H70_L30")]:
        i = 0
        while i < n:
            if not pd.isna(rsi_arr[i]) and rsi_arr[i] >= hth and (i == 0 or pd.isna(rsi_arr[i - 1]) or rsi_arr[i - 1] < hth):
                buy_i = i
                sell_i = None
                for j in range(i + 1, n):
                    if not pd.isna(rsi_arr[j]) and rsi_arr[j] < lth and (j == 0 or pd.isna(rsi_arr[j - 1]) or rsi_arr[j - 1] >= lth):
                        sell_i = j
                        break
                if sell_i is not None:
                    ret = (px[sell_i] / px[buy_i] - 1) * 100
                    pair_all.append({"ticker": t, "tag": tag,
                                     "buy": str(df["date"].iloc[buy_i].date()),
                                     "sell": str(df["date"].iloc[sell_i].date()),
                                     "hold": sell_i - buy_i, "ret": round(float(ret), 2)})
                    i = sell_i + 1
                else:
                    ret = (px[n - 1] / px[buy_i] - 1) * 100
                    pair_open.append({"ticker": t, "tag": tag,
                                      "buy": str(df["date"].iloc[buy_i].date()),
                                      "hold": n - 1 - buy_i, "ret": round(float(ret), 2)})
                    i = n
            else:
                i += 1

# ---------- 一次补充：给 high_events/low_events 填 sfwd20（SPY fwd20） ----------
spy_idx = {d: k for k, d in enumerate(spy["date"].values)}
for e in high_events:
    sname = e["date"] + "T"
    pass
# 用另一路：预建 date→spy_fwd20 map
spy_fwd20_map = {}
spy_dates_list = spy["date"].values
spy_px = spy["spy"].values
m = len(spy_dates_list)
for i in range(m - 20):
    spy_fwd20_map[spy_dates_list[i]] = (spy_px[i + 20] / spy_px[i] - 1) * 100

for e in high_events + low_events:
    sd = spy_fwd20_map.get(np.datetime64(e["date"]))
    if sd is not None and e["fwd20"] is not None:
        e["ex"] = round(e["fwd20"] - sd, 2)
    else:
        e["ex"] = None

# ---------- 聚合 ----------
high_ev = pd.DataFrame(high_events)
low_ev = pd.DataFrame(low_events)
high_cd10 = cd10_filter(high_ev)
low_cd10 = cd10_filter(low_ev)

def by_band(df, band_map, order):
    if len(df) == 0:
        return {b: stat_block([]) for b in order}
    return {b: stat_block(df[df["band"] == b].to_dict("records")) for b in order}

def stage_band(df, band_map, order):
    out = {}
    for stg in ["疫情前", "疫情~2022", "本轮牛市"]:
        sub = [r for r in df.to_dict("records") if stage_of(r["date"]) == stg]
        out[stg] = {b: stat_block([r for r in sub if r["band"] == b]) for b in order}
    return out

# 基率：全部股票所有重叠 20 日窗口
base_rows = []
prev = set()
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 300:
        continue
    px = df["px"].values
    for i in range(1, len(px) - 20):
        w = wfeat(px, i, 20)
        if w:
            base_rows.append({"maxg": round(w["maxg"] * 100, 2), "fwd": round(w["fwd"] * 100, 2),
                              "er": round(w["er"], 3) if w["er"] is not None else None,
                              "date": str(df["date"].iloc[i].date())})
base = {
    "maxg": agg(base_rows, "maxg"), "fwd": agg(base_rows, "fwd"), "er": agg(base_rows, "er"),
    "n": len(base_rows),
}

def pair_stats(pairs):
    if not pairs:
        return {"n": 0}
    rs = [p["ret"] for p in pairs]
    return {"n": len(rs), "mean": round(st.mean(rs), 3), "median": round(st.median(rs), 3),
            "win": round(100 * sum(1 for r in rs if r > 0) / len(rs), 1),
            "min": round(min(rs), 2), "max": round(max(rs), 2),
            "avg_hold": round(st.mean([p["hold"] for p in pairs]), 1)}

def year_dist(ev):
    return [{"y": y, "n": c} for y, c in sorted(Counter(r["date"][:4] for r in ev).items())]

# 配对按 tag 分组
pair_by_tag = {}
for tag in ["H65_L35", "H70_L30"]:
    pair_by_tag[tag] = {
        "closed": [p for p in pair_all if p["tag"] == tag],
        "open": [p for p in pair_open if p["tag"] == tag],
    }

res = {
    "meta": {
        "universe": "blue_chips.csv 蓝筹股池", "n_loaded": n_loaded, "n_pool": len(tickers),
        "skipped": [t for t in tickers if t not in ticker_done] if False else [],
        "note": "高买=RSI升入更高档首日买入(60/65/70)；低卖=RSI跌入更低档首日卖出(40/35/30)。方向与之前'低买'报告相反(镜像)。",
        "n_loaded": n_loaded,
    },
    "n_high": len(high_ev), "n_low": len(low_ev),
    "n_high_cd10": len(high_cd10), "n_low_cd10": len(low_cd10),
    "base": base,
    "high": {"by_band": by_band(high_ev, H_BAND, H_ORDER), "by_band_cd10": by_band(high_cd10, H_BAND, H_ORDER),
             "stage_band": stage_band(high_ev, H_BAND, H_ORDER), "year_dist": year_dist(high_events)},
    "low": {"by_band": by_band(low_ev, L_BAND, L_ORDER), "by_band_cd10": by_band(low_cd10, L_BAND, L_ORDER),
            "stage_band": stage_band(low_ev, L_BAND, L_ORDER), "year_dist": year_dist(low_events)},
    "pairs": {tag: {"stats": pair_stats(v["closed"]), "closed_n": len(v["closed"]), "open_n": len(v["open"]),
                    "orders": v["closed"][:200], "open_orders": v["open"][:80]} for tag, v in pair_by_tag.items()},
    "events_high": high_events, "events_low": low_events,
    "recent_high": sorted(high_events, key=lambda x: x["date"])[-10:][::-1],
    "recent_low": sorted(low_events, key=lambda x: x["date"])[-10:][::-1],
    "n_loaded_true": n_loaded,
}
res["meta"]["skipped"] = [t for t in tickers if t not in {r["ticker"] for r in high_events + low_events}]

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o

out_path = os.path.join(OUT, "blue_chip_rsi_highbuy_lowsell.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(clean(res), f, ensure_ascii=False, indent=1, allow_nan=False)

# ---------- 控制台汇总 ----------
print(f"加载 {n_loaded} 只 | 高买事件 {len(high_ev)} (cd10 {len(high_cd10)}) | 低卖事件 {len(low_ev)} (cd10 {len(low_cd10)})")
print(f"[基率] fwd20 med {base['fwd']['median']}% | maxG20 med {base['maxg']['median']}% | ER med {base['er']['median']}")
print("\n[高买] 追高买入后 T+5/T+10/T+20:")
for b in H_ORDER:
    s = res["high"]["by_band"][b]
    print(f"  RSI {b:6s}: n={s['fwd20']['n']:5d} | T5 {s['fwd5']['median']:+6.2f}% T10 {s['fwd10']['median']:+6.2f}% T20 {s['fwd20']['median']:+6.2f}% 胜率{s['win20']}% 超额T20 {s['ex20']['median']:+5.2f}pp maxG {s['maxg20']['median']:+.2f}%")
print("\n[低卖] 卖出后 T+5/T+10/T+20:")
for b in L_ORDER:
    s = res["low"]["by_band"][b]
    print(f"  RSI {b:6s}: n={s['fwd20']['n']:5d} | T5 {s['fwd5']['median']:+6.2f}% T10 {s['fwd10']['median']:+6.2f}% T20 {s['fwd20']['median']:+6.2f}% 胜率{s['win20']}% 超额T20 {s['ex20']['median']:+5.2f}pp")
print("\n[配对]")
for tag in ["H65_L35", "H70_L30"]:
    p = res["pairs"][tag]
    print(f"  {tag}: 完整回合 {p['closed_n']} | 未平仓 {p['open_n']} | 均值 {p['stats']['mean']}% 中位 {p['stats']['median']}% 胜率 {p['stats']['win']}% 平均持有 {p['stats']['avg_hold']}日")
print("written:", out_path)