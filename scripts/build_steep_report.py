# -*- coding: utf-8 -*-
"""US2Y 走弱 + US10Y 走强 时期复盘：KO/PM/MO 表现 研报生成器"""
import json, os, glob
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
OUT = os.path.join(BASE, "..", "reports", "06_陡峭化消费股")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "steep_episodes.json"), encoding="utf-8") as f:
    R = json.load(f)

# ---------- 工具 ----------
def js(o):
    return json.dumps(o, ensure_ascii=False)

def load_yield(name):
    df = pd.read_csv(os.path.join(DATA, f"{name}.csv"), parse_dates=["observation_date"])
    df.columns = ["date", "y"]
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    return df.dropna().reset_index(drop=True)

def load_stock(name):
    cands = [p for p in glob.glob(os.path.join(DATA, name, "*.csv")) if not os.path.basename(p).startswith("BATS_")]
    df = pd.read_csv(sorted(cands)[0], parse_dates=["date"])
    col = "adj_close" if "adj_close" in df.columns else "close"
    return df[["date", col]].rename(columns={col: "px"}).dropna().sort_values("date").reset_index(drop=True)

d2 = load_yield("dgs2")
d10 = load_yield("dgs10")
stocks = {s: load_stock(s) for s in ["ko", "mo", "pm", "gspc", "xlp"]}

# ---------- 图1：月频利差 ----------
m2 = d2.set_index("date")["y"].resample("ME").last().dropna()
m10 = d10.set_index("date")["y"].resample("ME").last().dropna()
mm = pd.DataFrame({"y2": m2, "y10": m10}).dropna()
mm["slope"] = mm["y10"] - mm["y2"]
mm = mm[mm.index <= "2026-07-31"]
slope_dates = [str(p)[:7] for p in mm.index]
slope_vals = [round(v, 3) for v in mm["slope"]]

sig_points = []
for e in R["episodes"]["sig"]:
    ts = pd.Timestamp(e["start"])
    sig_points.append({"name": e["start"][:7], "value": [e["start"][:7], round(float(mm.loc[ts, "slope"]), 3)]})

# ---------- 图2：top12 时期 × 标的 收益热力图 ----------
loose = sorted(R["episodes"]["loose"], key=lambda x: (x["y10_chg"], x["y2_chg"]), reverse=True)[:12]
loose = sorted(loose, key=lambda x: x["start"])
hm_cats = [f"{e['start'][:7]}~{e['end'][:7]}" for e in loose]
hm_data = []
for e in loose:
    for sym, sym_name in [("ko", "KO"), ("mo", "MO"), ("pm", "PM"), ("gspc", "S&P500")]:
        v = e.get(f"ret_{sym}")
        hm_data.append([hm_cats[loose.index(e)], sym_name, round(v, 2) if v is not None else None])

# ---------- 图3：分档 ----------
bucket_keys = ["B1_2Y深降_10Y显著升", "B2_2Y微降_10Y显著升", "B3_2Y深降_10Y微升", "B4_双向弱"]
bucket_series = []
for sym, sym_name in [("ko", "KO"), ("mo", "MO"), ("pm", "PM"), ("gspc", "S&P500")]:
    bucket_series.append({"name": sym_name, "data": [R["buckets"][sym][k]["median"] if R["buckets"][sym][k]["median"] is not None else None for k in bucket_keys]})

# ---------- 图4：案例日频 ----------
def case_daily(start, end, syms=("ko", "mo", "pm", "gspc")):
    d2w = d2[(d2["date"] >= start) & (d2["date"] <= end)]
    d10w = d10[(d10["date"] >= start) & (d10["date"] <= end)]
    merged = pd.merge(d2w[["date", "y"]], d10w[["date", "y"]], on="date", suffixes=("2", "10")).dropna()
    dates = [str(d)[:10] for d in merged["date"]]
    y2v = [round(v, 3) for v in merged["y2"]]
    y10v = [round(v, 3) for v in merged["y10"]]
    rets = {}
    ret_dates = dates
    for sym in syms:
        df = stocks[sym]
        w = df[(df["date"] >= start) & (df["date"] <= end)].copy()
        if w.empty:
            rets[sym] = None
            continue
        base = w.iloc[0]["px"]
        rets[sym] = [round((p / base - 1) * 100, 2) for p in w["px"]]
        ret_dates = [str(d)[:10] for d in w["date"]]
    return {"dates": dates, "y2": y2v, "y10": y10v, "ret_dates": ret_dates, "rets": rets}

