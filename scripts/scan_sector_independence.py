# -*- coding: utf-8 -*-
"""
Step 2: 历史横盘切片 × 11板块 批量打分 + 标签阈值校准 + bootstrap 随机基线
（交接文档 §5 Step2，依赖 find_choppy_slices.py 输出与 sector_wave_er.py 修正版）

流程：
 1) 读 results/choppy_slices.csv；
 2) 第一遍以 ret_th=8% 跑全部切片 → 用全切片 |区间涨跌| 的 75 分位校准阈值，冻结；
 3) 第二遍用校准阈值 + th 分档（切片长度<120 → th=3%，否则 5%；敏感性 3/5/8 三档全跑），
    标签 + 稳健性二级标注，输出长表 results/sector_independence_scan.csv；
 4) bootstrap：500 个等长随机窗口（全历史，避开切片本身）同口径打标签，
    得"独立标签板块数"的经验分布 → 每切片经验 p 值，写 json 摘要。
另输出：results/scan_slices.json（含校准阈值、每切片元信息、确认日索引，供 Step3 用）。
"""
import pandas as pd, numpy as np, os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sector_wave_er as swe

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(HERE, '..')
R = os.path.join(root, 'results')

def th_for(length):
    return 0.03 if length < 120 else 0.05

def scan_all(slices, ret_th, ths=(0.03, 0.05, 0.08)):
    """返回长表 + 每切片主口径表"""
    long_rows = []
    main_tables = {}
    for _, sl in slices.iterrows():
        t1, t2 = str(sl.start), str(sl.end)
        primary = th_for(sl.length)
        tables = {}
        for th in ths:
            df = swe.label_table(swe.analyze(t1, t2, th), ret_th=ret_th)
            tables[th] = df
        main = tables[primary]
        # 稳健性：三档th方向一致性
        rb = swe.robustness(t1, t2, ret_th)
        # 确认日：EP05≥5 首日（切片内位置）
        w = swe.S.loc[t1:t2].dropna(subset=['SPY'])
        conf = {}
        for s in main.index:
            dates = w[s].dropna().index
            dates = dates[(dates >= pd.Timestamp(t1)) & (dates <= pd.Timestamp(t2))]
            pos = swe.first_day_ep_reaches(swe.RE[s], dates, 0.5, 5)
            conf[s] = int(pos) if pos is not None else -1
        for s in main.index:
            r = main.loc[s]
            row = dict(slice_id=sl.slice_id, start=t1, end=t2, length=int(sl.length),
                       ongoing=bool(sl.ongoing), th=primary, sector=s,
                       标签=r['标签'], 稳健=rb.get(s, ''), 确认日偏移=conf[s],
                       区间涨跌pct=r['区间涨跌pct'], 全局ER=r['全局ER'],
                       上行ER=r['上行ER'], 上行ER中位=r['上行ER中位'], n_up=int(r['n_up']), low_n_up=bool(r['low_n_up']),
                       下行ER=r['下行ER'], 下行ER中位=r['下行ER中位'], n_dn=int(r['n_dn']), low_n_dn=bool(r['low_n_dn']),
                       EP05=int(r['EP05']), EP06=int(r['EP06']), ER20最大=r['ER20最大'],
                       HV20=r['HV20'], 静态corr=r['静态corr'],
                       corr60均值=r['corr60均值'], corr60最低=r['corr60最低'],
                       up分位=r['up分位'], dn分位=r['dn分位'],
                       hist80高up=bool(r['hist80高up']), hist80高dn=bool(r['hist80高dn']))
            # 敏感性：th=3% 和 8% 时标签
            row['标签th3'] = tables[0.03].loc[s, '标签'] if s in tables[0.03].index else 'NA'
            row['标签th8'] = tables[0.08].loc[s, '标签'] if s in tables[0.08].index else 'NA'
            long_rows.append(row)
        main_tables[sl.slice_id] = main
    return pd.DataFrame(long_rows), main_tables

