#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""板块中期选举波动率 —— matplotlib 图表（3 张 PNG → reports/38_板块中期选举波动率/）"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "STHeiti"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.facecolor"] = "white"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "reports", "38_板块中期选举波动率")
STATS = os.path.join(ROOT, "results", "sector_midterm_vol_stats.json")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]
os.makedirs(OUT_DIR, exist_ok=True)
d = json.load(open(STATS, encoding="utf-8"))
SECTORS = d["meta"]["sectors"]
FULL = set(d["meta"]["full_history_sectors"])


def fig1_ranking():
    """板块 v20 平均放大排序（含 SPY 参考线与命中率）。"""
    rank = d["ranking"]
    syms = [r["symbol"] for r in rank]
    names = [f"{s}\n({SECTORS[s]})" for s in syms]
    vals = [r["v20_mean"] for r in rank]
    hits = [r["hit_p20"] for r in rank]
    colors = ["#c0392b" if s in FULL else "#e67e22" for s in syms]
    fig, ax = plt.subplots(figsize=(11, 5.8))
    bars = ax.bar(range(len(syms)), vals, color=colors, alpha=0.9)
    spy = d["spy"]["v20_midterm_mean"]
    ax.axhline(spy, color="#333", lw=1.6, ls="--")
    ax.text(len(syms) - 0.5, spy + 1.2, f"SPY 全市场 = +{spy}%", fontsize=10, ha="right", color="#333")
    for i, (v, h) in enumerate(zip(vals, hits)):
        ax.text(i, v + 1.5, f"+{v:.0f}%\n(≥+20% 命中 {int(h)}%)", ha="center", fontsize=9)
    ax.set_xticks(range(len(syms)))
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("选举前 20 个交易日平均波动放大（%，vs 基准）")
    ax.set_title("各板块受中期选举波动冲击排序（2000 年以来 6 次中期选举）")
    ax.grid(axis="y", alpha=0.25)
    ax.set_ylim(0, max(vals) * 1.35)
    fig.tight_layout()
    plt.show()
    fig.savefig(os.path.join(OUT_DIR, "sector_v20_ranking.png"), dpi=150)
    plt.close(fig)


def fig2_heatmap():
    """板块 × 窗口 放大% 热力图。"""
    syms = [r["symbol"] for r in d["ranking"]]
    mat = np.array([[d["sectors"][s][f"v{k}"]["mean"] for k in WINDOWS] for s in syms])
    fig, ax = plt.subplots(figsize=(11, 6.2))
    im = ax.imshow(mat, cmap="Reds", aspect="auto", vmin=-10, vmax=50)
    ax.set_xticks(range(len(WINDOWS)))
    ax.set_xticklabels([f"前{k}日" for k in WINDOWS])
    ax.set_yticks(range(len(syms)))
    ax.set_yticklabels([f"{s} ({SECTORS[s]})" for s in syms])
    for i in range(len(syms)):
        for j in range(len(WINDOWS)):
            v = mat[i, j]
            ax.text(j, i, f"{v:+.0f}", ha="center", va="center", fontsize=9,
                    color="white" if v > 30 else "#333")
    ax.set_title("板块 × 前置窗口 平均波动放大%（中期选举事件平均）")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("放大 %")
    fig.tight_layout()
    plt.show()
    fig.savefig(os.path.join(OUT_DIR, "sector_windows_heatmap.png"), dpi=150)
    plt.close(fig)


def fig3_curves():
    """代表板块逐日放大曲线：最大(XLB) vs SPY vs 最小(XLV/XLC)。"""
    picks = ["XLB", "XLU", "SPY", "XLV"]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    styles = {"XLB": ("#c0392b", 2.4), "XLU": ("#e67e22", 2.0), "SPY": ("#333333", 1.8), "XLV": ("#7f8c8d", 2.0)}
    for sym in picks:
        if sym == "SPY":
            spy_curve = json.load(open(os.path.join(ROOT, "results", "midterm_vol_group_stats.json"), encoding="utf-8"))
            c = spy_curve["groups"]["midterm"]["avg_curve"]
            t = sorted((int(k) for k in c), reverse=True)
            v = [c[str(k)] for k in t]
            ax.plot(t, v, label="SPY 全市场", color="#333333", lw=1.8)
            continue
        c = d["sectors"][sym]["avg_curve"]
        t = sorted((int(k) for k in c), reverse=True)
        v = [c[str(k)] for k in t]
        ax.plot(t, v, label=f"{sym} {SECTORS[sym]}", color=styles[sym][0], lw=styles[sym][1])
    ax.axhline(1.0, color="#999", lw=1, ls="--")
    ax.axhline(1.2, color="#c0392b", lw=1, ls=":")
    ax.text(-89, 1.21, "×1.2", fontsize=9, color="#c0392b")
    ax.invert_xaxis()
    ax.set_xlabel("距选举日交易日数（0 = 选举日）")
    ax.set_ylabel("当日 10 日滚动波动率 ÷ 基准")
    ax.set_title("中期选举前波动放大曲线：材料/公用事业 vs 全市场 vs 医疗")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    plt.show()
    fig.savefig(os.path.join(OUT_DIR, "sector_curves.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig1_ranking()
    fig2_heatmap()
    fig3_curves()
    print("written: 3 PNG ->", OUT_DIR)