case_1998 = case_daily("1998-10-01", "1998-10-31", syms=("ko", "mo", "gspc"))
case_2008 = case_daily("2008-09-02", "2008-10-31", syms=("ko", "mo", "pm", "gspc"))

# ---------- 时期后持有 ----------
def forward_ret(sym, anchor):
    df = stocks[sym]
    out = {}
    for k, tag in [(3, "m3"), (6, "m6"), (12, "m12")]:
        end = anchor + pd.DateOffset(months=k)
        e = df[(df["date"] > anchor) & (df["date"] <= end)]
        s = df[df["date"] <= anchor]
        if e.empty or s.empty:
            out[tag] = None
            continue
        out[tag] = round((e.iloc[-1]["px"] / s.iloc[-1]["px"] - 1) * 100, 2)
    return out

fwd_cases = []
for label, p0, syms in [
    ("1998-10（LTCM 后）", pd.Timestamp("1998-10-31"), ["ko", "mo"]),
    ("2008-10（雷曼后）", pd.Timestamp("2008-10-31"), ["ko", "mo", "pm"]),
    ("2003-06（降息+长端抛售）", pd.Timestamp("2003-06-30"), ["ko", "mo"]),
    ("2020-12~2021-01（疫苗+通胀预期）", pd.Timestamp("2021-01-31"), ["ko", "mo", "pm"]),
]:
    row = {"label": label, "gspc": forward_ret("gspc", p0)}
    for sym in syms:
        row[sym] = forward_ret(sym, p0)
    fwd_cases.append(row)

# ---------- 汇总表 ----------
def cell(v, fmt="{:+.2f}%", na="<td class=na>-</td>"):
    if v is None:
        return na
    cls = "up" if v > 0 else "dn" if v < 0 else ""
    return f"<td class='{cls}'>{fmt.format(v)}</td>"

def cellpct(v, na="<td class=na>-</td>"):
    if v is None:
        return na
    return f"<td>{v}%</td>"

summary_rows_html = []
for k, name in [("loose", "月频·宽松（Δ2Y&lt;0 且 Δ10Y&gt;0）"), ("sig", "月频·显著（2Y≤-10bp 且 10Y≥+10bp）"),
                ("strong", "月频·强显著（±20bp）"), ("rev", "反向·宽松（Δ2Y&gt;0 且 Δ10Y&lt;0）"),
                ("rev_sig", "反向·显著（±10bp）")]:
    s = R["summary"][k]
    wr = "".join(cellpct(s[x].get("win_rate")) for x in ["ko", "mo", "pm", "gspc"])
    md = "".join(cell(s[x].get("median")) for x in ["ko", "mo", "pm", "gspc"])
    summary_rows_html.append(
        f"<tr><td rowspan=2><b>{name}</b></td><td rowspan=2>{s['n_episodes']}</td><td>胜率</td>{wr}</tr>"
        f"<tr><td>收益中位</td>{md}</tr>")

fwd_rows_html = []
for c in fwd_cases:
    rows3 = "".join(cell(c[s]["m3"], "{:+.1f}%") if c.get(s) and c[s]["m3"] is not None else "<td class=na>-</td>" for s in ["ko", "mo", "pm", "gspc"])
    rows6 = "".join(cell(c[s]["m6"], "{:+.1f}%") if c.get(s) and c[s]["m6"] is not None else "<td class=na>-</td>" for s in ["ko", "mo", "pm", "gspc"])
    rows12 = "".join(cell(c[s]["m12"], "{:+.1f}%") if c.get(s) and c[s]["m12"] is not None else "<td class=na>-</td>" for s in ["ko", "mo", "pm", "gspc"])
    fwd_rows_html.append(
        f"<tr><td rowspan=3><b>{c['label']}</b></td><td>后 3 个月</td>{rows3}</tr>"
        f"<tr><td>后 6 个月</td>{rows6}</tr>"
        f"<tr><td>后 12 个月</td>{rows12}</tr>")

