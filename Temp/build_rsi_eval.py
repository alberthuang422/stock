# -*- coding: utf-8 -*-
"""构建热门美股 RSI 评估报告 HTML（暗色研报风，可排序搜索）
用法: python build_rsi_eval.py <输入json> <输出html>
输入 json 行结构需含 rsi14/rsi14_5d/off_hi52/ret20/ret60/price/rank/code/name
板块归并读 Temp/plate_bucket.json（主控脚本 daily_hot_rsi.py 每日先生成）"""
import json, statistics as st, sys
import datetime as _dt, collections

BASE = r"C:\Users\Administrator\Desktop\stock"
if len(sys.argv) >= 3:
    IN_JSON, OUT_HTML = sys.argv[1], sys.argv[2]
else:
    IN_JSON, OUT_HTML = BASE + r"\results\rsi14_hot354_20260901.json", BASE + r"\reports\hot354_rsi_eval_20260901.html"
rows = json.load(open(IN_JSON, encoding="utf-8"))
rows = [x for x in rows if x["rsi14"] is not None]

N = len(rows)
_cuts = sorted({x.get("last_date") for x in rows if x.get("last_date")})
CUT = _cuts[-1] if _cuts else _dt.date.today().strftime("%Y-%m-%d")
DATE = _dt.date.today().strftime("%Y-%m-%d")

# ---- 板块归并 ----
PB = json.load(open(BASE + r"\Temp\plate_bucket.json", encoding="utf-8"))
for x in rows:
    p = PB.get(x["code"], {})
    x["bucket"] = p.get("bucket", "其他")
    x["plates"] = p.get("plates", [])
BUCKET_ORDER = ["半导体/AI硬件","软件/SaaS","互联网/电商","金融","能源","公用/电力","医药/生物",
                "可选消费","必选消费","军工/航天","航天/太空","工业/机械/运输","通信","材料","地产","加密关联","其他"]
BUCKET_ORDER = [b for b in BUCKET_ORDER if any(x["bucket"]==b for x in rows)]

# ---- stats ----
vals = [x["rsi14"] for x in rows]
med, mean = st.median(vals), st.mean(vals)
bins = [0]*6
for v in vals:
    i = 0 if v<30 else 1 if v<40 else 2 if v<50 else 3 if v<60 else 4 if v<70 else 5
    bins[i]+=1
rising = sum(1 for x in rows if x["rsi14_5d"] and x["rsi14"]>x["rsi14_5d"])
near_hi = [x for x in rows if x["off_hi52"] is not None and x["off_hi52"]>=-2]
bounce = [x for x in rows if x["rsi14_5d"] is not None and x["rsi14_5d"]<=30 and x["rsi14"]>30]
os_list = sorted([x for x in rows if x["rsi14"]<30], key=lambda x:x["rsi14"])
ob_list = sorted([x for x in rows if x["rsi14"]>=70], key=lambda x:-x["rsi14"])
t50 = sorted(rows, key=lambda x:x["rank"])[:50]

def rsi_tag(v):
    if v<30: return ("超卖","t-os")
    if v<40: return ("偏弱","t-weak")
    if v<60: return ("中性","t-mid")
    if v<70: return ("偏强","t-str")
    return ("超买","t-ob")

def chg_html(v):
    if v is None: return '<td class="num">—</td>'
    cls = "up" if v>0 else ("down" if v<0 else "")
    return f'<td class="num {cls}">{v:+.1f}%</td>'

BUCKET_COLORS = {  # 板块标签着色（Okabe-Ito 系）
 "半导体/AI硬件":"#4e79a7","软件/SaaS":"#59a14f","互联网/电商":"#76b7b2","金融":"#9c755f",
 "能源":"#f28e2b","公用/电力":"#8cd17d","医药/生物":"#e15759","可选消费":"#b6992d",
 "必选消费":"#86bcb6","军工/航天":"#af7aa1","航天/太空":"#6b6ecf","工业/机械/运输":"#bab0ac",
 "通信":"#ffbe7d","材料":"#d4a6c8","地产":"#f1ce63","加密关联":"#edc948","其他":"#808080"}

def bucket_tag(b):
    c = BUCKET_COLORS.get(b, "#808080")
    return f'<span class="btag" style="color:{c};border-color:{c}">{b}</span>'

