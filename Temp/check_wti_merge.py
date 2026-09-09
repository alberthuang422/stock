# -*- coding: utf-8 -*-
import csv

old = {}
with open('data/wti.csv', newline='') as f:
    for r in csv.DictReader(f):
        old[r['observation_date']] = r['DCOILWTICO']
new = {}
with open('Temp/fred_wti_full.csv', newline='') as f:
    for r in csv.DictReader(f):
        if r.get('DCOILWTICO'):
            new[r['observation_date']] = r['DCOILWTICO']
overlap = sorted(set(old) & set(new))
mism = [d for d in overlap if old[d] != new[d]]
print('old=%d new=%d overlap=%d mismatch=%d' % (len(old), len(new), len(overlap), len(mism)))
if mism[:5]:
    print('mismatch examples:', mism[:5], old[mism[0]], new[mism[0]])
extra = sorted(set(new) - set(old))
print('new rows to append:', len(extra))
for d in extra[-8:]:
    print(d, new[d])
# 检查本地旧数据最后日期
print('old last date:', sorted(old)[-1], old[sorted(old)[-1]])