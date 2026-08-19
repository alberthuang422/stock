#!/usr/bin/env python3
"""生成 VIX 低位 → SPX 后续行情 + VIX 低位持续时长 分析报告。
输出 reports/vix_low_spx_report.html (浅底深字研报风 + ECharts)
数据源: results/vix_low_spx.json + data/vix + data/gspc
"""
import os, json
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "results", "vix_low_spx.json")))
RD = json.load(open(os.path.join(ROOT, "results", "vix_rebound_dd.json")))

RED, GREEN, BLUE, AMBER = "#e03131", "#0aa06e", "#1e66d6", "#b45309"

# ---------- 补充统计 ----------
m = pd.read_csv(os.path.join(ROOT, "data", "vix", "VIX, 1D.csv"), parse_dates=["date"])
m = m.merge(pd.read_csv(os.path.join(ROOT, "data", "gspc", "GSPC, 1D.csv"), parse_dates=["date"]),
            on="date", suffixes=("_vix", "_gspc")).sort_values("date").reset_index(drop=True)
vix, spx = m["close_vix"].values, m["close_gspc"].values
n = len(m)

# VIX 直方图
hist, edges = np.histogram(vix, bins=list(range(10, 52, 2)))
hist_labels = [f"{edges[i]}-{edges[i+1]}" for i in range(len(edges) - 1)]

# 近两年月度序列 (图表用)
m2 = m[m["date"] >= "2014-01-01"].copy()
m2["ym"] = m2["date"].dt.strftime("%Y-%m")
mm = m2.groupby("ym").agg(vix=("close_vix", "mean"), spx=("close_gspc", "last")).reset_index()

# 区间结束后表现 (VIX<15)
runs = D["run_detail"]["15"]
f20 = [r["spx_fwd20"] for r in runs if r["spx_fwd20"] is not None]
f60 = [r["spx_fwd60"] for r in runs if r["spx_fwd60"] is not None]

# 区间长度分桶 (VIX<15)
lens = np.array([r["days"] for r in runs])
buckets = [(1, 3, "1-3天"), (4, 10, "4-10天"), (11, 20, "11-20天"), (21, 40, "21-40天"), (41, 80, "41-80天"), (81, 9999, "80天以上")]
buck_vals = [int(((lens >= lo) & (lens <= hi)).sum()) for lo, hi, _ in buckets]
buck_lab = [b[2] for b in buckets]

# 长区间表 (>=20天, 按起止)
long_runs = [r for r in runs if r["days"] >= 20]

# 危险案例: high_scenario 中 fwd120 < -5% 或 fwd20 < -8%
h15 = D["high_scenario"]["15"]
bad = [r for r in h15["detail"] if (r.get("fwd120") is not None and r["fwd120"] < -5) or (r.get("fwd20") is not None and r["fwd20"] < -8)]
bad.sort(key=lambda r: r.get("fwd120") or 999)

meta = D["meta"]
print(f"long runs: {len(long_runs)}, bad cases: {len(bad)}")

# ---------- 回撤时点数据 (vix_rebound_dd.json) ----------
rd_meta = RD["meta"]
rd_detail = RD["detail"]

def bucket(days, edges):
    if days < edges[0]:
        return 0
    for i in range(len(edges) - 1):
        if days >= edges[i] and days < edges[i + 1]:
            return i
    return len(edges) - 1

# 谷底时点分桶 (相对E天数)
dd_bucket_names = ["0-5天", "6-10天", "11-20天", "21-30天", "31-60天", ">60天"]
dd_bucket_vals = [0] * 6
for r in rd_detail:
    off = r["cum_min_offset"]
    idx = bucket(off, [0, 6, 11, 21, 31, 61, 9999])
    dd_bucket_vals[idx] += 1
# 谷底时 VIX 分桶
vix_bucket_names = ["15-18", "18-20", "20-23", "23-26", "26-30", ">30"]
vix_bucket_vals = [0] * 6
for r in rd_detail:
    v = r["vix_at_valley"]
    idx = bucket(v, [15, 18, 20, 23, 26, 30, 9999])
    vix_bucket_vals[idx] += 1
# 去重后的深回撤案例 (按T20去重, 保留cum_min最深)
seen_t20 = {}
for r in sorted(rd_detail, key=lambda x: x["cum_min"]):
    seen_t20.setdefault(r["T20"], r)
deep_cases = sorted(seen_t20.values(), key=lambda x: x["max_dd"])[:10]
dd_cases_raw = deep_cases

