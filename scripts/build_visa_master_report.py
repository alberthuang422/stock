# -*- coding: utf-8 -*-
"""V/MA（银行卡网络）× KBWB（银行ETF）+ × QQQ/XLK（科技）相关性研报生成器
读 results/visa_master_corr.json；输出 reports/27_银行卡网络_银行科技相关性/
规范：普通三引号模板 + @@PLACEH@@ 占位符 replace（避免 f-string 与 JS 花括号冲突）
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "..", "reports", "27_银行卡网络_银行科技相关性")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(BASE, "..", "results", "visa_master_corr.json"), encoding="utf-8") as f:
    D = json.load(f)

SPLIT = D["split"]
P = D["pairs"]
meta = D["meta"]


def js(o):
    return json.dumps(o, ensure_ascii=False)


# ---------- 动态片段 ----------
def blocks_rows(pair, xlab, ylab):
    rows = ""
    for b in pair["blocks"]:
        if not b["n"]:
            continue
        rows += (f"""<tr><td>{b['name']}</td><td>{b['n']:,}</td><td class="hl">{b['pearson']:.3f}</td>"""
                 f"""<td>{b['spearman']:.3f}</td><td>{b['beta']:+.2f}</td><td>{b['r2']:.2f}</td>"""
                 f"""<td>{b['p_same_dir']:.0f}%</td><td class="up">{b['x_up_y_avg']:+.2f}%</td>"""
                 f"""<td class="dn">{b['x_dn_y_avg']:+.2f}%</td></tr>""")
    return rows


def price_rows(pair):
    rows = ""
    for key, label in [("full", "全期"), ("after_split", f"分界后（{SPLIT} 起）"),
                       ("last1y", "近 1 年（2025-08 起）"), ("ytd", "2026 年以来")]:
        pb = pair["price_blocks"][key]
        x_ = pb.get(pair["xname"]) or pb.get("x")
        y_ = pb.get(pair["yname"].lower()) or pb.get(pair["yname"]) or pb.get("y")
        if not x_ or not y_:
            continue
        rows += f"""<tr><td>{label}</td>
            <td><span class="hl">{x_['total_ret']:+.0f}%</span> / <b class="hl">{y_['total_ret']:+.0f}%</b></td>
            <td>{x_['max_dd']:.0f}% / {y_['max_dd']:.0f}%</td>
            <td>{x_['ann_vol']:.0f}% / {y_['ann_vol']:.0f}%</td>
            <td>{x_['sharpe']:.2f} / <b>{y_['sharpe']:.2f}</b></td></tr>"""
    return rows


def yearly_rows(pair):
    rows = ""
    for y in pair["years"]:
        r = pair["yearly"].get(str(y)) or pair["yearly"].get(y)
        if not r:
            continue
        x_c = "up" if r["x"] >= 0 else "dn"
        y_c = "up" if r["y"] >= 0 else "dn"
        diff = r["x"] - r["y"]
        diff_c = "up" if diff >= 0 else "dn"
        rows += f"""<tr><td>{y}</td><td class="{x_c}">{r['x']:+.1f}%</td><td class="{y_c}">{r['y']:+.1f}%</td>"""
        rows += f"""<td class="{diff_c}">{diff:+.1f}pp</td></tr>"""
    return rows


def yearly_chart_series(pair):
    """按对返回 {years, series_a, series_b} 用于 ECharts"""
    ys = [str(y) for y in pair["years"]]
    a = [(pair["yearly"].get(y) or pair["yearly"].get(int(y)))["x"] for y in ys]
    b = [(pair["yearly"].get(y) or pair["yearly"].get(int(y)))["y"] for y in ys]
    return {"years": ys, "a": a, "b": b}


# 关键 KPI：V/MA × KBWB
vk = P["V"]
mk = P["MA"]
kt = P["V_vs_QQQ"]
mt = P["MA_vs_QQQ"]
xlk_v = P["V_vs_XLK"]
xlk_m = P["MA_vs_XLK"]

verdict_1 = f"""
    <div class="verdict">
      <div class="t">核心结论 · 任务①：银行卡网络 × 银行板块（KBWB）</div>
      <div class="b">全期正相关（V×KBWB <span class="hlb">0.55</span> / MA×KBWB <span class="hlb">0.56</span>），但
        <span class="hl">2026-02 起结构性脱钩</span>：分界后 Pearson 骤降至 <span class="hlb">0.23 / 0.25</span>
        （Fisher z = 4.6 / 4.5，显著），60 日滚动最新仅 <span class="hlb">0.13 / 0.10</span>，近 1 年同向占比降至 ~58% / 57%。
        银行卡是<b>交易处理费模式</b>（按交易额抽成，V/MA 费率模式），银行是<b>利差模式</b>（净息差），2026 年典型的有
        X 案例：KBWB 随利率上行走强（2026 YTD <span class="hl">+12.8%</span>），V/MA 却跑输（<span class="hl">+7.7% / +3.6%</span>）——
        板块驱动（利率）与个股驱动（估值、反垄断、监管、AI叙事）开始分离。
      </div>
    </div>"""

verdict_2 = f"""
    <div class="verdict">
      <div class="t">核心结论 · 任务②：银行卡网络 × 科技板块（QQQ/XLK）</div>
      <div class="b">全期相关更高（<span class="hlb">0.61~0.62</span>，历史两者同属「成长+流动性敏感」篮子），但
        <span class="hl">2026 年脱钩更彻底</span>：分界后 4 组相关全部 <span class="hl">≈0 或转负</span>（V×QQQ <span class="hlb">−0.03</span>、
        V×XLK <span class="hlb">−0.10</span>），60 日滚动最新 <span class="hlb">−0.26 ~ −0.42</span>，处历史最低区间。
        近 1 年 XLK <span class="hl">+42.3%</span> vs MA <span class="hl">−1.3%</span>，板块 beta 从全期 0.42~0.52 塌缩到
        分界后的 <b>≈0</b>（V×XLK 甚至 −0.13）。科技上涨由 AI（英伟达/半导体）驱动，V/MA 的「AI 支付叙事」与
        <b>实际盈利兑现节奏错位</b>，相关性被打破。
      </div>
    </div>"""

# 相对强弱表格（纯表格片段，注入 ⑪ 卡片内）
ratio_blocks = f"""
      <div class="scroll">
      <table>
        <tr><th>比值</th><th>最新归一化</th><th>历史高点（时段）</th><th>历史低点（时段）</th><th>解读</th></tr>
        <tr><td>KBWB / V</td><td class="hlb">{P['V']['ratio']['norm_latest']:.2f}</td>
            <td>{P['V']['ratio']['max']:.2f}（{P['V']['ratio']['max_date']}）</td>
            <td>{P['V']['ratio']['min']:.2f}（{P['V']['ratio']['min_date']}）</td>
            <td>V 长期跑赢板块，2026 年收敛</td></tr>
        <tr><td>KBWB / MA</td><td class="hlb">{P['MA']['ratio']['norm_latest']:.2f}</td>
            <td>{P['MA']['ratio']['max']:.2f}（{P['MA']['ratio']['max_date']}）</td>
            <td>{P['MA']['ratio']['min']:.2f}（{P['MA']['ratio']['min_date']}）</td>
            <td>MA 长期跑赢更明显，2026 年收敛</td></tr>
        <tr><td>QQQ / V</td><td class="hlb">{P['V_vs_QQQ']['ratio']['norm_latest']:.2f}</td>
            <td>{P['V_vs_QQQ']['ratio']['max']:.2f}（{P['V_vs_QQQ']['ratio']['max_date']}）</td>
            <td>{P['V_vs_QQQ']['ratio']['min']:.2f}（{P['V_vs_QQQ']['ratio']['min_date']}）</td>
            <td>科技 2023 年起显著跑赢 V</td></tr>
        <tr><td>XLK / MA</td><td class="hlb">{P['MA_vs_XLK']['ratio']['norm_latest']:.2f}</td>
            <td>{P['MA_vs_XLK']['ratio']['max']:.2f}（{P['MA_vs_XLK']['ratio']['max_date']}）</td>
            <td>{P['MA_vs_XLK']['ratio']['min']:.2f}（{P['MA_vs_XLK']['ratio']['min_date']}）</td>
            <td>近 1 年科技 vs MA 分化最大</td></tr>
      </table>
      </div>
      <div class="note">归一化起点 = 区间首日比值。数值 <1 意味着分母（银行卡）相对走强，<span class="hl">&gt;1 意味着板块/科技相对银行卡走强</span>。</div>
    """

# 年度收益对比（双柱：V/MA 与 KBWB）
yc_v_kbwb = yearly_chart_series(P["V"])
yc_ma_kbwb = yearly_chart_series(P["MA"])
yc_v_qqq = yearly_chart_series(P["V_vs_QQQ"])
yc_ma_xlk = yearly_chart_series(P["MA_vs_XLK"])

# 2026 年相对表现速览
def y26_of(pair):
    r = pair["yearly"].get("2026") or pair["yearly"].get(2026)
    return r

y26_v_kbwb = y26_of(P["V"])
y26_ma_kbwb = y26_of(P["MA"])
y26_v_qqq = y26_of(P["V_vs_QQQ"])
y26_ma_xlk = y26_of(P["MA_vs_XLK"])

# ---------- 模板 ----------
html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>银行卡网络 vs 银行板块 / 科技板块 · V/MA 相关性拆解</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root{--bg:#f7f8fa;--card:#fff;--ink:#1f2329;--sub:#6b7280;--line:#e5e7eb;
        --red:#d23b2e;--green:#1a9e4b;--blue:#1f4e79;--orange:#e67e22;--purple:#7048e8;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:24px 16px 48px;}
  .wrap{max-width:1220px;margin:0 auto;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.05);}
  h1{font-size:21px;margin-bottom:4px;}
  .meta{color:var(--sub);font-size:12.5px;margin-bottom:14px;}
  h2{font-size:16px;margin:0 0 12px;padding-left:10px;border-left:4px solid var(--blue);}
  h3{font-size:14px;margin:14px 0 8px;}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:14px;}
  .kpi{background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .kpi .num{font-size:22px;font-weight:700;color:var(--ink);}
  .kpi .lab{color:var(--sub);font-size:12px;margin-top:2px;}
  .verdict{background:linear-gradient(135deg,#eef4ff,#f4f0ff);border:1px solid #d7e0f7;border-radius:12px;padding:16px 20px;margin-top:14px;}
  .verdict .t{font-size:13px;color:var(--sub);margin-bottom:6px;}
  .verdict .b{font-size:15px;font-weight:700;line-height:1.75;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th{background:#f3f5f8;text-align:left;padding:7px 9px;border-bottom:2px solid var(--line);white-space:nowrap;font-weight:600;}
  td{padding:6px 9px;border-bottom:1px solid #f0f1f3;white-space:nowrap;}
  td.up{color:var(--red);font-weight:600;} td.dn{color:var(--green);font-weight:600;} td.na{color:#c3c8cf;}
  .scroll{overflow-x:auto;}
  .chart{width:100%;height:380px;}
  .chart.sm{height:320px;}
  .note{color:var(--sub);font-size:12px;margin-top:8px;}
  .keypoint{background:#eef7f2;border:1px solid #cde8da;border-radius:10px;padding:12px 16px;font-size:12.5px;color:#17442f;margin-top:10px;}
  .dis{color:var(--sub);font-size:12px;border-top:1px dashed var(--line);padding-top:12px;margin-top:16px;}
  .hl{font-weight:700;color:var(--red);} .hlg{font-weight:700;color:var(--green);} .hlb{font-weight:700;color:var(--blue);}
  .tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
  .tag.v{background:#e8eef6;color:var(--blue);} .tag.ma{background:#fdf1e7;color:#c05c0b;}
  .tag.kbwb{background:#eef6ef;color:#1a9e4b;} .tag.tech{background:#f3eefb;color:#7048e8;}
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <h1>银行卡网络 vs 银行板块 / 科技板块 —— V / MA 相关性拆解</h1>
    <div class="meta">Visa (V) · Mastercard (MA) × Invesco KBW Bank ETF (KBWB) × QQQ / XLK（科技）· 分析窗口 @@START@@ ~ @@END@@（数据源：Yahoo Finance 日线复权收盘）</div>
    @@KPIS_1@@
    @@VERDICT_1@@
  </div>

  <div class="card">
    <h2>① 任务①：V/MA × KBWB 分阶段相关性（Pearson / Spearman / β / 同向占比）</h2>
    <div class="scroll">
    <table>
      <tr><th>区间</th><th>样本 n</th><th>Pearson</th><th>Spearman</th><th>β (V/MA~KBWB)</th><th>R²</th><th>同向占比</th><th>KBWB 涨日 V/MA 日均</th><th>KBWB 跌日 V/MA 日均</th></tr>
      @@BLOCKS_V_KBWB@@
    </table>
    </div>
    <div class="note">分界点 @@SPLIT@@ 前后：V×KBWB Fisher z = @@Z_VK@@（p = @@P_VK@@，<b>@@SIG_VK@@</b>）；MA×KBWB z = @@Z_MK@@（p = @@P_MK@@，<b>@@SIG_MK@@</b>）。分界后相关不足 0.3，2026 年银行板块不再驱动银行卡个股。</div>
  </div>

  <div class="card">
    <h2>② 任务①：滚动 60 日相关曲线（V/MA × KBWB，主口径）</h2>
    <div class="chart" id="ch_roll_kbwb"></div>
    <div class="note">全期均值 ~0.46/0.48；<b>2026-08 最新 0.13 / 0.10，处于历史区间底部</b>（历史区间下沿曾达 −0.2~−0.3，2020-03 疫情期冲高 ~0.94）。2024 年后持续下行，2026 年确认脱钩。</div>
  </div>

  <div class="card">
    <h2>③ 任务①：2026 年以来走势（归一化 = 1，同期对照）</h2>
    <div class="chart sm" id="ch_2026_kbwb"></div>
    <div class="note">2026 YTD：KBWB <span class="hl">＋@@Y26_KBWB@@%</span> vs V <span class="hl">＋@@Y26_V@@%</span> / MA <span class="hl">＋@@Y26_MA@@%</span>。银行板块由利率叙事驱动走强，V/MA 反而跑输——同步性被打破的直接证据。</div>
  </div>

  <div class="card">
    <h2>④ 任务②：V/MA × QQQ / XLK 分阶段相关性</h2>
    <div class="scroll">
    <table>
      <tr><th>区间</th><th>样本 n</th><th>Pearson</th><th>Spearman</th><th>β</th><th>R²</th><th>同向占比</th><th>板块涨日 V/MA 日均</th><th>板块跌日 V/MA 日均</th></tr>
      <tr><td colspan="9" style="background:#f3f5f8;font-weight:600;">V × QQQ</td></tr>
      @@BLOCKS_V_QQQ@@
      <tr><td colspan="9" style="background:#f3f5f8;font-weight:600;">V × XLK</td></tr>
      @@BLOCKS_V_XLK@@
      <tr><td colspan="9" style="background:#f3f5f8;font-weight:600;">MA × QQQ</td></tr>
      @@BLOCKS_MA_QQQ@@
      <tr><td colspan="9" style="background:#f3f5f8;font-weight:600;">MA × XLK</td></tr>
      @@BLOCKS_MA_XLK@@
    </table>
    </div>
    <div class="note">Fisher z（分界前后）：V×QQQ @@Z_VQ@@（p=@@P_VQ@@）、V×XLK @@Z_VX@@（p=@@P_VX@@）、MA×QQQ @@Z_MQ@@（p=@@P_MQ@@）、MA×XLK @@Z_MX@@（p=@@P_MX@@）——四组全部<b>强显著</b>。分界后相关清零、甚至转负。</div>
  </div>

  <div class="card">
    <h2>⑤ 任务②：滚动 60 日相关曲线（V/MA × 科技，双线对照）</h2>
    <div class="chart" id="ch_roll_tech"></div>
    <div class="note"><span class="tag v">V×QQQ 实线</span> <span class="tag ma">MA×QQQ 虚线</span> <span class="tag tech">V×XLK 点线</span>。历史均值 0.58~0.60，2026-07/08 全线跌入 <b>−0.3 ~ −0.5</b> 历史极端负区间。</div>
  </div>

  <div class="card">
    <h2>⑥ 任务②：2026 年以来走势（归一化 = 1，V/MA vs QQQ/XLK）</h2>
    <div class="chart sm" id="ch_2026_tech"></div>
    <div class="note">2026 YTD：XLK <span class="hl">＋@@Y26_XLK@@%</span> / QQQ <span class="hl">＋@@Y26_QQQ@@%</span> vs V <span class="hl">＋@@Y26_V@@%</span> / MA <span class="hl">＋@@Y26_MA@@%</span>。近 1 年（2025-08 起）XLK <span class="hl">＋42.3%</span> vs MA <span class="hl">−1.3%</span>，分化扩大到极端水平。</div>
  </div>

  <div class="card">
    <h2>⑦ 近 3 年日收益散点（V/MA × KBWB，分界前/后分色）</h2>
    <div class="chart" id="ch_scatter_kbwb"></div>
    <div class="note">分界前（蓝点）沿正向带分布；分界后（紫◆）明显散开、斜率趋平——2026 年同向联动显著减弱。</div>
  </div>

  <div class="card">
    <h2>⑧ 近 3 年日收益散点（V/MA × QQQ/XLK，分界前/后分色）</h2>
    <div class="chart" id="ch_scatter_tech"></div>
    <div class="note">V×QQQ 与 MA×XLK 双散点。分界后（深色点）呈「十字交叉」形态：银行卡与科技日收益几乎不再共动。</div>
  </div>

  <div class="card">
    <h2>⑨ 年度收益对比（V/MA vs KBWB，%）</h2>
    <div class="chart" id="ch_year_kbwb"></div>
    <div class="note">红 = 正收益，绿 = 负收益，KPI 上方标数值。银行卡在 2020/2021 疫后消费复苏大幅跑赢银行；2022 双双回调；<b>2026 年银行板块反超银行卡</b>（KBWB +12.8% vs V +7.7% / MA +3.6%）。</div>
  </div>

  <div class="card">
    <h2>⑩ 年度收益对比（V/MA vs 科技，%）</h2>
    <div class="chart" id="ch_year_tech"></div>
    <div class="note">科技（QQQ/XLK）与银行卡 2019 前大体同步；2023 起 AI 驱动科技持续跑赢；<b>2026 年分化达到历史极值</b>（XLK +27.3% vs MA +3.6%）。</div>
  </div>

  <div class="card">
    <h2>⑪ 相对强弱：银行卡 vs 银行 / 科技（归一化比值）</h2>
    @@RATIO_TABLE@@
    <div class="chart sm" id="ch_ratio_all"></div>
    <div class="note"><span class="tag kbwb">KBWB/V 实线</span> <span class="tag ma">KBWB/MA 虚线</span> <span class="tag tech">QQQ/V 点线</span> <span class="tag v">XLK/MA 双点线</span>。全部相对银行卡走强方向抬升，其中科技最为极端。</div>
  </div>

  <div class="card">
    <h2>⑫ 价格表现与风险对比（V/MA vs KBWB）</h2>
    <div class="scroll">
    <table>
      <tr><th>区间</th><th>累计收益 V/MA / KBWB</th><th>最大回撤 V/MA / KBWB</th><th>年化波动 V/MA / KBWB</th><th>夏普 V/MA / KBWB</th></tr>
      @@PRICE_V_KBWB@@
    </table>
    </div>
  </div>

  <div class="card">
    <h2>⑬ 价格表现与风险对比（V/MA vs QQQ/XLK）</h2>
    <div class="scroll">
    <table>
      <tr><th>区间</th><th>累计收益 V/MA / QQQ</th><th>最大回撤 V/MA / QQQ</th><th>年化波动 V/MA / QQQ</th><th>夏普 V/MA / QQQ</th></tr>
      @@PRICE_V_QQQ@@
    </table>
    </div>
  </div>

  <div class="card">
    <h2>⑭ 任务①：月频相关性（V/MA × KBWB）</h2>
    <div class="chart sm" id="ch_monthly_kbwb"></div>
    <div class="note">月频口径同样验证脱钩：全期均值 ~0.44/0.46，近 36 月降至 0.36/0.35，<b>2026-08 最新 −0.03 / −0.08</b>。</div>
  </div>

  <div class="card">
    <h2>⑮ 方法口径与局限</h2>
    <ul>
      <li><b>数据</b>：Yahoo Finance 日线复权收盘价（adj_close）；KBWB 2011-11 上市，V/MA 起于 2008-03/2006-05；统一窗口 @@START@@ ~ @@END@@（n=@@N@@），KBWB 对为 2011-11 起。</li>
      <li><b>相关口径</b>：日收益率 Pearson / Spearman；滚动 60 日为主口径（项目长期规则），月频辅助；β 为 V/MA 对板块/科技的 OLS 斜率。</li>
      <li><b>分阶段</b>：以 @@SPLIT@@ 为结构分界点（沿用项目既有口径），Fisher z 检验分界前后差异。</li>
      <li><b>局限</b>：① V/MA 与 KBWB/QQQ/XLK 并非同质资产，都是「个股 vs 板块」对比；② 分界后样本仅 ~140 日，相关估计的标准误较大（单点 ±0.08 量级），结论偏谨慎；③ KBWB 为等权银行 ETF，QQQ/XLK 权重集中（英伟达等），板块内部结构会影响相关；④ 未控宏观因子（利率/美元/VIX），相关性非因果。</li>
      <li><b>核心结论的稳健性</b>：脱钩并非单点噪音——60 日滚动、月频、Pearson、Spearman、同向占比 5 个口径一致向下，且多组同时成立，可信度较高。</li>
    </ul>
  </div>

  <div class="card dis">
    <div style="font-weight:600;margin-bottom:6px;">免责声明</div>
    本报告仅为数据分析参考，不构成任何投资建议。历史相关性不代表未来表现，文中所有统计基于历史数据，存在样本区间依赖。
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
var RED = "#d23b2e", GREEN = "#1a9e4b", ORANGE = "#e67e22", BLUE = "#1f4e79", GRAY = "#999", PURPLE = "#7048e8";
var CB = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#CC79A7", verm:"#D55E00", black:"#000000", green:"#009E73"};

function lineBase(id, legend, ymin, ymax, yname){
  return {
    tooltip:{ trigger:"axis", valueFormatter:function(v){ return (v==null?"-":v.toFixed(3)); } },
    legend:{ data:legend, top:0 },
    grid:{ left:60, right:30, top:40, bottom:45 },
    xAxis:{ type:"category", axisLabel:{ fontSize:10, interval:"auto" } },
    yAxis:{ type:"value", name:yname||"", scale:false,
      min:ymin, max:ymax,
      axisLabel:{ formatter:function(v){ return (v==null?"":v.toFixed(2)); } } },
    dataZoom:[{ type:"inside", start:0, end:100 }]
  };
}

// ② 滚动60日 KBWB 对
(function(){
  var ch = echarts.init(document.getElementById("ch_roll_kbwb"));
  var dV = DATA.pairs.V.rolling60.filter(function(x){return x.corr!=null;});
  var dM = DATA.pairs.MA.rolling60.filter(function(x){return x.corr!=null;});
  var opt = lineBase("ch_roll_kbwb", ["V × KBWB (实线)","MA × KBWB (虚线)"], -0.5, 1.0);
  opt.xAxis.data = dV.map(function(x){return x.date;});
  opt.series = [
    { name:"V × KBWB (实线)", type:"line", data:dV.map(function(x){return x.corr;}), showSymbol:false,
      lineStyle:{ color:CB.blue, width:1.6 }, itemStyle:{ color:CB.blue },
      markLine:{ silent:true, symbol:"none",
        data:[ { yAxis:0, lineStyle:{color:GRAY,type:"dashed"}, label:{formatter:"0",fontSize:9,color:GRAY} } ] } },
    { name:"MA × KBWB (虚线)", type:"line", data:dM.map(function(x){return x.corr;}), showSymbol:false,
      lineStyle:{ color:CB.orange, width:1.6, type:"dashed" }, itemStyle:{ color:CB.orange } }
  ];
  ch.setOption(opt);
})();

// ③ 2026 KBWB 对
(function(){
  var ch = echarts.init(document.getElementById("ch_2026_kbwb"));
  var dV = DATA.pairs.V.series_2026;
  var dM = DATA.pairs.MA.series_2026;
  var opt = lineBase("ch_2026_kbwb", ["KBWB","V","MA"], null, null, "归一化(2026-01=1)");
  opt.xAxis.data = dV.map(function(x){return x.date;});
  opt.series = [
    { name:"KBWB", type:"line", data:dV.map(function(x){return x.y;}), symbol:"circle", symbolSize:3,
      lineStyle:{ color:CB.green, width:2 } },
    { name:"V", type:"line", data:dV.map(function(x){return x.x;}), symbol:"diamond", symbolSize:3,
      lineStyle:{ color:CB.blue, width:2, type:"dashed" } },
    { name:"MA", type:"line", data:dM.map(function(x){return x.x;}), symbol:"triangle", symbolSize:3,
      lineStyle:{ color:CB.orange, width:2, type:"dotted" } }
  ];
  ch.setOption(opt);
})();

// ⑤ 滚动60日 科技对
(function(){
  var ch = echarts.init(document.getElementById("ch_roll_tech"));
  function dd(key){ return DATA.pairs[key].rolling60.filter(function(x){return x.corr!=null;}); }
  var dVQ = dd("V_vs_QQQ"), dMQ = dd("MA_vs_QQQ"), dVX = dd("V_vs_XLK");
  var opt = lineBase("ch_roll_tech", ["V×QQQ (实线)","MA×QQQ (虚线)","V×XLK (点线)"], -0.6, 1.0);
  opt.xAxis.data = dVQ.map(function(x){return x.date;});
  opt.series = [
    { name:"V×QQQ (实线)", type:"line", data:dVQ.map(function(x){return x.corr;}), showSymbol:false,
      lineStyle:{ color:CB.sky, width:1.6 }, itemStyle:{ color:CB.sky },
      markLine:{ silent:true, symbol:"none",
        data:[ { yAxis:0, lineStyle:{color:GRAY,type:"dashed"}, label:{formatter:"0",fontSize:9,color:GRAY} } ] } },
    { name:"MA×QQQ (虚线)", type:"line", data:dMQ.map(function(x){return x.corr;}), showSymbol:false,
      lineStyle:{ color:CB.verm, width:1.6, type:"dashed" }, itemStyle:{ color:CB.verm } },
    { name:"V×XLK (点线)", type:"line", data:dVX.map(function(x){return x.corr;}), showSymbol:false,
      lineStyle:{ color:CB.purple, width:1.6, type:"dotted" }, itemStyle:{ color:CB.purple } }
  ];
  ch.setOption(opt);
})();

// ⑥ 2026 科技对
(function(){
  var ch = echarts.init(document.getElementById("ch_2026_tech"));
  var dVQ = DATA.pairs.V_vs_QQQ.series_2026;
  var dVX = DATA.pairs.V_vs_XLK.series_2026;
  var dMX = DATA.pairs.MA_vs_XLK.series_2026;
  var opt = lineBase("ch_2026_tech", ["QQQ","XLK","V","MA"], null, null, "归一化(2026-01=1)");
  opt.xAxis.data = dVQ.map(function(x){return x.date;});
  opt.series = [
    { name:"QQQ", type:"line", data:dVQ.map(function(x){return x.y;}), symbol:"circle", symbolSize:3,
      lineStyle:{ color:CB.sky, width:2 } },
    { name:"XLK", type:"line", data:dVX.map(function(x){return x.y;}), symbol:"circle", symbolSize:3,
      lineStyle:{ color:CB.purple, width:2, type:"dashed" } },
    { name:"V", type:"line", data:dVQ.map(function(x){return x.x;}), symbol:"diamond", symbolSize:3,
      lineStyle:{ color:CB.blue, width:2, type:"dotted" } },
    { name:"MA", type:"line", data:dMX.map(function(x){return x.x;}), symbol:"triangle", symbolSize:3,
      lineStyle:{ color:CB.orange, width:2, type:"dot" } }
  ];
  ch.setOption(opt);
})();

// ⑦ 散点 KBWB 对
(function(){
  var ch = echarts.init(document.getElementById("ch_scatter_kbwb"));
  var dV = DATA.pairs.V.scatter;
  var opt = {
    tooltip:{ trigger:"item", formatter:function(p){
        return p.data[3] + "<br>" + p.seriesName + "<br>V " + p.data[0].toFixed(2) + "%　KBWB " + p.data[1].toFixed(2) + "%";
      } },
    legend:{ data:["分界前 (2011-2026-01)","分界后 (2026-02 起)"], top:0 },
    grid:{ left:60, right:40, top:40, bottom:45 },
    xAxis:{ type:"value", name:"V 日收益 %", scale:true, axisLabel:{formatter:function(v){return v+"%";}} },
    yAxis:{ type:"value", name:"KBWB 日收益 %", scale:true, axisLabel:{formatter:function(v){return v+"%";}} },
    series:[
      { name:"分界前 (2011-2026-01)", type:"scatter",
        data:dV.filter(function(x){return !x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:3.5, itemStyle:{ color:"rgba(0,114,178,0.35)" } },
      { name:"分界后 (2026-02 起)", type:"scatter",
        data:dV.filter(function(x){return x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:7, symbol:"diamond", itemStyle:{ color:"rgba(204,121,167,0.85)" } }
    ]
  };
  ch.setOption(opt);
})();

// ⑧ 散点 科技对（V×QQQ，MA×XLK 分色）
(function(){
  var ch = echarts.init(document.getElementById("ch_scatter_tech"));
  var dVQ = DATA.pairs.V_vs_QQQ.scatter;
  var dMX = DATA.pairs.MA_vs_XLK.scatter;
  var opt = {
    tooltip:{ trigger:"item", formatter:function(p){
        var nm = p.seriesName.indexOf("V×QQQ")>=0 ? "V" : "MA";
        var ym = p.seriesName.indexOf("V×QQQ")>=0 ? "QQQ" : "XLK";
        return p.data[3] + "<br>" + p.seriesName + "<br>" + nm + " " + p.data[0].toFixed(2) + "%　" + ym + " " + p.data[1].toFixed(2) + "%";
      } },
    legend:{ data:["V×QQQ 分界前","V×QQQ 分界后","MA×XLK 分界前","MA×XLK 分界后"], top:0 },
    grid:{ left:60, right:40, top:40, bottom:45 },
    xAxis:{ type:"value", name:"V/MA 日收益 %", scale:true, axisLabel:{formatter:function(v){return v+"%";}} },
    yAxis:{ type:"value", name:"QQQ/XLK 日收益 %", scale:true, axisLabel:{formatter:function(v){return v+"%";}} },
    series:[
      { name:"V×QQQ 分界前", type:"scatter",
        data:dVQ.filter(function(x){return !x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:3.5, itemStyle:{ color:"rgba(86,180,233,0.4)" } },
      { name:"V×QQQ 分界后", type:"scatter",
        data:dVQ.filter(function(x){return x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:7, symbol:"diamond", itemStyle:{ color:"rgba(0,114,178,0.85)" } },
      { name:"MA×XLK 分界前", type:"scatter",
        data:dMX.filter(function(x){return !x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:3.5, symbol:"triangle", itemStyle:{ color:"rgba(230,159,0,0.4)" } },
      { name:"MA×XLK 分界后", type:"scatter",
        data:dMX.filter(function(x){return x.after;}).map(function(x){return [x.x, x.y, x.date]; }),
        symbolSize:7, symbol:"triangle", itemStyle:{ color:"rgba(213,94,0,0.85)" } }
    ]
  };
  ch.setOption(opt);
})();

// ⑨ 年度 KBWB 对
(function(){
  var ch = echarts.init(document.getElementById("ch_year_kbwb"));
  var dV = DATA.pairs.V, dM = DATA.pairs.MA;
  var ys = dV.years;
  var opt = {
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"}, valueFormatter:function(v){ return (v==null?"-":v.toFixed(1)+"%"); } },
    legend:{ data:["KBWB","V","MA"], top:0 },
    grid:{ left:60, right:20, top:40, bottom:30 },
    xAxis:{ type:"category", data:ys.map(function(y){return String(y);}) },
    yAxis:{ type:"value", name:"%", axisLabel:{ formatter:function(v){return v+"%";} } },
    series:[
      { name:"KBWB", type:"bar", data:ys.map(function(y){return dV.yearly[y].y;}), barGap:"5%",
        itemStyle:{ color:function(p){ return p.value>=0 ? "#71c49a" : "#a8d5bc"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } },
      { name:"V", type:"bar", data:ys.map(function(y){return dV.yearly[y].x;}),
        itemStyle:{ color:function(p){ return p.value>=0 ? CB.blue : "#8fb5d9"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } },
      { name:"MA", type:"bar", data:ys.map(function(y){return dM.yearly[y].x;}),
        itemStyle:{ color:function(p){ return p.value>=0 ? CB.orange : "#e0b877"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } }
    ]
  };
  ch.setOption(opt);
})();

// ⑩ 年度 科技对
(function(){
  var ch = echarts.init(document.getElementById("ch_year_tech"));
  var dVQ = DATA.pairs.V_vs_QQQ, dMX = DATA.pairs.MA_vs_XLK;
  var ys = dVQ.years;
  var opt = {
    tooltip:{ trigger:"axis", axisPointer:{type:"shadow"}, valueFormatter:function(v){ return (v==null?"-":v.toFixed(1)+"%"); } },
    legend:{ data:["QQQ","XLK","V","MA"], top:0 },
    grid:{ left:60, right:20, top:40, bottom:30 },
    xAxis:{ type:"category", data:ys.map(function(y){return String(y);}) },
    yAxis:{ type:"value", name:"%", axisLabel:{ formatter:function(v){return v+"%";} } },
    series:[
      { name:"QQQ", type:"bar", data:ys.map(function(y){return dVQ.yearly[y].y;}), barGap:"5%",
        itemStyle:{ color:function(p){ return p.value>=0 ? "#89c2e0" : "#b8d9ea"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } },
      { name:"XLK", type:"bar", data:ys.map(function(y){return dMX.yearly[y].y;}),
        itemStyle:{ color:function(p){ return p.value>=0 ? CB.purple : "#c9b8E8"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } },
      { name:"V", type:"bar", data:ys.map(function(y){return dVQ.yearly[y].x;}),
        itemStyle:{ color:function(p){ return p.value>=0 ? CB.blue : "#8fb5d9"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } },
      { name:"MA", type:"bar", data:ys.map(function(y){return dMX.yearly[y].x;}),
        itemStyle:{ color:function(p){ return p.value>=0 ? CB.orange : "#e0b877"; } },
        label:{ show:true, position:"top", formatter:function(p){ return p.value.toFixed(0); }, fontSize:9 } }
    ]
  };
  ch.setOption(opt);
})();

// ⑪ 相对强弱
(function(){
  var ch = echarts.init(document.getElementById("ch_ratio_all"));
  function dd(key){ return DATA.pairs[key].full_series; }
  var fv = dd("V"), fma = dd("MA"), fvq = dd("V_vs_QQQ"), fmx = dd("MA_vs_XLK");
  var dates = fv.map(function(x){return x.date;});
  function ratio(ser){ return ser.map(function(x){ return x.y / x.x; }); }
  var opt = lineBase("ch_ratio_all", ["KBWB/V (实线)","KBWB/MA (虚线)","QQQ/V (点线)","XLK/MA (双点线)"], null, null, "板块/科技 ÷ 银行卡 (归一)");
  opt.xAxis.data = dates;
  opt.series = [
    { name:"KBWB/V (实线)", type:"line", data:ratio(fv), showSymbol:false, lineStyle:{ color:CB.green, width:1.5 }, itemStyle:{ color:CB.green } },
    { name:"KBWB/MA (虚线)", type:"line", data:ratio(fma), showSymbol:false, lineStyle:{ color:CB.orange, width:1.5, type:"dashed" }, itemStyle:{ color:CB.orange } },
    { name:"QQQ/V (点线)", type:"line", data:ratio(fvq), showSymbol:false, lineStyle:{ color:CB.sky, width:1.5, type:"dotted" }, itemStyle:{ color:CB.sky } },
    { name:"XLK/MA (双点线)", type:"line", data:ratio(fmx), showSymbol:false, lineStyle:{ color:CB.purple, width:1.5, type:"dashed", dashOffset:2 }, itemStyle:{ color:CB.purple } }
  ];
  ch.setOption(opt);
})();

// ⑭ 月频 KBWB 对
(function(){
  var ch = echarts.init(document.getElementById("ch_monthly_kbwb"));
  var dV = DATA.pairs.V.monthly, dM = DATA.pairs.MA.monthly;
  var opt = lineBase("ch_monthly_kbwb", ["V×KBWB (实线)","MA×KBWB (虚线)"], -0.9, 1.0);
  opt.xAxis.data = dV.map(function(x){return x.month;});
  opt.series = [
    { name:"V×KBWB (实线)", type:"line", data:dV.map(function(x){return x.corr;}), showSymbol:false, lineStyle:{ color:CB.blue, width:1.4 }, itemStyle:{ color:CB.blue } },
    { name:"MA×KBWB (虚线)", type:"line", data:dM.map(function(x){return x.corr;}), showSymbol:false, lineStyle:{ color:CB.orange, width:1.4, type:"dashed" }, itemStyle:{ color:CB.orange } }
  ];
  ch.setOption(opt);
})();
</script>
</body>
</html>
"""

