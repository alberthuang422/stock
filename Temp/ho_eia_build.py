# -*- coding: utf-8 -*-
"""把用户 EIA WPSR psw0x.xls 抽成周度面板, 并与 HO 价格/月差合并."""
import pandas as pd, numpy as np, glob, os, json

D = r'C:/Users/Administrator/Desktop/eia/eia数据'
OUT = r'C:/Users/Administrator/Desktop/stock/Temp'

def load(fn, sheet):
    x = pd.read_excel(os.path.join(D, fn), sheet_name=sheet, header=None)
    keys = x.iloc[1].tolist()
    names = x.iloc[2].tolist()
    body = x.iloc[3:].copy()
    body = body[body[0].notna()]
    df = pd.DataFrame({'date': pd.to_datetime(body[0])})
    for j in range(1, len(keys)):
        k = keys[j]
        if not isinstance(k, str):
            continue
        df[k] = pd.to_numeric(body[j], errors='coerce')
    return df.reset_index(drop=True)

d1 = load('psw01.xls', 'Data 1')   # stocks
d2 = load('psw01.xls', 'Data 2')   # supply
d6 = load('psw06.xls', 'Data 1')   # distillate by PADD

# --- 选取列 ---
s1 = d1[['date', 'WCRSTUS1', 'WCESTUS1', 'WCSSTUS1', 'WGTSTUS1',
         'WKJSTUS1', 'WDISTUS1', 'WD0ST_NUS_1', 'WD1ST_NUS_1', 'WDGSTUS1',
         'WRESTUS1', 'WPRSTUS1', 'WTTSTUS1', 'WTESTUS1']].copy()
s1.columns = ['date', 'crude_total', 'crude_exspr', 'crude_spr', 'gasoline',
              'jet', 'dist_total', 'dist_ulsd', 'dist_ls500', 'dist_hs',
              'residual', 'propane', 'total_stocks', 'total_exspr']

s2 = d2[['date', 'WCRFPUS2', 'WCRNTUS2', 'WCRIMUS2', 'WCREXUS2', 'WCRRIUS2',
         'WRPIMUS2', 'WRPEXUS2', 'WDIUPUS2', 'WDISTUS1' if 'WDISTUS1' in d2.columns else 'WCRFPUS2',
         'WGFUPUS2', 'W_EPP1_YPT_NUS_MBBLD']].copy()
s2.columns = ['date', 'crude_prod', 'crude_netimp', 'crude_imp', 'crude_exp', 'refinery_input',
              'prod_imp', 'prod_exp', 'dist_supplied', 'x1', 'gas_supplied', 'prod_total']

s6 = d6[['date', 'WDISTUS1', 'WDISTP11', 'WDIST1A1', 'WDIST1B1', 'WDIST1C1',
         'WDISTP21', 'WDISTP31', 'WDISTP41', 'WDISTP51',
         'WD0ST_NUS_1', 'WD0ST_R10_1', 'WD1ST_NUS_1', 'WD1ST_R10_1']].copy()
s6.columns = ['date', 'dist_us', 'dist_p1', 'dist_p1a', 'dist_p1b', 'dist_p1c',
              'dist_p2', 'dist_p3', 'dist_p4', 'dist_p5',
              'ulsd_us', 'ulsd_p1', 'ls500_us', 'ls500_p1']

for f in (s1, s2, s6):
    f.set_index('date', inplace=True)
s2.drop(columns=['x1'], inplace=True)

w = s1.join(s2, how='outer').join(s6[['dist_p1', 'dist_p1a', 'dist_p1b', 'dist_p1c', 'dist_p2', 'dist_p3', 'dist_p4', 'dist_p5',
                                       'ulsd_p1', 'ls500_p1', 'ulsd_us', 'ls500_us']], how='outer')
w = w.sort_index()
w.to_csv(os.path.join(OUT, 'eia_wpsr_weekly.csv'))

print('=== WPSR 面板 ===')
print('范围 %s ~ %s, n=%d' % (w.index[0].date(), w.index[-1].date(), len(w)))
print()
cols = ['dist_total', 'dist_ulsd', 'dist_ls500', 'dist_hs', 'crude_exspr', 'gasoline', 'jet', 'dist_supplied']
print('=== 最新 8 周 ===')
print(w.tail(8)[cols].round(0).to_string())
print()
print('=== 2026 年内关键周 ===')
print(w.loc['2026-01-01':][cols].round(0).to_string())