# ---------- HTML ----------
JS = json.dumps({
    "meta": meta,
    "hist": {"labels": hist_labels, "vals": [int(x) for x in hist], "cur": meta["cur_vix"],
             "q25": meta["vix_q25"], "median": meta["vix_median_all"]},
    "monthly": {"labels": mm["ym"].tolist(), "vix": [round(x, 2) for x in mm["vix"].tolist()],
                "spx": [round(x, 1) for x in mm["spx"].tolist()]},
    "base": D["base_fwd"],
    "by_start": D["by_start"],
    "by_day": D["by_day"],
    "run_stats": D["run_stats"],
    "life15": D["life_tab_15"],
    "break20": D["break_to20"],
    "high": h15["agg"],
    "high_n": h15["n"],
    "end20": {"n": len(f20), "mean": round(float(np.mean(f20)), 2), "med": round(float(np.median(f20)), 2),
              "win": round(float((np.array(f20) > 0).mean()) * 100, 1), "worst": round(float(min(f20)), 1)},
    "end60": {"n": len(f60), "mean": round(float(np.mean(f60)), 2), "med": round(float(np.median(f60)), 2),
              "win": round(float((np.array(f60) > 0).mean()) * 100, 1), "worst": round(float(min(f60)), 1)},
    "lenbuck": {"labels": buck_lab, "vals": buck_vals},
    "dd_timing": {"labels": dd_bucket_names, "vals": dd_bucket_vals},
    "dd_vix": {"labels": vix_bucket_names, "vals": vix_bucket_vals},
    "dd_meta": {k: rd_meta[k] for k in ["E_to_T20", "valley_offset_E", "vix_at_valley",
                                        "valley_rel_T20", "valley_rel_vixpeak", "cum_min", "max_dd",
                                        "frac_dd_gt3", "frac_dd_gt5", "frac_dd_gt10"]},
    "dd_speed": RD["by_speed"],
}, ensure_ascii=False).replace("</", "<\\/")

# 长区间表行
def fmt_pct(v, na="—"):
    if v is None: return f'<td class="na">{na}</td>'
    c = "up" if v > 0 else ("dn" if v < 0 else "")
    return f'<td class="{c}">{v:+.1f}%</td>'

dd_case_rows = ""
for r in dd_cases_raw:
    dd_case_rows += ("<tr><td>" + r["start"] + " ~ " + r["end"] + "</td><td>" + r["E"] + "</td><td>"
                     + r["T20"] + "</td><td>" + str(r["days_E_to_T20"]) + "</td><td>" + str(r["cum_min_offset"]) + "</td><td>"
                     + str(r["vix_at_valley"]) + "</td>" + fmt_pct(r["cum_min"]) + fmt_pct(r["max_dd"]) + "</tr>")

long_rows = ""
for r in long_runs:
    long_rows += ("<tr><td>" + r["start"] + "</td><td>" + r["end"] + "</td><td>" + str(r["days"]) + "</td>"
                  + f'<td>{r["vix_start"]}</td><td>{r["vix_end"]}</td>'
                  + fmt_pct(r["spx_chg"]) + fmt_pct(r["spx_fwd20"]) + fmt_pct(r["spx_fwd60"]) + "</tr>")

bad_rows = ""
for r in bad:
    bad_rows += ("<tr><td>" + r["start"] + "</td><td>" + str(r["vix"]) + "</td>"
                 + f'<td>{r["spx_drawdown_from_high"]:+.1f}%</td>'
                 + fmt_pct(r.get("fwd20")) + fmt_pct(r.get("fwd60")) + fmt_pct(r.get("fwd120")) + "</tr>")

# 前瞻收益表 (by_start 主口径)
def stat_cell(s):
    if not s: return '<td class="na">—</td>'
    c = "up" if s["mean"] > 0 else "dn"
    return f'<td class="{c}">{s["mean"]:+.2f}%</td><td>{s["win"]:.1f}%</td><td>{s["median"]:+.2f}%</td><td>{s["worst"]:+.1f}</td><td>{s["n"]}</td>'

fwd_rows = ""
for n_ in [5, 10, 20, 60, 120]:
    b = D["base_fwd"][f"T{n_}"]
    s15, s13, s12 = D["by_start"]["15"][f"T{n_}"], D["by_start"]["13"][f"T{n_}"], D["by_start"]["12"][f"T{n_}"]
    fwd_rows += (f'<tr><td>T+{n_}</td><td>{b["mean"]:+.2f}%</td><td>{b["win"]:.1f}%</td>'
                 + stat_cell(s15) + stat_cell(s13) + stat_cell(s12) + "</tr>")

# 按日口径表 (by_day)
day_rows = ""
for n_ in [5, 10, 20, 60, 120]:
    b = D["base_fwd"][f"T{n_}"]
    cells = ""
    for th in ["15", "13", "12"]:
        s = D["by_day"][th][f"T{n_}"]
        cells += f'<td>{s["mean"]:+.2f}%</td><td>{s["win"]:.1f}%</td><td>{s["p25"]:+.1f}</td>'
    day_rows += (f'<tr><td>T+{n_}</td><td>{b["mean"]:+.2f}%</td><td>{b["win"]:.1f}%</td>'
                 + f'<td>{b["p25"]:+.1f}</td>{cells}</tr>')

# 条件剩余寿命表
life_rows = ""
Ds = [1, 3, 5, 10, 20, 40]
Ks = [3, 5, 10, 20, 40, 60]
for d in Ds:
    row = D["life_tab_15"][str(d)]
    cells = "".join(f'<td>{row[str(k)] if row[str(k)] is not None else "—"}%</td>' for k in Ks)
    life_rows += f'<tr><td>{d}</td>{cells}</tr>'

# 回归速度表
bk_rows = ""
for th in ["15", "13", "12"]:
    b = D["break_to20"][th]
    if not b: continue
    bk_rows += (f'<tr><td>VIX &lt; {th}</td><td>{b["n"]}</td><td>{b["median"]}</td><td>{b["mean"]}</td>'
                + f'<td>{b["p25"]}</td><td>{b["best"]}</td></tr>')

