# -*- coding: utf-8 -*-
"""
Step 3: 板块独立行情倾向频次 + 延续收益事件研究
（交接文档 §5 Step3；T+N 一律交易日，项目口径）

输入: results/sector_independence_scan.csv, results/scan_slices.json, results/choppy_slices.csv
输出: results/independence_stats.json（倾向频次、EP05/波段长度分布、延续收益表）
      results/continuation_trades.csv（逐事件明细，供报告"事件明细"tab）

规则:
- 倾向频次主口径 = 2010 年后非 ongoing 切片（§6.2）；2010 前单列稳健性。
- 延续收益: 切片内被标 强势独立上涨/弱势独立下跌 且 确认日偏移≥0（EP05≥5首日），
  自确认日起 T+20/T+60/T+120 交易日板块收益 − SPY 同窗收益 = 超额。
  起点=确认日收盘，终点=min(确认日+N, 数据末)。若事件后进入新趋势段则仍按固定持有期计。
- 对照: 同切片"跟随震荡"板块同起点同持有期的超额。
- 显著性: 按切片聚类（block bootstrap over slices 重抽样估计 t 与二项 p 上限），
  明示为上限（§6.1）。
"""
import pandas as pd, numpy as np, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(HERE, '..')
R = os.path.join(root, 'results')
os.makedirs(R, exist_ok=True)

scan = pd.read_csv(os.path.join(R, 'sector_independence_scan.csv'))
meta = json.load(open(os.path.join(R, 'scan_slices.json'), encoding='utf-8'))
slices = pd.read_csv(os.path.join(R, 'choppy_slices.csv'), parse_dates=['start', 'end'])

import sector_wave_er as swe
S = swe.S.dropna(subset=['SPY'])
spy = S['SPY']

def fwd_ret(series, pos, N):
    """series: pd.Series indexed; pos: 整数位置; 返回未来N交易日收益（截断容许）"""
    arr = series.values
    end = min(pos + N, len(arr)-1)
    if end <= pos: return np.nan
    return arr[end]/arr[pos]-1

# ---------- 倾向频次 ----------
IND = ('强势独立上涨', '弱势独立下跌')
scan['切片年份'] = pd.to_datetime(scan['start']).dt.year
main = scan[(scan['start'] >= '2010-01-01') & (~scan['ongoing'])]
pre = scan[(scan['start'] < '2010-01-01') & (~scan['ongoing'])]
main_slices = main.slice_id.nunique(); pre_slices = pre.slice_id.nunique()

freq = []
for s in [c for c in scan.sector.unique()]:
    m = main[main.sector == s]
    p = pre[pre.sector == s]
    n_m = m.slice_id.nunique(); n_p = p.slice_id.nunique()
    ind_m = m[m['标签'].isin(IND)]; ind_p = p[p['标签'].isin(IND)]
    freq.append(dict(
        sector=s,
        主口径切片数=n_m, 独立次数=len(ind_m), 倾向频次=round(len(ind_m)/n_m, 3) if n_m else None,
        强势次数=int((m['标签'] == '强势独立上涨').sum()),
        弱势次数=int((m['标签'] == '弱势独立下跌').sum()),
        稳健次数=int(m['稳健'].eq('稳健').sum()),
        EP05中位=round(float(ind_m.EP05.median()), 1) if len(ind_m) else None,
        区间涨跌中位=round(float(ind_m['区间涨跌pct'].median()), 1) if len(ind_m) else None,
        早期切片数=n_p, 早期独立次数=len(ind_p),
    ))
freq_df = pd.DataFrame(freq).sort_values('倾向频次', ascending=False)

# ---------- 延续收益事件 ----------
events = []
for _, r in scan.iterrows():
    if r['标签'] not in IND: continue
    sid = r['slice_id']
    sl = slices[slices.slice_id == sid].iloc[0]
    t1 = pd.Timestamp(r['start'])
    pos0 = S.index.searchsorted(t1) + int(r['确认日偏移'])
    if int(r['确认日偏移']) < 0:  # 未触发 EP05≥5
        continue
    if r['sector'] not in S.columns: continue
    ser = S[r['sector']].dropna()
    p0 = ser.index.searchsorted(S.index[pos0])
    if p0 >= len(ser): continue
    row = dict(slice_id=sid, sector=r['sector'], 标签=r['标签'], 稳健=r['稳健'],
               确认日=str(S.index[pos0].date()), 区间涨跌pct=r['区间涨跌pct'], EP05=r['EP05'])
    for N in (20, 60, 120):
        b = fwd_ret(ser, p0, N)
        a = fwd_ret(spy, pos0, N)
        row[f'T+{N}超额pp'] = round((b-a)*100, 2) if pd.notna(b) and pd.notna(a) else None
    events.append(row)