def bootstrap_baseline(slices, ret_th, n_boot=500, seed=42):
    """随机等长窗口基线：每切片长度 → 随机抽同长窗口打标签 → 独立标签板块数分布"""
    rng = np.random.default_rng(seed)
    Sdf = swe.S.dropna(subset=['SPY'])
    n = len(Sdf)
    out = {}
    for _, sl in slices.iterrows():
        L = int(sl.length)
        th = th_for(L)
        # 避开真实切片±区间
        forbidden = []
        for _, s2 in slices.iterrows():
            i0 = Sdf.index.searchsorted(pd.Timestamp(s2.start)); i1 = Sdf.index.searchsorted(pd.Timestamp(s2.end))
            forbidden.extend(range(max(0, i0-10), min(n, i1+10)))
        forbidden = set(forbidden)
        counts = []
        tries = 0
        while len(counts) < n_boot and tries < n_boot*20:
            tries += 1
            i0 = rng.integers(250, n-L)
            if any(j in forbidden for j in range(i0, i0+L)):
                continue
            t1 = str(Sdf.index[i0].date()); t2 = str(Sdf.index[i0+L-1].date())
            try:
                df = swe.label_table(swe.analyze(t1, t2, th), ret_th=ret_th)
            except Exception:
                continue
            counts.append(int(df['标签'].str.contains('独立').sum()))
        out[sl.slice_id] = counts
    return out

def main():
    slices = pd.read_csv(os.path.join(R, 'choppy_slices.csv'), parse_dates=['start', 'end'])
    print(f'切片 {len(slices)} 个：{"主口径" if True else ""}')

    # 第一遍：固定 8% 校准
    print('pass1 ret_th=8% ...'); sys.stdout.flush()
    df1, _ = scan_all(slices, 8.0)
    q75 = float(df1['区间涨跌pct'].abs().quantile(0.75))
    ret_th = round(q75, 1)
    print(f'校准阈值：全切片|区间涨跌| 75分位 = {q75:.2f}% → 冻结 ret_th={ret_th}%')

    # 第二遍：校准阈值
    print('pass2 校准阈值重跑 ...'); sys.stdout.flush()
    df, tables = scan_all(slices, ret_th)
    df.to_csv(os.path.join(R, 'sector_independence_scan.csv'), index=False, encoding='utf-8-sig')

    # bootstrap 基线（500 × ~16 切片，耗时较长，逐切片打印进度）
    print('bootstrap 500 随机等长窗口 ...'); sys.stdout.flush()
    base = bootstrap_baseline(slices, ret_th)
    summary = []
    for _, sl in slices.iterrows():
        sid = sl.slice_id
        sub = df[df.slice_id == sid]
        strong = int((sub['标签'] == '强势独立上涨').sum())
        weak = int((sub['标签'] == '弱势独立下跌').sum())
        ind = strong + weak
        counts = np.array(base.get(sid, []))
        p = (1 + (counts >= ind).sum()) / (1 + len(counts)) if len(counts) else np.nan
        summary.append(dict(slice_id=sid, start=str(sl.start.date()), end=str(sl.end.date()),
                            length=int(sl.length), ongoing=bool(sl.ongoing),
                            独立强势数=strong, 独立弱势数=weak, 独立合计=ind,
                            基线均值=round(float(counts.mean()), 2) if len(counts) else None,
                            p_value=round(float(p), 3) if len(counts) else None))
    sm = pd.DataFrame(summary)
    print(sm.to_string(index=False))

    meta = dict(
        ret_th=ret_th, ret_th_source='全切片|区间涨跌|75分位（第一遍用8%跑）',
        th_rule='切片<120交易日→th=3%，否则5%；敏感性3/5/8',
        slices=summary, calibration_pass1_q75=round(q75, 3),
        n_slices=len(slices), generated=pd.Timestamp.now().isoformat(timespec='seconds'))
    with open(os.path.join(R, 'scan_slices.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f'\nwritten: {os.path.join(R,"sector_independence_scan.csv")} + scan_slices.json')

if __name__ == '__main__':
    main()