# ---------- KPI 卡片 ----------
kpis_1 = f"""
    <div class="kpis">
      <div class="kpi"><div class="num">{P['V']['blocks'][0]['pearson']:.2f}</div><div class="lab">V × KBWB 全期 Pearson</div></div>
      <div class="kpi"><div class="num">{P['MA']['blocks'][0]['pearson']:.2f}</div><div class="lab">MA × KBWB 全期 Pearson</div></div>
      <div class="kpi"><div class="num">{P['V']['blocks'][1]['pearson']:.2f} → {P['V']['blocks'][2]['pearson']:.2f}</div><div class="lab">V×KBWB 分界前 → 后</div></div>
      <div class="kpi"><div class="num">{P['V']['latest_roll']:.2f}</div><div class="lab">V×KBWB 60日滚动最新</div></div>
      <div class="kpi"><div class="num">{P['V_vs_QQQ']['blocks'][1]['pearson']:.2f} → {P['V_vs_QQQ']['blocks'][2]['pearson']:.2f}</div><div class="lab">V×QQQ 分界前 → 后</div></div>
      <div class="kpi"><div class="num">{P['V_vs_XLK']['latest_roll']:.2f}</div><div class="lab">V×XLK 60日滚动最新</div></div>
    </div>"""

# 任务① / ② 分块相关表格
blocks_v_kbwb = blocks_rows(P["V"], "V", "KBWB")
blocks_ma_kbwb = blocks_rows(P["MA"], "MA", "KBWB")
blocks_v_qqq = blocks_rows(P["V_vs_QQQ"], "V", "QQQ")
blocks_v_xlk = blocks_rows(P["V_vs_XLK"], "V", "XLK")
blocks_ma_qqq = blocks_rows(P["MA_vs_QQQ"], "MA", "QQQ")
blocks_ma_xlk = blocks_rows(P["MA_vs_XLK"], "MA", "XLK")

