# -*- coding: utf-8 -*-
"""
强 El Niño 窗口内路径分析：run-up（最大累计超额）vs 期末超额
回答：强事件期末转负，是"冲高后剧烈回撤"还是"全程阴跌"？
- 对 4 次有数据的事件（1997/2009/2014/2023），逐月累计超额路径
- peak = 窗口内最大累计超额（pp）；trough = 最小；end = 期末；dd = peak - end
- 口径沿用 57 号：累计收益 = 逐月复利，超额 = 标的累计 - SPY 累计
输出 results/agri_runup.json
"""
import json
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "agri_runup.json")

TICKERS = ["DE", "AGCO", "MOS", "CF", "NTR", "CTVA", "FMC", "ADM", "BG",
           "DAR", "FPI", "TSN", "HRL", "MOO", "DBA"]
SUB = {"DE": "农机", "AGCO": "农机", "MOS": "化肥", "CF": "化肥", "NTR": "化肥",
       "ADM": "粮商", "BG": "粮商", "CTVA": "种子植保", "FMC": "种子植保",
       "DAR": "油脂加工", "FPI": "农业REIT", "TSN": "肉类", "HRL": "肉类",
       "MOO": "农业ETF", "DBA": "商品ETF"}

# ---------- 1. ONI 解析（复用 57 号/强 El 专项） ----------
seas_to_mon = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
               "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
