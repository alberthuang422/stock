#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中期选举波动率研究 —— matplotlib 图表（3 张 PNG，输出到 reports/37_中期选举波动率/）"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "STHeiti"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.facecolor"] = "white"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "reports", "37_中期选举波动率")
STATS = os.path.join(ROOT, "results", "midterm_vol_group_stats.json")
TRADES = os.path.join(ROOT, "results", "midterm_vol_trades.csv")

WINDOWS = [5, 10, 15, 20, 30, 45, 60, 90]
GROUPS = {"midterm": "中期选举", "offyear": "奇数年(无选举)", "pres": "总统大选年"}
COLORS = {"midterm": "#c0392b", "offyear": "#7f8c8d", "pres": "#2c6fbb"}

os.makedirs(OUT_DIR, exist_ok=True)
stats = json.load(open(STATS, encoding="utf-8"))
trades = pd.read_csv(TRADES)


def fig1_curve():
    """选举前 -90~-1 交易日平均波动放大曲线（三组对比）。"""
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for g in GROUPS:
        c = stats["groups"][g]["avg_curve"]
        t = sorted((int(k) for k in c), reverse=True)     # -1..-90
        v = [c[str(k)] for k in t]
        ax.plot(t, v, label=GROUPS[g], color=COLORS[g], lw=2.2)
    ax.axhline(1.0, color="#333", lw=1, ls="--")
    ax.axhline(1.2, color="#999", lw=1, ls=":")
    ax.axhline(1.3, color="#999", lw=1, ls=":")
    ax.text(-89, 1.21, "×1.2", fontsize=9, color="#666")
    ax.text(-89, 1.31, "×1.3", fontsize=9, color="#666")
    # 标注中期选举持续抬升起点（-20）
    ax.axvspan(-20, -1, color="#c0392b", alpha=0.06)
    ax.annotate("中期选举：前 20 个交易日起持续 ≥×1.2", xy=(-20, 1.28), xytext=(-88, 1.62),
                fontsize=10, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.2))
    ax.set_xlabel("距选举日交易日数（0 = 选举日）")
    ax.set_ylabel("当日 10 日滚动波动率 ÷ 基准（基准=前 121~180 交易日均值）")
    ax.set_title("标普500（SPY）选举前波动率放大曲线 · 2000 年以来事件平均")
    ax.invert_xaxis()
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    plt.show()
    fig.savefig(os.path.join(OUT_DIR, "midterm_vol_curve.png"), dpi=150)
    plt.close(fig)


def fig2_windows():
    """各累积窗口平均放大% 对比（三组）。"""
    fig, ax = plt.subplots(figsize=(10, 5.6))
    x = np_arange = list(range(len(WINDOWS)))
    width = 0.26
    for i, g in enumerate(GROUPS):
        means = [stats["groups"][g][f"v{k}"]["mean"] for k in WINDOWS]
        ax.bar([xi + (i - 1) * width for xi in x], means, width=width,
               label=GROUPS[g], color=COLORS[g], alpha=0.9)
    ax.axhline(0, color="#333", lw=1)
    ax.axhline(20, color="#c0392b", lw=1, ls=":", alpha=0.6)
    ax.text(-0.4, 20.8, "+20%（明显放大阈值）", fontsize=9, color="#c0392b")
    ax.set_xticks(x)
    ax.set_xticklabels([f"前{k}日" for k in WINDOWS])
    ax.set_ylabel("窗口平均波动放大（%，vs 基准）")
    ax.set_title("选举前各前置窗口的波动放大幅度（2000 年以来事件平均）")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncol=3)
    fig.tight_layout()
    plt.show()
    fig.savefig(os.path.join(OUT_DIR, "midterm_vol_windows.png"), dpi=150)
    plt.close(fig)


def fig3_events():
    """6 次中期选举个体放大曲线。"""
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for _, row in trades.iterrows():
        vals = [row[f"v{k}"] for k in WINDOWS]
        ax.plot(WINDOWS, vals, marker="o", ms=4, lw=1.8, label=str(row["label"]))
    ax.axhline(0, color="#333", lw=1)
    ax.axhline(20, color="#c0392b", lw=1, ls=":", alpha=0.6)
    ax.text(1.5, 21.5, "+20%", fontsize=9, color="#c0392b")
    ax.set_xticks(WINDOWS)
    ax.set_xticklabels([f"前{k}日" for k in WINDOWS])
    ax.set_ylabel("窗口平均波动放大（%）")
    ax.set_title("6 次中期选举个体差异：放大与否取决于当年宏观环境")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, ncol=3, fontsize=9)
    fig.tight_layout()
    plt.show()
    fig.savefig(os.path.join(OUT_DIR, "midterm_vol_events.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig1_curve()
    fig2_windows()
    fig3_events()
    print("written: 3 PNG ->", OUT_DIR)
