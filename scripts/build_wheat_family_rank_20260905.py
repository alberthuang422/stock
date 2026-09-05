# -*- coding: utf-8 -*-
"""小麦家族排行榜（79号附属）：非商多头增仓 / 非商空头砍仓 / 净多头变化 三榜"""
import json, os, html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(BASE, "results", "cot")
OD = os.path.join(BASE, "reports", "79_CFTC农产品持仓32年_1995_2026")

d = json.load(open(os.path.join(RD, "wheat_family_rank_20260901.json"), encoding="utf-8"))
rows = d["rows"]
ASOF = d["asof"]

RED, GREEN, BLUE, ORANGE, GREY = "#C8102E", "#009E73", "#0072B2", "#D55E00", "#666666"

# 本周活跃（end == asof）与退市分开
active = [r for r in rows if r["end"] == ASOF]
retired = [r for r in rows if r["end"] != ASOF]

def fm(v, dash="—"):
    return dash if v is None else f"{v:,}"

def sign(v, unit=""):
    if v is None:
        return "—"
    s = "+" if v > 0 else ("−" if v < 0 else "±")
    return f"{s}{abs(v):,}{unit}"

def col(v):
    return RED if (v or 0) > 0 else (GREEN if (v or 0) < 0 else GREY)

def rank_block(title, key, rev=True, note="单位：张（官方 Change 列）"):
    sub = sorted([r for r in active if r.get(key) is not None], key=lambda x: x[key], reverse=rev)
    if not sub:
        return f'<h3 class="g">{title}</h3><div class="empty">无本周数据</div>'
    med = abs(sub[len(sub)//2][key]) if len(sub) > 1 else abs(sub[0][key])
    items = []
    for i, r in enumerate(sub, 1):
        v = r[key]
        bar = min(100, abs(v) / max(med, 1) * 100)
        items.append(f"""<div class="rk">
        <div class="rkno">{i:02d}</div>
        <div class="rkbody">
          <div class="rkname">{html.escape(r["name"])}</div>
          <div class="rkbar"><div class="bar" style="width:{bar:.0f}%;background:{col(v)}"></div>
          <span class="rkval" style="color:{col(v)}">{sign(v)}</span></div>
          <div class="rkm">净多 {fm(r['nc_net'])} · 非商多 {fm(r['nc_l'])} / 空 {fm(r['nc_s'])} ｜ 净多4周 {sign(r['nc_net_chg4'])}</div>
        </div></div>""")
    return f'<h3 class="g">{title} <span class="cnt">{note}</span></h3><div class="rks">{"".join(items)}</div>'

# 退市区块
def retired_block():
    items = []
    for r in retired:
        items.append(f"""<div class="rc">
        <div class="rcn">{html.escape(r["name"])}</div>
        <div class="rcm">可回溯 {r["start"]} ~ {r["end"]}（{r["n"]} 周）· 末周数据</div>
        <div class="rcv">非商多 {fm(r["nc_l"])} · 空 {fm(r["nc_s"])} · 净 {fm(r["nc_net"])}</div>
        <div class="rcv2">末周 多{sign(r["nc_l_chg1"])} / 空{sign(r["nc_s_chg1"])} / 净{sign(r["nc_net_chg1"])}</div></div>""")
    return f'<h3 class="g">已退市小麦品种（末周数据，不参与本周排名）</h3><div class="rcs">{"".join(items)}</div>'

# 明细表
def detail_table():
    out = []
    for r in sorted(rows, key=lambda x: x["end"], reverse=True):
        nd = "本周" if r["end"] == ASOF else "末周"
        out.append(f"""<tr>
        <td class="l nm">{html.escape(r["name"])}</td>
        <td class="dim">{r["start"]} ~ {r["end"]}<br><span class="d2">{r["n"]} 周</span></td>
        <td>{nd}</td>
        <td>{fm(r["nc_l"])}</td><td class="pos">{sign(r["nc_l_chg1"])}</td>
        <td>{fm(r["nc_s"])}</td><td class="neg">{sign(r["nc_s_chg1"])}</td>
        <td class="hi" style="color:{col(r['nc_net'])}">{fm(r["nc_net"])}</td>
        <td>{sign(r["nc_net_chg1"])}</td><td class="dim">{sign(r["nc_net_chg4"])}</td>
        <td class="dim">{sign(r["c_net"])}</td></tr>""")
    return "\n".join(out)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>小麦家族排行榜 · CFTC COT 截至 {ASOF}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f7f7f5;color:#1a1a1a;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.65}}
.wrap{{max-width:1000px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:24px;margin:0 0 6px}}
.sub{{color:#666;font-size:13px;margin-bottom:3px}}
h2{{font-size:18px;margin:30px 0 10px;padding-left:11px;border-left:4px solid {BLUE}}}
h3.g{{font-size:14.5px;margin:22px 0 8px;color:#1a1a1a}}
h3.g .cnt{{font-size:11px;color:#999;font-weight:400;margin-left:8px}}
.note{{background:#fffdf5;border:1px solid #e8dcc0;border-left:4px solid #E69F00;border-radius:6px;padding:12px 15px;font-size:13px;margin:14px 0}}
.note li{{margin:5px 0}}
.rks{{display:flex;flex-direction:column;gap:8px}}
.rk{{display:flex;gap:10px;background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:10px 14px;align-items:center}}
.rkno{{font-size:17px;font-weight:800;color:#bbb;width:26px}}
.rkbody{{flex:1}}
.rkname{{font-size:13.5px;font-weight:600;margin-bottom:4px}}
.rkbar{{position:relative;height:18px;background:#f0efea;border-radius:4px;overflow:hidden}}
.bar{{position:absolute;left:0;top:0;bottom:0;opacity:.85;min-width:8px}}
.rkval{{position:absolute;left:10px;top:-1px;font-size:12.5px;font-weight:700;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.35)}}
.rkm{{font-size:11px;color:#888;margin-top:4px}}
.empty{{background:#fff;border:1px solid #e6e4df;border-radius:8px;padding:14px;color:#999;font-size:12.5px}}
.rcs{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}}
.rc{{background:#fbfbf9;border:1px dashed #d8d5cc;border-radius:8px;padding:11px 14px}}
.rcn{{font-size:13px;font-weight:600}}
.rcm{{font-size:11px;color:#999;margin:2px 0}}
.rcv{{font-size:12.5px;color:#333;font-variant-numeric:tabular-nums}}
.rcv2{{font-size:12px;margin-top:2px;color:#666}}
.tw{{overflow-x:auto;background:#fff;border:1px solid #e6e4df;border-radius:8px}}
table{{border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}}
th{{background:#f0efe9;color:#333;font-weight:600;padding:8px 9px;text-align:right;border-bottom:1.5px solid #ddd9d0;font-size:11.5px}}
th.l{{text-align:left}}
td{{padding:7px 9px;text-align:right;border-bottom:1px solid #f0efea;font-variant-numeric:tabular-nums}}
td.l{{text-align:left}}
td.nm{{font-weight:600}}
td.hi{{font-weight:700}}
.pos{{color:{RED}}}
.neg{{color:{GREEN}}}
.dim{{color:#888;font-size:11.5px}}
.d2{{color:#aaa;font-size:10.5px}}
.foot{{margin-top:28px;font-size:11px;color:#999;border-top:1px solid #e6e4df;padding-top:10px}}
</style></head><body><div class="wrap">

<h1>小麦家族排行榜 · CFTC COT</h1>
<div class="sub">持仓截至 <b>{ASOF}</b>（周二）｜ Futures-Only 口径 ｜ 与 79 号报告同源数据（1995-2026 全史）</div>
<div class="sub">榜单 = <b>本周（1 周）变动</b>，单位：张（官方 Change 列）；红=增仓/净多增，绿=砍仓/净多减</div>

<div class="note"><b>关于"小麦品种数量"：</b>CFTC 仅管辖美国交易所期货，其跟踪的小麦合约就这三类——
<ul>
<li><b>CBOT 小麦</b>：2013 年 12 月起拆分为 <b>SRW 软红冬</b>与 <b>HRW 硬红冬</b>两个合约（此前为单一 WHEAT - CBOT）</li>
<li><b>MGE/MIAX 小麦</b>：<b>HRS 硬红春</b>（Minneapolis Grain Exchange，2024-11 更名 MIAX Futures Exchange）</li>
<li>已退市：<b>黑海金融小麦</b>（CBOT，2018-2022）、<b>白小麦</b>（MGE，1995-1998）、<b>硬质杜伦麦</b>（MGE，1998 年短期上市）</li>
</ul>
欧洲（巴黎制粉小麦）、澳大利亚（ASX 小麦）等境外小麦不在 CFTC 数据内。因此"前 20"在本数据集中只有 3 个活跃合约 + 合计与退市记录共 <b>7 个序列</b>，已全部列出。</div>

<h2>一、非商业多头增仓榜（本周）</h2>
{rank_block("非商业多头增仓 TOP（全部）", "nc_l_chg1")}

<h2>二、非商业空头砍仓榜（本周，空头减仓 = 回补）</h2>
{rank_block("非商业空头砍仓 TOP（全部）", "nc_s_chg1", rev=False)}

<h2>三、净多头变化榜（本周）</h2>
{rank_block("净多头变化 TOP（全部）", "nc_net_chg1")}

<h2>四、退市小麦品种</h2>
{retired_block()}

<h2>五、全量明细（含商业端）</h2>
<div class="tw"><table>
<thead><tr>
<th class="l">品种</th><th>可回溯</th><th>状态</th>
<th class="sep">非商多</th><th>多变</th><th>非商空</th><th>空变</th>
<th class="hi">净多</th><th>净变1w</th><th>净变4w</th><th class="sep">商业净</th>
</tr></thead><tbody>
{detail_table()}
</tbody></table></div>

<div class="foot">数据源：CFTC COT Futures-Only（deahistfo 1995-2026）｜ 明细 results/cot/wheat_family_rank_20260901.csv ｜ 脚本 scripts/wheat_family_rank_20260905.py</div>
</div></body></html>"""

p = os.path.join(OD, "小麦家族排行榜_20260901.html")
open(p, "w", encoding="utf-8").write(HTML)
print("written", p, len(HTML), "bytes")