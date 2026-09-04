# -*- coding: utf-8 -*-
"""Step 4 稳健性（备用震荡定义 × T+5/T+20 窗口 × 四时段）+ Step 5 控制回归 + 前视自检。
产出 results/70_v2/robustness.csv、regression.csv、leak_check.json"""
import sys, os, json
import numpy as np
import pandas as pd
sys.path.insert(0, r"C:\Users\Administrator\Desktop\stock\scripts")
from v2_choppy_breakout import CONFIG, load_ohlc, load_spy, choppy_detector
from v2_pipeline import build_all_events, rate_diff_ci, fisher_test, bh_adjust, fade_backtest

OUT = CONFIG["out_dir"]; cfg = CONFIG

def main():
    spy = load_spy()
    earn_csv = os.path.join(OUT, "earnings_all.csv")
    edf = pd.read_csv(earn_csv); edf["date"] = pd.to_datetime(edf["date"])
    earn_map = edf.groupby("ticker")

    # ------- Step 4a 备用定义 -------
    rows = []
    for variant in [None, "altA", "altB", "altC"]:
        ch = choppy_detector(spy, variant)
        ev = build_all_events(ch, earn_map)
        ev = ev[~ev["gap_skip"]].copy()
        for dr in ("up","down"):
            sub = ev[ev["dir"]==dr]
            for k in (1.0,):
                obs, lo, hi = rate_diff_ci(sub, k, n_boot=1000)
                ft = fisher_test(sub, k)
                rows.append(dict(variant=str(variant), dir=dr, k=k,
                                 diff=obs, lo=lo, hi=hi, odds=ft["odds"], p=ft["p"]))
        print(f"variant={variant}: n={len(ev)} done", flush=True)
    rdf = pd.DataFrame(rows)
    rdf["p_bh"] = bh_adjust(rdf["p"].values)
    rdf.to_csv(os.path.join(OUT, "robustness_variants.csv"), index=False)
    print(rdf.to_string(index=False))

    # ------- Step 4b T+5 / T+20 窗口（dev 窗口改 N）-------
    # dev_max 当前为 T+10；为窗口稳健性，改用 fwd5/fwd20 收益差做辅助（不改 dev 定义）
    rows2 = []
    ch = choppy_detector(spy)
    ev = build_all_events(ch, earn_map)
    evm = ev[~ev["gap_skip"]].copy()
    for N in (5, 10, 20):
        for dr in ("up","down"):
            sub = evm[evm["dir"]==dr]
            for c_ in (1, 0):
                x = sub[sub["choppy"]==c_][f"fwd{N}"].dropna()
                rows2.append(dict(window=N, dir=dr, choppy=c_, n=len(x),
                                  med=float(x.median()), mean=float(x.mean())))
    pd.DataFrame(rows2).to_csv(os.path.join(OUT, "robustness_windows.csv"), index=False)

    # ------- Step 4c 四时段 -------
    periods = [("2010-15","2010-01-01","2015-12-31"),("2016-19","2016-01-01","2019-12-31"),
               ("2020-21","2020-01-01","2021-12-31"),("2022-26","2022-01-01","2026-12-31")]
    rows3 = []
    for name, a, b in periods:
        sub = evm[(evm["date"]>=a)&(evm["date"]<=b)]
        for dr in ("up","down"):
            s2 = sub[sub["dir"]==dr]
            if s2["choppy"].nunique() < 2 or len(s2) < 50:
                rows3.append(dict(period=name, dir=dr, n=len(s2), diff=np.nan, lo=np.nan, hi=np.nan, p=np.nan))
                continue
            obs, lo, hi = rate_diff_ci(s2, 1.0, n_boot=1000)
            ft = fisher_test(s2, 1.0)
            rows3.append(dict(period=name, dir=dr, n=len(s2), diff=obs, lo=lo, hi=hi, p=ft["p"]))
    pdf = pd.DataFrame(rows3)
    pdf["p_bh"] = bh_adjust(pdf["p"].fillna(1).values)
    pdf.to_csv(os.path.join(OUT, "robustness_periods.csv"), index=False)
    print(pdf.to_string(index=False))

    # ------- Step 5 控制回归 -------
    # 特征：震荡 + 突破幅度(×ATR) + 量能比 + beta + 板块固定效应
    # 市值代理：无本地数据 → 用量能比与 beta；市值缺失在报告中如实标注
    ev2 = evm.copy()
    # beta(250d, 截至突破日前一日, 防泄漏)：对每只股票滚动
    betas = {}
    for t, g in ev2.groupby("ticker"):
        df = load_ohlc(t)
        df = df[df["date"] >= pd.Timestamp(cfg["start_date"])].reset_index(drop=True)
        r_s = df["adj_close"].pct_change()
        spy_r = spy.set_index("date")["adj_close"].pct_change()
        mr = spy_r.reindex(df["date"]).values
        sr = r_s.values
        cov = pd.Series(sr*mr).rolling(cfg["beta_len"], min_periods=200).mean().shift(1)
        var = pd.Series(mr**2).rolling(cfg["beta_len"], min_periods=200).mean().shift(1)
        b = (cov/var).values
        # zip(g["idx"], b) 错位 bug：b 是全日线数组长度，g["idx"] 是截断后行号。
        # g 是 evm 全体该 ticker 的行（升序 idx），逐事件取 b[idx]：
        b_idx = np.asarray(g["idx"].values)
        for i in b_idx:
            bi = b[i] if i < len(b) else np.nan
            betas[(t, i)] = bi if np.isfinite(bi) else np.nan
    ev2["beta"] = [betas.get((t, i), np.nan) for t, i in zip(ev2["ticker"], ev2["idx"])]
    # 量能比：突破日 volume / 20日均量（量能比用 ≤当日，当日成交量含突破日 —— 突破日量能是当日收盘后已知，允许）
    volrat = {}
    for t, g in ev2.groupby("ticker"):
        df = load_ohlc(t)
        df = df[df["date"] >= pd.Timestamp(cfg["start_date"])].reset_index(drop=True)
        vr = (df["volume"] / df["volume"].rolling(20).mean().shift(1)).values
        for i in g["idx"]:
            volrat[(t, i)] = vr[i] if i < len(vr) and np.isfinite(vr[i]) else np.nan
    ev2["vol_ratio"] = [volrat.get((t, i), np.nan) for t, i in zip(ev2["ticker"], ev2["idx"])]
    ev2["y"] = (ev2["dev_adr"] >= 1.0).astype(int)
    ev2["chop"] = ev2["choppy"]
    keep_cols = ["y","chop","brk_atr","vol_ratio","beta","sector","dir"]
    reg_df = ev2[keep_cols].copy()
    reg_df = reg_df.dropna(subset=["y","chop","brk_atr","vol_ratio","beta"]).reset_index()
    reg_df = pd.get_dummies(reg_df, columns=["sector"], drop_first=True)
    reg_df["dir_down"] = (reg_df["dir"]=="down").astype(int)
    reg_df = reg_df.drop(columns=["dir"])
    import statsmodels.api as sm
    X = sm.add_constant(reg_df.drop(columns=["y","index"]).astype(float))
    y_ = reg_df["y"].astype(float)
    grp = ev2.loc[reg_df["index"], "date"].dt.to_period("M").astype(str)
    logit = sm.Logit(y_, X).fit(cov_type="cluster", cov_kwds={"groups": grp}, disp=0)
    res = pd.DataFrame({"coef": logit.params, "OR": np.exp(logit.params),
                        "se": logit.bse, "p": logit.pvalues,
                        "ci_lo": np.exp(logit.conf_int()[0]), "ci_hi": np.exp(logit.conf_int()[1])})
    res.to_csv(os.path.join(OUT, "regression.csv"))
    print(res.round(4).to_string())

    # ------- 前视自检：数据截断到 2019-12-31 重跑，2010-2018 事件应逐位一致 -------
    ch2 = choppy_detector(spy[spy["date"] <= "2019-12-31"].reset_index(drop=True))
    ev_cut = build_all_events(ch2, earn_map)
    ev_full = ev.copy()
    cut = pd.Timestamp("2018-12-31")
    a = ev_full[ev_full["date"] <= cut][["ticker","date","dir","ref","dev_adr","choppy"]].reset_index(drop=True)
    b = ev_cut[ev_cut["date"] <= cut][["ticker","date","dir","ref","dev_adr","choppy"]].reset_index(drop=True)
    # 注意 dev_adr 含 T+10 前瞻（截断点后数据不同属预期），只比 choppy/ref/dir/date 逐位
    same = a[["ticker","date","dir","ref","choppy"]].equals(b[["ticker","date","dir","ref","choppy"]])
    dev_same = np.allclose(a["dev_adr"].values[:len(b)], b["dev_adr"].values, atol=1e-9) if len(a)==len(b) else False
    leak = dict(events_full_before_cut=len(a), events_cut_before_cut=len(b),
                labels_bitwise_same=bool(same), dev_adr_same=bool(dev_same))
    json.dump(leak, open(os.path.join(OUT, "leak_check.json"),"w"), indent=1)
    print("LEAK CHECK:", leak)

if __name__ == "__main__":
    main()
