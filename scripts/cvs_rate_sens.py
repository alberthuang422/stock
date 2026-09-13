# -*- coding: utf-8 -*-
"""
CVS × 美债利率（US10Y / US2Y）敏感性分析
- 日频多元回归：ret_CVS = α + β1·ΔUS10Y(bp) + β2·ΔUS2Y(bp) + β3·ret_SPY + ε
- 等价正交化规格：ret_CVS = α + β_level·ΔUS10Y + β_slope·Δ(10Y−2Y) + β_spy·ret_SPY
- 60 日滚动相关（项目主口径）
- 利率变动分档的绝对/超额收益与胜率
- 期限结构形态（陡/平 × 走阔/收窄）分组
- pre-Aetna(2018-11-28 前) / post-Aetna 分段
- 同业对照：UNH / CI / XLV
p 值一律用 scipy，禁止手写 t 分布 CDF（项目 57 号报告的踩坑教训）
"""
import json
import os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "cvs_rate_sens.json")

AETNA_DATE = pd.Timestamp("2018-11-28")      # Aetna 收购完成日
WIN = 60                                      # 滚动窗口（项目主口径）
MAIN = "CVS"
PEERS = ["CVS", "UNH", "CI", "XLV", "SPY"]


# ---------------- 数据载入 ----------------
def load_px(tk):
    p = os.path.join(DATA, tk.lower(), f"{tk}, 1D.csv")
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df = df.dropna(subset=["adj_close"])
    return df.set_index("date")


def load_rate(name):
    df = pd.read_csv(os.path.join(DATA, "us_treasury", f"{name}.csv"))
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    df[name] = pd.to_numeric(df[name], errors="coerce")
    return df.dropna(subset=[name]).set_index("observation_date")[name].astype(float)


px = {t: load_px(t) for t in PEERS}
r10 = load_rate("DGS10")
r2 = load_rate("DGS2")

# ---------------- 面板构建 ----------------
# 只保留股债同时有报价的交易日（债券市场休市日如哥伦布日/退伍军人节，美股照常交易）
close = pd.DataFrame({t: px[t]["adj_close"] for t in PEERS})
vol = px[MAIN]["volume"].rename("volume")
df = close.join(vol, how="left")
df = df.join(r10.rename("y10"), how="inner").join(r2.rename("y2"), how="inner")
df = df.dropna(subset=["y10", "y2"])

# 收益率（%）与利率变动（bp）
for t in PEERS:
    df[f"ret_{t.lower()}"] = df[t].pct_change() * 100
df["d10"] = df["y10"].diff() * 100
df["d2"] = df["y2"].diff() * 100
df["slope"] = df["y10"] - df["y2"]
df["dslope"] = df["d10"] - df["d2"]
panel = df.dropna(subset=["ret_cvs", "d10", "d2", "ret_spy"]).copy()
panel["era"] = np.where(panel.index >= AETNA_DATE, "post_aetna", "pre_aetna")

SAMPLE = {
    "start": str(panel.index.min().date()),
    "end": str(panel.index.max().date()),
    "n_days": int(len(panel)),
    "aetna_date": str(AETNA_DATE.date()),
    "n_pre": int((panel["era"] == "pre_aetna").sum()),
    "n_post": int((panel["era"] == "post_aetna").sum()),
}


# ---------------- OLS（scipy 求 p 值） ----------------
def ols(y, cols, names):
    y = np.asarray(y, dtype=float)
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, dtype=float) for c in cols])
    if len(y) <= X.shape[1] + 2:
        return None
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    resid = y - yhat
    dof = len(y) - X.shape[1]
    s2 = resid @ resid / dof
    cov = s2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    with np.errstate(divide="ignore", invalid="ignore"):
        tval = beta / se
        pval = 2 * (1 - stats.t.cdf(np.abs(tval), dof))
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = float(1 - (resid @ resid) / ss_tot) if ss_tot > 0 else 0.0
    out = {"n": int(len(y)), "r2": round(r2, 4), "dof": int(dof)}
    for i, nm in enumerate(names):
        out[f"beta_{nm}"] = round(float(beta[i + 1]), 5)
        out[f"t_{nm}"] = round(float(tval[i + 1]), 2)
        out[f"p_{nm}"] = round(float(pval[i + 1]), 5)
    out["alpha"] = round(float(beta[0]), 4)
    out["p_alpha"] = round(float(pval[0]), 5)
    return out


