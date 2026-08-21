# -*- coding: utf-8 -*-
"""构建研报：KO 日线 RSI14 进入超买区间后的 T+5 / T+10 表现（分阶段事件研究）
读取 results/ko_rsi_overbought.json + data/ko 原始 csv（生成时序）
输出 reports/17_KO超买/ko_rsi_overbought_report.html
静默写盘：只打印 written 路径与体积。
"""
import os, json, glob, re
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(ROOT, "reports", "17_KO超买")
os.makedirs(OUTD, exist_ok=True)

with open(os.path.join(RES, "ko_rsi_overbought.json"), encoding="utf-8") as f:
    D = json.load(f)

# ---------- 时序数据（供图表） ----------
kf = [p for p in glob.glob(os.path.join(ROOT, "data", "ko", "*.csv"))
      if not os.path.basename(p).startswith("BATS_")][0]
ko = pd.read_csv(kf, parse_dates=["date"]).sort_values("date").reset_index(drop=True)

def rsi_wilder(close, p=14):
    d = close.diff(); g = d.clip(lower=0); l = -d.clip(upper=0)
    return 100 - 100 / (1 + g.ewm(alpha=1/p, adjust=False).mean() / l.ewm(alpha=1/p, adjust=False).mean())

ko["rsi14"] = rsi_wilder(ko["adj_close"], 14)
ko["rsi6"] = rsi_wilder(ko["adj_close"], 6)
ko = ko.set_index("date")

# 全历史日线（供主图 category 轴）：[date, price, rsi14]
dailyD = [[str(d.date()), round(float(r["adj_close"]), 2), round(float(r["rsi14"]), 1)]
          for d, r in ko.iterrows()]
recent = ko.loc["2025-06-01":].reset_index()
recentD = [[str(r["date"].date()), round(float(r["adj_close"]), 2),
            round(float(r["rsi14"]), 1), round(float(r["rsi6"]), 1)]
           for _, r in recent.iterrows()]

# ---------- 派生统计 ----------
ev = D["events"]
STAGE_CN = {"A_pre": "疫情前(1995~2020-02)", "B_post": "疫情及股灾后(2020-02~2022-12)",
            "C_bull": "本轮牛市(2023~)"}

def pct(v, nd=2):
    return "—" if v is None else f"{v:+.{nd}f}"

def stage_rows():
    rows = []
    base = D["baseline_all_days"]
    for st in ["A_pre", "B_post", "C_bull"]:
        b = D["by_stage"][st]
        rows.append((STAGE_CN[st], b, ""))
    rows.append(("全历史基率(所有交易日)", base, "base"))
    html = []
    for name, b, tag in rows:
        t5, t10, t20 = b["T5"], b["T10"], b["T20"]
        if t5.get("n", 0) == 0: continue
        cls = " class='baserow'" if tag else ""
        html.append(
            f"<tr{cls}><td class='nowrap'><b>{name}</b></td><td>{t5['n']}</td>"
            f"<td class='{ 'up' if t5['mean']>0 else 'dn'}'>{pct(t5['mean'])}%</td><td>{t5['win']}%</td>"
            f"<td class='{ 'up' if t10['mean']>0 else 'dn'}'>{pct(t10['mean'])}%</td><td>{t10['win']}%</td>"
            f"<td class='{ 'up' if t20['mean']>0 else 'dn'}'>{pct(t20['mean'])}%</td><td>{t20['win']}%</td></tr>")
    return "".join(html)

def sub_rows():
    html = []
    order = ["B1 暴跌+V反(2020-02~05)", "B2 放水牛(2020-06~2021)", "B3 2022熊市", "C 本轮牛市(2023~)"]
    for ss in order:
        b = D["by_substage"].get(ss)
        if not b: continue
        t5, t10, t20 = b["T5"], b["T10"], b["T20"]
        if t5.get("n", 0) == 0: continue
        html.append(
            f"<tr><td class='nowrap'><b>{ss}</b></td><td>{t5['n']}</td>"
            f"<td class='{'up' if t5['mean']>0 else 'dn'}'>{pct(t5['mean'])}%</td><td>{t5['win']}%</td>"
            f"<td class='{'up' if t10['mean']>0 else 'dn'}'>{pct(t10['mean'])}%</td><td>{t10['win']}%</td>"
            f"<td class='{'up' if t20['mean']>0 else 'dn'}'>{pct(t20['mean'])}%</td><td>{t20['win']}%</td></tr>")
    return "".join(html)

