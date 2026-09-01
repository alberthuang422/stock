# -*- coding: utf-8 -*-
"""生成 61 号 APO 报告的内嵌 chart 数据 JS（reports/61_apo_data.js）。
文件:// 打开时 <script src> 本地相对路径可加载，规避 fetch CORS。
"""
import json
import pandas as pd

ROOT = r"C:\Users\Administrator\Desktop\stock\data"
def load(t):
    return pd.read_csv(f"{ROOT}/{t.lower()}/{t.upper()}, 1D.csv", parse_dates=["date"]).dropna(subset=["adj_close"]).sort_values("date").reset_index(drop=True)

apo, bx, kkr, spy = load("APO"), load("BX"), load("KKR"), load("SPY")

def month_end(s):
    df = s.copy()
    df["ym"] = df["date"].dt.to_period("M")
    out = df.groupby("ym").tail(1)
    return out

# 1) 月末复权价格序列（2011-03 起，对齐）
def align_monthly(series_list):
    frames = []
    for s, name in series_list:
        m = month_end(s)[["date", "adj_close"]].rename(columns={"adj_close": name})
        m[name] = (m[name] / m[name].iloc[0]) * 100  # 以各自 2011-03 末为 100（APO 上市起）
        frames.append(m.set_index("date"))
    df = frames[0]
    for f in frames[1:]:
        df = df.join(f, how="outer")
    df = df.sort_index()
    return [[str(d.date()), None if pd.isna(df.loc[d, c]) else round(float(df.loc[d, c]), 1)]
            for d in df.index for c in ["APO", "SPY", "BX", "KKR"]]

# 分别以各自起点归一不适合共存一图（BX 2007、SPY 1993），统一从 2011-04 起按各自 2011-04 底=100
def series_from(s, name):
    m = month_end(s)
    m = m[m["date"] >= "2011-04-01"]
    base = m.iloc[0]["adj_close"]
    return m[["date"]].assign(v=round((m["adj_close"] / base) * 100, 1), name=name)

m_apo, m_spy, m_bx, m_kkr = series_from(apo, "APO"), series_from(spy, "SPY"), series_from(bx, "BX"), series_from(kkr, "KKR")

price_by = {"date": [], "APO": [], "SPY": [], "BX": [], "KKR": []}
dates = sorted(set(m_apo["date"]).union(m_spy["date"]).union(m_bx["date"]).union(m_kkr["date"]))
dmap = {}
for name, m in [("APO", m_apo), ("SPY", m_spy), ("BX", m_bx), ("KKR", m_kkr)]:
    dmap[name] = dict(zip(m["date"], m["v"]))
import pandas as _pd
_df = _pd.DataFrame(index=_pd.to_datetime(dates))
for _name in ["APO", "SPY", "BX", "KKR"]:
    _df[_name] = [dmap[_name].get(d) for d in dates]
_df = _df.sort_index()
# 各标的数据截止日不同（如 APO 到 08-27、BX 到 08-26），每月只保留最新交易日并前向填充缺失列
_df = _df.groupby(_df.index.to_period("M")).tail(1).ffill()
for _d, _row in _df.iterrows():
    price_by["date"].append(str(_d.date()))
    for _name in ["APO", "SPY", "BX", "KKR"]:
        price_by[_name].append(None if _pd.isna(_row[_name]) else round(float(_row[_name]), 1))

# 2) 年度收益（2012-2026YTD，APO/SPY/BX/KKR）
def yearly(s):
    rows = {}
    for y, g in s.groupby(s["date"].dt.year):
        if len(g) >= 2:
            rows[int(y)] = round((g.iloc[-1]["adj_close"] / g.iloc[0]["adj_close"] - 1) * 100, 1)
    return rows
ya, ys, yb, yk = yearly(apo), yearly(spy), yearly(bx), yearly(kkr)
years = sorted(set(ya) & set(ys))
yearly_data = {
    "years": [str(y) for y in years],
    "APO": [ya.get(y) for y in years],
    "SPY": [ys.get(y) for y in years],
    "BX": [yb.get(y) for y in years],
    "KKR": [yk.get(y) for y in years],
}

# 3) 60 日滚动相关性（从 2013 起，含 None 前段用 null）
def rolling_corr(a, b, win=60, start="2012-01-01"):
    aa = a.set_index("date")["adj_close"].reindex(a.date).astype(float)
    bb = b.set_index("date")["adj_close"].reindex(a.date).astype(float)
    ra, rb = aa.pct_change(), bb.pct_change()
    df = pd.concat([ra, rb], axis=1).dropna()
    c = df.iloc[:, 0].rolling(win).corr(df.iloc[:, 1])
    c = c[c.index >= start]
    return [[str(d.date()), None if pd.isna(v) else round(float(v), 3)] for d, v in c.items()]

