# -*- coding: utf-8 -*-
"""小麦各品种历史单周变动 TOP20 报告（79号附属·按用户口径修正版）"""
import json, os, html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(BASE, "results", "cot")
OD = os.path.join(BASE, "reports", "79_CFTC农产品持仓32年_1995_2026")

d = json.load(open(os.path.join(RD, "wheat_weekly_top20_20260901.json"), encoding="utf-8"))
fams = d["families"]

RED, GREEN, BLUE, ORANGE, GREY = "#C8102E", "#009E73", "#0072B2", "#D55E00", "#666666"

def fm(v, dash="—"):
    return dash if v is None else f"{v:,}"

def sign(v):
    if v is None: return "—"
    s = "+" if v > 0 else ("−" if v < 0 else "±")
    return f"{s}{abs(v):,}"

def col_of(v):
    return RED if (v or 0) > 0 else (GREEN if (v or 0) < 0 else GREY)

# 每个品种的三榜 HTML 块
def block_for(label, fam):
    def rank_table(title, items, key, metric, sub):
        rows = []
        for i, r in enumerate(items, 1):
            lvl = {"dl": r["l_after"], "ds": r["s_after"], "dnet": r["net"]}[key]
            p = {"dl": r["prev_l"], "ds": r["prev_s"], "dnet": r["prev_net"]}[key]
            rows.append(f"""<tr>
            <td class="rk">{i:02d}</td>
            <td class="dt">{r["date"]}</td>
            <td class="chg" style="color:{col_of(r[key])}">{sign(r[key])}</td>
            <td>{fm(lvl)}</td>
            <td class="dim">{fm(p)}</td>
            <td class="dim">{fm(r["net"])}</td></tr>""")
        return f"""<h4 class="bt">{title} <span class="cnt">{sub}</span></h4>
        <div class="tw"><table>
        <thead><tr><th>#</th><th class="l">日期</th><th>变动</th><th>变动后</th><th>变动前</th><th>净多</th></tr></thead>
        <tbody>{''.join(rows)}</tbody></table></div>"""

    blk = []
    blk.append(rank_table("非商业多头增仓 TOP20", fam["long_up"], "dl", "多头",
                          f"正数=本周多头增仓（官方 Change 列）"))
    blk.append(rank_table("非商业空头砍仓 TOP20", fam["short_cut"], "ds", "空头",
                          f"最负=本周空头减仓/回补最多"))
    blk.append(rank_table("净多头变化 TOP20", fam["net_up"], "dnet", "净多",
                          f"净多增加最多（多增+空减）"))
    return "\n".join(blk)

# Tab 结构
tabs = []
panels = []
for i, (label, fam) in enumerate(fams.items()):
    active = " active" if i == 0 else ""
    tabs.append(f'<button class="tab{active}" data-t="t{i}">{html.escape(label)}<span class="tc">{fam["n"]}周<br>{fam["start"]}~{fam["end"]}</span></button>')
    panels.append(f'<div class="panel{active}" id="t{i}">{block_for(label, fam)}</div>')

TAB_BTNS = "\n".join(tabs)
PANELS = "\n".join(panels)

# 结论要点：跨品种 Top 对比（各品种自己的 #1）
headlines = []
for label, fam in fams.items():
    a = fam["long_up"][0]
    b = fam["short_cut"][0]
    c = fam["net_up"][0]
    headlines.append(f"""<li><b>{html.escape(label)}</b>（{fam["start"]}~{fam["end"]}，{fam["n"]}周）：多头单周最大增仓 <b class="r">{sign(a["dl"])}</b> @ {a["date"]}；空头单周最大砍仓 <b class="g">{sign(b["ds"])}</b> @ {b["date"]}；净多单周最大变化 <b class="r">{sign(c["dnet"])}</b> @ {c["date"]}。</li>""")
