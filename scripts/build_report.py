# -*- coding: utf-8 -*-
"""单股 MACD 水下金叉回测报告生成器（参数化，供全部股票复用）
用法: python build_report.py [ticker]   （缺省生成全部10只）
输出: MACD水下金叉回测报告.html(IBKR) / MACD水下金叉回测_<TICKER>.html
"""
import pandas as pd
import numpy as np
import json
import sys

BASE = "/Users/alberthuang/Desktop/股票分析"
NAMES = {
    "ibkr": "Interactive Brokers（盈透证券）", "amzn": "Amazon（亚马逊）",
    "brk.b": "Berkshire Hathaway（伯克希尔）", "ge": "GE Aerospace（通用电气）",
    "gs": "Goldman Sachs（高盛）", "jnj": "Johnson &amp; Johnson（强生）",
    "ms": "Morgan Stanley（摩根士丹利）", "nvda": "NVIDIA（英伟达）",
    "spy": "SPDR S&amp;P 500 ETF（标普500ETF）", "unh": "UnitedHealth（联合健康）",
}
ALL = ["ibkr", "amzn", "brk.b", "ge", "gs", "jnj", "ms", "nvda", "spy", "unh"]

def fmt_pct(v): return f"{v*100:.1f}%"
def fmt_avg(v): return f"{v:+.2f}%"

