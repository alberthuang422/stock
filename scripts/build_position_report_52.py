# -*- coding: utf-8 -*-
"""构建研报52：美股持仓组合技术面与操作建议（2026-08-28，数据截至 08-27 收盘）
8 标的：CSCO/MCD/VST/APO（波段多）+ ABBV/GILD（核心多）+ SBUX/XYZ（空头）
宏观：10Y-2Y 利差扩大验证、板块轮动验证（XLF/XLV 去趋势 vs 其余震荡）
浅底深字研报风 + ECharts + Okabe-Ito 色弱安全；红涨绿跌；静默写盘。
"""
import csv, os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUTD = os.path.join(ROOT, "reports", "52_持仓组合技术面与操作建议")
os.makedirs(OUTD, exist_ok=True)

TICKER_FILES = {
    "CSCO": "csco/csco, 1D.csv", "MCD": "mcd/mcd, 1D.csv", "VST": "vst/VST, 1D.csv",
    "APO": "apo/APO, 1D.csv", "ABBV": "abbv/ABBV, 1D.csv", "GILD": "gild/GILD, 1D.csv",
    "SBUX": "sbux/SBUX, 1D.csv", "XYZ": "xyz/xyz, 1D.csv",
}

def load(p):
    rows = []
    with open(os.path.join(DATA, p), encoding="utf-8") as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            if len(r) < 6 or not r[0] or not r[4]:
                continue
            try:
                rows.append([r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])])
            except ValueError:
                continue
    return rows