def sig(p):
    if p is None:
        return "no"
    if p < 0.01:
        return "sig"
    if p < 0.05:
        return "edge"
    return "no"


def add_sig(d, key):
    d[f"sig_{key}"] = sig(d.get(f"p_{key}"))
    return d


# ---------------- 1) 全样本 / 分段回归 ----------------
def run_models(sub, label):
    res = {"label": label, "n": int(len(sub))}
    if len(sub) < 40:
        res["error"] = "样本不足"
        return res
    # 模型 A：长端 + 短端 + 大盘
    a = ols(sub["ret_cvs"].values,
            [sub["d10"].values, sub["d2"].values, sub["ret_spy"].values],
            ["d10", "d2", "spy"])
    if a:
        for k in ("d10", "d2"):
            add_sig(a, k)
        res["modelA"] = a
    # 模型 B：长端水平 + 期限斜率 + 大盘（正交化表述）
    b = ols(sub["ret_cvs"].values,
            [sub["d10"].values, sub["dslope"].values, sub["ret_spy"].values],
            ["level", "slope", "spy"])
    if b:
        for k in ("level", "slope"):
            add_sig(b, k)
        res["modelB"] = b
    # 模型 C：加入板块（XLV，1998 后才有数据）
    if "ret_xlv" in sub.columns:
        c = sub.dropna(subset=["ret_xlv"])
        if len(c) >= 40:
            cc = ols(c["ret_cvs"].values,
                     [c["d10"].values, c["d2"].values, c["ret_spy"].values, c["ret_xlv"].values],
                     ["d10", "d2", "spy", "xlv"])
            if cc:
                for k in ("d10", "d2"):
                    add_sig(cc, k)
                res["modelC"] = cc
    # 单变量相关（相关系数 R）
    res["corr"] = {
        "cvs_d10": round(float(sub["ret_cvs"].corr(sub["d10"])), 4),
        "cvs_d2": round(float(sub["ret_cvs"].corr(sub["d2"])), 4),
        "cvs_dslope": round(float(sub["ret_cvs"].corr(sub["dslope"])), 4),
        "cvs_spy": round(float(sub["ret_cvs"].corr(sub["ret_spy"])), 4),
    }
    res["sd"] = {"cvs": round(float(sub["ret_cvs"].std()), 3),
                 "d10_bp": round(float(sub["d10"].std()), 1),
                 "d2_bp": round(float(sub["d2"].std()), 1)}
    return res


models = {
    "full": run_models(panel, "全样本"),
    "pre_aetna": run_models(panel[panel["era"] == "pre_aetna"], "Pre-Aetna（2018-11-28 前）"),
    "post_aetna": run_models(panel[panel["era"] == "post_aetna"], "Post-Aetna（2018-11-28 起）"),
}

# 利率水平分档
# 注意：仅在 post-Aetna 内分档。全样本分档会把 1993-2000 的高利率时代
# （当时 CVS 还是纯零售药房）与 2023 年后的高利率环境混为一谈，结论不可比。
_post = panel[panel["era"] == "post_aetna"]
LEVEL_BINS = [("<2%", _post["y10"] < 2),
              ("2–3%", (_post["y10"] >= 2) & (_post["y10"] < 3)),
              ("3–4%", (_post["y10"] >= 3) & (_post["y10"] < 4)),
              ("≥4%", _post["y10"] >= 4)]
models_by_level = {}
for lb, mask in LEVEL_BINS:
    sub = _post[mask]
    m = run_models(sub, f"US10Y {lb} 环境（post-Aetna）")
    if len(sub):
        m["span"] = f"{sub.index.min().date()} ~ {sub.index.max().date()}"
        m["y10_mean"] = round(float(sub["y10"].mean()), 2)
    models_by_level[lb] = m

# 全样本口径（仅作对照，标注存在跨时代混杂）
level_full = {}
for lb, mask in [("<2%", panel["y10"] < 2),
                 ("2–4%", (panel["y10"] >= 2) & (panel["y10"] < 4)),
                 ("≥4%", panel["y10"] >= 4)]:
    sub = panel[mask]
    m = run_models(sub, f"US10Y {lb}（全样本，含跨时代混杂）")
    if len(sub):
        m["span"] = f"{sub.index.min().date()} ~ {sub.index.max().date()}"
    level_full[lb] = m

