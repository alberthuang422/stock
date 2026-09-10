# -*- coding: utf-8 -*-
"""
HO(取暖油/超低硫柴油) 价格水平 vs 近-次月价差 关系拆解
输入: TradingView 导出 HO1! 日线 + HO1!-HO2! 价差日线
问题: 为何 2026 年价格创新高、月差却远低于 2022 年价格前高时的月差?
"""
import pandas as pd, numpy as np, os

P1 = r"C:\Users\Administrator\Downloads\NYMEX_DL_HO1!, 1D.csv"
P2 = r"C:\Users\Administrator\Downloads\NYMEX_DL_HO1!-NYMEX_DL_HO2!, 1D.csv"

a = pd.read_csv(P1)
b = pd.read_csv(P2)
a = a[['time', 'close']].rename(columns={'close': 'ho1'})
b = b[['time', 'close']].rename(columns={'close': 'spread'})

a['time'] = pd.to_datetime(a['time'])
b['time'] = pd.to_datetime(b['time'])
df = a.merge(b, on='time', how='inner').sort_values('time').reset_index(drop=True)

print("=" * 78)
print("HO1! rows=%d  range %s -> %s" % (len(a), a.time.min().date(), a.time.max().date()))
print("SPREAD rows=%d  range %s -> %s" % (len(b), b.time.min().date(), b.time.max().date()))
print("MERGED rows=%d  %s -> %s" % (len(df), df.time.min().date(), df.time.max().date()))
print("=" * 78)

print("\n[TAIL 6]")
print(df.tail(6).to_string(index=False))

# ---------- 1. 全历史 水平 vs 月差 ----------
x, y = df.ho1.values, df.spread.values
slope, inter = np.polyfit(x, y, 1)
r = np.corrcoef(x, y)[0, 1]
yhat = slope * x + inter
r2 = r ** 2
resid = y - yhat
print("\n[1] FULL-HISTORY regression  spread = a + b*ho1")
print("   corr = %.3f   R2 = %.3f   b = %.4f $/gal per $1   a = %.4f" % (r, r2, slope, inter))
print("   spread mean = %.4f   median = %.4f   min = %.4f   max = %.4f" % (y.mean(), np.median(y), y.min(), y.max()))
print("   ho1    mean = %.3f   max = %.3f (%s)" % (x.mean(), x.max(), df.loc[df.ho1.idxmax(), 'time'].date()))

# ---------- 2. 逐年统计 ----------
df['year'] = df.time.dt.year
g = df.groupby('year').agg(
    ho1_mean=('ho1', 'mean'), ho1_max=('ho1', 'max'), ho1_min=('ho1', 'min'),
    sp_mean=('spread', 'mean'), sp_max=('spread', 'max'), sp_min=('spread', 'min'),
    n=('spread', 'size'))
# 年内月差极值日 + 当日价格
rows = []
for yr, sub in df.groupby('year'):
    imax = sub.spread.idxmax()
    rows.append({'year': yr, 'spread_peak': sub.loc[imax, 'spread'],
                 'peak_date': sub.loc[imax, 'time'].date(), 'ho1_at_spread_peak': sub.loc[imax, 'ho1'],
                 'ho1_peak': sub.ho1.max(), 'ho1_peak_date': sub.loc[sub.ho1.idxmax(), 'time'].date(),
                 'spread_at_ho1_peak': sub.loc[sub.ho1.idxmax(), 'spread']})
peak = pd.DataFrame(rows).set_index('year')
out = g.round(4).join(peak)
print("\n[2] BY-YEAR (ho1 $/gal, spread $/gal)")
print(out.to_string())

# ---------- 3. 2022 vs 2026 关键日 ----------
print("\n[3] KEY DATES")
for d in ['2022-04-28', '2022-03-07', '2022-06-09', '2026-09-09', '2026-09-10', '2026-08-01']:
    s = df[df.time == d]
    if len(s):
        rr = s.iloc[0]
        print("   %s  ho1=%.4f  spread=%.4f ($%.2f/bbl)  resid=%+.4f (%.1f sigma)" % (
            d, rr.ho1, rr.spread, rr.spread * 42, rr.spread - (slope * rr.ho1 + inter),
            (rr.spread - (slope * rr.ho1 + inter)) / resid.std()))
    else:
        print("   %s  (no data)" % d)

# ---------- 4. 2022 与 2026 在相同价格区间的月差对比 ----------
print("\n[4] SAME-PRICE-BAND COMPARISON  (ho1 in [4.40, 5.20])")
band = df[(df.ho1 >= 4.40) & (df.ho1 <= 5.20)]
print("   n = %d days" % len(band))
for yr, sub in band.groupby('year'):
    print("   %d : n=%3d  ho1 mean %.3f | spread mean %.4f  median %.4f  max %.4f" % (
        yr, len(sub), sub.ho1.mean(), sub.spread.mean(), sub.spread.median(), sub.spread.max()))

# ---------- 5. 最新分位与曲线形状 ----------
last = df.iloc[-1]
pct_sp = (df.spread <= last.spread).mean()
pct_ho = (df.ho1 <= last.ho1).mean()
print("\n[5] LATEST %s  ho1=%.4f (pct %.1f%%)  spread=%.4f (pct %.1f%%)" % (
    last.time.date(), last.ho1, pct_ho * 100, last.spread, pct_sp * 100))
print("   next month implied = %.4f   HO2/HO1 = %.3f" % (last.ho1 - last.spread, (last.ho1 - last.spread) / last.ho1))

d22 = df[df.time == '2022-04-28']
if len(d22):
    p22 = d22.iloc[0]
    print("   2022-04-28  ho1=%.4f  spread=%.4f  HO2/HO1=%.3f ($%.1f/bbl spread)" % (
        p22.ho1, p22.spread, (p22.ho1 - p22.spread) / p22.ho1, p22.spread * 42))

# ---------- 6. 月差历史 Top20 ----------
print("\n[6] TOP 20 SPREAD DAYS")
print(df.nlargest(20, 'spread')[
    ['time', 'ho1', 'spread']].assign(bbl=lambda t: (t.spread * 42).round(2)).to_string(index=False))

# ---------- 7. 导出散点/时间序列供绘图 ----------
os.makedirs(r"C:\Users\Administrator\Desktop\stock\Temp", exist_ok=True)
df[['time', 'ho1', 'spread']].to_csv(
    r"C:\Users\Administrator\Desktop\stock\Temp\ho_price_spread_merged.csv", index=False)
print("\n[saved] Temp/ho_price_spread_merged.csv")