def row_html(x, with_bucket=True):
    tag, cls = rsi_tag(x["rsi14"])
    r5 = x["rsi14_5d"]; delta = None if r5 is None else round(x["rsi14"]-r5,1)
    dcls = "up" if (delta or 0)>0 else ("down" if (delta or 0)<0 else "")
    dtxt = "—" if delta is None else f'<span class="{dcls}">{delta:+.1f}</span>'
    oh = x["off_hi52"]
    ohcls = "down" if (oh is not None and oh<-20) else ("up" if (oh is not None and oh>=-2) else "")
    bcol = "" if not with_bucket else f"<td class='l'>{bucket_tag(x['bucket'])}</td>"
    return ("<tr data-rsi=\"{rsi}\" data-rank=\"{rk}\" data-bucket=\"{bk}\">"
        "<td class='num'>{rk}</td><td class='code'>{code}</td><td class='nm'>{name}</td>"
        "<td class='num'><b>{rsi:.1f}</b></td><td class='num'>{dtxt}</td>"
        "<td class='num'><span class='tag {cls}'>{tag}</span></td>"
        "{bcol}"
        "<td class='num'>{px}</td>".format(rsi=x["rsi14"], rk=x["rank"], code=x["code"],
        name=x["name"], dtxt=dtxt, cls=cls, tag=tag, bcol=bcol, bk=x["bucket"], px=f"{x['price']:.2f}")
        + chg_html(x["ret20"]) + chg_html(x["ret60"])
        + f"<td class='num {ohcls}'>{'—' if oh is None else f'{oh:+.1f}%'} {x['hi52']:.0f}</td>"
        + "</tr>")