# run_stats 卡
rs15 = D["run_stats"]["15"]; rs13 = D["run_stats"]["13"]; rs12 = D["run_stats"]["12"]

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VIX 低位 · 标普500 后续行情与低位持续性分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}}
  .wrap{{max-width:1220px;margin:0 auto;}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}}
  h1{{font-size:21px;margin-bottom:4px;}}
  .meta{{color:var(--sub);font-size:12.5px;margin-bottom:14px;}}
  h2{{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}}
  .kpi{{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}}
  .kpi .num{{font-size:21px;font-weight:700;}}
  .kpi .num.up{{color:var(--red);}} .kpi .num.dn{{color:var(--green);}}
  .kpi .lab{{color:var(--sub);font-size:12px;margin-top:2px;}}
  table{{width:100%;border-collapse:collapse;font-size:12px;}}
  th{{background:#f3f5f8;text-align:left;padding:6px 7px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}}
  td{{padding:5px 7px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}}
  td.up{{color:var(--red);font-weight:600;}} td.dn{{color:var(--green);font-weight:600;}} td.na{{color:#c3c8cf;}}
  .scroll{{overflow-x:auto;}}
  .chart{{width:100%;height:380px;}}
  .chart.sm{{height:320px;}}
  .note{{color:var(--sub);font-size:12px;margin-top:8px;}}
  .keypoint{{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}}
  .warn{{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;}}
  .dis{{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}}
  .hl{{font-weight:700;color:var(--red);}} .hlg{{font-weight:700;color:var(--green);}}
  .tag{{display:inline-block;background:#eef3fb;color:var(--blue);border:1px solid #d5e2f7;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:600;margin-right:6px;}}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>VIX 低位 · 标普500 后续行情与低位持续性分析</h1>
    <div class="meta">数据：CBOE VIX 指数（^VIX）+ 标普500 指数（^GSPC）日线，{meta["start"]} ~ {meta["end"]}，共 {meta["n_days"]} 个交易日（Yahoo Finance 收盘口径）｜分析框架：VIX 低位定义 = 收盘 &lt; 15（低）/ &lt; 13（极低）/ &lt; 12（罕见极低）｜前瞻收益按「连续低位区间起点」入场（独立样本）与「低位日」入场（全样本）双口径</div>
    <div class="kpis">
      <div class="kpi"><div class="num up">{meta["cur_vix"]}</div><div class="lab">当前 VIX（{meta["end"]}）· 历史分位 {meta["cur_pctile"]}%</div></div>
      <div class="kpi"><div class="num">-0.2%</div><div class="lab">标普500 距历史高点（{meta["cur_spx"]:,.0f} 点，接近新高）</div></div>
      <div class="kpi"><div class="num">{meta["cur_run_days_under15"]} 天</div><div class="lab">当前 VIX 连续 &lt; 15 的天数（8/12 起）</div></div>
      <div class="kpi"><div class="num">{meta["vix_median_all"]}</div><div class="lab">VIX 全期中位数（均值 {meta["vix_mean_all"]}）</div></div>
      <div class="kpi"><div class="num">{rs15["pct_time"]}%</div><div class="lab">1990 年以来 VIX&lt;15 时间占比</div></div>
    </div>
  </div>

  <div class="card">
    <h2>核心结论</h2>
    <div class="keypoint">
      <b>① VIX 低位不是看跌信号，而是「确定性更高的慢环境」。</b>VIX&lt;15 的交易日入场，T+20 上涨概率 {D["by_day"]["15"]["T20"]["win"]}%（基线 {D["base_fwd"]["T20"]["win"]}%），T+120 上涨概率 <b>{D["by_day"]["15"]["T120"]["win"]}%</b>（基线 73.8%）；VIX&lt;12 时 T+120 胜率高达 {D["by_day"]["12"]["T120"]["win"]}%。但<b>平均收益并不更高</b>（T+20 均值 0.62% vs 基线 0.77%）——低波动期涨幅温和、缺少危机后的暴力反弹。
      <br><b>② 风险不在「VIX 低」，而在「VIX 低位结束」。</b>VIX&lt;15 区间结束后 20 日内，标普平均 <b>-0.05%</b>（胜率仅 54%，最差 -29.2%），60 日才修复至 +1.25%。2018-02、2018-Q4、2020-02 三次大回调均发生在 VIX 长期低位区间的尾声。
      <br><b>③ VIX&lt;15 低位维持：中位仅 3 天、均值 13.7 天。</b>当前已连续 3 天，历史上「已持续 3 天时」再维持 ≥5 天概率 {D["life_tab_15"]["3"]["5"]}%、≥10 天 {D["life_tab_15"]["3"]["10"]}%、≥20 天 {D["life_tab_15"]["3"]["20"]}%；VIX 从 &lt;15 回升至 ≥20 中位需 {D["break_to20"]["15"]["median"]} 天。
      <br><b>④ 当前形态 = 低波动 + 标普接近新高</b>，历史上同形态 200 例中 T+120 胜率仍达 {h15["agg"]["120"]["win"]}%，但存在 11 例 120 日内跌超 5%（最差 {h15["agg"]["120"]["worst"]}%，2019-09 起 COVID 案例），尾部不可忽视。
      <br><b>⑤ 若低位终结，「跌最多的时候」有时点规律可循</b>：从 VIX 脱离低位日 E 算起，SPX 谷底中位出现在 <b>E+18 个交易日</b>，且谷底时 VIX 中位 20.5——<b>VIX 冲破 20 前后即历史上股市最痛的位置</b>（谷底与 VIX 首破 20 日中位差 0 天）；86.8% 的事件峰谷回撤 ≤10%，深跌（&gt;10%）仅 COVID、2015 两例。
    </div>
  </div>

  <div class="card">
    <h2>一、当前状态定位：VIX 历史分布</h2>
    <div id="chart_hist" class="chart sm"></div>
    <div class="note">VIX 1990~2026 收盘分布（2 点/桶）。当前 14.25 落在「14-16」桶，低于全期中位数 17.61 与均值 19.45，处于 <b>26.8% 分位</b>——比历史 73% 的时间低，属于「偏低但远未到极端」：VIX&lt;12（罕见极低，占 8.7%）和 &lt;10 才是真正的极端区。</div>
    <div id="chart_trend" class="chart"></div>
    <div class="note">2014 年以来 VIX 月均（蓝线，左轴）与标普500（红线，右轴）。VIX 长期在 14~20 区间运行，14 以下是「顺风区」，多数牛市月份（2017、2021 大部分时间、2023 下半年）VIX 都压在 15 以下。</div>
  </div>

  <div class="card">
    <h2>二、VIX 低位后，标普500 的后续行情（核心问题 1）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>持有期</th><th>基线·全期均值</th><th>基线·胜率</th>
        <th>VIX&lt;15 均值</th><th>胜率</th><th>中位</th><th>最差</th><th>n</th>
        <th>VIX&lt;13 均值</th><th>胜率</th><th>中位</th><th>最差</th><th>n</th>
        <th>VIX&lt;12 均值</th><th>胜率</th><th>中位</th><th>最差</th><th>n</th></tr></thead>
      <tbody>{fwd_rows}</tbody>
    </table>
    </div>
    <div class="note">口径：以每个<b>连续低位区间的起点</b>（VIX 首次跌破阈值的交易日）入场，独立样本，无重叠。VIX 越低，T+20 以后胜率抬升越明显；但均值普遍不高于基线——低波动环境的收益特征是「涨得稳、跌得少」而非「涨得猛」。</div>
    <div id="chart_win" class="chart sm"></div>
    <div class="note">胜率对比（按区间起点入场）。VIX&lt;12 时 T+60 胜率 {D["by_start"]["12"]["T60"]["win"]}% / T+120 {D["by_start"]["12"]["T120"]["win"]}%，显著高于基线。</div>
  </div>

  <div class="card">
    <h2>三、按日口径（任何一天看到 VIX 低就持有）：全样本重叠口径</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>持有期</th><th>基线均值</th><th>基线胜率</th><th>基线P25</th>
        <th>VIX&lt;15 均值</th><th>胜率</th><th>P25</th>
        <th>VIX&lt;13 均值</th><th>胜率</th><th>P25</th>
        <th>VIX&lt;12 均值</th><th>胜率</th><th>P25</th></tr></thead>
      <tbody>{day_rows}</tbody>
    </table>
    </div>
    <div class="note">P25 = 最差四分之一分位（尾部风险参考）。VIX&lt;15 时 T+120 胜率 80.9%、VIX&lt;12 时 84.1% vs 基线 73.8%；P25 也显著更厚（-0.4%~-1.5% vs 基线 -0.4% 以上，最差档 -6% 以内 vs 基线最差 -45%）。<b>核心含义：VIX 低时买入并长期持有，是「低尾部 + 高确定性」的组合，代价是平均弹性略低。</b></div>
  </div>

  <div class="card">
    <h2>四、VIX 低位能维持多久（核心问题 2）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>阈值</th><th>低位区间段数</th><th>区间长度 中位</th><th>均值</th><th>P90</th><th>最长</th><th>占全期时间</th></tr></thead>
      <tbody>
        <tr><td>VIX &lt; 15</td><td>{rs15["n_runs"]}</td><td>{rs15["len_median"]} 天</td><td>{rs15["len_mean"]} 天</td><td>{rs15["len_p90"]} 天</td><td>{rs15["len_max"]} 天</td><td>{rs15["pct_time"]}%</td></tr>
        <tr><td>VIX &lt; 13</td><td>{rs13["n_runs"]}</td><td>{rs13["len_median"]} 天</td><td>{rs13["len_mean"]} 天</td><td>{rs13["len_p90"]} 天</td><td>{rs13["len_max"]} 天</td><td>{rs13["pct_time"]}%</td></tr>
        <tr><td>VIX &lt; 12</td><td>{rs12["n_runs"]}</td><td>{rs12["len_median"]} 天</td><td>{rs12["len_mean"]} 天</td><td>{rs12["len_p90"]} 天</td><td>{rs12["len_max"]} 天</td><td>{rs12["pct_time"]}%</td></tr>
      </tbody>
    </table>
    </div>
    <div id="chart_len" class="chart sm"></div>
    <div class="note">VIX&lt;15 区间长度分布：<b>41% 只维持 1-3 天</b>（短暂下探），但尾部存在超长段——205 天（1994-12~1995-10）、135 天（2005-11~2006-05）、136 天（2006-08~2007-02）、115 天（2017-08~2018-02）。</div>
    <h2 style="margin-top:18px;">条件剩余寿命：已持续 D 天，还能再维持 ≥K 天的历史概率（VIX&lt;15）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>已持续 ↓ / 再维持 →</th><th>≥3 天</th><th>≥5 天</th><th>≥10 天</th><th>≥20 天</th><th>≥40 天</th><th>≥60 天</th></tr></thead>
      <tbody>{life_rows}</tbody>
    </table>
    </div>
    <div class="note">读法：当前已连续 3 天（D=3 行），再维持 ≥5 天概率 {D["life_tab_15"]["3"]["5"]}%、≥10 天 {D["life_tab_15"]["3"]["10"]}%、≥20 天（一个月）{D["life_tab_15"]["3"]["20"]}%。<b>VIX 低位有强「自我强化」特征</b>：持续越久，再维持的概率越高（D=10 后 ≥10 天概率升至 66%），因为长时间低波动往往对应稳定的宏观环境。</div>
    <h2 style="margin-top:18px;">回归速度：从低位到 VIX 首次升破 20（均值附近）需要多久</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>起点阈值</th><th>样本</th><th>中位</th><th>均值</th><th>P25</th><th>最长</th></tr></thead>
      <tbody>{bk_rows}</tbody>
    </table>
    </div>
    <div class="note">VIX 均值回归极慢：从 &lt;15 到重新 &gt;20，一半情形要 <b>60 个交易日（约 3 个月）</b>以上；VIX&lt;12 后中位更是要 7 个月。这也是「低波动期可以按季度而非按周来规划持仓」的统计依据。</div>
  </div>

  <div class="card">
    <h2>五、风险点：VIX 低位结束 ≠ 利空出尽，反而是回调高发窗口</h2>
    <div id="chart_end" class="chart sm"></div>
    <div class="note">对每个 VIX&lt;15 区间，统计「区间结束日（VIX 重新站上 15）」之后标普的 T+20 / T+60。T+20 平均 -0.05%、胜率仅 54%（最差 -29.2%），明显弱于基线 T+20（+0.77%、63.7%）；T+60 才修复到 +1.25%。<b>低波动结束时往往伴随波动率跳升和指数回调</b>——历史上 2018-02（2017 低位区后）、2018-Q4、2020-02（COVID）均是「长期低位 → VIX 快速抬升 → 指数急跌」的路径。</div>
    <div class="warn"><b>操作含义：</b>与其问「VIX 低位能撑多久再跑」，不如盯「VIX 是否开始快速脱离低位」——VIX 连续 3 日抬升或单日跳升 &gt;3 点，往往才是低位环境终结的领先信号；届时再评估减仓比在低位时提前离场更科学。</div>
  </div>

  <div class="card">
    <h2>五之二、那么「跌最多的时候」具体在什么时候发生？—— 回撤时点解剖</h2>
    <div class="keypoint">对 197 段「VIX 从低位回升至 ≥20」的完整周期解剖：<b>标普的谷底（从低位结束日 E 起算的最大回撤点）中位出现在 E+18 个交易日</b>（P25=5 天，P75=39 天），<b>37.6% 在 10 天内见底、26.9% 在 11~30 天、23.9% 在 31~60 天，只有 11.7% 拖到 60 天以后</b>。谷底时 VIX 中位 <b>20.5</b>（P25=18 / P75=24）——<b>即「跌得最狠的一刻」几乎与 VIX 冲破 20 同步发生</b>（谷底相对 VIX 首次破 20 日的中位差为 0 天；相对 VIX 峰值日的中位差也为 0 天）。深度上：从 E 起算的最低累计收益中位 <b>-3.0%</b>，但窗口内峰谷回撤中位 <b>-6.8%</b>；回撤 &gt;3% 占 92.9%、&gt;5% 占 70.6%、&gt;10% 占 13.2%。</div>
    <div id="chart_dd_timing" class="chart sm"></div>
    <div class="note">SPX 谷底相对「VIX 脱离低位日 E」的天数分布（197 例）。<b>中位 18 天、P90=65 天</b>——若按「E 之后 VIX 中位还需 39 天才能到 20」推算，跌得最狠的时刻通常出现在 VIX 回升行程的前半程末端（约 40% 位置），而非等到 VIX 真正摸到 20 才爆发。</div>
    <div id="chart_dd_vix" class="chart sm"></div>
    <div class="note">谷底日的 VIX 水平分布：<b>64% 的谷底发生在 VIX 18~26 区间</b>（18-20 与 20-23 两桶合计 42%）。操作上可理解为：<b>VIX 从 15 开始回升、走到 20 上下时，是历史上股市最痛的位置</b>——这也是为什么「VIX 破 20」常被当作恐慌确认而非抄底信号的统计原因。</div>
    <div class="scroll">
    <table>
      <thead><tr><th>低波动区间</th><th>脱离日 E</th><th>VIX首破20日</th><th>E→20(天)</th><th>谷底 E+N(天)</th><th>谷底VIX</th><th>谷底累计收益</th><th>窗口峰谷回撤</th></tr></thead>
      <tbody>{dd_case_rows}</tbody>
    </table>
    </div>
    <div class="note">回撤最深的 10 段（按 VIX 首破 20 日去重）。<b>COVID（2020-02，-33.7%）与 2015 年中国股灾（-11.1%）</b>是仅有的两段回撤超 10% 的系统性案例，且谷底都比 VIX 见顶滞后（COVID 滞后 19 天、2015 滞后 1 天）——事件冲击型下跌中，VIX 先见顶、股市后见底。</div>
    <div class="warn"><b>结合当前状态：</b>当前 VIX 14.25、刚进入低位第 3 天。若历史模式重演：脱离低位（E）后中位 18 个交易日见底、谷底 VIX 约 20.5。从「VIX 重新站上 15」算起，<b>未来 1~6 周是历史上回撤最集中的窗口</b>，其中 VIX 在 18~24 区间时风险最大；但需同时记住 86.8% 的历史事件峰谷回撤 ≤10%、且中位仅 -6.8%——多数「低波动结束」是温和修正而非崩盘。</div>
  </div>

  <div class="card">
    <h2>六、当前形态复盘：低波动 + 标普接近历史高点</h2>
    <div class="keypoint">标普当前距历史高点仅 -0.2%，同时 VIX&lt;15——这是 1990 年以来出现过的「低波动 + 高位」组合（{h15["n"]} 例）。历史上该形态：<b>T+20 胜率 {h15["agg"]["20"]["win"]}%、T+120 胜率 {h15["agg"]["120"]["win"]}%、T+120 均值 {h15["agg"]["120"]["mean"]:+.1f}%</b>——长期仍偏正面，与「高位就该跌」的直觉相悖；但 T+120 最差 -20.2%，尾部风险集中在宏观拐点（COVID、2015-07 新兴市场冲击、2018）。</div>
    <div id="chart_high" class="chart sm"></div>
    <div class="note">低波动+高位形态 vs 所有 VIX&lt;15 起点 vs 基线：长期（T+120）三者胜率 80.3% / 80.9% / 73.8%，高位并未显著恶化长期胜率。</div>
    <h2 style="margin-top:18px;">历史危险案例（低波动+高位后 120 日内跌超 5%）</h2>
    <div class="scroll">
    <table>
      <thead><tr><th>起点</th><th>VIX</th><th>距250日高点</th><th>后20日</th><th>后60日</th><th>后120日</th></tr></thead>
      <tbody>{bad_rows}</tbody>
    </table>
    </div>
    <div class="note">11 例中 3 例（2019-09、2019-10、2018-07）对应 COVID/2018 系统性回调，其余多为 2015、2011 的中期震荡。触发因素几乎都是<b>外部宏观冲击而非估值本身</b>——低波动状态下市场的脆弱性来自「波动率压缩 → 杠杆累积 → 事件冲击放大」。</div>
  </div>

  <div class="card">
    <h2>七、历史 VIX&lt;15 长区间（≥20 天）复盘</h2>
    <div class="scroll" style="max-height:480px;overflow-y:auto;">
    <table>
      <thead><tr><th>起点</th><th>结束</th><th>持续</th><th>起VIX</th><th>末VIX</th><th>期间SPX</th><th>结束后T+20</th><th>结束后T+60</th></tr></thead>
      <tbody>{long_rows}</tbody>
    </table>
    </div>
    <div class="note">共 {len(long_runs)} 段。绿色 = 区间结束后仍上涨；<span class="hl">红色</span> = 结束后回调。可看到 1994-12~1995-10（205 天）、2006-08~2007-02（136 天）、2017-08~2018-02（115 天）是典型的「低波动持续 → 结束即回撤」模式。</div>
  </div>

  <div class="card">
    <div class="warn"><b>局限与提醒：</b>① 前瞻收益未扣除任何成本/股息，也未考虑波动率相关的衍生品对冲；② VIX 与 SPX 的因果关系无法从此类统计中识别——低 VIX 更多是「结果」而非「原因」；③ 2007 年以前 VIX 定价结构（CBOE 1990 起）与 2010 后低波动时代市场结构差异大，长历史统计仅供参考；④ 本文样本为 1990-01 ~ 2026-08 收盘数据，最近区间（8/12 起）无前瞻数据，不构成对未来时点的预测。</div>
    <div class="dis">数据来源：Yahoo Finance（^VIX / ^GSPC 日线，1990-01-02 ~ 2026-08-14，收盘口径）。仅供研究参考。<br><br><b>免责声明：</b>以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。</div>
  </div>

</div>
<script>
const D = {JS};
const RED='#e03131', GREEN='#0aa06e', BLUE='#1e66d6', AMBER='#b45309';

// 1 直方图
echarts.init(document.getElementById('chart_hist')).setOption({{
  tooltip:{{trigger:'axis',formatter:ps=>ps[0].axisValue+' 区间：'+ps[0].value+' 天'}},
  grid:{{left:48,right:24,top:30,bottom:36}},
  xAxis:{{type:'category',data:D.hist.labels,axisLabel:{{fontSize:10}}}},
  yAxis:{{type:'value',name:'交易日数',axisLabel:{{fontSize:10}}}},
  series:[{{type:'bar',data:D.hist.vals,barWidth:'70%',
    itemStyle:{{color:p=>p.dataIndex>=11?RED:'#9db8e8'}},
    markLine:{{silent:true,symbol:'none',data:[
      {{xAxis:'14-16',label:{{formatter:'当前 14.25',color:RED,position:'insideEndTop'}},lineStyle:{{color:RED,type:'dashed'}}}},
      {{xAxis:'16-18',label:{{formatter:'中位 17.61',color:AMBER,position:'insideEndTop'}},lineStyle:{{color:AMBER,type:'dashed'}}}},
      {{xAxis:'18-20',label:{{formatter:'均值 19.45',color:'#555',position:'insideEndTop'}},lineStyle:{{color:'#888',type:'dashed'}}}}
    ]}}
  }}]
}});

// 2 月度趋势
echarts.init(document.getElementById('chart_trend')).setOption({{
  tooltip:{{trigger:'axis'}},
  legend:{{data:['VIX 月均','标普500'],top:0}},
  grid:{{left:52,right:56,top:32,bottom:40}},
  xAxis:{{type:'category',data:D.monthly.labels,axisLabel:{{fontSize:9.5,interval:11}}}},
  yAxis:[
    {{type:'value',name:'VIX',min:0,axisLabel:{{fontSize:10}}}},
    {{type:'value',name:'SPX',axisLabel:{{fontSize:10,formatter:v=>v/1000+'k'}}}}
  ],
  dataZoom:[{{type:'inside',start:60}},{{type:'slider',start:60,height:16,bottom:2}}],
  series:[
    {{name:'VIX 月均',type:'line',data:D.monthly.vix,smooth:true,showSymbol:false,lineStyle:{{width:1.4,color:BLUE}},itemStyle:{{color:BLUE}},
      markLine:{{silent:true,symbol:'none',data:[{{yAxis:15,label:{{formatter:'15 低位线',color:AMBER,fontSize:10}},lineStyle:{{color:AMBER,type:'dashed'}}}}]}}}},
    {{name:'标普500',type:'line',yAxisIndex:1,data:D.monthly.spx,smooth:true,showSymbol:false,lineStyle:{{width:1.4,color:RED}},itemStyle:{{color:RED}}}}
  ]
}});

// 3 胜率对比
const winFwd = [5,10,20,60,120].map(n=>'T'+n);
const mk = (th,key)=>winFwd.map(n=>(D.by_start[th][n]||{{}})[key]);
echarts.init(document.getElementById('chart_win')).setOption({{
  tooltip:{{trigger:'axis',valueFormatter:v=>v==null?'—':v+'%'}},
  legend:{{data:['基线','VIX<15','VIX<13','VIX<12'],top:0}},
  grid:{{left:48,right:20,top:34,bottom:36}},
  xAxis:{{type:'category',data:winFwd,axisLabel:{{fontSize:11}}}},
  yAxis:{{type:'value',min:40,max:90,axisLabel:{{formatter:'{{value}}%'}}}},
  series:[
    {{name:'基线',type:'line',data:winFwd.map(n=>D.base[n].win),lineStyle:{{width:1.6,color:'#9aa2ab',type:'dashed'}},symbol:'circle',symbolSize:6,itemStyle:{{color:'#9aa2ab'}}}},
    {{name:'VIX<15',type:'line',data:mk('15','win'),lineStyle:{{width:2,color:BLUE}},symbolSize:7,itemStyle:{{color:BLUE}}}},
    {{name:'VIX<13',type:'line',data:mk('13','win'),lineStyle:{{width:2,color:AMBER}},symbolSize:7,itemStyle:{{color:AMBER}}}},
    {{name:'VIX<12',type:'line',data:mk('12','win'),lineStyle:{{width:2,color:RED}},symbolSize:7,itemStyle:{{color:RED}}}}
  ]
}});

// 4 区间长度分布
echarts.init(document.getElementById('chart_len')).setOption({{
  tooltip:{{trigger:'axis',formatter:ps=>ps[0].axisValue+'：'+ps[0].value+' 段'}},
  grid:{{left:48,right:20,top:30,bottom:36}},
  xAxis:{{type:'category',data:D.lenbuck.labels,axisLabel:{{fontSize:10}}}},
  yAxis:{{type:'value',name:'区间段数',axisLabel:{{fontSize:10}}}},
  series:[{{type:'bar',data:D.lenbuck.vals,barWidth:'55%',itemStyle:{{color:BLUE}},
    label:{{show:true,position:'top',fontSize:10,formatter:p=>p.value+'段 ('+((p.value/D.run_stats['15'].n_runs)*100).toFixed(0)+'%)'}}}}
  ]
}});

// 5 低位结束后 SPX 表现
echarts.init(document.getElementById('chart_end')).setOption({{
  tooltip:{{trigger:'axis',valueFormatter:v=>v+'%'}},
  legend:{{data:['基线 T+20','基线 T+60','低位结束 T+20','低位结束 T+60'],top:0}},
  grid:{{left:48,right:20,top:34,bottom:36}},
  xAxis:{{type:'category',data:['均值','胜率(右轴)'],axisLabel:{{fontSize:11}}}},
  yAxis:[
    {{type:'value',name:'均值 %',axisLabel:{{fontSize:10}}}},
    {{type:'value',name:'胜率 %',min:0,max:100,axisLabel:{{fontSize:10,formatter:'{{value}}%'}}}}
  ],
  series:[
    {{name:'基线 T+20',type:'bar',data:[D.base.T20.mean,null],itemStyle:{{color:'#c8cdd3'}},barGap:'30%'}},
    {{name:'基线 T+60',type:'bar',data:[D.base.T60.mean,null],itemStyle:{{color:'#9aa2ab'}},barGap:'30%'}},
    {{name:'低位结束 T+20',type:'bar',data:[D.end20.mean,null],itemStyle:{{color:RED}},barGap:'30%'}},
    {{name:'低位结束 T+60',type:'bar',data:[D.end60.mean,null],itemStyle:{{color:AMBER}},barGap:'30%'}},
    {{name:'基线 T+20',type:'bar',yAxisIndex:1,data:[null,D.base.T20.win],itemStyle:{{color:'#c8cdd3',opacity:.5}}}},
    {{name:'基线 T+60',type:'bar',yAxisIndex:1,data:[null,D.base.T60.win],itemStyle:{{color:'#9aa2ab',opacity:.5}}}},
    {{name:'低位结束 T+20',type:'bar',yAxisIndex:1,data:[null,D.end20.win],itemStyle:{{color:RED,opacity:.5}}}},
    {{name:'低位结束 T+60',type:'bar',yAxisIndex:1,data:[null,D.end60.win],itemStyle:{{color:AMBER,opacity:.5}}}}
  ]
}});

// 6 高位场景胜率对比
echarts.init(document.getElementById('chart_high')).setOption({{
  tooltip:{{trigger:'axis',valueFormatter:v=>v==null?'—':v+'%'}},
  legend:{{data:['基线','VIX<15','低波动+高位(当前形态)'],top:0}},
  grid:{{left:48,right:20,top:34,bottom:36}},
  xAxis:{{type:'category',data:winFwd,axisLabel:{{fontSize:11}}}},
  yAxis:{{type:'value',min:40,max:95,axisLabel:{{formatter:'{{value}}%'}}}},
  series:[
    {{name:'基线',type:'line',data:winFwd.map(n=>D.base[n].win),lineStyle:{{width:1.6,color:'#9aa2ab',type:'dashed'}},symbol:'circle',symbolSize:6,itemStyle:{{color:'#9aa2ab'}}}},
    {{name:'VIX<15',type:'line',data:mk('15','win'),lineStyle:{{width:2,color:BLUE}},symbolSize:7,itemStyle:{{color:BLUE}}}},
    {{name:'低波动+高位(当前形态)',type:'line',data:winFwd.map(n=>(D.high[n.replace('T','')]||{{}}).win),lineStyle:{{width:2.4,color:RED}},symbolSize:8,itemStyle:{{color:RED}}}}
  ]
}});

// 7 回撤时点: 谷底相对E天数分布
echarts.init(document.getElementById('chart_dd_timing')).setOption({{
  tooltip:{{trigger:'axis',formatter:ps=>ps[0].axisValue+'：'+ps[0].value+' 例 ('+((ps[0].value/D.dd_meta.valley_offset_E.n)*100).toFixed(0)+'%)'}},
  grid:{{left:48,right:20,top:30,bottom:36}},
  xAxis:{{type:'category',data:D.dd_timing.labels,axisLabel:{{fontSize:10}}}},
  yAxis:{{type:'value',name:'事件数',axisLabel:{{fontSize:10}}}},
  series:[{{type:'bar',data:D.dd_timing.vals,barWidth:'60%',
    itemStyle:{{color:p=>p.dataIndex<=1?RED:(p.dataIndex<=3?AMBER:'#9db8e8')}},
    label:{{show:true,position:'top',fontSize:10,formatter:p=>p.value+'例'}},
    markLine:{{silent:true,symbol:'none',label:{{formatter:'中位 18 天',color:RED,position:'end'}},lineStyle:{{color:RED,type:'dashed'}}}}}}
  ]
}});

// 8 谷底时 VIX 分布
echarts.init(document.getElementById('chart_dd_vix')).setOption({{
  tooltip:{{trigger:'axis',formatter:ps=>ps[0].axisValue+'：'+ps[0].value+' 例 ('+((ps[0].value/D.dd_meta.vix_at_valley.n)*100).toFixed(0)+'%)'}},
  grid:{{left:48,right:20,top:30,bottom:36}},
  xAxis:{{type:'category',data:D.dd_vix.labels,axisLabel:{{fontSize:10}}}},
  yAxis:{{type:'value',name:'事件数',axisLabel:{{fontSize:10}}}},
  series:[{{type:'bar',data:D.dd_vix.vals,barWidth:'58%',
    itemStyle:{{color:p=>p.dataIndex===1||p.dataIndex===2?RED:'#9db8e8'}},
    label:{{show:true,position:'top',fontSize:10,formatter:p=>p.value+'例'}},
    markLine:{{silent:true,symbol:'none',label:{{formatter:'中位 20.5',color:RED,position:'end'}},lineStyle:{{color:RED,type:'dashed'}}}}}}
  ]
}});
</script>
</body>
</html>"""

out_path = os.path.join(ROOT, "reports", "vix_low_spx_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)
print("saved:", out_path, f"({len(HTML)/1024:.0f} KB)")