HEAD = "\n".join(headlines)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>小麦各品种历史单周变动 TOP20 · CFTC COT</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f7f7f5;color:#1a1a1a;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.65}}
.wrap{{max-width:1080px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:24px;margin:0 0 6px}}
.sub{{color:#666;font-size:13px;margin-bottom:3px}}
h2{{font-size:18px;margin:28px 0 10px;padding-left:11px;border-left:4px solid {BLUE}}}
h4.bt{{font-size:14px;margin:20px 0 8px;color:#1a1a1a}}
h4.bt .cnt{{font-size:11px;color:#999;font-weight:400;margin-left:8px}}
.r{{color:{RED}}}
.g{{color:{GREEN}}}
.tabs{{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 4px}}
.tab{{background:#fff;border:1px solid #ddd9d0;border-radius:7px;padding:8px 12px;font-size:12.5px;font-weight:600;color:#444;cursor:pointer;text-align:left;line-height:1.35}}
.tab .tc{{display:block;font-size:10px;font-weight:400;color:#999;margin-top:2px}}
.tab.active{{background:{BLUE};color:#fff;border-color:{BLUE}}}
.tab.active .tc{{color:#dce9f5}}
.panel{{display:none}}
.panel.active{{display:block}}
.tw{{overflow-x:auto;background:#fff;border:1px solid #e6e4df;border-radius:8px}}
table{{border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}}
th{{background:#f0efe9;color:#333;font-weight:600;padding:7px 10px;text-align:right;border-bottom:1.5px solid #ddd9d0;font-size:11.5px}}
th.l{{text-align:left}}
td{{padding:7px 10px;text-align:right;border-bottom:1px solid #f0efea;font-variant-numeric:tabular-nums}}
td.rk{{color:#bbb;font-weight:700;width:34px}}
td.dt{{text-align:left;font-variant-numeric:tabular-nums}}
td.chg{{font-weight:700}}
.dim{{color:#888;font-size:11.5px}}
.head{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px 18px;font-size:13px}}
.head li{{margin:7px 0}}
.note{{background:#fffdf5;border:1px solid #e8dcc0;border-left:4px solid #E69F00;border-radius:6px;padding:12px 15px;font-size:12.5px;margin:16px 0 0}}
.foot{{margin-top:26px;font-size:11px;color:#999;border-top:1px solid #e6e4df;padding-top:10px}}
</style></head><body><div class="wrap">

<h1>小麦各品种 · 历史单周变动 TOP20</h1>
<div class="sub">CFTC COT Futures-Only ｜ 逐品种从全部历史周（1995-2026）中取单周变动排名 ｜ 截至 2026-09-01</div>
<div class="sub">榜单口径：<b>① 非商业多头单周增仓</b>（官方 Change 列，正数=增仓）<b>② 非商业空头单周砍仓</b>（最负=空头回补最多）<b>③ 净多头单周变化</b>（多增+空减的净效应）</div>

<h2>每品种 #1 一览</h2>
<div class="head"><ul>{HEAD}</ul></div>

<h2>逐品种 TOP20</h2>
<div class="tabs">{TAB_BTNS}</div>
{PANELS}

<div class="note"><b>口径说明</b>：<br>
· 变动优先取 CFTC 官方 <i>Change in Noncommercial-Long/Short (All)</i> 列（各品种序列内逐周一致性），官方缺失时用连续周持仓差补（±1 张舍入差异不影响排名）。<br>
· 「变动后/变动前」为当周变动基准下的持仓水平（多头增仓榜看多头张数、空头砍仓榜看空头张数、净多榜看净头寸）。<br>
· 1995 年前 4 周为交易所简写名（CBT/KCBT/MGE），已并入对应链；黑海金融小麦仅 2018-2022 上市、白小麦 1995-1998、杜伦麦 1998 年 24 周，样本短，榜单为"上市期内"单周记录。<br>
· 历史早期（1995-1998）CBOT 小麦为单一合约（1996-01-30 多头单周 +56,953 系官方原始记录），2013-12 起 SRW/HRW 分列，跨度含口径切换，绝对水平不可跨段直比，排名按各段自身记录。</div>

<div class="foot">数据源：CFTC COT Futures-Only（deahistfo 1995-2026，7 序列 × 1642/199/93/24 周）｜ 明细 results/cot/wheat_weekly_top20_20260901.csv ｜ 脚本 scripts/wheat_weekly_top20_20260905.py</div>
</div>
<script>
document.querySelectorAll('.tab').forEach(function(t){{
  t.addEventListener('click',function(){{
    document.querySelectorAll('.tab').forEach(function(x){{x.classList.remove('active')}});
    document.querySelectorAll('.panel').forEach(function(p){{p.classList.remove('active')}});
    t.classList.add('active');
    document.getElementById(t.dataset.t).classList.add('active');
  }});
}});
</script>
</body></html>"""

p = os.path.join(OD, "小麦各品种历史单周变动TOP20_20260901.html")
open(p, "w", encoding="utf-8").write(HTML)
print("written", p, len(HTML), "bytes")