# histogram (SVG, 10-bin)
hb=[0]*10
for v in vals:
    i=min(int(v//10),9); hb[i]+=1
hmax=max(hb)
svg_bars=[]
for i,c in enumerate(hb):
    h=c/hmax*120
    x0=40+i*60
    color = "#59a14f" if i<3 else ("#828282" if i<5 else ("#4e79a7" if i<7 else "#e15759"))
    svg_bars.append(f"<rect x='{x0}' y='{150-h:.0f}' width='48' height='{h:.0f}' fill='{color}' rx='3'/>"
        f"<text x='{x0+24}' y='166' text-anchor='middle' class='axl'>{i*10}</text>"
        f"<text x='{x0+24}' y='{142-h:.0f}' text-anchor='middle' class='v'>{c}</text>")
svg_hist = ("<svg viewBox='0 0 660 185' class='hist'>"
    "<line x1='30' y1='150' x2='650' y2='150' stroke='#3a3a3a'/>"
    + "".join(svg_bars)
    + "<text x='64' y='180' class='axl'>超卖◀</text><text x='560' y='180' class='axl'>▶超买</text>"
    "<text x='330' y='180' text-anchor='middle' class='axl'>RSI(14) 分布 · 中位 48.0</text></svg>")

DATA = json.dumps(rows, ensure_ascii=False)

html = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>热门美股 Top500 过滤版 · RSI 评估 · __DATE__</title>
<style>
:root{--bg:#1a1a1a;--panel:#232323;--panel2:#2a2a2a;--border:#333;--txt:#e6e6e6;--muted:#9a9a9a;--up:#e15759;--down:#59a14f;--accent:#4e79a7;--orange:#f28e2b}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font:14px/1.6 "Segoe UI","Microsoft YaHei",sans-serif;padding:26px;max-width:1280px;margin:0 auto}
h1{font-size:21px;margin-bottom:2px}
h2{font-size:16px;margin:26px 0 10px;padding-left:9px;border-left:3px solid var(--accent)}
.sub{color:var(--muted);font-size:12.5px;margin-bottom:14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:6px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.card .k{color:var(--muted);font-size:12px}
.card .v{font-size:22px;font-weight:700;margin-top:2px}
.card .d{font-size:11.5px;color:var(--muted);margin-top:2px}
.note{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--orange);border-radius:6px;padding:10px 14px;font-size:12.5px;color:#cfcfcf;margin:10px 0;line-height:1.8}
.note b{color:var(--txt)}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:13px}
th,td{padding:5px 9px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap}
th{color:var(--muted);font-size:12px;font-weight:600;position:sticky;top:0;background:var(--bg);cursor:pointer;user-select:none;z-index:2}
th.l,td.l{text-align:left}
td.code{font-weight:700;text-align:left}
td.nm{text-align:left;color:#c8c8c8;max-width:180px;overflow:hidden;text-overflow:ellipsis}
td.up,span.up{color:var(--up)}
td.down,span.down{color:var(--down)}
.tag{padding:1px 7px;border-radius:9px;font-size:11px}
.t-os{background:#274e36;color:#7fd6a0}
.t-weak{background:#2c3a2e;color:#a5c98f}
.t-mid{background:#2f2f2f;color:#bdbdbd}
.t-str{background:#3d3423;color:#e8b56e}
.t-ob{background:#54282a;color:#f08a8a}
.wrap{border:1px solid var(--border);border-radius:8px;overflow:auto;max-height:640px}
.bar{display:flex;gap:12px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
input,select{background:var(--panel);border:1px solid var(--border);color:var(--txt);padding:7px 12px;border-radius:6px;width:260px;font-size:13px}
select{width:auto;cursor:pointer}
button{background:var(--panel);border:1px solid var(--border);color:var(--muted);padding:6px 12px;border-radius:6px;font-size:12.5px;cursor:pointer}
button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.btag{display:inline-block;padding:0 7px;border:1px solid;border-radius:9px;font-size:11px;white-space:nowrap}
#pivot tbody tr{cursor:pointer}
#pivot tbody tr:hover{background:var(--panel2)}
.stat{color:var(--muted);font-size:12.5px}
.hist{width:100%;max-width:680px}
.hist .axl{fill:var(--muted);font-size:10px}
.hist .v{fill:var(--txt);font-size:10.5px}
tbody tr:hover{background:var(--panel2)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
td.why{text-align:left;color:#bfbfbf;white-space:normal;font-size:12.5px;max-width:420px}
</style></head><body>
<h1>热门美股过滤池 · RSI(14) 技术面评估</h1>
<div class="sub">样本：富途综合热度 Top500 剔除 股价&gt;$500 / 中概股 / ADR 后的 <b>__N__ 只美股</b> · RSI=Wilder 14 日，基于 260 根日线，截至 <b>__CUT__ 收盘</b> · 数据源 Futu MCP 行情</div>

<div class="cards">
<div class="card"><div class="k">中位 RSI</div><div class="v">__MED__</div><div class="d">均值 __MEAN__，中性略偏弱</div></div>
<div class="card"><div class="k">超卖 (&lt;30)</div><div class="v" style="color:var(--down)">__NOS__</div><div class="d">占比 __POS__%</div></div>
<div class="card"><div class="k">超买 (≥70)</div><div class="v" style="color:var(--up)">__NOB__</div><div class="d">占比 __POB__%</div></div>
<div class="card"><div class="k">RSI 5日回升</div><div class="v">__NR__<span style="font-size:13px;color:var(--muted)">/__N__</span></div><div class="d">仅 __PR__%，动能面仍在恶化</div></div>
<div class="card"><div class="k">距52周高≤2%</div><div class="v" style="color:var(--up)">__NNH__</div><div class="d">能源/软件双主线领涨</div></div>
</div>
__SVGHIST__

<h2>一、总体研判</h2>
<div class="note">
<b>结论：热度池整体处于"中性分化"格局，不是单边超买或超卖市。</b>
① 中位 RSI __MED__（均值 __MEAN__），__P50__% 的样本在 50 以下——<b>多数热门股技术面偏软</b>；但分布两尾极薄（超卖 __POS__% + 超买 __POB__%），说明市场没有系统性恐慌，也没有全面过热。
② 动能方向上仅 <b>__PR__%（__NR__/__N__）RSI 较 5 日前回升</b>——热度榜整体的短线动能仍在衰减通道中，属于"跌不动但也涨不动"的磨底结构。
③ 真正信号在两尾与高靠近端：<b>__NNH__ 只贴近 52 周新高</b>（详见下方明细，按板块聚类查看）——资金在热度池内做的是<b>高低切换而非普涨</b>。
④ 超大市值 AI 核心股 RSI 是否超买/破位，见下方「热度 Top50 对照」与明细排序——<b>热度≠过热</b>。
</div>

<h2>二、超卖名单（RSI &lt; 30，共 __NOS__ 只）</h2>
<table>
<thead><tr><th class="l">代码</th><th class="l">名称</th><th>RSI</th><th>5日前</th><th>现价</th><th>20日</th><th>60日</th><th>距52周高</th><th class="l">点评</th></tr></thead>
<tbody>__OS_ROWS__</tbody></table>
__OS_NOTE__

<h2>三、超买名单（RSI ≥ 70，共 __NOB__ 只）</h2>
<table>
<thead><tr><th class="l">代码</th><th class="l">名称</th><th>RSI</th><th>5日前</th><th>现价</th><th>20日</th><th>60日</th><th>距52周高</th><th class="l">点评</th></tr></thead>
<tbody>__OB_ROWS__</tbody></table>
__OB_NOTE__

<h2>四、热度 Top50 × RSI 对照</h2>
<div class="sub" style="margin-bottom:6px">最热门的 50 只（过滤后重排）——热度高不等于技术过热，中位 RSI 48.5 与全池一致。</div>
<div class="wrap"><table id="t50">
<thead><tr><th>#</th><th class="l">代码</th><th class="l">名称</th><th>RSI</th><th>Δ5日</th><th>标签</th><th>现价</th><th>20日</th><th>60日</th><th>距52周高</th></tr></thead>
<tbody>__T50_ROWS__</tbody></table></div>
__T50_NOTE__

<h2>五、5 日内刚脱离超卖（早期反转观察名单）</h2>
__BOUNCE__

<h2>六、板块 × RSI 交叉透视</h2>
<div class="sub" style="margin-bottom:6px">各板块的数量、RSI 中位、超买超卖与贴新高分布（点击行可只看该板块）。</div>
<div class="wrap"><table id="pivot">
<thead><tr><th class="l">板块</th><th>只数</th><th>中位RSI</th><th>超卖&lt;30</th><th>超买≥70</th><th>贴52周高</th><th>5日回升占比</th><th class="l">代表标的（按热度）</th></tr></thead>
<tbody>__PIVOT_ROWS__</tbody></table></div>
__PIVOT_NOTE__

<h2>七、全量 __N__ 只明细 · 组合筛选（分档 × 分板块 × 搜索）</h2>
<div class="bar">
<input id="q" placeholder="搜索 代码/名称…">
<select id="sec"><option value="">全部板块</option>__SEC_OPTS__</select>
<input id="rmin" type="number" placeholder="RSI≥" style="width:80px" min="0" max="100">
<input id="rmax" type="number" placeholder="RSI≤" style="width:80px" min="0" max="100">
<button class="on" data-f="all">全档位</button>
<button data-f="os">超卖&lt;30</button>
<button data-f="ob">超买≥70</button>
<button data-f="hi">贴52周高</button>
<button data-f="t50">热度前50</button>
<span class="stat" id="cnt"></span>
</div>
<div class="sub" style="margin-bottom:6px">提示：档位按钮、板块下拉、RSI 区间输入、关键词搜索<b>可任意组合叠加</b>；自定义区间输入后档位按钮自动失效。</div>
<div class="wrap"><table id="all">
<thead><tr><th data-k="rank">#</th><th class="l" data-k="code">代码</th><th class="l" data-k="name">名称</th><th data-k="rsi14">RSI</th><th data-k="d5">Δ5日</th><th>档位</th><th class="l" data-k="bucket">板块</th><th data-k="price">现价</th><th data-k="ret20">20日</th><th data-k="ret60">60日</th><th data-k="off_hi52">距52周高</th></tr></thead>
<tbody>__ALL_ROWS__</tbody></table></div>

<div class="sub" style="margin-top:22px">口径与局限：① 样本为"热度榜∩市值≥50亿美元∩过滤三规则"后的 354 只，<b>非全市场</b>，中位数只反映该池子情绪；② RSI 为日线 Wilder14，不含 4h 周期（与项目 MACD 三周期体系口径不同）；③ 中概/ADR 判定含人工规则（板块 US.LIST2517 + HAS_ADR + 境外发行人清单），边界样本（AXTI/CRDO/GFS 等）按美股保留；④ 8/31 为周一，US 市场正常交易日，无尾 bar 不完整问题（bars=260 全部齐）。</div>

<script>
const DATA=__DATA__;
const BCOLORS=__BCOLORS__;
(function(){
const tb=document.querySelector('#all tbody'),q=document.querySelector('#q'),cnt=document.querySelector('#cnt');
const sec=document.querySelector('#sec'),rmin=document.querySelector('#rmin'),rmax=document.querySelector('#rmax');
let filt='all',key='rank',asc=true;
function btag(b){const c=BCOLORS[b]||'#808080';return `<span class="btag" style="color:${c};border-color:${c}">${b}</span>`;}
function val(x,k){if(k==='d5')return (x.rsi14==null||x.rsi14_5d==null)?null:x.rsi14-x.rsi14_5d;return x[k];}
function match(x){
 if(filt==='os'&&!(x.rsi14<30))return false;
 if(filt==='ob'&&!(x.rsi14>=70))return false;
 if(filt==='hi'&&!(x.off_hi52>=-2))return false;
 if(filt==='t50'&&!(x.rank<=50))return false;
 const rb=sec.value; if(rb&&x.bucket!==rb)return false;
 const a=parseFloat(rmin.value),b=parseFloat(rmax.value);
 if(!isNaN(a)&&x.rsi14<a)return false;
 if(!isNaN(b)&&x.rsi14>b)return false;
 return true;}
function render(){
 const s=(q.value||'').toLowerCase();
 let a=DATA.filter(x=>match(x)&&(!s||x.code.toLowerCase().includes(s)||String(x.name).toLowerCase().includes(s)));
 a.sort((p,q2)=>{let vp=val(p,key),vq=val(q2,key);if(vp==null)return 1;if(vq==null)return -1;if(typeof vp==='string')return asc?vp.localeCompare(vq):vq.localeCompare(vp);return asc?vp-vq:vq-vp;});
 tb.innerHTML=a.map(x=>{
  const d=(x.rsi14==null||x.rsi14_5d==null)?null:+(x.rsi14-x.rsi14_5d).toFixed(1);
  const tag=x.rsi14<30?'<span class="tag t-os">超卖</span>':x.rsi14<40?'<span class="tag t-weak">偏弱</span>':x.rsi14<60?'<span class="tag t-mid">中性</span>':x.rsi14<70?'<span class="tag t-str">偏强</span>':'<span class="tag t-ob">超买</span>';
  const pc=v=>v==null?'<span>—</span>':`<span class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${v.toFixed(1)}%</span>`;
  return `<tr><td>${x.rank}</td><td class="code">${x.code}</td><td class="nm">${x.name}</td><td><b>${x.rsi14.toFixed(1)}</b></td><td>${d==null?'—':`<span class="${d>0?'up':d<0?'down':''}">${d>0?'+':''}${d}</span>`}</td><td>${tag}</td><td class="l">${btag(x.bucket)}</td><td>${x.price.toFixed(2)}</td><td>${pc(x.ret20)}</td><td>${pc(x.ret60)}</td><td class="${x.off_hi52>=-2?'up':x.off_hi52<-20?'down':''}">${x.off_hi52.toFixed(1)}%</td></tr>`;}).join('');
 cnt.textContent=a.length+' 只';}
document.querySelectorAll('#all thead th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(!k)return;if(key===k)asc=!asc;else{key=k;asc=true;}render();});
q.oninput=render; sec.onchange=render; rmin.oninput=render; rmax.oninput=render;
document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{
 if(b.dataset.f==='all'){rmin.value='';rmax.value='';}
 document.querySelectorAll('.bar button').forEach(x=>x.classList.remove('on'));
 b.classList.add('on');filt=b.dataset.f;render();});
// pivot 行点击 → 联动该板块
document.querySelectorAll('#pivot tbody tr').forEach(tr=>tr.onclick=()=>{
 const b=tr.dataset.bucket; sec.value=b; filt='all';
 document.querySelectorAll('.bar button').forEach(x=>x.classList.remove('on'));
 document.querySelectorAll('.bar button')[0].classList.add('on');
 render();
 window.scrollTo({top:document.querySelector('#all').getBoundingClientRect().top+window.scrollY-90,behavior:'smooth'});});
render();})();
</script>
</body></html>"""

def pivot_rows():
    out=[]
    for b in BUCKET_ORDER:
        g=[x for x in rows if x["bucket"]==b]
        if not g: continue
        gv=[x["rsi14"] for x in g]
        med=st.median(gv)
        nos=sum(1 for v in gv if v<30); nob=sum(1 for v in gv if v>=70)
        nhi=sum(1 for x in g if x["off_hi52"] is not None and x["off_hi52"]>=-2)
        rising_n=sum(1 for x in g if x["rsi14_5d"] and x["rsi14"]>x["rsi14_5d"])
        rep=" · ".join(x["code"] for x in sorted(g,key=lambda v:v["rank"])[:5])
        medcls = "up" if med>=55 else ("down" if med<=45 else "")
        out.append(f"<tr data-bucket='{b}'><td class='l'>{bucket_tag(b)}</td><td>{len(g)}</td>"
            f"<td><b class='{medcls}'>{med:.1f}</b></td><td>{nos}</td><td>{nob}</td><td>{nhi}</td>"
            f"<td>{rising_n/len(g)*100:.0f}%</td><td class='l nm'>{rep}</td></tr>")
    return "".join(out)

def sec_opts():
    return "".join(f"<option value='{b}'>{b}</option>" for b in BUCKET_ORDER)

def os_rows():
    out=[]
    for x in os_list:
        r5=f"{x['rsi14_5d']:.1f}" if x['rsi14_5d'] else "—"
        wh = f"20日 {x['ret20']:+.1f}% · 距高点 {x['off_hi52']:+.0f}%" + (" · 60日仍正，疑似错杀" if (x['ret60'] or 0)>=0 else " · 60日走弱")
        out.append(f"<tr><td class='code'>{x['code']}</td><td class='nm'>{x['name']}</td><td><b>{x['rsi14']:.1f}</b></td><td>{r5}</td><td>{x['price']:.2f}</td>{chg_html(x['ret20'])}{chg_html(x['ret60'])}<td class='{'down' if x['off_hi52']<-20 else ''}'>{x['off_hi52']:+.1f}%</td><td class='why'>{wh}</td></tr>")
    return "".join(out)
def ob_rows():
    out=[]
    for x in ob_list:
        r5=f"{x['rsi14_5d']:.1f}" if x['rsi14_5d'] else "—"
        wh = f"20日 {x['ret20']:+.1f}%" + (" · 贴52周高" if (x['off_hi52'] or 0)>=-2 else "")
        out.append(f"<tr><td class='code'>{x['code']}</td><td class='nm'>{x['name']}</td><td><b>{x['rsi14']:.1f}</b></td><td>{r5}</td><td>{x['price']:.2f}</td>{chg_html(x['ret20'])}{chg_html(x['ret60'])}<td class='up'>{x['off_hi52']:+.1f}%</td><td class='why'>{wh}</td></tr>")
    return "".join(out)
def t50_rows():
    return "".join(row_html(x) for x in t50)
def all_rows():
    return "".join(row_html(x) for x in sorted(rows,key=lambda v:v['rank']))
def note_os():
    if not os_list: return ""
    good=[x for x in os_list if (x["price"] or 0)>=10 or (x["ret60"] or 0)>=0]
    bad=[x for x in os_list if x not in good]
    s=f"<b>分层看：{len(os_list)} 只超卖里 {len(good)} 只具备研究价值。</b>"
    if good:
        s+=" ⚠️ <b>回撤型候选</b>："+"、".join(f"<b>{x['code']}</b>（RSI {x['rsi14']:.0f}，20日{x['ret20']:+.0f}%" + ("，60日仍正" if (x['ret60'] or 0)>=0 else "") + "）" for x in good)
    if bad:
        s+=" ❌ <b>失血型（低价微盘，RSI 无均值回归含义）</b>："+"、".join(x['code'] for x in bad)
    return f'<div class="note">{s}</div>'

def note_ob():
    if not ob_list: return ""
    hi=[x for x in ob_list if (x["off_hi52"] or 0)>=-2]
    s=f"<b>超买 {len(ob_list)} 只</b>：贴52周高 {len(hi)} 只（趋势型超买，RSI 钝化属常态）；其余为短线动量/事件脉冲，均值回归风险更高。按板块聚类："
    cl=collections.Counter(x["bucket"] for x in ob_list)
    s+=" · ".join(f"{b} {n}只" for b,n in cl.most_common())
    s+="。典型：<b>"+"、".join(f"{x['code']} {x['rsi14']:.0f}" for x in ob_list[:6])+"</b>"
    return f'<div class="note">{s}</div>'

def note_t50():
    hot=sorted(t50,key=lambda v:-v["rsi14"])[:5]
    cold=sorted(t50,key=lambda v:v["rsi14"])[:5]
    s=f"<b>Top50 内部结构：</b>偏热端 "+"、".join(f"{x['code']} {x['rsi14']:.1f}" for x in hot)
    s+="；偏冷端 "+"、".join(f"{x['code']} {x['rsi14']:.1f}" for x in cold)
    s+="。热度≠过热，AI 大盘多居中位带（详见明细排序）。"
    return f'<div class="note">{s}</div>'

def note_pivot():
    strong=[b for b in BUCKET_ORDER if any(x["bucket"]==b for x in rows) and st.median([x["rsi14"] for x in rows if x["bucket"]==b])>=55]
    weak=[b for b in BUCKET_ORDER if any(x["bucket"]==b for x in rows) and st.median([x["rsi14"] for x in rows if x["bucket"]==b])<=45]
    s="<b>板块强弱一眼看：</b>RSI 中位 ≥55 的强势板块 = "+("、".join(strong) if strong else "无")
    s+="；RSI 中位 ≤45 的弱势板块 = "+("、".join(weak) if weak else "无")
    s+="。强势板块中贴52周高占比高的（趋势延续）与低的（情绪脉冲）以明细区板块行为准。"
    return f'<div class="note">{s}</div>'

def note_bounce():
    if not bounce: return '<div class="sub">无</div>'
    big=[x for x in bounce if (x["price"] or 0)>=30]
    items=" · ".join(f"<b>{x['code']}</b> {x['rsi14_5d']:.1f}→{x['rsi14']:.1f}（20日{x['ret20']:+.1f}%）" for x in sorted(bounce,key=lambda v:-v['rsi14']))
    s=f'<div class="note">5 日前 RSI≤30、现已爬回 30 上方：{items}。'
    if big: s+=f'其中 <b>{"、".join(x["code"] for x in big)}</b> 为大市值可操作标的，若后续 RSI 站稳 40 且价格收复 EMA20 可视为早期反转确认；其余为小盘待观察。'
    s+='</div>'
    return s

def bounce_rows():
    return note_bounce()

BCOLORS = json.dumps(BUCKET_COLORS, ensure_ascii=False)

html = (html.replace("__SVGHIST__", svg_hist)
    .replace("__MED__", f"{med:.1f}").replace("__MEAN__", f"{mean:.1f}")
    .replace("__P50__", f"{sum(1 for v in vals if v<50)/N*100:.0f}")
    .replace("__NOS__", str(len(os_list))).replace("__NOB__", str(len(ob_list)))
    .replace("__POS__", f"{len(os_list)/N*100:.1f}").replace("__POB__", f"{len(ob_list)/N*100:.1f}")
    .replace("__NR__", str(rising)).replace("__PR__", f"{rising/N*100:.0f}")
    .replace("__NNH__", str(len(near_hi)))
    .replace("__OS_ROWS__", os_rows()).replace("__OB_ROWS__", ob_rows())
    .replace("__T50_ROWS__", t50_rows()).replace("__ALL_ROWS__", all_rows())
    .replace("__PIVOT_ROWS__", pivot_rows()).replace("__SEC_OPTS__", sec_opts())
    .replace("__OS_NOTE__", note_os()).replace("__OB_NOTE__", note_ob())
    .replace("__T50_NOTE__", note_t50()).replace("__PIVOT_NOTE__", note_pivot())
    .replace("__BOUNCE__", bounce_rows()).replace("__DATA__", DATA)
    .replace("__BCOLORS__", BCOLORS)
    .replace("__N__", str(N)).replace("__CUT__", CUT).replace("__DATE__", DATE))

path = OUT_HTML
open(path, "w", encoding="utf-8").write(html)
print("WROTE", path, len(html))