def build(ticker):
    upper = ticker.upper()
    nodes_path = f"{BASE}/results/signal_nodes.csv" if ticker == "ibkr" else f"{BASE}/results/signal_nodes_{ticker}.csv"
    stats_path = f"{BASE}/results/summary_stats.json" if ticker == "ibkr" else f"{BASE}/results/summary_stats_{ticker}.json"
    out_path = f"{BASE}/reports/MACD水下金叉回测报告.html" if ticker == "ibkr" else f"{BASE}/reports/MACD水下金叉回测_{upper}.html"
    kline_path = f"{BASE}/data/{ticker}/BATS_{upper}, 1D.csv"

    nodes = pd.read_csv(nodes_path)
    stats = json.load(open(stats_path, encoding="utf-8"))
    summary = stats["summary"]
    buy = summary.get("_buy", {})

    df = pd.read_csv(kline_path)
    df.columns = ["time", "open", "high", "low", "close", "ema20", "ema10", "hist", "dif", "dea"]
    df["time"] = pd.to_datetime(df["time"])
    n = len(df)
    dates = df["time"].dt.strftime("%Y-%m-%d").tolist()
    ohlc = [[o, c, l, h] for o, c, l, h in zip(df["open"], df["close"], df["low"], df["high"])]
    ema10 = [round(x, 4) for x in df["ema10"]]
    ema20 = [round(x, 4) for x in df["ema20"]]
    dif = [round(x, 4) for x in df["dif"]]
    dea = [round(x, 4) for x in df["dea"]]
    hist = [round(x, 4) for x in df["hist"]]

    all_nodes = nodes.copy()
    all_nodes["hold3_ok"] = all_nodes["hold3"].fillna(False).astype(bool)
    all_nodes["hold4_ok"] = all_nodes["hold4"].fillna(False).astype(bool)
    all_nodes["hold5_ok"] = all_nodes["hold5"].fillna(False).astype(bool)
    all_nodes = all_nodes.sort_values("gold_date").reset_index(drop=True)

    # 成交点（紫=买入5日盈利 / 黑=不盈利）
    date2idx = {d: i for i, d in enumerate(dates)}
    buy_points = []
    for _, r in all_nodes.iterrows():
        if pd.notna(r["buy_status"]) and r["buy_status"] == "hit" and pd.notna(r["buy_date"]):
            bd = str(r["buy_date"])
            if bd in date2idx:
                ret5 = r["buy_ret5"]
                col = "#7048e8" if (pd.notna(ret5) and float(ret5) > 0) else "#1f2329"
                buy_points.append({"x": date2idx[bd], "price": float(r["buy_px"]), "d": bd, "c": col})

    # 信号分类
    fullUp, fullDn, partial, insuff, markArea = [], [], [], [], []
    for _, r in all_nodes.iterrows():
        gi, si = int(r["idx"]), int(r["stand_idx"])
        price = round(float(r["gold_close"]), 2)
        d = r["gold_date"]
        if pd.isna(r["hold5"]):
            insuff.append({"d": d, "x": gi, "price": price})
        elif r["hold5_ok"]:
            up = pd.notna(r["ret5"]) and float(r["ret5"]) > 0
            (fullUp if up else fullDn).append({"d": d, "x": gi, "price": price})
            markArea.append([{"name": d, "xAxis": gi}, {"xAxis": min(si + 4, n - 1)}])
        else:
            partial.append({"d": d, "x": gi, "price": price})

    # 统计对比
    ORDER = [("all_gold", "① 全部水下金叉"), ("pass_stand", "② +3天内站上EMA10/20"),
             ("pass_hold3", "③ +站稳3天"), ("pass_hold4", "④ +站稳4天"), ("pass_hold5", "⑤ +站稳5天")]
    group_labels, counts, win5, win10, win20, avg5, avg10, avg20 = [], [], [], [], [], [], [], []
    for key, label in ORDER:
        s = summary[key]
        group_labels.append(label); counts.append(s["count"])
        win5.append(round(s["ret5"]["win_rate"] * 100, 1)); win10.append(round(s["ret10"]["win_rate"] * 100, 1)); win20.append(round(s["ret20"]["win_rate"] * 100, 1))
        avg5.append(round(s["ret5"]["avg"], 2)); avg10.append(round(s["ret10"]["avg"], 2)); avg20.append(round(s["ret20"]["avg"], 2))

    # 买入对比
    buy_rows, buy_win_o, buy_win_b = [], [], []
    for k, lab in ((5, "T+5"), (10, "T+10"), (20, "T+20")):
        o, b = buy.get(f"orig_ret{k}"), buy.get(f"buy_ret{k}")
        if o and b:
            bc = "up" if b["win_rate"] * 100 >= 50 else "dn"
            buy_rows.append(f"<tr><td>{lab}</td><td class='up'>{fmt_pct(o['win_rate'])} / {fmt_avg(o['avg'])}</td>"
                            f"<td class='{bc}'>{fmt_pct(b['win_rate'])} / {fmt_avg(b['avg'])}</td><td>{b['n']}</td></tr>")
            buy_win_o.append(round(o["win_rate"] * 100, 1)); buy_win_b.append(round(b["win_rate"] * 100, 1))

    # 明细表
    def cell(v):
        if v == "—": return "<td class='na'>—</td>"
        fv = float(v); c = "up" if fv > 0 else ("dn" if fv < 0 else "")
        return f"<td class='{c}'>{v}</td>"
    node_rows = []
    for _, r in all_nodes.iterrows():
        cls = " class='hit'" if r["hold5_ok"] else ""
        h3 = "✓" if r["hold3_ok"] else "—"; h4 = "✓" if r["hold4_ok"] else "—"; h5 = "✓" if r["hold5_ok"] else "—"
        r5 = f"{r['ret5']:+.2f}" if pd.notna(r["ret5"]) else "—"
        r10 = f"{r['ret10']:+.2f}" if pd.notna(r["ret10"]) else "—"
        r20 = f"{r['ret20']:+.2f}" if pd.notna(r["ret20"]) else "—"
        bp = f"{r['buy_px']:.2f}" if pd.notna(r["buy_px"]) else "—"
        bs = r["buy_status"] if pd.notna(r["buy_status"]) else None
        if bs == "hit":
            bs_txt = "<span class='up'>成交</span>"
            b5 = cell(f"{r['buy_ret5']:+.2f}") if pd.notna(r["buy_ret5"]) else "<td class='na'>—</td>"
            b10 = cell(f"{r['buy_ret10']:+.2f}") if pd.notna(r["buy_ret10"]) else "<td class='na'>—</td>"
            b20 = cell(f"{r['buy_ret20']:+.2f}") if pd.notna(r["buy_ret20"]) else "<td class='na'>—</td>"
        elif bs == "miss":
            bs_txt = "<span style='color:#b45309'>错过</span>"; b5 = b10 = b20 = "<td class='na'>—</td>"
        else:
            bs_txt = "<span class='na'>—</span>"; b5 = b10 = b20 = "<td class='na'>—</td>"
        node_rows.append(
            f"<tr{cls}><td>{r['gold_date']}</td><td>{r['stand_date']}</td><td>{int(r['x_days'])}</td>"
            f"<td>{r['gold_close']}</td><td>{h3}</td><td>{h4}</td><td>{h5}</td>"
            f"{cell(r5)}{cell(r10)}{cell(r20)}<td>{bp}</td><td>{bs_txt}</td>{b5}{b10}{b20}</tr>")

    def stat_row(s):
        return (f"{fmt_pct(s['win_rate'])}|{fmt_avg(s['avg'])}|{fmt_avg(s['med'])}"
                f"|{s['std']:.2f}%|{s['min']:+.1f}% ~ {s['max']:+.1f}%")
    table_rows = []
    for key, label in ORDER:
        s = summary[key]
        table_rows.append(f"<tr><td>{label}</td><td>{s['count']}</td>"
                          f"<td>{stat_row(s['ret5'])}</td><td>{stat_row(s['ret10'])}</td><td>{stat_row(s['ret20'])}</td></tr>")

    # 热力图
    h5df = all_nodes[all_nodes["hold5_ok"]].reset_index(drop=True)
    hm_dates = h5df["gold_date"].tolist()
    hm_vals = []
    for i, (_, r) in enumerate(h5df.iterrows()):
        for k, col in [(0, "ret5"), (1, "ret10"), (2, "ret20")]:
            v = r[col]
            hm_vals.append([i, k, round(float(v), 2) if pd.notna(v) else None])

    # 动态数字
    d = {
        "name": NAMES[ticker], "t": upper, "days": n,
        "range": f"{df['time'].iloc[0].date()} ~ {df['time'].iloc[-1].date()}",
        "gold_n": summary["all_gold"]["count"], "stand_n": summary["pass_stand"]["count"],
        "h3_n": buy.get("hold3", 0), "h5_n": summary["pass_hold5"]["count"],
        "hit_n": buy.get("hit", 0), "miss_n": buy.get("miss", 0),
        "hit_rate": buy.get("hit_rate", 0) or 0,
        "h5_T5_win": fmt_pct(summary["pass_hold5"]["ret5"]["win_rate"]),
        "buy_T5_win": fmt_pct(buy["buy_ret5"]["win_rate"]) if buy.get("buy_ret5") else "—",
        "orig_T5_avg": fmt_avg(buy["orig_ret5"]["avg"]) if buy.get("orig_ret5") else "—",
        "buy_T5_avg": fmt_avg(buy["buy_ret5"]["avg"]) if buy.get("buy_ret5") else "—",
        "buy_T10_win": fmt_pct(buy["buy_ret10"]["win_rate"]) if buy.get("buy_ret10") else "—",
        "buy_T10_avg": fmt_avg(buy["buy_ret10"]["avg"]) if buy.get("buy_ret10") else "—",
        "buy_T20_win": fmt_pct(buy["buy_ret20"]["win_rate"]) if buy.get("buy_ret20") else "—",
        "buy_T20_avg": fmt_avg(buy["buy_ret20"]["avg"]) if buy.get("buy_ret20") else "—",
        "orig_T5_win": fmt_pct(buy["orig_ret5"]["win_rate"]) if buy.get("orig_ret5") else "—",
        "orig_T10_win": fmt_pct(buy["orig_ret10"]["win_rate"]) if buy.get("orig_ret10") else "—",
        "orig_T20_win": fmt_pct(buy["orig_ret20"]["win_rate"]) if buy.get("orig_ret20") else "—",
        "orig_T10_avg": fmt_avg(buy["orig_ret10"]["avg"]) if buy.get("orig_ret10") else "—",
        "orig_T20_avg": fmt_avg(buy["orig_ret20"]["avg"]) if buy.get("orig_ret20") else "—",
        "n_buy_up": sum(1 for p in buy_points if p["c"] == "#7048e8"),
        "n_buy_dn": sum(1 for p in buy_points if p["c"] == "#1f2329"),
        "group_labels": group_labels, "counts": counts,
        "win5": win5, "win10": win10, "win20": win20, "avg5": avg5, "avg10": avg10, "avg20": avg20,
        "buy_win_o": buy_win_o, "buy_win_b": buy_win_b,
        "hm_dates": hm_dates, "hm_vals": hm_vals,
        "dates": dates, "ohlc": ohlc, "ema10": ema10, "ema20": ema20,
        "dif": dif, "dea": dea, "hist": hist,
        "fullUp": fullUp, "fullDn": fullDn, "partial": partial, "insuff": insuff,
        "markArea": markArea, "buy_points": buy_points,
    }

    html = open(f"{BASE}/scripts/_report_template.html", encoding="utf-8").read()
    html = html.replace("__JSON__", json.dumps({k: v for k, v in d.items() if k in
        ["group_labels","counts","win5","win10","win20","avg5","avg10","avg20","buy_win_o","buy_win_b",
         "hm_dates","hm_vals","dates","ohlc","ema10","ema20","dif","dea","hist",
         "fullUp","fullDn","partial","insuff","markArea","buy_points"]}, ensure_ascii=False))
    html = html.replace("__NAME__", d["name"]).replace("__T__", d["t"]).replace("__RANGE__", d["range"]).replace("__DAYS__", str(d["days"]))
    html = html.replace("__GOLD_N__", str(d["gold_n"])).replace("__STAND_N__", str(d["stand_n"]))
    html = html.replace("__H3_N__", str(d["h3_n"])).replace("__H5_N__", str(d["h5_n"]))
    html = html.replace("__HIT_N__", str(d["hit_n"])).replace("__MISS_N__", str(d["miss_n"]))
    html = html.replace("__HIT_RATE__", f"{d['hit_rate']*100:.0f}%")
    html = html.replace("__H5_T5_WIN__", d["h5_T5_win"]).replace("__BUY_T5_WIN__", d["buy_T5_win"])
    html = html.replace("__ORIG_T5_WIN__", d["orig_T5_win"])
    html = html.replace("__ORIG_T5_AVG__", d["orig_T5_avg"]).replace("__BUY_T5_AVG__", d["buy_T5_avg"])
    html = html.replace("__BUY_T10__", f"{d['buy_T10_win']} / {d['buy_T10_avg']}").replace("__BUY_T20__", f"{d['buy_T20_win']} / {d['buy_T20_avg']}")
    html = html.replace("__ORIG_T10__", f"{d['orig_T10_win']} / {d['orig_T10_avg']}").replace("__ORIG_T20__", f"{d['orig_T20_win']} / {d['orig_T20_avg']}")
    html = html.replace("__N_BUY_UP__", str(d["n_buy_up"])).replace("__N_BUY_DN__", str(d["n_buy_dn"]))
    html = html.replace("__TABLE_ROWS__", "\n".join(table_rows)).replace("__BUY_ROWS__", "\n".join(buy_rows))
    html = html.replace("__NODE_ROWS__", "\n".join(node_rows))
    html = html.replace("__N_UP__", str(len(fullUp))).replace("__N_DN__", str(len(fullDn)))
    html = html.replace("__HM_H__", "330px" if len(hm_dates) > 40 else "310px")
    open(out_path, "w", encoding="utf-8").write(html)
    print(f"[{ticker}] {out_path.split('/')[-1]} | hold5={d['h5_n']} 成交={d['hit_n']}/{d['h3_n']} 紫{len([p for p in buy_points if p['c']=='#7048e8'])}/黑{len([p for p in buy_points if p['c']=='#1f2329'])}")

if __name__ == "__main__":
    targets = [sys.argv[1]] if len(sys.argv) > 1 else ALL
    for t in targets:
        build(t)
    print("done")
