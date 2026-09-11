# -*- coding: utf-8 -*-
"""
CL 曲线「做空月差」候选组合评估
=================================
做空月差 = 空近月 / 多远月，盈亏 = -(P_near - P_far) 的变动 * 1000 桶/手
本脚本对 13 腿（CL2610~CL2710）的全部 78 个可交易腿对做多维度打分：
  1) 流动性与到期约束（两腿的最小 OI / 20 日均量 / 剩余到期日）
  2) 当前水平的分位（129 日样本）
  3) 波动（日变动的标准差，$ 与占名义 %）
  4) 均值回归空间（回到样本中位 / 样本最低的潜在收益）
  5) 趋势对抗度（近 20/60 日该价差自身的变化方向）
输出 results/cl_spread_short_candidates.json
"""
import os, json, math
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LEGS = ["CL2610", "CL2611", "CL2612", "CL2701", "CL2702", "CL2703",
        "CL2704", "CL2705", "CL2706", "CL2707", "CL2708", "CL2709", "CL2710"]
NAME = {L: n for L, n in zip(LEGS,
        ["OCT26", "NOV26", "DEC26", "JAN27", "FEB27", "MAR27", "APR27",
         "MAY27", "JUN27", "JUL27", "AUG27", "SEP27", "OCT27"])}
M = {L: f"M{i+1}" for i, L in enumerate(LEGS)}          # 位置标签
EXP = {  # 最后交易日（ET）
    "CL2610": "2026-09-22", "CL2611": "2026-10-20", "CL2612": "2026-11-20",
    "CL2701": "2026-12-21", "CL2702": "2027-01-20", "CL2703": "2027-02-22",
    "CL2704": "2027-03-22", "CL2705": "2027-04-20", "CL2706": "2027-05-20",
    "CL2707": "2027-06-22", "CL2708": "2027-07-20", "CL2709": "2027-08-20",
    "CL2710": "2027-09-21",
}
LAST = pd.Timestamp("2026-09-11")

# ---------- 1. 读取 13 腿价格 / OI / 成交 ----------
px, oi, vol = {}, {}, {}
for L in LEGS:
    d = pd.read_csv(f"data/cl_contracts/daily/US.{L}.csv")
    d["date"] = pd.to_datetime(d["date"])
    d = d.set_index("date").sort_index()
    px[L], oi[L], vol[L] = d["close"], d["open_interest"], d["volume"]
P = pd.DataFrame(px)          # 收盘
O = pd.DataFrame(oi)
V = pd.DataFrame(vol)

legs_info = []
for L in LEGS:
    e = pd.Timestamp(EXP[L])
    legs_info.append(dict(
        leg=L, name=NAME[L], pos=M[L], expiry=EXP[L],
        days_to_exp=(e - LAST).days,
        close=round(float(P[L].iloc[-1]), 2),
        oi=int(O[L].iloc[-1]),
        oi_chg_0805_pct=round(float(O[L].iloc[-1] / O[L].loc["2026-08-05"] - 1) * 100, 1),
        vol20=int(V[L].tail(20).mean()),
    ))

# ---------- 2. 全部腿对 ----------
rows = []
for i in range(len(LEGS)):
    for j in range(i + 1, len(LEGS)):
        a, b = LEGS[i], LEGS[j]          # a=近腿, b=远腿
        s = (P[a] - P[b]).dropna()       # 月差（多头月差口径，backwardation 下 >0）
        cur = float(s.iloc[-1])
        pct = float((s <= cur).mean() * 100)
        chg = s.diff().dropna()
        sd = float(chg.std())
        chg20 = float(s.iloc[-1] - s.iloc[-21]) if len(s) > 21 else np.nan
        chg60 = float(s.iloc[-1] - s.iloc[-61]) if len(s) > 61 else np.nan
        # 均值回归空间（做空方向：价差下跌）
        room_med = cur - float(s.median())
        room_min = cur - float(s.min())
        # 名义：1 手 = 1000 桶
        rows.append(dict(
            near=a, far=b, near_pos=M[a], far_pos=M[b],
            label=f"{M[a]}-{M[b]} ({NAME[a]}/{NAME[b]})",
            span=j - i,
            cur=round(cur, 2), pct=round(pct, 1),
            hist_min=round(float(s.min()), 2), hist_max=round(float(s.max()), 2),
            hist_med=round(float(s.median()), 2),
            room_to_med_usd=round(room_med, 2),
            room_to_min_usd=round(room_min, 2),
            sd_daily=round(sd, 3),
            sd_pct_of_cur=round(sd / cur * 100, 2) if cur else np.nan,
            chg20=round(chg20, 2), chg60=round(chg60, 2),
            liq_oi=int(min(O[a].iloc[-1], O[b].iloc[-1])),
            liq_vol20=int(min(V[a].tail(20).mean(), V[b].tail(20).mean())),
            near_days_to_exp=(pd.Timestamp(EXP[a]) - LAST).days,
            far_days_to_exp=(pd.Timestamp(EXP[b]) - LAST).days,
            # 风险调整：回归到中位所需"日波动倍数"
            z_to_med=round(room_med / sd, 1) if sd else np.nan,
        ))