def bull_year_rows():
    html = []
    for y, b in D["bull_by_year"].items():
        t5, t10, t20 = b["T5"], b["T10"], b["T20"]
        if t5.get("n", 0) == 0: continue
        ex5, ex10, ex20 = b["T5_ex_spy"], b["T10_ex_spy"], b["T20_ex_spy"]
        html.append(
            f"<tr><td class='nowrap'><b>{y}</b></td><td>{t5['n']}</td>"
            f"<td class='{'up' if t5['mean']>0 else 'dn'}'>{pct(t5['mean'])}%</td><td>{t5['win']}%</td>"
            f"<td class='{'na' if ex5.get('n',0)==0 else ('up' if ex5['mean']>0 else 'dn')}'>{pct(ex5.get('mean'))}%</td>"
            f"<td class='{'up' if t10['mean']>0 else 'dn'}'>{pct(t10['mean'])}%</td><td>{t10['win']}%</td>"
            f"<td class='{'na' if ex10.get('n',0)==0 else ('up' if ex10['mean']>0 else 'dn')}'>{pct(ex10.get('mean'))}%</td>"
            f"<td class='{'up' if t20['mean']>0 else 'dn'}'>{pct(t20['mean'])}%</td><td>{t20['win']}%</td>"
            f"<td class='{'na' if ex20.get('n',0)==0 else ('up' if ex20['mean']>0 else 'dn')}'>{pct(ex20.get('mean'))}%</td></tr>")
    return "".join(html)

def pre_year_rows():
    html = []
    py = D["pre_by_year"]
    for y in sorted(py, key=int):
        b = py[y]; t5, t10, t20 = b["T5"], b["T10"], b["T20"]
        if t5.get("n", 0) == 0: continue
        html.append(
            f"<tr><td class='nowrap'>{y}</td><td>{t5['n']}</td>"
            f"<td class='{'up' if t5['mean']>0 else 'dn'}'>{pct(t5['mean'])}%</td><td>{t5['win']}%</td>"
            f"<td class='{'up' if t10['mean']>0 else 'dn'}'>{pct(t10['mean'])}%</td><td>{t10['win']}%</td>"
            f"<td class='{'up' if t20['mean']>0 else 'dn'}'>{pct(t20['mean'])}%</td><td>{t20['win']}%</td></tr>")
    return "".join(html)

# 逐年 T+5 均值（图表数据）
yearT5 = []
py = D["pre_by_year"]
for y in sorted(py, key=int):
    t5 = py[y]["T5"]
    if t5.get("n", 0) > 0:
        yearT5.append({"y": int(y), "label": y, "n": t5["n"], "mean": t5["mean"], "win": t5["win"], "stage": "pre"})
for y, b in D["bull_by_year"].items():
    t5 = b["T5"]
    if t5.get("n", 0) > 0:
        yearT5.append({"y": int(y[:4]), "label": y, "n": t5["n"], "mean": t5["mean"], "win": t5["win"], "stage": "bull"})

def excess_rows():
    html = []
    for st in ["A_pre", "B_post", "C_bull"]:
        b = D["by_stage"][st]
        def cell(k):
            s = b.get(k) or {}
            if s.get("n", 0) == 0: return "<td class='na'>—</td>"
            return f"<td class='{'up' if s['mean']>0 else 'dn'}'>{pct(s['mean'])}%</td>"
        html.append(f"<tr><td class='nowrap'><b>{STAGE_CN[st]}</b></td>"
                    f"{cell('T5_ex_spy')}{cell('T10_ex_spy')}{cell('T20_ex_spy')}"
                    f"{cell('T5_ex_xlp')}{cell('T10_ex_xlp')}{cell('T20_ex_xlp')}</tr>")
    return "".join(html)