def ema(vals, n):
    k = 2 / (n + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out

# ------------- 读取 K 线数据（近 90 日）与均线 -------------
K = {}
for tk, p in TICKER_FILES.items():
    rows = load(p)
    closes = [r[4] for r in rows]
    seg = rows[-90:]
    n0 = len(rows) - 90
    kdata = [[r[0], round(r[1], 2), round(r[2], 2), round(r[3], 2), round(r[4], 2), int(r[5])] for r in seg]
    e10 = ema(closes, 10)[n0:]
    e20 = ema(closes, 20)[n0:]
    e50 = ema(closes, 50)[n0:]
    K[tk] = {
        "k": kdata,
        "dates": [r[0] for r in seg],
        "e10": [round(x, 2) for x in e10],
        "e20": [round(x, 2) for x in e20],
        "e50": [round(x, 2) for x in e50],
        "last": rows[-1][4],
        "last_date": rows[-1][0],
    }

# ------------- 板块温度计 / 轮动数据（已由验证脚本算出） -------------
SECTOR_TEMP = [  # 距253日最高收盘
    ("XLF 金融", -0.7), ("XLV 医疗", -1.7), ("XLE 能源", -2.3), ("SPY", -0.9),
    ("QQQ", -5.0), ("XLK 科技", -5.1), ("XLP 必需", -5.8), ("XLU 公用", -10.5), ("XLRE 地产", -16.0),
]
ROTATION = [  # 8/27 单日
    ("XLK", 3.16), ("SPY", 0.66), ("XLV", -1.13), ("XLRE", -0.95),
    ("XLU", -0.76), ("XLF", -0.65), ("XLE", -0.22), ("XLP", -1.38),
]
DAI_PAIRS = [  # (date, 10Y-2Y bp)
    ("06-22", 27), ("06-30", 26), ("07-07", 36), ("07-15", 42),
    ("07-22", 36), ("07-28", 35), ("08-07", 46), ("08-14", 44),
    ("08-20", 50), ("08-21", 50), ("08-24", 46), ("08-25", 47), ("08-26", 47),
]

# ------------- 逐标的操作建议（手工整理锚点，基于计算值） -------------
PLANS = [
    {
        "tk": "CSCO", "name": "思科", "dir": "多", "ptype": "波段",
        "logic": "箱体震荡（109–117）下沿企稳的博反弹；现价 112.15 位于 EMA20/EMA50（113.7）下方，RSI 45.5 中性偏弱、MACD 柱 −0.47 尚未转正——左侧信号未完备，宜等 109–110 试仓或收复 EMA20（113.7）跟进。CSCO 属 XLK 内部分化标的：科技板块 8/27 +3.16% 独强，但 CSCO 单日 −0.19% 未跟随，板块 beta 钝化。",
        "supports": [("109.2", "8/20 低"), ("107.5", "60日低")],
        "resists": [("117.3", "7/29 高"), ("124.7", "8/10 高")],
        "sl": "收盘 < 106.5（跌破 60 日低支撑区）", "targets": [("117", "+4.3%"), ("124", "+10.5%")],
        "pos": "波段反弹，仓位 ≤ 1/4 波段额度，左侧分批",
    },
    {
        "tk": "MCD", "name": "麦当劳", "dir": "多", "ptype": "波段",
        "logic": "RSI 36.7 偏弱临近超卖 + 260 支撑带的超卖反弹（详见专项验证节）。8/27 单日 −2.57% 创一年收盘新低，但 260–262 支撑带近一年仅 3 次盘中触及（7/22、7/23、8/27），前两次触及后 5 日内分别反弹至 264.8 / 274.5。该支撑带真实且历史有效。",
        "supports": [("259.9", "8/27 低·一年低点"), ("255", "缺口下沿")],
        "resists": [("270.5", "+4% 目标"), ("274", "7-8月平台")],
        "sl": "收盘 < 255（软）/ < 253（硬，一年低区下沿）", "targets": [("270.5", "+4.0%"), ("274", "+5.4%")],
        "pos": "波段反弹：RSI<35 或 259–261 放量止跌后分批，不追第一根暴跌",
    },
    {
        "tk": "VST", "name": "Vistra", "dir": "多", "ptype": "波段",
        "logic": "趋势已转空（现价 < EMA20 143.4 < EMA50 148.6 < EMA200 157.5），距 253 日高 219.8 已回撤 −36%。134.5 构成 8/7 与 8/24 双底，博反抽 EMA20（143.5）—但属下降趋势中的反弹，值博率与确定性弱于 MCD/APO。AI 电力长逻辑仍在，但利率敏感（XLU 月线 −3.9% 板块承压）。",
        "supports": [("134.5", "双底 8/7·8/24"), ("132.7", "253日低")],
        "resists": [("143.5", "EMA20"), ("150.2", "8/14 高")],
        "sl": "收盘 < 131（跌破 253 日低）", "targets": [("143.5", "+2.6%"), ("150", "+7.3%")],
        "pos": "波段：仅 134.5 双底确认后试单，否则等站回 EMA20；高波动（ATR 3.97%），仓位从严",
    },
    {
        "tk": "APO", "name": "阿波罗全球管理", "dir": "多", "ptype": "波段",
        "logic": "四只波段股中趋势最健康：现价 > EMA20 132.1 > EMA50 129.0 > EMA200 128.0，8/14 创新高 144.3 后回踩 130.8–131.0（8/25 低）未破坏上升结构，RSI 54.2 中性。资管板块（30 号报告背景）对陡峭化敏感，当前为震荡市中的强势标的。",
        "supports": [("130.8", "8/25 低"), ("126.7", "8/10 低")],
        "resists": [("144.3", "8/14 高"), ("153.3", "253日高")],
        "sl": "收盘 < 126.5（跌破 8/10 低，趋势破坏）", "targets": [("140", "+4.9%"), ("144.3", "+8.1%")],
        "pos": "波段：130–132 区间分批，跌破 126.5 离场",
    },
    {
        "tk": "ABBV", "name": "艾伯维", "dir": "多", "ptype": "核心",
        "logic": "多头趋势（> EMA20 256.9 > EMA50 248.9 > EMA200 229.0），8/19 与 8/25 两度高点 267 附近后两日回落至 258.2，属创新高后的正常整固，RSI 53.7 中性。核心防御（免疫/肿瘤管线）逻辑不变，回调即是核心仓加仓窗口。",
        "supports": [("256.9", "EMA20"), ("252.3", "7/22 低")],
        "resists": [("267.0", "8/19·8/25 高"), ("269+", "新高突破")],
        "sl": "收盘 < 245（EMA50 下方 1.5%）", "targets": [("270", "+4.6%"), ("新高", "破 267 后")],
        "pos": "核心：持有为主，回调 252–256 区间分批加仓",
    },
    {
        "tk": "GILD", "name": "吉利德", "dir": "多", "ptype": "核心",
        "logic": "六标的中趋势最强：> EMA20 141.2（偏离 +5.4%）> EMA50 136.4 > EMA200 130.9，8/19 突破 148.97 后平台整固，8/27 收 148.9 逼近前高。RSI 69.1 接近超买、距 253 高 157.3 仅 +5.6%——已走出主升，警惕高位波动，但核心持仓逻辑（HIV/肿瘤管线+防御属性）成立。",
        "supports": [("145", "8/21-26 平台"), ("141.2", "EMA20")],
        "resists": [("149.6", "8/26 高"), ("157.3", "253日高")],
        "sl": "收盘 < 138（跌破 EMA20 2%）", "targets": [("151.5", "+1.8%"), ("157.3", "+5.7%")],
        "pos": "核心：持有为主，RSI≥70 减持 1/3 波段化，回踩 145 不破可加",
    },
    {
        "tk": "SBUX", "name": "星巴克", "dir": "空", "ptype": "空头",
        "logic": "压力区博弈型空头（非基本面恶化）：现价 107.3，2026 年内 107–110.5 已反复测试 6 次未破（5/14 高 108.9、7/17 109.2、8/13 110.5、8/18 109.2），年内压力区真实有效——空头有技术依据。但需认清：①上方 113.5（2025-02）与 117.5（2025-03）是真实前高，110.5 只是年内区间上沿、非多年顶；②51 号报告实证 SBUX 2026 年以来 +25.9% 独立反弹（换帅+重组叙事），基本面在改善，本空头是'压力位赌回落'而非'基本面做空'，值博率全在压力区反复确认上；③风险结构呈收敛（低点 103-105 同步抬升），不是单边空头形态。",
        "supports": [("106.3", "EMA20·减半位"), ("104.9", "EMA50·目标"), ("103", "区间下沿·平仓")],
        "resists": [("108.6–110.5", "年内压力区"), ("113.5–117.5", "2025年前高·真反转区")],
        "sl": "激进：收盘 > 110.5（年内区间上沿跌破位）；稳健：收盘 > 114（2025年前高水平，真趋势反转）", "targets": [("104.9", "−2.2%"), ("103", "−4.0%")],
        "pos": "空头持有：压力区未破前持有，目标 104.9 减半、103 平仓；止损按仓位风险偏好选 110.5 或 114 两档",
    },
    {
        "tk": "XYZ", "name": "Block（原Square）", "dir": "空", "ptype": "空头",
        "logic": "压力区博弈型空头：现价 84.85，2026 年内 82–87 已反复测试 4 次未破（7/15 84.1、8/05 86.75、8/27 86.92），'年内多次突破失败'判断与数据一致，空头有依据。但需认清：①上方 87–99 是 2024-12/2025-01 真实成交区（高 99.26/94.25），86.9 只是年内区间上沿、非多年顶，真突破后第一目标仅 90–94；②基本面空头论据部分成立：50 号/sofi 报告——总营收仅 +9.3%、比特币收入 −12.8% 拖累、但毛利 +25%、资产负债表干净，是'增长钝化'而非'基本面恶化'；③形态呈收敛（低点 83.5→84.85 抬高），需警惕假突破扫损。",
        "supports": [("81.4", "EMA20·减半位"), ("79–80", "EMA50/前低带·目标"), ("77.2", "8/12 低")],
        "resists": [("86.9", "年内压力区"), ("90–94", "2024-25成交区·真反转区")],
        "sl": "激进：收盘 > 87（年内区间上沿）；稳健：收盘 > 90（2024-25 成交区下沿，真趋势反转）", "targets": [("81.4", "−4.1%"), ("79", "−6.9%")],
        "pos": "空头持有：86.9 压力区未破前持有，目标 81.4 减半、79 平仓；止损按风险偏好选 87 或 90 两档",
    },
]

def cls(v):
    return "up" if v > 0 else "dn"

# ------------- 构建 HTML -------------
def build_kline_js():
    """生成 8 个标的的 ECharts K 线 option"""
    charts = {}
    for tk, d in K.items():
        dates = d["dates"]
        kk = d["k"]
        vol = [[x[0], x[5]] for x in kk]
        vols = [x[5] for x in kk]
        vmax = max(vols) if vols else 1
        vol_data = [[i, x[1], 1] for i, x in enumerate(vol)]
        up_col = "#C0392B"  # 红涨
        dn_col = "#009E73"  # 绿跌
        # 预计算成交量柱子颜色（红涨绿跌），避免 f-string 内嵌表达式
        vol_colors = json.dumps([{"value": v, "itemStyle": {"color": up_col if kk[i][4] >= kk[i][1] else dn_col}} for i, v in enumerate(vols)])
        charts[tk] = f"""option_{tk} = {{
  backgroundColor: 'transparent',
  animation: false,
  dataZoom: [{{type:'inside', start: 55, end: 100}}],
  tooltip: {{trigger: 'axis', axisPointer: {{type: 'cross'}}, backgroundColor: 'rgba(255,255,255,.97)', borderColor:'#d9e1ec', textStyle: {{color:'#1f2733'}}}},
  axisPointer: {{link: [{{xAxisIndex: 'all'}}]}},
  grid: [{{left: 55, right: 18, top: 18, height: '58%'}}, {{left: 55, right: 18, top: '80%', height: '14%'}}],
  xAxis: [{{type: 'category', data: {json.dumps(dates)}, gridIndex: 0, axisLine: {{lineStyle:{{color:'#c9d2de'}}}}, axisLabel: {{color:'#5b6675', fontSize:10}}, axisTick: {{show:false}}}},
          {{type: 'category', data: {json.dumps(dates)}, gridIndex: 1, axisLabel: {{show: false}}, axisTick: {{show:false}}, axisLine: {{lineStyle:{{color:'#c9d2de'}}}}}}],
  yAxis: [{{scale: true, gridIndex: 0, splitLine: {{lineStyle:{{color:'#eef1f6'}}}}, axisLabel: {{color:'#5b6675'}}}},
          {{gridIndex: 1, splitLine: {{show:false}}, axisLabel: {{show:false}}}}],
  series: [
    {{name: 'K线', type: 'candlestick', data: {json.dumps([[x[1], x[4], x[3], x[2]] for x in kk])},
      itemStyle: {{color: '{up_col}', color0: '{dn_col}', borderColor: '{up_col}', borderColor0: '{dn_col}'}}}},
    {{name: 'EMA10', type: 'line', data: {json.dumps(d['e10'])}, smooth: true, showSymbol: false, lineStyle: {{width: 1.2, color: '#E69F00'}}}},
    {{name: 'EMA20', type: 'line', data: {json.dumps(d['e20'])}, smooth: true, showSymbol: false, lineStyle: {{width: 1.2, color: '#0072B2'}}}},
    {{name: 'EMA50', type: 'line', data: {json.dumps(d['e50'])}, smooth: true, showSymbol: false, lineStyle: {{width: 1.2, color: '#CC79A7'}}}},
    {{name: '量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
      data: {vol_colors}
    }}
  ]
}};"""
    return charts

KJS = build_kline_js()

def plan_rows():
    rows = []
    for p in PLANS:
        sup = " / ".join(f"{a}（{b}）" for a, b in p["supports"])
        res = " / ".join(f"{a}（{b}）" for a, b in p["resists"])
        tg = " / ".join(f"{t}（{v}）" for t, v in p["targets"])
        dcls = "up" if p["dir"] == "多" else ("na" if p["dir"] == "观望" else "dn")
        rows.append(
            f"<tr><td class='nowrap'><b>{p['tk']}</b> <span class='muted'>{p['name']}</span></td>"
            f"<td class='{dcls}' style='font-weight:700'>{p['dir']}</td>"
            f"<td class='nowrap'><span class='ptag'>{p['ptype']}</span></td>"
            f"<td class='l'>{p['logic']}</td>"
            f"<td class='nowrap'>{sup}</td><td class='nowrap'>{res}</td>"
            f"<td class='nowrap'>{p['sl']}</td><td class='nowrap'>{tg}</td></tr>")
    return "".join(rows)

def detail_blocks():
    """逐标的卡片：K线图 + 锚点表"""
    blocks = []
    for p in PLANS:
        tk = p["tk"]
        sup = " / ".join(f"{a}（{b}）" for a, b in p["supports"])
        res = " / ".join(f"{a}（{b}）" for a, b in p["resists"])
        tg = " / ".join(f"{t}（{v}）" for t, v in p["targets"])
        dcls = "up" if p["dir"] == "多" else ("na" if p["dir"] == "观望" else "dn")
        arrow = {"多": "▲ 做多", "观望": "◇ 观望", "空": "▼ 做空"}[p["dir"]]
        blocks.append(f"""
  <div class="card">
    <h2>{p['tk']} · {p['name']} · <span class="dir-{p['dir']}">{arrow}</span> <span class="tag">{p['ptype']}</span></h2>
    <div class="logic">{p['logic']}</div>
    <div id="chart_{tk}" class="chart"></div>
    <table class="anchor">
      <tr><th>支撑位</th><th>阻力位</th><th>止损</th><th>目标</th></tr>
      <tr><td>{sup}</td><td>{res}</td><td>{p['sl']}</td><td>{tg}</td></tr>
    </table>
    <div class="note posnote"><b>操作：</b>{p['pos']}</div>
  </div>""")
    return "\n".join(blocks)

# 板块温度计行（横向条形）
def temp_bar():
    mx = max(a for _, a in SECTOR_TEMP)
    return f"""
    <table class="temp">
      <tr><th>板块 / 指数</th><th>距一年收盘高</th><th style="width:46%">位置</th></tr>
      {''.join(
        f"<tr><td>{name}</td><td class='{cls(v)}'><b>{v:+.1f}%</b></td>"
        f"<td><div class='bar'><div class='fill {cls(v)}' style='width:{max(2, abs(v)/mx*100):.0f}%'></div></div></td></tr>"
        for name, v in SECTOR_TEMP)}
    </table>"""

def rot_bar():
    return f"""
    <table class="temp">
      <tr><th>板块</th><th>8/27 单日</th><th style="width:50%">移动</th></tr>
      {''.join(
        f"<tr><td>{name}</td><td class='{cls(v)}'><b>{v:+.2f}%</b></td>"
        f"<td><div class='hbar'><div class='hfill {cls(v)}' style='width:{(abs(v)/4.2)*100:.0f}%'></div></div></td></tr>"
        for name, v in ROTATION)}
    </table>"""

def dai_chart():
    return f"""
    <div id="chart_dai" class="chart-sm"></div>"""

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>持仓组合技术面与操作建议 · 52</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root {{ --ink:#1f2733; --sub:#5b6675; --line:#e3e8ef; --bg:#f7f9fc; --card:#fff;
          --blue:#0072B2; --orange:#E69F00; --sky:#56B4E9; --green:#009E73; --purple:#CC79A7;
          --red:#C0392B; --verm:#D55E00; --grey:#8c97a6; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--ink); font-family: -apple-system, "PingFang SC",
         "Microsoft YaHei", "Helvetica Neue", sans-serif; line-height: 1.65; padding: 24px 16px 60px; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; }}
  h1 {{ font-size: 26px; letter-spacing: .5px; margin-bottom: 4px; }}
  .subtitle {{ color: var(--sub); font-size: 13px; margin-bottom: 22px; }}
  .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(20,30,50,.05); }}
  .card h2 {{ font-size: 17px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
  .card h2::before {{ content: ""; width: 4px; height: 16px; background: var(--blue); border-radius: 2px; }}
  .grid3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 4px; }}
  .grid4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
  .kv {{ background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }}
  .kv .k {{ font-size: 12px; color: var(--sub); }}
  .kv .v {{ font-size: 21px; font-weight: 700; margin-top: 2px; }}
  .kv .v small {{ font-size: 12px; font-weight: 400; color: var(--sub); }}
  .kv .muted {{ font-size: 13px; color: var(--sub); margin-top: 4px; font-weight: 400; }}
  .up {{ color: var(--red); }} .dn {{ color: var(--green); }} .na {{ color: var(--grey); }}
  .tag {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 20px;
         background: #eef3fb; color: var(--blue); margin-left: 6px; vertical-align: 2px; }}
  .dir-多 {{ color: var(--red); font-weight: 700; }}
  .dir-空 {{ color: var(--green); font-weight: 700; }}
  .ptag {{ display: inline-block; font-size: 11px; padding: 1px 8px; border-radius: 4px;
          background: #f0f2f6; color: var(--sub); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; margin-top: 6px; }}
  th, td {{ padding: 8px 8px; text-align: right; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ background: #f1f4f9; font-weight: 600; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  td.l {{ text-align: left; }}
  tr.hl {{ background: #f4f8ff; }}
  .note {{ font-size: 12.5px; color: var(--sub); margin-top: 10px; }}
  .logic {{ font-size: 13.5px; color: var(--ink); background: #f7f9fc; border: 1px solid var(--line);
           border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; }}
  .posnote {{ background: #f4f8ff; border-left: 3px solid var(--blue); padding: 8px 12px; border-radius: 0 6px 6px 0; }}
  table.anchor th, table.anchor td {{ text-align: left; }}
  .chart {{ width: 100%; height: 380px; }}
  .chart-sm {{ width: 100%; height: 260px; }}
  .concl {{ border-left: 4px solid var(--blue); background: #f4f8ff; padding: 12px 16px;
           border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }}
  .risk {{ border-left: 4px solid var(--verm); background: #fdf6ee; padding: 12px 16px;
          border-radius: 0 8px 8px 0; font-size: 14px; margin-top: 10px; }}
  ul.tl {{ list-style: none; }}
  ul.tl li {{ padding: 8px 0 8px 18px; border-left: 2px solid var(--line); margin-left: 6px; position: relative; }}
  ul.tl li::before {{ content: ""; position: absolute; left: -5px; top: 14px; width: 8px; height: 8px;
                     border-radius: 50%; background: var(--blue); }}
  ul.tl li b {{ color: var(--blue); }}
  .legend-dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; }}
  .disclaimer {{ font-size: 12px; color: var(--sub); margin-top: 16px; border-top: 1px dashed var(--line);
                padding-top: 12px; }}
  .src {{ font-size: 11.5px; color: var(--sub); margin-top: 8px; }}
  .sect-title {{ font-size: 19px; font-weight: 700; margin: 26px 0 12px; display: flex; align-items: center; gap: 8px; }}
  .sect-title::before {{ content: ""; width: 5px; height: 18px; background: var(--verm); border-radius: 2px; }}
  table.temp td, table.temp th {{ text-align: left; }}
  .bar {{ background: #eef1f6; border-radius: 6px; height: 10px; width: 100%; }}
  .fill {{ height: 10px; border-radius: 6px; }}
  .fill.up {{ background: var(--red); }} .fill.dn {{ background: var(--green); }}
  .hbar {{ background: #f1f4f9; border-radius: 6px; height: 10px; width: 100%; position: relative; }}
  .hfill {{ height: 10px; border-radius: 6px; }}
  .hfill.up {{ background: var(--red); }} .hfill.dn {{ background: var(--green); float: right; }}
  @media (max-width: 760px) {{ .grid3, .grid4 {{ grid-template-columns: 1fr 1fr; }}
    .chart {{ height: 320px; }} }}
</style>
</head>
<body>
<div class="wrap">

  <h1>美股持仓组合 · 技术面与操作建议</h1>
  <div class="subtitle">8 标的逐一个股拆解（核心多 2 + 波段多 4 + 空头 2） · 宏观前提：通胀粘滞 + 10Y-2Y 利差扩大 · 市场结构：指数横盘 + 板块快速轮动 · 数据截至 2026-08-27（周四）收盘 · 生成于 2026-08-28</div>

  <!-- 核心结论 -->
  <div class="card">
    <h2>一图总览 · 逐标的操作建议</h2>
    <table>
      <tr><th>代码/名称</th><th>方向</th><th>性质</th><th>核心逻辑</th><th>支撑位</th><th>阻力位</th><th>止损</th><th>目标位</th></tr>
      {plan_rows()}
    </table>
    <div class="note"><b>参数图例</b>：支撑/阻力取近 90 日 swing 高低点 + 均线 + 整数关口，标注来源日期；止损统一为<b>收盘价</b>跌破即离场（非盘中）；目标价为离场参考区间，波段目标按回测/形态给 2 档。趋势判断基于 EMA10/20/50/200 排列。数据口径：Yahoo 复权日线，前复权一致性（ABBV/GILD 2015 起、VST 2016 起、其余 1990 起）。</div>
  </div>

  <!-- 宏观背景 -->
  <div class="sect-title">宏观背景：通胀粘滞 + 曲线陡峭化，利率敏感板块受压</div>
  <div class="card">
    <h2>10Y-2Y 利差：6 月末 +27bp → 8 月末 +47bp，长端上行主导</h2>
    <div class="grid4">
      <div class="kv"><div class="k">10Y 收益率</div><div class="v">4.66%</div><div class="muted">8/26，6月末 4.47%</div></div>
      <div class="kv"><div class="k">2Y 收益率</div><div class="v">4.19%</div><div class="muted">8/26，6月末 4.05%</div></div>
      <div class="kv"><div class="k">利差 10Y-2Y</div><div class="v">+47<span class="up"> bp</span></div><div class="muted">6月末 +27bp → 扩大 +20bp</div></div>
      <div class="kv"><div class="k">驱动端</div><div class="v">长端</div><div class="muted">10Y +19bp vs 2Y +14bp，通胀粘滞/长债供给为主因</div></div>
    </div>
    {dai_chart()}
    <div class="concl">
      ① <b>利差扩大为"长端上行驱动"（熊陡），对长久期资产最不利</b>：XLU（波动率利差敏感）8 月以来 −1.4%、XLP −0.3%、XLRE −0.9% 全部逆势走弱，SPY 同期 +1.1%——利率敏感板块被持续抽血，验证"其他板块震荡、资金不往利率久期处去"。<br>
      ② <b>对持仓的直接含义</b>：VST（IPP/独立发电，长债久期属性 +31% 回撤）是组合内对曲线陡峭化敞口最大的标的；APO（资管）历史上对"大幅走阔（>+30bp/月）"重挫，当前 +20bp/两月幅度温和，但需跟踪单月速率；ABBV/GILD（医药）利率久期中性，防御属性受益于风险偏好收敛。<br>
      ③ <b>约束</b>：2Y 未大幅上行说明美联储政策路径预期仍稳，曲线陡峭化本身不必然利空指数——它更多是"类别的轮动压力"而非"systemic 风险信号"。
    </div>
    <div class="src">数据：FRED DGS2/DGS10（截至 2026-08-26 收盘）。利差 = 10Y − 2Y。2026-05 以来区间实测：6/22 最低 +27bp → 8/20 最高 +50bp → 8/26 +47bp。注：FRED 末个数据点 8/26（8/27 未发布）。</div>
  </div>

  <!-- 市场结构：板块轮动验证 -->
  <div class="sect-title">市场结构验证：指数横盘，仅金融/医疗有趋势</div>
  <div class="card">
    <h2>板块温度计：距一年收盘高</h2>
    {temp_bar()}
    <div class="concl">
      <b>与你"只有 XLF/XLV 去趋势、其余震荡"的判断一致</b>：XLF 距一年高 −0.7%（8/5 刚创 253 日新高，趋势延续）、XLV −1.7%（8/19 创新高）——两个板块在趋势位；SPY −0.9%（60 日净变 +2.2%，横盘确认）；震荡的代表是 XLP −5.8%、XLU −10.5%、XLRE −16.0%（利率长尾拖累）。<b>例外提示</b>：XLK 距高 −5.1% 但近 1 月 +13.2%、8/27 单日 +3.16% 正在向上试探，是"震荡中带方向"的板块。
    </div>
  </div>

  <div class="card">
    <h2>8/27 单日轮动实证：科技独强吸金，防御集体失血</h2>
    {rot_bar()}
    <div class="concl">
      单日剪刀差高达 <b>4.5pp（XLK +3.16% vs XLP −1.38%）</b>，XLV/XLU/XLRE 全线下跌。这条对持仓有直接指示：<b>MCD 8/27 暴跌 −2.57% 的部分原因是防御板块被轮动抽血</b>（非公司基本面单独恶化）；反之，仓位最重的防御性核心（ABBV/GILD）今日小幅回调属于板块β，不是个股破位。
    </div>
  </div>

  <!-- 逐标的 -->
  <div class="sect-title">逐标的拆解（K线 · EMA10/20/50 · 近 90 交易日）</div>
  {detail_blocks()}

  <!-- MCD 专项 -->
  <div class="card">
    <h2>MCD 专项：RSI 超卖反弹逻辑验证 <span class="tag">回测结论 48/49 号</span></h2>
    <div class="grid3">
      <div class="kv"><div class="k">当前 RSI(14)</div><div class="v">36.7</div><div class="muted">偏弱（30–45 档），尚未到超卖 &lt;30</div></div>
      <div class="kv"><div class="k">8/27 低点</div><div class="v">259.85</div><div class="muted">一年新低 · 260 支撑带第 3 次试探</div></div>
      <div class="kv"><div class="k">ATR(14)</div><div class="v">2.01%</div><div class="muted">近 30 日 3 次单日跌 &gt;2%</div></div>
    </div>
    <div class="concl">
      <b>验证结论：反弹逻辑成立，但"4% 是窗口内最高反弹、不是 20 日确定收益"</b>。<br>
      ① <b>回测证据（48 号）</b>：MCD RSI 下穿 40 后 20 日窗口 <b>maxG 中位 +3.4% ~ +5.0%</b>（35-40 档 +3.77% / 30-35 档 +4.53% / &lt;30 档 +4.99%），<b>你的 4% 目标与 maxG 中位（+4.0% 附近）吻合</b>——作为"反弹离场目标"合理。<br>
      ② <b>但（49 号）</b>：fwd20 中位只有 +1.3%~+2.2%，且<b>三档超额全部 ≤0（弹性弱于大盘）</b>——这是"抢自己弹回来的钱"，不是"跑赢大盘的钱"。4% 应理解为"弹到 270.5 即止盈、不恋战"，而非持股 20 日等 4%。<br>
      ③ <b>触发条件</b>：RSI 尚未进入最优档（&lt;35）。可等 RSI≤35（现 36.7）或 259–261 放量止跌后分批介入；若直接跌破 255，反弹逻辑推迟到 250–253 区间（一年低区下沿）。<br>
      ④ <b>止损纪律</b>：收盘 &lt;255 减半、&lt;253 全离。260 支撑带近一年仅 3 次盘中触及、前两次均 5 日内反弹（至 264.8/274.5），历史上继续深跌的次数少，但单次深跌（8/27 −2.57%）已被观察到，止损不可省略。
    </div>
  </div>

  <!-- 组合风险 -->
  <div class="card">
    <h2>组合风险提示与仓位管理</h2>
    <ul class="tl">
      <li><b>风险 1 · 波动率分布不均</b>：VST（ATR 3.97%）、APO（3.09%）贡献主要波动；ABBV（2.25%）、MCD（2.01%）次之。若 VST 仓位偏重，组合波动被单一 IP 标的放大。<b>建议：单标的波段仓 ≤ 15%，VST 因趋势转空额外减半。</b></li>
      <li><b>风险 2 · 波段仓集体逆风</b>：CSCO/MCD/VST 三只波段股现价均低于 EMA50（空头/震荡形态），只有 APO 在多头结构上。叠加"指数横盘+轮动快"，波段仓胜率环境一般，<b>建议波段总仓位压至组合 1/4 以下，且全部严格执行收盘止损</b>。</li>
      <li><b>风险 3 · 板块轮动抽血防御</b>：8/27 XLK 单日 +3.16% 抽走防御资金（MCD −2.57% 即为典型）。核心仓 ABBV/GILD 同为防御属性，短期会跟随板块波动，<b>不因单日回撤误判为个股破位</b>。</li>
      <li><b>风险 4 · 利率曲线陡峭化的板块重估</b>：长端 4.66% 且继续上行预期下，VST 的 IPP 久期属性、以及任何高估值成长仓继续承压；若 10Y 突破 4.8%，需系统性下调 VST 目标并评估 APO 敞口（30 号报告：大幅走阔 &gt;+30bp/月时资管 −6.8%）。</li>
      <li><b>风险 5 · 空头腿的性质：压力区博弈，不是趋势空</b>：SBUX/XYZ 空头依据是<b>年内压力区反复测试未破</b>（SBUX 107–110.5 六次未破、XYZ 82–87 四次未破），技术上有据——但二者均站上均线（多头排列）、上方存在 2024-25 真实成交区（SBUX 113.5–117.5、XYZ 90–94）。<b>风险量化：压力区是区间上沿而非多年顶，真突破的第一目标是上方成交区（有限涨幅），谈不上"亏损无上限"；真正须切换判断的是站上历史成交区（SBUX&gt;114 / XYZ&gt;90）——那才构成趋势反转，届时无条件离场</b>。</li>
    </ul>
    <div class="risk">
      <b>总体判断</b>：组合结构上"核心多（ABBV/GILD）健康可持有、波段多（CSCO/MCD/VST/APO）需精挑时点、空头腿（SBUX/XYZ）为压力区博弈——技术上有据（年内反复未破）但非趋势空，止损按压力区（激进）或历史成交区（稳健）双档执行"。在指数横盘+板块轮动的环境下，<b>核心仓位纪律 &gt; 波段进攻</b>：建议维持核心 55–60%、波段 ≤25%、现金 ≥15% 的配置，波段仓全部以收盘止损为硬约束，MCD 加仓等待 RSI≤35 或止跌确认。
    </div>
    <div class="disclaimer">免责声明：本报告基于公开行情数据（Yahoo Finance 复权日线、FRED 国债数据）与量化统计，仅供参考，不构成投资建议。支撑/阻力/止损/目标为技术分析参考位，非保证。过往回测表现不预示未来收益。市场有风险，投资需谨慎。</div>
  </div>

</div>

<script>
{KJS["CSCO"]}
{KJS["MCD"]}
{KJS["VST"]}
{KJS["APO"]}
{KJS["ABBV"]}
{KJS["GILD"]}
{KJS["SBUX"]}
{KJS["XYZ"]}
const colors = {{ up: '#C0392B', dn: '#009E73' }};
Object.keys(window).forEach(k => {{
  if (k.startsWith('option_')) {{
    const el = document.getElementById('chart_' + k.slice(7));
    if (el) {{ const c = echarts.init(el, null, {{renderer: 'canvas'}}); c.setOption(window[k]); }}
  }}
}});
// 利差图
const dai = echarts.init(document.getElementById('chart_dai'));
dai.setOption({{
  tooltip: {{trigger: 'axis', backgroundColor: 'rgba(255,255,255,.97)', borderColor: '#d9e1ec', textStyle: {{color: '#1f2733'}}}},
  grid: {{left: 45, right: 15, top: 12, bottom: 24}},
  xAxis: {{type: 'category', data: {json.dumps([x[0] for x in DAI_PAIRS])}, axisLine: {{lineStyle:{{color:'#c9d2de'}}}}, axisLabel: {{color:'#5b6675', fontSize: 10}}}},
  yAxis: {{type: 'value', min: 20, max: 55, splitLine: {{lineStyle:{{color:'#eef1f6'}}}}, axisLabel: {{color:'#5b6675', formatter: '{{value}}bp'}}}},
  series: [{{name: '10Y-2Y (bp)', type: 'line', data: {json.dumps([x[1] for x in DAI_PAIRS])}, smooth: true,
    lineStyle: {{color: '#0072B2', width: 2}}, itemStyle: {{color: '#0072B2'}}, showSymbol: true,
    markLine: {{data: [{{yAxis: 35}}], label: {{formatter: '6月末水平'}}, lineStyle: {{color: '#8c97a6', type: 'dashed'}}}}}}]
}});
window.addEventListener('resize', () => {{ Object.keys(window).forEach(k => {{ if (k.startsWith('option_')) {{ const el = document.getElementById('chart_' + k.slice(7)); if (el) {{ echarts.getInstanceByDom(el)?.resize(); }} }} }}); dai.resize(); }});
</script>
</body>
</html>"""

# 写入
with open(os.path.join(OUTD, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
size = os.path.getsize(os.path.join(OUTD, "index.html"))
print(f"written: reports/52_持仓组合技术面与操作建议/index.html  size={size//1024}KB")