# ---------------- 2) 同业对照（post-Aetna 同期，口径可比） ----------------
post = panel[panel["era"] == "post_aetna"]
peer_res = {}
for t in ["CVS", "UNH", "CI", "XLV"]:
    col = f"ret_{t.lower()}"
    sub = post.dropna(subset=[col])
    if len(sub) < 40:
        continue
    m = ols(sub[col].values,
            [sub["d10"].values, sub["d2"].values, sub["ret_spy"].values],
            ["d10", "d2", "spy"])
    if m:
        for k in ("d10", "d2"):
            add_sig(m, k)
        m["corr_d10"] = round(float(sub[col].corr(sub["d10"])), 4)
        m["corr_d2"] = round(float(sub[col].corr(sub["d2"])), 4)
        m["ann_vol"] = round(float(sub[col].std()) * np.sqrt(252), 1)
        peer_res[t] = m

# ---------------- 3) 60 日滚动相关（项目主口径） ----------------
roll = pd.DataFrame(index=panel.index)
roll["corr_d10"] = panel["ret_cvs"].rolling(WIN).corr(panel["d10"])
roll["corr_d2"] = panel["ret_cvs"].rolling(WIN).corr(panel["d2"])
roll["corr_dslope"] = panel["ret_cvs"].rolling(WIN).corr(panel["dslope"])
roll["beta_d10"] = np.nan
# 滚动 β：ret_cvs ~ d10 + ret_spy（60 日窗口）
rc, rd, rs = panel["ret_cvs"].values, panel["d10"].values, panel["ret_spy"].values
for i in range(WIN, len(panel)):
    sl = slice(i - WIN, i)
    m = ols(rc[sl], [rd[sl], rs[sl]], ["d10", "spy"])
    if m:
        roll.iloc[i, roll.columns.get_loc("beta_d10")] = m["beta_d10"]
roll = roll.dropna(how="all")

# 滚动窗口按季度降采样太多，这里输出 post-Aetna 段的滚动序列 + 全样本关键分位
roll_post = roll[roll.index >= AETNA_DATE].dropna(subset=["corr_d10"])
roll_stats = {
    "win": WIN,
    "post_corr_d10_mean": round(float(roll_post["corr_d10"].mean()), 4),
    "post_corr_d10_med": round(float(roll_post["corr_d10"].median()), 4),
    "post_corr_d10_p10": round(float(roll_post["corr_d10"].quantile(0.10)), 4),
    "post_corr_d10_p90": round(float(roll_post["corr_d10"].quantile(0.90)), 4),
    "post_corr_d10_latest": round(float(roll_post["corr_d10"].iloc[-1]), 4),
    "post_beta_d10_mean": round(float(roll_post["beta_d10"].dropna().mean()), 4),
    "post_beta_d10_latest": round(float(roll_post["beta_d10"].dropna().iloc[-1]), 4),
    "latest_date": str(roll_post.index[-1].date()),
}

# 滚动序列（2019 年起，供图表使用；相关系数为小数，前端注入 ECharts 前需 ×100 转百分数）
roll_series = [
    {"d": str(d.date()),
     "c10": None if pd.isna(r.corr_d10) else round(float(r.corr_d10), 4),
     "c2": None if pd.isna(r.corr_d2) else round(float(r.corr_d2), 4),
     "b10": None if pd.isna(r.beta_d10) else round(float(r.beta_d10), 4)}
    for d, r in roll[roll.index >= pd.Timestamp("2019-01-01")].iterrows()
]

# ---------------- 4) 利率变动分档（日频） ----------------
BINS = [("大幅上行 >+10bp", lambda s: s > 10),
        ("上行 +3~+10bp", lambda s: (s > 3) & (s <= 10)),
        ("震荡 −3~+3bp", lambda s: (s >= -3) & (s <= 3)),
        ("下行 −10~−3bp", lambda s: (s >= -10) & (s < -3)),
        ("大幅下行 <−10bp", lambda s: s < -10)]


def bucket_stats(sub, col, val_col="ret_cvs"):
    out = []
    for name, fn in BINS:
        m = sub[fn(sub[col])]
        if len(m) < 30:
            out.append({"bucket": name, "n": int(len(m)), "skip": True})
            continue
        r = m[val_col]
        ex = r - m["ret_spy"]
        t_ex, p_ex = stats.ttest_1samp(ex.dropna(), 0.0)
        out.append({
            "bucket": name, "n": int(len(m)),
            "mean": round(float(r.mean()), 4),
            "med": round(float(r.median()), 4),
            "excess": round(float(ex.mean()), 4),
            "win": round(float((r > 0).mean()) * 100, 1),
            "t_ex": round(float(t_ex), 2), "p_ex": round(float(p_ex), 5),
            "sig": sig(float(p_ex)),
            "mean_d10bp": round(float(m["d10"].mean()), 1),
        })
    return out


