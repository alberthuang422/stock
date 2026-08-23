# -*- coding: utf-8 -*-
"""26 号报告：IHI×XBI 13 日滚动相关性重做（对比旧 60 日窗口版 23 号）"""
import json, math
import pandas as pd, numpy as np

BASE = r'C:/Users/Administrator/Desktop/stock'
DATA = BASE + '/data'
OUT = BASE + '/reports/26_ihi_xbi_13日滚动相关'

def load(t):
    p = f'{DATA}/{t}/{t}, 1D.csv'
    df = pd.read_csv(p, parse_dates=['date']).set_index('date')['adj_close']
    return df

def clean_np(o):
    if isinstance(o, dict): return {k: clean_np(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean_np(i) for i in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return round(float(o), 6)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, (np.ndarray, pd.Series)): return clean_np(o.tolist())
    if isinstance(o, pd.Timestamp): return o.strftime('%Y-%m-%d')
    if o is None or (isinstance(o, float) and (math.isnan(o) or math.isinf(o))): return None
    return o

ihi = load('ihi'); xbi = load('xbi')
df = pd.concat([ihi.rename('IHI'), xbi.rename('XBI')], axis=1, sort=True).dropna()
r = df.pct_change().dropna()
SPLIT = '2026-02-01'

def pear(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3: return np.nan
    return np.corrcoef(x[m], y[m])[0, 1]

def spearman(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3: return np.nan
    return pear(pd.Series(x[m]).rank().values, pd.Series(y[m]).rank().values)

# ---------- 静态口径（与 23 号一致） ----------
seg = {
    '全期': (r.index[0], r.index[-1]),
    '分界前': (r.index[0], pd.Timestamp('2026-01-31')),
    '分界后': (r.index >= pd.Timestamp(SPLIT)),
    '2025-09以来': (r.index >= pd.Timestamp('2025-09-01')),
    '2026以来': (r.index >= pd.Timestamp('2026-01-01')),
}
def seg_mask(name):
    if name == '全期': return np.ones(len(r), bool)
    if name == '分界前': return (r.index <= np.datetime64('2026-01-31'))
    if name == '分界后': return (r.index >= np.datetime64(SPLIT))
    if name == '2025-09以来': return (r.index >= np.datetime64('2025-09-01'))
    if name == '2026以来': return (r.index >= np.datetime64('2026-01-01'))

stat = {}
for name in ['全期', '分界前', '分界后', '2025-09以来', '2026以来']:
    m = seg_mask(name)
    x = r['XBI'][m].values; y = r['IHI'][m].values
    n = int(m.sum())
    pr = pear(x, y)
    sp = spearman(x, y)
    r2 = pr**2
    beta = np.cov(x, y)[0, 1] / np.var(x)
    resid = y - beta * x
    stat[name] = dict(n=n, pearson=pr, spearman=sp, r2=r2, beta=beta,
                      resid_std=float(np.nanstd(resid)))
    # Fisher z 检验 分界前 vs 分界后
    if name == '分界前':
        z_pre = 0.5 * math.log((1 + pr) / max(1 - pr, 1e-9)); n_pre = n
    if name == '分界后':
        z_post = 0.5 * math.log((1 + pr) / max(1 - pr, 1e-9)); n_post = n

fz = (z_pre - z_post) / math.sqrt(1 / max(n_pre - 3, 1) + 1 / max(n_post - 3, 1))
fz_p = 2 * (1 - 0.5 * (1 + math.erf(abs(fz) / math.sqrt(2))))

# ---------- 滚动相关：13 日 vs 60 日 ----------
roll13 = r['IHI'].rolling(13).corr(r['XBI'])
roll60 = r['IHI'].rolling(60).corr(r['XBI'])

# 关键对比指标
def roll_stats(s, name):
    d = s.dropna()
    return dict(name=name, from_d=str(d.index[0].date()), to_d=str(d.index[-1].date()),
                mean=float(d.mean()), median=float(d.median()), std=float(d.std()),
                p10=float(d.quantile(.1)), p90=float(d.quantile(.9)),
                below05=float((d < .5).mean()), neg=float((d < 0).mean()))

rs13 = roll_stats(roll13, '13日')
rs60 = roll_stats(roll60, '60日')

# 全期分组：滚动 13 日在分界前后的均值
roll13_pre = roll13.loc[:'2026-01-31'].dropna().mean()
roll13_post = roll13.loc['2026-02-01':].dropna().mean()
roll60_pre = roll60.loc[:'2026-01-31'].dropna().mean()
roll60_post = roll60.loc['2026-02-01':].dropna().mean()

# 滚动 13 日相关性落在各带的占比（2025-09 以来）
recent = roll13.loc['2025-09-01':].dropna()
bands = {
    '≥0.5 高相关': float((recent >= .5).mean()),
    '0.2~0.5 中相关': float(((recent >= .2) & (recent < .5)).mean()),
    '0~0.2 弱相关': float(((recent >= 0) & (recent < .2)).mean()),
    '<0 负相关': float((recent < 0).mean()),
}

# 月度滚动 13 均值（2025-01 起）
roll13_m = roll13.resample('ME').mean().dropna()
m_dates = [d.strftime('%Y-%m') for d in roll13_m.index]
m_vals = [round(v, 3) if np.isfinite(v) else None for v in roll13_m.values]

# 全期滚动 13 月度（用于趋势图，2015 起采样降低体积）
roll13_q = roll13.resample('QE').mean().dropna()
q_dates = [d.strftime('%Y-%m') for d in roll13_q.index]
q_vals = [round(v, 3) if np.isfinite(v) else None for v in roll13_q.values]

# 近两年（2025-01 起）日度滚动 13 曲线（13 与 60 对照）
mask_recent = roll13.index >= pd.Timestamp('2025-01-01')
d13 = roll13[mask_recent]
d60 = roll60[roll60.index >= pd.Timestamp('2025-01-01')]
rd_dates = [d.strftime('%Y-%m-%d') for d in d13.index]
rd13 = [round(v, 3) if np.isfinite(v) else None for v in d13.values]
rd60 = [round(v, 3) if np.isfinite(v) else None for v in d60.values]

# 关键月度（滚动13均值）表格
key_rows = []
for md in ['2025-08', '2025-09', '2025-10', '2025-11', '2025-12',
           '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08']:
    v = roll13_m.asof(pd.Timestamp(md + '-28')) if md in roll13_m.index else np.nan
    key_rows.append([md, round(float(v), 3) if np.isfinite(v) else None])

# ---------- 事件标注（用于解释滚动13为什么剧烈） ----------
# XBI 极端日（|日收益|>=4%）与 IHI 响应
ext = r[np.abs(r['XBI']) >= 0.04].copy()
ext_resp = []
for d0, row in ext.iterrows():
    xv = row['XBI']; iv = row['IHI']
    ext_resp.append(dict(date=str(d0.date()), xbi=round(xv, 2), ihi=round(iv, 2),
                         same=(xv * iv > 0)))
ext_resp = ext_resp[-12:]  # 最近 12 个

# 13 日窗口的采样数说明：13 日前 12 日无值，60 日前 59 日无值
out = dict(
    meta=dict(ihi_last=str(df.index[-1].date()), xbi_last=str(df.index[-1].date()),
              n=len(df), split=SPLIT),
    stat=stat, fisher_z=round(fz, 2), fisher_p=round(fz_p, 6),
    roll13=rs13, roll60=rs60,
    roll13_pre=round(float(roll13_pre), 3), roll13_post=round(float(roll13_post), 3),
    roll60_pre=round(float(roll60_pre), 3), roll60_post=round(float(roll60_post), 3),
    bands=bands,
    m_dates=m_dates, m_vals=m_vals,
    q_dates=q_dates, q_vals=q_vals,
    rd_dates=rd_dates, rd13=rd13, rd60=rd60,
    key_rows=key_rows,
    ext_resp=ext_resp,
)
with open(OUT + '/data26.json', 'w', encoding='utf-8') as f:
    json.dump(clean_np(out), f, ensure_ascii=False)
print('written:', OUT + '/data26.json')
print('静态:', {k: round(v['pearson'], 3) for k, v in stat.items()})
print('Fisher z:', round(fz, 2))
print('滚动13 均值/中位/负占比:', round(rs13['mean'], 3), round(rs13['median'], 3), round(rs13['neg'], 3))
print('滚动60 均值/中位/负占比:', round(rs60['mean'], 3), round(rs60['median'], 3), round(rs60['neg'], 3))
print('滚动13 分界前/后均值:', round(roll13_pre, 3), round(roll13_post, 3))
print('滚动60 分界前/后均值:', round(roll60_pre, 3), round(roll60_post, 3))
print('2025-09以来带分布:', {k: round(v, 3) for k, v in bands.items()})