# 对照: 同切片 跟随震荡 板块同确认逻辑（无确认日者以切片中点近似？ → 直接用切片末日起算，
# 与事件组不一致。规范做法：对照组同样用 EP05≥5 首日；无触发者跳过，切片内取均值。）
ctrl = []
for _, r in scan.iterrows():
    if r['标签'] != '跟随震荡': continue
    if int(r['确认日偏移']) < 0: continue
    t1 = pd.Timestamp(r['start'])
    pos0 = S.index.searchsorted(t1) + int(r['确认日偏移'])
    ser = S[r['sector']].dropna()
    p0 = ser.index.searchsorted(S.index[pos0])
    if p0 >= len(ser): continue
    row = dict(slice_id=r['slice_id'], sector=r['sector'], 标签=r['标签'])
    for N in (20, 60, 120):
        b = fwd_ret(ser, p0, N); a = fwd_ret(spy, pos0, N)
        row[f'T+{N}超额pp'] = round((b-a)*100, 2) if pd.notna(b) and pd.notna(a) else None
    ctrl.append(row)

ev = pd.DataFrame(events); ct = pd.DataFrame(ctrl)
ev.to_csv(os.path.join(R, 'continuation_trades.csv'), index=False, encoding='utf-8-sig')

# ---------- 统计（切片聚类，显著性为上限） ----------
def stats_block(df, col):
    v = df[[col, 'slice_id']].dropna()
    if len(v) < 5:
        return dict(n=int(len(v)), 均值=None, 中位=None, 胜率=None, std=None,
                    p25=None, p75=None, t=None, 二项p=None, t聚类=None)
    x = v[col].values
    groups = [g[col].values for _, g in v.groupby('slice_id')]
    # block bootstrap over slices
    rng = np.random.default_rng(7)
    boots = []
    for _ in range(2000):
        idxs = rng.integers(0, len(groups), len(groups))
        samp = np.concatenate([groups[i] for i in idxs])
        boots.append(samp.mean())
    boots = np.array(boots)
    se = boots.std(ddof=1)
    t_cl = x.mean()/se if se > 0 else np.nan
    n = len(x)
    win = (x > 0).mean()
    t_i = x.mean()/(x.std(ddof=1)/np.sqrt(n))
    # 二项近似（正态双侧）
    import math
    z = (win-0.5)/np.sqrt(0.25/n)
    p_bin = 2*(1 - 0.5*(1+math.erf(abs(z)/np.sqrt(2))))
    return dict(n=n, 均值=round(float(x.mean()), 2), 中位=round(float(np.median(x)), 2),
                胜率=round(float(win*100), 1), std=round(float(x.std(ddof=1)), 2),
                p25=round(float(np.percentile(x, 25)), 2), p75=round(float(np.percentile(x, 75)), 2),
                t独立=round(float(t_i), 2), 二项p=round(float(p_bin), 3),
                t聚类=round(float(t_cl), 2), 聚类切片数=len(groups))

res = {}
for N in (20, 60, 120):
    col = f'T+{N}超额pp'
    for lab in IND:
        sub = ev[ev.标签 == lab] if len(ev) else pd.DataFrame(columns=[col, 'slice_id'])
        res[f'{lab}_T{N}'] = stats_block(sub, col)
    res[f'跟随震荡_T{N}'] = stats_block(ct, col) if len(ct) else dict(n=0)

out = dict(
    ret_th=meta['ret_th'], 主口径='2010年后非ongoing切片', 主口径切片数=main_slices,
    早期稳健性='2010前切片单列', 早期切片数=pre_slices,
    倾向频次=freq_df.to_dict('records'),
    延续收益=res,
    事件数=len(ev), 对照数=len(ct),
    显著性说明='t聚类=切片block bootstrap(2000次)；同切片多板块非独立，显著性为上限（§6.1）',
)
with open(os.path.join(R, 'independence_stats.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print(f'written: independence_stats.json + continuation_trades.csv  事件{len(ev)} 对照{len(ct)} 主口径切片{main_slices}')
print(freq_df.to_string(index=False))
for k, v in res.items():
    print(k, v)