# 事件明细表（全部 161 个，倒序）
STAGE_TAG = {"A_pre": "st-a", "B_post": "st-b", "C_bull": "st-c"}
STAGE_SHORT = {"A_pre": "疫情前", "B_post": "疫情后", "C_bull": "牛市"}
ev_rows = []
for e in sorted(ev, key=lambda r: r["date"], reverse=True):
    def fmt(v):
        if v is None: return "<td class='na'>—</td>"
        return f"<td class='{'up' if v>0 else 'dn'}'>{v:+.2f}%</td>"
    ev_rows.append(
        f"<tr><td class='nowrap'>{e['date']}</td><td>{e['rsi']}</td><td>{e['px']}</td>"
        f"<td><span class='st {STAGE_TAG[e['stage']]}'>{STAGE_SHORT[e['stage']]}</span></td>"
        f"{fmt(e['fwd5'])}{fmt(e['fwd10'])}{fmt(e['fwd20'])}"
        f"<td class='na'>{pct(e['spy5'])}%</td><td class='na'>{pct(e['spy10'])}%</td><td class='na'>{pct(e['spy20'])}%</td></tr>")
ev_rows_html = "".join(ev_rows)

cur = D["current"]
ea = D["event_stats_all"]; bs = D["by_stage"]
r75 = D["rsi75_robust"]; cd10 = D["event_stats_cd10"]

DATA = {
    "dailyD": dailyD, "recentD": recentD, "events": ev, "yearT5": yearT5,
    "stageMark": [
        next(d[0] for d in dailyD if d[0] >= "2020-02-20"),
        next(d[0] for d in reversed(dailyD) if d[0] <= "2022-12-31"),
        next(d[0] for d in dailyD if d[0] >= "2023-01-01"),
    ],
    "stageBar": {st: {"t5m": bs[st]["T5"]["mean"], "t5w": bs[st]["T5"]["win"],
                      "t10m": bs[st]["T10"]["mean"], "t10w": bs[st]["T10"]["win"],
                      "t20m": bs[st]["T20"]["mean"], "t20w": bs[st]["T20"]["win"],
                      "n": bs[st]["T5"]["n"]} for st in ["A_pre", "B_post", "C_bull"]},
    "baseline": {"t5m": D["baseline_all_days"]["T5"]["mean"], "t5w": D["baseline_all_days"]["T5"]["win"],
                 "t10m": D["baseline_all_days"]["T10"]["mean"], "t10w": D["baseline_all_days"]["T10"]["win"],
                 "t20m": D["baseline_all_days"]["T20"]["mean"], "t20w": D["baseline_all_days"]["T20"]["win"]},
}

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, float) and np.isnan(o): return None
    return o

DATA = clean(DATA)

def rob_rows():
    ea = D["event_stats_all"]; cd = D["event_stats_cd10"]; r75 = D["rsi75_robust"]
    def m(s, k):
        t = s[k]
        return f"{pct(t['mean'])}% / {t['win']}%"
    return ("".join(
        f"<tr><td>全部上穿70事件（含密集重复）</td><td>{ea['T5']['n']}</td><td>{m(ea,'T5')}</td><td>{m(ea,'T10')}</td><td>{m(ea,'T20')}</td></tr>"
        f"<tr><td>cooldown=10 交易日去重</td><td>{cd['T5']['n']}</td><td>{m(cd,'T5')}</td><td>{m(cd,'T10')}</td><td>{m(cd,'T20')}</td></tr>"
        f"<tr><td>仅深超买（上穿 75 首日）</td><td>{r75['T5']['n']}</td><td class=\"dn\">{m(r75,'T5')}</td><td class=\"dn\">{m(r75,'T10')}</td><td class=\"dn\">{m(r75,'T20')}</td></tr>"))

with open(os.path.join(ROOT, "scripts", "__ko_rsi_tpl.html"), encoding="utf-8") as f:
    tpl = f.read()

html = tpl
html = html.replace("{{stage_rows}}", stage_rows())
html = html.replace("{{sub_rows}}", sub_rows())
html = html.replace("{{bull_year_rows}}", bull_year_rows())
html = html.replace("{{pre_year_rows}}", pre_year_rows())
html = html.replace("{{excess_rows}}", excess_rows())
html = html.replace("{{rob_rows}}", rob_rows())
html = html.replace("{{ev_rows}}", ev_rows_html)
html = html.replace("__ECHARTS__", open(os.path.join(ROOT, "scripts", "__echarts_block.txt"), encoding="utf-8").read())
html = html.replace("__DATA_JSON__", json.dumps(DATA, ensure_ascii=False, allow_nan=False))

out = os.path.join(OUTD, "ko_rsi_overbought_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out} size={os.path.getsize(out)}")