oni_rows = []
with open(os.path.join(DATA, "agri", "raw", "oni.txt"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("SEAS"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            seas, yr, anom = parts[0], int(parts[1]), float(parts[3])
        except (ValueError, IndexError):
            continue
        mon = seas_to_mon.get(seas)
        if mon is not None:
            oni_rows.append({"year": int(yr), "month": int(mon), "oni": float(anom)})
oni = pd.DataFrame(oni_rows).sort_values(["year", "month"]).reset_index(drop=True)
oni = oni[(oni["year"] >= 1950) & oni["oni"].notna()].copy()
oni["ym"] = oni["year"].astype(int) * 100 + oni["month"].astype(int)
oni_val = dict(zip(oni["ym"], oni["oni"]))

def el_events():
    vals = {int(k): float(v) for k, v in oni_val.items()}
    yms = sorted(vals.keys())
    evs = []
    i = 0
    n = len(yms)
    while i < n:
        if vals[yms[i]] >= 0.5:
            j = i
            while j < n and vals[yms[j]] >= 0.5:
                j += 1
            if j - i >= 5:
                evs.append({
                    "onset": int(yms[i]), "end": int(yms[j - 1]),
                    "peak": max(vals[yms[k]] for k in range(i, j)),
                    "len": j - i,
                    "peak_ym": int(yms[i + int(np.argmax([vals[yms[k]] for k in range(i, j)]))]),
                })
            i = j
        else:
            i += 1
    return evs

events = el_events()
strong_evs = [e for e in events if e["peak"] >= 1.5]

def ym_to_label(ym):
    return f"{int(ym) // 100}-{int(ym) % 100:02d}"

# ---------- 2. 月度收益 ----------
def monthly_df(ticker):
    path = os.path.join(DATA, ticker.lower(), f"{ticker}, 1D.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    m = df["adj_close"].resample("ME").last().dropna()
    ret = m.pct_change().dropna() * 100
    r = pd.DataFrame({"ret": ret})
    r["ym"] = r.index.year.astype(int) * 100 + r.index.month.astype(int)
    return r

mrets = {t: monthly_df(t) for t in TICKERS}
mrets["SPY"] = monthly_df("SPY")

# ---------- 3. 窗口内逐月累计超额路径 ----------
def window_path(ticker, onset_ym, months):
    df = mrets[ticker]
    cy = int(onset_ym)
    if cy not in set(df["ym"]):
        return None
    yy, mm = divmod(cy, 100)
    for _ in range(months):
        mm += 1
        if mm > 12:
            mm, yy = 1, yy + 1
    end_ym = yy * 100 + mm
    sub = df[(df["ym"] >= cy) & (df["ym"] < end_ym)]["ret"]
    if len(sub) < max(2, months - 2):
        return None
    acc = 1.0
    path = []
    for r in sub:
        acc *= (1 + r / 100.0)
        path.append((acc - 1) * 100)
    return path

def runup_stats(ticker, onset_ym, months):
    pt = window_path(ticker, onset_ym, months)
    ps = window_path("SPY", onset_ym, months)
    if pt is None or ps is None:
        return None
    n = min(len(pt), len(ps))
    ex = [pt[i] - ps[i] for i in range(n)]
    peak = max(ex)
    return {"n_m": n,
            "peak": round(peak, 1),
            "peak_m": int(np.argmax(ex)) + 1,
            "trough": round(min(ex), 1),
            "end": round(ex[-1], 1),
            "dd": round(peak - ex[-1], 1),  # peak 到期末的回撤幅度（pp）
            "path": [round(x, 1) for x in ex]}  # 逐月累计超额路径（pp）

# ---------- 4. 汇总 ----------
W = 12  # T+12 主口径
ev_records = []
for e in strong_evs:
    rec = {"onset": ym_to_label(e["onset"]), "end": ym_to_label(e["end"]),
           "peak": round(e["peak"], 2), "len": e["len"], "tickers": {}}
    for t in TICKERS:
        st = runup_stats(t, e["onset"], W)
        if st:
            rec["tickers"][t] = st
    ev_records.append(rec)

# 事件级汇总（仅对有数据的标的）
ev_summary = []
for r in ev_records:
    ts = r["tickers"]
    if not ts:
        ev_summary.append({"onset": r["onset"], "n": 0})
        continue
    vals = list(ts.values())
    n = len(vals)
    ev_summary.append({
        "onset": r["onset"], "peak": r["peak"], "n": n,
        "n_peak_pos": int(sum(1 for v in vals if v["peak"] > 0)),
        "n_end_pos": int(sum(1 for v in vals if v["end"] > 0)),
        "avg_peak": round(float(np.mean([v["peak"] for v in vals])), 1),
        "avg_end": round(float(np.mean([v["end"] for v in vals])), 1),
        "avg_dd": round(float(np.mean([v["dd"] for v in vals])), 1),
        "n_updown": int(sum(1 for v in vals if v["peak"] > 0 and v["end"] < 0)),  # 冲高后转负
        "n_alldown": int(sum(1 for v in vals if v["peak"] <= 0)),  # 全程未正
    })

# 标的级汇总（跨有数据强事件）
by_ticker = {}
for t in TICKERS:
    rows = []
    for r in ev_records:
        if t in r["tickers"]:
            rows.append(r["tickers"][t])
    if not rows:
        continue
    by_ticker[t] = {
        "sub": SUB[t], "n": len(rows),
        "avg_peak": round(float(np.mean([x["peak"] for x in rows])), 1),
        "avg_end": round(float(np.mean([x["end"] for x in rows])), 1),
        "avg_dd": round(float(np.mean([x["dd"] for x in rows])), 1),
        "n_updown": int(sum(1 for x in rows if x["peak"] > 0 and x["end"] < 0)),
        "n_alldown": int(sum(1 for x in rows if x["peak"] <= 0)),
        "cases": [{"onset": r["onset"], "peak": x["peak"], "peak_m": x["peak_m"],
                   "end": x["end"], "dd": x["dd"]} for r in ev_records if t in r["tickers"]
                  for x in [r["tickers"][t]]],
    }

out = {
    "meta": {"window_months": W,
             "note": "excess path = ticker 累计收益 - SPY 累计收益（pp，逐月复利）; peak=窗口最大累计超额, end=期末, dd=peak-end, peak_m=峰值所在月(1=onset月)"},
    "event_summary": ev_summary,
    "by_ticker": by_ticker,
    "events_detail": ev_records,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("written:", OUT, os.path.getsize(OUT), "bytes")

# ---------- 5. HTML 可视化（可选：python build_html 生成） ----------
def build_html():
    # 4 次有数据事件 × 代表标的超额路径折线（Okabe-Ito 色弱安全）
    import html as H
    pal = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9",
           "#F0E442", "#000000", "#999999"]
    events = [r for r in ev_records if r["tickers"]]
    lines = []
    for idx, ev in enumerate(events):
        # 每事件选 6 个代表标的（化肥/农化/农机/粮商/油脂/肉类 + 指数）
        picks = [t for t in ["CF", "MOS", "FMC", "DE", "ADM", "DAR", "TSN", "HRL"]
                 if t in ev["tickers"]][:6]
        ser = []
        for t in picks:
            st = ev["tickers"][t]
            ser.append({"name": t, "data": st["path"],
                        "lineStyle": {"width": 2.5, "color": pal[picks.index(t) % len(pal)]},
                        "itemStyle": {"color": pal[picks.index(t) % len(pal)]}})
        x = [str(i + 1) for i in range(ev["tickers"][picks[0]]["n_m"])]
        lines.append({
            "title": f"{ev['onset']} ~ {ev['end']}  ONI峰值 {ev['peak']}",
            "x": x, "series": ser,
            "ev": ev,
        })
    # 生成 HTML
    divs = []
    scripts = []
    for i, L in enumerate(lines):
        divs.append(f'<div class="chart" id="runup{i}"></div>')
        scripts.append(f'''mkChart("runup{i}", {H.escape(str(L["x"])).replace("'", "&#39;")}, {H.escape(str(L["series"]))});''')
    # 简化：直接内嵌 JSON
    import json as J
    opts = []
    for L in lines:
        opts.append({"title": L["title"], "x": L["x"], "series": L["series"],
                     "ev": {k: L["ev"][k] for k in ("onset", "peak", "n") if k in L["ev"]}})
    html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>强 El Niño 窗口内超额路径（T+12）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
body{{font-family:"Segoe UI","Microsoft YaHei",sans-serif;background:#fff;color:#222;margin:24px;}}
h1{{font-size:20px}}h2{{font-size:15px;color:#333;margin-top:28px}}
.note{{font-size:12px;color:#666;background:#f6f6f6;padding:8px 12px;border-left:3px solid #0072B2}}
.chart{{width:100%;height:380px;margin:10px 0 26px}}
</style></head><body>
<h1>强 El Niño 事件：onset 后 12 个月逐月累计超额路径（vs SPY）</h1>
<div class="note">纵轴为标的 T+N 累计收益 − SPY 同期累计收益（pp）。蓝点为期末值，注意多数标的窗口内先冲高（run-up）再回撤，期末转负≠全程阴跌。色板为 Okabe-Ito 色弱安全。</div>
<div id="charts"></div>
<script>
const OPTS = {J.dumps(opts, ensure_ascii=False)};
function mkChart(id, o){{
  var el = document.getElementById(id);
  var ch = echarts.init(el);
  ch.setOption({{
    title:{{text:o.title, left:10, textStyle:{{fontSize:14}}}},
    tooltip:{{trigger:'axis', valueFormatter:v=>v+' pp'}},
    legend:{{top:6, left:10}},
    grid:{{left:60,right:20,top:44,bottom:30}},
    xAxis:{{type:'category',data:o.x,name:'onset 后月份'}},
    yAxis:{{type:'value',name:'超额 pp', axisLine:{{show:true}}, splitLine:{{lineStyle:{{type:'dashed'}}}}}},
    series:o.series.map(s=>({{...s,type:'line',smooth:false,showSymbol:true,symbolSize:6}}))
  }});
}}
const wrap = document.getElementById('charts');
OPTS.forEach((o,i)=>{{const d=document.createElement('div');d.className='chart';d.id='runup'+i;wrap.appendChild(d);mkChart('runup'+i,o);}});
</script></body></html>"""
    p = os.path.join(BASE, "reports", "57_农业股ENSO与利率敏感性", "runup_paths.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    print("html:", p, os.path.getsize(p), "bytes")

if __name__ == "__main__" and os.environ.get("BUILD_HTML") == "1":
    build_html()
print("\n== 事件级汇总（T+12 窗口） ==")
for s in ev_summary:
    if s["n"] == 0:
        print(f"  {s['onset']}: 无个股数据"); continue
    print(f"  {s['onset']} (ONI {s['peak']}): n={s['n']}  平均peak={s['avg_peak']}pp 平均end={s['avg_end']}pp 平均回撤={s['avg_dd']}pp | 冲高转负 {s['n_updown']}/{s['n']} 全程阴跌 {s['n_alldown']}/{s['n']}")
print("\n== 标的总览（跨强事件平均） ==")
for t, v in by_ticker.items():
    print(f"  {t:5s} {v['sub']}: avg_peak={v['avg_peak']:6.1f}  avg_end={v['avg_end']:6.1f}  avg_dd={v['avg_dd']:6.1f}  | 冲高转负 {v['n_updown']}/{v['n']}  全程阴跌 {v['n_alldown']}/{v['n']}")