corr = {
    "dates": [x[0] for x in rolling_corr(apo, spy)],
    "APO_SPY": [x[1] for x in rolling_corr(apo, spy)],
}
cb = rolling_corr(apo, bx); ck = rolling_corr(apo, kkr)
corr["APO_BX"] = [x[1] for x in cb]
corr["APO_KKR"] = [x[1] for x in ck]

# 4) 同行估值对比卡（检索源 2026-09-01 快照）
peers = [
    {"ticker": "BX", "aum": 13460, "mktcap": 163.7, "pe": 30.6, "pb": 11.4, "dy": 3.82},
    {"ticker": "APO", "aum": 10470, "mktcap": 101.8, "pe": 46.7, "pb": 4.0, "dy": 1.64},
    {"ticker": "KKR", "aum": 7960, "mktcap": 99.3, "pe": 34.1, "pb": 3.4, "dy": 0.71},
    {"ticker": "OWL", "aum": 3190, "mktcap": 18.5, "pe": 148.9, "pb": 4.0, "dy": 7.73},
    {"ticker": "TPG", "aum": 3060, "mktcap": 20.5, "pe": 78.3, "pb": 7.1, "dy": 4.27},
]

# 5) FRE/SRE 季度序列（已核实点）单位 百万美元
fre = {"q": ["1Q25*", "4Q25*", "1Q26", "2Q26"], "fre": [560, 624, 728, 785], "sre": [None, None, 719, 877]}
# 注：1Q25 FRE 由 1Q26 +30%YoY 反推(=728/1.30)；4Q25 由 LTM1Q26 2697-1Q26-4Q25? 不可直接推，
# 保守只画 1Q26 与 2Q26 + LTM 标注。改为季度两列可用点。

fre2 = {"q": ["1Q26", "2Q26"], "fre": [728, 785], "sre": [719, 877]}

data = {
    "price": price_by,
    "yearly": yearly_data,
    "corr60": corr,
    "peers": peers,
    "fre": fre2,
    "regions": {
        "periods": {
            "1Y": {"APO": -0.54, "SPY": 20.14, "BX": -13.38, "KKR": -21.99},
            "3Y": {"APO": 67.09, "SPY": 80.77, "BX": 56.15, "KKR": 82.55},
            "5Y": {"APO": 150.65, "SPY": 83.24, "BX": 37.29, "KKR": 76.25},
            "10Y": {"APO": 951.83, "SPY": 314.57, "BX": 708.72, "KKR": 759.83},
            "IPO": {"APO": 1801.13, "SPY": 659.92, "BX": 1596.14, "KKR": 990.41},
        },
        "cagr": {
            "1Y": {"APO": -0.55, "SPY": 20.22, "BX": -13.45, "KKR": -22.11},
            "3Y": {"APO": 18.68, "SPY": 21.83, "BX": 16.04, "KKR": 22.26},
            "5Y": {"APO": 20.18, "SPY": 12.88, "BX": 6.55, "KKR": 12.01},
            "10Y": {"APO": 26.55, "SPY": 15.29, "BX": 23.27, "KKR": 24.03},
            "IPO": {"APO": 21.06, "SPY": 14.06, "BX": 20.17, "KKR": 16.77},
        },
        "maxdd": {
            "1Y": {"APO": -34.05, "SPY": -8.88, "BX": -44.76, "KKR": -43.64},
            "3Y": {"APO": -42.82, "SPY": -18.76, "BX": -46.5, "KKR": -49.42},
            "5Y": {"APO": -42.82, "SPY": -24.5, "BX": -49.29, "KKR": -49.42},
            "10Y": {"APO": -53.48, "SPY": -33.72, "BX": -49.29, "KKR": -49.42},
            "IPO": {"APO": -56.99, "SPY": -33.72, "BX": -49.29, "KKR": -53.1},
        },
    },
    "miles": {
        "aum_2026q1": 1026, "aum_2026q2": 1047, "fgaum_q1": 836, "fgaum_q2": 858,
        "ltm_fre_1q": 2697, "ltm_fre_2q": 2754, "ltm_sre_1q": 3276, "ltm_sre_2q": 3434,
    },
    "quick": {"pe_ttm": 46.7, "target": 154.26, "target_up": 17.5},
}

js = "// 61 号报告图表数据（由 scripts/apo_61_gen_data.py 生成）\nconst APO_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
with open(r"C:\Users\Administrator\Desktop\stock\reports\61_apo_data.js", "w", encoding="utf-8") as f:
    f.write(js)
print("OK len(js):", len(js), "price points:", len(price_by["date"]))