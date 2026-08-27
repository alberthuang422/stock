# -*- coding: utf-8 -*-
"""
Step 1: SPY 历史横盘震荡切片自动识别（1998 年以来）
口径（交接文档 §5 Step1）：
  逐日标记"震荡态"= 截至当日的滚动 120 交易日窗口同时满足：
    ① 窗口全局 ER < 0.15  ② 窗口累计涨跌 ∈ [-5%, +5%]  ③ 窗口最大回撤 > -12%
    ④ 20日HV均值 ≤ 全历史80分位（默认关闭 --use-hv 开启）
  合并：连续/间隔<20交易日的震荡日并为切片；边界各外扩10交易日；长度<120丢弃；
  非极大值抑制：以窗口ER最低者为优先，去重至彼此重叠<50%。
  剔除 2020-02-01~2020-12-31（疫情结构性异常）。
  数据末端不完整切片 ongoing=True（不入主统计，由下游脚本处理）。
输出: results/choppy_slices.csv
"""
import pandas as pd, numpy as np, os, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(HERE, '..')

def load_spy():
    d = os.path.join(root, 'data', 'spy')
    f = [x for x in os.listdir(d) if x.upper().startswith('SPY') and '1D' in x and not x.startswith('BATS')][0]
    return pd.read_csv(os.path.join(d, f), parse_dates=['date']).set_index('date')['adj_close'].sort_index()

def seg_er(c):
    path = np.abs(np.diff(c)).sum()
    return abs(c[-1]-c[0])/path if path > 0 else np.nan

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--er', type=float, default=0.15)
    ap.add_argument('--ret', type=float, default=0.05)
    ap.add_argument('--mdd', type=float, default=-0.12)
    ap.add_argument('--win', type=int, default=120)
    ap.add_argument('--minlen', type=int, default=120,
                    help='切片最短长度（交易日），默认120；§4.2 允许短切片配 th=3%%')
    ap.add_argument('--use-hv', action='store_true')
    ap.add_argument('--start', default='1998-01-01')
    a = ap.parse_args()

    spy = load_spy()
    spy = spy[spy.index >= a.start]
    arr = spy.values
    idx = spy.index
    n = len(arr)
    W = a.win

    hv20 = spy.pct_change().rolling(20).std()*np.sqrt(252)
    hv80 = hv20.quantile(0.80)

    # 校准说明（§5 Step1 决策规则，<10 切片故放宽）：
    # 纯120日口径下 2025-11~2026-02（已验证横盘，窗口全局ER=0.02）完全无法命中——
    # 回看120日会吸入 2025-09~10 单边大涨（cum +17~28%）。
    # 改为双口径：120日窗 或 60日窗 同时满足三条件即标"震荡态"（ER阈值对60日窗同用 a.er）。
    def day_state(i, w):
        if i < w-1: return False, np.nan
        c = arr[i-w+1:i+1]
        e = seg_er(c)
        cum = c[-1]/c[0]-1
        mdd = (c/np.maximum.accumulate(c)-1).min()
        ok = (e < a.er) and (-a.ret <= cum <= a.ret) and (mdd > a.mdd)
        return ok, e

    choppy = np.zeros(n, dtype=bool)
    er_arr = np.full(n, np.nan)
    for i in range(n):
        ok120, e120 = day_state(i, W)
        ok60, e60 = day_state(i, 60)
        if ok120: er_arr[i] = e120
        elif ok60: er_arr[i] = e60
        choppy[i] = ok120 or ok60
        if a.use_hv and choppy[i]:
            choppy[i] = hv20.iloc[i] <= hv80

    # 疫情段剔除
    mask_cov = np.asarray((idx >= '2020-02-01') & (idx <= '2020-12-31'))
    choppy[mask_cov] = False

    # 震荡日 → 原始区段（间隔<20合并）
    days = np.where(choppy)[0]
    if len(days) == 0:
        print('无震荡日'); return
    segs = []
    s0 = days[0]; prev = days[0]
    for d in days[1:]:
        if d - prev >= 20:
            segs.append((s0, prev)); s0 = d
        prev = d
    segs.append((s0, prev))

    # 外扩 ±10 交易日
    EXP = 10
    segs = [(max(0, s-EXP), min(n-1, e+EXP)) for s, e in segs]
    # 合并外扩后重叠的
    merged = [segs[0]]
    for s, e in segs[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    # 长度 < minlen 丢弃（震荡日本身需覆盖 ≥W 才有意义）
    merged = [(s, e) for s, e in merged if e-s+1 >= max(a.minlen, W)]

    # NMS：以切片内最低 er_arr 排序（ER越低越优先），贪心保留，重叠<50%（相对较短切片）
    def slice_score(se):
        vals = er_arr[se[0]:se[1]+1]
        return np.nanmin(vals)
    order = sorted(merged, key=slice_score)
    kept = []
    for se in order:
        ok = True
        for k in kept:
            ov = min(se[1], k[1]) - max(se[0], k[0]) + 1
            if ov > 0 and ov / min(se[1]-se[0]+1, k[1]-k[0]+1) >= 0.5:
                ok = False; break
        if ok: kept.append(se)

    # 裁边校验：外扩后切片整体 |累计涨跌| 可能超阈值；从两端逐日收缩直至满足或长度<minlen
    minlen = max(a.minlen, 80)
    def trim(se):
        s, e = se
        while e - s + 1 >= minlen:
            c = arr[s:e+1]
            cum = abs(c[-1]/c[0]-1)
            if cum <= a.ret + 1e-9:
                return (s, e)
            # 收缩端点中使 |cum| 更接近达标的一端
            cl = arr[s+1:e+1]; cr = arr[s:e]
            dl = abs(cl[-1]/cl[0]-1); dr = abs(cr[-1]/cr[0]-1)
            if dl <= dr: s += 1
            else: e -= 1
        return None
    kept = [t for t in (trim(se) for se in kept) if t is not None]
    kept.sort()

    rows = []
    for i, (s, e) in enumerate(kept, 1):
        c = arr[s:e+1]
        cum = c[-1]/c[0]-1
        mdd = (c/np.maximum.accumulate(c)-1).min()
        rows.append(dict(
            slice_id=f'S{i:02d}',
            start=idx[s].date(), end=idx[e].date(), length=e-s+1,
            spy_ret_pct=round(cum*100, 2),
            spy_ER=round(float(np.nanmin(er_arr[s:e+1])), 3),
            spy_MDD_pct=round(mdd*100, 2),
            hv20_mean=round(float(hv20.iloc[s:e+1].mean()*100), 1),
            ongoing=bool(n-1-e < 20),
        ))
    out = pd.DataFrame(rows)
    path = os.path.join(root, 'results', 'choppy_slices.csv')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.to_csv(path, index=False, encoding='utf-8-sig')
    print(f'saved: {path}  共 {len(out)} 个切片 (ER阈值={a.er}, 平均长度 {out.length.mean():.0f})')
    print(out.to_string(index=False))

if __name__ == '__main__':
    main()