R = pd.DataFrame(rows)

# ---------- 2b. 静态曲线日 roll（做空月差的持有成本） ----------
# 曲线形状不变时：近腿沿曲线向上收敛比远腿快 → 价差自然走阔 → 做空方支付 roll。
TAU = np.array([(pd.Timestamp(EXP[L]) - LAST).days / 365 for L in LEGS])
LP = np.log(P.iloc[-1].values.astype(float))
_s0 = (LP[1] - LP[0]) / (TAU[1] - TAU[0])


def _g(t):
    if t <= TAU[0]:
        return LP[0] + _s0 * (t - TAU[0])      # 前腿外推
    return float(np.interp(t, TAU, LP))


def short_roll(a, b):
    """曲线静止时，做空 a-b 一手每日 $ 收益（正=顺风，backwardation 下应为负）"""
    i, j = LEGS.index(a), LEGS.index(b)
    pa, pb = float(P[a].iloc[-1]), float(P[b].iloc[-1])
    na, nb = math.exp(_g(TAU[i] - 1 / 365)), math.exp(_g(TAU[j] - 1 / 365))
    return -((na - nb) - (pa - pb))


R["roll_short_daily"] = [round(short_roll(a, b), 4) for a, b in zip(R.near, R.far)]
R["carry_pct_daily"] = (R.roll_short_daily / R.cur * 100).round(3)
R["roll_to_exp_usd"] = (R.roll_short_daily * R.near_days_to_exp).round(2)

# 做空性价比：回归到中位的空间 ÷ 每日 roll 成本（越大越抗 carry）
R["room_over_carry_days"] = (R.room_to_med_usd / R.roll_short_daily.abs()).round(0)

# ---------- 3. 输出 ----------
def show(df, title, n=None):
    print("\n" + "=" * 120)
    print(title)
    print("=" * 120)
    dd = df if n is None else df.head(n)
    print(f"{'组合':<26}{'span':>5}{'现值':>8}{'分位%':>7}{'min':>7}{'max':>7}{'中位':>7}"
          f"{'回中位$':>9}{'回最低$':>9}{'日sd':>7}{'sd/现%':>8}{'z':>6}"
          f"{'Δ20':>7}{'Δ60':>7}{'OI(min)':>9}{'vol20':>8}{'近腿到期':>9}")
    for _, r in dd.iterrows():
        print(f"{r['label']:<26}{r['span']:>5}{r['cur']:>8.2f}{r['pct']:>7.1f}{r['hist_min']:>7.2f}"
              f"{r['hist_max']:>7.2f}{r['hist_med']:>7.2f}{r['room_to_med_usd']:>9.2f}{r['room_to_min_usd']:>9.2f}"
              f"{r['sd_daily']:>7.2f}{r['sd_pct_of_cur']:>8.2f}{r['z_to_med']:>6.1f}"
              f"{r['chg20']:>7.2f}{r['chg60']:>7.2f}{r['liq_oi']:>9,}{r['liq_vol20']:>8,}{r['near_days_to_exp']:>9}")

print("\n### 腿流动性 / 到期")
print(f"{'腿':<8}{'位置':<6}{'到期':<12}{'剩余天':>7}{'收盘':>8}{'OI':>10}{'OI自8/5':>9}{'vol20':>9}")
for x in legs_info:
    print(f"{x['leg']:<8}{x['pos']:<6}{x['expiry']:<12}{x['days_to_exp']:>7}{x['close']:>8.2f}"
          f"{x['oi']:>10,}{x['oi_chg_0805_pct']:>8.1f}%{x['vol20']:>9,}")

