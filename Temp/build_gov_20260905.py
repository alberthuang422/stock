# -*- coding: utf-8 -*-
"""报告治理盘点与合并方案生成器 2026-09-05
扫描 reports/ 编号目录与散件 -> 内嵌人工标注 -> 输出 reports/00_报告治理_20260905/index.html
"""
import os, re, html, json, datetime

ROOT = r"C:\Users\Administrator\Desktop\stock"
REP = os.path.join(ROOT, "reports")
OUTDIR = os.path.join(REP, "00_报告治理_20260905")
OUT = os.path.join(OUTDIR, "index.html")

def read_title(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(8000)
        m = re.search(r"<title>([^<]{0,130})", head, re.S)
        if m:
            t = re.sub(r"\s+", " ", m.group(1)).strip()
            return t
    except Exception:
        pass
    return ""

def scan_units():
    """单元=顶层编号目录(跳过00_)或顶层html; 编号目录内有 index.html 视目录为主"""
    units = []
    for name in sorted(os.listdir(REP)):
        p = os.path.join(REP, name)
        if os.path.isdir(p):
            if not name.startswith("00_") and any(f.endswith(".html") for f in os.listdir(p)):
                idx = os.path.join(p, "index.html")
                if os.path.exists(idx):
                    units.append({"key": name, "dir": True, "entry": "index.html",
                                  "files": [f for f in os.listdir(p) if f.endswith(".html")],
                                  "title": read_title(idx)})
                else:
                    hs = sorted([f for f in os.listdir(p) if f.endswith(".html")])
                    units.append({"key": name, "dir": True, "entry": hs[0] if hs else "",
                                  "files": hs,
                                  "title": read_title(os.path.join(p, hs[0])) if hs else ""})
        else:
            if name.endswith(".html"):
                units.append({"key": name, "dir": False, "entry": name,
                              "files": [name], "title": read_title(p)})
    return units

# ---------------- 人工标注 ----------------
# fam: q_tm/q_rsi/c_ph/c_cons/c_bank/c_tech/c_pwr/c_fin/macro/fund/sec/ag/mkt/ops
# stat: active/series/absorb/superse/redund/ops/snap
# act: keep/grp/arch/merge/clean
SEC = {
 "S1": ("量化回测 · 技术形态 / RSI 低吸信号", ["q_tm","q_rsi"]),
 "S2": ("相关性 · 医药与工具链", ["c_ph"]),
 "S3": ("相关性/基本面 · 消费与金融科技", ["c_cons","c_fin"]),
 "S4": ("相关性 · 银行/资管/电力/科技等跨板块", ["c_bank","c_tech","c_pwr"]),
 "S5": ("个股基本面深度研究", ["fund"]),
 "S6": ("行业景气 / 资金流 / 专利悬崖", ["sec"]),
 "S7": ("宏观利率背景与板块联动", ["macro"]),
 "S8": ("市场结构 / 情绪 / 事件研究", ["mkt"]),
 "S9": ("农业大宗（CFTC/ENSO/库存/回测）", ["ag"]),
 "S10": ("流水线产物 / 操作快照 / 非报告资产", ["ops","snap"]),
}
FAM = {"q_tm":"量化·形态", "q_rsi":"量化·RSI低吸", "c_ph":"相关·医药工具", "c_cons":"相关·消费",
       "c_bank":"相关·银行资管", "c_tech":"相关·科技网络", "c_pwr":"相关·电力IPP", "c_fin":"相关·金融科技",
       "macro":"宏观利率", "fund":"个股基本面", "sec":"景气/资金流", "ag":"农业大宗", "mkt":"情绪/结构", "ops":"流水线", "snap":"快照"}
STAT = {"active":"有效", "series":"系列成员", "absorb":"被吸收", "superse":"被替代", "redund":"冗余", "ops":"流水线", "snap":"时效快照"}
ACT = {"keep":"保留", "grp":"索引归组", "arch":"归档候选", "merge":"物理合并候选", "clean":"整理候选"}

# key -> (fam, stat, act, note)
A = {
 "01_MACD回测": ("q_tm","series","keep","11 个 html：IBKR 主报告+9 标的+横向对比。系列内部可再归组，README 已索引"),
 "02_gild_xlv_ibb相关性板块分析": ("c_ph","series","keep","8 个 html（IBB×GILD/AMGN/VRTX/top10/财报窗口/VIX 冲击）。README 已拆子条目，属 GILD 系列"),
 "03_wuxi_bigpharma药明康德vs美国药企": ("c_ph","series","keep","2 个 html：相关性+财务错配传导"),
 "04_ceg_vst电力股对比": ("c_pwr","active","keep","CEG vs VST 基本面+相关性对比"),
 "05_vst_utes阶段分析": ("c_pwr","series","keep","VST×UTES 分阶段相关（IPP 主题线成员，与 04/07 互链）"),
 "06_陡峭化消费股": ("macro","active","keep","陡峭化窗口 KO/PM/MO 历史表现（宏观×消费双视角）"),
 "07_ipp大跌归因": ("mkt","active","keep","8/18 IPP 大跌当日归因（时效事件快照，但归因方法可复用）"),
 "07_sbux星巴克": ("fund","absorb","arch","早期 SBUX 财报估值研究；2026-08-24 的 29 号已做全面基本面覆盖 → 内容重叠，建议归档或在 29 号内补链接"),
 "08_银行陡峭化": ("macro","series","keep","银行股×10Y-2Y 陡峭化；与 09 熊陡为姊妹篇（牛市陡 vs 熊市陡各一份）"),
 "09_银行熊陡": ("macro","series","keep","同上姊妹篇，两篇建议 README 合并为『银行×曲线陡峭化（牛陡/熊陡）』一行"),
 "10_涨3%事件": ("q_tm","active","keep","生物医药股单日≥3% 事件研究"),
 "11_gild突破回踩": ("q_tm","active","keep","GILD/ABBV 横盘突破 T+N（医药×量化交叉）"),
 "12_周线超买": ("q_tm","active","keep","周线 MACD 转正→4h RSI 超买→调整深度（GILD/ABBV）"),
 "13_kbwb支撑位": ("q_tm","series","clean","3 个 html 主题混杂：支撑识别 demo(MS)/下降趋势线识别/KBWB×MS 相关性。README 已拆 3 条；目录内相关性文件建议归到 KBWB 族"),
 "13_道指板块支撑": ("q_tm","active","keep","道指板块破位×龙头强支撑共振事件"),
 "14_ETF弱势支撑": ("q_tm","active","keep","ETF 弱势窗口×成分股触支撑事件"),
 "14_kbwb科技弱势": ("c_bank","series","merge","KBWB 弱势条件族成员（与 15/16 同模板不同板块：科技/医药/资管）→ 三份可物理合并为『银行走弱时的板块传导』1 份，或索引合并"),
 "15_kbwb医药弱势": ("c_bank","series","merge","同 14_kbwb科技弱势"),
 "16_kbwbAM弱势": ("c_bank","series","merge","同 14_kbwb科技弱势"),
 "17_KO超买": ("q_tm","active","keep","KO 日线 RSI 超买后 T+5/T+10"),
 "18_公用事业MACD水下金叉回测": ("q_tm","active","keep","策略板块验证（01 号的公用事业版）"),
 "19_csco_bug网络安全": ("c_tech","series","keep","CSCO 族（与 35/38 相关），同涨不同频"),
 "20_期权墙八标的": ("mkt","active","keep","2026-09-18 到期期权结构（时效：随到期失效，属事件快照）"),
 "21_生物医药行业景气度": ("sec","series","keep","大药企 16 项景气核查（与 22 姊妹篇）"),
 "22_小型生物科技景气度": ("sec","series","keep","同上小 biotech 版；21/22 建议 README 归一组"),
 "23_ihi_xbi器械vs生物科技": ("c_ph","active","keep","工具链相关性主报告（60 日口径）"),
 "24_工具龙头_ibb_xbi相关性": ("c_ph","active","keep","A/WAT/DHR/TMO×IBB/XBI（与 23/25/26 属工具链研究线）"),
 "25_工具业绩传导时滞": ("sec","active","keep","biotech 景气→工具订单收入传导"),
 "26_ihi_xbi_13日滚动相关": ("c_ph","superse","arch","13 日滚动辅助口径——项目口径铁律已定 60 日为主（13 日被实证否定，见 2026-08-23 设定），README 已标注辅助；建议并入 23 号作附录或归档"),
 "26_千亿美元药企专利悬崖": ("sec","active","keep","15 巨头专利悬崖与管线接力"),
 "27_nvs诺华深度研究": ("fund","active","keep","NVS 全面研究"),
 "27_银行卡网络_银行科技相关性": ("c_bank","active","keep","V/MA×银行/科技（编号与 27_nvs 冲突，历史遗留）"),
 "28_abbv艾伯维深度研究": ("fund","active","keep","ABBV 全面研究"),
 "28_ko_vs_pep_相对强弱研究.html": ("fund","active","keep","KO 基本面+KO/PEP 强弱（顶层散件，无编号目录；编号 28 已用于 abbv → 命名冲突）"),
 "29_sbux基本面分析": ("fund","active","keep","SBUX 2026-08 全面基本面（已覆盖 07_sbux 早期版）"),
 "30_资管陡峭化": ("macro","active","keep","APO/BX/KKR×利差（资管×宏观）"),
 "31_蓝筹区间下沿支撑_周线EMA20压制回测": ("q_tm","active","keep","周线 EMA20 压制下支撑触达（蓝筹）"),
 "32_ko_科技医药相关性": ("c_cons","active","keep","KO×科技/制药/医疗相关"),
 "33_周线MACD收敛支撑位回测": ("q_tm","active","keep","MACD 柱状态×支撑位"),
 "34_道指板块超买横向": ("q_tm","active","keep","道指 9 板块代表股 RSI 超买横向"),
 "35_网安vs网络设备": ("c_tech","active","keep","CSCO×PANW/CRWD（README 死链：31_网安vs网络设备 实际指向此目录，需修正）"),
 "36_高位死叉回踩EMA20支撑": ("q_tm","active","keep","0 轴上方死叉×回踩 EMA20"),
 "37_ko_xlv_dji相关性": ("c_cons","active","keep","KO/XLV×道指"),
 "37_中期选举波动率": ("mkt","series","merge","选举族 1/3：SP500 波动放大（与 38_板块、42_VIX 同批研究 → 三份可物理合并『中期选举窗口波动率合集』或索引归一行）"),
 "38_思科纳指道指相关性": ("c_tech","active","keep","CSCO×纳指/道指"),
 "38_板块中期选举波动率": ("mkt","series","merge","选举族 2/3（同上）"),
 "39_蓝筹RSI超卖买入": ("q_rsi","series","keep","蓝筹 RSI 族 1/3（超卖<30 / 动态支撑 / swing low，40/41 同批）"),
 "40_蓝筹RSI支撑位买入": ("q_rsi","series","keep","蓝筹 RSI 族 2/3"),
 "41_蓝筹RSI摆动低点支撑买入": ("q_rsi","series","keep","蓝筹 RSI 族 3/3；39/40/41 建议 README 归『蓝筹 RSI 低吸系列』一行"),
 "42_VIX中期选举抬升": ("mkt","series","merge","选举族 3/3（同上 37/38）"),
 "43_ABBV_IBB_IHE_相关性": ("c_ph","active","keep","ABBV×IBB/IHE"),
 "44_贴EMA20缩量跌破平台": ("q_tm","active","keep","蓝筹跌破平台事件"),
 "45_震荡市板块独立行情": ("q_tm","active","keep","震荡市板块独立趋势统计（与 70 系列语境同源）"),
 "46_MCD_RSI摆动低点支撑买入": ("q_rsi","series","merge","MCD RSI 四连 1/4；46-49 为同标的同信号族迭代产物（46 摆动低点 / 47 分档 / 48 窗口质量 / 49 区间跌落），建议物理合并为『MCD RSI 低吸方法族』1 份 + 附录，或索引归一行"),
 "47_MCD_RSI低位分档买入": ("q_rsi","series","merge","MCD RSI 四连 2/4（同上）"),
 "48_MCD_RSI低位窗口质量": ("q_rsi","series","merge","MCD RSI 四连 3/4（同上）"),
 "49_MCD_RSI区间跌落买入": ("q_rsi","series","merge","MCD RSI 四连 4/4（同上）"),
 "50_SOFI_BTC_相关性季度分阶段": ("c_fin","active","keep","SOFI/XYZ×BTC（SOFI 族成员）"),
 "50_纳指区间RSI低买高卖": ("q_rsi","active","keep","纳指横盘 RSI 配对回测（编号与 50_SOFI 冲突）"),
 "51_MCD_SBUX_DJI_XLY_相关性": ("c_cons","active","keep","消费×指数 2×2"),
 "52_持仓组合技术面与操作建议": ("snap","active","keep","8 标的持仓逐股技术面（个性化时效快照，非可复用方法）"),
 "53_金融科技财报日相关性": ("c_fin","active","keep","SOFI/AFRM/UPST 财报日事件（SOFI 族）"),
 "54_宏观利率背景六股影响": ("macro","active","keep","利差扩张→熊平切换×六股（与 55 常设页配套）"),
 "55_宏观背景": ("macro","active","keep","常设背景页：蓝筹池索引+利差+Jackson Hole（兼索引职能，勿动）"),
 "56_CCL_RSI档位买入": ("q_rsi","absorb","arch","被 62 号第六章『量化回测专章（56 号沉淀）』完整吸收（62 报告内明示）→ 归档候选，README 改指 62 章六"),
 "57_农业股ENSO与利率敏感性": ("ag","series","keep","目录内 4 html：主报告/绝对收益版/runup_paths/厄尔尼诺x农业股.html（152k 与主同大，疑为早期副本）→ 可清理重复文件"),
 "58_农业股地缘溢价脱钩监测": ("ag","active","keep","CF/DAR×油价脱钩（与 57/59 属农业股研究线）"),
 "59_MOS与CF化肥走势分化": ("ag","active","keep","化肥股分化归因"),
 "60_MACD死叉_4hRSI超卖_胜率回测": ("q_tm","active","keep","死叉×4hRSI 共振（SOXX/NVDA/XAUUSD/QQQ，与 01/18 同体系）"),
 "61_Apollo全球资管深度研究.html": ("fund","active","keep","APO 全周期+财务+估值（顶层散件+data.js；编号体系内唯一 61）"),
 "62_CCL全面分析": ("fund","active","keep","CCL 全面（吸收 56 号量化专章；与 64 DAL 行业可比）"),
 "63_SOFI_AFRM_SQ相关性分析": ("c_fin","active","keep","选举后窗口相关性（SOFI 族；与顶层 sofi_xyz_afrm 财报对比互补不重复）"),
 "64_DAL_RSI档位买入": ("q_rsi","active","keep","DAL RSI 越跌越买（结论与 CCL 相反：无超卖 α）"),
 "66_CVS与VIX高波动期表现": ("mkt","active","keep","VIX>18 状态×CVS 事件拆解"),
 "67_PG宝洁深度分析": ("fund","active","keep","PG 深度"),
 "68_谷物暴涨归因调查_20260903": ("ag","active","keep","谷物暴涨归因（内含 brief 简报版+主报告）"),
 "69_UNP多基准分阶段相关性": ("c_tech","active","keep","UNP×四基准分阶段（交运股×指数，与 71 配套：先相关后基本面）"),
 "70_震荡市个股突破延续性": ("q_tm","superse","arch","v1：双路径震荡判定口径；结论被 v2 严格口径否定（v2 README 明示『v1 核心结论未复现』）→ 建议归档或标注 superseded（保留供对照）"),
 "70_震荡市个股突破延续性_v2": ("q_tm","active","keep","70 主报告（重做版，结论以此为准）"),
 "71_UNP基本面深度分析": ("fund","active","keep","UNP SEC XBRL 拆解+合并专题（与 69 配套）"),
 "72_CFTC农产品持仓_20260901": ("ag","series","keep","COT 全量持仓全景（73/74/75 的上游数据报告）"),
 "73_小麦投机增仓见顶回测_20260905": ("ag","series","grp","小麦/玉米极端增仓见顶回测三连 1/3（73/74 同批方法，75 归因；建议 README 合并为『CFTC 极端持仓见顶回测系列』一行或建合集入口）"),
 "74_玉米投机净多极端脉冲_20260905": ("ag","series","grp","三连 2/3（同上）"),
 "75_小麦增仓驱动归因_20260905": ("ag","series","grp","三连 3/3（同上）"),
 # ---- 顶层散件 ----
 "13f_q2_2026_sector_flow.html": ("sec","active","keep","13F 全量资金流（季度数据，随季度更新）"),
 "DHR_vs_TMO_生物科技卖铲人对比.html": ("fund","active","keep","工具龙头基本面对比（与 24 相关性互补；顶层散件建议归入医药/工具链主题目录）"),
 "global-bond-yields-risk-20260817.html": ("macro","active","keep","全球 10Y 创高全景（顶层散件，8/17 时效快照+风险分层，与 54/55 宏观族互链）"),
 "hot_us_stocks_top300_20260901.html": ("ops","redund","arch","Top300 初版——同日被 Top500 过滤版取代（README 只登记 500 版）→ 冗余归档候选"),
 "hot_us_stocks_top500_filtered_20260901.html": ("ops","ops","keep","热榜流水线模板文件（每日由任务产出新版本）"),
 "hot354_rsi_eval_20260901.html": ("ops","ops","keep","354 池 RSI 首版"),
 "hot_rsi_eval_20260902.html": ("ops","ops","keep","日报 09-02"),
 "hot_rsi_eval_20260903.html": ("ops","ops","keep","日报 09-03"),
 "hot_rsi_eval_20260904.html": ("ops","ops","keep","日报 09-04"),
 "hot_rsi_eval_20260905.html": ("ops","ops","keep","日报 09-05"),
 "hot_rsi_latest.html": ("ops","ops","clean","『latest』=当日文件副本（与 09-05 版逐字节一致）→ 别名机制保留，但建议流水线把历史版移入独立目录，避免 reports/ 顶层膨胀"),
 "resistance_10stocks_20260902.html": ("ops","ops","clean","支撑阻力 skill 演示产物（一次性）→ 可移入 skill 演示/流水线目录"),
 "sofi_xyz_afrm_report.html": ("c_fin","active","clean","SOFI×XYZ×AFRM 财报对比+US10Y 敏感性（顶层散件；SOFI 族共 4 份横跨顶层/50/53/63 → 建议聚拢或 README 索引处集中）"),
 "vix_low_spx_report.html": ("mkt","active","clean","VIX 低位×SPX 后续（早期版）"),
 "vix_low_spy_dashboard": ("mkt","active","clean","VIX 低位×SPY 事件 dashboard（升级交互版；与 spx_report 姊妹篇，README 需标关系）"),
 "月线EMA20支撑位买入_回测报告.html": ("q_tm","active","keep","月线级别支撑回测（顶层散件）"),
 "支撑阻力日报": ("ops","ops","keep","自动任务产物（proximity 日报，每日刷新单文件；建议与 hot 日报同策略处理）"),
}

def sec_of(fam):
    for k,(_,fams) in SEC.items():
        if fam in fams: return k
    return "S10"

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    units = scan_units()
    rows, warns = [], []
    unk = [u for u in units if u["key"] not in A]
    for u in unk:
        warns.append("未标注: " + u["key"])
    for u in units:
        key = u["key"]
        fam, stat, act, note = A.get(key, ("ops","ops","clean","【待补标注】"))
        n_files = len(u["files"])
        entry = u["entry"]
        title = (u["title"] or key).strip()
        rows.append(dict(key=key, dir=u["dir"], entry=entry, n_files=n_files,
                         title=title, fam=fam, stat=stat, act=act, note=note,
                         sec=sec_of(fam)))
    # section order 固定 S1..S10
    order = [f"S{i}" for i in range(1,11)]
    stat_cn = {"active":"✓ 有效","series":"◈ 系列成员","absorb":"⊘ 被吸收","superse":"⇦ 被替代","redund":"✕ 冗余","ops":"⏱ 流水线","snap":"⌛ 时效快照"}
    act_cn = {"keep":"保留","grp":"索引归组","arch":"归档候选","merge":"合并候选","clean":"整理候选"}
    stat_color = {"active":"#1f77b4","series":"#9467bd","absorb":"#d62728","superse":"#d62728","redund":"#d62728","ops":"#7f7f7f","snap":"#ff7f0e"}
    act_color = {"keep":"#1f77b4","grp":"#9467bd","arch":"#d62728","merge":"#ff7f0e","clean":"#2ca02c"}

    def badge(txt, color, dark="#fff"):
        return f'<span class="bdg" style="border-color:{color};color:{color};">{txt}</span>'

    html_parts = []
    html_parts.append("""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>报告治理盘点与合并方案 · 2026-09-05</title><style>
:root{--ink:#1c2733;--sub:#5a6b7b;--line:#dde4ea;--bg:#f6f8fa;--card:#fff;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font:14px/1.7 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--bg);padding:28px;}
.wrap{max-width:1180px;margin:0 auto;}
h1{font-size:24px;margin-bottom:4px;} .sub{color:var(--sub);margin-bottom:18px;}
h2{font-size:18px;margin:30px 0 12px;padding-left:10px;border-left:4px solid #1f77b4;}
h3{font-size:15px;margin:16px 0 8px;}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0;}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:130px;}
.card b{font-size:22px;display:block;} .card span{color:var(--sub);font-size:12px;}
.filters{margin:12px 0;display:flex;gap:8px;flex-wrap:wrap;}
.filters button{border:1px solid var(--line);background:var(--card);border-radius:20px;padding:4px 14px;cursor:pointer;font-size:13px;}
.filters button.on{background:#1f77b4;color:#fff;border-color:#1f77b4;}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:12.5px;border:1px solid var(--line);}
th{background:#eef2f6;text-align:left;padding:7px 8px;border-bottom:2px solid var(--line);white-space:nowrap;}
td{padding:7px 8px;border-bottom:1px solid #e8edf2;vertical-align:top;}
tr.tr-arch td{background:#fdf5f5;}
tr.tr-merge td{background:#fff8ee;}
.bdg{display:inline-block;border:1px solid;border-radius:4px;padding:0 6px;font-size:11px;white-space:nowrap;margin:1px 0;}
.sec-t{background:#eef2f6;font-weight:600;cursor:pointer;}
.note{color:var(--sub);font-size:12px;}
.sum{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0;}
.sum li{margin:6px 0 6px 18px;}
.dl{border:1px solid var(--line);border-radius:10px;background:var(--card);padding:14px 16px;margin:10px 0;}
.dl b{color:#1f77b4;}
.foot{color:var(--sub);font-size:12px;margin-top:26px;border-top:1px solid var(--line);padding-top:10px;}
code{background:#eef2f6;padding:1px 5px;border-radius:4px;font-size:12px;}
</style></head><body><div class="wrap">""")

    # stats
    n_units=len(rows); n_arch=sum(1 for r in rows if r["act"]=="arch"); n_merge=len({r["key"].rsplit('_',0)[0] for r in rows if r["act"]=="merge"})
    n_files_total=sum(r["n_files"] for r in rows)
    arch_keys=[r["key"] for r in rows if r["act"]=="arch"]
    merge_groups=[("14/15/16 kbwb 弱势传导",["14_kbwb科技弱势","15_kbwb医药弱势","16_kbwbAM弱势"]),
                  ("37/38/42 中期选举窗口",["37_中期选举波动率","38_板块中期选举波动率","42_VIX中期选举抬升"]),
                  ("46-49 MCD RSI 四连",["46_MCD_RSI摆动低点支撑买入","47_MCD_RSI低位分档买入","48_MCD_RSI低位窗口质量","49_MCD_RSI区间跌落买入"])]
    html_parts.append(f"""<h1>📋 报告治理盘点与合并方案</h1>
<div class="sub">2026-09-05 · 前置检查点：已推送 <code>cd401df</code>（origin/main），可随时回滚 · 工作树 clean</div>
<div class="cards">
<div class="card"><b>{n_units}</b><span>研究条目(目录/文件)</span></div>
<div class="card"><b>{n_files_total}</b><span>HTML 文件总数</span></div>
<div class="card"><b>{n_arch}</b><span>归档候选</span></div>
<div class="card"><b>3</b><span>物理合并候选组</span></div>
<div class="card"><b>1</b><span>README 死链待修</span></div>
<div class="card"><b>0</b><span>文件已改动(纯盘点)</span></div>
</div>""")

    # 摘要
    html_parts.append("""<div class="sum"><b>执行建议（三档，按风险从低到高，可分批批准）：</b>
<ul>
<li><b>档 A · 索引重构（零文件移动，推荐先做）</b>：README 增加锚点目录 + 修正死链(<code>31_网安vs网络设备</code>→<code>35_</code>) + 系列归一行（银行牛/熊陡、蓝筹 RSI 39-41、MCD 46-49、选举 37/38/42、CFTC 73-75、景气 21/22）+ 归档项标注「已被 XX 吸收 / 已被 XX 替代」。</li>
<li><b>档 B · 归档瘦身（git mv，不动内容，可随时回滚）</b>：把「被吸收/被替代/冗余」单元移入 <code>reports/_archive_202609/</code>，README 保留一行指引到 archive 与替代报告。候选：07_sbux(被29吸收)、26_ihi_xbi_13日(口径被否)、56_CCL(被62吸收)、70v1(被v2否定)、hot_us_stocks_top300(同日被500替代)。</li>
<li><b>档 C · 物理合并（重写 HTML，成本最高，需逐组确认）</b>：候选 3 组 —— KBWB 弱势传导 14/15/16、中期选举窗口 37/38/42、MCD RSI 四连 46-49（每组合并为主报告+附录/对照归档）。</li>
<li><b>档 D · 目录整洁（可选）</b>：hot_* 日报历史版与支撑阻力日报迁入 <code>reports/_流水线/</code>；顶层散件（DHR_vs_TMO、sofi_xyz_afrm、13f、vix_low_spx 等）归入主题目录或保留但在 README 归类补齐。</li>
</ul></div>""")

    # 全表
    html_parts.append("<h2>一、全量清单（按研究族分类）</h2>")
    html_parts.append('<div class="filters" id="flt">'
        '<button data-f="*" class="on">全部</button>'
        '<button data-f="arch">⊘ 归档候选</button>'
        '<button data-f="merge">◇ 合并候选</button>'
        '<button data-f="series">◈ 系列成员</button>'
        '<button data-f="superse">⇦ 被替代</button>'
        '<button data-f="absorb">⊘ 被吸收</button>'
        '</div>')
    html_parts.append("<table><thead><tr><th style='width:26%'>报告单元 / 入口文件</th><th>核心主题 · 标的</th><th>研究族</th><th>状态</th><th>建议</th><th>备注</th></tr></thead><tbody>")
    for r in rows:
        p = r["key"] if r["dir"] else r["key"]
        entry = (r["key"] + "/" + r["entry"]) if r["dir"] and r["n_files"]>1 and not r["entry"].startswith("index") else (r["key"] if r["dir"] else r["key"])
        nm = r["key"].replace("_"," ")
        nf = f'<br><span class="note">{r["n_files"]} html</span>' if r["n_files"]>1 else ""
        t = html.escape(r["title"])
        note = html.escape(r["note"])
        trcls = "tr-arch" if r["act"]=="arch" else ("tr-merge" if r["act"]=="merge" else "")
        tags = f'data-s="{r["stat"]}" data-a="{r["act"]}"'
        html_parts.append(f'<tr class="{trcls}" {tags}><td><b>{html.escape(nm)}</b>{nf}</td>'
                          f'<td>{t}</td>'
                          f'<td>{badge(FAM[r["fam"]],"#5a6b7b")}</td>'
                          f'<td>{badge(stat_cn[r["stat"]],stat_color[r["stat"]])}</td>'
                          f'<td>{badge(act_cn[r["act"]],act_color[r["act"]])}</td>'
                          f'<td class="note">{note}</td></tr>')
    html_parts.append("</tbody></table>")

    # 重复关系明细
    html_parts.append("<h2>二、识别出的重复 / 子集 / 被替代关系（证据）</h2>")
    rels = [
        ("56 号 CCL RSI 回测 → 被 62 号吸收（最强证据）", "62 号报告第六章标题即为『量化回测专章（56 号沉淀 · 4 套口径 · 2000-2026）』，56 号的全部回测内容已在 62 号内；保留 56 号仅剩『原始口径细节』价值。", "56 归档或 README 改为指向 62 章六"),
        ("07_sbux 星巴克早期研究 → 被 29 号覆盖", "07_sbux（早期财报估值：PE 虚高）与 29 号《SBUX 基本面分析 2026-08-24》同标的同主题；29 为全面版且更新。", "07_sbux 归档（29 号内补一段早期复盘引用即可）"),
        ("70 v1 震荡市突破 → 被 70v2 否定", "v2 README 摘要明示『v1 核心结论未复现：向上突破震荡-趋势差 +2.9pp 不显著…假摔黄金坑在趋势日』；v1 的 ZigZag 双路径口径被 3 支柱检测器严格口径取代。", "v1 目录归档（对照价值保留，README 标注 superseded）"),
        ("26 IHI×XBI 13日滚动 → 辅助口径被项目铁律否决", "2026-08-23 设定：相关性以 60 日为主口径，13/30 日仅辅助、曾实证否定（13 日单点 SE=0.32 易被极端日扭曲）；26 号即该 13 日版。", "并入 23 号作附录 or 归档"),
        ("hot_us_stocks_top300 vs top500_filtered（同日 09-01）", "top500 过滤版即 300+ 的处理后产物（README 只登记 500/354 口径）；300 版无独立索引价值。", "300 版归档"),
        ("hot_rsi_latest.html = hot_rsi_eval_20260905.html（逐字节一致）", "latest 是当日文件的别名副本（固定 URL 供引用），机制合理但每日版本持续堆积在 reports/ 顶层。", "日报历史版迁移 _流水线/，latest 保留"),
        ("57 目录内疑似残留副本", "57_农业股ENSO 目录含 4 个 html：index(152k) 与 厄尔尼诺x农业股.html(152k) 同为『农业股×ENSO』主报告疑似重复副本；绝对收益版(84k) 为独立口径、runup_paths(8k) 为辅助图。", "人工确认后删/归档重复副本"),
        ("KBWB 系列命名混乱（13/14/15/16）", "13_kbwb支撑位 与 14_kbwb科技弱势 前缀重复；14/15/16 三份同模板不同板块（科技/医药/资管弱势传导）。", "14/15/16 物理合并 or 索引归组；目录改名不建议（破坏链接）"),
        ("选举三连（37/38/42）", "同为 2026 中期选举窗口事件研究：SPX 波动 / 板块波动 / VIX 抬升——同一研究批次的三份输出。", "物理合并 or README 归一行"),
        ("MCD RSI 四连（46-49）", "同一标的同一『RSI 低吸』信号族的四份独立回测（摆动低点/分档/窗口质量/区间跌落），方法逐次迭代。", "物理合并为方法族或索引归组"),
        ("KO 主题散落 6 处", "06(陡峭化窗口)、17(超买回测)、28_ko_vs_pep(基本面)、32(×科技医药相关)、37(×XLV/道指)——同标的多角度研究，不构成重复，但 README 缺少 KO 总入口。", "README 处加『按标的检索』索引"),
        ("CSCO 主题 3 处", "19(×BUG)、35(×PANW/CRWD)、38(×纳指/道指)——同上，非重复。", "README 按标的索引覆盖"),
        ("SOFI 主题 4 处", "顶层 sofi_xyz_afrm(财报+US10Y)、50(×BTC)、53(财报日)、63(×AFRM/SQ)——互补研究。", "README 按标的索引覆盖"),
        ("UNP 69+71 / CCL 56+62 / MCD 46-49+51 / ABBV 11+28+43 / GILD 02+10+11+12", "个股常同时出现在『事件/量化回测』与『基本面深度』两条线，构成跨报告研究链而非重复。", "README 增『按标的检索』层"),
    ]
    for t, det, sug in rels:
        html_parts.append(f'<div class="dl"><b>◇ {html.escape(t)}</b><br><span class="note">{html.escape(det)}</span><br><span class="note">→ 处理：{html.escape(sug)}</span></div>')

    # 执行清单
    html_parts.append("<h2>三、建议执行顺序（Git 全程可控，回滚点 cd401df）</h2>")
    steps = [
        ("档 A（推荐先做 · 零风险）", "① 修 README 死链 31→35；② README 顶部加锚点目录；③ 系列归一行（银行 08/09、蓝筹RSI 39-41、MCD 46-49、选举 37/38/42、景气 21/22、CFTC 73-75）；④ 归档项加『superseded/absorbed』标注；⑤ 可加『按标的检索』小节。commit 一次。"),
        ("档 B（建议本批做 · 中风险低）", "git mv 以下单元至 reports/_archive_202609/：07_sbux星巴克、26_ihi_xbi_13日滚动相关、56_CCL_RSI档位买入、70_震荡市个股突破延续性(v1)、hot_us_stocks_top300_20260901.html。README 同步。commit 一次。回滚：git revert 或 git mv 回来。"),
        ("档 C（需逐组确认 · 高风险高成本）", "物理合并 3 组（KBWB 14/15/16、选举 37/38/42、MCD 46-49），每组：新建合集 index.html（保留全部图表/表格），原文归档 _archive_202609/。建议一次只做一组，各 commit 一次。"),
        ("档 D（可选）", "hot 日报历史版+支撑阻力日报迁入 reports/_流水线/；57 目录重复副本清理；顶层散件归类。"),
    ]
    for t, d in steps:
        html_parts.append(f'<div class="dl"><b>{html.escape(t)}</b><br><span>{html.escape(d)}</span></div>')

    html_parts.append("""<div class="foot">生成：2026-09-05 · 本页为决策草案，未改动任何报告文件 · 数据源：README.md 索引 + reports/ 目录实扫 + 各报告 <title> · 颜色说明：红系=归档/被替代候选，橙=物理合并候选，蓝=保留 · 图例均含文字标签（色弱安全）</div>
<script>
document.getElementById('flt').addEventListener('click',function(e){
  if(e.target.tagName!=='BUTTON')return;
  var f=e.target.getAttribute('data-f');
  document.querySelectorAll('#flt button').forEach(b=>b.classList.remove('on'));
  e.target.classList.add('on');
  document.querySelectorAll('tbody tr').forEach(tr=>{
    var show = f==='*'|| (f==='arch'&&tr.getAttribute('data-a')==='arch')||(f==='merge'&&tr.getAttribute('data-a')==='merge')||(f==='series'&&tr.getAttribute('data-s')==='series')||(f==='superse'&&tr.getAttribute('data-s')==='superse')||(f==='absorb'&&tr.getAttribute('data-s')==='absorb');
    tr.style.display=show?'':'none';
  });
});
</script>
</div></body></html>""")
    html_out = "\n".join(html_parts)
    with open(OUT,"w",encoding="utf-8") as f:
        f.write(html_out)
    print("OUT:", OUT)
    print("units:", n_units, "| html files:", n_files_total)
    print("归档候选:", [r["key"] for r in rows if r["act"]=="arch"])
    print("合并候选:", [r["key"] for r in rows if r["act"]=="merge"])
    if warns:
        print("WARNINGS:")
        for w in warns: print("  ", w)
    else:
        print("warnings: none (all annotated)")

if __name__ == "__main__":
    main()
