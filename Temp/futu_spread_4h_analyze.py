# -*- coding: utf-8 -*-
"""核实 4h 层面 OCT-NOV / NOV-DEC 的突破与强弱"""
import json, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\Administrator\Desktop\stock"
d = json.load(open(BASE + r"\results\futu_spread_4h_raw.json", encoding="utf-8"))
A = d["legs"]["US.CL2610"]; B = d["legs"]["US.CL2611"]; C = d["legs"]["US.CL2612"]
tk = [x["time_key"] for x in A]
n = len(A)

def T(i):
    return dt.datetime.fromtimestamp(tk[i] / 1000 + 8 * 3600, dt.UTC).strftime("%m-%d %H:%M")

def D(i):
    return dt.datetime.fromtimestamp(tk[i] / 1000 + 8 * 3600, dt.UTC).strftime("%m-%d")

p = {"OCT": A, "NOV": B, "DEC": C}
sp = {"OCT-NOV": [A[i]["close"] - B[i]["close"] for i in range(n)],
      "NOV-DEC": [B[i]["close"] - C[i]["close"] for i in range(n)]}

# 找 08-25 起点
start = next(i for i in range(n) if D(i) >= "08-25")
print(f"数据覆盖 {T(0)} ~ {T(n-1)}，共 {n} 根 4h\n")

print("=== 8/25 以来 4h 收盘序列（每 4 根取样 + 关键日逐根）===")
print(f"{'time':<13}{'OCT':>8}{'NOV':>8}{'DEC':>8}{'10-11':>8}{'11-12':>8}")
for i in range(start, n):
    if D(i) in ("08-26", "09-03", "09-08", "09-09", "09-10") or i % 4 == 0:
        print(f"{T(i):<13}{A[i]['close']:>8.2f}{B[i]['close']:>8.2f}{C[i]['close']:>8.2f}"
              f"{sp['OCT-NOV'][i]:>8.2f}{sp['NOV-DEC'][i]:>8.2f}")

print("\n=== 多窗口涨幅对比 ===")
def idx_of(day, hh="02:00"):
    for i in range(n - 1, -1, -1):
        if D(i) == day:
            return i
    return None

last = n - 1
for lbl, sday in [("08-26 起", "08-26"), ("08-31 起", "08-31"), ("09-03 起", "09-03"), ("09-08 起", "09-08")]:
    i0 = idx_of(sday)
    if i0 is None:
        continue
    print(f"\n[{lbl}] {T(i0)} → {T(last)}")
    print(f"{'':10}{'起点':>9}{'终点':>9}{'Δ':>8}{'%':>8}")
    for k, arr in p.items():
        a, b = arr[i0]["close"], arr[last]["close"]
        print(f"  {k:<8}{a:>9.2f}{b:>9.2f}{b-a:>+8.2f}{(b/a-1)*100:>+7.2f}%")
    for k, arr in sp.items():
        a, b = arr[i0], arr[last]
        print(f"  {k:<8}{a:>9.2f}{b:>9.2f}{b-a:>+8.2f}{(b/a-1)*100:>+7.2f}%")

print("\n=== 盘整区间与突破判定 ===")
# 09-03 ~ 09-07 区间
pl_start = idx_of("09-03")
pl_end = max(i for i in range(n) if D(i) == "09-07")
after = [i for i in range(n) if D(i) >= "09-08"]
for k, arr in sp.items():
    seg = arr[pl_start:pl_end + 1]
    hi, lo = max(seg), min(seg)
    hi_i = pl_start + seg.index(hi)
    seg0303 = [arr[i] for i in range(n) if D(i) == "09-03"]
    print(f"\n  【{k}】")
    print(f"    09-03~09-07 盘整区: {lo:.2f} ~ {hi:.2f} (高点在 {T(hi_i)})")
    print(f"    09-03 当日区间: {min(seg0303):.2f} ~ {max(seg0303):.2f}  高点 {max(seg0303):.2f}")
    mx_after = max(arr[i] for i in after)
    mx_i = [i for i in after if arr[i] == mx_after][0]
    print(f"    09-08 之后最高: {mx_after:.2f} @ {T(mx_i)}")
    print(f"    → 突破 09-07 盘整上沿({hi:.2f})? {'✅ 是' if mx_after > hi else '❌ 否'}  (超出 {mx_after-hi:+.2f})")
    print(f"    → 突破 09-03 当日高点({max(seg0303):.2f})? {'✅ 是' if mx_after > max(seg0303) else '❌ 否'}  (超出 {mx_after-max(seg0303):+.2f})")
    # 首次突破时间
    brk = next((i for i in after if arr[i] > hi), None)
    print(f"    → 首次突破盘整上沿时间: {T(brk) if brk else '未突破'}")

print("\n=== 相对强度：谁在接棒 ===")
print(f"{'窗口':<12}{'OCT':>9}{'NOV':>9}{'DEC':>9}   最强腿")
for lbl, sday in [("08-26起", "08-26"), ("09-03起", "09-03"), ("09-08起", "09-08"), ("09-09起", "09-09")]:
    i0 = idx_of(sday)
    gains = {k: (p[k][last]["close"] / p[k][i0]["close"] - 1) * 100 for k in p}
    best = max(gains, key=gains.get)
    print(f"{lbl:<12}{gains['OCT']:>+8.2f}%{gains['NOV']:>+8.2f}%{gains['DEC']:>+8.2f}%   {best}")