price_v_kbwb = price_rows(P["V"])
price_ma_kbwb = price_rows(P["MA"])
price_v_qqq = price_rows(P["V_vs_QQQ"])
price_ma_xlk = price_rows(P["MA_vs_XLK"])

# ---------- 替换 ----------
repl = {
    "@@START@@": D["pairs"]["V"]["period"]["start"],
    "@@END@@": D["pairs"]["V"]["period"]["end"],
    "@@N@@": f'{D["pairs"]["V"]["period"]["n"]:,}',
    "@@KPIS_1@@": kpis_1,
    "@@VERDICT_1@@": verdict_1,
    "@@SPLIT@@": SPLIT,
    "@@BLOCKS_V_KBWB@@": blocks_v_kbwb,
    "@@BLOCKS_MA_KBWB@@": blocks_ma_kbwb,
    "@@BLOCKS_V_QQQ@@": blocks_v_qqq,
    "@@BLOCKS_V_XLK@@": blocks_v_xlk,
    "@@BLOCKS_MA_QQQ@@": blocks_ma_qqq,
    "@@BLOCKS_MA_XLK@@": blocks_ma_xlk,
    "@@PRICE_V_KBWB@@": price_v_kbwb,
    "@@PRICE_MA_KBWB@@": price_ma_kbwb,
    "@@PRICE_V_QQQ@@": price_v_qqq,
    "@@PRICE_MA_XLK@@": price_ma_xlk,
    "@@Z_VK@@": str(P["V"]["fisher"]["z"]), "@@P_VK@@": str(P["V"]["fisher"]["p_value"]),
    "@@SIG_VK@@": "显著" if P["V"]["fisher"]["sig"] else "不显著",
    "@@Z_MK@@": str(P["MA"]["fisher"]["z"]), "@@P_MK@@": str(P["MA"]["fisher"]["p_value"]),
    "@@SIG_MK@@": "显著" if P["MA"]["fisher"]["sig"] else "不显著",
    "@@Z_VQ@@": str(P["V_vs_QQQ"]["fisher"]["z"]), "@@P_VQ@@": str(P["V_vs_QQQ"]["fisher"]["p_value"]),
    "@@Z_VX@@": str(P["V_vs_XLK"]["fisher"]["z"]), "@@P_VX@@": str(P["V_vs_XLK"]["fisher"]["p_value"]),
    "@@Z_MQ@@": str(P["MA_vs_QQQ"]["fisher"]["z"]), "@@P_MQ@@": str(P["MA_vs_QQQ"]["fisher"]["p_value"]),
    "@@Z_MX@@": str(P["MA_vs_XLK"]["fisher"]["z"]), "@@P_MX@@": str(P["MA_vs_XLK"]["fisher"]["p_value"]),
    "@@Y26_KBWB@@": f'{y26_v_kbwb["y"]:+.1f}',
    "@@Y26_V@@": f'{y26_v_kbwb["x"]:+.1f}',
    "@@Y26_MA@@": f'{y26_ma_kbwb["x"]:+.1f}',
    "@@Y26_QQQ@@": f'{y26_v_qqq["y"]:+.1f}',
    "@@Y26_XLK@@": f'{y26_ma_xlk["y"]:+.1f}',
    "@@RATIO_TABLE@@": ratio_blocks,
}
html = html.replace("<!-- RATIO_PLACEHOLDER -->", "")
for k, v in repl.items():
    html = html.replace(k, v)
html = html.replace("var DATA = __DATA_JSON__;", "var DATA = " + js(D) + ";")

out_path = os.path.join(OUT_DIR, "visa_master_corr_report.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written: {out_path} size={os.path.getsize(out_path)}")