buckets = {
    "post_d10": bucket_stats(post, "d10"),
    "post_d2": bucket_stats(post, "d2"),
    "pre_d10": bucket_stats(panel[panel["era"] == "pre_aetna"], "d10"),
}

# ---------------- 5) 期限结构形态分组 ----------------
# 【单位陷阱】slope = US10Y − US2Y，单位为「百分点」，不是 bp。
# 50bp 必须写成 0.50；写成 50 会让"陡峭"档永远为空、而"平坦"档吞掉全部正斜率样本。
shape_bins = [("倒挂 slope<0", post["slope"] < 0),
              ("平缓 0~50bp", (post["slope"] >= 0) & (post["slope"] < 0.50)),
              ("陡峭 ≥50bp", post["slope"] >= 0.50)]
shape_stats = []
for name, mask in shape_bins:
    m = post[mask]
    if len(m) < 30:
        shape_stats.append({"shape": name, "n": int(len(m)), "skip": True})
        continue
    mm = ols(m["ret_cvs"].values, [m["d10"].values, m["ret_spy"].values], ["d10", "spy"])
    e = m["ret_cvs"] - m["ret_spy"]
    t_ex, p_ex = stats.ttest_1samp(e.dropna(), 0.0)
    shape_stats.append({
        "shape": name, "n": int(len(m)),
        "ann_ret": round(float(m["ret_cvs"].mean() * 252), 2),
        "ann_vol": round(float(m["ret_cvs"].std()) * np.sqrt(252), 1),
        "excess_d": round(float(e.mean()), 4),
        "p_ex": round(float(p_ex), 5),
        "beta_d10": mm["beta_d10"] if mm else None,
        "p_d10": mm["p_d10"] if mm else None,
        "sig_d10": sig(mm["p_d10"]) if mm else "no",
        "corr_d10": round(float(m["ret_cvs"].corr(m["d10"])), 4),
    })

# 走阔 / 收窄
steep_bins = [("走阔 >+5bp", post["dslope"] > 5),
              ("平稳 −5~+5bp", (post["dslope"] >= -5) & (post["dslope"] <= 5)),
              ("收窄 <−5bp", post["dslope"] < -5)]
steep_stats = []
for name, mask in steep_bins:
    m = post[mask]
    if len(m) < 30:
        steep_stats.append({"move": name, "n": int(len(m)), "skip": True})
        continue
    e = m["ret_cvs"] - m["ret_spy"]
    t_ex, p_ex = stats.ttest_1samp(e.dropna(), 0.0)
    steep_stats.append({
        "move": name, "n": int(len(m)),
        "mean": round(float(m["ret_cvs"].mean()), 4),
        "excess": round(float(e.mean()), 4),
        "win": round(float((m["ret_cvs"] > 0).mean()) * 100, 1),
        "t_ex": round(float(t_ex), 2), "p_ex": round(float(p_ex), 5),
        "sig": sig(float(p_ex)),
    })

# ---------------- 6) 季度分阶段（post-Aetna，自然年日历季度） ----------------
q = post.copy()
q["q"] = q.index.to_period("Q").astype(str)
quarters = []
for qs, g in q.groupby("q"):
    if len(g) < 30:
        continue
    m = ols(g["ret_cvs"].values, [g["d10"].values, g["ret_spy"].values], ["d10", "spy"])
    e = g["ret_cvs"] - g["ret_spy"]
    quarters.append({
        "q": qs, "n": int(len(g)),
        "y10_start": round(float(g["y10"].iloc[0]), 2),
        "y10_end": round(float(g["y10"].iloc[-1]), 2),
        "d_q_bp": round(float((g["y10"].iloc[-1] - g["y10"].iloc[0]) * 100), 0),
        "corr_d10": round(float(g["ret_cvs"].corr(g["d10"])), 4),
        "beta_d10": m["beta_d10"] if m else None,
        "p_d10": m["p_d10"] if m else None,
        "sig": sig(m["p_d10"]) if m else "no",
        "ret_cvs": round(float(g["ret_cvs"].sum()), 2),
        "ret_spy": round(float(g["ret_spy"].sum()), 2),
        "excess": round(float(e.sum()), 2),
    })

