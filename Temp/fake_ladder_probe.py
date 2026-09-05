# -*- coding: utf-8 -*-
"""
假突破严重度阶梯探针（70 号复核用）
从 choppy_breakout_backtest.py 中用 AST 抽取纯函数与常量（不执行顶层回测、无副作用），
重建 K=5/e=0.5% 主口径事件，计算每个事件 T+10 内相对突破位的最大偏离（以事件日 ADR% 归一），
输出阈值阶梯：P(max_dev >= k x ADR), k = 0(触回),0.25,...,3.0，分 震荡/趋势 x 上/下。
"""
import ast, os, csv, json
import numpy as np
import pandas as pd

ROOT = r"C:/Users/Administrator/Desktop/stock"
SRC = os.path.join(ROOT, "scripts", "choppy_breakout_backtest.py")

tree = ast.parse(open(SRC, encoding="utf-8").read())
keep = []
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
        keep.append(node)
    elif isinstance(node, ast.Assign):
        if all(isinstance(t, ast.Name) for t in node.targets) and isinstance(node.value, (ast.Constant, ast.Tuple, ast.List)):
            keep.append(node)
        elif len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            keep.append(node)
mod = ast.Module(body=keep, type_ignores=[])
ns = {"__name__": "probe_extract"}
exec(compile(mod, SRC, "exec"), ns)
ns["ROOT"] = ROOT
ns["DATA"] = os.path.join(ROOT, "data")
ns["OUT"] = os.path.join(ROOT, "results")

load_stock = ns["load_stock"]
build_spy_regime = ns["build_spy_regime"]
detect_events = ns["detect_events"]
DATA = ns["DATA"]

spy = load_stock("SPY").rename(columns={"px": "spy"})
spy_reg, spy_wins = build_spy_regime(spy)
spy_map = {np.datetime64(d, "D"): bool(c) for d, c in zip(spy_reg["date"].values, spy_reg["choppy_day"].values)}
print(f"spy choppy coverage={spy_reg['choppy_day'].mean() * 100:.1f}% windows={len(spy_wins)}")

tickers, src = [], {}
with open(os.path.join(DATA, "blue_chips.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        t = row["ticker"].strip()
        tickers.append(t); src[t] = "bluechip"
hot = json.load(open(os.path.join(ROOT, "results", "rsi14_hot_20260904.json"), encoding="utf-8"))
for h in hot[:50]:
    t = h["code"].strip()
    if t not in src:
        tickers.append(t); src[t] = "hot50"

THS = [0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0]
rows = []
for t in tickers:
    df = load_stock(t)
    if df is None or len(df) < 130:
        continue
    df = df.merge(spy_reg[["date", "spy"]], on="date", how="inner")
    if len(df) < 130:
        continue
    if src[t] == "hot50":
        df = df[df["date"] >= "2015-01-01"].reset_index(drop=True)
        if len(df) < 130:
            continue
    df["choppy"] = df["date"].map(lambda d: spy_map.get(np.datetime64(d, "D"), False))
    ret_abs = df["px"].pct_change().abs()
    jumps = set(np.where(ret_abs > 0.40)[0])
    if {"high", "low", "close"}.issubset(df.columns):
        pc = df["close"].shift(1)
        tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    else:
        tr = df["px"].diff().abs()
    df["adr_pct"] = tr.rolling(20).mean() / df["px"] * 100
    for evd in detect_events(df, 5.0, 0.005):
        ti = evd["t"]
        if any(ti - 1 <= j <= ti + 60 for j in jumps):
            continue
        adr0 = df["adr_pct"].iloc[ti]
        if np.isnan(adr0) or adr0 <= 0:
            continue
        ref = evd["ref"]
        devmax = -1e9
        for j in range(1, 11):
            if ti + j >= len(df):
                break
            c2 = df["px"].iloc[ti + j]
            dev = (ref - c2) / ref * 100 if evd["dir"] == "up" else (c2 - ref) / ref * 100
            devmax = max(devmax, dev)
        rows.append({"ticker": t, "date": str(evd["date"])[:10], "dir": evd["dir"],
                     "choppy": bool(df["choppy"].iloc[ti]), "dev_adr": devmax / adr0})

r = pd.DataFrame(rows)
out_csv = os.path.join(ROOT, "results", "fake_ladder_probe.csv")
r.to_csv(out_csv, index=False)
print(f"events={len(r)} -> {out_csv}")
for dirv in ("up", "dn"):
    for chop in (True, False):
        g = r[(r["dir"] == dirv) & (r["choppy"] == chop)]
        if not len(g):
            continue
        parts = [f"{dirv}_{'choppy' if chop else 'trend'} n={len(g)}"]
        for th in THS:
            parts.append(f">={th}xADR {(g['dev_adr'] >= th).mean() * 100:.1f}%")
        parts.append(f"med {g['dev_adr'].median():.2f}xADR")
        print(" | ".join(parts))