loose_rows_html = []
for e in sorted(R["episodes"]["loose"], key=lambda x: x["y10_chg"], reverse=True):
    def rc(sym):
        v = e.get("ret_" + sym)
        if v is None:
            return "<td class=na>-</td>"
        cls = "up" if v > 0 else "dn" if v < 0 else ""
        return f"<td class='{cls}'>{v:+.1f}%</td>"
    xs = e.get("xs_ko")
    xs_td = f"<td class='{'up' if xs > 0 else 'dn'}'>{xs:+.1f}pp</td>" if xs is not None else "<td class=na>-</td>"
    loose_rows_html.append(
        f"<tr><td>{e['start'][:7]} ~ {e['end'][:7]}</td><td>{e['months']}M</td>"
        f"<td class='dn'>{e['y2_chg']:+.0f}bp</td><td class='up'>{e['y10_chg']:+.0f}bp</td>"
        + rc("ko") + rc("mo") + rc("pm") + rc("gspc") + xs_td + "</tr>")

# ---------- KPI ----------
n_loose = R["cond_counts"]["loose"]
n_sig = R["cond_counts"]["sig"]
n_months = R["n_months"]
ko_m = R["summary"]["loose"]["ko"]["median"]
mo_m = R["summary"]["loose"]["mo"]["median"]
pm_m = R["summary"]["loose"]["pm"]["median"]
sp_m = R["summary"]["loose"]["gspc"]["median"]
b1_ko = R["buckets"]["ko"]["B1_2Y深降_10Y显著升"]
b1_gspc = R["buckets"]["gspc"]["B1_2Y深降_10Y显著升"]
xs_b1 = round(b1_ko["median"] - b1_gspc["median"], 2)

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>历史复盘：US2Y 走弱 + US10Y 走强时期 · KO/PM/MO 表现</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#e03131;--green:#0aa06e;--blue:#1e66d6;--amber:#b45309;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1240px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:20px;font-weight:700;}
  .kpi .num.up{color:var(--red);} .kpi .num.dn{color:var(--green);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .verdict{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:15.5px;font-weight:700;line-height:1.7;}
  .verdict .b .hl{color:var(--blue);}
  .verdict .b .hl2{color:var(--red);}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:400px;}
  .chart.sm{height:340px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .warn{background:#fff8ec;border:1px solid #f3dfb6;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#7c4a03;margin-top:10px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
  @media(max-width:900px){.grid2{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
  <h1>历史复盘：US2Y 走弱 + US10Y 走强的日子，KO / PM / MO 怎么走？</h1>
  <div class="meta">数据窗口：1976-07 ~ 2026-07（月频 601 个月）｜收益率口径：<b>2Y 收益率下行（走弱）、10Y 收益率上行（走强）</b>，即曲线陡峭化｜数据源：FRED（DGS2/DGS10）+ Yahoo Finance 日线</div>
  <div class="kpis">
    <div class="kpi"><div class="num">@@N_LOOSE@@/@@N_MONTHS@@</div><div class="lab">宽松口径满足月份数（占比 @@PCT_LOOSE@@%）</div></div>
    <div class="kpi"><div class="num">@@N_SIG@@</div><div class="lab">显著期（2Y≤-10bp 且 10Y≥+10bp）例数</div></div>
    <div class="kpi"><div class="num">KO @@KO_M@@%</div><div class="lab">宽松期 KO 收益中位数</div></div>
    <div class="kpi"><div class="num">MO @@MO_M@@%</div><div class="lab">宽松期 MO 收益中位数</div></div>
    <div class="kpi"><div class="num">PM @@PM_M@@%</div><div class="lab">宽松期 PM 收益中位数</div></div>
    <div class="kpi"><div class="num">SP @@SP_M@@%</div><div class="lab">同期标普500 收益中位数</div></div>
  </div>
  <div class="verdict">
    <div class="t">核心结论</div>
    <div class="b">历史上「2Y 降 + 10Y 升」<span class="hl">确实存在但极稀有</span>：50 年只有约 6% 的月份方向符合，真正「2Y 明显降 &amp; 10Y 明显升」只有 <span class="hl2">1998-10（LTCM 后）和 2008-09~10（雷曼后）</span>两段——都是「联储紧急降息 + 长端通胀/供给担忧」的危机型熊陡。<br>
    消费股整体<span class="hl">没有系统性防御优势</span>（宽松期 KO 中位 +0.5%、MO -0.6%、PM -0.7%，全部跑输标普 +1.3%）；但 <span class="hl2">危机型深陡（2Y 深降 + 10Y 显著升）时期 KO 大幅跑赢</span>：1998-10 KO +20.1% vs 标普 +11.4%，2008-09~10 KO -14.6% vs 标普 -24.2%。</div>
  </div>
</div>

<div class="card">
  <h2>一、50 年利差全景：这种组合有多罕见？</h2>
  <div class="chart" id="c1"></div>
  <div class="note">蓝线 = 10Y-2Y 利差（%）。紫色菱形 = 显著陡峭期（1998-10、2008-10）。"2Y 降 + 10Y 升"意味着曲线在该月走陡的同时短端下行，历史上多集中在危机后的"政策宽松 + 长端担忧"窗口。</div>
</div>

<div class="card">
  <h2>二、消费股在「2Y 弱 + 10Y 强」时期的收益</h2>
  <div class="scroll"><table>
    <tr><th>口径</th><th>时期数</th><th></th><th>KO</th><th>MO</th><th>PM</th><th>S&P500</th></tr>
    @@SUMMARY_ROWS@@
  </table></div>
  <div class="note">可见：宽松口径下消费股中位收益≈0、胜率≈50%，<b>系统性跑输标普</b>；反向口径（2Y 升 + 10Y 降，即价格口径的"2Y 弱 10Y 强"）下 PM 反而最好。PM 2008-03 才上市，早期时期无数据。</div>
  <h3>按幅度分档：真正的"熊陡"（2Y 深降 + 10Y 显著升）才是消费股的避风港</h3>
  <div class="chart sm" id="c3"></div>
  <div class="note">分档规则（月频宽松 35 期）：B1=2Y 累计降≥10bp 且 10Y 升≥10bp（2 期）；B2=2Y 降&lt;10bp 且 10Y 升≥10bp（12 期）；B3=2Y 降≥10bp 且 10Y 升&lt;10bp（10 期）；B4=双向弱波动（11 期）。柱 = 各档收益中位数。</div>
</div>

<div class="card">
  <h2>三、显著期全解析：1998-10 与 2008-09~10</h2>
  <div class="grid2">
    <div class="chart sm" id="c4a"></div>
    <div class="chart sm" id="c4b"></div>
  </div>
  <div class="note">左：1998-10（LTCM 危机后联储 3 连降息，2Y -18bp、10Y +20bp）；右：2008-09~10（雷曼倒闭，2Y -44bp、10Y +16bp）。绿/红线为 2Y/10Y 日值（左轴），其余为个股自段首归一化收益 %（右轴）。</div>
  <div class="keypoint">两个危机型熊陡中，消费股都是显著避风港：1998-10 KO +20.1% / MO +10.0% vs 标普 +11.4%；2008-09~10 KO -14.6% / MO -8.7% / PM -19.9% vs 标普 -24.2%。原因：短端深降=联储紧急宽松 + 市场恐慌，防御性现金流资产（类债券消费股）获避险资金流入，跑赢大盘。</div>
</div>

<div class="card">
  <h2>四、温和陡峭期：为什么消费股反而跑输？</h2>
  <div class="chart" id="c2"></div>
  <div class="note">12 个「2Y 微降 + 10Y 显著升」时期的区间收益热力图（按 10Y 升幅取前 12）。这种"非危机"陡峭多由增长/通胀预期驱动：10Y 上行抬升贴现率，直接压 KO/PM/MO 这类<b>长久期类债券资产</b>的估值，同时 2Y 下行意味着风险偏好回升、资金流向成长——两头挤压，故消费股中位跑输标普约 1pp。</div>
</div>

<div class="card">
  <h2>五、陡峭期之后的持有表现</h2>
  <div class="scroll"><table>
    <tr><th>时期</th><th></th><th>KO</th><th>MO</th><th>PM</th><th>S&P500</th></tr>
    @@FWD_ROWS@@
  </table></div>
  <div class="note">仅 4 个代表时期，样本极小，仅作观察：危机型陡峭（1998-10、2008-10）之后 3-6 个月消费股与大盘一同反弹；2021-01 之后 12 个月消费股跑输（成长风格主导）。</div>
</div>

<div class="card">
  <h2>六、全部 35 个宽松期明细</h2>
  <div class="scroll" style="max-height:460px;overflow-y:auto;"><table>
    <tr><th>时期</th><th>长度</th><th>2Y 变化</th><th>10Y 变化</th><th>KO</th><th>MO</th><th>PM</th><th>S&P500</th><th>KO 超额</th></tr>
    @@LOOSE_ROWS@@
  </table></div>
  <div class="note">按 10Y 升幅降序。红涨绿跌。KO 超额 = 区间内 KO 收益 − 标普收益（pp）。</div>
</div>

<div class="card">
  <h2>结论与机制</h2>
  <h3>回答：历史上有没有「US2Y 走弱、US10Y 走强」的时候？</h3>
  <p><b>有，但非常少。</b>1976 年以来月频满足「2Y 降 + 10Y 升」仅 38/601 个月（6.3%），且多数幅度很小（2Y 降 &lt;10bp、10Y 升 &lt;15bp）。真正显著的只有 <b>1998-10</b> 与 <b>2008-09~10</b> 两段，均为危机后「联储紧急降息（2Y 深降）+ 长端通胀/供给/财政担忧（10Y 升）」的熊陡窗口。若按价格口径理解（2Y 弱=收益率升、10Y 强=收益率降），则是"2Y 升 + 10Y 降"的平坦化，该组合稍常见（34 期），见汇总表。</p>
  <h3>这种时候消费股（KO/PM/MO）怎么样？</h3>
  <p><b>整体：无系统性防御优势，温和跑输大盘。</b>宽松期三只股票胜率 49-54%、中位收益 -0.7%~+0.5%，全部低于标普中位 +1.3%。机制：<b>10Y 上行抬升贴现率</b>，对 KO/PM/MO 这类高股息、低增长、长久期的"类债券"资产估值直接构成压制；同时 <b>2Y 下行通常伴随风险偏好修复</b>，资金流向成长/周期，进一步削弱防御股相对吸引力。</p>
  <p><b>例外：危机型深陡时期（2Y 深降 + 10Y 显著升）消费股是明确避风港</b>（KO 中位 +2.8% vs 标普 -6.4%，超额约 +9pp）。此时市场恐慌压过估值逻辑，防御性现金流的避险属性主导，KO 相对抗跌（2008 段 KO -14.6% vs 标普 -24.2%），1998-10 甚至绝对上涨 +20.1%。</p>
  <div class="warn">局限性：显著期仅 2 例，统计功效极低；月频定义依赖月末值，边界有噪音；未计交易成本；KO/PM/MO 仅代表大市值成熟消费股，不适用于所有消费板块。周频口径（宽松 156 周）结论一致：消费股胜率 52-57%、中位 ±0.5%，无系统性超额。</div>
</div>

</div>
<script>
const hmData = @@HM_DATA@@;
const hmCats = @@HM_CATS@@;
const bucketKeys = @@BUCKET_KEYS@@;
const bucketSeries = @@BUCKET_SERIES@@;
const slopeDates = @@SLOPE_DATES@@;
const slopeVals = @@SLOPE_VALS@@;
const sigPoints = @@SIG_POINTS@@;
const c1998 = @@C1998@@;
const c2008 = @@C2008@@;

function mk(id){ return echarts.init(document.getElementById(id)); }
const RED="#e03131", GREEN="#0aa06e", BLUE="#1e66d6", AMBER="#b45309", PURPLE="#7048e8", GRAY="#9aa4b2";

// 图1 利差
const c1 = mk('c1');
c1.setOption({
  tooltip:{trigger:'axis'},
  grid:{left:55,right:30,top:35,bottom:45},
  xAxis:{type:'category',data:slopeDates,axisLabel:{show:false},axisTick:{show:false}},
  yAxis:{type:'value',name:'10Y-2Y (%)'},
  dataZoom:[{type:'slider',height:18,bottom:6}],
  series:[{
    name:'10Y-2Y 利差',type:'line',data:slopeVals,symbol:'none',
    lineStyle:{color:BLUE,width:1.2},
    markPoint:{data:sigPoints.map(p=>({coord:[p.value[0],p.value[1]],value:p.name,itemStyle:{color:PURPLE},symbol:'diamond',symbolSize:14})),
      label:{show:true,fontSize:9,formatter:p=>p.name}}
  }]
});

// 图2 top12 热力图
const c2 = mk('c2');
c2.setOption({
  tooltip:{formatter:p=>p.data[2]==null?'-':`${p.data[1]} · ${p.data[0]}: ${p.data[2]}%`},
  grid:{left:70,right:30,top:40,bottom:80},
  xAxis:{type:'category',data:hmCats,axisLabel:{rotate:40,fontSize:10}},
  yAxis:{type:'category',data:['S&P500','PM','MO','KO']},
  visualMap:{min:-25,max:25,inRange:{color:['#0aa06e','#f3f4f6','#e03131']},orient:'horizontal',left:'center',bottom:0,text:['涨','跌'],textStyle:{fontSize:10}},
  series:[{type:'heatmap',data:hmData.map(d=>[d[0],d[2],d[2]]),label:{show:true,formatter:p=>p.value[2]==null?'-':p.value[2].toFixed(1)+'%',fontSize:10}}]
});

// 图3 分档
const c3 = mk('c3');
c3.setOption({
  tooltip:{trigger:'axis'},
  legend:{top:0},
  grid:{left:50,right:20,top:40,bottom:30},
  xAxis:{type:'category',data:bucketKeys},
  yAxis:{type:'value',name:'收益中位数 %'},
  series:bucketSeries.map(s=>({
    name:s.name,type:'bar',data:s.data,barGap:'10%',
    itemStyle:{color:{'KO':RED,'MO':AMBER,'PM':PURPLE,'S&P500':BLUE}[s.name],borderRadius:[3,3,0,0]}
  }))
});

// 图4a 1998-10
const c4a = mk('c4a');
c4a.setOption({
  title:{text:'1998-10 · LTCM 危机后（2Y -18bp / 10Y +20bp）',fontSize:13,left:0},
  tooltip:{trigger:'axis'},
  legend:{top:22},
  grid:{left:45,right:50,top:55,bottom:25},
  xAxis:{type:'category',data:c1998.dates,axisLabel:{interval:2}},
  yAxis:[{type:'value',name:'收益率 %',scale:true},{type:'value',name:'收益 %',scale:true,splitLine:{show:false}}],
  series:[
    {name:'2Y',type:'line',data:c1998.y2,symbol:'none',lineStyle:{color:GREEN,width:1.2},yAxisIndex:0},
    {name:'10Y',type:'line',data:c1998.y10,symbol:'none',lineStyle:{color:RED,width:1.2},yAxisIndex:0},
    {name:'KO',type:'line',data:c1998.rets.ko,symbol:'none',lineStyle:{color:BLUE,width:1.6},yAxisIndex:1},
    {name:'MO',type:'line',data:c1998.rets.mo,symbol:'none',lineStyle:{color:AMBER,width:1.6},yAxisIndex:1},
    {name:'S&P500',type:'line',data:c1998.rets.gspc,symbol:'none',lineStyle:{color:GRAY,width:1.2,type:'dashed'},yAxisIndex:1}
  ]
});
// 图4b 2008
const c4b = mk('c4b');
c4b.setOption({
  title:{text:'2008-09~10 · 雷曼倒闭（2Y -44bp / 10Y +16bp）',fontSize:13,left:0},
  tooltip:{trigger:'axis'},
  legend:{top:22},
  grid:{left:45,right:50,top:55,bottom:25},
  xAxis:{type:'category',data:c2008.dates,axisLabel:{interval:5}},
  yAxis:[{type:'value',name:'收益率 %',scale:true},{type:'value',name:'收益 %',scale:true,splitLine:{show:false}}],
  series:[
    {name:'2Y',type:'line',data:c2008.y2,symbol:'none',lineStyle:{color:GREEN,width:1.2},yAxisIndex:0},
    {name:'10Y',type:'line',data:c2008.y10,symbol:'none',lineStyle:{color:RED,width:1.2},yAxisIndex:0},
    {name:'KO',type:'line',data:c2008.rets.ko,symbol:'none',lineStyle:{color:BLUE,width:1.6},yAxisIndex:1},
    {name:'MO',type:'line',data:c2008.rets.mo,symbol:'none',lineStyle:{color:AMBER,width:1.6},yAxisIndex:1},
    {name:'PM',type:'line',data:c2008.rets.pm,symbol:'none',lineStyle:{color:PURPLE,width:1.6},yAxisIndex:1},
    {name:'S&P500',type:'line',data:c2008.rets.gspc,symbol:'none',lineStyle:{color:GRAY,width:1.2,type:'dashed'},yAxisIndex:1}
  ]
});
window.addEventListener('resize',()=>{[c1,c2,c3,c4a,c4b].forEach(c=>c.resize())});
</script>
</body>
</html>"""

html = (TEMPLATE
        .replace("@@N_LOOSE@@", str(n_loose))
        .replace("@@N_MONTHS@@", str(n_months))
        .replace("@@PCT_LOOSE@@", f"{round(n_loose / n_months * 100, 1)}")
        .replace("@@N_SIG@@", str(n_sig))
        .replace("@@KO_M@@", f"{ko_m:+.1f}")
        .replace("@@MO_M@@", f"{mo_m:+.1f}")
        .replace("@@PM_M@@", f"{pm_m:+.1f}")
        .replace("@@SP_M@@", f"{sp_m:+.1f}")
        .replace("@@SUMMARY_ROWS@@", "\n    ".join(summary_rows_html))
        .replace("@@FWD_ROWS@@", "\n    ".join(fwd_rows_html))
        .replace("@@LOOSE_ROWS@@", "\n    ".join(loose_rows_html))
        .replace("@@HM_DATA@@", js(hm_data))
        .replace("@@HM_CATS@@", js(hm_cats))
        .replace("@@BUCKET_KEYS@@", js(bucket_keys))
        .replace("@@BUCKET_SERIES@@", js(bucket_series))
        .replace("@@SLOPE_DATES@@", js(slope_dates))
        .replace("@@SLOPE_VALS@@", js(slope_vals))
        .replace("@@SIG_POINTS@@", js(sig_points))
        .replace("@@C1998@@", js(case_1998))
        .replace("@@C2008@@", js(case_2008)))

with open(os.path.join(OUT, "steep_ko_pm_mo_report.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("报告已生成:", os.path.join(OUT, "steep_ko_pm_mo_report.html"))