# ---------------- 6.5) 解释力拆解：利率到底贡献了多少？ ----------------
# β 统计显著 ≠ 经济意义重大。必须量化利率因子的增量 R²，否则会高估利率的作用。
def _r2(y, cols):
    y = np.asarray(y, dtype=float)
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, dtype=float) for c in cols])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    return float(1 - (r @ r) / ((y - y.mean()) @ (y - y.mean())))


expl = {}
for lbl, sub in [("full", panel),
                 ("pre_aetna", panel[panel["era"] == "pre_aetna"]),
                 ("post_aetna", post)]:
    y = sub["ret_cvs"].values
    rs, d1, d2v = sub["ret_spy"].values, sub["d10"].values, sub["d2"].values
    r_spy = _r2(y, [rs])
    r_10 = _r2(y, [rs, d1])
    r_both = _r2(y, [rs, d1, d2v])
    expl[lbl] = {
        "r2_spy_only": round(r_spy, 4),
        "r2_plus_d10": round(r_10, 4),
        "r2_plus_d2": round(r_both, 4),
        "incr_d10": round(r_10 - r_spy, 4),
        "incr_d2": round(r_both - r_10, 4),
        "corr_d10_d2": round(float(pd.Series(d1).corr(pd.Series(d2v))), 3),
        "corr_d10_dslope": round(float(pd.Series(d1).corr(pd.Series(d1 - d2v))), 3),
    }

# ---------------- 7) 当前环境快照 ----------------
last = panel.iloc[-1]
recent = panel.tail(60)
cur = {
    "date": str(panel.index[-1].date()),
    "y10": round(float(last["y10"]), 2),
    "y2": round(float(last["y2"]), 2),
    "slope_bp": round(float((last["y10"] - last["y2"]) * 100), 0),
    "y10_1y_ago": round(float(panel["y10"].iloc[-253]), 2) if len(panel) > 253 else None,
    "d10_sd_60d_bp": round(float(recent["d10"].std()), 1),
    "corr_60d": roll_stats["post_corr_d10_latest"],
    "beta_60d": roll_stats["post_beta_d10_latest"],
    "cvs_close": round(float(px[MAIN]["close"].iloc[-1]), 2),
    "cvs_volume": int(px[MAIN]["volume"].iloc[-1]) if not pd.isna(px[MAIN]["volume"].iloc[-1]) else None,
    "cvs_vol_med60": int(px[MAIN]["volume"].tail(60).median()),
}

# 尾 bar 体检（项目规范：成交量远低于常态 = 不完整 bar）
cur["tail_bar_ok"] = bool(cur["cvs_volume"] and cur["cvs_vol_med60"]
                          and cur["cvs_volume"] > 0.3 * cur["cvs_vol_med60"])

# 累计曲线（post-Aetna 起，CVS / SPY / XLV 净值 + US10Y 背景）
cum = post[["ret_cvs", "ret_spy", "ret_xlv"]].copy()
cum = (1 + cum / 100).cumprod() * 100
cum_series = [
    {"d": str(d.date()),
     "cvs": round(float(r.ret_cvs), 2),
     "spy": round(float(r.ret_spy), 2),
     "xlv": round(float(r.ret_xlv), 2) if not pd.isna(r.ret_xlv) else None,
     "y10": round(float(post.loc[d, "y10"]), 2)}
    for d, r in cum.iterrows()
]

result = {
    "meta": {"generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
             "win": WIN, "main": MAIN, "peers": PEERS,
             "source": "行情 Yahoo(CDP)；利率 FRED DGS10/DGS2",
             "aetna_date": str(AETNA_DATE.date())},
    "sample": SAMPLE,
    "models": models,
    "models_by_level": models_by_level,
    "models_by_level_full": level_full,
    "explained": expl,
    "peers": peer_res,
    "roll_stats": roll_stats,
    "roll_series": roll_series,
    "buckets": buckets,
    "shape": shape_stats,
    "steep": steep_stats,
    "quarters": quarters,
    "current": cur,
    "cum_series": cum_series,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False)
print("written:", OUT, os.path.getsize(OUT), "bytes")
print("样本:", SAMPLE)
print("全样本 β(d10):", models["full"].get("modelA", {}).get("beta_d10"),
      "p=", models["full"].get("modelA", {}).get("p_d10"))
print("post-Aetna β(d10):", models["post_aetna"].get("modelA", {}).get("beta_d10"),
      "p=", models["post_aetna"].get("modelA", {}).get("p_d10"))
print("当前:", cur)
