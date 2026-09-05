# -*- coding: utf-8 -*-
"""生成小麦 COT 周间变化事件表 CSV（供回测使用）"""
import json,csv,os
d=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'wheat_3c_1995.json')))
s=d['series']; ds=sorted(s)
rows=[]
for i in range(1,len(ds)):
    p,w=s[ds[i-1]],s[ds[i]]
    rows.append(dict(date=ds[i],prev=ds[i-1],
        L=w[0],S=w[1],OI=w[2],net=w[0]-w[1],
        dL=w[0]-p[0],dS=w[1]-p[1],dNet=(w[0]-w[1])-(p[0]-p[1]),dOI=w[2]-p[2],
        dLpct=(w[0]-p[0])/p[2]*100,net_prev=p[0]-p[1]))
with open('wheat_events.csv','w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
print('events',len(rows),'range',rows[0]['date'],'->',rows[-1]['date'])
# 阈值预览
import collections
for thr in [10000,15000,20000,25000,30000]:
    n=sum(1 for r in rows if r['dL']>=thr)
    print(f'dL>=+{thr:,}: n={n}')
