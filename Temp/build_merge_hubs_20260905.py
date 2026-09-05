# -*- coding: utf-8 -*-
"""生成 76 中期选举合集 / 77 MCD RSI 合集 / 78 KBWB 合集（导览+iframe 原文分区）"""
import os, html

REP = r"C:\Users\Administrator\Desktop\stock\reports"
ARCH = "../_archive_202609"

TEMPLATE = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title><style>
:root{{--ink:#1c2733;--sub:#5a6b7b;--line:#dde4ea;--bg:#f6f8fa;--card:#fff;--blue:#1f77b4;--org:#ff7f0e;--pur:#9467bd;--teal:#17becf;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font:14px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--bg);}}
.wrap{{max-width:1240px;margin:0 auto;padding:28px 22px 60px;}}
h1{{font-size:25px;line-height:1.4;margin-bottom:6px;}}
.meta{{color:var(--sub);font-size:13px;margin-bottom:20px;}}
.banner{{background:#fff8ee;border:1px solid #f0d9a8;border-radius:10px;padding:10px 14px;margin:0 0 22px;font-size:13px;color:#7a5b16;}}
h2{{font-size:18px;margin:28px 0 12px;padding-left:10px;border-left:4px solid var(--blue);}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px;margin:14px 0;}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;}}
.card b{{display:block;font-size:15px;margin-bottom:6px;}}
.card .pos{{font-size:12px;color:var(--sub);margin-bottom:8px;}}
.card p{{font-size:13px;}}
.tag{{display:inline-block;background:#eef2f6;border-radius:4px;padding:0 8px;font-size:12px;color:#5a6b7b;margin-right:6px;}}
ul.tabs{{display:flex;gap:8px;list-style:none;flex-wrap:wrap;margin:14px 0;}}
ul.tabs li button{{border:1px solid var(--line);background:var(--card);border-radius:20px;padding:5px 16px;cursor:pointer;font-size:13px;color:var(--ink);}}
ul.tabs li button.on{{background:var(--blue);border-color:var(--blue);color:#fff;}}
.pane{{display:none;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;}}
.pane.on{{display:block;}}
.pane iframe{{width:100%;height:1080px;border:0;display:block;}}
.pane .phead{{padding:8px 14px;background:#eef2f6;font-size:13px;border-bottom:1px solid var(--line);}}
.pane .phead a{{color:var(--blue);text-decoration:none;}}
.flow{{font-size:13px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:12px 0;}}
.foot{{color:var(--sub);font-size:12px;margin-top:30px;border-top:1px solid var(--line);padding-top:10px;}}
</style></head><body><div class="wrap">
{TITLEBLOCK}
<script>
function sw(el){{var panes=el.parentElement.parentElement.querySelectorAll('.pane');
var btns=el.parentElement.querySelectorAll('button');
panes.forEach(p=>p.classList.remove('on'));btns.forEach(b=>b.classList.remove('on'));
el.classList.add('on');var pane=document.getElementById('pane-'+el.getAttribute('data-t'));
if(pane&&!pane.getAttribute('data-l')){{pane.setAttribute('data-l','1');var f=pane.querySelector('iframe');f.src=f.getAttribute('data-src');}}
}}
</script>
{BODY}
<div class="foot">{FOOT}</div></div></body></html>"""

def page(title, meta, banner, sections, body, foot):
    tb = f"<h1>{title}</h1><div class='meta'>{meta}</div>" + (f"<div class='banner'>{banner}</div>" if banner else "")
    return TEMPLATE.format(TITLE=title, TITLEBLOCK=tb, BODY=body, FOOT=foot)

def tab_block(items):
    """items: [(key,label,phead,path)]"""
    out = []
    btns = []
    panes = []
    for i,(k,lbl,path,note) in enumerate(items):
        btns.append(f"<li><button data-t='{k}'{' class=on' if i==0 else ''} onclick='sw(this)'>{lbl}</button></li>")
        srcattr = f"src='{path}'" if i == 0 else f"data-src='{path}'"
        panes.append(f"<div class='pane{' on' if i==0 else ''}' id='pane-{k}'><div class='phead'>{note}</div><iframe {srcattr}></iframe></div>")
    return "<ul class='tabs'>" + "".join(btns) + "</ul><div>" + "".join(panes) + "</div>"

def card(title, pos, txt):
    return f"<div class='card'><b>{title}</b><div class='pos'>{pos}</div><p>{txt}</p></div>"

# ============ 76 中期选举 ============
b76 = []
b76.append("<h2>系列说明：同一事件窗口的三个测量视角</h2>")
b76.append("<div class='flow'>三份报告（原 37 / 38 / 42 号，2026-08 同批产出）研究<b>同一个对象</b>——美国中期选举前市场的波动率行为——只是<b>观察层级</b>不同：<b>37</b> 看大盘（标普500 在选举窗口的波动放大与事件统计）；<b>38</b> 下钻到板块（九大板块逐一的选举窗口波动曲线与横向排名）；<b>42</b> 看直接的情绪读数（VIX 在选举前的走势与事件研究）。合并后入口统一，三份原文完整保留于下方，可 Tab 切换或点『新窗口打开』。\n\n<b>导读</b>：判断『这轮选举前要不要降波动敞口』→ 先看 37；想知道哪类板块最敏感/最抗跌 → 看 38；做期权/波动率交易盯 VIX 阈值 → 看 42。三份信号可以互相印证：VIX 抬升（42）应主要体现在高 β 板块（38），并在 SPX 事件统计（37）中留下痕迹。</div>")
b76.append("<div class='grid'>" +
  card("37 · 标普500 波动率放大", "层级：大盘指数", "中期选举前 SPX 波动率放大的事件研究——历史选举窗口与平日的波动对比、选举后收敛节奏，回答『选举是不是系统性波动事件』。") +
  card("38 · 板块波动率横向", "层级：板块（9 大板块代表）", "把 37 的框架拆到板块层：各板块在选举窗口的 V20 曲线、波动抬升幅度排名与热图，定位哪类板块（高 β 成长 / 防御 / 金融）在选举窗口最敏感。") +
  card("42 · VIX 前抬升", "层级：波动率指数", "VIX 在中期选举前是否系统性抬升、抬升幅度与时间窗，作为情绪面的直接读数与交易参考。") + "</div>")

# ============ 77 MCD RSI ============
b77 = []
b77.append("<h2>系列说明：同一标的、同一信号族、四次递进回测</h2>")
b77.append("<div class='flow'>四份报告（原 46-49 号）研究同一问题——<b>MCD 的 RSI 低位能不能买</b>——是四次递进的方法迭代：<b>46</b> 先复刻蓝筹 41 号『RSI 摆动低点聚集支撑』（信号稀缺：31.7 年仅 6 次，超额为负）；<b>47</b> 放宽到『下穿 40 分档』（发现越宽越稀释，且『身处低位有价值、下穿当天买没有』）；<b>48</b> 引入窗口质量（最大涨幅 + 效率比率 ER）解释超额为什么少（反弹磕绊 + 假反弹拖累）；<b>49</b> 改为『越跌越买』状态口径（RSI&lt;30 从 5 次接飞刀变 82 次可操作，绝对收益正但超额≤0，唯一正超额=30-35 档 cd10 去重首档）。\n\n<b>方法族总纲</b>：MCD 防御属性（低 β）决定其低位反弹『绝对收益为正、相对 SPY 跑输』——抄底赚的是自己弹回来的钱，不是跑赢大盘的钱；与 CCL（56→62）相反、DAL（64）同侧。同方法族的池子级母报告是 39/40/41（72 蓝筹）与 50 号（纳指）。</div>")
b77.append("<div class='grid'>" +
  card("46 · 摆动低点支撑", "定位：稀缺性检验", "31.7 年仅触发 6 次（最近 2022-12-15）；6 次 T+20 +4.96% 但超额 −0.56% 不显著 = 是 β 不是择时 edge。") +
  card("47 · 下穿40 分档", "定位：阈值稀释", "门槛从 30 放宽到 40，edge 反而更弱（+1.83%→+0.89%）；关键发现：RSI&lt;30 的状态日（226 天）T+20 +2.53% 显著，下穿当天买只有 +0.89%。") +
  card("48 · 窗口质量 ER", "定位：归因解释", "MCD 反弹更『磕绊』（ER 0.19 vs SPY 0.22）；ER&gt;0.3 的单边反弹几乎都是大正超额，最差超额事件=『MCD 没涨而 SPY 大涨』的假反弹窗口。") +
  card("49 · 越跌越买阶梯", "定位：可操作口径", "449 次三档绝对收益全正、maxG 随档位递增；但超额全 ≤0（30-35 档 cd10 去重后 +0.71pp 胜率 74.2% 是唯一正超额子集）。") + "</div>")

# ============ 78 KBWB ============
b78 = []
b78.append("<h2>系列说明：同一方法模板 × 三个目标板块</h2>")
b78.append("<div class='flow'>三份报告（原 14 / 15 / 16 号）共用同一<b>方法模板</b>——以 KBWB（Invesco KBW 银行 ETF）定义『银行走弱』信号（信号 A：EMA20 跌破 5 日未修复；信号 B：跌破上升趋势线），然后做两件事：① 事件研究（走弱信号后目标板块前瞻收益）；② 条件相关性（走弱期 vs 正常期 KBWB↔目标板块的日收益相关）。差别只在<b>目标板块</b>：科技（SOXX/XLK）、医药（XPH/XBI）、资管（APO/BX/KKR/BLK/TROW）。\n\n<b>横向结论</b>（三份拼起来的板块间比较）：银行走弱期的联动强度 <b>资管 &gt; 科技 &gt; 医药</b>（相关最高值 0.82 / 0.76 / 0.65）——资管是『银行的影子』（费率+信贷敞口+资本市场 β 同源），医药独立性最强；『银行走弱后板块反弹』的现象出现在科技与另类资管（fwd20 高于基线），医药则走自己的节奏无此现象。</div>")
b78.append("<div class='grid'>" +
  card("14 · 科技（SOXX / XLK）", "联动：0.45→0.71 / 0.46→0.76", "银行走弱不是科技看空信号而是『联动加剧』信号：前瞻 fwd20 +2.81%/+2.02% 高于基线、胜率 66-70%；但结构性破趋势线时相关性反而回落（科技脱钩走独立行情）。") +
  card("15 · 医药（XPH / XBI）", "联动：0.46→0.65 / 0.40→0.55", "比科技弱一档：化学制药升幅大、生物制药升幅小；走弱确认后医药无『跟着反弹』现象（fwd20 与基线持平），独立性最强、偏防御。") +
  card("16 · 资管（APO/BX/KKR/BLK/TROW）", "联动：0.49-0.64→0.71-0.82", "与银行联动最紧（BLK 0.82）：走弱确认后另类资管普遍强于基线（APO fwd20 +3.11% vs 基线 +2.23%）、传统资管贴基线——『银行的影子』。") + "</div>")

def build(name, dirname, title, meta, banner, header_html, items, foot):
    # items: list of (key,label,note,reldir,relfile)
    tb = tab_block([(k, lbl, f"../_archive_202609/{rel}/{relfile}", note) for k, lbl, note, rel, relfile in items])
    os.makedirs(os.path.join(REP, dirname), exist_ok=True)
    body = header_html + "<h2>原文阅读（Tab 切换 · 懒加载）</h2>" + tb
    p = os.path.join(REP, dirname, "index.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(page(title, meta, banner, None, body, foot))
    print("OK", p)

foot76 = "合集 76 号（2026-09-05 报告治理合并）· 原文 37/38/42 归档于 reports/_archive_202609/ · 数据与图表未做任何改动"
foot77 = "合集 77 号（2026-09-05 报告治理合并）· 原文 46-49 归档于 reports/_archive_202609/ · 方法族母报告：39/40/41 蓝筹 RSI、50 纳指 RSI；同族个股：CCL(56→62)、DAL(64)"
foot78 = "合集 78 号（2026-09-05 报告治理合并）· 原文 14/15/16 归档于 reports/_archive_202609/ · KBWB 系另见 13_kbwb支撑位(kbwb_ms_corr) 与 13_道指板块支撑"

build("76", "76_中期选举窗口波动率合集", "76 · 中期选举窗口波动率合集（原 37/38/42）",
      "2026-09-05 报告治理合并 · 三份原文完整保留",
      None,
      "".join(b76),
      [("s37","37 · SPX 波动率放大","37 号原文 · 中期选举前标普500 波动率事件研究 · 图：波动曲线/事件/窗口对比","37_中期选举波动率","index.html"),
       ("s38","38 · 板块波动横向","38 号原文 · 各板块选举窗口波动率对比 · 图：板块曲线/排名/热图","38_板块中期选举波动率","index.html"),
       ("s42","42 · VIX 前抬升","42 号原文 · VIX 中期选举前走势事件研究 · 图：VIX 曲线/事件/窗口","42_VIX中期选举抬升","index.html")],
      foot76)

build("77", "77_MCD_RSI低吸系列合集", "77 · MCD RSI 低吸方法族合集（原 46-49）",
      "2026-09-05 报告治理合并 · 四份原文完整保留",
      None,
      "".join(b77),
      [("m46","46 · 摆动低点支撑","46 号原文 · swing low 聚集支撑买入 · 6 事件全史","46_MCD_RSI摆动低点支撑买入","index.html"),
       ("m47","47 · 下穿40 分档","47 号原文 · RSI 低位分档买入 · 258 事件","47_MCD_RSI低位分档买入","index.html"),
       ("m48","48 · 窗口质量 ER","48 号原文 · 最大涨幅+效率比率 · cd10 171 事件","48_MCD_RSI低位窗口质量","index.html"),
       ("m49","49 · 越跌越买阶梯","49 号原文 · 区间跌落买入 · 449 次全量+明细","49_MCD_RSI区间跌落买入","index.html")],
      foot77)

build("78", "78_银行弱势传导合集_KBWB", "78 · 银行走弱 × 板块传导合集（原 14/15/16）",
      "2026-09-05 报告治理合并 · 三份原文完整保留",
      None,
      "".join(b78),
      [("k14","14 · 科技 SOXX/XLK","14 号原文 · 银行走弱→科技 · 条件相关性+事件研究","14_kbwb科技弱势","kbwb_tech_weakness_report.html"),
       ("k15","15 · 医药 XPH/XBI","15 号原文 · 银行走弱→医药 · 条件相关性+事件研究","15_kbwb医药弱势","kbwb_med_weakness_report.html"),
       ("k16","16 · 资管 5 股","16 号原文 · 银行走弱→资管 · 条件相关性+事件研究","16_kbwbAM弱势","kbwb_am_weakness_report.html")],
      foot78)
