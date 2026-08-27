# -*- coding: utf-8 -*-
"""构建 45 号研报 HTML：震荡市板块独立行情回测
输出 reports/45_震荡市板块独立行情/index.html；只 print written/path size。"""
import pandas as pd, numpy as np, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
R = os.path.join(root, 'results')
import sector_wave_er as swe

meta = json.load(open(os.path.join(R, 'scan_slices.json'), encoding='utf-8'))
ret_th = meta['ret_th']
scan = pd.read_csv(os.path.join(R, 'sector_independence_scan.csv'))
slices = pd.read_csv(os.path.join(R, 'choppy_slices.csv'), parse_dates=['start', 'end'])
stats = json.load(open(os.path.join(R, 'independence_stats.json'), encoding='utf-8'))
trades = pd.read_csv(os.path.join(R, 'continuation_trades.csv'))

# ---- 本期 80 日窗口打分表（2025-11-03~2026-02-27, th=5%, 校准阈值） ----
cur = swe.label_table(swe.analyze('2025-11-03', '2026-02-27', 0.05), ret_th=ret_th)
cur = cur.sort_values('区间涨跌pct', ascending=False)

# ---- 本期 ER20 / corr60 时序 ----
w = swe.S.loc['2025-11-03':'2026-02-27']
dates = [str(d.date()) for d in w.index]
er_series = {s: [None if pd.isna(v) else round(float(v), 3) for v in swe.RE[s].loc[w.index]] for s in cur.index}
cr_series = {s: [None if pd.isna(v) else round(float(v)*100, 1)/100 for v in swe.CR[s].loc[w.index]] for s in cur.index}

# ---- 切片地图 + 每切片标签 ----
slice_rows = []
for _, sl in slices.iterrows():
    sub = scan[scan.slice_id == sl.slice_id]
    labs = {r.sector: r.标签 for r in sub.itertuples()}
    slice_rows.append(dict(id=sl.slice_id, start=str(sl.start.date()), end=str(sl.end.date()),
                           length=int(sl.length), spy=round(float(sl.spy_ret_pct), 1),
                           er=round(float(sl.spy_ER), 3), mdd=round(float(sl.spy_MDD_pct), 1),
                           hv=round(float(sl.hv20_mean), 1), ongoing=bool(sl.ongoing), labs=labs))

# ---- 倾向频次 ----
freq = pd.DataFrame(stats['倾向频次'])

# ---- 延续收益 ----
res = stats['延续收益']
def fmt(k, field):
    v = res.get(k, {}).get(field)
    return v if v is not None else '—'

cont_table = []
for lab in ('强势独立上涨', '弱势独立下跌', '跟随震荡'):
    for N in (20, 60, 120):
        k = f'{lab}_T{N}'
        d = res.get(k, {})
        if not d or d.get('n') in (None, 0):
            cont_table.append(dict(标签=lab, T=f'T+{N}', n=d.get('n', 0), mean='—', med='—', win='—', t='—', bp='—', tc='—'))
            continue
        cont_table.append(dict(标签=lab, T=f'T+{N}', n=d['n'], mean=d.get('均值'), med=d.get('中位'),
                               win=d.get('胜率'), t=d.get('t独立'), bp=d.get('二项p'), tc=d.get('t聚类')))

# 事件明细（含全部切片标签长表）
detail = scan.copy()
detail_cols = ['slice_id', 'start', 'end', 'sector', '区间涨跌pct', '标签', '稳健', '标签th3', '标签th8',
               'EP05', 'EP06', '全局ER', '上行ER', '下行ER', 'n_up', 'n_dn', 'corr60均值', 'corr60最低', 'HV20']
detail = detail[detail_cols].round(3)
detail.to_csv(os.path.join(R, '_45_detail_ready.csv'), index=False)

# SPY 本期区间校验值
spy_chg = (w['SPY'].iloc[-1]/w['SPY'].iloc[0]-1)*100

DATA = dict(
    dates=dates, er=er_series, cr=cr_series,
    cur=[dict(sector=s, ret=round(float(r['区间涨跌pct']), 2), ger=round(float(r['全局ER']), 3),
              uper=None if pd.isna(r['上行ER']) else round(float(r['上行ER']), 3),
              upmed=None if pd.isna(r['上行ER中位']) else round(float(r['上行ER中位']), 3),
              nup=int(r['n_up']), ndn=int(r['n_dn']),
              dner=None if pd.isna(r['下行ER']) else round(float(r['下行ER']), 3),
              ep05=int(r['EP05']), ep06=int(r['EP06']), er20=round(float(r['ER20最大']), 3),
              hv=round(float(r['HV20']), 1), sc=round(float(r['静态corr']), 2),
              c60=round(float(r['corr60均值']), 2), label=r['标签'],
              h80u=bool(r['hist80高up']), h80d=bool(r['hist80高dn']))
         for s, r in cur.iterrows()],
    slices=slice_rows,
    freq=freq.to_dict('records'),
    cont=cont_table,
    trades=trades.to_dict('records'),
    detail=detail.to_dict('records'),
    ret_th=ret_th, spy_chg=round(float(spy_chg), 2),
    说明=dict(主口径切片数=stats['主口径切片数'], 早期切片数=stats['早期切片数'],
             事件数=stats['事件数'], 对照数=stats['对照数']),
)

with open(os.path.join(root, 'scripts', '_45_data.json'), 'w', encoding='utf-8') as f:
    json.dump(DATA, f, ensure_ascii=False)
print('data prepared:', os.path.getsize(os.path.join(root, 'scripts', '_45_data.json')))