show(R.sort_values("cur", ascending=False), "A. 全部 78 个腿对（按现值降序，前 25）", 25)
show(R[R.span == 1].sort_values("cur", ascending=False), "B. 相邻 +1 段（12 段）")
show(R[R.span == 2], "C. +2 段（跨一腿，11 段）")
show(R[(R.span >= 4) & (R.span <= 7)], "D. 跨 4~7 腿的中长跨度")
show(R.sort_values("pct", ascending=False).head(20), "E. 分位最高的 20 个（最'拉伸'）")
show(R[(R.liq_oi >= 40000) & (R.liq_vol20 >= 8000)].sort_values("pct", ascending=False).head(20),
     "F. 流动性达标（两腿 OI≥4万 且 20日均量≥8千）+ 分位最高 20 个")

# ---------- 4. 关键候选的相关性与近 20 日路径 ----------
print("\n" + "=" * 120)
print("G. 候选组合近 15 个交易日路径（现值排序前 8 + 相邻段）")
print("=" * 120)
pick = list(R.sort_values("cur", ascending=False).head(8).index) + list(R[R.span == 1].sort_values("cur", ascending=False).index)
pick = list(dict.fromkeys(pick))
sub = R.loc[pick]
print(f"{'组合':<26}" + "".join(f"{str(d)[5:]:>7}" for d in P.index[-15:]))
for _, r in sub.iterrows():
    s = (P[r.near] - P[r.far]).dropna().iloc[-15:]
    print(f"{r['label']:<26}" + "".join(f"{v:>7.2f}" for v in s.values))

# ---------- 6. 做空 carry 一览（可交易候选） ----------
CAND = [("M2-M3", "CL2611", "CL2612"), ("M3-M4", "CL2612", "CL2701"),
        ("M1-M2", "CL2610", "CL2611"), ("M4-M6", "CL2701", "CL2703"),
        ("M2-M6", "CL2611", "CL2703"), ("M4-M9", "CL2701", "CL2706"),
        ("M2-M9", "CL2611", "CL2706"), ("M1-M13", "CL2610", "CL2710")]
print("\n" + "=" * 120)
print("H. 做空 carry（静态曲线口径）：每日 roll 成本 & 与波动/回归空间的关系")
print("=" * 120)
print(f"{'组合':<8}{'现值':>7}{'日roll$':>9}{'占现值%/日':>11}{'日sd$':>8}{'roll/sd':>8}"
      f"{'回归中位$':>10}{'空间/日roll(天)':>15}{'近腿到期天':>10}")
carry_rows = []
for lab, a, b in CAND:
    rr = R[(R.near == a) & (R.far == b)].iloc[0]
    carry_rows.append(dict(label=lab, near=a, far=b, cur=rr.cur,
                           roll_daily=rr.roll_short_daily, carry_pct=rr.carry_pct_daily,
                           sd=rr.sd_daily, room_med=rr.room_to_med_usd,
                           days_to_exp=rr.near_days_to_exp,
                           room_over_carry_days=rr.room_over_carry_days))
    print(f"{lab:<8}{rr.cur:>7.2f}{rr.roll_short_daily:>9.4f}{rr.carry_pct_daily:>11.3f}"
          f"{rr.sd_daily:>8.3f}{rr.roll_short_daily/rr.sd_daily:>8.3f}{rr.room_to_med_usd:>10.2f}"
          f"{rr.room_over_carry_days:>15.0f}{rr.near_days_to_exp:>10}")
print("负值 = 做空方支付 roll（backwardation 的必然结果：近腿向上收敛快于远腿 → 价差自动走阔）。")

# ---------- 7. 存储 ----------
out = dict(
    meta=dict(asof=str(P.index[-1].date()), legs=13, pairs=len(R),
              note="做空月差 = 空近腿/多远腿；cur 为近腿-远腿（backwardation 下为正）；"
                   "roll_short_daily 为静态曲线下做空一手每日 $，backwardation 下为负（做空方付 roll）"),
    legs=legs_info,
    carry_check=carry_rows,
    pairs=R.to_dict(orient="records"),
)
os.makedirs("results", exist_ok=True)
json.dump(out, open("results/cl_spread_short_candidates.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1,
          default=lambda o: float(o) if isinstance(o, (np.integer, np.floating)) else str(o))
print("\n[saved] results/cl_spread_short_candidates.json")
